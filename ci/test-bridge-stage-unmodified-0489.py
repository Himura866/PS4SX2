#!/usr/bin/env python3
"""Negative preflight tests; no owner binaries, no PKG, and no PS4 boot claims."""
import importlib.util
from pathlib import Path
import tempfile
import zipfile


def load(name, modname):
    spec = importlib.util.spec_from_file_location(modname, Path(__file__).with_name(name))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bridge = load("bridge-stage-unmodified-0489.py", "bridge_0489")
prep = load("prepare-neweden-v15-image0.py", "source_export_rules")
guard = load("v15-preflight-gp4-from-exact-app0.py", "source_app0_rules")

assert guard.BASELINE_HASHES["eboot.bin"] == prep.ORIGINAL_EBOOT_SHA
assert guard.BASELINE_HASHES["sce_sys/param.sfo"] == prep.ORIGINAL_SFO_SHA
assert guard.BASELINE_HASHES["sce_sys/icon0.png"] == prep.ORIGINAL_ICON_SHA
assert len(guard.BASELINE_HASHES) == 15

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    pkg, export, dest = root / "source.pkg", root / "source.zip", root / "image0"
    # Missing inputs must stop before creating any destination.
    try:
        bridge.stage_unmodified(pkg, export, dest)
    except ValueError as e:
        assert "missing" in str(e) or "differs" in str(e), str(e)
    else:
        raise AssertionError("missing originals accepted")
    assert not dest.exists() and not dest.with_name(dest.name + "-integrity.json").exists()
    print("PASS: originals required; no output on missing input")

    pkg.write_bytes(b"not-original")
    try:
        bridge.stage_unmodified(pkg, export, dest)
    except ValueError as e:
        assert "SHA-256" in str(e), str(e)
    else:
        raise AssertionError("incorrect original PKG accepted")
    assert not dest.exists()
    print("PASS: wrong PKG blocked")

    dest.mkdir()
    try:
        bridge.stage_unmodified(pkg, export, dest)
    except ValueError as e:
        assert "overwrite" in str(e), str(e)
    else:
        raise AssertionError("existing output was not protected")
    print("PASS: overwrite blocked")

    # The verified PS4-export ZIP parser must reject path traversal and
    # unexpected files; this is tested without any user-supplied app binaries.
    malformed = root / "malformed.zip"
    with zipfile.ZipFile(malformed, "w") as z:
        z.writestr("EDNP00001-app0/../../payload.bin", b"x")
    with zipfile.ZipFile(malformed) as z:
        try:
            prep.zip_entries_checked(z)
        except ValueError as e:
            assert "suspeito" in str(e), str(e)
        else:
            raise AssertionError("ZIP path traversal accepted")
    print("PASS: unsafe ZIP member rejected")

print("PASS: integrity gate negative tests completed. No PKG, no console test.")
