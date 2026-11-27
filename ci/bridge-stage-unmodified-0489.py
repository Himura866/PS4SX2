#!/usr/bin/env python3
"""Prepare a byte-exact New Eden 04.89 Image0 from the owner's verified files.

No binary patches, branding, PS4 PKG creation, game files, or remote uploads.
Original inputs are read-only. This is a preflight stage, not an installable app.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


def load_local(filename, module_name):
    spec = importlib.util.spec_from_file_location(module_name, Path(__file__).with_name(filename))
    if spec is None or spec.loader is None:
        raise ValueError("Missing local verification module: " + filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_source(path, expected, label):
    if not path.is_file() or path.is_symlink() or hash_file(path) != expected:
        raise ValueError("STOP: exact original " + label + " missing or SHA-256 differs")


def stage_unmodified(pkg, app0_zip, out):
    pkg, app0_zip, out = Path(pkg), Path(app0_zip), Path(out)
    report_path = out.with_name(out.name + "-integrity.json")
    if out.exists() or report_path.exists():
        raise ValueError("STOP: destination or report exists; refusing overwrite")
    if not out.parent.is_dir():
        raise ValueError("STOP: output parent must exist")
    prep = load_local("prepare-neweden-v15-image0.py", "neweden_orig_zip_rules")
    guard = load_local("v15-preflight-gp4-from-exact-app0.py", "neweden_orig_image_rules")
    require_source(pkg, prep.ORIGINAL_PKG_SHA, "NewEden-04.89.pkg")
    require_source(app0_zip, prep.SOURCE_ZIP_SHA, "EDNP00001-app0.zip")
    if set(guard.BASELINE_HASHES) != guard.EXPECTED:
        raise ValueError("STOP: manifest is incomplete")
    if guard.BASELINE_HASHES["eboot.bin"] != prep.ORIGINAL_EBOOT_SHA:
        raise ValueError("STOP: source hashes disagree")

    with zipfile.ZipFile(app0_zip) as archive:
        members = prep.zip_entries_checked(archive)
        if archive.testzip() is not None:
            raise ValueError("STOP: original ZIP CRC failed")
        with tempfile.TemporaryDirectory(prefix=".himura-baseline-", dir=out.parent) as temporary:
            work = Path(temporary)
            image0 = work / "image0"
            image0.mkdir()
            for name, info in sorted(members.items()):
                target = image0.joinpath(*name.split("/"))
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("xb") as dest:
                    shutil.copyfileobj(source, dest, 1024 * 1024)
                if target.stat().st_size != info.file_size:
                    raise ValueError("STOP: truncated ZIP entry " + name)
                if hash_file(target) != guard.BASELINE_HASHES[name]:
                    raise ValueError("STOP: changed ZIP entry " + name)

            with pkg.open("rb") as original:
                for filename, (offset, length) in prep.META_OFFSETS.items():
                    original.seek(offset)
                    data = original.read(length)
                    target = image0 / "sce_sys" / filename
                    target.parent.mkdir(exist_ok=True, parents=True)
                    target.write_bytes(data)
                    if len(data) != length or hash_file(target) != guard.BASELINE_HASHES["sce_sys/" + filename]:
                        raise ValueError("STOP: original PKG metadata mismatch: " + filename)

            manifest = guard.make(image0, work / "gp4-audit")
            if manifest["file_count"] != 15 or hash_file(image0 / "eboot.bin") != prep.ORIGINAL_EBOOT_SHA:
                raise ValueError("STOP: exact 15-file app0 baseline not proven")
            report = {
                "status": "STAGED_ONLY_NOT_PKG_NOT_PS4_TESTED",
                "base": "New Eden 04.89",
                "identity": "EDNP00001",
                "source_pkg_sha256": prep.ORIGINAL_PKG_SHA,
                "source_app0_zip_sha256": prep.SOURCE_ZIP_SHA,
                "file_count": manifest["file_count"],
                "files": manifest["files"],
                "original_eboot_unchanged": True,
                "original_metadata_unchanged": True,
                "pending": ["PS4 packaging/validation", "PS4 boot of repacked baseline", "R13 UI integration"],
            }
            (work / "integrity.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            # All hash and SFO checks completed before any output is published.
            image0.rename(out)
            (work / "integrity.json").rename(report_path)
            return report


def main():
    p = argparse.ArgumentParser(description="Stage only the exact original New Eden 04.89 Image0")
    p.add_argument("--original-pkg", required=True, type=Path)
    p.add_argument("--app0-zip", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    result = stage_unmodified(args.original_pkg, args.app0_zip, args.out)
    print("PASS: %s exact original app0 files; NO PKG built." % result["file_count"])
    print("NEXT: separately validate original-only PKG build and boot on PS4 Pro.")


if __name__ == "__main__":
    main()
