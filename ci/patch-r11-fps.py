#!/usr/bin/env python3
"""R11 live in-game FPS overlay from emulated GPU frames, rendered by Vulkan transfer.

Reports FPS as a 1-second sample (0.1 FPS display resolution), not a PS4 VideoOut
flip count. Uses host-coherent staging buffers per presentation frame, reuses the
existing GPU queue without a new WaitIdle per frame, and is isolated to PS4.
No assertion that it cures game crashes or unlocks full-speed emulation.
"""
from pathlib import Path
import sys

def once(s,old,new,label):
    n=s.count(old)
    if n!=1: raise RuntimeError("R11 FPS %s: anchor count %d" % (label,n))
    return s.replace(old,new,1)

GLYPHS=r'''
#ifdef __OPENORBIS__
constexpr u32 R11FpsW = 256, R11FpsH = 48;
const char* R11Glyph(char c) {
    switch (c) {
    case 'F': return "11111""10000""10000""11110""10000""10000""10000";
    case 'P': return "11110""10001""10001""11110""10000""10000""10000";
    case 'S': return "01111""10000""10000""01110""00001""00001""11110";
    case ':': return "00000""00100""00100""00000""00100""00100""00000";
    case '.': return "00000""00000""00000""00000""00000""00110""00110";
    case '0': return "01110""10001""10011""10101""11001""10001""01110";
    case '1': return "00100""01100""00100""00100""00100""00100""01110";
    case '2': return "01110""10001""00001""00010""00100""01000""11111";
    case '3': return "11110""00001""00001""00110""00001""00001""11110";
    case '4': return "00010""00110""01010""10010""11111""00010""00010";
    case '5': return "11111""10000""10000""11110""00001""00001""11110";
    case '6': return "01110""10000""10000""11110""10001""10001""01110";
    case '7': return "11111""00001""00010""00100""00100""00100""00100";
    case '8': return "01110""10001""10001""01110""10001""10001""01110";
    case '9': return "01110""10001""10001""01111""00001""00001""01110";
    default: return "00000""00000""00000""00000""00000""00000""00000";
    }
}
void R11PaintFps(void* mem) {
    if (!mem) return;
    u32* dst = static_cast<u32*>(mem);
    std::fill_n(dst, size_t(R11FpsW) * R11FpsH, 0xff171717u);
    const int raw = Common::PS4Diagnostics::r11_game_fps_tenths.load(std::memory_order_relaxed);
    const int tenth = std::clamp(raw,0,9999);
    char label[32];
    std::snprintf(label,sizeof(label),"FPS: %d.%d", tenth/10, tenth%10);
    constexpr int scale=3, startx=15, starty=12;
    int x=startx;
    for (const char* cp=label; *cp; ++cp, x+=18) {
        const char* glyph=R11Glyph(*cp);
        if (x+15 >= int(R11FpsW)) break;
        for (int cy=0;cy<7;++cy) {
            for (int cx=0;cx<5;++cx) {
                if (glyph[cy*5+cx]!='1') continue;
                for (int py=0;py<scale;++py)
                    for (int px=0;px<scale;++px)
                        dst[size_t(starty+cy*scale+py)*R11FpsW+x+cx*scale+px]=0xfff5f5f5u;
            }
        }
    }
}
void R11FreeFps(Frame& f, const Device& device) {
    const auto& api = device.GetLogical().Dispatch();
    const VkDevice dev = *device.GetLogical();
    if (f.fps_mapped && f.fps_memory) api.vkUnmapMemory(dev,f.fps_memory);
    if (f.fps_buffer) api.vkDestroyBuffer(dev,f.fps_buffer,nullptr);
    if (f.fps_memory) api.vkFreeMemory(dev,f.fps_memory,nullptr);
    f.fps_mapped=nullptr;
    f.fps_buffer=VK_NULL_HANDLE;
    f.fps_memory=VK_NULL_HANDLE;
}
void R11InitFps(Frame& f, const Device& device) {
    const auto& api = device.GetLogical().Dispatch();
    const VkDevice dev = *device.GetLogical();
    VkBufferCreateInfo create{
        .sType=VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        .size=VkDeviceSize(R11FpsW)*R11FpsH*4,
        .usage=VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        .sharingMode=VK_SHARING_MODE_EXCLUSIVE
    };
    if (api.vkCreateBuffer(dev,&create,nullptr,&f.fps_buffer)!=VK_SUCCESS) return;
    // Eden4 only exposes vkGetBufferMemoryRequirements2 in DeviceDispatch.
    // Query the requirements through its supported Vulkan 1.1 entry point.
    VkMemoryRequirements2 requirements2{.sType=VK_STRUCTURE_TYPE_MEMORY_REQUIREMENTS_2};
    const VkBufferMemoryRequirementsInfo2 query{
        .sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_REQUIREMENTS_INFO_2,
        .buffer=f.fps_buffer
    };
    api.vkGetBufferMemoryRequirements2(dev,&query,&requirements2);
    const VkMemoryRequirements& requirements=requirements2.memoryRequirements;
    const auto props=device.GetPhysical().GetMemoryProperties().memoryProperties;
    u32 type=props.memoryTypeCount;
    for(u32 i=0;i<props.memoryTypeCount;++i) {
        if (!(requirements.memoryTypeBits&(1u<<i))) continue;
        const auto flags=props.memoryTypes[i].propertyFlags;
        if ((flags&(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
            (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT|VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
            type=i;break;
        }
    }
    if(type==props.memoryTypeCount) {R11FreeFps(f,device);return;}
    const VkMemoryAllocateInfo allocation{
        .sType=VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
        .allocationSize=requirements.size,
        .memoryTypeIndex=type
    };
    if(api.vkAllocateMemory(dev,&allocation,nullptr,&f.fps_memory)!=VK_SUCCESS) {
        R11FreeFps(f,device);return;
    }
    if(api.vkBindBufferMemory(dev,f.fps_buffer,f.fps_memory,0)!=VK_SUCCESS ||
       api.vkMapMemory(dev,f.fps_memory,0,create.size,0,&f.fps_mapped)!=VK_SUCCESS) {
        R11FreeFps(f,device);return;
    }
}
#endif
'''
DRAW=r'''
#ifdef __OPENORBIS__
    // Overwrite a tiny top-right region *after* the game transfer and *before*
    // VideoOut flips the same GPU image. This does not create another flip or
    // wait for GPU idle; the per-frame staging buffer is fence-protected.
    if (frame->fps_mapped && extent.width > R11FpsW+32 && extent.height > R11FpsH+32) {
        R11PaintFps(frame->fps_mapped);
        const VkBufferMemoryBarrier host_write{
            .sType=VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER,
            .srcAccessMask=VK_ACCESS_HOST_WRITE_BIT,
            .dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT,
            .srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
            .dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
            .buffer=frame->fps_buffer,
            .offset=0,
            .size=VK_WHOLE_SIZE
        };
        cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_HOST_BIT,
                               VK_PIPELINE_STAGE_TRANSFER_BIT,0,host_write);
        const VkImageMemoryBarrier transfer_write{
            .sType=VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
            .srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT,
            .dstAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT,
            .oldLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            .newLayout=VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            .srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
            .dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
            .image=image,
            .subresourceRange={VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1}
        };
        cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_TRANSFER_BIT,
                               VK_PIPELINE_STAGE_TRANSFER_BIT,0,transfer_write);
        const VkBufferImageCopy overlay_region{
            .bufferOffset=0,
            .bufferRowLength=R11FpsW,
            .bufferImageHeight=R11FpsH,
            .imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1},
            .imageOffset={s32(extent.width-R11FpsW-16),16,0},
            .imageExtent={R11FpsW,R11FpsH,1}
        };
        const std::array regions{overlay_region};
        cmdbuf.CopyBufferToImage(frame->fps_buffer,image,
                                 VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,regions);
    }
#endif
'''

