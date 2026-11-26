#!/usr/bin/env bash
# R14 host-side verification; intentionally no PS4 SDK, ELF or PKG.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash -n ci/r14/prepare-orbis-r14.sh
python3 -m py_compile ci/r14/patch-frontend.py ci/r14/build-branding.py \
  ci/generate-r11-branding.py
TARGET="$ROOT/.himura-r14/orbis-eden"
bash ci/r14/prepare-orbis-r14.sh "$TARGET"
# The ROM picker uses plain C++ and OS call declarations; check C++ syntax without PS4 SDK.
g++ -std=c++20 -fsyntax-only -I "$TARGET/frontend" "$TARGET/frontend/menu/rom_menu.cpp"

python3 - "$TARGET" <<'PY'
from pathlib import Path
import subprocess
import sys

base = Path(sys.argv[1])
menu = (base/"frontend/menu/rom_menu.cpp").read_text()
platform = (base/"frontend/ps4_platform.h").read_text()
package = (base/"package-eden.sh").read_text()
assert 'HIMURA SWITCH PS4 | R14' in menu
assert 'R14Background(c);' in menu
assert 'R14ReleaseBackground();' in menu
assert 'Ps4::Button::Left | Ps4::Button::Right' in menu
assert 'selected = (selected + (step % count) + count) % count;' in menu
assert 'int language = 1;' in menu
assert '/data/himura_switch_r14' in platform
assert 'TITLE_ID="HIMU00014"' in package
assert 'HIMURASWITCHR14X' in package
assert 's VERSION Utf8 8 "01.14"' in package
assert 'skin/himura-r14-menu.bgra' in package
image = base/"assets/himura-r14-menu.bgra"
assert image.stat().st_size == 1920*1080*4
with image.open('rb') as handle:
    handle.seek((1025*1920 + 600)*4)
    assert handle.read(4) == bytes([17,9,7,255]), "inert controller bar returned"
changed = set(subprocess.check_output(["git","-C",str(base),"diff","--name-only"],
                                      text=True).splitlines())
expected = {"frontend/menu/rom_menu.cpp", "frontend/ps4_platform.h", "package-eden.sh"}
assert changed == expected, f"unexpected upstream core changes: {changed ^ expected}"
patches = list((base/"patches/eden").glob("*.patch"))
assert len(patches) >= 40, f"expected PS4-specific upstream patch series, got {len(patches)}"
print(f"R14 PREFLIGHT OK: image, live buttons, packaging, {len(patches)} upstream PS4 patches")
print("Upstream CPU/JIT/Vulkan/memory source unchanged by HIMURA adaptation.")
print("NOT a PS4 compilation, PKG or gameplay validation.")
PY
