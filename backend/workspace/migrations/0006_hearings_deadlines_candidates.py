"""Migration 0006: Hearings, Deadlines, Matter Dependencies, and Case Candidates (P7).

Normative sources:
- Session R2: hearings, dates and Today
- docs/mvp/03_data_model_and_contracts.md §3.9 (tpl.hearing, tpl.matter_dependency)
- docs/mvp/03_data_model_and_contracts.md §3.10 (tpl.deadline)
- DECISIONS.md (2026-10-18: tpl.case_candidate, cnd prefix, chk_deadline_rule_id_refused)
- User Corrections:
  - Stable key on tpl.hearing for cause-list updates: (tenant_id, matter_id, date, bench, court_no)
  - Stable key on tpl.case_candidate: (tenant_id, matter_id, kind, list_date, bench, normalized_case_no)
  - Normalization of existing matter_case_link rows
"""

from typing import Any

from django.db import migrations

from anchor_lib.case_numbers import normalize_case_number

SQL_FORWARD = """
-- 1. Hearings table (tpl.hearing)
CREATE TABLE tpl.hearing (
  tenant_id text NOT NULL REFERENCES tpl.tenant,
  matter_id text NOT NULL,
  hearing_id text NOT NULL,
  case_id text,
  date date NOT NULL,
  court_no text,
  item_no text,
  bench text,
  purpose text,
  source text NOT NULL DEFAULT 'MANUAL' CHECK (source IN ('MANUAL','CAUSE_LIST','ECOURTS','SC')),
  source_ref text,
  status text NOT NULL DEFAULT 'LISTED' CHECK (status IN ('LISTED','HEARD','ADJOURNED','NOT_REACHED','CANCELLED')),
  next_date date,
  entered_by text NOT NULL,
  observed_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, hearing_id),
  CONSTRAINT fk_hearing_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id)
);

-- Stable unique index for cause-list revisions per Correction 2
CREATE UNIQUE INDEX idx_hearing_causelist_stable
  ON tpl.hearing (tenant_id, matter_id, date, bench, court_no)
  WHERE source = 'CAUSE_LIST';

CREATE INDEX idx_hearing_matter_date
  ON tpl.hearing (tenant_id, matter_id, date);

-- 2. Deadlines table (tpl.deadline)
CREATE TABLE tpl.deadline (
  tenant_id text NOT NULL REFERENCES tpl.tenant,
  matter_id text NOT NULL,
  deadline_id text NOT NULL,
  rule_id text,
  rule_code text,
  rule_version text,
  label text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('LIMITATION','STATUTORY_REPLY','COURT_ORDERED','COMPLIANCE','INTERNAL','MANUAL')),
  calendar_ref jsonb,
  trigger_event jsonb,
  computed_date date,
  due_on date NOT NULL,
  window_kind text,
  hard_limit date,
  extendable text CHECK (extendable IN ('NO','CONDONABLE','COURT_DISCRETION')),
  statutory_anchors text[] NOT NULL DEFAULT '{}',
  trace jsonb NOT NULL DEFAULT '[]',
  sensitivity jsonb NOT NULL DEFAULT '[]',
  interpretation_variant text,
  status text CHECK (status IN ('CONFIRMED_INPUTS','ASSUMED_INPUTS','UNCERTAIN_CALENDAR','CONTESTED_RULE')),
  lifecycle text NOT NULL DEFAULT 'PROPOSED' CHECK (lifecycle IN ('PROPOSED','CONFIRMED','DONE','WAIVED','MISSED')),
  owner text,
  reminders jsonb,
  created_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, deadline_id),
  CONSTRAINT fk_deadline_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id),
  CHECK (rule_id IS NOT NULL OR kind = 'MANUAL'),
  CHECK (lifecycle <> 'CONFIRMED' OR status = 'CONFIRMED_INPUTS' OR kind = 'MANUAL'),
  -- Enforce non-negotiable 2 at database level until R4 lands plc.rule_spec:
  CONSTRAINT chk_deadline_rule_id_refused CHECK (rule_id IS NULL)
);

CREATE INDEX idx_deadline_matter_due
  ON tpl.deadline (tenant_id, matter_id, due_on);

-- 3. Matter dependency table (tpl.matter_dependency)
CREATE TABLE tpl.matter_dependency (
  tenant_id text NOT NULL REFERENCES tpl.tenant,
  matter_id text NOT NULL,
  public_id text NOT NULL,
  match_key text NOT NULL,
  as_of_legal_date date,
  kind text NOT NULL CHECK (kind IN ('OWN_CASE','CITED_IN_OUR_DRAFT','CITED_BY_OPPONENT','IN_MEMO_FAVOURABLE','IN_MEMO_ADVERSE','GOVERNING_PROVISION','WATCHED')),
  weight real,
  source_ref text NOT NULL,
  added_at timestamptz NOT NULL,
  PRIMARY KEY (tenant_id, matter_id, public_id, kind),
  CONSTRAINT fk_dependency_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id)
);

CREATE INDEX idx_matter_dependency_match_key
  ON tpl.matter_dependency (tenant_id, match_key);

-- 4. Case Candidate table (tpl.case_candidate) for "Check these"
CREATE TABLE tpl.case_candidate (
  tenant_id text NOT NULL REFERENCES tpl.tenant,
  candidate_id text NOT NULL,
  matter_id text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('HEARING', 'ORDER', 'HEARING_DROPPED')),
  source text NOT NULL CHECK (source IN ('CAUSE_LIST', 'IBBI_ORDER')),
  source_ref text NOT NULL,
  case_number_raw text NOT NULL,
  list_date date,
  bench text,
  normalized_case_no text,
  details jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CONFIRMED', 'DISMISSED')),
  created_at timestamptz NOT NULL,
  resolved_at timestamptz,
  resolved_by text,
  PRIMARY KEY (tenant_id, candidate_id),
  CONSTRAINT fk_candidate_matter FOREIGN KEY (tenant_id, matter_id) REFERENCES tpl.matter(tenant_id, matter_id),
  -- Stable unique key per Correction 2
  CONSTRAINT uq_case_candidate_stable UNIQUE (tenant_id, matter_id, kind, list_date, bench, normalized_case_no)
);

-- 5. Row-Level Security: Enable and FORCE on all 4 tables
ALTER TABLE tpl.hearing ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.hearing FORCE ROW LEVEL SECURITY;
CREATE POLICY hearing_isolation ON tpl.hearing
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.deadline ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.deadline FORCE ROW LEVEL SECURITY;
CREATE POLICY deadline_isolation ON tpl.deadline
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.matter_dependency ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.matter_dependency FORCE ROW LEVEL SECURITY;
CREATE POLICY matter_dependency_isolation ON tpl.matter_dependency
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

ALTER TABLE tpl.case_candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE tpl.case_candidate FORCE ROW LEVEL SECURITY;
CREATE POLICY case_candidate_isolation ON tpl.case_candidate
  USING (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  )
  WITH CHECK (
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')
    AND tpl.can_read_matter(matter_id, NULLIF(current_setting('app.user_id', true), ''))
  );

-- 6. Grant least-privilege permissions to app_rw and worker
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.hearing TO app_rw, worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.deadline TO app_rw, worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.matter_dependency TO app_rw, worker;
GRANT SELECT, INSERT, UPDATE, DELETE ON tpl.case_candidate TO app_rw, worker;
"""

