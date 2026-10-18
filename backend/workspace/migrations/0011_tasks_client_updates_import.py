"""Migration 0011: Tasks, Client Updates, Share Links, and Case Imports (Session R3).

Normative sources:
- Session R3 specification & review approvals:
  1. tpl.task: prefixed tsk_, matter-scoped, composite FKs to hearing, deadline, app_user.
  2. tpl.client_update: prefixed cup_, immutable snapshot (no DRAFT status, update/delete forbidden).
  3. tpl.share_link: prefixed shl_, token hash stored, unique unrevoked per matter.
  4. ops.share_link_access: view log & rate limiting per IP and link, accessed only by share_reader.
  5. tpl.import_job: prefixed imj_, import history, mappings, overrides, report.
  6. Security: share_reader role owns tpl.get_public_share_update; worker access revoked.
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
-- 1. Tasks table (tpl.task)
CREATE TABLE tpl.task (
  tenant_id text NOT NULL REFERENCES tpl.tenant(tenant_id),
  task_id text NOT NULL,
  matter_id text NOT NULL,
  title text NOT NULL,
  notes text,
  assignee text NOT NULL,
  due_on date,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'DONE', 'CANCELLED')),
  hearing_id text,
  deadline_id text,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  done_by text,
  done_at timestamptz,
  PRIMARY KEY (tenant_id, task_id),
  CONSTRAINT fk_task_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id),
  CONSTRAINT fk_task_hearing FOREIGN KEY (tenant_id, hearing_id) REFERENCES tpl.hearing(tenant_id, hearing_id),
  CONSTRAINT fk_task_deadline FOREIGN KEY (tenant_id, deadline_id) REFERENCES tpl.deadline(tenant_id, deadline_id),
  CONSTRAINT fk_task_assignee FOREIGN KEY (tenant_id, assignee) REFERENCES tpl.app_user(tenant_id, user_id),
  CONSTRAINT chk_task_link_mutual_exclusive CHECK (hearing_id IS NULL OR deadline_id IS NULL)
);

CREATE INDEX idx_task_matter_status ON tpl.task (tenant_id, matter_id, status);
CREATE INDEX idx_task_assignee_due ON tpl.task (tenant_id, assignee, due_on);

-- 2. Client Updates table (tpl.client_update)
-- Holds published snapshots only (no DRAFT status; drafts generated deterministically)
CREATE TABLE tpl.client_update (
  tenant_id text NOT NULL REFERENCES tpl.tenant(tenant_id),
  update_id text NOT NULL,
  matter_id text NOT NULL,
  text text NOT NULL,
  facts jsonb NOT NULL DEFAULT '{}',
  published_by text NOT NULL,
  published_at timestamptz NOT NULL,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, update_id),
  CONSTRAINT fk_client_update_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id)
);

CREATE INDEX idx_client_update_matter_pub ON tpl.client_update (tenant_id, matter_id, published_at DESC);

-- Immutable trigger on tpl.client_update
CREATE OR REPLACE FUNCTION tpl.prevent_client_update_update_or_delete()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'tpl.client_update is immutable; UPDATE and DELETE are strictly forbidden.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS client_update_immutable ON tpl.client_update;
CREATE TRIGGER client_update_immutable
BEFORE UPDATE OR DELETE ON tpl.client_update
FOR EACH ROW EXECUTE FUNCTION tpl.prevent_client_update_update_or_delete();

-- 3. Share Link table (tpl.share_link)
CREATE TABLE tpl.share_link (
  tenant_id text NOT NULL REFERENCES tpl.tenant(tenant_id),
  link_id text NOT NULL,
  matter_id text NOT NULL,
  token_hash text NOT NULL UNIQUE,
  client_matter_title text NOT NULL,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  revoked_by text,
  PRIMARY KEY (tenant_id, link_id),
  CONSTRAINT fk_share_link_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id)
);

CREATE UNIQUE INDEX idx_share_link_active_matter ON tpl.share_link (tenant_id, matter_id) WHERE revoked_at IS NULL;

-- 4. Share Link Access & Rate Limiting table (ops.share_link_access)
CREATE TABLE ops.share_link_access (
  access_id bigserial PRIMARY KEY,
  link_id text,
  tenant_id text,
  ip_hash text NOT NULL,
  accessed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE INDEX idx_share_link_access_ip ON ops.share_link_access (ip_hash, accessed_at);
CREATE INDEX idx_share_link_access_link ON ops.share_link_access (link_id, accessed_at);

-- 5. Case Import Job table (tpl.import_job)
CREATE TABLE tpl.import_job (
  tenant_id text NOT NULL REFERENCES tpl.tenant(tenant_id),
  import_id text NOT NULL,
  filename text NOT NULL,
  file_size int NOT NULL,
  row_count int NOT NULL,
  status text NOT NULL DEFAULT 'PREVIEW' CHECK (status IN ('PREVIEW', 'COMMITTED', 'FAILED')),
  sha256 text NOT NULL,
  mapping jsonb NOT NULL DEFAULT '{}',
  client_overrides jsonb NOT NULL DEFAULT '{}',
  counts jsonb NOT NULL DEFAULT '{}',
  report jsonb NOT NULL DEFAULT '[]',
  file_ref text NOT NULL,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  committed_at timestamptz,
  committed_by text,
  PRIMARY KEY (tenant_id, import_id)
);

CREATE INDEX idx_import_job_tenant_sha256 ON tpl.import_job (tenant_id, sha256);
CREATE INDEX idx_import_job_tenant_created ON tpl.import_job (tenant_id, created_at DESC);

-- 6. Row-Level Security: Enable and FORCE
ALTER TABLE tpl.task ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.task FORCE ROW LEVEL SECURITY;
CREATE POLICY task_isolation ON tpl.task
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.client_update ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.client_update FORCE ROW LEVEL SECURITY;
CREATE POLICY client_update_isolation ON tpl.client_update
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.share_link ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.share_link FORCE ROW LEVEL SECURITY;
CREATE POLICY share_link_isolation ON tpl.share_link
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.import_job ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.import_job FORCE ROW LEVEL SECURITY;
CREATE POLICY import_job_isolation ON tpl.import_job
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 7. Role share_reader and column-level security
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'share_reader') THEN
    CREATE ROLE share_reader NOLOGIN NOBYPASSRLS;
  END IF;
END $$;

GRANT USAGE ON SCHEMA tpl, ops TO share_reader;

GRANT SELECT (link_id, tenant_id, matter_id, client_matter_title, token_hash, expires_at, revoked_at)
  ON tpl.share_link TO share_reader;

GRANT SELECT (update_id, text, published_at, tenant_id, matter_id)
  ON tpl.client_update TO share_reader;

GRANT SELECT (tenant_id, name)
  ON tpl.tenant TO share_reader;

CREATE POLICY share_reader_share_link ON tpl.share_link FOR SELECT TO share_reader USING (true);
CREATE POLICY share_reader_client_update ON tpl.client_update FOR SELECT TO share_reader USING (true);
CREATE POLICY share_reader_tenant ON tpl.tenant FOR SELECT TO share_reader USING (true);

REVOKE ALL ON ops.share_link_access FROM app_rw, worker;
GRANT SELECT, INSERT, DELETE ON ops.share_link_access TO share_reader;
GRANT USAGE, SELECT ON SEQUENCE ops.share_link_access_access_id_seq TO share_reader;

-- 8. SECURITY DEFINER function for public share resolution with Postgres sliding-window rate limiting
CREATE OR REPLACE FUNCTION tpl.get_public_share_update(
  p_token_hash text,
  p_ip_hash text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, tpl, ops
AS $$
DECLARE
  v_link record;
  v_firm_name text;
  v_updates jsonb;
  v_recent_ip_count int;
  v_recent_link_count int;
BEGIN
  -- Housekeeping: delete rate-limiting rows older than 1 day
  DELETE FROM ops.share_link_access WHERE accessed_at < clock_timestamp() - interval '1 day';

  -- Rate limit per IP: max 30 req/min
  SELECT count(*) INTO v_recent_ip_count
  FROM ops.share_link_access
  WHERE ip_hash = p_ip_hash AND accessed_at > clock_timestamp() - interval '1 minute';
  IF v_recent_ip_count >= 30 THEN
    RETURN jsonb_build_object('error', 'RATE_LIMITED');
  END IF;

  -- Lookup active, unexpired, unrevoked share link
  SELECT link_id, tenant_id, matter_id, client_matter_title
  INTO v_link
  FROM tpl.share_link
  WHERE token_hash = p_token_hash
    AND revoked_at IS NULL
    AND expires_at > clock_timestamp();

  IF NOT FOUND THEN
    -- Audit attempt with unknown/invalid link (link_id NULL)
    INSERT INTO ops.share_link_access (link_id, tenant_id, ip_hash) VALUES (NULL, NULL, p_ip_hash);
    RETURN NULL;
  END IF;

  -- Rate limit per link: max 60 req/min
  SELECT count(*) INTO v_recent_link_count
  FROM ops.share_link_access
  WHERE link_id = v_link.link_id AND accessed_at > clock_timestamp() - interval '1 minute';
  IF v_recent_link_count >= 60 THEN
    RETURN jsonb_build_object('error', 'RATE_LIMITED');
  END IF;

  -- Audit valid view in ops.share_link_access
  INSERT INTO ops.share_link_access (link_id, tenant_id, ip_hash)
  VALUES (v_link.link_id, v_link.tenant_id, p_ip_hash);

  -- Retrieve firm name
  SELECT name INTO v_firm_name FROM tpl.tenant WHERE tenant_id = v_link.tenant_id;

  -- Retrieve published updates newest first (strictly text and published_at only, no facts)
  SELECT COALESCE(jsonb_agg(
    jsonb_build_object(
      'update_id', update_id,
      'text', text,
      'published_at', published_at
    ) ORDER BY published_at DESC
  ), '[]'::jsonb)
  INTO v_updates
  FROM tpl.client_update
  WHERE tenant_id = v_link.tenant_id
    AND matter_id = v_link.matter_id;

  -- Return tenant_id and link_id for server-side audit event recording (never rendered to client)
  RETURN jsonb_build_object(
    'tenant_id', v_link.tenant_id,
    'link_id', v_link.link_id,
    'firm_name', v_firm_name,
    'client_matter_title', v_link.client_matter_title,
    'updates', v_updates
  );
END;
$$;

ALTER FUNCTION tpl.get_public_share_update(text, text) OWNER TO share_reader;
REVOKE EXECUTE ON FUNCTION tpl.get_public_share_update(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tpl.get_public_share_update(text, text) TO app_rw;

-- 9. Explicit grants: revoke worker, restrict app_rw
REVOKE ALL ON tpl.task FROM worker;
REVOKE ALL ON tpl.client_update FROM worker;
REVOKE ALL ON tpl.share_link FROM worker;
REVOKE ALL ON tpl.import_job FROM worker;

GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.task TO app_rw;
GRANT SELECT, INSERT ON tpl.client_update TO app_rw;
REVOKE UPDATE, DELETE ON tpl.client_update FROM app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.share_link TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.import_job TO app_rw;
"""

