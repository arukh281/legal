# P0 — Source Acquisition

**Abstract.** P0 acquires every public legal document the platform relies on. That covers Supreme Court, High Court and tribunal judgments and orders, Acts, Rules, notifications, gazettes, and regulator circulars. P0 gets them only through routes that are lawful and defensible. It stores the exact bytes it fetched as immutable, content-addressed blobs, with WARC-grade provenance. It works out whether each source record is new, changed, deleted or unchanged, and emits one `raw.captured.v1` event per material observation. The design follows six rules:
- **Legal-gate-as-code.** No adapter runs unless its source has an approved, current legal profile. CAPTCHA-gated portals are never solved by machines.
- **Seed first, then delta.** The CC-BY open datasets seed the historical backfill. That covers about 17.8M High Court judgments and the Supreme Court from 1950 [P0-1][P0-2][P0-3]. Daily freshness then comes from direct, polite polling of official listings.
- **Durable workflows.** Temporal workflows run discovery, capture and backfill with checkpointed cursors.
- **Normalized fingerprints** detect change, so re-generated PDFs do not look like new versions.
- **Calendar-aware yield models** catch silent scraper failures, which cause most coverage loss.
- **Measured freshness SLOs** are tracked separately from source-side lag, which we cannot control.

P0 is cheap in compute (well under 1 TB/yr of new raw data). Its real cost is adapter maintenance and legal diligence, so the design puts its effort there.

---

## 1. Purpose and scope

**Purpose.** Produce a complete, current, provenance-bearing mirror of the public Indian legal corpus. It must be complete enough that a missing judgment is a measured, alerted exception and not a silent gap. It must be current enough that an overruling pronounced today can propagate to client matters today. It must be provable enough that we can show exactly what the official source published, and when.

**In scope**
1. The **source registry** and a **legal profile** per source: terms of use (ToU) snapshots, robots policy, access-control class, permitted access modes, attribution duties, and reviewer sign-off.
2. **Discovery**: listing pages, RSS/XML feeds, date-wise search pages, JSON back-ends of single-page-app (SPA) portals, bulk datasets and licensed APIs.
3. **Capture**: HTTP and headless-browser fetch; WARC archival; content-addressed raw storage.
4. **Scheduling**: hot/warm/cool polling classes, rolling re-scans, backfills, targeted acquisition.
5. **Change detection and dedup at the source-record level**: NEW, CHANGED, UNCHANGED, DELETED, REAPPEARED, METADATA_CHANGED (proposed).
6. **Resilience**: outages, WAF blocks, TLS misconfiguration, soft errors, layout and format drift, and adapter repair.
7. **Freshness, coverage and health SLOs**, and the reconciliation that measures them.
8. **Takedown/suppression** handling when a court orders anonymisation or removal.
9. The **`raw.captured.v1`** event and a read API over raw bytes and capture history.

**Out of scope, owned elsewhere**
- OCR, text extraction, structural parsing, metadata normalisation, citation resolution, Work/Expression/Manifestation identity: **P1**. P0 passes `source_metadata` exactly *as published* and only gives near-duplicate *hints*.
- Point-in-time reconstruction of statutes: P1 and P3. P0 contributes a dated capture history of consolidated texts from day one, which cannot be recreated later.
- Propagation and reprocessing: **P4**.
- Private firm documents: **P7**. P0 never touches tenant data; see §5.9 for how matter-driven demand reaches P0 without tenant attribution.

**Corpus scope by tier.** Tier A is the MVP, Tier B follows within 3 months, and Tier C is the full build. The detailed catalogue is in §5.1.
- **Tier A**: Supreme Court judgments and daily orders; the open-dataset HC backfill; delta for 6–8 high-volume HCs; India Code (central); the central e-Gazette; NCLT, NCLAT and ITAT.
- **Tier B**: the remaining HCs, the other major tribunals, SEBI, RBI, CBIC and CBDT, and Parliament bills.
- **Tier C**: state gazettes, state tribunals, district-court orders for watched cases only, and historical gazette archives.

---

## 2. Input and output contracts

### 2.1 Inputs

**(a) `SourceDescriptor`**: configuration held in the source registry and versioned in git. It is the unit of onboarding.

```yaml
source_id: in.sc.judgments            # stable, dotted
display_name: "Supreme Court of India — Judgments"
issuing_authority: crt_sc             # court/ministry registry id (P1 owns registry; P0 references)
provenance_tier: OFFICIAL_PRIMARY     # see 2.4
adapter: {kind: declarative|code, name: sci_judgments, version: 1.4.2}
discovery:
  mode: listing_by_date               # listing_by_date | rss | sitemap | json_api | bulk_dataset | licensed_api
  window: {rescan_days_daily: 7, rescan_days_weekly: 60, full_sweep: quarterly}
schedule_class: HOT                   # HOT | WARM | COOL | COLD (see 5.4)
calendar: cal_sc                      # court working-day calendar for yield model
politeness: {max_concurrency: 1, min_delay_ms: 2000, daily_request_budget: 20000, night_window_ist: "23:00-07:00"}
egress_pool: in-mum-static-a          # India-resident, fixed, declared IPs
legal_profile_ref: lp_in.sc.judgments@2026-09-01   # must be APPROVED and < 180 days old
record_key: "{diary_no}|{judgment_date}|{file_stem}"
expectations: {model: poisson_weekday, min_daily_on_working_day: 1}
slo: {freshness_p95_min: 30, coverage_target: 0.995}
lang_policy: capture_all_variants
```

**(b) `LegalProfile`**: written by legal review, enforced in code.

```yaml
legal_profile_id: lp_in.sc.judgments@2026-09-01
tou_snapshot_raw_id: sha256:…        # the archived ToU/copyright-policy page itself
robots_snapshot_raw_id: sha256:…
access_control: NONE | CAPTCHA | LOGIN | API_KEY | WAF_GEO
permitted_access_modes: [OPEN]        # OPEN | BULK_DATASET | LICENSED_API | HUMAN_ASSISTED | PARTNER_CONTRIBUTED
content_legal_basis: "Copyright Act s.52(1)(q)(iv)"   # or CC-BY-4.0, GODL, licence contract id
redistribution: {display_full_text: true, attribution: null, restrictions: []}
personal_data_notes: "judgments may contain victim identities — honour court masking; see 5.10"
status: APPROVED | PROVISIONAL | BLOCKED
reviewer: counsel_id, reviewed_at: 2026-09-01, review_due: 2027-03-01
```

**(c) `acquire.requested.v1` (proposed; see 2.5)**: targeted acquisition from P1, P3, P4, the P9 Privacy Gate or ops.

```json
{"type":"acquire.requested.v1","tenant_id":null,
 "data":{"request_id":"acq_01J…","reason":"UNRESOLVED_CITATION|MATTER_WATCH|CORRIGENDUM_SUSPECTED|COVERAGE_GAP|OPS",
  "target":{"scheme":"CNR|NEUTRAL_INSC|NEUTRAL_HC|CASE_NO|SC_DIARY_NO|GAZETTE_ID|URL|CITATION_STRING",
            "value":"DLHC010012342023","court_hint":"crt_dhc","date_hint":"2024-03-11"},
  "priority":"P1|P2|P3","deadline":"2026-10-01T12:00:00+05:30",
  "allowed_access_modes":["OPEN","LICENSED_API"]}}
```

**(d) Operator directives**: `BackfillRequest{source_id, date_range, access_mode, budget}`, `SuppressionOrder{target, authority_ref(order anchor/URL), scope, effective_at}`, `PauseSource{source_id, reason}`.

### 2.2 Output: `raw.captured.v1` (spine §G, with proposed extensions marked ★)

```json
{
 "id":"01J9ZK…", "type":"raw.captured.v1", "specversion":"1.0",
 "source":"p0/capture-worker@2.3.0", "time":"2026-09-30T15:04:11+05:30",
 "subject":"in.sc.judgments/31245-2019|2026-09-30|31245_2019_3_1501_61234_Judgement_30-Sep-2026",
 "tenant_id":null, "traceparent":"00-…", "causation_id":"crawl_run_01J…",
 "idempotency_key":"in.sc.judgments|<record_key>|nfp:pdftext-v1:9f3c…|NEW",
 "schema_version":"1.1",
 "data":{
  "raw_id":"sha256:4be1…", "source_id":"in.sc.judgments",
  "source_record_key":"31245-2019|2026-09-30|31245_2019_3_1501_61234_Judgement_30-Sep-2026",
  "url":"https://www.sci.gov.in/…/31245_2019_…pdf", "fetched_at":"2026-09-30T15:04:09+05:30",
  "http":{"status":200,"etag":"\"a1b2\"","last_modified":"Tue, 30 Sep 2026 09:21:00 GMT","content_type":"application/pdf"},
  "storage_uri":"s3://plc-raw/sha256/4b/e1/4be1…", "byte_size":412233,
  "source_metadata":{"diary_no":"31245/2019","case_no":"C.A. No. 1234/2020","parties":"A v. B",
                     "bench":"HON'BLE …","judgment_date":"30-09-2026","language":"English","neutral_citation":"2026 INSC 812"},
  "change_kind":"NEW",            // NEW|CHANGED|UNCHANGED|DELETED|REAPPEARED|METADATA_CHANGED★
  "prior_raw_id":null, "crawl_run_id":"crun_01J…",
  "terms_ref":"lp_in.sc.judgments@2026-09-01",
  "capture_id":"cap_01J…",                                   // ★ one fetch event; raw_id is content identity
  "norm_fingerprint":{"scheme":"pdftext-v1","value":"9f3c…"}, // ★ basis of change_kind
  "warc":{"file_uri":"s3://plc-warc/in.sc.judgments/2026/09/30/crun_…-0003.warc.gz","record_id":"<urn:uuid:…>","offset":1837221}, // ★
  "fetch_context":{"adapter":"sci_judgments@1.4.2","access_mode":"OPEN","egress_region":"ap-south-1",
                   "egress_ip":"x.x.x.x","tls_leaf_sha256":"…","browser":false},  // ★
  "provenance_tier":"OFFICIAL_PRIMARY",                       // ★
  "listing_raw_id":"sha256:77aa…",                            // ★ listing page that proves publication
  "first_seen_at":"2026-09-30T15:03:58+05:30",                // ★ first appearance on listing
  "lang_hint":"en",                                           // ★ as published, not detected
  "near_dup_hint":[{"raw_id":"sha256:…","source_id":"aws.odi.sc","simhash_hd":2}], // ★ hint only
  "flags":{"text_layer":"present|absent|unknown","malware_suspect":false,"soft_error_suspect":false}, // ★
  "suppression":null                                          // ★ {reason, authority_ref, scope} when takedown
 }}
```

**Delivery semantics**
- At-least-once delivery.
- Ordered per partition key `source_id|source_record_key`.
- Consumers de-duplicate on `idempotency_key`.
- The event is published from a transactional outbox in the same Postgres transaction that commits the `capture` and `source_record` rows, so there is never an event without a capture, nor a capture without an event.

