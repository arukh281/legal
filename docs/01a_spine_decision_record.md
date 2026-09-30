# Spine v1.0 Decision Record (D1–D23)

The principal architect's rulings on every interface change proposed by the phase research, and on conflicts between phase documents. Precedence: this record and [01_master_architecture.md](01_master_architecture.md) §5–§9 override the provisional spine v0.1 (reproduced in Appendix A) and any phase document's own proposals. Phase documents record their dispositions in their "Spine v1.0 conformance" subsections.

Legend: ACCEPT / ACCEPT-MODIFIED / REJECT. "Owner" = the phase that owns the schema.


## D1. Technology posture (fixed)
- System of record: **PostgreSQL 18** (PLC metadata, anchors, chunks, bitemporal assertion store with WITHOUT OVERLAPS temporal keys, partitioned by predicate family). Graph traversal/PPR via an **in-memory CSR Graph Projection** rebuilt from Postgres; graph DBs only as optional analytics exports (P3).
- Text indexes: **OpenSearch** (BM25 + k-NN in the same doc, on-disk quantised vectors + rescoring), accessed only through P2's **Index Access Layer** (IndexQuery/IndexHit). pgvector only for small on-prem tenant planes.
- Bus: **Apache Kafka 4.x (KRaft)** with a **Postgres transactional outbox + Debezium** in every producer; real-time and bulk lanes on separate topics; retry + DLQ topics.
- Durable workflows: **Temporal** (self-hosted, or Temporal Cloud in an India region) for crawls/backfills, reprocess campaigns, P6 strategy jobs, alert lifecycles. DBOS fallback for small on-prem.
- AuthZ: **OpenFGA** (Zanzibar ReBAC), per-tenant store, deny-first ethical walls; Postgres FORCE RLS as backstop.
- Observability: OpenTelemetry (traceparent propagated in CloudEvents), self-hosted **Langfuse** in India, **OpenLineage** for data lineage.
- Model access only via the **Model Gateway** with normative `ModelTaskContract` (task_id, I/O schemas, eval gate, data_class_max, allowed_trust_labels, tools_allowed, batch_ok, per-family prompt variants), ≥2 qualified endpoints per task, fail-closed `residency_policy`.
- Dense embedder default: self-hosted Qwen3-Embedding-4B with Indian legal fine-tune (MRL 1024-d); reranker: bge-reranker-v2-m3 / Qwen3-Reranker (MVP) → fine-tuned Qwen3-Reranker (full). Both swappable behind contracts.
- Region: AWS Mumbai (ap-south-1) primary, Hyderabad (ap-south-2) DR; Indian GPU cloud secondary for self-hosted models.

## D2. Envelope (CloudEvents 1.0) — ACCEPT-MODIFIED (XC S11 + P9)
Extension attribute names must be lowercase alphanumeric: `tenantid`, `causationid`, `idempotencykey`, `schemaversion`, `dataclass` (PUBLIC|TENANT_CONFIDENTIAL|PRIVILEGED), plus standard `traceparent`. Wherever docs wrote tenant_id/causation_id/idempotency_key/schema_version *as envelope attributes*, treat them as these names (payload fields may keep snake_case).
**Privacy-Gate envelope rule:** any PLC-side event caused by tenant activity carries `tenantid` = null, a fresh trace root and no tenant causation chain.

## D3. Impact propagation topology — ACCEPT (P4/P7/P10 consensus). REPLACES spine "P7 registers dependency fingerprints with P4".
P4 publishes signed `impact.detected.v1` on the public topic `plc.impact.public.v1` with `tenantid`=null and a public `affected[]` closure (+ manifest_uri/sha256 for large closures). Each tenant cell's **Impact Matcher** (P4-owned `impact-match-core` library, run by P7 in the tenant boundary, also on-prem) matches it against the private `matter_dependency` inverted index. Tenants download whole manifests (never per-ID lookups). P4 never stores tenant dependency sets.
**PLC read-path rule (resolves P4 side-channel concern):** synchronous PLC read APIs (Graph Query API, Index Access Layer, anchor API) called from tenant contexts are stateless: no tenant-attributable ID logs outside the tenant-scoped audit store; ops telemetry is tenant-redacted; D3/D4 deployments use a local PLC replica.

## D4. Event catalogue v1.0 (all ACCEPT; owner = producer)
Spine originals: `raw.captured.v1`, `doc.parsed.v1`, `doc.indexed.v1`, `graph.delta.v1`, `impact.detected.v1`, `matter.alert.v1`, `feedback.recorded.v1`, `reprocess.requested.v1`.
Added: `source.health.v1` (P0), `acquire.requested.v1` (P4/P3→P0; reasons incl. COVERAGE_GAP, LINEAGE_WATCH), `source.recheck.requested.v1` (P9/P3→P0), `identity.merged.v1` / `identity.split.v1` (P1→P2,P3,P4,P7), `doc.redacted.v1` (P0/P1/ops/legal → P2,P3,P4,P5 caches,P7; data = RedactionOverlay; this is the single name — replaces "plc.redaction.v1"), `index.generation.promoted.v1` (P2), `kg.proposal.v1` (P9→P3), `kg.proposal.resolved.v1` (P3→P9; replaces "kg.proposal.status.v1"), `retrieval.served.v1` (P5/P6→P8,P9 tenant plane; schema owned by P5), `matter.document.ingested.v1` (P7→P6,P10), `strategy.memo.published.v1` / `strategy.memo.stale.v1` (P6→P7,P10), `verification.completed.v1`, `eval.run.completed.v1`, `eval.case.adjudicated.v1` (P8), `eval.case.proposed.v1`, `training.dataset.published.v1`, `feedback.resolved.v1` (P9), `erasure.requested.v1` / `erasure.completed.v1` (P7→P9,P2,P5,P6), `alert.state.v1`, `interaction.logged.v1`, `digest.edition.published.v1` (P10).
Case-tracking feeds: P0 owns all court-portal connectors (case status by CNR, cause lists, daily orders, court calendars) and publishes **tenant-agnostic** feeds; watch registry is an unattributed union; P7 matches locally.
P3 must emit a `graph.delta.v1` (possibly empty) for every `doc.parsed.v1` (propagation frontier). graph.delta.v1 gains `graph_watermark`, `cause{kind: EXTRACTION|HUMAN_REVIEW|RECOMPUTE|SCHEDULED|RETRACTION|PROPOSAL, ref}`, `status_changes[].{definitive, reason_codes, valid_from}`, `manifest_uri`. P3 exposes `commit_status_batch` so P3 stays the single writer of status.

## D5. impact.detected.v1 / matter.alert.v1 — ACCEPT merged (P4 SP4-1, P7 2.5-2, P10 S10-3)
impact.detected.v1 adds: impact_version, lifecycle PROVISIONAL|CONFIRMED|UPDATED|RETRACTED, supersedes_impact_id, change_kind, cause_kind LAW_CHANGE|KNOWLEDGE_CORRECTION|RECLASSIFICATION|SCHEDULED, root{old,new,direction}, trigger_authority, affected[]{id, ring, via, weight}, affected_count, manifest_uri+sha256, temporal_scope RETROSPECTIVE|PROSPECTIVE|FROM_DATE|CONDITIONAL, significance, verification{definitive, review_state}, coalesce_key, graph_watermark, doctrine_version, p4_logic_version, storm.
matter.alert.v1 = {alert_id, tenant_id, matter_id, alert_kind AUTHORITY_CHANGE|NEW_ORDER|HEARING_LISTED|HEARING_CHANGED|DEADLINE_DUE|DEADLINE_PROPOSED|DOCUMENT_RECEIVED|SYNC_STALE|WALL_VIOLATION_ATTEMPT, severity 1|2|3, impact_id?, impact_version?, lifecycle?, source_event_id, dedupe_key = hash(impact_id|source_event_id, matter_id), subject_ids[], definitive, revision, supersedes_alert_id?, requires_ack, due_at?, recipients[], explanation{text (deterministic template), anchors[]}, sensitivity}. Alerts update in place; retractions reach every original channel.
Severity-1 on a machine-detected impact only if: explicit cue, doctrinally competent bench, confidence ≥0.9, official source (P4 rule).

