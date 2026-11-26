#!/usr/bin/env bash
# HIMURA SWITCH PS4 R11: independent preflight (no PS4 SDK required).
# An actionable failed step is printed before the expensive cross-build.
set -Eeuo pipefail
ROOT="$(pwd)"
BASE="$ROOT/.r11-smoke/eden4"
mkdir -p "$BASE"
trap 'echo "R11 preflight FAILED at $BASH_COMMAND (line $LINENO)" >&2' ERR

echo "R11 preflight: syntax"
bash -n ci/build-r11-samurai-library.sh
for py in ci/patch-eden4-credits.py ci/patch-r10-switch-toolbar.py \
 ci/patch-r11-samurai-library.py ci/patch-r11-theme-cache.py ci/patch-r11-autocovers.py ci/patch-r11-fps.py \
 ci/generate-r11-branding.py ci/patch-r11-authorship.py ci/patch-r10-boot-trace.py \
 ci/patch-r11-stability.py ci/patch-r11-approved-menu.py ci/patch-r11-home-return.py \
 ci/patch-r11-videoout-visibility.py ci/patch-r11-build-cache.py ci/patch-r12-active-user-videoout.py; do
  python3 -m py_compile "$py"
done

echo "R11 preflight: download exact pinned patch targets"
python3 - "$BASE" <<'PY'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
from urllib.request import urlopen
root=Path(sys.argv[1])
sha="fab246cbac93c7995aaf451dca83ae93ba0bd234"
paths=[
  "eden/src/yuzu_ps4/ui_launcher.cpp",
  "eden/src/yuzu_ps4/platform.cpp",
  "eden/src/video_core/renderer_vulkan/vk_swapchain_ps4.cpp",
  "eden/src/yuzu_ps4/ui_canvas.h",
  "eden/src/yuzu_ps4/ui_canvas.cpp",
  "eden/src/yuzu_ps4/ui_metadata.cpp",
  "eden/src/yuzu_ps4/main.cpp",
  "eden/src/common/ps4_diagnostics.h",
  "eden/src/common/stb.h",
  "eden/src/video_core/renderer_vulkan/vk_present_manager.cpp",
  "eden/src/video_core/renderer_vulkan/vk_present_manager.h",
  "eden/src/video_core/vulkan_common/vulkan_wrapper.h",
  "eden/ps4/ui-preview/preview.cpp",
  "eden/ps4/build.sh",
]
def fetch(path):
    output=root/path
    output.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://raw.githubusercontent.com/xatyy/Eden4/{sha}/{path}"
    data=urlopen(url,timeout=60).read()
    if not data: raise RuntimeError(f"empty source file: {path}")
    output.write_bytes(data)
    print("Fetched:",path,flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(fetch, paths))
PY

echo "R11 preflight: all patches in packaging order"
for patch in patch-eden4-credits patch-r10-switch-toolbar patch-r11-samurai-library patch-r11-theme-cache \
 patch-r11-autocovers patch-r11-fps generate-r11-branding patch-r11-authorship \
 patch-r10-boot-trace patch-r11-stability patch-r11-approved-menu patch-r11-home-return \
 patch-r11-videoout-visibility patch-r12-active-user-videoout; do
  echo "APPLY $patch"
  python3 "ci/$patch.py" "$BASE"
done

