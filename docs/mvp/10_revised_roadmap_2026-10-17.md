# 10 — Revised Roadmap (17 October 2026)

## 1. Why the Product is Re-centred

The product is a client file for law firms: a firm creates a client, opens matters (cases) under it, keeps every document there, and the system helps run each case through to filing. It must work for any kind of case across any court or tribunal.

Research is the one capability law firms already purchase elsewhere. Building research and a citator first placed the product in the position of an ungrounded secondary tool. Law firms operate their daily practice out of active client matter files, hearings, orders, and filings.

## 2. The "Works For" Rule

- **Universal capabilities first:** Anything that works for every case type and every court goes first (client entities, matter workspace, document vault, hearing dates, tasks, client updates, standard filing bundles).
- **Domain depth one area at a time:** Deep procedural rules, statute expressions, and specialized forms are added domain-by-domain, with Insolvency and Bankruptcy Code (IBC) first because the repository already contains its public orders and drafted RuleSpecs.

## 3. Revised Session Roadmap (R1 to R8)

| # | Session | Works for |
|---|---|---|
| R1 | Client file: client entity, matters under a client with free-text case type and court, document vault (PDF, DOCX, EML, ZIP) with stage tags, versions and private anchors, manual case-number entry | Any case |
| R2 | Hearings, dates and Today: manual hearing and date entry for any court; NCLT/NCLAT cause-list PDF matching on entered case numbers; new orders in IBC cases land in the matter via the IBBI delta crawl; Today page, phone-usable | Any case (manual); IBC (automatic) |
| R3 | Tasks with due dates linked to hearings or deadlines; client status link or email per matter; Excel import of live cases | Any case |
| R4 | Dates and facts from documents with exact quotes for lawyer confirmation; order-set dates for any court; statutory deadlines for the IBC pack only (02 Part A), after re-anchoring to India Code text | Any case (order-set); IBC (statutory) |
| R5 | Corpus to real scale: IBC, CIRP Regulations and AAA Rules from India Code with point-in-time for the 2026 amendment; IBBI mirror backfill; real embeddings as g2; hybrid retrieval; research inside the matter | IBC |
| R6 | Templates and filing bundles: vakalatnama, affidavit, memo of parties, annexure index first; then IBC forms (s.8 notice, s.7 and s.9 petition skeletons, reply skeleton), e-filing checklist, defect-cure tracker. Assemble, never submit | Any case (generic); IBC (forms) |
| R7 | Cite-check on uploaded drafts against the corpus, honest "not in MVP corpus" | Any case within corpus |
| R8 | Hardening and pilot: residency decision, DPA, backups and restore drill, firm-visible access log, two law firms live | — |

## 4. Plain-Words Reason for Each Session

- **R1:** Law firms organize their entire practice by client and matter; without the client file, case documents have nowhere to live.
- **R2:** Lawyers need to know what is happening today and upcoming across courts, with automatic cause-list order matching.
- **R3:** Matters move forward through assigned tasks, deadline tracking, and keeping clients informed on case progress.
- **R4:** Turning raw case filings into verified procedural facts and deadlines relieves lawyers from manual date auditing.
- **R5:** Real-scale statute, regulation, and order retrieval grounds legal analysis in authoritative primary sources.
- **R6:** Preparing standard court filings, affidavits, and petition skeletons cuts repetitive assembly work before submission.
- **R7:** Validating draft citations against corpus authorities ensures lawyers never file misattributed or out-of-corpus law.
- **R8:** Production security, residency compliance, backups, and access logs establish enterprise trustworthiness for pilot rollout.

## 5. Deferred List

The following capabilities from the original week-by-week build plan (`docs/mvp/05_build_plan.md`) are deferred, not deleted:
- **S09 Citator:** Deferred until the corpus possesses comprehensive statute expressions and appellate history links.
- **S12 Strategy Memo Chain:** Deferred until client facts and procedural clock integrations are active.
- **S17 Alerts and Digest:** Deferred until firm matters, watchlists, and regulatory feed integrations are established.
- **Corpus breadth beyond IBC (High Court subsets, SEBI, SAT, CCI):** Staged to follow IBC depth.

## 6. Beyond R8

After R8:
1. A module for insolvency professionals (CIRP compliance calendar, claims management, CoC meetings, IBBI forms).
2. Additional legal areas added one per session from `docs/mvp/02_workflows_and_rules.md` Parts B to D (Arbitration, Company law, Section 138 cheque bounce, and Commercial suits).
