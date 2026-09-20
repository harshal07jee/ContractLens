"""Generate the reproducible ContractLens demo contract."""
from pathlib import Path

import pymupdf as fitz


OUTPUT = Path(__file__).resolve().parents[1] / "sample_contracts" / "Enterprise_Service_Agreement.pdf"

PAGES = [
    """ENTERPRISE SERVICE AGREEMENT

This Enterprise Service Agreement (Agreement) is entered into by and between ABC Technologies, Inc. (Vendor) and XYZ Retail, LLC (Customer).

1. PURPOSE

Vendor will provide managed analytics, reporting, and support services to Customer under the terms of this Agreement.

2. TERM

The Effective Date is October 1, 2026. This Agreement expires on December 31, 2027, unless earlier terminated in accordance with Section 7.
""",
    """3. SERVICES AND REPORTING

Vendor shall provide the services described in the applicable statement of work.

Vendor shall submit monthly performance reports to Customer no later than the fifth business day of each month. Each report must describe service availability, open incidents, and agreed performance metrics.

Customer shall provide Vendor with reasonable access to the systems and contacts required to perform the services.
""",
    """4. FEES AND PAYMENT

Customer must pay each undisputed invoice within 30 days after invoice receipt. Invoices are issued monthly in arrears.

Late payments may accrue interest at the rate permitted by applicable law after Vendor gives Customer written notice of the overdue amount.

5. CONFIDENTIALITY

Each party shall protect the other party's confidential information and use it only to perform this Agreement.
""",
    """6. RENEWAL

This Agreement will automatically renew for successive 12-month periods unless either party gives the other party written notice of non-renewal at least 60 days before the then-current expiration date.

7. TERMINATION

Either party may terminate this Agreement for material breach if the breach is not cured within 30 days after written notice. Either party may also terminate for convenience by providing 30 days prior written notice.

8. DATA PROTECTION

Vendor shall process Customer data only as necessary to provide the services and shall maintain reasonable administrative, technical, and physical safeguards.
""",
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = fitz.open()
    for index, content in enumerate(PAGES, start=1):
        page = document.new_page(width=612, height=792)
        page.insert_textbox(fitz.Rect(72, 72, 540, 685), content, fontsize=11, fontname="helv", lineheight=1.55)
        page.insert_text((72, 730), f"Enterprise Service Agreement | Page {index}", fontsize=9, fontname="helv", color=(0.35, 0.4, 0.5))
    document.set_metadata({"title": "Enterprise Service Agreement", "author": "ContractLens Demo"})
    document.save(OUTPUT)
    document.close()
    print(OUTPUT)


if __name__ == "__main__":
    main()
