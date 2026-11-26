#!/usr/bin/env python3
"""PS4 foreground display: use the same logged-in user as the working controller.

Prefer the signed-in user for both HOME and Vulkan, with the original system
user as a fallback on consoles that reject opening the port for that user.
"""
from pathlib import Path
import sys

def once(s,old,new,label):
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"HIMURA R12 VideoOut {label}: expected one anchor, got {n}")
    return s.replace(old,new,1)

def patch(root):
    platform=root/"eden/src/yuzu_ps4/platform.cpp"
    game=root/"eden/src/video_core/renderer_vulkan/vk_swapchain_ps4.cpp"
    p=platform.read_text(encoding="utf8")
    g=game.read_text(encoding="utf8")

    p=once(p,
       '    video = sceVideoOutOpen(0xff, 0, 0, nullptr);',
       '    // A system-user VideoOut can submit successful flips without being\n'
       '    // the logged-in game user\\x27s foreground display. The DS4 already\n'
       '    // uses this initial user; the HOME must use the same identity.\n'
       '    OrbisUserServiceUserId display_user{-1};\n'
       '    const int user_result = sceUserServiceGetInitialUser(&display_user);\n'
       '    if (user_result >= 0 && display_user >= 0) {\n'
       '        video = sceVideoOutOpen(display_user, 0, 0, nullptr);\n'
       '        if (video < 0)\n'
       '            LOG_WARNING(Frontend, "R12 HOME VideoOut: user port open failed {:#x}", u32(video));\n'
       '    }\n'
       '    if (video < 0) {\n'
       '        LOG_INFO(Frontend, "R12 HOME VideoOut: using system port fallback");\n'
       '        video = sceVideoOutOpen(0xff, 0, 0, nullptr);\n'
       '    }',
       "foreground HOME output")

    g=once(g,
       '#include <orbis/VideoOut.h>',
       '#include <orbis/VideoOut.h>\n#include <orbis/UserService.h>',
       "game includes")
    g=once(g,
       '    ps4->video = sceVideoOutOpen(0xff, 0, 0, nullptr);',
       '    // Use the same signed-in PS4 user as Controller and HOME VideoOut;\n'
       '    // 0xff denotes system user and may not own the visible TV layer.\n'
       '    OrbisUserServiceUserId display_user{-1};\n'
       '    const int user_result = sceUserServiceGetInitialUser(&display_user);\n'
       '    if (user_result >= 0 && display_user >= 0) {\n'
       '        ps4->video = sceVideoOutOpen(display_user, 0, 0, nullptr);\n'
       '        if (ps4->video < 0)\n'
       '            LOG_WARNING(Render_Vulkan, "R12 game VideoOut: user port open failed {:#x}", u32(ps4->video));\n'
       '    }\n'
       '    if (ps4->video < 0) {\n'
       '        LOG_INFO(Render_Vulkan, "R12 game VideoOut: using system port fallback");\n'
       '        ps4->video = sceVideoOutOpen(0xff, 0, 0, nullptr);\n'
       '    }',
       "foreground game output")

    for path,value in ((platform,p),(game,g)):
        path.write_text(value,encoding="utf8")
    print("R12: HOME and Vulkan prefer the signed-in PS4 user with a system port fallback")

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: patch-r12-active-user-videoout.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
