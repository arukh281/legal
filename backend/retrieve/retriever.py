"""Phase P5 Retrieval Engine — compiles a legally coherent EvidenceBundle.

Normative sources:
- docs/mvp/00_mvp_spec.md §4.1
- docs/mvp/03_data_model_and_contracts.md §3.11 (tpl.research_query, tpl.evidence_bundle)
- docs/01_master_architecture.md §7.8, §7.9
- docs/07_P5_retrieval_fusion.md §2.1, §2.2
- DECISIONS.md (2026-10-10 S07 Directives):
  - Lexical retrieval only for now (g1 fake embeddings).
  - Contrary sweep: status LIMITED ("lexical only, no citator").
  - Dynamic law_current_to from latest capture date in corpus.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from django.utils import timezone

from anchor_lib.ids import mint_id, mint_ulid
from index.ial import IndexAccessLayer, IndexHit, IndexQuery
from ingest.models import Capture
from ops.models import PipelineVersion
from parse.models import Anchor, Work
from retrieve.models import EvidenceBundle, ResearchQuery
from workspace.authz import ExecutionContext

logger = logging.getLogger(__name__)


def get_law_current_to_date() -> datetime.date:
    """Return latest capture date across the corpus dynamically (S07 Amendment #7)."""
    latest_capture = Capture.objects.order_by("-fetched_at").first()
    if latest_capture and latest_capture.fetched_at:
        return latest_capture.fetched_at.date()
    return datetime.date(2026, 10, 1)


class RetrievalEngine:
    """Retrieval Engine for compiling EvidenceBundle using IndexAccessLayer."""

    def __init__(self, index_family: str = "plc_chunks") -> None:
        self.index_family = index_family
        self.ial = IndexAccessLayer(index_family=index_family)

    def retrieve(
        self,
        query: ResearchQuery,
        ctx: ExecutionContext,
        k: int = 15,
        generation: str | None = None,
        hybrid: bool = True,
    ) -> EvidenceBundle:
        """Execute hybrid search (lexical + dense with RRF) and build EvidenceBundle."""
        target_gen = generation or self.ial._resolve_generation(generation)

        # 1. Candidate Generation
        # Leg 1: Lexical
        lex_query = IndexQuery(
            query_id=query.query_id,
            mode="LEXICAL",
            text=query.text,
            k=k * 2,
            generation=target_gen,
        )
        lex_hits = self.ial.search(lex_query)

        # Leg 2: Dense (if hybrid is enabled)
        dense_hits: list[IndexHit] = []
        if hybrid:
            try:
                dense_query = IndexQuery(
                    query_id=query.query_id,
                    mode="DENSE",
                    text=query.text,
                    k=k * 2,
                    generation=target_gen,
                )
                dense_hits = self.ial.search(dense_query)
            except Exception as exc:
                logger.warning(
                    "Dense retrieval leg failed for generation %s (falling back to lexical): %s",
                    target_gen,
                    exc,
                )
                dense_hits = []

        # 2. Reciprocal Rank Fusion (RRF k=60 per Cormack et al. 2009; docs/07 §5.7)
        has_dense = len(dense_hits) > 0
        rrf_scores: dict[str, float] = {}
        legs_hit_map: dict[str, list[str]] = {}
        hit_by_id: dict[str, IndexHit] = {}

        if has_dense:
            for rank, hit in enumerate(lex_hits, start=1):
                rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + (1.0 / (60.0 + rank))
                if "LEXICAL" not in legs_hit_map.get(hit.chunk_id, []):
                    legs_hit_map.setdefault(hit.chunk_id, []).append("LEXICAL")
                hit_by_id[hit.chunk_id] = hit

            for rank, hit in enumerate(dense_hits, start=1):
                rrf_scores[hit.chunk_id] = rrf_scores.get(hit.chunk_id, 0.0) + (1.0 / (60.0 + rank))
                if "DENSE" not in legs_hit_map.get(hit.chunk_id, []):
                    legs_hit_map.setdefault(hit.chunk_id, []).append("DENSE")
                if hit.chunk_id not in hit_by_id:
                    hit_by_id[hit.chunk_id] = hit

            fused_cids = sorted(
                rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True
            )[:k]
            hits = [hit_by_id[cid] for cid in fused_cids]
        else:
            rrf_scores = {h.chunk_id: h.score for h in lex_hits}
            legs_hit_map = {h.chunk_id: ["LEXICAL"] for h in lex_hits}
            hits = lex_hits[:k]

        # 3. Extract and resolve anchor and work details
        items: list[dict[str, Any]] = []
        anchor_ids_to_fetch: list[str] = []
        for hit in hits:
            anchor_ids_to_fetch.extend(hit.anchor_ids)

        # Bulk fetch anchors preserving LIVE state
        anchors_by_id: dict[str, Anchor] = {
            a.anchor_id: a
            for a in Anchor.objects.filter(anchor_id__in=anchor_ids_to_fetch, state="LIVE")
        }

        # Bulk fetch works
        work_ids = list({h.work_id for h in hits if h.work_id})
        works_by_id: dict[str, Work] = {
            w.work_id: w for w in Work.objects.filter(work_id__in=work_ids)
        }

        for rank, hit in enumerate(hits, start=1):
            target_anchor = None
            for a_id in hit.anchor_ids:
                if a_id in anchors_by_id:
                    target_anchor = anchors_by_id[a_id]
                    break

            if target_anchor is not None:
                anchor_id = target_anchor.anchor_id
                excerpt = target_anchor.text
                rhetorical_role = target_anchor.node_type or "PARA"
            elif hit.anchor_ids:
                anchor_id = hit.anchor_ids[0]
                excerpt = hit.text
                rhetorical_role = "PARA"
            else:
                continue

            work = works_by_id.get(hit.work_id)
            court_id = hit.court_id or (work.court_id if work else None)
            decision_date_str = (
                hit.decision_date.isoformat()
                if hit.decision_date
                else (work.decision_date.isoformat() if work and work.decision_date else None)
            )

            item_id = f"item_{rank:03d}_{mint_ulid()[:8]}"
            hit_score = rrf_scores.get(hit.chunk_id, hit.score)
            legs = legs_hit_map.get(hit.chunk_id, ["LEXICAL"])

            items.append(
                {
                    "item_id": item_id,
                    "anchor_ids": [anchor_id],
                    "work_id": hit.work_id,
                    "excerpt": excerpt,
                    "context": {
                        "header": hit.context_header,
                        "court_id": court_id,
                        "decision_date": decision_date_str,
                        "doc_type": hit.doc_type,
                        "rhetorical_role": rhetorical_role,
                    },
                    "retrieval_signals": {
                        "lexical": hit.score if "LEXICAL" in legs else 0.0,
                        "fused": hit_score,
                        "legs_hit": legs,
                    },
                    "authority": {
                        "court_id": court_id,
                        "decision_date": decision_date_str,
                        "ocr_conf": (target_anchor.ocr_conf if target_anchor else 1.0) or 1.0,
                    },
                    "stance": {
                        "toward_client": "NEUTRAL",
                        "confidence": 1.0,
                    },
                    "why_included": f"{'+'.join(legs)} match on '{query.text[:50]}' (rank {rank}, score {hit_score:.4f})",
                    "role": (
                        "RULE"
                        if (target_anchor and target_anchor.node_type == "STATUTE_SECTION")
                        else "APPLICATION"
                    ),
                    "source_layer": "PLC",
                    "trust_label": "PUBLIC_PRIMARY",
                    "lang": (target_anchor.lang if target_anchor else "en") or "en",
                    "display_rank": rank,
                }
            )

        # 4. Contrary authority sweep: Directive #2
        contrary_reason = (
            "hybrid (lexical + dense RRF), no citator" if has_dense else "lexical only, no citator"
        )
        coverage: dict[str, Any] = {
            "per_issue": {
                "main": {
                    "binding_found": len(items),
                    "adverse_found": 0,
                    "gaps": [] if items else ["NO_RELEVANT_CHUNKS_IN_CORPUS"],
                    "sufficiency": "SUFFICIENT" if items else "NONE",
                    "adverse_search": {
                        "status": "LIMITED",
                        "contra_queries": [f"contrary to {query.text[:60]}"],
                        "binding_candidates_examined": len(items),
                        "graph_negative_checks": 0,
                        "attested": True,
                        "reason": contrary_reason,
                    },
                }
            }
        }

        # 5. Warnings and degradations (D19.2)
        warnings: list[dict[str, Any]] = []
        if not has_dense:
            warnings.append(
                {
                    "kind": "INDEX_LAG",
                    "severity": "INFO",
                    "anchor_ids": [],
                    "message": f"Lexical retrieval only ({target_gen} dense embeddings not active).",
                }
            )

        bundle_id = mint_id("evb")
        pipeline_ver_str = (
            "p5.retriever@0.1.0|hybrid_rrf_v1" if has_dense else "p5.retriever@0.1.0|lexical_v1"
        )
        pipeline_ver = PipelineVersion.objects.get(pipeline_version=pipeline_ver_str)
        now = timezone.now()

        bundle = EvidenceBundle(
            tenant_id=ctx.tenant_id,
            bundle_id=bundle_id,
            query_id=query.query_id,
            as_of_legal_date=query.as_of_legal_date,
            as_known_at=now,
            index_generation=target_gen,
            graph_watermark=0,
            pipeline_version=pipeline_ver,
            issues=[
                {
                    "issue_id": f"{query.query_id}/i1",
                    "text": query.text,
                    "issue_kind": "RESEARCH",
                    "as_of_legal_date": query.as_of_legal_date.isoformat(),
                    "sub_queries": [
                        {
                            "sq_id": f"{query.query_id}/sq1",
                            "slot": "PRO",
                            "text": query.text,
                            "as_of_legal_date": query.as_of_legal_date.isoformat(),
                        }
                    ],
                }
            ],
            items=items,
            coverage=coverage,
            warnings=warnings,
            searched=[
                {
                    "sq_id": f"{query.query_id}/sq1",
                    "legs": ["LEXICAL", "DENSE"] if has_dense else ["LEXICAL"],
                    "candidates": len(hits),
                }
            ],
            trace_id=ctx.traceparent or mint_ulid(),
            created_at=now,
        )

        # Persist to database if in tenant context
        bundle.save()
        return bundle
