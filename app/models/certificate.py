# app/models/certificate.py
from pydantic import BaseModel

class CertificateData(BaseModel):
    name: str
    event_name: str
