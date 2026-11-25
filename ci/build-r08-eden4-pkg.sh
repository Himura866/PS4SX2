#!/usr/bin/env bash
# HIMURA SWITCH PS4 R08: PS4 cross-build from pinned Eden4. No console testing.
set -Eeuo pipefail
BASE="$(pwd)"
EDEN="$BASE/.himura-bases/eden4"
REPORT="$BASE/switch-r08-reports"
PKGS="$BASE/switch-r08-pkgs"
export PS4_BUILD_ROOT="$BASE/.himura-r08-build"
export PSB="$PS4_BUILD_ROOT"
export OPENORBIS="/opt/pacbrew/ps4/openorbis"
export JOBS="${JOBS:-2}"
export EDEN4_TITLE_ID="HIMU00008"
export EDEN4_VERSION="01.00"
export EDEN_PKG_SUFFIX="-R08"
export EDEN_SFO_ATTRIBUTE="0"
STAGE="start"
mkdir -p "$REPORT" "$PKGS" "$PS4_BUILD_ROOT"

on_exit() {
  local code=$?
  set +e
  printf 'stage=%s\nexit_code=%s\n' "$STAGE" "$code" > "$REPORT/result.txt"
  if [ "$code" -ne 0 ]; then
    grep -inE 'fatal error:|error:|FAILED:|CMake Error|ninja:.*stop|Traceback|No such file' \
      "$REPORT/$STAGE.log" 2>/dev/null | tail -45 > "$REPORT/ERRO-PRINCIPAL.txt" || true
  fi
  du -sh "$PS4_BUILD_ROOT" > "$REPORT/build-size.txt" 2>/dev/null || true
}
trap on_exit EXIT

stage() {
  STAGE="$1"; shift
  printf '\n=== R08: %s ===\n' "$STAGE"
  "$@" 2>&1 | tee "$REPORT/$STAGE.log"
}

check_host() {
  test "$(uname -m)" = x86_64
  . /etc/os-release
  echo "Host: $PRETTY_NAME"
  test "$ID" = ubuntu && test "$VERSION_ID" = 26.04
  for t in clang-21 clang++-21 ld.lld-21 llvm-ar-21 llvm-ranlib-21 cmake ninja meson \
    glslangValidator python3 curl git patch zstd; do
    command -v "$t" || { echo "Host tool missing: $t"; return 4; }
  done
  clang-21 --version | head -1
  df -h . | tail -1
}

prepare_source() {
  bash ci/prepare-eden4-base.sh "$EDEN"
  git -C "$EDEN" rev-parse HEAD > "$REPORT/eden4-source-commit.txt"
  python3 ci/patch-eden4-credits.py "$EDEN"
  python3 - "$EDEN/eden/ps4/build.sh" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
assert s.count('NAME="Eden4"') == 1
p.write_text(s.replace('NAME="Eden4"', 'NAME="HIMURA SWITCH PS4"', 1))
PY
  git -C "$EDEN" diff --check
}

install_sdk() {
  python3 "$EDEN/tools/pacbrew/install-pacbrew.py"
  test -s "$OPENORBIS/ps4vars.sh"
  test -x "$OPENORBIS/bin/linux/PkgTool.Core"
  echo "PacBrew tools available"
}

fetch_mesa() {
  local root="$PS4_BUILD_ROOT/src" archive="$PS4_BUILD_ROOT/src/mesa-26.0.8.tar.xz"
  mkdir -p "$root"
  curl --fail --location --retry 3 --connect-timeout 30 \
    https://archive.mesa3d.org/mesa-26.0.8.tar.xz -o "$archive"
  tar -tJf "$archive" >/dev/null
  tar -xJf "$archive" -C "$root"
  mv "$root/mesa-26.0.8" "$root/mesa"
  patch -d "$root/mesa" -p1 < "$EDEN/runtime/patches/mesa-ps4.patch"
  git clone --depth 1 --branch libdrm-2.4.125 \
    https://gitlab.freedesktop.org/mesa/drm.git "$root/libdrm"
  sha256sum "$archive" > "$REPORT/mesa-sha256.txt"
  # Eden4's Mesa build script assumes Git HEAD but BUILDING.md uses a tarball.
  # Derive the build ID from the pinned Mesa source archive instead.
  python3 - "$EDEN/runtime/scripts/build-mesa.sh" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]); s = p.read_text()
old = 'build_id="$(git -C "$MESA" rev-parse HEAD)"'
new = 'build_id="$(sha256sum "$ROOT/src/mesa-26.0.8.tar.xz" | cut -c1-40)"'
assert s.count(old) == 1
p.write_text(s.replace(old, new))
PY
  git -C "$EDEN" diff --check
}

build_pkg() {
  bash "$EDEN/eden/ps4/build.sh"
  local obj="$PS4_BUILD_ROOT/build/eden/src/yuzu_ps4/eden-ps4_eboot"
  local pkg="$PS4_BUILD_ROOT/out/HIMURA SWITCH PS4-01.00-R08.pkg"
  test -s "$obj/eden-ps4.oelf" || { echo "Missing PS4 ELF"; return 7; }
  test -s "$obj/eboot.bin" || { echo "Missing PS4 eboot.bin"; return 8; }
  test -s "$pkg" || { echo "Missing PKG $pkg"; return 9; }
  cp "$pkg" "$PKGS/HIMURA_SWITCH_PS4_R08_EXPERIMENTAL.pkg"
  cp "$obj/eden-ps4.oelf" "$PKGS/HIMURA_SWITCH_PS4_R08.oelf"
  sha256sum "$PKGS"/* > "$REPORT/output-sha256.txt"
  ls -lh "$PKGS" > "$REPORT/output-list.txt"
}

stage 01_host check_host
stage 02_source prepare_source
stage 03_sdk_download python3 "$EDEN/tools/pacbrew/fetch-pacbrew.py"
stage 04_sdk_install install_sdk
stage 05_libcxx bash "$EDEN/runtime/toolchain/build-libcxx.sh"
stage 06_runtime bash "$EDEN/runtime/toolchain/build-runtime.sh"
stage 07_mesa_source fetch_mesa
stage 08_mesa_build bash "$EDEN/runtime/scripts/build-mesa.sh" setup
stage 09_eden_pkg build_pkg
STAGE="complete"
echo "R08 ELF/PKG was generated, but PS4 boot and games remain untested."
