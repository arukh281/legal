# PROGRESS.md — Build State

## Current State: Session S04 Complete (Source capture + legal gate: IBBI orders first)

### 1. What Was Built

#### A. Identifier Minting & Prefix Registry (`backend/anchor_lib/ids.py`)
- **Monotonic Crockford ULID Generator:**
  - 128-bit layout: 48-bit UNIX millisecond timestamp + 80-bit random entropy.
  - Thread-safe generator (`threading.Lock`) that monotonically increments the 80-bit entropy for calls within the same millisecond and guards against backward clock drift.
  - Generates 26-character uppercase Crockford Base32 strings (excluding `I`, `L`, `O`, `U`).
  - Tested at 100,000 mints: guarantees 100% uniqueness and strict ascending creation-order sortability.
- **Complete Prefix Registry (64 prefixes):**
  - All prefixes from `docs/01_master_architecture.md §5.2` and decisions (D12, D16, D19.3, D20.5, D21.5, D21.16, D22.1):
    - *PLC:* `wrk`, `cas`, `man`, `par`, `cap`, `crun`, `acq`, `lp`, `cal`, `jex`, `cm`, `sm`, `em`, `ai`, `cc`, `asr`, `prp`, `lga`, `crt`, `bnc`, `jdg`, `ent`, `itp`, `rvw`, `rul`, `prs`, `ter`, `xrn`, `xwg`, `xtr`, `gdl`, `imp`, `camp`, `rpq`, `kgp`, `dig`, `dgi`, `ovl`
    - *TPL:* `ten`, `usr`, `grp`, `mat`, `pdoc`, `fct`, `iss`, `opc`, `hrg`, `hold`, `pasr`, `adt`, `tec`, `alr`, `qry`, `evb`, `job`, `clm`, `mem`, `drf`, `ddl`, `mck`, `fb`, `act`, `cns`, `uim`, `wl`, `wr`, `wh`, `ntf`, `chb`, `udg`, `cck`
    - *Shared:* `sum`, `chk`, `gld`, `evc`, `evr`, `aud`, `vr`
  - Automated test reads `docs/01_master_architecture.md §5.2` table directly and verifies 100% parity with zero drift.
  - Unknown prefixes are strictly rejected with `ValueError`.
- **Curated Reference Registry Mnemonics:**
  - Allowed exclusively for: `crt`, `ent`, `rul`, `ter` per 01 §5.2 line 482 (e.g. `crt_IN_SC`, `rul_IN_PREC_07`, `ent_GOV_IN_UP`, `ter_IN_DL`).
  - Works are strictly forbidden from having mnemonics (`wrk_ACT_NI` is rejected with `ValueError` per 01 §5.2 line 483).
- **Content Addresses:**
  - Validates `sha256:<64-char-lowercase-hex>` via `is_valid_sha256()` and `parse_id()`.

#### B. Django Model Field & Domain Convention (`backend/anchor_lib/models.py`)
- `PrefixedULIDField(models.CharField)`:
  - Takes `prefix: str` (e.g. `prefix="wrk"`), sets `max_length=64`, `editable=False`.
  - Uses `@deconstructible class IDMinter` as the default callable (safely serializable in Django migrations without unsupported lambda expressions).
  - Validates prefix matching and Crockford format on save and clean.
- `DomainModel`: abstract base model for all domain models across `plc` and `tpl`.
- Architectural test (`test_no_domain_model_has_autofield_or_uuid_pk`): iterates across all registered models and asserts that no model in `plc` or `tpl` schemas (or domain apps) has an auto-increment integer or UUID primary key.

#### C. Anchor Grammar v1.1 Parser & Canonicalizer (`backend/anchor_lib/anchors.py`)
- Full formal EBNF implementation of Anchor Grammar v1.1 (01 §5.3 and D22.2):
  - `PublicAnchor`: `wrk_<ulid>/<expression_key>#<fragment>`
  - `ProvisionRef`: `wrk_<ulid>#<statute_frag>` (expression-independent; D7)
  - `PITRef`: `wrk_<ulid>#<statute_frag>@<date>[~<territory>]` (point-in-time)
  - `PrivateAnchor`: `pdoc_<ulid>/v<pver>[.<rendition>]#[att<att_no>/]<private_frag>`
  - Schedule anchors with Orders and Rules per D22.2: `sch-1.ord-8.rule-1`, `sch-1.ord-39.rule-2A`, `sch-1.item-5`.
