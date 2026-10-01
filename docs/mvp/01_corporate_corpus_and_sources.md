# MVP 01 — Corporate Corpus and Sources

**Scope.** This document sets out which public legal sources the MVP ingests for an Indian corporate-law firm, how each is acquired lawfully, and what each costs. It also re-verifies the "fresh law" named in the brief.
**Method.** Every site was probed fresh on **2026-10-01** from this session's egress, which is a non-Indian cloud egress behind an agent proxy. For each site we fetched robots.txt, the policy pages, listing pages and sample PDFs, and counted records. Each claim is tagged `verified` (fetched and read), `snippet` (search result only) or `unverified`.
**Upstream.** This document reuses the blueprint's legal gate, LegalProfile and source catalogue (02_P0 §2.1, §3–§5, §10) and the licensing analysis (21_india §1–§2). It changes the blueprint where the fresh probes contradict it; see §0.3.
**Feeds:** 03 (source registry rows), 05/06 (test corpus), 07 (counsel questions, §7.2), 08 (cut list).

---

## 0. Summary

### 0.1 Decisions

| # | Decision |
|---|---|
| D1 | The corpus is **corporate-law only**: SC, NCLAT, NCLT, Delhi HC and Bombay HC (company, commercial and arbitration case types), SEBI quasi-judicial orders, SAT (thin), CCI (optional), 16 Acts, about 60 rules and regulations, and four regulator feeds. |
| D2 | **No CAPTCHA is ever solved by a machine.** Every CAPTCHA-gated path (SC search and cause list, NCLT order-by-date, SAT orders, Delhi HC judgment search, SCR) is closed to automation. Coverage gaps are filled from open datasets, IBBI's mirror, a licensed API, partner uploads or manual capture of single watched matters. |
| D3 | **Bulk history comes from open bulk sources:** the AWS SC and HC datasets (CC-BY-4.0) and IBBI's order mirror. **Daily deltas come from official listings** that are open and robots-permitted: the SC homepage widget, the NCLAT display board, IBBI orders, SEBI RSS and listings, the NCLT and NCLAT cause-list PDFs, and the RBI RSS. |
| D4 | **Point-in-time versioning** is built only for the IBC (the mandatory 2026 test case) and for the IBBI CIRP and Liquidation Regulations, where IBBI publishes dated consolidated snapshots. Every other instrument is held as current consolidated text with a displayed "law current to" date. |
| D5 | **India Code has moved to `indiacode.gov.in`** (DSpace 9.1) and exposes a public REST API. It is the primary source for Act text. Its section-level records lag its full-Act PDFs, so the PDF is canonical (§3.1). |

### 0.2 Headline numbers (counts observed 2026-10-01)

| Source | Count |
|---|---|
| IBBI order mirror | NCLT **31,792**; NCLAT **5,700**; SC **844**; HC **612** |
| SEBI enforcement orders | **30,957** in total, including AO 12,007, WTM/Chairperson 6,427, settlement 2,001, courts 1,118, ED/CGM 442 and SAT 2,447 (the SAT set stops in 2015) |
| SEBI circulars | 2,802, plus 134 master circulars |
| CCI | 1,246 antitrust orders; 1,472 combination orders and notices |
| SC dataset (AWS) | Only **214** judgments for 2026, against **2026 INSC 1072** issued by 30 Sep 2026 |
| Delhi HC (AWS) | 50,414 rows for 2025, of which about 6–7k are corporate, commercial or arbitration |
| Bombay HC Original Side (AWS) | 74,621 rows for 2025, of which 14,370 are commercial or arbitration (about 4.3k final) |

The MVP corpus is about **175k documents, about 1.9M pages and about 0.8B tokens** (§6).

### 0.3 Contradictions with the brief and the blueprint

1. **Corporate Laws (Amendment) Bill 2026.** The brief has it as introduced on 23 Mar 2026 and referred to a JPC. It has moved on: the **JPC presented its report on 3 Aug 2026**, and the Bill has not passed as of 1 Oct 2026 [R43].
2. **IBC (Amendment) Act 2026.** The brief's list of provisions not yet notified is **confirmed**. However, it is incomplete:
   - Further provisions of the amending Act are also not notified (amending ss. 7, 34(a)(i)–(ii), 45, 47, 60, 67, 69(b), 70(b)(xx)).
   - The notification also brought into force two **omissions** that affect deadline rules: IBC ss.38–42 (liquidation claims, including the s.42 appeal) and Chapter IV of Part II (fast-track, ss.55–58) [R19][R20]. See §5.
3. **India Code** moved from `indiacode.nic.in` to `indiacode.gov.in`, and the old host now shows a migration notice [R38]. Its `last_modified` metadata is unreliable (IBC shows 2024-07-25 although the PDF includes the 2026 amendments), and its **section-level text for IBC s.7 is still the pre-2026 text** [R39].
4. **The SC AWS dataset is not "SC 1950–present".** It holds the **SCR-reported subset** (about 570–900 judgments a year), and its 2026 partition stops at 25 May 2026 [R24–R26]. Non-reportable judgments have to come from sci.gov.in.
5. **The AWS HC dataset is near-daily, not quarterly, for Delhi and Bombay.** The Delhi 2026 partition was updated on 2026-09-28 with decisions up to 28 Sep 2026 [R29]. The registry still says "Quarterly" [R27].
6. **Delhi HC.** P0 recorded a CAPTCHA-free judgment listing. Today the judge-wise search has a CAPTCHA, and the "Latest Judgments" page returned "An error occurred while fetching data" [R31].
7. **SEBI's mirror of SAT orders ends in Jul 2015** [R35]. SAT's own `sat.gov.in` still returns **503**. The new portal `satweb.sat.gov.in` gates all four order searches behind a CAPTCHA [R33].
8. **About a third of the IBBI-hosted NCLT copies we sampled are image-only and need OCR** (1 of 3 NCLT samples). Others are re-rendered Word or Google-Docs PDFs. None of the samples was a bench-signed original [R14].

---

## 1. Scope and principles

| Principle | Rule for the MVP |
|---|---|
| Corporate slice | Ingest only the fora, case types and instruments in §2–§4. Anything else enters only as a cited authority fetched on demand (SC/HC/IK gap-fill) or as a partner upload. |
| Official sources first | Use the court- or regulator-issued bytes where an open route exists (`provenance_tier = OFFICIAL_PRIMARY`). Use official mirrors (IBBI) as `OFFICIAL_AGGREGATOR`, CC-BY datasets as `OPEN_DATASET`, and Indian Kanoon only as `LICENSED_THIRD_PARTY` gap-fill. Never ingest reporter text (SCC, Manupatra): EBC v. Modak (21_india §2.2). |
| Legal gate per source | No adapter runs without an `APPROVED` LegalProfile (02_P0 §2.1b) that names `permitted_access_modes`, the `rights_class` and a `terms_ref` pointing to archived ToU and robots snapshots. The profiles proposed here are `PROVISIONAL` until counsel signs (§7.2). |
| Access-control signals | CAPTCHA, login, robots `Disallow` and WAF blocks are treated as "no" (21_india `rul_IN_ACCESS_1`). **No CAPTCHA solving, rotating proxies or UA spoofing to evade blocks.** CSRF tokens and session cookies issued to every browser are not access control (see the NCLAT row). |
| Politeness | Declared UA with contact address; at most 1 request per 2–3 s per host; backfills at night IST; conditional GETs. |
| Provenance | Every capture stores `raw_id` (sha256), URL, `fetched_at`, `terms_ref` and `rights_class`. A document's **order date comes from the document**, never from the mirror's upload date (an IBBI sample was uploaded 4 calendar days after the order date; see §2.4). |
| Uncertified copies | Mirror copies (IBBI) and dataset copies (AWS) are flagged `flags.uncertified = true`. Deadline features (02/05) must not treat the upload date as the date of an order or of a certified copy. |

**Rights classes used.** These come from blueprint D9; doc 03's `default_rights_class` uses the same list.

| Class | Meaning |
|---|---|
| `OFFICIAL` | Court, regulator or government bytes |
| `OPEN_LICENSED` | CC-BY datasets; PRS |
| `LICENSED_RESTRICTED` | Indian Kanoon API |
| `THIRD_PARTY_LINK_ONLY` | Reporters and news; store headline, URL and timestamp only |
| `USER_UPLOADED` | Partner documents |

---

## 2. Courts and tribunals

**Legend.**
- **Access modes:** `OPEN` (official listing), `BULK_DATASET`, `LICENSED_API`, `HUMAN_ASSISTED` (a person fetches one item and solves any CAPTCHA personally; needs counsel sign-off), `PARTNER_CONTRIBUTED`.
- **Risk:** L means an open listing with a statutory basis (Copyright Act s.52(1)(q)(iv) for judgments). M means a ToU or permission question. H means do not automate.
- **`terms_ref`:** an archived snapshot ID, `tou_<source>@2026-10-01`, to be captured as WARC at onboarding.

### 2.1 Supreme Court of India (sci.gov.in, SCR, AWS SC dataset)

