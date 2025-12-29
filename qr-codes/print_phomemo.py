#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys

import phomemo_m02s._image_helper
from phomemo_m02s.printer import Printer


def main() -> int:
    default_image = Path(__file__).resolve().parent / "qr_daily_note.png"

    parser = argparse.ArgumentParser(
        description="Print a QR PNG to a Phomemo M02S printer."
    )
    parser.add_argument("image", nargs="?", default=str(default_image))
    parser.add_argument("--width", type=int, default=Printer.MAX_WIDTH)
    parser.add_argument("--port", default="/dev/tty.M02S")
    parser.add_argument("--mac", default=None)
    parser.add_argument("--convert-only", action="store_true", default=False)

    args = parser.parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Image not found: {image_path}", file=sys.stderr)
        return 2

    if args.convert_only:
        phomemo_m02s._image_helper.preprocess_image(
            str(image_path), width=args.width, save=True
        )
        return 0

    printer = Printer(args.port, args.mac)
    printer.initialize()
    printer.reset()
    printer.align_center()
    printer.print_image(str(image_path), width=args.width)
    printer.reset()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
