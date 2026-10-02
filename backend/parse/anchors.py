"""Anchor assignment and re-parse stability protocol.

Normative sources:
- docs/01_master_architecture.md §5.3 (anchor grammar v1.1) & §5.5 (stability rules)
- docs/03_P1_ingestion_parsing.md §5.10 (anchor assignment and stability protocol)
- User Directives:
  #2: anchor_alias.method in NUM_EQ|HASH_EQ|NW_ALIGN|SPLIT|MERGE|RENUMBER|GRAMMAR_V11
  #3: Unmatched new nodes with printed numbers keep p{n}
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Any

import xxhash

from anchor_lib import parse as parse_anchor
from anchor_lib.selectors import QuoteSelector
from parse.judgment import ParsedBlock
from parse.models import Anchor


def normalize_for_hashing(text: str) -> str:
    """Normalize whitespace and punctuation for canonical text hashing."""
    norm = re.sub(r"\s+", " ", text.strip().lower())
    norm = re.sub(r"[^\w\s]", "", norm)
    return norm


@dataclass(slots=True)
class AlignedAnchorNode:
    anchor_id: str
    fragment: str
    node_type: str
    number_as_printed: str | None
    numbering: str
    text: str
    text_hash: str
    quote_prefix: str = ""
    quote_suffix: str = ""
    spans: list[dict[str, Any]] = field(default_factory=list)
    ocr_conf: float = 1.0
    is_handwriting: bool = False
    state: str = "LIVE"
    forward_to: str | None = None
    children: list[AlignedAnchorNode] | None = None


@dataclass(slots=True)
class AnchorAlignmentResult:
    nodes: list[AlignedAnchorNode]
    anchor_changes: dict[str, int]  # preserved, aliased, tombstoned, new
    new_aliases: list[dict[str, Any]]  # old_anchor, new_anchor, method, confidence
    tombstoned_anchors: list[dict[str, Any]]  # anchor_id, forward_to


class AnchorAssigner:
    """Assigns and aligns anchors across re-parses with stability guarantees."""

    def assign_anchors(
        self,
        blocks: list[ParsedBlock],
        *,
        work_id: str,
        expression_key: str,
        full_doc_text: str = "",
        parse_id: str = "",
    ) -> AnchorAlignmentResult:
        """Assign anchors to blocks, aligning against existing anchors if re-parsing."""
        # 1. Fetch live existing anchors for this work and expression
        existing_anchors = list(
            Anchor.objects.filter(
                work_id=work_id,
                expression_key=expression_key,
                state="LIVE",
            )
        )

        existing_by_printed: dict[str, Anchor] = {}
        existing_by_hash: dict[str, list[Anchor]] = {}
        existing_by_frag: dict[str, Anchor] = {}
        all_existing_ids = {a.anchor_id for a in existing_anchors}

        for ea in existing_anchors:
            existing_by_frag[ea.fragment] = ea
            if ea.number_as_printed:
                existing_by_printed[ea.number_as_printed] = ea
            existing_by_hash.setdefault(ea.text_hash, []).append(ea)

        preserved = 0
        aliased = 0
        tombstoned = 0
        new_count = 0

        new_aliases: list[dict[str, Any]] = []
        tombstoned_records: list[dict[str, Any]] = []

        aligned_nodes: list[AlignedAnchorNode] = []
        claimed_old_ids: set[str] = set()

        # Track highest synthetic u number in existing
        max_u = 0
        for ea in existing_anchors:
            m = re.match(r"^u(\d+)$", ea.fragment)
            if m:
                max_u = max(max_u, int(m.group(1)))

        for block in blocks:
            # Normalized hash
            norm_text = normalize_for_hashing(block.text)
            thash = xxhash.xxh3_64_hexdigest(norm_text.encode("utf-8"))

            # Calculate quote selector context
            char_idx = (
                full_doc_text.find(block.text[:40])
                if len(block.text) >= 40
                else full_doc_text.find(block.text)
            )
            if char_idx != -1:
                start = char_idx
                end = min(len(full_doc_text), start + len(block.text))
                qs = QuoteSelector.from_text(full_doc_text, start, end, max_context=32)
                q_prefix = qs.prefix
                q_suffix = qs.suffix
            else:
                q_prefix = ""
                q_suffix = ""

            chosen_frag = block.fragment
            matched_old_id: str | None = None
            alias_method: str | None = None
            alias_conf: float = 1.0

            if existing_anchors:
                # Re-parse alignment protocol (01 §5.5, 03_P1 §5.10)
                # 1. NUM_EQ: Court printed number match
                if block.number_as_printed and block.number_as_printed in existing_by_printed:
                    candidate = existing_by_printed[block.number_as_printed]
                    if candidate.anchor_id not in claimed_old_ids:
                        sim = difflib.SequenceMatcher(None, block.text, candidate.text).ratio()
                        if sim >= 0.80:
                            matched_old_id = candidate.anchor_id
                            chosen_frag = candidate.fragment
                            claimed_old_ids.add(candidate.anchor_id)
                            preserved += 1
                            if sim < 0.95:
                                # Text changed slightly: record alias via NW_ALIGN per enum rule
                                alias_method = "NW_ALIGN"
                                alias_conf = round(sim, 4)

                # 2. HASH_EQ: Exact text_hash match anywhere in old
                if not matched_old_id and thash in existing_by_hash:
                    candidates = [
                        c for c in existing_by_hash[thash] if c.anchor_id not in claimed_old_ids
                    ]
                    if candidates:
                        candidate = candidates[0]
                        matched_old_id = candidate.anchor_id
                        chosen_frag = candidate.fragment
                        claimed_old_ids.add(candidate.anchor_id)
                        preserved += 1
                        if candidate.fragment != block.fragment:
                            alias_method = "HASH_EQ"
                            aliased += 1

                # 3. Fragment equality check (e.g. ord, u1)
                if not matched_old_id and block.fragment in existing_by_frag:
                    candidate = existing_by_frag[block.fragment]
                    if candidate.anchor_id not in claimed_old_ids:
                        sim = difflib.SequenceMatcher(None, block.text, candidate.text).ratio()
                        if sim >= 0.60:
                            matched_old_id = candidate.anchor_id
                            chosen_frag = candidate.fragment
                            claimed_old_ids.add(candidate.anchor_id)
                            preserved += 1
                            if sim < 0.95:
                                alias_method = "NW_ALIGN"
                                alias_conf = round(sim, 4)

            if not matched_old_id:
                # Unmatched new node (Directive #3)
                if block.numbering == "EXPLICIT":
                    # Keeps court-printed number (p{n})
                    chosen_frag = block.fragment
                elif block.fragment.startswith("u"):
                    # Synthetic unnumbered block gets fresh u{max_u + 1}
                    max_u += 1
                    chosen_frag = f"u{max_u}"
                else:
                    chosen_frag = block.fragment
                new_count += 1

            # Format PublicAnchor via anchor_lib
            anchor_ref = parse_anchor(f"{work_id}/{expression_key}#{chosen_frag}")
            anchor_id_str = str(anchor_ref)

            if alias_method and matched_old_id:
                new_aliases.append(
                    {
                        "old_anchor": matched_old_id,
                        "new_anchor": anchor_id_str,
                        "method": alias_method,
                        "confidence": alias_conf,
                    }
                )

            aligned_nodes.append(
                AlignedAnchorNode(
                    anchor_id=anchor_id_str,
                    fragment=chosen_frag,
                    node_type=block.node_type,
                    number_as_printed=block.number_as_printed,
                    numbering=block.numbering,
                    text=block.text,
                    text_hash=thash,
                    quote_prefix=q_prefix,
                    quote_suffix=q_suffix,
                    spans=block.spans,
                    ocr_conf=block.ocr_conf,
                    is_handwriting=block.is_handwriting,
                    state="LIVE",
                )
            )

        # 4. Check for tombstoned old anchors — find best-overlap forward_to
        unclaimed_old = all_existing_ids - claimed_old_ids
        # Build lookup for old anchor text
        existing_by_id = {a.anchor_id: a for a in existing_anchors}
        for old_id in unclaimed_old:
            tombstoned += 1
            old_anchor = existing_by_id.get(old_id)
            old_text = old_anchor.text if old_anchor else ""

            # Find best-overlap new anchor by text similarity
            best_forward: str | None = None
            best_sim = 0.0
            for new_node in aligned_nodes:
                sim = difflib.SequenceMatcher(None, old_text, new_node.text).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_forward = new_node.anchor_id

            # Only set forward_to if similarity meets threshold
            if best_sim < 0.50:
                best_forward = None

            tombstoned_records.append(
                {
                    "anchor_id": old_id,
                    "forward_to": best_forward,
                }
            )

        anchor_changes = {
            "preserved": preserved,
            "aliased": aliased,
            "tombstoned": tombstoned,
            "new": new_count,
        }

        return AnchorAlignmentResult(
            nodes=aligned_nodes,
            anchor_changes=anchor_changes,
            new_aliases=new_aliases,
            tombstoned_anchors=tombstoned_records,
        )