- `parse()`, `format()`, `validate()`, `canonical_key()`, `is_public()`, `is_private()`, `is_fallback_locator()`.
- Exact round-trip guarantee: `format(parse(x)) == x` across all 36 normative examples from 01 §5.3 and D22.2.
- Semantic constraints A1–A8 implemented as pure functions (no DB access):
  - **A1 Paragraph source:** Court-printed numbers (`p{n}`) and synthetic (`u{n}`) only; rejects `p0` and `u0`.
  - **A2 Fallback locators:** `pg{n}` and `pg{n}.l{m}` are permitted only for `quality.gate=QUARANTINED` documents.
  - **A3 Point-in-time resolution (`resolve_pit`):** Resolves by date and territory precedence (`~T` over national); raises `NoExpressionError("NO_EXPRESSION")` on gap (never nearest).
  - **A4 Reconstructed text (`check_reconstructed_text`):** Reconstructed expressions (`derived=True`) require `ROUNDTRIP_OK` for tier-1 claims.
  - **A5 Translations (`check_translation_support`):** Machine translation is forbidden as an expression (`-x-mt` forbidden in lang tag per 01 §5.3 line 563); private `mt-` renditions can never support claims (`MT_ANCHOR`); private `ht-` renditions can support `RECORD_FACT` claims only.
  - **A6 Canonical match key (`canonical_key`):** Formulated strictly for public legal anchors (`wrk_...#<frag>`): strips expression key and default `o1.` prefix, preserves non-default opinion prefixes (`o2.`), drops PIT date/territory; raises `SemanticConstraintError` on private document anchors to prevent cross-revision paragraph collision.
  - **A7 IAL rewriting (`rewrite_statute_expression`):** Rewrites statute anchors to target expression keys valid on query `valid_at`.
  - **A8 Clause level (`get_clause_hierarchy`):** Positional tree depth segment hierarchy.

#### D. Quote Selector (`backend/anchor_lib/selectors.py`)
- `QuoteSelector(exact, prefix, suffix)`: W3C TextQuoteSelector-style representation adhering strictly to 01 §5.5 item 7, 01 §7.1 line 963, and 03 §3.4 (`quote_prefix`, `quote_suffix`).
- Context window of up to 32 characters before and after exact text.
- `find_in()` locates and disambiguates phrases even when repeated across documents or shifted during re-parsing.

#### E. PostgreSQL Database Domains (`backend/anchor_lib/migrations/0001_anchor_domains.py`)
- Migration applying verbatim DDL from 03 §1 item 3:
  - `public_anchor_ref` domain with CHECK regex.
  - `private_anchor_ref` domain with CHECK regex.
  - `any_anchor_ref` domain with CHECK regex.
- Migration is verified reversible (`migrate anchor_lib zero` followed by `migrate anchor_lib`).
- Live PostgreSQL tests verify that valid anchors insert cleanly and invalid/mutated anchors violate check constraints.

#### F. Tenancy & Workspace Domain Models (`backend/workspace/models.py`)
- Implemented all 9 `tpl` domain models using Django 5.2's `CompositePrimaryKey` verbatim matching the PostgreSQL DDL in `docs/mvp/03_data_model_and_contracts.md §3.8, §3.9`:
  - `Tenant`: `tenant_id` (`ten_`), `name`, `deployment_mode`, `residency_policy` (`IN_ONLY`, `ANY`, `HYBRID`), `audit_retention_days`, `soft_delete_retention_days`, `created_at`.
  - `AppUser`: `(tenant_id, user_id)` PK (`usr_`), `email`, `display_name`, `idp_subject`, `firm_role` (`ADMIN`, `PARTNER`, `SENIOR_ASSOCIATE`, `ASSOCIATE`, `PARALEGAL`, `KM_LAWYER`, `EDITOR`), `active`.
  - `Matter`: `(tenant_id, matter_id)` PK (`mat_`), `client_matter_no`, `title`, `client_role` (`PETITIONER`, `RESPONDENT`, etc.), `status`, `walled` (boolean), `created_at`.
  - `MatterMember`: `(tenant_id, matter_id, user_id)` PK, `matter_role` (`LEAD_PARTNER`, `PARTNER`, `ASSOCIATE`, `PARALEGAL`, `VIEWER`), `assigned_by`, `assigned_at`.
  - `EthicalWall`: `(tenant_id, wall_id)` PK (`ewl_`), `matter_id`, `reason`, `active`, `created_by`, `created_at`.
  - `WallExclusion`: `(tenant_id, wall_id, user_id)` PK, `reason`, `excluded_at`.
  - `ActorPseudonym`: `(tenant_id, matter_id, real_id)` PK, `pseudonym`, `created_at`.
  - `ConsentRecord`: `(tenant_id, consent_id)` PK (`cns_`), `purpose`, `granted_by`, `granted_at`, `expires_at`, `revoked_at`.
  - `AuditEvent`: `(tenant_id, audit_id)` PK (`adt_`), `actor`, `action`, `target_type`, `target_id`, `matter_id`, `at`, `prev_hash` (bytea), `row_hash` (bytea), `detail` (jsonb).
