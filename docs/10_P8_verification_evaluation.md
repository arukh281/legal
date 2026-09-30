# P8 — Verification, Trust and Evaluation

**Abstract.** P8 is the platform's quality authority. It has two halves that share one data model. The first is the **Verifier**, an online service. It takes typed `Claim`s from P6 (memos, answers, drafts) and checks each one against a *legal-warrant* ladder. Does the anchor exist? Is the quote exact? Does the **cited paragraph**, and not merely the case, entail the claim? Is that paragraph the court's holding, or counsel's submission, obiter or a dissent? Is the authority good law as of the relevant date? Is it binding on this forum? Are the dates, numbers and old↔new criminal-code sections right? The output is a `VerificationReport`: a per-claim status, a calibrated confidence, a display band and a PASS / PARTIAL / BLOCK gate. The second half is the **Evaluation Platform**. It holds versioned, signed gold sets built with the design-partner firm, a metric catalogue for every phase (P0–P10), a regression-gating policy for every model, prompt, parser, index or ontology change, production audit sampling, and the Design Partner Program (consent, MoU/DPA, privilege, annotation, incentives). Four findings shape the design. (1) Commercial legal RAG tools hallucinated 17–33% of the time, and their most insidious failure was *misgrounding*: a real source that does not support the claim [P8-1]. (2) The hard verification case is not a fake case but a **wrong pinpoint**. Frontier models caught only 37–61% of wrong-pinpoint corruptions in court opinions [P8-4], and the best agentic checker reached 52.8% recall on incorrect pincites [P8-3]. (3) Citation-graph "hallucination rates" mostly measure the *coverage of the oracle*, not the model [P8-6]. (4) Indian courts have set aside orders in 2025–2026 because they rested on fabricated or misrepresented case law, including Supreme Court decisions in 2026 [P8-8]. So P8 (a) verifies at **anchor level with role and status awareness**, (b) separates *UNVERIFIABLE* (we could not check) from *UNSUPPORTED* (we checked and it fails), (c) shows **ordinal, audited confidence bands** instead of raw percentages, and (d) gates every change on *statistically powered* non-inferiority tests plus zero-tolerance sentinel suites. Target verifier cost is ≈US$0.02–0.05 per Q&A answer and ≈US$0.2–0.6 per full memo. Target latency is ≤4 s p95 for an answer and ≤20 s p95 per memo section. Both are estimates (§5.14).

---

## 1. Purpose and scope

**Purpose.** Make "every claim traces to a specific paragraph of a specific source" (brief) *true and measurable*. The platform should never show a lawyer an unverified legal proposition as verified. It should tell the lawyer how reliable each shown claim is, in terms that match measured error rates. And it should prove, before and after every change, that quality has not regressed on the slices that matter in Indian practice: Hindi and regional-language material, bad OCR, the tribunals, the IPC→BNS transition, and adverse authority.

