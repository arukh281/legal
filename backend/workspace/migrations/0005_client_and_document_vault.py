"""Migration 0005: Client entity, matter extensions, and document vault (P7).

Normative sources:
- Session R1: the client file (clients, matters, document vault)
- docs/mvp/03_data_model_and_contracts.md §3.8, §3.9, §6
- DECISIONS.md (2026-10-17: tpl.client, cli prefix, stage tag, client visibility)
"""

from django.db import migrations

SQL_FORWARD = """
-- 1. Client table (tpl.client)
CREATE TABLE tpl.client (
  tenant_id text NOT NULL REFERENCES tpl.tenant,
  client_id text NOT NULL,
  display_name text NOT NULL,
  client_type text NOT NULL CHECK (client_type IN ('INDIVIDUAL', 'COMPANY', 'LLP', 'PARTNERSHIP', 'GOVERNMENT', 'OTHER')),
  identifiers jsonb NOT NULL DEFAULT '{}',
  contact jsonb NOT NULL DEFAULT '{}',
  notes text,
  status text NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ARCHIVED')),
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, client_id)
);

-- 2. Matter extensions
ALTER TABLE tpl.matter ADD COLUMN IF NOT EXISTS client_id text;
ALTER TABLE tpl.matter ADD COLUMN IF NOT EXISTS case_type text;
ALTER TABLE tpl.matter ADD COLUMN IF NOT EXISTS court_or_forum text;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'matter_client_fk'
  ) THEN
    ALTER TABLE tpl.matter
      ADD CONSTRAINT matter_client_fk
      FOREIGN KEY (tenant_id, client_id)
      REFERENCES tpl.client(tenant_id, client_id);
  END IF;
END $$;

-- 3. Matter case links (tpl.matter_case_link)
CREATE TABLE tpl.matter_case_link (
  tenant_id text NOT NULL,
  matter_id text NOT NULL,
  case_id text,
  scheme text NOT NULL,
  value_normalized text NOT NULL,
  role text NOT NULL DEFAULT 'CASE',
  track boolean NOT NULL DEFAULT true,
  PRIMARY KEY (tenant_id, matter_id, scheme, value_normalized)
);

-- 4. Document vault: pdoc, pdoc_version, private_anchor
CREATE TABLE tpl.pdoc (
  tenant_id text NOT NULL,
  matter_id text NOT NULL,
  pdoc_id text NOT NULL,
  family_id text,
  parent_pdoc_id text,
  doc_type text NOT NULL,
  provenance text NOT NULL,
  trust_label text NOT NULL CHECK (trust_label IN ('TENANT_CLIENT_DOC','TENANT_OPPOSING_DOC','TENANT_CORRESPONDENCE','TENANT_WORK_PRODUCT','TENANT_COURT_RECORD')),
  privilege_class text NOT NULL,
  privilege_state text NOT NULL DEFAULT 'SUGGESTED',
  stage text NOT NULL DEFAULT 'OTHER' CHECK (stage IN ('NOTICE','PLEADING','REPLY','ORDER','CORRESPONDENCE','EVIDENCE','DRAFT','OTHER')),
  title text,
  doc_date date,
  received_on date,
  current_version text,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  tombstoned_at timestamptz,
  PRIMARY KEY (tenant_id, pdoc_id)
);

CREATE TABLE tpl.pdoc_version (
  tenant_id text NOT NULL,
  pdoc_id text NOT NULL,
  pver text NOT NULL CHECK (pver ~ '^v[1-9][0-9]*$'),
  raw_sha256 text NOT NULL,
  storage_uri text NOT NULL,
  mime text,
  parsed_doc_uri text,
  quality jsonb,
  gate text CHECK (gate IN ('PASS','FLAGGED','QUARANTINED')),
  pipeline_version text REFERENCES ops.pipeline_version,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, pdoc_id, pver)
);

CREATE TABLE tpl.private_anchor (
  tenant_id text NOT NULL,
  anchor_id private_anchor_ref NOT NULL,
  pdoc_id text NOT NULL,
  pver text NOT NULL,
  rendition text CHECK (rendition IS NULL OR rendition LIKE 'ht-%'),
  fragment text NOT NULL,
  text text NOT NULL,
  text_hash text NOT NULL,
  quote_prefix text,
  quote_suffix text,
  spans jsonb NOT NULL DEFAULT '[]',
  ocr_conf real,
  privilege_class text NOT NULL,
  PRIMARY KEY (tenant_id, anchor_id)
);

-- 5. Security definer function for client read access
CREATE OR REPLACE FUNCTION tpl.can_read_client(c_id text, u_id text)
RETURNS boolean AS $$
BEGIN
  IF u_id IS NULL OR u_id = '' THEN
    RETURN false;
  END IF;

  -- 1. Firm ADMIN can view any client in the tenant
  IF EXISTS (
    SELECT 1 FROM tpl.app_user u
    WHERE u.user_id = u_id AND u.firm_role = 'ADMIN'
      AND u.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
      AND u.active = true
  ) THEN
    RETURN true;
  END IF;

  -- 2. Creator of the client can view it
  IF EXISTS (
    SELECT 1 FROM tpl.client c
    WHERE c.client_id = c_id
      AND c.created_by = u_id
      AND c.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
  ) THEN
    RETURN true;
  END IF;

  -- 3. Active member of at least one readable matter under this client
  IF EXISTS (
    SELECT 1 FROM tpl.matter m
    WHERE m.client_id = c_id
      AND m.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
      AND tpl.can_read_matter(m.matter_id, u_id)
  ) THEN
    RETURN true;
  END IF;

  RETURN false;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog, tpl;

-- 6. Enable and FORCE Row Level Security on new tpl tables
ALTER TABLE tpl.client ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.client FORCE ROW LEVEL SECURITY;
CREATE POLICY client_isolation ON tpl.client
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_client(client_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), ''));

ALTER TABLE tpl.matter_case_link ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter_case_link FORCE ROW LEVEL SECURITY;
CREATE POLICY matter_case_link_isolation ON tpl.matter_case_link
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.pdoc ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.pdoc FORCE ROW LEVEL SECURITY;
CREATE POLICY pdoc_isolation ON tpl.pdoc
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.pdoc_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.pdoc_version FORCE ROW LEVEL SECURITY;
CREATE POLICY pdoc_version_isolation ON tpl.pdoc_version
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.pdoc_version.tenant_id
        AND p.pdoc_id = tpl.pdoc_version.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.pdoc_version.tenant_id
        AND p.pdoc_id = tpl.pdoc_version.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  );

ALTER TABLE tpl.private_anchor ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.private_anchor FORCE ROW LEVEL SECURITY;
CREATE POLICY private_anchor_isolation ON tpl.private_anchor
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.private_anchor.tenant_id
        AND p.pdoc_id = tpl.private_anchor.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND EXISTS (
      SELECT 1 FROM tpl.pdoc p
      WHERE p.tenant_id = tpl.private_anchor.tenant_id
        AND p.pdoc_id = tpl.private_anchor.pdoc_id
        AND tpl.can_read_matter(p.matter_id, NULLIF(current_setting('app.user_id', true), ''))
    )
  );

-- 7. Permissions and grants
GRANT EXECUTE ON FUNCTION tpl.can_read_client(text, text) TO app_rw, worker, admin_rw;
GRANT ALL ON TABLE tpl.client TO app_rw, worker, admin_rw;
GRANT ALL ON TABLE tpl.matter_case_link TO app_rw, worker, admin_rw;
GRANT ALL ON TABLE tpl.pdoc TO app_rw, worker, admin_rw;
GRANT ALL ON TABLE tpl.pdoc_version TO app_rw, worker, admin_rw;
GRANT ALL ON TABLE tpl.private_anchor TO app_rw, worker, admin_rw;
"""

