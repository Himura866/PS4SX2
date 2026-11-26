#!/usr/bin/env python3
"""Install a functional, controller-operated USB NSP update/DLC importer in R14."""
from pathlib import Path
import shutil
import sys

def once(s, old, new, title):
    count = s.count(old)
    if count != 1:
        raise RuntimeError(f"R14 {title}: expected 1 anchor; got {count}")
    return s.replace(old, new, 1)

def main(path):
    src = Path(__file__).resolve().parent.parent / "r14/updates"
    root = Path(path).resolve()
    folder = root / "frontend/menu"
    for name in ("r14_update_manager.cpp", "r14_update_manager.h"):
        shutil.copyfile(src / name, folder / name)

    file = folder / "rom_menu.cpp"
    s = file.read_text()
    s = once(s, '#include "menu/rom_menu.h"',
                '#include "menu/rom_menu.h"\n#include "menu/r14_update_manager.h"', "include")
    s = once(s,
        "void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected,\n"
        "          const uint32_t* wallpaper) {",
        "void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected,\n"
        "          const uint32_t* wallpaper, bool manager_open,\n"
        "          const std::vector<Himura::Updates::Package>& packages, int package_focus,\n"
        "          const Himura::Updates::Importer& importer) {", "draw args")
    s = once(s,
        '    c.Print(Left, Height - 83, Tx().controls, Text, Background);',
        '    c.Print(Left, Height - 83, Tx().controls, Text, Background);\n'
        '    c.Print(Left, Height - 43, "Quadrado: Atualizacoes / DLCs", Text, Background);',
        "real menu help")
    modal = r'''    // Native menu: actual files and actions, no static screenshot buttons.
    if (manager_open) {
        constexpr int mx = 185, my = 215, mw = 1550, mh = 650;
        c.Fill(mx, my, mw, mh, 0xFF0A1020);
        c.Fill(mx, my, mw, 5, 0xFFD52236);
        c.Print(mx + 48, my + 30, "INSTALAR / IMPORTAR UPDATES E DLCs (NSP)",
                0xFFFFFFFF, 0xFF0A1020);
        c.Print(mx + 48, my + 83,
                "USB: pastas updates/ ou dlc/   |   X: importar   Circulo: voltar/cancelar",
                0xFFB8CBDF, 0xFF0A1020);
        const int count = int(packages.size());
        const int first = std::clamp(package_focus - 4, 0, std::max(count - 9, 0));
        for (int row = 0; row < 9 && first + row < count; ++row) {
            const int index = first + row, top = my + 145 + row * 47;
            const bool selected = index == package_focus;
            const uint32_t bg = selected ? 0xFF254C86 : 0xFF0A1020;
            if (selected) c.Fill(mx + 32, top - 4, mw - 64, 40, bg);
            const auto& pkg = packages[index];
            c.Print(mx + 53, top, pkg.source + "  " + pkg.path.filename().string(),
                    selected ? 0xFFFFFFFF : 0xFFE4ECF7, bg, 90);
        }
        if (!count)
            c.Print(mx + 48, my + 195, "Nao ha NSP no USB em updates/ ou dlc/",
                    0xFFE4ECF7, 0xFF0A1020);
        c.Fill(mx, my + mh - 85, mw, 85, 0xFF131F34);
        std::string progress = importer.Message();
        if (importer.Active()) {
            progress += " " + std::to_string(importer.Percent()) + "%";
            c.Fill(mx + 42, my + mh - 23, mw - 84, 10, 0xFF344561);
            c.Fill(mx + 42, my + mh - 23, (mw - 84) * int(importer.Percent()) / 100,
                   10, 0xFF3CD192);
        }
        c.Print(mx + 48, my + mh - 73, progress, 0xFFFFFFFF, 0xFF131F34, 103);
    }
}'''
    s = once(s,
        "    // Full upstream credits are shipped in the package license notice.\n}",
        modal, "modal")
    s = once(s,
        "    int selected = std::clamp(initial, 0, int(names.size()) - 1);\n    int back = 0;",
        "    int selected = std::clamp(initial, 0, int(names.size()) - 1);\n"
        "    std::vector<Himura::Updates::Package> packages;\n"
        "    Himura::Updates::Importer importer;\n"
        "    int package_focus = 0;\n"
        "    bool manager_open = false;\n    int back = 0;",
        "manager state")
    s = once(s,
        "        Draw(canvas, names, selected, wallpaper.empty() ? nullptr : wallpaper.data());",
        "        Draw(canvas, names, selected, wallpaper.empty() ? nullptr : wallpaper.data(),\n"
        "             manager_open, packages, package_focus, importer);",
        "modal render")
    old = '''        const std::uint32_t pressed = now & ~previous;
        previous = now;
        if (pressed & Ps4::Button::Cross) {
            break;
        }
        if (pressed & Ps4::Button::Triangle) {'''
    new = '''        const std::uint32_t pressed = now & ~previous;
        previous = now;
        if (manager_open) {
            if (pressed & Ps4::Button::Circle) {
                importer.Cancel();
                manager_open = false;
                present();
            } else if ((pressed & Ps4::Button::Cross) && !importer.Active()) {
                if (!packages.empty()) importer.Start(packages[size_t(package_focus)]);
                present();
            } else if (!importer.Active() && !packages.empty() &&
                       (pressed & (Ps4::Button::Up | Ps4::Button::Down))) {
                const int delta = (pressed & Ps4::Button::Up) ? -1 : 1;
                package_focus = (package_focus + delta + int(packages.size())) % int(packages.size());
                present();
            }
            if (importer.Active()) {
                importer.Tick(); // 256 KiB per frame, no UI freeze while copying
                present();
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(16));
            continue;
        }
        if (pressed & Ps4::Button::Square) {
            packages = Himura::Updates::Discover();
            package_focus = 0;
            manager_open = true;
            present();
            std::this_thread::sleep_for(std::chrono::milliseconds(16));
            continue;
        }
        if (pressed & Ps4::Button::Cross) {
            break;
        }
        if (pressed & Ps4::Button::Triangle) {'''
    s = once(s, old, new, "PS4 input routing")
    file.write_text(s)

    cmake_file = root / "frontend/frontend.cmake"
    cmake = cmake_file.read_text()
    fe = "$" + "{_fe}"
    a = f'"{fe}/menu/rom_menu.cpp" "{fe}/menu/rom_menu.h"'
    b = a + f'\n    "{fe}/menu/r14_update_manager.cpp" "{fe}/menu/r14_update_manager.h"'
    cmake = once(cmake, a, b, "CMake update manager")
    cmake_file.write_text(cmake)

    main_cpp = (root / "frontend/main.cpp").read_text()
    assert 'v.external_content_dirs = {(fs::path{Ps4::DataDir} / "updates").string()};' in main_cpp, \
        "Orbis no longer loads updates NSP directory"
    print("R14: Square opens native update/DLC manager; Cross imports USB NSP; Circle cancels")
    print("R14: existing Eden external_content_dirs loads imported NSPs on game boot")
    print("R14: compatibility of each NSP with game's TitleID still validated at boot")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: r14-enable-update-manager.py <adapted Orbis Eden>")
    main(sys.argv[1])
