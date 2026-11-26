#!/usr/bin/env python3
"""R11: don't interpret the PS4 XMB's held X as a game launch;
hold Options + Touchpad to return to the *emulator* HOME menu.

Keeps the pre-existing L3 + R3 + Options emergency shortcut and gamepad
bindings intact. The main UI is always rendered/presented before it is armed.
Applies last to the pinned disposable Eden4 checkout, not to previous PKGs.
"""
from pathlib import Path
import sys

def once(s, old, new, tag):
    hits=s.count(old)
    if hits != 1:
        raise RuntimeError(f"R11 HOME {tag}: expected one source anchor, got {hits}")
    return s.replace(old,new,1)

def patch(root: Path):
    main=root/"eden/src/yuzu_ps4/main.cpp"
    ui=root/"eden/src/yuzu_ps4/ui_launcher.cpp"
    s=main.read_text(encoding="utf8")
    u=ui.read_text(encoding="utf8")
    s=once(s,
        'class MenuInput {\npublic:\n    void Update(',
        'class MenuInput {\npublic:\n'
        '    void Reset() { previous = 0; repeat = 0; }\n'
        '    void Update(', "input reset")
    s=once(s,
        '    while (true) {\n'
        '        HimuraBootTrace("launcher VideoOut begin");\n',
        '    while (true) {\n'
        '        input.Reset();\n'
        '        HimuraBootTrace("launcher VideoOut begin");\n',
        "reset after return to HOME")
    s=once(s,
        '        int launch = -1;\n'
        '        u64 frames = 0;',
        '        int launch = -1;\n'
        '        u64 frames = 0;\n'
        '        // The Cross pressed on PS4 XMB to start our application can still\n'
        '        // be held when the first frame is polled. Never auto-launch a game.\n'
        '        // Show the actual library first, then require a full button release.\n'
        '        bool menu_armed = false;\n'
        '        int release_frames = 0;',
        "first frame gate")
    s=once(s,
        '            input.Update(controller.State(), dt, pressed, held);\n'
        '            host.Poll();',
        '            input.Update(controller.State(), dt, pressed, held);\n'
        '            if (!menu_armed) {\n'
        '                constexpr uint32_t xmb_keys = Ui::Cross | Ui::Circle |\n'
        '                                              Ui::Options | Ui::Triangle;\n'
        '                release_frames = (held & xmb_keys) ? 0 : release_frames + 1;\n'
        '                if (release_frames >= 2) menu_armed = true;\n'
        '                pressed = 0;\n'
        '            }\n'
        '            host.Poll();',
        "prevent phantom launch")
    s=once(s,
        '    constexpr uint32_t exit_buttons = ORBIS_PAD_BUTTON_L3 | ORBIS_PAD_BUTTON_R3 | ORBIS_PAD_BUTTON_OPTIONS;',
        '    constexpr uint32_t exit_buttons = ORBIS_PAD_BUTTON_L3 | ORBIS_PAD_BUTTON_R3 | ORBIS_PAD_BUTTON_OPTIONS;\n'
        '    // One-second deliberate shortcut to leave game, *not* the PS4 app.\n'
        '    // Keep the original L3+R3+Options shortcut as an emergency fallback.\n'
        '    constexpr uint32_t return_buttons = ORBIS_PAD_BUTTON_OPTIONS | ORBIS_PAD_BUTTON_TOUCH_PAD;\n'
        '    std::array<std::chrono::steady_clock::time_point, OrbisFrontend::Controller::MaxPads> return_since{};',
        "safe hotkey")
    s=once(s,
        '            UpdateInput(input, pad, port);\n'
        '            exit_requested |= pad.connected && (pad.buttons & exit_buttons) == exit_buttons;',
        '            UpdateInput(input, pad, port);\n'
        '            exit_requested |= pad.connected && (pad.buttons & exit_buttons) == exit_buttons;\n'
        '            const bool return_held = pad.connected &&\n'
        '                (pad.buttons & return_buttons) == return_buttons;\n'
        '            if (return_held) {\n'
        '                const auto now = std::chrono::steady_clock::now();\n'
        '                if (return_since[port].time_since_epoch().count() == 0) return_since[port] = now;\n'
        '                else if (now - return_since[port] >= std::chrono::seconds{1}) exit_requested = true;\n'
        '            } else {\n'
        '                return_since[port] = {};\n'
        '            }',
        "deliberate per-controller combo")
    s=once(s,
        '            LOG_INFO(Input, "PS4 exit shortcut received");\n'
        '            break;',
        '            LOG_INFO(Input, "PS4 in-game return-to-HOME shortcut received");\n'
        '            R11GameCheckpoint("return to launcher requested");\n'
        '            break;',
        "trace return")
    u=once(u,
        '"L3 + R3 + Options on any controller: close the game and return here."',
        '"Segure Options + Touchpad por 1 s para voltar ao menu (ou L3 + R3 + Options)."',
        "help on controllers")
    # Sanity: guest emulation still performs Pause -> shutdown on break,
    # Launcher() still loops and Ui::Launcher::Returned() resets the screen.
    for required in ('system.ShutdownMainProcess();','ui.Returned(message);',
                     'if (request.kind == Ui::Request::Launch)'):
        if required not in s: raise RuntimeError(f"R11 HOME: upstream flow missing {required}")
    main.write_text(s,encoding="utf8")
    ui.write_text(u,encoding="utf8")
    print("R11 HOME: menu first frame guarded, in-game Options+Touchpad return, original combo retained")

if __name__=="__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r11-home-return.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
