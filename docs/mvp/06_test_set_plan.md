# 06 — Test Set Plan (gold set from closed partner matters)

**Purpose.** This file defines how we build the MVP's gold set from 20–30 *closed* matters at the design-partner firm, plus a few corpus-level suites, and how we score every release against it. It cuts down the blueprint's evaluation design (10_P8 §5.10, §10; 22 §5) to a two-engineer team and about 5 lawyer-hours a week. Statuses stay **"uncalibrated preview"** throughout the MVP: we measure error rates, but we do not yet claim calibrated confidence bands (10_P8 §10, 22 §3.3).

---

## 1. Principles

1. **Real matters first, synthetic second.** A closed matter has three things no synthetic case has: the notice or petition the firm actually received, the response it actually filed, and the deadlines it actually worked to. Synthetic cases are added only for edge cases real matters will not cover, such as point-in-time traps and seeded cite-check errors.
2. **Zero tolerance where errors are dangerous.** Wrong deadlines, fabricated anchors and bad law shown as good law are gating failures (10_P8 §5.11). Everything else is *reported* with confidence intervals, not gated, until the gold is large enough (22 §3.3 exit criteria).
3. **The firm's own work is a floor, not a ceiling.** The authorities a firm cited in its filed reply are a sample of the relevant law, not all of it. We therefore measure **recall against the firm's set** and **precision by lawyer review** of the extra items the system finds.
4. **Gold stays in the firm's deployment.** Matter documents and annotations are tenant data (`tenant_id` set). They never enter the public corpus (blueprint spine A; 11_P9). Only public-law test cases, such as statute point-in-time questions, are corpus-level.

## 2. Consent, privilege and handling (before any document moves)

| Item | MVP handling | Owner |
|---|---|---|
| Firm authorisation to use closed matters for internal evaluation | Written approval from the firm's managing partner or GC, listing the matters. Client consent is needed if the engagement terms require it; this is a question in [07 Q4](07_partner_firm_questions.md). | Partner firm |
| Privilege | Documents stay inside the firm deployment, under app-level matter permissions limited to the founder and named partner lawyers. Every access is audit-logged. No third-party annotators in the MVP. | Founder |
| LLM processing of matter text | Runs through the Model Gateway under the provider terms the partner approves (zero data retention where offered). The residency question goes to the firm ([07 Q3](07_partner_firm_questions.md)); until it is answered, gold runs use only the endpoints the firm approves. | Founder |
| Retention | Gold artefacts kept for the pilot plus 12 months unless the firm says otherwise. Matter purge deletes the matter's documents and annotations (`erasure.requested.v1` → `erasure.completed.v1`, see 03). | Founder |
| Naming the firm or matters externally | Never without separate written consent. The blueprint flags a possible Bar Council of India advertising/solicitation concern *(unverified; 12_P10 Q11)*. | Founder |

## 3. Matter selection (20–30 matters)

Stratify by the **trigger types the partner ranks in week 1** ([02](02_workflows_and_rules.md), [07 Q2](07_partner_firm_questions.md)).

| Stratum | Matters | Why |
|---|---|---|
| Each of the top 3–4 full-mode triggers (e.g. IBC s.8/s.9 notice→reply, s.7 petition, s.241–242 petition, SEBI SCN, arbitration s.34) | **5–6 each** (≈20) | Enough to see systematic misses per workflow; not enough for statistics, which is acceptable for a pilot. |
| General-mode triggers | **1–2 each** (≈5) | Checks that general mode is honest: no deadline guarantees and clear banners. |
| Spread inside each stratum | Mix of forums (NCLT benches, NCLAT, HC, SAT, arbitral tribunal); outcomes (won, lost, settled); for IBC, at least one where a pre-existing dispute was raised and one where it was not | Avoids training our expectations on one bench or one fact pattern. |
| Recency | Prefer matters closed in the last 3–5 years; include ≥ 3 that straddle a change in law | Exercises point-in-time logic. IBC 2026 traps are mostly synthetic (§5.6), because few closed matters will postdate 26 May 2026. |

