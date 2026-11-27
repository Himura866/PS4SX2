#!/usr/bin/env python3
"""Instrument C++ OOM failures without changing memory allocations or gameplay.

This is diagnostic ONLY. It does not claim a fix for bad_alloc.
Applied last on a disposable pinned Eden4 checkout, not on main or New Eden.
"""
from pathlib import Path
import shutil,sys

def once(source,old,new,label):
    count=source.count(old)
    if count!=1: raise RuntimeError(f"R13 OOM probe {label}: expected 1 anchor, found {count}")
    return source.replace(old,new,1)

NEW_HANDLER=r'''
// Diagnose std::operator new failure, even on an emulation worker thread.
// This handler never dynamically allocates; it rethrows the standard error.
void R13OOMNewHandler() {
    static std::atomic_flag reported = ATOMIC_FLAG_INIT;
    if (!reported.test_and_set(std::memory_order_relaxed)) {
        HimuraMemoryProbe::Append("/data/EdenPS4/HIMURA_R13_OOM.txt",
            "operator_new", Common::PS4Diagnostics::stage.load(std::memory_order_relaxed),
            0, 0,
            Common::PS4Diagnostics::composites.load(std::memory_order_relaxed),
            Common::PS4Diagnostics::flips.load(std::memory_order_relaxed),
            ps4_heap_overflow_size() >> 20);
    }
    throw std::bad_alloc{};
}
'''

def patch(root: Path):
    main=root/"eden/src/yuzu_ps4/main.cpp"
    memory=root/"eden/src/common/host_memory.cpp"
    s=main.read_text(encoding="utf-8")
    h=memory.read_text(encoding="utf-8")

    s=once(s,'#include "yuzu_ps4/ui_launcher.h"\n',
       '#include "yuzu_ps4/ui_launcher.h"\n'
       '#include "yuzu_ps4/r13_memory_failure_probe.h"\n'
       '#include <new>\n','safe handler includes')
    s=once(s,'constexpr char Version[] = "1.0";',
           NEW_HANDLER+'\nconstexpr char Version[] = "1.0";','nonallocating handler placement')
    s=once(s,'int main() {\n    mkdir("/data/EdenPS4", 0777);',
       'int main() {\n    mkdir("/data/EdenPS4", 0777);\n'
       '    std::set_new_handler(R13OOMNewHandler);', 'install handler at boot')
    # Guest direct memory can fail without invoking operator new. Capture the
    # requested size and kernel code before throwing the pre-existing bad_alloc.
    h=once(h,'#include "common/host_memory.h"\n',
       '#include "common/host_memory.h"\n'
       '#ifdef __OPENORBIS__\n'
       '#include "yuzu_ps4/r13_memory_failure_probe.h"\n'
       '#endif\n',
       'direct allocation include')
    h=once(h,
       '        if (result != 0) {\n'
       '            LOG_CRITICAL(HW_Memory, "PS4 guest RAM allocation of {} MiB failed: {:#x}",',
       '        if (result != 0) {\n'
       '            HimuraMemoryProbe::Append("/data/EdenPS4/HIMURA_R13_OOM.txt",\n'
       '                "guest_RAM_direct_alloc", "sceKernelAllocateDirectMemory",\n'
       '                allocated_size, static_cast<uint32_t>(result), 0, 0, 0);\n'
       '            LOG_CRITICAL(HW_Memory, "PS4 guest RAM allocation of {} MiB failed: {:#x}",',
       'guest RAM allocation')
    h=once(h,
       '        if (result != 0) {\n'
       '            sceKernelReleaseDirectMemory(physical, allocated_size);',
       '        if (result != 0) {\n'
       '            HimuraMemoryProbe::Append("/data/EdenPS4/HIMURA_R13_OOM.txt",\n'
       '                "guest_RAM_map", "sceKernelMapDirectMemory",\n'
       '                allocated_size, static_cast<uint32_t>(result), 0, 0, 0);\n'
       '            sceKernelReleaseDirectMemory(physical, allocated_size);',
       'guest RAM mapping')

    package=Path(__file__).resolve().parent
    shutil.copyfile(package/"r13_memory_failure_probe.h",
                    root/"eden/src/yuzu_ps4/r13_memory_failure_probe.h")
    main.write_text(s,encoding="utf-8")
    memory.write_text(h,encoding="utf-8")
    print("R13: nonallocating bad_alloc / PS4 guest RAM direct-memory OOM tracing integrated")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch-r13-memory-oom-probe.py <Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
