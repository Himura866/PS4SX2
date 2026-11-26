#!/usr/bin/env python3
"""Fast fail-closed V15 package-builder checks; no owner's binary required."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v15_pkg_builder", here / "build-neweden-v15-pkg.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix="v15-pkg-fast-gates-") as tmp:
    root = Path(tmp)
    image = root / "image0"
    image.mkdir()
    gp4 = root / "create-gp4"
    tool = root / "PkgTool.Core"
    gp4.write_text("not executable")
    tool.write_text("not executable")
    dest = root / "out"
    args = SimpleNamespace(
        allow_experimental=False,
        image0=image,
        out=dest,
        create_gp4=str(gp4),
        pkgtool=str(tool),
        r13_icon=root / "not-present.webp",
    )
    def rejected(message):
        try:
            module.run(args)
        except ValueError as err:
            assert message in str(err), (message, err)
        else:
            raise AssertionError("unsafe V15 builder accepted " + message)

    rejected("explicit --allow-experimental needed")
    assert not dest.exists()
    print("PASS: explicit experimental approval required")

    args.allow_experimental = True
    args.image0 = root / "missing-image0"
    rejected("Image0 missing")
    assert not dest.exists()
    print("PASS: missing private source rejected")

    args.image0 = image
    dest.mkdir()
    marker = dest / "owner-do-not-overwrite.txt"
    marker.write_text("untouched")
    rejected("Refusing to overwrite PKG output")
    assert marker.read_text() == "untouched"
    print("PASS: pre-existing output directory rejected without modifying files")

config = (here.parent / ".circleci" / "config.yml").read_text()
assert "mkdir -p v15-pkg-status v15-pkg-output" not in config
assert "test ! -e v15-pkg-output" in config
print("PASS: CircleCI does not pre-create the output directory")
print("PASS: fast PKG gates passed; NO PKG generated or PS4 boot claimed")
