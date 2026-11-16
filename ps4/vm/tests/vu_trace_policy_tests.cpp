// SPDX-License-Identifier: GPL-3.0-or-later
#define PCSX2_PS4_VM_BOOT 1
#include "ps4/vm/HimuraVUDiagnostics.hpp"
#include <array>
#include <cassert>
#include <cstdint>

int main() {
    assert(!HimuraVUDiagnostics::Enabled());
    HimuraVUDiagnostics::Configure(true);
    assert(HimuraVUDiagnostics::Enabled());
    HimuraVUDiagnostics::Configure(false);
    assert(!HimuraVUDiagnostics::Enabled());

    // Diagnostic logging is observational. Simulate command processing
    // and ensure enabling it does not affect cycle totals or packet counts.
    const std::array<unsigned, 8> packets = {2, 1, 0, 0, 1, 2, 5, 1};
    const auto test = [&](bool trace) {
        HimuraVUDiagnostics::Configure(trace);
        std::uint64_t cycles = 0;
        unsigned recorded = 0;
        unsigned processed = 0;
        for (const unsigned packet : packets) {
            ++processed;
            cycles += 11 + packet;
            if (HimuraVUDiagnostics::Enabled())
                ++recorded;
        }
        return std::array<std::uint64_t, 3>{cycles, processed, recorded};
    };
    const auto off = test(false), on = test(true);
    assert(off[0] == on[0] && off[1] == on[1]);
    assert(off[2] == 0 && on[2] == packets.size());
}
