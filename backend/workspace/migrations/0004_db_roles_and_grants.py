"""Migration 0004: Create admin_rw role (NOLOGIN, no password) and grant cross-role permissions.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §1 item 1: DB roles
- Session S03 follow-up: Move admin_rw to dedicated roles migration, create without password,
  grant app_rw to worker for tenant-scoped jobs, and configure default privileges.
"""

from django.db import migrations

SQL_FORWARD = """
-- 1. Ensure admin_rw role exists with BYPASSRLS and NOLOGIN (no password hardcoded)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin_rw') THEN
    CREATE ROLE admin_rw NOLOGIN NOINHERIT BYPASSRLS;
  ELSE
    ALTER ROLE admin_rw NOINHERIT BYPASSRLS;
  END IF;
END $$;

-- 2. Grant permissions on schemas tpl, plc, ops, public to admin_rw
GRANT USAGE ON SCHEMA tpl, plc, ops, public TO admin_rw;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tpl, plc, ops, public TO admin_rw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tpl, plc, ops, public TO admin_rw;

-- 3. Configure default privileges for future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA tpl, plc, ops, public GRANT ALL PRIVILEGES ON TABLES TO admin_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA tpl, plc, ops, public GRANT ALL PRIVILEGES ON SEQUENCES TO admin_rw;

-- 4. Permissions and default privileges for app_rw and worker
GRANT USAGE ON SCHEMA tpl, plc, ops, public TO app_rw, worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tpl, ops, public TO app_rw, worker;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tpl, plc, ops, public TO app_rw, worker;
GRANT SELECT ON ALL TABLES IN SCHEMA plc TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA plc TO worker;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, tpl, ops GRANT ALL PRIVILEGES ON TABLES TO app_rw, worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA public, tpl, ops, plc GRANT ALL PRIVILEGES ON SEQUENCES TO app_rw, worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA plc GRANT SELECT ON TABLES TO app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA plc GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO worker;

-- 5. Grant app_rw to worker so worker can execute SET LOCAL ROLE app_rw for tenant-scoped jobs
GRANT app_rw TO worker;

-- 6. Security definer function for safe walled status check under RLS
CREATE OR REPLACE FUNCTION tpl.is_matter_walled(m_id text)
RETURNS boolean AS $$
DECLARE
  v_walled boolean;
BEGIN
  SELECT walled INTO v_walled
  FROM tpl.matter
  WHERE matter_id = m_id AND tenant_id = NULLIF(current_setting('app.tenant_id', true), '');
  RETURN COALESCE(v_walled, false);
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, tpl;

GRANT EXECUTE ON FUNCTION tpl.is_matter_walled(text) TO app_rw, worker, admin_rw;
"""

SQL_REVERSE = """
DROP FUNCTION IF EXISTS tpl.is_matter_walled(text);
REVOKE app_rw FROM worker;
DROP OWNED BY admin_rw;
DROP ROLE IF EXISTS admin_rw;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0003_audit_chain_head_and_seq"),
        ("sessions", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("procrastinate", "0041_post_retry_failed_job"),
        ("ops", "0002_initial_ops_tables"),
        ("gateway", "0001_initial_gateway_tables"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
