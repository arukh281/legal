# 02 — Workflows and Rules

**What this file is.** This file lists every candidate trigger type for the corporate-law MVP. For each one it gives:
- the deterministic **RuleSpecs** behind the Procedural Clock (capability 4), with statutory anchors;
- the strategy-memo outline (capability 3);
- the reply skeleton or para-wise grid (capability 6).

The front matter (§0–§7) is the normative summary. Parts A–D are the four research packs, kept nearly verbatim so that every operative quote and source stays attached to its rule.

**Law as at 1 October 2026.** Every rule carries a verification status. **No deadline in this file was produced by an LLM.** Each one either quotes a statutory provision or regulation that a researcher read, or is marked TO VERIFY WITH PARTNER.

> **Access caveat that affects activation.** indiacode.nic.in, egazette.gov.in and sci.gov.in were unreachable from the research sandbox: Akamai 403s, TLS failures and resets. The blueprint already recorded geo-blocking of non-Indian egress on these sites (02_P0). Statute text was therefore read from regulator-hosted official consolidations (IBBI, SEBI, CCI, ED, the MCA/NCLT-hosted Gazette copy) or from Indian Kanoon. **Indian Kanoon is not a safe point-in-time source.** Its pages print the un-notified 2019 rewrite of Arbitration Act s.11 as if in force, and carry stale texts of NI Act, Commercial Courts Act and Specific Relief Act sections (Part D §0, "Ingestion hazard"). Every rule marked VERIFIED-SECONDARY must therefore be **re-anchored against the India Code or Gazette text from an Indian network in weeks 1–3** ([09](09_first_two_weeks.md)) before it can be activated.

---

## 0. RuleSpec fields and status legend

Each RuleSpec (`prs_…` in the data model, keyed by `rule_code`) has these fields:
- trigger event, i.e. what starts the clock;
- computation;
- nature;
- statutory anchor (operative words quoted, with URL);
- settling case law;
- verification status;
- golden test vectors (only where the computation is verified);
- notes.

The engine is specified in [03](03_data_model_and_contracts.md); the conventions are in §3 below.

| Nature | Meaning | How the product shows it |
|---|---|---|
| **HARD** | Statutory limit; no condonation power | Red deadline with the computed date; "no extension available" |
| **CONDONABLE (cap N)** | Base period plus a capped condonation window (e.g. "within a further period not exceeding 15 days") | Base deadline (red) and outer limit (amber) labelled "condonation discretionary; sufficient cause must be shown". Never present the outer limit as the deadline. |
| **CONDONABLE (no cap)** | Base period; the forum may condone without a statutory cap | Base deadline (red), plus "late filing needs a condonation application; no statutory cap" |
| **DIRECTORY** | A timeline for the authority or tribunal that courts have held directory | Grey "target, not a deadline" with the authority cited |
| **ORDER-SET** | The period is fixed by the notice or order itself, sometimes within a statutory band | The date is read from the document by extraction (with quote) and **must be confirmed by a lawyer**. The engine only checks it against the statutory floor or ceiling. |
| **PRACTICE** | No statutory period; the date is whatever the notice demands, or firm practice | Shown as a reminder, never as a legal deadline |

| Verification status | Meaning | Can it be activated? |
|---|---|---|
| **VERIFIED-PRIMARY** | Operative words read in an official text (statute, Gazette, regulator consolidation) | Yes, after a partner lawyer signs off on the rule card |
| **VERIFIED-SECONDARY** | Full text read on a reliable secondary host, or quoted in an SC judgment | **Only after re-anchoring to the official text** (§0 caveat) plus lawyer sign-off |
| **TO VERIFY WITH PARTNER** (TVP) | Unsettled, forum-specific, or seen only in a snippet | **Never computes a date.** Shown as "verify manually", with the open question attached. |

**Activation record.** A RuleSpec becomes `ACTIVE` only when its row has `anchor_verified_at`, `anchor_text_hash` (hash of the official text quoted), `signed_off_by` (a partner lawyer) and a passing golden-vector suite ([06](06_test_set_plan.md) §5.2). Anything less leaves the rule `DRAFT`, and the UI says "verify manually".

---

## 1. Trigger catalogue and default ranking (the partner re-ranks in week 1)

**Full mode** means:
- the trigger's activated RuleSpecs compute deadlines;
- a trigger-specific issue template, evidence checklist and reply skeleton are used;
- it is covered by 5–6 gold matters ([06](06_test_set_plan.md)).

**General mode** means:
- the same memo pipeline with a generic issue template;
- **no computed deadlines**: a clearly labelled banner "General mode — no deadline guarantee", plus a list of *statutory periods that may apply*, each with its anchor and status, none computed into a date;
- a generic reply skeleton.

| ID | Trigger | Forum | Our side | Rule readiness (from Parts A–D) | Default rank (hypothesis) |
|---|---|---|---|---|---|
| T-IBC-1 | s.8 demand notice received | pre-NCLT | Corporate debtor | s.8(2) 10-day reply VERIFIED-PRIMARY; s.9(1) earliest filing VERIFIED-PRIMARY | **1 (IBC pack)** |
| T-IBC-2 | s.9 petition (operational creditor) | NCLT | Either | Threshold, s.10A bar, Art.137 limitation and s.215(3) IU pre-filing verified; the NCLT reply period is ORDER-SET (r.37 says only "before the date of hearing") | **1 (IBC pack)** |
| T-IBC-3 | s.7 petition (financial creditor) / s.10 | NCLT | Either | s.7 admission is **point-in-time** (two versions either side of 26.05.2026), verified | **1 (IBC pack)** |
| T-IBC-4 | Appeal to NCLAT (s.61) / SC (s.62) | NCLAT, SC | Either | s.61(2) 30 + 15 and s.62 45 + 15 verified; the SC confirmed a golden vector | **1 (IBC pack)** |
| T-ARB-3 / T-ARB-4 / T-ARB-2 | s.34 challenge; s.37 appeal; s.9 interim relief | HC / commercial court | Either | s.34(3) 3 months + 30 days "but not thereafter"; s.37 60 days (CCA s.13(1A)); s.9(2) 90 days. **All VERIFIED-SECONDARY: re-anchor first.** | **2 (arbitration pack)** |
| T-CA-1 / T-CA-2 | s.241–242 oppression and mismanagement; appeals s.421(3)/s.423 | NCLT, NCLAT, SC | Either | Appeals verified (45 + 45; 60 + 60). s.244 eligibility verified. **Reply/rejoinder dates are ORDER-SET.** Limitation article contested (TVP). | **3** |
| T-SEBI-1 / T-SEBI-2 | SEBI SCN; settlement application; SAT appeal; SC appeal | SEBI, SAT, SC | Noticee | SCN reply ORDER-SET (≥ 14 days, r.4(1)); settlement 60 days **HARD** since 14.01.2022; SAT 45 days (no cap); SC 60 + 60 — all VERIFIED-PRIMARY | **4** |
| T-CA-3 / T-CA-4 | ROC adjudication SCN; RD appeal; compounding | ROC/AO, RD, NCLT | Company / officers | SCN reply ORDER-SET (15–30 days); RD appeal 60 days, HARD (no condonation power found); s.454(8) 90 days; compounding has no limitation | General mode; cheap to promote |
| T-COMP-1 | CCI investigation / NCLAT appeal | CCI, NCLAT, SC | Either | DG-report objections 8 weeks; s.53B 60 days (no cap, 25% pre-deposit); s.53T 60 days — VERIFIED-PRIMARY | General mode |
| T-FEMA-1 | FEMA adjudication / appeal / compounding | AA, SDA, AT, HC | Noticee | SCN ≥ 10 days ORDER-SET; ss.17/19 45 days (no cap); s.35 60 + 60; compounding payment 15 days **HARD** — VERIFIED-PRIMARY | General mode |
| T-COM-1 | Commercial suit summons | Commercial court / HC | Defendant | WS 30 days, forfeited after 120 (*SCG Contracts*); s.12A mediation — VERIFIED-SECONDARY | General mode (strong candidate for rank 4 if the partner litigates commercial suits) |
| T-CON-1 | Contract-breach legal notice | — | Recipient | **No statutory reply deadline** (PRACTICE); suit limitation Arts 55/113 etc. VERIFIED-SECONDARY | General mode |
| T-NI-1 | s.138 NI Act notice | Magistrate | Drawer (company / directors) | Provisos (b), (c) and s.142(1)(b) VERIFIED-SECONDARY; BNSS s.223 pre-cognizance hearing is contested | General mode (needs a minimal BNSS note) |
| T-ARB-1 / T-ARB-5 | Invocation notice; s.11; s.29A timelines | Arbitral / HC | Either | s.11 30-day waits (2015 text in force; 2019 rewrite **not notified**); s.29A 12 + 6 months — VERIFIED-SECONDARY | Folded into the arbitration pack |

**Why this default ranking (to be replaced by the partner's).**
- (a) **IBC first.** It is the highest-volume corporate dispute type in NCLT. Its rules are mostly VERIFIED-PRIMARY from IBBI-hosted official texts. It also carries the mandated point-in-time test case (IBC (Amendment) Act 2026).
- (b) **Arbitration second.** Most corporate contracts route disputes to arbitration, and s.34/s.37 deadlines are unforgiving ("but not thereafter"). Its rules still need re-anchoring.
- (c) **Oppression and mismanagement third.** It is core corporate practice, but its own clock is mostly ORDER-SET, so the Procedural Clock adds less than for IBC.
- (d) **SEBI fourth.** It applies if the partner has a listed-company practice. Its rules are clean and primary.

The sensitivity rule: if the partner ranks T-COM-1 or T-CA-3 above SEBI, swap them. Their rules are already drafted and verified to the same level.

**Cost of promoting a general-mode trigger later.** Once the engine and pipeline exist, promotion takes about 2–3 engineer-days plus 1–2 lawyer-hours for sign-off and 3–5 gold matters. The work is:
- activate the verified rules;
- write the issue template and reply skeleton;
- add golden vectors.

---

## 2. What the Procedural Clock does (and never does)

1. **The LLM extracts; it never computes.** From the uploaded trigger document, extraction proposes candidate trigger events. Each candidate has an exact-substring quote and a page/anchor. Examples: "date of receipt of demand notice", "date of order", "date copy made available", "date of service". Exact-substring validation is per 09_P7.
2. **A lawyer confirms the trigger date** in one click, or corrects it. Until it is confirmed, the deadline shows as `PROPOSED`, never as a deadline.
3. **The engine computes.** It takes the active RuleSpecs, the confirmed trigger date, the court calendar and the conventions in §3. The output is a `Deadline` (`ddl_`) with a full computed-by trace: rule, anchor, convention steps and calendar used.
4. **ORDER-SET dates** are not computed. They are taken from the notice or order (quoted) and confirmed by the lawyer. The engine only validates them against any statutory floor or ceiling. Example: a SEBI penalty SCN giving fewer than 14 days from service raises a "below statutory minimum" flag (r.4(1), Part C).
5. **Point-in-time.** The rule version in force on the relevant date is selected:
   - for appeals: the date of the order;
   - for the pre-2026 vs post-2026 s.7 admission rule: the date of the step (Part A §8);
   - the stored `valid_from`/`valid_to` of each RuleSpec version decides it.
6. **Never.** No deadline is shown from a TVP rule. No outer condonation limit is shown as "the deadline". No holiday is assumed without a calendar row.

## 3. Shared computation conventions (harmonised across Parts A–D)

| ID | Convention | Anchor | Status |
|---|---|---|---|
| CV1 | Exclude the first day for periods running "from" a date | General Clauses Act 1897 s.9(1) | VERIFIED-PRIMARY (Part A) |
| CV2 | Exclude the trigger day for "of" / "within N days of" | *Saketh India v India Securities*, AIR 1999 SC 1090 | VERIFIED-SECONDARY |
| CV3 | Limitation Act s.12(1): exclude the day from which the period is reckoned; applies via IBC s.238A, Companies Act s.433, SEBI Act s.15W and Arbitration Act s.43 | LA s.12(1); *Sanket Kumar Agarwal* (2023); *Himachal Techno* | VERIFIED-SECONDARY |
| CV4 | Months and years by corresponding calendar date ("British calendar"), never n × 30. Clamp to month-end when there is no corresponding day. The policy for a trigger on the last day of a shorter month (30 Apr → 30 Jul vs 31 Jul) is to show the earlier date with a sensitivity row. | GCA s.3(35), s.3(66); *Himachal Techno* para 11 | VERIFIED-SECONDARY; clamp and edge policy **TVP** |
| CV5 | Court closed on the last day: roll forward to reopening (LA s.4) **for the base limitation period only**, never for a capped condonation window | LA s.4; *Sagufa Ahmed*; *Tata Steel v Raj Kumar Banerjee* 2025 INSC 639; *My Preferred Transformation* 2025 INSC 56 | VERIFIED-PRIMARY (s.4) / VERIFIED-SECONDARY (cases) |
| CV6 | Offices (ROC/AO/RD) and acts outside the Limitation Act: GCA s.10 next-open-day rollover. Whether an always-on e-filing platform is "closed" on holidays is TVP. | GCA s.10(1) | VERIFIED-PRIMARY (text) / TVP (platforms) |
| CV7 | E-filing stops the clock (NCLAT) | *Sanket* paras 19–21 | VERIFIED-SECONDARY |
| CV8 | Service by registered post is deemed in the ordinary course of post unless the contrary is proved | GCA s.27 | VERIFIED-PRIMARY |
| CV9 | COVID exclusion 15.03.2020–28.02.2022 (historical triggers only) | *In re Cognizance for Extension of Limitation* (2022) 3 SCC 117 | **TVP** (snippet only) |
| CV10 | Calendars: no holiday is hard-coded. The `court_calendar` table is seeded manually from official holiday lists for SC, NCLAT, NCLT benches, SAT and the three HCs ([08](08_cut_list_and_upgrade_path.md) §3). Golden vectors give the raw date and the weekday. | blueprint 08_P6 §5.5.2 | — |

## 4. Draft outputs (common structure; trigger specifics in Parts A–D)

Every memo is a `StrategyMemo` of `Claim[]` ([03](03_data_model_and_contracts.md)). Its sections map one-to-one to the core experience in the brief:

| Section | Content |
|---|---|
| 1. Opponent's claims | Each claim with the paragraph of the trigger document it comes from (RECORD_FACT claims with private anchors) |
| 2. Issues | From the trigger's issue template plus extraction; lawyer-confirmable |
| 3. Favourable law and precedents | EvidenceBundle items with AuthorityView badges and binding-for-forum |
| 4. Adverse authority | Mandatory. Each binding or persuasive adverse item needs a disposition: distinguish, concede, or argue inapplicable. Otherwise the memo cannot PASS (08_P6). |
| 5. Strongest counter-arguments and likely opposing arguments | From one opposing-counsel pass and one rebuttal round |
| 6. Evidence and documents to prepare | Trigger checklist plus matter-specific items |
| 7. Deadlines and limitation | From the Procedural Clock only, with traces; general mode shows the banner |
| 8. Draft response strategy | STRATEGIC_OPINION claims that depend on grounded claims |
| 9. Uncertainties and verification report | Withheld or unverified items |

**Reply skeleton or para-wise grid** (DOCX export, capability 6):
- **Header block:** forum, parties, matter number, and a "DRAFT — for lawyer review" watermark.
- **Preliminary objections:** maintainability, limitation, jurisdiction. Each objection carries its anchors.
- **Para-wise grid:** one row per paragraph of the incoming document. Columns:
  - para no. and quote;
  - response: ADMITTED, DENIED, NOT WITHIN KNOWLEDGE or MATTER OF RECORD (lawyer chooses; the system suggests);
  - our response text, with claims linked to the memo;
  - supporting authorities and record documents (anchors).
- **Prayer / relief skeleton.**
- **List of documents** from the evidence checklist.

The trigger-specific skeletons are in Parts A–D under "Draft output".

## 5. Consolidated TO VERIFY WITH PARTNER list (feeds [07](07_partner_firm_questions.md))

**IBC (Part A)**
1. Whether the 2026 "record reasons" timelines and new s.61(6) (NCLAT three-month disposal) are directory.
2. Whether substituted s.7(5) ("shall admit") applies to s.7 petitions pending on 26.05.2026.
3. Whether IBBI regulations make the s.215(3) IU pre-filing workable now.
4. The meaning of "receipt" under s.62.
5. NCLT reply practice per bench (r.37: "before the date of hearing").
6. How courts treat contested s.8 delivery.
7. The COVID exclusion (CV9).

**Companies Act (Part B)**
1. Which limitation article governs s.241 (Art.113 vs Art.137; *Chalasani* 2024 calls it a mixed question).
2. Whether a website upload counts as "made available" under s.421(3).
3. Whether LA s.4 rollover applies to condonation windows.
4. How GCA s.10 applies to the e-adjudication platform.
5. RD practice on late appeals.
6. The current CAP Rules text (2024 Gazette) and platform URL.
7. Whether s.441(6)(a) wording survived the 2020 amendment.
8. A s.423-specific ruling.

**SEBI / SAT / Competition / FEMA (Part C)**
1. ss.11/11B directions-only SCN and interim-order objection periods (PRACTICE).
2. SAT procedure-rule amendments after 2005, the SAT holiday calendar, and the "one month" arithmetic.
3. The scope of the s.22A proviso.
4. NCLAT/SDA/AT applicability of LA s.4.
5. CCI penalty-SCN periods.
6. The CCI commitment-window transition (orders received before 18.08.2026).
7. First-day exclusion for regulations (not Acts).
8. Boundary days for 3-year bars.
9. Whether the FEMA Adjudication Rules text is current.
10. LODR reg 30 disclosure of a SEBI SCN.

**Arbitration / commercial / NI (Part D)**
1. Whether Mediation Act s.64 (s.12A rewrite) has been notified.
2. The consequence of missing s.9(2) in Delhi, Bombay and the partner HC.
3. Whether s.23(4) is directory.
4. LA s.12(2) for CCA s.13 appeals.
5. GCA s.10 for the WS 120-day limit.
6. The "three months" month-end edge policy (CV4).
7. Whether s.138(b) is satisfied by dispatch within 30 days.
8. SRA s.20 and Order XXXVII texts.
9. The BNSS s.223 pre-cognizance hearing for s.138 complaints (HCs differ).
10. The s.143A commencement date and *Rakesh Ranjan*.
11. HC original-side rules.

## 6. Corrections to the brief found during research

| # | Brief said | Finding | Part |
|---|---|---|---|
| 1 | IBC 2026: "14-day admission timeline for s.7" came into force 26.05.2026 | The 14 days has been in s.7(4) since 2016. The change in force from 26.05.2026 is s.7(5): "**shall** … admit" (was "may"), plus Explanation I (no other ground to reject) and Explanation II (IU record suffices for financial institutions). This closes the *Vidarbha* discretion. | A, C3 |
| 2 | Not in force: Ch. IV-A ss.58A–58K, s.59A, s.240B, s.240C | Correct, but also not in force: Amendment Act s.7, ss.34(a)(i)–(ii), 45, 47, 60, 67 (IBC Fund), 69(b), 70(b)(xx). A LiveLaw article claiming the creditor-initiated process was "operationalised" is contradicted by the S.O. text and **must not be ingested as authority**. | A, C4–C5 |
| 3 | Also in force from 26.05.2026 (not in brief) | s.215(3) mandatory IU filing before s.9; s.67C civil penalty for concealing a dispute; s.64A frivolous proceedings; new s.61(6); s.12A withdrawal rewritten; fast-track Chapter IV omitted | A, C7 |
| 4 | Corporate Laws (Amendment) Bill 2026 "referred to a JPC" | Bill No. 85 of 2026; introduced and referred 23.03.2026; **JPC report presented 03.08.2026; not passed by either House**. Watchlist only. It would add a 10% pre-deposit for RD-level appeals (new s.454D) and raise RD compounding to ₹1 crore. | B |
| 5 | s.244 "100 members / one-tenth" | Full test: 100 members or one-tenth of members, whichever is less, or members holding one-tenth of issued capital (calls paid); one-fifth of members for companies without share capital; joint holders count once | B |
| 6 | CCI (General) Regulations 2009 | Replaced by the CCI (General) Regulations 2024 (17.09.2024). The commitment-application window is now 60 days (from 18.08.2026). | C |
| 7 | FEMA compounding "Rules 2000" | Superseded by the Foreign Exchange (Compounding Proceedings) Rules 2024 (G.S.R. 566(E)). RBI Master Direction No. 04/2025-26. | C |
| 8 | — | SEBI Settlement Regulations 2026 approved by the Board on 24.09.2026 but **not notified**; the Securities Markets Code 2025 is pending. Both are watchlist only. | C |
| 9 | Blueprint s.34 RuleSpec rollover | LA s.4 rollover applies to the three-month end only, **not** to the 30-day window (*My Preferred Transformation*) | D, C5 |
| 10 | Blueprint: *Patil Automation* prospective date "assumed" | Verified: effective **20.08.2022** (para 84) | D, C1 |

## 7. Point-in-time test case summary (IBC (Amendment) Act 2026)

- **Act No. 6 of 2026:** assent and Gazette 06.04.2026.
- **S.O. 2625(E):** dated 22.05.2026, published 25.05.2026, appointed day **26.05.2026**.
- **The test suite** (Part A §8.3) checks two things:
  - The system answers differently for steps before and after 26.05.2026. Examples: s.7(5) "may" vs "shall"; s.215(3) "may" vs "shall".
  - For each enacted-but-not-notified provision, it answers "enacted, **not in force** as of <date>". These are Ch. IV-A, s.59A, s.240B, s.240C and the others listed in §6 row 2.
- **These are zero-tolerance items** in [06](06_test_set_plan.md) §5.6.
- **No consolidated version yet.** IBBI has not published a consolidated post-2026 Code. The MVP builds `provision_text@date` itself from Act 6 of 2026 and S.O. 2625(E). That is the integration test for the bitemporal ledger.

---

*Parts A–D follow. Reference tags are prefixed per part to avoid collisions: `I-R` (IBC), `C-R` (Companies), `S-R` (SEBI/competition/FEMA). Part D keeps its own prefixes `AR-`, `CC-`, `NI-`, `GL-`, etc.*



---

# Part A — IBC

*Source pack title: IBC rules pack: triggers T-IBC-1 to T-IBC-6 (MVP deadline and strategy rules)*

Research date: **2026-10-01**. Researcher: IBC rules agent. Format: RuleSpec, as defined in mvp_brief.md and blueprint 08_P6 §5.5.1.
Status legend: **VERIFIED-PRIMARY** means I read the statute, notification or judgment text and quote the operative words. **VERIFIED-SECONDARY** means I read the full text on a reliable secondary host (Indian Kanoon, an IBBI-hosted copy of an NCLT order, ca2013.com). **TO VERIFY WITH PARTNER** means the point is not settled or rests on a search snippet only.
Reference tags are listed in §10: `verified` / `snippet` / `unverified`.

---

### 0. Summary of findings and corrections to the brief

| # | Brief said | What the primary text shows | Source |
|---|---|---|---|
| C1 | Assent 6 April 2026 | **Correct.** Act No. 6 of 2026. Assent and Gazette publication were both on **6 April 2026** (Gazette of India Extraordinary, Part II s.1, No. 11, CG-DL-E-06042026-271594). Some secondary sources say "published 7 April". That is the date IBBI uploaded the file, not the Gazette date. | [I-R1] |
| C2 | S.O. 2625(E), 22 May 2026, in force 26 May 2026 | **Correct.** Published in Gazette Extraordinary Part II s.3(ii), No. 2533 on **Monday 25 May 2026**. The appointed day is **26 May 2026**. | [I-R2] |
| C3 | "14-day admission timeline for s.7 came into force 26 May 2026" | **Misleading.** The 14-day period has been in s.7(4) since 2016 ("shall, within fourteen days of the receipt of the application ... ascertain the existence of a default"), and s.7(4) still contains it. The 2026 Act (Amendment Act s.4) did three things. (i) It omitted the s.7(4) proviso. (ii) It substituted s.7(5), so the Adjudicating Authority (AA) now "**shall**, within fourteen days ... by an order (a) **admit** ... or (b) reject". Before, it "**may**, by order, admit". (iii) It added a second proviso (record reasons for delay), **Explanation I** ("no other ground shall be considered to reject") and **Explanation II** (an information utility (IU) record of default is sufficient for financial institutions). The real change is that **admission becomes mandatory once debt and default are shown**, which legislatively closes the Vidarbha discretion. The 14 days probably remain directory, because the only consequence of missing them is that reasons must be recorded. That point is TO VERIFY. | [I-R1] s.4; [I-R4] s.7 |
| C4 | Not notified: Ch. IV-A ss.58A–58K, s.59A, s.240B, s.240C | **Correct but incomplete.** Ch. IV-A is ss.58A–58H, **58-I**, 58J, 58K. Also NOT in force: Amendment Act **s.7** (adds "or Chapter IV-A" to Code s.11(ba)); **s.34(a)(i)–(ii)** (references to the creditor-initiated process (CIIRP) in s.54A); **s.45** (s.65(3)); **s.47** (s.67A); **s.60** (s.208(1)(cb)); **s.67** (s.224, the Insolvency and Bankruptcy Fund, a substantive change); **s.69(b)** (rule-making heads in s.239(2)); **s.70(b)(xx)** (regulation-making heads for Ch. IV-A). No later commencement notification appears on IBBI's notifications page (latest entry 8 Jul 2026, an appointment). | [I-R2], [I-R3] |
| C5 | — | A LiveLaw article dated 26 May 2026 says the notification "operationalises" the CIIRP. **This is contradicted by the S.O. text**: Amendment Act s.40, which inserts Ch. IV-A, is not in the list. The MVP must not ingest that article as authority. | [I-R31] vs [I-R2] |
| C6 | ₹1 crore threshold "by default date" | S.O. 1205(E) of 24.03.2020 is verified. It is silent on timing. NCLAT (*Jumbo Paper Products v Hansraj Agrofresh*, CA(AT)(Ins) 813/2021, as quoted by NCLT benches) keys the threshold to the **date of filing**, not the date of default. *Madhusudan Tantia* (NCLAT) was distinguished because both its notice and its filing pre-dated 24.03.2020. | [I-R7], [I-R29] |
| C7 | — | Also in force from 26.05.2026 and directly relevant to the triggers: **s.215(3)** (an operational creditor (OC) "**shall, before filing an application under section 9**", submit financial information to an IU; previously "may"); **s.67C** (civil penalty of ₹1 lakh–₹2 crore on an OC that conceals a notice of dispute in a s.9 application; replaces the s.76 offence, which is omitted); **s.64A** (penalty for frivolous or vexatious Part II proceedings); **new s.61(6)** (NCLAT "shall dispose of the appeal within three months"); **s.12A substituted** (post-admission withdrawal only on RP's application, not before CoC constitution and not after the first invitation for resolution plans); **Ch. IV fast-track (ss.55–58) omitted**. | [I-R1], [I-R2] |

---

### 1. Source baseline and point-in-time method

- **Pre-2026 text:** IBBI's consolidated Code "upto 12.08.2021" [I-R4]. IBBI's Act listing [I-R5] shows no amending Act between the IBC (Amendment) Act 2021 and the 2026 Act; the 2025 Bill introduced on 12 Aug 2025 became the 2026 Act. So the 12.08.2021 text is the operative text up to 25.05.2026 for ss.4, 7–10, 10A, 12, 12A, 14, 61, 62, 215 and 238A. *Assumption:* no Finance Act or other Act amended these sections between 2021 and 2026. A partner should spot-check this on indiacode.
- **Post-2026 text:** apply Act 6 of 2026 [I-R1] provision by provision, filtered by S.O. 2625(E) [I-R2]. IBBI has **not yet published a consolidated post-2026 Code** (its Act page still lists the 12.08.2021 consolidation as the latest). The MVP's bitemporal ledger must therefore build `provision_text@date` itself. That is a good integration test (§8).
- **Rules:** IBC (Application to Adjudicating Authority) Rules 2016 ("AAA Rules"), as amended up to 24.09.2020 [I-R6]. IBBI's rules listing shows no later AAA Rules amendment.

### 2. Shared computation conventions (apply to every IBC RuleSpec)

| Convention | Rule | Anchor | Status |
|---|---|---|---|
| CV1 First-day exclusion ("from") | "it shall be sufficient, for the purpose of excluding the first in a series of days ... to use the word 'from'". | GCA 1897 s.9(1) [I-R27a] | VERIFIED-PRIMARY |
| CV2 First-day exclusion ("of", "within N days of") | The Supreme Court holds that where time is given "from a certain date" or "of" a date, "the day on that day is to be excluded". Applied to "within one month of the date". | *Saketh India v India Securities*, AIR 1999 SC 1090 [I-R26] | VERIFIED-SECONDARY |
| CV3 Limitation Act exclusion | s.12(1) LA: "the day from which such period is to be reckoned, shall be excluded". Applied to s.61(2) IBC via s.238A: the date of pronouncement is excluded. | *Sanket Kumar Agarwal v APG Logistics* (SC, 1 May 2023) paras 23–24 [I-R22] | VERIFIED-SECONDARY |
| CV4 Court-closure rollover | s.4 LA: "Where the prescribed period ... expires on a day when the court is closed, the ... appeal or application may be ... made on the day when the court reopens". NCLAT Rules 2016 r.3 gives the same next-working-day rule. **The rollover applies to the limitation period only, NOT to the condonable extension.** | LA s.4 [I-R27c]; *Sagufa Ahmed v Upper Assam Plywood* paras 21–23 [I-R25]; *Tata Steel v Raj Kumar Banerjee*, 2025 INSC 639, paras 10.1–10.2 [I-R24] | VERIFIED-PRIMARY (s.4) / VERIFIED-SECONDARY (cases) |
| CV5 Service by post | Service by registered post is deemed "effected at the time at which the letter would be delivered in the ordinary course of post" unless the contrary is proved. | GCA s.27 [I-R27b] | VERIFIED-PRIMARY |
| CV6 COVID exclusion | The period 15.03.2020–28.02.2022 is excluded from limitation. Where limitation expired inside that window, 90 days from 01.03.2022 (or the longer balance). | *In re Cognizance for Extension of Limitation*, order of 10.01.2022, (2022) 3 SCC 117 [I-R30] | **TO VERIFY WITH PARTNER** (snippet only; affects computations whose window spans 2020–22) |
| CV7 Court calendar | NCLT and NCLAT bench calendars come from P0 `CourtCalendar`. This pack hard-codes no holidays. Golden vectors give the **raw date before rollover** and state when rollover would apply. | blueprint 08_P6 §5.5.1 | — |
| CV8 E-filing | Limitation stops on **e-filing**. NCLAT order of 24.12.2022: physical copy within 7 days of e-filing. | *Sanket* paras 19–21 [I-R22] | VERIFIED-SECONDARY (current NCLAT standard operating procedure (SOP): TO VERIFY) |

---

### 3. T-IBC-1: s.8 demand notice received by our client (corporate debtor)

**event_type vocabulary:** `IBC_DEMAND_NOTICE_DELIVERED` (OC side), `IBC_DEMAND_NOTICE_RECEIVED_BY_CD` (CD side; usually the same day), `IBC_DISPUTE_NOTICE_SENT`.

#### IBC.S8.DEMAND_NOTICE_FORM_SERVICE (maintainability check, not a deadline)
```yaml
code: IBC.S8.DEMAND_NOTICE_FORM_SERVICE
kind: MAINTAINABILITY_CHECK
applies_when: { statute_basis_any: ["wrk_IBC2016#sec-8"], client_role_any: [CORPORATE_DEBTOR, OPERATIONAL_CREDITOR] }
checks:
  - "Notice in Form 3, OR copy of invoice attached with notice in Form 4"            # AAA Rules r.5(1)
  - "Delivered (a) at the registered office by hand, registered post or speed post with acknowledgement due; or
     (b) by electronic mail service to a whole time director or designated partner or key managerial personnel"  # r.5(2)
  - "Copy of demand notice/invoice filed with an information utility, if any"        # r.5(3)
  - "Default is of an operational debt; amount of default ≥ ₹1 crore (assessed at filing date)"  # s.4 + S.O.1205(E); see IBC.S4.THRESHOLD
anchors:
  - "IBC s.8(1): 'An operational creditor may, on the occurrence of a default, deliver a demand notice of unpaid operational debt or copy of an invoice demanding payment ... in such form and manner as may be prescribed.'"  # [I-R4] (IBBI consolidation has the typo 'operational debtor copy')
  - "AAA Rules 2016 r.5(1)–(3)"  # [I-R6]
verification: VERIFIED-PRIMARY
notes: >
  Rule 5(2) uses "may be delivered". Whether a mode not listed (courier, or email to someone other than a WTD, DP or KMP)
  is fatal is a question of fact and NCLAT practice: TO VERIFY WITH PARTNER. The GCA s.27 presumption covers registered
  post only. Not amended by the 2026 Act; Code s.8 itself is unamended.
```

#### IBC.S8.DISPUTE_REPLY (the corporate debtor's 10-day window)
```yaml
code: IBC.S8.DISPUTE_REPLY
version: 1.0.0
valid_from: 2018-06-06        # current s.8(2) wording ("if any, or"; "payment") after Act 26 of 2018; window itself since 2016-12-01
applies_when: { statute_basis_any: ["wrk_IBC2016#sec-8.ss-2"], client_role_any: [CORPORATE_DEBTOR] }
trigger_event: IBC_DEMAND_NOTICE_RECEIVED_BY_CD   # CD's receipt; burden: OC must prove delivery (s.9(3)(a), s.9(5)(i)(c)); GCA s.27 presumption if RPAD
period: { value: 10, unit: DAYS }
computation:
  exclude_first_day: true            # CV2 (statute says "of the receipt"); Saketh India
  court_closure_rollover: false      # reply goes to the OC, not to a court or office; GCA s.10 / LA s.4 do not apply
output: { window_kind: LAST_DATE, label: "Last day to bring to OC's notice: dispute / pending suit or arbitration / payment" }
nature: HARD                         # statutory window, no condonation mechanism (see notes on consequence)
anchors:
  - "IBC s.8(2): 'The corporate debtor shall, within a period of ten days of the receipt of the demand notice or copy of the invoice ...
     bring to the notice of the operational creditor— (a) existence of a dispute, if any, or record of the pendency of the suit or
     arbitration proceedings filed before the receipt of such notice or invoice in relation to such dispute; (b) the payment of unpaid
     operational debt— (i) by sending an attested copy of the record of electronic transfer ... or (ii) ... attested copy of record that
     the operational creditor has encashed a cheque ...'"   # [I-R4]
  - "IBC s.5(6): '\"dispute\" includes a suit or arbitration proceedings relating to (a) the existence of the amount of debt;
     (b) the quality of goods or service; or (c) the breach of a representation or warranty'"   # [I-R4]
case_law:
  - "Mobilox Innovations v Kirusa Software, (2018) 1 SCC 353, para 24: '... the existence of the dispute and/or the suit or arbitration
     proceeding must be pre-existing – i.e. it must exist before the receipt of the demand notice or invoice'"   # [I-R10]
  - "Mobilox para 40: AA must reject if notice of dispute received; 'all that the adjudicating authority is to see at this stage is
     whether there is a plausible contention which requires further investigation and that the \"dispute\" is not a patently feeble legal
     argument or an assertion of fact unsupported by evidence ... So long as a dispute truly exists in fact and is not spurious,
     hypothetical or illusory, the adjudicating authority has to reject the application.'"   # [I-R10]
  - "Mobilox para 29 (reading 'and' as 'or'): dispute need not already be in a suit or arbitration. (2018 amendment then substituted 'if any, or'.)"  # [I-R10]
  - "Kay Bouvet Engineering v Overseas Infrastructure Alliance, AIR 2021 SC 4199: applies Mobilox; dispute shown by the CD's reply to the
     demand notice and material on record; s.9 application rejected"   # [I-R11]
verification: VERIFIED-PRIMARY (period) / VERIFIED-SECONDARY (first-day convention, case law)
tests:   # computation verified: 10 days, first day excluded, no rollover
  - { trigger: 2026-06-01, expect: 2026-06-11 }   # Thu
  - { trigger: 2026-06-25, expect: 2026-07-05 }   # Sun: no rollover (not a court filing); UI should advise sending by Fri 2026-07-03
notes: >
  (1) Consequence of missing the window: the OC may file under s.9 once the 10 days have run (IBC.S9.EARLIEST_FILING). Whether a CD
  that did not reply can still rely in its s.9 reply on a dispute that pre-existed the notice and is evidenced on record is
  TO VERIFY WITH PARTNER. Kay Bouvet looked at the reply and the record; s.9(5)(ii)(d) speaks of "notice of dispute has been
  received by the operational creditor or there is a record of dispute in the information utility". The engine must therefore
  present day 10 as the action date.
  (2) A dispute raised for the first time AFTER receipt is not "pre-existing" (Mobilox para 24). The memo must date-stamp every
  dispute document against the receipt date.
  (3) 2026 Act: s.8 unamended. New s.67C (in force 26.05.2026) penalises an OC that conceals the CD's notice of dispute in its s.9
  application (₹1 lakh–₹2 crore). The reply should be sent so that it is provably received (RPAD + email), to set up s.67C/s.9(5)(ii)(d).
```

#### Draft output for T-IBC-1 (CD side)
**Strategy memo must contain:**
1. *Their claim:* OC identity; whether the debt is an operational debt (s.5(20)/(21)); invoices; amount; claimed date of default; notice form (Form 3/4), mode and date of delivery, and to whom.
2. *Deadlines block:* IBC.S8.DISPUTE_REPLY last day; the OC's earliest s.9 filing date (IBC.S9.EARLIEST_FILING); limitation check (IBC.S7S9.LIMITATION_ART137); threshold check (IBC.S4.THRESHOLD); s.10A-window check (IBC.S10A.SUSPENDED_DEFAULT). Each shows its anchors and an ASSUMED/CONFIRMED trigger date.
3. *Our grounds:* (a) pre-existing dispute under s.5(6)(a)–(c), with a dated chronology; (b) pending suit or arbitration filed before receipt; (c) payment (attested bank record / encashed cheque); (d) threshold below ₹1 crore; (e) time-barred debt; (f) default inside 25.03.2020–24.03.2021 (permanent bar); (g) defective notice (form, mode, addressee); (h) not an operational debt or not an OC; (i) arbitration clause (strategy: invoke arbitration *after* the notice does not create a "pre-existing" dispute).
4. *Likely adverse authorities to check:* Mobilox's limits (dispute must pre-exist and not be spurious); NCLAT decisions treating post-notice or "afterthought" disputes as moonshine (to research in the corpus); Kay Bouvet (favourable). Run AuthorityView status on each.
5. *Evidence checklist:* every email, letter, debit note, rejection or quality report, warranty claim and meeting minute **dated before receipt**; proof of the receipt date (envelope, courier tracking, email headers); bank statements for payments; pleadings and case numbers of any suit or arbitration; the contract (dispute resolution, acceptance and warranty clauses).
6. *Risk:* failure to reply → s.9 filing becomes likely; admission leads to moratorium and loss of management control (s.14/s.17). Settlement options: pre-admission withdrawal (AAA Rules r.8); post-admission constraints (s.12A as substituted, §7).

**Reply skeleton, "Reply under section 8(2) IBC to demand notice dated __ received on __":** (1) reference and receipt date; (2) preliminary objections: notice defective/not maintainable (form, mode, threshold, limitation, s.10A, not an operational debt); (3) existence of a pre-existing dispute: numbered chronology with annexure references, each document pre-dating receipt; (4) pending suit/arbitration (forum, case no., filing date); (5) payment (if any) with attested records; (6) reservation of rights, caution against filing under s.9 while suppressing this reply (s.67C, s.65, s.64A); (7) annexure index; (8) delivery block (RPAD/speed post to the OC's address and to the lawyer if the notice came through a lawyer, plus email; keep proof).
**Para-wise grid:** `notice_para | allegation | admit/deny/not-known | our response | evidence_id + date (must be < receipt date) | authority | risk_flag`.

---

### 4. T-IBC-2: s.9 petition by operational creditor at NCLT (either side)

**event_type:** `IBC_DEMAND_NOTICE_DELIVERED`, `IBC_S9_FILED`, `IBC_APPLICATION_LISTED` (first listing before AA), `IBC_DEFECT_NOTICE_RECEIVED`, `NCLT_NOTICE_ISSUED`, `NCLT_HEARING`.

#### IBC.S9.EARLIEST_FILING
```yaml
code: IBC.S9.EARLIEST_FILING
valid_from: 2016-12-01
applies_when: { statute_basis_any: ["wrk_IBC2016#sec-9.ss-1"], client_role_any: [OPERATIONAL_CREDITOR, CORPORATE_DEBTOR] }
trigger_event: IBC_DEMAND_NOTICE_DELIVERED    # OC proves delivery
period: { value: 10, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }   # "from the date of delivery" → GCA s.9
output: { window_kind: EARLIEST_DATE, offset_after_expiry_days: 1,
          label: "Earliest date OC may file s.9 (if no payment and no notice of dispute received)" }
nature: HARD    # statutory precondition; a premature filing is a maintainability objection
anchors:
  - "IBC s.9(1): 'After the expiry of the period of ten days from the date of delivery of the notice or invoice demanding payment under
     sub-section (1) of section 8, if the operational creditor does not receive payment from the corporate debtor or notice of the dispute
     under sub-section (2) of section 8, the operational creditor may file an application ...'"   # [I-R4]
  - "GCA s.9(1)"   # [I-R27a]
verification: VERIFIED-PRIMARY
tests:
  - { trigger: 2026-06-01, expect: 2026-06-12 }   # period 02–11 Jun; earliest filing Fri 12 Jun
  - { trigger: 2026-07-20, expect: 2026-07-31 }
notes: >
  s.8(2) counts from "receipt" and s.9(1) from "delivery". Treat them as one event unless the facts differ, and flag any
  difference. Filings on or after 26.05.2026 must ALSO satisfy IBC.S215.IU_PREFILING. Unamended in 2026 except s.9(3)(e)
  ("any other information, as may be specified") and the new second proviso to s.9(5).
```

#### IBC.S4.THRESHOLD (maintainability)
```yaml
code: IBC.S4.THRESHOLD
kind: MAINTAINABILITY_CHECK
point_in_time:
  - { valid_from: 2016-12-01, valid_to: 2020-03-23, min_default: "₹1,00,000" }   # s.4(1)
  - { valid_from: 2020-03-24, min_default: "₹1,00,00,000" }                        # S.O. 1205(E)
key_date: FILING_DATE          # not default date; see case law
anchors:
  - "IBC s.4(1): 'This Part shall apply to matters relating to the insolvency and liquidation of corporate debtors where the minimum amount of
     the default is one lakh rupees: Provided that the Central Government may, by notification, specify the minimum amount of default of
     higher value which shall not be more than one crore rupees.'"   # [I-R4]
  - "S.O. 1205(E), 24.03.2020: '... the Central Government hereby specifies one crore rupees as the minimum amount of default for the
     purposes of the said section.'"   # [I-R7] Gazette No. 1076, 24.03.2020
case_law:
  - "Jumbo Paper Products v Hansraj Agrofresh, NCLAT CA(AT)(Ins) 813/2021, as quoted in NCLT Kolkata IA(IB) 995/KB/2021: 'It is the date of filing
     of the application which is the relevant factor for considering the applicability of the threshold limit'; Madhusudan Tantia
     (CA(AT)(Ins) 557/2020) distinguished (notice and filing both before 24.3.2020)"   # [I-R29]
verification: VERIFIED-PRIMARY (notification) / VERIFIED-SECONDARY (filing-date rule; NCLAT, not SC)
tests: n/a (boolean)
notes: "Not amended by the 2026 Act. Whether the threshold is assessed on the aggregate claim or on the 'amount of default' net of disputed parts: TO VERIFY."
```

#### IBC.S10A.SUSPENDED_DEFAULT (permanent bar; point-in-time)
```yaml
code: IBC.S10A.SUSPENDED_DEFAULT
kind: MAINTAINABILITY_CHECK
applies_to: [s.7, s.9, s.10 applications]
barred_default_window: { from: 2020-03-25, to: 2021-03-24 }   # 6 months + 3 + 3
anchors:
  - "IBC s.10A (ins. by Act 17 of 2020 w.e.f. 05.06.2020): '... no application for initiation of corporate insolvency resolution process of a
     corporate debtor shall be filed, for any default arising on or after 25th March, 2020 for a period of six months or such further period,
     not exceeding one year from such date, as may be notified ... Provided that no application shall ever be filed ... for the said default
     occurring during the said period. Explanation.– ... shall not apply to any default committed ... before 25th March, 2020.'"   # [I-R4]
  - "S.O. 3265(E), 24.09.2020: 'further period of three months from the 25th September, 2020'"   # [I-R8]
  - "S.O. 4638(E), 22.12.2020: 'further period of three months from the 25th December, 2020'"    # [I-R9]
case_law:
  - "Ramesh Kymal v Siemens Gamesa Renewable Power, AIR 2021 SC 833 (09.02.2021), paras 26–27: bar applies to applications filed after
     25.03.2020 for defaults on/after that date, even if filed before s.10A was inserted on 05.06.2020; 'date of initiation' = filing date"  # [I-R17]
verification: VERIFIED-PRIMARY
tests: [ {default: 2020-03-24, expect: NOT_BARRED}, {default: 2021-03-24, expect: BARRED}, {default: 2021-03-25, expect: NOT_BARRED} ]
notes: >
  The end date 24.03.2021 is inferred from "one year from such date" and the two "three months from 25th" notifications. The
  boundary day is worth partner sign-off. A continuing or recurring default (e.g. instalments) straddling the window needs
  the default date pinned per instalment: TO VERIFY.
```

#### IBC.S7S9.LIMITATION_ART137 (s.7 and s.9 applications)
```yaml
code: IBC.S7S9.LIMITATION_ART137
trigger_event: DATE_OF_DEFAULT            # applicant must plead; resets on ACKNOWLEDGMENT_OF_DEBT (s.18 LA) / DECREE_OR_RECOVERY_CERTIFICATE
period: { value: 3, unit: YEARS }
computation: { exclude_first_day: true, month_convention: SAME_DAY_NUMBER_CLAMP_TO_MONTH_END, court_closure_rollover: true, covid_exclusion: CV6 }
nature: CONDONABLE (no fixed cap; s.5 LA "sufficient cause")
anchors:
  - "IBC s.238A: 'The provisions of the Limitation Act, 1963 shall, as far as may be, apply to the proceedings or appeals before the
     Adjudicating Authority, the National Company Law Appellate Tribunal ...'"   # [I-R4]
case_law:
  - "B.K. Educational Services v Parag Gupta, (2019) 11 SCC 633, para 27: '... Article 137 of the Limitation Act gets attracted. \"The right to
     sue\", therefore, accrues when a default occurs. If the default has occurred over three years prior to the date of filing of the
     application, the application would be barred under Article 137 ..., save and except in those cases where ... Section 5 ... may be
     applied to condone the delay'"   # [I-R13]
  - "Laxmi Pat Surana v Union Bank of India, AIR 2021 SC 1707, para 42: fresh limitation from written acknowledgment (s.18 LA) applies to s.7"   # [I-R16]
  - "Asset Reconstruction Co v Bishal Jaiswal (SC, 15.04.2021), para 33: majority of the NCLAT Full Bench in V. Padmakumar (balance-sheet entries are not
     acknowledgments) set aside; balance-sheet entries can be acknowledgments under s.18 LA (fact-dependent)"   # [I-R14]
  - "Dena Bank v C. Shivakumar Reddy (SC, 04.08.2021), para 118: 'entries in books of accounts and/or balance sheets ... would amount to an
     acknowledgment under Section 18'; para 143: DRT decree / Recovery Certificate gives a fresh 3-year period to file s.7 if unpaid;
     para 144: 'There is no bar in law to the amendment of pleadings in an application under Section 7 ... or to the filing of additional documents'"  # [I-R15]
verification: VERIFIED-SECONDARY (case law) / VERIFIED-PRIMARY (s.238A)
tests:   # simple case only: no acknowledgment, no exclusion window
  - { trigger: 2023-09-15, expect: 2026-09-15 }   # Tue; NCLT closure → rollover to reopening day
  - { trigger: 2024-03-31, expect: 2027-03-31 }
notes: >
  Any default date before 2022-03-01 must run through CV6 (TO VERIFY) and is excluded from golden tests. Whether s.5 LA
  condonation is realistically available for an *application* (vs. appeal) is fact-specific. Show as "CONDONABLE (discretionary)"
  and never compute a condoned date. Acknowledgment analysis (s.18 LA: signed writing before expiry) must cite the document,
  and the lawyer confirms it.
```

#### IBC.S215.IU_PREFILING (new, in force 26.05.2026)
```yaml
code: IBC.S215.IU_PREFILING
kind: MAINTAINABILITY_CHECK
point_in_time:
  - { valid_to: 2026-05-25, text: "An operational creditor may submit financial information to the information utility in such form and manner as may be specified." }  # [I-R4]
  - { valid_from: 2026-05-26, text: "An operational creditor shall, before filing an application under section 9 of the Code, submit financial information ..." }  # [I-R1] Amendment s.62(b); [I-R2]
also: "new s.215(4): CD/debtor to authenticate IU information 'in such manner and within such period, as may be specified'; non-response → deemed authenticated"
verification: VERIFIED-PRIMARY (statute) / TO VERIFY WITH PARTNER (whether IBBI IU Regulations specifying the 'manner' have been notified; an IBBI 2026 discussion paper exists [I-R33])
notes: "For s.9 applications filed on/after 26.05.2026, a missing IU submission is a live maintainability objection for the CD."
```

#### IBC.S9.ADMIT_14D (AA's decision window; directory)
```yaml
code: IBC.S9.ADMIT_14D
trigger_event: IBC_APPLICATION_LISTED     # 'receipt' = date first presented/listed before AA, not date of filing (NCLAT view noted in Surendra para 18)
period: { value: 14, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }
output: { window_kind: TARGET_DATE, label: "Statutory target for NCLT order (directory; not a party deadline)" }
nature: DIRECTORY
anchors:
  - "IBC s.9(5): 'The Adjudicating Authority shall, within fourteen days of the receipt of the application under sub-section (2), by an order– (i) admit ... (ii) reject ...'"  # [I-R4]
  - "2026 second proviso to s.9(5) (in force 26.05.2026): 'Provided further that if the Adjudicating Authority has not passed an order under this sub-section
     within a period of fourteen days from the date of receipt of application under sub-section (2), it shall record the reasons for such delay in writing.'"  # [I-R1] s.5(b)
case_law:
  - "Surendra Trading Co v Juggilal Kamlapat Jute Mills, 2017 (16) SCC 143, para 14: NCLAT held the 14-day period 'cannot be treated as mandatory'; 'this view is not under challenge (and rightly so)'"  # [I-R12]
verification: VERIFIED-PRIMARY (text) / VERIFIED-SECONDARY (directory)
tests: [ {trigger: 2026-06-01, expect: 2026-06-15}, {trigger: 2026-05-20, expect: 2026-06-03} ]
notes: "The 2026 proviso attaches only 'record reasons' to delay, which supports the directory reading. No post-amendment ruling found: TO VERIFY."
```

#### IBC.S7S9S10.RECTIFY_7D (defect cure; directory)
```yaml
code: IBC.S7S9S10.RECTIFY_7D
trigger_event: IBC_DEFECT_NOTICE_RECEIVED   # applicant's receipt of AA's notice
period: { value: 7, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: true }
nature: DIRECTORY (cure late only with an application showing sufficient cause)
anchors:
  - "s.9(5) proviso: '... give a notice to the applicant to rectify the defect in his application within seven days of the date of receipt of such notice ...'"  # [I-R4]
  - "s.7(5) first proviso (as substituted 2026): '... within seven days from the date of receipt of such notice ...'"  # [I-R1]
  - "s.10(4) proviso: '... within seven days from the date of receipt of such notice ...'"  # [I-R4]
case_law:
  - "Surendra Trading, para 24: 'the aforesaid provision of removing the defects within seven days is directory and not mandatory';
     para 25: if not removed in 7 days, applicant must file an application showing sufficient cause; AA decides"   # [I-R12]
verification: VERIFIED-SECONDARY
tests: [ {trigger: 2026-07-01, expect: 2026-07-08} , {trigger: 2026-06-25, expect: 2026-07-02} ]
notes: "Show as the applicant's action date. Beyond it, show 'late, needs a condonation-type application (Surendra para 25)'."
```

#### IBC.NCLT.R37.REPLY (CD's reply to a s.9 or s.7 petition): PRACTICE / TO VERIFY
```yaml
code: IBC.NCLT.R37.REPLY
trigger_event: NCLT_NOTICE_ISSUED
period: null     # no statutory number of days found
nature: PRACTICE
anchors:
  - "NCLT Rules 2016 r.37(1): 'The Tribunal shall issue notice to the respondent to show cause against the application or petition on a date of hearing to be specified in the Notice.'
     r.37(3): '... file a reply accompanied with an affidavit and along with copies of such documents on which it relies, with an advance service to the petitioner or applicant,
     to the Registry before the date of hearing ...'"   # [I-R28] secondary host
verification: TO VERIFY WITH PARTNER
notes: >
  The binding deadline is whatever the bench's order fixes (often a short period, e.g. 1–2 weeks, with a rejoinder period:
  practice only, unverified). The MVP should capture the order-sheet direction as a lawyer-entered deadline (manual `ddl_`),
  with r.37(3) ("before the date of hearing") as the fallback outer limit. No IBC-specific reply period exists in the Code or AAA Rules.
```

#### Other s.9-relevant rules (in force 26.05.2026)
- **s.67C** (Amendment Act s.48): penalty of ₹1 lakh to ₹2 crore where "an operational creditor has concealed in an application under section 9, the fact that the corporate debtor had notified him of a dispute ... or the full and final payment". The CD side asks for it; the OC side must check its s.9(3)(b) affidavit. It replaces the **s.76** offence (omitted by Amendment Act s.50). Pending s.76 prosecutions are saved by s.235A Explanation II. [I-R1]
- **s.64A** (Amendment Act s.44): penalty of ₹1 lakh to ₹2 crore for a "frivolous or vexatious proceeding" under Part II. [I-R1]
- **s.12A** (substituted, Amendment Act s.8). Post-admission withdrawal requires an RP application with 90% CoC approval, made in the manner to be specified. It is barred "(a) before the constitution of the committee of creditors ... and (b) after the first invitation for submission of a resolution plan". The AA decides within 30 days (record reasons if late). **Settlement strategy:** settle before admission (AAA Rules r.8 withdrawal "before its admission") wherever possible. [I-R1], [I-R6]
- **AAA Rules r.6(2)**: the OC serves a copy of the application on the CD's registered office and on IBBI "before filing". [I-R6]

#### Draft output for T-IBC-2
**A. Acting for the CD: strategy memo**
1. *Their claim:* the petition (Form 5) particulars, the date of default pleaded, the amount, the s.8 notice relied on, the s.9(3)(b) affidavit, the IU record (filings on or after 26.05.2026), and the proposed IRP.
2. *Deadlines:* the reply date fixed by the bench (IBC.NCLT.R37.REPLY, lawyer-entered); the next hearing; the statutory 14-day admission target (directory); the 30+15-day appeal window that runs if the petition is admitted (IBC.S61.APPEAL_NCLAT).
3. *Maintainability objections (ranked):* (i) pre-existing dispute or notice of dispute (s.9(5)(ii)(d); Mobilox); (ii) payment; (iii) below the threshold (filing-date test); (iv) limitation (Art. 137); (v) s.10A default; (vi) premature filing (before D+11); (vii) defective demand notice or delivery (Rule 5); (viii) no IU submission (s.215(3), filings ≥26.05.2026); (ix) not an operational debt or not an OC; (x) application incomplete. Plus counter-relief: s.67C / s.64A / s.65 penalties.
4. *Adverse authorities to check:* NCLAT decisions holding particular disputes "spurious" or post-notice; decisions on deemed service; Surendra (defects curable); any post-2026 ruling on s.9(5) or s.215(3).
5. *Evidence checklist:* as in T-IBC-1, plus a copy of our s.8(2) reply with proof of delivery, IU authentication status (new s.215(4): a non-response means deemed authentication, so check), and board authorisation for the deponent.
6. *Settlement or exit:* payment before admission leads to withdrawal under r.8. After admission only s.12A applies, subject to the new bars.

**Reply skeleton: "Reply on behalf of the Corporate Debtor to C.P.(IB) No. __ /__ (s.9 IBC)".** (1) Synopsis and list of dates; (2) preliminary objections on maintainability, one heading each; (3) brief facts; (4) para-wise reply to Form 5 Parts I–V (grid below); (5) legal submissions with authorities (Mobilox paras 24 and 40; Kay Bouvet; Jumbo Paper; B.K. Educational); (6) prayer: reject under s.9(5)(ii)(d) / (a); costs; direction under s.67C or s.64A; (7) verification and affidavit; (8) annexures, chronologically indexed with dates.
**Para-wise grid:** `petition_part/para | averment | admitted/denied/not admitted | reply | annexure (date vs. notice receipt) | authority | objection_code (THRESHOLD|LIMITATION|S10A|DISPUTE|PAYMENT|NOTICE_DEFECT|IU_PREFILING|PREMATURE) | evidence_strength`.

**B. Acting for the OC: pre-filing checklist memo**
Form 3/4 compliant and delivered per r.5(2) (proof); D+11 reached (IBC.S9.EARLIEST_FILING); no payment and **no notice of dispute** received (search inbox and post; s.67C exposure); amount ≥ ₹1 crore at filing; within 3 years of default or acknowledgment; default not in the s.10A window; IU submission made (s.215(3), ≥26.05.2026); copy served on the CD and IBBI before filing (r.6(2)); Form 2 IRP consent if proposing an IRP (r.9); fee; NCLT bench (registered office). Defects notice → 7-day cure (IBC.S7S9S10.RECTIFY_7D).

---

### 5. T-IBC-3: s.7 petition by financial creditor; s.10 corporate applicant

**event_type:** `IBC_S7_FILED`, `IBC_APPLICATION_LISTED`, `IBC_DEFECT_NOTICE_RECEIVED`, `DATE_OF_DEFAULT`, `ACKNOWLEDGMENT_OF_DEBT`, `DECREE_OR_RECOVERY_CERTIFICATE`, `INSOLVENCY_COMMENCEMENT`.

#### IBC.S7.ADMISSION (point-in-time rule; two versions)
```yaml
code: IBC.S7.ADMISSION
interpretation: VERSIONED_BY_LEGAL_TIME     # select by date of AA decision; transitional application to pending petitions TO VERIFY
versions:
  - id: PRE_2026
    valid_from: 2019-08-16        # proviso to s.7(4) ins. by Act 26 of 2019
    valid_to: 2026-05-25
    text:
      - "s.7(4): 'The Adjudicating Authority shall, within fourteen days of the receipt of the application under sub-section (2), ascertain the existence of a default ...'"
      - "s.7(4) proviso: 'Provided that if the Adjudicating Authority has not ascertained the existence of default and passed an order under sub-section (5) within such time, it shall record its reasons in writing for the same.'"
      - "s.7(5): 'Where the Adjudicating Authority is satisfied that– (a) a default has occurred and the application ... is complete, and there is no disciplinary proceedings pending against the proposed resolution professional, it may, by order, admit such application; or (b) ... it may, by order, reject such application'"
    case_law:
      - "Vidarbha Industries Power v Axis Bank (SC, 12.07.2022), paras 30–31: AA 'has the discretion to admit or not admit' even where debt and default exist"   # [I-R19]
      - "M. Suresh Kumar Reddy v Canara Bank (SC, 11.05.2023), paras 12–13: review order of 22.09.2022 confined Vidarbha to its facts; 'The view taken in ... Innoventive Industries still holds good'"   # [I-R20]
  - id: POST_2026
    valid_from: 2026-05-26        # Amendment Act s.4, S.O. 2625(E)
    text:
      - "s.7(4): unchanged (14-day ascertainment); its proviso omitted"
      - "s.7(5): 'The Adjudicating Authority shall, within fourteen days of the receipt of the application under sub-section (2), by an order— (a) admit the application, if it is satisfied that a default has occurred and the application ... is complete, and there is no disciplinary proceeding pending against the proposed resolution professional; or (b) reject the application, if ...'"
      - "first proviso: 7-day notice to rectify before rejection under (b)"
      - "second proviso: 'if the Adjudicating Authority has not passed an order under this sub-section within a period of fourteen days ... it shall record the reasons for such delay in writing.'"
      - "Explanation I: 'where the requirements under clause (a) have been complied with, no other ground shall be considered to reject an application filed under this section.'"
      - "Explanation II: record of default with an IU, furnished by a financial institution, 'shall be considered sufficient for the Adjudicating Authority to ascertain the existence of default'"
nature: DIRECTORY (14-day target; both versions; post-2026 directory status TO VERIFY) / MANDATORY OUTCOME post-2026 (admit if (a) satisfied)
trigger_event: IBC_APPLICATION_LISTED
period: { value: 14, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }
verification: VERIFIED-PRIMARY (both texts) / TO VERIFY WITH PARTNER (directory character after 2026; application to petitions pending on 26.05.2026)
tests: [ {trigger: 2026-06-01, expect: 2026-06-15}, {trigger: 2026-05-20, expect: 2026-06-03} ]   # target dates only
notes: >
  Strategy impact for the CD side after 26.05.2026: "commercial" defences (viability, pending receivables, regulatory
  orders: the Vidarbha line) are statutorily excluded by Explanation I. The surviving grounds: no financial debt; no default;
  application incomplete; disciplinary proceeding pending against the proposed RP; limitation; threshold; s.10A; s.11
  ineligibility; allottee/security-holder minimum numbers (s.7(1) provisos).
```

#### IBC.S10.ADMISSION (corporate applicant)
```yaml
code: IBC.S10.ADMISSION
versions:
  - id: PRE_2026  (valid_to 2026-05-25): "s.10(4): 'shall, within a period of fourteen days of the receipt of the application, by an order– (a) admit the application, if it is complete and no disciplinary proceeding is pending against the proposed resolution professional; or (b) reject ...' + 7-day rectification proviso"   # [I-R4]
  - id: POST_2026 (valid_from 2026-05-26): "disciplinary-proceeding limbs omitted from s.10(4)(a)/(b); second proviso (record reasons if >14 days); s.10(3)(b) (information on proposed RP) omitted;
       new s.16(3A): AA refers to IBBI for recommendation of the IRP in s.10 cases"   # [I-R1] ss.6, 10
nature: DIRECTORY (Surendra para 14/23 reasoning covers s.10(4))
verification: VERIFIED-PRIMARY (text) / VERIFIED-SECONDARY (directory)
notes: "s.10(3)(c) special resolution (or ¾ partners) still required. AAA Rules r.7(2): copy to IBBI before filing."
```

#### Draft output for T-IBC-3
**Memo (CD side, s.7):** their claim (facility documents, sanction, the default date per the IU record or the bank's books, NPA date, amount, the claimed acknowledgments); deadlines (bench reply date; 14-day target; appeal window); our grounds limited to the post-2026 list above plus limitation (Art. 137 / s.18 acknowledgment / decree or RC fresh period: check each balance sheet, OTS letter and restructuring letter by date); adverse authorities (Bishal Jaiswal, Dena Bank, Laxmi Pat Surana; Explanation I after 2026; Innoventive / E.S. Krishnamurthy line); evidence (statement of account under the Bankers' Books Evidence Act, IU authentication status, sanction letters, balance sheets for each FY with the auditor's notes, OTS correspondence, DRT/RC orders); settlement (pre-admission withdrawal under r.8; after admission s.12A with 90% CoC and the new timing bars).
**Memo (FC side, s.7):** Form 1 completeness (AAA Rules r.4); r.4(3) service on the CD and IBBI before filing; IU record (Explanation II if a financial institution); limitation chain table; proposed IRP's Form 2 and no disciplinary proceedings; threshold and s.10A.
**Reply skeleton (CD to a s.7 petition):** synopsis; objections (limitation with a date table; no financial debt; no default or default disputed with reasons; incomplete application; proposed-IRP disqualification; threshold; s.10A; s.11); para-wise reply to Form 1 Parts I–V; prayer; affidavit. Grid as in T-IBC-2, with objection codes `LIMITATION|NOT_FINANCIAL_DEBT|NO_DEFAULT|INCOMPLETE|IRP_DISCIPLINARY|THRESHOLD|S10A|S11`.

---

### 6. T-IBC-4: Appeals (NCLAT s.61; Supreme Court s.62)

**event_type:** `NCLT_ORDER_PRONOUNCED`, `NCLT_ORDER_UPLOADED`, `CERTIFIED_COPY_APPLIED`, `CERTIFIED_COPY_RECEIVED`, `APPEAL_E_FILED`, `NCLAT_ORDER_RECEIVED`.

#### IBC.S61.APPEAL_NCLAT
```yaml
code: IBC.S61.APPEAL_NCLAT
valid_from: 2016-12-01
applies_when: { statute_basis_any: ["wrk_IBC2016#sec-61.ss-2"], client_role_any: [ANY_AGGRIEVED] }
trigger_event: NCLT_ORDER_PRONOUNCED   # if order NOT pronounced in open court → NCLT_ORDER_UPLOADED (Kalate)
period: { value: 30, unit: DAYS }
computation:
  exclude_first_day: true               # Sanket paras 23–24 (s.12(1) LA; NCLAT Rules)
  certified_copy_exclusion: "s.12(2) LA: exclude time from CC application to CC receipt ONLY IF CC applied within the 30-day period"   # V. Nagarajan; Sanket
  court_closure_rollover: { applies_to: BASE_PERIOD_ONLY }   # s.4 LA / NCLAT r.3; NOT to the 15-day condonable extension (Sagufa; Tata Steel)
  stop_event: APPEAL_E_FILED            # Sanket paras 19–21
extension: { period: {value: 15, unit: DAYS}, condition: "sufficient cause shown", extendable_beyond: NO }
output: [ {window_kind: LAST_DATE, label: "Last day to appeal as of right"}, {window_kind: OUTER_LIMIT, label: "Absolute last day (condonation only); NCLAT has no power beyond"} ]
nature: CONDONABLE (cap 15 days)
anchors:
  - "IBC s.61(2): 'Every appeal under sub-section (1) shall be filed within thirty days before the National Company Law Appellate Tribunal:
     Provided that the National Company Law Appellate Tribunal may allow an appeal to be filed after the expiry of the said period of thirty
     days if it is satisfied that there was sufficient cause for not filing the appeal but such period shall not exceed fifteen days.'"   # [I-R4]
  - "NCLAT Rules 2016 r.22(2): 'Every appeal shall be accompanied by a certified copy of the impugned order'"   # quoted in V. Nagarajan [I-R21]
case_law:
  - "V. Nagarajan v SKS Ispat & Power, (2022) 2 SCC 244 (22.10.2021): limitation runs from pronouncement, not upload or receipt of copy; CC time excluded
     only if CC applied within limitation (as summarised in Kalate para 13 and Tata Steel para 10.3)"   # [I-R21][I-R23][I-R24]
  - "Sanket Kumar Agarwal v APG Logistics (SC, 01.05.2023): date of pronouncement excluded; limitation stops on e-filing; order of 26.08.2022 → appeal e-filed 10.10.2022 = 45th day, within the condonable period"   # [I-R22]
  - "Sanjay Pandurang Kalate v Vistra ITCL, (2024) 3 SCC 27 (04.12.2023), paras 19–21: where the matter was heard but the order was not pronounced, limitation starts on the upload date"   # [I-R23]
  - "Tata Steel v Raj Kumar Banerjee, 2025 INSC 639 (07.05.2025), para 11.1: 'Once the prescribed and condonable periods (i.e., 30 + 15 days) expire, the NCLAT
     has no jurisdiction to entertain appeals, regardless of the reason for the delay'; para 10.2: s.4 LA benefit only within the prescribed period"   # [I-R24]
  - "A. Rajendra v Gonugunta Madhusudhan Rao, 2025 SCC OnLine SC 721: order pronounced in open court → limitation from that day (as cited in Tata Steel)"   # snippet via [I-R24]
verification: VERIFIED-PRIMARY (s.61(2)) / VERIFIED-SECONDARY (start-date and computation rules)
tests:
  - { trigger: 2022-08-26, expect: { last_date: 2022-09-25 (Sun → rollover per NCLAT calendar), outer_limit: 2022-10-10 } }   # outer limit confirmed by SC in Sanket
  - { trigger: 2026-06-01, expect: { last_date: 2026-07-01, outer_limit: 2026-07-16 } }   # no CC exclusion; raw dates before calendar check
notes: >
  Inputs to confirm with the lawyer: (i) was the order pronounced in open court, and was the client present or represented? (ii) upload date;
  (iii) CC application date and receipt date. If the CC was applied for within 30 days, add the CC-pending days to both dates.
  Present all variants when facts are unclear (CONTESTED_RULE policy: earliest date is the action date).
  Edge: if the outer-limit date falls on a closed day there is no rollover; whether e-filing on a holiday is accepted is TO VERIFY (current NCLAT SOP).
  The 2026 Act did not change s.61(2). It inserted s.61(6) (below).
```

#### IBC.S61.DISPOSAL_3M (new s.61(6); NCLAT's own target)
```yaml
code: IBC.S61.DISPOSAL_3M
valid_from: 2026-05-26
trigger_event: NCLAT_APPEAL_RECEIVED
period: { value: 3, unit: MONTHS }
nature: DIRECTORY? (no consequence stated)   # TO VERIFY WITH PARTNER
anchor: "IBC s.61(6) (ins. by Amendment Act s.43): 'The National Company Law Appellate Tribunal shall dispose of the appeal within three months from the date of its receipt.'"  # [I-R1][I-R2]
verification: VERIFIED-PRIMARY (text) / TO VERIFY (nature)
tests: none (informational target; not a party deadline)
notes: "Earlier, s.64(1) (record reasons; President/Chairperson may extend up to 10 days) was the general rule. No ruling yet on s.61(6)."
```

#### IBC.S62.APPEAL_SC
```yaml
code: IBC.S62.APPEAL_SC
trigger_event: NCLAT_ORDER_RECEIVED    # statute says "date of receipt of such order"; whether presence at pronouncement = receipt: TO VERIFY
period: { value: 45, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: { applies_to: BASE_PERIOD_ONLY } }
extension: { period: {value: 15, unit: DAYS}, condition: "prevented by sufficient cause", extendable_beyond: NO }
nature: CONDONABLE (cap 15 days)
anchors:
  - "IBC s.62(1): 'Any person aggrieved by an order of the National Company Law Appellate Tribunal may file an appeal to the Supreme Court on a question of law
     arising out of such order under this Code within forty-five days from the date of receipt of such order.'
     s.62(2): '... allow the appeal to be filed within a further period not exceeding fifteen days.'"   # [I-R4]
verification: VERIFIED-PRIMARY (period) / TO VERIFY (meaning of "receipt"; SC Rules 2013 filing mechanics)
tests: [ {trigger: 2026-06-01, expect: {last_date: 2026-07-16, outer_limit: 2026-07-31}}, {trigger: 2026-08-03, expect: {last_date: 2026-09-17, outer_limit: 2026-10-02}} ]
notes: "Unamended by the 2026 Act. A question of law only. SC summer vacation: rollover via CourtCalendar for the 45-day base only."
```

#### IBC.S220.APPEAL_NCLAT (new; appeals against IBBI disciplinary committee orders, for IP/service-provider clients)
Anchor: new s.220(7)–(8) (Amendment Act s.66, in force 26.05.2026): appeal "within a period of thirty days from the date of receipt of the order", plus "a further period not exceeding fifteen days". CONDONABLE (cap 15). VERIFIED-PRIMARY [I-R1]. It is outside the MVP's top triggers, so the full RuleSpec is deferred.

#### Draft output for T-IBC-4
**Appeal memo:** impugned order (bench, date pronounced, whether the client was present, upload date, CC applied/received); a **limitation box** giving the 30-day date, the 45-day outer limit, CC exclusion and rollover, with every variant shown; appealability and grounds (s.61(1) "any person aggrieved"; s.61(3) closed grounds against plan approval; s.61(4) material irregularity or fraud against liquidation orders); stay/interim relief and moratorium consequences; adverse authorities (Tata Steel: no condonation beyond 45 days; V. Nagarajan: CC diligence); filing mechanics (Form NCLAT-1, certified copy under r.22(2), e-filing and the 7-day physical copy per the NCLAT order of 24.12.2022, current SOP TO VERIFY); target disposal (s.61(6)).
**Grounds grid:** `impugned_para | finding | error_type (law/fact/jurisdiction/natural justice) | ground | record ref | authority | relief`.
**SC appeal note:** question-of-law framing; 45 + 15 from receipt.

---

### 7. T-IBC-5: CIRP timeline facts (informational, not client deadlines)

| Fact | Anchor (operative words) | Status |
|---|---|---|
| CIRP completes in 180 days from admission | s.12(1): "shall be completed within a period of one hundred and eighty days from the date of admission of the application" [I-R4] | VERIFIED-PRIMARY |
| One extension of ≤90 days (CoC 66%) | s.12(2)–(3): "...not exceeding ninety days: Provided that any extension ... shall not be granted more than once" [I-R4] | VERIFIED-PRIMARY |
| 330-day outer limit, including litigation time | s.12(3) second proviso: "shall **mandatorily** be completed within a period of three hundred and thirty days from the insolvency commencement date, including any extension ... and the time taken in legal proceedings" [I-R4]. *Essar Steel* (SC, 15.11.2019): "we strike down the word 'mandatorily' as being manifestly arbitrary ... ordinarily ... must be completed within the outer limit of 330 days" [I-R18]. The 2026 Act does not amend s.12. | VERIFIED-SECONDARY (case) |
| Moratorium runs from the admission order until CIRP ends, plan approval or liquidation order | s.14(1), (4) [I-R4]. 2026: s.14(1) now cross-refers to (2A); new Explanation to s.14(3)(b): moratorium applies where "the surety seeks to initiate or continue any action ... against the corporate debtor pursuant to a contract of guarantee"; new s.67B civil penalty for breach (₹1 lakh–₹2 crore) [I-R1] | VERIFIED-PRIMARY |
| Insolvency commencement date = date of admission | s.7(6), s.9(6), s.10(5) [I-R4]. New s.5(11) proviso: with multiple pending applications, "initiation date" = first application's date [I-R1] | VERIFIED-PRIMARY |
| Plan approval order within 30 days of receipt of the plan (record reasons if late) | new s.31(2A) [I-R1] | VERIFIED-PRIMARY (directory, presumably) |
| Liquidation order within 30 days; CIRP restoration (≤120 days, once) | new s.33(2A), (1A), (1B) [I-R1] | VERIFIED-PRIMARY |
| Liquidation completes in 180 days (+ ≤90 days); dissolution order within 30 days | substituted s.54(1); new s.54(4) [I-R1] | VERIFIED-PRIMARY |
| Secured creditor's realisation election: 14 days from liquidation commencement, else deemed relinquished | substituted s.52(2) (not for liquidations initiated on or before 26.05.2026, s.52 Explanation) [I-R1] | VERIFIED-PRIMARY |
| Sample per-CIRP display (admission 2026-06-01) | day 180 = 2026-11-28; +90 = 2027-02-26; day 330 = 2027-04-27 (GCA s.9 "from") | computed; informational |

---

### 8. T-IBC-6: IBC (Amendment) Act 2026, point-in-time test case

#### 8.1 Enactment facts (all VERIFIED-PRIMARY)
- Act No. 6 of 2026; assent **6 Apr 2026**; Gazette Extraordinary Part II s.1, No. 11, **6 Apr 2026** (CG-DL-E-06042026-271594). s.1(2): commencement by notification, with different dates permitted for different provisions [I-R1].
- Bill introduced in Lok Sabha on 12 Aug 2025 (IBBI listing [I-R5]). Passed by Parliament around 1 Apr 2026 [I-R34, snippet].
- Commencement: **S.O. 2625(E)**, dated 22 May 2026, Gazette Part II s.3(ii) No. 2533 of **25 May 2026** (CG-DL-E-25052026-272855), F. No. Insol-30/8/2025-Insolvency-MCA, signed by Anita Shah Akella, Jt. Secy. Appointed day **26 May 2026** for: ss.2–6; 8–33; 34(a)(iii) and 34(b); 35–39; 41; 43–44; 46; 48–59; 61–66; 68; 69(a); 70(a); 70(b)(i)–(xxvi) except (xx); 72 [I-R2].
- No further commencement notification is listed on IBBI's notifications page as of 2026-10-01 (entries after 25 May 2026: only an 8 Jul 2026 appointment) [I-R3]. *Confirm on egazette before each release.*

#### 8.2 Provision-by-provision status table
Key: **IF** = IN FORCE from 26.05.2026 (S.O. 2625(E)); **NIF** = ENACTED NOT IN FORCE (as of 2026-10-01). "AA" = Amendment Act section; "Code" = provision of IBC 2016 affected. Source for every row: [I-R1] (text) + [I-R2] (status).

| AA s. | Code provision | Gist of change | Status |
|---|---|---|---|
| 1 | — | Short title; commencement by notification | operative on enactment (s.1(2) is the power used) |
| 2 | s.3 | New defs: (27A) registered valuer; (31A) service provider; Explanation to (31): security interest only if created by agreement of parties, not by operation of law | IF |
| 3 | s.5 | New (2A) "avoidance transaction"; (9A) fraudulent/wrongful trading; s.5(11) proviso (initiation date = first of multiple applications); (26) Explanation adds sale of assets via multiple plans; (28) voting-eligible members | IF |
| 4 | s.7 | Proviso to s.7(4) omitted; **s.7(5) substituted ("shall ... admit/reject" within 14 days; 7-day rectification; record reasons for delay; Expl. I no other ground; Expl. II IU record sufficient for FIs)** | IF |
| 5 | s.9 | s.9(3)(e) "as may be specified"; **new 2nd proviso to s.9(5): record reasons if no order within 14 days** | IF |
| 6 | s.10 | s.10(3) revised ((b) omitted); disciplinary-proceeding limbs removed from s.10(4); new proviso, record reasons if >14 days | IF |
| 7 | s.11(ba) | Adds "or Chapter IV-A" (bar after CIIRP plan) | **NIF** |
| 8 | s.12A | Substituted: withdrawal on RP's application with 90% CoC; barred before CoC constitution and after first invitation for plans; order within 30 days | IF |
| 9 | s.14 | s.14(1) refers to (2A); Explanation to (3)(b): moratorium covers a surety's action against the CD under a guarantee | IF |
| 10 | s.16 | IRP = FC-proposed RP if no disciplinary proceedings; new (3A) IBBI recommends IRP for s.10 cases | IF |
| 11 | s.18(b) | Claims "in such manner as may be specified"; IRP to verify and value claims | IF |
| 12 | s.19 | Cooperation duty extended to promoters, contractors, persons in management | IF |
| 13 | s.21 | New s.21(11): CoC supervises liquidation (applies to new and certain ongoing liquidations) | IF |
| 14 | s.22(3)(a) | CoC-proposed RP deemed appointed from date of resolution | IF |
| 15 | s.25(2)(j) | RP to file avoidance/fraudulent-trading applications | IF |
| 16 | s.26 | Substituted: avoidance proceedings survive CIRP/liquidation completion | IF |
| 17 | new s.28A | Transfer of guarantor's assets (secured creditor in possession) during CIRP with CoC approval | IF |
| 18 | s.30 | New s.30(2)(ba): dissenting-FC floor (lower of liquidation value or s.53 waterfall); Expl. II transitional; s.30(2)(d) monitoring committee; s.30(4) reasons for approval | IF |
| 19 | s.31 | Phased approval proviso; rectification notice before rejection; **s.31(2A) 30 days**; new s.31(5)–(6) licences continue and clean slate; Expl. III deemed retrospective (except matters attained finality) | IF |
| 20 | s.33 | Fast-track reference removed; liquidation moratorium; **s.33(1A)/(1B) CIRP restoration ≤120 days, once**; dissolve option; **s.33(2A) 30 days**; s.33(5) omitted; new s.33(6) | IF |
| 21 | s.34 | Liquidator via IBBI recommendation; CIRP RP cannot be liquidator; IBBI names within 10 days | IF |
| 22 | new s.34A | CoC (66%) may replace liquidator | IF |
| 23 | s.35 | Liquidator duties revised; CoC supervises; Expl.: ss.38–42 changes not for pre-commencement liquidations | IF |
| 24 | s.36(3)(f) | Wording on avoidance/fraudulent-trading proceedings | IF |
| 25 | ss.38–42 | **Omitted** (liquidation claims process, incl. s.42 appeal against liquidator's decision); saved for liquidations initiated on or before commencement (s.35 Expl.) | IF |
| 26 | s.43(4) | Look-back runs from initiation date to commencement date | IF |
| 27 | s.46 | "Undervalued" transactions; same look-back change | IF |
| 28 | s.47 | Substituted: creditor, member or partner may apply where RP/liquidator has not reported avoidance/fraudulent trading; IBBI disciplinary referral | IF |
| 29 | s.49 | Proviso covers related parties | IF |
| 30 | s.50(1) | Look-back from two years before initiation date | IF |
| 31 | s.52 | **s.52(2): secured creditor must elect within 14 days of liquidation commencement, else deemed relinquished; 66% inter-creditor consent**; s.52(8) substituted; Expl. (not for liquidations initiated on or before commencement) | IF |
| 32 | s.53 | Explanations: relinquished-security split; government dues 2-year rule; Illustrations on subordination agreements | IF |
| 33 | s.54 | Liquidation in 180 days (+ ≤90); (1A)/(1B) pending proceedings; (2A)/(2B) dissolution on CoC decision; **(4) dissolution order in 30 days** | IF |
| 34 | s.54A | (a)(i)–(ii): CIIRP cross-references | **NIF** |
| 34 | s.54A | (a)(iii), (b): PPIRP approval threshold 66% → 51% | IF |
| 35–38 | ss.54C, 54F, 54L, 54N | PPIRP information; cooperation duty; plan rectification notice; cross-refs | IF |
| 39 | Ch. IV (ss.55–58) | **Fast-track CIRP omitted** | IF |
| 40 | new Ch. IV-A (ss.58A–58H, 58-I, 58J, 58K) | **Creditor-initiated insolvency resolution process** (notified CDs; notified FIs with 51% approval appoint RP after ≥30-day representation notice; CD objection to AA within 30 days of commencement (s.58C); 150 days + ≤45 (s.58D)) | **NIF** |
| 41 | s.59 | Voluntary liquidation ≤1 year; termination mechanism (5A)–(5C) | IF |
| 42 | new Ch. VA (s.59A) | **Group insolvency** (rules by Central Government; draft rules laid before Parliament for 30 days) | **NIF** |
| 43 | s.61(6) | **NCLAT to dispose of appeal within 3 months** | IF |
| 44 | new s.64A | Penalty ₹1 lakh–₹2 crore for frivolous or vexatious Part II proceedings | IF |
| 45 | s.65(3) | CIIRP reference | **NIF** |
| 46 | s.66 | "Fraudulent or wrongful trading"; liquidator can apply | IF |
| 47 | s.67A | CIIRP reference | **NIF** |
| 48 | new ss.67B, 67C | Civil penalties: moratorium or plan contravention (67B); **OC concealing dispute or payment in s.9 application (67C)** | IF |
| 49, 50 | ss.74, 76 | **Omitted** (offences decriminalised; prosecutions pending before commencement saved by s.235A Expl. II) | IF |
| 51–58 | ss.96, 99, 106, 121, 124, 164A, 178, 183A | Part III (personal insolvency): interim-moratorium carve-outs for personal guarantors; s.99(1) RP report 10 → 21 days; repayment-plan failure; transactions defrauding creditors; govt-dues Explanation; frivolous-proceedings penalty | IF |
| 59 | s.196 | "Service providers"; IBBI fees; CoC conduct standards and decision timelines (new (sa)) | IF |
| 60 | s.208(1)(cb) | CIIRP function of IPs | **NIF** |
| 61–64 | ss.214, 215, 217, 218 | IU authentication manner; **s.215(3) OC must submit to IU before s.9 application; s.215(4) deemed authentication**; complaints and investigation of service providers | IF |
| 65, 66 | ss.219, 220 | Show-cause procedure; disciplinary committees; penalty to ₹2 crore; **appeal to NCLAT 30 + 15 days from receipt** | IF |
| 67 | s.224 | Insolvency and Bankruptcy Fund: new sources; contributor withdrawal | **NIF** |
| 68 | s.235A | Substituted: AA-imposed penalty ≥₹1 lakh/day, up to 3× loss or gain (cap ₹5 crore if unquantifiable); saving for pending prosecutions | IF |
| 69(a) | s.239(1) | "provisions" → "purposes" | IF |
| 69(b) | s.239(2) | Omit (ea); add rule-making heads for ss.58B, 58C, 59A, 224, 240C | **NIF** |
| 70(a), 70(b)(i)–(xxvi) except (xx) | s.240 | IBBI regulation-making heads for the in-force changes | IF |
| 70(b)(xx) | s.240(2)(zla)–(zll) | Regulation-making heads for Ch. IV-A | **NIF** |
| 71 | new ss.240B, 240C | **Electronic portal (240B); cross-border insolvency rules (240C)** | **NIF** |
| 72 | s.242(1A) | Removal-of-difficulties power for 5 years from commencement | IF |

#### 8.3 Point-in-time and "enacted but not in force" test suite (expected answers)
| # | Question | Expected answer | Anchors |
|---|---|---|---|
| Q1 | On **20 May 2026**, what was the s.7 admission rule? | AA "shall, within fourteen days ... ascertain the existence of a default" (s.7(4)). If satisfied, it "**may**, by order, admit" (s.7(5)(a)). The s.7(4) proviso required recorded reasons if not done in time. The 14 days are directory (Surendra). Discretion was confined by *M. Suresh Kumar Reddy* (Vidarbha limited to its facts). | [I-R4], [I-R12], [I-R19], [I-R20] |
| Q2 | On **1 June 2026**, same question | s.7(5) as substituted: AA "**shall**, within fourteen days ... admit" if default, completeness and no disciplinary proceeding against the proposed RP are shown. Explanation I: no other ground. Explanation II: an IU record suffices for a financial institution. Delay → record reasons. Status IF from 26.05.2026 via **Amendment Act s.4**. The 14-day period is *not* new. | [I-R1] s.4, [I-R2] |
| Q3 | Is **section 7 of the IBC (Amendment) Act 2026** in force on 1 June 2026? (trap) | **No.** AA s.7 (adding "or Chapter IV-A" to Code s.11(ba)) is not notified. The amendment to **Code s.7** is AA **s.4**, which is in force. The engine must distinguish amending-Act numbering from Code numbering. | [I-R1], [I-R2] |
| Q4 | On **1 Oct 2026**, can a bank initiate the creditor-initiated insolvency resolution process, or can a CD object under s.58C within 30 days? | **No.** Ch. IV-A (AA s.40) is enacted, not in force. No notification as of 2026-10-01. Answer must carry the "ENACTED NOT IN FORCE" banner and a watchlist hook. (A LiveLaw report saying otherwise is wrong on this point.) | [I-R2], [I-R3], [I-R31] |
| Q5 | On **20 May 2026** vs **1 June 2026**, is fast-track CIRP (Ch. IV) available? | 20 May: yes (ss.55–58 in the Code). 1 June: **no**, omitted by AA s.39 w.e.f. 26.05.2026. Treatment of pending fast-track processes: TO VERIFY (GCA s.6 savings). | [I-R1], [I-R2], [I-R4] |
| Q6 | An OC files a s.9 petition on **1 June 2026** without submitting financial information to an IU. Maintainable? | Contestable. s.215(3) as amended (IF 26.05.2026): OC "**shall, before filing an application under section 9**" submit financial information. The "form and manner" depends on IBBI regulations (operationalisation TO VERIFY). On 20 May 2026 the obligation was "may" (optional). | [I-R1] s.62, [I-R4] |
| Q7 | An OC concealed the CD's dispute notice in its s.9 affidavit. What sanction applies on 20 May 2026 vs 1 June 2026? | 20 May: **s.76** offence ("imprisonment for a term which shall not be less than one year but may extend to five years or with fine which shall not be less than one lakh rupees but may extend to one crore rupees, or with both"). 1 June: **s.67C** civil penalty ₹1 lakh–₹2 crore imposed by the AA on application by IBBI or the Central Government. s.76 omitted (AA s.50). A prosecution pending before 26.05.2026 continues (s.235A Expl. II). | [I-R1], [I-R4] |
| Q8 | Is the cross-border insolvency framework (s.240C) or group insolvency (s.59A) usable on 1 Oct 2026? | **No.** AA ss.71 and 42 are not notified. Rule-making heads (AA s.69(b)) are also not in force. | [I-R2] |
| Q9 | Within what time must NCLAT decide an IBC appeal received on 10 June 2026? | New s.61(6): "within three months from the date of its receipt", i.e. by about 10 Sep 2026. A target only (consequence unstated; nature TO VERIFY). For an appeal received on 20 May 2026 the provision did not exist (s.64(1) general rule). | [I-R1] s.43 |
| Q10 | A CD's default occurred on 15 Jan 2021. Can an FC file s.7 on 1 June 2026 if the amount is ₹5 crore? | **No, ever.** s.10A proviso: the default falls in the suspension window (25.03.2020–24.03.2021, per S.O. 3265(E) and 4638(E)). Also independent of the 2026 Act. | [I-R4], [I-R8], [I-R9], [I-R17] |
| Q11 | A ₹60 lakh operational default from 2019; s.9 filed on 1 June 2026. Maintainable? | No. The ₹1 crore threshold (S.O. 1205(E)) applies by **filing date** (NCLAT, *Jumbo Paper*). Separately, prima facie time-barred (Art. 137) unless acknowledged. | [I-R7], [I-R29], [I-R13] |
| Q12 | A secured creditor in a liquidation commenced on 1 June 2026 has not told the liquidator within 14 days that it will realise its security. Result? And for a liquidation commenced on 1 May 2026? | 1 June: deemed relinquished to the liquidation estate (s.52(2) as substituted). 1 May: the amended s.52(2) does **not** apply (s.52 Explanation: not for liquidations initiated on or before commencement). | [I-R1] s.31 |

---

### 9. General-mode notes (cannot yet be anchored; run without a deadline guarantee)

- **Reply and rejoinder periods before NCLT in s.7/s.9 matters:** no statutory period. NCLT Rules r.37(3) only says "before the date of hearing". Capture the bench's order-sheet direction as a lawyer-entered deadline. TO VERIFY WITH PARTNER: typical bench practice and any NCLT standing orders or SOPs for IBC petitions.
- **Directory or mandatory character of the 2026 "record reasons" timelines** (ss.7(5), 9(5), 10(4), 12A(3), 31(2A), 33(2A), 54(4)) and of s.61(6): no post-commencement ruling found. Treat as AA-side targets, never as party deadlines.
- **Transitional application** of the new s.7(5) (Explanation I) to s.7 petitions pending on 26.05.2026: the Act has no saving clause for s.7. Procedural-vs-substantive analysis is needed. TO VERIFY.
- **s.215(3) IU pre-filing:** depends on IBBI Information Utilities regulations. IBBI issued a 2026 discussion paper [I-R33]; whether final regulations are notified is unknown. TO VERIFY.
- **Meaning of "receipt" in s.62** (pronouncement in presence vs. receipt of copy) and the Supreme Court Rules 2013 filing mechanics: TO VERIFY.
- **COVID limitation exclusion** (15.03.2020–28.02.2022): rests on a snippet. Needed for any default or acknowledgment chain that crosses 2020–22. TO VERIFY before any golden test uses it.
- **Delivery disputes under s.8** (courier, refused or unclaimed RPAD, email to a non-KMP): a large body of NCLAT case law; nothing verified here. Show as an "issue to research" in the memo, not a rule.
- **IBBI CIRP Regulations** (claims timelines, model timeline, Reg. 30A withdrawal mechanics, now superseded by the new s.12A "manner as may be specified"): not researched. IBBI consulted on CIRP changes in April 2026 [I-R34b]. TO VERIFY.
- **Pre-2026 consolidated text:** relied on IBBI's 12.08.2021 consolidation plus the absence of any amending Act 2022–2025 in IBBI's listing. Spot-check on indiacode.

---

### 10. References

| Tag | Source | URL | Status |
|---|---|---|---|
| I-R1 | IBC (Amendment) Act 2026 (No. 6 of 2026), Gazette Extraordinary Part II s.1 No. 11, 06.04.2026 (full text read) | https://ibbi.gov.in/uploads/legalframwork/2026-04-07-115842-i5nsk-7ed69ef2a4d23a8b0d472cc0fcd55e79.pdf | verified |
| I-R2 | MCA S.O. 2625(E), 22.05.2026, Gazette Extraordinary Part II s.3(ii) No. 2533, 25.05.2026 (full text read) | https://ibbi.gov.in/uploads/legalframwork/d31669ba7f826ee9ebefe58e85d652ec.pdf | verified |
| I-R3 | IBBI notifications listing (fetched 2026-10-01; latest 08.07.2026) | https://ibbi.gov.in/en/legal-framework/notifications | verified |
| I-R4 | IBC 2016, IBBI consolidated text upto 12.08.2021 (ss.4, 5, 7–12A, 14, 61, 62, 76, 215, 238A read) | https://ibbi.gov.in/uploads/legalframwork/2022-04-28-181717-r28jw-af0143991dbbd963f47def187e86517f.pdf | verified |
| I-R5 | IBBI Act listing (no amending Act between 2021 and 2026; 2025 Bill introduced 12.08.2025) | https://ibbi.gov.in/en/legal-framework/act | verified |
| I-R6 | IBC (Application to Adjudicating Authority) Rules 2016, upto 24.09.2020 (rr.4–10 read); IBBI rules listing | https://ibbi.gov.in//uploads/legalframwork/97f265ffe63b83fa6ca7c2c01795be66.pdf ; https://ibbi.gov.in/en/legal-framework/rules | verified |
| I-R7 | S.O. 1205(E), 24.03.2020 (₹1 crore threshold) | https://ibbi.gov.in/uploads/legalframwork/48bf32150f5d6b30477b74f652964edc.pdf | verified |
| I-R8 | S.O. 3265(E), 24.09.2020 (s.10A extension) | https://ibbi.gov.in/uploads/legalframwork/2987e1e33d62d2e1781c700ee16baa36.pdf | verified |
| I-R9 | S.O. 4638(E), 22.12.2020 (s.10A extension) | https://ibbi.gov.in/uploads/legalframwork/df55d4f612f270d6c637ee4b3c8131c8.pdf | verified |
| I-R10 | Mobilox Innovations v Kirusa Software, (2018) 1 SCC 353 (paras 24, 29, 40) | https://indiankanoon.org/doc/166780307/ | verified |
| I-R11 | Kay Bouvet Engineering v Overseas Infrastructure Alliance, AIR 2021 SC 4199 (10.08.2021) | https://indiankanoon.org/doc/49414702/ | verified |
| I-R12 | Surendra Trading Co v Juggilal Kamlapat Jute Mills, 2017 (16) SCC 143 (paras 14, 18, 23–25) | https://indiankanoon.org/doc/156252615/ | verified |
| I-R13 | B.K. Educational Services v Parag Gupta & Associates, 2019 (11) SCC 633 (para 27) | https://indiankanoon.org/doc/4992553/ | verified |
| I-R14 | Asset Reconstruction Co (India) v Bishal Jaiswal (SC, 15.04.2021), AIRONLINE 2021 SC 267 (para 33); "(2021) 6 SCC 366" citation | https://indiankanoon.org/doc/107688497/ | verified (SCC cite: snippet) |
| I-R15 | Dena Bank v C. Shivakumar Reddy (SC, 04.08.2021) (paras 118, 143–144); "(2021) 10 SCC 330" citation | https://indiankanoon.org/doc/140970077/ | verified (SCC cite: snippet) |
| I-R16 | Laxmi Pat Surana v Union Bank of India, AIR 2021 SC 1707 (para 42) | https://indiankanoon.org/doc/12052125/ | verified |
| I-R17 | Ramesh Kymal v Siemens Gamesa Renewable Power, AIR 2021 SC 833 (paras 8, 26–27) | https://indiankanoon.org/doc/108671199/ | verified |
| I-R18 | CoC of Essar Steel v Satish Kumar Gupta (SC, 15.11.2019), (2019) 16 SCALE 319 ("mandatorily" struck down) | https://indiankanoon.org/doc/7427609/ | verified |
| I-R19 | Vidarbha Industries Power v Axis Bank (SC, 12.07.2022) (paras 30–31) | https://indiankanoon.org/doc/192959010/ | verified |
| I-R20 | M. Suresh Kumar Reddy v Canara Bank (SC, 11.05.2023) (paras 12–13) | https://indiankanoon.org/doc/131399423/ | verified |
| I-R21 | V. Nagarajan v SKS Ispat & Power, (2022) 2 SCC 244 (22.10.2021) | https://indiankanoon.org/doc/182291550/ | verified (holding via R23, R24) |
| I-R22 | Sanket Kumar Agarwal v APG Logistics (SC, 01.05.2023) (paras 19–24) | https://indiankanoon.org/doc/72267455/ | verified |
| I-R23 | Sanjay Pandurang Kalate v Vistra ITCL, (2024) 3 SCC 27 (04.12.2023) (paras 13–21) | https://indiankanoon.org/doc/62674739/ | verified |
| I-R24 | Tata Steel v Raj Kumar Banerjee, 2025 INSC 639 (07.05.2025) (paras 10.1–11.1, 13) | https://indiankanoon.org/doc/103070905/ | verified |
| I-R25 | Sagufa Ahmed v Upper Assam Plywood (SC, 18.09.2020) (paras 21–23) | https://indiankanoon.org/doc/105327534/ | verified |
| I-R26 | Saketh India v India Securities, AIR 1999 SC 1090 | https://indiankanoon.org/doc/796212/ | verified |
| I-R27 | (a) GCA 1897 s.9; (b) GCA s.27; (c) Limitation Act 1963 s.4 | https://indiankanoon.org/doc/1353686/ ; https://indiankanoon.org/doc/1428703/ ; https://indiankanoon.org/doc/1393166/ | verified |
| I-R28 | NCLT Rules 2016 r.37 (secondary host) | https://ca2013.com/rule-37-national-company-law-tribunal-rules-2016/ | verified (secondary) |
| I-R29 | Jumbo Paper Products v Hansraj Agrofresh (NCLAT CA(AT)(Ins) 813/2021) as quoted in NCLT Kolkata IA(IB) 995/KB/2021 and NCLT New Delhi C.P.(IB) 154/ND/2022 (30.11.2023) | https://ibbi.gov.in/uploads/order/95b0385db484bc5c32714f2341165f17.pdf ; https://ibbi.gov.in/uploads/order/40fe6c148a028a660df40996f60cdf10.pdf | verified (secondary) |
| I-R30 | In re Cognizance for Extension of Limitation, order 10.01.2022, (2022) 3 SCC 117 | https://www.scconline.com/blog/post/2023/09/22/cognizance-for-extension-of-limitation-in-re-operative-effect-of-the-supreme-courts-order-dated-10-1-2022-a-case-comment/ | snippet |
| I-R31 | LiveLaw, 26.05.2026, "Centre Notifies Key IBC Amendment Provisions, Operationalises Creditor-Initiated Insolvency Resolution Process" (contradicted by R2) | https://www.livelawbiz.com/compliance/ibc/centre-notifies-key-ibc-amendment-provisions-operationalises-creditor-initiated-insolvency-resolution-process-535725 | snippet (wrong on CIIRP) |
| I-R32 | ibclaw.in and TaxGuru reproductions of S.O. 2625(E) (consistent with R2) | https://ibclaw.in/appointing-26-may-2026-as-the-date-for-certain-provisions-of-ibc-amendment-act-2026/ ; https://taxguru.in/corporate-law/mca-notifies-key-ibc-amendment-provisions-effective-262026.html | verified (secondary) |
| I-R33 | IBBI discussion paper on IU regulations (2026) | https://ibbi.gov.in/uploads/public_comments/DP%20-%20IU%20Website%20version%202026.pdf | snippet |
| I-R34 | (a) AIR News: Parliament passes IBC Bill 2026 (01.04.2026); (b) IBBI CIRP discussion paper annex (15.04.2026) | https://www.newsonair.gov.in/parliament-passes-insolvency-and-bankruptcy-code-bill-2026 ; https://ibbi.gov.in/uploads/public_comments/Annex%20A%20-%20DP%20-%20CIRP%20-%20150426.pdf | snippet |
| I-R35 | iPleaders: cross-border and group insolvency not in force | https://blog.ipleaders.in/cross-border-and-group-insolvency-under-the-ibc-amendment-act-2026/ | snippet |
| I-R36 | Cyril Amarchand blog, "Vidarbha – the final chapter" (Jul 2026); no post-amendment case law reported | https://disputeresolution.cyrilamarchandblogs.com/2026/07/vidarbha-the-final-chapter/ | verified (secondary) |
| I-R37 | Blueprint RuleSpec format | /home/user/legal/docs/08_P6_strategic_reasoning.md §5.5.1 | internal |


---

# Part B — Companies Act and LLP

*Source pack title: Companies Act trigger rules (T-CA-1 to T-CA-6): RuleSpecs, authorities, draft-output outlines*

**Researcher:** Companies Act rules agent · **As of:** 1 October 2026 · **Scope:** Companies Act 2013 (CA), NCLT Rules 2016, NCLAT Rules 2016, Companies (Adjudication of Penalties) Rules 2014 (CAP Rules), LLP Act 2008 (brief), Corporate Laws (Amendment) Bill 2026 (watchlist only).
**Evidence convention:** follows `mvp_brief.md`. Reference tags: `[Rn]`, listed at the end with `verified` / `snippet` / `unverified`. RuleSpec status values: VERIFIED-PRIMARY | VERIFIED-SECONDARY | TO VERIFY WITH PARTNER. Nature values: HARD | CONDONABLE (cap) | DIRECTORY | PRACTICE. I add one more label, ORDER-SET, for a deadline fixed by a tribunal or officer's order or notice and not by statute. The engine must read that date from the document and must never default it.

> **Point-in-time caveat (applies throughout).** I could not reach India Code (Akamai error) or eGazette (TLS chain failure through the proxy). I verified the *as-enacted* text from the Gazette copy of the Act hosted on nclt.gov.in [C-R1] and from Indian Kanoon [C-R2]. I verified the *current* text of ss.164(2), 167(1)(a), 242(8), 271, 441(1), 454(1)/(5)/(7)/(8), 454A and 446B from the "Extracts from the Companies Act, 2013" annexure printed in the Corporate Laws (Amendment) Bill 2026, Bill No. 85 of 2026 [C-R3]. That annexure reproduces the law as it stands today. Any provision quoted only "as enacted" is flagged. Before go-live, confirm it against the India Code consolidated text.

---

### 0. Summary of rules

| rule_code | What | Period | Nature | Status |
|---|---|---|---|---|
| CA.S241.LIMITATION | Time bar for oppression/mismanagement petition | 3 years (Art.113 or Art.137 via s.433; the NCLAT is divided on which) | HARD-but-contested (screening only, not a deadline) | TO VERIFY WITH PARTNER (law VERIFIED-SECONDARY) |
| CA.S244.ELIGIBILITY | Standing to file under s.241 | 100 members / 1/10 members (whichever is less) / 1/10 issued capital; 1/5 for non-share cos; waiver | Eligibility test (no date) | VERIFIED-PRIMARY |
| NCLT.R37.REPLY | Reply to s.241 petition | "before the date of hearing" (Rule 37(3)); actual days set by bench order | ORDER-SET / PRACTICE | VERIFIED-PRIMARY (rule) |
| NCLT.REJOINDER | Rejoinder | No rule; set by bench order | ORDER-SET | VERIFIED-PRIMARY (absence of a rule) |
| CA.S242_4.INTERIM | Interim relief | No time limit | n/a | VERIFIED-PRIMARY |
| CA.S422.DISPOSAL_3M | Tribunal/NCLAT disposal target | "every endeavour… within three months" | DIRECTORY | VERIFIED-PRIMARY |
| CA.S421_3.NCLAT_APPEAL | Appeal NCLT→NCLAT (Companies Act orders) | 45 days from copy "made available" + ≤45 on sufficient cause; nothing beyond 90 | CONDONABLE (cap 45) | VERIFIED-PRIMARY (text) + VERIFIED-SECONDARY (Bengal Chemists; Sagufa Ahmed) |
| CA.S423.SC_APPEAL | Appeal NCLAT→SC | 60 days from "receipt of the order" + ≤60 | CONDONABLE (cap 60) | VERIFIED-PRIMARY (text); s.423-specific ruling TO VERIFY |
| CAP.R3_2.SCN_REPLY | Reply to adjudication show-cause notice | Period fixed in notice: 15–30 days from service | ORDER-SET (statutory band) | VERIFIED-SECONDARY (2019 rule text via IK) |
| CAP.R3_4.REPLY_EXTENSION | AO extension | ≤15 further days, discretionary | CONDONABLE (cap 15) | VERIFIED-SECONDARY |
| CAP.R3_7.AO_ORDER | AO's own timeline to pass order | 30 days / 90 days | DIRECTORY (the rule itself says a late order is not invalid) | VERIFIED-SECONDARY |
| CA.S454_6.RD_APPEAL (+CAP.R4) | Appeal from AO order to Regional Director | 60 days from receipt of copy; Form ADJ | HARD (no condonation power found) | VERIFIED-PRIMARY (s.454(6) as enacted) + VERIFIED-SECONDARY (Rule 4) |
| CA.S454_8.COMPLY_90D | Pay or comply with AO/RD order | 90 days from receipt of copy; prosecution exposure after | HARD (penal consequence) | VERIFIED-PRIMARY (current text via Bill annexure) |
| CA.S454A.REPEAT_3Y | Repeat-default doubling window | Same default within 3 years of penalty order → 2× penalty | Look-back window | VERIFIED-PRIMARY (current text via Bill annexure) |
| CA.S441.TIMING | Compounding: when it can be applied for | No limitation period; barred while investigation initiated or pending, and within 3 years of a prior compounding of a similar offence | Eligibility bars | VERIFIED-PRIMARY |
| CA.S441_3B.INTIMATION_7D | Company to intimate ROC after compounding | 7 days from compounding | HARD | VERIFIED-PRIMARY (as enacted) |
| LLP.S76A_6.RD_APPEAL | LLP adjudication appeal to RD | 60 days + RD may extend ≤30 | CONDONABLE (cap 30) | VERIFIED-SECONDARY (IK text as amended 2021) |
| LLP.S76A_8_9.COMPLY_90D | LLP pay or comply with order | 90 days from receipt | HARD (penal) | VERIFIED-SECONDARY |
| CA.S230_4/5, CA.S233_1A | Scheme objection / representation windows | 1 month / 30 days | general mode | VERIFIED-PRIMARY (as enacted) |
| WATCH.CLAB2026 | Corporate Laws (Amendment) Bill 2026 | n/a (BILL) | WATCHLIST | VERIFIED-SECONDARY (PRS) + VERIFIED-PRIMARY (bill text) |

---

### 1. Common computation conventions (shared by all CA rules)

- **Exclusion of the first day.** General Clauses Act 1897 s.9(1): "it shall be sufficient, for the purpose of excluding the first in a series of days or any other period of time, to use the word 'from'…" [C-R18]. Every CA period below runs "from" a date, so day 0 is excluded and the last day is included. The SC's arithmetic in *Sagufa Ahmed* (copy received 19.12.2019 → 45 days "expired on 02.02.2020") matches this convention [C-R20].
- **Limitation Act brought in for NCLT/NCLAT only.** CA s.433: "The provisions of the Limitation Act, 1963 (36 of 1963) shall, **as far as may be**, apply to proceedings or appeals before the Tribunal or the Appellate Tribunal, as the case may be." [C-R1][C-R2]. The words "as far as may be" stop Limitation Act s.5 from overriding the capped proviso in s.421(3) (*Bengal Chemists*, §3) and also defeated a claim to s.15(2) exclusion [C-R21].
- **Court closed on the last day (NCLT/NCLAT/SC).** Limitation Act s.4: "Where the prescribed period for any suit, appeal or application expires on a day when the court is closed, the suit, appeal or application may be instituted, preferred or made on the day when the court reopens." [C-R19]. s.29(2) applies ss.4–24 to special-law periods "only in so far as, and to the extent to which, they are not expressly excluded" [C-R19]. **Engine rule:** for the *base* statutory period, output the raw date plus a roll-forward to the next open day, flagged as "s.4 roll-forward". Apply **no** roll-forward to the *condonation/extension window* until the partner confirms; the SC has refused s.4 on an extended window in an analogous arbitration context (*Assam Urban Water Supply*, (2012) 2 SCC 624; I have not verified it) [C-R32]. Vectors below are chosen so that base dates fall on weekdays.
- **Offices (ROC/AO/RD) closed on the last day.** The Limitation Act applies only to courts (*Sakuru v Tanaji* (1985) 3 SCC 590, from memory, not verified [C-R33]; s.433 extends it only to NCLT/NCLAT). For AO/RD steps, GCA s.10(1) applies: "if the Court or office is closed on that day or the last day of the prescribed period, the act or proceeding shall be considered as done or taken in due time if it is done or taken on the next day afterwards on which the Court or office is open", with the proviso excluding acts governed by the Limitation Act [C-R18]. Whether an always-on **e-adjudication platform** counts as an "office" that can be "closed" is **TO VERIFY WITH PARTNER**. Until then, show the raw date as the deadline and the GCA s.10 date as an advisory.
- **Calendar days throughout.** No CA provision below uses working days. The one exception is CAP Rule 3(5), which binds the AO and says "ten working days".

---

### T-CA-1 Oppression and mismanagement (ss.241–244) — petitioner or respondent

#### 1.1 Statutory frame (verified)
- **s.241(1)** lets "Any member" apply where (a) affairs "have been or are being conducted in a manner prejudicial to public interest or in a manner prejudicial or oppressive to him or any other member or members or in a manner prejudicial to the interests of the company", or (b) a material change in management or control makes prejudicial conduct likely, "provided such member has a right to apply under section 244" [C-R1][C-R2]. Under s.241(2) the Central Government may itself apply (sub-ss. (3)–(4) were added in 2017; the as-enacted text I read predates them, so confirm on India Code).
- **s.242(4) interim relief:** "The Tribunal may, on the application of any party to the proceeding, make any interim order which it thinks fit for regulating the conduct of the company's affairs upon such terms and conditions as appear to it to be just and equitable." [C-R1]. **No time limit.**
- **s.242(8)** (current text): it is an offence for a company to alter its memorandum or articles contrary to s.242(5) without leave. The Bill would omit it (cl.71), leaving contempt under s.425 [C-R3].
- **s.422(1):** "every endeavour shall be made … for the disposal of such application or petition or appeal within three months from the date of its presentation". Under s.422(2) the Tribunal must record reasons if it misses this. The provision is **DIRECTORY** on its face ("every endeavour"; consequence is recording reasons) [C-R1].

#### 1.2 RuleSpec CA.S244.ELIGIBILITY
- **Anchor (VERIFIED-PRIMARY):** s.244(1)(a): "in the case of a company having a share capital, not less than one hundred members of the company or not less than one-tenth of the total number of its members, **whichever is less**, or any member or members holding not less than one-tenth of the issued share capital of the company, subject to the condition that the applicant or applicants has or have paid all calls and other sums due on his or their shares"; (b) "in the case of a company not having a share capital, not less than one-fifth of the total number of its members". Proviso: "the Tribunal may, on an application made to it in this behalf, waive all or any of the requirements specified in clause (a) or clause (b)". Explanation: joint holders "shall be counted only as one member". s.244(2): one or more may apply for all "having obtained the consent in writing of the rest" [C-R1][C-R2].
- **Procedure (VERIFIED-SECONDARY, consolidated to the 2020 amendment):** NCLT Rule 81(1): petition in **Form NCLT-1** with Annexure B documents. Rule 81(2): consent letters must be annexed, with a schedule of names and addresses and a statement that calls are paid. Rule 81(3): "A copy of every application made under this rule shall be served on the company, other respondents and all such persons as the Tribunal may direct". Rule 82: no withdrawal without leave (Form NCLT-9). **Rule 83A** (inserted by G.S.R. 1159(E), 20.12.2016): waiver application under s.244 "in Form No. NCLT. 9" [C-R10]. The NCLT's own list of procedure-rule amendments ends with the 2020 amendment rules, so the consolidated IK text is current [C-R11].
- **Interpretation:**
  - *Cyrus Investments v Tata Sons* (NCLAT, 21.09.2017): waiver granted in "exceptional circumstances". Petitioners held about 18% of equity but only 2.71% of issued capital once preference capital was counted. A waiver order must be a reasoned order passed after notice [C-R28] `snippet`.
  - *Neeraj Gupta v A-1 Equipments* (NCLAT, 09.09.2022): a s.244 application is not time-barred under Art.137 and needs no condonation application [C-R27] `verified`.
- **Golden vectors (rule verified; non-date):**
  1. 650 members (share capital), 70 petitioners, calls paid → threshold = min(100, 65) = 65 → **eligible**.
  2. 2,000 members, 90 petitioners holding 12% of issued share capital → member limb fails (needs 100), capital limb passes (≥10%) → **eligible**.
  3. Non-share-capital company with 50 members, 9 petitioners → needs 10 (one-fifth) → **ineligible → waiver route (Rule 83A, Form NCLT-9)**.
- **Notes:** the engine must count joint holders once. It must treat "issued share capital" as possibly including preference capital (Cyrus, `snippet`; TO VERIFY WITH PARTNER). It must check the calls-paid condition.

#### 1.3 RuleSpec CA.S241.LIMITATION (screening rule, not a filing deadline)
- **Trigger event:** the date the right to apply "accrues". On the NCLAT's approach, that is when the petitioner knew or became aware of the antecedent facts (*Vijay Kumar Agarwal v Juhu Hotel*, NCLAT CA(AT) 197/2025, quoted in [C-R26]: "Once a party becomes aware of the antecedent facts necessary to pursue a legal proceedings, the limitation period commences"). The **petitioner** must show knowledge or a continuing course of conduct. The **respondent** must plead and prove the bar.
- **Computation:** 3 years. The NCLAT has applied different articles:
  - **Art.113** ("Any suit for which no period of limitation is provided elsewhere… Three years… When the right to sue accrues") in *Esquire Electronics v Netherlands India Communications*, NCLAT CA(AT) 26/2016, quoted and followed in *Shefali Agrawal v Stone Age* (NCLAT, 14.05.2026) [C-R26]. Its holding: "the suit for which there is no prescribed period is provided as per Article 113 … period of limitation is three years … appellant(s) cannot rake up any issue which is barred by limitation i.e., of a period which is three years prior to the date of filing of the Petition."
  - **Art.137** ("Any other application for which no period of limitation is provided elsewhere in this division. Three years. When the right to apply accrues") [C-R19], applied to a s.59 rectification petition joined with a s.241 petition in *Niklesh Nihalani v Shah Poddar Nihlani Organisers* (NCLAT, 02.08.2021) [C-R25], relying on *Kerala SEB v T.P. Kunhaliumma* (1976) 4 SCC 634 (Art.137 covers petitions under special Acts).
  - **Continuing wrong:** Limitation Act s.22 [C-R19]. Petitioners rely on *M. Nandana Reddy*, 2023 SCC OnLine NCLAT 770, and *Surinder Singh Bindra* (Del HC, 1990). The NCLAT rejected the argument where the petitioner had knowledge, invoking *Khatri Hotels* (Art.58 "first accrues") [C-R26].
  - **Supreme Court:** *Chalasani Udaya Shankar v Lexus Technologies*, 2024 INSC 671 (09.09.2024). The NCLAT erred by going "simply … by the date of purchase of the shares and the date of the institution of the Company Petition", because limitation was "a mixed question of law in fact" requiring examination "as to when the clock would start ticking" [C-R23] `verified`. *Shailja Krishna v Satori Global*, 2025 INSC 1065 (02.09.2025), restored an NCLT order despite the respondents' plea that the CLB petition came "after a delay of two and half years" [C-R24].
- **Nature:** HARD in principle (suit-type bar; if Art.113 applies, s.5 condonation is unavailable for suits). It is contested in practice: which article applies, when time accrues, continuing wrong, and whether s.5 can apply if Art.137 governs are all open. **The engine must not present a deadline.** It should present an "acts older than 3 years before filing are at limitation risk" screen with the competing authorities.
- **Status:** law VERIFIED-SECONDARY. Which article the partner's bench favours: **TO VERIFY WITH PARTNER**.
- **Golden vectors:** none. Accrual is fact-dependent, so the brief's rule (vectors only for verified computations) excludes them.

#### 1.4 RuleSpec NCLT.R37.REPLY and NCLT.REJOINDER
- **Anchor (VERIFIED-PRIMARY, Gazette G.S.R. 716(E) 21.07.2016 [C-R9]; unchanged in the 2020 consolidation [C-R10]):**
  - Rule 37(1): "The Tribunal shall issue notice to the respondent to show cause against the application or petition on a date of hearing to be specified in the Notice. Such notice in Form No. NCLT.5 shall be accompanied by a copy of the application with supporting documents."
  - Rule 37(2): if the respondent does not appear, the Tribunal "after according reasonable opportunity … shall forthwith proceed ex-parte".
  - Rule 37(3): the respondent "may … file a reply accompanied with an affidavit and along with copies of such documents on which it relies, with an advance service to the petitioner or applicant, to the Registry **before the date of hearing**".
  - **No rule fixes days for reply or rejoinder.** Rule 34(1) and Rule 51 leave procedure to the Tribunal ("may regulate its own procedure in accordance with the rules of natural justice and equity"). CA s.424(1) frees the Tribunal from the CPC, so CPC Order VIII time limits do not apply of their own force [C-R1][C-R10].
- **Service:** Rule 38 allows post, courier, e-mail, hand delivery, party service or substituted service, with an affidavit of service. Rule 38A: "A petition shall be based upon a single cause of action" [C-R10]. Rule 35 advertisement applies only where a petition "is required to be advertised". It is not the default for s.241.
- **Practice (snippet only):** benches commonly direct a reply in 2–4 weeks and a rejoinder 1–2 weeks after that [C-R31]. **Nature:** ORDER-SET. The engine takes the date from the order sheet and offers no default.
- **Golden vectors:** n/a (no statutory computation).

#### 1.5 Authorities to pre-load (T-CA-1)
| Authority | Proposition (for retrieval tags) | Status |
|---|---|---|
| *Tata Consultancy Services Ltd v Cyrus Investments (P) Ltd*, **(2021) 9 SCC 449** (SC, 26.03.2021) | The Tribunal's relief must bring an end to the matters complained of. Removal of an executive chairman or director is not per se oppression. The s.242(1)(b) "just and equitable winding up" precondition is mandatory. Articles validly adopted cannot be overridden by "legitimate expectation". | Citation verified via [C-R24]; holdings `snippet` [C-R29] |
| *Shanti Prasad Jain v Kalinga Tubes*, 1965 SCC OnLine SC 15 / AIR 1965 SC 1535 | Oppression requires a lack of probity and burdensome, harsh and wrongful conduct affecting the member *as member*. | Citation verified via [C-R24] |
| *Needle Industries (India) Ltd v Needle Industries Newey (India) Holding Ltd*, (1981) 3 SCC 333 | A series of acts may amount to oppression. Equity is superimposed on legality. | Citation partly verified via [C-R24] ("(1981) 3 …"); page `unverified` |
| *Dale & Carrington Invt (P) Ltd v P.K. Prathapan*, (2005) 1 SCC 212 | Directors of a private company are tested "on a much finer scale" (allotments for control). | Verified via [C-R24] |
| *Sangramsinh P. Gaekwad v Shantadevi P. Gaekwad*, (2005) 11 SCC 314 | Scope of ss.397/398 and family-company disputes. | Citation verified via [C-R24] |
| *V.S. Krishnan v Westfort Hi-Tech Hospital*, (2008) 3 SCC 363 | Allotments to gain control can be oppression. | Verified via [C-R24] |
| *Shailja Krishna v Satori Global Ltd*, **2025 INSC 1065** (02.09.2025) | The NCLT has wide jurisdiction over matters "incidental and/or integral" to the complaint, including fraud and validity of a gift deed. Minority not to be left remediless. | Verified [C-R24] |
| *Chalasani Udaya Shankar v Lexus Technologies*, **2024 INSC 671** | Limitation is a mixed question. The NCLT/NCLAT must examine the material and not dismiss summarily. | Verified [C-R23] |
| *Esquire Electronics* (NCLAT CA(AT) 26/2016); *Shefali Agrawal* (NCLAT 14.05.2026); *Niklesh Nihalani* (NCLAT 02.08.2021) | 3-year limitation (Art.113 or Art.137); knowledge; continuing wrong rejected on facts. | Verified [C-R25][C-R26] |
| *Cyrus Investments v Tata Sons* (NCLAT 21.09.2017) | s.244 waiver criteria. | `snippet` [C-R28] |
| Candidates to verify: *Rajahmundry Electric Supply v A. Nageswara Rao*, AIR 1956 SC 213 (withdrawal of consent after filing); *World Wide Agencies v Margarat T. Desor*, (1990) 1 SCC 536 (heirs' locus) | Locus and maintainability. | `unverified`: TO VERIFY |

#### 1.6 Draft output — strategy memo (T-CA-1)
**A. If we act for the petitioner.**
1. *Their story / our story:* chronology of acts complained of (allotments, removals, related-party transactions, siphoning, denial of information, AGM defaults), each tagged to a document and a date.
2. *Maintainability:* the s.244 calculator (1.2), consents (Rule 81(2)), calls paid. Prepare a waiver application (Rule 83A) if the thresholds fail.
3. *Limitation screen (1.3):* bucket each act as within 3 years, outside 3 years but continuing, or outside 3 years and at risk. Record the knowledge-date evidence (MCA filings date, notice receipt).
4. *Grounds:* s.241(1)(a) limbs (oppressive / prejudicial to member / company / public interest), s.241(1)(b) material change, and the s.242(1)(b) just-and-equitable showing required by TCS v Cyrus.
5. *Reliefs menu:* s.242(2) heads and interim relief under s.242(4): status quo on shareholding, board and assets; injunction on EGM resolutions; inspection.
6. *Likely adverse authorities:* TCS v Cyrus (no oppression from a mere loss of confidence; reliefs confined); Esquire / Shefali (limitation); NCLAT Cyrus waiver standard ("exceptional"). Possible arbitration or civil-court objections. *Shailja Krishna* (2025) now cuts against the civil-court objection.
7. *Evidence checklist:* register of members and share ledger; MGT-7/annual returns; PAS-3 allotment filings; DIR-12; AOC-4 financials; board and general meeting notices, minutes and attendance; AoA/SHA; valuation reports; bank statements for siphoning; correspondence and legal notices; MCA V3 master-data snapshots with download date (proof of knowledge date).
8. *Deadlines panel:* none statutory for filing (limitation screen only). ORDER-SET dates from each order sheet. s.422 three-month DIRECTORY target as context. Appeal clock (T-CA-2) once the order is "made available".

**B. If we act for a respondent.**
1. Preliminary objections, in order: (i) s.244 standing or waiver (calls unpaid; joint holders counted once; consents defective); (ii) limitation (s.433 + Art.113/137; Chalasani makes this a mixed question, so plead facts and documents on the knowledge date); (iii) Rule 38A single cause of action / misjoinder; (iv) disputes about title or fraud as civil disputes (weakened after Shailja Krishna 2025, so flag risk); (v) no "just and equitable" case (TCS v Cyrus); (vi) suppression, delay, unclean hands.
2. Merits: business-judgment defence; acts were authorised under the AoA; acquiescence or participation by the petitioner (attendance at meetings, signatures).
3. Interim-relief opposition: no prima facie case, balance of convenience, undertaking offered instead of injunction.
4. Deadlines: reply "before the date of hearing" (Rule 37(3)) and the actual date from the NCLT order; advance service on the petitioner; ex parte risk under Rule 37(2).

#### 1.7 Reply skeleton / para-wise grid (reply to s.241 petition)
```
IN THE NATIONAL COMPANY LAW TRIBUNAL, <Bench> | C.P. No. __/241-242/<bench>/<yr>
REPLY ON BEHALF OF RESPONDENT NO. __ (with affidavit, Rule 37(3); advance copy served on petitioner)
I.   Preliminary submissions & objections
     1. Petition not maintainable — s.244(1) [calculator output; consents; calls] / no waiver under Rule 83A
     2. Barred by limitation — s.433 CA + Art.113/137 Limitation Act [table of acts > 3 yrs before filing; knowledge evidence]
     3. Multiple causes of action — Rule 38A NCLT Rules
     4. No case of oppression/mismanagement; s.242(1)(b) "just and equitable" test unmet — TCS v Cyrus (2021) 9 SCC 449
     5. Suppression / delay / acquiescence
II.  Brief facts (respondent's chronology, document-anchored)
III. Para-wise reply (grid below)
IV.  Reply to interim application (s.242(4))
V.   Prayer: dismiss petition with costs; vacate/decline interim relief
Verification / affidavit; list of documents (Annexure R-1…)
```
Para-wise grid columns: `Petition ¶ | Allegation (1-line) | Type (fact/law/doc) | Response (admitted / denied / not within knowledge / matter of record) | Our counter-facts | Annexure ref | Authority (anchor-pinned) | Limitation bucket | Risk flag`.

---

### T-CA-2 Appeals: NCLT → NCLAT (s.421) and NCLAT → Supreme Court (s.423)

> **Routing guard:** s.421 governs appeals from NCLT orders made under the **Companies Act**. Appeals from NCLT orders under the IBC go under IBC s.61 (30 + 15 days, running from pronouncement; see the IBC rules file). The SC in *V. Nagarajan* (2022) 2 SCC 244 expressly contrasted the two: "Sections 61(1) and (2) IBC consciously omit the requirement of limitation being computed from when the 'order is made available to the aggrieved party' in contradistinction to Section 421(3) of the Companies Act" (¶33, as quoted in [C-R22]). The engine must classify the impugned order by statute first.

#### 2.1 RuleSpec CA.S421_3.NCLAT_APPEAL
- **Trigger event:** "the date on which a copy of the order of the Tribunal is made available to the person aggrieved". The **appellant** must prove it, through the certified-copy endorsement, the NCLT dispatch record or the date of counsel's receipt.
- **Computation:** 45 calendar days, excluding day 0 (GCA s.9). Then a further window of ≤45 days that runs from the expiry of the first 45 (per *Sagufa Ahmed*). Limitation Act s.4 roll-forward for the base period only, flagged (see §1). Limitation Act s.12 is irrelevant because the trigger is already the copy. Limitation Act s.15(2) exclusion is not available (*RD v Gentle Realtors*, NCLAT 19.03.2026 [C-R21]).
- **Nature:** CONDONABLE (cap 45). Nothing can be condoned beyond 45 + 45.
- **Anchor (VERIFIED-PRIMARY):** s.421(3): "Every appeal under sub-section (1) shall be filed within a period of forty-five days from the date on which a copy of the order of the Tribunal is made available to the person aggrieved … Provided that the Appellate Tribunal may entertain an appeal after the expiry of the said period of forty-five days from the date aforesaid, but within a further period not exceeding forty-five days, if it is satisfied that the appellant was prevented by sufficient cause from filing the appeal within that period." [C-R1][C-R2]. s.421(2): "No appeal shall lie … from an order made by the Tribunal with the consent of parties." s.420(3): "The Tribunal shall send a copy of every order passed under this section to all the parties concerned." NCLT Rule 50: "The Registry shall send a certified copy of final order passed to the parties concerned free of cost" [C-R10][C-R20].
- **Case law:**
  - *Sagufa Ahmed v Upper Assam Plywood Products*, SC CA 3007-3008/2020, 18.09.2020 [C-R20] `verified`. The 45 days "would start running only from the date on which a copy of the order of the Tribunal is made available". A party who awaits the free copy under s.420(3) and Rule 50 is "perfectly justified" in relying on s.421(3). Once a copy is actually received, "the period of limitation cannot be stopped from running".
  - *Bengal Chemists & Druggists Assn v Kalyan Chowdhury*, (2018) 3 SCC 41: the second 45-day limit is "peremptory", and s.433 / Limitation Act s.5 cannot extend it (as quoted in NCLAT *RD v Gentle Realtors*, 19.03.2026) [C-R21] `verified` (secondary).
  - *SBI v India Power Corporation*, CA 10424/2024 (IBC context): a free copy and a paid copy are both "certified copies", and a party who never applies cannot fall back on awaiting the free copy [C-R22] `verified` (secondary). Flag as persuasive for s.421 diligence.
- **NCLAT procedure (VERIFIED-SECONDARY [C-R12]):** Rule 22(1): Form NCLAT-1. Rule 22(2): "Every appeal shall be accompanied by a certified copy of the impugned order". Rule 31: an IA for "condonation of delay" or "exemption from production of copy" goes in Form NCLAT-2. Form NCLAT-1 ¶6 requires the appellant to "Explain how the appeal is within the period prescribed … In case the appeal barred by limitation, the number of days of delay should be given along with interlocutory application for condonation of delay."
- **Status:** VERIFIED-PRIMARY (text) / VERIFIED-SECONDARY (interpretation).
- **Golden vectors:**
  1. Copy received 2019-12-19 → base expiry **2020-02-02**; condonable window ends **2020-03-18**. This is the SC's own arithmetic in *Sagufa Ahmed* ¶¶16–17. Note that 02.02.2020 was a Sunday and the SC still ran the further window from that date.
  2. Copy made available 2026-03-03 (Tue) → base expiry **2026-04-17 (Fri)**; condonable window ends **2026-06-01 (Mon)**.
- **Notes:** whether an order uploaded on the NCLT website counts as "made available" is **TO VERIFY WITH PARTNER**. Conservative mode should also show pronouncement-date + 45 and pronouncement-date + 90 as "safe-harbour" dates, clearly labelled as non-statutory.

#### 2.2 RuleSpec CA.S423.SC_APPEAL
- **Trigger event:** "the date of receipt of the order of the Appellate Tribunal to him". The **appellant** must prove receipt.
- **Computation:** 60 calendar days, excluding day 0, plus a further window of ≤60 days on sufficient cause. Appeal lies only "on any question of law arising out of such order".
- **Nature:** CONDONABLE (cap 60).
- **Anchor (VERIFIED-PRIMARY):** s.423: "Any person aggrieved by any order of the Appellate Tribunal may file an appeal to the Supreme Court within sixty days from the date of receipt of the order of the Appellate Tribunal to him on any question of law arising out of such order: Provided that the Supreme Court may, if it is satisfied that the appellant was prevented by sufficient cause from filing the appeal within the said period, allow it to be filed within a further period not exceeding sixty days." [C-R1][C-R2].
- **Case law:** I found no s.423-specific ruling on condonation beyond 120 days or on what counts as "receipt". *Bengal Chemists*' reasoning on s.421(3) is the closest parallel. **TO VERIFY WITH PARTNER.**
- **Golden vectors:**
  1. Order received 2026-01-12 → base **2026-03-13 (Fri)**; outer **2026-05-12 (Tue)**.
  2. Order received 2026-06-08 → base **2026-08-07 (Fri)**; outer **2026-10-06 (Tue)**.

#### 2.3 Draft output — appeal strategy memo and grounds skeleton
- **Memo:** (i) Is an appeal maintainable? Not if the order was made by consent (s.421(2)). For s.423, is there a question of law? (ii) Limitation computation card: trigger evidence, base and outer dates, s.4 flag, delay days, and a condonation IA if needed. (iii) Errors to plead: jurisdiction, misreading of s.244 or s.241 tests, limitation treated as a pure question of law (Chalasani), reliefs beyond pleadings (TCS v Cyrus), natural justice under Rule 37. (iv) Stay or interim prayer. (v) Adverse authorities: Bengal Chemists (no condonation beyond the cap); Sagufa (time runs from actual receipt even if the party applied late).
- **Grounds skeleton:** `Form NCLAT-1: parties | order impugned & date | date copy made available (evidence) | limitation para (¶6) | facts (chronological) | questions of law | grounds (A, B, C… each anchor-pinned) | interim relief | reliefs | IA (NCLAT-2): condonation / exemption from certified copy`.

---

### T-CA-3 ROC / adjudicating-officer penalty notices (s.454; CAP Rules 2014; s.454A)

#### 3.1 Statutory frame
- **s.454(1)** (current): the Central Government appoints AOs "not below the rank of Registrar". s.454(3): the AO "may, by an order impose the penalty". s.454(4): reasonable opportunity of being heard. The as-enacted text is in [C-R1]. Sub-ss.(3)/(4) were amended in 2019 to add "any other person" and a rectification direction (`snippet`; confirm on India Code).
- **s.454(5)** (current): appeal "to the Regional Director having jurisdiction in the matter". **s.454(7)**: the RD may confirm, modify or set aside after hearing [C-R3].
- **Rule 3A** (inserted by Companies (Adjudication of Penalties) Amendment Rules 2024, G.S.R. 476(E) of 05.08.2024, in force 16.09.2024): all AO and RD proceedings, "including issue of notices, filing replies or documents, evidences, holding of hearing … passing of orders and payment of penalty", take place **only on the MCA e-adjudication platform**. Where there is no e-mail, notice goes by post, with a copy kept on the platform. The Second Amendment Rules 2024 (G.S.R. 630(E), 09.10.2024) keep pending proceedings under the old rules [C-R14][C-R15][C-R16] `snippet` (summaries only; the Gazette text was not reachable). Platform URL: TO VERIFY.

#### 3.2 RuleSpec CAP.R3_2.SCN_REPLY (+ CAP.R3_4.REPLY_EXTENSION)
- **Trigger event:** date of service of the show-cause notice. The service mode is s.20 plus the KYC e-mail (Explanation 1); after 16.09.2024 it is the platform timestamp. The **AO** must prove service. The **noticee** should capture the platform or e-mail timestamp.
- **Computation:** the period specified in the notice, which must be "not being less than fifteen days and more than thirty days from the date of service". Excluding day 0. The engine takes the notice's stated date. It validates that the period is within 15–30 days and flags a short notice as a ground for extension. Extension: "a further period not exceeding fifteen days" at the AO's discretion "for reasons to be recorded in writing", if sufficient cause is shown or the person "received a shorter notice".
- **Nature:** ORDER-SET within a statutory band. Extension is CONDONABLE (cap 15, discretionary).
- **Anchor (VERIFIED-SECONDARY; Rule 3 as substituted by G.S.R. 131(E), 19.02.2019, read on IK [C-R13]; same wording in [C-R14]):**
  - Rule 3(2): "…to show cause, within such period as may be specified in the notice (not being less than fifteen days and more than thirty days from the date of service thereon), why the penalty should not be imposed on it or him."
  - Rule 3(3): the notice must "clearly indicate the nature of non-compliance or default … draw attention to the relevant penal provisions of the Act and the maximum penalty which can be imposed".
  - Rule 3(4): "The reply to such notice shall be filed in electronic mode only within the period as specified in the notice: Provided that the adjudicating officer may … extend the period … by a further period not exceeding fifteen days…".
- **Hearing:** Rule 3(5): if physical appearance is needed, the AO issues notice "within a period of ten working days from the date of receipt of reply". Under the proviso, the noticee gets an oral hearing if it **indicates this in its reply**, which is a drafting checkbox. Rule 3(11): failure to reply or appear allows an ex parte penalty order.
- **AO's order timeline (CAP.R3_7.AO_ORDER):** within 30 days of expiry of the reply period (no appearance) or 90 days of the notice (appearance). The proviso says "no such order shall be invalid merely because of its passing after the expiry of such thirty days or ninety days". This is **DIRECTORY** on the rule's own terms [C-R13].
- **Status:** VERIFIED-SECONDARY. Confirm that the 2024 amendments left Rule 3(2)–(7) unchanged: **TO VERIFY WITH PARTNER**. My `snippet` sources report only Rule 3A and Form ADJ changes.
- **Golden vectors:**
  1. Served 2026-03-02, notice specifies 30 days → reply due **2026-04-01 (Wed)**.
  2. Served 2026-07-06, notice specifies 15 days → due **2026-07-21 (Tue)**. Maximum extended date if the AO grants the full 15 days: **2026-08-05 (Wed)**.

#### 3.3 RuleSpec CA.S454_6.RD_APPEAL (with CAP Rule 4)
- **Trigger event:** the date the copy of the AO's order "is received by the aggrieved person" (platform or e-mail receipt). The **appellant** must prove it.
- **Computation:** 60 calendar days, excluding day 0. GCA s.10 roll-forward is advisory only (see §1).
- **Nature:** **HARD.** Neither s.454 nor Rule 4 contains a condonation proviso, unlike LLP s.76A(6) (§4.3). The Limitation Act s.5 does not reach the RD, because s.433 covers only NCLT/NCLAT. **TO VERIFY WITH PARTNER** whether RDs entertain late appeals in practice and whether writ relief is the only route.
- **Anchor:**
  - s.454(6) (VERIFIED-PRIMARY as enacted [C-R1]; the Bill [C-R3] does not amend (6)): "Every appeal under sub-section (5) shall be filed within sixty days from the date on which the copy of the order made by the adjudicating officer is received by the aggrieved person and shall be in such form, manner and be accompanied by such fees as may be prescribed."
  - CAP Rule 4(1) (VERIFIED-SECONDARY [C-R13]): "Every appeal against the order of the adjudicating officer shall be filed in writing with the Regional Director having jurisdiction in the matter within a period of sixty days from the date of receipt of the order of adjudicating officer by the aggrieved party, in **Form ADJ** setting forth the grounds of appeal and shall be accompanied by a certified copy of the order…". Second proviso: one appeal may not seek relief against more than one order unless the reliefs are consequential. Rule 4(2): fee per the Companies (Registration Offices and Fees) Rules 2014. Form ADJ was revised by the 2024 amendment (`snippet` [C-R15]).
- **Golden vectors:**
  1. AO order received 2026-01-19 → appeal due **2026-03-20 (Fri)**.
  2. AO order received 2026-09-14 → due **2026-11-13 (Fri)**.

#### 3.4 RuleSpec CA.S454_8.COMPLY_90D
- **Anchor (VERIFIED-PRIMARY, current text via Bill annexure [C-R3]):** s.454(8)(i): "Where company fails to comply with the order made under sub-section (3) or sub-section (7), as the case may be, within a period of ninety days from the date of the receipt of the copy of the order, the company shall be punishable with fine which shall not be less than twenty-five thousand rupees but which may extend to five lakh rupees." Clause (ii) covers the officer in default or any other person: imprisonment up to 6 months, or fine of ₹25,000–₹1 lakh, or both.
- **Trigger:** receipt of a copy of the AO order (s.454(3)) or the RD order (s.454(7)). **Computation:** 90 days, excluding day 0. **Nature:** HARD (criminal exposure). Filing an appeal does not, by the text, suspend the 90 days, so the engine shows both clocks.
- **Golden vectors:**
  1. Order received 2026-09-01 → comply by **2026-11-30 (Mon)**.
  2. Received 2026-02-10 → **2026-05-11 (Mon)**.

#### 3.5 RuleSpec CA.S454A.REPEAT_3Y (look-back, not a deadline)
- **Anchor (VERIFIED-PRIMARY, current text via [C-R3]):** "Where a company or an officer of a company or any other person having already been subjected to penalty for default under any provisions of this Act, again commits such default within a period of three years from the date of order imposing such penalty passed by the adjudicating officer or the Regional Director, as the case may be, it or he shall be liable for the second or subsequent defaults for an amount equal to twice the amount of penalty provided for such default".
- **Engine use:** risk flag on a new SCN. Look up prior penalty orders for the same default in the last 3 years and show 2× exposure.
- **Vectors:** penalty order 2026-08-03. Same default committed 2029-07-15 → **2× applies**. Committed 2029-09-01 → **does not apply**. Exact-anniversary boundary cases: TO VERIFY.

#### 3.6 Draft output — SCN reply skeleton / grid; RD appeal skeleton
- **Strategy memo:** (i) what the default is (section, period, company or officer, and whether a fixed-sum or per-day penalty under Rule 3(13)); (ii) exposure calculator (penalty provision, per-day cap, s.446B halving for OPC, small, start-up and producer companies [C-R3], s.454A doubling); (iii) defences: no default, defect in the notice under Rule 3(3), default made good before the notice (additional fee paid under s.403), AO without jurisdiction (appointment notification and territory), wrong person named as "officer in default"; (iv) mitigation under the Rule 3(12) factors; (v) compound or adjudicate (s.441 is not available for penalty-only provisions after decriminalisation, so confirm the provision type); (vi) deadlines: reply date, ≤15-day extension request, appeal 60 days, compliance 90 days.
- **SCN reply skeleton:** `Ref: SCN no./date/AO/section; date of service (platform timestamp) | 1. Preliminary: jurisdiction; Rule 3(3) deficiencies; service | 2. Facts & compliance chronology (with SRN/challans) | 3. No default / rectified (s.454(3) rectification direction sought instead of penalty) | 4. Quantum: Rule 3(12) factors; s.446B; fixed-sum provisions | 5. Request for personal hearing (Rule 3(5) proviso) | 6. Prayer: drop proceedings / minimum penalty | Annexures`.
- **Grid columns:** `SCN ¶ | Alleged default | Section & penalty provision | Period of default | Exposure (company / each officer; per-day; cap) | Our position | Evidence (MCA SRN, board minutes) | s.446B applicable? | s.454A prior order? | Risk`.
- **RD appeal (Form ADJ) skeleton:** `AO order details & receipt date | certified copy | authorisation & consent of representative (Rule 4(1) proviso) | grounds (jurisdiction; natural justice under Rule 3(5)/(11); misapplication of penalty provision; quantum) | relief | fee`.

---

### T-CA-4 Compounding (s.441) and LLP parallels (ss.39, 76A)

#### 4.1 RuleSpec CA.S441.TIMING (eligibility, no limitation)
- **Anchor (current s.441(1) via Bill annexure [C-R3]; rest as enacted [C-R1]):** "any offence punishable under this Act … **not being an offence punishable with imprisonment only, or punishable with imprisonment and also with fine**, may, either before or after the institution of any prosecution, be compounded by— (a) the Tribunal; or (b) where the maximum amount of fine which may be imposed for such offence does not exceed **twenty-five lakh rupees**, by the Regional Director or any officer authorised by the Central Government". The sum specified may not exceed the maximum fine. Third proviso: no compounding "if the investigation against such company has been initiated or is pending under this Act". s.441(2): no compounding of an offence committed "within a period of three years from the date on which a similar offence committed by it or him was compounded". s.441(3)(a): "Every application for the compounding of an offence shall be made to the Registrar who shall forward the same, together with his comments thereon" to the NCLT or RD. s.441(6)(b) (as enacted): offences punishable "with imprisonment only or with imprisonment and also with fine shall not be compoundable". s.441(7): compounding only under this section.
- **Who compounds:** maximum fine ≤ ₹25 lakh → RD (or authorised officer); above that → NCLT. NCLT Rule 88: the ROC's reference to the Tribunal under s.441 goes in Form NCLT-9 [C-R10]. The applicant files with the ROC in e-form GNL-1 (`snippet` [C-R36]; TO VERIFY current MCA V3 form).
- **Timing:** **no limitation period** in s.441. The bars are (i) a pending or initiated investigation and (ii) the 3-year repeat window. Compounding before prosecution bars prosecution under s.441(3)(c). Compounding after prosecution leads to discharge under s.441(3)(d).
- **Nature:** eligibility bars (no deadline). **Status:** VERIFIED-PRIMARY. The interaction between amended s.441(1) and as-enacted s.441(6)(a) ("with the permission of the Special Court") is **TO VERIFY WITH PARTNER**.
- **Watchlist:** Bill cl.97 would raise the RD limit from ₹25 lakh to **₹1 crore** [C-R3].

#### 4.2 RuleSpec CA.S441_3B.INTIMATION_7D
- **Anchor (VERIFIED-PRIMARY as enacted [C-R1]):** s.441(3)(b): "Where any offence is compounded under this section … an intimation thereof shall be given by the company to the Registrar within seven days from the date on which the offence is so compounded." s.441(4): the compounding authority may direct filing of returns "within such time as may be specified in the order" (ORDER-SET). s.441(5): non-compliance is punishable.
- **Nature:** HARD. **Golden vectors:**
  1. Compounded 2026-10-05 → intimate by **2026-10-12**.
  2. Compounded 2026-04-28 → **2026-05-05**.

#### 4.3 LLP parallels (brief; VERIFIED-SECONDARY, IK text as amended by LLP (Amendment) Act 2021 [C-R17])
- **LLP s.39 compounding:** the RD (or an officer not below RD rank) may compound "any offence under this Act which is punishable with fine only". There is a 3-year repeat bar (s.39(2)). The application goes to the Registrar (s.39(3)), with intimation to the Registrar "within a period of seven days" (s.39(4)).
- **LLP s.76A adjudication:**
  - AOs not below Registrar rank.
  - Proviso to (3)(a): no penalty if a default under s.34(3) or s.35(1) is rectified "either prior to or within thirty days of the issue of the notice".
  - Small or start-up LLPs pay half the penalty, capped at ₹1 lakh (LLP) / ₹50,000 (partner).
  - **s.76A(6):** appeal to the RD "within a period of sixty days from the date on which the copy of the order … is received … Provided that the Regional Director may, for the reasons to be recorded in writing, extend the period of filing an appeal … by not more than thirty days."
  - s.76A(8)/(9): 90 days to comply, or fine/prosecution.
- **RuleSpec LLP.S76A_6.RD_APPEAL:** CONDONABLE (cap 30). Vectors:
  1. Received 2026-05-14 → base **2026-07-13 (Mon)**, outer **2026-08-12 (Wed)**.
  2. Received 2026-09-10 → base **2026-11-09 (Mon)**, outer **2026-12-09 (Wed)**.
- **RuleSpec LLP.S76A_8_9.COMPLY_90D:** HARD; same arithmetic as CA.S454_8. LLP adjudication rules and forms: TO VERIFY. Watchlist: Bill cl.16 adds s.76A(1A) (suo motu application for adjudication) and s.76A(10) (transfer of pending prosecutions) [C-R3].

#### 4.4 Draft output — compounding memo and application skeleton
- **Memo:** offence classification (fine-only / fine-or-imprisonment / imprisonment-only, i.e. compoundable or not); forum (RD if max fine ≤ ₹25 lakh, else NCLT); bars (investigation; 3-year repeat; offence already converted to a penalty, in which case route to adjudication instead); the default made good or not, and rectification filings with additional fees under s.403; exposure versus compounding fee; post-order deadlines (7-day intimation; s.441(4) filing directions).
- **Application skeleton:** `Applicant(s) & DIN/PAN | offence, section, punishment | period of default & facts | rectification done (SRN) | prior compounding in last 3 yrs (none/details) | no investigation initiated/pending (declaration) | prosecution status | board resolution & affidavit | prayer (compound at minimum) | ROC comments (s.441(3)(a))`.

---

### T-CA-5 Other Companies Act triggers — "general mode" (no deadline guarantee)

| Trigger | Anchors verified | What the engine may show | Status |
|---|---|---|---|
| Scheme (ss.230–232): objection by shareholder/creditor | s.230(4) proviso: objection "only by persons holding not less than ten per cent. of the shareholding or having outstanding debt amounting to not less than five per cent. of the total outstanding debt"; voting/postal ballot "within one month from the date of receipt of such notice" [C-R1] | Standing check + 1-month voting window (informational) | VERIFIED-PRIMARY (as enacted); CAA Rules 2016 timelines TO VERIFY |
| Scheme: regulator representations | s.230(5): representations "within a period of thirty days from the date of receipt of such notice, failing which, it shall be presumed that they have no representations to make" [C-R1] | Regulator-response window (when acting for an authority or tracking objections) | VERIFIED-PRIMARY (as enacted) |
| Fast-track merger s.233 | s.233(1)(a): objections from ROC, OL and affected persons "within thirty days" [C-R1] | Objection window | VERIFIED-PRIMARY (as enacted); Bill cl.69 changes approval thresholds |
| Winding up s.271 | Current s.271 (post-IBC; via [C-R3]): special resolution; acts against sovereignty etc.; fraud on application of ROC; 5-year filing default; just and equitable | No deadline; route insolvency-type matters to IBC | General mode |
| Director disqualification s.164(2) / vacation s.167(1)(a) | s.164(2) (current via [C-R3]): no reappointment "for a period of five years from the date on which the said company fails to do so"; 6-month grace for a newly appointed director. s.167(1)(a) proviso: vacation in all companies other than the defaulting one [C-R3] | 5-year disqualification window calculator (informational) | VERIFIED-PRIMARY (current text); challenges (writ/HC) general mode |
| s.59 rectification | Limitation: Art.137, 3 years (*Niklesh*) [C-R25] | Screening only | VERIFIED-SECONDARY |

---

### T-CA-6 Watchlist — Corporate Laws (Amendment) Bill 2026 (BILL, **not law**)

**Watchlist record (fields the product needs):**
```yaml
watch_id: WATCH.CLAB2026
instrument_type: BILL            # never render as law; never feed RuleSpecs
title: The Corporate Laws (Amendment) Bill, 2026
bill_no: "85 of 2026"            # VERIFIED-PRIMARY: cover page "AS INTRODUCED IN LOK SABHA / Bill No. 85 of 2026" [C-R3]
amends: [Companies Act 2013, LLP Act 2008]
ministry: Corporate Affairs
member_in_charge: Smt. Nirmala Sitharaman, Minister of Finance and Corporate Affairs   # [C-R3] back page
house_of_origin: Lok Sabha
introduced_on: 2026-03-23        # [C-R4][C-R5][C-R7]
committee:
  type: Joint Parliamentary Committee
  name: Joint Committee on the Corporate Laws (Amendment) Bill, 2026
  referred_on: 2026-03-23        # PRS bill track "In Committee … Mar 23, 2026" [C-R4]
  chair: Sudhir (Sudheer) Gupta  # [C-R6]
  members: 31                    # snippet (news/blog) [C-R8]
  report_due: null               # TO VERIFY (LS motion text not retrieved); moot — report presented
  report_presented_on: 2026-08-03   # [C-R4][C-R6]
stage: REPORTED_BY_COMMITTEE_PENDING_CONSIDERATION_IN_LS   # as of 2026-10-01 PRS shows no passage event
passed_ls: null
passed_rs: null
assent: null
act_no: null
commencement_clause: "on such date as the Central Government may, by notification … appoint; and different dates may be appointed for different provisions"   # cl.1(2) [C-R3]
sources: [PRS bill track, PRS bill summary, PRS JPC summary, bill text PDF; Lok Sabha/Sansad page TO ADD]
last_checked: 2026-10-01
```
**Headline changes and our RuleSpecs they would touch (if enacted and notified):**
- **Compounding:** RD/authorised-officer limit under s.441(1)(b) rises from ₹25 lakh to **₹1 crore** (cl.97). This affects CA.S441.TIMING forum routing. s.447 fraud thresholds rise: ₹10 lakh → ₹25 lakh and ₹50 lakh → ₹1 crore (cl.99).
- **Adjudication:**
  - s.454(1): AO rank lowered to **Assistant Registrar**.
  - New s.454(1A): **suo motu application for adjudication**.
  - s.454(5): an **Appellate Authority** (≥ Joint Director) may be notified in addition to the RD.
  - s.454(8): the court may also order the penalty paid.
  - New (9) and (10): a transfer scheme for pending prosecutions.
  - New **s.454B** (Recovery Officer), **s.454C** (settlement before a "Specified Authority") and **s.454D** (no appeal against an NFRA, Valuation Authority or AO order "unless the person has deposited ten per cent. of that penalty amount").
  - These affect CA.S454_6, CA.S454_8 and CA.S454A (cl.101–103) [C-R3].
  - **The 60-day period in s.454(6) is not amended.**
- **Oppression:** s.242(8) offence omitted, with contempt under s.425 instead (cl.71). ss.241, 244, 421, 423 and 433 are **not** amended (grep of the Bill text).
- **Schemes:** every s.230–233 application to go to the NCLT bench having jurisdiction over the **transferee** company (new proviso to s.230(1)). Fast-track (s.233) member approval drops from 90% of shares to 75% of shares among those present and voting; creditors 9/10 → 75% (cl.67, 69). New s.233A covers treasury shares.
- **Directors:** a new "fit and proper" disqualification under s.164, which the JPC recommended deleting. s.167 amendments (cl.54, 57) [C-R3][C-R6].
- **NCLT:** s.419(4A) special benches. The JPC recommends **mandatory dedicated IBC benches** [C-R6].
- **Other:** CSR net-profit trigger ₹5 crore → ₹10 crore; small-company caps ₹20 crore capital / ₹200 crore turnover; AGM by VC with a physical meeting at least once in 3 years; **IBBI as Valuation Authority** (s.247); wider NFRA powers; trust → LLP conversion; LLP s.76A(1A) [C-R5].
- **JPC (3 Aug 2026) key recommendations:**
  - remove the government's power to revise the CSR threshold;
  - limit the auditor exemption to private companies;
  - delete the "fit and proper" amendment;
  - keep NFRA investigation procedure in Central Government rules;
  - drop imprisonment for NFRA non-compliance;
  - add an exit right for dissenting shareholders in fast-track mergers;
  - MD/WTD age band 18–75 [C-R6].
- **Product rule:** alerts and digests may report Bill events. RuleSpecs stay on current law until (a) assent, (b) Gazette publication and (c) a commencement notification for the specific clause. The Bill has a staggered-commencement clause, so this must be checked clause by clause.

---

### General-mode notes
In general mode the engine answers with anchored law but **no deadline guarantee**. Every date it shows carries one of these labels: ORDER-SET (read from the order or notice), DIRECTORY (target only), PRACTICE (customary range; never a default), or "screening" (limitation risk). Concretely:
1. s.241 petitions have **no filing deadline**. Limitation is a 3-year screen with unsettled article choice and a contested accrual date.
2. NCLT reply and rejoinder dates come only from the bench's order (Rule 37(3) says only "before the date of hearing").
3. s.422 three-month disposal and CAP Rule 3(7) order timelines are DIRECTORY.
4. AO/RD steps sit outside the Limitation Act. GCA s.10 roll-forward is advisory until the partner confirms how it applies to the e-adjudication platform.
5. Statute routing matters. An NCLT order under the IBC uses IBC s.61, not CA s.421(3). A competition order goes to the NCLAT under Competition Act s.53B (not covered here).
6. No RD-appeal condonation exists under the Companies Act. LLP s.76A(6) does allow up to 30 days. The UI must not reuse the LLP rule for companies.
7. Watchlist Bills never alter RuleSpecs.
8. Prosecution-side limitation (CrPC s.468 / BNSS equivalent) for CA offences is out of scope and **TO VERIFY**.

### TO VERIFY WITH PARTNER (consolidated)
1. Which limitation article (113 or 137) the partner's NCLT bench applies to s.241, and the bench's stance on continuing wrong. Whether s.5 is pleaded where Art.137 applies.
2. Typical reply and rejoinder windows at the partner's bench (for the UI hint only).
3. Whether a website upload counts as "made available" under s.421(3). Conservative safe-harbour display.
4. s.4 roll-forward on condonation windows (s.421(3) and s.423 provisos), and GCA s.10 on the e-adjudication platform.
5. RD practice on late appeals under s.454(6); writ as the remedy.
6. CAP Rules: exact 2024 Gazette text (Rule 3A; Form ADJ); confirm Rule 3(2)–(7) is unchanged; platform URL.
7. s.441(6)(a) "permission of the Special Court" after the 2020 amendment; current e-form for compounding (GNL-1 on MCA V3?).
8. s.423-specific SC ruling on receipt date and outer cap.
9. Unverified case citations listed in §1.5 and [C-R32][C-R33].

### Deltas / contradictions versus the brief
- **The Bill has moved past "referred to JPC".** The JPC **presented its report on 3 Aug 2026** [C-R4][C-R6]. As of 1 Oct 2026 PRS shows no passage in either House. Stage should read "reported by committee; pending in LS". Bill number confirmed as **85 of 2026**.
- **The brief's "(100 members / one-tenth)" is incomplete.** s.244 is "100 members **or** one-tenth of members, whichever is less, **or** members holding one-tenth of issued capital", plus calls paid. Non-share companies need one-fifth of members. Joint holders count once.
- **The brief's "time for reply/objections and rejoinder" has no rule.** The NCLT Rules fix no days. Rule 37(3) says only "before the date of hearing". Everything else is ORDER-SET.
- **The brief's "appeal to RD under s.454(5)/(6)".** Confirmed: 60 days, Form ADJ (Rule 4). Unlike LLP s.76A(6), it has **no** condonation window. Treat as HARD.
- **The brief's "Limitation Act applies (s.433)".** Yes, but only to NCLT/NCLAT "as far as may be". It cannot extend capped provisos (*Bengal Chemists*). The NCLAT is divided between Art.113 and Art.137 for s.241, though both give 3 years.
- s.421(3) (45 + 45) and s.423 (60 + 60) are confirmed verbatim. *TCS v Cyrus* is (2021) 9 SCC 449.

---

### References
- [C-R1] Companies Act, 2013 as enacted, Gazette of India copy hosted by NCLT — https://nclt.gov.in/sites/default/files/Act%26rules/the_companies_act_2013_0.pdf — `verified` (read ss.241, 242(4), 244, 420–423, 433, 441, 454 as enacted).
- [C-R2] Companies Act, 2013, Indian Kanoon (as-enacted version) — https://indiankanoon.org/doc/172276913/ ; s.421 https://indiankanoon.org/doc/30641282/ ; s.441 https://indiankanoon.org/doc/32266889/ ; s.454 https://indiankanoon.org/doc/144254605/ — `verified`.
- [C-R3] The Corporate Laws (Amendment) Bill, 2026, Bill No. 85 of 2026, as introduced in Lok Sabha (with Notes on Clauses and Annexure "Extracts from the Companies Act, 2013" / LLP Act) — https://prsindia.org/files/bills_acts/bills_parliament/2026/Corporate_Laws_(A)_Bill_2026_Text.pdf — `verified`.
- [C-R4] PRS Bill Track, The Corporate Laws (Amendment) Bill, 2026 — https://prsindia.org/billtrack/the-corporate-laws-amendment-bill-2026 — `verified` (Introduced LS 23.03.2026; In Committee JPC 23.03.2026; Report JPC 03.08.2026).
- [C-R5] PRS Bill Summary (27.03.2026) — https://prsindia.org/files/bills_acts/bills_parliament/2026/Summary_Corporate_Laws_2026.pdf — `verified`.
- [C-R6] PRS JPC Report Summary (31.08.2026) — https://prsindia.org/files/bills_acts/bills_parliament/2026/JPC_Report_Summary_Corporate_Laws_(A)_Bill_2026.pdf — `verified`.
- [C-R7] Morung Express, "Lok Sabha gives nod for referring Corporate Laws (Amendment) Bill to JPC" — https://morungexpress.com/lok-sabha-gives-nod-for-referring-corporate-laws-amendment-bill-to-jpc — `verified` (news).
- [C-R8] Ratra blog (31-member JPC; status) — https://www.ratra.in/corporate-laws-amendment-bill-2026/ ; CAalley — https://www.caalley.com/news-updates/indian-news/corporate-laws-amendment-bill-2026-introduced-in-lok-sabha-sent-to-jpc — `snippet` for the 31-member figure.
- [C-R9] NCLT Rules, 2016, Gazette G.S.R. 716(E) dated 21.07.2016 (nclt.gov.in) — https://nclt.gov.in/sites/default/files/Act%26rules/NCLT%20Rules%202016%20dated%2021%2007%202016.pdf — `verified` (Rule 37).
- [C-R10] NCLT Rules, 2016 consolidated to 07.02.2020, Indian Kanoon — https://indiankanoon.org/doc/8775712/ — `verified` (Rules 34, 35, 37, 38, 38A, 50, 51, 81, 82, 83A, 88).
- [C-R11] NCLT "Acts / Rules" page listing procedure-rule amendments (2016, 2017, 2019, 2nd 2019, 2020) — https://nclt.gov.in/index.php/act-rule — `verified`.
- [C-R12] NCLAT Rules, 2016, Indian Kanoon — https://indiankanoon.org/doc/6870327/ — `verified` (Rules 22, 31; Form NCLAT-1 ¶6).
- [C-R13] Companies (Adjudication of Penalties) Rules, 2014 as amended to 23.02.2019, Indian Kanoon — https://indiankanoon.org/doc/161928924/ — `verified` (Rules 3, 4).
- [C-R14] IBClaw consolidated Adjudication Rules (incl. 2024 amendments) — https://ibclaw.in/the-companies-adjudication-of-penalties-rules-2014/ — `snippet` (WebFetch summary).
- [C-R15] SCC Online blog, MCA notifies Companies (Adjudication of Penalties) Amendment Rules 2024 (05.08.2024; w.e.f. 16.09.2024) — https://www.scconline.com/blog/post/2024/08/07/mca-notifies-companies-adjudication-of-penalties-amendment-rules-2024-legal-news/ — `snippet`.
- [C-R16] CAclubindia, Second Amendment Rules 2024, G.S.R. 630(E), 09.10.2024 — https://www.caclubindia.com/news/-mca-notifies-companies-adjudication-of-penalties-second-amendment-rules-2024-23986.asp — `snippet`.
- [C-R17] LLP Act, 2008 as amended by Act 31 of 2021, Indian Kanoon — https://indiankanoon.org/doc/161391573/ — `verified` (ss.39, 76A).
- [C-R18] General Clauses Act, 1897, Indian Kanoon — https://indiankanoon.org/doc/905940/ — `verified` (ss.9, 10).
- [C-R19] Limitation Act, 1963, Indian Kanoon — https://indiankanoon.org/doc/1317393/ — `verified` (ss.4, 22, 29(2); Arts.113, 137).
- [C-R20] *Sagufa Ahmed v Upper Assam Plywood Products Pvt Ltd*, SC, CA 3007-3008/2020, 18.09.2020 (digitally signed judgment copy) — https://insolvencylawacademy.com/wp-content/uploads/2022/09/Sagufa-Ahmed-_-Ors.-V.-Upper-Assam-Plywood-Products-Pvt.-Ltd.-_-Ors.-2020.pdf — `verified`. SCC citation (2021) 2 SCC 317 — `unverified`.
- [C-R21] *Regional Director (NR) v Gentle Realtors Pvt Ltd*, NCLAT, Comp. App. (AT) 140/2025, 19.03.2026 (quoting *Bengal Chemists & Druggists Assn v Kalyan Chowdhury* (2018) 3 SCC 41) — https://indiankanoon.org/doc/153365155/ — `verified`; IndiaCorpLaw note — https://indiacorplaw.in/?p=6968 — `snippet`.
- [C-R22] Cyril Amarchand Mangaldas client alert (30.10.2024) quoting *V. Nagarajan v SKS Ispat* (2022) 2 SCC 244 ¶¶33–34 and summarising *SBI v India Power Corporation* CA 10424/2024 — https://cyrilshroff.com/wp-content/uploads/2024/10/Client-Alert-Supreme-Court-settles-the-law-on-Certified-copies-3010.pdf — `verified` (secondary).
- [C-R23] *Chalasani Udaya Shankar v Lexus Technologies Pvt Ltd*, 2024 INSC 671 (09.09.2024) — https://api.sci.gov.in/supremecourt/2023/24030/24030_2023_2_1501_55462_Judgement_09-Sep-2024.pdf — `verified`.
- [C-R24] *Shailja Krishna v Satori Global Ltd*, 2025 INSC 1065 (02.09.2025), Indian Kanoon — https://indiankanoon.org/doc/81816562/ — `verified` (also source for the TCS v Cyrus, Needle, Dale & Carrington, Sangramsinh, V.S. Krishnan and Kalinga Tubes citations).
- [C-R25] *Niklesh Tirathdas Nihalani v Shah Poddar Nihlani Organisers Pvt Ltd*, NCLAT CA(AT) 167/2020, 02.08.2021 — https://indiankanoon.org/doc/93618766/ — `verified`.
- [C-R26] *Shefali Agrawal v Stone Age Pvt Ltd*, NCLAT CA(AT) 225/2023, 14.05.2026 (quoting *Esquire Electronics*, *Vijay Kumar Agarwal v Juhu Hotel*, *Khatri Hotels*) — https://indiankanoon.org/doc/119090374/ — `verified`.
- [C-R27] *Neeraj Gupta v A-1 Equipments Pvt Ltd*, NCLAT CA(AT) 239/2020, 09.09.2022 — https://indiankanoon.org/doc/25697290/ — `verified`.
- [C-R28] SCC Online blog on *Cyrus Investments v Tata Sons* (NCLAT, waiver, 21.09.2017) — https://www.scconline.com/blog/post/2017/10/18/nclat-lays-factors-forming-opinion-whether-application-merits-waiver/ ; Vinod Kothari — https://vinodkothari.com/2021/12/grounds-for-grant-of-waiver-under-section-244-of-companies-act/ — `snippet`.
- [C-R29] TCS v Cyrus case notes — https://cbcl.nliu.ac.in/company-law/conclusion-of-a-corporate-saga-the-tata-mistry-dispute/ ; https://lawfullegal.in/tata-consultancy-services-ltd-v-cyrus-investment-pvt-ltd-2021/ — `snippet`.
- [C-R30] MCA e-adjudication platform notes — https://khaitanco.com/thought-leadership/MCAs-Introduction-of-E-Adjudication-Platform ; https://mondaq.com/india/corporate-and-company-law/1504284/mca-introduces-e-adjudication-platform — `snippet`.
- [C-R31] NCLT reply/rejoinder practice (search results incl. NCLT/NCLAT orders) — e.g. https://archive.nclt.gov.in/sites/default/files/old_interm-final_order/36_44.pdf — `snippet`.
- [C-R32] *Assam Urban Water Supply & Sewerage Board v Subash Projects & Marketing Ltd*, (2012) 2 SCC 624 — `unverified` (proposition from memory; citation corroborated only by search snippet).
- [C-R33] *Sakuru v Tanaji*, (1985) 3 SCC 590 — `unverified` (memory).
- [C-R34] *Kerala SEB v T.P. Kunhaliumma*, (1976) 4 SCC 634 — `verified` as quoted in [C-R25].
- [C-R35] *Khatri Hotels Pvt Ltd v Union of India* — `verified` as quoted in [C-R26]; SCC citation `unverified`.
- [C-R36] Compounding practice (GNL-1; RD ≤ ₹25 lakh) — https://taxguru.in/company-law/application-compounding-offence-companies-act-2013.html — `snippet`.
- [C-R37] Deccan Chronicle / Ommcom on JPC report — https://www.deccanchronicle.com/nation/parliamentary-panel-clears-corporate-laws-amendment-bill-boosts-ease-of-doing-business-1976205 ; https://ommcomnews.com/india-news/joint-parliamentary-panel-backs-corporate-laws-amendment-bill-2026/ — `snippet`.


---

# Part C — SEBI, SAT, Competition and FEMA

*Source pack title: Rules file: SEBI, competition and FEMA triggers (MVP)*

**Scope:** T-SEBI-1 (SEBI show-cause notice), T-SEBI-2 (appeal to SAT, then to the Supreme Court), T-COMP-1 (CCI investigation, appeal to NCLAT, then to the Supreme Court), T-FEMA-1 (FEMA contravention: adjudication, appeal and compounding). The file also gives the SEBI corpus and feed map.
**Law as at:** 1 October 2026. **Author role:** securities, competition and FEMA rules researcher.
**Evidence tags (per brief):** `verified` means the primary or reliable text was fetched and read, and the operative words quoted here were seen in that text. `snippet` means only a search-result summary was seen. `unverified` means neither. RuleSpec statuses: VERIFIED-PRIMARY, VERIFIED-SECONDARY and TO VERIFY WITH PARTNER (shortened to **TVP**).
**Access note:** indiacode.nic.in returned an Akamai error or HTTP 403 from this environment. Acts were therefore read from regulator-hosted consolidated texts: SEBI for the SEBI Act, SCRA and Depositories Act; CCI for the Competition Act; the Enforcement Directorate for FEMA. sat.gov.in returned HTTP 503, matching blueprint P0. rbidocs.rbi.org.in PDFs are behind a CAPTCHA, but the rbi.org.in HTML pages are readable.

---

### 0. Summary table

| rule_code | What the clock does | Period | Nature | Status |
|---|---|---|---|---|
| SEBI.PENRULES.R4.SCN_REPLY | Reply to an adjudication or penalty SCN | As stated in the notice, and at least 14 days from service | Floor on SEBI; the client's deadline is the date stated in the notice | VERIFIED-PRIMARY |
| SEBI.PENRULES.R5_5.RECTIFICATION | Point out an error apparent in an AO/WTM penalty order | 15 days from the **date of the order** | HARD (text gives no extension) | VERIFIED-PRIMARY |
| SEBI.S11.DIRECTIONS_SCN_REPLY | Reply to a SCN under ss.11/11B/11D that seeks directions only | Whatever the notice states (practice: about 21 days) | PRACTICE | TVP |
| SEBI.S11.INTERIM_ORDER_OBJECTIONS | Objections to an ex parte interim order under s.11(4) | Whatever the order states | PRACTICE | TVP |
| SEBI.INTERMED.R25_2.SCN_REPLY | Reply in an enquiry under the Intermediaries Regulations | As stated in the notice, and **at most** 21 days from service; extendable | DIRECTORY (extension power exists) | VERIFIED-PRIMARY |
| SEBI.INTERMED.R25_5.INSPECTION_REQUEST | Ask to inspect the documents relied on | Within the reply period | HARD for the request (no condonation stated) | VERIFIED-PRIMARY |
| SEBI.INTERMED.R27_2.DA_REPORT_REPLY | Reply to the designated authority's report | As stated, and at most 21 days; extendable | DIRECTORY | VERIFIED-PRIMARY |
| SEBI.SETTLE18.R4_1.APPLICATION | File a settlement application after a SCN | 60 days from service of the SCN or of the last supplementary SCN, whichever is later | **HARD**: condonation was deleted with effect from 14-01-2022 | VERIFIED-PRIMARY |
| SEBI.SETTLE18.R15_2a.REMIT | Pay the settlement amount | 30 calendar days from receipt of the notice of demand | HARD: the extension proviso was deleted with effect from 14-01-2022 | VERIFIED-PRIMARY |
| SEBI.SETTLE26.* (watchlist) | New Settlement Regulations, 2026 | 90 days after the SCN; 60 days after a settlement notice; a one-time 90-day window | **Approved 24-09-2026; not notified** | VERIFIED-PRIMARY (press release only) |
| SEBI.S15T_3.SAT_APPEAL | Appeal to SAT against a SEBI, AO, IRDAI or PFRDA order | 45 days from receipt of a copy of the order | CONDONABLE, **no cap** | VERIFIED-PRIMARY |
| SCRA.S23L_2.SAT_APPEAL | Appeal to SAT against an order under the SCRA (stock exchange, AO or SEBI) | 45 days from receipt of a copy | CONDONABLE, no cap | VERIFIED-PRIMARY |
| DEPACT.S23A_3.SAT_APPEAL | Appeal to SAT against an order under the Depositories Act | 45 days from receipt of a copy | CONDONABLE, no cap | VERIFIED-PRIMARY |
| SCRA.S22A.LISTING_REFUSAL_APPEAL | Appeal to SAT against an exchange's refusal to list | 15 days (plus up to 1 month on sufficient cause, at least under clause (b)) | CONDONABLE (cap 1 month) | VERIFIED-PRIMARY (scope of the cap is TVP) |
| SAT.PROC.R14.RESPONDENT_REPLY | Respondent's reply in SAT | 1 month from service of notice of the appeal | DIRECTORY (SAT may allow later) | VERIFIED-PRIMARY (text); month arithmetic TVP |
| SEBI.S15Z.SC_APPEAL (also SCRA s.22F, DA s.23F) | Appeal to the Supreme Court from SAT | 60 days from communication, plus at most 60 more | CONDONABLE (cap 60) | VERIFIED-PRIMARY |
| COMP.S53B_2.NCLAT_APPEAL | Appeal to NCLAT against a CCI order | 60 days from receipt of a copy, plus a 25% pre-deposit where an amount is payable | CONDONABLE, **no cap** | VERIFIED-PRIMARY |
| COMP.S53T.SC_APPEAL | Appeal to the Supreme Court from NCLAT (competition) | 60 days from communication | CONDONABLE, **no cap** (unlike SEBI s.15Z) | VERIFIED-PRIMARY |
| CCI.GEN24.R22_2.DG_REPORT_OBJECTIONS | Objections or suggestions on the DG report | 8 weeks from receipt of the report | Regulatory; extension practice TVP | VERIFIED-PRIMARY |
| CCI.GEN24.R36_7b.CONF_RING_REQUEST | Ask for a confidentiality ring after receiving the non-confidential DG report | 10 days, plus at most 7 on sufficient cause | CONDONABLE (cap 7) | VERIFIED-PRIMARY |
| CCI.GEN24.R36_9.CONF_RING_UNDERTAKING | File confidentiality-ring undertakings | 10 days, plus at most 5 | CONDONABLE (cap 5) | VERIFIED-PRIMARY |
| CCI.SETTLE24.R5_2.APPLICATION | CCI settlement application | 45 days from receipt of the DG report, plus at most 30 | CONDONABLE (cap 30) | VERIFIED-PRIMARY |
| CCI.COMMIT24.R3_3.APPLICATION | CCI commitment application | **60 days** (45 before 18-08-2026) from receipt of the s.26(1) order, plus at most 30, and before the DG report is received | CONDONABLE (cap 30) | VERIFIED-PRIMARY (transition TVP) |
| FEMA.ADJRULES.R4_1.SCN_REPLY | Reply to a FEMA adjudication SCN | As stated in the notice, and at least 10 days from service | Floor on the AA | VERIFIED-PRIMARY |
| FEMA.S17_3.SDA_APPEAL | Appeal to the Special Director (Appeals) | 45 days from receipt of a copy | CONDONABLE, no cap | VERIFIED-PRIMARY |
| FEMA.S19_2.AT_APPEAL | Appeal to the Appellate Tribunal (SAFEMA Tribunal) | 45 days from receipt of a copy, plus pre-deposit of the penalty (waivable) | CONDONABLE, no cap | VERIFIED-PRIMARY |
| FEMA.S35.HC_APPEAL | Appeal to the High Court on a question of law | 60 days from communication, plus at most 60 more | CONDONABLE (cap 60) | VERIFIED-PRIMARY |
| FEMA.CPR24.R10.PAY_COMPOUNDING | Pay the compounding amount | 15 days from the **date of the compounding order** | **HARD**: if missed, the application is deemed never made (r.11) | VERIFIED-PRIMARY |
| FEMA.CPR24.R4_2.THREE_YEAR_BAR | Eligibility to compound | A similar contravention within 3 years of an earlier compounding is not compoundable | Eligibility gate | VERIFIED-PRIMARY (boundary TVP) |
| FEMA.CPR24.R8_2.AUTHORITY_180D | Compounding authority's own timeline | 180 days from a complete application | Authority-side; **not a client deadline** | VERIFIED-PRIMARY |
| FEMA.LSF.2022 | Late submission fee for reporting delays | Available up to 3 years from the due date; pay within 30 days of the advice | Informational and eligibility | VERIFIED-PRIMARY |

---

### 1. Shared computation conventions (apply to every RuleSpec below)

1. **The trigger event differs by provision, and the engine must store which one applies.**
   - "Receipt of copy": SEBI Act s.15T(3), SCRA s.23L(2), Depositories Act s.23A(3), Competition Act s.53B(2), FEMA ss.17(3) and 19(2).
   - "Communication": SEBI Act s.15Z, SCRA s.22F, Depositories Act s.23F, Competition Act s.53T, FEMA s.35.
   - "Service": Penalty Rules r.4(1), Intermediaries Regulations r.25(2), SAT Rules r.14(1), FEMA Adjudication Rules r.4(1), Settlement Regulations 2018 r.4(1).
   - "Date of the order": Penalty Rules r.5(5) and FEMA Compounding Rules r.10. **These two clocks run even if the order reaches the client late.**
2. **Who proves the trigger date.** The appellant states the date of receipt in the memo of appeal. The regulator relies on its service record. SEBI may serve by digitally signed e-mail; "bouncing of the electronic mail shall not constitute valid service" (Penalty Rules r.7(1), proviso) [S-R1]. The matter workspace must capture the *e-mail receipt timestamp* as well as the physical receipt date, and flag any gap between them.
3. **First-day exclusion.** General Clauses Act 1897 s.9 is used for Central Acts and for rules made under them. For SEBI and CCI regulations, first-day exclusion is applied by analogy (**TVP**: confirm the partner's convention). The text of GCA s.9 is held in the core rules file, not re-verified here. The golden vectors below exclude the trigger day: last day = trigger date + N.
4. **Court-closed extension.**
   - SEBI Act s.15W: "The provisions of the Limitation Act, 1963 … shall, as far as may be, apply to an appeal made to a Securities Appellate Tribunal" [S-R2]. So Limitation Act s.4 (next opening day) and s.5 apply to SAT appeals. **TVP:** the SAT holiday calendar, because the site is down.
   - Whether Limitation Act s.4 applies to NCLAT competition appeals, the Special Director (Appeals) and the FEMA Appellate Tribunal: **TVP**.
   - Capped extension windows (s.15Z, FEMA s.35, the CCI caps): s.4 does not extend a condonation window that is not the "prescribed period" (State of West Bengal v Rajpath Contractors, SC 2024, on the Arbitration Act s.34(3) proviso; `snippet` [S-R35]). Applying that by analogy here is **TVP**.
5. **Golden vectors give the raw last day.** The engine then applies the forum-closure calendar separately, only where s.4 applies.
6. **Never compute a deadline from a SCN.** A SCN's reply date is whatever the notice states. The rules here only validate it against statutory floors and caps (14, 10 or 21 days) and raise a "possible procedural ground" flag.

---

### 2. T-SEBI-1: SEBI show-cause notice received

#### 2.1 Pick the regime from the SCN caption (intake step)
| SCN caption or recital | Regime | Who decides | Reply-period source |
|---|---|---|---|
| "Rule 4(1) of SEBI (Procedure for Holding Inquiry and Imposing Penalties) Rules, 1995" plus s.15-I | Adjudication by an AO | Adjudicating Officer | Penalty Rules r.4(1): at least 14 days |
| "Sections 11(1), 11(4), 11(4A), 11B(1), 11B(2), 11D" (WTM "quasi-judicial" SCN) | Directions or disgorgement, and penalty if under s.11(4A)/11B(2) | Whole Time Member | Penalty part: r.4(1) (the rules now read "the Board or the adjudicating officer"). Directions part: no statutory period (PRACTICE) |
| "Chapter V, SEBI (Intermediaries) Regulations, 2008", "designated authority" | Enquiry against an intermediary | Designated authority, then the competent authority | r.25(2): at most 21 days |
| SCRA s.23-I or Depositories Act s.19-I adjudication | Adjudication under the SCRA or DA | AO | SCRA and DA penalty rules 2005 (listed on SEBI's rules page; text not read, **TVP**) [S-R10] |

#### 2.2 RuleSpecs

**SEBI.PENRULES.R4.SCN_REPLY**
- *Trigger:* the date the SCN is served under r.7. Proof: the service record (hand delivery, speed post with AD, or digitally signed e-mail).
- *Computation:* the deadline is the date **stated in the notice**. Validation check: the stated date must be at least service date + 14 days, counting calendar days and excluding the day of service.
- *Nature:* the 14-day floor binds SEBI and is not a client deadline. The client's deadline is the notice date (PRACTICE: extensions are routinely sought by letter; whether one is granted is discretionary, **TVP**).
- *Anchor:* SEBI (Procedure for Holding Inquiry and Imposing Penalties) Rules 1995, r.4(1): "issue a notice to such person requiring him to show cause within such period as may be specified in the notice (being not less than fourteen days from the date of service thereof) why an inquiry should not be held against him". r.4(2): the notice "shall indicate the nature of offence alleged". r.4(7) allows the inquiry to proceed ex parte. Consolidated text last amended 31-12-2021 (G.S.R. 919(E)) [S-R1] `verified`.
- *Related:* SEBI Act s.15-I(1) requires "a reasonable opportunity of being heard"; s.11(4A) and s.11B(2) let the Board levy penalty "after holding an inquiry in the prescribed manner" [S-R2] `verified`.
- *Case law:* none needed for the computation. On the remedy for too short a period: **TVP**.
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors (floor check):* served 2026-10-01, so the earliest lawful due date is **2026-10-15**. Served 2026-12-25, so the earliest is **2027-01-08**.
- *Notes:* the r.4(1) list reads "15A … 15G, 15HA and 15HB". The 2006 amendment substituted ", 15HA and 15HB" for "and 15H", so 15H does not appear in the rule although s.15-I(1) covers 15H. This is a possible drafting point (**TVP**). No amendment after 31-12-2021 appears on SEBI's rules page as at 2026-10-01 [S-R10].

**SEBI.PENRULES.R5_5.RECTIFICATION**
- *Trigger:* the **date of the order**, not the date it was received.
- *Computation:* 15 days, excluding the order date.
- *Nature:* HARD as written; no extension clause. The Board or AO may also rectify of its own motion.
- *Anchor:* r.5(5): "may rectify any error apparent on the face of record … either on its own motion or where such error is brought to his notice by the affected person within a period of fifteen days from the date of such order." The Explanation limits this to typographical-type errors [S-R1] `verified`.
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* order 2026-10-01 gives **2026-10-16**. Order 2026-12-22 gives **2027-01-06**.
- *Notes:* this does not stop the s.15T 45-day clock. Diarise both.

**SEBI.S11.DIRECTIONS_SCN_REPLY** and **SEBI.S11.INTERIM_ORDER_OBJECTIONS**
- *Anchor:* SEBI Act s.11B(1) ("after making or causing to be made an enquiry") and s.11D (cease and desist "after causing an inquiry to be made"). s.11(4), second proviso: "the Board shall, either before or after passing such orders, give an opportunity of hearing" [S-R2] `verified`. **No statutory reply period.**
- *Practice:* SCNs commonly allow about 21 days (`snippet` [S-R38]). Interim orders state their own window for objections.
- *Nature:* PRACTICE, so **TVP**. The engine shows the date stated in the notice or order, labelled "as stated; no statutory rule".

**SEBI.INTERMED.R25_2.SCN_REPLY**
- *Trigger:* service of the designated authority's notice (Intermediaries Regulations reg. 34 modes, which include e-mail).
- *Computation:* the date stated in the notice. Cap check: at most service + 21 days.
- *Nature:* DIRECTORY. The designated authority "may extend the time … for sufficient grounds … after recording reasons in writing".
- *Anchor:* reg. 25(2): "within a period to be specified in the notice, not exceeding twenty-one days from the date of service thereof, a written reply". reg. 25(4) requires the documents relied on to be annexed, with extracts of the inspection or investigation report. reg. 25(7) allows ex parte conclusion. Text as substituted with effect from 21-01-2021, consolidated up to 16-04-2026 [S-R3] `verified`.
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors (cap check):* served 2026-10-01, latest permissible stated date **2026-10-22**. Served 2026-12-20, latest **2027-01-10**.

**SEBI.INTERMED.R25_5.INSPECTION_REQUEST**
- *Anchor:* reg. 25(5): "If the noticee demands inspection of such documents within the period specified in sub-regulation (2) … the designated authority may issue … a notice fixing a date for inspection … Provided that the date for inspection of documents shall be within thirty days from the date of receipt of such request." [S-R3] `verified`.
- *Client deadline:* the request must be made by the reply due date. *Authority-side:* the inspection date must fall within 30 days of the request (example: request 2026-10-05, inspection by 2026-11-04).
- *Nature:* the request is HARD as written; whether inspection is granted is discretionary ("may").
- *Status:* VERIFIED-PRIMARY.

**SEBI.INTERMED.R27_2.DA_REPORT_REPLY**
- *Anchor:* reg. 27(2): "within a period as specified in the notice, but not exceeding twenty-one days from the date of service thereof … Provided that upon the request of the noticee, the competent authority, after recording reasons, in writing may cause to extend the time". The competent authority must give a personal hearing only where cancellation is recommended or is prima facie in view (reg. 27(4)) [S-R3] `verified`.
- *Status:* VERIFIED-PRIMARY. *Vectors:* the same as R25_2.

**SEBI.SETTLE18.R4_1.APPLICATION** (the main SEBI deadline)
- *Trigger:* the date of service of the SCN, or of the last supplementary SCN, **whichever is later**. The engine must track every supplementary SCN.
- *Computation:* 60 calendar days, excluding the service day.
- *Nature:* **HARD.** reg. 4(2), the sufficient-cause window (with a 25% uplift and an outer cap of 120 days), was "Omitted by the … (Amendment) Regulations, 2022, w.e.f. 14-01-2022" [S-R4] `verified`.
- *Anchor:* reg. 4(1): "An application in respect of any specified proceeding pending before the Board shall not be considered if it is made after sixty days from the date of service of the notice to show cause or supplementary notice(s) to show cause, whichever is later." reg. 4(3): "shall not apply in the case of proceedings pending before the Tribunal or any court." Consolidated "[Amended upto November 28, 2024]" [S-R4] `verified`.
- *Consequence of filing:* reg. 8(1): "shall not affect the continuance of the proceedings save that the passing of the final order shall be kept in abeyance till the application is disposed of" [S-R4] `verified`.
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* served 2026-10-01, last day **2026-11-30**. Served 2026-12-31, last day **2027-03-01**.
- *Point in time:* see SEBI.SETTLE26 below. When the 2026 Regulations commence, applications after a SCN get 90 days, and there is a one-time 90-day window for pending matters, including where the 60 days has lapsed. Do not apply this until it is notified.

**SEBI.SETTLE18.R15_2a.REMIT**
- *Anchor:* reg. 15(2): the notice of demand issues "within seven working days of the decision of the panel", and the applicant shall "(a) remit the settlement amount … not later than thirty calendar days from the date of receipt of the notice of demand". The 60-day extension proviso was omitted with effect from 14-01-2022 [S-R4] `verified`.
- *Nature:* HARD.
- *Golden vectors:* receipt 2026-10-01 gives **2026-10-31**. Receipt 2026-12-10 gives **2027-01-09**.
- *Status:* VERIFIED-PRIMARY.

**SEBI.SETTLE26 (WATCHLIST: not law yet)**
- SEBI Press Release 59/2026, 24-09-2026: "The Board approved the SEBI (Settlement of Administrative and Civil Proceedings) Regulations, 2026 … which will replace the SEBI (Settlement Proceedings) Regulations, 2018 … shall come into force the day succeeding the 30th day from the date of notification".
  - A settlement notice will issue *before* a SCN, "giving 60 days to file a settlement application". It will not issue where prosecution or an interim order is contemplated.
  - "The period for filing a settlement application after service of a show cause notice increased from 60 days to 90 days."
  - There will be a "One-time window of 90 days from commencement" for pending proceedings, with an additional 20% settlement amount.
  - There will be a fast-track route at or below ₹10 lakh [S-R5] `verified`.
- The SEBI regulations listing at 2026-10-01 still shows the 2018 Regulations as current; there is no 2026 notification [S-R10] `verified`.
- **Engine:** hold rule versions SEBI.SETTLE26.SCN_90D, SEBI.SETTLE26.SETTLEMENT_NOTICE_60D and SEBI.SETTLE26.ONE_TIME_90D as *not in force*. Watch the SEBI regulations listing and the Gazette. On notification, compute commencement as notification date + 31 days and confirm against the gazetted text.
- **TVP:** the transitional rule for SCNs served before commencement.

**Inspection of documents in AO or WTM proceedings (practice plus case law)**
- The Penalty Rules have no inspection rule. r.4(5) gives an "opportunity … to produce such documents or evidence" [S-R1].
- In practice the noticee requests inspection of the documents relied on and of the investigation report.
- *T. Takano v SEBI*, Civil Appeal 487-488 of 2022, decided 18-02-2022: SEBI must disclose the investigation report (redacted for third-party or confidential material) and give a hearing on what is disclosed. Links: https://indiankanoon.org/doc/69409420/ and https://api.sci.gov.in/supremecourt/2020/24222/24222_2020_34_1502_33505_Judgement_18-Feb-2022.pdf (`snippet` [S-R14]).
- Follow-ups to check: *Kavi Arora v SEBI* (SC, 14-09-2022) and the 2025 commentary on "relied-upon only" disclosure (`snippet` [S-R18], [S-R19]).

#### 2.3 Draft output for T-SEBI-1

**Strategy memo (sections in order)**
1. **Snapshot.** Noticee(s), SCN date, service date and mode, regime (from table 2.1), sections and regulations alleged, sanctions proposed (penalty range under s.15A–15HB; directions; disgorgement with interest; debarment), and any parallel actions (exchange, prosecution under s.24, other regulators).
2. **Deadlines panel.** Each line shows its tag: VERIFIED, AS STATED IN NOTICE, or TVP.
   - Reply date as stated, with the r.4(1) 14-day floor check or the reg. 25(2) 21-day cap check.
   - **Settlement window: 60 days, HARD** (SETTLE18.R4_1). Note that the 2026 regime is pending.
   - Inspection request: by the reply date under reg. 25(5); otherwise at once.
   - Personal hearing date once notified.
3. **Their allegations.** A numbered list that mirrors the SCN paragraphs, generated from the parsed SCN with paragraph anchors.
4. **Our grounds** (choose those that apply):
   - jurisdiction or wrong regime;
   - delay and laches (**TVP** on the current SC and SAT position);
   - non-disclosure of the investigation report or relied-upon documents (T. Takano);
   - vague or omnibus charge (r.4(2) "nature of offence"; reg. 25(3) "specify the contravention");
   - merits defences per allegation;
   - parity with other noticees;
   - quantum under s.15J and r.5(2) factors (no disproportionate gain, no investor loss, not repetitive), with the AO's discretion per *AO, SEBI v Bhavesh Pabari*, 28-02-2019 (`snippet` [S-R16]).
5. **Adverse authorities to check** (citator status before use):
   - *SEBI v Shriram Mutual Fund* (2006) 5 SCC 361: mens rea not needed for civil penalty (`snippet` [S-R15]).
   - *SEBI v Kishore R. Ajmera* (2016): preponderance of probabilities and inferential proof. It is relied on in [S-R17]; full text not read.
   - *SEBI v Terrascope Ventures Ltd*, 2026 INSC 245 (17-03-2026): SC reversed SAT and restored PFUTP findings on a preferential-issue misstatement (`verified` header only [S-R17]).
   - Recent SAT orders on the same regulation, pulled from the corpus.
6. **Evidence checklist:**
   - trading and demat statements, order and trade logs, KYC and relationship maps;
   - board and audit committee minutes;
   - exchange disclosures (LODR reg. 30 filings) and price-sensitive announcement timelines;
   - PIT records: the structured digital database, trading-window closures, pre-clearances, the designated-persons list and the UPSI-sharing log;
   - e-mails and call records;
   - auditor and forensic reports;
   - SAST disclosures (reg. 29/31) and open-offer workings;
   - ICDR offer-document drafts and due-diligence files;
   - compliance-officer certificates.
7. **Settle vs contest.** Indicative settlement amount (Schedule-II formula of the 2018 Regulations; compare the 2026 formula once notified), exclusions under reg. 5 (market-wide impact, investor losses, integrity), and the effect on other proceedings.
8. **Disclosure duty of a listed noticee.** Does LODR reg. 30 / Schedule III require disclosure of the SCN or order? **TVP** against the LODR text as last amended 14-07-2026 [S-R12].
9. **Open questions for the partner.**

**Reply skeleton (SEBI SCN)**
- Part A. Preliminary submissions: without prejudice; reservation of the right to file an additional reply after inspection; request for the investigation report and relied-upon documents; request for a personal hearing; jurisdiction or limitation objections.
- Part B. **Allegation-by-allegation grid:**

| SCN ¶ (anchor) | Allegation (quoted) | Provision alleged | SEBI's evidence (Annexure no.) | Our response (admit, deny, or explain) | Our evidence (Exhibit) | Legal ground and authority (citator status) | Open issue |
|---|---|---|---|---|---|---|---|

- Part C. Quantum and mitigation (s.15J; r.5(2)(a)–(c)).
- Part D. Prayer: drop proceedings, or in the alternative minimum penalty.
- Annexures; verification; authorisation.

---

### 3. T-SEBI-2: appeal to SAT, then to the Supreme Court

#### 3.1 RuleSpecs

**SEBI.S15T_3.SAT_APPEAL**
- *Trigger:* the date the appellant **receives a copy** of the order (SEBI, AO, IRDAI or PFRDA). The appellant states and proves it.
- *Computation:* 45 calendar days, excluding the day of receipt. Limitation Act s.4 applies through s.15W, subject to the SAT calendar.
- *Nature:* CONDONABLE with **no cap**.
- *Anchor:* SEBI Act s.15T(3): "Every appeal under sub-section (1) shall be filed within a period of forty-five days from the date on which a copy of the order made by the Board or the Adjudicating Officer … is received by him … Provided that the Securities Appellate Tribunal may entertain an appeal after the expiry of the said period of forty-five days if it is satisfied that there was sufficient cause for not filing it within that period." s.15W applies the Limitation Act "as far as may be". s.15T(6) asks SAT to "endeavour … to dispose of the appeal finally within six months", which is DIRECTORY [S-R2] `verified`. Repeated in SAT (Procedure) Rules 2000 r.3(1) [S-R7] `verified`.
- *Case law:* the text is enough for the computation. Liberal construction of "sufficient cause" is general SC law (**TVP**: pick a leading SAT condonation order for the corpus).
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* receipt 2026-10-01 gives a raw last day of **2026-11-15** (a Sunday; s.4 would move it to the next SAT working day, subject to the calendar). Receipt 2026-12-20 gives **2027-02-03**.
- *Notes:* the SEBI-hosted consolidated SEBI Act is "as amended by the Finance Act, 2021". The SEBI acts listing shows no later amendment at 2026-10-01 [S-R10]. **Watchlist:** the Securities Markets Code, 2025 would repeal the SEBI Act, SCRA and DA. It was introduced in the Lok Sabha on 18-12-2025, and the Standing Committee reported on 23-07-2026; it is not passed. PRS notes it "leaves out certain orders from the purview of appeal to SAT" [S-R13] `verified` (secondary).

**SCRA.S23L_2.SAT_APPEAL** and **DEPACT.S23A_3.SAT_APPEAL**
- *Anchors:*
  - SCRA s.23L(2): "Every appeal under sub-section (1) shall be filed within a period of forty-five days from the date on which a copy of the order or decision is received by the appellant … Provided that the Securities Appellate Tribunal may entertain an appeal after the expiry of the said period of forty-five days if it is satisfied that there was sufficient cause". s.23L(1) covers orders of a **recognised stock exchange**, the AO, or SEBI under s.23-I(3) [S-R8] `verified`.
  - Depositories Act s.23A(3): the same 45 days "from the date on which a copy of the order made by the Board is received", with the same proviso [S-R9] `verified`.
- *Nature:* CONDONABLE, no cap. *Status:* VERIFIED-PRIMARY. *Vectors:* the same as s.15T.

**SCRA.S22A.LISTING_REFUSAL_APPEAL**
- *Anchor:* SCRA s.22A(1). Where a recognised stock exchange "refuses to list the securities of any company", the company may, "(a) within fifteen days from the date on which the reasons for such refusal are furnished to it, or (b) where the stock exchange has omitted or failed to dispose of, within the time specified … within fifteen days from the date of expiry of the specified time or within such further period, not exceeding one month, as the Securities Appellate Tribunal may, on sufficient cause being shown, allow, appeal to the Securities Appellate Tribunal" [S-R8] `verified`.
- *Nature:* CONDONABLE with a cap of 1 month. **TVP:** whether the one-month extension also governs clause (a), since the layout places it inside (b). The text still cross-refers to s.73 of the Companies Act 1956 (legacy).
- *Golden vectors (15-day base only):* reasons furnished 2026-10-01 gives **2026-10-16**; 2026-12-20 gives **2027-01-04**.
- *Status:* VERIFIED-PRIMARY (base period).

**SAT.PROC.R14.RESPONDENT_REPLY** (used when the client is the respondent or an intervenor, or to diarise SEBI's reply)
- *Anchor:* SAT (Procedure) Rules 2000 r.14(1): the respondent may file its reply "within one month of the service of the notice on him of the filing of the memorandum of appeal". r.14(4): "The Appellate Tribunal may, in its discretion, on application by the respondent allow the filing of reply … after the expiry of the period". r.13 has the Registrar serve the memo and paper book "as soon as they are registered" [S-R7] `verified`.
- *Nature:* DIRECTORY.
- *Status:* VERIFIED-PRIMARY for the text. **TVP:** the SEBI-hosted copy shows amendments up to 2005; later amendments and SAT e-filing practice directions could not be checked because sat.gov.in returned 503. Rejoinder timelines are set by SAT order (PRACTICE). Month arithmetic is to follow the core engine's convention, so **no vectors** here.

**SEBI.S15Z.SC_APPEAL** (same rule for **SCRA s.22F** and **DA s.23F**)
- *Trigger:* the date of **communication** of the SAT decision.
- *Computation:* 60 days, then a condonation window of at most 60 days running from the end of the first 60.
- *Nature:* CONDONABLE with a cap of 60 days. Appeal lies only "on any question of law arising out of such order".
- *Anchor:* SEBI Act s.15Z: "within sixty days from the date of communication of the decision or order of the Securities Appellate Tribunal to him on any question of law … Provided that the Supreme Court may, if it is satisfied that the applicant was prevented by sufficient cause from filing the appeal within the said period, allow it to be filed within a further period not exceeding sixty days." [S-R2]. SCRA s.22F and DA s.23F use identical words [S-R8], [S-R9]. All `verified`.
- *Case law:* the cap is express. Analogue: *Chhattisgarh SEB v CERC* (2010) 5 SCC 23 on a similar cap (`unverified` [S-R36]).
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* communicated 2026-10-01 gives base **2026-11-30** and outer cap **2027-01-29**. Communicated 2027-01-15 gives base **2027-03-16** and outer cap **2027-05-15** (a Saturday; do *not* roll the cap forward unless the partner confirms s.4 applies to the window).

#### 3.2 Draft output for T-SEBI-2

**Strategy memo:**
- the order under appeal (forum, date, operative directions, penalty);
- the limitation computation, showing the receipt date, its proof and the raw and effective last day;
- whether a delay-condonation application is needed;
- appealable or not (s.15T(1));
- a stay or interim-relief strategy (SAT commonly conditions a stay on deposit of a part of the penalty: PRACTICE, **TVP**);
- grounds grouped as jurisdiction, natural justice (non-disclosure, no hearing), merits and quantum;
- adverse SAT and SC authorities with citator status;
- the parallel settlement option (2018 reg. 4(3): the 60-day bar does not apply before the Tribunal; the 2026 regime adds re-consideration at the appellate stage, pending);
- the next-tier path (s.15Z, questions of law only, and its cap).

**SAT appeal memo skeleton** (the Form under SAT Rules r.4, as followed in practice):
1. Particulars of the appellant and respondent.
2. Order appealed against (number, date, authority).
3. Jurisdiction statement.
4. **Limitation statement:** "copy received on [date] by [mode]; appeal filed within 45 days"; or "delay of N days; Misc. Application for condonation filed".
5. Facts in brief, with paragraph anchors to the impugned order.
6. Questions of law.
7. Grounds A, B, C …, each linked to an impugned-order paragraph and an authority.
8. Relief sought.
9. Interim relief.
10. Matters not pending elsewhere.
11. List of documents and paper book index.
12. Verification and fee.

Companion drafts: a condonation application (day-by-day explanation of the delay) and a stay application with a deposit offer.

---

### 4. T-COMP-1: CCI investigation, then NCLAT and the Supreme Court

#### 4.1 Instruments in force (verified on the CCI list, 2026-10-01 [S-R26])
- The **CCI (General) Regulations, 2024** (No. 08 of 2024, Gazette CG-DL-E-17092024-257199, 17-09-2024) **replace the 2009 General Regulations** that the task names. No General amendment has been listed since then.
- Also in force: Settlement Regulations 2024 and Commitment Regulations 2024 (06-03-2024); Commitment Amendment Regulations 2026 (Gazette No. 514, 18-08-2026); Combinations Regulations 2024 (09-09-2024); Determination of Monetary Penalty Guidelines 2024; Manner of Recovery of Monetary Penalty Regulations 2025 [S-R23]–[S-R26] `verified`.

#### 4.2 RuleSpecs

**CCI.GEN24.R22_2.DG_REPORT_OBJECTIONS**
- *Trigger:* receipt of the (non-confidential) DG investigation report forwarded by the Secretary.
- *Computation:* 8 weeks, which is 56 days, excluding the day of receipt.
- *Nature:* regulatory. A general extension practice exists, but its basis is **TVP**: the confidentiality-ring extension power in reg. 36(12) is specific to that regulation.
- *Anchor:* reg. 22(2)(i): "forward a physical or electronic copy of the non-confidential version of the report … to … the parties concerned … for filing objections or suggestions, if any, thereto, within a period of 08 (eight) weeks from the receipt of the report". reg. 22(3) allows a direction to file financial information (turnover regulations and penalty guidelines). The same 8 weeks applies to a supplementary report under reg. 22(6)(i) [S-R23] `verified`.
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* receipt 2026-10-01 gives **2026-11-26**. Receipt 2026-12-15 gives **2027-02-09**.

**CCI.GEN24.R36.CONFIDENTIALITY_RING** (several clocks)
- reg. 36(7)(b): a request made after receiving the non-confidential report "shall be made within a period of 10 (ten) days from the receipt thereof: Provided that if the Commission is satisfied that the party was prevented by sufficient cause … it may entertain the request made within a further period of 7 (seven) days." So 10 days, CONDONABLE with a cap of 7.
- reg. 36(9): undertakings within 10 days of the order setting up the ring, plus at most 5. CONDONABLE with a cap of 5.
- reg. 36(11): inspection application within 7 days of the undertakings; inspection "completed … within a period of 21 (twenty-one) days of being allowed"; certified-copy application within 7 days after that; supply within 14 days (the Secretary may extend "for a further period of 7 (seven) days but not thereafter").
- reg. 36(12)(1): "The Commission may … in exceptional cases, extend the timelines prescribed under this regulation". reg. 36(12)(2): if a party fails, "the Commission shall continue with the proceedings".
- Source: [S-R23] `verified`.
- *Status:* VERIFIED-PRIMARY. Because of reg. 36(12), classify these as CONDONABLE (cap) with an "exceptional" override.
- *Golden vectors (36(7)(b)):* receipt 2026-10-01 gives **2026-10-11**, cap **2026-10-18**. Receipt 2026-12-26 gives **2027-01-05**, cap **2027-01-12**.

**CCI.SETTLE24.R5_2.APPLICATION**
- *Anchor:* Competition Act s.48A(2), inserted 2023: the application may be made "at any time after the receipt of the report of the Director General … but prior to such time before the passing of an order under section 27 or section 28 as may be specified by regulations" [S-R21].
- CCI (Settlement) Regulations 2024 reg. 5(2), provisos: "shall not be entertained … if it is made after expiry of 45 (forty five) days from the receipt of report of the Director General or confidential version thereof … Provided further that the Commission may entertain a Settlement Application after the period specified above, if the Settlement Application is received within a further period of 30 (thirty) days and the Commission is satisfied that there had been sufficient cause" [S-R24] `verified`.
- *Nature:* CONDONABLE with a cap of 30.
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* receipt 2026-10-01 gives **2026-11-15**, cap **2026-12-15**. Receipt 2026-12-15 gives **2027-01-29**, cap **2027-02-28**.
- *Notes:* settlement applies only to s.3(4) and s.4 cases. Under s.48A(7) "No appeal shall lie under section 53B against any order passed by the Commission under this section" [S-R21] `verified`.

**CCI.COMMIT24.R3_3.APPLICATION**
- *Anchor:* Competition Act s.48B(2): "at any time after an order under sub-section (1) of section 26 has been passed … but within such time prior to the receipt by the party of the report of the Director General" [S-R21].
- Commitment Regulations 2024 reg. 3(3): "A Commitment Application shall be filed within 45 (forty five) days from the receipt of the order passed by the Commission under sub-section (1) of section 26", plus "a further period of 30 (thirty) days" on sufficient cause [S-R25] `verified`.
- **Amended:** "the words '45 (forty-five)' shall be substituted with the words '60 (sixty)'". This took effect on publication, Gazette Extraordinary No. 514, 18-08-2026 [S-R25] `verified`. reg. 3(2) also requires filing before receipt of the DG report, "whichever is earlier".
- *Nature:* CONDONABLE with a cap of 30, and an outer bar at receipt of the DG report.
- *Status:* VERIFIED-PRIMARY. **TVP:** whether 60 days applies to s.26(1) orders received before 18-08-2026.
- *Golden vectors (post-amendment):* receipt 2026-10-01 gives **2026-11-30**, cap **2026-12-30**. Receipt 2026-12-15 gives **2027-02-13**, cap **2027-03-15**. In both cases the answer is "or receipt of the DG report, if earlier".

**COMP.S53B_2.NCLAT_APPEAL**
- *Trigger:* receipt of a copy of the CCI direction, decision or order.
- *Computation:* 60 days, excluding the day of receipt.
- *Nature:* CONDONABLE with **no cap**.
- *Anchor:* Competition Act s.53B(2): "Every appeal under sub-section (1) shall be filed within a period of sixty days from the date on which a copy of the direction or decision or order made by the Commission is received … Provided that the Appellate Tribunal may entertain an appeal after the expiry of the said period of sixty days if it is satisfied that there was sufficient cause for not filing it within that period." [S-R20] `verified`.
- **2023 second proviso:** "no appeal by a person, who is required to pay any amount in terms of an order of the Commission, shall be entertained by the Appellate Tribunal unless the appellant has deposited twenty-five per cent. of that amount in the manner as directed by the Appellate Tribunal" (Amendment Act 2023, s.39) [S-R21] `verified`. In force from 18-05-2023 under S.O. 2228(E) (`snippet` [S-R22]).
- *Status:* VERIFIED-PRIMARY.
- *Golden vectors:* receipt 2026-10-01 gives **2026-11-30**. Receipt 2027-02-10 gives **2027-04-11** (a Sunday; whether s.4 applies is **TVP**).
- *Notes:* the CCI-hosted Act PDF predates 2023, so read it with the Amendment Act. **TVP:** NCLAT Rules 2016 for reply and rejoinder timelines in competition appeals, and the NCLAT's 6-month disposal endeavour in s.53B(5) (DIRECTORY; not re-read).

**COMP.S53T.SC_APPEAL**
- *Anchor:* s.53T: "within sixty days from the date of communication of the decision or order of the Appellate Tribunal to them; Provided that the Supreme Court may, if it is satisfied that the applicant was prevented by sufficient cause from filing the appeal within the said period, allow it to be filed **after the expiry of the said period of sixty days**." [S-R20] `verified`.
- *Nature:* CONDONABLE with **no cap**. This differs from SEBI s.15Z and FEMA s.35, which cap at 60 more days.
- *Status:* VERIFIED-PRIMARY. **TVP:** whether any 2023 amendment changed s.53T; none was seen in the 2023 Amendment Act text that was read.
- *Golden vectors:* communicated 2026-10-01 gives **2026-11-30**. Communicated 2027-01-15 gives **2027-03-16**.

**Other CCI steps (TVP; general mode):**
- penalty SCNs under ss.43–45 and s.48C;
- hearing notices under reg. 30;
- a s.26(1) prima facie order directing investigation (no client clock beyond the commitment window);
- DG summons and information requests, whose dates are set in each notice.

**Watchlist only:**
- Merger control: the Combinations Regulations 2024 (09-09-2024) and the deal-value threshold [S-R26].
- Digital Competition Bill: ex-ante framework paused; MCA commissioned a study in November 2025 (`snippet` [S-R27]).

#### 4.3 Draft output for T-COMP-1

**Strategy memo:**
- the case posture (information or suo motu; s.3(3), s.3(4) or s.4 theory; relevant market);
- the DG's findings by issue;
- a deadlines panel: objections in 8 weeks; confidentiality ring in 10 days (plus 7); settlement in 45 days (plus 30); commitment in 60 days (plus 30) and before the DG report; NCLAT 60 days with the 25% deposit;
- the settlement vs commitment vs contest decision (eligibility applies only to 3(4)/4 cases; there is no appeal from a s.48A/48B order);
- penalty exposure under the 2024 Penalty Guidelines and global-turnover rules;
- adverse authorities (NCLAT and SC competition rulings; **TVP**: corpus pull);
- an evidence checklist (internal pricing and dealer documents, trade-association minutes, e-mails seized under s.41, economic expert report, turnover statements under the 2024 Turnover Regulations).

**Objections to the DG report: para-wise grid:**

| DG report ¶ | Finding | Evidence cited by the DG | Our objection (factual, economic, legal) | Our evidence or expert | Authority (citator status) |
|---|---|---|---|---|---|

**NCLAT appeal memo skeleton:**
- the order and the limitation statement (receipt date, 60 days, plus a condonation application if late);
- a **25% deposit compliance paragraph** or a deposit application;
- facts; grounds (natural justice, market definition, effects, penalty quantum against the Guidelines);
- interim relief; relief sought.

---

### 5. T-FEMA-1: FEMA contravention (adjudication, appeal, compounding)

#### 5.1 RuleSpecs

**FEMA.ADJRULES.R4_1.SCN_REPLY**
- *Anchor:* Foreign Exchange Management (Adjudication Proceedings and Appeal) Rules 2000 (G.S.R. 382(E), 03-05-2000), r.4(1): the Adjudicating Authority "shall, issue a notice to such person requiring him to show cause within such period as may be specified in the notice (being not less than ten days from the date of service thereof) why an inquiry should not be held against him." [S-R29] `verified` (ED-hosted copy; **TVP** whether it reflects later amendments).
- FEMA s.16(1) requires "a reasonable opportunity of being heard". s.16(3) allows inquiry only on a written complaint by an authorised officer. s.16(4) permits representation by "a legal practitioner or a chartered accountant". s.16(6) sets a one-year disposal endeavour, which is DIRECTORY [S-R28] `verified`.
- *Nature:* a floor on the AA; the client's deadline is the date stated in the notice.
- *Golden vectors (floor):* served 2026-10-01, earliest lawful due date **2026-10-11**. Served 2026-12-25, earliest **2027-01-04**.
- *Status:* VERIFIED-PRIMARY.

**FEMA.S17_3.SDA_APPEAL** (for orders of an AA who is an Assistant or Deputy Director of Enforcement)
- *Anchor:* FEMA s.17(3): "Every appeal under sub-section (1) shall be filed within forty-five days from the date on which the copy of the order made by the Adjudicating Authority is received by the aggrieved person … Provided that the Special Director (Appeals) may entertain an appeal after the expiry of the said period of forty-five days, if he is satisfied that there was sufficient cause". The statute says "sub-section (1)", but the right of appeal is in s.17(2) [S-R28] `verified`.
- *Nature:* CONDONABLE, no cap.
- *Golden vectors:* receipt 2026-10-01 gives **2026-11-15**. Receipt 2026-11-20 gives **2027-01-04**.
- *Status:* VERIFIED-PRIMARY.

**FEMA.S19_2.AT_APPEAL** (orders of other AAs, or of the Special Director (Appeals))
- *Anchor:* FEMA s.19(2): "within a period of forty-five days from the date on which a copy of the order … is received by the aggrieved person or by the Central Government … Provided that the Appellate Tribunal may entertain an appeal after the expiry of the said period of forty-five days if it is satisfied that there was sufficient cause".
- **Pre-deposit:** s.19(1), first proviso: "shall while filing the appeal, deposit the amount of such penalty". The second proviso allows the Tribunal to dispense with it for "undue hardship".
- **Forum:** s.18, as substituted by the Finance Act 2017: the Appellate Tribunal constituted under s.12(1) of SAFEMA 1976 "shall … be the Appellate Tribunal for the purposes of this Act".
- s.19(5): 180-day disposal endeavour, DIRECTORY.
- Source: [S-R28] `verified`.
- *Nature:* CONDONABLE, no cap; filing is conditioned on deposit or a waiver.
- *Golden vectors:* the same as s.17.
- *Status:* VERIFIED-PRIMARY.

**FEMA.S35.HC_APPEAL**
- *Anchor:* FEMA s.35: "within sixty days from the date of communication of the decision or order of the Appellate Tribunal to him on any question of law arising out of such order: Provided that the High Court may, if it is satisfied that the appellant was prevented by sufficient cause from filing the appeal within the said period, allow it to be filed within a further period not exceeding sixty days." The Explanation fixes the HC by where the party resides or carries on business [S-R28] `verified`.
- *Nature:* CONDONABLE with a cap of 60.
- *Golden vectors:* communicated 2026-10-01 gives **2026-11-30**, cap **2027-01-29**. Communicated 2027-01-15 gives **2027-03-16**, cap **2027-05-15**.
- *Status:* VERIFIED-PRIMARY.

**FEMA.CPR24.R10.PAY_COMPOUNDING** (the main FEMA client deadline)
- *Instrument:* the **Foreign Exchange (Compounding Proceedings) Rules, 2024**, G.S.R. 566(E), 12-09-2024, made "in supersession of the Foreign Exchange (Compounding Proceedings) Rules, 2000" [S-R30] `verified`. The ED's website still lists the 2000 Rules [S-R34]; do not ingest those as current.
- *Trigger:* the **date of the compounding order** (not its receipt).
- *Computation:* 15 days.
- *Nature:* **HARD.** r.11: "In case a person fails to pay the sum compounded in accordance with rule 10 within the time specified in that rule, he shall be deemed to have never made an application for compounding … and the provisions of the Act for contravention shall apply to him."
- *Anchor:* r.10: "shall be paid … within fifteen days from the date of the compounding order for such contravention." The RBI Master Direction repeats this at para 7.1 and adds that payment must be intimated "not later than 2 hours from time of payment" [S-R30], [S-R31] `verified`.
- *Golden vectors:* order 2026-10-01 gives **2026-10-16**. Order 2026-12-22 gives **2027-01-06**.
- *Status:* VERIFIED-PRIMARY.

**FEMA.CPR24.R4_2.THREE_YEAR_BAR** (eligibility gate; the same text appears in r.5(2) for ED)
- *Anchor:* r.4(2): "Nothing contained in sub-rule (1) shall apply to a contravention committed by any person within a period of three years from the date on which a similar contravention committed by him was compounded under these rules." The Explanation: a contravention "committed after the expiry of a period of three years … shall be deemed to be a first contravention" [S-R30] `verified`. MD para 4.1 [S-R31].
- *Golden vectors (clear cases only):* earlier compounding 2024-10-01 and a similar contravention on 2027-09-15 gives **not compoundable**. Earlier compounding 2024-10-01 and a contravention on 2027-10-15 gives **eligible as a first contravention**. Boundary days are **TVP**.
- *Status:* VERIFIED-PRIMARY.

**FEMA.CPR24.R9.INELIGIBLE** (gate)
- No compounding where the amount "is not quantifiable", where s.37A applies, where the ED sees a serious contravention (money laundering, terror financing, sovereignty), "where the Adjudicating Authority has already passed an order imposing penalty under section 13", or where further investigation is needed [S-R30] `verified`.
- *Effect for the engine:* compounding must be applied for and concluded **before** the AA's penalty order. Under r.7 a compounding after the complaint discharges the person.

**FEMA.CPR24.R8_2.AUTHORITY_180D** (authority-side)
- "pass compounding order as expeditiously as possible but not later than one hundred and eighty days from the date of receipt of such application" [S-R30]. FEMA s.15(1) has the same 180 days [S-R28] `verified`.
- This is **not a client deadline**. Display it as "RBI or ED processing target", never in the client's deadline list.
- RBI routing: by sum involved; AGM up to ₹60 lakh, DGM up to ₹2.5 crore, GM up to ₹5 crore, CGM above that. The fee is ₹10,000 plus GST.
- Incomplete applications, and applications where the client fails to supply information "within the specified period", "shall be liable to be returned" (MD paras 3.5 and 5.2). Under r.14, pending applications at commencement follow the 2000 Rules [S-R30], [S-R31] `verified`.
- The Master Direction is RBI/FED/2025-26/135, FED Master Direction No. 04/2025-26, dated 22-04-2025, "Updated as on April 24, 2025". It replaces the MD of 24-05-2022 [S-R31] `verified`.

**FEMA.LSF.2022** (informational; reporting delays)
- *Anchor:* RBI A.P. (DIR Series) Circular No. 16, RBI/2022-23/122, 30-09-2022.
  - Non-flow returns: LSF of ₹7,500 per return.
  - Flow returns: "[7500 + (0.025% × A × n)]", where n is years of delay "rounded-upwards to the nearest month and expressed up to 2 decimal points".
  - "Maximum LSF amount will be limited to 100 per cent of 'A'".
  - An unpaid advice is "null and void" after 30 days.
  - "The facility for opting for LSF shall be available up to three years from the due date of reporting/ submission."
  - A person who neither files on time nor files with LSF is "liable for penal action" [S-R32] `verified`.
- A 2026 ECB-specific change (A.P. (DIR) Circular No. 25, 30-03-2026, which treats ECB-1 as a non-flow return) was seen only in a search result (`snippet` [S-R33]).
- *Engine:* "LSF eligible until due date + 3 years; after that, use the compounding route". Mark the boundary-day arithmetic **TVP**.

#### 5.2 Draft output for T-FEMA-1

**Strategy memo:**
- which contravention (FDI reporting, pricing, downstream investment, ODI, ECB, export realisation);
- the stage: pre-SCN, SCN or complaint, AA order, appeal;
- **a route decision tree:**
  1. Is it a reporting delay within 3 years of the due date? Then **LSF**.
  2. If not, is it compoundable (r.9 gates, the 3-year bar, quantifiable, no AA order yet)? Then **compound** with RBI (by threshold) or the ED.
  3. If not, contest the adjudication. The appeal lies to the SDA or the AT depending on the AA's rank (s.17(2) and s.19(1)), with a pre-deposit or waiver application.
- deadlines: the reply date as stated (10-day floor); compounding payment within 15 days of the order (HARD, deemed withdrawal); appeal 45 days (condonable); HC 60 + 60 (cap);
- penalty exposure under s.13(1): up to thrice the sum involved; ₹2 lakh where not quantifiable; ₹5,000 per day for continuing contraventions, as quoted in MD para 1.3 [S-R31];
- evidence: FIRMS or SMF filings and acknowledgements, AD bank correspondence, valuation reports, board resolutions, the share allotment timeline (the 180-day refund or allotment rule), FC-GPR or FC-TRS UINs.

**SCN reply grid (FEMA):**

| SCN ¶ | Contravention alleged (provision, regulation, direction) | Transaction facts and dates | Sum involved (as alleged / correct) | Our response | Evidence | Mitigation (bona fide, delay cured, LSF paid, AD bank error) |
|---|---|---|---|---|---|---|

**Compounding application pack:** the Form under the 2024 Rules; the fee; a statement of facts; computation tables mirroring the MD matrix; an undertaking; the PRAVAAH filing (per the MD, `snippet` [S-R31]).

**Appeal memo (SDA or AT):** limitation statement; pre-deposit or waiver application under the s.19(1) proviso; grounds; relief.

---

### 6. SEBI corpus and publication map

#### 6.1 Key regulations: latest consolidated versions on sebi.gov.in at 2026-10-01 [S-R10], [S-R12] `verified`
| Regulation | Page (version-specific URL) | Consolidated PDF behind the page | Header text in the PDF |
|---|---|---|---|
| LODR 2015 | https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-listing-obligations-and-disclosure-requirements-regulations-2015-last-amended-on-july-14-2026-_102974.html | https://www.sebi.gov.in/sebi_data/attachdocs/jul-2026/1784630770711.pdf | "[Last amended on July 14, 2026]" (page title) |
| SAST 2011 | https://www.sebi.gov.in/legal/regulations/dec-2025/securities-and-exchange-board-of-india-substantial-acquisition-of-shares-and-takeovers-regulations-2011-last-amended-on-december-5-2025-_98643.html | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf | "[Amended upto December 5, 2025]" |
| PIT 2015 | https://www.sebi.gov.in/legal/regulations/mar-2025/securities-and-exchange-board-of-india-prohibition-of-insider-trading-regulations-2015-last-amended-on-march-12-2025-_92672.html | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786963663321.pdf | "Amended upto March 12, 2025" |
| ICDR 2018 | https://www.sebi.gov.in/legal/regulations/mar-2026/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-21-2026-_100581.html | https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774592300989.pdf | "[Last amended on March 21, 2026]" (page title) |
| PFUTP 2003 | https://www.sebi.gov.in/legal/regulations/dec-2025/securities-and-exchange-board-of-india-prohibition-of-fraudulent-and-unfair-trade-practices-relating-to-securities-market-regulations-2003-last-amended-on-december-05-2025-_98694.html | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786957017377.pdf | page title "Last amended on December 05, 2025" |
| Intermediaries 2008 | https://www.sebi.gov.in/legal/regulations/apr-2026/securities-and-exchange-board-of-india-intermediaries-regulations-2008-last-amended-on-april-16-2026-_101073.html | https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1777024110709.pdf | "Amended upto April 16, 2026" |
| Settlement 2018 | https://www.sebi.gov.in/legal/regulations/nov-2024/securities-and-exchange-board-of-india-settlement-proceedings-regulations-2018-last-amended-on-november-28-2024-_89270.html | https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786079544836.pdf | "[Amended upto November 28, 2024]" |
| Penalty Rules 1995 | https://www.sebi.gov.in/legal/rules/jan-2022/securities-and-exchange-board-of-india-procedure-for-holding-inquiry-and-imposing-penalties-rules-1995-last-amended-on-december-31-2021-_55412.html | https://www.sebi.gov.in/sebi_data/attachdocs/jan-2022/1642652416221.pdf | last amended 31-12-2021 |
| SAT (Procedure) Rules 2000 | https://www.sebi.gov.in/legal/rules/feb-2000/securities-appellate-tribunal-procedure-rules-2000_34665.html | https://www.sebi.gov.in/sebi_data/attachdocs/apr-2017/1492086931711.pdf | amendments to 2005 |
| SEBI Act, SCRA, DA | SEBI Acts listing (see 6.2) | SEBI Act: …/apr-2021/1618910643277.pdf · SCRA: …/apr-2024/1712903397070.pdf · DA: …/feb-2024/1708418233857.pdf | Finance Act 2021 / Finance Act 2021 / IFSCA Act 2019 |

Other current entries seen on the listing: Delisting 2021 (last amended 03-09-2025); NCS 2021 (21-01-2026); SBEB&SE 2021 (04-12-2025); Depositories and Participants 2018 (22-11-2025); Mutual Funds Regulations **2026** (07-07-2026) and Stock Brokers Regulations **2026** (January 2026), which are new replacement regulations; Procedure for making, amending and reviewing Regulations 2025.

**Versioning behaviour (relevant to ingestion):**
1. Each consolidated version gets a **new page URL with a new numeric id**, and the title carries "[Last amended on …]". Older pages remain online. The "updated as on" date sits in the title and PDF header, not in metadata.
2. **The PDF behind a page can be replaced without a new page.** The SAST (December 2025), PIT (March 2025), Settlement (November 2024) and PFUTP pages all iframe PDFs uploaded in August 2026. Hash the PDF, not just the page. Treat a changed hash on an unchanged "last amended" date as a possible corrigendum or re-upload, and route it to human review.
3. The PDFs are text-based, so pdfminer extraction works. Amendment footnotes carry "w.e.f." dates (SAST has 123 and PIT 141), which can be used to build point-in-time versions.

#### 6.2 How SEBI publishes, and the feeds [S-R10], [S-R11] `verified`
- **RSS:** https://www.sebi.gov.in/sebirss.xml (RSS 2.0, `ttl` 60). It holds only the **latest 30 items across all sections**. On 2026-10-01 these were 12 enforcement orders and 17 recovery proceedings. A busy day can therefore push circulars out of the window: poll hourly **and** poll the listing pages.
- **Listing pages:** https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=…&ssid=…&smid=0
  - Acts: `sid=1&ssid=1`
  - Rules: `sid=1&ssid=2`
  - Regulations: `sid=1&ssid=3`
  - Master Circulars: `sid=1&ssid=6`
  - Circulars: `sid=1&ssid=7`
  - Press Releases: `sid=6&ssid=23`
  - These pages are HTML tables of date, title and link. Each detail page embeds the PDF through `web/?file=…/sebi_data/attachdocs/<mon-yyyy>/<id>.pdf`.
- **URL patterns:**
  - circulars: `/legal/circulars/<mon-yyyy>/<slug>_<id>.html`
  - master circulars: `/legal/master-circulars/…`
  - orders: `/enforcement/orders/<mon-yyyy>/…`
  - settlement orders and recovery: `/enforcement/…`
  - press releases: `/media-and-notifications/press-releases/…`
- **Latest at 2026-10-01:** circular "Review of Position Limits …" (09-09-2026); Master Circular for Debenture Trustees (28-09-2026); PR 59/2026 (24-09-2026).

#### 6.3 CCI, RBI and ED sources [S-R23]–[S-R26], [S-R30]–[S-R34] `verified`
- **CCI:**
  - Regulations list JSON: https://www.cci.gov.in/legal-framwork/fetch-regulationslist (DataTables parameters `draw`, `start`, `length`; 47 records). PDFs are under `/images/legalframeworkregulation/en/`.
  - Act page: https://www.cci.gov.in/legal-framwork/act
- **RBI:**
  - FEMA rule texts appear as HTML at `rbi.org.in/Scripts/bs_viewcontent.aspx?Id=…`.
  - Master Directions at `rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=…`.
  - Notifications at `rbi.org.in/Scripts/NotificationUser.aspx?Id=…`.
  - `rbidocs.rbi.org.in` PDFs return a CAPTCHA to scripts, so prefer the HTML pages.
- **ED:** FEMA documents API https://enforcementdirectorate.gov.in/umbraco/backoffice/api/FemaManagerApi/GetPublic?language=English (JSON of title and PdfUrl). It lists the **superseded** 2000 Compounding Rules.

---

### 7. General-mode notes

Some notices in this area have no RuleSpec here or are marked TVP:
- SEBI s.11C investigation summonses and information requests;
- s.11(4) interim or ex parte orders;
- stock-exchange or depository disciplinary notices and LODR fine letters (the SOP fines under the SEBI master circular);
- SEBI recovery certificates;
- CCI penalty SCNs (ss.43–45, 48C), s.36(2) and DG summonses, and combination (merger) queries;
- RBI letters on ECB, ODI or FDI reporting other than the LSF advice;
- ED summonses under FEMA s.37;
- any SAT or NCLAT procedural direction.

For all of these the system runs in **general mode**. It extracts the notice's own stated dates and shows them as "AS STATED IN NOTICE — no rule-based deadline guarantee". It still produces the strategy memo and para-wise grid outlines above. It attaches the nearest verified rule only as context (for example, "settlement window may apply once a SCN issues"). It never computes or implies a limitation date.

Two kinds of watchlist item never become live deadlines until the Gazette text is ingested and a partner verifies the rule:
- approved but un-notified instruments: the SEBI Settlement Regulations 2026 and the Securities Markets Code 2025;
- authority-side timelines: the RBI or ED 180-day compounding target, SAT's 6-month endeavour, the AA's one-year endeavour, and the CCI's internal 7-day and 4-week steps.

---

### 8. Points that contradict or refine the brief and task

1. **CCI (General) Regulations 2009 have been replaced** by the CCI (General) Regulations 2024 (17-09-2024). Objections to the DG report are due in **8 weeks** under reg. 22(2)(i).
2. **The FEMA Compounding Rules 2000 have been superseded** by the 2024 Rules (G.S.R. 566(E), 12-09-2024). The current RBI MD is No. 04/2025-26 (22-04-2025, updated 24-04-2025). The ED website still lists the 2000 Rules.
3. **SEBI Settlement Regulations 2018 are about to be replaced:** the Board approved the 2026 Regulations on 24-09-2026, but they are not notified. When in force, the 60 days becomes 90. Since 14-01-2022 the 60-day bar has had **no condonation**, so late filing means the application "shall not be considered".
4. **Competition Act s.53T has no cap on condonation**, unlike SEBI s.15Z and FEMA s.35, which allow at most 60 more days. The CCI commitment window became **60 days** on 18-08-2026.
5. **Intermediaries Regulations reg. 25(2)'s 21 days is a ceiling, not a floor.** The Penalty Rules' 14 days and the FEMA Adjudication Rules' 10 days are floors. In none of these cases is the computed figure the client's deadline: the deadline is the date in the notice.
6. **Watchlist:** the Securities Markets Code 2025 (introduced 18-12-2025; Standing Committee report 23-07-2026) would repeal the SEBI Act, SCRA and DA and narrow SAT's appellate jurisdiction.
7. Feed reality: the SEBI RSS carries only 30 items, so circulars need listing-page polling. Consolidated PDFs are silently replaced, so hash them. sat.gov.in remains unavailable (HTTP 503).

---

### 9. References

- [S-R1] SEBI (Procedure for Holding Inquiry and Imposing Penalties) Rules 1995, last amended 31-12-2021. Page: https://www.sebi.gov.in/legal/rules/jan-2022/securities-and-exchange-board-of-india-procedure-for-holding-inquiry-and-imposing-penalties-rules-1995-last-amended-on-december-31-2021-_55412.html; PDF: https://www.sebi.gov.in/sebi_data/attachdocs/jan-2022/1642652416221.pdf. `verified`
- [S-R2] SEBI Act 1992 (as amended by the Finance Act 2021), ss.11, 11B, 11D, 15-I, 15T, 15W, 15Z: https://www.sebi.gov.in/sebi_data/attachdocs/apr-2021/1618910643277.pdf. `verified`
- [S-R3] SEBI (Intermediaries) Regulations 2008, amended up to 16-04-2026, regs. 24–27 and 34: https://www.sebi.gov.in/sebi_data/attachdocs/apr-2026/1777024110709.pdf. `verified`
- [S-R4] SEBI (Settlement Proceedings) Regulations 2018, amended up to 28-11-2024, regs. 4, 8 and 15: https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786079544836.pdf. `verified`
- [S-R5] SEBI PR 59/2026, Board meeting 24-09-2026: https://www.sebi.gov.in/media-and-notifications/press-releases/sep-2026/key-decisions-taken-in-the-sebi-board-meeting-dated-24th-september-2026_104725.html; PDF: https://www.sebi.gov.in/sebi_data/attachdocs/sep-2026/1790259036651.pdf. `verified`
- [S-R6] ELP, "SEBI Board Meeting dated 24.09.2026": https://elplaw.in/wp-content/uploads/2026/09/SEBI-Board-Meeting-dated-24.09.2026-.pdf. `verified` (secondary)
- [S-R7] SAT (Procedure) Rules 2000, rr.3, 13 and 14 (SEBI-hosted): https://www.sebi.gov.in/sebi_data/attachdocs/apr-2017/1492086931711.pdf. `verified` (amendments after 2005 are **TVP**)
- [S-R8] Securities Contracts (Regulation) Act 1956, ss.22A, 22F and 23L: https://www.sebi.gov.in/sebi_data/attachdocs/apr-2024/1712903397070.pdf. `verified`
- [S-R9] Depositories Act 1996, ss.23A and 23F: https://www.sebi.gov.in/sebi_data/attachdocs/feb-2024/1708418233857.pdf. `verified`
- [S-R10] SEBI listing pages (acts, rules, regulations, circulars, master circulars, press releases): https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=3&smid=0 (and the ssid values in §6.2). `verified`
- [S-R11] SEBI RSS: https://www.sebi.gov.in/sebirss.xml. `verified`
- [S-R12] LODR, SAST, PIT, ICDR and PFUTP version pages and PDFs (URLs in §6.1). `verified`
- [S-R13] PRS Legislative Research, Securities Markets Code 2025: https://prsindia.org/billtrack/the-securities-markets-code-2025. `verified` (secondary)
- [S-R14] T. Takano v SEBI (SC, 18-02-2022): https://indiankanoon.org/doc/69409420/; https://api.sci.gov.in/supremecourt/2020/24222/24222_2020_34_1502_33505_Judgement_18-Feb-2022.pdf. `snippet`
- [S-R15] Chairman, SEBI v Shriram Mutual Fund (2006) 5 SCC 361: https://future.indiankanoon.org/doc/1741822. `snippet`
- [S-R16] AO, SEBI v Bhavesh Pabari (SC, 28-02-2019): https://api.sci.gov.in/supremecourt/2013/36291/36291_2013_Judgement_28-Feb-2019.pdf. `snippet`
- [S-R17] SEBI v Terrascope Ventures Ltd, 2026 INSC 245 (17-03-2026): https://api.sci.gov.in/supremecourt/2022/23328/23328_2022_7_1501_69386_Judgement_17-Mar-2026.pdf. `verified` (header and parties read; holdings not fully read)
- [S-R18] Kavi Arora v SEBI (SC, 14-09-2022): https://api.sci.gov.in/supremecourt/2021/22631/22631_2021_5_1504_38169_Judgement_14-Sep-2022.pdf. `snippet`
- [S-R19] CAM Dispute Resolution blog, "Is SEBI obligated to provide only the documents it relies upon" (July 2025): https://disputeresolution.cyrilamarchandblogs.com/2025/07/is-sebi-obligated-to-provide-only-the-documents-it-relies-upon/. `snippet`
- [S-R20] Competition Act 2002 (CCI-hosted, before 2023), ss.53B and 53T: https://www.cci.gov.in/images/legalframeworkact/en/the-competition-act-20021652103427.pdf. `verified`
- [S-R21] Competition (Amendment) Act 2023, ss.48A, 48B and s.39 (amending s.53B): https://www.cci.gov.in/images/legalframeworkact/en/the-competition-amendment-act-20231681363446.pdf. `verified`
- [S-R22] S.O. 2228(E), 18-05-2023 (commencement): https://scconline.com/blog/post/2023/05/20/provisions-of-competition-amendment-act-2023-comes-into-force-w-e-f-18-05-2023/amp. `snippet`
- [S-R23] CCI (General) Regulations 2024, regs. 22 and 36: https://www.cci.gov.in/images/legalframeworkregulation/en/the-competition-commission-of-india-general-regulations-20241731301969.pdf. `verified`
- [S-R24] CCI (Settlement) Regulations 2024, reg. 5: https://www.cci.gov.in/images/legalframeworkregulation/en/the-competition-commission-of-india-settlement-regulations-20241731065378.pdf. `verified`
- [S-R25] CCI (Commitment) Regulations 2024, reg. 3: https://www.cci.gov.in/images/legalframeworkregulation/en/the-competition-commission-of-india-commitment-regulations-20241731302607.pdf. Commitment Amendment Regulations 2026: https://www.cci.gov.in/images/legalframeworkregulation/en/the-competition-commission-of-india-commitment-amendment-regulations-20261787115203.pdf. `verified`
- [S-R26] CCI regulations list (JSON): https://www.cci.gov.in/legal-framwork/fetch-regulationslist. `verified`
- [S-R27] Digital Competition Bill status (Outlook Business / Medianama): https://www.medianama.com/2025/08/223-parliamentary-report-digital-competition-bill-delayed/. `snippet`
- [S-R28] FEMA 1999 (ED-hosted), ss.15–19 and 35: https://enforcementdirectorate.gov.in/media/fema/c24cce9a-6765-4b22-a41a-cde7ec7af79c_FEMA_ACT_1999.pdf. `verified`
- [S-R29] FEM (Adjudication Proceedings and Appeal) Rules 2000 (ED-hosted), r.4: https://enforcementdirectorate.gov.in/media/fema/fe8bad04-d060-4ff9-8d63-b8bb128a805f_Foreign%20Exchange%20Management%20(ADJUDICATION%20PROCEEDINGS%20AND%20APPEAL)%20Rules%202000.pdf. `verified` (currency **TVP**)
- [S-R30] Foreign Exchange (Compounding Proceedings) Rules 2024, G.S.R. 566(E): https://www.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=5082. `verified`
- [S-R31] RBI Master Direction, Compounding of Contraventions under FEMA 1999 (No. 04/2025-26, 22-04-2025, updated 24-04-2025): https://rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12839. `verified`
- [S-R32] RBI A.P. (DIR Series) Circular No. 16 (30-09-2022), LSF: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12393. `verified`
- [S-R33] ECB LSF change, A.P. (DIR) Circular No. 25 (30-03-2026), via Taxmann: https://www.taxmann.com/post/blog/rbi-revises-ecb-reporting-framework-and-timelines/. `snippet`
- [S-R34] ED FEMA documents API: https://enforcementdirectorate.gov.in/umbraco/backoffice/api/FemaManagerApi/GetPublic?language=English. `verified`
- [S-R35] State of West Bengal v Rajpath Contractors (SC 2024), s.4 Limitation Act not available for a condonation window: https://www.livelaw.in/amp/top-stories/s-4-limitation-act-cant-be-invoked-using-30-day-extension-for-arbitration-appeals-filed-beyond-3-months-from-award-supreme-court-262951. `snippet`
- [S-R36] Chhattisgarh SEB v CERC (2010) 5 SCC 23: https://lawsathi.in/judgements/sc/2010/chattisgarh-state-electricity-board-central-electricity-regulatory-commission/. `unverified`
- [S-R37] Business Today on the SEBI settlement reforms (24-09-2026): https://businesstoday.in/personal-finance/story/sebis-new-settlement-rules-90-day-window-fast-track-route-and-new-penalty-formula-explained-557682-2026-09-24. `snippet`
- [S-R38] SEBI SCN practice of about 21 days (Sansa Legal): https://www.sansalegal.com/post/how-to-handle-sebi-show-cause-notices-and-enforcement-proceedings-in-india. `snippet`
- [S-R39] General Clauses Act 1897 s.9 and Limitation Act 1963 ss.4, 5 and 12: see the core rules file. Not re-verified here (indiacode blocked). `unverified` (here)


---

# Part D — Arbitration, commercial suits, contract notices and NI Act s.138

*Source pack title: Arbitration, commercial-suit, contract-notice and s.138 rules pack: T-ARB-1 to T-ARB-5, T-COM-1, T-CON-1, T-NI-1*

Research date: **2026-10-01**. Researcher: arbitration / commercial-litigation rules agent. Format: RuleSpec, as defined in mvp_brief.md and blueprint 08_P6 §5.5.1.

**Status legend.**
- **VERIFIED-PRIMARY**: I read the official text (statute, gazette, regulator circular) and quote the operative words.
- **VERIFIED-SECONDARY**: I read the full statute or judgment text on a reliable secondary host (Indian Kanoon, "IK"), or the statute as quoted verbatim inside a Supreme Court judgment, and I quote the words.
- **TO VERIFY WITH PARTNER**: the point is unsettled, forum-specific, or rests on a search snippet only.

Reference tags (§13) are `verified`, `snippet` or `unverified`.

**Access caveat (this affects every status below).** From this sandbox, indiacode.nic.in timed out or returned 403/504, egazette.gov.in failed TLS or returned 503, and sci.gov.in / webapi.sci.gov.in reset the connection. So every statute text here was read on Indian Kanoon, or in an SC judgment that quotes the statute, and **no statute rule is VERIFIED-PRIMARY**. The only primary text read was the RBI circular. Before any rule is activated, P3/21 must re-anchor it to India Code.

**Ingestion hazard found during this research.** Indian Kanoon's consolidated texts are not reliable as point-in-time sources. (a) Its s.11 Arbitration Act page prints the **un-notified** 2019 substitutions as if in force. (b) Its "Entire Act" page still carries the **pre-2015 s.17**. (c) Its NI Act "Entire Act" page has **no s.143A or s.148**. (d) Its Commercial Courts Act pages show the **pre-2018 s.13 and no s.12A**. (e) Its Specific Relief Act s.20 is the **pre-2018** text. The P1 ingestion pipeline must not treat IK consolidations as `valid_time` truth.

---

### 0. Summary of findings and corrections to the brief or blueprint

| # | Brief or blueprint said | What I found | Source |
|---|---|---|---|
| C1 | Blueprint W2: *Patil Automation* prospective date "unverified, shown as ASSUMED" | **Verified.** Para 84: "We, however, make this declaration effective from **20.08.2022**". Also from para 84: plaints already rejected cannot be reopened, and a plaint filed in breach of s.12A *after the jurisdictional HC declared s.12A mandatory* gets no relief. | [CC-3] |
| C2 | Blueprint P6-37: s.138 provisos (b),(c) "snippet" | **Verified** (IK text): proviso (b) "within thirty days of the receipt of information by him from the bank regarding the return of the cheque as unpaid"; proviso (c) "within fifteen days of the receipt of the said notice". | [NI-1] |
| C3 | Blueprint: *SCG Contracts* decision date not confirmed | **12 February 2019**, CA 1638/2019, (2019) 12 SCC 210 (equivalent citations on IK). | [CC-5] |
| C4 | Blueprint: NI Act s.143A unverified | **Verified-secondary.** Cap of 20%; pay within 60 days of the order, plus a further period of up to 30 days on sufficient cause. Text from the 2017 Bill and a consolidated reproduction; the commencement date (1.9.2018) is unverified. *Rakesh Ranjan Shrivastava* (2024) 4 SCC 419 holds s.143A(1) **directory** (snippet). | [NI-2], [NI-5] |
| C5 | Blueprint ACA.34 RuleSpec: `court_closure_rollover: true`; 30-day extension `extendable: NO` | **Needs a correction.** LA s.4 rollover applies **only to the end of the 3-month period**. If the 30-day condonable window ends in a vacation, there is no rollover, and GCA s.10 is excluded (*My Preferred Transformation*, 2025 INSC 56, para 35, as quoted in *R.K. Transport*, 2025 INSC 438). The blueprint's month-end test vectors (2026-11-30 → 2027-02-28; 2027-01-31 → 2027-04-30) are **consistent** with *Himachal Techno*'s corresponding-date rule. | [AR-8], [AR-9], [AR-7] |
| C6 | Brief T-ARB-1: verify s.11 text in force | The 2019 Amendment Act was notified on 30.08.2019 (S.O. 3154(E)) only for **ss.1, 4–9, 11–13, 15**. **s.3** (which rewrites Act s.11 around "arbitral institutions"), **s.2** and **s.10** (Part IA, Arbitration Council) are **not in force**. So s.11 is the **2015 text**: SC/HC "or any person or institution designated by such Court" appoints; **s.11(6A) survives**; s.11(13) target is **60 days** (the un-notified 2019 text says 30). The **30-day periods in s.11(4)(a), (4)(b) and (5) are the same in both versions.** | [AR-2], [AR-3], [AR-4], [AR-5] |
| C7 | Brief T-ARB-2: s.9(2) "90 days … or such further time" | **Verified**, but s.9 states **no consequence**. The consequence comes from forum rules. *Regenta Hotels v Hotel Grand Centre Point*, 2026 INSC 32 (7 Jan 2026), applied the 2001 Rules used in the Karnataka courts (r.9(4): interim order "shall stand vacated" if proceedings are not initiated within 3 months of presenting the s.9 application). It held that **commencement = the s.21 receipt by the respondent only**: filing a s.11 petition is not commencement, and neither is a judicial application. | [AR-19] |
| C8 | Brief T-ARB-3: s.34(6) "directory — cite" | *Bihar Rajya Bhumi Vikas Bank Samiti* para 23 (as quoted in *SCG Contracts*): for ss.34(5) and (6), "if the period for deciding the application under Section 34 has elapsed, no consequence is provided". Both are directory. | [CC-5] |
| C9 | Brief T-ARB-4: Art.116 "90 days to HC / 30 days other courts" | **Verified**. For intra-HC appeals, **Art.117 (30 days)** also applies. *Borse* para 61 covers all three periods (90/30/60), with condonation "by way of exception and not by way of rule". | [AR-5], [GL-1] |
| C10 | Brief T-COM-1: s.12A mediation period | s.12A(3) (current text): **3 months + 2 months by consent**; the mediation period is excluded from limitation. The Mediation Act 2023 s.64 / Ninth Schedule rewrite of s.12A was **not notified as of 14 May 2025** (secondary source). I found no later notification, but the 27.08.2026 establishment of the Mediation Council is a sign of activity: **TO VERIFY WITH PARTNER**. | [CC-3], [CC-6] |
| C11 | — | **New authorities post-dating the blueprint**: *R.K. Transport* (2025): s.12(1) LA applies to s.34(3); calendar months; s.4 rollover. *Rohan Builders* (2024): a s.29A(4) extension application is maintainable after expiry. *C. Velusamy* (2026 INSC 112): extension is possible even after an award is rendered out of time. *Regenta* (2026). *Sanjabij Tari* (2025 INSC 1158): s.138 procedural guidelines. *Bharat Kalra* (SC order, 9.5.2022): non-commercial WS delay condoned on costs. | §13 |
| C12 | — | **Draft Arbitration and Conciliation (Amendment) Bill 2024** (appellate arbitral tribunal, s.9A emergency arbitrators): a consultation draft only, **not introduced** as of mid-2026 (snippet). Watchlist; never law. | [AR-29] |

Nothing in the brief is contradicted outright. C5 corrects the blueprint's RuleSpec (rollover scope), and C6 corrects any assumption that IK's s.11 text is in force.

---

### 1. Source baseline and point-in-time method

**Arbitration Act 1996, versions that matter:**

| Layer | In force from | Effect on this pack | Status |
|---|---|---|---|
| 2015 Amendment (Act 3 of 2016) | 23.10.2015 | s.8(1), s.9(2)–(3), s.11(6A)/(13), s.17 (substituted), s.29A, s.34(5)–(6), s.36 (no automatic stay) | VERIFIED-SECONDARY [AR-1] |
| 2019 Amendment (Act 33 of 2019), **notified part** | 30.08.2019 (S.O. 3154(E)) | Amendment Act ss.1, 4–9, 11–13, 15. Amends Act ss.17, 23 (new **s.23(4)**), 29A (new **s.29A(1)** keyed to s.23(4); 2nd and 3rd provisos to s.29A(4)), 34, 37, 45, 50; inserts ss.42A, 42B, 87 | VERIFIED-SECONDARY [AR-2] |
| 2019 Amendment, **un-notified part** | — | Amendment Act **s.2** (definition of arbitral institution), **s.3** (s.11 rewrite incl. omission of 6A and 7, 30-day disposal), **s.10** (Part IA, ss.43A–43M, Arbitration Council), **s.14** | VERIFIED-SECONDARY as of 2021 [AR-3]; snippet as of 2024 [AR-4]; re-check India Code |
| s.87 (2019) | struck down | *Hindustan Construction Co v UoI* (27.11.2019) | snippet [AR-26] |
| 2021 Amendment (Act 3 of 2021) | proviso to s.36(3) deemed from 23.10.2015 | unconditional stay of the award if fraud or corruption is prima facie shown | VERIFIED-SECONDARY [AR-1] |
| Draft 2024 Bill | not law | watchlist only | snippet [AR-29] |

**Commercial Courts Act 2015.** The 2018 Amendment (Act 28 of 2018, w.e.f. 3.5.2018, per the IK footnote) lowered the specified value to **₹3 lakh** and inserted **s.12A** and the current **s.13(1)/(1A)**. The CPC amendments in the Schedule (O.V r.1, O.VIII r.1, r.3A, r.5, r.10) date from 23.10.2015.

**NI Act.** ss.143A and 148 come from Act 20 of 2018 (commencement unverified). s.142(2) dates from the 2015 Amendment. Since 1.7.2024 the procedure is BNSS (§10.6).

---

### 2. Shared computation conventions

| Conv. | Rule | Anchor | Status |
|---|---|---|---|
| CV1 "from" | "it shall be sufficient, for the purpose of excluding the first in a series of days or any other period of time, to use the word *from*". | GCA s.9(1) [GL-2] | VERIFIED-SECONDARY |
| CV2 "of" / "within N of" | Exclude the day of the trigger. *Saketh India*: the cause of action arose 15.10.1995, "That day (15th October) is to be excluded for counting the period of one month. Complaint is filed on 15th November, 1995 … within time." | [NI-4] | VERIFIED-SECONDARY |
| CV3 LA s.12(1) | "In computing the period of limitation for any suit, appeal or application, the day from which such period is to be reckoned, shall be excluded." Applies to s.34(3) (*Himachal Techno*; *R.K. Transport*). | [GL-1], [AR-7], [AR-8] | VERIFIED-SECONDARY |
| CV4 Months | GCA s.3(35): "month shall mean a month reckoned according to the British calendar". *Himachal Techno* para 11: the period "would expire in the third month on the date corresponding to the date upon which the period starts … it may mean 90 days or 91 days or 92 days or 89 days". Worked example in the case: receipt 12.11.2007 → expiry **12.2.2008**. **Engine convention:** `end = trigger_date + n months`, same day-number, clamped to month-end when there is no corresponding day (Dodds v Walker, cited in *Himachal Techno*). Never n×30. | [GL-2], [AR-7] | VERIFIED-SECONDARY (clamp: see CV9) |
| CV5 Years | GCA s.3(66): "year shall mean a year reckoned according to the British calendar". Same corresponding-date convention as CV4. | [GL-2] | VERIFIED-SECONDARY (29-Feb edge: CV9) |
| CV6 Court closure | LA s.4: "Where the prescribed period for any suit, appeal or application expires on a day when the court is closed, the suit, appeal or application may be instituted, preferred or made on the day when the court reopens." Where the LA applies, GCA s.10 is excluded by its proviso. **For s.34 the rollover applies to the 3-month period only, never to the 30-day condonable window** (*My Preferred Transformation* para 35.2–35.4). For non-LA acts done "in any Court or office" under a Central Act (e.g. a written statement), GCA s.10 gives next-open-day rollover. | [GL-1], [GL-2], [AR-9] | VERIFIED-SECONDARY (WS application of GCA s.10: TO VERIFY, CV9) |
| CV7 Condonation | LA s.5 covers "Any appeal or any application" (**not suits**). For special laws, s.29(2) applies ss.4–24 "only in so far as … they are not expressly excluded". "but not thereafter" = express exclusion (*Popular Construction*). | [GL-1], [AR-6] | VERIFIED-SECONDARY |
| CV8 Covid overlay | 15.03.2020–28.02.2022 excluded. Reuse the blueprint overlay [P6-35]. Only matters for historical triggers (e.g. *My Preferred*'s own facts). | blueprint [P6-35] | as blueprint |
| CV9 Edge cases needing legal-engineer sign-off | (i) **Month-end clamp** (e.g. receipt 30.11 → 28/29.02). (ii) **A trigger on the last day of a short month followed by a longer month** (receipt 30.04 → corresponding date **30.07**; a "start 01.05 + 3 months − 1 day" reading gives 31.07). **Policy: emit the earlier date as the action date and show the other as a sensitivity row.** (iii) A 29 February year trigger. (iv) GCA s.10 rollover for the WS 120-day limit. | — | TO VERIFY WITH PARTNER |
| CV10 Calendar | No holidays are hard-coded. Golden vectors give the **raw date before rollover** and name the weekday. Rollover uses P0 `CourtCalendar`. | blueprint 08_P6 §5.5.2 | — |

---

### 3. T-ARB-1: Arbitration invocation notice (received or to be sent)

**event_type vocabulary:** `ARB_REQUEST_SENT`, `ARB_REQUEST_RECEIVED_BY_RESPONDENT` (the s.21 event), `ARB_APPOINTMENT_REQUEST_RECEIVED`, `ARB_TRIBUNAL_CONSTITUTED`, `ARB_ARBITRATOR_NOTICE_OF_APPOINTMENT`, `ARB_AWARE_OF_CHALLENGE_GROUND`.

#### ACA.21.COMMENCEMENT (event definition; drives limitation of the claims)
```yaml
code: ACA.21.COMMENCEMENT
kind: EVENT_DEFINITION            # not a deadline; produces the date against which claim limitation and s.9(2) are tested
trigger_event: ARB_REQUEST_RECEIVED_BY_RESPONDENT   # who proves: claimant (courier POD / AD card / email read-receipt / acknowledgement)
anchors:
  - "ACA s.21: 'Unless otherwise agreed by the parties, the arbitral proceedings in respect of a particular dispute commence on the date
     on which a request for that dispute to be referred to arbitration is received by the respondent.'"      # [AR-1]
  - "ACA s.43(1): 'The Limitation Act, 1963 (36 of 1963), shall apply to arbitrations as it applies to proceedings in Court.'
     s.43(2): '... an arbitration shall be deemed to have commenced on the date referred in section 21.'"   # [AR-1]
  - "ACA s.43(3): where the agreement bars claims unless a step is taken within a contractual time, the Court may extend that time if
     'undue hardship would otherwise be caused'. s.43(4): if an award is set aside, the period from commencement to the setting-aside
     order is excluded for fresh proceedings."   # [AR-1]
case_law:
  - "Regenta Hotels v Hotel Grand Centre Point, 2026 INSC 32, para 23: 'commencement of arbitral proceedings is a statutory event defined
     exclusively under Section 21 ... the respondent's receipt of a request to refer the dispute to arbitration sets the arbitral
     proceedings in motion and no judicial application i.e. whether under Section 9 or Section 11 petition, constitutes commencement.'"  # [AR-19]
verification: VERIFIED-SECONDARY
notes: >
  The claim-limitation test is: is each claim within its Limitation Act article (Arts 14/15/18/19/21/55/113 etc., §9) on the date of
  s.21 RECEIPT? The memo must compute this per claim. "Unless otherwise agreed": institutional rules (e.g. a request filed with an
  institution) can alter the commencement event. Extract the clause; if it does, TO VERIFY WITH PARTNER.
```

#### ACA.11.APPOINT_WAIT_30D (waiting period before the court's appointment power arises)
```yaml
code: ACA.11.APPOINT_WAIT_30D
applies_when: { statute_basis_any: ["wrk_ACA1996#sec-11.ss-4", "wrk_ACA1996#sec-11.ss-5"], appointment_procedure: STATUTORY_DEFAULT }
variants:
  - { id: S11_4a, trigger_event: ARB_APPOINTMENT_REQUEST_RECEIVED, text: "a party fails to appoint an arbitrator within thirty days from the receipt of a request to do so from the other party" }
  - { id: S11_4b, trigger_event: ARB_CO_ARBITRATORS_APPOINTED,    text: "the two appointed arbitrators fail to agree on the third arbitrator within thirty days from the date of their appointment" }
  - { id: S11_5,  trigger_event: ARB_APPOINTMENT_REQUEST_RECEIVED, text: "if the parties fail to agree on the arbitrator within thirty days from receipt of a request by one party from the other party to so agree" }
period: { value: 30, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }   # CV1 ("from"); inter-party act, not a court filing
output: { window_kind: LAST_DATE, label: "Last day for the other side to appoint/agree; s.11 application lies from the next day" }
nature: HARD   # statutory waiting period; the court's power under s.11(4)/(5) arises only on failure within 30 days
anchors:
  - "ACA s.11(4) (2015 text, in force): '... the appointment shall be made, upon request of a party, by the Supreme Court or, as the case may be,
     the High Court or any person or institution designated by such Court'"   # as quoted in Borse Brothers [AR-5]
  - "ACA s.11(5): '... within thirty days from receipt of a request by one party from the other party to so agree ...'"   # [AR-1]
  - "ACA s.11(13) (2015 text, in force): '... an endeavour shall be made to dispose of the matter within a period of sixty days from the date of
     service of notice on the opposite party'"   # [AR-5]  (directory target for the court; not a party deadline)
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-10-01, expect: 2026-10-31 }   # Sat; s.11 application possible from 2026-11-01
  - { trigger: 2027-01-31, expect: 2027-03-02 }   # Tue
notes: >
  (1) Point-in-time: IK's s.11 page shows the UN-NOTIFIED 2019 text ("arbitral institution designated by ..."; 6A omitted; 30-day
  disposal). The in-force text is the 2015 version (C6). s.11(6A) ("confine to the examination of the existence of an arbitration
  agreement") remains on the statute book. Scope of s.11 review: In re Interplay (7J, 13.12.2023) and SBI General v Krish Spinning
  (2024): prima facie existence only [AR-20].
  (2) Under an agreed procedure (s.11(6)), the contract's own time limits govern: extract them as DOCUMENT_STATED deadlines.
  (3) Unilateral appointment clauses: CORE v ECI-SPIC-SMO-MCML (CB, 8.11.2024) [AR-28] must be checked before relying on a
  clause that lets one party appoint (snippet).
```

#### ACA.11.PETITION_LIMIT_ART137 (limitation for a s.11 petition)
```yaml
code: ACA.11.PETITION_LIMIT_ART137
trigger_event: ARB_NOTICE_FAILURE_OR_REFUSAL   # date of refusal, or the day after ACA.11.APPOINT_WAIT_30D expires without appointment (lawyer confirms)
period: { value: 3, unit: YEARS }
computation: { exclude_first_day: true, year_convention: CORRESPONDING_DATE_CLAMP, court_closure_rollover: true }  # CV3, CV5, CV6 (LA s.4)
nature: CONDONABLE   # LA s.5 covers "any application"; whether s.5 is applied to s.11 petitions is TO VERIFY WITH PARTNER
anchors:
  - "LA Sch. Art.137: 'Any other application for which no period of limitation is provided elsewhere in this division. | Three years |
     When the right to apply accrues.'"   # [GL-1]
case_law:
  - "Arif Azim Co. v Aptech Ltd (SC, 1.3.2024), para 56, as quoted in Krish Spinning para 128: 'the limitation period for filing a petition under
     Section 11(6) of the Act, 1996 can only commence once a valid notice invoking arbitration has been sent by the applicant to the other party,
     and there has been a failure or refusal on part of that other party in complying with the requirements mentioned in such notice.'"  # [AR-20],[AR-21]
  - "Krish Spinning para 128: referral court must examine that the s.11(6) application 'is not barred by period of limitation as prescribed
     under Article 137'."  # [AR-20]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-11-01, expect: 2029-11-01 }   # Thu (raw)
  - { trigger: 2026-10-01, expect: 2029-10-01 }   # Mon (raw)
notes: >
  Two limitation questions run separately: (a) limitation of the s.11 PETITION (this rule); (b) limitation of the underlying CLAIMS
  (tested at s.21 receipt; ACA.21.COMMENCEMENT). Krish Spinning confines the referral court to "ex facie" time-barred claims and leaves
  the rest to the tribunal.
```

#### ACA.13.CHALLENGE_15D and ACA.16.JURISDICTION_PLEA (respondent-side windows)
```yaml
code: ACA.13.CHALLENGE_15D
trigger_event: ARB_AWARE_OF_CHALLENGE_GROUND     # constitution of tribunal, or awareness of s.12(3) circumstances; who proves: the challenger
period: { value: 15, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }   # "within fifteen days after"
nature: TO VERIFY WITH PARTNER   # default procedure only ("Failing any agreement"); waiver (s.4) and s.12(5) ineligibility (non-waivable except by express writing) interplay
anchors:
  - "ACA s.13(2): 'Failing any agreement referred to in sub-section (1), a party who intends to challenge an arbitrator shall, within fifteen days
     after becoming aware of the constitution of the arbitral tribunal or after becoming aware of any circumstances referred to in sub-section (3)
     of section 12, send a written statement of the reasons for the challenge to the arbitral tribunal.'"   # as quoted in Borse [AR-5]
verification: VERIFIED-SECONDARY (text) / TO VERIFY (nature)
tests:
  - { trigger: 2026-10-01, expect: 2026-10-16 }
  - { trigger: 2027-01-31, expect: 2027-02-15 }
---
code: ACA.16.JURISDICTION_PLEA
kind: EVENT_BOUND_DEADLINE        # "not later than the submission of the statement of defence"; no date arithmetic
nature: CONDONABLE                # s.16(4): tribunal "may ... admit a later plea if it considers the delay justified" (no cap)
anchors:
  - "ACA s.16(2): 'A plea that the arbitral tribunal does not have jurisdiction shall be raised not later than the submission of the statement of
     defence; however, a party shall not be precluded from raising such a plea merely because that he has appointed, or participated in the
     appointment of, an arbitrator.'"   # [AR-1]
verification: VERIFIED-SECONDARY
```

#### ACA.PRE_ARB.CONTRACT_STEPS (multi-tier clause): PRACTICE
```yaml
code: ACA.PRE_ARB.CONTRACT_STEPS
nature: PRACTICE
kind: DOCUMENT_STATED_DEADLINE     # extracted from the contract with a pdoc anchor (negotiation period, senior-management meeting, mediation)
verification: TO VERIFY WITH PARTNER
notes: >
  The Act prescribes no pre-arbitral step. Whether a contractual pre-arbitral step is mandatory (so that invoking arbitration early is
  premature) or directory turns on clause wording and forum case law (Delhi and Bombay HC decisions diverge; not researched to
  verification here). The engine shows the contract's own periods, labelled "contract-stated, enforceability TO VERIFY", and never
  treats them as statutory.
```

#### Draft output for T-ARB-1
**Strategy memo (claimant sending, or respondent receiving, the invocation):**
1. *Their claims / our claims:* the claims listed in the notice; amounts; contract clauses relied on; the dispute-resolution clause verbatim (seat, venue, institution, number of arbitrators, appointment procedure, pre-arbitral tiers, governing law).
2. *Deadlines block:* the s.21 receipt date (CONFIRMED/ASSUMED); `ACA.11.APPOINT_WAIT_30D` last day; `ACA.11.PETITION_LIMIT_ART137`; per-claim limitation tested at s.21 receipt (§9 articles); `ACA.13.CHALLENGE_15D` once the tribunal is constituted; `ACA.16.JURISDICTION_PLEA` (tied to the statement of defence); contract-stated tiers (PRACTICE). If a s.9 order already exists, `ACA.9.COMMENCE_90D` (§4) must be met **by receipt**, not by dispatch.
3. *Our grounds (respondent):* no arbitration agreement or no privity (group-of-companies doctrine: *Cox & Kings*, CB 2023, to check); claims time-barred at s.21 receipt; pre-arbitral steps not complied with (PRACTICE); dispute outside the clause; arbitrator ineligible (s.12(5), Seventh Schedule); invalid unilateral appointment (*CORE*, 2024); "accord and satisfaction" (*Krish Spinning*: for the tribunal, not the referral court).
4. *Adverse authorities to check:* *In re Interplay* (2023); *Krish Spinning* (2024); *Arif Azim* (2024); *BSNL v Nortel* (2021); *CORE* (2024); *Cox & Kings* (2023). Run AuthorityView on each; all are snippet-level here except *Krish Spinning* and *Arif Azim* para 56.
5. *Evidence checklist:* the signed contract, all amendments and the arbitration clause (original or certified copy: s.8(2) / s.11 practice); proof of dispatch **and receipt** of the notice; reply (if any) and its date; chronology of claim accrual dates (invoices, breach events, acknowledgements: LA ss.18/19); board resolution / authority to invoke.

**Reply skeleton ("Reply to notice invoking arbitration dated __ received on __"):** (1) receipt date and reservation of rights; (2) objections to existence, validity or scope of the arbitration agreement (preserved for s.16); (3) objections to the proposed arbitrator (s.12 disclosure request; s.12(5) ineligibility); (4) counter-nomination, or consent to the sole arbitrator, **within the s.11 window** if strategy requires; (5) time-bar of specific claims (per-claim table); (6) non-compliance with pre-arbitral tiers (if any); (7) counter-claims (s.23(2A)) noted, without prejudice; (8) delivery block.
**Para-wise grid:** `notice_para | claim | accrual_date | limitation_article | time-barred_at_s21? | our response | evidence_id | authority | risk_flag`.

---

### 4. T-ARB-2: s.9 interim relief (and s.17 tribunal measures)

#### ACA.9.COMMENCE_90D
```yaml
code: ACA.9.COMMENCE_90D
applies_when: { statute_basis_any: ["wrk_ACA1996#sec-9.ss-2"], s9_order_before_commencement: true }
trigger_event: S9_ORDER_PRONOUNCED            # date of the interim order (incl. ad-interim); who proves: order sheet
period: { value: 90, unit: DAYS }              # DAYS, not "three months"
computation: { exclude_first_day: true, court_closure_rollover: false }  # CV1; the act required is s.21 RECEIPT by the respondent, not a court filing
output: { window_kind: LAST_DATE, label: "Last day by which the respondent must have RECEIVED the s.21 request (unless court fixed further time)" }
nature: CONDONABLE   # "or within such further time as the Court may determine" (no cap); consequence of default is forum-specific (notes)
anchors:
  - "ACA s.9(2): 'Where, before the commencement of the arbitral proceedings, a Court passes an order for any interim measure of protection under
     sub-section (1), the arbitral proceedings shall be commenced within a period of ninety days from the date of such order or within such
     further time as the Court may determine.'"   # [AR-1], also quoted in Regenta [AR-19]
  - "ACA s.9(3): 'Once the arbitral tribunal has been constituted, the Court shall not entertain an application under sub-section (1), unless the
     Court finds that circumstances exist which may not render the remedy provided under section 17 efficacious.'"  # [AR-1]
case_law:
  - "Regenta Hotels, 2026 INSC 32, para 23 (commencement = s.21 receipt only) and para 26: s.9 'does not provide for the consequences of
     non-compliance with its mandate of commencing arbitral proceedings within ninety days, however, the said vacuum stands statutorily filled
     through Rule 9(4) of the 2001 Rules' (r.9(4): '... if the arbitral proceedings are not initiated within three months from the date of the
     presentation of the Application under Section 9, any interim order granted shall stand vacated without any specific order being passed by
     the Court to that effect'); para 27: 'initiated' in r.9(4) is read as 'commenced' under s.21."   # [AR-19]
verification: VERIFIED-SECONDARY (period, commencement event) / TO VERIFY WITH PARTNER (consequence in the partner's forum)
tests:
  - { trigger: 2024-02-17, expect: 2024-05-17 }   # the Karnataka HC's arithmetic recorded in Regenta para 11 ("ought to have been initiated by 17.05.2024")
  - { trigger: 2026-10-01, expect: 2026-12-30 }   # Wed
notes: >
  (1) Emit a SECOND rule where the forum has a rule like Karnataka r.9(4): `FORUM.ARB_RULES.S9_LAPSE` = 3 MONTHS from PRESENTATION of
  the s.9 application (a different trigger and unit). The earlier of the two is the action date. For the Delhi and Bombay HCs, whether an
  equivalent rule exists, and whether lapse is automatic, is TO VERIFY WITH PARTNER. HCs diverge where no rule exists (snippet [AR-30]).
  (2) Ask the court to fix "further time" in the s.9 order itself if invocation or receipt is uncertain (practice).
  (3) Deemed-service and refusal cases: the s.21 receipt date is contested → `procedural_events.certainty=DEEMED` with alt_dates.
```

#### ACA.17.TRIBUNAL_INTERIM (rule card, no deadline)
```yaml
code: ACA.17.TRIBUNAL_INTERIM
kind: RULE_CARD
anchors:
  - "ACA s.17(1) (as substituted 2015; post-award words omitted by the 2019 Act w.e.f. 30.08.2019): 'A party may, during the arbitral
     proceedings, apply to the arbitral tribunal—' (guardian; interim measures (a)–(e))"   # [AR-1] s.17 page, '[***]' marks the 2019 omission
  - "ACA s.17(2): 'Subject to any orders passed in an appeal under section 37, any order issued by the arbitral tribunal under this section shall be
     deemed to be an order of the Court for all purposes and shall be enforceable under the Code of Civil Procedure, 1908, in the same manner as
     if it were an order of the Court.'"
  - "ACA s.37(2)(b): an appeal lies from a tribunal order 'granting or refusing to grant an interim measure under section 17'."
verification: VERIFIED-SECONDARY
notes: After the award, interim relief lies only from the Court under s.9(1) ("at any time after the making of the arbitral award but before it is enforced").
```

#### Draft output for T-ARB-2
**Strategy memo (applicant or respondent to a s.9):**
1. *Their case:* the relief sought (s.9(1)(ii)(a)–(e)); the urgency pleaded; whether the tribunal is constituted (s.9(3) bar); whether s.17 is efficacious.
2. *Deadlines block:* `ACA.9.COMMENCE_90D` (+ forum lapse rule); the s.21 notice status; `ACA.11.APPOINT_WAIT_30D` if appointment is needed; appeal window against the s.9 order (`ACA.37.*`, §6).
3. *Our grounds (respondent):* no prima facie case or balance of convenience; no arbitration agreement; s.9(3) bar (tribunal constituted, s.17 efficacious); applicant failed to commence within 90 days (lapse under forum rule / *Regenta*); securing an amount without strong prima facie claim (CPC O.XXXVIII r.5 standards are applied by courts: to check).
4. *Adverse authorities to check:* *Regenta* (2026); *Arcelor Mittal Nippon Steel v Essar Bulk Terminal* (2021) on s.9(3) (snippet); forum-specific s.9 decisions.
5. *Evidence checklist:* the arbitration clause; the s.21 notice with **proof of receipt**; documents showing urgency or dissipation; undertaking / security offered.

**Reply skeleton (reply to s.9 petition):** preliminary objections (maintainability; s.9(3); no arbitration agreement; suppression); para-wise reply; prima facie case / balance of convenience / irreparable harm; s.9(2) non-commencement; prayer (dismissal; or, alternatively, conditions: security from the applicant, time-bound commencement).
**Para-wise grid:** `petition_para | averment | admit/deny | our version | evidence_id | authority | relief_impact`.

---

### 5. T-ARB-3: s.34 challenge to an award (either side)

**event_type vocabulary:** `AWARD_SIGNED_COPY_RECEIVED_BY_PARTY`, `S33_REQUEST_DISPOSED`, `S34_PRIOR_NOTICE_SERVED`.

#### ACA.34.SET_ASIDE_3M
```yaml
code: ACA.34.SET_ASIDE_3M
version: 2.0.0                       # supersedes blueprint 1.x: rollover scope corrected (C5)
trigger_event: AWARD_SIGNED_COPY_RECEIVED_BY_PARTY   # or S33_REQUEST_DISPOSED if a s.33 request was made; who proves: the party alleging delay disputes it; keep the AD/POD/email
period: { value: 3, unit: MONTHS }
computation:
  exclude_first_day: true            # LA s.12(1) + GCA s.9 (Himachal Techno para 12; R.K. Transport para 11–13)
  month_convention: CORRESPONDING_DATE_CLAMP_TO_MONTH_END   # CV4; never 90 days
  court_closure_rollover: true       # LA s.4 applies to the 3-month end ONLY (My Preferred para 35.2)
output: { window_kind: LAST_DATE, label: "Last day to file s.34 without condonation" }
nature: CONDONABLE                   # cap: 30 days ("but not thereafter"), see ACA.34.CONDONE_30D
anchors:
  - "ACA s.34(3): 'An application for setting aside may not be made after three months have elapsed from the date on which the party making that
     application had received the arbitral award or, if a request had been made under section 33, from the date on which that request had been
     disposed of by the arbitral tribunal: Provided that if the Court is satisfied that the applicant was prevented by sufficient cause from making
     the application within the said period of three months it may entertain the application within a further period of thirty days, but not
     thereafter.'"   # [AR-1] s.34 page
  - "ACA s.31(5): 'After the arbitral award is made, a signed copy shall be delivered to each party.'"   # [AR-1]
case_law:
  - "Himachal Techno Engineers (2010) 12 SCC 210, para 9: ''three months' mentioned in section 34(3) of the Act refers to a period of 90 days.
     This is erroneous.'; para 12: received 12.11.2007 → 'calculated from 13.11.2007 and would expire on 12.2.2008'; delivery to a peon on a
     holiday is not 'receipt' — 'the date of receipt will have to be the next working day'."   # [AR-7]
  - "R.K. Transport Co v BALCO, 2025 INSC 438 (3.4.2025), para 13: award received 09.04.2022 → 'reckoned from 10.04.2022. This expires on
     09.07.2022', a court holiday; para 14: filing on 11.07.2022, 'the next working day of the court, must be considered as being filed within the
     limitation period'. Para 5: 'the limitation period is 3 calendar months as opposed to 90 days.'"   # [AR-8]
  - "State of West Bengal v Rajpath Contractors (2024) 7 SCC 257, para 8 (quoted in R.K. Transport): received 30-6-2022 → started 1-7-2022 →
     'the last day of the period of three months would be 30-9-2022'."   # [AR-10]
  - "Benarsi Krishna Committee v Karmyogi Shelters (2012) 9 SCC 496: delivery to the party's advocate is not delivery to the party under s.31(5)."  # [AR-27] snippet
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2022-04-09, expect_raw: 2022-07-09, expect_after_rollover: 2022-07-11 }   # Sat holiday → Mon (R.K. Transport, SC-decided)
  - { trigger: 2007-11-12, expect: 2008-02-12 }    # Himachal Techno (SC-decided)
  - { trigger: 2022-06-30, expect: 2022-09-30 }    # Rajpath (SC-decided)
  - { trigger: 2026-11-30, expect_raw: 2027-02-28 }  # Sun → rollover per calendar; month-end clamp (CV9-i: sign-off)
  - { trigger: 2027-01-31, expect: 2027-04-30 }    # clamp (CV9-i)
  - { trigger: 2027-04-30, expect: 2027-07-30, sensitivity: 2027-07-31 }   # CV9-ii: action date = earlier
notes: >
  (1) The trigger is receipt by the PARTY of a SIGNED copy. For a corporate party, which officer received it matters (Union of India v
  Tecco Trichy (2005), unverified). The memo must ask "who received it, when, how".
  (2) A s.33 request resets the start to the date of its disposal. See ACA.33.CORRECTION_30D.
  (3) s.14 LA (bona fide proceedings in the wrong court) can apply to s.34: Consolidated Engineering (2008), as discussed in Borse
  (verified mention); conditions TO VERIFY WITH PARTNER.
```

#### ACA.34.CONDONE_30D
```yaml
code: ACA.34.CONDONE_30D
trigger_event: DERIVED(ACA.34.SET_ASIDE_3M.raw_end)   # chain from the RAW 3-month end, not the rolled-over date (Himachal: 30 days 'calculated from 13.2.2008')
period: { value: 30, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }   # NO rollover: My Preferred para 35.3
output: { window_kind: OUTER_LIMIT, label: "Absolute last day (sufficient cause required); no power to condone beyond" }
nature: HARD
anchors: ["ACA s.34(3) proviso: '... within a further period of thirty days, but not thereafter.'"]   # [AR-1]
case_law:
  - "Union of India v Popular Construction Co (5.10.2001; 2001 Supp(3) SCR 619; (2001) 8 SCC 470): 'the crucial words are 'but not thereafter' ...
     this phrase would amount to an express exclusion within the meaning of Section 29(2) of the Limitation Act, and would therefore bar the
     application of Section 5 of that Act.'"   # [AR-6]
  - "My Preferred Transformation & Hospitality v Faridabad Implements, 2025 INSC 56, para 35.3 (quoted in R.K. Transport): 'The 30-day condonable
     period expiring during the court holidays will not survive and neither Section 4, nor any other provision of the Limitation Act, will inure
     to the benefit of the party'; para 35.4: GCA s.10 excluded."   # [AR-9]
verification: VERIFIED-SECONDARY
tests:
  - { trigger_raw_3m_end: 2008-02-12, expect: 2008-03-13 }   # Himachal Techno para 12 (leap year), SC-decided
  - { trigger_raw_3m_end: 2027-01-01, expect: 2027-01-31 }   # Sun: NO rollover, file by Fri 2027-01-29
notes: The UI must show this as an outer limit with a red "no rollover, no condonation" badge, and propose the last working day before it as the action date.
```

#### ACA.33.CORRECTION_30D
```yaml
code: ACA.33.CORRECTION_30D
trigger_event: AWARD_SIGNED_COPY_RECEIVED_BY_PARTY
period: { value: 30, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }   # request to the tribunal, not a court
nature: TO VERIFY WITH PARTNER   # statutory default "unless another period of time has been agreed upon by the parties"; tribunal's power to entertain a late request is unclear
anchors:
  - "ACA s.33(1): 'Within thirty days from the receipt of the arbitral award, unless another period of time has been agreed upon by the parties—
     (a) a party, with notice to the other party, may request the arbitral tribunal to correct any computation errors, any clerical or
     typographical errors ...; (b) if so agreed by the parties, ... give an interpretation ...'; s.33(4): additional award request 'within thirty
     days from the receipt of the arbitral award'."   # [AR-1]
verification: VERIFIED-SECONDARY (text)
tests: [ { trigger: 2026-10-01, expect: 2026-10-31 }, { trigger: 2027-01-31, expect: 2027-03-02 } ]
notes: Strategic: a genuine s.33 request moves the s.34 start date. A sham request is a known adverse-argument risk (to research).
```

#### ACA.34.PRIOR_NOTICE and ACA.34.DISPOSAL_1Y (directory)
```yaml
code: ACA.34.PRIOR_NOTICE
nature: DIRECTORY
anchors: ["ACA s.34(5): 'An application under this section shall be filed by a party only after issuing a prior notice to the other party and such
           application shall be accompanied by an affidavit by the applicant endorsing compliance with the said requirement.'"]   # [AR-1]
case_law:
  - "State of Bihar v Bihar Rajya Bhumi Vikas Bank Samiti (2018) 9 SCC 472 (s.34(5) directory), para 23 as quoted in SCG Contracts (12.2.2019):
     'unlike Sections 34(5) and (6), if an award is made beyond the stipulated or extended period [s.29A] ... the consequence ... is expressly
     provided. This provision is in stark contrast to Sections 34(5) and (6) where ... if the period for deciding the application under
     Section 34 has elapsed, no consequence is provided.'"   # [CC-5]
verification: VERIFIED-SECONDARY (via SCG quote; Bihar Rajya citation snippet)
notes: Not a deadline. A checklist item: issue the notice and the affidavit anyway.
---
code: ACA.34.DISPOSAL_1Y
nature: DIRECTORY
trigger_event: S34_PRIOR_NOTICE_SERVED
period: { value: 1, unit: YEARS }
anchors: ["ACA s.34(6): '... shall be disposed of expeditiously, and in any event, within a period of one year from the date on which the notice
           referred to in sub-section (5) is served upon the other party.'"]   # [AR-1]
case_law: ["Bihar Rajya para 23 (above)"]
verification: VERIFIED-SECONDARY
notes: Show it as an informational "court target" only, never as a client deadline. No golden vector is needed.
```

#### ACA.36.NO_AUTOMATIC_STAY (rule card)
```yaml
code: ACA.36.NO_AUTOMATIC_STAY
kind: RULE_CARD
anchors:
  - "ACA s.36(2): '... the filing of such an application shall not by itself render that award unenforceable, unless the Court grants an order of
     stay of the operation of the said arbitral award in accordance with the provisions of sub-section (3), on a separate application made for
     that purpose.'"
  - "s.36(3) first proviso: for money awards the Court 'shall ... have due regard to the provisions for grant of stay of a money decree under the
     provisions of the Code of Civil Procedure, 1908'."
  - "s.36(3) second proviso (Act 3 of 2021, w.e.f. 23.10.2015): where a prima facie case is made out that the agreement or contract, or the making
     of the award, 'was induced or effected by fraud or corruption, it shall stay the award unconditionally pending disposal of the challenge'."   # [AR-1]
case_law:
  - "BCCI v Kochi Cricket (15.3.2018): amended s.36 applies to s.34 petitions pending on 23.10.2015 (snippet)."   # [AR-26]
  - "Hindustan Construction Co v Union of India (27.11.2019): s.87 (inserted 2019) struck down (snippet)."   # [AR-26]
verification: VERIFIED-SECONDARY (text) / snippet (cases)
notes: Award-holder memo: enforcement can start once the s.34 time expires (s.36(1)) or, if a s.34 is pending, absent a stay. Award-debtor memo: file a SEPARATE stay application and budget for a deposit or security (CPC O.XLI r.5 standards: to check).
```

#### Draft output for T-ARB-3
**Strategy memo (award-debtor challenging; mirror for award-holder):**
1. *The award:* date; seat; majority/dissent; heads awarded; interest under s.31(7); costs; **receipt facts** (who received the signed copy, when, by what mode).
2. *Deadlines block:* `ACA.34.SET_ASIDE_3M` (raw and rolled-over), `ACA.34.CONDONE_30D` (outer limit, no rollover), `ACA.33.CORRECTION_30D`, enforcement exposure (s.36), the `ACA.37.*` appeal window after the s.34 decision.
3. *Our grounds:* s.34(2)(a) incapacity, invalid agreement, no notice, beyond scope, composition/procedure defect (to be "established on the basis of the record of the arbitral tribunal": 2019 wording, TO VERIFY exact text); s.34(2)(b) non-arbitrability / public policy (Explanation 1–2); s.34(2A) patent illegality (domestic only); limitation of the challenge itself.
4. *Adverse authorities to check:* *Associate Builders v DDA* (2015); *Ssangyong v NHAI* (2019); *Gayatri Balasamy v ISG Novasoft* (CB, 30.4.2025, limited power to modify awards); *Popular Construction*; *My Preferred* (no rollover of the 30 days). Award-holder: *R.K. Transport* if the 3-month end fell on a holiday.
5. *Evidence checklist:* the arbitral record (pleadings, evidence, procedural orders) (s.34(2)(a) "record" requirement); proof of receipt date; s.34(5) notice and affidavit; for a stay, financial capacity documents and the security offered.

**Petition skeleton (s.34):** synopsis and list of dates (with receipt date and computation); jurisdiction (Court as defined in s.2(1)(e); Commercial Court/Division under CCA s.10); limitation paragraph (3 months, s.12(1) LA, s.4 if applicable, or condonation within 30 days with sufficient cause); grounds (each mapped to s.34(2)(a)(i)–(v), (b), (2A)); s.34(5) compliance affidavit; prayer; separate s.36(3) stay application.
**Award-holder reply grid:** `ground | petitioner's contention | record reference | why not within s.34 (no merits review) | authority | risk`.

---

### 6. T-ARB-4: s.37 appeal

#### ACA.37.APPEAL_COMMERCIAL_60D
```yaml
code: ACA.37.APPEAL_COMMERCIAL_60D
applies_when: { dispute_is_commercial: true, specified_value_inr_gte: 300000 }   # CCA s.10 + s.2(1)(i)
trigger_event: ORDER_OR_JUDGMENT_PRONOUNCED
period: { value: 60, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: true, s12_2_copy_time_exclusion: TO_VERIFY }   # CV1/CV3/CV6
nature: CONDONABLE    # LA s.5 applies; condone only "by way of exception and not by way of rule" (Borse para 61); no statutory cap
anchors:
  - "CCA s.13(1): 'Any person aggrieved by the judgment or order of a Commercial Court below the level of a District Judge may appeal to the
     Commercial Appellate Court within a period of sixty days from the date of judgment or order.'"
  - "CCA s.13(1A): 'Any person aggrieved by the judgment or order of a Commercial Court at the level of District Judge exercising original civil
     jurisdiction or, as the case may be, Commercial Division of a High Court may appeal to the Commercial Appellate Division of that High Court
     within a period of sixty days from the date of the judgment or order: Provided that an appeal shall lie from such orders ... that are
     specifically enumerated under Order XLIII ... and section 37 of the Arbitration and Conciliation Act, 1996.'"   # as quoted in Borse [AR-5]
  - "CCA s.2(1)(i): 'Specified Value' ... 'shall not be less than three lakh rupees or such higher value, as may be notified by the Central
     Government.'"   # [AR-5]
  - "ACA s.37(1): appeal lies 'from the following orders (and from no others)': (a) refusing to refer under s.8; (b) granting or refusing any
     measure under s.9; (c) setting aside or refusing to set aside an award under s.34. s.37(2): from tribunal orders (a) accepting a s.16(2)/(3)
     plea; (b) granting or refusing a s.17 measure. s.37(3): 'No second appeal shall lie ... but nothing in this section shall affect or take
     away any right to appeal to the Supreme Court.'"   # [AR-1]
case_law:
  - "Government of Maharashtra v Borse Brothers Engineers (19.3.2021, CA 995/2021; (2021) 6 SCC 460), para 61: 'for appeals filed under section 37
     ... governed by Articles 116 and 117 of the Limitation Act or section 13(1A) of the Commercial Courts Act, a delay beyond 90 days, 30 days or
     60 days, respectively, is to be condoned by way of exception and not by way of rule. In a fit case in which a party has otherwise acted bona
     fide and not in a negligent manner, a short delay beyond such period can, in the discretion of the court, be condoned ...'; para 63:
     131-day delay with 'file-pushing' explanation not condoned."   # [AR-5]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-10-01, expect: 2026-11-30 }   # Mon
  - { trigger: 2027-01-31, expect: 2027-04-01 }   # Thu
notes: >
  (1) Whether LA s.12(2) (exclude the time to obtain a certified copy) applies to CCA s.13 appeals: by Borse's s.29(2) reasoning,
  ss.4–24 apply unless expressly excluded, but I found no authority applying s.12(2) specifically to s.13(1A). TO VERIFY WITH PARTNER.
  Compute WITHOUT the exclusion (conservative) and show the exclusion as a sensitivity row.
  (2) "Specified value" for an arbitration matter: the value of the subject-matter of the arbitration (CCA s.10, s.12). If it is below
  ₹3 lakh, or not a "commercial dispute", use ACA.37.APPEAL_NONCOMM.
```

#### ACA.37.APPEAL_NONCOMM (Art.116 / Art.117)
```yaml
code: ACA.37.APPEAL_NONCOMM
applies_when: { dispute_is_commercial_of_specified_value: false }
variants:
  - { id: ART116A, forum: HIGH_COURT_FROM_SUBORDINATE, period: {value: 90, unit: DAYS} }
  - { id: ART116B, forum: OTHER_COURT,                  period: {value: 30, unit: DAYS} }
  - { id: ART117,  forum: SAME_HIGH_COURT_INTRA_COURT,  period: {value: 30, unit: DAYS} }
trigger_event: ORDER_OR_JUDGMENT_PRONOUNCED
computation: { exclude_first_day: true, court_closure_rollover: true, s12_2_copy_time_exclusion: true }  # LA s.12(2) expressly covers appeals
nature: CONDONABLE   # LA s.5; Borse para 61 (exception, not rule)
anchors:
  - "LA Art.116: 'Under the Code of Civil Procedure, 1908 (5 of 1908),— (a) to a High Court from any decree or order. | Ninety days | The date of
     the decree or order. (b) to any other court from any decree or order. | Thirty days | The date of the decree or order.'"
  - "LA Art.117: 'From a decree or order of any High Court to the same Court. | Thirty days | The date of the decree or order.'"   # [GL-1]
  - "LA s.12(2): exclude 'the day on which the judgment complained of was pronounced and the time requisite for obtaining a copy of the decree,
     sentence or order appealed from'."   # [GL-1]
case_law: ["Borse para 61 (above): Arts 116/117 govern s.37 appeals outside CCA"]   # [AR-5]
verification: VERIFIED-SECONDARY
tests:
  - { variant: ART116A, trigger: 2026-10-01, expect_before_s12_2: 2026-12-30 }
  - { variant: ART116B, trigger: 2026-10-01, expect_before_s12_2: 2026-10-31 }
notes: Which variant applies depends on the forum hierarchy (e.g. District Judge → HC = 116(a); Single Judge → Division Bench = 117). The forum mapping is a P0 court-hierarchy lookup; ask the user if it is ambiguous.
```

#### Draft output for T-ARB-4
**Memo:** (1) the order appealed against and whether it falls in s.37(1)/(2) (else no appeal, only SLP/Art.227: check); (2) the commercial or non-commercial gate (CCA s.2(1)(c), (i)); (3) the deadlines block (`ACA.37.*`, condonation risk per *Borse*); (4) grounds (the s.37 review standard mirrors s.34 limits: no reappraisal of merits; *Gayatri Balasamy* on modification); (5) adverse authorities (*Borse* on delay; *MMTC v Vedanta* (2019) on s.37 scope, unverified); (6) evidence: certified or e-copy of the order, the date of pronouncement, the arbitral record.
**Appeal skeleton:** memo of appeal (synopsis, list of dates with the limitation computation, the impugned order, grounds as numbered propositions, prayer); an application for stay; an application for condonation (only if needed: specific day-by-day explanation; *Borse* rejects "file-pushing").
**Respondent grid:** `ground | appellant's contention | order para | response | authority`.

---

### 7. T-ARB-5: Arbitral timelines (s.23(4) pleadings; s.29A award)

#### ACA.23.PLEADINGS_6M
```yaml
code: ACA.23.PLEADINGS_6M
valid_from: 2019-08-30
trigger_event: ARB_ARBITRATOR_NOTICE_OF_APPOINTMENT   # date the arbitrator (or the LAST of all arbitrators) received written notice of appointment
period: { value: 6, unit: MONTHS }
computation: { exclude_first_day: true, month_convention: CORRESPONDING_DATE_CLAMP_TO_MONTH_END, court_closure_rollover: false }
nature: TO VERIFY WITH PARTNER   # statute gives no consequence; HC commentary treats it as directory (snippet); no SC ruling found
anchors:
  - "ACA s.23(4) (ins. by Act 33 of 2019, in force 30.08.2019): 'The statement of claim and defence under this section shall be completed within a
     period of six months from the date the arbitrator or all the arbitrators, as the case may be, received notice, in writing, of their
     appointment.'"   # [AR-1], [AR-2]
verification: VERIFIED-SECONDARY (text, commencement) / TO VERIFY (nature)
tests:
  - { trigger: 2026-10-01, expect: 2027-04-01 }
  - { trigger: 2026-08-31, expect: 2027-02-28 }   # clamp (CV9-i)
notes: Applies to statement of claim and defence; whether a counter-claim defence or rejoinder is inside "pleadings" for s.29A(1) is fact-specific (Delhi HC view on completion of pleadings: snippet [AR-24]).
```

#### ACA.29A.AWARD_12M (+ consent 6M + court extension)
```yaml
code: ACA.29A.AWARD_12M
valid_from: 2019-08-30            # 12 months from completion of pleadings (pre-30.08.2019: 12 months from tribunal entering upon reference; point-in-time variant)
applies_when: { arbitration_type: DOMESTIC }   # ICA: proviso is "endeavour" only → DIRECTORY variant
trigger_event: ARB_PLEADINGS_COMPLETED
period: { value: 12, unit: MONTHS }
extension:
  - { by: CONSENT_OF_PARTIES, period: {value: 6, unit: MONTHS}, anchor: "s.29A(3)" }
  - { by: COURT, period: null, anchor: "s.29A(4)-(5)", condition: "sufficient cause", timing: "before or after expiry" }
computation: { exclude_first_day: true, month_convention: CORRESPONDING_DATE_CLAMP_TO_MONTH_END, court_closure_rollover: false }
nature: CONDONABLE     # mandate terminates on expiry "unless the Court has, either prior to or after the expiry ... extended the period"; no cap
anchors:
  - "ACA s.29A(1): 'The award in matters other than international commercial arbitration shall be made by the arbitral tribunal within a period of
     twelve months from the date of completion of pleadings under sub-section (4) of section 23: Provided that the award in the matter of
     international commercial arbitration may be made as expeditiously as possible and endeavour may be made to dispose of the matter within a
     period of twelve months ...'"
  - "s.29A(3): 'The parties may, by consent, extend the period specified in sub-section (1) for making award for a further period not exceeding six
     months.'"
  - "s.29A(4): '... the mandate of the arbitrator(s) shall terminate unless the Court has, either prior to or after the expiry of the period so
     specified, extended the period' + provisos: fee reduction 'not exceeding five per cent. for each month of such delay'; 'where an application
     under sub-section (5) is pending, the mandate of the arbitrator shall continue till the disposal of the said application'."
  - "s.29A(5): extension 'may be granted only for sufficient cause and on such terms and conditions as may be imposed by the Court'."   # [AR-1]
case_law:
  - "Rohan Builders v Berger Paints, 2024 INSC 686 (12.9.2024), para 19: 'an application for extension of the time period for passing an arbitral
     award under Section 29A(4) read with Section 29A(5) is maintainable even after the expiry of the twelve-month or the extended six-month
     period'."   # [AR-22]
  - "C. Velusamy v K. Indhera, 2026 INSC 112 (3.2.2026): the Court can entertain a s.29A(5) application even after an 'award' is rendered after
     expiry of the 18 months (para 1 question); para 2: the Court's power is not impaired by an award rendered without a mandate, 'particularly
     when such an award does not partake the character of a decree and is unenforceable under Section 36'; para 13 restates the s.29A scheme
     (Rohan Builders; Lancor Holdings; Jagdeep Chowgule, 2026 INSC 92)."   # [AR-23]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-10-01, expect_12m: 2027-10-01, expect_18m_with_consent: 2028-04-01 }
  - { trigger: 2027-01-31, expect_12m: 2028-01-31, expect_18m_with_consent: 2028-07-31 }
notes: >
  (1) Point-in-time: for references entered upon before 30.08.2019 the trigger was different: TO VERIFY the transitional
  position with the partner before computing old matters.
  (2) The 18-month end is the date to file the s.29A(5) application, but per Rohan Builders it can still be filed after.
  The memo should flag "mandate expired, extension application required" and warn that an award passed in the gap is
  vulnerable (C. Velusamy).
```

#### Draft output for T-ARB-5
**Memo:** a timeline table (appointment notice, s.23(4) six-month mark, pleadings completion, 12-month and 18-month marks, pending s.29A application); the risk if the mandate lapses (an award is unenforceable without extension: *C. Velusamy*); a recommended action (consent extension letter / s.29A(5) application with sufficient cause; fee-reduction exposure for the tribunal); adverse authorities (*Lancor Holdings*, *Jagdeep Chowgule*: to check).
**Skeleton (s.29A(5) application):** procedural history with dates; reasons for delay not attributable to the applicant; period sought; prayer for continuation of mandate (and, where relevant, substitution under s.29A(6)).

---

### 8. T-COM-1: Commercial suit summons received (defendant)

**event_type vocabulary:** `SUMMONS_SERVED_ON_DEFENDANT`, `PLAINT_DOCUMENTS_COMPLETE_RECEIVED` (sensitivity only), `S12A_MEDIATION_APPLICATION`, `S12A_NON_STARTER_REPORT`.

#### CPC.O8R1.COMM_WS_120D
```yaml
code: CPC.O8R1.COMM_WS_120D
applies_when: { suit_is_commercial: true }   # CCA s.2(1)(c) commercial dispute AND specified value ≥ ₹3 lakh AND before Commercial Court/Division
trigger_event: SUMMONS_SERVED_ON_DEFENDANT   # who proves: service report / acknowledgement; the court's record governs
outputs:
  - { id: DAY30,  period: {value: 30,  unit: DAYS}, label: "WS as of right",                  nature: DIRECTORY_WITHIN_OUTER_LIMIT }
  - { id: DAY120, period: {value: 120, unit: DAYS}, label: "Absolute last day; right forfeited after", nature: HARD }
computation:
  exclude_first_day: true                   # "from the date of service" → GCA s.9
  court_closure_rollover: TO_VERIFY         # GCA s.10 text supports next-open-day; no authority found for the 120-day limit (CV9-iv) → action date = raw day
anchors:
  - "CPC O.VIII r.1 proviso (as substituted for commercial disputes by CCA Schedule): 'Provided that where the defendant fails to file the written
     statement within the said period of thirty days, he shall be allowed to file the written statement on such other day, as may be specified by
     the Court, for reasons to be recorded in writing and on payment of such costs as the Court deems fit, but which shall not be later than one
     hundred twenty days from the date of service of summons and on expiry of one hundred twenty days from the date of service of summons, the
     defendant shall forfeit the right to file the written statement and the Court shall not allow the written statement to be taken on record.'"
  - "CPC O.V r.1(1) second proviso: identical 120-day text."
  - "CPC O.VIII r.10 proviso (commercial): 'no Court shall make an order to extend the time provided under Rule 1 of this Order for filing of the
     written statement.'"   # all [CC-1]
case_law:
  - "SCG Contracts (India) v K.S. Chamankar Infrastructure (12.2.2019), (2019) 12 SCC 210, para 8: 'beyond 120 days from the date of service of
     summons, the defendant shall forfeit the right to file the written statement and the Court shall not allow the written statement to be taken
     on record. This is further buttressed by the proviso in Order VIII Rule 10 also adding that the Court has no further power to extend the time
     beyond this period of 120 days.'"   # [CC-5]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-10-01, expect_day30: 2026-10-31, expect_day120: 2027-01-29 }
  - { trigger: 2027-01-31, expect_day30: 2027-03-02, expect_day120: 2027-05-31 }
notes: >
  (1) Days 31–120: leave of court, reasons, costs. The memo must budget for costs and file an application with the WS.
  (2) Commercial pleading rules apply to the WS: O.VIII r.3A (specific denials with reasons; own version; reasons if jurisdiction or valuation is
  disputed); r.5 proviso ("every allegation of fact in the plaint, if not denied in the manner provided under Rule 3A of this Order, shall be
  taken to be admitted"); statement of truth; documents disclosure under O.XI as substituted [CC-1]. These drive the para-wise grid.
  (3) If the contract has an arbitration clause, ACA.8.APPLY_BEFORE_FIRST_STATEMENT must be done FIRST.
  (4) If the suit is a summary suit under O.XXXVII, different short windows apply (LA Art.118: leave to defend 'Ten days | When the summons is
  served' [GL-1]); the O.XXXVII text (as amended for commercial suits) is TO VERIFY. Route to general mode with a red flag.
  (5) Forum rules: Delhi HC (Original Side) Rules 2018 and Commercial Division practice directions may add requirements. TO VERIFY WITH PARTNER.
```

#### CPC.O8R1.NONCOMM_WS (ordinary civil suit, for contrast and for the classifier)
```yaml
code: CPC.O8R1.NONCOMM_WS
applies_when: { suit_is_commercial: false }
trigger_event: SUMMONS_SERVED_ON_DEFENDANT
outputs:
  - { id: DAY30, period: {value: 30, unit: DAYS} }
  - { id: DAY90, period: {value: 90, unit: DAYS} }
computation: { exclude_first_day: true, court_closure_rollover: false }
nature: DIRECTORY
anchors:
  - "CPC O.VIII r.1: 'The defendant shall, within thirty days from the date of service of summons on him, present a written statement of his defence:
     Provided that where the defendant fails to file the written statement within the said period of thirty days, he shall be allowed to file the
     same on such other day, as may be specified by the Court, for reasons to be recorded in writing, but which shall not be later than ninety days
     from the date of service of summons.'"   # as quoted in Kailash [CC-7]
case_law:
  - "Kailash v Nanhku (6.4.2005), (2005) 4 SCC 480: 'We hold that Order VIII Rule 1, though couched in mandatory form, is directory being a provision
     in the domain of processual law'; extension 'only by way of exception and for reasons to be recorded in writing'."   # [CC-7]
  - "Bharat Kalra v Raj Kishan Chabra (SC order, 9.5.2022, CA 3788/2022): suit 'not ... governed by the Commercial Court Act, 2015. Therefore, the time
     limit for filing of the written statement under Order VIII Rule 1 of CPC is not mandatory'; 193-day delay 'could very well be compensated with
     costs'."   # [CC-8]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-10-01, expect_day30: 2026-10-31, expect_day90: 2026-12-30 }
  - { trigger: 2027-01-31, expect_day30: 2027-03-02, expect_day90: 2027-05-01 }
notes: Present day 30 as the action date. Day 90 is a "court leave expected" marker, not a forfeiture. HC original-side rules may be stricter: TO VERIFY WITH PARTNER.
```

#### ACA.8.APPLY_BEFORE_FIRST_STATEMENT
```yaml
code: ACA.8.APPLY_BEFORE_FIRST_STATEMENT
kind: EVENT_BOUND_DEADLINE   # must be filed no later than the first statement on the substance of the dispute (in practice: before or with the WS)
nature: HARD
anchors:
  - "ACA s.8(1): 'A judicial authority, before which an action is brought in a matter which is the subject of an arbitration agreement shall, if a
     party to the arbitration agreement or any person claiming through or under him, so applies not later than the date of submitting his first
     statement on the substance of the dispute, then, notwithstanding any judgment, decree or order of the Supreme Court or any Court, refer the
     parties to arbitration unless it finds that prima facie no valid arbitration agreement exists.'"
  - "s.8(2): application must be accompanied by 'the original arbitration agreement or a duly certified copy thereof' (proviso where the other party retains it)."  # [AR-1]
verification: VERIFIED-SECONDARY
notes: The deadline output is "on or before the WS" and is linked to CPC.O8R1.COMM_WS_120D. A refusal to refer is appealable (s.37(1)(a)) under ACA.37.*. What counts as a "first statement on the substance" (e.g. a reply to an interim application) is TO VERIFY WITH PARTNER: be conservative and file s.8 first.
```

#### CCA.12A.PRE_INSTITUTION_MEDIATION (maintainability check for the defendant)
```yaml
code: CCA.12A.PRE_INSTITUTION_MEDIATION
kind: MAINTAINABILITY_CHECK
applies_when: { suit_is_commercial: true, suit_instituted_on_or_after: 2022-08-20 }   # Patil Automation para 84
checks:
  - "Did the plaintiff exhaust pre-institution mediation (non-starter report or failure report annexed)?"
  - "If not: does the plaint 'contemplate any urgent interim relief'? (genuineness is examinable: Yamini Manohar (Del HC 2023 / SC 2023), unverified)"
  - "If neither → plaint liable to rejection under O.VII r.11 (suo motu power too)."
anchors:
  - "CCA s.12A(1): 'A suit, which does not contemplate any urgent interim relief under this Act, shall not be instituted unless the plaintiff exhausts
     the remedy of pre-institution mediation in accordance with such manner and procedure as may be prescribed by rules made by the Central
     Government.'"
  - "s.12A(3): '... shall complete the process of mediation within a period of three months from the date of application made by the plaintiff under
     sub-section (1): Provided that the period of mediation may be extended for a further period of two months with the consent of the parties:
     Provided further that, the period during which the parties remained occupied with the pre-institution mediation, such period shall not be
     computed for the purpose of limitation under the Limitation Act, 1963.'"   # as quoted in Patil Automation [CC-3]
case_law:
  - "Patil Automation v Rakheja Engineers (17.8.2022), para 84: 'We declare that Section 12A of the Act is mandatory and hold that any suit instituted
     violating the mandate of Section 12A must be visited with rejection of the plaint under Order VII Rule 11. This power can be exercised even suo
     moto by the court ... We, however, make this declaration effective from 20.08.2022 ...'"   # [CC-3]
verification: VERIFIED-SECONDARY
tests: []   # not a computed deadline; the s.12A(3) exclusion is an overlay on the PLAINTIFF's limitation (see notes)
notes: >
  (1) Limitation overlay: for limitation of the plaintiff's suit, exclude the days "occupied with" mediation (an overlay with start = the s.12A
  application, end = the report date). Used when we test whether the suit is time-barred (§9).
  (2) Mediation Act 2023 s.64 + Ninth Schedule (amending s.12A: mediation under that Act; reportedly 120 + 60 days) was NOT notified as of
  14.05.2025 [CC-6]. Status in Oct 2026: TO VERIFY WITH PARTNER (the Mediation Council was established 27.08.2026, which may precede wider commencement).
  (3) Post-2022 SC refinements (Yamini Manohar; Dhanbad Fuels (2025); Novenco v Xero Energy (2025)) are adverse/supportive authorities to check: unverified.
```

#### CCA.SPECIFIED_VALUE (classifier gate)
```yaml
code: CCA.SPECIFIED_VALUE
kind: CLASSIFIER_GATE
anchors: ["CCA s.2(1)(i): 'Specified Value' ... 'which shall not be less than three lakh rupees or such higher value, as may be notified by the Central Government.'"]  # [AR-5]
verification: VERIFIED-SECONDARY (text; threshold since 3.5.2018 per IK footnote to Act 28 of 2018: snippet) / snippet: no higher value notified as of mid-2026 [CC-9]
notes: Gate for CPC.O8R1.COMM_WS_120D vs CPC.O8R1.NONCOMM_WS, for CCA.12A, and for ACA.37.APPEAL_COMMERCIAL_60D. The classifier must also test "commercial dispute" (s.2(1)(c) list, text TO VERIFY) and whether the court is a designated Commercial Court/Division.
```

#### Draft output for T-COM-1
**Strategy memo (defendant):**
1. *Their claims:* the reliefs and amounts; causes of action; valuation; documents relied on (O.XI); whether urgent interim relief is sought; whether the s.12A mediation report is annexed.
2. *Deadlines block:* `CPC.O8R1.COMM_WS_120D` (day 30 / day 120, with the forfeiture badge); `ACA.8.APPLY_BEFORE_FIRST_STATEMENT` (if there is an arbitration clause); reply to the interim application (court-set date: DOCUMENT_STATED); appeal windows for adverse interim orders (`CCA.13`, 60 days); O.XXXVII short windows if it is a summary suit.
3. *Our grounds (preliminary):* rejection of the plaint (O.VII r.11) for s.12A non-compliance (suit after 20.08.2022, no urgent relief); time-bar (§9 articles, with the s.12A(3) exclusion overlay); lack of territorial or pecuniary jurisdiction; not a "commercial dispute" or below specified value (transfer); arbitration clause (s.8); improper valuation.
   *Merits:* contract construction; breach denied; damages not proved (Contract Act ss.73–74: authorities to check); set-off/counter-claim.
4. *Adverse authorities to check:* *SCG Contracts* (no WS after day 120); *Patil Automation* (s.12A mandatory); *Yamini Manohar*; Order XIII-A summary-judgment risk (commercial); *Kailash* (only if the suit is non-commercial).
5. *Evidence checklist:* the summons and **proof of the service date** (envelope, process server's report, e-service log); a complete set of plaint documents (note any missing pages: a sensitivity row); the contract; the correspondence; the s.12A record; a board resolution authorising the WS signatory and the statement of truth; documents for O.XI disclosure (with the WS).

**Written-statement skeleton:** preliminary objections (s.12A / O.VII r.11; s.8 reference *if not already applied*; limitation; jurisdiction under O.VIII r.3A(4); valuation under O.VIII r.3A(5)); para-wise reply; the defendant's own version of events (r.3A(3)); counter-claim/set-off (with court fee); statement of truth; O.XI documents list and declaration.
**Para-wise grid (mandatory, because of the O.VIII r.3A/r.5 deemed-admission rule):** `plaint_para | allegation | ADMIT / DENY / UNABLE_TO_ADMIT_OR_DENY_PUT_TO_PROOF | reason for denial (required) | our version | evidence_id | authority | deemed_admission_risk (auto-flag if blank)`.

---

### 9. T-CON-1: Contract-breach legal notice received

#### CON.NOTICE.REPLY (no statutory deadline)
```yaml
code: CON.NOTICE.REPLY
nature: PRACTICE
kind: DOCUMENT_STATED_DEADLINE    # the period stated in the notice (e.g. "within 15 days"), extracted with a pdoc anchor
verification: VERIFIED-SECONDARY as a negative finding (none of the provisions of the Contract Act, Specific Relief Act, CPC or Limitation Act read for this pack sets a reply period for a private legal notice). The partner should confirm that no sector statute or contract clause applies.
notes: >
  (1) Say this explicitly in the memo: "There is no statutory time limit to reply to this notice. The date shown is the date the
  sender demanded, a PRACTICE deadline. Missing it has no direct legal consequence, but the sender may then sue, invoke
  arbitration, or start a statutory process."
  (2) CLASSIFY FIRST. Some "legal notices" are statutory and carry real clocks; route them to their own rules:
      IBC s.8 demand notice → rules_ibc.md (10 days, HARD);
      cheque-dishonour demand → T-NI-1 (15 days, HARD);
      notice invoking arbitration → T-ARB-1;
      s.12A pre-institution mediation notice from a Legal Services Authority → CCA.12A;
      SRA s.20 substituted-performance notice (as amended 2018: notice "of not less than thirty days" before substituted performance;
        text snippet [CON-1]) → show the stated date and flag that the sender may contract a third party after it and recover costs;
      CPC s.80 (suit against Government; text not verified here) → only if our client is Government (out of corporate scope).
  (3) A drafting caution that the engine must enforce: a reply that admits liability in writing can restart limitation (LA s.18: 'a fresh
  period of limitation shall be computed from the time when the acknowledgment was so signed'), and so can a part-payment (s.19) [GL-1].
  The reply generator must run an "acknowledgment detector" on draft text.
```

#### LA.SUIT_LIMITATION.CONTRACT (the other side's clock; our time-bar defence)
```yaml
code: LA.SUIT_LIMITATION.CONTRACT
kind: LIMITATION_TO_INSTITUTE       # used both to tell the client how long the threat lives and to test time-bar
variants:
  - { id: ART55,  text: "For compensation for the breach of any contract, express or implied not herein specially provided for | Three years | When the contract is broken or (where there are successive breaches) when the breach in respect of which the suit is instituted occurs or (where the breach is continuing) when it ceases." }
  - { id: ART14,  text: "For the price of goods sold and delivered where no fixed period of credit is agreed upon. | Three years | The date of the delivery of the goods." }
  - { id: ART15,  text: "For the price of goods sold and delivered to be paid for after the expiry of a fixed period of credit. | Three years | When the period of credit expires." }
  - { id: ART18,  text: "For the price of work done by the plaintiff for the defendant at his request, where no time has been fixed for payment. | Three years | When the work is done." }
  - { id: ART19,  text: "For money payable for money lent. | Three years | When the loan is made." }
  - { id: ART21,  text: "For money lent under an agreement that it shall be payable on demand. | Three years | When the loan is made." }
  - { id: ART54,  text: "For specific performance of a contract. | Three years | The date fixed for the performance, or, if no such date is fixed, when the plaintiff has notice that performance is refused." }
  - { id: ART113, text: "Any suit for which no period of limitation is provided elsewhere in this Schedule. | Three years | When the right to sue accrues." }
period: { value: 3, unit: YEARS }
computation: { exclude_first_day: true, year_convention: CORRESPONDING_DATE_CLAMP, court_closure_rollover: true }   # CV3, CV5, CV6
nature: HARD            # suits: LA s.5 does not apply ("Any appeal or any application"); s.3 dismissal even if not pleaded
overlays: [LA_S18_ACKNOWLEDGMENT, LA_S19_PART_PAYMENT, CCA_S12A3_MEDIATION_EXCLUSION, LA_S14, COVID_2020_22]
anchors: ["Limitation Act 1963 Schedule Arts 14, 15, 18, 19, 21, 54, 55, 113; ss.3, 5, 12(1), 18, 19"]   # [GL-1]
verification: VERIFIED-SECONDARY (article texts) / TO VERIFY WITH PARTNER (which article fits the facts is a legal judgment: the engine proposes, the lawyer confirms)
tests:
  - { variant: ART55, trigger: 2026-10-01, expect: 2029-10-01 }
  - { variant: ART19, trigger: 2026-11-30, expect: 2029-11-30 }
notes: >
  (1) Article choice drives the start date (delivery vs credit expiry vs breach vs refusal). The memo must show the competing articles
  side by side when facts are ambiguous, and take the earliest end as the conservative "their claim may already be barred" test.
  (2) For arbitration, the same articles apply, measured at s.21 receipt (ACA.21.COMMENCEMENT).
  (3) Leap-day trigger (29 Feb) → CV9-iii.
```

#### Draft output for T-CON-1
**Strategy memo:**
1. *Their claims:* the alleged breach(es) with dates; the amount; reliefs threatened (suit, arbitration, specific performance, termination, substituted performance); the stated reply date.
2. *Deadlines block:* `CON.NOTICE.REPLY` (PRACTICE, from the notice); the sender's limitation per claim (`LA.SUIT_LIMITATION.CONTRACT`, with competing articles); statutory clocks if the notice is statutory (routing table); our own counter-claim limitation.
3. *Our grounds:* no breach / performance tendered; breach by the sender (prior breach, s.39 Contract Act repudiation); force majeure / frustration (s.56); damages remote or unproved (s.73), penalty vs genuine pre-estimate (s.74); time-bar; exclusion and limitation-of-liability clauses; notice and cure clauses not complied with; jurisdiction / arbitration clause.
4. *Adverse authorities to check:* *Kailash Nath Associates v DDA* (2015) on s.74; *ONGC v Saw Pipes* (2003) on liquidated damages (both unverified); the 2018 SRA amendments (specific performance no longer discretionary; s.20 substituted performance: text TO VERIFY).
5. *Evidence checklist:* the contract and its amendments; performance records (delivery challans, completion certificates, acceptance emails); notices and replies; the payment ledger; any **prior acknowledgments** (s.18 risk); board approvals.

**Reply skeleton:** (1) reference and receipt; (2) "without prejudice" and reservation of rights; (3) preliminary objections (no cause of action, time-bar, wrong party, arbitration clause); (4) para-wise denial; (5) our version and counter-allegations (prior breach); (6) counter-claim / demand (if strategic); (7) no admission of liability (run the acknowledgment detector); (8) call for documents; (9) delivery block.
**Para-wise grid:** `notice_para | allegation | admit/deny/not_known | our response | evidence_id | acknowledgment_risk (s.18) | authority`.

---

### 10. T-NI-1: s.138 NI Act notice / complaint (corporate client; drawer side, mirror for payee)

**event_type vocabulary (reuse blueprint):** `CHEQUE_DRAWN`, `CHEQUE_PRESENTED`, `BANK_RETURN_MEMO_RECEIVED_BY_PAYEE`, `DEMAND_NOTICE_SENT`, `NOTICE_RECEIVED_BY_DRAWER` (deemed-service alt_dates), `CAUSE_OF_ACTION_138` (derived), `S143A_ORDER`.

#### NIA.138.PRESENTMENT_VALIDITY
```yaml
code: NIA.138.PRESENTMENT_VALIDITY
kind: CONDITION_PRECEDENT_CHECK
nature: HARD
anchors:
  - "NI Act s.138 proviso (a): 'the cheque has been presented to the bank within a period of six months from the date on which it is drawn or within
     the period of its validity, whichever is earlier'"   # [NI-1]
  - "RBI/2011-12/251, DBOD.AML BC.No.47/14.01.001/2011-12 (4.11.2011): w.e.f. 1.4.2012 banks 'should not make payment of cheques/drafts/pay
     orders/banker's cheques bearing that date or any subsequent date, if they are presented beyond the period of three months from the date of
     such instrument'."   # [NI-3] VERIFIED-PRIMARY
verification: VERIFIED-SECONDARY (s.138) / VERIFIED-PRIMARY (RBI)
tests: []   # no vector: how a bank counts "three months" at month-end is banking practice (CV9) → show the bank's return memo reason instead
notes: Check that the cheque was presented within validity (dates on the cheque vs the presentation date). Post-dated cheques run from the date the cheque bears.
```

#### NIA.138.DEMAND_NOTICE_30D (payee's window; drawer's defence check)
```yaml
code: NIA.138.DEMAND_NOTICE_30D
trigger_event: BANK_RETURN_MEMO_RECEIVED_BY_PAYEE   # who proves: payee (bank memo / intimation date)
period: { value: 30, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }   # CV2 ("of the receipt")
nature: HARD    # condition precedent; s.138 has no condonation for (b)
anchors:
  - "NI Act s.138 proviso (b): 'the payee or the holder in due course of the cheque, as the case may be, makes a demand for the payment of the said
     amount of money by giving a notice in writing, to the drawer of the cheque, within thirty days of the receipt of information by him from the
     bank regarding the return of the cheque as unpaid'"   # [NI-1]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 2026-10-01, expect: 2026-10-31 }
  - { trigger: 2027-01-31, expect: 2027-03-02 }
notes: >
  "Giving" a notice is generally taken as dispatch within 30 days, while receipt can fall later (K. Bhaskaran (1999); C.C. Alavi Haji
  (18.5.2007) on deemed service: snippet [NI-9]). TO VERIFY WITH PARTNER before the engine treats dispatch as sufficient. Notice must
  demand "the said amount" (the cheque amount). Demands that inflate or differ from it are a known invalidity ground (authorities to check).
```

#### NIA.138.PAYMENT_WINDOW (reused from blueprint; now VERIFIED-SECONDARY)
```yaml
code: NIA.138.PAYMENT_WINDOW
trigger_event: NOTICE_RECEIVED_BY_DRAWER    # deemed service → alt_dates (blueprint C6)
period: { value: 15, unit: DAYS }
computation: { exclude_first_day: true, court_closure_rollover: false }
nature: HARD
anchors:
  - "NI Act s.138 proviso (c): 'the drawer of such cheque fails to make the payment of the said amount of money to the payee or, as the case may be,
     to the holder in due course of the cheque, within fifteen days of the receipt of the said notice.' Explanation: 'debt or other liability'
     means a legally enforceable debt or other liability."   # [NI-1]
case_law:
  - "Saketh India v India Securities (10.3.1999), AIR 1999 SC 1090 / (1999) 3 SCC 1: notices served 29.9.1995; 'Period of 15 days, in the present
     case, expired on 14th October, 1995. So cause of action for filing complaint would arise from 15th October, 1995.'"   # [NI-4]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 1995-09-29, expect: 1995-10-14 }   # Saketh (SC-decided)
  - { trigger: 2026-09-10, expect: 2026-09-25 }   # blueprint vector, consistent with Saketh
notes: Corporate drawer: payment by the company within the window prevents the offence for the company AND the s.141 officers. Pay to the payee's account with a traceable reference and send a covering letter.
```

#### NIA.142.COMPLAINT_1M (reused from blueprint; chain from CAUSE_OF_ACTION_138)
```yaml
code: NIA.142.COMPLAINT_1M
trigger_event: CAUSE_OF_ACTION_138        # = day after NIA.138.PAYMENT_WINDOW ends unpaid
period: { value: 1, unit: MONTHS }
computation: { exclude_first_day: true, month_convention: CORRESPONDING_DATE_CLAMP_TO_MONTH_END, court_closure_rollover: true }   # rollover anchor: LA s.4 vs GCA s.10, TO VERIFY which; both give next open day
nature: CONDONABLE   # proviso: cognizance after the period on 'sufficient cause'; no cap
anchors:
  - "NI Act s.142(1)(b): 'such complaint is made within one month of the date on which the cause of action arises under clause (c) of the proviso to
     section 138: Provided that the cognizance of a complaint may be taken by the Court after the prescribed period, if the complainant satisfies the
     Court that he had sufficient cause for not making a complaint within such period.'"
  - "s.142(2): jurisdiction where the payee's bank branch is (cheque delivered for collection through an account) or the drawer's branch (presented otherwise)."  # [NI-1]
case_law: ["Saketh India: CoA 15.10.1995 excluded → complaint on 15.11.1995 'within time'"]   # [NI-4]
verification: VERIFIED-SECONDARY
tests:
  - { trigger: 1995-10-15, expect: 1995-11-15 }   # Saketh (SC-decided)
  - { trigger: 2026-09-26, expect: 2026-10-26 }   # chain from blueprint vector
  - { trigger: 2027-01-31, expect_raw: 2027-02-28 }   # clamp (CV9-i), Sun → rollover per calendar
```

#### NIA.141.COMPANY_OFFICERS (rule card)
```yaml
code: NIA.141.COMPANY_OFFICERS
kind: RULE_CARD
anchors:
  - "NI Act s.141(1): where the offender is a company, 'every person who, at the time the offence was committed, was in charge of, and was responsible
     to the company for the conduct of the business of the company, as well as the company, shall be deemed to be guilty'; first proviso: no
     liability if 'the offence was committed without his knowledge, or that he had exercised all due diligence'; second proviso: Government-nominated
     directors excluded. s.141(2): director/manager/secretary/officer liable on 'consent or connivance' or 'neglect'. Explanation: 'company' includes
     a firm; 'director' of a firm means a partner."   # [NI-1]
verification: VERIFIED-SECONDARY (text) / authorities unverified
notes: Authorities to check (unverified here): SMS Pharmaceuticals v Neeta Bhalla (2005) (specific averments needed); Aneeta Hada v Godfather Travels (2012) (the company must be arraigned); recent SC rulings on non-executive/independent directors. The memo lists each named director with role, date of appointment/resignation and the averments made against them.
```

#### NIA.143A.INTERIM_COMPENSATION and NIA.147 / NIA.148
```yaml
code: NIA.143A.INTERIM_COMPENSATION
trigger_event: S143A_ORDER
outputs:
  - { id: PAY60, period: {value: 60, unit: DAYS}, nature: CONDONABLE, cap: {value: 30, unit: DAYS} }
computation: { exclude_first_day: true, court_closure_rollover: false }
anchors:
  - "NI Act s.143A(1): the court trying a s.138 offence 'may order the drawer of the cheque to pay interim compensation to the complainant— (a) in a
     summary trial or a summons case, where he pleads not guilty ...; and (b) in any other case, upon framing of charge.' (2): 'shall not exceed
     twenty per cent of the amount of the cheque.' (3): 'shall be paid within sixty days from the date of the order under sub-section (1), or within
     such further period not exceeding thirty days as may be directed by the Court on sufficient cause being shown by the drawer of the cheque.'
     (4): repayment with interest on acquittal."   # [NI-2] (Bill text as introduced + consolidated reproduction)
case_law: ["Rakesh Ranjan Shrivastava v State of Jharkhand (2024) 4 SCC 419: s.143A(1) is directory; the court must prima facie evaluate the merits (snippet [NI-5])"]
verification: VERIFIED-SECONDARY (text) / snippet (case, commencement 1.9.2018)
tests:
  - { trigger: 2026-10-01, expect_pay60: 2026-11-30, expect_outer: 2026-12-30 }
  - { trigger: 2027-01-31, expect_pay60: 2027-04-01, expect_outer: 2027-05-01 }
notes: >
  s.147: 'every offence punishable under this Act shall be compoundable' [NI-1]. s.148: appellate court may order a deposit of 'a minimum of
  twenty per cent. of the fine or compensation', within 60 days + up to 30 days (Bill text [NI-2]; enacted text TO VERIFY). Sanjabij Tari v
  Kishore S. Borcar, 2025 INSC 1158 (25.9.2025): guidelines on electronic/dasti service of summons, online payment (QR/UPI) for early
  compounding, and a structured complaint synopsis [NI-6]. The compounding-cost slabs were not confirmed here: TO VERIFY.
```

#### 10.6 Post-1 July 2024 procedure note (minimal; crosswalk flag)
- s.138 complaints are criminal complaints. For complaints **filed on or after 1.7.2024**, procedure is under the **BNSS 2023**. For matters pending before then, **BNSS s.531(2)(a)** saves the CrPC ("shall be disposed of, continued, held or made … in accordance with the provisions of the Code of Criminal Procedure, 1973"): blueprint [P4-49], verified there. NI Act ss.142–147 still override the general code ("Notwithstanding anything contained in the Code of Criminal Procedure, 1973"). Whether those references read as BNSS references is a GCA s.8 / BNSS s.531 question: **TO VERIFY WITH PARTNER**.
- **Contested point → crosswalk needed:** whether the **BNSS s.223(1) proviso** (accused to be heard before cognizance) applies to s.138 complaints. HCs differ (Delhi, Karnataka and J&K decisions reported; snippet [NI-7]). Encode it as `CONTESTED_RULE` (blueprint §5.5.1) with two variants. No deadline depends on it, but it changes the drawer's first procedural opportunity.
- **Recommendation:** W1 needs only the minimal `governing_code()` crosswalk (CrPC↔BNSS for ss.200/202/204/223/531, summons and service). Defer the full crosswalk.

#### Draft output for T-NI-1 (drawer = our corporate client)
**Strategy memo:**
1. *Their claim:* cheque particulars (number, date, amount, bank, signatory); the return reason; dates of the bank memo, notice dispatch and notice receipt; the debt alleged; the persons named (company, directors, signatories).
2. *Deadlines block:* `NIA.138.PAYMENT_WINDOW` (**the most decision-relevant date**: pay and no offence is complete); the derived `CAUSE_OF_ACTION_138`; the payee's `NIA.142.COMPLAINT_1M`; `NIA.138.DEMAND_NOTICE_30D` and `NIA.138.PRESENTMENT_VALIDITY` as defence checks (the engine says so even when they are satisfied, i.e. when they remove a defence); `NIA.143A` exposure if a complaint is filed.
3. *Our grounds:* no legally enforceable debt (security cheque before liability crystallised: authority to check, blueprint *Sampelly*); presumption rebuttal under ss.118/139 (*Rangappa*: to check); notice defects (amount, timing, addressee); presentation beyond validity; stop-payment vs insufficiency; s.141 averments missing for named directors; jurisdiction under s.142(2); complaint time-barred.
4. *Adverse authorities to check:* *Rangappa v Sri Mohan* (2010); *Sampelly Satyanarayana Rao v IREDA* (2016); *Sanjabij Tari* (2025: s.269SS IT Act breach does not make the debt unenforceable; presumptions); *Rakesh Ranjan Shrivastava* (2024); s.141 line of cases.
5. *Evidence checklist:* the cheque copy and return memo; the notice envelope and tracking (receipt date and deemed-service facts); the underlying contract, ledger and invoices; proof of any payment or dispute; board resolutions on signatories; director appointment and resignation filings (MCA DIR-12) for s.141 defences.

**Reply-to-notice skeleton:** reference (cheque, notice dated/received); denial of a legally enforceable debt with facts; circumstances of issue (security/advance, purpose); notice defects; s.141 position of each named officer (role, dates); offer to settle without prejudice or a payment made within the window (with proof); reservation of rights; delivery block.
**Para-wise grid:** `notice_para | allegation | admit/deny | our response | evidence_id | s.141_person_affected | authority`.

---

### 11. Golden-vector index (computation verified; raw dates before rollover unless stated)

| Rule | Input | Expected | Basis |
|---|---|---|---|
| ACA.34.SET_ASIDE_3M | receipt 2022-04-09 | 2022-07-09 (Sat) → filed 2022-07-11 OK | *R.K. Transport* (SC) |
| ACA.34.SET_ASIDE_3M | receipt 2007-11-12 | 2008-02-12 | *Himachal Techno* (SC) |
| ACA.34.SET_ASIDE_3M | receipt 2022-06-30 | 2022-09-30 | *Rajpath* (SC) |
| ACA.34.SET_ASIDE_3M | receipt 2026-11-30 | 2027-02-28 (Sun) | CV4 clamp (CV9 sign-off) |
| ACA.34.SET_ASIDE_3M | receipt 2027-01-31 | 2027-04-30 | CV4 clamp (CV9 sign-off) |
| ACA.34.SET_ASIDE_3M | receipt 2027-04-30 | 2027-07-30 (sensitivity 2027-07-31) | CV9-ii |
| ACA.34.CONDONE_30D | 3-month end 2008-02-12 | 2008-03-13 | *Himachal Techno* (SC) |
| ACA.34.CONDONE_30D | 3-month end 2027-01-01 | 2027-01-31 (Sun, **no rollover**) | *My Preferred* |
| ACA.33.CORRECTION_30D | 2026-10-01 / 2027-01-31 | 2026-10-31 / 2027-03-02 | CV1 |
| ACA.9.COMMENCE_90D | order 2024-02-17 | 2024-05-17 | *Regenta* para 11 (HC arithmetic) |
| ACA.9.COMMENCE_90D | order 2026-10-01 | 2026-12-30 | CV1 |
| ACA.11.APPOINT_WAIT_30D | 2026-10-01 / 2027-01-31 | 2026-10-31 / 2027-03-02 | CV1 |
| ACA.11.PETITION_LIMIT_ART137 | accrual 2026-11-01 | 2029-11-01 | CV5 |
| ACA.13.CHALLENGE_15D | 2026-10-01 / 2027-01-31 | 2026-10-16 / 2027-02-15 | CV1 |
| ACA.23.PLEADINGS_6M | 2026-10-01 / 2026-08-31 | 2027-04-01 / 2027-02-28 | CV4 |
| ACA.29A.AWARD_12M | 2026-10-01 | 12m 2027-10-01; 18m 2028-04-01 | CV4 |
| ACA.37.APPEAL_COMMERCIAL_60D | 2026-10-01 / 2027-01-31 | 2026-11-30 / 2027-04-01 | CV1 |
| ACA.37.APPEAL_NONCOMM | 2026-10-01 (116a / 116b) | 2026-12-30 / 2026-10-31 (before s.12(2)) | CV1 |
| CPC.O8R1.COMM_WS_120D | service 2026-10-01 | d30 2026-10-31; d120 2027-01-29 | CV1 |
| CPC.O8R1.COMM_WS_120D | service 2027-01-31 | d30 2027-03-02; d120 2027-05-31 | CV1 |
| CPC.O8R1.NONCOMM_WS | service 2026-10-01 | d30 2026-10-31; d90 2026-12-30 | CV1 |
| LA.SUIT_LIMITATION.CONTRACT (Art.55) | breach 2026-10-01 | 2029-10-01 | CV5 |
| NIA.138.DEMAND_NOTICE_30D | memo 2026-10-01 / 2027-01-31 | 2026-10-31 / 2027-03-02 | CV2 |
| NIA.138.PAYMENT_WINDOW | receipt 1995-09-29 | 1995-10-14 | *Saketh* (SC) |
| NIA.138.PAYMENT_WINDOW | receipt 2026-09-10 | 2026-09-25 | blueprint; CV2 |
| NIA.142.COMPLAINT_1M | CoA 1995-10-15 | 1995-11-15 | *Saketh* (SC) |
| NIA.142.COMPLAINT_1M | CoA 2026-09-26 | 2026-10-26 | CV2/CV4 |
| NIA.143A | order 2026-10-01 | 2026-11-30; outer 2026-12-30 | CV1 |

---

### 12. General-mode notes (run without a deadline guarantee)

These items have no verified, activatable rule. The engine must label any date as "contract-stated", "court-set" or "lawyer-entered (not computed)":
- **Forum-specific procedural rules**: the partner HC's Original Side Rules and Commercial Division practice directions (WS, replication, O.XI timelines); the s.9 lapse rules (Karnataka-type r.9(4); Delhi/Bombay equivalents unknown); arbitration (proceedings before courts) rules. Lawyer-entered.
- **O.XXXVII summary suits** (commercial): the appearance and leave-to-defend windows. LA Art.118 (10 days) is verified, but the O.XXXVII text is not.
- **s.12(2) LA certified-copy exclusion for CCA s.13 appeals**: shown as sensitivity only.
- **Contract-stated tiers** (negotiation and mediation periods, notice-and-cure periods, SRA s.20 substituted-performance notice periods): extracted as DOCUMENT_STATED. Enforceability is TO VERIFY.
- **Emergency arbitration / institutional rules** (SIAC, ICC, MCIA, DIAC timelines): document- or rules-stated; not in MVP corpus.
- **s.36 enforcement and execution** (CPC O.XXI), **s.48 foreign awards (Part II)**, **international commercial arbitration** under s.29A (endeavour only): rule cards, no deadlines.
- **BNSS-era s.138 procedure** (s.223 pre-cognizance hearing; summons modes per *Sanjabij Tari*): CONTESTED_RULE / informational.
- **Pre-30.08.2019 s.29A matters and pre-23.10.2015 arbitrations**: point-in-time variants not built. Flag "legacy regime: lawyer to confirm".
- **Watchlist (never law)**: the draft Arbitration and Conciliation (Amendment) Bill 2024; commencement of Mediation Act s.64 (s.12A rewrite); any notification raising the CCA specified value.

---

### 13. References

**Arbitration (AR)**
- [AR-1] Arbitration and Conciliation Act 1996, Indian Kanoon section pages. Entire Act (ss.8, 9, 11, 16, 21, 29A): https://indiankanoon.org/doc/1306164/ ; s.17: https://indiankanoon.org/doc/318136/ ; s.23: https://indiankanoon.org/doc/1460737/ ; s.31: https://indiankanoon.org/doc/1769118/ ; s.33: https://indiankanoon.org/doc/1977813/ ; s.34: https://indiankanoon.org/doc/536284/ ; s.36: https://indiankanoon.org/doc/1282684/ ; s.37: https://indiankanoon.org/doc/772406/ ; s.43: https://indiankanoon.org/doc/1724405/ — **verified** (IK consolidation: s.11 page shows un-notified 2019 text; the Entire Act page shows the pre-2015 s.17)
- [AR-2] S.O. 3154(E), 30.08.2019 (commencement of ss.1, 4–9, 11–13, 15 of Act 33 of 2019): SCC Online Blog, 4.9.2019, https://www.scconline.com/blog/post/2019/09/04/enforcement-of-various-provisions-of-the-arbitration-and-conciliation-amendment-act-2019/ — **verified** (secondary); gazette PDF https://egazette.gov.in/WriteReadData/2019/211902.pdf — **unverified** (503/TLS from sandbox)
- [AR-3] Bar & Bench, "Has Section 11(6A) been deleted from the Arbitration Act?" (10.3.2021): "Section 3 of the Amendment Act ... is yet to be notified." https://www.barandbench.com/columns/policy-columns/has-section-116a-been-deleted-from-the-arbitration-act — **verified** (secondary)
- [AR-4] IndiaCorpLaw, "Supreme Court Clarifies the Scope of Section 11" (26.11.2024): s.3 of the 2019 Act (omission of 6A) "not yet been brought into force". https://indiacorplaw.in/2024/11/26/supreme-court-clarifies-the-scope-of-section-11-of-the-arbitration-and-conciliation-act-1996/ — **snippet**
- [AR-5] *Government of Maharashtra v Borse Brothers Engineers & Contractors*, CA 995/2021, 19.3.2021 (quotes in-force s.11(4), s.11(13), s.13(2), CCA ss.2(1)(i), 10, 13(1)/(1A), LA Arts 116–117; para 61). https://indiankanoon.org/doc/197941333/ — **verified**
- [AR-6] *Union of India v Popular Construction Co*, CA 6997/2001, 5.10.2001, 2001 Supp(3) SCR 619. https://indiankanoon.org/doc/487135/ — **verified** ((2001) 8 SCC 470 cite: snippet)
- [AR-7] *State of H.P. v Himachal Techno Engineers*, 26.7.2010, (2010) 12 SCC 210. https://indiankanoon.org/doc/1248572/ — **verified**
- [AR-8] *R.K. Transport Co v Bharat Aluminium Co (BALCO)*, 2025 INSC 438, CA 4763/2025, 3.4.2025. https://indiankanoon.org/doc/20609962/ — **verified**; LiveLaw summary https://www.livelaw.in/amp/supreme-court/s-343-arbitration-act-application-filed-on-next-working-day-after-90-day-period-is-within-limitation-supreme-court-288491 — **verified**
- [AR-9] *My Preferred Transformation & Hospitality v Faridabad Implements*, 2025 INSC 56 (10.1.2025), para 35 as quoted in [AR-8] — **verified** (via quote); JSA Prism Jan 2025 https://www.jsalaw.com/newsletters-and-updates/jsa-prism-dispute-resolution-january-2025-5/ — **snippet**
- [AR-10] *State of West Bengal v Rajpath Contractors & Engineers*, (2024) 7 SCC 257, para 8 as quoted in [AR-8] — **verified** (via quote)
- [AR-19] *Regenta Hotels v Hotel Grand Centre Point*, 2026 INSC 32, 7.1.2026. https://indiankanoon.org/doc/92086946/ — **verified**; Verdictum summary https://www.verdictum.in/court-updates/supreme-court/regenta-hotels-private-limited-v-hotel-grand-centre-point-2026-insc-32-arbitration-1603826 — **verified** (summary)
- [AR-20] *SBI General Insurance v Krish Spinning*, 18.7.2024 (para 128 quoting *Arif Azim* para 56). https://indiankanoon.org/doc/171443079/ — **verified**
- [AR-21] *Arif Azim Co v Aptech Ltd*, 1.3.2024. https://indiankanoon.org/doc/127312055/ — **snippet** (listing; para 56 verified via [AR-20])
- [AR-22] *Rohan Builders (India) v Berger Paints India*, 2024 INSC 686, 12.9.2024. https://indiankanoon.org/doc/110025499/ — **verified**
- [AR-23] *C. Velusamy v K. Indhera*, 2026 INSC 112, 3.2.2026. https://indiankanoon.org/doc/104614449/ — **verified**
- [AR-24] s.23(4) mandatory or directory: LiveLaw article https://livelaw.in/articles/arbitration-conciliation-act-1996-sec-234-mandatory-directory-256476 ; Delhi HC on completion of pleadings https://www.livelaw.in/amp/arbitration-cases/twelve-month-period-for-arbitral-award-begins-from-completion-of-pleadings-not-statement-of-defense-delhi-high-court-269083 — **snippet**
- [AR-25] *Gayatri Balasamy v ISG Novasoft Technologies* (CB, 30.4.2025). https://indiankanoon.org/doc/111751006/ — **snippet** (listing)
- [AR-26] *Hindustan Construction Co v Union of India* (27.11.2019) https://indiankanoon.org/doc/102230863/ ; *BCCI v Kochi Cricket* (15.3.2018) https://indiankanoon.org/doc/64244161/ — **snippet** (listings)
- [AR-27] *Benarsi Krishna Committee v Karmyogi Shelters* (2012) 9 SCC 496: Nishith Desai hotline https://nishithdesai.com/research-and-articles/hotline/dispute-resolution-hotline/new-supreme-court-rules-serve-award-upon-party-not-advocate-5566 — **snippet**
- [AR-28] *Central Organisation for Railway Electrification v ECI-SPIC-SMO-MCML (JV)* (CB, 8.11.2024). https://indiankanoon.org/doc/94564485/ — **snippet** (listing)
- [AR-29] Draft Arbitration and Conciliation (Amendment) Bill 2024, status: GAR, Asia-Pacific Arbitration Review 2027, https://globalarbitrationreview.com/review/the-asia-pacific-arbitration-review/2027/article/indias-2024-arbitration-amendment-bill-the-architecture-of-change ; draft text https://www.scobserver.in/wp-content/uploads/2025/02/2024-Draft-Arbitration-Amendment-Bill.pdf — **snippet**
- [AR-30] s.9(2) consequence divergence: Mondaq, "Section 9(2) and the 90-day limitation" https://www.mondaq.com/india/arbitration-dispute-resolution/1798958/section-92-and-the-90-day-limitation-no-automatic-termination-of-interim-protection — **snippet**

**Commercial courts and CPC (CC)**
- [CC-1] Commercial Courts Act 2015, Schedule (CPC amendments: O.V r.1, O.VI r.3A, O.VIII rr.1, 3A, 5, 10; O.XI). https://indiankanoon.org/doc/24236663/ — **verified** (Schedule text; the body of this IK page is pre-2018 and has no s.12A)
- [CC-3] *Patil Automation v Rakheja Engineers*, 17.8.2022 (s.12A text quoted at para 24; para 84). https://indiankanoon.org/doc/164693074/ — **verified**
- [CC-5] *SCG Contracts (India) v K.S. Chamankar Infrastructure*, 12.2.2019, (2019) 12 SCC 210 (quotes *Bihar Rajya* para 23). https://indiankanoon.org/doc/135625260/ — **verified**
- [CC-6] Mediation Act 2023 s.64 / Ninth Schedule not notified: Mondaq (14.5.2025) https://www.mondaq.com/india/trials-appeals-compensation/1622952/territorial-jurisdiction-for-pre-institution-mediation-under-the-commercial-courts-act-2015 — **verified** (secondary); commencement S.O. 4384(E) of 9.10.2023 (sections listed) — **snippet**; Mediation Council established 27.8.2026: SCC Online https://www.scconline.com/blog/post/2026/08/31/new-mediation-council-of-india-established/ — **verified** (secondary; silent on s.64)
- [CC-7] *Kailash v Nanhku*, 6.4.2005, (2005) 4 SCC 480. https://indiankanoon.org/doc/877414/ — **verified**
- [CC-8] *Bharat Kalra v Raj Kishan Chabra*, SC order 9.5.2022, CA 3788/2022. https://indiankanoon.org/doc/124852403/ — **verified**
- [CC-9] Specified value, no enhancement notified (search result summary, 2026); 2018 Bill text https://prsindia.org/files/bills_acts/bills_parliament/2018/The%20Commercial%20Courts,%20Commercial%20Division%20and%20Commercial%20Appellate%20Division%20of%20High%20Courts%20(Amendment)%20Bill,%202018%20Bill%20Text.pdf — **snippet**
- *Yamini Manohar v T.K.D. Keerthi*; *Dhanbad Fuels v UoI* (2025); *Novenco v Xero Energy* — **unverified** (listings only)

**General (GL)**
- [GL-1] Limitation Act 1963 (ss.3, 4, 5, 12, 18, 19, 29(2); Sch. Arts 14, 15, 18, 19, 21, 54, 55, 113, 116, 117, 118, 137). https://indiankanoon.org/doc/1317393/ — **verified**
- [GL-2] General Clauses Act 1897, ss.3(35), 3(66), 9, 10. https://indiankanoon.org/doc/905940/ ; s.9 https://indiankanoon.org/doc/1353686/ — **verified**
- Blueprint [P6-35] (Covid exclusion order) and [P4-49] (BNSS s.531, https://indiankanoon.org/doc/74791982/) — as tagged in the blueprint

**NI Act (NI)**
- [NI-1] Negotiable Instruments Act 1881, ss.138 (incl. provisos (a)–(c), Explanation), 141, 142, 147. https://indiankanoon.org/doc/1132672/ — **verified** (IK "Entire Act" lacks ss.143A/148)
- [NI-2] s.143A and s.148: Negotiable Instruments (Amendment) Bill 2017 as introduced, https://prsindia.org/files/bills_acts/bills_parliament/2018/Negotiable%20Instruments%20Amendment%20Bill%202017.pdf — **verified** (bill text); consolidated s.143A https://devgan.in//iea/index.php?a=3&q=143A — **verified**; commencement 1.9.2018 — **unverified**
- [NI-3] RBI circular RBI/2011-12/251, DBOD.AML BC.No.47/14.01.001/2011-12, 4.11.2011. https://rbi.org.in/commonman/English/Scripts/Notification.aspx?Id=961 — **verified** (primary)
- [NI-4] *Saketh India Ltd v India Securities Ltd*, 10.3.1999, AIR 1999 SC 1090. https://indiankanoon.org/doc/796212/ — **verified**
- [NI-5] *Rakesh Ranjan Shrivastava v State of Jharkhand* (2024) 4 SCC 419: s.143A directory. Search results; cited in Bombay HC (15.7.2026) https://indiankanoon.org/doc/191387303/ — **snippet**
- [NI-6] *Sanjabij Tari v Kishore S. Borcar*, 2025 INSC 1158, 25.9.2025: IndiaLaw summary https://www.indialaw.in/blog/criminal/sc-issues-guidelines-on-cheque-bounce-cash-loan-cases/ — **verified** (secondary summary)
- [NI-7] BNSS s.223 proviso and s.138 complaints, HC divergence: Delhi HC https://delhihighcourt.nic.in/app/showFileJudgment/SKS18032026CRLMM25512025_181233.pdf ; LiveLaw tag https://livelaw.in/amp/tags/section-223-bnss — **snippet**
- [NI-9] *C.C. Alavi Haji v Palapetty Muhammed*, 18.5.2007. https://indiankanoon.org/doc/272690/ — **snippet** (listing); *K. Bhaskaran v Sankaran Vaidhyan Balan* (1999) — **unverified**

**Contract (CON)**
- [CON-1] Specific Relief (Amendment) Act 2018, s.20 substituted performance (notice "of not less than thirty days"): NLIU CBCL https://cbcl.nliu.ac.in/contemporary-issues/substituted-performance-a-new-perspective-in-specific-relief-amendment-act-2018/ — **snippet**; commencement 1.10.2018: King Stubb & Kasiva https://ksandk.com/md/corporate/specific-relief-amendment-act-2018/ — **verified** (secondary)
