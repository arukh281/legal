# DECISIONS.md — Architecture & Implementation Decisions

Record of decisions made during the build. Every entry has: date, decision, reason, and doc reference.

---

### 2026-10-01 — Dedicate `ops` Django Application for Operational Schema
- **Decision:** Created a dedicated `backend/ops` Django app owning the `ops` database schema, `pipeline_version`, outbox, event inbox, job chains, and operational models.
- **Reason:** AGENTS.md §3 lists phase apps, while `docs/mvp/03_data_model_and_contracts.md` §1 & §3.16 define a distinct `ops` schema containing cross-cutting operational infrastructure. Creating `ops` encapsulates outbox delivery, job chains, and pipeline versioning without coupling operational mechanics to any single domain phase.
- **Doc Reference:** AGENTS.md §3; `docs/mvp/03_data_model_and_contracts.md` §1, §3.1, §3.16.

---

### 2026-10-01 — PostgreSQL 18 with pgvector & Cluster Mount Configuration
- **Decision:** Pinned database container image to `pgvector/pgvector:pg18` and mapped the host data volume to `/var/lib/postgresql`.
- **Reason:** PostgreSQL 18 stores cluster files at `/var/lib/postgresql/18/docker/` in the official images. Volume mounting `/var/lib/postgresql` avoids breaking initialization while ensuring data persistence. Mapped container port 5432 to host port 5433 to avoid collision with local Homebrew PostgreSQL 16.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.1.

---

### 2026-10-01 — Immutable MinIO Image Tag
- **Decision:** Pinned MinIO to immutable digest `elestio/minio@sha256:25348a257f1ece1b192f25f6cd9854618fa86422ac87b494b5d4e629c556d4bd` (release `RELEASE.2025-09-07T16-13-09Z`).
- **Reason:** Docker Hub has deprecated unauthenticated pulls for legacy `minio/minio`. Pinning an immutable digest guarantees reproducible builds without `:latest` tags.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.1.

---

### 2026-10-01 — Django 5.2 LTS Version Pin
- **Decision:** Pinned `django>=5.2,<5.3` in `backend/pyproject.toml`.
- **Reason:** Strict compliance with the stack definition in `docs/mvp/04_stack_and_infra.md` §2.1.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.1.

---

### 2026-10-01 — Uvicorn ASGI Application Server
- **Decision:** Configured the `web` container to run `uvicorn core.asgi:application --host 0.0.0.0 --port 8000`.
- **Reason:** Guarantees production-grade ASGI serving, async compatibility for streaming responses, and avoids running Django `runserver` in containers.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.1; User Directive #7.

---

### 2026-10-01 — Atomic Consumer Side-Effect and Inbox Insertion in ONE Transaction
- **Decision:** Implemented `ops.outbox.process_event_delivery` such that the consumer handler and the `ops.event_inbox` insert execute within the same `transaction.atomic()` block.
- **Reason:** 03 §4 step 3 requires atomic execution so that if a handler fails, the inbox delivery record rolls back, ensuring true at-least-once delivery without phantom acks.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §4 step 3; User Directive #2.

---

### 2026-10-01 — Dedicated Test-Only Event Name for Demo Job Chain
- **Decision:** Configured the demo job chain to emit `ops.demo.completed.v1` on topic `plc.ops.demo.completed.v1` instead of `doc.parsed.v1`.
- **Reason:** Event names are immutable contracts. Emitting `doc.parsed.v1` from a test demo chain would violate contract boundaries and falsely signal parsed documents to downstream consumers.
- **Doc Reference:** `docs/mvp/00_mvp_spec.md` §2; `docs/01_master_architecture.md` §6.2; User Directive #3.

---

### 2026-10-01 — Psycopg 3 JSONB Deserialization via Connection Created Signal
- **Decision:** Connected `django.db.backends.signals.connection_created` in `ops.apps` to invoke `psycopg.types.json.register_default_adapters`.
- **Reason:** Raw cursor queries in psycopg 3 return raw strings for JSONB columns unless default adapters are registered on the underlying psycopg connection. Procrastinate requires JSON payloads to be deserialized into native Python dictionaries.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.1.

---

### 2026-10-01 — Procrastinate Worker Configured with `--no-listen-notify`
- **Decision:** Configured worker command to execute `python manage.py procrastinate worker --no-listen-notify --queues rt,bulk,dispatch`.
- **Reason:** Procrastinate's Django connector does not support synchronous `listen/notify` (`NotImplementedError`). Polling mode is robust and reliable across container boundaries.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.2.

---

### 2026-10-01 — Deliberate CHECK Constraints Added to `ops` Schema DDL
- **Decision:** Added three database CHECK constraints beyond the base DDL in 03 §3.16:
  1. `chk_outbox_traceparent` on `ops.event_outbox`: `CHECK (traceparent IS NULL OR traceparent ~ '^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$')`
  2. `chk_parked_reason` on `ops.event_parked`: `CHECK (reason IN ('IDEMPOTENCY_KEY_REUSE', 'MAX_RETRIES_EXCEEDED', 'UNHANDLED_EXCEPTION', 'SCHEMA_VALIDATION_FAILED'))`
  3. `chk_step_key` on `ops.job_step`: `CHECK (step_key ~ '^[a-f0-9]{32,64}$')`
