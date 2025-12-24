# app/core/qr_engine.py
import qrcode

def generate_qr(data: str, output_path: str):
    qr = qrcode.make(data)
    qr.save(output_path)
