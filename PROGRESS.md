# PROGRESS.md — Build State

## Current State: Session S07 Complete (Retrieval, Q&A with claims pinned to anchors, source viewer; Demo 1)

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
- Corpus execution results across 156 distinct source PDFs (154 eligible documents, 2 quarantined skipped):
  - Total citations persisted to `plc.citation_mention`: 1,086 (avg 7.05 per doc; 0 rows from non-latest runs)
  - Citations by scheme: SCC: 459 | CASE_NO: 393 | SCC_ONLINE: 143 | NEUTRAL_INSC: 37 | AIR: 33 | SCR: 15 | NEUTRAL_HC: 6
  - Citations honest resolution status:
    - `RESOLVED_CORPUS` (matched real corpus work): 0 (expected for initial single-source IBBI corpus)
    - `STUB_CREATED` (STUB work or case minted): 962
    - `UNRESOLVED` (court unstated on bare case number): 124
  - Statute mentions found: 4,990 (100% resolved as "not in MVP corpus")
  - Degraded citations flagged: 3 (due to `ocr_conf < 0.80` or hidden text)
- Root cause of duplicate works resolved: `parse_captured` now looks up existing work for the same raw blob and passes `existing_work_id` and `supersedes_parse_id`. For `CHANGED` captures where the raw blob changed, it looks up earlier captures by `source_record_key` and aligns against the existing work, preserving surviving anchors and marking deleted paragraphs as `TOMBSTONED`. Idempotency and tombstoning verified by `backend/parse/tests/test_parse_captured_idempotency.py`.
- 346 duplicate works retired via `manage.py retire_duplicate_works` in a single atomic transaction: all marked `status='MERGED'` with `merged_into=canonical_work_id`, recorded in `plc.identity_merge_ledger` with reason `'REPARSE_DUPLICATE_RAW_BLOB'` (confidence 1.0), manifestations re-pointed, 346 CloudEvents emitted to `ops.event_outbox`, and 0 deletions. Confirmed 0 citations and 0 aliases pointing to duplicate works.
- Reproducible real corpus citation tests: 6 public fixture PDFs added to `eval/fixtures/ibbi/` (plus existing `nclat_born_digital_del.pdf`). `test_real_corpus_citations.py` parses fixture PDFs live through `ParsingPipeline`, locates anchors, asserts snippets within anchor text, and verifies extraction against hand-written expectations.

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
#### O. Citations: Extraction, Resolution & Deduplication (Session S05b: `backend/parse/citations/`)
- **Citation Extractor (`backend/parse/citations/extractor.py`):**
  - Robust regex grammar extracting SCC, SCC OnLine, AIR (including multi-word Supreme Court), SCR, INSC neutral citations, High Court neutral citations, NCLT CP (IB), NCLAT Company Appeal, and bare case numbers.
  - Generates `QuoteSelector` (prefix, exact, suffix) for resilient re-anchoring.
  - Extracts pinpoint locators (`page`, `para`, `unknown`).
  - Temporal sanity checks: flags citations dated after the citing order's decision date (`CITED_AFTER_CITING`).
  - Flags degraded mentions (`ocr_conf < 0.80` or `is_hidden`).
- **Statute Mentions (`backend/parse/citations/statutes.py`):**
  - Regex grammar for statutory sections, subsections, and Constitution articles.
  - Extracts in-document definitions (`extract_in_document_definitions`, e.g. `"the Code"` -> IBC 2016).
  - Point-in-time rules (`AS_CITED` vs `NO_EXPRESSION`).
  - Corpus-only resolution: returns `resolved_anchor_ids = []` and `resolution_status = "not in MVP corpus"` (zero false positives or external law fabrication).
  - Zero new SQL tables for statute mentions (persisted strictly inside new `ParsedDocument` objects with bumped `pipeline_version = "p1.citation@0.1.0|det_v1"` in S3).
- **AuthorityView Citation Resolver & Alias Lifecycle (`backend/parse/citations/resolver.py`):**
  - Resolves mentions against `plc.identifier_alias` honoring trust tier hierarchy (`T0 > T1 > T2 > T3 > T4`).
  - Pinned self-minted STUB aliases to `T4` trust tier (`source = "citation_mention"`, `evidence = {mention_id, citing_work_id, anchor_id}`).
  - Resolves reporter citations to STUB `Work`; resolves case numbers to `LegalCase` with STUB case (not STUB judgment work).
  - Leaves case numbers without court context `UNRESOLVED` (`target_id = None`) without alias or STUB.
  - Promotes authoritative aliases upon arrival: supersedes `T4` row, merges STUB into real work via `plc.identity_merge_ledger`, re-points mentions, and emits `plc.identity.merged.v1` and `plc.acquire.requested.v1`.