| Item | Finding (2026-10-01) |
|---|---|
| What's there | Judgments and daily orders as PDF, cause lists, case status and the neutral-citation lookup. The SCR portal carries reported judgments with official headnotes [R21][R23]. |
| Open route | **The homepage "latest judgments/orders" widget** lists `view-pdf/?diary_no={diary}{year}&type=j\|o&order_date=YYYY-MM-DD` links. On 1 Oct it showed 25 judgments (22–30 Sep) and 22 orders for 30 Sep. The underlying `sci-get-pdf/?diary_no=…&type=j&order_date=…` returns `application/pdf` directly. The sample was **2026 INSC 1072**: 19 pages, text layer present, paragraphs numbered [R21]. |
| CAPTCHA | **The Securimage (`siwp_captcha`) CAPTCHA sits on every search form:** judgment by date, judgment by case number, daily order by case number, **cause list** and neutral citation [R21]. **The SCR search has a CAPTCHA** [R23]. `digiscr.sci.gov.in` returned 502 at CONNECT. |
| robots | `Disallow: /wp-admin/` only [R21]. |
| ToU | Website Policies say contents "shall not be reproduced partially or fully, without duly & prominently acknowledging the source" and not in a "misleading or objectionable context or derogatory manner" [R22]. The disclaimer says "information in the original records will be final and binding" [R22]. |
| AWS SC dataset | CC-BY-4.0; registry "UpdateFrequency: Bi-monthly"; source scr.sci.gov.in [R24].<br>Yearly counts are **589 (2016), 571 (2020), 856 (2023), 782 (2024), 897 (2025), 214 (2026, decisions to 25 May 2026; index updated 2026-08-31)** [R26]. Every 2026 row carries an SCR citation (e.g. "[2026] 2 S.C.R. 107"), so the dataset is the **reported subset**.<br>The registry says ~35k judgments and ~52 GB including regional-language versions [R24][R25]. |
| Format | Born-digital PDF with text layer and neutral citation; dataset adds JSON and Parquet metadata. |
| Volume | About 1,400 judgments a year (INSC 1072 by 30 Sep) and about 20+ "latest" orders a day on the widget. |
| Cadence | Judgments appear on the widget the same day or the next (sample: decided 30 Sep, listed 1 Oct). |
| rights_class | `OFFICIAL` (sci.gov.in); `OPEN_LICENSED` (AWS). SCR headnotes are treated as display-only (21_india §1). |
| Gap | Non-SCR judgments since 2023 (≈ 500–700 a year, *estimate*) are in neither the dataset nor any open bulk listing. Back-catalogue search is CAPTCHA-gated. |

**LegalProfiles**

| `source_id` | access_mode | access_control | terms_ref | risk | counsel? |
|---|---|---|---|---|---|
| `SCI_JUDGMENTS` (widget + sci-get-pdf) | OPEN | NONE on widget | `tou_sci@2026-10-01` | L | No (attribution obligation only) |
| `SCI_SEARCH` (search, cause list, daily orders for watched matters) | HUMAN_ASSISTED | CAPTCHA | same | M | **Yes** (Q4) |
| `AWS_SC` | BULK_DATASET | NONE | `lic_ccby4_dattam_sc@2026-10-01` | L | Q6 (derivation from a CAPTCHA portal) |

**MVP decision**
- **Backfill:** all English AWS SC judgments, about 35k. LLM enrichment runs only on the corporate-filtered subset, ≈ 8–10k (*estimate*).
- **Daily delta:** poll the SC widget every 30 min, 09:00–22:00 IST. Reconcile **INSC sequence gaps** each week, since neutral citations are sequential, so a gap means a judgment we missed.
- **Non-SCR 2023–26 gap:** fill only for SC judgments that corporate documents cite, via the IK API or partner uploads.
- **Cause list and daily orders for watched matters:** manual entry. These forms are CAPTCHA-gated, and the brief allows manual entry.

### 2.2 NCLAT (nclat.nic.in)

| Item | Finding |
|---|---|
| What's there | Daily orders and judgments (New Delhi Principal Bench and Chennai), cause lists, court notices, act and rules, and a calendar [R9]. |
| Open route | **The display board** (`/display-board/orders`, `/display-board/judge`) is a Laravel app. Search runs by POST to `/display-board/order_details` with the page's CSRF `_token` and modes `order_date_wise`, `case_no_wise`, `party_wise` and others. **No CAPTCHA** [R9]. |
| PDFs | The homepage links `/display-board/view_order_pdf?fid={filing_no}&l=delhi\|chennai&d=YYYY-MM-DD&order_type=J\|D`. **This is not a direct PDF.** It returns an auto-submitting form that POSTs to `/display-board/view_order` with a session `_token`, and the POST returns `application/pdf`. We verified it: the sample was 1 page, LibreOffice-generated, with text layer [R9]. The adapter must keep a cookie jar and re-read the token. |
| Pre-2021 | `/judgement-data` and `/daily-order-data` (orders before 31.05.2021) are Drupal views with **direct** PDF links (`/sites/default/files/migration/upload/*.pdf`) and sector filters (Company, Competition, Insolvency, MRTP, Compensation) [R12]. |
| robots | Drupal default. `Disallow: /search/`, `/admin/`, `/user/*`; `/display-board/` is **allowed** [R8]. |
| ToU | Copyright policy: material "may be reproduced free of charge in any format or media without requiring specific permission", subject to accuracy, no derogatory or misleading use, and the source "prominently acknowledged" [R10]. **Hyperlinking policy: "Prior permission is required before hyper links are directed from any website/portal to this site"**, by request to the webmaster [R11]. |
| Volume | An `order_date_wise` search for New Delhi, 28–30 Sep 2026, returned **217 cases**:<br>• by date: 158 daily orders on 28 Sep, 57 on 29 Sep, 2 on 30 Sep, so uploads lag 1–2 days;<br>• by type: Company Appeal(AT)(Ins) 126, Company Appeal(AT) 15, **Competition Appeal(AT) 14**, Contempt 2 [R9].<br>The homepage showed about 4 judgments a bench a day. **Estimate:** 60–110 daily orders and 3–8 judgments per working day; ≈ 1.5–2.5k judgments a year (*unverified*). |
| Cadence | Daily; 1–2 day upload lag. |
| rights_class | `OFFICIAL` |

| `source_id` | access_mode | access_control | terms_ref | risk | counsel? |
|---|---|---|---|---|---|
| `NCLAT` (display board + migration pages + cause lists) | OPEN | NONE (CSRF/session only) | `tou_nclat@2026-10-01` | L–M | **Yes, narrow:** (a) send the hyperlink permission request; (b) confirm that scripted use of the site's own POST search is acceptable (Q5) |

**MVP decision**
- **Backfill:** judgments 2017–2026, from the display-board judgments search plus `/judgement-data`.
- **Daily delta:** daily orders and judgments. Cause-list PDFs feed hearing tracking.
- **Daily orders before go-live:** only for watched matters.

### 2.3 NCLT (nclt.gov.in) — allowed paths only

| Item | Finding |
|---|---|
| What's there | Orders and judgments of 15 benches (search pages), daily cause lists, the NCLT calendar and holidays, public notices (bench transfers, recalls, special benches), act and rules, forms, and annual reports [R1][R5]. |
| robots | `Disallow: /search/` plus the Drupal defaults (`/admin/`, `/user/*`, `/node/add/`) [R1]. **The order pages are not under `/search/`.** |
| CAPTCHA (rechecked) | `/order-date-wise` ("Judgement/Orders By Order Date") **has a CAPTCHA** ("Captcha Code * … testing whether or not you are a human visitor"). `/diary-number-wise` (case status) **has a CAPTCHA** [R2]. **This confirms 02_P0.** |
| Open, allowed | `/all-cause-list` has **no CAPTCHA**. It holds per-court cause-list PDFs under `/sites/default/files/pdf_cause_list/…`; page 1 on 1 Oct showed 20 lists with 528 entries. Public notices are direct PDFs on the homepage [R5]. |
| e-filing "Case History" | `efiling.nclt.gov.in/casehistorybeforeloginmenutrue.drt` showed **no CAPTCHA in its markup**. It is driven by AJAX endpoints (`caseHistoryalldetails.drt`, `caseHistoryoptionalCIN.drt`, `ordersview.drt`) [R6]. Its robots.txt and `archive.nclt.gov.in` were **unreachable** (connection reset) from our egress. |
| ToU | Copyright policy: reproducible "free of charge in any format or media without requiring specific permission", with prominent acknowledgment [R3]. Hyperlinking policy: "**Prior permission is required** before hyper links are directed … to this site" [R4]. |
| Volume | National: ≈ 800–1,500 listed matters a day (*estimate* from cause-list counts). Final orders are a fraction of these. |
| rights_class | `OFFICIAL` |

| `source_id` | access_mode | access_control | terms_ref | risk | counsel? |
|---|---|---|---|---|---|
| `NCLT_CAUSELIST` (+ notices, calendar) | OPEN | NONE | `tou_nclt@2026-10-01` | L | Hyperlink permission request |
| `NCLT_ORDERS` (order-by-date) | — (**BLOCKED for automation**) | CAPTCHA | same | H | — |
| `NCLT_CASEHISTORY` (per watched matter) | HUMAN_ASSISTED (MVP: a lawyer reads it); automation only after counsel says yes | NONE observed | same | M | **Yes** (Q4/Q5) |

**MVP decision.**
- NCLT **orders** come from the **IBBI mirror** (§2.4). Those are IBC matters only.
- **Companies Act NCLT orders** (ss.241–242, schemes, s.252 restoration, compounding appeals) have **no open route**:
  - bring them in as partner uploads, plus IK gap-fill for cited orders;
  - send a written **data-access/MoU request to the NCLT Registry** in week 1.
- **Daily delta:** cause lists and public notices.
- **Hearing tracking:** cause-list PDFs are parsed for the case numbers on the watchlist. Anything not matched is entered manually.

### 2.4 IBBI order mirror (ibbi.gov.in/orders/…)

