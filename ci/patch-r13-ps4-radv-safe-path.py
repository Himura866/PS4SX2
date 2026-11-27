#!/usr/bin/env python3
"""R13-only PS4 RADV GFX7 safety experiment; port of Orbis-EDEN patch 0009.

The PS4 Eden4 build uses __OPENORBIS__, not __ORBIS__. Do not change
the original R13 branch or apply this to the New Eden 04.89 binary.
"""
from pathlib import Path
import sys


def replace_one(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"R13 PS4 RADV safety {label}: expected one anchor, got {count}")
    return source.replace(old, new, 1)


def patch_text(macro_text: str, device_text: str):
    macro_anchor = """    const auto topology = Maxwell3D::Regs::PrimitiveTopology(parameters[2]);
    if (IsTopologySafe(topology)) {
        const u32 start_indirect = parameters[0];"""
    macro_replacement = """    const auto topology = Maxwell3D::Regs::PrimitiveTopology(parameters[2]);
#ifdef __OPENORBIS__
    // RADV GFX7 on PS4: use the existing individual-draw fallback instead of
    // a count-buffer indirect draw, which can wedge the PS4 GPU command processor.
    Fallback(system, maxwell3d, parameters);
    return;
#endif
    if (IsTopologySafe(topology)) {
        const u32 start_indirect = parameters[0];"""
    macro_text = replace_one(macro_text, macro_anchor, macro_replacement, "macro fallback")

    device_anchor = """    logical = vk::Device::Create(physical, queue_cis, ExtensionListForVulkan(loaded_extensions), first_next, dld);"""
    device_replacement = """#ifdef __OPENORBIS__
    // Disable extension paths reported to hang the PS4's RADV GFX7 driver.
    // Use PS4-specific guards so this does not change host/Linux targets.
    LOG_WARNING(Render_Vulkan, "R13 PS4 RADV safe-path: disabling indirect count and conditional rendering");
    RemoveExtension(extensions.conditional_rendering, VK_EXT_CONDITIONAL_RENDERING_EXTENSION_NAME);
    RemoveExtension(extensions.draw_indirect_count, VK_KHR_DRAW_INDIRECT_COUNT_EXTENSION_NAME);
#endif
    logical = vk::Device::Create(physical, queue_cis, ExtensionListForVulkan(loaded_extensions), first_next, dld);"""
    device_text = replace_one(device_text, device_anchor, device_replacement, "device extensions")
    return macro_text, device_text


def patch(root: Path):
    sources = [
        root / "eden/src/video_core/macro.cpp",
        root / "eden/src/video_core/vulkan_common/vulkan_device.cpp",
    ]
    originals = [p.read_text(encoding="utf-8") for p in sources]
    changed = patch_text(*originals)
    # Both anchors must validate before the first file is overwritten.
    for path, content in zip(sources, changed):
        path.write_text(content, encoding="utf-8")
    print("R13 PS4 RADV safe-path: indirect-count fallback and extension guard applied")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch-r13-ps4-radv-safe-path.py <pinned Eden4 checkout>")
    patch(Path(sys.argv[1]).resolve())
