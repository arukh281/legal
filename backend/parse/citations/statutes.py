"""Statute mention grammar, in-document definitions, and corpus provision resolution.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.8 (statute mentions & in-document definitions)
- docs/01_master_architecture.md §7.1 (StatuteMention interface)
- Non-negotiable #3: Never invent law. Corpus provisions only, else "not in MVP corpus".
- S05b Directive #5: Statute mentions live only inside ParsedDocument.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from anchor_lib.ids import mint_id
from anchor_lib.selectors import QuoteSelector
from parse.models import Anchor, Work


@dataclass(slots=True)
class ExtractedStatuteMention:
    """A statute mention extracted from an anchor."""

    mention_id: str  # sm_
    anchor_id: str
    raw_text: str
    act_raw: str
    act_work_id: str | None
    provisions: list[dict[str, str]]  # [{"raw": "Section 7", "anchor": "sec-7"}]
    as_cited_date: str
    pit_rule: (
        str  # AS_CITED | EVENT_DATE_UNDER_SAVINGS | LAST_IN_FORCE_BEFORE_REPEAL | NO_EXPRESSION
    )
    resolved_anchor_ids: list[str]
    resolution_status: str  # RESOLVED | not in MVP corpus
    quote_selector: dict[str, str]
    conf: float = 1.0
    degraded_quality: bool = False
    quality_reasons: list[str] = field(default_factory=list)


# Known Act Acronyms -> Canonical Act Names
ACT_ACRONYMS: dict[str, str] = {
    "IBC": "Insolvency and Bankruptcy Code, 2016",
    "I&B CODE": "Insolvency and Bankruptcy Code, 2016",
    "THE CODE": "Insolvency and Bankruptcy Code, 2016",
    "CODE": "Insolvency and Bankruptcy Code, 2016",
    "COMPANIES ACT": "Companies Act, 2013",
    "COMPANIES ACT, 2013": "Companies Act, 2013",
    "THE ACT": "Insolvency and Bankruptcy Code, 2016",  # Default in insolvency tribunal orders unless defined otherwise
    "ACT": "Insolvency and Bankruptcy Code, 2016",
    "N.I. ACT": "Negotiable Instruments Act, 1881",
    "NI ACT": "Negotiable Instruments Act, 1881",
    "NEGOTIABLE INSTRUMENTS ACT": "Negotiable Instruments Act, 1881",
    "CPC": "Code of Civil Procedure, 1908",
    "CODE OF CIVIL PROCEDURE": "Code of Civil Procedure, 1908",
    "CRPC": "Code of Criminal Procedure, 1973",
    "CR.P.C.": "Code of Criminal Procedure, 1973",
    "CONSTITUTION": "Constitution of India",
    "CONSTITUTION OF INDIA": "Constitution of India",
}

# Regex to detect in-document definitions in header / early paras
RE_IN_DOC_DEF = re.compile(
    r"(?P<act_full>[A-Za-z\s,]+(?:Act|Code|Rules|Regulations)(?:,\s*\d{4})?)\s*\((?:hereinafter\s+(?:(?:referred\s+to\s+as|called)\s+)?(?:the\s+)?[\'\"]?(?P<alias1>[A-Za-z\s]+?)[\'\"]?|[\'\"](?P<alias2>[A-Za-z\s]+)[\'\"])\)",
    re.IGNORECASE,
)

# Regex for sections: Section 7 | Sec. 7 | S. 7 | s. 7 | u/s 7 | Sections 7 and 9
RE_STATUTE_SECTION = re.compile(
    r"\b(?:under\s+)?(?P<prefix>Section|Sec\.?|S\.|s\.|u/s|U/s|Sections|Ss\.)\s*(?P<sec>\d+[A-Za-z]?)(?:\s*\((?P<subsec>\d+[a-z]?)\))*(?:\s*\((?P<clause>[a-z]+)\))*\s*(?:of\s+(?:the\s+)?)?(?P<act>IBC|I&B\s+Code|Insolvency\s+and\s+Bankruptcy\s+Code(?:\s*,\s*2016)?|Code|Companies\s+Act(?:\s*,\s*2013)?|Act|N\.?I\.?\s*Act|Negotiable\s+Instruments\s+Act|CPC|Code\s+of\s+Civil\s+Procedure|Cr\.?P\.?C\.?|Constitution(?:\s+of\s+India)?)?",
    re.IGNORECASE,
)

# Regex for articles: Article 141 | Art. 136 | Article 226
RE_STATUTE_ARTICLE = re.compile(
    r"\b(?P<prefix>Article|Art\.)\s*(?P<art>\d+[A-Za-z]?)(?:\s*\((?P<clause>\d+[a-z]?)\))*\s*(?:of\s+(?:the\s+)?)?(?P<act>Constitution(?:\s+of\s+India)?)?",
    re.IGNORECASE,
)

# Regex for rules and regulations: Rule 11 | Regulation 30
RE_STATUTE_RULE = re.compile(
    r"\b(?P<prefix>Rule|Regulation)\s*(?P<num>\d+[A-Za-z]?)(?:\s*\((?P<subnum>\d+[a-z]?)\))*\s*(?:of\s+(?:the\s+)?)?(?P<act>[A-Za-z\s,]+(?:Rules|Regulations)(?:,\s*\d{4})?)?",
    re.IGNORECASE,
)


def extract_in_document_definitions(text: str) -> dict[str, str]:
    """Extract document-local definitions such as 'hereinafter referred to as the Code'."""
    definitions: dict[str, str] = {}
    for m in RE_IN_DOC_DEF.finditer(text):
        full_act = m.group("act_full").strip()
        alias = (m.group("alias1") or m.group("alias2") or "").strip()
        if full_act and alias:
            alias_key = alias.strip().upper()
            if alias_key.startswith("THE "):
                alias_key = alias_key[4:].strip()
            definitions[alias_key] = full_act
    return definitions


def resolve_provision_in_corpus(
    act_canonical_name: str,
    provision_frag: str,
    as_cited_date: str,
) -> tuple[str | None, list[str], str]:
    """Resolve provision against corpus. Strictly out of corpus means 'not in MVP corpus'.

    Never invents law. Returns (act_work_id, resolved_anchor_ids, status).
    """
    act_work = Work.objects.filter(
        work_type="ACT",
        title__iexact=act_canonical_name,
    ).first()

    if not act_work:
        return None, [], "not in MVP corpus"

    anchor_pattern = f"{act_work.work_id}#{provision_frag}"
    matching_anchor = Anchor.objects.filter(anchor_id__startswith=anchor_pattern).first()

    if not matching_anchor:
        return act_work.work_id, [], "not in MVP corpus"

    pit_anchor = f"{act_work.work_id}#{provision_frag}@{as_cited_date}"
    return act_work.work_id, [pit_anchor], "RESOLVED"


def extract_statute_mentions_from_anchor(
    anchor_id: str,
    text: str,
    decision_date: date | None = None,
    document_definitions: dict[str, str] | None = None,
    ocr_conf: float = 1.0,
    is_hidden: bool = False,
) -> list[ExtractedStatuteMention]:
    """Extract statute mentions from an anchor and attempt corpus resolution."""
    mentions: list[ExtractedStatuteMention] = []
    as_cited_str = decision_date.isoformat() if decision_date else date.today().isoformat()
    matched_ranges: list[tuple[int, int]] = []

    doc_defs = document_definitions or {}

    degraded = False
    quality_reasons: list[str] = []
    if ocr_conf < 0.80:
        degraded = True
        quality_reasons.append("LOW_OCR_CONF")
    if is_hidden:
        degraded = True
        quality_reasons.append("HIDDEN_TEXT")

    def _overlaps(start: int, end: int) -> bool:
        for s, e in matched_ranges:
            if max(start, s) < min(end, e):
                return True
        return False

    # 1. Sections
    for m in RE_STATUTE_SECTION.finditer(text):
        start, end = m.start(), m.end()
        if _overlaps(start, end):
            continue

        raw = m.group(0).strip()
        sec = m.group("sec")
        subsec = m.group("subsec")
        clause = m.group("clause")
        act_raw = m.group("act") or ""

        # Normalize provision fragment: sec-7 or sec-7.1
        frag = f"sec-{sec}"
        if subsec:
            frag += f".{subsec}"
        if clause:
            frag += f".{clause}"

        # Resolve Act Name
        act_canonical = "Insolvency and Bankruptcy Code, 2016"  # default in IBC orders
        if act_raw:
            act_clean = act_raw.strip().upper()
            if act_clean in doc_defs:
                act_canonical = doc_defs[act_clean]
            elif act_clean in ACT_ACRONYMS:
                act_canonical = ACT_ACRONYMS[act_clean]
            else:
                act_canonical = act_raw.strip()

        act_work_id, resolved_ids, status = resolve_provision_in_corpus(
            act_canonical, frag, as_cited_str
        )

        quote_sel = QuoteSelector.from_text(text, start, end, max_context=32)
        selector_dict = {
            "exact": quote_sel.exact,
            "prefix": quote_sel.prefix,
            "suffix": quote_sel.suffix,
        }

        matched_ranges.append((start, end))
        mentions.append(
            ExtractedStatuteMention(
                mention_id=mint_id("sm"),
                anchor_id=anchor_id,
                raw_text=raw,
                act_raw=act_canonical,
                act_work_id=act_work_id,
                provisions=[{"raw": f"Section {sec}", "anchor": frag}],
                as_cited_date=as_cited_str,
                pit_rule="AS_CITED" if status == "RESOLVED" else "NO_EXPRESSION",
                resolved_anchor_ids=resolved_ids,
                resolution_status=status,
                quote_selector=selector_dict,
                conf=1.0 if status == "RESOLVED" else 0.5,
                degraded_quality=degraded,
                quality_reasons=list(quality_reasons),
            )
        )

    # 2. Articles
    for m in RE_STATUTE_ARTICLE.finditer(text):
        start, end = m.start(), m.end()
        if _overlaps(start, end):
            continue

        raw = m.group(0).strip()
        art = m.group("art")
        clause = m.group("clause")
        frag = f"art-{art}" + (f".{clause}" if clause else "")
        act_canonical = "Constitution of India"

        act_work_id, resolved_ids, status = resolve_provision_in_corpus(
            act_canonical, frag, as_cited_str
        )

        quote_sel = QuoteSelector.from_text(text, start, end, max_context=32)
        selector_dict = {
            "exact": quote_sel.exact,
            "prefix": quote_sel.prefix,
            "suffix": quote_sel.suffix,
        }

        matched_ranges.append((start, end))
        mentions.append(
            ExtractedStatuteMention(
                mention_id=mint_id("sm"),
                anchor_id=anchor_id,
                raw_text=raw,
                act_raw="Constitution of India",
                act_work_id=act_work_id,
                provisions=[{"raw": f"Article {art}", "anchor": frag}],
                as_cited_date=as_cited_str,
                pit_rule="AS_CITED" if status == "RESOLVED" else "NO_EXPRESSION",
                resolved_anchor_ids=resolved_ids,
                resolution_status=status,
                quote_selector=selector_dict,
                conf=1.0 if status == "RESOLVED" else 0.5,
                degraded_quality=degraded,
                quality_reasons=list(quality_reasons),
            )
        )

    return mentions
