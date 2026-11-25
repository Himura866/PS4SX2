#!/usr/bin/env python3
"""R11 performance: cache only the static 1920x1080 samurai menu background.

The real launcher, animated neon selection, scrolling carousel and live buttons
remain drawn every frame. One additional 7.9 MiB CPU-side canvas saves repeated
full-screen gradient and shape rasterisation. No GPU/guest emulation changes.
Applies after ci/patch-r11-samurai-library.py in the disposable Eden4 checkout.
"""
from pathlib import Path
import sys

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"R11 theme cache: {label} expected once, found {count}")
    return text.replace(old, new, 1)

def patch(root: Path):
    header = root / "eden/src/yuzu_ps4/ui_canvas.h"
    impl = root / "eden/src/yuzu_ps4/ui_canvas.cpp"
    launcher = root / "eden/src/yuzu_ps4/ui_launcher.cpp"
    if not all(path.is_file() for path in (header, impl, launcher)):
        raise RuntimeError("R11 theme cache: incomplete pinned Eden4 checkout")

    h = header.read_text(encoding="utf8")
    cpp = impl.read_text(encoding="utf8")
    ui = launcher.read_text(encoding="utf8")

    h = once(h,
        '    void Clear(Color color);\n',
        '    void Clear(Color color);\n'
        '    /// Restore a previously rendered opaque full-screen background.\n'
        '    /// Does not alter the clip stack or input state.\n'
        '    void CopyOpaque(const Canvas& source);\n',
        "Canvas API")
    cpp = once(cpp,
        'void Canvas::Clear(Color color) {\n'
        '    std::fill(pixels.begin(), pixels.end(), Pack(color));\n'
        '}\n',
        'void Canvas::Clear(Color color) {\n'
        '    std::fill(pixels.begin(), pixels.end(), Pack(color));\n'
        '}\n'
        '\nvoid Canvas::CopyOpaque(const Canvas& source) {\n'
        '    // Canvas dimensions are fixed, and all pixels have an opaque alpha.\n'
        '    std::memcpy(pixels.data(), source.pixels.data(),\n'
        '                pixels.size() * sizeof(uint32_t));\n'
        '}\n',
        "Canvas copy")

    ui = once(ui,
        '    canvas.Clear(p.base);\n'
        '    if (!white && (st.screen == Screen::Home || st.screen == Screen::Library)) DrawR11Backdrop(canvas);\n'
        '    const auto& games = host.Games();',
        '    // R11: rasterise the static theme once; copying 8 MiB is cheaper than\n'
        '    // painting 90+ full-screen gradients/shapes on every navigation frame.\n'
        '    // Live controls, neon, scrolling, text and game covers still draw below.\n'
        '    if (!white && (st.screen == Screen::Home || st.screen == Screen::Library)) {\n'
        '        static Canvas cached_background;\n'
        '        static bool background_ready = false;\n'
        '        if (!background_ready) {\n'
        '            cached_background.Clear(p.base);\n'
        '            DrawR11Backdrop(cached_background);\n'
        '            background_ready = true;\n'
        '        }\n'
        '        canvas.CopyOpaque(cached_background);\n'
        '    } else {\n'
        '        canvas.Clear(p.base);\n'
        '    }\n'
        '    const auto& games = host.Games();',
        "render background")

    for anchor in ("R11NeonCover(canvas", "const auto& games = host.Games();",
                   "case 5: st.modal = Modal::Power;",
                   "DrawR11Backdrop(cached_background);"):
        if anchor not in ui:
            raise RuntimeError(f"R11 theme cache: missing live UI checkpoint {anchor}")

    # Only write once every related target passed its own preflight.
    header.write_text(h, encoding="utf8")
    impl.write_text(cpp, encoding="utf8")
    launcher.write_text(ui, encoding="utf8")
    print("R11 theme background: rasterised once, cached; all live UI retained")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r11-theme-cache.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
