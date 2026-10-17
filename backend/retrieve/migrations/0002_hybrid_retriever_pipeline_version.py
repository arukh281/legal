"""Migration 0002: Seed p5.retriever@0.1.0|hybrid_rrf_v1 for hybrid retrieval.

Normative source:
- docs/07_P5_retrieval_fusion.md §5.7 (RRF fusion of lexical + dense)
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
INSERT INTO ops.pipeline_version (
  pipeline_version, component, semver, model_id, model_snapshot, endpoint_region, prompt_hash, code_sha, created_at
) VALUES (
  'p5.retriever@0.1.0|hybrid_rrf_v1', 'p5.retriever', '0.1.0', NULL, NULL, NULL, NULL, 'git-s09-step5', now()
) ON CONFLICT (pipeline_version) DO NOTHING;
"""

SQL_REVERSE = """
DELETE FROM ops.pipeline_version WHERE pipeline_version = 'p5.retriever@0.1.0|hybrid_rrf_v1';
"""


class Migration(migrations.Migration):
    dependencies = [
        ("retrieve", "0001_initial_retrieve_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
