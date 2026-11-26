#!/usr/bin/env python3
"""R14: non-destructive HIMURA UI port onto pinned Orbis Eden (GPL-3.0-or-later).
The emulation core, JIT, memory subsystem, Vulkan drivers and patches are unchanged.
"""
from pathlib import Path
import sys

def one(s, a, b, label):
    if s.count(a) != 1:
        raise RuntimeError(f"R14 {label}: upstream anchor not unique ({s.count(a)})")
    return s.replace(a, b, 1)

BACKGROUND = r'''
// A raw, validated copy of the owner's R13 samurai image (1920x1080 BGRA).
// Loading once avoids decoding pictures on PS4 while the controller scrolls.
std::vector<uint32_t> r14_background;
bool r14_background_attempted = false;
void R14Background(Canvas& canvas) {
    if (!r14_background_attempted) {
        r14_background_attempted = true;
        if (FILE* f = std::fopen("/app0/skin/himura-r14-menu.bgra", "rb")) {
            r14_background.resize(size_t(Width) * Height);
            if (std::fread(r14_background.data(), 4, r14_background.size(), f) !=
                r14_background.size()) {
                r14_background.clear();
                Ps4::Log("R14: damaged menu image, fallback active");
            }
            std::fclose(f);
        }
    }
    if (!r14_background.empty()) {
        std::copy(r14_background.begin(), r14_background.end(), canvas.pixels);
    } else {
        canvas.Fill(0, 0, Width, Height, 0xFF141821);
    }
}
void R14ReleaseBackground() {
    std::vector<uint32_t>().swap(r14_background);
}
'''

DRAW = r'''void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected) {
    constexpr uint32_t Back = 0xFF0B101C;
    constexpr uint32_t Focus = 0xFF541528;
    constexpr uint32_t Red = 0xFFFF425C;
    constexpr uint32_t White = 0xFFF4F6F9;
    constexpr uint32_t Gray = 0xFFB9C1D2;
    constexpr int Cols = 5;
    constexpr int Page = 10;
    R14Background(c);
    // Hide all five printed demo covers, even when the user has fewer games.
    c.Fill(135, 435, 355, 369, Back);
    c.Fill(490, 447, 319, 336, Back);
    c.Fill(814, 447, 325, 336, Back);
    c.Fill(1144, 447, 326, 336, Back);
    c.Fill(1476, 448, 324, 336, Back);
    // Cover only inert screenshot arrows, dots and the old R13 badge.
    // Navigation and version are drawn by the running program instead.
    c.Fill(62, 570, 65, 118, Back);
    c.Fill(1807, 570, 75, 118, Back);
    c.Fill(790, 797, 345, 61, Back);
    c.Fill(697, 123, 150, 70, Back);
    c.Fill(80, 50, 670, 132, Back);
    c.Fill(80, 50, 7, 132, Red);
    c.Print(105, 73, "HIMURA SWITCH PS4 | R14", White, Back);
    c.Print(105, 125, "Nucleo Orbis Eden - PS4 Pro", Gray, Back);
    c.Fill(976, 48, 832, 140, Back);
    c.Print(1000, 72, "BIBLIOTECA DE JOGOS", White, Back);
    c.Print(1000, 130, Tx().language_name, Red, Back);
    // Each card is a real game from the discovered INT/USB list. It overlays
    // only the old screenshot's illustrative tiles, never fake menu controls.
    const int count = int(entries.size());
    const int first = (selected / Page) * Page;
    for (int slot = 0; slot < Page && first + slot < count; ++slot) {
        const int index = first + slot;
        const int x = 127 + (slot % Cols) * 334;
        const int y = 435 + (slot / Cols) * 254;
        const bool selected_card = index == selected;
        const uint32_t bg = selected_card ? Focus : Back;
        c.Fill(x, y, 325, 239, bg);
        c.Fill(x, y, 325, selected_card ? 7 : 3,
               selected_card ? Red : 0xFF3D4356);
        c.Fill(x, y, selected_card ? 6 : 3, 239,
               selected_card ? Red : 0xFF3D4356);
        c.Print(x + 17, y + 36, entries[index].source, Red, bg, 7);
        const std::string title = DisplayName(entries[index].name);
        c.Print(x + 17, y + 91, title.substr(0, 14), White, bg, 14);
        if (title.size() > 14) {
            c.Print(x + 17, y + 136, title.substr(14, 14), White, bg, 14);
        }
        if (selected_card) {
            c.Print(x + 17, y + 192, "X: INICIAR", White, bg);
        }
    }
    // Footer is produced by running controller code; the image has no buttons.
    constexpr uint32_t Footer = 0xFF070911;
    c.Fill(0, 970, Width, 110, Footer);
    c.Fill(0, 968, Width, 2, Red);
    c.Print(90, 989, "SETAS: ESCOLHER   X: JOGAR   TRIANGULO: IDIOMA",
            White, Footer, 70);
    char page[40];
    std::snprintf(page, sizeof(page), "%d/%d", selected + 1, count);
    c.Print(1710, 989, page, Red, Footer);
    c.Print(90, 1034, "Eden e port Orbis: credito aos respectivos autores (GPL-3.0)",
            Gray, Footer);
}
'''

