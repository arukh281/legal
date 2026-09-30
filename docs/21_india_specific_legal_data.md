# 21 — India-Specific Legal Data: Sources, Licensing, Citations, Precedent Rules, Treatment, Criminal-Code Transition, Temporal Law, Languages, Compliance

**Abstract.** This document is the platform's *legal reference layer*. Other phases implement mechanisms. This one fixes the Indian legal facts and rules those mechanisms encode. It covers eight things:
1. What official sources exist and what we may lawfully do with them.
2. How Indian citations are formed and resolved: a formal grammar plus an alias strategy that includes observed neutral-citation formats for 20+ High Courts.
3. The doctrine of precedent as machine rules. P3's doctrine engine can execute these directly (`binding_on_forum`, AuthorityStatus inputs), and every rule cites the case that establishes it.
4. An Indian treatment vocabulary that beats KeyCite and Shepard's on granularity and honesty.
5. The IPC/CrPC/IEA → BNS/BNSS/BSA transition. This includes a 2026 Supreme Court holding that the unit of transition is the *proceeding*, not the case. That holding forces a spine change.
6. Point-in-time law: commencement, ordinances, state amendments, and the limits of India Code.
7. Multilingual realities.
8. Compliance: DPDP Act and Rules 2025, CERT-In, advocate privilege under BSA, and a May 2026 Delhi High Court right-to-be-forgotten judgment that directly binds legal-database design.

Each legal proposition carries a verified citation with a URL. Where Indian law is unsettled, the doc says so and maps the point to `UNDETERMINED` rather than guessing. The WebSearch budget for this session ran out before this doc began. Research therefore relied on direct fetches of primary sources (mostly Supreme Court and High Court texts on Indian Kanoon, and constitutional and statutory text) and on sources that sibling docs had already verified. Items we could not re-verify are marked *(unverified)*.

---

## 0. Conventions used in this document

- **Rule IDs.** `rul_IN_<area>_<n>` are doctrine rules for P3's DoctrineRule registry (P3 proposes the `rul_` prefix, 05_P3 §2.4 S3-5). Each rule has:
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
| **HC websites** (25 HCs, with permanent benches and circuit benches) | Judgments, cause lists | Heterogeneous | Daily | Varies; some geo-blocked (P0) | Same | Bench-level provenance. ★ The HC ↔ state/UT map is not 1:1. Examples: the Bombay HC covers Maharashtra, Goa, Dadra & Nagar Haveli and Daman & Diu, with benches at Nagpur and Aurangabad and a circuit bench at Kolhapur. The Gauhati HC covers Assam, Arunachal, Mizoram and Nagaland. The P&H HC covers Punjab, Haryana and Chandigarh. The Calcutta HC covers Andaman & Nicobar. The Madras HC covers Puducherry. The Kerala HC covers Lakshadweep. The J&K and Ladakh HC covers two UTs [IN-52]. | Drives `binding_on_forum` (§4) |
| **India Code** | Central and state Acts, subordinate legislation | HTML/PDF | Irregular ("re-typed and updated from time to time", P0) | Front page returned 200 to us; deep links failed from our egress | Acts may be reproduced only *with commentary or other original matter* (s.52(1)(q)(ii)) [IN-1]. See §2.2. | Current consolidated text. It is **not** a point-in-time source (§7). |
| **e-Gazette** (central) + state gazettes | Acts as enacted, ordinances, notifications, commencement orders | PDF | Weekly + extraordinary | Broken TLS chain (P0) | Gazette matter is freely reproducible *except* Acts of a legislature (s.52(1)(q)(i)) [IN-1] | **Primary source for commencement, amendments, ordinances.** It is the backbone of point-in-time law. |
| **MHA new-criminal-laws page** | BNS/BNSS/BSA official texts (PDFs dated 01-04-2024) [IN-44] | PDF | Static | Reachable | Government work | Authoritative text for the crosswalk |
| **NCRB** | "Flyers on New Criminal Laws" archive [IN-45] | ZIP | Static | Reachable | Government work | Candidate official crosswalk source *(contents not opened)* |
| **Tribunal portals** (NCLT/NCLAT, ITAT, CESTAT, NGT, CAT, APTEL, SAT, consumer commissions via e-Jagriti) | Orders | PDF/JSON | Daily | Mixed (P0: NCLT robots disallow `/search/`; e-Jagriti JSON API) | s.52(1)(q)(iv) covers "Tribunal or other judicial authority" [IN-1] | Tribunal layer of the hierarchy (§4) |
| **Nyaykosh** (NeGD) | Some laws as Akoma Ntoso XML | XML/REST | Unknown | Not reached (P0/P1) | Government | Optional structured statute seed [IN-71] |
| **AWS Open Data**: Indian HC judgments / Indian SC judgments | ~17.8M HC judgments; SC 1950– (per P0) | PDF + Parquet | Quarterly–daily (inconsistent, P0) | Stable S3 | **CC-BY-4.0** [IN-65] | Bulk backfill. Attribution required. |
| **Indian Kanoon API** | Judgments + statutes + IK metadata | JSON | Live | Paid per call | ToU permit RAG/fine-tuning use with attribution; 1-month termination (P0) [IN-64] | Gap-filler and cross-check. **Never the sole source of metadata** (see §3.6: IK title-parse errors). |
| **Commercial reporters** (SCC/SCC OnLine, AIR, Manupatra, etc.) | Reported judgments + editorial layers | Proprietary | — | Licence only | Editorial additions are copyrighted (EBC v Modak) [IN-3] | **Citation strings only** (facts). No text, headnotes or paragraphing. |

