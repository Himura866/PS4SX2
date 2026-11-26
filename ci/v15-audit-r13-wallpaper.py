#!/usr/bin/env python3
"""Audit the EXACT R13 menu reference before any V15 wallpaper work.

Read-only verification: this is a composite screenshot containing fake UI, NOT
a clean runtime background. Never claim that upscaling creates native 4K detail.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

APPROVED_SHA256 = "b36c6a9eb5af0ee280c52845c91ca2f3a04b68e79d4f85b620bba9c25705b058"


def inspect_reference(asset: Path, expected_sha256: str = APPROVED_SHA256) -> dict:
    if not asset.is_file() or asset.is_symlink():
        raise ValueError("R13 reference missing or symbolic link")
    h = hashlib.sha256()
    with asset.open("rb") as fd:
        for block in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(block)
    digest = h.hexdigest()
    if digest != expected_sha256:
        raise ValueError("R13 reference SHA-256 mismatch; no substitution allowed")
    with Image.open(asset) as original:
        original.verify()  # Check that the container can be decoded.
    with Image.open(asset) as original:
        w, h = original.size
        if original.format != "WEBP":
            raise ValueError("Expected the approved original R13 WebP")
        if w < 1280 or h < 720 or w * h > 50_000_000:
            raise ValueError("R13 native size outside permitted range")
        mode = original.mode
    return {
        "asset": "assets/r11-approved-menu.webp",
        "sha256": digest,
        "source_width": w,
        "source_height": h,
        "source_format": "WEBP",
        "source_color_mode": mode,
        "source_aspect_16_9": (w * 9 == h * 16),
        "source_native_1080p_or_higher": (w >= 1920 and h >= 1080),
        "source_native_4k_or_higher": (w >= 3840 and h >= 2160),
        "upscaling_can_restore_lost_detail": False,
        "contains_printed_fake_ui": True,
        "is_clean_runtime_wallpaper": False,
        "approved_edit_scope": "only the bottom fake buttons and black panel below game covers",
        "preserve_r13_composition": True,
        "no_black_mask_or_replacement_artwork": True,
        "ps4_runtime_tested": False,
        "status": "READ-ONLY R13 QUALITY AUDIT; NOT A V15 RUNTIME ASSET",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("refusing to overwrite a quality audit")
    report = inspect_reference(args.asset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
