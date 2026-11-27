#!/usr/bin/env python3
"""PS4-only GPU command batch guard for the pinned Eden4 tree.

Adapted experimentally from Orbis-EDEN patch 0015 (2026-10-04);
this does not prove a fix for any console crash.
"""
from pathlib import Path
import sys

TARGET = "eden/src/video_core/renderer_vulkan"
FILES = (
    "vk_rasterizer.cpp", "vk_scheduler.h", "vk_scheduler.cpp",
    "vk_buffer_cache.cpp", "vk_texture_cache.cpp",
)

def replace_one(source: str, before: str, after: str, label: str) -> str:
    matches = source.count(before)
    if matches != 1:
        raise RuntimeError(f"V13 GPU {label}: expected one anchor, found {matches}")
    return source.replace(before, after, 1)

def patch_text(files: dict[str, str]) -> dict[str, str]:
    if set(files) != set(FILES):
        raise ValueError("Five pinned Vulkan source files are required")
    result = files.copy()
    original = """void RasterizerVulkan::FlushWork() {
#ifdef __ANDROID__
    static constexpr u32 DRAWS_TO_DISPATCH = 512;
    static constexpr u32 CHECK_MASK = 3;
#else
    static constexpr u32 DRAWS_TO_DISPATCH = 4096;
    static constexpr u32 CHECK_MASK = 7;
#endif // __ANDROID__

    static_assert(DRAWS_TO_DISPATCH % (CHECK_MASK + 1) == 0);
    if ((++draw_counter & CHECK_MASK) != CHECK_MASK) {
        return;
    }
    if (draw_counter < DRAWS_TO_DISPATCH) {
        scheduler.DispatchWork();
        return;
    }
    scheduler.Flush();
    draw_counter = 0;
}"""
    guarded = """void RasterizerVulkan::FlushWork() {
#ifdef __OPENORBIS__
    // PS4 GFX7: smaller GPU submits; account for texture-heavy transitions.
    static constexpr u32 DRAWS_TO_DISPATCH = 256;
    static constexpr u32 CHECK_MASK = 3;
    static constexpr u32 UPLOADS_TO_DISPATCH = 96;
    if (scheduler.ps4_uploads_since_submit >= UPLOADS_TO_DISPATCH) {
        scheduler.Flush();
        draw_counter = 0;
        return;
    }
#elif defined(__ANDROID__)
    static constexpr u32 DRAWS_TO_DISPATCH = 512;
    static constexpr u32 CHECK_MASK = 3;
#else
    static constexpr u32 DRAWS_TO_DISPATCH = 4096;
    static constexpr u32 CHECK_MASK = 7;
#endif // __OPENORBIS__ / __ANDROID__

    static_assert(DRAWS_TO_DISPATCH % (CHECK_MASK + 1) == 0);
    if ((++draw_counter & CHECK_MASK) != CHECK_MASK) {
        return;
    }
    if (draw_counter < DRAWS_TO_DISPATCH) {
        scheduler.DispatchWork();
        return;
    }
    scheduler.Flush();
    draw_counter = 0;
}"""
    result["vk_rasterizer.cpp"] = replace_one(
        files["vk_rasterizer.cpp"], original, guarded, "rasterizer")
    result["vk_scheduler.h"] = replace_one(
        files["vk_scheduler.h"],
        "    std::mutex submit_mutex;\n\nprivate:",
        "    std::mutex submit_mutex;\n"
        "#ifdef __OPENORBIS__\n"
        "    // Upload count since last GPU submission on PS4.\n"
        "    u32 ps4_uploads_since_submit{};\n"
        "#endif\n\nprivate:",
        "scheduler counter")
    result["vk_scheduler.cpp"] = replace_one(
        files["vk_scheduler.cpp"],
        "void Scheduler::AllocateNewContext() {\n"
        "    // Enable counters once again. These are disabled when a command buffer is finished.\n"
        "}",
        "void Scheduler::AllocateNewContext() {\n"
        "#ifdef __OPENORBIS__\n"
        "    ps4_uploads_since_submit = 0;\n"
        "#endif\n"
        "}",
        "scheduler counter reset")
    result["vk_buffer_cache.cpp"] = replace_one(
        files["vk_buffer_cache.cpp"],
        "    if (dst_buffer == VK_NULL_HANDLE || src_buffer == VK_NULL_HANDLE) {\n"
        "        return;\n"
        "    }\n"
        "    static constexpr VkMemoryBarrier READ_BARRIER{",
        "    if (dst_buffer == VK_NULL_HANDLE || src_buffer == VK_NULL_HANDLE) {\n"
        "        return;\n"
        "    }\n"
        "#ifdef __OPENORBIS__\n"
        "    // Sixteen short regions count roughly as one texture upload.\n"
        "    scheduler.ps4_uploads_since_submit += static_cast<u32>((copies.size() + 15) / 16);\n"
        "#endif\n"
        "    static constexpr VkMemoryBarrier READ_BARRIER{",
        "buffer copies")
    result["vk_texture_cache.cpp"] = replace_one(
        files["vk_texture_cache.cpp"],
        "void Image::UploadMemory(VkBuffer buffer, VkDeviceSize offset,\n"
        "                         std::span<const VideoCommon::BufferImageCopy> copies) {\n"
        "    // TODO: Move this to another API",
        "void Image::UploadMemory(VkBuffer buffer, VkDeviceSize offset,\n"
        "                         std::span<const VideoCommon::BufferImageCopy> copies) {\n"
        "#ifdef __OPENORBIS__\n"
        "    scheduler->ps4_uploads_since_submit += static_cast<u32>(copies.size());\n"
        "#endif\n"
        "    // TODO: Move this to another API",
        "texture uploads")
    return result

def main(root: Path) -> None:
    directory = root / TARGET
    paths = {name: directory / name for name in FILES}
    originals = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    # Verify all five anchors before overwriting the first file.
    updated = patch_text(originals)
    for name, path in paths.items():
        path.write_text(updated[name], encoding="utf-8")
    print("V13 PS4 Vulkan: smaller 256-draw and 96-upload GPU batches patched")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: patch-v13-gpu-batch.py <checkout Eden4>")
    main(Path(sys.argv[1]).resolve())
