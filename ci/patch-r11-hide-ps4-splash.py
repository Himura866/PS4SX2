#!/usr/bin/env python3
"""Fix PS4 shell's boot splash persisting above an otherwise working launcher.

Source evidence: PS4 HOME audio/game input works, R10 boot log shows VideoOut
flips and rendered HOME, but pic1.png remains visibly stuck after launch.
The OpenOrbis piglet sample explicitly hides the shell splash using
sceSystemServiceHideSplashScreen() after loading the SystemService module.
Eden4 already loads that module and links SceSystemService, but never calls it.

This patch hides the PS4 shell splash ONLY AFTER the first successful launcher
Present(); preserves sce_sys/pic1.png and actual Samurai HOME artwork.
"""
from pathlib import Path
import sys

def replace_once(src, before, after, label):
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"R11 PS4 splash fix {label}: expected one anchor; found {n}")
    return src.replace(before, after, 1)

def main(root: Path):
    platform = root / "eden/src/yuzu_ps4/platform.cpp"
    cmake = root / "eden/src/yuzu_ps4/CMakeLists.txt"
    src = platform.read_text(encoding="utf-8")
    link = cmake.read_text(encoding="utf-8")
    if "SceSystemService" not in link or "ORBIS_SYSMODULE_INTERNAL_SYSTEM_SERVICE" not in src:
        raise RuntimeError("R11 splash fix: cannot prove SystemService load and link")
    if "sceSystemServiceHideSplashScreen" in src:
        raise RuntimeError("R11 splash fix: HideSplashScreen already exists (avoid double patch)")

    src = replace_once(src,
        '#include <stdexcept>\n',
        '#include <stdexcept>\n#include <cstdio>\n',
        "headers")
    src = replace_once(src,
        'namespace OrbisFrontend {\n',
        '// OpenOrbis libSceSystemService; linked by eden/src/yuzu_ps4/CMakeLists.txt.\n'
        '// The PS4 shell splash is distinct from the app\\'s samurai menu background.\n'
        'extern "C" int sceSystemServiceHideSplashScreen(void);\n\n'
        'namespace OrbisFrontend {\n',
        "export")
    src = replace_once(src,
        '    if (!Flip())\n'
        '        throw std::runtime_error{"PS4 launcher display flip failed"};\n'
        '}\n',
        '    if (!Flip())\n'
        '        throw std::runtime_error{"PS4 launcher display flip failed"};\n'
        '    // The PS4 launcher keeps sce_sys/pic1.png as a system-owned splash\n'
        '    // until explicitly dismissed. A successful VideoOut flip is NOT\n'
        '    // sufficient (the menu can be alive behind the splash with sound).\n'
        '    // Do this only after a REAL frame was flipped. Do not alter pic1.png.\n'
        '    static bool splash_hidden = false;\n'
        '    static unsigned attempts = 0;\n'
        '    if (!splash_hidden && attempts < 4) {\n'
        '        ++attempts;\n'
        '        const int result = sceSystemServiceHideSplashScreen();\n'
        '        splash_hidden = result >= 0;\n'
        '        LOG_INFO(Frontend, "R11 PS4 shell splash dismissal attempt {}: {:#x}",\n'
        '                 attempts, static_cast<uint32_t>(result));\n'
        '        if (std::FILE* log = std::fopen("/data/EdenPS4/HIMURA_R11_SPLASH_STATUS.txt", "a")) {\n'
        '            std::fprintf(log, "HideSplashScreen attempt %u result 0x%08x hidden=%d\\n",\n'
        '                         attempts, static_cast<unsigned>(result), int(splash_hidden));\n'
        '            std::fclose(log);\n'
        '        }\n'
        '    }\n'
        '}\n',
        "dismiss after successful VideoOut present")
    platform.write_text(src, encoding="utf-8")
    print("R11 shell splash dismissal installed after first completed launcher present, without changing pic1.png")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r11-hide-ps4-splash.py <pinned Eden4 checkout>")
    main(Path(sys.argv[1]).resolve())
