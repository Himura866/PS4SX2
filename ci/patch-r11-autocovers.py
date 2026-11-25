#!/usr/bin/env python3
"""R11: reliable offline cover caching, without initializing a guest Core::System.

Embedded NSP/XCI icons are still cached when the original Eden loader launches
that game. Before first launch, optional .jpg/.png sidecar art next to an NSP/XCI
is imported automatically. The original Eden4 notes that loading NSP/XCI from
the menu metadata worker crashed on PS4; never repeat that unsafe approach.
"""
from pathlib import Path
import sys

def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise RuntimeError("R11 auto covers %s: expected 1 anchor, found %d" % (label,n))
    return s.replace(old,new,1)

HEADERS = r'''
#include <string>
#include <vector>
'''

EXTRACT = r'''
// R11: stable import of user-provided sidecar JPEG/PNG artwork only.
// Never initialise the guest CPU/Core::System from the menu metadata thread:
// Eden4 00.26 did that and crashed. The real embedded icon remains cached by
// RunGame's Metadata::Store after the first launch (unchanged).
bool ImportSidecar(const Metadata::Entry& entry, Info& info) {
    if (entry.path.empty()) return false;
    const auto slash = entry.path.find_last_of('/');
    const auto dot = entry.path.find_last_of('.');
    const bool has_ext = dot != std::string::npos &&
                         (slash == std::string::npos || dot > slash);
    const std::string stem = has_ext ? entry.path.substr(0, dot) : entry.path;
    const std::vector<std::string> candidates{
        entry.path + ".jpg", entry.path + ".png",
        stem + ".jpg", stem + ".jpeg", stem + ".png"
    };
    for (const std::string& path : candidates) {
        FILE* file = std::fopen(path.c_str(), "rb");
        if (!file) continue;
        bool ok = std::fseek(file, 0, SEEK_END) == 0;
        const long size = ok ? std::ftell(file) : -1;
        ok = ok && size > 16 && size < (8L << 20) &&
             std::fseek(file, 0, SEEK_SET) == 0;
        std::vector<uint8_t> bytes;
        if (ok) {
            bytes.resize(static_cast<size_t>(size));
            ok = std::fread(bytes.data(), 1, bytes.size(), file) == bytes.size();
        }
        std::fclose(file);
        if (!ok) continue;
        // PNG/JPEG validation is performed by Ui::DecodeImage as before.
        const std::string name = stem.substr(
            stem.find_last_of('/') == std::string::npos ? 0 : stem.find_last_of('/') + 1);
        info = Info{name, 0, std::move(bytes)};
        return true;
    }
    return false;
}
'''

def main(root):
    p=root/"eden/src/yuzu_ps4/ui_metadata.cpp"
    s=p.read_text(encoding="utf8")
    s=once(s, '#include "yuzu_ps4/ui_metadata.h"',
           '#include "yuzu_ps4/ui_metadata.h"\n'+HEADERS,"includes")
    s=once(s, '\nvoid WriteCache(const std::string& path, const Info& info) {',
           '\n'+EXTRACT+'\nvoid WriteCache(const std::string& path, const Info& info) {',
           "reader")
    s=once(s,
           '    size_t cached = 0;\n    for (size_t index = 0; index < entries.size() && !stop; ++index) {\n        const Entry& entry = entries[index];\n        Info info;\n        if (entry.path.empty() || !ReadCache(CachePath(entry), info)) continue;\n        ++cached;',
           '    size_t cached = 0, extracted = 0;\n    for (size_t index = 0; index < entries.size() && !stop; ++index) {\n        const Entry& entry = entries[index];\n        Info info;\n        if (entry.path.empty()) continue;\n        const bool cache_hit = ReadCache(CachePath(entry), info);\n        if (cache_hit && !info.icon.empty()) {\n            ++cached;\n        } else {\n            Info from_game;\n            if (ImportSidecar(entry, from_game)) {\n                info = std::move(from_game);\n                WriteCache(CachePath(entry), info);\n                ++extracted;\n            } else if (cache_hit) {\n                ++cached;\n            } else {\n                continue;\n            }\n        }',
           "cache and fallback")
    s=once(s,
           '    LOG_INFO(Frontend, "PS4 HOME menu: {} of {} games have saved icons (the others get theirs when started)",\n             cached, entries.size());',
           '    LOG_INFO(Frontend, "R11 covers: {} cached, {} sidecars imported, {} games",\n             cached, extracted, entries.size());',
           "log summary")
    p.write_text(s,encoding="utf8")
    print("R11: safe cached covers and local sidecars patched",p)

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r11-autocovers.py <checkout>")
    main(Path(sys.argv[1]).resolve())