**`UNCHANGED` policy.** Routine polls that confirm no change are **not** emitted. They only update `last_verified_at`. `UNCHANGED` is emitted only for explicit *verification sweeps*, for example after a backfill or on an audit request, so that P4 and P8 can see "still published as of D". This avoids tens of thousands of no-op events per day.

**`DELETED` semantics.** `DELETED` means *no longer published at source*. A record is marked DELETED only after:
- it is absent from **3 consecutive successful** listing sweeps, **and**
- a direct GET returns 404/410 or a verified soft-404.

It never implies the law changed, and P1 treats it as `manifestation.withdrawn_at`.

**Suppression** is different from DELETED. A court-ordered suppression carries `suppression{…}`, and downstream phases must tombstone derived text (§5.10).

### 2.3 Synchronous read API (for P1, P4, P8 and ops)

```
GET  /v1/raw/{raw_id}                    -> 302 signed URL (India-region), checks suppression ACL
GET  /v1/captures?source_record_key=&source_id=   -> capture history [{capture_id, raw_id, fetched_at, change_kind, warc ref}]
GET  /v1/records/{source_id}/{record_key}         -> current state + version chain
GET  /v1/replay/{capture_id}              -> WARC record (request+response+metadata) for audit/click-to-source
GET  /v1/sources/{source_id}/health       -> freshness, coverage, last success, open incidents
POST /v1/acquire                          -> same body as acquire.requested.v1 (ops/UI)
```

### 2.4 Internal system of record (PostgreSQL)

```sql
CREATE TABLE source (source_id text PRIMARY KEY, descriptor jsonb, legal_profile_id text, status text, tier char(1));
CREATE TABLE legal_profile (legal_profile_id text PRIMARY KEY, source_id text, body jsonb, status text,
  reviewed_at date, review_due date, tou_snapshot_raw_id text, robots_snapshot_raw_id text);
CREATE TABLE crawl_run (crawl_run_id text PRIMARY KEY, source_id text, kind text /*SWEEP|BACKFILL|TARGETED|CANARY|RECONCILE*/,
  window_from date, window_to date, adapter_version text, started_at timestamptz, ended_at timestamptz,
  status text, items_listed int, items_captured int, errors jsonb);
CREATE TABLE source_record (source_id text, record_key text, current_capture_id text, current_raw_id text,
  current_nfp text, state text /*LIVE|DELETED|SUPPRESSED*/, first_seen_at timestamptz, last_seen_at timestamptz,
  last_verified_at timestamptz, last_changed_at timestamptz, source_metadata jsonb, absent_streak int DEFAULT 0,
  PRIMARY KEY (source_id, record_key));
CREATE TABLE capture (capture_id text PRIMARY KEY, source_id text, record_key text, raw_id text, nfp text,
  change_kind text, prior_raw_id text, url text, fetched_at timestamptz, http jsonb, warc_ref jsonb,
  fetch_context jsonb, listing_raw_id text, crawl_run_id text, recorded_at timestamptz DEFAULT now());
CREATE TABLE raw_blob (raw_id text PRIMARY KEY, byte_size bigint, media_type_sniffed text, storage_uri text,
  first_stored_at timestamptz, simhash64 bigint, text_layer text, av_scan text, suppressed boolean DEFAULT false);
CREATE TABLE acquisition_request (request_id text PRIMARY KEY, reason text, target jsonb, priority text,
  status text /*OPEN|FOUND|NOT_FOUND|BLOCKED_LEGAL*/, attempts jsonb, resolved_capture_id text); -- no tenant columns, by design
CREATE TABLE suppression (suppression_id text PRIMARY KEY, target jsonb, authority_ref text, scope text, effective_at timestamptz, created_by text);
CREATE TABLE outbox (event_id text PRIMARY KEY, partition_key text, payload jsonb, created_at timestamptz, published_at timestamptz);
```

**`provenance_tier`** is an ordered enum that P1 uses to choose the canonical manifestation. From most to least preferred:
1. `OFFICIAL_PRIMARY`: the issuing court's or ministry's own site.
2. `OFFICIAL_AGGREGATOR`: eCourts, SCR, India Code, e-Gazette.
3. `OPEN_DATASET`: CC-BY mirrors.
4. `LICENSED_THIRD_PARTY`: for example, the Indian Kanoon API.
5. `PARTNER_CONTRIBUTED`.

### 2.5 Proposed spine changes

| # | Target | Change | Justification |
|---|---|---|---|
| 1 | `raw.captured.v1` | Add `capture_id`, `norm_fingerprint`, `warc{}`, `fetch_context{access_mode,…}`, `provenance_tier`, `listing_raw_id`, `first_seen_at`, `lang_hint`, `near_dup_hint[]`, `flags{}`, `suppression?`. Add `METADATA_CHANGED` to `change_kind`. | `raw_id` is content identity, not a fetch event, so the same bytes are captured many times. Change must be judged on a normalized fingerprint, because regenerated PDFs change bytes without changing content (§5.6). Evidentiary replay needs the WARC reference. P1 needs `provenance_tier` to choose canonical manifestations. P8 and P10 need `first_seen_at` for "known-at" audits. Listing metadata can change (for example, a corrected party name) with identical bytes. |
| 2 | New event `acquire.requested.v1` (P1, P3, P4, P9-gate, ops → P0) | Targeted acquisition by identifier. | Closes the loop from unresolved citations and watched matters to acquisition (§7.1). Without it, coverage gaps are only discovered by users. |
| 3 | New event `source.health.v1` (P0 → P4, P8, P10) | `{source_id, status: OK/DEGRADED/DOWN/BLOCKED, freshness_lag_p95, last_success_at, coverage_estimate, incident_id}` | P8 must lower confidence in a "no negative treatment found" statement when a relevant source is stale. P10 must show a "data current as of" caveat per court. |
| 4 | Spine §I bus | Recommend a Kafka-API log (Redpanda self-hosted, or MSK in ap-south-1) with a Postgres transactional outbox, and Temporal for durable workflows. P4 co-owns the decision. | Low event volume, but P4 needs replay and ordered partitions. Temporal gives checkpointed long backfills (§6.2). |

---

## 3. State-of-the-art survey (with citations)

### 3.1 The Indian official source landscape (as observed, September 2026)

**Supreme Court**
- sci.gov.in publishes judgments, daily orders, cause lists and case status [P0-37].
- The official law reporter is now the **SCR portal** (scr.sci.gov.in). It was formed by merging the eSCR and DigiSCR portals, which have both been decommissioned. It is free, and every judgment has a neutral citation and an official headnote [P0-7].
- e-SCR launched with free access to about 34,000 judgments [P0-8]. Translations were reported at about 37,000 in Hindi, with work under way in every Eighth Schedule language [P0-9].
- The neutral citation format is `YYYY INSC N`. Phase I covered judgments and orders from 1 Jan 2014 onward [P0-10].
- Our probes on 2026-09-30 found:
  - The SCR search page is protected by a **Securimage CAPTCHA**.
  - `www.sci.gov.in` sits behind Akamai and returned **403 "Access Denied"** to our non-Indian cloud egress [P0-33].

**High Courts via eCourts**
- `judgments.ecourts.gov.in` is described as the portal for "judgements and final orders passed by all High Courts". It offers free-text search by court, judge, act, section, party, date and disposal nature [P0-37]. It uses an image and audio CAPTCHA [P0-6], confirmed as Securimage in our probe [P0-33].
- `hcservices.ecourts.gov.in` and `services.ecourts.gov.in` (district courts) also carry Securimage and hCaptcha markup [P0-33].
- A July 2024 Rajya Sabha answer put eCourts at about 26.04 crore (≈260M) cases and about 26.05 crore orders/judgments available [P0-13].
- **NJDG** offers an Open API only to Central and State Government departments, using departmental IDs and access keys. Extension to other users was "planned" [P0-12].
- No general developer API is offered. Third-party SDKs describe the live portals as "CAPTCHA-gated and rate-limited" [P0-4].

**High Court websites (heterogeneous)**
- Delhi HC's judgment listing served without a CAPTCHA, and Allahabad HC exposes RSS.
- Bombay, Madras and Kerala HCs reset, timed out or failed at the proxy from our non-Indian egress [P0-33].
- Delhi HC introduced neutral citations `YEAR:DHC:NNNN` from 17 Oct 2022 [P0-11]. Other HCs followed with court-specific formats (P1 and 21_india doc own the grammar).

**Legislation**
- **India Code** holds central and state Acts and subordinate legislation. Central Acts "are re-typed and updated from time to time" [P0-36]. We found no documented official point-in-time versioning *(unverified; the portal returned 403 to our egress)*.
- The central **e-Gazette** publishes weekly and extraordinary issues. Extraordinary issues appear as and when departments request them [P0-34]. PDFs sit under `egazette.gov.in/WriteReadData/<year>/…` [P0-35]. The site's TLS chain failed verification because the intermediate certificate is not served [P0-33].
- Historical gazettes are mirrored on the Internet Archive [P0-35].
- Nyaykosh (NeGD) publishes some laws as Akoma Ntoso XML with REST APIs, per 03_P1 [P1-34] *(not independently verified by P0; the portal was unreachable from our egress)*.

**Tribunals and regulators**
- NCLT runs Drupal. Its robots.txt **disallows `/search/`**, and the order-by-date page shows a CAPTCHA.
- CAT allows all crawling.
- ITAT, APTEL and e-Gazette serve incomplete TLS chains.
- SAT returned 503.
- e-Jagriti (consumer commissions) is a React SPA backed by a JSON API.
- SEBI, RBI (with RSS/XML) and CCI were reachable without a CAPTCHA [P0-33].

### 3.2 Open and third-party datasets

**AWS Open Data "Indian High Court Judgments"** (Dattam Labs)
- 25 HCs, 45 benches, about 17.8M judgments, about 1.25 TiB of tar archives.
- PDF plus raw JSON plus Parquet metadata, partitioned `year/court/bench`, licensed **CC-BY-4.0**, bucket in ap-south-1 [P0-1][P0-2].
- Most records come from the eCourts judgments website. Gaps were filled from the **eCourts mobile API** (`source="mobile"`).
- Recommended dedup key: `(cnr, decision_date, order_number)` [P0-2].
- The registry says "Quarterly" updates, while the dataset docs say daily [P0-1][P0-2]. A downstream SDK reports a lag of 2–3 months [P0-4].

**AWS "Indian Supreme Court Judgments"**: 1950 to present, about 35k judgments plus regional-language versions, about 52.24 GB, CC-BY-4.0, scraped from scr.sci.gov.in. The maintainers ask users to "avoid scraping with high concurrency" [P0-3].