- Multi-schema quoting: models use `db_table = 'tpl"."<table_name>'` to compile to schema-qualified table identifiers under PostgreSQL without namespace collisions.
- Django Admin integration (`backend/workspace/admin.py`): clean admin interfaces for Tenant, AppUser, and Matter with search, filtering, and readonly timestamp protections.

#### G. Database Roles, Row-Level Security, and Context Isolation (`backend/workspace/`)
- Verbatim PostgreSQL DDL migration (`workspace/migrations/0002_db_roles_and_rls.py`):
  - Defined roles: `app_rw`, `worker`, `plc_writer`.
  - Enforced `ALTER TABLE tpl.<table_name> ENABLE ROW LEVEL SECURITY;` and `FORCE ROW LEVEL SECURITY;`.
  - Created `tpl.tenant_isolation_policy` across all `tpl` domain tables: `tenant_id = NULLIF(current_setting('app.tenant_id', true), '')`.
  - Implemented `tpl.can_read_matter(matter_id, user_id, user_role)` marked `STABLE SET search_path = pg_catalog, tpl` enforcing ethical wall exclusions and matter memberships.
  - Implemented `tpl.matter_access_policy` combining tenant matching and `tpl.can_read_matter()`.
  - Granted strict least-privilege permissions: `plc_writer` has zero access to `tpl`. `app_rw` and `worker` have `SELECT, INSERT, UPDATE` on `tpl` tables (except `tpl.audit_event`).
  - Truly append-only audit event security: `REVOKE UPDATE, DELETE ON tpl.audit_event FROM app_rw, worker;` and created PostgreSQL trigger `trg_audit_event_immutable` raising `RESTRICTED_ACCESS`.
- Session context management (`backend/workspace/db.py`):
  - `set_db_tenant_context(tenant_id, user_id, purpose)` configures PostgreSQL session variables `app.tenant_id`, `app.user_id`, and `app.purpose`.
  - `reset_db_tenant_context()` unconditionally clears all session settings.
  - `TenantContextMiddleware`: guarantees context is set on authenticated requests and completely reset in a `finally:` block upon release, preventing cross-request connection reuse leakage.

#### H. Authentication & Authorization Choke Point (`backend/core/` & `backend/workspace/authz.py`)
- SSO & Dev Authentication:
  - `allauth` integrated for enterprise SSO (Google/Microsoft OAuth).
  - Custom adapters `LawyerBrainAccountAdapter` and `LawyerBrainSocialAccountAdapter` prevent open self-signup / uninvited user onboarding.
  - `DevAuthenticationBackend` (`backend/core/auth.py`): dev-only token/user authentication strictly disabled if `DEBUG=False` or `DEV_AUTH_ENABLED=False`.
  - Django system check `core.E001` refuses to boot if dev-auth backend is enabled when `DEBUG=False`.
  - Django system check `core.E004` refuses to boot if runtime DB role is a superuser or has `BYPASSRLS`.
- `authz.can(ctx, action, obj)` (`backend/workspace/authz.py`):
  - Single choke point authorization adhering to `docs/mvp/03_data_model_and_contracts.md §6` and `docs/01a_spine_decision_record.md: D9`.
  - Enforces firm roles (`ADMIN`, `PARTNER`, `ASSOCIATE`, `PARALEGAL`, `KM_LAWYER`, `EDITOR`).
  - Enforces active status and ethical wall exclusions (logging `WALL_VIOLATION_ATTEMPT` with `DENY` decision).
  - Enforces matter membership and walled matter isolation.
