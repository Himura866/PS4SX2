#!/usr/bin/env python3
"""Invoke the real pinned OpenOrbis create-gp4 with synthetic app files only.

This validates CLI compatibility and LibOrbisPkg's GP4-relative orig_path
resolution. It does not compile or package the actual New Eden emulator.
"""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from xml.etree import ElementTree as ET

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("v15_builder",here/"build-neweden-v15-pkg.py")
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--create-gp4",type=Path,required=True)
    args=ap.parse_args()
    tool=args.create_gp4.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="v15-real-gp4-") as t:
        stage=Path(t)/"Image0"
        (stage/"sce_sys").mkdir(parents=True)
        (stage/"eboot.bin").write_bytes(b"SYNTHETIC_TEST_EBOOT_NOT_PS4")
        (stage/"sce_sys"/"icon0.png").write_bytes(b"SYNTHETIC_ICON_NOT_PNG")
        paths=["eboot.bin","sce_sys/icon0.png"]
        gp4=stage/"test.gp4"
        subprocess.run([str(tool),"-out",str(gp4),
                        "--content-id="+builder.CONTENT_ID,
                        "--files"," ".join(paths)],
                       cwd=stage,check=True,timeout=60)
        if not gp4.is_file():
            raise AssertionError("OpenOrbis did not create a GP4")
        count=builder.validate_gp4_sources(gp4,stage,paths)
        if count!=2:
            raise AssertionError("Expected two GP4 source entries")
        root=ET.parse(gp4).getroot()
        assert root.find("./volume/package").get("content_id")==builder.CONTENT_ID
        assert root.find("./volume/volume_type").text=="pkg_ps4_app"
        print("PASS: real OpenOrbis create-gp4 executable generated a correct GP4")
        print("PASS: LibOrbisPkg source resolution from GP4 directory verified")
        print("NO PRIVATE INPUT, NO PKG, NO PS4 BOOT")
if __name__=="__main__":
    main()
