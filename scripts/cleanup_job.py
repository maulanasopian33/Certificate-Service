import os
import time
from pathlib import Path

# --- KONFIGURASI ---
DAYS_TO_KEEP = 7  # File yang lebih tua dari 7 hari akan dihapus
FOLDERS_TO_CLEAN = [
    "app/storage/output/pdf",
    "app/storage/output/docx",
    "app/storage/qr"
]

def cleanup_old_files():
    # Mendapatkan path root project (asumsi script ini ada di root project)
    base_dir = Path(__file__).parent
    limit_seconds = DAYS_TO_KEEP * 86400 # Konversi hari ke detik
    now = time.time()
    
    print(f"--- Memulai Cleanup Job (Batas: {DAYS_TO_KEEP} hari) ---")

    for folder in FOLDERS_TO_CLEAN:
        target_dir = base_dir / folder
        
        if not target_dir.exists():
            print(f"Skipping (Folder not found): {target_dir}")
            continue
            
        print(f"Scanning folder: {folder}")
        deleted_count = 0
        
        for file_path in target_dir.iterdir():
            # Hapus jika file (bukan folder), bukan .gitkeep, dan umurnya melebihi batas
            if file_path.is_file() and file_path.name != ".gitkeep":
                try:
                    file_age = now - file_path.stat().st_mtime
                    if file_age > limit_seconds:
                        file_path.unlink() # Hapus file
                        print(f"  [DELETED] {file_path.name}")
                        deleted_count += 1
                except Exception as e:
                    print(f"  [ERROR] Gagal menghapus {file_path.name}: {e}")
        
        print(f"Selesai. Total dihapus: {deleted_count} file.\n")

if __name__ == "__main__":
    cleanup_old_files()