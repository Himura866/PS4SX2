#!/usr/bin/env python3
"""Work around LLVM libc++ 18.1.8 random.cpp seeing host Linux headers.

In the PS4 cross-compile, __has_include(<linux/random.h>) is true because
Ubuntu supplies /usr/include/linux/random.h. The PS4 sysroot does not
provide its transitive <asm/types.h> dependency. Never select Linux's
RNDGETENTCNT ioctl path for the PS4 target; the libc++ random_device
implementation continues to use /dev/urandom.
This patch is target-specific and fails if LLVM upstream changes.
"""
from pathlib import Path
import sys

OLD = "#  if __has_include(<sys/ioctl.h>) && __has_include(<linux/random.h>)"
NEW = "#  if !defined(__ORBIS__) && __has_include(<sys/ioctl.h>) && __has_include(<linux/random.h>)"
LINUX_HEADER = "#    include <linux/random.h>"

def patch(file: Path) -> None:
    if file.name != "random.cpp" or file.parent.name != "src" or file.parent.parent.name != "libcxx":
        raise ValueError(f"Refusing to patch unexpected path: {file}")
    original = file.read_text(encoding="utf-8")
    if original.count(LINUX_HEADER) != 1:
        raise RuntimeError("Unexpected LLVM 18.1.8 Linux random header layout")
    if original.count(OLD) == 1 and NEW not in original:
        modified = original.replace(OLD, NEW, 1)
        file.write_text(modified, encoding="utf-8")
        print("HIMURA R14: disabled host Linux random ioctl includes for __ORBIS__")
    elif original.count(NEW) == 1 and OLD not in original:
        print("HIMURA R14: PS4 random header guard already patched")
    else:
        raise RuntimeError("LLVM random.cpp preprocessor anchor does not match audited LLVM 18.1.8")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: r14-fix-libcxx-random.py <LLVM-18.1.8/libcxx/src/random.cpp>")
    patch(Path(sys.argv[1]))
