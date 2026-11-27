#!/usr/bin/env python3
"""Apply only 131 approved PT-BR label bytes to an exact 04.89 staging COPY.

Incomplete UI translation; no PS4 boot validation. DO NOT INSTALL as final V15.
"""
import hashlib
from pathlib import Path

ORIGINAL_SHA256 = '5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381'
PATCHED_SHA256 = 'bab383c0271c2a7a3efa119c5e25b73459ad06d79c848f7d1c147e288e45bb6b'
EXPECTED_BYTES = 78376440
EXPECTED_CHANGED_BYTES = 131
# Offset, exact owner-export bytes, translated experimental bytes.
PATCHES = [
    (0x1de527a, "47616d65205370656564", "56656c6f636964616465"),
    (0x1df0b8a, "53686164", "43616368"),
    (0x1df0b8f, "722043", "205368"),
    (0x1df0b93, "636865", "646572"),
    (0x1df0b97, "4672616d65", "54656d706f"),
    (0x1df0b9d, "506163696e67", "71756164726f"),
    (0x1e27cbf, "47616d65", "4a6f676f"),
    (0x1e3df8f, "4e6577204564656e2030342e3839", "48494d5552412050533420563135"),
    (0x1e4bcbe, "50", "44"),
    (0x1e4bcc0, "72666f726d616e6365", "73656d70656e686f00"),
    (0x1e8369f, "41626f7574", "536f627265"),
    (0x1e8e48a, "53797374656d2053657474696e6773", "436f6e666967757261636f65730000"),
    (0x1e98ce2, "47616d65", "4a6f676f"),
    (0x1e98ce8, "616e64204b6579", "65204368617665"),
    (0x1ea8003, "4578", "5361"),
    (0x1ea8006, "74", "72"),
    (0x1ec95f6, "6e74726f6c", "6d616e646f"),
    (0x1eda12e, "7469", "6361"),
    (0x1eda131, "6e", "00"),
    (0x1ee3c1c, "6476616e636564", "76616e6361646f"),
    (0x1eef3f4, "416c6c20536f667477617265", "546f646f73204a6f676f7300"),
    (0x1f2758b, "46505320436f756e746572", "4d6f737472617220465053"),
]

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def verify_patch_table():
    ranges = []
    count = 0
    for offset, original_hex, translated_hex in PATCHES:
        before, after = bytes.fromhex(original_hex), bytes.fromhex(translated_hex)
        if len(before) != len(after) or before == after or offset < 0:
            raise ValueError('Invalid PT-BR patch')
        ranges.append((offset, offset + len(before)))
        count += len(before)
    ranges.sort()
    if count != EXPECTED_CHANGED_BYTES or any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])):
        raise ValueError('PT-BR patch overlaps or changed-byte count unexpected')
    return count

def patch_bytes(original):
    verify_patch_table()
    if len(original) != EXPECTED_BYTES or sha256(original) != ORIGINAL_SHA256:
        raise ValueError('Refusing unknown eboot: only original New Eden 04.89 supported')
    result = bytearray(original)
    for offset, original_hex, translated_hex in PATCHES:
        before, after = bytes.fromhex(original_hex), bytes.fromhex(translated_hex)
        if result[offset:offset + len(before)] != before:
            raise ValueError('Unexpected original bytes at offset %x' % offset)
        result[offset:offset + len(after)] = after
    if sha256(result) != PATCHED_SHA256:
        raise ValueError('Unexpected PT-BR executable SHA-256')
    return bytes(result)

if __name__ == '__main__':
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--input', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        cli.exit(2, 'STOP: output must be a new path separate from original\n')
    try:
        output = patch_bytes(args.input.read_bytes())
    except ValueError as error:
        cli.exit(2, 'STOP: ' + str(error) + '\n')
    args.output.write_bytes(output)
    print('PASS: exactly 131 label bytes changed in a separate experimental copy')
    print('NOT a complete UI translation; DO NOT INSTALL before PS4 tests')
