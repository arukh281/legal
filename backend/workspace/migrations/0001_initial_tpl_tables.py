"""Migration 0001: Initial tpl tables from 03 §3.8 and §3.9."""

from django.db import migrations

SQL_FORWARD = """
CREATE TABLE tpl.tenant (
  tenant_id text PRIMARY KEY,
  name text NOT NULL,
  deployment_mode text NOT NULL DEFAULT 'D2',
  residency_policy text NOT NULL DEFAULT 'ANY' CHECK (residency_policy IN ('IN_ONLY','IN_PREFERRED','ANY')),
  llm_policy jsonb NOT NULL DEFAULT '{}',
  idp jsonb NOT NULL,
  created_at timestamptz NOT NULL
);

CREATE TABLE tpl.app_user (
  tenant_id text NOT NULL REFERENCES tpl.tenant,
  user_id text NOT NULL,
  email text NOT NULL,
  display_name text,
  idp_subject text NOT NULL UNIQUE,
  firm_role text NOT NULL CHECK (firm_role IN ('ADMIN','PARTNER','SENIOR_ASSOCIATE','ASSOCIATE','PARALEGAL','KM_LAWYER','EDITOR')),
  active boolean NOT NULL DEFAULT true,
  PRIMARY KEY (tenant_id, user_id)
);

CREATE TABLE tpl.matter (
  tenant_id text NOT NULL,
  matter_id text NOT NULL,
  client_matter_no text,
  title text NOT NULL,
  client_role text NOT NULL,
  forum jsonb,
  jurisdiction_state text,
  status text NOT NULL DEFAULT 'ACTIVE',
  residency_policy text,
  walled boolean NOT NULL DEFAULT false,
  legal_hold boolean NOT NULL DEFAULT false,
  context_version bigint NOT NULL DEFAULT 0,
  membership_version bigint NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL,
  closed_at timestamptz,
  PRIMARY KEY (tenant_id, matter_id)
);

CREATE TABLE tpl.matter_member (
  tenant_id text NOT NULL,
  matter_id text NOT NULL,
  user_id text NOT NULL,
  role text NOT NULL CHECK (role IN ('LEAD','MEMBER','VIEWER')),
  granted_by text NOT NULL,
  granted_at timestamptz NOT NULL,
  revoked_at timestamptz,
  PRIMARY KEY (tenant_id, matter_id, user_id, granted_at)
);

CREATE TABLE tpl.ethical_wall (
  tenant_id text NOT NULL,
  wall_id text NOT NULL,
  matter_id text NOT NULL,
  basis text NOT NULL,
  created_by text NOT NULL,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, wall_id)
);

CREATE TABLE tpl.wall_exclusion (
  tenant_id text NOT NULL,
  wall_id text NOT NULL,
  user_id text NOT NULL,
  PRIMARY KEY (tenant_id, wall_id, user_id)
);

CREATE TABLE tpl.actor_pseudonym (
  tenant_id text NOT NULL,
  user_id text NOT NULL,
  actor_ref text NOT NULL UNIQUE,
  PRIMARY KEY (tenant_id, user_id)
);

CREATE TABLE tpl.consent_record (
  tenant_id text NOT NULL,
  consent_snapshot_id text NOT NULL,
  level text NOT NULL CHECK (level IN ('TENANT','PRACTICE_GROUP','MATTER','CLIENT','ACTOR')),
  level_ref text,
  flags jsonb NOT NULL,
  evidence jsonb NOT NULL,
  valid_from timestamptz NOT NULL,
  revoked_at timestamptz,
  PRIMARY KEY (tenant_id, consent_snapshot_id)
);

CREATE TABLE tpl.audit_event (
  tenant_id text NOT NULL,
  audit_id text NOT NULL,
  at timestamptz NOT NULL,
  actor text NOT NULL,
  action text NOT NULL,
  object_ref text,
  matter_id text,
  decision text CHECK (decision IN ('ALLOW','DENY')),
  detail jsonb,
  prev_hash bytea,
  row_hash bytea NOT NULL,
  PRIMARY KEY (tenant_id, audit_id)
);
"""

SQL_REVERSE = """
DROP TABLE IF EXISTS tpl.audit_event CASCADE;
DROP TABLE IF EXISTS tpl.consent_record CASCADE;
DROP TABLE IF EXISTS tpl.actor_pseudonym CASCADE;
DROP TABLE IF EXISTS tpl.wall_exclusion CASCADE;
DROP TABLE IF EXISTS tpl.ethical_wall CASCADE;
DROP TABLE IF EXISTS tpl.matter_member CASCADE;
DROP TABLE IF EXISTS tpl.matter CASCADE;
DROP TABLE IF EXISTS tpl.app_user CASCADE;
DROP TABLE IF EXISTS tpl.tenant CASCADE;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("ops", "0001_initial_extensions_and_schemas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
