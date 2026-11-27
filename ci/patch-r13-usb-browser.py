#!/usr/bin/env python3
"""R13: controller-driven source-folder browser for the pinned Eden4 PS4 launcher.

Fail closed on unexpected source changes. No keyboard input or writes to USB.
"""
from pathlib import Path
import sys


def once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"R13 folder browser {label}: expected 1 anchor, got {count}")
    return source.replace(old, new, 1)


BROWSER_HELPER = r'''
// Only list directories. lstat refuses symlinks, avoiding navigation outside
// the chosen USB/internal source via links. Never enumerate whole files here.
std::vector<std::string> R13FolderChoices(const std::string& folder) {
    std::vector<std::string> result;
    DIR* dir = opendir(folder.c_str());
    if (!dir) return result;
    while (const dirent* entry = readdir(dir)) {
        const std::string name = entry->d_name;
        if (name.empty() || name == "." || name == ".." || name[0] == '.') continue;
        const std::string full = folder + "/" + name;
        struct stat status{};
        if (lstat(full.c_str(), &status) == 0 && S_ISDIR(status.st_mode))
            result.push_back(name);
        if (result.size() >= 512) break; // keep controller screen responsive
    }
    closedir(dir);
    std::sort(result.begin(), result.end());
    if (result.size() > 128) result.resize(128);
    return result;
}
'''

BROWSER_UPDATE = r'''
        case Modal::FolderPicker: {
            // Empty path means choose a storage device; otherwise browse its
            // directories, with row zero always being "select this folder".
            const auto all = host.Sources();
            std::vector<Source> roots;
            for (const Source& source : all) {
                if (!source.removable &&
                    (source.path == "/data/EdenPS4/games" ||
                     source.path.rfind("/mnt/usb", 0) == 0))
                    roots.push_back(source);
            }
            const bool choose_drive = st.picker_path.empty();
            const int count = choose_drive ? int(roots.size()) : int(st.picker_dirs.size()) + 1;
            if (pressed & Up) {
                if (st.picker_row > 0) --st.picker_row;
                else host.Play(Sound::Limit);
            }
            if (pressed & Down) {
                if (st.picker_row + 1 < count) ++st.picker_row;
                else host.Play(Sound::Limit);
            }
            st.picker_row = std::clamp(st.picker_row, 0, std::max(0, count - 1));
            if (pressed & Circle) {
                if (choose_drive) {
                    close_modal(Sound::Back);
                } else if (st.picker_path == st.picker_root) {
                    st.picker_path.clear();
                    st.picker_dirs.clear();
                    st.picker_row = 0;
                    host.Play(Sound::Back);
                } else {
                    const auto pos = st.picker_path.find_last_of('/');
                    const std::string parent = st.picker_path.substr(0, pos);
                    if (parent.size() >= st.picker_root.size() &&
                        parent.compare(0, st.picker_root.size(), st.picker_root) == 0)
                        st.picker_path = parent;
                    else st.picker_path = st.picker_root;
                    st.picker_dirs = R13FolderChoices(st.picker_path);
                    st.picker_row = 0;
                    host.Play(Sound::Back);
                }
                break;
            }
            if (pressed & Cross && choose_drive && count > 0) {
                const Source& source = roots[st.picker_row];
                if (!source.available) {
                    say("USB desconectado ou pasta inacessivel.");
                    host.Play(Sound::Error);
                } else {
                    st.picker_root = source.path;
                    st.picker_path = source.path;
                    st.picker_dirs = R13FolderChoices(st.picker_path);
                    st.picker_row = 0;
                    host.Play(Sound::Select);
                }
                break;
            }
            if (!choose_drive && (pressed & Square || (pressed & Cross && st.picker_row == 0))) {
                const bool ok = host.AddSource(st.picker_path);
                if (ok) st.file_row = int(host.Sources().size()) - 1;
                say(ok ? "Pasta adicionada. Procurando jogos no HD..." :
                         "Nao foi possivel abrir a pasta selecionada.");
                close_modal(ok ? Sound::Select : Sound::Error);
                break;
            }
            if (!choose_drive && (pressed & Cross) && st.picker_row > 0) {
                const std::string next = st.picker_path + "/" + st.picker_dirs[st.picker_row - 1];
                // A removed drive or changed directory cannot be opened.
                if (DIR* check = opendir(next.c_str())) {
                    closedir(check);
                    st.picker_path = next;
                    st.picker_dirs = R13FolderChoices(st.picker_path);
                    st.picker_row = 0;
                    host.Play(Sound::Select);
                } else {
                    say("Pasta inacessivel. Verifique a conexao USB.");
                    host.Play(Sound::Error);
                }
            }
            break;
        }
'''

