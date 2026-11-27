#!/usr/bin/env python3
"""Synthetic regressions for the read-only PS4 executable audit (no owner binaries)."""
import importlib.util
import io
from pathlib import Path
import struct
import tempfile

spec = importlib.util.spec_from_file_location("audit_v15_elf", Path(__file__).with_name("v15-ps4-boot-format-audit.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def elf(ph_offset=64, segment_offset=1024, segment_size=16, etype=0xfe10):
    buf = bytearray(4096)
    ident = b"\x7fELF" + bytes([2, 1, 1, 9]) + bytes(8)
    mod.ELF_HEADER.pack_into(buf, 0, ident, etype, 0x3e, 1, 0x20, ph_offset, 0, 0, 64, 56, 1, 0, 0, 0)
    mod.PROGRAM_HEADER.pack_into(buf, ph_offset, 1, 5, segment_offset, 0, 0, segment_size, segment_size, 0x1000)
    return bytes(buf)


ok = mod.parse_elf(elf(), 4096)
assert ok["type"] == "0xfe10" and ok["machine"] == "0x003e" and ok["osabi"] == 9
assert ok["program_header_count"] == 1
assert len(ok["program_table_sha256"]) == 64
stream = mod.audit_stream(io.BytesIO(elf()), 4096)
assert stream["sha256"] == mod.hashlib.sha256(elf()).hexdigest()
print("PASS: valid synthetic Orbis ELF and segment layout inspected")

bad = bytearray(elf())
bad[0] = 0
try:
    mod.parse_elf(bytes(bad), len(bad))
except ValueError as exc:
    assert "ELF64" in str(exc)
else:
    raise AssertionError("non-ELF file accepted")

out_of_bounds_table = bytearray(elf())
# Patch e_phoff at ELF64 byte offset 32 *after* constructing a valid file.
# This tests the parser, not struct.pack_into()'s buffer-size check.
struct.pack_into("<Q", out_of_bounds_table, 32, 4050)
for candidate in [elf(segment_offset=4092, segment_size=20), bytes(out_of_bounds_table)]:
    try:
        mod.parse_elf(candidate, len(candidate))
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-bounds ELF layout accepted")
print("PASS: non-ELF and out-of-bounds ELF entries rejected")

with tempfile.TemporaryDirectory() as directory:
    d = Path(directory)
    pkg = d / "synthetic.pkg"
    pkg.write_bytes(b"\x7fCNT" + bytes(40))
    assert mod.audit_pkg(pkg)["has_ps4_cnt_magic"]
    pkg.write_bytes(b"WRONG" + bytes(40))
    try:
        mod.audit_pkg(pkg)
    except ValueError as exc:
        assert "CNT" in str(exc)
    else:
        raise AssertionError("non-PKG file accepted")

    try:
        mod.audit_original_zip(d / "missing-original.zip")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("missing owner's ZIP accepted")

print("PASS: PS4 CNT magic and absent original inputs gated")
print("INFO: No owner binaries used, no PKG produced, no PS4 hardware test")
