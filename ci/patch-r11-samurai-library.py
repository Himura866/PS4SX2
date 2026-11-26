#!/usr/bin/env python3
"""HIMURA SWITCH PS4 R11 - samurai library on the disposable Eden4 checkout.

Keeps R10 input, launch actions, sources, and diagnostics. No fake cover images:
the game carousel and toolbar are still rendered by the live launcher.
"""
from pathlib import Path
import sys

def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise RuntimeError(f"R11 {label}: expected one anchor, found {n}")
    return s.replace(old, new, 1)

BACKGROUND = r"""
// R11: inexpensive, original geometric Japanese-inspired scenery. Everything here
// is drawn behind the live launcher widgets (never a screenshot of fake games).
void DrawR11Backdrop(Canvas& c) {
    for (int y = 0; y < Canvas::Height; y += 12) {
        const float t = float(y) / Canvas::Height;
        const int red = int(10 + 24 * t);
        const int green = int(11 + 2 * t);
        const int blue = int(22 + 4 * (1.0f - t));
        c.FillRect(0, y, Canvas::Width, 12,
                   {uint32_t((red << 16) | (green << 8) | blue)});
    }
    // Red moon with a low-cost three-ring halo.
    c.FillCircle(1560, 285, 260, {0x780b17}, 0.22f);
    c.FillCircle(1560, 285, 215, {0xca1426}, 0.30f);
    c.FillCircle(1560, 285, 170, {0xd31829}, 0.73f);
    // Snow-capped mountain on the right, built as horizontal ribbons.
    for (int i = 0; i < 52; ++i) {
        const float y = 218 + i * 6.0f, half = i * 7.2f;
        const Color mountain = i < 18 ? Color{0xcfd8e6} : Color{0x292f40};
        c.FillRect(1600 - half, y, half * 2, 6.5f, mountain,
                   i < 18 ? 0.81f : 0.75f);
    }
    // Abstract samurai shadow, at left. Helmet, mask, shoulder guard and sword.
    c.FillCircle(183, 298, 120, {0x0a0e18}, 0.96f);
    c.FillRoundRect(126, 243, 127, 110, 35, {0x11141c});
    c.FillRoundRect(95, 225, 176, 30, 11, {0x070a11});
    c.FillRoundRect(155, 171, 56, 95, 17, {0x090c15});
    c.HLine(106, 278, 260, 5, {0xc52337}, 0.83f);
    c.FillCircle(112, 415, 115, {0x130d16});
    c.FillCircle(263, 423, 110, {0x100e18});
    for (int k = 0; k < 7; ++k) {
        c.HLine(70, 302, 339 + k * 17, 2, {0xbd202e}, 0.27f);
    }
    c.HLine(70, 412, 518, 4, {0xee303e}, 0.68f);
    c.HLine(105, 420, 525, 2, {0xff8d94}, 0.35f);
    // Torii silhouette and red wind strokes at the bottom right.
    c.FillRect(1546, 833, 21, 116, {0x090b12});
    c.FillRect(1762, 833, 21, 116, {0x090b12});
    c.FillRect(1515, 809, 300, 20, {0x170c12});
    c.FillRect(1494, 796, 340, 11, {0xac1727}, 0.84f);
    c.FillRect(1573, 866, 180, 12, {0x200e15});
    for (int i = 0; i < 13; ++i) {
        const float y = 853 + i * 12.0f;
        c.HLine(0, 490 + i * 24, y, 2, {0xe71a2b}, 0.30f);
    }
    // The game tiles stay readable while texture remains visible at their edges.
    c.Text("HIMURA", 70, 93, 40, {0xf5f6fb});
    c.Text("SWITCH PS4  |  R13", 73, 135, 28, {0xff3b4d});
    // Personalisation label visible in the live HOME and its UI preview.
    c.Text("POD DO HIMURA", 73, 172, 21, {0xf2cbd2});
}

// Lightweight focus neon: red/blue ring + a moving highlight around one game.
// The original Cross/Options game actions and carousel physics stay unchanged.
void R11NeonCover(Canvas& c, float left, float top, float size, float time) {
    const float pulse = 0.72f + 0.28f * std::sin(time * 4.7f);
    c.StrokeRoundRect(left - 9, top - 9, size + 18, size + 18, 14, 7, {0xe51c44}, 0.20f * pulse);
    c.StrokeRoundRect(left - 5, top - 5, size + 10, size + 10, 12, 3, {0xff3e60}, 0.90f);
    c.StrokeRoundRect(left - 2, top - 2, size + 4, size + 4, 9, 1.5f, {0xff8795}, 0.8f);
    const float edge = std::fmod(std::max(0.0f, time) * 220.0f, 4.0f * size);
    const float glow = 46.0f;
    if (edge < size) {
        c.HLine(left + edge, left + std::min(size, edge + glow), top - 5, 5, {0xff5269}, 0.98f);
    } else if (edge < 2.0f * size) {
        const float y = edge - size;
        c.VLine(left + size + 5, top + y, top + std::min(size, y + glow), 5, {0xff5269}, 0.98f);
    } else if (edge < 3.0f * size) {
        const float x = edge - 2.0f * size;
        c.HLine(left + size - std::min(size,x + glow), left + size - x, top + size + 5, 5, {0xff5269}, 0.98f);
    } else {
        const float y = edge - 3.0f * size;
        c.VLine(left - 5, top + size - std::min(size,y + glow), top + size - y, 5, {0xff5269}, 0.98f);
    }
}
"""