## D6. Authority semantics — ACCEPT (P3)
- `AuthorityView` (new §H object, P3-owned) is the ONLY input for badges, P5 ranking features and P8 status checks: {subject_id, status GOOD|CAUTION|NEGATIVE|PARTIAL_NEGATIVE|UNKNOWN, definitive, reason_codes[], status_confidence, status_mode CURRENT|HISTORICAL, valid_from/valid_to segment, binding_on_forum BINDING|PERSUASIVE|NOT_BINDING|UNDETERMINED, binding_basis{rule_ids, authority_anchor_ids, contested}, court_level, bench_strength, treatment_summary, graph_watermark}.
- Status enum stays 5-valued. "Under review" = status CAUTION + definitive=false + reason_code NEGATIVE_SIGNAL_UNDER_REVIEW. Coverage gaps = UNKNOWN + reason_code COVERAGE_GAP. (Resolves P8 S8-8.)
- Date semantics: statute text/validity at `as_of_legal_date`; precedent status at `as_known_at` in CURRENT mode (declaratory/retrospective), with the prospective-overruling exception resolved by P3; HISTORICAL mode optional.
- Asymmetric display: plausible unverified negatives show immediately as CAUTION (never hidden, never definitive); definitive only after HITL for impact_tier 1.
- AuthorityStatus "no change" equivalence (P4): same (status, definitive, reason_codes, binding rule_ids, confidence bucket 0.1).
- Doctrine library `authority-core@semver` with cited DoctrineRules; contested rules return both views.

## D7. Assertion & ontology — ACCEPT (P3)
Assertion adds logical_key, version, justification{kind EXTRACTED|DERIVED|ATTESTED|HUMAN|IMPORT, rule_id, from_assertion_ids[]}, extraction_run_id; qualifiers speaker, opinion_role, effect RETROSPECTIVE|PROSPECTIVE, effective_from, change_type, territory, proposal_ids[]. Predicates added: HOLDS, OBSERVES, RELIES_ON, RESTATES, ANSWERS_REFERENCE, DISMISSES_IN_LIMINE, RECALLS, ATTESTS_TREATMENT, NO_COUNTERPART_IN, PRECEDENT_CARRIES_TO (derived), IN_FORCE_IN, DECLARES_SUB_SILENTIO. Provision ID form `{work_id}#{fragment}` (expression-independent) — ACCEPT (S3-7). Crosswalk: CORRESPONDS_TO at clause level, many-to-many, change_type + diff_ref + source OFFICIAL_TABLE|JUDICIAL|EDITORIAL|MODEL, always impact_tier 1.

## D8. Anchors — ACCEPT
- Private anchors: `{pdoc_id}/{pver}#{fragment}`; pver v1..vn; new fragments m12, m12.att2, hdr.from|to|date|subject, sheet2.r15.c4, pg3.rg2, t00:03:15-00:03:40. Clause-within-proviso `sec-138.p1.c` is valid grammar.
- Machine translations are NOT Expressions (public: Chunk.mt shadow field; private: display renditions `v1.mt-en`). MT renditions may be displayed/aligned but are never support anchors; claims anchor to original-language (or official-translation) text.
- Anchor read API exposes: text, text_hash, page/bbox, rhetorical_role, speaker, opinion_role MAJORITY|CONCURRING|DISSENT|REFERENCE_ORDER, ocr_conf, sibling-expression links, `is_authoritative_expression`.
- Persist anchors, never chunk_ids, in any durable cross-phase record (feedback, claims, dependencies). chunk_id is deterministic but generation-scoped.

## D9. Core objects — ACCEPT merged
- Manifestation + raw.captured.v1 add `rights_class` OFFICIAL|OPEN_LICENSED|THIRD_PARTY_LINK_ONLY|LICENSED_RESTRICTED|USER_UPLOADED (runtime filter for any external/API output).
- ParsedDocument.quality adds `hidden_text_flags[]`; plus P1's quality.gate, anchor_changes, supersedes_parse_id, work_id_status.
- `trust_label` on MatterContext.documents[], EvidenceBundle.items[], chunks: PLC_OFFICIAL|PLC_THIRD_PARTY|TENANT_CLIENT_DOC|TENANT_OPPOSING_DOC|TENANT_CORRESPONDENCE|TENANT_WORK_PRODUCT|USER_INPUT. Only PLC_OFFICIAL, TENANT_WORK_PRODUCT and USER_INPUT may influence control flow; everything else is data-only (dual-LLM / plan-then-execute).
- **Tenant Execution Context (TEC)** (P7): signed ≤5-min token {tenant, matter scope, purpose, authz consistency token, llm_policy, residency_policy, DEK grants}; required for any TPL access by P5/P6/P8/Gateway/index shards. All caches (provider prompt cache, prefix cache, semantic cache) isolated per tenant+matter; no cross-tenant semantic cache.
- ResearchQuery adds: as_known_at, mode QUICK|STANDARD|DEEP, seed_ids[], issue_hints[{issue_id, text, elements[], client_position}], stance_target SUPPORTING|ADVERSE|BOTH, requester{kind, agent_role}, residency_policy, experiment{exp_id, arm}, personalization_profile_ref, budget{latency_ms, max_items, max_cost_usd, max_llm_calls, max_input_tokens}.
- EvidenceBundle adds (P5): as_known_at, index_generation, graph_watermark, pipeline_version, warnings[], searched[]; items[] add role RULE|APPLICATION|TREATMENT|STATUTE_TEXT|ADVERSE|PROCEDURAL|RECORD_FACT, source_layer PLC|TPL, trust_label, lang, pack{…}, display_rank, group, retrieval_signals.{rerank, ltr, legs_hit}, authority = AuthorityView subset + via_crosswalk + statute_version, stance.rationale_anchor, quality{ocr_conf, is_authoritative_expression}; private items (source_layer TPL) have work_id null and authority null. coverage.per_issue adds sufficiency SUFFICIENT|THIN|NONE, adverse_search{contra_queries, binding_candidates_examined, graph_negative_checks, attested}, pending_references[], conflicts[]. PublicEvidenceBundle (no stance, NEUTRAL only) for the external PLC API.
- MatterContext adds (P7/P6/P4): context_version, context_hash, as_of_legal_date_default, case_links[], documents[].{pver, provenance, trust_label, privilege_class, received_on}, fact_timeline[].{date_precision, asserted_by, status PROPOSED|CONFIRMED|DISPUTED, contradicted_by}, opponent_claims[], **procedural_events[]{event_type (controlled vocab), date, certainty, alt_dates, anchor, confirmed_by?, source EXTRACTED|LAWYER}** (key_dates becomes a derived view incl. date_basis-matched keys), facts{} for scope predicates, deadlines[], privilege_flags.outbound_forbidden_anchors_bloom, access_policy{authz_token, llm_policy}, residency_policy. Only CONFIRMED facts back RECORD_FACT claims without an "unconfirmed" label.
- Claim adds (P6 C2): issue_ids[], origin_role, strength STRONG|ARGUABLE|WEAK|UNTENABLE (ordinal only), assumptions[], support[].span, computed_ref (PROCEDURAL claims reference a Deadline computation AND ≥1 statutory anchor), revision_of. Rule unchanged: every non-STRATEGIC_OPINION claim needs ≥1 anchor; summaries (sum_) never count as support.
- New objects: `Deadline` (P6), `DraftArtifact` (P6), `Summary` (sum_, P2, non-citable), `IndexQuery/IndexHit` (P2), `Freshness` (P4: law_current_to, capture_frontier, propagation_frontier, stage_lag, known_gaps, source_health), `CitationAuditReport`, `EvalCase` (evc_), `EvalRun`, `GateDecision` (P8), `KgProposal` (P9), `RedactionOverlay`, `ModelTaskContract`, `LLMCallRecord`, `AuthorityView`.
- VerificationReport (P8): statuses VERIFIED|PARTIAL|UNSUPPORTED|CONTRADICTED|BAD_LAW|UNVERIFIABLE; gate PASS|PARTIAL|BLOCK with section_gates and the P8 aggregation rule (tier-1 section failure — deadline, limitation, maintainability — BLOCKs that section; memo is PARTIAL with a withheld list); display_band (4 ordinal bands with audited error rates); warrant{exists, quote_exact, pinpoint_support, role_ok, status_ok, binding_ok, temporal_ok, numeric_ok, attribution_ok}; reason_codes; narrowed_text; suggested_anchor_ids; graph_watermark; anchor_generation; verifier_version; coverage; signature; supersedes_report_id.
- FeedbackEvent (P9 + P10): actor_ref (tenant pseudonym), reason_code (closed enum), context{query_id, trace_id, impression_id, position, surface (incl. DIGEST, WORD_ADDIN, SOURCE_VIEWER, COMMAND_BAR, MOBILE, WHATSAPP), ranker_version, memo_id}, consent_snapshot_id, recorded_at; target kinds + ANCHOR, CITATION_MENTION, DRAFT_SPAN, MEMORY_ITEM; actions + FLAG_WRONG_TREATMENT, FLAG_PARSE_ERROR, FLAG_MISSING_AUTHORITY, USED_IN_FILING, RETRACT; privilege_class PUBLIC_OBJECT_SIGNAL|CONFIDENTIAL|WORK_PRODUCT|PRIVILEGED.
- Privacy Gate classes (P9): S0 objective defect, S1 legal status, S2 relevance/strategy (aggregates only, k≥5 tenants, DP noise), S3 private (never crosses). Closed-vocabulary codes + public IDs only.

