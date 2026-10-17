"""Management command to index the canonical public corpus into a generation partition.

Normative sources:
- Session S06 Plan & Exit Check
- Skips MERGED and STUB works
- Uses forced re-index path per Directive #5
"""

from __future__ import annotations

import time
from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

from index.indexer import IndexPipeline


class Command(BaseCommand):
    help = "Backfill indexing across the canonical public corpus into a generation partition."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--generation",
            type=str,
            default="g1",
            help="Target index generation partition (default: g1).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of documents to index (0 = all).",
        )
        parser.add_argument(
            "--real-embedder",
            action="store_true",
            default=False,
            help="Use real external embedding model via Model Gateway (do not use FakeModelAdapter).",
        )
        parser.add_argument(
            "--resume",
            action="store_true",
            default=False,
            help="Skip expressions that already have chunks in the target generation partition.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.0,
            help="Delay in seconds between indexing expressions to avoid rate limits.",
        )
        parser.add_argument(
            "--fake-embedder",
            action="store_true",
            default=True,
            help="Use FakeModelAdapter to generate embeddings locally without external API calls.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        generation = options.get("generation", "g1")
        limit = options.get("limit", 0)
        use_real = options.get("real_embedder", False)
        resume = options.get("resume", False)
        delay = options.get("delay", 0.0)

        if not use_real:
            from gateway.adapters.fake import FakeModelAdapter
            from gateway.runner import set_adapter_override

            set_adapter_override("voyage", FakeModelAdapter())
            set_adapter_override("google", FakeModelAdapter())
            self.stdout.write(
                self.style.WARNING("Using FakeModelAdapter (no external embedding API calls).")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Using real embedding models via Model Gateway.")
            )

        self.stdout.write(
            self.style.NOTICE(
                f"=== Session S06: Indexing Corpus into Generation '{generation}' ==="
            )
        )

        # Query all candidate canonical works with accepted parses
        if resume:
            sql = """
            SELECT DISTINCT ON (w.work_id, p.expression_key)
                   w.work_id, p.expression_key, p.parse_id
            FROM plc.work w
            JOIN plc.parse_run p ON p.work_id = w.work_id
            WHERE w.status NOT IN ('MERGED', 'STUB')
              AND NOT EXISTS (
                  SELECT 1 FROM plc.chunk c
                  WHERE c.index_generation = %s
                    AND c.work_id = w.work_id
                    AND c.expression_key = p.expression_key
              )
            ORDER BY w.work_id, p.expression_key, p.parse_id DESC
            """
            params: list[Any] = [generation]
        else:
            sql = """
            SELECT DISTINCT ON (w.work_id, p.expression_key)
                   w.work_id, p.expression_key, p.parse_id
            FROM plc.work w
            JOIN plc.parse_run p ON p.work_id = w.work_id
            WHERE w.status NOT IN ('MERGED', 'STUB')
            ORDER BY w.work_id, p.expression_key, p.parse_id DESC
            """
            params = []

        if limit > 0:
            sql += f" LIMIT {limit};"
        else:
            sql += ";"

        with connection.cursor() as cur:
            cur.execute(sql, params)
            candidates = cur.fetchall()

        if use_real and delay == 0.0:
            delay = 4.5

        gold_works = {
            "wrk_01M3Y2TMYE567QN84SXM3431NZ",
            "wrk_01M3Y2VC1MR98J1A5C6GTG8DCW",
            "wrk_01M3Y2VDC4AF2SJSPMYBSRXK99",
            "wrk_01M3Y2VHSCW4DQSH9VJ3Z2RJWX",
            "wrk_01M3Y2VM40R56G8R4YMDNM1BTA",
            "wrk_01M3Y2VN62VEPM3MH330JF3VKD",
            "wrk_01M3Y2VRFJGZAF26VMB4236ZFS",
            "wrk_01M3Y2W3B6E90BS9NC96GF0W9V",
        }
        candidates.sort(key=lambda c: (0 if c[0] in gold_works else 1, c[0], c[1]))

        self.stdout.write(f"Found {len(candidates)} canonical expression(s) eligible for indexing.")

        pipeline = IndexPipeline(generation=generation)
        indexed_count = 0
        total_chunks = 0
        quarantined_count = 0
        skipped_count = 0

        for idx, (work_id, expr_key, parse_id) in enumerate(candidates, 1):
            if delay > 0 and idx > 1:
                time.sleep(delay)
            try:
                res = pipeline.index_expression(
                    work_id=work_id,
                    expression_key=expr_key,
                    parse_id=parse_id,
                    force=True,  # Backfill path per Directive #5
                    generation=generation,
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ERROR] {work_id}/{expr_key}: {exc}. Sleeping 20s before continuing..."
                    )
                )
                time.sleep(20.0)
                continue

            if res.quarantined:
                quarantined_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  [QUARANTINED] {work_id}/{expr_key}: {', '.join(res.quarantine_reasons)}"
                    )
                )
            elif res.skipped:
                skipped_count += 1
                self.stdout.write(f"  [SKIPPED] {work_id}/{expr_key}: {res.skip_reason}")
            else:
                indexed_count += 1
                total_chunks += res.chunk_count
                self.stdout.write(
                    f"  [INDEXED] {work_id}/{expr_key} -> {res.chunk_count} chunk(s) (seq={res.doc_seq})"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nIndexing complete: {indexed_count} indexed ({total_chunks} chunks), "
                f"{quarantined_count} quarantined, {skipped_count} skipped."
            )
        )
