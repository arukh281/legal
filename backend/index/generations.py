"""Index generation lifecycle management: partitions, atomic promotion, and rollback.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.5 (index generations, aliases, and promotion)
- docs/04_P2_enrichment_indexing.md §2.4 (index.generation.promoted.v1 event)
- Session S06 Directive #8: Initial promotion from BUILDING to LIVE writes alias and emits event
"""

from __future__ import annotations

import datetime

from django.db import connection, connections, transaction
from django.utils import timezone

from anchor_lib.ids import mint_id
from index.models import IndexAlias, IndexGeneration
from ops.models import EventOutbox


class IndexNotReadyError(Exception):
    """Raised when no active index alias exists for an index family."""


class GenerationNotFoundError(Exception):
    """Raised when an index generation does not exist."""


class GenerationGoneError(Exception):
    """Raised when get_chunks is called on a retired or rolled back generation."""

    def __init__(self, message: str, anchor_ids: list[str]) -> None:
        super().__init__(message)
        self.anchor_ids = anchor_ids


def get_active_generation(index_family: str = "plc_chunks") -> str:
    """Resolve the active LIVE generation for an index family from ops.index_alias."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT generation FROM ops.index_alias WHERE index_family = %s;",
            [index_family],
        )
        row = cur.fetchone()
        if not row:
            raise IndexNotReadyError(
                f"No active generation alias configured for family '{index_family}'."
            )
        return str(row[0])


def create_generation_partition(
    index_family: str,
    generation: str,
    chunker_version: str = "p2.chunker@0.1.0|det_v1",
    embed_model: str = "voyage-4-large",
    embed_dims: int = 1024,
    fts_config: str = "public.legal_en",
) -> IndexGeneration:
    """Create a new partition table in plc.chunk and register in ops.index_generation."""
    table_name = f"chunk_{generation}"
    ddl_conn = connections["owner"] if "owner" in connections else connection

    with ddl_conn.cursor() as cur:
        # Create partition
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS plc.{table_name}
            PARTITION OF plc.chunk FOR VALUES IN (%s);
            """,
            [generation],
        )
        cur.execute(f"ALTER TABLE plc.{table_name} ALTER COLUMN embedding SET STORAGE PLAIN;")
        cur.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {table_name}_embedding_hnsw
            ON plc.{table_name} USING hnsw ((embedding::halfvec({embed_dims})) halfvec_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """
        )
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS {table_name}_tsv_gin ON plc.{table_name} USING gin (tsv);"
        )
        cur.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {table_name}_binding_tags_gin
            ON plc.{table_name} USING gin (binding_scope_tags);
            """
        )
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS {table_name}_work_id_idx ON plc.{table_name} (work_id);"
        )

        # Grant permissions
        cur.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON plc.{table_name} TO app_rw, worker, plc_writer, admin_rw;"
        )

        # Register in ops.index_generation
        cur.execute(
            """
            INSERT INTO ops.index_generation (
                index_family, generation, chunker_version, embed_model, embed_dims, fts_config, state, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, 'BUILDING', now())
            ON CONFLICT (index_family, generation) DO NOTHING;
            """,
            [index_family, generation, chunker_version, embed_model, embed_dims, fts_config],
        )

    return IndexGeneration.objects.get(index_family=index_family, generation=generation)


