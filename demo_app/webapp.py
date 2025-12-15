# demo_app/webapp.py

import os
import sys

# ---------- PATH FIX ----------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ----------------------------

from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from ocr_matcher import process_invoice

load_dotenv()

# ---------- CONFIG ----------
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff"}

app = Flask(__name__, template_folder="templates")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "drug-inspector-demo"

# ---------- DATASET PATHS ----------
DATA_CSVS = [
    os.path.join(PROJECT_ROOT, "output", "train", "train_dataset.csv"),
    os.path.join(PROJECT_ROOT, "output", "test", "test_dataset.csv"),
]

# ---------- HELPERS ----------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template(
        "index.html",
        filename=None,
        ocr_pages=None,
        banned_drugs=None
    )


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        flash("No file uploaded")
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        # ---------- FULL OCR + MATCH PIPELINE ----------
        result = process_invoice(
            pdf_path=file_path,
            dataset_csvs=DATA_CSVS
        )

        return render_template(
            "index.html",
            filename=filename,
            ocr_pages=[result["ocr_text"]],
            banned_drugs=result["banned_drugs"]
        )

    except Exception as e:
        flash(f"Processing failed: {e}")
        return redirect(url_for("index"))


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True, port=8001)