**Indian Kanoon API**
- Prepaid pricing: search ₹0.50, document ₹0.20, fragment ₹0.05, metainfo ₹0.02 per call [P0-16].
- The ToU explicitly permit use of documents "for building context for a Retrieval-Augmented Generation (RAG) system, or for fine-tuning", with conspicuous attribution ("powered by IKanoon"). Either party can terminate with one month's notice [P0-15].

**Commercial reporters (SCC Online, Manupatra)**: licence-only. Their editorial layers are protected (§3.4).

### 3.3 Engineering prior art

- **Juriscraper** (Free Law Project) is the closest analogue.
  - It is a Python library of per-court `Site` classes plus "back-scrapers", tested against recorded example files with expected JSON outputs [P0-25].
  - It watches over 200 court pages every weekday and publishes a daily status email for its scrapers [P0-26].
  - It had 239 open issues when fetched [P0-25]. This is evidence that court-scraper maintenance is continuous, not a one-off build.
- **Web archiving standards**
  - WARC (ISO 28500) has been the canonical capture format since 2009 [P0-29][P0-40].
  - WACZ packages WARCs with a CDXJ index, `pages.jsonl` and a `datapackage.json` of hashes.
  - An optional **signing spec** gives cryptographic proof of who created an archive and when [P0-27][P0-28]. Adopters include Harvard LIL (Perma.cc/Scoop), the Internet Archive and Starling Lab [P0-27][P0-42].
- **Change detection and dedup**
  - HTTP validators (`ETag`, `Last-Modified`, conditional GET) [P0-38].
  - Near-duplicate detection via **simhash** fingerprints with small Hamming-distance thresholds at web scale [P0-30].
  - Canonical JSON (RFC 8785) for API payloads [P0-39].
- **Orchestration**
  - Temporal gives durable execution through event-sourced replay. Completed activity results are recorded and not re-executed after a crash, and workflows can run "for years" [P0-31]. Event histories are size-bounded, so long workflows must "continue-as-new" [P0-41] *(limit values unverified)*.
  - Airflow retries a failed task from the start. It is best suited to scheduled batch DAGs, while Dagster emphasises data-asset lineage [P0-32].

### 3.4 Legal basis

- **Copyright Act 1957 s.52(1)(q)** [P0-17]. It is not infringement to reproduce or publish:
  - (i) matter published in any Official Gazette, *except an Act of a Legislature*;
  - (ii) an Act of a Legislature, *on condition it is reproduced together with commentary or other original matter*;
  - (iv) any judgment or order of a court, tribunal or other judicial authority, *unless the court prohibits it*.
