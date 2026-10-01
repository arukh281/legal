# PROGRESS.md — Build State

## Current State: Session S01 Complete (Foundation)

### 1. What Was Built
- **Monorepo Structure (AGENTS.md §3):**
  - Django project `core` at `backend/` with settings split (`base`, `local`, `prod`, `test`).
  - 15 Django apps created with `apps.py` and `README.md` defining blueprint phase ownership and contract boundaries:
    `ops` (owns `ops` schema, outbox, job chains), `anchor_lib`, `ingest` (P0), `parse` (P1), `index` (P2), `kg` (P3), `propagate` (P4), `retrieve` (P5), `reason` (P6), `rules` (Procedural Clock), `workspace` (P7), `verify` (P8), `feedback` (P9), `surface` (P10), `gateway` (Model Gateway).
  - React 19 + TypeScript + Vite 6 SPA at `frontend/` with nav for Today, Research, Matters, Authority, Alerts, Login placeholder, and TanStack Query.
  - Infra directory at `infra/` with `compose.yaml`, `Dockerfile.web` (Uvicorn ASGI), `Dockerfile.worker` (Procrastinate).
- **Database & Schemas:**
  - PostgreSQL 18 with `pgvector/pgvector:pg18` running in Docker Compose.
  - Three database schemas: `plc` (public legal corpus), `tpl` (tenant plane), `ops` (operational, outbox, jobs, gateway).
  - PostgreSQL extensions: `vector`, `btree_gist`, `pg_trgm`, `unaccent`.
  - Verbatim DDL from `docs/mvp/03_data_model_and_contracts.md` §3.1 & §3.16 applied via migrations:
    - `ops.pipeline_version`
    - `ops.event_outbox`
    - `ops.event_subscription`
    - `ops.event_inbox`
    - `ops.event_parked`
    - `ops.job_chain`
    - `ops.job_step`
    - `ops.job_signal`
    - Strict CHECK constraints (`chk_outbox_dataclass_tenant`, `chk_outbox_topic_prefix`, `chk_outbox_traceparent`, `chk_parked_reason`, `chk_step_key`, etc.) and indices.
  - Procrastinate database schema (migrations 1 to 41).
- **Outbox & Inbox (03 §4):**
  - Outbox publisher (`ops.outbox.publish_event`): atomic transactional insert into `ops.event_outbox` + `pg_notify('outbox', topic)`.
  - Outbox dispatcher (`ops.outbox.dispatch_pending_events`): `SELECT ... FOR UPDATE SKIP LOCKED` batching with per-partition-key serial locks (`lock = f"{consumer}:{partition_key}"`).
  - Inbox delivery (`ops.outbox.process_event_delivery`): consumer handler execution and `ops.event_inbox` insertion occur in **ONE atomic transaction** (03 §4 step 3).
  - Idempotency guarantees: duplicate delivery with identical payload is a no-op (`NO_OP`); duplicate delivery with modified payload is parked in `ops.event_parked` with `IDEMPOTENCY_KEY_REUSE`.
- **Resumable Job Chains (03 §5):**
  - Job chain runner (`ops.jobs.start_job_chain`, `ops.jobs.run_step_logic`): deterministic step-level retry, output caching by `(chain_id, step_key)`, heartbeat monitoring (`heartbeat_step`), stalled step reaping (`reap_stalled_steps`), and atomic step transition + next step deferral in ONE transaction.
  - 3-step test demo chain (`ops.demo_chain`) executing `demo_step_one` → `demo_step_two` → `demo_step_three` emitting test-only event `ops.demo.completed.v1` on `plc.ops.demo.completed.v1` (never emitting production contract events).
  - Crash recovery test (`ops.tests.test_jobs.test_job_chain_crash_recovery_killing_real_worker_process`) spawns a real OS worker subprocess, kills it with `SIGKILL` mid-step, and verifies a new worker resumes from the unfinished step without re-executing completed steps.
- **API & Frontend Generation:**
  - Django Ninja API at `/api/health` returning `{ status: "ok", database: "connected", schemas: ["ops", "plc", "tpl"] }`.
  - Management command `export_openapi` to generate `openapi.json`.
  - Frontend type generation via `openapi-typescript` emitting `frontend/src/api/schema.d.ts`.
