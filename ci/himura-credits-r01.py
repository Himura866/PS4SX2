#!/usr/bin/env python3
"""HIMURA menu credits on the pinned experimental Orbis-EDEN source.

Never modifies NewEden-04.89.pkg or its executable. All edits happen in the
temporary CircleCI checkout. Fail closed if source anchors differ.
"""
from pathlib import Path
import sys

CREDITS = """HIMURA SWITCH PS4 - CREDITOS E LICENCAS

Identidade visual e personalizacao: projeto HIMURA SWITCH PS4.
Base experimental de desenvolvimento: Orbis-EDEN.
Nucleo de emulacao: Eden Emulator e seus colaboradores.
Creditos exibidos pela interface original da base PS4:
Mr.Kitsune9, @blorbus0866, @titotostito_ (icone), @loony_user, Claude.
Base historica: NX on Orbis (Alejo). Referencia Eden4: xatyy.

Licenca da base Orbis-EDEN: GNU GPL-3.0-or-later.
Consulte LICENSE.txt para a licenca completa; sem garantias.

IMPORTANTE: A autoria do binario New Eden 04.89 do usuario nao foi
verificada. Estes creditos sao da base de codigo Orbis-EDEN usada
somente na compilacao experimental e NAO identificam os autores
do PKG 04.89 original.
"""


def replace_once(text, old, new, context):
    count = text.count(old)
    if count != 1:
        raise ValueError(f"creditos: ancora {context} esperada 1 vez, obtida {count}")
    return text.replace(old, new, 1)


def apply(root):
    root = Path(root).resolve()
    menu = root / "frontend/menu/rom_menu.cpp"
    package = root / "ci/70-package.sh"
    if not menu.is_file() or not package.is_file() or not (root / "LICENSE").is_file():
        raise FileNotFoundError("Fonte Orbis-EDEN original incompleta")

    src = menu.read_text()
    src = replace_once(
        src,
        "void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected) {",
        "void Draw(Canvas& c, const std::vector<MenuEntry>& entries, int selected, bool showCredits) {",
        "assinatura Draw",
    )
    src = replace_once(
        src,
        '    c.Print(Left + 36, 60, "ORBIS EDEN", 0xFFFFFFFF, Background);',
        '    c.Print(Left + 36, 60, "HIMURA SWITCH PS4", 0xFFFFFFFF, Background);',
        "titulo de interface",
    )
    src = replace_once(
        src,
        "    c.Fill(Left, 190, Width - 2 * Left, 3, Dim);",
        """    c.Print(Left, 161, "QUADRADO: CREDITOS    TRIANGULO: IDIOMA", Accent, Background);
    c.Fill(Left, 190, Width - 2 * Left, 3, Dim);""",
        "controles reais no topo",
    )
    src = replace_once(
        src,
        "    const int count = int(entries.size());",
        """    if (showCredits) {
        c.Fill(Left, 225, Width - 2 * Left, 740, Background);
        constexpr int X = Left + 24;
        c.Print(X, 258, "CREDITOS E LICENCAS", Accent, Background);
        c.Print(X, 316, "Emulacao: Eden Emulator e contribuidores", Text, Background);
        c.Print(X, 370, "Port PS4: Orbis-EDEN / Mr.Kitsune9 e contribuidores", Text, Background);
        c.Print(X, 424, "Creditos originais: @blorbus0866, @titotostito_, @loony_user, Claude", Text, Background);
        c.Print(X, 478, "Base historica: NX on Orbis (Alejo); referencia Eden4 (xatyy)", Text, Background);
        c.Print(X, 532, "Interface personalizada: HIMURA SWITCH PS4", Text, Background);
        c.Print(X, 586, "Licenca do codigo: GPL-3.0-or-later", Text, Background);
        c.Print(X, 640, "Sem garantias. Veja licenses/LICENSE.txt no pacote", Dim, Background);
        c.Print(X, 750, "CIRCULO OU X: VOLTAR AOS JOGOS", Accent, Background);
        return;
    }
    const int count = int(entries.size());""",
        "tela creditos",
    )
    src = replace_once(
        src,
        "    int selected = std::clamp(initial, 0, int(names.size()) - 1);",
        "    int selected = std::clamp(initial, 0, int(names.size()) - 1);\n    bool creditsOpen = false;",
        "estado de creditos",
    )
    src = replace_once(
        src,
        "        Draw(canvas, names, selected);",
        "        Draw(canvas, names, selected, creditsOpen);",
        "renderizacao da tela",
    )
    src = replace_once(
        src,
        """        if (pressed & Ps4::Button::Cross) {
            break;
        }""",
        """        if (pressed & Ps4::Button::Square) {
            creditsOpen = !creditsOpen;
            present();
            continue;
        }
        if (creditsOpen) {
            if (pressed & (Ps4::Button::Circle | Ps4::Button::Cross)) {
                creditsOpen = false;
                present();
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(16));
            continue;
        }
        if (pressed & Ps4::Button::Cross) {
            break;
        }""",
        "controle Quadrado/Circulo para creditos, sem iniciar jogo",
    )
    pkg = package.read_text()
    pkg = replace_once(
        pkg,
        'FILES="eboot.bin sce_sys/param.sfo sce_sys/icon0.png sce_sys/about/right.sprx sce_module/libc.prx sce_module/libSceFios2.prx assets/misc/hbmenu.nro assets/misc/hbmenu-LICENSE.txt"',
        """FILES="eboot.bin sce_sys/param.sfo sce_sys/icon0.png sce_sys/about/right.sprx sce_module/libc.prx sce_module/libSceFios2.prx assets/misc/hbmenu.nro assets/misc/hbmenu-LICENSE.txt"
# Preserve GPL-3.0 and original project attributions in the installed PKG.
mkdir -p "$ST/licenses"
cp "$ROOT/LICENSE" "$ST/licenses/LICENSE.txt"
cp "$ROOT/licenses/HIMURA-CREDITS.txt" "$ST/licenses/HIMURA-CREDITS.txt"
FILES="$FILES licenses/LICENSE.txt licenses/HIMURA-CREDITS.txt" """.rstrip(),
        "inclusao de creditos e licenca no PKG",
    )
    credit_dir = root / "licenses"
    credit_dir.mkdir(parents=True, exist_ok=True)
    (credit_dir / "HIMURA-CREDITS.txt").write_text(CREDITS)
    menu.write_text(src)
    package.write_text(pkg)
    print("UI: Quadrado abre Creditos; Circulo/X volta sem iniciar jogo.")
    print("UI: Controles reais no topo, GPL e creditos preservados no PKG.")
    print("ATENCAO: esta e a base Orbis-EDEN experimental, NAO o binario New Eden 04.89.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("uso: python3 ci/himura-credits-r01.py ORBIS_EDEN_CHECKOUT")
    apply(sys.argv[1])
