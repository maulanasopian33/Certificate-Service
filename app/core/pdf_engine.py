import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger("uvicorn")

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
    # dummy context manager for windows
    from contextlib import nullcontext as LibreOfficeLock


def docx_to_pdf(docx_path, pdf_path):
    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if sys.platform == "win32":
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
        return

    # === Linux: LibreOffice headless ===
    base_dir = pdf_path.parent.parent if pdf_path.parent.name else pdf_path.parent
    lo_profile_dir = (base_dir / ".libreoffice-profile").resolve()
    xdg_cache_dir = (base_dir / ".cache").resolve()
    xdg_config_dir = (base_dir / ".config").resolve()

    lo_profile_dir.mkdir(parents=True, exist_ok=True)
    xdg_cache_dir.mkdir(parents=True, exist_ok=True)
    xdg_config_dir.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    user_install = "file://" + lo_profile_dir.as_posix()

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

    env = os.environ.copy()
    env["HOME"] = str(base_dir)
    env["XDG_CACHE_HOME"] = str(xdg_cache_dir)
    env["XDG_CONFIG_HOME"] = str(xdg_config_dir)

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