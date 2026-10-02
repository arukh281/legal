"""End-to-end parsing pipeline for documents (P1).

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.1 (Pipeline DAG)
- docs/01_master_architecture.md §7.1 (ParsedDocument)
- User Directives #1 to #10
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog

from anchor_lib.ids import mint_id
from parse.anchors import AlignedAnchorNode, AnchorAssigner
from parse.gates import QualityEvaluation, QualityGate
from parse.judgment import ExtractedHeader, JudgmentParser
from parse.storage import ParsedDocStorage
from parse.triage import DocumentTriager

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class PipelineResult:
    parse_id: str
    work_id: str
    case_id: str | None
    expression_key: str
    manifestation_id: str
    raw_ids: list[str]
    doc_type: str
    header: ExtractedHeader
    nodes: list[AlignedAnchorNode]
    quality: QualityEvaluation
    anchor_changes: dict[str, int]
    new_aliases: list[dict[str, Any]]
    tombstoned_anchors: list[dict[str, Any]]
    parsed_doc_uri: str
    parsed_doc_sha256: str
    parsed_doc: dict[str, Any]
    pipeline_version: str
    used_llm_fallback: bool


class ParsingPipeline:
    """Orchestrates triage, scan robustness, OCR, judgment parsing, anchors, and storage."""

    def __init__(
        self,
        triager: DocumentTriager | None = None,
        judgment_parser: JudgmentParser | None = None,
        anchor_assigner: AnchorAssigner | None = None,
        quality_gate: QualityGate | None = None,
        doc_storage: ParsedDocStorage | None = None,
    ) -> None:
        self.triager = triager or DocumentTriager()
        self.judgment_parser = judgment_parser or JudgmentParser()
        self.anchor_assigner = anchor_assigner or AnchorAssigner()
        self.quality_gate = quality_gate or QualityGate()
        self.doc_storage = doc_storage or ParsedDocStorage()

    def process(
        self,
        raw_bytes: bytes,
        *,
        raw_id: str = "raw_default",
        source_id: str = "src_ibbi",
        url: str = "",
        terms_ref: str = "",
        fetched_at: str = "",
        rights_class: str = "OFFICIAL",
        provenance_tier: str = "OFFICIAL_PRIMARY",
        source_metadata: dict[str, Any] | None = None,
        pipeline_version: str = "p1.parser@0.1.0|det_v1",
        existing_work_id: str | None = None,
        expression_key: str = "en",
        use_ocr_cache: bool = True,
    ) -> PipelineResult:
        """Execute parsing pipeline on raw bytes and upload ParsedDocument to S3."""
        # 1. Mint parse_id
        parse_id = mint_id("par")

        # 2. Triage & OCR
        triaged_pages = self.triager.triage_document(
            raw_bytes,
            raw_id=raw_id,
            mime_hint=source_metadata.get("mime", "") if source_metadata else "",
            use_ocr_cache=use_ocr_cache,
        )

        full_doc_text = "\n\n".join(p.full_text for p in triaged_pages)

        # Aggregate hidden text flags
        all_hidden_flags: set[str] = set()
        for p in triaged_pages:
            all_hidden_flags.update(p.hidden_flags)

        # 3. Judgment Parser (NCLT/NCLAT)
        parsed_judgment = self.judgment_parser.parse(
            triaged_pages,
            source_metadata=source_metadata,
            raw_full_text=full_doc_text,
        )
        header = parsed_judgment.header

        # 4. Identity Minting / Reuse
        work_id = existing_work_id or mint_id("wrk")
        case_id = mint_id("cas") if header.case_number else None
        manifestation_id = mint_id("man")

        # 5. Anchor Assignment & Stability Protocol (01 §5.5, 03_P1 §5.10)
        alignment_result = self.anchor_assigner.assign_anchors(
            parsed_judgment.blocks,
            work_id=work_id,
            expression_key=expression_key,
            full_doc_text=full_doc_text,
            parse_id=parse_id,
        )

        # 6. Quality Gate Evaluation (03_P1 §5.11, 04 §2.7)
        quality = self.quality_gate.evaluate(
            triaged_pages,
            header,
            alignment_result.nodes,
            sorted(all_hidden_flags),
        )

        # 7. Assemble ParsedDocument JSON (01 §7.1)
        now_iso = datetime.now(UTC).isoformat()
        parsed_doc: dict[str, Any] = {
            "parse_id": parse_id,
            "pipeline_version": pipeline_version,
            "parsed_at": now_iso,
            "ids": {
                "work_id": work_id,
                "case_ids": [case_id] if case_id else [],
                "expression_key": expression_key,
                "manifestation_id": manifestation_id,
                "raw_ids": [raw_id],
            },
            "doc_type": header.doc_type,
            "source": {
                "source_id": source_id,
                "url": url,
                "terms_ref": terms_ref,
                "fetched_at": fetched_at,
            },
            "pages": [
                {
                    "n": p.page_number,
                    "text_source": p.text_source,
                    "ocr_engines": ["tesseract"] if p.text_source == "OCR" else [],
                    "ocr_conf": p.ocr_conf,
                    "script": ["Latin"] if not p.is_lang_unsupported else ["Indic/Other"],
                    "source_type": p.source_type,
                    "rotation_applied": p.rotation_applied,
                    "dpi": p.dpi,
                    "image_uri": "",
                }
                for p in triaged_pages
            ],
            "metadata": {
                "court": {
                    "court_id": header.court_id,
                    "conf": 1.0,
                    "bench_name": header.bench_name,
                },
                "jurisdiction_kind": "TRIBUNAL" if "TRIBUNAL" in header.court_id else "COURT",
                "case_numbers": [
                    {
                        "raw": header.case_number,
                        "type": header.case_type,
                        "year": header.case_year,
                    }
                ],
                "decision_date": header.decision_date.isoformat() if header.decision_date else None,
                "coram": header.coram,
                "bench_strength": header.bench_strength,
                "opinions": parsed_judgment.opinions,
                "authoritative_expression_key": expression_key,
                "parties": header.parties,
                "advocates": [],
                "disposition": {
                    "label": header.doc_type,
                    "anchor_id": f"{work_id}/{expression_key}#ord"
                    if any(n.fragment == "ord" for n in alignment_result.nodes)
                    else "",
                    "conf": 0.9,
                },
                "field_provenance": {
                    "decision_date": ["DOCUMENT_HEADER"] if header.decision_date else [],
                    "case_number": ["DOCUMENT_HEADER"] if header.case_number else [],
                },
            },
            "nodes": [
                {
                    "anchor_id": n.anchor_id,
                    "node_type": n.node_type,
                    "number_as_printed": n.number_as_printed,
                    "numbering": n.numbering,
                    "lang": "en",
                    "aux_text": {},
                    "text": n.text,
                    "text_hash": n.text_hash,
                    "quote_selector": {
                        "prefix": n.quote_prefix,
                        "suffix": n.quote_suffix,
                    },
                    "spans": n.spans,
                    "ocr_conf": n.ocr_conf,
                    "is_handwriting": n.is_handwriting,
                    "children": [],
                }
                for n in alignment_result.nodes
            ],
            "citations": [],
            "statute_mentions": [],
            "entities": [],
            "amendment_instructions": [],
            "alignment": {
                "previous_parse_id": None,
                "records": alignment_result.new_aliases,
            },
            "quality": {
                "ocr_conf": quality.ocr_conf,
                "structure_conf": quality.structure_conf,
                "rr_mean_conf": 1.0,
                "lang": quality.lang,
                "critical_token_disagreements": quality.critical_token_disagreements,
                "citation_resolution_rate": quality.citation_resolution_rate,
                "gate": quality.gate,
                "gate_reasons": quality.gate_reasons,
                "hidden_text_flags": quality.hidden_text_flags,
            },
            "security": {
                "injection_signals": [],
                "hidden_text_detected": bool(all_hidden_flags),
                "sensitive_identity_flags": [],
                "unicode_anomalies": {},
                "active_content_stripped": [],
            },
        }

        # 8. Upload ParsedDocument to S3 first (Directive #5)
        parsed_doc_uri, parsed_doc_sha256 = self.doc_storage.upload_parsed_document(
            parsed_doc,
            work_id=work_id,
            expression_key=expression_key,
            parse_id=parse_id,
        )

        return PipelineResult(
            parse_id=parse_id,
            work_id=work_id,
            case_id=case_id,
            expression_key=expression_key,
            manifestation_id=manifestation_id,
            raw_ids=[raw_id],
            doc_type=header.doc_type,
            header=header,
            nodes=alignment_result.nodes,
            quality=quality,
            anchor_changes=alignment_result.anchor_changes,
            new_aliases=alignment_result.new_aliases,
            tombstoned_anchors=alignment_result.tombstoned_anchors,
            parsed_doc_uri=parsed_doc_uri,
            parsed_doc_sha256=parsed_doc_sha256,
            parsed_doc=parsed_doc,
            pipeline_version=pipeline_version,
            used_llm_fallback=parsed_judgment.used_llm_fallback,
        )

    run = process
