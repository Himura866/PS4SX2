#!/usr/bin/env python3
"""Synthetic regression: no owner's PKG, firmware, keys or games."""
import importlib.util
from pathlib import Path
import struct

spec = importlib.util.spec_from_file_location('v15_fself', Path(__file__).with_name('v15-wrap-orbis-fself.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

raw = bytearray(8192)
raw[:64] = m.ELF.pack(b'\x7fELF\x02\x01\x01\x09' + bytes(8),
                      0xfe10, 62, 1, 32, 64, 0, 0, 64, 56, 2, 0, 0, 0)
m.PH.pack_into(raw, 64, 1, 5, 4096, 0, 0, 256, 256, 0x1000)
m.PH.pack_into(raw, 120, 0x61000000, 4, 6144, 0, 0, 128, 0, 16)
raw[4096:4352] = bytes(range(256))
raw[6144:6272] = bytes(range(128))
out, info = m.wrap(bytes(raw), require_original=False)
assert out[:4] == m.SELF_MAGIC
assert m.validate_wrapper(bytes(raw), out)
assert info['self_entries'] == 4
assert info['preserves_original_segment_bytes']
assert info['wrapped_fself_sha256'] != info['original_elf_sha256']

corrupted = bytearray(out)
entry_offset = struct.unpack_from('<Q', out, 0x20 + 32 + 8)[0]
corrupted[entry_offset + 12] ^= 1
try:
    m.validate_wrapper(bytes(raw), bytes(corrupted))
except ValueError as exc:
    assert 'differ' in str(exc)
else:
    raise AssertionError('corrupted wrapped segment accepted')
try:
    m.wrap(bytes(raw), require_original=True)
except ValueError as exc:
    assert 'hash' in str(exc)
else:
    raise AssertionError('unverified ELF accepted')
try:
    m.wrap(b'WRONG', require_original=False)
except ValueError:
    pass
else:
    raise AssertionError('garbage ELF accepted')
print('PASS: Orbis ELF -> fSELF, byte preservation, tamper detection, SHA guard')
print('INFO: no PS4 hardware test and no installable PKG produced')
