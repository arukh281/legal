"""Migration 0007: Update can_read_matter and tenant policy for system background actors.

Normative sources:
- Session R2: hearings, dates and Today (User Correction 5:
  'The consumer must loop tenant by tenant with the tenant context set and the purpose logged,
   not read every tenant's case links in one query. Audit system writes with actor system:causelist.')
- docs/mvp/03_data_model_and_contracts.md §1
"""

from django.db import migrations

SQL_FORWARD = """
-- 1. Update tpl.can_read_matter to support system actors and background sync purposes
CREATE OR REPLACE FUNCTION tpl.can_read_matter(m_id text, u_id text)
RETURNS boolean AS $$
BEGIN
  -- System actor or system background sync purpose
  IF current_setting('app.purpose', true) IN ('CAUSELIST_SYNC', 'ORDER_SYNC') OR u_id LIKE 'system:%' THEN
    -- Ethical wall exclusion: deny-first even for system
    IF u_id IS NOT NULL AND u_id != '' AND EXISTS (
      SELECT 1 FROM tpl.wall_exclusion we
      JOIN tpl.ethical_wall ew ON ew.tenant_id = we.tenant_id AND ew.wall_id = we.wall_id
      WHERE ew.matter_id = m_id AND we.user_id = u_id
    ) THEN
      RETURN false;
    END IF;
    RETURN true;
  END IF;

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

-- 2. Update tenant policy to allow tenant discovery during system sync purposes
DROP POLICY IF EXISTS tenant_isolation ON tpl.tenant;
CREATE POLICY tenant_isolation ON tpl.tenant
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    OR current_setting('app.purpose', true) IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
  )
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));
"""

SQL_REVERSE = """
CREATE OR REPLACE FUNCTION tpl.can_read_matter(m_id text, u_id text)
RETURNS boolean AS $$
BEGIN
  IF u_id IS NULL OR u_id = '' THEN
    RETURN false;
  END IF;

  IF EXISTS (
    SELECT 1 FROM tpl.wall_exclusion we
    JOIN tpl.ethical_wall ew ON ew.tenant_id = we.tenant_id AND ew.wall_id = we.wall_id
    WHERE ew.matter_id = m_id AND we.user_id = u_id
  ) THEN
    RETURN false;
  END IF;

  IF EXISTS (
    SELECT 1 FROM tpl.matter_member mm
    WHERE mm.matter_id = m_id AND mm.user_id = u_id AND mm.revoked_at IS NULL
  ) THEN
    RETURN true;
  END IF;

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

DROP POLICY IF EXISTS tenant_isolation ON tpl.tenant;
CREATE POLICY tenant_isolation ON tpl.tenant
  USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''))
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));
"""


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0006_hearings_deadlines_candidates"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