- Append-Only Audit Chain (`backend/workspace/audit.py`):
  - `record_audit_event()` serializes audit insertions per tenant using `pg_advisory_xact_lock(hashtext('audit_' || tenant_id))` inside transactions.
  - Monotonically timestamps each event and computes cryptographic SHA-256 hash chains `SHA-256(prev_hash || canonical_json)`. Tested under concurrent multi-threaded execution.
- Ninja API Security Choke Point (`backend/core/authz_dependency.py`):
  - `authz_required` dependency validates credentials, hydrates `ExecutionContext`, sets DB session variables, and attaches context to requests.
  - Architectural test (`test_all_ninja_routes_enforce_authz_unless_allowlisted`) inspects all registered Ninja routes to ensure no route can skip authz unless explicitly placed on the public allowlist (`/health`, `/auth/dev-login`).

#### I. Model Gateway v0 (`backend/gateway/`)
- Normative tables implemented in `ops` schema (`backend/gateway/models.py`):
  - `ModelTaskContract`: `(task_code, version)` PK, `description`, `allowed_trust_labels` (`text[]`), `tools_allowed` (`text[]`), `per_call_budget_usd`, `timeout_seconds`, `output_schema` (jsonb).
  - `ModelEndpoint`: `endpoint_id` PK, `provider` (`ANTHROPIC`, `OPENAI`, `GOOGLE`), `model_id`, `model_snapshot`, `residency_country`, `data_class_max` (`PUBLIC`, `INTERNAL`, `TENANT_CONFIDENTIAL`, `PRIVILEGED`), `input_cost_per_token_usd`, `output_cost_per_token_usd`, `active`.
  - `LLMCallRecord`: `(call_id, created_at)` PK using unprefixed 26-character Crockford ULID (`mint_ulid()`), recording full task context, tokens, costs, duration, residency validation, and schema validity.
- Gateway Runner (`backend/gateway/runner.py`):
  - `gateway.run(ctx, task_code, prompt, ...)` enforces routing with strict residency fail-closed check (D14/D15: India residency enforced if tenant policy is `IN_ONLY`), data class ceiling (`endpoint.data_class_max >= call.dataclass`), and budget limits.
  - Validates model output against JSON schema; performs exactly one repair attempt on validation failure; fails loudly on repeated schema violation.
  - Metering and cost calculation based on token usage.
  - Privacy guard: suppresses prompt and response bodies from call records and logs if dataclass is `TENANT_CONFIDENTIAL` or `PRIVILEGED` (recording hash and byte length only per `docs/mvp/04_stack_and_infra.md §2.13`).
- Adapters:
  - Anthropic SDK adapter (`gateway/adapters/anthropic_adapter.py`).
  - OpenAI SDK adapter (`gateway/adapters/openai_adapter.py`).
  - Google GenAI SDK adapter (`gateway/adapters/google_adapter.py`).
  - Fake adapter (`gateway/adapters/fake_adapter.py`) for deterministic test execution.
- Architectural SDK Guard Test (`test_no_direct_sdk_imports_outside_gateway`):
  - AST scanner inspects all Python files across `backend/` and asserts that `anthropic`, `openai`, and `google` SDKs are never imported outside `backend/gateway`.

#### J. Source Capture & Legal Gate (`backend/ingest/` — Session S04)
- **Repo-Wide HTTP Guard (`backend/core/http_client.py`):**
  - Private `RawHttpClient` encapsulates `httpx.Client`. Only obtainable via `GatedHttpClient`.
  - Architectural AST guard test (`test_no_direct_http_imports_outside_core_http_client`): scans all Python files in `backend/` and guarantees no direct imports of `httpx`, `requests`, `urllib.request`, or `aiohttp` outside `core/http_client.py` (with exemptions for gateway LLM SDK adapters and storage `boto3`).
  - Settings `CRAWLER_USER_AGENT` and `CRAWLER_CONTACT_EMAIL` with Django startup system checks `core.E005` and `core.E006` refusing default/example values in production.
- **Legal Gate & Cross-Process Rate Limiter (`backend/ingest/gate.py`):**
  - `check_legal_gate`: verifies profile status (`PROVISIONAL`/`APPROVED`), kill switch, expiry, permitted access modes, allowed hours IST, and backfill night window (23:00–07:00 IST with midnight wrap).
  - `enforce_host_rate_limit`: cross-process per-host rate limiting via PostgreSQL advisory locks (`pg_advisory_xact_lock`) and `plc.host_rate_limit`. Tested across concurrent worker processes.
