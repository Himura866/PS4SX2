#!/usr/bin/env bash
# HIMURA SWITCH PS4 R14 - auditar a base Orbis Eden antes de qualquer novo PKG.
# Nao compila, nao instala nem gera PKG; usa apenas o codigo-fonte publico.
set -Eeuo pipefail

EXPECTED_ORBIS="f004df1c7a812cc65703d8f937d0bd12a6d06a58"
EXPECTED_EDEN="5f142c7926d0c7fcbbd0ce30794d72f638a43b2a"
build_script="ci/himura-switch-build.sh"

bash -n "$build_script"
grep -Fq "SOURCE_COMMIT=\"$EXPECTED_ORBIS\"" "$build_script" || {
  echo "FALHA: compilacao Orbis nao usa o commit auditado" >&2
  exit 2
}
if grep -Fq 'git clone --depth 1 --single-branch --branch main' "$build_script"; then
  echo "FALHA: checkout depende do HEAD movel" >&2
  exit 3
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
git init -q "$work/orbis-eden"
git -C "$work/orbis-eden" remote add origin https://github.com/MrKitsune9/Orbis-EDEN.git
git -C "$work/orbis-eden" fetch --depth 1 origin "$EXPECTED_ORBIS"
git -C "$work/orbis-eden" checkout --detach -q FETCH_HEAD
actual="$(git -C "$work/orbis-eden" rev-parse HEAD)"
test "$actual" = "$EXPECTED_ORBIS"

root="$work/orbis-eden"
grep -Fq "COMMIT=$EXPECTED_EDEN" "$root/scripts/fetch-eden.sh"
patch_count="$(find "$root/patches/eden" -maxdepth 1 -type f -name '*.patch' | wc -l | tr -d '[:space:]')"
test "$patch_count" = 46 || {
  echo "FALHA: Orbis nao contem 46 patches, encontrados $patch_count" >&2
  exit 4
}
for path in \
  "patches/eden/0003-PS4-64-MiB-JIT-caches-generic-dynarmic-exception-han.patch" \
  "patches/eden/0009-PS4-avoid-RADV-GFX7-GPU-hangs-from-indirect-count-dr.patch" \
  "patches/eden/0027-ORBIS-commit-lazy-guest-memory-from-the-top-2-GiB-of.patch" \
  "patches/eden/0031-PS4-built-in-Miis-when-database-is-empty.patch" \
  "frontend/libc_wide_fixes.cpp" "frontend/ps4_platform.cpp" \
  "tools/analyze-boot.py"; do
  test -s "$root/$path" || { echo "FALHA: componente ausente: $path" >&2; exit 5; }
done

echo "AUDITORIA R14 APROVADA"
echo "Orbis Eden commit: $actual"
echo "Eden base: $EXPECTED_EDEN"
echo "Patches PS4: $patch_count"
echo "JIT, GPU RADV, memoria, Mii, runtime e diagnostico: presentes"
echo "Nao foram compilados ELF/PKG, nem realizados testes de jogos no PS4 Pro."
