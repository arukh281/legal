"""Consumer of raw.captured.v1 events and atomic persistence of ParsedDocument records.

Normative sources:
- docs/01_master_architecture.md §6.2, §6.3 (doc.parsed.v1 schema)
- docs/mvp/03_data_model_and_contracts.md §3.3 & §3.4
- User Directives:
  #1: topic = plc.doc.parsed.v1, lane in lane column
  #5: S3 upload first, then atomic DB transaction committing rows + outbox event
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from django.db import transaction

from ingest.models import Source
from ingest.storage import BlobStorage
from ops.outbox import publish_event, register_handler
from parse.models import (
    Anchor,
    AnchorAlias,
    Court,
    Expression,
    IdentifierAlias,
    LegalCase,
    Manifestation,
    ParseRun,
    Work,
    WorkCase,
)
from parse.pipeline import ParsingPipeline, PipelineResult

logger = structlog.get_logger(__name__)


def persist_pipeline_result(
    result: PipelineResult,
    *,
    source_id: str,
    raw_id: str,
    url: str,
    rights_class: str = "PUBLIC_DOMAIN",
    provenance_tier: str = "OFFICIAL_PORTAL",
    lane: str = "rt",
    supersedes_parse_id: str | None = None,
) -> str:
    """Atomically insert all DB rows (work, case, manifestation, parse_run, anchors)

    and emit doc.parsed.v1 to ops.event_outbox in the SAME transaction (Directive #5).
    """
    now = datetime.now(UTC)

    with transaction.atomic():
        # 1. Resolve or create Court
        court_obj, _ = Court.objects.get_or_create(
            court_id=result.header.court_id,
            defaults={
                "level": "TRIBUNAL_APPELLATE"
                if "APPELLATE" in result.header.court_id
                else ("TRIBUNAL" if "TRIBUNAL" in result.header.court_id else "SC"),
                "parent_ids": ["crt_IN_SC"] if "SC" not in result.header.court_id else [],
                "binding_scope_tags": ["ALL_INDIA"],
                "territory": "IN",
                "meta": {"name": result.header.bench_name or result.header.court_id},
            },
        )

        # 2. Resolve or create Work
        work_obj, _ = Work.objects.get_or_create(
            work_id=result.work_id,
            defaults={
                "work_type": result.doc_type,
                "status": "ACTIVE" if result.quality.gate == "PASS" else "PROVISIONAL",
                "court": court_obj,
                "decision_date": result.header.decision_date,
                "title": result.header.title,
                "bench_strength": result.header.bench_strength,
                "access_restriction": {},
                "integrity_flags": [],
            },
        )

        # 3. Resolve or create LegalCase if identifiable
        case_obj = None
        if result.header.case_number:
            norm_val = f"{court_obj.court_id}|{result.header.case_type}|{result.header.case_number}|{result.header.case_year or ''}"
            existing_alias = IdentifierAlias.objects.filter(
                scheme="CASE_NO",
                value_normalized=norm_val,
                status="ACTIVE",
            ).first()

            if existing_alias:
                case_obj = LegalCase.objects.filter(case_id=existing_alias.target_id).first()

            if not case_obj and result.case_id:
                case_obj, _ = LegalCase.objects.get_or_create(
                    case_id=result.case_id,
                    defaults={
                        "court": court_obj,
                        "case_type": result.header.case_type,
                        "number": result.header.case_number,
                        "year": result.header.case_year,
                        "status": "ACTIVE",
                    },
                )
                IdentifierAlias.objects.get_or_create(
                    scheme="CASE_NO",
                    value_normalized=norm_val,
                    defaults={
                        "target_id": case_obj.case_id,
                        "confidence": 1.0,
                        "source": "P1_DOCUMENT_HEADER",
                        "trust_tier": "T0",
                        "status": "ACTIVE",
                        "first_seen": now,
                        "evidence": {"raw_as_printed": result.header.case_number},
                    },
                )

            if case_obj:
                WorkCase.objects.get_or_create(
                    work=work_obj,
                    case=case_obj,
                    defaults={"role": "LEAD"},
                )

        # 4. Expression
        expr_obj, _ = Expression.objects.get_or_create(
            work=work_obj,
            expression_key=result.expression_key,
            defaults={
                "lang": "en",
                "rev": 1,
                "authoritative": True,
                "derived": False,
                "verification": "ROUNDTRIP_OK",
                "authority_basis": "ORIGINAL",
            },
        )

        # 5. Manifestation
        source_obj = Source.objects.filter(source_id=source_id).first()
        manif_obj, _ = Manifestation.objects.get_or_create(
            manifestation_id=result.manifestation_id,
            defaults={
                "work": work_obj,
                "expression_key": result.expression_key,
                "source": source_obj,
                "url": url,
                "raw_ids": result.raw_ids,
                "rights_class": rights_class,
                "provenance_tier": provenance_tier,
                "first_seen": now,
            },
        )

        # 6. ParseRun
        ParseRun.objects.update_or_create(
            parse_id=result.parse_id,
            defaults={
                "raw_ids": result.raw_ids,
                "manifestation": manif_obj,
                "work": work_obj,
                "work_id_status": "RESOLVED",
                "expression_key": result.expression_key,
                "doc_type": result.doc_type,
                "parsed_doc_uri": result.parsed_doc_uri,
                "parsed_doc_sha256": result.parsed_doc_sha256,
                "quality": {
                    "ocr_conf": result.quality.ocr_conf,
                    "structure_conf": result.quality.structure_conf,
                    "rr_mean_conf": 1.0,
                    "lang": result.quality.lang,
                    "gate": result.quality.gate,
                    "gate_reasons": result.quality.gate_reasons,
                    "hidden_text_flags": result.quality.hidden_text_flags,
                    "critical_token_disagreements": result.quality.critical_token_disagreements,
                    "citation_resolution_rate": result.quality.citation_resolution_rate,
                },
                "gate": result.quality.gate,
                "anchor_changes": result.anchor_changes,
                "supersedes_parse_id": supersedes_parse_id,
                "rights_class": rights_class,
                "provenance_tier": provenance_tier,
                "pipeline_version_id": result.pipeline_version,
                "cost_usd": None,
            },
        )

        # 7. Update tombstoned anchors if re-parsing
        for tr in result.tombstoned_anchors:
            Anchor.objects.filter(anchor_id=tr["anchor_id"]).update(
                state="TOMBSTONED",
                forward_to=tr.get("forward_to"),
            )

        # 8. Insert new Anchor rows
        for node in result.nodes:
            Anchor.objects.update_or_create(
                anchor_id=node.anchor_id,
                defaults={
                    "work": work_obj,
                    "expression_key": result.expression_key,
                    "fragment": node.fragment,
                    "node_type": node.node_type,
                    "number_as_printed": node.number_as_printed,
                    "numbering": node.numbering,
                    "text": node.text,
                    "text_hash": node.text_hash,
                    "quote_prefix": node.quote_prefix,
                    "quote_suffix": node.quote_suffix,
                    "spans": node.spans,
                    "ocr_conf": node.ocr_conf,
                    "lang": "en",
                    "is_authoritative_expression": True,
                    "state": node.state,
                    "forward_to": node.forward_to,
                    "first_parse_id": result.parse_id,
                    "last_parse_id": result.parse_id,
                },
            )

        # 9. Insert AnchorAlias rows
        for alias in result.new_aliases:
            AnchorAlias.objects.update_or_create(
                old_anchor=alias["old_anchor"],
                new_anchor=alias["new_anchor"],
                defaults={
                    "method": alias["method"],
                    "confidence": alias.get("confidence", 1.0),
                    "parse_id": result.parse_id,
                },
            )

        # 10. Emit doc.parsed.v1 event into ops.event_outbox (Directive #1 & 01 §6.3)
        doc_parsed_data = {
            "parse_id": result.parse_id,
            "raw_ids": result.raw_ids,
            "manifestation_id": result.manifestation_id,
            "work_id": result.work_id,
            "work_id_status": "RESOLVED",
            "case_id": case_obj.case_id if case_obj else None,
            "case_ids": [case_obj.case_id] if case_obj else [],
            "expression_key": result.expression_key,
            "doc_type": result.doc_type,
            "metadata": result.parsed_doc["metadata"],
            "parsed_doc_uri": result.parsed_doc_uri,
            "citations": [],
            "statute_mentions_count": 0,
            "quality": {
                "ocr_conf": result.quality.ocr_conf,
                "lang": result.quality.lang,
                "structure_conf": result.quality.structure_conf,
                "needs_review": result.quality.needs_review,
                "gate": result.quality.gate,
                "critical_token_disagreements": result.quality.critical_token_disagreements,
                "citation_resolution_rate": result.quality.citation_resolution_rate,
                "hidden_text_flags": result.quality.hidden_text_flags,
            },
            "supersedes_parse_id": supersedes_parse_id,
            "anchor_changes": result.anchor_changes,
            "rights_class": rights_class,
            "provenance_tier": provenance_tier,
            "pipeline_version": result.pipeline_version,
        }

        publish_event(
            event_type="doc.parsed.v1",
            source=f"p1/parser@{result.pipeline_version.split('|')[0].split('@')[-1]}",
            subject=f"{result.work_id}/{result.expression_key}",
            dataschema="schemareg://plc/doc.parsed.v1/1.0",
            dataclass="PUBLIC",
            idempotencykey=f"p1|parse|{result.work_id}|{result.expression_key}|{result.parsed_doc_sha256}|{result.pipeline_version}",
            schemaversion="1.0",
            data=doc_parsed_data,
            topic="plc.doc.parsed.v1",  # Directive #1: topic without .rt
            partition_key=result.work_id,
            lane=lane,  # Directive #1: lane in column
        )

    logger.info(
        "parsed_document_persisted",
        parse_id=result.parse_id,
        work_id=result.work_id,
        gate=result.quality.gate,
        nodes=len(result.nodes),
    )
    return result.parse_id


@register_handler("p1_parser", "raw.captured.v1")
def handle_raw_captured(event: dict[str, Any]) -> dict[str, Any]:
    """Consumer handler for raw.captured.v1 events (NEW and CHANGED only)."""
    data = event.get("data", {})
    change_kind = data.get("change_kind")
    if change_kind not in ("NEW", "CHANGED"):
        logger.info("parse_consumer_skipped_change_kind", change_kind=change_kind)
        return {"status": "SKIPPED", "reason": f"change_kind_{change_kind}"}

    raw_id = data.get("raw_id")
    if not raw_id:
        return {"status": "ERROR", "reason": "MISSING_RAW_ID"}

    # Fetch blob bytes from storage
    storage = BlobStorage()
    content_type = data.get("http", {}).get("content_type", "application/pdf")
    try:
        raw_bytes = storage.get_blob(raw_id, content_type=content_type)
    except Exception as e:
        logger.error("failed_to_fetch_raw_blob", raw_id=raw_id, error=str(e))
        return {"status": "ERROR", "reason": "RAW_BLOB_NOT_FOUND"}

    pipeline = ParsingPipeline()
    pipeline_res = pipeline.process(
        raw_bytes,
        raw_id=raw_id,
        source_id=data.get("source_id", "UNKNOWN"),
        url=data.get("url", ""),
        terms_ref=data.get("terms_ref", ""),
        fetched_at=data.get("fetched_at", ""),
        rights_class=data.get("rights_class", "OFFICIAL"),
        provenance_tier=data.get("provenance_tier", "OFFICIAL_PRIMARY"),
        source_metadata=data.get("source_metadata", {}),
    )

    parse_id = persist_pipeline_result(
        pipeline_res,
        source_id=data.get("source_id", "UNKNOWN"),
        raw_id=raw_id,
        url=data.get("url", ""),
        rights_class=data.get("rights_class", "OFFICIAL"),
        provenance_tier=data.get("provenance_tier", "OFFICIAL_PRIMARY"),
        lane=event.get("lane", "rt") or "rt",
    )

    return {"status": "SUCCESS", "parse_id": parse_id, "work_id": pipeline_res.work_id}
