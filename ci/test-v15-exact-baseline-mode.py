#!/usr/bin/env python3
"""Regression test: the baseline guard rejects changed executable/assets."""
import importlib.util
import hashlib
import tempfile
from pathlib import Path

spec=importlib.util.spec_from_file_location("v15_pkg_builder", Path(__file__).with_name("build-neweden-v15-pkg.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as temp:
    stage=Path(temp)
    (stage/"sce_sys").mkdir()
    (stage/"eboot.bin").write_bytes(b"original-working-eboot")
    (stage/"sce_sys"/"param.sfo").write_bytes(b"original-sfo")
    report={"files":[{"path":str(p.relative_to(stage)), "sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in stage.rglob("*") if p.is_file()]}
    assert mod.assert_staged_baseline(report,stage)==2
    (stage/"eboot.bin").write_bytes(b"modified-eboot")
    try:
        mod.assert_staged_baseline(report,stage)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("Baseline guard accepted modified executable")
    (stage/"eboot.bin").write_bytes(b"original-working-eboot")
    (stage/"experimental.gp4").write_text("generated package recipe")
    assert mod.assert_staged_baseline(report,stage,allow_generated_gp4=True)==2
    (stage/"new-file").write_text("unwanted")
    try:
        mod.assert_staged_baseline(report,stage,allow_generated_gp4=True)
    except ValueError as exc:
        assert "file list changed" in str(exc)
    else:
        raise AssertionError("Baseline guard accepted added files")
print("PASS: baseline byte integrity, modification rejection and added-file rejection")
