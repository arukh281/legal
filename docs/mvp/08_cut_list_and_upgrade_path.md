# 08 — Cut List and Upgrade Path

**Purpose.** This is everything in the blueprint (docs 00–25) that the MVP does not build at full strength, and how each item comes back **without a rewrite**. Each item has three parts:

- **MVP treatment.** KEPT AS CONTRACT means the contract is built now at full fidelity. SIMPLIFIED means a simpler implementation behind the same contract. THIN means the capability exists but narrowly. DEFERRED means it is not built. NEVER (BY DEFAULT) carries the blueprint's own "never" rulings.
- **Trigger.** When to upgrade.
- **Path.** How to upgrade.

Upgrades are cheap because of blueprint principle 9, "reversible by construction" (22 §1). The contracts are kept from day 1: anchors, ParsedDocument, Assertion ledger, AuthorityView, EvidenceBundle, Claim/VerificationReport, `rights_class`, `pipeline_version`, index generations and aliases, Model Gateway and event names. Every upgrade below therefore swaps an implementation behind an existing interface.

---

## 1. Kept as contract from day 1 (not cut)

| Contract | Blueprint source | Why it cannot wait |
|---|---|---|
| Anchor grammar v1.1, incl. private `pdoc_…/v1#…` anchors and the schedule `ord-`/`rule-` units | 01 §5.3; D8, D16, D22.2 | Every claim, memo, feedback row and gold item points at anchors. Changing the grammar later would invalidate all of them. |
| `ParsedDocument` (JSON in the object store, plus anchor rows) | 01 §7.1; 03_P1 §2 | Re-parsing must reproduce stable anchors (anchor stability ≥ 99.5%, 22 §3.3). |
| `identifier_alias` with status + trust tiers T0–T4 | D16 | Citation resolution and cite-check depend on it. |
| Bitemporal `assertion` ledger with evidence, provenance, `review_state`, `impact_tier` | 01 §7.5; D7 | The citator and alerts are built on it. Retrofitting bitemporality means replaying history. |
| `AuthorityView` (fields, including `definitive` and `reason_codes`) | D6, D20.12 | It is the only input to badges, ranking and verification (D6). |
| `EvidenceBundle`, `Claim`, `VerificationReport` (statuses incl. UNVERIFIABLE; gate PASS/PARTIAL/BLOCK) | 01 §7.9, §7.15, §7.19; D9, D21.6 | The memo and Q&A contracts. P8 checks are written against them. |
| `rights_class`, `provenance_tier` | D9, D16, D20.14 | Sets what may be shown, exported or redistributed (EBC v. Modak). It must be captured at ingest. |
| `pipeline_version` lineage | D10 | Reprocessing, audit replay, eval comparisons. |
| Index generations + aliases | 04_P2 §10; 22 §3.3 | "Retrofitting them later means a live migration" (04_P2 §10). |
| Model Gateway (`ModelTaskContract`, `LLMCallRecord`) | 13 §4; D14 | Lets us swap providers, enforce residency later, and attribute cost. |
| Event names and the CloudEvents envelope | 01 §6; D2, D4, D20.16 | Consumers are written against them. Kafka can be introduced later without touching consumers' payload code. |
| Deterministic Procedural Clock + RuleSpecs (`prs_`) | 08_P6 §5.5 | Deadlines are never computed by an LLM (brief rule). |

## 2. Infrastructure

