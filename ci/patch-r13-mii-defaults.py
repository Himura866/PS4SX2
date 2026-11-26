#!/usr/bin/env python3
"""R13 PS4: Mii default fallback for an empty Mii database.

Derived from Orbis Eden patch 0031, GPL-3.0-or-later:
https://github.com/MrKitsune9/Orbis-EDEN/blob/main/patches/eden/0031-PS4-built-in-Miis-when-database-is-empty.patch

Backport is isolated to four MiiManager::Get overloads. It does not change
the approved samurai launcher or claim to fix unrelated game crashes.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch-r13-mii-defaults.py <Eden4 checkout root>")

source = Path(sys.argv[1]) / "eden/src/core/hle/service/mii/mii_manager.cpp"
body = source.read_text(encoding="utf-8")
anchor = "    // Include default Mii at the end of the list\n    return BuildDefault("
if body.count(anchor) != 4:
    raise RuntimeError(f"R13 Mii backport: expected 4 fallback anchors, found {body.count(anchor)}")
replacement = (
    "    // Include default Mii at the end of the list\n"
    "#ifdef __ORBIS__\n"
    "    // Keep games using only database Miis from receiving an empty list.\n"
    "    if (mii_count == 0) {\n"
    "        source_flag = source_flag | SourceFlag::Default;\n"
    "    }\n"
    "#endif\n"
    "    return BuildDefault("
)
body = body.replace(anchor, replacement)
if body.count("source_flag = source_flag | SourceFlag::Default;") != 4:
    raise RuntimeError("R13 Mii backport: replacement count failed")
source.write_text(body, encoding="utf-8")
print("R13: four default Mii fallbacks inserted (PS4 only)")
