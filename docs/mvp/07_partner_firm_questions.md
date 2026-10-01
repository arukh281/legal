# 07 — Questions for the Partner Firm (priority order)

**How to use this file.** Send §1–§3 before the week-1 kick-off and settle them in it. Each question says why it matters, what is blocked until it is answered, and the **safe default** we use meanwhile. Answers are logged in the decision log and linked from the affected docs (01–06).

---

## 1. Data access: legal opinion first (blocks the corpus)

We want one short written opinion, from the firm's own counsel or counsel it nominates, covering the questions below. **Safe default until answered:**
- only official, robots-permitted, CAPTCHA-free listings and the CC-BY open datasets are ingested;
- profiles stay `PROVISIONAL`;
- no CAPTCHA is ever solved by a machine;
- permission and notice emails go to SEBI, CCI, Delhi HC, NCLT, NCLAT and IBBI in week 1 ([01](01_corporate_corpus_and_sources.md) §6.2).

| # | Question | Why it matters | Blocks |
|---|---|---|---|
| **Q1.1** | SEBI, CCI and Delhi HC copyright pages ask for permission "by mail" before reproduction. Does Copyright Act s.52(1)(q)(iv) (judgments and orders of a court, tribunal or other judicial authority) allow us to show full text of their orders anyway? Are SEBI WTM/AO orders "other judicial authority"? Are non-gazetted SEBI circulars reproducible? | Full-text display in research, memos and cite-check | SEBI, CCI and Delhi HC text display |
| **Q1.2** | NCLT and NCLAT policies require "prior permission" for hyperlinks. Is deep-linking to their PDFs inside a closed, firm-only tool covered, or should we request permission? (We recommend requesting it.) | Source links in the UI | NCLT/NCLAT links |
| **Q1.3** | IBBI-hosted NCLT/NCLAT orders are "not certified copies", and some are re-rendered. May we display them as the order text with an "uncertified copy" badge? May paragraph anchors rest on them where no official copy is reachable? | **The IBBI mirror is our only bulk route to NCLT orders** | IBC corpus; capabilities 1–3, 7 |
| **Q1.4** | Is scripted use of a site's own unauthenticated search (no CAPTCHA, robots-allowed, session token only) acceptable? This covers the NCLAT display board, the CCI listing and the NCLT case-history call. | Core NCLAT adapter | NCLAT and CCI corpus |
| **Q1.5** | Is it acceptable to use the CC-BY open SC/HC datasets, given they were built from CAPTCHA-gated portals and a mobile API? | Bulk SC and HC history | SC and HC backfill |
| **Q1.6** | Is "human-assisted" capture, where a lawyer or our staff solves a CAPTCHA by hand to fetch one watched matter's order or cause list, consistent with site terms and IT Act s.43? What daily cap is acceptable? | Hearing tracking and gap-fill | Capability 10 beyond manual entry |
| **Q1.7** | Is annotated display of Acts (with our version history) "original matter" under s.52(1)(q)(ii)? Must we disable bulk bare-Act export? | Statute views | Statute export |
| **Q1.8** | Reporter citations (SCC/AIR) are stored only as identifiers, never reporter text or headnotes (*EBC v. D.B. Modak*). Please confirm this policy, and that showing SCR official headnotes is out. | Citation resolution | — |
| **Q1.9** | Must deadlines be computed from the order date on an uncertified mirror copy, or must the tool always ask for the certified-copy date, since Limitation Act s.12 excludes copy time? | Deadline UX | Capability 4 |
| **Q1.10** | Does the Delhi HC privacy ruling (*Laksh Vir Singh Yadav*, 29 May 2026) bind us as an "other host", so that we must suppress name search for protected parties? | Privacy | Search over party names |
| **Q1.11** | Bills (Corporate Laws (Amendment) Bill 2026): are excerpts with links enough for the watchlist? | Watchlist | — |
| **Q1.12** | Indian Kanoon API, if used for gap-fill: retention after termination; use of its metadata for alias tables | Gap-fill | Optional |

## 2. Trigger-type ranking (blocks full-mode work in weeks 8–18)

**Q2.1** Rank the candidate triggers by how often the firm handles them and how much a missed step costs. The candidates are in [02](02_workflows_and_rules.md) §1. Default hypothesis: (1) IBC pack (s.8 notice, s.9/s.7 petitions, s.61 appeal); (2) arbitration (s.34, s.37, s.9); (3) Companies Act s.241–242 + appeals; (4) SEBI SCN + SAT.

Please answer:
- **Volume:** roughly how many of each did the firm handle in the last 12 months?
- **Side:** which side does the firm usually act for (creditor or debtor, petitioner or respondent, noticee)?
- **Corpus caveat on s.241–242:** NCLT Companies Act orders have no open bulk route (01 R-1). Would the firm supply the NCLT orders it holds for its own matters, or accept a thinner corpus (NCLAT, SC and HC only) for this trigger?

**Q2.2** For the top 3, name one lawyer who will sign off the rule cards (02 §0 "activation record"). **Safe default:** the default ranking, with no RuleSpec activated until it is signed off.

