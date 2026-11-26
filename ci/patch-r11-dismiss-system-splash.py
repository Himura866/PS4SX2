#!/usr/bin/env python3
"""R11 PS4: explicitly dismiss the native XMB loading splash on the first
successfully presented framebuffer.

Symptoms: PS4 app responds to D-pad/audio/game launch while the pkg's
pic1.png remains in front of the interactive HOME. The official OpenOrbis
piglet sample calls sceSystemServiceHideSplashScreen() explicitly. Eden4
already loads ORBIS_SYSMODULE_INTERNAL_SYSTEM_SERVICE in InitializeModules()
and links both SceSysmodule and SceSystemService. It never called HideSplash.

Hide only after the first completed VideoOut flip so HOME is ready behind it;
log each result, retry at most three times if the OS temporarily rejects it.
The external approved XMB icon and pic1 assets are not changed.
"""
from pathlib import Path
import sys

def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f"R11 splash {label}: expected once, got {n}")
    return s.replace(old,new,1)

def patch(root: Path):
    path=root/"eden/src/yuzu_ps4/platform.cpp"
    cmake=root/"eden/src/yuzu_ps4/CMakeLists.txt"
    s=path.read_text(encoding="utf8")
    libs=cmake.read_text(encoding="utf8")
    if "SceSysmodule SceSystemService" not in libs:
        raise RuntimeError("R11 splash: required OpenOrbis system-service libraries not linked")
    if "ORBIS_SYSMODULE_INTERNAL_SYSTEM_SERVICE" not in s:
        raise RuntimeError("R11 splash: system service not initialized")
    if "sceSystemServiceHideSplashScreen" in s:
        raise RuntimeError("R11 splash: method unexpectedly already present")
    s=once(s,
        '#include <orbis/Sysmodule.h>\n',
        '#include <orbis/Sysmodule.h>\n#include <orbis/SystemService.h>\n',
        "system service header")
    s=once(s,
        '    if (flips <= 3)\n'
        '        LOG_INFO(Frontend, "R11 HOME VideoOut frame {} visible, mode {}", flips - 1, mode.name);\n'
        '}',
        '    if (flips <= 3)\n'
        '        LOG_INFO(Frontend, "R11 HOME VideoOut frame {} visible, mode {}", flips - 1, mode.name);\n'
        '\n'
        '    // The PS4 shell keeps pic1.png visible until the title dismisses its\n'
        '    // own splash; VideoOut flips alone do not always remove that overlay.\n'
        '    // Hide only after a real UI frame has been presented and accepted.\n'
        '    static bool splash_hidden = false;\n'
        '    static unsigned splash_attempts = 0;\n'
        '    if (!splash_hidden && splash_attempts < 3) {\n'
        '        ++splash_attempts;\n'
        '        const int result = sceSystemServiceHideSplashScreen();\n'
        '        LOG_INFO(Frontend, "R11 system splash hide attempt {}: {:#x}", splash_attempts, u32(result));\n'
        '        splash_hidden = result >= 0;\n'
        '    }\n'
        '}',
        "first successful VIDEOOUT frame")
    path.write_text(s,encoding="utf8")
    print("R11: call sceSystemServiceHideSplashScreen after first successful VideoOut frame")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch-r11-dismiss-system-splash.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
