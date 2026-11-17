// SPDX-License-Identifier: GPL-3.0-or-later
#include "ps4/vm/HimuraDrawBufferingPolicy.hpp"
#include <cassert>
#include <initializer_list>
#include <cstdio>

using HimuraDrawBufferingPolicy::Choose;
using HimuraDrawBufferingPolicy::Mode;
using HimuraDrawBufferingPolicy::Resolve;
using HimuraDrawBufferingPolicy::IsSafeSerial;

static_assert(Choose(false, false) == Mode::GameDatabase);
static_assert(Choose(true, false) == Mode::ForceOn);
static_assert(Choose(false, true) == Mode::ForceOff);
static_assert(Choose(true, true) == Mode::ForceOff);
static_assert(Choose(false, false, true, false) == Mode::ForceOn);
static_assert(Choose(true, false, false, true) == Mode::ForceOff);
static_assert(Choose(false, true, true, false) == Mode::ForceOff);
static_assert(Choose(false, false, true, true) == Mode::ForceOff);
static_assert(IsSafeSerial("SLUS-21257"));
static_assert(IsSafeSerial("SLES-54402"));
static_assert(!IsSafeSerial(""));
static_assert(!IsSafeSerial("../bad"));
static_assert(!IsSafeSerial("SLUS-21257/../../file"));
static_assert(!IsSafeSerial("slus-21257"));
static_assert(!Resolve(false, Mode::GameDatabase));
static_assert(Resolve(true, Mode::GameDatabase));
static_assert(Resolve(false, Mode::ForceOn));
static_assert(!Resolve(true, Mode::ForceOff));

int main()
{
    for (bool game_db : {false, true})
    {
        assert(Resolve(game_db, Choose(false, false)) == game_db);
        assert(Resolve(game_db, Choose(true, false)));
        assert(!Resolve(game_db, Choose(false, true)));
        assert(!Resolve(game_db, Choose(true, true)));
    }
    std::puts("PASS: GameDB default; per-game override; global and game rollback; safe serial paths");
}
