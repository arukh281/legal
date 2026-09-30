# 23 — Risk Register

**Abstract.** This register consolidates the risks raised across the blueprint: the eleven phase documents (02–12), cross-cutting (13), competitive teardown (20) and India-specific legal data (21). Its inputs are their §11 open questions and risks, §8 red-team findings, §8.R independent-review findings and "could not verify" lists, all read against the spine v1.0 decision record (D1–D21 in 01a_spine_decision_record.md, including the synthesis-pass rulings D19–D21; catalogues in 01_master_architecture.md §5–§9). It scores 70 risks in eight categories on a 5×5 likelihood × impact grid. It then explains the ten that matter most, lists every question that needs an Indian counsel opinion, and records the unverified assumptions the blueprint depends on, with the test that would settle each one. Nothing here is new external evidence. Every entry points back to the document section, and where relevant the source tag, that supports it; tags resolve in 24_bibliography.md. Scores are our judgement (inference), not measurements. The scoring method itself is a starting point that must be recalibrated against incidents as they happen. The register's main finding: the platform's largest risks are not model risks. They are (a) lawful, complete access to official sources, (b) the supply of qualified human reviewers who make tier-1 legal edges trustworthy, (c) errors that change a legal conclusion (authority status, deadlines, the criminal-code crosswalk, point-in-time statutes), and (d) confidentiality and privilege of tenant data. Model choice mostly appears as a medium-scored cost and quality risk, because the architecture keeps every model behind a contract and at least two qualified endpoints (D1, D14).

---

## 1. Method

### 1.1 Scope and inputs
- **In scope.** Risks to building the platform, running it, its legality, and the trust lawyers place in it, from MVP (one D2 dedicated cell for the design partner, D17) through GA (pooled D1 SaaS) to twelve months after GA.
- **Inputs.**
  - The §11, §8 and §8.R sections of documents 02–13, 20 and 21.
  - The summaries digest of all research-agent reports: top risks, open questions, "could not verify" lists and reviewer remaining issues.
  - The spine v1.0 decision record, which prevails where the documents differ.
- **Not in scope.** Generic corporate risks (fundraising, hiring market, office) unless a phase document ties them to the architecture.

### 1.2 Scoring scales
Likelihood (L) is scored *before* the listed mitigations, over the horizon in §1.1.

| L | Label | Meaning |
|---|---|---|
| 1 | Rare | <5% chance in the horizon |
| 2 | Unlikely | 5–20% |
| 3 | Possible | 20–50% |
| 4 | Likely | 50–80% |
| 5 | Almost certain | >80%, or already happening (e.g., a structural property of Indian sources) |

| I | Label | Meaning (worst credible consequence) |
|---|---|---|
| 1 | Negligible | Cosmetic; no user-visible legal error |
| 2 | Minor | Quality dip on one slice or a delayed feature, recoverable within a sprint; cost overrun <10% |
| 3 | Moderate | Errors that users see but that gates catch or the product discloses; a single-source or single-phase SLO breach lasting days; cost overrun 10–50%; slip of up to one quarter |
| 4 | Major | Wrong legal output reaching lawyers on several matters; regulatory inquiry; losing a launch court or segment; cost overrun >50%; slip of more than one quarter |
| 5 | Severe | Client harm in a live matter (missed deadline, privileged or cross-tenant exposure, reliance on overruled law); enforceable legal action; loss of the design partner; a trust event that threatens the company |

**Score** = L × I (1–25). **Bands:**
- **Critical** ≥15;
- **High** 10–14;
- **Medium** 5–9;
- **Low** ≤4.

**Residual** is the L × I we expect once the listed mitigations are live. It is written as a number, and its band follows from the thresholds above.

### 1.3 Escalation and ranking rules
1. Any risk with I = 5 and L ≥ 2 is **reviewed as Critical**, whatever its score. That means weekly review and a rehearsed contingency. A single occurrence can end the design partnership (e.g., SP-01 cross-tenant leakage, scored 10).
2. Top-10 ranking (§3) sorts by residual score, then by inherent score, then by impact.
   - When two risks tie, the one with I = 5 ranks higher.
   - Risks that share one mitigation plan are grouped under a single top-10 entry.
3. A risk whose **early-warning indicator (EWI)** trips is re-scored within 24 hours (§6.2). EWIs are wired to the observability stack (13 §7) wherever a metric already exists.

### 1.4 Owner roles
| Code | Role | Owns |
|---|---|---|
| CEO/BD | Founder / business development | MoUs, partnerships, pricing, competitive response |
| GC | General Counsel (manages external Indian counsel) | Legal opinions (§4), ToU, contracts, takedowns |
| DPO | Data Protection Officer | DPDP, CERT-In, erasure, residency attestations |
| CISO | Security lead | Tenant isolation, injection defences, incident response |
| HEAD-ACQ | Source acquisition lead (P0) | Adapters, source health, coverage ledger |
| HEAD-PARSE | Parsing lead (P1) | OCR, segmentation, citation and identity resolution, anchors |
| HEAD-SEARCH | Index and retrieval lead (P2, P5) | Embeddings, indexes, ranking, stance, summaries |
| HEAD-KG | Knowledge-graph and doctrine lead (P3, 21 rule registry) | Assertions, AuthorityView, doctrine rules, crosswalk model |
| EDITOR | Legal editorial lead | Tier-1 HITL editors, crosswalk review, reviewer roster |
| HEAD-PLATFORM | Platform/SRE lead (P4, bus, DR) | Propagation, campaigns, capacity, DR |
| HEAD-REASON | Reasoning lead (P6) | Agents, memo pipeline |
| LEGAL-ENG | Legal-engineering lead (P6 RuleSpecs) | Procedural rules, deadline engine, court calendars |
| HEAD-WORKSPACE | Workspace lead (P7) | Matter layer, court sync, erasure mechanics |
| HEAD-EVAL | Trust and evaluation lead (P8) | Verification, gold sets, calibration, release gates |
| HEAD-ML | ML platform and learning lead (Model Gateway, P9) | Model qualification, routing, feedback loop, Privacy Gate |
| HEAD-PRODUCT | Product lead (P10) | UX, alerts, adoption, public API surface (D13) |
| DPP-MGR | Design-partner programme manager | Partner hours, consent paperwork, second and third partners |
| FINOPS | Finance / FinOps | Cost model, unit economics |

### 1.5 Conventions
- **Evidence column.**
  - `NN §x(n)` = document `docs/NN_*.md`, section x, item n.
  - `Dn` / `Dn.m` = spine v1.0 decision n (item m), D1–D21 (01a_spine_decision_record.md). Deployment names D1–D4h (D17) appear only in risk text, never in the Evidence column.
  - Section numbers were re-checked against the documents after the D19–D21 conformance edits (spot-check of the top-20 risks by residual); the fixes are in the rows themselves.
  - `[XX-n]` = a source tag from that document's reference list. Its confidence grade (verified, snippet or unverified) carries over unchanged.
