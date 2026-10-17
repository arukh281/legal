"""Tenant document vault: magic-byte detection, storage, and private anchor parsing.

Normative sources:
- Session R1: the client file (clients, matters, document vault)
- docs/mvp/03_data_model_and_contracts.md §3.4, §3.9
- docs/mvp/04_stack_and_infra.md §2.9
- AGENTS.md §4 item 1, 6 (full fidelity private anchors, untrusted documents are data, hidden-text flags)
"""

from __future__ import annotations

import email
import gzip
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.client import Config
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from anchor_lib.anchors import parse as parse_anchor
from anchor_lib.ids import mint_id
from parse.triage import DocumentTriager
from workspace.audit import record_audit_event
from workspace.db import tenant_db_context
from workspace.models import Pdoc


class VaultStorage:
    """Storage client for raw and parsed tenant documents in S3 / MinIO."""

    def __init__(
        self,
        *,
        endpoint_url: str | None = None,
        bucket_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url or getattr(
            settings, "S3_ENDPOINT_URL", "http://localhost:9000"
        )
        self.bucket_name = bucket_name or getattr(
            settings, "S3_TENANT_BUCKET", "tpl-vault"
        )
        self.access_key = access_key or getattr(
            settings, "S3_ACCESS_KEY_ID", "minioadmin"
        )
        self.secret_key = secret_key or getattr(
            settings, "S3_SECRET_ACCESS_KEY", "minioadmin"
        )
        self.region = region or getattr(settings, "S3_REGION", "ap-south-1")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version="s3v4"),
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            try:
                self._client.create_bucket(Bucket=self.bucket_name)
            except Exception:
                pass

    def store_raw(
        self, tenant_id: str, matter_id: str, raw_sha256: str, raw_bytes: bytes, mime: str
    ) -> str:
        """Store immutable raw bytes in tenant bucket at tpl/{tenant}/{matter}/raw/{sha256}."""
        key = f"tpl/{tenant_id}/{matter_id}/raw/{raw_sha256}"
        client = self._get_client()
        client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=raw_bytes,
            ContentType=mime,
        )
        return f"s3://{self.bucket_name}/{key}"

    def get_raw(self, storage_uri: str) -> bytes:
        """Fetch raw bytes from S3 storage URI."""
        client = self._get_client()
        # Parse s3://bucket/key
        if storage_uri.startswith("s3://"):
            parts = storage_uri[5:].split("/", 1)
            bucket = parts[0]
            key = parts[1]
        else:
            bucket = str(self.bucket_name)
            key = storage_uri
        response = client.get_object(Bucket=bucket, Key=key)
        raw_body: bytes = response["Body"].read()
        return raw_body

    def store_parsed_doc(
        self,
        tenant_id: str,
        matter_id: str,
        pdoc_id: str,
        pver: str,
        parsed_doc: dict[str, Any],
    ) -> str:
        """Store gzip-compressed ParsedDocument at tpl/{tenant}/{matter}/parsed/{pdoc_id}/{pver}.json.gz."""
        key = f"tpl/{tenant_id}/{matter_id}/parsed/{pdoc_id}/{pver}.json.gz"
        raw_json_bytes = json.dumps(parsed_doc, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        compressed = gzip.compress(raw_json_bytes)
        client = self._get_client()
        client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=compressed,
            ContentType="application/json",
            ContentEncoding="gzip",
        )
        return f"s3://{self.bucket_name}/{key}"


def detect_file_type(raw_bytes: bytes) -> tuple[str, str]:
    """Detect file mime type and format strictly by magic bytes.

    Accepts only PDF, DOCX, EML, and ZIP.
    Returns (mime_type, format_name: "PDF" | "DOCX" | "EML" | "ZIP").
    Raises ValueError for any other file type.
    """
    if not raw_bytes:
        raise ValueError("Cannot ingest empty file (0 bytes).")

    # 1. PDF: starts with %PDF-
    if raw_bytes.startswith(b"%PDF-"):
        return "application/pdf", "PDF"

    # 2. PKZip archives: starts with PK\x03\x04, PK\x05\x06, or PK\x07\x08
    if raw_bytes.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                namelist = zf.namelist()
                # DOCX check: word/document.xml or [Content_Types].xml with word
                if "word/document.xml" in namelist:
                    return (
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "DOCX",
                    )
                return "application/zip", "ZIP"
        except zipfile.BadZipFile as e:
            raise ValueError(f"Corrupt or unreadable zip archive: {e}") from e

    # 3. EML (RFC 822/5322): ASCII/UTF-8 email headers
    # Look for common header tokens at the start
    head_sample = raw_bytes[:1024]
    try:
        text_sample = head_sample.decode("utf-8", errors="replace")
        lines = [line.strip() for line in text_sample.splitlines() if line.strip()]
        header_patterns = (
            "from:",
            "to:",
            "subject:",
            "date:",
            "message-id:",
            "mime-version:",
            "received:",
            "content-type:",
            "return-path:",
            "delivered-to:",
        )
        # Check if any of the first few lines start with standard email headers
        has_email_header = False
        for line in lines[:8]:
            line_lower = line.lower()
            if any(line_lower.startswith(pat) for pat in header_patterns):
                has_email_header = True
                break

        if has_email_header:
            return "message/rfc822", "EML"
    except Exception:
        pass

    raise ValueError(
        "Unsupported file type. Document vault strictly accepts only PDF, DOCX, EML, and ZIP."
    )


