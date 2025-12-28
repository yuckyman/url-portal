# QR Code Generator

Simple script to generate QR codes for portal URLs.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Or:

```bash
pip install qrcode[pil]
```

## Usage

Generate a QR code for the daily note portal:

```bash
python generate_qr.py
```

This creates `qr_daily_note.png` in this directory.

## Customization

Edit `generate_qr.py` to change:
- `PORTAL_URL`: The portal URL to encode
- `OUTPUT_FILE`: Where to save the QR code image
- QR code appearance (size, error correction, colors)

## Future: QR Code Generator

This is a simple test script. A full QR code generator would:
- Accept portal IDs as arguments
- Generate QR codes for multiple portals
- Support custom styling/branding
- Output in multiple formats (PNG, SVG, PDF)
- Batch generation from portals.json

