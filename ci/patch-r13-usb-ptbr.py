#!/usr/bin/env python3
"""R13: USB mount naming/access checks and Brazilian Portuguese UI.

Runs LAST, after the existing pinned Eden4 patches. No changes to game keys,
firmware, saves or user files. Fails on missing structural anchors.
"""
from pathlib import Path
import sys


def exactly_one(text: str, old: str, new: str, where: str) -> str:
    number = text.count(old)
    if number != 1:
        raise RuntimeError(f"R13 PT-BR {where}: expected 1 anchor, got {number}: {old[:85]!r}")
    return text.replace(old, new, 1)


def optional_literal(text: str, old: str, new: str) -> str:
    """Translate complete quoted strings, never keys or variable fragments."""
    if old in text:
        return text.replace(old, new)
    return text


def patch_main(text: str) -> str:
    text = exactly_one(
        text,
        'std::vector<SourceDef> defs{{"internal", "Internal storage", "/data/EdenPS4/games", false}};',
        'std::vector<SourceDef> defs{{"internal", "Armazenamento interno", "/data/EdenPS4/games", false}};',
        "internal source label",
    )
    text = exactly_one(
        text,
        '// USB 1 is always listed (it shows "Not connected"); further drives when they are plugged in.\n'
        '    for (int i = 0; i < 8; ++i) {\n'
        '        const std::string path = "/mnt/usb" + std::to_string(i);\n'
        '        if (i == 0 || IsDirectory(path)) defs.push_back({"usb" + std::to_string(i), "USB " + std::to_string(i + 1), path, false});\n'
        '    }',
        '// The labels match actual Orbis mount paths, not physical USB port numbering.\n'
        '    // Always show USB 0 and USB 1; list other mounted USBs dynamically.\n'
        '    for (int i = 0; i < 8; ++i) {\n'
        '        const std::string path = "/mnt/usb" + std::to_string(i);\n'
        '        if (i < 2 || IsDirectory(path))\n'
        '            defs.push_back({"usb" + std::to_string(i), "USB " + std::to_string(i), path, false});\n'
        '    }',
        "USB path numbering",
    )
    text = exactly_one(
        text,
        'bool IsDirectory(const std::string& path) {\n'
        '    struct stat status{};\n'
        '    return stat(path.c_str(), &status) == 0 && S_ISDIR(status.st_mode);\n'
        '}',
        'bool IsDirectory(const std::string& path) {\n'
        '    struct stat status{};\n'
        '    return stat(path.c_str(), &status) == 0 && S_ISDIR(status.st_mode);\n'
        '}\n'
        '\n'
        '// A mount can exist yet not be readable by the game process.\n'
        'bool CanBrowseDirectory(const std::string& path) {\n'
        '    DIR* directory = opendir(path.c_str());\n'
        '    if (!directory) return false;\n'
        '    closedir(directory);\n'
        '    return true;\n'
        '}',
        "USB access diagnostic",
    )
    text = exactly_one(
        text, 'IsDirectory(def.path), def.removable,',
        'CanBrowseDirectory(def.path), def.removable,', "mounted access report")
    text = exactly_one(
        text,
        '{"Keys", keys ? "Ready" : "Missing"},\n'
        '            {"Firmware", firmware ? "Installed" : "Missing"},\n'
        '            {"Software", std::to_string(games.size())}',
        '{"Chaves", keys ? "Prontas" : "Ausentes"},\n'
        '            {"Firmware", firmware ? "Instalado" : "Ausente"},\n'
        '            {"Jogos", std::to_string(games.size())}',
        "file info translations",
    )
    text = exactly_one(
        text,
        '"Logs copied to USB. You can attach the EdenPS4-*.log files."',
        '"Registros copiados para USB. Envie os arquivos EdenPS4-*.log."',
        "USB export success",
    )
    text = exactly_one(
        text,
        '"USB unavailable. Logs remain in /data/EdenPS4/"',
        '"USB inacessivel. Registros mantidos em /data/EdenPS4/"',
        "USB export error",
    )
    for old, new in MAIN_LITERALS.items():
        text = optional_literal(text, old, new)
    return text



