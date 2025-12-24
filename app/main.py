from fastapi import FastAPI, Depends
from app.config import settings
from fastapi import Header, HTTPException
from fastapi.staticfiles import StaticFiles
from app.core.worker import job_queue, start_worker
from typing import Union, List, Dict, Optional
from pydantic import BaseModel
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.cleanup import cleanup_old_files

app = FastAPI()

# Inisialisasi Scheduler
scheduler = BackgroundScheduler()

# Pastikan folder storage ada dan mount ke URL /storage
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")

# Model data agar lebih rapi (opsional, tapi disarankan untuk validasi)
class GenerateRequest(BaseModel):
    data: Dict # Data sertifikat (nama, no, dll)
    callback_url: Optional[str] = None # URL untuk notifikasi saat selesai

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.on_event("startup")
def startup_event():
    # Menjalankan background worker saat aplikasi mulai
    start_worker()
    
    # Menjadwalkan cleanup job setiap 24 jam (1 hari)
    scheduler.add_job(cleanup_old_files, 'interval', days=1, id='daily_cleanup')
    scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.post("/generate", dependencies=[Depends(verify_api_key)])
def generate(payload: Union[GenerateRequest, List[GenerateRequest]]):
    """
    Menerima single request atau list request (bulk).
    Langsung return 202 Accepted.
    """
    requests_list = payload if isinstance(payload, list) else [payload]
    
    for req in requests_list:
        job_queue.put(req.model_dump())

    return {"status": "queued", "message": f"{len(requests_list)} task(s) added to queue."}

@app.get("/health")
def health():
    return {"status": "ok"}
