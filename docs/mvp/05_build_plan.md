# 05 — Build Plan (week by week)

**Team assumption** (the brief left it blank, so the brief's own example is used): **a technical founder + 1 full-stack engineer + partner-firm lawyers ≈ 5 hrs/week**. **Target:** partner lawyers using it on real work within **4–5 months**. This plan uses **20 weeks** with a stated buffer policy; §5 shows what changes under other team sizes.

**Earliest working demo: end of week 4.** A partner lawyer asks an IBC question and gets an answer whose every sentence is pinned to a paragraph of an NCLT/NCLAT/SC order or a section of the IBC, with click-to-source. **Real work starts in week 14** with 2–3 lawyers. **All 11 capabilities are live by week 18**, and weeks 19–20 are pilot hardening plus the go/no-go scorecard.

---

## 1. Capacity arithmetic

| Person | Engineering share | Weeks | Engineer-weeks |
|---|---|---|---|
| Founder | 60%. The other 40% (≈ 8 weeks) goes to the partner relationship, legal opinions and legal profiles, RuleSpec re-anchoring and sign-off coordination, gold-set annotation (≈ 95–110 h, [06](06_test_set_plan.md) §8) and tier-1 treatment review of the curated head | 20 | **12.0** |
| Full-stack engineer | 85% (meetings, ops, partner support) | 20 | **17.0** |
| **Total capacity** | | | **29.0** |

AI coding assistants are expected to help with boilerplate (CRUD, admin, tests), but **no speed-up is counted**. Any gain becomes buffer.

## 2. Work breakdown (engineer-weeks)

"Full" is the scope if nothing is staged. "Planned" is after the scope decisions in §3, all of which cut scope and none of which cut quality.

| # | Workstream (capability) | Full | Planned | What makes "planned" smaller |
|---|---|---|---|---|
| A | Platform: Django, SSO, RDS, S3, CI, Procrastinate, outbox, `pipeline_version`, Model Gateway, `LLMCallRecord`, audit log (03, 04) | 1.5 | 1.5 | — |
| B | Sources + legal gate: adapters for IBBI orders, NCLAT, SC (open dataset + delta), HC subsets, SEBI, SAT, CCI, statutes, 4 regulator feeds ([01](01_corporate_corpus_and_sources.md)) | 3.0 | 2.0 | **Staged corpus:** IBC-first sources by week 6. HC subsets, SAT, SEBI and CCI orders move to weeks 15–18. Feeds use one generic "listing → PDF" adapter. |
| C | Parsing: text layer + OCR, judgment paragraphs and metadata for 6–7 court formats, statute parser, anchors + stability, citation extraction + resolver | 5.0 | 3.5 | Court formats staged with B. **Clause-level anchors only for the ~10 instruments that RuleSpecs and full-mode triggers cite**; the rest get section-level anchors (grammar unchanged, just less depth) |
| D | Point-in-time IBC 2026 (expressions, `COMMENCES`, enacted-not-in-force) | 0.5 | 0.5 | — |
| E | Indexing: chunks, FTS, embeddings, pgvector, generations/aliases, Index Access Layer | 1.0 | 1.0 | — |
| F | Citator: assertion ledger, direct-history linking (NCLT→NCLAT→SC), treatment cascade on the head set, AuthorityView + corporate doctrine rules, review console | 3.0 | 2.5 | Review console = Django admin + 2 custom views |
| G | Retrieval + EvidenceBundle (intents, lexical + dense + BIND + treatment legs, RRF, rerank, CONTRA sweep, coverage) | 1.5 | 1.5 | — |
| H | Q&A answers + Claims + verification (deterministic checks + second-provider judge) | 2.0 | 2.0 | — |
| I | Matter workspace: upload, tenant parse, extraction with quotes, confirm UI, timeline, permissions | 2.0 | 2.0 | — |
| J | Procedural Clock: engine, RuleSpecs, conventions, calendars, golden tests, deadline UI | 1.5 | 1.5 | — |
| K | Strategy memo pipeline (job chain S0–S9, streaming UI) + trigger templates | 2.5 | 2.0 | **3 full-mode triggers** in the MVP. The 4th is a week-19+ stretch; its rules are already drafted (02). |
| L | Drafting: DOCX reply skeleton + para-wise grid | 0.75 | 0.75 | — |
| M | Cite-check (reuses C's extraction and H's checks) | 1.0 | 1.0 | — |
| N + O | Alerts (dependency index, impacts, matching, lifecycle, email) + digest + watchlists (shared matching) | 2.5 | 2.0 | One matching engine serves alerts and watchlists |
| P | Hearings (manual entry, reminders, ICS) | 0.5 | 0.5 | — |
| Q | Feedback capture + `retrieval.served` logs | 0.5 | 0.5 | — |
| R | Frontend shell: layout, PDF.js source viewer with highlight, badges, smart search box | 2.0 | 1.5 | Component library (no custom design system) |
| S | Eval harness: gold store, runner, scorecard | 1.0 | 1.0 | — |
| T | Security hardening, backups, runbooks, partner onboarding | 0.75 | 0.75 | — |
| | **Total** | **32.5** | **28.0** | |

**Result: planned 28.0 vs capacity 29.0, leaving a 1.0 engineer-week buffer (3%). That is too thin to promise.** So the plan uses a buffer policy instead of pretending:
1. **Protected path (must land by week 14):** A, B (IBC-first), C (staged), D, E, F, G, H, I, J, K (trigger 1), M, Q, R, S. That is ≈ 22 ew of the 28.0 (counting only the IBC-first part of B and C and trigger 1 of K), against ≈ 20.3 ew of capacity by week 14 (29 × 14/20). **Week 14 therefore only works if about 2 ew of trigger-1 memo polish and corpus breadth slip to weeks 15–16.** The schedule in §4 already reflects this.
2. **Weeks 15–18 deliver the rest:** K (triggers 2–3), L, N+O, P, T, corpus breadth (HC/SAT/SEBI/CCI).
3. **If buffer runs out**, slip in this order:
   - (i) trigger 3 to general mode;
   - (ii) SAT/CCI corpus to after the MVP;
   - (iii) watchlist types beyond STATUTE and PARTY.

   **Never slip:** zero-tolerance gates, verification, or the deadline-confirmation step.

**Realistic estimate.** P50 ≈ 21–22 weeks for everything in this plan; P80 ≈ 24 weeks. The 20-week plan is achievable only if no major surprise occurs. The likeliest surprises are a source becoming unavailable, OCR quality on scanned NCLT orders, and Postgres FTS ranking failing the week-8 test (04 §2.3).

## 3. Scope decisions that make it fit (all keep the 11 capabilities)

| Decision | Options weighed | Choice and why |
|---|---|---|
| Corpus breadth by week 14 | (a) everything in 01 at once; (b) **IBC-first** (IBBI NCLT/NCLAT/SC/HC orders + NCLAT site + SC subset + statutes), then the rest | **(b).** The IBC slice alone exercises every capability and the point-in-time test case. The other sources reuse the same adapter and parser shapes. |
| Statute anchor depth | (a) clause-level everywhere; (b) **clause-level for the ~10 instruments the rules cite, section-level elsewhere** | **(b).** The anchor grammar is identical; deeper parsing later only adds child anchors, which the stability protocol handles. |
| Full-mode triggers | (a) 4 now; (b) **3 now, 4th as stretch** | **(b).** Each full-mode trigger needs templates and gold matters, and the third and fourth add less value than finishing alerts and the digest. |
| Treatment review | (a) review every machine-detected negative (≈ 5,400 at backfill, 04 §4.4); (b) **review the curated head (≈ 300–500 candidates)** and show everything else as CAUTION + `definitive=false` | **(b).** This is honest under D6. Reviewing everything needs about 2.5–6 reviewer-months that the team does not have. A part-time law-graduate reviewer (§6) widens the head. |
| Review consoles | (a) custom React tools; (b) **Django admin + 2 custom views** | **(b)**, saving about 0.5 ew. |

## 4. Week-by-week schedule

F = founder, E = engineer. "Demo" = shown to the partner.

| Week | Engineering (F + E) | Founder non-engineering | Partner lawyers (≈ 5 h/wk) | Exit check |
|---|---|---|---|---|
| **1** | Repo, Django skeleton, CI, AWS Mumbai (RDS PG 18, S3, 2 EC2), SSO, schema v0 (03 §3.1–3.5), outbox + Procrastinate | Legal profiles for IBBI, NCLAT, SC and India Code; send the access questions to counsel (07 Q1); kick-off | Kick-off (1 h); **trigger ranking (07 Q2)**; consent for closed matters (07 Q4) | Deploys; SSO works |
| **2** | IBBI orders adapter (NCLT + NCLAT + SC sections); IBC + IBBI regs + AAA Rules statute ingest; text layer + Textract OCR | **Re-anchor the IBC RuleSpecs to the official text from an Indian network** (02 §0); calendars for NCLT/NCLAT/SC seeded | Rule-card sign-off session #1 (IBC, 1.5 h) | 5–10K IBC orders captured with `rights_class` |
| **3** | Judgment parser (NCLT/NCLAT formats), anchors + stability tests, statute parser (section/clause), citation extraction v1 (SCC/AIR/SCR/INSC/neutral + "CP (IB)/CA (AT)" case numbers) | Gold matter selection; associate starts collecting packages | Gold interviews begin (2 × 30 min/wk through week 8) | Anchor stability ≥ 99.5% on re-parse |
| **4** | Chunks, FTS, embeddings + pgvector generation 1 + alias, lexical/dense retrieval, Q&A v0 with claims pinned to anchors, source viewer | — | **DEMO 1** (30 min) | **Earliest working demo**: IBC research Q&A with click-to-source |
| **5** | Resolver + `identifier_alias`; direct-history linking (appeal chains); assertion ledger; SC subset from the open dataset | Re-anchor arbitration and Companies Act RuleSpecs (or those of the ranked triggers) | Rule sign-off #2 | Every CITES edge carries an evidence span |
| **6** | AuthorityView + doctrine rules (SC, NCLAT→NCLT, HC, coordinate benches); treatment cascade (cue rules + LLM) on the head; review console; badges in the UI | Tier-1 review of the head begins (≈ 4 h/wk); sentinels list | Sentinel verification (1 h) | Sentinels show no GOOD badge |
| **7** | Matter workspace: upload (PDF/DOCX/EML/ZIP), tenant parse, extraction with exact quotes, confirm UI, timeline, permissions | Annotation of gold matters (≈ 8 h/wk to week 9) | — | Extraction G-Extract run on 5 matters |
| **8** | Procedural Clock engine + trigger-1 RuleSpecs + golden vectors; deadline UI with confirm; **FTS ranking test on partner queries (04 §2.3)** | — | **DEMO 2**: closed matter → extracted facts + deadlines | G-Deadline 100% on activated rules; FTS decision recorded |
| **9** | Strategy memo pipeline S0–S9 for trigger 1 (job chain, streaming), EvidenceBundle with CONTRA sweep, opponent pass | — | — | Memo end to end on 3 gold matters |
| **10** | Verification v1 (C0–C3, C5–C10 deterministic + judge), gate PASS/PARTIAL/BLOCK, "uncalibrated preview" labels, re-verify button | Eval run #1 prep | Rule sign-off #3 | **Eval run #1** scorecard |
| **11** | Cite-check (upload → CitationAuditReport); point-in-time IBC 2026 expressions + G-Temporal suite | — | **DEMO 3**: memo + cite-check on closed matters | G-Temporal (b)(c) 100% |
| **12** | Feedback capture everywhere + `retrieval.served`; hardening; security checklist; backups/restore drill | Pilot onboarding material | Pilot users nominated (2–3) | Restore drill passes |
| **13** | Buffer / fix list from eval run #1; performance; trigger-1 polish | — | — | All zero-tolerance gates green |
| **14** | **PILOT START: real work** (research, citator, cite-check, matter workspace, deadlines, trigger-1 memos, feedback) | Daily support (≈ 3 h/wk) | Pilot use on live matters; 1 h weekly feedback session from here on | ≥ 2 lawyers active |
| **15** | Trigger-2 templates + rules; drafting DOCX skeleton + para-wise grid; HC subsets (Delhi/Bombay/partner) from the open dataset | — | — | Drafting export used once |
| **16** | Alerts: matter dependency index, impact rows (new judgments, amendments, notifications), matching, lifecycle, in-app + email; time-travel drill harness | Eval run #2 | — | **Eval run #2**; G-Alert drill |
| **17** | Digest (06:30 IST email) + watchlists (STATUTE, PROVISION, TOPIC, PARTY, COURT); regulator feeds (MCA/SEBI/IBBI/RBI); Bill watch (Corporate Laws (Amendment) Bill 2026) | — | — | First digest sent |
| **18** | Hearings (manual entry, reminders, ICS); trigger-3 templates + rules; SEBI/SAT/CCI corpus (if legal profiles approved) | — | — | **All 11 capabilities live** |
| **19** | Fix list from pilot feedback; stretch items if buffer remains: NCLT/NCLAT cause-list parsing (≈ 0.3 ew), then the 4th trigger; docs and runbooks | — | — | — |
| **20** | Hardening; **eval run #3**; go/no-go scorecard | Scorecard, decision memo | Go/no-go meeting (1 h) | Decision recorded |

## 5. Sensitivity: other team shapes

| Team | Outcome |
|---|---|
| **Founder + 1 engineer** (this plan) | 20 weeks with 3 full-mode triggers and a 3% buffer; P50 ≈ 21–22 weeks |
| Founder + 2 engineers | 20 weeks with 4 full-mode triggers, HC own-site deltas for 3 HCs, and a ≈ 20% buffer |
| Founder (non-technical) + 2 engineers | ≈ 22–24 weeks. The founder still owns the legal, partner and gold work; engineering capacity ≈ 34 ew, minus about 2 ew for onboarding |
| Founder + 1 engineer + a part-time law-graduate reviewer (recommended, §6) | Same dates; the definitive citator head grows from ≈ 300 to ≈ 1,500 candidates, and the founder recovers ≈ 2 weeks of time |
| Founder alone | Not viable for 11 capabilities in 5 months; ≈ 10–12 months |

## 6. Recommended low-cost additions (not assumed in the plan)

1. **Part-time law-graduate reviewer** (≈ 15–20 h/week from week 6). This widens the reviewed citator head and takes on the first pass of gold annotation. The cost is an estimate to be set with the partner. 04 §4.4 prices reviewer time at $700–1,400 per reviewer-month (≈ ₹62K–1.2 lakh, D23.1).
2. **One partner associate for 2–3 hours a week in weeks 2–8** to collect gold matter packages and answer factual questions. This keeps the partner lawyers' own 5 hours a week for sign-off and interviews.

## 7. Lawyer-hours budget (≈ 100 h over 20 weeks)

| Activity | Hours |
|---|---|
| Kick-off, trigger ranking, questions (07) | 6 |
| RuleSpec sign-off sessions (3–4 × 1.5 h) | 6 |
| Gold-set selection + 30-minute interviews + spot-checks ([06](06_test_set_plan.md)) | 18–21 |
| Sentinel verification + disputed tier-1 treatments | 6 |
| Demos (3 × 0.5 h) + go/no-go | 3 |
| Weekly pilot feedback (weeks 14–20, 1 h/week) | 7 |
| G-QA questions (≈ 2/week from week 10) | 10 |
| **Total** | **≈ 56–60 h** (the rest of the 100 h is slack for pilot questions) |

## 8. Definition of done for the MVP (week 20)

- All 11 capabilities usable by pilot lawyers, each meeting the scope in [00](00_mvp_spec.md) §4.
- **Zero-tolerance gates green** ([06](06_test_set_plan.md) §6):
  - G-Deadline 100% on activated rules;
  - sentinels 0 leaks;
  - fabricated anchors 0;
  - G-Temporal (b)(c) 100%.
- Reported metrics (with confidence intervals) for extraction, issues, authority and adverse recall, claim support, cite-check, alerts.
- Every activated RuleSpec re-anchored to official text and signed off by a partner lawyer.
- Every source running under an APPROVED legal profile.
- Restore drill passed; security checklist done.
- Go/no-go decision recorded with the partner.
