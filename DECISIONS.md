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