**Exclude** matters the firm considers too sensitive, matters with unresolved privilege questions, and matters where the incoming document is mostly in a language other than English (Hindi is deferred; see 08).

## 4. Per-matter package and the 30-minute answer-key interview

**Documents** (an associate collects them once, ~20 minutes per matter):
1. The incoming trigger document (notice, petition, SCN, award or order).
2. The firm's filed response (reply, objections, written statement, appeal memo).
3. Key orders and the final order, if any.
4. The internal deadline note or diary entry, if one exists.

**Answer-key interview** (30 minutes with the lawyer who ran the matter; the founder records it in a structured form):

| Field | Captured as |
|---|---|
| Issues that mattered (3–8) | Free text. The founder normalises it to the issue templates in 02. |
| Authorities relied on, and why | Taken from the filed response. The lawyer marks the 3–5 that carried the matter. |
| Adverse authorities the team worried about | List with how each was handled: distinguished, conceded or ignored. **This field is the most valuable one in the set.** |
| Deadlines worked to | Each with its trigger event, trigger date, the rule the team applied, and the date it filed. |
| Evidence and documents prepared | Checklist |
| Opponent's main claims | List with the paragraphs of the trigger document they come from |
| Anything the team got wrong or nearly missed | Free text; feeds trap cases |

Total partner time is **≈ 20–30 × 30 min ≈ 10–15 lawyer-hours**, plus 2–3 hours to select the matters. This fits the ~5 hrs/week budget over weeks 2–8 (05).

## 5. Annotation schema and derived suites

The founder annotates against the answer key, about 1.5–2 hours per matter (≈40–55 founder-hours in total, scheduled in 05). One partner lawyer spot-checks 20% of the annotations. Each suite below maps to a capability and a blueprint gold set (10_P8 §5.10).

### 5.1 G-Extract — facts, parties, dates, amounts (capability 5)
- **Gold:** from each trigger document, every party (name, role, CIN or PAN if present), every date with its event type, the amounts claimed and the relief sought.
- **Metrics:** precision and recall per field type. Date-event pairing accuracy is scored separately, because a right date with the wrong event is worse than a missed date.

### 5.2 G-Deadline — Procedural Clock (capability 4) — **ZERO TOLERANCE**
- **Gold:** (a) every golden test vector in [02](02_workflows_and_rules.md) for each *activated* RuleSpec, at least 2 per rule, with month-end and holiday edge cases; (b) the deadlines from the answer keys, recomputed from the trigger date the lawyer gave.
- **Gate:** **100%** match on (a), and every disagreement on (b) investigated. A disagreement has one of three causes: a rule error (fix the rule), a fact error (wrong trigger date), or a practice difference, such as the firm filing early (record it as a note).
- **Rule:** no RuleSpec ships as active until it passes, and only RuleSpecs marked VERIFIED in 02 can be activated. TO VERIFY rules show "verify manually" and never a computed date.

### 5.3 G-Issue and G-Opponent — issue spotting (capability 3)
- **Metrics:** issue recall against the gold issues (the lawyer's issues mapped to the system's, judged by the founder, with disagreements decided by the lawyer); opponent-claim recall with correct source paragraph.
- **Target (proposal):** issue recall ≥ 0.8 on full-mode triggers.

### 5.4 G-Authority and G-Adverse — retrieval and authority (capabilities 1, 2, 3)
- **Gold:** the authorities the firm relied on (positive) and the adverse authorities it worried about.
- **Metrics:**
  - recall@20 of relied-on authorities in the memo's EvidenceBundle;
  - **adverse recall**, the share of the firm's adverse authorities that the system surfaced;
  - precision@10 by lawyer review of the top extra items (sample 5 matters per eval run).
- **Targets (proposals, not gates):** relied-on recall@20 ≥ 0.6; adverse recall ≥ 0.7. Adverse recall comes first because missing binding adverse authority is the costliest error (07_P5).

