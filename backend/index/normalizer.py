"""Legal lexeme normalisation for full-text search.

Normative sources:
- Session S06 Directive #1:
  - Extract section paths (138(1)(a), 7(5)), penal combos (302/34), u/s, r/w,
    Art. 21A, CP(IB) case numbers, SCC/AIR/INSC citations.
  - Map each to canonical lexemes and emit ancestor lexemes (e.g. s138, s138_1, s138_1_a).
  - Preserved via array_to_tsvector($lexemes::text[]) at weight C.
  - On query side, construct direct tsquery terms combined with websearch_to_tsquery.
"""

from __future__ import annotations

import re

# Regex for section paths like Section 138(1)(a), s. 7(5), Sec 9(5)(i), u/s 9, or bare 138(1)(a)
SECTION_RE = re.compile(
    r"(?:(?:Section|Sec\.?|s\.|u/s)\s*(\d+[A-Za-z]?(?:\s*\([0-9A-Za-z]+\))*))"
    r"|(?:\b(\d+[A-Za-z]?\s*\([0-9A-Za-z]+\)(?:\s*\([0-9A-Za-z]+\))*))",
    re.IGNORECASE,
)

# Penal / joint section combos like 302/34 or 420/120B
PENAL_COMBO_RE = re.compile(r"\b(\d+[A-Za-z]?)\s*/\s*(\d+[A-Za-z]?)\b")

# Constitutional articles like Article 141, Art. 21A, Art 226
ARTICLE_RE = re.compile(r"\b(?:Article|Art\.?)\s*(\d+[A-Za-z]?)\b", re.IGNORECASE)

# Procedural shortcuts
US_RE = re.compile(r"\bu/s\b", re.IGNORECASE)
RW_RE = re.compile(r"\br/w\b", re.IGNORECASE)

# NCLT / NCLAT case numbers
# e.g. CP(IB) No. 1234/MB/2019, CP (IB) 188 of 2026, CP(IB)/66/7/AMR/2024, CP(IB)/247(MB)/2026
CPIB_RE = re.compile(
    r"\b(?:C\.?P\.?|Company\s+Petition)\s*\(IB\)[/\s-]*(?:No\.?)?\s*(\d+)(?:[/\s]+(\d+))?(?:[/\s(]*([A-Za-z]+)[/\s)]*)?[\s/of]*(\d{4})\b",
    re.IGNORECASE,
)

# Restoration Company Petitions: RCP (IB)
# e.g. RCP (IB) 6/MB/2023, RCP(IB) No. 12/2022
RCPIB_RE = re.compile(
    r"\b(?:R\.?C\.?P\.?|Restoration\s+Company\s+Petition)\s*\(IB\)[/\s-]*(?:No\.?)?\s*(\d+)(?:[/\s]+(\d+))?(?:[/\s(]*([A-Za-z]+)[/\s)]*)?[\s/of]*(\d{4})\b",
    re.IGNORECASE,
)
COMP_APP_RE = re.compile(
    r"\bCompany\s+Appeal\s*\(AT\)\s*(?:\([A-Za-z\s]+\)\s*)?(?:No\.?)?\s*(\d+)\s*(?:of|/)\s*(\d{4})\b",
    re.IGNORECASE,
)

# Standard citations
SCC_RE = re.compile(r"\((?P<year>\d{4})\)\s*(?P<vol>\d+)\s*SCC\s*(?P<page>\d+)", re.IGNORECASE)
AIR_RE = re.compile(r"\bAIR\s+(?P<year>\d{4})\s+(?P<court>[A-Za-z]+)\s+(?P<page>\d+)\b", re.IGNORECASE)
INSC_RE = re.compile(r"\b(?P<year>\d{4})\s+INSC\s+(?P<num>\d+)\b", re.IGNORECASE)
SCR_RE = re.compile(r"\[(?P<year>\d{4})\]\s*(?P<vol>\d+)\s*SCR\s*(?P<page>\d+)", re.IGNORECASE)


def _split_section_components(raw_sec: str) -> list[str]:
    """Split section string like '138(1)(a)' into ['138', '1', 'a']."""
    cleaned = raw_sec.strip().replace(" ", "")
    # Find base number + letter
    match = re.match(r"^(\d+[A-Za-z]?)", cleaned)
    if not match:
        return []
    base = match.group(1).lower()
    parts = [base]
    # Find bracketed components: (1), (a), (i)
    subs = re.findall(r"\(([0-9A-Za-z]+)\)", cleaned)
    for s in subs:
        parts.append(s.lower())
    return parts


