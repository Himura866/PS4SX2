#!/usr/bin/env bash
# HIMURA SWITCH PS4 R14 - pinned Orbis Eden source and live HIMURA UI.
# Does not compile, create a PKG or modify any R13 branch.
set -Eeuo pipefail
ROOT="$(git rev-parse --show-toplevel)"
DEST="$ROOT/.himura-r14/orbis-eden"
if [ "$#" -gt 0 ]; then DEST="$1"; fi
SOURCE="https://github.com/MrKitsune9/Orbis-EDEN.git"
PIN="f004df1c7a812cc65703d8f937d0bd12a6d06a58"

if [ -e "$DEST" ]; then
  echo "R14: refusing to overwrite existing source: $DEST" >&2
  exit 2
fi
mkdir -p "$(dirname "$DEST")"
git clone --filter=blob:none --no-checkout "$SOURCE" "$DEST"
git -C "$DEST" checkout --detach "$PIN"
actual="$(git -C "$DEST" rev-parse HEAD)"
test "$actual" = "$PIN" || { echo 'R14: upstream pin mismatch' >&2; exit 3; }
for f in frontend/main.cpp frontend/menu/rom_menu.cpp frontend/ps4_platform.h \
         scripts/fetch-eden.sh configure-eden.sh package-eden.sh docs/STATUS.md; do
  test -s "$DEST/$f" || { echo "R14: missing upstream source: $f" >&2; exit 4; }
done

python3 "$ROOT/ci/r14/patch-frontend.py" "$DEST"
python3 "$ROOT/ci/r14/build-branding.py" "$DEST"
git -C "$DEST" diff --check
test -s "$DEST/assets/himura-r14-menu.bgra"
test "$(wc -c < "$DEST/assets/himura-r14-menu.bgra")" -eq 8294400

mkdir -p "$ROOT/.himura-r14"
{
  echo "HIMURA SWITCH PS4 R14 MIGRATION SOURCE"
  echo "base=MrKitsune9/Orbis-EDEN"
  echo "base_commit=$PIN"
  echo "guest=Eden 5f142c7926d0c7fcbbd0ce30794d72f638a43b2a + Orbis PS4 patches"
  echo "frontend=HIMURA R14 live menu and validated samurai backdrop"
  echo "package_title_id=HIMU00014"
  echo "console_status=NOT TESTED"
  echo "build_status=NOT BUILT"
} > "$ROOT/.himura-r14/source-manifest.txt"
echo "R14: source and artwork prepared at $DEST"
echo "R14: no PKG generated and no game compatibility claim"