- **Reason:** Defense-in-depth database enforcement. `chk_outbox_traceparent` guarantees W3C Trace Context spec compliance before any event is accepted into the outbox. `chk_parked_reason` constrains dead-letter entries to known operational error codes for automated triaging. `chk_step_key` guarantees that step replay keys are valid cryptographic hashes (32–64 hex digits), preventing unhashed or malformed strings from polluting deterministic replay caches.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.16, §4, §5; `docs/01_master_architecture.md` §6.1.

---

### 2026-10-01 — Local-Dev Only Usage of `elestio/minio` Image
- **Decision:** Pinned `elestio/minio` digest for local development in `infra/compose.yaml`.
- **Reason:** Docker Hub deprecated unauthenticated pulls for legacy `minio/minio`. This image is strictly for local Compose development and developer machines. Production relies solely on native AWS S3 in `ap-south-1` with Object Lock and SSE-KMS per 04 §0 and AGENTS.md §2; MinIO is never deployed to production.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §0, §2.1; AGENTS.md §2.

---

### 2026-10-01 — 2-Second Periodic Dispatcher Sweep Guarantee
- **Decision:** Configured `ops.outbox.dispatch_task` on queue `dispatch` to reschedule the next sweep after every execution using `schedule_in={"seconds": 2}` and `queueing_lock="outbox_dispatcher"`.
- **Reason:** Implements the required 2-second periodic sweep in 03 §4 step 2 without relying on listen/notify. Using `queueing_lock="outbox_dispatcher"` prevents duplicate runs from accumulating in the queue while guaranteeing that pending outbox rows (`SELECT ... FOR UPDATE SKIP LOCKED`) are processed within 2 seconds of insertion.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §4 step 2.

---

### 2026-10-01 — Monotonic Crockford ULID Generator with 80-Bit Entropy Counter
- **Decision:** Built a pure-Python, thread-safe monotonic Crockford ULID generator in `anchor_lib.ids` encoding 48-bit UNIX millisecond timestamps and 80-bit randomness with monotonic intra-millisecond entropy incrementing.
- **Reason:** AGENTS.md §5 and 01 §5.2 require domain IDs to be `prefix_` + 26-char Crockford ULID, strictly monotonic within a millisecond and strictly matching creation order.
- **Doc Reference:** AGENTS.md §5; `docs/01_master_architecture.md` §5.2; `docs/mvp/03_data_model_and_contracts.md` §1 item 2.

---

### 2026-10-01 — Deconstructible `IDMinter` for `PrefixedULIDField`
- **Decision:** Implemented `@deconstructible class IDMinter` instead of a lambda function as the default callable on `PrefixedULIDField`.
- **Reason:** Django migrations fail to serialize lambda expressions into migration files. A deconstructible callable serializes cleanly into migration definitions.
- **Doc Reference:** Django migration framework; User Directive #2.

---

### 2026-10-01 — Dynamic Documentation Parity Test for Prefix Registry and Mnemonics
- **Decision:** Added automated tests reading the markdown table and text of `docs/01_master_architecture.md` §5.2 directly to verify that `PREFIX_REGISTRY` (all 64 entity prefixes) and `MNEMONIC_PREFIXES` (`crt`, `ent`, `rul`, `ter`) match documentation with zero drift.
- **Reason:** Prevents specification drift and verifies that no unapproved prefixes or non-canonical mnemonics can enter the codebase.
- **Doc Reference:** `docs/01_master_architecture.md` §5.2; User Directive #1.

---

### 2026-10-01 — Pure-Function Design for Semantic Constraints A3, A4, A5, and A8
- **Decision:** Implemented semantic constraints A3 (`resolve_pit`), A4 (`check_reconstructed_text`), A5 (`check_translation_support`), and A8 (`get_clause_hierarchy`) as pure functions accepting plain data structures and flags with zero database queries.
- **Reason:** Keeps `anchor_lib` stateless and portable across worker processes, API servers, and future client add-ins without database coupling. Downstream phase callers (S05, S13, S14) will wire these to live records.
- **Doc Reference:** `docs/01_master_architecture.md` §5.3; User Directive #7.

---

### 2026-10-01 — W3C TextQuoteSelector Conformance for Re-alignment
- **Decision:** Implemented `QuoteSelector(exact, prefix, suffix)` with up to 32 context characters and fuzzy disambiguation matching `docs/01_master_architecture.md §5.5` item 7 and `docs/mvp/03_data_model_and_contracts.md §3.4` (`quote_prefix`, `quote_suffix`).
- **Reason:** Ensures durable records (claims, memos, citations) can be re-aligned if underlying anchor IDs change during document re-parsing.
- **Doc Reference:** `docs/01_master_architecture.md` §5.5, §7.1; `docs/mvp/03_data_model_and_contracts.md` §1 item 6, §3.4.

---

### 2026-10-01 — Ethical Wall ID Prefix (`ewl`) as MVP Addition
- **Decision:** Added `ewl` to `MVP_PREFIX_ADDITIONS` in `backend/anchor_lib/ids.py` for `tpl.ethical_wall.wall_id`. The normative table in `docs/01_master_architecture.md §5.2` is preserved unchanged, and registry tests assert `PREFIX_REGISTRY == DOC_PREFIX_REGISTRY | MVP_PREFIX_ADDITIONS`.
- **Reason:** `docs/mvp/03_data_model_and_contracts.md §3.8` defines `tpl.ethical_wall` with `wall_id text NOT NULL` but leaves the prefix unspecified. User consultation and directive #1 approved `ewl_` as the designated prefix for ethical walls.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.8; `docs/01_master_architecture.md` §5.2; Session S03 Directive #1.

