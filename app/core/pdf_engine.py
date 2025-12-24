# app/core/pdf_engine.py
from docx2pdf import convert

def docx_to_pdf(docx_path, pdf_path):
    convert(docx_path, pdf_path)
