#!/usr/bin/env python3
"""
Generate QR code for a portal URL.
"""

import qrcode
from pathlib import Path

# Portal URL for daily note
# Using direct Tailscale IP (temporary until DNS is configured)
PORTAL_URL = "https://yuckbox.spillyourguts.online/wm/p/dle"
OUTPUT_FILE = Path(__file__).parent / "qr_daily_note.png"

def generate_qr_code(url: str, output_path: Path):
    """
    Generate a QR code for the given URL.
    
    Args:
        url: The URL to encode in the QR code
        output_path: Path to save the QR code image
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save
    img.save(output_path)
    print(f"✓ QR code generated: {output_path}")
    print(f"  URL: {url}")

if __name__ == "__main__":
    generate_qr_code(PORTAL_URL, OUTPUT_FILE)

