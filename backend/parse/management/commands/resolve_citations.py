"""Management command to extract and resolve citations across the parsed corpus.

Normative sources:
- docs/03_P1_ingestion_parsing.md §5.8 & §5.9
- docs/01_master_architecture.md §5.4, §6.3, §7.1
- docs/mvp/03_data_model_and_contracts.md §3.3 & §3.4
- Directives:
  #1: Don't edit stored ParsedDocument in S3 or ParseRun in place.
  #2: Case numbers mint STUB cases; only reporters mint STUB judgment works.
  #3: court_hint: set only when citation explicitly states court.
  #4: Trust tier T4 for citation-derived aliases.
  #5: Statute mentions live only inside ParsedDocument (new object in S3 with bumped pipeline_version).
  #6: Skip QUARANTINED documents. Degraded mentions (ocr_conf < 0.80 or hidden text) reported separately.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from anchor_lib.ids import mint_id
from parse.citations.extractor import ExtractedCitation, extract_citations_from_anchor
from parse.citations.resolver import resolve_citation
from parse.citations.statutes import (
    ExtractedStatuteMention,
    extract_in_document_definitions,
    extract_statute_mentions_from_anchor,
)
from parse.models import Anchor, CitationMention, ParseRun
from parse.storage import ParsedDocStorage


class Command(BaseCommand):
    help = "Extract and resolve citations and statute mentions across parsed documents."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of documents to process (0 = all).",
        )
        parser.add_argument(
            "--write-new-s3-artifacts",
            action="store_true",
            default=True,
            help="Write new ParsedDocument artifacts with bumped pipeline_version to S3.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        limit = options.get("limit", 0)
        write_new_s3 = options.get("write_new_s3_artifacts", True)
        storage = ParsedDocStorage()

        self.stdout.write(
            self.style.NOTICE("=== Session S05b: Citations Extraction & Resolution ===")
        )

        # 1. Fetch latest parse runs per work, skipping QUARANTINED (Directive #6)
        all_runs = (
            ParseRun.objects.select_related("work")
            .order_by("work_id", "-created_at")
            .distinct("work_id")
        )

        quarantined_count = 0
        eligible_runs: list[ParseRun] = []
        for r in all_runs:
            if r.gate == "QUARANTINED":
                quarantined_count += 1
            else:
                eligible_runs.append(r)

        if limit > 0:
            eligible_runs = eligible_runs[:limit]

        self.stdout.write(
            f"Found {len(all_runs)} total parse runs: {len(eligible_runs)} eligible, {quarantined_count} QUARANTINED (skipped)."
        )

        # Statistics accumulators
        citations_by_scheme: Counter[str] = Counter()
        citations_by_status: Counter[str] = Counter()
        statutes_by_status: Counter[str] = Counter()
        degraded_citations = 0
        degraded_statutes = 0

        resolved_examples: list[
            tuple[ExtractedCitation, str, str]
        ] = []  # (mention, target, anchor_text)
        unresolved_examples: list[tuple[ExtractedCitation, str]] = []  # (mention, anchor_text)

        total_citations_persisted = 0
        total_statute_mentions_found = 0

        for idx, run in enumerate(eligible_runs, 1):
            work = run.work
            parse_id = run.parse_id
            expr_key = run.expression_key

            # Fetch anchors for this work and expression
            anchors = list(
                Anchor.objects.filter(
                    work_id=work.work_id,
                    expression_key=expr_key,
                    state="LIVE",
                ).order_by("anchor_id")
            )

            # Extract in-document definitions from early anchors
            early_text = " ".join(
                a.text
                for a in anchors
                if any(h in a.anchor_id for h in ("#hdr", "#p1", "#u1", "#p2"))
            )
            doc_defs = extract_in_document_definitions(early_text)

            doc_citations: list[ExtractedCitation] = []
            doc_statutes: list[ExtractedStatuteMention] = []

            for anc in anchors:
                ocr_conf = anc.ocr_conf if anc.ocr_conf is not None else 1.0
                is_hidden = anc.anchor_id in (run.quality.get("hidden_text_flags") or [])

                # 1. Extract citations
                anc_cites = extract_citations_from_anchor(
                    anchor_id=anc.anchor_id,
                    text=anc.text,
                    decision_date=work.decision_date,
                    ocr_conf=ocr_conf,
                    is_hidden=is_hidden,
                )
                doc_citations.extend(anc_cites)

                # 2. Extract statute mentions
                anc_statutes = extract_statute_mentions_from_anchor(
                    anchor_id=anc.anchor_id,
                    text=anc.text,
                    decision_date=work.decision_date,
                    document_definitions=doc_defs,
                    ocr_conf=ocr_conf,
                    is_hidden=is_hidden,
                )
                doc_statutes.extend(anc_statutes)

            # Persist citations to plc.citation_mention
            with transaction.atomic():
                # Clear previous mentions for this parse_id to be idempotent
                CitationMention.objects.filter(parse_id=parse_id).delete()

                for cite in doc_citations:
                    citations_by_scheme[cite.scheme] += 1
                    if cite.degraded_quality:
                        degraded_citations += 1

                    # Resolve citation
                    target_id, conf, method = resolve_citation(
                        mention=cite,
                        citing_work_id=work.work_id,
                    )

                    # Determine status
                    if target_id and method == "ALIAS_EXACT":
                        status_label = "RESOLVED"
                        if len(resolved_examples) < 5 and not cite.degraded_quality:
                            resolved_examples.append((cite, target_id, cite.raw_text))
                    elif method == "STUB_MINTED":
                        status_label = "STUB_MINTED"
                        if len(resolved_examples) < 5 and not cite.degraded_quality:
                            resolved_examples.append((cite, f"STUB:{target_id}", cite.raw_text))
                    else:
                        status_label = "UNRESOLVED"
                        if len(unresolved_examples) < 5:
                            unresolved_examples.append((cite, cite.raw_text))

                    citations_by_status[status_label] += 1

                    CitationMention.objects.create(
                        mention_id=cite.mention_id,
                        parse=run,
                        citing_work=work,
                        anchor_id=cite.anchor_id,
                        raw_text=cite.raw_text,
                        mention_kind=cite.mention_kind,
                        scheme=cite.scheme,
                        normalized=cite.normalized,
                        pin=cite.pin,
                        resolved_target_id=target_id,
                        resolution_confidence=conf,
                        resolution_method=method,
                        temporal_check=cite.temporal_check,
                    )
                    total_citations_persisted += 1

            for st in doc_statutes:
                statutes_by_status[st.resolution_status] += 1
                if st.degraded_quality:
                    degraded_statutes += 1
                total_statute_mentions_found += 1

            # Directive #5: Write new ParsedDocument to S3 with bumped pipeline_version
            if write_new_s3:
                try:
                    old_doc = storage.get_parsed_document(run.parsed_doc_uri)
                    new_doc = dict(old_doc)
                    new_parse_id = mint_id("par")

                    # Add serializable citations
                    new_doc["citations"] = [
                        {
                            "mention_id": c.mention_id,
                            "raw_text": c.raw_text,
                            "anchor_id": c.anchor_id,
                            "char_range": list(c.char_range),
                            "mention_kind": c.mention_kind,
                            "scheme": c.scheme,
                            "normalized": c.normalized,
                            "pin": c.pin,
                            "court_hint": c.court_hint,
                            "date_hint": c.date_hint,
                            "temporal_check": c.temporal_check,
                            "quote_selector": c.quote_selector,
                            "degraded_quality": c.degraded_quality,
                            "quality_reasons": c.quality_reasons,
                        }
                        for c in doc_citations
                    ]

                    # Add serializable statute mentions
                    new_doc["statute_mentions"] = [
                        {
                            "mention_id": s.mention_id,
                            "anchor_id": s.anchor_id,
                            "raw_text": s.raw_text,
                            "act_raw": s.act_raw,
                            "act_work_id": s.act_work_id,
                            "provisions": s.provisions,
                            "as_cited_date": s.as_cited_date,
                            "pit_rule": s.pit_rule,
                            "resolved_anchor_ids": s.resolved_anchor_ids,
                            "resolution_status": s.resolution_status,
                            "quote_selector": s.quote_selector,
                            "conf": s.conf,
                            "degraded_quality": s.degraded_quality,
                            "quality_reasons": s.quality_reasons,
                        }
                        for s in doc_statutes
                    ]

                    new_doc["pipeline_version"] = "p1.citation@0.1.0|det_v1"

                    # Upload to new S3 key (old S3 object remains untouched)
                    storage.upload_parsed_document(
                        new_doc,
                        work_id=work.work_id,
                        expression_key=expr_key,
                        parse_id=new_parse_id,
                    )
                except Exception as exc:
                    self.stdout.write(
                        self.style.WARNING(
                            f"S3 artifact creation skipped for {work.work_id}: {exc}"
                        )
                    )

            if idx % 20 == 0 or idx == len(eligible_runs):
                self.stdout.write(f"Processed [{idx}/{len(eligible_runs)}] documents...")

        # Print Comprehensive Quality Summary Report
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("=== S05b CITATIONS & STATUTE MENTIONS QUALITY REPORT ===")
        self.stdout.write("=" * 70)
        self.stdout.write(
            f"Total Eligible Documents Processed: {len(eligible_runs)} (Quarantined Skipped: {quarantined_count})"
        )
        self.stdout.write(
            f"Total Citations Persisted to plc.citation_mention: {total_citations_persisted}"
        )
        self.stdout.write(f"Total Statute Mentions Found: {total_statute_mentions_found}")

        self.stdout.write("\n--- Citations Breakdown by Scheme ---")
        for sch, cnt in sorted(citations_by_scheme.items(), key=lambda x: -x[1]):
            self.stdout.write(f"  • {sch:<15}: {cnt}")

        self.stdout.write("\n--- Citations Resolution Status ---")
        for status_label, cnt in sorted(citations_by_status.items(), key=lambda x: -x[1]):
            self.stdout.write(f"  • {status_label:<15}: {cnt}")

        self.stdout.write("\n--- Statute Mentions Resolution Status ---")
        for status_label, cnt in sorted(statutes_by_status.items(), key=lambda x: -x[1]):
            self.stdout.write(f"  • {status_label:<20}: {cnt}")

        self.stdout.write("\n--- Quality Degradation (Directive #6) ---")
        self.stdout.write(
            f"  • Degraded Citations (ocr_conf < 0.80 or hidden text): {degraded_citations}"
        )
        self.stdout.write(f"  • Degraded Statute Mentions: {degraded_statutes}")

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("=== 5 RESOLVED / STUB-LINKED EXAMPLES WITH ANCHORS ===")
        self.stdout.write("=" * 70)
        for i, (cite, target, raw) in enumerate(resolved_examples[:5], 1):
            self.stdout.write(
                f"[{i}] Mention ID: {cite.mention_id} | Scheme: {cite.scheme} | Kind: {cite.mention_kind}"
            )
            self.stdout.write(f"    Source Anchor:   {cite.anchor_id}")
            self.stdout.write(f"    Raw Text:        {raw!r}")
            self.stdout.write(f"    Normalized Key:  {cite.normalized}")
            self.stdout.write(f"    Resolved Target: {target}")
            self.stdout.write(
                f"    Quote Selector:  prefix={cite.quote_selector['prefix']!r}, exact={cite.quote_selector['exact']!r}, suffix={cite.quote_selector['suffix']!r}"
            )

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("=== 5 UNRESOLVED EXAMPLES WITH ANCHORS ===")
        self.stdout.write("=" * 70)
        for i, (cite, raw) in enumerate(unresolved_examples[:5], 1):
            self.stdout.write(
                f"[{i}] Mention ID: {cite.mention_id} | Scheme: {cite.scheme} | Kind: {cite.mention_kind}"
            )
            self.stdout.write(f"    Source Anchor:   {cite.anchor_id}")
            self.stdout.write(f"    Raw Text:        {raw!r}")
            self.stdout.write(f"    Normalized Key:  {cite.normalized}")
            self.stdout.write(
                f"    Quote Selector:  prefix={cite.quote_selector['prefix']!r}, exact={cite.quote_selector['exact']!r}, suffix={cite.quote_selector['suffix']!r}"
            )
        self.stdout.write("=" * 70 + "\n")
