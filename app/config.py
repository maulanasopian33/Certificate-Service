# app/config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATE_PATH = BASE_DIR / "app/templates/certificate.docx"

DOCX_OUTPUT = BASE_DIR / "app/storage/output/docx"
PDF_OUTPUT  = BASE_DIR / "app/storage/output/pdf"
QR_OUTPUT   = BASE_DIR / "app/storage/qr"

VERIFY_URL = "https://sertifikat.devlokal.id/verify"
