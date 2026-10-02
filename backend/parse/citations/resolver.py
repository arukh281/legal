"""Resolver for legal citations using IdentifierAlias and trust tiers.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.9 (resolution algorithm, STUB works, acquire.requested.v1)
- docs/01_master_architecture.md §5.4 (trust tiers T0-T4), §6.3 (acquire.requested.v1)
- docs/mvp/03_data_model_and_contracts.md §3.3 & §3.4
- S05b Directives:
  #2: Case numbers mint STUB cases; only reporters mint STUB judgment works.
  #3: court_hint: set only when citation explicitly states court.
  #4: Trust tier T4 for citation-derived aliases; source="citation_mention", evidence={mention_id, citing_work_id, anchor_id}.
      When T0-T2 arrives later, T4 becomes SUPERSEDED, STUB merges into real work via identity_merge_ledger, and mentions re-point.
"""

from __future__ import annotations

from datetime import UTC, datetime

from django.db import transaction

from anchor_lib.ids import mint_id
from ops.outbox import publish_event
from parse.citations.extractor import ExtractedCitation
from parse.models import (
    CitationMention,
    Court,
    IdentifierAlias,
    IdentityMergeLedger,
    LegalCase,
    Work,
    WorkCase,
)

TRUST_TIER_PRIORITY: dict[str, int] = {
    "T0": 5,
    "T1": 4,
    "T2": 3,
    "T3": 2,
    "T4": 1,
}


def resolve_citation(
    mention: ExtractedCitation,
    citing_work_id: str,
) -> tuple[str | None, float, str]:
    """Resolve an extracted citation against identifier_alias.

    Returns (resolved_target_id, resolution_confidence, resolution_method).
    """
    now = datetime.now(UTC)

    # 1. Check existing active aliases
    aliases = list(
        IdentifierAlias.objects.filter(
            scheme=mention.scheme,
            value_normalized=mention.normalized,
            status="ACTIVE",
        )
    )

    if aliases:
        # Pick the highest trust tier
        best_alias = max(
            aliases,
            key=lambda a: TRUST_TIER_PRIORITY.get(a.trust_tier, 0),
        )
        target = best_alias.target_id

        # If target is a case_id, look up lead WorkCase
        if target.startswith("cas_"):
            wc = WorkCase.objects.filter(case_id=target).first()
            if wc:
                return wc.work_id, best_alias.confidence, "ALIAS_EXACT"
            return target, best_alias.confidence, "ALIAS_EXACT"

        return target, best_alias.confidence, "ALIAS_EXACT"

    # 2. Unresolved: Handle by citation kind (Directive #2 & Directive #4)
    # 2a. Case Numbers: "CP (IB) 188 of 2026", "Civil Appeal No. 1234 of 2019"
    if mention.scheme == "CASE_NO":
        # Directive 4: If court isn't stated in citation, leave mention UNRESOLVED
        if not mention.court_hint:
            return None, 0.0, "UNRESOLVED"

        with transaction.atomic():
            # Check if active STUB alias was created concurrently
            existing_stub_alias = IdentifierAlias.objects.filter(
                scheme="CASE_NO",
                value_normalized=mention.normalized,
                status="ACTIVE",
            ).first()

            if existing_stub_alias:
                return existing_stub_alias.target_id, 0.5, "STUB_MINTED"

            # Parse court
            court_obj = Court.objects.filter(court_id=mention.court_hint).first()
            case_id = mint_id("cas")

            # Extract case number and year from normalized key: court|type|num|year
            parts = mention.normalized.split("|")
            ctype = parts[1] if len(parts) > 1 else ""
            cnum = parts[2] if len(parts) > 2 else ""
            cyear_str = parts[3] if len(parts) > 3 else ""
            cyear = int(cyear_str) if cyear_str.isdigit() else None

            stub_case = LegalCase.objects.create(
                case_id=case_id,
                court=court_obj,
                case_type=ctype,
                number=cnum,
                year=cyear,
                status="STUB",
            )

            # Directive 4: T4 trust tier, source="citation_mention", evidence={mention_id, citing_work_id, anchor_id}
            IdentifierAlias.objects.create(
                scheme="CASE_NO",
                value_normalized=mention.normalized,
                target_id=stub_case.case_id,
                confidence=1.0,
                source="citation_mention",
                trust_tier="T4",
                status="ACTIVE",
                first_seen=now,
                evidence={
                    "mention_id": mention.mention_id,
                    "citing_work_id": citing_work_id,
                    "anchor_id": mention.anchor_id,
                },
            )
            return stub_case.case_id, 0.5, "STUB_MINTED"

    # 2b. Reporter Citations: SCC, SCC OnLine, AIR, SCR, INSC, NEUTRAL_HC
    # Mint a STUB judgment work and emit acquire.requested.v1
    with transaction.atomic():
        existing_stub_alias = IdentifierAlias.objects.filter(
            scheme=mention.scheme,
            value_normalized=mention.normalized,
            status="ACTIVE",
        ).first()

        if existing_stub_alias:
            return existing_stub_alias.target_id, 0.5, "STUB_MINTED"

        stub_work_id = mint_id("wrk")
        court_obj = (
            Court.objects.filter(court_id=mention.court_hint).first()
            if mention.court_hint
            else None
        )

        stub_work = Work.objects.create(
            work_id=stub_work_id,
            work_type="JUDGMENT",
            status="STUB",
            court=court_obj,
            title=None,
            decision_date=None,
            bench_strength=None,
            access_restriction={},
            integrity_flags=[],
        )

        # Directive 4: T4 trust tier
        IdentifierAlias.objects.create(
            scheme=mention.scheme,
            value_normalized=mention.normalized,
            target_id=stub_work.work_id,
            confidence=1.0,
            source="citation_mention",
            trust_tier="T4",
            status="ACTIVE",
            first_seen=now,
            evidence={
                "mention_id": mention.mention_id,
                "citing_work_id": citing_work_id,
                "anchor_id": mention.anchor_id,
            },
        )

        # Emit acquire.requested.v1 event (01 §6.3 / D20.2)
        publish_event(
            event_type="acquire.requested.v1",
            source="p1/citations",
            subject=f"{mention.scheme}:{mention.normalized}",
            dataschema="schemareg://plc/acquire.requested.v1/1.0",
            dataclass="PUBLIC",
            idempotencykey=f"acq|{mention.scheme}|{mention.normalized}",
            schemaversion="1.0",
            data={
                "request_id": mint_id("acq"),
                "reason": "UNRESOLVED_CITATION",
                "sub_reason": None,
                "target": {
                    "scheme": mention.scheme,
                    "value": mention.normalized,
                    "court_hint": mention.court_hint,
                    "date_hint": mention.date_hint,
                },
                "priority": "P2",
                "deadline": None,
                "allowed_access_modes": ["OPEN", "PARTNER_CONTRIBUTED"],
            },
            topic="plc.acquire.requested.v1",
            partition_key=f"{mention.scheme}|{mention.normalized}",
            tenantid=None,
        )

        return stub_work.work_id, 0.5, "STUB_MINTED"


