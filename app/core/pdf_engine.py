from docx2pdf import convert

def docx_to_pdf(docx_path, pdf_path):
    convert(str(docx_path), str(pdf_path))
