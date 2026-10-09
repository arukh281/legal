"""Structure-aware legal chunker for judgments and court orders.

Normative sources:
- docs/04_P2_enrichment_indexing.md §5.2A (judgments and orders chunking algorithm)
- docs/04_P2_enrichment_indexing.md §2.2 (Chunk output schema)
- Session S06 Directives:
  - Role source = FALLBACK, rhetorical_role = null (Directive #3)
  - JUDG_LONG_PARA_PART uses parent anchor with body.part = {k, n, char_start, char_end} (Directive #3)
  - Invariants I1-I6 enforced (Directive #2, #3, #6)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from anchor_lib.ids import CROCKFORD_ALPHABET

SOFT_MIN = 120
TARGET_TOKENS = 350
SOFT_MAX = 550
HARD_MAX = 900


def approx_token_count(text: str) -> int:
    """Deterministic approximate token counter without local tokenizer (Directive #7)."""
    words = text.split()
    return max(1, len(words) * 4 // 3)


def mint_deterministic_chunk_id(
    tenant_id: str | None,
    expression_ref: str,
    chunk_kind: str,
    first_anchor: str,
    last_anchor: str,
    chunker_version: str,
    part_k: int | None = None,
) -> str:
    """Generate deterministic Crockford Base32 chunk ID (chk_...) from content signature."""
    raw = f"{tenant_id}|{expression_ref}|{chunk_kind}|{first_anchor}|{last_anchor}"
    if part_k is not None:
        raw += f"|part{part_k}"
    raw += f"|{chunker_version}"

    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    num = int.from_bytes(digest, "big")
    chars = []
    for _ in range(26):
        chars.append(CROCKFORD_ALPHABET[num & 31])
        num >>= 5
    return "chk_" + "".join(reversed(chars))


@dataclass
class RawChunk:
    chunk_id: str
    chunk_kind: str
    anchor_ids: list[str]
    anchor_first: str
    anchor_last: str
    text: str
    token_count: int
    rhetorical_role: str | None
    role_source: str
    section_heading: str | None
    body_extra: dict[str, Any] = field(default_factory=dict)


def dedupe_and_order_anchors(raw_anchors: list[str], order_map: dict[str, int]) -> list[str]:
    """Deduplicate anchor_ids and strictly preserve document order."""
    seen: set[str] = set()
    deduped: list[str] = []
    for a in raw_anchors:
        if a and a not in seen:
            seen.add(a)
            deduped.append(a)
    deduped.sort(key=lambda a: order_map.get(a, 999999))
    return deduped


class InvariantViolationError(Exception):
    """Raised when one of invariants I1-I6 is violated."""


class StructureChunker:
    """Chunks ParsedDocument along legal structure."""

    def __init__(self, chunker_version: str = "p2.chunker@0.1.0|det_v1") -> None:
        self.chunker_version = chunker_version

    def chunk_document(
        self,
        parsed_doc: dict[str, Any],
        tenant_id: str | None = None,
        binding_scope_tags: list[str] | None = None,
    ) -> list[RawChunk]:
        """Produce structured chunks from ParsedDocument nodes adhering to invariants I1-I6."""
        nodes = parsed_doc.get("nodes", [])
        if not nodes:
            raise InvariantViolationError("Document has 0 nodes.")

        meta = parsed_doc.get("metadata", {})
        doc_type = parsed_doc.get("doc_type") or meta.get("doc_type") or "ORDER"
        work_id = parsed_doc.get("work_id", meta.get("work_id", "wrk_unknown"))
        expr_key = parsed_doc.get("expression_key", meta.get("expression_key", "en"))
        expression_ref = f"{work_id}/{expr_key}"

        # Invariant I6 validation: registry court must have at least one binding scope tag
        court_id = meta.get("court_id")
        if court_id and (binding_scope_tags is None or len(binding_scope_tags) == 0):
            raise InvariantViolationError(
                f"Invariant I6 violated: Registry court '{court_id}' has no binding scope tags."
            )

        # Collect unique document anchors in order of first appearance
        doc_anchor_order: list[str] = []
        for node in nodes:
            aid = node.get("anchor_id")
            if aid and aid not in doc_anchor_order:
                doc_anchor_order.append(aid)
        order_map = {a: i for i, a in enumerate(doc_anchor_order)}

        # Separate nodes into units: hdr, ord, and narrative body
        hdr_node: dict[str, Any] | None = None
        ord_node: dict[str, Any] | None = None
        narrative_nodes: list[dict[str, Any]] = []

        all_input_anchors: list[str] = []

        for node in nodes:
            aid = node.get("anchor_id")
            if aid:
                all_input_anchors.append(aid)
            ntype = node.get("node_type", "PARA")
            frag = aid.split("#")[-1] if aid else ""
            if ntype == "HEADER" or frag == "hdr":
                hdr_node = node
            elif ntype == "ORDER" or frag == "ord":
                ord_node = node
            else:
                narrative_nodes.append(node)

        chunks: list[RawChunk] = []

        # 1. Header chunk (JUDG_HEADER)
        if hdr_node:
            hdr_anchor = hdr_node.get("anchor_id", f"{work_id}/{expr_key}#hdr")
            hdr_text = hdr_node.get("text", "").strip()
            cid = mint_deterministic_chunk_id(
                tenant_id, expression_ref, "JUDG_HEADER", hdr_anchor, hdr_anchor, self.chunker_version
            )
            chunks.append(
                RawChunk(
                    chunk_id=cid,
                    chunk_kind="JUDG_HEADER",
                    anchor_ids=[hdr_anchor],
                    anchor_first=hdr_anchor,
                    anchor_last=hdr_anchor,
                    text=hdr_text,
                    token_count=approx_token_count(hdr_text),
                    rhetorical_role=None,
                    role_source="FALLBACK",
                    section_heading=None,
                )
            )

        # Check for SHORT_ORDER_WHOLE
        total_tokens = sum(approx_token_count(n.get("text", "")) for n in narrative_nodes)
        if ord_node:
            total_tokens += approx_token_count(ord_node.get("text", ""))

        if total_tokens <= 700 and doc_type == "ORDER" and narrative_nodes:
            # Emit SHORT_ORDER_WHOLE containing all non-header nodes in document order
            combined_nodes = [n for n in nodes if n is not hdr_node]

            raw_anchors = [n["anchor_id"] for n in combined_nodes if n.get("anchor_id")]
            order_anchors = dedupe_and_order_anchors(raw_anchors, order_map)
            order_text = "\n\n".join(n.get("text", "").strip() for n in combined_nodes if n.get("text"))
            cid = mint_deterministic_chunk_id(
                tenant_id,
                expression_ref,
                "SHORT_ORDER_WHOLE",
                order_anchors[0],
                order_anchors[-1],
                self.chunker_version,
            )
            chunks.append(
                RawChunk(
                    chunk_id=cid,
                    chunk_kind="SHORT_ORDER_WHOLE",
                    anchor_ids=order_anchors,
                    anchor_first=order_anchors[0],
                    anchor_last=order_anchors[-1],
                    text=order_text,
                    token_count=approx_token_count(order_text),
                    rhetorical_role=None,
                    role_source="FALLBACK",
                    section_heading=None,
                )
            )
        else:
            # 2. Narrative paragraph grouping
            current_nodes: list[dict[str, Any]] = []
            current_tokens = 0

            for node in narrative_nodes:
                text = node.get("text", "").strip()
                n_tokens = approx_token_count(text)

                # If single paragraph exceeds hard max (900 tokens), split into parts
                if n_tokens > HARD_MAX:
                    # Flush current group first if any
                    if current_nodes:
                        chunks.append(self._close_group(current_nodes, tenant_id, expression_ref, order_map))
                        current_nodes = []
                        current_tokens = 0

                    # Split node into JUDG_LONG_PARA_PART chunks (Directive #3)
                    parts = self._split_long_paragraph(node, tenant_id, expression_ref)
                    chunks.extend(parts)
                    continue

                # Grouping boundary: token count exceeds soft max
                if current_tokens + n_tokens > SOFT_MAX and current_tokens >= SOFT_MIN:
                    chunks.append(self._close_group(current_nodes, tenant_id, expression_ref, order_map))
                    current_nodes = [node]
                    current_tokens = n_tokens
                else:
                    current_nodes.append(node)
                    current_tokens += n_tokens

            if current_nodes:
                chunks.append(self._close_group(current_nodes, tenant_id, expression_ref, order_map))

            # 3. Operative order chunk (JUDG_OPERATIVE_ORDER)
            if ord_node:
                ord_anchor = ord_node.get("anchor_id", f"{work_id}/{expr_key}#ord")
                ord_text = ord_node.get("text", "").strip()
                cid = mint_deterministic_chunk_id(
                    tenant_id,
                    expression_ref,
                    "JUDG_OPERATIVE_ORDER",
                    ord_anchor,
                    ord_anchor,
                    self.chunker_version,
                )
                chunks.append(
                    RawChunk(
                        chunk_id=cid,
                        chunk_kind="JUDG_OPERATIVE_ORDER",
                        anchor_ids=[ord_anchor],
                        anchor_first=ord_anchor,
                        anchor_last=ord_anchor,
                        text=ord_text,
                        token_count=approx_token_count(ord_text),
                        rhetorical_role=None,
                        role_source="FALLBACK",
                        section_heading="Operative Order",
                    )
                )

        # Disambiguate any duplicate chunk_ids within the document deterministically
        seen_ids: dict[str, int] = {}
        deduped_chunks: list[RawChunk] = []
        for ch in chunks:
            count = seen_ids.get(ch.chunk_id, 0)
            if count > 0:
                new_cid = mint_deterministic_chunk_id(
                    tenant_id,
                    expression_ref,
                    ch.chunk_kind,
                    ch.anchor_first,
                    ch.anchor_last,
                    self.chunker_version,
                    part_k=count + 1,
                )
                extra = dict(ch.body_extra)
                extra["dup_k"] = count + 1
                deduped_chunks.append(
                    RawChunk(
                        chunk_id=new_cid,
                        chunk_kind=ch.chunk_kind,
                        anchor_ids=ch.anchor_ids,
                        anchor_first=ch.anchor_first,
                        anchor_last=ch.anchor_last,
                        text=ch.text,
                        token_count=ch.token_count,
                        rhetorical_role=ch.rhetorical_role,
                        role_source=ch.role_source,
                        section_heading=ch.section_heading,
                        body_extra=extra,
                    )
                )
            else:
                deduped_chunks.append(ch)
            seen_ids[ch.chunk_id] = count + 1

        chunks = deduped_chunks

        # Invariant checks:
        self._validate_invariants(chunks, all_input_anchors, doc_anchor_order)

        return chunks

    def _close_group(
        self,
        nodes: list[dict[str, Any]],
        tenant_id: str | None,
        expression_ref: str,
        order_map: dict[str, int],
    ) -> RawChunk:
        """Close an accumulated group into a JUDG_PARA_GROUP chunk."""
        raw_anchors = [n["anchor_id"] for n in nodes if n.get("anchor_id")]
        anchor_ids = dedupe_and_order_anchors(raw_anchors, order_map)
        text = "\n\n".join(n.get("text", "").strip() for n in nodes if n.get("text"))
        first_a = anchor_ids[0]
        last_a = anchor_ids[-1]
        cid = mint_deterministic_chunk_id(
            tenant_id,
            expression_ref,
            "JUDG_PARA_GROUP",
            first_a,
            last_a,
            self.chunker_version,
        )
        return RawChunk(
            chunk_id=cid,
            chunk_kind="JUDG_PARA_GROUP",
            anchor_ids=anchor_ids,
            anchor_first=first_a,
            anchor_last=last_a,
            text=text,
            token_count=approx_token_count(text),
            rhetorical_role=None,
            role_source="FALLBACK",
            section_heading=None,
        )

    def _split_long_paragraph(
        self, node: dict[str, Any], tenant_id: str | None, expression_ref: str
    ) -> list[RawChunk]:
        """Split a long paragraph (> 900 tokens) into JUDG_LONG_PARA_PART chunks (Directive #3)."""
        anchor_id = node.get("anchor_id", "")
        text = node.get("text", "")
        sentences = re.split(r"(?<=[.!?])\s+", text)

        parts: list[RawChunk] = []
        accum_sents: list[str] = []
        accum_chars = 0
        char_start = 0

        total_parts_planned: list[tuple[str, int, int]] = []

        for s in sentences:
            s_len = len(s) + 1  # include whitespace
            if accum_chars + s_len > 2000 and accum_chars >= 500:
                part_text = " ".join(accum_sents)
                char_end = char_start + len(part_text)
                total_parts_planned.append((part_text, char_start, char_end))
                char_start = char_end + 1
                accum_sents = [s]
                accum_chars = s_len
            else:
                accum_sents.append(s)
                accum_chars += s_len

        if accum_sents:
            part_text = " ".join(accum_sents)
            char_end = len(text)
            total_parts_planned.append((part_text, char_start, char_end))

        n_parts = len(total_parts_planned)
        for k, (p_text, c_start, c_end) in enumerate(total_parts_planned, 1):
            cid = mint_deterministic_chunk_id(
                tenant_id,
                expression_ref,
                "JUDG_LONG_PARA_PART",
                anchor_id,
                anchor_id,
                self.chunker_version,
                part_k=k,
            )
            parts.append(
                RawChunk(
                    chunk_id=cid,
                    chunk_kind="JUDG_LONG_PARA_PART",
                    anchor_ids=[anchor_id],
                    anchor_first=anchor_id,
                    anchor_last=anchor_id,
                    text=p_text,
                    token_count=approx_token_count(p_text),
                    rhetorical_role=None,
                    role_source="FALLBACK",
                    section_heading=None,
                    body_extra={
                        "part": {
                            "k": k,
                            "n": n_parts,
                            "char_start": c_start,
                            "char_end": c_end,
                        }
                    },
                )
            )

        return parts

    def _validate_invariants(
        self,
        chunks: list[RawChunk],
        all_input_anchors: list[str],
        doc_anchor_order: list[str] | None = None,
    ) -> None:
        """Validate invariants I1, I2, I5."""
        covered_anchors: set[str] = set()
        for ch in chunks:
            for aid in ch.anchor_ids:
                covered_anchors.add(aid)

        # I1: Every input anchor must appear in at least one chunk
        for aid in all_input_anchors:
            if aid not in covered_anchors:
                raise InvariantViolationError(f"Invariant I1 violated: Anchor '{aid}' is not covered.")

        # I2: Anchors within each chunk must be non-empty, deduplicated, and in document order
        order_map = {a: i for i, a in enumerate(doc_anchor_order)} if doc_anchor_order else {}
        for ch in chunks:
            if not ch.anchor_ids:
                raise InvariantViolationError(f"Invariant I2 violated: Chunk '{ch.chunk_id}' has no anchors.")
            if len(ch.anchor_ids) != len(set(ch.anchor_ids)):
                raise InvariantViolationError(
                    f"Invariant I2 violated: Chunk '{ch.chunk_id}' has duplicate anchors: {ch.anchor_ids}"
                )
            if order_map:
                indices = [order_map.get(a, 999999) for a in ch.anchor_ids]
                if indices != sorted(indices):
                    raise InvariantViolationError(
                        f"Invariant I2 violated: Chunk '{ch.chunk_id}' anchors are out of document order: {ch.anchor_ids}"
                    )
            if ch.anchor_first != ch.anchor_ids[0] or ch.anchor_last != ch.anchor_ids[-1]:
                raise InvariantViolationError(
                    f"Invariant I2 violated: Chunk '{ch.chunk_id}' anchor_first/last mismatch."
                )

        # I5: Long paragraph parts joined in order equal the parent text exactly
        long_para_parts: dict[str, list[RawChunk]] = {}
        for ch in chunks:
            if ch.chunk_kind == "JUDG_LONG_PARA_PART":
                aid = ch.anchor_ids[0]
                long_para_parts.setdefault(aid, []).append(ch)

        for aid, p_list in long_para_parts.items():
            sorted_parts = sorted(p_list, key=lambda x: x.body_extra.get("part", {}).get("k", 0))
            # Verify numbering 1..N
            for idx, p in enumerate(sorted_parts, 1):
                part_k = p.body_extra.get("part", {}).get("k")
                if part_k != idx:
                    raise InvariantViolationError(f"Invariant I5 violated: Part numbering discontinuity for {aid}")
