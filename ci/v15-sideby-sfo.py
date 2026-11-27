#!/usr/bin/env python3
"""Change ONLY a copied New Eden 04.89 param.sfo for a distinct V15 test title.
Not sufficient to prove runtime data separation or a PS4 boot.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SFO_SHA = '9bfff1385d1cd7593825090616e4a0c198b7f0fb69a9ceaedb3e3eaf732f9c54'
TITLE_ID = 'HIMU00015'
CONTENT_ID = 'IV0000-HIMU00015_00-HIMURASWITCHV150'
TITLE = 'HIMURA SWITCH V15'
APP_VER = '15.00'
REPLACEMENTS = {'TITLE_ID': TITLE_ID, 'CONTENT_ID': CONTENT_ID, 'TITLE': TITLE,
                'APP_VER': APP_VER, 'VERSION': APP_VER}


def patch(original):
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SFO_SHA:
        raise ValueError('STOP: input must be exact untouched 04.89 original param.sfo')
    buf = bytearray(original)
    if len(buf) < 20 or buf[:4] != b'\x00PSF':
        raise ValueError('invalid SFO header')
    _, version, keys, values, count = struct.unpack_from('<4sIIII', buf)
    if count > 128 or keys >= len(buf) or values >= len(buf) or 20 + count * 16 > len(buf):
        raise ValueError('SFO index outside data')
    replaced = set()
    for i in range(count):
        entry_at = 20 + 16*i
        keyoff, typ, length, capacity, off = struct.unpack_from('<HHIII', buf, entry_at)
        keypos = keys + keyoff
        end = buf.find(b'\x00', keypos, values)
        if end < 0:
            raise ValueError('unterminated SFO key')
        name = bytes(buf[keypos:end]).decode('utf-8')
        if name not in REPLACEMENTS:
            continue
        if typ != 0x0204 or values + off + capacity > len(buf):
            raise ValueError('invalid SFO replacement slot: ' + name)
        value = REPLACEMENTS[name].encode('utf-8') + b'\x00'
        if len(value) > capacity:
            raise ValueError('SFO value too large: ' + name)
        start = values + off
        buf[start:start + capacity] = value.ljust(capacity, b'\x00')
        struct.pack_into('<I', buf, entry_at + 4, len(value))
        replaced.add(name)
    if replaced != set(REPLACEMENTS):
        raise ValueError('SFO fields missing: ' + str(set(REPLACEMENTS)-replaced))
    return bytes(buf)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-sfo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a=p.parse_args()
    if a.out.exists():
        p.error('refusing overwrite')
    a.out.write_bytes(patch(a.original_sfo.read_bytes()))
    print('PASS: copy-only V15 test SFO; runtime/data isolation NOT proven')


if __name__=='__main__':
    main()
