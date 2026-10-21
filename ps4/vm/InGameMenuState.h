// SPDX-License-Identifier: GPL-3.0+
// (AI-assisted) Atomic CPU-to-GS menu snapshot, independent of renderer headers.
#pragma once

#include <algorithm>
#include <cstdint>

namespace PS4GameMenu
{
	struct InGameMenuState
	{
		bool visible;
		unsigned selected;
		unsigned upscale;
		unsigned max_upscale;
		unsigned aspect;
		bool show_overlay;
		unsigned ee_profile;
		bool async_audio;
		unsigned ee_skip;
		unsigned frame_queue;
	};

	constexpr std::uint32_t PackInGameMenuState(InGameMenuState value)
	{
		if (!value.visible)
			return 0;
		const unsigned limit = std::clamp(value.max_upscale, 1u, 4u);
		return (std::min(value.selected, 9u) + 1u) |
			(std::clamp(value.upscale, 1u, limit) << 8) |
			(limit << 12) |
			(std::min(value.aspect, 4u) << 16) |
			(value.show_overlay ? (1u << 20) : 0u) |
			(std::min(value.ee_profile, 2u) << 21) |
			(value.async_audio ? (1u << 23) : 0u) |
			(std::min(value.ee_skip, 1u) << 24) |
			(std::clamp(value.frame_queue, 1u, 3u) << 25);
	}

	constexpr InGameMenuState UnpackInGameMenuState(std::uint32_t value)
	{
		// These fields occupy FOUR bits, not eight. Reading 0xff here mixed the
		// resolution with its limit (1 became 65), and aspect with overlay (0 became 16).
		const unsigned selection = value & 0xffu;
		const unsigned limit = std::clamp((value >> 12) & 0x0fu, 1u, 4u);
		return {selection != 0, selection ? std::min(selection - 1u, 9u) : 0u,
			std::clamp((value >> 8) & 0x0fu, 1u, limit), limit,
			std::min((value >> 16) & 0x0fu, 4u), (value & (1u << 20)) != 0,
			std::min((value >> 21) & 3u, 2u), (value & (1u << 23)) != 0,
			(value >> 24) & 1u, std::clamp((value >> 25) & 3u, 1u, 3u)};
	}
} // namespace PS4GameMenu
