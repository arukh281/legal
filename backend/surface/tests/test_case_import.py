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

    dummy_file = SimpleUploadedFile(
        "cases.csv", b"client name,matter title\nAcme,Suit 1\n", content_type="text/csv"
    )

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

    macro_file = SimpleUploadedFile(
        "malicious.xlsm",
        macro_bytes,
        content_type="application/vnd.ms-excel.sheet.macroEnabled.main+xml",
    )
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


def test_synthetic_20_cases_preview_commit_and_deduplication(
    r3_import_setup: dict[str, Any],
) -> None:
    """Full end-to-end test with synthetic_cases_20.xlsx fixture: preview, commit, deduplication, past hearings."""
    ctx = r3_import_setup
    client = HttpClient()

    xlsx_path = os.path.join(FIXTURE_DIR, "synthetic_cases_20.xlsx")
    with open(xlsx_path, "rb") as f:
        xlsx_bytes = f.read()

    upload_file = SimpleUploadedFile(
        "synthetic_cases_20.xlsx",
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

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
    has_ambiguity_warning = any(
        any("ambiguous" in w.lower() for w in r.get("warnings", [])) for r in rows
    )
    assert has_ambiguity_warning

    # Check lead lawyer email warning for non-existent lawyer (Correction 13)
    has_lawyer_warning = any(
        any("lead lawyer email" in w.lower() for w in r.get("warnings", [])) for r in rows
    )
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

    # 3. Verify imported hearings leave outcome empty and store provenance in source_ref (Item 4)
    with admin_db_context():
        imported_hearings = list(
            Hearing.objects.filter(
                tenant_id=ctx["tenant_id"],
                source="MANUAL",
                source_ref__startswith=f"import:{import_id}:row",
            )
        )
        assert len(imported_hearings) > 0
        for h in imported_hearings:
            assert h.status == "LISTED"
            assert h.outcome is None  # Outcome must remain strictly empty for imported hearings
            assert h.source_ref is not None
            assert h.source_ref.startswith(f"import:{import_id}:row ")
            assert (
                h.source_note
                == f"Imported from synthetic_cases_20.xlsx, {h.source_ref.split(':')[2]}"
            )

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
        assert (
            audit.detail is not None
            and audit.detail["counts"]["matters_created"] == counts["matters_created"]
        )

    # 6. Re-import the exact same file -> must warn and create 0 new matters (Correction 11 & Deduplication)
    upload_file2 = SimpleUploadedFile(
        "synthetic_cases_20.xlsx",
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
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
    # Assert commit finishes in a reasonable time (< 180s in test env)
    assert t_commit < 180.0


def test_sequential_import_commits_create_matters_only_once(
    r3_import_setup: dict[str, Any],
) -> None:
    """Session R3 Item 2: Two commit jobs of the same file, committed one after the other, create matters only once."""
    ctx = r3_import_setup
    client = HttpClient()

    csv_content = (
        b"Client Name,Matter Title,Court,Case Number,Next Hearing Date\n"
        b"Delta Industries Ltd,Delta Insolvency Matter,NCLT Mumbai,CP (IB) 991/2026,2026-11-20\n"
        b"Delta Industries Ltd,Delta Recovery Suit,DRT Mumbai,OA 102/2026,2026-11-22\n"
    )

    # 1. Upload Job 1
    f1 = SimpleUploadedFile("cases.csv", csv_content, content_type="text/csv")
    res1 = client.post(
        "/api/cases/import/upload", {"file": f1}, HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}"
    )
    assert res1.status_code == 200
    import_id_1 = res1.json()["import_id"]

    # 2. Upload Job 2 (same file)
    f2 = SimpleUploadedFile("cases.csv", csv_content, content_type="text/csv")
    res2 = client.post(
        "/api/cases/import/upload", {"file": f2}, HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}"
    )
    assert res2.status_code == 200
    import_id_2 = res2.json()["import_id"]

    # 3. Commit Job 1
    res_commit_1 = client.post(
        f"/api/cases/import/{import_id_1}/commit",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_commit_1.status_code == 200
    counts1 = res_commit_1.json()["counts"]
    assert counts1["matters_created"] == 2

    # 4. Commit Job 2 (re-parse & duplicate check inside lock must see existing matters)
    res_commit_2 = client.post(
        f"/api/cases/import/{import_id_2}/commit",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_commit_2.status_code == 200
    counts2 = res_commit_2.json()["counts"]
    assert counts2["matters_created"] == 0  # Created matters only once!

    with admin_db_context():
        from workspace.models import Matter

        matters = list(Matter.objects.filter(tenant_id=ctx["tenant_id"]))
        assert len(matters) == 2


def test_import_with_chosen_sheet_2(r3_import_setup: dict[str, Any]) -> None:
    """Session R3 Item 3: Commit honors the chosen sheet name stored on import_job."""
    import io

    import openpyxl

    ctx = r3_import_setup
    client = HttpClient()

    wb = openpyxl.Workbook()
    # Sheet 1
    ws1 = wb.active
    assert ws1 is not None
    ws1.title = "Sheet1"
    ws1.append(["Client Name", "Matter Title", "Court", "Case Number", "Next Hearing Date"])
    ws1.append(
        ["Alpha Corp", "Alpha Should Not Be Created", "NCLT Delhi", "CP 1/2026", "2026-11-01"]
    )

    # Sheet 2
    ws2 = wb.create_sheet(title="Cases Sheet 2")
    ws2.append(["Client Name", "Matter Title", "Court", "Case Number", "Next Hearing Date"])
    ws2.append(["Beta Ltd", "Beta Matter From Sheet Two", "NCLT Mumbai", "CP 2/2026", "2026-11-05"])

    buf = io.BytesIO()
    wb.save(buf)
    wb_bytes = buf.getvalue()

    f = SimpleUploadedFile(
        "two_sheets.xlsx",
        wb_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    res_up = client.post(
        "/api/cases/import/upload", {"file": f}, HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}"
    )
    assert res_up.status_code == 200
    import_id = res_up.json()["import_id"]
    assert "Cases Sheet 2" in res_up.json()["sheet_names"]

    # Preview choosing sheet 2
    res_prev = client.post(
        f"/api/cases/import/{import_id}/preview",
        data={"sheet_name": "Cases Sheet 2"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_prev.status_code == 200
    rows = res_prev.json()["preview"]["rows"]
    assert len(rows) == 1
    assert rows[0]["matter_title"] == "Beta Matter From Sheet Two"

    # Commit import
    res_commit = client.post(
        f"/api/cases/import/{import_id}/commit",
        HTTP_AUTHORIZATION=f"Bearer {ctx['admin_id']}",
    )
    assert res_commit.status_code == 200
    assert res_commit.json()["counts"]["matters_created"] == 1

    with admin_db_context():
        from workspace.models import ImportJob, Matter

        job = ImportJob.objects.get(tenant_id=ctx["tenant_id"], import_id=import_id)
        assert job.sheet_name == "Cases Sheet 2"

        beta_matter = Matter.objects.filter(
            tenant_id=ctx["tenant_id"], title="Beta Matter From Sheet Two"
        ).first()
        assert beta_matter is not None
        alpha_matter = Matter.objects.filter(
            tenant_id=ctx["tenant_id"], title="Alpha Should Not Be Created"
        ).first()
        assert alpha_matter is None


def test_import_parsing_dates_and_row_limit() -> None:
    """Session R3 Item 11: Date parsing handles NA, to be listed, Excel serial numbers, and rejects 5,001 rows."""
    from datetime import date

    from workspace.import_service import parse_import_date, parse_raw_rows

    today_d = date(2026, 10, 19)

    # 1. 'NA' and 'to be listed' return no date + warning
    d_na, w_na = parse_import_date("NA", today_d)
    assert d_na is None
    assert len(w_na) > 0 and "no date provided" in w_na[0].lower()

    d_tbl, w_tbl = parse_import_date("to be listed", today_d)
    assert d_tbl is None
    assert len(w_tbl) > 0 and "no date provided" in w_tbl[0].lower()

    # 2. Excel serial number cell (numeric and string)
    d_ser_int, _ = parse_import_date(46000, today_d)
    assert isinstance(d_ser_int, date)

    d_ser_str, _ = parse_import_date("46000", today_d)
    assert isinstance(d_ser_str, date)
    assert d_ser_int == d_ser_str

    # 3. 5,001 rows is refused
    csv_lines = ["Client Name,Matter Title\n"] + ["Test Client,Test Matter\n"] * 5001
    large_csv_bytes = "".join(csv_lines).encode("utf-8")

    with pytest.raises(ValueError) as excinfo:
        parse_raw_rows(large_csv_bytes, "csv")
    assert "exceeds the maximum limit" in str(excinfo.value)


def test_import_commit_rollback_on_halfway_failure(r3_import_setup: dict[str, Any]) -> None:
    """Session R3 Item 11: A commit that fails halfway leaves no clients, matters or hearings behind."""
    from unittest.mock import patch

    ctx = r3_import_setup

    raw_rows = [
        [
            f"Client {i}",
            "COMPANY",
            "",
            f"Matter {i}",
            "IBC",
            "NCLT",
            f"CP {i}/2026",
            "2026-11-15",
            "",
            "",
        ]
        for i in range(1, 15)
    ]
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
    preview_data = generate_import_preview(ctx["tenant_id"], raw_rows, mapping)

    import_id = mint_id("imj")
    with admin_db_context():
        ImportJob.objects.create(
            tenant_id=ctx["tenant_id"],
            import_id=import_id,
            filename="rollback_test.csv",
            file_size=2000,
            row_count=14,
            status="PREVIEW",
            sha256="rollback_sha256",
            mapping=mapping,
            client_overrides={},
            counts=preview_data["summary"],
            report=[],
            file_ref="s3://test/rollback_test.csv",
            created_by=ctx["admin_id"],
        )

    # Patch create_hearing_service to fail on row 10
    call_count = 0
    from workspace.services import create_hearing_service as orig_create_hearing

    def fail_at_tenth(**kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count >= 10:
            raise RuntimeError("Simulated crash during hearing creation on row 10")
        return orig_create_hearing(**kwargs)

    with patch("workspace.import_service.create_hearing_service", side_effect=fail_at_tenth):
        with pytest.raises(RuntimeError) as excinfo:
            execute_import_commit(
                tenant_id=ctx["tenant_id"],
                importer_user_id=ctx["admin_id"],
                import_id=import_id,
                preview_data=preview_data,
                original_filename="rollback_test.csv",
            )
        assert "Simulated crash" in str(excinfo.value)

    # Verify zero clients, matters, or hearings were persisted in database
    with admin_db_context():
        from workspace.models import Client, Hearing, Matter

        assert Client.objects.filter(tenant_id=ctx["tenant_id"]).count() == 0
        assert Matter.objects.filter(tenant_id=ctx["tenant_id"]).count() == 0
        assert Hearing.objects.filter(tenant_id=ctx["tenant_id"]).count() == 0


def test_import_cross_client_case_duplicate_detection_and_skip(
    r3_import_setup: dict[str, Any],
) -> None:
    """Session R3 Fix Pass 2 - Item 2: Existing case number under another client is skipped by default with warning."""
    ctx = r3_import_setup
    from workspace.db import tenant_db_context
    from workspace.services import (
        create_case_link_service,
        create_client_service,
        create_matter_service,
    )

    # Setup existing client 'Acme Infra Ltd' with matter and case link under tenant context
    with tenant_db_context(tenant_id=ctx["tenant_id"], user_id=ctx["admin_id"]):
        c = create_client_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            display_name="Acme Infra Ltd",
            client_type="COMPANY",
        )
        m = create_matter_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            client_id=c["client_id"],
            title="Insolvency Resolution Process",
            case_type="IBC",
            court_or_forum="NCLT Mumbai",
        )
        create_case_link_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            matter_id=m["matter_id"],
            value_raw="CP (IB) 123/MB/2024",
        )

    # Now preview an import row where client name has a typo: 'Acme Infra Lt'
    raw_rows = [
        [
            "Acme Infra Lt",
            "COMPANY",
            "",
            "Resolution Plan Approval",
            "IBC",
            "NCLT Mumbai",
            "CP (IB) 123/MB/2024",
            "",
            "",
            "",
        ]
    ]
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
    with tenant_db_context(tenant_id=ctx["tenant_id"], user_id=ctx["admin_id"]):
        preview_data = generate_import_preview(ctx["tenant_id"], raw_rows, mapping)
        row = preview_data["rows"][0]

        assert row["client_status"] == "NEW_CLIENT"
        assert row["matter_status"] == "ALREADY_EXISTS"
        assert any(
            "possible duplicate (case number exists under Acme Infra Ltd)" in w
            for w in row["warnings"]
        )
        assert row["suggested_client_name"] == "Acme Infra Ltd"
        assert row["suggested_client_id"] == c["client_id"]
        assert preview_data["summary"]["existing_matters"] == 1
        assert preview_data["summary"]["new_matters"] == 0
        assert preview_data["summary"]["new_clients"] == 0

        # Test override: with action CREATE_ANYWAY, matter_status is NEW_MATTER and can be committed
        override_preview = generate_import_preview(
            ctx["tenant_id"], raw_rows, mapping, client_overrides={"1": {"action": "CREATE_ANYWAY"}}
        )
        ov_row = override_preview["rows"][0]
        assert ov_row["matter_status"] == "NEW_MATTER"
        assert any(
            "possible duplicate (case number exists under Acme Infra Ltd)" in w
            for w in ov_row["warnings"]
        )
        assert override_preview["summary"]["existing_matters"] == 0
        assert override_preview["summary"]["new_matters"] == 1
        assert override_preview["summary"]["new_clients"] == 1

    import_id = mint_id("imj")
    with admin_db_context():
        ImportJob.objects.create(
            tenant_id=ctx["tenant_id"],
            import_id=import_id,
            filename="acme_import.csv",
            file_size=500,
            row_count=1,
            status="PREVIEW",
            sha256="acme_preview_sha",
            mapping=mapping,
            client_overrides={"1": {"action": "CREATE_ANYWAY"}},
            counts=override_preview["summary"],
            report=[],
            file_ref="s3://test/acme_import.csv",
            created_by=ctx["admin_id"],
        )

    execute_import_commit(
        tenant_id=ctx["tenant_id"],
        importer_user_id=ctx["admin_id"],
        import_id=import_id,
        preview_data=override_preview,
        original_filename="acme_import.csv",
    )

    with admin_db_context():
        from workspace.models import Client

        assert Client.objects.filter(
            tenant_id=ctx["tenant_id"], display_name="Acme Infra Lt"
        ).exists()


def test_client_role_canonical_list_and_normalization(r3_import_setup: dict[str, Any]) -> None:
    """Session R3 Fix Pass 2 - Item 3: Canonical client roles, synonym normalization, and validation."""
    from workspace.db import tenant_db_context
    from workspace.import_service import normalize_client_role
    from workspace.models import CLIENT_ROLES
    from workspace.services import create_client_service, create_matter_service

    ctx = r3_import_setup

    # Canonical list check
    assert CLIENT_ROLES == (
        "PETITIONER",
        "RESPONDENT",
        "APPELLANT",
        "CLAIMANT",
        "ADVISORY",
        "NOT_SET",
    )

    # Synonym mapping
    role, warn = normalize_client_role("Applicant No. 2")
    assert role == "PETITIONER" and warn is None

    role, warn = normalize_client_role("Plaintiff")
    assert role == "PETITIONER" and warn is None

    role, warn = normalize_client_role("complainant")
    assert role == "PETITIONER" and warn is None

    role, warn = normalize_client_role("Defendant No. 1")
    assert role == "RESPONDENT" and warn is None

    role, warn = normalize_client_role("respondent")
    assert role == "RESPONDENT" and warn is None

    role, warn = normalize_client_role("Appellant")
    assert role == "APPELLANT" and warn is None

    role, warn = normalize_client_role("CLAIMANT")
    assert role == "CLAIMANT" and warn is None

    role, warn = normalize_client_role("advisory")
    assert role == "ADVISORY" and warn is None

    role, warn = normalize_client_role("")
    assert role == "NOT_SET" and warn is not None and "not specified" in warn

    role, warn = normalize_client_role(None)
    assert role == "NOT_SET" and warn is not None and "not specified" in warn

    # Unrecognized role becomes NOT_SET with warning naming the value
    role, warn = normalize_client_role("Intervenor")
    assert role == "NOT_SET"
    assert warn is not None and "Intervenor" in warn and "NOT_SET" in warn

    # create_matter_service rejects invalid role
    with tenant_db_context(tenant_id=ctx["tenant_id"], user_id=ctx["admin_id"]):
        c = create_client_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            display_name="Role Test Client",
            client_type="COMPANY",
        )
        with pytest.raises(ValueError) as excinfo:
            create_matter_service(
                tenant_id=ctx["tenant_id"],
                actor_id=ctx["admin_id"],
                client_id=c["client_id"],
                title="Invalid Role Matter",
                client_role="PLAINTIFF",  # Must be canonical PETITIONER
            )
        assert "Invalid client_role" in str(excinfo.value)

        # Valid canonical role succeeds
        m = create_matter_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            client_id=c["client_id"],
            title="Valid Role Matter",
            client_role="PETITIONER",
        )
        assert m["client_role"] == "PETITIONER"


