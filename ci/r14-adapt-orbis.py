#!/usr/bin/env python3
"""R14: patch a pinned Orbis Eden 25/11 checkout, fail on upstream drift.

No core files are replaced: keep the matched 46 patches for the PS4 CPU/JIT,
Vulkan, memory, Mii and runtime. Only adapt the launcher, package and assets.
"""
from pathlib import Path
import sys

def one(text, before, after, what):
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"R14 {what}: expected one anchor, got {count}")
    return text.replace(before, after, 1)

def apply(root):
    root = Path(root).resolve()
    menu_file = root / "frontend/menu/rom_menu.cpp"
    header_file = root / "frontend/ps4_platform.h"
    pkg_file = root / "ci/70-package.sh"
    for file in (menu_file, header_file, pkg_file):
        if not file.is_file():
            raise RuntimeError(f"Missing upstream file: {file}")

    m = menu_file.read_text()
    m = one(m,
        "void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected) {",
        "void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected,\n"
        "          const uint32_t* wallpaper) {",
        "live rendering signature")
    m = one(m,
        "    c.Fill(0, 0, Width, Height, Background);\n    // Header: name, then what it is.",
        "    if (wallpaper) std::memcpy(c.pixels, wallpaper, BufferBytes);\n"
        "    else c.Fill(0, 0, Width, Height, Background);\n"
        "    // Header: name, then what it is.",
        "original wallpaper drawing")
    m = one(m,
        "    c.Fill(Left, 70, 10, 100, Accent);",
        "    if (!wallpaper) c.Fill(Left, 70, 10, 100, Accent);",
        "preserve wallpaper top")
    m = one(m,
        '    c.Print(Left + 36, 60, "ORBIS EDEN", 0xFFFFFFFF, Background);',
        '    if (!wallpaper) c.Print(Left + 36, 60, "HIMURA SWITCH PS4", 0xFFFFFFFF, Background);',
        "samurai logo")
    m = one(m,
        '    c.Print(Left + 36, 112, Tx().tagline, Dim, Background);',
        '    if (!wallpaper) c.Print(Left + 36, 112, Tx().tagline, Dim, Background);',
        "remove double static title")
    m = one(m,
        "int language = 0; // 0 = English, 1 = Portuguese, 2 = Spanish",
        "int language = 1; // R14 default: Portuguese, can change with Triangle",
        "PT-BR default")
    m = one(m,
        "    c.Fill(Left, Height - 170, Width - 2 * Left, 3, Dim);",
        "    c.Fill(0, Height - 112, Width, 3, 0xFFD52236);",
        "bottom red separator")
    if m.count("Height - 150") != 2:
        raise RuntimeError("R14 footer has changed")
    m = m.replace("Height - 150", "Height - 83")
    m = one(m,
        '    c.Print(Left, Height - 105,\n'
        '            "Mr.Kitsune9, @blorbus0866, @titotostito_ (icon), @loony_user, Claude",\n'
        '            Dim, Background);\n'
        '    c.Print(Left, Height - 65, "Based on NX on Orbis by Alejo  -  Reference: xatyy (Eden4)", Dim,\n'
        '            Background);\n',
        '    // Full upstream credits are shipped in the package license notice.\n',
        "remove inert screenshot credits")
    m = one(m,
        '    LoadLanguage();\n    Ps4::Log("menu: %zu games listed, language %s", names.size(), LanguageCodes[language]);',
        '    // Load exactly one 1080p BGRA from the approved R13 samurai wallpaper.\n'
        '    // The buffer is freed when RunRomMenu returns, before loading a game.\n'
        '    std::vector<uint32_t> wallpaper;\n'
        '    if (FILE* file = std::fopen("/app0/assets/himura/r14-menu.bgra", "rb")) {\n'
        '        wallpaper.resize(size_t(Width) * Height);\n'
        '        if (std::fread(wallpaper.data(), 1, BufferBytes, file) != BufferBytes ||\n'
        '            std::fgetc(file) != EOF) {\n'
        '            wallpaper.clear();\n'
        '            Ps4::Log("HIMURA R14: bad wallpaper, using fallback menu");\n'
        '        }\n'
        '        std::fclose(file);\n'
        '    } else {\n'
        '        Ps4::Log("HIMURA R14: wallpaper missing, using fallback menu");\n'
        '    }\n'
        '    LoadLanguage();\n'
        '    Ps4::Log("menu: %zu games listed, language %s", names.size(), LanguageCodes[language]);',
        "load approved wallpaper once")
    m = one(m,
        "        Draw(canvas, names, selected);",
        "        Draw(canvas, names, selected, wallpaper.empty() ? nullptr : wallpaper.data());",
        "live menu atop wallpaper")
    if "if (pressed & Ps4::Button::Cross)" not in m or "pressed & Ps4::Button::Triangle" not in m:
        raise RuntimeError("R14 controller input missing")
    menu_file.write_text(m)

    h = header_file.read_text()
    h = one(h, 'inline constexpr const char* DataDir = "/data/edenps4";',
            'inline constexpr const char* DataDir = "/data/himura-switch-r14";',
            "independent saves/configuration")
    header_file.write_text(h)

    p = pkg_file.read_text()
    p = one(p, 'TITLE="NX on Orbis"; TITLE_ID="EDPS00001"',
            'TITLE="HIMURA SWITCH PS4"; TITLE_ID="HIMU00014"', "app title")
    p = one(p, 'EDENPS4000000000', 'HIMURASWITCH0140', "package content suffix")
    p = one(p,
        'python3 "$ROOT/probe/make-icon.py" "$ST/sce_sys/icon0.png" "NX"',
        'if [ -s "$ROOT/assets/icon0.png" ]; then\n'
        '  cp "$ROOT/assets/icon0.png" "$ST/sce_sys/icon0.png"\n'
        'else\n'
        '  python3 "$ROOT/probe/make-icon.py" "$ST/sce_sys/icon0.png" "HM"\n'
        'fi',
        "real approved icon")
    if p.count('"01.00"') != 2:
        raise RuntimeError("Unexpected SFO version number in original package")
    p = p.replace('"01.00"', '"01.14"')
    p = one(p, '(\n    cd "$ST"\n    SFO=sce_sys/param.sfo',
        'test -s "$ROOT/assets/himura-r14-menu.bgra" || { echo "R14 missing art"; exit 19; }\n'
        'test "$(stat -c %s "$ROOT/assets/himura-r14-menu.bgra")" -eq 8294400 || { echo "R14 art dimensions invalid"; exit 20; }\n'
        'mkdir -p "$ST/assets/himura" "$ST/licenses"\n'
        'cp "$ROOT/assets/himura-r14-menu.bgra" "$ST/assets/himura/r14-menu.bgra"\n'
        'cp "$ROOT/LICENSE" "$ST/licenses/LICENSE.txt"\n'
        'FILES="$FILES assets/himura/r14-menu.bgra licenses/LICENSE.txt"\n'
        '(\n    cd "$ST"\n    SFO=sce_sys/param.sfo',
        "include art and GNU GPL notice in PKG")
    pkg_file.write_text(p)
    print("R14 adapted: Orbis Eden 25/11 PS4 core unchanged; real HIMURA samurai skin/controls; PT language; isolated data")
    print("No emulation performance claim until hardware testing")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: r14-adapt-orbis.py <pinned Orbis Eden repo>")
    apply(sys.argv[1])
