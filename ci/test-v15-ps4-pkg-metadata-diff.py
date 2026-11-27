#!/usr/bin/env python3
"""Pure synthetic tests: no user PKG, firmware, keys or game files."""
import importlib.util
from pathlib import Path
import struct
import tempfile

spec = importlib.util.spec_from_file_location("v15_pkg_metadata", Path(__file__).with_name("v15-ps4-pkg-metadata-diff.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def make_sfo():
    entries = [("APP_TYPE", 0x0404, (1).to_bytes(4, "little")),
               ("ATTRIBUTE", 0x0404, (0x10002).to_bytes(4, "little")),
               ("CATEGORY", 0x0204, b"gd\x00"),
               ("APP_VER", 0x0204, b"04.89\x00"),
               ("TITLE_ID", 0x0204, b"EDNP00001\x00")]
    key_table = bytearray()
    value_table = bytearray()
    indexes = bytearray()
    for key, typ, value in entries:
        keyoff = len(key_table)
        valueoff = len(value_table)
        key_table.extend(key.encode("utf-8") + b"\x00")
        value_table.extend(value)
        indexes.extend(struct.pack("<HHIII", keyoff, typ, len(value), max(len(value), 4), valueoff))
    keys_at = 20 + len(indexes)
    data_at = keys_at + len(key_table)
    return struct.pack("<4sIIII", b"\x00PSF", 0x101, keys_at, data_at, len(entries)) + indexes + key_table + value_table


def make_pkg(path):
    sfo = make_sfo()
    blob = bytearray(0x6000)
    blob[:4] = b"\x7fCNT"
    struct.pack_into(">I", blob, 0x10, 2)
    struct.pack_into(">I", blob, 0x18, 0x800)
    blob[0x40:0x70] = mod.CONTENT_ID.encode().ljust(0x30, b"\x00")
    struct.pack_into(">I", blob, 0x70, 15)
    struct.pack_into(">I", blob, 0x74, 0x1A)
    struct.pack_into(">I", blob, 0x78, 0x0A000000)
    struct.pack_into(">IIIIIIII", blob, 0x800, 0x1000, 0, 0, 0, 0x2000, len(sfo), 0, 0)
    struct.pack_into(">IIIIIIII", blob, 0x820, 0x1200, 0, 0, 0, 0x3000, 16, 0, 0)
    blob[0x2000:0x2000+len(sfo)] = sfo
    blob[0x3000:0x3010] = b"\x89PNG\r\n\x1a\n" + bytes(8)
    path.write_bytes(blob)


with tempfile.TemporaryDirectory() as directory:
    pkg = Path(directory) / "fake-synthetic.pkg"
    make_pkg(pkg)
    report = mod.read_package(pkg)
    assert report["header"]["drm_type"] == 15
    assert report["header"]["content_type"] == 0x1A
    assert report["header"]["content_flags"] == 0x0A000000
    assert report["header"]["content_id"] == mod.CONTENT_ID
    assert report["sfo"]["APP_TYPE"] == 1
    assert report["sfo"]["ATTRIBUTE"] == 0x10002
    assert report["sfo"]["CATEGORY"] == "gd"
    assert report["sfo"]["APP_VER"] == "04.89"
    assert report["sfo"]["TITLE_ID"] == "EDNP00001"
    assert len(report["sfo_sha256"]) == 64
    assert len(report["icon_sha256"]) == 64
    print("PASS: PS4 CNT header, metadata table, embedded SFO integers/strings and icon")

    data = bytearray(pkg.read_bytes())
    # Make the metadata table location point past the end of the file.
    struct.pack_into(">I", data, 0x18, 0x7000)
    pkg.write_bytes(data)
    try:
        mod.read_package(pkg)
    except ValueError as e:
        assert "table outside" in str(e)
    else:
        raise AssertionError("out-of-file metadata table accepted")

    make_pkg(pkg)
    data = bytearray(pkg.read_bytes())
    # Duplicate metadata entry identifiers must not be silently accepted.
    struct.pack_into(">I", data, 0x820, 0x1000)
    pkg.write_bytes(data)
    try:
        mod.read_package(pkg)
    except ValueError as e:
        assert "duplicate" in str(e)
    else:
        raise AssertionError("duplicate metadata entry accepted")

    make_pkg(pkg)
    data = bytearray(pkg.read_bytes())
    data[0x2000] = 0
    data[0x2001] = 0
    pkg.write_bytes(data)
    try:
        mod.read_package(pkg)
    except ValueError as e:
        assert "param.sfo" in str(e)
    else:
        raise AssertionError("invalid SFO accepted")
    print("PASS: bad metadata offset, duplicate entries and broken SFO rejected")
print("INFO: tests are synthetic; no PS4 app or repackage built")