SQL_REVERSE = """
DROP POLICY IF EXISTS private_anchor_isolation ON tpl.private_anchor;
DROP TABLE IF EXISTS tpl.private_anchor;

DROP POLICY IF EXISTS pdoc_version_isolation ON tpl.pdoc_version;
DROP TABLE IF EXISTS tpl.pdoc_version;

DROP POLICY IF EXISTS pdoc_isolation ON tpl.pdoc;
DROP TABLE IF EXISTS tpl.pdoc;

DROP POLICY IF EXISTS matter_case_link_isolation ON tpl.matter_case_link;
DROP TABLE IF EXISTS tpl.matter_case_link;

ALTER TABLE tpl.matter DROP CONSTRAINT IF EXISTS matter_client_fk;
ALTER TABLE tpl.matter DROP COLUMN IF EXISTS court_or_forum;
ALTER TABLE tpl.matter DROP COLUMN IF EXISTS case_type;
ALTER TABLE tpl.matter DROP COLUMN IF EXISTS client_id;

DROP POLICY IF EXISTS client_isolation ON tpl.client;
DROP FUNCTION IF EXISTS tpl.can_read_client(text, text);
DROP TABLE IF EXISTS tpl.client;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0004_db_roles_and_grants"),
        ("anchor_lib", "0001_anchor_domains"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
