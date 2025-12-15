"""
generate_demo_dataset.py
Generates demo dataset:
- Train invoices (PDF + CSV + JSON)
- Test invoices (PDF + CSV + JSON)
"""

import os
import random
import csv
import json
import string
import shutil
from datetime import datetime, timedelta

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.graphics.barcode import code128

# ------------------ CONFIG ------------------
NUM_TRAIN = 100
NUM_TEST = 50
OUT_DIR = "output"
TRAIN_DIR = os.path.join(OUT_DIR, "train")
TEST_DIR = os.path.join(OUT_DIR, "test")

# ------------------ PREP FOLDERS ------------------
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)

os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(TEST_DIR, exist_ok=True)

# ------------------ FONTS / STYLES ------------------
styles = getSampleStyleSheet()

try:
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    styles["Normal"].fontName = "HeiseiMin-W3"
    styles["Title"].fontName = "HeiseiMin-W3"
except:
    pass  # safe fallback

# ------------------ UTILITIES ------------------
def format_inr(x):
    """Format number as INR currency."""
    return f"₹{x:,.2f}"

def random_batch():
    """Generate a random batch number."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ------------------ FIXED DRUG POOL ------------------
drug_pool = [
    ("Analgin", "Metamizole", "500mg", True),
    ("Nimesulide DT", "Nimesulide", "100mg", True),
    ("Corex", "Codeine + CPM", "10mg/4mg", True),
    ("Saridon", "Paracetamol Combo", "250/150/50mg", True),
    ("Dolo 650", "Paracetamol", "650mg", False),
    ("Cefixime 200", "Cefixime", "200mg", False),
    ("Azithral 500", "Azithromycin", "500mg", False),
    ("Cetcip", "Cetirizine", "10mg", False),
    ("Oflox-OZ", "Ofloxacin + Ornidazole", "200/500mg", False),
    ("Amoxyclav", "Amoxicillin + Clavulanic Acid", "500/125mg", False)
]

pharmacies = [
    "CityMed Pharmacy",
    "WellCare Medicals",
    "GreenLife Drug House",
    "TrustCare Pharma",
    "HealthPlus Medical Store"
]

# ------------------ PDF GENERATION ------------------
def write_invoice(pdf_path, inv_id, pharmacy, date, doctor_id, items):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []

    # Header
    header_html = (
        f"<b>{pharmacy}</b><br/>"
        f"GSTIN: 32ABCDE1234F1Z<br/>"
        f"Address: Kochi, Kerala<br/>"
        f"Doctor Prescription: {doctor_id}<br/>"
    )
    story.append(Paragraph(header_html, styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"<b>Invoice No:</b> {inv_id}<br/><b>Date:</b> {date.strftime('%d-%m-%Y')}", styles["Normal"]))
    story.append(Spacer(1, 8))

    # Barcode
    barcode = code128.Code128(inv_id, barHeight=30)
    story.append(barcode)
    story.append(Spacer(1, 8))

    # Table structure
    table_data = [
        ["#", "Brand", "Generic", "Strength", "Batch", "Qty", "MRP", "GST%", "Line Total"]
    ]

    for idx, it in enumerate(items, start=1):
        table_data.append([
            idx,
            it["brand"],
            it["generic"],
            it["strength"],
            it["batch"],
            it["qty"],
            format_inr(it["price"]),
            f"{it['gst']}%",
            format_inr(it["line_total"]),
        ])

    table = Table(table_data, hAlign="LEFT")
    story.append(table)
    story.append(Spacer(1, 10))

    total_amount = sum(it["line_total"] for it in items)
    total_gst = sum(it["gst_amount"] for it in items)

    story.append(Paragraph(f"<b>Grand Total: {format_inr(total_amount)}</b>", styles["Heading2"]))
    story.append(Paragraph(f"GST Total: {format_inr(total_gst)}", styles["Normal"]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("<i>Authorized Signature</i><br/>_________________", styles["Normal"]))

    doc.build(story)

# ------------------ GENERATE INVOICE ------------------
def generate_invoice(inv_id, outdir):
    pharmacy = random.choice(pharmacies)
    date = datetime.now() - timedelta(days=random.randint(1, 365))
    doctor_id = "DR-" + ''.join(random.choices(string.digits, k=6))

    n_items = random.randint(2, 4)
    items = []

    for _ in range(n_items):
        brand, generic, strength, is_banned = random.choice(drug_pool)
        qty = random.randint(1, 3)
        price = round(random.uniform(30, 400), 2)
        gst = random.choice([5, 12, 18])

        gst_amount = price * qty * gst / 100
        line_total = price * qty + gst_amount

        items.append({
            "brand": brand,
            "generic": generic,
            "strength": strength,
            "qty": qty,
            "price": price,
            "gst": gst,
            "gst_amount": gst_amount,
            "line_total": line_total,
            "batch": random_batch(),
            "is_banned": is_banned
        })

    pdf_path = os.path.join(outdir, f"{inv_id}.pdf")
    write_invoice(pdf_path, inv_id, pharmacy, date, doctor_id, items)

    return {
        "invoice_id": inv_id,
        "pdf": pdf_path,
        "pharmacy": pharmacy,
        "date": date.strftime("%Y-%m-%d"),
        "doctor": doctor_id,
        "items": items
    }

# ------------------ SAVE DATASET ------------------
def save_dataset(records, outdir, name):
    json_path = os.path.join(outdir, f"{name}.json")
    csv_path = os.path.join(outdir, f"{name}.csv")

    with open(json_path, "w", encoding="utf-8") as jf, open(csv_path, "w", newline="", encoding="utf-8") as cf:
        json.dump(records, jf, indent=2, ensure_ascii=False)

        writer = csv.writer(cf)
        writer.writerow(["invoice_id", "pdf", "pharmacy", "date", "doctor", "brand",
                         "generic", "strength", "batch", "qty", "price", "gst",
                         "line_total", "is_banned"])

        for rec in records:
            for item in rec["items"]:
                writer.writerow([
                    rec["invoice_id"],
                    rec["pdf"],
                    rec["pharmacy"],
                    rec["date"],
                    rec["doctor"],
                    item["brand"],
                    item["generic"],
                    item["strength"],
                    item["batch"],
                    item["qty"],
                    f"{item['price']:.2f}",
                    item["gst"],
                    f"{item['line_total']:.2f}",
                    item["is_banned"]
                ])

# ------------------ MAIN ------------------
def main():
    print("Generating TRAIN dataset...")
    train_records = [generate_invoice(f"TRAIN-{i+1:04d}", TRAIN_DIR) for i in range(NUM_TRAIN)]
    save_dataset(train_records, TRAIN_DIR, "train_dataset")

    print("Generating TEST dataset...")
    test_records = [generate_invoice(f"TEST-{i+1:04d}", TEST_DIR) for i in range(NUM_TEST)]
    save_dataset(test_records, TEST_DIR, "test_dataset")

    print("\nDataset generation completed!")
    print("Output folder:", os.path.abspath(OUT_DIR))

if __name__ == "__main__":
    main()