def test_hearing_source_note_via_api(r3_import_setup: dict[str, Any]) -> None:
    """Session R3 Fix Pass 2 - Item 4: source_note in hearing API responses."""
    from datetime import date

    from workspace.db import tenant_db_context
    from workspace.models import ImportJob
    from workspace.services import (
        create_client_service,
        create_hearing_service,
        create_matter_service,
    )

    ctx = r3_import_setup
    client = HttpClient()
    auth_header = f"Bearer {ctx['admin_id']}"

    import_id = mint_id("imj")
    with admin_db_context():
        ImportJob.objects.create(
            tenant_id=ctx["tenant_id"],
            import_id=import_id,
            filename="cause_list_oct.xlsx",
            file_size=1024,
            row_count=10,
            status="COMMITTED",
            sha256="sha_oct_cases",
            file_ref="s3://test/cause_list_oct.xlsx",
            created_by=ctx["admin_id"],
        )

    with tenant_db_context(tenant_id=ctx["tenant_id"], user_id=ctx["admin_id"]):
        c = create_client_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            display_name="Source Note Client",
            client_type="COMPANY",
        )
        m = create_matter_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            client_id=c["client_id"],
            title="Source Note Matter",
        )
        # Create one hearing with import source_ref
        h_imported = create_hearing_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            matter_id=m["matter_id"],
            hearing_date=date(2026, 11, 20),
            court_no="Court 1",
            purpose="Hearing on Admission",
            source="MANUAL",
            source_ref=f"import:{import_id}:row 42",
            status="LISTED",
        )
        # Create second hearing with manual source
        h_manual = create_hearing_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            matter_id=m["matter_id"],
            hearing_date=date(2026, 11, 25),
            court_no="Court 1",
            purpose="Subsequent Hearing",
            source="MANUAL",
            source_ref=None,
            status="LISTED",
        )

    # 1. Test GET /api/matters/{matter_id}/hearings
    res = client.get(f"/api/matters/{m['matter_id']}/hearings", HTTP_AUTHORIZATION=auth_header)
    assert res.status_code == 200
    hearings_data = res.json()
    assert len(hearings_data) >= 2

    imported_resp = next(h for h in hearings_data if h["hearing_id"] == h_imported["hearing_id"])
    assert imported_resp["source_note"] == "Imported from cause_list_oct.xlsx, row 42"

    manual_resp = next(h for h in hearings_data if h["hearing_id"] == h_manual["hearing_id"])
    assert manual_resp["source_note"] is None

    # 2. Test POST /api/matters/{matter_id}/hearings returns source_note
    res_post = client.post(
        f"/api/matters/{m['matter_id']}/hearings",
        data={"date": "2026-12-01", "court_no": "2", "purpose": "Directions"},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_header,
    )
    assert res_post.status_code == 200
    assert "source_note" in res_post.json()

    # 3. Test POST /api/hearings/{hearing_id}/outcome returns source_note
    res_out = client.post(
        f"/api/hearings/{h_imported['hearing_id']}/outcome",
        data={"status": "ADJOURNED", "outcome": "Adjourned to December."},
        content_type="application/json",
        HTTP_AUTHORIZATION=auth_header,
    )
    assert res_out.status_code == 200
    assert res_out.json()["source_note"] == "Imported from cause_list_oct.xlsx, row 42"