---

### 2026-10-01 — Unprefixed Crockford ULID for Model Gateway `call_id`
- **Decision:** Used unprefixed 26-character Crockford ULIDs for `ops.llm_call_record.call_id` minted via `mint_ulid()`.
- **Reason:** `docs/mvp/03_data_model_and_contracts.md §3.15` and `docs/01_master_architecture.md §7.24` define `call_id` without a prefix. User consultation and directive #1 confirmed that `call_id` is an unprefixed Crockford ULID rather than inventing a custom prefix.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.15; `docs/01_master_architecture.md` §7.24; Session S03 Directive #1.

---

### 2026-10-01 — Django 5.2 `CompositePrimaryKey` on Multi-Tenant Domain Models
- **Decision:** Used `django.db.models.fields.composite.CompositePrimaryKey` on all composite-keyed domain models (`AppUser`, `Matter`, `MatterMember`, `EthicalWall`, `WallExclusion`, `ActorPseudonym`, `ConsentRecord`, `AuditEvent`, `LLMCallRecord`).
- **Reason:** Matches verbatim PostgreSQL DDL from 03 §3.8, §3.9, and §3.15 (`PRIMARY KEY (tenant_id, ...)`) without artificially reducing the primary key to a single field on the Django model.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.8, §3.9, §3.15; Session S03 Directive #2.

---

### 2026-10-01 — Multi-Schema Table Quoting in Django ORM (`schema"."table`)
- **Decision:** Specified `db_table = 'tpl"."table_name'` for `tpl` models and `'ops"."table_name'` for `ops` models.
- **Reason:** Django's SQL compiler wraps `db_table` as `"{db_table}"`. Specifying `"tpl.table"` produces `"tpl.table"` (treated as a table name containing a period in the default search path). Quoting as `'tpl"."table'` compiles to `"tpl"."table"`, which correctly resolves schema-qualified tables across `tpl`, `plc`, and `ops`.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §1 item 1.

---

### 2026-10-01 — O(1) Audit Chain Head Table and Monotonic Sequence
- **Decision:** Upgraded audit event appending from a `row_hash NOT IN (SELECT prev_hash ...)` subquery to a dedicated `tpl.audit_chain_head` table and monotonic `seq bigint` column on `tpl.audit_event`, updated atomically under `pg_advisory_xact_lock(hashtext('audit_' || tenant_id))`. Added `verify_chain(tenant_id)` function.
- **Reason:** Scanning the audit log table to find unreferenced `prev_hash` values degrades from O(1) to O(N) as the log grows and risks ambiguity if two rows ever share a hash. A dedicated per-tenant chain head table provides instantaneous O(1) head lookups. The monotonic `seq` column guarantees strict deterministic sequencing, and `verify_chain()` allows complete end-to-end cryptographic verification of hash continuity and payload integrity.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.8; `docs/09_P7_firm_matter_workspace.md` line 723; Session S03 follow-up Directive #5.

---

### 2026-10-01 — Dedicated `admin_rw` Role for Django Admin Operations
- **Decision:** Created role `admin_rw NOINHERIT BYPASSRLS` for Django Admin / internal platform operations, completely separate from `app_rw` (which has `NOBYPASSRLS` and enforces RLS) and `worker` (which requires `app.purpose` logging).
- **Reason:** Under PostgreSQL `FORCE ROW LEVEL SECURITY` on `tpl` domain tables (`tenant`, `app_user`, `matter`), connecting as `app_rw` without an active `app.tenant_id` session setting produces 0 rows on `SELECT` and blocks `INSERT`. The Django Admin operates across all tenants to provision new tenants, assign global firm users, and inspect matters. Using a dedicated `admin_rw` connection ensures internal admin operations are explicit, audited, and strictly segregated from the public API server (`app_rw`).
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §1 item 1; Session S03 follow-up Directive #2.

---

### 2026-10-01 — Psycopg 3 JSON Adapter and Django JSONField Deserialization Patch
- **Decision:** Connected `django.db.backends.signals.connection_created` in `ops.apps` to register psycopg3 default adapters (`register_default_adapters`), and patched `models.JSONField.from_db_value` to gracefully pass through already-deserialized `dict` and `list` objects.
- **Reason:** Procrastinate's PostgreSQL driver directly queries raw psycopg3 connections and expects `args` and job payloads to be returned as native Python dictionaries. When psycopg3 default adapters are registered, psycopg3 deserializes `jsonb` columns into native Python dictionaries on retrieval. However, Django's default `models.JSONField.from_db_value` expects a string from the driver and calls `json.loads(value)`, raising a `TypeError` when passed a dictionary. The narrowly scoped pass-through in `_safe_from_db_value` preserves standard Django `JSONField` behavior (natively round-tripping `dict`/`list` objects without returning strings) while maintaining 100% compatibility with Procrastinate.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.1; Session S03 follow-up Directive #6.

---

### 2026-10-01 — Mypy Strict Overrides for `allauth.*` and `core.adapters`
- **Decision:** Added `[[tool.mypy.overrides]]` in `backend/pyproject.toml` for `allauth.*` (`ignore_missing_imports = true`) and `core.adapters` (`disallow_subclassing_any = false`), while preserving repo-wide `strict = true` across all 100 backend source files.
- **Reason:** `django-allauth` does not ship `py.typed` markers or stub packages. Custom adapters `LawyerBrainAccountAdapter` and `LawyerBrainSocialAccountAdapter` must subclass allauth's `DefaultAccountAdapter` and `DefaultSocialAccountAdapter`. Mypy strict mode disallows subclassing untyped `Any` bases unless explicitly permitted for those adapter modules. Repo-wide type checking (`uv run mypy .`) continues to enforce strict typing across all domain and infrastructure apps without exclusions.
- **Doc Reference:** AGENTS.md §2; Session S03 follow-up Directive #7.

