#!/usr/bin/env python3
"""R11: read actual NSP/XCI artwork automatically, without launching the game.

Patch is applied only to a disposable, pinned Eden4 checkout in the R11 job.
Uses Eden's own loader and game keys; no internet covers and no synthetic artwork.
"""
from pathlib import Path
import sys

def once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise RuntimeError("R11 auto covers %s: expected 1 anchor, found %d" % (label,n))
    return s.replace(old,new,1)

HEADERS = r'''
#include "core/core.h"
#include "core/file_sys/registered_cache.h"
#include "core/file_sys/vfs/vfs_real.h"
#include "core/loader/loader.h"
'''

EXTRACT = r'''
// Attempt to read the container's Control NCA using the existing Eden loader.
// No guest CPU, GPU, audio, or executable is started; results are cached on disk.
// This runs in the existing metadata worker thread, one title at a time.
bool ExtractFromContainer(const Metadata::Entry& entry, Info& info) {
    if (entry.path.empty()) return false;
    try {
        Core::System system;
        system.SetContentProvider(std::make_unique<FileSys::ContentProviderUnion>());
        system.SetFilesystem(std::make_shared<FileSys::RealVfsFilesystem>());
        system.GetFileSystemController().CreateFactories(*system.GetFilesystem());
        const auto file = system.GetFilesystem()->OpenFile(entry.path, FileSys::OpenMode::Read);
        if (!file) return false;
        auto loader = Loader::GetLoader(system, file);
        if (!loader) return false;
        std::vector<u8> icon;
        if (loader->ReadIcon(icon) != Loader::ResultStatus::Success || icon.empty() ||
            icon.size() >= (8u << 20)) {
            return false;
        }
        std::string title;
        u64 program_id{};
        void(loader->ReadTitle(title));
        void(loader->ReadProgramId(program_id));
        info = Info{std::move(title), program_id, std::move(icon)};
        return true;
    } catch (const std::exception& ex) {
        LOG_WARNING(Frontend, "R11 auto icon skipped {}: {}", entry.path, ex.what());
    } catch (...) {
        LOG_WARNING(Frontend, "R11 auto icon skipped {}", entry.path);
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
           '    size_t cached = 0, extracted = 0;\n    for (size_t index = 0; index < entries.size() && !stop; ++index) {\n        const Entry& entry = entries[index];\n        Info info;\n        if (entry.path.empty()) continue;\n        const bool cache_hit = ReadCache(CachePath(entry), info);\n        if (cache_hit && !info.icon.empty()) {\n            ++cached;\n        } else {\n            Info from_game;\n            if (ExtractFromContainer(entry, from_game)) {\n                info = std::move(from_game);\n                WriteCache(CachePath(entry), info);\n                ++extracted;\n            } else if (cache_hit) {\n                ++cached;\n            } else {\n                continue;\n            }\n        }',
           "cache and fallback")
    s=once(s,
           '    LOG_INFO(Frontend, "PS4 HOME menu: {} of {} games have saved icons (the others get theirs when started)",\n             cached, entries.size());',
           '    LOG_INFO(Frontend, "R11 covers: {} cached, {} extracted, {} games",\n             cached, extracted, entries.size());',
           "log summary")
    p.write_text(s,encoding="utf8")
    print("R11: automatic offline NSP/XCI icons patched",p)

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r11-autocovers.py <checkout>")
    main(Path(sys.argv[1]).resolve())