| Blueprint item | MVP treatment | MVP implementation | Upgrade trigger | Upgrade path |
|---|---|---|---|---|
| Kafka 4.x + Debezium outbox (D1) | SIMPLIFIED | Postgres `outbox_event` table in the same transaction as the write; a Postgres-backed job queue delivers events to in-process consumers. Event types and envelope fields are identical. | A second deployment or tenant cell; sustained events > ~50/s; need for > 30-day replay or external consumers | Add an outbox relay (Debezium or a poller) that publishes rows to Kafka topics named per D20.16. Consumers switch from queue polling to Kafka consumers; payload code is unchanged. Run both side by side for one week. |
| Temporal durable workflows | SIMPLIFIED | Resumable **job chains**. Each step is an idempotent job with an idempotency key and persisted step state. A failed step retries; the chain resumes from the last completed step. | HITL waits measured in days across many matters; > 1 deployment; complex compensation logic | Wrap each step function as a Temporal activity. The chain definition becomes a workflow. Step state tables become history (migrate open chains or drain them). |
| OpenSearch (BM25 + k-NN) behind the Index Access Layer | SIMPLIFIED | Postgres full-text search + pgvector, with generation-suffixed tables and alias views (see 03/04). The `IndexQuery`/`IndexHit` interface is kept. | > ~10M chunks; p95 search > 800 ms; multilingual analyzers needed (Hindi) | Implement the Index Access Layer backend on OpenSearch, build a new generation by dual-write or backfill, run the eval gate, then swap the alias. Callers are unaffected. |
| In-memory CSR graph projection (PPR, traverse) | DEFERRED | SQL recursive CTEs (depth ≤ 2) over `assertion` | PPR retrieval leg adopted; traversal p95 > 200 ms | Build the projection from the same tables (05_P3). |
| OpenFGA (Zanzibar ReBAC), ethical walls | SIMPLIFIED | One `authz.can(user, action, resource)` choke point. Matter membership + roles (PARTNER, ASSOCIATE, ADMIN) + a matter `restricted` flag that hides the matter from non-members (a basic inclusionary wall). | Second firm; exclusionary walls; DMS ACL mirroring | Re-implement `authz.can` and `list_visible` on OpenFGA Check/ListObjects. Tuples are generated from the membership tables (09_P7 §5). |
| Tenant cells D1–D4h, router, promotion | SIMPLIFIED | One deployment for the partner firm. `tenant_id` on every tenant row; public corpus rows have `tenant_id = NULL`. | Second firm (pooled) or a firm demanding isolation | D2 = this deployment, unchanged. D1 adds Postgres RLS on `tenant_id` and per-tenant index partitions. D3/D4 add a local PLC replica (D19.7). |
| Per-tenant KMS key + per-matter DEK, crypto-shredding | SIMPLIFIED | Provider-managed encryption at rest (database + object store) and TLS everywhere. Matter purge = hard delete + object deletion, logged. | Second firm; BYOK request; DPDP erasure at volume | Envelope encryption per matter for blobs and sensitive columns (09_P7 §5). Purge becomes key destruction. |
| Audit hash chain + WORM anchoring | THIN | Append-only `audit_event` table with `prev_hash` (cheap to keep). No WORM, no RFC 3161 timestamps. | Firm security review; SOC 2 | Ship Merkle roots to an object-lock bucket every 5 minutes (09_P7). |
| Model Gateway with residency fail-closed routing, eval-gated qualification, ≥ 2 endpoints per task | THIN | Thin gateway: task registry (`model_task_contract`), 2 provider adapters, an `LLMCallRecord` per call, a per-task budget. `residency_policy` is stored per tenant (default ANY until the partner answers, [07 Q3](07_partner_firm_questions.md)). No automatic router. | Partner requires IN_ONLY; a provider price or quality shock | Turn on fail-closed routing from the endpoint registry (D15); add in-India endpoints (Bedrock "in." profiles, Azure South India) as qualified endpoints. |
| OpenTelemetry + Langfuse + OpenLineage | THIN | Structured JSON logs with `trace_id`; `llm_call_record` rows; `pipeline_version` on every artefact | > 2 engineers; latency debugging across services | Add the OTel SDK and propagate `traceparent` (already in the envelope). Langfuse self-hosted. |
| Multi-AZ, Mumbai→Hyderabad DR (RPO 5 min) | THIN | Managed Postgres with automated backups and point-in-time restore; object-store versioning | Paid customers beyond the partner | Cross-region replicas per 13 §8. |
| SOC 2 / ISO 27001 | DEFERRED | Security checklist in 05 (SSO, MFA, least privilege, backups, dependency scanning, secrets manager) | Second firm or the partner's IT review | Programme per 13 §5.8. |

