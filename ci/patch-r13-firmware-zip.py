#!/usr/bin/env python3
"""R13 firmware ZIP picker: controller input -> queued real streaming NAND importer.

Applied AFTER patch-r13-fps-toggle-no-clock; modifies native PS4 launcher and
CMake; preserves existing user's keys/saves/installed firmware and sources.
"""
from pathlib import Path
import sys,shutil,os

def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f"Firmware ZIP {label}: expected one anchor, got {n}")
    return s.replace(a,b,1)

HELPER=r'''
struct R13FirmwareItem { std::string name; bool folder{}; };
std::vector<R13FirmwareItem> R13FirmwareEntries(const std::string& folder) {
    std::vector<R13FirmwareItem> result;
    DIR* dir=opendir(folder.c_str());
    if (!dir) return result;
    while (const dirent* item=readdir(dir)) {
        const std::string name=item->d_name;
        if(name.empty() || name[0]=='.' || name==".." || name.size()>200 ||
           name.find('/')!=std::string::npos || name.find('\\')!=std::string::npos) continue;
        const std::string full=folder+"/"+name;
        struct stat st{};
        if(lstat(full.c_str(),&st)!=0)continue;
        if(S_ISDIR(st.st_mode))result.push_back({name,true});
        else if(S_ISREG(st.st_mode) && name.size()>4){
            std::string ending=name.substr(name.size()-4);
            std::transform(ending.begin(),ending.end(),ending.begin(),
                           [](unsigned char ch){return char(std::tolower(ch));});
            if(ending==".zip")result.push_back({name,false});
        }
        if(result.size()>=256)break;
    }
    closedir(dir);
    std::sort(result.begin(),result.end(),[](const auto& a,const auto& b){
        if(a.folder!=b.folder)return a.folder>b.folder;
        return a.name<b.name;
    });
    return result;
}
'''
UPDATE=r'''
        case Modal::FirmwarePicker: {
            std::vector<Source> roots;
            roots.push_back({"Armazenamento interno", "/data/EdenPS4",true,true,false,0});
            for(const Source& source:host.Sources())
                if(!source.removable && source.path.rfind("/mnt/usb",0)==0)
                    roots.push_back(source);
            const bool choose_root=st.firmware_path.empty();
            const int count=choose_root?int(roots.size()):int(st.firmware_items.size());
            if(pressed & Up){if(st.firmware_row>0)--st.firmware_row;else host.Play(Sound::Limit);}
            if(pressed & Down){if(st.firmware_row+1<count)++st.firmware_row;else host.Play(Sound::Limit);}
            st.firmware_row=std::clamp(st.firmware_row,0,std::max(0,count-1));
            if(pressed & Circle) {
                if(choose_root)close_modal(Sound::Back);
                else if(st.firmware_path==st.firmware_root){
                    st.firmware_path.clear();st.firmware_items.clear();st.firmware_row=0;
                    host.Play(Sound::Back);
                } else {
                    const size_t pos=st.firmware_path.find_last_of('/');
                    const std::string parent=st.firmware_path.substr(0,pos);
                    if(parent.size()>=st.firmware_root.size() &&
                       parent.compare(0,st.firmware_root.size(),st.firmware_root)==0)
                        st.firmware_path=parent;
                    else st.firmware_path=st.firmware_root;
                    st.firmware_items=R13FirmwareEntries(st.firmware_path);
                    st.firmware_row=0;host.Play(Sound::Back);
                }
                break;
            }
            if((pressed & Cross) && count>0){
                if(choose_root){
                    const Source& selected=roots[st.firmware_row];
                    if(!selected.available){say("USB desconectado ou inacessivel.");host.Play(Sound::Error);}
                    else{
                        st.firmware_root=selected.path;st.firmware_path=selected.path;
                        st.firmware_items=R13FirmwareEntries(st.firmware_path);
                        st.firmware_row=0;host.Play(Sound::Open);
                    }
                }else{
                    const R13FirmwareItem selected=st.firmware_items[st.firmware_row];
                    const std::string next=st.firmware_path+"/"+selected.name;
                    if(selected.folder) {
                        DIR* check=opendir(next.c_str());
                        if(!check){say("Pasta USB inacessivel.");host.Play(Sound::Error);}
                        else {
                            closedir(check);st.firmware_path=next;
                            st.firmware_items=R13FirmwareEntries(next);
                            st.firmware_row=0;host.Play(Sound::Select);
                        }
                    }else{
                        const bool queued=host.InstallFirmwareZip(next);
                        say(queued?"Firmware ZIP: verificando e instalando. Acompanhe o estado nesta tela.":
                                   "Instalacao ja em andamento; aguarde terminar.");
                        close_modal(queued?Sound::Select:Sound::Error);
                    }
                }
            }
            break;
        }
'''
RENDER=r'''
        case Modal::FirmwarePicker: {
            Panel(x,170,145,1580,805);
            const bool choose_root=st.firmware_path.empty();
            canvas.Text(choose_root?"Escolha USB ou armazenamento":"Selecionar firmware ZIP",
                        230,223,36,p.title);
            canvas.Text(choose_root?"Navegue com o controle":st.firmware_path,
                        230,273,23,p.copy,Align::Left,1400);
            std::vector<std::pair<std::string,bool>> choices;
            if(choose_root){
                choices.push_back({"Armazenamento interno",true});
                for(const Source& source:host.Sources())
                    if(!source.removable && source.path.rfind("/mnt/usb",0)==0)
                        choices.push_back({source.name+(source.available?"":" (desconectado)"),source.available});
            }else{
                for(const auto& item:st.firmware_items)
                    choices.push_back({item.name+(item.folder?" /":"  [ZIP]"),true});
            }
            const int first=std::clamp(st.firmware_row-5,0,std::max(0,int(choices.size())-7));
            canvas.PushClip(210,312,1500,545);
            for(int i=first;i<std::min(int(choices.size()),first+7);++i){
                const float y=323+75.0f*(i-first);
                Plate(x,230,y,1420,65,i==st.firmware_row);
                canvas.Text(choices[i].first,260,y+43,26,
                            !choices[i].second?p.meta:
                            i==st.firmware_row?p.accent:p.text,Align::Left,1300);
            }
            canvas.PopClip();
            canvas.Text("O ZIP e verificado por CRC; suas chaves e saves nao sao alterados.",
                        230,884,22,p.copy);
            Footer(x,host,Hints{{"circle","Voltar"},{"cross","Abrir / Instalar"}});
            break;
        }
'''