| Item | Finding |
|---|---|
| Sections and counts | `/orders/nclt` **31,792**; `/orders/nclat` **5,700**; `/orders/supreme-court` **844**; `/orders/high-courts` **612**; 20 rows a page. The legacy `/en/orders/*` paths 301-redirect to these [R14]. |
| Row schema | Orders Date · Subject ("In the matter of TAKSHASHILA CORPORATION LLP [CP(IB) 188 of 2026] (548.55 KB)") · **Orders Remarks**. Remarks seen on page 1 include "Admission - Final Order", "Approval of Resolution Plan", "Appointment - Appointment of Liquidator", "Dissolution", "Dismissed", "CIRP Withdrawn", "Rejected" and "Others". There is a bench filter (Principal … Mumbai, Others) [R14]. |
| Links | Direct, unquoted `href=/uploads/order/{timestamp}-{rand}-{md5}.pdf`. The timestamp is the upload time: an order dated 25 Sep 2026 was uploaded 2026-09-29 [R14]. |
| PDF quality | Of the 3 NCLT samples, 1 was **image-only** (FPDF, 16 pages, 0 text characters), 1 was a Word export and 1 was a "Google Docs Renderer" export. NCLAT samples were PDFium with text. **OCR is required for part of the set**, and these are **not bench-issued originals** [R14]. |
| Disclaimer (verbatim) | "These Orders/Judgments are not certified copies issued by the judicial authorities. The Orders/Judgments of Courts/Tribunals available on IBBIs website are merely for facilitation purpose." It also says IBBI "does not authenticate the contents" [R14]. |
| robots | `/robots.txt` returns an application error page; there is no robots file [R14]. |
| ToU | Copyright policy: "may be reproduced free of charge in any format or media without requiring specific permission", with prominent acknowledgment. Hyperlink policy: "no prior permission is required" but "we would like you to inform us"; "We do not permit our pages to be loaded into frames" [R15]. |
| Cadence | Daily weekday uploads; the sample was uploaded 4 calendar days (2 working days) after the order date. |
| rights_class | `OFFICIAL`, with `provenance_tier = OFFICIAL_AGGREGATOR` and `flags.uncertified = true` |

| `source_id` | access_mode | access_control | terms_ref | risk | counsel? |
|---|---|---|---|---|---|
| `IBBI_ORDERS` (nclt, nclat, sc, hc) | OPEN | NONE | `tou_ibbi@2026-10-01` | L | Q3 (displaying uncertified copies); courtesy notice of links |

**MVP decision**
- **Backfill all four sections** (≈ 38.9k).
- **Daily delta.**
- **Dedupe** NCLAT, SC and HC copies against the official and AWS copies on (forum, case number, order date). The **official copy wins for paragraph anchors**.
- **Use "Orders Remarks" as a weak outcome label** for the citator, with `assertion.source = IBBI_REMARK`.

### 2.5 Securities Appellate Tribunal (SAT)

| Item | Finding |
|---|---|
| Legacy site | `https://sat.gov.in/` and `www.sat.gov.in` return **503 "No server is available to handle this request"**, as do robots.txt and the English index. WebFetch also returned 503. So SAT is **still down, as in 02_P0** [R33]. |
| New portal | `https://satweb.sat.gov.in/` is up and has no robots.txt (404). `/orders` offers Appeal No., AL No., Party Name and Date-wise searches, **each with a CAPTCHA** (`captcha_word_tab1…4`). `/sat-judgment` returns 404 [R33]. |
| ToU | `/terms-of-services` is a generic privacy and disclaimer statement. No reproduction clause was found [R33]. |
| Alternative routes | SEBI "Orders of SAT" (`smid=1`) has **2,447 records, but the newest is dated Jul 06, 2015** [R35]. SEBI "Orders of Courts" (1,118, latest 21 Aug 2026) covers SC/HC rulings in SEBI matters [R35]. Listed companies disclose SAT orders on NSE/BSE (`snippet`). |
| rights_class | `OFFICIAL` (SEBI mirror); IK: `LICENSED_RESTRICTED` |

| `source_id` | access_mode | access_control | risk | counsel? |
|---|---|---|---|---|
| `SAT_PORTAL` | — (BLOCKED for automation) | CAPTCHA | H | Q4 if HUMAN_ASSISTED |
| `SEBI_SAT_ORDERS` (≤2015) | OPEN | NONE | L | SEBI permission email (Q1) |

**MVP decision**
- **Backfill** the SEBI-hosted SAT orders up to 2015.
- **Orders after 2015:** fetch only cited SAT orders, via IK, plus partner uploads.
- **Watched SAT appeals:** manual.
- **Ask SAT's Registrar** for permission or a data-access route.
- **Re-probe `sat.gov.in` monthly.**
- SAT stays a **thin source**, so the "SAT appeal" trigger runs in general mode unless the partner supplies orders.

### 2.6 SEBI orders (sebi.gov.in)

| Item | Finding |
|---|---|
| Listings | `HomeAction.do?doListing=yes&sid=2&ssid=9&smid={n}`. The rows are date and title, linking to an HTML page that embeds the PDF. **No CAPTCHA** on listings; the only CAPTCHA is on the login/feedback modal [R34][R35]. |
| Counts | All orders **30,957**. By sub-type (`smid`): 1 SAT 2,447 (to 2015) · 2 Chairperson/Members 6,427 · 3 Settlement 2,001 · 6 AO 12,007 · 7 Courts 1,118 · 133 ED/CGM 442 [R35]. |
| RSS | `https://www.sebi.gov.in/sebirss.xml` holds the 30 latest items with `<ttl>60</ttl>`. On 1 Oct these were 17 recovery proceedings and 11 orders [R34]. It is a trigger only, and listings are still polled. |
| robots | `Disallow: /js`, `/css`, `/hindi/js`, `/hindi/css` only [R34]. |
| ToU | Website policy: material "may be reproduced free of charge **after taking proper permission by sending a mail to us**", with accuracy and acknowledgment [R34]. |
| Cadence | Daily, with 5–15 orders on a working day. |
| rights_class | `OFFICIAL`. SEBI orders are quasi-judicial, so s.52(1)(q)(iv) "other judicial authority" probably applies *(counsel)*. |

| `source_id` | access_mode | terms_ref | risk | counsel? |
|---|---|---|---|---|
| `SEBI_ORDERS` | OPEN (RSS + listings) | `tou_sebi@2026-10-01` | M (ToU asks permission) | **Yes** (Q1): send the permission email in week 1 |

**MVP decision**
- **Backfill** smid 2, 3, 6, 7 and 133 (≈ 22k), plus smid 1.
- **Daily delta** from RSS (hourly) plus a nightly listing sweep.

### 2.7 CCI orders and NCLAT competition appeals

| Item | Finding |
|---|---|
| Listings | `/antitrust/orders` is a DataTables POST to `/antitrust/orders/list` (CSRF header) that returns JSON. It reports **recordsTotal 1,246**; for example, case 02/2026 "Section 26(1)", order 10/09/2026, file `images/antitrustorder/en/order1789038268.pdf`. `/combination/orders-section31` (GET JSON) reports **1,472** (orders and green-channel notices). **No CAPTCHA** [R37]. |
| robots | Disallows only image subfolders [R37]. |
| ToU | Copyright policy: "may be reproduced free of charge **after taking proper permission by sending a mail to us**" [R37]. |
| NCLAT competition appeals | Already covered by `NCLAT`: case type "Competition Appeal(AT)" (14 cases in the 3-day sample) [R9]. |

**MVP decision.** **Defer CCI** unless the partner ranks competition work in the top triggers. Competition appeals come free through NCLAT. If CCI is enabled, the backfill is ≈ 2.7k orders at low effort, and the permission email (Q1) is needed.

### 2.8 Delhi High Court (company, commercial, arbitration)

| Item | Finding |
|---|---|
| Official site | `delhihighcourt.nic.in/web/` loads. `/web/judgement/fetch-data` ("Latest Judgments") showed "**An error occurred while fetching data**". `/app/sitting-judge-wise` (judgment search) **has a CAPTCHA** (`captchaInput`). robots.txt returns 404 (none). Some sub-pages reset the connection [R31]. |
| ToU | Copyright policy: "Material featured on this Website may be reproduced free of charge **after taking proper permission by sending a mail to us**" [R30]. |
| AWS HC dataset | Court `7_26`, bench `dhcdb`, CC-BY-4.0 [R27][R28].<br>**2025:** 50,414 metadata rows and **53,051 PDFs (4.14 GB)**.<br>**2026:** 35,852 rows, decisions up to **2026-09-28**, index updated 2026-09-28 [R29].<br>Metadata fields include `title` (case type/no./year + parties), `cnr`, `decision_date`, `judge`, `disposal_nature` and `pdf_link`. `pdf_exists` reads False on every 2025 row although the PDFs are present, so the flag is unreliable. |
| Corporate filter (2025, from `title` prefix) | ARB.P. 2,186 · O.M.P.(MISC.)(COMM.) 1,014 · CS(COMM) 800 · O.M.P.(I)(COMM.) 483 · FAO(COMM) 254 · O.M.P.(COMM) 243 · RFA(COMM) 236 · FAO(OS)(COMM) 233 · OMP(ENF.)(COMM.) 145 · O.M.P.(T)(COMM.) 112 · EX.P. 78 · ARB.A.(COMM.) 63 · CO.PET. 44 · EX.F.A. 38 · CO.APP. 28 · others. This is **≈ 6.1k a year excluding LPA and IPD** [R29]. |
| Format | PDF (text layer typical for Delhi HC); orders and judgments are mixed. |

| `source_id` | access_mode | terms_ref | risk | counsel? |
|---|---|---|---|---|
| `AWS_HC_DEL` | BULK_DATASET | `lic_ccby4_dattam_hc@2026-10-01` | L | Q6 |
| `DHC_SITE` | — (CAPTCHA; listing broken) | `tou_dhc@2026-10-01` | M | Q1 (permission mail) before any later open adapter |

**MVP decision**
- **Backfill 2019–2026** from AWS, filtered by an allow-list of case types: ARB.*, O.M.P.*, CS(COMM), FAO(OS)(COMM), FAO(COMM), RFA(COMM), RFA(OS)(COMM), EFA(COMM), EX.P., EX.F.A., CO.PET., CO.APP., and COMPANY APPEALS if present.
- **Delta:** `aws s3 sync` weekly.
- **Watched matters:** manual.

### 2.9 Bombay High Court (Original Side: commercial, arbitration, company)