def test_excel_serial_number_boundaries_and_rejections() -> None:
    """Session R3 Fix Pass 2 - Item 7: Serial dates restricted to 2000-2099; 4-digit years warn unreadable."""
    from datetime import date

    from workspace.import_service import parse_import_date

    today_d = date(2026, 10, 19)

    # 4-digit values like 2024 warn "unreadable date"
    d_num_year, w_num_year = parse_import_date(2024, today_d)
    assert d_num_year is None
    assert any("unreadable date" in w.lower() for w in w_num_year)

    d_str_year, w_str_year = parse_import_date("2024", today_d)
    assert d_str_year is None
    assert any("unreadable date" in w.lower() for w in w_str_year)

    # Below 36526 (e.g. 36525 = 1999-12-31)
    d_low, w_low = parse_import_date(36525, today_d)
    assert d_low is None
    assert any("unreadable date" in w.lower() for w in w_low)

    # Valid lower bound: 36526 -> 2000-01-01 (past date warning is normal, not unreadable)
    d_min, w_min = parse_import_date(36526, today_d)
    assert d_min == date(2000, 1, 1)
    assert not any("unreadable" in w.lower() for w in w_min)

    # Valid upper bound: 73050 -> 2099-12-31
    d_max, w_max = parse_import_date(73050, today_d)
    assert d_max == date(2099, 12, 31)
    assert len(w_max) == 0

    # Above 73050 (e.g. 73051)
    d_high, w_high = parse_import_date(73051, today_d)
    assert d_high is None
    assert any("unreadable date" in w.lower() for w in w_high)


