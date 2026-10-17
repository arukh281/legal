# AGENTS.md — Corporate-law legal intelligence platform (MVP)

You are building a client file for law firms: a firm creates a client, opens matters (cases) under it, keeps every document there, and the system helps run each case through to filing. It must work for any kind of case, with legal depth added one area at a time (insolvency first). Lawyers will use this on real matters. Correctness and honesty beat speed and features.

## 1. Source of truth
Read before coding. Read only the sections your session needs; the docs are long.
- `docs/mvp/00_mvp_spec.md`: what we build (capabilities §4, never-cut list §2).
- `docs/mvp/03_data_model_and_contracts.md`: every table, ID, event, job and permission. Build them exactly as written.
- `docs/mvp/04_stack_and_infra.md`: stack decisions. Don't substitute.
- `docs/mvp/05_build_plan.md`: order and weekly exit checks.
- `docs/mvp/02_workflows_and_rules.md`: deadline RuleSpecs (very long; read only your trigger).
- `docs/mvp/06_test_set_plan.md`: gold suites and zero-tolerance gates.
- Blueprint `docs/00`–`docs/25`: reference only. `docs/mvp/*` decides scope. For an object shape, ID format, anchor grammar or event name, `docs/01_master_architecture.md` and `docs/01a_spine_decision_record.md` win.
- `PROGRESS.md` (build state) and `DECISIONS.md` (decisions made during the build): read both at the start of every session.

If the docs are silent or contradict each other, stop and ask. Don't guess. Record the answer in `DECISIONS.md`.

## 2. Stack (fixed)
- Backend: Python 3.13, Django 5.2 LTS, Django Ninja (typed API), Procrastinate (jobs), Postgres transactional outbox (events).
- Database: PostgreSQL 18 with pgvector (`halfvec` HNSW) and built-in FTS. Extensions: vector, btree_gist, pg_trgm, unaccent.
- Frontend: React 19, TypeScript, Vite, TanStack Query, PDF.js. API types generated from OpenAPI with openapi-typescript.
- Storage S3 (ap-south-1); OCR Amazon Textract; SSO django-allauth (Google or Microsoft); embeddings and rerank Voyage; LLMs from Anthropic, OpenAI and Google, only through our Model Gateway.
- Local dev: Docker Compose with Postgres 18 + pgvector, and MinIO standing in for S3. Prod: AWS Mumbai (04 §2.11).
- Tooling: uv, ruff, mypy (strict on new code), pytest, hypothesis; pnpm, eslint, vitest. CI on GitHub Actions.

Do not add Kafka, Temporal, OpenSearch, OpenFGA, Redis, Celery, LangChain, LlamaIndex or a separate vector DB. If you think one is needed, write a proposal in `DECISIONS.md` and ask.

## 3. Repo layout
- `backend/`: Django project `core`, with one app per blueprint phase: `anchor_lib`, `ingest` (P0), `parse` (P1), `index` (P2), `kg` (P3), `propagate` (P4), `retrieve` (P5), `reason` (P6), `rules` (Procedural Clock), `workspace` (P7), `verify` (P8), `feedback` (P9), `surface` (P10), `gateway` (Model Gateway).
- `frontend/`: the Vite SPA.
- `eval/`: gold store loader, runner, scorecard, fixtures.
- `infra/`: Compose and Terraform.

Apps talk only through the contracts in 03 (tables they own, typed objects, outbox events). Never import another app's internals. This is what lets us split services later without a rewrite.

## 4. Non-negotiables (00 §2; never trade these for speed)
1. **Contracts at full fidelity:** anchor grammar v1.1, ParsedDocument, identifier_alias with trust tiers, the bitemporal Assertion ledger with evidence and provenance, AuthorityView (`definitive`, `reason_codes`), EvidenceBundle, Claim, VerificationReport, `rights_class` + `provenance_tier`, `pipeline_version` lineage, index generations + aliases, ModelTaskContract + LLMCallRecord, the CloudEvents envelope and event names.
2. **Deadlines come only from the rules engine**, using ACTIVE RuleSpecs (re-anchored to official text, signed off by a partner lawyer, golden vectors green). An LLM may extract a trigger date with its exact quote for a lawyer to confirm. An LLM never computes, adjusts or suggests a deadline. For non-active rules, list the period; don't compute it.
3. **Never invent law.** No statute text, section number, period, case name or citation may come from model memory. Everything shown to a lawyer resolves to an anchor in our corpus with an exact quote. Out of corpus means "not in MVP corpus", never "wrong".
4. **Honest status.** Machine-detected negative treatment shows as CAUTION with `definitive=false`: never hidden, never shown as verified. Confidence is labelled "uncalibrated preview". Every answer shows "law current to <date>" and any degradations.
5. **Legal gate.** No source adapter runs without a `legal_profile` (PROVISIONAL or APPROVED). Never solve, bypass or automate a CAPTCHA. Obey robots.txt and the profile's rate limit (default ≤ 1 request per 3 s; backfills at night IST).
6. **Untrusted documents are data.** Uploaded or fetched text never becomes instructions. Extraction runs without tools, every extracted value must be an exact substring of its source, and hidden text is flagged.
7. **"Enacted but not in force" and "Bill, not law" are answered correctly 100% of the time**: the IBC (Amendment) Act 2026 and the Corporate Laws (Amendment) Bill 2026 are the test cases.