| Item | Finding |
|---|---|
| Official site | `bombayhighcourt.nic.in` reset the connection. `bombayhighcourt.gov.in` failed TLS ("unsafe legacy renegotiation disabled"). Both were **unreachable** from our egress, consistent with 02_P0 [R32]. |
| AWS HC dataset | Court `27_1`. Benches: `newos` (Original Side), `newos_spl`, `newas` (Appellate Side), `hcbgoa`, `hcaurdb`, `kolhcdb` [R28].<br>Two metadata series: web `metadata.parquet` (Original Side 2025: only 1,578 rows) and **mobile-API `metadata-mobile.parquet`** (Original Side 2025: **74,621 rows, `source = "mobile"`**). The mobile series has rich fields: `case_type`, `petitioner`, `respondent`, advocates, `order_type`, `is_final`, `order_number` [R29].<br>The Original Side 2025 tar parts hold 51,331 files of about 2 GB. The 2026 partition was updated **2026-09-30** [R29]. |
| Corporate filter (Original Side 2025, mobile) | CARBP 4,138 · CARAP 3,023 · ARBP 2,468 · ARBAP 2,245 · COMIP 941 · COMAP 351 · COMMP 315 · COMS 141 · COMAS 113 · COMEX 91 · CARBA 122 · CPCD 185 · OLR 184 · CA 53. That is **14,370 orders, of which ≈ 4.3k have `is_final=True`**. Order types across all Original Side 2025 rows: Interim 54,443, "Farad" 19,439, Judgement 728 [R29]. |
| Provenance caveat | The dataset documentation says mobile-sourced rows "may have `pdf_exists = null`" and that "The mobile scraper is not yet part of this repository" [R28]. |

| `source_id` | access_mode | risk | counsel? |
|---|---|---|---|
| `AWS_HC_BOM` (`BHC_COMM` in doc 03) | BULK_DATASET | L–M (mobile-API derivation) | Q6 |

**MVP decision**
- **Backfill 2021–2026** final orders and judgments (`is_final` or `order_type = View Judgement`) for the case types above.
- **Interim orders:** only for watched matters.
- **Delta:** weekly sync.
- **Dedupe key:** `(cnr, decision_date, order_number)` [R28].

### 2.10 Partner's High Court (placeholder)

| Step | Action |
|---|---|
| 1 | Get the court code and benches from `high_courts.csv` [R28]. Pull one year of parquet and tabulate case types, as in §2.8 and §2.9. |
| 2 | The partner confirms the case-type allow-list (company, commercial division, arbitration). |
| 3 | Probe the official site for a CAPTCHA-free listing or RSS (02_P0 notes Allahabad HC has RSS), plus robots and copyright policy. If it is clean, add an `OPEN` adapter; if not, stay on AWS. |
| 4 | LegalProfile `AWS_HC_<code>` (BULK_DATASET, L). Add the HC cause list to manual hearing tracking. |

### 2.11 Gap-fill and signal sources (all fora)

| Source | Role | rights_class | Access mode | Notes |
|---|---|---|---|---|
| Indian Kanoon API | Cited-but-missing items: SC non-SCR, SAT after 2015, NCLT Companies Act orders | `LICENSED_RESTRICTED` | LICENSED_API | Prepaid per call; attribution required; 1-month termination; retention questions open (02_P0 §3.2, Q9). Spend cap. Every IK-only document is queued for official re-acquisition. |
| Partner uploads | Certified copies, SAT/NCLT orders, HC orders for watched matters | `USER_UPLOADED` (tenant) | PARTNER_CONTRIBUTED | Never promoted to the shared corpus in the MVP. |
| LiveLaw / Bar & Bench RSS | "Judgment pronounced" signal | `THIRD_PARTY_LINK_ONLY` | SIGNAL_ONLY | Store headline, URL and timestamp only. |
| SCC Online / Manupatra | — | `THIRD_PARTY_LINK_ONLY` | none | Citation strings appearing inside court text only. |

---

## 3. Statutes and subordinate legislation

### 3.1 Where official consolidated text lives (findings)

- **India Code (`indiacode.gov.in`), DSpace 9.1.**
  - The REST API is `https://indiacode.gov.in/server/api`, and search is `/discover/search/objects?query=…`. We counted **130,852 items** [R39].
  - Collections seen: `ACT`, `ACT_AMENDMENT`, `RULE`, `REGULATION`, `NOTIFICATION`, `SECTION`.
  - `SECTION` items carry section text plus **amendment footnotes with "w.e.f." dates**. Example, Advocates Act s.39: "Subs. by s. 29, ibid., for section 39 (w.e.f. 31-1-1974)" [R39].
  - Act items carry the full-Act PDF (`A{year}-{no}.pdf`) and a Hindi PDF.
  - **Data-quality findings:**
    - The IBC PDF (created 2026-07-10) includes the 2026 amendments: "Ins. by Act 6 of 2026, s. 2 (w.e.f. 26.05.2026)", ss.38–42 "Omitted", Chapter IV "OMITTED", and new s.64A (printed "Peralty …").
    - The **SECTION item for IBC s.7 still shows the old s.7(5)** ("Where the Adjudicating Authority is satisfied that—…"), and its footnotes stop at Act 1 of 2020.
    - `dc.date.last_modified` = 2024-07-25 for the IBC.
    - `dc.description.abstract` holds an editorial "Summary", and `dc.identifier.uri` points to `test1.indiacode.nic.in` [R39].
  - **Rule:** the full-Act PDF is canonical. SECTION items are used only for navigation and amendment-footnote parsing, and are always diffed against the PDF.
  - Robots.txt returns 500. The ToU and copyright pages render client-side and could not be read without JS (`unverified`).
- **MCA (`mca.gov.in`)** returned **403 (Akamai "Access Denied")** to both curl and WebFetch [R40], so it is **blocked from our egress**. Re-test from India egress in week 1 (02_P0 Q4). MCA's "e-Book" of 10 Acts with rules is `snippet` only.
- **IBBI legal framework.**
  - `/legal-framework/act` (37 records) holds amending Acts, Ordinances and Bills, plus **dated consolidated IBC snapshots** ("IBC 2016 (Upto 04.04.2021)", "(Upto 12.08.2021)").
  - `/legal-framework/updated` (144 records) holds **dated consolidated regulations**, e.g. "IBBI (Liquidation Process) Regulations, 2016 (Amended upto 22-09-2026)".
  - Snapshot counts: **≈ 33 CIRP and ≈ 20 Liquidation snapshots** (title variants merged), back to Nov 2016.
  - `/legal-framework/rules` (36) and `/notifications` (85) [R16][R17][R18].
- **SEBI legal pages.**
  - Acts are consolidated ("SEBI Act, 1992 (As amended by the Finance Act, 2021 … w.e.f. April 1, 2021)").
  - Rules and Regulations are consolidated, titled "[Last amended on …]", and each version has its own URL id [R36]. Whether older consolidated versions stay listed is `unverified`.
- **NCLT / NCLAT sites.** These host the **NCLT Rules 2016 plus separate amendment PDFs** (2016, 2017, 2019, 2019 (2nd), 2020) and the NCLAT Rules 2016 plus the 2017 amendment. There is no consolidated text, and the chain on the tribunal sites ends in 2020 [R7][R13]. Later amendments must be checked in India Code `RULE` and the e-Gazette.
- **RBI.** The Master Directions page lists FEMA MDs with "Updated as on" dates, e.g. "Master Direction – Foreign Investment in India ( Updated up to June 15, 2026 )" and "Risk Management and Inter-Bank Dealings ( Updated as on September 22, 2026 )". Only the current version is offered [R42].

### 3.2 Instrument table

**Abbreviations.**
- **Versioning:** PIT = full point-in-time (valid-time intervals per provision); CUR = current consolidated text with "law current to" date; CUR+Δ = current text plus amending instruments ingested as events (no reconstructed history).
- **Sources:** IC = India Code; IBBI-U = IBBI "updated" page.

