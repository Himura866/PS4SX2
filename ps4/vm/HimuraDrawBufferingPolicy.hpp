// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <string_view>

// GS draw buffering is useful for some games, but can introduce graphical
// regressions in others. Keep each game's GameDB choice unless the user
// explicitly chooses an experimental PS4-only override before launching.
namespace HimuraDrawBufferingPolicy
{
enum class Mode : unsigned char
{
    GameDatabase,
    ForceOn,
    ForceOff
};

// Only normalized serials can become file paths (no slashes, whitespace or dots).
[[nodiscard]] constexpr bool IsSafeSerial(std::string_view serial) noexcept
{
    if (serial.empty() || serial.size() > 32)
        return false;
    for (char ch : serial)
    {
        if (!((ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') || ch == '-'))
            return false;
    }
    return true;
}

[[nodiscard]] constexpr Mode Choose(bool enable_all_marker, bool disable_all_marker,
                                   bool enable_game_marker = false, bool disable_game_marker = false) noexcept
{
    // A global emergency OFF always wins. Per-game OFF also wins over global ON.
    if (disable_all_marker || disable_game_marker)
        return Mode::ForceOff;
    return (enable_all_marker || enable_game_marker) ? Mode::ForceOn : Mode::GameDatabase;
}

[[nodiscard]] constexpr bool Resolve(bool recommended_by_game_db, Mode mode) noexcept
{
    switch (mode)
    {
        case Mode::ForceOn: return true;
        case Mode::ForceOff: return false;
        case Mode::GameDatabase:
        default: return recommended_by_game_db;
    }
}
} // namespace HimuraDrawBufferingPolicy