SQL_REVERSE = """
REVOKE EXECUTE ON FUNCTION tpl.get_public_share_update(text, text) FROM app_rw;
DROP FUNCTION IF EXISTS tpl.get_public_share_update(text, text);

DROP POLICY IF EXISTS share_reader_tenant ON tpl.tenant;
DROP POLICY IF EXISTS share_reader_client_update ON tpl.client_update;
DROP POLICY IF EXISTS share_reader_share_link ON tpl.share_link;

DROP POLICY IF EXISTS import_job_isolation ON tpl.import_job;
DROP POLICY IF EXISTS share_link_isolation ON tpl.share_link;
DROP POLICY IF EXISTS client_update_isolation ON tpl.client_update;
DROP POLICY IF EXISTS task_isolation ON tpl.task;

DROP TRIGGER IF EXISTS client_update_immutable ON tpl.client_update;
DROP FUNCTION IF EXISTS tpl.prevent_client_update_update_or_delete();

DROP TABLE IF EXISTS tpl.import_job CASCADE;
DROP TABLE IF EXISTS ops.share_link_access CASCADE;
DROP TABLE IF EXISTS tpl.share_link CASCADE;
DROP TABLE IF EXISTS tpl.client_update CASCADE;
DROP TABLE IF EXISTS tpl.task CASCADE;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0010_reapply_can_read_matter_security"),
    ]

    operations = [
        migrations.RunSQL(SQL_FORWARD, SQL_REVERSE),
    ]
