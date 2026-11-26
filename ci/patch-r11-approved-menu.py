#!/usr/bin/env python3
"""R11: draw actual approved Samurai library picture behind LIVE widgets.

The approved image serves as decorative reference ONLY. Real games, covers,
navigation, actions and focus are drawn by the existing C++ launcher on top,
never by treating the static picture as clickable buttons.

The original geometric background remains a fallback for missing/corrupt skin.
"""
from pathlib import Path
import sys

def once(s,old,new,tag):
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f"R11 approved menu {tag}: expected one anchor; found {count}")
    return s.replace(old,new,1)

R11_SKIN_SOURCE=r'''
    // Native 1920x1080 skin packaged under /app0. Decode ONCE at HOME's
    // cached-backdrop construction. It is never re-decoded during game scrolling.
    const char* skin_path = "/app0/skin/himura-r11-menu.png";
    if (std::FILE* fp = std::fopen(skin_path, "rb")) {
        const bool seek_ok = std::fseek(fp, 0, SEEK_END) == 0;
        const long n = seek_ok ? std::ftell(fp) : -1;
        if (n > 0 && n <= (16 * 1024 * 1024) &&
            std::fseek(fp, 0, SEEK_SET) == 0) {
            std::vector<uint8_t> data(static_cast<size_t>(n));
            if (std::fread(data.data(), 1, data.size(), fp) == data.size()) {
                Image picture = DecodeImage(data, Canvas::Width, Canvas::Height);
                if (!picture.Empty()) {
                    std::fclose(fp);
                    c.DrawImage(picture, 0, 0);
                    // The approved picture contains MOCK game covers, arrows, dots
                    // and six printed buttons. Hide those inert example controls;
                    // the actual PS4 library draws real games, cursor and buttons
                    // on top of these opaque panels on EVERY interactive frame.
                    c.FillRoundRect(94, 434, 1732, 406, 18, {0x090e1b}, 0.98f);
                    c.StrokeRoundRect(94, 434, 1732, 406, 18, 2, {0x9a1e35}, 0.55f);
                    c.FillRect(0, 485, 105, 190, {0x090e1b}, 0.96f);
                    c.FillRect(1815, 485, 105, 190, {0x090e1b}, 0.96f);
                    c.FillRoundRect(964, 28, 930, 150, 15, {0x090d19}, 0.98f);
                    // Footer hints are actual LIVE controls, not baked screenshot.
                    c.FillRect(0, 970, Canvas::Width, 110, {0x070911}, 0.95f);
                    c.HLine(0, Canvas::Width, 969, 3, {0xd52236}, 0.85f);
                    c.Text("POD DO HIMURA", 1820, 200, 20, {0xf8dfdf}, Align::Right);
                    return;
                }
            }
        }
        std::fclose(fp);
    }
    // Fallback: keep original R11 geometric menu if the skin file is missing.
'''

def patch(root: Path):
    launcher=root/"eden/src/yuzu_ps4/ui_launcher.cpp"
    build=root/"eden/ps4/build.sh"
    s=launcher.read_text(encoding="utf8")
    b=build.read_text(encoding="utf8")
    s=once(s,'#include <algorithm>\n','#include <algorithm>\n#include <cstdio>\n',"stdio")
    s=once(s,
        'void DrawR11Backdrop(Canvas& c) {\n',
        'void DrawR11Backdrop(Canvas& c) {\n'+R11_SKIN_SOURCE,
        "real approved menu skin")
    s=once(s,
        'constexpr float TileStep = 336, TileSize = 302, TileTop = 393, StripLeft = 128.0f;',
        'constexpr float TileStep = 327, TileSize = 310, TileTop = 450, StripLeft = 145.0f;',
        "actual template cover coordinates")
    s=once(s,
        'canvas.PushClip(0, 366, Canvas::Width, 382);',
        'canvas.PushClip(0, 434, Canvas::Width, 410);',
        "cover region clip")
    s=once(s,
        'canvas.Text(title, left + (canvas.Measure(title, 32) < w ? (w - canvas.Measure(title, 32)) / 2 : 0), 757, 32,',
        'canvas.Text(title, left + (canvas.Measure(title, 32) < w ? (w - canvas.Measure(title, 32)) / 2 : 0), 817, 32,',
        "real game title below cover row")
    s=once(s,
        'constexpr float barLeft = 703.0f, barTop = 42.0f;\n'
        '        constexpr float barStep = 177.0f, barWidth = 158.0f, barHeight = 118.0f;',
        'constexpr float barLeft = 971.0f, barTop = 46.0f;\n'
        '        constexpr float barStep = 146.0f, barWidth = 135.0f, barHeight = 116.0f;',
        "functional toolbar aligned with approved picture")
    s=once(s,
        '        canvas.Text("Biblioteca de Jogos", 960, 266, 40, p.title, Align::Center);\n'
        '        canvas.Text("Selecione um jogo para comecar", 960, 315, 26, p.copy, Align::Center);\n',
        '',"avoid double printing fixed title over approved artwork")
    # Real cards are ALWAYS opaque on the snapshot. Prevent the five fake
    # decorative example covers in the screenshot from showing as playable games.
    anchor='            const bool focused = st.zone == Zone::Games && st.game_focus == i;\n'
    s=once(s,anchor,anchor+
        '            canvas.FillRoundRect(left - 5, TileTop - 5, TileSize + 10, TileSize + 10,\n'
        '                                 13, {0x080b16}); // hide illustrative sample covers\n',
        "overwrite static example game pictures")
    # The existing Canvas::Render code retains launch and navigation branches.
    for a in ('R11NeonCover(canvas','case 5: st.modal = Modal::Power;',
              'else start(st.game_focus);'):
        if a not in s: raise RuntimeError("R11 approved menu missing live feature "+a)
    b=once(b,
        'cp "$REPO/branding/HIMURA-ATTRIBUTION.txt" "$STAGE/licenses/HIMURA-ATTRIBUTION.txt"',
        'cp "$REPO/branding/HIMURA-ATTRIBUTION.txt" "$STAGE/licenses/HIMURA-ATTRIBUTION.txt"\n'
        '# Real, approved 1080p background for the dynamic PS4 game library.\n'
        'mkdir -p "$STAGE/skin"\n'
        'cp "$REPO/branding/himura-r11-menu.png" "$STAGE/skin/himura-r11-menu.png"',
        "PS4 PKG skin stage")
    launcher.write_text(s,encoding="utf8")
    build.write_text(b,encoding="utf8")
    print("R11: exact approved menu art layered under live controls and staged to PS4 PKG")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch-r11-approved-menu.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
