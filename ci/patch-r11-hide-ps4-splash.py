#!/usr/bin/env python3
"""R11: dismiss PS4 system-owned splash AFTER the first real VideoOut flip.

The original shell wallpaper (sce_sys/pic1.png) is not the application's
interactive canvas. The PS4 shell may keep it above the running application
until sceSystemServiceHideSplashScreen() is called. Preserve both icon0 and
pic1; fix hand-off from system splash to live Samurai HOME instead.

OpenOrbis's Piglet sample calls this same function. The Eden4 target already
links SceSystemService and loads the internal SystemService module.
"""
from pathlib import Path
import sys

def replace_once(src, before, after, label):
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"R11 shell splash {label}: expected 1 anchor, found {n}")
    return src.replace(before, after, 1)

def main(root: Path):
    source = root / "eden/src/yuzu_ps4/platform.cpp"
    cmake = root / "eden/src/yuzu_ps4/CMakeLists.txt"
    s = source.read_text(encoding="utf-8")
    target = cmake.read_text(encoding="utf-8")
    if "SceSystemService" not in target:
        raise RuntimeError("R11 shell splash: executable does not link SceSystemService")
    if "ORBIS_SYSMODULE_INTERNAL_SYSTEM_SERVICE" not in s:
        raise RuntimeError("R11 shell splash: SystemService module not loaded")
    if "sceSystemServiceHideSplashScreen" in s:
        raise RuntimeError("R11 shell splash: already patched")

    s = replace_once(s, "#include <stdexcept>\n",
                        "#include <stdexcept>\n"
                        "#include <cstdio>\n"
                        "#include <orbis/SystemService.h>\n",
                        "header from OpenOrbis SDK")

    # The preceding R11 VideoOut patch has already inserted the first-frame
    # log, so insert immediately after the actual completed Present() flip.
    anchor = ('    if (flips <= 3)\n'
              '        LOG_INFO(Frontend, "R11 HOME VideoOut frame {} visible, mode {}", flips - 1, mode.name);\n')
    addition = (
        '    // A successful flipArg alone does not dismiss the PS4 system splash.\n'
        '    // Hide it only after a real HOME framebuffer has been presented.\n'
        '    static bool shell_splash_hidden = false;\n'
        '    static unsigned shell_hide_attempts = 0;\n'
        '    if (!shell_splash_hidden && shell_hide_attempts < 4 &&\n'
        '        (flips == 2 || (flips > 2 && (flips - 2) % 60 == 0))) {\n'
        '        const int status = sceSystemServiceHideSplashScreen();\n'
        '        ++shell_hide_attempts;\n'
        '        shell_splash_hidden = status >= 0;\n'
        '        LOG_INFO(Frontend, "R11 PS4 splash handoff attempt {} returned {:#x}",\n'
        '                 shell_hide_attempts, static_cast<uint32_t>(status));\n'
        '        if (std::FILE* log = std::fopen("/data/EdenPS4/HIMURA_R11_SPLASH_STATUS.txt", "a")) {\n'
        '            std::fprintf(log, "HideSplashScreen attempt %u result 0x%08x success=%d\\n",\n'
        '                         shell_hide_attempts, static_cast<unsigned>(status),\n'
        '                         static_cast<int>(shell_splash_hidden));\n'
        '            std::fclose(log);\n'
        '        }\n'
        '    }\n'
    )
    s = replace_once(s, anchor, anchor + addition, "post-VideoOut splash handoff")
    s = replace_once(s,
        '"R11 HOME VideoOut frame {} visible, mode {}"',
        '"R11 HOME VideoOut frame {} flip completed, mode {}"',
        "honest VideoOut log wording")
    source.write_text(s, encoding="utf-8")
    print("R11: PS4 system splash is dismissed only after successful HOME VideoOut flip")
    print("R11: diagnostic: /data/EdenPS4/HIMURA_R11_SPLASH_STATUS.txt")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r11-hide-ps4-splash.py <pinned Eden4 checkout>")
    main(Path(sys.argv[1]).resolve())
