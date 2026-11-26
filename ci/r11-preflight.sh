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
 ci/patch-r11-stability.py ci/patch-r11-approved-menu.py ci/patch-r11-home-return.py; do
  python3 -m py_compile "$py"
done

echo "R11 preflight: download exact pinned patch targets"
python3 - "$BASE" <<'PY'
from pathlib import Path
import sys
from urllib.request import urlopen
root=Path(sys.argv[1])
sha="fab246cbac93c7995aaf451dca83ae93ba0bd234"
paths=[
  "eden/src/yuzu_ps4/ui_launcher.cpp",
  "eden/src/yuzu_ps4/ui_canvas.h",
  "eden/src/yuzu_ps4/ui_canvas.cpp",
  "eden/src/yuzu_ps4/ui_metadata.cpp",
  "eden/src/yuzu_ps4/main.cpp",
  "eden/src/common/ps4_diagnostics.h",
  "eden/src/video_core/renderer_vulkan/vk_present_manager.cpp",
  "eden/src/video_core/renderer_vulkan/vk_present_manager.h",
  "eden/src/video_core/vulkan_common/vulkan_wrapper.h",
  "eden/ps4/ui-preview/preview.cpp",
  "eden/ps4/build.sh",
]
for path in paths:
    output=root/path
    output.parent.mkdir(parents=True,exist_ok=True)
    url=f"https://raw.githubusercontent.com/xatyy/Eden4/{sha}/{path}"
    data=urlopen(url,timeout=60).read()
    if not data: raise RuntimeError(f"empty source file: {path}")
    output.write_bytes(data)
    print("Fetched:",path,flush=True)
PY

echo "R11 preflight: all patches in packaging order"
for patch in patch-eden4-credits patch-r10-switch-toolbar patch-r11-samurai-library patch-r11-theme-cache \
 patch-r11-autocovers patch-r11-fps generate-r11-branding patch-r11-authorship \
 patch-r10-boot-trace patch-r11-stability patch-r11-approved-menu patch-r11-home-return; do
  echo "APPLY $patch"
  python3 "ci/$patch.py" "$BASE"
done

echo "R11 preflight: complete theme/assets and safe metadata"
test -s "$BASE/branding/icon0.png"
test -s "$BASE/branding/pic1.png"
test -s "$BASE/branding/himura-r11-menu.png"
grep -Fq '$STAGE/skin/himura-r11-menu.png' "$BASE/eden/ps4/build.sh"
grep -Fq '/app0/skin/himura-r11-menu.png' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
test -s "$BASE/branding/HIMURA-ATTRIBUTION.txt"
grep -Fq 'POD DO HIMURA' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'canvas.CopyOpaque(cached_background)' "$BASE/eden/src/yuzu_ps4/ui_launcher.cpp"
grep -Fq 'void Canvas::CopyOpaque' "$BASE/eden/src/yuzu_ps4/ui_canvas.cpp"
grep -Fq 'R11GameCheckpoint' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'bool menu_armed = false' "$BASE/eden/src/yuzu_ps4/main.cpp"
grep -Fq 'constexpr uint32_t return_buttons' "$BASE/eden/src/yuzu_ps4/main.cpp"
echo "R11 preflight: validate diagnostic path argument is C-compatible"
grep -Fq 'R11GameCheckpoint("launch begin",game.path.c_str(),true);' "$BASE/eden/src/yuzu_ps4/main.cpp"
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
bash -n ci/.r11-build-generated.sh
for patch in patch-r11-samurai-library patch-r11-theme-cache patch-r11-autocovers patch-r11-fps \
 generate-r11-branding patch-r11-authorship patch-r11-stability patch-r11-approved-menu patch-r11-home-return; do
 grep -Fq "ci/$patch.py" ci/.r11-build-generated.sh
done
echo "R11 PREFLIGHT PASSED: code transformations and PKG recipe checked."
echo "Note: PS4 compilation and console boot still require separate confirmation."
