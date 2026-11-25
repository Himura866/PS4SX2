#!/usr/bin/env bash
# R09 keeps the working R08 recipe but changes the ID and adds boot tracing.
set -Eeuo pipefail
src=ci/build-r08-eden4-pkg.sh
dst=ci/.r09-build-generated.sh
test -s "$src"
sed -e 's/switch-r08-reports/switch-r09-reports/g' \
    -e 's/switch-r08-pkgs/switch-r09-pkgs/g' \
    -e 's/\.himura-r08-build/.himura-r09-build/g' \
    -e 's/HIMU00008/HIMU00009/g' \
    -e 's/EDEN4_VERSION="01.00"/EDEN4_VERSION="01.09"/g' \
    -e 's/R08/R09/g' \
    -e 's/HIMURA SWITCH PS4-01.00-R09.pkg/HIMURA SWITCH PS4-01.09-R09.pkg/g' \
    -e '/python3 ci\/patch-eden4-credits.py "\$EDEN"/a\  python3 ci/patch-r09-boot-trace.py "$EDEN"' \
    "$src" > "$dst"
grep -q 'EDEN4_TITLE_ID="HIMU00009"' "$dst"
# Fail in seconds if the package recipe and declared version drift apart.
grep -Fq 'EDEN4_VERSION="01.09"' "$dst"
grep -Fq 'local pkg="$PS4_BUILD_ROOT/out/HIMURA SWITCH PS4-01.09-R09.pkg"' "$dst"
if grep -Fq 'HIMURA SWITCH PS4-01.00-R09.pkg' "$dst"; then
  echo 'R09: stale package filename detected before expensive compilation' >&2
  exit 9
fi
grep -q 'patch-r09-boot-trace.py' "$dst"
bash -n "$dst"
exec bash "$dst"