def promote_authoritative_alias(
    scheme: str,
    value_normalized: str,
    authoritative_target_id: str,
    trust_tier: str,
    source: str = "OFFICIAL_REGISTRY",
) -> None:
    """Promote an authoritative (T0-T2) alias for an existing key.

    When an authoritative alias arrives for a key that currently has a T4 STUB alias:
    1. The T4 alias becomes SUPERSEDED.
    2. The new authoritative alias becomes ACTIVE.
    3. The STUB work merges into the real work via plc.identity_merge_ledger.
    4. All CitationMention rows pointing to the STUB are re-pointed.
    5. Emits plc.identity.merged.v1 event.
    """
    now = datetime.now(UTC)

    with transaction.atomic():
        existing_alias = IdentifierAlias.objects.filter(
            scheme=scheme,
            value_normalized=value_normalized,
            status="ACTIVE",
        ).first()

        if existing_alias:
            old_target_id = existing_alias.target_id
            existing_alias.status = "SUPERSEDED"
            existing_alias.save(update_fields=["status"])

            # If old target was a STUB work, merge it
            if old_target_id != authoritative_target_id and old_target_id.startswith("wrk_"):
                old_work = Work.objects.filter(work_id=old_target_id).first()
                if old_work and old_work.status == "STUB":
                    old_work.status = "MERGED"
                    old_work.merged_into_id = authoritative_target_id
                    old_work.save(update_fields=["status", "merged_into"])

                    merge_event_id = mint_id("evr")
                    IdentityMergeLedger.objects.create(
                        event_id=merge_event_id,
                        kind="WORK",
                        op="MERGE",
                        from_id=old_target_id,
                        to_id=authoritative_target_id,
                        reason="AUTHORITATIVE_ALIAS_PROMOTION",
                        confidence=1.0,
                        reversible_until=None,
                        recorded_at=now,
                    )

                    # Re-point citation mentions
                    CitationMention.objects.filter(resolved_target_id=old_target_id).update(
                        resolved_target_id=authoritative_target_id,
                        resolution_method="ALIAS_EXACT",
                        resolution_confidence=1.0,
                    )

                    # Emit identity.merged.v1 event
                    publish_event(
                        event_type="identity.merged.v1",
                        source="p1/citations",
                        subject=f"{old_target_id}->{authoritative_target_id}",
                        dataschema="schemareg://plc/identity.merged.v1/1.0",
                        dataclass="PUBLIC",
                        idempotencykey=f"merge|{merge_event_id}",
                        schemaversion="1.0",
                        data={
                            "kind": "WORK",
                            "from_id": old_target_id,
                            "to_id": authoritative_target_id,
                            "reason": "AUTHORITATIVE_ALIAS_PROMOTION",
                            "confidence": 1.0,
                        },
                        topic="plc.identity.merged.v1",
                        partition_key=old_target_id,
                        tenantid=None,
                    )

        # Create the new authoritative alias
        IdentifierAlias.objects.update_or_create(
            scheme=scheme,
            value_normalized=value_normalized,
            target_id=authoritative_target_id,
            defaults={
                "confidence": 1.0,
                "source": source,
                "trust_tier": trust_tier,
                "status": "ACTIVE",
                "first_seen": now,
                "evidence": {},
            },
        )
