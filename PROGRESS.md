# PROGRESS.md — Build State

## Current State: Session S05b Complete (Citations: extraction, resolution, deduplication and merge ledger)

### 1. What Was Built

#### A. Citation Extraction Engine (`backend/parse/citations/extractor.py`)
- Regex-based grammar parser extracting reporter citations and case numbers across ParsedDocument text:
  - Reporter schemes: SCC (`(2019) 4 SCC 17`), SCC OnLine (`2023 SCC OnLine NCLAT 839`), AIR (`AIR 1968 SC 1432`), SCR (`[1968] 3 SCR 724`), INSC Neutral (`2026 INSC 1046`), High Court Neutral (`2023:DHC:1234`).
  - Case numbers: NCLT CP (IB) (`Company Petition (IB) No. 149 of 2023`), NCLAT Company Appeal (`Company Appeal (AT) (Insolvency) No. 123 of 2021`), explicit court prefix cases, bare case numbers without court.
  - Pinpoints: extracted adjacent paragraphs (`para 14` -> `#p14`) and page numbers.
  - `QuoteSelector`: W3C prefix (up to 32 chars), exact, suffix disambiguation selector.
  - Temporal sanity: validates citation year vs citing decision date; flags `CITED_AFTER_CITING` if a document cites a future publication.
  - Quality degradation flags: anchors with `ocr_conf < 0.80` or hidden text are flagged as degraded and not counted as trusted resolved evidence.

#### B. Statute & Provision Mention Extractor (`backend/parse/citations/statutes.py`)
- Grammar parser for sections, subsections, and Constitution articles (`Section 7`, `Section 9(5)(i)`, `Article 141`).
- In-document definition resolution (`extract_in_document_definitions`): captures definitions from early paragraphs (e.g. `(hereinafter referred to as the 'Code')`) mapping short names to canonical statutes.
- Point-in-time rules (`AS_CITED`, `NO_EXPRESSION`).
- Strictly corpus-only provision resolution: since no ACT works exist in `plc.work`, 100% of statute mentions return `resolved_anchor_ids = []` and `resolution_status = "not in MVP corpus"`.
- Zero new SQL tables for statute mentions per `docs/mvp/03_data_model_and_contracts.md` line 321 (`StatuteMention` lives only inside `ParsedDocument`).

#### C. Citation Resolver & Alias Lifecycle (`backend/parse/citations/resolver.py`)
- AuthorityView & alias resolution engine implementing Directive #2, #3, #4:
  - Reporter citations: mints STUB Work (`status="STUB"`, `work_type="JUDGMENT"`), creates T4 alias, emits `acquire.requested.v1` to `ops.event_outbox`.
  - Case numbers with court stated: mints STUB LegalCase (`status="STUB"`), creates T4 alias, returns `case_id` (never mints a STUB judgment work).
  - Case numbers without court stated: left UNRESOLVED (`target_id=None`), no alias minted, no STUB minted.
  - `court_hint`: set only when citation explicitly states court, never inferred from reporter.
  - Trust tier T4: citation-derived aliases stamped with `trust_tier="T4"`, `source="citation_mention"`, and `evidence={"mention_id": ..., "citing_work_id": ..., "anchor_id": ...}`.
  - `promote_authoritative_alias`: when an authoritative T0–T2 alias arrives for a key, the T4 alias becomes `SUPERSEDED`, the STUB work merges into the real work via `plc.identity_merge_ledger`, existing `CitationMention` rows re-point, and `identity.merged.v1` event is emitted.

#### D. Deduplication and Merge Ledger (`backend/parse/citations/dedupe.py`)
- Exact-match deduplication engine: checks `(court_id, normalized_case_no, decision_date)`.
- Auto-merge executes only when all three match exactly. Ambiguous matches (different year, different bench, missing date) reject merge and route to review queue.
- `dedupe_and_merge`: updates from_work status to `MERGED`, sets `merged_into`, records in `plc.identity_merge_ledger`, supersedes active aliases, re-points mentions, and emits `identity.merged.v1`.
- `split_work`: reverts merge, sets from_work back to `ACTIVE`, records `SPLIT` in `plc.identity_merge_ledger`, and emits `identity.split.v1`.