def patch_source(s):
    s = once(s,
        """constexpr Palette Dark{{0x2d2d2d}, {0xf5f5f5}, {0xffffff}, {0xcfcfcf}, {0xbdbdbd}, {0x555555},
                       {0x414141}, {0x30d5c8}, {0x505050}, {0xffb36a}, {0x383838}, {0x000000}};""",
        """constexpr Palette Dark{{0x140d17}, {0xf5f5f7}, {0xffffff}, {0xd4d5de}, {0xa6aaba}, {0x632b3e},
                       {0x161a28}, {0xff3b4d}, {0x111a2b}, {0xffbd75}, {0x10131e}, {0x000000}};""", "palette")
    s = once(s,
        'constexpr float TileStep = 405, TileSize = 384, TileTop = 291, StripLeft = 160.5f;',
        'constexpr float TileStep = 336, TileSize = 302, TileTop = 393, StripLeft = 128.0f;', "five real tiles")
    s = once(s,
        'const char* const ShortcutNames[] = {"About", "Game Files", "Users", "Controllers", "System Settings", "Power"};',
        'const char* const ShortcutNames[] = {"Sobre", "Jogos", "Usuarios", "Controles", "Ajustes", "Sair"};', "labels")
    s = once(s, 'struct Ctx {\n', BACKGROUND + '\nstruct Ctx {\n', "static background")
    s = once(s,
        '    canvas.Clear(p.base);\n    const auto& games = host.Games();',
        '    canvas.Clear(p.base);\n'
        '    if (!white && (st.screen == Screen::Home || st.screen == Screen::Library)) DrawR11Backdrop(canvas);\n'
        '    const auto& games = host.Games();', "background on HOME and Library")
    s = once(s,
        '            const float cx = 136.5f + i * 90, cy = 98;',
        '            const float cx = 130.5f + i * 90, cy = 212;', "user avatars")
    s = once(s,
        'if (i == host.CurrentUser()) canvas.FillRoundRect(cx - 20, 144, 40, 4, 2, p.accent);',
        'if (i == host.CurrentUser()) canvas.FillRoundRect(cx - 20, 258, 40, 4, 2, p.accent);',
        "active profile")
    s = once(s,
        'canvas.Text(users[i].name, cx, 192, 28, p.accent, Align::Center, 300);',
        'canvas.Text(users[i].name, cx, 303, 28, p.accent, Align::Center, 300);',
        "profile label")
    s = once(s,
        'canvas.Text(host.Clock(), 1860, 115.5f, 30, p.text, Align::Right);',
        'canvas.Text(host.Clock(), 1840, 220, 30, p.text, Align::Right);',
        "clock")
    s = once(s,
        '        const int shown = std::min<int>(games.size(), HomeSlots);',
        '        canvas.Text("Biblioteca de Jogos", 960, 266, 40, p.title, Align::Center);\n'
        '        canvas.Text("Selecione um jogo para comecar", 960, 315, 26, p.copy, Align::Center);\n'
        '        const int shown = std::min<int>(games.size(), HomeSlots);',
        "home heading")
    s = once(s,
        'const float tile_x = StripLeft + st.game_focus * TileStep - st.strip;\n'
        '            const float left = std::clamp(tile_x + 192 - w / 2, 112.0f, 1808.0f - w);',
        'const float tile_x = StripLeft + st.game_focus * TileStep - st.strip;\n'
        '            const float left = std::clamp(tile_x + TileSize / 2 - w / 2, 112.0f, 1808.0f - w);',
        "selected title location")
    s = once(s,
        'canvas.Text(title, left + (canvas.Measure(title, 32) < w ? (w - canvas.Measure(title, 32)) / 2 : 0), 258, 32,',
        'canvas.Text(title, left + (canvas.Measure(title, 32) < w ? (w - canvas.Measure(title, 32)) / 2 : 0), 757, 32,',
        "selected title baseline")
    s = once(s,
        'canvas.Text(host.Scanning() ? "Looking for software..." : "Add software in Game Files.", 160.5f, 258, 30, p.copy);',
        'canvas.Text(host.Scanning() ? "Procurando jogos..." : "Adicione seus jogos em Jogos.", 960, 755, 30, p.copy, Align::Center);',
        "empty state")
    s = once(s,
        'canvas.PushClip(0, 270, Canvas::Width, 440);',
        'canvas.PushClip(0, 366, Canvas::Width, 382);',
        "cover clip")
    s = once(s, 'canvas.CircleShadow(left + 192, 483, 120);',
             'canvas.CircleShadow(left + TileSize / 2, TileTop + TileSize / 2, 100);', "all games tile shadow")
    s = once(s, 'if (focused) FocusCircle(x, left + 192, 483, 120);',
             'if (focused) FocusCircle(x, left + TileSize / 2, TileTop + TileSize / 2, 100);', "all games tile focus")
    s = once(s, 'canvas.FillCircle(left + 192, 483, 120, p.shortcut);',
             'canvas.FillCircle(left + TileSize / 2, TileTop + TileSize / 2, 100, p.shortcut);', "all games tile bg")
    s = once(s, 'canvas.MaskCentered("grid", left + 192, 483, p.title);',
             'canvas.MaskCentered("grid", left + TileSize / 2, TileTop + TileSize / 2, p.title);', "all games grid")
    s = once(s,
        'constexpr float barLeft = 510.0f, barTop = 52.0f;\n'
        '        constexpr float barStep = 184.0f, barWidth = 164.0f, barHeight = 120.0f;',
        'constexpr float barLeft = 703.0f, barTop = 42.0f;\n'
        '        constexpr float barStep = 177.0f, barWidth = 158.0f, barHeight = 118.0f;',
        "toolbar beside HIMURA logo")
    s = once(s,
        'if (focused) FocusRect(x, left, TileTop, TileSize, TileSize);',
        'if (focused) R11NeonCover(canvas, left, TileTop, TileSize, st.time);',
        "selected game neon")
    s = once(s,
        '// No icon (homebrew, or not read yet): the title on a plain tile.',
        '// No cached icon: show the actual game title without inventing a game cover.',
        "placeholder policy")
    s = once(s,
        'st.strip_target = std::clamp((st.game_focus - 3) * TileStep, 0.0f, std::max(0, tiles - 4) * TileStep);',
        'st.strip_target = std::clamp((st.game_focus - 4) * TileStep, 0.0f, std::max(0, tiles - 5) * TileStep);',
        "five game slots before scrolling")
    # Visual checks: no interaction branch or launch path changed.
    for action in ('st.about_return = Screen::Home; open(Screen::About);',
                   'case 1: st.file_row = 0; open(Screen::Files);',
                   'case 4: st.category = 0; open(Screen::Settings);',
                   'case 5: st.modal = Modal::Power;',
                   'else start(st.game_focus);'):
        if action not in s:
            raise RuntimeError(f"R11 missing live action: {action}")
    return s

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r11-samurai-library.py <pinned Eden4 checkout>")
    file = Path(sys.argv[1]).resolve() / "eden/src/yuzu_ps4/ui_launcher.cpp"
    if not file.is_file():
        raise RuntimeError("R11: missing Eden4 HOME launcher")
    original = file.read_text(encoding="utf-8")
    rendered = patch_source(original)
    file.write_text(rendered, encoding="utf-8")
    print("R11: samurai theme, live top toolbar, larger library and original geometry added")

if __name__ == "__main__":
    main()
