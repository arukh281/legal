"""Migration adding tpl.audit_chain_head, seq column on audit_event, and admin_rw role.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1, §3.8
- Session S03 follow-up directives: O(1) audit chain head, verify_chain(tenant), admin_rw role
"""

from django.db import migrations

SQL_FORWARD = """
-- 1. Add monotonic seq column on tpl.audit_event
ALTER TABLE tpl.audit_event ADD COLUMN IF NOT EXISTS seq bigint NOT NULL DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_audit_event_tenant_seq ON tpl.audit_event (tenant_id, seq DESC);

-- 2. Dedicated per-tenant chain-head table for O(1) audit log appends under advisory lock
CREATE TABLE IF NOT EXISTS tpl.audit_chain_head (
  tenant_id text PRIMARY KEY,
  latest_audit_id text NOT NULL,
  latest_hash bytea NOT NULL,
  seq bigint NOT NULL,
  updated_at timestamptz NOT NULL
);

ALTER TABLE tpl.audit_chain_head ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.audit_chain_head FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS audit_chain_head_isolation ON tpl.audit_chain_head;
CREATE POLICY audit_chain_head_isolation ON tpl.audit_chain_head
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

GRANT SELECT, INSERT, UPDATE ON tpl.audit_chain_head TO app_rw, worker;
"""

SQL_REVERSE = """
DROP POLICY IF EXISTS audit_chain_head_isolation ON tpl.audit_chain_head;
DROP TABLE IF EXISTS tpl.audit_chain_head CASCADE;
DROP INDEX IF EXISTS tpl.idx_audit_event_tenant_seq;
ALTER TABLE tpl.audit_event DROP COLUMN IF EXISTS seq;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0002_db_roles_and_rls"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
