import threading
import queue
import requests
import logging
from app.services.certificate_service import generate_certificate

# Inisialisasi Queue
job_queue = queue.Queue()

logger = logging.getLogger("uvicorn")

def worker():
    """
    Fungsi ini berjalan di thread terpisah.
    Mengambil tugas dari queue dan memprosesnya satu per satu (Serial).
    """
    while True:
        # Ambil item dari queue (blocking jika kosong)
        task = job_queue.get()
        
        try:
            data = task.get("data")
            callback_url = task.get("callback_url")
            
            logger.info(f"Processing certificate: {data.get('certificate_number')}")
            
            # Proses Generate (Berat/Lama)
            result = generate_certificate(data)
            
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
            logger.error(f"Error processing task: {e}")
        finally:
            # Menandakan tugas selesai di queue
            job_queue.task_done()

# Jalankan worker thread saat modul di-load (atau dipanggil via startup event)
def start_worker():
    t = threading.Thread(target=worker, daemon=True)
    t.start()