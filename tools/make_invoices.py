"""Generate 20 FAKE invoices (US + UK, 5 layouts) and a ground-truth CSV.
All vendors, addresses and numbers are invented. Run: python tools/make_invoices.py
"""
import csv, os, random
from datetime import date, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "..", "01-invoice-ingestion", "sample_invoices")
os.makedirs(OUT, exist_ok=True)

# (vendor, region, category, line items [(desc, unit price, qty)], tax_rate)
V = [
    ("Brightline Software Inc.", "US", "Software & Subscriptions", [("Team plan, 12 seats, monthly", 18.00, 12)], 0.0825),
    ("Maple & Pine Office Supply", "US", "Office Supplies", [("Copy paper, 10 reams", 6.50, 10), ("Toner cartridge", 74.00, 2)], 0.07),
    ("Skyway Travel Co.", "US", "Travel", [("Flight JFK-ORD return", 342.00, 1), ("Seat selection", 25.00, 1)], 0.0),
    ("Harbor Grill & Catering", "US", "Meals & Entertainment", [("Client lunch, 6 guests", 28.50, 6)], 0.0875),
    ("Northgrid Electric", "US", "Utilities", [("Electricity usage, Mar", 1.00, 412.30)], 0.05),
    ("Calloway & Reed LLP", "US", "Professional Fees", [("Contract review, hours", 225.00, 3.5)], 0.0),
    ("Pixelbeam Ads", "US", "Marketing & Advertising", [("Social campaign, March", 1.00, 1200.00)], 0.0),
    ("Union Square Workspaces", "US", "Rent", [("Hot desk membership", 450.00, 2)], 0.0),
    ("Keystone Mutual", "US", "Insurance", [("Business liability premium Q1", 1.00, 865.00)], 0.0),
    ("ClearWave Telecom", "US", "Telecoms", [("Business fibre 500Mbps", 89.99, 1), ("Static IP", 15.00, 1)], 0.06),
    ("Thistle Stationery Ltd", "UK", "Office Supplies", [("A4 paper, 5 boxes", 24.00, 5), ("Ring binders", 2.40, 30)], 0.20),
    ("Cloudnine Hosting Ltd", "UK", "Software & Subscriptions", [("VPS Business, annual", 240.00, 1)], 0.20),
    ("Great Northern Rail", "UK", "Travel", [("Advance return Leeds-London", 86.50, 2)], 0.0),
    ("The Copper Kettle Cafe", "UK", "Meals & Entertainment", [("Team breakfast", 9.75, 8)], 0.20),
    ("Albion Energy plc", "UK", "Utilities", [("Gas and electricity, Feb", 1.00, 298.40)], 0.05),
    ("Whitcombe Accountancy", "UK", "Professional Fees", [("Year-end accounts preparation", 650.00, 1)], 0.20),
    ("Lantern Digital Marketing", "UK", "Marketing & Advertising", [("SEO retainer, March", 750.00, 1)], 0.20),
    ("Regent Business Centres", "UK", "Rent", [("Serviced office, March", 1100.00, 1)], 0.20),
    ("Firstline Bank Business", "UK", "Bank Charges", [("Monthly account fee", 18.00, 1), ("Card terminal rental", 12.50, 1)], 0.0),
    ("Orbit Tech Retail", "UK", "Equipment", [("27in monitor", 229.00, 2), ("Docking station", 119.00, 1)], 0.20),
]

def money(x, cur):
    return f"{cur}{x:,.2f}"

