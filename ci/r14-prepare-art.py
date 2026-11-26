#!/usr/bin/env python3
"""Make the R14 native BGRA wallpaper directly from the approved R13 WebP.

The original file is verified by SHA-256. No resizing by distortion, no AI
redrawing. Bottom screenshot-only buttons are erased; actual controller hints
come from the C++ frontend and remain interactive.
"""
from pathlib import Path
import hashlib
import sys
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent.parent / "assets"
ICON_SHA = "ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778"
WALL_SHA = "b36c6a9eb5af0ee280c52845c91ca2f3a04b68e79d4f85b620bba9c25705b058"

def verify(path, expected):
    if not path.is_file():
        raise RuntimeError(f"Approved art file missing: {path}")
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != expected:
        raise RuntimeError(f"Approved art hash mismatch: {path}")
    return Image.open(path).convert("RGB")

def main(path):
    root = Path(path).resolve()
    out = root / "assets"
    out.mkdir(parents=True, exist_ok=True)
    image = verify(HERE / "r11-approved-menu.webp", WALL_SHA)
    if image.size[0] * 9 == image.size[1] * 16:
        image = image.resize((1920, 1080), Image.Resampling.LANCZOS)
    else:
        # Contain without stretching or silently cropping part of the samurai.
        contained = ImageOps.contain(image, (1920, 1080), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (1920, 1080), (7, 9, 17))
        canvas.paste(contained, ((1920 - contained.width) // 2,
                                (1080 - contained.height) // 2))
        image = canvas
    # Printed, non-interactive buttons in the lower strip of the R13 mockup.
    # This is the only intentionally blanked region of the approved wallpaper.
    d = ImageDraw.Draw(image)
    d.rectangle((0, 970, 1919, 1079), fill=(7, 9, 17))
    d.line((0, 969, 1919, 969), fill=(213, 34, 54), width=3)
    # Format matches sceVideoOut PixelFormatA8R8G8B8Srgb: uint32 AARRGGBB.
    raw = image.convert("RGBA").tobytes("raw", "BGRA")
    if len(raw) != 1920 * 1080 * 4:
        raise RuntimeError("R14 invalid BGRA dimensions")
    (out / "himura-r14-menu.bgra").write_bytes(raw)
    icon = verify(HERE / "r11-approved-icon.webp", ICON_SHA)
    ImageOps.fit(icon, (512, 512), Image.Resampling.LANCZOS).save(
        out / "icon0.png", optimize=True)
    print("R14 art: original verified samurai at 1920x1080, no distortion")
    print("R14 art: screenshot buttons erased; live PS4 menu renders controller help")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: r14-prepare-art.py <pinned Orbis Eden repo>")
    main(sys.argv[1])