## D10. Pipeline versioning — ACCEPT
`pipeline_version` = component@semver + model_id + model_snapshot + endpoint_region + prompt_hash.

## D11. Evaluation gate policy — ACCEPT (P8)
Zero-tolerance sentinel suites + one-sided 95% paired-bootstrap non-inferiority at δ_s = max(1pt, 2·SE_diff,s) per slice + rolling 3-release windows. Replaces "no regression >1pt" wherever it appears (P9, XC).

## D12. ID prefix registry (collisions resolved)
wrk_ work · cas_ case/proceeding · man_ manifestation · sha256: raw · asr_ assertion · prp_ proposition · lga_ legislative action · crt_ court · bnc_ bench · jdg_ judge (person) · itp_ public issue-topic taxonomy node (**P3 must rename its iss_ → itp_**) · iss_ private matter issue (P7) · rvw_ review task · rul_ doctrine rule (P3) · prs_ procedural RuleSpec (P6) · ddl_ deadline · drf_ draft artifact · mem_ strategy memo · clm_ claim · ter_ territory · xrn_ crosswalk row · sum_ summary · chk_ chunk · pdoc_ private document · mat_ matter · ten_ tenant · imp_ impact (P4) · alr_ alert · uim_ UI impression (P10) · fb_ feedback · kgp_ KG proposal · evc_ eval case · gld_ gold set · evr_ eval run · aud_ citation audit · qry_ query · evb_ evidence bundle · vr_ verification report · job_ strategy job · camp_ reprocess campaign · dig_ digest edition. Any doc using a colliding prefix must adopt this registry.

## D13. External surface — ACCEPT (post-MVP; CT)
**PLC Access API / MCP** (owner P10 BFF, backed by P5/P3): resolve_citation, get_anchor (point-in-time anchor form), authority_status, research(PublicResearchQuery) → PublicEvidenceBundle; rights_class-filtered; metered; tenant-less.

## D14. Model allocation — ACCEPT (XC + P3 refinement of the client's hypothesis)
"Premium for KG construction, cheap for serving" is REFUTED as a phase rule and replaced by **risk-weighted allocation**: model tier = f(impact_tier, calibrated uncertainty, residency). Construction = cascade (deterministic rules → cue rules → distilled small classifier → premium LLM on ~5–12% hard/high-impact slice, dual-provider for tier 1 → human for tier 1). Serving of graph facts uses zero LLM. Premium reasoning models are used at serving time for P6 advocate/opponent/bench roles (two different families), with in-India endpoints for IN_ONLY tenants.

## D15. Residency reality (verified by XC, Sep 2026)
No in-India Claude processing; IN_ONLY tenants route to Bedrock "in." OpenAI GPT-5.6 profiles, Azure southindia regional/provisioned deployments, or self-hosted open-weight (Sarvam-105B, Qwen3). Claude/global endpoints only for PUBLIC data or tenants with residency ANY. Per-residency quality scores published by P8.

