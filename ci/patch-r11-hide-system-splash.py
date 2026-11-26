#!/usr/bin/env python3
"""R11: release the real PS4 system boot splash after the first VideoOut frame.

Important: PS4 XMB's sce_sys/pic1.png is NOT drawn by the emulator. Orbis
holds its splash until the app explicitly calls sceSystemServiceHideSplashScreen.
The menu already renders/accepts input according to real PS4 boot logs, yet
the user only sees pic1. OpenOrbis officially uses this API to unmask the app.
Preserves the approved external artwork and all actual in-app UI.
"""
from pathlib import Path
import sys

def once(src, old, new, name):
    n=src.count(old)
    if n != 1:
        raise RuntimeError(f"PS4 hide splash {name}: one anchor required, found {n}")
    return src.replace(old, new, 1)

def patch(root: Path):
    main=root/"eden/src/yuzu_ps4/main.cpp"
    cmake=root/"eden/src/yuzu_ps4/CMakeLists.txt"
    if not main.is_file() or not cmake.is_file():
        raise RuntimeError("Missing Eden4 launcher source or link recipe")
    source=main.read_text(encoding="utf8")
    links=cmake.read_text(encoding="utf8")
    if "SceSystemService" not in links:
        raise RuntimeError("SceSystemService must be linked before using HideSplashScreen")
    source=once(source,
        '#include "yuzu_ps4/platform.h"',
        '#include <orbis/SystemService.h>\n#include "yuzu_ps4/platform.h"',
        "SystemService declaration")
    source=once(source,
        '        HimuraBootTrace("launcher first VideoOut submit OK");\n'
        '        HimuraBootTrace("launcher host.Begin begin");',
        '        HimuraBootTrace("launcher first VideoOut submit OK");\n'
        '        // OpenOrbis: successful VideoOut flips do NOT dismiss Orbis XMB\n'
        '        // startup artwork by themselves. Explicitly release shell splash\n'
        '        // ONLY after we have a valid application frame. Leave icon0/pic1\n'
        '        // untouched on XMB; do not paint those files as live HOME widgets.\n'
        '        HimuraBootTrace("launcher hide PS4 system splash begin");\n'
        '        const int32_t splash_rc = sceSystemServiceHideSplashScreen();\n'
        '        if (splash_rc >= 0) {\n'
        '            HimuraBootTrace("launcher PS4 system splash HIDDEN");\n'
        '            LOG_INFO(Frontend, "R11 system splash hidden: {:#x}", u32(splash_rc));\n'
        '        } else {\n'
        '            HimuraBootTrace("launcher PS4 system splash HIDE FAILED");\n'
        '            LOG_ERROR(Frontend, "R11 system splash hide failed: {:#x}", u32(splash_rc));\n'
        '        }\n'
        '        HimuraBootTrace("launcher host.Begin begin");',
        "first real framebuffer followed by splash dismissal")
    if "ui.Render(*canvas);" not in source or "display->Present(canvas->Pixels());" not in source:
        raise RuntimeError("Launcher rendering/presentation was lost")
    main.write_text(source, encoding="utf8")
    print("R11: real SystemService splash dismissed after first VideoOut submit; existing menu intact")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch-r11-hide-system-splash.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