**Catalogue-level conclusions**
1. Every *legal-change* fact (commencement, amendment, ordinance, repeal) must come from the **Gazette**, never from a consolidated text.
2. Every *judgment* must come from a **court-issued copy**. That copy is the only lawful and authentic source of paragraph numbers (§2.3).
3. The HC → territory map is a first-class reference table (`court_jurisdiction(court_id, bench_id, territory_code, valid_from, valid_to)`). Benches and territories change: Andhra Pradesh and Telangana split on 1 Jan 2019, and J&K became J&K + Ladakh [IN-52].

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
- The Court also upheld protection for **headnotes** and editorial notes (P0 [P0-18]).

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
- **Status.** Single-judge decision. It binds courts and authorities under the Delhi HC's superintendence and is persuasive elsewhere (§4). *Appeal status not verified.*

**Design rule `rul_IN_PRIV_1`.** Every Work carries `access_restriction`:
```json
{ "name_search_suppressed": [{"party_entity_id":"ent_…","basis":"COURT_ORDER","order_ref":"wrk_…#p285","scope":"ALL_TENANTS","effective_from":"2026-06-12"}],
  "masked_expression_required": false,
  "court_prohibition": null }
```
- P2 must exclude suppressed party names from the *lexical name field and entity facets*, while case number, citation, court and date retrieval still work.
- P5 must not return the Work for a query whose only match is a suppressed name.
- P10 must not surface the name in digests.
- Statutory anonymity also applies:
  - BNS s.72 (disclosure of identity of victims of certain offences) [IN-41];
  - POCSO and JJ Act analogues *(not re-verified here)*.
  
  This anonymity is enforced at P1 as `needs_masking` detection on sexual-offence and juvenile matters. P1 then produces a masked Expression (`en.m1`) that becomes the display default.

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
- The Supreme Court e-committee also asked all High Courts to adopt a *uniform* neutral citation [IN-48].
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
1. Canonical key is `HCNC|{court_code}|{bench_code?}|{year}|{int(number)}|{bench_type?}`. The number is stripped of zero padding. `bench_type ∈ {DB, FB, ∅}`.
2. Whether single-bench and DB numbers share one sequence is **unknown**. The resolver therefore indexes both `…|DB` and the bare key. If both hit different Works, it raises `ALIAS_CONFLICT` for review. It never auto-merges (P1 §5.9 rule 3).
3. Slash and colon forms (`2023/MHC/4812` ≡ `2023:MHC:4812`) normalise to the same key.
4. Before matching, remove line breaks and hyphenation inside a candidate span when both sides match the code grammar. This is required by the Rajasthan observation.
5. The neutral-citation year is the **decision year**, including for retro-assigned citations *(inferred from retro examples; verify per HC)*.

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

**Alias trust tiers** stored as `identifier_alias.source` + `confidence`:

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

P3's doctrine engine computes `binding_on_forum` and feeds AuthorityStatus (05_P3 §2.2–2.3). P5 ranks with it; P6/P8 must state it correctly. Below are the rules, each tied to an authority we read. Paragraph numbers refer to the court copy where we saw them.

### 4.1 Rule registry