rows = []
for i, (vendor, region, cat, items, rate) in enumerate(V, start=1):
    d = date(2026, 3, 1) + timedelta(days=random.randint(0, 27))
    sub = round(sum(round(p * q, 2) for _, p, q in items), 2)
    tax = round(sub * rate, 2)
    total = round(sub + tax, 2)
    cur = "$" if region == "US" else "\u00a3"
    tax_label = "Sales Tax" if region == "US" else "VAT"
    inv_no = f"{random.choice(['INV','A','SI','R'])}-{random.randint(10000, 99999)}"
    date_str = d.strftime("%m/%d/%Y") if region == "US" else d.strftime("%d %B %Y")
    layout = (i - 1) % 5
    fn = os.path.join(OUT, f"invoice_{i:02d}.pdf")
    size = letter if region == "US" else A4
    c = canvas.Canvas(fn, pagesize=size)
    W, H = size
    inv_label = ["INVOICE", "Tax Invoice", "Invoice", "BILL", "STATEMENT OF CHARGES"][layout]
    total_label = ["Amount Due", "Total Payable", "Total", "Balance Due", "TOTAL DUE"][layout]
    tax_text = f"{tax_label} ({rate*100:.2f}%)" if rate else f"{tax_label} (0%)"
    no_label = ["Invoice No.", "Inv #", "Reference", "Bill #", "Doc ref"][layout]

    if layout == 0:  # classic: header left, table
        c.setFont("Helvetica-Bold", 20); c.drawString(50, H - 60, vendor)
        c.setFont("Helvetica", 10); c.drawString(50, H - 76, "100 Example Street, Sampleville")
        c.setFont("Helvetica-Bold", 16); c.drawRightString(W - 50, H - 60, inv_label)
        c.setFont("Helvetica", 10)
        c.drawRightString(W - 50, H - 78, f"{no_label}: {inv_no}")
        c.drawRightString(W - 50, H - 92, f"Date: {date_str}")
        y = H - 150
        c.setFont("Helvetica-Bold", 10); c.drawString(50, y, "Description"); c.drawRightString(W - 160, y, "Qty"); c.drawRightString(W - 50, y, "Amount")
        c.line(50, y - 4, W - 50, y - 4); y -= 20; c.setFont("Helvetica", 10)
        for desc, p, q in items:
            c.drawString(50, y, desc); c.drawRightString(W - 160, y, f"{q:g}"); c.drawRightString(W - 50, y, money(round(p*q, 2), cur)); y -= 16
        y -= 10
        c.drawRightString(W - 120, y, "Subtotal"); c.drawRightString(W - 50, y, money(sub, cur)); y -= 16
        c.drawRightString(W - 120, y, tax_text); c.drawRightString(W - 50, y, money(tax, cur)); y -= 20
        c.setFont("Helvetica-Bold", 12); c.drawRightString(W - 120, y, total_label); c.drawRightString(W - 50, y, money(total, cur))
    elif layout == 1:  # centered header, key/value block
        c.setFont("Helvetica-Bold", 22); c.drawCentredString(W / 2, H - 70, inv_label.upper())
        c.setFont("Helvetica-Bold", 13); c.drawCentredString(W / 2, H - 95, vendor)
        c.setFont("Helvetica", 10)
        y = H - 140
        for k, v in [(no_label, inv_no), ("Issued", date_str), ("Currency", "USD" if region == "US" else "GBP")]:
            c.drawString(60, y, f"{k}:"); c.drawString(160, y, v); y -= 15
        y -= 15
        for desc, p, q in items:
            c.drawString(60, y, f"{desc}  x{q:g} @ {money(p, cur)}"); y -= 15
        y -= 10
        c.drawString(60, y, f"Net: {money(sub, cur)}"); y -= 15
        c.drawString(60, y, f"{tax_text}: {money(tax, cur)}"); y -= 15
        c.setFont("Helvetica-Bold", 11); c.drawString(60, y, f"{total_label}: {money(total, cur)}")
    elif layout == 2:  # boxed, two columns, vendor at bottom
        c.rect(40, H - 200, W - 80, 160)
        c.setFont("Helvetica-Bold", 14); c.drawString(55, H - 65, inv_label)
        c.setFont("Helvetica", 10); c.drawString(55, H - 85, f"{no_label} {inv_no}"); c.drawString(55, H - 100, f"Dated {date_str}")
        y = H - 230
        for desc, p, q in items:
            c.drawString(55, y, desc); c.drawRightString(W - 55, y, money(round(p*q, 2), cur)); y -= 16
        y -= 20
        c.drawString(55, y, "Sub-total"); c.drawRightString(W - 55, y, money(sub, cur)); y -= 16
        c.drawString(55, y, tax_text); c.drawRightString(W - 55, y, money(tax, cur)); y -= 20
        c.setFont("Helvetica-Bold", 12); c.drawString(55, y, total_label); c.drawRightString(W - 55, y, money(total, cur))
        c.setFont("Helvetica", 9); c.drawString(55, 60, f"Issued by {vendor}. Thank you for your business.")
    elif layout == 3:  # minimal receipt-like
        c.setFont("Courier-Bold", 14); c.drawString(60, H - 60, vendor.upper())
        c.setFont("Courier", 10); y = H - 90
        for line in [f"{inv_label} {inv_no}", f"DATE {date_str}", "-" * 44]:
            c.drawString(60, y, line); y -= 14
        for desc, p, q in items:
            c.drawString(60, y, f"{desc[:28]:<28} {money(round(p*q,2), cur):>12}"); y -= 14
        c.drawString(60, y, "-" * 44); y -= 14
        c.drawString(60, y, f"{'SUBTOTAL':<28} {money(sub, cur):>12}"); y -= 14
        c.drawString(60, y, f"{tax_label.upper():<28} {money(tax, cur):>12}"); y -= 14
        c.setFont("Courier-Bold", 10); c.drawString(60, y, f"{total_label.upper():<28} {money(total, cur):>12}")
    else:  # letterhead with tax number, total top-right
        c.setFont("Helvetica-Bold", 18); c.drawString(50, H - 55, vendor)
        c.setFont("Helvetica", 9)
        tn = f"VAT Reg No. GB{random.randint(100000000, 999999999)}" if region == "UK" else f"EIN {random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        c.drawString(50, H - 70, tn)
        c.setFont("Helvetica-Bold", 14); c.drawRightString(W - 50, H - 55, f"{total_label}: {money(total, cur)}")
        c.setFont("Helvetica", 10); c.drawString(50, H - 120, f"{inv_label}  |  {no_label}: {inv_no}  |  {date_str}")
        y = H - 160
        for desc, p, q in items:
            c.drawString(50, y, f"{q:g} x {desc} @ {money(p, cur)}"); y -= 15
        y -= 10
        c.drawString(50, y, f"Goods/services total: {money(sub, cur)}"); y -= 15
        c.drawString(50, y, f"{tax_text}: {money(tax, cur)}")
    c.save()
    rows.append(dict(file=f"invoice_{i:02d}.pdf", vendor=vendor, invoice_number=inv_no, date=d.isoformat(),
                     currency="USD" if region == "US" else "GBP", subtotal=f"{sub:.2f}", tax=f"{tax:.2f}",
                     total=f"{total:.2f}", category=cat, region=region))

with open(os.path.join(OUT, "..", "ground_truth.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", len(rows), "invoices")
