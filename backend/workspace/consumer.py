"""Tenant-side court event consumers for cause-lists and orders.

Normative sources:
- Session R2: hearings, dates and Today (§2, §3, User Approval & Corrections)
- User Correction 1: Matching rule, parent case matching, bench mapping.
- User Correction 2: Stable keys on hearings and candidates across revisions.
- User Correction 3: Dropped from revised list creates HEARING_DROPPED candidate.
- User Correction 5: Loop tenant by tenant with tenant context and purpose logged.
- User Correction 7: Order cause title (text before paragraph 1) only, negative citation guard.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import structlog
from django.db import connection
from django.utils import timezone

from anchor_lib.case_numbers import (
    NormalizedCaseNumber,
    compare_case_numbers,
    normalize_bench,
    normalize_case_number,
)
from anchor_lib.ids import mint_id
from ops.outbox import register_handler
from parse.storage import ParsedDocStorage
from workspace.db import tenant_db_context
from workspace.models import CaseCandidate, Hearing, MatterCaseLink, MatterDependency

logger = structlog.get_logger(__name__)


def get_active_tenant_ids(purpose: str = "CAUSELIST_SYNC") -> list[str]:
    """Retrieve all active tenant IDs using system purpose to discover tenants across RLS."""
    with connection.cursor() as cursor:
        cursor.execute("SET app.purpose = %s;", [purpose])
        cursor.execute("SELECT tenant_id FROM tpl.tenant WHERE deployment_mode IS NOT NULL")
        rows = cursor.fetchall()
        return [r[0] for r in rows]


@register_handler("workspace_sync", "court.causelist.published.v1")
def handle_causelist_published(event: dict[str, Any]) -> dict[str, Any]:
    """Consumer handler for court.causelist.published.v1.

    Processes NCLT cause lists and updates tenant hearings/candidates per Correction 1, 2, 3, 5.
    """
    data = event.get("data", {})
    raw_id = data.get("raw_id", "")
    bench = normalize_bench(data.get("bench"))
    court_no = str(data.get("court_no", "1"))
    list_date_str = data.get("list_date")
    if not list_date_str:
        return {"status": "ERROR", "reason": "MISSING_LIST_DATE"}
    list_date = date.fromisoformat(list_date_str)
    items_data = data.get("items", [])

    tenant_ids = get_active_tenant_ids(purpose="CAUSELIST_SYNC")
    total_exact_matches = 0
    total_partial_matches = 0
    total_dropped_created = 0

    # User Correction 5: Loop tenant by tenant with tenant context set and purpose logged
    for tenant_id in tenant_ids:
        with tenant_db_context(tenant_id=tenant_id, user_id="system:causelist", purpose="CAUSELIST_SYNC"):
            # Load tracked case links for this tenant
            tracked_links = list(
                MatterCaseLink.objects.filter(tenant_id=tenant_id, track=True)
            )
            if not tracked_links:
                continue

            # Parse tracked links into NormalizedCaseNumber
            tracked_parsed: list[tuple[MatterCaseLink, NormalizedCaseNumber]] = []
            for link in tracked_links:
                norm_c = normalize_case_number(link.value_normalized)
                if norm_c.parseable:
                    tracked_parsed.append((link, norm_c))

            matched_matter_ids: set[str] = set()

            # Iterate through cause list items
            for item in items_data:
                item_no = str(item.get("item_no", ""))
                purpose = item.get("purpose", "")
                parties = item.get("parties", "")
                raw_cases = item.get("normalized_cases", [])

                norm_cases: list[NormalizedCaseNumber] = []
                for c_dict in raw_cases:
                    norm_cases.append(
                        NormalizedCaseNumber(
                            raw=c_dict.get("raw", ""),
                            case_type=c_dict.get("case_type", ""),
                            case_number=c_dict.get("case_number", ""),
                            year=c_dict.get("year"),
                            bench=normalize_bench(c_dict.get("bench")) or bench,
                            canonical=c_dict.get("canonical", ""),
                            parseable=c_dict.get("parseable", True),
                            parent_case_type=c_dict.get("parent_case_type"),
                            parent_case_number=c_dict.get("parent_case_number"),
                            parent_year=c_dict.get("parent_year"),
                            parent_bench=normalize_bench(c_dict.get("parent_bench")),
                        )
                    )

                # Match against tracked cases in this tenant
                for item_norm in norm_cases:
                    for link, tracked_norm in tracked_parsed:
                        match_res = compare_case_numbers(item_norm, tracked_norm)

                        if match_res == "EXACT":
                            matched_matter_ids.add(link.matter_id)
                            # User Correction 2: Stable key (tenant_id, matter_id, date, bench, court_no)
                            existing_hearing = Hearing.objects.filter(
                                tenant_id=tenant_id,
                                matter_id=link.matter_id,
                                date=list_date,
                                bench=bench,
                                court_no=court_no,
                                source="CAUSE_LIST",
                            ).first()

                            now = timezone.now()
                            if existing_hearing:
                                # Update item_no in place across revisions
                                existing_hearing.item_no = item_no
                                existing_hearing.source_ref = f"{raw_id}:{item_no}"
                                existing_hearing.purpose = purpose or existing_hearing.purpose
                                existing_hearing.observed_at = now
                                existing_hearing.save(
                                    update_fields=["item_no", "source_ref", "purpose", "observed_at"]
                                )
                            else:
                                Hearing.objects.create(
                                    tenant_id=tenant_id,
                                    matter_id=link.matter_id,
                                    hearing_id=mint_id("hrg"),
                                    date=list_date,
                                    court_no=court_no,
                                    item_no=item_no,
                                    bench=bench,
                                    purpose=purpose,
                                    source="CAUSE_LIST",
                                    source_ref=f"{raw_id}:{item_no}",
                                    status="LISTED",
                                    entered_by="system:causelist",
                                    observed_at=now,
                                )
                            total_exact_matches += 1

                        elif match_res == "PARTIAL":
                            # User Correction 2: Stable key on candidates: (tenant, matter, kind, date, bench, norm_case)
                            cand = CaseCandidate.objects.filter(
                                tenant_id=tenant_id,
                                matter_id=link.matter_id,
                                kind="HEARING",
                                list_date=list_date,
                                bench=bench,
                                normalized_case_no=item_norm.canonical,
                            ).first()

                            # If dismissed or already exists, never overwrite or recreate
                            if not cand:
                                CaseCandidate.objects.create(
                                    tenant_id=tenant_id,
                                    candidate_id=mint_id("cnd"),
                                    matter_id=link.matter_id,
                                    kind="HEARING",
                                    source="CAUSE_LIST",
                                    source_ref=f"{raw_id}:{item_no}",
                                    case_number_raw=item_norm.raw,
                                    list_date=list_date,
                                    bench=bench,
                                    normalized_case_no=item_norm.canonical,
                                    details={
                                        "court_no": court_no,
                                        "item_no": item_no,
                                        "purpose": purpose,
                                        "parties": parties,
                                    },
                                    status="PENDING",
                                )
                                total_partial_matches += 1

            # User Correction 3: Check if previously matched hearing was dropped from revised list
            existing_cause_hearings = Hearing.objects.filter(
                tenant_id=tenant_id,
                date=list_date,
                bench=bench,
                court_no=court_no,
                source="CAUSE_LIST",
            )
            for eh in existing_cause_hearings:
                if eh.matter_id not in matched_matter_ids:
                    dropped_norm_key = f"DROPPED:{eh.hearing_id}"
                    drop_cand = CaseCandidate.objects.filter(
                        tenant_id=tenant_id,
                        matter_id=eh.matter_id,
                        kind="HEARING_DROPPED",
                        list_date=list_date,
                        bench=bench,
                        normalized_case_no=dropped_norm_key,
                    ).first()

                    if not drop_cand:
                        CaseCandidate.objects.create(
                            tenant_id=tenant_id,
                            candidate_id=mint_id("cnd"),
                            matter_id=eh.matter_id,
                            kind="HEARING_DROPPED",
                            source="CAUSE_LIST",
                            source_ref=f"{raw_id}:dropped",
                            case_number_raw=f"Item {eh.item_no}",
                            list_date=list_date,
                            bench=bench,
                            normalized_case_no=dropped_norm_key,
                            details={
                                "message": f"Listing at item {eh.item_no} no longer appears in revised cause list",
                                "hearing_id": eh.hearing_id,
                                "court_no": court_no,
                                "original_item_no": eh.item_no,
                            },
                            status="PENDING",
                        )
                        total_dropped_created += 1

    return {
        "status": "SUCCESS",
        "exact_matches": total_exact_matches,
        "partial_matches": total_partial_matches,
        "dropped_candidates": total_dropped_created,
    }


@register_handler("workspace_sync", "doc.parsed.v1")
def handle_doc_parsed(event: dict[str, Any]) -> dict[str, Any]:
    """Consumer handler for doc.parsed.v1.

    Matches orders against tracked cases strictly from listing subject and cause title (header before para 1).
    Body citations are strictly ignored (User Correction 7).
    """
    data = event.get("data", {})
    parse_id = data.get("parse_id", "")
    work_id = data.get("work_id", "")
    metadata = data.get("metadata", {})
    parsed_doc_uri = data.get("parsed_doc_uri", "")

    court_info = metadata.get("court", {})
    bench_str = court_info.get("bench_name") or ""
    bench = normalize_bench(bench_str)
    decision_date_str = metadata.get("decision_date")
    decision_date = date.fromisoformat(decision_date_str) if decision_date_str else None
    parties = metadata.get("parties", "")

    # Extract header candidate case numbers
    header_case_numbers: list[str] = []

    # 1. Header case numbers from metadata
    for cn in metadata.get("case_numbers", []):
        raw_val = cn.get("raw") or ""
        if raw_val:
            header_case_numbers.append(raw_val)

    # 2. User Correction 7: If parsed_doc_uri available, extract text BEFORE paragraph 1
    if parsed_doc_uri:
        try:
            storage = ParsedDocStorage()
            doc_json = storage.fetch_parsed_document(parsed_doc_uri)
            nodes = doc_json.get("nodes", [])

            header_text_parts: list[str] = []
            for n in nodes:
                anchor_id = str(n.get("anchor_id", ""))
                node_type = str(n.get("node_type", ""))
                # Stop at the first numbered paragraph (e.g. #p1 or number_as_printed == '1')
                if "#p1" in anchor_id or (node_type == "PARAGRAPH" and str(n.get("number_as_printed", "")).strip() in ("1", "1.")):
                    break
                header_text_parts.append(str(n.get("text", "")))

            combined_header_text = " ".join(header_text_parts)
            # Scan for case numbers in header text only
            patterns = [
                r"(?:(?:RCP|CP)\s*\([A-Za-z\s]+\)\s*(?:No\.?)?\s*[\d\w\/\-]+)",
                r"(?:(?:Company\s+Appeal|Comp\.\s*App)\s*(?:\([A-Za-z\s]+\))?\s*(?:No\.?)?\s*[\d\w\/\-]+)",
                r"(?:(?:IA|CA|MA)\s*(?:\([A-Za-z\s]+\))?\s*(?:No\.?)?\s*[\d\/]+(?:\s+in\s+[^\n,]+)?)",
            ]
            for pat in patterns:
                for m in re.finditer(pat, combined_header_text, re.IGNORECASE):
                    val = m.group(0).strip()
                    if val not in header_case_numbers:
                        header_case_numbers.append(val)
        except Exception as exc:
            logger.warn("failed_to_extract_order_header_text", error=str(exc))

    if not header_case_numbers:
        return {"status": "SKIPPED", "reason": "NO_HEADER_CASE_NUMBERS"}

    # Normalize header cases with default_bench = bench
    normalized_order_cases = [
        normalize_case_number(cn, default_bench=bench)
        for cn in header_case_numbers
    ]

    tenant_ids = get_active_tenant_ids(purpose="ORDER_SYNC")
    exact_matches = 0
    partial_matches = 0

    for tenant_id in tenant_ids:
        with tenant_db_context(tenant_id=tenant_id, user_id="system:ordersync", purpose="ORDER_SYNC"):
            tracked_links = list(
                MatterCaseLink.objects.filter(tenant_id=tenant_id, track=True)
            )
            if not tracked_links:
                continue

            for ord_c in normalized_order_cases:
                if not ord_c.parseable:
                    continue

                for link in tracked_links:
                    tracked_c = normalize_case_number(link.value_normalized)
                    if not tracked_c.parseable:
                        continue

                    match_res = compare_case_numbers(ord_c, tracked_c)

                    if match_res == "EXACT":
                        # Insert matter dependency: kind='OWN_CASE'
                        MatterDependency.objects.update_or_create(
                            tenant_id=tenant_id,
                            matter_id=link.matter_id,
                            public_id=work_id or parse_id,
                            kind="OWN_CASE",
                            defaults={
                                "match_key": ord_c.canonical,
                                "as_of_legal_date": decision_date,
                                "source_ref": f"ibbi:{parse_id}",
                                "weight": 1.0,
                            },
                        )
                        exact_matches += 1

                    elif match_res == "PARTIAL":
                        # Insert case candidate: kind='ORDER'
                        cand = CaseCandidate.objects.filter(
                            tenant_id=tenant_id,
                            matter_id=link.matter_id,
                            kind="ORDER",
                            list_date=decision_date,
                            bench=ord_c.bench or bench,
                            normalized_case_no=ord_c.canonical,
                        ).first()

                        if not cand:
                            CaseCandidate.objects.create(
                                tenant_id=tenant_id,
                                candidate_id=mint_id("cnd"),
                                matter_id=link.matter_id,
                                kind="ORDER",
                                source="IBBI_ORDER",
                                source_ref=parse_id,
                                case_number_raw=ord_c.raw,
                                list_date=decision_date,
                                bench=ord_c.bench or bench,
                                normalized_case_no=ord_c.canonical,
                                details={
                                    "parties": parties,
                                    "decision_date": decision_date_str,
                                    "work_id": work_id,
                                },
                                status="PENDING",
                            )
                            partial_matches += 1

    return {
        "status": "SUCCESS",
        "exact_matches": exact_matches,
        "partial_matches": partial_matches,
    }
