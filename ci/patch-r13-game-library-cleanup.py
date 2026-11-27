#!/usr/bin/env python3
"""R13: hide *clearly marked* Update/DLC package files from the game carousel,
and automatically rediscover game sources when an Orbis USB mount changes.

Never remove/modify any NSP/XCI and never claim to install updates.
"""
from pathlib import Path
import sys

def once(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f"R13 library {label}: expected one anchor, got {c}")
    return s.replace(a,b,1)

FILTER=r'''
// Only explicit filename/folder signals. Never delete anything on disk.
bool R13IsSupplement(const std::string& path) {
    std::string lower=path;
    std::transform(lower.begin(), lower.end(), lower.begin(),
                   [](unsigned char ch){return char(std::tolower(ch));});
    if(lower.size()<4 || lower.substr(lower.size()-4)!=".nsp")return false;
    const auto slash=lower.find_last_of('/');
    const std::string name=slash==std::string::npos?lower:lower.substr(slash+1);
    for(const char* mark:{"[upd]","[update]","(update)","[dlc]","(dlc)","[add-on]",
                          "[patch]","(patch)"," update."," dlc."})
        if(name.find(mark)!=std::string::npos)return true;
    // Known 16-digit program-ID suffixes in conventional NSP names. An update
    // ID usually ends in 800; do not assume arbitrary similar digits are DLC.
    for(size_t i=0;i+18<=name.size();++i){
        if(name[i]!='[' || name[i+17]!=']')continue;
        bool hex=true;
        for(size_t j=i+1;j<i+17;++j)
            if(!std::isxdigit(static_cast<unsigned char>(name[j]))){hex=false;break;}
        if(hex && name.substr(i+14,3)=="800")return true;
    }
    if(lower.find("/updates/")!=std::string::npos ||
       lower.find("/update/")!=std::string::npos ||
       lower.find("/dlc/")!=std::string::npos)return true;
    return false;
}
'''

def patch(root):
    main=root/"eden/src/yuzu_ps4/main.cpp"
    s=main.read_text()
    s=once(s,'bool IsGameFile(const std::string& name) {',
           FILTER+'\nbool IsGameFile(const std::string& name) {','package detector')
    s=once(s,'        if (S_ISREG(status.st_mode) && IsGameFile(name)) {',
           '        if (S_ISREG(status.st_mode) && IsGameFile(name) && !R13IsSupplement(path)) {',
           'only base games shown')
    s=once(s,'    void Begin() {\n        RefreshGames();',
        '''    void Begin() {
        for(int i=0;i<8;++i)
            r13_usb_ready[i]=CanBrowseDirectory("/mnt/usb"+std::to_string(i));
        r13_usb_poll=std::chrono::steady_clock::now()+std::chrono::seconds{3};
        RefreshGames();''','USB initial availability')
    s=once(s,
       '    void Poll() {\n        for (auto& result : metadata.Take()) {',
       '''    void Poll() {
        const auto now=std::chrono::steady_clock::now();
        if(now>=r13_usb_poll){
            r13_usb_poll=now+std::chrono::seconds{3};
            bool changed=false;
            for(int i=0;i<8;++i){
                const bool mounted=CanBrowseDirectory("/mnt/usb"+std::to_string(i));
                if(mounted!=r13_usb_ready[i]){r13_usb_ready[i]=mounted;changed=true;}
            }
            if(changed) {
                LOG_INFO(Frontend,"R13 USB mounts changed: rescan game library");
                RefreshGames();
            }
        }
        for (auto& result : metadata.Take()) {''','USB reconnect refresh')
    s=once(s,'    std::atomic<bool> firmware_busy{false};',
       '''    std::array<bool,8> r13_usb_ready{};
    std::chrono::steady_clock::time_point r13_usb_poll{};
    std::atomic<bool> firmware_busy{false};''','source poll state')
    main.write_text(s)
    print('R13: supplement packages hidden, USB hotplug auto refresh every 3 seconds')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: patch-r13-game-library-cleanup.py <Eden4 checkout>')
    patch(Path(sys.argv[1]).resolve())
