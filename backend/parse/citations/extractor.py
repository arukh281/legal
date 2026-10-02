"""Citation extractor over ParsedDocument anchors.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.8 (citation grammar)
- docs/01_master_architecture.md §5.4 (schemes & normalized forms), §7.1 (CitationMention)
- docs/mvp/03_data_model_and_contracts.md §3.4 (plc.citation_mention)
- S05b Directives:
  #2: Case numbers identify cases, not judgments.
  #3: court_hint: set only when citation itself states court, otherwise None.
  #6: Quality flags: degraded if ocr_conf < 0.80 or hidden text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from anchor_lib.ids import mint_id
from anchor_lib.selectors import QuoteSelector


@dataclass(slots=True)
class ExtractedCitation:
    """A citation mention extracted from an anchor."""

    mention_id: str
    raw_text: str
    anchor_id: str
    char_range: tuple[int, int]
    quote_selector: dict[str, str]
    mention_kind: str  # FULL | NEUTRAL | CASE_NUMBER
    scheme: str  # SCC | SCC_ONLINE | AIR | SCR | NEUTRAL_INSC | NEUTRAL_HC | CASE_NO
    normalized: str
    pin: dict[str, Any]
    court_hint: str | None = None
    date_hint: str | None = None
    temporal_check: str = "OK"  # OK | CITED_AFTER_CITING | UNKNOWN
    degraded_quality: bool = False
    quality_reasons: list[str] = field(default_factory=list)


# 1. SCC: (1978) 1 SCC 248 | (2014) 3 SCC (Cri) 449 | 1980 SCC (Cri) 580
RE_SCC = re.compile(
    r"\(?(?P<year>(?:19|20)\d{2})\)?\s*(?P<vol>\d{1,2})?\s*S\.?C\.?C\.?\s*(?:\((?P<series>Cri|L&S|Tax)\)\s*)?(?P<page>\d{1,5})",
    re.IGNORECASE,
)

# 2. SCC OnLine: 2024 SCC OnLine SC 123 | 2023 SCC OnLine NCLAT 456 | 2022 SCC OnLine Del 789
RE_SCC_ONLINE = re.compile(
    r"(?P<year>(?:19|20)\d{2})\s*SCC\s*OnLine\s*(?P<court>[A-Za-z&]+)\s*(?P<num>\d{1,6})",
    re.IGNORECASE,
)

# 3. AIR: AIR 1978 SC 597 | AIR 2020 SC 1234 | AIR 1999 Bom 123 | AIR 2025 Supreme Court 2431
RE_AIR = re.compile(
    r"AIR\s*(?P<year>(?:19|20)\d{2})\s*(?P<court>Supreme\s+Court|[A-Za-z]+)\s*(?P<page>\d{1,5})",
    re.IGNORECASE,
)

# 4. SCR: [1978] 2 SCR 621 | (1978) 2 SCR 621 | [2021] 13 S.C.R. 737
RE_SCR = re.compile(
    r"[\[\(](?P<year>(?:19|20)\d{2})[\]\)]\s*(?P<vol>\d{1,2})?\s*S\.?C\.?R\.?\s*(?P<page>\d{1,5})",
    re.IGNORECASE,
)

# 5. NEUTRAL_INSC: 2026 INSC 1046 | 2023 INSC 1
RE_INSC = re.compile(
    r"(?P<year>(?:19|20)\d{2})\s*INSC\s*(?P<num>\d{1,5})",
    re.IGNORECASE,
)

# 6. NEUTRAL_HC: 2023:DHC:1234 | 2022/DHC/1234 | 2024:BHC-OS:123 | 2023/MHC/1234 | 2026:CHC-AS:739-DB
RE_NEUTRAL_HC = re.compile(
    r"(?P<year>20\d{2})\s*(?P<sep>[:/])\s*(?P<code>[A-Za-z]{2,6}(?:-[A-Za-z0-9]{1,4})?)\s*(?P=sep)\s*(?P<num>\d{1,6})(?:-(?P<bench>DB|FB|SB))?",
    re.IGNORECASE,
)

# 7. NCLAT Case Numbers: Company Appeal (AT) (Insolvency) No. 188 of 2026 | Comp. App. (AT) (Ins) No. 123 of 2023
RE_NCLAT_APP = re.compile(
    r"(?:Company\s+Appeal|Comp\.?\s*App\.?)\s*\(AT\)\s*(?:\(Insolvency\)|\(Ins\.?\))?\s*(?:No\.?|Number)?\s*[-:]?\s*(?P<num>\d+)\s*(?:of|/)\s*(?P<year>(?:19|20)\d{2})",
    re.IGNORECASE,
)

# 8. NCLT Case Numbers: CP (IB) 188 of 2026 | CP (IB) No. 188/MB/2026 | Company Petition (IB) No. 149/2023
RE_NCLT_CP = re.compile(
    r"(?:C\.?P\.?|Company\s+Petition)\s*\(IB\)\s*(?:No\.?)?\s*[-:]?\s*(?P<num>\d+)(?:/(?P<bench>[A-Za-z]+))?(?:\s*(?:of|/)\s*(?P<year>(?:19|20)\d{2}))?",
    re.IGNORECASE,
)

# 9. General Case Numbers where court is explicitly mentioned:
# e.g. "Supreme Court Civil Appeal No. 123 of 2020", "Delhi High Court W.P.(C) 456/2021"
RE_EXPLICIT_COURT_CASE = re.compile(
    r"(?P<court_prefix>Supreme\s+Court|Delhi\s+High\s+Court|Bombay\s+High\s+Court|High\s+Court)\s+(?:in\s+)?(?P<type>Civil\s+Appeal|W\.?P\.?\s*\([A-Za-z]+\)|Special\s+Leave\s+Petition|SLP\s*\([A-Za-z]+\))\s*(?:No\.?)?\s*(?P<num>\d+)\s*(?:of|/)\s*(?P<year>(?:19|20)\d{2})",
    re.IGNORECASE,
)

# 10. Bare Case Numbers without court: e.g. "Civil Appeal No. 1234 of 2019", "W.P.(C) 5678/2021"
RE_BARE_CASE = re.compile(
    r"\b(?P<type>Civil\s+Appeal|W\.?P\.?\s*\([A-Za-z]+\)|Special\s+Leave\s+Petition|SLP\s*\([A-Za-z]+\))\s*(?:No\.?)?\s*(?P<num>\d+)\s*(?:of|/)\s*(?P<year>(?:19|20)\d{2})",
    re.IGNORECASE,
)

# Pinpoint pattern (trailing or nearby paragraph / page)
RE_PIN = re.compile(
    r"(?:,\s*|\s+)?(?:at\s+)?(?P<kind>para(?:graph)?s?|paras?\.?|¶|page|p\.?|pp\.?)\s*(?P<val>\d+(?:[–-]\d+)?)",
    re.IGNORECASE,
)

# High Court Neutral Code to Court ID mapping
HC_NEUTRAL_COURTS: dict[str, str] = {
    "DHC": "crt_IN_HC_DEL",
    "BHC": "crt_IN_HC_BOM",
    "MHC": "crt_IN_HC_MAD",
    "CHC": "crt_IN_HC_CAL",
    "PHHC": "crt_IN_HC_P&H",
    "AHC": "crt_IN_HC_ALL",
    "KHC": "crt_IN_HC_KAR",
    "KER": "crt_IN_HC_KER",
    "GHC": "crt_IN_HC_GUJ",
}

# SCC OnLine court code to Court ID mapping
SCC_ONLINE_COURTS: dict[str, str] = {
    "SC": "crt_IN_SC",
    "NCLAT": "crt_IN_NCLAT",
    "NCLT": "crt_IN_NCLT",
    "DEL": "crt_IN_HC_DEL",
    "BOM": "crt_IN_HC_BOM",
    "CAL": "crt_IN_HC_CAL",
    "MAD": "crt_IN_HC_MAD",
    "KAR": "crt_IN_HC_KAR",
    "KER": "crt_IN_HC_KER",
    "GUJ": "crt_IN_HC_GUJ",
    "ALL": "crt_IN_HC_ALL",
}

# AIR court code to Court ID mapping
AIR_COURTS: dict[str, str] = {
    "SC": "crt_IN_SC",
    "SUPREME COURT": "crt_IN_SC",
    "BOM": "crt_IN_HC_BOM",
    "BOMBAY": "crt_IN_HC_BOM",
    "DEL": "crt_IN_HC_DEL",
    "DELHI": "crt_IN_HC_DEL",
    "CAL": "crt_IN_HC_CAL",
    "CALCUTTA": "crt_IN_HC_CAL",
    "MAD": "crt_IN_HC_MAD",
    "MADRAS": "crt_IN_HC_MAD",
    "ALL": "crt_IN_HC_ALL",
    "ALLAHABAD": "crt_IN_HC_ALL",
    "KER": "crt_IN_HC_KER",
    "KERALA": "crt_IN_HC_KER",
    "KAR": "crt_IN_HC_KAR",
    "KANT": "crt_IN_HC_KAR",
    "KARNATAKA": "crt_IN_HC_KAR",
    "GUJ": "crt_IN_HC_GUJ",
    "GUJARAT": "crt_IN_HC_GUJ",
    "LAH": "crt_IN_HC_LAH",
    "LAHORE": "crt_IN_HC_LAH",
}

# NCLT bench code to Court ID mapping
NCLT_BENCH_COURTS: dict[str, str] = {
    "MB": "crt_IN_NCLT_MUM",
    "MUM": "crt_IN_NCLT_MUM",
    "PB": "crt_IN_NCLT_PB",
    "DEL": "crt_IN_NCLT_DEL",
    "ND": "crt_IN_NCLT_DEL",
    "CHD": "crt_IN_NCLT_CHD",
    "AHM": "crt_IN_NCLT_AHM",
    "CHE": "crt_IN_NCLT_CHE",
    "KOL": "crt_IN_NCLT_KOL",
    "HYD": "crt_IN_NCLT_HYD",
    "KOC": "crt_IN_NCLT_KOC",
    "CUT": "crt_IN_NCLT_CUT",
    "IND": "crt_IN_NCLT_IND",
}


def _extract_pinpoint(text: str, cite_end: int) -> tuple[dict[str, Any], int]:
    """Look for an adjacent pinpoint immediately following the citation match."""
    trailing_text = text[cite_end : cite_end + 32]
    match = RE_PIN.match(trailing_text)
    if not match:
        return {
            "kind": "NONE",
            "method": "UNRESOLVED",
            "confidence": 0.0,
        }, cite_end

    kind_raw = match.group("kind").lower()
    val = match.group("val")
    end_pos = cite_end + match.end()

    if "para" in kind_raw or "¶" in kind_raw:
        return {
            "kind": "PARA",
            "value": val,
            "cited_anchor": f"#p{val}",
            "method": "SAME_NUMBERING",
            "confidence": 0.99,
        }, end_pos

    return {
        "kind": "PAGE",
        "value": val,
        "cited_anchor": None,
        "method": "PAGE_SPAN_ALIGN",
        "confidence": 0.7,
    }, end_pos


def _check_temporal(cited_year: int | None, decision_date: date | None) -> str:
    """Validate temporal sanity: citing decision cannot cite a future publication."""
    if not cited_year or not decision_date:
        return "OK"
    if cited_year > decision_date.year:
        return "CITED_AFTER_CITING"
    return "OK"


def extract_citations_from_anchor(
    anchor_id: str,
    text: str,
    decision_date: date | None = None,
    ocr_conf: float = 1.0,
    is_hidden: bool = False,
) -> list[ExtractedCitation]:
    """Extract all case and reporter citations from an anchor's text."""
    citations: list[ExtractedCitation] = []
    matched_ranges: list[tuple[int, int]] = []

    # Quality degradation check (Directive #6)
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

    def _add_mention(
        raw_text: str,
        start: int,
        end: int,
        mention_kind: str,
        scheme: str,
        normalized: str,
        court_hint: str | None,
        year: int | None,
    ) -> None:
        if _overlaps(start, end):
            return

        pin, final_end = _extract_pinpoint(text, end)
        full_raw_text = text[start:final_end]
        matched_ranges.append((start, final_end))

        quote_sel = QuoteSelector.from_text(text, start, final_end, max_context=32)
        selector_dict = {
            "exact": quote_sel.exact,
            "prefix": quote_sel.prefix,
            "suffix": quote_sel.suffix,
        }

        temporal_status = _check_temporal(year, decision_date)

        citations.append(
            ExtractedCitation(
                mention_id=mint_id("cm"),
                raw_text=full_raw_text,
                anchor_id=anchor_id,
                char_range=(start, final_end),
                quote_selector=selector_dict,
                mention_kind=mention_kind,
                scheme=scheme,
                normalized=normalized,
                pin=pin,
                court_hint=court_hint,
                date_hint=str(year) if year else None,
                temporal_check=temporal_status,
                degraded_quality=degraded,
                quality_reasons=list(quality_reasons),
            )
        )

    # 1. NEUTRAL_INSC (Supreme Court Neutral Citation)
    for m in RE_INSC.finditer(text):
        y = int(m.group("year"))
        n = m.group("num")
        norm = f"{y} INSC {n}"
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "NEUTRAL",
            "NEUTRAL_INSC",
            norm,
            court_hint="crt_IN_SC",
            year=y,
        )

    # 2. NEUTRAL_HC (High Court Neutral Citation)
    for m in RE_NEUTRAL_HC.finditer(text):
        y = int(m.group("year"))
        code = m.group("code").upper()
        num = m.group("num")
        bench = m.group("bench")
        norm = f"{y}:{code}:{num}" + (f"-{bench.upper()}" if bench else "")
        chint = None
        base_code = code.split("-")[0]
        if base_code in HC_NEUTRAL_COURTS:
            chint = HC_NEUTRAL_COURTS[base_code]
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "NEUTRAL",
            "NEUTRAL_HC",
            norm,
            court_hint=chint,
            year=y,
        )

    # 3. SCC OnLine
    for m in RE_SCC_ONLINE.finditer(text):
        y = int(m.group("year"))
        court_code = m.group("court")
        num = m.group("num")
        norm = f"{y} SCC OnLine {court_code} {num}"
        chint = SCC_ONLINE_COURTS.get(court_code.upper())
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "FULL",
            "SCC_ONLINE",
            norm,
            court_hint=chint,
            year=y,
        )

    # 4. SCC
    for m in RE_SCC.finditer(text):
        y = int(m.group("year"))
        vol = m.group("vol") or ""
        series = m.group("series")
        page = m.group("page")
        if series:
            norm = f"({y}) {vol} SCC ({series}) {page}".replace("  ", " ")
        elif vol:
            norm = f"({y}) {vol} SCC {page}"
        else:
            norm = f"({y}) SCC {page}"
        # Directive 3: Never infer court from SCC -> court_hint = None
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "FULL",
            "SCC",
            norm,
            court_hint=None,
            year=y,
        )

    # 5. AIR
    for m in RE_AIR.finditer(text):
        y = int(m.group("year"))
        court_raw = m.group("court")
        page = m.group("page")
        court_key = court_raw.upper()
        if court_key in ("SC", "SUPREME COURT"):
            norm_court = "SC"
        elif court_key in ("BOM", "BOMBAY"):
            norm_court = "Bom"
        elif court_key in ("DEL", "DELHI"):
            norm_court = "Del"
        elif court_key in ("CAL", "CALCUTTA"):
            norm_court = "Cal"
        elif court_key in ("MAD", "MADRAS"):
            norm_court = "Mad"
        elif court_key in ("ALL", "ALLAHABAD"):
            norm_court = "All"
        elif court_key in ("LAH", "LAHORE"):
            norm_court = "Lah"
        else:
            norm_court = court_raw.capitalize()
        norm = f"AIR {y} {norm_court} {page}"
        chint = AIR_COURTS.get(court_key)
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "FULL",
            "AIR",
            norm,
            court_hint=chint,
            year=y,
        )

    # 6. SCR
    for m in RE_SCR.finditer(text):
        y = int(m.group("year"))
        vol = m.group("vol")
        page = m.group("page")
        vol_str = f" {vol}" if vol else ""
        norm = f"[{y}]{vol_str} SCR {page}"
        # Stated court in reporter name is SC
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "FULL",
            "SCR",
            norm,
            court_hint="crt_IN_SC",
            year=y,
        )

    # 7. NCLAT Appeal: Company Appeal (AT) (Insolvency) No. 188 of 2026
    for m in RE_NCLAT_APP.finditer(text):
        num = m.group("num")
        y = int(m.group("year"))
        norm = f"crt_IN_NCLAT|Company Appeal (AT) (Insolvency)|{num}|{y}"
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "CASE_NUMBER",
            "CASE_NO",
            norm,
            court_hint="crt_IN_NCLAT",
            year=y,
        )

    # 8. NCLT CP (IB): CP (IB) 188 of 2026 | CP (IB) No. 188/MB/2026
    for m in RE_NCLT_CP.finditer(text):
        num = m.group("num")
        bench = m.group("bench")
        y_str = m.group("year")
        year_num: int | None = int(y_str) if y_str else None
        nclt_court_hint: str | None = None
        if bench:
            nclt_court_hint = NCLT_BENCH_COURTS.get(bench.upper(), f"crt_IN_NCLT_{bench.upper()}")
        else:
            nclt_court_hint = "crt_IN_NCLT"

        norm = f"{nclt_court_hint}|CP (IB)|{num}|{year_num or ''}"
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "CASE_NUMBER",
            "CASE_NO",
            norm,
            court_hint=nclt_court_hint,
            year=year_num,
        )

    # 9. Case number with explicit court prefix (Directive 3):
    for m in RE_EXPLICIT_COURT_CASE.finditer(text):
        cpfx = m.group("court_prefix").lower()
        ctype = m.group("type")
        num = m.group("num")
        y = int(m.group("year"))
        chint = None
        if "supreme" in cpfx:
            chint = "crt_IN_SC"
        elif "delhi" in cpfx:
            chint = "crt_IN_HC_DEL"
        elif "bombay" in cpfx:
            chint = "crt_IN_HC_BOM"

        norm = f"{chint or ''}|{ctype}|{num}|{y}"
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "CASE_NUMBER",
            "CASE_NO",
            norm,
            court_hint=chint,
            year=y,
        )

    # 10. Bare case number without court: court_hint = None
    for m in RE_BARE_CASE.finditer(text):
        ctype = m.group("type")
        num = m.group("num")
        y = int(m.group("year"))
        # Directive 4: If court isn't stated, court_hint = None
        norm = f"|{ctype}|{num}|{y}"
        _add_mention(
            m.group(0),
            m.start(),
            m.end(),
            "CASE_NUMBER",
            "CASE_NO",
            norm,
            court_hint=None,
            year=y,
        )

    return citations
