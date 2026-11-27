#!/usr/bin/env python3
"""Wrap an already-built PS4 Orbis ELF64 as a fake SELF (fSELF).
Preserves executable segment bytes. Not a PS4 hardware test.
Layout based on the publicly documented OpenOrbis/create-fself/pkg/fself.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ELF = struct.Struct('<16sHHIQQQIHHHHHH')
PH = struct.Struct('<IIQQQQQQ')
SELF_MAGIC = b'\x4f\x15\x3d\x1d'
SIGNABLE = {1, 0x61000010, 0x61000000}
ORIGINAL_SHA = '5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381'


def align(n, k=16):
    return (n + k - 1) & -k


def inspect_elf(data, require_original=True):
    if len(data) < ELF.size:
        raise ValueError('truncated input')
    (ident, typ, machine, version, entry, phoff, shoff, flags, ehsize,
     phentsize, phnum, shentsize, shnum, shstrndx) = ELF.unpack_from(data)
    digest = hashlib.sha256(data).hexdigest()
    if require_original and digest != ORIGINAL_SHA:
        raise ValueError('STOP: original New Eden 04.89 ELF hash does not match')
    if (ident[:4] != b'\x7fELF' or ident[4] != 2 or ident[5] != 1 or
            ident[7] != 9 or typ not in (0xfe00, 0xfe10, 0xfe18) or
            machine != 62 or version != 1 or ehsize != 64 or phentsize != 56 or
            not (1 <= phnum <= 64) or phoff < ELF.size or
            phoff + phnum * phentsize > len(data)):
        raise ValueError('not a compatible prebuilt PS4 Orbis ELF64')
    segments = []
    for i in range(phnum):
        ptyp, pflags, off, vaddr, paddr, fsize, msize, palign = PH.unpack_from(data, phoff + 56 * i)
        if off > len(data) or fsize > len(data) - off:
            raise ValueError('ELF segment extends beyond input')
        if ptyp in SIGNABLE:
            segments.append((i, off, fsize, ptyp))
    if not segments or len(segments) > 16:
        raise ValueError('no signable load segments')
    return digest, phnum, segments, phoff


def wrap(data, require_original=True, paid=0x3800000000000011):
    digest, phnum, segments, phoff = inspect_elf(data, require_original)
    nentries = len(segments) * 2
    base_header = align(0x20 + nentries * 0x20 + 0x40 + phnum * 0x38) + 0x40 + 0x30
    cursor = base_header + nentries * 0x50 + 0x50 + 0x100
    entries = []
    blocks = []
    for segindex, off, fsize, _ in segments:
        metadata = b'\0' * (align(fsize, 0x4000) // 0x4000 * 0x20)
        props_meta = 4 | (1 << 16) | ((len(entries)+1) << 20)
        entries.append((props_meta, cursor, len(metadata), len(metadata)))
        blocks.append((cursor, metadata))
        cursor = align(cursor + len(metadata))
        props_data = 4 | (1 << 11) | (2 << 12) | (segindex << 20)
        entries.append((props_data, cursor, fsize, fsize))
        blocks.append((cursor, memoryview(data)[off:off + fsize]))
        cursor = align(cursor + fsize)
    if base_header > 0xffff or (nentries * 0x50 + 0x50 + 0x100) > 0xffff:
        raise ValueError('SELF header fields exceed 16 bits')
    out = bytearray(cursor)
    struct.pack_into('<I4BIHHQHH', out, 0,
                     0x1d3d154f, 0, 1, 1, 0x12, 0x101, base_header,
                     nentries * 0x50 + 0x50 + 0x100, cursor, nentries, 0x22)
    pos = 0x20
    for item in entries:
        struct.pack_into('<4Q', out, pos, *item)
        pos += 32
    out[pos:pos + 0x40] = data[:0x40]
    pos += 0x40
    out[pos:pos + phnum * 56] = data[phoff:phoff + phnum * 56]
    pos = align(pos + phnum * 56)
    struct.pack_into('<4Q32s', out, pos, paid, 1, 0, 0, bytes.fromhex(digest))
    pos += 0x40
    struct.pack_into('<H', out, pos, 3)
    pos += 0x30 + nentries * 0x50
    struct.pack_into('<I', out, pos + 0x30, 0x10000)
    pos += 0x50 + 0x100
    if pos != blocks[0][0]:
        raise ValueError('SELF offset accounting failed')
    for off, block in blocks:
        out[off:off + len(block)] = block
    return bytes(out), {
        'original_elf_sha256': digest,
        'wrapped_fself_sha256': hashlib.sha256(out).hexdigest(),
        'original_elf_size': len(data), 'wrapped_size': len(out),
        'original_elf_program_headers': phnum, 'self_entries': nentries,
        'preserves_original_segment_bytes': True,
        'disclaimer': 'Structural conversion, not a PS4 hardware boot test'}


def validate_wrapper(raw, wrapped):
    digest, phnum, segments, phoff = inspect_elf(raw, False)
    if len(wrapped) < 0x20 or wrapped[:4] != SELF_MAGIC:
        raise ValueError('not a PS4 fSELF')
    _, version, mode, endian, attribs, keytype, headerlen, metalen, filesize, nentries, flags = struct.unpack_from('<I4BIHHQHH', wrapped)
    if (mode, endian, nentries) != (1, 1, 2 * len(segments)) or filesize != len(wrapped):
        raise ValueError('SELF header mismatch')
    for k, (segindex, off, fsize, _) in enumerate(segments):
        props, offset, data_size, memsize = struct.unpack_from('<4Q', wrapped, 0x20 + (k * 2 + 1) * 32)
        if data_size != fsize or offset > len(wrapped) or data_size > len(wrapped) - offset:
            raise ValueError('SELF data segment out of range')
        if wrapped[offset:offset + fsize] != raw[off:off + fsize]:
            raise ValueError('SELF wrapped bytes differ from original ELF segment')
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original-elf', type=Path, required=True)
    p.add_argument('--output-eboot', type=Path, required=True)
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    if a.output_eboot.exists() or (a.report and a.report.exists()):
        p.error('refusing overwrite')
    raw = a.original_elf.read_bytes()
    wrapped, report = wrap(raw)
    validate_wrapper(raw, wrapped)
    a.output_eboot.write_bytes(wrapped)
    if a.report:
        a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: original PS4 Orbis ELF wrapped as fSELF; PS4 BOOT NOT TESTED')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