@transaction.atomic
def promote_generation(
    index_family: str,
    to_generation: str,
    eval_report_uri: str | None = None,
    gate_decision_id: str | None = None,
    reason: str = "PROMOTION",
) -> IndexAlias:
    """Atomically swap the alias to to_generation, set LIVE state, and emit promotion event."""
    try:
        target_gen = IndexGeneration.objects.select_for_update().get(
            index_family=index_family, generation=to_generation
        )
    except IndexGeneration.DoesNotExist as exc:
        raise GenerationNotFoundError(
            f"Generation '{to_generation}' for family '{index_family}' does not exist."
        ) from exc

    # Check existing alias
    alias = IndexAlias.objects.select_for_update().filter(index_family=index_family).first()
    from_generation = alias.generation if alias else None

    now = timezone.now()
    rollback_deadline = now + datetime.timedelta(days=14)

    # 1. Update previous generation if exists
    if from_generation and from_generation != to_generation:
        IndexGeneration.objects.filter(
            index_family=index_family, generation=from_generation
        ).update(state="RETIRED")

    # 2. Update target generation
    target_gen.state = "LIVE"
    target_gen.promoted_at = now
    target_gen.rollback_deadline = rollback_deadline
    target_gen.eval_report_uri = eval_report_uri
    target_gen.gate_decision_id = gate_decision_id
    target_gen.save(
        update_fields=[
            "state",
            "promoted_at",
            "rollback_deadline",
            "eval_report_uri",
            "gate_decision_id",
        ]
    )

    # 3. Upsert ops.index_alias
    if alias:
        alias.previous_generation = from_generation
        alias.generation = to_generation
        alias.swapped_at = now
        alias.save(update_fields=["previous_generation", "generation", "swapped_at"])
    else:
        alias = IndexAlias.objects.create(
            index_family=index_family,
            generation=to_generation,
            previous_generation=None,
            swapped_at=now,
        )

    # 4. Emit index.generation.promoted.v1 in same transaction
    event_id = mint_id("evc")
    EventOutbox.objects.create(
        id=event_id,
        source="p2/indexer@0.1.0|det_v1",
        type="index.generation.promoted.v1",
        time=now,
        subject=f"{index_family}/{to_generation}",
        datacontenttype="application/json",
        dataschema="https://lawyerbrain.in/schemas/index.generation.promoted.v1.json",
        tenantid=None,
        dataclass="PUBLIC",
        idempotencykey=f"p2|promote|{index_family}|{to_generation}|{int(now.timestamp())}",
        schemaversion="1.0",
        data={
            "index_family": index_family,
            "from_generation": from_generation,
            "to_generation": to_generation,
            "eval_report_uri": eval_report_uri,
            "gate_decision_id": gate_decision_id,
            "promoted_at": now.isoformat(),
            "rollback_deadline": rollback_deadline.isoformat(),
            "rolled_back_from": None,
            "reason": reason,
        },
        topic="plc.index.generation.promoted.v1",
        partition_key=index_family,
        lane="rt",
    )

    return alias


@transaction.atomic
def rollback_generation(index_family: str) -> IndexAlias:
    """Atomically rollback alias to previous generation and emit promotion event."""
    alias = IndexAlias.objects.select_for_update().filter(index_family=index_family).first()
    if not alias or not alias.previous_generation:
        raise RuntimeError(
            f"No previous generation available to rollback to for family '{index_family}'."
        )

    target_gen_id = alias.previous_generation
    current_gen_id = alias.generation

    now = timezone.now()

    # Mark current generation as ROLLED_BACK
    IndexGeneration.objects.filter(index_family=index_family, generation=current_gen_id).update(
        state="ROLLED_BACK"
    )

    # Mark restored generation as LIVE
    IndexGeneration.objects.filter(index_family=index_family, generation=target_gen_id).update(
        state="LIVE", promoted_at=now
    )

    # Swap alias
    alias.generation = target_gen_id
    alias.previous_generation = current_gen_id
    alias.swapped_at = now
    alias.save(update_fields=["generation", "previous_generation", "swapped_at"])

    # Emit event
    event_id = mint_id("evc")
    EventOutbox.objects.create(
        id=event_id,
        source="p2/indexer@0.1.0|det_v1",
        type="index.generation.promoted.v1",
        time=now,
        subject=f"{index_family}/{target_gen_id}",
        datacontenttype="application/json",
        dataschema="https://lawyerbrain.in/schemas/index.generation.promoted.v1.json",
        tenantid=None,
        dataclass="PUBLIC",
        idempotencykey=f"p2|rollback|{index_family}|{target_gen_id}|{int(now.timestamp())}",
        schemaversion="1.0",
        data={
            "index_family": index_family,
            "from_generation": current_gen_id,
            "to_generation": target_gen_id,
            "eval_report_uri": None,
            "gate_decision_id": None,
            "promoted_at": now.isoformat(),
            "rollback_deadline": now.isoformat(),
            "rolled_back_from": current_gen_id,
            "reason": "ROLLBACK",
        },
        topic="plc.index.generation.promoted.v1",
        partition_key=index_family,
        lane="rt",
    )

    return alias