BROWSER_RENDER = r'''
        case Modal::FolderPicker: {
            Panel(x, 170, 145, 1580, 805);
            const bool choose_drive = st.picker_path.empty();
            canvas.Text(choose_drive ? "Escolha o armazenamento" : "Selecionar pasta de jogos",
                        230, 223, 38, p.title);
            const std::string location = choose_drive ?
                "Armazenamento interno ou HD externo" : st.picker_path;
            canvas.Text(location, 230, 273, 23, p.copy, Align::Left, 1400);
            std::vector<std::pair<std::string, bool>> entries;
            if (choose_drive) {
                for (const Source& source : host.Sources()) {
                    if (!source.removable &&
                        (source.path == "/data/EdenPS4/games" ||
                         source.path.rfind("/mnt/usb", 0) == 0))
                        entries.push_back({source.name + (source.available ? "" : " (desconectado)"),
                                           source.available});
                }
            } else {
                entries.push_back({"Selecionar esta pasta", true});
                for (const auto& name : st.picker_dirs) entries.push_back({name, true});
            }
            const int first = std::clamp(st.picker_row - 5, 0, std::max(0, int(entries.size()) - 7));
            canvas.PushClip(210, 312, 1500, 545);
            for (int i = first; i < std::min(int(entries.size()), first + 7); ++i) {
                const float y = 323 + 75.0f * (i - first);
                Plate(x, 230, y, 1420, 65, i == st.picker_row);
                canvas.Text(entries[i].first, 260, y + 43, 26,
                            !entries[i].second ? p.meta :
                            i == st.picker_row ? p.accent : p.text, Align::Left, 1300);
            }
            canvas.PopClip();
            canvas.Text("Jogos sao indexados no HD sem copiar arquivos grandes.",
                        230, 884, 22, p.copy);
            Footer(x, host, choose_drive ?
                Hints{{"circle", "Voltar"}, {"cross", "Abrir"}} :
                Hints{{"circle", "Pasta anterior"}, {"square", "Selecionar"}, {"cross", "Abrir/Selecionar"}});
            break;
        }
'''


def patch_launcher(source: str) -> str:
    source = once(source, '#include <algorithm>\n',
                  '#include <algorithm>\n#include <dirent.h>\n#include <sys/stat.h>\n', "includes")
    source = once(source,
        'enum class Modal { None, GameInfo, Choice, Power, Keyboard, ConfirmRemove, Order, Test };',
        'enum class Modal { None, GameInfo, Choice, Power, Keyboard, ConfirmRemove, Order, Test, FolderPicker };',
        "modal type")
    source = once(source, '} // namespace\n\nstruct Launcher::State {',
                  BROWSER_HELPER + '\n} // namespace\n\nstruct Launcher::State {',
                  "directory helper")
    source = once(source, '    int file_row{};\n',
                  '    int file_row{};\n'
                  '    std::string picker_root, picker_path;\n'
                  '    std::vector<std::string> picker_dirs;\n'
                  '    int picker_row{};\n', "modal state")
    source = once(source,
                  '        case Modal::Keyboard: {\n            // Rows 0-3:',
                  BROWSER_UPDATE + '        case Modal::Keyboard: {\n            // Rows 0-3:',
                  "update modal")
    source = once(source,
                  '                st.keyboard_text = "/mnt/usb0/";\n'
                  '                st.keyboard_mode = AddFolder; st.keyboard_row = 1; st.keyboard_col = 0;\n'
                  '                st.modal = Modal::Keyboard; st.modal_time = 0; host.Play(Sound::Open);',
                  '                st.picker_root.clear(); st.picker_path.clear();\n'
                  '                st.picker_dirs.clear(); st.picker_row = 0;\n'
                  '                st.modal = Modal::FolderPicker; st.modal_time = 0; host.Play(Sound::Open);',
                  "add-folder button")
    source = once(source, '        case Modal::Keyboard: {\n            const char* prompts[]',
                  BROWSER_RENDER + '        case Modal::Keyboard: {\n            const char* prompts[]',
                  "render modal")
    if 'st.keyboard_text = "/mnt/usb0/";' in source:
        raise RuntimeError("R13 browser must not leave keyboard launch active")
    return source


def patch_scanner(source: str) -> str:
    source = once(source,
        'void ScanFolder(const std::string& folder, int depth, const std::string& source, std::vector<Game>& out) {',
        'void ScanFolder(const std::string& folder, int depth, const std::string& source,\n'
        '                std::vector<Game>& out, size_t& remaining_dirs) {\n'
        '    if (remaining_dirs == 0) return;\n'
        '    --remaining_dirs;', 'scan limit')
    source = once(source, '        if (stat(path.c_str(), &status) != 0) continue;',
                  '        if (lstat(path.c_str(), &status) != 0) continue;', 'skip symlinks')
    source = once(source,
        '    for (const auto& path : subfolders) ScanFolder(path, depth - 1, source, out);',
        '    for (const auto& path : subfolders) {\n'
        '        if (remaining_dirs == 0 || out.size() >= 20000) break;\n'
        '        ScanFolder(path, depth - 1, source, out, remaining_dirs);\n'
        '    }', 'bounded recursion')
    source = once(source, '        ScanFolder(source.path, 1, source.name, games);',
                  '        size_t remaining_dirs = 4096;\n'
                  '        ScanFolder(source.path, 4, source.name, games, remaining_dirs);',
                  'recursive search depth')
    return source


def patch(root: Path):
    ui = root / 'eden/src/yuzu_ps4/ui_launcher.cpp'
    main = root / 'eden/src/yuzu_ps4/main.cpp'
    rendered_ui = patch_launcher(ui.read_text(encoding='utf-8'))
    rendered_main = patch_scanner(main.read_text(encoding='utf-8'))
    ui.write_text(rendered_ui, encoding='utf-8')
    main.write_text(rendered_main, encoding='utf-8')
    print('R13: controller folder picker and bounded recursive USB game scanning integrated')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: patch-r13-usb-browser.py <pinned Eden4 checkout>')
    patch(Path(sys.argv[1]).resolve())