SQL_REVERSE = """
REVOKE ALL ON tpl.case_candidate FROM app_rw, worker;
REVOKE ALL ON tpl.matter_dependency FROM app_rw, worker;
REVOKE ALL ON tpl.deadline FROM app_rw, worker;
REVOKE ALL ON tpl.hearing FROM app_rw, worker;

DROP TABLE IF EXISTS tpl.case_candidate CASCADE;
DROP TABLE IF EXISTS tpl.matter_dependency CASCADE;
DROP TABLE IF EXISTS tpl.deadline CASCADE;
DROP TABLE IF EXISTS tpl.hearing CASCADE;
"""

def backfill_normalize_case_links(apps: Any, schema_editor: Any) -> None:
    """Normalize existing matter_case_link rows in place per Correction 4."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT tenant_id, matter_id, scheme, value_normalized FROM tpl.matter_case_link")
        rows = cursor.fetchall()
        for tenant_id, matter_id, scheme, val in rows:
            parsed = normalize_case_number(val)
            if parsed.parseable and parsed.canonical != val:
                # Update to canonical
                cursor.execute(
                    """
                    UPDATE tpl.matter_case_link
                    SET value_normalized = %s
                    WHERE tenant_id = %s AND matter_id = %s AND scheme = %s AND value_normalized = %s
                    """,
                    [parsed.canonical, tenant_id, matter_id, scheme, val],
                )


def noop_reverse(apps: Any, schema_editor: Any) -> None:
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("workspace", "0005_client_and_document_vault"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
        migrations.RunPython(
            code=backfill_normalize_case_links,
            reverse_code=noop_reverse,
        ),
    ]
