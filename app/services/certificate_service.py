from pathlib import Path
from app.core.qr_engine import generate_qr
from app.core.docx_engine import fill_docx
from app.core.pdf_engine import docx_to_pdf

BASE = Path("app/storage")

def generate_certificate(data: dict):
    cert_no = data["certificate_number"]

    pdf_path = BASE / "output/pdf" / f"{cert_no}.pdf"
    docx_path = BASE / "output/docx" / f"{cert_no}.docx"
    qr_path = BASE / "qr" / f"{data['qr_token']}.png"

    # Idempotent
    if pdf_path.exists():
        return {
            "pdf_path": str(pdf_path),
            "download_url": f"/storage/output/pdf/{cert_no}.pdf"
        }

    generate_qr(data["verify_url"], qr_path)

    fill_docx(
        template_path="app/templates/certificate.docx",
        output_path=docx_path,
        context=data,
        qr_path=qr_path
    )

    docx_to_pdf(docx_path, pdf_path)

    return {
        "pdf_path": str(pdf_path),
        "download_url": f"/storage/output/pdf/{cert_no}.pdf"
    }