---

### 2026-10-01 — Strict Startup Role and RLS Bypass Check
- **Decision:** Added Django system check `core.E004` that verifies at startup that the runtime database role is not a superuser and does not have `BYPASSRLS`.
- **Reason:** Superusers and roles with `BYPASSRLS` bypass PostgreSQL Row-Level Security even when `FORCE ROW LEVEL SECURITY` is enabled. The web API and workers must connect strictly as `app_rw` or `worker`.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §1 item 1; Session S03 Directive #3.

---

### 2026-10-01 — Model Gateway Routing with Residency and Data Class Ceilings
- **Decision:** Enforced `endpoint.data_class_max >= call.dataclass` and strict residency fail-closed check (`endpoint.residency_country == "IN"` when tenant policy is `IN_ONLY`) in `gateway.runner.pick_endpoint`.
- **Reason:** Guarantees that privileged or tenant-confidential requests never route to public or foreign-hosted models unless explicitly permitted by tenant policy.
- **Doc Reference:** `docs/mvp/04_stack_and_infra.md` §2.8, §2.13; `docs/01a_spine_decision_record.md` D14, D15; Session S03 Directive #8.

---

### 2026-10-02 — Worker Tenant-Scoped Jobs Elevate to `app_rw` via `SET ROLE`
- **Decision:** The `worker` role retains `BYPASSRLS` for cross-tenant system tasks (outbox dispatcher, PLC ingestion). All tenant-scoped work transitions to `app_rw` via `SET ROLE app_rw;` inside `tenant_db_context()`, ensuring RLS enforcement on tenant jobs. `GRANT app_rw TO worker;` enables this role switch.
- **Reason:** 03 §1 specifies `worker` with `BYPASSRLS`. However, tenant-scoped work (memos, matter parsing, alerts for one firm) must be RLS-protected. Rather than removing `BYPASSRLS` from `worker` (breaking outbox dispatch and PLC ingestion), scoped elevation to `app_rw` inside `tenant_db_context()` precisely constrains tenant-scoped jobs while preserving system-level access.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §1 item 1; Session S03 follow-up Directive #2.

---

### 2026-10-02 — Admin Connection Routing via `DatabaseRouter` and `admin_db_context()`
- **Decision:** Pre-authentication user/tenant lookups in `AuthzDependency`, `TenantContextMiddleware`, and `core.auth` use `admin_db_context()` (connecting as `admin_rw` with `BYPASSRLS`). The `DatabaseRouter` routes reads/writes to `admin` alias when the admin context is active.
- **Reason:** Before a user is authenticated, `app.tenant_id` is unknown and RLS blocks all queries on `tpl` tables. Admin lookups must bypass RLS to resolve the user's identity and tenant.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §1 item 1, §6; Session S03 follow-up Directive #1.

---

### 2026-10-02 — Custom `conftest.py` for Multi-Role Test Database Setup
- **Decision:** Overrode pytest-django's `django_db_setup` fixture in `backend/conftest.py` to: (1) create and migrate the test DB using only the `owner` alias (postgres), then (2) point `default` (app_rw), `admin` (admin_rw), and `worker` connections to the same test DB by name. This avoids Django's `MIRROR`/`DEPENDENCIES` mechanisms which cause circular dependency errors when all aliases share the same physical DB signature.
- **Reason:** Django's test runner treats DB aliases with identical connection params as aliases of one physical DB. `MIRROR` silently routes queries through the mirrored alias (losing role separation). `DEPENDENCIES` triggers circular-dependency detection. The custom fixture preserves real role separation: `default` connects as `app_rw` (exercising RLS), `admin` as `admin_rw` (BYPASSRLS), and `worker` as `worker`.
- **Doc Reference:** Session S03 follow-up Directive #3.

---

### 2026-10-02 — Repo-Wide HTTP Guard and Gated Transport
- **Decision:** Restricted raw HTTP libraries (`httpx`, `requests`, `urllib.request`, `aiohttp`) repo-wide to `backend/core/http_client.py` (with explicit AST exemptions for gateway LLM SDK adapters and storage boto3). The raw transport is private and only obtainable through `GatedHttpClient`. An AST test (`test_no_direct_http_imports_outside_core_http_client`) enforces this across all of `backend/`.
- **Reason:** Non-negotiable #5 and Directive #1. Any direct HTTP call skips legal profile checks, rate limits, robots enforcement, and audit logs.
- **Doc Reference:** Session S04 Directive #1; `docs/02_P0_source_acquisition.md` §5.2.

---

### 2026-10-02 — Cross-Process Per-Host Rate Limiting via PostgreSQL Advisory Locks
- **Decision:** Implemented cross-process per-host rate limiting using PostgreSQL advisory transaction locks (`pg_advisory_xact_lock(hashtext('host_rate_limit_' || host))`) and `plc.host_rate_limit` tracking `last_request_at` and `min_delay_seconds`.
- **Reason:** Directive #2. Multiple Procrastinate workers can crawl at once; an in-process token bucket would hit source servers N times faster. Cross-process database locking guarantees the per-host minimum delay (≥ 3.0s) holds across all worker processes.
- **Doc Reference:** Session S04 Directive #2; `docs/mvp/01_corporate_corpus_and_sources.md` §6.2.

