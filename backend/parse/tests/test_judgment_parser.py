"""Tests for JudgmentParser paragraph sequence validation and rejection of in-text citation years.

Normative source: Session S07 Directive #2:
- Court-printed numbering must be sequential/plausible.
- Rejection of in-text citation years like (2012) 3 SCC (Cri) 241] and citation pages like 7869.
"""

from __future__ import annotations

from parse.judgment import JudgmentParser
from parse.triage import PageLine, TriagedPage


def make_page(page_num: int, lines_text: list[str]) -> TriagedPage:
    lines = [
        PageLine(
            text=text,
            bbox=[0.1, 0.1 * i, 0.9, 0.1 * (i + 1)],
            confidence=0.99,
            words=[],
            is_handwriting=False,
        )
        for i, text in enumerate(lines_text)
    ]
    return TriagedPage(
        page_number=page_num,
        text_source="NATIVE_PDF_TEXT",
        ocr_conf=0.99,
        lines=lines,
        full_text="\n".join(lines_text),
    )


def test_sequential_paragraph_numbering_rejects_citation_years() -> None:
    """Ensure in-text citation years and split lines are not minted as bogus paragraph anchors."""
    parser = JudgmentParser()

    pages = [
        make_page(
            1,
            [
                "IN THE SUPREME COURT OF INDIA",
                "CIVIL APPELLATE JURISDICTION",
                "ORDER",
                "1. This appeal arises from the judgment of the High Court.",
                "2. The learned counsel for the appellant submitted that Section 14 moratorium applies.",
                "3. In support of this contention, counsel relied on Aneeta Hada [ (2012) 5 SCC 661 ] and",
                "(2012) 3 SCC (Cri) 241] would then become applicable to the directors.",
                "4. On the contrary, respondent submitted that proceedings under Section 138 continue.",
                "7869.",
                "5. Having heard both parties, we hold that the appeal lacks merit.",
            ],
        )
    ]

    blocks = parser.parse_blocks(pages)
    para_blocks = [b for b in blocks if b.node_type == "PARA"]

    # Must produce strictly paragraphs 1, 2, 3, 4, 5
    para_frags = [b.fragment for b in para_blocks]
    assert para_frags == ["p1", "p2", "p3", "p4", "p5"]

    # (2012) must be in p3 text, not a separate p2012 block
    p3 = next(b for b in para_blocks if b.fragment == "p3")
    assert "(2012) 3 SCC (Cri) 241] would then become applicable" in p3.text

    # 7869. must be in p4 text, not a separate p7869 block
    p4 = next(b for b in para_blocks if b.fragment == "p4")
    assert "7869." in p4.text


def test_implausible_initial_paragraph_jump_rejected() -> None:
    """A document starting with an implausible number (e.g. 2012 or 100) does not start at 2012."""
    parser = JudgmentParser()

    pages = [
        make_page(
            1,
            [
                "ORDER",
                "(2012) SCC 123 is cited as general background.",
                "1. The proceedings were instituted on 1st January 2026.",
                "2. Notice was issued.",
            ],
        )
    ]

    blocks = parser.parse_blocks(pages)
    para_blocks = [b for b in blocks if b.node_type == "PARA"]
    para_frags = [b.fragment for b in para_blocks]
    assert para_frags == ["p1", "p2"]
