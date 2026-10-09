"""Index Access Layer (IAL) — sync query interface for P2 chunk retrieval.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5
- docs/04_P2_enrichment_indexing.md §2.5, §5.11a
- Directives 1 & 7 approved by aru:
  #1: Quoted tsquery terms for lexemes combined with websearch_to_tsquery for remaining text
  #7: GenerationGone typed exception carrying anchor_ids on retired generation
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

from django.db import connection

from gateway.runner import embed
from index.generations import get_active_generation
from index.models import IndexGeneration
from index.normalizer import extract_query_lexemes


class UnsupportedFilterError(Exception):
    """Raised when an unrecognized filter is passed to IndexQuery."""


class GenerationGone(Exception):
    """Raised when get_chunks is called on a retired or rolled back generation (Directive #7)."""

    def __init__(self, generation: str, anchor_ids: list[str]) -> None:
        super().__init__(f"Generation '{generation}' is retired or gone.")
        self.generation = generation
        self.anchor_ids = anchor_ids


SUPPORTED_FILTERS: frozenset[str] = frozenset(
    {
        "court_ids",
        "court_levels",
        "doc_types",
        "decided_on_or_before",
        "decided_on_or_after",
        "binding_scope_tags_any",
        "work_ids",
        "rights_classes",
        "trust_labels",
        "min_quality_gate",
    }
)


@dataclass(slots=True)
class IndexQuery:
    """Query object specifying retrieval view, mode, text, vector, and filters."""

    query_id: str = "q_default"
    tenant_scope: dict[str, Any] = field(default_factory=lambda: {"plc": True})
    view: str = "CHUNK"
    mode: str = "LEXICAL"  # LEXICAL or DENSE
    text: str | None = None
    vector: list[float] | None = None
    query_instruction_id: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    k: int = 20
    generation: str | None = None


@dataclass(frozen=True, slots=True)
class IndexHit:
    """A single chunk match returned by the Index Access Layer."""

    chunk_id: str
    work_id: str
    expression_key: str
    anchor_ids: list[str]
    anchor_first: str
    anchor_last: str
    chunk_kind: str
    context_header: str
    text: str
    score: float
    court_id: str | None
    decision_date: datetime.date | None
    doc_type: str
    binding_scope_tags: list[str]
    body: dict[str, Any]


class IndexAccessLayer:
    """Index Access Layer providing single-leg (lexical or dense) search across chunk partitions."""

    def __init__(self, index_family: str = "plc_chunks") -> None:
        self.index_family = index_family

    def _resolve_generation(self, generation: str | None) -> str:
        if generation and generation != "current":
            return generation
        return get_active_generation(self.index_family)

    def embed_query(
        self,
        text: str,
        instruction_id: str | None = None,
        ctx: Any = None,
    ) -> list[float]:
        """Embed a search query via Model Gateway."""
        res = embed(
            task_id="p2.embed.v1",
            texts=[text],
            model_id="voyage-4-large",
            dims=1024,
            ctx=ctx,
            input_type="query",
        )
        return res.embeddings[0]

    def _build_where_clause(
        self, filters: dict[str, Any]
    ) -> tuple[list[str], list[Any]]:
        """Compile filters into SQL WHERE clauses and parameters."""
        clauses: list[str] = []
        params: list[Any] = []

        for key, val in filters.items():
            if key not in SUPPORTED_FILTERS:
                raise UnsupportedFilterError(f"Filter '{key}' is not supported by IAL.")

            if key == "court_ids" and val:
                clauses.append("court_id = ANY(%s)")
                params.append(list(val))
            elif key == "court_levels" and val:
                clauses.append("court_level = ANY(%s)")
                params.append(list(val))
            elif key == "doc_types" and val:
                clauses.append("doc_type = ANY(%s)")
                params.append(list(val))
            elif key == "decided_on_or_before" and val:
                clauses.append("decision_date <= %s")
                params.append(val)
            elif key == "decided_on_or_after" and val:
                clauses.append("decision_date >= %s")
                params.append(val)
            elif key == "binding_scope_tags_any" and val:
                clauses.append("binding_scope_tags && %s::text[]")
                params.append(list(val))
            elif key == "work_ids" and val:
                clauses.append("work_id = ANY(%s)")
                params.append(list(val))
            elif key == "rights_classes" and val:
                clauses.append("rights_class = ANY(%s)")
                params.append(list(val))
            elif key == "trust_labels" and val:
                clauses.append("trust_label = ANY(%s)")
                params.append(list(val))
            # min_quality_gate is enforced by default excluding quarantined expressions

        return clauses, params

    def search(self, query: IndexQuery) -> list[IndexHit]:
        """Execute search against the active or requested index generation partition."""
        gen = self._resolve_generation(query.generation)
        table_name = f"chunk_{gen}"
        k = min(max(1, query.k), 1000)

        where_clauses, params = self._build_where_clause(query.filters)

        if query.mode == "LEXICAL":
            return self._search_lexical(query, table_name, where_clauses, params, k)
        elif query.mode == "DENSE":
            return self._search_dense(query, table_name, where_clauses, params, k)
        else:
            raise ValueError(
                f"Invalid search mode '{query.mode}'. Must be 'LEXICAL' or 'DENSE'. Fusion belongs to P5 (S07)."
            )

    def _search_lexical(
        self,
        query: IndexQuery,
        table_name: str,
        where_clauses: list[str],
        params: list[Any],
        k: int,
    ) -> list[IndexHit]:
        """Lexical search combining quoted lexemes with websearch on remaining prose (Directive #1)."""
        if not query.text or not query.text.strip():
            return []

        lexemes, remaining_text = extract_query_lexemes(query.text)

        # Build tsquery expression
        tsquery_parts: list[str] = []
        sql_params: list[Any] = []

        if lexemes:
            # Combine lexemes with || (OR) so searching for s138 matches chunks having s138 or ancestors
            # Each lexeme is quoted and cast to tsquery: '''s138'''::tsquery
            lex_expr = " || ".join(f"'''{lex}'''::tsquery" for lex in lexemes)
            tsquery_parts.append(f"({lex_expr})")

        if remaining_text:
            tsquery_parts.append("websearch_to_tsquery('public.legal_en', %s)")
            sql_params.append(remaining_text)

        if not tsquery_parts:
            # Fallback if text was somehow stripped
            tsquery_sql = "websearch_to_tsquery('public.legal_en', %s)"
            sql_params.append(query.text)
        elif len(tsquery_parts) == 1:
            tsquery_sql = tsquery_parts[0]
        else:
            # AND combination: legal lexeme AND remaining query terms
            tsquery_sql = f"({tsquery_parts[0]} && {tsquery_parts[1]})"

        combined_where = list(where_clauses)
        combined_where.append(f"tsv @@ {tsquery_sql}")

        where_str = " AND ".join(combined_where)
        all_params = (sql_params * 2) + list(params) + sql_params + [k]

        sql = f"""
        SELECT chunk_id, work_id, expression_key, anchor_ids, anchor_first, anchor_last,
               chunk_kind, context_header, text,
               GREATEST(ts_rank_cd(tsv, {tsquery_sql}), ts_rank(tsv, {tsquery_sql})) AS score,
               court_id, decision_date, doc_type, binding_scope_tags, body
        FROM plc.{table_name}
        WHERE {where_str}
        ORDER BY score DESC
        LIMIT %s;
        """

        with connection.cursor() as cur:
            cur.execute(sql, all_params)
            rows = cur.fetchall()

        return [
            IndexHit(
                chunk_id=r[0],
                work_id=r[1],
                expression_key=r[2],
                anchor_ids=list(r[3]),
                anchor_first=r[4],
                anchor_last=r[5],
                chunk_kind=r[6],
                context_header=r[7],
                text=r[8],
                score=float(r[9]),
                court_id=r[10],
                decision_date=r[11],
                doc_type=r[12],
                binding_scope_tags=list(r[13]) if r[13] else [],
                body=r[14] if isinstance(r[14], dict) else {},
            )
            for r in rows
        ]

    def _search_dense(
        self,
        query: IndexQuery,
        table_name: str,
        where_clauses: list[str],
        params: list[Any],
        k: int,
    ) -> list[IndexHit]:
        """Dense vector search using HNSW halfvec cosine distance."""
        vec = query.vector
        if vec is None:
            if not query.text:
                return []
            vec = self.embed_query(query.text, query.query_instruction_id)

        vec_str = "[" + ",".join(str(x) for x in vec) + "]"

        combined_where = list(where_clauses)
        where_str = f"WHERE {' AND '.join(combined_where)}" if combined_where else ""

        with connection.cursor() as cur:
            cur.execute("SET LOCAL hnsw.ef_search = 100;")
            cur.execute(
                f"""
                SELECT chunk_id, work_id, expression_key, anchor_ids, anchor_first, anchor_last,
                       chunk_kind, context_header, text,
                       (1.0 - ((embedding::halfvec(1024)) <=> %s::halfvec(1024))) AS score,
                       court_id, decision_date, doc_type, binding_scope_tags, body
                FROM plc.{table_name}
                {where_str}
                ORDER BY (embedding::halfvec(1024)) <=> %s::halfvec(1024)
                LIMIT %s;
                """,
                [vec_str] + list(params) + [vec_str, k],
            )
            rows = cur.fetchall()

        return [
            IndexHit(
                chunk_id=r[0],
                work_id=r[1],
                expression_key=r[2],
                anchor_ids=list(r[3]),
                anchor_first=r[4],
                anchor_last=r[5],
                chunk_kind=r[6],
                context_header=r[7],
                text=r[8],
                score=float(r[9]),
                court_id=r[10],
                decision_date=r[11],
                doc_type=r[12],
                binding_scope_tags=list(r[13]) if r[13] else [],
                body=r[14] if isinstance(r[14], dict) else {},
            )
            for r in rows
        ]

    def get_chunks(self, ids: list[str], generation: str = "current") -> list[IndexHit]:
        """Fetch chunks by IDs, raising GenerationGone if generation is retired or rolled back (Directive #7)."""
        gen = self._resolve_generation(generation)

        # Check generation state
        gen_record = IndexGeneration.objects.filter(
            index_family=self.index_family, generation=gen
        ).first()
        if gen_record and gen_record.state in ("RETIRED", "ROLLED_BACK"):
            anchors: list[str] = []
            try:
                with connection.cursor() as cur:
                    cur.execute(
                        f"SELECT unnest(anchor_ids) FROM plc.chunk_{gen} WHERE chunk_id = ANY(%s);",
                        [ids],
                    )
                    anchors = [r[0] for r in cur.fetchall()]
            except Exception:
                pass
            raise GenerationGone(generation=gen, anchor_ids=anchors)

        table_name = f"chunk_{gen}"
        if not ids:
            return []

        sql = f"""
        SELECT chunk_id, work_id, expression_key, anchor_ids, anchor_first, anchor_last,
               chunk_kind, context_header, text, 1.0 AS score,
               court_id, decision_date, doc_type, binding_scope_tags, body
        FROM plc.{table_name}
        WHERE chunk_id = ANY(%s);
        """

        with connection.cursor() as cur:
            cur.execute(sql, [ids])
            rows = cur.fetchall()

        return [
            IndexHit(
                chunk_id=r[0],
                work_id=r[1],
                expression_key=r[2],
                anchor_ids=list(r[3]),
                anchor_first=r[4],
                anchor_last=r[5],
                chunk_kind=r[6],
                context_header=r[7],
                text=r[8],
                score=1.0,
                court_id=r[10],
                decision_date=r[11],
                doc_type=r[12],
                binding_scope_tags=list(r[13]) if r[13] else [],
                body=r[14] if isinstance(r[14], dict) else {},
            )
            for r in rows
        ]

    def get_neighbours(
        self, anchor_id: str, before: int = 1, after: int = 1, generation: str = "current"
    ) -> list[IndexHit]:
        """Fetch contiguous neighbouring chunks around the chunk containing anchor_id."""
        gen = self._resolve_generation(generation)
        table_name = f"chunk_{gen}"

        with connection.cursor() as cur:
            # Find the target chunk
            cur.execute(
                f"""
                SELECT chunk_id, work_id, expression_key, doc_seq
                FROM plc.{table_name}
                WHERE %s = ANY(anchor_ids)
                LIMIT 1;
                """,
                [anchor_id],
            )
            target = cur.fetchone()
            if not target:
                return []

            cid, work_id, expr_key, dseq = target

            # Fetch before, target, after
            cur.execute(
                f"""
                SELECT chunk_id, work_id, expression_key, anchor_ids, anchor_first, anchor_last,
                       chunk_kind, context_header, text, 1.0 AS score,
                       court_id, decision_date, doc_type, binding_scope_tags, body
                FROM plc.{table_name}
                WHERE work_id = %s AND expression_key = %s
                ORDER BY chunk_id
                """,
                [work_id, expr_key],
            )
            all_chunks = cur.fetchall()

        # Find target index
        idx = -1
        for i, row in enumerate(all_chunks):
            if row[0] == cid:
                idx = i
                break

        if idx == -1:
            return []

        start = max(0, idx - before)
        end = min(len(all_chunks), idx + after + 1)
        selected = all_chunks[start:end]

        return [
            IndexHit(
                chunk_id=r[0],
                work_id=r[1],
                expression_key=r[2],
                anchor_ids=list(r[3]),
                anchor_first=r[4],
                anchor_last=r[5],
                chunk_kind=r[6],
                context_header=r[7],
                text=r[8],
                score=1.0,
                court_id=r[10],
                decision_date=r[11],
                doc_type=r[12],
                binding_scope_tags=list(r[13]) if r[13] else [],
                body=r[14] if isinstance(r[14], dict) else {},
            )
            for r in selected
        ]
