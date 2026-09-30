# 21 — India-Specific Legal Data: Sources, Licensing, Citations, Precedent Rules, Treatment, Criminal-Code Transition, Temporal Law, Languages, Compliance

**Abstract.** This document is the platform's *legal reference layer*. Other phases implement mechanisms. This one fixes the Indian legal facts and rules those mechanisms encode. It covers eight things:
1. What official sources exist and what we may lawfully do with them.
2. How Indian citations are formed and resolved: a formal grammar plus an alias strategy that includes observed neutral-citation formats for 20+ High Courts.
3. The doctrine of precedent as machine rules. P3's doctrine engine can execute these directly (`binding_on_forum`, `AuthorityView` inputs), and every rule cites the case that establishes it. Under spine v1.0 (D16), this registry is the canonical DoctrineRule source for P3's `authority-core`.
4. An Indian treatment vocabulary that beats KeyCite and Shepard's on granularity and honesty.
5. The IPC/CrPC/IEA → BNS/BNSS/BSA transition. This includes a 2026 Supreme Court holding that the unit of transition is the *proceeding*, not the case. That holding forces a spine change.
6. Point-in-time law: commencement, ordinances, state amendments, and the limits of India Code.
7. Multilingual realities.
8. Compliance: DPDP Act and Rules 2025, CERT-In, advocate privilege under BSA, and a May 2026 Delhi High Court right-to-be-forgotten judgment that directly binds legal-database design.

Each legal proposition carries a verified citation with a URL. Where Indian law is unsettled, the doc says so and maps the point to `UNDETERMINED` rather than guessing. The WebSearch budget for this session ran out before this doc began. Research therefore relied on direct fetches of primary sources (mostly Supreme Court and High Court texts on Indian Kanoon, and constitutional and statutory text) and on sources that sibling docs had already verified. Items we could not re-verify are marked *(unverified)*. An independent review (2026-09-30) re-fetched 23 high-stakes sources, corrected five claims, added three authorities and patched India-specific design gaps; see §8.R.

---

## 0. Conventions used in this document

- **Spine v1.0.** This doc conforms to the spine v1.0 decision record (D1–D18). §10.4A gives the disposition of every proposed change (C1–C9) and the renames this doc follows. In summary:
  - MT is a *rendition*, never an Expression;
  - masking is a RedactionOverlay carried on `doc.redacted.v1`;
  - the crosswalk enum in §6.4 is canonical;
  - the rule registry in §4.1 is canonical for P3.
- **Rule IDs.** `rul_IN_<area>_<n>` are doctrine rules for P3's DoctrineRule registry (P3 proposed the `rul_` prefix, 05_P3 §2.4 S3-5, registered in spine v1.0 D12). Per D6/D16, `rul_IN_PREC_*` is the **canonical** doctrine source that P3's `authority-core@semver` library implements. `AuthorityView.binding_basis.rule_ids` cite these IDs. Each rule has:
  - `authority` (anchor-grade citation);
  - `status`: `SETTLED` or `CONTESTED`;
  - `output`: the value it contributes.
- **Evidence tags.** `[IN-n]` points to the reference list. Verified means we fetched and read the relevant passage. Paragraph numbers are given where we read them.
- **Settledness.** A rule marked **CONTESTED** must never yield a definitive answer. P3 returns `UNDETERMINED` or `CAUTION` with `binding_basis.contested=true`, and P10 shows the controversy.

---

## 1. Official data sources: a concise catalogue

02_P0 owns the engineering: crawl cadence, WAF and CAPTCHA handling, WARC capture. This table gives the legal-data view and stays consistent with P0's 2026-09-30 probes. Rows marked ★ are new facts verified for this doc.

| Source | Coverage | Format | Update | Reliability / access (observed) | ToU / legal status | Role in our corpus |
|---|---|---|---|---|---|---|
| **sci.gov.in** (Supreme Court) | Judgments, daily orders, cause lists, case status | PDF | Daily | ★ Returned 200 from our egress on 2026-09-30, where P0 had earlier recorded a 403 (so WAF behaviour is intermittent) [IN-50]. ★ "Latest judgments" links follow `view-pdf/?diary_no={diaryNo}{year}&type=j\|o&order_date=YYYY-MM-DD`, e.g. `diary_no=1462024` = Diary 146/2024 [IN-50]. | Judgments are free to reproduce unless the court prohibits it (s.52(1)(q)(iv)) [IN-1] | Canonical SC source. The diary number gives the stable `SC_DIARY_NO` alias. |
| ★ **sci.gov.in/neutral-citation** | Neutral citation lookup | HTML form (date range) | Live | CAPTCHA-protected form (Securimage-style markup) [IN-49] | As above | Reference only. We derive `NEUTRAL_INSC` from the judgment PDF header, not from the form. |
| **scr.sci.gov.in** (official Supreme Court Reports, which absorbed e-SCR/Digi-SCR per P0) | Reported SC judgments with official headnotes | HTML/PDF | Continuous | CAPTCHA search (P0) | Headnotes are a *Government work* (s.2(k)(iii)) [IN-2]. Official headnotes are court-made, so EBC v Modak does not apply to them, but we still treat headnotes as licensed-display only *(policy choice; no authority found either way)*. | SCR volume/page aliases; official headnote display with attribution |
| **judgments.ecourts.gov.in**, **hcservices**, **services.ecourts** | HC judgments/final orders; district court orders | PDF + metadata | Daily | Securimage/hCaptcha (P0) | s.52(1)(q)(iv); CAPTCHA = access-control signal (§2.4) | Bulk HC/district text via licensed/open mirrors first (AWS CC-BY), live portal for gaps |
| **HC websites** (25 HCs, with permanent benches and circuit benches) | Judgments, cause lists | Heterogeneous | Daily | Varies; some geo-blocked (P0) | Same | Bench-level provenance. ★ The HC ↔ state/UT map is not 1:1. Examples: the Bombay HC covers Maharashtra, Goa, Dadra & Nagar Haveli and Daman & Diu, with benches at Nagpur and Aurangabad and a circuit bench at Kolhapur. The Gauhati HC covers Assam, Arunachal, Mizoram and Nagaland. The P&H HC covers Punjab, Haryana and Chandigarh. The Calcutta HC covers Andaman & Nicobar. The Madras HC covers Puducherry. The Kerala HC covers Lakshadweep. The J&K and Ladakh HC covers two UTs [IN-52]. Drives `binding_on_forum` (§4). |
| **NJDG** (National Judicial Data Grid) | Aggregate pendency and disposal statistics | Dashboard; Open API offered only to government/institutional litigants with departmental keys (P0 §3.1, §5.1, ref P0-12) | Daily | CAPTCHA markers (P0 §5.1) | NDSAP-aligned statistics; API not available to law firms (P0 §5.1; 09_P7 §3.7) | **Not a text source.** Used only for coverage reconciliation (P0 §5.12) and daily-volume estimates (P0 §5.1); an MoU/API application is tracked in P0 §11. *(QC addition: pointer row so the catalogue lists every source the brief names.)* |
| **India Code** | Central and state Acts, subordinate legislation | HTML/PDF | Irregular ("re-typed and updated from time to time", P0) | Front page returned 200 to us; deep links failed from our egress | Acts may be reproduced only *with commentary or other original matter* (s.52(1)(q)(ii)) [IN-1]. See §2.2. | Current consolidated text. It is **not** a point-in-time source (§7). |
| **e-Gazette** (central) + state gazettes | Acts as enacted, ordinances, notifications, commencement orders | PDF | Weekly + extraordinary | Broken TLS chain (P0) | Gazette matter is freely reproducible *except* Acts of a legislature (s.52(1)(q)(i)) [IN-1] | **Primary source for commencement, amendments, ordinances.** It is the backbone of point-in-time law. |
| **MHA new-criminal-laws page** | BNS/BNSS/BSA official texts (PDFs dated 01-04-2024) [IN-44] | PDF | Static | Reachable | Government work | Authoritative text for the crosswalk |
| **NCRB** | "Flyers on New Criminal Laws" archive [IN-45] | ZIP (≈46 MB, 10 PDFs) | Static (Feb 2024) | Reachable (downloaded 2026-09-30) | Government work | ★ **Not a crosswalk.** The archive holds 10 thematic flyers (acid attack, human trafficking, medical professionals, organised crime, proclaimed offender, sexual harassment, snatching, stakeholder-driven reforms, technology, terrorism) [IN-45]. Useful only as spot-check evidence for those themes. |
| **Tribunal portals** (NCLT/NCLAT, ITAT, CESTAT, NGT, CAT, APTEL, SAT, consumer commissions via e-Jagriti) | Orders | PDF/JSON | Daily | Mixed (P0: NCLT robots disallow `/search/`; e-Jagriti JSON API) | s.52(1)(q)(iv) covers "Tribunal or other judicial authority" [IN-1] | Tribunal layer of the hierarchy (§4) |
| **Nyaykosh** (NeGD) | Some laws as Akoma Ntoso XML | XML/REST | Unknown | Not reached (P0/P1) | Government | Optional structured statute seed [IN-71] |
| **AWS Open Data**: Indian HC judgments / Indian SC judgments | ~17.8M HC judgments; SC 1950– (per P0) | PDF + Parquet | Quarterly–daily (inconsistent, P0) | Stable S3 | **CC-BY-4.0** [IN-65] | Bulk backfill. Attribution required. |
| **Indian Kanoon API** | Judgments + statutes + IK metadata | JSON | Live | Paid per call | ToU permit RAG/fine-tuning use with attribution; 1-month termination (P0) [IN-64] | Gap-filler and cross-check. **Never the sole source of metadata** (see §3.6: IK title-parse errors). |
| **Commercial reporters** (SCC/SCC OnLine, AIR, Manupatra, etc.) | Reported judgments + editorial layers | Proprietary | — | Licence only | Editorial additions are copyrighted (EBC v Modak) [IN-3] | **Citation strings only** (facts). No text, headnotes or paragraphing. |

**Catalogue-level conclusions**
1. Every *legal-change* fact (commencement, amendment, ordinance, repeal) must come from the **Gazette**, never from a consolidated text.
2. Every *judgment* must come from a **court-issued copy**. That copy is the only lawful and authentic source of paragraph numbers (§2.3).
3. The HC → territory map is a first-class reference table. Benches and territories change: Andhra Pradesh and Telangana split on 1 Jan 2019, and J&K became J&K + Ladakh [IN-52]. Concrete shape (P3 owns it; `crt_`/`bnc_`/`ter_` prefixes per 05_P3 S3-5):
   ```sql
   CREATE TABLE court_jurisdiction (
     court_id text NOT NULL,              -- crt_… (e.g. Bombay HC)
     bench_id text,                       -- bnc_… (Principal/Nagpur/Aurangabad/Goa/Kolhapur-circuit); NULL = whole court
     territory_code text NOT NULL,        -- ISO 3166-2:IN (e.g. IN-GA) or district code for bench allocation
     role text NOT NULL CHECK (role IN ('SUPERINTENDENCE','SEAT','CIRCUIT')),
     valid_period daterange NOT NULL,     -- legal validity, e.g. [2019-01-01,) for Telangana HC
     recorded_period tstzrange NOT NULL,  -- spine §E transaction time
     source_ref text NOT NULL,            -- gazette / notification anchor
     EXCLUDE USING gist (territory_code WITH =, role WITH =, valid_period WITH &&) WHERE (role = 'SUPERINTENDENCE' AND upper_inf(recorded_period))
   );
   ```
   The exclusion constraint guarantees that `territory_to_hc(t, date)` returns exactly one HC for superintendence at any date.

---

## 2. Legality and licensing

### 2.1 The statutory safe harbour: Copyright Act 1957, s.52(1)(q)–(r)

It is not infringement to reproduce or publish four kinds of material [IN-1]:
- **(q)(i)** "any matter which has been published in any Official Gazette except an Act of a Legislature";
- **(q)(ii)** "any Act of a Legislature subject to the condition that such Act is reproduced or published together with any commentary thereon or any other original matter";
- **(q)(iii)** reports of legislative committees, unless the Government prohibits it;
- **(q)(iv)** "any judgment or order of a court, Tribunal or other judicial authority, unless the reproduction or publication of such judgment or order is prohibited by the court, the Tribunal or other judicial authority".

**s.52(1)(r)** separately permits publishing a *translation in any Indian language* of an Act and rules made under it, but only if the Government has not already published one, or if the Government's version is not available for sale [IN-1].

**s.2(k)** defines "Government work" to include works made or published under the direction or control of any Legislature and any court, tribunal or judicial authority [IN-2]. Without s.52, Acts and judgments would be government-copyright works.

**Design consequences**
1. **Judgments/orders: free**, subject to court prohibition. The prohibition is per document. P0/P1 must capture signals such as "not for publication", in-camera orders and masking directions, and P3 records them as a Work-level `access_restriction` (§2.5, spine change C6).
2. **Acts: conditional.** A bare reproduction of an Act does not literally meet (q)(ii). Our statute view always ships with "original matter": our annotations, point-in-time history, crosswalk and treatment signals. This is a legal requirement, not only a product feature. Bulk *export* of bare statute text (e.g., an API returning only `text`) should carry our annotations or be limited to snippets. *(This is our reading of the text. We found no judgment applying (q)(ii) to a legal database.)* **CONTESTED/untested.**
3. **Gazette notifications, rules and orders: free**, because (q)(i) excludes only "an Act of a Legislature". Ordinances are promulgated in the Gazette but are not "Acts of a Legislature". We treat them as (q)(i) matter *(our reading; unverified)*.
4. **Translations of Acts** that we generate by machine may be published only where s.52(1)(r) conditions hold. Otherwise machine translations of statutes are for internal retrieval use only, and the UI shows the official text (§8).

### 2.2 Commercial reporters: *Eastern Book Company v. D.B. Modak*, (2008) 1 SCC 1

- **Holding.** Copy-editing inputs (cross-references, standardisation, formatting) lack the "minimal degree of creativity" needed for copyright (para 40) [IN-3].
- **But (para 41)** three inputs "have a flavour of minimum amount of creativity" and are protected [IN-3]:
  - "(i) segregating the existing paragraphs in the original text by breaking them into separate paragraphs;
  - (ii) adding internal paragraph numbering within a judgment after providing uniform paragraph numbering to the multiple judgments; and
  - (iii) indicating in the judgment the Judges who have dissented or concurred".
- **Headnotes, footnotes and editorial notes.** The Court did not itself adjudicate these. It left in place the Delhi HC's interim restraint on copying SCC's headnotes, footnotes and editorial notes, and added its own direction that the respondents "shall not use the paragraphs made by the appellants" (para 42) [IN-3]. *(Corrected in independent review: an earlier draft said the Court "upheld protection for headnotes"; the operative text shows an un-challenged interim restraint, which is weaker authority but has the same design consequence: never ingest reporter headnotes.)*

**Consequences** (these tighten P0 §3.4 and P1):
- **Paragraph anchors come only from court-issued copies.** Where the court copy is unnumbered, P1's synthetic `u7` anchors are *our* numbering, never a reporter's (spine §C). We must never align our `u`-numbers to SCC paragraphing, even "for convenience". That alignment would reproduce a protected creative choice.
- **Opinion labels** ("concurring", "partly dissenting") are protected *editorial* inputs when a reporter adds them. Our opinion-role labels (P1 S1 `o{n}` prefix; P3 `opinion_role`) must be derived from the court copy itself (the judge's own "I agree", signature blocks, headings in the original) or from our own model. They must not be imported from a reporter.
- **Pin cites to reporter pages** ("(1978) 1 SCC 248 at 280") are facts we can store. We cannot resolve them to text without the reporter. P1's quote-anchoring approach is the lawful workaround.

### 2.3 Access-control law and terms of use

- The IT Act 2000 s.43 has not been definitively applied to scraping public pages. In Feb 2025 the Government's stated position was that scraping for AI training violates s.43, and experts disputed this (P0 [IN-63]).
- **Rule `rul_IN_ACCESS_1`.** CAPTCHAs, logins and robots disallows are access-control signals. We **never circumvent** them. Where the official portal is gated, we use:
  - (a) open mirrors (CC-BY);
  - (b) the IK API under its ToU;
  - (c) written permission or MoU with the court or NIC (22_roadmap);
  - (d) the firm's own lawful copies (TPL, never promoted to PLC without P9's Privacy Gate).

### 2.4 Third-party datasets

| Dataset | Licence | Allowed use | Obligations |
|---|---|---|---|
| AWS Open Data (Dattam Labs) Indian HC / SC judgments [IN-65] | CC-BY-4.0 (P0) | Any, including commercial | Attribution. Provenance kept per `raw_id`. The maintainers ask users to avoid high-concurrency scraping of the origin (P0). |
| Indian Kanoon API [IN-64] | Contract ToU (P0) | RAG context, fine-tuning; "powered by IKanoon" attribution | 1-month termination risk, so never make IK a single point of failure. Using IK-derived *metadata* (e.g., its "Equivalent citations" lists) to build our alias tables needs **written confirmation** (open question Q2). |
| GODL-India (data.gov.in) | Commercial use with attribution (P0 [IN-66], snippet) | Datasets published under GODL | Attribution |
| Reporter citation tables (SCC/AIR equivalents) | Proprietary | None without licence | Citation *strings appearing inside court judgments* are facts we may harvest (P1 §5.9). Reporter-compiled tables are not. |
| OpenNyAI / IL-TUR / InLegalBERT artefacts | Per-repo licences (P1/P2) | Research and models | Check each licence before production use |

### 2.5 Privacy-driven publication limits (new, binding in Delhi)

- ***Laksh Vir Singh Yadav v. Union of India***, W.P.(C) 1021/2016 & connected matters, Delhi HC (Sachin Datta J.), 29 May 2026 [IN-55].
- **The question.** Whether persons named in judicial records may, under Article 21 informational privacy, obtain **de-indexing** from name-based search and **masking** of identifiers (para 1).
- **The relief.** Granted case by case: acquittals, abated proceedings, private matrimonial disputes. Refused for public figures and recent serious convictions (paras 279–283).
- **Directions.**
  - Search engines must de-index from name-based results (as a Rule 3(1)(d) IT Rules 2021 direction, para 284).
  - **"Indian Kanoon ... is directed to restrict name-based search functionality within its platform in respect of the records of the petitioners ... The judgments and orders shall remain accessible on Indian Kanoon by case number, citation, Court details and date"** (para 285).
  - Masking must be sought from the court that rendered the judgment (para 286).
  - Compliance within **two weeks** (para 284). MeitY must communicate the directions to "all other search engine operators and intermediary platforms operating within the jurisdiction of India" and file a compliance affidavit within four weeks (para 287) [IN-55].
  - **Upload-time duty (para 277).** "Indian Kanoon is directed to put in place appropriate systems at the point of upload, to ensure that in future, the identity of victims of sexual offences are not disclosed." [IN-55]
  - **General principle (iv) of the masking framework** (heading VI of the judgment): a masking order by the concerned court is an order of a court of competent jurisdiction for Rule 3(1)(d), and on receipt "'Indian Kanoon' and other hosts are obliged to disable name-based search functionality on their platform/s in respect of that judgment". Principle (iii): masking operates retrospectively *and* prospectively, i.e. on "any future digitisation or uploading" [IN-55]. **This reaches us directly as an "other host"**, without our being a party.
- **Status.** Single-judge decision. It binds courts and authorities under the Delhi HC's superintendence and is persuasive elsewhere (§4). *Appeal status not verified.* Whether a closed legal-research SaaS is an "intermediary" (IT Act s.2(1)(w)) for PLC content, and so within Rule 3(1)(d), is untested → **CONTESTED**. We comply as if it were (low cost, high downside).

