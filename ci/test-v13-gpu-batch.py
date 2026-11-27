#!/usr/bin/env python3
"""Static regression verification of patched Eden4 Vulkan sources, not PS4 gameplay."""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("v13gpu", Path(__file__).with_name("patch-v13-gpu-batch.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if len(sys.argv) != 2:
    raise SystemExit("Uso: test-v13-gpu-batch.py <patched Eden4 checkout>")
base = Path(sys.argv[1]) / module.TARGET
files = {name: (base/name).read_text(encoding="utf-8") for name in module.FILES}
r = files["vk_rasterizer.cpp"]
assert "DRAWS_TO_DISPATCH = 256;" in r, "PS4 branch missing"
assert "DRAWS_TO_DISPATCH = 512;" in r, "Android fallback missing"
assert "DRAWS_TO_DISPATCH = 4096;" in r, "PC fallback missing"
assert "UPLOADS_TO_DISPATCH = 96;" in r
assert r.index("scheduler.ps4_uploads_since_submit >= UPLOADS_TO_DISPATCH") < r.index("(++draw_counter & CHECK_MASK)")
assert files["vk_scheduler.h"].count("u32 ps4_uploads_since_submit{};") == 1
assert files["vk_scheduler.cpp"].count("ps4_uploads_since_submit = 0;") == 1
assert files["vk_buffer_cache.cpp"].count("scheduler.ps4_uploads_since_submit +=") == 1
assert files["vk_texture_cache.cpp"].count("scheduler->ps4_uploads_since_submit +=") == 1
for name in module.FILES:
    assert "#ifdef __OPENORBIS__" in files[name], f"Missing PS4-only guard: {name}"
try:
    module.patch_text(files)
except RuntimeError:
    pass
else:
    raise AssertionError("A second patch application must fail")
print("PASS V13: PS4-only GPU batches, upload counter, non-PS4 configurations retained")
