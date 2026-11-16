// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once

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

[[nodiscard]] constexpr Mode Choose(bool enable_all_marker, bool disable_all_marker) noexcept
{
    // The safe rollback wins if both marker files are present.
    return disable_all_marker ? Mode::ForceOff :
           enable_all_marker ? Mode::ForceOn : Mode::GameDatabase;
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
