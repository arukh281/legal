"""Test suite for anchor assignment stability protocol and re-parse canaries.

Normative references:
- docs/01_master_architecture.md §5.5 (stability rules)
- docs/03_P1_ingestion_parsing.md §5.10 (anchor assignment and stability protocol)
- User Directive #2 (anchor_alias.method enum & tombstones on state/forward_to)
- User Directive #3 (unmatched new nodes: court-numbered keep p{n}, only unnumbered get u{n})
"""

from __future__ import annotations

from pathlib import Path

import pytest

from parse.anchors import AnchorAssigner
from parse.consumer import persist_pipeline_result
from parse.judgment import ParsedBlock
from parse.models import Anchor, Work
from parse.pipeline import ParsingPipeline


@pytest.mark.django_db
class TestAnchorStability:
    """Verifies anchor stability and alias creation across re-parse cycles."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.pipeline = ParsingPipeline()
        self.assigner = AnchorAssigner()
        self.repo_root = Path(__file__).resolve().parent.parent.parent.parent

    def test_reparse_unchanged_document_100_percent_stable(self) -> None:
        pdf_path = self.repo_root / "eval" / "fixtures" / "ibbi" / "nclt_born_digital_chd.pdf"
        raw_bytes = pdf_path.read_bytes()

        # Run 1: initial parse
        res1 = self.pipeline.run(raw_bytes, source_metadata={"mime": "application/pdf"})
        assert len(res1.nodes) >= 5

        # Persist Run 1
        persist_pipeline_result(
            res1, source_id="src_ibbi", raw_id="raw_test_1", url="http://test/1"
        )

        # Run 2: re-parse with same work_id
        res2 = self.pipeline.run(
            raw_bytes,
            existing_work_id=res1.work_id,
            source_metadata={"mime": "application/pdf"},
        )

        assert res2.anchor_changes["preserved"] == len(res1.nodes)
        assert res2.anchor_changes["aliased"] == 0
        assert res2.anchor_changes["tombstoned"] == 0
        assert res2.anchor_changes["new"] == 0
        assert len(res2.new_aliases) == 0

    def test_text_amendment_triggers_nw_align_alias(self) -> None:
        work_id = "wrk_01H1234567890ABCDEFGHJKMNP"
        blocks_v1 = [
            ParsedBlock(
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="The Corporate Debtor owes an operational debt of Rs. 10 Crores to the applicant.",
            ),
            ParsedBlock(
                fragment="p2",
                node_type="PARA",
                number_as_printed="2",
                numbering="EXPLICIT",
                text="Default occurred on 15.01.2025 and remained unpaid despite demand notice.",
            ),
        ]

        # Initial assignment
        Work.objects.get_or_create(
            work_id=work_id, defaults={"work_type": "JUDGMENT", "status": "ACTIVE"}
        )
        res_v1 = self.assigner.assign_anchors(blocks_v1, work_id=work_id, expression_key="en")
        assert len(res_v1.nodes) == 2
        for n in res_v1.nodes:
            Anchor.objects.create(
                anchor_id=n.anchor_id,
                work_id=work_id,
                expression_key="en",
                fragment=n.fragment,
                node_type=n.node_type,
                number_as_printed=n.number_as_printed,
                numbering=n.numbering,
                text=n.text,
                text_hash=n.text_hash,
                state="LIVE",
                first_parse_id="par_1",
                last_parse_id="par_1",
                lang="en",
                is_authoritative_expression=True,
            )

        # Version 2 with minor clerical amendment to paragraph 1 text
        blocks_v2 = [
            ParsedBlock(
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="The Corporate Debtor owes an operational debt of Rs. 10,00,00,000/- (Rupees Ten Crores) to the applicant.",
            ),
            ParsedBlock(
                fragment="p2",
                node_type="PARA",
                number_as_printed="2",
                numbering="EXPLICIT",
                text="Default occurred on 15.01.2025 and remained unpaid despite demand notice.",
            ),
        ]

        res_v2 = self.assigner.assign_anchors(blocks_v2, work_id=work_id, expression_key="en")
        # Preserved via NUM_EQ + NW_ALIGN for text change
        assert res_v2.anchor_changes["preserved"] == 2
        assert len(res_v2.new_aliases) == 1
        alias = res_v2.new_aliases[0]
        # Must be NW_ALIGN with correct confidence and anchor IDs
        assert alias["method"] == "NW_ALIGN"
        assert 0.80 <= alias["confidence"] < 0.95
        assert alias["old_anchor"] == f"{work_id}/en#p1"
        assert alias["new_anchor"] == f"{work_id}/en#p1"

    def test_paragraph_deletion_records_tombstone(self) -> None:
        work_id = "wrk_01H1234567890ABCDEFGHJKMNQ"
        blocks_v1 = [
            ParsedBlock(
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="Paragraph 1 text content about the Corporate Debtor and insolvency.",
            ),
            ParsedBlock(
                fragment="p2",
                node_type="PARA",
                number_as_printed="2",
                numbering="EXPLICIT",
                text="Paragraph 2 about the Corporate Debtor insolvency will be deleted.",
            ),
            ParsedBlock(
                fragment="p3",
                node_type="PARA",
                number_as_printed="3",
                numbering="EXPLICIT",
                text="XYZZY completely unrelated gibberish text with no overlap at all.",
            ),
        ]

        Work.objects.get_or_create(
            work_id=work_id, defaults={"work_type": "JUDGMENT", "status": "ACTIVE"}
        )
        res_v1 = self.assigner.assign_anchors(blocks_v1, work_id=work_id, expression_key="en")
        for n in res_v1.nodes:
            Anchor.objects.create(
                anchor_id=n.anchor_id,
                work_id=work_id,
                expression_key="en",
                fragment=n.fragment,
                node_type=n.node_type,
                number_as_printed=n.number_as_printed,
                numbering=n.numbering,
                text=n.text,
                text_hash=n.text_hash,
                state="LIVE",
                first_parse_id="par_1",
                last_parse_id="par_1",
                lang="en",
                is_authoritative_expression=True,
            )

        # Version 2 with paragraphs 2 and 3 deleted
        blocks_v2 = [
            ParsedBlock(
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text="Paragraph 1 text content about the Corporate Debtor and insolvency.",
            ),
        ]

        res_v2 = self.assigner.assign_anchors(blocks_v2, work_id=work_id, expression_key="en")
        assert res_v2.anchor_changes["tombstoned"] == 2
        assert len(res_v2.tombstoned_anchors) == 2

        tombs_by_id = {t["anchor_id"]: t for t in res_v2.tombstoned_anchors}

        # p2 had similar text to p1 (both about Corporate Debtor insolvency)
        tomb_p2 = tombs_by_id[f"{work_id}/en#p2"]
        assert tomb_p2["forward_to"] == f"{work_id}/en#p1"

        # p3 had completely unrelated text — no good match, forward_to is None
        tomb_p3 = tombs_by_id[f"{work_id}/en#p3"]
        assert tomb_p3["forward_to"] is None

    def test_tombstone_fallback_requires_40_chars_and_single_match(self) -> None:
        """Item 0: containment/QuoteSelector fallback only applies when old text >= 40 chars

        and matches exactly one new node; otherwise forward_to stays null.
        """
        work_id = "wrk_01H9999999999ABCDEFGHJKMNP"
        Work.objects.get_or_create(
            work_id=work_id, defaults={"work_type": "JUDGMENT", "status": "ACTIVE"}
        )

        # 3 old anchors:
        # p1: short text (< 40 chars) -> "Short text under 40." (20 chars)
        # p2: text >= 40 chars matching exactly ONE new node
        # p3: text >= 40 chars matching TWO new nodes (ambiguous)
        old_short_text = "Short text under 40."
        assert len(old_short_text) < 40

        old_single_match_text = "The Adjudicating Authority held that notice was properly served on respondent."
        assert len(old_single_match_text) >= 40

        old_ambiguous_text = "Standard clause repeated verbatim across multiple orders in this tribunal."
        assert len(old_ambiguous_text) >= 40

        blocks_v1 = [
            ParsedBlock(
                fragment="p1",
                node_type="PARA",
                number_as_printed="1",
                numbering="EXPLICIT",
                text=old_short_text,
            ),
            ParsedBlock(
                fragment="p2",
                node_type="PARA",
                number_as_printed="2",
                numbering="EXPLICIT",
                text=old_single_match_text,
            ),
            ParsedBlock(
                fragment="p3",
                node_type="PARA",
                number_as_printed="3",
                numbering="EXPLICIT",
                text=old_ambiguous_text,
            ),
        ]
        res_v1 = self.assigner.assign_anchors(blocks_v1, work_id=work_id, expression_key="en")
        for n in res_v1.nodes:
            Anchor.objects.create(
                anchor_id=n.anchor_id,
                work_id=work_id,
                expression_key="en",
                fragment=n.fragment,
                node_type=n.node_type,
                number_as_printed=n.number_as_printed,
                numbering=n.numbering,
                text=n.text,
                text_hash=n.text_hash,
                state="LIVE",
                first_parse_id="par_1",
                last_parse_id="par_1",
                lang="en",
                is_authoritative_expression=True,
            )

        # In version 2, p1, p2, p3 are deleted.
        # Node A contains old_short_text (similarity < 0.50 because Node A is 250 chars)
        # Node B contains old_single_match_text (similarity < 0.50 because Node B is 300 chars)
        # Node C and Node D BOTH contain old_ambiguous_text (similarity < 0.50)
        blocks_v2 = [
            ParsedBlock(
                fragment="p10",
                node_type="PARA",
                number_as_printed="10",
                numbering="EXPLICIT",
                text=(
                    "Introductory discourse on corporate insolvency process under Indian laws. "
                    + old_short_text
                    + " Additional long prose continuing for many sentences to ensure overall similarity stays below 0.50 threshold."
                ),
            ),
            ParsedBlock(
                fragment="p20",
                node_type="PARA",
                number_as_printed="20",
                numbering="EXPLICIT",
                text=(
                    "Comprehensive reasoning on procedural notices in insolvency applications. "
                    + old_single_match_text
                    + " Further extensive discussion regarding compliance and service requirements under NCLT procedural rules."
                ),
            ),
            ParsedBlock(
                fragment="p30",
                node_type="PARA",
                number_as_printed="30",
                numbering="EXPLICIT",
                text=(
                    "First operative section discussing boilerplate directives in long detail. "
                    "This paragraph contains extensive narrative background explaining why the order is necessary. "
                    + old_ambiguous_text
                    + " Concluding extensive directions issued to the resolution professional with further legal citations and remarks."
                ),
            ),
            ParsedBlock(
                fragment="p40",
                node_type="PARA",
                number_as_printed="40",
                numbering="EXPLICIT",
                text=(
                    "Second operative section discussing boilerplate directives in long detail. "
                    "This paragraph contains extensive narrative background explaining why the order is necessary. "
                    + old_ambiguous_text
                    + " Concluding extensive directions issued to the resolution professional with further legal citations and remarks."
                ),
            ),
        ]

        res_v2 = self.assigner.assign_anchors(blocks_v2, work_id=work_id, expression_key="en")
        tombs = {t["anchor_id"]: t for t in res_v2.tombstoned_anchors}

        # 1. Old p1 text < 40 chars -> forward_to stays None even though contained in p10
        assert tombs[f"{work_id}/en#p1"]["forward_to"] is None

        # 2. Old p2 text >= 40 chars matching exactly ONE new node (p20) -> forward_to == p20
        assert tombs[f"{work_id}/en#p2"]["forward_to"] == f"{work_id}/en#p20"

        # 3. Old p3 text >= 40 chars matching TWO new nodes (p30 and p40) -> ambiguous, forward_to stays None
        assert tombs[f"{work_id}/en#p3"]["forward_to"] is None
