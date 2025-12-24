import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("uvicorn")

def docx_to_pdf(docx_path, pdf_path):
    """
    Konversi DOCX ke PDF.
    - Windows: Menggunakan docx2pdf (MS Word).
    - Linux: Menggunakan LibreOffice (Headless).
    """
    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if sys.platform == "win32":
        # Windows: Gunakan docx2pdf (Butuh MS Word terinstall)
        # Import di dalam fungsi agar tidak error saat install di Linux
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
    else:
        # Linux: Gunakan LibreOffice Headless
        # Requirement di Server: sudo apt-get install libreoffice
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_path.parent),
            str(docx_path)
        ]
        
        try:
            # Menjalankan command line LibreOffice
            subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            
            # LibreOffice otomatis menamai output sesuai nama file input (file.docx -> file.pdf)
            # Kita cek apakah nama file output sesuai dengan pdf_path yang diinginkan
            created_pdf = pdf_path.parent / (docx_path.stem + ".pdf")
            
            if created_pdf.exists() and created_pdf != pdf_path:
                # Rename jika nama file target berbeda dari default LibreOffice
                if pdf_path.exists():
                    pdf_path.unlink()
                created_pdf.rename(pdf_path)
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode()
            logger.error(f"LibreOffice conversion failed: {error_msg}")
            raise RuntimeError(f"LibreOffice conversion error: {error_msg}")
        except FileNotFoundError:
            logger.error("LibreOffice not found in system path.")
            raise RuntimeError("LibreOffice not found. Please install: sudo apt-get install libreoffice")
