#!/usr/bin/env python3
"""R08 FFmpeg linker shim: remove the duplicate PacBrew linker script.

FFmpeg configure assembles PS4 CMake's -Wl,--script=<OPENORBIS>/link.x
and then invokes Eden4's ps4-cc, which itself adds
<EDEN>/runtime/toolchain/ps4-link.x. Two scripts cause lld's RELRO
section contiguity failure. Only FFmpeg's *link* command is changed.
"""
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-r08-ffmpeg-linker-shim.py <Eden4 checkout>")
    repo = Path(sys.argv[1]).resolve()
    cmake = repo / "eden/externals/ffmpeg/CMakeLists.txt"
    wrapper = repo / "runtime/toolchain/bin/ps4-ffmpeg-ld"
    original = cmake.read_text(encoding="utf-8")
    old = '        set(FFmpeg_LD "${FFmpeg_CC}")'
    new = '        set(FFmpeg_LD "${DOLPHIN_PS4_ROOT}/toolchain/bin/ps4-ffmpeg-ld")'
    if original.count(old) != 1:
        raise RuntimeError("Cannot uniquely locate FFmpeg_LD in pinned Eden4 source")
    if wrapper.exists():
        raise RuntimeError(f"Refusing to overwrite existing wrapper: {wrapper}")
    content = """#!/usr/bin/env bash
# FFmpeg-only linker shim: ps4-cc already supplies its own PS4 link script.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OPENORBIS="${OPENORBIS:-/opt/pacbrew/ps4/openorbis}"
args=()
removed=0
for arg in "$@"; do
  case "$arg" in
    "-Wl,--script=$OPENORBIS/link.x"|"-Wl,--script,$OPENORBIS/link.x")
      removed=$((removed + 1))
      continue
      ;;
  esac
  args+=("$arg")
done
exec "$HERE/ps4-cc" "${args[@]}"
"""
    cmake.write_text(original.replace(old, new, 1), encoding="utf-8")
    wrapper.write_text(content, encoding="utf-8")
    wrapper.chmod(0o755)
    print("HIMURA R08: FFmpeg-only LD shim installed; duplicate OpenOrbis link.x dropped")

if __name__ == "__main__":
    main()
