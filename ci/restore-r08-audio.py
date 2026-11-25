#!/usr/bin/env python3
"""R08: restore 4 audio_core/out files absent from the pinned Eden4 snapshot.

Provenance: a pinned public Eden-NS2 mirror; verify Git blob SHA-1 and four
already-present neighboring files before copying. This runs ONLY inside the
disposable .himura-bases/eden4 checkout used by CircleCI.
No binary blobs, firmware, console keys or Sony modules are fetched.
"""
from __future__ import annotations

import hashlib
import sys
import time
import urllib.request
from pathlib import Path

MIRROR = "0x2593/Eden-NS2"
REVISION = "b2cef0c0f2e8517673233e22c929918e2c60e654"
# Each expected digest is Git's SHA-1 of "blob <length>\0<bytes>", not a
# checksum of the HTML returned by a GitHub web page.
MATCHING_NEIGHBORS = {
    "audio_out_manager.cpp": "569df8d1e0aa971b5603e6010815cced1f66265a",
    "audio_out_manager.h": "c3e445d5d3c736f7abadeaed8da7d96bb736e2f4",
    "in/audio_in.cpp": "df8c44d1f2755de4211fb3fb556d61215bfe9136",
    "in/audio_in.h": "092ab7236980751279797497b59c6a40d3938e03",
}
MISSING = {
    "out/audio_out.cpp": "b7ea134055b91c058de92cccddec731c00ed47d0",
    "out/audio_out.h": "946f345c6196a2eb0f8e67f920dc7aca211da6c1",
    "out/audio_out_system.cpp": "46f30f19c6528e16be2058c6e3c0150ca8013c83",
    "out/audio_out_system.h": "82aada1855740ffdd9f1244241e4527000df5959",
}


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify(path: Path, expected: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"compatibility file missing: {path}")
    found = git_blob_id(path.read_bytes())
    if found != expected:
        raise RuntimeError(f"compatibility mismatch for {path}: {found} != {expected}")


def download(name: str, expected: str) -> bytes:
    url = (
        "https://raw.githubusercontent.com/"
        f"{MIRROR}/{REVISION}/src/audio_core/{name}"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                content = response.read()
            observed = git_blob_id(content)
            if observed != expected:
                raise RuntimeError(f"unexpected Git blob: {name}: {observed}")
            return content
        except (OSError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError(f"could not fetch {url}: {exc}") from exc
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: restore-r08-audio.py <pinned Eden4 checkout>")
    root = Path(sys.argv[1]).resolve()
    audio = root / "eden/src/audio_core"
    cmake = audio / "CMakeLists.txt"
    if not cmake.is_file():
        raise RuntimeError(f"audio source not found: {cmake}")
    original_cmake = cmake.read_text(encoding="utf-8")
    # Prevent importing code into a different version just because filenames match.
    for name, blob in MATCHING_NEIGHBORS.items():
        verify(audio / name, blob)
    for name in MISSING:
        if original_cmake.count(name) != 1:
            raise RuntimeError(f"CMakeLists does not list exactly one {name}")
    # Check all network sources and checksums before changing any local files.
    saved: dict[str, bytes] = {}
    for name, expected in MISSING.items():
        dst = audio / name
        if dst.exists():
            verify(dst, expected)
            print(f"R08 audio already present and checked: {name}", flush=True)
        else:
            saved[name] = download(name, expected)
            print(f"R08 verified missing audio: {name}", flush=True)
    for name, content in saved.items():
        path = audio / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(content)
        verify(path, MISSING[name])
    # Track provenance inside the copy whose licenses get packaged by Eden4.
    note = (
        "\n\nHIMURA SWITCH PS4 R08 — source restoration: "
        "four audio_core/out source files from "
        f"https://github.com/{MIRROR}/tree/{REVISION}/src/audio_core/out "
        "(Eden/yuzu contributors; original SPDX notices retained). "
        "Files are verified against pinned Git blob IDs. "
        "The original Eden4 snapshot and its license notices remain preserved.\n"
    )
    credits = root / "CREDITS.md"
    existing = credits.read_text(encoding="utf-8")
    if "HIMURA SWITCH PS4 R08 — source restoration:" not in existing:
        credits.write_text(existing + note, encoding="utf-8")
    print("R08: missing audio files restored with pinned integrity checks", flush=True)


if __name__ == "__main__":
    main()
