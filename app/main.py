from fastapi import FastAPI, Depends, Request
from app.config import settings
from fastapi import Header, HTTPException
from fastapi.staticfiles import StaticFiles
from app.core.worker import job_queue, start_worker, stop_event
from typing import Union, List, Dict, Optional
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.cleanup import cleanup_old_files

app = FastAPI()

# SECURITY: Konfigurasi CORS
# Di production, ubah allow_origins=["*"] menjadi domain frontend Anda, misal ["https://my-app.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inisialisasi Scheduler
scheduler = BackgroundScheduler()

logger = logging.getLogger("uvicorn")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"Validation Error: {exc}")
    logger.error(f"Received Body: {body.decode()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": body.decode()},
    )

# Pastikan folder storage ada dan mount ke URL /storage
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")

# Model khusus untuk validasi data sertifikat
class CertificateData(BaseModel):
    certificate_number: str
    qr_token: str
    verify_url: str
    
    # Mengizinkan field tambahan (nama, event, score, dll) untuk template
    model_config = {"extra": "allow"}

# Model data agar lebih rapi (opsional, tapi disarankan untuk validasi)
class GenerateRequest(BaseModel):
    data: CertificateData # Menggunakan model spesifik, bukan sekadar Dict
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
    # Memberi sinyal ke worker untuk berhenti setelah tugas saat ini selesai
    stop_event.set()
    scheduler.shutdown()

@app.post("/generate", dependencies=[Depends(verify_api_key)])
def generate(payload: Union[List[GenerateRequest], GenerateRequest]):
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