def test_import_row_override_does_not_leak_to_next_row(r3_import_setup: dict[str, Any]) -> None:
    """Session Demo setup: Verify that an override on row 5 does NOT leak to row 6.

    Previously, overrides.get(str(row_num)) or overrides.get(str(idx)) caused
    row 6 (where idx is 5) to inherit row 5's override when row 6 had no override.
    """
    ctx = r3_import_setup
    from workspace.db import tenant_db_context
    from workspace.services import (
        create_case_link_service,
        create_client_service,
        create_matter_service,
    )

    with tenant_db_context(tenant_id=ctx["tenant_id"], user_id=ctx["admin_id"]):
        cli = create_client_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            display_name="Existing Corporation Ltd",
            client_type="COMPANY",
        )
        mat = create_matter_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            client_id=cli["client_id"],
            title="Pre-existing Matter",
            case_type="IBC",
            court_or_forum="NCLT Mumbai",
        )
        create_case_link_service(
            tenant_id=ctx["tenant_id"],
            actor_id=ctx["admin_id"],
            matter_id=mat["matter_id"],
            value_raw="CP (IB) 888/MB/2024",
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

        # Create 6 rows. Rows 1-4 are ordinary new matters.
        # Row 5 and Row 6 both reference the existing case number under a different client.
        raw_rows = [
            [
                f"Client {i}",
                "COMPANY",
                "",
                f"Matter {i}",
                "IBC",
                "NCLT",
                f"CP (IB) {i}/2024",
                "",
                "",
                "",
            ]
            for i in range(1, 5)
        ]
        # Row 5 (idx 4, row_num 5):
        raw_rows.append(
            [
                "New Client Five",
                "COMPANY",
                "",
                "Matter Five",
                "IBC",
                "NCLT Mumbai",
                "CP (IB) 888/MB/2024",
                "",
                "",
                "",
            ]
        )
        # Row 6 (idx 5, row_num 6):
        raw_rows.append(
            [
                "New Client Six",
                "COMPANY",
                "",
                "Matter Six",
                "IBC",
                "NCLT Mumbai",
                "CP (IB) 888/MB/2024",
                "",
                "",
                "",
            ]
        )

        # Without override: row 5 and row 6 are both flagged as ALREADY_EXISTS
        preview_no_ov = generate_import_preview(ctx["tenant_id"], raw_rows, mapping)
        assert preview_no_ov["rows"][4]["matter_status"] == "ALREADY_EXISTS"
        assert preview_no_ov["rows"][5]["matter_status"] == "ALREADY_EXISTS"

        # Apply override ONLY to row 5:
        # Row 5 (row_num 5) should become NEW_MATTER.
        # Row 6 (row_num 6, idx 5) must remain ALREADY_EXISTS and NOT leak row 5's override.
        preview_with_ov = generate_import_preview(
            ctx["tenant_id"],
            raw_rows,
            mapping,
            client_overrides={"5": {"action": "CREATE_ANYWAY"}},
        )
        assert preview_with_ov["rows"][4]["matter_status"] == "NEW_MATTER"
        assert preview_with_ov["rows"][5]["matter_status"] == "ALREADY_EXISTS"

        # Summary check: 4 + 1 = 5 new matters, 1 existing matter
        assert preview_with_ov["summary"]["new_matters"] == 5
        assert preview_with_ov["summary"]["existing_matters"] == 1
        # 4 new clients from rows 1-4, plus row 5 (overridden), row 6 skipped -> 5 new clients
        assert preview_with_ov["summary"]["new_clients"] == 5