#### E. PostgreSQL Database Migration (`backend/parse/migrations/0002_citation_and_merge_tables.py`)
- Created `plc.citation_mention` with ULID PK (`cm_`), FKs, resolution fields, and temporal check.
- Created `plc.identity_merge_ledger` with ULID PK (`evr_`), `kind`, `op`, `from_id`, `to_id`, `reason`, `confidence`.
- Granted permissions to `app_rw`, `worker`, `plc_writer`, `admin_rw`.
- Registered bumped pipeline version `p1.citation@0.1.0|det_v1` in `ops.pipeline_version`.
- Migration is verified reversible.

#### F. Corpus Resolution Management Command (`backend/parse/management/commands/resolve_citations.py`)
- Processes parsed documents in `plc.parse_run` (skipping QUARANTINED).
- Writes new `ParsedDocument` JSON artifacts with bumped `pipeline_version = "p1.citation@0.1.0|det_v1"` to S3 without editing old S3 objects or ParseRun stats in place.
- Corpus execution results across 496 eligible documents (6 quarantined skipped):
  - Total citations persisted to `plc.citation_mention`: 3,411
  - Citations by scheme: SCC: 1,404 | CASE_NO: 1,275 | SCC_ONLINE: 453 | NEUTRAL_INSC: 123 | AIR: 93 | SCR: 45 | NEUTRAL_HC: 18
  - Citations resolution: 3,024 RESOLVED (including case numbers to STUB cases and reporter cites to STUB works), 387 UNRESOLVED
  - Statute mentions found: 15,355 (100% resolved as "not in MVP corpus")
  - Degraded citations flagged: 15 (due to `ocr_conf < 0.80` or hidden text)

#### G. Identifier Minting & Prefix Registry (`backend/anchor_lib/ids.py`)
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

#### N. Parsing Engine & Judgment Structure (Session S05a: `backend/parse/`)
- **Schema & Models (`backend/parse/models.py`, `backend/parse/migrations/0001_initial_parse_tables.py`):**
  - Applied verbatim SQL DDL for 10 domain tables in `plc`: `court`, `work`, `legal_case`, `work_case`, `expression`, `manifestation`, `identifier_alias`, `parse_run`, `anchor`, `anchor_alias`.
  - Configured RLS grants for `app_rw` and seeded initial court registry mnemonics (`crt_IN_SC`, `crt_IN_NCLAT`, `crt_IN_NCLT_MUM`, `crt_IN_NCLT_CHD`, etc.) using 01 §5.2 rules.
  - Registered `p1.parser@0.1.0|det_v1` in `ops.pipeline_version`.
- **Pre-processor & Scan Robustness (`backend/parse/preprocessor.py`):**
  - Auto-rotates upside-down/sideways pages using projection variance.
  - Deskews skewed scans (-10° to +10° projection profile peak search).
  - Low-DPI detection and upscaling to 300 DPI, contrast stretching for faint scans.
  - Multi-format image wrapping: accepts JPG, PNG, TIFF, and HEIC inputs and wraps them into single-page PDF streams for identical processing.
  - Indic script detection: post-OCR check flags `lang_unsupported` on Indic pages to avoid OCR hallucinations.
- **OCR Engine Abstraction & Tesseract Integration (`backend/parse/ocr.py`):**
  - `OcrEngine` protocol and `TesseractOcrEngine` implementation using local binary.
  - Queries dynamic version (`pytesseract.get_tesseract_version()`, verified `5.5.3`), records engine name and exact version per page.
  - Fails loudly if binary is missing (never silently skips OCR).
  - Emits word-level bounding boxes normalized to `[0, 1]` with individual word confidences.
  - Caches OCR page JSON results in `eval/fixtures/ocr/` for deterministic offline test runs.
- **Adversarial Hidden Text Detector (`backend/parse/hidden_text.py`):**
  - Temporarily expands page cropbox to mediabox to detect text placed outside the visible area (e.g. off-canvas prompt injection).
  - Applies 5pt edge tolerance so footers near the bottom margin are not falsely flagged as OFF_PAGE.
  - Flags white text (sRGB ≥ 248), tiny fonts (< 1.0 pt), and off-page text beyond the visible cropbox.
  - Drops adversarial injection text from clean blocks and records flagged regions.
- **Page-Level Triage (`backend/parse/triage.py`):**
  - Triage decision tree: born-digital text-layer validation vs scan preprocessing + OCR routing.
