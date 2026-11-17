// SPDX-License-Identifier: GPL-3.0-or-later
#include "ps4/vm/HimuraDrawBufferingPolicy.hpp"
#include <cassert>
#include <initializer_list>
#include <cstdio>

using HimuraDrawBufferingPolicy::Choose;
using HimuraDrawBufferingPolicy::Mode;
using HimuraDrawBufferingPolicy::Resolve;

static_assert(Choose(false, false) == Mode::GameDatabase);
static_assert(Choose(true, false) == Mode::ForceOn);
static_assert(Choose(false, true) == Mode::ForceOff);
static_assert(Choose(true, true) == Mode::ForceOff);
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
    std::puts("PASS: draw buffering preserves GameDB, supports experimental global ON, and safe rollback");
}
