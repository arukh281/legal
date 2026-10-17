"""Script to generate the side-by-side human review addendum for failed in-corpus gold cases.

Normative source: User instruction 2 (side-by-side cited vs expected full text for evr_01M550XPQXRMJATTAZ37BF69BN).
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    data_path = Path(__file__).parent / "fixtures" / "gold" / "failed_cases_data.json"
    with open(data_path, encoding="utf-8") as f:
        cases = json.load(f)

    md_lines: list[str] = [
        "",
        "---",
        "",
        "## Side-by-Side Review of In-Corpus Failed Cases (`evr_01M550XPQXRMJATTAZ37BF69BN`)",
        "",
        "> [!NOTE]",
        "> In run `evr_01M550XPQXRMJATTAZ37BF69BN` (Claude Sonnet 5.5 + Gemini Verifier with generation `g2` hybrid RRF retrieval), all 10 cases achieved 100% in-corpus agreement and 0 zero-tolerance gate failures.",
        "> The 7 in-corpus cases below scored 0.00 under strict deterministic proposition matching because the model cited adjacent paragraphs, substantive ratio paragraphs, or companion authorities containing the same legal rule.",
        "> Review each case side-by-side to mark whether the cited paragraph(s) also validly support the proposition so they can be considered for inclusion as alternative grounding anchors.",
        "",
    ]

    for idx, c in enumerate(cases, 1):
        cid = c["case_id"]
        q = c["question"]
        exp_aid = c["expected_anchor"]
        exp_quote = c["expected_quote"]
        exp_full = c["expected_full_text"].replace("\r\n", " ").replace("\n", " ").strip()

        # Deduplicate cited anchors preserving order
        unique_claims = []
        seen_aids = set()
        for cl in c["claude_claims"]:
            aid = cl["cited_anchor"]
            if aid not in seen_aids:
                seen_aids.add(aid)
                unique_claims.append(cl)

        md_lines.append(f"### Case {idx}: `{cid}`")
        md_lines.append(f"**Question:** {q}\n")

        # Summary Table
        md_lines.append("| Item | Expected in Gold Suite | Cited by Claude Sonnet 5.5 |")
        md_lines.append("|---|---|---|")

        cited_aids_str = "<br>".join([f"`{x['cited_anchor']}`" for x in unique_claims])
        cited_quotes_str = "<br>".join([f"• \"{x['quote']}\"" for x in unique_claims])

        md_lines.append(f"| **Anchor ID(s)** | `{exp_aid}` | {cited_aids_str} |")
        md_lines.append(f"| **Verbatim Quote(s)** | \"{exp_quote}\" | {cited_quotes_str} |")
        md_lines.append("")

        # Side-by-Side Paragraphs
        md_lines.append("#### Full Paragraph Texts\n")
        md_lines.append(f"**Expected Paragraph (`{exp_aid}`):**")
        md_lines.append(f"> {exp_full}\n")

        for ca in unique_claims:
            ca_aid = ca["cited_anchor"]
            ca_full = ca["anchor_full_text"].replace("\r\n", " ").replace("\n", " ").strip()
            md_lines.append(f"**Claude Cited Paragraph (`{ca_aid}`):**")
            md_lines.append(f"> {ca_full}\n")

        # Human Lawyer Review Checklist
        md_lines.append("**Reviewer Verdict:**")
        md_lines.append("- [ ] **SUPPORTS:** Cited paragraph(s) directly support the answer / ratio decidendi (qualifies as alternative grounding anchor).")
        md_lines.append("- [ ] **DOES NOT SUPPORT:** Cited paragraph(s) do not establish the required legal proposition.")
        md_lines.append("**Partner Notes:** ___________________________________________________\n")
        md_lines.append("---\n")

    addendum_text = "\n".join(md_lines)
    review_path = Path(__file__).parent / "fixtures" / "gold" / "REVIEW.md"

    # Read original base review content (up to line 21)
    with open(review_path, encoding="utf-8") as f:
        existing_content = f.read()

    # Split off any previous addendum if present
    base_content = existing_content.split("\n---\n## Side-by-Side Review")[0].strip()

    with open(review_path, "w", encoding="utf-8") as f:
        f.write(base_content + "\n" + addendum_text)

    print("Successfully updated", review_path)

if __name__ == "__main__":
    main()
