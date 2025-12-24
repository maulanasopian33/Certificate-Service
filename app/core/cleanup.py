import time
import logging
from pathlib import Path
from app.config import settings

logger = logging.getLogger("uvicorn")

DAYS_TO_KEEP = 7

def cleanup_old_files():
    """
    Menghapus file di folder storage yang lebih tua dari DAYS_TO_KEEP hari.
    Dijalankan otomatis oleh Scheduler.
    """
    # Menggunakan path dari settings
    storage_base = Path(settings.STORAGE_PATH)
    
    # Folder target (relative terhadap storage path)
    folders = [
        storage_base / "output/pdf",
        storage_base / "output/docx",
        storage_base / "qr"
    ]

    limit_seconds = DAYS_TO_KEEP * 86400
    now = time.time()
    
    logger.info(f"--- Starting Cleanup Job (Limit: {DAYS_TO_KEEP} days) ---")
    deleted_count = 0

    for target_dir in folders:
        if not target_dir.exists():
            continue
            
        for file_path in target_dir.iterdir():
            if file_path.is_file() and file_path.name != ".gitkeep":
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > limit_seconds:
                        file_path.unlink()
                        logger.info(f"[CLEANUP] Deleted old file: {file_path.name}")
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"[CLEANUP] Error deleting {file_path.name}: {e}")
    
    logger.info(f"--- Cleanup Finished. Total deleted: {deleted_count} ---")