| Instrument | Official consolidated source | Format | History available? | MVP versioning |
|---|---|---|---|---|
| **IBC 2016** | IC full-Act PDF (current to 26.05.2026, verified); IBBI Act page (snapshots to 2021 + amending Acts incl. Act 6 of 2026) | PDF; IC SECTION JSON | **Yes**: IBBI snapshots 04.04.2021 and 12.08.2021, amending Acts 2018–2026 and the S.O. 2625(E) | **PIT (mandatory test case)** for every IBC section touched by Act 6 of 2026. States: before 26.05.2026; in force from 26.05.2026; **enacted, not in force** (§5). |
| IBC (Application to Adjudicating Authority) Rules 2016 | IBBI rules page ("upto 24-09-2020") + amendment rules; IC `RULE` | PDF | Partial (consolidated to 2020 + amendments) | CUR (law current to 24.09.2020 + any later amendment found — **TO VERIFY**) |
| IBBI CIRP Regulations 2016 | IBBI-U ("Amended upto 09-06-2026", latest seen) | PDF | **Yes**: ≈ 30 dated snapshots | **PIT** (snapshots → version intervals) |
| IBBI Liquidation Process Regulations 2016 | IBBI-U ("Amended upto 22-09-2026") | PDF | **Yes**: ≈ 19 snapshots | **PIT** |
| IBBI Voluntary Liquidation / PPIRP Regs | IBBI-U | PDF | Yes | CUR (PIT later) |
| Companies Act 2013 | IC full-Act PDF; MCA (blocked to us) | PDF | Footnotes only | CUR+Δ |
| NCLT Rules 2016 | NCLT `/act-rule` (base + 5 amendment PDFs to 2020); IC `RULE` | PDF | Amendment chain, not consolidated | CUR (we consolidate base + amendments; **partner/counsel check**) |
| NCLAT Rules 2016 | NCLAT `/act-rules` (base + 2017 amendment) | PDF | Partial | CUR (same caveat) |
| Companies (Adjudication of Penalties) Rules 2014 | MCA (blocked); IC `RULE` holds the amendment rules (e.g. 2019) | PDF | Amendment chain | CUR+Δ — **TO VERIFY the consolidated source** |
| SEBI Act 1992; SCRA 1956; Depositories Act 1996 | SEBI Acts page (consolidated to Finance Act 2021); IC | HTML/PDF | Snapshot titles only | CUR |
| SEBI (Procedure for Holding Inquiry and Imposing Penalties) Rules 1995 | SEBI Rules page "[Last amended on December 31, 2021]" | HTML/PDF | Per-version URLs | CUR |
| SEBI Settlement Proceedings Regs 2018 | SEBI Regs "[Last amended on November 28, 2024]" | HTML/PDF | Per-version URLs | CUR |
| SEBI LODR 2015 | SEBI Regs "[Last amended on July 14, 2026]" | HTML/PDF | Per-version URLs | CUR (PIT later; frequent amendments) |
| SEBI SAST 2011 | SEBI Regs "[Last amended on December 5, 2025]" | HTML/PDF | Same | CUR |
| SEBI PIT 2015 | SEBI Regs "[Last amended on March 12, 2025]" | HTML/PDF | Same | CUR |
| SEBI ICDR 2018 | SEBI Regs "[Last amended on March 21, 2026]" | HTML/PDF | Same | CUR |
| Arbitration and Conciliation Act 1996 | IC | PDF/SECTION | Footnotes | CUR+Δ (the 2015/2019/2021 amendment w.e.f. dates matter for s.34/s.29A — the rules doc decides) |
| Indian Contract Act 1872; Specific Relief Act 1963; NI Act 1881; LLP Act 2008; General Clauses Act 1897; Competition Act 2002; FEMA 1999 | IC | PDF/SECTION | Footnotes | CUR |
| Limitation Act 1963 | IC | PDF/SECTION | Footnotes | CUR (the computation rules depend on it; the text is stable) |
| CPC 1908 | IC | PDF/SECTION | Footnotes | CUR (Commercial Courts Act modifications read with CCA Schedule) |
| Commercial Courts Act 2015 | IC (two ACT items seen, one with last_modified 2019-08-29) | PDF | Footnotes | CUR |
| Commercial Courts rules: Pre-Institution Mediation and Settlement Rules 2018; Delhi HC (Original Side) Rules 2018; Bombay HC Original Side / Commercial Division rules | IC `RULE` (central rules); HC "Court Rules" pages | PDF | Unknown | CUR — **TO VERIFY** sources with the partner |
| Constitution of India | IC; Legislative Department PDF (*unverified this session*) | PDF | Footnotes | CUR |
| FEMA key rules/regs: NDI Rules 2019; Overseas Investment Rules/Regs 2022; Foreign Exchange (Compounding Proceedings) Rules 2024 (G.S.R. 566(E), 12 Sep 2024, `snippet`) [R48] | e-Gazette; RBI "FEMA notifications"; IC `RULE` | PDF | Amendment chain | CUR |
| RBI FEMA Master Directions (Foreign Investment in India; ECB; Compounding; Reporting; Import/Export; LRS) | RBI MD page ("Updated as on …") [R42]; RBI's new site `website.rbi.org.in` (`snippet`) [R49] | HTML/PDF | Current only | CUR (our captures start the history) |
| CCI regulations (if CCI is enabled) | CCI legal framework pages [R37] | PDF | Unknown | CUR |

**Legal note (from 21_india §2.1).** Acts may be reproduced only "together with any commentary thereon or any other original matter" (s.52(1)(q)(ii)). Statute views must therefore always carry our annotations, version history and treatment. A bare-Act bulk export is not allowed (Q7). Rules, regulations and notifications published in the Gazette fall under (q)(i).

---

## 4. Regulator and legislative feeds

| Feed | Access route (verified) | Format | Cadence | ToU / risk | MVP |
|---|---|---|---|---|---|
| **MCA notifications and circulars** | `mca.gov.in` returned **403 (Akamai)** to us [R40]. Fallbacks: MCA S.O./G.S.R. notifications via the **e-Gazette**; India Code `NOTIFICATION` items. *General circulars are not gazetted, so they need MCA itself.* | PDF | Weekly–daily | Unknown (blocked); **H for now** | Week-1 India-egress test. If it is still blocked, MCA circulars come in as partner/manual uploads and gazette items are polled. |
| **SEBI circulars, master circulars, orders** | RSS `sebirss.xml` (30 latest; `ttl 60`) + listings: circulars `sid=1&ssid=7` (**2,802**), master circulars `ssid=6` (**134**), orders §2.6 [R34][R36] | HTML wrapper + PDF; RSS 2.0 | Daily | Permission-by-mail clause (Q1) | Hourly RSS + nightly listings. Backfill all circulars from 2015 and all master circulars. |
| **IBBI circulars, notifications, regs** | `/legal-framework/circulars` (**112**), `/notifications` (**85**), `/rules` (36), `/act` (37), `/updated` (144) [R16–R18]. No RSS observed (*unverified*). | HTML table + PDF | Ad hoc, weekly | Open reproduction policy; L | Daily poll; full backfill (small). |
| **RBI notifications and FEMA Master Directions** | RSS: `notifications_rss.xml` (10 latest; e.g. "Foreign Exchange Management (Export and Import of Goods and Services) (Amendment) Regulations, 2026", 25 Sep 2026), `pressreleases_rss.xml`; MD page `BS_ViewMasterDirections.aspx` [R42]. `robots.txt` returned 418 "Unauthorised Access". | RSS + HTML/PDF | Daily | Disclaimer: RBI may "block access from a particular Internet address"; no reproduction clause found. M (rate limits). | RSS hourly; filter to FEMA/FED and corporate items; MD page weekly with diff. |
| **e-Gazette (central)** | Homepage "Recent Extra Ordinary Gazettes" table (ministry, subject, date, Gazette ID, e.g. `CG-DL-E-01102026-276672`), **no CAPTCHA**. **The TLS chain is leaf-only**: a Let's Encrypt YR2 leaf without the intermediate. Fetching works after **AIA-chasing** the intermediate (`http://yr2.i.lencr.org/`); TLS verification is never disabled. Inner pages need an ASP.NET session (cookie-in-URL) [R41]. | PDF | Daily (extraordinary ad hoc) | s.52(1)(q)(i); L | Poll the homepage table every 2 h; filter by ministry (Corporate Affairs, Finance/DEA, Law/Legislative) and by keywords (SEBI/IBBI/RBI regulations). Gazette IDs rose from 271594 (6 Apr) to 276672 (1 Oct), i.e. **≈ 28 extraordinary gazettes a day** across government (derived). |
| **Parliament / PRS bill tracking** | PRS billtrack page (status timeline, bill text, JPC report PDF), licensed "**Creative Commons Attribution 4.0**" (footer) [R43]. robots: `Crawl-delay: 10`. sansad.in is an SPA (not probed in depth). | HTML + PDF | Weekly; daily in session | PRS: `OPEN_LICENSED`. Bill text: not under s.52(1)(q) (Q10). | Weekly watch of bills on a watchlist; store status events only. Bill text shown as a link plus excerpt. |
| **Tribunal notices** (NCLT public notices; NCLAT court and adjournment notices) | Homepage PDF links [R5][R9] | PDF | Daily | As parent; L | Daily; feeds hearing tracking (bench transfers, recalls). |

---

## 5. Fresh-law verification

### 5.1 IBC (Amendment) Act 2026: verified against the gazette PDFs

| Fact | Verified text / value | Source |
|---|---|---|
| Act | "THE INSOLVENCY AND BANKRUPTCY CODE (AMENDMENT) ACT, 2026, NO. 6 OF 2026" | [R19] |
| Assent | "The Following Act of Parliament received the assent of the President on the 6th April, 2026" | [R19] |
| Gazette | Gazette of India Extraordinary, Part II—Section 1, No. 11, New Delhi, 6 Apr 2026; ID **CG-DL-E-06042026-271594** | [R19] |
| Commencement clause | s.1(2): "It shall come into force on such date as the Central Government may, by notification in the Official Gazette, appoint: Provided that different dates may be appointed for different provisions" | [R19] |
| Commencement notification | **S.O. 2625(E)**, MCA, "New Delhi, the 22nd May, 2026"; published Gazette Extraordinary Part II—Sec. 3(ii), **No. 2533, 25 May 2026**, ID **CG-DL-E-25052026-272855**; F. No. Insol-30/8/2025-Insolvency-MCA; signed by Anita Shah Akella, Jt. Secy. | [R20] |
| Operative words | "the Central Government hereby appoints the **26th day of May, 2026**, as the date on which the following provisions of the said Act shall come into force, namely: – 1. sections 2 to 6 (both inclusive); 2. sections 8 to 33 (both inclusive); 3. sub-clause (iii) of clause (a) and clause (b) of section 34; 4. sections 35 to 39 (both inclusive); 5. section 41; 6. sections 43 to 44 (both inclusive); 7. section 46; 8. sections 48 to 59 (both inclusive); 9. sections 61 to 66 (both inclusive); 10. section 68; 11. clause (a) of section 69; 12. clause (a) of section 70; 13. sub-clause (i) to sub-clause (xxvi) of clause (b) of section 70 [Except sub-clause (xx) of clause (b) of section 70]; and 14. section 72." | [R20] |
| Later notifications | IBBI's notifications list (85 records, newest first) shows the s.1(2) notification (25 May 2026), and after it only an appointment notice (8 Jul 2026). No later commencement notification was found up to 1 Oct 2026. This is **not exhaustive**: a gazette search for "Act 6 of 2026" is needed before go-live. Secondary sources agree that CIIRP, group and cross-border are "pending notification" (`snippet`) [R47]. | [R18] |

**Not brought into force.** Each row is a section of the amending Act; the IBC provision it affects is named in the second column.

