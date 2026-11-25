#!/usr/bin/env python3
"""Instrument pinned Eden4 startup. Runs only on CI's disposable checkout."""
import sys
from pathlib import Path

TRACE = r'''
// HIMURA R10: persistent diagnostics, independent of the normal Eden logger.
void HimuraBootTrace(const char* phase, const char* detail = nullptr) noexcept {
    FILE* file = std::fopen("/data/EdenPS4/HIMURA_R10_BOOT.txt", "a");
    if (!file) return;
    std::fprintf(file, "R10 %s", phase);
    if (detail) std::fprintf(file, " | %.300s", detail);
    std::fputc('\n', file);
    std::fflush(file);
    ::fsync(::fileno(file));
    std::fclose(file);
}
'''
MAIN = r'''int main() {
    mkdir("/data/EdenPS4", 0777);
    mkdir("/data/EdenPS4/games", 0777);
    HimuraBootTrace("00 boot started");
    const char* stage = "settings";
    bool logger_started = false;
    bool failed = false;
    try {
        HimuraBootTrace("01 settings begin");
        SetDefaults();
        HimuraBootTrace("01 settings OK");
        stage = "log";
        Common::Log::Initialize();
        Common::Log::Start();
        logger_started = true;
        HimuraBootTrace("02 log OK");
        LOG_INFO(Frontend, "Eden4 {} - HIMURA R10 boot diagnostics", Version);
        LOG_INFO(Frontend, "Host CPU: {}, AVX={}, AVX2={}, page size={}",
                 Common::g_cpu_caps.cpu_string, Common::g_cpu_caps.avx,
                 Common::g_cpu_caps.avx2, sysconf(_SC_PAGESIZE));
        LOG_INFO(Frontend, "PS4 Pro mode: {}, CPUs: {}, CPU clock: {} MHz, direct memory: {} MiB",
                 sceKernelIsNeoMode() ? "on" : "off", sysconf(_SC_NPROCESSORS_ONLN),
                 sceKernelGetCpuFrequency() / 1000000, sceKernelGetDirectMemorySize() >> 20);
        HimuraBootTrace("03 CPU reported");
        stage = "CreateEdenPaths";
        HimuraBootTrace("04 paths begin");
        Common::FS::CreateEdenPaths();
        HimuraBootTrace("04 paths OK");
        stage = "InitializeModules";
        HimuraBootTrace("05 modules begin");
        OrbisFrontend::InitializeModules();
        HimuraBootTrace("05 modules OK");
        stage = "Controller";
        HimuraBootTrace("06 controller begin");
        OrbisFrontend::Controller controller;
        HimuraBootTrace("06 controller OK");
        stage = "Launcher";
        HimuraBootTrace("07 launcher begin");
        Launcher(controller);
        HimuraBootTrace("07 launcher returned normally");
    } catch (const std::exception& error) {
        failed = true;
        HimuraBootTrace(stage, error.what());
        if (logger_started)
            LOG_CRITICAL(Frontend, "R10 startup failed at {}: {}", stage, error.what());
    } catch (...) {
        failed = true;
        HimuraBootTrace(stage, "unknown C++ exception");
        if (logger_started)
            LOG_CRITICAL(Frontend, "R10 startup failed at {}: unknown exception", stage);
    }
    HimuraBootTrace(failed ? "08 ERROR: returning to XMB" : "08 normal return");
    if (logger_started) Common::Log::Stop();
    HimuraBootTrace("09 calling sceSystemServiceLoadExec");
    sceSystemServiceLoadExec("exit", nullptr);
    return failed ? 1 : 0;
}
'''

def once(data, old, new):
    n = data.count(old)
    if n != 1:
        raise RuntimeError("R10 source mismatch at %s (%s occurrences)" % (old[:45], n))
    return data.replace(old, new, 1)

if len(sys.argv) != 2:
    raise SystemExit("usage: patch-r10-boot-trace.py <Eden4 checkout>")
p = Path(sys.argv[1]) / "eden/src/yuzu_ps4/main.cpp"
s = p.read_text(encoding="utf8")
s = once(s, 'namespace {\nconstexpr char Version[] = "1.0";',
            'namespace {\n' + TRACE + '\nconstexpr char Version[] = "1.0";')
start = s.index("int main() {")
end = s.index("\n#define VMA_IMPLEMENTATION", start)
old_main = s[start:end]
for needle in ["OrbisFrontend::InitializeModules();", "Launcher(controller);",
               'sceSystemServiceLoadExec("exit", nullptr);']:
    if old_main.count(needle) != 1:
        raise RuntimeError("Unexpected Eden4 main: " + needle)
s = s[:start] + MAIN + s[end:]
for old, new in [
    ('void Launcher(OrbisFrontend::Controller& controller) {\n    PsHost host{controller};',
     'void Launcher(OrbisFrontend::Controller& controller) {\n    HimuraBootTrace("launcher host begin");\n    PsHost host{controller};\n    HimuraBootTrace("launcher host OK");'),
    ('    Ui::Launcher ui{host};\n    MenuInput input;',
     '    HimuraBootTrace("launcher UI begin");\n    Ui::Launcher ui{host};\n    HimuraBootTrace("launcher UI OK");\n    MenuInput input;'),
    ('        auto display = std::make_unique<OrbisFrontend::Display>();',
     '        HimuraBootTrace("launcher VideoOut begin");\n        auto display = std::make_unique<OrbisFrontend::Display>();\n        HimuraBootTrace("launcher VideoOut OK");'),
    ('        auto canvas = std::make_unique<Ui::Canvas>();\n        host.Begin();',
     '        HimuraBootTrace("launcher canvas begin");\n        auto canvas = std::make_unique<Ui::Canvas>();\n        HimuraBootTrace("launcher canvas OK");\n        HimuraBootTrace("launcher host.Begin begin");\n        host.Begin();\n        HimuraBootTrace("launcher host.Begin OK");'),
    ('            if (request.kind == Ui::Request::Exit) {\n                host.End();',
     '            if (request.kind == Ui::Request::Exit) {\n                HimuraBootTrace("launcher UI requested exit");\n                host.End();'),
    ('            if (++frames == 1) LOG_INFO(Frontend, "PS4 HOME menu: first frame shown");',
     '            if (++frames == 1) {\n                LOG_INFO(Frontend, "PS4 HOME menu: first frame shown");\n                HimuraBootTrace("launcher first frame OK");\n            }')
]:
    s = once(s, old, new)
p.write_text(s, encoding="utf8")
print("R10 startup checkpoints added:", p)
