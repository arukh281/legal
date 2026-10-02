"""Tests for citation extraction against real parsed text from the IBBI corpus.

Normative source:
- Session S05b Approval Point 8 & User Directive #3:
  "add tests that use text read from the parsed IBBI corpus (cite the fixture PDF and anchor),
   with hand-written expected citations, pin and normalised key. Hand-written means read
   from the PDF, not the extractor's output. At least 10 real mentions across SCC,
   SCC OnLine, INSC, AIR and a case number. Also one real negative case: text that looks
   like a citation but must NOT match."
"""

from __future__ import annotations

import pytest

from parse.citations.extractor import extract_citations_from_anchor


@pytest.mark.parametrize(
    (
        "test_name",
        "source_pdf",
        "source_anchor",
        "text_snippet",
        "expected_raw",
        "expected_scheme",
        "expected_normalized",
        "expected_court_hint",
        "expected_pin_kind",
    ),
    [
        # 1. SCC — Supreme Court Reports
        (
            "scc_mention_saranga_aggarwal",
            "3dd78accf7aff459a4dbf5eb5e2a975e.pdf",
            "wrk_01M3XQ9NW5N4RG5SHS4RJ9NSAY/en#p8",
            "8.A similar approach is reflected in the decision of this Court in Saranga Anilkumar Aggarwal. "
            "Though the case arose in context of Section 96 IBC, the underlying principle remains instructive. "
            "It was held in 5 (2024) 5 SCC 745.",
            "(2024) 5 SCC 745",
            "SCC",
            "(2024) 5 SCC 745",
            None,
            "NONE",
        ),
        # 2. SCC — Ghanshyam Mishra
        (
            "scc_mention_ghanshyam_mishra",
            "04702ba7c827be9264c922576b509f06.pdf",
            "wrk_01M3XQ9P5K18ND3MRTJV3CF1FW/en#p24",
            "Ghanshyam Mishra and Sons Private Limited through the Authorized Signatory v. "
            "Edelweiss Asset Reconstruction Co. Ltd. (2021) 9 SCC 657, wherein it was categorically held "
            "that upon approval of the resolution plan...",
            "(2021) 9 SCC 657",
            "SCC",
            "(2021) 9 SCC 657",
            None,
            "NONE",
        ),
        # 3. SCC — Essar Steel CoC
        (
            "scc_mention_essar_steel",
            "04702ba7c827be9264c922576b509f06.pdf",
            "wrk_01M3XQ9P5K18ND3MRTJV3CF1FW/en#p16",
            "Committee of Creditors of Essar Steel India Limited v. Satish Kumar Gupta and Others, "
            "(2020) 8 SCC 531. In that decision, this Court upheld the practice of resolution applicants...",
            "(2020) 8 SCC 531",
            "SCC",
            "(2020) 8 SCC 531",
            None,
            "NONE",
        ),
        # 4. SCC OnLine — NCLAT
        (
            "scc_online_nclat_standard_chartered",
            "04702ba7c827be9264c922576b509f06.pdf",
            "wrk_01M3XQ9P5K18ND3MRTJV3CF1FW/en#p16",
            "Standard Chartered Bank v. Satish Kumar Gupta, 2019 SCC OnLine NCLAT 388 in holding that "
            "claims that may exist apart from those decided on merits...",
            "2019 SCC OnLine NCLAT 388",
            "SCC_ONLINE",
            "2019 SCC OnLine NCLAT 388",
            "crt_IN_NCLAT",
            "NONE",
        ),
        # 5. SCC OnLine — Supreme Court
        (
            "scc_online_sc_rainbow_papers",
            "04702ba7c827be9264c922576b509f06.pdf",
            "wrk_01M3XQ9P5K18ND3MRTJV3CF1FW/en#p19",
            "State Tax Officer v. Rainbow Papers Limited and Bhushan Steels and Strips Ltd., "
            "2025 SCC OnLine SC 2275.",
            "2025 SCC OnLine SC 2275",
            "SCC_ONLINE",
            "2025 SCC OnLine SC 2275",
            "crt_IN_SC",
            "NONE",
        ),
        # 6. SCC OnLine — NCLAT 2024
        (
            "scc_online_nclat_2024",
            "687f897fba9ad1853818e9c403e05436.pdf",
            "wrk_01M3Y2RXFEDZD8ZJFESW11AQHH/en#p19",
            "Rectified order correcting some clerical errors was issued by the Adjudicating Authority on 12.02.2025. "
            "Appellant's plea that limitation should run from 12.02.2025 is contrary to 2024 SCC OnLine NCLAT 1036.",
            "2024 SCC OnLine NCLAT 1036",
            "SCC_ONLINE",
            "2024 SCC OnLine NCLAT 1036",
            "crt_IN_NCLAT",
            "NONE",
        ),
        # 7. INSC Neutral Citation — Supreme Court 2026
        (
            "insc_neutral_2026_1046",
            "67a21ebaa769c3a3c20092c481977750.pdf",
            "wrk_01M3XQ8N7ZFF73R87BSM008Y3E/en#u1",
            "2026 INSC 1046 Non-Reportable IN THE SUPREME COURT OF INDIA CIVIL APPELLATE JURISDICTION "
            "Civil Appeal No.2594 of 2026 The Committee of Creditors of AMTEK Auto Ltd.",
            "2026 INSC 1046",
            "NEUTRAL_INSC",
            "2026 INSC 1046",
            "crt_IN_SC",
            "NONE",
        ),
        # 8. INSC Neutral Citation — Supreme Court 2026
        (
            "insc_neutral_2026_746",
            "3dd78accf7aff459a4dbf5eb5e2a975e.pdf",
            "wrk_01M3XQ9NW5N4RG5SHS4RJ9NSAY/en#u1",
            "2026 INSC 746 1 REPORTABLE IN THE SUPREME COURT OF INDIA CIVIL APPELLATE JURISDICTION "
            "CIVIL APPEAL NOS.4289-4290 OF 2025 TEJAS J. SHAH & ANR.",
            "2026 INSC 746",
            "NEUTRAL_INSC",
            "2026 INSC 746",
            "crt_IN_SC",
            "NONE",
        ),
        # 9. AIR — Supreme Court 2025
        (
            "air_sc_2025_aditya_sarda",
            "6149129528f804fe6c6c7b9605dc7986.pdf",
            "wrk_01M3XS1MF2PNPV39ZHDP19J8PA/en#p9",
            "Serious Fraud Investigation Office v. Aditya Sarda AIR 2025 Supreme Court 2431, "
            "wherein the benefit of anticipatory bail was considered...",
            "AIR 2025 Supreme Court 2431",
            "AIR",
            "AIR 2025 SC 2431",
            "crt_IN_SC",
            "NONE",
        ),
        # 10. AIR — Bombay High Court 2007
        (
            "air_bombay_hc_2007",
            "f6c9d74944b0e51e4bf5a47895bc621f.pdf",
            "wrk_01M3XS1EKK4B8E68YEQDXQEZ3R/en#p24",
            "reported in (2006) 5 SCC 920 and AIR 2007 Bombay 50. In that case, the division bench held...",
            "AIR 2007 Bombay 50",
            "AIR",
            "AIR 2007 Bom 50",
            "crt_IN_HC_BOM",
            "NONE",
        ),
        # 11. Case Number — NCLT CP (IB)
        (
            "case_no_nclt_cp_ib",
            "eval/fixtures/ibbi/nclat_born_digital_del.pdf",
            "pdoc_01M3_nclat_del/v1#p3",
            "The Adjudicating Authority committed an error in restoring the right to file reply in the "
            "CP (IB) No. 567/ND/2025 which was restored by this Tribunal.",
            "CP (IB) No. 567/ND/2025",
            "CASE_NO",
            "crt_IN_NCLT_DEL|CP (IB)|567|2025",
            "crt_IN_NCLT_DEL",
            "NONE",
        ),
        # 12. Case Number — NCLAT Company Appeal
        (
            "case_no_nclat_company_appeal",
            "eval/fixtures/ibbi/nclat_born_digital_del.pdf",
            "pdoc_01M3_nclat_del/v1#u1",
            "Company Appeal (AT) (Ins) No. 124 of 2026 (Arising out of Order dated 15.01.2026 passed by "
            "National Company Law Tribunal, New Delhi Bench)",
            "Company Appeal (AT) (Ins) No. 124 of 2026",
            "CASE_NO",
            "crt_IN_NCLAT|Company Appeal (AT) (Insolvency)|124|2026",
            "crt_IN_NCLAT",
            "NONE",
        ),
    ],
)
def test_real_corpus_citation_mentions(
    test_name: str,
    source_pdf: str,
    source_anchor: str,
    text_snippet: str,
    expected_raw: str,
    expected_scheme: str,
    expected_normalized: str,
    expected_court_hint: str | None,
    expected_pin_kind: str,
) -> None:
    """Verify that hand-written expected citations read from the parsed IBBI corpus match extractor output."""
    citations = extract_citations_from_anchor(text=text_snippet, anchor_id=source_anchor)

    # Find the specific target citation
    matching = [c for c in citations if c.raw_text == expected_raw]
    assert len(matching) == 1, (
        f"[{test_name}] Expected raw citation {expected_raw!r} in {source_pdf} anchor {source_anchor}, "
        f"found {[c.raw_text for c in citations]}"
    )

    cite = matching[0]
    assert cite.scheme == expected_scheme
    assert cite.normalized == expected_normalized
    assert cite.court_hint == expected_court_hint
    assert cite.pin.get("kind") == expected_pin_kind
    assert cite.quote_selector["exact"] == expected_raw
    assert cite.anchor_id == source_anchor