- **Content-Addressed Storage (`backend/ingest/storage.py`):**
  - S3 / MinIO CAS storage at `raw/sha256/{h[:2]}/{h[2:4]}/{h}.pdf` and `RawBlob` table.
  - Automatically provisions `plc-raw` bucket in MinIO during local development.
- **IBBI Order Mirror Adapter (`backend/ingest/adapters/ibbi.py`):**
  - Extracts listing items across `/orders/nclt`, `/orders/nclat`, `/orders/supreme-court`, `/orders/high-courts`.
  - Stable `source_record_key = f"{section}:{file_stem}"` avoiding date/number churn.
  - CAPTCHA breaker (`detect_captcha` halts on signature tokens, marks source `BLOCKED`).
  - Layout drift breaker (`detect_layout_drift` halts on table/header mismatch or 0 items parsed, marks source `DEGRADED`).
- **Resumable Source Crawler & Safety Breakers (`backend/ingest/crawler.py`):**
  - Checkpoints page completion in `plc.crawl_checkpoint`; resumes crashed runs without duplicating work.
  - Mass-change breaker halts and marks source `DEGRADED` if >10% of items change (after ≥20 items).
  - Delta deduplication: skips re-downloading PDFs when URL and metadata are unchanged (`change_kind = "UNCHANGED"`, `pdf_fetched = false`); stops delta sweep after 20 consecutive unchanged records.
  - CloudEvents outbox emission: emits `plc.raw.captured.v1` atomically with `Capture`, and `plc.source.health.v1` on run completion/failure (lane populated in `lane` column; `warc`, `norm_fingerprint`, `near_dup_hint` set to `None`).
- **Live Archived ToU/Robots Snapshots via GatedHttpClient (`backend/ingest/management/commands/seed_ibbi_profile.py`):**
  - Fetched live through `GatedHttpClient` from `https://ibbi.gov.in/home/website-policy` (HTTP 200, 104,889 bytes) and `https://ibbi.gov.in/robots.txt` (HTTP 404, 736 bytes), archived in CAS, and seeded into `PROVISIONAL` LegalProfile (`lp_01M3XG2HKBBTC4XSK093P2HB3W`).
  - Recorded exact policy fetch timestamp (`2026-10-02T05:05:57.250792+00:00`) in profile notes and `plc.capture` audit records.
  - Verified that `https://ibbi.gov.in/home/website-policy` contains both the copyright section ("Material featured on this site may be reproduced free of charge...") and hyperlink section ("no prior permission is required but we would like you to inform us... We do not permit our pages to be loaded into frames") cited in `docs/mvp/01_corporate_corpus_and_sources.md §2.4`.
- **Gated Fixture Refresh CLI Command (`backend/ingest/management/commands/refresh_fixtures.py`):**
  - Refreshes evaluation and test fixtures strictly through `GatedHttpClient(source_id="IBBI_ORDERS")`. Raw curl or un-gated HTTP calls are prohibited repo-wide.
- **Crawl CLI Command (`backend/ingest/management/commands/crawl_ibbi.py`):**
  - Runs manual delta/backfill sweeps with `--section`, `--pages`, `--mode`, and `--offline` fixture replay support.
  - Reports rows parsed, PDFs downloaded, captures by change_kind, profile_id in fetch_context, and observed rate-limit spacing.
- **Live Real Exit Check Demonstrated Across All 4 IBBI Sections (2 pages each):**
  - *Initial Delta Sweep:*
    - `supreme-court`: 40 rows parsed, 40 PDFs downloaded, captures: 40 NEW, profile: `lp_01M3XG2HKBBTC4XSK093P2HB3W`, observed rate spacing: min=2.93s, avg=4.05s, max=17.06s.
    - `high-courts`: 40 rows parsed, 40 PDFs downloaded, captures: 40 NEW, profile: `lp_01M3XG2HKBBTC4XSK093P2HB3W`, observed rate spacing: min=2.93s, avg=4.22s, max=16.39s.
    - `nclat`: 40 rows parsed, 40 PDFs downloaded, captures: 40 NEW, profile: `lp_01M3XG2HKBBTC4XSK093P2HB3W`, observed rate spacing: min=2.93s, avg=4.67s, max=13.80s.
    - `nclt`: 40 rows parsed, 39 PDFs downloaded (1 existing fixture), captures: 39 NEW, 1 UNCHANGED, profile: `lp_01M3XG2HKBBTC4XSK093P2HB3W`, observed rate spacing: min=2.92s, avg=6.92s, max=50.21s.
  - *Re-run Delta Sweep (Idempotency & Deduplication):*
    - All 4 sections yielded 100% `UNCHANGED` (20 consecutive unchanged items per section) and terminated at page 1 with **0 duplicate PDF downloads**.