---

### 2026-10-02 — Immutable Legal Profiles and Single Active Profile via Partial Index
- **Decision:** `plc.legal_profile` records are immutable: updates insert a new row and set `status = 'SUSPENDED'` on the previous active profile. A partial unique index (`WHERE status <> 'SUSPENDED'`) ensures at most one active profile per source. Every capture stamps `profile_id` into `fetch_context`.
- **Reason:** Directive #4. Enables evidentiary audit trails proving exactly which legal profile governed every historical fetch.
- **Doc Reference:** Session S04 Directive #4; `docs/mvp/03_data_model_and_contracts.md` §3.2.

---

### 2026-10-02 — Stable Source Record Key Formulation for IBBI Orders
- **Decision:** `source_record_key` formatted as `{section}:{file_stem}` (e.g. `nclt:2026-09-29-115640-houbm-a240fa27925a635b08dc28c9e4f9216d`). Case numbers and order dates are stored in `source_metadata` rather than the record key.
- **Reason:** Directive #6. If IBBI corrects a typo in an order date or case number, the record key remains unchanged, preventing duplicate or ghost records.
- **Doc Reference:** Session S04 Directive #6; `docs/02_P0_source_acquisition.md` §5.6.

---

### 2026-10-02 — Delta Crawl Deduplication without PDF Re-download
- **Decision:** In delta crawl sweeps, if an existing capture exists with identical PDF URL and listing metadata, the crawler records `change_kind = "UNCHANGED"` and sets `fetch_context.pdf_fetched = false` without fetching the PDF. Delta terminates upon seeing 20 consecutive unchanged records.
- **Reason:** Directive #7. Conserves bandwidth and source portal load while updating observation timestamps.
- **Doc Reference:** Session S04 Directive #7; `docs/02_P0_source_acquisition.md` §5.6.

---

### 2026-10-02 — CloudEvents Outbox Topic and Schema Compliance
- **Decision:** Captures emit to `plc.raw.captured.v1` and health updates emit to `plc.source.health.v1`. The `lane` (`rt` or `bulk`) is populated in the outbox `lane` column, not in the topic name. Unproduced fields (`warc`, `norm_fingerprint`, `near_dup_hint`) are present and set to `None`.
- **Reason:** Directive #8; `docs/01_master_architecture.md` §6.3, §6.4.

---

### 2026-10-02 — Mandatory Gated Client for All Network Fetches (Including Fixtures)
- **Decision:** Raw curl, direct requests, or un-gated HTTP client calls are strictly prohibited for any source data acquisition across the entire codebase, including test fixture generation and refreshes. All source network calls must proceed through `GatedHttpClient` (e.g. via management commands like `refresh_fixtures` and `seed_ibbi_profile`), ensuring legal profile checks, rate-limit enforcement (≥ 3.0s delay enforced across processes via PostgreSQL advisory locking), and declared User-Agent headers are respected at all times.
- **Reason:** Session S04 Closure Directive #3; Non-negotiable #5. Guarantees that neither automated crawler processes nor developer fixture refresh workflows ever bypass legal governance or rate limits.
- **Doc Reference:** Session S04 Closure Directive #3; `docs/02_P0_source_acquisition.md` §5.2; AGENTS.md §4 item 5.

---

### 2026-10-02 — Rate Limit Floor Guarantee via DB Clock and Monotonic Loop
- **Decision:** In `enforce_host_rate_limit`, elapsed time is calculated using PostgreSQL DB clock (`EXTRACT(EPOCH FROM (clock_timestamp() - last_request_at))`) under row locks, eliminating clock drift between host environments. If elapsed time is below the legal profile floor (`min_delay_seconds`), the worker sleeps the exact remaining duration using a monotonic clock loop (`deadline = time.monotonic() + needed; while time.monotonic() < deadline: time.sleep(...)`). `GatedHttpClient` also validates monotonic floor spacing before recording intervals.
- **Reason:** S04 Closure Directive #2. Operating system sleep granularity and Python-to-DB clock skew previously caused observed intervals to dip slightly below 3.0s (to ~2.92s). The DB clock computation and monotonic loop strictly guarantee that observed spacing never drops below the legal profile floor.
- **Doc Reference:** Session S04 Closure Directive #2; `docs/02_P0_source_acquisition.md` §5.8.

---

### 2026-10-02 — AST Guard Prohibiting Disabled TLS Verification (`verify=False`)
- **Decision:** Added an AST guard test (`test_no_disabled_tls_verification_anywhere_in_backend`) that scans all Python files in `backend/` and asserts that no function or method call passes `verify=False`, `verify=0`, or `verify=None`.
- **Reason:** S04 Closure Directive #3; Non-negotiable #5; `02_P0 §5.8`. Disabling TLS verification creates critical security vulnerabilities and breaks legal acquisition compliance. The AST test prevents any commit with disabled TLS verification.
- **Doc Reference:** Session S04 Closure Directive #3; `docs/02_P0_source_acquisition.md` §5.8.

---