@dataclass(slots=True)
class ParsedParagraph:
    text: str
    ocr_conf: float
    quote_prefix: str
    quote_suffix: str
    spans: list[dict[str, Any]]


def parse_docx_paragraphs(raw_bytes: bytes) -> tuple[list[ParsedParagraph], str]:
    """Extract paragraphs from DOCX document.xml."""
    paragraphs: list[ParsedParagraph] = []
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
        xml_content = zf.read("word/document.xml")
    root = ET.fromstring(xml_content)

    # Word XML namespaces
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    all_p = root.findall(".//w:p", ns)
    for p_elem in all_p:
        texts = [t.text for t in p_elem.findall(".//w:t", ns) if t.text]
        full_p_text = "".join(texts).strip()
        if full_p_text:
            paragraphs.append(
                ParsedParagraph(
                    text=full_p_text,
                    ocr_conf=1.0,
                    quote_prefix="",
                    quote_suffix="",
                    spans=[],
                )
            )

    return paragraphs, "PASS"


def parse_eml_paragraphs(raw_bytes: bytes) -> tuple[list[ParsedParagraph], str]:
    """Extract paragraphs from EML message."""
    msg = email.message_from_bytes(raw_bytes)
    paragraphs: list[ParsedParagraph] = []

    # Header summary as first paragraph
    hdr_lines: list[str] = []
    for h in ("Subject", "From", "To", "Date"):
        val = msg.get(h)
        if val:
            hdr_lines.append(f"{h}: {val}")
    if hdr_lines:
        paragraphs.append(
            ParsedParagraph(
                text="\n".join(hdr_lines),
                ocr_conf=1.0,
                quote_prefix="",
                quote_suffix="",
                spans=[],
            )
        )

    # Extract message body
    body_text = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disp:
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    body_text += payload.decode("utf-8", errors="replace") + "\n\n"
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            body_text = payload.decode("utf-8", errors="replace")

    # Split body on double newlines
    raw_paras = re.split(r"\n\s*\n", body_text)
    for p in raw_paras:
        p_clean = p.strip()
        if p_clean:
            paragraphs.append(
                ParsedParagraph(
                    text=p_clean,
                    ocr_conf=1.0,
                    quote_prefix="",
                    quote_suffix="",
                    spans=[],
                )
            )

    return paragraphs, "PASS"


def parse_pdf_paragraphs(
    raw_bytes: bytes, triager: DocumentTriager | None = None
) -> tuple[list[ParsedParagraph], str]:
    """Parse PDF through DocumentTriager, extracting paragraphs and checking hidden text."""
    if triager is None:
        triager = DocumentTriager()

    triaged_pages = triager.triage_document(raw_bytes)
    paragraphs: list[ParsedParagraph] = []

    has_hidden = False
    for p in triaged_pages:
        if p.hidden_flags:
            has_hidden = True

        # Group page text into paragraphs
        page_paras = re.split(r"\n\s*\n", p.full_text)
        for para in page_paras:
            para_clean = para.strip()
            if para_clean:
                paragraphs.append(
                    ParsedParagraph(
                        text=para_clean,
                        ocr_conf=float(p.ocr_conf),
                        quote_prefix="",
                        quote_suffix="",
                        spans=[],
                    )
                )

    gate = "FLAGGED" if has_hidden else "PASS"
    return paragraphs, gate


