"""Indian legal case-number parser, normalizer, and matcher.

Normative sources:
- Session R2 Directive: shared case-number normalizer across P0, P1, P2, P7.
- DECISIONS.md (2026-10-09: CP (IB) vs RCP (IB) strictly distinct).
- Session R2 Corrections:
  1. EXACT only when case type, number, year, and bench are all present and equal.
  2. Missing bench or missing year on either side yields PARTIAL (if type & number match).
  3. Bench mismatch or year mismatch yields NONE.
  4. Bench aliases mapped to canonical 3-letter codes (e.g. MB=MUM=Mumbai, ND=DEL=New Delhi).
  5. Applications like "IA 456/2026 in CP (IB) 123/MB/2026" match on parent case number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Canonical 3-letter bench code mapping
BENCH_ALIASES: dict[str, str] = {
    # Mumbai
    "MB": "MUM",
    "MUM": "MUM",
    "MUMBAI": "MUM",
    # New Delhi / Principal Bench
    "PB": "PB",
    "PRINCIPAL": "PB",
    "PRINCIPAL BENCH": "PB",
    "ND": "DEL",
    "DEL": "DEL",
    "DELHI": "DEL",
    "NEW DELHI": "DEL",
    # Ahmedabad
    "AHM": "AHM",
    "AHMEDABAD": "AHM",
    # Chandigarh
    "CHD": "CHD",
    "CHANDIGARH": "CHD",
    # Chennai
    "CHE": "CHE",
    "CHENNAI": "CHE",
    "MAS": "CHE",
    "MADRAS": "CHE",
    # Kolkata
    "KOL": "KOL",
    "KOLKATA": "KOL",
    "CAL": "KOL",
    "CALCUTTA": "KOL",
    # Hyderabad
    "HYD": "HYD",
    "HYDERABAD": "HYD",
    # Bengaluru
    "BLR": "BLR",
    "BENGALURU": "BLR",
    "BANGALORE": "BLR",
    "BNG": "BLR",
    # Cuttack
    "CUT": "CUT",
    "CUTTACK": "CUT",
    # Kochi
    "KOC": "KOC",
    "KOCHI": "KOC",
    "COCHIN": "KOC",
    # Indore
    "IND": "IND",
    "INDORE": "IND",
    # Allahabad
    "ALL": "ALL",
    "ALD": "ALL",
    "ALLAHABAD": "ALL",
    # Jaipur
    "JAI": "JAI",
    "JAIPUR": "JAI",
    # Guwahati
    "GWH": "GWH",
    "GUWAHATI": "GWH",
    # Amaravati
    "AMR": "AMR",
    "AMRAVATI": "AMR",
    "AMARAVATI": "AMR",
    # Kanpur
    "CNB": "CNB",
    "KANPUR": "CNB",
    # Nagpur
    "NGP": "NGP",
    "NAGPUR": "NGP",
}


STOPWORDS: frozenset[str] = frozenset(
    {"OF", "IN", "NO", "FOR", "AND", "AT", "THE", "TO", "ON", "BY", "ORDER", "ORDERS", "DAILY", "MATTER"}
)


def normalize_bench(raw_bench: str | None) -> str | None:
    """Normalize any bench string or alias to a canonical uppercase code."""
    if not raw_bench:
        return None
    cleaned = re.sub(r"[^A-Za-z\s]", " ", raw_bench).strip().upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return None
    if cleaned in STOPWORDS:
        return None
    # Direct alias match
    if cleaned in BENCH_ALIASES:
        return BENCH_ALIASES[cleaned]
    # Check words for match (e.g. "NCLT MUMBAI BENCH COURT 1" -> "MUM")
    words = cleaned.split()
    for w in words:
        if w not in STOPWORDS and w in BENCH_ALIASES:
            return BENCH_ALIASES[w]
    # Check multi-word phrase
    for k, v in BENCH_ALIASES.items():
        if k in cleaned:
            return v
    return None


@dataclass(frozen=True, slots=True)
class NormalizedCaseNumber:
    """Structured representation of a parsed and normalized Indian case number."""

    raw: str
    case_type: str
    case_number: str
    year: int | None
    bench: str | None
    canonical: str
    parseable: bool = True
    parent_case_type: str | None = None
    parent_case_number: str | None = None
    parent_year: int | None = None
    parent_bench: str | None = None

    @property
    def parent(self) -> NormalizedCaseNumber | None:
        """Return parent case number if this is an application/motion in a parent case."""
        if not self.parent_case_type or not self.parent_case_number:
            return None
        canon_parts = [self.parent_case_type, self.parent_case_number]
        if self.parent_bench:
            canon_parts.append(self.parent_bench)
        if self.parent_year:
            canon_parts.append(str(self.parent_year))
        return NormalizedCaseNumber(
            raw=f"{self.parent_case_type} {self.parent_case_number}",
            case_type=self.parent_case_type,
            case_number=self.parent_case_number,
            year=self.parent_year,
            bench=self.parent_bench,
            canonical="/".join(canon_parts[:2])
            + (f"/{self.parent_bench}" if self.parent_bench else "")
            + (f"/{self.parent_year}" if self.parent_year else ""),
            parseable=True,
        )


# Pre-compiled regex patterns for case numbers
# Note: RCP (IB) MUST precede CP (IB)
RE_RCP_IB = re.compile(
    r"\b(?:R\.?C\.?P\.?|Restoration\s+(?:Company\s+)?Petition)\s*\(IB\)[/\s-]*(?:No\.?)?\s*(?P<num>\d+)"
    r"(?:[/\s]+(?P<subnum>\d+))?"
    r"(?:[/\s(]+(?P<bench>[A-Za-z]{2,15})(?:/[A-Za-z]+)*[/\s)]*)?"
    r"(?:\s+of\s+|[/\s-]|\bin\b)*(?P<year>\d{4})?\b",
    re.IGNORECASE,
)

RE_CP_IB = re.compile(
    r"\b(?:C\.?P\.?|Company\s+Petition)\s*\(IB\)[/\s-]*(?:No\.?)?\s*(?P<num>\d+)"
    r"(?:[/\s]+(?P<subnum>\d+))?"
    r"(?:[/\s(]+(?P<bench>[A-Za-z]{2,15})(?:/[A-Za-z]+)*[/\s)]*)?"
    r"(?:\s+of\s+|[/\s-]|\bin\b)*(?P<year>\d{4})?\b",
    re.IGNORECASE,
)

# NCLAT Appeals
RE_NCLAT_APP = re.compile(
    r"\bCompany\s+Appeal\s*\(AT\)\s*(?:\((?P<sector>Insolvency|Competition|[A-Za-z\s]+)\)\s*)?(?:No\.?)?\s*(?P<num>\d+)\s*(?:of|/|-)\s*(?P<year>\d{4})?\b",
    re.IGNORECASE,
)

RE_COMPETITION_APP = re.compile(
    r"\bCompetition\s+Appeal\s*\(AT\)\s*(?:No\.?)?\s*(?P<num>\d+)\s*(?:of|/|-)\s*(?P<year>\d{4})?\b",
    re.IGNORECASE,
)

# Interlocutory / Company Applications: IA (IBC) 123/2024 or IA 123/MB/2024, CONT.A, COMP.APPL, MA, IVN.P, EP
RE_APPLICATION = re.compile(
    r"\b(?P<app_type>I\.?A\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*|C\.?A\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*|M\.?A\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*|IVN\.?P\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*|CONT\.?A\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*|COMP\.?APPL\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*|E\.?P\.?(?:\s*\([A-Za-z.\s\(\)-]+\))*)\s*(?:No\.?)?[/\s-]*(?P<num>\d+)"
    r"(?:[/\s]+(?P<subnum>\d+))?"
    r"(?:[/\s(]+(?P<bench>[A-Za-z]{2,15})(?:/[A-Za-z]+)*[/\s)]*)?"
    r"(?:\s+of\s+|[/\s-]|\bin\b)*(?P<year>\d{4})?\b",
    re.IGNORECASE,
)

# General High Court / Civil Court pattern: W.P.(C) 1234/2024, CS (COMM) 101/2023
RE_GENERAL_COURT = re.compile(
    r"\b(?P<type>[A-Za-z.\s\(\)-]+?)\s*(?:No\.?)?\s*(?P<num>\d+)\s*(?:of|/|-)\s*(?P<year>\d{4})\b",
    re.IGNORECASE,
)


def _clean_case_type(raw_type: str) -> str:
    """Normalize whitespace and punctuation in case type strings."""
    t = raw_type.strip().upper()
    t = re.sub(r"\s+", " ", t)
    # Standardize common abbreviations
    if "REST" in t and "IB" in t:
        return "RCP (IB)"
    if "RCP" in t and "IB" in t:
        return "RCP (IB)"
    if "CP" in t and "IB" in t:
        return "CP (IB)"
    if "INSOLVENCY" in t and "AT" in t:
        return "Company Appeal (AT) (Insolvency)"
    if "COMPETITION" in t and "AT" in t:
        return "Competition Appeal (AT)"
    if "COMPANY APPEAL" in t and "AT" in t:
        return "Company Appeal (AT)"
    if "CONT" in t:
        return "CONT.A"
    if "COMP" in t and "APPL" in t:
        return "COMP.APPL"
    if "IVN" in t:
        return "IVN.P"
    if "EP" in t or "E.P" in t:
        return "EP"
    if "MA" in t or "M.A" in t:
        return "MA"
    if "I.A" in t or "IA" in t:
        return "IA"
    if "C.A" in t or "CA" in t:
        return "CA"
    return t


def normalize_case_number(
    text: str,
    default_bench: str | None = None,
    parent_case: str | None = None,
) -> NormalizedCaseNumber:
    """Parse, standardize, and canonicalize a case number string.

    Handles:
    - Parent cases: "IA 456/2026 in CP (IB) 123/MB/2026"
    - Strict CP (IB) vs RCP (IB) separation
    - Bench alias mapping (MB -> MUM)
    - Year validation
    """
    raw_stripped = text.strip()
    if not raw_stripped:
        return NormalizedCaseNumber(
            raw=text,
            case_type="UNKNOWN",
            case_number="",
            year=None,
            bench=normalize_bench(default_bench),
            canonical="",
            parseable=False,
        )

    # 1. Check for compound application syntax: "<App> in <ParentCase>"
    parent_type: str | None = None
    parent_num: str | None = None
    parent_year: int | None = None
    parent_bench: str | None = None

    main_text = raw_stripped
    in_split = re.split(r"\s+\bin\b\s+", raw_stripped, maxsplit=1, flags=re.IGNORECASE)
    if len(in_split) == 2:
        app_part, parent_part = in_split[0].strip(), in_split[1].strip()
        parsed_parent = normalize_case_number(parent_part, default_bench=default_bench)
        if parsed_parent.parseable:
            parent_type = parsed_parent.case_type
            parent_num = parsed_parent.case_number
            parent_year = parsed_parent.year
            parent_bench = parsed_parent.bench
        main_text = app_part
    elif parent_case:
        parsed_parent = normalize_case_number(parent_case, default_bench=default_bench)
        if parsed_parent.parseable:
            parent_type = parsed_parent.case_type
            parent_num = parsed_parent.case_number
            parent_year = parsed_parent.year
            parent_bench = parsed_parent.bench

    # 2. Check RCP (IB) first (Restoration Company Petition)
    m = RE_RCP_IB.search(main_text)
    if m:
        num = m.group("num")
        subnum = m.group("subnum")
        year: int | None = None
        if subnum and len(subnum) == 4 and not m.group("year"):
            year = int(subnum)
            case_num = num
        elif subnum:
            case_num = f"{num}/{subnum}"
            year = int(m.group("year")) if m.group("year") else None
        else:
            case_num = num
            year = int(m.group("year")) if m.group("year") else None

        bench = normalize_bench(m.group("bench")) or normalize_bench(default_bench)
        canonical = f"RCP (IB) {case_num}" + (f"/{bench}" if bench else "") + (f"/{year}" if year else "")
        return NormalizedCaseNumber(
            raw=raw_stripped,
            case_type="RCP (IB)",
            case_number=case_num,
            year=year,
            bench=bench,
            canonical=canonical,
            parseable=True,
            parent_case_type=parent_type,
            parent_case_number=parent_num,
            parent_year=parent_year,
            parent_bench=parent_bench,
        )

    # 3. Check CP (IB)
    m = RE_CP_IB.search(main_text)
    if m:
        num = m.group("num")
        subnum = m.group("subnum")
        year = None
        if subnum and len(subnum) == 4 and not m.group("year"):
            year = int(subnum)
            case_num = num
        elif subnum:
            case_num = f"{num}/{subnum}"
            year = int(m.group("year")) if m.group("year") else None
        else:
            case_num = num
            year = int(m.group("year")) if m.group("year") else None

        bench = normalize_bench(m.group("bench")) or normalize_bench(default_bench)
        canonical = f"CP (IB) {case_num}" + (f"/{bench}" if bench else "") + (f"/{year}" if year else "")
        return NormalizedCaseNumber(
            raw=raw_stripped,
            case_type="CP (IB)",
            case_number=case_num,
            year=year,
            bench=bench,
            canonical=canonical,
            parseable=True,
            parent_case_type=parent_type,
            parent_case_number=parent_num,
            parent_year=parent_year,
            parent_bench=parent_bench,
        )

    # 4. Check NCLAT Appeals
    m = RE_NCLAT_APP.search(main_text)
    if m:
        num = m.group("num")
        year = int(m.group("year")) if m.group("year") else None
        sector = m.group("sector")
        if sector and "insolvency" in sector.lower():
            c_type = "Company Appeal (AT) (Insolvency)"
        else:
            c_type = "Company Appeal (AT)"
        bench = normalize_bench(default_bench)
        canonical = f"{c_type} {num}" + (f"/{bench}" if bench else "") + (f"/{year}" if year else "")
        return NormalizedCaseNumber(
            raw=raw_stripped,
            case_type=c_type,
            case_number=num,
            year=year,
            bench=bench,
            canonical=canonical,
            parseable=True,
            parent_case_type=parent_type,
            parent_case_number=parent_num,
            parent_year=parent_year,
            parent_bench=parent_bench,
        )

    m = RE_COMPETITION_APP.search(main_text)
    if m:
        num = m.group("num")
        year = int(m.group("year")) if m.group("year") else None
        bench = normalize_bench(default_bench)
        return NormalizedCaseNumber(
            raw=raw_stripped,
            case_type="Competition Appeal (AT)",
            case_number=num,
            year=year,
            bench=bench,
            canonical=f"Competition Appeal (AT) {num}" + (f"/{bench}" if bench else "") + (f"/{year}" if year else ""),
            parseable=True,
            parent_case_type=parent_type,
            parent_case_number=parent_num,
            parent_year=parent_year,
            parent_bench=parent_bench,
        )

    # 5. Check Applications (IA, CA, MA)
    m = RE_APPLICATION.search(main_text)
    if m:
        c_type = _clean_case_type(m.group("app_type"))
        num = m.group("num")
        subnum = m.group("subnum")
        year = None
        if subnum and len(subnum) == 4 and not m.group("year"):
            year = int(subnum)
            case_num = num
        elif subnum:
            case_num = f"{num}/{subnum}"
            year = int(m.group("year")) if m.group("year") else None
        else:
            case_num = num
            year = int(m.group("year")) if m.group("year") else None

        bench = normalize_bench(m.group("bench")) or normalize_bench(default_bench)
        canonical = f"{c_type} {case_num}" + (f"/{bench}" if bench else "") + (f"/{year}" if year else "")
        return NormalizedCaseNumber(
            raw=raw_stripped,
            case_type=c_type,
            case_number=case_num,
            year=year,
            bench=bench,
            canonical=canonical,
            parseable=True,
            parent_case_type=parent_type,
            parent_case_number=parent_num,
            parent_year=parent_year,
            parent_bench=parent_bench,
        )

    # 6. Fallback: general court case e.g. "W.P.(C) 1234/2024"
    m = RE_GENERAL_COURT.search(main_text)
    if m:
        c_type = _clean_case_type(m.group("type"))
        num = m.group("num")
        year = int(m.group("year")) if m.group("year") else None
        bench = normalize_bench(default_bench)
        canonical = f"{c_type} {num}" + (f"/{bench}" if bench else "") + (f"/{year}" if year else "")
        return NormalizedCaseNumber(
            raw=raw_stripped,
            case_type=c_type,
            case_number=num,
            year=year,
            bench=bench,
            canonical=canonical,
            parseable=True,
            parent_case_type=parent_type,
            parent_case_number=parent_num,
            parent_year=parent_year,
            parent_bench=parent_bench,
        )

    # Unparseable fallback
    bench = normalize_bench(default_bench)
    return NormalizedCaseNumber(
        raw=raw_stripped,
        case_type="UNCLASSIFIED",
        case_number=raw_stripped,
        year=None,
        bench=bench,
        canonical=raw_stripped,
        parseable=False,
    )


def compare_case_numbers(
    tracked: NormalizedCaseNumber,
    observed: NormalizedCaseNumber,
) -> str:
    """Compare a tracked matter case number against an observed case number.

    Implements Session R2 Matching Rules:
    1. Parent case matching: "IA 456/2026 in CP (IB) 123/MB/2026" matches tracked "CP (IB) 123/MB/2026".
    2. EXACT: case_type, case_number, year, and bench are all present and equal.
    3. PARTIAL: case_type and case_number match, but either side lacks bench or year.
    4. NONE: case_type, case_number, year, or bench mismatch.
    """
    if not tracked.parseable or not observed.parseable:
        return "NONE"

    # Candidates to compare against: observed case itself, or its parent case
    candidates = [observed]
    if observed.parent is not None:
        candidates.append(observed.parent)

    best_result = "NONE"

    for cand in candidates:
        # Case type and number must match
        if tracked.case_type != cand.case_type:
            continue
        if tracked.case_number != cand.case_number:
            continue

        # Year check: mismatch -> NONE
        if tracked.year is not None and cand.year is not None:
            if tracked.year != cand.year:
                continue

        # Bench check: mismatch -> NONE
        if tracked.bench is not None and cand.bench is not None:
            if tracked.bench != cand.bench:
                continue

        # EXACT condition: all four fields (type, number, year, bench) are present and equal
        if (
            tracked.case_type == cand.case_type
            and tracked.case_number == cand.case_number
            and tracked.year is not None
            and cand.year is not None
            and tracked.year == cand.year
            and tracked.bench is not None
            and cand.bench is not None
            and tracked.bench == cand.bench
        ):
            return "EXACT"

        # If we got here, type & number matched, and neither year nor bench conflicted,
        # but at least one side is missing year or bench -> PARTIAL
        best_result = "PARTIAL"

    return best_result