**Design rule `rul_IN_PRIV_1`.** Every Work carries `access_restriction`:
```json
{ "name_search_suppressed": [{"party_ref":{"name_as_printed":"…","spans":[{"anchor_id":"wrk_…/en#hdr","char_range":[0,0]}]},  // v1.0 D16: no ent_ for individuals
                              "basis":"COURT_ORDER",
                              "order_ref":"wrk_…/en#p285","scope":"ALL_TENANTS",
                              "effective_from":"2026-06-12","verified_by":"rvw_…",
                              "order_source_raw_id":"sha256:…"}],
  "masked_expression_required": false,   // v1.0 D16: "a masked rendition (RedactionOverlay) must be applied before display", not a masked expression_key
  "court_prohibition": null,
  "statutory_bar": null }          // "BNS_72" | "POCSO_23" | "JJ_74" (last two unverified) — set by P1 needs_masking
                                   // v1.0 D16: Work.access_restriction is {name_search_suppressed[], masked_expression_required, court_prohibition};
                                   // the statutory basis also travels as RedactionOverlay.legal_basis on doc.redacted.v1
```
- `order_ref` is a spine §C anchor (`{work_id}/{expression_key}#{fragment}`) into the *ordering* judgment. `ent_` (party entity) is a new prefix; see spine change C6. *(v1.0 D16 accepts `ent_` for **recurring institutional parties only**, with no global IDs for individuals. RTBF petitioners are individuals, so they are identified by `party_ref` (name as printed + anchor spans) and not by an `ent_` ID. The same spans go into the RedactionOverlay's `spans[]`.)*
- `basis ∈ {COURT_ORDER, STATUTORY_BAR, SOURCE_REMASKED}`. **A suppression is activated only from a court order we have fetched from an official source** (`order_source_raw_id`), never from an emailed PDF alone. This blocks abuse by a person who forges or overstates an order to bury adverse judgments (red team §10.2).
- **Upload-time gate (para 277 analogue).** P1 runs the `needs_masking` classifier *before* a Work becomes searchable. Sexual-offence and juvenile matters with a positive or uncertain score (≥0.2) are held in `QUARANTINED` display state until masked or cleared by review; the SLA target is 72 h **[NOVEL — unvalidated threshold]**. *(v1.0 D16: the hold is a `doc.redacted.v1` overlay (`kind=MASK_SPANS`, or `SUPPRESS_ALL` when spans are unknown) with `review_state=PENDING_REVIEW`. It is a display state, distinct from P1's `quality.gate=QUARANTINED`.)*
- **One event (v1.0 D16).** Every change to `access_restriction` is published as `doc.redacted.v1` carrying a RedactionOverlay:
  - name-search restriction → `kind=NAME_SEARCH_SUPPRESSED`, `scope=WORK`;
  - court masking order → `MASK_SPANS`, or `COURT_PROHIBITION` for s.52(1)(q)(iv) prohibitions;
  - removal → `SUPPRESS_ALL`.
  
  Each overlay carries `legal_basis{type, ref, anchor_id?}`, `ordered_by`, `effective_at`, `review_state` and a `purge_sla`. The `purge_sla` in 01_master §7.13 is serving 1 h, derived 24 h, replicas at the next bundle, well inside the para 284 two-week compliance. This doc's `basis` values map to `legal_basis.type` as COURT_ORDER → COURT_ORDER, STATUTORY_BAR → STATUTE, SOURCE_REMASKED → SOURCE_TAKEDOWN. The separate `work.access_restricted.v1` event proposed in C6 is folded into `doc.redacted.v1`, while `Work.access_restriction` is kept.
- **Producers and compliance evidence (spine v1.0 D20.3, D19.3).** An RTBF or masking order served on us is entered by ops/legal; a court order captured from an official source is emitted by P0; statutory masking found in parsing is emitted by P1. Every consumer (P1, P2, P3, P4, P5 caches, P7, P8, P9, P10 and replicas; D21.3) acks with `redaction.applied.v1`, and P0's redaction ledger pages on any missed `purge_sla`. The ledger is the record we would file to show compliance within the para 284 window.
- P2 must exclude suppressed party names from the *lexical name field and entity facets*, while case number, citation, court and date retrieval still work.
- P5 must not return the Work for a query whose only match is a suppressed name.
- P10 must not surface the name in digests.
- Statutory anonymity also applies:
  - BNS s.72 (disclosure of identity of victims of certain offences) [IN-41];
  - POCSO and JJ Act analogues *(not re-verified here)*.
  
  This anonymity is enforced at P1 as `needs_masking` detection on sexual-offence and juvenile matters. P1 then emits a `doc.redacted.v1` RedactionOverlay (`kind=MASK_SPANS`, `legal_basis{type: STATUTE, ref: "BNS s.72"}`), and the *masked rendition* becomes the display, index, snippet, export and quote-check default (spine v1.0 D16). No masked `expression_key` is minted, and anchors keep their IDs. (This replaces the earlier proposal of a masked Expression `en.m1`, spine change C8, which v1.0 rejected; §10.4A.)

---
## 3. Citation systems: grammar and resolution

P1 §5.8–5.9 owns the extractor and resolver implementation (`reporters_in.yaml`, calibrated GBM resolver, STUB works). This section supplies the **Indian facts** those components must encode, with a formal grammar and the hazards we verified.

### 3.1 Reporter families and their real-world variants

Indian judgments and databases print the *same* reporter in several syntactic orders. The strings below were copied from Indian Kanoon's "Equivalent citations" lines of judgments we fetched, and from the Wikipedia survey of Indian reporters. There are "over 200 law reports in India – subject-wise and state-wise, authorized and unauthorized" [IN-51].

| Scheme (`identifier_alias.scheme`) | Canonical form | Observed variants (verbatim) | Year semantics | Volume | Source |
|---|---|---|---|---|---|
| `SCC` | `(2008) 1 SCC 1` | `2008 (1) SCC 1`; `1991 SCC (4) 139`; `(2017) 16 SCC 680` | **Publication year** [IN-51] | Yes | [IN-3][IN-14][IN-16] |
| `SCC` (supplementary) | `1992 Supp (2) SCC 239` | — | Publication | Supp n | [IN-51] |
| `SCC` sub-series | `1994 SCC (Cri) 740`; `1991 SCC (L&S) 1213` | — | Publication | none | [IN-51] |
| `SCC_ONLINE` | `2023 SCC OnLine SC 663` | `1958 SCC OnLine SC 81` (retro-numbered old case) | Decision year (retro for old cases) | none | [IN-26][IN-36] |
| `AIR` | `AIR 2008 SC 809` | `AIR 2008 SUPREME COURT 809`; `1962 AIR 1893`; `AIR 2018 SC (CIVIL) 81`; `AIRONLINE 1991 SC 57`; `2008 AIR SCW 49` (weekly) | Year of judgment per [IN-51] (but see Modak below) | none ("AIR does not use a volume-based classification") | [IN-3][IN-21][IN-51] |
| `SCR` | `1963 SCR (3) 338` | `(1991) 3 SCR 64`; `1989 SCR (3) 405`; post-2023 digital SCR `[YYYY] n S.C.R. p` *(unverified)* | Publication | Yes | [IN-21][IN-16][IN-22] |
| `SCALE` | `2007 (14) SCALE 191` | `(1990) 2 Scale 1352` | Publication | Yes | [IN-3][IN-51] |
| `JT` | `(1997) 3 JT 589 (SC)` | `JT (1994) 1 SC 374`; `(2000) 9 JT 110 (SC)` | Publication | Yes | [IN-24][IN-51][IN-17] |
| `CRILJ` | `1984 Cri LJ 289 (SC)` | — | Publication | none | [IN-51] |
| Subject/state reporters (extend) | e.g. `(2000) 113 TAXMAN 470`, `(1992) 87 STC 289`, `1997 LAB. I. C. 1069`, `2017 AAC 2436 (SC)`, `(2016) 1 RECCIVR 429`, `2008 AIHC NOC 873` (a *note of case*, not a full report), `2007 (2) COPYTR 487` | — | Varies | Varies | [IN-3][IN-12][IN-14][IN-16][IN-17] |
| `NJRS` (Income-tax Dept.) | `2009-LL-1021` / `2009-LL-1021-SC` | — | — | — | [IN-51] |
| `NEUTRAL_INSC` | `2023 INSC 1066` | — | Decision year | none | [IN-30][IN-48] |
| `NEUTRAL_HC` | see §3.2 | — | Decision year (retro-assigned too) | none | [IN-54] |
| `SC_DIARY_NO` | `146/2024` | URL form `diary_no=1462024` | Filing year | — | [IN-50] |
| `MANU`, `LIVELAW` | identifier only | — | — | — | *(format unverified here; P1 treats MANU as identifier)* |

**The year trap (verified).** *EBC v. Modak* was decided on **12 Dec 2007** but is reported as `(2008) 1 SCC 1`, `AIR 2008 SC 809` and `2007 (14) SCALE 191` [IN-3]. The cited year can therefore precede *or* follow the decision year, and it differs across reporters for the same case. P1's temporal sanity check (`CITED_AFTER_CITING`) must allow a window of `[decision_year, decision_year+1]` for publication-year reporters. It must key on the **decision date** only for `NEUTRAL_*` and `SCC_ONLINE`.

**Same case, many reports.** SCC main, SCC (Cri)/(L&S) sub-series, AIR, AIR SCW, SCR, SCALE, JT and several state reporters all denote **one Work**. Parallel clusters in court-issued judgments are the lawful harvest source (P1 §5.9).

### 3.2 Neutral citations

**Supreme Court.**
- Announced 23 Feb 2023. It applies to judgments from 1 Jan 2023, and was to be applied retrospectively in phases (2014–2023, then 1950–2014).
- The same report notes that the Delhi and Kerala HCs already ran their own neutral-citation systems [IN-48]. A request by the SC e-Committee that all HCs adopt a *uniform* format is widely reported but is **not** in [IN-48] *(unverified; an earlier draft attributed it to [IN-48])*. The HC table below shows that in practice the formats are not uniform.
- Format: `YYYY INSC N`, e.g. `2023 INSC 1066` (*In re Interplay*, 7 judges, 13 Dec 2023) [IN-30].

**High Courts: the "uniform" format is not uniform.** On 2026-09-30 we sampled HC judgments hosted on Indian Kanoon, one or two per HC, and extracted the neutral citation printed in each judgment [IN-54]. Observed:

| HC | Observed pattern(s) | Notes |
|---|---|---|
| Delhi | `2025:DHC:10348` | First adopter, 17 Oct 2022 (P0/P1) |
| Bombay | `2025:BHC-AS:29961` (Appellate Side), `2025:BHC-OS:19595-DB`, `2026:BHC-OS:11242-DB` (Original Side) | Nagpur/Aurangabad/Goa bench codes *not observed* |
| Allahabad | `2025:AHC:56952-DB`, `2025:AHC-LKO:24631` (Lucknow) | Retro-assigned `2016:AHC:167643` and `2019:AHC:44274-DB` observed |
| Madras | `2023/MHC/4812` (**slash-separated**) | Cited inside an Allahabad HC judgment |
| Kerala | `2025:KER:62117` | — |
| Karnataka | `2025:KHC:1408-DB`, `2024:KHC-K:7531` (Kalaburagi) | Retro `2019:KHC:28061-DB`; Dharwad code not observed |
| Punjab & Haryana | `2025:PHHC:037643-DB` | **Zero-padded** 6 digits |
| Rajasthan | `2026:RJ-JP:37928` (Jaipur), `2025:RJ-JD:19943` (Jodhpur) | Observed **split across a line break** (`2025:RJ-⏎⏎JD:19943`) |
| Madhya Pradesh | `2025:MPHC-JBP:3856`, `2024:MPHC-IND:29476` | Gwalior code not observed |
| Calcutta | `2026:CHC-OS:159` | Appellate side not observed |
| Orissa | `2026:OHC:5-DB` | — |
| Jharkhand | `2025:JHHC:33563-DB`, `2021:JHHC:10505` | — |
| Chhattisgarh | `2025:CGHC:21002` | — |
| Uttarakhand | `2026:UHC:5906` | — |
| Himachal Pradesh | `2025:HHC:33005` | — |
| Gauhati | `2025:GAU-AS:17275` | Code suggests per-state bench suffixes (AS = Assam) *(inference)* |
| J&K and Ladakh | `2026:JKLHC-JMU:1090-DB` | — |
| Tripura / Manipur / Meghalaya | `2026:THC:1120`, `2026:MNHC:129`, `2025:MLHC:531` | — |
| Gujarat, Patna, Telangana, Andhra Pradesh, Sikkim | **not observed in sample** | Must be obtained from HC notifications (P0 task) |

**Normalisation rules (`rul_IN_CIT_*`)**
1. Canonical key is `HCNC|{court_code}|{bench_code?}|{year}|{int(number)}|{bench_type?}`. The number is stripped of zero padding. `bench_type ∈ {DB, FB, ∅}`. In `identifier_alias` this is stored as scheme `NEUTRAL_HC` with value `court_code|bench_code|year|n|bench_type` (spine v1.0 D16); `HCNC|` is only the in-memory key prefix.
2. Whether single-bench and DB numbers share one sequence is **unknown**. The resolver therefore indexes both `…|DB` and the bare key. If both hit different Works, it raises `ALIAS_CONFLICT` for review, and the alias rows take `status=CONFLICT` (01_master §5.4). It never auto-merges (P1 §5.9 rule 3).
3. Slash and colon forms (`2023/MHC/4812` ≡ `2023:MHC:4812`) normalise to the same key.
4. Before matching, remove line breaks and hyphenation inside a candidate span when both sides match the code grammar. This is required by the Rajasthan observation.
5. The neutral-citation year is the **decision year**, including for retro-assigned citations *(inferred from retro examples; verify per HC)*.
6. **The format table is data, not code** (closes 01_master §14.2 Q7 as a design rule; the facts stay open). The table above is shipped as `neutral_hc_formats.yaml` (court code, bench codes, separator, padding, `bench_type` suffixes, `verified_by` source, `status VERIFIED|OBSERVED|UNVERIFIED`) and versioned with `reporters_in.yaml`. For the five unobserved HCs, a generic pattern `YYYY[:/]CODE(-BENCH)?[:/]N(-DB|-FB)?` is accepted with `format_status=UNVERIFIED`. Such aliases keep trust tier T0 (the citation is court-issued) but stay `PENDING`, not `ACTIVE`, until the HC's notification is on file or three independently captured judgments of that HC confirm the parse.

### 3.3 Formal grammar (EBNF, normative for `reporters_in.yaml`)

```ebnf
citation        = neutral_sc | neutral_hc | scc | scc_series | scc_online | air | scr | scale | jt | crilj
                | generic_reporter | njrs | case_number ;
year            = ("19" | "20") digit digit ;
num             = digit { digit } ;
lp = "(" ; rp = ")" ; lb = "[" ; rb = "]" ;
neutral_sc      = year ws "INSC" ws num ;
neutral_hc      = year sep hc_code [ "-" bench_code ] sep num [ "-" ("DB"|"FB") ] ;
sep             = ws? (":" | "/") ws? ;                         (* MHC uses "/" *)
hc_code         = "DHC"|"BHC"|"AHC"|"MHC"|"KER"|"KHC"|"PHHC"|"RJ"|"MPHC"|"CHC"|"OHC"|"JHHC"|"CGHC"
                | "UHC"|"HHC"|"GAU"|"JKLHC"|"THC"|"MNHC"|"MLHC"| hc_code_ext ;   (* table-driven *)
bench_code      = "AS"|"OS"|"LKO"|"K"|"JP"|"JD"|"JBP"|"IND"|"JMU"| bench_code_ext ;
scc             = ( lp year rp ws vol ws "SCC" ws page )                   (* (2008) 1 SCC 1 *)
                | ( year ws lp vol rp ws "SCC" ws page )                   (* 2008 (1) SCC 1 *)
                | ( year ws "SCC" ws lp vol rp ws page )                   (* 1991 SCC (4) 139 *)
                | ( year ws "Supp" ws lp vol rp ws "SCC" ws page ) ;       (* 1992 Supp (2) SCC 239 *)
scc_series      = year ws "SCC" ws lp ("Cri"|"L&S"|"Tax") rp ws page ;
scc_online      = year ws "SCC" ws "OnLine" ws court_abbr ws num ;
air             = ( "AIR" ws year ws air_court ws page )
                | ( year ws "AIR" ws page )                                (* 1962 AIR 1893 = SC *)
                | ( "AIR" ws year ws "SC" ws lp ("CIVIL"|"CRI") rp ws page )
                | ( "AIRONLINE" ws year ws air_court ws page )
                | ( year ws "AIR" ws "SCW" ws page ) ;
air_court       = "SC" | "SUPREME COURT" | state_abbr ;
scr             = ( year ws "SCR" ws lp vol rp ws page ) | ( lp year rp ws vol ws "SCR" ws page )
                | ( lb year rb ws vol ws "S.C.R." ws page ) ;
scale           = ( year ws lp vol rp ws "SCALE" ws page ) | ( lp year rp ws vol ws "Scale" ws page ) ;
jt              = ( lp year rp ws vol ws "JT" ws page ws "(SC)" ) | ( "JT" ws lp year rp ws vol ws "SC" ws page ) ;
crilj           = year ws "Cri" ws "LJ" ws page [ ws "(" court_abbr ")" ] ;
njrs            = year "-LL-" num [ "-" court_abbr ] ;
case_number     = case_type ws ("No." | "Nos.")? ws num [ ws? ("of"|"/") ws? year ] ;   (* per-court case-type gazetteer *)
```

Dots and spaces inside abbreviations (`S.C.C.`, `S C C`, `Cri. L.J.`) and Devanagari numerals and abbreviations are normalised before matching (P1 §5.8).

### 3.4 Resolution strategy (India-specific additions to P1 §5.9)

**Alias trust tiers** stored as `identifier_alias.source` + `confidence`. *(Spine v1.0 D16 promotes the tier to an explicit `identifier_alias.trust_tier` column with exactly these T0–T4 definitions, alongside `status ACTIVE|PENDING|REJECTED|SUPERSEDED`; third-party never overrides T0.)*

| Tier | Source | Examples | Auto-activate? |
|---|---|---|---|
| T0 | Court-issued identifier on the document itself | `2023 INSC 1066` in the SC PDF header; `NC: 2024:KHC-K:7531` in the running header [IN-31]; diary number from the sci.gov.in URL | Yes |
| T1 | Court-issued parallel citations inside judgments (clusters) | "(2017) 16 SCC 680" next to a case name in a later judgment | After ≥3 independent citing documents from ≥2 courts (P1) |
| T2 | Official equivalence tables (SC Equivalent Citation Table, P1 [P1-31]) | SCR ↔ SCC/AIR/JT/SCALE | Yes, if obtained lawfully |
| T3 | Contracted third-party metadata (IK) | "Equivalent citations" lines | Only after legal clearance (Q2). Never the sole source. |
| T4 | Model-inferred (party + date + court matching) | STUB → Work merges | Review if the citing court is SC or a larger HC bench |

**Hazards we verified**
1. **The SC itself cites the commercial SCC OnLine.** Recent SC judgments cite `2023 SCC OnLine SC 663`, `2025 SCC OnLine SC 1221`, `1958 SCC OnLine SC 81` [IN-26][IN-34][IN-36]. We cannot license SCC's concordance, so resolution relies on:
   - T1 clusters;
   - party-name + year matching against our SC registry;
   - for recent cases, the neutral citation printed in the *cited* judgment.
   
   `resolution_basis` must be exposed so P8 can down-weight T4 resolutions.
2. **Case-name ambiguity across generations.** "Kunhayammed" and "Rooplal" titles each return several unrelated judgments [IN-17][IN-23]. Party-name matching must combine court, year and citation context.
3. **Statute-number collisions across the old and new codes** affect *case* resolution too. A pleading citing "u/s 482" in 2025 may mean CrPC 482 (inherent powers, now BNSS 528) or BNSS 482 (anticipatory bail, formerly CrPC 438) [IN-41]. See §6.5.

### 3.5 Third-party metadata is not ground truth (verified examples)

Indian Kanoon mis-parses cause titles:
- A Calcutta HC anticipatory-bail order is titled "**Section 318 Of The Bharatiya Nyaya ... vs In Re: Sadhan Ghosh**" [IN-75].
- A Gauhati HC criminal appeal is titled "**Page No.# 1/35 vs The State Of Assam And Anr**" [IN-39].

IK "Equivalent citations" lines mix full reports with notes of cases (`AIHC NOC`) [IN-3]. **Rule `rul_IN_META_1`:** party, court, date and citation metadata is *triangulated* (P1 §5.4). A third-party field never overrides a T0 field.

---
## 4. The doctrine of precedent as machine rules

P3's doctrine engine computes `binding_on_forum` and feeds `AuthorityView` (05_P3 §2.2–2.3; spine v1.0 D6). AuthorityView is the only input for badges, P5 ranking features and P8 status checks. Its `status` is the 5-valued AuthorityStatus enum. P5 ranks with it; P6/P8 must state it correctly. Below are the rules, each tied to an authority we read. Paragraph numbers refer to the court copy where we saw them.

### 4.1 Rule registry

**Canonical (spine v1.0 D16).** This registry is the canonical DoctrineRule source for P3's `authority-core@semver`.
- P3 stores each rule in `doctrine_rule` with its `authority_anchor_ids` and `contested` flag. It returns both views for CONTESTED rules (D6).
- The registry is `rul_IN_PREC_01..24`, all canonical (D20.8). Earlier decision-record text cited `01..22`; rules 23–24 were added in the independent review (§8.R).
- Every rule ID below is what `AuthorityView.binding_basis.rule_ids` carries.

| Rule ID | Rule | Authority (verified) | Status |
|---|---|---|---|
| `rul_IN_PREC_01` | "The law declared by the Supreme Court shall be binding on all courts within the territory of India." | Art. 141 [IN-4] | SETTLED |
| `rul_IN_PREC_02` | "All authorities, civil and judicial, in the territory of India shall act in aid of the Supreme Court". SC law therefore also governs tribunals and quasi-judicial authorities. | Art. 144 [IN-5] | SETTLED |
| `rul_IN_PREC_03` | The SC is **not** bound by its own decisions: "all Courts" in Art. 141 "must refer to Courts other than the Supreme Court". | *Bengal Immunity Co. v. State of Bihar* (1955) [IN-19] | SETTLED |
| `rul_IN_PREC_04` | A decision of a Bench of **larger strength binds** later Benches of lesser or co-equal strength. | *Central Board of Dawoodi Bohra v. State of Maharashtra*, (2005) 2 SCC 673, proposition (1) [IN-12] | SETTLED |
| `rul_IN_PREC_05` | A lesser Bench **cannot doubt** a larger Bench. It can only request the CJ to place the matter before a larger Bench. A co-equal Bench may doubt, and the matter then goes to a larger Bench. Exceptions: the CJ's roster power, and a larger Bench already seized may reconsider. | *Dawoodi Bohra*, propositions (2)–(3) [IN-12] | SETTLED |
| `rul_IN_PREC_06` | Bench strength = judges on the Bench, **not** the size of the majority. "The majority decision of a Bench of larger strength would prevail over the decision of a Bench of lesser strength, irrespective of the number of Judges constituting the majority." | *Trimurthi Fragrances v. Govt. of NCT of Delhi* (SC, 5-J, 19 Sep 2022), relying on *Jaishri Laxmanrao Patil*, (2021) 8 SCC 1 [IN-13] | SETTLED |
| `rul_IN_PREC_07` | **Per incuriam** covers (a) ignorance of a statutory provision or rule, or (b) a ratio irreconcilable with an earlier co-equal or larger Bench. "An earlier decision of co-equal Bench binds the Bench of same strength." | *National Insurance v. Pranay Sethi*, (2017) 16 SCC 680, para 30 (endorsing *Sundeep Kumar Bafna*, (2014) 16 SCC 623) [IN-14] | SETTLED |
| `rul_IN_PREC_08` | **Sub silentio.** A decision "which is not express and is not founded on reasons nor it proceeds on consideration of issue cannot be deemed to be a law declared to have a binding effect as is contemplated by Article 141". | *State of U.P. v. Synthetics & Chemicals*, (1991) 4 SCC 139 [IN-16] | SETTLED |
| `rul_IN_PREC_09` | HCs must decide on "the law as it stands". A pending **reference to a larger Bench or review** does not suspend a precedent. An HC may not refuse to follow an SC judgment because a later coordinate Bench doubted it. Between **conflicting SC judgments of equal strength, HCs follow the earlier**. | *UT of Ladakh v. J&K National Conference* (SC, 6 Sep 2023), para 35 (following *Pranay Sethi*) [IN-15] | SETTLED |
| `rul_IN_PREC_10` | **SLP dismissal** (speaking or non-speaking) attracts no merger. For a *speaking* dismissal, "the statement of law contained in the order is a declaration of law ... within the meaning of Article 141". For a non-speaking dismissal, nothing is declared. Where an appeal *is* decided, the lower decision **merges** into the superior one. | *Kunhayammed v. State of Kerala*, (2000) 6 SCC 359, conclusions (i), (iv), (v) [IN-17] | SETTLED |
| `rul_IN_PREC_11` | **Curative petitions** lie only on narrow grounds: a natural-justice violation affecting a non-party or unserved party, or undisclosed judicial bias. They require a Senior Advocate's certification. | *Rupa Ashok Hurra v. Ashok Hurra*, (2002) 4 SCC 388 [IN-18] | SETTLED |
| `rul_IN_PREC_12` | **SC obiter** "is expected to be obeyed and followed" ("normally"). | *Sarwan Singh Lamba v. Union of India* (1995) [IN-20] | **CONTESTED** as to strictness (the word "normally") |
| `rul_IN_PREC_13` | HC-declared law binds "authorities or tribunals under its superintendence" (majority per Subba Rao and Mudholkar JJ.). Art. 227 gives each HC superintendence "over all courts and tribunals throughout the territories" in which it exercises jurisdiction. | *East India Commercial Co. v. Collector of Customs*, AIR 1962 SC 1893 [IN-21]; Art. 227 [IN-6] | SETTLED |
| `rul_IN_PREC_14` | **Within an HC**: where a single Judge or Division Bench disagrees with a coordinate Bench, "the matter shall be referred to a larger Bench. It is a subversion of judicial process not to follow this procedure." | *Sundarjas Kanyalal Bhatija v. Collector, Thane*, AIR 1990 SC 261; 1989 SCR (3) 405 [IN-22] | SETTLED |
| `rul_IN_PREC_15` | **Tribunal coordinate Benches** are bound by each other. A disagreeing Bench must refer to a larger Bench. | *S.I. Rooplal v. Lt. Governor* (SC, 14 Dec 1999) [IN-23] | SETTLED |
| `rul_IN_PREC_16` | Decisions of Art. 323A/323B tribunals are "subject to scrutiny before a Division Bench of the High Court within whose jurisdiction the concerned Tribunal falls". Tribunals act as courts of first instance in their fields. | *L. Chandra Kumar v. Union of India*, (1997) 3 SCC 261 [IN-24] | SETTLED. **Which HC governs an all-India tribunal bench is fact-specific → CONTESTED.** |
| `rul_IN_PREC_17` | **Another HC's** decisions are persuasive, not binding. No constitutional provision extends an HC's binding force beyond its territory: Art. 141 is SC-only, and Art. 227 is territorial. | Inference from Arts. 141 and 227 [IN-4][IN-6] and *East India Commercial*'s territorial framing [IN-21] | SETTLED (by inference; no single verified dictum) |
| `rul_IN_PREC_18` | **Prospective overruling** can be applied "only by the highest court of the country, i.e., the Supreme Court". The scope of retroactivity is in its discretion. | *Golak Nath* propositions as quoted in *Somaiya Organics v. State of U.P.* (2001) [IN-25] | SETTLED for the SC. HC attempts → CONTESTED. |
| `rul_IN_PREC_19` | The SC may **mould** retroactivity without declaring prospective overruling. In *MADA v. SAIL*, 2024 INSC 607 (14 Aug 2024) it rejected prospective effect but directed that demands not operate on transactions before 1 Apr 2005, that payment be staggered over 12 years from 1 Apr 2026, and that pre-25-Jul-2024 interest and penalty be waived (paras 24–25). | [IN-26] | SETTLED (as an instance) |
| `rul_IN_PREC_20` | **Stay ≠ quash.** "The stay of operation of an order ... does not mean that the said order has been wiped out from existence". | *Shree Chamundi Mopeds v. Church of South India Trust Assn.* (1992) [IN-27] | SETTLED for orders. **Effect of a stay on a judgment's *precedential* value: CONTESTED** (no authority verified) |
| `rul_IN_PREC_21` | **Multi-opinion judgments.** The ratio is what a majority supports. Opinions may agree in part (e.g., *Krishna Kumar Singh v. State of Bihar* (7 judges, 2017): the majority rejects the "enduring rights" theory of *Bhupendra Kumar Bose* and *T. Venkata Reddy* (both Constitution Benches), and Lokur J. separately says the contrary view "requires to be overruled"; opinions differ on ordinance-laying consequences). | [IN-28] | SETTLED principle, hard extraction |
| `rul_IN_PREC_22` | **Tax canon**: "if two reasonable constructions of a taxing provision are possible that construction which favours the assessee must be adopted". Tribunals often invoke it when non-jurisdictional HCs conflict *(practice, unverified)*. | *CIT v. Vegetable Products* (SC, 1973) [IN-29] | CONTESTED as a *precedent-selection* rule |
| `rul_IN_PREC_23` | **Directions under Art. 142 are not precedent.** Directions that "relax the application of law or exempt the case in hand from the rigour of the law ... do not comprise the ratio decidendi and therefore lose its basic premise of making it a binding precedent". | *State of Punjab v. Rafiq Masih (White Washer)* (SC, 8 Jul 2014) [IN-79] | SETTLED. Detecting *which* part of a judgment is an Art. 142 direction is hard → `law_declared=ART142_DIRECTION` needs HITL. |
| `rul_IN_PREC_24` | **HC order on validity of a Parliamentary Act has all-India effect.** "An order passed on writ petition questioning the constitutionality of a Parliamentary Act whether interim or final keeping in view the provisions contained in Clause (2) of Article 226 ... will have effect throughout the territory of India subject of course to the applicability of the Act." | *Kusum Ingots & Alloys Ltd v. Union of India*, (2004) 6 SCC 254 (28 Apr 2004) [IN-78] | SETTLED as to the *order's effect*. Whether the HC's *reasoning* then binds other HCs is not established by this passage → the reasoning stays PERSUASIVE outside the HC's territory (rul 17); **CONTESTED**. |

### 4.2 `binding_on_forum` decision table

Inputs:
- **A (authority):** `court_level`, `court_id`, `bench_strength`, `decision_date`, and two proposition-level inputs:
  - `law_declared` — the optional P3 Proposition field ratified by spine v1.0 D20.7: `NORMAL | ART142_DIRECTION | EXPRESSLY_NOT_PRECEDENT | CONCESSION_BASED | PER_INCURIAM_DECLARED` (absent = `NORMAL`). `EXPRESSLY_NOT_PRECEDENT` covers orders that say of themselves "shall not be treated as a precedent" (a common SC formula; cue-detected by P1, HITL-confirmed). `PER_INCURIAM_DECLARED` is set only from a `DECLARES_PER_INCURIAM` assertion by a competent Bench, never by our machine.
  - `form` — derived inside `authority-core`, **not** a spine field: `RATIO | OBITER | SUB_SILENTIO | NON_SPEAKING_SLP | NO_MAJORITY`. It comes from P3's graph: OBITER from the proposition's holding type (P1's `OBITER_CANDIDATE` confirmed by P3), SUB_SILENTIO from a `DECLARES_SUB_SILENTIO` assertion (rul 08), NON_SPEAKING_SLP from `DISMISSES_IN_LIMINE` with no reasons (rul 10), NO_MAJORITY from the opinion structure (rul 21). *(Earlier drafts put these values in `law_declared`; D20.7 fixed that enum, so they moved to `form`.)*
- **F (forum):** `court_level`, `court_id`, `bench_strength?`, `territory`, `jurisdictional_hc?`.

Output ∈ `BINDING | PERSUASIVE | NOT_BINDING | UNDETERMINED`, plus `binding_basis.rule_ids[]`.

| # | Authority A | Forum F | Output | Rules |
|---|---|---|---|---|
| 1 | SC, `form=RATIO`, `law_declared=NORMAL` | Any HC, subordinate court, tribunal or authority | **BINDING** | 01, 02 |
| 1a | SC, `law_declared=CONCESSION_BASED` | Any HC, subordinate court, tribunal or authority | **BINDING** + `contested=true` *(treatment of concession-based propositions is not verified in this doc → surfaced as contested)* | 01, 02 |
| 2 | SC, `form=OBITER` | Any non-SC forum | **PERSUASIVE** + `contested=true`; "strongly persuasive" is expressed by `rule_ids ∋ rul_IN_PREC_12` (no `weight` field, D20.7) | 12 |
| 3 | SC, `form ∈ {SUB_SILENTIO, NON_SPEAKING_SLP, NO_MAJORITY}` or `law_declared ∈ {ART142_DIRECTION, EXPRESSLY_NOT_PRECEDENT}` | Any | **NOT_BINDING** (as precedent; the parties remain bound). D20.7: `authority-core` treats ART142_DIRECTION and EXPRESSLY_NOT_PRECEDENT as non-binding precedent from any court | 08, 10, 21, 23 |
| 3b | Any court, `law_declared=PER_INCURIAM_DECLARED` | Any | **NOT_BINDING** | 07 |
| 3a | HC X, `STRIKES_DOWN` / stays a **Parliamentary Act** provision | Any forum in India | Provision validity: `AuthorityView(provision).status=NEGATIVE` (final) or `CAUTION` (interim stay), `territory=ALL_INDIA`. HC X's *reasoning*: row 7 rules apply (PERSUASIVE outside X) | 24, 17 |
| 4 | SC Bench of n judges | SC Bench of m judges | n > m → **BINDING**; n = m → **BINDING** (may doubt and refer); n < m → **PERSUASIVE** | 03–06 |
| 5 | HC X (any Bench) | Court, tribunal or authority under X's superintendence (territory ∈ X's map) | **BINDING** | 13 |
| 6 | HC X, Bench of a | HC X, Bench of f | a > f or a = f → **BINDING** (disagreement → reference); a < f → **PERSUASIVE** | 14 (+04 by analogy) |
| 7 | HC X | HC Y ≠ X, or a forum under Y | **PERSUASIVE** | 17 |
| 8 | HC X | Tribunal, with `jurisdictional_hc = X` | **BINDING** | 13, 16 |
| 9 | HC X | Tribunal with all-India jurisdiction, `jurisdictional_hc` unknown | **UNDETERMINED** (P10 asks the user) | 16 |
| 10 | Tribunal Bench | Coordinate Bench of the same tribunal | **BINDING** | 15 |
| 11 | Appellate tribunal (e.g. NCLAT) | Tribunal below it (e.g. NCLT) | **BINDING** *(structural inference; no authority verified)* | — |
| 12 | Any tribunal or district court | HC/SC | **PERSUASIVE** (tribunal) / **NOT_BINDING** (trial court) | — |
| 13 | Any | Forum unknown | **UNDETERMINED** (P3 S3-2) | — |

**Conflict resolution among BINDING authorities.** Apply these in order, and record the result as `binding_basis.conflict = LARGER_BENCH | EARLIER_COEQUAL | UNRESOLVED`:
1. The larger Bench wins (rul 04, 06).
2. Between equal strength, the **earlier** wins (rul 07, 09).
3. A proposition **declared** per incuriam by a competent Bench is NOT_BINDING (via a `DECLARES_PER_INCURIAM` assertion).

**Our own machine must never declare anything per incuriam.** A detected irreconcilability yields `CAUTION` + `reason_code=POSSIBLE_PER_INCURIAM`, and is shown as an argument, not a status.

**Status modifiers** (P3 `AuthorityView.status`, applied after binding is computed; v1.0 D6):
- A pending reference or review does **not** change binding (rul 09). P10 shows it as an informational chip (v1.0: listed in `EvidenceBundle.coverage.per_issue.pending_references[]`, not in `status`).
- A plausible but unverified negative signal is shown as `CAUTION` + `definitive=false` + `reason_code=NEGATIVE_SIGNAL_UNDER_REVIEW` until tier-1 HITL (D6). `NEGATIVE_SIGNAL_UNDER_REVIEW` is a reason code, not a status value.
- A coverage gap adds `reason_code=COVERAGE_GAP` and sets `definitive=false` **without changing the status** (spine v1.0 D20.12, refining D6). Only when the gap exceeds the per-source threshold (default 72 h for HOT sources, 7 days for WARM/COOL sources that can bind the forum) does a GOOD status degrade to `UNKNOWN`. A negative status never loses its value on a gap. P10 shows "status current to <law_current_to>". A "pronounced, text awaited" judgment (`judgment.expected.v1`) is expressed through reason codes (P3 owns the authority reason-code registry, D21.8; 01_master R-29 proposes `TEXT_AWAITED`), never as a status value.
- `STAYED` → `CAUTION` (rul 20).
- `OVERRULES` with `effect=PROSPECTIVE|MOULDED` → the P3 date semantics apply (05_P3 §2.3), with conditions carried as anchored qualifiers (rul 18, 19).

```python
def binding_on_forum(A: AuthorityRef, F: Forum, prop: Proposition|None) -> Binding:
    if F is None or F.court_id is None: return UNDETERMINED(rule="PREC_13_FORUM_UNKNOWN")
    ld   = (prop.law_declared if prop and prop.law_declared else "NORMAL")   # D20.7 enum
    form = (prop.form if prop else "RATIO")                                   # authority-core internal, see Inputs
    if ld == "PER_INCURIAM_DECLARED": return NOT_BINDING(["PREC_07"])
    if ld in {"ART142_DIRECTION","EXPRESSLY_NOT_PRECEDENT"}: return NOT_BINDING(["PREC_23"])   # D20.7: any court
    if A.level == "SC":
        if form in {"SUB_SILENTIO","NON_SPEAKING_SLP","NO_MAJORITY"}:
            return NOT_BINDING(["PREC_08","PREC_10","PREC_21"])
        if F.level == "SC":
            if A.bench is None or F.bench is None: return UNDETERMINED(["PREC_04"])
            return BINDING(["PREC_04","PREC_06"]) if A.bench >= F.bench else PERSUASIVE(["PREC_03"])
        if form == "OBITER": return PERSUASIVE(["PREC_12"], contested=True)
        return BINDING(["PREC_01","PREC_02"], contested=(ld == "CONCESSION_BASED"))
    if A.level == "HC":
        hc_of_forum = F.court_id if F.level == "HC" else (F.jurisdictional_hc or territory_to_hc(F.territory, at=F.date))
        if hc_of_forum is None: return UNDETERMINED(["PREC_16"])
        if hc_of_forum != A.court_id: return PERSUASIVE(["PREC_17"])
        if F.level == "HC":
            if A.bench is None or F.bench is None: return UNDETERMINED(["PREC_14"])
            return BINDING(["PREC_14"]) if A.bench >= F.bench else PERSUASIVE(["PREC_14"])
        return BINDING(["PREC_13","PREC_16"])
    if A.level.startswith("TRIBUNAL"):
        if same_tribunal(A, F) and A.bench >= (F.bench or 0): return BINDING(["PREC_15"])
        if is_appellate_over(A, F): return BINDING(["STRUCTURAL"], contested=True)
        return PERSUASIVE([])
    return NOT_BINDING([])   # district/trial courts
```

Row 3a is not part of `binding_on_forum` (it concerns the *provision*, not the precedent). P3 applies it when computing the provision's `AuthorityView` status: an HC `STRIKES_DOWN` edge whose object is a central Act gets `qualifiers.territory = "IN"` instead of the HC's territory, while a `STRIKES_DOWN` of a *state* Act keeps the state's territory.

**Machine positions on the contested points in 01_master §14.2 Q2.** 01_master returns `UNDETERMINED` + `contested=true` for four points "until 21_india settles them". The law is not settled on all four, but the machine behaviour is. Every case below sets `binding_basis.contested=true` and carries the rule IDs, so P10 can show the controversy.

| Point | Machine output | Basis |
|---|---|---|
| Weight of SC obiter | `PERSUASIVE`, `rule_ids ∋ rul_IN_PREC_12` (row 2). Never `UNDETERMINED`, never `BINDING` | rul 12 (*Sarwan Singh Lamba*, "normally") |
| Precedential effect of a stayed HC judgment | Binding is computed as usual (a stay does not wipe out the order, rul 20); `AuthorityView.status=CAUTION` with an authority reason code for the stay (P3 registry); never `NEGATIVE` | rul 20 (*Shree Chamundi Mopeds*) for orders; precedential effect unverified |
| Territorial effect of an HC strike-down of a central Act | Provision status `NEGATIVE` (final order) or `CAUTION` (interim stay) with territory `IN` (all-India), per row 3a; the HC's *reasoning* is `PERSUASIVE` outside its territory | rul 24 (*Kusum Ingots*), rul 17 |
| Governing HC for an all-India tribunal bench | If the forum's bench seat is known, `jurisdictional_hc` = the HC with territorial jurisdiction over that seat (row 8); otherwise `UNDETERMINED` and P10 asks the user (row 9) | rul 16 (*L. Chandra Kumar*: "the High Court within whose jurisdiction the concerned Tribunal falls"); the seat-based default is an inference *(unverified)* |

**Input types** (so P3 and P5 implement the same signature):
```ts
type CourtLevel = "SC" | "HC" | "TRIBUNAL_APPELLATE" | "TRIBUNAL" | "DISTRICT" | "AUTHORITY";
interface AuthorityRef { work_id: string; level: CourtLevel; court_id: string /* crt_… */; bench_id?: string /* bnc_… */;
  bench: number | null /* judges on the bench, not the majority (rul 06) */; decision_date: string; tribunal_family?: string /* e.g. "NCLT" */ }
interface Forum { level: CourtLevel; court_id: string | null; bench: number | null; territory?: string /* ISO 3166-2:IN */;
  jurisdictional_hc?: string | null; date: string /* the as_of_legal_date for the question */; source: "USER" | "MATTER" | "ASSUMED" }
interface PropositionInput { law_declared?: "NORMAL" | "ART142_DIRECTION" | "EXPRESSLY_NOT_PRECEDENT" | "CONCESSION_BASED" | "PER_INCURIAM_DECLARED";   // D20.7 (P3 field)
  form: "RATIO" | "OBITER" | "SUB_SILENTIO" | "NON_SPEAKING_SLP" | "NO_MAJORITY" }                                                            // authority-core internal
interface Binding { value: "BINDING" | "PERSUASIVE" | "NOT_BINDING" | "UNDETERMINED"; rule_ids: string[]; contested: boolean;
  conflict?: "LARGER_BENCH" | "EARLIER_COEQUAL" | "UNRESOLVED" }
// v1.0 D6/D16: surfaced as AuthorityView.binding_on_forum + binding_basis{rule_ids, authority_anchor_ids, contested, conflict}.
// D20.7: binding_basis.weight is NOT adopted; consumers derive "strongly persuasive" from rule_ids ∋ rul_IN_PREC_12.
```

`territory_to_hc(territory, at)` reads the `court_jurisdiction` table (§1), which is time-versioned. For example, before 1 Jan 2019 the forum for an Andhra Pradesh or Telangana matter resolves to the common Hyderabad HC [IN-52].

---
## 5. Treatment vocabulary: an Indian citator that is better than KeyCite and Shepard's

### 5.1 Why existing citators fall short

**Global citators.** Western citators disagree with each other heavily on negative treatment (Hellyer 2018, summarised in 05_P3 §3.4). Commercial legal AI cites overruled authority (the Stanford study's *Casey*-after-*Dobbs* example; Magesh et al. [IN-70]).

**Indian products.** 20_competitive_teardown and 05_P3 §3.4 give the detail. In short, Indian products expose case-level flags or citing lists, not the answer to the question "is this *proposition* still good law *for my forum*". Four Indian features make case-level flags misleading:
- **Paragraph-level overruling.** "The decision in NN Global 2 ... and SMS Tea Estates ... are overruled. **Paragraphs 22 and 29 of Garware Wall Ropes ... are overruled to that extent**" (*In re Interplay*, 2023 INSC 1066) [IN-30].
- **Bench-strength limits on who can overrule whom** (rul 04–06).
- **SLP dismissals that look like affirmances but are not** (rul 10).
- **Pending references that do not unsettle law** (rul 09).

### 5.2 Vocabulary (maps to spine §F predicates plus P3's S3-4 additions)

Tier 1 marks assertions that can change legal conclusions. They go to human review (HITL) before they are shown as definitive (spine §F).

| Predicate | Indian meaning | Textual cues (English; seed list) | Verified example | Tier |
|---|---|---|---|---|
| `FOLLOWS` / `APPLIES` | Adopts a ratio as binding or persuasive and applies it | "followed", "applied", "relied upon", "in view of the law laid down in", "squarely covered by" | — | 3 |
| `EXPLAINS` | Clarifies the scope of the cited ratio | "explained", "must be understood in the context of" | — | 3 |
| `DISTINGUISHES` | Holds the ratio inapplicable on facts or issue | "distinguishable", "has no application to the facts", "rendered in a different context" | — | 2 |
| `DOUBTS` | A co-equal Bench doubts correctness. This is *not* negative status (rul 09). | "we have our doubts", "requires reconsideration" | *Ladakh* notes HCs wrongly refusing deference when a coordinate Bench has doubted [IN-15] | 2 |
| `REFERS_TO_LARGER_BENCH` | A reference order. It creates a `PendingReference` node. | "place the papers before Hon'ble the Chief Justice for constitution of a larger Bench" | *Nabam Rebia* referred to a larger Bench (noted in *Ladakh*) [IN-15] | 2 |
| `ANSWERS_REFERENCE` (P3 S3-4) | The larger Bench answers the reference questions | "reference answered accordingly" | *In re Interplay* (7-J; the curative-petition context is visible in the text) [IN-30] | 1 |
| `NOT_FOLLOWED` / `CONFLICTS_WITH` | Declines to follow (HC vs other HC; tribunal) | "we respectfully disagree", "not followed" | — | 2 |
| `OVERRULES` | Only a Bench of larger strength, or the same strength in the SC exceptionally via reference, can do this (rul 04–05) | "is overruled", "stands overruled", "was wrongly decided", "does not lay down the correct law" | *Interplay*: "SMS Tea Estates and Garware Wall Ropes were wrongly decided"; "NN Global 2 ... overruled" [IN-30]. *Krishna Kumar Singh* overruling *Bhupendra Kumar Bose* and *Venkata Reddy* [IN-28]. | 1 |
| `OVERRULES_IN_PART` | Paragraph- or proposition-level overruling. `qualifiers.cited_anchor` is mandatory where given. | "overruled to that extent", "to the extent it holds" | *Interplay* → *Garware* paras 22, 29 [IN-30] | 1 |
| `DECLARES_PER_INCURIAM` | A competent Bench declares a decision per incuriam | "per incuriam", "not a binding precedent" | *Pranay Sethi*: *Rajesh* "is not a binding precedent" [IN-14] | 1 |
| `LEGISLATIVELY_OVERRIDDEN_BY` | The basis of a ruling is removed by amendment | "legislatively overruled", "the basis of the judgment has been removed" | Phrase "has been legislatively overruled" in *Interplay* [IN-30] | 1 |
| Direct history: `AFFIRMS`, `REVERSES`, `MODIFIES`, `SETS_ASIDE`, `REMANDS` | Appellate outcome. The lower decision **merges** (rul 10(i)). | "appeal dismissed", "impugned judgment set aside", "remitted" | — | 1 |
| `DISMISSES_IN_LIMINE` (P3 S3-4) | SLP refused: **no merger, no affirmance** | "special leave petition is dismissed", "we are not inclined to interfere" | *Kunhayammed* (iv) [IN-17] | 2 (1 if a speaking order declares law) |
| `STAYS` | Interim stay of operation. Not wiped out (rul 20). | "operation of the impugned judgment shall remain stayed" | *Shree Chamundi Mopeds* [IN-27] | 1 |
| `REVIEW_OF`, `CURATIVE_OF`, `RECALLS` | Post-finality correction | "review petition dismissed", "curative petition" | *Rupa Ashok Hurra* grounds [IN-18]; *Interplay* is captioned in a curative petition [IN-30] | 1 |
| `STRIKES_DOWN`, `READS_DOWN`, `UPHOLDS_VALIDITY`, `INTERPRETS` | Statute–judgment edges | "ultra vires", "read down", "intra vires" | — | 1 (`INTERPRETS` 3) |

**Hindi cue lexicon.** Seed terms such as "पलट दिया" (overruled), "अनुसरण" (followed), "भिन्न/विभेद" (distinguished), "वृहद पीठ" (larger bench), "अपास्त" (set aside) and "पुष्टि" (affirmed) are **[NOVEL — unvalidated]**. They must be mined from the Hindi judgments of the four Hindi-authorised HCs (§8) and validated by bilingual annotators before use.

### 5.3 Design rules that make it better than existing citators

1. **Granularity.** Treatment attaches to `(citing_anchor → cited Work | cited_anchor | proposition_id)`. Case-level flags are *derived* summaries, never stored truth.
2. **Competence check** **[NOVEL — unvalidated]**. An `OVERRULES` candidate from a Bench *smaller* than the cited Bench is doctrinally impossible (rul 05). It is re-typed `NOT_FOLLOWED` or `DOUBTS`, with `reason_code=INCOMPETENT_OVERRULING_CUE`, and routed to review. This catches both extraction errors and genuine judicial indiscipline, which *Sundarjas* and *Rooplal* treat as serious [IN-22][IN-23].
3. **Forum-relative status.** "Good law" is always reported *for a forum and a date*. The same HC judgment is BINDING in Lucknow and PERSUASIVE in Patna.
4. **Honest non-events.** Pending references, review or curative petitions, doubts and non-speaking SLP dismissals are displayed as *information* with the rule that neutralises them (rul 09, 10). A **"false red flag" is a first-class error metric** (§10.3).
5. **Derived negativity** (`RELIES_ON_OVERRULED`). A judgment whose ratio paragraph relies on an overruled proposition gets `CAUTION`. This is P3's KeyCite "Overruling Risk" analogue, applied at paragraph level.
6. **Evidence first.** Every treatment assertion carries the citing paragraph quote (spine §F `evidence`). The UI shows the sentence ("are overruled to that extent"), not only a colour.

---
## 6. Criminal law transition: IPC/CrPC/IEA → BNS/BNSS/BSA

### 6.1 Verified statutory basis

**Commencement.** The three Sanhitas/Adhiniyam apply from **1 July 2024**. Courts treat offences before 01.07.2024 as IPC offences [IN-31]. The BNS has 358 sections, adds 20 new offences and drops 19 IPC provisions [IN-43].

**BNS s.358** (repeal and savings), quoted in [IN-31]:
- (1) repeals the IPC.
- (2) the repeal "shall not affect" (a) previous operation; (b) rights and liabilities accrued; (c) "any penalty, or punishment incurred in respect of any offences committed against the Code so repealed"; (d)–(e) any investigation, proceeding or remedy for them, which "may be instituted, continued or enforced ... as if that Code had not been repealed".
- (3) anything done under the IPC is deemed done under the corresponding BNS provisions.
- (4) preserves the general application of **General Clauses Act s.6** [IN-47].

**BNSS s.531** [IN-32]:
- (2)(a) any "appeal, application, trial, inquiry or investigation pending" immediately before commencement is disposed of under the CrPC "as if this Sanhita had not come into force".
- (2)(b) notifications, powers, local jurisdictions, sentences, orders, rules and appointments (other than Special Magistrates) are deemed made under the "corresponding provisions" of the BNSS.
- (2)(c) sanctions given under the CrPC with no proceeding yet commenced are deemed given under the BNSS.
- (3) a limitation period that expired before commencement is **not revived** by a longer BNSS period.

**BSA s.170** [IN-33]: any "application, trial, inquiry, investigation, proceeding or appeal pending" before commencement is dealt with under the IEA.

**Art. 20(1)**: no conviction except for violation of "a law in force at the time of the commission of the act", nor "a penalty greater than that which might have been inflicted under the law in force at the time of the commission of the offence" [IN-7].

### 6.2 Case law 2024–2026 (verified)

| Case | Holding relevant to the engine |
|---|---|
| *Parvinder Singh v. Directorate of Enforcement*, **2026 INSC 519** (19 May 2026; M.M. Sundresh, N. Kotiswar Singh JJ.) [IN-34] | s.531(2)(a) "is meant to give a prospective application to the provisions of the BNSS ... once a proceeding such as an appeal, application, investigation, inquiry or trial is initiated under the CrPC, then the same must meet its logical conclusion under the CrPC itself ... to avoid piecemeal application" (para 28). A BNSS substantive right "would definitely enure to the benefit of an accused against whom none of the proceedings envisaged under Section 531(2)(a) ... has been initiated" (para 29). "A mere ministerial act cannot be termed as an 'inquiry'" (numbering a complaint is not inquiry; cognizance is application of judicial mind) (para 34). The first proviso to BNSS s.223(1) (hearing before cognizance) is **substantive**: it "confers a right upon the accused to be heard before taking cognizance" (para 27). CrPC ss.200–205 (now BNSS ss.223–228) apply to PMLA complaints, following *Kushal Kumar Agarwal*, 2025 SCC OnLine SC 1221. |
| *CBI v. Ramesh Chander Diwan*, **2025 INSC 539** (22 Apr 2025; Dipankar Datta, Manmohan JJ.) [IN-35] | Because of s.531 BNSS, "pending proceedings are to be continued under the repealed law". The Court declined liberty to seek BNSS s.218 deemed sanction and reserved liberty to seek sanction under the CrPC (para 30). |
| *Arunkumar v. State of Karnataka*, Karnataka HC (Kalaburagi), 30 Sep 2024, `2024:KHC-K:7531` [IN-31] | Offences committed before 01.07.2024 are to be registered under the IPC, not the BNS, reading BNS s.358(2). |
| *Rajendra Bihari Lal v. State of U.P.*, **2025 INSC 1249** [IN-36] | CrPC 1898 s.561A is "in pari materia with Section 482 of the Cr.P.C., and Section 528 of the B.N.S.S." This gives a **three-generation chain**, and pre-1973 inherent-power precedent carries forward. |
| *Kasireddy Upender Reddy v. State of A.P.*, **2025 INSC 768** [IN-37] | "Sections 420, 409 read with Section 120-B of the IPC ... (Now Sections 318, 316(5) read with Section 61(2) of the BNS)". The SC cites **section-level "318"**, while the specific cheating-with-inducement limb is commonly cited as 318(4) [IN-40]. |
| *Achin Gupta v. State of Haryana*, **2024 INSC 369** [IN-38] | BNS ss.85 and 86 are "nothing but verbatim" reproduction of IPC s.498A. That is **one IPC section → two BNS sections**: offence and definition. |
| Gauhati HC, criminal appeal, 19 Jun 2025 [IN-39] | Convicted "under Section 302 of the Indian Penal Code, 1860 [Corresponding to Section 103 of the Bharatiya Nyaya Sanhita, 2023]". |

**Unsettled and flagged.**
- **Continuing offences that straddle 1 July 2024** have no verified authority. → `UNDETERMINED`.
- **Whether a *lesser* BNS penalty benefits a pre-July-2024 offender.** Art. 20(1) bars only *greater* penalties [IN-7], and we have no verified post-2024 authority. → `CONTESTED`.
- **HC decisions before May 2026 on "which procedure"** must be re-tested against *Parvinder Singh* (P4 backfill task).

### 6.3 Which-code decision procedure (for P3 doctrine engine and the P6 procedural agent)

The unit of transition is the **proceeding**, not the matter. A single matter can have its offence under the IPC, its investigation under the CrPC (pending on 1 Jul 2024), and its cognizance/inquiry under the BNSS (initiated later), with evidence governed by whether that proceeding was pending (BSA s.170).

```python
CUTOVER = date(2024, 7, 1)
def governing_code(matter, stage):            # stage ∈ {OFFENCE, INVESTIGATION, INQUIRY, TRIAL, APPEAL, APPLICATION, EVIDENCE, LIMITATION}
    if stage == "OFFENCE":
        d = matter.offence_date                    # may be a range
        if d is None: return UNDETERMINED("offence date unknown")
        if d.is_range and d.start < CUTOVER <= d.end: return UNDETERMINED("straddling offence")  # CONTESTED
        return ("IPC", ["BNS s.358(2)", "Art.20(1)"]) if d.end < CUTOVER else ("BNS", [])
    p = matter.proceeding(stage)                   # each proceeding has initiated_on + initiation_kind
    if p is None or p.initiated_on is None: return UNDETERMINED("proceeding initiation unknown")
    if p.initiation_kind == "MINISTERIAL":         # e.g. numbering/registration of complaint (Parvinder, para 34)
        p = p.next_judicial_step()                 # cognizance etc.
    pending_on_cutover = p.initiated_on < CUTOVER and (p.concluded_on is None or p.concluded_on >= CUTOVER)
    if stage == "EVIDENCE":
        return ("IEA", ["BSA s.170(2)"]) if pending_on_cutover else ("BSA", [])
    if stage == "LIMITATION" and p.limitation_expired_before(CUTOVER):
        return ("CrPC", ["BNSS s.531(3)"])         # no revival
    return ("CrPC", ["BNSS s.531(2)(a)", "Parvinder Singh 2026 INSC 519 ¶28"]) if pending_on_cutover \
           else ("BNSS", ["Parvinder Singh 2026 INSC 519 ¶29"])
```

This requires dates per proceeding, not one `as_of_legal_date`. See spine change C2 (§10.4).

**Spine v1.0 (D16, C2 accepted-modified).**
- **Raw record.** `MatterContext.procedural_events[]{event_type (controlled vocab), date, certainty, alt_dates, anchor, confirmed_by?, source EXTRACTED|LAWYER}` (P7) is the raw record of these dates.
- **Derived view.** `temporal_context{substantive_event_date?, proceedings[]{stage, initiated_on, initiation_kind JUDICIAL|MINISTERIAL, concluded_on?}, filing_date?}` is derived from those events. It is exposed on MatterContext, and optionally on ResearchQuery. `as_of_legal_date` remains the default.
- **Inputs.** `governing_code()` reads `matter.offence_date` from `temporal_context.substantive_event_date` and `matter.proceeding(stage)` from `temporal_context.proceedings[]`.
- **Ownership.** This doc owns the procedure; P3 implements it, and the P6 procedural agent calls it.
- **Unit of transition.** The proceeding stage. The offence date governs substantive law.
- **Uncertain dates.** An event whose `alt_dates` straddle the cutover, or whose `certainty` is `ESTIMATED` (P7 values: EXACT|DEEMED|ESTIMATED) within the uncertainty window around 1 Jul 2024, yields `UNDETERMINED` (the straddling rule above).

### 6.4 Crosswalk data model

`CORRESPONDS_TO` is a Tier-1 assertion (spine §F). P3 owns storage. This doc fixes the semantics. **Under spine v1.0 (D7, D16), the `change_type` enum below is canonical.** P3 adopts it, together with `group_id`, `granularity`, `penalty_delta`, `chain_prev` and `source_kind`, using the mapping table below to migrate its earlier enum. Every row is `impact_tier 1`, clause-level and many-to-many (D7), and each row's ID uses the `xrn_` prefix (D12, confirmed by D20.5: `xrn_` = crosswalk row, `xtr_` = extraction run).

```ts
type Correspondence = Assertion & {
  predicate: "CORRESPONDS_TO";
  subject: ProvisionRef;       // old provision, expression-independent (05_P3 S3-7): wrk_…(IPC)#sec-498A
  object:  ProvisionRef | null;// new provision, e.g. wrk_…(BNS)#sec-85 ; null for OMITTED
                               // (wrk_… are opaque ULIDs per spine §B; "IPC"/"BNS" above are labels, not IDs)
                               // compared texts are pinned in evidence[]: …/en@2024-06-30#sec-498A vs …/en@2024-07-01#sec-85
  qualifiers: {
    change_type: "SAME_RENUMBERED" | "SAME_TEXT_SPLIT" | "MERGED" | "SPLIT" | "MODIFIED_SCOPE"
               | "MODIFIED_PENALTY" | "REPLACED_BY_DIFFERENT_OFFENCE" | "FUNCTIONAL_ANALOGUE"
               | "NEW_NO_PREDECESSOR" | "OMITTED";
    group_id?: string;         // binds the 1→n or n→1 members of one mapping (498A → 85 + 86)
    granularity: "SECTION" | "SUBSECTION" | "CLAUSE";
    text_similarity?: number;  // normalized alignment score old↔new text (P1 diff)
    penalty_delta?: "SAME" | "HIGHER" | "LOWER" | "DIFFERENT_KIND";   // drives Art.20(1) warnings
    chain_prev?: AssertionId;  // CrPC1898 s.561A → CrPC s.482 → BNSS s.528
    source_kind: "OFFICIAL_TABLE" | "GAZETTE_TEXT_DIFF" | "JUDICIAL" | "EDITORIAL" | "THIRD_PARTY" | "MODEL";
    // Final enum = spine v1.0 D20.11 (extends D16). Mapping from this doc's earlier draft values:
    //   OFFICIAL_TABLE → OFFICIAL_TABLE; JUDICIAL_STATEMENT → JUDICIAL; GAZETTE_TEXT_DIFF → GAZETTE_TEXT_DIFF (reviewed diff of
    //   the official Gazette texts); EDITORIAL → EDITORIAL; THIRD_PARTY → THIRD_PARTY; an unreviewed machine alignment → MODEL.
    //   A row whose only source_kind is THIRD_PARTY or MODEL is never displayed as definitive (Tier-1 HITL first);
    //   THIRD_PARTY (e.g. IK "[Similar to Section …]" annotations) is used as cross-check evidence under the IK ToU.
    diff_ref?: string;         // v1.0 D7: pointer to the stored old↔new text diff (P1 alignment)
  };
};
```

**Reconciliation with 05_P3 §5.7** *(added in independent review; previously a silent divergence; **settled by spine v1.0 D16: one enum, this doc's**, so `legal_change_type` is retired and its values *are* `change_type`; the table below is now P3's migration mapping from its pre-v1.0 enum, and the P5 `via_crosswalk` penalty keys on the canonical values)*. P3's stored `change_type` enum was `{IDENTICAL_TEXT, RENUMBERED_EQUIVALENT, NARROWED, WIDENED, PUNISHMENT_CHANGED, MERGED, SPLIT, PARTIAL_OVERLAP}`. This doc's enum is finer and legal-classification oriented. Until the spine fixes one enum (C5), P3 stores **both**: `change_type` (P3 enum, used by P5's `via_crosswalk` penalty) and `legal_change_type` (this enum, used by P6/P8 and `PRECEDENT_CARRIES_TO`). Deterministic mapping:

| Canonical v1.0 `change_type` (formerly this doc's `legal_change_type`) | P3 pre-v1.0 `change_type` (legacy, for migration) | Carry rule |
|---|---|---|
| SAME_RENUMBERED, `text_similarity ≥ 0.97` | IDENTICAL_TEXT | GOOD |
| SAME_RENUMBERED, `< 0.97` | RENUMBERED_EQUIVALENT | GOOD only with judicial pari-materia statement, else CAUTION |
| SAME_TEXT_SPLIT | SPLIT | GOOD per member (group_id) |
| MERGED / SPLIT | MERGED / SPLIT | CAUTION |
| MODIFIED_SCOPE | NARROWED or WIDENED (editor chooses; PARTIAL_OVERLAP if both) | CAUTION |
| MODIFIED_PENALTY | PUNISHMENT_CHANGED | GOOD for the elements; CAUTION for sentence propositions; Art. 20(1) check |
| FUNCTIONAL_ANALOGUE | PARTIAL_OVERLAP | CAUTION |
| REPLACED_BY_DIFFERENT_OFFENCE / NEW_NO_PREDECESSOR / OMITTED | PARTIAL_OVERLAP / (none, `NO_COUNTERPART_IN`) / (none, `NO_COUNTERPART_IN`) | no carry |

`text_similarity` = token-level Jaccard over normalised text (lower-cased, punctuation and cross-reference numbers stripped, section numbers mapped through the crosswalk itself) **[NOVEL — threshold 0.97 unvalidated; calibrate on the 498A→85 pair and 50 reviewed pairs]**.

**`PRECEDENT_CARRIES_TO`** (derived, P3 S3-4). A judgment interpreting old provision X carries to new provision Y with this status:
- `GOOD` if `change_type ∈ {SAME_RENUMBERED, SAME_TEXT_SPLIT}` and `text_similarity ≥ 0.97`, or if a judicial pari-materia statement exists (e.g. [IN-36]).
- `CAUTION` + `reason_code=PROVISION_MODIFIED` for the MODIFIED_* types.
- No carry for `REPLACED_BY_DIFFERENT_OFFENCE`, `NEW_NO_PREDECESSOR` or `OMITTED`.

**Evidence sources, strongest first**
1. **Gazette text diff** of the MHA/Gazette texts [IN-44], aligned by P1.
2. **Judicial statements** harvested by P1 (`correspondence_hint`: "now Section …", "corresponding to", "in pari materia"), e.g. [IN-34][IN-36]–[IN-39].
3. **Official tables.** The NCRB flyers [IN-45] turned out to be thematic flyers, not a section-level table. The BPR&D handbooks are *unverified* because the site reset our connection. **No official, machine-readable, section-level IPC/CrPC/IEA → BNS/BNSS/BSA table has been located.** The text diff (1) is therefore the primary builder, not a cross-check.
   - **Build cost (estimate) [NOVEL — unvalidated].** IPC (511 ss.), CrPC (484 ss.) and IEA (167 ss.) *(last-section numbers; not re-verified here)* give ≈1,160 old sections, ≈3,500 including sub-sections. At two independent reviewers per section-level row and ~10 min per row, that is ≈390 reviewer-hours for section level; sub-section rows for the ~150 most-cited sections add ≈150 h. This is a one-time cost and is cheap relative to its Tier-1 risk. Budget it in 22_roadmap.
4. **Third-party annotations.** Indian Kanoon marks sections "[Similar to Section 438 from Old CrPC]" etc. [IN-41]. Use these only as a cross-check under the IK ToU.

**Every mapping is human-verified before it is shown as definitive** (Tier 1).

### 6.5 Worked crosswalk (verified rows only; others must be built from text diff + review)

| Old | New | change_type (canonical v1.0 enum, D16) | Evidence |
|---|---|---|---|
| IPC 302 | BNS 103 ("Punishment for murder") | SAME_RENUMBERED (sub-section 103(1)) | [IN-39][IN-41] |
| IPC 420 | BNS 318(4) | SAME_RENUMBERED, `granularity=SUBSECTION` (SC cites "318") | [IN-40] snippet; [IN-37] |
| IPC 409 / 120-B | BNS 316(5) / 61(2) | SAME_RENUMBERED | [IN-37] |
| IPC 498A | BNS 85 + 86 | SAME_TEXT_SPLIT (`group_id`) | [IN-38] |
| IPC 124A (sedition) | BNS 152 ("Act endangering sovereignty, unity and integrity of India") | REPLACED_BY_DIFFERENT_OFFENCE, **no precedent carry** | [IN-42][IN-41] |
| IPC 377 | — | OMITTED (BNS "does not retain section 377") | [IN-42] |
| IPC 497 (adultery) | — | OMITTED | [IN-42] |
| — | BNS 111 (organised crime), 113 (terrorist act), 304 (snatching) | NEW_NO_PREDECESSOR | [IN-41][IN-42] |
| — | BNS **103(2)**: murder by "a group of five or more persons acting in concert ... on the ground of race, caste or community, sex, place of birth, language, personal belief or any other ground" (text as reproduced by [IN-77]; the "mob lynching" limb). So IPC 302 maps to **103(1)** only; 103(2) has no predecessor. The grievous-hurt analogue (reported as s.117(4)) is *unverified*. | NEW_NO_PREDECESSOR, `granularity=SUBSECTION` | [IN-77] (secondary) |
| CrPC 438 | BNSS 482 | SAME_RENUMBERED (modified text: review) | [IN-41] |
| CrPC 482 | BNSS 528 (chain from CrPC 1898 s.561A) | SAME_RENUMBERED + `chain_prev` | [IN-41][IN-36] |
| CrPC 154 | BNSS 173 | MODIFIED_SCOPE *(review; BNSS 173 text differs)* | [IN-41] |
| CrPC 200–205 | BNSS 223–228 | MODIFIED_SCOPE (s.223(1) proviso: pre-cognizance hearing) | [IN-34] |
| CrPC 272 | BNSS 307 (language of courts) | SAME_RENUMBERED | [IN-41] |
| CrPC 484 | BNSS 531 | FUNCTIONAL_ANALOGUE (repeal and savings; content differs) | [IN-32] |
| IEA 65B | BSA 63 (certificate by person in charge **and** an expert) | MODIFIED_SCOPE | [IN-41][IN-76] |

**The number-collision trap** (verified): "Section 482" means **inherent powers** under the CrPC but **anticipatory bail** under the BNSS [IN-41]. Any bare "u/s 482" mention in a document dated after 1 Jul 2024 is `AMBIGUOUS_ACT` until the act context or the relief sought disambiguates it. P1 must not default the act from the document date.

---
## 7. Temporal law: point-in-time design

### 7.1 Indian sources of temporal complexity (verified where cited)

| Phenomenon | Rule | Modelling consequence |
|---|---|---|
| **Enactment ≠ commencement** | Acts commence on notified dates, often in stages. The DPDP Act illustrates this: Rules notified 13 Nov 2025; Rules 1, 2 and 17–21 in force immediately; Rule 4 (consent managers) after 12 months; Rules 3, 5–16, 22 and 23 after 18 months (AZB gives 12 Nov 2026 and 12 May 2027) [IN-59]. The Income-tax Act 2025 is in force from 1 Apr 2026 (08_P6 [IN-72]). | `LegislativeAction(kind=COMMENCES, target_anchor_set, effective_from, gazette_ref)`. Provision-level `valid_from`. Never use assent date as `valid_from` (consistent with P2 §5). |
| **Ordinances** | Same force as an Act, but an ordinance "shall cease to operate at the expiration of six weeks from the reassembly of Parliament" unless disapproved earlier, and may be withdrawn (Art. 123(2)) [IN-8]. Art. 213 is the state analogue. Repeated re-promulgation is a "fraud on the Constitution" (*Krishna Kumar Singh*, 7-J, 2017), with separate opinions differing on what survives lapse [IN-28]. | Ordinance expression `valid_to = min(withdrawal, disapproval, reassembly+6 weeks)`. `valid_to` stays *provisional* until the Gazette shows replacement, lapse or disapproval. Survival of effects after lapse → `CONTESTED` flag, not auto-inference. |
| **State amendments to central Acts** (Concurrent List) | A repugnant state law on a Concurrent List matter that has received Presidential assent "shall prevail in that State" (Art. 254(2)) [IN-9]. | **Territorial expressions.** The same Work has different text in different states on the same date (spine change C3, accepted in v1.0 D16: `expression_key = lang@YYYY-MM-DD[~TERR]`). |
| **Repeal and savings** | GCA s.6: a repeal does not revive, does not affect previous operation or accrued rights/liabilities, and saves pending proceedings "unless a different intention appears" [IN-47]. BNS s.358(4) expressly preserves s.6 [IN-31]. | Repeal ends the expression's `valid_to` for *new* conduct. Saved rights keep the old expression **operative** for events before repeal. P3 therefore evaluates by event date, not query date. |
| **Retrospective and validating Acts** | Legislatures amend with retrospective effect to override judgments (`LEGISLATIVELY_OVERRIDDEN_BY`, §5) *(general practice; no specific instance re-verified here)*. | Bitemporal: a retrospective amendment enacted on T2 with `valid_from = T0 < T2` is recorded at T2. Queries `as_known_at < T2` see the old law (spine §E). |
| **Judicially moulded retroactivity** | *MADA* (2024) moulded the past effect of a declaration [IN-26]. | `effect=MOULDED` + anchored `conditions[]` on the assertion (spine change C4). |
| **Constitution amendments** | Same pattern as Acts: amendment Act → commencement → articles substituted or inserted. Two constitution-specific twists (QC addition). **(a) An amendment can itself be struck down.** The Constitution (Ninety-ninth Amendment) Act 2014 inserted Arts. 124A–124C and amended Arts. 124, 127, 128, 217, 222, 224, 224A and 231. It came into force on 13 Apr 2015 (S.O. 999(E)). A five-judge Bench declared it "unconstitutional and void" on 16 Oct 2015 in *Supreme Court Advocates-on-Record Assn. v. Union of India*, W.P.(C) No. 13 of 2015 (commonly reported as (2016) 5 SCC 1 *(reporter citation unverified)*), and declared the pre-amendment ("collegium") system operative [IN-80]. **(b) How the Constitution applies can change by Presidential order.** C.O. 272 and C.O. 273 (5–6 Aug 2019) amended Art. 367 as applied to Jammu and Kashmir and made the Constitution apply there in full. The Constitution Bench upheld both orders in *In Re: Article 370 of the Constitution*, 2023 INSC 1058 (11 Dec 2023) [IN-81]. | `art-21A`-style anchors with `@date` (spine §C). For (a), the 05_P3 §5.6 validity overlay (`STRIKES_DOWN`) is not enough on its own: for dates after the strike-down, `resolve()` must return the **pre-amendment expression** as operative, while the struck-down expression stays retrievable with `validity=STRUCK_DOWN` for the interval it was in force. For (b), the change is a territorial expression (C3, `~JK`) whose `valid_from` comes from the Presidential order, not from an amendment Act. The P1 amending-instruction grammar (03_P1 §5.7) must therefore accept constitution orders as a source of `LegislativeAction`. |
| **India Code limits** | India Code is a consolidated text "re-typed and updated from time to time". We found no documented point-in-time versioning (02_P0). | India Code = **current-text cross-check only**. Historical versions are *reconstructed* from Gazette amendment instructions (P1 amending-Act grammar). Automatic consolidation has known risks, so each reconstructed version is diffed against any available official consolidated snapshot [IN-74]. |

### 7.2 Point-in-time resolution contract

`resolve(anchor, legal_date, territory)` does four things. Under spine v1.0 D16, statute expression keys take the form `lang@YYYY-MM-DD[~TERR]`, e.g. `en@2019-06-06~UP`. `TERR` is the ISO 3166-2:IN subdivision code without its `IN-` prefix, and the corresponding `ter_` ID follows D12. Point-in-time resolution takes `(date, territory)`, and an expression without `~TERR` is the all-India text.
1. Pick the Work's expression whose `[valid_from, valid_to)` contains `legal_date`, filtered to `recorded_at ≤ as_known_at`.
2. If a **territorial variant** exists for `territory`, pick it; otherwise pick the all-India expression.
3. If an ordinance expression is `provisional`, return `status=PROVISIONAL` with the reason.
4. Attach the savings context. If the provision was repealed before `legal_date` but a savings clause applies to the event (GCA s.6 / BNS s.358 / BNSS s.531 / BSA s.170), return the repealed text with `operative_by_saving=true` and the saving anchor.

**Which date?** This follows the *Parvinder Singh* logic (§6.3) generalised:
- **Substantive** questions use the date of the operative event (offence, cause of action, transaction, assessment year).
- **Procedural** questions use the date the relevant proceeding was initiated.
- **Limitation** questions use both the accrual date and the filing date.

One `as_of_legal_date` per query is therefore insufficient (C2).

---

## 8. Multilingual realities

**Constitutional baseline.**
- Art. 348(1) requires English for "all proceedings in the Supreme Court and in every High Court". It also makes English the authoritative text of Bills, Acts, Ordinances, orders, rules, regulations and bye-laws [IN-10].
- Art. 348(2) lets a Governor, with Presidential consent, authorise Hindi or the state's official language in HC *proceedings*. The proviso excludes judgments, decrees and orders [IN-10].
- **Official Languages Act 1963 s.7** separately permits Hindi or the state's official language for HC *judgments, decrees and orders*, "in addition to the English language". Such a judgment "shall be accompanied by a translation of the same in the English language issued under the authority of the High Court" [IN-11].
- Four states — **Bihar, Uttar Pradesh, Madhya Pradesh, Rajasthan** — have HC proceedings authorised in Hindi. Tamil Nadu's request was not granted [IN-53] *(secondary source)*.

**Subordinate courts.**
- The State Government determines the language of civil courts (CPC s.137) [IN-46] and criminal courts (BNSS s.307, formerly CrPC s.272) [IN-41].
- District-level orders in Marathi, Tamil, Kannada, Gujarati, Bengali, Hindi and others are therefore normal, not exceptional. This matters for TPL case files (P7) far more than for the PLC.

**Supreme Court translations.**
- ~2,900 SC judgments had been translated into Hindi and other languages by Feb 2023. The work was AI-assisted, with verification by retired district judges [IN-48].
- P0 reports later counts (~37,000 Hindi) *(not re-verified here)*.

**Design rules**
1. **Authoritative-expression flag.** For HC judgments under OLA s.7, the pronounced-language text and the HC-issued English translation are *both* Expressions of one Work (`hi`, `en`). Their authority labels are ORIGINAL and OFFICIAL_TRANSLATION. Earlier drafts also listed an `OUR_MT` value, which v1.0 removes.
   - *Spine v1.0 D16 form.* Both carry `authoritative=true`, with `authority_basis=ORIGINAL` or `OLA_S7_HC_TRANSLATION` (P1 §2.4) and `translation_of` on the translation. This doc's label `OFFICIAL_TRANSLATION` maps to `OLA_S7_HC_TRANSLATION`. SC vernacular translations are `COURT_PUBLISHED_TRANSLATION` with `authoritative=false`.
   - *No `OUR_MT` value.* Machine translation is **not an Expression at all** (rule 2), so no Expression carries this label.
   - Which of `hi` and `en` prevails on conflict is **not settled** by any authority we verified → `CONTESTED`.
   - P6/P8 quote the ORIGINAL and show the official translation alongside it.
2. **Machine translation is never a citation source.**
   - **MT renditions** (e.g. IndicTrans2 [IN-69]) are never Expressions (spine v1.0 D8/D16). On the public side they are node `aux_text['{lang}-x-mt']` / `Chunk.mt` with `authoritative=false`; on the private side they are display renditions such as `pdoc_…/v1.mt-en`. They exist for retrieval and for the lawyer's reading aid only.
   - Anchors are aligned to the original's paragraphs via P1's alignment record.
   - A claim anchored to an MT rendition fails P8 verification by design. MT renditions may be displayed and aligned, but they are never support anchors.
3. **For statutes**, English is authoritative (Art. 348(1)(b)). Hindi statute texts are official translations (Authoritative Texts (Central Laws) Act, 1973 *(not re-verified)*). The display follows s.52(1)(r) limits for any translation we generate (§2.1).
4. **Script and numeral normalisation** (Devanagari digits; "धारा" = section; Latin-script citations inside Hindi judgments) happen before citation extraction (P1 §5.8).
5. **Missing official translation** *(added in independent review)*. OLA s.7 requires an HC-issued English translation [IN-11], but it may lag or be absent from the portal. Until it appears, the Hindi ORIGINAL is the only citable expression, and treatment edges proposed from an MT rendition are forced to `PENDING_REVIEW` with a bilingual reviewer. P0 re-polls for the official translation weekly for 90 days (§10.2).
6. **Private translations of regional-language orders** (spine v1.0 D21.17, D21.12). District-court orders in a TPL case file are often in the state language (CPC s.137 [IN-46]; BNSS s.307 [IN-41]). A lawyer-attested certified translation uploaded by the firm is a private rendition `pdoc_…/v1.ht-en` with `authoritative=true`, recorded by P7. It may support RECORD_FACT claims only, never public-law claims. A certified copy of the order itself carries `trust_label=TENANT_COURT_RECORD`. An MT rendition (`v1.mt-en`) supports nothing.
7. **Confusable characters** *(added in independent review)*. Before the citation grammar runs, NFKC-normalise the text and map homoglyphs (Latin `O`/digit `0`, Cyrillic lookalikes, Devanagari digits) inside candidate spans only. A citation that resolves only *after* homoglyph repair is tagged `resolution_basis=REPAIRED` and never auto-activates an alias (T0/T1). This blocks both OCR noise and deliberately spoofed citations in uploaded TPL documents.

### 8.R Independent review findings

*This doc keeps the topic-brief structure (§1–§10). Its full red-team table is §10.2. This subsection records what the independent review (2026-09-30) verified, changed and left open.*

**Citation audit.** 23 high-stakes references were re-fetched from primary or near-primary sources: [IN-3], [IN-13], [IN-14], [IN-15], [IN-26], [IN-28], [IN-30], [IN-31], [IN-34], [IN-35], [IN-36], [IN-37], [IN-38], [IN-41] (BNSS 482/528, BSA 63, BNS 152 pages), [IN-45], [IN-48], [IN-55], [IN-59], [IN-62], [IN-64], [IN-65], [IN-68], [IN-75]. Corrections made:
- *EBC v. Modak*: the headnote point was overstated. The SC left an un-challenged HC interim restraint in place (para 42); it did not itself "uphold" headnote copyright (§2.2).
- The SC e-Committee "uniform HC neutral citation" request is **not** in [IN-48]; now marked unverified (§3.2).
- DPDP Rules commencement dates aligned to [IN-59] (12 Nov 2026 / 12 May 2027, with rule lists). The cross-border rule number is now marked unverified (§7.1, §9).
- NCRB "flyers" [IN-45] opened: they are 10 thematic flyers, not a crosswalk. No official section-level table has been located, so the text diff becomes the primary crosswalk builder (§1, §6.4).
- BNS 103(2) (group murder on specified grounds) confirmed [IN-77]; IPC 302 now maps to 103(1) only (§6.5).
- Precision fixes: *Parvinder Singh* para 27 for the substantive-proviso holding; *Ramesh Chander Diwan* date; *MADA* neutral citation; *Trimurthi* bench size; *Krishna Kumar Singh* overruling scoped to the "enduring rights" theory; *In re Summoning Advocates* holding on in-house counsel.
- Confirmed as accurate: *Parvinder Singh* paras 28, 29 and 34; *Ladakh* para 35, including "the earlier one ... is to be followed by the High Courts"; *Interplay*'s paragraph-level overruling of *Garware* paras 22 and 29; *Achin Gupta* paras 38–39; the IK API ToU (RAG and fine-tuning permitted with attribution; one-month termination); AWS datasets CC-BY-4.0; OpenAI India residency is storage-only.

**Gaps patched** (India-specific):
1. *Laksh Vir Singh Yadav* reaches us directly. Principle (iv) obliges "other hosts" on receipt of a court masking order, and para 277 imposes an upload-time duty on IK for victim identity. Added: an upload-time masking gate, order-authenticity checks against RTBF abuse, and the CONTESTED intermediary question (§2.5, Q8).
2. Two missing precedent rules: Art. 142 directions are not precedent (*Rafiq Masih*, rul 23), and an HC order on a central Act's validity has all-India effect (*Kusum Ingots*, rul 24). Both are wired into the decision table (rows 3, 3a) and the pseudo-code (§4).
3. Typed inputs for `binding_on_forum` (§4.2), and SQL for `court_jurisdiction` with a no-overlap constraint (§1).
4. A silent divergence from 05_P3's `change_type` enum was resolved with a mapping table and a `legal_change_type` field. *(Spine v1.0 D16 then made this doc's enum the single canonical `change_type`; §6.4.)* Crosswalk rows now use P3's expression-independent `ProvisionRef` (S3-7) (§6.4).
5. A silent spine divergence (`en.m1` masked expressions) is now explicit spine change C8 and reconciled with 04_P2's `doc.redacted.v1`. *(Spine v1.0 D16 rejected C8: masking is a RedactionOverlay on `doc.redacted.v1`, with no masked expression_key; §2.5, §10.4A.)* `order_ref` now uses spine-conformant anchor syntax.
6. Privilege: `privilege_basis` for in-house-counsel tenants (C9).
7. Cost: a crosswalk HITL budget (≈540 reviewer-hours) and a cost-control row in the red team (§6.4, §10.2).
8. Freshness SLO for "overruled yesterday", and a masking-gate recall metric (§10.3).
9. Hindi judgments without an official translation, and homoglyph or spoofed citations (§8 rules 5 and 7).

**Remaining open** (not fixable within this review's budget; the WebSearch quota was exhausted, so only direct fetches were possible):
- Formats for Gujarat, Patna, Telangana, AP and Sikkim HC neutral citations; the Digital SCR citation form; the SCC OnLine abbreviation for HCs. All still unverified.
- BPR&D / MHA official correspondence tables. Not located.
- The 2024–2026 HC split on straddling offences and on lesser BNS penalties. No authority found; stays UNDETERMINED/CONTESTED.
- BCI conduct rules, POCSO s.23 and JJ Act s.74 section numbers, and the Authoritative Texts (Central Laws) Act 1973. Not re-verified.
- Whether the SC has narrowed *Kusum Ingots* for interim orders (Q9). Whether *Laksh Vir Singh Yadav* is under appeal (Q7).
- `text_similarity` threshold (0.97), masking-gate threshold (0.2) and the freshness SLOs are unvalidated targets.

---

## 9. Compliance

| Regime | Verified content | Engineering consequence |
|---|---|---|
| **DPDP Act 2023** | **s.3(c)(ii)** excludes personal data made publicly available by the Data Principal or under a legal obligation to publish. Whether court publication qualifies is arguable (02_P0 [IN-58]). **s.16(1)**: the Central Government "may, by notification, restrict the transfer of personal data ... to such country or territory outside India as may be so notified" (a negative list). **s.16(2)**: sectoral laws with stricter transfer rules still apply [IN-56]. **s.17(1)(a)** exempts processing "necessary for enforcing any legal right or claim"; **17(1)(b)** processing by courts and tribunals; **17(2)(b)** research, archiving or statistical purposes where the data is not used for decisions about the principal [IN-57]. | PLC judgments are treated as personal data with masking and takedown support (§2.5). TPL processing for a client's matter relies on s.17(1)(a) for the *legal claim* purpose. It is **not** a blanket exemption for our product analytics or model training: P9's Privacy Gate stays mandatory. Cross-border LLM calls are lawful unless the destination is notified, but client contracts and CERT-In logs still drive India residency (13_XC). |
| **DPDP Rules 2025** | Notified **13 Nov 2025**. Rules 1, 2 and 17–21 (Board, procedure) immediate. Rule 4 (consent managers, s.6(9)) from **12 Nov 2026**. Rules 3, 5–16, 22 and 23 (notice, security safeguards, breach notification, retention/erasure, cross-border transfer) from **12 May 2027** [IN-59]. *(The specific rule number for cross-border transfer — reported as Rule 15 — is not stated in [IN-59]; unverified.)* | Roadmap (22) must have DPDP-core controls live before **12 May 2027**: breach runbook, retention schedules, data-principal request handling for any PLC personal data (masking) and TPL data. |
| **CERT-In Directions, 28 Apr 2022** (IT Act s.70B(6)) | Cyber incidents reported within **6 hours**; ICT logs kept **180 days within India**; clock sync (09_P7 / 13_XC [IN-60]) | Log pipeline region-pinned to India. Incident runbook with a 6-hour SLA (13_XC). |
| **Advocate privilege: BSA ss.132–134** (formerly IEA ss.126–129) | s.132 protects professional communications and extends to advocates' clerks and employees (09_P7 [IN-61]). *In re: Summoning Advocates...*, **2025 INSC 1275** (31 Oct 2025; Gavai CJI, K.V. Chandran, N.V. Anjaria JJ.): an investigating officer cannot directly summon an advocate to extract details of a client's case except within the s.132 exceptions, and such summons are subject to judicial review. The protection **does not extend to in-house counsel**, who are not "Advocates" under the Advocates Act, 1961 [IN-62] (verified on the SCO case page). | Privilege class on every TPL object (spine `privilege_flags`). **Tenant type matters:** for a corporate legal-department tenant, communications with in-house counsel get `privilege_basis=NONE_IN_HOUSE` unless an external advocate is party to them, and the UI must not display a "privileged" badge on them. `privilege_flags` therefore needs `{basis: ADVOCATE_S132 \| NONE_IN_HOUSE \| LITIGATION_WORK_PRODUCT_UNTESTED, advocate_ids[]}` (spine change C9). The vendor (us) is treated as an agent within the advocate's privilege circle by contract. **Whether a SaaS vendor's staff count as "employees" of the advocate under s.132 is untested → CONTESTED.** This is the core argument for customer-managed keys and private deployment options (P7). |
| **Right to be forgotten / masking** | *Laksh Vir Singh Yadav* (Delhi HC, 2026) directs name-search restriction for legal databases, and says a court's masking order obliges "other hosts" to disable name-based search [IN-55] | `access_restriction` (§2.5, spine change C6); upload-time masking gate |
| **Bar Council of India Rules** (advocates' conduct) | BCI Rules Part VI, Ch. II, rule 36 bars advocates from soliciting work or advertising *(unverified in this session)*. BCI rules on registration of foreign lawyers and law firms (2022/2023) *(unverified)*. | Product features that publish a firm's "wins", rank advocates by outcomes, or route leads to advocates can expose **tenants** to conduct complaints. P9 outcome data stays tenant-internal. P10 has no public advocate-ranking or marketplace feature without a legal opinion. Open question Q10. |
| **Hallucinated citations in Indian fora** | Documented Indian instance: an ITAT Bangalore order (Dec 2024) was recalled after it was reported to cite non-existent judgments (20_CT [IN-73]) | Justifies P8's hard gate. Also a sales argument: Indian benches now notice fake citations. A recalled order is flagged in the graph: P3 sets `Work.integrity_flags ∋ RECALLED` (and `AI_GENERATION_ALLEGED` where the recall cites fabricated authority) from the `RECALLS` predicate, surfaced as an `AuthorityView` reason code (spine v1.0 D19.5). |
| **Data residency and on-prem demand** | No general DPDP localisation (s.16 negative list) [IN-56]. Model providers differ: one major provider offers India *storage* but not India *processing* (13_XC [IN-68]). Top Indian firms (Shardul Amarchand Mangaldas, AZB) adopted a US SaaS legal-AI vendor in 2025 (20_CT [IN-67]). | Evidence suggests **SaaS in an India region is acceptable to large firms** when security is strong. Private-cloud or on-prem (spine v1.0 D17: D3 customer VPC, D4 on-prem/air-gapped, D4h on-prem with in-India cloud LLM endpoints) is a premium tier for PSU and government-adjacent or high-sensitivity matters, not the default *(demand split unverified; validate with the design partner, 22_roadmap)*. The MVP is one D2 dedicated cell running the same code as the D1 pooled SaaS cell that opens at GA (D17). |

---
## 10. Design implications per phase

### 10.1 Phase-by-phase obligations

| Phase | Must implement (from this doc) |
|---|---|
| **P0** | Gazette-first capture for all legal-change events (§1, §7). Capture court-prohibition, in-camera and masking signals and `terms_ref`, and publish them as `doc.redacted.v1` overlays with `raw.captured.v1.change_kind=SUPPRESSED` for takedowns (v1.0 D16). Publish the tenant-agnostic court feeds as the ratified events `court.calendar.published.v1`, `court.causelist.published.v1` and `case.status.observed.v1` (D20.1), daily orders as ordinary captures, and `judgment.expected.v1` (record prefix `jex_`, D20.5) with `referenced_authorities[]` for reference orders (D21.18). Never circumvent CAPTCHAs (`rul_IN_ACCESS_1`). Seed the `court_jurisdiction` table (25 HCs, benches, time-versioned) [IN-52]. Harvest SC `diary_no` from `view-pdf` URLs [IN-50]. Obtain each HC's neutral-citation notification (Gujarat, Patna, Telangana, AP and Sikkim formats unobserved). |
| **P1** | Grammar §3.3 incl. slash/colon, zero-padding, `-DB/-FB`, line-break repair. Year-window check for publication-year reporters (§3.1). Opinion segmentation from the court copy only (EBC ¶41). `AMBIGUOUS_ACT` for post-2024 "482"-type mentions (§6.5). Harvest `correspondence_hint`s. Masking for BNS s.72-type matters via the upload-time gate (§2.5). Under v1.0 D16 this is a `doc.redacted.v1` RedactionOverlay (`MASK_SPANS`), not a masked expression (C8 rejected). Court-issued paragraph numbering only (D16). Signals for P3's `law_declared` (D20.7 enum: Art. 142 / "not a precedent" / concession cues, rul 23) and for the internal `form` input (SLP non-speaking; speaking-order law). Mint EXPECTED Works on P3's request (D20.4). Hindi and regional cue lexicons. |
| **P2** | Territory-aware statute chunks (`valid_from/valid_to` + `territory`). Suppressed-name exclusion from lexical name fields and facets (§2.5). Index MT renditions (`Chunk.mt` shadow field, `authoritative=false`; never Expressions, per v1.0 D16) so retrieval can hit them but citation cannot. Build every projection from the masked rendition when a RedactionOverlay applies. |
| **P3** | Rule registry §4.1 and decision table §4.2. Competence check on OVERRULES (§5.3). `DISMISSES_IN_LIMINE` ≠ `AFFIRMS`. `effect=MOULDED`. All-India territory for HC `STRIKES_DOWN` of central Acts (row 3a). Adopt this doc's `change_type` enum as the single canonical crosswalk enum, with `source_kind` OFFICIAL_TABLE\|GAZETTE_TEXT_DIFF\|JUDICIAL\|EDITORIAL\|THIRD_PARTY\|MODEL (D20.11), and migrate the pre-v1.0 enum via the §6.4 mapping (v1.0 D16; `legal_change_type` retired). Crosswalk model §6.4 with Tier-1 HITL. Implement `rul_IN_PREC_*` in `authority-core` as the canonical DoctrineRule registry, and `governing_code()` (§6.3) over `temporal_context`. `PRECEDENT_CARRIES_TO` derivation. `access_restriction` on Work (the Work registry is P1's; P3 reads it). `law_declared` (D20.7) on Proposition. `Work.integrity_flags[]` (D19.5). Never machine-declare per incuriam. |
| **P4** | Trigger AuthorityView recomputation when a reference is answered, a stay is vacated, or an ordinance lapses (timer events at reassembly+6 weeks). P3 commits the status through `commit_status_batch` (v1.0 D4). Backfill: re-test pre-May-2026 "which procedure" treatments against *Parvinder Singh*. Propagate takedown and masking within 2 weeks. The Delhi HC direction gave two weeks (para 284) [IN-55]. In v1.0 this is `doc.redacted.v1`, whose `purge_sla` (serving 1 h, derived 24 h) is well inside two weeks. |
| **P5** | Rank by `binding_on_forum`. Never collapse to court level. Treat `UNDETERMINED` forums with a generic-HC profile plus a warning (as P5 already does). Fire the I8 CROSSWALK intent for both codes. Apply date-per-stage (§6.3). Suppress name-only hits on restricted Works. |
| **P6** | The procedural agent uses `governing_code()` per stage. Memos state *which code and why* with the savings anchor (BNSS s.531(2)(a) ¶ / *Parvinder* ¶28). Memos distinguish BINDING from PERSUASIVE in claim text. SC obiter is phrased as "strongly persuasive" (rul 12, contested). |
| **P7** | `MatterContext` carries a proceedings timeline (initiation dates per stage), not just `cause_of_action`. v1.0 D16: raw `procedural_events[]`, from which the derived `temporal_context` is exposed (§6.3). Privilege flags per BSA s.132, with `privilege_basis` by tenant type (in-house counsel not covered; C9). Regional-language district-court orders are the norm in case files (§8). |
| **P8** | Block claims anchored to MT renditions (v1.0 D16). Block tier-1 claims whose only support is a `pg{n}` locator. Check the stated binding status against P3. Check "which code" claims against `governing_code()`. Treat a false red flag as an error class alongside missed negative treatment. |
| **P9** | Lawyer corrections on treatment or crosswalk are `ASSERTION` feedback → P3 review queue. Never train on TPL-derived text beyond s.17(1)(a) purposes without the Privacy Gate. |
| **P10** | Show forum and date assumptions on every status chip. Show pending references and stays as information, not red flags. Offer a "why this code applies" explainer. Show the takedown/RTBF state for PLC content. |

### 10.2 Red-team findings

| Attack / stress | What breaks | Mitigation in this design |
|---|---|---|
| **10M+ documents** | Alias conflicts explode for AIR (no volumes) and for SCC across the main series and sub-series. Party-name matching fails on common names ("State of U.P."). | Tiered aliases (§3.4). Conflicts freeze merges (P1). Year windows. Neutral citations as T0 anchors for post-2023 material; retro HC citations exist for older material [IN-54]. |
| **Bad OCR** | Citations split across lines (`RJ-⏎JD`) [IN-54]. "INSC" misread. "498A" becomes "49BA". | Grammar-aware line repair. Critical-token uncertainty (P1). Resolver temporal and court sanity checks. |
| **Hindi judgment** | Treatment cues are missed. The English translation and the Hindi original conflict. | Hindi cue lexicon (novel, validated). `authoritative` flag. Contested-precedence display (§8). |
| **Precedent overruled yesterday** | Status lags. A paragraph-level overruling is shown as whole-case red. | Tier-1 fast-path review (P3/P4). `OVERRULES_IN_PART` with `cited_anchor` (*Interplay* pattern) [IN-30]. |
| **"Overruled" by a smaller Bench** (extraction error or judicial indiscipline) | A false NEGATIVE status. | Competence check (§5.3). |
| **Pending reference / SLP dismissal misread** | False red flag or false green. | rul 09/10 encoded. `DISMISSES_IN_LIMINE`. |
| **Crosswalk mis-mapping** (482 collision; 124A → 152 treated as the same offence) | Wrong law applied: catastrophic. | `AMBIGUOUS_ACT`. `REPLACED_BY_DIFFERENT_OFFENCE` blocks precedent carry. Tier-1 HITL on every mapping. |
| **Straddling offence / unknown proceeding dates** | A confident wrong code. | `UNDETERMINED` + P10 asks the user for dates. |
| **Malicious or prompt-injected document** (a fake "this case was overruled by 2025 INSC 9999") | A poisoned treatment edge. | Treatment is accepted only from PLC court-issued documents. Every citation is resolved and verified to exist. TPL documents never create PLC assertions (spine §A). |
| **Confused user** (asks "is X good law?" without a forum) | Answers BINDING/PERSUASIVE without a basis. | `UNDETERMINED` + forum prompt. The assumed forum is displayed. |
| **Source outage / format change** (neutral-citation format change at an HC; SCI WAF 403s) | Parser misses. Ingestion gaps. | Format table as data, not code. Alias learning from T1 clusters. Multi-source (AWS CC-BY + IK API + portal) fallback, per P0. |
| **RTBF abuse** (a litigant forges or overstates a "masking order" to bury adverse precedent) | Good law disappears from name search; opposing counsel cannot find it. | Suppression activates only from an order fetched from an official source (`order_source_raw_id`) and reviewed (§2.5). Suppression never removes a Work from citation, case-number or proposition retrieval (para 285 model). |
| **Art. 142 / "not to be treated as a precedent" read as law** | A false BINDING, especially in service and tax matters, where such directions are common. | `law_declared ∈ {ART142_DIRECTION, EXPRESSLY_NOT_PRECEDENT}` → NOT_BINDING (rul 23, row 3). P1 cue list: "in exercise of our powers under Article 142", "shall not be treated as a precedent", "peculiar facts and circumstances". HITL on every SC proposition carrying such a cue. |
| **HC strikes down a central Act; engine treats it as local** | A provision is shown GOOD in Chennai while a Delhi HC final order has struck it down. | Row 3a / rul 24 (*Kusum Ingots*): the provision's status is all-India, while the HC's reasoning stays persuasive outside its territory. |
| **Hindi judgment with no official English translation yet** (OLA s.7 requires one, but it can lag or be missing on the portal) | Treatment cues in the Hindi original are missed, or an MT is quoted as law. | Hindi ORIGINAL is the citable expression. The MT rendition (never an Expression, v1.0 D16) is used only to *propose* candidate treatment edges, which are forced to `PENDING_REVIEW` with a bilingual reviewer. P0 re-polls for the HC translation weekly for 90 days and adds it as `OFFICIAL_TRANSLATION` (`authority_basis=OLA_S7_HC_TRANSLATION`, `authoritative=true`) when it appears. |
| **In-house-counsel tenant assumes privilege** | Documents shown as "privileged" are not protected (2025 INSC 1275). | `privilege_basis` (§9, C9). Tenant onboarding captures tenant type. |
| **Cost blow-up** (IK API per-call fees at 10M-doc backfill; HITL volume on Tier-1 edges; MT of district orders) | Unbounded spend. | IK is gap-filler only; the AWS CC-BY bulk sets are the backfill (§1). Tier-1 HITL is budgeted: crosswalk ≈540 reviewer-hours one-time (§6.4); treatment review is prioritised by `citation_count × forum_reach` so only the head of the distribution waits for humans; the long tail shows `definitive=false`. MT runs on demand per matter (TPL), never corpus-wide. |
| **Legal-risk red team** | A bare-Act export breaches s.52(1)(q)(ii). Reporter paragraphing leaks via a third-party dataset. Name search on RTBF-protected parties. | "Original matter" requirement on statute outputs (§2.1). A provenance filter bans reporter-derived text (§2.2). `access_restriction` (§2.5). |

### 10.3 Evaluation metrics owned by this doc (feed P8)

- **Doctrine-rule accuracy.** `binding_on_forum` agreement with partner-firm lawyers on ≥300 (authority, forum) pairs stratified over the rows of table §4.2. Target ≥98% on SETTLED rows. On CONTESTED rows, 100% `contested=true` surfaced.
- **False-red-flag rate.** NEGATIVE/PARTIAL_NEGATIVE shown where lawyers judge the proposition good for the forum. Target <1% of flagged items, tracked separately from the missed-negative rate.
- **Crosswalk precision.** 100% on displayed-definitive mappings (HITL). Coverage = share of IPC/CrPC/IEA sections with a reviewed mapping. Target 100% before GA of the criminal module.
- **Which-code accuracy** on a gold set of ≥100 transition scenarios (built with the partner firm from real FIR/charge-sheet timelines). Target ≥97%, and 0 confident answers on UNDETERMINED cases.
- **Citation resolution by scheme.** Precision ≥99.5% for T0/T1. Recall reported per HC neutral-citation format.
- **Negative-treatment freshness** *(added in independent review)* **[NOVEL — targets unvalidated]**. From an SC judgment appearing on sci.gov.in to (a) a machine `CAUTION` signal (`definitive=false`, `reason_code=NEGATIVE_SIGNAL_UNDER_REVIEW`, per v1.0 D6) on every cited Work carrying an OVERRULES/OVERRULES_IN_PART cue: p95 ≤ 6 h; (b) Tier-1 HITL decision: p95 ≤ 2 business days for SC Benches of ≥3 judges. HC judgments: (a) ≤ 24 h after capture.
- **Masking-gate recall.** Share of sexual-offence and juvenile Works caught by the upload-time gate before first display (§2.5). Target ≥99.5% on a reviewed sample of 1,000 such Works; zero known victim-identity displays.

### 10.4 Proposed spine changes

*This table is the original proposal record. Spine v1.0 dispositions are in §10.4A.*

| # | Target | Change | Justification |
|---|---|---|---|
| C1 | §H AuthorityView / `binding_on_forum` | **Endorse P3 S3-2** (`UNDETERMINED`, `binding_basis{rule_ids, contested}`) and add `binding_basis.conflict: LARGER_BENCH\|EARLIER_COEQUAL\|UNRESOLVED` and `binding_basis.weight: HIGH\|NORMAL` (SC obiter). Proposition field `law_declared` enum as in §4.2, including `ART142_DIRECTION` and `EXPRESSLY_NOT_PRECEDENT`. | Rules 04–09. Contested rules (12, 16, 20, 22) must surface as contested. |
| C2 | §H ResearchQuery + MatterContext | Add `temporal_context{ substantive_event_date?, proceedings[]{stage, initiated_on, initiation_kind, concluded_on?}, filing_date? }`. `as_of_legal_date` stays as a default. | *Parvinder Singh* (2026 INSC 519): the transition unit is the proceeding. BSA s.170 and BNSS s.531 key on pending proceedings, and Art. 20(1) keys on the offence date. One date cannot express this. |
| C3 | §B/§C expression_key + point-in-time resolution | Statute `expression_key = lang@YYYY-MM-DD[~TERR]` (e.g. `en@2019-06-06~UP`). Anchor resolution takes `(date, territory)`. Territory codes = ISO 3166-2:IN. | Art. 254(2) state amendments make the text territory-dependent. P3's `IN_FORCE_IN` covers extent but not *text variants*. |
| C4 | §F Assertion qualifiers (P3 S3-1 `effect`) | Add `effect=MOULDED` with `conditions[]{text, anchor_id}` | *MADA* 2024 [IN-26]: retroactivity limited by date, instalments and waivers. That is neither prospective nor fully retrospective. |
| C5 | §F `CORRESPONDS_TO` qualifiers | Store both P3's `change_type` and this doc's `legal_change_type` with the deterministic mapping in §6.4 (or adopt one enum). Fix `group_id`, `granularity`, `penalty_delta`, `chain_prev` and `source_kind` as in §6.4 | Needed for 1→n splits (498A → 85+86), chains (561A → 482 → 528), and Art. 20(1) warnings. |
| C6 | §B Work + §G events | Add `access_restriction{name_search_suppressed[], masked_expression_required, court_prohibition, statutory_bar}` (schema §2.5) and event `work.access_restricted.v1` (P0/P3/ops → P2, P5, P10) with `data{work_id, change: ADDED\|LIFTED, entries[], order_ref, effective_from, deadline}`. Add ID prefix `ent_` (party/person entity). | Delhi HC 2026 [IN-55] (two-week compliance, para 284; "other hosts", principle (iv)); s.52(1)(q)(iv) court prohibition [IN-1]; BNS s.72. |
| C7 | §D identifier_alias | `NEUTRAL_HC` value normalised as `{court_code}\|{bench_code}\|{year}\|{n}\|{bench_type}`. Add schemes `SCC_SUPP`, `SCC_SERIES`, `AIR_SCW`, `AIRONLINE`, `NJRS`. `SC_DIARY_NO` format `n/yyyy`. | Observed formats §3.1–3.2 [IN-51][IN-54]. |
| C8 | §B expression_key (judgments) | Reserve suffix `.m{n}` for **masked expressions** (e.g. `en.m1`), alongside `.r{n}` for corrigenda. A masked expression reuses the source expression's fragment IDs (identity `anchor_alias`, method `MASK`) and becomes the display and index default. For the unmasked expression, 04_P2's `doc.redacted.v1` procedure applies unchanged (derived text purged from all generations, hashes kept). The court-issued raw blob stays in the object store under legal-hold access only, for provenance and for revocation (Delhi HC principle (v)). Register `doc.redacted.v1` (P2) and `work.access_restricted.v1` (C6) together in spine §G: the first masks *text*, the second suppresses *name search*. *(Previously a silent divergence: §2.5 used `en.m1` with no spine change, and P2 masked in place without an expression key.)* | Masking is retrospective and prospective (principle (iii)) [IN-55]; audit replay (spine §E) needs a stable key for "what we displayed when". |
| C9 | §H MatterContext `privilege_flags` | `privilege_flags{basis: ADVOCATE_S132\|NONE_IN_HOUSE\|LITIGATION_WORK_PRODUCT_UNTESTED, advocate_ids[], asserted_by, asserted_at}` per TPL object | *In re: Summoning Advocates*, 2025 INSC 1275: s.132 does not cover in-house counsel [IN-62]. |

### 10.4A Spine v1.0 conformance

The principal architect's spine v1.0 decision record (D1–D21, [01a_spine_decision_record.md](01a_spine_decision_record.md)) disposed of C1–C9 as follows. Where this doc's body and v1.0 differ, v1.0 wins. The affected passages have been annotated in place.

| # | Proposal | Disposition |
|---|---|---|
| C1 | `binding_on_forum` UNDETERMINED, `binding_basis{rule_ids, contested}`, `conflict`, `weight`; Proposition `law_declared` | **ACCEPTED-MODIFIED (D6, D16).** `AuthorityView` (P3-owned) is the only input for badges, ranking and P8 status checks. `binding_on_forum` is BINDING\|PERSUASIVE\|NOT_BINDING\|UNDETERMINED, and `binding_basis{rule_ids, authority_anchor_ids, contested}` gains **`conflict` LARGER_BENCH\|EARLIER_COEQUAL\|UNRESOLVED** (D16). **`weight` is not adopted** (confirmed by D20.7): "strongly persuasive" SC obiter is expressed by PERSUASIVE + `contested=true` + `rule_ids ∋ rul_IN_PREC_12`. **`law_declared` is ACCEPTED (D20.7)** as an optional P3 Proposition field with the enum `ART142_DIRECTION \| EXPRESSLY_NOT_PRECEDENT \| CONCESSION_BASED \| PER_INCURIAM_DECLARED \| NORMAL`; `authority-core` treats ART142_DIRECTION and EXPRESSLY_NOT_PRECEDENT as non-binding precedent. This doc's other former values moved to the engine-internal `form` input (§4.2). |
| C2 | `temporal_context{…}` on ResearchQuery + MatterContext | **ACCEPTED-MODIFIED (D16).** `MatterContext.procedural_events[]` is the raw record, and `temporal_context{substantive_event_date?, proceedings[]{stage, initiated_on, initiation_kind JUDICIAL\|MINISTERIAL, concluded_on?}, filing_date?}` is *derived* from it. It is exposed on MatterContext and optionally on ResearchQuery, and `as_of_legal_date` stays the default. `governing_code()` is owned here and implemented in P3 (§6.3). |
| C3 | Territorial statute expressions `lang@YYYY-MM-DD[~TERR]` | **ACCEPTED (D16).** ISO 3166-2:IN codes; point-in-time resolution takes `(date, territory)` (§7.2). |
| C4 | `effect=MOULDED` with `conditions[]{text, anchor_id}` | **ACCEPTED (D16).** |
| C5 | Crosswalk `change_type` / `legal_change_type` + qualifiers | **ACCEPTED-MODIFIED (D7, D16).** A single enum is adopted, and **the canonical enum is this doc's** (§6.4), plus `group_id`, `granularity`, `penalty_delta` and `chain_prev`. `source_kind` is final in D20.11: `OFFICIAL_TABLE\|GAZETTE_TEXT_DIFF\|JUDICIAL\|EDITORIAL\|THIRD_PARTY\|MODEL` (mapping in §6.4); `diff_ref` is added; P5's `via_crosswalk` penalty keys on `change_type`. P3 migrates its pre-v1.0 enum via the §6.4 table, and `legal_change_type` is retired. Crosswalk rows are always `impact_tier 1`. |
| C6 | `Work.access_restriction{…}` + event `work.access_restricted.v1` + prefix `ent_` | **ACCEPTED-MODIFIED (D16).** `Work.access_restriction{name_search_suppressed[], masked_expression_required, court_prohibition}` is **kept**. `work.access_restricted.v1` is **folded into `doc.redacted.v1`**: name-search suppression is a RedactionOverlay with `kind=NAME_SEARCH_SUPPRESSED`. `statutory_bar` travels as `RedactionOverlay.legal_basis`. Producers (D20.3): P0 for source suppression and captured court orders, P1 for statutory identity masking found in parsing, ops/legal for manual entries (e.g. an RTBF order served on us). Every consumer acks with `redaction.applied.v1` and P0's redaction ledger alerts on `purge_sla` breach (D19.3); the ledger is our compliance evidence for the para 284 two-week direction. `ent_` is accepted for recurring institutional parties only, with no IDs for individuals, so RTBF entries use `party_ref` spans (§2.5). |
| C7 | `NEUTRAL_HC` normalisation; schemes `SCC_SUPP`, `SCC_SERIES`, `AIR_SCW`, `AIRONLINE`, `NJRS`; `SC_DIARY_NO` `n/yyyy` | **ACCEPTED (D16).** Alias rows also carry `trust_tier` T0–T4 (T0 court-issued … T4 model-inferred), and third-party never overrides T0. This matches §3.4's tiering. |
| C8 | Masked expressions `.m{n}` (`en.m1`) | **REJECTED (D16).** Masking is a **RedactionOverlay** carried on **`doc.redacted.v1`** `{overlay_id, scope WORK\|EXPRESSION\|ANCHOR_SPANS, kind SUPPRESS_ALL\|MASK_SPANS\|NAME_SEARCH_SUPPRESSED\|COURT_PROHIBITION, spans[], legal_basis, ordered_by?, effective_at, purge_sla}`. Indexes, snippets, exports and quote checks use the masked rendition, and no masked `expression_key` exists. The audit-replay need ("what we displayed when") is met by the overlay's `overlay_id` + `effective_at` under the bitemporal model. The raw blob stays under legal hold (unchanged). Producers are P0, P1, ops and legal (not P2). |
| C9 | `privilege_flags{basis, …}` | **ACCEPTED (D16).** `MatterContext.privilege_flags` gains `basis`. |
| — | Doctrine registry size | **D20.8:** `rul_IN_PREC_01..24`, all canonical (§4.1). |
| — | Coverage-gap semantics | **D20.12 (refines D6):** `COVERAGE_GAP` is a reason code with `definitive=false`; the status changes (GOOD → UNKNOWN) only past the per-source threshold; negatives keep their status (§4.2). |
| — | Recalled and AI-generated judgments | **D19.5:** `Work.integrity_flags[]` (owner P3) = RECALLED \| AI_GENERATION_ALLEGED \| CORRIGENDUM_PENDING \| WITHDRAWN_FROM_SOURCE \| SUPPRESSED, surfaced via `AuthorityView.reason_codes`. The ITAT Bangalore recall (§9) is the Indian instance behind RECALLED + AI_GENERATION_ALLEGED. |
| — | Reference orders | **D21.18:** `judgment.expected.v1` carries optional `referenced_authorities[]`, so a reference order naming a precedent (rul 05, rul 09) lets P4 raise a PROVISIONAL impact on it at any bench size. Binding is unchanged while the reference is pending (rul 09). |
| — | Private translations and court records | **D21.17:** a private certified translation `v1.ht-en` (authoritative=true, lawyer-attested, recorded by P7) may support RECORD_FACT claims only. **D21.12:** privately held certified copies of court records carry `trust_label=TENANT_COURT_RECORD` (data-only; RECORD_FACT support). Regional-language district-court orders in case files (§8) use both. |
| — | 01_master §14.2 Q2 (contested doctrine) | Machine positions fixed in §4.2 ("Machine positions on the contested points"); the legal questions stay CONTESTED. |
| — | 01_master §14.2 Q7 (unverified HC formats) | Design rule fixed in §3.2 rule 6 (format table as data, `PENDING` aliases for unverified formats); the five formats stay unverified. |

**Renames this doc now follows**
- "`OUR_MT` expressions" → **MT renditions**, which are never Expressions: `aux_text['{lang}-x-mt']` / `Chunk.mt` on the public side and `{pdoc_id}/v1.mt-en` on the private side. The `authoritative` labels ORIGINAL / OFFICIAL_TRANSLATION map to `authority_basis` ORIGINAL / OLA_S7_HC_TRANSLATION with `authoritative=true`.
- Masked expression `en.m1` → RedactionOverlay on `doc.redacted.v1`. `work.access_restricted.v1` → `doc.redacted.v1`.
- `legal_change_type` → `change_type` (canonical). `source_kind` (final, D20.11) = `OFFICIAL_TABLE | GAZETTE_TEXT_DIFF | JUDICIAL | EDITORIAL | THIRD_PARTY | MODEL`; the draft value `JUDICIAL_STATEMENT` → `JUDICIAL`. P5's `via_crosswalk` penalty keys on the canonical `change_type` (D20.11).
- AuthorityStatus as the consumer-facing object → **`AuthorityView`** (the status enum stays 5-valued: GOOD\|CAUTION\|NEGATIVE\|PARTIAL_NEGATIVE\|UNKNOWN). "Under review" = `CAUTION` + `definitive=false` + reason code `NEGATIVE_SIGNAL_UNDER_REVIEW` (D6). A coverage gap = reason code `COVERAGE_GAP` + `definitive=false` with the status unchanged, degrading GOOD → `UNKNOWN` only past the per-source threshold (D20.12, refining D6).
- The DoctrineRule registry `rul_IN_PREC_01..24` (§4.1) is canonical for P3's `authority-core` (D20.8).
- `law_declared` takes the D20.7 enum; the former values OBITER / SUB_SILENTIO / NON_SPEAKING_SLP / NO_MAJORITY are the engine-internal `form` input (§4.2); `binding_basis.weight` is dropped.
- The P0 judgment-expected record is `jex_` (D20.5), and EXPECTED stub Works are minted by P1 at P3's request (D20.4).
- Deployment names follow D17 (D1/D2/D3/D4/D4h), and ID prefixes follow D12 (`rul_`, `ter_`, `xrn_`, `rvw_`, `ent_`, `bnc_`, `crt_`).

### 10.5 Open questions and risks

- **Q1.** Does s.52(1)(q)(ii) ("together with commentary") constrain API or bulk exports of statute text? This is untested. Get a legal opinion before a public statute API launches.
- **Q2.** May IK-derived metadata ("Equivalent citations") seed our alias tables under the IK ToU? Get written confirmation. Until then, use it for cross-check only.
- **Q3.** Is a SaaS vendor within the BSA s.132 privilege circle? This is untested. It drives the default deployment (P7) and contract language.
- **Q4.** The precedential effect of an SC stay of an HC judgment (rul 20) and HC-declared "prospective" overruling (rul 18) have no verified authority. Both stay CONTESTED.
- **Q5.** Neutral-citation numbering: do single-bench and DB judgments share one sequence per HC? Get the per-HC notifications (P0 task).
- **Q6.** Official IPC/CrPC/IEA correspondence tables: get the BPR&D and NCRB documents from India egress and diff them against our text alignment.
- **Q7.** Delhi HC RTBF judgment: track any appeal or SC position. The design already complies, so this is low risk.
- **Q8.** Is our platform an "intermediary" (IT Act s.2(1)(w)) for PLC content, and so directly bound by Rule 3(1)(d) masking/de-indexing directions? We comply as if it were; get a legal opinion.
- **Q9.** *Kusum Ingots* gives an HC order on a central Act all-India effect. Do later SC or HC decisions narrow this for *interim* stays? Not researched here → the interim-stay case shows CAUTION, never NEGATIVE.
- **Q10.** BCI conduct rules (advertising/solicitation; foreign firms) were not verified in this session. Get a legal opinion before any outcome-sharing or advocate-discovery feature.
- **Risk (high).** Crosswalk or which-code errors in criminal matters could cause missed limitation periods or wrong remedies. Mitigated by Tier-1 HITL, UNDETERMINED defaults and P8 checks.
- **Risk (medium).** The neutral-citation formats drift. Format tables are data, not code.

---

## References

- [IN-1] Copyright Act 1957, s.52(1)(q)–(r) (text). Indian Kanoon. https://indiankanoon.org/doc/1013176/ — verified
- [IN-2] Copyright Act 1957, s.2(k) "Government work" (text). Indian Kanoon search. https://indiankanoon.org/search/?formInput=title%3A%22Section%202%20in%20The%20Copyright%20Act%2C%201957%22 — verified
- [IN-3] Supreme Court of India. Eastern Book Company & Ors v. D.B. Modak & Anr, (2008) 1 SCC 1; AIR 2008 SC 809 (12 Dec 2007), paras 40–42. https://indiankanoon.org/doc/1062099/ — verified (re-checked in review)
- [IN-4] Constitution of India, Art. 141. https://indiankanoon.org/doc/882644/ — verified
- [IN-5] Constitution of India, Art. 144. https://indiankanoon.org/doc/1799967/ — verified
- [IN-6] Constitution of India, Art. 227. https://indiankanoon.org/doc/1331149/ — verified
- [IN-7] Constitution of India, Art. 20. https://indiankanoon.org/doc/655638/ — verified
- [IN-8] Constitution of India, Art. 123. https://indiankanoon.org/doc/1090693/ — verified
- [IN-9] Constitution of India, Art. 254. https://indiankanoon.org/doc/1930681/ — verified
- [IN-10] Constitution of India, Art. 348. https://indiankanoon.org/doc/928281/ — verified
- [IN-11] Official Languages Act 1963, s.7. https://indiankanoon.org/doc/958327/ — verified
- [IN-12] Supreme Court of India. Central Board of Dawoodi Bohra Community v. State of Maharashtra, (2005) 2 SCC 673 (17 Dec 2004), propositions (1)–(3). https://indiankanoon.org/doc/708017/ — verified
- [IN-13] Supreme Court of India. Trimurthi Fragrances (P) Ltd v. Govt of NCT of Delhi (19 Sep 2022). https://indiankanoon.org/doc/85806537/ — verified
- [IN-14] Supreme Court of India. National Insurance Co. Ltd v. Pranay Sethi, (2017) 16 SCC 680 (31 Oct 2017), para 30. https://indiankanoon.org/doc/139996215/ — verified
- [IN-15] Supreme Court of India. Union Territory of Ladakh v. Jammu & Kashmir National Conference (6 Sep 2023), para 35. https://indiankanoon.org/doc/175104903/ — verified
- [IN-16] Supreme Court of India. State of U.P. v. Synthetics and Chemicals Ltd, (1991) 4 SCC 139 (18 Jul 1991). https://indiankanoon.org/doc/1488034/ — verified
- [IN-17] Supreme Court of India. Kunhayammed v. State of Kerala, (2000) 6 SCC 359 (19 Jul 2000), conclusions (i)–(v). https://indiankanoon.org/doc/1940266/ — verified
- [IN-18] Supreme Court of India. Rupa Ashok Hurra v. Ashok Hurra, (2002) 4 SCC 388 (10 Apr 2002). https://indiankanoon.org/doc/854624/ — verified
- [IN-19] Supreme Court of India. Bengal Immunity Co. Ltd v. State of Bihar (6 Sep 1955). https://indiankanoon.org/doc/1629830/ — verified
- [IN-20] Supreme Court of India. Sarwan Singh Lamba v. Union of India, (1995) 4 SCC 546 (12 May 1995). https://indiankanoon.org/doc/538878/ — verified
- [IN-21] Supreme Court of India. East India Commercial Co. Ltd v. Collector of Customs, Calcutta, AIR 1962 SC 1893 (4 May 1962). https://indiankanoon.org/doc/1839963/ — verified
- [IN-22] Supreme Court of India. Sundarjas Kanyalal Bhatija v. Collector, Thane, AIR 1990 SC 261; 1989 SCR (3) 405 (13 Jul 1989). https://indiankanoon.org/doc/1931795/ — verified
- [IN-23] Supreme Court of India. S.I. Rooplal v. Lt. Governor, (2000) 1 SCC 644 (14 Dec 1999). https://indiankanoon.org/doc/1273655/ — verified
- [IN-24] Supreme Court of India. L. Chandra Kumar v. Union of India, (1997) 3 SCC 261 (18 Mar 1997). https://indiankanoon.org/doc/1152518/ — verified
- [IN-25] Supreme Court of India. Somaiya Organics (India) Ltd v. State of U.P. (17 Apr 2001) (quoting Golak Nath propositions). https://indiankanoon.org/doc/108182/ — verified
- [IN-26] Supreme Court of India. Mineral Area Development Authority v. Steel Authority of India, 2024 INSC 607 (14 Aug 2024), paras 24–25. https://indiankanoon.org/doc/96063944/ — verified
- [IN-27] Supreme Court of India. Shree Chamundi Mopeds Ltd v. Church of South India Trust Assn., (1992) 3 SCC 1 (29 Apr 1992). https://indiankanoon.org/doc/422729/ — verified
- [IN-28] Supreme Court of India. Krishna Kumar Singh v. State of Bihar (7 judges, 2 Jan 2017). https://indiankanoon.org/doc/107225908/ — verified
- [IN-29] Supreme Court of India. CIT v. Vegetable Products Ltd, (1973) 1 SCC 442 (29 Jan 1973). https://indiankanoon.org/doc/957191/ — verified
- [IN-30] Supreme Court of India. In re: Interplay between Arbitration Agreements under the Arbitration Act 1996 and the Indian Stamp Act 1899, 2023 INSC 1066 (7 judges, 13 Dec 2023). https://indiankanoon.org/doc/139003074/ — verified
- [IN-31] Karnataka High Court (Kalaburagi). Arunkumar v. State of Karnataka, Crl.P. 200913/2024, 2024:KHC-K:7531 (30 Sep 2024) (quotes BNS s.358 in full). https://indiankanoon.org/doc/47759402/ — verified
- [IN-32] Bharatiya Nagarik Suraksha Sanhita 2023, s.531. https://indiankanoon.org/doc/74791982/ — verified
- [IN-33] Bharatiya Sakshya Adhiniyam 2023, s.170. https://indiankanoon.org/doc/10673658/ — verified
- [IN-34] Supreme Court of India. Parvinder Singh v. Directorate of Enforcement, 2026 INSC 519 (19 May 2026), paras 26–34. https://indiankanoon.org/doc/46844204/ — verified
- [IN-35] Supreme Court of India. CBI v. Ramesh Chander Diwan, 2025 INSC 539 (22 Apr 2025), para 30. https://indiankanoon.org/doc/101752699/ — verified
- [IN-36] Supreme Court of India. Rajendra Bihari Lal v. State of U.P., 2025 INSC 1249 (17 Oct 2025). https://indiankanoon.org/doc/12774401/ — verified
- [IN-37] Supreme Court of India. Kasireddy Upender Reddy v. State of Andhra Pradesh, 2025 INSC 768 (23 May 2025). https://indiankanoon.org/doc/64477422/ — verified
- [IN-38] Supreme Court of India. Achin Gupta v. State of Haryana, 2024 INSC 369 (3 May 2024), paras 38–39. https://indiankanoon.org/doc/172613397/ — verified
- [IN-39] Gauhati High Court. Criminal appeal decided 19 Jun 2025 (IK title mis-parsed as "Page No.# 1/35 vs The State Of Assam And Anr"). https://indiankanoon.org/doc/160208619/ — verified
- [IN-40] Jharkhand High Court. Order of 19 Feb 2025 discussing IPC s.420 and BNS s.318(4). https://indiankanoon.org/doc/105667861/ — snippet
- [IN-41] Indian Kanoon section pages with "[Similar to …]" annotations: BNS ss.72, 103, 111, 113, 152, 304; BNSS ss.173, 307, 482, 528; BSA s.63. e.g. https://indiankanoon.org/doc/73182733/ (BNSS 482), https://indiankanoon.org/doc/99044874/ (BNSS 528), https://indiankanoon.org/doc/125020475/ (BSA 63), https://indiankanoon.org/doc/126533912/ (BNS 103), https://indiankanoon.org/doc/37266782/ (BNS 152), https://indiankanoon.org/doc/11650179/ (BNSS 307) — verified
- [IN-42] PRS Legislative Research. "The Bharatiya Nyaya (Second) Sanhita, 2023" bill track. https://prsindia.org/billtrack/the-bharatiya-nyaya-second-sanhita-2023 — verified
- [IN-43] Wikipedia. "Bharatiya Nyaya Sanhita, 2023" (358 sections; 20 new offences; 19 dropped). https://en.wikipedia.org/wiki/Bharatiya_Nyaya_Sanhita — verified (secondary)
- [IN-44] Ministry of Home Affairs. New criminal laws page (BNS/BNSS/BSA PDFs, e.g. /sites/default/files/2024-04/250883_english_01042024.pdf). https://www.mha.gov.in/en/commoncontent/new-criminal-laws — verified (links present)
- [IN-45] National Crime Records Bureau. "Flyers on New Criminal Laws" (ZIP). https://www.ncrb.gov.in/uploads/files/flyers-26022024.zip — verified (archive downloaded 2026-09-30; 10 thematic flyer PDFs, no section-level table)
- [IN-46] Code of Civil Procedure 1908, s.137. https://indiankanoon.org/doc/87116228/ — verified
- [IN-47] General Clauses Act 1897, s.6. https://indiankanoon.org/doc/1030013/ — verified
- [IN-48] Verdictum. "All Supreme Court Judgments to Have Neutral Citations" (23 Feb 2023) (neutral citations from 1 Jan 2023; retro phases; ~2,900 translated judgments; Delhi/Kerala HC systems — does not mention a uniform-HC-format request). https://www.verdictum.in/court-updates/supreme-court/neutral-citations-judgments-chief-justice-dy-chandrachud-1463966 — verified
- [IN-49] Supreme Court of India. Neutral Citation search page (date-range form with CAPTCHA), probed 2026-09-30. https://www.sci.gov.in/neutral-citation/ — verified
- [IN-50] Supreme Court of India. Homepage "latest judgments" view-pdf links (diary_no pattern), probed 2026-09-30. https://www.sci.gov.in/ — verified
- [IN-51] Wikipedia. "Neutral citation" — India section (reporter formats; 200+ law reports; NJRS). https://en.wikipedia.org/wiki/Neutral_citation — verified (secondary)
- [IN-52] Wikipedia. "High courts of India" (state/UT → HC and bench table). https://en.wikipedia.org/wiki/High_courts_of_India — verified (secondary)
- [IN-53] Wikipedia. "Languages with official recognition in India" (Hindi in HCs of Bihar, UP, MP, Rajasthan). https://en.wikipedia.org/wiki/Languages_with_official_recognition_in_India — snippet (secondary)
- [IN-54] IN doc analysis. Neutral citations extracted from HC judgments hosted on Indian Kanoon, sampled 2026-09-30 (e.g. docs 28899933, 58356618, 115370172, 106494537, 183818669, 22332753, 75969105, 158106960, 134652804, 153623724, 29261763, 54875004, 30668313, 87248603, 88578743, 20591891, 171878345, 93589483, 144875592). https://indiankanoon.org/doc/22332753/ (example) — verified (probe)
- [IN-55] Delhi High Court. Laksh Vir Singh Yadav v. Union of India & connected matters, W.P.(C) 1021/2016 (Sachin Datta J., 29 May 2026), para 1, masking principles (iii)–(v), paras 277, 279–287. https://indiankanoon.org/doc/4658201/ — verified
- [IN-56] Digital Personal Data Protection Act 2023, s.16 (text). https://dpdpa.com/dpdpa2023/chapter-4/section16.html — verified
- [IN-57] Digital Personal Data Protection Act 2023, s.17 (text). https://dpdpa.com/dpdpa2023/chapter-4/section17.html — verified
- [IN-58] Digital Personal Data Protection Act 2023, s.3(c)(ii) (via 02_P0 [P0-23]). https://www.dpdpa.com/dpdpa2023/chapter-1/section3.html — verified (by P0)
- [IN-59] AZB & Partners. "DPDP Rules 2025 notified" (13 Nov 2025; Rules 1, 2, 17–21 immediate; Rule 4 from 12 Nov 2026; Rules 3, 5–16, 22, 23 from 12 May 2027). https://www.azbpartners.com/?p=87799 — verified
- [IN-60] Khaitan & Co. "CERT-In Direction: Paradigm Shift in Cyber Incident Reporting" (Directions of 28 Apr 2022) (via 09_P7 [P7-7]). https://khaitanco.com/thought-leaderships/Indian-Computer-Emergency-Response-Team-Direction-Paradigm-Shift-in-Cyber-Incident-Reporting — verified (by P7)
- [IN-61] Vidhi Judicial. "Section 132 of the Bharatiya Sakshya Adhiniyam, 2023" (via 09_P7 [P7-8]). https://vidhijudicial.com/section-132-of-the-bharatiya-sakshya-adhiniyam,-2023.html — verified (by P7)
- [IN-62] Supreme Court Observer. In re: Summoning Advocates who give Legal Opinion or Represent Parties during Investigation of Cases and Related Issues, 2025 INSC 1275 (31 Oct 2025; Gavai CJI, K.V. Chandran, N.V. Anjaria JJ.; in-house counsel excluded) (via 09_P7 [P7-9]; re-checked in review). https://www.scobserver.in/supreme-court-observer-law-reports-scolr/re-summoning-advocates-who-give-legal-opinion-or-represent-parties-during-investigation-of-cases-and-related-issues/ — verified (by P7)
- [IN-63] MediaNama. "223 experts concerned about MeitY's stance on web scraping to train AI models" (Feb 2025) (via 02_P0 [P0-21]). https://www.medianama.com/2025/02/223-experts-concerned-about-meitys-stance-on-web-scraping-to-train-ai-models/ — verified (by P0)
- [IN-64] Indian Kanoon. API Service Description / Terms (via 02_P0 [P0-15]). https://api.indiankanoon.org/terms/ — verified (by P0)
- [IN-65] AWS Registry of Open Data. "Indian High Court Judgments" and "Indian Supreme Court Judgments" (CC-BY-4.0). https://registry.opendata.aws/indian-high-court-judgments/ ; https://registry.opendata.aws/indian-supreme-court-judgments/ — verified (pages reachable; licence per P0)
- [IN-66] Government of India. Government Open Data License – India (via 02_P0 [P0-24]). https://app.indiapost.gov.in/documents/media/OGD.pdf — snippet (503 on fetch)
- [IN-67] Bar & Bench. "Shardul Amarchand Mangaldas announces partnership with Harvey AI" (4 Jun 2025); "AZB & Partners announces adoption of Harvey AI" (10 Sep 2025) (via 20_CT [CT-26][CT-27]). https://www.barandbench.com/news/corporate/shardul-amarchand-mangaldas-announces-partnership-with-harvey-ai ; https://www.barandbench.com/news/corporate/azb-partners-announces-adoption-of-harvey-ai — verified (by CT)
- [IN-68] OpenAI. "Data controls in the OpenAI platform" (data residency: India storage yes / processing no) (via 13_XC [XC-5]). https://developers.openai.com/api/docs/guides/your-data — verified (by XC)
- [IN-69] Gala, J. et al. "IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22 Scheduled Indian Languages." TMLR 2023. https://arxiv.org/abs/2305.16307 — verified (by P1)
- [IN-70] Magesh, V., Surani, F., Dahl, M., Suzgun, M., Manning, C.D., Ho, D.E. "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools." 2024. https://arxiv.org/abs/2405.20362 — verified (by P1)
- [IN-71] National e-Governance Division (MeitY). "Nyaykosh: Law as Code." https://negd.gov.in/our_projects/nyaykosh-law-as-code/ — verified (by P1)
- [IN-72] TaxGuru. "Income-tax Act 2025 in force from 1 April 2026" (via 08_P6 [P6-38]). https://taxguru.in/income-tax/income-tax-act-2025-force-1st-april-2026.html — verified (by P6; commencement only)
- [IN-73] Buckeye Trust v. PCIT, ITA No. 1051/Bang/2024, ITAT Bangalore (orders 30 Dec 2024 and 12 Feb 2026) (via 20_CT [CT-48]). https://indiankanoon.org/search/?formInput=Buckeye%20Trust%20ITAT%20Bangalore — verified (by CT; existence and dates)
- [IN-74] Etcheverry, M., Real, T., Chavallard, P. "Algorithm for Automatic Legislative Text Consolidation." NLLP 2024 (via 03_P1 [P1-32]); Prior, M. et al. "Risks and Limits of Automatic Consolidation of Statutes." NLLP 2025 [P1-33]. https://aclanthology.org/2024.nllp-1.13 ; https://aclanthology.org/2025.nllp-1.29 — verified / snippet (by P1)
- [IN-75] Calcutta High Court. C.R.M.(A) 2354 of 2026, In re: Sadhan Ghosh (27 Aug 2026) (IK title mis-parsed as "Section 318 Of The Bharatiya Nyaya ... vs In Re: Sadhan Ghosh"). https://indiankanoon.org/doc/96134630/ — verified
- [IN-76] Vidhi Judicial. "Section 63 of the Bharatiya Sakshya Adhiniyam, 2023" (via 09_P7 [P7-10]). https://vidhijudicial.com/section-63-of-the-bharatiya-sakshya-adhiniyam,-2023.html — verified (by P7)
- [IN-77] Devgan.in. "BNS Section 103: Punishment for murder" (text of s.103(1)–(2); IPC 302 correspondence). https://devgan.in/bns/section/103/ — verified (secondary; official text at [IN-44])
- [IN-78] Supreme Court of India. Kusum Ingots & Alloys Ltd v. Union of India, (2004) 6 SCC 254 (28 Apr 2004). https://indiankanoon.org/doc/1876565/ — verified
- [IN-79] Supreme Court of India. State of Punjab v. Rafiq Masih (White Washer) (8 Jul 2014) (Art. 142 directions not a binding precedent). https://indiankanoon.org/doc/154195973/ — verified
- [IN-80] Wikipedia. "Ninety-ninth Amendment of the Constitution of India" (Arts. 124A–124C inserted; in force 13 Apr 2015 per S.O. 999(E); struck down 16 Oct 2015 in *Supreme Court Advocates-on-Record Assn. v. Union of India*, W.P.(C) No. 13 of 2015 (commonly reported as (2016) 5 SCC 1 *(reporter citation unverified)*); pre-amendment collegium system declared operative). https://en.wikipedia.org/wiki/Ninety-ninth_Amendment_of_the_Constitution_of_India — verified (secondary; added in final QC)
- [IN-81] Supreme Court Observer. "Challenge to the Abrogation of Article 370" (final judgment 11 Dec 2023, 2023 INSC 1058; C.O. 272 and C.O. 273 upheld). https://www.scobserver.in/court-case/article-370 — verified (secondary; added in final QC)
