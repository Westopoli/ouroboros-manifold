# Sim viewer

Watch the C sim live over the debug pipe: territory hulls, edges, nodes in owner colour,
a 4-arm radar per region (military, economy, tension, population), 60-tick sparklines,
a faction sidebar and an event log. Mission mode picks a band for each mission and shows
the pipe's band beside it. Tooling only, never in the game loop.

Install (once): `uv pip install --python .venv/bin/python pygame`

Build the debug pipe: `make pipe/ouroboros_pipe_dbg`

Launch: `.venv/bin/python -m scripts.simviewer --seed 1 --n-regions 80 --rate 10 [--mode mission]`

Headless screenshots (`tick_mode.png`, `mission_mode.png`): add `--shot DIR`.

## On a Mac

Build the debug pipe natively (arm64; `ARCH=x86_64` for Intel): `scripts/simviewer/build_pipe_dbg_macos.sh`

Launch: `.venv/bin/python -m scripts.simviewer --seed 1 --n-regions 80 --rate 10` (`--pipe PATH` picks another binary; the macOS default is `dist/macos/ouroboros_pipe_dbg`).

Over plain ssh no window can open: use `--shot DIR` there.

## Keys

| Key | Does |
|---|---|
| SPACE | run / pause (tick mode: `rate` steps per second; mission mode: one advance per second) |
| RIGHT | one tick |
| `[` `]` | rate down / up (1, 2, 5, 10, 20, 50) |
| M | tick / mission mode |
| 1 to 5 | pick band 0 to 4 (total failure to total success) |
| 0 | pick refuse (band 5) |
| RETURN | mission mode: start a mission, resolve it with the picked band, then jump 50 ticks |
| F | sidebar: region inspector / tracked faction; TAB cycles factions |
| V | radar on / off |
| R | reset camera |
| mouse | drag pans, wheel zooms, left click picks a region, right click clears |
| ESC | quit |

## Known gap

Pick 0 (total failure) needs retention 0 forced, which the pipe ignores until SV-0 lands
(`mission_end` gains `retention`); until then it shows a red MISMATCH, not a crash.

Spec: `docs/northstar/plans/2026-10-12-simviewer-spec.md`.
