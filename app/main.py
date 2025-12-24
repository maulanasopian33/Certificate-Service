# app/main.py
from fastapi import FastAPI
from app.services.certificate_service import generate_certificate

app = FastAPI(title="Certificate Generator")

@app.post("/generate")
def generate(data: dict):
    return generate_certificate(data)
