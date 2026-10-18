"""Tests for Surface REST API: Clients, Matters, and Document Vault (Session R1).

Normative sources:
- Session R1: the client file (clients, matters, document vault)
- docs/mvp/00_mvp_spec.md §4.1, §4.3
- docs/mvp/03_data_model_and_contracts.md §3.8, §3.9, §6
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from workspace.models import AppUser, Tenant

pytestmark = pytest.mark.django_db(databases="__all__", transaction=True)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture(autouse=True)
def enable_dev_auth(settings: Any) -> None:
    settings.DEBUG = True
    settings.DEV_AUTH_ENABLED = True


@pytest.fixture
def api_setup() -> dict[str, Any]:
    t1 = mint_id("ten")
    t2 = mint_id("ten")

    u_lead = mint_id("usr")
    u_outsider = mint_id("usr")
    u_other = mint_id("usr")

    lead_email = f"lead_{u_lead}@firm1.in"
    outsider_email = f"outsider_{u_outsider}@firm1.in"
    other_email = f"other_{u_other}@firm2.in"

    with admin_db_context():
        Tenant.objects.create(
            tenant_id=t1,
            name="Firm 1",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )
        Tenant.objects.create(
            tenant_id=t2,
            name="Firm 2",
            deployment_mode="D2",
            residency_policy="ANY",
            idp={"kind": "GOOGLE"},
        )

        AppUser.objects.create(
            tenant_id=t1,
            user_id=u_lead,
            email=lead_email,
            idp_subject=f"sub_{u_lead}",
            firm_role="PARTNER",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=t1,
            user_id=u_outsider,
            email=outsider_email,
            idp_subject=f"sub_{u_outsider}",
            firm_role="ASSOCIATE",
            active=True,
        )
        AppUser.objects.create(
            tenant_id=t2,
            user_id=u_other,
            email=other_email,
            idp_subject=f"sub_{u_other}",
            firm_role="PARTNER",
            active=True,
        )

    return {
        "t1": t1,
        "t2": t2,
        "lead_email": lead_email,
        "outsider_email": outsider_email,
        "other_email": other_email,
    }


def test_client_matter_vault_full_lifecycle_and_exit_checks(api_setup: dict[str, Any]) -> None:
    """Exit check flow:

    1. Create client 'Acme Steel Pvt Ltd'. Open matter 'Acme v. Zenith, s.9 petition'
       with case type 'Insolvency (IBC)' and court 'NCLT Mumbai'. Add case number 'CP (IB) 123/MB/2026'.
    2. Upload one IBBI fixture PDF as ORDER with provenance COURT, one DOCX as DRAFT
       with provenance FIRM, and one ZIP containing two PDFs.
    3. The matter page lists them by stage. Opening the order shows numbered paragraphs
       with private anchors and ocr_conf, and a quote highlights in the viewer.
    4. Upload a second version of the DOCX. Both versions are listed and the v1 anchors still resolve.
    5. A second user who is not a matter member gets 403 on the matter, its documents,
       and the client if they share no other matter with it. A user in another tenant sees nothing.
    """
    client_http = Client()

    # Authenticate lead user
    login_resp = client_http.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": api_setup["lead_email"]}),
        content_type="application/json",
    )
    assert login_resp.status_code == 200

    # 1. Create client 'Acme Steel Pvt Ltd'
    create_cli_resp = client_http.post(
        "/api/clients",
        data=json.dumps({
            "display_name": "Acme Steel Pvt Ltd",
            "client_type": "COMPANY",
            "identifiers": {"CIN": "U12345MH2020PTC123456", "PAN": "AAACA1234A"},
            "contact": {"name": "Legal Head", "email": "legal@acme.com", "phone": "+91-9876543210"},
            "notes": "Primary manufacturing client",
        }),
        content_type="application/json",
    )
    assert create_cli_resp.status_code == 200
    client_data = create_cli_resp.json()
    cli_id = client_data["client_id"]
    assert cli_id.startswith("cli_")
    assert client_data["display_name"] == "Acme Steel Pvt Ltd"

    # Open matter 'Acme v. Zenith, s.9 petition'
    create_mat_resp = client_http.post(
        "/api/matters",
        data=json.dumps({
            "client_id": cli_id,
            "title": "Acme v. Zenith, s.9 petition",
            "client_role": "PETITIONER",
            "case_type": "Insolvency (IBC)",
            "court_or_forum": "NCLT Mumbai",
        }),
        content_type="application/json",
    )
    assert create_mat_resp.status_code == 200
    matter_data = create_mat_resp.json()
    mat_id = matter_data["matter_id"]
    assert mat_id.startswith("mat_")
    assert matter_data["case_type"] == "Insolvency (IBC)"
    assert matter_data["court_or_forum"] == "NCLT Mumbai"

    # Add case number 'CP (IB) 123/MB/2026'
    add_case_resp = client_http.post(
        f"/api/matters/{mat_id}/case-links",
        data=json.dumps({
            "scheme": "CASE_NO",
            "value_normalized": "CP (IB) 123/MB/2026",
            "role": "PETITION",
            "track": True,
        }),
        content_type="application/json",
    )
    assert add_case_resp.status_code == 200
    case_link_data = add_case_resp.json()
    assert case_link_data["value_normalized"] == "CP (IB) 123/MUM/2026"
    assert case_link_data["parseable"] is True

    # 2. Upload one IBBI fixture PDF as ORDER with provenance COURT
    ibbi_fixture_path = REPO_ROOT / "eval" / "fixtures" / "ibbi" / "sample_order_1.pdf"
    assert ibbi_fixture_path.exists()
    pdf_bytes = ibbi_fixture_path.read_bytes()

    upload_pdf_resp = client_http.post(
        f"/api/matters/{mat_id}/documents/upload",
        data={
            "file": SimpleUploadedFile("sample_order_1.pdf", pdf_bytes, content_type="application/pdf"),
            "stage": "ORDER",
            "provenance": "COURT",
            "trust_label": "TENANT_COURT_RECORD",
            "privilege_class": "UNPRIVILEGED",
            "doc_type": "ORDER",
            "title": "Admission Order",
        },
    )
    assert upload_pdf_resp.status_code == 200
    pdf_doc_list = upload_pdf_resp.json()
    assert len(pdf_doc_list) == 1
    order_doc_id = pdf_doc_list[0]["pdoc_id"]
    assert pdf_doc_list[0]["stage"] == "ORDER"
    assert pdf_doc_list[0]["provenance"] == "COURT"

    # Upload one DOCX as DRAFT with provenance FIRM
    docx_buf = io.BytesIO()
    with zipfile.ZipFile(docx_buf, "w") as zf:
        zf.writestr(
            "word/document.xml",
            """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                 <w:body>
                   <w:p><w:t>This is paragraph 1 of the strategy draft.</w:t></w:p>
                   <w:p><w:t>This is paragraph 2 of the strategy draft.</w:t></w:p>
                 </w:body>
               </w:document>""",
        )
    docx_bytes = docx_buf.getvalue()

    upload_docx_resp = client_http.post(
        f"/api/matters/{mat_id}/documents/upload",
        data={
            "file": SimpleUploadedFile("strategy_draft.docx", docx_bytes, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "stage": "DRAFT",
            "provenance": "FIRM",
            "trust_label": "TENANT_WORK_PRODUCT",
            "privilege_class": "ATTORNEY_CLIENT",
            "doc_type": "DRAFT",
            "title": "Strategy Draft",
        },
    )
    assert upload_docx_resp.status_code == 200
    docx_doc_list = upload_docx_resp.json()
    docx_doc_id = docx_doc_list[0]["pdoc_id"]
    assert docx_doc_list[0]["stage"] == "DRAFT"
    assert docx_doc_list[0]["provenance"] == "FIRM"

    # Upload one ZIP containing two PDFs
    dummy_pdf1 = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    dummy_pdf2 = b"%PDF-1.4\n2 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("exhibit_1.pdf", dummy_pdf1)
        zf.writestr("exhibit_2.pdf", dummy_pdf2)
    zip_bytes = zip_buf.getvalue()

    upload_zip_resp = client_http.post(
        f"/api/matters/{mat_id}/documents/upload",
        data={
            "file": SimpleUploadedFile("exhibits.zip", zip_bytes, content_type="application/zip"),
            "stage": "EVIDENCE",
            "provenance": "CLIENT",
            "trust_label": "TENANT_CLIENT_DOC",
            "privilege_class": "ATTORNEY_CLIENT",
            "doc_type": "EVIDENCE",
        },
    )
    assert upload_zip_resp.status_code == 200
    zip_doc_list = upload_zip_resp.json()
    assert len(zip_doc_list) == 2
    assert zip_doc_list[0]["family_id"] is not None
    assert zip_doc_list[0]["family_id"] == zip_doc_list[1]["family_id"]

    # 3. Matter documents list grouped by stage
    list_docs_resp = client_http.get(f"/api/matters/{mat_id}/documents")
    assert list_docs_resp.status_code == 200
    all_docs = list_docs_resp.json()
    # 1 ORDER + 1 DRAFT + 2 EVIDENCE = 4 documents
    assert len(all_docs) == 4
    stages_present = {d["stage"] for d in all_docs}
    assert "ORDER" in stages_present
    assert "DRAFT" in stages_present
    assert "EVIDENCE" in stages_present

    # Opening the order shows numbered paragraphs with private anchors and ocr_conf
    para_resp = client_http.get(f"/api/documents/{order_doc_id}/paragraphs")
    assert para_resp.status_code == 200
    order_paras = para_resp.json()["paragraphs"]
    assert len(order_paras) > 0
    first_para = order_paras[0]
    assert first_para["anchor_id"] == f"{order_doc_id}/v1#p1"
    assert first_para["fragment"] == "p1"
    assert first_para["ocr_conf"] is not None
    assert len(first_para["text"].strip()) > 0

    # Raw download works
    download_resp = client_http.get(f"/api/documents/{order_doc_id}/download")
    assert download_resp.status_code == 200
    assert len(download_resp.content) == len(pdf_bytes)

    # 4. Upload a second version of the DOCX
    docx_v2_buf = io.BytesIO()
    with zipfile.ZipFile(docx_v2_buf, "w") as zf:
        zf.writestr(
            "word/document.xml",
            """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                 <w:body>
                   <w:p><w:t>Revised paragraph 1.</w:t></w:p>
                   <w:p><w:t>Revised paragraph 2.</w:t></w:p>
                   <w:p><w:t>Revised paragraph 3.</w:t></w:p>
                 </w:body>
               </w:document>""",
        )
    docx_v2_bytes = docx_v2_buf.getvalue()

    upload_v2_resp = client_http.post(
        f"/api/matters/{mat_id}/documents/upload",
        data={
            "file": SimpleUploadedFile("strategy_draft_v2.docx", docx_v2_bytes, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "pdoc_id": docx_doc_id,  # Version update
            "stage": "DRAFT",
            "provenance": "FIRM",
            "trust_label": "TENANT_WORK_PRODUCT",
            "privilege_class": "ATTORNEY_CLIENT",
            "doc_type": "DRAFT",
        },
    )
    assert upload_v2_resp.status_code == 200
    v2_doc = upload_v2_resp.json()[0]
    assert v2_doc["current_version"] == "v2"

    # Both versions are listed
    versions_resp = client_http.get(f"/api/documents/{docx_doc_id}/versions")
    assert versions_resp.status_code == 200
    ver_list = versions_resp.json()
    assert len(ver_list) == 2
    assert [v["pver"] for v in ver_list] == ["v1", "v2"]

    # v1 anchors still resolve!
    v1_paras_resp = client_http.get(f"/api/documents/{docx_doc_id}/paragraphs?pver=v1")
    assert v1_paras_resp.status_code == 200
    v1_paras = v1_paras_resp.json()["paragraphs"]
    assert len(v1_paras) == 2
    assert v1_paras[0]["anchor_id"] == f"{docx_doc_id}/v1#p1"

    # v2 anchors resolve
    v2_paras_resp = client_http.get(f"/api/documents/{docx_doc_id}/paragraphs?pver=v2")
    assert v2_paras_resp.status_code == 200
    v2_paras = v2_paras_resp.json()["paragraphs"]
    assert len(v2_paras) == 3
    assert v2_paras[2]["anchor_id"] == f"{docx_doc_id}/v2#p3"

    # 5. Second user who is NOT a matter member gets 403 on matter, documents, and client
    outsider_http = Client()
    outsider_login = outsider_http.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": api_setup["outsider_email"]}),
        content_type="application/json",
    )
    assert outsider_login.status_code == 200

    # 403 on matter
    resp = outsider_http.get(f"/api/matters/{mat_id}")
    assert resp.status_code == 403

    # 403 on documents
    resp = outsider_http.get(f"/api/matters/{mat_id}/documents")
    assert resp.status_code == 403

    # 403 on client (shares no matters with it, not admin, not creator)
    resp = outsider_http.get(f"/api/clients/{cli_id}")
    assert resp.status_code == 403

    # User in another tenant sees nothing / gets 403
    other_http = Client()
    other_login = other_http.post(
        "/api/auth/dev-login",
        data=json.dumps({"email": api_setup["other_email"]}),
        content_type="application/json",
    )
    assert other_login.status_code == 200

    resp = other_http.get(f"/api/clients/{cli_id}")
    assert resp.status_code == 403

    resp = other_http.get(f"/api/matters/{mat_id}")
    assert resp.status_code == 403
