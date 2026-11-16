# HIMURA R25D — PS4 emulation, NFS tests and CircleCI

This branch contains a **backend-only** experimental MTVU tracing optimization.
It is not the R25 full launcher/cover/Pix release, and it is not a ready-to-install PS4 PKG.

## What has changed
- The detailed 24-event VU history, per-program histograms and long-run snapshot logging are **off by default** for PS4 builds.
- Opt in, before game start, by creating `/data/HIMURA_PS4SX2/vm-vu-trace`; remove the marker and restart to restore normal mode.
- Guest microcode execution, packet synchronization, cycles and aggregate HUD counters remain in place.
- Fastmem remains OFF by default. It may improve memory translation but can crash on PS4 until fault handling is validated.

## CI workflows (no GitHub Actions required)
- `r25d-host-checks` is a small Linux test job on branch `perf/r25d-vu-trace-circleci-20261116`, **if** the repo is linked to CircleCI.
- `r25d-optional-orbis-compile` does not run automatically; explicitly pass the CircleCI pipeline parameter `build_ps4=true`. Check remaining free credits and pricing before doing so; do not authorize purchases. Its output, if successful, is **PS4 backend EBOOT + symbols**, not a full HIMURA app PKG.
- The optional job downloads the **public, SHA-256 pinned** PS4SX2 SDK v2 archive and uses the already versioned `ps4/vm/build-wsl.sh` with JIT=ON, MTVU=ON and FASTMEM=OFF. It uses no BIOS, game ISO or licensed Sony binaries committed into Git.
- To package a real R25, compile the independently maintained HIMURA frontend from the SAME intended revision, include the user-approved image/QR from the private R25D patch, and validate a new complete GP4/PKG with Orbis tools. Do not reuse old EBOOT.

## Next physical PS4 measurements
Use the **same saved race** for each A/B test (2 min after warmup). Capture FPS, emulated speed%, EE, VU1, GS, graphics errors, and audio.
Do not report frames alone: 60 FPS at 50% emulation speed is not the PS2 experience.
Run a baseline at 1x native with no turbo or frameskip, then:
1. Baseline old R25 / current experimental R25D with trace OFF.
2. Repeat with trace ON only to quantify tracing overhead.
3. Compare a later compiled Fastmem ON vs OFF only if it actually boots safely, preserving saves.
4. PS4 Pro first, then Fat/Slim separately. Report per game: NFS Underground, Underground 2, Most Wanted, Carbon, Hot Pursuit 2, ProStreet.

## External PS4 emulators researched (16 Nov 2026)
- DawnStation is reported to reach 60 FPS in Tekken 5, but its performance and architecture (Sony PS2 Classics cores) cannot be extrapolated to Need for Speed or PCSX2. News: https://www.biteyourconsole.net/2026/11/02/dawnstation-il-nuovo-emulatore-ps2-per-ps4-punta-ai-60-fps-con-upscaling/
- PS2 Classics compatibility data for PS4: NFS Carbon and Underground 2 have playable reports; Underground 2 needs a game-specific config; Most Wanted has reflection issues. https://www.psdevwiki.com/ps4/PS2_Classics_Emulator_Compatibility_List
- Never bundle proprietary Sony emulator binaries or BIOS into the distributed R25. A separately installed legally sourced alternative backend might be investigated in a later launcher integration.
- PCSX2-based PS4SX2 reports a base PS4 CPU bottleneck (EE and VU1 saturating cores) and a GTA San Andreas scene at ~50% speed. https://github.com/iHaiDeeZ/PS4SX2

**No physical PS4 FPS improvement or PS4 PKG build has been demonstrated by this branch.**
