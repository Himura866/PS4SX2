#!/usr/bin/env python3
"""R13 Silksong post-intro crash tracing and safe display-name rebranding.

Preserves internal /data/EdenPS4 paths to protect installed user data while the
migration protocol is developed. Does not remove upstream legal credits.
Applies LAST after the integrated R13 patches, guarded by exact anchors.
"""
from pathlib import Path
import sys

def one(s,old,new,label):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"R13 gameplay trace/rebrand {label}: expected 1, found {n}")
    return s.replace(old,new,1)

def apply(root):
    main=root/"eden/src/yuzu_ps4/main.cpp"
    src=main.read_text(encoding="utf8")
    # More frequent low-overhead, durable checkpoints during cutscene->gameplay;
    # no instrumentation on individual GPU draws, only once every 2 seconds.
    src=one(src,
        'auto next_status = std::chrono::steady_clock::now() + std::chrono::seconds{10};',
        'auto next_status = std::chrono::steady_clock::now() + std::chrono::seconds{2};',
        'first heartbeat')
    src=one(src,
        'next_status = std::chrono::steady_clock::now() + std::chrono::seconds{10};',
        'next_status = std::chrono::steady_clock::now() + std::chrono::seconds{2};',
        'subsequent heartbeat')
    src=one(src,
        '"quadros_compostos=%llu video=%llu audio=%llu memoria_extra_mib=%llu",',
        '"quadros_compostos=%llu video=%llu audio=%llu memoria_extra_mib=%llu fase=%s callbacks=%llu",',
        'crash checkpoint format')
    src=one(src,
        'static_cast<unsigned long long>(ps4_heap_overflow_size() >> 20));',
        'static_cast<unsigned long long>(ps4_heap_overflow_size() >> 20),\n'
        '                Common::PS4Diagnostics::stage.load(std::memory_order_relaxed),\n'
        '                static_cast<unsigned long long>(Common::PS4Diagnostics::MemoryCallbackTotal()));',
        'crash checkpoint stage and memory callbacks')
    src=one(src,
        'R11GameCheckpoint("andamento do jogo (10 s)", r13_state);',
        'R11GameCheckpoint("andamento do jogo (2 s)", r13_state);',
        'crash checkpoint interval')
    # The user-facing Data folder *label* and exported names can change
    # without moving any save, firmware or keys in the PS4 filesystem.
    src=one(src,
        '{"Data folder", "/data/EdenPS4"}',
        '{"Armazenamento", "Dados do HIMURA SWITCH (legado preservado)"}',
        'user-facing system info label')
    src=one(src,
        'const std::string destination = std::string{mount} + "/EdenPS4-" + name;',
        'const std::string export_name = std::string{name} == "eden.log" ? "emulator.log" :\n'
        '                                            std::string{name} == "eden.previous.log" ? "emulator.previous.log" : name;\n'
        '            const std::string destination = std::string{mount} + "/HIMURA-SWITCH-" + export_name;',
        'exported diagnostic names')
    src=one(src,
        '"Logs copied to USB. You can attach the EdenPS4-*.log files."',
        '"Relatorios do HIMURA SWITCH copiados para USB."',
        'logs exported notification')
    src=one(src,
        '"USB unavailable. Logs remain in /data/EdenPS4/"',
        '"USB indisponivel. Relatorios permanecem no armazenamento interno."',
        'logs unavailable notification')
    # No changes to Core::System, graphics backend, or user's real data roots.
    main.write_text(src,encoding="utf8")
    print("R13: post-intro 2-second crash checkpoints and non-destructive HIMURA names integrated")

if __name__ == "__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r13-gameplay-trace-brand.py <Eden4 checkout>")
    apply(Path(sys.argv[1]).resolve())
