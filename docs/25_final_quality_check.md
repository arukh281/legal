# Final Quality Check

*This is the blueprint's answer to the brief's "FINAL QUALITY CHECK". Three independent critics ran after all synthesis passes, each fixing small defects in place: A covered requirements traceability, B interfaces, and C the moat, buildability and citations. Their full findings are in §A–§C below. Rulings they triggered are in [01a_spine_decision_record.md](01a_spine_decision_record.md) D22–D23.*

## Answers to the five questions

| # | Question (brief) | Answer | Evidence |
|---|---|---|---|
| 1 | Does every interface between phases line up exactly? | **Yes, with one measured exception.** 14 critical producer→consumer contracts were audited field by field; 12 had naming, enum or optionality drift and all were fixed. The canonical catalogues are [01 §5–§9](01_master_architecture.md), ruled by D1–D23. 37 of 38 residual mismatches (R-01…R-38) are RESOLVED. **R-18** (the latency capacity of P3 `authority:batch` for P5's ~600-ID calls) stays open until the M1 load test; a two-call fallback is specified. All 29 Mermaid diagrams parse and render, and all 369 tables have consistent columns. | §B; 01 §8, §14 |
| 2 | Is every factual claim cited or clearly marked as unverified? | **Yes, as a documentation standard; see the caveat.** Every doc tags claims to its own reference list. 24_bibliography merges 588 unique sources (≈489 verified, ≈83 snippet, ≈12 unverified at merge time), and each doc's §8.R and §11 list what could not be verified. A fresh fetch of 25 high-stakes claims found no material error in 00 or 01. **Caveat (D23.8):** "verified" means machine-assisted fetch and read. Two automated fetch summaries were wrong during QC. Every legal source a tier-1 output relies on must be checked by a human word for word before production. | §C.3; 24 |
| 3 | Did we address every India-specific requirement? | **Yes.** All 23 India-specific rows are ADDRESSED (two gaps were fixed during QC: NJDG in the source catalogue and constitutional point-in-time cases). The remaining weaknesses are disclosed research limits, not omissions: the Hindi and regional-language quality gap, five unverified HC neutral-citation formats, and 22 pending legal opinions (23 §4). | §A.3; 21 |
| 4 | Would a senior engineer know exactly what to build? | **Largely yes.** Buildability scores are P0 4, P1 4, P2 5, P3 5, P4 5, P5 4, P6 4, P7 4, P8 5, P9 4, P10 4 (average 4.4/5); no phase needs a design session before sprint 1. The remaining gaps are mostly empirical (OCR, embedder and cheap-model benchmarks; reviewer throughput, D23.1; ratio/obiter annotator agreement) or legal (portal access), not architectural. The docs are long (≈17–23K words per phase), so read 01 first, then each phase's §2, §5 and §10. | §C.2; §A.10; 22 |
| 5 | Is the moat real, or just features a funded competitor could copy in 6 months? | **Real only as a combination, and only if we run it well.** Features are copyable, as are M1 (clean anchored corpus), M3 (point-in-time statutes and crosswalk) and M6 (benchmark) on their own. The durable part is **M2 × M4 × M5**: a *calibrated*, audited, proposition-level treatment ledger (M2), wired into precise matter alerts (M4), improved by consented feedback across at least 5 firms (M5). Capital is not the barrier. Plan on **≈12 months** of lead against an incumbent–Harvey alliance, and 18–30 months against a funded startup. 00 and 20 §6 were reworded to say exactly this. | §C.1; 20 §6; 00 |

## What the QC could not close (next research actions)

1. **Indian user-complaint evidence** (Reddit, LinkedIn, G2, Play Store) for the teardown was not gathered (20 §1.3). It needs a dedicated research sprint, plus hands-on trials of SCC Online AI Pro, Manupatra AI and Prism with the partner firm.
2. **Per-court real-time feasibility matrix** for HC listings before the M1 scope is fixed. Only Delhi and Allahabad listings were observed working (§C.2, P0).
3. **Ratio/obiter inter-annotator agreement** (κ ≥ 0.6 target) with partner lawyers. P3's proposition layer depends on it.
4. **The ~40 MVP procedural RuleSpecs** (P6) must be enumerated and every statutory anchor verified word for word (D23.8).
5. **Privacy budget and k-threshold analysis** for P9 S2 aggregates before GA.
6. **Tier-1 reviewer throughput** measured in the pilot (D23.1; 23 U-08). It drives both cost and the M2 moat.
7. **R-18 load test**, and P5's 2.5 s evidence-bundle target against its own stage budget (07_P5 §5.13 note).
8. **Moat-strengthening proposals** MS-1…MS-6 (§C.1.3) await a product decision, especially partner exclusivity and retention terms, which need a competition-law check, and signing 3–5 firms by month 12.
9. **One-page "build cards" per phase** (components, contracts, storage, SLOs, MVP cut) would make the long phase docs faster to act on.

---

## A. Requirements traceability matrix (brief quality questions 3 and 4)

*Status: complete (final QC, 30 Sep 2026). Scope: every requirement in the client brief, traced to doc and section.*

Legend: **ADDRESSED** = requirement is met with concrete design + citations; **PARTIAL** = discussed but thin, scattered, or missing a required element; **GAP** = not found; **FIXED** = was PARTIAL/GAP, a small in-place fix was applied during this check (location given).

### A.1 "How you must work" rules (brief §HOW YOU MUST WORK)

| # | Requirement | Where addressed | Status |
|---|---|---|---|
| W1 | ≥2–3 alternatives per major choice, compared on accuracy, cost, latency, maintainability, defensibility | §6 of every phase doc (02–12), each with 4–9 comparison tables; 13 §4.8 (Gateway); 01 §12 Decision Log (30 decisions, each with rejected alternatives and the five criteria); 01a D1–D22 | ADDRESSED. P7 §6 and P8 §6 adapt the column set to the decision (for example "Isolation/accuracy", "Defensibility to a GC", "India fit"). That is acceptable, but not every table carries all five named criteria. |
| W2 | Exhaustive research, 2024–2026 priority, including user complaints | §3 survey in every phase doc; 20 §3 (reviews, docs, complaints per competitor) and 20 §1.3 (research limits); 24 bibliography | ADDRESSED |
| W3 | Mistakes of others, per phase, and how we avoid each | §4 table `System/paper \| What went wrong \| Evidence \| How we avoid it` in all 11 phase docs (11–16 rows each); 13 §1.4 (cross-cutting); 20 §4 (cross-competitor failure patterns) | ADDRESSED |
| W4 | Novel ideas clearly labelled as unvalidated | §7 in every phase doc; `[NOVEL — unvalidated]` tag used 1–18 times per doc (for example 06_P4 §5.8, 21, 13, 20) | ADDRESSED |
| W5 | Cite every factual claim; never invent; say when a claim cannot be verified | Inline `[CODE-n]` tags with a verified/snippet/unverified grade in every doc; 24 bibliography; 23 §5 "Unverified assumptions"; "could not be located" and "(snippet only)" markers (for example 05_P3 §3.2) | ADDRESSED at the requirement level. Claim-level audit belongs to the citation lens (brief quality Q2), not this one. |
| W6 | Red-team each phase: 10M docs, bad OCR, Hindi judgment, precedent overruled yesterday, malicious or confused user | §8 plus §8.R "Independent review findings" in all 11 phase docs. All seven standard scenarios, including source outage/format change, appear in every §8 (grep-verified). Also 13 §10, 20 §8, 21 §10.2 | ADDRESSED |
| W7 | Parallel research per phase, then a synthesis pass that checks every interface | 01 §8 (producer × consumer matrix, contract check); 01 §14 (residual mismatches); 01a D19–D22 (synthesis and conformance rulings); "2.0 Spine v1.0 conformance" subsection in every phase doc | ADDRESSED |

### A.2 Known starting points (brief §KNOWN STARTING POINTS)

| # | Requirement | Where addressed | Status |
|---|---|---|---|
| K1 | Hybrid (vector + curated KG) vs pure vector RAG vs pure GraphRAG | 05_P3 §3.1–3.2 (Ongris et al. CEUR 2025: hybrid modes won, KG-only "often underperform"); 07_P5 §3.3, §6.1 (overall retrieval architecture alternatives); 01 §12 | ADDRESSED |
| K2 | LegalGraphRAG | 05_P3 §3.2 [P3-2] (hierarchical graph plus Researcher→Auditor→Adjudicator chain; "abstract gives no numbers" stated) | ADDRESSED |
| K3 | SBV-LawGraph | 05_P3 §3.2 [P3-3] (marked *snippet; full text not accessible*) | ADDRESSED, with the evidence limit disclosed |
| K4 | "Graph RAG for Legal Norms: A Hierarchical, Temporal and Deterministic Approach" | 05_P3 §3.2 [P3-4] as SAT-Graph RAG (arXiv 2505.00039, v5 retitled "…Structural, Temporal, and Deterministic…", JURIX 2025); its ideas are adopted in 05_P3 §5.6 | ADDRESSED. The title drift from the brief is disclosed. |
| K5 | KG-based RAG benchmarking studies on legal documents | 05_P3 §3.2 [P3-5] (Ongris et al. 2025: HippoRAG 2, nano-GraphRAG, LightRAG, LlamaIndex) | ADDRESSED |
| K6 | Judgments segmented into facts / issues / arguments / ratio / obiter / order (rhetorical roles) | 03_P1 §3.2, §5.6 (S6 rhetorical-role labeller), §6.2; 04_P2 §5.2 (role-aware chunking); 05_P3 (ratio-level propositions); 07_P5 (role features) | ADDRESSED |
| K7 | Validate "premium models for KG construction, cheap for serving" | 13 §3.5 (verdict: **refuted as a phase rule**, replaced by risk-weighted allocation), with a cost comparison in 13 §3.3; 05_P3 §5.4 (partly validated; cost cascade); 03_P1 §6.6; 01a D14; 01 §10.4; experiment gate in 13 §4.6 | ADDRESSED |
| K8 | Fusing and reranking vector, keyword and graph results | 07_P5 §3.4–3.5, §5.6–5.9 (RRF candidate fusion, reranker cascade, relevance-gated monotone authority ranking), §6.2–6.4 | ADDRESSED |
| K9 | Stanford legal-tool hallucination study: how and why | 10_P8 §3.1 (Magesh et al. JELS 2025 figures and hallucination definition); 07_P5 §3.1 (four-mode error typology: naive retrieval, inapplicable authority, reasoning error, sycophancy), mapped into P5's design; 20 §3.22; 08_P6 §3.2 | ADDRESSED |

### A.3 India-specific requirements (brief §INDIA-SPECIFIC REQUIREMENTS, quality Q3)

| # | Requirement | Where addressed | Status |
|---|---|---|---|
| I1 | Official sources (eCourts, NJDG, SC and HC websites, India Code, e-Gazette, tribunal portals): coverage, formats, update frequency, reliability | 02_P0 §3.1 and §5.1 (catalogue with Coverage / Format / Update freq / Reliability (observed) / Access / ToU risk / Tier columns, from probes on 2026-09-30); 21 §1 (legal-data view) | ADDRESSED. **FIXED:** 21 §1 had no NJDG row although the brief names NJDG and P0 assesses it. A pointer row now links to P0 §3.1/§5.1/§5.12 and 09_P7 §3.7. |
| I2 | Legal terms of use for each official source | 02_P0 §3.4, §5.1 ("Legal basis / ToU risk" L/M/H), §5.2 lawful acquisition ladder; 21 §2.1 (Copyright Act s.52(1)(q)–(r)), §2.3 (access-control law and ToU, CAPTCHA as an access-control signal), §2.5 (privacy-driven publication limits); robots.txt probes | ADDRESSED |
| I3 | Licensing and legality of third-party sources | 21 §2.2 (*EBC v. D.B. Modak*: reporters' editorial layers), §2.4 (third-party datasets: AWS CC-BY-4.0, Indian Kanoon API terms), §3.5 (third-party metadata is not ground truth); 02_P0 §3.2; 23 §4 (legal opinions required) | ADDRESSED |
| I4 | Citation systems: SCC, AIR, SCR, other reporters, neutral citations; robust extraction and resolution | 21 §3.1 (reporter families with verbatim variants), §3.2 (neutral citations, INSC and HC schemes), §3.3 (normative EBNF), §3.4 (resolution strategy); 03_P1 §5.8 (S7 citation grammar, including SCALE, JT, Cri LJ, ILR, MANU and others), §5.9 (S8–S9 resolution and identity: five formats resolve to one Work); 01 §5.4 `identifier_alias` trust tiers | ADDRESSED |
| I5 | Article 141 binding force | 21 §4.1 `rul_IN_PREC_01–03` (Arts. 141 and 144, *Bengal Immunity*); 05_P3 §5.5 doctrine engine | ADDRESSED |
| I6 | Bench strength (larger binds smaller) | 21 `rul_IN_PREC_04–06` (*Dawoodi Bohra*, *Trimurthi Fragrances*: strength means Bench size, not majority size); 05_P3 `Bench.strength`, competence check (21 §5.3 rule 2, NOVEL); 07_P5 §5.9 authority features | ADDRESSED |
| I7 | Per incuriam | 21 `rul_IN_PREC_07` (*Pranay Sethi*), `DECLARES_PER_INCURIAM` predicate (21 §5.2); 05_P3 | ADDRESSED |
| I8 | Sub silentio | 21 `rul_IN_PREC_08` (*Synthetics & Chemicals*); 05_P3 (3 references) | ADDRESSED. There is no dedicated predicate: a sub silentio decision is a doctrine rule applied at status computation, not a treatment edge. That is defensible. |
| I9 | References to larger benches | 21 `rul_IN_PREC_05`, `_09` (pending reference does not suspend a precedent), `_14`, `_15`; `REFERS_TO_LARGER_BENCH` and `ANSWERS_REFERENCE` predicates plus the `PendingReference` node (21 §5.2); 05_P3 | ADDRESSED |
| I10 | HC decisions: binding or persuasive across states | 21 `rul_IN_PREC_13`, `_16`, `_17` (other-HC persuasive), `_24` (HC ruling on validity of a Parliamentary Act has all-India effect, *Kusum Ingots*); 21 §4.2 `binding_on_forum` decision table; `court_jurisdiction` territory map (21 §1: HC ↔ state/UT is not 1:1); 05_P3 §5.6 territory-scoped validity | ADDRESSED |
| I11 | Treatment classes: followed, distinguished, overruled, doubted, affirmed, reversed, referred | 21 §5.2 (all seven present: `FOLLOWS`, `DISTINGUISHES`, `OVERRULES`/`OVERRULES_IN_PART`, `DOUBTS`, `AFFIRMS`, `REVERSES`, `REFERS_TO_LARGER_BENCH`, plus about 15 India-specific predicates such as `DISMISSES_IN_LIMINE` and `STAYS`); Hindi cue lexicon; 05_P3 §5.2 ontology | ADDRESSED |
| I12 | An Indian Shepard's/KeyCite that is better than what exists | 21 §5.1 (why existing citators fall short), §5.3 (six design rules: proposition granularity, competence check, forum-relative status, honest non-events, derived negativity, evidence first); 12_P10 §5.5 citator badge; 20 §6.2 M2 | ADDRESSED |
| I13 | BNS/BNSS/BSA section-level mapping | 21 §6.1 (statutory basis), §6.4 (crosswalk model, `change_type` enum, clause-level many-to-many), §6.5 (worked verified rows); 05_P3 §5.7; 01a D16 | ADDRESSED |
| I14 | Pending and pre-transition cases | 21 §6.2 (2024–26 case law incl. *Parvinder Singh* 2026 INSC 519), §6.3 `governing_code()` per proceeding stage (BNS s.358, BNSS s.531(2)(a)/(3), BSA s.170(2), straddling offence → UNDETERMINED); `MatterContext.temporal_context` (01a D16 C2) | ADDRESSED |
| I15 | Criminal transition as a differentiator | 00 "India-specific capabilities"; 20 §6.2 moat element M3 (crosswalk carried through the treatment graph), while 00/20 §6.1 honestly class crosswalk *tables* alone as copyable; 23 §3.10 (T-10) | ADDRESSED |
| I16 | Point-in-time statutes | 21 §7.1–7.2 (commencement, ordinances, state amendments, repeal and savings, retrospective Acts, moulded retroactivity; `resolve(anchor, legal_date, territory)`); 05_P3 §5.6 (bitemporal `ProvisionVersion`, replay of amendment instructions, validity overlay); 03_P1 §5.7; 04_P2 §5.9 | ADDRESSED |
| I17 | Point-in-time constitutional provisions | 03_P1 §5.7 (same grammar: Articles, clauses, Parts, Schedules; amendment Acts parsed identically); 21 §7.1 row "Constitution amendments" (one line, uncited); `art-21A@date` anchors; 05_P3 §5.6 validity overlay | PARTIAL → see FIXED note in A.3a below |
| I18 | Multilingual judgments (Hindi, regional) | 21 §8 (Arts. 348(1)–(2), Official Languages Act s.7, the four Hindi-HC states, subordinate-court languages), §8.R; 03_P1 §3.6, §5.13; 04_P2 §3.7, §5.10 (cross-lingual); 23 §3.4 (T-09, a top-10 risk) | ADDRESSED. The Indic-language capability gap is recorded honestly as a top-10 residual risk. |
| I19 | Poor-quality scanned PDFs | 03_P1 §3.1, §5.2–5.3 (text-layer validation, OCR Gateway, dual-reader consensus, critical-token audit), §6.1; 10_P8 §5.3 (OCR-trust check) | ADDRESSED |
| I20 | DPDP Act 2023 (and Rules 2025) | 21 §9 (ss.3(c)(ii), 16, 17(1)(a); Rules commencement schedule); 09_P7 §3.6, §5.10 (retention, erasure, legal hold); 13 §5.8; 22 (DPDP-core controls before 12 May 2027) | ADDRESSED. There is a one-day discrepancy in the 18-month date (12 vs 13 May 2027), which 09_P7 §3.6 discloses and resolves by planning for the earlier date. |
| I21 | Client confidentiality and privilege | 21 §9 (BSA ss.132–134; *In re: Summoning Advocates*, 2025 INSC 1275); 09_P7 §3.6, §5.7 (ethical walls), §5.9 (per-matter keys and privilege protection); 11_P9 §5.5 Privacy Gate; 23 §3.5 | ADDRESSED |
| I22 | Data residency | 21 §9; 13 §4.4 (frontier-model availability with in-India processing, verified Sep 2026), §8 (DR inside India); 01 §10.3 residency routing; 01a D15; CERT-In 180-day in-India logs | ADDRESSED |
| I23 | Will large firms require on-prem or private cloud? | 21 §9 last row (evidence: SAM/CAM adopted US SaaS in 2025 → SaaS in an India region is acceptable when security is strong; D3/D4 for the rest); 09_P7 §3.6, §5.13; 01 §10.2 (D17 topologies); 13 §9 | ADDRESSED (evidence-based answer, not an assumption) |

#### A.3a Fixes applied for India-specific rows

- **I1 FIXED.** Added an NJDG row to 21 §1. It contains no new facts: it points to the P0 §5.1 assessment, including the government-only Open API and CAPTCHA markers, and to P0 §5.12, where NJDG serves only coverage reconciliation.
- **I17 FIXED (PARTIAL → ADDRESSED).** The 21 §7.1 row "Constitution amendments" was one uncited line saying "same pattern as Acts". It now covers two constitution-specific point-in-time cases, both verified this session:
  - **(a) An amendment struck down after it commenced.** The 99th Amendment/NJAC came into force on 13 Apr 2015 and was declared void on 16 Oct 2015, with the pre-amendment system declared operative [IN-80].
  - **(b) Application changed by Presidential order, not by an amendment Act.** C.O. 272/273 (2019) were upheld in 2023 INSC 1058 [IN-81].
  - The row also states the modelling consequence. `resolve()` must return the pre-amendment expression as operative after a strike-down; the 05_P3 §5.6 validity overlay alone only flags the text. Constitution orders must also be accepted as a `LegislativeAction` source in 03_P1 §5.7.
  - The case is cited by its verified writ-petition number (W.P.(C) 13 of 2015). The commonly used SCC citation is marked *(reporter citation unverified)* because no fetched source confirmed it.
  - IN-80 and IN-81 were added to the 21 reference list, to 24 §3 (entries 96–97, with the Counts table and fragment totals updated to 588 unique sources / 757 entries) and to `bib/IN.md`.
- **Follow-up (not fixed; needs owners).** 05_P3 §5.6 and 03_P1 §5.7 should adopt the two consequences above in their own text. Today only 21 states them.

### A.4 Phase sub-items P0–P10 (brief §ATOMIC PHASES)

All 11 phase docs follow the 11-section template exactly (§1–§11 + References, verified by heading scan). Every phase also carries a "2.0 Spine v1.0 conformance" subsection and a §5.N cross-cutting subsection. The per-phase "purpose / input contract / output contract / internal design / hand-off" requirement is met by §1, §2 and §5 in each doc, plus 01 §8 (producer × consumer matrix).

| Phase | Brief sub-item | Where addressed | Status |
|---|---|---|---|
| P0 | Crawling, scraping, API ingestion | 02_P0 §5.2 (lawful acquisition ladder: OPEN / LICENSED_API / BULK_DATASET / HUMAN_ASSISTED / MoU), §5.3, §5.5 adapter plug-in contract, §6.1/§6.3 | ADDRESSED |
| P0 | Scheduling | §5.4, §6.2 (orchestration alternatives) | ADDRESSED |
| P0 | Deduplication | §1 item 5, §2.2 `near_dup_hint` (simhash), §3.2 dedup key `(cnr, decision_date, order_number)`, §5.6 | ADDRESSED |
| P0 | Change detection | §5.6 (NEW/CHANGED/UNCHANGED/DELETED/REAPPEARED/METADATA_CHANGED/SUPPRESSED), §6.4 | ADDRESSED |
| P0 | Provenance and versioning of raw documents | §5.7 (WARC/WACZ archival, content-addressed raw IDs) | ADDRESSED |
| P0 | Site outages and format changes | §5.8 (WAFs, format drift), §5.12 (health, reconciliation), §8 red-team | ADDRESSED |
| P1 | OCR for scanned and multilingual documents | 03_P1 §5.2–5.3 (OCR Gateway, dual-reader consensus, critical-token audit), §5.13, §6.1 | ADDRESSED |
| P1 | Layout analysis | §5.4 (layout, reading order, document type) | ADDRESSED |
| P1 | Structural segmentation (facts, issues, arguments, ratio, obiter, order) | §5.6 S6 rhetorical-role labeller, §5.5 operative-order `ord` anchor, §6.2 | ADDRESSED |
| P1 | Statute parsing (parts, chapters, sections, sub-sections, provisos, explanations) | §5.7 (grammar with provisos `p1`, explanations `e1`, illustrations, schedules; Constitution articles and clauses) | ADDRESSED |
| P1 | Metadata (court, bench, judges, date, parties, case type, statutes cited, cases cited) | §5.5 header grammar (case_block, party_block, coram_block, dates, SLP→appeal lineage, CNR), triangulation from three sources; §5.8 statute and citation mentions | ADDRESSED |
| P1 | Citation extraction and resolution | §5.8 (S7 grammar and reporter registry), §5.9 resolver (alias exact → page window → party-name → cluster siblings) | ADDRESSED |
| P1 | Entity resolution (5 formats → one node) | §5.9 S8–S9 identity (P1 is sole writer of Work identity, 01a D20.4); 01 §5.4 `identifier_alias` | ADDRESSED |
| P2 | Hierarchical, structure-aware chunking | 04_P2 §5.2, §5.4 (structure-derived tree) | ADDRESSED |
| P2 | Legal embedding models (InLegalBERT + general embedders) evaluated | §3.2–3.3, §5.6, §6 table (InLegalBERT as a baseline arm only: a 512-token encoder, not a retrieval embedder) | ADDRESSED |
| P2 | Multi-level summaries | §2.3 `Summary` (non-citable), §5.5 (anchored, verified, labelled) | ADDRESSED |
| P2 | Keyword index / vector index | §5.7 lexical index design, §5.8 index topology, §3.4 engines | ADDRESSED |
| P2 | Indexes consistent with each other | §5.11 (generations, outbox, versioning, deletes, reconciliation) | ADDRESSED |
| P3 | Ontology (node and edge types) | 05_P3 §5.2; 01 §7.5 Assertion | ADDRESSED |
| P3 | Treatment edges with confidence scores | §5.4 cost cascade, §5.11 confidence calibration | ADDRESSED |
| P3 | Statute-to-judgment interpretation links | §5.4 "Statute links" (`CITES` → `INTERPRETS` upgrade rule), `STRIKES_DOWN`/`READS_DOWN` | ADDRESSED |
| P3 | Temporal versioning | §5.6 (bitemporal `ProvisionVersion`, PG18 temporal keys) | ADDRESSED |
| P3 | Old-to-new criminal code mapping | §5.7 (+ 21 §6.4–6.5) | ADDRESSED |
| P3 | Provenance on every edge | §5.3 storage schema; spine §F reified assertions with evidence and method | ADDRESSED |
| P3 | Self-enrichment from new documents and lawyer feedback | §5.8 (ten loops: forward, backward, attestation mining, consensus maps, implied-conflict miner (NOVEL), upgrades, lawyer feedback via `kg.proposal.v1` only, parser feedback, active learning, expected judgments) | ADDRESSED |
| P3 | Error detection, quarantine and correction | §5.9 (truth maintenance) | ADDRESSED |
| P3 | Human-in-the-loop for high-impact edges | §5.10 (queues, roles, SLAs; impact tier 1) | ADDRESSED |
| P3 | Graph database choice and why | §5.13 (PostgreSQL 18 system of record + in-memory CSR projection), §6 comparison, §3.7 landscape | ADDRESSED |
| P4 | Daily incremental ingestion; event-driven enrichment | 06_P4 §5.1–5.2 (event topology and backbone), §5.3 "law current to" frontier | ADDRESSED |
| P4 | Ripple effects to active client matters → alerts | §5.4 status recompute, §5.5 impact detection, §5.6 tenant-scoped fan-out without leakage (D3 broadcast + in-tenant match), §5.7 severity and storms; 01 §4.3 flow (c) | ADDRESSED |
| P4 | Idempotency | §2.3 idempotency-key grammar, §5.10 exactly-once *effect* | ADDRESSED |
| P4 | Backfills and reprocessing when parsers improve | §5.11 campaigns, §5.12 runbook; 01 §4.5 flow (e) shadow → P8 gate → promote | ADDRESSED |
| P5 | Query understanding and intent routing | 07_P5 §5.3 S1, §5.4 routing taxonomy | ADDRESSED |
| P5 | Legal-issue decomposition | §5.5 S2, §6.6 | ADDRESSED |
| P5 | Hybrid retrieval (keyword, vector, graph) | §5.6 S3–S4 | ADDRESSED |
| P5 | Authority-aware ranking (court level, bench strength, recency, treatment status, jurisdiction) | §5.9 S8 (relevance-gated, monotone; features include `court_level`, strength, `binding`, treatment, `age_years` for recency, jurisdiction); §6.4 | ADDRESSED |
| P5 | Reranker design | §5.8 cascade, §3.5, §6.3 | ADDRESSED |
| P5 | Legally coherent context assembly | §5.12 S11 authority packs, §6.7 | ADDRESSED |
| P5 | Adverse authority surfaced | §5.10 S9 mandatory adverse sweep; AAR metric in §9 | ADDRESSED |
| P6 | Multi-agent design (issue spotter, research, client advocate, opposing counsel, bench simulator, citation verifier, synthesis) | 08_P6 §5.3 agent catalogue (Issue Spotter, Research Planner, Client Advocate, Opposing Counsel, Rebuttal, Bench Assessor, Composer, …). The citation verifier is deliberately *not* an LLM agent: it is deterministic plus P8, with the reason stated. §6 alternatives | ADDRESSED |
| P6 | "Notice arrives → full response strategy" workflow | §5.2; §5.13 worked example (s.138 NI Act); 01 §4.2 flow (b) | ADDRESSED |
| P6 | Procedural intelligence (limitation, jurisdiction, forum, maintainability) | §5.5 deterministic Procedural Clock (calendar-month arithmetic, contested readings → one Deadline per variant), `Maintainability` output; §3.7 verified Indian procedural anchors | ADDRESSED |
| P6 | Drafting support | §5.8; `DraftArtifact` (01 §7.18); 12_P10 §5.11 Word add-in | ADDRESSED |
| P6 | Grounded and verified before shown | §5.6 closed-world citation protocol, §5.7 verify-then-show with P8 and repair loop | ADDRESSED |
| P6 | What Harvey, CoCounsel, Lexis+ AI, vLex Vincent do and where they fall short | §3.1, §4; 20 §3.15–3.18 | ADDRESSED |
| P7 | Case-file ingestion (pleadings, evidence, correspondence, emails) | 09_P7 §5.4, §3.8 | ADDRESSED |
| P7 | Private layer linked to the public graph without leakage | §5.3 bridge tenancy, §5.5 MatterContext, §5.6 tenant-side impact matching, §6.8; invariant INV-1 | ADDRESSED |
| P7 | Multi-tenant isolation; RBAC; audit logs; privilege protection | §5.2 TEC, §5.3, §5.7 (RBAC + ReBAC + ABAC, ethical walls), §5.8 tamper-evident audit, §5.9 per-matter keys; 13 §5.5 | ADDRESSED |
| P7 | Deployment options (SaaS, private cloud, on-prem) | §5.13; 01 §10.2 (D17: D1 pooled SaaS … D4 on-prem/air-gapped); 13 §9 | ADDRESSED |
| P7 | Matter tracking, hearing dates, alerts | §5.11 court tracking and eCourts sync, §5.12 `matter.alert.v1`; 12_P10 S1 "Court day" | ADDRESSED |
| P8 | Citation verification (paragraph exists and says what is claimed) | 10_P8 §5.3 check ladder (existence, pinpoint, quote hash, OCR trust, masked spans, entailment), §5.5 | ADDRESSED |
| P8 | Hallucination detection | §5.3–5.5, §5.10.4 perturbation factory (NOVEL), §9.1 | ADDRESSED |
| P8 | Confidence shown to users | §5.6 (stratified calibration + conformal bands), §5.7 UI semantics; §6 D2 | ADDRESSED |
| P8 | IL-TUR, LegalBench, RAG metrics (faithfulness, context precision, context recall) | §3.7 (Indian benchmarks incl. IL-TUR, with a stated gap), §3.3 (RAGAS/ARES); §6 (RAGAS metric ideas reused, not the harness); §9.2 P5 row "context precision/recall reported" → 07_P5 §9 "RAG context metrics". Faithfulness is operationalised as claim-level entailment/support rate | ADDRESSED. Context recall appears only by delegation to P5 §9, with target "report" and no numeric threshold. That is acceptable for MVP. |
| P8 | Gold set with the partner firm | §5.10 evaluation platform and gold sets (pooling ≥3 systems, blind judging, α agreement), §5.13 Design Partner Program; §6 D3 | ADDRESSED |
| P8 | Continuous regression testing when any phase changes | §5.11 regression gating (paired-bootstrap non-inferiority + zero-tolerance sentinels), §9.2 per-phase metric catalogue P0–P10; 01a D11 | ADDRESSED |
| P9 | Capture corrections, accepted/rejected arguments, outcomes | 11_P9 §5.2 feedback taxonomy and capture points, §5.10 outcomes and argument uptake; 12_P10 §5.13 | ADDRESSED |
| P9 | → graph improvements, reranker training data, eval cases | §5.6 (a) KG proposals → P3; §5.7 (b) ranking data → P5; §5.8 (c) eval cases → P8; §5.9 (d) personalization | ADDRESSED |
| P9 | Without violating confidentiality | §5.4 consent model, §5.5 Privacy Gate (classes S0–S3, k≥5 aggregation), §5.11 anti-poisoning, §5.12 unlearning | ADDRESSED |
| P10 | Daily digests | 12_P10 §5.10 | ADDRESSED |
| P10 | Watchlists for statutes, judges, topics | §5.9 (WORK, PROVISION, CASE, JUDGE/BENCH/COURT, topic kinds) | ADDRESSED |
| P10 | Alerts on changes affecting matters | §5.8 (routing, fatigue control, escalation, retraction) | ADDRESSED |
| P10 | Dashboards | §5.4 S1 "Today" and S2 "Matter cockpit" | ADDRESSED for lawyer and matter level. There is no firm-level or practice-group portfolio dashboard (for example a managing partner's view of exposure across matters); worth adding post-MVP. |
| P10 | Interaction model for busy, skeptical lawyers | §1.2 users and constraints, §1.5 design principles, §3.3 trust/reliance HCI evidence, §5.3 keyboard command grammar, §5.6 click-to-source, §5.7 uncertainty display | ADDRESSED |

### A.5 Cross-cutting concerns (applied to every phase)

Every phase doc has a "§5.N Cross-cutting: security, cost at scale, latency, observability, model-agnostic design" subsection: P0 §5.13, P1 §5.15, P2 §5.16, P3 §5.15, P4 §5.16, P5 §5.16, P6 §5.12, P7 §5.14, P8 §5.14, P9 §5.14 and P10 §5.17.

| # | Requirement | Where addressed | Status |
|---|---|---|---|
| X1 | Security | 13 §5 (assets and trust boundaries, STRIDE by boundary, OWASP LLM Top 10 2025 → controls, prompt-injection architecture, tenant isolation, secrets, supply chain, India compliance programme, PLC redaction and takedown); 01 §11.3; phase §5.N | ADDRESSED |
| X2 | Cost at scale (≈5M+ documents) | 13 §2 (corpus sizing, verified anchors + flagged estimates), §3 (formulas and results at 5M/10M/20M, monthly run, cost controls); 01 §11.2; 01a D18/D19.1 figures of record; 04_P2 §5.14, 05_P3 §5.14 | ADDRESSED. The figures are labelled planning estimates pending the P1 10K-document measurement (D19.8), which is the honest treatment. |
| X3 | Latency targets | 13 §6 (interactive SLOs; freshness and alert SLOs P0→P4→P7→P10); 01 §4 per-hop SLOs and §11.1; 07_P5 §5.13 per-stage budget; 12_P10 §5.15 | ADDRESSED |
| X4 | Observability | 13 §7 (stack, SLOs and error budgets, per-stage data-quality checks, privacy in telemetry); 01 §11.4 lineage | ADDRESSED |
| X5 | Model-agnostic design (survive swapping LLM providers) | 13 §4 Model Gateway (`ModelTaskContract`, routing, prompt portability and structured outputs, eval gates on promotion, fallbacks, §4.8 alternatives); 01 §10.5, §11.5; 01 §7.23–7.24 | ADDRESSED |
| X6 | Failure modes | 13 §10 failure-mode catalogue, §8 reliability and DR inside India; §8 in every phase doc | ADDRESSED |

### A.6 Design-partner requirements (brief §PRODUCT CONTEXT)

| # | Requirement | Where addressed | Status |
|---|---|---|---|
| DP1 | Gold-standard evaluation sets from the partner | 10_P8 §5.10 (gold construction: pooling, blind judging, inter-annotator α), §5.13 Design Partner Program ("gold room", data classes DC0–DC4), §6 D3; 22 §5 month-by-month gold construction | ADDRESSED |
| DP2 | Feedback loops | 11_P9 (whole doc); 12_P10 §5.13 capture points, §5.14 onboarding the partner; 22 §5 "feedback loop activation" column | ADDRESSED |
| DP3 | Proprietary data advantages | 10_P8 §5.13 "Proprietary data advantage (what compounds)"; 11_P9 §5.13 (proving the loop improves things); 20 §6.2 moat element M5 (with time-to-copy) | ADDRESSED |
| DP4 | Proper consent | 10_P8 §5.13 legal instruments (Design Partnership Agreement, DPA, contribution schedule, IP, exit); 11_P9 §5.4 consent model; `ConsentRecord` (01 §7.25, D21.16); 22 §5 consent instruments C1–C3 | ADDRESSED |
| DP5 | Privilege protection | 11_P9 §5.5 Privacy Gate (classes S0–S3, k≥5 cross-tenant aggregation), §5.12 unlearning; 09_P7 §5.9; 21 §9 (BSA s.132, 2025 INSC 1275); 23 §3.5 | ADDRESSED |

### A.7 Competitive teardown (brief §COMPETITIVE TEARDOWN)

The brief asks for three things per competitor: what it does well, where it fails (reviews, docs, demos, complaints), and which architectural choices likely explain the failures. 20 §3 sets its own five-heading rule for every entry: Facts / Does well / Fails-gaps / Probable architectural cause / Threat-borrow. The heading scan below checks each named competitor against that rule.

| Competitor (brief-named) | Where | Does well | Fails | Arch. cause | Status |
|---|---|---|---|---|---|
| SCC Online (AI Pro) | 20 §3.1 | ✔ | ✔ | ✔ | ADDRESSED |
| Manupatra (ManuWorks) | 20 §3.2 | ✔ | ✔ | ✔ | ADDRESSED |
| Indian Kanoon (Prism) | 20 §3.3 | ✔ | ✔ | ✔ | ADDRESSED |
| CaseMine (AMICUS) | 20 §3.4 | ✔ | ✔ | ✔ | ADDRESSED |
| Jhana.ai | 20 §3.6 | ✔ | ✔ | ✔ | ADDRESSED |
| NyaySaathi | 20 §3.10 | was ✘ | was ✘ | was ✘ | **FIXED.** The entry had only Facts / Assessment / Threat. The homepage was re-fetched (30 Sep 2026) and the entry now has Does well, Fails/gaps (structural: no sourcing or verification statement, no citator flags, no firm or security features), a labelled architectural-cause inference mapped to §4 F4/F5/F8/F9, and Threat/borrow. |
| Bharat.Law | 20 §3.7 | ✔ | ✔ | ✔ | ADDRESSED |
| Claw | 20 §3.11 | ✔ | ✔ | was ✘ | **FIXED.** Added the architectural cause (inference): a docket-metadata-first practice-management data model (§4 F5, F8). |
| LegitQuest | 20 §3.5 | ✔ | ✔ | ✔ | ADDRESSED |
| LawCentral | 20 §3.12 | ✔ | ✔ | was ✘ | **FIXED.** Added the architectural cause (inference): third-party existence check instead of anchored entailment (§4 F4); credit-metered calls (F13). |
| Harvey | 20 §3.15; 08_P6 §3.1 | ✔ | ✔ | ✔ | ADDRESSED |
| CoCounsel | 20 §3.16; 08_P6 §3.1 | ✔ | ✔ | ✔ | ADDRESSED |
| Lexis+ AI | 20 §3.17; 07_P5 §3.1; 10_P8 §3.1 | ✔ | ✔ | was ✘ | **FIXED.** Added the architectural cause (inference): citator used post hoc, not as a pre-generation ranking input, consistent with the Stanford 38% inapplicable-authority share (§4 F2, F1/F14). |
| vLex (Vincent) | 20 §3.18; 08_P6 §3.1 | ✔ | India gap only | was ✘ | **FIXED.** Added "Fails/gaps (beyond India)", which honestly states that no Vincent-specific failure evidence was found (VLAIR Feb 2025 per-vendor scores unreadable, snippet), and an architectural cause of the India gap (breadth-first global corpus, §4 F10). This remains **evidence-thin**, which is a research limit, not a structural gap. |
| "Any others you find" | 20 §3.8 Lexlegis, §3.9 Lucio, §3.13 Adalat AI/SUPACE/SUVAS, §3.14 Vaquill/BharatLaw.ai, §3.19 Legora, §3.20 Paxton/Midpage, §3.21 foundation-model providers | — | — | Lexlegis, Lucio and Legora lack an explicit architectural-cause line (not brief-named; left as is) | ADDRESSED |
| User complaints / reviews | 20 §1.3 states honestly that Indian user complaints (Reddit, LinkedIn, G2) could not be gathered systematically. Global complaints: Bloomberg Law on Harvey [CT-32] | | | | **PARTIAL (open).** A research gap acknowledged in the doc. Closing it needs fresh research, not a QC edit. |
| Moat analysis: what is genuinely hard to copy, and why | 20 §6.1 (what is *not* a moat), §6.2 (M1–M6 with time-to-copy for startup / incumbent / Harvey), §6.3 honest verdict, §6.4 threat scenarios; 00 "The moat, stated honestly" | | | | ADDRESSED |

### A.8 Product-context requirements (brief §PRODUCT CONTEXT)

| # | Requirement | Where addressed | Status |
|---|---|---|---|
| PC1 | B2B multi-seat law firms | 09_P7 (tenancy, RBAC/ReBAC, ethical walls); 12_P10 §1.2; 20 §5 pricing and GTM | ADDRESSED |
| PC2 | Corpus: SC, all HCs, major tribunals (NCLT, NCLAT, ITAT, NGT, CAT, consumer commissions), Constitution and amendments, central and state statutes, rules, notifications, ordinances, gazettes | 02_P0 §5.1 (every class has a row, with a tier); 22 §3.3–3.6 phasing (tribunals from M2; state gazettes for the partner's states at M3; all state gazettes and district orders at M4) | ADDRESSED. The phasing is explicit and justified. |
| PC3 | Freshness to a Bloomberg standard: daily ingestion with automatic propagation | 13 §6.2 freshness and alert SLOs; 06_P4 §5.3 "law current to" frontier; 01 §4.1 flow (a); 12_P10 S1 "Law current to" banner; 22 kill criterion K-3 (drop the HC freshness claim if no lawful route exists) | ADDRESSED |
| PC4 | Core experience: other side's claims, favourable law, hurting law, strongest counter-arguments, likely opposing arguments, evidence to prepare, deadlines and limitation, draft response strategy | `StrategyMemo.sections` (01 §7.17): `opponent_claims`, `favourable_authorities`, `adverse_authorities`, `counter_arguments`, `likely_opposing_arguments`, `evidence_checklist`, `deadlines`, `draft_strategy`, plus `uncertainties`. This is a one-to-one match. 08_P6 §5.2, §5.13 worked example | ADDRESSED |
| PC5 | Every claim traces to a specific paragraph of a specific source | 01 §5.3 anchor grammar (EBNF), §5.5 anchor stability; 08_P6 §5.6 closed-world citation; 10_P8 §5.3; 12_P10 §5.6 click-to-source | ADDRESSED |
| PC6 | Moat is architecture, data structure and trust, not model choice | 20 §6 (explicitly lists "the model" as not a moat); 00 "The moat, stated honestly"; 23 §3.1 (BC-01 moat erosion is the top risk) | ADDRESSED (moat *strength* is quality Q5, out of this lens) |

### A.9 Deliverables and template

| # | Requirement | Where | Status |
|---|---|---|---|
| D1 | 00_executive_summary.md | present (164 lines) | ADDRESSED |
| D2 | 01_master_architecture.md | present (1,897 lines), plus 01a_spine_decision_record.md (D1–D22) | ADDRESSED |
| D3 | One file per phase P0–P10 using the 11-section template | 02–12 present. Heading scan: every file has §1–§11 in the brief's exact order and wording, plus References; §8.R independent-review subsections added | ADDRESSED |
| D4 | 20_competitive_teardown.md | present | ADDRESSED (fixes in A.7) |
| D5 | 21_india_specific_legal_data.md | present | ADDRESSED (fixes in A.3a) |
| D6 | 22_build_roadmap.md | present (milestones M0–M4, critical path, team, budget, design-partner timeline, kill criteria) | ADDRESSED |
| D7 | 23_risk_register.md | present (8 categories, top-10, legal opinions required, unverified assumptions, review cadence) | ADDRESSED |
| D8 | 24_bibliography.md | present (588 unique sources after this pass) | ADDRESSED |
| D9 | "Refine the phase list if research shows a better decomposition" | Decomposition kept, with a cross-cutting doc (13) and a spine decision record (01a) added; 01 §3 phase catalogue | ADDRESSED. No explicit "we considered re-cutting the phases and why not" paragraph exists; this is minor. |

### A.10 Verdicts on brief quality questions 3 and 4

**Q3. Did we address every India-specific requirement?** **Yes.** After this pass, all 23 India-specific rows (I1–I23) are ADDRESSED. Two were fixed in place: I1 (NJDG row) and I17 (constitution-specific point-in-time cases). Precedent doctrine is the strongest area: 21 §4.1 turns Art. 141, bench strength, per incuriam, sub silentio, larger-bench references and inter-HC effect into 24 cited machine rules. The weakest remaining areas are honest research limits, not omissions:
- Indic-language capability is a top-10 residual risk (T-09).
- Five HC neutral-citation formats are unverified (01 §14.2 item 7).
- Several legal-interpretation points await counsel (23 §4): BSA s.132 scope for vendor staff, DPDP s.3(c)(ii) for court-published data, and SCC pinpoint mapping.

**Q4. Would a senior engineer know exactly what to build?** **Largely yes.**
- **What is in place.** Every phase doc has concrete schemas (TypeScript, JSON, SQL DDL; 0–20 `CREATE TABLE`s per doc), at least one Mermaid diagram, pseudo-code for the core algorithms, SLO tables with p95 targets, and an MVP-vs-full split. 01 fixes shared identifiers, events and objects (§5–§7) with a producer × consumer contract check (§8). 22 gives build order, a critical path and per-milestone scope (§3.7).
- **What still blocks exact build instructions.**
  1. One interface item remains OPEN (01 §14.1 R-18: P3 `authority:batch` capacity vs P5's 600-id p95 requirement), deferred to an M1 load test.
  2. Eight substantive open questions in 01 §14.2. Each has an owner and a plan.
  3. Length: phase docs run 17K–23K words against the 6K–11K guidance in the standards. The reading paths in 01 §1.3 mitigate this, but a new engineer faces about 230K words of phase text. A per-phase one-page "build card" (components, contracts, storage, SLOs, MVP cut) would help. That is not a cheap fix and is left open.

### A.11 Summary of in-place fixes made by this lens

1. **21 §1:** added an NJDG pointer row (no new facts; cross-refs to P0 §3.1/§5.1/§5.12/§11 and 09_P7 §3.7).
2. **21 §7.1:** expanded the "Constitution amendments" row with two verified constitution-specific point-in-time cases (99th Amendment/NJAC struck down; C.O. 272/273 upheld in 2023 INSC 1058) and their modelling consequences. Added [IN-80] and [IN-81] to 21 References, 24 §3 (entries 96–97; Counts table and totals updated to 588 unique / 757 entries / IN fragment 81) and `bib/IN.md`.
3. **20 §3.10 NyaySaathi:** restructured to 20's own five-heading rule after re-fetching the homepage. Architectural cause labelled as inference and mapped to real §4 patterns (F4, F5, F8, F9).
4. **20 §3.11 CLAW, §3.12 LawCentral, §3.17 Lexis+ AI, §3.18 vLex:** added labelled "Probable architectural cause (inference)" lines. vLex also got a "Fails/gaps (beyond India)" line that states the evidence limit honestly. All reuse only citations already in the doc ([CT-23], [CT-35], [CT-38], [CT-40], [CT-41], [CT-42]).

### A.12 Open issues for the owners (not fixed; too large or needs research)

1. **05_P3 §5.6 / 03_P1 §5.7 (P3, P1 owners).** Adopt the two constitution consequences now recorded in 21 §7.1:
   - after a strike-down, `resolve()` returns the pre-amendment expression as operative;
   - constitution (application) orders are a `LegislativeAction` source.
2. **20 §1.3 (CT owner).** Indian user complaints and reviews (Reddit, LinkedIn, G2, Play Store) are still not gathered. The brief explicitly asks for them, so fresh research is needed.
3. **20 §3.18 (CT owner).** vLex Vincent failure evidence is still thin. The VLAIR Feb 2025 per-vendor scores were not readable. Obtain a text version.
4. **12_P10.** No firm-level or practice-group portfolio dashboard (for example a managing partner's view of adverse-authority exposure across matters). Consider it for M3/M4.
5. **Standards compliance (length).** Phase docs are about twice the recommended length. Consider one-page build cards per phase (Q4).
6. **01 §14.1 R-18.** Still OPEN, pending the M1 load test.


---

## B. Interfaces lens — contracts, diagrams, tables

*Status: complete. Scope: (1) 14 critical producer→consumer contracts from 01_master §6–§8; (2) every Mermaid block in all docs; (3) every Markdown table in all docs. Canonical baseline: 01a (D1–D22) + 01_master §5–§9; per 01 §1.1, where a 01 passage disagreed with a D-ruling the ruling won and the 01 passage was corrected.*

### B.1 Mermaid diagram validation (all docs)

Tooling: `mermaid@11` + `jsdom` in `scratchpad/mmcheck/` — `check.mjs` (`mermaid.parse`) and `render.mjs` (full `mermaid.render` with jsdom `getBBox`/`CSSStyleSheet` stubs; the output SVG is also scanned for mermaid's embedded "Syntax error in text" diagram).

| Doc | Blocks | Types | Parse | Render |
|---|---|---|---|---|
| 00_executive_summary | 1 | flowchart | OK | OK |
| 01_master_architecture | 7 | flowchart, 5× sequenceDiagram, erDiagram | 7/7 OK | 7/7 OK |
| 02_P0 | 1 | flowchart | OK | OK |
| 03_P1 | 1 | flowchart | OK | OK |
| 04_P2 | 2 | flowchart ×2 | OK | OK |
| 05_P3 | 2 | flowchart, stateDiagram-v2 | OK | OK |
| 06_P4 | 2 | flowchart, stateDiagram-v2 | OK | OK |
| 07_P5 | 1 | flowchart | OK | OK |
| 08_P6 | 2 | flowchart, sequenceDiagram | OK | OK |
| 09_P7 | 2 | flowchart ×2 | OK | OK |
| 10_P8 | 1 | flowchart | OK | OK |
| 11_P9 | 1 | flowchart | OK | OK |
| 12_P10 | 2 | flowchart ×2 | OK | OK |
| 13_cross_cutting | 1 | flowchart | OK | OK |
| 20_competitive_teardown | 1 | quadrantChart | OK | OK |
| 22_build_roadmap | 2 | flowchart, gantt | OK | OK |
| 01a, 21, 23, 24 | 0 | — | — | — |

**Result: 29/29 Mermaid blocks parse and render; no diagram fixes were needed in this pass** (the label-quoting fixes applied by the earlier interrupted run hold).

### B.2 Markdown table column-count check (all docs)

Tooling: `scratchpad/qcB/tables.py` — GFM rule (a `|` inside a code span still splits a cell unless escaped as `\|`); every table outside fenced blocks is checked (header vs delimiter vs each body row).

**Result: 369 tables scanned, 0 rows with a column-count mismatch.** (The pipe-escaping fixes applied by the earlier run hold.)

### B.3 Producer → consumer contract audit (14 critical contracts)

Method: for each contract, the field names and enums in the producer's §2, the consumer's §2 (inputs) and 01_master §6–§7 were compared (01 + 01a canonical; where a 01 passage disagreed with a D-ruling, the D-ruling won per 01 §1.1). "Fixed" = edited in place during this check.

| # | Contract | Producer (§) | Consumer(s) (§) | Status | Fix / note |
|---|---|---|---|---|---|
| 1 | `raw.captured.v1` | P0 (02 §2.2) | P1 (03 §2.1a); P3 filtered (05 §2.1 I14) | ✔ fields match; **fixed** consumer list | All P1-relied fields (`raw_id`, `change_kind` incl. `METADATA_CHANGED`/`SUPPRESSED`, `prior_raw_id`, `terms_ref`, `provenance_tier`, `rights_class`, `lang_hint`, `flags{…}`, `fetch_context.priority`, `redaction_overlay_id`) exist with identical enums in 02 §2.2 and 01 §6.3. P3's metadata-only filtered subscription (for `Work.integrity_flags[]`, D19.5) was missing from 01 §6.2 and the §8.1 matrix although 05_P3 asked for it → added to 01 §6.2 row and matrix cell P0→P3 (`RC(filtered)`); 05_P3 I14 and §11 item 12 updated to say it is listed. |
| 2 | `doc.parsed.v1` + `ParsedDocument` | P1 (03 §2.2, §2.3) | P2 (04 §2.1), P3 (05 §2.1 I1) | ✔ after **fix in 01** | Payload fields match 01 §6.3 (`par_` prefix, `work_id_status`, `case_ids[]`, `quality.gate`, `hidden_text_flags`, `supersedes_parse_id`, `anchor_changes`, `rights_class`, `provenance_tier`). Mismatch: 01 §7.1 `ParsedNode.rhetorical_role` used `{…, conf, method, source?}` and §8.2 C4 said `{label, fine, dist, conf}`, contradicting D16 (`{label, confidence, source}`), which 03_P1 §2.3 and 04_P2 §2.1 (reads `.confidence` < 0.6 for fallback) already follow → 01 §7.1 and C4 corrected to `{label, fine, dist, confidence, source}` (`fine`/`dist` additive per 03_P1 §2.0 S11). |
| 3 | `graph.delta.v1` | P3 (05 §2.2 O1) | P4 (06 §2.1 I4), P5 (07 §2.1 events), P2 (04 §2.1), P8 (10 §2.2) | ✔ | `graph_watermark` int64, `cause.kind` 7-value enum (D4 + `IDENTITY`), `status_changes[].{subject_id, definitive, reason_codes, valid_from}`, `retracted[].reason`, `superseded[].change`, `manifest_uri` identical in producer, both consumers and 01 §6.3. "One delta per `doc.parsed.v1`" stated on both sides. No fix needed. |
| 4 | `impact.detected.v1` | P4 (06 §2.2 O1, O6) | P7 Impact Matcher (09 §2.5-6, §5.6), P6 RuleSpec registry, P10 | ✔ after **fix in 01** | 01 §6.3 still wrote `verification.state`, contradicting D5 (`verification{definitive, review_state}`), which P4 emits and P7/`impact-match-core` read; 01 §8.2 C10 and §14 R-19 repeated `verification.state` → 01 §6.3 now lists `review_state` (D5) plus `state?` as the v1.x read alias P4 already emits; C10/R-19 updated; 06_P4 §2.0 wording ("01 still uses that name") updated. P4 also emits `text_awaited` (D16 "PROVISIONAL impact flagged text awaited", consumed by P10's "text awaited" chip) which 01 §6.3 omitted → added. |
| 4b | `Freshness` (sync, read by P3/P5/P6/P8/P10) | P4 (06 §2.2 O4) | P5, P6, P8, P10 (12 §2.1 I12) | ✔ after **fix in 01 + P10** | 01 §7.14 used the flat `stage_lag_p95_min`; D9 names the field `stage_lag` and P4 serves `stage_lag.p95_min` (flat name as a v1 alias) → 01 §7.14 corrected (and `expected_pending`, which P4 serves and P5/P10 use, added); 12_P10 I12 and 06_P4 §2.0 note aligned. |
| 5 | `matter.alert.v1` | P7 (09 §2.5-2, §5.6, §5.12) | P10 (12 §2.1 I1) | ✔; **fixed** P7 details | Field list identical in 09_P7, 12_P10 and 01 §6.3 (D5 merged schema incl. `polarity?`, `sensitivity`). Fixes: 09_P7 §5.6 matcher pseudo-code emitted `matter.alert.v1` without the required `subject_ids`/`source_event_id` and dropped the `polarity` returned by `tenant_severity()` → added. 09_P7 envelope example used `"schemaversion":"2"` inside a `.v1` type (a major bump, which 01 §13 forbids within `*.v1`) → `"1.0"` (same for the 10_P8 `verification.completed.v1` example: `"1"` → `"1.0"`). |
| 6 | `ResearchQuery` → `EvidenceBundle` | P6/P10 → P5 (08 §2.4, 12 §2.2 O5); P5 → P6/P8 (07 §2.1–§2.2) | P5; P6 (08 §2.2), P8 (10 §2.1) | ✔ after **fix in P5** | 07_P5 §2.1 typed `residency_policy: "IN_ONLY"\|"ANY"`, but D9/01 §7.8, the TEC (§7.12) and P7's tenant/matter records use `IN_ONLY\|IN_PREFERRED\|ANY`, and P6/P10 copy the TEC value → P5 enum corrected. EvidenceBundle fields (`bundle_id evb_`, `issues[].issue_id` = `iss_` or `qry_…/i{n}` per D21.5, `items[].authority` = AuthorityView subset, `source_layer`, `trust_label` incl. `TENANT_COURT_RECORD`, `private{…}` on TPL items, `warnings[].kind` incl. the six D19.2 kinds) match 01 §7.9 and what P6/P8 read. Residual (not fixed, cosmetic): P5 marks `stance_target`, `requester`, `budget.max_*` optional where 01 §7.8 lists them as required; P5's defaults (BOTH, USER) make this harmless. 12_P10 I10 still called the P5 path `/research` → canonical `POST /p5/v1/retrieve` (alias noted, R-28). |
| 7 | `MatterContext` | P7 (09 §2.2 O1, §2.5-5) | P5 (07 §2.1), P6 (08 §2.2), P8 (10 §2.1) | ✔ | Every field P5/P6/P8 read (`client_role`, `forum`, `temporal_context`, `procedural_events[]`, `key_dates` fallback keys, `issues[]` `iss_`, `documents[].{trust_label, privilege_class, provenance, parsed_doc_uri}`, `fact_timeline[].status PROPOSED\|CONFIRMED\|DISPUTED`, `privilege_flags.outbound_forbidden_anchors_bloom`, `access_policy`, `residency_policy`, `deadlines[].lifecycle`) exists in 09_P7 and 01 §7.11 with the same enums. Minor optionality differences only (`temporal_context?` in P7 vs required in 01; it is derived). Also fixed a stale sentence in 09_P7 §2.0 claiming 01 §6.2 "still shows the pre-D20.16 `ten.{t}.` prefix" (it uses `tpl.<t>.`). |
| 8 | `Claim` → `VerifyRequest` → `VerificationReport` | P6 (08 §2.3–§2.4) ↔ P8 (10 §2.1 I1, §2.3 O1) | P8; P6, P10 | ✔ after **fixes in P6 and 01** | `Claim` identical in 08_P6, 10_P8 and 01 §7.15. Mismatch: 08_P6 §2.4 described `VerifyRequest` as `{memo_id, section, claims[], ledger_ref, as_of_legal_date, as_known_at, forum}`, whereas the owner (P8, 10 §2.1 I1) defines `{request_id, tenant_id, matter_id?, subject{kind, id, section?}, claims[], ledger_ref, evidence_bundle_ref?, matter_context_ref?, as_of_legal_date, as_known_at?, forum, jurisdiction_state?, lang_ui, budget, residency_policy, mode_flags?}` → 08_P6 rewritten to P8's shape. 01 §7.19 lacked `withheld_sections` (P8 emits it; D9 "withheld list") and `authority_snapshot[].reason_codes` → added. 01 §7.17 `StrategyMemo.verification` lacked `section_gates` and `degradations` which 08_P6 §2.3 carries (D9, D19.2; P10 must disclose) and `graph_watermark` → added. |
| 9 | `Deadline` | P6 (08 §2.3) | P7 (09 §2.3.6, §5.11), via `strategy.memo.published.v1.deadlines[]` | ✔ after **fix in P7** | Enums agree (P6 `Deadline.status` = input certainty; P7 `deadline.lifecycle` PROPOSED\|CONFIRMED\|DONE\|WAIVED\|MISSED, R-22). Gap: the event carries only `{deadline_id, computed_date, label}` while P7's row needs `due_on`, `kind`, `basis{anchor_id, computation_trace_id, trigger_date}`; no doc said how P7 fills them → 09_P7 §5.11 now states the mapping (`due_on` = `computed_date`, basis from `statutory_anchors[0]`/`trigger_event.date`, full Deadline read from `GET /p6/v1/memos/{memo_id}`, 01 §9.5). |
| 10 | `feedback.recorded.v1` (`FeedbackEvent`) → P9; `feedback.resolved.v1` back to P10 | P10, P6, P7 (12 §2.2 O1, 08 §2.5, 09 §2.2 O5) | P9 (11 §2.1, §2.4) → P10 (12 §2.1 I7) | ✔ after **fix in P9 + 01** | `FeedbackEvent` (target kinds incl. `REVIEW_TASK`, actions incl. `MICRO_REVIEW_ANSWER`, `surface` incl. the six P10 surfaces, `consent_snapshot_id`, `privilege_class`, `fb_`) identical in 11_P9 §2.4 and 01 §7.10; producers use the same names. Mismatch on the return event: 11_P9 §2.4 typed `feedback.resolved.v1.outcome` with an extra closed value `NEEDS_EVIDENCE` while claiming to be "identical to 01_master §6.4" (whose enum is `ACCEPTED\|REJECTED\|MERGED\|DEFERRED\|LOCAL_ONLY`, "needs evidence" = `DEFERRED` + note code per D21.11) → P9 enum and its §2.0 R-33 row aligned to 01 (no consumer used `NEEDS_EVIDENCE`). P9's optional `graph_watermark` (used to delay "fixed" until the badge cache catches up) was missing from 01 §6.4 → added there as optional. |
| 11 | `kg.proposal.v1` (`KgProposal`) | P9-global (11 §2.2, §2.4) | P3 (05 §2.1 I4, §5.10) | ✔ after **fix in P3** | Field names/enums identical in 11_P9, 01 §7.21 and what P3 reads. Mismatch: 05_P3 §5.10 review-priority formula read the D21.19 exposure signal as "`n_tenants_bucket` carried on `kg.proposal.v1`" and never named `exposure_bucket`, the field 01 §8.2 C20 says P3 relies on → P3 now reads `KgProposal.exposure_bucket` (with `support.n_tenants_bucket` as the tenant-count component). |
| 12 | `retrieval.served.v1` | P5 (07 §2.4, canonical per D21.9), P6 | P9 (11 §2.1, §2.4), P8 (10 §2.2) | ✔ after **fix in P9** | 07_P5 §2.4 = 01 §6.4 (tenant only in `tenantid`, `idempotencykey = impression_id`). 11_P9 §2.4 reproduced the schema "as the merged schema of 01_master §6.4" but omitted `requester`, `as_known_at`, `stance_target?`, `items[].role/status?/definitive?`, made `forum` optional and `rendered_at` required → P9 copy aligned to P5/01. |
| 13 | `doc.redacted.v1` → consumers, acked by `redaction.applied.v1` | P0 (02 §2.2A c), P1 (03 §2.2B), ops/legal | P1, P2, P3, P4, P5, P7, P8, P9, P10, replicas (each §2.1) → P0 ledger (02 §2.1 c3) | ✔ overlay fields; **fixed** ack contract | `RedactionOverlay` fields/enums (`scope`, `kind`, `spans[]`, `legal_basis.type`, `purge_sla{serving_h, derived_h, replica}`, `review_state`, `ovl_`) are identical in 02_P0, 03_P1, 04_P2, 06_P4, 13_XC and 01 §7.13; every consumer de-duplicates on `overlay_id`. Mismatch: **D22.4** (closing ruling, R-38) says each tenant cell acks once per overlay as `CELL:<cell_id>` against the control-plane cell registry, but 01 §6.2/§6.4, 02_P0 §2.1 c3, 09_P7 (§2.0, §2.4, O13), 11_P9 (§2.0, O-table), 12_P10 (§2.0, O9) and 13_XC `RedactionApplied` still had cells acking per phase as `P7`/`P9`/`P10` → all aligned: consumer enum `P1\|P2\|P3\|P4\|P5\|P8\|P9\|P10\|CELL:<cell_id>\|REPLICA:<id>`; PLC-side P9-global/P10-public keep their phase codes; cell-local stores are covered by the cell's single ack. *Interpretation to confirm (P7/P0 owners):* 09_P7 now says the cell ack is sent once all cell-local stores (P7, tenant P2, P5 caches, p9-tenant, P10 tenant stage) have applied the overlay; D22.4 does not name the emitting component. |
| 14 | `AuthorityView` (sync, Graph Query API) | P3 (05 §2.2 O4) | P5 (07 §2.1–2.2), P8 (10 §2.1), P10 (12 §2.3.1 CitatorBadge), P6 | ✔ after **fix in P5 example** | `subject_id` (not `target_id`), 5-valued `status`, `definitive`, `reason_codes` (P3 registry incl. `COVERAGE_GAP`, `TEXT_AWAITED`, integrity flags), `binding_on_forum` incl. `UNDETERMINED`, `binding_basis.conflict`, int64 `graph_watermark` agree across P3, P5, P8, P10 and 01 §7.7. The 07_P5 §2.2 example keyed `treatment_summary` with ad-hoc lowercase buckets (`followed`, `negative`) whereas the owner types it `Record<Predicate, number>` → example re-keyed to predicates. |

**Summary of the contract audit.** Of the 14 contracts, 2 matched with no field or enum defect (#3 `graph.delta.v1`, #7 `MatterContext`). The other 12 each had at least one naming, enum, optionality or coverage mismatch between producer, consumer and 01, and all were fixed in place with surgical edits (plus #4b, Freshness, found on the way). Four of those defects were in 01_master itself, where a passage lagged a D-ruling: `rhetorical_role.{conf,method}` vs D16, `verification.state` vs D5, `stage_lag_p95_min` vs D9, and the per-phase redaction ack code vs D22.4. None of the fixes removed content or citations.

### B.4 Additional interface fixes made while auditing (outside the 14, same edit rules)

| Where | Defect | Fix |
|---|---|---|
| 12_P10 §2.0 (topic row), 11_P9 §2.1 | Pre-D20.16 topic spellings survived although 01 §14 R-37 says D22.3 updated all phase docs: `tpl.<tenant>.interaction.v1`, `plc.digest.edition.v1`, `tpl.<tenant>.verification.v1` | → `tpl.<tenant>.interaction.logged.v1`, `plc.digest.edition.published.v1`, `tpl.<tenant>.verification.completed.v1`. A script comparing every `plc.*`/`tpl.<t>.*` topic in all docs against the 01 §6.2 topic map now finds only the deliberately quoted legacy names in 01 §13/§14 R-37 and the retired `plc.redaction.v1` mentions. |
| 01 §7.16 `Deadline` | Owner fields `rule_code` and `calendar_ref{forum, calendar_version}` (08_P6 §2.3; used for CourtCalendar rollover) missing from the cross-phase view | Added |
| 01 §7.18 `DraftArtifact.status` | P6 emits `STALE` (08_P6 §2.3 comment: "01_master §7.18 enum (+ STALE …)") but the canonical enum lacked it | Added `STALE` |
| 01 §6.4 `verification.completed.v1` | P8 emits `section_gates?` (10_P8 §2.3 O4) | Added as optional |
| 01 §8.2 C31 | Did not reflect D22.4 | Now cites D22.4 / R-38 (cell and replica ack codes) |

### B.5 Open issues (not fixed; need an owner decision)

1. **Who emits the per-cell `CELL:<cell_id>` redaction ack (D22.4).** The ruling fixes the consumer code and expected set but not the emitting component or the rule for aggregating inside a cell. 09_P7 now says the ack goes out once all cell-local stores have applied the overlay. P0 and P7 should confirm this and add a cell-internal completion check. Owners: P0, P7.
2. **`ResearchQuery` optionality drift.** 07_P5 marks `stance_target`, `requester` and the `budget.max_*` caps optional; 01 §7.8 lists them as required. This is harmless today because P5 applies defaults, but consumer-driven contract tests (01 §13.1) will flag it. Owner: P5. Either mark them optional in 01 or required in P5.
3. **Two mechanisms feed `Work.integrity_flags[]`.** 05_P3 I14 subscribes to `raw.captured.v1` (now listed in 01 §6.2). 03_P1 §2.0 says P1 exposes `withdrawn_at`/`suppressed_at` on the Work registry read path. Both are consistent with D19.5, but only one should be normative, to avoid double derivation. Owners: P1, P3.
4. **`matter.alert.v1` subject_ids for AUTHORITY_CHANGE.** 09_P7 §5.6 now emits `[root.target_id] + matched dependency ids`. P10's in-place update logic keys on `(alert_id, revision)`, so this is compatible, but P10 should confirm it does not also dedupe on `subject_ids`. Owner: P10.
5. **`residency_scores` keyed `IN_ONLY|ANY` only** (10_P8 §2.3 O3). It is not wrong, because scores are per endpoint class, but readers may expect the three-valued `residency_policy` enum. A one-line note in 10_P8 would help. Owner: P8.

### B.6 Files edited in this pass (interfaces lens)

01_master_architecture.md (§6.2 raw.captured and redaction.applied rows; §6.3 impact.detected `verification`/`text_awaited`; §6.4 redaction.applied, feedback.resolved, verification.completed; §7.1 rhetorical_role; §7.14 Freshness; §7.16 Deadline; §7.17 StrategyMemo; §7.18 DraftArtifact; §7.19 VerificationReport; §8.1 matrix P0→P3; §8.2 C4, C10, C31; §14 R-19) · 02_P0 (§2.1 c3) · 05_P3 (§2.1 I14, §5.10 priority, §11 item 12) · 06_P4 (§2.0 alias wording ×3) · 07_P5 (§2.1 residency enum, §2.2 treatment_summary example) · 08_P6 (§2.4 VerifyRequest) · 09_P7 (§2.0 topic and redaction rows, §2.2 O13, §2.4, §2.5 envelope example, §5.6 matcher emit, §5.11 deadline mapping) · 10_P8 (§2.3 O4 example schemaversion) · 11_P9 (§2.0 R-33 and redaction rows, §2.1 topic, §2.2 redaction row, §2.4 retrieval.served copy and feedback.resolved enum) · 12_P10 (§2.0 topic and redaction rows, §2.1 I10 and I12, §2.2 O9) · 13_cross_cutting (§1.3.1 `RedactionApplied.consumer`). After all edits: 29/29 Mermaid blocks parse and 369/369 tables have consistent column counts.

---

## C. Moat red-team, buildability and citation spot-check (QC lens: quality questions 2, 4, 5)

_Status: complete (30 Sep 2026). Lens: quality questions 2 (citations), 4 (buildability) and 5 (moat)._

**Summary.**
- **Moat (Q5).** Under red-team, only the *combination* M2 × M4 × M5 holds, and it holds only against a startup, and only if reviewer calibration, partner data rights, a multi-firm base and published quality figures are in place. Capital is not a barrier: our own build is ≈$90K of corpus cost inside an ≈$8.6–14M programme. Verdicts: M1 not a moat; M2 partially real; M3 not a moat alone; M4 partially real (00 overstated "compounding switching costs"); M5 partially real and execution-dependent; M6 not a moat but the only way to make M2/M4 visible. Against an SCC Online/Manupatra × Harvey alliance, plan on ~12 months, not 18–30. 00 was reworded accordingly, and six strengthening proposals (MS-1…MS-6) are listed. A reviewer-throughput inconsistency between 13 (7,000 reviews per reviewer-month) and 23 (3–5 editors for 100–300 items a day) means tier-1 HITL could cost ≈3–16× the $13.5K line. The conclusion is unchanged, but the owners should reconcile.
- **Buildability (Q4).** Average 4.4/5 across P0–P10. No phase needs a design session before sprint 1. The one design defect found was P5's stage latency budget (≈5 s p95) contradicting the spine's 2.5 s `EvidenceBundle` SLO; it is patched with a reconciliation note pending an owner ruling. The other biggest gaps are empirical or legal (portal feasibility, base rates, reviewer agreement, rule inventory, channel policy).
- **Citations (Q2).** 25 high-stakes claims were fetched and checked, with no material error in 00/01. Small fixes: the DPDP Rules date hedge in 02_P0, the doctrine-rule count in 00 (22→24), the Azure South India nuance in 00, and the CT-28 grade upgraded to verified. Two WebFetch summaries (a PDF and a long judgment) were wrong, and verbatim text was used instead. The earlier run's VLAIR/Stanford wording in 00 was re-checked and is correct.

**Files edited in place (surgical, nothing removed):** `00_executive_summary.md` (moat wording and conditions; doctrine-rule count; residency nuance), `02_P0_source_acquisition.md` (DPDP Rules date), `07_P5_retrieval_fusion.md` (latency reconciliation note under §5.13), `20_competitive_teardown.md` and `24_bibliography.md` (CT-28 grade).


### C.1 Moat red-team (quality question 5: "is the moat real, or copyable in 6 months?")

**Method.** Read 00 "The moat, stated honestly", 20 §6–§7 (M1–M6, threat scenarios S1–S5, competitive minimums) and 01 §12 (AD-01…AD-30), then argued as two attackers with a 6-month clock:
- **Attacker A: SCC Online or Manupatra plus Harvey.** They hold 25 years of editorial treatment metadata (Manupatra claims its corpus shows whether judgments "have been overruled or distinguished", 20 §3.2 [CT-4]), the citation strings the bar uses, ManuWorks as a live firm workspace (20 §3.2 [CT-5]), and Harvey's firm-wide presence at SAM and AZB (verified above, C.3 #7) with a Bengaluru engineering office (C.3 #23). The template is the LexisNexis–Harvey alliance, which already put Shepard's and the Shepard's Knowledge Graph inside Harvey (C.3 #22).
- **Attacker B: a $20M Indian startup.** It has open inputs: the CC-BY High Court dataset of 17.8M PDFs (C.3 #3), the public doctrine (every rule in 21 §4.1 is a published judgment), and this blueprint's own method, which is described in enough detail to copy.

**The single most important red-team fact comes from our own numbers.** The whole one-time corpus and graph build costs ≈$90K at 5M documents, including only **$13.5K (19 reviewer-months) of human review of tier-1 edges** (13 §3.3), with reviewers budgeted at ≈$700 per reviewer-month (23 U-08). The full 30-month programme is ≈$8.6–14M (22). **Capital is therefore no barrier to either attacker.** A $20M startup can fund our entire programme, and an incumbent already employs editors. Every durable element has to rest on something money cannot buy quickly: elapsed calendar time, calibrated judgment, exclusive relationships, or a public track record.

#### C.1.1 Element-by-element: the 6-month copy attempt and a verdict

All attacker timelines and "what they reach" entries are this reviewer's inference (as in 20 §6.2), built on the cited facts. They are not measured.

| # | Element (20 §6.2) | Attacker A (incumbent + Harvey), 6-month play | Attacker B ($20M startup), 6-month play | What they reach in 6 months | Verdict |
|---|---|---|---|---|---|
| M1 | Paragraph-anchored, bitemporal, clean-title corpus | Skip it. They already own curated text with reporter paragraphing and do not need to redistribute to third parties. | Ingest the CC-BY HC dataset plus SC/eSCR, build court-paragraph anchors, and license nothing. | A: nothing to copy (they have an equivalent). B: SC + major HCs anchored, without alias stability across re-parses. | **Not a moat.** It is an enabler, plus IP hygiene that matters only for *our* API redistribution (I11/I12). Anchor stability across 25 HC formats is 6–12 months of engineering, not a barrier. |
| M2 | Verified, proposition-level treatment ledger with `AuthorityView` / `binding_on_forum` as of any date | Convert editorial "overruled / distinguished" notes into typed case-level edges; put 20–50 existing editors on SC tier-1 negatives; encode the doctrine rules (all public). Ship "overruled / distinguished" flags inside Harvey. | Hire 30 law graduates (≈$21K/month at the doc-13/23 rate), run an LLM cascade (the 68–79% treatment accuracy in C.3 #19 is available to everyone), and copy the 24 rules from the case law. | A: **case-level** negative flags for SC and major HCs, credible to buyers, within 3–6 months. Proposition-level partial overrulings, forum-relative binding, stays and pending references would *not* be there yet. B: a noisy typed graph; reviewers not yet calibrated (no κ history). | **Partially real.** It is real against B for ~12–18 months because of reviewer calibration time and the doctrine engine. Against A it is thin, because buyers cannot see the difference between proposition-level and case-level treatment unless we *measure it publicly* (see M6). The "reviewer-hours" framing overstates the barrier: hours are cheap, and what is scarce is *calibrated* hours plus an audited error record. |
| M3 | Point-in-time statutes + crosswalk carried through the graph | Buy or build the table (public). Point-in-time central Acts from their existing amendment notes. | Build the table in ≈540 reviewer-hours (21 §10.2; ≈$2K of review); point-in-time for central Acts. | Both reach table + basic point-in-time. Carrying IPC-era treatment to BNS with `change_type` needs M2. | **Not a moat alone** (agrees with 20). It is a strong *feature* for a 2026–2028 window while pre-2024 offences are still being tried. |
| M4 | Matter-linked propagation (broadcast `impact.detected.v1` → tenant Impact Matcher → `matter.alert.v1`) | ManuWorks (20 §3.2) or Harvey Vault (a document store of up to 100,000 files per vault, per Harvey's help centre, help.harvey.ai/en/articles/9558438-vault, `snippet`) already hold firm documents. Extract citations from uploaded drafts and memos and alert when a cited case gets a new negative editorial flag. That is a KeyCite-Alerts-style feature (per-document monitors, 12_P10 [P10-2]): 3–6 months. | Same feature on its own workspace, 6 months. No installed base of loaded matters. | A: a **case-level** "your cited authority was just overruled" alert on uploaded documents, i.e. most of the *visible* value. Missing: paragraph and proposition precision (it fires on partial overrulings that do not touch the relied-on holding), forum relativity, and a provisional→confirmed→retracted lifecycle. | **Partially real.** 00's "compounding switching costs" is overstated. Matter files are the firm's and are portable (re-upload is days). The stickiness is (i) alert *precision*, which depends on M2, (ii) the alert and audit history and lawyer annotations, and (iii) workflow integration (Word add-in, digests). Durability is medium, not high, until alert precision is shown to beat case-level alerts. |
| M5 | Partner gold set + feedback flywheel through the Privacy Gate | Harvey can run the same programme *now* with SAM/AZB (20 §6.2 already concedes this). Incumbents have many firm relationships. | Sign any mid-size firm; lawyer-authored rubrics in 3–6 months. | A: a comparable single-firm gold set within 6–9 months. | **Partially real and execution-dependent.** Two structural limits: (1) the cross-tenant S2 signals need **k ≥ 5 firms** (D9), so before GA (month 18) the flywheel is single-firm S0/S1 only and does not "compound" across firms; (2) nothing in the plan gives us exclusivity. The value is the *rubric and the gold labels*, and a partner firm can do the same with Harvey. |
| M6 | Public, reproducible Indian benchmark + track record | Publish a benchmark in 3 months (anyone can). | Same. | A benchmark, but no multi-quarter record. | **Not a moat by itself, but the only way M2 and M4 become visible to buyers.** Only the *track record* (quarters of held-out results, audited) cannot be backfilled. |
| — | The combination M2 × M4 × M5 | Alliance path: case-level M2 from editorial notes + Harvey's workspace for M4 + SAM/AZB for M5. Reaches "good enough for most buyers" in ≈9–12 months. | 18–24 months to match all three at our bar. | — | **Real only against B, and only if the conditions in C.1.2 hold.** Against A, 20 §6.4 rates the alliance "medium–high within 12–24 months", so the expected lead is nearer 12 months than 18–30. |

#### C.1.2 What must be true operationally for the moat to hold

1. **Calibrated review, measured before it is relied on.** 3–5 editors clearing ≈100–300 tier-1 items a day with a 4-hour SLA on SC items, plus Hindi-reading reviewers (23 §3.3). The 4-week M1–M2 pilot queue must show inter-reviewer κ and throughput. Until it does, "verified ledger" is a plan, not an asset.
2. **Partner hours and data rights in writing before the gold build.** ≈3,000–3,500 partner lawyer-hours in Year 1 (10; 23 §3.3). The Design Partnership Agreement must grant (a) the right to keep and reuse S0/S1 codes and the gold labels after termination, and (b) a time-limited exclusivity on co-developing an Indian legal-AI evaluation set with a competing vendor (see C.1.3).
3. **At least five firms before the cross-tenant flywheel is claimed.** S2 aggregates need k ≥ 5 tenants (D9). Second and third firms are planned for months 9–12 (23 §3.3), so cross-firm compounding starts after GA, not before.
4. **Time on the clock.** Our own GA is month 18 (22). "Lead" can only mean time-to-copy *after* a competitor sees the product. It is not a head start over a competitor that starts building today.
5. **Lawful sources.** The counsel opinions on CAPTCHA-gated portals and on the derivative-data status of the open datasets (00 risk 1) must come back clean. Otherwise M1 shrinks to what the attackers also have.
6. **Visible quality.** Negative-treatment recall and precision, alert precision and time-to-alert must be published per court (M6), or buyers will score an incumbent's case-level flags as equivalent.

#### C.1.3 Concrete strengthening proposals **[NOVEL — unvalidated]**

| # | Proposal | Why it helps | Owner / where |
|---|---|---|---|
| MS-1 | **Aim M2 where incumbents' static editorial notes are weakest:** HC and tribunal negative treatment (ITAT, NCLT/NCLAT, CESTAT), Hindi-language HC judgments, and *dynamic* statuses (interim stays, pending references to larger benches, recalls). Publish per-court coverage for these. | Case-level editorial flags cannot express these, so a 6-month copy by Attacker A misses exactly what we measure. | 05_P3, 21 §4, 10_P8 |
| MS-2 | **Publish a "partial-overruling" sentinel suite** in the benchmark: cases where a later bench overrules one holding and leaves others intact, and alerts where the relied-on paragraph is or is not affected. Report alert precision against a case-level-alert baseline. | Turns the M2 + M4 precision gap into a number a buyer can see. Without it the copy looks equivalent. | 10_P8 (I10), 12_P10 |
| MS-3 | **Contract for exclusivity and retention** in the DPA: 24–36 months of exclusive co-development of the Indian evaluation set; perpetual rights to de-identified S0/S1 codes and gold labels; a named-hours schedule. Get a competition-law check on the exclusivity clause (Competition Act 2002 s.3 vertical agreements) *(unverified whether needed)*. | Converts M5 from "a relationship anyone can replicate" into a time-bounded exclusive asset. | 10_P8 §5.13, 11_P9, 23 |
| MS-4 | **Sign 3–5 partner firms across practice areas by month 12**, not only after GA. Offer the D2 cell at cost to firms 2–5 in exchange for gold-set hours. | Makes the k ≥ 5 S2 flywheel real before GA and reduces the single-firm bias flagged in 20 M5. | 22, 23 §3.3 |
| MS-5 | **Pre-empt the alliance through distribution.** Offer the PLC Access API/MCP (`AuthorityView` subset) to Harvey and Lucio as soon as M2 coverage passes the partner's practice areas, with the R8 anti-harvesting controls (quotas, canary assertions, no proposition text). | If we are the Indian citator inside Harvey, S1 becomes a channel. The alternative is that SCC or Manupatra fills that slot. This resolves 20 §8.R open item 5 in favour of *earlier*. | 20 §7.1 I12, 22 |
| MS-6 | **Track moat KPIs in the roadmap:** human-verified tier-1 edges and their audited precision; negative-treatment recall on sentinels; live matters monitored; alerts acted on and alert precision; firms with signed data-rights agreements; benchmark quarters published. | 22 mentions the moat once (§ principle 7) but has no moat KPI. A moat that is not measured cannot be managed or pitched. | 22 |

#### C.1.4 Edits made to 00 (wording only; no content removed)

- "The moat is the verified treatment ledger…" → now says the moat is the *combination*, and that capital is not the barrier (≈$90K corpus build inside an ≈$8.6–14M programme that a funded startup can afford).
- M2 bullet: "grows only with reviewer-hours and time" → "calibrated reviewer-hours, elapsed time and an audited error record". Reviewer-hours are cheap; calibration and track record are not.
- M4 bullet: "compounding switching costs" → switching costs that rise with alert precision, alert and audit history, and workflow integration, because matter files are portable.
- M5 bullet: added that cross-firm (k ≥ 5) signals only start once five firms are live.
- "Estimated lead" → restated as time-to-copy *after a competitor sees the product* (our own GA is month 18), with the alliance case (~12 months, rated medium–high likelihood in 20 §6.4) as the planning case. Added the operating conditions and a pointer to this section.

**Inconsistency found (not edited; owners 13 and 23).** The HITL cost line in 13 §3.2–3.3 assumes **7,000 reviews per reviewer-month** at $700 (≈320 tier-1 reviews per reviewer per working day, ≈1.5 minutes each). 23 §3.3 and 05 staff the same queue at **3–5 editors for ≈100–300 tier-1 items a day** (≈20–100 per editor-day, i.e. ≈440–2,200 a month). A tier-1 negative-treatment decision (which proposition, bench-strength check, evidence span) is unlikely to take 1.5 minutes. At 23's rate the ≈133K prioritised reviews behind the $13.5K line would need ≈60–300 reviewer-months, i.e. ≈$42K–$210K at the same monthly rate, and more if SC-level editors cost more than $700. This does **not** change the moat conclusion (still small against an ≈$8.6–14M programme), but 13's HITL line and the 4-week pilot's throughput target (23 U-08) should use one number. 00 now calls the $13.5K a planning figure that could overrun several-fold.

**Open for the owners (not edited):** 20 §6.2 should (a) downgrade M4 durability from "High" to "Medium–high, conditional on alert precision beating case-level alerts", (b) note the k ≥ 5 limit under M5, and (c) add a row or footnote that the full build costs ≈$90K, so capital is not a barrier. 20 §6.3's "18–30 months" should carry the same basis note as 00.

### C.2 Buildability of §5 (quality question 4: "would a senior engineer know exactly what to build?")

**Method.** For each phase doc P0–P10, §5 was checked for six things: (1) a component inventory with technology; (2) data structures and schemas (DDL, TypeScript or JSON, in §5 or referenced from §2); (3) algorithms or pseudo-code; (4) storage choices; (5) SLOs with numbers; (6) an MVP cut in §10 with scope and, where given, staffing. The check combined a structural scan (sub-section inventory; counts of DDL, typed schemas, pseudo-code blocks, Mermaid diagrams and SLO rows) with targeted reads of each doc's components, storage, SLO and MVP sub-sections and its §11 open questions. Cross-doc SLO consistency was checked against 13 §6 and 01_master §11.

**Scale:** 5 = buildable as written, with only empirical tuning left; 4 = buildable, but one named artefact or decision is missing and would stall a sprint; 3 = an engineer would need a design session first; ≤2 = not buildable.

| Phase | (1) Components | (2) Schemas | (3) Algorithms | (4) Storage | (5) SLOs | (6) MVP | Score | Single biggest gap |
|---|---|---|---|---|---|---|---|---|
| **P0** Acquisition | ✔ §5.3; adapter plug-in contract §5.5 | ✔ 15 DDL tables in §2; JSON/YAML adapter specs | ✔ `nfp` change detection, scheduling, breakers | ✔ S3 WARC, Postgres, Kafka via outbox, Temporal | ✔ freshness per tier (§5.13; 13 §6.2) | ✔ 8–10 wk, 2 eng + counsel; explicit "not in MVP" list | **4** | **The HC real-time path is unproven.** The MVP names 6–8 HCs for own-site delta, but only Delhi (open listing) and Allahabad (RSS) were observed working. Bombay, Madras and Kerala were unreachable from non-Indian egress; the eCourts judgments portal is CAPTCHA-gated; and the AWS HC dataset lags 2–3 months. The ≤6 h HC freshness and alert SLOs therefore rest on adapters whose feasibility is a week-1 test (§11 Q4). The DATASET_ONLY disclosure is the correct fallback, but the per-HC feasibility matrix must exist before M1 scope is fixed. |
| **P1** Parsing | ✔ §5.14 table with runtimes and scaling | ✔ 13 DDL in §2; `ocr.page.v1`; task contracts | ✔ dual-reader OCR consensus, citation grammar, anchor alignment | ✔ S3 derived and parsed; partitioned Postgres `anchor` (~300M rows) | ✔ per-lane p50/p95 (§5.15); anchor API p95 40 ms | ✔ 3–4 mo, 1 ML + 2 BE + annotators; M0 10K sample | **4** | **Rhetorical-role (ratio/obiter) labels are unproven.** The MVP trains on public data plus a 150-judgment gold set, and §11 Q6 asks whether lawyers can even agree on ratio at κ ≥ 0.6. P3's proposition extraction consumes `rhetorical_role ∈ {RATIO, ANALYSIS}`, so this is the upstream risk to M2. The OCR engine choice is also deferred to IC-OCR-Bench, though a default stack is named. |
| **P2** Indexing | ✔ §5.1; Index Access Layer §5.12 | ✔ DDL in §2; TS IAL interfaces | ✔ chunking invariants I1–I5, generation/outbox reconciliation | ✔ OpenSearch (BM25 + on-disk k-NN) + Postgres chunk SoR; capacity at 5M/20M (§5.14) | ✔ full SLO table (§5.15) | ✔ component-by-component MVP/full table | **5** | Chunk and vector counts rest on corpus assumptions A1–A5 (±2×, §11 Q2) until P1's M0 profile lands. The embedder has a default (Qwen3-4B) and a bake-off rule, so it is not a blocker. |
| **P3** Knowledge graph | ✔ §5.1 | ✔ 13 DDL in §5.3 (bitemporal assertions, `logical_key`, reason-code registry) | ✔ cost cascade L0–L3, proposition extraction steps 1–5, `tau_prop_match` fallback when no pin cite, JTMS retraction | ✔ PG18 SoR + CSR projection (§5.13) | ✔ Graph API per-endpoint latencies; HITL SLAs | ✔ MVP/full table incl. predicates and doctrine subset | **5** | **Base rates are unmeasured** (mentions per judgment, negative-treatment prevalence, daily tier-1 volume; §11 Q4). They set HITL staffing (3–5 editors) and L3 spend, which are the moat's operating cost. Measure in sprint 1 as planned. |
| **P4** Propagation | ✔ §5.1 event topology | ✔ 11 DDL in §5.14 | ✔ closure algorithm §5.5.2, early-cutoff recompute, storm control, campaigns runbook | ✔ Kafka 4 KRaft + outbox, Postgres ledger, Temporal | ✔ §5.15 per-flow table nested in 13 §6.2 | ✔ MVP/full table | **5** | Prospective and conditional overruling scope (`temporal_scope`, `date_basis`) is not yet reliably extractable (§11 Q1). The MVP correctly maps these to UNCERTAIN, so it is a quality gap, not a build gap. |
| **P5** Retrieval | ✔ §5.1; stateless services §5.15 | ✔ TS in §2; YAML plan config; no SoR by design | ✔ RRF → cross-encoder → relevance-gated utility U = r²·A → monotone LTR; adverse sweep | ✔ config in Postgres; bundle snapshots and LTR logs in TPL object store | ⚠ **stage budget broke the spine SLO** (see note) | ✔ MVP/full table | **4** | **Latency budget inconsistent with the platform SLO.** P5 §5.13 STANDARD sums to ≈5 s p95 (7 s with a corrective round), while 00, 01_master §11 and 13 §6.1 fix `EvidenceBundle` p95 at 2.5 s with a 400 ms decomposition and 500 ms stance. **FIXED (reconciliation note added under P5 §5.13):** build to the 2.5 s split (small-model decomposition, classifier stance, corrective round outside the SLO and reported as a degradation), or revise the SLO explicitly. The owner must still rule. Second gap: ≈1,500 graded issues are needed for monotone LTR (§11 Q3). |
| **P6** Strategy | ✔ §5.1, agent catalogue §5.3 | ✔ DDL ×3; RuleSpec YAML; `Deadline`, `MaintainabilityCheck` | ✔ Procedural Clock evaluator pseudo-code §5.5.2; closed-world citation ledger | ✔ PLC rule registry; Temporal workflows | ✔ milestone p50/p95 table; memo p95 ≤ 15 min | ✔ MVP triggers (s.138 NI, GST SCN, civil suits) and ~40 RuleSpecs | **4** | **The ~40 MVP RuleSpecs are not inventoried.** The format and two worked rules (NI Act s.138/142, Arbitration Act s.34) are specified, but the MVP rule list with statutory anchors is not, and §11 Q1 lists anchors still unverified (NI Act s.143A/147, CPC O.VIII r.1, CGST s.107/169, Income-tax Act 2025 mapping, BSA s.63). The rule inventory is the P6 artefact a legal engineer needs on day 1. |
| **P7** Workspace | ✔ §5.1; TEC §5.2 | ✔ 19 DDL in §2; OpenFGA model (`schema 1.1`) in §5.7 | ✔ ingestion pipeline, dependency index, tenant-side impact matching | ✔ bridge model (pooled schema + FORCE RLS; dedicated cells), per-tenant KMS + per-matter DEK, WORM audit | ✔ via §5.14 and 13 §6.1 | ✔ MVP/full table | **4** | **Automated court tracking has no lawful path yet.** eCourts case status and cause lists are CAPTCHA-gated and the NJDG API is government-only (§11 Q7), so the brief's "matter tracking, hearing dates" runs on manual entry plus P0's SC/HC feeds in the MVP. The DMS connector priority is also unknown (§11 Q5). |
| **P8** Verification | ✔ §5.1 table with tech per component | ✔ TS objects (`VerificationReport`, `EvalCase`, `EvalRun`); no DDL (Postgres + object store named) | ✔ check ladder C0–C12 with thresholds, pinpoint re-anchoring, calibrator, non-inferiority gate | ✔ Redis + Postgres cache isolated per tenant+matter; gold store | ✔ latency table fitting 25 s p95 | ✔ MVP with gold-set sizes and staffing | **5** | Hindi and cross-lingual entailment has no qualified checker (no Indian legal NLI set exists; §11 Q2), so cross-lingual VT1 claims route to humans. That is a known quality and cost gap. Minor: persisted tables for reports and eval runs are TS-only (no DDL or partitioning). |
| **P9** Feedback | ✔ §5.1 | ✔ 5 DDL in §2; TS allowlist | ✔ Privacy Gate algorithm §5.5.2; anti-poisoning; IPS LTR | ✔ tenant-plane feedback store; gate ledger | ✔ §5.14 | ✔ MVP (S0+S1 only) with staffing | **4** | **The S2 parameters are placeholders.** ε budget and k thresholds await a formal privacy analysis (§11 Q5). S2 is post-MVP, but it is the cross-firm half of the M5 flywheel (see C.1), so the analysis should be scheduled before GA, not after. |
| **P10** Product surface | ✔ §5.1 | ✔ 3 DDL in §2; TS view models | ✔ Watch Matcher, digest ranking, alert fatigue and escalation rules | ◐ thin in §5 (BFF + tenant plane named; storage mostly inherited from P7) | ✔ §5.15 performance budgets (800 ms search, 25 s verified) | ✔ screen-by-screen MVP table | **4** | **Channel and deployment decisions are unverified:** WhatsApp template and pricing policy, SMS DLT registration (§11 Q2–Q3) and the Word add-in path (Exchange Online vs on-prem, §11 Q5). All are needed for the alert and drafting surfaces in M1. |

**Average 4.4 / 5.** Every phase has components, schemas (in §2 or §5), named algorithms, storage and SLO targets, and an MVP cut. No phase needs a design session before sprint 1. The recurring pattern is that the *biggest gap is empirical or legal, not architectural*: base rates (P3), corpus profile (P1/P2), portal feasibility (P0/P7), reviewer agreement (P1) and counsel opinions. The roadmap already sequences these into M0 (22 §3.2). The one true design defect found, the P5 latency budget, is patched with a reconciliation note pending an owner ruling.

### C.3 Citation spot-check (primary sources fetched 30 Sep 2026)

Verdicts: **OK** = the blueprint's statement matches the source; **FIXED** = wording corrected in place; **NOTE** = accurate but with a caveat recorded here.

| # | Claim (doc) | Source fetched | Verdict |
|---|---|---|---|
| 1 | Stanford RegLab: 17% hallucination for Lexis+ AI, 33% for Westlaw AI-Assisted Research; "hallucination" includes misgrounded answers; leading causes naive retrieval, inapplicable authority, reasoning errors (00; 01 AD-16) | arXiv 2405.20362 abstract + HTML v1 (Table 6; definition "incorrect or misgrounded") | **OK.** Per-tool figures are from the paper body (abstract says "between 17% and 33%"). Ask Practical Law AI also 17%. Note: the error-cause shares differ by tool (reasoning errors are the largest share for Westlaw, 61%), so "leading causes" is fair as a set. |
| 2 | VLAIR Oct 2025: 200 US questions; all four AI products incl. ChatGPT at 74–78% weighted; lawyer baseline 69%; specialists ahead by ~6 pts on authoritativeness; Lexis+ AI and Westlaw absent; ChatGPT's own weighted score not printed (00; 20 §6.1) | vals.ai/industry-reports/vlair-10-14-25 | **OK.** Participants were Alexi, Counsel Stack, Midpage and ChatGPT; ChatGPT scored 80% on accuracy. The earlier-run fix to 00 is correct and stays. |
| 3 | Open HC dataset: 17.8M PDFs, ≈1.25 TiB, grows ≈1.4M/yr (00; 01) | github.com/vanga/indian-high-court-judgments STATS.md (snapshot 1 Jun 2026) | **OK.** 17,771,420 PDFs; 1,276.94 GiB; 1,380,115 (2024) and 1,428,922 (2025) PDFs; 25 courts / 45 benches. |
| 4 | "As of September 2026 there is no in-India processing for Claude" (00 row 9; 01 [MA-13]) | platform.claude.com data-residency doc | **OK.** `inference_geo` accepts only `"us"` and `"global"`; workspace geo only `"us"`. |
| 5 | Claude on Bedrock in India is global cross-Region inference only (01 [MA-14]) | AWS ML Blog, 9 Mar 2026 | **OK.** Only `global.` profiles; no India geographic profile for Claude. |
| 6 | In-India OpenAI on Bedrock (00 row 9; 01 [MA-15]) | AWS ML Blog, 27 Aug 2026 | **OK.** GPT-5.6 models with an India geographic profile routing only between ap-south-1 and ap-south-2. These are proprietary models, so "OpenAI-on-Bedrock" is the right label (not "open-weight"). |
| 7 | SAM and AZB deployed Harvey firm-wide in 2025 (00; 20 §3.15) | amsshardul.com (3 Jun 2025, "all seven of its offices"); Bar & Bench (10 Sep 2025, "across all its offices") | **OK.** |
| 8 | DPDP Rules 2025 timeline (09_P7; 13; 02_P0) | MeitY gazette PDF G.S.R. 846(E) dated 13 Nov 2025, r.1(2)–(4); PIB backgrounder (announced 14 Nov 2025) | **OK in 09_P7/13** (Rules 1, 2, 17–21 immediate; r.4 at one year; rr.3, 5–16, 22, 23 at eighteen months = 13 May 2027). **FIXED in 02_P0 §5 (line ≈527):** removed "exact notification date not confirmed" and stated G.S.R. 846(E) of 13 Nov 2025. Caution for future reviewers: a WebFetch summary of the PIB PDF hallucinated "4 November 2025" and a wrong rule split; the raw PDF text was used instead. |
| 9 | Kùzu archived (00 row 2; 05 [P3-44]) | github.com/kuzudb/kuzu | **OK.** Archived 10 Oct 2025 after final v0.11.3 ("Kuzu is working on something new"). |
| 10 | BNSS s.531 saves pending proceedings (00; 21 §6.1) | indiankanoon.org/doc/74791982 (s.531(1), (2)(a), (2)(b), (3)) | **OK.** (2)(a) text and (3) no-revival of expired periods match 21 §6.1. |
| 11 | *Parvinder Singh v. ED*, 2026 INSC 519 (19 May 2026), paras 28–29 (21 §6.2; 01 [MA-21]) | indiankanoon.org/doc/46844204 | **OK.** Para 28 ("meant to give a prospective application … must meet its logical conclusion under the CrPC itself") and para 29 ("would definitely enure to the benefit of an accused…") match. |
| 12 | *EBC v. D.B. Modak*, (2008) 1 SCC 1, para 41: copy-edited text not protected; paragraph segregation, internal numbering and concurring/dissenting annotations protected (00 row 1; 20 M1; 21) | indiankanoon.org/doc/1062099 (plus the full text saved by an earlier run, `scratchpad/modak.html`) | **OK.** Para 40 rejects copyright in copy-edited inputs; para 41 opens "However, the inputs … in (i) segregating … (ii) adding internal paragraph numbering … (iii) indicating … concurring … dissenting … have to be viewed in a different light". Caution: the WebFetch summariser mis-stated (c) as unprotected; the verbatim para 41 text was checked instead. |
| 13 | *Dawoodi Bohra*, (2005) 2 SCC 673, propositions (1)–(3) incl. both exceptions (21 rul 04–05; 05 B2; 07 §5) | indiankanoon.org/doc/708017 | **OK.** 5 judges, 17 Dec 2004. (1) larger-strength law binds lesser or co-equal benches; (2) a lesser bench cannot dissent and can only ask the CJ; a co-equal bench may doubt and refer; (3) exceptions for the CJ's roster power and a larger bench already seized. |
| 14 | *Kunhayammed v. State of Kerala*, (2000) 6 SCC 359, conclusions (i), (iv), (v) (21 rul 10) | indiankanoon.org/doc/1940266 | **OK.** 3 judges, 19 Jul 2000. No merger on refusal of leave, whether speaking or not; a speaking order's statement of law is Art. 141 law; merger after leave is granted (conclusion (vi)). |
| 15 | *Kusum Ingots*, (2004) 6 SCC 254: an HC order on a Parliamentary Act's validity has all-India effect (21 rul 24) | indiankanoon.org/doc/1876565 | **OK.** Verbatim quote matches (3 judges incl. CJ, 28 Apr 2004). |
| 16 | *State of Punjab v. Rafiq Masih* (8 Jul 2014): Art. 142 directions are not precedent (21 rul 23) | indiankanoon.org/doc/154195973 | **OK.** Para 11 quote matches. |
| 17 | PostgreSQL 18 temporal keys (00 row 2; 01 AD-04 [MA-5]) | postgresql.org/docs/18/release-18.html | **OK.** `WITHOUT OVERLAPS` for PK/UNIQUE and `PERIOD` for FKs; released 25 Sep 2025. |
| 18 | Azure South India serves in-India OpenAI (00 row 9; 13 §4 table) | MS Learn region-availability page (updated 4 Sep 2026), parsed per deployment type | **OK in 13** (regional Standard: gpt-4.1-mini, gpt-4o; Regional Provisioned up to gpt-5.1 / gpt-5.4-mini; Data Zone Standard is APAC-wide). **FIXED in 00 row 9:** added that Azure South India regional deployments list only older models and gpt-5.1 needs provisioned capacity, while the frontier in-India option is Bedrock GPT-5.6. |
| 19 | Precedent-treatment classification only 68–79% accurate (05 abstract; 01 [MA-18]) | arXiv 2605.17691 (Demir & Canbaz, NLLP 2025) | **OK.** 79.1% (Gemini 2.5 Flash, coarse) and 67.7% (GPT-5-mini, fine-grained). |
| 20 | Pinpoint errors are the hard case, 37–61% caught (01 AD-20 [MA-30]) | arXiv 2608.12571 (Verma) | **OK.** 37–61% on court opinions; 52–83% on briefs; wrong-case 93–100%. |
| 21 | "On Indian prior-case retrieval, dense retrievers underperform BM25" (00 row 5; 01 AD-14 [MA-28]) | IL-PCSR (arXiv 2511.00268), Table of results (local full text from an earlier run) | **OK, with scope note.** PCR F1: BM25 5-gram 33.29 vs best single semantic model 24.67 (Para-GNN) and SAILER ≤ 19.37. For *statute* retrieval the semantic models win (Para-GNN 32.85 vs BM25 ≤ 18.59), and lexical+semantic ensembles beat both. The claim is right as stated (prior-case only). |
| 22 | LexisNexis–Harvey alliance incl. Shepard's (00; 20 S1 [CT-34]) | lexisnexis.com press release, 18 Jun 2025 | **OK.** US case law, statutes, Shepard's Citations and the Shepard's Knowledge Graph / Point of Law graph. |
| 23 | Harvey Bengaluru office (20 S1 [CT-28], graded `snippet`) | harvey.ai blog, 10 Jul 2025 | **OK; upgradeable to verified.** Engineering, sales and operations teams; "deepen our ability to serve the Indian legal market". |
| 24 | *Trimurthi Fragrances v. Govt of NCT of Delhi* (SC, 5-J, 19 Sep 2022): bench strength counts judges, not the size of the majority (21 rul 06) | indiankanoon.org/doc/85806537 (raw text) | **OK.** "the majority decision of a Bench of larger strength would prevail over the decision of a Bench of lesser strength, irrespective of the number of Judges constituting the majority", relying on *Jaishri Laxmanrao Patil*. |
| 25 | *National Insurance v. Pranay Sethi*, (2017) 16 SCC 680, para 30: per incuriam test; "an earlier decision of co-equal Bench binds the Bench of same strength" (21 rul 07; 05 B2) | indiankanoon.org/doc/139996215 (raw text) | **OK.** The quote and the two per-incuriam limbs are in para 30 (IK numbering). |

**Citation-check summary.** 25 claims checked against primary or first-party sources (16 of them from 00_executive_summary and 01_master; 8 legal holdings from 21_india); 0 material errors found in the high-stakes set. Three wording fixes were made (02_P0 DPDP date hedge; 00 doctrine-rule count 22→24; 00 Azure South India nuance). Two WebFetch summaries (PIB DPDP PDF, EBC v. Modak) were wrong and were overridden by the verbatim source text, so any earlier "verified" grade that rested only on a WebFetch summary of a PDF or long judgment deserves a verbatim re-check.