| Rule ID | Rule | Authority (verified) | Status |
|---|---|---|---|
| `rul_IN_PREC_01` | "The law declared by the Supreme Court shall be binding on all courts within the territory of India." | Art. 141 [IN-4] | SETTLED |
| `rul_IN_PREC_02` | "All authorities, civil and judicial, in the territory of India shall act in aid of the Supreme Court". SC law therefore also governs tribunals and quasi-judicial authorities. | Art. 144 [IN-5] | SETTLED |
| `rul_IN_PREC_03` | The SC is **not** bound by its own decisions: "all Courts" in Art. 141 "must refer to Courts other than the Supreme Court". | *Bengal Immunity Co. v. State of Bihar* (1955) [IN-19] | SETTLED |
| `rul_IN_PREC_04` | A decision of a Bench of **larger strength binds** later Benches of lesser or co-equal strength. | *Central Board of Dawoodi Bohra v. State of Maharashtra*, (2005) 2 SCC 673, proposition (1) [IN-12] | SETTLED |
| `rul_IN_PREC_05` | A lesser Bench **cannot doubt** a larger Bench. It can only request the CJ to place the matter before a larger Bench. A co-equal Bench may doubt, and the matter then goes to a larger Bench. Exceptions: the CJ's roster power, and a larger Bench already seized may reconsider. | *Dawoodi Bohra*, propositions (2)–(3) [IN-12] | SETTLED |
| `rul_IN_PREC_06` | Bench strength = judges on the Bench, **not** the size of the majority. "The majority decision of a Bench of larger strength would prevail over the decision of a Bench of lesser strength, irrespective of the number of Judges constituting the majority." | *Trimurthi Fragrances v. Govt. of NCT of Delhi* (SC, 19 Sep 2022) [IN-13] | SETTLED |
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
| `rul_IN_PREC_19` | The SC may **mould** retroactivity without declaring prospective overruling. In *MADA v. SAIL* (14 Aug 2024) it rejected prospective effect but directed that demands not operate on transactions before 1 Apr 2005, that payment be staggered over 12 years from 1 Apr 2026, and that pre-25-Jul-2024 interest and penalty be waived (paras 24–25). | [IN-26] | SETTLED (as an instance) |
| `rul_IN_PREC_20` | **Stay ≠ quash.** "The stay of operation of an order ... does not mean that the said order has been wiped out from existence". | *Shree Chamundi Mopeds v. Church of South India Trust Assn.* (1992) [IN-27] | SETTLED for orders. **Effect of a stay on a judgment's *precedential* value: CONTESTED** (no authority verified) |
| `rul_IN_PREC_21` | **Multi-opinion judgments.** The ratio is what a majority supports. Opinions may agree in part (e.g., *Krishna Kumar Singh v. State of Bihar* (7 judges, 2017): overruling *Bhupendra Kumar Bose* and *Venkata Reddy*, with several separate opinions differing on ordinance-laying consequences). | [IN-28] | SETTLED principle, hard extraction |
| `rul_IN_PREC_22` | **Tax canon**: "if two reasonable constructions of a taxing provision are possible that construction which favours the assessee must be adopted". Tribunals often invoke it when non-jurisdictional HCs conflict *(practice, unverified)*. | *CIT v. Vegetable Products* (SC, 1973) [IN-29] | CONTESTED as a *precedent-selection* rule |

### 4.2 `binding_on_forum` decision table

Inputs:
- **A (authority):** `court_level`, `court_id`, `bench_strength`, `decision_date`, and the proposition's `law_declared ∈ {YES, OBITER, SUB_SILENTIO, NON_SPEAKING_SLP, NO_MAJORITY}`.
- **F (forum):** `court_level`, `court_id`, `bench_strength?`, `territory`, `jurisdictional_hc?`.

Output ∈ `BINDING | PERSUASIVE | NOT_BINDING | UNDETERMINED`, plus `binding_basis.rule_ids[]`.

| # | Authority A | Forum F | Output | Rules |
|---|---|---|---|---|
| 1 | SC, `law_declared=YES` | Any HC, subordinate court, tribunal or authority | **BINDING** | 01, 02 |
| 2 | SC, `OBITER` | Any non-SC forum | **PERSUASIVE** + `weight=HIGH`, `contested=true` | 12 |
| 3 | SC, `SUB_SILENTIO` / `NON_SPEAKING_SLP` / `NO_MAJORITY` | Any | **NOT_BINDING** (as precedent; the parties remain bound) | 08, 10, 21 |
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

**Status modifiers** (P3 AuthorityStatus, applied after binding is computed):
- A pending reference or review does **not** change binding (rul 09). P10 shows it as an informational chip.
- `STAYED` → `CAUTION` (rul 20).
- `OVERRULES` with `effect=PROSPECTIVE|MOULDED` → the P3 date semantics apply (05_P3 §2.3), with conditions carried as anchored qualifiers (rul 18, 19).

