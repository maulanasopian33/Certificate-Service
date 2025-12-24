from docx import Document
from docx.shared import Inches

def fill_docx(template_path, output_path, data, qr_path):
    # PASTIKAN semua path jadi string
    doc = Document(str(template_path))

    for p in doc.paragraphs:
        # Replace text placeholder
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in p.text:
                p.text = p.text.replace(placeholder, value)

        # Replace QR placeholder
        if "[QR_CODE]" in p.text:
            p.text = ""
            run = p.add_run()
            run.add_picture(str(qr_path), width=Inches(1.5))

    doc.save(str(output_path))