## 3. Sources and corpus (P0)

| Blueprint item | MVP treatment | MVP implementation | Upgrade path |
|---|---|---|---|
| All 25 HCs with own-site deltas; district courts | THIN | Delhi, Bombay and the partner's HC: company/commercial/arbitration subsets from the open HC dataset (backfill), labelled `backing: DATASET_ONLY` with the dataset's as-of date (02_P0 §10). No own-site delta in the MVP. | Add own-site delta adapters for these 3 HCs (M2), then more by partner demand. |
| Tribunals beyond the corporate set (ITAT, NGT, CAT, consumer, …) | DEFERRED | Corporate set only: NCLT (via IBBI orders + allowed NCLT paths), NCLAT, SAT, SEBI and CCI orders (see 01) | Add adapters behind the same legal gate. |
| WARC/WACZ capture archive, signed Merkle roots | SIMPLIFIED | Content-addressed raw blobs (`sha256`) + a `capture` row with URL, time, HTTP headers and adapter version. Provenance is the same; the packaging is simpler. | Write WARC files from the same capture rows (warcio) when evidentiary replay is needed. |
| Legal-gate-as-code (LegalProfile) | KEPT | `source` + `legal_profile` tables. No adapter runs without an APPROVED profile (01). | — |
| `judgment.expected.v1` pronouncement watch | DEFERRED | — | Add the SC pronouncement watch (02_P0) when SC cause lists are ingested. |
| Court calendars from P0 (`court.calendar.published.v1`) | SIMPLIFIED | `court_calendar` table seeded manually from official holiday lists for SC, NCLT, NCLAT, SAT and the 3 HCs; re-entered yearly. Same table shape as the feed. | A P0 calendar adapter publishes `court.calendar.published.v1` into the same table. |
| Case-status, cause-list and daily-order feeds (eCourts CNR, CAPTCHA-gated) | DEFERRED | Manual hearing entry (capability 10). NCLAT daily orders from its open listing where the legal profile allows (01). | P0 feeds per D20.1 once access is lawful (MoU or opinion). |
| Indian Kanoon API gap-fill | DEFERRED | — | Only after counsel opinion (b) (22 §3.2). |
| Hindi and the 22 scheduled languages | DEFERRED | English only. Non-English documents are flagged `lang_unsupported` and excluded from answers; the user sees a banner. | Hindi first (OLA s.7 HCs): Indic OCR, Hindi analyzer, MT renditions per D8 (never citable). |

## 4. Parsing and indexing (P1, P2)

| Blueprint item | MVP treatment | MVP implementation | Upgrade path |
|---|---|---|---|
| Self-hosted OCR-VLM + Tesseract second reader + Google DAI fallback | SIMPLIFIED | Born-digital text-layer path first; one managed OCR API for scans (English) (04). `ocr_conf` stored per anchor. | Self-host for cost or residency; add a second reader for critical tokens (03_P1 §5). |
| Rhetorical-role model (InLegalBERT-class + CRF) | THIN | Heuristics (operative order, headers, "submissions of counsel" cues) + LLM labelling **only for the curated head** of authorities. Other anchors get `rhetorical_role = UNKNOWN`. | Train the RR model once ≥ 150 labelled judgments exist; backfill with a new `pipeline_version` and a new generation. |
| Proposition extraction (`prp_`) corpus-wide | THIN | Propositions only for the curated head (SC and NCLAT landmark rulings in the chosen workflows); work-level treatment elsewhere | Corpus-wide proposition extraction (05_P3 §5). |
| Point-in-time versions for all Acts; amendment grammar + round-trip | THIN | Current consolidated text with a "law current to" date for every instrument. **Full point-in-time versions only for the IBC (Amendment) Act 2026 changes** (the mandated test case) and any provision a full-mode RuleSpec anchors to. | Amendment-instruction grammar + round-trip verification (03_P1 §5.7) per Act, by usage. |
| Criminal-code crosswalk (IPC/CrPC/IEA → BNS/BNSS/BSA) | DEFERRED (conditional) | Only if s.138 NI Act is a top-3/4 trigger: then a minimal note that complaint procedure after 1 July 2024 follows BNSS, with the s.531 savings (02 §NI). No crosswalk table. | Full `CORRESPONDS_TO` crosswalk (21_india §6). |
| Learned sparse, late chunking, contextual headers by LLM, Indian embedder fine-tune | DEFERRED | Deterministic chunk headers; one embedding model via the API (04) | Bake-off and fine-tune per 04_P2 §10; new generation and alias swap. |
| Summaries (CARD, ROLE_SEGMENT) | THIN | One-line extractive + LLM summaries for digest items only, marked non-citable (`sum_`) | Case cards per 04_P2. |

