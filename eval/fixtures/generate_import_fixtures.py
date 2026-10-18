"""Generate synthetic case import fixtures for R3 test suite."""

import csv
import io
import os
import zipfile
from datetime import date
import openpyxl
from openpyxl.utils.datetime import from_excel

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "import")
os.makedirs(FIXTURE_DIR, exist_ok=True)

SAMPLE_ROWS = [
    # --- Client 1: Acme Infra Ltd (4 matters) ---
    # 1. Standard IBC CP with future date (Acme v. Zenith matter used in Exit Checks 4-5)
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "PETITIONER", "Acme v. Zenith, s.9 petition", "IBC", "NCLT New Delhi Bench Court-II", "CP (IB) No. 421/ND/2024", "25/11/2026", "partner@lawfirm.in", "Section 9 petition for unpaid operational debt"],
    # 2. Case number from real NCLT fixture (nclt_causelist_1.pdf Court 4) -> EXACT match in Exit Check 3
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "PETITIONER", "Insolvency Petition vs Beta Corp", "IBC", "NCLT Mumbai Bench Court-IV", "CP (IB) 736/MB/2025", "21/10/2026", "partner@lawfirm.in", "Section 7 petition for operational debt"],
    # 3. Advisory matter with blank client role (warns in preview and sets NOT_SET)
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "", "Acme Restructuring Advisory", "Advisory", "NCLT New Delhi", "CA/99/ND/2024", "18/12/2026", "partner@lawfirm.in", "Scheme of arrangement"],
    # 4. Unparseable case number (unreadable #1, saved with track=false)
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "PETITIONER", "Commercial Arbitration with Builder", "Arbitration", "High Court of Karnataka", "ARB/COMM/SPECIAL/2023", "20/11/2026", "associate@lawfirm.in", "Non-standard citation format"],

    # --- Client 2: State Bank of Horizon (3 matters) ---
    # 5. Financial creditor claim with ambiguous day-first date #1 (06/07/2026)
    ["State Bank of Horizon", "COMPANY", "AAACS1234E", "PETITIONER", "Horizon CIRP Application", "IBC", "NCLT Mumbai Bench-I", "CP (IB)/888/MB/2024", "06/07/2026", "associate@lawfirm.in", "Financial creditor claim under section 7"],
    # 6. Commercial suit with unparseable case number #2 & ambiguous day-first date #2 (03/04/2026)
    ["State Bank of Horizon", "COMPANY", "AAACS1234E", "PLAINTIFF", "Recovery vs Defaulting Promoters", "Commercial Suit", "City Civil Court Bengaluru", "SUIT-COMM-BLR-01/2024", "03/04/2026", "associate@lawfirm.in", "Recovery suit"],
    # 7. Formula injection attempt in notes
    ["State Bank of Horizon", "COMPANY", "AAACS1234E", "PETITIONER", "Finlease vs Defaults", "IBC", "NCLT Mumbai Bench-II", "CP (IB)/600/MB/2024", "14/11/2026", "partner@lawfirm.in", "=cmd|' /C calc'!A0"],

    # --- Client 3: Zenith Global Pvt Ltd (3 matters) ---
    # 8. Appeal before NCLAT with native date object
    ["Zenith Global Pvt Ltd", "COMPANY", "U98765MH2015PTC654321", "APPELLANT", "Zenith Appeal against Liquidation Order", "Company Appeal", "NCLAT New Delhi", "Company Appeal (AT) (Insolvency) No. 102/2024", date(2026, 12, 10), "partner@lawfirm.in", "Stay on CoC constitution"],
    # 9. Execution petition
    ["Zenith Global Pvt Ltd", "COMPANY", "U98765MH2015PTC654321", "PETITIONER", "Arbitral Award Execution", "Execution", "Delhi High Court", "OMP (ENF) (COMM) 55/2024", "15/12/2026", "partner@lawfirm.in", "Execution of arbitral award"],
    # 10. Unreadable case number #3 & 'to be listed' string date
    ["Zenith Global Pvt Ltd", "COMPANY", "U98765MH2015PTC654321", "", "Zenith Patent Invalidation", "IP Dispute", "High Court of Bombay", "DIARY-NO-9999-2026", "to be listed", "associate@lawfirm.in", "Listing awaited"],

    # --- Client 4: Pinnacle Steel Ltd (3 matters) ---
    # 11. Past hearing date (imported as LISTED with past warning)
    ["Pinnacle Steel Ltd", "COMPANY", "L55555WB2005PLC555555", "APPLICANT", "Pinnacle Resolution Plan Approval", "IBC", "NCLT Kolkata Bench", "CP (IB)/12/KB/2023", "15/01/2024", "associate@lawfirm.in", "Historical hearing from last year"],
    # 12. Case in NCLT causelist fixture Court 4, entered with Court II -> Candidate match in Exit Check 3
    ["Pinnacle Steel Ltd", "COMPANY", "L55555WB2005PLC555555", "RESPONDENT", "Pinnacle Plant Equipment Dispute", "IBC", "NCLT Mumbai Bench Court-II", "CP (IB) 1388/MB/2020", "28/11/2026", "associate@lawfirm.in", "Plant equipment CIRP"],
    # 13. Dotted case number notation
    ["Pinnacle Steel Ltd", "COMPANY", "L55555WB2005PLC555555", "PETITIONER", "Pinnacle Invalidation Plea", "IBC", "NCLT New Delhi Bench-IV", "C.P. (IB) - 789 / ND / 2024", "19/11/2026", "associate@lawfirm.in", "Dotted case number notation"],

    # --- Client 5: Vanguard Estates (4 matters) ---
    # 14. Excel numeric serial date (46350)
    ["Vanguard Estates", "COMPANY", "U11111KA2018PTC111111", "PETITIONER", "CIRP against Vendor", "IBC", "NCLT Chennai Bench", "CP(IB)/45/CHE/2024", 46350, "partner@lawfirm.in", "Serial date cell"],
    # 15. Individual guarantor s.95 application
    ["Vanguard Estates", "COMPANY", "U11111KA2018PTC111111", "PETITIONER", "Personal Insolvency against Guarantor", "Personal Insolvency", "NCLT New Delhi Court-III", "CP (IB) No. 55/ND/2024", "05/11/2026", "associate@lawfirm.in", "Section 95 guarantor application"],
    # 16. Preferential avoidance IA
    ["Vanguard Estates", "COMPANY", "U11111KA2018PTC111111", "APPLICANT", "Preferential Transaction Avoidance", "IBC Avoidance", "NCLT Mumbai Bench-I", "IA(IBC)/124/MB/2024", "17/11/2026", "associate@lawfirm.in", "Section 43 avoidance petition"],
    # 17. Pre-litigation mediation with blank case number & blank date
    ["Vanguard Estates", "COMPANY", "U11111KA2018PTC111111", "", "Pre-litigation Insolvency Mediation", "Mediation", "Pre-filing", "", "", "partner@lawfirm.in", "Mediation in progress"],

    # --- Client 6: Aura Technologies (3 matters) ---
    # 18. Commercial suit
    ["Aura Technologies", "COMPANY", "U22222DL2019PTC222222", "PLAINTIFF", "Recovery Suit under Commercial Courts Act", "Commercial Suit", "Delhi High Court", "CS(COMM) 312/2024", "12/12/2026", "associate@lawfirm.in", "Summary commercial suit"],
    # 19. Unrecognized lawyer email warning
    ["Aura Technologies", "COMPANY", "U22222DL2019PTC222222", "DEFENDANT", "Goods Supply Contract Breach", "Commercial Suit", "Delhi High Court", "CS (COMM) 101/2024", "10/12/2026", "nonexistent_lawyer@lawfirm.in", "External briefing counsel"],
    # 20. Section 138 NI Act
    ["Aura Technologies", "COMPANY", "U22222DL2019PTC222222", "COMPLAINANT", "Negotiable Instruments Complaint", "Section 138 NI Act", "Patiala House Courts New Delhi", "CC NI ACT 450/2024", "08/12/2026", "associate@lawfirm.in", "Dishonour of cheque"],
]