| Amending § | Effect on IBC | Brief said | Status |
|---|---|---|---|
| s.40 | Inserts **Chapter IV-A "Creditor-Initiated Insolvency Resolution Process", ss.58A–58K** (no 58I in the numbering) | Not notified | **Confirmed not in force** |
| s.42 | Inserts **Chapter VA "Group Insolvency", s.59A** | Not notified | **Confirmed** |
| s.71 | Inserts **s.240B** (electronic portal) and **s.240C** (cross-border insolvency) | Not notified | **Confirmed** (both come from the same amending s.71) |
| s.7 | s.11(ba): adds "or Chapter IV-A" | — | **Also not in force** (added) |
| s.34(a)(i)–(ii) | s.54A(2)(a),(b): CIIRP references in PPIRP eligibility. **(a)(iii) and (b), which change 66%→51%, ARE in force.** | — | Added |
| s.45 | s.65(3): CIIRP reference | — | Added |
| s.47 | s.67A: CIIRP reference | — | Added |
| s.60 | s.208(1)(cb): IP functions in CIIRP | — | Added |
| s.67 | s.224: Insolvency and Bankruptcy Fund (sources and purposes) | — | Added |
| s.69(b) | s.239(2): rule-making heads (omits (ea); inserts (ff) s.58B, (fg) s.58C fee, (fh) s.59A, (zi)/(zia)/(zib) s.224, (zma) s.240C) | — | Added |
| s.70(b)(xx) | s.240(2): regulation heads (zla), (zlb)… for s.58B | — | Added |

**In force from 26 May 2026, with deadline or point-in-time impact (feeds the rules doc):**

| Amending § | Effect | Verified words |
|---|---|---|
| s.4 | Substitutes **IBC s.7(5)** and omits the s.7(4) proviso | "(5) The Adjudicating Authority shall, **within fourteen days of the receipt of the application** under sub-section (2), by an order— (a) admit … (b) reject …"; first proviso: notice "to rectify the defect … within seven days"; second proviso: if no order "within a period of fourteen days … it shall record the reasons for such delay in writing". *Because of the statute's own second proviso, the rules doc should treat the 14 days as **DIRECTORY** unless case law says otherwise (TO VERIFY WITH PARTNER).* |
| s.5, s.6 | Amend IBC ss.9, 10 (parallel changes; text in [R19]) | — rules doc to quote |
| s.8 | Substitutes s.12A (withdrawal) | — rules doc to quote |
| s.25 | "Sections 38, 39, 40, 41 and 42 of the principal Act shall be omitted." This removes the liquidation claims process, including the **s.42 appeal against the liquidator's decision**. | Verified. India Code TOC shows "38. Omitted. … 42. Omitted." |
| s.39 | "In Part II of the principal Act, Chapter IV shall be omitted." (Fast-track CIRP, ss.55–58) | Verified. India Code TOC shows "OMITTED" |
| s.44 | Inserts s.64A (penalty for frivolous or vexatious proceedings; India Code prints "Peralty") | TOC verified |

**Point-in-time test vectors for the IBC** (to 05/06):
1. An s.7 application filed 20 May 2026: s.7(5) applies **as it stood before 26.05.2026**; transitional treatment is **TO VERIFY WITH PARTNER**.
2. An s.7 application filed 27 May 2026: the new s.7(5) applies.
3. Any query about CIIRP (s.58A) as of 1 Oct 2026: answer "**enacted, not in force**".
4. A s.42 appeal against a liquidator's decision dated 1 Jun 2026: s.42 is omitted, so the rules doc must find the replacement route. **Do not compute a deadline.**

**Secondary-source warning.** A Taxmann post (29 May 2026, updated 1 Sep 2026) on the commencement notification lists "Chapter IV-A creditor-initiated process" among the amendments without stating that it is excluded from S.O. 2625(E) [R46]. This is exactly the error the point-in-time model must prevent: commencement facts come only from the gazette (21_india §1, conclusion 1).

### 5.2 Corporate Laws (Amendment) Bill 2026

| Fact | Finding | Tag |
|---|---|---|
| Introduction | Lok Sabha, **23 Mar 2026**, Ministry of Corporate Affairs; amends the Companies Act 2013 and the LLP Act 2008 | verified [R43] |
| JPC referral | PRS: "In Committee — Joint Parliamentary Committee — Mar 23, 2026". News: the Lok Sabha approved the referral motion on 23 Mar 2026 and the Rajya Sabha concurred on 24 Mar 2026 | verified (PRS) / snippet (news) [R43][R44] |
| JPC report | "Report — Joint Parliamentary Committee — **Aug 03, 2026**"; chair Sudhir Gupta (PRS JPC summary) | verified [R43]; snippet [R45] |
| Composition | Reported variously as 31 and 24 members | conflicting `snippet`: do not use |
| Status at 1 Oct 2026 | No passage recorded on PRS; pending consideration and passing | verified (absence on PRS) [R43] |
| Product treatment | **Watchlist only; never law.** Store `bill.status` events. Show "Bill — not law" banners on any Companies Act or LLP section the Bill touches (from the PRS bill text PDF). If it passes, the Act and its commencement notifications enter via the e-Gazette. | — |

---

## 6. MVP corpus size and ingestion plan

### 6.1 Size estimate

**Basis.** Counts are observed where marked ✓ and estimated elsewhere. Pages and tokens are estimates.
- SC sample: 19 pages and 24.1k characters (≈ 320 tokens a page).
- Tribunal and HC pages assumed at ≈ 450 tokens a page.

| Source | Docs (backfill) | Avg pages | Pages | Tokens (≈) | Daily delta (docs) |
|---|---|---|---|---|---|
| SC: AWS SCR set (all years, English) | 35,000 ✓(registry) | 15 | 525k | 170M | — |
| SC: sci.gov.in widget + INSC gap-fill (2023–26 non-SCR, cited only) | 1,000 | 12 | 12k | 4M | 5–6 judgments + ~20 orders |
| NCLAT judgments 2017–2026 | 15,000 (est.) | 15 | 225k | 100M | 3–8 J + 60–110 D |
| IBBI mirror (NCLT 31,792 ✓, NCLAT 5,700 ✓, SC 844 ✓, HC 612 ✓) | 38,948 (dedupe → ≈ 33k new) | 10 | 330k (≈ 30% OCR) | 150M | ≈ 15–20 |
| Delhi HC corporate slice 2019–26 (AWS) | 45,000 (≈ 6.1k/yr ✓ 2025) | 6 | 270k | 120M | ≈ 25 |
| Bombay HC OS commercial/arb finals 2021–26 (AWS) | 22,000 (≈ 4.3k/yr ✓ 2025) | 6 | 130k | 60M | ≈ 20 finals (+ ≈ 35 interim, watched only) |
| SEBI orders (smid 1,2,3,6,7,133) | 24,400 ✓ | 12 | 290k | 130M | 5–15 |
| CCI (if enabled) | 2,700 ✓ | 20 | 54k | 25M | ≈ 1 |
| Statutes: 16 Acts + ≈ 60 rules/regs + PIT snapshots (≈ 55) | ≈ 135 instruments (≈ 5k sections) | — | ≈ 12k | 6M | event-driven |
| Circulars and notifications (SEBI 2,936 ✓, IBBI 197 ✓, RBI FEMA ≈ 300, MCA ≈ 1,500 (est.), gazette corp ≈ 1,000/yr) | ≈ 6,000 | 6 | 36k | 15M | 3–10 |
| **Total** | **≈ 175k docs** | | **≈ 1.9M pages** | **≈ 0.8B tokens** | **≈ 200–300 docs/day** |

**Cost implications** (rough; for doc 04):
- Raw PDFs ≈ 150–250 GB, extrapolated from the AWS averages: HC ≈ 80 KB per PDF (Delhi 2025: 4.14 GB / 53k); SC ≈ 190 KB per English PDF (2025: 168.7 MB / 897).
- OCR ≈ 100k pages.
- Embeddings of 0.8B tokens are cheap.
- **LLM enrichment** (headnote, treatment, holdings) is the cost driver. Restrict it to the corporate-filtered SC subset, NCLAT judgments, NCLT final orders (IBBI "Admission/Approval/Liquidation" remarks), and HC finals, about **60–70k documents**.

### 6.2 Ingestion plan (order, legal gate, cadence)

| Wk | Step | Legal gate prerequisite |
|---|---|---|
| 0–1 | Archive ToU, robots and copyright pages for every source as `terms_ref`. Send **permission/notice emails**: SEBI, CCI, Delhi HC (copyright "permission by mail"); NCLT, NCLAT (hyperlink "prior permission"); IBBI (link courtesy notice); SAT and NCLT registries (data-access request). Test MCA and sci.gov.in from India egress. | Profiles `PROVISIONAL`. Counsel reviews Q1–Q6 before step 3. |
| 1–2 | **Statutes first**:<br>(a) IBC PIT (IC PDF + IBBI snapshots + Act 6/2026 + S.O. 2625(E));<br>(b) CIRP and Liquidation Regs PIT (IBBI-U);<br>(c) Companies Act, NCLT/NCLAT Rules, Limitation Act, GCA, Arbitration Act, CCA, CPC, NI Act, Contract Act, SRA;<br>(d) SEBI Act + PIHIP Rules + Settlement Regs + LODR/SAST/PIT/ICDR;<br>(e) FEMA + key rules + MDs. | Statute views carry commentary (Q7) |
| 2–4 | **NCLAT** judgments backfill (night IST, ≤ 1 req/3 s), then daily delta. **IBBI** mirror backfill (all four sections) and daily delta. | `NCLAT`, `IBBI_ORDERS` APPROVED |
| 3–5 | **SC**: sync the AWS SCR set; widget delta (HOT); weekly INSC gap report. | `AWS_SC`, `SCI_JUDGMENTS` |
| 4–6 | **HC**: sync AWS Delhi and Bombay parquet first, apply the case-type allow-list, then fetch only the selected PDFs (tar parts). Weekly sync. | `AWS_HC_*` (Q6 noted) |
| 5–7 | **SEBI** orders backfill + RSS; circulars + master circulars. **RBI** RSS + MDs. **e-Gazette** poll. **PRS** watch. **IBBI** legal framework poll. | SEBI permission sent (Q1) |
| 6–8 | **Hearing feeds**: NCLT/NCLAT cause-list PDFs and public notices parsed against the watchlist. SC, HC and SAT hearings entered manually. | — |
| 8+ | Gap-fill: IK for unresolved citations (spend cap); partner uploads; CCI if ranked. | IK contract; Q9 |

