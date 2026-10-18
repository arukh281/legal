"""Generate synthetic case import fixtures for R3 test suite."""

import csv
import io
import os
import zipfile
from datetime import date, datetime
import openpyxl

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "import")
os.makedirs(FIXTURE_DIR, exist_ok=True)

SAMPLE_ROWS = [
    # 1. Standard IBC CP with valid CIN and future hearing date
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "Insolvency Petition vs Beta Corp", "IBC", "NCLT New Delhi Bench Court-II", "CP (IB) No. 421/ND/2024", "25/11/2026", "partner@lawfirm.in", "Section 9 petition for unpaid operational debt"],
    # 2. Financial creditor s.7 petition with ambiguous day-first date (06/07/2026)
    ["State Bank of Horizon", "COMPANY", "AAACS1234E", "Horizon CIRP Application", "IBC", "NCLT Mumbai Bench-I", "CP (IB)/888/MB/2024", "06/07/2026", "associate@lawfirm.in", "Financial creditor claim under section 7"],
    # 3. Appeal before NCLAT with date object
    ["Zenith Global Pvt Ltd", "COMPANY", "U98765MH2015PTC654321", "Zenith Appeal against Liquidation Order", "Company Appeal", "NCLAT New Delhi", "Company Appeal (AT) (Insolvency) No. 102/2024", date(2026, 12, 10), "partner@lawfirm.in", "Stay on CoC constitution"],
    # 4. Past hearing date (should be imported as LISTED with past warning)
    ["Pinnacle Steel Ltd", "COMPANY", "L55555WB2005PLC555555", "Pinnacle Resolution Plan Approval", "IBC", "NCLT Kolkata Bench", "CP (IB)/12/KB/2023", "15/01/2024", "associate@lawfirm.in", "Historical hearing from last year"],
    # 5. Unparseable case number (should be saved with track=false)
    ["Vanguard Estates", "COMPANY", "U11111KA2018PTC111111", "Commercial Arbitration with Builder", "Arbitration", "High Court of Karnataka", "ARB/COMM/SPECIAL/2023", "20/11/2026", "unknown_lawyer@lawfirm.in", "Non-standard citation format"],
    # 6. Matter with no case number (title matching only)
    ["Aura Technologies", "COMPANY", "U22222DL2019PTC222222", "Pre-litigation Insolvency Mediation", "Mediation", "Pre-filing", "", "", "partner@lawfirm.in", "Mediation in progress"],
    # 7. Same client as #1 (testing multiple matters under one client)
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "Acme Restructuring Advisory", "Advisory", "NCLT New Delhi", "CA/99/ND/2024", "18/12/2026", "partner@lawfirm.in", "Scheme of arrangement"],
    # 8. Individual client with PAN
    ["Rohan Sharma", "INDIVIDUAL", "ABCPS1234A", "Personal Insolvency against Guarantor", "Personal Insolvency", "NCLT New Delhi Court-III", "CP (IB) No. 55/ND/2024", "05/11/2026", "associate@lawfirm.in", "Section 95 guarantor application"],
    # 9. Excel serial date (numeric)
    ["Delta Logistics Ltd", "COMPANY", "U33333TN2012PTC333333", "CIRP against Vendor", "IBC", "NCLT Chennai Bench", "CP(IB)/45/CHE/2024", 46350, "partner@lawfirm.in", "Serial date cell"],
    # 10. Another individual client
    ["Vikram Malhotra", "INDIVIDUAL", "ABCPM5678B", "Recovery Suit under Commercial Courts Act", "Commercial Suit", "Delhi High Court", "CS(COMM) 312/2024", "12/12/2026", "associate@lawfirm.in", "Summary commercial suit"],
    # 11. Matter with notes containing formula injection attempt
    ["Secured Finlease Corp", "COMPANY", "U44444MH2011PLC444444", "Finlease vs Defaults", "IBC", "NCLT Mumbai Bench-II", "CP (IB)/600/MB/2024", "14/11/2026", "partner@lawfirm.in", "=cmd|' /C calc'!A0"],
    # 12. Row with non-standard case number spacing
    ["Blue Star Exports", "COMPANY", "U66666DL2008PLC666666", "Blue Star Invalidation Plea", "IBC", "NCLT New Delhi Bench-IV", "C.P. (IB) - 789 / ND / 2024", "19/11/2026", "associate@lawfirm.in", "Dotted case number notation"],
    # 13. Case with second sheet reference or notes
    ["Omicron Biotech", "COMPANY", "U77777KA2020PTC777777", "Biotech Patent Dispute", "Commercial Suit", "High Court of Bombay", "COMMS 45/2024", "22/11/2026", "partner@lawfirm.in", "IP litigation"],
    # 14. Section 7 financial debt
    ["Sunrise Power Ltd", "COMPANY", "L88888GJ2000PLC888888", "Sunrise CIRP Admission", "IBC", "NCLT Ahmedabad Bench", "CP(IB) 34/AHM/2024", "28/11/2026", "associate@lawfirm.in", "Thermal power plant project debt"],
    # 15. Operational creditor section 9
    ["Silverline Shipping", "COMPANY", "U99999MH2014PTC999999", "Vessel Demurrage Claim", "Admiralty", "Bombay High Court", "ADM 12/2024", "02/12/2026", "partner@lawfirm.in", "Maritime lien"],
    # 16. Matter with lead lawyer not in firm
    ["Northwind Traders", "COMPANY", "U12121DL2016PTC121212", "Goods Supply Contract Breach", "Commercial Suit", "Delhi High Court", "CS (COMM) 101/2024", "10/12/2026", "nonexistent_lawyer@lawfirm.in", "External briefing counsel"],
    # 17. Duplicate case number in batch (same as #1, will be flagged duplicate)
    ["Acme Infra Ltd", "COMPANY", "L12345DL2010PLC123456", "Insolvency Petition vs Beta Corp - Duplicate", "IBC", "NCLT New Delhi Bench Court-II", "CP (IB) No. 421/ND/2024", "25/11/2026", "partner@lawfirm.in", "Duplicate row in same batch"],
    # 18. IBC avoidance application
    ["Crest Pharmaceuticals", "COMPANY", "L13131MH2002PLC131313", "Preferential Transaction Avoidance", "IBC Avoidance", "NCLT Mumbai Bench-I", "IA(IBC)/124/MB/2024", "17/11/2026", "associate@lawfirm.in", "Section 43 avoidance petition"],
    # 19. Cheque bounce s.138
    ["Apex Retailers", "COMPANY", "U14141DL2017PTC141414", "Negotiable Instruments Complaint", "Section 138 NI Act", "Patiala House Courts New Delhi", "CC NI ACT 450/2024", "08/12/2026", "associate@lawfirm.in", "Dishonour of cheque"],
    # 20. Execution petition
    ["Zenith Global Pvt Ltd", "COMPANY", "U98765MH2015PTC654321", "Arbitral Award Execution", "Execution", "Delhi High Court", "OMP (ENF) (COMM) 55/2024", "15/12/2026", "partner@lawfirm.in", "Execution of arbitral award"]
]

HEADERS = [
    "client name",
    "client type",
    "CIN or PAN",
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
            # For serial date in CSV, write date string or serial
            row_copy = list(r)
            if isinstance(row_copy[7], date):
                row_copy[7] = row_copy[7].strftime("%d/%m/%Y")
            elif row_copy[7] == 46350:
                row_copy[7] = "24/11/2026"
            writer.writerow(row_copy)
    print(f"Created {path}")

def generate_malicious_xlsm():
    path = os.path.join(FIXTURE_DIR, "malicious_macro.xlsm")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        # Standard xlsx files have [Content_Types].xml
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
