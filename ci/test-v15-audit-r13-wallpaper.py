#!/usr/bin/env python3
"""Offline tests for the R13 quality audit. No private PKG or emulator data."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile

from PIL import Image

source = Path(__file__).with_name("v15-audit-r13-wallpaper.py")
spec = importlib.util.spec_from_file_location("v15_wallpaper", source)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

with tempfile.TemporaryDirectory(prefix="v15-r13-quality-") as tmp:
    root = Path(tmp)
    image = root / "test.webp"
    Image.new("RGB", (1280, 720), (46, 35, 40)).save(image, "WEBP", lossless=True)
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    report = audit.inspect_reference(image, digest)
    assert report["source_width"] == 1280 and report["source_height"] == 720
    assert report["source_aspect_16_9"]
    assert report["source_native_1080p_or_higher"] is False
    assert report["source_native_4k_or_higher"] is False
    assert report["is_clean_runtime_wallpaper"] is False
    assert report["contains_printed_fake_ui"] is True
    print("PASS: source dimensions and honesty flags validated")

    try:
        audit.inspect_reference(image, "0" * 64)
    except ValueError as exc:
        assert "SHA-256 mismatch" in str(exc)
    else:
        raise AssertionError("Source substitution accepted")
    print("PASS: R13 source substitution refused")

    missing = root / "not-present.webp"
    try:
        audit.inspect_reference(missing, digest)
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Missing reference accepted")
    print("PASS: missing source refused")

    invalid = root / "invalid.webp"
    invalid.write_bytes(b"not-a-valid-webp-file")
    invalid_digest = hashlib.sha256(invalid.read_bytes()).hexdigest()
    try:
        audit.inspect_reference(invalid, invalid_digest)
    except (OSError, ValueError):
        pass
    else:
        raise AssertionError("Invalid image accepted")
    print("PASS: invalid WebP refused")

print("PASS: R13 quality audit tests passed; no artwork or PKG modified")
