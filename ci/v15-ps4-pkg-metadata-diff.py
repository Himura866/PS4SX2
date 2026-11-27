#!/usr/bin/env python3
"""Read-only PS4 CNT/param.sfo comparison. No PFS decryption or PS4 execution.

Use with the owner's verified New Eden 04.89 PKG and any candidate PKG.
Reports structural differences important for package loader compatibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ORIGINAL_PKG_SHA = "06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd"
CONTENT_ID = "IV0000-EDNP00001_00-EDENPS4000000000"
EXPECTED_SFO_SHA = "9bfff1385d1cd7593825090616e4a0c198b7f0fb69a9ceaedb3e3eaf732f9c54"
EXPECTED_ICON_SHA = "a91ec10529ee9f371d7657dd6bb09ef5c0cc4d21ef72fdd114f44d9528ccb9f8"
MAX_ENTRY_COUNT = 1024
FIELDS = ("flags", "drm_type", "content_type", "content_flags", "content_id",
          "entry_count", "pfs_flags", "pfs_image_offset", "pfs_image_size")
SFO_FIELDS = ("APP_TYPE", "ATTRIBUTE", "CATEGORY", "SYSTEM_VER", "TITLE",
              "TITLE_ID", "CONTENT_ID", "APP_VER", "VERSION")


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sfo(raw):
    if len(raw) < 20 or raw[:4] != b"\x00PSF":
        raise ValueError("missing or invalid param.sfo")
    _, ver, keys_at, data_at, count = struct.unpack_from("<4sIIII", raw)
    if count > 256 or keys_at > len(raw) or data_at > len(raw) or 20 + 16 * count > len(raw):
        raise ValueError("param.sfo header beyond data")
    out = {}
    for index in range(count):
        keyoff, typ, length, maxsize, valueoff = struct.unpack_from("<HHIII", raw, 20 + 16 * index)
        key_start = keys_at + keyoff
        value_start = data_at + valueoff
        if key_start >= data_at or value_start > len(raw) or length > len(raw) - value_start or length > maxsize:
            raise ValueError("param.sfo entry out of bounds")
        end = raw.find(b"\x00", key_start, data_at)
        if end < 0:
            raise ValueError("param.sfo key not terminated")
        key = raw[key_start:end].decode("utf-8")
        value = raw[value_start:value_start + length]
        if typ == 0x0204:
            out[key] = value.rstrip(b"\x00").decode("utf-8")
        elif typ == 0x0404 and length == 4:
            out[key] = int.from_bytes(value, "little")
    return out


def read_package(path):
    path = Path(path)
    size = path.stat().st_size
    with path.open("rb") as f:
        head = f.read(0x5a0)
        if len(head) < 0x430 or head[:4] != b"\x7fCNT":
            raise ValueError("not a PS4 CNT package")
        u16 = lambda off: struct.unpack_from(">H", head, off)[0]
        u32 = lambda off: struct.unpack_from(">I", head, off)[0]
        u64 = lambda off: struct.unpack_from(">Q", head, off)[0]
        entry_count = u32(0x10)
        table_offset = u32(0x18)
        if not (1 <= entry_count <= MAX_ENTRY_COUNT):
            raise ValueError("PS4 CNT entry count unreasonable")
        if table_offset < 0x5a0 or table_offset > size or 32 * entry_count > size - table_offset:
            raise ValueError("PS4 CNT entry table outside file")
        content_id = head[0x40:0x70].split(b"\x00")[0].decode("ascii")
        header = {"flags": u32(0x04), "entry_count": entry_count,
                  "sc_entry_count": u16(0x14), "entry_count_2": u16(0x16),
                  "entry_table_offset": table_offset,
                  "content_id": content_id,
                  "drm_type": u32(0x70), "content_type": u32(0x74),
                  "content_flags": u32(0x78), "body_offset": u64(0x20),
                  "body_size": u64(0x28),
                  "pfs_flags": u64(0x408), "pfs_image_offset": u64(0x410),
                  "pfs_image_size": u64(0x418)}
        f.seek(table_offset)
        table = f.read(entry_count * 32)
        entries = {}
        for i in range(entry_count):
            entry_id, flags, unk1, unk2, offset, length, unk3, unk4 = struct.unpack_from(">IIIIIIII", table, i * 32)
            if entry_id in entries:
                raise ValueError("duplicate PS4 CNT table entry")
            if offset > size or length > size - offset:
                raise ValueError("PS4 CNT metadata entry out of bounds")
            entries[entry_id] = {"flags": flags, "offset": offset, "size": length}
        if 0x1000 not in entries:
            raise ValueError("PS4 CNT lacks param.sfo metadata entry")
        if entries[0x1000]["size"] > 64 * 1024:
            raise ValueError("param.sfo too large")
        f.seek(entries[0x1000]["offset"])
        raw_sfo = f.read(entries[0x1000]["size"])
        sfo = parse_sfo(raw_sfo)
        icon_sha = None
        if 0x1200 in entries:
            if entries[0x1200]["size"] > 10 * 1024 * 1024:
                raise ValueError("PS4 CNT icon too large")
            f.seek(entries[0x1200]["offset"])
            icon = f.read(entries[0x1200]["size"])
            if icon[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError("PS4 CNT icon metadata is not PNG")
            icon_sha = hashlib.sha256(icon).hexdigest()
    return {"file_size": size, "sha256": sha256_file(path), "header": header,
            "sfo": {k: sfo[k] for k in SFO_FIELDS if k in sfo},
            "sfo_sha256": hashlib.sha256(raw_sfo).hexdigest(),
            "icon_sha256": icon_sha,
            "metadata_entries": [{"id": f"0x{x:04x}", "size": y["size"]}
                                 for x, y in sorted(entries.items())]}


def audit(reference, candidate=None, output=None):
    original = read_package(reference)
    h, sfo = original["header"], original["sfo"]
    if original["sha256"] != ORIGINAL_PKG_SHA:
        raise ValueError("STOP: reference PKG is not the verified original 04.89")
    if h["drm_type"] != 0xF or h["content_type"] != 0x1A or h["content_flags"] != 0x0A000000:
        raise ValueError("STOP: original package metadata unexpectedly changed")
    if h["content_id"] != CONTENT_ID or original["sfo_sha256"] != EXPECTED_SFO_SHA or original["icon_sha256"] != EXPECTED_ICON_SHA:
        raise ValueError("STOP: original content ID/SFO/icon differs")
    for key, expected in {"APP_TYPE": 1, "ATTRIBUTE": 0x00010002,
                          "CATEGORY": "gd", "APP_VER": "04.89", "TITLE_ID": "EDNP00001"}.items():
        if sfo.get(key) != expected:
            raise ValueError("STOP: original SFO field mismatch: " + key)
    result = {"status": "READ_ONLY_PACKAGE_METADATA_AUDIT_NOT_PS4_TEST",
              "reference": original,
              "cautions": ["PKG metadata comparison does not prove loader acceptance",
                           "PFS/eboot are not decrypted or extracted by this script",
                           "Do not overwrite the proven-working EDNP00001 installation"]}
    if candidate is not None:
        trial = read_package(candidate)
        diffs = {}
        for key in FIELDS:
            if original["header"].get(key) != trial["header"].get(key):
                diffs["pkg_header." + key] = {"reference": original["header"].get(key),
                                               "candidate": trial["header"].get(key)}
        for key in SFO_FIELDS:
            if original["sfo"].get(key) != trial["sfo"].get(key):
                diffs["param.sfo." + key] = {"reference": original["sfo"].get(key),
                                            "candidate": trial["sfo"].get(key)}
        for key in ("sfo_sha256", "icon_sha256"):
            if original.get(key) != trial.get(key):
                diffs[key] = {"reference": original.get(key), "candidate": trial.get(key)}
        result["candidate"] = trial
        result["differences"] = diffs
        result["candidate_pkg_byte_identical"] = original["sha256"] == trial["sha256"]
    if output is not None:
        out = Path(output)
        if out.exists() or not out.parent.is_dir():
            raise ValueError("STOP: output exists or destination parent missing")
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-original-pkg", type=Path, required=True)
    parser.add_argument("--candidate-pkg", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.reference_original_pkg, args.candidate_pkg, args.out)
    except (OSError, ValueError, UnicodeError) as e:
        parser.exit(2, "AUDIT FAILED: " + str(e) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