echo "R11 preflight: complete theme/assets and safe metadata"
test -s "$BASE/branding/icon0.png"
test -s "$BASE/branding/pic1.png"
test -s "$BASE/branding/himura-r11-menu.png"
grep -Fq '$STAGE/skin/himura-r11-menu.png' "$BASE/eden/ps4/build.sh"
grep -Fq '/app0/skin/himura-r11-menu.png' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fxq '#define STBI_ONLY_PNG 1' "$BASE/eden/src/common/stb.h"
grep -Fxq '#define STBI_ONLY_JPEG 1' "$BASE/eden/src/common/stb.h"
test -s "$BASE/branding/HIMURA-ATTRIBUTION.txt"
grep -Fq 'POD DO HIMURA' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'canvas.CopyOpaque(cached_background)' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'void Canvas::CopyOpaque' "$BASE/eden/src/yuzu_ps4/ui_canvas.cpp"
grep -Fq 'R11GameCheckpoint' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'bool menu_armed = false' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'constexpr uint32_t return_buttons' "$BASE/eden/src/yuzu_ps4/main.cpp"
echo 'R11 preflight: verify VideoOut takeover and corrected Vulkan flip completion'
grep -Fq 'launcher first VideoOut submit OK' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'launcher interactive HOME rendered' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq '__builtin_ia32_sfence()' "$BASE/eden/src/yuzu_ps4/platform.cpp"
grep -Fq 'status.flipArg >= previous' "$BASE/eden/src/video_core/renderer_vulkan/vk_swapchain_ps4.cpp"
echo 'R12 preflight: splash dismissal follows the first interactive presentation'
python3 - "$BASE" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1]) / "eden/src"
main = (root / "yuzu_ps4/main.cpp").read_text()
render = main.index('HimuraBootTrace("launcher interactive HOME rendered")')
present = main.index('display->Present(canvas->Pixels())', render)
first_frame = main.index('if (++frames == 1)', present)
hide = main.index('const int result = sceSystemServiceHideSplashScreen()', first_frame)
assert main.count('sceSystemServiceHideSplashScreen()') == 2
assert present < first_frame < hide

for filename, handle in [
    ("yuzu_ps4/platform.cpp", "video"),
    ("video_core/renderer_vulkan/vk_swapchain_ps4.cpp", "ps4->video"),
]:
    source = (root / filename).read_text()
    lookup = source.index('sceUserServiceGetInitialUser(&display_user)')
    primary = source.index(f'{handle} = sceVideoOutOpen(display_user,', lookup)
    fallback_guard = source.index(f'if ({handle} < 0) {{', primary)
    fallback = source.index(f'{handle} = sceVideoOutOpen(0xff,', fallback_guard)
    assert lookup < primary < fallback_guard < fallback
    assert source.count('sceVideoOutOpen(0xff,') == 1
PY
if grep -Fq 'status.flipArg > previous' "$BASE/eden/src/video_core/renderer_vulkan/vk_swapchain_ps4.cpp"; then
 echo 'ERROR: stale Vulkan flip condition can cause a timeout' >&2; exit 34
fi
echo 'R13 preflight: approved wallpaper, five localized masks, working focus and version label'
if grep -Fq 'c.FillRoundRect(94, 434, 1732, 406' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"; then
  echo 'R13 preflight ERROR: opaque wide panel still hides samurai art' >&2
  exit 36
fi
grep -Fq 'c.DrawImage(picture, 0, 0);' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'c.FillRoundRect(137, 437, 349, 364' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'c.FillRoundRect(1478, 450, 317, 330' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'c.Text("R13", 728, 164, 35' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'R11NeonCover(canvas, left, TileTop, TileSize, st.time)' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'else start(st.game_focus);' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'case 5: st.modal = Modal::Power;' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
echo "R11 preflight: validate diagnostic path argument is C-compatible"
grep -Fq 'R11GameCheckpoint("launch begin",game.path.c_str(),true);' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq '{"docked", "Modo do console",' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq '"Portatil (recomendado)"' "$BASE/eden/src/yuzu_ps4/main.cpp"
if grep -Fq '{"docked", "Console mode",' "$BASE/eden/src/yuzu_ps4/main.cpp"; then
  echo 'R13 preflight ERROR: console setting not translated' >&2
  exit 37
