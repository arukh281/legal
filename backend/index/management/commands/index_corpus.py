"""Management command to index the canonical public corpus into a generation partition.

Normative sources:
- Session S06 Plan & Exit Check
- Skips MERGED and STUB works
- Uses forced re-index path per Directive #5
"""

from __future__ import annotations

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
            "--fake-embedder",
            action="store_true",
            default=True,
            help="Use FakeModelAdapter to generate embeddings locally without external API calls.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        generation = options.get("generation", "g1")
        limit = options.get("limit", 0)

        if options.get("fake_embedder", True):
            from gateway.adapters.fake import FakeModelAdapter
            from gateway.runner import set_adapter_override

            set_adapter_override("voyage", FakeModelAdapter())
            self.stdout.write(
                self.style.WARNING("Using FakeModelAdapter (no external Voyage API calls).")
            )

        self.stdout.write(
            self.style.NOTICE(
                f"=== Session S06: Indexing Corpus into Generation '{generation}' ==="
            )
        )

        # Query all candidate canonical works with accepted parses
        sql = """
        SELECT DISTINCT ON (w.work_id, p.expression_key)
               w.work_id, p.expression_key, p.parse_id
        FROM plc.work w
        JOIN plc.parse_run p ON p.work_id = w.work_id
        WHERE w.status NOT IN ('MERGED', 'STUB')
        ORDER BY w.work_id, p.expression_key, p.parse_id DESC
        """
        if limit > 0:
            sql += f" LIMIT {limit};"
        else:
            sql += ";"

        with connection.cursor() as cur:
            cur.execute(sql)
            candidates = cur.fetchall()

        self.stdout.write(f"Found {len(candidates)} canonical expression(s) eligible for indexing.")

        pipeline = IndexPipeline(generation=generation)
        indexed_count = 0
        total_chunks = 0
        quarantined_count = 0
        skipped_count = 0

        for work_id, expr_key, parse_id in candidates:
            res = pipeline.index_expression(
                work_id=work_id,
                expression_key=expr_key,
                parse_id=parse_id,
                force=True,  # Backfill path per Directive #5
                generation=generation,
            )

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
