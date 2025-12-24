import threading
import queue
import requests
import logging
import psutil
import os
import gc
from app.services.certificate_service import generate_certificate

# Inisialisasi Queue
job_queue = queue.Queue()

# Event untuk menghentikan worker secara graceful
stop_event = threading.Event()

logger = logging.getLogger("uvicorn")

def log_memory_usage(stage: str):
    """
    Mencatat penggunaan RAM saat ini oleh proses Python.
    """
    process = psutil.Process(os.getpid())
    # RSS (Resident Set Size) adalah memori fisik yang digunakan
    mem_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"[RAM-ANALYSIS] {stage}: {mem_mb:.2f} MB")

def worker():
    """
    Fungsi ini berjalan di thread terpisah.
    Mengambil tugas dari queue dan memprosesnya satu per satu (Serial).
    """
    while not stop_event.is_set():
        try:
            # Ambil item dari queue dengan timeout 1 detik agar bisa cek stop_event secara berkala
            task = job_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        try:
            data = task.get("data")
            callback_url = task.get("callback_url")
            
            logger.info(f"Processing certificate: {data.get('certificate_number')}")
            
            log_memory_usage("Before Generate")
            # Proses Generate (Berat/Lama)
            result = generate_certificate(data)
            log_memory_usage("After Generate")
            
            # Paksa Garbage Collection untuk membersihkan objek yang tidak terpakai
            gc.collect()
            log_memory_usage("After GC")
            
            # Kirim Callback jika url disediakan
            if callback_url:
                try:
                    payload = {
                        "status": "success",
                        "original_data": data,
                        "result": result
                    }
                    requests.post(callback_url, json=payload, timeout=10)
                    logger.info(f"Callback sent to {callback_url}")
                except Exception as e:
                    logger.error(f"Failed to send callback: {e}")
                    
        except Exception as e:
            # Log error dengan traceback singkat atau pesan jelas untuk production monitoring
            logger.critical(f"[WORKER ERROR] Failed to generate certificate. Error: {str(e)} | Data: {task.get('data')}")
        finally:
            # Menandakan tugas selesai di queue
            job_queue.task_done()

# Jalankan worker thread saat modul di-load (atau dipanggil via startup event)
def start_worker():
    t = threading.Thread(target=worker, daemon=True)
    t.start()