MAIN_LITERALS = {
    '"Version"': '"Versao"',
    '"Console mode"': '"Modo do console"',
    '"PS4 Pro mode"': '"Modo PS4 Pro"',
    '"PS4 (base mode)"': '"PS4 (modo base)"',
    '"Memory for games"': '"Memoria para jogos"',
    '"Current user"': '"Usuario atual"',
    '"Data folder"': '"Pasta de dados"',
    '"Sampling profiler"': '"Analise de desempenho"',
    '"Writes where CPU time goes to eden.log every 10 s. Costs a little speed."':
        '"Registra o uso da CPU em eden.log a cada 10 s; pode reduzir o desempenho."',
    '"Renderer"': '"Renderizador"',
    '"Null draws nothing (CPU-only test)."': '"Nulo nao desenha imagens (teste somente de CPU)."',
    '"JIT inline memory"': '"Memoria inline JIT"',
    '"JIT direct page table"': '"Tabela de paginas direta JIT"',
    '"JIT page reuse"': '"Reutilizacao de paginas JIT"',
    '"JIT register tweaks"': '"Otimizacoes dos registradores JIT"',
    '"Diagnostics: Off sends every guest memory access through a slow callback."':
        '"Diagnostico: desativar torna o acesso a memoria mais lento."',
    '"Diagnostics: Off decodes packed page table entries instead."':
        '"Diagnostico: desativar usa a decodificacao da tabela de paginas."',
    '"Diagnostics: Off looks up the page table for every access."':
        '"Diagnostico: desativar pesquisa a tabela de paginas a cada acesso."',
    '"Diagnostics: Off uses Dynarmic\'s original register allocation."':
        '"Diagnostico: desativar usa a alocacao original de registradores Dynarmic."',
    '"Theme"': '"Tema"',
    '"Menu sounds"': '"Sons do menu"',
    '"Sounds when you move around the HOME menu. Games are not affected."':
        '"Sons ao navegar no menu principal. Os jogos nao sao afetados."',
    '"Video output"': '"Saida de video"',
    '"Resolution sent to the TV. 1080p uses ~13 MiB more GPU memory; pair it with Docked."':
        '"Resolucao da TV. 1080p consome aproximadamente 13 MiB adicionais da GPU."',
    '"Player 1 controller"': '"Controle do jogador 1"',
    '"Player 2 controller"': '"Controle do jogador 2"',
    '"Player 3 controller"': '"Controle do jogador 3"',
    '"Player 4 controller"': '"Controle do jogador 4"',
    '"The Switch controller this PS4 controller acts as."':
        '"Tipo de controle Switch emulado pelo controle do PS4."',
}

UI_LITERALS = {
    '"About"': '"Sobre"',
    '"Game Files"': '"Arquivos de jogos"',
    '"System Settings"': '"Configuracoes do sistema"',
    '"Power"': '"Desligar"',
    '"All Software"': '"Todos os jogos"',
    '"By File Name"': '"Por nome do arquivo"',
    '"By Title"': '"Por titulo"',
    '"No software found."': '"Nenhum jogo encontrado."',
    '"User Page"': '"Pagina do usuario"',
    '"User Settings"': '"Configuracoes do usuario"',
    '"Current user"': '"Usuario atual"',
    '"Add User"': '"Adicionar usuario"',
    '"System Information"': '"Informacoes do sistema"',
    '"Copy logs to USB"': '"Copiar registros para USB"',
    '"Look for software again"': '"Procurar jogos novamente"',
    '"Changes are saved at once and apply when software starts."':
        '"As alteracoes sao salvas imediatamente e aplicadas ao iniciar o jogo."',
    '"Each user keeps their own save data. The current user plays the next game."':
        '"Cada usuario mantem seus proprios saves. O usuario atual joga o proximo jogo."',
    '"Basic Black"': '"Preto basico"',
    '"Basic White"': '"Branco basico"',
    '"Sources"': '"Origens"',
    '"Add Folder"': '"Adicionar pasta"',
    '"Not connected"': '"Nao conectado: verifique a montagem USB"',
    '" game - "': '" jogo - "',
    '" games - "': '" jogos - "',
    '"Looking for software..."': '"Procurando jogos..."',
    '"Folder removed."': '"Pasta removida."',
    '" is on."': '" ativado."',
    '" is off."': '" desativado."',
    '"File"': '"Arquivo"',
    '"Source"': '"Origem"',
    '"Size"': '"Tamanho"',
    '"Title ID"': '"ID do titulo"',
    '"Cross: Start      Circle: Back"': '"X: Iniciar      O: Voltar"',
    '"Emulation"': '"Emulacao"',
    '"PS4 port"': '"Versao para PS4"',
    '"HOME menu layout"': '"Interface do menu principal"',
    '"Font"': '"Fonte"',
    '"Eden developers and contributors (GPL-3.0)"':
        '"Desenvolvedores e colaboradores do Eden (GPL-3.0)"',
    '"Eden4, on the DolphinPS4 runtime, Mesa RADV and OpenOrbis"':
        '"Eden4, com DolphinPS4, Mesa RADV e OpenOrbis"',
    '"Inspired by SwitchLauncher (kasobos67, GPL-3.0)"':
        '"Inspirado em SwitchLauncher (kasobos67, GPL-3.0)"',
    '"Nunito (SIL Open Font License)"': '"Nunito (licenca SIL Open Font)"',
    '"Not affiliated with or endorsed by Nintendo or Sony. No console artwork, fonts or sounds are included."':
        '"Projeto independente, sem vinculo ou apoio da Nintendo ou Sony. Creditos e licencas preservados."',
    '"Close Eden4?"': '"Fechar HIMURA SWITCH?"',
    '"You return to the PS4 home screen."': '"Voce voltara a tela inicial do PS4."',
    '"Player "': '"Jogador "',
    '"Copy Logs to USB"': '"Copiar registros para USB"',
    '"Refresh"': '"Atualizar"',
    '"Remove"': '"Remover"',
    '"Turn Off"': '"Desativar"',
    '"Turn On"': '"Ativar"',
    '"Start"': '"Iniciar"',
    '"Sort"': '"Ordenar"',
    '"Options"': '"Opcoes"',
    '"Open"': '"Abrir"',
    '"Back"': '"Voltar"',
    '"Next"': '"Avancar"',
    '"Add"': '"Adicionar"',
    '"Loading"': '"Carregando"',
    '"Internal storage and USB drives are always listed. Turn them off instead."':
        '"O armazenamento interno e as USBs permanecem na lista. Desative a origem, se desejar."',
}

