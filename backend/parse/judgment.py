"""Judgment parser for Indian legal documents (NCLT, NCLAT, SC, HC).

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.4 (layout and furniture) & §5.5 (judgment parser and metadata)
- docs/01_master_architecture.md §5.3 (anchor grammar v1.1) & §7.1 (ParsedDocument / ParsedNode)
- User Directives #3 (court numbering), #5 (verbatim substring check), #10 (gateway fallback logging)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import structlog

from parse.triage import PageLine, TriagedPage

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class ExtractedHeader:
    court_id: str
    bench_name: str
    case_number: str
    case_type: str
    case_year: int | None
    decision_date: date | None
    parties: dict[str, Any]
    coram: list[dict[str, str]] = field(default_factory=list)
    doc_type: str = "ORDER"  # FINAL_ORDER | INTERIM_ORDER | JUDGMENT
    title: str = ""
    bench_strength: int = 1


@dataclass(slots=True)
class ParsedBlock:
    fragment: str  # p1, p1.1, u1, ord, hdr, fn1
    node_type: str  # PARA | ORDER | HEADER | FOOTNOTE | UNNUMBERED
    number_as_printed: str | None
    numbering: str  # EXPLICIT | SYNTHETIC
    text: str
    spans: list[dict[str, Any]] = field(default_factory=list)
    ocr_conf: float = 1.0
    is_handwriting: bool = False
    children: list[ParsedBlock] = field(default_factory=list)


@dataclass(slots=True)
class ParsedJudgment:
    header: ExtractedHeader
    blocks: list[ParsedBlock]
    opinions: list[dict[str, Any]]
    furniture_lines: list[str]
    used_llm_fallback: bool = False


# Indian Month Mapping for DD-MM-YYYY parsing
MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "sept": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_indian_date(text: str) -> date | None:
    """Parse dates in Indian legal formats (DD-MM-YYYY, DD/MM/YYYY, 22nd September, 2026)."""
    # 1. Numeric DD.MM.YYYY or DD-MM-YYYY or DD/MM/YYYY
    m = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b", text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31 and 1950 <= year <= 2030:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # 2. Textual: 22nd September, 2026 or 22 September 2026
    m2 = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+),?\s+(\d{4})\b", text)
    if m2:
        day = int(m2.group(1))
        month_name = m2.group(2).lower()
        year = int(m2.group(3))
        if month_name in MONTH_MAP and 1 <= day <= 31 and 1950 <= year <= 2030:
            try:
                return date(year, MONTH_MAP[month_name], day)
            except ValueError:
                pass

    return None


class JudgmentParser:
    """Deterministic parser for NCLT, NCLAT, and court orders."""

    def filter_furniture(self, pages: list[TriagedPage]) -> tuple[list[TriagedPage], list[str]]:
        """Remove lines recurring at matching relative positions on >= 60% of pages (03_P1 §5.4)."""
        if len(pages) < 3:
            return pages, []

        line_pos_counts: dict[str, int] = {}
        for p in pages:
            seen_on_page = set()
            for line in p.lines:
                # Top 15% or bottom 15%
                if line.bbox[1] < 0.15 or line.bbox[3] > 0.85:
                    norm = re.sub(r"\d+", "#", line.text.strip().lower())
                    if len(norm) > 4 and norm not in seen_on_page:
                        seen_on_page.add(norm)
                        line_pos_counts[norm] = line_pos_counts.get(norm, 0) + 1

        threshold = max(2, int(len(pages) * 0.60))
        furniture_signatures = {sig for sig, count in line_pos_counts.items() if count >= threshold}

        filtered_pages: list[TriagedPage] = []
        removed_furniture: list[str] = []

        for p in pages:
            clean_lines: list[PageLine] = []
            for line in p.lines:
                norm = re.sub(r"\d+", "#", line.text.strip().lower())
                if (line.bbox[1] < 0.15 or line.bbox[3] > 0.85) and norm in furniture_signatures:
                    removed_furniture.append(line.text)
                else:
                    clean_lines.append(line)

            filtered_pages.append(
                TriagedPage(
                    page_number=p.page_number,
                    text_source=p.text_source,
                    ocr_conf=p.ocr_conf,
                    lines=clean_lines,
                    full_text="\n".join(line.text for line in clean_lines),
                    hidden_flags=p.hidden_flags,
                    hidden_regions=p.hidden_regions,
                    source_type=p.source_type,
                    rotation_applied=p.rotation_applied,
                    dpi=p.dpi,
                    is_lang_unsupported=p.is_lang_unsupported,
                    preprocessing_meta=p.preprocessing_meta,
                )
            )

        return filtered_pages, removed_furniture

    def extract_header(
        self, pages: list[TriagedPage], source_metadata: dict[str, Any]
    ) -> ExtractedHeader:
        """Extract court, bench, case number, parties, coram, and date from the first 2 pages."""
        header_text = ""
        for p in pages[:2]:
            header_text += "\n" + p.full_text

        # 1. Court & Bench
        court_id = "crt_IN_NCLT"
        bench_name = ""
        upper_text = header_text.upper()

        if "APPELLATE TRIBUNAL" in upper_text or "NCLAT" in upper_text:
            if "CHENNAI" in upper_text:
                court_id = "crt_IN_NCLAT_CHE"
                bench_name = "Chennai Bench"
            else:
                court_id = "crt_IN_NCLAT"
                bench_name = "Principal Bench, New Delhi"
        elif "SUPREME COURT" in upper_text:
            court_id = "crt_IN_SC"
            bench_name = "New Delhi"
        elif "HIGH COURT" in upper_text:
            if "BOMBAY" in upper_text:
                court_id = "crt_IN_HC_BOM"
                bench_name = "Bombay"
            elif "DELHI" in upper_text:
                court_id = "crt_IN_HC_DEL"
                bench_name = "Delhi"
            elif "CALCUTTA" in upper_text or "KOLKATA" in upper_text:
                court_id = "crt_IN_HC_CAL"
                bench_name = "Calcutta"
            elif "MADRAS" in upper_text:
                court_id = "crt_IN_HC_MAD"
                bench_name = "Madras"
            else:
                court_id = "crt_IN_HC"
                bench_name = "High Court"
        elif "COMPANY LAW TRIBUNAL" in upper_text or "NCLT" in upper_text:
            benches = [
                ("CHANDIGARH", "crt_IN_NCLT_CHD", "Chandigarh Bench"),
                ("INDORE", "crt_IN_NCLT_IND", "Indore Bench"),
                ("AHMEDABAD", "crt_IN_NCLT_AHM", "Ahmedabad Bench"),
                ("KOLKATA", "crt_IN_NCLT_KOL", "Kolkata Bench"),
                ("CHENNAI", "crt_IN_NCLT_CHE", "Chennai Bench"),
                ("HYDERABAD", "crt_IN_NCLT_HYD", "Hyderabad Bench"),
                ("KOCHI", "crt_IN_NCLT_KOC", "Kochi Bench"),
                ("CUTTACK", "crt_IN_NCLT_CUT", "Cuttack Bench"),
                ("PRINCIPAL", "crt_IN_NCLT_PB", "Principal Bench New Delhi"),
                ("NEW DELHI", "crt_IN_NCLT_DEL", "New Delhi Bench"),
                ("DELHI", "crt_IN_NCLT_DEL", "New Delhi Bench"),
                ("MUMBAI", "crt_IN_NCLT_MUM", "Mumbai Bench"),
            ]
            matched = False
            # Pass 1: explicit "{CITY} BENCH" or "BENCH AT {CITY}"
            for city, cid, bname in benches:
                if (
                    f"{city} BENCH" in upper_text
                    or f"BENCH AT {city}" in upper_text
                    or f"BENCH, {city}" in upper_text
                    or f"BENCH - {city}" in upper_text
                ):
                    court_id = cid
                    bench_name = bname
                    matched = True
                    break

            if not matched:
                # Pass 2: check before party names
                top_text = (
                    upper_text.split("IN THE MATTER")[0].split("VERSUS")[0].split("APPLICANT")[0]
                )
                for city, cid, bname in benches:
                    if city in top_text:
                        court_id = cid
                        bench_name = bname
                        matched = True
                        break

            if not matched:
                court_id = "crt_IN_NCLT_MUM"
                bench_name = "Mumbai Bench"

        # 2. Case Number
        case_no = ""
        case_type = "ORDER"
        case_year = None

        case_patterns = [
            r"(?:Company\s+Appeal|Comp\.?\s*App\.?)\s*\(AT\)\s*(?:\([^)]+\))?\s*No\.?\s*(\d+)\s+of\s+(\d{4})",
            r"(?:C\.?P\.?|CP)\s*(?:\([A-Z]+\))?[/\s-]*No\.?\s*([0-9()A-Za-z/-]+)",
            r"I\.?A\.?\s*(?:\([A-Z]+\))?\s*No\.?\s*(\d+(?:/[A-Za-z0-9/-]+)?)\s+(?:of\s+(\d{4}))?",
            r"(?:Civil\s+Appeal|Criminal\s+Appeal)\s+No\.?\s*(\d+)\s+of\s+(\d{4})",
            r"(\b[A-Z]{2,4}\s*(?:\([A-Z]+\))?\s*No\.?\s*\d+[/A-Za-z0-9-]+\b)",
        ]

        for pat in case_patterns:
            m = re.search(pat, header_text, re.IGNORECASE)
            if m:
                case_no = m.group(0).strip()
                if "Company Appeal" in case_no or "Comp. App" in case_no or "Comp.App" in case_no:
                    case_type = "Company Appeal"
                elif "CP" in case_no.upper() or "C.P." in case_no.upper():
                    case_type = "CP (IB)"
                # Extract year if possible
                year_m = re.search(r"\b(20[12]\d)\b", case_no)
                if year_m:
                    case_year = int(year_m.group(1))
                break

        if not case_no:
            # Fallback to source metadata
            case_no = str(
                source_metadata.get("case_no") or source_metadata.get("subject") or "ORDER"
            )

        # 3. Decision Date
        decision_date = None
        # Check source_metadata first
        sm_date_str = str(source_metadata.get("date") or source_metadata.get("order_date") or "")
        if sm_date_str:
            decision_date = parse_indian_date(sm_date_str)

        # Check explicit pronouncement / delivered pattern in header
        if not decision_date:
            pronounce_pat = r"(?:Order\s+(?:delivered|pronounced)\s+on|Delivered\s+on|Pronounced\s+on)[:\s]*([^\n]+)"
            pm = re.search(pronounce_pat, header_text, re.IGNORECASE)
            if pm:
                decision_date = parse_indian_date(pm.group(1))

        # Check daily order start stamp e.g. "14.08.2026:"
        if not decision_date:
            sm = re.search(r"(?:^|\n)\s*(\d{1,2}[./-]\d{1,2}[./-]20[12]\d)\s*:", header_text)
            if sm:
                decision_date = parse_indian_date(sm.group(1))

        # Check end of document next to signatures: "Dated: 09.09.2026"
        if not decision_date and pages:
            dm_lasts = re.findall(
                r"(?:^|\n)\s*(?:Dated|Date)[:\s]+(\d{1,2}[./-]\d{1,2}[./-]20[12]\d)",
                pages[-1].full_text,
                re.IGNORECASE,
            )
            if dm_lasts:
                decision_date = parse_indian_date(dm_lasts[-1])

        if not decision_date:
            # Extract from general header patterns
            date_patterns = [
                r"(?:^|\n)\s*(?:Dated|Date)[:\s]+(\d{1,2}[./-]\d{1,2}[./-]20[12]\d)",
                r"(\d{1,2}[./-]\d{1,2}[./-]20[12]\d)",
                r"(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+20[12]\d)",
            ]
            for dpat in date_patterns:
                dm = re.search(dpat, header_text, re.IGNORECASE)
                if dm:
                    parsed_d = parse_indian_date(dm.group(1))
                    if parsed_d:
                        decision_date = parsed_d
                        break

        # 4. Parties
        petitioner = ""
        respondent = ""
        vs_m = re.search(r"(?:^|\s)(?:Versus|VERSUS|V/s|V/S|Vs\.|VS\.|Vs|VS)(?:\s|$)", header_text)
        if vs_m:
            before_text = header_text[: vs_m.start()]
            after_text = header_text[vs_m.end() :]

            before_lines = [line.strip() for line in before_text.splitlines() if line.strip()]
            role_pattern = re.compile(
                r"^[.\s…]*(?:APPLICANT|PETITIONER|APPELLANT|CREDITOR|DEBTOR|DEFENDANT|PLAINTIFF)s?.*$",
                re.I,
            )
            addr_pattern = re.compile(
                r"^(?:Having\s+Registered|Through\s+|Registered\s+Office|Plot\s+No|Sector|\d{3,}|[A-Za-z0-9\s,-]+–\s*\d{6})",
                re.I,
            )

            candidates: list[str] = []
            for line in reversed(before_lines):
                if re.search(
                    r"(?:IN\s+THE\s+MATTER\s+OF|NAME\s+OF\s+THE\s+PARTIES|BETWEEN)[:\s-]*$",
                    line,
                    re.I,
                ):
                    break
                if role_pattern.match(line):
                    continue
                if (
                    addr_pattern.match(line)
                    or "Road" in line
                    or "MIDC" in line
                    or "Maharashtra" in line
                ):
                    continue
                cleaned = re.sub(
                    r"\s*[.…-]+\s*(?:APPLICANT|PETITIONER|APPELLANT|CREDITOR|DEBTOR).*$",
                    "",
                    line,
                    flags=re.I,
                ).strip()
                cleaned = re.sub(
                    r"^(?:IN\s+THE\s+MATTER\s+OF|NAME\s+OF\s+THE\s+PARTIES|BETWEEN)[:\s-]*",
                    "",
                    cleaned,
                    flags=re.I,
                ).strip()
                if len(cleaned) > 2:
                    candidates.append(cleaned)
                    break

            if candidates:
                petitioner = candidates[-1]

            after_lines = [line.strip() for line in after_text.splitlines() if line.strip()]
            for line in after_lines:
                if role_pattern.match(line):
                    continue
                cleaned = re.sub(
                    r"\s*[.…-]+\s*(?:RESPONDENT|DEFENDANT|CORPORATE\s+DEBTOR).*$",
                    "",
                    line,
                    flags=re.I,
                ).strip()
                if len(cleaned) > 2:
                    respondent = cleaned
                    break

        parties = {
            "petitioner": petitioner or "Applicant",
            "respondent": respondent or "Respondent",
        }

        # 5. Coram
        coram = []
        coram_lines = re.findall(
            r"((?:HON'BLE|SHRI|SMT|JUSTICE|DR\.)\s+[A-Z\s.]+(?:MEMBER\s*\([^)]+\)|JUDGE|CJI)?)",
            upper_text,
        )
        for cline in coram_lines[:4]:
            cleaned_judge = cline.strip()
            if len(cleaned_judge) > 5:
                coram.append({"judge_name": cleaned_judge, "role": "MEMBER"})

        bench_strength = max(1, len(coram))

        # 6. Doc Type
        doc_type = "FINAL_ORDER"
        if "JUDGMENT" in upper_text[:1000]:
            doc_type = "JUDGMENT"
        elif "DAILY ORDER" in upper_text or "ORDER SHEET" in upper_text:
            doc_type = "INTERIM_ORDER"

        # 7. Title
        title = f"{parties['petitioner']} v. {parties['respondent']}"
        if len(title) > 200:
            title = title[:197] + "..."

        return ExtractedHeader(
            court_id=court_id,
            bench_name=bench_name,
            case_number=case_no,
            case_type=case_type,
            case_year=case_year,
            decision_date=decision_date,
            parties=parties,
            coram=coram,
            doc_type=doc_type,
            title=title,
            bench_strength=bench_strength,
        )

    def parse_blocks(self, pages: list[TriagedPage]) -> list[ParsedBlock]:
        """Extract structured paragraphs, sub-paragraphs, unnumbered blocks, and orders."""
        blocks: list[ParsedBlock] = []

        para_pat = re.compile(
            r"^\s*(?:([1-9]\d*\.[1-9]\d*)[.)]?\s+|(?:\b[Pp]ara(?:graph)?\s*)?([1-9]\d*)[.)]\s*|\(([1-9]\d{0,2})\)\s*)"
        )
        citation_follow_pat = re.compile(
            r"^\s*\]?\s*(?:\d+\s+)?(?:SCC|AIR|SCR|SCALE|Comp\s*Cas|Cri|Civ|OnLine|ILR|DLT|Bom\s*CR|MLJ)\b",
            re.IGNORECASE,
        )
        date_pat = re.compile(r"^\s*\d{1,2}[./-]\d{1,2}[./-]20[12]\d")
        order_divider_pat = re.compile(
            r"^\s*(?:O\s*R\s*D\s*E\s*R|JUDGMENT|DAILY\s+ORDER|ORDER\s+SHEET)(?:\s*\([^)]+\))?\s*$",
            re.IGNORECASE,
        )
        operative_pat = re.compile(
            r"^\s*(?:(?:OPERATIVE\s+)?ORDER(?:\s*[:—-]|\s*$)|Accordingly[,\s]|In\s+the\s+result[,\s]|(?:The\s+)?(?:appeal|application)\s+is\s+)",
            re.IGNORECASE,
        )

        unnum_idx = 0
        current_block: ParsedBlock | None = None
        has_seen_first_numbered_para = False
        has_seen_order_divider = False

        for page in pages:
            if page.is_lang_unsupported:
                continue
            lines = page.lines
            for line in lines:
                text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", line.text).strip()
                if not text:
                    continue

                # 1. Order divider separating tribunal header from order body
                if (
                    not has_seen_order_divider
                    and not has_seen_first_numbered_para
                    and order_divider_pat.match(text)
                ):
                    has_seen_order_divider = True
                    if current_block is not None:
                        current_block.fragment = "hdr"
                        current_block.node_type = "HEADER"
                        blocks.append(current_block)
                        current_block = None
                    unnum_idx = 0
                    continue

                # Skip standalone parenthesized modifier directly under order divider e.g. (Hybrid Mode)
                if (
                    has_seen_order_divider
                    and current_block is None
                    and re.match(r"^\s*\([A-Za-z\s]+\)\s*$", text)
                ):
                    continue

                # 2. Check if operative order keyword appears (excluding continuation of just-started numbered para)
                is_empty_or_num_only = (
                    current_block is not None and len(current_block.text.strip()) <= 10
                )
                if (
                    operative_pat.match(text)
                    and has_seen_first_numbered_para
                    and not is_empty_or_num_only
                ):
                    if current_block is not None:
                        blocks.append(current_block)
                    current_block = ParsedBlock(
                        fragment="ord",
                        node_type="ORDER",
                        number_as_printed=None,
                        numbering="SYNTHETIC",
                        text=text,
                        spans=[
                            {
                                "page": page.page_number,
                                "bbox": line.bbox,
                                "char_range": [0, len(text)],
                            }
                        ],
                        ocr_conf=line.confidence,
                        is_handwriting=line.is_handwriting,
                    )
                    continue

                # 3. Check if numbered paragraph (ignoring date lines e.g. 14.08.2026:)
                m = None
                if not date_pat.match(text):
                    m = para_pat.match(text)

                is_valid_para = False
                dec_sub = main_num = paren_num = None
                cand_main_int: int | None = None

                if m:
                    dec_sub, main_num, paren_num = m.groups()
                    after_match = text[m.end():]
                    cand_main_int = (
                        int(main_num)
                        if main_num
                        else (
                            int(paren_num)
                            if paren_num
                            else int(dec_sub.split(".")[0])
                        )
                    )

                    # Court-printed numbering must be sequential/plausible:
                    # 1. 4-digit numbers (years 1900-2099 or >= 1000) are never paragraph numbers
                    # 2. Parenthesized numbers must be sub-paragraphs (<= 99)
                    # 3. Numbers followed immediately by citation markers or ']' are citations
                    if cand_main_int >= 1000 or (1900 <= cand_main_int <= 2099):
                        is_valid_para = False
                    elif paren_num and int(paren_num) > 99:
                        is_valid_para = False
                    elif citation_follow_pat.match(after_match):
                        is_valid_para = False
                    else:
                        is_valid_para = True

                if is_valid_para:
                    has_seen_first_numbered_para = True
                    if current_block is not None:
                        blocks.append(current_block)

                    if dec_sub:
                        frag = f"p{dec_sub}"
                        printed = dec_sub
                    elif main_num:
                        frag = f"p{main_num}"
                        printed = main_num
                    else:
                        frag = f"p{paren_num}"
                        printed = paren_num

                    current_block = ParsedBlock(
                        fragment=frag,
                        node_type="PARA",
                        number_as_printed=printed,
                        numbering="EXPLICIT",
                        text=text,
                        spans=[
                            {
                                "page": page.page_number,
                                "bbox": line.bbox,
                                "char_range": [0, len(text)],
                            }
                        ],
                        ocr_conf=line.confidence,
                        is_handwriting=line.is_handwriting,
                    )
                else:
                    # Continuation of current block or unnumbered block
                    if current_block is not None:
                        current_block.text += " " + text
                        current_block.spans.append(
                            {
                                "page": page.page_number,
                                "bbox": line.bbox,
                                "char_range": [0, len(text)],
                            }
                        )
                        current_block.ocr_conf = round(
                            (current_block.ocr_conf + line.confidence) / 2.0, 4
                        )
                        if line.is_handwriting:
                            current_block.is_handwriting = True
                    else:
                        unnum_idx += 1
                        current_block = ParsedBlock(
                            fragment=f"u{unnum_idx}",
                            node_type="UNNUMBERED",
                            number_as_printed=None,
                            numbering="SYNTHETIC",
                            text=text,
                            spans=[
                                {
                                    "page": page.page_number,
                                    "bbox": line.bbox,
                                    "char_range": [0, len(text)],
                                }
                            ],
                            ocr_conf=line.confidence,
                            is_handwriting=line.is_handwriting,
                        )

        if current_block is not None:
            blocks.append(current_block)

        return blocks

    def parse(
        self,
        triaged_pages: list[TriagedPage],
        source_metadata: dict[str, Any] | None = None,
        raw_full_text: str = "",
    ) -> ParsedJudgment:
        """Parse judgment document from triaged pages."""
        source_meta = source_metadata or {}

        # 1. Filter repeated furniture
        clean_pages, furniture = self.filter_furniture(triaged_pages)

        # 2. Extract header
        header = self.extract_header(clean_pages, source_meta)

        # 3. Extract blocks
        blocks = self.parse_blocks(clean_pages)

        # 4. Fallback if no numbered paragraphs recovered on multi-page doc
        used_llm = False
        if len(blocks) < 2 and len(triaged_pages) >= 2:
            # Fallback segmentation using Gateway contract if available
            used_llm = True
            logger.info("segmentation_fallback_invoked", pages=len(triaged_pages))

        # Default opinion o1
        opinions = [
            {
                "opinion_id": "o1",
                "kind": "MAJORITY",
                "author_judge_ids": [c["judge_name"] for c in header.coram],
                "anchor_range": [
                    blocks[0].fragment if blocks else "u1",
                    blocks[-1].fragment if blocks else "u1",
                ],
            }
        ]

        return ParsedJudgment(
            header=header,
            blocks=blocks,
            opinions=opinions,
            furniture_lines=furniture,
            used_llm_fallback=used_llm,
        )
