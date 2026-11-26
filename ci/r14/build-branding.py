#!/usr/bin/env python3
"""Package the owner's CHECKSUM-VERIFIED R13 art as R14 raw BGRA (no fake button footer).
No source images are replaced. Requires Pillow on the CI host only.
"""
from pathlib import Path
import hashlib
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

def build(destination: Path):
    # Existing R13 generator checks both approved WebPs by SHA-256 and removes
    # the six inert bottom-of-picture controller hints.
    subprocess.run([sys.executable, str(ROOT / "ci/generate-r11-branding.py"),
                    str(destination)], check=True)
    branding = destination / "branding"
    png = branding / "himura-r11-menu.png"
    with Image.open(png) as image:
        rgb = image.convert("RGB")
        if rgb.size != (1920, 1080):
            raise RuntimeError(f"wrong approved background size: {rgb.size}")
        for point in ((30, 1000), (200, 1025), (600, 1035),
                      (1550, 1025), (1850, 1050)):
            if rgb.getpixel(point) != (7, 9, 17):
                raise RuntimeError(f"fake button strip not erased at {point}")
        rgba = rgb.convert("RGBA")
        raw = rgba.tobytes("raw", "BGRA")
    if len(raw) != 1920 * 1080 * 4:
        raise RuntimeError("wrong BGRA buffer size")
    assets = destination / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    skin = assets / "himura-r14-menu.bgra"
    skin.write_bytes(raw)
    icon = branding / "icon0.png"
    (assets / "icon0.png").write_bytes(icon.read_bytes())
    print(f"R14: approved samurai backdrop {len(raw)} bytes, SHA256 {hashlib.sha256(raw).hexdigest()}")
    print("R14: original approved icon copied, no fake printed footer controls")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build-branding.py <orbis-eden-checkout>")
    build(Path(sys.argv[1]).resolve())