- **Deduplication & Auto-Merge Engine (`backend/parse/citations/dedupe.py`):**
  - Exact-match auto-merge: auto-merges only when court, normalized case number, and decision date match 100% exactly.
  - Reversible merge via `split_work()` emitting `plc.identity.split.v1`.
- **Corpus Resolution Run & Quality Report (`eval/reports/s05b_quality.txt`):**
  - Evaluated across 154 distinct eligible documents (2 quarantined skipped = 156 distinct PDFs).
  - Total citations persisted to `plc.citation_mention`: **1,086** (average 7.05 per doc).
  - Citations breakdown by scheme:
    - SCC: 459 | CASE_NO: 393 | SCC_ONLINE: 143 | NEUTRAL_INSC: 37 | AIR: 33 | SCR: 15 | NEUTRAL_HC: 6.
  - Citations honest resolution status (Directive #2):
    - `RESOLVED_CORPUS`: 0 (0.0% — honest status; zero cited judgments exist in initial MVP corpus)
    - `STUB_CREATED`: 962 (88.6% — STUB works for reporters, STUB cases for case numbers)
    - `UNRESOLVED`: 124 (11.4% — case numbers without court stated, left un-stubbed)
  - Statute mentions: 4,990 found across 154 docs (avg 32.40 per doc) — 100% "not in MVP corpus".
  - Quality degradation flags: 3 citations degraded (`ocr_conf < 0.80`), 0 statute mentions degraded.
- **Test Suite (`backend/parse/tests/`):**
  - 39 new tests for S05b, **200 total passed** across backend (1 skipped: real LLM smoke):
    - `test_real_corpus_citations.py`: 13 tests asserting citation extraction against real parsed IBBI corpus anchors across SCC, SCC OnLine, INSC, AIR, and case numbers with hand-written expected citations, pin, normalized keys, and real negative cases.
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

# Type check (strict repo-wide across all 173 source files)
uv run mypy .

# Lint & formatting check
uv run ruff check .
uv run ruff format --check .

# Run all 200 backend tests against PostgreSQL 18
uv run pytest

# Extract and resolve citations across distinct source PDFs
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

### 2. Session S06 Implementation Details (Index: Chunks, FTS, pgvector, Generations & IAL)

#### A. Database Schema & Migrations (`backend/index/migrations/`)
- `0001_fts_legal_en.py`: text search configuration `public.legal_en` (copied from `english`).
- `0002_ops_index_tables.py`: `ops.index_generation` and `ops.index_alias` with foreign keys and check constraints.
- `0003_chunk_tables.py`: `plc.chunk` partitioned table by list (`index_generation`), with partition `plc.chunk_g1`, HNSW index on `((embedding::halfvec(1024)) halfvec_cosine_ops)`, GIN on `tsv`, GIN on `binding_scope_tags`, B-tree on `work_id`.
- `0004_expression_state.py`: `plc.index_expression_state` table tracking `serial_key`, `accepted_parse_id`, `doc_seq`, `content_digest`, `enrichment_level`, `status` (`ACTIVE`, `QUARANTINED`, `SUPERSEDED_REV`, `REKEYED`), `last_quarantined_parse_id`, `quarantine_reasons`, `pipeline_version`, and `updated_at`.
- `0005_summary_table.py`: `plc.summary` non-citable digest table.
- `0006_private_chunk.py`: `tpl.private_chunk` table with forced RLS and tenant isolation policy (`current_setting('app.tenant_id')`), with partial HNSW index on `g1`.
- `0007_seed_index_records.py`: seeds pipeline versions (`p2.chunker@0.1.0|det_v1`, `p2.embedder@0.1.0|approx_tok_v1|voyage-4-large|1024`, `p2.index@0.1.0|g1`), provisional `g1` in `ops.index_generation` (`state='BUILDING'`), model endpoint `ep_voyage_4_large`, and subscriptions.
- `0008_grants.py`: grants on index tables to `app_rw`, `worker`, `plc_writer`.
- `0009_fix_voyage_endpoint_and_subscriptions.py`: sets `ep_voyage_4_large` processing and storage geo to `US` to preserve tenant residency fail-closed checks; deduplicates index event subscriptions to canonical CloudEvent types (`doc.parsed.v1`, `identity.merged.v1`, `identity.split.v1`).

#### B. Legal Normalizer & Lexeme Emission (`backend/index/normalizer.py`)
- Regex-based extraction of legal entities:
  - Section paths: `138(1)(a)`, `7(5)`, `s. 9`, `u/s 9` with ancestor emission (`s138`, `s138_1`, `s138_1_a`).
  - Penal combos: `302/34`, `420/120B` (`s302`, `s34`, `s302_34`).
  - Constitutional articles: `Art. 21A` (`art21`, `art21a`).
  - Procedural abbreviations: `u/s` (`lex_u_s`), `r/w` (`lex_r_w`).
  - Case numbers: `CP(IB) 149 of 2023`, `CP(IB) No. 1234/MB/2019`, `Company Appeal (AT)`.
  - Neutral citations: `SCC`, `AIR`, `INSC`, `SCR`.
- Indexed at weight C via `setweight(array_to_tsvector($lexemes::text[]), 'C')`.
- Query parsing combines quoted tsquery terms for lexemes with `websearch_to_tsquery('public.legal_en', ...)` for remaining prose.

#### C. Legal Chunker (`backend/index/chunker.py`)
- `StructureChunker`:
  - `JUDG_HEADER`: header chunk from title and court metadata.
  - `SHORT_ORDER_WHOLE`: whole order if total tokens <= 700.
  - `JUDG_PARA_GROUP`: paragraphs grouped along soft token boundaries (120–550 tokens).
  - `JUDG_LONG_PARA_PART`: paragraphs exceeding hard max (900 tokens) split into parts under the parent paragraph anchor with `body.part = {"k": k, "n": n, "char_start": s, "char_end": e}` (Directive #3).
  - `JUDG_OPERATIVE_ORDER`: operative order chunk.
- Deterministic chunk ID minting (`mint_deterministic_chunk_id`) hashing `tenant_id|expression_ref|chunk_kind|first_anchor|last_anchor|chunker_version`.
- Disambiguation: sequential `part_k` counters for identical `(chunk_kind, first_anchor, last_anchor)` tuples within a document to prevent PK collisions.
- Strictly validates Invariants I1–I6 (coverage, contiguity, token bounds, part reconstruction, registry binding scope tags).

#### D. Index Generations & Hot-Swapping (`backend/index/generations.py`)
- `create_generation_partition(index_family, generation)`: dynamically creates partition table `plc.chunk_<gen>` with HNSW index, GIN indexes, and B-tree indexes.
- `promote_generation(index_family, to_generation, reason)`: atomic promotion swap updating `ops.index_alias` and setting generation state to `LIVE`, emitting `index.generation.promoted.v1` to `ops.event_outbox`.
- `rollback_generation(index_family)`: restores previous generation from alias history.

#### E. Index Access Layer (`backend/index/ial.py`)
- Single-leg retrieval only (`LEXICAL` or `DENSE`), returning raw, uncalibrated scores (`GREATEST(ts_rank_cd, ts_rank)` or cosine similarity `1 - distance`). Rejects hybrid mode with `ValueError` (fusion belongs to P5 / S07).
- Supported filters: `court_ids`, `court_levels`, `doc_types`, `decided_on_or_before`, `decided_on_or_after`, `binding_scope_tags_any`, `work_ids`, `rights_classes`, `trust_labels`, `min_quality_gate`.
- `get_chunks(ids, generation)`: raises `GenerationGone` carrying `anchor_ids` if generation is in state `RETIRED` or `ROLLED_BACK`.
- `get_neighbours(anchor_id, before, after)`: retrieves contiguous surrounding chunks.
- Dense search uses `SET LOCAL hnsw.ef_search = 100` and matches expression index `((embedding::halfvec(1024)) <=> %s::halfvec(1024))`.

#### F. Ingestion & Event Consumer (`backend/index/consumer.py` & `backend/index/indexer.py`)
- Subscribes to:
  - `doc.parsed.v1`: triggers structural chunking, vector embedding, and atomic DB insertion.
  - `identity.merged.v1`: tombstones chunks for duplicate work, updates `index_expression_state` to `REKEYED`, and emits `plc.chunk.removed.v1`.
  - `identity.split.v1`: re-indexes survivor works and restores split targets.
- Monotonic `doc_seq` assignment and ULID parse timestamp check to drop out-of-order/stale events.

---

### 3. Verification & Commands
```bash
# Apply index migrations
uv run python manage.py migrate index --database=owner

# Test migration reversibility
uv run python manage.py migrate index zero --database=owner
uv run python manage.py migrate index --database=owner

# Run index tests (31 tests)
uv run pytest index/

# Run full backend test suite (242 tests)
uv run pytest

# Check code formatting and typing
uv run ruff check index gateway
uv run mypy index gateway

# Index corpus with local fake embedder (no real API calls)
uv run python manage.py index_corpus --generation g1

# Promote g1 to LIVE
uv run python manage.py swap_index_alias --family plc_chunks --to-generation g1 --reason "S06_PROMOTION"
```

---

### 4. Corpus & Exit Check Output
- **Corpus Indexing Results:**
  - Canonical expressions indexed: 154
  - Total chunks inserted into `plc.chunk_g1`: 2,706
  - Quarantined: 2 (Invariant I1 anchor coverage violations)
  - Active index expression states: 154
  - Chunks with duplicate or out-of-order anchors: 0 (verified 100% clean across all 2,706 rows)
- **Exit Check Queries (IAL against promoted `g1`):**
  - **Query `CP (IB) 6/MB/2023`:** 0 hits (strictly does not match restoration petition `RCP (IB)`).
  - **Query `RCP (IB) 6/MB/2023`:**
    - Hit 1: `chk_5K88NHJWQMZ4WM29YAMZY0T28S` (`wrk_01M3Y2TKNSKABZEC0BKMN4ZBDM/en#p16–p18`, score=0.4000)
      - Text: *"18. In view of the above, the Section 7 application, RCP (IB) 6/MB/2023, is restored to its original number."*
  - **Query `section 7` (differentiated scores & tiebreak):**
    - Hit 1: `chk_8BDQDH199ZKMX084BSMJGCMH6F` (`wrk_01M3Y2VEG8THQJKN5YB145XX06/en#p129`, score=3.3422)
    - Hit 2: `chk_3R3AJ12902FZ2PY3AYN0E1ANHV` (`wrk_01M3Y2VC850YSD3QE4NY90FN3Q/en#p36–p38`, score=2.6392)
    - Hit 3: `chk_EBC5DEE6GQQRPFMRZ581K3K8XK` (`wrk_01M3Y2VEG8THQJKN5YB145XX06/en#p32–p36`, score=2.4609)
    - Hit 4: `chk_JEW20BQMQX9S647KN0ECDZG47M` (`wrk_01M3Y2VRR5268SKTX4GKDW97C7/en#p6`, score=2.1419)
    - Hit 5: `chk_MSKKMFZ7P0JR0E2VX95RMFB3HH` (`wrk_01M3Y2VW60C8S73617APFN9PTV/en#p6`, score=2.1419)
  - **Query `CP(IB) 149 of 2023`:**
    - Hit 1: `chk_98A1XHY356M0BH2CJGD3PBWNZ4` (`wrk_01M3Y2TJ29AV6V8P7KZ33HNK33/en#p5–p8`, score=0.0608)
    - Hit 2: `chk_949FYB3EED6552JEZ7Y4XZP6QW` (`wrk_01M3Y2V5PEBHAYFF943QYGQ00M/en#p5–p7`, score=0.0608)
    - Hit 3: `chk_E9RQC0D3573Y3EJH2ZH5SH5DAA` (`wrk_01M3Y2V5PEBHAYFF943QYGQ00M/en#p14–p16`, score=0.0608)

---

### 5. Session S07 Implementation Details (Retrieval P5, Strategic Reasoning P6, Verification P8, Surface P10)

#### A. Database Schemas, Tables & Migrations
- **Phase P5 Retrieval (`backend/retrieve/migrations/0001_initial_retrieve_tables.py`):**
  - Created `tpl.research_query` (`qry_`) with tenant isolation RLS, forum, mode (`QUICK`, `STANDARD`, `DEEP`), and verification link.
  - Created `tpl.evidence_bundle` (`evb_`) storing typed retrieved items, coverage analysis, and pipeline version `p5.retriever@0.1.0|lexical_v1`.
- **Phase P6 Strategic Reasoning (`backend/reason/migrations/0001_initial_reason_tables.py`):**
  - Created `tpl.claim` (`clm_`) with tenant isolation RLS, claim types (`LEGAL_PROPOSITION`, `RECORD_FACT`, `PROCEDURAL`, `STRATEGIC_OPINION`), support array with anchor IDs and quotes.
  - Registered `p6.reasoner@0.1.0|qa_synthesis_v1` in `ops.pipeline_version`.
  - Registered ModelTaskContract `p6.qa_synthesis@1` with input/output schemas and seeded endpoints `ep_fake_qa` and `ep_claude_sonnet_3_5`.
- **Phase P8 Verification (`backend/verify/migrations/0001_initial_verify_tables.py`):**
  - Created `tpl.verification_report` (`vr_`) with gate (`PASS`, `PARTIAL`, `BLOCK`), withheld claim IDs, degradations, and verifier version `p8.verifier@0.1.0|ladder_c0_c2_v1`.
  - Created `tpl.claim_verification` with warrant checks (`exists`, `quote_exact`, etc.), display bands (`VERIFIED`, `VERIFIED_WITH_CAVEAT`, `CHECK`, `WITHHELD`), and `confidence_stratum = 'UNCALIBRATED_PREVIEW'`.
  - All migrations applied cleanly and tested reversible.

#### B. Domain Engines & Contracts
- **P5 Retrieval Engine (`backend/retrieve/retriever.py`):**
  - High-fidelity single-leg lexical search over `plc_chunks` via Index Access Layer.
  - Dynamically computes `law_current_to` from `plc.capture` (`2026-10-02`) rather than hardcoding.
  - Honest contrary authority sweep: reports status `LIMITED` (`"lexical only, no citator"`).
  - Emits `INDEX_LAG` degradation note disclosure.
- **P6 Strategic Reasoning Synthesizer (`backend/reason/synthesizer.py`):**
  - Delimited untrusted chunk blocks (`<source_chunk>`) with strict prompt-injection isolation.
  - Forbids stating statute content unless quoted verbatim from a retrieved anchor.
  - Out-of-corpus honest handling: immediately returns `in_corpus=False` with "not in MVP corpus" and zero claims.
  - Mints `tpl.claim` rows pinned to anchor IDs and verbatim quote selectors.
- **P8 Verification Engine (`backend/verify/verifier.py`):**
  - Deterministic warrant checks C0 (JSON schema), C1 (existence in `plc.anchor`), C2 (exact quote substring).
  - Closed-world bundle constraint: rejects any anchor not present in this query's `EvidenceBundle` (`OUT_OF_BUNDLE`).
  - Assigns display band `"quote verified · uncalibrated preview"`.
- **P10 Surface REST API (`backend/surface/router_research.py`):**
  - `POST /api/research/query`: End-to-end research query execution with authz and RLS enforcement.
  - `GET /api/research/documents/anchor?anchor_id=...`: Point-to-source pinpoint anchor resolution.
  - `GET /api/research/documents/{work_id}/source`: Document paragraph sequence viewer.

#### C. Frontend UI & Source Viewer
- **Typed API Client (`frontend/src/api/client.ts`):** `executeResearchQuery()`, `fetchAnchorSource()`, and `fetchDocumentSource()`.
- **Source Viewer (`frontend/src/components/SourceViewer.tsx`):** Slide-over modal with primary court header, OCR confidence badge, auto-scroll to pinpoint anchor, and high-contrast yellow quote highlighting (`<mark>`).
- **Research Q&A Page (`frontend/src/pages/ResearchPage.tsx`):** Complete UI with 4 pre-configured demo chips (Section 7, Section 9/10A, Section 14, and Admiralty out-of-corpus), executive summary card labeled with `summary_status` badge, proposition cards with `"quote verified · uncalibrated preview"`, contrary sweep card, and dynamic lineage footer.

---

### 6. Corpus & Exit Check Demonstration Output

Ran `eval/run_s07_exit_check.py` against the real database and Model Gateway (demonstrating gateway router-level 429 failover from `ep_gemini_3_8_flash` to `ep_gemini_3_5_flash` and audited `LLMCallRecord` capture):

> [!NOTE]
> **Exit-Check Annotation & Router Failover:**
> Earlier runs utilized an internal fallback loop in `google_adapter.py`. This was refactored: all silent adapter-level fallbacks were removed, and the Gateway Router (`backend/gateway/runner.py`) now explicitly handles failovers across qualified endpoints upon encountering HTTP 429 (`RateLimitError`). The exit check below demonstrates live 429 quota exhaustion on `ep_gemini_3_8_flash` (free tier daily quota) immediately triggering clean failover to `ep_gemini_3_5_flash`, with each `LLMCallRecord` recording the exact endpoint (`ep_gemini_3_5_flash`) and model (`gemini-3.5-flash`) actually invoked.
>
> Furthermore, anchor `wrk_01M3Y2TMYE567QN84SXM3431NZ/en#p2012` was investigated and diagnosed: a multi-page SCC citation `(2012) 3 SCC (Cri) 241]` was previously misparsed as a paragraph number. The judgment parser was upgraded with strict sequential/plausible numbering constraints (rejecting 4-digit years and citations).
>
> **Full Corpus Re-parse & Tombstone Counts:**
> Re-parsed all 157 captures across the corpus using the updated `judgment.py` rules:
> - **Works Re-parsed:** 156 distinct works.
> - **Anchors Tombstoned:** 163 spurious anchors eradicated (citation years like `#p2012`, `#p2010`, `#p1954`, `#p2023`, `#p2014`, `#p2018`, phone numbers, etc.).
> - **Tombstones with `forward_to`:** 82 (e.g. `#p2012` forwarded to `#p39`, `#p2010` forwarded to `#p125`).
> - **Tombstones without `forward_to`:** 81 (dissolved fragments/unmapped deleted numbers).
> - **Corpus Indexing:** Re-indexed 154 works (2710 chunks) cleanly into index generation `g1`.
> - **Executive Summary:** Flagged `unverified summary` across API and UI.
> - **Synthesis Prompt:** Atomic claims enforced (one proposition per claim, no joining with "as/because/therefore", rules and exceptions split into separate claims).

```
================================================================================
SESSION S07 EXIT CHECK DEMO: RESEARCH Q&A WITH PINPOINTED CLAIMS
================================================================================
[*] Tenant: ten_01M3DEMOTENANT0000000000 (Partner Law Firm LLP)
[*] Actor: partner.lawyer@firm.in (Role: PARTNER)
[*] Law current to: 2026-10-02 (dynamically derived from plc.capture)
--------------------------------------------------------------------------------

[DEMO RUN #1] Q1_SECTION_7
Question: "What is the scope of enquiry under Section 7 of the IBC for a financial debt and default?"
  -> P5 Retrieval: 2 evidence chunks retrieved (bundle_id: evb_01M4KDJR5JAJV2QF5ZA3SE4DJP)
  -> Router Failover: ep_gemini_3_8_flash 429 RESOURCE_EXHAUSTED -> failed over to ep_gemini_3_5_flash
  -> P6 Synthesis: in_corpus=True, claims_count=1
  -> Gateway Call: Endpoint=ep_gemini_3_5_flash | Model=gemini-3.5-flash | Provider=google
     LLMCallRecord ID: 01M4KDJYTT3QTA40JW3B7T3ASS (Tokens: in=1181, out=286)
  -> P8 Verification: gate=PASS, withheld=0
  -> Executive Summary: Under Section 7 of the IBC, the scope of enquiry involves determining the existence of a financial debt and the occurrence of default, as well as verifying the anterior issue regarding the authority of the petitioner to invoke insolvency jurisdiction.
    Claim [clm_01M4KDJYTZY3KWR7VB30XTMEB4]:
      Text:   The scope of enquiry under Section 7 of the Insolvency and Bankruptcy Code requires examining the existence of a financial debt and the occurrence of default, alongside anterior questions regarding the authority of the petitioner to invoke insolvency jurisdiction.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2VN62VEPM3MH330JF3VKD/en#p7
      Quote:  "Has the Adjudicating Authority overstepped the scope of enquiry when it is required to examine merely the existence of a financial debt and the occurrence of default; (b) the other is an anterior question and it relates to the authority of the petitioner invoking the insolvency jurisdiction"
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2VN62VEPM3MH330JF3VKD)
  -> Contrary Sweep: STATUS=LIMITED (lexical only, no citator)

[DEMO RUN #2] Q2_SECTION_9_10A
Question: "Can an operational creditor invoke Section 9 for default during the Section 10A period?"
  -> P5 Retrieval: 1 evidence chunks retrieved (bundle_id: evb_01M4KDJYW7WSAA6C8WJ9QJRC2J)
  -> Router Failover: ep_gemini_3_8_flash 429 RESOURCE_EXHAUSTED -> failed over to ep_gemini_3_5_flash
  -> P6 Synthesis: in_corpus=True, claims_count=2
  -> Gateway Call: Endpoint=ep_gemini_3_5_flash | Model=gemini-3.5-flash | Provider=google
     LLMCallRecord ID: 01M4KDK2J2F43MG5D1TNTP8DX5 (Tokens: in=646, out=484)
  -> P8 Verification: gate=PASS, withheld=0
  -> Executive Summary: An operational creditor cannot invoke Section 9 of the IBC for a default occurring within the Section 10A protected period. Continued non-payment or subsequent acknowledgement of debt after the period expires does not shift the default date, and amounts arising from a Section 10A-protected default must be excluded when assessing CIRP initiation requirements.
    Claim [clm_01M4KDK2J5F9DVG4KH1T98EVCB]:
      Text:   An Operational Creditor is prohibited from initiating a Section 9 application for a default that occurred during the Section 10A statutory bar period.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2VRFJGZAF26VMB4236ZFS/en#p3.9
      Quote:  "an Operational Creditor cannot invoke Section 9 in respect of a default which falls within the statutory prohibition merely because the debt subsequently continued to remain outstanding or was subsequently acknowledged."
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2VRFJGZAF26VMB4236ZFS)
    Claim [clm_01M4KDK2JDDMBD4R73PRB9WFZJ]:
      Text:   The continuation of non-payment post the Section 10A period or subsequent acknowledgment does not alter the original default date occurring within the protected period, and amounts arising from a protected default cannot be considered to fulfill CIRP initiation requirements.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2VRFJGZAF26VMB4236ZFS/en#p3.9
      Quote:  "Continuation of non-payment after expiry of the Section 10A period does not shift the original default occurring during the protected period to a later date so as to overcome the statutory bar.The principle emerging from the aforesaid judgment is that a creditor cannot rely upon an amount arising from a Section 10A-protected default for satisfying the statutory requirements governing initiation of CIRP."
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2VRFJGZAF26VMB4236ZFS)
  -> Contrary Sweep: STATUS=LIMITED (lexical only, no citator)

[DEMO RUN #3] Q3_SECTION_14_NI
Question: "Does moratorium under Section 14 of IBC apply to Section 138 NI Act proceedings?"
  -> P5 Retrieval: 10 evidence chunks retrieved (bundle_id: evb_01M4KDK2QDWRQJX4FXGPTB4ZS6)
  -> Router Failover: ep_gemini_3_8_flash 429 RESOURCE_EXHAUSTED -> failed over to ep_gemini_3_5_flash
  -> P6 Synthesis: in_corpus=True, claims_count=4
  -> Gateway Call: Endpoint=ep_gemini_3_5_flash | Model=gemini-3.5-flash | Provider=google
     LLMCallRecord ID: 01M4KHNWX5K51DSJC26HQB8TYZ (Tokens: in=3653, out=674)
  -> P8 Verification: gate=PASS, withheld=0
  -> Executive Summary: Under the Insolvency and Bankruptcy Code (IBC), the moratorium provision under Section 14 applies exclusively to the corporate debtor entity itself and does not cover criminal proceedings or shield natural persons (such as directors) from their personal statutory liability under Section 138 of the Negotiable Instruments Act, 1881.
    Claim [clm_01M4KHNWXBVKHJC292JV8DG55X]:
      Text:   The moratorium under Section 14 of the IBC applies solely to the corporate debtor.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2TMYE567QN84SXM3431NZ/en#p27
      Quote:  "the moratorium provision contained in Section 14 IBC would apply only to the corporate debtor"
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2TMYE567QN84SXM3431NZ)
    Claim [clm_01M4KHNWXG3BNHGV11HM56GW98]:
      Text:   Natural persons remain statutorily liable under the Negotiable Instruments Act, 1881, notwithstanding the corporate debtor's moratorium under Section 14 of the IBC.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2TMYE567QN84SXM3431NZ/en#p27
      Quote:  "the natural persons mentioned therein, continuing to be statutorily liable under the NI Act, 1881"
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2TMYE567QN84SXM3431NZ)
    Claim [clm_01M4KHNWXKGSPDBFGAXY9MB75C]:
      Text:   The moratorium provided under the IBC does not extend to criminal proceedings.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2TMYE567QN84SXM3431NZ/en#p27
      Quote:  "the moratorium under IBC does not extend to criminal proceedings"
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2TMYE567QN84SXM3431NZ)
    Claim [clm_01M4KHNWXNTEAPXPPQXDNGET0F]:
      Text:   Personal statutory liability under Section 138 of the Negotiable Instruments Act, 1881, continues to bind natural persons irrespective of any moratorium applicable to the corporate debtor.
      Status: VERIFIED | Band: "quote verified · uncalibrated preview"
      Anchor: wrk_01M3Y2V16518DGSHGHCARB4SH6/en#p13
      Quote:  "The statutory liability against the directors under Section 138 of the N.I. Act, 1881, is personal and hence, continues to bind natural persons, irrespective of any moratorium applicable to the corporate debtor."
      Corpus Check: ✓ Exists in plc.anchor (Work: wrk_01M3Y2V16518DGSHGHCARB4SH6)
  -> Contrary Sweep: STATUS=LIMITED (lexical only, no citator)

[DEMO RUN #4] Q4_OUT_OF_CORPUS
Question: "What are the rules for maritime salvage under the Admiralty Act 2017?"
  -> P5 Retrieval: 0 evidence chunks retrieved (bundle_id: evb_01M4KDK6BV60GSYV79F2VDZ0FS)
  -> P6 Synthesis: in_corpus=False, claims_count=0
  -> Gateway Call: Skipped (honest out-of-corpus gate halted before LLM call)
  -> P8 Verification: gate=PASS, withheld=0
  -> Executive Summary: The requested topic was not found in the MVP corpus. Out of corpus means 'not in MVP corpus', not that the legal proposition is incorrect.
    Honest Negative Output: "The requested topic was not found in the MVP corpus. Out of corpus means 'not in MVP corpus', not that the legal proposition is incorrect."
    Claims minted: 0 (Honest zero-hallucination compliance)
  -> Contrary Sweep: STATUS=LIMITED (lexical only, no citator)

================================================================================
EXIT CHECK SUMMARY SCORECARD
================================================================================
  - Q1_SECTION_7: in_corpus=True, claims=1, gate=PASS
  - Q2_SECTION_9_10A: in_corpus=True, claims=2, gate=PASS
  - Q3_SECTION_14_NI: in_corpus=True, claims=4, gate=PASS
  - Q4_OUT_OF_CORPUS: in_corpus=False, claims=0, gate=PASS

================================================================================
SESSION S07 EXIT CHECK COMPLETED SUCCESSFULLY
================================================================================
Verified Checks Executed:
  ✓ Real Gateway Endpoint Execution (ep_gemini_3_8_flash / ep_gemini_3_5_flash)
  ✓ Audited LLMCallRecord Generation with Token Metering
  ✓ P5 Lexical Retrieval with Dynamic Law Current Date (plc.capture)
  ✓ In-Corpus vs Honest Out-of-Corpus Negative Grounding Gate
  ✓ Verifier Ladder C0: Schema & Typing Integrity
  ✓ Verifier Ladder C0: Closed-World EvidenceBundle Boundary (OUT_OF_BUNDLE rejection)
  ✓ Verifier Ladder C1: Anchor Existence in Public Corpus (plc.anchor)
  ✓ Verifier Ladder C2: Exact Quote Substring Match (NFC Normalized)
  ✓ Verifier Ladder C2: Role Check for Party Submissions (C2_role_submission)
  ✓ Contrary Authority Sweep Status (LIMITED: lexical only, no citator)
================================================================================
```

- **Backend Test Suite:** 263 passed, 1 skipped, 0 failed in 32s.
- **Lint & Types:** Ruff clean (0 errors), mypy clean (0 errors across 237 source files).
- **Frontend Test Suite & Build:** Vitest 3 passed, ESLint clean (0 errors), `pnpm build` clean bundle in 827ms.

---

### 7. Stubs & Notes
- **Dense Retrieval Deferred:** Single-leg lexical search active for S07 (generation `g1` holds fake embeddings to save dev cost). Real Voyage generation `g2` will be built in Session S08 under partner approval.
- **Citator Doctrine Rules:** Adverse treatment graph propagation and citator badges deferred to Session S09; contrary sweep honestly reports `LIMITED ("lexical only, no citator")`.

---

### 8. What the Next Session (S08) Needs
- **Session S08: Eval harness + gold store + real Voyage generation build:**
  - Gold store loader and runner (`eval/`).
  - Scorecard generation across legal question gold suites.
  - Zero-tolerance gates for hallucination, statute fabrication, and out-of-corpus handling.
  - Promotion of real Voyage embeddings generation `g2`.


