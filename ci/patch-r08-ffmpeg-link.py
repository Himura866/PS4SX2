#!/usr/bin/env python3
"""HIMURA SWITCH R08: prevent PS4 FFmpeg cross-linker flag conflicts.

The PS4 wrapper ps4-cc supplies OpenOrbis's custom linker script and CRT
itself. Passing CMake's global C link flags again via FFmpeg --extra-ldflags
inserts a second PS4 linker script and trips lld's RELRO section ordering.
Patch only the disposable, pinned Eden4 checkout used by CircleCI.
"""
from pathlib import Path
import sys

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-r08-ffmpeg-link.py <Eden4 checkout>")
    root = Path(sys.argv[1]).resolve()
    cmake = root / "eden/externals/ffmpeg/CMakeLists.txt"
    if not cmake.is_file():
        raise SystemExit(f"missing FFmpeg CMake module: {cmake}")
    original = cmake.read_text(encoding="utf-8")
    anchor = '''        set(FFmpeg_LD "${FFmpeg_CC}")
    endif()
    add_custom_command('''
    replacement = '''        set(FFmpeg_LD "${FFmpeg_CC}")
    endif()
    # HIMURA R08: ps4-cc provides its own PS4 linker script and runtime libs.
    # Passing CMAKE_C_LINK_FLAGS adds a second OpenOrbis linker script and
    # results in lld's ".eh_frame is not contiguous with other relro sections".
    set(FFmpeg_EXTRA_LDFLAGS "${CMAKE_C_LINK_FLAGS}")
    if(PS4)
        set(FFmpeg_EXTRA_LDFLAGS "")
    endif()
    add_custom_command('''
    if original.count(anchor) != 1:
        raise RuntimeError("FFmpeg linker preflight anchor mismatch")
    old_flags = '                --extra-ldflags=${CMAKE_C_LINK_FLAGS}'
    new_flags = '                --extra-ldflags=${FFmpeg_EXTRA_LDFLAGS}'
    if original.count(old_flags) != 1:
        raise RuntimeError("FFmpeg CMake linker flags are not as expected")
    patched = original.replace(anchor, replacement, 1).replace(old_flags, new_flags, 1)
    if patched == original:
        raise RuntimeError("FFmpeg patch made no changes")
    cmake.write_text(patched, encoding="utf-8")
    print("HIMURA R08: FFmpeg PS4 link flags isolated; PS4 wrapper retains sole linker script")

if __name__ == "__main__":
    main()
