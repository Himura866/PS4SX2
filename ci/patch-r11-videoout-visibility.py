#!/usr/bin/env python3
"""R11 PS4: diagnose visible HOME frames and fix Vulkan flip completion test.

The PS4 XMB "pic1.png" is a *shell wallpaper*, never an in-app overlay.
The user hears UI navigation while only that wallpaper is visible, so add a
separate early VideoOut frame and durable phase logs for objective diagnosis.
Never replace the live carousel with a static screenshot.
"""
from pathlib import Path
import sys

def replace_once(src,old,new,label):
    n=src.count(old)
    if n!=1:
        raise RuntimeError(f"R11 VideoOut {label}: expected one anchor, found {n}")
    return src.replace(old,new,1)

def patch(root: Path):
    main=root/"eden/src/yuzu_ps4/main.cpp"
    platform=root/"eden/src/yuzu_ps4/platform.cpp"
    swapchain=root/"eden/src/video_core/renderer_vulkan/vk_swapchain_ps4.cpp"
    s=main.read_text(encoding="utf8")
    p=platform.read_text(encoding="utf8")
    v=swapchain.read_text(encoding="utf8")

    # PS4 keeps displaying the PKG pic1.png until SystemService releases its
    # splash layer. A successful VideoOut flip alone does not prove it is visible.
    s=replace_once(s,
        'extern "C" int sceSystemServiceLoadExec(const char*, char* const[]);',
        'extern "C" int sceSystemServiceHideSplashScreen();\n'
        'extern "C" int sceSystemServiceLoadExec(const char*, char* const[]);',
        "PS4 splash system service declaration")

    # Distinguish "still seeing PS4 shell wallpaper" from HOME scanning
    # stalls and failures to create or submit the first VideoOut frame.
    s=replace_once(s,
        '        HimuraBootTrace("launcher canvas OK");\n'
        '        HimuraBootTrace("launcher host.Begin begin");',
        '        HimuraBootTrace("launcher canvas OK");\n'
        '        // Prove VideoOut has taken over before metadata, audio or games\n'
        '        // scanning can delay the real interactive HOME.  Not a fake menu.\n'
        '        canvas->Clear({0x080d1b});\n'
        '        canvas->Text("HIMURA SWITCH PS4  |  Preparando biblioteca",\n'
        '                     960, 520, 40, {0xffffff}, Ui::Align::Center);\n'
        '        HimuraBootTrace("launcher first VideoOut submit begin");\n'
        '        display->Present(canvas->Pixels());\n'
        '        // PS4 SystemService owns the PKG splash; release it after the first frame.\n'
        '        const int hide_splash_result = sceSystemServiceHideSplashScreen();\n'
        '        LOG_INFO(Frontend, "R11 hide PS4 splash result: {:#x}", static_cast<u32>(hide_splash_result));\n'
        '        HimuraBootTrace(hide_splash_result < 0 ? "launcher splash hide FAILED" : "launcher splash hidden");\n'
        '        HimuraBootTrace("launcher first VideoOut submit OK");\n'
        '        HimuraBootTrace("launcher host.Begin begin");',
        "first visible HOME frame")
    s=replace_once(s,
        '            ui.Render(*canvas);\n'
        '            if (frames == 0) LOG_INFO(Frontend, "PS4 HOME menu: first present");',
        '            ui.Render(*canvas);\n'
        '            if (frames == 0) HimuraBootTrace("launcher interactive HOME rendered");\n'
        '            if (frames == 0) LOG_INFO(Frontend, "PS4 HOME menu: first present");',
        "interactive frame checkpoint")

    # Guarantee writes to write-combined VideoOut memory have been ordered
    # before submitting their flip to the PS4 scanout engine.
    p=replace_once(p,
        '    if (!Flip())\n        throw std::runtime_error{"PS4 launcher display flip failed"};',
        '    __builtin_ia32_sfence();\n'
        '    if (!Flip())\n'
        '        throw std::runtime_error{"PS4 launcher display flip failed"};',
        "VideoOut write-combine ordering")
    p=replace_once(p,
        '    if (!Flip())\n        throw std::runtime_error{"PS4 launcher display flip failed"};\n}',
        '    if (!Flip())\n'
        '        throw std::runtime_error{"PS4 launcher display flip failed"};\n'
        '    if (flips <= 3)\n'
        '        LOG_INFO(Frontend, "R11 HOME VideoOut frame {} visible, mode {}", flips - 1, mode.name);\n'
        '}',
        "VideoOut first frame log")

    # VideoOut flipArg records *last completed* flip. A buffer whose last
    # flipArg equals that value has already been released. Original > is wrong.
    v=replace_once(v,
        '            if (status.flipArg > previous) { available = true; break; }',
        '            if (status.flipArg >= previous) { available = true; break; }',
        "Vulkan buffer release condition")
    v=replace_once(v,
        '            LOG_ERROR(Render_Vulkan, "PS4 display did not release buffer {}", image_index);',
        '            LOG_ERROR(Render_Vulkan, "PS4 display did not release buffer {} (flipArg={})",\n'
        '                      image_index, previous);',
        "swapchain timeout details")

    for path,data in ((main,s),(platform,p),(swapchain,v)):
        path.write_text(data,encoding="utf8")
    print("R11: visible HOME frame before scanning; correct Vulkan completed-flip comparison; CPU scanout ordering")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch-r11-videoout-visibility.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
