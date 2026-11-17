#!/usr/bin/env python3
"""Static integration checks. They do not represent a PS4 FPS benchmark."""
from pathlib import Path

vm = Path("pcsx2/VMManager.cpp").read_text(encoding="utf-8")
db = Path("pcsx2/GameDatabase.cpp").read_text(encoding="utf-8")
gs = Path("pcsx2/GS/GSState.cpp").read_text(encoding="utf-8")

checks = {
    "opt-in global marker": "/data/PS4SX2/vm-gs-draw-buffering-all" in vm,
    "rollback marker": "/data/PS4SX2/vm-no-draw-buffering" in vm,
    "game database preserved": "HimuraDrawBufferingPolicy::Resolve" in vm,
    "game database fixes still applied": "game->applyGSHardwareFixes(EmuConfig.GS)" in vm,
    "PS4-only override": "#if defined(PCSX2_PS4_VM_BOOT)" in vm,
    "Carbon PAL-F exception": '"SLES-54402"' in db and "GSHWFixId::DrawBuffering" in db,
    "real draw buffering implementation": "GSConfig.UserHacks_DrawBuffering" in gs,
}
for name, ok in checks.items():
    assert ok, "FAIL: " + name
    print("PASS:", name)
