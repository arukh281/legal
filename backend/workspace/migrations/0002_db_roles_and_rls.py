"""Migration 0002: DB roles, FORCE ROW LEVEL SECURITY, and append-only audit enforcement."""

from django.db import migrations

SQL_FORWARD = """
-- 1. Create DB roles if they do not already exist
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'plc_writer') THEN
    CREATE ROLE plc_writer;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') THEN
    CREATE ROLE app_rw NOBYPASSRLS;
  ELSE
    ALTER ROLE app_rw NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'worker') THEN
    CREATE ROLE worker BYPASSRLS;
  ELSE
    ALTER ROLE worker BYPASSRLS;
  END IF;
END $$;

-- 2. Schema and table grants per 03 §1
-- plc_writer: reads and writes plc; strictly forbidden from reading tpl
GRANT USAGE ON SCHEMA plc TO plc_writer;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA plc TO plc_writer;
REVOKE ALL ON SCHEMA tpl FROM plc_writer;
REVOKE ALL ON ALL TABLES IN SCHEMA tpl FROM plc_writer;

-- app_rw: reads plc; reads/writes tpl under RLS; reads/writes ops
GRANT USAGE ON SCHEMA plc, tpl, ops TO app_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA plc TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tpl TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ops TO app_rw;

-- worker: reads/writes plc, tpl, ops with BYPASSRLS
GRANT USAGE ON SCHEMA plc, tpl, ops TO worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA plc, tpl, ops TO worker;

-- 3. Security definer function for matter read access (Directive 5: STABLE, search_path locked down)
CREATE OR REPLACE FUNCTION tpl.can_read_matter(m_id text, u_id text)
RETURNS boolean AS $$
BEGIN
  IF u_id IS NULL OR u_id = '' THEN
    RETURN false;
  END IF;

  -- 1. Ethical wall exclusion: deny-first
  IF EXISTS (
    SELECT 1 FROM tpl.wall_exclusion we
    JOIN tpl.ethical_wall ew ON ew.tenant_id = we.tenant_id AND ew.wall_id = we.wall_id
    WHERE ew.matter_id = m_id AND we.user_id = u_id
  ) THEN
    RETURN false;
  END IF;

  -- 2. Active matter membership
  IF EXISTS (
    SELECT 1 FROM tpl.matter_member mm
    WHERE mm.matter_id = m_id AND mm.user_id = u_id AND mm.revoked_at IS NULL
  ) THEN
    RETURN true;
  END IF;

  -- 3. Firm ADMIN can view non-walled matters
  IF EXISTS (
    SELECT 1 FROM tpl.app_user u
    JOIN tpl.matter m ON m.tenant_id = u.tenant_id AND m.matter_id = m_id
    WHERE u.user_id = u_id AND u.firm_role = 'ADMIN' AND m.walled = false
  ) THEN
    RETURN true;
  END IF;

  RETURN false;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, tpl;

-- 4. Enable and FORCE Row Level Security on all tpl tables
ALTER TABLE tpl.tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.tenant FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tpl.tenant
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.app_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.app_user FORCE ROW LEVEL SECURITY;
CREATE POLICY app_user_isolation ON tpl.app_user
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.matter ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter FORCE ROW LEVEL SECURITY;
CREATE POLICY matter_isolation ON tpl.matter
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.matter_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter_member FORCE ROW LEVEL SECURITY;
CREATE POLICY matter_member_isolation ON tpl.matter_member
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.ethical_wall ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.ethical_wall FORCE ROW LEVEL SECURITY;
CREATE POLICY ethical_wall_isolation ON tpl.ethical_wall
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.wall_exclusion ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.wall_exclusion FORCE ROW LEVEL SECURITY;
CREATE POLICY wall_exclusion_isolation ON tpl.wall_exclusion
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.actor_pseudonym ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.actor_pseudonym FORCE ROW LEVEL SECURITY;
CREATE POLICY actor_pseudonym_isolation ON tpl.actor_pseudonym
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.consent_record ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.consent_record FORCE ROW LEVEL SECURITY;
CREATE POLICY consent_record_isolation ON tpl.consent_record
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.audit_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.audit_event FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_event_isolation ON tpl.audit_event
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 5. Audit Log append-only enforcement (Directive 6)
REVOKE UPDATE, DELETE ON tpl.audit_event FROM app_rw, worker;

CREATE OR REPLACE FUNCTION tpl.prevent_audit_update_or_delete()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'tpl.audit_event is append-only; UPDATE and DELETE are strictly forbidden.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_event_append_only ON tpl.audit_event;
CREATE TRIGGER audit_event_append_only
BEFORE UPDATE OR DELETE ON tpl.audit_event
FOR EACH ROW EXECUTE FUNCTION tpl.prevent_audit_update_or_delete();
"""

SQL_REVERSE = """
DROP TRIGGER IF EXISTS audit_event_append_only ON tpl.audit_event;
DROP FUNCTION IF EXISTS tpl.prevent_audit_update_or_delete();

DROP POLICY IF EXISTS audit_event_isolation ON tpl.audit_event;
DROP POLICY IF EXISTS consent_record_isolation ON tpl.consent_record;
DROP POLICY IF EXISTS actor_pseudonym_isolation ON tpl.actor_pseudonym;
DROP POLICY IF EXISTS wall_exclusion_isolation ON tpl.wall_exclusion;
DROP POLICY IF EXISTS ethical_wall_isolation ON tpl.ethical_wall;
DROP POLICY IF EXISTS matter_member_isolation ON tpl.matter_member;
DROP POLICY IF EXISTS matter_isolation ON tpl.matter;
DROP POLICY IF EXISTS app_user_isolation ON tpl.app_user;
DROP POLICY IF EXISTS tenant_isolation ON tpl.tenant;

ALTER TABLE tpl.audit_event NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.audit_event DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.consent_record NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.consent_record DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.actor_pseudonym NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.actor_pseudonym DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.wall_exclusion NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.wall_exclusion DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.ethical_wall NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.ethical_wall DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter_member NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter_member DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.app_user NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.app_user DISABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.tenant NO FORCE ROW LEVEL SECURITY;
ALTER TABLE tpl.tenant DISABLE ROW LEVEL SECURITY;

DROP FUNCTION IF EXISTS tpl.can_read_matter(text, text);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0001_initial_tpl_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