### 2026-10-02 — Tesseract Local OCR Engine with Pinned Version Reporting
- **Decision:** Configured `TesseractOcrEngine` (via `pytesseract` and local binary installed with `brew install tesseract` locally and `sudo apt-get install -y tesseract-ocr` in CI) as the local OCR engine, pinned and recording engine name and exact version (e.g. `tesseract 5.5.3`) in the OCR adapter's page output. Tests fail loudly if the binary is missing or unusable. Migration to AWS Textract (Mumbai ap-south-1) is scheduled behind the same `OcrEngine` contract for production deployment in S15.
- **Reason:** User Request; stack adaptation for local dev and CI execution without AWS billing or egress, while strictly maintaining the immutable OCR abstraction contract (`OcrEngine`, `OcrPageResult`).
- **Doc Reference:** User Request; `docs/mvp/04_stack_and_infra.md` §2.7; `docs/03_P1_ingestion_parsing.md` §5.3.

---

### 2026-10-02 — Quality Gate Thresholds and Tier-1 Claim Safety Constraints
- **Decision:** Document-level quality gating produces 3 mutually exclusive gate classifications: `PASS` (structure_conf ≥ 0.65, ocr_conf ≥ 0.90, decision date resolved, no hidden text), `FLAGGED` (routed to Django Admin review queue with visible badge: missing date, unresolved case number, low structure confidence, or detected hidden text), and `QUARANTINED` (excluded from index and claims: mean ocr_conf < 0.80 or unsupported language). In addition, per-anchor `ocr_conf < 0.80` strictly excludes the anchor from backing Tier-1 claims even if the overall document passes.
- **Reason:** Non-negotiable #4 (Honest status) & Requirement 8. Ensures degraded or machine-hallucinated OCR text never backs legal assertions without human lawyer verification.
- **Doc Reference:** `docs/03_P1_ingestion_parsing.md` §5.11; `docs/mvp/00_mvp_spec.md` §2; `docs/mvp/04_stack_and_infra.md` §2.7.

---

### 2026-10-02 — ParsedDocument S3 Storage and Database Transaction Separation
- **Decision:** Pipeline writes gzip-compressed `ParsedDocument` JSON artifacts to S3/MinIO first (content-addressed at `parsed/{work_id}/{expression_key}/{parse_id}.json.gz`), hashes with SHA-256, and only upon successful storage upload initiates `transaction.atomic()` to commit domain rows (`work`, `manifestation`, `parse_run`, `anchor`, `anchor_alias`) and emit `doc.parsed.v1` outbox event in the same transaction.
- **Reason:** User Directive #5. S3 and Postgres do not share a two-phase commit. An orphaned S3 object is harmless; a database row pointing to a missing S3 object is a catastrophic integrity failure.
- **Doc Reference:** User Directive #5; `docs/mvp/03_data_model_and_contracts.md` §3.4; `docs/01_master_architecture.md` §7.1.

---

### 2026-10-02 — Anchor Assignment Stability Enum Restriction and Tombstone Encoding
- **Decision:** `anchor_alias.method` strictly restricted to the 03 §3.4 enum values (`NUM_EQ`, `HASH_EQ`, `NW_ALIGN`, `SPLIT`, `MERGE`, `RENUMBER`, `GRAMMAR_V11`). Paragraph deletions are recorded on `anchor.state = 'TOMBSTONED'` and `forward_to = <new_anchor_id>`, rather than creating synthetic methods. Minor text amendments on preserved paragraphs record `method = 'NW_ALIGN'` with confidence score.
- **Reason:** User Directive #2; `docs/mvp/03_data_model_and_contracts.md` §3.4.

---

### 2026-10-02 — Court Numbering Fidelity for Unmatched Paragraphs
- **Decision:** Newly introduced numbered paragraphs in court orders keep their printed numbers `p{n}` (`numbering = "EXPLICIT"`), satisfying Constraint A1. Only unnumbered blocks are minted synthetic locators `u{n}` (`numbering = "SYNTHETIC"`).
- **Reason:** User Directive #3; Constraint A1 (`docs/01_master_architecture.md` §5.3).

---

