import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("uvicorn")

# Runtime dir yang FIX (tidak bergantung pada pdf_path)
STORAGE_DIR = Path("/opt/Certificate-Service/app/storage").resolve()
LO_PROFILE_DIR = (STORAGE_DIR / ".libreoffice-profile").resolve()
XDG_CACHE_DIR = (STORAGE_DIR / ".cache").resolve()
XDG_CONFIG_DIR = (STORAGE_DIR / ".config").resolve()

# ---- LOCK (Linux only) ----
if sys.platform != "win32":
    import fcntl

    class LibreOfficeLock:
        def __init__(self, lock_path: str = "/tmp/libreoffice_convert.lock"):
            self.lock_path = lock_path
            self.fp = None

        def __enter__(self):
            self.fp = open(self.lock_path, "w")
            fcntl.flock(self.fp, fcntl.LOCK_EX)  # block sampai giliran
            return self

        def __exit__(self, exc_type, exc, tb):
            try:
                fcntl.flock(self.fp, fcntl.LOCK_UN)
            finally:
                self.fp.close()
                self.fp = None
else:
    from contextlib import nullcontext as LibreOfficeLock


def docx_to_pdf(docx_path, pdf_path):
    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if sys.platform == "win32":
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
        return

    # Pastikan runtime dir & output dir ada
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    LO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    XDG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    XDG_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # LibreOffice butuh format file:// untuk UserInstallation
    user_install = "file://" + LO_PROFILE_DIR.as_posix()

    cmd = [
        "libreoffice",
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--nodefault",
        "--norestore",
        f"-env:UserInstallation={user_install}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pdf_path.parent),
        str(docx_path),
    ]

    # Set env supaya LO/dconf tidak nulis ke lokasi lain (mis. /var/www)
    env = os.environ.copy()
    env["HOME"] = str(STORAGE_DIR)
    env["XDG_CACHE_HOME"] = str(XDG_CACHE_DIR)
    env["XDG_CONFIG_HOME"] = str(XDG_CONFIG_DIR)

    # 🔒 KUNCI: hanya 1 konversi LibreOffice pada satu waktu
    with LibreOfficeLock("/tmp/libreoffice_convert.lock"):
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                env=env,
            )

            created_pdf = pdf_path.parent / (docx_path.stem + ".pdf")
            if not created_pdf.exists():
                raise RuntimeError(
                    "LibreOffice selesai tapi file PDF tidak ditemukan. "
                    f"stdout={result.stdout.decode(errors='ignore')} "
                    f"stderr={result.stderr.decode(errors='ignore')}"
                )

            # Rename kalau nama target berbeda
            if created_pdf != pdf_path:
                if pdf_path.exists():
                    pdf_path.unlink()
                created_pdf.rename(pdf_path)

        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="ignore")
            stdout = e.stdout.decode(errors="ignore")
            logger.error(f"LibreOffice conversion failed. stdout={stdout} stderr={stderr}")
            raise RuntimeError(f"LibreOffice conversion error: {stderr or stdout}")
        except FileNotFoundError:
            logger.error("LibreOffice not found in system path.")
            raise RuntimeError("LibreOffice not found. Install: sudo apt-get install libreoffice")