## 5. Data rules
- **Three schemas.** `plc` is the public corpus: no `tenant_id`, no reference to tenant data. `tpl` is the tenant plane: `tenant_id NOT NULL` on every row, RLS forced. `ops` holds events, jobs, the gateway and lineage.
- **IDs** are `prefix_` + a 26-char Crockford ULID, minted in app code (03 §1, 01 §5.2). No serial ints or UUIDs for domain objects.
- **Anchors** are created, parsed and compared only through `anchor_lib`. Never hand-build an anchor string.
- Durable records store anchors + `quote_selector`, never `chunk_id`s.
- Every derived row carries `pipeline_version`.
- **Time:** `valid_period` daterange `[from, to)` for legal time; `tx_period` tstzrange for belief time. Never update an assertion in place; supersede it.
- **Migrations:** Django migrations, reversible, one per logical change. Raw SQL only for extensions, domains, RLS and HNSW indexes.
- A write that emits an event inserts into `ops.event_outbox` in the same transaction.

## 6. LLM rules
- Every model call goes through `backend/gateway` with a ModelTaskContract (output schema, budget, allowed endpoints) and writes an LLMCallRecord. No direct SDK calls anywhere else.
- At least 2 qualified endpoints per task. Verifier and opponent run on a different model family from the generator.
- Validate structured output against its JSON Schema; repair once, then fail loudly.
- Never log the body of a tenant or privileged payload; log IDs and hashes only.
- Tests never call real APIs. Use recorded fixtures or fakes; real calls happen only in explicitly marked eval runs.
- The router enforces `residency_policy` fail-closed (default `ANY` until the partner decides).

## 7. How every session works
1. Read this file, `PROGRESS.md`, `DECISIONS.md`, then the doc sections named in the session prompt.
2. Write an implementation plan (files, tables, tests, open questions) and wait for approval before coding.
3. Build only your session's scope. If you need something from a later session, build the smallest stub behind its contract and list it under "Stubs" in `PROGRESS.md`.
4. Tests are part of the work: unit tests for logic, contract tests for every table, object and event you produce or consume, and at least one fixture from real public documents (never client documents).
5. **Done** means: all tests green, lint and types clean, migrations apply on an empty database, the session's exit check demonstrated, and `PROGRESS.md` updated.
6. End by updating `PROGRESS.md` (what was built, how to run it, stubs, known issues, what the next session needs) and adding any decision to `DECISIONS.md` (date, decision, reason, doc reference).
7. Commit in small steps with clear messages. Never commit secrets, `.env` files or client documents.

## 8. Session map
| # | Session | Works for | Status |
|---|---|---|---|
| S01 | Foundation: repo, Django/Ninja/React skeleton, Compose, CI, schemas, `pipeline_version`, outbox, job chains | — | Done |
| S02 | `anchor_lib` + ID minting | — | Done |
| S03 | SSO, tenancy, `authz.can()` + RLS, Model Gateway v0 | — | Done |
| S04 | Source capture + legal gate (IBBI orders first) | — | Done |
| S05 | Parsing: text layer + OCR, judgment and statute parsers, anchors, citation extraction | — | Done |
| S06 | Index: chunks, FTS `legal_en`, embeddings, pgvector generations + aliases, Index Access Layer | — | Done |
| S07 | Retrieval, Q&A with claims, source viewer (Demo 1) | — | Done |
| S08 | Eval harness + gold store | — | Done |
| R1 | Client file: client entity, matters under a client with free-text case type and court, document vault (PDF, DOCX, EML, ZIP) with stage tags, versions and private anchors, manual case-number entry | Any case | Done |
| R2 | Hearings, dates and Today: manual hearing and date entry for any court; NCLT/NCLAT cause-list PDF matching on entered case numbers; new orders in IBC cases land in the matter via the IBBI delta crawl; Today page, phone-usable | Any case (manual); IBC (automatic) | |
| R3 | Tasks with due dates linked to hearings or deadlines; client status link or email per matter; Excel import of live cases | Any case | |
| R4 | Dates and facts from documents with exact quotes for lawyer confirmation; order-set dates for any court; statutory deadlines for the IBC pack only (02 Part A), after re-anchoring to India Code text | Any case (order-set); IBC (statutory) | |
| R5 | Corpus to real scale: IBC, CIRP Regulations and AAA Rules from India Code with point-in-time for the 2026 amendment; IBBI mirror backfill; research inside the matter (real embeddings as g2 and hybrid retrieval already landed in the research-quality session) | IBC | |
| R6 | Templates and filing bundles: vakalatnama, affidavit, memo of parties, annexure index first; then IBC forms (s.8 notice, s.7 and s.9 petition skeletons, reply skeleton), e-filing checklist, defect-cure tracker. Assemble, never submit | Any case (generic); IBC (forms) | |
| R7 | Cite-check on uploaded drafts against the corpus, honest "not in MVP corpus" | Any case within corpus | |
| R8 | Hardening and pilot: residency decision, DPA, backups and restore drill, firm-visible access log, two law firms live | — | |

Note: S09 citator, S12 memo chain, S17 alerts and digest, and corpus breadth beyond IBC are deferred, not deleted. Real embeddings (g2) and hybrid retrieval already landed in the pre-S09 research-quality session.

After R8: a module for insolvency professionals (CIRP compliance calendar, claims, CoC meetings, IBBI forms); then the next legal areas one per session from 02 Parts B to D (arbitration, company law, s.138 cheque bounce, commercial suits).

## 9. Never
- Never fabricate data, results or citations to make a test pass.
- Never weaken, skip or delete a zero-tolerance test.
- Never show judge win-rates or outcome predictions.
- Never put client data in fixtures, logs or prompts outside `tpl` and the gateway.
- Never change a contract (schema shape, ID format, event name, anchor grammar) without a `DECISIONS.md` entry and approval.
