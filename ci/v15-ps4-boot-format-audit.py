#!/usr/bin/env python3
"""Read-only PS4 ELF/PKG format audit for the owner's New Eden 04.89.

Compares the exact user-exported executable with optional candidates.
A passing audit DOES NOT prove package authentication or console boot.
Never edits app0, PKG, keys, saves or the PS4 installation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

ORIGINAL_ZIP_SHA = "66e8154774498ce8bd30bde0af36b561cebd6f24ef2d3cdaabafa7ff9a16ec02"
ORIGINAL_EBOOT_SHA = "5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381"
ORIGINAL_PKG_SHA = "06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd"
ORIGINAL_SFO_SHA = "9bfff1385d1cd7593825090616e4a0c198b7f0fb69a9ceaedb3e3eaf732f9c54"
ORIGINAL_ICON_SHA = "a91ec10529ee9f371d7657dd6bb09ef5c0cc4d21ef72fdd114f44d9528ccb9f8"
ORIGINAL_MEMBER = "EDNP00001-app0/eboot.bin"
ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
ORIGINAL_PKG_FIELDS = {"param.sfo": (0x47F0, 1076, ORIGINAL_SFO_SHA),
                       "icon0.png": (0x6C30, 59196, ORIGINAL_ICON_SHA)}


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_elf(data, total_size):
    """Parse actual ELF64 program headers, not a guessed SELF magic or filename."""
    if len(data) < ELF_HEADER.size:
        raise ValueError("truncated ELF header")
    ident, etype, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = ELF_HEADER.unpack_from(data)
    if ident[:4] != b"\x7fELF" or ident[4] != 2 or ident[5] != 1:
        raise ValueError("not little-endian ELF64")
    if ehsize != ELF_HEADER.size or version != 1 or phsize != PROGRAM_HEADER.size or not (1 <= phnum <= 128):
        raise ValueError("unexpected ELF64 program header layout")
    end = phoff + phsize * phnum
    if phoff < ELF_HEADER.size or end > total_size or end > len(data):
        raise ValueError("program header table missing/truncated")
    segments = []
    for i in range(phnum):
        ptype, pflags, offset, vaddr, paddr, filesz, memsz, align = PROGRAM_HEADER.unpack_from(data, phoff + i * phsize)
        if offset > total_size or filesz > total_size - offset:
            raise ValueError("program segment outside ELF file")
        segments.append({"type": f"0x{ptype:08x}", "flags": pflags, "offset": offset,
                         "file_size": filesz, "memory_size": memsz, "vaddr": f"0x{vaddr:x}"})
    return {"format": "ELF64 little-endian", "osabi": ident[7], "type": f"0x{etype:04x}",
            "machine": f"0x{machine:04x}", "entry": f"0x{entry:x}",
            "program_header_count": phnum, "program_headers": segments,
            "program_table_sha256": hashlib.sha256(data[phoff:end]).hexdigest()}


def audit_stream(stream, total_size):
    h = hashlib.sha256()
    prefix = stream.read(min(total_size, 16384))
    h.update(prefix)
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            break
        h.update(block)
    result = parse_elf(prefix, total_size)
    result["size_bytes"] = total_size
    result["sha256"] = h.hexdigest()
    return result


def audit_original_zip(path):
    path = Path(path)
    if file_sha256(path) != ORIGINAL_ZIP_SHA:
        raise ValueError("STOP: source ZIP SHA-256 differs from the owner's verified export")
    with zipfile.ZipFile(path) as archive:
        found = [x for x in archive.infolist() if x.filename == ORIGINAL_MEMBER and not x.is_dir()]
        if len(found) != 1 or found[0].file_size != 78376440:
            raise ValueError("STOP: exact original eboot member missing or different size")
        if archive.testzip() is not None:
            raise ValueError("STOP: original ZIP CRC failure")
        with archive.open(found[0]) as stream:
            result = audit_stream(stream, found[0].file_size)
    if result["sha256"] != ORIGINAL_EBOOT_SHA:
        raise ValueError("STOP: original executable digest mismatch")
    if result["type"] != "0xfe10" or result["machine"] != "0x003e" or result["osabi"] != 9:
        raise ValueError("STOP: original ELF header does not match verified Orbis format")
    return result


def audit_pkg(path, known_original=False):
    path = Path(path)
    with path.open("rb") as f:
        magic = f.read(4)
    result = {"size_bytes": path.stat().st_size, "sha256": file_sha256(path),
              "pkg_magic_hex": magic.hex(), "has_ps4_cnt_magic": magic == b"\x7fCNT"}
    if not result["has_ps4_cnt_magic"]:
        raise ValueError("not a PS4 CNT package")
    if known_original:
        if result["sha256"] != ORIGINAL_PKG_SHA:
            raise ValueError("STOP: original 04.89 PKG hash mismatch")
        result["original_embedded_metadata"] = {}
        with path.open("rb") as f:
            for name, (offset, length, expected_hash) in ORIGINAL_PKG_FIELDS.items():
                f.seek(offset)
                data = f.read(length)
                digest = hashlib.sha256(data).hexdigest()
                if digest != expected_hash:
                    raise ValueError("STOP: verified original PKG " + name + " bytes changed")
                result["original_embedded_metadata"][name] = {"size": length, "sha256": digest}
    return result


def run(reference_zip, original_pkg=None, candidate_eboot=None, candidate_pkg=None, output=None):
    original = audit_original_zip(reference_zip)
    report = {"status": "READ_ONLY_DIAGNOSTIC_NOT_PS4_BOOT_TEST",
              "name_reserved_after_hardware_validation": "HIMURA SWITCH V15",
              "reference": {"source": "New Eden 04.89 exported app0", "eboot": original},
              "warnings": ["ELF and PKG header checks do not prove PS4 loader acceptance",
                           "pkg_validate checks container structure, not runtime execution",
                           "do not overwrite installed EDNP00001 on the PS4"]}
    if original_pkg is not None:
        report["reference"]["original_pkg"] = audit_pkg(original_pkg, known_original=True)
    if candidate_eboot is not None:
        candidate_path = Path(candidate_eboot)
        with candidate_path.open("rb") as f:
            candidate = audit_stream(f, candidate_path.stat().st_size)
        candidate["byte_identical_to_reference"] = candidate["sha256"] == original["sha256"]
        candidate["program_headers_identical_to_reference"] = candidate["program_table_sha256"] == original["program_table_sha256"]
        report["candidate_eboot"] = candidate
    if candidate_pkg is not None:
        report["candidate_pkg"] = audit_pkg(candidate_pkg)
        report["candidate_pkg"]["byte_identical_to_original_pkg"] = (
            report["candidate_pkg"]["sha256"] == ORIGINAL_PKG_SHA)
        report["candidate_pkg"]["contained_eboot_not_extracted"] = True
    if output is not None:
        dest = Path(output)
        if dest.exists() or not dest.parent.is_dir():
            raise ValueError("STOP: output exists or parent directory missing")
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-zip", type=Path, required=True)
    parser.add_argument("--original-pkg", type=Path)
    parser.add_argument("--candidate-eboot", type=Path)
    parser.add_argument("--candidate-pkg", type=Path)
    parser.add_argument("--out", type=Path)
    a = parser.parse_args()
    try:
        result = run(a.reference_zip, a.original_pkg, a.candidate_eboot, a.candidate_pkg, a.out)
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        parser.exit(2, "AUDIT FAILED: " + str(e) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
