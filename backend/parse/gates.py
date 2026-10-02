"""Quality gate evaluation and review queue classification.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.11 (quality gates and review queues)
- docs/mvp/04_stack_and_infra.md §2.7 (ocr_conf < 0.80 flagged / excluded from tier-1 claims)
- DECISIONS.md (Session S05a): Doc-level gate bands proposal
"""

from __future__ import annotations

from dataclasses import dataclass

from parse.anchors import AlignedAnchorNode
from parse.judgment import ExtractedHeader
from parse.triage import TriagedPage


@dataclass(slots=True)
class QualityEvaluation:
    gate: str  # PASS | FLAGGED | QUARANTINED
    gate_reasons: list[str]
    ocr_conf: float
    structure_conf: float
    needs_review: bool
    hidden_text_flags: list[str]
    lang: list[str]
    critical_token_disagreements: int = 0
    citation_resolution_rate: float = 1.0


class QualityGate:
    """Evaluates document quality against 03_P1 §5.11 and 04 §2.7 thresholds."""

    def evaluate(
        self,
        pages: list[TriagedPage],
        header: ExtractedHeader,
        nodes: list[AlignedAnchorNode],
        hidden_flags: list[str],
    ) -> QualityEvaluation:
        reasons: list[str] = []

        # 1. OCR Confidence
        if pages:
            mean_ocr = round(sum(p.ocr_conf for p in pages) / len(pages), 4)
        else:
            mean_ocr = 0.0

        # Check for any page below 0.80
        low_ocr_pages = [p.page_number for p in pages if p.ocr_conf < 0.80]
        if low_ocr_pages:
            reasons.append(f"LOW_OCR_CONFIDENCE_PAGES_{low_ocr_pages}")

        # Check for non-Latin script pages
        unsupported_pages = [p.page_number for p in pages if p.is_lang_unsupported]
        if unsupported_pages:
            reasons.append(f"LANG_UNSUPPORTED_PAGES_{unsupported_pages}")

        # 2. Structure Confidence
        num_paras = sum(1 for n in nodes if n.node_type == "PARA")
        total_nodes = len(nodes)
        structure_conf = round(num_paras / max(1, total_nodes), 4) if total_nodes else 0.0

        if total_nodes == 0:
            reasons.append("NO_NODES_FOUND")
        elif num_paras == 0 and len(pages) >= 2:
            reasons.append("NO_NUMBERED_PARAGRAPHS")

        # 3. Header completeness
        if not header.decision_date:
            reasons.append("MISSING_DECISION_DATE")
        if not header.case_number or header.case_number == "ORDER":
            reasons.append("UNRESOLVED_CASE_NUMBER")

        # 4. Hidden text flags
        if hidden_flags:
            reasons.append(f"HIDDEN_TEXT_DETECTED: {','.join(hidden_flags)}")

        # 5. Handwriting presence
        has_hw = any(n.is_handwriting for n in nodes)
        if has_hw:
            reasons.append("HANDWRITING_PRESENT")

        # Gate determination
        gate = "PASS"
        if mean_ocr < 0.80 or "NO_NODES_FOUND" in reasons:
            gate = "QUARANTINED"
        elif mean_ocr < 0.95 or reasons or structure_conf < 0.50 or gate == "QUARANTINED":
            if gate != "QUARANTINED":
                gate = "FLAGGED"

        needs_review = gate != "PASS"
        lang = ["en"]
        if unsupported_pages:
            lang.append("und")

        return QualityEvaluation(
            gate=gate,
            gate_reasons=reasons,
            ocr_conf=mean_ocr,
            structure_conf=structure_conf,
            needs_review=needs_review,
            hidden_text_flags=hidden_flags,
            lang=lang,
        )
