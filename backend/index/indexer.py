"""Index pipeline: structures parsed documents into searchable chunks.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5 (plc.chunk, plc.index_expression_state)
- docs/04_P2_enrichment_indexing.md §2.2, §2.4, §2.5, §2.7, §5.1-5.6
- Directives 1-6 approved by aru:
  #1: Lexemes via setweight(array_to_tsvector($lexemes::text[]), 'C') on index, quoted tsquery on query
  #3: I6 null decision_date uses registry row with unbounded valid_period
  #4: On identity.merged.v1, from_id state is REKEYED, not SUPERSEDED_REV
  #5: Forced re-index path for identity events and index_corpus (monotonic doc_seq, bypass stale check)
  #6: Quarantine re-parse keeps good chunk set live; records last_quarantined_parse_id & quarantine_reasons
"""

from __future__ import annotations

import datetime
import functools
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from django.db import connection, transaction
from django.utils import timezone

from anchor_lib.ids import mint_id
from gateway.runner import embed
from index.chunker import InvariantViolationError, StructureChunker
from index.headers import build_context_header
from index.models import IndexExpressionState
from index.normalizer import extract_legal_lexemes
from index.storage import fetch_parsed_document
from ops.models import EventOutbox

logger = logging.getLogger(__name__)

PIPELINE_VERSION_P2 = "p2.index@0.1.0|g1"
CHUNKER_VERSION = "p2.chunker@0.1.0|det_v1"
EMBED_MODEL = "voyage-4-large"
EMBED_DIMS = 1024


@dataclass(frozen=True, slots=True)
class IndexResult:
    """Outcome of indexing an expression."""

    work_id: str
    expression_key: str
    generation: str
    chunk_count: int = 0
    doc_seq: int = 0
    quarantined: bool = False
    quarantine_reasons: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str | None = None