fi
# R13: the final patched binary must expose durable diagnostics in Portuguese.
# It is not enough for the Python patch itself to mention these features.
grep -Fq 'HIMURA_R13_GAME_STATUS.txt' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq '"crash.log", "samples.log", "HIMURA_R13_GAME_STATUS.txt"' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'andamento do jogo (10 s)' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'quadros_compostos=%llu video=%llu audio=%llu memoria_extra_mib=%llu' "$BASE/eden/src/yuzu_ps4/main.cpp"
if grep -Fq 'HIMURA_R11_GAME_STATUS.txt' "$BASE/eden/src/yuzu_ps4/main.cpp"; then
    echo 'R13 preflight ERROR: outdated crash checkpoint file path' >&2
    exit 35
fi
if grep -Fq 'R11GameCheckpoint("launch begin",game.path,true);' "$BASE/eden/src/yuzu_ps4/main.cpp"; then
   echo "R11 preflight ERROR: std::string passed as const char* without c_str()" >&2
   exit 32
fi
grep -Fq 'R11PaintFps' "$BASE/eden/src/video_core/renderer_vulkan/vk_present_manager.cpp"
echo "R11 preflight: Vulkan FPS memory API must match pinned Eden4 dispatch"
python3 - "$BASE" <<'PY'
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])
renderer=(root/"eden/src/video_core/renderer_vulkan/vk_present_manager.cpp").read_text()
dispatch=(root/"eden/src/video_core/vulkan_common/vulkan_wrapper.h").read_text()
assert "api.vkGetBufferMemoryRequirements2(" in renderer, "R11 must query buffer memory with Vulkan 1.1"
assert "api.vkGetBufferMemoryRequirements(" not in renderer, "obsolete Vulkan call must be absent"
used=set(re.findall(r"api\.(vk[A-Za-z0-9_]+)\s*\(",renderer))
available=set(re.findall(r"PFN_(vk[A-Za-z0-9_]+)\s+\1",dispatch))
missing=sorted(used-available)
if missing:
    raise RuntimeError("R11 Vulkan dispatcher has no such methods: "+", ".join(missing))
print("R11 Vulkan dispatch resolved:", ", ".join(sorted(used)))
PY
if grep -Fq 'Core::System system;' "$BASE/eden/src/yuzu_ps4/ui_metadata.cpp"; then
   echo "R11 preflight ERROR: unsafe guest initialisation in the metadata worker" >&2
   exit 31
fi

echo "R11 preflight: generated packaging recipe, no toolchain run"
python3 - <<'PY'
from pathlib import Path
import subprocess
import sys
source=Path("ci/build-r11-samurai-library.sh").read_text()
mark="<<'PY'\n"
start=source.index(mark)+len(mark)
end=source.index("\nPY\n",start)
subprocess.run([sys.executable,"-","ci/build-r08-eden4-pkg.sh",
                "ci/.r11-build-generated.sh"],input=source[start:end],
               text=True,check=True)
PY
python3 ci/patch-r11-build-cache.py ci/.r11-build-generated.sh
bash -n ci/.r11-build-generated.sh
grep -Fq 'R11_CACHE_V1' ci/.r11-build-generated.sh
grep -Fq 'R11_DEPS_ONLY' ci/.r11-build-generated.sh
grep -Fq 'R11_PKG_ONLY' ci/.r11-build-generated.sh
grep -Fq 'EDEN4_VERSION="01.13"' ci/.r11-build-generated.sh
grep -Fq 'EDEN_PKG_SUFFIX="-R13"' ci/.r11-build-generated.sh
grep -Fq 'HIMURA SWITCH PS4-01.13-R13.pkg' ci/.r11-build-generated.sh
grep -Fq 'stage 09_eden_pkg build_pkg' ci/.r11-build-generated.sh
for patch in patch-r11-samurai-library patch-r11-theme-cache patch-r11-autocovers patch-r11-fps \
 generate-r11-branding patch-r11-authorship patch-r11-stability patch-r11-approved-menu \
 patch-r11-home-return patch-r11-videoout-visibility patch-r12-active-user-videoout; do
 grep -Fq "ci/$patch.py" ci/.r11-build-generated.sh
done
echo "R11 PREFLIGHT PASSED: code transformations and PKG recipe checked."
echo "Note: PS4 compilation and console boot still require separate confirmation."