def patch(root):
    ui=root/"eden/src/yuzu_ps4/ui_launcher.cpp"
    hdr=root/"eden/src/yuzu_ps4/ui_launcher.h"
    main=root/"eden/src/yuzu_ps4/main.cpp"
    cmake=root/"eden/src/yuzu_ps4/CMakeLists.txt"
    preview=root/"eden/ps4/ui-preview/preview.cpp"
    u=ui.read_text();h=hdr.read_text();m=main.read_text();c=cmake.read_text()
    v=preview.read_text()

    h=once(h,'    virtual std::string ExportLogs() = 0;',
        '    virtual bool InstallFirmwareZip(const std::string& path) = 0;\n'
        '    virtual std::string FirmwareImportStatus() = 0;\n'
        '    virtual std::string ExportLogs() = 0;', 'Host methods')

    u=once(u,'#include <dirent.h>\n', '#include <dirent.h>\n#include <cctype>\n', 'cctype include')
    u=once(u,'enum class Modal { None, GameInfo, Choice, Power, Keyboard, ConfirmRemove, Order, Test, FolderPicker };',
        'enum class Modal { None, GameInfo, Choice, Power, Keyboard, ConfirmRemove, Order, Test, FolderPicker, FirmwarePicker };','modal type')
    u=once(u,'} // namespace\n\nstruct Launcher::State {',
           HELPER+'} // namespace\n\nstruct Launcher::State {','browse helper')
    u=once(u,'    int picker_row{};\n',
           '    int picker_row{};\n'
           '    std::string firmware_root, firmware_path;\n'
           '    std::vector<R13FirmwareItem> firmware_items;\n'
           '    int firmware_row{};\n','file state')
    u=once(u,'        case Modal::FolderPicker: {\n            // Empty path',
           UPDATE+'        case Modal::FolderPicker: {\n            // Empty path','modal update')
    u=once(u,'        case Modal::FolderPicker: {\n            Panel(x, 170, 145, 1580, 805);',
           RENDER+'        case Modal::FolderPicker: {\n            Panel(x, 170, 145, 1580, 805);','modal render')
    count_anchor='const int count = int(sources.size()) + 1;'
    assert u.count(count_anchor)==2, 'source row count has changed'
    u=u.replace(count_anchor,'const int count = int(sources.size()) + 2;')
    u=once(u,'        const bool add = st.file_row >= int(sources.size());\n',
        '        const bool add = st.file_row == int(sources.size());\n'
        '        const bool install = st.file_row == int(sources.size()) + 1;\n','input add row')
    u=once(u,'        if (pressed & Triangle) { say(host.ExportLogs()); host.Play(Sound::Select); }\n'
        '        if (pressed & Cross) {\n            if (add) {\n',
        '        if (pressed & Triangle) { say(host.ExportLogs()); host.Play(Sound::Select); }\n'
        '        if (pressed & Cross) {\n'
        '            if (install) {\n'
        '                st.firmware_root.clear();st.firmware_path.clear();\n'
        '                st.firmware_items.clear();st.firmware_row=0;\n'
        '                st.modal=Modal::FirmwarePicker;st.modal_time=0;host.Play(Sound::Open);\n'
        '            } else if (add) {\n','input start installer')
    u=once(u,'        if (!add && (pressed & Square)) {\n'
        '            if (sources[st.file_row].removable && host.RemoveSource(st.file_row)) {',
        '        if (!add && !install && (pressed & Square)) {\n'
        '            if (sources[st.file_row].removable && host.RemoveSource(st.file_row)) {',
        'prevent out of bounds when ZIP row selected')
    u=once(u,'            const Source& source = sources[i];\n',
        '            if(i==int(sources.size())+1){\n'
        '                canvas.MaskCentered("folder_small",150,y+39,here?p.accent:p.text,0.8f);\n'
        '                canvas.Text("Instalar firmware ZIP",190,y+48,26,here?p.accent:p.text);\n'
        '                continue;\n'
        '            }\n'
        '            const Source& source = sources[i];\n','render firmware row')
    u=once(u,'        const bool add = st.file_row >= int(sources.size());\n',
        '        const bool add = st.file_row == int(sources.size());\n'
        '        const bool install = st.file_row == int(sources.size()) + 1;\n','render row state')
    u=once(u,'        Footer(x, host, add ? Hints{{"options", "Atualizar"},',
        '        Footer(x, host, install ? Hints{{"circle", "Voltar"}, {"cross", "Instalar ZIP"}} :\n'
        '                      add ? Hints{{"options", "Atualizar"},','render footer')
    # PTBR patch maps complete literals; if old anchor differs, fail closed.
    u=once(u,'        if (!st.message.empty()) canvas.Text(st.message, 844, 900, 22, p.accent, Align::Left, 950);',
        '        canvas.Text(host.FirmwareImportStatus(),844,846,22,p.copy,Align::Left,960);\n'
        '        if (!st.message.empty()) canvas.Text(st.message, 844, 900, 22, p.accent, Align::Left, 950);',
        'installer status')

    if os.getenv('R13_FW_STOP_AFTER') == 'ui':
        print('PASS: firmware picker UI anchors confirmed')
        return
    m=once(m,'#include <memory>\n','#include <memory>\n#include <mutex>\n','mutex include')
    m=once(m,'#include "yuzu_ps4/ui_launcher.h"\n',
        '#include "yuzu_ps4/ui_launcher.h"\n#include "yuzu_ps4/r13_firmware_zip.h"\n','zip import')
    m=once(m,'    void End() {\n        metadata.Stop();',
        '    void End() {\n'
        '        // Never start guest emulation while firmware NAND files are changing.\n'
        '        if(firmware_thread.joinable())firmware_thread.join();\n'
        '        metadata.Stop();','join installer before game boot')
    m=once(m,'    std::string ExportLogs() override { return ::ExportLogs(); }',
        '''    bool InstallFirmwareZip(const std::string& path) override {
        if(firmware_busy.load())return false;
        if(firmware_thread.joinable())firmware_thread.join();
        firmware_busy.store(true);
        {std::lock_guard<std::mutex> lock(firmware_mutex);
         firmware_status="Lendo ZIP, verificando indice...";}
        firmware_thread=std::thread([this,path]{
            std::string result;
            try {
                result=HimuraFirmware::InstallZip(path,[this](size_t done,size_t total){
                    std::lock_guard<std::mutex> lock(firmware_mutex);
                    firmware_status="Firmware: "+std::to_string(done)+"/"+
                                    std::to_string(total)+" NCAs verificados";
                });
            } catch(const std::exception& e) { result=std::string("Falha na instalacao: ")+e.what(); }
            catch(...) {result="Falha ao extrair firmware ZIP";}
            {std::lock_guard<std::mutex> lock(firmware_mutex);
             firmware_status=result;}
            firmware_busy.store(false);
        });
        return true;
    }
    std::string FirmwareImportStatus() override {
        std::lock_guard<std::mutex> lock(firmware_mutex);
        return firmware_status;
    }
    std::string ExportLogs() override { return ::ExportLogs(); }''','Host implementation')
    m=once(m,'    OrbisFrontend::Controller& controller;\n',
        '''    std::atomic<bool> firmware_busy{false};
    std::thread firmware_thread;
    std::mutex firmware_mutex;
    std::string firmware_status{"Firmware: selecione o ZIP na opcao abaixo"};
    OrbisFrontend::Controller& controller;
''','Host state')
    m=once(m,'    explicit PsHost(OrbisFrontend::Controller& controller_) : controller{controller_} {\n',
        '''    ~PsHost() override { if(firmware_thread.joinable())firmware_thread.join(); }
    explicit PsHost(OrbisFrontend::Controller& controller_) : controller{controller_} {
''','thread lifecycle')
    if os.getenv('R13_FW_STOP_AFTER') == 'main':
        print('PASS: firmware picker UI and main native host anchors confirmed')
        return
    c=once(c,'add_executable(eden-ps4 main.cpp platform.cpp',
           'add_executable(eden-ps4 main.cpp r13_firmware_zip.cpp platform.cpp',
           'CMake compilation')
    v=once(v,'    std::string ExportLogs() override { return "Logs copied to USB."; }',
        '    bool InstallFirmwareZip(const std::string&) override { return false; }\n'
        '    std::string FirmwareImportStatus() override { return "Firmware ZIP so existe no PS4"; }\n'
        '    std::string ExportLogs() override { return "Logs copied to USB."; }','preview Host implementation')
    # Stage exact source under the Eden4 checkout, no network or runtime libraries.
    package=Path(__file__).resolve().parent
    dst=root/"eden/src/yuzu_ps4"
    shutil.copyfile(package/"r13_firmware_zip.cpp",dst/"r13_firmware_zip.cpp")
    shutil.copyfile(package/"r13_firmware_zip.h",dst/"r13_firmware_zip.h")
    ui.write_text(u);hdr.write_text(h);main.write_text(m);cmake.write_text(c)
    preview.write_text(v)
    print('R13 firmware ZIP picker integrated with native PS4 UI and zlib importer')

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r13-firmware-zip.py <Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
