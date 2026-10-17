"""Tests for Document Vault: magic bytes, IBBI upload, ZIP expansion, and hidden-text flag (Session R1).

Normative sources:
- Session R1: the client file (clients, matters, document vault)
- docs/mvp/00_mvp_spec.md §2 (non-negotiable 6: hidden text is flagged)
- docs/mvp/03_data_model_and_contracts.md §3.9 (tpl.pdoc, tpl.pdoc_version, tpl.private_anchor)
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from django.db import connections, transaction

from anchor_lib.ids import mint_id
from core.db_router import admin_db_context
from parse.vault import DocumentVaultService, detect_file_type
from workspace.models import PdocVersion, PrivateAnchor

pytestmark = pytest.mark.django_db(
    databases=["default", "owner", "admin", "worker"], transaction=True
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def vault_setup() -> dict[str, str]:
    """Create tenant, user, and matter for vault testing."""
    t1 = mint_id("ten")
    u1 = mint_id("usr")
    m1 = mint_id("mat")
    c1 = mint_id("cli")

    with transaction.atomic(using="owner"):
        with connections["owner"].cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tpl.tenant (tenant_id, name, deployment_mode, residency_policy, llm_policy, idp, created_at)
                VALUES (%s, 'Vault Test Firm', 'D2', 'ANY', '{}', '{"kind":"GOOGLE"}', now());
                """,
                [t1],
            )
            cursor.execute(
                """
                INSERT INTO tpl.app_user (tenant_id, user_id, email, display_name, idp_subject, firm_role, active)
                VALUES (%s, %s, 'lawyer@firm.in', 'Test Lawyer', %s, 'PARTNER', true);
                """,
                [t1, u1, f"sub-{u1}"],
            )
            cursor.execute(
                """
                INSERT INTO tpl.client (tenant_id, client_id, display_name, client_type, created_by, created_at)
                VALUES (%s, %s, 'Vault Client', 'COMPANY', %s, now());
                """,
                [t1, c1, u1],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter (tenant_id, matter_id, client_id, title, client_role, status, created_at)
                VALUES (%s, %s, %s, 'Vault Matter', 'PETITIONER', 'ACTIVE', now());
                """,
                [t1, m1, c1],
            )
            cursor.execute(
                """
                INSERT INTO tpl.matter_member (tenant_id, matter_id, user_id, role, granted_by, granted_at)
                VALUES (%s, %s, %s, 'LEAD', %s, now());
                """,
                [t1, m1, u1, u1],
            )

    return {"tenant_id": t1, "user_id": u1, "matter_id": m1}


def test_magic_byte_detection_and_rejection() -> None:
    """Test detect_file_type strictly verifies magic bytes and rejects forbidden types."""
    # 1. PDF
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    mime, kind = detect_file_type(pdf_bytes)
    assert mime == "application/pdf"
    assert kind == "PDF"

    # 2. DOCX (zip containing word/document.xml)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<w:document><w:body><w:p><w:t>Hello</w:t></w:p></w:body></w:document>")
    docx_bytes = buf.getvalue()
    mime, kind = detect_file_type(docx_bytes)
    assert "wordprocessingml" in mime
    assert kind == "DOCX"

    # 3. Regular ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", "Plain text in zip")
    zip_bytes = buf.getvalue()
    mime, kind = detect_file_type(zip_bytes)
    assert mime == "application/zip"
    assert kind == "ZIP"

    # 4. EML
    eml_bytes = b"From: partner@firm.in\nTo: client@acme.com\nSubject: Matter strategy\nDate: 17 Oct 2026\n\nDear Client,\nPlease find attached."
    mime, kind = detect_file_type(eml_bytes)
    assert mime == "message/rfc822"
    assert kind == "EML"

    # 5. Rejection: PNG image bytes
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with pytest.raises(ValueError, match="Unsupported file type"):
        detect_file_type(png_bytes)

    # 6. Rejection: ELF binary
    elf_bytes = b"\x7fELF\x02\x01\x01\x00"
    with pytest.raises(ValueError, match="Unsupported file type"):
        detect_file_type(elf_bytes)


def test_ibbi_pdf_upload_and_private_anchors(vault_setup: dict[str, str]) -> None:
    """Upload public IBBI fixture PDF as ORDER with provenance COURT into matter vault."""
    ibbi_path = REPO_ROOT / "eval" / "fixtures" / "ibbi" / "sample_order_1.pdf"
    assert ibbi_path.exists(), f"Missing fixture {ibbi_path}"

    raw_bytes = ibbi_path.read_bytes()
    vault = DocumentVaultService()

    pdocs = vault.ingest(
        tenant_id=vault_setup["tenant_id"],
        matter_id=vault_setup["matter_id"],
        user_id=vault_setup["user_id"],
        filename="sample_order_1.pdf",
        raw_bytes=raw_bytes,
        doc_type="ORDER",
        provenance="COURT",
        trust_label="TENANT_COURT_RECORD",
        privilege_class="UNPRIVILEGED",
        stage="ORDER",
        title="IBBI Final Order",
    )

    assert len(pdocs) == 1
    pdoc = pdocs[0]
    assert pdoc.pdoc_id.startswith("pdoc_")
    assert pdoc.stage == "ORDER"
    assert pdoc.provenance == "COURT"
    assert pdoc.trust_label == "TENANT_COURT_RECORD"
    assert pdoc.current_version == "v1"

    # Verify pdoc_version in DB
    with admin_db_context():
        pver = PdocVersion.objects.get(tenant_id=vault_setup["tenant_id"], pdoc_id=pdoc.pdoc_id, pver="v1")
        assert pver.gate in ("PASS", "FLAGGED")
        assert pver.storage_uri.startswith("s3://")

        # Verify private anchors sorted by paragraph number
        anchors = sorted(
            PrivateAnchor.objects.filter(
                tenant_id=vault_setup["tenant_id"], pdoc_id=pdoc.pdoc_id, pver="v1"
            ),
            key=lambda a: int(a.fragment.lstrip("p")),
        )
        assert len(anchors) > 0

        # Anchor format must strictly be pdoc_<ulid>/v1#p<n>
        for idx, a in enumerate(anchors, start=1):
            assert a.anchor_id == f"{pdoc.pdoc_id}/v1#p{idx}"
            assert a.fragment == f"p{idx}"
            assert len(a.text.strip()) > 0
            assert a.ocr_conf is not None


def test_docx_upload_and_versioning(vault_setup: dict[str, str]) -> None:
    """Upload DOCX as DRAFT with provenance FIRM, then upload v2 and verify old anchors stay."""
    # Create simple docx in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "word/document.xml",
            """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                 <w:body>
                   <w:p><w:t>This is the first paragraph of the draft petition.</w:t></w:p>
                   <w:p><w:t>This is the second paragraph specifying the debt default.</w:t></w:p>
                 </w:body>
               </w:document>""",
        )
    raw_v1 = buf.getvalue()

    vault = DocumentVaultService()

    # 1. Ingest Version 1
    pdocs_v1 = vault.ingest(
        tenant_id=vault_setup["tenant_id"],
        matter_id=vault_setup["matter_id"],
        user_id=vault_setup["user_id"],
        filename="petition_draft.docx",
        raw_bytes=raw_v1,
        doc_type="DRAFT",
        provenance="FIRM",
        trust_label="TENANT_WORK_PRODUCT",
        privilege_class="ATTORNEY_CLIENT",
        stage="DRAFT",
        title="Petition Draft",
    )
    pdoc = pdocs_v1[0]
    assert pdoc.current_version == "v1"

    with admin_db_context():
        v1_anchors = list(PrivateAnchor.objects.filter(pdoc_id=pdoc.pdoc_id, pver="v1"))
        assert len(v1_anchors) == 2

    # 2. Ingest Version 2 of same document
    buf_v2 = io.BytesIO()
    with zipfile.ZipFile(buf_v2, "w") as zf:
        zf.writestr(
            "word/document.xml",
            """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                 <w:body>
                   <w:p><w:t>Revised paragraph 1 with updated dates.</w:t></w:p>
                   <w:p><w:t>Revised paragraph 2 with interest calculations.</w:t></w:p>
                   <w:p><w:t>New third paragraph with prayer for relief.</w:t></w:p>
                 </w:body>
               </w:document>""",
        )
    raw_v2 = buf_v2.getvalue()

    pdocs_v2 = vault.ingest(
        tenant_id=vault_setup["tenant_id"],
        matter_id=vault_setup["matter_id"],
        user_id=vault_setup["user_id"],
        filename="petition_draft_v2.docx",
        raw_bytes=raw_v2,
        doc_type="DRAFT",
        provenance="FIRM",
        trust_label="TENANT_WORK_PRODUCT",
        privilege_class="ATTORNEY_CLIENT",
        stage="DRAFT",
        pdoc_id=pdoc.pdoc_id,  # Updating existing document
    )
    assert pdocs_v2[0].current_version == "v2"

    with admin_db_context():
        # Both versions exist
        versions = list(PdocVersion.objects.filter(pdoc_id=pdoc.pdoc_id).order_by("pver"))
        assert len(versions) == 2
        assert [v.pver for v in versions] == ["v1", "v2"]

        # Old v1 anchors are still present and intact!
        v1_anchors_still_present = list(PrivateAnchor.objects.filter(pdoc_id=pdoc.pdoc_id, pver="v1"))
        assert len(v1_anchors_still_present) == 2

        # New v2 anchors created
        v2_anchors = list(PrivateAnchor.objects.filter(pdoc_id=pdoc.pdoc_id, pver="v2"))
        assert len(v2_anchors) == 3


def test_zip_one_level_expansion(vault_setup: dict[str, str]) -> None:
    """Upload ZIP containing 2 PDFs; verify 1-level expansion creates 2 pdocs with same family_id."""
    pdf1_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    pdf2_bytes = b"%PDF-1.4\n2 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("exhibit_a.pdf", pdf1_bytes)
        zf.writestr("exhibit_b.pdf", pdf2_bytes)
        # Non-supported child file to verify safe skipping
        zf.writestr("readme.txt", "Some random notes")
    raw_zip = zip_buf.getvalue()

    vault = DocumentVaultService()
    ingested_children = vault.ingest(
        tenant_id=vault_setup["tenant_id"],
        matter_id=vault_setup["matter_id"],
        user_id=vault_setup["user_id"],
        filename="exhibits_bundle.zip",
        raw_bytes=raw_zip,
        doc_type="EVIDENCE",
        provenance="CLIENT",
        trust_label="TENANT_CLIENT_DOC",
        privilege_class="ATTORNEY_CLIENT",
        stage="EVIDENCE",
    )

    assert len(ingested_children) == 2
    family_id = ingested_children[0].family_id
    assert family_id is not None
    assert ingested_children[1].family_id == family_id
    assert ingested_children[0].stage == "EVIDENCE"
    assert ingested_children[1].stage == "EVIDENCE"


def test_hidden_text_flagged(vault_setup: dict[str, str]) -> None:
    """Non-negotiable 6: Untrusted documents with hidden text must be FLAGGED in gate."""
    hidden_pdf_path = REPO_ROOT / "eval" / "fixtures" / "synthetic" / "hidden_text_adversarial.pdf"
    assert hidden_pdf_path.exists(), f"Missing fixture {hidden_pdf_path}"

    raw_bytes = hidden_pdf_path.read_bytes()
    vault = DocumentVaultService()

    pdocs = vault.ingest(
        tenant_id=vault_setup["tenant_id"],
        matter_id=vault_setup["matter_id"],
        user_id=vault_setup["user_id"],
        filename="hidden_text_adversarial.pdf",
        raw_bytes=raw_bytes,
        doc_type="NOTICE",
        provenance="OPPONENT",
        trust_label="TENANT_OPPOSING_DOC",
        privilege_class="UNPRIVILEGED",
        stage="NOTICE",
    )

    pdoc = pdocs[0]
    with admin_db_context():
        pver = PdocVersion.objects.get(pdoc_id=pdoc.pdoc_id, pver="v1")
        assert pver.gate == "FLAGGED", f"Expected FLAGGED gate for adversarial hidden text, got {pver.gate}"
