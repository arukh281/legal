"""Management command to parse captured documents and print a comprehensive quality report.

Normative source:
- Session S05a Requirement 8 & Exit Check:
  "A management command to parse N captured documents and print a quality report:
   pages by text-layer vs OCR, paragraphs found, anchors issued, flags, failures.
   Exit check: parse all ~160 captured IBBI orders; report the quality summary
   (pass/fail/review counts, OCR share, average paragraphs per doc); show 3 parsed
   documents with their anchors next to the PDF pages."
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from ingest.models import Capture
from ingest.storage import BlobStorage
from parse.consumer import persist_pipeline_result
from parse.models import Manifestation, ParseRun, Work
from parse.pipeline import ParsingPipeline


def resolve_canonical_work_id(work_id: str | None) -> str | None:
    """Follow merged_into chain if work status is MERGED, never attaching to a MERGED work."""
    if not work_id:
        return None
    visited: set[str] = set()
    current_id: str | None = work_id
    while current_id and current_id not in visited:
        visited.add(current_id)
        work = Work.objects.filter(work_id=current_id).first()
        if not work:
            break
        if work.status == "MERGED" and work.merged_into_id:
            current_id = work.merged_into_id
        else:
            break
    return current_id


class Command(BaseCommand):
    help = "Parse captured PDFs and display quality and anchor assignment report."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of captured documents to parse.",
        )
        parser.add_argument(
            "--capture-id",
            type=str,
            default=None,
            help="Parse a specific capture by capture_id.",
        )
        parser.add_argument(
            "--source-record-key",
            type=str,
            default=None,
            help="Filter by specific source_record_key.",
        )
        parser.add_argument(
            "--section",
            type=str,
            default=None,
            help="Filter by section (e.g. nclt, nclat, supreme-court, high-courts).",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Parse all captured PDF documents.",
        )
        parser.add_argument(
            "--show-samples",
            type=int,
            default=3,
            help="Number of parsed documents to display in detail.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        limit = options.get("limit")
        section = options.get("section")
        capture_id = options.get("capture_id")
        source_record_key = options.get("source_record_key")
        show_samples = options.get("show_samples", 3)

        qs = Capture.objects.filter(change_kind__in=["NEW", "CHANGED"])
        if capture_id:
            qs = qs.filter(capture_id=capture_id)
        if source_record_key:
            qs = qs.filter(source_record_key=source_record_key)
        if section:
            qs = qs.filter(source_record_key__startswith=f"{section}:")
        elif not capture_id and not source_record_key:
            # Exclude non-PDF policies
            qs = qs.exclude(source_record_key__startswith="policy:")

        # Deduplicate by raw_id so each distinct PDF is parsed
        captures_by_raw: dict[str, Capture] = {}
        for c in qs.order_by("fetched_at"):
            if c.raw_id not in captures_by_raw:
                captures_by_raw[c.raw_id] = c

        all_captures = list(captures_by_raw.values())
        if limit:
            all_captures = all_captures[:limit]

        total_to_parse = len(all_captures)
        self.stdout.write(
            self.style.NOTICE(
                f"=== S05a Parsing Engine: Processing {total_to_parse} Captured Documents ==="
            )
        )

        pipeline = ParsingPipeline()
        storage = BlobStorage()

        stats: dict[str, int] = {
            "total_docs": 0,
            "pass_count": 0,
            "flagged_count": 0,
            "quarantined_count": 0,
            "born_digital_pages": 0,
            "ocr_pages": 0,
            "total_pages": 0,
            "total_anchors": 0,
            "total_paras": 0,
            "hidden_text_docs": 0,
            "handwriting_docs": 0,
            "lang_unsupported_docs": 0,
            "llm_fallback_docs": 0,
            "errors": 0,
        }
        sections: dict[str, int] = {}

        sample_results: list[Any] = []

        for idx, cap in enumerate(all_captures, 1):
            sec = cap.source_record_key.split(":")[0]
            sections[sec] = sections.get(sec, 0) + 1

            # Look up existing work_id for this raw_id to ensure idempotent re-parses
            existing_run = (
                ParseRun.objects.filter(raw_ids__contains=[cap.raw_id])
                .order_by("-created_at")
                .first()
            )
            existing_work_id = existing_run.work_id if existing_run else None
            supersedes_parse_id = existing_run.parse_id if existing_run else None

            if not existing_work_id:
                manifestation = (
                    Manifestation.objects.filter(raw_ids__contains=[cap.raw_id])
                    .order_by("-first_seen")
                    .first()
                )
                if manifestation:
                    existing_work_id = manifestation.work_id

            # When no ParseRun/Manifestation matches cap.raw_id, look up the latest work
            # for the same source_record_key (e.g. CHANGED captures where the raw blob changed)
            if not existing_work_id:
                prior_raw_ids = list(
                    Capture.objects.filter(
                        source_id=cap.source_id,
                        source_record_key=cap.source_record_key,
                    )
                    .exclude(raw_id=cap.raw_id)
                    .order_by("-fetched_at")
                    .values_list("raw_id", flat=True)
                )
                if cap.prior_raw_id and cap.prior_raw_id not in prior_raw_ids:
                    prior_raw_ids.append(cap.prior_raw_id)

                if prior_raw_ids:
                    prior_run = (
                        ParseRun.objects.filter(raw_ids__overlap=prior_raw_ids)
                        .order_by("-created_at")
                        .first()
                    )
                    if prior_run:
                        existing_work_id = prior_run.work_id
                        supersedes_parse_id = prior_run.parse_id
                    else:
                        prior_man = (
                            Manifestation.objects.filter(raw_ids__overlap=prior_raw_ids)
                            .order_by("-first_seen")
                            .first()
                        )
                        if prior_man:
                            existing_work_id = prior_man.work_id

            # Whenever an existing work is picked, follow merged_into if status is MERGED,
            # ensuring a new parse run is never attached to a MERGED work.
            if existing_work_id:
                canonical_work_id = resolve_canonical_work_id(existing_work_id)
                if canonical_work_id != existing_work_id:
                    existing_work_id = canonical_work_id
                    latest_canonical_run = (
                        ParseRun.objects.filter(work_id=canonical_work_id)
                        .order_by("-created_at")
                        .first()
                    )
                    if latest_canonical_run:
                        supersedes_parse_id = latest_canonical_run.parse_id

            try:
                raw_bytes = storage.get_blob(cap.raw_id, content_type="application/pdf")
            except Exception as e:
                self.stderr.write(
                    f"[{idx}/{total_to_parse}] Failed to fetch blob {cap.raw_id}: {e}"
                )
                stats["errors"] += 1
                continue

            try:
                res = pipeline.process(
                    raw_bytes,
                    raw_id=cap.raw_id,
                    source_id=cap.source_id,
                    url=cap.url or "",
                    terms_ref=getattr(cap, "terms_ref", "tou_ibbi@2026-10-01"),
                    fetched_at=cap.fetched_at.isoformat() if cap.fetched_at else "",
                    rights_class=cap.rights_class,
                    provenance_tier=cap.provenance_tier,
                    source_metadata=cap.source_metadata,
                    existing_work_id=existing_work_id,
                )

                # Persist to database & outbox
                persist_pipeline_result(
                    res,
                    source_id=cap.source_id,
                    raw_id=cap.raw_id,
                    url=cap.url or "",
                    rights_class=cap.rights_class,
                    provenance_tier=cap.provenance_tier,
                    lane="bulk",
                    supersedes_parse_id=supersedes_parse_id,
                )

                stats["total_docs"] += 1
                gate = res.quality.gate
                if gate == "PASS":
                    stats["pass_count"] += 1
                elif gate == "FLAGGED":
                    stats["flagged_count"] += 1
                else:
                    stats["quarantined_count"] += 1

                doc_pages = len(res.parsed_doc.get("pages", []))
                stats["total_pages"] += doc_pages
                bd_pages = sum(
                    1
                    for p in res.parsed_doc.get("pages", [])
                    if p.get("text_source") == "TEXT_LAYER"
                )
                stats["born_digital_pages"] += bd_pages
                stats["ocr_pages"] += doc_pages - bd_pages

                doc_anchors = len(res.nodes)
                stats["total_anchors"] += doc_anchors
                doc_paras = sum(1 for n in res.nodes if n.node_type == "PARA")
                stats["total_paras"] += doc_paras

                if res.quality.hidden_text_flags:
                    stats["hidden_text_docs"] += 1
                if any(n.is_handwriting for n in res.nodes):
                    stats["handwriting_docs"] += 1
                if any(p.get("is_lang_unsupported") for p in res.parsed_doc.get("pages", [])):
                    stats["lang_unsupported_docs"] += 1
                if res.used_llm_fallback:
                    stats["llm_fallback_docs"] += 1

                if len(sample_results) < show_samples:
                    sample_results.append(res)

                if idx % 10 == 0 or idx == total_to_parse:
                    self.stdout.write(
                        f"Progress: [{idx}/{total_to_parse}] docs parsed | "
                        f"Gate: PASS={stats['pass_count']} FLAGGED={stats['flagged_count']} QUARANTINED={stats['quarantined_count']} | "
                        f"Anchors: {stats['total_anchors']}"
                    )

            except Exception as exc:
                self.stderr.write(
                    f"[{idx}/{total_to_parse}] Parse error on {cap.source_record_key}: {exc}"
                )
                stats["errors"] += 1

        # Summary Report
        avg_paras = round(stats["total_paras"] / max(1, stats["total_docs"]), 1)
        ocr_share = round((stats["ocr_pages"] / max(1, stats["total_pages"])) * 100, 2)
        pass_share = round((stats["pass_count"] / max(1, stats["total_docs"])) * 100, 1)

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("=== S05a PARSING QUALITY SUMMARY REPORT ==="))
        self.stdout.write("=" * 70)
        self.stdout.write(f"Total Captured Documents Processed: {stats['total_docs']}")
        self.stdout.write(f"Sections Breakdown: {sections}")
        self.stdout.write(f"Total Pages Analyzed: {stats['total_pages']}")
        self.stdout.write(f"  - Born-Digital Pages (Text Layer): {stats['born_digital_pages']}")
        self.stdout.write(
            f"  - OCR Pages (Scanned/Image):        {stats['ocr_pages']} ({ocr_share}% OCR Share)"
        )
        self.stdout.write(f"Total Permanent Anchors Issued:      {stats['total_anchors']}")
        self.stdout.write(f"Average Numbered Paragraphs / Doc:    {avg_paras}")
        self.stdout.write("\nQuality Gate Distribution:")
        self.stdout.write(f"  - PASS:        {stats['pass_count']:>4} ({pass_share}%)")
        self.stdout.write(
            f"  - FLAGGED:     {stats['flagged_count']:>4} (Routed to Admin Review Queue)"
        )
        self.stdout.write(f"  - QUARANTINED: {stats['quarantined_count']:>4} (Excluded from Index)")
        self.stdout.write("\nIntegrity & Safety Flags:")
        self.stdout.write(f"  - Hidden Text Detected:   {stats['hidden_text_docs']} documents")
        self.stdout.write(f"  - Handwriting Flagged:     {stats['handwriting_docs']} documents")
        self.stdout.write(
            f"  - Lang Unsupported Flags:  {stats['lang_unsupported_docs']} documents"
        )
        self.stdout.write(f"  - LLM Fallback Invocations: {stats['llm_fallback_docs']} documents")
        self.stdout.write("=" * 70)

        # Display Sample Documents with Anchors next to PDF extracts
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(
            self.style.NOTICE("=== SAMPLE PARSED DOCUMENTS WITH PERMANENT ANCHORS ===")
        )
        self.stdout.write("=" * 70)

        for s_idx, sample in enumerate(sample_results, 1):
            h = sample.header
            self.stdout.write(
                f"\n[Sample {s_idx}] Work ID: {sample.work_id} | Parse ID: {sample.parse_id}"
            )
            self.stdout.write(f"  Title:     {h.title}")
            self.stdout.write(f"  Court:     {h.court_id} ({h.bench_name})")
            self.stdout.write(f"  Case No:   {h.case_number} | Date: {h.decision_date}")
            self.stdout.write(
                f"  Gate:      {sample.quality.gate} | Reasons: {sample.quality.gate_reasons}"
            )
            self.stdout.write(f"  Total Anchors: {len(sample.nodes)}")
            self.stdout.write("  --- First 5 Anchors & Coordinates ---")
            for node in sample.nodes[:5]:
                page_info = f"p.{node.spans[0]['page']}" if node.spans else "p.?"
                bbox_info = f"{node.spans[0]['bbox']}" if node.spans else "[]"
                snippet = node.text[:75].replace("\n", " ")
                self.stdout.write(f"    • {node.anchor_id}")
                self.stdout.write(
                    f"      [{node.numbering} {node.node_type} | {page_info} bbox={bbox_info} | conf={node.ocr_conf:.2f}]"
                )
                self.stdout.write(f'      "{snippet}..."')
        self.stdout.write("\n" + "=" * 70)
