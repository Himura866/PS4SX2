#!/usr/bin/env python3
"""Test original R13 art provenance and external-only output; no emulator/PKG changes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from PIL import Image

root=Path(__file__).resolve().parent.parent
path=root/'ci'/'prepare-neweden-v15-r13-art.py'
spec=importlib.util.spec_from_file_location('r13art',path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
assets=root/'assets'
with tempfile.TemporaryDirectory() as td:
    dest=Path(td)/'r13-approved'
    data=mod.prepare(assets,dest)
    icon=dest/'external-ps4'/'icon0.png'
    composite=dest/'reference-only'/'R13_ORIGINAL_COMPOSITE_NOT_WALLPAPER.webp'
    assert icon.is_file() and composite.is_file()
    with Image.open(icon) as im:
        assert im.size==(512,512) and im.format=='PNG'
    assert hashlib.sha256(composite.read_bytes()).hexdigest()==mod.MENU_SHA
    assert data['runtime_wallpaper_ready'] is False
    assert data['ps4_pkg_ready'] is False
    assert not (dest/'skin').exists()
    assert not (dest/'image0').exists()
    try:
        mod.prepare(assets,dest)
    except ValueError:
        pass
    else: raise AssertionError('Allowed output overwrite')
    changed=Path(td)/'changed'
    changed.mkdir()
    shutil.copyfile(assets/'r11-approved-menu.webp',changed/'r11-approved-menu.webp')
    shutil.copyfile(assets/'r11-approved-icon.webp',changed/'r11-approved-icon.webp')
    with (changed/'r11-approved-icon.webp').open('r+b') as fd:
        fd.seek(12); old=fd.read(1); fd.seek(12); fd.write(bytes([old[0]^1]))
    try:
        mod.prepare(changed,Path(td)/'rejected')
    except ValueError:
        pass
    else: raise AssertionError('Allowed changed R13 cover art')
print('PASS R13: genuine art hash, icon 512 PNG, no fake wallpaper, no overwrite, wrong art rejected')
