#!/usr/bin/env bash
# Light CircleCI check BEFORE starting the long Orbis-EDEN PS4 build.
set -Eeuo pipefail
python3 -m py_compile ci/himura-credits-r01.py
bash -n ci/himura-switch-build.sh
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SOURCE_COMMIT=f004df1c7a812cc65703d8f937d0bd12a6d06a58
git init -q "$WORK/orbis"
git -C "$WORK/orbis" remote add origin https://github.com/MrKitsune9/Orbis-EDEN.git
git -C "$WORK/orbis" fetch -q --depth=1 origin "$SOURCE_COMMIT"
git -C "$WORK/orbis" checkout -q --detach FETCH_HEAD
test "$(git -C "$WORK/orbis" rev-parse HEAD)" = "$SOURCE_COMMIT"
python3 ci/himura-credits-r01.py "$WORK/orbis"
bash -n "$WORK/orbis/ci/70-package.sh"
c++ -std=c++20 -fsyntax-only -I"$WORK/orbis/frontend" "$WORK/orbis/frontend/menu/rom_menu.cpp"
python3 - "$WORK/orbis" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
menu = (root / "frontend/menu/rom_menu.cpp").read_text()
pkg = (root / "ci/70-package.sh").read_text()
assert "bool creditsOpen = false" in menu
assert "if (creditsOpen)" in menu
assert "Ps4::Button::Square" in menu
assert "Ps4::Button::Circle | Ps4::Button::Cross" in menu
assert "CREDITOS E LICENCAS" in menu
assert "HIMURA SWITCH PS4" in menu
assert "licenses/HIMURA-CREDITS.txt" in pkg
assert (root / "licenses/HIMURA-CREDITS.txt").is_file()
assert (root / "LICENSE").is_file()
print("PASS: screen, controller, GNU GPL files and host syntax")
print("NOTE: game boot, real New Eden 04.89 and PS4 Pro remain untested")
PY
