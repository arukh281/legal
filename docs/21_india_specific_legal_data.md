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
| **Nyaykosh** (NeGD) | Some laws as Akoma Ntoso XML | XML/REST | Unknown | Not reached (P0/P1) | Government | Optional structured statute seed [IN-72] |
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
- A Calcutta HC anticipatory-bail order is titled "**Section 318 Of The Bharatiya Nyaya ... vs In Re: Sadhan Ghosh**" [IN-76].
- A Gauhati HC criminal appeal is titled "**Page No.# 1/35 vs The State Of Assam And Anr**" [IN-39].

IK "Equivalent citations" lines mix full reports with notes of cases (`AIHC NOC`) [IN-3]. **Rule `rul_IN_META_1`:** party, court, date and citation metadata is *triangulated* (P1 §5.4). A third-party field never overrides a T0 field.

---
