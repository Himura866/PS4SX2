#!/usr/bin/env python3
"""R13: actual persistent FPS overlay toggle and HOME clock removal.

Apply last on the disposable pinned Eden4 checkout after R13 PT-BR.
Never confuse the HOME wall clock with the Vulkan game FPS overlay.
"""
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    hits = text.count(old)
    if hits != 1:
        raise RuntimeError(f"R13 FPS/clock {label}: expected exactly 1 anchor, got {hits}")
    return text.replace(old, new, 1)


def patch_files(root: Path) -> None:
    main = root / "eden/src/yuzu_ps4/main.cpp"
    ui = root / "eden/src/yuzu_ps4/ui_launcher.cpp"
    diagnostics = root / "eden/src/common/ps4_diagnostics.h"
    present = root / "eden/src/video_core/renderer_vulkan/vk_present_manager.cpp"

    sources = [p.read_text(encoding="utf-8") for p in (main, ui, diagnostics, present)]
    m, u, d, p = sources

    # REAL setting. PsHost.SetOption already applies and saves all g_options
    # to /data/EdenPS4/ps4.ini. Default ON preserves older R13 behaviour.
    m = replace_once(
        m,
        '    {"profile", "Analise de desempenho",',
        '    {"fps_overlay", "Mostrar FPS",'
        ' "Exibe ou oculta o contador REAL de quadros dos jogos. Vale a partir do proximo jogo.",'
        ' "display", {{"on", "On"}, {"off", "Off"}}},\n'
        '    {"profile", "Analise de desempenho",',
        "fps option in existing g_options list",
    )
    m = replace_once(
        m,
        '    Common::PS4Diagnostics::profiler = enabled("profile");',
        '    Common::PS4Diagnostics::r13_fps_overlay_enabled.store('
        'enabled("fps_overlay"), std::memory_order_relaxed);\n'
        '    Common::PS4Diagnostics::profiler = enabled("profile");',
        "apply FPS option to native Vulkan overlay",
    )
    d = replace_once(
        d,
        'inline std::atomic<int> r11_game_fps_tenths{0};',
        'inline std::atomic<int> r11_game_fps_tenths{0};\n'
        '// Read by the in-game Vulkan present path; not reset between games.\n'
        'inline std::atomic<bool> r13_fps_overlay_enabled{true};',
        "atomic state",
    )
    p = replace_once(
        p,
        '    if (frame->fps_mapped && extent.width > R11FpsW+32 && extent.height > R11FpsH+32) {',
        '    if (Common::PS4Diagnostics::r13_fps_overlay_enabled.load(std::memory_order_relaxed) &&\n'
        '        frame->fps_mapped && extent.width > R11FpsW+32 && extent.height > R11FpsH+32) {',
        "real draw gate",
    )
    u = replace_once(
        u,
        '        canvas.Text(host.Clock(), 1840, 220, 30, p.text, Align::Right);',
        '        // R13: no HOME clock. In-game FPS remains independently configurable.',
        "remove HOME clock, not FPS",
    )

    # Validate every edit before touching even one on-disk file.
    assert m.count('"fps_overlay"') == 2, "unexpected FPS setting wiring"
    assert "r13_fps_overlay_enabled" in d and "r13_fps_overlay_enabled" in p
    assert "canvas.Text(host.Clock()" not in u, "HOME clock still rendered"
    for path, content in zip((main, ui, diagnostics, present), (m, u, d, p)):
        path.write_text(content, encoding="utf-8")
    print("R13: FPS setting persists in ps4.ini; Vulkan overlay obeys it; HOME clock removed")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r13-fps-toggle-no-clock.py <Eden4 checkout>")
    patch_files(Path(sys.argv[1]).resolve())
