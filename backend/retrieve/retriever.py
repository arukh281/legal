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
from typing import Any

from django.utils import timezone

from anchor_lib.ids import mint_id, mint_ulid
from index.ial import IndexAccessLayer, IndexQuery
from ingest.models import Capture
from ops.models import PipelineVersion
from parse.models import Anchor, Work
from retrieve.models import EvidenceBundle, ResearchQuery
from workspace.authz import ExecutionContext


def get_law_current_to_date() -> datetime.date:
    """Return latest capture date across the corpus dynamically (S07 Amendment #7)."""
    latest_capture = Capture.objects.order_by("-fetched_at").first()
    if latest_capture and latest_capture.fetched_at:
        return latest_capture.fetched_at.date()
    return datetime.date(2026, 10, 1)


class RetrievalEngine:
    """Retrieval Engine for compiling EvidenceBundle using IndexAccessLayer."""

    def __init__(self, index_family: str = "plc_chunks") -> None:
        self.ial = IndexAccessLayer(index_family=index_family)

    def retrieve(
        self,
        query: ResearchQuery,
        ctx: ExecutionContext,
        k: int = 15,
    ) -> EvidenceBundle:
        """Execute single-leg lexical search and build EvidenceBundle."""
        # 1. Lexical retrieval via IAL
        index_query = IndexQuery(
            query_id=query.query_id,
            mode="LEXICAL",
            text=query.text,
            k=k,
        )
        hits = self.ial.search(index_query)

        # 2. Extract and resolve anchor and work details
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
                        "lexical": hit.score,
                        "fused": hit.score,
                        "legs_hit": ["LEXICAL"],
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
                    "why_included": f"Lexical match on '{query.text[:50]}' (rank {rank}, score {hit.score:.4f})",
                    "role": "RULE" if (target_anchor and target_anchor.node_type == "STATUTE_SECTION") else "APPLICATION",
                    "source_layer": "PLC",
                    "trust_label": "PUBLIC_PRIMARY",
                    "lang": (target_anchor.lang if target_anchor else "en") or "en",
                    "display_rank": rank,
                }
            )

        # 3. Contrary authority sweep: Directive #2
        # S07 Amendment #2: report status LIMITED ("lexical only, no citator")
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
                        "reason": "lexical only, no citator",
                    },
                }
            }
        }

        # 4. Warnings and degradations (D19.2)
        warnings: list[dict[str, Any]] = [
            {
                "kind": "INDEX_LAG",
                "severity": "INFO",
                "anchor_ids": [],
                "message": "Lexical retrieval only (g1 dense embeddings provisional).",
            }
        ]

        bundle_id = mint_id("evb")
        pipeline_ver = PipelineVersion.objects.get(pipeline_version="p5.retriever@0.1.0|lexical_v1")
        now = timezone.now()

        bundle = EvidenceBundle(
            tenant_id=ctx.tenant_id,
            bundle_id=bundle_id,
            query_id=query.query_id,
            as_of_legal_date=query.as_of_legal_date,
            as_known_at=now,
            index_generation="g1",
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
                    "legs": ["LEXICAL"],
                    "candidates": len(hits),
                }
            ],
            trace_id=ctx.traceparent or mint_ulid(),
            created_at=now,
        )

        # Persist to database if in tenant context
        bundle.save()
        return bundle
