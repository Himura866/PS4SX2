#!/usr/bin/env python3
"""Regression: the parallel V15 external PS4 tile uses the exact approved R13 art."""
import hashlib
import importlib.util
import tempfile
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("v15builder", root/"ci"/"build-neweden-v15-pkg.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
approved = root/"assets"/"r11-approved-icon.webp"
expected = "ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778"
assert hashlib.sha256(approved.read_bytes()).hexdigest() == expected

with tempfile.TemporaryDirectory(prefix="v15-r13-icon-") as d:
    stage = Path(d)/"Image0"
    (stage/"sce_sys").mkdir(parents=True)
    icon_hash = mod.install_approved_r13_icon(stage, approved)
    produced = stage/"sce_sys"/"icon0.png"
    assert icon_hash == hashlib.sha256(produced.read_bytes()).hexdigest()
    with Image.open(produced) as img:
        assert img.size == (512, 512) and img.format == "PNG"

    tampered = Path(d)/"tampered.webp"
    altered = bytearray(approved.read_bytes())
    altered[len(altered)//2] ^= 1
    tampered.write_bytes(altered)
    try:
        mod.install_approved_r13_icon(stage, tampered)
    except ValueError as e:
        assert "hash mismatch" in str(e)
    else:
        raise AssertionError("Altered external Samurai art was accepted")
print("PASS: approved R13 Samurai icon converted to PS4 PNG; altered input rejected")