## 5. Knowledge graph and propagation (P3, P4)

| Blueprint item | MVP treatment | MVP implementation | Upgrade path |
|---|---|---|---|
| Full predicate ontology | THIN | CITES; POSITIVE (FOLLOWS/APPLIES merged); DISTINGUISHES; DOUBTS; REFERS_TO_LARGER_BENCH; OVERRULES(_IN_PART); DECLARES_PER_INCURIAM; direct history (APPEAL_OF, AFFIRMS, REVERSES, SETS_ASIDE, MODIFIES, REMANDS, STAYS, DISMISSES_IN_LIMINE); INTERPRETS; STRIKES_DOWN/READS_DOWN; AMENDS/SUBSTITUTES/INSERTS/OMITS; COMMENCES | Add predicates: the ledger is predicate-agnostic. |
| Doctrine library `authority-core` (24 rules) | THIN | The rules needed for corporate forums: SC (Art. 141/144), HC superintendence, tribunal coordinate benches, NCLAT→NCLT (marked `contested` until an authority is verified; see 01 §2), bench strength for SC | Port the rest of `rul_IN_PREC_01..24` as forums are added. |
| Cascade L0–L3 + distilled L2 classifier | SIMPLIFIED | L0 direct history from appeal links (NCLT→NCLAT→SC) + L1 cue rules + L3 LLM on citations to the head set | Train L2 once ≥ 3k adjudicated treatments exist (05_P3 §10). |
| HITL editors (R1/R2), SLAs, two-person rule | THIN | The founder reviews tier-1 candidates for the curated head, with a partner lawyer for disputed ones; optionally a contract law-graduate reviewer (05 §4). Everything unreviewed shows CAUTION + `definitive=false` + "machine-detected" (D6). | Editor roles and queues per 05_P3 §5.9. |
| Depth-2 propagation, storms, campaigns, impact dry-run | DEFERRED | Depth-1 matching (a direct hit on a matter dependency); nightly recompute of AuthorityView for changed works | 06_P4 §10 full version. |
| Freshness API | THIN | A `law_current_to` per source, shown on answers, memos and badges | Full frontier API (06_P4). |
| Reprocess campaigns (shadow → gate → promote) | SIMPLIFIED | Re-run jobs over a scope with a new `pipeline_version` into a new index generation; run the eval suite; swap the alias | Campaign automation per 06_P4 §5.11. |

## 6. Retrieval, reasoning and verification (P5, P6, P8)