- **Milestones.**
  - **W1**, **M1** = week 1 and month 1 of the MVP build;
  - **MVP-live** = the partner's D2 cell in use;
  - **GA** = D1 opens (22's M3; the deployment menu D1–D4h is published then, v1.0 D19.10);
  - the PLC Access API/MCP (D13) ships only after M2 coverage (D19.10).

  These milestones must be aligned with 22_build_roadmap.md.
- **Lifecycle.** A risk is in one of five states:
  - **Open**: identified, no mitigation live;
  - **Mitigating**: controls are being built;
  - **Accepted**: the residual risk is signed off by its owner and by GC or CEO;
  - **Closed**: the cause has been removed;
  - **Realised**: the risk has become an incident, which opens a post-mortem and a re-score.
- **Novelty.** The scoring grid, the EWIs and the residual estimates are **[NOVEL — unvalidated]** judgements. Recalibrate them after the first two quarterly reviews against the incidents actually observed.

---

## 2. Register

Columns follow the brief:
- ID, Risk, Category, Phase(s), L, I, Score;
- EWI (early-warning indicators);
- Mitigations, Contingency;
- Owner role, Residual;
- Evidence.

The category appears in the Cat column and as the ID prefix:
- T = Technical;
- DA = Data-access;
- LR = Legal/regulatory;
- SP = Security/privacy;
- MV = Model/vendor;
- BC = Business/competitive;
- OP = Operational/people;
- ET = Evaluation/trust.

### 2.1 Technical (T)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-01 | VLM OCR hallucinates critical tokens (digits, citations, party names, dates) in degraded scans. Result: wrong anchors and false support | T | P1, P8 | 4 | 4 | 16 | Dual-reader disagreement rate; share of critical tokens flagged uncertain; anchor `text_hash` churn after re-OCR; P8 UNSUPPORTED spike where `ocr_conf`<0.85 | Dual-reader consensus, third read on disagreement; L0 docs quarantined if header or operative order is affected; claims on low-`ocr_conf` anchors capped at PARTIAL; IC-OCR-Bench-driven routing | Re-OCR queue with a better VLM; page-image highlighting; `pg{n}` locator anchors never support tier-1 claims | HEAD-PARSE | 6 | 03 §3, §8, §11; 13 §10 F3; 20 §8.1 R2; D16 |
| T-02 | False merges in citation or Work identity resolution corrupt treatment history | T | P1, P3, P4 | 3 | 4 | 12 | Audited false-merge rate >0.1%; `identity.split.v1` volume; alias-conflict freezes (e.g., AIR without volume numbers) | Keys first; match ≥0.97 with a 0.2 margin; STUB works; a conflict freezes the merge; T0 court-issued aliases are never overridden by third-party ones | `identity.split.v1`, then a P4 recompute campaign; retract affected impacts | HEAD-PARSE | 6 | 03 §11; 21 §3.4, §10.2; D16 |
| T-03 | Ratio/obiter and opinion-role (majority/dissent) mislabelling puts wrong propositions into tier-1 treatment | T | P1, P3, P5 | 4 | 3 | 12 | Partner κ on ratio <0.6; HITL rejection rate of propositions; opinion-segmentation errors | Labels are candidates with calibrated confidence; HITL on tier-1; the UI never shows P1 labels as definitive; opinion roles come only from the court copy (EBC ¶41) | P3 moves to a proposition model that does not depend on a ratio/obiter binary | HEAD-KG | 6 | 03 §11(6); 07 §8.R; 21 §2.2 [IN-3] |
| T-04 | Point-in-time statute text is wrong: the law as on date D is misstated. India Code documents no point-in-time versions, so history is rebuilt from gazette amendments | T | P0, P1, P3, P5, P8 | 4 | 4 | 16 | Round-trip verification failures; share of tier-1 Acts with UNVERIFIED expressions; lawyer flags on a statute version | Official consolidated text is the anchor; reconstructed text is `derived=true`; only official or ROUNDTRIP_OK text backs tier-1 claims; HITL on tier-1 Acts first; territory-aware keys | Restrict point-in-time answers to verified Acts; "reconstructed" badge; ask the user for the date | HEAD-KG | 8 | 03 §11(8); 02 §11(5) [P0-36]; D16 |
| T-05 | Anchor churn on re-parse or model swap breaks tenant claims, memos and matter dependencies | T | P1, P2, P4, P7, P8 | 3 | 4 | 12 | Canary set shows >0.5% anchor change; tombstone and alias rates; P8 UNVERIFIABLE on stored claims | Alignment protocol with aliases and tombstones; anchors never reused; release gate at 0.5%; durable records store anchors, never `chunk_id`s | Roll back the parser; backfill aliases; REVERIFY affected memos | HEAD-PARSE | 4 | 03 §11; 09 §11(11); D8 |
| T-06 | Impact propagation to a live matter is missed or late (outbox loss, DLQ, partial fan-out) | T | P3, P4, P7 | 3 | 5 | 15 | Reconciler re-emit count; `propagation_frontier` lag; DLQ depth; time-travel drill recall <95% | Outbox and inbox; ledger stages; reconciler every 15 min; a stuck document holds back the frontier, so "law current to" visibly lags; P3 emits a `graph.delta.v1` for every `doc.parsed.v1`; every impact_tier-1 impact takes the real-time lane without tenant knowledge (D19.4) | Manual re-propagation campaign; notify tenants with the lag stated | HEAD-PLATFORM | 6 | 06 §11, top risks; 13 §6.2; D3, D4, D19.4 |
| T-07 | Prospective, conditional or moulded legal effect is given the wrong scope (prospective overruling, MADA-type moulding) | T | P3, P4, P5, P6 | 3 | 4 | 12 | Share of impacts with `temporal_scope` UNCERTAIN; FLAG_WRONG_TREATMENT on scope | `temporal_scope` on every impact; UNCERTAIN plus a request for dates; `effect`/`effective_from` under HITL; `effect=MOULDED` with conditions | Turn off automatic scoping; route to an editor | HEAD-KG | 6 | 06 §11(1) [P4-39]; 21 §10.4 C4 [IN-26] |
| T-08 | At 10M–20M docs, binding or adverse authority drops out of a crowded top-k; filtered-ANN recall and index heap degrade | T | P2, P5 | 3 | 4 | 12 | Per-leg recall monitors at each 2× growth; BAR/AAR regressions; p95 search latency | BIND leg with precomputed `binding_scope_tags`; graph legs independent of corpus size; binary/int8 quantisation; sharding by court and decade | Hot/cold tiers; drop dense vectors for short orders | HEAD-SEARCH | 6 | 07 §8, top risks; 13 §10 F2; 04 §11(2–3) |
| T-09 | Indic-language gap: OCR, treatment cues, retrieval and NLI are weaker on Hindi and regional text. Machine translation (MT) may be quoted as if authoritative | T | P1, P2, P3, P5, P8 | 4 | 4 | 16 | Per-language slice metrics; non-English share of tier-1 queue; Hindi cue coverage; claims anchored to MT | Anchors on original-language text; MT is never an Expression and fails P8; Hindi cue lexicon built with partner reviewers; ≥10–20% non-English gold; bilingual reviewers | Force PENDING_REVIEW on non-English tier-1 items; publish language coverage per court | HEAD-KG, HEAD-EVAL | 9 | 03 §11(2); 04 §11(8); 10 §11(2); 20 §8.1 R3; 13 §10 F4, F18; D16 |
| T-10 | Criminal crosswalk or which-code error (IPC→BNS etc.; the "482" collision; 124A→152 treated as the same offence). Worse if no official correspondence table is found | T | P3, P5, P6, P8 | 3 | 5 | 15 | Which-code accuracy <97% on gold; AMBIGUOUS_ACT rate; crosswalk rows still PENDING | Tier-1 HITL on every mapping by two editors; `REPLACED_BY_DIFFERENT_OFFENCE` blocks precedent carry; UNDETERMINED when proceeding dates are unknown; P8 check | Hold GA of the criminal module until 100% of mappings are reviewed | HEAD-KG, EDITOR | 6 | 21 §6, §10.3, §10.5 Q6; 05 §11(2) |
| T-11 | A wrong procedural RuleSpec gives a systematically wrong deadline or limitation across tenants | T | P6, P7, P10 | 3 | 5 | 15 | Golden-test failures; lawyers overriding computed deadlines; P4 flags on amended anchors | Two-person legal review; golden tests; canary rollout; anchors on every deadline; no activation without verified anchors; per-rule kill switch | Kill switch, plus DEADLINE correction alerts to every affected matter | LEGAL-ENG | 8 | 08 §11(1), §11(8), top risks |

### 2.2 Data-access (DA)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DA-01 | Core official portals are CAPTCHA-gated with no public bulk API (the NJDG Open API is government-only), and an MoU is uncertain. Result: HC/tribunal coverage and freshness gaps | DA | P0, P3, P7 | 4 | 4 | 16 | `coverage_estimate` per source; reconciliation-ledger gaps; IK-only share; `freshness_lag_p95` | CC-BY bulk backfill; official HC-site deltas; IK gap-fill; MoU track from day 1; human-assisted targeted capture after counsel sign-off; never circumvent | Publish a per-court coverage matrix; COVERAGE_GAP reason codes; launch on fewer courts | HEAD-ACQ, CEO/BD | 9 | 02 §11(1), §11(3), top risks [P0-5][P0-12]; 21 §2.3 |
| DA-02 | Geo/WAF blocking of our egress (Akamai 403s on sci.gov.in and India Code); Indian cloud ASNs may also be blocked | DA | P0 | 3 | 4 | 12 | 403 rate by egress ASN; W1 probe result | India-region static egress; Indian colo fallback (budgeted); whitelisting requests; never evade | Colo/ISP egress; partner-contributed documents | HEAD-ACQ | 6 | 02 §11(4) |
| DA-03 | Indian Kanoon dependency: ToU allow termination on 1 month's notice; rights to keep IK text after termination are unclear | DA | P0, P1 | 3 | 3 | 9 | IK-only share >5%; ToU changes | Gap-fill and reconciliation only; IK-only Works capped below 5% by month 12; IK text under a purgeable LICENSED_THIRD_PARTY prefix; provenance-upgrade queue | Purge IK-only text; re-acquire from primary sources | HEAD-ACQ | 4 | 02 §11(7), §11(11) [P0-15]; 21 §2.4 |
| DA-04 | Open CC-BY SC/HC dumps stall, change licence or turn out to carry derivative taint | DA | P0 | 3 | 3 | 9 | Dump cadence (SC bi-monthly, HC quarterly); licence-file changes | Bootstrap only; deltas come from primary sources; attribution in `terms_ref`; provenance kept per `raw_id` | Content-addressed purge by source; re-acquire from primary | HEAD-ACQ | 4 | 13 §10 F20; 02 §11(1) [P0-2][P0-4] |
| DA-05 | HC neutral-citation formats vary and drift; five HCs' formats are unobserved | DA | P0, P1 | 4 | 2 | 8 | Volume of the unknown-code review queue; recall per HC format | Format table kept as data; per-HC notifications; T1 alias learning; conflicts freeze merges | Route unknown codes to review | HEAD-PARSE | 4 | 21 §3.2, §10.5 Q5; 20 §8.1 R12 |
| DA-06 | Court calendars and cause-list timings cannot be obtained reliably for every HC and district court. Deadlines and court-day alerts degrade | DA | P0, P6, P10 | 3 | 4 | 12 | CourtCalendar coverage by court; deadlines missing a calendar basis | CourtCalendar feed (D16); lawyer-confirmed trigger dates; calendar basis shown on each deadline | Mark deadlines PROPOSED; show the earliest date | LEGAL-ENG | 6 | 08 §11; 12 §11(4); D16 |
| DA-07 | A judgment is pronounced but its text is not uploaded for hours or days, so an overruling from yesterday is invisible to every check | DA | P0, P3, P4, P8 | 5 | 3 | 15 | Age of `judgment.expected.v1` with no `raw.captured.v1`; gap between cause list and capture | `judgment.expected.v1` (`jex_`) makes P3 ask P1 to mint an EXPECTED stub Work (D20.4), plus a PROVISIONAL "text awaited" impact for larger benches and for precedents named in `referenced_authorities[]` (D21.18), on the real-time lane (D19.4); third-party reports set CAUTION only; watermark disclosure | Editorial fast track once the official copy appears | HEAD-ACQ | 9 | 13 §10 F19; 10 §8.R; D16, D19.4, D20.4, D21.18 |
| DA-08 | Court sync gives a wrong or stale hearing date, or misses an order (portal change, bad OCR of a served date) | DA | P0, P7, P10 | 3 | 5 | 15 | SYNC_STALE counts; weekly missed-alert audit against eCourts; rate of disagreement between sources | Multi-source observations with `observed_at`; cause-list cross-check; lawyer-confirmed dates; every date shows its source | SYNC_STALE alerts; manual path | HEAD-WORKSPACE | 8 | 09 §11(7), top risks; 12 §11(10) |
| DA-09 | Silent source-template drift or format change degrades metadata and structure | DA | P0, P1 | 4 | 3 | 12 | Volume anomalies; drift in fill rate, label distribution and quarantine rate; `structure_conf` drop | WARC-fixture CI; drift monitors pause emission; canaries per source; parser versioning | `reprocess.requested.v1`; gap shown in `Freshness.known_gaps` | HEAD-ACQ | 6 | 13 §10 F1; 02 top risks; 03 §11 |

### 2.3 Legal/regulatory (LR)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LR-01 | Access legality: the IT Act s.43 posture (MeitY, Feb 2025), portal ToU and human-assisted CAPTCHA capture; our corpus provenance is challenged | LR | P0 | 3 | 5 | 15 | Legal notice; government statement; portal blocks; ToU revisions | Never circumvent (`rul_IN_ACCESS_1`); legal gate as code; archived ToU and robots; per-source kill switch; counsel opinion before Tier A (LO-01, LO-02) | Kill switch; content-addressed purge by source | GC | 8 | 02 §11(1); 21 §2.3 [IN-63]; 13 §10 F16 |
| LR-02 | Copyright: bare-Act export under s.52(1)(q)(ii); reporter paragraphing, headnotes or opinion labels leaking in (EBC v. Modak ¶41–42); reporter-pinpoint resolution | LR | P0, P1, P2, P10, D13 | 3 | 4 | 12 | Provenance-filter hits; reporter-derived text detected; shape of API exports | Statutes always shipped with original matter; reporter-derived text banned; anchors from court numbering only; quote-anchoring for pinpoints (LO-04, LO-08) | Withdraw the export; purge by provenance | GC | 4 | 21 §2.1–2.2 [IN-1][IN-3]; 20 §8.R; 04 §11(5) |
| LR-03 | Masking, RTBF and victim-identity non-compliance: derived copies linger after a court order or statutory bar (*Laksh Vir Singh Yadav*; BNS s.72). Also abuse through forged masking orders | LR | P0–P5, P10 | 3 | 4 | 12 | Overlay-ack lag; masking-gate recall <99.5%; volume of takedown requests | `doc.redacted.v1` + RedactionOverlay (01 §7.13) with a `redaction.applied.v1` ack from every consumer and replica, joined in P0's redaction ledger with `purge_sla` breach alarms (D19.3, D20.3); P2 purge in 1 h (search) and 24 h (all artefacts); upload-time masking gate; `access_restriction`; activation only from orders fetched from an official source | Emergency SUPPRESS_ALL; disclose residual exposure in replicas | GC, DPO | 6 | 21 §2.5, §10.2 [IN-55]; 13 §5.9, §10 F21; 04 top risks; D16, D19.3, D20.3 |
| LR-04 | DPDP status of court-published personal data is unresolved (s.3(c)(ii), limb B) | LR | P0–P5, P8, P9 | 3 | 4 | 12 | Data Protection Board guidance; notifications; complaints | Treat PLC judgments as personal data (masking, takedown); PUBLIC tasks default to ZDR endpoints; opinion LO-09 | Move PLC tasks to in-India endpoints; tighten handling of eval data | DPO | 6 | 13 §11 Q3 [XC-42]; 21 §9 [IN-58] |
| LR-05 | Privilege: whether vendor staff and processors fall inside BSA s.132(3); lawful demands served on the platform; in-house counsel not covered (2025 INSC 1275) | LR | P7, P8, P9 | 3 | 5 | 15 | A police or court demand; objections in tenant procurement | No standing operator access; break-glass only with firm approval; per-matter keys; BYOK/HYOK; `privilege_basis` by tenant type; opinion LO-11 | D3/D4 for sensitive firms; disclosure limited to the matter | GC, CISO | 8 | 09 §11(1); 21 §9, Q3 [XC-43][P7-8][IN-62] |
| LR-06 | DPDP for private data: advisory and transactional matters may fall outside s.17(1)(a), and eval/training use of client data is probably not covered | LR | P7, P8, P9 | 3 | 3 | 9 | Counsel view; Board rulings | Partner agreement designed not to need the exemption; lawyer-authored restatements; Privacy Gate; notice and consent features ready for either reading | Switch off the affected eval/training flows | DPO | 4 | 09 §11(2); 10 §5.13, §11(10) [P8-68][IN-57] |
| LR-07 | BCI conduct rules (advertising, solicitation, confidentiality) are engaged by client-facing digests, judge pages, outcome sharing or naming the partner | LR | P8, P9, P10 | 2 | 3 | 6 | BCI circulars; concerns from the partner's GC | No public advocate ranking; outcome data stays inside the tenant; judge pages list-only; opinion LO-16 before these features | Withdraw the feature | GC | 3 | 21 §9, Q10; 12 §11(7), §11(11); 10 §11(6) |
| LR-08 | Professional-reliance liability: a lawyer relies on a wrong memo or deadline; "Verified" is read as a guarantee; a published trust ledger is read as a warranty | LR | P6, P8, P10 | 3 | 4 | 12 | Complaints; output that reached a filing; Indian orders on fake citations | Ordinal strength only; appendix stating "verified = supported by sources"; tier-1 confirmation; contracts say "measured performance" (LO-17) | Incident review; notification; service credit | GC | 6 | 08 §11(4), §11(8); 10 §11(7); 20 §8.1 R5 [CT-56] |
| LR-09 | Compliance deadlines missed: DPDP-core controls by 12 May 2027 (Rule 4 from 12 Nov 2026); CERT-In 6-hour reporting and 180-day in-India logs | LR | XC, P7, all | 2 | 4 | 8 | Programme burndown against the dates; log-retention audit | Logs pinned to India; 6-hour incident runbook; DPDP-core controls scheduled before May 2027 | External compliance support | DPO | 4 | 21 §9 [IN-59]; 13 §5.8 [XC-36][XC-38] |
| LR-10 | Licence exposure from components and data: restricted OCR weights (Surya), unchecked open-weight LLM licences, reporter or third-party citation tables, IK metadata, competitor outputs used in eval | LR | P1, P2, P3, P8, XC | 3 | 2 | 6 | Gaps in the procurement register | Apache-licensed defaults; clearance before use (LO-06, LO-07, LO-21); citation strings taken only from judgments | Swap the component; purge seeded aliases | GC | 3 | 03 §11(5), top risks; 05 §11(6); 13 could-not-verify |
| LR-11 | Unsettled doctrine answered with false confidence: SC obiter weight, stayed HC judgments, reach of an HC strike-down (including interim stays), HC binding on all-India tribunals, straddling offences | LR | P3, P4, P5, P6 | 4 | 3 | 12 | Lawyers dispute `binding_on_forum`; how often contested rules are invoked | `contested=true` DoctrineRules return both views; UNDETERMINED or CAUTION; partner panel approves rule changes; DOCTRINE_CHANGE campaigns run in shadow first (LO-19) | Revert the rule version; consolidated reclassification impacts | HEAD-KG | 6 | 05 §11(1); 21 §4, §10.5 Q4, Q9; 06 §11(2–3) |

### 2.4 Security/privacy (SP)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SP-01 | Cross-tenant or cross-wall leakage via caches, indexes, autocomplete, alerts, logs, query text, firm memory or LLM context | SP | P2, P5, P7, P9, XC | 2 | 5 | 10 | Honeytoken canary hit; output scanner finds a foreign `pdoc` ID; RLS/authz test failures | Per-tenant stores, indexes, caches and keys; OpenFGA deny-first walls plus FORCE RLS; TEC token; no cross-tenant semantic cache; no query-text logging; scoped memory | Sev-1 incident; tenant notice; CERT-In report; key rotation | CISO | 5 | 09 top risks; 13 §5.5, F7; 07 top risks; 11 top risks; D9 |
| SP-02 | Indirect prompt injection through opponent filings, emails or scraped PDFs steers decomposition, suppresses adverse authority or exfiltrates data | SP | P1, P5, P6, P7 | 4 | 4 | 16 | Hidden-text flags; red-team CI pass rate; P8 unsupported-claim spike; adverse section missing items P5 found | Hidden-text and Unicode detection; `trust_label` typing, so only PLC_OFFICIAL, TENANT_WORK_PRODUCT and USER_INPUT steer control flow; plan-then-execute; tool-less, schema-bound extraction; adverse coverage computed by P5; P8 block; red-team corpus of 500+ documents | Quarantine the document; re-run the memo without it | CISO, HEAD-REASON | 8 | 13 §5.4, F6 [XC-33][XC-34]; 20 §8.1 R6; 08 top risks; 09 top risks; D9 |
| SP-03 | Privacy Gate leak: matter terms or strategy can be inferred from S0/S1/S2 releases, including re-identification by timing in a small market | SP | P9, P3 | 2 | 5 | 10 | Matter-term lint hits; red-team findings; queries on the tenant ledger | No free text; public-ID allowlist; 72 h delay on S1; S2 only as aggregates with k≥5 and DP noise; ledger visible to tenants; red-team before the second S1 tenant | Halt releases; purge by proposal lineage | HEAD-ML, DPO | 4 | 11 §11(5), §11(7), top risks |
| SP-04 | Residency violation: a mislabelled endpoint or cross-border processing (including WhatsApp or push) for IN_ONLY tenants | SP | XC, P6, P10 | 2 | 4 | 8 | Per-call geography mismatch (e.g., `inference_geo`); registry change without two-person approval | Fail-closed routing; two-person registry changes; per-call geography check; zero-tolerance SLO with a kill switch; WhatsApp content MINIMAL, and off for IN_ONLY | Kill switch; contractual notice | HEAD-ML | 3 | 13 §10 F8 [XC-2]; 12 top risks; D15 |
| SP-05 | Access-pattern side channel: PLC reads reveal which authorities a tenant relies on | SP | P4, P5, P7 | 2 | 4 | 8 | Tenant-attributable IDs in PLC logs | Stateless PLC read path (D2 cells read the shared PLC this way); tenant-redacted telemetry; whole-manifest downloads; mandatory local PLC replica for D3/D4/D4h (D19.7) | Purge logs; move the tenant to a replica | CISO | 3 | 06 §11, §8.R; 13 §7.4; D3, D19.7 |
| SP-06 | Incomplete erasure (embeddings, backups, caches, P9 items), or erasure that collides with a legal hold | SP | P2, P7, P9 | 3 | 3 | 9 | Failures in the erasure verification sweep; exceptions on erasure certificates | Lineage-based erasure; crypto-shredding of matter DEKs; index compaction plus sweep; legal-hold check on every delete path; every consumer of `erasure.requested.v1` (P2, P5 caches, P6 memory, P8, P9) acks with `erasure.applied.v1` and only P7 emits `erasure.completed.v1` (D20.15, D21.3) | Manual purge; disclosure | DPO | 4 | 09 §11(3), top risks; D20.15, D21.3 |
| SP-07 | Tampered or malicious source files: MITM on government sites with broken TLS chains; malware or hidden text in PDFs | SP | P0, P1 | 2 | 4 | 8 | TLS fingerprint changes; canary hash mismatches on historical docs; malware flags | AIA chasing plus pinned intermediates; TLS verification never disabled; TLS fingerprint in the WARC; sandboxed parsers | Quarantine the source; re-verify from another copy | HEAD-ACQ | 3 | 02 top risks; D16 |
| SP-08 | Feedback poisoning or mass mis-flagging corrupts the KG or rankers | SP | P9, P3, P5 | 3 | 3 | 9 | Outlier actors; honeypot failures; FLAG_BAD_LAW spikes | Proposals never write directly; tier-1 HITL; caps per actor and per tenant; reliability weighting; anomaly holds | Purge by `proposal_ids` lineage; retrain | HEAD-ML | 4 | 11 top risks; 13 §10 F11; 05 top risks |

### 2.5 Model/vendor (MV)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MV-01 | No in-India Claude processing: IN_ONLY tenants get a different, possibly weaker, model mix, and the gap is unmeasured | MV | P6, P8, XC | 4 | 3 | 12 | Per-residency P8 quality scores; P6 gate failures on in-India endpoints | ≥2 qualified in-India endpoints per P6 role (Bedrock `in.` GPT-5.6, Azure southindia, self-hosted Sarvam/Qwen); per-residency scores published | Reduced mode; D4h | HEAD-ML | 6 | 13 §4.4, §11 Q2 [XC-2][XC-6][XC-7][XC-8][XC-12]; D15 |
| MV-02 | Cheap models fail on Indian treatment classification, so escalations rise and the build moves toward mid-tier cost (≈$110–142K at 5M) | MV | P3, XC | 3 | 3 | 9 | Cascade gate fails: cheap model <95% of premium macro-F1, or ECE >0.05 | Cascade gate on P8 gold; distil premium and HITL labels into self-hosted models | Raise the escalation share; re-budget | HEAD-ML | 6 | 13 §3.5, §11 Q5; D14 |
| MV-03 | Provider price shocks, model retirements, silent drift behind aliases (e.g., Gemini price step on 1 Jan 2027; retirement of a judge model) | MV | XC, P8 | 4 | 2 | 8 | Cost dashboard; weekly canary-replay deltas; deprecation notices | ≥2 qualified endpoints per task; snapshot pinning; the router re-optimises; self-hosted checker | Roll back; recalibrate judges | HEAD-ML | 4 | 13 §10 F9–F10 [XC-4]; 10 §11(8) |
| MV-04 | The default embedder or reranker underperforms on Indian legal data (MLEB has no Indian data; rerankers can regress legal ranking) | MV | P2, P5 | 3 | 3 | 9 | Bake-off on IL-PCSR, IL-PCR and partner gold; per-slice eval against no-rerank | Three-way bake-off decided on hybrid Recall@100; lexical retrieval first-class; per-slice rerank gate; a swap costs a few thousand USD | Swap the index generation; turn off rerank on failing slices | HEAD-SEARCH | 4 | 04 §11(1) [P2-3]; 07 top risks |
| MV-05 | Fallback services lack India-region zero-retention processing or are unavailable (Document AI, Sarvam API, Cohere/Voyage rerank; managed Kafka/Temporal in India) | MV | P1, P4, P5, XC | 3 | 2 | 6 | Vendor confirmations still pending | Benchmark-only use on tenant data until confirmed; self-hosted equivalents; self-managed KRaft/Temporal | Self-host | HEAD-PLATFORM | 3 | 03 §11(3); 07 §11(7); 06 §11(8–9) |
| MV-06 | On-prem (D4) open-weight models fail the P6 T1 gate; 8×H100-class sizing and support load | MV | P6, P7, XC | 3 | 3 | 9 | P8 gate results for self-hosted T1; on-prem support tickets | MVP is D2 only; reduced on-prem mode; D4h option; premium pricing | Limit D4 to deadlines and research | HEAD-PLATFORM | 6 | 08 §11(6); 09 §11(6); 13 §9, top risks; D17 |

### 2.6 Business/competitive (BC)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BC-01 | SCC Online or Manupatra forms an India content alliance with Harvey, as LexisNexis did | BC | All | 4 | 4 | 16 | Joint announcements; Harvey hiring for Indian content | Lead with matter propagation (M4) and the partner flywheel (M5); offer the PLC API/MCP to assistants first; lock in the partner's litigation practice | Reposition as a verification and authority API | CEO/BD | 12 | 20 §6.4 S1 [CT-34][CT-26][CT-27] |
| BC-02 | Incumbents turn editorial treatment notes into machine-readable signals within 9–18 months, eroding M2 | BC | P3 | 3 | 4 | 12 | "Overruled/distinguished" signals appear in competitor UIs | Move fast on tier-1 edges in the partner's practice areas; proposition-level, as-of-date status; publish the benchmark | Compete on M4 plus verification | CEO/BD, HEAD-KG | 9 | 20 §6.2–6.4 [CT-4] |
| BC-03 | Foundation-model assistants plus open Indian data become "good enough" for small firms | BC | P10 | 4 | 2 | 8 | Assistants cite IK or eSCR natively | Skip the solo segment at launch; sell a verification/status API | — | CEO/BD | 6 | 20 §6.4 S3 [CT-39] |
| BC-04 | The MVP cuts the treatment graph or the matter loop and ships a Bharat.Law/Prism clone | BC | All | 3 | 5 | 15 | Scope cuts to P3 tier-1 or to the impact path (P4 broadcast → P7 Impact Matcher, D3) | Competitive minimums (20 §7.2) are hard gates in the roadmap (22) | Re-plan the release | CEO/BD | 5 | 20 §7.2, top risks |
| BC-05 | Unit economics break: serving is ≈78% of monthly cost (≈$60K of ≈$77K at S-5M; figures of record, D19.1), seat usage is unvalidated, and flat seat pricing meets deep agentic runs | BC | P5, P6, P10, XC | 3 | 3 | 9 | $/seat telemetry; deep runs per seat | Per-request budgets (`max_cost_usd`, `max_input_tokens`); pooled firm quota of deep runs; caching; routing | Repricing; usage caps | FINOPS | 6 | 13 §3.4, §11 Q9; 20 §8.2; D18, D19.1 |
| BC-06 | Moat leakage through our PLC API: competitors harvest AuthorityStatus and verified edges | BC | D13, P10 | 3 | 3 | 9 | A canary assertion shows up elsewhere; quota anomalies | Quotas; canary assertions; terms banning training and redistribution; responses carry reason predicates, not proposition text; launch only after M2 coverage | Throttle; terminate the key | HEAD-PRODUCT | 4 | 20 §8.1 R8 |
| BC-07 | Single design partner: bias, capacity limits or exit | BC | P8, P9 | 3 | 4 | 12 | Annotation hours below plan; renewal signals | Second and third partners by months 9–12; exit terms keep our D0/D1 licence | Paid annotators; supervised students | DPP-MGR | 8 | 10 §5.13, top risks; 20 §6.2 M5 |
| BC-08 | Firms refuse S0/S1 consent, starving the global learning loop | BC | P9 | 3 | 3 | 9 | Consent rate at onboarding | Explicit schemas and a sample ledger; visible resolution feedback; partner consents first | Rely on gold and LLM-judge labels | HEAD-ML | 6 | 11 top risks |
| BC-09 | Adoption friction: HITL confirmations, a blocked Word add-in, long flows; on-prem demands distort the roadmap | BC | P6, P7, P10 | 3 | 3 | 9 | Abandonment at date confirmation; add-in install failures | Confirmations that do not block the rest of the memo; optional issue gate; sideload path and .docx re-import; MVP is D2 only | Simplify flows | HEAD-PRODUCT | 6 | 08 top risks; 12 top risks; 09 top risks |

### 2.7 Operational/people (OP)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OP-01 | Not enough tier-1 HITL editors, or they miss SLAs (≈100–300 items/day; 4-hour SLA on SC; few reviewers who read Hindi) | OP | P3, P4, P9 | 4 | 4 | 16 | Queue age p95; SLA breaches in big-judgment weeks; non-English backlog | Signal first (CAUTION shown at once); priority by severity × exposure × uncertainty; roster of 3–5 editors; tier 3 auto-applied | Surge contract editors; narrow the scope | EDITOR | 9 | 05 §11(5), top risks; 11 §11(4); 13 §11 Q4 |
| OP-02 | Partner lawyer time is too short for gold and calibration (≈3,000–3,500 h in Year 1; ≈3k treatment + 1k status labels; ≈1,500 graded issues) | OP | P3, P5, P8 | 4 | 4 | 16 | Hours/week against the 15-hour target; label throughput; κ | Supervised NLU students do the first pass; perturbation factory; pooled, conservative thresholds; paid hours; more partners | More "Check this" outputs; report machine-only metrics honestly | DPP-MGR, HEAD-EVAL | 9 | 10 §11(1), top risks; 05 §11(3); 07 §11(3) |
| OP-03 | Adapter maintenance (~100 adapters, 1.5–2 FTE) outruns the team, and silent breakage erodes freshness | OP | P0 | 4 | 3 | 12 | MTTR; adapters in DEGRADED state; freshness SLO misses | WARC-fixture CI; canaries; calendar-aware yield models; fixture-gated LLM repair; MTTR SLO | Prioritise HOT sources; drop COOL ones | HEAD-ACQ | 6 | 02 §11(10), top risks [P0-25] |
| OP-04 | Legal-engineering capacity and ownership for 300+ RuleSpecs and their upkeep as law is amended | OP | P6, P3 | 3 | 4 | 12 | Rule backlog; rules waiting on unverified anchors | Registry with named owners; activation gated on verified anchors | Launch only with verified rules | LEGAL-ENG | 8 | 08 §11(8) |
| OP-05 | A reprocess campaign overruns its budget, regresses the graph or starves the real-time lane | OP | P4, P1–P3 | 3 | 3 | 9 | Campaign spend against its cap; real-time lane degraded by >10% | Frozen ID lists; minimality filter; shadow runs with an impact dry run; P8 gate; hard cost cap; separate lanes; bitemporal rollback | Abort and roll back | HEAD-PLATFORM | 4 | 06 top risks; 13 §10 F14 |
| OP-06 | An India-wide cloud or network event impairs both Mumbai and Hyderabad | OP | XC | 1 | 5 | 5 | External synthetic probes | Offline read-only PLC snapshot for D2–D4; status page | Degraded read-only service | HEAD-PLATFORM | 4 | 13 §8, F15 |
| OP-07 | A mass law-change wave (new codes, Income-tax Act 2025, a doctrine revision) needs large, synchronised updates to rules, crosswalk and status | OP | P3, P4, P6 | 3 | 4 | 12 | Gazette signals; commencement notifications | Precomputed campaigns for planned waves; storm mode; crosswalk review budget (≈540 reviewer-hours for the criminal codes) | Prioritise by matter exposure; UNDETERMINED by default | HEAD-KG | 8 | 06 §8, top risks; 08 §8.R; 21 §10.2 |

### 2.8 Evaluation/trust (ET)

| ID | Risk | Cat | Phase(s) | L | I | Score | Early-warning indicators | Mitigations | Contingency | Owner | Res. | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ET-01 | False red flags or false severity-1 "overruled" alerts (a pending reference, an SLP dismissal, a cue from a smaller bench) destroy trust | ET | P3, P4, P10 | 3 | 5 | 15 | Retraction rate; false-red-flag rate >1%; severity-1 precision <90% | Four-condition gate for severity 1; bench-competence check; rul 05/09/10; retraction ≤30 min p95; target <1 false severity-1 per quarter | Retraction reaches every channel; circuit breaker per method version | HEAD-KG | 6 | 06 top risks; 21 §10.3, top risks; D5, D6 |
| ET-02 | An overruling is missed or late (feed lag, misresolved citation, non-English judgment), so "Verified" appears on bad law | ET | P0, P3, P5, P8 | 3 | 5 | 15 | Time-travel drill recall; freshness SLO misses; negatives found late | Immediate CAUTION on any plausible negative; `COVERAGE_GAP` reason code with `definitive=false`, and GOOD degrades to UNKNOWN past the per-source threshold (D20.12); every tier-1 impact on the real-time lane (D19.4); `graph_watermark` chips; `/revalidate` before the P8 gate; re-check at export | REVERIFY via P4→P7→P6; alert affected matters | HEAD-KG, HEAD-EVAL | 8 | 05 top risks; 07 top risks; 10 top risks; 13 §6.2, §10 F1, F5; D6, D19.4, D20.12 |
| ET-03 | Published trust numbers fail in production: the false-verify rate exceeds the displayed band after distribution shift, or gold contamination leads to Goodharting | ET | P8 | 3 | 4 | 12 | Breach in the weekly PPI audit; canary strings in outputs | Weekly stratified audit; thresholds tighten automatically; recalibration on every model or parser change; sealed EXAM split; quarterly rotation; ZDR-only eval endpoints | Downgrade display bands; publish a correction | HEAD-EVAL | 6 | 10 §11(4), top risks; 20 §8.1 R11 |
| ET-04 | Wrong-pinpoint and role errors go undetected (frontier models miss 39–63% on the hard variant) | ET | P8 | 4 | 3 | 12 | `wrong_pinpoint_hard` recall on the perturbation suite | Anchor-level entailment; C3b re-anchoring; role check; checker fine-tuned on Indian hard negatives; perturbation recall is gated | Withhold, or downgrade to PARTIAL | HEAD-EVAL | 8 | 10 §11(3) [P8-4] |
| ET-05 | Over-trust and automation bias: lawyers rubber-stamp a strategy, act on provisional alerts, or read ordinal strength as calibrated probability | ET | P6, P10 | 3 | 4 | 12 | Action taken before verification (UX telemetry); override rates | Ordinal strength with the decisive facts; no definitive styling before VERIFIED; tier-1 confirmation; uncertainty phrasing tested with users | UX changes; training | HEAD-PRODUCT | 8 | 08 §11(3), top risks; 13 §10 F12; 12 §11(1) [P10-10] |
| ET-06 | Adverse authority is suppressed, through stance-model errors or through feedback that learns to hide unfavourable cases | ET | P5, P9 | 3 | 4 | 12 | Adverse recall (AAR) regressions; rank shifts driven by engagement | Pinned binding and adverse slots; stance-stratified objectives; perspective-flip checks; adverse-recall release guardrail; P8 blocks memos missing adverse items P5 found | Revert the ranker | HEAD-SEARCH | 6 | 07 top risks; 11 top risks; 20 §8.1 R6 |
| ET-07 | Over-blocking makes memos vacuous, and lawyers abandon the tool | ET | P6, P8 | 3 | 3 | 9 | Withheld and BLOCK rates; informativeness | Gates on withheld rates; `narrowed_text` and C3b repair turn failures into PARTIAL | Loosen thresholds within the audited bands | HEAD-EVAL | 6 | 10 top risks |
| ET-08 | LLM summaries and digests introduce plausible but wrong content, including via injected documents | ET | P2, P10 | 3 | 3 | 9 | NLI failure rate; partner audit of a 1% sample | Anchored sentences; NLI plus exact checks; extraction-only prompts; summaries are never citable; audit of 1% plus all constitution-bench judgments | Pull summaries; headline-only digest | HEAD-SEARCH | 4 | 04 top risks; D9 |
| ET-09 | Alert fatigue or storms after a landmark judgment or a commencement, so lawyers miss the critical alert | ET | P4, P10 | 4 | 3 | 12 | Alerts per user per day; ack rates; storm-mode activations | Only severity 1 interrupts; coalescing; storm mode; interrupt budget; per-rule demotion on low precision | Digest-only mode | HEAD-PRODUCT | 6 | 06 top risks; 12 top risks; 05 §11(9) |

**Register summary.** 70 risks.
- **Inherent bands:** 18 Critical, 26 High, 26 Medium, 0 Low.
- **Residual bands:** 0 Critical, 1 High (BC-01), 47 Medium, 22 Low.
- **Inherent Critical risks (score ≥15), by category:**
  - Technical (6): T-01, T-04, T-06, T-09, T-10, T-11.
  - Data-access (3): DA-01, DA-07, DA-08.
  - Legal/regulatory (2): LR-01, LR-05.
  - Security/privacy (1): SP-02.
  - Business/competitive (2): BC-01, BC-04.
  - Operational/people (2): OP-01, OP-02.
  - Evaluation/trust (2): ET-01, ET-02.
- **Escalated under rule 1.3(1)** (I = 5, L ≥ 2, score <15): SP-01 and SP-03 are reviewed as Critical. OP-06 (L = 1) is not escalated.
- **Residual profile.** Planned mitigation brings every risk below Critical. The only residual High is BC-01, which is competitive and outside our control. Next come five risks at residual 9: capacity (OP-01, OP-02), coverage (DA-01, DA-07) and the Indic gap (T-09). A sixth, BC-02, is also at 9.

---

## 3. Top-10 risks

Ranking follows §1.3 rule 2. Each entry names a lead ID and the linked IDs that share its mitigation plan.

### 3.1 Moat erosion: BC-01 (with BC-02, BC-04). Residual 12
**Why it ranks first.**
- Harvey is deployed firm-wide at two tier-1 Indian firms [CT-26][CT-27], and LexisNexis has already bundled a citator into Harvey [CT-34].
- General models score close to specialists on legal research: all products fell within 74–78% on VLAIR [CT-39]. The model is therefore not a moat (20 §6.1).
- The teardown estimates our lead at 18–30 months, falling to about 12 if an incumbent–workspace alliance forms (20 §6.3).
- We cannot prevent that alliance. We can only make it matter less.

**Plan.**
1. Make the 20 §7.2 competitive minimums hard MVP release gates in 22:
   - typed negative treatment with tier-1 HITL in the partner's practice areas;
   - claim-level verification;
   - per-issue adverse coverage;
   - one end-to-end SC/HC decision → `impact.detected.v1` → `matter.alert.v1` loop;
   - the benchmark harness.
2. Win the partner's litigation practice before any alliance lands.
3. Sequence the D13 PLC API only after M2 coverage passes the partner's practice areas (20 §8.R, remaining-open item 5; ruled as v1.0 D19.10).
4. Re-check the watch list quarterly (20 §7.4).

**KRIs.** Verified tier-1 edges in partner practice areas; matters under live propagation; watch-list events.

**Acceptance.** The residual is accepted by CEO/BD. The contingency is to reposition as a verification and authority API.

### 3.2 Official-source access and its legality: DA-01 + LR-01 (with DA-02, DA-07)
**Why.** Everything downstream depends on lawful, measurable coverage: freshness, the clean provenance claimed as moat M1, and adverse-authority recall.
- The core portals are CAPTCHA-gated [P0-5].
- The NJDG API is government-only [P0-12].
- The government's IT Act s.43 stance on scraping is disputed [IN-63].
- The CC-BY bulk datasets were themselves built from gated portals and a mobile API [P0-2].

**Plan.**
- **W1:** test egress from Indian cloud ASNs against the Akamai-fronted sites.
- **Before Tier A launch, and before the CC-BY backfill is treated as more than bootstrap:** obtain LO-01 and LO-02.
- Run the MoU track from day 1 as business development, never as an engineering dependency.
- Surface the reconciliation ledger in `Freshness.known_gaps` and in a per-court coverage matrix.
- Cap IK-only Works below 5%.
- Keep per-source kill switches.
- **Launch scope** = the courts whose coverage has been measured, not a document count (20 §8.1 R1).

**KRIs.** `coverage_estimate` per court; IK-only share; `freshness_lag_p95`; legal-gate status per source.

### 3.3 Human review capacity: OP-01 + OP-02 (with BC-07, OP-04)
**Why.** The durable moat is a verified-edge ledger that "grows with reviewer-hours and time" (20 §6.2 M2), plus partner gold (M5). The plan needs, all as unmeasured estimates (U-08, U-09):
- 3–5 editors handling ≈100–300 tier-1 items a day, with a 4-hour SLA on SC items (05);
- ≈3,000–3,500 partner lawyer-hours in Year 1 (10);
- ≈540 reviewer-hours for the crosswalk (21 §10.2);
- 5k+ reviewer-hours for the P1 backfill (03).

**Plan.**
- **Before the gold build:** sign the Design Partnership Agreement with an hours commitment (10 §5.13).
- **M1–M2:** run a 4-week pilot queue that measures throughput, κ and cost.
- Prioritise queues by severity × exposure × uncertainty.
- Show signals first, so an SLA breach delays certainty, not the warning (05 §11(5)).
- Use supervised students and paid hours.
- Recruit Hindi-reading editors.
- **Months 9–12:** sign second and third partner firms.

**Acceptance.** A long tail of `definitive=false` statuses is accepted.

### 3.4 Indic-language gap: T-09
**Why.**
- District-court orders in regional languages are the norm in case files (21 §8).
- Public OCR leaderboards contain no Indian court pages (03 §4).
- No Indian legal NLI benchmark exists (10 §11(2)).
- The P3 and P5 cue lexicons are English-only.
- When a Hindi HC judgment distinguishes a precedent and we miss it, the adverse authority is missed (20 §8.1 R3).

**Plan.**
- **Before OCR routing is frozen:** build IC-OCR-Bench with Indic strata.
- Keep ≥10–20% non-English items in the gold sets, with a Hindi share of 15% in G-QA.
- Author the Hindi cue lexicon with partner reviewers.
- Force PENDING_REVIEW, with a bilingual reviewer, on every non-English tier-1 item.
- MT stays a rendition, never an Expression (D16).
- Publish per-court language coverage and per-language scores.

**KRIs.** Per-language slice metrics; non-English backlog.

### 3.5 Privilege and tenant confidentiality: LR-05 + SP-01 (with SP-03, LR-06)
**Why.**
- BSA s.132 covers the "clerks or employees of advocates" [P7-8][XC-43]. Whether it covers vendor staff is untested.
- In-house counsel are outside s.132 [IN-62].
- A single cross-tenant leak is catastrophic (13 §10 F7).

**Plan.**
- **Before the GA contract template:** obtain LO-11.
- No standing operator access; break-glass only with firm approval.
- Per-matter DEKs and BYOK/HYOK; `privilege_basis` set by tenant type.
- **From MVP-live:** honeytoken canary tenants and an output scanner for foreign IDs.
- The partner runs in a dedicated D2 cell (D17).
- Red-team the Privacy Gate before a second S1 tenant (11 §11(7); recommended in the P9 review).

**KRIs.**
- Canary hits (target 0);
- break-glass events;
- matter-term lint hits.

### 3.6 Authority-status errors in both directions: ET-01 + ET-02 (with DA-07, LR-11)
**Why.** The citator signal is the product's core trust claim. Both failure directions hurt: false red flags from pending references, SLP dismissals or cues from smaller benches (21), and missed or late overrulings. Status is never fresher than P0/P3, and a pronounced judgment is invisible until its text is uploaded (10 §8.R).

**Plan.**
- Severity 1 only when all four conditions of D5 hold, plus the bench-competence check.
- Asymmetric display (D6): CAUTION immediately, definitive only after HITL.
- Retraction ≤30 min p95.
- `graph_watermark` chips, and `/revalidate` before the P8 gate.
- `judgment.expected.v1` for larger-bench pronouncements.
- Quarterly time-travel drills, target recall ≥95%.
- The false-red-flag rate (<1%) is tracked separately from the missed-negative rate (21 §10.3).

**KRIs.**
- Severity-1 precision ≥90%;
- fewer than 1 false severity-1 per quarter (06).

### 3.7 Deadlines and court dates: T-11 + DA-08 + DA-06 (with OP-04)
**Why.**
- One wrong hearing date damages trust more than any AI error (12 §11(10)).
- A wrong RuleSpec is systematic across tenants and is rated critical (08).
- Several procedural anchors are still unverified (08 §11(1)).

**Plan.**
- No RuleSpec is activated without verified anchors.
- Two-person legal review, golden tests, canary rollout and a per-rule kill switch.
- Lawyers confirm trigger dates before a deadline becomes CONFIRMED.
- Every date shows its source and `observed_at`.
- Weekly missed-alert audit against eCourts.
- CourtCalendar coverage per court.
- LO-17 for liability framing.

**KRIs.** Deadline overrides; audit misses; SYNC_STALE rate.

### 3.8 Prompt injection through adversarial documents: SP-02
**Why.** The core workflow ingests documents written by the other side. Injection-resistant design patterns reduce the attack surface but do not remove it [XC-33][XC-34].

**Plan.**
- Layered controls in 13 §5.4, with `trust_label` control-flow typing (D9).
- Adverse coverage is computed by P5, not by the generating model, and P8 blocks memos that omit what P5 found (20 §8.1 R6).
- A red-team corpus of 500+ documents gates every P5/P6 prompt or model change in CI.
- Hidden-text detection must be committed in P1 and P7, which the 08 §8.R review flagged as a dependency.

**KRIs.**
- Red-team pass rate;
- hidden-text flags;
- spikes in unsupported claims.

### 3.9 Point-in-time statutes: T-04
**Why.**
- "What the law was on the cause-of-action date" is an explicit client requirement.
- India Code documents no historical versions [P0-36], so history is rebuilt from gazette amendments.
- Art. 254(2) makes some text vary by territory (21 §10.4 C3).

**Plan.**
- **M1:** confirm whether any official history exists (U-13).
- Official consolidated text is the anchor, with round-trip verification.
- Reconstructed text is `derived=true`. Only official or ROUNDTRIP_OK text may back tier-1 claims (D16).
- Tier-1 Acts go through HITL first.
- The UI shows a "reconstructed" badge and asks for the date.

**KRI.** Share of tier-1 Acts whose versions are verified.

### 3.10 Criminal crosswalk and which-code logic: T-10 (with OP-07)
**Why.**
- This is a differentiator.
- An error means a wrong remedy or a missed limitation period.
- No official section-level correspondence table has been located, and the example mappings are unverified (21 §8.R; 05 §8.R).

**Plan.**
- Fetch the BPR&D/NCRB tables from Indian egress and diff them against our text alignment.
- Two editors review the ≈1,000 old-code sections (≈540 hours).
- AMBIGUOUS_ACT flag, and `governing_code()` applied per proceeding stage (D16).
- Criminal-module GA is gated on 100% reviewed coverage and which-code accuracy ≥97% (21 §10.3).

**Next five.** These ranked just below the top ten; they are reviewed monthly and escalate if an EWI trips:
- T-01 OCR hallucination;
- T-06 missed propagation;
- LR-03 masking and RTBF;
- MV-01 in-India model gap;
- OP-03 adapter maintenance.

---

## 4. Legal opinions required

This table consolidates every item that the source documents mark as needing a counsel opinion, a legal opinion, written confirmation, legal sign-off or legal clearance.
- The positions in the phase documents are **design intent, not legal advice**.
- Until an opinion arrives, the conservative design default stays in force. The "Default until answered" column records it.
- **Owner of every row: GC.** The DPO co-owns LO-09 to LO-14.
- "Needed by" uses the milestones in §1.5.

| ID | Question for Indian counsel | Why it matters | Blocks (phases / features) | Default until answered | Needed by | Sources |
|---|---|---|---|---|---|---|
| LO-01 | Is low-volume HUMAN_ASSISTED capture, where an operator solves the CAPTCHA personally in an audited console, consistent with the eCourts, SCR and NCLT ToU and with IT Act s.43? | This is the only lawful-looking route to gated documents that a matter needs | P0 access mode 5 (sign-off per source); P7 manual court-sync path; `acquire.requested.v1` MATTER_WATCH | Mode disabled | Before Tier A launch | 02 §5, §11(1); 21 §2.3 [IN-63] |
| LO-02 | Does using the CC-BY AWS SC/HC datasets carry derivative risk, given they were built from CAPTCHA-gated portals and a mobile API? | These datasets are the MVP backfill | P0 bootstrap; everything downstream of the backfill | Use for bootstrap, provenance-tagged and purgeable | Before relying on the backfill beyond bootstrap (M1) | 02 §11(1) [P0-2]; 13 §10 F20 |
| LO-03 | Are SCR official headnotes reproducible under s.52(1)(q)(iv), or are they separate government works needing permission? | Headnotes are high-value summaries | P1/P2 ingestion of headnotes; P10 display | Not ingested | Before any headnote feature | 02 §11(1) |
| LO-04 | s.52(1)(q)(ii): does reproducing an Act require accompanying commentary or original matter for every display, bulk export or API response? | Statute text is a core product surface | P10 bare-Act downloads; D13 statute API; P5 statute snippets in exports | Statutes always shipped with our annotations; exports limited to snippets | Before GA downloads or a public statute API | 02 §11(2); 21 §2.1, §10.5 Q1 [IN-1] |
| LO-05 | May we use Bills (outside s.52(1)(q)) and cause lists (as facts only), and use news-RSS feeds as SIGNAL_ONLY under their ToU? | These feed legislative tracking and `judgment.expected.v1` | P0 Bills adapter; P0 pronouncement watch; P4 PROVISIONAL impacts | Signals only; no text reproduced | Before the Bills and news adapters | 02 §11(12) |
| LO-06 | Indian Kanoon: (a) may IK "Equivalent citations" metadata seed our alias tables (trust tier T3)? (b) may IK-sourced text be kept after the ToU terminate? | IK is the gap-fill path | P1 alias seeding; P0 retention and purge | (a) cross-check only; (b) IK text kept in a purgeable prefix | Before T3 seeding; before month-12 IK share review | 21 §2.4, §10.5 Q2; 02 §11(11) [P0-15] |
| LO-07 | May third-party or commercial citation tables (reporter equivalents, the SC Equivalent Citation Table) seed aliases? May licensed citator outputs be used in comparative evaluation? | Alias recall; competitive benchmarking | P1 identity resolution; P3/P8 comparative eval | Only citation strings found in judgments; no comparisons | Before seeding or publishing comparisons | 03 §11(5); 05 §11(6) |
| LO-08 | *EBC v. Modak*: can we resolve a user's reporter pinpoint ("SCC para 41") to our court-numbered anchor per mention, without storing a reporter's paragraph map? | Lawyers cite reporter paragraphs every day | P1 pinpoint resolution; P10 citation go-to; P8 audit of user drafts | Quote-anchoring only; UI says "reporter para; official para unresolved" | Before Word cite-check GA | 20 §8.R; 04 §11(5); 21 §2.2 [IN-3] |
| LO-09 | DPDP s.3(c)(ii): is a court "under an obligation under any law" to publish judgments, so that court-published personal data falls outside DPDP? | It decides PLC processing on global endpoints, and eval data built from judgments | XC routing of PUBLIC data; P8 eval-data class; P9; masking duties | Treat PLC judgments as personal data; ZDR endpoints | Before GA; in any case before 12 May 2027 | 13 §11 Q3 [XC-42]; 21 §9 [IN-58]; 10 §11(6c); 11 §11(2) |
| LO-10 | Are we an "intermediary" (IT Act s.2(1)(w)) for PLC content, directly bound by Rule 3(1)(d) masking and de-indexing directions? What is the verified statutory list of identity-suppression duties (BNS s.72; POCSO s.23 and JJ Act s.74, both unverified) and the required purge SLA? | *Laksh Vir Singh Yadav* binds "other hosts"; compliance within two weeks | P0–P5, P10 masking; P1 `needs_masking` gate; P2 purge SLO | Comply as if bound; 1 h / 24 h purge; 2-week SLA | Verified memo before GA (13 §11 Q12) | 21 §2.5, §10.5 Q8 [IN-55]; 04 §11(6); 03 §11(9) |
| LO-11 | BSA s.132(3): are SaaS vendor staff or processors within "clerks or employees of advocates"? Does a vendor annotation tool running inside the tenant plane keep protection intact? | It sets the default deployment, break-glass policy and contract language | P7 D1 vs D2/D3 default; P8 partner-programme annotation design; contracts | No standing operator access; per-matter keys | Before the GA contract template | 09 §11(1); 21 §9, §10.5 Q3; 10 §11(6b) [XC-43][P7-8][IN-62] |
| LO-12 | DPDP s.17(1)(a): does it cover advisory and transactional matters? Can it ever cover evaluation or training use of client personal data? | The firms' obligations from 12 May 2027 and our processor terms depend on it | P7 notice, consent and rights features; P8 partner programme; P9 training | Design needs no exemption; lawyer restatements; Privacy Gate | Before 12 May 2027 | 09 §11(2); 10 §5.13 [P8-68]; 21 §9 [IN-57] |
| LO-13 | DPDP Rules mechanics, checked against the gazette text: Rule 8 erasure (48-hour intimation; classes covered), Rule 6 log period, Rule 7 72-hour breach report, and the number of the cross-border rule | Secondary sources only so far | P7 erasure workflow; XC breach runbook | Follow the stricter secondary reading | Before 12 May 2027 | 09 §11(3), §8.R; 21 §9 [IN-59] |
| LO-14 | Before DPDP commencement, do IT Act s.43A and the SPDI Rules 2011 govern sensitive personal data in case files? | Controls may need attesting now | P7 security attestations | Controls designed to satisfy either regime | Before MVP-live contract | 09 §11(12) |
| LO-15 | BSA s.63 Schedule: what hash requirements apply to electronic-evidence certificates? | A certificate helper and procedural rule depend on it | P7 hash-report template; P6 BSA certificate RuleSpec | Rule not activated | Before the feature | 09 §11(4); 08 §11(1) |
| LO-16 | BCI conduct rules: (a) advertising and solicitation, for firm-branded client digests, judge pages, outcome sharing, advocate discovery; (b) co-authorship, case studies, naming the partner; (c) confidentiality and outsourcing, including whether clients such as PSUs or banks must consent to S0/S1 releases | Features could expose tenants to conduct complaints | P10 full client digests and judge pages; P8 public benchmark with the partner; P9 S0/S1 beyond the partner | Features off; outcome data stays inside the tenant | Before each feature | 21 §9, §10.5 Q10; 12 §11(6–7), §11(11); 10 §11(6a); 11 §11(1) |
| LO-17 | Professional-responsibility posture and liability: disclaimers for AI strategy memos; who is liable for a wrong RuleSpec; whether a published trust ledger creates warranty exposure | Memos and deadlines are relied on in live matters | P6 GA; P8 public trust ledger; customer contracts | "Measured performance, not guarantee" wording; tier-1 confirmation | Before P6 GA | 08 §11(4), §11(8); 10 §11(7) |
| LO-18 | Does Indian law (BCI Rules or case law) impose a duty of candour to disclose adverse authority, as US ABA MR 3.3(a)(2) does (unverified)? | Product framing of adverse sections | P5/P6 copy only | Adverse authority always surfaced anyway | Before marketing copy | 07 §11(1) |
| LO-19 | Doctrine panel (counsel plus partner lawyers), not a single opinion. Topics: SC obiter weight for HCs; precedential effect of stayed HC judgments; territorial reach of an HC strike-down of a central Act, including interim stays (*Kusum Ingots*); which HC binds all-India tribunals; HC-declared prospective overruling; straddling offences and BNSS s.531 for pending investigations; which language prevails between an OLA s.7 Hindi judgment and its English translation; binding succession after HC reorganisation; the substantive-vs-procedural temporal split | These settle `contested` DoctrineRules | P3 `authority-core`; P4 contested CROSSWALK impacts; P6 automation of the temporal split | `contested=true`; UNDETERMINED/CAUTION; both views shown | Rolling; partner panel approves each rule change | 05 §11(1); 21 §10.5 Q4, Q9; 06 §11(2–3); 08 §11(2); 07 §8.R |
| LO-20 | s.52(1)(r): may machine translations of Acts be shown to users where no Government translation is on sale? | Hindi and regional statute display | P2/P10 statute MT display | MT used internally only; official text displayed | Before an Indic statute view | 21 §2.1(4) |
| LO-21 | Licence clearance for OCR model weights (e.g., Surya's restricted weights licence) and open-weight LLMs (Llama, Mistral, DeepSeek, BharatGen) used commercially or on-prem | Self-hosting is central to residency and D4 | P1 OCR routing; XC self-hosted models; D4 bundles | Apache-2.0 components only (e.g., Sarvam-105B [XC-12]) | Before each component is promoted | 03 §11, top risks; 13 could-not-verify |
| LO-22 | Channel regulation: TRAI DLT registration and sender-ID rules for SMS fallback; WhatsApp template policy for legal alerts; client forwarding of digests (consent, privilege waiver) | Severity-1 delivery and client-facing surfaces | P10 SMS/WhatsApp; client digests | SMS off; MINIMAL WhatsApp; no client forwarding | Before those channels are enabled | 12 §11(2–3), §11(6) |

**Packaging.** Group LO-01 to LO-22 into five counsel briefs so external counsel can be engaged efficiently:
- **A. Access and copyright:** LO-01 to LO-08 and LO-20.
- **B. Data protection:** LO-09, LO-10 and LO-12 to LO-14.
- **C. Privilege and professional conduct:** LO-11 and LO-15 to LO-18.
- **D. Doctrine panel:** LO-19, standing and rolling.
- **E. Licensing and channels:** LO-21 and LO-22.

Briefs A, B and C sit on the MVP critical path.

---

## 5. Unverified assumptions the blueprint depends on

Each row names the assumption, what breaks if it is false, how it stands today, the test that settles it, when that test runs, and its owner. Results feed back into the risk scores (§6.2).

| ID | Assumption | Depends on it | Status today | Resolving test | When | Owner |
|---|---|---|---|---|---|---|
| U-01 | **Corpus shape**: tokens/doc, pages/doc, OCR share (≈30% assumed in P1), citations/doc, Indic share, tokenizer inflation (λ_lang) | Every cost, capacity and HITL figure; D18, D19.1 | Estimates (13 §2.2, §11 Q1, Q11; 03 §11(1)) | Stratified 10K-document sample owned by P1 and measured in M0 (D19.8); rebase the cost model, whose formulas are linear in T and C | W1–W2 (M0; 22 §3.2 item 6, DP-2) | HEAD-PARSE, FINOPS |
| U-02 | **Cost shape** (figures of record, D19.1): build ≈$90K at 5M docs (cascade); monthly ≈$77K (5M) and ≈$89K (20M) at 2,000 seats; ≈$0.105 per verified Q&A; ≈$2.16 per memo; FX ₹88/$ | Budget, pricing, D14 | Planning estimates (D18, D19.1; 13 §3.3–§3.4). **Reconciled by D19.1:** 13 is the canonical cost model; the uncorrected ≈$0.086/≈$1.66 are list-price lower bounds only; 08's ≈$2.7 per memo (placeholder prices, excluding P5/P8) is a sensitivity upper bound | Rebase after U-01; replace usage assumptions with telemetry | W2, then MVP-live + 90 days | FINOPS |
| U-03 | **Seat usage**: 200 Q&A and 4 memos per seat-month, driving ≈78% of monthly cost at S-5M (D19.1; 13 §11 Q9) | BC-05, pricing | Assumption (13 §11 Q9) | P10 telemetry from partner use | First 90 days of MVP-live | HEAD-PRODUCT |
| U-04 | **Volumes and base rates**: ≈6.5–10k docs/day; SC/HC daily counts from one ambiguous secondary source [P0-14]; tribunal and gazette volumes; citation mentions per judgment; prevalence of negative treatment | Capacity for P0–P4; HITL staffing | Estimates; capacity sized at 3× meanwhile (02 §11(13); 05 §11(4)) | Measured counts per source; P3 base rates from the 10K sample | M1 / sprint 1 | HEAD-ACQ, HEAD-KG |
| U-05 | **OCR accuracy on Indian court pages**, per script. Sarvam's figures are self-reported; PaddleOCR-VL's per-script accuracy is unreported; Chitrapathak's licence is unclear; prevalence of legacy-font text layers is unknown | T-01, T-09; P1 routing and cost | No Indian court OCR benchmark exists (03 §11(2)) | IC-OCR-Bench: ≈2,000 court and gazette pages stratified by court, script and scan quality, with critical-token metrics | Before OCR routing is frozen for the backfill (M1–M2) | HEAD-PARSE |
| U-06 | **Embedder and reranker**: the Qwen3-Embedding-4B default wins on Indian data; the reranker helps on every slice; short orders (~70% of Works) need dense vectors | MV-04, T-08; P2/P5 sizing | MLEB has no Indian data [P2-3]; IL-PCSR shows dense retrieval weak on precedents (04 §3) | Three-way bake-off on IL-PCSR, IL-PCR and partner gold (hybrid Recall@100); per-slice gate against no-rerank; IN-Ret-Gold test for short orders | Before the first index generation is promoted | HEAD-SEARCH |
| U-07 | **Cheap-model adequacy** for Indian treatment classification: ≥95% of premium macro-F1, ECE ≤0.05; premium slice ≈5–12% | MV-02; build cost; D14 | Cascade literature is general; not verified for India (13 §3.5) | Cascade gate on P8 gold | Before the backfill enrichment run | HEAD-ML |
| U-08 | **Reviewer economics**: $700 per reviewer-month; 7,000 reviews/month; 100–300 tier-1 items/day; 3–5 editors; P1 backfill needs 5k+ reviewer-hours | OP-01; budget | Assumptions (13 §11 Q4; 05; 03) | 4-week pilot queue measuring throughput, agreement and cost | M1–M2 | EDITOR |
| U-09 | **Partner capacity and agreement**: ~15 lawyer-hours/week (3,000–3,500 h in Year 1); ratio κ ≥0.6; stance κ measurable | OP-02, T-03, ET-06 | Unmeasured (10 §11(1); 03 §11(6); 07 §11(4)) | Signed partnership agreement with hours; pilot annotation sprint measuring hours and κ | Before the MVP gold build | DPP-MGR |
| U-10 | **GPU throughput and sizing**: Qwen3-4B at 5–10k tok/s per L4; small checker ≳100 pairs/s per L40S; rerank ≈0.25 H100-GPU-s per query; D4 at 8×H100 class | Latency SLOs; D4 pricing | Planning figures (04, 07, 10, 13) | Load tests on the target instances | M2 | HEAD-PLATFORM |
| U-11 | **In-India model quality**: the gap between IN_ONLY and ANY routes on P6 roles | MV-01 | Unmeasured (13 §11 Q2) | P8 per-residency eval on P6 tasks | Before the first IN_ONLY tenant | HEAD-ML |
| U-12 | **DPDP applicability**: s.3(c)(ii) for judgments; s.17(1)(a) scope | LR-04, LR-06; routing of PUBLIC data | Arguable (21 §9) | LO-09, LO-12 | Before GA; controls before 12 May 2027 | DPO |
| U-13 | **Source availability**: Akamai-fronted sites accept Indian cloud ASNs; India Code has no point-in-time history; NJDG API stays government-only; MoU timeline; formats of the 5 unobserved HC neutral citations; per-court calendars obtainable; dump cadence | DA-01 to DA-06, T-04 | Partly verified (02 §11; 21 §10.5) | W1 egress probes; source onboarding profiles; HC notifications; MoU outreach log | W1 (egress); M1–M3 (the rest) | HEAD-ACQ |
| U-14 | **Official crosswalk tables** (BPR&D/NCRB) exist and can be used; example rows (e.g., IPC 420→BNS 318) are correct | T-10 | Not located; fetch failed (21 §10.5 Q6; 05 §11(2)) | Fetch from Indian egress; diff against our text alignment; two-editor review | Before criminal-module GA | EDITOR |
| U-15 | **Freshness SLOs are achievable**: HOT p95 ≤30 min; SC judgment → CAUTION ≤6 h; SC hard negative definitive ≤4 business hours; impact → alert ≤15 min | ET-02, DA-07 | Unvalidated targets (02; 05; 06; 21 §10.3) | Month-1 measurement; quarterly time-travel drills (recall ≥95%) | M1, then quarterly | HEAD-PLATFORM |
| U-16 | **Prospective scope can be extracted**: `effect`/`effective_from`, date basis, scope predicates | T-07 | Unmeasured (06 §11(1)) | Labelled extraction set from known prospective rulings | Before automatic `temporal_scope` | HEAD-KG |
| U-17 | **Thresholds**: P8 α (0.5% VT1, 2% VT2); merge 0.97; masking 0.2; anchor churn 0.5%; severity weights; 6-hour coalescing; k≥5 and ε for S2 | P1, P4, P8, P9 gates | Planning values in every document | Calibrate on the sealed G-Claim EXAM split and partner data; formal privacy analysis for k and ε | MVP → GA | HEAD-EVAL, HEAD-ML |
| U-18 | **Authoritative language**: SC vernacular versions state the English text governs; the OLA s.7 route for Hindi HC judgments | T-09, ET-02 | Unverified (13 §10 F18; 04 §8.R) | Per-court check of translation notices | M1–M2 | HEAD-PARSE |
| U-19 | **Deployment demand**: large firms accept India-region SaaS; D4 is a niche | MV-06, BC-09 | Indirect evidence only: top firms adopted a US SaaS vendor [CT-26][CT-27] (21 §9) | Interviews with the partner and the first 10 prospects | Before investing in D3/D4 | CEO/BD |
| U-20 | **UX transfer**: uncertainty wording (evidence from US/medical settings [P10-10]); acceptance of mandatory date confirmation; Indic MT good enough for Hindi drafts; value of model-family heterogeneity | ET-05, BC-09 | Evidence is neither Indian nor legal (12 §11(1); 08 §11(5), §11(7), §11(9)) | A/B tests with the partner | MVP months 2–4 | HEAD-PRODUCT, HEAD-REASON |
| U-21 | **Traffic** is enough for IPS learning-to-rank and interleaving | P9 ranking roadmap | Estimated 12–18 months away (11 §11(3)) | Traffic monitoring; the roadmap must not depend on it | Quarterly | HEAD-ML |
| U-22 | **Peripheral prices and eligibility**: IndiaAI subsidised compute; WhatsApp India utility rate; managed Kafka/Temporal prices in India | BC-05, MV-05 | Unverified (13 §11 Q7; 12 §11(2); 06 §11(8)) | Vendor and regulator enquiries | Before GA | FINOPS |
| U-23 | **Real-time lane share without tenant knowledge**: admitting every impact_tier-1 impact plus impacts above a public citation-footprint threshold keeps the real-time lane at ≤15% of the daily delta [NOVEL — unvalidated threshold] | OP-05, BC-05; batch discount; alert SLOs | Ruled as policy (D19.4); share unmeasured (13 §6.2, §11 Q15) | Measure the real-time share on the M1 slice and tune `rt_footprint_min_indegree`; the unattributed union watch-list is post-GA only | M1–M2 | HEAD-PLATFORM, FINOPS |

**Order of resolution.**
1. U-01, U-04 and U-13: the week-1 and month-1 measurements.
2. U-05, U-06, U-07 and U-08: the gating benchmarks and pilots.
3. U-09: partner capacity.

Only these first tests materially re-base the risk scores. Everything else refines individual risks.

---

## 6. Review cadence and triggers

### 6.1 Cadence
| Cadence | Forum | Scope | Output |
|---|---|---|---|
| Weekly | Risk triage: phase leads plus CISO and EDITOR | Top 10; the "next five"; risks reviewed as Critical under §1.3(1); any tripped EWI | Updated status; actions with owners |
| Every release | P8 release gate (D11) | Risks linked to the changed components (e.g., model swap → MV-03, ET-03, T-05) | Risk sign-off recorded with the GateDecision |
| Monthly | Steering: CEO, GC, DPO, CISO, heads | Full register; §4 opinion tracker; §5 assumption tracker | Re-scored register; new, closed and accepted risks |
| Quarterly | Deep review | Re-score all risks against observed incidents; recalibrate the grid (§1.5); competitive watch list (20 §7.4); time-travel and DR drills; Privacy Gate red-team | Published register version (changelog); lessons learned |
| Annually | Board / external audit | Accepted residuals; compliance programme (DPDP, CERT-In, ISO 27001/SOC 2 roadmap in 13 §5.8) | Attestation |

### 6.2 Event triggers: re-score within the stated time
| Trigger | Re-score | Within |
|---|---|---|
| Honeytoken hit; residency geography mismatch; any Privacy Gate lint breach | SP-01, SP-04, SP-03 (Sev-1 incident first) | Immediately; CERT-In clock if applicable (6 h) |
| False severity-1 alert, retraction, or a drill missing a known impact | ET-01, ET-02, T-06 | 24 h |
| Counsel opinion received (any LO) | All linked risks; update the legal-gate config | 1 week |
| Court order or government direction affecting hosts (masking/RTBF, scraping); a DPDP milestone (12 Nov 2026, 12 May 2027) | LR-01, LR-03, LR-04, LR-09 | 1 week |
| Source DOWN or BLOCKED for more than 24 h; a ToU change (including IK); a dump licence change | DA-01 to DA-04, LR-01 | 48 h |
| Commencement notification, constitution-bench judgment, or doctrine rule change | OP-07, T-10, LR-11, ET-09 | 48 h |
| Provider price or model change; a new in-India endpoint (e.g., in-India Claude processing) | MV-01, MV-03, BC-05 | 1 week |
| A §5 measurement lands (U-01 to U-09) | Cost-, capacity- and quality-driven risks | 2 weeks |
| Each 2× growth of the corpus; first D3 or D4 tenant; first IN_ONLY tenant | T-08, MV-06, MV-01, SP-05 | Before go-live |
| Competitor event on the watch list; design-partner renewal; second partner signed; before the D13 public API; before the second S1 tenant | BC-01 to BC-08, SP-03 | 2 weeks, or before go-live |

### 6.3 Governance
- The register is versioned alongside the blueprint.
- Every EWI must map to an observability metric (13 §7) or a named manual audit. An EWI with no data source counts as a defect of the register.
- Accepting a residual of 10 or above needs CEO and GC sign-off.
- A risk can be closed only with evidence: a test result, an opinion, or a removed dependency.

---

## References

This register introduces **no new external sources**. It cites the phase documents by section, and the spine v1.0 decisions as D1–D21 (01a_spine_decision_record.md). Bracketed tags belong to the originating documents' reference lists, keep their confidence grades, and resolve in 24_bibliography.md. The tags cited here are:
- **[P0-2]** Dattam Labs, indian-high-court-judgments dataset docs — verified.
- **[P0-4]** bharat-courts 0.3.1, PyPI — verified.
- **[P0-5]** eCourts Judgment Search Portal (Securimage CAPTCHA) — verified.
- **[P0-12]** Drishti IAS, NJDG Open API (secondary) — verified.
- **[P0-14]** GKToday, NJDG disposals 2024 (secondary; ambiguous) — verified.
- **[P0-15]** Indian Kanoon API ToU — verified.
- **[P0-25]** Free Law Project, juriscraper — verified.
- **[P0-36]** IALS, India Code resource description — verified.
- **[P2-3]** Butler et al., MLEB, arXiv:2510.19365 — verified.
- **[P4-39]** CORE, prospective-scope paragraphs, as cited in 06 — per 06.
- **[P7-8]** Vidhi Judicial, BSA s.132 — verified.
- **[P8-4]** Verma, "Is this Citation on Point?", arXiv:2608.12571 — verified (abstract).
- **[P8-68]** DPDP Act s.17 — verified.
- **[P10-10]** Kim et al., FAccT 2024 — verified.
- **[IN-1]** Copyright Act s.52(1)(q)–(r) — verified.
- **[IN-3]** *EBC v. D.B. Modak*, (2008) 1 SCC 1 — verified.
- **[IN-26]** *MADA v. SAIL* (2024) — verified.
- **[IN-55]** *Laksh Vir Singh Yadav v. UoI*, Delhi HC, 29 May 2026 — verified.
- **[IN-57]** DPDP Act s.17 — verified.
- **[IN-58]** DPDP Act s.3(c)(ii) — verified (by P0).
- **[IN-59]** AZB, DPDP Rules 2025 timeline — verified.
- **[IN-62]** *In re: Summoning Advocates*, 2025 INSC 1275 (SCO) — verified.
- **[IN-63]** MediaNama on MeitY's scraping stance — verified (by P0).
- **[XC-2]** Anthropic data residency — verified.
- **[XC-4]** Gemini API pricing — verified.
- **[XC-6]** AWS, Claude in India via Global CRIS — verified.
- **[XC-7]** AWS, OpenAI models in-country in India — verified.
- **[XC-8]** Azure Foundry region availability — verified.
- **[XC-12]** Sarvam-105B model card — verified.
- **[XC-33]** Beurer-Kellner et al., design patterns for securing LLM agents against prompt injection — verified.
- **[XC-34]** CaMeL — verified.
- **[XC-36]** AZB, DPDP phased rollout — snippet.
- **[XC-38]** CERT-In Directions 2022 (via PSA Legal) — snippet.
- **[XC-42]** DPDP Act s.3(c)(ii) — verified.
- **[XC-43]** BSA s.132 — verified.
- **[CT-4]** Bar & Bench / Manupatra — verified.
- **[CT-26]** Bar & Bench, SAM–Harvey — verified.
- **[CT-27]** Bar & Bench, AZB–Harvey — verified.
- **[CT-34]** LexisNexis–Harvey alliance — verified.
- **[CT-39]** Vals AI VLAIR, 14 Oct 2025 — verified.
- **[CT-56]** Karnataka HC, *Buckeye Trust v. Registrar, ITAT* (18 Sep 2025) — verified.
