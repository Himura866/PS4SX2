#!/usr/bin/env python3
"""Convert R11 generated build to optional, version-pinned CI dependency reuse.

R11 keeps rebuilding its application and the final PKG. Only immutable upstream
PS4 toolchain/LLVM21/Mesa artifacts can be reused from a successful CI cache.
On a cache miss it performs the complete original, audited setup.
Never skips source/asset validation or the PS4 ELF/PKG packaging.
"""
from pathlib import Path
import sys

def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f"R11 cache {label}: expected one anchor, found {n}")
    return s.replace(old,new,1)

def main(p: Path):
    s=p.read_text(encoding="utf8")
    s=once(s,
        'stage 03_sdk_download python3 "$EDEN/tools/pacbrew/fetch-pacbrew.py"\n'
        'stage 04_sdk_install install_sdk\n'
        'stage 05_libcxx bash "$EDEN/runtime/toolchain/build-libcxx.sh"\n'
        'stage 06_runtime bash "$EDEN/runtime/toolchain/build-runtime.sh"',
        '''# R11_CACHE_V1: reusable pinned dependencies, not the emulator itself.
# CI cache is immutable and keyed on the pinned LLVM, Mesa, Eden4 and SDK.
# Detect partial/stale restores: if incomplete, rebuild the missing components.
if test -s "$OPENORBIS/ps4vars.sh" && test -x "$OPENORBIS/bin/linux/PkgTool.Core"; then
  echo "R11 cache: OpenOrbis SDK restored; skipping repeated download/install"
else
  stage 03_sdk_download python3 "$EDEN/tools/pacbrew/fetch-pacbrew.py"
  stage 04_sdk_install install_sdk
fi
if test -s "$PS4_BUILD_ROOT/sysroot/lib/libc++.a" &&
   test -s "$PS4_BUILD_ROOT/sysroot/lib/libc++abi.a"; then
  echo "R11 cache: compiled LLVM21 libc++ restored"
else
  stage 05_libcxx bash "$EDEN/runtime/toolchain/build-libcxx.sh"
fi
if test -s "$PS4_BUILD_ROOT/sysroot/lib/libdolphinps4_rt.a"; then
  echo "R11 cache: PS4 runtime restored"
else
  stage 06_runtime bash "$EDEN/runtime/toolchain/build-runtime.sh"
fi''',
        "SDK and compiler dependencies")

    s=once(s,
        'stage 07_mesa_source fetch_mesa\n'
        'stage 08_mesa_build bash "$EDEN/runtime/scripts/build-mesa.sh" setup',
        '''# R11_CACHE_V1: only skip Mesa when ALL pinned dependency outputs exist.
if test -s "$PS4_BUILD_ROOT/src/mesa-26.0.8.tar.xz" &&
   test -f "$PS4_BUILD_ROOT/src/mesa/meson.build" &&
   test -d "$PS4_BUILD_ROOT/src/libdrm"; then
  sha256sum "$PS4_BUILD_ROOT/src/mesa-26.0.8.tar.xz" > "$REPORT/mesa-sha256.txt"
  echo "R11 cache: pinned Mesa source restored"
else
  stage 07_mesa_source fetch_mesa
fi
if test -s "$PS4_BUILD_ROOT/build/mesa/src/amd/vulkan/libvulkan_radeon.a" &&
   test -s "$PS4_BUILD_ROOT/build/mesa/src/amd/addrlib/libaddrlib.a" &&
   test -s "$PS4_BUILD_ROOT/build/mesa/src/amd/common/libamd_common.a"; then
  echo "R11 cache: compiled Mesa/RADV restored"
else
  stage 08_mesa_build bash "$EDEN/runtime/scripts/build-mesa.sh" setup
fi''',
        "Mesa setup")

    # First CI phase prepares expensive dependencies and stores a reusable cache
    # BEFORE compiling the app, so an app compilation error does not throw it away.
    s=once(s,
        'stage 01_host check_host',
        '''if test "${R11_PKG_ONLY:-0}" = "1"; then
  echo "R11: package phase using prepared dependencies and patched checkout"
  test -s "$EDEN/eden/ps4/build.sh"
  test -s "$REPORT/eden4-source-commit.txt"
  test -s "$PS4_BUILD_ROOT/sysroot/lib/libc++.a"
  test -s "$PS4_BUILD_ROOT/build/mesa/src/amd/vulkan/libvulkan_radeon.a"
  stage 09_eden_pkg build_pkg
  STAGE="complete"
  exit 0
fi
stage 01_host check_host''',
        "package-only reuse of prepared checkout")
    s=once(s,
        'stage 09_eden_pkg build_pkg\\nSTAGE="complete"',
        '''if test "${R11_DEPS_ONLY:-0}" = "1"; then
  echo "R11: dependencies prepared; safe to save cache before app compilation"
  STAGE="dependencies_complete"
  exit 0
fi
stage 09_eden_pkg build_pkg
STAGE="complete"''',
        "cache checkpoint before app compilation")

    # With a cache miss we still compile all dependencies as before.
    for required in ("stage 09_eden_pkg build_pkg", "stage 06b_ps4_link_smoke", "stage 06c_ffmpeg_link_smoke"):
        if required not in s: raise RuntimeError("R11 cache: critical build stage missing: "+required)
    p.write_text(s,encoding="utf8")
    print("R11 cache recipe: reuse pinned compiler and Mesa only when complete; always rebuild application and PKG")

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r11-build-cache.py <generated R11 script>")
    main(Path(sys.argv[1]))
