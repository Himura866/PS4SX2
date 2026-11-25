#!/usr/bin/env python3
"""R10: move real HOME shortcuts into a compact, navigable Switch-style top toolbar.

Patches only the disposable, pinned Eden4 checkout built by CircleCI.
R09/R08 sources and artifacts remain untouched.
"""
from pathlib import Path
import sys

def replace_once(text, old, new, name):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"R10 {name}: expected one source anchor, got {count}")
    return text.replace(old, new, 1)

NAV_OLD = """        if (pressed & Up) {
            if (st.zone == Zone::Shortcuts && tiles > 0) st.zone = Zone::Games;
            else if (st.zone == Zone::Shortcuts || st.zone == Zone::Games) {
                st.zone = Zone::Users;
                st.user_focus = std::clamp(host.CurrentUser(), 0, std::max(0, users - 1));
            } else { host.Play(Sound::Limit); break; }
            host.Play(Sound::Focus);
        }
        if (pressed & Down) {
            if (st.zone == Zone::Users) st.zone = tiles > 0 ? Zone::Games : Zone::Shortcuts;
            else if (st.zone == Zone::Games) st.zone = Zone::Shortcuts;
            else { host.Play(Sound::Limit); break; }
            host.Play(Sound::Focus);
        }
"""

NAV_NEW = """        // R10 top-to-bottom navigation: users > top toolbar > game covers.
        if (pressed & Up) {
            if (st.zone == Zone::Games) st.zone = Zone::Shortcuts;
            else if (st.zone == Zone::Shortcuts) {
                st.zone = Zone::Users;
                st.user_focus = std::clamp(host.CurrentUser(), 0, std::max(0, users - 1));
            } else { host.Play(Sound::Limit); break; }
            host.Play(Sound::Focus);
        }
        if (pressed & Down) {
            if (st.zone == Zone::Users) st.zone = Zone::Shortcuts;
            else if (st.zone == Zone::Shortcuts && tiles > 0) st.zone = Zone::Games;
            else { host.Play(Sound::Limit); break; }
            host.Play(Sound::Focus);
        }
"""

TOOLBAR = """        // R10: premium but lightweight top toolbar; all six controls retain live actions.
        // Keep the game-cover carousel in its original Switch-like position and size.
        const Color inks[] = {{0xff4d4d}, {0xffae2e}, {0x4a9bdb}, p.title, p.title, p.title};
        constexpr float barLeft = 510.0f, barTop = 52.0f;
        constexpr float barStep = 184.0f, barWidth = 164.0f, barHeight = 120.0f;
        for (int i = 0; i < 6; ++i) {
            const float left = barLeft + i * barStep;
            const float center = left + barWidth * 0.5f;
            const bool focused = st.zone == Zone::Shortcuts && st.shortcut_focus == i;
            canvas.Shadow(left, barTop + 2, barWidth, barHeight, 0.23f);
            canvas.FillRoundRect(left, barTop, barWidth, barHeight, 18, focused ? p.row : p.shortcut);
            canvas.StrokeRoundRect(left, barTop, barWidth, barHeight, 18,
                                   focused ? 3.0f : 1.2f, focused ? p.accent : p.line,
                                   focused ? 1.0f : 0.50f);
            if (focused) FocusRect(x, left, barTop, barWidth, barHeight);
            canvas.MaskCentered(ShortcutIcons[i], center, barTop + 49, focused ? p.accent : inks[i]);
            canvas.Text(ShortcutNames[i], center, barTop + 109, 19,
                        focused ? p.accent : p.text, Align::Center, barWidth - 12);
        }
"""

def patch_launcher(source):
    source = replace_once(source, NAV_OLD, NAV_NEW, "navigation")
    start = "        // Shortcut buttons.\n"
    end = "        if (!st.message.empty()) canvas.Text(st.message,"
    if source.count(start) != 1 or source.count(end) != 1:
        raise RuntimeError("R10 toolbar: changed upstream render anchors")
    a = source.index(start)
    z = source.index(end, a)
    source = source[:a] + TOOLBAR + source[z:]
    # Verify that the replacement left all shortcut actions intact.
    for action in ("case 0: open(Screen::About);",
                   "case 1: st.file_row = 0; open(Screen::Files);",
                   "case 3: st.controllers_row = 0; open(Screen::Controllers);",
                   "case 4: st.category = 0; open(Screen::Settings);",
                   "case 5: st.modal = Modal::Power;"):
        if action not in source:
            raise RuntimeError(f"R10 missing live shortcut action: {action}")
    return source

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r10-switch-toolbar.py <pinned Eden4 checkout>")
    root = Path(sys.argv[1]).resolve()
    launcher = root / "eden/src/yuzu_ps4/ui_launcher.cpp"
    preview = root / "eden/ps4/ui-preview/preview.cpp"
    if not launcher.is_file() or not preview.is_file():
        raise RuntimeError("R10: missing Eden4 launcher or preview sources")
    original = launcher.read_text(encoding="utf-8")
    rendered = patch_launcher(original)
    pv = preview.read_text(encoding="utf-8")
    pv = replace_once(
        pv,
        '    shot("home_shortcuts", {Down, Right, Right, Right});',
        '    shot("home_shortcuts", {Up, Right, Right, Right});\n'
        '    shot("home_r10_toolbar", {Up, Right, Right});',
        "host preview toolbar navigation",
    )
    # Do not write either file until both preflight patches pass.
    launcher.write_text(rendered, encoding="utf-8")
    preview.write_text(pv, encoding="utf-8")
    print("R10: functional HOME top toolbar, controller flow and preview integrated")

if __name__ == "__main__":
    main()
