// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// The VU worker configures this once at startup, before processing commands.
// Do not toggle while the worker is running.
namespace HimuraVUDiagnostics {
#if defined(PCSX2_PS4_VM_BOOT)
inline bool s_enabled = false;
#else
inline bool s_enabled = true;
#endif
inline void Configure(bool enabled) noexcept { s_enabled = enabled; }
[[nodiscard]] inline bool Enabled() noexcept { return s_enabled; }
}