**In scope**
1. **Online claim verification.** Check ladder C0–C12 (§5.3), status assignment, repair hints for P6, and PASS/PARTIAL/BLOCK gates.
2. **Hallucination detection** across answers, memos, drafts and **uploaded third-party documents** (opponent pleadings, lower-court orders, a firm's own drafts), exposed as the Citation Audit service (§5.8).
3. **Confidence**: a calibrated per-claim probability, conformal display thresholds, UI band semantics and the "trust ledger" (§5.6–5.7).
4. **Re-verification** when law changes (graph deltas) or when the claim text is edited (drafts).
5. **Evaluation platform**: gold-set store, eval runner, metric catalogue P0–P10, benchmark adapters (IL-TUR, LegalBench, etc.), LLM-as-judge policy, regression gates in CI/CD, shadow/canary evaluation, production audit sampling and drift detection (§5.10–5.12).
6. **Gold-set construction with the design partner**, and the **Design Partner Program** (§5.13).
7. **Adjudication of eval-case candidates** proposed by P9 (`eval.case.proposed.v1`).

**Out of scope** (owned elsewhere)
- Generating claims and repairing them: P6. P8 returns hints (`narrowed_text`, `suggested_anchor_ids`); P6 decides.
- Anchors, citation parsing and resolution: P1. Authority status, binding rules and the crosswalk: P3. Retrieval: P5. P8 *consumes* these, *tests* them and *never writes* them. P8 findings reach P3 only as review tasks via P9 or ops.
- Model routing and promotion mechanics: 13_cross_cutting.md (Model Gateway). P8 supplies the gold sets, metrics and gate verdicts that the Gateway's `ModelTaskContract.eval` refers to.
- UI rendering: P10. P8 defines the *semantics* of bands and badges.

**Design principles**
- **V-1 Verify the warrant, not the vibe.** A legal claim is warranted only if its authority exists, applies to the jurisdiction, is current for the date of analysis, has the status the system represents, and supports the proposition [P8-5]. Every one of these is a separate, logged check.
- **V-2 Deterministic before probabilistic.** Existence, quote hash, metadata, status, binding, dates and deadlines are computed exactly. Models judge only entailment and role subtleties.
- **V-3 Independence.** The verifier never uses the generator's model family as its only judge. LLM evaluators favour their own generations [P8-36], and self-verification is a documented multi-agent failure (P6 §3, MAST).
- **V-4 Honest uncertainty.** "Could not check" is never reported as "false", and "passed the checks" is never reported as "certainly correct". Displayed confidence is tied to *audited* error rates.
- **V-5 Every gate is a statistical test.** Point estimates on small slices do not block or pass releases. Confidence intervals do [P8-42].

---

## 2. Input and output contracts

### 2.1 Synchronous inputs

**I1 — `VerifyRequest`** (P6 → P8; also P10 for draft edits, via P6). Implements P6's `POST /verify` (P6 doc §2).
```ts
type VerifyRequest = {
  request_id: string;                       // ULID; idempotency key
  tenant_id: string; matter_id?: string;
  subject: { kind: "MEMO_SECTION"|"ANSWER"|"DRAFT"|"EXPORT"|"REVERIFY"; id: string; section?: string };
  claims: Claim[];                          // spine §H Claim + P6 C2 extension (issue_ids[], origin_role, strength?, assumptions[])
  ledger_ref: string;                       // P6 Citation Ledger: handle → anchor_id map (closed world)
  evidence_bundle_ref?: string;             // P5 EvidenceBundle (coverage, stance, adverse items)
  matter_context_ref?: string;              // P7 MatterContext (private anchors; resolved only inside the tenant boundary)
  as_of_legal_date: string;                 // ISO date
  as_known_at?: string;                     // default now
  forum: { court_id: string; bench_strength?: number };
  jurisdiction_state?: string;
  lang_ui: string;                          // for narrowed_text language
  budget: { latency_ms: number; max_llm_calls?: number };
  mode_flags?: { strict_export?: boolean }  // EXPORT: re-run C6/C7 at graph head, no cache
};
```
`Claim` (spine §H) is used unchanged, including `support[{anchor_id, quote, support_type}]`, `contrary[]`, `confidence` (P6 raw; P8 replaces it) and `depends_on_claim_ids[]`.

**I2 — `AuditRequest`** (P10/P6/P7 → P8), new. Used to audit an arbitrary document's citations (§5.8).
```ts
type AuditRequest = { request_id: string; tenant_id: string; matter_id?: string; pdoc_id?: string;
                      parsed_doc_uri: string;              // P1/P7 ParsedDocument
                      as_of_legal_date?: string;           // default: document date from ParsedDocument.metadata
                      forum?: { court_id: string; bench_strength?: number };
                      purpose: "OWN_DRAFT"|"OPPONENT_FILING"|"LOWER_COURT_ORDER"|"OTHER";
                      budget?: { max_mentions?: number /*default 2000*/; max_llm_calls?: number; deadline_ms?: number } };
```
`AuditRequest` is always processed asynchronously. Mentions beyond `max_mentions` are reported as `UNVERIFIABLE` with reason `BUDGET_EXHAUSTED` rather than silently dropped (see §8.R).

**Read dependencies** (all read-only; P8 holds no write rights on PLC)
| Dependency | Owner | Fields P8 needs |
|---|---|---|
| Anchor read API `GET /anchors/{anchor_id}?as_of=` | P1/P2 | `text`, `text_hash`, `lang`, `rhetorical_role`, **`speaker`/`opinion_role`** (majority/concurring/dissent), page+bbox, **`ocr_conf`**, `structure_conf`, alias/tombstone resolution, sibling expressions (e.g. `hi`↔`en`) |
| Graph Query API (`AuthorityView`, provision-at-date, `CORRESPONDS_TO` crosswalk, propositions) | P3 | `status`, `definitive`, `reason_codes`, `status_confidence`, `binding_on_forum`, `binding_basis`, `court_level`, `bench_strength`, `decision_date`, `graph_watermark` (P3 doc §2.2) |
| Citation parser + alias resolver (library + service) | P1 | parse citation strings in claim text; `identifier_alias` lookups |
| Rule engine `RuleSpec`/`Deadline` (R-handles) | P6 | deterministic recomputation of PROCEDURAL claims |
| MatterContext / private anchors | P7 | fact `asserted_by`, trust labels (`TENANT_OPPOSING_DOC`, etc.), privilege flags |
| Model Gateway tasks `p8.entail_small@n`, `p8.entail_judge@n`, `p8.role_judge@n`, `p8.decompose@n` | XC | typed outputs; `pipeline_version` lineage |

### 2.2 Asynchronous inputs (events)
| Event | Producer | P8 use |
|---|---|---|
| `graph.delta.v1` (with `graph_watermark`, `status_changes[].definitive/reason_codes`, per P3 S3-3) | P3 | invalidate the verification cache; mark gold items stale (§5.10.6); generate temporal-trap sentinels from new definitive NEGATIVE statuses (§7) |
| `eval.case.proposed.v1` (`EvalCaseCandidate`) *(P9-proposed spine addition, not yet in spine §G)* | P9 | adjudication queue → gold/regression suites |
| `model.endpoint.candidate.v1` / registry change *(XC-owned name; if absent, P8 polls the registry)* | Model Gateway | trigger offline gate runs |
| `release.candidate.v1` (CI) | build system | trigger L1/L2 suites (§5.11) |
| `doc.parsed.v1` with a changed `pipeline_version` | P1 | anchor-stability canary checks on gold works |

### 2.3 Outputs

**O1 — `VerificationReport`** (P8 → P6, P10; spine §H, extended per §2.5)
```ts
type VerificationReport = {
  report_id: string;                         // "vrp_…"
  request_id: string; tenant_id: string;
  subject: VerifyRequest["subject"];
  as_of_legal_date: string; as_known_at: string;
  graph_watermark: number;                   // P3 watermark the status checks were read at
  anchor_generation: string;                 // P1/P2 anchor-store generation
  verifier_version: string;                  // "p8.verifier@1.3.0|small:minicheck-in@2|judge:<endpoint>@<snap>|calib:2026-09-15"
  claims: ClaimVerification[];
  gate: "PASS" | "PARTIAL" | "BLOCK";
  gate_reasons: string[];                    // e.g. "TIER1_CLAIM_FAILED:clm_…", "SECTION_ALL_WITHHELD"
  withheld_claim_ids: string[];
  coverage: { checked: number; verifiable_share: number; unverifiable_by_reason: Record<string, number> };
  created_at: string;
  supersedes_report_id?: string;             // set when a re-run at a newer watermark replaces an earlier report (§5.9)
  context_warnings?: string[];               // e.g. "FORUM_MISMATCH_WITH_MATTER", "AS_OF_DATE_MISMATCH_WITH_MATTER" (§8.R)
  signature: string;                         // Ed25519 over canonical JSON (exports embed it; §5.8)
};

type ClaimVerification = {
  claim_id: string; claim_hash: string;      // hash(text, support anchors, claim_type)
  status: "VERIFIED"|"PARTIAL"|"UNSUPPORTED"|"CONTRADICTED"|"BAD_LAW"|"UNVERIFIABLE";
  display_band: "VERIFIED"|"VERIFIED_WITH_CAVEAT"|"CHECK"|"WITHHELD";
  calibrated_confidence: number;             // P(claim correct and adequately supported); §5.6
  confidence_stratum: string;                // e.g. "LEGAL_PROPOSITION|SC|en|ocr_ok"
  warrant: {                                 // V-1: one verdict per warrant element
    exists: Verdict; quote_exact: Verdict; pinpoint_support: Verdict; role_ok: Verdict;
    status_ok: Verdict; binding_ok: Verdict; temporal_ok: Verdict; numeric_ok: Verdict; attribution_ok: Verdict;
  };
  checks: CheckResult[];
  subclaims?: { text: string; anchor_id: string; label: "ENTAILED"|"NEUTRAL"|"CONTRADICTED"; p: number }[];
  reason_codes: string[];                    // §5.4 taxonomy, e.g. "WRONG_PINPOINT", "ROLE_ARGUMENT_AS_HOLDING"
  narrowed_text?: string;                    // PARTIAL: entailed portion only
  suggested_anchor_ids?: string[];           // pinpoint re-anchoring hits in the same work (§5.3 C3b)
  authority_snapshot?: { target_id: string; status: string; definitive: boolean;
                         binding_on_forum?: string; status_confidence: number }[];
  human_review?: { required: boolean; queue: "TIER1_CLAIM"|"CROSS_LINGUAL"|"LOW_OCR" };
};
type Verdict = "PASS"|"WARN"|"FAIL"|"UNKNOWN"|"NA";
type CheckResult = { check_id: string; version: string; verdict: Verdict; score?: number;
                     detail?: Record<string, unknown>; latency_ms: number };
```

**O2 — `CitationAuditReport`** (P8 → P10/P6; new).
```ts
type AuditFinding = "NOT_FOUND"|"NAME_MISMATCH"|"WRONG_PINPOINT"|"MISQUOTE"|"MISREPRESENTS"|"NEGATIVE_STATUS"
                  |"UNDER_APPEAL_OR_STAYED"|"NOT_BINDING"|"SUPERSEDED_PROVISION"|"OK"|"UNVERIFIABLE";
type CitationAuditReport = {
  audit_id: string;                          // "aud_…"
  request_id: string; tenant_id: string; pdoc_id?: string; parsed_doc_uri: string;
  as_of_legal_date: string; graph_watermark: number; verifier_version: string;
  mentions: { mention_id: string; raw_text: string; anchor_id: string;        // where it occurs in the audited doc
              kind: "CITATION"|"STATUTE";
              resolved_target_id?: string; resolution_confidence: number;
              findings: AuditFinding[]; reason_codes: string[];                // §5.4 taxonomy
              status_at_doc_date?: string; status_today?: string;              // AuthorityStatus at both dates (§5.8 step 4)
              evidence_anchor_ids: string[]; note?: string;
              coverage_basis: "SCHEME_FULLY_HELD"|"SCHEME_PARTIAL"|"NOT_HELD" }[];
  summary: Record<AuditFinding, number>;
  truncated: boolean;                        // true if max_mentions was hit
  created_at: string; signature: string;
};
```

**O3 — Evaluation artefacts** (Postgres + object store; §5.10)
```ts
type EvalCase = {                            // superset of P9 EvalCaseCandidate
  eval_case_id: string;                      // "evc_…" — NOT `case_id`, which the spine reserves for Case (cas_…)
  gold_set_id: string;                       // "gld_…"
  version: number; split: "DEV"|"EXAM"|"SENTINEL";
  scope: "GLOBAL"|"TENANT_PRIVATE"; tenant_id?: string;
  task: "RESEARCH_QA"|"RETRIEVAL"|"CLAIM_SUPPORT"|"CITATOR_TREATMENT"|"AUTHORITY_STATUS"|"CROSSWALK"
       |"MEMO_SECTION"|"DEADLINE"|"CITATION_PARSE"|"RR_LABEL"|"OCR_PAGE"|"ALERT_PROPAGATION"|"INJECTION"|"CITATION_AUDIT";
  strata: { forum: string; subject: string; lang: string; ocr: "OK"|"LOW"; era: "PRE_BNS"|"POST_BNS"|"SPANNING"|"NA";
            task_type: string; perspective?: "PETITIONER"|"RESPONDENT" };
  input: Record<string, unknown>;            // question / claim+anchor / trigger ref / etc.
  as_of_legal_date?: string;
  expected: { must_include_anchors?: string[]; must_include_adverse?: string[]; must_not_include?: string[];
              label?: string; status?: string; deadline?: string; rubric_ref?: string };
  provenance: { authored_by_role: string; source: "GOLD_ROOM"|"RETRO_MATTER"|"SHADOW"|"P9_FEEDBACK"|"PERTURBATION"|"PUBLIC_BENCH"|"SENTINEL_AUTO";
                consent_ref?: string; adjudication: { annotators: number; alpha_batch?: number; adjudicator_role: string } };
  depends_on_ids: string[];                  // works/provisions/propositions: gold subscribes to graph.delta (§5.10.6)
  stale: boolean; canary_string: string;     // contamination detection
};
type EvalRun = { run_id /* "evr_…" */; suite_ids[]; candidate: { component, pipeline_version, task_id?, endpoint_id? };
                 baseline_run_id; metrics: Record<string, {value, ci95:[number,number], n}>; slices: Record<string, …>;
                 sentinel_failures: string[]; started_at; finished_at; cost_usd };
type GateDecision = { gate_id; run_id; decision: "PROMOTE"|"REJECT"|"WAIVED"; rule_results[]; waiver?: {by[], reason, expires} };
```

**O4 — Events (new)**
| Event | Producer → Consumers | data (minimum) |
|---|---|---|
| `verification.completed.v1` | P8 → P9 (tenant plane), P10 telemetry | report_id, subject, per-claim {claim_id, status, band, reason_codes}, verifier_version, tenant_id |
| `eval.run.completed.v1` | P8 → Model Gateway registry, P4 (backfill decisions), CI | run_id, candidate, gate decision, summary metrics |
| `eval.case.adjudicated.v1` | P8 → P9 | candidate_id, decision ACCEPTED/REJECTED/MERGED, eval_case_id? (closes P9's loop) |

All O4 events use the spine §G CloudEvents envelope unchanged. `tenant_id` is set for `verification.completed.v1` and for eval runs over `TENANT_PRIVATE` suites, and is `null` for GLOBAL eval events. `idempotency_key` = `report_id` / `run_id` / `candidate_id`. Example:
```json
{ "id":"01J…","type":"verification.completed.v1","specversion":"1.0","source":"p8/verifier@1.3.0",
  "time":"2026-09-30T06:10:04Z","subject":"vrp_01J…","tenant_id":"ten_…","traceparent":"00-…",
  "causation_id":"<VerifyRequest.request_id>","idempotency_key":"vrp_01J…","schema_version":"1",
  "data":{ "report_id":"vrp_01J…","subject":{"kind":"MEMO_SECTION","id":"mem_…","section":"adverse_authorities"},
           "gate":"PARTIAL","verifier_version":"p8.verifier@1.3.0|…",
           "claims":[{"claim_id":"clm_…","status":"PARTIAL","band":"VERIFIED_WITH_CAVEAT","reason_codes":["OBITER_AS_HOLDING"]}] } }
```
`data` carries IDs, statuses and reason codes only — never claim text or quotes (§5.9).

### 2.4 Handoffs
- **P6** calls `/verify` for each section. It uses `status`, `reason_codes`, `narrowed_text` and `suggested_anchor_ids` in its repair loop (P6 §5.7), and streams only sections whose gate allows it.
- **P10** renders `display_band` with reason chips and click-to-source. It shows `gate_reasons` in the diagnostic view, and embeds the signed report in exports.
- **P9** receives `verification.completed.v1` as machine labels (P9 §2), sends `eval.case.proposed.v1`, and receives adjudication outcomes.
- **Model Gateway (XC §4.6)** references `gold_set_id`s owned by P8. P8's `eval.run.completed.v1` updates `qualified_tasks`.

### 2.5 Proposed spine changes
| # | Target | Change | Justification |
|---|---|---|---|
| S8-1 | §H `VerificationReport` | Add status `UNVERIFIABLE`; gate `PARTIAL` (P6 already uses it); fields `display_band`, `warrant{…}`, `reason_codes[]`, `narrowed_text`, `suggested_anchor_ids`, `graph_watermark`, `anchor_generation`, `verifier_version`, `coverage`, `signature` | Oracle coverage drives measured hallucination rates [P8-6], so "cannot check" must not be reported as "unsupported". P6's repair loop needs hints. Exports need a reproducible, signed record. |
| S8-2 | §C anchors / anchor read API | Expose anchor-level `rhetorical_role`, `speaker`, `opinion_role` (MAJORITY/CONCURRING/DISSENT/REFERENCE_ORDER), `ocr_conf` and sibling-expression links | Needed for role checks (C4) and OCR-aware quote trust (C2). P1 already computes these (P1 §9 metrics); they must be addressable per anchor. |
| S8-3 | §G events | Add `verification.completed.v1`, `eval.run.completed.v1`, `eval.case.adjudicated.v1` | P9 needs machine labels and closure. The Gateway and P4 need gate outcomes. |
| S8-4 | §H new objects | `CitationAuditReport`, `EvalCase`, `EvalRun`, `GateDecision` | Shared by P6/P9/P10/XC. They are schema'd once here. |
| S8-5 | Policy (P9 §5.13, XC §4.6) | Replace "no regression > 1 point on any gold slice" with **non-inferiority at a slice-specific margin δ_s = max(1 pt, 2·SE_diff,s), one-sided 95%, plus zero-tolerance sentinels** | A slice of 200 binary items at p≈0.85 has SE≈2.5 pts. A 1-pt rule is therefore either noise-driven (it blocks good changes) or ignored [P8-42]. §5.11 gives the arithmetic. |
| S8-6 | §H `VerificationReport` gate granularity | The spine defines a *memo-level* PASS/BLOCK gate. P8 computes the gate per `subject` (answer or memo section) and defines the memo gate deterministically as: **BLOCK** if any section is BLOCK; **PARTIAL** if any section is PARTIAL; else **PASS** (§5.4). P6 may still stream non-blocked sections, but an export requires memo gate ≠ BLOCK | P6 streams per section (P6 §5.7); a single memo gate computed only at the end would delay every section. Making the aggregation rule explicit keeps P6, P10 and exports consistent |
| S8-7 | §B/§H naming | Eval objects use `eval_case_id` (`evc_…`), `gold_set_id` (`gld_…`), `run_id` (`evr_…`), `report_id` (`vrp_…`), `audit_id` (`aud_…`). The bare name `case_id` is **never** used for eval items | The spine reserves `case_id` (`cas_…`) for proceedings; the earlier draft of this doc reused it for eval items, which would collide in P9 joins |
| S8-8 | §F `AuthorityStatus` (P3-owned) | P8 consumes P3's proposed extensions `NEGATIVE_SIGNAL_UNDER_REVIEW`, `COVERAGE_GAP`, plus the `definitive` flag and direct-history cautions (`STAYS`, pending appeal, `REFERS_TO_LARGER_BENCH`). **If P3's extension is not adopted**, P8 maps `NEGATIVE_SIGNAL_UNDER_REVIEW` → `CAUTION` + `definitive=false`, and `COVERAGE_GAP` → `UNKNOWN` | Avoids a silent divergence: the C6 table (§5.3) is written against the extended enum, and this row states the fallback onto the spine's five values |
| S8-9 | §C anchor read API | Expose per-expression `authoritative: boolean` (which language version is the court's original/authentic text) alongside sibling-expression links | The cross-lingual rule (§5.5) must know which version is authoritative; it cannot assume English (many HC and district judgments are delivered in Hindi, while SC regional-language versions are translations) |

---
## 3. State-of-the-art survey (with citations)

### 3.1 How legal AI actually fails
- **Stanford RegLab (Magesh et al., preregistered; JELS 2025).** 202 queries. Lexis+ AI answered 65% accurately and hallucinated on ≈17%. Westlaw AI-Assisted Research: 41% and ≈33%. Ask Practical Law AI: 19% and ≈17%, with 62% incomplete answers. A response counts as a hallucination if it is *incorrect* or *misgrounded*, i.e. it cites a source that does not support the claim. Contributing causes were naive retrieval, **inapplicable authority** (wrong jurisdiction, overruled, superseded), reasoning errors and sycophancy toward false premises [P8-1]. The paper's stated contribution is a typology that separates hallucination from accurate answers, and a finding that vendor "hallucination-free" claims were overstated [P8-1].
- **General LLMs (Dahl et al., 2024).** GPT-4 hallucinated on 58% of verifiable questions about U.S. federal cases and Llama 2 on 88%. The models often failed to correct false legal premises, and **could not reliably predict when they were hallucinating** [P8-2]. Verbalised LLM confidence is systematically overconfident, and elicitation methods "struggle in challenging tasks, such as those requiring professional knowledge" [P8-32]. **Implication:** model self-reports can be *features* for calibration, never the confidence we display.
- **Vals Legal AI Report, Legal Research (Oct 2025).** 200 questions from U.S. firms, scored 50% accuracy, 40% authoritativeness, 10% appropriateness. All four AI products (Alexi, Counsel Stack, Midpage and ChatGPT) scored within 74–78% on the weighted score, against a lawyer baseline of 69%. Lexis+ AI and Westlaw declined to take part. Multi-jurisdiction questions cost ≈14 points. The legal tools' main edge over ChatGPT was authoritativeness (≈+6) [P8-10]. **Implication:** aggregate "accuracy" barely separates systems. Authority and warrant metrics do.
- **Harvey BigLaw Bench** reports an *answer score* and a *source score* separately, and finds that public foundation models "struggle significantly" to give verifiable sources [P8-11]. We adopt the split (§9).
- **Retrieval sets the ceiling.** Legal RAG Bench (built on 4,876 passages of the Australian *Victorian Criminal Charge Book*) uses a full factorial design and hierarchical error decomposition. It found retrieval to be "the primary driver" of legal RAG correctness, and found that many errors labelled hallucinations were retrieval failures [P8-7]. **Implication:** P8's end-to-end evals must attribute each failure to a phase (§5.10.5). A single hallucination number is not enough.

### 3.2 Citation checking: the hard cases
- **Taxonomy from real filings (Liu, Stammbach, Henderson, 2026).** More than 1,000 court filings contained fabricated citations, and the number grows year on year. The taxonomy comes from real filings, but the benchmark errors are mostly *synthetically injected* into 1,000 real U.S. appellate-brief excerpts, plus 300 naturally occurring content misrepresentations. In total there are 1,300 excerpts, 4,499 citations and 1,107 hallucinated citations. The five classes are non-existent citation, case-name mismatch, incorrect pincite, verbatim misquote and content misrepresentation. The highest-recall agentic checker (GPT-5) reached 84.4% recall at F1 55.0%, which implies ≈40.8% precision, and needed 15.3 steps per excerpt. The highest-precision agent reached 76.1%. Incorrect pincites were hardest (52.8% recall), and misquotes easiest (95.2%). *Information access* was a binding constraint: 19.9% of retrieved opinions lacked usable text or pagination [P8-3].
- **Wrong pinpoint vs wrong case (Verma, 2026).** The paper starts from *Mata v. Avianca* (S.D.N.Y. 2023), where two attorneys were sanctioned for ChatGPT-fabricated citations [P8-9]. Such fabrications are mostly caught by database lookups. Fourteen model configurations caught 93–100% of wrong-case corruptions but only **37–61% of wrong-pinpoint corruptions on court opinions**, and 52–83% on briefs. When the models failed, they accepted the citation because the topic overlapped. GPT-5.4 at high reasoning effort still missed 40% of opinion pinpoint mismatches. Prompting the model to check support at the cited page raised recall but also false positives [P8-4]. **Implication:** our spine's paragraph anchors are the right unit, and verification must entail against *the cited anchor alone* (C3), never the whole judgment.
- **Legal warrant (Taranukhin & Shwartz, 2026, position paper).** Legal hallucination should be evaluated as a *failure of warrant*: the authority exists, applies to the jurisdiction, is current for the date, has the represented status, and supports the proposition. Warranted systems also narrow, ask, warn, correct false premises or abstain. Existence checks, generic attribution and sentence-citation alignment benchmarks miss warrant failures [P8-5]. Our `warrant{}` vector operationalises this.
- **Oracle coverage (Ovcharov, 2026; Ukrainian law, 100 queries × 4 commercial LLMs).** The same 400 LLM responses scored 0.791–0.855 citation grounding against a sparse citation-graph snapshot (4.7×10⁵ records) and 0.989–0.999 against a dense one (3.3×10⁸ records). Coverage, not the model, drove the "15–21% hallucinated" figure: all 54 citations flagged by the sparse oracle were real. No pair of systems was separable at 95% [P8-6]. **Implication:** status `UNVERIFIABLE`, a coverage metric on every report, and bootstrap CIs on every comparison.
- **Graph-constrained verification in India.** Falkor-IRAC accepts an answer only if a supporting path exists in an IRAC knowledge graph of SC/HC judgments. It uses a "Verifier Agent" and treats doctrinal conflicts as first-class outputs. Its evaluation is a proof of concept on 51 SC judgments, and it defers comparison with vector-RAG baselines [P8-65]. An Italian tax-court pipeline filters LLM-extracted references against citations detected in the judgment by a dedicated extractor [P8-66]. Both confirm the pattern "generate, then deterministically check against structured data". Neither reports lawyer-adjudicated error rates at scale.
- **Treatment classification remains error-prone.** On 239 expert-annotated citations, the best high-level treatment accuracy was 79.1% and the best fine-grained accuracy 67.7%. The authors propose an *Average Severity Error* that weights misclassifications by harm [P8-63]. We use severity-weighted metrics for P3 (§9).

### 3.3 Faithfulness and grounding checkers
- **NLI/alignment checkers.** AlignScore trains a unified alignment function across many data sources [P8-13]. MiniCheck trains small checkers on synthetic, structured errors. It reports GPT-4-level grounding accuracy at ≈400× lower cost and introduced the LLM-AggreFact benchmark [P8-12]. The LLM-AggreFact leaderboard (11 datasets, balanced accuracy) lists Bespoke-MiniCheck-7B at 77.4%, Claude-3.5 Sonnet 77.2%, Granite Guardian 3.3 (8B) 76.5%, FactCG-DeBERTa-L (0.4B) 75.6% and MiniCheck-Flan-T5-L (0.8B) 75.0% [P8-14]. **So sub-1B checkers are within ≈2 points of frontier LLMs on generic grounding.** They are not validated on Indian legal text.
- **Decompose-then-verify.** FActScore scores the share of atomic facts supported by a knowledge source [P8-15]. The results depend on the decomposition method [P8-16], can be inflated with trivial sub-claims [P8-17], and wrongly assume every claim is verifiable [P8-18]. LeMAJ decomposes legal answers into "Legal Data Points". It reports better agreement with lawyers and improved inter-annotator agreement [P8-38]. **Implication:** P6 emits typed claims (so we avoid decomposing free text in the hot path). P8 decomposes only *within* a claim, with a gold-evaluated decomposer.
- **RAG evaluation frameworks.** RAGAS offers reference-free metrics (faithfulness, context relevance) [P8-19]. ARES fine-tunes lightweight judges and uses **prediction-powered inference (PPI)** with a few hundred human labels to produce valid CIs [P8-20][P8-41]. ALCE evaluates citation quality (recall and precision of citations) [P8-21]. RAGTruth provides ≈18,000 responses annotated at word level for RAG hallucinations [P8-22]. None of them models authority, time or jurisdiction.
- **Uncertainty from sampling.** Semantic entropy clusters sampled answers by meaning [P8-25]. It was published in *Nature* in 2024 [P8-23]. It costs 5–10× the compute, which motivated single-pass *semantic entropy probes* [P8-24]. Useful for free-form opinions. Less relevant where claims are closed-world and anchor-bound.

### 3.4 Calibration and conformal guarantees
- Modern neural nets are miscalibrated, and temperature/isotonic post-hoc calibration plus ECE measurement are standard [P8-34]. Larger LMs are reasonably calibrated on well-formatted multiple-choice questions [P8-33]. That setting does not describe open legal claims.
- **Conformal factuality.** Filter or back off claims using a threshold calibrated on held-out data, which gives a high-probability correctness guarantee [P8-26]. Conditional conformal methods address the fact that validity varies by topic, and they preserve more true claims [P8-27]. For multi-step reasoning, *coherent* factuality requires that each step be judged in the context of its premises [P8-30]. Conformal linguistic calibration unifies abstention and hedging [P8-31].
- **Caveats (2025–2026).** In RAG settings, conformal filtering gives *vacuous* output at high factuality levels, and its guarantee **is not robust to distribution shift or distractors**. Lightweight entailment verifiers matched or beat LLM confidence scorers at >100× fewer FLOPs [P8-28]. Standard conformal prediction under-covers under domain shift, and reweighting calibration samples helps [P8-29]. **Implication:** stratified calibration, calibration data drawn from production-like traffic, informativeness tracked alongside error, and recalibration on every model change (§5.6).

### 3.5 Evaluating with LLM judges and humans
- LLM judges reach >80% agreement with humans on general chat, but show position, verbosity and self-enhancement biases [P8-35]. They recognise and favour their own generations [P8-36]. EvalGen shows that evaluation criteria drift as graders see outputs, so judges must be validated against human grades [P8-37].
- **Legal-specific evidence.** On a Polish public-procurement qualifying exam, LLM-as-judge verdicts "often diverged" from the official committee [P8-40]. GreekBarBench meta-evaluated judges against experts and found that **simple span-based rubrics improve alignment** [P8-39]. LeMAJ's data-point method improved agreement [P8-38].
- **Statistics.** Treat eval items as samples from a super-population. Report CIs. Use *paired* differences and clustered standard errors. Plan sample sizes [P8-42]. PPI combines many model-judged items with few human-labelled ones for valid, tighter intervals [P8-41].
- **Agreement.** Krippendorff's α ≥ 0.800 is the conventional bar for relying on data, and 0.667–0.800 supports only tentative conclusions. Higher is expected when errors are costly [P8-43].

### 3.6 Communicating uncertainty to users
- In a preregistered study (N=404), first-person uncertainty phrases ("I'm not sure, but…") reduced over-reliance and improved accuracy. Impersonal phrasing had weaker effects [P8-44].
- Uncertainty *granularity* matters (N=192). Token-level uncertainty *increased* agreement with the AI. Relation-level uncertainty (on individual reasoning steps) *reduced* users' own external verification and steered them toward relying on the AI's cues [P8-45]. **Implication:** do not decorate text with fine-grained scores. Show claim-level ordinal bands whose meaning is an audited error rate, and keep click-to-source one tap away (§5.7).

### 3.7 Benchmarks relevant to Indian legal AI
| Benchmark | What it measures | Use in P8 |
|---|---|---|
| **IL-TUR** (ACL 2024) | 8 Indian tasks: L-NER, rhetorical roles, CJPE, BAIL (Hindi), statute identification, prior-case retrieval, summarisation, legal MT (9 languages). Public leaderboard. GPT models underperformed task-specific SOTA on every task except GPT-4 on legal MT (MILPaC) [P8-46] | Comparability smoke tests for P1 (RR, NER), P2/P5 (PCR, LSI), MT. Not a release gate |
| SemEval-2023 LegalEval | RR labelling, legal NER, judgment prediction (Indian) [P8-56] | P1 RR/NER sanity |
| ILDC / PredEx / NyayaAnumana | Judgment prediction (+explanation). 35k SC cases [P8-51]; 15k+ expert annotations [P8-52]; 702,945 cases across courts [P8-53] | **Not used as a product metric** (no outcome prediction, P6 §5.9). Used only to probe long-document comprehension |
| AILQA (2026) | Indian legal QA with RAG, expert ratings and AIBE questions [P8-55] | Public-question smoke set; its rating protocol informs G-QA |
| BHRAM-IL (2025) | Hallucination recognition in Hindi, Gujarati, Marathi, Odia and English, 36,047 questions; **general-domain, not legal** [P8-59] | Indic hallucination sanity for the judge models only (no legal signal) |
| IndicXNLI | NLI in 11 Indic languages, machine-translated from XNLI [P8-60] | Multilingual checker sanity (not legal) |
| LegalBench | 162 tasks, six reasoning types, lawyer-built, U.S.-centric [P8-47] | Model-tier qualification, rule-application subset |
| LegalBench-RAG | Precise snippet retrieval [P8-48] | Harness-compatible retrieval format |
| LexGLUE, CaseHOLD | EU/US legal NLU; holding identification [P8-49][P8-50] | Historical baselines only |
| LEXam | 340 exams, 7,537 questions, long-form reasoning with guidance [P8-54] | Reasoning-tier qualification |
| COLIEE (2025–2026) | Case retrieval, **statute entailment**, legal QA (5 tasks in 2026) [P8-57] | Entailment-checker comparability |
| CLERC | Case retrieval + retrieval-augmented analysis generation with citations [P8-58] | Citation-generation eval design reference |
| MILPaC | Translation of legal text into Indian languages [P8-61] | Legal-MT sanity for the cross-lingual path (§5.5) |
| LePhantomCite | Citation hallucination detection, 5-class taxonomy [P8-3] | Checker comparability (U.S.) |
| ContractNLI | Document-level legal NLI [P8-62] | Additional NLI training/eval data |
| LeKUBE, LexKairos | Legal knowledge updates; legal temporal reasoning (Chinese law) [P8-64] | Design pattern for our temporal-trap suite |

**Gap.** No public Indian benchmark tests the things the product promises: paragraph-level support, adverse-authority recall, good-law-as-of-date, binding-on-forum, IPC↔BNS crosswalk, or deadline correctness. We therefore **build the gold ourselves** (§5.10) and treat public benchmarks as smoke tests and contamination-prone comparability checks.

### 3.8 India: why verification is now a litigation issue
Damien Charlotin's database lists 16 Indian decisions involving AI-hallucinated material (as of 30 Sep 2026) [P8-8]. Most involve **judicial or quasi-judicial orders**:
- *Buckeye Trust v. PCIT*, ITAT Bengaluru, 30 Dec 2024. Misrepresented case law and outdated/repealed norms; the order was retracted and the matter re-heard.
- Supreme Court orders in *Pooja Ramesh Singh v. J&K Bank* (2 Jul 2026, NCLT/NCLAT judgments set aside) and *Vijay Ghanshyam Gadiya v. Union of India* (2 Sep 2026, order set aside and remanded).
- Delhi HC W.P.(C) 6049/2026 (17 Jul 2026; six fabricated authorities; order set aside).
- Tax administration: *KMG Wires Pvt. Ltd. v. National Faceless Assessment Centre*, Bombay HC, 6 Oct 2025 (assessment quashed and set aside). Trial courts: a Bengaluru civil-court judgment later revoked (21 Jan 2026), and a Saket commercial-court judgment stayed (30 Apr 2026).
- Lawyer filings: *Greenopolis Welfare Assn. v. Narender Singh*, Delhi HC, 25 Sep 2025 (petition withdrawn); *Omkara Assets Reconstruction v. Gstaad Hotels*, SC, 8 Dec 2025 (warning).
- Pro se litigants: Bombay HC, 7 Jan 2026 (costs).

All details are as recorded in the database [P8-8]. We have not read the underlying orders ourselves, so the characterisations are *secondary*. **Implication:** verification is needed not only for our own outputs but also for **incoming documents** (opponent filings, lower-court and tribunal orders). A fabricated or misrepresented authority in an impugned order is itself a potential ground of challenge (§5.8).

---

## 4. Mistakes others made and how we avoid them

| System/paper | What went wrong | Evidence | How we avoid it |
|---|---|---|---|
| Lexis+ AI, Westlaw AI-AR, Ask Practical Law AI | 17–33% hallucination; misgrounded citations; "hallucination-free" marketing | [P8-1] | Anchor-level entailment gate (C3) blocks misgrounding. Displayed bands are tied to *audited* error rates (trust ledger, §5.7). No "hallucination-free" claim is ever made |
| General LLMs | 58–88% legal hallucination; accept false premises; poor self-knowledge | [P8-2][P8-32] | LLM self-confidence is a feature only. Premise contradictions are caught by C6/C9 against P3 (e.g. a claim that "X was overruled" when P3 says GOOD → CONTRADICTED) |
| Citation checkers (research + agents) | Catch fake cases, miss **wrong pinpoints** (37–61%; pincite recall 52.8%); accept on topical overlap | [P8-3][P8-4] | Entailment against the *cited anchor text only* (±1 neighbour for coreference). If that fails, **pinpoint re-anchoring search** within the same work (C3b) → PARTIAL with a suggestion, never PASS |
| Agentic verification | 15.3 steps/excerpt; costly; limited by database access | [P8-3] | We own the corpus and anchors, so verification is a lookup plus a small model, not web browsing. Agentic search only in Citation Audit fallback for unresolved citations |
| Citation-graph hallucination metrics | Measure oracle coverage; systems not separable | [P8-6] | `UNVERIFIABLE` status with reason. `coverage.verifiable_share` on every report. Bootstrap CIs on all comparisons |
| RAG eval frameworks (reference-free LLM metrics) | No notion of authority, time or jurisdiction; judge biases | [P8-19][P8-35][P8-36] | Warrant checks are deterministic against P3. LLM judges only for entailment and role subtleties, from a different family than the generator, position-swapped, validated on lawyer labels |
| FActScore-style decomposition | Scores depend on decomposer; inflatable; assume verifiability | [P8-16][P8-17][P8-18] | Claims are typed at generation (P6). Intra-claim decomposition is a gated model task with its own gold. Sub-claims are de-duplicated and weighted by informativeness |
| Conformal filtering in RAG | Vacuous at high factuality; breaks under shift | [P8-28][P8-29] | Stratified (Mondrian-style) thresholds. Informativeness/withheld-rate tracked with the error rate. Recalibration on any model or corpus shift, and monthly audit-driven checks |
| LLM-as-judge in legal exams | Diverges from official examiners | [P8-40] | Judges never the sole gate for tier-1 or memo quality. Lawyer panels calibrate judges. PPI corrects judge bias in estimates |
| Legal "accuracy" leaderboards | Legal AI ≈ ChatGPT on accuracy; the differences are in authority | [P8-10] | Separate *answer* and *source/warrant* scores [P8-11]; binding/adverse recall; bad-law leakage |
| Public Indian benchmarks | Tasks (judgment prediction, summarisation) don't test paragraph support, adverse authority or temporal validity; LLMs trail SOTA | [P8-46][P8-51] | Proprietary gold with adverse sets, temporal traps and crosswalk items. Public benchmarks are smoke tests only |
| Indian orders with fabricated/misrepresented citations (incl. ITAT *Buckeye Trust*, SC 2026 set-asides) | Unchecked AI output entered judicial orders; repealed norms cited | [P8-8] | C8 temporal/provision checks. Citation Audit of incoming orders and filings. Export-time re-verification and signed verification appendix |
| Treatment classifiers | 67.7–79.1% accuracy on treatment; flat accuracy hides severity | [P8-63] | Severity-weighted metrics. Definitive negative status needs HITL (P3). P8 distinguishes `definitive` vs machine signal |
| Graph-only verification (IRAC path oracle) | Paths prove *linkage*, not that the cited paragraph says the claim | [P8-65] | Path/status checks (C6/C7) are combined with text entailment (C3) and role checks (C4) |

---
## 5. Recommended design, in detail

### 5.1 Components
| Component | Responsibility | Tech |
|---|---|---|
| **Verify API** | `/verify`, `/revalidate`, `/audit`; idempotent on `request_id`; streams per-claim results | Stateless service (Go/Python), horizontally scaled; runs **inside the tenant trust boundary** when private anchors are involved (spine §A) |
| **Deterministic checker** | C0–C2, C5–C10 (existence, quote, metadata, status, binding, temporal, numeric, attribution, dependencies) | Library shared with P6's pre-check (same code, same version) |
| **Entailment engine** | C3 support, C4 role (model-assisted), intra-claim decomposition | Small checker on GPU (Triton/vLLM); LLM judge via Model Gateway tasks |
| **Calibrator** | Features → `calibrated_confidence`; conformal band thresholds per stratum | Versioned model artefact; nightly refit job; stored in model registry |
| **Verification cache** | `(claim_hash, anchor text_hashes, as_of, forum) → entailment results`; status checks keyed additionally by `graph_watermark` | Redis + Postgres; entailment results reusable across tenants **only for public anchors with no private text in the claim** |
| **Citation Auditor** | Parses any ParsedDocument's citations and runs a subset of the ladder | Uses P1 citation parser + ladder |
| **Gold Store** | `EvalCase`, gold-set manifests, splits, signatures, staleness | Postgres + object store; signed manifests; 2-reviewer change control (XC threat model) |
| **Eval Runner** | Executes suites against candidates; records `EvalRun`; computes CIs | Batch workers; deterministic replay; OSS eval harnesses may be used as runners *(feature fit unverified)* |
| **Gatekeeper** | Applies the gate rules (§5.11); emits `eval.run.completed.v1`; manages waivers | CI integration; Model Gateway integration |
| **Annotation Studio** | Gold-room authoring, adjudication, IAA, perturbation review | Web app. **Tenant-plane deployment** for private data (D2/D3, §5.13) |
| **Audit Sampler + Trust Ledger** | Stratified sampling of displayed claims for lawyer audit; PPI estimates; published error rates | Batch + P10 widget |

```mermaid
flowchart LR
  P6[P6 workflow] -->|VerifyRequest| API[Verify API]
  P10u[P10 upload / draft] -->|AuditRequest| API
  API --> D0[C0 schema & typing]
  D0 --> D1[C1 existence/alias/PIT]
  D1 --> D2[C2 quote fidelity + OCR trust]
  D2 --> MD[C5 metadata consistency]
  MD --> ST[C6 status as-of ⟵ P3 AuthorityView]
  ST --> BI[C7 binding on forum]
  BI --> TE[C8 temporal/crosswalk]
  TE --> NU[C9 numeric/deadline ⟵ P6 rules]
  NU --> EN{C3 entailment on cited anchor}
  EN -->|p≥0.90 & not tier-1| RO[C4 role/attribution]
  EN -->|uncertain or tier-1| J[LLM judge: other family, span rubric]
  J --> RO
  EN -->|fail| RA[C3b pinpoint re-anchoring in same work]
  RA --> RO
  RO --> AT[C10 attribution / C11 dependencies / C12 overclaim]
  AT --> CAL[Calibrator + conformal band]
  CAL --> G[Status, band, gate]
  G -->|VerificationReport| P6
  G -->|verification.completed.v1| P9[P9 tenant plane]
  G --> P10[P10 render / export appendix]
  P3[(P3 graph)] -. graph.delta.v1 .-> INV[cache invalidation + gold staleness + sentinel generation]
```

### 5.2 Verification tiers
Every claim gets a **verification tier** (VT). The tier sets which checks are mandatory and how failures gate.

| VT | Claims | Mandatory | Failure consequence |
|---|---|---|---|
| **VT1** | PROCEDURAL (deadlines, limitation, maintainability); claims that an authority is binding, overruled or good law; crosswalk claims (IPC↔BNS etc.); any claim in `favourable_authorities` whose anchor is SC or a Constitution provision | All deterministic checks. **Two independent entailment verdicts** (small checker + judge) must agree. Status must be `definitive` or disclosed | Section **BLOCK** (P6 §5.7). UNKNOWN verdicts go to the human queue `TIER1_CLAIM` |
| **VT2** | Other LEGAL_PROPOSITION; RECORD_FACT | Deterministic checks + small checker; judge on uncertainty | Claim withheld / narrowed; section PARTIAL |
| **VT3** | STRATEGIC_OPINION | Dependency closure (C11) + "no new legal proposition" check | Opinion withheld if any dependency fails |

### 5.3 The check ladder (algorithms and initial thresholds)
Thresholds are *initial values*. The Calibrator re-fits them on adjudicated data (§5.6), and each change is versioned in `verifier_version`.

**C0 — Schema and type rules.** Enforces spine §H ("all other types need ≥1 anchor"): LEGAL_PROPOSITION ≥1 DIRECT support from a PLC anchor (an R-handle alone is *not* sufficient); RECORD_FACT ≥1 private anchor; PROCEDURAL ≥1 R-handle **and** ≥1 statutory/rule anchor that the R-handle's `RuleSpec` cites (spine: deadlines "with statutory anchor"), so every PROCEDURAL claim is still anchor-traceable; STRATEGIC_OPINION non-empty `depends_on_claim_ids`, acyclic. Every `support.anchor_id` must be in the P6 ledger, which enforces the closed world. Failure → UNSUPPORTED (`SCHEMA`/`OUT_OF_LEDGER`). Cost ≈0.

**C1 — Existence, alias and point-in-time.** Resolve each `anchor_id` through the anchor store. Follow `anchor_alias` records and tombstone forward pointers. For statute anchors, resolve `@as_of_legal_date` to the valid expression. Outcomes: `PASS`; `WARN` (resolved via alias, confidence <0.95); `FAIL` (no such anchor → `FABRICATED_ANCHOR`, which should be impossible and is logged as a P6 defect); `UNKNOWN` (anchor store unavailable → the claim becomes UNVERIFIABLE and is never PASSed).

**C2 — Quote fidelity with OCR trust.**
```
q  = normalize(claim.support.quote)          # NFC, collapse whitespace, unify quotes/dashes, strip ellipsis markers,
                                             # strip zero-width/bidi controls (U+200B–U+200F, U+202A–U+202E, U+2066–U+2069),
                                             # map Indic digits (Devanagari ०–९, Bengali, Gujarati, Tamil …) → ASCII,
                                             # NFKC-fold confusable Latin/Cyrillic homoglyphs; log if any fold was needed
a  = normalize(anchor.text[span])
if q == a                         → PASS  (P6 quote-by-reference normally guarantees this)
elif lawyer-edited draft:
     r = token_levenshtein_ratio(q, a)
     if r ≥ 0.97 and digits(q)==digits(a) and negations(q, lang)==negations(a, lang) → WARN(MINOR_QUOTE_VARIANCE)
     # negations() is language-aware: en {not, no, never, nor, neither, cannot, un-/in-/non- prefixed legal terms list},
     # hi {नहीं, न, ना, मत, बिना, अ-/अन- prefixed list}; lists are versioned config owned by P8, tested on G-Claim hi slice
     else FAIL(MISQUOTE)
else FAIL(MISQUOTE)
# OCR trust: a correct hash match against *wrong OCR text* is still wrong for the lawyer
if anchor.ocr_conf < 0.90 or anchor has critical-token flags (P1):
     if another manifestation of the same expression agrees on the span (P1 cross-manifestation) → PASS
     else WARN(QUOTE_FROM_LOW_OCR) → band ≤ VERIFIED_WITH_CAVEAT; exports require a page-image check (P10 shows the image crop)
```

**C3 — Pinpoint entailment (the core check).** Premise = the *cited anchor's text*, plus at most the previous and next paragraph, flagged as context-only (for pronouns and "the aforesaid"). **Never the whole judgment.** Hypothesis = the claim text, or each sub-claim if the claim is decomposed.
```
subclaims = decompose(claim) if len(claim.text) > 240 chars or has conjunctions/lists else [claim.text]   # p8.decompose, gated task
for s in subclaims:
   p = small_checker(premise, s)                      # calibrated P(entailed)
   if VT1 or has_number_or_date(s) or cross_lingual(premise, s) or 0.10 < p < 0.90:
        j = judge(premise, s, rubric=SPAN_RUBRIC)      # other model family; must quote the supporting span
        verify j.span ⊂ premise (exact substring), else discard j (judge hallucinated support)
        label = combine(p, j)                          # agreement → label; disagreement → NEUTRAL + escalate (VT1 → human)
   else label = ENTAILED if p ≥ 0.90 else NOT_ENTAILED
   if label == NOT_ENTAILED: c = contradiction_prob(premise, s)   # same model heads
        label = CONTRADICTED if c ≥ 0.80 else NEUTRAL
```
Claim-level result: all sub-claims ENTAILED → PASS. Some ENTAILED → PARTIAL, with `narrowed_text` built only from the entailed sub-claims (P6 accepts or rewrites it). None → go to **C3b**.

**C3b — Pinpoint re-anchoring.** Addresses the wrong-pinpoint failure [P8-4]. Search the *same work* (and the same expression) for paragraphs that entail the claim. Retrieval is BM25 + dense within the work; the top 5 go to the small checker. If a paragraph passes, return `suggested_anchor_ids`, set reason `WRONG_PINPOINT` and status PARTIAL. P6 repair can re-point. **The original pinpoint is never silently accepted.** If nothing passes → UNSUPPORTED (`MISREPRESENTS_SOURCE`). If the cited anchor is NEUTRAL and another paragraph of the same work *contradicts* the claim → CONTRADICTED.

**C4 — Rhetorical role and speaker.** Uses P1 anchor labels (S8-2).
| Claim asserts | Anchor role / speaker | Verdict |
|---|---|---|
| "the Court held / laid down / ratio" | RATIO / court's analysis, majority | PASS |
| same | OBITER | WARN (`OBITER_AS_HOLDING`) → narrowed "observed" wording |
| same | ARGUMENT (counsel's submission), FACTS, recital of the impugned order | FAIL (`ROLE_ARGUMENT_AS_HOLDING`) |
| same | DISSENT / separate minority opinion | FAIL (`DISSENT_AS_HOLDING`) unless the claim says dissent |
| same | a paragraph *quoting* an earlier judgment | WARN (`QUOTED_AUTHORITY`): the claim should cite the original as well; P3 resolves the quoted source |
| any | role confidence < 0.7 | `p8.role_judge` (LLM) decides; disagreement → UNKNOWN → band CHECK |

Most tools do not check this, but it is a characteristic Indian-judgment trap. Long judgments recite submissions at length before the analysis, so a "supporting" paragraph is often counsel's argument.

**C5 — Metadata consistency.** Parse every citation string, case name, court, year, bench size ("Constitution Bench", "three-Judge Bench") and judge name mentioned in the claim text with the P1 parser. Compare each against the cited work's metadata and aliases. Mismatches → FAIL (`NAME_MISMATCH`, `CITATION_STRING_MISMATCH`, `BENCH_MISMATCH`). This covers the "case name mismatch" class [P8-3] and wrong SCC/AIR/neutral strings. Case-name comparison uses P1's party-name normaliser (strip "& Ors.", "and another", "M/s", "Shri/Smt."; expand "UoI"/"Union of India", "State of U.P."/"State of Uttar Pradesh"; transliteration-insensitive match for Devanagari cause titles) and passes at token-set Jaccard ≥ 0.6 on the *first-named* party on each side; a lower score is `NAME_MISMATCH` only if the citation string resolves to a different work, otherwise WARN.

**C6 — Authority status as of the relevant date.** Batch-fetch `AuthorityView` for every cited work and proposition, in P3's `status_mode` (CURRENT by default; HISTORICAL when the claim is explicitly historical; P3 §2.3). Record `graph_watermark`.
| AuthorityView | Claim uses authority as support | Claim is about negative treatment |
|---|---|---|
| GOOD | PASS | CONTRADICTED if the claim says overruled/doubted |
| CAUTION or NEGATIVE_SIGNAL_UNDER_REVIEW (`definitive=false`) | WARN → band ≤ VERIFIED_WITH_CAVEAT, reason chip "under review" | PASS only if phrased as "doubted/under review" |
| NEGATIVE, `definitive=true` | **BAD_LAW** | PASS |
| NEGATIVE, `definitive=false` | WARN, VT1 → human queue | WARN |
| PARTIAL_NEGATIVE | proposition match: if the claim's proposition (NLI vs `prp_…` text, p≥0.8) is the negated one → BAD_LAW, else WARN | as above |
| UNKNOWN / COVERAGE_GAP | UNKNOWN → UNVERIFIABLE for VT1; WARN for VT2 | UNVERIFIABLE |
| GOOD, but direct-history caution: a `STAYS` assertion, a pending appeal/SLP recorded on the case lineage, or `REFERS_TO_LARGER_BENCH` on the relied-on proposition | WARN (`UNDER_APPEAL_OR_STAYED` / `REFERRED_TO_LARGER_BENCH`) → band ≤ VERIFIED_WITH_CAVEAT; VT1 → chip mandatory in exports. Never BAD_LAW | PASS if the claim states the pendency |

`NEGATIVE_SIGNAL_UNDER_REVIEW` and `COVERAGE_GAP` are P3's proposed extensions of spine `AuthorityStatus`; if they are not adopted, the fallback mapping in S8-8 applies. The direct-history caution row matters in Indian practice. HC judgments are routinely stayed or kept under challenge in SLPs, and a reference to a larger bench unsettles a proposition without overruling it. None of these is "negative treatment", but a lawyer must be told.

**C7 — Binding on the forum.** If the claim text asserts bindingness ("binding on this Court", "the High Court is bound"), or the claim sits in `favourable_authorities` with a binding label, then `AuthorityView.binding_on_forum` for `forum` must equal BINDING. PERSUASIVE → FAIL (`NOT_BINDING_ON_FORUM`). UNDETERMINED → WARN. Bench-strength language is checked against `bench_strength` (C5). **Context sanity:** if `VerifyRequest.forum` or `as_of_legal_date` differs from the `MatterContext` forum or `key_dates.cause_of_action` (when a matter is attached), the report adds `context_warnings[]` (`FORUM_MISMATCH_WITH_MATTER`, `AS_OF_DATE_MISMATCH_WITH_MATTER`) and every C7/C8 verdict carries reason `CONTEXT_MISMATCH` until a user confirms. A wrong forum silently flips binding verdicts, so this is not left to the user to notice.

**C8 — Temporal and crosswalk.** For each statute anchor, the expression must be valid on `as_of_legal_date` (P3 provision-at-date). If a claim cites a provision not in force on that date → FAIL (`SUPERSEDED_PROVISION`), with the `CORRESPONDS_TO` counterpart as a suggestion. Crosswalk claims ("s.X IPC corresponds to s.Y BNS") must match a P3 `CORRESPONDS_TO` assertion, including `change_type`. The legal rule on *which* code applies to a given offence date or pending proceeding is P3/P6 doctrine. P8 only checks consistency with it.

**C9 — Numeric, date and deadline.** Extract numbers, dates, amounts, periods and section numbers from the claim. Each must appear in the supporting anchor or be produced by the cited R-handle's computation. For PROCEDURAL claims, **recompute** via the P6 rule engine using the same inputs and require exact equality. Mismatch → FAIL (`NUMERIC_MISMATCH` / `DEADLINE_MISMATCH`, VT1). NLI checkers are unreliable on numbers, so numbers are never left to the model.
Indian normalisation, applied to claim and anchor before comparison:
- Indic digits → ASCII.
- Lakh/crore grouping ("1,00,000" = 100000) and words ("₹5 lakh", "2.5 crore", "पाँच लाख") → integer paise.
- Dates are parsed **day-first** (DD.MM.YYYY, DD/MM/YYYY, "30th September, 2026", Hindi month names). An ambiguous all-numeric date whose day ≤ 12 is compared both ways and passes only if it matches under day-first.
- Periods ("ninety days", "3 months", "one year") → (count, unit). "Months" and "days" are never converted into each other, because limitation law distinguishes them.
- Section numbers keep letter suffixes and dots ("302", "34A", "498-A" → `498A`, "138" ≠ "13.8").
A number from a low-`ocr_conf` anchor is WARN, never PASS on its own.

**C10 — Attribution (record facts).** A RECORD_FACT whose only support comes from a document with trust label `TENANT_OPPOSING_DOC` (or a fact with `asserted_by = OPPONENT`) must be phrased attributively ("the notice alleges…"). A small classifier plus patterns checks this. Otherwise → FAIL (`ATTRIBUTION`). This stops an opponent's allegation from becoming "fact", and it also contains injected assertions (XC §5).

**C11 — Dependency closure (VT3).** An opinion's status is the worst status among its dependencies (VERIFIED > PARTIAL > others). In addition, `p8.decompose` extracts legal-proposition-like sub-claims *from the opinion text*, and each must be entailed by the union of its dependencies' texts. This is coherent factuality [P8-30]. Otherwise → FAIL (`UNGROUNDED_PROPOSITION_IN_OPINION`).

**C12 — Overclaim and adverse acknowledgement.** Intensifiers need evidence:
- "settled law", "consistently held", "no authority to the contrary" require ≥1 BINDING + GOOD supporting authority *and* no undisposed BINDING ADVERSE item on the same issue in the EvidenceBundle.
- "no contrary authority" additionally requires P5 `coverage.per_issue.adverse_found = 0` with coverage attested.

Otherwise → WARN (`OVERCLAIM`), with `narrowed_text` that drops the intensifier. It also cross-checks P6's adverse accountability. A claim whose `contrary[]` or bundle ADVERSE items contradict it without acknowledgement → WARN (`ADVERSE_UNACKNOWLEDGED`).

**Injection handling inside the ladder.** Anchor texts are *data*. The small checker is not instruction-following. The judge receives premise and hypothesis in delimited, typed JSON fields, and its output schema is constrained, including an exact-substring `span` check. If an anchor's text matches the XC/P7 injection classifier, the judge is skipped for that anchor, the verdict comes from the small checker alone, and the band is capped at VERIFIED_WITH_CAVEAT. Uploaded documents (Citation Audit, private anchors) get two extra checks, both flagged `HIDDEN_TEXT_SUSPECT`:
- **Text-layer vs render mismatch.** P1 flags spans whose PDF text layer is invisible (white-on-white, zero-size font, off-page, or covered by an image). These spans are excluded from premises.
- **Normalisation-changed text.** Zero-width, bidi or homoglyph folding altered the text.
Neither kind of span can support a claim without a page-image check.

### 5.4 Status assignment, reason taxonomy and gates
```
status(claim) =
  BAD_LAW       if any support anchor's authority fails C6 with BAD_LAW
  CONTRADICTED  if C3/C3b yields CONTRADICTED (p_c ≥ 0.80), or C6 contradicts a treatment claim
  UNVERIFIABLE  if a mandatory check is UNKNOWN (store down, coverage gap, unsupported language pair for VT1, OCR unusable,
                or budget exhausted before a mandatory model check ran → BUDGET_EXHAUSTED)
  UNSUPPORTED   if C0/C1/C2/C5/C7/C8/C9/C10 FAIL, or C3 finds no entailed sub-claim and C3b finds nothing
  PARTIAL       if some sub-claims entailed, or C3b re-anchored, or C4/C12 WARN requiring narrowed wording
  VERIFIED      otherwise
```
**Reason codes** (stable enum, used by P6 repair, P9 analytics and eval attribution). `SCHEMA`, `OUT_OF_LEDGER`, `FABRICATED_ANCHOR`, `MISQUOTE`, `MINOR_QUOTE_VARIANCE`, `QUOTE_FROM_LOW_OCR`, `WRONG_PINPOINT`, `MISREPRESENTS_SOURCE`, `PARTIAL_SUPPORT`, `ROLE_ARGUMENT_AS_HOLDING`, `OBITER_AS_HOLDING`, `DISSENT_AS_HOLDING`, `QUOTED_AUTHORITY`, `NAME_MISMATCH`, `CITATION_STRING_MISMATCH`, `BENCH_MISMATCH`, `NEGATIVE_STATUS_DEFINITIVE`, `STATUS_UNDER_REVIEW`, `NOT_BINDING_ON_FORUM`, `BINDING_UNDETERMINED`, `SUPERSEDED_PROVISION`, `CROSSWALK_MISMATCH`, `NUMERIC_MISMATCH`, `DEADLINE_MISMATCH`, `ATTRIBUTION`, `UNGROUNDED_PROPOSITION_IN_OPINION`, `OVERCLAIM`, `ADVERSE_UNACKNOWLEDGED`, `COVERAGE_GAP`, `CROSS_LINGUAL_UNVERIFIED`, `CHECKER_DISAGREEMENT`, `INJECTION_SUSPECT`, `HIDDEN_TEXT_SUSPECT`, `UNDER_APPEAL_OR_STAYED`, `REFERRED_TO_LARGER_BENCH`, `CONTEXT_MISMATCH`, `BUDGET_EXHAUSTED`.

**Budget semantics.** `VerifyRequest.budget.max_llm_calls` and `latency_ms` are hard caps. The deterministic checks (C0–C2, C5–C10) always run, because they cost nothing. Judge calls are then allocated in priority order: VT1 first, then claims with 0.10 < p < 0.90, then cross-lingual claims. Any claim whose *mandatory* model check did not run becomes UNVERIFIABLE (`BUDGET_EXHAUSTED`), never PASS. A per-tenant daily judge-call quota (default 50× the tenant's seat count, set in XC) protects against runaway cost. When it is exhausted, the verifier degrades to *small checker only* and caps bands at VERIFIED_WITH_CAVEAT; it does not keep spending.

**Gate** (per section; P6 aggregates to memo level per P6 §5.7):
- **BLOCK** if any VT1 claim is not VERIFIED/PARTIAL-with-accepted-narrowing; or if >50% of the section's claims are withheld (a *vacuous* section is worse than an honest "needs review" [P8-28]); or if `strict_export` and any displayed claim is below band VERIFIED_WITH_CAVEAT.
- **PARTIAL** if any non-VT1 claims are withheld.
- **PASS** otherwise.

**Memo gate** (S8-6; computed by P8 when P6 sends the final `subject.kind="EXPORT"` call, or on demand):
- **BLOCK** if any section is BLOCK;
- **PARTIAL** if any section is PARTIAL;
- **PASS** otherwise.

A memo whose `deadlines` section is BLOCK can never be exported, even with a waiver.

### 5.5 Entailment engine
**Small checker (hot path).** MVP: an off-the-shelf grounding checker from the LLM-AggreFact top tier. Sub-1B models are within ≈2 balanced-accuracy points of frontier LLMs on generic grounding [P8-14], and MiniCheck-style training cuts cost ≈400× versus GPT-4-class checking [P8-12]. Candidates, all run through the P8 gate: a MiniCheck-class 0.4–0.8B model for speed and a 7–8B checker for quality. **Full version: `minicheck-in`**, fine-tuned on:
1. Adjudicated Indian claim–anchor pairs (G-Claim DEV split only).
2. The **Indian perturbation factory** (§5.10.4): wrong pinpoint with high lexical overlap, argument-vs-ratio swaps, dissent swaps, negation and number edits, bench and court swaps.
3. Synthetic hard negatives generated MiniCheck-style by a frontier model and filtered by lawyers on a sample.
4. ContractNLI and COLIEE statute-entailment data as auxiliary sources [P8-62][P8-57].

The model has three heads (entail / neutral / contradict). Promotion requires beating the incumbent on the G-Claim EXAM split in every slice (§5.11).

**Judge (escalation path).** Gateway task `p8.entail_judge@n`. Its output schema is `{label, span:{start,end}, rationale≤40 words}`, with span-based rubrics, which improve judge–expert alignment [P8-39]. Rules:
- The judge's model family must differ from the family of the P6 step that produced the claim. The Gateway enforces this through `origin_role` and the endpoint registry, because of self-preference bias [P8-36].
- For VT1, the judge runs twice with premise/hypothesis order variations (position-bias control [P8-35]) and must agree with itself and with the small checker.
- Temperature 0. Prompt hashes pinned.

**Cross-lingual and Hindi/regional anchors.** When premise and claim languages differ:
- (a) If P1 has an aligned sibling expression (e.g. an `en` translation of a `hi` judgment) with paragraph alignment confidence ≥0.9, verify against both. PASS requires the **authoritative** anchor to pass via the judge; the other version is a helper only. Which expression is authoritative is read from the anchor API's `authoritative` flag (S8-9), never assumed. A Hindi-original HC or district judgment is authoritative in `hi`. A regional-language version of an SC judgment is normally a translation of the English original *(general practice; unverified here, P1/21 to confirm per court)*. If the flag is missing, both versions must pass, or the claim gets `CROSS_LINGUAL_UNVERIFIED`.
- (b) Otherwise use a multilingual judge (qualified on the Hindi slice of G-Claim; BHRAM-IL and IndicXNLI, both general-domain, as sanity checks only [P8-59][P8-60]). The claim carries reason `CROSS_LINGUAL_UNVERIFIED` until the Hindi slice meets its gate.
- (c) VT1 cross-lingual claims without a qualified checker → human queue `CROSS_LINGUAL`.

The quote is always shown in the original language, with the translation beside it and flagged as machine translation.

**Decomposer.** Gateway task `p8.decompose@n`, a small LLM that splits compound claims into ≤5 sub-claims. It is gold-evaluated for *coverage* (no content lost) and *atomicity*, because decomposition choices change scores [P8-16]. Sub-claims that restate the premise or add nothing informative are dropped before scoring [P8-17].

---
### 5.6 Confidence model
**Target quantity.** `calibrated_confidence` = P(a senior lawyer, reading the cited anchor, would judge the claim *correct and adequately supported as worded*). Labels come from adjudicated G-Claim items plus production audit samples (§5.12).

**Features** (no single one is trusted):
- small-checker probabilities (min over sub-claims), judge label and span agreement;
- checker–judge agreement;
- C3b used (re-anchored);
- role label and its P1 confidence;
- `ocr_conf`, `structure_conf`;
- cross-lingual flag;
- `AuthorityView.status_confidence`, `definitive`, and binding determination (`binding_basis.contested`);
- claim type and VT; sub-claim count; presence of numbers;
- P5 retrieval signals for the anchor (fused rank);
- P6 raw confidence and, for opinions only, self-consistency agreement across n=3 samples.

LLM-verbalised confidence enters as a weak feature only, because it is overconfident [P8-32].

**Model.** Gradient-boosted trees with monotone constraints (e.g. confidence non-decreasing in checker probability and in `ocr_conf`), then **isotonic calibration per stratum** [P8-34]. The strata are `claim_type × court_tier × lang_group × ocr_ok`. Hierarchical back-off: a stratum with <300 labelled items borrows from its parent (e.g. `LEGAL_PROPOSITION × *`).

**Conformal band threshold.** For band VERIFIED we pick the lowest threshold τ_s such that the one-sided 95% Clopper–Pearson upper bound on the error rate among calibration items with score ≥ τ_s is ≤ α_s. This is split-conformal risk control in the spirit of [P8-26][P8-27].
- Targets: α = **0.5% for VT1**, **2% for VT2 LEGAL_PROPOSITION**, **3% for RECORD_FACT**. Planning values, to be confirmed with the partner.
- Worked example: with 1,000 calibration items above τ and 8 errors, the upper bound is ≈1.6%, which meets α=2%. Certifying 0.5% needs ≈1,000 items with ≤1 error. **Until a stratum has enough data it cannot display VERIFIED on its own evidence.** It inherits the pooled threshold and its chip says "calibrated on pooled data".
- **Shift controls.** Conformal guarantees break under distribution shift [P8-28][P8-29]. So: (i) calibration items are sampled from *production-like* traffic (shadow outputs adjudicated), not only gold-room questions; (ii) thresholds are refit on every change to the checker, judge, P1 role model or P3 status model; (iii) the weekly audit (§5.12) tests whether realised error in the VERIFIED band stays ≤ α_s. A breach → automatic tightening (τ_s raised to the next conformal step) plus an incident.
- **Informativeness.** Track the withheld rate and the share of sections that are PARTIAL or BLOCK next to the error rate, because tight thresholds can make output vacuous [P8-28].

### 5.7 What the lawyer sees (UI semantics owned by P8, rendered by P10)
| Band | Visual (P10) | Meaning, stated in the legend | Where allowed |
|---|---|---|---|
| **Verified** | solid badge | "Paragraph checked. Quote exact. Good law as of {date}. {Binding/Persuasive} for {forum}. In our last audit, about {k} in {n} Verified claims had a problem." | everywhere, exports |
| **Verified with caveat** | badge + mandatory chip | same, plus the specific caveat: "treatment under review", "obiter", "quote from low-quality scan: see image", "verified via translation", "wording narrowed" | everywhere; exports show the chip |
| **Check this** | outlined, amber | "We could not fully verify this (reason). Read the source before relying on it." | interactive research only. Excluded from exports unless a lawyer ticks "reviewed" (which becomes a P9 label) |
| **Withheld** | not shown in the memo | Diagnostic view lists withheld claims and reasons (useful for spotting what the other side might argue) | diagnostic only |

Rules:
1. **No raw percentages on claims.** Evidence: the wording of uncertainty changes reliance [P8-44], and fine-grained, step-level uncertainty cues can *reduce* users' own verification [P8-45]. The number lives in the legend as an audited error rate. This is honest calibration disclosure, and it is the anchor of the **trust ledger**.
2. **Reason chips always name the check**, e.g. "¶45 supports this", "Binding: 3-judge SC bench", "Good law as of 30-09-2026 (graph as of 11:40 today)". Every chip is click-to-source (anchor bbox highlight).
3. **Status freshness is visible.** Each status chip shows `graph_watermark` time. If the watermark is older than the P0/P4 freshness SLO for that court, the chip turns amber ("status may be stale").
4. **Adverse and bad-law items are never "withheld silently".** A BAD_LAW authority removed from support reappears in `adverse_authorities` (P6), with the treatment claim verified.
5. STRATEGIC_OPINION shows P6's ordinal strength with reasons (P6 §5.7). P8 shows only "grounded in N verified claims" plus dependency links.
6. **Verification ≠ advice.** The legend states that verification checks sources and status, not whether the strategy is wise.

**Trust ledger** [NOVEL — unvalidated as a product mechanism]. A monthly in-app page per tenant (and globally) showing, for each band × stratum, the audited error rate with a 95% CI (PPI estimate, §5.12), the audit sample size, the withheld rate, and the top reason codes. It turns calibration into a public commitment. Competitors report hallucination rates only when outsiders measure them [P8-1].

### 5.8 Citation Audit service and signed exports
**Citation Audit** (`/audit`). The input is any ParsedDocument: the firm's own draft, an opponent's filing, or a lower-court/tribunal order. For every `CitationMention` and `StatuteMention`:
1. Resolve via `identifier_alias`. Unresolvable → `NOT_FOUND` if the citation string is well-formed for a scheme we cover completely (e.g. the SC neutral citation `INSC` range we hold), else `UNVERIFIABLE`. Coverage-aware, as the oracle-coverage study requires [P8-6].
2. Case-name/citation consistency (C5).
3. If the document states a proposition or quote next to the citation (sentence window from P1), run C2, C3 and C3b against the cited pinpoint, or against the whole work if no pinpoint is given (weaker; flagged).
4. Status (C6) at the document's date *and* today. Binding (C7) for the document's forum. Provision-in-force (C8) at the document's date.

The output is a `CitationAuditReport`. For **incoming orders**, findings of `NOT_FOUND`/`MISREPRESENTS`/`SUPERSEDED_PROVISION` become a P6 input ("possible ground: impugned order relies on non-existent/misrepresented authority"), always framed as *to be confirmed by the lawyer*. Indian appellate courts have set aside orders on this basis (§3.8) [P8-8]. For the firm's own drafts, the audit is a pre-filing check.

**Signed verification appendix.** Every export (DOCX/PDF, P6 §5.8) embeds an appendix listing, for each cited authority: anchor, quote hash, status as of the export time and `graph_watermark`, binding verdict, `verifier_version` and report signature. Export always re-runs C6–C8 at graph head (`strict_export`). A later re-verification (living memo) can prove what was known when. This matches the spine's bitemporal audit goal (§E).

### 5.9 Re-verification, caching and idempotency
- **Cache keys.** Entailment: `(claim_hash, sorted anchor text_hashes, checker/judge versions)`. Status/binding/temporal: also `graph_watermark` and `(as_of_legal_date, forum)`. Entailment results never depend on graph state, so they survive status changes. Only C6–C8 are recomputed.
- **Invalidation.** On `graph.delta.v1`, cached status entries for affected `target_id`s are invalidated. P8 does *not* push alerts to matters. P4 → P7 → P6 `REVERIFY` owns that path (P6 §5.7). P8 answers `/revalidate` in ≤5 s p95 for ≤200 claims, because only C6–C8 run.
- **Delta storms.** A single Constitution Bench overruling, or a P3 backfill after an ontology change, can touch 10⁴–10⁶ cached status entries. Invalidation is O(affected keys) via a reverse index `target_id → cache keys` (Postgres table `vcache_dep(target_id, cache_key)`), so it is not a scan. Revalidation work is queued with priority:
  1. claims in open matters with an export pending or a hearing ≤7 days away (from `MatterContext.key_dates`);
  2. VT1 claims in open matters;
  3. everything else, lazily on next read.

  Priority 3 is never proactively recomputed, and a read after invalidation always recomputes C6–C8. The queue has a per-tenant concurrency cap, so one large tenant cannot starve others. If P3 marks a delta `bulk=true` (backfill, not new law), P8 invalidates but does not generate temporal-trap sentinels (§5.10.6).
- **Idempotency.** `request_id` gives the same report. A re-run with a changed watermark gives a new report that references the old one (`supersedes_report_id`).
- **Private data.** Reports containing private anchors are stored in the tenant plane (P7 storage). Only `verification.completed.v1` metadata (IDs, statuses, reason codes; no text) goes to P9's tenant-plane consumer.

---
### 5.10 Evaluation platform and gold sets

#### 5.10.1 Gold-set inventory (MVP at month 6 → Year 1)
| Gold set | Unit | MVP → Y1 size | Primary consumers | Key labels |
|---|---|---|---|---|
| **G-QA** research questions | question + `as_of_legal_date` + forum | 300 → 800 | P5, P6, end-to-end | must-include binding anchors; **must-include adverse**; must-not-include (bad law, superseded provisions); graded relevance |
| **G-Claim** claim–anchor pairs | claim + anchor(s) | 2,000 → 8,000 (≈60% natural system outputs, ≈40% perturbations, always reported separately) | P8 checker/calibrator, P6 | ENTAILED/PARTIAL/NOT/CONTRADICTED; role; correct-as-worded |
| **G-Temporal** traps | query/claim at a date | 150 → 500 | P3, P5, P8 C6/C8 | expected status/expression at date: overruled, prospectively overruled, reversed on appeal, struck down, amended/substituted, IPC/CrPC/IEA vs BNS/BNSS/BSA eras |
| **G-Crosswalk** | old↔new section pair | 200 → 500 | P3, P5 | `CORRESPONDS_TO` + `change_type` |
| **G-Deadline** (with P6) | rule × scenario | 300 → 800 | P6 rules, P8 C9 | exact date, anchor of the rule |
| **G-Memo** | trigger document (notice/petition/order) | 20 → 60 | P6, end-to-end | reference issue list, must-cite binding/adverse, deadlines, evidence checklist; lawyer pairwise preference |
| **G-Treat** (with P3) | citing ¶ → cited work/proposition | 1,000 → 3,000 | P3 | treatment predicate, proposition, severity |
| **G-Audit** | citation mention in a real Indian document | 300 → 1,000 | Citation Audit | 5 classes [P8-3] + Indian classes (role swap, superseded provision, not binding) |
| **G-Sec** | injected documents | 300 → 1,000 | P6/P7/P8 | expected: no instruction following, flagged, no exfiltration |
| **Sentinels** | zero-tolerance items | 200 → 400 | all gates | must never fail (e.g. a BAD_LAW authority shown as support; wrong deadline; fabricated anchor) |
| Phase-owned sets registered here | e.g. P1 IC-OCR-Bench (≈2,000 pages), 5,000 citation mentions, 300 gold judgments; P2 IN-Ret-* | per phase docs | P1, P2 | per phase docs |

**Strata** (every set is tagged; G-QA quotas shown).
- **Forum:** SC 30%; High Courts 40%, spread over ≥6 HCs incl. Delhi, Bombay, Madras, Calcutta, Allahabad, Karnataka; tribunals 20% (NCLT/NCLAT, ITAT, consumer commissions, CAT, NGT); district/other 10%.
- **Subject:** ≥10 practice areas, weighted to the partner's practice (criminal incl. BNS transition, civil procedure/limitation, commercial & arbitration, insolvency, direct/indirect tax, constitutional/service, consumer, property/tenancy, labour, family). No single area above 25%.
- **Language:** English 80%, Hindi 15%, other regional 5%. Oversampled relative to query traffic so slices can be measured.
- **OCR:** ≥15% of anchors from low-`ocr_conf` works.
- **Era:** pre-BNS / post-BNS / spanning (offence before, trial after 1 Jul 2024).
- **Task type:** existence/holding lookup, status, multi-issue research, statutory interpretation at date, procedure/limitation, crosswalk.
- **Perspective:** petitioner vs respondent phrasing of the same question, to test adverse surfacing symmetry.

**Why these sizes.** With n=800, a binary metric at p≈0.85 has SE≈1.3 points, and a paired comparison with 6% discordant items has SE_diff≈0.9 points. Both are adequate for a 1–2 point overall gate. A slice of 200 has SE≈2.5 points, so slices get the δ_s rule of §5.11 [P8-42]. G-Claim at 8,000 supports per-stratum calibration (§5.6) for the ~8 largest strata. Smaller strata back off.

#### 5.10.2 Construction protocol
1. **Guidelines v0 → v1.** A written label manual (support, role, status, binding, adverse relevance) with worked Indian examples. Pilot on 50 items. Compute Krippendorff's α per label family. Revise until **α ≥ 0.80** on support and status labels. Labels in 0.667–0.80 (e.g. graded relevance) are used only for "tentative" metrics [P8-43].
2. **Authoring (gold room).** Partner lawyers write *public-law* questions that mirror their practice. They contain no client facts. Each question records `as_of_legal_date`, forum, the lawyer's own research trail (sources they would cite, including adverse), and must-not-cite traps. Authors may use their usual subscriptions to *find* authorities. We store citations and our anchor IDs only, never reporter headnotes or editorial text (spine §D).
3. **Pooling.** Candidate authorities are pooled from ≥3 system configurations (our full stack, a lexical baseline, a dense-only baseline) plus the author's list. Annotators judge the pool **blind to source**. Unjudged items count as *unknown*, not irrelevant, in recall estimates *(standard IR pooling practice; specific citation unverified)*.
4. **Double annotation + adjudication.** Two independent annotators: associates with 2–6 years' practice, or supervised law-student annotators for G-Claim first pass. Disagreements go to an adjudicator (senior associate/partner), who records a rationale. α is reported per batch, and batches below the bar are re-annotated.
5. **Perturbations** (§5.10.4) are generated automatically and *spot-verified* by lawyers (10% sample, plus 100% for Sentinels).
6. **Freeze and sign.** Each version is split **DEV 60% / EXAM 30% (sealed; never used for tuning or prompt iteration; access-logged) / SENTINEL ≤10%**. Every item carries a unique **canary string** so leakage into any training corpus or provider log can be detected. Manifests are signed, and any change needs 2 reviewers (XC threat model).
7. **Rotation.** 20% of EXAM is retired to DEV each quarter and replaced with fresh items. This limits overfitting and contamination. Public benchmarks are treated as possibly contaminated.

#### 5.10.3 Privilege-safe handling
- Gold-room items (data class D0, §5.13) contain no client information and are GLOBAL.
- Retrospective and live-matter items (D2/D3) are authored **inside the tenant plane** in Annotation Studio. They stay `TENANT_PRIVATE` and run only on the tenant-plane eval runner. Only pass/fail counts per task family leave (as P9 specifies).
- Promotion of a D2 item to GLOBAL requires: the client's written consent, a *lawyer-written* public restatement (not automated scrubbing, given PII-tool gaps noted by P9), a P9 Privacy Gate lint, and partner sign-off.
- Masking/RTBF status of public judgments is re-checked at each suite build (P9 §5.8).

#### 5.10.4 Indian perturbation factory
Generates labelled negatives from verified positives. Each operator is a versioned function with a `source=PERTURBATION` tag:
1. `wrong_case`: same-topic work swap.
2. **`wrong_pinpoint_hard`**: move to the paragraph with the highest lexical overlap in the same judgment that does *not* entail. This is the failure models miss [P8-4].
3. `misquote`: 1–3 token edits, negation insertion, number change.
4. **`role_swap`**: replace a ratio paragraph with the counsel-submission paragraph on the same point.
5. **`dissent_swap`**.
6. `quoted_authority`: cite the quoting judgment for the quoted holding.
7. `status_swap`: an overruled authority on the same proposition.
8. `jurisdiction_swap`: another HC's decision for a "binding" claim.
9. `bench_swap`: two-judge presented as three-judge, or division bench as full bench.
10. **`era_swap`**: IPC section asserted for a post-1-July-2024 offence, or vice versa.
11. `citation_corrupt`: neutral citation year/number, SCC volume/page, or AIR year.
12. `name_mismatch`.

Detection recall per operator is a first-class metric (§9).

#### 5.10.5 End-to-end runs and failure attribution
Every end-to-end item runs with full tracing (`trace_id` across P5/P6/P8). A failed item is attributed to the **first failing phase** using the trace [NOVEL — unvalidated as an automated procedure; inspired by hierarchical error decomposition [P8-7]]:

`P1` gold anchor text/role wrong → `P2/P5` gold anchor absent from the candidates or the bundle → `P3` status or binding wrong → `P6` evidence present but claim wrong or omitted → `P8` claim wrong but VERIFIED (false pass) or right but withheld (false block).

Weekly dashboards show the attribution shares, so engineering effort goes where the errors originate.

#### 5.10.6 Self-maintaining gold
Gold items list `depends_on_ids` (works, provisions, propositions). P8 consumes `graph.delta.v1`. When a status change touches a dependency, the item is marked `stale`, withdrawn from gates, and queued for re-adjudication. Law moves, and a gold set that silently expects yesterday's answer punishes a correct system. Conversely, **each new *definitive* NEGATIVE status auto-generates a draft temporal-trap item** ("Is X good law on proposition P as of today?"; "as of the day before?"). A lawyer confirms it within 5 working days, and it then joins G-Temporal [NOVEL — unvalidated].

#### 5.10.7 LLM-as-judge policy
- **Allowed:** (a) scaling pairwise memo comparisons *after* validation against a lawyer panel on ≥150 pairs, with agreement reported; (b) entailment escalation inside the Verifier; (c) pre-labelling for annotators (shown only after the annotator's own first judgment, to avoid anchoring).
- **Not allowed:** as the sole gate for VT1 metrics, deadline correctness, status, or any EXAM-split headline number without PPI correction.
- **Controls:**
  - judge family ≠ candidate family [P8-36];
  - both orderings for pairwise comparisons [P8-35];
  - span-based rubrics [P8-39];
  - criteria revisited with lawyers when disagreement clusters [P8-37];
  - **PPI**: headline metrics estimated from all judge-labelled items plus the lawyer-labelled subset, giving valid CIs [P8-41][P8-20].

### 5.11 Regression-gating policy (continuous, all phases)

**Levels**
| Level | Trigger | Suites | Budget |
|---|---|---|---|
| **L0** | every PR touching a phase | contract/schema tests, deterministic checker unit tests, 200-item Sentinel mini-suite for the touched component | ≤10 min |
| **L1** | model/prompt/endpoint change; parser/embedder/reranker/index-mapping change; ontology/doctrine rule change; P8 checker/calibrator change | DEV + EXAM for the component's suites, plus the downstream end-to-end sample (change-impact matrix below) | ≤3 h; nightly for batch components |
| **L2** | release candidate | all EXAM suites + 60-memo G-Memo run with judge + a 2-hour lawyer spot review (20 memo sections, 100 claims) | ≤24 h |
| **Shadow → canary** | after L2 (XC §4.6) | 7-day shadow with pairwise disagreement sampling to lawyers; canary 5→25→100% with rollback on quality alarms (§5.12) | per XC |

**Change-impact matrix** (which suites a change must pass)
| Change | Own suites | Downstream suites |
|---|---|---|
| P1 OCR/layout/RR/citation parser | P1 sets | G-Claim (role and quote strata), G-QA sample (200), anchor-stability canary |
| P2 embedder/chunker/index | IN-Ret-* | G-QA full retrieval metrics; G-Memo sample (10) |
| P3 classifier/doctrine rule/ontology | G-Treat, G-Temporal, G-Crosswalk | G-QA status-sensitive subset; Sentinels |
| P5 ranker/fusion/stance | G-QA retrieval | G-Memo (20); adverse metrics |
| P6 prompt/model/workflow | G-Memo, G-Deadline | G-Claim natural outputs (first-pass verification rate) |
| P8 checker/judge/calibrator | G-Claim, G-Audit, perturbation recall | recalibration + band-threshold refit; G-Memo gate outcomes |
| Model Gateway endpoint swap | task's own gold (XC `ModelTaskContract.eval`) | owning phase's L1 set |

**Gate rules**
1. **Zero-tolerance invariants** (any failure = REJECT):
   - Sentinel suite 100%;
   - deadline suite 100%;
   - bad-law leakage 0 (P5 metric);
   - fabricated anchors displayed 0;
   - cross-tenant canary hits 0 (P7);
   - anchor-stability ≥99.5% (P1).
2. **Non-inferiority** on every primary metric, overall and per registered slice. Lower bound of the one-sided 95% paired-bootstrap CI of (candidate − incumbent) ≥ −δ_s, with **δ_s = max(1.0 pt, 2·SE_diff,s)**. Resampling is clustered by question/work, so items from one judgment are not treated as independent [P8-42]. Worked example: a 200-item slice with 6% discordance → SE_diff≈1.7 → δ_s≈3.5 pts. The overall 2,000-item set → δ≈1.1 pts. *Consequence:* small-slice regressions are caught by accumulating across releases (a rolling 3-release window) rather than by a single noisy run.
3. **Improvement claims** (e.g. "new reranker is better") require the CI lower bound > 0 on the primary metric.
4. **Nondeterminism budget.** LLM-dependent suites are run with temperature 0 where supported. Any suite whose run-to-run SD on an unchanged candidate exceeds 0.5 δ_s is re-run with n=3 repeats and averaged. Flaky items are quarantined with a ticket.
5. **Waivers.** Signed by the eval owner + the legal lead. Time-boxed (≤14 days). Listed on the trust ledger's internal twin. Never for zero-tolerance invariants.
6. **Backfill hand-off.** `eval.run.completed.v1` carries the metric deltas. P4 decides reprocessing (P4/P1 own cost), and P8 re-runs the affected gold after backfill.

### 5.12 Production monitoring, audit sampling and drift
- **Online signals** (per model/prompt/tenant/stratum, daily): first-pass verification rate (P6 metric); status mix; withheld rate; judge escalation rate; checker–judge disagreement rate; C3b re-anchor rate; UNVERIFIABLE by reason; lawyer flags per 100 displayed claims (P9); Citation Audit finding rates.
- **Drift alarms.** Weekly rates vs an 8-week baseline, with alarms on >3σ moves or a p<0.01 χ² test on the stratum mix. *Input drift* (language, OCR, court mix) triggers a calibration review. *Output drift* (verification rate, disagreement) triggers the canary replay: XC's weekly 200 fixed items per task (13_cross_cutting.md §4.6).
- **Audit sampling (ground truth in production).**
  - Each week, sample displayed claims stratified by band × stratum: MVP 100/week at the design partner, full version ≥300/week across tenants (consented).
  - Oversample VERIFIED-band VT1 claims and new strata.
  - Partner lawyers adjudicate in Annotation Studio in the tenant plane. The realised false-verify rate is estimated with **PPI** (the verifier's confidence as the predictor), giving valid CIs from a few hundred labels [P8-41].
  - The results feed the trust ledger and the α_s breach rule (§5.6), and the labelled items become calibration data.
- **Verification nudges** [NOVEL — unvalidated]. At most one per memo, randomised: "Quick check: does ¶45 support this line? ✓/✗". This yields unbiased audit labels and keeps lawyers in the habit of verifying. It is rate-limited and switchable per user.

---
### 5.13 Design Partner Program (DPP)

**Goal.** Turn one firm's expertise into (a) gold sets no competitor has (Indian, adverse-aware, temporal, paragraph-level), (b) a verifier and calibrator trained on Indian legal adjudications, and (c) a credible, audited trust record. The firm's clients and privilege must never be put at risk.

**Legal instruments** (drafts for Indian counsel review; positions below are design intent, not legal advice)
1. **Design Partnership Agreement.**
   - *Scope:* pilot seats, SLAs, and the annotation commitment (hours/month).
   - *IP:* the firm keeps all work product. We receive a perpetual, royalty-free licence to D0/D1 data (below). Co-branding or naming the firm requires separate written consent.
   - *Exit:* on termination the firm keeps its tenant-private eval suite (export), and D2/D3-derived items are deleted.
2. **Data Processing Agreement.** We act as processor for the firm (data fiduciary). The DPDP s.17(1)(a) exemption ("processing … necessary for enforcing any legal right or claim") disapplies Chapter II except s.8(1) and s.8(5), plus Chapter III and s.16 [P8-68]. **Do not assume it covers evaluation use.** Using client personal data to evaluate or train a vendor's tool is plausibly *not* "necessary for enforcing a legal right or claim". D2/D3 eval processing is therefore designed to need no exemption. It runs on de-identified, lawyer-restated items (D2) or stays inside the tenant plane under the firm's own processing purpose (D3), with client consent as the basis whenever personal data survives restatement *(legal position unverified; Indian counsel to confirm)*. Timing: the DPDP Rules, 2025 were notified on 14 Nov 2025 (G.S.R. 843(E)). Most substantive obligations (ss.3–5, 7–17) commence 18 months later, around **May 2027** [P8-74], which falls inside the full-version window (§10). The DPP must be DPDP-compliant from day one, not retrofitted. Breach notification, sub-processor list, India residency, and deletion SLAs are per P7/XC.
3. **Evaluation Data Contribution Schedule.** Defines data classes D0–D4 (table below), permitted uses, retention and withdrawal.
4. **Client consent template** for retrospective matters (D2). BSA s.132 bars an advocate from disclosing client communications or advice without the client's *express consent*, and the duty extends to the advocate's clerks and employees [P8-69]. The SC recently reaffirmed advocate privilege protections, extending s.132 to advisory and pre-litigation work. It also held that the privilege does **not** extend to salaried in-house counsel, who are not "advocates" under the Advocates Act, and that privilege does not by itself shield documents from production orders [P8-70]. Two design consequences follow. The vendor's own legal engineers and annotation staff cannot claim s.132 cover, which is one more reason they get no D2/D3 content access. And items derived from a corporate client's in-house counsel communications must be treated as *unprivileged but confidential*, needing the same consent path. So D2 requires *written, specific* client consent covering: purpose (evaluation of a research tool), the lawyer-authored restatement, no disclosure of identity, and withdrawal rights.
5. **Annotator notice.** Per-annotator reliability scores and labels are personal data of the firm's employees. The notice covers purpose, retention and access; reliability scores are never shared with the employer for performance evaluation.
6. **Ethics review.** An ABA-512-style duty of competence and confidentiality is used as a comparative benchmark for informed consent on GenAI use [P8-71]. Bar Council of India rules on advertising, solicitation and confidentiality *must be reviewed by Indian counsel before any public co-authorship or case study (not verified in this research)*.

**Data classes**
| Class | What | Consent basis | Location | Retention | Use |
|---|---|---|---|---|---|
| **D0** gold-room public-law items | questions over public law, authored by partner lawyers; no client facts | DPA + contribution schedule | global Gold Store | indefinite (versioned) | GLOBAL gold; subset may be published as an open Indian verification benchmark with the firm's consent |
| **D1** adjudications of our outputs on public queries | labels on public anchors | same | global | indefinite | calibration, checker training, GLOBAL eval |
| **D2** retrospective closed matters | lawyer-written, de-identified case studies + expected authorities | **client written consent** + partner sign-off | tenant plane; GLOBAL only for the public restatement | until withdrawal; review annually | TENANT_PRIVATE eval; GLOBAL after restatement |
| **D3** live shadow matters (opted-in) | the firm's actual research/filed authorities vs our outputs | matter-level opt-in by the responsible partner (P7 `privilege_flags`) | tenant plane only | matter retention | TENANT_PRIVATE regression; only aggregate counts leave |
| **D4** raw privileged documents | pleadings, correspondence, advice | none for eval | never leaves the tenant | per P7 | **never** used for global eval or training; vendor staff never see it |

**Privilege-protective mechanics**
- Annotation Studio for D2/D3 runs **inside the firm's tenant plane** (or their private cloud for dedicated deployments). Vendor staff have no content access (P7 operator model).
- Restatements are checked by the P9 Privacy Gate lint (identifiers, PAN/Aadhaar-like patterns via India recognisers) and then by the firm's designated privacy partner.
- Ethical walls (P7) apply to annotation assignment. An annotator never labels items derived from matters they are walled from.
- Withdrawal: deleting a consent triggers removal of derived eval items and retraining exclusions via P9's unlearning path.

**Annotation protocol**
- *Roles:* Contributors (associates 2–6 yrs), Adjudicators (senior associates/partners), and optionally supervised law-student annotators (NLU clinic) for D0 first-pass and perturbation spot-checks.
- *Cadence:* a weekly 2-hour "gold room" (3–4 lawyers) plus an async queue; month-1 calibration workshop; monthly α report and guideline update.
- *Effort planning estimate [unvalidated]:*
  - ≈2.5 lawyer-hours per G-QA item (authoring + second annotation + adjudication);
  - ≈6 lawyer-minutes per G-Claim pair (two annotators);
  - ≈4 h per G-Memo reference outline.
  - Year-1 gold ≈ 800×2.5 + 8,000×0.1 + 60×4 ≈ **3,000–3,500 lawyer-hours**. Most G-Claim first passes can use supervised students, which reduces senior time.
- *Quality:* α per label family per batch; reliability-weighted adjudication (P9 `actor_reliability`); honeypot items (known answers) at 5%.

**Incentives for the firm** (combine, don't rely on one)
1. Pilot seats free, then founding-customer pricing.
2. **Firm-private eval dashboards**: measured accuracy of the system on *their* practice areas and their own research. This is useful for their own AI governance.
3. **Free Citation Audit** of their outgoing filings and of incoming orders (§5.8), a direct risk-reduction benefit given the Indian incidents [P8-8].
4. Paid annotation hours for work outside billable time.
5. Roadmap influence via a monthly steering committee.
6. Optional co-authorship of an open Indian legal-verification benchmark built from D0 (subject to the ethics review above).

**Governance.** Monthly steering committee: firm KM partner, our eval lead, our legal lead. Data-use register visible to the firm. Quarterly consent re-confirmation. Audit rights for the firm over D2/D3 handling.

**Proprietary data advantage (what compounds).**
1. Adjudicated Indian claim–anchor pairs with role, status and binding labels. They train `minicheck-in` and the calibrator. No public equivalent exists (§3.7).
2. Adverse-aware, temporal and crosswalk gold that tracks law changes automatically (§5.10.6).
3. A multi-year audited trust ledger.
4. The error taxonomy and perturbation factory tuned to Indian judgments.

A competitor can copy the *method* in months. The *adjudicated data, the partner relationships and the audit history* take years. **Concentration risk:** one firm skews practice areas and style. Add a second and third partner firm (different cities and practice mixes) and an academic partner for D0 by months 9–12, and cap any single firm's share of GLOBAL gold at ≤50% by the end of Year 1, falling as partners are added.

### 5.14 Cross-cutting: security, cost at scale (≈5M+ docs), latency, observability, model-agnostic design
**Security.**
- The Verifier runs inside the tenant boundary for private claims. Egress only to the Gateway, P1/P3 read APIs and the tenant store.
- Gold Store: signed manifests, 2-reviewer changes, access logging on the EXAM split, canary strings to detect training contamination.
- Eval calls to external LLMs use only ZDR/no-training endpoints (XC registry `zdr`, `trains_on_data=false`), and EXAM items are never sent to endpoints without those guarantees.
- Judge prompt-injection controls are in §5.3.
- Reports are signed (Ed25519), and keys are managed per XC.

**Latency** (fits XC §6.1: a full verified answer within 25 s p95)
| Step | Q&A answer (~20 claims) p95 | Memo section (~20 claims, VT1-heavy) p95 |
|---|---|---|
| Anchor + AuthorityView batch fetch (C1, C6–C8) | 150 ms | 200 ms |
| Deterministic checks (C0, C2, C5, C9, C10, C12) | 50 ms | 100 ms (incl. rule recompute) |
| Small checker, ~80 sub-claim pairs, 1 GPU batch | 300 ms | 300 ms |
| Judge escalations (≈20% of claims; VT1 all), parallel | 2.5 s | 4 s (two passes) |
| C3b re-anchoring (≈5% of claims) | 400 ms | 600 ms |
| Calibration, report assembly, signing | 50 ms | 50 ms |
| **Total** | **≈3.5 s (target ≤4 s)** | **≈5.3 s (target ≤8 s; ≤20 s incl. one repair round-trip)** |

Revalidation (C6–C8 only): ≤5 s p95 for 200 claims. Citation Audit of a 50-page order: ≤60 s p95 (async).

**Cost** (token model. Prices are illustrative and owned by 13_cross_cutting.md.)
- Judge call ≈1,800 input + 200 output tokens.
- Q&A answer: ≈5 judge calls → ≈9K in / 1K out. At an illustrative $1–3 per M input and $5–15 per M output, that is **≈$0.015–0.045**.
- Memo: ≈100 claims, ≈50 judge calls including VT1 double passes and one repair re-verification → ≈90K in / 10K out → **≈$0.15–0.45**, plus decomposer calls (small model) ≈$0.02.
- Small-checker GPU: 1–2 L40S-class GPUs serve ≳100 pair-checks/s for sub-1B models *(throughput unverified; benchmark before sizing)*. On AWS Mumbai that is ≈$1.6–3.3K/month (g6e.xlarge at $2.235/h [P8-72]), or roughly half on Indian GPU clouds (L40S ₹102/h [P8-73]).
- At XC's planning load (2,000 seats × 200 answers + 4 memos/month): ≈$6–18K/month for judges plus ≈$2–3K for GPU. **Corpus size (5M → 10M+) does not change per-claim cost**. It changes only anchor-store and P3 lookup scale, which those phases own.
- Eval: a nightly L1 on the largest suites is ≈20K judge calls → ≈$40–120/night. L2 is ≈$150–400 per release. **Lawyer time dominates** (≈3,000+ hours in Year 1, §5.13).

**Observability.** Per-check latency and verdict histograms. Reason-code rates by `verifier_version`. Checker–judge confusion matrix. Calibration reliability diagrams per stratum (weekly). An eval-run lineage graph (candidate `pipeline_version` → run → gate decision). OpenTelemetry spans share `trace_id` with P5/P6.

**Model-agnostic design.** All model calls are Gateway tasks (`p8.entail_small`, `p8.entail_judge`, `p8.role_judge`, `p8.decompose`) with JSON schemas and per-family prompt templates. The small checker is self-hosted (open weights), so it survives provider changes and runs on-prem. A judge swap is an L1 gate plus recalibration. On-prem/IN_ONLY tenants get a qualified open-weight judge, and any quality gap is **measured and disclosed** per residency tier (13_cross_cutting.md §4, "model-quality parity gap").

---
## 6. Alternatives considered and why they were rejected

**D1 — Verifier architecture**
| Option | Accuracy | Cost | Latency | Maintainability | Defensibility |
|---|---|---|---|---|---|
| A. Frontier LLM judges every claim | good on generic grounding; misses pinpoints on topical overlap [P8-4]; self-preference if same family [P8-36] | high (≈10–20× ours) | 3–8 s per section, variable | prompt drift per provider | low (anyone can do it) |
| B. Small NLI checker only | ≈frontier on generic grounding [P8-14]; weak on numbers, roles, cross-lingual | very low | <0.5 s | easy | low–medium |
| C. Agentic verifier (search + read) | 84% recall / 41% precision on U.S. citations [P8-3] | very high (15 steps/item) | tens of seconds | complex | low |
| **D. Deterministic warrant checks + small checker + heterogeneous judge on uncertainty/VT1 + human for VT1 disagreements (chosen)** | highest: exact checks where possible, models only for entailment/role; C3b fixes pinpoints | low–medium | ≤4 s answer | medium (shared library with P6) | **high**: depends on our anchors, roles, statuses and Indian adjudications |

**D2 — Displayed confidence**
| Option | Pros | Cons | Verdict |
|---|---|---|---|
| LLM verbalised % | trivial | overconfident [P8-32]; not auditable | ✗ |
| Raw checker probability | cheap | uncalibrated across strata; percentages alter reliance unpredictably [P8-44][P8-45] | ✗ (feature only) |
| Semantic entropy / self-consistency | strong for free-form QA [P8-23] | 5–10× compute [P8-24]; weak fit for closed-world, anchor-bound claims | feature for opinions only |
| **Stratified calibrated model + conformal band thresholds + ordinal bands with audited error rates (chosen)** | auditable, honest, stratum-aware | needs labelled data; shift-fragile → audit loop (§5.6, §5.12) | ✔ |

**D3 — Gold-set sourcing**
| Option | Quality | Cost | India fit | Verdict |
|---|---|---|---|---|
| Public benchmarks only | uneven; contaminated; wrong tasks (§3.7) | ≈0 | poor (no adverse/temporal/paragraph support) | smoke tests only |
| LLM-synthesised Q&A | scalable | cheap | inherits model blind spots; circular | perturbations only, lawyer-spot-checked |
| Crowd / law students alone | moderate | low | α likely lower on status/role *(unverified)* | supervised first pass only |
| **Partner lawyers (gold room + consented matters) + supervised students + perturbation factory (chosen)** | high, measured by α | high (lawyer hours) | best | ✔ |

**D4 — Regression statistics**
| Option | False blocks | Missed regressions | Verdict |
|---|---|---|---|
| Fixed point thresholds ("no slice drops > 1 pt") | many on small slices (SE≈2.5 pts at n=200) | few, but people learn to ignore the gate | ✗ |
| Online A/B only | — | traffic too small in Year 1 (one firm; P9 §5.7) | complement only |
| **Paired-bootstrap non-inferiority with δ_s + zero-tolerance sentinels + rolling windows (chosen)** | controlled | small-slice drifts caught over 3 releases | ✔ |

**D5 — Eval harness**
| Option | Verdict |
|---|---|
| Adopt RAGAS/ARES-style frameworks wholesale | ✗ as the harness: no authority/temporal semantics. Reused as metric ideas (faithfulness, context precision/recall, PPI) [P8-19][P8-20] |
| Fully bespoke runner | ✗: reinvents scheduling, caching and reporting |
| **Thin in-house legal metrics + gold store + gatekeeper on top of an OSS runner (chosen)** | ✔: legal semantics and gold are ours (moat), plumbing is commodity *(specific OSS runner choice deferred; fit unverified)* |

**D6 — Where verification runs**
Verification could run only in the export step (cheap, but lawyers read unverified text meanwhile). It could run as a background audit only (never blocks, but misleads). **Chosen: inline verify-then-show** (P6 §5.7), plus export-time status re-check and background revalidation on graph change.

---

## 7. Novel ideas (clearly labeled as unvalidated)
1. **Warrant vector per claim** [NOVEL — unvalidated]. The `warrant{}` object operationalises the "legal warrant" framing [P8-5] as nine separately logged verdicts. Error analysis, UI chips and calibration all use the same decomposition.
2. **Pinpoint re-anchoring (C3b)** [NOVEL — unvalidated]. When the cited paragraph fails, search the same work for the paragraph that does support the claim. Return PARTIAL with a suggested re-pin instead of pass/fail. It directly targets the wrong-pinpoint gap [P8-3][P8-4].
3. **Role-aware support (C4)** [NOVEL — unvalidated in this form]. Treat "counsel's submission cited as holding" and "dissent cited as majority" as first-class verification failures, using P1's anchor-level speaker/role labels.
4. **Citation Audit of incoming orders as a litigation input** [NOVEL — unvalidated]. Fabricated or misrepresented authority in an impugned order becomes a candidate ground for the lawyer to confirm. This is motivated by Indian set-asides in 2025–2026 [P8-8].
5. **Trust ledger** [NOVEL — unvalidated]. Audited, PPI-estimated error rates per band are published to customers each month. Calibration becomes a contractual-grade promise.
6. **Self-maintaining, law-change-aware gold** [NOVEL — unvalidated]. Gold items subscribe to `graph.delta.v1`: stale items leave the gates, and each definitive overruling generates a temporal-trap item within days.
7. **Indian perturbation factory** [NOVEL — unvalidated]. Operators specific to Indian practice (era_swap IPC↔BNS, bench_swap, jurisdiction_swap across HCs, neutral-citation corruption) measure verifier recall where it matters.
8. **Verification nudges as unbiased audit labels** [NOVEL — unvalidated]. Rare, randomised one-tap checks give ground truth and counter automation bias.
9. **Signed verification appendix** [NOVEL — unvalidated for Indian court practice]. A reproducible record of what was verified, at what graph state, attached to every export.

---

## 8. Failure modes and red-team findings
| Attack / condition | What breaks | Mitigation (design change made) |
|---|---|---|
| **10M+ documents** | Per-claim cost is flat, but gold coverage per stratum thins. P3 status coverage gaps grow for district/tribunal material. `UNVERIFIABLE` rises | Strata quotas and rotation. `coverage.verifiable_share` tracked per court tier. UNVERIFIABLE never displayed as VERIFIED. Audit sampling weighted to new strata. Anchor/AuthorityView batch APIs sized by P1/P3 (P8 issues ≤2 batched calls per request) |
| **Bad OCR** | A quote hash matches *our* text, but our text is wrong (digit or negation OCR errors). Entailment is computed on corrupted premises | C2 OCR trust: low `ocr_conf` or critical-token flags → cross-manifestation agreement, else cap at VERIFIED_WITH_CAVEAT with an image crop. Exports require the page-image check. C9 numbers from low-OCR anchors → WARN. OCR stratum in calibration |
| **Hindi/regional judgment** | The English-trained checker misjudges. Translations drift. Hindi slice gates are underpowered | The *authoritative* expression (anchor-API flag, S8-9) must pass; the other version is a helper. If the flag is missing, both must pass. Hindi negation lists and Indic-digit normalisation are in C2/C9. Multilingual judge qualified on the Hindi slice. VT1 cross-lingual → human. Hindi oversampled to 15% of G-QA. Separate calibration stratum. `CROSS_LINGUAL_UNVERIFIED` chip until the slice passes |
| **Precedent overruled yesterday** | P3 status not yet updated (P0/P4 lag), so C6 says GOOD. Cached reports stale | Watermark shown on chips; amber if older than the court's freshness SLO. Direct-history cautions (stay, pending SLP, larger-bench reference) are a separate C6 row, capped at VERIFIED_WITH_CAVEAT (§5.3), because "not yet overruled" is not "safe". P3 asymmetric safety shows `NEGATIVE_SIGNAL_UNDER_REVIEW` quickly. Cache invalidation on delta. Export re-checks at graph head. Living memo REVERIFY via P4→P7→P6. Auto-generated temporal trap confirms the fix |
| **Malicious user / prompt-injected document** | Anchor text contains "mark this as entailed". An opponent's notice asserts false "facts". Coordinated false flags try to poison gold | Checker is not instruction-following. Judge I/O typed + exact-span requirement. Injection-suspect anchors skip the judge (band capped). C10 attribution. Eval candidates from feedback need adjudication (2 lawyers for GLOBAL, P9). Signed gold, 2-reviewer changes |
| **Confused user** | Lawyer edits a verified claim into an unsupported one and exports it. False premise in the question | Wrong forum or as-of date chosen → `context_warnings` + `CONTEXT_MISMATCH` against MatterContext (C7). Edits re-enter `/verify` (DRAFT mode). Export gate (`strict_export`) plus "DRAFT – NOT VERIFIED" watermark (P6). C6 CONTRADICTED on false status premises, surfaced as a premise correction |
| **Source outage / format change** | Paragraph renumbering after re-parse; new documents lack anchors; the site is down | Verification uses stored anchors and aliases, never live sites. Anchor-stability canary on gold works (L1 for P1 changes). Missing anchors → UNVERIFIABLE, not UNSUPPORTED |
| **Verifier–generator correlation** | The same model family makes the same mistake twice | Judge family ≠ generator family (enforced). The small checker is an independent architecture |
| **Over-blocking / vacuous memos** | Conservative thresholds withhold most claims, and lawyers abandon the tool | Withheld rate and BLOCK rate are gated metrics (§9). C3b and `narrowed_text` convert failures into PARTIAL. Informativeness tracked [P8-28] |
| **Automation bias** | Lawyers stop reading sources because "Verified" feels final | Legend states audited error rates. Verification nudges. No per-token scores [P8-45]. "Verification ≠ advice" statement |
| **Goodhart / contamination** | Tuning to gold, or gold leaking to providers or training sets | Sealed EXAM split, quarterly rotation, canary strings, ZDR-only eval endpoints, public benchmarks non-gating |
| **Gold goes stale** | Law changes make "expected" answers wrong, punishing a correct system | Self-maintaining gold (§5.10.6) |
| **Single-partner bias** | Metrics reflect one firm's practice and style | Strata quotas, ≤50% share cap, additional partners by months 9–12 |
| **Cost blow-up** | A 2,000-page paper book with thousands of citations sent to `/audit`; a tenant scripting `/verify`; judge price rise | `AuditRequest.budget.max_mentions` (default 2,000) with `truncated=true`, not silent drops. Per-request `max_llm_calls`. Per-tenant daily judge quota, after which the verifier degrades to small-checker-only with capped bands. `BUDGET_EXHAUSTED` → UNVERIFIABLE, never PASS (§5.4). Cost-per-claim gate (§9.1) |
| **Hidden-text / Unicode tricks in uploaded PDFs** | Invisible text-layer spans or zero-width/homoglyph characters make a quote "match", or smuggle instructions into premises | P1 invisible-span flags plus C2 normalisation logging → `HIDDEN_TEXT_SUSPECT`. These spans are excluded from premises and need a page-image check (§5.3) |
| **Delta storm** | A Constitution Bench overruling or a P3 backfill invalidates 10⁴–10⁶ cached statuses at once | Reverse-index invalidation, priority revalidation (export or hearing ≤7 days first), per-tenant concurrency caps, lazy recompute-on-read, `bulk=true` deltas do not spawn sentinels (§5.9) |

### 8.R Independent review findings
An independent adversarial review (30 Sep 2026) re-fetched about 35 of the highest-stakes references and red-teamed the design.

**Citation corrections made**
- **Vals VLAIR [P8-10].** The earlier text gave "ChatGPT 77%". The report gives only a 74–78% band for *all four* AI products including ChatGPT, and Lexis+ AI and Westlaw declined to participate. Corrected.
- **IL-TUR [P8-46].** "GPT underperformed SOTA on every task" was wrong: GPT-4 beat SOTA on legal MT (MILPaC). Corrected.
- **LePhantomCite [P8-3].** Added that the benchmark's errors are mostly *synthetically injected* into real U.S. briefs, that the 40.8% precision is derived from recall and F1, that the best precision was 76.1%, and that 19.9% of opinions lacked pagination.
- **Scope of foreign evidence.** Ovcharov [P8-6] studies Ukrainian law and Legal RAG Bench [P8-7] uses an Australian corpus. Both are now labelled, so their numbers are not read as Indian evidence.
- **BHRAM-IL [P8-59]** is general-domain, not legal, and is now labelled as such. **Falkor-IRAC [P8-65]** is a 51-judgment proof of concept, now stated.
- **Other clarifications.** Relation-level vs "step-level" uncertainty [P8-45] was clarified. The SC privilege judgment [P8-70] now includes the in-house-counsel exclusion. A DPDP Rules 2025 commencement reference was added [P8-74].
- **Confirmed as written.** Magesh per-tool rates [P8-1], Dahl 58/88% [P8-2], Verma 37–61% [P8-4], Taranukhin & Shwartz warrant elements [P8-5], all Charlotin India entries cited [P8-8], LLM-AggreFact numbers [P8-14], MiniCheck 400× [P8-12], conformal-RAG caveats [P8-28], Demir & Canbaz 79.1/67.7% [P8-63], DPDP s.3(c)(ii) and s.17 texts [P8-67][P8-68], and author lists and titles of 14 further arXiv references.

**Spine conformance fixes**
- `EvalCase.case_id` collided with the spine's `case_id` (`cas_…`). It is renamed `eval_case_id` (`evc_…`) (S8-7).
- C0 allowed an R-handle alone to support a LEGAL_PROPOSITION, and PROCEDURAL claims with no anchor, contrary to spine §H ("≥1 anchor"). Now fixed.
- The memo-level gate (spine) vs section-level gate (this doc) is made explicit (S8-6).
- The use of P3-proposed `AuthorityStatus` values now has a stated fallback (S8-8).
- New events now show the §G envelope.
- `supersedes_report_id` is now in the schema. `CitationAuditReport` and `AuditRequest.forum` are now concrete schemas.

**Design gaps patched**
1. Indic-digit, lakh/crore, day-first date and section-suffix normalisation in C2/C9. Language-aware (Hindi) negation lists.
2. Direct-history cautions (stay, pending SLP, larger-bench reference) in C6. They are common in Indian practice and were previously invisible.
3. Authoritative-language determination instead of assuming the original is English (S8-9).
4. Forum and as-of-date mismatch with MatterContext (confused user).
5. Hidden-text-layer and Unicode/homoglyph injection in uploaded PDFs.
6. Hard budget semantics (`BUDGET_EXHAUSTED` → UNVERIFIABLE), `/audit` mention caps and per-tenant judge quotas (cost blow-up).
7. Delta-storm invalidation and priority revalidation.
8. Case-name matching rule for Indian cause titles.
9. The DPDP s.17(1)(a) exemption is no longer assumed to cover evaluation use, and the DPDP commencement date (~May 2027) is flagged.
10. Advocate privilege does not cover in-house counsel.

**Still open (not fixable on paper)**
- (a) No measured Indian numbers exist yet for any threshold in §5.3–5.6. Every τ/α is a planning value until G-Claim EXAM exists.
- (b) The recall of `wrong_pinpoint_hard` on Indian judgments is unknown (§11.3).
- (c) Hindi and regional verification quality is unknown, and no Indian legal NLI set exists (§11.2).
- (d) "Overruled yesterday" is bounded by P0/P3 latency. P8 can only disclose staleness, not remove it. Pronounced-but-unuploaded judgments are invisible to every check.
- (e) The DPDP and BCI positions in §5.13 need Indian counsel.
- (f) The Charlotin-listed Indian orders are still secondary descriptions (§11.9).
- (g) Throughput and GPU sizing for the small checker are unbenchmarked (§5.14).

---
## 9. Evaluation metrics for this phase

### 9.1 Verifier and trust metrics (P8's own)
| Metric | Definition | MVP (m6) | Full (m18) | Gate type |
|---|---|---|---|---|
| **Realised false-verify rate** | share of VERIFIED-band claims judged wrong or unsupported in production audit (PPI 95% CI upper bound) | VT2 ≤ 3%, VT1 ≤ 1% | VT2 ≤ 2%, VT1 ≤ 0.5% | SLO; breach → auto-tighten + incident |
| Perturbation detection recall | per operator (§5.10.4) on G-Claim/G-Audit | wrong_case ≥ 0.99; misquote 1.0; **wrong_pinpoint_hard ≥ 0.85**; role_swap ≥ 0.85; dissent_swap ≥ 0.95; status/era/jurisdiction swaps ≥ 0.98 | ≥ 0.99 / 1.0 / **≥ 0.93** / ≥ 0.93 / ≥ 0.98 / ≥ 0.995 | non-inferiority + floors |
| False-block rate | correct, adequately supported claims marked UNSUPPORTED/CONTRADICTED (G-Claim natural positives) | ≤ 6% | ≤ 3% | non-inferiority |
| Withheld rate / BLOCK rate | share of claims withheld; share of memo sections BLOCKed | ≤ 15% / ≤ 5% | ≤ 8% / ≤ 2% | tracked, alarm on +50% |
| Calibration | ECE per stratum with ≥300 labels; reliability-diagram slope | ECE ≤ 0.05 pooled | ≤ 0.05 per stratum | gate on calibrator change |
| UNVERIFIABLE share | by reason and court tier | report | ≤ 5% for SC/HC | tracked |
| Budget exhaustion | share of claims UNVERIFIABLE with `BUDGET_EXHAUSTED`; share of audits `truncated` | ≤ 1% / ≤ 5% | ≤ 0.3% / ≤ 2% | alarm |
| Normalisation robustness | detection recall on Indic-digit, lakh/crore, day-first-date and hidden-text perturbations (G-Claim/G-Sec) | ≥ 0.98 | 1.0 | sentinel (zero-tolerance for hidden-text) |
| Citation Audit | per-class recall/precision on G-Audit | recall ≥ 0.90 (NOT_FOUND/NAME_MISMATCH ≥ 0.98), precision ≥ 0.80 | recall ≥ 0.95, precision ≥ 0.90 | non-inferiority |
| Latency | p95 per mode (§5.14) | ≤ 4 s answer / ≤ 8 s section | same | SLO |
| Cost | $ per verified claim; judge escalation rate | ≤ $0.004/claim; ≤ 30% | ≤ $0.003; ≤ 20% | tracked |
| Gold health | α per label family; stale-item turnaround; EXAM access anomalies | α ≥ 0.80 core labels; ≤ 10 working days | ≤ 5 days | process |
| Judge validity | judge–lawyer agreement on the validation set; κ/α reported | report | ≥ lawyer–lawyer agreement − 5 pts | required before a judge may be used for a metric |

### 9.2 Per-phase metric catalogue (P0–P10) — what the gates run
Targets come from the phase docs where they exist; P8 adds gate type and gold set. Where a phase doc is not yet written (P4, P10) or lacks metrics (P3), targets are **P8 proposals** for the owning phase to confirm.

| Phase | Primary metrics (target MVP → full) | Gold / source | Gate type |
|---|---|---|---|
| **P0** acquisition | Freshness p95 HOT ≤ 30 min; coverage recall ≥ 99.5% HOT; false-change ≤ 0.5%; provenance completeness 100% (P0 §9) | audited listing samples (200/source/month) | SLO + zero-tolerance for legal-compliance counters |
| **P1** parsing | OCR CER EN ≤ 1%, HI ≤ 3% → 0.5%/2%; **critical-token error ≤ 0.5% → 0.1%**; RR macro-F1 ≥ 0.75; citation resolution top-1 ≥ 0.97, false-merge ≤ 0.1%; anchor stability ≥ 99.5% (P1 §9) | IC-OCR-Bench, 5,000 mentions, 300 gold judgments; IL-TUR RR/NER smoke [P8-46] | L1 non-inferiority; anchor stability zero-tolerance |
| **P2** indexing | Hybrid Recall@100, nDCG@10 per language/court tier; as-of statute correctness 100%; summary sentence entailment ≥ 98% (P2 §9) | IN-Ret-*; G-Temporal statute subset | L1 |
| **P3** graph | **Negative-treatment recall** (OVERRULES/REVERSES/STRUCK_DOWN) ≥ 0.95 → 0.98 at review-queue level; treatment macro-F1 ≥ 0.70 → 0.80; **Average Severity Error** [P8-63] ↓; AuthorityStatus accuracy on G-Temporal ≥ 0.97 → 0.995; crosswalk accuracy ≥ 0.98; tier-1 review SLA | G-Treat, G-Temporal, G-Crosswalk | L1; bad-status sentinels zero-tolerance *(P8 proposal)* |
| **P4** propagation | Seeded-event recall 100% (every affected matter dependency flagged); impact→alert p95 ≤ 15 min (P7 §9.3); false-impact rate ≤ 10%; reprocessing idempotency (re-run yields identical outputs) 100% | seeded overrule/amend events on a replayed graph | zero-tolerance on recall *(P8 proposal)* |
| **P5** retrieval | nDCG@10 ≥ 0.55 → 0.70; **BAR ≥ 0.85 → 0.95; AAR ≥ 0.75 → 0.90**; bad-law leakage 0; as-of ≥ 0.98; Hindi gap ≤ 0.15 → 0.07; context precision/recall reported (P5 §9) | G-QA, G-Temporal | L1 non-inferiority; leakage zero-tolerance |
| **P6** reasoning | Issue recall ≥ 0.85; adverse binding coverage ≥ 0.80; deadline correctness 100%; first-pass verification ≥ 0.80 → 0.90; lawyer preference ≥ 40% prefer-or-tie; **answer score vs source score** reported separately [P8-11] (P6 §9) | G-Memo, G-Deadline, G-Claim natural | L2 + deadline zero-tolerance |
| **P7** workspace | Cross-tenant/cross-wall canary hits 0; privilege suggestion recall ≥ 0.98; hearing-date accuracy ≥ 99.5%; deadline-candidate recall ≥ 0.95 (P7 §9) | P7 canary + partner diaries | zero-tolerance isolation |
| **P8** verification | §9.1 | G-Claim, G-Audit, audits | as §9.1 |
| **P9** feedback | Proposal precision; flag→fix time; citation-flag rate per 100 claims ↓; loop health (P9 §9) | adjudicated proposals | release train (P9 §5.13) using §5.11 statistics |
| **P10** surface | Click-to-source success ≥ 99.9%; time-to-first-verified-section p95 ≤ 2 min (P6); alert precision ≥ 0.8 (sev 1–2); **appropriate-reliance rate**: share of nudged claims where the lawyer's ✓/✗ matches the audit label ≥ 0.9; exported "Check this" items without review = 0 | telemetry + nudges | SLO *(P8 proposal)* |
| **End-to-end** | Warrant-accuracy per answer (all consequential claims warranted); first-failing-phase attribution shares (§5.10.5); hallucination rate *with* coverage reported [P8-6] | G-QA, G-Memo | L2 |

---

## 10. MVP version vs. full version
| Capability | MVP (months 0–6, one design partner) | Full (months 6–18) |
|---|---|---|
| Checks | C0–C3, C5–C10, C12 deterministic + off-the-shelf small checker + one heterogeneous judge; C3b; C4 via P1 labels + judge fallback | `minicheck-in` fine-tuned (EN+HI); C11 coherent-opinion check; cross-lingual qualified judge; injection-aware routing |
| Confidence | Pooled isotonic calibration on ≈1,500–2,000 adjudicated claims; three visible bands; audited error rates in the legend | Stratified calibration + conformal thresholds per stratum; trust ledger per tenant; PPI weekly |
| Audit | Citation Audit for own drafts and incoming orders (SC/HC citations) | All schemes incl. tribunals; batch audits; signed appendix standard in exports |
| Gold | G-QA 300, G-Claim 2,000, G-Temporal 150, G-Crosswalk 200, G-Deadline 300, G-Memo 20, Sentinels 200; α reports | Year-1 sizes (§5.10.1); self-maintaining gold; auto temporal traps; 2–3 partner firms + academic D0 partner |
| Gating | L0 + L1 for P5/P6/P8/Gateway swaps; manual L2; non-inferiority statistics | Full change-impact matrix for all phases; automated L2; rolling-window slice detection; waiver register |
| Monitoring | Online signals + 100 audited claims/week | ≥300/week across consenting tenants; drift alarms feeding the canary replay |
| DPP | Agreement + DPA + contribution schedule; gold room weekly; D0/D1 only, D2 pilot with 5 consented matters | D2/D3 at volume in tenant plane; published open benchmark subset (if the ethics review permits) |

**MVP build estimate [unvalidated]:** 2 ML engineers (checker, calibrator, judge prompts), 1 backend engineer (Verify API, gold store, runner), 0.5 legal engineer (guidelines, adjudication ops), plus ≈15 partner lawyer-hours/week. Assumes P1 anchor roles and the P3 AuthorityView API exist.

---

## 11. Open questions and risks
1. **Can the gold be built fast enough?** ≈3,000+ lawyer-hours in Year 1 is a real cost. If partner time slips, calibration strata stay pooled and VERIFIED thresholds stay conservative (more "Check this").
2. **Hindi/regional verification quality is unknown.** No Indian legal NLI benchmark exists. IndicXNLI is machine-translated general NLI [P8-60]. Until the Hindi slice passes, cross-lingual VT1 claims need humans.
3. **Pinpoint recall ceiling.** Even with anchor-level entailment and C3b, `wrong_pinpoint_hard` ≥ 0.93 is a target, not a known result. The literature shows frontier models at 39–63% miss rates on the harder variant [P8-4]. Our advantage (exact paragraph anchors, closed world) is plausible but unmeasured.
4. **Conformal guarantees under shift** remain fragile [P8-28]. The weekly audit is the real safeguard, and it costs lawyer time.
5. **Status freshness vs verification.** P8 is only as current as P3 statuses. Lags on HC/tribunal ingestion (P0) bound what "good law as of today" can mean. The watermark chip is our honesty mechanism.
6. **Legal questions for Indian counsel:** (a) whether BCI rules restrict co-authorship, case studies or naming the partner; (b) whether a vendor's annotation tool inside the firm's tenant keeps s.132 protection intact (P7 open question on vendor staff); (c) DPDP classification of eval data derived from published judgments. s.3(c)(ii) excludes personal data made public by a person under a legal obligation to do so [P8-67]. Whether court publication qualifies is *unverified*, so P9/21 should confirm.
7. **Liability framing.** Does a published trust ledger create warranty exposure? Contract language must describe it as measured performance, not a guarantee.
8. **Judge dependence on frontier providers.** If a provider retires a judge model, recalibration is needed. The self-hosted checker limits the blast radius.
9. **Charlotin-listed Indian incidents are secondary descriptions.** Before any marketing or product copy cites them, the underlying orders must be read and anchored (feed to 21/23).
10. **DPDP timing and basis.** Most substantive DPDP obligations commence around May 2027 [P8-74], during the full-version build. Whether any eval use of client personal data can rely on s.17(1)(a) is doubtful (§5.13). The DPP is designed not to need it, which costs lawyer restatement time.

---
## References

[P8-1] Magesh, V., Surani, F., Dahl, M., Suzgun, M., Manning, C.D., Ho, D.E. "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools." arXiv:2405.20362 (2024); Journal of Empirical Legal Studies, 2025. https://arxiv.org/abs/2405.20362 — verified (arXiv HTML re-fetched in independent review: 202 queries; per-tool accurate/hallucinated/incomplete rates; four causes)

[P8-2] Dahl, M., Magesh, V., Suzgun, M., Ho, D.E. "Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models." arXiv:2401.01301, 2024. https://arxiv.org/abs/2401.01301 — verified (abstract; 58%/88% figures via sibling P6-2)

[P8-3] Liu, P., Stammbach, D., Henderson, P. "Who Checks the Citations? Benchmarking Legal Hallucination Detection" (LePhantomCite). arXiv:2606.21155, 2026. https://arxiv.org/abs/2606.21155 — verified (HTML: dataset composition, synthetic injection, per-class recall, 76.1% best precision, 19.9% missing pagination)

[P8-4] Verma, A. "Is this Citation on Point?" arXiv:2608.12571, 2026. https://arxiv.org/abs/2608.12571 — verified (abstract)

[P8-5] Taranukhin, M., Shwartz, V. "Legal LLM Hallucination Should Be Evaluated as Failure of Legal Warrant." arXiv:2609.17546, 2026. https://arxiv.org/abs/2609.17546 — verified (abstract)

[P8-6] Ovcharov, V. "Citation Grounding Measures the Oracle: Graph Coverage Determines Reported LLM Hallucination Rates in Law." arXiv:2606.00898, 2026. https://arxiv.org/abs/2606.00898 — verified (abstract; Ukrainian legal queries)

[P8-7] Butler, A.-R., Butler, U. "Legal RAG Bench: an end-to-end benchmark for legal RAG." arXiv:2603.01710, 2026. https://arxiv.org/abs/2603.01710 — verified (abstract; Victorian Criminal Charge Book corpus, Australia)

[P8-8] Charlotin, D. "AI Hallucination Cases" database, India filter (16 entries incl. Buckeye Trust v. PCIT, ITAT Bangalore 30 Dec 2024; Greenopolis Welfare Assn. v. Narender Singh, Delhi HC 25 Sep 2025; Omkara Assets Reconstruction v. Gstaad Hotels, SC 8 Dec 2025; Pooja Ramesh Singh v. J&K Bank, SC 2 Jul 2026; Vijay Ghanshyam Gadiya v. UoI, SC 2 Sep 2026). Accessed 30 Sep 2026. https://www.damiencharlotin.com/hallucinations/?q=&sort_by=-date&states=India — verified (database entries; underlying orders not read)

[P8-9] Mata v. Avianca, Inc., No. 22-cv-1461 (S.D.N.Y. 2023) (sanctions for ChatGPT-fabricated citations), as described in Verma 2026. https://arxiv.org/abs/2608.12571 — snippet

[P8-10] Vals AI. "Vals Legal AI Report (VLAIR): Legal Research." 14 Oct 2025. https://vals.ai/industry-reports/vlair-10-14-25 — verified (re-fetched in review: participants Alexi, Counsel Stack, Midpage, ChatGPT; all 74–78%; Lexis/Westlaw declined; individual ChatGPT score not stated)

[P8-11] Harvey. "Introducing BigLaw Bench." 2024. https://www.harvey.ai/blog/introducing-biglaw-bench — verified (sibling fetch, 08_P6)

[P8-12] Tang, L., Laban, P., Durrett, G. "MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents." EMNLP 2024; arXiv:2404.10774. https://arxiv.org/abs/2404.10774 — verified

[P8-13] Zha, Y., Yang, Y., Li, R., Hu, Z. "AlignScore: Evaluating Factual Consistency with a Unified Alignment Function." ACL 2023; arXiv:2305.16739. https://arxiv.org/abs/2305.16739 — verified

[P8-14] LLM-AggreFact Leaderboard (11 grounded-factuality datasets; balanced accuracy). Accessed 30 Sep 2026. https://llm-aggrefact.github.io/ — verified

[P8-15] Min, S. et al. "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation." EMNLP 2023; arXiv:2305.14251. https://arxiv.org/abs/2305.14251 — verified

[P8-16] Wanner, M., Ebner, S., Jiang, Z., Dredze, M., Van Durme, B. "A Closer Look at Claim Decomposition." arXiv:2403.11903, 2024. https://arxiv.org/abs/2403.11903 — verified

[P8-17] Jiang, Z. et al. "Core: Robust Factual Precision with Informative Sub-Claim Identification." arXiv:2407.03572, 2024. https://arxiv.org/abs/2407.03572 — verified

[P8-18] Song, Y., Kim, Y., Iyyer, M. "VeriScore: Evaluating the factuality of verifiable claims in long-form text generation." arXiv:2406.19276, 2024. https://arxiv.org/abs/2406.19276 — verified

[P8-19] Es, S., James, J., Espinosa-Anke, L., Schockaert, S. "Ragas: Automated Evaluation of Retrieval Augmented Generation." EACL 2024 (demo); arXiv:2309.15217. https://arxiv.org/abs/2309.15217 — verified

[P8-20] Saad-Falcon, J., Khattab, O., Potts, C., Zaharia, M. "ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems." NAACL 2024; arXiv:2311.09476. https://arxiv.org/abs/2311.09476 — verified

[P8-21] Gao, T., Yen, H., Yu, J., Chen, D. "Enabling Large Language Models to Generate Text with Citations" (ALCE). EMNLP 2023; arXiv:2305.14627. https://arxiv.org/abs/2305.14627 — verified

[P8-22] Niu, C. et al. "RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models." ACL 2024; arXiv:2401.00396. https://arxiv.org/abs/2401.00396 — verified

[P8-23] Farquhar, S., Kossen, J., Kuhn, L., Gal, Y. "Detecting hallucinations in large language models using semantic entropy." Nature 630, 2024. https://www.nature.com/articles/s41586-024-07421-0 — snippet (referenced in [P8-24])

[P8-24] Kossen, J. et al. "Semantic Entropy Probes: Robust and Cheap Hallucination Detection in LLMs." arXiv:2406.15927, 2024. https://arxiv.org/abs/2406.15927 — verified

[P8-25] Kuhn, L., Gal, Y., Farquhar, S. "Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation." ICLR 2023; arXiv:2302.09664. https://arxiv.org/abs/2302.09664 — verified

[P8-26] Mohri, C., Hashimoto, T. "Language Models with Conformal Factuality Guarantees." ICML 2024; arXiv:2402.10978. https://arxiv.org/abs/2402.10978 — verified

[P8-27] Cherian, J.J., Gibbs, I., Candès, E.J. "Large language model validity via enhanced conformal prediction methods." arXiv:2406.09714, 2024. https://arxiv.org/abs/2406.09714 — verified

[P8-28] Chen, Y. et al. "Is Conformal Factuality for RAG-based LLMs Robust? Novel Metrics and Systematic Insights." arXiv:2603.16817, 2026. https://arxiv.org/abs/2603.16817 — verified (abstract)

[P8-29] Lin, Z. et al. "Domain-Shift-Aware Conformal Prediction for Large Language Models." arXiv:2510.05566, 2025. https://arxiv.org/abs/2510.05566 — verified (abstract)

[P8-30] Rubin-Toles, M., Gambhir, M., Ramji, K., Roth, A., Goel, S. "Conformal Language Model Reasoning with Coherent Factuality." arXiv:2505.17126, 2025. https://arxiv.org/abs/2505.17126 — verified (abstract)

[P8-31] Jiang, Z., Liu, A., Van Durme, B. "Conformal Linguistic Calibration: Trading-off between Factuality and Specificity." arXiv:2502.19110, 2025. https://arxiv.org/abs/2502.19110 — verified (abstract)

[P8-32] Xiong, M. et al. "Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs." ICLR 2024; arXiv:2306.13063. https://arxiv.org/abs/2306.13063 — verified

[P8-33] Kadavath, S. et al. "Language Models (Mostly) Know What They Know." arXiv:2207.05221, 2022. https://arxiv.org/abs/2207.05221 — verified

[P8-34] Guo, C., Pleiss, G., Sun, Y., Weinberger, K.Q. "On Calibration of Modern Neural Networks." ICML 2017; arXiv:1706.04599. https://arxiv.org/abs/1706.04599 — verified

[P8-35] Zheng, L. et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS 2023 D&B; arXiv:2306.05685. https://arxiv.org/abs/2306.05685 — verified

[P8-36] Panickssery, A., Bowman, S.R., Feng, S. "LLM Evaluators Recognize and Favor Their Own Generations." NeurIPS 2024; arXiv:2404.13076. https://arxiv.org/abs/2404.13076 — verified

[P8-37] Shankar, S. et al. "Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences" (EvalGen). UIST 2024; arXiv:2404.12272. https://arxiv.org/abs/2404.12272 — verified

[P8-38] Enguehard, J. et al. "LeMAJ (Legal LLM-as-a-Judge): Bridging Legal Reasoning and LLM Evaluation." arXiv:2510.07243, 2025. https://arxiv.org/abs/2510.07243 — verified (abstract)

[P8-39] Chlapanis, O.S., Galanis, D., Aletras, N., Androutsopoulos, I. "GreekBarBench: A Challenging Benchmark for Free-Text Legal Reasoning and Citations." arXiv:2505.17267, 2025. https://arxiv.org/abs/2505.17267 — verified (abstract)

[P8-40] Karp, M. et al. "LLM-as-a-Judge is Bad, Based on AI Attempting the Exam Qualifying for the Member of the Polish National Board of Appeal." arXiv:2511.04205, 2025. https://arxiv.org/abs/2511.04205 — verified (abstract)

[P8-41] Angelopoulos, A.N., Bates, S., Fannjiang, C., Jordan, M.I., Zrnic, T. "Prediction-Powered Inference." Science 2023; arXiv:2301.09633. https://arxiv.org/abs/2301.09633 — verified (abstract)

[P8-42] Miller, E. "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations." arXiv:2411.00640, 2024. https://arxiv.org/abs/2411.00640 — verified (abstract)

[P8-43] Wikipedia. "Krippendorff's alpha" (acceptability thresholds α≥0.800; 0.667–0.800 tentative; citing Krippendorff, K., Content Analysis, 2004, pp. 241–243). https://en.wikipedia.org/wiki/Krippendorff%27s_alpha — verified (secondary; primary not accessible, 403)

[P8-44] Kim, S.S.Y., Liao, Q.V., Vorvoreanu, M., Ballard, S., Wortman Vaughan, J. "'I'm Not Sure, But…': Examining the Impact of Large Language Models' Uncertainty Expression on User Reliance and Trust." FAccT 2024; arXiv:2405.00623. https://arxiv.org/abs/2405.00623 — verified

[P8-45] Villavicencio, M., Pan, S., Wang, Q. "Not All Uncertainty Is Equal: How Uncertainty Granularity Shapes Human Verification in LLM-Assisted Decision Making." arXiv:2605.28571, 2026. https://arxiv.org/abs/2605.28571 — verified (abstract)

[P8-46] Joshi, A., Paul, S., Sharma, A., Goyal, P., Ghosh, S., Modi, A. "IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning." ACL 2024; arXiv:2407.05399. https://arxiv.org/html/2407.05399v2 ; leaderboard https://exploration-lab.github.io/IL-TUR/ — verified (HTML re-fetched in review: 8 tasks; GPT worse than SOTA on each task except GPT-4 on MILPaC L-MT)

[P8-47] Guha, N. et al. "LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models." NeurIPS 2023 D&B; arXiv:2308.11462. https://arxiv.org/abs/2308.11462 — verified

[P8-48] Pipitone, N., Houir Alami, G. "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain." arXiv:2408.10343, 2024. https://arxiv.org/abs/2408.10343 — verified

[P8-49] Chalkidis, I. et al. "LexGLUE: A Benchmark Dataset for Legal Language Understanding in English." ACL 2022; arXiv:2110.00976. https://arxiv.org/abs/2110.00976 — verified

[P8-50] Zheng, L., Guha, N., Anderson, B.R., Henderson, P., Ho, D.E. "When Does Pretraining Help? Assessing Self-Supervised Learning for Law and the CaseHOLD Dataset." ICAIL 2021; arXiv:2104.08671. https://arxiv.org/abs/2104.08671 — verified

[P8-51] Malik, V. et al. "ILDC for CJPE: Indian Legal Documents Corpus for Court Judgment Prediction and Explanation." ACL 2021; arXiv:2105.13562. https://arxiv.org/abs/2105.13562 — verified

[P8-52] Nigam, S.K. et al. "Legal Judgment Reimagined: PredEx and the Rise of Intelligent AI Interpretation in Indian Courts." Findings of ACL 2024; arXiv:2406.04136. https://arxiv.org/abs/2406.04136 — verified

[P8-53] Nigam, S.K. et al. "NyayaAnumana & INLegalLlama: The Largest Indian Legal Judgment Prediction Dataset and Specialized Language Model." COLING 2025; arXiv:2412.08385. https://arxiv.org/abs/2412.08385 — verified

[P8-54] Fan, Y. et al. "LEXam: Benchmarking Legal Reasoning on 340 Law Exams." arXiv:2505.12864, 2025. https://arxiv.org/abs/2505.12864 — verified

[P8-55] Nigam, S.K., Mishra, S.K., Shallum, N., Ghosh, K. et al. "AILQA: Evaluating AI-Driven Legal Question Answering Systems for the Indian Legal System." arXiv:2607.18825, 2026. https://arxiv.org/abs/2607.18825 — verified (abstract)

[P8-56] Modi, A. et al. "SemEval 2023 Task 6: LegalEval — Understanding Legal Texts." SemEval 2023; arXiv:2304.09548. https://arxiv.org/abs/2304.09548 — verified

[P8-57] Ngo, T.-H. et al. "NOWJ@COLIEE 2026: Adaptive Pipelines for Legal Retrieval and Reasoning" (all five COLIEE 2026 tasks). arXiv:2607.16603, 2026; Nguyen, H.-T. et al. "NOWJ@COLIEE 2025…Legal Retrieval and Entailment." arXiv:2509.08025. https://arxiv.org/abs/2607.16603 — verified (abstract)

[P8-58] Hou, A.B. et al. "CLERC: A Dataset for Legal Case Retrieval and Retrieval-Augmented Analysis Generation." arXiv:2406.17186, 2024. https://arxiv.org/abs/2406.17186 — verified

[P8-59] Terdalkar, H., Bhojani, K., Dongare, A., Behera, O.A. "BHRAM-IL: A Benchmark for Hallucination Recognition and Assessment in Multiple Indian Languages." arXiv:2512.01852, 2025. https://arxiv.org/abs/2512.01852 — verified (abstract; general-domain, not legal; BHASHA workshop, IJCNLP-AACL 2025)

[P8-60] Aggarwal, D., Gupta, V., Kunchukuttan, A. "IndicXNLI: Evaluating Multilingual Inference for Indian Languages." EMNLP 2022; arXiv:2204.08776. https://arxiv.org/abs/2204.08776 — verified

[P8-61] Mahapatra, S. et al. "MILPaC: A Novel Benchmark for Evaluating Translation of Legal Text to Indian Languages." arXiv:2310.09765, 2023. https://arxiv.org/abs/2310.09765 — verified (arXiv metadata: title and authors Mahapatra, Datta, Soni, Goswami, Ghosh; results not read)

[P8-62] Koreeda, Y., Manning, C.D. "ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts." Findings of EMNLP 2021; arXiv:2110.01799. https://arxiv.org/abs/2110.01799 — verified

[P8-63] Demir, M.M., Canbaz, M.A. "Validate Your Authority: Benchmarking LLMs on Multi-Label Precedent Treatment Classification." NLLP 2025; arXiv:2605.17691. https://arxiv.org/abs/2605.17691 — verified (abstract)

[P8-64] Wang, C. et al. "LeKUBE: A Legal Knowledge Update BEnchmark." arXiv:2407.14192, 2024; Li, C. et al. "LexKairos: Benchmarking Legal Temporal Capabilities in LLMs." arXiv:2608.09106, 2026. https://arxiv.org/abs/2407.14192 ; https://arxiv.org/abs/2608.09106 — verified (abstracts)

[P8-65] Bose, J. "Falkor-IRAC: Graph-Constrained Generation for Verified Legal Reasoning in Indian Judicial AI." arXiv:2605.14665, 2026. https://arxiv.org/abs/2605.14665 — verified (abstract; proof of concept on 51 SC judgments; InIRAC dataset)

[P8-66] Piccioli, G., Fidelangeli, A., Santin, P., Vivo, P. "From Judgments to Issues: Structured Extraction of Legal Reasoning with Citation-Hallucination Control." arXiv:2607.03325, 2026. https://arxiv.org/abs/2607.03325 — verified (abstract)

[P8-67] Digital Personal Data Protection Act, 2023, s.3(c)(ii) (exclusion of personal data made publicly available by the Data Principal or by a person under a legal obligation). Text via dpdpa.com. https://www.dpdpa.com/dpdpa2023/chapter-1/section3.html — verified

[P8-68] Digital Personal Data Protection Act, 2023, s.17 (s.17(1)(a) legal-claims exemption; s.8(1), s.8(5) still apply). https://dpdpa.com/dpdpa2023/chapter-4/section17.html — verified (sibling P7-3/P9-22)

[P8-69] Vidhi Judicial. "Section 132 of the Bharatiya Sakshya Adhiniyam, 2023" (express client consent; extends to clerks/employees of advocates). https://vidhijudicial.com/section-132-of-the-bharatiya-sakshya-adhiniyam,-2023.html — verified (sibling P7-8)

[P8-70] Supreme Court Observer. "In re: Summoning Advocates who give Legal Opinion or Represent Parties during Investigation of Cases and Related Issues", 2025 INSC 1275 (31 Oct 2025; Gavai CJI, K.V. Chandran, N.V. Anjaria JJ). https://www.scobserver.in/supreme-court-observer-law-reports-scolr/re-summoning-advocates-who-give-legal-opinion-or-represent-parties-during-investigation-of-cases-and-related-issues/ — verified (re-fetched in review: s.132 scope; in-house counsel excluded; documents not shielded from production)

[P8-71] American Bar Association. "Formal Opinion 512: Generative Artificial Intelligence Tools." 29 Jul 2024 (via summaries). https://ezel.ai/ethics-opinions/aba/512-generative-ai-tools — snippet (sibling P9-15; primary PDF 403)

[P8-72] AWS. Price List API, AmazonEC2, ap-south-1 (g6e.xlarge $2.235/h). Retrieved 30 Sep 2026. https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-south-1/index.csv — verified (sibling XC-20)

[P8-73] E2E Networks. "Pricing" (L40S ₹102/h ex-GST). Retrieved 30 Sep 2026. https://www.e2enetworks.com/pricing.md — verified (sibling XC-26)

[P8-74] Digital Personal Data Protection Rules, 2025, G.S.R. 843(E), 14 Nov 2025; enforcement timeline (immediate / +12 months / +18 months for ss.3–5, 7–17 of the Act). https://dpdpa.com/dpdpa_enforcement_timeline.html ; rules PDF https://dpdpa.com/DPDP_Rules_2025_English_only.pdf — verified (timeline page; secondary host, gazette PDF not read)

