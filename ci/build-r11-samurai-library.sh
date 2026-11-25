#!/usr/bin/env bash
# HIMURA SWITCH PS4 R11 - isolated samurai-themed playable launcher.
# Reuses R08 packaging and R10 navigation/diagnostics without changing those branches.
set -Eeuo pipefail
src=ci/build-r08-eden4-pkg.sh
dst=ci/.r11-build-generated.sh
test -s "$src"
python3 - "$src" "$dst" <<'PY'
from pathlib import Path
import sys
source = Path(sys.argv[1]).read_text(encoding="utf-8")
def once(old, new):
    global source
    assert source.count(old) == 1, f"R11 recipe mismatch: {old}"
    source = source.replace(old, new, 1)
once('switch-r08-reports', 'switch-r11-reports')
once('switch-r08-pkgs', 'switch-r11-pkgs')
once('.himura-r08-build', '.himura-r11-build')
once('HIMU00008', 'HIMU00011')
once('EDEN4_VERSION="01.00"', 'EDEN4_VERSION="01.11"')
source = source.replace('R08', 'R11')
once('HIMURA SWITCH PS4-01.00-R11.pkg', 'HIMURA SWITCH PS4-01.11-R11.pkg')
once('  python3 ci/patch-eden4-credits.py "$EDEN"\n',
     '  python3 ci/patch-eden4-credits.py "$EDEN"\n'
     '  python3 ci/patch-r10-switch-toolbar.py "$EDEN"\n'
     '  python3 ci/patch-r11-samurai-library.py "$EDEN"\n'
     '  python3 ci/patch-r11-theme-cache.py "$EDEN"\n'
     '  python3 ci/patch-r11-autocovers.py "$EDEN"\n'
     '  python3 ci/patch-r11-fps.py "$EDEN"\n'
     '  python3 ci/generate-r11-branding.py "$EDEN"\n'
     '  python3 ci/patch-r11-authorship.py "$EDEN"\n'
     '  python3 ci/patch-r10-boot-trace.py "$EDEN"\n'
     '  python3 ci/patch-r11-stability.py "$EDEN"\n')
Path(sys.argv[2]).write_text(source, encoding="utf-8")
PY
grep -Fq 'EDEN4_TITLE_ID="HIMU00011"' "$dst"
grep -Fq 'EDEN4_VERSION="01.11"' "$dst"
grep -Fq 'local pkg="$PS4_BUILD_ROOT/out/HIMURA SWITCH PS4-01.11-R11.pkg"' "$dst"
grep -Fq 'python3 ci/patch-r11-samurai-library.py "$EDEN"' "$dst"
grep -Fq 'python3 ci/patch-r10-switch-toolbar.py "$EDEN"' "$dst"
if grep -Fq 'HIMURA SWITCH PS4-01.00-R11.pkg' "$dst"; then
  echo "R11: stale package path detected before compilation" >&2
  exit 9
fi
bash -n "$dst"
exec bash "$dst"