def extract_legal_lexemes(text: str) -> list[str]:
    """Extract legal lexemes including full paths and ancestors from text.

    Example:
    'Section 138(1)(a)' -> ['s138', 's138_1', 's138_1_a']
    'Art. 21A' -> ['art21', 'art21a']
    '302/34' -> ['s302', 's34', 's302_34']
    'CP(IB) No. 1234/MB/2019' -> ['cp_ib_1234_mb_2019']
    """
    lexemes: set[str] = set()

    # 1. Sections with ancestor emission
    for m in SECTION_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        if not raw:
            continue
        parts = _split_section_components(raw)
        if parts:
            # Emit ancestors: s138, s138_1, s138_1_a
            accum = "s" + parts[0]
            lexemes.add(accum)
            for sub in parts[1:]:
                accum = f"{accum}_{sub}"
                lexemes.add(accum)

    # 2. Penal section combos
    for m in PENAL_COMBO_RE.finditer(text):
        s1 = m.group(1).lower()
        s2 = m.group(2).lower()
        # Avoid false positives on date fractions like 10/12
        if len(s1) <= 4 and len(s2) <= 4:
            lexemes.add(f"s{s1}")
            lexemes.add(f"s{s2}")
            lexemes.add(f"s{s1}_{s2}")

    # 3. Constitutional articles
    for m in ARTICLE_RE.finditer(text):
        raw_art = m.group(1).lower()
        lexemes.add(f"art{raw_art}")
        # Ancestor if letter suffix e.g. 21A -> art21, art21a
        match = re.match(r"^(\d+)([a-z])$", raw_art)
        if match:
            lexemes.add(f"art{match.group(1)}")

    # 4. Procedural abbreviations
    if US_RE.search(text):
        lexemes.add("lex_u_s")
    if RW_RE.search(text):
        lexemes.add("lex_r_w")

    # 5. Case numbers
    for m in CPIB_RE.finditer(text):
        num, bench, yr = m.group(1), m.group(3), m.group(4)
        if bench and bench.lower() == "of":
            bench = None
        if bench:
            lexemes.add(f"cp_ib_{num}_{bench.lower()}_{yr}")
        lexemes.add(f"cp_ib_{num}_{yr}")

    for m in RCPIB_RE.finditer(text):
        num, bench, yr = m.group(1), m.group(3), m.group(4)
        if bench and bench.lower() == "of":
            bench = None
        if bench:
            lexemes.add(f"rcp_ib_{num}_{bench.lower()}_{yr}")
        lexemes.add(f"rcp_ib_{num}_{yr}")

    for m in COMP_APP_RE.finditer(text):
        num, yr = m.group(1), m.group(2)
        lexemes.add(f"comp_app_at_{num}_{yr}")

    # 6. Citations
    for m in SCC_RE.finditer(text):
        lexemes.add(f"scc_{m.group('year')}_{m.group('vol')}_{m.group('page')}")

    for m in AIR_RE.finditer(text):
        lexemes.add(f"air_{m.group('year')}_{m.group('court').lower()}_{m.group('page')}")

    for m in INSC_RE.finditer(text):
        lexemes.add(f"insc_{m.group('year')}_{m.group('num')}")

    for m in SCR_RE.finditer(text):
        lexemes.add(f"scr_{m.group('year')}_{m.group('vol')}_{m.group('page')}")

    return sorted(lexemes)


def extract_query_lexemes(query_text: str) -> tuple[list[str], str]:
    """Extract lexemes from query text and return (lexemes, remaining_text)."""
    lexemes = extract_legal_lexemes(query_text)

    # Clean query text by stripping matched citation / section spans so remaining prose is searched cleanly
    remaining = query_text
    # Strip matched patterns
    remaining = SECTION_RE.sub(" ", remaining)
    remaining = PENAL_COMBO_RE.sub(" ", remaining)
    remaining = ARTICLE_RE.sub(" ", remaining)
    remaining = RCPIB_RE.sub(" ", remaining)
    remaining = CPIB_RE.sub(" ", remaining)
    remaining = COMP_APP_RE.sub(" ", remaining)
    remaining = SCC_RE.sub(" ", remaining)
    remaining = AIR_RE.sub(" ", remaining)
    remaining = INSC_RE.sub(" ", remaining)
    remaining = SCR_RE.sub(" ", remaining)
    remaining = re.sub(r"\s+", " ", remaining).strip()

    return lexemes, remaining
