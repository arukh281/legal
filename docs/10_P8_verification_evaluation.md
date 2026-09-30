# P8 — Verification, Trust and Evaluation

**Abstract.** P8 is the platform's quality authority. It has two halves that share one data model. The first is the **Verifier**, an online service. It takes typed `Claim`s from P6 (memos, answers, drafts) and checks each one against a *legal-warrant* ladder. Does the anchor exist? Is the quote exact? Does the **cited paragraph**, and not merely the case, entail the claim? Is that paragraph the court's holding, or counsel's submission, obiter or a dissent? Is the authority good law as of the relevant date? Is it binding on this forum? Are the dates, numbers and old↔new criminal-code sections right? The output is a `VerificationReport`: a per-claim status, a calibrated confidence, a display band and a PASS / PARTIAL / BLOCK gate. The second half is the **Evaluation Platform**. It holds versioned, signed gold sets built with the design-partner firm, a metric catalogue for every phase (P0–P10), a regression-gating policy for every model, prompt, parser, index or ontology change, production audit sampling, and the Design Partner Program (consent, MoU/DPA, privilege, annotation, incentives). Four findings shape the design. (1) Commercial legal RAG tools hallucinated 17–33% of the time, and their most insidious failure was *misgrounding*: a real source that does not support the claim [P8-1]. (2) The hard verification case is not a fake case but a **wrong pinpoint**. Frontier models caught only 37–61% of wrong-pinpoint corruptions in court opinions [P8-4], and the best agentic checker reached 52.8% recall on incorrect pincites [P8-3]. (3) Citation-graph "hallucination rates" mostly measure the *coverage of the oracle*, not the model [P8-6]. (4) Indian courts have set aside orders in 2025–2026 because they rested on fabricated or misrepresented case law, including Supreme Court decisions in 2026 [P8-8]. So P8 (a) verifies at **anchor level with role and status awareness**, (b) separates *UNVERIFIABLE* (we could not check) from *UNSUPPORTED* (we checked and it fails), (c) shows **ordinal, audited confidence bands** instead of raw percentages, and (d) gates every change on *statistically powered* non-inferiority tests plus zero-tolerance sentinel suites. Target verifier cost is ≈US$0.02–0.05 per Q&A answer and ≈US$0.2–0.6 per full memo. Target latency is ≤4 s p95 for an answer and ≤20 s p95 per memo section. Both are estimates (§5.12).

---

## 1. Purpose and scope

**Purpose.** Make "every claim traces to a specific paragraph of a specific source" (brief) *true and measurable*. The platform should never show a lawyer an unverified legal proposition as verified. It should tell the lawyer how reliable each shown claim is, in terms that match measured error rates. And it should prove, before and after every change, that quality has not regressed on the slices that matter in Indian practice: Hindi and regional-language material, bad OCR, the tribunals, the IPC→BNS transition, and adverse authority.

**In scope**
1. **Online claim verification.** Check ladder C0–C12 (§5.3), status assignment, repair hints for P6, and PASS/PARTIAL/BLOCK gates.
2. **Hallucination detection** across answers, memos, drafts and **uploaded third-party documents** (opponent pleadings, lower-court orders, a firm's own drafts), exposed as the Citation Audit service (§5.8).
3. **Confidence**: a calibrated per-claim probability, conformal display thresholds, UI band semantics and the "trust ledger" (§5.6–5.7).
4. **Re-verification** when law changes (graph deltas) or when the claim text is edited (drafts).
5. **Evaluation platform**: gold-set store, eval runner, metric catalogue P0–P10, benchmark adapters (IL-TUR, LegalBench, etc.), LLM-as-judge policy, regression gates in CI/CD, shadow/canary evaluation, production audit sampling and drift detection (§5.9–5.11).
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
type AuditRequest = { request_id; tenant_id; matter_id?; pdoc_id?: string; parsed_doc_uri: string; // P1/P7 ParsedDocument
                      as_of_legal_date?: string; forum?: {...}; purpose: "OWN_DRAFT"|"OPPONENT_FILING"|"LOWER_COURT_ORDER"|"OTHER" };
```

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
| `eval.case.proposed.v1` (`EvalCaseCandidate`) | P9 | adjudication queue → gold/regression suites |
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

**O2 — `CitationAuditReport`** (P8 → P10/P6; new). For each citation mention in the audited document: `{mention_id, raw_text, anchor_id (in the audited doc), resolved_target_id?, resolution_confidence, findings: ("NOT_FOUND"|"NAME_MISMATCH"|"WRONG_PINPOINT"|"MISQUOTE"|"MISREPRESENTS"|"NEGATIVE_STATUS"|"NOT_BINDING"|"SUPERSEDED_PROVISION"|"OK"|"UNVERIFIABLE")[], evidence_anchor_ids[], note}`. It also carries a summary and a `signature`.

**O3 — Evaluation artefacts** (Postgres + object store; §5.10)
```ts
type EvalCase = {                            // superset of P9 EvalCaseCandidate
  case_id: string; gold_set_id: string; version: number; split: "DEV"|"EXAM"|"SENTINEL";
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
type EvalRun = { run_id; suite_ids[]; candidate: { component, pipeline_version, task_id?, endpoint_id? };
                 baseline_run_id; metrics: Record<string, {value, ci95:[number,number], n}>; slices: Record<string, …>;
                 sentinel_failures: string[]; started_at; finished_at; cost_usd };
type GateDecision = { gate_id; run_id; decision: "PROMOTE"|"REJECT"|"WAIVED"; rule_results[]; waiver?: {by[], reason, expires} };
```

**O4 — Events (new)**
| Event | Producer → Consumers | data (minimum) |
|---|---|---|
| `verification.completed.v1` | P8 → P9 (tenant plane), P10 telemetry | report_id, subject, per-claim {claim_id, status, band, reason_codes}, verifier_version, tenant_id |
| `eval.run.completed.v1` | P8 → Model Gateway registry, P4 (backfill decisions), CI | run_id, candidate, gate decision, summary metrics |
| `eval.case.adjudicated.v1` | P8 → P9 | candidate_id, decision ACCEPTED/REJECTED/MERGED, case_id? (closes P9's loop) |

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

---
