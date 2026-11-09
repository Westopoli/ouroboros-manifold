# R5 round 1, fix 3: vantages over traffic, lanes by width, loud failures. Tests (red) first.

Role: Engineer (Sonnet 5.5), test writer. Tests only; a different engineer builds. Spawn nothing. Think tersely. Report once, under 25 lines: file, test names, run command, the red output's decisive lines.

## Westley's words (2026-11-08, per-picture round 1, `ruled.md`)

- "the vantage points purpose is to be a high ground looking over 'lanes' of 'traffic', and thus strategically valuable. (Or they could be vantage over economic resources)."
- "vantage cliff isn't even accessible at all, that should be an automatic flag for failing loudly."
- "The lanes leading toward base A are very thin, which is ok but there are only two of them. Thin = more, thick = fewer, as a general rule. We want to give both players lots of options and be specifically restrictive as opposed to accidentally restrictive."
- "it's just a dead-end, there's no reason for the player to travel there if there's not resources there"

## The rules the tests pin (Architect's reading; every number a DRAFT he owns)

Generator: the terrain-obeys assault mode, `~/Projects/om-wt/r5-obey` (branch `wip/r5-obey-shots`), `scenes/mockups/landscape/obey_layer.gd` (`_build_requests_assault`, `_vantage_beside`, `_carve_all`, `_routes`, `_assault_checks`, `_check`, `panel_text`, `_run_shots`), `obey_overlay.gd`. Tests sit beside `tests/test_mockup_obey_assault.gd` (read it for the harness: `extends SceneTree`, `scripts/run_godot_tests.sh`, generation at 16,000 wu seeds 1 to 5, `--mode assault`).

1. **Vantage overlooks traffic.** After carving, the vantage's position is within DRAFT-vantage-overlook 600 wu of a carved road centreline cell, or within DRAFT-vantage-overlook of a resource site's pad edge. The panel prints `vantage_over: road | site_0 | site_1 | none`; `none` is a check FAIL. Holds for every seed 1 to 5 (the builder moves the vantage along the road or beside a site; `vantage-near-base` stays, so a vantage beside a base must still be within reach of a road, which the base's roads give).
2. **Vantage reachable, else loud.** The walk flood from `base_a` at the 35-degree limit reaches the vantage pad (the ramp cutter or a carved climb gives the way up). If not: the check `vantage_reach` is FAIL, the panel's first line carries `FAIL`, the overlay draws the vantage ring in `FAIL_COLOR`, and the `--shot` file name gains the suffix `_FAIL` (`obey_assault_16000_<seed>_FAIL.png`). Positive control: a scratch call that moves the vantage onto an unreachable peak must produce all four signs.
3. **Lane count follows width.** The number of carved roads to each place is `clamp(round(DRAFT-lane-budget 720 / width), 1, route-max-count)`, so 180 wu gives 4, 360 gives 2, 600 gives 1; `route_count` is no longer a free roll but derived; the panel prints `lanes <width> -> <count>` per width used. Total roads reaching the objective across all widths at least DRAFT-options-min 3.
4. **Restriction is named, never accidental.** Every place reachable from `base_a` by at least two carved roads that share no cell outside the pads (R-189-07; already a check for small/big, keep it), and the only cells where the walkable corridor to a place narrows below DRAFT-route-small-width 180 wu are inside a choke's wall span; the panel prints `narrowings <n> (<n_outside_choke> outside chokes)` and the check `accidental_narrowing` is FAIL when `n_outside_choke > 0`. Measure corridor width by the erosion radius at which the place stops being reachable (`_erode` already exists).
5. **Dead ends are flagged.** A walkable connected region of at least DRAFT-deadend-area 400 cells that touches a carved road by exactly one corridor and contains no place pad is a dead end; the panel prints `dead_ends <n>`; this is a report line, not a FAIL (the fix is a later round).

Deterministic across two runs (panel identical except timing lines).

## Tests: `tests/test_mockup_obey_vantage_lanes.gd`

One assertion group per rule above, seeds 1 to 5 at 16,000 in assault mode; name this brief and the Westley sentence in each; a positive control for rules 2 and 4 (force the bad state through a scratch hook the test itself injects, for example by moving the vantage or by closing a corridor in the walk mask before the check). Expect red on: missing `vantage_over`, `vantage_reach`, `lanes` and `narrowings` panel lines, no `_FAIL` suffix, `route_count` still rolled. Do not touch `tests/test_mockup_obey_assault.gd`. Commit subject `R5 round 1: red tests for vantages over traffic, lanes by width, loud failures`, trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; add only your test file (and `.uid` if Godot writes one), never `-a`/`-A`. Another engineer is editing water code in this worktree at the same time: do not run `godot --import` with uncommitted changes of theirs staged, and `git stash` nothing.