### 5.5 G-Claim — claim support (capabilities 1, 3)
- **Gold:** each eval run samples 100–200 claims from generated memos and Q&A answers. The founder adjudicates each claim against its anchor as VERIFIED, PARTIAL, UNSUPPORTED, CONTRADICTED, BAD_LAW or UNVERIFIABLE (the 10_P8 taxonomy). A lawyer adjudicates every claim the founder marks uncertain.
- **Metrics:**
  - the *misgrounding rate* (real citation, wrong support), the Stanford typology our design targets (00; 10_P8 §3);
  - the unsupported rate;
  - agreement between the P8 verifier and the human adjudication, i.e. the verifier's own precision and recall.
- **Gate (zero tolerance):** fabricated anchors displayed = 0. Any claim shown with an anchor that does not exist or does not contain the quoted text is a release blocker.

### 5.6 G-Temporal — point-in-time and "enacted but not in force" (capabilities 1, 2, 8)
**Synthetic.** Built from the IBC (Amendment) Act 2026 table in [02](02_workflows_and_rules.md) Part A §8.3 (test questions with expected answers), plus:
- (a) as-of questions either side of 26 May 2026;
- (b) questions on provisions enacted but not notified, where the system must answer "enacted, not in force as of <date>";
- (c) Corporate Laws (Amendment) Bill 2026 questions, where the system must say it is a bill under JPC examination and never present it as law;
- (d) s.10A IBC (the COVID suspension window) as a historical point-in-time check *(if verified in 02)*.

Target: 30–50 items; **gate: 100%** on (b) and (c), which are sentinel-class.

### 5.7 G-Cite — cite-check (capability 7)
Built from the firm's **filed responses** (our drafts) and **incoming orders** in the closed matters:
1. **Natural pass.** Run cite-check on the documents as filed and record what it flags. A lawyer reviews a sample of flags for false positives.
2. **Seeded errors (perturbation).** For 10 documents, a script injects 5–8 known errors each:
   - non-existent citation;
   - wrong reporter page;
   - wrong paragraph pinpoint;
   - misquote (a word changed);
   - a citation to an authority with a verified negative treatment;
   - a statutory provision cited in a form not in force on the document date. IBC 2026 traps go here.
- **Metrics:** detection rate per error type, and the false-flag rate on clean citations.
- **Targets (proposals):** existence and resolution errors ≥ 0.95, misquote ≥ 0.8, pinpoint ≥ 0.7, status ≥ 0.9 where the treatment is verified.
- **Unresolved is not wrong.** A citation the MVP corpus does not cover is reported as *"not in MVP corpus"*, never as *"wrong"*. Its false-flag rate is tracked separately.

### 5.8 G-QA — research questions (capability 1)
- **Gold:** 60–100 questions written by partner lawyers, about 2 per week across the pilot. Others are derived from matter issues, for example "Is a pre-existing dispute raised only in reply to the s.8 notice sufficient?".
- **Scoring:** a lawyer grades each answer in 2 minutes as correct, partially correct or wrong. A claim-level check uses G-Claim.

### 5.9 G-Alert — alert drill (capability 8)
- **Time-travel drill** (06_P4 §9; 22 §3.3): seed demo matters with the authorities and provisions from closed matters, then replay historical events. These are later judgments that reversed, set aside or overruled authorities those matters relied on, plus amendments and notifications to the provisions they relied on.
- **Metric:** matter-level alert recall on the replayed events, plus the false-alert rate per week of replay.
- **Target (proposal):** recall ≥ 0.9 on direct-history and verified negative-treatment events.

### 5.10 Sentinels — bad-law leakage (capability 2) — **ZERO TOLERANCE**
- **Gold:** a curated list of 30–50 corporate-law authorities whose negative treatment is **verified word for word** by the founder and a partner lawyer before the list is used (D23.8). Candidates come from the curated head in 01/03.
- **Gate:** none of them may ever be shown as GOOD law or cited without its negative treatment, in Q&A, memos or cite-check.

