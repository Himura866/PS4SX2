#!/usr/bin/env python3
"""Source invariants for the PS4 MTVU trace optimization, not an FPS benchmark."""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "pcsx2/MTVU.cpp")
src = path.read_text(encoding="utf-8")
checks = {
    "vu trace policy header": '#include "ps4/vm/HimuraVUDiagnostics.hpp"',
    "opt-in marker": 'HimuraVUDiagnostics::Configure(access("/data/HIMURA_PS4SX2/vm-vu-trace", F_OK) == 0)',
    "guard history": "if (!HimuraVUDiagnostics::Enabled())",
    "guard special log": "if (vu_trace && addr != -1",
    "gate diagnostics": "if (vu_trace)",
    "keep guest execution": "CpuVU1->Execute(vu1RunCycles);",
    "keep packet flow": "semaXGkick.Post();",
    "keep cycle accounting": "g_orbis_vu1_cycles.store",
    "keep run accounting": "g_orbis_vu1_runs.store",
    "keep synchronization": "vuCycles[vuCycleIdx].store(VU1.cycle, std::memory_order_release);",
    "keep buffer commit": "CommitReadPos();",
}
for label, fragment in checks.items():
    assert fragment in src, f"Missing {label}: {fragment}"
assert src.count(checks["opt-in marker"]) == 1
print(f"PASS: {len(checks)} static guest-path and diagnostics checks for {path}")
