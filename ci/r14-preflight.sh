#!/usr/bin/env bash
# R14 native menu preflight; NO SDK, no PKG and no PS4 executable build.
set -Eeuo pipefail
bash -n ci/himura-switch-build.sh
python3 -m py_compile ci/r14-adapt-orbis.py ci/r14-prepare-art.py ci/r14-enable-update-manager.py
ROOT="$(pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SOURCE_COMMIT="f004df1c7a812cc65703d8f937d0bd12a6d06a58"
git init -q "$WORK/orbis"
git -C "$WORK/orbis" remote add origin https://github.com/MrKitsune9/Orbis-EDEN.git
git -C "$WORK/orbis" fetch -q --depth=1 origin "$SOURCE_COMMIT"
git -C "$WORK/orbis" checkout -q --detach FETCH_HEAD
test "$(git -C "$WORK/orbis" rev-parse HEAD)" = "$SOURCE_COMMIT"
printf 'R14 upstream locked to %s\n' "$SOURCE_COMMIT"
test "$(find "$WORK/orbis/patches/eden" -maxdepth 1 -name '*.patch' | wc -l | tr -d ' ')" = 46
python3 ci/r14-adapt-orbis.py "$WORK/orbis"
python3 ci/r14-prepare-art.py "$WORK/orbis"
python3 ci/r14-enable-update-manager.py "$WORK/orbis"
bash -n "$WORK/orbis/ci/70-package.sh"
# Compile C++ frontend as a host syntax smoke test, before an expensive PS4 cross-build.
c++ -std=c++20 -fsyntax-only -I"$WORK/orbis/frontend" "$WORK/orbis/frontend/menu/r14_update_manager.cpp"
c++ -std=c++20 -fsyntax-only -I"$WORK/orbis/frontend" "$WORK/orbis/frontend/menu/rom_menu.cpp"
python3 - "$WORK/orbis" <<'PY'
from pathlib import Path
from PIL import Image
import hashlib
import sys
root = Path(sys.argv[1])
menu = (root / "frontend/menu/rom_menu.cpp").read_text()
settings = (root / "frontend/ps4_platform.h").read_text()
pkg = (root / "ci/70-package.sh").read_text()
assert 'HIMURA SWITCH PS4' in pkg and 'HIMU00014' in pkg
assert '"01.14"' in pkg
assert '/data/himura-switch-r14' in settings
assert '/app0/assets/himura/r14-menu.bgra' in menu
assert 'Draw(canvas, names, selected, wallpaper.empty() ? nullptr : wallpaper.data(),' in menu
assert 'Himura::Updates::Discover()' in menu
assert 'importer.Tick()' in menu
assert 'if (pressed & Ps4::Button::Square)' in menu
assert 'Ps4::Button::Circle' in menu
updater = (root / 'frontend/menu/r14_update_manager.cpp').read_text()
assert 'NSP invalido' in updater and '"PFS0"' in updater
assert 'fs::rename(tmp_, destination_' in updater
assert 'fs::remove(tmp_, ec)' in updater
cmake = (root / 'frontend/frontend.cmake').read_text()
assert 'r14_update_manager.cpp' in cmake
assert 'external_content_dirs' in (root / 'frontend/main.cpp').read_text()
assert 'if (pressed & Ps4::Button::Cross)' in menu
assert 'pressed & Ps4::Button::Triangle' in menu
assert 'int language = 1;' in menu
bgra = root / 'assets/himura-r14-menu.bgra'
assert bgra.stat().st_size == 1920 * 1080 * 4
# BGRA at bottom is solid opaque dark: no static printed controller hints.
b = bgra.read_bytes()
expected = bytes((17, 9, 7, 255))
for x,y in ((25,1010),(200,1040),(600,1005),(1550,1030),(1800,1070)):
    off = (y * 1920 + x) * 4
    assert b[off:off+4] == expected, f"fake footer found at {x,y}"
icon = root / 'assets/icon0.png'
with Image.open(icon) as im:
    assert im.size == (512,512)
print("R14 PREFLIGHT PASSED: 46 patches, authentic art without fake buttons, real update/DLC importer, native pad, isolated saves and package")
print("NO CLAIM OF GAME COMPATIBILITY: ELF/PKG and PS4 Pro gameplay still require separate testing.")
PY
