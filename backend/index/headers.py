"""Deterministic context header builder for chunk embedding input.

Normative sources:
- docs/04_P2_enrichment_indexing.md §5.3 (deterministic header format)
- Rule: citations appear as printed (normalised), never resolved short names
- Rule: header is prepended to embedding input only, never source text
"""

from __future__ import annotations


def build_context_header(
    court_name: str | None,
    bench_strength: int | None,
    decision_date: str | None,
    title: str | None,
    first_anchor: str,
    last_anchor: str,
    section_heading: str | None = None,
    cited_provisions: list[str] | None = None,
    cited_cases_norm: list[str] | None = None,
) -> str:
    """Construct deterministic context header string.

    Example:
    'Supreme Court of India | 3-judge bench | 2024-02-05 | ABC v. XYZ | ¶¶ p45–p47 | cites: s.5 Limitation Act 1963; (2021) 9 SCC 657'
    """
    parts: list[str] = []

    if court_name:
        parts.append(court_name)

    if bench_strength:
        parts.append(f"{bench_strength}-judge bench")

    if decision_date:
        parts.append(str(decision_date))

    if title:
        parts.append(title.strip())

    if section_heading:
        parts.append(section_heading.strip())

    # Anchor range
    p_first = first_anchor.split("#")[-1] if "#" in first_anchor else first_anchor
    p_last = last_anchor.split("#")[-1] if "#" in last_anchor else last_anchor
    if p_first == p_last:
        parts.append(f"¶ {p_first}")
    else:
        parts.append(f"¶¶ {p_first}–{p_last}")

    # Citations as printed
    cites: list[str] = []
    if cited_provisions:
        cites.extend(cited_provisions[:3])
    if cited_cases_norm:
        cites.extend(cited_cases_norm[:3])

    if cites:
        parts.append("cites: " + "; ".join(cites))

    return " | ".join(parts)