- **Judgment Parser & Court Header Extraction (`backend/parse/judgment.py`):**
  - Strips repeated furniture lines (headers/footers appearing on ≥60% of pages).
  - Extracts Indian court and bench identity, resolving bench city over party address matches.
  - Resolves case number, court type, and decision date using prioritized stamp hierarchy.
  - Robust party extraction using backward line traversal from `Versus`/`Vs.` to distinguish party names from representative/address blocks.
  - Order divider handling: detects `ORDER` / `O R D E R` / `JUDGMENT` before body; accumulates header into `hdr` block; resets unnumbered index so first narrative paragraph starts at `u1`.
  - Extracts explicit numbered paragraphs `p{n}`, sub-paragraphs `p{n}.{m}`, unnumbered paragraphs `u{n}`, and operative order `ord`.
- **Anchor Stability & Assignment Engine (`backend/parse/anchors.py`):**
  - Assigns canonical `PublicAnchor` strings via `anchor_lib.parse()`.
  - Re-parse alignment protocol: aligns blocks across parse runs using `NUM_EQ` (court printed number), `HASH_EQ` (exact text hash), and `NW_ALIGN` (Needleman-Wunsch diff on text modifications).
  - Tombstones deleted paragraphs on `anchor.state = 'TOMBSTONED'` and `forward_to` set to the best-overlap new anchor by `SequenceMatcher` similarity (≥ 0.50 threshold); `None` if no match is close.
  - Unmatched new court-numbered paragraphs keep their printed numbers `p{n}` (`EXPLICIT`), satisfying Constraint A1.
- **Quality Gating & Django Admin Review Queue (`backend/parse/gates.py`, `backend/parse/admin.py`):**
  - Gates documents into `PASS`, `FLAGGED`, or `QUARANTINED`.
  - Enforces per-anchor `ocr_conf < 0.80` restriction, preventing low-confidence OCR text from backing Tier-1 legal claims.
  - Django Admin provides review queue with colored gate badges, filter by gate status, and direct inspection of parsed blocks.
- **S3 Storage & DB Atomic Persistence (`backend/parse/storage.py`, `backend/parse/consumer.py`):**
  - Uploads gzip-compressed `ParsedDocument` JSON to `parsed/{work_id}/{expression_key}/{parse_id}.json.gz` in MinIO/S3 first, hashes SHA-256.
  - Executes atomic database commit (`work`, `legal_case`, `manifestation`, `parse_run`, `anchor`, `anchor_alias`) and emits `doc.parsed.v1` event to `ops.event_outbox` in the SAME transaction.
  - Tested crash scenario between S3 upload and DB commit: leaves orphaned S3 artifact but clean database.
- **Management Command & Full Corpus Exit Check (`backend/parse/management/commands/parse_captured.py`):**
  - Full output saved to `eval/reports/s05a_quality.txt`.
  - Processed all 156 unique captured IBBI orders in storage (`raw_id` deduplicated):
    - Breakdown by section: Supreme Court (40), High Courts (40), NCLAT (40), NCLT (36).
    - Note on the 4 missing documents to 160: In Session S04, the IBBI portal mirror captured 40 items each for SC, HC, and NCLAT, but only 36 unique order records existed for NCLT. Zero documents were skipped, zero failed, zero left unparsed — exactly 156 / 156 (100%) captured PDFs were processed.
    - 3,605 pages analyzed: 3,502 born-digital (97.14%), 103 OCR scanned (2.86% OCR share).
    - 8,463 permanent anchors issued (average 51.9 numbered paragraphs per document; 8,095 explicit paragraph nodes / 156 docs).
    - Quality gate distribution:
      - 140 PASS (89.7%)
      - 14 FLAGGED (9.0% — routed to admin review queue due to unnumbered paragraphs)
      - 2 QUARANTINED (1.3% — excluded from index)
      - Total: 140 + 14 + 2 = 156.
    - Integrity flags: 3 hidden text detected (quarantined), 0 handwriting, 0 unsupported languages, 0 LLM fallback invocations.
  - **Re-parse Anchor Stability Canary (6 Golden Fixtures):**
    - Ran re-parse cycle across all 6 golden fixtures (`nclt_born_digital_chd`, `nclat_word_export`, `nclat_born_digital_del`, `nclt_scanned_ahm`, `nclt_scanned_ahm_2`, `nclt_born_digital_mum`).
    - Stored anchors preserved: 89 / 89 = **100.00%** (target ≥ 99.5% PASS).
    - Tombstones / breaking changes on unchanged re-parse: 0 (0.00%).