```python
def binding_on_forum(A: AuthorityRef, F: Forum, prop: Proposition|None) -> Binding:
    if F is None or F.court_id is None: return UNDETERMINED(rule="PREC_13_FORUM_UNKNOWN")
    ld = prop.law_declared if prop else "YES"
    if A.level == "SC":
        if ld in {"SUB_SILENTIO","NON_SPEAKING_SLP","NO_MAJORITY"}: return NOT_BINDING(["PREC_08","PREC_10","PREC_21"])
        if F.level == "SC":
            if A.bench is None or F.bench is None: return UNDETERMINED(["PREC_04"])
            return BINDING(["PREC_04","PREC_06"]) if A.bench >= F.bench else PERSUASIVE(["PREC_03"])
        return PERSUASIVE(["PREC_12"], weight="HIGH", contested=True) if ld == "OBITER" else BINDING(["PREC_01","PREC_02"])
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
| *Parvinder Singh v. Directorate of Enforcement*, **2026 INSC 519** (19 May 2026; M.M. Sundresh, N. Kotiswar Singh JJ.) [IN-34] | s.531(2)(a) "is meant to give a prospective application to the provisions of the BNSS ... once a proceeding such as an appeal, application, investigation, inquiry or trial is initiated under the CrPC, then the same must meet its logical conclusion under the CrPC itself ... to avoid piecemeal application" (para 28). A BNSS substantive right "would definitely enure to the benefit of an accused against whom none of the proceedings envisaged under Section 531(2)(a) ... has been initiated" (para 29). "A mere ministerial act cannot be termed as an 'inquiry'" (numbering a complaint is not inquiry; cognizance is application of judicial mind) (para 34). The first proviso to BNSS s.223(1) (hearing before cognizance) is **substantive**. CrPC ss.200–205 (now BNSS ss.223–228) apply to PMLA complaints, following *Kushal Kumar Agarwal*, 2025 SCC OnLine SC 1221. |
| *CBI v. Ramesh Chander Diwan*, **2025 INSC 539** (Dipankar Datta, Manmohan JJ.) [IN-35] | Because of s.531 BNSS, "pending proceedings are to be continued under the repealed law". The Court declined liberty to seek BNSS s.218 deemed sanction and reserved liberty to seek sanction under the CrPC (para 30). |
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

### 6.4 Crosswalk data model

`CORRESPONDS_TO` is a Tier-1 assertion (spine §F). P3 owns storage. This doc fixes the semantics.

```ts
type Correspondence = Assertion & {
  predicate: "CORRESPONDS_TO";
  subject: AnchorId;           // old provision, e.g. wrk_IPC/en@2024-06-30#sec-498A
  object:  AnchorId | null;    // new provision, e.g. wrk_BNS/en@2024-07-01#sec-85 ; null for OMITTED
  qualifiers: {
    change_type: "SAME_RENUMBERED" | "SAME_TEXT_SPLIT" | "MERGED" | "SPLIT" | "MODIFIED_SCOPE"
               | "MODIFIED_PENALTY" | "REPLACED_BY_DIFFERENT_OFFENCE" | "FUNCTIONAL_ANALOGUE"
               | "NEW_NO_PREDECESSOR" | "OMITTED";
    group_id?: string;         // binds the 1→n or n→1 members of one mapping (498A → 85 + 86)
    granularity: "SECTION" | "SUBSECTION" | "CLAUSE";
    text_similarity?: number;  // normalized alignment score old↔new text (P1 diff)
    penalty_delta?: "SAME" | "HIGHER" | "LOWER" | "DIFFERENT_KIND";   // drives Art.20(1) warnings
    chain_prev?: AssertionId;  // CrPC1898 s.561A → CrPC s.482 → BNSS s.528
    source_kind: "GAZETTE_TEXT_DIFF" | "OFFICIAL_TABLE" | "JUDICIAL_STATEMENT" | "THIRD_PARTY" | "EDITORIAL";
  };
};
```

**`PRECEDENT_CARRIES_TO`** (derived, P3 S3-4). A judgment interpreting old provision X carries to new provision Y with this status:
- `GOOD` if `change_type ∈ {SAME_RENUMBERED, SAME_TEXT_SPLIT}` and `text_similarity ≥ 0.97`, or if a judicial pari-materia statement exists (e.g. [IN-36]).
- `CAUTION` + `reason_code=PROVISION_MODIFIED` for the MODIFIED_* types.
- No carry for `REPLACED_BY_DIFFERENT_OFFENCE`, `NEW_NO_PREDECESSOR` or `OMITTED`.

**Evidence sources, strongest first**
1. **Gazette text diff** of the MHA/Gazette texts [IN-44], aligned by P1.
2. **Judicial statements** harvested by P1 (`correspondence_hint`: "now Section …", "corresponding to", "in pari materia"), e.g. [IN-34][IN-36]–[IN-39].
3. **Official tables.** The NCRB flyers [IN-45] are unopened. The BPR&D handbooks are *unverified* because the site reset our connection.
4. **Third-party annotations.** Indian Kanoon marks sections "[Similar to Section 438 from Old CrPC]" etc. [IN-41]. Use these only as a cross-check under the IK ToU.

**Every mapping is human-verified before it is shown as definitive** (Tier 1).

### 6.5 Worked crosswalk (verified rows only; others must be built from text diff + review)

| Old | New | change_type (our classification) | Evidence |
|---|---|---|---|
| IPC 302 | BNS 103 ("Punishment for murder") | SAME_RENUMBERED (sub-section 103(1)) | [IN-39][IN-41] |
| IPC 420 | BNS 318(4) | SAME_RENUMBERED, `granularity=SUBSECTION` (SC cites "318") | [IN-40] snippet; [IN-37] |
| IPC 409 / 120-B | BNS 316(5) / 61(2) | SAME_RENUMBERED | [IN-37] |
| IPC 498A | BNS 85 + 86 | SAME_TEXT_SPLIT (`group_id`) | [IN-38] |
| IPC 124A (sedition) | BNS 152 ("Act endangering sovereignty, unity and integrity of India") | REPLACED_BY_DIFFERENT_OFFENCE, **no precedent carry** | [IN-42][IN-41] |
| IPC 377 | — | OMITTED (BNS "does not retain section 377") | [IN-42] |
| IPC 497 (adultery) | — | OMITTED | [IN-42] |
| — | BNS 111 (organised crime), 113 (terrorist act), 304 (snatching); murder or grievous hurt by five or more persons on specified grounds (sub-section of s.103, *number unverified*) | NEW_NO_PREDECESSOR | [IN-41][IN-42] |
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
| **Enactment ≠ commencement** | Acts commence on notified dates, often in stages. The DPDP Act illustrates this: Rules notified 13 Nov 2025; some sections in force immediately; consent-manager provisions after 12 months; core obligations after 18 months (~13 May 2027) [IN-59]. The Income-tax Act 2025 is in force from 1 Apr 2026 (06_P6 [IN-72]). | `LegislativeAction(kind=COMMENCES, target_anchor_set, effective_from, gazette_ref)`. Provision-level `valid_from`. Never use assent date as `valid_from` (consistent with P2 §5). |
| **Ordinances** | Same force as an Act, but an ordinance "shall cease to operate at the expiration of six weeks from the reassembly of Parliament" unless disapproved earlier, and may be withdrawn (Art. 123(2)) [IN-8]. Art. 213 is the state analogue. Repeated re-promulgation is a "fraud on the Constitution" (*Krishna Kumar Singh*, 7-J, 2017), with separate opinions differing on what survives lapse [IN-28]. | Ordinance expression `valid_to = min(withdrawal, disapproval, reassembly+6 weeks)`. `valid_to` stays *provisional* until the Gazette shows replacement, lapse or disapproval. Survival of effects after lapse → `CONTESTED` flag, not auto-inference. |
| **State amendments to central Acts** (Concurrent List) | A repugnant state law on a Concurrent List matter that has received Presidential assent "shall prevail in that State" (Art. 254(2)) [IN-9]. | **Territorial expressions.** The same Work has different text in different states on the same date (spine change C3). |
| **Repeal and savings** | GCA s.6: a repeal does not revive, does not affect previous operation or accrued rights/liabilities, and saves pending proceedings "unless a different intention appears" [IN-47]. BNS s.358(4) expressly preserves s.6 [IN-31]. | Repeal ends the expression's `valid_to` for *new* conduct. Saved rights keep the old expression **operative** for events before repeal. P3 therefore evaluates by event date, not query date. |
| **Retrospective and validating Acts** | Legislatures amend with retrospective effect to override judgments (`LEGISLATIVELY_OVERRIDDEN_BY`, §5) *(general practice; no specific instance re-verified here)*. | Bitemporal: a retrospective amendment enacted on T2 with `valid_from = T0 < T2` is recorded at T2. Queries `as_known_at < T2` see the old law (spine §E). |
| **Judicially moulded retroactivity** | *MADA* (2024) moulded the past effect of a declaration [IN-26]. | `effect=MOULDED` + anchored `conditions[]` on the assertion (spine change C4). |
| **Constitution amendments** | Same pattern as Acts: amendment Act → commencement → articles substituted or inserted. | `art-21A`-style anchors with `@date` (spine §C). |
| **India Code limits** | India Code is a consolidated text "re-typed and updated from time to time". We found no documented point-in-time versioning (02_P0). | India Code = **current-text cross-check only**. Historical versions are *reconstructed* from Gazette amendment instructions (P1 amending-Act grammar). Automatic consolidation has known risks, so each reconstructed version is diffed against any available official consolidated snapshot [IN-74]. |

### 7.2 Point-in-time resolution contract

`resolve(anchor, legal_date, territory)` does four things:
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
1. **Authoritative-expression flag.** For HC judgments under OLA s.7, the pronounced-language text and the HC-issued English translation are *both* Expressions of one Work (`hi`, `en`). `authoritative ∈ {ORIGINAL, OFFICIAL_TRANSLATION, OUR_MT}`.
   - Which of `hi` and `en` prevails on conflict is **not settled** by any authority we verified → `CONTESTED`.
   - P6/P8 quote the ORIGINAL and show the official translation alongside it.
2. **Machine translation is never a citation source.**
   - `OUR_MT` expressions (e.g. IndicTrans2 [IN-69]) exist for retrieval and for the lawyer's reading aid only.
   - Anchors are aligned to the original's paragraphs via P1's alignment record.
   - A claim anchored to `OUR_MT` fails P8 verification by design.
3. **For statutes**, English is authoritative (Art. 348(1)(b)). Hindi statute texts are official translations (Authoritative Texts (Central Laws) Act, 1973 *(not re-verified)*). The display follows s.52(1)(r) limits for any translation we generate (§2.1).
4. **Script and numeral normalisation** (Devanagari digits; "धारा" = section; Latin-script citations inside Hindi judgments) happen before citation extraction (P1 §5.8).

---

## 9. Compliance

| Regime | Verified content | Engineering consequence |
|---|---|---|
| **DPDP Act 2023** | **s.3(c)(ii)** excludes personal data made publicly available by the Data Principal or under a legal obligation to publish. Whether court publication qualifies is arguable (02_P0 [IN-58]). **s.16(1)**: the Central Government "may, by notification, restrict the transfer of personal data ... to such country or territory outside India as may be so notified" (a negative list). **s.16(2)**: sectoral laws with stricter transfer rules still apply [IN-56]. **s.17(1)(a)** exempts processing "necessary for enforcing any legal right or claim"; **17(1)(b)** processing by courts and tribunals; **17(2)(b)** research, archiving or statistical purposes where the data is not used for decisions about the principal [IN-57]. | PLC judgments are treated as personal data with masking and takedown support (§2.5). TPL processing for a client's matter relies on s.17(1)(a) for the *legal claim* purpose. It is **not** a blanket exemption for our product analytics or model training: P9's Privacy Gate stays mandatory. Cross-border LLM calls are lawful unless the destination is notified, but client contracts and CERT-In logs still drive India residency (13_XC). |
| **DPDP Rules 2025** | Notified **13 Nov 2025**. Stage 1 immediate (Board, definitions). Consent-manager provisions (s.6(9), Rule 4) from **~13 Nov 2026**. Core obligations, including notice, consent, breach notification, retention/erasure and cross-border Rule 15, from **~13 May 2027** [IN-59]. | Roadmap (22) must have DPDP-core controls live before May 2027: breach runbook, retention schedules, data-principal request handling for any PLC personal data (masking) and TPL data. |
| **CERT-In Directions, 28 Apr 2022** (IT Act s.70B(6)) | Cyber incidents reported within **6 hours**; ICT logs kept **180 days within India**; clock sync (09_P7 / 13_XC [IN-60]) | Log pipeline region-pinned to India. Incident runbook with a 6-hour SLA (13_XC). |
| **Advocate privilege: BSA ss.132–134** (formerly IEA ss.126–129) | s.132 protects professional communications and extends to advocates' clerks and employees (09_P7 [IN-61]). *In re: Summoning Advocates...*, **2025 INSC 1275** (31 Oct 2025) laid down the scope of s.132 protection against investigative summons, including the position of in-house counsel (09_P7/11_P9 [IN-62]). | Privilege class on every TPL object (spine `privilege_flags`). The vendor (us) is treated as an agent within the advocate's privilege circle by contract. **Whether a SaaS vendor's staff count as "employees" of the advocate under s.132 is untested → CONTESTED.** This is the core argument for customer-managed keys and private deployment options (P7). |
| **Right to be forgotten / masking** | *Laksh Vir Singh Yadav* (Delhi HC, 2026) directs name-search restriction for legal databases [IN-55] | `access_restriction` (§2.5, spine change C6) |
| **Hallucinated citations in Indian fora** | Documented Indian instance: an ITAT Bangalore order (Dec 2024) was recalled after it was reported to cite non-existent judgments (20_CT [IN-73]) | Justifies P8's hard gate. Also a sales argument: Indian benches now notice fake citations. |
| **Data residency and on-prem demand** | No general DPDP localisation (s.16 negative list) [IN-56]. Model providers differ: one major provider offers India *storage* but not India *processing* (13_XC [IN-68]). Top Indian firms (Shardul Amarchand Mangaldas, AZB) adopted a US SaaS legal-AI vendor in 2025 (20_CT [IN-67]). | Evidence suggests **SaaS in an India region is acceptable to large firms** when security is strong. Private-cloud or on-prem is a premium tier for PSU and government-adjacent or high-sensitivity matters, not the default *(demand split unverified; validate with the design partner, 22_roadmap)*. |

---
## 10. Design implications per phase

### 10.1 Phase-by-phase obligations

| Phase | Must implement (from this doc) |
|---|---|
| **P0** | Gazette-first capture for all legal-change events (§1, §7). Capture court-prohibition, in-camera and masking signals and `terms_ref`. Never circumvent CAPTCHAs (`rul_IN_ACCESS_1`). Seed the `court_jurisdiction` table (25 HCs, benches, time-versioned) [IN-52]. Harvest SC `diary_no` from `view-pdf` URLs [IN-50]. Obtain each HC's neutral-citation notification (Gujarat, Patna, Telangana, AP and Sikkim formats unobserved). |
| **P1** | Grammar §3.3 incl. slash/colon, zero-padding, `-DB/-FB`, line-break repair. Year-window check for publication-year reporters (§3.1). Opinion segmentation from the court copy only (EBC ¶41). `AMBIGUOUS_ACT` for post-2024 "482"-type mentions (§6.5). Harvest `correspondence_hint`s. Masked expressions for BNS s.72-type matters. `law_declared` signals (SLP non-speaking; speaking-order law). Hindi and regional cue lexicons. |
| **P2** | Territory-aware statute chunks (`valid_from/valid_to` + `territory`). Suppressed-name exclusion from lexical name fields and facets (§2.5). Index `OUR_MT` expressions with an `authoritative` flag so retrieval can hit them but citation cannot. |
| **P3** | Rule registry §4.1 and decision table §4.2. Competence check on OVERRULES (§5.3). `DISMISSES_IN_LIMINE` ≠ `AFFIRMS`. `effect=MOULDED`. Crosswalk model §6.4 with Tier-1 HITL. `PRECEDENT_CARRIES_TO` derivation. `access_restriction` on Work. Never machine-declare per incuriam. |
| **P4** | Re-run AuthorityStatus when a reference is answered, a stay is vacated, or an ordinance lapses (timer events at reassembly+6 weeks). Backfill: re-test pre-May-2026 "which procedure" treatments against *Parvinder Singh*. Propagate takedown and masking within 2 weeks. The Delhi HC direction gave two weeks (para 284) [IN-55]. |
| **P5** | Rank by `binding_on_forum`. Never collapse to court level. Treat `UNDETERMINED` forums with a generic-HC profile plus a warning (as P5 already does). Fire the I8 CROSSWALK intent for both codes. Apply date-per-stage (§6.3). Suppress name-only hits on restricted Works. |
| **P6** | The procedural agent uses `governing_code()` per stage. Memos state *which code and why* with the savings anchor (BNSS s.531(2)(a) ¶ / *Parvinder* ¶28). Memos distinguish BINDING from PERSUASIVE in claim text. SC obiter is phrased as "strongly persuasive" (rul 12, contested). |
| **P7** | `MatterContext` carries a proceedings timeline (initiation dates per stage), not just `cause_of_action`. Privilege flags per BSA s.132. Regional-language district-court orders are the norm in case files (§8). |
| **P8** | Block claims anchored to `OUR_MT`. Check the stated binding status against P3. Check "which code" claims against `governing_code()`. Treat a false red flag as an error class alongside missed negative treatment. |
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
| **Legal-risk red team** | A bare-Act export breaches s.52(1)(q)(ii). Reporter paragraphing leaks via a third-party dataset. Name search on RTBF-protected parties. | "Original matter" requirement on statute outputs (§2.1). A provenance filter bans reporter-derived text (§2.2). `access_restriction` (§2.5). |

### 10.3 Evaluation metrics owned by this doc (feed P8)

- **Doctrine-rule accuracy.** `binding_on_forum` agreement with partner-firm lawyers on ≥300 (authority, forum) pairs stratified over the rows of table §4.2. Target ≥98% on SETTLED rows. On CONTESTED rows, 100% `contested=true` surfaced.
- **False-red-flag rate.** NEGATIVE/PARTIAL_NEGATIVE shown where lawyers judge the proposition good for the forum. Target <1% of flagged items, tracked separately from the missed-negative rate.
- **Crosswalk precision.** 100% on displayed-definitive mappings (HITL). Coverage = share of IPC/CrPC/IEA sections with a reviewed mapping. Target 100% before GA of the criminal module.
- **Which-code accuracy** on a gold set of ≥100 transition scenarios (built with the partner firm from real FIR/charge-sheet timelines). Target ≥97%, and 0 confident answers on UNDETERMINED cases.
- **Citation resolution by scheme.** Precision ≥99.5% for T0/T1. Recall reported per HC neutral-citation format.

### 10.4 Proposed spine changes

| # | Target | Change | Justification |
|---|---|---|---|
| C1 | §H AuthorityView / `binding_on_forum` | **Endorse P3 S3-2** (`UNDETERMINED`, `binding_basis{rule_ids, contested}`) and add `binding_basis.conflict: LARGER_BENCH\|EARLIER_COEQUAL\|UNRESOLVED` | Rules 04–09. Contested rules (12, 16, 20, 22) must surface as contested. |
| C2 | §H ResearchQuery + MatterContext | Add `temporal_context{ substantive_event_date?, proceedings[]{stage, initiated_on, initiation_kind, concluded_on?}, filing_date? }`. `as_of_legal_date` stays as a default. | *Parvinder Singh* (2026 INSC 519): the transition unit is the proceeding. BSA s.170 and BNSS s.531 key on pending proceedings, and Art. 20(1) keys on the offence date. One date cannot express this. |
| C3 | §B/§C expression_key + point-in-time resolution | Statute `expression_key = lang@YYYY-MM-DD[~TERR]` (e.g. `en@2019-06-06~UP`). Anchor resolution takes `(date, territory)`. Territory codes = ISO 3166-2:IN. | Art. 254(2) state amendments make the text territory-dependent. P3's `IN_FORCE_IN` covers extent but not *text variants*. |
| C4 | §F Assertion qualifiers (P3 S3-1 `effect`) | Add `effect=MOULDED` with `conditions[]{text, anchor_id}` | *MADA* 2024 [IN-26]: retroactivity limited by date, instalments and waivers. That is neither prospective nor fully retrospective. |
| C5 | §F `CORRESPONDS_TO` qualifiers | Fix the `change_type` enum, `group_id`, `granularity`, `penalty_delta`, `chain_prev` and `source_kind` as in §6.4 | Needed for 1→n splits (498A → 85+86), chains (561A → 482 → 528), and Art. 20(1) warnings. |
| C6 | §B Work + §G events | Add `access_restriction{name_search_suppressed[], masked_expression_required, court_prohibition}` and event `work.access_restricted.v1` (P0/P3/ops → P2, P5, P10) | Delhi HC 2026 [IN-55]; s.52(1)(q)(iv) court prohibition [IN-1]; BNS s.72. |
| C7 | §D identifier_alias | `NEUTRAL_HC` value normalised as `{court_code}\|{bench_code}\|{year}\|{n}\|{bench_type}`. Add schemes `SCC_SUPP`, `SCC_SERIES`, `AIR_SCW`, `AIRONLINE`, `NJRS`. `SC_DIARY_NO` format `n/yyyy`. | Observed formats §3.1–3.2 [IN-51][IN-54]. |

### 10.5 Open questions and risks

- **Q1.** Does s.52(1)(q)(ii) ("together with commentary") constrain API or bulk exports of statute text? This is untested. Get a legal opinion before a public statute API launches.
- **Q2.** May IK-derived metadata ("Equivalent citations") seed our alias tables under the IK ToU? Get written confirmation. Until then, use it for cross-check only.
- **Q3.** Is a SaaS vendor within the BSA s.132 privilege circle? This is untested. It drives the default deployment (P7) and contract language.
- **Q4.** The precedential effect of an SC stay of an HC judgment (rul 20) and HC-declared "prospective" overruling (rul 18) have no verified authority. Both stay CONTESTED.
- **Q5.** Neutral-citation numbering: do single-bench and DB judgments share one sequence per HC? Get the per-HC notifications (P0 task).
- **Q6.** Official IPC/CrPC/IEA correspondence tables: get the BPR&D and NCRB documents from India egress and diff them against our text alignment.
- **Q7.** Delhi HC RTBF judgment: track any appeal or SC position. The design already complies, so this is low risk.
- **Risk (high).** Crosswalk or which-code errors in criminal matters could cause missed limitation periods or wrong remedies. Mitigated by Tier-1 HITL, UNDETERMINED defaults and P8 checks.
- **Risk (medium).** The neutral-citation formats drift. Format tables are data, not code.

---
