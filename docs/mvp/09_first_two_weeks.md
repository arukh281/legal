# 09 — First Two Weeks (start Monday)

One page. F = founder, E = engineer, P = partner firm. Each item references the doc that defines it.

## Week 1

**Monday**
- [ ] **F:** Send the partner the pre-read: [00](00_mvp_spec.md) summary + [07](07_partner_firm_questions.md) §1–§3. Book the kick-off (1 h), the trigger-ranking session and the first rule sign-off slot.
- [ ] **F:** Send the counsel brief: 07 §1 (Q1.1–Q1.12) with [01](01_corporate_corpus_and_sources.md) §7.2 attached. Ask for a written opinion by the end of week 3.
- [ ] **E:** Create the repo; Django 5.2 + Django Ninja + React/Vite skeleton; CI (lint, type-check, tests); pre-commit; secrets in AWS Secrets Manager ([04](04_stack_and_infra.md) §0).
- [ ] **E:** In AWS ap-south-1, create RDS PostgreSQL 18 (pgvector enabled), S3 buckets (raw with Object Lock, tenant with SSE-KMS), and 2 EC2 + ALB. Turn on backups and PITR.

**Tuesday–Wednesday**
- [ ] **F:** Send the permission and notice emails to SEBI, CCI, Delhi HC (reproduction), NCLT and NCLAT (hyperlinks), IBBI (courtesy) and the SAT/NCLT registries (data access) (01 §6.2). Log every reply in `terms_ref`.
- [ ] **F:** **From an Indian network**, test India Code (`indiacode.gov.in` API + PDFs), e-Gazette, MCA, sci.gov.in and SAT. The research sandbox was blocked on several of these (02 §0; 01 §0.3).
- [ ] **E:** Schema v0. Apply 03 §3.1–§3.5:
  - `pipeline_version`;
  - `source` / `legal_profile` / `capture` / `raw_blob`;
  - work / expression / manifestation / `identifier_alias`;
  - `parsed_document` + `anchor` + `anchor_alias`;
  - `index_generation` + alias views;
  - the outbox table and Procrastinate.
- [ ] **E:** Anchor grammar v1.1 parser + validator as a library, with unit tests from 01_master §5.3 (incl. `pdoc_…/v1#…` and `sch-1.ord-8.rule-1`).

**Thursday**
- [ ] **P + F:** Kick-off.
  - **Trigger ranking** (07 Q2); name rule sign-off lawyers (Q2.2).
  - Residency answer, or an interim rule (Q3.1).
  - Closed-matter authorisation (Q4.1–Q4.2); user list and SSO provider (Q7.4).
- [ ] **E:** SSO login (django-allauth, firm Google or Microsoft); `tenant`, `user`, `matter_member` tables; `authz.can()` choke point (03 §6).

**Friday**
- [ ] **F:** Create legal profiles (PROVISIONAL) for IBBI orders, NCLAT, SC (open dataset + widget), India Code and the e-Gazette. Archive ToU, robots and copyright pages.
- [ ] **E:** Model Gateway v0: `model_task_contract`, 2 provider adapters, `llm_call_record`, per-task budget. `residency_policy` is stored per tenant (03 §3.15).
- [ ] **Check:** deploy to the server; SSO works for one partner user; anchor-grammar tests are green.

## Week 2

- [ ] **E:** IBBI orders adapter (NCLT, NCLAT, SC and HC sections). Store raw blobs (`sha256`), `capture` rows and `rights_class` / `provenance_tier`. Backfill the first 5–10K orders at ≤ 1 request per 3 seconds, at night IST (01 §6.2).
- [ ] **E:** PDF text-layer extraction; Textract OCR path for image-only pages (about a third of IBBI NCLT copies, 01 §0.3); `ocr_conf` per page.
- [ ] **E:** Ingest the IBC statute and its point-in-time inputs (01 §6.2 step a):
  - the India Code PDF (canonical);
  - IBBI's dated consolidations;
  - Act 6 of 2026;
  - S.O. 2625(E).

  Also ingest the AAA Rules 2016 and the CIRP Regulations.
- [ ] **F:** **Re-anchor the IBC RuleSpecs** (02 Part A) against the official text from an Indian network. Record `anchor_verified_at` and `anchor_text_hash`, and encode the golden vectors as tests.
- [ ] **F:** Seed `court_calendar` for NCLT benches, NCLAT and SC from the official holiday lists (02 §3 CV10; 01 §6.3 #4).
- [ ] **P + F:** **Rule sign-off session #1** (IBC, 1.5 h): walk through the 02 Part A rule cards and record sign-off or open questions.
- [ ] **P:** Choose the 20–30 closed matters (06 §3); the associate starts collecting packages.
- [ ] **F:** Draft the data-processing agreement and confidentiality undertaking (07 Q3.4). Write the security checklist (05 §8).
- [ ] **Check (end of week 2):**
  - 5–10K IBC orders captured, each with `rights_class` and a legal profile;
  - the IBC statute parsed with section and clause anchors;
  - the IBC RuleSpecs re-anchored, with golden-vector tests green;
  - the trigger ranking and residency answers recorded (or interim defaults logged);
  - counsel brief acknowledged.

## Do not start in weeks 1–2

- **Treatment classification.** Wait for the citation resolver (week 5).
- **Memo prompts.** Wait for the trigger ranking and retrieval (week 9).
- **Alerts and digest.** Weeks 16–17.
- **Any CAPTCHA-gated source, or any source without at least a PROVISIONAL legal profile.**