- **Test Suite (`backend/parse/tests/`):**
  - 26 new tests for S05b, 187 total passed across backend:
    - `test_citation_extractor.py`: full reporter schemes (SCC, SCC OnLine, AIR, SCR, INSC, Neutral HC), case numbers (CP(IB), Company Appeal, bare cases), pinpoints, quote selectors, temporal sanity, and quality degradation flags.
    - `test_statute_extractor.py`: sections, subsections, articles, in-document definitions, and strictly corpus-only provision resolution ("not in MVP corpus").
    - `test_resolver.py`: STUB work vs STUB case minting, T4 alias trust tier, case numbers without court staying UNRESOLVED, and `acquire.requested.v1` event contract.
    - `test_alias_lifecycle.py`: T4 alias supersession upon arrival of authoritative T0–T2 alias, STUB work merge into real work via `plc.identity_merge_ledger`, mention re-pointing, and `identity.merged.v1` event.
    - `test_dedupe_and_merge.py`: exact-match auto-merge, rejection of ambiguous matches (year mismatch, bench mismatch) to review queue, and `split_work` reversal with `identity.split.v1`.
    - `test_migration_0002.py`: database schema verification for `plc.citation_mention`, `plc.identity_merge_ledger`, and zero SQL tables for statute mentions.
  - Plus 22 existing parse tests from S05a (golden outputs, anchor stability, hidden text, OCR gate, scan robustness, S3 crash resilience, doc.parsed.v1 event).

---

### 2. How to Run It

```bash
cd backend

# Type check (strict repo-wide across all 172 source files)
uv run mypy .

# Lint & formatting check
uv run ruff check .
uv run ruff format --check .

# Run all 187 backend tests against PostgreSQL 18
uv run pytest

# Extract and resolve citations across the parsed corpus
uv run python manage.py resolve_citations

# Parse captured documents (e.g. 5 sample docs or full corpus)
uv run python manage.py parse_captured --limit 5
uv run python manage.py parse_captured --limit 160

# Run IBBI crawl
uv run python manage.py crawl_ibbi --section nclt --pages 2 --mode delta

# Test migration reversibility
uv run python manage.py migrate parse zero --database=owner
uv run python manage.py migrate parse --database=owner
```

---

### 3. Stubs & Notes
- **Downstream Domain Phases (S06–S18):**
  - Indexing & Retrieval (`index`, `retrieve` / P2, P5): S06 will build chunks, FTS `legal_en`, embeddings (Voyage), pgvector generations + aliases, and Index Access Layer.
  - Citator (`citator` / P3): S09.
- **Model Gateway Real-API Smoke Test:**
  - `test_real_llm_smoke` is marked `@pytest.mark.skipif` unless real API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) are present in the environment.
- **OCR Engine Migration (S15):**
  - Tesseract local engine configured for dev and CI; AWS Textract (ap-south-1) migration planned behind the same `OcrEngine` contract for production deployment in S15.

---

### 4. Known Issues
1. **Docker configuration modification:** Recorded previously: `~/.docker/config.json` had its `credsStore` entry removed.
2. **Host port 5432 conflict:** Docker Compose maps PostgreSQL container port 5432 to host port 5433 (`POSTGRES_HOST_PORT=5433`).
3. **Host port 8000 conflict:** Python HTTP server on host port 8000; web port defaults to 8000 (configurable via `WEB_HOST_PORT`).
4. **Procrastinate Django connector listen/notify:** Psycopg3 connection under Django connector runs with `--no-listen-notify`.
5. **Database migrations require `--database=owner`:** Due to multi-role architecture, migration runner routes DDL through the `owner` connection alias.

---

### 5. What the Next Session (S06) Needs
- **Session S06: Index: chunks, FTS `legal_en`, embeddings, pgvector generations + aliases, Index Access Layer (IAL):**
  - Consumes `doc.parsed.v1` events from `ops.event_outbox`.
  - Chunking strategy rooted strictly in durable anchors (`anchor_id` + `quote_selector`).
  - PostgreSQL 18 FTS config `legal_en` with custom stop words and legal stemmer.
  - Vector embeddings (Voyage `halfvec` HNSW in pgvector).
  - Dual generation index aliases with zero-downtime hot-swapping.
  - Index Access Layer contract adhering to 01 §5.4.
