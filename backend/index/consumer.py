"""Event consumer for indexing pipeline.

Consumes:
- doc.parsed.v1: triggers index_expression for new or updated parse
- identity.merged.v1: deletes chunks for from_id, sets status REKEYED, ensures to_id indexed
- identity.split.v1: re-indexes unmerged works with force=True
"""

from __future__ import annotations

import logging
from typing import Any

from index.indexer import IndexPipeline
from ops.outbox import register_handler

logger = logging.getLogger(__name__)


@register_handler("index_pipeline", "doc.parsed.v1")
@register_handler("index_pipeline", "plc.doc.parsed.v1")
def handle_doc_parsed(event: dict[str, Any]) -> dict[str, Any]:
    """Handle doc.parsed.v1 event by indexing the parsed expression."""
    data = event.get("data", {})
    work_id = data.get("work_id")
    expression_key = data.get("expression_key", "en")
    parse_id = data.get("parse_id")

    if not work_id:
        return {"status": "SKIPPED", "reason": "MISSING_WORK_ID"}

    pipeline = IndexPipeline()
    result = pipeline.index_expression(
        work_id=work_id,
        expression_key=expression_key,
        parse_id=parse_id,
        force=False,
    )

    return {
        "status": "SUCCESS" if not result.quarantined and not result.skipped else "PROCESSED",
        "work_id": work_id,
        "chunk_count": result.chunk_count,
        "doc_seq": result.doc_seq,
        "quarantined": result.quarantined,
        "skipped": result.skipped,
        "skip_reason": result.skip_reason,
    }


@register_handler("index_pipeline", "identity.merged.v1")
@register_handler("index_pipeline", "plc.identity.merged.v1")
def handle_identity_merged(event: dict[str, Any]) -> dict[str, Any]:
    """Handle identity.merged.v1: delete chunks of from_id, mark REKEYED, index to_id."""
    data = event.get("data", {})
    from_id = data.get("from_id") or data.get("from_work_id")
    to_id = data.get("to_id") or data.get("to_work_id")
    reason = data.get("reason", "MERGE")

    if not from_id or not to_id:
        return {"status": "ERROR", "reason": "MISSING_FROM_OR_TO_ID"}

    pipeline = IndexPipeline()
    removed_chunk_ids = pipeline.handle_identity_merged(from_id=from_id, to_id=to_id, reason=reason)

    return {
        "status": "SUCCESS",
        "from_id": from_id,
        "to_id": to_id,
        "removed_chunk_count": len(removed_chunk_ids),
    }


@register_handler("index_pipeline", "identity.split.v1")
@register_handler("index_pipeline", "plc.identity.split.v1")
def handle_identity_split(event: dict[str, Any]) -> dict[str, Any]:
    """Handle identity.split.v1: re-index unmerged works with force=True."""
    data = event.get("data", {})
    split_works = data.get("split_works") or data.get("work_ids") or []

    pipeline = IndexPipeline()
    results = []
    for wid in split_works:
        res = pipeline.index_expression(work_id=wid, expression_key="en", force=True)
        results.append(
            {
                "work_id": wid,
                "chunk_count": res.chunk_count,
                "quarantined": res.quarantined,
            }
        )

    return {"status": "SUCCESS", "results": results}


def handle_event(event: dict[str, Any]) -> dict[str, Any]:
    """Generic dispatcher entrypoint matching ops.event_subscription."""
    event_type = event.get("type", "")
    if event_type in ("doc.parsed.v1", "plc.doc.parsed.v1"):
        return handle_doc_parsed(event)
    elif event_type in ("identity.merged.v1", "plc.identity.merged.v1"):
        return handle_identity_merged(event)
    elif event_type in ("identity.split.v1", "plc.identity.split.v1"):
        return handle_identity_split(event)
    return {"status": "SKIPPED", "reason": f"unhandled_event_type_{event_type}"}