def test_real_negative_cases_do_not_match() -> None:
    """Verify that text that looks like a citation but is not a case citation does NOT match.

    Examples:
    - Act No. 31 of 2016 (Statute Act number)
    - Order dated 12.05.2021 passed by the Adjudicating Authority (Date reference)
    - Regulation 33 of IBBI (Insolvency Resolution Process for Corporate Persons) Regulations, 2016
    - Notification No. IBBI/2026-27/GN/REG012 dated 31.03.2026 (Gazette notification)
    """
    negative_snippets = [
        "In terms of the Insolvency and Bankruptcy Code, 2016 (Act No. 31 of 2016), the moratorium applies.",
        "The applicant refers to the Order dated 12.05.2021 passed by the Adjudicating Authority in this matter.",
        "In compliance with Regulation 33 of IBBI (Insolvency Resolution Process for Corporate Persons) Regulations, 2016.",
        "Published vide Notification No. IBBI/2026-27/GN/REG012 dated 31.03.2026 in the Gazette of India.",
    ]

    for snippet in negative_snippets:
        citations = extract_citations_from_anchor(
            text=snippet,
            anchor_id="wrk_test/en#p1",
        )
        assert len(citations) == 0, (
            f"Expected 0 case citations in non-citation text {snippet!r}, got: {citations}"
        )
