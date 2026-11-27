// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
// Low-memory, no-heap diagnostic. Never call the fmt/LOG macros from new_handler.
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <fcntl.h>
#include <unistd.h>

namespace HimuraMemoryProbe {
// Best effort only: a filesystem or kernel error must not change OOM behavior.
inline bool Append(const char* path, const char* origin, const char* phase,
                   uint64_t request_bytes, uint32_t error_code,
                   uint64_t composites, uint64_t flips, uint64_t overflow_mib) noexcept {
    char buffer[448];
    const int n = std::snprintf(buffer, sizeof(buffer),
        "HIMURA R13 OOM origin=%.55s phase=%.80s bytes=%llu code=0x%08x "
        "composites=%llu flips=%llu overflow_heap_mib=%llu\n",
        origin ? origin : "unknown", phase ? phase : "unknown",
        static_cast<unsigned long long>(request_bytes), error_code,
        static_cast<unsigned long long>(composites),
        static_cast<unsigned long long>(flips),
        static_cast<unsigned long long>(overflow_mib));
    if(n<=0 || static_cast<size_t>(n)>=sizeof(buffer))return false;
    const int fd = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0644);
    if(fd<0)return false;
    const ssize_t result = ::write(fd, buffer, static_cast<size_t>(n));
    if(result==n) ::fsync(fd);  // OOM is rare; durable evidence takes precedence.
    ::close(fd);
    return result==n;
}
} // namespace HimuraMemoryProbe
