#!/usr/bin/env python3
"""HIMURA SWITCH V13: early load visibility + conservative file/firmware audit.

The existing R13 watchdog only starts after system.Run(). This patch adds a
temporary, read-only watchdog during earlier (potentially blocking) stages.
It does not change guest GPU/CPU timings, firmware contents, keys or saves.
Runs after patch-r13-usb-ptbr.py on the pinned Eden4 disposable checkout.
"""
from pathlib import Path
import sys


def once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"V13 load audit {label}: expected 1 anchor, found {count}")
    return source.replace(old, new, 1)


def patch_main(s: str) -> str:
    s = once(s,
        '    R11GameCheckpoint("launch begin",game.path.c_str(),true);\n'
        '    LOG_INFO(Frontend, "Launching {}", game.path);',
        '    R11GameCheckpoint("launch begin",game.path.c_str(),true);\n'
        '    // USB drives can disappear between indexing the library and launching.\n'
        '    // Reject invalid/unreadable paths early rather than showing endless Loading.\n'
        '    struct stat r13_file_info{};\n'
        '    if (stat(game.path.c_str(), &r13_file_info) != 0 ||\n'
        '        !S_ISREG(r13_file_info.st_mode) || r13_file_info.st_size <= 0) {\n'
        '        R11GameCheckpoint("arquivo do jogo ausente, vazio ou inacessivel");\n'
        '        throw std::runtime_error{"Arquivo do jogo ausente ou inacessivel. Verifique o HD USB."};\n'
        '    }\n'
        '    LOG_INFO(Frontend, "Launching {}", game.path);',
        "check file accessibility before loader")
    s = once(s,
        '    LOG_INFO(Frontend, "PS4 options: {}", OptionsSummary());\n'
        '    Common::PS4Diagnostics::Reset();',
        '    LOG_INFO(Frontend, "PS4 options: {}", OptionsSummary());\n'
        '    // The normal hang watchdog starts only *after* system.Run(). Observe\n'
        '    // system.Initialize(), system.Load() and GPU.Start() as well.\n'
        '    std::atomic<bool> r13_load_audit_stop{false};\n'
        '    std::atomic<int> r13_load_audit_phase{1};\n'
        '    std::thread r13_load_audit([&] {\n'
        '        int seconds = 0;\n'
        '        while (!r13_load_audit_stop.load(std::memory_order_relaxed)) {\n'
        '            std::this_thread::sleep_for(std::chrono::seconds{1});\n'
        '            if (r13_load_audit_stop.load(std::memory_order_relaxed)) break;\n'
        '            if (++seconds % 30 == 0) {\n'
        '                const char* phase = "inicializacao do sistema";\n'
        '                switch (r13_load_audit_phase.load(std::memory_order_relaxed)) {\n'
        '                    case 2: phase = "abertura do container"; break;\n'
        '                    case 3: phase = "inicializacao Vulkan"; break;\n'
        '                    case 4: phase = "execucao inicial"; break;\n'
        '                    default: break;\n'
        '                }\n'
        '                R11GameCheckpoint("carregamento acima de 30 s", phase);\n'
        '            }\n'
        '        }\n'
        '    });\n'
        '    // Safe even if the loader throws before normal emulation begins.\n'
        '    SCOPE_EXIT {\n'
        '        r13_load_audit_stop.store(true, std::memory_order_relaxed);\n'
        '        if (r13_load_audit.joinable()) r13_load_audit.join();\n'
        '    };\n'
        '    Common::PS4Diagnostics::Reset();',
        "early load watchdog")
    s = once(s,
        '    R11GameCheckpoint("begin container load");\n'
        '    const auto result = system.Load(window, game.path, parameters);\n'
        '    R11GameCheckpoint("container load returned");',
        '    r13_load_audit_phase.store(2, std::memory_order_relaxed);\n'
        '    const auto r13_load_start = std::chrono::steady_clock::now();\n'
        '    R11GameCheckpoint("begin container load");\n'
        '    const auto result = system.Load(window, game.path, parameters);\n'
        '    const auto r13_load_ms = std::chrono::duration_cast<std::chrono::milliseconds>(\n'
        '        std::chrono::steady_clock::now() - r13_load_start).count();\n'
        '    const auto r13_load_duration = std::to_string(r13_load_ms) + " ms";\n'
        '    R11GameCheckpoint("container load returned", r13_load_duration.c_str());',
        "timed loader")
    s = once(s,
        '    R11GameCheckpoint("container accepted; starting GPU");',
        '    r13_load_audit_phase.store(3, std::memory_order_relaxed);\n'
        '    R11GameCheckpoint("container accepted; starting GPU");',
        "gpu stage")
    s = once(s,
        '    R11GameCheckpoint("guest CPU ready; entering game");',
        '    r13_load_audit_phase.store(4, std::memory_order_relaxed);\n'
        '    R11GameCheckpoint("guest CPU ready; entering game");',
        "guest cpu stage")
    s = once(s,
        '    R11GameCheckpoint("guest emulation running");',
        '    R11GameCheckpoint("guest emulation running");\n'
        '    r13_load_audit_stop.store(true, std::memory_order_relaxed);\n'
        '    if (r13_load_audit.joinable()) r13_load_audit.join();',
        "stop early probe once gameplay loop starts")
    s = once(s,
        '        const bool keys = stat("/data/EdenPS4/keys/prod.keys", &status) == 0;',
        '        const bool keys = stat("/data/EdenPS4/keys/prod.keys", &status) == 0 &&\n'
        '                          S_ISREG(status.st_mode) && status.st_size > 0;',
        "keys existence not validity")
    s = once(s,
        '{"Chaves", keys ? "Prontas" : "Ausentes"},\n'
        '            {"Firmware", firmware ? "Instalado" : "Ausente"},',
        '{"Chaves", keys ? "Arquivo presente (nao validado)" : "Ausentes"},\n'
        '            {"Firmware", firmware ? "Dados presentes (nao verificados)" : "Nao detectado"},',
        "no false ready/installed states")
    return s


def patch_ui(s: str) -> str:
    return once(s,
        'TextBlock(x, "Escolha uma pasta do HD para localizar NSP, XCI, NRO e NSO. "\n'
        '                     "A busca inclui subpastas. Chaves e firmware precisam ser configurados separadamente.",',
        'TextBlock(x, "Jogos NSP, XCI, NRO e NSO sao indexados no HD. "\n'
        '                     "Importacao de firmware, chaves e atualizacoes ainda nao esta disponivel nesta V13.",',
        "accurate import capability explanation")


def patch(root: Path):
    main = root / "eden/src/yuzu_ps4/main.cpp"
    ui = root / "eden/src/yuzu_ps4/ui_launcher.cpp"
    original_main = main.read_text(encoding="utf-8")
    original_ui = ui.read_text(encoding="utf-8")
    revised_main = patch_main(original_main)
    revised_ui = patch_ui(original_ui)
    # Verify all anchors before changing either file.
    main.write_text(revised_main, encoding="utf-8")
    ui.write_text(revised_ui, encoding="utf-8")
    print("V13: inaccessible game fast-fail, early load audit and honest firmware status")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: patch-v13-loading-firmware-audit.py <checkout Eden4>")
    patch(Path(sys.argv[1]).resolve())