## 3. Data residency and processing of client documents (blocks real matters, week 14)

| # | Question | Default until answered |
|---|---|---|
| **Q3.1** | May client matter documents be processed by LLM providers whose processing happens outside India, under zero-data-retention terms where offered? Providers: Anthropic, OpenAI, Google. Or must processing stay in India (`residency_policy = IN_ONLY`)? | Only closed, consented gold matters are processed, on endpoints the firm approves in writing. No live matter is uploaded before the answer. |
| **Q3.2** | Is hosting in AWS Mumbai (ap-south-1), with backups copied to Hyderabad (ap-south-2), acceptable? | Yes (planned) |
| **Q3.3** | Do any client engagement letters or sector rules (e.g. listed-company UPSI under SEBI PIT, or banking secrecy) restrict where documents go or who may see them? | Treat SEBI/UPSI matters as restricted: matter-level `restricted` flag, named members only |
| **Q3.4** | Under the DPDP Act the firm is the data fiduciary and we are its processor. Will the firm sign a data-processing agreement plus a confidentiality undertaking? Who in the firm is the contact for security and IT review? | Draft DPA sent in week 1 |

Note the residency fact from the blueprint: as of September 2026, no Claude endpoint processes inside India. In-India options are OpenAI models on Bedrock "in." profiles, Azure South India, or self-hosted open-weight models (13; D15). An IN_ONLY answer therefore changes the model mix, though the cost stays roughly the same (04 §4.5).

## 4. Test matters for the gold set (blocks evaluation, weeks 2–9)

| # | Question |
|---|---|
| **Q4.1** | Will the firm authorise 20–30 **closed** matters for internal evaluation (notice or petition + filed response + key orders)? Who signs the authorisation? |
| **Q4.2** | Do the engagement letters require client consent for this internal use? If so, which clients and matters can be cleared quickly? |
| **Q4.3** | Who collects the packages? We suggest one associate for 2–3 hours a week in weeks 2–8. |
| **Q4.4** | Which lawyers can give a 30-minute answer-key interview per matter (06 §4)? |
| **Q4.5** | May we keep gold artefacts for 12 months after the pilot? Confirm that the firm and its matters will never be named externally without separate written consent. |

## 5. Lawyer time and roles (blocks scheduling)

| # | Question |
|---|---|
| **Q5.1** | Confirm ≈ 5 hours a week from named partner lawyers for 20 weeks (budget in [05](05_build_plan.md) §7): sign-off sessions, interviews, demos, weekly pilot feedback. |
| **Q5.2** | Who are the 2–3 pilot users from week 14, and the 10–25 users after go-live? |
| **Q5.3** | Would the firm co-fund or host a part-time law-graduate reviewer for tier-1 treatment review and annotation (05 §6)? |
| **Q5.4** | Who has authority to dispute a machine-detected negative treatment and record the final word (citator review)? |

## 6. Forums and practice details (blocks calendars and rules)

| # | Question |
|---|---|
| **Q6.1** | Which High Court is the firm's primary HC (beyond Delhi and Bombay)? Which NCLT benches does it appear before most? Are SAT and CCI matters relevant? |
| **Q6.2** | NCLT reply and rejoinder practice per bench. NCLT Rules r.37 says only "before the date of hearing", so dates come from bench orders. What lead times does the firm work to? |
| **Q6.3** | Court holiday calendars the firm relies on (SC, NCLAT, NCLT benches, SAT, the three HCs). We seed them manually from official lists; please confirm the sources. |
| **Q6.4** | E-filing practice (NCLAT e-filing stops the clock per *Sanket*). Physical-copy follow-up norms. |
| **Q6.5** | The open legal points in 02 §5 for the ranked triggers. These are reviewed in the rule sign-off sessions; there is no need to answer them in writing in advance. |

## 7. Product preferences (needed by weeks 10–17)

| # | Question |
|---|---|
| **Q7.1** | Firm templates for replies, para-wise grids and appeal memos (DOCX styles, cause-title format) |
| **Q7.2** | Digest: recipients, send time (default 06:30 IST), email allowed? Initial watchlists: statutes, topics, clients (company names / CINs), courts |
| **Q7.3** | Alerts: who gets matter alerts (matter team only by default)? Severity preferences? |
| **Q7.4** | Sign-in: Google Workspace or Microsoft 365? |
| **Q7.5** | Matter permissions: do any matters need restricted access (an ethical wall) from day 1? |

## 8. Success criteria and commercial (needed by week 12)

| # | Question |
|---|---|
| **Q8.1** | What would make the pilot a success for the firm (e.g. hours saved per memo, a deadline caught, adverse authority surfaced)? This feeds the week-20 go/no-go. |
| **Q8.2** | Pilot terms: fee or no fee, duration, exit, ownership of firm-specific artefacts (templates, gold set), confidentiality of our product roadmap. |
| **Q8.3** | Would the firm co-author a public Indian legal-AI benchmark later? This needs separate consent and possibly a BCI advertising check (12_P10 Q11, unverified). |