def main(root):
    h=root/"eden/src/common/ps4_diagnostics.h"
    s=h.read_text(encoding="utf8")
    s=once(s,'inline std::atomic<u64> audio_buffers{};',
           'inline std::atomic<u64> audio_buffers{};\n'
           '// R11: GPU-game frame rate in tenths, sampled from core PerfStats every second.\n'
           'inline std::atomic<int> r11_game_fps_tenths{0};',
           "metric")
    s=once(s,'    audio_buffers = 0;\n    stage = "waiting for guest display";',
           '    audio_buffers = 0;\n    r11_game_fps_tenths = 0;\n    stage = "waiting for guest display";',
           "metric reset")
    h.write_text(s,encoding="utf8")

    p=root/"eden/src/yuzu_ps4/main.cpp"
    s=p.read_text(encoding="utf8")
    s=once(s,
        '    auto next_status = std::chrono::steady_clock::now() + std::chrono::seconds{10};',
        '    auto next_status = std::chrono::steady_clock::now() + std::chrono::seconds{10};\n'
        '    auto next_fps = std::chrono::steady_clock::now() + std::chrono::seconds{1};',
        "sample clock")
    s=once(s,
        '        if (std::chrono::steady_clock::now() >= next_status) {\n            LOG_INFO(Frontend,',
        '        const auto now = std::chrono::steady_clock::now();\n'
        '        if (now >= next_fps) {\n'
        '            const auto perf = system.GetAndResetPerfStats();\n'
        '            const double fps = std::clamp(perf.average_game_fps, 0.0, 999.9);\n'
        '            Common::PS4Diagnostics::r11_game_fps_tenths.store(\n'
        '                static_cast<int>(fps * 10.0 + 0.5), std::memory_order_relaxed);\n'
        '            next_fps = now + std::chrono::seconds{1};\n'
        '        }\n'
        '        if (now >= next_status) {\n            LOG_INFO(Frontend,',
        "1-second sample")
    s=once(s,
        '            const auto perf = system.GetAndResetPerfStats();\n'
        '            LOG_INFO(Frontend, "PS4 performance: game {:.1f} fps, emulation speed {:.0f}%, frame time {:.1f} ms",\n'
        '                     perf.average_game_fps, perf.emulation_speed * 100.0, perf.frametime * 1000.0);',
        '            LOG_INFO(Frontend, "R11 overlay: sampled game FPS {:.1f} (not PS4 display flips)",\n'
        '                     Common::PS4Diagnostics::r11_game_fps_tenths.load() / 10.0);',
        "heartbeat")
    p.write_text(s,encoding="utf8")

    ph=root/"eden/src/video_core/renderer_vulkan/vk_present_manager.h"
    s=ph.read_text(encoding="utf8")
    s=once(s,'    bool storage_capable{};',
           '    bool storage_capable{};\n'
           '#ifdef __OPENORBIS__\n'
           '    VkBuffer fps_buffer{VK_NULL_HANDLE};\n'
           '    VkDeviceMemory fps_memory{VK_NULL_HANDLE};\n'
           '    void* fps_mapped{};\n'
           '#endif',
           "per-frame resource")
    ph.write_text(s,encoding="utf8")

    cpp=root/"eden/src/video_core/renderer_vulkan/vk_present_manager.cpp"
    s=cpp.read_text(encoding="utf8")
    s=once(s,
      '#include "common/settings.h"',
      '#include <cstdio>\n#include "common/ps4_diagnostics.h"\n#include "common/settings.h"',
      "renderer imports")
    s=once(s,
      '} // Anonymous namespace\n\nPresentManager::PresentManager',
      GLYPHS + '\n} // Anonymous namespace\n\nPresentManager::PresentManager',
      "bitmap resource")
    s=once(s,
      '        free_queue.push_back(&frame);\n    }\n\n    if (use_present_thread) {',
      '        free_queue.push_back(&frame);\n'
      '#ifdef __OPENORBIS__\n'
      '        R11InitFps(frame,device);\n'
      '#endif\n'
      '    }\n\n    if (use_present_thread) {',
      "init resources")
    s=once(s,'PresentManager::~PresentManager() = default;',
      'PresentManager::~PresentManager() {\n'
      '#ifdef __OPENORBIS__\n'
      '    // All staged copies must finish before their source buffers are released.\n'
      '    void(device.GetLogical().WaitIdle());\n'
      '    for (auto& frame : frames) R11FreeFps(frame,device);\n'
      '#endif\n'
      '}',
      "free resources")
    s=once(s,
      '    cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_ALL_GRAPHICS_BIT, {},\n                           {}, {}, post_barriers);',
      DRAW+'\n'
      '    cmdbuf.PipelineBarrier(VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_ALL_GRAPHICS_BIT, {},\n                           {}, {}, post_barriers);',
      "present overlay")
    cpp.write_text(s,encoding="utf8")
    print("R11: sampled actual game FPS and staged Vulkan top-right overlay patched")

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: patch-r11-fps.py <checkout>")
    main(Path(sys.argv[1]).resolve())
