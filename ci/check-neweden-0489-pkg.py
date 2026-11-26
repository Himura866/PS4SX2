#!/usr/bin/env python3
"""Read-only identification of the user's original New Eden 04.89 PS4 PKG."""
import hashlib
import struct
import sys
from pathlib import Path

SHA = "06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd"
CID = "IV0000-EDNP00001_00-EDENPS4000000000"


def check(pkg: Path) -> None:
    h = hashlib.sha256()
    size = pkg.stat().st_size
    with pkg.open("rb") as f:
        header = f.read(0x1000)
        assert header[:4] == b"\x7fCNT", "Not a PS4 PKG"
        content_id = header[0x40:0x64].split(b"\0", 1)[0].decode("ascii")
        count = struct.unpack_from(">I", header, 0x10)[0]
        off = struct.unpack_from(">I", header, 0x18)[0]
        assert count < 1024 and 0 <= off <= size - count * 32
        f.seek(off)
        table = f.read(count * 32)
        assert len(table) == count * 32
        for i in range(count):
            id, _, _, _, start, length, _, _ = struct.unpack_from(">8I", table, i * 32)
            assert start <= size and length <= size - start, f"entry {i} out of bounds"
        f.seek(0)
        while block := f.read(1048576):
            h.update(block)
    print("Content ID:", content_id)
    print("Bytes:", size)
    print("SHA-256:", h.hexdigest())
    print("Metadata entries:", count)
    print("Matches uploaded reference:", size == 69337088 and content_id == CID and h.hexdigest() == SHA)
    print("WARNING: this does not validate PS4 gameplay or extract ELF/PFS")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 ci/check-neweden-0489-pkg.py NEWEDEN.pkg")
    check(Path(sys.argv[1]))
