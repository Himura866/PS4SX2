#!/usr/bin/env python3
"""Check GP4 file-path resolution without a PS4 binary or private input."""
import importlib.util
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

builder_path=Path(__file__).with_name("build-neweden-v15-pkg.py")
spec=importlib.util.spec_from_file_location("v15_pkg_builder",builder_path)
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

with tempfile.TemporaryDirectory(prefix="v15-gp4-source-") as temp:
    root=Path(temp)
    stage=root/"Image0"
    (stage/"sce_sys").mkdir(parents=True)
    (stage/"eboot.bin").write_bytes(b"PS4 TEST CONTENT, NOT A REAL EBOOT")
    (stage/"sce_sys"/"icon0.png").write_bytes(b"MOCK ICON")
    names=["eboot.bin","sce_sys/icon0.png"]
    x=ET.Element("psproject",fmt="gp4",version="1000")
    vol=ET.SubElement(x,"volume")
    ET.SubElement(vol,"package",{"content_id":builder.CONTENT_ID})
    files=ET.SubElement(x,"files",{"img_no":"0"})
    a=ET.SubElement(files,"file",{"targ_path":names[0],"orig_path":names[0]})
    b=ET.SubElement(files,"file",{"targ_path":names[1],"orig_path":names[1]})
    gp4=stage/"project.gp4"
    def write():
        ET.ElementTree(x).write(gp4,encoding="utf-8",xml_declaration=True)
    def reject(needle):
        try:
            builder.validate_gp4_sources(gp4,stage,names)
        except (ValueError,FileNotFoundError) as exc:
            assert needle in str(exc),(needle,str(exc))
        else:
            raise AssertionError("Unsafe GP4 passed: "+needle)

    write()
    assert builder.validate_gp4_sources(gp4,stage,names)==2
    print("PASS: GP4 beside staged files resolves all source paths")

    wrong=root/"project.gp4"
    gp4.rename(wrong)
    gp4=wrong
    reject("GP4 must reside in the stage folder")
    gp4.rename(stage/"project.gp4")
    gp4=stage/"project.gp4"
    print("PASS: GP4 outside stage refused")

    b.set("orig_path","../other/icon.png")
    write()
    reject("Unsafe GP4 source path")
    b.set("orig_path","eboot.bin")
    write()
    reject("does not resolve to verified image file")
    b.set("orig_path","sce_sys/icon0.png")
    a.set("targ_path","unexpected.bin")
    write()
    reject("GP4 files do not match")
    a.set("targ_path",names[0])
    write()
    assert builder.validate_gp4_sources(gp4,stage,names)==2
    print("PASS: rejected traversal, wrong source, unexpected target")

builder_source=builder_path.read_text(encoding="utf-8")
assert "gp4=stage/'experimental.gp4'" in builder_source
assert "validate_gp4_sources(gp4,stage,verified_paths)" in builder_source
print("PASS: actual V15 builder stages GP4 correctly; no PKG created")
