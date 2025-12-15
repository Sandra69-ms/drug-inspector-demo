# ocr_matcher.py
import os
import re
import csv
from pdf2image import convert_from_path
import pytesseract
from rapidfuzz import fuzz

# ---------------- CONFIG ----------------
POPPLER_PATH = os.getenv("POPPLER_PATH")

# Canonical banned generics (lowercase)
BANNED_KEYWORDS = {
    "nimesulide",
}

FUZZY_THRESHOLD = 85
# --------------------------------------


def pdf_to_images(pdf_path):
    if POPPLER_PATH:
        return convert_from_path(pdf_path, dpi=200, poppler_path=POPPLER_PATH)
    return convert_from_path(pdf_path, dpi=200)


def ocr_image(image):
    return pytesseract.image_to_string(image, lang="eng")


def ocr_pdf_text(pdf_path):
    images = pdf_to_images(pdf_path)
    return [ocr_image(img) for img in images]


# ---------------- TEXT NORMALIZATION ----------------
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------- DATASET ----------------
def load_dataset_csv(csv_paths):
    rows = []
    for p in csv_paths:
        if not p or not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append({
                    "brand": r.get("brand", "").strip(),
                    "generic": r.get("generic", "").strip(),
                    "is_banned": str(r.get("is_banned", "")).lower() == "true",
                    "batch": r.get("batch", "").strip()
                })
    return rows


# ---------------- CORE MATCHER ----------------
def find_banned_drugs_in_invoice(ocr_texts, dataset_rows):
    """
    Returns ONLY banned drugs actually present in the invoice
    """

    invoice_text = normalize("\n".join(ocr_texts))
    found_banned = set()

    for r in dataset_rows:
        if not r["is_banned"]:
            continue

        generic = normalize(r["generic"])
        if not generic:
            continue

        # -------- Exact / substring match (preferred) --------
        if generic in invoice_text:
            found_banned.add(r["generic"])
            continue

        # -------- Fuzzy match fallback --------
        score = fuzz.partial_ratio(generic, invoice_text)
        if score >= FUZZY_THRESHOLD:
            found_banned.add(r["generic"])

    # -------- Safety net (hard keywords) --------
    for kw in BANNED_KEYWORDS:
        if kw in invoice_text:
            found_banned.add(kw.capitalize())

    return sorted(found_banned)


# ---------------- MAIN PIPELINE ----------------
def process_invoice(pdf_path, dataset_csvs):
    ocr_texts = ocr_pdf_text(pdf_path)
    dataset_rows = load_dataset_csv(dataset_csvs)

    banned_found = find_banned_drugs_in_invoice(
        ocr_texts,
        dataset_rows
    )

    return {
        "ocr_text": "\n".join(ocr_texts),
        "banned_drugs": banned_found
    }