**Daily schedule (IST).**

| Class | Sources |
|---|---|
| HOT, 30 min from 09:00–22:00 | SC widget; SEBI RSS; RBI RSS |
| WARM, 2–4 h | NCLAT display board; IBBI orders; e-Gazette; NCLT/NCLAT cause lists and notices (evening) |
| COOL, daily or nightly | SEBI listings; IBBI legal framework; RBI MDs; CCI |
| Weekly | AWS HC/SC sync; PRS; India Code re-snapshot of watched Acts |

### 6.3 Sources needed per capability (all 11)

| # | Capability | Required sources | Nice-to-have |
|---|---|---|---|
| 1 | Research Q&A pinned to paragraphs | SC (AWS + widget), NCLAT, IBBI mirror, Delhi/Bombay HC (AWS), statutes (IC, IBBI-U, SEBI) | IK gap-fill, SEBI orders, CCI |
| 2 | Citator / authority status | SC full set incl. non-SCR via INSC gap list; NCLAT; HC finals; IBBI remarks as weak outcome labels | SEBI "Orders of Courts" |
| 3 | Notice → strategy memo | Statutes + rules + regs per trigger (IBC + CIRP Regs, Companies Act + NCLT Rules + Adjudication of Penalties Rules, SEBI Act + PIHIP Rules + Settlement Regs, Arbitration Act, NI Act, CCA/CPC); leading SC/NCLAT/HC cases | SAT orders (thin) |
| 4 | Rules-based deadlines / limitation | **Point-in-time IBC** (§5), CIRP/Liq Regs PIT, Limitation Act, GCA s.9/s.10, CCA, Arbitration Act; **court calendars and holidays** (NCLT `/nclt-calender`, `/notifcation-holidays`; NCLAT `/calendar`; SC calendar *unverified*) | — |
| 5 | Matter workspace | Partner uploads (`USER_UPLOADED`) | — |
| 6 | Drafting help | Statutes; NCLT/NCLAT forms pages; partner templates | — |
| 7 | Cite-check | Citation resolver over SC (INSC/SCR), NCLAT, HC (neutral cites), statutes (IC section ids); IK for unresolved cites | — |
| 8 | Alerts | SEBI RSS, RBI RSS, IBBI framework, e-Gazette, MCA (if unblocked), new judgments in watched topics | PRS |
| 9 | Daily digest + watchlists | Same as 8, plus NCLAT/IBBI/SC deltas and PRS bill status | — |
| 10 | Hearing / cause-list tracking | NCLT cause lists + public notices; NCLAT cause lists + notices; **manual entry** for SC, HC and SAT | NCLT case history (if counsel approves) |
| 11 | Lawyer feedback capture | none (internal) | — |

---

## 7. Risks and counsel questions

### 7.1 Risks

| # | Risk | Likelihood / impact | Mitigation |
|---|---|---|---|
| R-1 | **No open route to official NCLT orders** (CAPTCHA). The IBBI mirror covers IBC only, is uncertified and partly image-only. | Certain / High for Companies Act work (s.241–242, schemes) | IBBI + OCR; partner uploads; NCLT data-access request; IK gap-fill; show "uncertified copy" badge |
| R-2 | **SC non-SCR judgments since 2023 are missing** from bulk; SC search and cause list are CAPTCHA-gated. | Certain / Medium | Widget delta from go-live; INSC gap list; IK for cited items; manual entry for hearings |
| R-3 | **SAT is effectively dark** (sat.gov.in 503; satweb CAPTCHA; SEBI mirror stops in 2015). | Certain / Medium (the SAT trigger runs in general mode) | Partner uploads; IK; Registrar request; monthly re-probe |
| R-4 | **MCA blocked (403)** from our egress. MCA general circulars have no other official route. | High / Medium | India-resident egress test in week 1; gazette fallback for notifications; manual upload of circulars |
| R-5 | **India Code internal inconsistency** (SECTION items stale vs PDF; unreliable `last_modified`). | Certain / High for deadline rules | PDF canonical; diff SECTION vs PDF; commencement only from the gazette; law-current-to computed from the latest w.e.f. footnote |
| R-6 | **AWS HC provenance** (mobile-API rows; scraper not public; `pdf_exists` unreliable); AWS SC lag ≈ 3 months. | Medium / Medium | `OPEN_DATASET` tier; sample-verify against court copies; official copy wins when present |
| R-7 | **ToU "permission by mail"** (SEBI, CCI, Delhi HC) and "prior permission for hyperlinks" (NCLT, NCLAT). | Medium / Medium (reputational) | Send requests in week 1; log replies in `terms_ref`; counsel opinion on s.52(1)(q)(iv) precedence |
| R-8 | **Scraper fragility**: NCLAT POST/CSRF flow, ASP.NET session on e-Gazette, leaf-only TLS chain, Drupal/Laravel redesigns. | High / Medium | Fixture tests; yield alerts ("0 items on a working day"); AIA chasing; never disable TLS verification |
| R-9 | **Upload lag misread as order date** (IBBI ≈ 2 working days in our sample; NCLAT 1–2 days). | Medium / High for deadlines | Order date from the document only; the upload date is stored as `first_seen_at` |
| R-10 | **Privacy**: Delhi HC *Laksh Vir Singh Yadav* (29 May 2026) name-search suppression applies to "other hosts" (21_india §2.5); DPDP phases. | Medium / High | `doc.redacted.v1` flow from day 1; no name-search on suppressed parties |
| R-11 | **The Corporate Laws (Amendment) Bill passes in the Winter Session** and is notified piecemeal. | Medium / High | Gazette watch; PRS weekly; PIT machinery reused from the IBC |
| R-12 | **IK dependence** grows beyond gap-fill. | Medium / Medium | Spend cap; IK-only share < 5%; purgeable prefix |

### 7.2 Counsel questions (→ doc 07)