def apply(repo: Path):
    menu = repo / "frontend/menu/rom_menu.cpp"
    platform = repo / "frontend/ps4_platform.h"
    pkg = repo / "package-eden.sh"
    linux_pkg = repo / "ci/70-package.sh"
    for path in (menu, platform, pkg, linux_pkg):
        if not path.is_file():
            raise RuntimeError(f"Missing Orbis source: {path}")
    s = menu.read_text(encoding="utf8")
    s = one(s, "struct Texts {\n", BACKGROUND + "\nstruct Texts {\n", "backdrop")
    s = one(s, "int language = 0; // 0 = English, 1 = Portuguese, 2 = Spanish",
               "int language = 1; // R14 Portuguese default, saved choice wins", "language")
    start = s.index("void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected) {")
    end = s.index("\n}\n\n} // Anonymous namespace", start)
    s = s[:start] + DRAW + s[end+2:]
    start = s.index("        int step = 0;\n", s.index("int RunRomMenu("))
    end = s.index("        if (step != 0) {\n", start)
    navigation = r'''        int step = 0;
        const std::uint32_t mask = Ps4::Button::Up | Ps4::Button::Down |
                                   Ps4::Button::Left | Ps4::Button::Right;
        const std::uint32_t held = now & mask;
        const std::uint32_t newly_pressed = pressed & mask;
        const std::uint32_t direction = newly_pressed ? newly_pressed :
            (held && Ps4::NowUs() >= repeat_at ? held : 0);
        if (direction) {
            step = (direction & Ps4::Button::Up) ? -5 :
                   (direction & Ps4::Button::Down) ? 5 :
                   (direction & Ps4::Button::Left) ? -1 : 1;
            repeat_at = Ps4::NowUs() + (newly_pressed ? 400000 : 110000);
        }
'''
    s = s[:start] + navigation + s[end:]
    s = one(s, "selected = (selected + step + count) % count;",
            "selected = (selected + (step % count) + count) % count;",
            "wrapping with <5 games")
    s = one(s, "    const int closed = sceVideoOutClose(handle);",
            "    const int closed = sceVideoOutClose(handle);\n    R14ReleaseBackground();",
            "free bitmap before game")
    menu.write_text(s, encoding="utf8")

    p = platform.read_text(encoding="utf8")
    p = one(p, 'inline constexpr const char* DataDir = "/data/edenps4";',
            'inline constexpr const char* DataDir = "/data/himura_switch_r14";',
            "isolate R14 user data")
    platform.write_text(p, encoding="utf8")

    p = pkg.read_text(encoding="utf8")
    title_ref = "$" + "{TITLE_ID}"
    for a, b, label in [
        ('TITLE="Orbis Eden"', 'TITLE="HIMURA SWITCH PS4 R14"', "package title"),
        ('TITLE_ID="EDPS00001"', 'TITLE_ID="HIMU00014"', "separate title id"),
        ('CID="IV0000-' + title_ref + '_00-EDENPS4000000000"',
         'CID="IV0000-' + title_ref + '_00-HIMURASWITCHR14X"', "content id"),
        ('s APP_VER Utf8 8 "01.01"', 's APP_VER Utf8 8 "01.14"', "app version"),
        ('s VERSION Utf8 8 "01.01"', 's VERSION Utf8 8 "01.14"', "package version"),
    ]:
        p = one(p, a, b, label)
    anchor = 'FILES="$FILES assets/misc/hbmenu.nro assets/misc/hbmenu-LICENSE.txt"'
    p = one(p, anchor, anchor + '\n'
            'mkdir -p "$ST/skin"\n'
            'cp "$ROOT/assets/himura-r14-menu.bgra" "$ST/skin/himura-r14-menu.bgra"\n'
            'FILES="$FILES skin/himura-r14-menu.bgra"',
            "ship approved image in PKG")
    pkg.write_text(p, encoding="utf8")

    # The Orbis Linux/CircleCI path uses a SECOND packager, not package-eden.sh.
    p = linux_pkg.read_text(encoding="utf8")
    for a, b, label in [
        ('TITLE="NX on Orbis"; TITLE_ID="EDPS00001"',
         'TITLE="HIMURA SWITCH PS4 R14"; TITLE_ID="HIMU00014"', "Linux pkg title/id"),
        ('CID="IV0000-' + title_ref + '_00-EDENPS4000000000"',
         'CID="IV0000-' + title_ref + '_00-HIMURASWITCHR14X"', "Linux pkg content id"),
        ('python3 "$ROOT/probe/make-icon.py" "$ST/sce_sys/icon0.png" "NX"',
         'cp "$ROOT/assets/icon0.png" "$ST/sce_sys/icon0.png"', "Linux pkg approved icon"),
        ('s APP_VER Utf8 8 "01.00"', 's APP_VER Utf8 8 "01.14"', "Linux pkg app version"),
        ('s VERSION Utf8 8 "01.00"', 's VERSION Utf8 8 "01.14"', "Linux pkg version"),
    ]:
        p = one(p, a, b, label)
    anchor = 'FILES="eboot.bin sce_sys/param.sfo sce_sys/icon0.png sce_sys/about/right.sprx sce_module/libc.prx sce_module/libSceFios2.prx assets/misc/hbmenu.nro assets/misc/hbmenu-LICENSE.txt"'
    p = one(p, anchor, anchor + '\n'
            'mkdir -p "$ST/skin"\n'
            'cp "$ROOT/assets/himura-r14-menu.bgra" "$ST/skin/himura-r14-menu.bgra"\n'
            'FILES="$FILES skin/himura-r14-menu.bgra"',
            "Linux pkg approved backdrop")
    linux_pkg.write_text(p, encoding="utf8")
    print("R14 Orbis frontend/UI and both native packaging paths patched successfully")
    print("CPU/JIT/Vulkan/memory upstream source is unchanged")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-frontend.py <orbis-eden-checkout>")
    apply(Path(sys.argv[1]).resolve())