## D16. P0 / P1 / IN addendum (all ACCEPT unless noted)
- **raw.captured.v1** adds (P0): capture_id, norm_fingerprint{scheme,value}, warc{file_uri,record_id,offset}, fetch_context{adapter, access_mode OPEN|BULK_DATASET|LICENSED_API|HUMAN_ASSISTED|PARTNER_CONTRIBUTED, egress_region, tls_leaf_sha256, browser}, provenance_tier OFFICIAL_PRIMARY>OFFICIAL_AGGREGATOR>OPEN_DATASET>LICENSED_THIRD_PARTY>PARTNER_CONTRIBUTED, listing_raw_id, first_seen_at, lang_hint, near_dup_hint[], flags{text_layer, malware_suspect, injection_suspect, soft_error_suspect, suspected_replacement}, rights_class (D9). change_kind adds METADATA_CHANGED and **SUPPRESSED** (ACCEPT-MODIFIED: an explicit kind, NOT "DELETED + suppression{}" — consumers must tombstone and purge per doc.redacted.v1). UNCHANGED only in verification sweeps; DELETED only after 3 absent sweeps + 404/soft-404.
- **acquire.requested.v1** (→P0): {request_id, reason UNRESOLVED_CITATION|MATTER_WATCH|CORRIGENDUM_SUSPECTED|COVERAGE_GAP|LINEAGE_WATCH|LOW_QUALITY_COPY|OPS, target{scheme, value, court_hint, date_hint}, priority, deadline, allowed_access_modes}; tenantid always null; MATTER_WATCH only via the Privacy Gate. Request-only schemes URL/CITATION_STRING never written to identifier_alias.
- **source.health.v1** (P0→P4,P8,P10): {source_id, status OK|DEGRADED|DOWN|BLOCKED, freshness_lag_p95, last_success_at, coverage_estimate, expected_pending, backing, incident_id}.
- **judgment.expected.v1** (NEW, ACCEPT; P0→P3,P4,P10): "pronounced, text awaited" signals from cause lists / daily orders / official notices; P3 records an EXPECTED stub work; P4 may raise a PROVISIONAL impact flagged "text awaited" for constitution-bench / larger-bench pronouncements.
- P0 also publishes tenant-agnostic **CourtCalendar** (holidays, vacations, sitting days) consumed by the P6 Procedural Clock, and case-status / cause-list / daily-order feeds (D4).
- Judgment paragraph anchors use ONLY court-issued numbering (never a reporter's); unnumbered → synthetic u-numbers (EBC v. D.B. Modak).
- Bus: "Kafka API" — Apache Kafka 4.x / MSK ap-south-1; Redpanda acceptable (API-compatible). Temporal for P0 schedules/backfills.
- **Anchor grammar (P1)**: optional opinion prefix `o{n}.` (unprefixed = o1), e.g. `#o2.p14`; fallback `pg{n}` / `pg{n}.l{m}` for QUARANTINED docs (locators only — never sufficient support for impact_tier-1 claims); extra fragments `ill-x`, `p12.a`, `p12.u1`, `p45.x1`, `att{n}/` accepted; 01_master_architecture publishes the full EBNF.
- **Expression authority attributes (P1/IN)**: authoritative, derived, verification ROUNDTRIP_OK|UNVERIFIED, translation_of, authority_basis. Reconstructed point-in-time statute text is derived=true; only official or ROUNDTRIP_OK text may back tier-1 claims. OLA s.7 Hindi originals and HC-issued English translations are both Expressions with an `authoritative` flag.
- **Machine translation (final)**: NOT an Expression anywhere. Public: `nodes[].aux_text['{lang}-x-mt']` / `Chunk.mt`, authoritative=false. Private: display rendition `v1.mt-en`. IN's "OUR_MT expressions" wording must be changed to "MT renditions". A claim anchored to MT fails P8.
- **Masking / takedown (final)**: one event **doc.redacted.v1** carrying a **RedactionOverlay** {overlay_id, scope WORK|EXPRESSION|ANCHOR_SPANS, kind SUPPRESS_ALL|MASK_SPANS|NAME_SEARCH_SUPPRESSED|COURT_PROHIBITION, spans[], legal_basis, ordered_by?, effective_at, purge_sla}. Masking is an overlay: indexes, snippets, exports and quote checks use the masked rendition; NO masked expression_key (reject IN's `en.m1`). Work gains `access_restriction{name_search_suppressed[], masked_expression_required, court_prohibition}`. IN's `work.access_restricted.v1` is folded into doc.redacted.v1.
- **identity.merged.v1 / identity.split.v1**: {kind WORK|CASE|ALIAS, from_id, to_id, reason, confidence}.
- **doc.parsed.v1** adds quality.gate PASS|FLAGGED|QUARANTINED, work_id_status, case_ids[], supersedes_parse_id, anchor_changes{preserved, aliased, tombstoned, new}. **pdoc.parsed.v1** (tenant-scoped, same payload shape, P1-tenant-mode→P7) + **ParseRequest** (P7→P1 tenant mode). P7 then emits matter.document.ingested.v1.
- **ParsedDocument** node shape per P1: spans[] (page+bbox per span), rhetorical_role {label, confidence, source}, speaker, opinion ref; quality.lang[]; metadata.opinions[]{author, kind}; amendment_instructions[] (AmendmentInstruction); security{}; pages[].text_source.
- **CitationMention** adds mention_kind, char_range, pin{kind, value, cited_anchor}, cluster_id, antecedent_mention_id, case_name_as_printed, context{rhetorical_role, speaker, cue_spans}, resolution_method, temporal_check.
- **identifier_alias** adds status ACTIVE|PENDING|REJECTED|SUPERSEDED and trust_tier T0 court-issued | T1 harvested parallel clusters | T2 official tables | T3 contracted third party | T4 model-inferred; third-party never overrides T0. New schemes SCC_SUPP, SCC_SERIES, AIR_SCW, AIRONLINE, NJRS; NEUTRAL_HC normalised as court_code|bench_code|year|n|bench_type; SC_DIARY_NO n/yyyy.
- ID registries add ent_ (recurring institutional parties only; no global IDs for individuals).
- **Temporal context (IN, ACCEPT-MODIFIED)**: MatterContext.procedural_events[] is the raw record; a derived `temporal_context{substantive_event_date?, proceedings[]{stage, initiated_on, initiation_kind JUDICIAL|MINISTERIAL, concluded_on?}, filing_date?}` is exposed on MatterContext and optionally on ResearchQuery; as_of_legal_date remains the default. The unit of criminal-code transition is the proceeding stage; the offence date governs substantive law (governing_code() procedure owned by 21_india, implemented in P3).
- **Territorial versions (IN)**: statute expression_key = `lang@YYYY-MM-DD[~TERR]` (ISO 3166-2:IN); point-in-time resolution takes (date, territory). Assertion qualifier effect adds MOULDED with conditions[]{text, anchor_id}.
- **Crosswalk enum (final, canonical = IN)**: change_type SAME_RENUMBERED|SAME_TEXT_SPLIT|MERGED|SPLIT|MODIFIED_SCOPE|MODIFIED_PENALTY|REPLACED_BY_DIFFERENT_OFFENCE|FUNCTIONAL_ANALOGUE|NEW_NO_PREDECESSOR|OMITTED, plus group_id, granularity, penalty_delta, chain_prev, source_kind OFFICIAL_TABLE|JUDICIAL|EDITORIAL|MODEL. P3 adopts this enum (with its mapping table from any earlier enum).
- AuthorityView.binding_basis adds conflict LARGER_BENCH|EARLIER_COEQUAL|UNRESOLVED. DoctrineRule registry `rul_IN_PREC_01..22` in 21_india is the canonical doctrine source for P3's authority-core.
- MatterContext.privilege_flags gains basis (IN C9).

## D17. Deployment naming (final)
D1 pooled SaaS cell · D2 dedicated cell (our India cloud) · D3 customer VPC · D4 on-prem/air-gapped (signed daily PLC delta bundles + self-hosted open-weight models) · D4h on-prem stores + in-India cloud LLM endpoints (XC's "C-lite"). XC's A/B/C naming maps A→D1, B→D2/D3, C→D4, C-lite→D4h. **MVP = one D2 dedicated cell for the design partner, running the same code as D1**; D1 opens at GA.

## D18. Cost planning figures to use downstream (from 13_cross_cutting, corrected)
Build (cascade): ≈$90K at 5M docs, ≈$180K at 10M, ≈$360K at 20M (all-premium LLM enrichment alone would be ≈$285K / $569K / $1.14M). Monthly run at 2,000 seats: ≈$77K (5M corpus) and ≈$89K (20M) — use these corrected figures, not the uncorrected table values. Per-unit serving: Q&A ≈$0.086, strategy memo ≈$1.66. All are planning estimates pending the P1 10K-doc measurement sample.

## D19. Synthesis-pass rulings (architect, after conformance pass)
1. **Cost figures of record (supersedes the per-unit numbers in D18):** tokenizer-corrected serving ≈$0.105 per verified Q&A and ≈$2.16 per strategy memo; monthly ≈$77K (5M corpus) / ≈$89K (20M) at 2,000 seats. The uncorrected $0.086/$1.66 are list-price lower bounds only. 08_P6's ≈$2.7/memo (placeholder prices, excl. retrieval/verification) is a sensitivity upper bound; 13_cross_cutting is the canonical cost model.
2. **VerificationReport.degradations[] — ACCEPT (XC S8):** `degradations[]{kind BUDGET|SOURCE_STALE|MODEL_FALLBACK|RESIDENCY_FALLBACK|INDEX_LAG|COVERAGE_GAP, detail, affected_claim_ids[]}` on VerificationReport, mirrored in EvidenceBundle.warnings[]; P10 must disclose any degradation next to the answer.
3. **Redaction acknowledgements — ACCEPT:** new event `redaction.applied.v1` {overlay_id, consumer (P2|P3|P4|P5|P7|P10|REPLICA:<id>), applied_at, generations_purged[]} from every consumer of doc.redacted.v1; P0 keeps the redaction ledger and alerts on purge_sla breach. ID prefix `ovl_` for overlay_id (as in 01 §7.13).
4. **Real-time lane under D3:** P4 never knows tenant interest. ALL impact_tier-1 impacts (and judgment.expected.v1 for larger/constitution benches) take the real-time lane; for other impacts significance = public citation footprint (in-degree / PPR centrality; threshold [NOVEL — unvalidated]). An unattributed union watch-list via the Privacy Gate (k≥5 tenants, decoy-padded) is a post-GA optimisation, not MVP.
5. **Work.integrity_flags[] — ACCEPT (CT 4b), owner P3:** {RECALLED, AI_GENERATION_ALLEGED, CORRIGENDUM_PENDING, WITHDRAWN_FROM_SOURCE, SUPPRESSED}, derived from P0 signals and the RECALLS predicate; surfaced via AuthorityView.reason_codes and the PLC Access API.
6. **CitationMention.pin — ACCEPT extension:** pin{kind, value, cited_anchor, method SAME_NUMBERING|QUOTE_ALIGN|PAGE_SPAN_ALIGN|UNRESOLVED, confidence}. P8 rule: PAGE_SPAN_ALIGN alone is never sufficient for VERIFIED.
7. **D2 cells** read the shared PLC through the stateless read path (same region); a local replica is optional. D3/D4/D4h MUST use a local replica; the ≤24 h replica-lag SLO applies to D3/D4/D4h.
8. **P1 owns the 10K-document stratified measurement sample** in M0 (tokens/doc, pages/doc, OCR share, citations/doc, Indic share); XC's cost model and the roadmap rebase on it.
9. **LLMCallRecord consumers:** P8 (audit replay, per-residency quality), P9 (lineage/erasure), FinOps (13). 
10. **Sequencing:** MVP/M1 = one D2 cell (D17); the deployment menu (D1–D4h) is published at GA (M3); PLC Access API/MCP (D13) after M2 coverage. 13_cross_cutting's "multi-tenant SaaS MVP" wording is superseded by D17.

## D20. Rulings on conformance-pass questions (final)
1. **Court-feed events ratified** (producer P0, tenant-agnostic, consumers P7 Impact/Case Matcher, P6 Procedural Clock, P10): `case.status.observed.v1`, `court.causelist.published.v1`, `court.calendar.published.v1`. Daily orders/judgments still flow raw.captured → doc.parsed.
2. **acquire.requested.v1**: no PRONOUNCEMENT_EXPECTED reason; use COVERAGE_GAP + internal `sub_reason`. Producers: P1 (UNRESOLVED_CITATION, CORRIGENDUM_SUSPECTED, LOW_QUALITY_COPY), P3/P4 (COVERAGE_GAP, LINEAGE_WATCH), P9 Privacy Gate (MATTER_WATCH, unattributed), ops (OPS).
3. **doc.redacted.v1**: producers P0 (source suppression, captured court orders), P1 (statutory identity masking detected in parsing), ops/legal (manual); consumers P1 (anchor read API), P2, P3, P4, P5 caches, P7, P10, replicas; de-duplicate on overlay_id; each consumer acks with `redaction.applied.v1` (D19.3). **RedactionOverlay canonical field list = 01_master §7.13** (superset of D16: work_id, expression_key, review_state, structured legal_basis, structured purge_sla).
4. **EXPECTED stub works**: P1 is the sole writer of Work/Case identity; P3 (on judgment.expected.v1) requests P1's identity service to mint `work.status = EXPECTED`.
5. **ID prefixes (additions/fixes to D12)**: parse_id = `par_` (P2/P3 examples showing prs_ for parse_id must change; prs_ stays P6 RuleSpec); `xrn_` = crosswalk row, `xtr_` = extraction run; `ovl_` = RedactionOverlay; `jex_` = judgment-expected record (P0's `exp_` renamed to avoid confusion with expressions); P0-internal `cap_` capture, `crun_` crawl run, `acq_` acquisition request, `lp_` legal profile, `cal_` court calendar — registered.
6. **identity.merged.v1.reversible_until**: optional, non-normative — ACCEPT.
7. **Proposition.law_declared** (ART142_DIRECTION | EXPRESSLY_NOT_PRECEDENT | CONCESSION_BASED | PER_INCURIAM_DECLARED | NORMAL) — ACCEPT as optional P3 field; authority-core treats ART142_DIRECTION and EXPRESSLY_NOT_PRECEDENT as non-binding precedent. binding_basis.weight is NOT adopted (expressed via rule_ids).
8. **Doctrine registry** = `rul_IN_PREC_01..24` (21_india §4.1), all canonical.
9. **source.recheck.requested.v1** schema owner = P9; 01_master §6.4 field list is canonical until P9 confirms.
10. **hidden_text_flags[]** = string codes; per-region detail in `security.hidden_text_regions[]` (P1) — ACCEPT.
11. **Crosswalk source_kind (final)** = OFFICIAL_TABLE | GAZETTE_TEXT_DIFF | JUDICIAL | EDITORIAL | THIRD_PARTY | MODEL (extends D16). change_type = D16 canonical enum; P5's via_crosswalk penalty must key on it (mapping from the legacy enum in 05_P3 §5.7).
12. **COVERAGE_GAP (refines D6)**: a coverage gap adds reason_code COVERAGE_GAP and sets definitive=false without changing status, UNLESS the gap exceeds the per-source threshold (default 72 h for HOT, 7 days for WARM/COOL sources that can bind the forum), in which case a GOOD status degrades to UNKNOWN. Negatives never lose their status on a gap. P10 shows "status current to <law_current_to>".
13. **pdoc.parsed.v1** consumers: P7 and P2 (tenant mode) on the tenant-scoped topic.
14. **doc.parsed.v1** adds `rights_class` and `provenance_tier` (copied from the manifestation) — ACCEPT.
15. **Erasure path**: every consumer of erasure.requested.v1 (P2, P5 caches, P6 memory, P9) emits `erasure.applied.v1` {erasure_id, consumer, applied_at, scope}; P7 aggregates and emits `erasure.completed.v1` (mirrors redaction acks).
16. **Kafka topic naming**: `{plane}.{domain}.{event}.v{n}` with plane ∈ `plc` | `tpl.<tenant>`; e.g. `plc.raw.captured.v1`, `plc.doc.parsed.v1`, `plc.impact.public.v1`, `plc.judgment.expected.v1`, `plc.doc.redacted.v1`, `tpl.<tenant>.pdoc.parsed.v1`. All producers (incl. P0) adopt it; 01_master publishes the topic map.
17. **P3 commit_status_batch** signature (batch_id, cause, computed_at_watermark, doctrine_version, rows[] → committed/unchanged/rejected) — ratified.

## D21. Final rulings (P5/P6/P8/P7/P9/P10 conformance questions)
1. **P5 FRESH_CITER reprocess — REJECTED.** P5 never emits PLC events from a tenant context. P4 guarantees that every new judgment is extracted by P3 (propagation frontier); P5 shows "treatment pending" from the P4 Freshness API (propagation_frontier) instead.
2. **Chunk.binding_scope_tags[] — ACCEPT (P2 owns field, P3 supplies values):** materialised court-hierarchy scopes (e.g. ALL_INDIA for SC; STATE:IN-MH for Bombay HC; TRIBUNAL:NCLT-ALL), refreshed on graph.delta.v1; exposed as an Index Access Layer filter for P5's binding-authority leg.
3. **Consumer lists (01_master event catalogue must reflect):** identity.merged/split.v1 → P2, P3, P4, P5, P7, P8, P10; index.generation.promoted.v1 → P4, P5, P8, P10; doc.redacted.v1 → P1, P2, P3, P4, P5 caches, P7, P8, P9, P10, replicas; erasure.requested.v1 → P2, P5, P6, P8, P9 (producer P7); **erasure.completed.v1 producer = P7** (after erasure.applied.v1 acks); training.dataset.published.v1 → P3, P5; plc.impact.public.v1 → P7 Impact Matcher, P6 RuleSpec registry, P10 (non-matter watches); model.endpoint.candidate.v1 (NEW, Model Gateway → P8 offline gate); matter.document.ingested.v1 → P6, P10 (P6 doc must reference it).
4. **opinion_role (final)** = MAJORITY | CONCURRING | DISSENT | REFERENCE_ORDER | UNKNOWN (per curiam → MAJORITY). P2's Chunk uses opinion_role (retire opinion_type).
5. **Bundle-local issue IDs** `qry_…/i{n}` for issues P5 decomposes without a matter — ACCEPT. **MaintainabilityCheck** prefix `mck_`; Claim.computed_ref targets = Deadline (ddl_) or MaintainabilityCheck (mck_).
6. **Memo-level gate:** BLOCK = no displayable section OR a memo-level integrity failure; a tier-1 section BLOCK makes the memo PARTIAL (P8 §5.4) — ratified.
7. **procedural_events[].event_type vocabulary** owned by P6 (versioned with RuleSpecs); stored by P7. **Auto DEADLINES_ONLY job** on matter.document.ingested.v1 — ACCEPT, tenant-configurable, default on; trigger dates need lawyer confirmation before a deadline becomes definitive.
8. **Reason-code registries:** verification reason codes owned by P8 (incl. MT_ANCHOR, LOCATOR_ONLY_ANCHOR, DERIVED_TEXT_TIER1, MASKED_SPAN_QUOTED, SUMMARY_AS_SUPPORT, UNCONFIRMED_FACT, RESIDENCY_NO_QUALIFIED_ENDPOINT); authority reason codes owned by P3. P9 and P10 consume both registries.
9. **retrieval.served.v1** schema = 07_P5 §2.4 (tenant in `tenantid` envelope attribute, not payload); P9 aligns.
10. **FeedbackEvent** adds target kind REVIEW_TASK and action MICRO_REVIEW_ANSWER — ACCEPT.
11. **kg.proposal.resolved.v1** = {proposal_id, decision ACCEPTED|REJECTED|MERGED|DEFERRED, resulting_assertion_ids[], graph_watermark, reviewer_role, decided_at, public_note_code (closed vocabulary)} — ACCEPT.
12. **trust_label adds TENANT_COURT_RECORD** (privately held certified copies of court records): data-only for control flow; may support RECORD_FACT claims.
13. **EvidenceBundle TPL items add privilege_class and provenance** — ACCEPT (avoids per-item P7 lookups in P8's leak check).
14. **impact-match-core.tenant_severity()** must implement P7's adjustment contract (OWN_CASE / CITED_IN_OUR_DRAFT +1; GOVERNING_PROVISION with PRE_CHANGE/SAVED −1; UNCERTAIN never downgrades) — P4 owns the library.
15. **reprocess.requested.v1** schema owner = P4 (reason enum per 06_P4 O2, incl. FEEDBACK).
16. **ConsentRecord (`cns_`)** — ACCEPT as a P7-owned core object consumed by P9 and P8 (Design Partner Program).
17. **Private certified translations** (`v1.ht-en`, authoritative=true, lawyer-attested) may support RECORD_FACT claims only; never public-law claims.
18. **judgment.expected.v1** adds optional `referenced_authorities[]` (e.g. precedents named in a reference order); P4 may raise PROVISIONAL impacts on them at any bench size when named.
19. **P9 exposure signal** (public citation in-degree/recency + distinct tenant bucket count + optional S2 aggregate) — accepted as [NOVEL — unvalidated].


## D22. Closing rulings (final lint pass)
1. **Crosswalk qualifiers (R-02):** a crosswalk row is materialised as one or more `CORRESPONDS_TO` assertions whose qualifiers carry `crosswalk_row_id` (`xrn_…`) and `group_id` (`xwg_…`, registered prefix for crosswalk groups).
2. **Anchor grammar v1.1 (R-30):** schedule fragments may nest Orders and Rules: `"sch-", unit_no, [ ".item-", unit_no | ".ord-", unit_no, [ ".rule-", unit_no ] ]` — e.g. CPC First Schedule O.VIII r.1 = `sch-1.ord-8.rule-1`; Roman numerals become Arabic; lettered rules keep their suffix (`ord-39.rule-2A`). Additive; any earlier `sch-1.item-…` anchors for such units are aliased. P1 emits it by default (feature flag retired).
3. **Topic spellings (R-37):** the 01_master §6.2 topic map is normative; phase documents have been updated to it; any older spelling is a read alias for one minor version only.
4. **Redaction acks from tenant cells (R-38):** the expected-ack set for `redaction.applied.v1` is the control-plane **cell registry** (every active D1/D2 cell and every D3/D4/D4h replica). Each cell acks once per overlay with consumer `CELL:<cell_id>` (or `REPLICA:<id>`) and `tenantid` = null. Because every cell must apply every overlay, an ack reveals nothing about any tenant's interests; P0's ledger alerts on any registered cell that misses `purge_sla`.
5. **Proposition.law_declared vs authority-core `form` (21_india):** `law_declared` (D20.7) records what the court itself said about the precedential status of its pronouncement; OBITER, SUB_SILENTIO, NON_SPEAKING_SLP and NO_MAJORITY are authority-core-internal `form` inputs derived from P1/P3 features, not `law_declared` values.


## D23. Final quality-check rulings
1. **Human-review throughput and cost (supersedes 13_cross_cutting's HITL line):** plan tier-1 review at **40–100 reviews per reviewer-day (≈800–2,000 per reviewer-month)**, not 7,000/month. At the 5M-document build this is ≈67–166 reviewer-months, ≈$47K–$233K at $700–$1,400 per reviewer-month, instead of $13.5K. The prioritisation share π (05_P3 §5.10) is the main lever, and the pilot measures real throughput (23 U-08). Reviewers are budgeted as staff in 22 §4; the compute/LLM build figures in D18/D19.1 are unchanged.
2. **Per-cell redaction ack (refines D22.4):** inside a tenant cell, the P7 cell agent emits the single `CELL:<cell_id>` ack only after every cell-local store (P7, tenant P2 indexes, P5 caches, P9-tenant, the P10 tenant stage) has applied the overlay.
3. **ResearchQuery optional fields:** `stance_target`, `requester` and the `budget.max_*` caps are optional with P5 defaults (stance_target = BOTH; caps from the tenant plan); 01_master §7.8 is normative on the defaults.
4. **Work.integrity_flags single writer = P3.** P0 signals, P1's `withdrawn_at`/`suppressed_at` and the RECALLS predicate are inputs; only P3 writes the flags.
5. **Alert de-duplication** in P10 keys on `dedupe_key` only; `subject_ids` are for display and filtering, never for de-duplication.
6. **P8 `EvalRun.residency_scores`** are keyed by endpoint class (IN endpoints vs ANY endpoints); tenants with IN_PREFERRED see both.
7. **Constitutional point-in-time (from 21 §7.1):** after a constitutional amendment is struck down, `resolve()` returns the pre-amendment expression as operative (not merely a flagged amended text); constitution application orders (e.g. under Art. 370) are a LegislativeAction source. P1 §5.7 and P3 §5.6 follow this.
8. **"Verified" grades are machine-assisted.** Some WebFetch summaries of long PDFs and judgments were wrong during QC (DPDP Rules, EBC v. D.B. Modak). Before any tier-1 output relies on a legal source, a human must check it word for word against the primary text (P3 HITL and the M0 legal opinions).

---

## Appendix A — Provisional spine v0.1 (historical; superseded where D1–D21 differ)


Every phase doc MUST use these names, IDs and schemas for its inputs/outputs. You may propose changes, but only with evidence: put them in your doc under "2.x Proposed spine changes" AND in your returned summary. Do not silently diverge.

### A. Layers
- **Public Legal Corpus (PLC)** = P0–P4. Shared, tenant-agnostic, read-only to tenants.
- **Intelligence services** = P5, P6, P8. Stateless compute over PLC + tenant layer; run inside the tenant's trust boundary when touching private data.
- **Tenant Private Layer (TPL)** = P7 (+ tenant-side P9). Per-firm stores. TPL references PLC by stable IDs only. NOTHING flows TPL → PLC except through the P9 **Privacy Gate** (consented, de-identified signals about *public* objects only).
- **Product** = P10.

### B. Document model (FRBR / Akoma-Ntoso inspired)
- **Work** = the abstract legal item: a judgment/order, an Act, a Rule, a Notification, the Constitution, an Ordinance. `work_id` = opaque, prefixed ULID: `wrk_…`.
- **Case** (proceeding) ≠ Work. `case_id` = `cas_…`: a proceeding in a forum (identified by CNR / case number / diary no). A Case has many decisions (orders/judgments). Cases link across forums via `APPEAL_OF` (trial → HC → SC). "Direct history" (affirmed/reversed) lives on case lineage; "citing treatment" (followed/overruled) lives on Work→Work/Proposition assertions.
- **Expression** = a language version and/or temporal version of a Work. `expression_key`: judgments → `lang` (+ `rev` for corrigenda), e.g. `en`, `hi`, `en.r2`; statutes/Constitution → `lang@YYYY-MM-DD` (version valid from that date).
- **Manifestation** = one concrete file from one source (PDF from sci.gov.in, HTML from India Code …). `manifestation_id` = `man_…`, points to ≥1 `raw_id`.
- **Raw blob**: `raw_id` = `sha256:<hex>` of the exact fetched bytes (content-addressed, immutable).

### C. Anchors (the unit every claim must trace to)
`anchor_id = {work_id}/{expression_key}#{fragment}`
- Judgment fragments: `p45` (para 45 as numbered in the judgment), `p45.2` (sub-para), `p45.s3` (sentence 3), `fn12` (footnote), `hdr` (cause title/coram block), `ord` (operative order). Unnumbered paras get synthetic numbers `u7` with a content-hash alignment record.
- Statute fragments: `sec-302`, `sec-302.1` (sub-s.1), `sec-302.1.a` (cl. a), `sec-302.1.a.i`, `sec-302.p1` (proviso 1), `sec-302.e1` (Explanation 1), `sch-1.item-5`, `art-21A` (Constitution), `rule-4.2`.
- Point-in-time resolution: `wrk_…#sec-302@2023-12-31` → resolves to the expression valid on that date.
- **Anchor stability**: re-parsing must preserve anchors; if structure changes, an `anchor_alias(old_anchor → new_anchor, method, confidence)` record is written. Anchors are never deleted, only tombstoned with forward pointers.
- Every anchor stores `text`, `text_hash`, page + bbox coordinates in the source manifestation (for click-to-source highlighting).

### D. Natural-key aliases (entity resolution target)
`identifier_alias(scheme, value_normalized, target_id, confidence, source, first_seen, status)`
Schemes (extend as needed): `NEUTRAL_INSC` (e.g. 2023 INSC 1), `NEUTRAL_HC` (e.g. 2023:DHC:1234 — verify formats), `SCC`, `SCR`, `AIR`, `SCALE`, `JT`, `SCC_ONLINE`, `CRILJ`, `ITR`, other reporters, `CNR`, `SC_DIARY_NO`, `CASE_NO` (court+type+number+year), `ECOURTS_URL`, `INDIA_CODE_ACT_ID`, `GAZETTE_ID`. Citation strings are facts (store the citation, never a reporter's copyrighted text/headnotes).

### E. Time model (bitemporal everywhere in PLC)
- `valid_from/valid_to` = when true in the legal world (e.g. provision version in force; overruling effective from decision date).
- `recorded_at/superseded_at` = when our system believed it (transaction time; enables audit replay: "why did we say X last Tuesday").
- Every query in P5/P6 accepts `as_of_legal_date` (law as on date D — e.g. date of cause of action) and optional `as_known_at`.

### F. Assertions (every KG edge is a reified, provenanced claim)
```
Assertion {
  assertion_id: "asr_…", subject: id, predicate: Predicate, object: id,
  qualifiers: { proposition_id?, citing_anchor?: anchor_id, cited_anchor?: anchor_id, issue_ids?: [] },
  valid_from, valid_to, recorded_at, superseded_at,
  confidence: float (calibrated probability),
  evidence: [ { anchor_id, span:[start,end], quote_hash } ],
  method: { kind: RULE|MODEL|HUMAN|IMPORT, name, version, prompt_hash? },
  review_state: MACHINE|PENDING_REVIEW|VERIFIED|REJECTED|QUARANTINED,
  impact_tier: 1|2|3   // 1 = can change legal conclusions (negative treatment, validity, crosswalk) → HITL before shown as definitive
}
```
Starter predicate set (P3 owns the final ontology): case treatment — `CITES, FOLLOWS, APPLIES, EXPLAINS, DISTINGUISHES, DOUBTS, NOT_FOLLOWED, CONFLICTS_WITH, REFERS_TO_LARGER_BENCH, OVERRULES, OVERRULES_IN_PART, DECLARES_PER_INCURIAM`; direct history — `APPEAL_OF, AFFIRMS, REVERSES, MODIFIES, SETS_ASIDE, REMANDS, STAYS, REVIEW_OF, CURATIVE_OF`; statute–judgment — `INTERPRETS, STRIKES_DOWN, READS_DOWN, UPHOLDS_VALIDITY, LEGISLATIVELY_OVERRIDDEN_BY`; statute–statute — `AMENDS, SUBSTITUTES, INSERTS, OMITS, REPEALS, SAVES, COMMENCES, MADE_UNDER, CORRESPONDS_TO` (old↔new criminal codes, with `change_type`).
- **Proposition** node (`prp_…`): a normalized legal holding extracted from ratio paragraphs; treatment can attach at proposition level (Case B overrules Case A *on proposition P2 only*).
- **AuthorityStatus** (derived, recomputed by P4): per Work and per Proposition, as-of a date: `GOOD | CAUTION | NEGATIVE | PARTIAL_NEGATIVE | UNKNOWN`, with `reason_assertion_ids[]`.

### G. Events (CloudEvents 1.0 envelope, at-least-once delivery, idempotent consumers)
Envelope: `{id (ULID), type, specversion, source (phase/component@version), time, subject, tenant_id|null, traceparent, causation_id, idempotency_key, schema_version, data}`.
| Event | Producer → Consumers | data (minimum) |
|---|---|---|
| `raw.captured.v1` | P0 → P1 | raw_id, source_id, source_record_key, url, fetched_at, http{status,etag,last_modified,content_type}, storage_uri, byte_size, source_metadata{…as published}, change_kind NEW/CHANGED/UNCHANGED/DELETED/REAPPEARED, prior_raw_id, crawl_run_id, terms_ref |
| `doc.parsed.v1` | P1 → P2, P3, P4 | parse_id, raw_ids[], work_id (resolved or provisional), case_id?, expression_key, manifestation_id, doc_type, metadata{…}, parsed_doc_uri (ParsedDocument JSON), citations[] (CitationMention), quality{ocr_conf, lang, structure_conf, needs_review}, pipeline_version |
| `doc.indexed.v1` | P2 → P4, P5 | expression ref, index_generation, chunk_ids[], targets[lexical,dense,…] |
| `graph.delta.v1` | P3 → P4, P5 caches, P8 | delta_id, assertions_added[], retracted[], superseded[], status_changes[] |
| `impact.detected.v1` | P4 → P7 (tenant-scoped fan-out), P10 | impact_id, trigger_delta_id, affected_ids[], severity, explanation with anchors |
| `matter.alert.v1` | P7 → P10 | tenant_id, matter_id, impact_id, severity, recipients, explanation |
| `feedback.recorded.v1` | P10/P6/P7 → P9 | see FeedbackEvent |
| `reprocess.requested.v1` | P4/P9/ops → P1/P2/P3 | scope selector, reason, target pipeline_version |

### H. Core API objects (synchronous)
- **ParsedDocument** (P1 output, JSON in object store): metadata; structural tree of nodes `{anchor_id, node_type, rhetorical_role?, text, page, bbox, children}`; `CitationMention{mention_id, raw_text, anchor_id (where it occurs), parsed{scheme, year, vol, page, court…}, resolved_target_id?, resolution_confidence, candidates[]}`; `StatuteMention` (act + provision + as-cited-date); entities (judges, parties, advocates); quality metrics.
- **Chunk** (P2): `{chunk_id, anchor_ids[], work_id, expression_key, node_path, text, context_header, rhetorical_role, valid_from/valid_to (statutes), embeddings refs, index_generation}`.
- **ResearchQuery** (→P5): `{query_id, tenant_id, matter_id?, text, intent?, as_of_legal_date, forum{court_id,bench_strength?}, jurisdiction_state?, client_role?, filters{}, perspective: NEUTRAL|CLIENT_SIDE, budget{latency_ms, max_items}}`.
- **EvidenceBundle** (P5 → P6): `{query_id, as_of_legal_date, issues[{issue_id, text, sub_queries[]}], items[{item_id, anchor_ids[], work_id, excerpt, context{prev,next,rhetorical_role}, retrieval_signals{lexical,dense,graph_path,fused}, authority{court_level, bench_strength, binding_on_forum: BINDING|PERSUASIVE|NOT_BINDING, status_as_of: AuthorityStatus}, stance{toward_client: SUPPORTS|ADVERSE|NEUTRAL|MIXED, confidence}, issue_ids[], why_included}], coverage{per_issue{binding_found, adverse_found, gaps}}, trace_id}`.
- **MatterContext** (P7 → P5/P6): `{tenant_id, matter_id, client_role, forum, jurisdiction_state, key_dates{cause_of_action, notice_received, filing, next_hearing}, parties[], documents[{pdoc_id, type, parsed_doc_uri}], fact_timeline[{fact_id, date, statement, anchors[] (private anchors: pdoc_id#p…)}], issues[] (lawyer-confirmed), privilege_flags, access_policy}`. Private anchors use the same fragment grammar with `pdoc_…` IDs.
- **Claim** (P6 → P8): `{claim_id, text, claim_type: LEGAL_PROPOSITION|RECORD_FACT|PROCEDURAL|STRATEGIC_OPINION, support[{anchor_id, quote, support_type: DIRECT|INFERENCE}], contrary[{anchor_id,…}], confidence, depends_on_claim_ids[]}`. STRATEGIC_OPINION must depend on grounded claims; all other types need ≥1 anchor.
- **StrategyMemo** (P6 output): sections — opponent_claims, issues, favourable_authorities, adverse_authorities(+how to distinguish), likely_opposing_arguments, counter_arguments, evidence_checklist, deadlines(computed deterministically, with statutory anchor), draft_strategy, uncertainties; each section = Claim[].
- **VerificationReport** (P8 → P6/P10): per claim `{claim_id, status: VERIFIED|PARTIAL|UNSUPPORTED|CONTRADICTED|BAD_LAW, checks[], calibrated_confidence}`; memo-level gate PASS/BLOCK.
- **FeedbackEvent** (→P9): `{feedback_id, tenant_id, matter_id?, actor_role, target{kind: CLAIM|ITEM|ASSERTION|ANSWER|ALERT, id}, action: ACCEPT|REJECT|EDIT|FLAG_WRONG_CITATION|FLAG_BAD_LAW|RELEVANT|IRRELEVANT|OUTCOME, payload, privilege_class, share_scope: TENANT_ONLY|DEIDENTIFIED_SHAREABLE}`.

### I. Provisional technology posture (challenge with evidence; P-owners decide)
- Object store S3-compatible (India region; MinIO for on-prem). System of record: PostgreSQL. Event bus + durable workflows: TBD (P0/P4). Lexical+vector+graph engines: TBD (P2/P3/P5). LLM access only via an internal **Model Gateway** with task-level contracts, eval gates and provider fallbacks (model-agnostic). All data resident in India by default.
- Every artifact carries `pipeline_version` = component@semver + model_id + prompt_hash, enabling deterministic reprocessing and lineage.

### J. Deliverable file map (cross-reference by filename)
00_executive_summary.md · 01_master_architecture.md · 02_P0_source_acquisition.md · 03_P1_ingestion_parsing.md · 04_P2_enrichment_indexing.md · 05_P3_knowledge_graph.md · 06_P4_update_propagation.md · 07_P5_retrieval_fusion.md · 08_P6_strategic_reasoning.md · 09_P7_firm_matter_workspace.md · 10_P8_verification_evaluation.md · 11_P9_feedback_learning.md · 12_P10_product_surface.md · 13_cross_cutting.md · 20_competitive_teardown.md · 21_india_specific_legal_data.md · 22_build_roadmap.md · 23_risk_register.md · 24_bibliography.md
