#!/usr/bin/env bash
# HIMURA SWITCH PS4 R10: isolated Switch-style top toolbar; CircleCI only.
# Build from the exact R08 recipe with R10-specific UI and boot diagnostics.
set -Eeuo pipefail
src=ci/build-r08-eden4-pkg.sh
dst=ci/.r10-build-generated.sh
test -s "$src"
python3 - "$src" "$dst" <<'PY'
from pathlib import Path
import sys
source = Path(sys.argv[1]).read_text(encoding="utf-8")
def once(old, new):
    global source
    assert source.count(old) == 1, f"R10 recipe mismatch: {old}"
    source = source.replace(old, new, 1)
once('switch-r08-reports', 'switch-r10-reports')
once('switch-r08-pkgs', 'switch-r10-pkgs')
once('.himura-r08-build', '.himura-r10-build')
once('HIMU00008', 'HIMU00010')
once('EDEN4_VERSION="01.00"', 'EDEN4_VERSION="01.10"')
source = source.replace('R08', 'R10')
once('HIMURA SWITCH PS4-01.00-R10.pkg', 'HIMURA SWITCH PS4-01.10-R10.pkg')
once('  python3 ci/patch-eden4-credits.py "$EDEN"\n',
     '  python3 ci/patch-eden4-credits.py "$EDEN"\n'
     '  python3 ci/patch-r10-switch-toolbar.py "$EDEN"\n'
     '  python3 ci/patch-r10-boot-trace.py "$EDEN"\n')
Path(sys.argv[2]).write_text(source, encoding="utf-8")
PY
grep -Fq 'EDEN4_TITLE_ID="HIMU00010"' "$dst"
grep -Fq 'EDEN4_VERSION="01.10"' "$dst"
grep -Fq 'local pkg="$PS4_BUILD_ROOT/out/HIMURA SWITCH PS4-01.10-R10.pkg"' "$dst"
grep -Fq 'python3 ci/patch-r10-switch-toolbar.py "$EDEN"' "$dst"
grep -Fq 'python3 ci/patch-r10-boot-trace.py "$EDEN"' "$dst"
if grep -Fq 'HIMURA SWITCH PS4-01.00-R10.pkg' "$dst"; then
  echo 'R10: stale package path detected before compilation' >&2
  exit 9
fi
bash -n "$dst"
exec bash "$dst"