def patch_ui(text: str) -> str:
    text = exactly_one(
        text,
        'const char* const ShortcutNames[] = {"About", "Game Files", "Users", "Controllers", "System Settings", "Power"};',
        'const char* const ShortcutNames[] = {"Sobre", "Arquivos de jogos", "Usuarios", "Controles", "Configuracoes", "Desligar"};',
        "top shortcut names",
    )
    # Category names are also used as internal control-flow keys.
    # Translate ONLY their displayed names, never their matching logic.
    text = exactly_one(
        text,
        'const Category Categories[] =',
        'const char* R13PTCategory(const char* value) {\n'
        '    const std::string_view category{value};\n'
        '    if (category == "Users") return "Usuarios";\n'
        '    if (category == "Display") return "Video";\n'
        '    if (category == "Controllers") return "Controles";\n'
        '    if (category == "Themes") return "Temas";\n'
        '    if (category == "Sound") return "Audio";\n'
        '    if (category == "Advanced") return "Avancado";\n'
        '    if (category == "System") return "Sistema";\n'
        '    return value;\n'
        '}\n'
        'const Category Categories[] =',
        "settings category labels",
    )
    text = exactly_one(
        text,
        'const Category Categories[] =',
        'std::string R13PTValue(const std::string& value) {\\n'
        '    if (value == "On") return "Ligado";\\n'
        '    if (value == "Off") return "Desligado";\\n'
        '    if (value == "Docked") return "Modo TV";\\n'
        '    if (value == "Handheld") return "Modo portatil";\\n'
        '    if (value == "Basic Black") return "Preto basico";\\n'
        '    if (value == "Basic White") return "Branco basico";\\n'
        '    return value;\\n'
        '}\\n'
        'const Category Categories[] =',
        "visible setting option values",
    )
    text = exactly_one(
        text, 'rows.push_back({option.label, value, IsOn(value), {}, index});',
        'rows.push_back({option.label, R13PTValue(value), IsOn(value), {}, index});',
        "settings row values",
    )
    text = exactly_one(
        text, 'canvas.Text(option.values[i], 632,',
        'canvas.Text(R13PTValue(option.values[i]), 632,',
        "choices in PT-BR",
    )

    text = exactly_one(
        text, 'canvas.Text(Categories[i].name, 188,',
        'canvas.Text(R13PTCategory(Categories[i].name), 188,',
        "visible category labels",
    )
    for old, new in UI_LITERALS.items():
        text = optional_literal(text, old, new)
    # Keep the internal On/Off setting values unchanged; translate only the USB label.
    text = exactly_one(text,
        'canvas.Text(source.enabled ? "On" : "Off",',
        'canvas.Text(source.enabled ? "Ativo" : "Desativado",',
        "source toggle label")

    text = exactly_one(
        text,
        'TextBlock(x, "Games are found in each source\'s folder and one folder down (for example a USB drive\'s "\n'
        '                     "switch folder). NSP, XCI, NRO and NSO files. Keys go in /data/EdenPS4/keys.",',
        'TextBlock(x, "Escolha uma pasta do HD para localizar NSP, XCI, NRO e NSO. "\n'
        '                     "A busca inclui subpastas. Chaves e firmware precisam ser configurados separadamente.",',
        "game files help",
    )
    text = exactly_one(
        text,
        'const std::string detail = !source.available ? "Nao conectado: verifique a montagem USB"',
        'const std::string detail = !source.available ? "Nao montado/acessivel: " + source.path',
        "show real inaccessible mount",
    )
    return text


def patch(root: Path) -> None:
    main = root / "eden/src/yuzu_ps4/main.cpp"
    ui = root / "eden/src/yuzu_ps4/ui_launcher.cpp"
    main.write_text(patch_main(main.read_text(encoding="utf-8")), encoding="utf-8")
    ui.write_text(patch_ui(ui.read_text(encoding="utf-8")), encoding="utf-8")
    print("R13: USB 0/1 nomes por mount real, acesso testado e telas principais traduzidas (PT-BR)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: patch-r13-usb-ptbr.py <checkout Eden4>")
    patch(Path(sys.argv[1]).resolve())