class IndexPipeline:
    """Pipeline converting canonical parsed documents into indexed retrieval chunks."""

    def __init__(self, generation: str = "g1") -> None:
        self.generation = generation
        self.chunker = StructureChunker(chunker_version=CHUNKER_VERSION)

    def _resolve_binding_scope_tags(
        self, court_id: str | None, decision_date: datetime.date | None
    ) -> list[str]:
        """Resolve binding_scope_tags from plc.court per Directive #3.

        - If court_id is set and found in plc.court:
          - If decision_date is not None, match valid_period @> decision_date.
          - If decision_date is None, use registry row whose valid_period is unbounded above.
          - I6 applies: if no tags resolved, raise InvariantViolationError.
        - If court_id is None or not in plc.court, returns empty list (I6 does not apply).
        """
        if not court_id:
            return []

        with connection.cursor() as cur:
            # Check if court exists in registry
            cur.execute("SELECT 1 FROM plc.court WHERE court_id = %s LIMIT 1;", [court_id])
            if not cur.fetchone():
                return []

            if decision_date is not None:
                cur.execute(
                    """
                    SELECT binding_scope_tags FROM plc.court
                    WHERE court_id = %s AND valid_period @> %s::date
                    LIMIT 1;
                    """,
                    [court_id, decision_date],
                )
            else:
                cur.execute(
                    """
                    SELECT binding_scope_tags FROM plc.court
                    WHERE court_id = %s AND upper(valid_period) IS NULL
                    LIMIT 1;
                    """,
                    [court_id],
                )

            row = cur.fetchone()
            tags = list(row[0]) if (row and row[0]) else []

            if not tags:
                raise InvariantViolationError(
                    f"Invariant I6 violated: Court '{court_id}' in registry but has no binding_scope_tags."
                )
            return tags

    def index_expression(
        self,
        work_id: str,
        expression_key: str = "en",
        parse_id: str | None = None,
        force: bool = False,
        generation: str | None = None,
    ) -> IndexResult:
        """Index a single expression into the specified or default generation partition."""
        target_gen = generation or self.generation
        serial_key = f"{work_id}/{expression_key}"

        # 1. Fetch work status
        with connection.cursor() as cur:
            cur.execute("SELECT status FROM plc.work WHERE work_id = %s;", [work_id])
            w_row = cur.fetchone()
            if not w_row:
                return IndexResult(
                    work_id=work_id,
                    expression_key=expression_key,
                    generation=target_gen,
                    skipped=True,
                    skip_reason=f"Work '{work_id}' not found.",
                )
            work_status = w_row[0]
            if work_status in ("MERGED", "STUB"):
                return IndexResult(
                    work_id=work_id,
                    expression_key=expression_key,
                    generation=target_gen,
                    skipped=True,
                    skip_reason=f"Work '{work_id}' is canonical status '{work_status}'.",
                )

        # 2. Fetch parse_run
        with connection.cursor() as cur:
            if parse_id:
                cur.execute(
                    """
                    SELECT p.parse_id, p.parsed_doc_uri, p.gate,
                           w.court_id, w.decision_date, p.doc_type, w.title
                    FROM plc.parse_run p
                    JOIN plc.work w ON w.work_id = p.work_id
                    WHERE p.work_id = %s AND p.expression_key = %s AND p.parse_id = %s
                    LIMIT 1;
                    """,
                    [work_id, expression_key, parse_id],
                )
            else:
                cur.execute(
                    """
                    SELECT p.parse_id, p.parsed_doc_uri, p.gate,
                           w.court_id, w.decision_date, p.doc_type, w.title
                    FROM plc.parse_run p
                    JOIN plc.work w ON w.work_id = p.work_id
                    WHERE p.work_id = %s AND p.expression_key = %s
                    ORDER BY p.parse_id DESC
                    LIMIT 1;
                    """,
                    [work_id, expression_key],
                )
            p_row = cur.fetchone()

        if not p_row:
            return IndexResult(
                work_id=work_id,
                expression_key=expression_key,
                generation=target_gen,
                skipped=True,
                skip_reason="No accepted parse run found.",
            )

        (
            actual_parse_id,
            parsed_doc_uri,
            quality_gate,
            court_id,
            decision_date,
            doc_type,
            title,
        ) = p_row

        # Check existing state
        existing_state = IndexExpressionState.objects.filter(serial_key=serial_key).first()

        # 3. Handle QUARANTINED parse runs (P1 quality gate) per Directive #6
        if quality_gate == "QUARANTINED":
            return self._handle_quarantine(
                serial_key,
                work_id,
                expression_key,
                actual_parse_id,
                ["P1 quality gate QUARANTINED"],
                existing_state,
                target_gen,
            )

        # 4. Monotonic parse_id check (stale event check) per Directive #5
        if not force and existing_state and existing_state.accepted_parse_id:
            # Drop if not strictly newer
            if actual_parse_id <= existing_state.accepted_parse_id:
                return IndexResult(
                    work_id=work_id,
                    expression_key=expression_key,
                    generation=target_gen,
                    skipped=True,
                    skip_reason=f"Stale parse_id '{actual_parse_id}' <= '{existing_state.accepted_parse_id}'.",
                )

        # 5. Fetch ParsedDocument JSON
        parsed_doc = fetch_parsed_document(parsed_doc_uri)

        # 6. Resolve binding_scope_tags & validate I6
        try:
            binding_scope_tags = self._resolve_binding_scope_tags(court_id, decision_date)
            # Run StructureChunker
            raw_chunks = self.chunker.chunk_document(parsed_doc, tenant_id=None)
        except InvariantViolationError as exc:
            return self._handle_quarantine(
                serial_key,
                work_id,
                expression_key,
                actual_parse_id,
                [str(exc)],
                existing_state,
                target_gen,
            )

        if not raw_chunks:
            return self._handle_quarantine(
                serial_key,
                work_id,
                expression_key,
                actual_parse_id,
                ["Chunker produced 0 chunks"],
                existing_state,
                target_gen,
            )

        # 7. Compute next doc_seq (monotonic per expression)
        doc_seq = (existing_state.doc_seq + 1) if existing_state else 1

        # 8. Build headers, lexemes, and embedding inputs
        prepared_chunks: list[dict[str, Any]] = []
        embedding_texts: list[str] = []

        for ch in raw_chunks:
            # Header
            header = build_context_header(
                court_name=court_id,
                bench_strength=None,
                decision_date=str(decision_date) if decision_date else None,
                title=title,
                first_anchor=ch.anchor_first,
                last_anchor=ch.anchor_last,
                section_heading=ch.section_heading,
            )
            # Lexemes
            full_chunk_text = f"{header} {ch.text}"
            lexemes = extract_legal_lexemes(full_chunk_text)

            embed_input = f"{header}\n{ch.text}"
            embedding_texts.append(embed_input)

            text_hash = hashlib.sha256(ch.text.encode("utf-8")).hexdigest()
            prepared_chunks.append(
                {
                    "raw": ch,
                    "header": header,
                    "lexemes": lexemes,
                    "text_hash": text_hash,
                }
            )

        # 9. Dense embeddings via Model Gateway
        embed_result = embed(
            task_id="p2.embed.v1",
            texts=embedding_texts,
            model_id=EMBED_MODEL,
            dims=EMBED_DIMS,
            ctx=None,
            input_type="document",
        )
        embeddings = embed_result.embeddings

        # 10. Compute content_digest (XOR fold of sha256(chunk_id|text_hash|doc_seq))
        chunk_hashes: list[bytes] = []
        for p_chunk in prepared_chunks:
            ch_raw = p_chunk["raw"]
            thash = p_chunk["text_hash"]
            ch_bytes = hashlib.sha256(f"{ch_raw.chunk_id}|{thash}|{doc_seq}".encode()).digest()
            chunk_hashes.append(ch_bytes)

        xor_digest = functools.reduce(
            lambda a, b: bytes(x ^ y for x, y in zip(a, b, strict=True)), chunk_hashes, b"\x00" * 32
        )

        # 11. Atomic write to DB partition and event outbox
        table_name = f"chunk_{target_gen}"
        now = timezone.now()

        with transaction.atomic():
            with connection.cursor() as cur:
                # Find old chunk IDs being removed
                cur.execute(
                    f"SELECT chunk_id FROM plc.{table_name} WHERE work_id = %s AND expression_key = %s;",
                    [work_id, expression_key],
                )
                removed_chunk_ids = [r[0] for r in cur.fetchall()]

                # Delete previous chunks
                cur.execute(
                    f"DELETE FROM plc.{table_name} WHERE work_id = %s AND expression_key = %s;",
                    [work_id, expression_key],
                )

                # Insert new chunks
                insert_sql = f"""
                INSERT INTO plc.{table_name} (
                    chunk_id, index_generation, work_id, expression_key,
                    anchor_ids, anchor_first, anchor_last, chunk_kind,
                    rhetorical_role, opinion_role, context_header, text, text_hash,
                    court_id, court_level, bench_strength, decision_date, doc_type,
                    binding_scope_tags, cited_work_ids, cited_provision_anchors,
                    valid_from, valid_to, in_force, trust_label, rights_class,
                    quality, body, tsv, embedding, doc_seq, pipeline_version
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s,
                    (
                        setweight(to_tsvector('public.legal_en', %s), 'A') ||
                        setweight(to_tsvector('public.legal_en', %s), 'B') ||
                        setweight(array_to_tsvector(%s::text[]), 'C')
                    ),
                    %s::halfvec(1024), %s, %s
                );
                """

                for p_chunk, emb in zip(prepared_chunks, embeddings, strict=True):
                    c = p_chunk["raw"]
                    vec_str = "[" + ",".join(str(x) for x in emb) + "]"
                    body_json = json.dumps(c.body_extra)
                    quality_json = json.dumps({"token_count": c.token_count})

                    cur.execute(
                        insert_sql,
                        [
                            c.chunk_id,
                            target_gen,
                            work_id,
                            expression_key,
                            c.anchor_ids,
                            c.anchor_first,
                            c.anchor_last,
                            c.chunk_kind,
                            c.rhetorical_role,
                            None,  # opinion_role
                            p_chunk["header"],
                            c.text,
                            p_chunk["text_hash"],
                            court_id,
                            None,  # court_level
                            None,  # bench_strength
                            decision_date,
                            doc_type or "JUDGMENT",
                            binding_scope_tags,
                            [],  # cited_work_ids
                            [],  # cited_provision_anchors
                            None,  # valid_from
                            None,  # valid_to
                            None,  # in_force
                            "PLC_OFFICIAL",
                            "OFFICIAL",  # rights_class
                            quality_json,
                            body_json,
                            p_chunk["header"],
                            c.text,
                            p_chunk["lexemes"],
                            vec_str,
                            doc_seq,
                            PIPELINE_VERSION_P2,
                        ],
                    )

                # 12. Upsert plc.index_expression_state
                cur.execute(
                    """
                    INSERT INTO plc.index_expression_state (
                        serial_key, accepted_parse_id, doc_seq, content_digest,
                        enrichment_level, status, last_quarantined_parse_id, quarantine_reasons,
                        pipeline_version, updated_at
                    ) VALUES (
                        %s, %s, %s, %s,
                        'BASE', 'ACTIVE', NULL, NULL,
                        %s, now()
                    )
                    ON CONFLICT (serial_key) DO UPDATE SET
                        accepted_parse_id = EXCLUDED.accepted_parse_id,
                        doc_seq = EXCLUDED.doc_seq,
                        content_digest = EXCLUDED.content_digest,
                        enrichment_level = EXCLUDED.enrichment_level,
                        status = 'ACTIVE',
                        last_quarantined_parse_id = NULL,
                        quarantine_reasons = NULL,
                        pipeline_version = EXCLUDED.pipeline_version,
                        updated_at = now();
                    """,
                    [
                        serial_key,
                        actual_parse_id,
                        doc_seq,
                        xor_digest,
                        PIPELINE_VERSION_P2,
                    ],
                )

                # 13. Emit plc.doc.indexed.v1 event into ops.event_outbox
                new_chunk_ids = [p["raw"].chunk_id for p in prepared_chunks]
                event_id = mint_id("evc")
                idempotency_key = f"p2|index|{serial_key}|sha256:{xor_digest.hex()}|{target_gen}:doc_seq={doc_seq}:BASE"

                EventOutbox.objects.create(
                    id=event_id,
                    source="p2/indexer@0.1.0|det_v1",
                    type="doc.indexed.v1",
                    time=now,
                    subject=f"{work_id}/{expression_key}",
                    datacontenttype="application/json",
                    dataschema="https://lawyerbrain.in/schemas/doc.indexed.v1.json",
                    tenantid=None,
                    dataclass="PUBLIC",
                    idempotencykey=idempotency_key,
                    schemaversion="1.1",
                    data={
                        "expression_ref": {"work_id": work_id, "expression_key": expression_key},
                        "index_generation": target_gen,
                        "chunk_ids": new_chunk_ids,
                        "removed_chunk_ids": removed_chunk_ids,
                        "targets": ["lexical", "dense"],
                        "enrichment_level": "BASE",
                        "summary_ids": [],
                        "doc_seq": doc_seq,
                        "parse_id": actual_parse_id,
                        "content_digest": f"sha256:{xor_digest.hex()}",
                    },
                    topic="plc.doc.indexed.v1",
                    partition_key=work_id,
                    lane="rt",
                )

        return IndexResult(
            work_id=work_id,
            expression_key=expression_key,
            generation=target_gen,
            chunk_count=len(prepared_chunks),
            doc_seq=doc_seq,
        )

    def _handle_quarantine(
        self,
        serial_key: str,
        work_id: str,
        expression_key: str,
        parse_id: str,
        reasons: list[str],
        existing_state: IndexExpressionState | None,
        target_gen: str,
    ) -> IndexResult:
        """Handle quarantine according to Directive #6.

        - If previously indexed successfully: keep previous live chunk set intact, leave
          accepted_parse_id and doc_seq as they were. Record last_quarantined_parse_id and quarantine_reasons.
        - If never indexed: status = QUARANTINED, no chunks.
        """
        with connection.cursor() as cur:
            if existing_state and existing_state.status == "ACTIVE":
                cur.execute(
                    """
                    UPDATE plc.index_expression_state
                    SET last_quarantined_parse_id = %s,
                        quarantine_reasons = %s::jsonb,
                        updated_at = now()
                    WHERE serial_key = %s;
                    """,
                    [parse_id, json.dumps(reasons), serial_key],
                )
            else:
                cur.execute(
                    """
                    INSERT INTO plc.index_expression_state (
                        serial_key, accepted_parse_id, doc_seq, content_digest,
                        enrichment_level, status, last_quarantined_parse_id, quarantine_reasons,
                        pipeline_version, updated_at
                    ) VALUES (
                        %s, NULL, 0, NULL,
                        'NONE', 'QUARANTINED', %s, %s::jsonb,
                        %s, now()
                    )
                    ON CONFLICT (serial_key) DO UPDATE SET
                        status = 'QUARANTINED',
                        last_quarantined_parse_id = EXCLUDED.last_quarantined_parse_id,
                        quarantine_reasons = EXCLUDED.quarantine_reasons,
                        updated_at = now();
                    """,
                    [
                        serial_key,
                        parse_id,
                        json.dumps(reasons),
                        PIPELINE_VERSION_P2,
                    ],
                )

        return IndexResult(
            work_id=work_id,
            expression_key=expression_key,
            generation=target_gen,
            quarantined=True,
            quarantine_reasons=reasons,
        )

    def handle_identity_merged(self, from_id: str, to_id: str, reason: str = "MERGE") -> list[str]:
        """Handle identity.merged.v1: delete chunks of from_id, mark REKEYED, ensure to_id indexed (Directive #4 & #5)."""
        now = timezone.now()

        with transaction.atomic():
            with connection.cursor() as cur:
                # 1. Fetch chunks being removed
                cur.execute("SELECT chunk_id FROM plc.chunk WHERE work_id = %s;", [from_id])
                removed_ids = [r[0] for r in cur.fetchall()]

                # 2. Delete all chunks of from_id across all partitions
                cur.execute("DELETE FROM plc.chunk WHERE work_id = %s;", [from_id])

                # 3. Set from_id state to REKEYED (Directive #4)
                cur.execute(
                    """
                    UPDATE plc.index_expression_state
                    SET status = 'REKEYED', updated_at = now()
                    WHERE serial_key LIKE %s;
                    """,
                    [f"{from_id}/%"],
                )

                # 4. Emit doc.indexed.v1 for from_id indicating removal
                event_id = mint_id("evc")
                EventOutbox.objects.create(
                    id=event_id,
                    source="p2/indexer@0.1.0|det_v1",
                    type="doc.indexed.v1",
                    time=now,
                    subject=f"{from_id}/en",
                    datacontenttype="application/json",
                    dataschema="https://lawyerbrain.in/schemas/doc.indexed.v1.json",
                    tenantid=None,
                    dataclass="PUBLIC",
                    idempotencykey=f"p2|merge|{from_id}|{int(now.timestamp())}",
                    schemaversion="1.1",
                    data={
                        "expression_ref": {"work_id": from_id, "expression_key": "en"},
                        "index_generation": self.generation,
                        "chunk_ids": [],
                        "removed_chunk_ids": removed_ids,
                        "targets": ["lexical", "dense"],
                        "enrichment_level": "NONE",
                        "summary_ids": [],
                        "doc_seq": 0,
                        "parse_id": "REKEYED",
                        "content_digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
                    },
                    topic="plc.doc.indexed.v1",
                    partition_key=from_id,
                    lane="rt",
                )

        # 5. Make sure canonical to_id is indexed (forced path per Directive #5)
        self.index_expression(work_id=to_id, expression_key="en", force=True)

        return removed_ids
