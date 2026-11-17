# HIMURA PS2 / PS4SX2 R25F — draw buffering experiment

## What this branch actually changes
- Keeps the normal PCSX2 GameDB draw buffering recommendations active for all supported game serials.
- Adds the missing `DrawBuffering=1` recommendation for Need for Speed Carbon Collector's Edition PAL-F (`SLES-54402`), matching other Carbon editions.
- Adds an **optional, PS4-only** game-wide switch for testing the already-implemented GS draw batching algorithm on games without a GameDB recommendation.
- Leaves JIT, MTVU, shader cache, fastmem and 1x/2x rendering behavior unchanged by this change.
- Does **not** change the HIMURA R25E menu, banner or offline ISO library, which are maintained in the separately packaged frontend patch.

## PS4 operation
Default (no marker files): **GameDB recommendations only**. Works for all titles without forcing a potentially unsafe hack.

- To experiment with draw buffering on **all PS2 games**, create the empty file `/data/PS4SX2/vm-gs-draw-buffering-all` before launching the game.
- To force it off for troubleshooting, create `/data/PS4SX2/vm-no-draw-buffering`. This **takes precedence** if both files exist.
- To return to the normal game-by-game policy, remove both markers and restart the game.
- These files are stored in the emulator data folder, not inside a game ISO.

Draw buffering combines eligible draws to reduce CPU/GS work on certain games, but may cause corruption or have little benefit depending on the title. It cannot guarantee a higher FPS for every title. It does not affect the game's native 30/60 FPS design.

## Real-hardware acceptance test
On the **same** PS4 Pro, game region, game version, saved race and resolution, compare:
1. GameDB default, at 1x native when that resolution is available in the compiled frontend.
2. Experimental global draw buffering ON.
3. Explicit draw buffering OFF.

Record *actual emulation speed (%)* and separately the internal FPS estimate, EE/GS/VU times, visual anomalies, audio and any crashes. Run each case for a similar duration after shader warm-up; do not compare different scenes or turbo rates. Carbon, Most Wanted and Underground 2 have first priority, then at least one graphics-heavy non-racing title.

This branch has **not** been compiled into an installable PKG or measured on a physical PS4 Pro. A CircleCI passing host test is not a performance result. The optional `build_ps4=true` CircleCI job builds a backend executable only, not the full HIMURA application, and may consume credits.
