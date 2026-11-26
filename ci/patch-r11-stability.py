#!/usr/bin/env python3
"""R11 conservative PS4 stability defaults and persistent per-game crash checkpoints.

Avoid unsafe driver modifications, external keys or runtime access, cache format
changes and forced FPS. Saved ps4.ini settings always continue to take precedence.
"""
from pathlib import Path
import sys

def once(s, old, new, label):
    n=s.count(old)
    if n!=1: raise RuntimeError(f"R11 stability {label}: expected one anchor, found {n}")
    return s.replace(old,new,1)

TRACE=r'''
// One write per loading stage, never in the render hot path; useful even if a
// fatal PS4 exception prevents eden.log from flushing. All errors are ignored.
void R11GameCheckpoint(const char* step, const char* detail=nullptr, bool reset=false) noexcept {
    FILE* out=std::fopen("/data/EdenPS4/HIMURA_R13_GAME_STATUS.txt",reset?"w":"a");
    if(!out)return;
    std::fprintf(out,"R13 %s",step);
    if(detail) std::fprintf(out," | %.240s",detail);
    std::fputc('\n',out);
    std::fflush(out);
    ::fsync(::fileno(out));
    std::fclose(out);
}
'''
def main(root):
    p=root/"eden/src/yuzu_ps4/main.cpp"
    s=p.read_text(encoding="utf8")
    s=once(s,
        'constexpr char Version[] = "1.0";',
        TRACE+'\nconstexpr char Version[] = "1.0";',
        "trace helper after boot trace")
    # Default to Handheld (720p guest resolution) for NEW settings files. If
    # user already chose Docked, LoadOptions() preserves that preference.
    s=once(s,
        '{"docked", "Modo do console",\n'
        '     "Docked: games render at up to 1080p. Handheld: 720p, less GPU work and memory (faster).", "display",\n'
        '     {{"1", "Docked"}, {"0", "Handheld"}}},',
        '{"docked", "Console mode",\n'
        '      "Portatil: usa 720p e menos memoria/GPU. TV: ate 1080p, exige mais desempenho.", "display",\n'
        '      {{"0", "Portatil (recomendado)"}, {"1", "Modo TV"}}},',
        "safe default mode")
    s=once(s,
        '    LOG_INFO(Frontend, "Launching {}", game.path);',
        '    R11GameCheckpoint("launch begin",game.path.c_str(),true);\n'
        '    LOG_INFO(Frontend, "Launching {}", game.path);',
        "launch trace")
    s=once(s,
        '    Core::System system;\n    system.Initialize();',
        '    R11GameCheckpoint("creating guest system");\n'
        '    Core::System system;\n    system.Initialize();\n'
        '    R11GameCheckpoint("guest system initialized");',
        "guest system trace")
    s=once(s,
        '    const auto result = system.Load(window, game.path, parameters);',
        '    R11GameCheckpoint("begin container load");\n'
        '    const auto result = system.Load(window, game.path, parameters);\n'
        '    R11GameCheckpoint("container load returned");',
        "loader trace")
    s=once(s,
        '        LOG_ERROR(Frontend, "Eden load failed: status={:#x}, path={}", u32(result), game.path);',
        '        R11GameCheckpoint("container load rejected");\n'
        '        LOG_ERROR(Frontend, "Eden load failed: status={:#x}, path={}", u32(result), game.path);',
        "load fail trace")
    s=once(s,
        '    system.GPU().Start();\n    system.GetCpuManager().OnGpuReady();\n    void(system.Run());',
        '    R11GameCheckpoint("container accepted; starting GPU");\n'
        '    Common::PS4Diagnostics::LogDirectMemory("R11 before GPU start");\n'
        '    system.GPU().Start();\n'
        '    R11GameCheckpoint("GPU start returned");\n'
        '    system.GetCpuManager().OnGpuReady();\n'
        '    R11GameCheckpoint("guest CPU ready; entering game");\n'
        '    void(system.Run());\n'
        '    R11GameCheckpoint("guest emulation running");',
        "gpu and cpu trace")
    s=once(s,
        '    std::atomic<u64> frontend_ticks{0};',
        '    bool r11_first_composite=false, r11_first_flip=false;\n'
        '    std::atomic<u64> frontend_ticks{0};',
        "display trace flags")
    s=once(s,
        '        frontend_ticks.fetch_add(1, std::memory_order_relaxed);\n        controller.Read();',
        '        frontend_ticks.fetch_add(1, std::memory_order_relaxed);\n'
        '        if(!r11_first_composite && Common::PS4Diagnostics::composites.load()>0){\n'
        '            r11_first_composite=true;\n'
        '            R11GameCheckpoint("first guest frame reached renderer");\n'
        '        }\n'
        '        if(!r11_first_flip && Common::PS4Diagnostics::flips.load()>0){\n'
        '            r11_first_flip=true;\n'
        '            R11GameCheckpoint("first game frame submitted to TV");\n'
        '        }\n'
        '        controller.Read();',
        "first video frame checkpoints")
    # Low-frequency, crash-resilient checkpoint for the cutscene -> gameplay
    # transition. The already-existing ten-second status cadence avoids
    # disk writes on individual frames. These counters do not claim game FPS.
    s=once(s,
        '        if (now >= next_status) {\\n            LOG_INFO(Frontend,',
        '        if (now >= next_status) {\\n'
        '            char r13_state[192];\\n'
        '            std::snprintf(r13_state, sizeof(r13_state),\\n'
        '                "quadros_compostos=%llu video=%llu audio=%llu memoria_extra_mib=%llu",\\n'
        '                static_cast<unsigned long long>(Common::PS4Diagnostics::composites.load()),\\n'
        '                static_cast<unsigned long long>(Common::PS4Diagnostics::flips.load()),\\n'
        '                static_cast<unsigned long long>(Common::PS4Diagnostics::audio_buffers.load()),\\n'
        '                static_cast<unsigned long long>(ps4_heap_overflow_size() >> 20));\\n'
        '            R11GameCheckpoint("andamento do jogo (10 s)", r13_state);\\n'
        '            LOG_INFO(Frontend,',
        "R13 ten-second crash checkpoint")
    s=once(s,
        '    LOG_INFO(Frontend, "Stopping emulation");',
        '    R11GameCheckpoint("stopping emulation");\n'
        '    LOG_INFO(Frontend, "Stopping emulation");',
        "shutdown trace")
    s=once(s,
        '    LOG_INFO(Frontend, "Emulation shutdown complete");',
        '    R11GameCheckpoint("emulation shutdown complete");\n'
        '    LOG_INFO(Frontend, "Emulation shutdown complete");',
        "shutdown complete")
    s=once(s,
        '        } catch (const std::exception& error) {\n            LOG_ERROR(Frontend, "Launch failure: {}", error.what());',
        '        } catch (const std::exception& error) {\n'
        '            R11GameCheckpoint("caught launch exception",error.what());\n'
        '            LOG_ERROR(Frontend, "Launch failure: {}", error.what());',
        "caught crash")
    p.write_text(s,encoding="utf8")
    print("R11: safe default handheld, per-game load, GPU, display and shutdown checkpoints")

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r11-stability.py <Eden4 checkout>")
    main(Path(sys.argv[1]).resolve())
