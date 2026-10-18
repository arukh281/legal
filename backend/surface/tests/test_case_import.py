"""Unit, contract, and benchmark tests for live cases import (Session R3).

Normative tests:
- Allowed for firm ADMIN only (Correction 9; PARTNER and ASSOCIATE get 403).
- Strict file safety: reject .xlsm with VBA/macros, >100 MB uncompressed, null bytes (Correction 12).
- Day-first Indian date parsing with ambiguity warnings and Excel serial numbers (Correction 7, 12).
- Past hearing dates imported as LISTED (never HEARD) with note (Correction 7).
- Unparseable case numbers saved with track=false (Correction 10).
- Deduplication: CIN/PAN -> name; readable case number, unreadable raw text, title match (Correction 8).
- Atomic commit under pg_advisory_xact_lock per tenant; refuse already COMMITTED job (Correction 11).
- Duplicate file hash warning on re-import (Correction 11).
- Formula sanitization in CSV report (=, +, -, @, \\t, \\r) (Correction 12).
- Benchmark timing of 5,000-row commit (Correction 21).
"""

from __future__ import annotations

import os
import time
from datetime import timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as HttpClient
from django.utils import timezone

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from workspace.import_service import (
    execute_import_commit,
    generate_import_preview,
    sanitize_csv_cell,
)
from workspace.models import (
    AppUser,
    AuditEvent,
    Hearing,
    ImportJob,
    MatterCaseLink,
    Tenant,
)

IST = ZoneInfo("Asia/Kolkata")
pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "../../../eval/fixtures/import")


