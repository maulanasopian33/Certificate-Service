from fastapi import FastAPI, Depends
from app.services.certificate_service import generate_certificate
from app.config import settings
from fastapi import Header, HTTPException

app = FastAPI()

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/generate", dependencies=[Depends(verify_api_key)])
def generate(data: dict):
    return generate_certificate(data)

@app.get("/health")
def health():
    return {"status": "ok"}