- **Tooling & CI:**
  - Structured JSON logging (`core.logging`) with W3C traceparent logging and SHA-256 masking of sensitive payloads (`TENANT_CONFIDENTIAL`, `PRIVILEGED`).
  - GitHub Actions CI workflow (`.github/workflows/ci.yml`) running against PostgreSQL 18 + pgvector service container: uv sync, ruff lint, ruff format check, mypy strict, pytest, pnpm lint, vitest, and tsc build.
  - Pre-commit configuration (`.pre-commit-config.yaml`).

### 2. How to Run It

#### A. Local Development with Docker Compose
```bash
# Bring up PostgreSQL 18, MinIO, Web (Uvicorn ASGI), and Worker (Procrastinate)
docker compose -f infra/compose.yaml up -d

# Verify health endpoint (default port 8000, or 8001 if WEB_HOST_PORT=8001)
curl http://127.0.0.1:8000/api/health
# Response: {"status":"ok","database":"connected","schemas":["ops","plc","tpl"],...}

# Run migrations
docker compose -f infra/compose.yaml exec web uv run python manage.py migrate
```

#### B. Running Backend Tests & Quality Checks
```bash
cd backend

# Type check (strict)
uv run mypy .

# Lint & formatting check
uv run ruff check .
uv run ruff format --check .

# Run all 10 unit, contract, and crash-recovery tests against real PostgreSQL 18
uv run pytest
```

#### C. Running Frontend
```bash
cd frontend

# Install dependencies
pnpm install

# Lint & unit tests
pnpm run lint
pnpm run test

# Production build
pnpm run build

# Dev server
pnpm run dev
```

### 3. Stubs
- Downstream domain apps (`anchor_lib`, `ingest`, `parse`, `index`, `kg`, `propagate`, `retrieve`, `reason`, `rules`, `workspace`, `verify`, `feedback`, `surface`, `gateway`) contain `apps.py` and `README.md` defining their phase boundaries. Their models and internal logic will be built in their respective sessions (S02–S18).
- Model Gateway (`gateway`) is stubbed until S03.
- Allauth & Tenancy (`authz.can()`, RLS) are stubbed until S03.
- Event handlers are registered dynamically via `HANDLER_REGISTRY` stub until real phase subscribers are wired.

### 4. Known Issues
1. **Docker configuration modification:** During initial Docker authentication troubleshooting on this host, `~/.docker/config.json` had its `credsStore` entry removed. Per user instruction, this is noted here, and all future actions outside the repository boundary strictly require prior approval.
2. **Host port 5432 conflict:** Host machine runs a local PostgreSQL 16 on port 5432. Docker Compose maps PostgreSQL container port 5432 to host port 5433 (`POSTGRES_HOST_PORT=5433`). Inside the Docker Compose network, services talk on standard port 5432.
3. **Host port 8000 conflict:** Host machine runs a Python HTTP server on port 8000 (PID 3905 serving BBRE project). Docker Compose supports `WEB_HOST_PORT` (defaults to 8000, can be set to 8001). Vite proxy config reads `VITE_API_URL` (defaults to `http://127.0.0.1:8000`).
4. **Procrastinate Django connector listen/notify:** Psycopg3 connection under Django connector does not support synchronous `listen_notify`. Procrastinate worker runs with `--no-listen-notify`.
5. **App `default_auto_field = BigAutoField`:** Django app skeletons currently declare `default_auto_field = "django.db.models.BigAutoField"`. Domain objects in `plc` and `tpl` must use prefixed Crockford ULIDs (AGENTS.md §5: `prefix_` + 26-char Crockford ULID minted in app code, never serial ints or standard UUIDs). Session S02 (`anchor_lib` + ID minting) must replace this with the domain ULID ID field across domain models.

### 5. What the Next Session (S02) Needs
- **`anchor_lib` + ID Minting:**
  - Build the Anchor grammar v1.1 parser + validator library per `docs/01_master_architecture.md` §5.3.
  - Implement unit tests from `01_master §5.3` (including `pdoc_…/v1#…` and `sch-1.ord-8.rule-1`).
  - Implement Crockford ULID minting utility (`prefix_` + 26-char Crockford ULID) per `03_data_model_and_contracts.md` §1 and `01 §5.2`.
  - Apply `work`, `expression`, `manifestation`, `identifier_alias`, `parsed_document`, `anchor`, and `anchor_alias` tables in `plc` schema.