| Blueprint item | MVP treatment | MVP implementation | Upgrade path |
|---|---|---|---|
| PPR leg, HyDE, proposition leg, learned router, LTR, fine-tuned reranker | DEFERRED | Lexical + dense + BIND filter + treatment expansion + opponent-cited; RRF; one reranker (API or small self-hosted, see 04); mandatory CONTRA sweep with attestation | 07_P5 §10 full column, gated by eval. |
| Bench assessor on a different model family; heterogeneous advocate/opponent | DEFERRED / THIN | One opposing-counsel pass + one rebuttal round, same model family. The **verifier judge uses the second provider** (heterogeneous verification is kept). | Add the bench assessor (08_P6) behind an A/B test. |
| DEEP mode; automatic living-memo REVERIFY | DEFERRED | A "Re-verify" button on memos; alerts link to affected memos | Automatic REVERIFY on `impact.detected.v1` (08_P6). |
| Calibrated confidence bands (isotonic, conformal) | SIMPLIFIED | **"Uncalibrated preview"** statuses: VERIFIED / PARTIAL / UNSUPPORTED / CONTRADICTED / BAD_LAW / UNVERIFIABLE, with no probability bands | Calibrate once ≈1,500–2,000 adjudicated claims exist (10_P8 §10). |
| Self-hosted small NLI checker | SIMPLIFIED | The LLM judge from the second provider + deterministic checks C0–C3, C5–C10 | Fine-tuned checker (10_P8 §10). |
| Gold sets at blueprint size | THIN | The 06 plan: 20–30 matters + synthetic suites | Grow via P9 and more firms. |

## 7. Workspace, feedback and product (P7, P9, P10)

| Blueprint item | MVP treatment | MVP implementation | Upgrade path |
|---|---|---|---|
| PST/OST, WhatsApp exports, XLSX, audio; DMS connectors | DEFERRED | PDF (native + scan), DOCX, EML (+ MSG if cheap), ZIP | Add ingest adapters (09_P7 §10). |
| eCourts CNR sync, cause-list matching | DEFERRED | Manual hearing entry + reminders + ICS export | P0 feeds per D20.1. |
| Erasure cascade (`erasure.requested/applied/completed.v1`) | THIN (events kept) | Matter purge job emits the three events; consumers are in-process | Distributed consumers when Kafka arrives. |
| Privacy Gate, S0–S3 releases, `kg.proposal.v1` flows, DP aggregates | DEFERRED | `feedback_event` + `retrieval_served` logs only; weekly manual triage by the founder. Corrections to public-law facts become manual review tasks. | Privacy Gate per 11_P9 when a second firm joins (it is meaningless with one firm). |
| Personalization memory, LoRA adapters, IPS-LTR | DEFERRED | — | 11_P9 §10. |
| Command-bar grammar (12 verbs), statute timeline UI, crosswalk explorer, graph view | THIN | One smart search box that recognises citations, provisions (e.g. "IBC s.7"), party names and questions | Add verbs incrementally (12_P10). |
| Word add-in (cite-check in Word, living citations) | DEFERRED | DOCX export of reply skeletons and grids; cite-check by upload | Office.js add-in (12_P10 §10, M2). |
| WhatsApp / push / SMS alerts | DEFERRED | In-app + email | WhatsApp Cloud API MINIMAL content (12_P10). |
| PWA / mobile | DEFERRED | Responsive web | PWA (12_P10). |
| Judge pages | DEFERRED | — | List-only pages; no outcome statistics, ever (22 §6). |
| PLC Access API / MCP | DEFERRED | — | After M2 coverage and opinions (D13, D19.10). |
| On-prem (D4/D4h) | DEFERRED | — | Only with ≥ 2 signed letters of intent (22 §6). |

## 8. Never, by default (carried from the blueprint)

- **A graph database as system of record.** Postgres is the system of record; graph DBs serve only as analytics exports (D1; 22 §6).
- **Win probabilities, judicial analytics, outcome statistics by judge.** None (08_P6; 12_P10).
- **LLM-computed deadlines.** The LLM extracts candidate trigger dates with quotes; the lawyer confirms; the Procedural Clock computes (08_P6).
- **Machine-translated text as a support anchor** (D8).

## 9. Re-entry order (after the pilot)

The order follows partner value and the blueprint's roadmap (22 §3.4–§3.6):
1. HC own-site deltas for the 3 HCs + an NCLT daily feed via allowed paths.
2. Word add-in.
3. Calibrated confidence bands.
4. Automatic REVERIFY + depth-2 propagation.
5. Hindi.
6. Kafka/Temporal/OpenSearch, when a second firm or the scale triggers above are hit.
7. Privacy Gate + learning loops (needs ≥ 2 firms).
8. Remaining tribunals and HCs.
9. On-prem only on demand.
