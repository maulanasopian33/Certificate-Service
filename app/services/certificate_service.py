# app/services/certificate_service.py
import uuid
from datetime import date

from app.core.qr_engine import generate_qr
from app.core.docx_engine import fill_docx
from app.core.pdf_engine import docx_to_pdf
from app.config import DOCX_OUTPUT, PDF_OUTPUT, QR_OUTPUT, VERIFY_URL, TEMPLATE_PATH

def generate_certificate(data):
    cert_id = str(uuid.uuid4())[:8]
    cert_number = f"CERT-{cert_id}"

    qr_data = f"{VERIFY_URL}?id={cert_number}"
    qr_path = QR_OUTPUT / f"{cert_number}.png"

    generate_qr(qr_data, str(qr_path))

    payload = {
        "name": data["name"],
        "event_name": data["event_name"],
        "date": date.today().strftime("%d %B %Y"),
        "certificate_number": cert_number
    }

    docx_path = DOCX_OUTPUT / f"{cert_number}.docx"
    pdf_path  = PDF_OUTPUT / f"{cert_number}.pdf"

    fill_docx(
        template_path=TEMPLATE_PATH,
        output_path=docx_path,
        data=payload,
        qr_path=qr_path
    )

    docx_to_pdf(str(docx_path), str(pdf_path))

    return {
        "certificate_number": cert_number,
        "pdf": str(pdf_path)
    }
