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

### 2026-10-01 — Transactional Advisory Locking for Append-Only Audit Log Chains
- **Decision:** Serialized audit event insertions per tenant using `SELECT pg_advisory_xact_lock(hashtext('audit_' || tenant_id))` and dynamically resolved chain heads via `row_hash NOT IN (SELECT prev_hash ...)`.
- **Reason:** Under high concurrency, two parallel requests in the same tenant could query the chain head simultaneously and create duplicate branches/forks in the SHA-256 hash chain. The transactional advisory lock serializes inserts per tenant with zero cross-tenant contention.
- **Doc Reference:** `docs/mvp/03_data_model_and_contracts.md` §3.8; `docs/09_P7_firm_matter_workspace.md` line 723; Session S03 Directive #6.

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