HEADERS = [
    "client name",
    "client type",
    "CIN or PAN",
    "client role",
    "matter title",
    "case type",
    "court or forum",
    "case number",
    "next hearing date",
    "lead lawyer email",
    "notes",
]

def generate_xlsx():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Live Cases"
    ws.append(HEADERS)
    for r in SAMPLE_ROWS:
        ws.append(r)
    path = os.path.join(FIXTURE_DIR, "synthetic_cases_20.xlsx")
    wb.save(path)
    print(f"Created {path}")

def generate_csv():
    path = os.path.join(FIXTURE_DIR, "synthetic_cases_20.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        for r in SAMPLE_ROWS:
            row_copy = list(r)
            if isinstance(row_copy[8], date):
                row_copy[8] = row_copy[8].strftime("%d/%m/%Y")
            elif row_copy[8] == 46350:
                row_copy[8] = from_excel(46350).strftime("%d/%m/%Y")
            writer.writerow(row_copy)
    print(f"Created {path}")

def generate_malicious_xlsm():
    path = os.path.join(FIXTURE_DIR, "malicious_macro.xlsm")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="bin" ContentType="application/vnd.ms-office.vbaProject"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.ms-excel.sheet.macroEnabled.main+xml"/>'
            '</Types>'
        )
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("xl/vbaProject.bin", b"DUMMY_VBA_PROJECT_BINARY_STREAM")
        z.writestr("xl/workbook.xml", b"<workbook/>")
    with open(path, "wb") as f:
        f.write(buffer.getvalue())
    print(f"Created {path}")

if __name__ == "__main__":
    generate_xlsx()
    generate_csv()
    generate_malicious_xlsm()
