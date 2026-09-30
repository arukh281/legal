# Bibliography

This is the consolidated, deduplicated bibliography for the architecture blueprint. It was built mechanically from the reference fragments of the 14 research documents: the eleven phase documents (P0–P10), the cross-cutting document (XC), the competitive teardown (CT) and the India-specific legal data document (IN). Those fragments hold **721 reference entries**, which collapse to **584 unique sources**. 102 of these sources are cited by two or more documents. No source was added, removed, re-fetched or re-verified in this pass. Every verification tag was recorded by the document that cites the source. Where documents disagree, the strongest tag wins, and the weaker per-document tags are listed in Appendix B so their owners can update them. Section 9 lists every source still tagged `snippet` or `unverified`, as a follow-up verification queue. A consistency check found that all 721 fragment entries match their documents' reference lists in tag and primary URL, and that no inline reference tag in any document is missing from its fragment.

## How to read this bibliography

**Entry format.** Each source takes one numbered line: *citation text and URL* — `tag` (qualifier) · Doc refs: *citing tags* · Also at: *other URLs used for the same source*. Numbers are positions within this version of the file, so they are not stable identifiers. Documents should keep citing their own tags (for example `[P3-12]`), and the Doc refs field maps each tag back to the source.

**Verification tags** (from the research standards):

| Tag | Meaning |
|---|---|
| `verified` | The citing author fetched and read the source (sometimes the abstract only; see the qualifier). |
| `snippet` | The source was seen only in search-result snippets or via a secondary quotation. Claims resting on it should be treated as provisional. |
| `unverified` | The source is from memory or could not be confirmed. The claims it supports are marked *(unverified)* in the citing document. |

**Strongest-tag rule.** When a source is cited by several documents, it carries the strongest tag any of them recorded (verified > snippet > unverified). The short qualifier in parentheses, such as "(abstract)" or "(secondary)", comes from the entry that supplied that tag. Longer author notes are omitted here, except in §9.

**Doc refs.** These are the reference tags, across all documents, that point to the source, sorted in the order P0…P10, XC, CT, IN. The prefixes map to files as follows:

| Prefix | Document | Fragment entries |
|---|---|---:|
| P0 | `02_P0_source_acquisition.md` | 44 |
| P1 | `03_P1_ingestion_parsing.md` | 47 |
| P2 | `04_P2_enrichment_indexing.md` | 56 |
| P3 | `05_P3_knowledge_graph.md` | 65 |
| P4 | `06_P4_update_propagation.md` | 50 |
| P5 | `07_P5_retrieval_fusion.md` | 41 |
| P6 | `08_P6_strategic_reasoning.md` | 45 |
| P7 | `09_P7_firm_matter_workspace.md` | 38 |
| P8 | `10_P8_verification_evaluation.md` | 74 |
| P9 | `11_P9_feedback_learning.md` | 45 |
| P10 | `12_P10_product_surface.md` | 37 |
| XC | `13_cross_cutting.md` | 44 |
| CT | `20_competitive_teardown.md` | 56 |
| IN | `21_india_specific_legal_data.md` | 79 |
| **Total** | | **721** |

**Deduplication.** Sources were merged when any of the following held:

1. The primary URLs were identical after normalisation: scheme, `www.`, trailing slash and fragment ignored, host lower-cased, and arXiv `abs`/`html`/`pdf` and version suffixes (`v1`, `v2`, `.pdf`) collapsed to a single arXiv ID.
2. The same arXiv ID or DOI appeared, whether in a URL or in the citation text.
3. A manual identity check matched the same paper under different hosts (arXiv vs ACL Anthology), the same statutory provision on different mirrors, or the same report or standard under two URLs. These 19 merges are listed in Appendix A.

Secondary URLs inside an entry do **not** cause merges. When one reference line cites two distinct sources (a *compound* entry), its tag appears in the Doc refs of each source it cites. Appendix A lists these cases and the deliberate non-merges.

**Citation text** comes from the most complete member entry. The selection prefers the strongest tag, then the full author list, then the longest title. Parenthetical remarks inside a citation, such as figures, dates or section numbers, are the citing author's annotations of what they relied on. They are not bibliographic fields. "Also at" lists other URLs that merged entries used for the same source.

**Categories and ordering.** Each source sits in exactly one of eight categories, chosen by the nature of the document rather than by the phase that cites it. The scope of each category is given under its heading. Within a category, sources are sorted alphabetically by the first significant word of the citation, which is usually the author or organisation. Leading quotation marks, markup and "(authors not verified)" are ignored for sorting. In §3, leading court or publisher designators ("Supreme Court of India.", "Delhi High Court.", "Indian Kanoon." and the like) are also ignored, so judgments sort by party name and statutes by the name of the Act.

## Counts