## 6. Scoring, gates and cadence

| Suite | Gate type | MVP gate | Reported |
|---|---|---|---|
| G-Deadline (activated rules) | Zero tolerance | 100% | Per rule |
| Sentinels (bad-law leakage) | Zero tolerance | 0 leaks | Per surface |
| G-Claim fabricated anchors | Zero tolerance | 0 | Per run |
| G-Temporal (b) and (c) | Zero tolerance | 100% | Per item |
| G-Extract, G-Issue, G-Authority, G-Adverse, G-Claim (rates), G-Cite, G-QA, G-Alert | Reported with 95% CIs, no gate | Proposal targets above | Per trigger type and per forum |

**Cadence.**
- **Every change to a prompt, model, RuleSpec, parser or ranker:** the L0 checks run (unit tests + golden vectors + sentinels, ≈ minutes), then the L1 checks (the full suite on the frozen gold, ≈ 1 hour, about $20–40 of LLM calls at MVP prices; see 04). The release is blocked if any zero-tolerance gate fails.
- **Comparing two versions:** for the non-gated metrics, report the paired difference with a bootstrap CI over matters, following the blueprint's non-inferiority policy (D11). A drop whose CI excludes zero is not a gate in the MVP, but the founder must sign it off in the changelog.
- **Eval runs** at weeks 8, 12, 16 and 20 (05), each with a one-page scorecard shared with the partner.

## 7. Storage (tables in 03)

| Table | Contents |
|---|---|
| `gold_set` | Name, version, frozen_at, scope (TENANT_PRIVATE / PUBLIC) |
| `eval_case` (`evc_`) | Inputs (trigger pdoc refs or a question), expected outputs (JSONB per suite schema), stratum tags, source (MATTER / SYNTHETIC / PERTURBATION) |
| `eval_run` (`evr_`) | `pipeline_version` tuple, timestamps, cost |
| `eval_result` | Per case, per metric; adjudications with adjudicator role |

Gold sets are **frozen and versioned**. Once a case has been used to tune prompts it moves to DEV. A sealed EXAM split (20% of matters) is never looked at during prompt work (10_P8).

## 8. Timeline and hours

| Weeks | Activity | Partner lawyer-hours | Founder hours |
|---|---|---|---|
| 1–2 | Consent and authorisation; choose matters | 3 | 4 |
| 2–6 | Associate collects document packages; 30-minute interviews | 10–15 (+ associate time) | 15 |
| 4–9 | Annotation; 20% spot-check | 3 | 40–55 |
| 3–9 | Synthetic suites: G-Temporal, G-Cite perturbations, sentinel list verification | 3 (verify sentinels) | 15 |
| 8, 12, 16, 20 | Eval runs, scorecards, adjudication of uncertain claims | 4 × 1.5 | 4 × 4 |
| 10–20 | G-QA questions written by lawyers | ~10 | 3 |
| **Total** | | **≈ 35–40** | **≈ 95–110** |

This fits inside the overall lawyer budget in [05](05_build_plan.md) §4 (≈100 lawyer-hours over 20 weeks).

## 9. Risks

| Risk | Mitigation |
|---|---|
| The firm cannot release enough closed matters for one trigger type | Lower that stratum to 3 matters and add synthetic notices drafted by a partner lawyer (≈1 hour each). |
| The answer keys reflect one lawyer's style | Use two different lawyers per trigger type where possible, and report results per lawyer. |
| Overfitting prompts to the gold | Keep the sealed EXAM split, and add new matters during the pilot as fresh EXAM cases. |
| Founder annotation bias | The partner lawyer spot-checks 20%; every disagreement is logged and resolved before the gold is frozen. |
| Gold drifts as the law changes, e.g. a later NCLAT ruling changes the right answer | Gold items record `as_of_legal_date`. A changed answer creates a new version; the old one is not overwritten (blueprint's self-maintaining gold, 10_P8). |
