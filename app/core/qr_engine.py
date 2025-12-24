import qrcode
from pathlib import Path

def generate_qr(data: str, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = qrcode.make(data)
    img.save(str(output_path))