- **Contract & Resiliency Test Suites (`backend/ingest/tests/`):**
  - `test_http_guard.py`: repo-wide AST import verification (no direct HTTP clients) + AST verification prohibiting disabled TLS (`verify=False`, `verify=0`, `verify=None`).
  - `test_legal_gate.py`: 8 comprehensive checks covering status, kill switch, expiry, access mode, and midnight-wrapping IST hours.
  - `test_rate_limit.py`: concurrent multi-worker cross-process rate limiter verification, plus assertion that request spacing is strictly never below the profile floor.
  - `test_ibbi_adapter.py`: real HTML listing fixtures, CAPTCHA detection, layout drift detection.
  - `test_crawl_idempotency.py`: first crawl yields NEW, second delta yields UNCHANGED with zero PDF re-downloads; modified PDF yields CHANGED.
  - `test_crash_and_resume.py`: interrupted crawl resumes at page 2 from checkpoint without duplicating page 1.
  - `test_safety_breakers.py`: CAPTCHA, layout drift, and mass-change breakers tested against fixtures.
  - `test_outbox_events.py`: field-for-field contract verification of `raw.captured.v1` and `source.health.v1` against master architecture §6.3/§6.4.

---

### 2. How to Run It

```bash
cd backend

# Type check (strict repo-wide across all 133 source files)
uv run mypy .

# Lint & formatting check
uv run ruff check .
uv run ruff format --check .

# Run all 139 backend tests against PostgreSQL 18
uv run pytest

# Seed IBBI legal profile with live archived ToU / policy snapshots
uv run python manage.py seed_ibbi_profile

# Run IBBI crawl (e.g. NCLT 2 pages delta)
uv run python manage.py crawl_ibbi --section nclt --pages 2 --mode delta

# Refresh evaluation fixtures strictly via GatedHttpClient
uv run python manage.py refresh_fixtures --section nclt --max-sample-pdfs 2

# Test migration reversibility
uv run python manage.py migrate ingest zero --database=owner
uv run python manage.py migrate ingest --database=owner
```

---

### 3. Stubs & Notes
- **Downstream Domain Phases (S05–S18):**
  - Parsing (`parse` / P1): S05 will consume `raw.captured.v1` outbox events, extract text layer/OCR, parse judgments/statutes, assign anchors, and emit `doc.parsed.v1`.
  - Indexing & Retrieval (`index`, `retrieve` / P2, P5): S06–S07.
  - Citator (`citator` / P3): S09.
- **Model Gateway Real-API Smoke Test:**
  - `test_real_llm_smoke` is marked `@pytest.mark.skipif` unless real API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) are present in the environment.

---

### 4. Known Issues
1. **Docker configuration modification:** Recorded previously: `~/.docker/config.json` had its `credsStore` entry removed.
2. **Host port 5432 conflict:** Docker Compose maps PostgreSQL container port 5432 to host port 5433 (`POSTGRES_HOST_PORT=5433`).
3. **Host port 8000 conflict:** Python HTTP server on host port 8000; web port defaults to 8000 (configurable via `WEB_HOST_PORT`).
4. **Procrastinate Django connector listen/notify:** Psycopg3 connection under Django connector runs with `--no-listen-notify`.
5. **Database migrations require `--database=owner`:** Due to multi-role architecture, migration runner routes DDL through the `owner` connection alias.

---

### 5. What the Next Session (S05) Needs
- **Session S05: Parsing (text layer + OCR, judgment and statute parsers, anchors, citation extraction):**
  - Consumes `raw.captured.v1` events from `ops.event_outbox`.
  - PDF text layer extraction (PDF.js / pypdf / Amazon Textract OCR fallback).
  - Indian legal document structure parsing (coram, bench, date, party names, headnotes, paragraph numbering).
  - Anchor generator for judgment paragraphs (`wrk_...#p45`) and statute sections (`wrk_...#sec-138`).
  - Citation extractor and preliminary resolution.
  - Emits `doc.parsed.v1` and generates `ParsedDocument` JSON.
