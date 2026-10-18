"""Migration 0010: Re-apply can_read_matter and tenant policy security hardening.

Normative source:
- Session R3 Correction 1: Re-apply corrected can_read_matter and tenant_isolation
  from 0007 in a forward migration so existing databases cleanly receive the hardening
  restricting background sync access strictly to SESSION_USER = 'worker'.
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
-- 1. Re-apply tpl.can_read_matter: system background actors/purposes are ONLY usable
-- by worker DB role (SESSION_USER = 'worker'),
-- and NEVER settable or effective from an app-role (app_rw) or admin-role (admin_rw) session.
CREATE OR REPLACE FUNCTION tpl.can_read_matter(m_id text, u_id text)
RETURNS boolean AS $$
BEGIN
  -- System actor or system background sync purpose: ONLY valid for worker DB role
  IF SESSION_USER = 'worker' THEN
    IF COALESCE(current_setting('app.purpose', true), '') IN ('CAUSELIST_SYNC', 'ORDER_SYNC') OR u_id LIKE 'system:%' THEN
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

-- 2. Update tenant policy: background sync purpose bypass ONLY applies to worker DB roles
DROP POLICY IF EXISTS tenant_isolation ON tpl.tenant;
CREATE POLICY tenant_isolation ON tpl.tenant
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    OR (
      SESSION_USER = 'worker'
      AND COALESCE(current_setting('app.purpose', true), '') IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    )
  )
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

-- 3. Document vault policies: system background actors NEVER have access to read or write documents
DROP POLICY IF EXISTS pdoc_isolation ON tpl.pdoc;
CREATE POLICY pdoc_isolation ON tpl.pdoc
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND COALESCE(NULLIF(current_setting('app.user_id', true), ''), '') NOT LIKE 'system:%'
    AND COALESCE(current_setting('app.purpose', true), '') NOT IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND COALESCE(NULLIF(current_setting('app.user_id', true), ''), '') NOT LIKE 'system:%'
    AND COALESCE(current_setting('app.purpose', true), '') NOT IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

DROP POLICY IF EXISTS pdoc_version_isolation ON tpl.pdoc_version;
CREATE POLICY pdoc_version_isolation ON tpl.pdoc_version
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND COALESCE(NULLIF(current_setting('app.user_id', true), ''), '') NOT LIKE 'system:%'
    AND COALESCE(current_setting('app.purpose', true), '') NOT IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.pdoc_version.tenant_id
        AND p.pdoc_id = tpl.pdoc_version.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND COALESCE(NULLIF(current_setting('app.user_id', true), ''), '') NOT LIKE 'system:%'
    AND COALESCE(current_setting('app.purpose', true), '') NOT IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.pdoc_version.tenant_id
        AND p.pdoc_id = tpl.pdoc_version.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  );

DROP POLICY IF EXISTS private_anchor_isolation ON tpl.private_anchor;
CREATE POLICY private_anchor_isolation ON tpl.private_anchor
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND COALESCE(NULLIF(current_setting('app.user_id', true), ''), '') NOT LIKE 'system:%'
    AND COALESCE(current_setting('app.purpose', true), '') NOT IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.private_anchor.tenant_id
        AND p.pdoc_id = tpl.private_anchor.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND COALESCE(NULLIF(current_setting('app.user_id', true), ''), '') NOT LIKE 'system:%'
    AND COALESCE(current_setting('app.purpose', true), '') NOT IN ('CAUSELIST_SYNC', 'ORDER_SYNC')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.private_anchor.tenant_id
        AND p.pdoc_id = tpl.private_anchor.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  );
"""

SQL_REVERSE = """
-- No-op reverse preserves functioning can_read_matter
"""


class Migration(migrations.Migration):

    dependencies = [
        ("workspace", "0009_hearing_outcome"),
    ]

    operations = [
        migrations.RunSQL(SQL_FORWARD, SQL_REVERSE),
    ]
