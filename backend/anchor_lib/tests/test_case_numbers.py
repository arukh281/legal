"""Tests for Indian legal case-number normalizer and matcher."""


from anchor_lib.case_numbers import (
    compare_case_numbers,
    normalize_bench,
    normalize_case_number,
)


def test_bench_normalization() -> None:
    assert normalize_bench("MB") == "MUM"
    assert normalize_bench("MUM") == "MUM"
    assert normalize_bench("Mumbai") == "MUM"
    assert normalize_bench("NCLT Mumbai Bench Court 1") == "MUM"
    assert normalize_bench("PB") == "PB"
    assert normalize_bench("Principal Bench") == "PB"
    assert normalize_bench("ND") == "DEL"
    assert normalize_bench("DEL") == "DEL"
    assert normalize_bench("New Delhi") == "DEL"
    assert normalize_bench("AHM") == "AHM"
    assert normalize_bench("Ahmedabad") == "AHM"
    assert normalize_bench("CHD") == "CHD"
    assert normalize_bench("Chandigarh") == "CHD"
    assert normalize_bench("CHE") == "CHE"
    assert normalize_bench("Chennai") == "CHE"
    assert normalize_bench(None) is None
    assert normalize_bench("") is None


def test_cp_ib_vs_rcp_ib_distinct() -> None:
    """DECISIONS.md 2026-10-09: CP (IB) and RCP (IB) MUST remain strictly distinct."""
    cp = normalize_case_number("CP (IB) 6/MB/2023")
    rcp = normalize_case_number("RCP (IB) 6/MB/2023")

    assert cp.case_type == "CP (IB)"
    assert cp.case_number == "6"
    assert cp.bench == "MUM"
    assert cp.year == 2023

    assert rcp.case_type == "RCP (IB)"
    assert rcp.case_number == "6"
    assert rcp.bench == "MUM"
    assert rcp.year == 2023

    # Compare must return NONE
    assert compare_case_numbers(cp, rcp) == "NONE"


def test_exact_match_rule() -> None:
    """Correction 1: EXACT only when case type, number, year and bench are all present and equal."""
    tracked = normalize_case_number("CP (IB) 188/MUM/2026")
    observed = normalize_case_number("Company Petition (IB) No. 188 of 2026", default_bench="Mumbai")

    assert tracked.case_type == "CP (IB)"
    assert observed.case_type == "CP (IB)"
    assert tracked.case_number == "188"
    assert observed.case_number == "188"
    assert tracked.year == 2026
    assert observed.year == 2026
    assert tracked.bench == "MUM"
    assert observed.bench == "MUM"

    assert compare_case_numbers(tracked, observed) == "EXACT"


def test_missing_bench_yields_partial() -> None:
    """Correction 1: If either side still has no bench, it is PARTIAL."""
    tracked = normalize_case_number("CP (IB) 188/MUM/2026")
    observed = normalize_case_number("CP (IB) 188 of 2026")  # no bench

    assert compare_case_numbers(tracked, observed) == "PARTIAL"

    tracked_no_bench = normalize_case_number("CP (IB) 188/2026")
    observed_with_bench = normalize_case_number("CP (IB) 188/MB/2026")
    assert compare_case_numbers(tracked_no_bench, observed_with_bench) == "PARTIAL"


def test_missing_year_yields_partial() -> None:
    """Correction 1: If either side still has no year, it is PARTIAL."""
    tracked = normalize_case_number("CP (IB) 188/MUM/2026")
    observed = normalize_case_number("CP (IB) No. 188/MB")  # no year
    assert compare_case_numbers(tracked, observed) == "PARTIAL"


def test_bench_or_year_mismatch_yields_none() -> None:
    """Correction 1: A bench or year mismatch is NONE."""
    tracked = normalize_case_number("CP (IB) 188/MUM/2026")
    observed_diff_bench = normalize_case_number("CP (IB) 188/DEL/2026")
    assert compare_case_numbers(tracked, observed_diff_bench) == "NONE"

    observed_diff_year = normalize_case_number("CP (IB) 188/MUM/2025")
    assert compare_case_numbers(tracked, observed_diff_year) == "NONE"


def test_parent_case_matching() -> None:
    """Correction 1: 'IA 456/2026 in CP (IB) 123/MB/2026' matches on the parent case number."""
    tracked = normalize_case_number("CP (IB) 123/MB/2026")
    observed_ia = normalize_case_number("IA 456/2026 in CP (IB) 123/MB/2026")

    assert observed_ia.case_type == "IA"
    assert observed_ia.case_number == "456"
    assert observed_ia.parent is not None
    assert observed_ia.parent.case_type == "CP (IB)"
    assert observed_ia.parent.case_number == "123"
    assert observed_ia.parent.bench == "MUM"
    assert observed_ia.parent.year == 2026

    assert compare_case_numbers(tracked, observed_ia) == "EXACT"


def test_nclat_appeals() -> None:
    # Without bench -> PARTIAL (per rule: if either side has no bench, it is PARTIAL)
    c_no_bench1 = normalize_case_number("Company Appeal (AT) (Insolvency) No. 123 of 2021")
    c_no_bench2 = normalize_case_number("Company Appeal (AT) (Insolvency) 123/2021")
    assert compare_case_numbers(c_no_bench1, c_no_bench2) == "PARTIAL"

    # With bench filled (e.g. from cause list header "Principal Bench") -> EXACT
    c1 = normalize_case_number(
        "Company Appeal (AT) (Insolvency) No. 123 of 2021", default_bench="Principal Bench"
    )
    c2 = normalize_case_number("Company Appeal (AT) 123/2021", default_bench="Principal Bench")
    c3 = normalize_case_number(
        "Company Appeal (AT) (Insolvency) 123/2021", default_bench="Principal Bench"
    )

    assert c1.case_type == "Company Appeal (AT) (Insolvency)"
    assert c1.case_number == "123"
    assert c1.year == 2021
    assert c1.bench == "PB"

    assert compare_case_numbers(c1, c3) == "EXACT"
    assert compare_case_numbers(c1, c2) == "NONE"  # Different sector