| Q | Question | Why it matters | Sources affected |
|---|---|---|---|
| Q1 | SEBI, CCI and Delhi HC copyright policies ask for "proper permission by sending a mail" before reproduction. Does s.52(1)(q)(iv) (judgments and orders of a court, tribunal or "other judicial authority") override this for orders? Are SEBI WTM/AO orders "other judicial authority"? Are non-gazetted SEBI circulars reproducible without permission? | Display of full text | `SEBI_ORDERS`, SEBI circulars, `CCI`, `DHC_SITE` |
| Q2 | NCLT and NCLAT hyperlinking policies require "prior permission" for links. Is deep-linking to their PDFs in a closed SaaS covered? Should we request permission (recommended)? | Source links in the UI | `NCLT_*`, `NCLAT` |
| Q3 | IBBI-hosted orders are "not certified copies", and some are re-rendered (Word/Google Docs). May we display them as the text of the order with a disclaimer? May paragraph anchors rest on them where no official copy exists? | Pinned answers, cite-check | `IBBI_ORDERS` |
| Q4 | Is **HUMAN_ASSISTED** capture (a person solves a CAPTCHA to fetch one watched matter's order or cause list) consistent with the ToU and IT Act s.43, for SC search, NCLT order-by-date and case status, SAT, and Delhi HC? What daily cap applies? | Hearing tracking, gap-fill | `SCI_SEARCH`, `NCLT_*`, `SAT_PORTAL`, `DHC_SITE` |
| Q5 | Is scripted use of a site's **own unauthenticated POST search** (CSRF token and session cookie, no CAPTCHA, robots-allowed) acceptable? This covers the NCLAT display board, the CCI DataTables JSON and the NCLT e-filing case-history AJAX. | Core NCLAT/CCI adapters | `NCLAT`, `CCI`, `NCLT_CASEHISTORY` |
| Q6 | Is using the CC-BY AWS SC/HC datasets risky when they were derived from CAPTCHA-gated portals and an unpublished mobile API (02_P0 Q)? | Bulk HC/SC history | `AWS_*` |
| Q7 | s.52(1)(q)(ii): is annotated display of Acts with our version history sufficient "original matter"? Is a bare-Act bulk export prohibited? | Statute views, exports | IC |
| Q8 | May SCR official headnotes be shown? (Our MVP policy: no headnotes; link only.) | SC display | SCR |
| Q9 | IK: retention after termination; use of IK metadata for alias tables (02_P0 §11). | Gap-fill | IK |
| Q10 | Bills (e.g. the Corporate Laws (Amendment) Bill text) are not covered by s.52(1)(q). Are excerpts plus a link enough? PRS content is CC-BY 4.0; the Bill text PRS hosts is Parliament's. | Watchlist | PRS / sansad |
| Q11 | For deadline features, may limitation be computed from the order date printed on an uncertified mirror copy, with the s.12 Limitation Act certified-copy exclusion left to user input? Or must the tool always ask for the certified-copy date? | Deadline UX | All |
| Q12 | Does the Delhi HC privacy judgment (*Laksh Vir Singh Yadav*, 29 May 2026) bind us as an "other host", and must we honour name-search suppression across tenants? | Privacy | All judgments |

---

## References

Probes were run on 2026-10-01 from this session's egress. "verified" means fetched and read in this session; "snippet" means a search-result summary only.

- [R1] NCLT robots.txt — https://nclt.gov.in/robots.txt — verified
- [R2] NCLT Order Date search (CAPTCHA) — https://nclt.gov.in/order-date-wise ; case status — https://nclt.gov.in/diary-number-wise — verified
- [R3] NCLT Copyright Policy — https://nclt.gov.in/copyright-policy — verified
- [R4] NCLT Hyperlinking Policy — https://nclt.gov.in/hyper-linking-policy ; Terms — https://nclt.gov.in/terms-conditions — verified
- [R5] NCLT cause lists and homepage public notices — https://nclt.gov.in/all-cause-list ; https://nclt.gov.in/ — verified
- [R6] NCLT e-filing Case History — https://efiling.nclt.gov.in/casehistorybeforeloginmenutrue.drt — verified (markup only); archive.nclt.gov.in unreachable
- [R7] NCLT Act & Rules — https://nclt.gov.in/act-rule — verified
- [R8] NCLAT robots.txt — https://nclat.nic.in/robots.txt — verified
- [R9] NCLAT homepage and display board (orders/judgments search, view_order flow, sample PDF) — https://nclat.nic.in/ ; https://nclat.nic.in/display-board/orders ; https://nclat.nic.in/display-board/judge — verified
- [R10] NCLAT Copyright Policy — https://nclat.nic.in/copyright-policy ; Terms — https://nclat.nic.in/terms-conditions — verified
- [R11] NCLAT Hyperlinking Policy — https://nclat.nic.in/hyper-Linking-Policy — verified
- [R12] NCLAT judgments and daily orders before 31.05.2021 — https://nclat.nic.in/judgement-data ; https://nclat.nic.in/daily-order-data — verified
- [R13] NCLAT Act & Rules — https://nclat.nic.in/act-rules — verified
- [R14] IBBI orders (counts, remarks, disclaimer, sample PDFs) — https://ibbi.gov.in/orders/nclt ; https://ibbi.gov.in/orders/nclat ; https://ibbi.gov.in/orders/supreme-court ; https://ibbi.gov.in/orders/high-courts ; robots: https://ibbi.gov.in/robots.txt (error page) — verified
- [R15] IBBI Website Policy (ToU, copyright, hyperlink) — https://ibbi.gov.in/home/website-policy — verified
- [R16] IBBI Legal Framework, Act — https://ibbi.gov.in/legal-framework/act — verified
- [R17] IBBI Legal Framework, Updated (consolidated regulation snapshots) — https://ibbi.gov.in/legal-framework/updated (pages 1–8) — verified
- [R18] IBBI Rules, Notifications, Circulars — https://ibbi.gov.in/legal-framework/rules ; https://ibbi.gov.in/legal-framework/notifications ; https://ibbi.gov.in/legal-framework/circulars — verified
- [R19] Insolvency and Bankruptcy Code (Amendment) Act, 2026 (No. 6 of 2026), Gazette CG-DL-E-06042026-271594 (IBBI copy) — https://ibbi.gov.in/uploads/legalframwork/2026-04-07-115842-i5nsk-7ed69ef2a4d23a8b0d472cc0fcd55e79.pdf — verified (full text extracted)
- [R20] MCA Notification S.O. 2625(E), 22 May 2026, Gazette No. 2533, CG-DL-E-25052026-272855 (IBBI copy) — https://ibbi.gov.in/uploads/legalframwork/d31669ba7f826ee9ebefe58e85d652ec.pdf — verified (full text extracted)
- [R21] Supreme Court website: homepage widget, sci-get-pdf sample (2026 INSC 1072), robots, search pages with siwp CAPTCHA — https://www.sci.gov.in/ ; https://www.sci.gov.in/robots.txt ; https://www.sci.gov.in/judgements-judgement-date/ ; https://www.sci.gov.in/cause-list/ ; https://www.sci.gov.in/sci-get-pdf/?diary_no=130912026&type=j&order_date=2026-09-30&from=latest_judgements_order — verified
- [R22] SC Website Policies and Disclaimer — https://www.sci.gov.in/website-policies/ ; https://www.sci.gov.in/disclaimer/ — verified
- [R23] SCR portal search (CAPTCHA) — https://scr.sci.gov.in/scrsearch/ — verified
- [R24] AWS Open Data registry, Indian Supreme Court Judgments — https://raw.githubusercontent.com/awslabs/open-data-registry/main/datasets/indian-supreme-court-judgments.yaml — verified
- [R25] SC dataset documentation (marked "OUTDATED" by its authors) — https://github.com/vanga/indian-supreme-court-judgments/blob/main/opendata/docs/dataset.md — verified
- [R26] SC dataset S3 indexes and 2026 parquet — https://indian-supreme-court-judgments.s3.ap-south-1.amazonaws.com/metadata/tar/year=2026/metadata.index.json — verified
- [R27] AWS Open Data registry, Indian High Court Judgments — https://raw.githubusercontent.com/awslabs/open-data-registry/main/datasets/indian-high-court-judgments.yaml — verified
- [R28] HC dataset documentation and court codes — https://github.com/vanga/indian-high-court-judgments/blob/main/opendata/docs/dataset.md ; https://github.com/vanga/indian-high-court-judgments/blob/main/opendata/docs/high_courts.csv — verified
- [R29] HC dataset S3 parquet and indexes (Delhi `7_26/dhcdb` 2025–2026; Bombay `27_1/newos` 2025 web and mobile) — https://indian-high-court-judgments.s3.ap-south-1.amazonaws.com/metadata/parquet/year=2025/court=7_26/bench=dhcdb/metadata.parquet ; …/year=2025/court=27_1/bench=newos/metadata-mobile.parquet — verified (our tabulation)
- [R30] Delhi HC Copyright Policy — https://delhihighcourt.nic.in/web/copyright-policy — verified
- [R31] Delhi HC Latest Judgments (error) and judge-wise search (CAPTCHA) — https://delhihighcourt.nic.in/web/judgement/fetch-data ; https://delhihighcourt.nic.in/app/sitting-judge-wise — verified
- [R32] Bombay HC sites unreachable (connection reset; TLS legacy renegotiation) — https://bombayhighcourt.nic.in/ ; https://bombayhighcourt.gov.in/ — verified (probe failure)
- [R33] SAT: legacy site 503; new portal orders (CAPTCHA) and terms — https://sat.gov.in/ ; https://satweb.sat.gov.in/orders ; https://satweb.sat.gov.in/terms-of-services — verified
- [R34] SEBI robots, RSS and website policy — https://www.sebi.gov.in/robots.txt ; https://www.sebi.gov.in/sebirss.xml ; https://www.sebi.gov.in/website-policy.html — verified
- [R35] SEBI orders listings by sub-type — https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&ssid=9&smid=0 (and smid=1,2,3,6,7,133) — verified
- [R36] SEBI Acts, Rules, Regulations, Circulars, Master Circulars listings — https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=3&smid=0 (ssid=1,2,3,6,7) — verified
- [R37] CCI robots, antitrust/combination order listings (JSON), copyright policy — https://www.cci.gov.in/robots.txt ; https://www.cci.gov.in/antitrust/orders ; https://www.cci.gov.in/combination/orders-section31 ; https://www.cci.gov.in/contents/copyright — verified
- [R38] India Code migration notice — https://www.indiacode.nic.in/ — verified
- [R39] India Code DSpace REST API, IBC item, IBC PDF (A2016-31.pdf), IBC s.7 SECTION item, Advocates Act s.39 SECTION item — https://indiacode.gov.in/server/api ; https://indiacode.gov.in/server/api/core/items/37c94edf-7892-4c4f-a284-0c24613a4bf5 ; https://indiacode.gov.in/server/api/core/bitstreams/bf689ae0-08e3-47e2-92f2-1711a774254e/content — verified
- [R40] MCA website 403 (Akamai) — https://www.mca.gov.in/content/mca/global/en/home.html — verified (blocked)
- [R41] e-Gazette homepage (Recent Extraordinary Gazettes), leaf-only TLS chain, AIA intermediate — https://egazette.gov.in/ ; http://yr2.i.lencr.org/ — verified
- [R42] RBI notifications RSS, RSS index, Master Directions, Disclaimer — https://www.rbi.org.in/notifications_rss.xml ; https://www.rbi.org.in/Scripts/rss.aspx ; https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx ; https://www.rbi.org.in/Scripts/Disclaimer.aspx — verified
- [R43] PRS Billtrack, The Corporate Laws (Amendment) Bill, 2026 (status timeline; CC-BY 4.0 footer; bill text and JPC report links) — https://prsindia.org/billtrack/the-corporate-laws-amendment-bill-2026 — verified
- [R44] News on the JPC referral — https://www.thenewsminute.com/news/lok-sabha-gives-nod-for-referring-corporate-laws-amendment-bill-to-jpc ; https://www.outlookbusiness.com/economy-and-policy/lok-sabha-refers-corporate-laws-amendment-bill-to-jpc — snippet
- [R45] JPC report coverage — https://studycafe.in/jpc-submits-report-on-corporate-laws-amendment-bill-2026-in-lok-sabha-check-key-recommendations-426369.html ; https://prsindia.org/billtrack/prs-products/prs-jpc-report-summary — snippet
- [R46] Taxmann, "Government Notifies IBC Amendment Act 2026 Provisions" (29 May 2026; updated 1 Sep 2026) — https://www.taxmann.com/post/blog/government-notifies-ibc-amendment-act-provisions/ — verified (WebFetch summary; used only as an example of an imprecise secondary source)
- [R47] Secondary commentary on non-notified CIIRP, group and cross-border provisions — https://blog.ipleaders.in/cross-border-and-group-insolvency-under-the-ibc-amendment-act-2026/ ; https://www.barandbench.com/law-firms/view-point/the-insolvency-and-bankruptcy-code-amendment-act-2026-a-comprehensive-analysis — snippet
- [R48] Foreign Exchange (Compounding Proceedings) Rules, 2024 (G.S.R. 566(E), 12 Sep 2024) — https://www.ey.com/en_in/technical/alerts-hub/2024/12/mof-and-rbi-issued-new-rules-and-directions-respectively-on-compounding-under-fema — snippet
- [R49] RBI new website, FEMA Master Directions — https://website.rbi.org.in/web/rbi/foreign-exchange-management/master-directions — snippet
- [R50] Blueprint: 02_P0_source_acquisition.md §2.1, §3.1–§3.4, §5.1–§5.2, §10, §11; 21_india_specific_legal_data.md §1–§2 (Copyright Act s.52(1)(q) text at [IN-1]; EBC v. Modak at [IN-3]; Laksh Vir Singh Yadav at [IN-55]) — internal; the legal texts were not re-fetched this session (unverified here)