- **Eastern Book Company v. D.B. Modak, (2008) 1 SCC 1** (https://indiankanoon.org/doc/1062099/)
  - Publishers cannot claim copyright in the judgment text. There is copyright in original **headnotes** and in the publishers' own editorial notes and footnotes [P0-18].
  - Secondary summaries report that editor-created paragraphing and editorial labels (concurring/dissenting) were also protected [P0-19] *(para-level verification pending; 21_india doc to confirm)*.
  - EBC later obtained an injunction against LexisNexis and Thomson Reuters in 2014 [P0-20].
  - **Operational consequence:** P0 never ingests reporter-edited text. Court-issued copies are the only source of paragraph numbers.
- **IT Act 2000 s.43** (unauthorised access to a computer system)
  - In Feb 2025 the Minister of State for Electronics and IT, Jitin Prasada, told the Rajya Sabha that scraping for AI training violates s.43. Experts disputed this. One lawyer argued that overriding robots.txt could amount to unauthorised access [P0-21].
  - Indian law does not expressly regulate scraping, and s.43 has not been definitively applied to public-page scraping [P0-22].
  - **Operational consequence:** treat CAPTCHAs, logins and robots disallows as *access-control signals* and never circumvent them.
- **DPDP Act 2023 s.3(c)(ii)** excludes personal data made publicly available by the Data Principal, or by any other person under a legal obligation to publish it [P0-23]. Whether courts' publication of judgments qualifies is **arguable**. We assume judgments contain regulated personal data and honour masking and takedown orders (§5.10).
- **Open licences**
  - The Dattam datasets are CC-BY-4.0 [P0-1].
  - GODL-India (data.gov.in) permits commercial use with attribution [P0-24]. The official GODL page returned 403 to our egress.

---

## 4. Mistakes others made and how we avoid them

| System/paper | What went wrong | Evidence | How we avoid it |
|---|---|---|---|
| Hobbyist and SDK scrapers (e.g. bharat-courts) | Built-in OCR/ONNX **CAPTCHA solvers** against eCourts and SC portals. This is legal exposure (s.43 posture, ToU) and brittle: every CAPTCHA upgrade (Securimage → hCaptcha) breaks them. | [P0-4][P0-21][P0-33] | CAPTCHA never solved by machine. The access ladder (§5.2) goes open listings → CC-BY bulk → licensed API → formal MoU → *human-assisted* capture for low-volume targeted needs, subject to counsel sign-off. |
| AWS HC dataset (Dattam) used as a live feed | Lag of weeks to months; mixed web and mobile-API provenance; update cadence stated inconsistently. | [P0-1][P0-2][P0-4] | Used **only as a backfill seed**, tagged `OPEN_DATASET`. Daily delta comes from official listings. Dedupe on `(cnr, decision_date, order_number)`. Sample-verify against official copies, and prefer `OFFICIAL_*` manifestations when both exist. |
| Juriscraper-style XPath scrapers | Silent breakage on redesigns. Maintenance debt shows in hundreds of open issues. Detection relied on a daily status email. | [P0-25][P0-26] | Contract tests on archived WARC fixtures; **calendar-aware yield models** that alert on "0 items on a working day"; canary URLs; adapter owner on-call; LLM-assisted, fixture-gated repair proposals (§5.8). |
| Aggregators serving HTML text only (e.g. Indian Kanoon as a sole source) | No byte-level official provenance and dependence on one vendor's continuity. The ToU allow one-month termination. | [P0-15] | Official bytes are canonical. IK is a `LICENSED_THIRD_PARTY` gap-filler with attribution. Every IK-only document is queued for official re-acquisition. |
| Copy-edited reporter texts (Modak's CD-ROMs; LexisNexis/Thomson Reuters) | Copying publisher headnotes and editorial layers led to injunctions. | [P0-18][P0-20] | No ingestion of reporter text. Citation strings are stored as facts (spine §D). Legal profile blocks any `commercial_reporter` source unless under licence. |
| Byte-hash change detection (common in naive pipelines) | Dynamically generated PDFs and HTML (timestamps, session tokens, "downloaded on" stamps) produce false "changed" events and re-parse storms. | General web-archiving practice [P0-30]; *specific Indian portal behaviour to be measured* | Change is decided on a `norm_fingerprint` (§5.6). Raw bytes are still always stored. |
| Scrapers that disable TLS verification to get past broken chains | Opens the pipeline to man-in-the-middle substitution of legal text. | Broken chains observed on e-Gazette, ITAT and APTEL [P0-33] | AIA-chasing verifier plus a curated intermediate bundle; the leaf certificate fingerprint is recorded per capture; verification is never disabled. |
| Rotating residential proxies to dodge WAF and geo blocks | ToU breach, and "evasion" undermines any good-faith defence. It gets blocked anyway. | Akamai 403s on sci.gov.in and indiacode for non-Indian egress [P0-33] | Fixed, declared India-resident egress with a contact user agent; blocks escalate to a human and to a whitelisting request, never to evasion. |
| Airflow-style whole-task retries for multi-day backfills | A crash loses progress, and cursors are re-derived ad hoc. | [P0-32] | Temporal workflows with a per-page checkpointed cursor; continue-as-new every N pages [P0-31][P0-41]. |
| Not recording ToU and robots state at capture time | Cannot later show what permissions existed when the data was taken. | — (design gap in most scrapers we reviewed) | `terms_ref` on every event points to the archived ToU and robots snapshot (legal-gate-as-code). |

---

## 5. Recommended design, in detail

### 5.1 Source catalogue

**How to read the Reliability column.** Reliability is what our single-point probe saw on 2026-09-30 from non-Indian egress [P0-33]. It must be re-measured from India-resident egress during onboarding.

**How to read the ToU risk column.** L means an open listing with a statutory basis. M means an access-control or ToU question. H means do not automate without a licence or permission.

| Source | Coverage | Format | Update freq | Reliability (observed) | Access method | Legal basis / ToU risk | Tier |
|---|---|---|---|---|---|---|---|
| SC judgments and daily orders (sci.gov.in) | All SC judgments; daily orders | PDF + HTML listings | Continuous on working days | Akamai WAF; 403 to non-Indian egress | OPEN listing poll (India egress) | s.52(1)(q)(iv); **L** | A |
| SC SCR portal (scr.sci.gov.in) | Reportable judgments with official headnotes; neutral citations; regional translations | PDF + search UI | As reported | Securimage CAPTCHA | HUMAN_ASSISTED targeted only; MoU requested; bulk via AWS SC dataset | Judgments: s.52(1)(q)(iv). Official headnotes are not a "judgment" (open question §11); **M** | A (via dataset) |
| AWS Open Data: Indian SC Judgments | 1950 to present, ~35k + regional versions, 52 GB | PDF, JSON, Parquet | Ongoing | S3, no CAPTCHA | BULK_DATASET | CC-BY-4.0; **L** | A |
| eCourts judgments portal (judgments.ecourts.gov.in) | Judgments and final orders of all HCs | PDF + metadata | Daily | Securimage CAPTCHA (+audio) | Not automated. MoU request to e-Committee/NIC; HUMAN_ASSISTED for gaps | s.52(1)(q)(iv) for content; access control ⇒ **M/H** | A (MoU track) |
| AWS Open Data: Indian HC Judgments | 25 HCs / 45 benches, ~17.8M, 1.25 TiB | PDF, JSON, Parquet | Quarterly (registry) / daily (docs); lag 2–3 months reported | S3 ap-south-1 | BULK_DATASET | CC-BY-4.0; derivation includes mobile API (provenance caveat); **L/M** | A |
| HC own websites (25 HCs) | Varies: judgments, orders, cause lists; some Hindi/regional | HTML listings + PDF; some RSS | Daily, court-specific | Heterogeneous: Delhi open listing; Allahabad RSS; Bombay/Madras/Kerala unreachable from non-Indian egress | OPEN listing poll per HC (declarative adapters) | s.52(1)(q)(iv); per-site ToU; **L–M** | A (6–8 HCs), B (rest) |
| HC services and district services (eCourts) | Case status, orders, cause lists | HTML/PDF | Daily | Securimage/hCaptcha | Not automated. Targeted HUMAN_ASSISTED for watched cases; MoU | Access control; **H** | C |
| NJDG | Aggregate pendency and disposal statistics | Dashboard; Open API for govt departments only | Daily | CAPTCHA markers | Statistics for reconciliation only; apply for API | NDSAP-aligned; **M** | B |
| Indian Kanoon API | Broad SC/HC/tribunal coverage (vendor claims) | JSON/HTML text | Daily (vendor) | Paid API, signed requests | LICENSED_API gap-fill and cross-check | Contract: attribution required; RAG and fine-tune allowed with attribution; 1-month termination; **L (contract)** | A |
| Commercial reporters (SCC Online, Manupatra) | Reported judgments with editorial layers | Proprietary | — | — | Licence only (citation-table data) | EBC v Modak; **H** unless licensed | — |
| India Code | Central + state Acts, subordinate legislation (consolidated) | HTML section views + PDF | On amendment (irregular) | Akamai; 403 to non-Indian egress | OPEN crawl; **snapshot every Act weekly from day 1** | s.52(1)(q)(ii) (Acts need accompanying commentary/original matter); **M** | A |
| e-Gazette (central) | Gazette of India: weekly + extraordinary; Acts, rules, notifications, S.O./G.S.R. | PDF | Daily (extraordinary ad hoc) | TLS intermediate missing | OPEN listing poll | s.52(1)(q)(i) except Acts; **L** | A |
| State gazettes (~36 portals) | State Acts, rules, notifications | PDF | Weekly + extraordinary | Unknown, heterogeneous | OPEN per state | s.52(1)(q)(i); **L** | C |
| Internet Archive gazette mirror | Historical Gazette of India issues | PDF | Static | Good | BULK (historical backfill) | Underlying s.52(1)(q)(i); mirror ToU; **L** | C |
| Nyaykosh (per P1) | Selected laws in Akoma Ntoso | XML + REST | Growing | Unreachable from our egress | OPEN API | Govt open data; **L** *(unverified)* | B |
| Parliament (sansad.in: LS/RS bills, debates) | Bills as introduced/passed | PDF/HTML | Session days | Redirects observed | OPEN | s.52(1)(q)(iii)/(i) partly; **L–M** | B |
| NCLT (nclt.gov.in) | Orders of all benches | PDF | Daily | robots disallows `/search/`; CAPTCHA on order-by-date | Not automated through `/search/`. Use allowed listing pages or MoU; HUMAN_ASSISTED for gaps | s.52(1)(q)(iv); robots/CAPTCHA ⇒ **M** | A |
| NCLAT, ITAT, NGT, CAT, CESTAT, DRT/DRAT, APTEL, TDSAT, SAT | Orders/judgments | PDF | Daily–weekly | CAT robots allow-all; ITAT/APTEL TLS chain broken; SAT 503; NGT apex cert mismatch | OPEN listing poll where permitted | s.52(1)(q)(iv); per-site; **L–M** | A (ITAT, NCLAT), B (rest) |
| Consumer commissions (e-Jagriti) | NCDRC/SCDRC/DCDRC orders | SPA over JSON API | Daily | React SPA | Browser-mode capture of public views; JSON only if ToU permits | s.52(1)(q)(iv); **M** | B |
| Regulators: SEBI orders, RBI notifications/circulars, CCI orders, CBIC, CBDT | Orders, circulars, master directions | HTML/PDF; RBI RSS/XML | Daily | SEBI/RBI/CCI reachable; CBIC reset to non-Indian egress | OPEN (RSS first) | Gazette-published items: s.52(1)(q)(i); others: site ToU; **L–M** | B |
| Partner-firm certified copies | Specific public orders/judgments missing online | PDF | Ad hoc | n/a | PARTNER_CONTRIBUTED via Privacy Gate (public docs only) | Public judgment; consent; **L** | B |

**Estimated daily volumes.** All figures are labelled estimates, to be replaced by measured values within 30 days of launch.

| Stream | Basis | New documents per working day |
|---|---|---|
| SC judgments + orders | 36,969 SC disposals in 2024 [P0-14] ≈ 150/working day of final disposals, plus many more daily orders | 150–600 |
| HC judgments and final orders | "more than 1.2 million" HC disposals in 2024 [P0-14] ÷ ~240 working days | ≈ 5,000 |
| HC interim orders (watched cases only) | Out of bulk scope | 0–500 |
| Tribunals + consumer commissions | *Unverified estimate* | 1,000–3,000 |
| Central + state gazettes | *Unverified estimate* | 150–600 |
| Regulators | *Unverified estimate* | 20–80 |
| **Total** | | **≈ 6,500–10,000/day, ≈ 1.6–2.4M/yr** |

**Bytes.** The HC dataset averages 1.25 TiB ÷ 17.8M ≈ **~75 KB per compressed PDF** [P0-2]. The SC dataset averages about 1.5 MB per judgment including regional versions [P0-3]. The daily delta is therefore about **0.5–1.5 GB/day**, or about 0.2–0.5 TB/yr, before WARC overhead of roughly 1.2×.

**Backfill.** About 17.8M HC + ~35k SC + tribunal archives (a few million, *unverified*) ⇒ **about 20–25M raw documents and ~2–3 TB**.

**Freshness SLOs ("Bloomberg standard").**
- Measured as `first_seen_at` → `raw.captured.v1` published, on source working days.
- Source-side lag (decision date → first appearance at source) is tracked separately. We cannot beat it, but we publish it (§7.5).

| Class | Sources | Poll cadence (IST) | Freshness SLO p95 | Coverage SLO |
|---|---|---|---|---|
| HOT | SC judgments and daily orders; e-Gazette extraordinary; RBI/SEBI | 10 min, 08:00–23:00; hourly otherwise | ≤ 30 min | ≥ 99.5% of items on the official listing |
| WARM | Tier-A HCs; NCLT/NCLAT/ITAT; India Code change feed | 60 min, working hours | ≤ 4 h | ≥ 99% |
| COOL | Other HCs, tribunals, state gazettes | 4–6 h | ≤ 24 h | ≥ 98% |
| COLD | Consolidated-Act snapshots; historical rescans | Daily/weekly | ≤ 7 days | n/a |

The HOT class costs about 100 requests/day per listing, which is trivial load.

### 5.2 The lawful acquisition ladder

For every document class, P0 tries access modes in this order. Each mode must be listed in the source's `permitted_access_modes`, and the legal gate is enforced in the worker, not by convention.

1. **OPEN official listing or feed** from the issuing authority (`OFFICIAL_PRIMARY`) or official aggregator. Rules:
   - Robots rules are honoured.
   - No CAPTCHA, login or WAF challenge may sit in the path.
   - The user agent is declared (`LexTerminalBot/1.0 (+https://…/bot; ops@…)`).
2. **BULK_DATASET** under an open licence (CC-BY, GODL). It seeds history and is never the freshness path.
3. **Formal access** (MoU, data-sharing agreement or registry request) with the e-Committee/NIC, individual HC registries and tribunals. This track starts on day 1 and is a *business-development workstream*, not an engineering dependency. Delivered feeds are onboarded as `OFFICIAL_AGGREGATOR` adapters.
4. **LICENSED_API** (Indian Kanoon) for gap-fill and cross-source reconciliation, within contract terms and with attribution.
5. **HUMAN_ASSISTED capture**, for low-volume, high-value targets such as a watched matter's order or an unresolved SC citation.
   - An operator uses an audited capture console: an isolated browser whose traffic passes through a WARC-writing proxy.
   - The operator solves any CAPTCHA personally.
   - A daily cap per source (default 200) applies.
   - Requires counsel sign-off per source (§11).
6. **PARTNER_CONTRIBUTED**: public documents supplied by the design-partner firm through the P9 Privacy Gate.

**Never:** automated CAPTCHA solving, credential sharing, rotating or residential proxies, robots violations, or reporter texts.

```mermaid
flowchart LR
  subgraph Control
    SR[Source Registry + Legal Profiles] --> GATE{Legal gate}
    ACQ[acquire.requested.v1] --> TQ
  end
  subgraph Orchestration[Temporal]
    SCHED[Schedules HOT/WARM/COOL/COLD] --> SW[SourceSweepWorkflow]
    TQ[TargetedAcquireWorkflow] 
    BF[BackfillWorkflow continue-as-new]
    CAN[Canary + Reconcile + TermsWatch]
  end
  GATE --> SW & TQ & BF
  SW --> DISC[Discover activity: adapter.discover]
  DISC --> FRONT[(Per-host token buckets)]
  FRONT --> HF[HTTP fetcher] & BR[Browser fetcher: Playwright sandbox]
  HF & BR --> WP[WARC writer]
  WP --> S3W[(S3 plc-warc: WARC/WACZ, Object Lock)]
  WP --> CAS[(S3 plc-raw: sha256 CAS)]
  WP --> NF[Normalize + fingerprint + AV scan + simhash]
  NF --> CD[Change decision]
  CD --> PG[(Postgres: source_record, capture, outbox)]
  PG --> OB[Outbox relay] --> BUS[[Kafka-API log: raw.captured.v1 / source.health.v1]]
  BUS --> P1[P1 Parsing] & P4[P4 Propagation] & OPS[Health monitor]
  OPS --> SH[source.health.v1] 
```

### 5.3 Components

| Component | Responsibility | Tech choice |
|---|---|---|
| Source Registry | Descriptors, legal profiles, schedules, SLOs; git-versioned YAML synced to Postgres | Postgres + git |
| Legal gate | Refuses to schedule or execute if the profile is not `APPROVED`, is past `review_due`, or the access mode is not permitted | Library in every worker |
| Orchestrator | Sweeps, backfills, targeted acquisition, canaries, reconciliation, TermsWatch | Temporal (self-hosted or Temporal Cloud; self-hosted in India for residency) |
| Politeness limiter | Per-host token bucket, concurrency ≤ 2, `Retry-After`, night windows, daily budgets | Postgres advisory-lock or Redis token buckets keyed by host |
| HTTP fetcher | Conditional GET (`If-None-Match`/`If-Modified-Since`) where validators exist [P0-38]; AIA-chasing TLS; redirect capture; size caps (200 MB); timeouts | Python `httpx` + `warcio` |
| Browser fetcher | For SPA/JS-only sources (e-Jagriti, some HC sites). Headless Chromium in gVisor sandboxes; traffic through a WARC-writing proxy | Playwright; Browsertrix-crawler for high-fidelity snapshots |
| WARC writer | Request, response and metadata records per fetch; rolls files at 1 GB per crawl run | `warcio`; WACZ packaging daily |
| Normaliser/fingerprinter | Media sniffing; PDF text-layer hash or page-image perceptual hash; HTML boilerplate strip; canonical JSON; simhash64 | Python workers (CPU) |
| AV/safety scan | ClamAV plus PDF structure checks (JS, embedded files, decompression bombs) → `flags.malware_suspect` | Sidecar |
| Change decider | Record-level state machine (§5.6) | Postgres transaction |
| Outbox relay | Publishes events in commit order per partition | Debezium or a simple poller |
| Health monitor | Yield models, freshness lag, error taxonomy, canaries; emits `source.health.v1` and pages on-call | Prometheus/OTel + rules |
| Capture console | HUMAN_ASSISTED captures with full audit | Isolated VDI browser + WARC proxy |

### 5.4 Scheduling

- **Classes.** HOT, WARM, COOL and COLD, as in §5.1, are implemented as Temporal Schedules per source. Their jitter is ±10% so that polls do not all land on the hour.
- **Rolling re-scan windows.** Courts upload late and re-upload corrected versions.
  - Every sweep covers `today`.
  - A daily run covers T-1…T-7.
  - A weekly run covers T-8…T-60.
  - A quarterly full sweep runs at the night-window rate.
- **Calendar awareness.** Each source is bound to a court or office working-day calendar (vacations, holidays), so yield alerts do not fire on non-working days. A Saturday vacation-bench order still produces items, which is why the yield model is probabilistic, not a hard rule.
- **Adaptive revisit** *(heuristic; to validate)*.
  - Learn each source's upload-time distribution, for example HCs uploading in evening batches.
  - Poll at 2× the base rate in the source's top upload-hour quantiles and at 0.5× elsewhere, subject to the SLO floor.
- **Priority lanes** map onto P1's lanes. Anything captured by the HOT class, or by a `MATTER_WATCH` or `UNRESOLVED_CITATION` request, is marked `priority: P1` in `fetch_context`, and P1 routes it to `L0-urgent`.
- **Budgets.**
  - Backfill and delta use separate Temporal task queues and separate per-host budgets.
  - Delta always pre-empts backfill.
  - Backfill uses the 23:00–07:00 IST window on official sites.
  - Bulk datasets (S3) carry no politeness constraint beyond our own cost limits.

### 5.5 Adapter plug-in contract

About 80% of Indian official sources follow a "date-wise listing → detail/PDF link" pattern. They are served by **declarative adapters**: YAML with CSS/XPath or JSONPath selectors plus field mappings. The rest use **code adapters** implementing:

```python
class SourceAdapter(Protocol):
    id: str; version: str                        # semver; bump on any selector change
    def discover(self, window: DateWindow, cursor: Cursor|None) -> Iterator[ListingItem]: ...
        # yields {record_key, detail_url?, file_urls[], source_metadata_raw{as published}, listing_capture_id}
    def fetch_plan(self, item: ListingItem) -> list[FetchSpec]: ...   # HTTP or BROWSER, headers, expected media types
    def extract_metadata(self, listing: Capture, detail: Capture|None) -> dict: ...  # as-published strings only
    def is_soft_error(self, capture: Capture) -> SoftErrorVerdict: ...  # site-specific error templates
    def expectations(self) -> YieldModel: ...    # per-weekday Poisson/NegBin params, learned + floor
    fixtures: list[FixtureCase]                  # archived WARC records + golden JSON outputs
```

**Rules**
1. **No interpretation in P0.** Dates, names and case numbers stay exactly as published, for example `"30-09-2026"`. P1 triangulates them against the text.
2. **Stable `record_key`** comes from source identifiers (CNR + order number + date; SC diary number + date + file stem; gazette ID). It never comes from the URL alone, because URLs change on redesigns. If a source has no stable ID, the key is `sha256(canonical listing tuple)`, flagged `key_quality: WEAK`.
3. **Fixture tests** (Juriscraper pattern [P0-25]), strengthened:
   - Each adapter ships ≥ 5 archived listing and detail WARC records covering normal, empty-day, multi-file, Hindi-title and error-page cases, with golden outputs.
   - CI replays them from WARC, so tests never touch live sites.
4. **Schema contracts.** `extract_metadata` output is validated against a per-source JSON Schema. More than 2% null-rate drift on a required field is a *layout-drift* signal.
5. **Versioning.** `adapter@version` goes on every capture. Old versions stay runnable, so a WARC can be re-extracted with the adapter that originally read it.

### 5.6 Capture, fingerprinting and change detection

**Normalized fingerprint (`nfp`), by media type**
- **PDF with a text layer**: `pdftext-v1` = sha256 of the concatenated per-page extracted text, NFC-normalised, whitespace-collapsed, with known volatile lines stripped by regex. Volatile lines include "Downloaded on …", digital-signature validity stamps, and QR/verification-code lines listed per source.
- **PDF without a text layer** (scanned): `pdfimg-v1` = the page count plus the sequence of 64-bit perceptual hashes of each page rendered at 72 dpi. Two files match when every page is within Hamming distance ≤ 6 *(threshold to calibrate)*.
- **HTML**: `html-v1` = sha256 of the main-content text after boilerplate removal with a per-source content selector.
- **JSON**: `json-v1` = sha256 of the RFC 8785 canonical form [P0-39] after removing per-source volatile keys.
- **Other types**: `bytes-v1` = `raw_id`.

**Change decision (per `source_id, record_key`)**

```
on capture(c):                                   # c has raw_id, nfp, metadata m
  r = source_record.get(src, key) FOR UPDATE
  store raw blob if raw_id not in raw_blob        # CAS dedup by bytes
  if r is None:            kind = NEW
  elif r.state == DELETED: kind = REAPPEARED
  elif c.nfp != r.current_nfp:
       kind = CHANGED                              # new bytes AND new content (corrigendum, re-scan, replacement)
  elif meaningful_diff(m, r.source_metadata):      # e.g., party name corrected, neutral citation added
       kind = METADATA_CHANGED
  else:
       r.last_verified_at = now(); r.last_seen_at = now(); r.absent_streak = 0
       if c.raw_id != r.current_raw_id: log 'byte-only drift' (metric; no event)
       return                                      # UNCHANGED: no event unless verification sweep
  persist capture(kind, prior_raw_id = r?.current_raw_id); update r; write outbox event   # one transaction

on sweep_complete(src, window, ok=True):
  for r in records_in_window(src, window) not seen in sweep:
      r.absent_streak += 1
      if r.absent_streak >= 3 and direct_get(r.url) in {404, 410, soft404}:
          r.state = DELETED; emit DELETED
```

A `CHANGED` result on an SC or HC judgment is the main **corrigendum/replacement signal**. P1 decides between `en.r2` and a different Work re-using the URL. P0 adds `flags.suspected_replacement=true` when the text similarity (simhash Hamming distance ≤ 10) is high but not identical. That points to a corrigendum rather than a new document.

**Cross-source near-dup hints.**
- A 64-bit simhash of the text layer (word 3-shingles), following Manku et al. [P0-30], is stored in `raw_blob.simhash64`.
- Candidates within Hamming distance ≤ 3 from *other* sources are attached as `near_dup_hint`.
- Lookup uses the standard permuted-table method: 4 tables of 16-bit prefixes.
- This is how the same SC judgment from sci.gov.in, the AWS SC dataset and the IK API is linked. P1 makes the final Work/Manifestation decision.

### 5.7 Provenance, archival and versioning

**Dual write**
1. **WARC** records (request, response and a `metadata` record) are the evidentiary trail. Each carries:
   - `WARC-Target-URI`, `WARC-Date`, `WARC-IP-Address`;
   - `WARC-Payload-Digest: sha256:…`;
   - our `crawl_run_id`, adapter version, egress IP, TLS leaf and chain fingerprints, and legal profile ID in the metadata record.
2. The **payload** is extracted to content-addressed storage at `s3://plc-raw/sha256/ab/cd/<hex>` for processing.
3. Identical payloads within a run are written as WARC `revisit` records to avoid duplicate bytes.

**Daily WACZ + signature** *(signing per the Webrecorder draft spec [P0-28])*
- Each day's WARCs per source are packaged as WACZ, with `datapackage.json` hashes and a CDXJ index [P0-27].
- A daily **Merkle root** over all `capture_id‖raw_id‖fetched_at` tuples is signed with an HSM-held key, and optionally timestamped by an RFC 3161 TSA *(unverified vendor choice)*.
- This gives tamper-evident proof that "this text was published at this URL at this time". That matters for disputes about when a judgment was uploaded and for the spine's `as_known_at` audit replay. It is **not** a certified copy, and the product must say so.

**Storage policy**
- S3 in ap-south-1, with MinIO for an on-prem PLC replica.
- Object Lock in **governance** mode, so only a two-person-approved legal-takedown role can remove objects (§5.10).
- Versioning on.
- Lifecycle: WARCs move to infrequent-access after 90 days and to archive tier after 1 year. CAS raw blobs stay in the standard tier, because P1 reprocessing reads them.

**Version chain.** `source_record` → `capture` rows chained by `prior_raw_id` give a full per-record history. Nothing is overwritten.

**Consolidated statutes.**
- Every India Code Act page and PDF is snapshotted **weekly from day 1**, plus immediately after any e-Gazette amendment notification that names the Act.
- The resulting chain is our own *observed* point-in-time history. It complements the P1/P3 reconstruction from amending Acts, and it cannot be recreated retroactively.

### 5.8 Resilience: outages, WAFs, format drift

**Error taxonomy** (per fetch, used for circuit-breaking and health)

| Class | Detection | Response |
|---|---|---|
| DNS/TCP failure, timeout | Socket errors | Exponential backoff with jitter (base 30 s, cap 30 min); circuit opens after 5 consecutive failures per host; half-open probe every 10 min |
| TLS chain incomplete | `unable to get local issuer certificate` (observed: e-Gazette, ITAT, APTEL [P0-33]) | Fetch the intermediate via AIA; cache pinned intermediates per host; **never disable verification**; alert if the leaf fingerprint changes unexpectedly |
| TLS name mismatch | e.g. greentribunal.gov.in apex [P0-33] | Try the canonical `www.` host listed in the descriptor; never override |
| WAF/geo block | Akamai "Access Denied" signature; 403 on all paths | Stop, open a `BLOCKED` incident, switch to the secondary India egress; human escalation (webmaster contact, whitelisting request). No evasion. |
| New CAPTCHA/login wall | Template signatures (Securimage, hCaptcha, reCAPTCHA markup) newly appear on a previously open path | Adapter auto-pauses; legal profile flips to `PROVISIONAL`; route to the ladder (MoU/IK/human) |
| HTTP 429/503 | Status + `Retry-After` | Honour the header; halve the host rate for 24 h |
| Soft error | 200/404 bodies matching error templates (e.g. eCourts' "Welcome User Search Page not Found here" [P0-33]); PDF without `%PDF-` magic; HTML where a PDF was expected; below-minimum size | Not stored as content; counted; retried |
| Layout drift | Selector yields 0 on a working day; required-field null rate > 2%; `record_key` collision spike; yield outside the model's 99% interval | Adapter paused; last-good adapter replay on the new WARC; repair workflow |
| Silent partial coverage | Reconciliation shortfall vs IK/NJDG/official counts (§5.12) | Coverage incident; targeted backfill |

**Adapter repair workflow** *(the LLM step is [NOVEL — unvalidated])*
1. The health monitor detects drift and archives the failing listing WARC.
2. A repair job diffs the last-good and current DOM structures and asks an LLM, via the Model Gateway, to propose new selectors or a mapping.
3. The candidate adapter must:
   - pass all old fixtures (for unchanged page types);
   - pass new fixtures cut from the current WARC, reviewed by a human;
   - reproduce yield within the model interval on a 7-day re-scan.
4. A human approves, and the version is bumped.

Mean time to repair (MTTR) target: ≤ 1 working day for Tier A and ≤ 3 days for others. Missed items are recovered automatically by the rolling re-scan windows.

**Canaries.** For each source, 3–5 known historical URLs are fetched hourly (HOT) or daily. Their `nfp` must match the stored fingerprint. A change flags silent replacement or tampering at source, or a MITM.

### 5.9 Targeted acquisition and privacy-preserving matter demand

`TargetedAcquireWorkflow(request)`:
1. Resolve the target identifier to candidate sources:
   - CNR → the court's HC/district sources;
   - `NEUTRAL_INSC` → SC;
   - `CITATION_STRING` → ask P1's resolver for candidate Works and case numbers.
2. Walk the lawful ladder (§5.2) in order, within `allowed_access_modes`.
3. Record every attempt, ending FOUND, NOT_FOUND or BLOCKED_LEGAL.
4. On NOT_FOUND, re-queue at a back-off of 1 d, 3 d, 7 d, then close and report to P3/P8. A citation that cannot be sourced gets `resolution=UNSOURCED`.

**Tenant privacy** *[NOVEL — unvalidated]*. Which public cases a firm is watching is itself confidential, because it reveals strategy. So:
- a `MATTER_WATCH` request is emitted only by the **P9 Privacy Gate**, with `tenant_id=null`;
- the gate pools identical requests across tenants and releases them in hourly batches mixed into the general sweep;
- P0 stores no tenant attribution, and P7 keeps the tenant-side audit.

The court website sees only our generic crawler fetching a public record.

### 5.10 Suppression, takedown and personal data

- **Suppression register.**
  - Entries are created from court orders (anonymisation or removal directions), statutory identity bars (e.g. victims of sexual offences *(specific provisions to be confirmed by 21_india)*), and verified takedown requests.
  - Each entry targets `raw_id`s, `record_key`s or `work_id`s.
  - On creation, P0 emits `raw.captured.v1` with `change_kind=DELETED` and `suppression{reason, authority_ref, scope}`. Downstream phases must tombstone their derived text and index entries.
  - Raw bytes move to a restricted legal-hold prefix and remain retrievable only by the legal role.
- **Source-side masking.** If a court re-publishes a judgment with names masked, we see `CHANGED` and a suspected replacement. The newer masked version becomes canonical, and the unmasked prior version is automatically suppressed from display (`scope: DISPLAY`), because the court's re-publication expresses a masking intent.
- **DPDP posture.** Because the s.3(c)(ii) exemption is arguable [P0-23], P0:
  - minimises: no scraping of litigant contact data or case-status pages beyond need;
  - logs the purpose on every source;
  - supports erasure flows through suppression.

### 5.11 Backfill plan

1. **Weeks 0–2: seed.** Sync the AWS HC and SC buckets (≈1.3 TB) into `plc-raw`.
   - Each file becomes a capture with `access_mode=BULK_DATASET`, `provenance_tier=OPEN_DATASET`, `source_metadata` from the dataset JSON, and a synthetic listing reference to the dataset manifest.
   - Dedupe on `(cnr, decision_date, order_number)` [P0-2].
2. **Weeks 2–6: legislation.** India Code full crawl (central, then state); e-Gazette crawl back to the portal's earliest year; Internet Archive gazette mirror for older issues.
3. **Weeks 2–12: tribunals.** Backfill over night windows at ≤ 1 request per 2 s per host.
4. **Continuous: provenance upgrade.**
   - For documents held only as `OPEN_DATASET` or `LICENSED_THIRD_PARTY`, fetch the official copy wherever an open official route exists. Priority order: SC first, then documents cited ≥ 5 times, then the rest.
   - Record the agreement rate (matching `nfp`) as a data-quality metric of the seed dataset.
5. **Verification sweep.** A 1% stratified sample per court and year is checked against official availability. Results go to the coverage dashboard.

### 5.12 Health, reconciliation and coverage measurement

**Yield model.** Per source and weekday, a negative-binomial model of expected new items, fitted on 8 weeks of history and conditioned on the calendar. An alert fires when the observed count falls below the 1st percentile on a working day, or when there are 0 items with P(0) < 0.01.

**Reconciliation ledger** *[NOVEL — unvalidated]*. Daily, for each court, we compare:
- (a) our captures;
- (b) Indian Kanoon's count for the same court and date, via metainfo or search at ₹0.02–0.50 per call [P0-16];
- (c) NJDG disposal counts [P0-12];
- (d) the AWS dataset once its update lands.

Each ratio has a learned "normal" band, since the sources measure different things (disposals vs uploaded judgments). A sustained deviation is a coverage incident. Items present in (b) but absent in (a) are enqueued as `COVERAGE_GAP` targeted requests.

**`source.health.v1`** is emitted on every status transition and hourly for HOT sources. P10 renders "current as of" per court. P8 uses it to downgrade "no adverse authority found" statements when a relevant source is `DEGRADED` or `DOWN`.

### 5.13 Cross-cutting: security, cost at scale (≈5M+ docs), latency targets, observability, model-agnostic design

**Security**
- Fetchers run in an isolated VPC. Egress is allowlisted to registry domains only. No path leads from the fetch tier to tenant stores.
- Browser workers run in gVisor sandboxes with no credentials, and are destroyed after each job.
- All payloads are treated as hostile: AV scan, PDF structure checks, size and decompression caps. P0 never renders or executes content in a privileged context.
- **Prompt-injection text** in a document is inert in P0. It is flagged by a cheap regex/classifier (`flags.injection_suspect`) so that P1, P5 and P6 can apply their defences.
- The legal-takedown role requires two-person approval.
- Signing keys live in an HSM.
- Every operator action in the capture console is recorded in WARC and the audit log.

**Cost at scale** *(estimates; cloud prices unverified, to be confirmed with an India-region quote)*
- **Storage**: about 3 TB backfill + 0.5 TB/yr growth, plus WARC overhead ⇒ single-digit TB. That is on the order of US$100–300/month on object storage.
- **Compute**:
  - 6–10 small fetcher and normaliser containers;
  - 2–4 browser workers;
  - a 3-node Temporal cluster and managed Postgres.
  - Order of US$2–5k/month.
- **Licensed API**: IK gap-fill and reconciliation at about 5–20k calls/day comes to about ₹2–8k/day [P0-16], roughly US$9–35k/yr.
- **People (dominant)**:
  - about 100 adapters (SC 3, HCs ~40, tribunals ~15, gazettes ~30, regulators ~10, legislation ~5);
  - at an *assumed* 5–10% breakage per month ⇒ 5–10 repairs/month ⇒ **1.5–2 FTE** of crawler engineering;
  - plus about 0.25 FTE legal review (legal-profile renewals every 180 days).
- **At 10M+ documents** P0 cost grows only with storage. Adapter count, not document count, drives cost.

**Latency targets**
- Detection → event published: p95 ≤ 60 s.
- HOT freshness: p95 ≤ 30 min.
- Targeted acquisition (`P1` priority): first attempt ≤ 5 min.
- Read API `GET /raw`: p95 ≤ 150 ms to the signed URL.

**Observability**
- OpenTelemetry traces from sweep to fetch to capture to outbox. The `traceparent` flows into the event, so P1 through P10 inherit the trace.
- Metrics:
  - `freshness_lag_seconds{source}` (histogram);
  - `source_lag_seconds{source}` (decision date → first seen);
  - `yield_ratio{source}`;
  - `fetch_errors_total{class}`;
  - `false_change_rate` (CHANGED later judged identical by P1);
  - `soft_error_total`;
  - `legal_gate_denials_total`;
  - `automated_captcha_solves_total`, which must be 0 and is enforced by a CI test that forbids solver dependencies.
- A public-facing status page per source is fed to P10.

**Model-agnostic design.** P0 has no LLM on the hot path. The adapter-repair assistant calls the Model Gateway through a task contract (`propose_selectors`) with fixture-based evaluation, so it survives a change of LLM provider.

---

## 6. Alternatives considered and why they were rejected

Scores are relative (++ best, −− worst).

### 6.1 Acquisition route for High Court judgments

| Option | Accuracy / coverage | Cost | Latency | Maintainability | Defensibility |
|---|---|---|---|---|---|
| A. Automate eCourts portals with CAPTCHA solvers (what hobby SDKs do [P0-4]) | ++ (single uniform source) | + | ++ | − (breaks on each CAPTCHA upgrade) | −− (s.43 posture [P0-21]; ToU; reputational risk with the judiciary we want an MoU from) |
| **B. CC-BY bulk seed + official HC-site delta + IK gap-fill + MoU track + human-assisted targets (chosen)** | + (reconciliation measures gaps) | + | + (HC sites ≤ 4 h) | − (many adapters) | ++ |
| C. License a full corpus from a commercial aggregator | ++ | −− | + | ++ | + (contractual), but a single-vendor dependency, and editorial layers remain off-limits (EBC) |
| D. IK API as the primary corpus | + | − (per-call at 20M docs ≈ ₹40 lakh just to fetch once; plus attribution) | + | ++ | + (contract), but a 1-month termination clause [P0-15] makes it a moat-killer |

**Choice: B.** It is the only option that is both defensible and not a single point of failure. Option A's gain in latency does not survive a legal challenge or the next CAPTCHA upgrade. The MoU track may later convert B into an official feed.

### 6.2 Orchestration

| Option | Fit to P0 | Failure recovery | Ops cost | Notes |
|---|---|---|---|---|
| **Temporal (chosen)** | Long-running sweeps and backfills with per-page cursors; human-in-the-loop waits (capture console); timers for re-queues | Replay from event history; completed activities not re-run [P0-31] | Medium (cluster) | Continue-as-new for long backfills [P0-41] |
| Airflow | Good for fixed daily DAGs | Task-level retry from scratch [P0-32] | Medium | Poor for 10-minute HOT polling and event-driven targeted requests |
| Dagster | Strong asset lineage [P0-32] | Run-level | Medium | Lineage is already covered by our capture tables; less natural for signals and human waits |
| Cron + queue (Celery/RQ) | Simple | Ad hoc | Low | Re-invents durable timers, cursors and idempotency; a risk at 100 sources |

### 6.3 Crawler framework

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Scrapy | Mature; selectors; middleware | Own scheduler and frontier conflict with Temporal; WARC needs plugins; long-lived process model | Rejected as the engine; its selector idioms are borrowed for declarative adapters |
| Crawlee (Playwright/Cheerio) | Good browser automation, queues | Its own persistent queue duplicates Temporal state; Node-first | Rejected as the engine |
| Browsertrix-crawler | Highest-fidelity WARC/WACZ, signing support [P0-27] | Heavy per page; designed for archiving whole sites, not metadata extraction | **Used** for SPA and high-fidelity snapshots (e-Jagriti, ToU pages) |
| **Thin httpx + warcio + Playwright activities (chosen)** | Every fetch is a Temporal activity with idempotency; explicit WARC; minimal magic | We own more code | **Chosen**; ~90% of sources are static listing + PDF |

### 6.4 Change detection basis

| Option | False-change rate | Missed-change rate | Cost |
|---|---|---|---|
| Byte hash only | High on dynamic PDFs/HTML | ~0 | Lowest |
| HTTP validators only (ETag/Last-Modified) | Low when present | High: many government servers omit validators or send them wrongly *(unverified; to measure)* | Lowest |
| **Normalized fingerprint + byte hash retained + validators as a fast path (chosen)** | Low | Low (per-source volatile-line rules) | Low (text extraction is cheap) |
| Full semantic diff with an LLM | Lowest | Low | High, non-deterministic; rejected for the hot path |

### 6.5 Egress strategy

| Option | Access success | Defensibility | Cost |
|---|---|---|---|
| **India-region cloud static IPs (primary) + Indian colo/ISP static IPs (secondary), declared user agent (chosen)** | Needed: non-Indian egress got Akamai 403s [P0-33]; whether Indian cloud ASNs are blocked is to be tested | ++ (transparent, contactable) | Low |
| Rotating residential proxies | Higher short-term | −− (evasion) | Medium |
| Operating only from Indian partner premises | + | + | High ops |

### 6.6 Event bus (co-decision with P4)

The candidates were a Kafka-API log (Redpanda or MSK), NATS JetStream and a pure Postgres queue. P0's requirements are:
- ordered partitions by record;
- replay ≥ 30 days;
- self-hostable for the on-prem PLC replica;
- a mature CDC/outbox ecosystem.

The Kafka API satisfies all four, and at 10–50k events/day any choice performs. **Recommendation: Kafka API with a Postgres outbox.** Final decision with P4.

---

## 7. Novel ideas (clearly labeled as unvalidated)

1. **[NOVEL — unvalidated] Citation-gap-driven acquisition.**
   - Every `CitationMention` that P1 cannot resolve, and every P3 edge whose target Work has no manifestation, becomes an `acquire.requested.v1`.
   - The corpus thereby grows toward what Indian courts actually cite, not what portals happen to expose. Unsourceable citations are measured explicitly (`UNSOURCED`).
   - To validate: the share of the partner firm's cited authorities that resolve before vs after 90 days.
2. **[NOVEL — unvalidated] Legal-gate-as-code.**
   - An adapter cannot execute without an approved, unexpired `LegalProfile`, and a mode not listed there cannot run.
   - ToU and robots pages are archived as WARC, and every event carries `terms_ref`.
   - This turns "we scrape responsibly" into auditable evidence for customers' general counsel and for any MoU negotiation.
3. **[NOVEL — unvalidated] Calendar-aware yield SLOs plus a multi-source reconciliation ledger.**
   - These detect *silent* coverage loss, which is the dominant failure of court scrapers (§4).
   - The measurable claim to validate: coverage incidents detected within ≤ 1 working day.
4. **[NOVEL — unvalidated] Publication-evidence chain.**
   - Signed daily Merkle roots over captures, with TLS fingerprints and listing captures, give tamper-evident proof of *what was published, where and when*.
   - It supports `as_known_at` audit replay, and customer disputes of the form "the judgment wasn't online when we filed".
5. **[NOVEL — unvalidated] Source-lag analytics as intelligence.**
   - Measured per-court upload lag (decision date → first seen) is itself a product signal for P10, e.g. "Bombay HC orders typically appear 3 days after pronouncement".
   - P8 uses it to phrase recency caveats.
6. **[NOVEL — unvalidated] Fixture-gated LLM adapter repair** (§5.8). The repair assistant proposes changes, and deterministic fixtures plus yield replay decide. The LLM output is never trusted on its own.
7. **[NOVEL — unvalidated] Tenant-blind matter demand** (§5.9). Pooled, batched, attribution-free acquisition requests via the Privacy Gate, so that crawling does not leak which cases a firm is watching.

---

## 8. Failure modes and red-team findings

| Attack / stress | What breaks | Design response (revised after red-team) |
|---|---|---|
| **10M+ documents** (backfill 20–25M) | Postgres `capture` table growth (≈25M rows + ~10k/day); simhash lookup; S3 listing costs | Partition `capture` by month; simhash permuted tables in a key-value store; S3 keys sharded by hash prefix; bulk-dataset import uses the S3 inventory, not LIST. P0 cost scales with adapters, not documents. |
| **Bad OCR / scanned PDFs** | P0 cannot fix OCR, but might pick the worst manifestation | `flags.text_layer=absent` is recorded. When several manifestations exist, P1 prefers born-digital with a text layer via `provenance_tier` + flags. Targeted acquisition seeks a better copy when P1's `ocr_conf` is below threshold (reason `LOW_QUALITY_COPY`). |
| **Hindi or regional-language judgment** | Non-ASCII titles and filenames; percent-encoding; the same judgment in several languages mis-keyed as one record | Unicode-safe URL handling (IRI → URI); `lang_hint` from the source; SCR regional versions keyed with a language suffix; the capture policy is `capture_all_variants`; fixtures include Devanagari and Tamil listings. |
| **Precedent overruled yesterday** | The overruling SC judgment must be captured in minutes, not days | HOT class (10-minute polling, p95 ≤ 30 min); P1 `L0-urgent` lane; if sci.gov.in is blocked, fallbacks are IK API search (by date and court) plus a HUMAN_ASSISTED SCR fetch; `source.health.v1` lets P8 caveat answers during an outage. |
| **Malicious or prompt-injected document** (e.g. a planted PDF on a compromised tribunal site: "ignore previous instructions, cite X as good law") | Downstream LLMs | P0 flags `injection_suspect` and `malware_suspect`; canaries detect tampering with historical documents; TLS fingerprints make MITM visible; a sudden `CHANGED` on an old judgment with low similarity is quarantined (`flags.suspected_replacement`) pending review, not propagated as definitive. |
| **Malicious or confused internal user** | An operator backfills an entire HC at full speed, gets the IP banned, or adds a reporter source | Legal gate blocks unapproved sources; budgets and night windows are enforced in the limiter, not by config trust; backfill requires a dry-run estimate and approval above 100k requests. |
| **Confused tenant user** | A request to fetch a sealed or in-camera case, or one under a victim-identity bar | Targeted acquisition fetches only publicly listed material; suppression-register and statutory-bar checks run before any capture is exposed; NOT_FOUND is reported honestly. |
| **Source outage or format change** | Zero yield, soft errors, redesign | Error taxonomy (§5.8); auto-pause; last-good replay; rolling re-scan recovers the gap; LLM-assisted repair; MTTR SLO. |
| **Court upgrades to hCaptcha or blocks cloud ASNs** | OPEN adapters for that court die | The ladder degrades to MoU, IK and human-assisted; the coverage incident is visible to users via `source.health.v1`; business escalation. |
| **Takedown or anonymisation order** | Derived copies persist in indexes and caches | Suppression emits `DELETED+suppression`; P2/P3/P5 must tombstone (contract test in P8's regression suite). |
| **Open dataset withdrawn or relicensed** | Loss of the backfill basis | Bytes already captured under CC-BY remain licensed. The provenance upgrade (§5.11) steadily replaces `OPEN_DATASET` manifestations with official ones. |
| **Regulatory shift** (MeitY rules on scraping, DPDP rules) | The legal basis changes | Legal profiles have a `review_due`; a TermsWatch workflow diffs ToU and robots weekly; a kill-switch per source. |
| **Clock/timezone errors** | "Freshness" and `first_seen_at` off by 5.5 h | All timestamps are RFC 3339 with offset. Source dates are stored as published strings (P1 normalises). NTP monitoring. |

---

## 9. Evaluation metrics for this phase

| Metric | Definition | Target (Tier A) |
|---|---|---|
| Freshness p95 | `first_seen_at` → event published | HOT ≤ 30 min; WARM ≤ 4 h; COOL ≤ 24 h |
| Coverage recall | Captured ÷ items on the official listing (audited sample; 200 items/source/month) | ≥ 99.5% HOT; ≥ 99% WARM |
| Reconciliation gap rate | Items in IK/NJDG-derived expectations missing from our captures after 7 days | ≤ 0.5% |
| MTTD silent failure | Layout break → alert | ≤ 1 working day (goal: ≤ 2 h for HOT) |
| MTTR adapter | Alert → fixed adapter deployed | ≤ 1 working day (Tier A) |
| False-change rate | `CHANGED` events later judged content-identical by P1 | ≤ 0.5% |
| Provenance completeness | Captures with WARC ref + `terms_ref` + TLS fingerprint + listing reference | 100% (OPEN/HUMAN); 100% `terms_ref` for all |
| Legal compliance | Automated CAPTCHA solves; robots violations; runs with expired profiles | 0 / 0 / 0 |
| Official-provenance share | Share of Works with ≥ 1 `OFFICIAL_*` manifestation | SC 100%; HC ≥ 60% by month 6 (rising via provenance upgrade) |
| Targeted acquisition success | FOUND ÷ requests (by reason) | Baseline in month 1; track trend |
| Cost per 1k captures | All-in infra cost | Track; alert on 2× regression |

---

## 10. MVP version vs. full version

**MVP (≈ 8–10 weeks, 2 engineers + part-time counsel)**
- **Sources**:
  - SC judgments and daily orders (HOT);
  - AWS SC + HC backfill;
  - own-site delta for 6–8 HCs by volume and partner relevance (e.g. Delhi, Bombay, Madras, Karnataka, Allahabad, Calcutta; *final list with partner firm*);
  - India Code central Acts (weekly snapshots) and the central e-Gazette;
  - NCLT (allowed paths), NCLAT, ITAT;
  - IK API for gap-fill.
- **Platform**: Temporal, Postgres, S3 (ap-south-1), httpx + warcio, declarative adapters with fixture CI, `nfp` change detection, outbox → bus, legal gate, a basic yield alert, `raw.captured.v1` with the proposed extensions.
- **Not in MVP**: browser-mode sources, WACZ signing, the reconciliation ledger (a manual weekly check instead), LLM repair, the capture console (targeted fetches done manually by an engineer, logged), state gazettes.

**Full version (months 3–12)**
- All 25 HCs.
- All listed tribunals and regulators.
- State gazettes.
- e-Jagriti via browser mode.
- Capture console with human-assisted mode.
- Signed WACZ and daily Merkle roots.
- The reconciliation ledger.
- Adaptive revisit.
- Fixture-gated LLM repair.
- `acquire.requested.v1` from P1/P3/P9.
- `source.health.v1` to P8/P10.
- An on-prem PLC replica feed (MinIO + bus mirror).
- MoU feeds onboarded as they materialise.

---

## 11. Open questions and risks

1. **Counsel opinion required.** Three questions:
   - Is HUMAN_ASSISTED CAPTCHA capture at low volume consistent with the eCourts, SCR and NCLT ToU and with IT Act s.43?
   - Does using the CC-BY AWS datasets carry derivative risk, given they were built from CAPTCHA-gated portals and a mobile API [P0-2]?
   - Are **SCR official headnotes** reproducible under s.52(1)(q)(iv), or are they separate government works needing permission?
2. **s.52(1)(q)(ii) on bare Acts.** Reproducing Acts is exempt only "together with any commentary thereon or any other original matter" [P0-17]. P10 must not expose a bare-Act-only download without our annotations. This needs legal confirmation.
3. **MoU feasibility** with the e-Committee/NIC for a bulk judgments feed. The NJDG Open API is currently government-only [P0-12]. Timeline unknown, so the plan must not depend on it.
4. **Indian cloud egress acceptance.** It is unverified whether Akamai-fronted sites (sci.gov.in, India Code) accept Indian cloud ASNs. Test in week 1; the colo fallback is budgeted.
5. **India Code point-in-time history**: none documented [P0-36]. Our observed snapshots start at day 1; earlier history must be reconstructed by P1/P3 from gazette amending Acts.
6. **Volume estimates** for tribunals and gazettes are unverified. Measure in the first 30 days and re-size.
7. **IK dependency.** The ToU allow termination at 1 month's notice [P0-15]. Keep usage to gap-fill and reconciliation, and cap the share of `LICENSED_THIRD_PARTY`-only Works (target < 5% by month 12).
8. **DPDP s.3(c)(ii)** applicability to court-published judgments is arguable [P0-23]. Rules and notifications under DPDP may change the posture.
9. **Dynamic-PDF behaviour** of Indian portals (the volatile stamps assumed in §5.6) is unmeasured. Calibrate the `nfp` rules per source during onboarding.
10. **Adapter maintenance burden** (1.5–2 FTE) is an estimate by analogy to Juriscraper's open-issue load [P0-25]. It is the biggest recurring P0 cost and the biggest risk to the freshness SLO.

---

## References

[P0-1] AWS Open Data Registry / Dattam Labs. "Indian High Court Judgments." registry.opendata.aws, 2025–26. https://registry.opendata.aws/indian-high-court-judgments/ — verified
[P0-2] Dattam Labs (vanga). "indian-high-court-judgments: opendata/docs/dataset.md." GitHub, 2025–26. https://github.com/vanga/indian-high-court-judgments/blob/main/opendata/docs/dataset.md — verified
[P0-3] Dattam Labs (vanga). "indian-supreme-court-judgments." GitHub, 2025–26. https://github.com/vanga/indian-supreme-court-judgments — verified
[P0-4] iamshouvikmitra. "bharat-courts 0.3.1 (async client for eCourts/HC/SCI; CAPTCHA solvers; archive client)." PyPI / Product Hunt, 2026. https://pypi.org/project/bharat-courts/0.3.1/ — snippet
[P0-5] eCommittee SC / NIC. "Judgment Search Portal." https://judgments.ecourts.gov.in/pdfsearch/ — verified (probe 2026-09-30: Securimage CAPTCHA)
[P0-6] Bar & Bench. "Supreme Court e-Committee makes audio captchas available on all High Court websites…" https://barandbench.com/amp/story/news/litigation/supreme-court-e-committee-makes-audio-captchas-available-on-all-high-court-websites-to-facilitate-access-for-visually-impaired — snippet
[P0-7] High Court of Manipur. "Notice: eSCR and DigiSCR merged into SCR portal." https://hcmimphal.nic.in/Documents/eSCR%20and%20DigiSCR_0001.pdf — snippet
[P0-8] Verdictum. "CJI Announces Launch Of e-SCR Project To Provide Free Access To 34,000 Judgments." 2023. https://www.verdictum.in/court-updates/supreme-court/e-scr-free-access-to-34000-judgments-1455548 — snippet
[P0-9] LiveLaw. "CJI DY Chandrachud Urges Lawyers To Use SCR." https://www.livelaw.in/top-stories/cji-dy-chandrachud-urges-lawyers-to-use-scr-270054 — snippet
[P0-10] Bar & Bench. "Supreme Court launches neutral citation for judgments." 2023. https://www.barandbench.com/news/supreme-court-launches-neutral-citation-judgments — snippet
[P0-11] Mondaq. "Delhi High Court First To Introduce Neutral Citation System For Its Judgements." 2022. https://www.mondaq.co.uk/india/performance/1241608/delhi-high-court-first-to-introduce-neutral-citation-system-for-its-judgements — snippet
[P0-12] Drishti IAS. "National Judicial Data Grid" (NJDG Open API for Central & State Govt departments). 2023. https://www.drishtiias.com/daily-updates/daily-news-analysis/national-judicial-data-grid/print_manually — snippet
[P0-13] Rajya Sabha. Answer to question, 25 July 2024 (eCourts: 26.044 crore cases; 26.047 crore orders/judgments). https://rsdebate.nic.in/bitstream/123456789/749688/1/PQ_265_25072024_U425_p410_p415.pdf — snippet
[P0-14] GKToday. "Indian Courts Achieve Milestone in Case Disposals" (NJDG 2024: HCs > 1.2M disposals; SC 36,969). 2025. https://www.gktoday.in/indian-courts-achieve-milestone-in-case-disposals/ — snippet
[P0-15] Indian Kanoon. "API Service Description / Terms." https://api.indiankanoon.org/terms/ — verified
[P0-16] Indian Kanoon. "API pricing." https://indiankanoon.org/members/pricing — snippet
[P0-17] Copyright Act 1957, s.52(1)(q) (text via DPIIT Copyright Office exceptions page / Indian Kanoon). https://www.copyright.gov.in/Exceptions.aspx — snippet (page returned 503 on fetch)
[P0-18] Supreme Court of India. Eastern Book Company & Ors v. D.B. Modak & Anr, (2008) 1 SCC 1; AIR 2008 SC 809 (12 Dec 2007). https://indiankanoon.org/doc/1062099/ — verified (partial)
[P0-19] LawFoyer. "Eastern Book Company v. D.B. Modak — case summary." https://lawfoyer.in/eastern-book-company-ors-v-d-b-modak-anr-air-2008-sc-809-2008-1-scc-1-2008-air-scw-49/ — snippet
[P0-20] SpicyIP. "EBC granted injunction against Lexis Nexis and Thomson Reuters…" 2014. https://spicyip.com/2014/02/ebc-granted-injunction-against-lexis-nexis-and-thomson-reuters-for-infringement-of-their-copyright.html — snippet
[P0-21] MediaNama. "223 experts concerned about MeitY's stance on web scraping to train AI models." Feb 2025. https://www.medianama.com/2025/02/223-experts-concerned-about-meitys-stance-on-web-scraping-to-train-ai-models/ — verified
[P0-22] Law.asia. "Legality of data scraping under Indian law." https://law.asia/india-data-scraping-regulation/ — snippet
[P0-23] Digital Personal Data Protection Act 2023, s.3(c)(ii) (mirror text; PRS copy of Act). https://www.dpdpa.com/dpdpa2023/chapter-1/section3.html ; https://prsindia.org/files/bills_acts/acts_parliament/2023/Digital_Personal_Data_Protection_Act,_2023.pdf — verified (clause text via mirror)
[P0-24] Government of India. "Government Open Data License – India (GODL)." (copy hosted by India Post) https://app.indiapost.gov.in/documents/media/OGD.pdf — snippet
[P0-25] Free Law Project. "juriscraper." GitHub. https://github.com/freelawproject/juriscraper — verified
[P0-26] Free Law Project. "Juriscraper" project page / announcements. https://free.law/projects/juriscraper — snippet
[P0-27] Webrecorder (I. Kreymer). "An update on the WACZ format." 2023. https://webrecorder.net/blog/2023-05-03-an-update-on-wacz — verified
[P0-28] Webrecorder. "WACZ Signing and Verification 0.1.0 (draft)." https://specs.webrecorder.net/wacz-auth/0.1.0/ — snippet
[P0-29] Library of Congress. "Sustainability of Digital Formats: WACZ." https://loc.gov/preservation/digital/formats/fdd/fdd000586.shtml — snippet
[P0-30] Manku, G.S., Jain, A., Das Sarma, A. "Detecting Near-Duplicates for Web Crawling." WWW 2007, pp. 141–150. https://research.google/pubs/detecting-near-duplicates-for-web-crawling/ — verified
[P0-31] Temporal Technologies. "Workflows" (durable execution, replay). https://docs.temporal.io/workflows — verified
[P0-32] AutomationAtlas. "Temporal vs Apache Airflow 2026: Durable Workflows vs DAG Orchestration." 2026. https://automationatlas.io/guides/temporal-vs-apache-airflow-2026-comparison/ — snippet
[P0-33] P0 author. HTTP probes of Indian legal portals from non-Indian cloud egress (robots.txt, CAPTCHA markers, TLS/WAF errors), 2026-09-30. Raw notes: SCRATCH/notes/ — verified (first-hand observation; single point in time)
[P0-34] Government of Odisha. "About e-Gazette" (weekly vs extraordinary gazettes). https://egazette.odisha.gov.in/about_gazette — snippet
[P0-35] e-Gazette of India PDF paths (e.g. https://egazette.gov.in/WriteReadData/1969/O-1469-1969-0001-66051.pdf) and Internet Archive mirror (https://archive.org/download/in.gazette.1972.112/) — snippet
[P0-36] IALS (University of London). "India Code" resource description. https://resources.ials.sas.ac.uk/node/708433 — snippet
[P0-37] Digital India Awards 2022 Compendium, p.21 (Judgment Search Portal description). https://digitalindiaawards.india.gov.in/assets/compendium2022/files/basic-html/page21.html — snippet
[P0-38] IETF. RFC 9110 "HTTP Semantics" (conditional requests, ETag, Last-Modified). 2022. https://www.rfc-editor.org/rfc/rfc9110 — unverified (not fetched this session)
[P0-39] IETF. RFC 8785 "JSON Canonicalization Scheme (JCS)." 2020. https://www.rfc-editor.org/rfc/rfc8785 — unverified
[P0-40] ISO 28500:2017 "Information and documentation — WARC file format." https://www.iso.org/standard/68004.html — unverified
[P0-41] Temporal Technologies. Event History limits and Continue-As-New (docs). https://docs.temporal.io/workflow-execution/continue-as-new — unverified (limit values not confirmed)
[P0-42] Harvard Library Innovation Lab. "Perma Tools / Scoop." https://tools.perma.cc — snippet
[P1-34] Cross-reference: 03_P1_ingestion_parsing.md reference for Nyaykosh (NeGD) Akoma Ntoso APIs — not independently verified by P0