| # | Category | Sources | verified | snippet | unverified |
|---:|---|---:|---:|---:|---:|
| 1 | [Academic papers — legal NLP, IR, KG, RAG, evaluation, LLM](#1-academic-papers--legal-nlp-ir-kg-rag-evaluation-llm) | 169 | 147 | 19 | 3 |
| 2 | [Indian legal NLP datasets & benchmarks](#2-indian-legal-nlp-datasets--benchmarks) | 32 | 29 | 2 | 1 |
| 3 | [Indian primary legal sources (statutes, judgments, official portals)](#3-indian-primary-legal-sources-statutes-judgments-official-portals) | 95 | 84 | 10 | 1 |
| 4 | [Government, regulatory & compliance](#4-government-regulatory--compliance) | 17 | 6 | 9 | 2 |
| 5 | [Products, vendors & pricing](#5-products-vendors--pricing) | 86 | 70 | 15 | 1 |
| 6 | [Engineering (databases, infrastructure, standards/RFCs, OSS)](#6-engineering-databases-infrastructure-standardsrfcs-oss) | 107 | 96 | 7 | 4 |
| 7 | [News, commentary & surveys](#7-news-commentary--surveys) | 53 | 37 | 16 | 0 |
| 8 | [Other](#8-other) | 25 | 20 | 5 | 0 |
| | **Total** | **584** | **489** | **83** | **12** |

| Tag | Unique sources (strongest tag) | Share | Raw fragment entries |
|---|---:|---:|---:|
| `verified` | 489 | 83.7% | 605 |
| `snippet` | 83 | 14.2% | 103 |
| `unverified` | 12 | 2.1% | 13 |
| **Total** | **584** | 100% | **721** |

The tag counts differ between raw entries and unique sources for two reasons. Duplicates collapse into one source, and 16 sources were upgraded because another document verified them (Appendix B).

**Most widely cited sources** (by number of documents citing them):

| Documents | Source | Doc refs |
|---:|---|---|
| 12 | Magesh, V., Surani, F., Dahl, M., Suzgun… "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools" | P1-38, P2-50, P3-1, P4-1, P5-6, P6-1, P8-1, P9-21, P10-20, XC-35, CT-38, IN-70 |
| 6 | Joshi, A., Paul, S., Sharma, A., Goyal, … "IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning" | P1-22, P2-7, P3-30, P5-10, P8-46, XC-18 |
| 4 | Government of India. Bharatiya Sakshya A… "Professional communications" | P7-8, P8-69, XC-43, IN-61 |
| 4 | Central Board of Dawoodi Bohra Community v. State of Maharashtra, (2005) 2 SCC 673 (SC, 5… | P3-51, P4-45, P5-36, IN-12 |
| 4 | Digital Personal Data Protection Act 2023, s.3(c)(ii) (mirror text; PRS copy of Act). | P0-23, P8-67, XC-42, IN-58 |
| 4 | Digital Personal Data Protection Act, 2023, s.17 (s.17(1)(a) legal-claims exemption;… | P7-3, P8-68, P9-22, IN-57 |
| 4 | Supreme Court of India. Eastern Book Company & Ors v. D.B. Modak & Anr, (2008) 1 SCC 1;… | P0-18, P2-28, CT-49, IN-3 |
| 4 | Supreme Court Observer "In re: Summoning Advocates who give Legal Opinion or Represent Parties during Investigation of Cases and Related Issues" | P7-9, P8-70, P9-25, IN-62 |
| 4 | Department of Official Language, GoI "The Official Languages Act, 1963" | P1-46, P5-41, P10-36, IN-11 |
| 4 | Vals AI "Vals Legal AI Report (VLAIR): Legal Research" | P6-3, P8-10, P10-21, CT-39 |

## 1. Academic papers — legal NLP, IR, KG, RAG, evaluation, LLM

*Scope:* Peer-reviewed papers, preprints and academic technical reports in NLP, IR, knowledge graphs, RAG, evaluation, LLMs, HCI-for-AI, privacy/ML security and CS systems. Papers whose subject is Indian legal text are in §2. (169 sources.)

1. Abadi, M., Chu, A., Goodfellow, I., McMahan, H.B., Mironov, I., Talwar, K., Zhang, L. "Deep Learning with Differential Privacy." ACM CCS, 2016. https://arxiv.org/abs/1607.00133 — `verified` · Doc refs: P9-41
2. Agarwal, A., Zaitsev, I., Wang, X., Li, C., Najork, M., Joachims, T. "Estimating Position Bias without Intrusive Interventions." WSDM, 2019. https://arxiv.org/abs/1812.05161 — `verified` (review: URL corrected from arXiv 1806.03555, a different paper) · Doc refs: P9-2
3. Aggarwal, D., Gupta, V., Kunchukuttan, A. "IndicXNLI: Evaluating Multilingual Inference for Indian Languages." EMNLP 2022; arXiv:2204.08776. https://arxiv.org/abs/2204.08776 — `verified` · Doc refs: P8-60
4. Amin, K., Bie, A., Kong, W., Kurakin, A., Ponomareva, N., Syed, U., Terzis, A., Vassilvitskii, S. (Google). "Private prediction for large-scale synthetic text generation." 2024; Google Research blog "Generating synthetic data with differentially private LLM inference," 2025. https://arxiv.org/abs/2407.12108 ; https://research.google/blog/generating-synthetic-data-with-differentially-private-llm-inference/ — `verified` (arXiv abstract) · Doc refs: P9-30
5. Angelopoulos, A.N., Bates, S., Fannjiang, C., Jordan, M.I., Zrnic, T. "Prediction-Powered Inference." Science 2023; arXiv:2301.09633. https://arxiv.org/abs/2301.09633 — `verified` (abstract) · Doc refs: P8-41
6. (authors not verified). "Are Large Language Models Effective Knowledge Graph Constructors?" arXiv 2510.11297, 2025. https://arxiv.org/abs/2510.11297 — `snippet` · Doc refs: P3-12
7. Arulanandam, R., de Silva, N. "Section-Weighted Hybrid Approach for Legal Case Retrieval." arXiv 2606.03138, 2026. https://arxiv.org/abs/2606.03138 — `verified` (abstract) · Doc refs: P5-5
8. Bansal, G., Wu, T., Zhou, J., Fok, R., Nushi, B., Kamar, E., Ribeiro, M.T., Weld, D.S. "Does the Whole Exceed its Parts? The Effect of AI Explanations on Complementary Team Performance." CHI 2021. https://arxiv.org/abs/2006.14779 — `verified` · Doc refs: P10-8
9. Beurer-Kellner, L. et al. "Design Patterns for Securing LLM Agents against Prompt Injections." arXiv:2506.08837, 2025. https://arxiv.org/abs/2506.08837 — `verified` · Doc refs: P7-22, XC-33
10. Bommarito, M., Katz, D.M., Detterman, E. "LexNLP: Natural language processing and information extraction for legal and regulatory texts." 2018. https://arxiv.org/abs/1806.03688 — `unverified` (not cited in text; background) · Doc refs: P1-43
11. Bourtoule, L. et al. "Machine Unlearning." IEEE S&P, 2021. https://arxiv.org/abs/1912.03817 — `snippet` · Doc refs: P9-31
12. Bruch, S., Gai, S., Ingber, A. "An Analysis of Fusion Functions for Hybrid Retrieval." ACM TOIS 42(1), 2023. https://arxiv.org/abs/2210.11934 (DOI 10.1145/3596512) — `verified` (abstract) · Doc refs: P5-2
13. Budiu, M., McSherry, F., Ryzhyk, L., Tannen, V. "DBSP: Automatic Incremental View Maintenance for Rich Query Languages." arXiv 2203.16684, 2022 (VLDB 2023 publication unverified). https://arxiv.org/abs/2203.16684 — `verified` (abstract) · Doc refs: P4-22
14. Burges, C.J.C. "From RankNet to LambdaRank to LambdaMART: An Overview." Microsoft Research Technical Report MSR-TR-2010-82, 2010. — `unverified` (foundational; not fetched) · Doc refs: P5-38
15. Butler, A.-R., Butler, U. "Legal RAG Bench: an end-to-end benchmark for legal RAG." arXiv:2603.01710, 2026. https://arxiv.org/abs/2603.01710 — `verified` · Doc refs: P2-4, P8-7
16. Butler, U., Butler, A.-R., Malec, A.L. "The Massive Legal Embedding Benchmark (MLEB)." arXiv:2510.19365, 2025. https://arxiv.org/html/2510.19365v1 — `verified` · Doc refs: P2-3
17. Cedar team, Amazon Web Services. "How We Built Cedar: A Verification-Guided Approach." FSE 2024 (Industry) / arXiv:2407.01688. https://arxiv.org/abs/2407.01688 — `verified` · Doc refs: P7-31
18. Cemri, M. et al. "Why Do Multi-Agent LLM Systems Fail?" arXiv 2503.13657 (v3, 26 Oct 2025). https://arxiv.org/abs/2503.13657 — `verified` · Doc refs: P6-5
19. Chalkidis, I. et al. "LexGLUE: A Benchmark Dataset for Legal Language Understanding in English." ACL 2022; arXiv:2110.00976. https://arxiv.org/abs/2110.00976 — `verified` · Doc refs: P8-49
20. Chapelle, O., Joachims, T., Radlinski, F., Yue, Y. "Large-scale Validation and Analysis of Interleaved Search Evaluation." ACM TOIS 30(1), Article 6, 2012. https://doi.org/10.1145/2094072.2094078 ; https://www.cs.cornell.edu/people/tj/publications/chapelle_etal_12a.pdf — `verified` · Doc refs: P9-3
21. Chen, G. et al. "AgentCourt: Simulating Court with Adversarial Evolvable Lawyer Agents." 2024. https://arxiv.org/abs/2408.08089 — `verified` · Doc refs: P6-16
22. Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., Liu, Z. "M3-Embedding (BGE-M3)." arXiv:2402.03216, 2024. https://arxiv.org/abs/2402.03216 — `verified` · Doc refs: P2-12
23. Chen, L., Zaharia, M., Zou, J. "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance." arXiv:2305.05176, 2023. https://arxiv.org/abs/2305.05176 — `verified` · Doc refs: XC-28
24. Chen, T., Wang, H., Chen, S., et al. "Dense X Retrieval: What Retrieval Granularity Should We Use?" arXiv:2312.06648, 2023/2024. https://arxiv.org/abs/2312.06648 — `verified` · Doc refs: P2-21
25. Chen, Y. et al. "Is Conformal Factuality for RAG-based LLMs Robust? Novel Metrics and Systematic Insights." arXiv:2603.16817, 2026. https://arxiv.org/abs/2603.16817 — `verified` (abstract) · Doc refs: P8-28
26. Chen, Z., Gul, M.O., Chen, Y., Geng, G., Wu, A., Artzi, Y. "Retrospective Learning from Interactions" (RESPECT). arXiv, 2024. https://arxiv.org/abs/2410.13852 — `verified` · Doc refs: P9-44
27. Chen, Z., Zhang, Q., Xiang, Z., Wei, Z., Gao, L., Huang, X., Zhang, Z., Su, J. "LegalGraphRAG: Multi-Agent Graph Retrieval-Augmented Generation for Reliable Legal Reasoning." ACL 2026 (arXiv 2605.28120). https://arxiv.org/abs/2605.28120 — `verified` · Doc refs: P3-2
28. Cherian, J.J., Gibbs, I., Candès, E.J. "Large language model validity via enhanced conformal prediction methods." arXiv:2406.09714, 2024. https://arxiv.org/abs/2406.09714 — `verified` · Doc refs: P8-27
29. Chlapanis, O.S., Galanis, D., Aletras, N., Androutsopoulos, I. "GreekBarBench: A Challenging Benchmark for Free-Text Legal Reasoning and Citations." arXiv:2505.17267, 2025. https://arxiv.org/abs/2505.17267 — `verified` (abstract) · Doc refs: P8-39
30. Chowdhury, S.B.R., Choromanski, K., Sehanobish, A., Dubey, A., Chaturvedi, S. "Towards Scalable Exact Machine Unlearning Using Parameter-Efficient Fine-Tuning" (S3T). ICLR, 2025. https://arxiv.org/abs/2406.16257 — `verified` · Doc refs: P9-32
31. Cohen, R., Biran, E., Yoran, O., Globerson, A., Geva, M. "Evaluating the Ripple Effects of Knowledge Editing in Language Models." TACL, 2024; arXiv 2307.12976. https://arxiv.org/abs/2307.12976 — `verified` · Doc refs: P4-6
32. Cormack, G.V., Clarke, C.L.A., Büttcher, S. "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods." SIGIR 2009. http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf — `snippet` (PDF not parseable; formula and k=60 confirmed via [P5-3]) · Doc refs: P5-1
33. Cormack, G.V., Grossman, M.R. "Evaluation of Machine-Learning Protocols for Technology-Assisted Review in Electronic Discovery." SIGIR, 2014; and "Autonomy and Reliability of Continuous Active Learning for Technology-Assisted Review," 2015. https://plg2.cs.uwaterloo.ca/~gvcormac/calstudy/study/sigir2014-cormackgrossman.pdf ; https://arxiv.org/abs/1504.06868 — `verified` (2015 abstract); SIGIR 2014 comparison snippet · Doc refs: P9-12
34. Cushman, J., Dahl, M., Lissner, M. "eyecite: A Tool for Parsing Legal Citations." Journal of Open Source Software, 2021. https://joss.theoj.org/papers/10.21105/joss.03617 — `verified` (metadata) · Doc refs: P1-26, P3-22
35. Cymbler, R., Guez, D., Fabre, L. "Temporal Misgrounding in Legal RAG: A Versioned-Corpus Benchmark for French Tax Law." arXiv 2608.09393, 2026. https://arxiv.org/abs/2608.09393 — `verified` (abstract) · Doc refs: P4-2
36. Dahl, M., Magesh, V., Suzgun, M., Ho, D.E. "Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models." 2024. https://arxiv.org/abs/2401.01301 — `verified` · Doc refs: P6-2, P8-2
37. Dawid, A.P., Skene, A.M. "Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm." Applied Statistics, 1979. — `unverified` · Doc refs: P9-40
38. de Martim, H. "An Ontology-Driven Graph RAG for Legal Norms: A Structural, Temporal, and Deterministic Approach" (orig. "Graph RAG for Legal Norms: A Hierarchical, Temporal and Deterministic Approach"). arXiv 2505.00039, 2025. https://arxiv.org/abs/2505.00039 — `verified` (abstract) · Doc refs: P3-4, P4-5, P5-20
39. de Martim, H. "Beyond Probabilistic Similarity: Structural, Temporal, and Causal Limitations of Retrieval-Augmented Generation in the Legal Domain." arXiv 2606.09724, 2026. https://arxiv.org/abs/2606.09724 — `verified` (abstract) · Doc refs: P4-4
40. Debenedetti, E. et al. "Defeating Prompt Injections by Design" (CaMeL). 2025. https://arxiv.org/abs/2503.18813 — `verified` · Doc refs: P6-17, P7-21, XC-34
41. Demir, M.M., Canbaz, M.A. "Validate Your Authority: Benchmarking LLMs on Multi-Label Precedent Treatment Classification." NLLP 2025; arXiv:2605.17691. https://arxiv.org/abs/2605.17691 — `verified` (abstract) · Doc refs: P3-13, P8-63
42. Deode, S., Gadre, J., Kajale, A., Joshi, A., Joshi, R. "L3Cube-IndicSBERT." arXiv:2304.11434, 2023. https://arxiv.org/abs/2304.11434 — `verified` · Doc refs: P2-49
43. Dong, Y. et al. "XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models." 2024. https://arxiv.org/abs/2411.15100 — `verified` · Doc refs: P6-20
44. "dots.ocr: Multilingual Document Layout Parsing in a Single Vision-Language Model." arXiv:2512.02498, 2025. https://arxiv.org/abs/2512.02498 — `snippet` · Doc refs: P1-6
45. Doyle, J. "A Truth Maintenance System." Artificial Intelligence 12(3), 1979; de Kleer, J. "An Assumption-based TMS." Artificial Intelligence 28(2), 1986. https://en.wikipedia.org/wiki/Reason_maintenance — `snippet` (via P3 [P3-39]) · Doc refs: P4-26
46. Du, Y., Li, S., Torralba, A., Tenenbaum, J.B., Mordatch, I. "Improving Factuality and Reasoning in Language Models through Multiagent Debate." 2023. https://arxiv.org/abs/2305.14325 — `verified` · Doc refs: P6-9
47. Edge, D. et al. "From Local to Global: A Graph RAG Approach to Query-Focused Summarization." arXiv 2404.16130, 2024/2025. https://arxiv.org/abs/2404.16130 — `verified` · Doc refs: P3-6
48. Enguehard, J. et al. "LeMAJ (Legal LLM-as-a-Judge): Bridging Legal Reasoning and LLM Evaluation." arXiv:2510.07243, 2025. https://arxiv.org/abs/2510.07243 — `verified` (abstract) · Doc refs: P8-38
49. Es, S., James, J., Espinosa-Anke, L., Schockaert, S. "Ragas: Automated Evaluation of Retrieval Augmented Generation." EACL 2024 (demo); arXiv:2309.15217. https://arxiv.org/abs/2309.15217 — `verified` · Doc refs: P8-19
50. Etcheverry, M., Real, T., Chavallard, P. "Algorithm for Automatic Legislative Text Consolidation." NLLP 2024. https://aclanthology.org/2024.nllp-1.13 — `verified` · Doc refs: P1-32, IN-74
51. Ethayarajh, K., Xu, W., Muennighoff, N., Jurafsky, D., Kiela, D. "KTO: Model Alignment as Prospect Theoretic Optimization." ICML, 2024. https://arxiv.org/abs/2402.01306 — `verified` · Doc refs: P9-6
52. Fan, Y. et al. "LEXam: Benchmarking Legal Reasoning on 340 Law Exams." arXiv:2505.12864, 2025. https://arxiv.org/abs/2505.12864 — `verified` · Doc refs: P8-54
53. Faraz, A., Kolla, R., Kulkarni, A., Agarwal, S. "Designing Production-Scale OCR for India: Multilingual and Domain-Specific Systems." arXiv:2602.16430, 2026. https://arxiv.org/abs/2602.16430 — `verified` · Doc refs: P1-8
54. Farquhar, S., Kossen, J., Kuhn, L., Gal, Y. "Detecting hallucinations in large language models using semantic entropy." Nature 630, 2024. https://www.nature.com/articles/s41586-024-07421-0 — `snippet` (referenced in [P8-24]) · Doc refs: P8-23
55. Gala, J., Chitale, P.A., et al. "IndicTrans2." TMLR 2023. https://arxiv.org/abs/2305.16307 — `verified` · Doc refs: P1-37, P2-48, IN-69 · Also at: https://github.com/AI4Bharat/IndicTrans2
56. Gao, G., Taymanov, A., Salinas, E., Mineiro, P., Misra, D. "Aligning LLM Agents by Learning Latent Preference from User Edits" (PRELUDE/CIPHER). NeurIPS, 2024. https://arxiv.org/abs/2404.15269 — `verified` · Doc refs: P9-7
57. Gao, L., Ma, X., Lin, J., Callan, J. "Precise Zero-Shot Dense Retrieval without Relevance Labels" (HyDE). ACL 2023 / arXiv 2212.10496. https://arxiv.org/abs/2212.10496 — `verified` · Doc refs: P5-26
58. Gao, T., Yen, H., Yu, J., Chen, D. "Enabling Large Language Models to Generate Text with Citations" (ALCE). EMNLP 2023; arXiv:2305.14627. https://arxiv.org/abs/2305.14627 — `verified` · Doc refs: P8-21
59. Gardella, M., Mariño, C., Belzarena, D., Ramírez, I., Randall, G., Morel, J.-M. "When Low CER is Not Enough: An Analysis of Hallucinations in Vision-Language OCR Systems on Historical Uruguayan Documents." arXiv:2607.24077, 2026. https://arxiv.org/abs/2607.24077 — `verified` · Doc refs: P1-14
60. Ghanem, H., Cruz, C. "Enhancing Knowledge Graph Construction: Evaluating with Emphasis on Hallucination, Omission, and Graph Similarity Metrics." arXiv 2502.05239, 2025. https://arxiv.org/abs/2502.05239 — `verified` (abstract) · Doc refs: P3-11
61. Greshake, K. et al. "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection." arXiv:2302.12173, 2023. https://arxiv.org/abs/2302.12173 — `verified` · Doc refs: XC-32
62. Gu, C., Li, X.L., Kuditipudi, R., Liang, P., Hashimoto, T. "Auditing Prompt Caching in Language Model APIs." arXiv:2502.07776, 2025. https://arxiv.org/abs/2502.07776 — `verified` · Doc refs: P7-23
63. Guha, N. et al. "LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models." arXiv 2308.11462, 2023. https://arxiv.org/abs/2308.11462 — `verified` · Doc refs: P3-16, P8-47
64. Guo, C., Pleiss, G., Sun, Y., Weinberger, K.Q. "On Calibration of Modern Neural Networks." ICML 2017; arXiv:1706.04599. https://arxiv.org/abs/1706.04599 — `verified` · Doc refs: P8-34
65. Guo, Z., Xia, L., Yu, Y., Ao, T., Huang, C. "LightRAG: Simple and Fast Retrieval-Augmented Generation." arXiv 2410.05779, 2024/2025. https://arxiv.org/abs/2410.05779 — `verified` · Doc refs: P3-8
66. Gutiérrez, B.J., Shu, Y., Qi, W., Zhou, S., Su, Y. "From RAG to Memory: Non-Parametric Continual Learning for Large Language Models" (HippoRAG 2). arXiv 2502.14802, 2025. https://arxiv.org/abs/2502.14802 — `verified` (abstract) · Doc refs: P3-9, P5-19
67. Günther, M., Mohr, I., Williams, D.J., Wang, B., Xiao, H. "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models." arXiv:2409.04701, 2024. https://arxiv.org/abs/2409.04701 — `verified` · Doc refs: P2-2
68. Han, J. et al. "RAG Meets Temporal Graphs: Time-Sensitive Modeling and Retrieval for Evolving Knowledge." arXiv 2510.13590, 2025. https://arxiv.org/abs/2510.13590 — `snippet` · Doc refs: P4-46
69. Hellyer, P. "Evaluating Shepard's, KeyCite, and BCite for Case Validation Accuracy." Law Library Journal 110(4), 2018. https://scholarship.law.wm.edu/libpubs/131/ — `verified` · Doc refs: P3-14, P4-9
70. Hines, K. et al. "Defending Against Indirect Prompt Injection Attacks With Spotlighting." 2024. https://arxiv.org/abs/2403.14720 — `verified` · Doc refs: P6-18, P7-20
71. Hou, A.B., et al. "CLERC: A Dataset for Legal Case Retrieval and Retrieval-Augmented Analysis Generation." Findings of NAACL 2025. https://arxiv.org/abs/2406.17186 — `verified` · Doc refs: P5-16, P8-58
72. Jayatilleke, N., de Silva, N. "Zero-shot OCR Accuracy of Low-Resourced Languages: A Comparative Analysis on Sinhala and Tamil." RANLP 2025 (Document AI best on Tamil, CER 0.78%; Surya best on Sinhala). https://aclanthology.org/2025.ranlp-1.56 — `verified` · Doc refs: P1-16
73. Jiang, R., Chiappa, S., Lattimore, T., György, A., Kohli, P. "Degenerate Feedback Loops in Recommender Systems." AIES, 2019. https://arxiv.org/abs/1902.10730 — `verified` (abstract); specific remedies snippet · Doc refs: P9-4
74. Jiang, Z. et al. "Core: Robust Factual Precision with Informative Sub-Claim Identification." arXiv:2407.03572, 2024. https://arxiv.org/abs/2407.03572 — `verified` · Doc refs: P8-17
75. Jiang, Z., Liu, A., Van Durme, B. "Conformal Linguistic Calibration: Trading-off between Factuality and Specificity." arXiv:2502.19110, 2025. https://arxiv.org/abs/2502.19110 — `verified` (abstract) · Doc refs: P8-31
76. Jin, B., Yoon, J., Han, J., Arık, S.Ö. "Long-Context LLMs Meet RAG: Overcoming Challenges for Long Inputs in RAG." ICLR 2025. https://arxiv.org/abs/2410.05983 — `snippet` · Doc refs: P5-22
77. Joachims, T., Swaminathan, A., Schnabel, T. "Unbiased Learning-to-Rank with Biased Feedback." WSDM, 2017 (Best Paper Award). https://arxiv.org/abs/1608.04468 ; https://www.cs.cornell.edu/people/tj/ — `verified` · Doc refs: P9-1
78. Joren, H., et al. "Sufficient Context: A New Lens on Retrieval Augmented Generation Systems." ICLR 2025. https://arxiv.org/abs/2411.06037 — `verified` (abstract; 2–10% selective-generation gain); ICLR venue — snippet · Doc refs: P5-24
79. Kadavath, S. et al. "Language Models (Mostly) Know What They Know." arXiv:2207.05221, 2022. https://arxiv.org/abs/2207.05221 — `verified` · Doc refs: P8-33
80. Kairouz, P., McMahan, H.B., Avent, B. et al. "Advances and Open Problems in Federated Learning." Foundations and Trends in Machine Learning, 2021. https://arxiv.org/abs/1912.04977 — `verified` · Doc refs: P9-43
81. Karp, M. et al. "LLM-as-a-Judge is Bad, Based on AI Attempting the Exam Qualifying for the Member of the Polish National Board of Appeal." arXiv:2511.04205, 2025. https://arxiv.org/abs/2511.04205 — `verified` (abstract) · Doc refs: P8-40
82. Kim, S.S.Y., Liao, Q.V., Vorvoreanu, M., Ballard, S., Vaughan, J.W. "'I'm Not Sure, But…': Examining the Impact of Large Language Models' Uncertainty Expression on User Reliance and Trust." FAccT 2024. https://arxiv.org/abs/2405.00623 — `verified` · Doc refs: P8-44, P10-10
83. Koreeda, Y., Manning, C.D. "ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts." Findings of EMNLP 2021; arXiv:2110.01799. https://arxiv.org/abs/2110.01799 — `verified` · Doc refs: P8-62
84. Kossen, J. et al. "Semantic Entropy Probes: Robust and Cheap Hallucination Detection in LLMs." arXiv:2406.15927, 2024. https://arxiv.org/abs/2406.15927 — `verified` · Doc refs: P8-24
85. Kuhn, L., Gal, Y., Farquhar, S. "Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation." ICLR 2023; arXiv:2302.09664. https://arxiv.org/abs/2302.09664 — `verified` · Doc refs: P8-25
86. Kusupati, A., et al. "Matryoshka Representation Learning." arXiv:2205.13147, 2022. https://arxiv.org/abs/2205.13147 — `verified` · Doc refs: P2-44
87. Lassance, C., Déjean, H., Formal, T., Clinchant, S. "SPLADE-v3: New baselines for SPLADE." arXiv:2403.06789, 2024. https://arxiv.org/abs/2403.06789 — `verified` · Doc refs: P2-46
88. Li, H., Ai, Q., Chen, J., et al. "SAILER: Structure-aware Pre-trained Language Model for Legal Case Retrieval." SIGIR 2023. https://arxiv.org/abs/2304.11370 — `verified` · Doc refs: P2-47
89. Li, H., Chen, J., Yang, J. et al. "LegalAgentBench: Evaluating LLM Agents in Legal Domain." arXiv 2412.17259, 2024. https://arxiv.org/abs/2412.17259 — `verified` (abstract) · Doc refs: P6-15
90. Li, Z., Li, C., Zhang, M., Mei, Q., Bendersky, M. "Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach." EMNLP 2024 (Industry). https://arxiv.org/abs/2407.16833 — `verified` · Doc refs: P5-23
91. Lin, Z. et al. "Domain-Shift-Aware Conformal Prediction for Large Language Models." arXiv:2510.05566, 2025. https://arxiv.org/abs/2510.05566 — `verified` (abstract) · Doc refs: P8-29
92. Liu, N.F., et al. "Lost in the Middle: How Language Models Use Long Contexts." TACL 12, 2024. https://aclanthology.org/2024.tacl-1.9/ — `snippet` · Doc refs: P5-21
93. Liu, P., Stammbach, D., Henderson, P. "Who Checks the Citations? Benchmarking Legal Hallucination Detection" (LePhantomCite). arXiv:2606.21155, 2026. https://arxiv.org/abs/2606.21155 — `verified` · Doc refs: P8-3
94. Liu, Y., Zhang, M.J.Q., Choi, E. "User Feedback in Human-LLM Dialogues: A Lens to Understand Users But Noisy as a Learning Signal." EMNLP, 2025. https://arxiv.org/abs/2507.23158 — `verified` · Doc refs: P9-8
95. LLM-AggreFact Leaderboard (11 grounded-factuality datasets; balanced accuracy). Accessed 30 Sep 2026. https://llm-aggrefact.github.io/ — `verified` · Doc refs: P8-14
96. Louis, A., van Dijck, G., Spanakis, G. "Know When to Fuse: Investigating Non-English Hybrid Retrieval in the Legal Domain." arXiv 2409.01357, 2024. https://arxiv.org/abs/2409.01357 — `verified` · Doc refs: P5-4
97. Magesh, V., Surani, F., Dahl, M., Suzgun, M., Manning, C.D., Ho, D.E. "Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools." Journal of Empirical Legal Studies, 2025 (arXiv 2405.20362). https://arxiv.org/abs/2405.20362 — `verified` (P3 session [P3-1]) · Doc refs: P1-38, P2-50, P3-1, P4-1, P5-6, P6-1, P8-1, P9-21, P10-20, XC-35, CT-38, IN-70 · Also at: https://law.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools
98. Mahari, R., et al. "LePaRD: A Large-Scale Dataset of Judicial Citations to Precedent." ACL 2024. https://aclanthology.org/2024.acl-long.532/ — `verified` (abstract) · Doc refs: P5-17
99. Manku, G.S., Jain, A., Das Sarma, A. "Detecting Near-Duplicates for Web Crawling." WWW 2007, pp. 141–150. https://research.google/pubs/detecting-near-duplicates-for-web-crawling/ — `verified` · Doc refs: P0-30
100. Medvedeva, M., McBride, P. "Legal Judgment Prediction: If You Are Going to Do It, Do It Right." NLLP Workshop, 2023. https://aclanthology.org/2023.nllp-1.9 — `verified` · Doc refs: P9-36
101. Merola, C., Singh, J. "Reconstructing Context: Evaluating Advanced Chunking Strategies for Retrieval-Augmented Generation." ECIR 2025 KEIR Workshop. https://arxiv.org/abs/2504.19754 — `verified` · Doc refs: P2-23
102. Miller, E. "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations." arXiv:2411.00640, 2024. https://arxiv.org/abs/2411.00640 — `verified` (abstract) · Doc refs: P8-42
103. Min, S. et al. "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation." EMNLP 2023; arXiv:2305.14251. https://arxiv.org/abs/2305.14251 — `verified` · Doc refs: P8-15
104. Mohri, C., Hashimoto, T. "Language Models with Conformal Factuality Guarantees." ICML 2024; arXiv:2402.10978. https://arxiv.org/abs/2402.10978 — `verified` · Doc refs: P8-26
105. Mokhov, A., Mitchell, N., Peyton Jones, S. "Build Systems à la Carte." Proc. ACM Program. Lang. (ICFP), 2018. https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems.pdf — `snippet` · Doc refs: P4-25
106. Morris, J.X., Kuleshov, V., Shmatikov, V., Rush, A.M. "Text Embeddings Reveal (Almost) As Much As Text." EMNLP 2023. https://arxiv.org/abs/2310.06816 — `verified` · Doc refs: P2-54, P7-24
107. Ngo, T.-H. et al. "NOWJ@COLIEE 2026: Adaptive Pipelines for Legal Retrieval and Reasoning" (all five COLIEE 2026 tasks). arXiv:2607.16603, 2026; Nguyen, H.-T. et al. "NOWJ@COLIEE 2025…Legal Retrieval and Entailment." arXiv:2509.08025. https://arxiv.org/abs/2607.16603 — `verified` (abstract) · Doc refs: P5-15, P8-57 · Also at: https://www.catalyzex.com/paper/nowj-coliee-2025-a-multi-stage-framework
108. Nguyen, T.-M. et al. "L-MAD: A Systematic Evaluation of Multi-Agent Debate Structures in Legal Reasoning." AI4Law@ICML 2026. https://arxiv.org/abs/2607.09099 — `verified` (abstract) · Doc refs: P6-12
109. Niu, C. et al. "RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models." ACL 2024; arXiv:2401.00396. https://arxiv.org/abs/2401.00396 — `verified` · Doc refs: P8-22
110. Nyffenegger, A., Stürmer, M., Niklaus, J. "Anonymity at Risk? Assessing Re-Identification Capabilities of Large Language Models in Court Decisions." Findings of NAACL, 2024. https://arxiv.org/abs/2308.11103 — `verified` · Doc refs: P9-29
111. Ong, I. et al. "RouteLLM: Learning to Route LLMs with Preference Data." arXiv:2406.18665, 2024. https://arxiv.org/abs/2406.18665 — `verified` · Doc refs: XC-29
112. Ongris, J.G., Darari, F., Tobing, B.C.L., Faisal, D.R., Lee, O. "Benchmarking KG-based RAG Systems: A Case Study of Legal Documents." CEUR-WS Vol-4079, 2025 (HippoRAG 2, Nano GraphRAG, LightRAG, LlamaIndex; EU Directives + Indonesian Government Regulations). https://ceur-ws.org/Vol-4079/paper6.pdf (abstract: https://dara.ui.ac.id/research-output/7409d879-ce06-4519-a24b-8da1fdd90d42) — `verified` · Doc refs: P3-5
113. OpenDataLab. "MinerU2.5: A Decoupled Vision-Language Model for Efficient High-Resolution Document Parsing." arXiv:2509.22186, 2025. https://arxiv.org/abs/2509.22186 — `snippet` · Doc refs: P1-5
114. Ouyang, L. et al. "OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations." CVPR 2025. https://arxiv.org/abs/2412.07626 — `snippet` · Doc refs: P1-3
115. Ovcharov, V. "Citation Grounding Measures the Oracle: Graph Coverage Determines Reported LLM Hallucination Rates in Law." arXiv:2606.00898, 2026. https://arxiv.org/abs/2606.00898 — `verified` (abstract; Ukrainian legal queries) · Doc refs: P8-6
116. PaddlePaddle team (Baidu). "PaddleOCR-VL: Boosting Multilingual Document Parsing via a 0.9B Ultra-Compact Vision-Language Model." arXiv:2510.14528, 2025. https://arxiv.org/abs/2510.14528 — `verified` (abstract) · Doc refs: P1-4
117. Pang, R. et al. "Zanzibar: Google's Consistent, Global Authorization System." USENIX ATC 2019. https://www.usenix.org/conference/atc19/presentation/pang — `verified` · Doc refs: P7-29
118. Panickssery, A., Bowman, S.R., Feng, S. "LLM Evaluators Recognize and Favor Their Own Generations." NeurIPS 2024; arXiv:2404.13076. https://arxiv.org/abs/2404.13076 — `verified` · Doc refs: P8-36
119. Piccioli, G., Fidelangeli, A., Santin, P., Vivo, P. "From Judgments to Issues: Structured Extraction of Legal Reasoning with Citation-Hallucination Control." arXiv:2607.03325, 2026. https://arxiv.org/abs/2607.03325 — `verified` (abstract) · Doc refs: P8-66
120. Pipitone, N., Houir Alami, G. "LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain." arXiv:2408.10343, 2024. https://arxiv.org/abs/2408.10343 — `verified` · Doc refs: P2-20, P5-8, P8-48
121. Poznanski, J. et al. "olmOCR: Unlocking Trillions of Tokens in PDFs with Vision Language Models." arXiv:2502.18443, 2025. https://arxiv.org/abs/2502.18443 — `verified` · Doc refs: P1-2, XC-25
122. Pradeep, R., Sharifymoghaddam, S., Lin, J. "RankZephyr: Effective and Robust Zero-Shot Listwise Reranking is a Breeze!" arXiv 2312.02724, 2023. https://arxiv.org/abs/2312.02724 — `snippet` · Doc refs: P5-32
123. Prior, M., Hof, A., Wais, N., Grabmair, M. "Risks and Limits of Automatic Consolidation of Statutes." NLLP 2025 (German federal law; 908 amendment-law pairs; 93–99% similarity; 50.3% / 20.51% exact match). https://aclanthology.org/2025.nllp-1.29 — `verified` · Doc refs: P1-33, IN-74
124. Prior, M., Schultz, A., Grabmair, M. "Asking For An Old Friend: Diagnosing and Mitigating Temporal Failure Modes in LLM-based Statutory Question Answering." ICAIL 2026; arXiv 2605.23497. https://arxiv.org/abs/2605.23497 — `verified` (abstract) · Doc refs: P4-3
125. Qu, R., Tu, R., Bao, F. "Is Semantic Chunking Worth the Computational Cost?" arXiv:2410.13070, 2024. https://arxiv.org/abs/2410.13070 — `verified` · Doc refs: P2-19
126. Qwen Team. "Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models." arXiv 2506.05176, 2025; model cards. https://arxiv.org/abs/2506.05176 ; https://huggingface.co/Qwen/Qwen3-Reranker-4B — `verified` · Doc refs: P2-11, P5-27
127. Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C.D., Finn, C. "Direct Preference Optimization: Your Language Model is Secretly a Reward Model." arXiv/NeurIPS, 2023. https://arxiv.org/abs/2305.18290 — `verified` · Doc refs: P9-5
128. Rando, J., Tramèr, F. "Universal Jailbreak Backdoors from Poisoned Human Feedback." ICLR, 2024. https://arxiv.org/abs/2311.14455 — `verified` · Doc refs: P9-13
129. Rasmussen, P., Paliychuk, P., Beauvais, T., Ryan, J., Chalef, D. "Zep: A Temporal Knowledge Graph Architecture for Agent Memory." arXiv 2501.13956, 2025. https://arxiv.org/abs/2501.13956 — `verified` · Doc refs: P3-10
130. Ratner, A., Bach, S.H., Ehrenberg, H., Fries, J., Wu, S., Ré, C. "Snorkel: Rapid Training Data Creation with Weak Supervision." VLDB 2018 (arXiv 1711.10160). https://arxiv.org/abs/1711.10160 — `verified` · Doc refs: P3-38, P9-11
131. Rubin-Toles, M., Gambhir, M., Ramji, K., Roth, A., Goel, S. "Conformal Language Model Reasoning with Coherent Factuality." arXiv:2505.17126, 2025. https://arxiv.org/abs/2505.17126 — `verified` (abstract) · Doc refs: P8-30
132. Saad-Falcon, J., Khattab, O., Potts, C., Zaharia, M. "ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems." NAACL 2024; arXiv:2311.09476. https://arxiv.org/abs/2311.09476 — `verified` · Doc refs: P8-20
133. Santhanam, K., Khattab, O., Saad-Falcon, J., Potts, C., Zaharia, M. "ColBERTv2." NAACL 2022. https://arxiv.org/abs/2112.01488 — `verified` · Doc refs: P2-45
134. Sarthi, P., Abdullah, S., Tuli, A., Khanna, S., Goldie, A., Manning, C.D. "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval." arXiv:2401.18059, 2024. https://arxiv.org/abs/2401.18059 — `verified` · Doc refs: P2-22
135. (authors not verified). "SBV-LawGraph: A Hybrid RAG Approach Integrating Knowledge Graph for the State Bank of Vietnam Legal Documents." ACIIDS 2026, Springer. https://link.springer.com/chapter/10.1007/978-981-92-0071-9_16 — `snippet` · Doc refs: P3-3
136. "Seeing is Believing? Mitigating OCR Hallucinations in Multimodal Large Language Models." NeurIPS 2025. https://arxiv.org/abs/2506.20168 — `snippet` · Doc refs: P1-15
137. Servantez, S., Barrow, J., Hammond, K., Jain, R. "Chain of Logic: Rule-Based Reasoning with Large Language Models." arXiv 2402.10400, 2024 (ACL Findings venue not confirmed in review). https://arxiv.org/abs/2402.10400 — `verified` (abstract) · Doc refs: P6-14
138. Shankar, S. et al. "Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences" (EvalGen). UIST 2024; arXiv:2404.12272. https://arxiv.org/abs/2404.12272 — `verified` · Doc refs: P8-37
139. Sharma, M. et al. "Towards Understanding Sycophancy in Language Models." 2023/2025. https://arxiv.org/abs/2310.13548 — `verified` · Doc refs: P6-19
140. Sheng, Y. et al. "S-LoRA: Serving Thousands of Concurrent LoRA Adapters." 2023. https://arxiv.org/abs/2311.03285 — `snippet` · Doc refs: P9-33
141. Singh, D., Narayanan, S. "Unmasking the Reality of PII Masking Models: Performance Gaps and the Call for Accountability." arXiv, 2025. https://arxiv.org/abs/2504.12308 — `verified` · Doc refs: P9-28
142. Smit, A.P., Grinsztajn, N., Duckworth, P., Barrett, T.D., Pretorius, A. "Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs." ICML 2024 (PMLR 235). https://proceedings.mlr.press/v235/smit24a.html — `verified` · Doc refs: P6-10
143. Song, Y., Kim, Y., Iyyer, M. "VeriScore: Evaluating the factuality of verifiable claims in long-form text generation." arXiv:2406.19276, 2024. https://arxiv.org/abs/2406.19276 — `verified` · Doc refs: P8-18
144. Souly, A., Rando, J., Chapman, E. et al. "Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples." arXiv, 2025 (with Anthropic, UK AISI, Alan Turing Institute). https://arxiv.org/abs/2510.07192 ; https://www.anthropic.com/research/small-samples-poison — `verified` · Doc refs: P9-14
145. "δ-Stance: A Large-Scale Real World Dataset of Stances in Legal Argumentation." ACL 2025. https://aclanthology.org/2025.acl-long.1517 — `verified` (abstract) · Doc refs: P5-18
146. Stanford RegLab & Casetext. "The Overruling Dataset: A Benchmark for Detecting Legal Decisions that Have Been Overruled." https://reglab.stanford.edu/data/the-overruling-dataset-a-benchmark-for-detecting-legal-decisions-that-have-been-overruled/ — `verified` · Doc refs: P3-15
147. Sun, W. et al. "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents." EMNLP, 2023. https://arxiv.org/abs/2304.09542 — `verified` · Doc refs: P9-10
148. Sweeney, L. "k-Anonymity: A Model for Protecting Privacy." Int. J. Uncertainty, Fuzziness and Knowledge-Based Systems 10(5):557–570, 2002. https://doi.org/10.1142/S0218488502001648 — `snippet` (bibliographic details via Wikipedia) · Doc refs: P9-42
149. Tang, L., Laban, P., Durrett, G. "MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents." EMNLP 2024; arXiv:2404.10774. https://arxiv.org/abs/2404.10774 — `verified` · Doc refs: P8-12
150. Tang, Y., Qiu, R., Yin, H., Li, X., Huang, Z. "CaseLink: Inductive Graph Learning for Legal Case Retrieval." SIGIR 2024. https://arxiv.org/abs/2403.17780 — `verified` (abstract; claims SOTA without naming COLIEE years in the abstract) · Doc refs: P5-13
151. Taranukhin, M., Shwartz, V. "Legal LLM Hallucination Should Be Evaluated as Failure of Legal Warrant." arXiv:2609.17546, 2026. https://arxiv.org/abs/2609.17546 — `verified` (abstract) · Doc refs: P8-5
152. Terdalkar, H., Bhojani, K., Dongare, A., Behera, O.A. "BHRAM-IL: A Benchmark for Hallucination Recognition and Assessment in Multiple Indian Languages." arXiv:2512.01852, 2025. https://arxiv.org/abs/2512.01852 — `verified` · Doc refs: P8-59
153. UQLegalAI. "UQLegalAI@COLIEE2025: Advancing Legal Case Retrieval with Large Language Models and Graph Neural Networks." arXiv 2505.20743, 2025. https://arxiv.org/abs/2505.20743 — `snippet` · Doc refs: P5-14
154. Verma, A. "Is this Citation on Point?" arXiv:2608.12571, 2026. https://arxiv.org/abs/2608.12571 — `verified` (abstract) · Doc refs: P8-4
155. Villavicencio, M., Pan, S., Wang, Q. "Not All Uncertainty Is Equal: How Uncertainty Granularity Shapes Human Verification in LLM-Assisted Decision Making." arXiv:2605.28571, 2026. https://arxiv.org/abs/2605.28571 — `verified` (abstract) · Doc refs: P8-45
156. Wang, C. et al. "LeKUBE: A Legal Knowledge Update BEnchmark." arXiv:2407.14192, 2024; Li, C. et al. "LexKairos: Benchmarking Legal Temporal Capabilities in LLMs." arXiv:2608.09106, 2026. https://arxiv.org/abs/2407.14192 ; https://arxiv.org/abs/2608.09106 — `verified` (abstracts) · Doc refs: P8-64
157. Wang, F., Li, B. "Leaner Training, Lower Leakage: Revisiting Memorization in LLM Fine-Tuning with LoRA." arXiv, 2025. https://arxiv.org/abs/2506.20856 — `verified` · Doc refs: P9-34
158. Wang, Q., Wang, Z., Su, Y., Tong, H., Song, Y. "Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Key?" 2024. https://arxiv.org/abs/2402.18272 — `verified` · Doc refs: P6-11
159. Wanner, M., Ebner, S., Jiang, Z., Dredze, M., Van Durme, B. "A Closer Look at Claim Decomposition." arXiv:2403.11903, 2024. https://arxiv.org/abs/2403.11903 — `verified` · Doc refs: P8-16
160. Weller, O., et al. "Rank1: Test-Time Compute for Reranking in Information Retrieval." COLM 2025 / arXiv 2502.18418. https://arxiv.org/abs/2502.18418 — `verified` (abstract; COLM 2025); benchmark margins not verified · Doc refs: P5-33
161. Xiong, M. et al. "Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs." ICLR 2024; arXiv:2306.13063. https://arxiv.org/abs/2306.13063 — `verified` · Doc refs: P8-32
162. "Youtu-Parsing: Perception, Structuring and Recognition via High-Parallelism Decoding." arXiv:2601.20430, 2026 (reports olmOCR-Bench for PaddleOCR-VL, dots.ocr, MinerU2.5). https://arxiv.org/abs/2601.20430 — `snippet` · Doc refs: P1-41
163. Zeng, L., Jin, Y. "FinCacheServe: Dependency-Consistent Answer Reuse for Cost-Efficient RAG Serving over Mutable Enterprise Documents." arXiv 2607.26076, 2026. https://arxiv.org/abs/2607.26076 — `verified` (abstract) · Doc refs: P4-7
164. Zha, Y., Yang, Y., Li, R., Hu, Z. "AlignScore: Evaluating Factual Consistency with a Unified Alignment Function." ACL 2023; arXiv:2305.16739. https://arxiv.org/abs/2305.16739 — `verified` · Doc refs: P8-13
165. Zhang, H., Cui, Z., Chen, J., Wang, X., Zhang, Q., Wang, Z., Wu, D., Hu, S. "Stop Overvaluing Multi-Agent Debate — We Must Rethink Evaluation and Embrace Model Heterogeneity." arXiv 2502.08788, 2025. https://arxiv.org/abs/2502.08788 — `verified` (abstract) · Doc refs: P6-13
166. Zhang, Y., Liao, Q.V., Bellamy, R.K.E. "Effect of Confidence and Explanation on Accuracy and Trust Calibration in AI-Assisted Decision Making." FAT* 2020. https://arxiv.org/abs/2001.02114 — `verified` · Doc refs: P10-9
167. Zheng, L. et al. "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." NeurIPS 2023 D&B; arXiv:2306.05685. https://arxiv.org/abs/2306.05685 — `verified` · Doc refs: P8-35
168. Zheng, L., Guha, N., Anderson, B.R., Henderson, P., Ho, D.E. "When Does Pretraining Help? Assessing Self-Supervised Learning for Law and the CaseHOLD Dataset." ICAIL 2021; arXiv:2104.08671. https://arxiv.org/abs/2104.08671 — `verified` · Doc refs: P3-17, P8-50
169. Ziegler, A., Kalliamvakou, E., Simister, S., Sittampalam, G., Li, A., Rice, A., Rifkin, D., Aftandilian, E. "Productivity Assessment of Neural Code Completion." MAPS@PLDI, 2022. https://arxiv.org/abs/2205.06537 — `verified` · Doc refs: P9-9

## 2. Indian legal NLP datasets & benchmarks

*Scope:* Datasets, benchmarks, models, libraries and papers whose primary subject is Indian legal text (judgments, statutes, legal translation), plus the open bulk judgment datasets. (32 sources.)

1. AWS Open Data Registry / Dattam Labs. "Indian High Court Judgments." https://registry.opendata.aws/indian-high-court-judgments/ — `verified` · Doc refs: P0-1, XC-15, IN-65
2. AWS Open Data Registry / vanga. "Indian Supreme Court Judgments" (~35K judgments 1950–2025, ~52.24 GB, CC-BY-4.0). https://registry.opendata.aws/indian-supreme-court-judgments/ ; https://github.com/vanga/indian-supreme-court-judgments — `verified` · Doc refs: XC-17, IN-65
3. Bhattacharya, P. et al. "Identification of Rhetorical Roles of Sentences in Indian Legal Judgments." JURIX 2019. https://arxiv.org/abs/1911.05405 — `unverified` · Doc refs: P1-21
4. Bhattacharya, P., Ghosh, K., Ghosh, S., Pal, A., et al. "FIRE 2019 AILA Track: Artificial Intelligence for Legal Assistance" (track site: ≈3,000 SC judgments, 197 statute sections, 50 test queries; see also arXiv 2105.11347 and the AILA 2020 site). https://sites.google.com/view/fire-2019-aila/ ; https://arxiv.org/abs/2105.11347 ; https://sites.google.com/view/aila-2020 — `verified` (track site) · Doc refs: P5-11
5. Bhattacharya, P., Ghosh, K., Pal, A., Ghosh, S. "Hier-SPCNet: A Legal Statute Hierarchy-based Heterogeneous Network for Computing Legal Case Document Similarity." SIGIR 2020 (arXiv 2007.03225). https://arxiv.org/abs/2007.03225 — `snippet` · Doc refs: P3-28, P5-12
6. Bose, J. "Falkor-IRAC: Graph-Constrained Generation for Verified Legal Reasoning in Indian Judicial AI." arXiv:2605.14665, 2026. https://arxiv.org/abs/2605.14665 — `verified` (abstract; proof of concept on 51 SC judgments; InIRAC dataset) · Doc refs: P8-65
7. Dattam Labs (vanga). "indian-high-court-judgments: opendata/docs/dataset.md." GitHub, 2025–26. https://github.com/vanga/indian-high-court-judgments/blob/main/opendata/docs/dataset.md — `verified` · Doc refs: P0-2
8. Dattam Labs (vanga). "indian-supreme-court-judgments." GitHub, 2025–26. https://github.com/vanga/indian-supreme-court-judgments — `verified` · Doc refs: P0-3, XC-17
9. Deroy, A., Ghosh, K., Ghosh, S. "A Tree-of-Thoughts Inspired Hybrid Approach for Legal Case Judgement Summarization using LLMs." arXiv:2606.28044, 2026. https://arxiv.org/abs/2606.28044 — `verified` (abstract) · Doc refs: P2-27
10. Deroy, A., Ghosh, K., Ghosh, S. "Applicability of Large Language Models and Generative Models for Legal Case Judgement Summarization." arXiv:2407.12848, 2024. https://arxiv.org/abs/2407.12848 — `verified` · Doc refs: P2-26
11. Deroy, A., Ghosh, K., Ghosh, S. "How Ready are Pre-trained Abstractive Models and LLMs for Legal Case Judgement Summarization?" arXiv:2306.01248, 2023. https://arxiv.org/abs/2306.01248 — `verified` · Doc refs: P2-25
12. Harde, P., Jain, B., Jain, S. "LeCNet: A Legal Citation Network Benchmark Dataset." Proc. 1st Workshop on NLP for Empowering Justice (JUST-NLP 2025). https://aclanthology.org/2025.justnlp-main.4/ — `verified` · Doc refs: P3-29
13. India Science & Technology portal. "Predictive Coding for Identification of Ratio Decidendi in Indian Judicial Decisions" (NIT Tiruchirappalli, 2024–2027). https://indiascienceandtechnology.gov.in/research/predictive-coding-identification-ratio-decidendi-indian-judicial-decisions — `snippet` · Doc refs: P1-44
14. Joshi, A., Paul, S., Sharma, A., Goyal, P., Ghosh, S., Modi, A. "IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning." ACL 2024. https://arxiv.org/abs/2407.05399 — `verified` · Doc refs: P1-22, P2-7, P3-30, P5-10, P8-46, XC-18 · Also at: https://exploration-lab.github.io/IL-TUR/
15. Joshi, A., Sharma, A., Tanikella, S.K., Modi, A. "U-CREAT: Unsupervised Case Retrieval using Events extrAcTion." ACL 2023. https://arxiv.org/html/2307.05260v1 — `verified` · Doc refs: P2-9, P5-9 · Also at: https://aclanthology.org/2023.acl-long.777
16. Kalamkar, P., Agarwal, A., Tiwari, A., Gupta, S., Karn, S., Raghavan, V. "Named Entity Recognition in Indian court judgments." NLLP Workshop, 2022. https://aclanthology.org/2022.nllp-1.15 — `verified` (46,545 entities, 14 types; type list unverified) · Doc refs: P1-23, P9-26 · Also at: https://arxiv.org/abs/2211.03442
17. Kalamkar, P., Tiwari, A., Agarwal, A., Karn, S., Gupta, S., Raghavan, V., Modi, A. "Corpus for Automatic Structuring of Legal Documents." LREC 2022. https://arxiv.org/abs/2201.13125 — `verified` · Doc refs: P1-17
18. law-ai. "InLegalBERT" model card. Hugging Face. https://huggingface.co/law-ai/InLegalBERT — `verified` · Doc refs: P2-6
19. Mahapatra, S. et al. "MILPaC: A Novel Benchmark for Evaluating Translation of Legal Text to Indian Languages." arXiv:2310.09765, 2023. https://arxiv.org/abs/2310.09765 — `verified` · Doc refs: P8-61
20. Malik, V. et al. "ILDC for CJPE: Indian Legal Documents Corpus for Court Judgment Prediction and Explanation." ACL 2021; arXiv:2105.13562. https://arxiv.org/abs/2105.13562 — `verified` · Doc refs: P8-51
21. Malik, V., Sanjay, R., Guha, S.K., Hazarika, A., Nigam, S., Bhattacharya, A., Modi, A. "Semantic Segmentation of Legal Documents via Rhetorical Roles." NLLP @ EMNLP 2022. https://arxiv.org/abs/2112.01836 — `verified` · Doc refs: P1-20
22. Modi, A. et al. "SemEval 2023 Task 6: LegalEval — Understanding Legal Texts." SemEval 2023; arXiv:2304.09548. https://arxiv.org/abs/2304.09548 — `verified` · Doc refs: P1-18, P8-56
23. MTEB. "AILA_casedocs" dataset card (FIRE 2019 AILA; 50 queries, 186 docs). Hugging Face. https://huggingface.co/datasets/mteb/AILA_casedocs — `verified` · Doc refs: P2-51
24. Nigam, S.K. et al. "Legal Judgment Reimagined: PredEx and the Rise of Intelligent AI Interpretation in Indian Courts." Findings of ACL 2024; arXiv:2406.04136. https://arxiv.org/abs/2406.04136 — `verified` · Doc refs: P8-52
25. Nigam, S.K. et al. "NyayaAnumana & INLegalLlama: The Largest Indian Legal Judgment Prediction Dataset and Specialized Language Model." COLING 2025; arXiv:2412.08385. https://arxiv.org/abs/2412.08385 — `verified` · Doc refs: P8-53
26. Nigam, S.K., Dubey, T., Sharma, G., Shallum, N., Ghosh, K., Bhattacharya, A. "LegalSeg: Unlocking the Structure of Indian Legal Judgments Through Rhetorical Role Classification." Findings of NAACL 2025. https://arxiv.org/abs/2502.05836 — `verified` · Doc refs: P1-19
27. Nigam, S.K., Mishra, S.K., Shallum, N., Ghosh, K., Bhattacharya, A. "AILQA: Evaluating AI-Driven Legal Question Answering Systems for the Indian Legal System." arXiv:2607.18825, 2026. https://arxiv.org/abs/2607.18825 — `verified` (abstract + HTML body: ~7,221 docs, ChromaDB, Ada/Instructor-XL/mxbai) · Doc refs: P2-52, P8-55
28. OpenNyAI. "Opennyai" library (NER, rhetorical roles, extractive summariser; MIT). https://github.com/OpenNyAI/Opennyai — `verified` · Doc refs: P1-25
29. Paul, S., Ghumare, D., Goyal, P., Ghosh, S., Modi, A. "IL-PCSR: Legal Corpus for Prior Case and Statute Retrieval." EMNLP 2025. https://arxiv.org/html/2511.00268v1 — `verified` · Doc refs: P2-8
30. Paul, S., Mandal, A., Goyal, P., Ghosh, S. "Pre-trained Language Models for the Legal Domain: A Case Study on Indian Law." ICAIL 2023. https://arxiv.org/abs/2209.06049 — `verified` · Doc refs: P1-24, P2-5
31. Shukla, A., Bhattacharya, P., Poddar, S., Mukherjee, R., Ghosh, K., Goyal, P., Ghosh, S. "Legal Case Document Summarization: Extractive and Abstractive Methods and their Evaluation." AACL-IJCNLP 2022. https://arxiv.org/abs/2210.07544 — `verified` · Doc refs: P2-24
32. vanga (Dattam Labs). "indian-high-court-judgments" GitHub repo and STATS.md (17,771,420 PDFs; 1,276.94 GiB; per-year counts). https://github.com/vanga/indian-high-court-judgments/blob/main/STATS.md — `verified` · Doc refs: XC-16

## 3. Indian primary legal sources (statutes, judgments, official portals)

*Scope:* Constitution, central statutes and rules, Supreme Court / High Court / tribunal judgments and orders, and official court, legislation and gazette portals. Statute text reached through a mirror (Indian Kanoon, dpdpa.com, devgan.in, Vidhi Judicial) is still listed here. (95 sources.)

1. Government of Odisha. "About e-Gazette" (weekly vs extraordinary gazettes). https://egazette.odisha.gov.in/about_gazette — `snippet` · Doc refs: P0-34
2. Supreme Court of India. Achin Gupta v. State of Haryana, 2024 INSC 369 (3 May 2024), paras 38–39. https://indiankanoon.org/doc/172613397/ — `verified` · Doc refs: IN-38
3. Anjum Kadari v. Union of India, 2024 INSC 831 (SC, 5 Nov 2024) — against Allahabad HC judgment of 22 Mar 2024 (UP Board of Madarsa Education Act, 2004). https://indiankanoon.org/doc/67107476/ — `verified` · Doc refs: P4-43
4. Arbitration and Conciliation Act 1996, s.34(3) and proviso (three months + 30 days, "but not thereafter"). https://indiankanoon.org/doc/536284/ — `verified` · Doc refs: P6-40
5. Karnataka High Court (Kalaburagi). Arunkumar v. State of Karnataka, Crl.P. 200913/2024, 2024:KHC-K:7531 (30 Sep 2024) (quotes BNS s.358 in full). https://indiankanoon.org/doc/47759402/ — `verified` · Doc refs: IN-31
6. Bar Council of India. "Rules on Professional Standards" (Bar Council of India Rules, Part VI, Chapter II — duty to client incl. confidentiality and not acting for the opposite party; rule numbers 17/33 from memory). https://www.barcouncilofindia.org/info/rules-on-professional-standards — `unverified` (page did not render rule text) · Doc refs: P7-38
7. Supreme Court of India. Bengal Immunity Co. Ltd v. State of Bihar (6 Sep 1955). https://indiankanoon.org/doc/1629830/ — `verified` · Doc refs: IN-19
8. Bharatiya Nagarik Suraksha Sanhita 2023, s.187(2)–(3) (police custody; default bail; "ten years or more" ambiguity). LiveLaw analysis: https://www.livelaw.in/top-stories/bnss-right-to-default-bail-under-bharatiya-nagarik-suraksha-sanhita-282457 — `verified` (secondary) · Doc refs: P6-36
9. Bharatiya Nagarik Suraksha Sanhita, 2023, s.531 "Repeal and savings" (CrPC 1973 repealed; pending appeals, applications, trials, inquiries and investigations continue under the CrPC). https://indiankanoon.org/doc/74791982/ — `verified` · Doc refs: P3-64, P4-49, IN-32 · Also at: https://indiankanoon.org/search/?formInput=Bharatiya%20Nagarik%20Suraksha%20Sanhita%202023%20repeal%20and%20savings%20doctypes:laws ; https://en.wikipedia.org/wiki/Bharatiya_Nagarik_Suraksha_Sanhita
10. Indian Kanoon. Bharatiya Nyaya Sanhita, 2023 — ss.103 "Punishment for murder", 104 "Punishment for murder by life-convict", 105 "Punishment for culpable homicide not amounting to murder" (section headings). https://indiankanoon.org/search/?formInput=punishment%20for%20murder%20Bharatiya%20Nyaya%20Sanhita%202023%20doctypes:laws — `verified` · Doc refs: P3-61
11. Bharatiya Sakshya Adhiniyam 2023, s.170. https://indiankanoon.org/doc/10673658/ — `verified` · Doc refs: IN-33
12. Bharatiya Sakshya Adhiniyam 2023, s.63 (admissibility of electronic records; s.63(4) certificate in the Schedule; successor to IEA s.65B). https://indiankanoon.org/doc/125020475/ — `verified` · Doc refs: P6-43, P7-10, IN-41, IN-76 · Also at: https://vidhijudicial.com/section-63-of-the-bharatiya-sakshya-adhiniyam,-2023.html
13. Government of India. Bharatiya Sakshya Adhiniyam, 2023, s.132 "Professional communications", via Indian Kanoon. https://indiankanoon.org/doc/142112571/ — `verified` · Doc refs: P7-8, P8-69, XC-43, IN-61 · Also at: https://vidhijudicial.com/section-132-of-the-bharatiya-sakshya-adhiniyam,-2023.html
14. Devgan.in. "BNS Section 103: Punishment for murder" (text of s.103(1)–(2); IPC 302 correspondence). https://devgan.in/bns/section/103/ — `verified` (secondary; official text at [IN-44]) · Doc refs: IN-77
15. "BNS Section 358 — Repeal and savings." Bharatiya Nyaya Sanhita, 2023 (secondary text via devgan.in). https://devgan.in/bns/section/358/ — `verified` (secondary) · Doc refs: P1-47
16. "BNS Section 72 — Disclosure of identity of the victim of certain offences, etc." Bharatiya Nyaya Sanhita, 2023 (secondary text via devgan.in). https://devgan.in/bns/section/72/ — `verified` (secondary) · Doc refs: P1-45
17. Indian Kanoon search: Buckeye Trust v. PCIT, ITA No. 1051/Bang/2024 (ITAT Bangalore order 30 Dec 2024; later order 12 Feb 2026). https://indiankanoon.org/search/?formInput=Buckeye%20Trust%20ITAT%20Bangalore — `verified` · Doc refs: CT-48, IN-73
18. High Court of Karnataka. *Buckeye Trust v. Registrar, Income Tax Appellate Tribunal*, WP No. 25280 of 2025, order of 18 Sep 2025 (M. Nagaprasanna J.), NC: 2025:KHC:37479. https://indiankanoon.org/doc/145492551/ — `verified` · Doc refs: CT-56
19. Calcutta High Court. C.R.M.(A) 2354 of 2026, In re: Sadhan Ghosh (27 Aug 2026) (IK title mis-parsed as "Section 318 Of The Bharatiya Nyaya ... vs In Re: Sadhan Ghosh"). https://indiankanoon.org/doc/96134630/ — `verified` · Doc refs: IN-75
20. Supreme Court of India. CBI v. Ramesh Chander Diwan, 2025 INSC 539 (22 Apr 2025), para 30. https://indiankanoon.org/doc/101752699/ — `verified` · Doc refs: IN-35
21. Central Board of Dawoodi Bohra Community v. State of Maharashtra, (2005) 2 SCC 673 (SC, 5 judges, 17 Dec 2004). https://indiankanoon.org/doc/708017/ — `verified` (P3 session [P3-51]) · Doc refs: P3-51, P4-45, P5-36, IN-12
22. Central Organisation for Railway Electrification v. ECI-SPIC-SMO-MCML (JV), SC Constitution Bench (5 judges), 8 Nov 2024. https://indiankanoon.org/doc/94564485/ — `verified` · Doc refs: P4-39
23. CGST Act 2017 s.74A (inserted by Finance (No.2) Act 2024; FY 2024-25 onward): 42-month SCN limit, ₹1,000 threshold, s.74A(7) 12 months + up to 6 months, s.74A(8)/(9) payment windows. VJM Global: https://www.vjmglobal.com/blog/detailed-insight-of-section-74-a-of-cgst-act-2017-common-provisions-for-fraud-and-non-fraud-cases-under-gst-law — `verified` (secondary) · Doc refs: P6-39
24. Supreme Court of India. CIT v. Vegetable Products Ltd, (1973) 1 SCC 442 (29 Jan 1973). https://indiankanoon.org/doc/957191/ — `verified` · Doc refs: IN-29
25. Code of Civil Procedure 1908, s.137. https://indiankanoon.org/doc/87116228/ — `verified` · Doc refs: IN-46
26. Constitution of India, Art. 123. https://indiankanoon.org/doc/1090693/ — `verified` · Doc refs: IN-8
27. Constitution of India, Art. 141. https://indiankanoon.org/doc/882644/ — `verified` · Doc refs: P3-50, IN-4 · Also at: https://www.constitutionofindia.net/articles/article-141-law-declared-by-supreme-court-to-be-binding-on-all-courts/
28. Constitution of India, Art. 144. https://indiankanoon.org/doc/1799967/ — `verified` · Doc refs: IN-5
29. Constitution of India, Art. 20. https://indiankanoon.org/doc/655638/ — `verified` · Doc refs: P4-50, IN-7
30. Constitution of India, Art. 227. https://indiankanoon.org/doc/1331149/ — `verified` · Doc refs: IN-6
31. Constitution of India, Art. 254. https://indiankanoon.org/doc/1930681/ — `verified` · Doc refs: IN-9
32. Constitution of India, Article 145(3) — minimum five judges for a substantial question of law as to the interpretation of the Constitution or an Art. 143 reference. https://www.constitutionofindia.net/articles/article-145-rules-of-court-etc/ — `verified` · Doc refs: P3-63
33. Constitution of India, Article 348 (language to be used in the Supreme Court and High Courts; Art. 348(2) proviso excludes judgments, decrees and orders). https://www.constitutionofindia.net/articles/article-348-language-to-be-used-in-the-supreme-court-and-in-the-high-courts-and-for-acts-bills-etc/ — `verified` · Doc refs: P9-45, IN-10 · Also at: https://indiankanoon.org/doc/928281/
34. Consumer Protection Act 2019, s.38(2)(a) (opposite party's version within 30 days or extended period not exceeding 15 days). https://indiankanoon.org/doc/84381021/ — `snippet` · Doc refs: P6-45
35. Copyright Act 1957, s.2(k) "Government work" (text). Indian Kanoon search. https://indiankanoon.org/search/?formInput=title%3A%22Section%202%20in%20The%20Copyright%20Act%2C%201957%22 — `verified` · Doc refs: IN-2
36. Copyright Act 1957, s.52(1)(q)–(r) (text). Indian Kanoon. https://indiankanoon.org/doc/1013176/ — `verified` · Doc refs: P0-17, IN-1 · Also at: https://www.copyright.gov.in/Exceptions.aspx
37. Gauhati High Court. Criminal appeal decided 19 Jun 2025 (IK title mis-parsed as "Page No.# 1/35 vs The State Of Assam And Anr"). https://indiankanoon.org/doc/160208619/ — `verified` · Doc refs: IN-39
38. Digital Personal Data Protection Act 2023, s.16 (text). https://dpdpa.com/dpdpa2023/chapter-4/section16.html — `verified` · Doc refs: P7-5, IN-56
39. Digital Personal Data Protection Act 2023, s.3(c)(ii) (mirror text; PRS copy of Act). https://www.dpdpa.com/dpdpa2023/chapter-1/section3.html ; https://prsindia.org/files/bills_acts/acts_parliament/2023/Digital_Personal_Data_Protection_Act,_2023.pdf — `verified` (clause text via mirror) · Doc refs: P0-23, P8-67, XC-42, IN-58 · Also at: https://indiankanoon.org/doc/84660522/
40. Digital Personal Data Protection Act, 2023, s.12 (right to correction and erasure). https://dpdpa.com/dpdpa2023/chapter-3/section12.html — `snippet` · Doc refs: P9-23
41. Digital Personal Data Protection Act, 2023, s.17 (s.17(1)(a) legal-claims exemption; s.8(1), s.8(5) still apply). https://dpdpa.com/dpdpa2023/chapter-4/section17.html — `verified` (sibling P7-3/P9-22) · Doc refs: P7-3, P8-68, P9-22, IN-57
42. Digital Personal Data Protection Act, 2023, s.7 (legitimate uses; s.7(i) employment). https://dpdpa.com/dpdpa2023/chapter-2/section7.html — `verified` · Doc refs: P10-16
43. Digital Personal Data Protection Rules, 2025, G.S.R. 843(E), 14 Nov 2025; enforcement timeline (immediate / +12 months / +18 months for ss.3–5, 7–17 of the Act). https://dpdpa.com/dpdpa_enforcement_timeline.html ; rules PDF https://dpdpa.com/DPDP_Rules_2025_English_only.pdf — `verified` (timeline page; secondary host, gazette PDF not read) · Doc refs: P8-74
44. e-Gazette of India PDF paths (e.g. https://egazette.gov.in/WriteReadData/1969/O-1469-1969-0001-66051.pdf) and Internet Archive mirror (https://archive.org/download/in.gazette.1972.112/) — `snippet` · Doc refs: P0-35
45. *East India Commercial Co. Ltd. v. Collector of Customs, Calcutta*, AIR 1962 SC 1893; 1963 (3) SCR 338 (decided 4 May 1962; Sarkar, Subba Rao, Mudholkar JJ.). https://indiankanoon.org/doc/1839963/ — `verified` · Doc refs: P5-35, IN-21
46. Supreme Court of India. Eastern Book Company & Ors v. D.B. Modak & Anr, (2008) 1 SCC 1; AIR 2008 SC 809 (12 Dec 2007), paras 40–42. https://indiankanoon.org/doc/1062099/ — `verified` (re-checked in review) · Doc refs: P0-18, P2-28, CT-49, IN-3
47. eCommittee SC / NIC. "Judgment Search Portal." https://judgments.ecourts.gov.in/pdfsearch/ — `verified` (probe 2026-09-30: Securimage CAPTCHA) · Doc refs: P0-5
48. eCourts Services portal (CNR search, case status, orders, cause list; CAPTCHA). https://services.ecourts.gov.in/ecourtindia_v6/ — `verified` · Doc refs: P7-15, P10-30
49. Supreme Court of India. "Equivalent Citation Table — how to find" (SCR ↔ SCC, AIR(SC), JT, SCALE). https://main.sci.gov.in/pdf/ECT/how2find.pdf — `snippet` (fetch failed: DNS) · Doc refs: P1-31
50. General Clauses Act 1897, s.6. https://indiankanoon.org/doc/1030013/ — `verified` · Doc refs: IN-47
51. General Clauses Act 1897, s.9 (commencement and termination of time: "from" excludes first day, "to" includes last). https://indiankanoon.org/doc/1353686/ — `verified` · Doc refs: P6-41
52. Supreme Court of India. Homepage "latest judgments" view-pdf links (diary_no pattern), probed 2026-09-30. https://www.sci.gov.in/ — `verified` · Doc refs: IN-50
53. Illustrative NI Act authorities: Rangappa v Sri Mohan (2010) 11 SCC 441; Sampelly Satyanarayana Rao v IREDA (2016) 10 SCC 458; Saketh India Ltd v India Securities Ltd (1999) 3 SCC 1. Citations and headline holdings confirmed via Indian Kanoon search results (https://indiankanoon.org/search/?formInput=Rangappa%20v%20Sri%20Mohan ; …Sampelly… ; …Saketh…) — `snippet` · Doc refs: P6-44
54. In Re: Cognizance for Extension of Limitation, SMWP(C) 3/2020, order 10 Jan 2022. S.S. Rana summary: https://ssrana.in/articles/extension-limitation-period-supreme-court-january10/ — `verified` (secondary) · Doc refs: P6-35
55. In re: Interplay between Arbitration Agreements under the Arbitration and Conciliation Act, 1996 and the Indian Stamp Act, 1899, 2023 INSC 1066 (SC, 7 judges, 13 Dec 2023) — overrules N.N. Global (2023); SMS Tea Estates and Garware Wall Ropes "wrongly decided". https://indiankanoon.org/doc/139003074/ — `verified` · Doc refs: P3-55, P4-36, IN-30
56. Supreme Court Observer. "In re: Summoning Advocates who give Legal Opinion or Represent Parties during Investigation of Cases and Related Issues", 2025 INSC 1275 (31 Oct 2025; Gavai CJI, K.V. Chandran, N.V. Anjaria JJ). https://www.scobserver.in/supreme-court-observer-law-reports-scolr/re-summoning-advocates-who-give-legal-opinion-or-represent-parties-during-investigation-of-cases-and-related-issues/ — `verified` · Doc refs: P7-9, P8-70, P9-25, IN-62 · Also at: https://globalinvestigationsreview.com/market-review/market-review-privilege/2025/article/india-insights-privilege-applicability-and-challenges-in-the-digital-age
57. Income-tax Act 2025 (assent 21 Aug 2025; in force 1 Apr 2026). TaxGuru: https://taxguru.in/income-tax/income-tax-act-2025-force-1st-april-2026.html — `verified` · Doc refs: P6-38, IN-72
58. Indian Kanoon section pages with "[Similar to …]" annotations: BNS ss.72, 103, 111, 113, 152, 304; BNSS ss.173, 307, 482, 528; BSA s.63. e.g. https://indiankanoon.org/doc/73182733/ (BNSS 482), https://indiankanoon.org/doc/99044874/ (BNSS 528), https://indiankanoon.org/doc/125020475/ (BSA 63), https://indiankanoon.org/doc/126533912/ (BNS 103), https://indiankanoon.org/doc/37266782/ (BNS 152), https://indiankanoon.org/doc/11650179/ (BNSS 307) — `verified` · Doc refs: IN-41
59. Delhi High Court. *Jorawer Singh Mundy @ Jorawar Singh Mundy v. Union of India & Ors*, W.P.(C) 3918/2021, order of 12 Apr 2021 (Prathiba M. Singh J.) directing Indian Kanoon to block a judgment from search-engine access pending the petition. https://indiankanoon.org/doc/86889244/ — `verified` · Doc refs: P2-55
60. Supreme Court of India. Kasireddy Upender Reddy v. State of Andhra Pradesh, 2025 INSC 768 (23 May 2025). https://indiankanoon.org/doc/64477422/ — `verified` · Doc refs: IN-37
61. Supreme Court of India. Krishna Kumar Singh v. State of Bihar (7 judges, 2 Jan 2017). https://indiankanoon.org/doc/107225908/ — `verified` · Doc refs: IN-28
62. Supreme Court of India. Kunhayammed v. State of Kerala, (2000) 6 SCC 359 (19 Jul 2000), conclusions (i)–(v). https://indiankanoon.org/doc/1940266/ — `verified` · Doc refs: P3-52, IN-17 · Also at: https://indiankanoon.org/search/?formInput=Kunhayammed%20State%20of%20Kerala%20merger
63. Supreme Court of India. Kusum Ingots & Alloys Ltd v. Union of India, (2004) 6 SCC 254 (28 Apr 2004). https://indiankanoon.org/doc/1876565/ — `verified` · Doc refs: IN-78
64. Supreme Court of India. L. Chandra Kumar v. Union of India, (1997) 3 SCC 261 (18 Mar 1997). https://indiankanoon.org/doc/1152518/ — `verified` · Doc refs: P3-59, IN-24
65. Delhi High Court. Laksh Vir Singh Yadav v. Union of India & connected matters, W.P.(C) 1021/2016 (Sachin Datta J., 29 May 2026), para 1, masking principles (iii)–(v), paras 277, 279–287. https://indiankanoon.org/doc/4658201/ — `verified` · Doc refs: IN-55
66. The Limitation Act, 1963 (Act 36 of 1963), ss.4, 5, 12, 14; Schedule Art. 113. https://indiankanoon.org/doc/1317393/ — `verified` · Doc refs: P6-31
67. Supreme Court of India. Mineral Area Development Authority v. Steel Authority of India, 2024 INSC 607 (14 Aug 2024), paras 24–25. https://indiankanoon.org/doc/96063944/ — `verified` · Doc refs: P4-38, IN-26
68. Mineral Area Development Authority v. Steel Authority of India: judgment of 25 Jul 2024 (9 judges) https://indiankanoon.org/doc/179331686/ — `snippet` · Doc refs: P4-38
69. Ministry of Home Affairs. New criminal laws page (BNS/BNSS/BSA PDFs, e.g. /sites/default/files/2024-04/250883_english_01042024.pdf). https://www.mha.gov.in/en/commoncontent/new-criminal-laws — `verified` (links present) · Doc refs: IN-44
70. Najma Khatun v. State of West Bengal, 2026 INSC 691 (SC, Dipankar Datta and Augustine George Masih JJ., 13 Jul 2026), ¶40 — quotes Shree Chamundi Mopeds on stay of operation vs quashing. https://indiankanoon.org/doc/106091339/ — `verified` · Doc refs: P3-62
71. Supreme Court of India. National Insurance Co. Ltd v. Pranay Sethi, (2017) 16 SCC 680 (31 Oct 2017), para 30. https://indiankanoon.org/doc/139996215/ — `verified` · Doc refs: P3-57, IN-14
72. Negotiable Instruments Act 1881, s.142(2) (territorial jurisdiction) — `verified` · Doc refs: P6-42
73. Negotiable Instruments Act, 1881, s.138 (current text: demand notice "within thirty days"). https://indiankanoon.org/doc/1823824/ — `verified` · Doc refs: P5-40, P6-37
74. Supreme Court of India. Neutral Citation search page (date-range form with CAPTCHA), probed 2026-09-30. https://www.sci.gov.in/neutral-citation/ — `verified` · Doc refs: IN-49
75. New India Assurance Co. Ltd v Hilli Multipurpose Cold Storage Pvt Ltd (SC Constitution Bench, 4 Mar 2020). https://api.sci.gov.in/supremecourt/2013/35086/35086_2013_3_1501_21326_Judgement_04-Mar-2020.pdf — `snippet` · Doc refs: P6-34
76. Supreme Court of India. *Nipun Saxena v. Union of India*, decided 11 Dec 2018 (directions against publishing the name or identifying facts of rape victims in print, electronic or social media). https://indiankanoon.org/doc/53672964/ — `verified` · Doc refs: P2-56
77. High Court of Manipur. "Notice: eSCR and DigiSCR merged into SCR portal." https://hcmimphal.nic.in/Documents/eSCR%20and%20DigiSCR_0001.pdf — `snippet` · Doc refs: P0-7
78. Jharkhand High Court. Order of 19 Feb 2025 discussing IPC s.420 and BNS s.318(4). https://indiankanoon.org/doc/105667861/ — `snippet` · Doc refs: IN-40
79. Supreme Court of India. Parvinder Singh v. Directorate of Enforcement, 2026 INSC 519 (19 May 2026), paras 26–34. https://indiankanoon.org/doc/46844204/ — `verified` · Doc refs: IN-34
80. Patil Automation Pvt Ltd v Rakheja Engineers Pvt Ltd (SC, 17 Aug 2022). https://indiacorplaw.in/2022/09/05/supreme-court-on-mandatory-pre-litigation-mediation-in-commercial-court-cases/ — `verified` · Doc refs: P6-33
81. Supreme Court of India. Rajendra Bihari Lal v. State of U.P., 2025 INSC 1249 (17 Oct 2025). https://indiankanoon.org/doc/12774401/ — `verified` · Doc refs: IN-36
82. Supreme Court of India. Rupa Ashok Hurra v. Ashok Hurra, (2002) 4 SCC 388 (10 Apr 2002). https://indiankanoon.org/doc/854624/ — `verified` · Doc refs: IN-18
83. Supreme Court of India. S.I. Rooplal v. Lt. Governor, (2000) 1 SCC 644 (14 Dec 1999). https://indiankanoon.org/doc/1273655/ — `verified` · Doc refs: IN-23
84. Supreme Court of India. Sarwan Singh Lamba v. Union of India, (1995) 4 SCC 546 (12 May 1995). https://indiankanoon.org/doc/538878/ — `verified` · Doc refs: IN-20
85. SCG Contracts (India) Pvt Ltd v K.S. Chamankar Infrastructure Pvt Ltd, Civil Appeal 1638 of 2019, (2019) 12 SCC 210 (SC, 2019; exact decision date not confirmed). Khaitan & Co summary: https://khaitanco.com/thought-leadership/supreme-court-filing-of-written-statement-within-120-days-from-issuance-of-summons-is-mandatory — `verified` · Doc refs: P6-32
86. Supreme Court of India. Shree Chamundi Mopeds Ltd v. Church of South India Trust Assn., (1992) 3 SCC 1 (29 Apr 1992). https://indiankanoon.org/doc/422729/ — `verified` · Doc refs: P3-54, IN-27
87. *Shreya Singhal v. Union of India*, Supreme Court of India, decided 24 March 2015 (J. Chelameswar, R.F. Nariman JJ.), reported (2015) 5 SCC 1; s.66A IT Act declared unconstitutional. https://indiankanoon.org/doc/110813550/ — `verified` (holding and date; SCC citation not shown on the page read) · Doc refs: P3-56, P4-40, P5-39
88. Sita Soren v. Union of India, 2024 INSC 161 (SC, 7 judges, 4 Mar 2024), para 188 (Conclusion; "We disagree with and overrule the judgment of the majority on this aspect", re P.V. Narasimha Rao v. State (CBI/SPE), 5 judges, 1998). https://indiankanoon.org/doc/193599726/ — `verified` (independent review; earlier "para 131" citation was wrong) · Doc refs: P4-37
89. Supreme Court of India. Somaiya Organics (India) Ltd v. State of U.P. (17 Apr 2001) (quoting Golak Nath propositions). https://indiankanoon.org/doc/108182/ — `verified` · Doc refs: IN-25
90. Supreme Court of India. State of Punjab v. Rafiq Masih (White Washer) (8 Jul 2014) (Art. 142 directions not a binding precedent). https://indiankanoon.org/doc/154195973/ — `verified` · Doc refs: IN-79
91. State of U.P. v. Synthetics and Chemicals Ltd. (SC, 2 judges: T.K. Thommen, R.M. Sahai JJ., 18 Jul 1991), ¶¶93–94 — per incuriam and sub silentio. https://indiankanoon.org/doc/1488034/ — `verified` · Doc refs: P3-58, IN-16
92. Supreme Court of India. Sundarjas Kanyalal Bhatija v. Collector, Thane, AIR 1990 SC 261; 1989 SCR (3) 405 (13 Jul 1989). https://indiankanoon.org/doc/1931795/ — `verified` · Doc refs: IN-22
93. Department of Official Language, GoI. "The Official Languages Act, 1963", s. 7 (optional use of Hindi/State language in HC judgments; English translation issued under HC authority). https://rajbhasha.gov.in/en/official-languages-act-1963 — `verified` · Doc refs: P1-46, P5-41, P10-36, IN-11 · Also at: https://indiankanoon.org/doc/1500927/ ; https://en.wikisource.org/wiki/Official_Languages_Act,_1963 ; https://indiankanoon.org/doc/958327/
94. Supreme Court of India. Trimurthi Fragrances (P) Ltd v. Govt of NCT of Delhi (19 Sep 2022). https://indiankanoon.org/doc/85806537/ — `verified` · Doc refs: IN-13
95. Union Territory of Ladakh v. Jammu and Kashmir National Conference (SC, 2 judges: Vikram Nath, Ahsanuddin Amanullah JJ., 6 Sep 2023), ¶¶32–33 — pendency of a reference to a larger Bench does not stay other proceedings; courts decide on existing law. https://indiankanoon.org/doc/175104903/ — `verified` · Doc refs: P3-53, IN-15

## 4. Government, regulatory & compliance

*Scope:* Government programmes and publications, judicial administrative policies, foreign regulatory/ethics instruments, and law-firm or consultancy compliance explainers (DPDP, CERT-In). (17 sources.)

1. American Bar Association. "Formal Opinion 512: Generative Artificial Intelligence Tools." 29 Jul 2024 (via summaries). https://ezel.ai/ethics-opinions/aba/512-generative-ai-tools — `snippet` (sibling P9-15; primary PDF 403) · Doc refs: P8-71, P9-15 · Also at: https://natlawreview.com/article/aba-weighs-generative-ai-use-legal-practice
2. AZB & Partners. "DPDP Rules 2025 notified" (phased commencement to May 2027). 14 Nov 2025. https://www.azbpartners.com/?p=87799 — `verified` (via P7-1) · Doc refs: P7-1, P10-35, IN-59
3. AZB & Partners. "India's Digital Personal Data Protection Act: Phased Rollout and Key Compliance Milestones" (Rules notified Nov 2025; 18-month phase-in to May 2027). https://www.azbpartners.com/bank/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones/ ; The Week/PTI 14 Nov 2025 https://www.theweek.in/wire-updates/business/2025/11/14/del148-biz-dpdp-rules-ld-govt.html — `snippet` · Doc refs: XC-36
4. CERT-In. Directions under s.70B(6) IT Act, 28 Apr 2022 (6-hour reporting; 180-day logs in India; NTP sync) — as summarised by PSA Legal https://psalegal.com/new-cert-in-directions-overview-and-implications/ — `snippet` · Doc refs: XC-38
5. Digital India Awards 2022 Compendium, p.21 (Judgment Search Portal description). https://digitalindiaawards.india.gov.in/assets/compendium2022/files/basic-html/page21.html — `snippet` · Doc refs: P0-37
6. Government of India. "Government Open Data License – India (GODL)." (copy hosted by India Post) https://app.indiapost.gov.in/documents/media/OGD.pdf — `snippet` · Doc refs: P0-24, IN-66
7. High Court of Kerala. Policy on use of AI tools in the district judiciary (Jul 2025). No URL verified. — `unverified` · Doc refs: CT-53
8. Khaitan & Co. "Indian Computer Emergency Response Team Direction: Paradigm Shift in Cyber Incident Reporting" (CERT-In Directions of 28 Apr 2022). 2022. https://khaitanco.com/thought-leaderships/Indian-Computer-Emergency-Response-Team-Direction-Paradigm-Shift-in-Cyber-Incident-Reporting — `verified` · Doc refs: P7-7, IN-60
9. Mondaq. "Digital Personal Data Protection Rules, 2025 Notified" (notification 13 Nov 2025; phased commencement; Rule 8; 72-hour breach reporting). https://www.mondaq.com/india/data-protection/1708164/digital-personal-data-protection-rules-2025-notified — `verified` · Doc refs: P9-24
10. NALSAR Tech Law Forum. "Privacy with a footnote: data retention under the DPDP framework" (s.8(7)). 2025. https://techlawforum.nalsar.ac.in/privacy-with-a-footnote-data-retention-under-the-dpdp-framework/ — `snippet` · Doc refs: P7-4
11. National Crime Records Bureau. "Flyers on New Criminal Laws" (ZIP). https://www.ncrb.gov.in/uploads/files/flyers-26022024.zip — `verified` · Doc refs: IN-45
12. National e-Governance Division (MeitY). "Nyaykosh: Law as Code." https://negd.gov.in/our_projects/nyaykosh-law-as-code/ — `verified` (by P1) · Doc refs: P1-34, IN-71
13. Protiviti. "Flash compliance update: DPDP Rules 2025" (Rules 6, 7; processors; commencement). Nov 2025. https://www.protiviti.com/sites/default/files/2025-11/flash_compliance_update_dpdp_rules-2025.pdf — `snippet` · Doc refs: P7-6
14. Rajya Sabha. Answer to question, 25 July 2024 (eCourts: 26.044 crore cases; 26.047 crore orders/judgments). https://rsdebate.nic.in/bitstream/123456789/749688/1/PQ_265_25072024_U425_p410_p415.pdf — `snippet` · Doc refs: P0-13
15. S.S. Rana & Co. "MeitY Notifies Final Digital Personal Data Protection Rules 2025" (G.S.R. 846(E), 13 Nov 2025; 72-hour breach report; Rule 8 one-year minimum retention of personal data, traffic data and logs; 18-month tranche 13 May 2027). 2025. https://ssrana.in/articles/meity-notifies-final-digital-personal-data-protection-rules-2025/ — `verified` · Doc refs: P7-2
16. Supreme Court of India. SUPACE (2021) and SUVAS (2019) AI tools. No URL verified. — `unverified` · Doc refs: CT-52
17. Taxmann / TCSA. "Cross-border data transfers under the DPDP Act 2023" (s.16 negative list; s.16(2); s.16 + Rule 15 commencement 13 May 2027). https://www.taxmann.com/post/blog/cross-border-data-transfers-under-the-dpdp-act/ ; https://www.tcsa.in/frameworks/dpdp/cross-border-transfer — `snippet` · Doc refs: XC-37

## 5. Products, vendors & pricing

*Scope:* Vendor-authored material: legal-AI and legal-research products, sponsored posts, model/API providers' pricing, residency and availability pages, cloud price lists, and hosted OCR/embedding/rerank services. (86 sources.)

1. Adalat AI. Homepage. https://adalat.ai — `verified` · Doc refs: CT-24
2. Amazon Web Services. "Amazon Textract: Best Practices" (supported languages). https://docs.aws.amazon.com/textract/latest/dg/textract-best-practices.html — `verified` · Doc refs: P1-12
3. Anthropic. "Data residency." Claude Platform Docs, retrieved 2026-09-30. https://platform.claude.com/docs/en/manage-claude/data-residency — `verified` · Doc refs: XC-2
4. Anthropic. "Pricing." Claude Platform Docs, retrieved 2026-09-30. https://platform.claude.com/docs/en/about-claude/pricing — `verified` · Doc refs: XC-1
5. AWS. "Access Anthropic Claude models in India on Amazon Bedrock with Global cross-Region inference." AWS ML Blog, 2026-03-09. https://aws.amazon.com/blogs/machine-learning/access-anthropic-claude-models-in-india-on-amazon-bedrock-with-global-cross-region-inference — `verified` · Doc refs: XC-6
6. AWS. "Amazon Textract FAQs" (languages: English, German, French, Spanish, Italian, Portuguese). https://aws.amazon.com/textract/faqs/ — `verified` · Doc refs: XC-24
7. AWS. "Introducing OpenAI models on Amazon Bedrock for in-country inferencing in India." AWS ML Blog, 2026-08-27. https://aws.amazon.com/blogs/machine-learning/introducing-openai-models-on-amazon-bedrock-for-in-country-inferencing-in-india/ — `verified` · Doc refs: XC-7
8. AWS. Price List API, Amazon OpenSearch Service, ap-south-1 (r7g.2xlarge.search $0.498/h; or2.2xlarge.search $0.562/h). retrieved 2026-09-30. https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonES/current/ap-south-1/index.csv — `verified` · Doc refs: XC-21
9. AWS. Price List API, Amazon RDS PostgreSQL, ap-south-1 (db.r7g.2xlarge Multi-AZ $2.176/h; db.r7g.4xlarge Multi-AZ $4.352/h). retrieved 2026-09-30. https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/ap-south-1/index.csv — `verified` · Doc refs: XC-23
10. AWS. Price List API, Amazon Textract, ap-south-1 (DetectDocumentText $1.50/1K pages ≤1M, $0.60 beyond; Layout $4→$3/1K). retrieved 2026-09-30. https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonTextract/current/ap-south-1/index.csv — `verified` · Doc refs: XC-22
11. AWS. Price List API, AmazonEC2, ap-south-1 (g6e.xlarge $2.235/h). Retrieved 30 Sep 2026. https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-south-1/index.csv — `verified` (sibling XC-20) · Doc refs: P8-72, XC-20
12. AWS. Price List API, AmazonS3, ap-south-1 (S3 Standard $0.025/GB-mo first 50 TB; Standard-IA $0.0138). retrieved 2026-09-30. https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/ap-south-1/index.json — `verified` · Doc refs: XC-19
13. Bar & Bench (sponsored, CaseMine). "CaseMine launches AI-powered legal assistant AMICUS." 18 Jul 2023. https://www.barandbench.com/news/casemine-launches-ai-powered-legal-assistant-amicus — `verified` · Doc refs: CT-9
14. Bar & Bench (sponsored, Manupatra). "Why Legal Research demands more than Raw AI." 18 Dec 2025. https://www.barandbench.com/news/why-legal-research-demands-more-than-raw-ai — `verified` (via CT-4) · Doc refs: P10-32, CT-4
15. Bharat.Law (competitor-authored). "Best AI legal research tools India 2026." https://bharat.law/resources/best-ai-legal-research-tools-india-2026 — `verified` (biased) · Doc refs: CT-17
16. Bharat.Law. Homepage (NyaI Research, India Courts). https://bharat.law — `verified` · Doc refs: CT-16
17. CaseMine. "FAQ / About" (citator; CaseIQ; AMICUS). https://www.casemine.com/home/faq — `snippet` · Doc refs: P3-26
18. CLAW. Homepage. https://www.clawlaw.in — `verified` · Doc refs: P10-26, CT-22
19. Clio. "Clio Completes Landmark $1B vLex Acquisition and Announces $500M Series G Funding Round at $5B Valuation." 10 Nov 2025. https://www.clio.com/about/press/clio-completes-landmark-1b-vlex-acquisition-series-g-5b-valuation/ — `snippet` · Doc refs: CT-41
20. Cohere. "Cohere's Embed Models" (Embed v4). Docs. https://docs.cohere.com/docs/cohere-embed — `verified` · Doc refs: P2-15
21. Cohere. "Pricing" (Model Vault dedicated Embed/Rerank hourly pricing). https://cohere.com/pricing — `verified` · Doc refs: P5-28, XC-14
22. Cohere. "Rerank v4.0 Pro / Fast" (released 11 Dec 2025; 32k context; per-search pricing). Model listings: https://vercel.com/ai-gateway/models/rerank-v4-pro/faq ; https://docs.pinecone.io/models/cohere-rerank-4-fast ; search-unit definition: https://cohere.com/pricing — `verified` · Doc refs: P5-28
23. E2E Networks. "Pricing" (L40S ₹102/h ex-GST). Retrieved 30 Sep 2026. https://www.e2enetworks.com/pricing.md — `verified` (sibling XC-26) · Doc refs: P8-73, XC-26
24. Google Cloud. "Data residency — Generative AI on Vertex AI" (Claude APAC regional endpoints Singapore/Taiwan). https://cloud.google.com/vertex-ai/generative-ai/docs/learn/data-residency — `snippet` · Doc refs: XC-9
25. Google Cloud. "Document AI pricing" and "Enterprise Document OCR supported languages." https://cloud.google.com/document-ai/pricing ; https://docs.cloud.google.com/document-ai/docs/process-forms — `snippet` · Doc refs: P1-11
26. Google Cloud. "Generative AI on Vertex AI locations" (asia-south1 Gemini 2.5 models; regional ML processing). https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations — `snippet` · Doc refs: XC-10
27. Google. "Embeddings" (gemini-embedding-001: 2,048 tokens; gemini-embedding-2: 8,192 tokens). Gemini API docs. https://ai.google.dev/gemini-api/docs/embeddings — `verified` · Doc refs: P2-16
28. Google. "Gemini Developer API pricing." retrieved 2026-09-30. https://ai.google.dev/gemini-api/docs/pricing — `verified` · Doc refs: XC-4
29. Harvey. "Harvey and Intapp ethical walls" (GA 23 Jul 2026; enforcement across Threads, Vault, Review Tables, Shared Spaces; block when access cannot be confirmed). https://www.harvey.ai/blog/harvey-intapp-ethical-walls — `verified` · Doc refs: P7-13
30. Harvey. "Harvey raises growth round at $11 billion valuation co-led by GIC and Sequoia." 25 Mar 2026. https://www.harvey.ai/fr-FR/blog/harvey-raises-growth-round-at-dollar11-billion-valuation-co-led-by-gic-and-sequoia — `verified` · Doc refs: CT-29
31. Harvey. "Harvey to Expand Team with New Bengaluru Office." 10 Jul 2025. https://www.harvey.ai/blog/harvey-to-expand-team-with-new-bengaluru-office — `snippet` · Doc refs: CT-28
32. Harvey. "Introducing BigLaw Bench." 2024. https://www.harvey.ai/blog/introducing-biglaw-bench — `verified` · Doc refs: P6-25, P8-11
33. Harvey. "Introducing Workflow Builder" (Agent Builder). 24 Jun 2025. https://www.harvey.ai/en-US/blog/introducing-workflow-builder — `verified` · Doc refs: P6-26
34. Harvey. "Memory is here: Harvey, personalized." Harvey blog, Aug 2026. https://www.harvey.ai/blog/memory-is-here-harvey-personalized — `verified` · Doc refs: P9-16
35. Harvey. "Security" (zero data retention required of model providers; no training of underlying models on inputs, outputs or uploaded documents; customer-set retention). https://www.harvey.ai/security — `verified` (review: replaced login-walled help-centre URL) · Doc refs: P9-17
36. Indian Kanoon IKademy. "Prism AI for Legal Practice: Mastering Indian Kanoon's Smart Tools." https://indiankanoon.org/ikademy/prism-ai-for-legal-practice-mastering-indian-kanoons-smart-tools/ — `verified` · Doc refs: CT-8
37. Indian Kanoon. "API pricing." https://api.indiankanoon.org/pricing/ — `verified` · Doc refs: P0-16
38. Indian Kanoon. "API Service Description / Terms." https://api.indiankanoon.org/terms/ — `verified` · Doc refs: P0-15, IN-64
39. Indian Kanoon. "Prism pricing." https://indiankanoon.org/prism/pricing/ — `verified` · Doc refs: P10-25, CT-7
40. Indian Kanoon. Document pages and search results showing "Cites / Cited by" counts (e.g., Shreya Singhal). https://indiankanoon.org/doc/110813550/ — `verified` · Doc refs: P3-27
41. Isaacus. "Kanon 2 Embedder & Kanon Universal Classifier" (SageMaker model package). AWS Marketplace. https://aws.amazon.com/marketplace/pp/prodview-lquokmsovgpsm — `verified` · Doc refs: P2-18
42. jhana. Homepage ("Neoeconomica by jhana"). https://jhana.ai — `verified` · Doc refs: CT-13
43. Kapoor, D. (Manupatra). "Why Native Legal AI is Required for India." Artificial Lawyer (sponsored), 2 Apr 2026. https://artificiallawyer.com/2026/04/02/why-native-legal-ai-is-required-for-india — `verified` · Doc refs: CT-6
44. LawCentral AI. Homepage and pricing. https://www.lawcentral.ai — `verified` · Doc refs: CT-23
45. Legal Technology Hub. "CaseMine" vendor profile (CaseIQ, Parallel Search). https://www.legaltechnologyhub.com/vendors/casemine/ — `snippet` · Doc refs: CT-11
46. Legal Technology Hub. "jhana" vendor profile (Searcher, Paralegal). https://www.legaltechnologyhub.com/vendors/jhana/ — `snippet` · Doc refs: CT-15
47. Legal Technology Hub. "ManuWorks by Manupatra" vendor profile. https://www.legaltechnologyhub.com/vendors/manuworks-by-manupatra/ — `verified` · Doc refs: CT-5
48. LegitQuest. Homepage (LIBIL, Patrol, research). https://www.legitquest.com — `verified` (re-fetched 30 Sep 2026) · Doc refs: P10-34, CT-12
49. LexisNexis / Harvey. "LexisNexis and Harvey announce strategic alliance…" 18 Jun 2025. https://www.lexisnexis.com/community/pressroom/b/news/posts/lexisnexis-and-harvey-announce-strategic-alliance-to-integrate-trusted-high-quality-ai-technology-and-legal-content-and-develop-advanced-workflows — `verified` · Doc refs: CT-34
50. LexisNexis. "Introducing LexisNexis Protégé, the next generation of personalised legal AI for lawyers." 25 June 2025. https://www.lexisnexis.com/blogs/en-au/insights/introducing-lexisnexis-protege-the-next-generation-of-personalised-legal-ai-for-lawyers — `verified` · Doc refs: P9-19
51. Lexlegis.ai. Homepage and pricing. https://lexlegis.ai — `verified` · Doc refs: CT-18
52. Manupatra training manual (Kerala Law Academy library mirror): Manu Cite shows citation counts and "the treatment of the subject case in other cases"; Authority Check / Case Map pages not opened. https://manupatrafast.library.keralalawacademy.in/Defaults/training-manual-manu-cite-feature.aspx — `verified` · Doc refs: P3-25
53. Meta for Developers. "Pricing on the WhatsApp Business Platform" (per-message pricing from 1 Jul 2025; free utility templates in open service window; India INR billing from 1 Jan 2026 and higher India marketing rate). https://developers.facebook.com/docs/whatsapp/pricing/ — `verified` · Doc refs: P10-13
54. Microsoft India. "AI First Movers: SCC Online." Microsoft, FY26. https://www.microsoft.com/en-in/aifirstmovers/fy26scconline — `verified` · Doc refs: CT-3
55. Microsoft. "Region availability for Foundry Models sold by Azure." Microsoft Learn, updated 2026-09-04. https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure-region-availability — `verified` · Doc refs: XC-8
56. Midpage. Homepage. https://midpage.ai — `verified` · Doc refs: CT-46
57. Mistral AI. "Mistral OCR" (2025; ~1,000 pages/US$, ~2× with batch; selective self-hosting; Hindi in vendor benchmark), https://mistral.ai/news/mistral-ocr — `verified` · Doc refs: P1-13
58. NyaySaathi. Homepage. https://www.nyaysaathi.com — `verified` · Doc refs: CT-21
59. OpenAI. "Data controls in the OpenAI platform" (data residency table: India storage Yes / processing No). retrieved 2026-09-30. https://developers.openai.com/api/docs/guides/your-data — `verified` · Doc refs: XC-5, IN-68
60. OpenAI. "Pricing." OpenAI API Docs, retrieved 2026-09-30. https://developers.openai.com/api/docs/pricing — `verified` · Doc refs: XC-3
61. Paxton. Homepage ("matter record, legal research, final work product live in separate workflows"). https://paxton.ai — `verified` (via CT-45) · Doc refs: P10-24, CT-45
62. Provakil app listing (automatic case updates from 10,000+ courts; daily cause lists). Apple App Store. https://apps.apple.com/mx/app/provakil/id1111933293 — `snippet` · Doc refs: P7-17, P10-31
63. Sarvam AI. "Sarvam Vision 2.1: Pushing the Pareto frontier of document intelligence." Blog, 24 Sept 2026 (olmOCR-Bench 87.3; Indic OCR benchmark 6,909 samples / 22 languages, 87.39% vs Bodhan 84.94%, Gemini 3.6 Flash 79.35%, Google Cloud Vision 71.76%; OmniDocBench v1.6: PaddleOCR-VL 1.6 96.01, Sarvam 94.97, GLM-OCR 94.71). https://www.sarvam.ai/blogs/sarvam-vision-2-1 — `verified` · Doc refs: P1-9
64. Sarvam AI. "Sarvam Vision." Blog, Feb 2026. https://www.sarvam.ai/blogs/sarvam-vision — `snippet` · Doc refs: P1-10
65. SCC Online. "Legal Research, Reimagined: SCC Online® AI Pro in Action at Vinsys Webinar." SCC Online Blog, 28 Apr 2026. https://www.scconline.com/blog/post/2026/04/28/scc-online-ai-pro-demo-legal-research-to-reasoning-vinsys/ — `verified` · Doc refs: CT-2
66. SCC Online. "SCC Online® AI Pro" (Republic Day announcement). SCC Online Blog, 26 Jan 2026. https://www.scconline.com/blog/post/2026/01/26/scc-online-ai-pro-republic-day-announcement/ — `verified` · Doc refs: CT-1
67. SCC Times (SCC Online Blog). Legal RoundUp formats (Supreme Court, High Courts, Legislation, Tribunals monthly, Topic-wise, Weekly). Accessed 30 Sep 2026. https://www.scconline.com/blog/ — `verified` · Doc refs: P10-17
68. Search-result snippet attributing "Rs. 48,500/user/year + 18% GST, separate add-on, Feb 2026 preview" to SCC Online AI Pro (vaquill.ai/alternative/scc-online). The fetched page did not contain the claim. — `unverified` · Doc refs: CT-55
69. Spellbook. Homepage (Word integration; "every suggestion tracked"; 5,000+ legal teams, self-reported). https://spellbook.com/ — `verified` (self-claims) · Doc refs: P10-5
70. Thomson Reuters / Legal Current. "Thomson Reuters Builds on Legacy of Innovation with Continued AI Investment" (editorial review of machine tags fed back to models). https://www.legalcurrent.com/thomson-reuters-builds-on-legacy-of-innovation-with-continued-ai-investment/ (now redirects to https://www.thomsonreuters.com/en-us/posts/innovation/) — `snippet` · Doc refs: P9-20
71. Thomson Reuters. "CoCounsel" product and data-handling statements (user content and prompts not used to train or improve CoCounsel or LLMs; zero-retention API calls). https://www.thomsonreuters.com/en/cocounsel — `verified` · Doc refs: P9-18
72. Thomson Reuters. "KeyCite flags and icons for cases." Westlaw Edge help. https://www.thomsonreuters.com/en-ca/help/westlaw-edge/tools/keycite/flags-and-icons.html — `snippet` · Doc refs: P3-18
73. Thomson Reuters. "KeyCite" product page (red/yellow/blue-striped flags, Overruling Risk quote, KeyCite Alerts). https://legal.thomsonreuters.com/en/products/westlaw/keycite — `verified` (flag definitions only summarised; blue-striped meaning unverified) · Doc refs: P10-2
74. Thomson Reuters. "Quickly uncover implied overrulings with KeyCite Overruling Risk." https://legal.thomsonreuters.com/en/insights/articles/quickly-uncover-implied-overrulings-with-keycite-overruling-risk — `verified` · Doc refs: P3-19, P4-8
75. Thomson Reuters. "Thomson Reuters launches CoCounsel Legal, transforming legal work with agentic AI and deep research." Press release, 5 Aug 2025. https://www.thomsonreuters.com/en/press-releases/2025/august/thomson-reuters-launches-cocounsel-legal-transforming-legal-work-with-agentic-ai-and-deep-research — `verified` (no run-time or Westlaw Advantage launch date stated) · Doc refs: P6-21, CT-36
76. Thomson Reuters. "Westlaw Edge Quick Check" product page. https://legal.thomsonreuters.com/en/products/westlaw-edge/quick-check — `verified` · Doc refs: P5-34
77. Vaquill (competitor-authored). "Harvey AI Review 2026: Honest Take + What It Really Costs." https://www.vaquill.ai/blog/harvey-ai-review-honest-assessment — `snippet` (unverified pricing) · Doc refs: CT-33
78. Vaquill. Homepage (US primary-law API). https://www.vaquill.ai — `verified` · Doc refs: CT-47
79. Various. IndiaAI Mission compute subsidised rates (≈₹92/h H100-class; ≈₹67/GPU-h). e.g. https://huggingface.co/blog/daya-shankar/nvidia-h100-price-india ; https://dev.to/mr_manushukla/gpu-cloud-pricing-in-india-2026-h100-h200-and-b200-rates-compared-bo7 — `snippet` · Doc refs: XC-27
80. vLex. "Vincent AI." https://vlex.com/vincent-ai — `verified` · Doc refs: CT-42
81. vLex/Clio. "Clio Signs Definitive Agreement to Acquire vLex for US $1 Billion." 30 Jun 2025. https://vlex.com/news/Clio-Signs-Definitive-Agreement-to-Acquire-vLex — `snippet` · Doc refs: P6-28
82. Voyage AI / MongoDB. "rerank-2.5 and rerank-2.5-lite: instruction-following rerankers." Aug 2025. https://mongodb.com/company/blog/product-release-announcements/rerank-2-5-and-rerank-2-5-lite-instruction-following-rerankers — `verified` (11 Aug 2025; +7.94% vs Cohere v3.5 on 93 datasets; 32k) · Doc refs: P5-29
83. Voyage AI. "Embeddings" documentation (voyage-4 family, voyage-law-2). 2026. https://docs.voyageai.com/docs/embeddings — `verified` · Doc refs: P2-13
84. Voyage AI. "Pricing." retrieved 2026-09-30. https://docs.voyageai.com/docs/pricing — `verified` · Doc refs: XC-11
85. Voyage AI. "voyage-context-3: focused chunk-level details with global document context." Blog, 2025. https://blog.voyageai.com/2025/07/23/voyage-context-3/ — `verified` · Doc refs: P2-14
86. WhatsApp. "WhatsApp Business Messaging Policy" (opt-in, opt-out, sensitive identifiers). https://whatsappbusiness.com/policy/ — `verified` · Doc refs: P10-14

## 6. Engineering (databases, infrastructure, standards/RFCs, OSS)

*Scope:* Databases, search engines, stream/workflow engines, cloud infrastructure docs, standards and specifications (IETF, W3C, OASIS, ISO, CNCF), open-source repositories and open-weight model cards, and engineering blogs. (107 sources.)

1. Allen Institute for AI. "olmOCR" GitHub repository (v0.4.0, Oct 2025; 7B Qwen2.5-VL; olmOCR-Bench 82.4; < $200 per million pages; English-only filter; Apache-2.0). https://github.com/allenai/olmocr — `verified` · Doc refs: P1-1
2. Anthropic. "Building effective agents." Dec 2024. https://www.anthropic.com/engineering/building-effective-agents — `verified` · Doc refs: P6-7
3. Anthropic. "How we built our multi-agent research system." 2025. https://www.anthropic.com/engineering/multi-agent-research-system — `verified` · Doc refs: P6-6
4. Anthropic. "Introducing Contextual Retrieval." 2024. https://www.anthropic.com/news/contextual-retrieval — `verified` · Doc refs: P2-1, P5-25
5. Apache Flink. "Timely Stream Processing" (watermarks). https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/ — `verified` · Doc refs: P4-32
6. Apache Kafka. "Apache Kafka 4.0.0 Release Announcement." 18 Mar 2025. https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/ — `verified` · Doc refs: P4-13
7. Apache Kafka. "Apache Kafka 4.1.0 Release Announcement." 4 Sep 2025 (KIP-932 "now in preview … still not ready for production"). https://kafka.apache.org/blog/2025/09/04/apache-kafka-4.1.0-release-announcement/ — `verified` · Doc refs: P4-48
8. Apache Kafka. "Apache Kafka 4.2.0 Release Announcement." 17 Feb 2026 ("Kafka Queues (Share Groups) is now production-ready"). https://kafka.apache.org/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/ — `verified` · Doc refs: P4-47
9. Apache Kafka. Blog index (4.1.0, 4 Sep 2025; 4.2.0, 17 Feb 2026; 4.3.0, 22 May 2026). https://kafka.apache.org/blog — `verified` · Doc refs: P4-14
10. Apache Software Foundation. "Apache AGE." https://age.apache.org/ — `verified` · Doc refs: P3-45
11. ArangoDB. "Update: Evolving ArangoDB's Licensing Model for a Sustainable Future." 2024. https://arango.ai/blog/update-evolving-arangodbs-licensing-model-for-a-sustainable-future — `verified` · Doc refs: P3-47
12. AutomationAtlas. "Temporal vs Apache Airflow 2026: Durable Workflows vs DAG Orchestration." 2026. https://automationatlas.io/guides/temporal-vs-apache-airflow-2026-comparison/ — `snippet` · Doc refs: P0-32
13. AWS Prescriptive Guidance. "Row-level security recommendations" (multi-tenant PostgreSQL). https://docs.aws.amazon.com/prescriptive-guidance/latest/saas-multitenant-managed-postgresql/rls.html — `verified` · Doc refs: P7-26
14. AWS. "Amazon OpenSearch Service endpoints and quotas" (ap-south-1, ap-south-2). https://docs.aws.amazon.com/general/latest/gr/opensearch-service.html — `verified` · Doc refs: P2-35
15. AWS. "External key stores" (HYOK, XKS proxy, double encryption, availability caveats). AWS KMS Developer Guide. https://docs.aws.amazon.com/kms/latest/developerguide/keystore-external.html — `verified` · Doc refs: P7-34
16. AWS. "Locking objects with Object Lock" (WORM, governance vs compliance mode, legal hold, Cohasset assessment). Amazon S3 User Guide. https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html — `verified` · Doc refs: P7-33
17. AWS. "Silo, Pool, and Bridge Models." AWS Well-Architected SaaS Lens. https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html — `snippet` · Doc refs: P7-25
18. BAAI. "bge-reranker-v2-m3" model documentation. https://bge-model.com/_sources/bge/bge_reranker_v2.rst.txt — `snippet` · Doc refs: P5-30
19. Beyer, B. et al. (eds). "Monitoring Distributed Systems." Site Reliability Engineering, Google/O'Reilly, 2016. https://sre.google/sre-book/monitoring-distributed-systems/ — `verified` · Doc refs: P4-31
20. Brandur. "Implementing Stripe-like Idempotency Keys in Postgres." 2017. https://brandur.org/idempotency-keys — `verified` · Doc refs: P4-29
21. CNCF CloudEvents. "CloudEvents — Version 1.0 specification", Attribute Naming Convention. https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md — `verified` · Doc refs: P4-10, XC-44 · Also at: https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
22. CNCF. "OpenFGA becomes a CNCF incubating project." 11 Nov 2025. https://www.cncf.io/blog/2025/11/11/openfga-becomes-a-cncf-incubating-project/ — `verified` · Doc refs: P7-30
23. Cognition. "Don't Build Multi-Agents." 2025. https://cognition.com/blog/dont-build-multi-agents — `verified` · Doc refs: P6-8
24. Datalab. "Surya" GitHub repository (650M; 91 languages, 87.2% internal multilingual benchmark; olmOCR-Bench 83.3; ~5 pages/s RTX 5090; code Apache-2.0, weights modified AI Pubs OpenRAIL-M — free for research/personal/startups < US$5M funding or revenue). https://github.com/datalab-to/surya — `verified` · Doc refs: P1-7
25. DBOS, Inc. "DBOS Transact (Python)." GitHub, MIT. https://github.com/dbos-inc/dbos-transact-py — `verified` · Doc refs: P4-17
26. Debezium. "Outbox Event Router." Documentation. https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html — `verified` · Doc refs: P4-11
27. Elastic. "Elasticsearch is Open Source. Again!" Blog, 29 Aug 2024. https://www.elastic.co/blog/elasticsearch-is-open-source-again — `verified` · Doc refs: P2-36
28. Elastic. "Update a document" API reference. https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update.html — `verified` · Doc refs: P2-37
29. FalkorDB. GitHub repository (SSPLv1; GraphBLAS). https://github.com/FalkorDB/FalkorDB — `verified` · Doc refs: P3-48
30. Feldera. "Feldera: incremental computation engine" (MIT). https://github.com/feldera/feldera — `verified` · Doc refs: P4-23
31. Free Law Project. "Citation depth data." 2020. https://free.law/2020/03/05/citation-depth-data/ — `snippet` · Doc refs: P3-23
32. Free Law Project. "CourtListener Citation Lookup API" (v4; 18,128,182 citations; uses eyecite). https://wiki.free.law/c/courtlistener/help/api/rest/v4/citation-lookup — `verified` · Doc refs: P3-21
33. Free Law Project. "eyecite" GitHub repository (reporters_db from >55M citations; Aho-Corasick default / Hyperscan tokenizer; resolve/annotate; BSD-2-Clause). https://github.com/freelawproject/eyecite — `verified` · Doc refs: P1-27
34. Free Law Project. "Juriscraper" project page. https://free.law/projects/juriscraper — `verified` · Doc refs: P0-26
35. Free Law Project. "juriscraper." GitHub. https://github.com/freelawproject/juriscraper — `verified` · Doc refs: P0-25
36. GitHub. "Scientist: a Ruby library for carefully refactoring critical paths." https://github.com/github/scientist — `verified` · Doc refs: P4-30
37. Google Cloud. "Spanner Graph overview." https://docs.cloud.google.com/spanner/docs/graph/overview — `verified` · Doc refs: P3-49
38. Harvard Library Innovation Lab. "Perma Tools / Scoop." https://tools.perma.cc — `snippet` · Doc refs: P0-42
39. Hoekstra, R. et al. "LKIF Core ontology" (Estrella). GitHub. https://github.com/RinkeHoekstra/lkif-core — `verified` · Doc refs: P3-35
40. iamshouvikmitra. "bharat-courts 0.3.1 (async client for eCourts/HC/SCI; built-in OCR and ONNX CAPTCHA solvers; AWS archive client)." PyPI, 2026. https://pypi.org/project/bharat-courts/0.3.1/ (metadata via https://pypi.org/pypi/bharat-courts/0.3.1/json) — `verified` · Doc refs: P0-4
41. IETF. RFC 8785 "JSON Canonicalization Scheme (JCS)." 2020. https://www.rfc-editor.org/rfc/rfc8785 — `unverified` · Doc refs: P0-39
42. IETF. RFC 9110 "HTTP Semantics" (conditional requests, ETag, Last-Modified). 2022. https://www.rfc-editor.org/rfc/rfc9110 — `unverified` (not fetched this session) · Doc refs: P0-38
43. IFLA. "LRMoo: object-oriented definition and mapping from the IFLA Library Reference Model" v1.0, 2024-12-09. https://repository.ifla.org/handle/20.500.14598/3677 — `verified` · Doc refs: P3-32
44. ISO 28500:2017 "Information and documentation — WARC file format." https://www.iso.org/standard/68004.html — `unverified` · Doc refs: P0-40
45. Jina AI. "jina-embeddings-v3" model card (license cc-by-nc-4.0). Hugging Face. https://huggingface.co/jinaai/jina-embeddings-v3 — `verified` · Doc refs: P2-17
46. Jina AI. "jina-reranker-v3: 0.6B Listwise Reranker for SOTA Multilingual Retrieval." 2025. https://jina.ai/news/jina-reranker-v3-0-6b-listwise-reranker-for-sota-multilingual-retrieval/ ; licence: https://huggingface.co/jinaai/jina-reranker-v3 — `verified` (BEIR 61.94, MIRACL 66.83, 131k context; CC BY-NC 4.0) · Doc refs: P5-31
47. Kreps, J. "Questioning the Lambda Architecture." O'Reilly Radar, 2 Jul 2014. https://www.oreilly.com/radar/questioning-the-lambda-architecture/ — `verified` · Doc refs: P4-27
48. Kùzu. GitHub repository (archived 10 Oct 2025). https://github.com/kuzudb/kuzu — `verified` · Doc refs: P3-44
49. Langfuse. "Self-hosting" (OSS; PostgreSQL, ClickHouse, Redis/Valkey, S3; EE features). https://langfuse.com/self-hosting — `verified` · Doc refs: XC-40
50. Library of Congress. "Sustainability of Digital Formats: WACZ." https://loc.gov/preservation/digital/formats/fdd/fdd000586.shtml — `snippet` · Doc refs: P0-29
51. libyal. "libpff" (PST/OST/PAB; LGPL-3.0; pypff; alpha). GitHub. https://github.com/libyal/libpff — `verified` · Doc refs: P7-35
52. LightGBM. "Parameters: objective=lambdarank; monotone_constraints; monotone_constraints_method." https://lightgbm.readthedocs.io/en/latest/Parameters.html — `verified` · Doc refs: P5-37
53. Memgraph. GitHub repository (BSL / MEL licences). https://github.com/memgraph/memgraph — `verified` · Doc refs: P3-46
54. Meta for Developers. "Cloud API — Local storage" (data at rest in selected country incl. India; in-use processing internationally up to 60 min). https://developers.facebook.com/docs/whatsapp/cloud-api/overview/local-storage — `verified` · Doc refs: P10-15
55. Microsoft Learn. "Requirements to use centralized deployment for Office Add-ins." Updated 2026. https://learn.microsoft.com/en-us/microsoft-365/admin/manage/centralized-deployment-of-add-ins — `verified` · Doc refs: P10-7
56. Microsoft Learn. "Word add-ins overview." Updated 2026. https://learn.microsoft.com/en-us/office/dev/add-ins/word/word-add-ins-programming-overview — `verified` · Doc refs: P10-6
57. Microsoft Research. "LazyGraphRAG: Setting a new standard for quality and cost." Blog, 2024. https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/ — `verified` · Doc refs: P3-7
58. Neo4j. "Licensing." https://neo4j.com/licensing/ — `verified` · Doc refs: P3-42
59. Neo4j. "Operations Manual — Introduction (edition feature comparison; online backup, clustering, RBAC, property/sub-graph access control EE-only; multiple databases in all editions)." https://neo4j.com/docs/operations-manual/current/introduction/ — `verified` · Doc refs: P3-43
60. OASIS LegalDocML TC. "Akoma Ntoso Version 1.0" OASIS Standard, 29 Aug 2018. https://www.oasis-open.org/standard/akn-v1-0/ — `verified` · Doc refs: P1-36, P3-31 · Also at: https://docs.oasis-open.org/legaldocml/akn-core/v1.0/
61. OASIS LegalRuleML TC. "LegalRuleML Core Specification Version 1.0" OASIS Standard, 30 Aug 2021. https://www.oasis-open.org/standard/legalruleml-core-specification-version-1-0/ — `verified` · Doc refs: P3-36
62. OpenFGA. "Configuring OpenFGA" (listObjectsMaxResults default 1000; listObjectsDeadline default 3s). openfga.dev. https://openfga.dev/docs/getting-started/setup-openfga/configuration — `verified` · Doc refs: P7-37
63. OpenLineage. "Object Model." https://openlineage.io/docs/spec/object-model — `verified` · Doc refs: P4-33
64. OpenSearch Project. "Disk-based vector search" (on_disk mode). Documentation. https://github.com/opensearch-project/documentation-website/blob/main/_vector-search/optimizing-storage/disk-based-vector-search.md — `verified` · Doc refs: P2-29
65. OpenSearch Project. "Index document API" (version_type external). Documentation. https://github.com/opensearch-project/documentation-website/blob/main/_api-reference/document-apis/index-document.md — `verified` · Doc refs: P2-33
66. OpenSearch Project. "Introducing reciprocal rank fusion for hybrid search." OpenSearch blog, 2025 (OpenSearch 2.19). https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/ — `verified` · Doc refs: P5-3
67. OpenSearch Project. "Language analyzers." Documentation. https://github.com/opensearch-project/documentation-website/blob/main/_analyzers/language-analyzers/index.md — `verified` · Doc refs: P2-34
68. OpenSearch Project. "Neural sparse ANN search" (SEISMIC, 3.3). Documentation. https://github.com/opensearch-project/documentation-website/blob/main/_vector-search/ai-search/neural-sparse-ann.md — `verified` · Doc refs: P2-32
69. OpenSearch Project. "Pretrained models" (neural sparse, incl. multilingual-v1). Documentation. https://github.com/opensearch-project/documentation-website/blob/main/_ml-commons-plugin/pretrained-models.md — `verified` · Doc refs: P2-31
70. OpenSearch Project. "Score ranker processor" (RRF, 2.19). Documentation. https://github.com/opensearch-project/documentation-website/blob/main/_search-plugins/search-pipelines/score-ranker-processor.md — `verified` · Doc refs: P2-30
71. OpenSearch Software Foundation (a Linux Foundation project). https://opensearch.org/foundation/ — `verified` · Doc refs: P2-53
72. OpenTelemetry. "GenAI semantic conventions" (moved to open-telemetry/semantic-conventions-genai). https://opentelemetry.io/docs/specs/semconv/gen-ai/ ; https://github.com/open-telemetry/semantic-conventions-genai — `verified` · Doc refs: XC-39
73. OWASP Gen AI Security Project. "LLM01:2025 Prompt Injection" (and 2025 list incl. LLM02, LLM08). https://genai.owasp.org/llmrisk/llm01-prompt-injection/ — `verified` · Doc refs: P7-19
74. OWASP GenAI Security Project. "OWASP Top 10 for Agentic Applications 2026" (9 Dec 2025; ASI01–ASI10). https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ — `verified` (release date); snippet (ASI item names) · Doc refs: XC-31
75. OWASP GenAI Security Project. "OWASP Top 10 for LLM Applications 2025" (v2.0, 18 Nov 2024). https://genai.owasp.org/llm-top-10/ — `verified` · Doc refs: XC-30
76. pg_trickle project blog. "Multi-tenant vector search with RLS" (filtered HNSW pitfalls; ~10× wasted work for small tenants). PGXN. https://pgxn.org/dist/pg_trickle/0.36.0/blog/multi-tenant-vector-search-rls.html — `verified` · Doc refs: P7-27
77. PostgreSQL Global Development Group. "PostgreSQL 18 Release Notes" (25 Sep 2025). https://www.postgresql.org/docs/18/release-18.html — `verified` · Doc refs: P3-40
78. PostgreSQL Global Development Group. "PostgreSQL 19 Release Notes (devel, beta 4)." accessed 2026-09-30. https://www.postgresql.org/docs/devel/release-19.html — `verified` · Doc refs: P3-41
79. Presidio. "Supported entities." https://presidio.dataprivacystack.org/supported_entities/ — `verified` · Doc refs: P9-27
80. Qdrant. "BM42: New Baseline for Hybrid Search" (with post-publication correction). 2024. https://qdrant.tech/articles/bm42/ — `verified` · Doc refs: P2-40
81. Qdrant. "Multitenancy" guide (is_tenant, m=0/payload_m=16, tiered multitenancy, ~20,000-point promotion threshold). https://qdrant.tech/documentation/guides/multiple-partitions/ — `verified` · Doc refs: P7-28
82. Qwen Team. "Qwen3-235B-A22B" model card, Hugging Face. https://huggingface.co/Qwen/Qwen3-235B-A22B — `verified` · Doc refs: XC-13
83. Qwen Team. "Qwen3-Embedding-4B" model card. Hugging Face, 2025. https://huggingface.co/Qwen/Qwen3-Embedding-4B — `verified` · Doc refs: P2-10
84. Redpanda Data. "Business Source License 1.1" (Redpanda). https://github.com/redpanda-data/redpanda/blob/dev/licenses/bsl.md — `verified` · Doc refs: P4-15
85. Restate. LICENSE (Business Source License 1.1; converts to Apache 2.0 four years after release). https://github.com/restatedev/restate — `verified` · Doc refs: P4-16
86. Richardson, C. "Pattern: Transactional outbox." microservices.io. https://microservices.io/patterns/data/transactional-outbox.html — `verified` · Doc refs: P2-42, P4-12
87. Salsa project. "The red-green algorithm" (backdating). https://salsa-rs.github.io/salsa/reference/algorithm.html — `verified` · Doc refs: P4-24
88. Sarvam AI. "sarvam-105b" model card, Hugging Face, 2026. https://huggingface.co/sarvamai/sarvam-105b — `verified` · Doc refs: XC-12
89. Sarvam AI. "sarvam-m" model card (24B, Mistral-Small-3.1 base, Apache-2.0, Indic languages). Hugging Face, 2025. https://huggingface.co/sarvamai/sarvam-m — `verified` · Doc refs: P7-36
90. Shakir, A., Aarsen, T., Lee, S. "Binary and Scalar Embedding Quantization for Significantly Faster & Cheaper Retrieval." Hugging Face Blog, 2024. https://huggingface.co/blog/embedding-quantization — `verified` · Doc refs: P2-43
91. Temporal Technologies. "Events and Event History" (limits: warn at 10,240 events; terminate above 51,200 events, 10,000 signals or 2,000 updates) and "Continue-As-New." https://docs.temporal.io/workflow-execution/event ; https://docs.temporal.io/workflow-execution/continue-as-new — `verified` · Doc refs: P0-41
92. Temporal Technologies. "Task Queue Priority and Fairness." https://docs.temporal.io/develop/task-queue-priority-fairness — `verified` · Doc refs: P4-19
93. Temporal Technologies. "Temporal Cloud regions." https://docs.temporal.io/cloud/regions — `verified` · Doc refs: P4-18
94. Temporal Technologies. "Workflow Execution limits." https://docs.temporal.io/workflow-execution/limits — `verified` · Doc refs: P4-20
95. Temporal Technologies. "Workflows" (durable execution, replay). https://docs.temporal.io/workflows — `verified` · Doc refs: P0-31, P4-21
96. Timescale. "pgvectorscale" README. GitHub. https://github.com/timescale/pgvectorscale — `verified` (vendor benchmark) · Doc refs: P2-41
97. turbopuffer. "Regions." Documentation. https://turbopuffer.com/docs/regions — `verified` · Doc refs: P2-39
98. Vespa. "Phased ranking." Documentation. https://docs.vespa.ai/en/ranking/phased-ranking.html — `verified` · Doc refs: P2-38
99. W3C. "PROV-O: The PROV Ontology." W3C Recommendation, 30 Apr 2013. https://www.w3.org/TR/prov-o/ — `verified` · Doc refs: P3-37
100. W3C. "Understanding Success Criterion 1.4.1: Use of Color" (WCAG 2.2, Level A). https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html — `verified` · Doc refs: P10-18
101. W3C. "Web Annotation Data Model" (TextQuoteSelector). W3C Recommendation, 2017. https://www.w3.org/TR/annotation-model/ — `unverified` · Doc refs: P1-39
102. web.dev (Google). "Interaction to Next Paint (INP)" (≤200 ms good, >500 ms poor, p75). https://web.dev/articles/inp — `verified` · Doc refs: P10-19
103. Webrecorder (I. Kreymer). "An update on the WACZ format." 2023. https://webrecorder.net/blog/2023-05-03-an-update-on-wacz — `verified` · Doc refs: P0-27
104. Webrecorder. "WACZ Signing and Verification 0.1.0 (draft)." https://specs.webrecorder.net/wacz-auth/0.1.0/ — `snippet` · Doc refs: P0-28
105. Webrecorder. "Web Archive Collection Zipped (WACZ) 1.1.1" specification. https://specs.webrecorder.net/wacz/1.1.1/ — `verified` · Doc refs: P0-43
106. Xia, N. (Uber Engineering). "Building Reliable Reprocessing and Dead Letter Queues with Apache Kafka." 2018. https://www.uber.com/blog/reliable-reprocessing/ — `verified` · Doc refs: P4-28
107. ZenML LLMOps Database. "Agentic AI for Legal Research: Building Deep Research in Westlaw and CoCounsel." https://zenml.io/llmops-database/agentic-ai-for-legal-research-building-deep-research-in-westlaw-and-cocounsel — `verified` · Doc refs: P6-22, P10-27, CT-37

## 7. News, commentary & surveys

*Scope:* Independent news, legal-industry journalism, commentary, industry reports and surveys, and trackers. (53 sources.)

1. ABA Journal. "France bans and creates criminal penalty for judicial analytics" (Art. 33, Law no. 2019-222 of 23 Mar 2019). Jun 2019. https://www.abajournal.com/news/article/france-bans-and-creates-criminal-penalty-for-judicial-analytics — `verified` · Doc refs: P6-30, P10-29
2. Ambrogi, R. (LawSites). "LexisNexis launches Lexis+ with Protégé, replacing Lexis+ AI with an end-to-end workflow platform." Feb 2026. https://www.lawnext.com/2026/02/lexisnexis-launches-lexis-with-protege-replacing-lexis-ai-with-an-end-to-end-workflow-platform.html — `verified` · Doc refs: P6-23
3. Artificial Lawyer. "Lucio, Lightbringer, Harvey, Jus Mundi, SpotDraft, LI UK + NY." 10 Oct 2025. https://www.artificiallawyer.com/2025/10/10/lucio-lightbringer-harvey-jus-mundi-spotdraft-li-uk-ny/ — `snippet` · Doc refs: CT-54
4. Bar & Bench. "AZB & Partners announces adoption of Harvey AI." 10 Sep 2025. https://www.barandbench.com/news/corporate/azb-partners-announces-adoption-of-harvey-ai — `verified` · Doc refs: CT-27, IN-67
5. Bar & Bench. "CaseMine launches 'AMICUS AI – Advanced', its most powerful AI model for legal work." 10 Mar 2026. https://www.barandbench.com/news/casemine-launches-amicus-ai-advanced-its-most-powerful-ai-model-for-legal-work — `verified` · Doc refs: P10-33, CT-10
6. Bar & Bench. "Shardul Amarchand Mangaldas announces partnership with Harvey AI." 4 Jun 2025. https://www.barandbench.com/news/corporate/shardul-amarchand-mangaldas-announces-partnership-with-harvey-ai — `verified` · Doc refs: CT-26, IN-67
7. Bar & Bench. "Supreme Court e-Committee makes audio captchas available on all High Court websites…" https://barandbench.com/amp/story/news/litigation/supreme-court-e-committee-makes-audio-captchas-available-on-all-high-court-websites-to-facilitate-access-for-visually-impaired — `snippet` · Doc refs: P0-6
8. Bar & Bench. "Supreme Court launches neutral citation for judgments." 2023. https://www.barandbench.com/news/supreme-court-launches-neutral-citation-judgments — `verified` · Doc refs: P0-10, P1-28
9. Bar & Bench. "Three Harvard graduates are leveraging AI to enhance productivity for lawyers in India" (jhana). https://www.barandbench.com/news/three-harvard-graduates-jhana-ai-lawyers-in-india — `snippet` · Doc refs: CT-50
10. Bloomberg Law. "Harvey's $8 Billion Question: Can AI Startup Match Its Hype." 2025. https://news.bloomberglaw.com/esg/harveys-8-billion-question-can-ai-startup-match-its-hype — `verified` (via CT-32) · Doc refs: P10-22, CT-32
11. Business Wire / Entrackr. "Lucio Raises $5M to Build AI Native Workspace for Lawyers." Oct 2025. https://www.businesswire.com/news/home/20251006027921/en/ — `snippet` · Doc refs: CT-19
12. Charlotin, D. "AI Hallucination Cases" database (2,097 decisions; 16 India; accessed 30 Sep 2026). https://www.damiencharlotin.com/hallucinations/ — `verified` · Doc refs: P6-29, P8-8 · Also at: https://www.damiencharlotin.com/hallucinations/?q=&sort_by=-date&states=India
13. Codesota. "OmniDocBench leaderboard" (v1.5; GLM-OCR 94.62, PaddleOCR-VL-1.5 94.50; updated 2026-05-21). https://www.codesota.com/ocr/benchmark/omnidocbench — `verified` · Doc refs: P1-42
14. Conventus Law. "India: Cyril Amarchand Mangaldas takes a bold leap towards an AI-first future with strategic AI adoption" (Harvey pilot, Lucio, Copilot, ChatGPT Plus). 11 Mar 2025. https://conventuslaw.com/press-releases/india-cyril-amarchand-mangaldas-takes-a-bold-leaptowards-an-ai-first-future-with-strategic-ai-adoption/ — `verified` · Doc refs: P7-12
15. DEV Community. "olmOCR review: AllenAI's VLM beats Mistral, Marker on PDFs" (secondary report of olmOCR-Bench numbers). https://dev.to/andrew-ooo/olmocr-review-allenais-vlm-beats-mistral-marker-on-pdfs-4cci — `snippet` · Doc refs: P1-40
16. Drishti IAS. "National Judicial Data Grid" (NJDG Open API via departmental IDs and access keys for institutional litigants; extension planned). 26 Aug 2023. https://www.drishtiias.com/daily-updates/daily-news-analysis/national-judicial-data-grid/print_manually — `verified` (secondary source) · Doc refs: P0-12
17. Drishti IAS. "National Judicial Data Grid" (Open API for Central/State governments and institutional litigants). Sep 2023. https://www.drishtiias.com/daily-updates/daily-news-analysis/national-judicial-data-grid-1/print_manually — `snippet` · Doc refs: P7-16
18. DSCI. "Acquittal, anonymity: Delhi High Court's ruling on right to be forgotten and what comes next" (*Laksh Vir Singh Yadav v. Union of India*, W.P.(C) 1021/2016, Delhi HC, 2026). https://www.dsci.in/article/content/acquittal-anonymity-delhi-high-courts-ruling-right-be-forgotten-and-what-comes-next — `verified` (secondary; judgment text not read) · Doc refs: P9-38
19. Entrackr. "AI paralegal startup Jhana raises $1.6 Mn in seed round." Sep 2024. https://entrackr.com/2024/09/ai-paralegal-startup-jhana-raises-1-6-mn-in-seed-round — `snippet` · Doc refs: CT-14
20. GKToday. "Indian Courts Achieve Milestone in Case Disposals" (NJDG 2024: HCs "more than 1.2 million" cases cleared; SC "addressed 36,969 cases"). 2025. https://www.gktoday.in/indian-courts-achieve-milestone-in-case-disposals/ — `verified` (secondary; wording does not define "disposal") · Doc refs: P0-14
21. The Hacker News. "Zero-Click AI Vulnerability Exposes Microsoft 365 Copilot Data Without User Interaction" (EchoLeak, CVE-2025-32711, CVSS 9.3; Aim Security; patched June 2025). Jun 2025. https://thehackernews.com/2025/06/zero-click-ai-vulnerability-exposes.html — `verified` · Doc refs: P7-18
22. Implicator.ai. "Legora and the 260x question." 2026. https://www.implicator.ai/legora-and-the-260x-question/ — `verified` (secondary; ARR conflicts with CT-43) · Doc refs: P10-23, CT-44
23. InfoQ. "AWS to discontinue Amazon QLDB" (end of support 31 Jul 2025; migrate to Aurora PostgreSQL). Jul 2024. https://www.infoq.com/news/2024/07/aws-kill-qldb — `verified` · Doc refs: P7-32
24. Internet Freedom Foundation. "Zombie Tracker" (Section 66A cases after 2015; timeline incl. SC directions of 15 Feb 2019). https://zombietracker.in/ — `verified` (CivicDataLab co-authorship not confirmed on the page) · Doc refs: P4-41
25. IT Brief. "Harvey launches 500 legal AI agents, Agent Builder tool." 5 May 2026. https://itbrief.news/story/harvey-launches-500-legal-ai-agents-builder-tool — `verified` · Doc refs: P6-27
26. law.asia. "Cyril Amarchand Mangaldas embarks on an AI-first future." https://law.asia/?p=560564 — `snippet` · Doc refs: CT-20
27. Law.asia. "Legality of data scraping under Indian law." https://law.asia/india-data-scraping-regulation/ — `snippet` · Doc refs: P0-22
28. LawFoyer. "Eastern Book Company v. D.B. Modak — case summary." https://lawfoyer.in/eastern-book-company-ors-v-d-b-modak-anr-air-2008-sc-809-2008-1-scc-1-2008-air-scw-49/ — `snippet` · Doc refs: P0-19
29. LawNext (Ambrogi, B.). "LexisNexis unveils the next generation of its Protégé General AI." 10 Dec 2025. https://www.lawnext.com/2025/12/lexisnexis-unveils-the-next-generation-of-its-protege-general-ai — `verified` · Doc refs: P10-28, CT-35
30. LawNext. "Harvey announces plan to develop Memory…" 8 Jan 2026. https://www.lawnext.com/2026/01/harvey-announces-plan-to-develop-memory-enabling-users-to-retain-context-for-more-consistent-work.html — `verified` · Doc refs: P9-39
31. LawSites. "LexisNexis introduces Protégé General AI…" Aug 2025. https://www.lawnext.com/2025/08/lexisnexis-introduces-protege-general-ai-and-expands-agentic-ai-leadership-bringing-secure-integrated-access-to-general-purpose-ai-for-legal-professionals.html — `snippet` · Doc refs: P6-24
32. Legal IT Insider. "Harvey partners with Intapp for ethical walls enforcement." 23 Feb 2026 (partnership announcement; CEO quote on standards following users "into every tool"). https://legaltechnology.com/2026/02/23/harvey-partners-with-intapp-for-ethical-walls-enforcement/ — `verified` · Doc refs: P7-14
33. LiveLaw. "CJI DY Chandrachud Urges Lawyers To Use SCR." 19 Sep 2024. https://www.livelaw.in/top-stories/cji-dy-chandrachud-urges-lawyers-to-use-scr-270054 — `verified` · Doc refs: P0-9
34. LiveLaw. "Madras High Court To Have Neutral Citation System From Jan 1" ("Year/MHC/auto generated number", w.e.f. 1 Jan 2023). https://livelaw.in/news-updates/madras-high-court-citation-system-from-1st-january-217771 — `verified` · Doc refs: P1-30
35. MediaNama. "223 experts concerned about MeitY's stance on web scraping to train AI models." Feb 2025. https://www.medianama.com/2025/02/223-experts-concerned-about-meitys-stance-on-web-scraping-to-train-ai-models/ — `verified` · Doc refs: P0-21, IN-63
36. Mondaq. "Delhi High Court First To Introduce Neutral Citation System For Its Judgements." 2022. https://www.mondaq.com/india/performance/1241608/delhi-high-court-first-to-introduce-neutral-citation-system-for-its-judgements — `verified` · Doc refs: P0-11, P1-29
37. Moneylife. "Kerala Becomes 1st State To Make AI-based Witness Recording Mandatory in All Courts." 7 Oct 2025. https://www.moneylife.in/article/kerala-becomes-1st-state-to-make-aibased-witness-recording-mandatory-in-all-courts/78510.html — `verified` · Doc refs: CT-25
38. Open Knowledge Foundation blog. "Opening up India's laws – the journey of Nyaaya.in" (Akoma Ntoso via Indigo). https://blogarchive.okfn.org/?p=23075 — `snippet` · Doc refs: P1-35
39. PRS Legislative Research. "The Bharatiya Nyaya (Second) Sanhita, 2023" bill track. https://prsindia.org/billtrack/the-bharatiya-nyaya-second-sanhita-2023 — `verified` · Doc refs: IN-42
40. PRS Legislative Research. "The Negotiable Instruments (Amendment) Bill, 2015" (territorial jurisdiction for cheque-bouncing cases; definition of electronic cheque). https://prsindia.org/billtrack/the-negotiable-instruments-amendment-bill-2015 — `verified` · Doc refs: P10-37
41. Pulse 2.0 / Sacra. "Legora: $550 Million Series D At $5.55 Billion Valuation…" Mar 2026. https://pulse2.com/legora-550-million-series-d-at-5-55-billion-valuation-raised-for-collaborative-ai-legal-platform — `snippet` · Doc refs: CT-43
42. SabrangIndia (citing Ministry of Law & Justice / NJDG). "26 thousand cases disposed of by the SC, 5.23 lakh by the HC in this year" (HC disposals 2020–2022). https://sabrangindia.in/26-thousand-cases-disposed-of-by-the-sc-5-23-lakh-by-the-hc-in-this-year-ministry-of-law-and-justice — `verified` (Lok Sabha reply, 22 Jul 2023) · Doc refs: XC-41
43. Sacra. "Harvey" company profile (ARR estimates). https://sacra.com/c/harvey/ — `snippet` · Doc refs: CT-31
44. Shardul Amarchand Mangaldas. "SAM leads Indian legal market with rollout of Harvey AI." 3 Jun 2025. https://www.amsshardul.com/sam-leads-indian-legal-market-with-rollout-of-harvey-ai/ — `verified` · Doc refs: P7-11
45. SpicyIP. "EBC granted injunction against Lexis Nexis and Thomson Reuters…" Feb 2014 (interim injunctions, District Judge, Lucknow; Mar 2013 and Jan 2014). https://spicyip.com/2014/02/ebc-granted-injunction-against-lexis-nexis-and-thomson-reuters-for-infringement-of-their-copyright.html — `verified` · Doc refs: P0-20
46. Stanford HAI. "AI on Trial: Legal Models Hallucinate in 1 out of 6 (or More) Benchmarking Queries." 2024. https://hai.stanford.edu/news/ai-trial-legal-models-hallucinate-1-out-6-or-more-benchmarking-queries — `verified` · Doc refs: P5-7
47. Thomson Reuters. "Future of Professionals" report (2026 edition findings). https://www.thomsonreuters.com/en/c/future-of-professionals — `verified` · Doc refs: P10-11
48. Unite.ai. "Harvey secures $550M in fresh funding; valuation climbs to $15.5B." 9 Sep 2026. https://www.unite.ai/harvey-secures-550m-in-fresh-funding-valuation-climbs-to-15-5b/ — `verified` (secondary; Tenet and LAB details) · Doc refs: CT-30
49. Vals AI. "Vals Legal AI Report (VLAIR)." Feb 2025. https://www.vals.ai/industry-reports/vlair-2-27-25 — `snippet` · Doc refs: P6-4, CT-40 · Also at: https://www.law.berkeley.edu/wp-content/uploads/archive/2025/12/VALs-AI-Legal-AI-report-February-2025-.pdf
50. Vals AI. "Vals Legal AI Report (VLAIR): Legal Research." 14 Oct 2025. https://vals.ai/industry-reports/vlair-10-14-25 — `verified` · Doc refs: P6-3, P8-10, P10-21, CT-39
51. Verdictum. "All Supreme Court Judgments to Have Neutral Citations" (Feb 2023; from 1 Jan 2023, then back "till 2014 and then from 1950 to 2014"; AI-assisted vernacular translation vetted by retired District Judges), https://www.verdictum.in/court-updates/supreme-court/neutral-citations-judgments-chief-justice-dy-chandrachud-1463966 — `verified` · Doc refs: P1-28, IN-48
52. Verdictum. "CJI Announces Launch Of e-SCR Project To Provide Free Access To 34,000 Judgments." 3 Jan 2023. https://www.verdictum.in/court-updates/supreme-court/e-scr-free-access-to-34000-judgments-1455548 — `verified` (incl. "all judgements will be placed online within 24 hours") · Doc refs: P0-8
53. YourStory. "How Adalat AI is bringing ease to India's overburdened justice system." Jan 2026. https://yourstory.com/socialstory/2026/01/adalat-ai-india-overburdened-justice-system-technology — `snippet` · Doc refs: CT-51

## 8. Other

*Scope:* Wikipedia and library guides (secondary reference), non-AI academic work (medicine, law and economics), foreign case law, and the authors' own probes/analyses. (25 sources.)

1. AHRQ PSNet. "Alert Fatigue" (primer). https://psnet.ahrq.gov/primer/alert-fatigue — `verified` · Doc refs: P10-12
2. Ancker, J.S. et al. "Effects of workload, work complexity, and repeated alerts on alert fatigue in a clinical decision support system." BMC Medical Informatics and Decision Making, 2017. doi:10.1186/s12911-017-0430-8 — `verified` (abstract via Europe PMC) · Doc refs: P4-35
3. eCourts Services portal (case status/orders by CNR) and third-party eCourts APIs (no general public API found). https://en.vikaspedia.in/viewcontent/e-governance/online-legal-services/how-to-check-court-case-status-online-in-india ; https://attestr.developerhub.io/attestr-docs/ecourts-case-order-judgment-document-api — `snippet` · Doc refs: P9-37
4. IALS (University of London). "India Code" resource description ("acts of the Parliament of India from 1834 to date"; updated versions; chronological table). https://resources.ials.sas.ac.uk/node/708433 — `verified` · Doc refs: P0-36
5. IN doc analysis. Neutral citations extracted from HC judgments hosted on Indian Kanoon, sampled 2026-09-30 (e.g. docs 28899933, 58356618, 115370172, 106494537, 183818669, 22332753, 75969105, 158106960, 134652804, 153623724, 29261763, 54875004, 30668313, 87248603, 88578743, 20591891, 171878345, 93589483, 144875592). https://indiankanoon.org/doc/22332753/ (example) — `verified` (probe) · Doc refs: IN-54
6. Mata v. Avianca, Inc., No. 22-cv-1461 (S.D.N.Y. 2023) (sanctions for ChatGPT-fabricated citations), as described in Verma 2026. https://arxiv.org/abs/2608.12571 — `snippet` · Doc refs: P8-9
7. O.P. Jindal Global University Library. "SCC Online: how to identify overruled judgments" (FAQ; red-circle exclamation mark = overruled). https://libguides.jgu.edu.in/subjects/faq.php?faq_id=42 — `verified` · Doc refs: P3-24
8. P0 author. HTTP probes of Indian legal portals from non-Indian cloud egress (robots.txt, CAPTCHA markers, TLS/WAF errors), 2026-09-30. Raw notes: SCRATCH/notes/ — `verified` (first-hand observation; single point in time) · Doc refs: P0-33
9. Priest, G., Klein, B. "The Selection of Disputes for Litigation." J. Legal Stud., 1984; Klerman, D., Lee, Y. "The Selection of Disputes at Forty." Yale J. on Reg. https://www.yalejreg.com/wp-content/uploads/11.-Klerman-Lee.-The-Selection-of-Disputes-at-Forty.-Print-1.pdf — `snippet` · Doc refs: P9-35
10. University of South Carolina School of Law Library. "Updating federal cases" (Shepard's signals). https://guides.law.sc.edu/LRAWSpring/LRAW/updatingfedcases — `snippet` · Doc refs: P3-20
11. van der Sijs, H., Aarts, J., Vulto, A., Berg, M. "Overriding of drug safety alerts in computerized physician order entry." JAMIA 13(2), 2006. doi:10.1197/jamia.m1809 — `verified` (abstract via Europe PMC) · Doc refs: P4-34
12. Wikipedia. "Bharatiya Nyaya Sanhita, 2023" (358 sections; 20 new offences; 19 dropped). https://en.wikipedia.org/wiki/Bharatiya_Nyaya_Sanhita — `verified` (secondary) · Doc refs: P3-60, P4-44, IN-43 · Also at: https://en.wikipedia.org/wiki/Bharatiya_Nyaya_Sanhita,_2023
13. Wikipedia. "Bharatiya Sakshya Adhiniyam" (170 sections vs 167 in IEA 1872; s.170 "Repeal and savings"; commenced 1 Jul 2024; secondary). https://en.wikipedia.org/wiki/Bharatiya_Sakshya_Adhiniyam — `verified` · Doc refs: P3-65
14. Wikipedia. "Bloomberg Terminal" (keyboard, GO key, mnemonic commands, panels, Launchpad, subscriber count and price). Accessed 30 Sep 2026. https://en.wikipedia.org/wiki/Bloomberg_Terminal — `verified` (secondary) · Doc refs: P10-1
15. Wikipedia. "Digital Personal Data Protection Act, 2023" (commencement: 13 Nov 2025; s.6(9) 13 Nov 2026; remainder 13 May 2027). https://en.wikipedia.org/wiki/Digital_Personal_Data_Protection_Act,_2023 — `verified` (secondary; confirm against Gazette notification) · Doc refs: P0-44
16. Wikipedia. "European Case Law Identifier" (secondary; Council conclusions OJ 2011/C 127/01). https://en.wikipedia.org/wiki/European_Case_Law_Identifier — `verified` · Doc refs: P3-34
17. Wikipedia. "European Legislation Identifier" (secondary). https://en.wikipedia.org/wiki/European_Legislation_Identifier — `verified` · Doc refs: P3-33
18. Wikipedia. "High courts of India" (state/UT → HC and bench table). https://en.wikipedia.org/wiki/High_courts_of_India — `verified` (secondary) · Doc refs: IN-52
19. Wikipedia. "KeyCite" (introduced to Westlaw in 1997). https://en.wikipedia.org/wiki/KeyCite — `verified` (secondary) · Doc refs: P10-3
20. Wikipedia. "Krippendorff's alpha" (acceptability thresholds α≥0.800; 0.667–0.800 tentative; citing Krippendorff, K., Content Analysis, 2004, pp. 241–243). https://en.wikipedia.org/wiki/Krippendorff%27s_alpha — `verified` (secondary; primary not accessible, 403) · Doc refs: P8-43
21. Wikipedia. "Languages with official recognition in India" (Hindi in HCs of Bihar, UP, MP, Rajasthan). https://en.wikipedia.org/wiki/Languages_with_official_recognition_in_India — `snippet` (secondary) · Doc refs: IN-53
22. Wikipedia. "Neutral citation" — India section (reporter formats; 200+ law reports; NJRS). https://en.wikipedia.org/wiki/Neutral_citation — `verified` (secondary) · Doc refs: IN-51
23. Wikipedia. "Reason maintenance" (Doyle 1979 JTMS; de Kleer 1986 ATMS; secondary). https://en.wikipedia.org/wiki/Reason_maintenance — `verified` · Doc refs: P3-39
24. Wikipedia. "Shepard's Citations" (status icon; plain-English treatment phrases). https://en.wikipedia.org/wiki/Shepard%27s_Citations — `verified` (secondary) · Doc refs: P10-4
25. Wikipedia. "Shreya Singhal v. Union of India" (s.66A "has continued to be used"). https://en.wikipedia.org/wiki/Shreya_Singhal_v._Union_of_India — `verified` (secondary) · Doc refs: P4-42

## 9. Follow-up verification list

Every source whose strongest tag is `unverified` (12) or `snippet` (83) is listed here, 95 in all. Each entry gives its category (§), the citing tags, and the citing authors' own notes, which often say exactly what remains to be checked. A doc owner who verifies a source should update the tag in both the document's reference list and its fragment, then regenerate this file. Sources whose claims support tier-1 outputs (limitation, deadlines, maintainability, statutory text, case status) should be verified first. In this list, those are mainly the §3 items.

### 9.1 Unverified (12)

1. **§1** Bommarito, M., Katz, D.M., Detterman, E. "LexNLP: Natural language processing and information extraction for legal and regulatory texts." 2018. https://arxiv.org/abs/1806.03688 · Doc refs: P1-43 · Notes — P1-43: (not cited in text; background)
2. **§1** Burges, C.J.C. "From RankNet to LambdaRank to LambdaMART: An Overview." Microsoft Research Technical Report MSR-TR-2010-82, 2010. · Doc refs: P5-38 · Notes — P5-38: (foundational; not fetched)
3. **§1** Dawid, A.P., Skene, A.M. "Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm." Applied Statistics, 1979. · Doc refs: P9-40
4. **§2** Bhattacharya, P. et al. "Identification of Rhetorical Roles of Sentences in Indian Legal Judgments." JURIX 2019. https://arxiv.org/abs/1911.05405 · Doc refs: P1-21
5. **§3** Bar Council of India. "Rules on Professional Standards" (Bar Council of India Rules, Part VI, Chapter II — duty to client incl. confidentiality and not acting for the opposite party; rule numbers 17/33 from memory). https://www.barcouncilofindia.org/info/rules-on-professional-standards · Doc refs: P7-38 · Notes — P7-38: (page did not render rule text)
6. **§4** High Court of Kerala. Policy on use of AI tools in the district judiciary (Jul 2025). No URL verified. · Doc refs: CT-53
7. **§4** Supreme Court of India. SUPACE (2021) and SUVAS (2019) AI tools. No URL verified. · Doc refs: CT-52
8. **§5** Search-result snippet attributing "Rs. 48,500/user/year + 18% GST, separate add-on, Feb 2026 preview" to SCC Online AI Pro (vaquill.ai/alternative/scc-online). The fetched page did not contain the claim. · Doc refs: CT-55
9. **§6** IETF. RFC 8785 "JSON Canonicalization Scheme (JCS)." 2020. https://www.rfc-editor.org/rfc/rfc8785 · Doc refs: P0-39
10. **§6** IETF. RFC 9110 "HTTP Semantics" (conditional requests, ETag, Last-Modified). 2022. https://www.rfc-editor.org/rfc/rfc9110 · Doc refs: P0-38 · Notes — P0-38: (not fetched this session)
11. **§6** ISO 28500:2017 "Information and documentation — WARC file format." https://www.iso.org/standard/68004.html · Doc refs: P0-40
12. **§6** W3C. "Web Annotation Data Model" (TextQuoteSelector). W3C Recommendation, 2017. https://www.w3.org/TR/annotation-model/ · Doc refs: P1-39

### 9.2 Snippet only (83)

1. **§1** (authors not verified). "Are Large Language Models Effective Knowledge Graph Constructors?" arXiv 2510.11297, 2025. https://arxiv.org/abs/2510.11297 · Doc refs: P3-12
2. **§1** Bourtoule, L. et al. "Machine Unlearning." IEEE S&P, 2021. https://arxiv.org/abs/1912.03817 · Doc refs: P9-31
3. **§1** Cormack, G.V., Clarke, C.L.A., Büttcher, S. "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods." SIGIR 2009. http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf · Doc refs: P5-1 · Notes — P5-1: (PDF not parseable; formula and k=60 confirmed via [P5-3])
4. **§1** "dots.ocr: Multilingual Document Layout Parsing in a Single Vision-Language Model." arXiv:2512.02498, 2025. https://arxiv.org/abs/2512.02498 · Doc refs: P1-6
5. **§1** Doyle, J. "A Truth Maintenance System." Artificial Intelligence 12(3), 1979; de Kleer, J. "An Assumption-based TMS." Artificial Intelligence 28(2), 1986. https://en.wikipedia.org/wiki/Reason_maintenance · Doc refs: P4-26 · Notes — P4-26: (via P3 [P3-39])
6. **§1** Farquhar, S., Kossen, J., Kuhn, L., Gal, Y. "Detecting hallucinations in large language models using semantic entropy." Nature 630, 2024. https://www.nature.com/articles/s41586-024-07421-0 · Doc refs: P8-23 · Notes — P8-23: (referenced in [P8-24])
7. **§1** Han, J. et al. "RAG Meets Temporal Graphs: Time-Sensitive Modeling and Retrieval for Evolving Knowledge." arXiv 2510.13590, 2025. https://arxiv.org/abs/2510.13590 · Doc refs: P4-46
8. **§1** Jin, B., Yoon, J., Han, J., Arık, S.Ö. "Long-Context LLMs Meet RAG: Overcoming Challenges for Long Inputs in RAG." ICLR 2025. https://arxiv.org/abs/2410.05983 · Doc refs: P5-22
9. **§1** Liu, N.F., et al. "Lost in the Middle: How Language Models Use Long Contexts." TACL 12, 2024. https://aclanthology.org/2024.tacl-1.9/ · Doc refs: P5-21
10. **§1** Mokhov, A., Mitchell, N., Peyton Jones, S. "Build Systems à la Carte." Proc. ACM Program. Lang. (ICFP), 2018. https://www.microsoft.com/en-us/research/uploads/prod/2018/03/build-systems.pdf · Doc refs: P4-25 · Notes — P4-25: (PDF fetched, text not extractable; definitions of minimality/early cutoff paraphrased from memory)
11. **§1** OpenDataLab. "MinerU2.5: A Decoupled Vision-Language Model for Efficient High-Resolution Document Parsing." arXiv:2509.22186, 2025. https://arxiv.org/abs/2509.22186 · Doc refs: P1-5
12. **§1** Ouyang, L. et al. "OmniDocBench: Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations." CVPR 2025. https://arxiv.org/abs/2412.07626 · Doc refs: P1-3
13. **§1** Pradeep, R., Sharifymoghaddam, S., Lin, J. "RankZephyr: Effective and Robust Zero-Shot Listwise Reranking is a Breeze!" arXiv 2312.02724, 2023. https://arxiv.org/abs/2312.02724 · Doc refs: P5-32
14. **§1** (authors not verified). "SBV-LawGraph: A Hybrid RAG Approach Integrating Knowledge Graph for the State Bank of Vietnam Legal Documents." ACIIDS 2026, Springer. https://link.springer.com/chapter/10.1007/978-981-92-0071-9_16 · Doc refs: P3-3
15. **§1** "Seeing is Believing? Mitigating OCR Hallucinations in Multimodal Large Language Models." NeurIPS 2025. https://arxiv.org/abs/2506.20168 · Doc refs: P1-15
16. **§1** Sheng, Y. et al. "S-LoRA: Serving Thousands of Concurrent LoRA Adapters." 2023. https://arxiv.org/abs/2311.03285 · Doc refs: P9-33
17. **§1** Sweeney, L. "k-Anonymity: A Model for Protecting Privacy." Int. J. Uncertainty, Fuzziness and Knowledge-Based Systems 10(5):557–570, 2002. https://doi.org/10.1142/S0218488502001648 · Doc refs: P9-42 · Notes — P9-42: (bibliographic details via Wikipedia)
18. **§1** UQLegalAI. "UQLegalAI@COLIEE2025: Advancing Legal Case Retrieval with Large Language Models and Graph Neural Networks." arXiv 2505.20743, 2025. https://arxiv.org/abs/2505.20743 · Doc refs: P5-14
19. **§1** "Youtu-Parsing: Perception, Structuring and Recognition via High-Parallelism Decoding." arXiv:2601.20430, 2026 (reports olmOCR-Bench for PaddleOCR-VL, dots.ocr, MinerU2.5). https://arxiv.org/abs/2601.20430 · Doc refs: P1-41
20. **§2** Bhattacharya, P., Ghosh, K., Pal, A., Ghosh, S. "Hier-SPCNet: A Legal Statute Hierarchy-based Heterogeneous Network for Computing Legal Case Document Similarity." SIGIR 2020 (arXiv 2007.03225). https://arxiv.org/abs/2007.03225 · Doc refs: P3-28, P5-12
21. **§2** India Science & Technology portal. "Predictive Coding for Identification of Ratio Decidendi in Indian Judicial Decisions" (NIT Tiruchirappalli, 2024–2027). https://indiascienceandtechnology.gov.in/research/predictive-coding-identification-ratio-decidendi-indian-judicial-decisions · Doc refs: P1-44
22. **§3** Government of Odisha. "About e-Gazette" (weekly vs extraordinary gazettes). https://egazette.odisha.gov.in/about_gazette · Doc refs: P0-34
23. **§3** Consumer Protection Act 2019, s.38(2)(a) (opposite party's version within 30 days or extended period not exceeding 15 days). https://indiankanoon.org/doc/84381021/ · Doc refs: P6-45
24. **§3** Digital Personal Data Protection Act, 2023, s.12 (right to correction and erasure). https://dpdpa.com/dpdpa2023/chapter-3/section12.html · Doc refs: P9-23
25. **§3** e-Gazette of India PDF paths (e.g. https://egazette.gov.in/WriteReadData/1969/O-1469-1969-0001-66051.pdf) and Internet Archive mirror (https://archive.org/download/in.gazette.1972.112/) · Doc refs: P0-35
26. **§3** Supreme Court of India. "Equivalent Citation Table — how to find" (SCR ↔ SCC, AIR(SC), JT, SCALE). https://main.sci.gov.in/pdf/ECT/how2find.pdf · Doc refs: P1-31 · Notes — P1-31: (fetch failed: DNS)
27. **§3** Illustrative NI Act authorities: Rangappa v Sri Mohan (2010) 11 SCC 441; Sampelly Satyanarayana Rao v IREDA (2016) 10 SCC 458; Saketh India Ltd v India Securities Ltd (1999) 3 SCC 1. Citations and headline holdings confirmed via Indian Kanoon search results (https://indiankanoon.org/search/?formInput=Rangappa%20v%20Sri%20Mohan ; …Sampelly… ; …Saketh…) · Doc refs: P6-44 · Notes — P6-44: ; paragraph anchors unverified
28. **§3** Mineral Area Development Authority v. Steel Authority of India: judgment of 25 Jul 2024 (9 judges) https://indiankanoon.org/doc/179331686/ · Doc refs: P4-38 · Notes — P4-38: ; order of 14 Aug 2024 (paras 24–25) https://indiankanoon.org/doc/96063944/ — verified
29. **§3** New India Assurance Co. Ltd v Hilli Multipurpose Cold Storage Pvt Ltd (SC Constitution Bench, 4 Mar 2020). https://api.sci.gov.in/supremecourt/2013/35086/35086_2013_3_1501_21326_Judgement_04-Mar-2020.pdf · Doc refs: P6-34 · Notes — P6-34: (PDF fetched in review but not machine-readable; holding from secondary sources)
30. **§3** High Court of Manipur. "Notice: eSCR and DigiSCR merged into SCR portal." https://hcmimphal.nic.in/Documents/eSCR%20and%20DigiSCR_0001.pdf · Doc refs: P0-7
31. **§3** Jharkhand High Court. Order of 19 Feb 2025 discussing IPC s.420 and BNS s.318(4). https://indiankanoon.org/doc/105667861/ · Doc refs: IN-40
32. **§4** American Bar Association. "Formal Opinion 512: Generative Artificial Intelligence Tools." 29 Jul 2024 (via summaries). https://ezel.ai/ethics-opinions/aba/512-generative-ai-tools · Doc refs: P8-71, P9-15 · Notes — P8-71: (sibling P9-15; primary PDF 403) | P9-15: (no note)
33. **§4** AZB & Partners. "India's Digital Personal Data Protection Act: Phased Rollout and Key Compliance Milestones" (Rules notified Nov 2025; 18-month phase-in to May 2027). https://www.azbpartners.com/bank/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones/ ; The Week/PTI 14 Nov 2025 https://www.theweek.in/wire-updates/business/2025/11/14/del148-biz-dpdp-rules-ld-govt.html · Doc refs: XC-36
34. **§4** CERT-In. Directions under s.70B(6) IT Act, 28 Apr 2022 (6-hour reporting; 180-day logs in India; NTP sync) — as summarised by PSA Legal https://psalegal.com/new-cert-in-directions-overview-and-implications/ · Doc refs: XC-38
35. **§4** Digital India Awards 2022 Compendium, p.21 (Judgment Search Portal description). https://digitalindiaawards.india.gov.in/assets/compendium2022/files/basic-html/page21.html · Doc refs: P0-37
36. **§4** Government of India. "Government Open Data License – India (GODL)." (copy hosted by India Post) https://app.indiapost.gov.in/documents/media/OGD.pdf · Doc refs: P0-24, IN-66 · Notes — P0-24: (no note) | IN-66: (503 on fetch)
37. **§4** NALSAR Tech Law Forum. "Privacy with a footnote: data retention under the DPDP framework" (s.8(7)). 2025. https://techlawforum.nalsar.ac.in/privacy-with-a-footnote-data-retention-under-the-dpdp-framework/ · Doc refs: P7-4
38. **§4** Protiviti. "Flash compliance update: DPDP Rules 2025" (Rules 6, 7; processors; commencement). Nov 2025. https://www.protiviti.com/sites/default/files/2025-11/flash_compliance_update_dpdp_rules-2025.pdf · Doc refs: P7-6
39. **§4** Rajya Sabha. Answer to question, 25 July 2024 (eCourts: 26.044 crore cases; 26.047 crore orders/judgments). https://rsdebate.nic.in/bitstream/123456789/749688/1/PQ_265_25072024_U425_p410_p415.pdf · Doc refs: P0-13
40. **§4** Taxmann / TCSA. "Cross-border data transfers under the DPDP Act 2023" (s.16 negative list; s.16(2); s.16 + Rule 15 commencement 13 May 2027). https://www.taxmann.com/post/blog/cross-border-data-transfers-under-the-dpdp-act/ ; https://www.tcsa.in/frameworks/dpdp/cross-border-transfer · Doc refs: XC-37
41. **§5** CaseMine. "FAQ / About" (citator; CaseIQ; AMICUS). https://www.casemine.com/home/faq · Doc refs: P3-26
42. **§5** Clio. "Clio Completes Landmark $1B vLex Acquisition and Announces $500M Series G Funding Round at $5B Valuation." 10 Nov 2025. https://www.clio.com/about/press/clio-completes-landmark-1b-vlex-acquisition-series-g-5b-valuation/ · Doc refs: CT-41
43. **§5** Google Cloud. "Data residency — Generative AI on Vertex AI" (Claude APAC regional endpoints Singapore/Taiwan). https://cloud.google.com/vertex-ai/generative-ai/docs/learn/data-residency · Doc refs: XC-9
44. **§5** Google Cloud. "Document AI pricing" and "Enterprise Document OCR supported languages." https://cloud.google.com/document-ai/pricing ; https://docs.cloud.google.com/document-ai/docs/process-forms · Doc refs: P1-11
45. **§5** Google Cloud. "Generative AI on Vertex AI locations" (asia-south1 Gemini 2.5 models; regional ML processing). https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations · Doc refs: XC-10
46. **§5** Harvey. "Harvey to Expand Team with New Bengaluru Office." 10 Jul 2025. https://www.harvey.ai/blog/harvey-to-expand-team-with-new-bengaluru-office · Doc refs: CT-28
47. **§5** Legal Technology Hub. "CaseMine" vendor profile (CaseIQ, Parallel Search). https://www.legaltechnologyhub.com/vendors/casemine/ · Doc refs: CT-11
48. **§5** Legal Technology Hub. "jhana" vendor profile (Searcher, Paralegal). https://www.legaltechnologyhub.com/vendors/jhana/ · Doc refs: CT-15
49. **§5** Provakil app listing (automatic case updates from 10,000+ courts; daily cause lists). Apple App Store. https://apps.apple.com/mx/app/provakil/id1111933293 · Doc refs: P7-17, P10-31 · Notes — P7-17: (no note) | P10-31: (via P7-17)
50. **§5** Sarvam AI. "Sarvam Vision." Blog, Feb 2026. https://www.sarvam.ai/blogs/sarvam-vision · Doc refs: P1-10 · Notes — P1-10: (no longer cited in text after review; the 20,267-sample figure previously attributed here could not be confirmed)
51. **§5** Thomson Reuters / Legal Current. "Thomson Reuters Builds on Legacy of Innovation with Continued AI Investment" (editorial review of machine tags fed back to models). https://www.legalcurrent.com/thomson-reuters-builds-on-legacy-of-innovation-with-continued-ai-investment/ (now redirects to https://www.thomsonreuters.com/en-us/posts/innovation/) · Doc refs: P9-20
52. **§5** Thomson Reuters. "KeyCite flags and icons for cases." Westlaw Edge help. https://www.thomsonreuters.com/en-ca/help/westlaw-edge/tools/keycite/flags-and-icons.html · Doc refs: P3-18
53. **§5** Vaquill (competitor-authored). "Harvey AI Review 2026: Honest Take + What It Really Costs." https://www.vaquill.ai/blog/harvey-ai-review-honest-assessment · Doc refs: CT-33 · Notes — CT-33: (unverified pricing)
54. **§5** Various. IndiaAI Mission compute subsidised rates (≈₹92/h H100-class; ≈₹67/GPU-h). e.g. https://huggingface.co/blog/daya-shankar/nvidia-h100-price-india ; https://dev.to/mr_manushukla/gpu-cloud-pricing-in-india-2026-h100-h200-and-b200-rates-compared-bo7 · Doc refs: XC-27
55. **§5** vLex/Clio. "Clio Signs Definitive Agreement to Acquire vLex for US $1 Billion." 30 Jun 2025. https://vlex.com/news/Clio-Signs-Definitive-Agreement-to-Acquire-vLex · Doc refs: P6-28
56. **§6** AutomationAtlas. "Temporal vs Apache Airflow 2026: Durable Workflows vs DAG Orchestration." 2026. https://automationatlas.io/guides/temporal-vs-apache-airflow-2026-comparison/ · Doc refs: P0-32
57. **§6** AWS. "Silo, Pool, and Bridge Models." AWS Well-Architected SaaS Lens. https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html · Doc refs: P7-25
58. **§6** BAAI. "bge-reranker-v2-m3" model documentation. https://bge-model.com/_sources/bge/bge_reranker_v2.rst.txt · Doc refs: P5-30
59. **§6** Free Law Project. "Citation depth data." 2020. https://free.law/2020/03/05/citation-depth-data/ · Doc refs: P3-23
60. **§6** Harvard Library Innovation Lab. "Perma Tools / Scoop." https://tools.perma.cc · Doc refs: P0-42
61. **§6** Library of Congress. "Sustainability of Digital Formats: WACZ." https://loc.gov/preservation/digital/formats/fdd/fdd000586.shtml · Doc refs: P0-29
62. **§6** Webrecorder. "WACZ Signing and Verification 0.1.0 (draft)." https://specs.webrecorder.net/wacz-auth/0.1.0/ · Doc refs: P0-28
63. **§7** Artificial Lawyer. "Lucio, Lightbringer, Harvey, Jus Mundi, SpotDraft, LI UK + NY." 10 Oct 2025. https://www.artificiallawyer.com/2025/10/10/lucio-lightbringer-harvey-jus-mundi-spotdraft-li-uk-ny/ · Doc refs: CT-54
64. **§7** Bar & Bench. "Supreme Court e-Committee makes audio captchas available on all High Court websites…" https://barandbench.com/amp/story/news/litigation/supreme-court-e-committee-makes-audio-captchas-available-on-all-high-court-websites-to-facilitate-access-for-visually-impaired · Doc refs: P0-6
65. **§7** Bar & Bench. "Three Harvard graduates are leveraging AI to enhance productivity for lawyers in India" (jhana). https://www.barandbench.com/news/three-harvard-graduates-jhana-ai-lawyers-in-india · Doc refs: CT-50
66. **§7** Business Wire / Entrackr. "Lucio Raises $5M to Build AI Native Workspace for Lawyers." Oct 2025. https://www.businesswire.com/news/home/20251006027921/en/ · Doc refs: CT-19
67. **§7** DEV Community. "olmOCR review: AllenAI's VLM beats Mistral, Marker on PDFs" (secondary report of olmOCR-Bench numbers). https://dev.to/andrew-ooo/olmocr-review-allenais-vlm-beats-mistral-marker-on-pdfs-4cci · Doc refs: P1-40
68. **§7** Drishti IAS. "National Judicial Data Grid" (Open API for Central/State governments and institutional litigants). Sep 2023. https://www.drishtiias.com/daily-updates/daily-news-analysis/national-judicial-data-grid-1/print_manually · Doc refs: P7-16
69. **§7** Entrackr. "AI paralegal startup Jhana raises $1.6 Mn in seed round." Sep 2024. https://entrackr.com/2024/09/ai-paralegal-startup-jhana-raises-1-6-mn-in-seed-round · Doc refs: CT-14
70. **§7** law.asia. "Cyril Amarchand Mangaldas embarks on an AI-first future." https://law.asia/?p=560564 · Doc refs: CT-20
71. **§7** Law.asia. "Legality of data scraping under Indian law." https://law.asia/india-data-scraping-regulation/ · Doc refs: P0-22
72. **§7** LawFoyer. "Eastern Book Company v. D.B. Modak — case summary." https://lawfoyer.in/eastern-book-company-ors-v-d-b-modak-anr-air-2008-sc-809-2008-1-scc-1-2008-air-scw-49/ · Doc refs: P0-19
73. **§7** LawSites. "LexisNexis introduces Protégé General AI…" Aug 2025. https://www.lawnext.com/2025/08/lexisnexis-introduces-protege-general-ai-and-expands-agentic-ai-leadership-bringing-secure-integrated-access-to-general-purpose-ai-for-legal-professionals.html · Doc refs: P6-24
74. **§7** Open Knowledge Foundation blog. "Opening up India's laws – the journey of Nyaaya.in" (Akoma Ntoso via Indigo). https://blogarchive.okfn.org/?p=23075 · Doc refs: P1-35
75. **§7** Pulse 2.0 / Sacra. "Legora: $550 Million Series D At $5.55 Billion Valuation…" Mar 2026. https://pulse2.com/legora-550-million-series-d-at-5-55-billion-valuation-raised-for-collaborative-ai-legal-platform · Doc refs: CT-43
76. **§7** Sacra. "Harvey" company profile (ARR estimates). https://sacra.com/c/harvey/ · Doc refs: CT-31
77. **§7** Vals AI. "Vals Legal AI Report (VLAIR)." Feb 2025. https://www.vals.ai/industry-reports/vlair-2-27-25 · Doc refs: P6-4, CT-40 · Notes — P6-4: (no note) | CT-40: (scores image-embedded; partially read)
78. **§7** YourStory. "How Adalat AI is bringing ease to India's overburdened justice system." Jan 2026. https://yourstory.com/socialstory/2026/01/adalat-ai-india-overburdened-justice-system-technology · Doc refs: CT-51
79. **§8** eCourts Services portal (case status/orders by CNR) and third-party eCourts APIs (no general public API found). https://en.vikaspedia.in/viewcontent/e-governance/online-legal-services/how-to-check-court-case-status-online-in-india ; https://attestr.developerhub.io/attestr-docs/ecourts-case-order-judgment-document-api · Doc refs: P9-37
80. **§8** Mata v. Avianca, Inc., No. 22-cv-1461 (S.D.N.Y. 2023) (sanctions for ChatGPT-fabricated citations), as described in Verma 2026. https://arxiv.org/abs/2608.12571 · Doc refs: P8-9
81. **§8** Priest, G., Klein, B. "The Selection of Disputes for Litigation." J. Legal Stud., 1984; Klerman, D., Lee, Y. "The Selection of Disputes at Forty." Yale J. on Reg. https://www.yalejreg.com/wp-content/uploads/11.-Klerman-Lee.-The-Selection-of-Disputes-at-Forty.-Print-1.pdf · Doc refs: P9-35
82. **§8** University of South Carolina School of Law Library. "Updating federal cases" (Shepard's signals). https://guides.law.sc.edu/LRAWSpring/LRAW/updatingfedcases · Doc refs: P3-20
83. **§8** Wikipedia. "Languages with official recognition in India" (Hindi in HCs of Bihar, UP, MP, Rajasthan). https://en.wikipedia.org/wiki/Languages_with_official_recognition_in_India · Doc refs: IN-53 · Notes — IN-53: (secondary)

## Appendix A. Deduplication and merge log

**A.1 Identity merges beyond URL normalisation.** Each pair names two fragment tags whose sources were judged identical. All tags in each group appear in the Doc refs of the resulting source.

- CT-40 + P6-4 → Vals AI "Vals Legal AI Report (VLAIR)"
- IN-4 + P3-50 → Constitution of India, Art. 141.
- IN-10 + P9-45 → Constitution of India, Article 348 (language to be used in the Supreme Court and High Courts; Art. 348(2)…
- IN-11 + P1-46 → Department of Official Language, GoI "The Official Languages Act, 1963"
- IN-11 + P10-36 → Department of Official Language, GoI "The Official Languages Act, 1963"
- IN-11 + P5-41 → Department of Official Language, GoI "The Official Languages Act, 1963"
- P5-40 + P6-37 → Negotiable Instruments Act, 1881, s.138 … "within thirty days"
- XC-42 + P0-23 → Digital Personal Data Protection Act 2023, s.3(c)(ii) (mirror text; PRS copy of Act).
- XC-43 + P7-8 → Government of India. Bharatiya Sakshya A… "Professional communications"
- P6-43 + P7-10 → Bharatiya Sakshya Adhiniyam 2023, s.63 (admissibility of electronic records; s.63(4) certificate in the…
- P4-10 + XC-44 → CNCF CloudEvents "CloudEvents — Version 1.0 specification"
- IN-32 + P3-64 → Bharatiya Nagarik Suraksha Sanhita, 2023… "Repeal and savings"
- IN-43 + P4-44 → Wikipedia "Bharatiya Nyaya Sanhita, 2023"
- P1-23 + P9-26 → Kalamkar, P., Agarwal, A., Tiwari, A., G… "Named Entity Recognition in Indian court judgments"
- P2-9 + P5-9 → Joshi, A., Sharma, A., Tanikella, S.K., … "U-CREAT: Unsupervised Case Retrieval using Events extrAcTion"
- P1-36 + P3-31 → OASIS LegalDocML TC "Akoma Ntoso Version 1.0"
- P6-29 + P8-8 → Charlotin, D "AI Hallucination Cases"
- IN-17 + P3-52 → Supreme Court of India. Kunhayammed v. State of Kerala, (2000) 6 SCC 359 (19 Jul 2000), conclusions (i)–(v).
- IN-27 + P3-54 → Supreme Court of India. Shree Chamundi Mopeds Ltd v. Church of South India Trust Assn., (1992) 3 SCC 1 (29…

**A.2 Compound entries cross-listed.** Each of these fragment entries cites more than one source. It is merged only with its first-cited source and is also listed in the Doc refs of the other source(s) shown.

- IN-67 → also listed under Bar & Bench "AZB & Partners announces adoption of Harvey AI"
- P4-38 → also listed under Supreme Court of India. Mineral Area Development Authority v. Steel Authority of India, 2024 INSC 607 (14 Aug…
- XC-17 → also listed under Dattam Labs (vanga) "indian-supreme-court-judgments"
- P1-28 → also listed under Bar & Bench "Supreme Court launches neutral citation for judgments"
- IN-74 → also listed under Prior, M., Hof, A., Wais, N., Grabmair, … "Risks and Limits of Automatic Consolidation of Statutes"
- IN-41 → also listed under Bharatiya Sakshya Adhiniyam 2023, s.63 (admissibility of electronic records; s.63(4) certificate in the…
- P5-28 → also listed under Cohere "Pricing"
- IN-65 → also listed under AWS Open Data Registry / vanga "Indian Supreme Court Judgments"
- P5-15 and P8-57 each cite both NOWJ@COLIEE 2025 and 2026 system papers; kept as one combined source.
- P1-28 and P4-38 cite a second source only inside their verification notes (Bar & Bench neutral-citation coverage; the 14 Aug 2024 *Mineral Area* order). They are cross-listed above.

**A.3 Deliberately not merged despite a shared URL.**

- P8-9 (*Mata v. Avianca*, S.D.N.Y. 2023) points to Verma 2026 (arXiv:2608.12571) as the place the case is described. The case is listed separately in §8 and not merged into the paper P8-4.
- P4-26 (Doyle 1979 and de Kleer 1986, the truth-maintenance papers) was seen via the Wikipedia article "Reason maintenance" (P3-39). The papers are listed in §1 and the Wikipedia article in §8.
- P3-27 (Indian Kanoon "Cites / Cited by" feature) uses the *Shreya Singhal* judgment page only as an example. The feature is listed in §5 and the judgment in §3.
- The dataset pages of one project on different hosts stay separate: the AWS Open Data registry pages, the GitHub `vanga/indian-*-court-judgments` repositories, `dataset.md` and `STATS.md`. The same holds for different judgments in the same matter, such as *Mineral Area Development Authority*, 25 Jul 2024 (P4-38) vs 14 Aug 2024 (IN-26).

## Appendix B. Per-document tags upgraded by merge

In these cases a document recorded a weaker tag for a source that another document verified. The bibliography shows the stronger tag. The owning document may upgrade its tag after checking that the verified source supports the same claim, but that check has not been done here.

| Weaker tag(s) | Source | Verified by |
|---|---|---|
| P1-2 (snippet) | Poznanski, J. et al. "olmOCR: Unlocking Trillions of Tokens in PDFs with Vision Language Models" | XC-25 |
| P1-36 (unverified) | OASIS LegalDocML TC "Akoma Ntoso Version 1.0" | P3-31 |
| P3-17 (snippet) | Zheng, L., Guha, N., Anderson, B.R., Hen… "When Does Pretraining Help? Assessing Self-Supervised Learning for Law and the CaseHOLD Dataset" | P8-50 |
| P3-19 (snippet) | Thomson Reuters "Quickly uncover implied overrulings with KeyCite Overruling Risk" | P4-8 |
| P3-22 (snippet) | Cushman, J., Dahl, M., Lissner, M "eyecite: A Tool for Parsing Legal Citations" | P1-26 |
| P3-52 (snippet) | Supreme Court of India. Kunhayammed v. State of Kerala, (2000) 6 SCC 359 (19 Jul 2000),… | IN-17 |
| P3-54 (snippet) | Supreme Court of India. Shree Chamundi Mopeds Ltd v. Church of South India Trust Assn.,… | IN-27 |
| P3-59 (snippet) | Supreme Court of India. L. Chandra Kumar v. Union of India, (1997) 3 SCC 261 (18 Mar… | IN-24 |
| P4-5 (snippet) | de Martim, H "An Ontology-Driven Graph RAG for Legal Norms: A Structural, Temporal, and Deterministic Approach" | P3-4, P5-20 |
| P5-15 (snippet) | Ngo, T.-H. et al. "NOWJ@COLIEE 2026: Adaptive Pipelines for Legal Retrieval and Reasoning" | P8-57 |
| P5-41 (snippet) | Department of Official Language, GoI "The Official Languages Act, 1963" | P1-46, P10-36, IN-11 |
| P6-37 (snippet) | Negotiable Instruments Act, 1881, s.138 … "within thirty days" | P5-40 |
| P6-43 (snippet) | Bharatiya Sakshya Adhiniyam 2023, s.63 (admissibility of electronic records; s.63(4)… | P7-10, IN-76 |
| P7-5 (snippet) | Digital Personal Data Protection Act 2023, s.16 (text). | IN-56 |
| P9-11 (snippet) | Ratner, A., Bach, S.H., Ehrenberg, H., F… "Snorkel: Rapid Training Data Creation with Weak Supervision" | P3-38 |
| P10-28 (snippet) | LawNext (Ambrogi, B.) "LexisNexis unveils the next generation of its Protégé General AI" | CT-35 |