class DocumentVaultService:
    """Service for managing tenant document uploads, versions, and private anchors."""

    def __init__(
        self,
        storage: VaultStorage | None = None,
        triager: DocumentTriager | None = None,
    ) -> None:
        self.storage = storage or VaultStorage()
        self.triager = triager or DocumentTriager()

    def ingest(
        self,
        *,
        tenant_id: str,
        matter_id: str,
        user_id: str,
        filename: str,
        raw_bytes: bytes,
        doc_type: str,
        provenance: str,
        trust_label: str,
        privilege_class: str = "ATTORNEY_CLIENT",
        stage: str = "OTHER",
        title: str | None = None,
        pdoc_id: str | None = None,
        family_id: str | None = None,
        parent_pdoc_id: str | None = None,
    ) -> list[Pdoc]:
        """Ingest a document into the vault.

        If a ZIP is uploaded, expands 1 level and ingests each valid child document.
        Returns the list of created or updated Pdoc objects.
        """
        mime, doc_kind = detect_file_type(raw_bytes)

        # Handle ZIP expansion (1 level)
        if doc_kind == "ZIP":
            return self._expand_and_ingest_zip(
                tenant_id=tenant_id,
                matter_id=matter_id,
                user_id=user_id,
                filename=filename,
                zip_bytes=raw_bytes,
                doc_type=doc_type,
                provenance=provenance,
                trust_label=trust_label,
                privilege_class=privilege_class,
                stage=stage,
            )

        return [
            self._ingest_single_document(
                tenant_id=tenant_id,
                matter_id=matter_id,
                user_id=user_id,
                filename=filename,
                raw_bytes=raw_bytes,
                mime=mime,
                doc_kind=doc_kind,
                doc_type=doc_type,
                provenance=provenance,
                trust_label=trust_label,
                privilege_class=privilege_class,
                stage=stage,
                title=title,
                pdoc_id=pdoc_id,
                family_id=family_id,
                parent_pdoc_id=parent_pdoc_id,
            )
        ]

    def _expand_and_ingest_zip(
        self,
        *,
        tenant_id: str,
        matter_id: str,
        user_id: str,
        filename: str,
        zip_bytes: bytes,
        doc_type: str,
        provenance: str,
        trust_label: str,
        privilege_class: str,
        stage: str,
    ) -> list[Pdoc]:
        """Expand 1 level of ZIP archive and ingest children carrying family_id."""
        zip_family_id = mint_id("pdoc")
        ingested_pdocs: list[Pdoc] = []

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for item_info in zf.infolist():
                if item_info.is_dir():
                    continue
                name = item_info.filename
                # Exclude macOS resource fork artifacts
                if name.startswith("__MACOSX/") or "/." in name or name.startswith("."):
                    continue

                child_bytes = zf.read(item_info)
                if not child_bytes:
                    continue

                try:
                    child_mime, child_kind = detect_file_type(child_bytes)
                except ValueError:
                    # Non-supported child file type in zip; skip per specification
                    continue

                if child_kind == "ZIP":
                    # Single level expansion only
                    continue

                child_pdoc = self._ingest_single_document(
                    tenant_id=tenant_id,
                    matter_id=matter_id,
                    user_id=user_id,
                    filename=name,
                    raw_bytes=child_bytes,
                    mime=child_mime,
                    doc_kind=child_kind,
                    doc_type=doc_type,
                    provenance=provenance,
                    trust_label=trust_label,
                    privilege_class=privilege_class,
                    stage=stage,
                    title=name.split("/")[-1],
                    family_id=zip_family_id,
                )
                ingested_pdocs.append(child_pdoc)

        return ingested_pdocs

    def _ingest_single_document(
        self,
        *,
        tenant_id: str,
        matter_id: str,
        user_id: str,
        filename: str,
        raw_bytes: bytes,
        mime: str,
        doc_kind: str,
        doc_type: str,
        provenance: str,
        trust_label: str,
        privilege_class: str,
        stage: str,
        title: str | None = None,
        pdoc_id: str | None = None,
        family_id: str | None = None,
        parent_pdoc_id: str | None = None,
    ) -> Pdoc:
        """Ingest and parse a single document file into pdoc, pdoc_version, and private anchors."""
        raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        # 1. Store raw bytes immutable in S3
        storage_uri = self.storage.store_raw(
            tenant_id=tenant_id,
            matter_id=matter_id,
            raw_sha256=raw_sha256,
            raw_bytes=raw_bytes,
            mime=mime,
        )

        # 2. Determine pdoc_id and pver
        now = timezone.now()
        is_new_pdoc = pdoc_id is None
        if is_new_pdoc:
            pdoc_id = mint_id("pdoc")
            pver = "v1"
        else:
            assert pdoc_id is not None
            # Find existing versions to compute next vN
            with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT pver FROM tpl.pdoc_version WHERE tenant_id = %s AND pdoc_id = %s ORDER BY created_at ASC",
                        [tenant_id, pdoc_id],
                    )
                    existing_vers = [row[0] for row in cursor.fetchall()]
            if not existing_vers:
                pver = "v1"
            else:
                max_v = max(int(v.lstrip("v")) for v in existing_vers if v.startswith("v"))
                pver = f"v{max_v + 1}"

        # 3. Parse paragraphs according to doc_kind
        if doc_kind == "PDF":
            paragraphs, gate = parse_pdf_paragraphs(raw_bytes, self.triager)
        elif doc_kind == "DOCX":
            paragraphs, gate = parse_docx_paragraphs(raw_bytes)
        elif doc_kind == "EML":
            paragraphs, gate = parse_eml_paragraphs(raw_bytes)
        else:
            paragraphs, gate = [], "PASS"

        # 4. Generate private anchors
        anchors_data: list[dict[str, Any]] = []
        for idx, para in enumerate(paragraphs, start=1):
            frag = f"p{idx}"
            anchor_id = f"{pdoc_id}/{pver}#{frag}"
            # Validate anchor grammar
            parse_anchor(anchor_id)
            para_hash = hashlib.sha256(para.text.encode("utf-8")).hexdigest()

            # Context quote prefixes/suffixes
            quote_prefix = paragraphs[idx - 2].text[-32:] if idx > 1 else ""
            quote_suffix = paragraphs[idx].text[:32] if idx < len(paragraphs) else ""

            anchors_data.append(
                {
                    "anchor_id": anchor_id,
                    "fragment": frag,
                    "text": para.text,
                    "text_hash": para_hash,
                    "quote_prefix": quote_prefix,
                    "quote_suffix": quote_suffix,
                    "spans": para.spans,
                    "ocr_conf": para.ocr_conf,
                    "privilege_class": privilege_class,
                }
            )

        # 5. Store ParsedDocument JSON to S3
        parsed_doc_payload = {
            "pdoc_id": pdoc_id,
            "pver": pver,
            "raw_sha256": raw_sha256,
            "filename": filename,
            "mime": mime,
            "gate": gate,
            "paragraphs_count": len(paragraphs),
            "anchors": [a["anchor_id"] for a in anchors_data],
        }
        parsed_doc_uri = self.storage.store_parsed_doc(
            tenant_id=tenant_id,
            matter_id=matter_id,
            pdoc_id=pdoc_id,
            pver=pver,
            parsed_doc=parsed_doc_payload,
        )

        # 6. Database transaction under tenant context
        with tenant_db_context(tenant_id=tenant_id, user_id=user_id):
            with transaction.atomic():
                # Upsert or insert tpl.pdoc
                doc_title = title or filename
                if is_new_pdoc:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO tpl.pdoc (
                                tenant_id, matter_id, pdoc_id, family_id, parent_pdoc_id,
                                doc_type, provenance, trust_label, privilege_class,
                                privilege_state, stage, title, current_version, created_by, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            [
                                tenant_id,
                                matter_id,
                                pdoc_id,
                                family_id,
                                parent_pdoc_id,
                                doc_type,
                                provenance,
                                trust_label,
                                privilege_class,
                                "SUGGESTED",
                                stage,
                                doc_title,
                                pver,
                                user_id,
                                now,
                            ],
                        )
                else:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE tpl.pdoc
                            SET current_version = %s
                            WHERE tenant_id = %s AND pdoc_id = %s
                            """,
                            [pver, tenant_id, pdoc_id],
                        )

                # Insert tpl.pdoc_version
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tpl.pdoc_version (
                            tenant_id, pdoc_id, pver, raw_sha256, storage_uri,
                            mime, parsed_doc_uri, quality, gate, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            tenant_id,
                            pdoc_id,
                            pver,
                            raw_sha256,
                            storage_uri,
                            mime,
                            parsed_doc_uri,
                            json.dumps({"paragraphs": len(paragraphs)}),
                            gate,
                            now,
                        ],
                    )

                # Insert tpl.private_anchor rows
                for a in anchors_data:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO tpl.private_anchor (
                                tenant_id, anchor_id, pdoc_id, pver, rendition,
                                fragment, text, text_hash, quote_prefix, quote_suffix,
                                spans, ocr_conf, privilege_class
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            [
                                tenant_id,
                                a["anchor_id"],
                                pdoc_id,
                                pver,
                                None,
                                a["fragment"],
                                a["text"],
                                a["text_hash"],
                                a["quote_prefix"],
                                a["quote_suffix"],
                                json.dumps(a["spans"]),
                                a["ocr_conf"],
                                a["privilege_class"],
                            ],
                        )

                # Record audit event
                record_audit_event(
                    tenant_id=tenant_id,
                    actor=user_id,
                    action="DOCUMENT_UPLOAD",
                    object_ref=f"{pdoc_id}/{pver}",
                    matter_id=matter_id,
                    decision="ALLOW",
                    detail={
                        "filename": filename,
                        "pdoc_id": pdoc_id,
                        "pver": pver,
                        "sha256": raw_sha256,
                        "gate": gate,
                        "paragraphs": len(paragraphs),
                    },
                )

                # Fetch updated Pdoc
                pdoc = Pdoc.objects.get(tenant_id=tenant_id, pdoc_id=pdoc_id)
                return pdoc
