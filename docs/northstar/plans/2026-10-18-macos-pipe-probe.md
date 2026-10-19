# macOS pipe probe (Q-NET-05, ROADMAP section 2 step 6)

Run 2026-10-18 on main `f2ea5f78`, Apple M-series arm64, Apple clang 21.0.0, Python 3.14.7. No source or Makefile edits.

## Build

- `make pipe/ouroboros_pipe` builds clean. The Makefile already gates `-msse2 -mfpmath=sse` on x86 (ARCH from `cc -dumpmachine`) and `-fexcess-precision=standard` on a compiler probe; clang here accepted the probe, so the arm64 command line is `-O2 -fno-fast-math -ffp-contract=off -fno-math-errno -fexcess-precision=standard`. No flag change needed. (The Makefile comment says clang rejects it; Apple clang 21 accepts it. Harmless, but the comment is stale.)
- `pipe/ouroboros_pipe`: Mach-O 64-bit executable arm64, 131.6 KB, dynamic, links `libouroboros.so` (Mach-O arm64 dylib, 732.1 KB) by rpath.
- `scripts/build_pipe_macos.sh` (static, all csrc, ad-hoc signed): `dist/macos/ouroboros_pipe`, Mach-O arm64, 846.6 KB, `codesign -dv` shows flags=0x2(adhoc).
- `libm_lint.py`: OK. `nm -u` on the static exe lists no sin/cos/pow/exp/log.

## Probe, seed 3 (`scripts/net_xplat_checksum.py`)

| tick | PINNED_FULL (Linux, `test_PP_portability.py`) | Mac, dynamic pipe | Mac, static `dist/macos` pipe |
|---|---|---|---|
| 100 | 15870404153552538785 | same | same |
| 500 | 5368266331726284326 | same | same |
| 1000 | 1335582271474088983 | same | same |
| 2000 | 6505739661716914864 | same | same |

All four match both builds. The nine section words printed per tick also look consistent (regions, factions, fog constant across ticks as expected); I did not have the Linux section words to diff, only the pins.

## A99 (`test_E13_A99_tactical_equivalence.py`)

7 passed, 3 failed. The 3 failures are `fight_990_gap300`, `gap1500`, `gap3000`, all at step 0. The idle runs and `fight_502_gap100` match the recorded hashes.

| run | Mac step 0 | recorded step 0 |
|---|---|---|
| fight_990_gap300 | 738ff9c1d41b59dd | d1b5491768fc017b |
| fight_990_gap1500 | 2fb6e3e21bc42da8 | 3ed69acfbd29f922 |
| fight_990_gap3000 | 9aa75a3fdd19a468 | 36f3c836c0b40bd0 |

This is not a Mac divergence. `docs/northstar/plans/2026-10-14-skill-lab-rev2-baseline.md` records the same three ids failing on the Linux box (`/home/westopoli`, main `b8edf56e`), "pre-existing". The same Mac hashes result from a source tree at `4b785400` (before the VG-W2 route commits), so W2 did not cause them; the recording (2026-10-09) predates other sim changes, or the harness is stale. Side finding: `a99_tactical_runs.stage_fight` uses Python `math.hypot`; swapping in libm hypot or sqrt(a*a+b*b) changes the gap1500 and gap3000 step-0 hashes. So that harness depends on the Python version, a test-side portability hazard (Python 3.14 here), separate from the sim. The recorded Linux Python version is unknown.

## First divergent tick and subsystem

None: the probe matches at all four marks, so no bisection was run. (A99 fails identically on Linux, so it carries no cross-OS signal.)

## libm sites on the tick path

- Sim transcendentals are private: `om_sin/om_cos/om_atan2/om_log/om_exp/om_pow` (`csrc/sim.c:36-109`, `tactical_move.c`). Only real libm pow is `sim.c:389`, inside `#ifdef OM_DEBUG_INJECT` (debug lib only).
- Release libm calls are only correctly rounded or exact ops: `sqrt` (fog.c, events.c, resolve.c, space_plates.c), `floor`, `round` (region.c:328, space_plates.c, resolve.c:510). IEEE-exact on both OSes. `libouroboros.so` imports no sin/cos/pow/exp/log.
- Risk stays in the compiler: arm64 has FMA, so `-ffp-contract=off` is load-bearing (set). Not exercised: x86_64 macOS (`ARCH=x86_64` branch of the script).

## Codesign and packaging state

- Exists: `scripts/codesign_macos.sh` (ad-hoc `codesign -s - --force`), `scripts/build_pipe_macos.sh` (calls it). Spec (steam wiring spec, W8a and decisions): ad-hoc signing for the pipe and Mac export, notarization is Westley's step, one depot per OS, pipe in `Contents/MacOS/`. No entitlements file is named anywhere in the spec, and none exists.
- Not present before this run: `dist/` (the build above created `dist/macos/ouroboros_pipe`, untracked build output). No `.app` bundle, no notarization script, no Godot export preset verified.

## Next step for Q-NET-05 (candidates)

(a) Close the Mac row: Linux and Mac probe match at 100/500/1000/2000, record it and keep the three-OS diff for Windows (done under wine).
(b) Also run the probe on an Intel Mac or `ARCH=x86_64` under Rosetta, to cover the SSE branch.
(c) Extend the probe to a longer or second seed (for example seed 7, 20000 ticks) and a tactical-fight script before closing, since 2000 ticks of seed 3 may not reach every path.