### 2026-10-02 — CI: MinIO Service Container for S3-Dependent Tests
- **Decision:** Added `docker run` step for MinIO in `.github/workflows/ci.yml` before Pytest, using the same pinned image digest as `infra/compose.yaml`. Waits up to 30s for `/minio/health/live`.
- **Reason:** All 7 CI failures in run 36980412972 were `EndpointConnectionError: Could not connect to http://localhost:9000`. Parse pipeline tests upload ParsedDocument JSON to S3 before DB commit (per Directive #5), requiring a live MinIO endpoint.
- **Doc Reference:** `infra/compose.yaml`; `docs/mvp/04_stack_and_infra.md` §2.11.

---

### 2026-10-02 — Hidden Text Fixture Regenerated with Truly Off-Canvas Text
- **Decision:** Regenerated `eval/fixtures/synthetic/hidden_text_adversarial.pdf`: mediabox 1000×1000, cropbox 595×842, adversarial text at `Point(700, 900)` (outside visible area). Previous fixture had "off-page" text at y=828 which was still within the 842pt page height and only detectable via a loose `y1 > page_h` check that also flagged normal footers.
- **Reason:** PyMuPDF clips text extraction to the cropbox regardless of clip parameter. The detection function now temporarily expands cropbox to mediabox to extract hidden text, then applies a 5pt tolerance so footers near the bottom margin are not flagged. A negative test confirms y=830 footers are clean.
- **Doc Reference:** `docs/03_P1_ingestion_parsing.md` §5.2 item 4; AGENTS.md §4.6.

---

### 2026-10-02 — Tombstone forward_to Uses Best-Overlap Similarity with 0.50 Threshold
- **Decision:** When a paragraph is deleted between re-parses, `forward_to` is set to the new anchor with highest `SequenceMatcher` similarity if ≥ 0.50, otherwise `None`. Previously defaulted to `aligned_nodes[0]` regardless of similarity.
- **Reason:** User directive: "forward_to must be the best-overlap new anchor by similarity, and null if nothing is close (no default to the first anchor)."
- **Doc Reference:** `docs/01_master_architecture.md` §5.5 (stability rules).

---

### 2026-10-02 — Golden Fixtures Expanded to 6 Total
- **Decision:** Added `sample_order_1.pdf` (NCLT Ahmedabad scanned, 16 pages, recorded OCR) and `sample_order_2.pdf` (NCLT Mumbai born-digital, 23 pages) as golden fixtures. Strengthened `nclt_scanned_ahm` golden data from 1 anchor to 5. All 6 fixtures have hand-read golden data with 5 anchors each.
- **Reason:** User directive to reach 6 fixtures and strengthen scanned goldens.
- **Doc Reference:** Session S05a requirement 7; `docs/mvp/06_test_set_plan.md`.

---

### 2026-10-02 — IBBI Order Mirror Duplicate PDF Blobs Across Distinct Listing Keys
- **Decision:** Documented that 160 S04 captures yielded 156 unique PDF blobs (`plc.raw_blob`). Two groups of captures (`sha256:a8eea...` across 3 distinct NCLT listing keys, and `sha256:3bdab...` across 2 distinct NCLT listing keys) downloaded identical PDF file bytes served under different order URLs on the IBBI portal. In the parsing pipeline, unique raw blobs were each parsed into a single `Work` (`wrk_01M3Y2VR23YM6F6HTG56AK5XA1` and `wrk_01M3Y2WB3TBSN758K2K5D69Q70`), with all listing keys mapped to manifestations of that work. Zero listings remain without an attached Work. Crawler investigation is deferred to a future session.
- **Reason:** Session S05b Directive #0b. Identical PDFs served under distinct listing URLs is a source portal artifact.
- **Doc Reference:** Session S05b Directive #0b; `docs/mvp/01_corporate_corpus_and_sources.md` §2.4.

---

### 2026-10-02 — Citation-Derived Alias Trust Tier Pinned to T4
- **Decision:** Pinned `trust_tier = "T4"` on `plc.identifier_alias` for self-minted STUB aliases created from regex-extracted citations inside court orders, with `source = "citation_mention"` and `evidence = {"mention_id": ..., "citing_work_id": ..., "anchor_id": ...}`.
- **Reason:** Session S05b Directive #4. While `T4` denotes "model-inferred", it represents the lowest available trust tier in the hierarchy (`T0 > T1 > T2 > T3 > T4`). A citation mention extracted from inside a judicial order is not court-authoritative for the cited case's canonical identity. When an authoritative `T0`–`T2` alias arrives later for the same normalized key, `alias_one_active` lifecycle ensures the `T4` row becomes `SUPERSEDED`, the STUB merges into the real work via `plc.identity_merge_ledger`, and existing mentions re-point.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.3 (line 240, 256); `docs/01_master_architecture.md` §5.4 (lines 659–665); Session S05b Directive #4.

---


---

### 2026-10-02 — Idempotent Re-Running of Citation Mention Resolution
- **Decision:** Re-running `resolve_citations` atomically deletes and rewrites `plc.citation_mention` rows for the same `parse_id`.
- **Reason:** User Directive #5. `plc.citation_mention` is an extractive mention ledger derived deterministically from immutable, content-addressed `ParsedDocument` anchors and their associated `ParseRun`. It contains no state mutated outside the extraction pipeline. Idempotently deleting and recreating mention rows for a `parse_id` prevents duplicate mentions across re-runs and ensures mentions stay completely synchronized with the latest extractor logic without data loss.
- **Doc Reference:** Session S05b User Directive #5; `docs/mvp/03_data_model_and_contracts.md` §3.3.

---

### 2026-10-02 — Idempotent Re-Parsing via Existing Work Lookup in parse_captured
- **Decision:** In `parse_captured`, the command looks up the existing `Work` matching `cap.raw_id` (via the latest `ParseRun` or `Manifestation` for that blob) and passes `existing_work_id` and `supersedes_parse_id` to `pipeline.process()`. A unit test (`test_parse_captured_twice_preserves_work_and_anchors`) enforces that re-parsing the same capture twice via the real command path creates exactly 1 work, mints 0 new works, and preserves 100% of live anchors.
- **Reason:** Session S05b Blocker #1. Previously, `parse_captured` invoked the pipeline without passing `existing_work_id`, minting a new `Work` on every re-parse pass. The lookup guarantees that re-parsing preserves paragraph anchors and work identity.
- **Doc Reference:** Session S05b Blocker #1; `docs/01_master_architecture.md` §5.5 (stability rules); `docs/03_P1_ingestion_parsing.md` §5.4.

---

### 2026-10-02 — Duplicate Works Retirement Proposal via Identity Merge Ledger
- **Decision:** The ~346 duplicate works created during historical development runs prior to the idempotency fix are preserved without deletion and proposed for retirement via `plc.identity_merge_ledger`. When approved by the user, duplicate works will be marked `status = 'MERGED'` with `merged_into = canonical_work_id`, recording an explicit `MERGE` operation in `plc.identity_merge_ledger` with reason `'REPARSE_DUPLICATE_RAW_BLOB'`. Zero rows will be deleted.
- **Reason:** Session S05b Blocker #2; Non-negotiable #1. Preserving historical parse runs and ledgering merges maintains full bitemporal auditability and adheres strictly to the spine decision record.
- **Doc Reference:** Session S05b Blocker #2; `docs/03_data_model_and_contracts.md` §3.3; `docs/01_master_architecture.md` §2.4, §5.4.

---

### 2026-10-08 — Idempotent Re-Parsing of CHANGED Captures via source_record_key Lookup
- **Decision:** In `parse_captured`, when no `ParseRun` or `Manifestation` matches the capture's `raw_id`, the command also queries previous captures for the same `source_record_key` (including `prior_raw_id`) to find the latest active `Work` and `ParseRun`. It passes `existing_work_id` and `supersedes_parse_id` to `pipeline.process()`. A unit test (`test_changed_capture_reuses_work_and_tombstones_deleted_anchors`) parses an original order followed by `sample_order_changed.pdf` and verifies that exactly 1 work is maintained, surviving anchors remain live or aliased, and anchors for deleted paragraphs are marked `state = 'TOMBSTONED'`.
- **Reason:** S05b Follow-up. When a court order is amended or replaced on a portal, the new PDF produces a distinct `raw_id`. Looking up by `source_record_key` ensures the amended document aligns against the existing work rather than minting an unlinked duplicate work.
- **Doc Reference:** S05b Follow-up; `docs/01_master_architecture.md` §5.5 (stability rules); `docs/03_P1_ingestion_parsing.md` §5.4.

---

### 2026-10-08 — Separation of Crawl Fixture and Truncated Order Test Fixture
- **Decision:** Restored `eval/fixtures/ibbi/sample_order_changed.pdf` to its original S04 state (`568c8d9`) so that S04 ingestion/crawl tests preserve their exact reference fixture. Moved the 10-page truncated order to `eval/fixtures/ibbi/sample_order_truncated.pdf` with its cached OCR results (`eval/fixtures/ocr/sha256_611d3739ebb48847a5e85fb1db2694fe080fd26d2a6e5aca6b4ef794194d2a1d_p*.json`), pointing the anchor revision and tombstone test at it.
- **Reason:** Decouples ingestion crawler test fixtures from parser anchor modification fixtures. S04 crawler tests expect the original fixture without truncation, while anchor revision tests explicitly require truncated pages to verify anchor tombstones and forwarding pointers.
- **Doc Reference:** S05b Follow-up Directive #1; `docs/01_master_architecture.md` §5.5.

---

### 2026-10-08 — Canonical Work Resolution Following `merged_into` in `parse_captured`
- **Decision:** In `parse_captured`, whenever an existing work is picked (whether by `raw_id`, `source_record_key`, or `prior_raw_id`), if the work's status is `MERGED`, `parse_captured` traverses `merged_into` to resolve to the canonical work (`resolve_canonical_work_id`), ensuring a new parse run is never attached to a `MERGED` duplicate. A dedicated unit test (`test_merged_work_resolution_attaches_to_canonical_work`) enforces this constraint.
- **Reason:** S05b Follow-up Directive #2. Ensures that once a duplicate work is retired and marked `MERGED`, subsequent parses for any capture or source record key pointing to it attach cleanly to the canonical work rather than reviving the duplicate.
- **Doc Reference:** S05b Follow-up Directive #2; `docs/01_master_architecture.md` §2.4, §5.4; `docs/03_data_model_and_contracts.md` §3.3.

---

### 2026-10-08 — Tombstone `forward_to` Assertion Matching Similarity Rule
- **Decision:** Asserted `forward_to` on tombstoned anchors during capture revisions. Paragraphs removed between revisions with text similarity below 0.50 threshold receive `forward_to = None` (e.g. `#p10`, `#ord` when pages 11–13 are truncated). Any non-null `forward_to` must point to an active anchor on the canonical work.
- **Reason:** S05b Follow-up Directive #3; `docs/01_master_architecture.md` §5.5 anchor stability protocol.
- **Doc Reference:** S05b Follow-up Directive #3; `docs/01_master_architecture.md` §5.5.

---

### 2026-10-08 — Retirement of 346 Duplicate Works via Single Atomic Transaction
- **Decision:** Executed retirement of 346 historical duplicate works via management command `retire_duplicate_works` in a single atomic transaction (`transaction.atomic()`). Updated all 346 works to `status = 'MERGED'` and `merged_into = canonical_work_id`, created 346 audit records in `plc.identity_merge_ledger` (`op='MERGE'`, `kind='WORK'`, `confidence=1.0`, `reason='REPARSE_DUPLICATE_RAW_BLOB'`), re-pointed manifestations and citations, marked active aliases as `SUPERSEDED`, and emitted `identity.merged.v1` CloudEvents to `ops.event_outbox`. Zero rows were deleted.
- **Reason:** S05b Follow-up Directive #4; AGENTS.md §4 & §5 non-negotiables. Preserves complete bitemporal audit history with zero deletions while resolving all duplicate works into their canonical entities.
- **Doc Reference:** S05b Follow-up Directive #4; `docs/mvp/03_data_model_and_contracts.md` §3.3; `docs/01_master_architecture.md` §2.4, §5.4.