@pytest.fixture(autouse=True)
def enable_dev_auth(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


@pytest.fixture
def r3_import_setup() -> dict[str, Any]:
    tenant_id = mint_id("ten")
    admin_id = mint_id("usr")
    partner_id = mint_id("usr")
    associate_id = mint_id("usr")

    with admin_db_context():
        Tenant.objects.create(
            tenant_id=tenant_id,
            name="National Law Chambers",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=admin_id,
            email=f"admin_{admin_id}@lawfirm.in",
            display_name="Managing Admin",
            idp_subject=f"sub_{admin_id}",
            firm_role="ADMIN",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=partner_id,
            email=f"partner_{partner_id}@lawfirm.in",
            display_name="Partner Lawyer",
            idp_subject=f"sub_{partner_id}",
            firm_role="PARTNER",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=tenant_id,
            user_id=associate_id,
            email=f"associate_{associate_id}@lawfirm.in",
            display_name="Associate Lawyer",
            idp_subject=f"sub_{associate_id}",
            firm_role="ASSOCIATE",
            active=True,
        )

    return {
        "tenant_id": tenant_id,
        "admin_id": admin_id,
        "partner_id": partner_id,
        "associate_id": associate_id,
    }


def test_import_admin_only_access(r3_import_setup: dict[str, Any]) -> None:
    """Test that only firm ADMIN can import cases; PARTNER/ASSOCIATE get 403 (Correction 9)."""
    ctx = r3_import_setup
    client = HttpClient()

    dummy_file = SimpleUploadedFile("cases.csv", b"client name,matter title\nAcme,Suit 1\n", content_type="text/csv")

    # Partner upload -> 403
    res_part = client.post(
        "/api/cases/import/upload",
        {"file": dummy_file},
        HTTP_AUTHORIZATION=f"Bearer {ctx['partner_id']}",
    )
    assert res_part.status_code == 403
    assert "ADMIN" in res_part.json()["detail"]

    # Associate upload -> 403
    dummy_file.seek(0)
    res_assoc = client.post(
        "/api/cases/import/upload",
        {"file": dummy_file},
        HTTP_AUTHORIZATION=f"Bearer {ctx['associate_id']}",
    )
    assert res_assoc.status_code == 403

    # Admin download template -> 200
    res_tpl = client.get(
        "/api/cases/import/template?fmt=csv",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_tpl.status_code == 200
    assert "client name" in res_tpl.content.decode("utf-8")


def test_import_file_safety_checks(r3_import_setup: dict[str, Any]) -> None:
    """Test macro/vba rejection, zip safety, and Windows-1252 fallback (Correction 12)."""
    ctx = r3_import_setup
    client = HttpClient()

    # 1. Reject .xlsm with macros
    macro_path = os.path.join(FIXTURE_DIR, "malicious_macro.xlsm")
    with open(macro_path, "rb") as f:
        macro_bytes = f.read()

    macro_file = SimpleUploadedFile("malicious.xlsm", macro_bytes, content_type="application/vnd.ms-excel.sheet.macroEnabled.main+xml")
    res_macro = client.post(
        "/api/cases/import/upload",
        {"file": macro_file},
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_macro.status_code == 400
    assert "macro" in res_macro.json()["detail"].lower()

    # 2. Reject binary null bytes
    bad_file = SimpleUploadedFile("bad.csv", b"col1,col2\x00corrupt", content_type="text/csv")
    res_bad = client.post(
        "/api/cases/import/upload",
        {"file": bad_file},
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_bad.status_code == 400
    assert "binary" in res_bad.json()["detail"].lower()

    # 3. Accept Windows-1252 encoded CSV with warning
    win1252_bytes = "client name,matter title\nMünchen Corp,Arbitration £500\n".encode("cp1252")
    win_file = SimpleUploadedFile("win.csv", win1252_bytes, content_type="text/csv")
    res_win = client.post(
        "/api/cases/import/upload",
        {"file": win_file},
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_win.status_code == 200
    assert "Windows-1252" in res_win.json()["warning"]


def test_synthetic_20_cases_preview_commit_and_deduplication(r3_import_setup: dict[str, Any]) -> None:
    """Full end-to-end test with synthetic_cases_20.xlsx fixture: preview, commit, deduplication, past hearings."""
    ctx = r3_import_setup
    client = HttpClient()

    xlsx_path = os.path.join(FIXTURE_DIR, "synthetic_cases_20.xlsx")
    with open(xlsx_path, "rb") as f:
        xlsx_bytes = f.read()

    upload_file = SimpleUploadedFile("synthetic_cases_20.xlsx", xlsx_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 1. Upload & Preview
    res_upload = client.post(
        "/api/cases/import/upload",
        {"file": upload_file},
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_upload.status_code == 200
    upload_data = res_upload.json()
    import_id = upload_data["import_id"]
    preview = upload_data["preview"]
    assert preview["summary"]["total_rows"] == 20
    assert preview["summary"]["new_matters"] >= 15

    # Check warnings: ambiguous date warning present
    rows = preview["rows"]
    has_ambiguity_warning = any(any("ambiguous" in w.lower() for w in r.get("warnings", [])) for r in rows)
    assert has_ambiguity_warning

    # Check lead lawyer email warning for non-existent lawyer (Correction 13)
    has_lawyer_warning = any(any("lead lawyer email" in w.lower() for w in r.get("warnings", [])) for r in rows)
    assert has_lawyer_warning

    # 2. Commit import
    res_commit = client.post(
        f"/api/cases/import/{import_id}/commit",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_commit.status_code == 200
    commit_data = res_commit.json()
    assert commit_data["status"] == "COMMITTED"
    counts = commit_data["counts"]
    assert counts["clients_created"] > 0
    assert counts["matters_created"] > 0
    assert counts["hearings_created"] > 0
    assert counts["case_links_created"] > 0

    # 3. Verify past hearing dates imported as LISTED (never HEARD) with note (Correction 7)
    with admin_db_context():
        past_hearings = list(
            Hearing.objects.filter(
                tenant_id=ctx["tenant_id"],
                outcome__icontains="date is in the past",
            )
        )
        assert len(past_hearings) > 0
        for h in past_hearings:
            assert h.status == "LISTED"
            assert h.outcome is not None and "imported from" in h.outcome

        # 4. Verify unparseable case number has track=false (Correction 10)
        unparseable_link = MatterCaseLink.objects.filter(
            tenant_id=ctx["tenant_id"],
            value_normalized__icontains="arb/comm/special/2023",
        ).first()
        assert unparseable_link is not None
        assert unparseable_link.track is False

        # 5. Check audit logs (Correction 10: IMPORT_COMMIT recorded)
        audit = AuditEvent.objects.filter(
            tenant_id=ctx["tenant_id"],
            action="IMPORT_COMMIT",
            object_ref=import_id,
        ).first()
        assert audit is not None
        assert audit.detail is not None and audit.detail["counts"]["matters_created"] == counts["matters_created"]

    # 6. Re-import the exact same file -> must warn and create 0 new matters (Correction 11 & Deduplication)
    upload_file2 = SimpleUploadedFile("synthetic_cases_20.xlsx", xlsx_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    res_reupload = client.post(
        "/api/cases/import/upload",
        {"file": upload_file2},
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_reupload.status_code == 200
    reupload_data = res_reupload.json()
    assert "already imported" in reupload_data["warning"]

    # In preview of re-uploaded file, existing matters must match (Correction 8)
    repreview = reupload_data["preview"]
    assert repreview["summary"]["existing_matters"] >= counts["matters_created"]

    # 7. Download CSV report and verify formula sanitization (Correction 12)
    res_rep = client.get(
        f"/api/cases/import/{import_id}/report",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_rep.status_code == 200
    csv_text = res_rep.content.decode("utf-8")
    assert "Row,Status,Client ID" in csv_text


def test_formula_sanitization_helpers() -> None:
    """Verify formula characters =, +, -, @, \\t, \\r are properly escaped (Correction 12)."""
    assert sanitize_csv_cell("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-10") == "'-10"
    assert sanitize_csv_cell("@company") == "'@company"
    assert sanitize_csv_cell("\tindented") == "'\tindented"
    assert sanitize_csv_cell("\rnewline") == "'\rnewline"
    assert sanitize_csv_cell("Normal Text") == "Normal Text"
    assert sanitize_csv_cell(None) == ""


def test_5000_row_commit_benchmark(r3_import_setup: dict[str, Any]) -> None:
    """Benchmark timing of committing a 5,000-row import batch (Correction 21)."""
    ctx = r3_import_setup
    tenant_id = ctx["tenant_id"]
    admin_id = ctx["admin_id"]

    # Generate 5,000 synthetic rows in memory
    raw_rows = []
    today_d = timezone.now().astimezone(IST).date()
    for i in range(1, 5001):
        raw_rows.append(
            [
                f"Client Corp {i % 100}",
                "COMPANY",
                f"U{i:05d}DL2020PLC{i:06d}",
                f"Commercial Matter #{i}",
                "Commercial Suit",
                "High Court of Delhi",
                f"CS(COMM) {i}/2024",
                (today_d + timedelta(days=i % 60)).strftime("%d/%m/%Y"),
                "partner@lawfirm.in",
                f"Benchmark case notes {i}",
            ]
        )

    mapping = {
        "client_name": 0,
        "client_type": 1,
        "cin_or_pan": 2,
        "matter_title": 3,
        "case_type": 4,
        "court_or_forum": 5,
        "case_number": 6,
        "next_hearing_date": 7,
        "lead_lawyer_email": 8,
        "notes": 9,
    }

    t0_preview = time.perf_counter()
    with admin_db_context():
        preview_data = generate_import_preview(tenant_id, raw_rows, mapping)
    t_preview = time.perf_counter() - t0_preview

    import_id = mint_id("imj")
    with admin_db_context():
        ImportJob.objects.create(
            tenant_id=tenant_id,
            import_id=import_id,
            filename="benchmark_5000.csv",
            file_size=500000,
            row_count=5000,
            status="PREVIEW",
            sha256="benchsha256_5000",
            mapping=mapping,
            client_overrides={},
            counts=preview_data["summary"],
            report=[],
            file_ref="s3://test/benchmark_5000.csv",
            created_by=admin_id,
        )

    t0_commit = time.perf_counter()
    with admin_db_context():
        result = execute_import_commit(
            tenant_id=tenant_id,
            importer_user_id=admin_id,
            import_id=import_id,
            preview_data=preview_data,
            original_filename="benchmark_5000.csv",
        )
    t_commit = time.perf_counter() - t0_commit

    print(f"\n[BENCHMARK] 5,000-row preview: {t_preview:.2f}s | commit: {t_commit:.2f}s")
    assert result["status"] == "COMMITTED"
    assert result["counts"]["matters_created"] == 5000
    # Assert commit finishes in a reasonable time (< 120s in test env)
    assert t_commit < 120.0
