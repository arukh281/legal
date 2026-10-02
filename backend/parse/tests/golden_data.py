"""Golden truth definitions for parser verification (Session S05a).

Normative reference:
- Directive #6: Hand-checked by reading the PDFs, not saved from parser self-output.
- Small: header fields, paragraph count, and 5 anchors with exact text per fixture.
"""

from __future__ import annotations

from typing import Any

GOLDEN_FIXTURES: dict[str, dict[str, Any]] = {
    "nclt_born_digital_chd": {
        "file": "eval/fixtures/ibbi/nclt_born_digital_chd.pdf",
        "header": {
            "court_id": "crt_IN_NCLT_CHD",
            "bench_name": "Chandigarh Bench",
            "case_number_contains": "36/Chd/Pb/2026",
            "decision_date": "2026-09-24",
            "applicant": "Tegral India Private Limited",
            "respondent": "Aastha Autotech Private Limited",
        },
        "min_paras": 4,
        "max_paras": 6,
        "anchors": {
            "u1": "The present Application, IA(I.B.C)/1343(CH)2026, has been filed by the Applicant/Operational Creditor under Rule 8",
            "p2": "2. It is stated that the Company Petition, seeking initiation of Corporate Insolvency Resolution Process",
            "p3": "3. Pursuant to this Tribunal's order dated 09.09.2026, whereby three days' time was granted",
            "p4": "4. Having perused the Application, the Settlement Agreement dated 01.09.2026 annexed thereto",
            "p5": "5. Accordingly, IA(I.B.C)/1343(CH)2026 stands allowed and CP(IB) No. 36/Chd/Pb/2026 filed against the Respondent",
        },
    },
    "nclat_word_export": {
        "file": "eval/fixtures/ibbi/nclat_word_export.pdf",
        "header": {
            "court_id": "crt_IN_NCLAT",
            "bench_name": "Principal Bench New Delhi",
            "case_number_contains": "1073 of 2026",
            "decision_date": "2026-08-14",
            "applicant": "Rajesh Bansal",
            "respondent": "Axis Bank",
        },
        "min_paras": 4,
        "max_paras": 6,
        "anchors": {
            "u1": "14.08.2026: This order is passed in continuation of the order dated 12.08.2026.",
            "p2": "2. Learned Counsel for the Respondent however, submits though before the Ld. High Court",
            "p3": "3. It is the submission of the Learned Senior Counsel for the Appellant to show his bonafides",
            "p4": "4. Let the amount be deposited in the name of ‘Registrar, National Company Law Appellate Tribunal, New Delhi’",
            "p5": "5. List the matter on 06.10.2026.",
        },
    },
    "nclat_born_digital_del": {
        "file": "eval/fixtures/ibbi/nclat_born_digital_del.pdf",
        "header": {
            "court_id": "crt_IN_NCLAT",
            "bench_name": "Principal Bench New Delhi",
            "case_number_contains": "124 of 2026",
            "decision_date": "2026-09-09",
            "applicant": "Rathi Powertech Global",
            "respondent": "Hannu Steels",
        },
        "min_paras": 6,
        "max_paras": 10,
        "anchors": {
            "u1": "This application IA No. 5813 of 2026 has been filed by the Respondent/",
            "p2": "2. The judgment in CA (AT)(Ins) No. 124 of 2026 was passed on 06.07.2026.",
            "p3": "3. In particular, the applicant has highlighted the observations made in para 54",
            "p5": "5. We have gone through the documents on record in IA No. 5813 of 2026",
            "p9": "9. It is absolutely clear from the above that, Ld. Adjudicating Authority has to dispose of the matter",
        },
    },
    "nclt_scanned_ahm": {
        "file": "eval/fixtures/ibbi/nclt_scanned_ahm.pdf",
        "header": {
            "court_id": "crt_IN_NCLT_AHM",
            "bench_name": "Ahmedabad Bench",
            "case_number_contains": "302",
            "decision_date": "2026-09-24",
            "applicant": "Operational Creditor",
            "respondent": "Spright Agro",
        },
        "min_paras": 1,
        "max_paras": 15,
        "anchors": {
            "u1": "This case is fixed for pronouncement of order",
            "p9": "9. On issuance of notice dtd. 19.03.2026",
            "p10": "10. Observations",
            "ord": "ORDER",
            "p2016": "2016.",
        },
    },
    "nclt_scanned_ahm_2": {
        "file": "eval/fixtures/ibbi/sample_order_1.pdf",
        "header": {
            "court_id": "crt_IN_NCLT_AHM",
            "bench_name": "Ahmedabad Bench",
            "case_number_contains": "188",
            "decision_date": "2026-09-25",
            "applicant": "Sheth",
            "respondent": "Takshashila",
        },
        "min_paras": 4,
        "max_paras": 12,
        "anchors": {
            "u1": "This case is fixed for pronouncement of order",
            "p1": "1. These petitions are filed under Section 7 of the IBC",
            "p2": "2. It is submitted that the applicant granted a financial facility",
            "p9": "9. Observations and conclusions",
            "ord": "ORDER",
        },
    },
    "nclt_born_digital_mum": {
        "file": "eval/fixtures/ibbi/sample_order_2.pdf",
        "header": {
            "court_id": "crt_IN_NCLT_MUM",
            "bench_name": "Mumbai Bench",
            "case_number_contains": "507",
            "decision_date": "2026-09-24",
            "applicant": "Shirpur Gold",
            "respondent": "Magicstone",
        },
        "min_paras": 20,
        "max_paras": 80,
        "anchors": {
            "u1": "NATIONAL COMPANY LAW TRIBUNAL",
            "p1": "1.",
            "p2": "2.",
            "p3": "3.",
            "p4": "4.",
        },
    },
}
