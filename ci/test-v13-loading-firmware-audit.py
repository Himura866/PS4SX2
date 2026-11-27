#!/usr/bin/env python3
"""Static regression guards; no claims of PS4 gameplay or firmware installation."""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "v13audit", Path(__file__).with_name("patch-v13-loading-firmware-audit.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if len(sys.argv) != 2:
    raise SystemExit("Uso: test-v13-loading-firmware-audit.py <patched checkout>")
root = Path(sys.argv[1]) / "eden/src/yuzu_ps4"
main = (root / "main.cpp").read_text(encoding="utf-8")
ui = (root / "ui_launcher.cpp").read_text(encoding="utf-8")

required = [
    'Arquivo do jogo ausente ou inacessivel. Verifique o HD USB.',
    'r13_load_audit_stop.store(true',
    'r13_load_audit_phase.store(2',
    'r13_load_audit_phase.store(3',
    'r13_load_audit_phase.store(4',
    'R11GameCheckpoint("carregamento acima de 30 s"',
    'std::to_string(r13_load_ms) + " ms"',
    '{"Chaves", keys ? "Arquivo presente (nao validado)"',
    '{"Firmware", firmware ? "Dados presentes (nao verificados)"',
]
for anchor in required:
    assert anchor in main, f"Missing early-load/firmware diagnostic: {anchor}"
assert main.index('r13_load_audit_phase.store(2') < main.index('system.Load(')
assert main.index('r13_load_audit_stop.store(true', main.index('R11GameCheckpoint("guest emulation running")')) < main.index('std::atomic<u64> frontend_ticks')
assert 'Importacao de firmware, chaves e atualizacoes ainda nao esta disponivel nesta V13.' in ui
assert 'firmware ? "Instalado"' not in main
try:
    module.patch_main(main)
except RuntimeError:
    pass
else:
    raise AssertionError("Applying early-load patch twice must fail")
print("PASS V13: early-load diagnostics, USB fail-fast, truthful status; NO installer claims")
