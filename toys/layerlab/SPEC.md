# Layer lab: build spec

Written 2026-09-30 by the Architect. This is the contract the Engineer builds against, with `include/layerlab.h`. Where this file and the plan disagree, this file wins. Why the lab exists, what it must show, and the dimension map: `docs/northstar/research/layer_dynamics/README.md`. The bible rules it carries: `docs/bible/epics/E-01-layer-system.md` (rule ids below are E-01's). Register rows it follows: Q-001-03, Q-001-04, Q-004-02 to Q-004-05, Q-005-02, Q-008-01 to Q-008-03.

The lab is a research tool. It measures damage and vision relationships between layers, not pathing, so movement is deliberately crude (section 5.10). It is standalone: nothing in `csrc/` is linked or copied. Production numbers are starting values only. Two production routines are re-implemented from reference, not copied: the Taylor `sincos` (`csrc/tactical_move.c:296-306`) and the segment-disc cover test (`csrc/fog.c:265`).

## 0. Ownership and fences

- Architect owns: this file, `include/layerlab.h`, `scenarios/base.toml` values, the README in `docs/`. The Engineer does not edit them; a needed change goes back to the Architect as a question in the report.
- Engineer owns, per rung (section 11): the files that rung lists. Write fence for every spawn: `toys/layerlab/**` only. No git commands that change state; the Architect commits.
- No sub-agents. Report once, at the end, in caveman style, under 150 words: what passed, what failed, what is open.
- A test is never weakened to pass. A failing test the Engineer believes is wrong goes in the report with the reason; it is not edited around.

## 1. Layout (relative to `toys/layerlab/`)

```
include/layerlab.h          ABI (Architect)
src/ll_math.c               PCG32, Taylor sincos, helpers
src/ll_terrain.c            grid queries, slopes, flow fields (Dijkstra)
src/ll_vision.c             can_see, side visibility, pulse, cover
src/ll_move.c               goals, steering, slopes, timed transfers, separation, facing
src/ll_combat.c             acquisition, fire, damage queue, area, burst ability
src/ll_sim.c                ll_run, tick loop, termination, trace, probes
src/ll_internal.h           shared internal structs (Engineer)
Makefile
layerlab/                   Python package (import name `layerlab`)
  ffi.py scenario.py terrain.py formations.py run.py sweep.py replay.py log.py __main__.py
scenarios/base.toml  r0_raiders_10v5.toml  r2_bombard_screen.toml  (more per rung)
tests/conftest.py test_*.py
results/log.md              kept; PNG and GIF ignored (results/.gitignore)
README.md                   written in R3
```

Run everything from `toys/layerlab/`. `python3 -m layerlab ...`. Python with `tomllib` (3.11+), numpy and matplotlib (all installed on this machine); no other dependency.

## 2. What is under test (the rules the sim carries)

| Rule | Where it lands |
|---|---|
| 5 layers, layer 1 bottom, one layer per unit at every tick (invariant) | `eff_layer` (5.1) |
| Terrain mask binary per layer per cell (R-001-04); a unit never occupies a blocked cell on its layer (R-001-01) | terrain (6), movement (5.10) |
| Terrain-forced auto-transition (R-001-05) and its edges (Q-001-04 reading a) | flow field (5.10) |
| Slopes (R-001-06, R-004-06 to R-004-08) | 5.9 |
| Walking vs flying (R-001-07, Q-004-04) | 5.9, 5.10 |
| Timed transfer, one duration, any distance (Q-002-01, R-004-01) | 5.8 |
| Halfway rule, transitioning units attack while they can see (R-004-02) | 5.4, 5.8, 5.9 |
| Cross-layer vision, vantage, interference, elevation bonus (R-005-01 to 07) | 5.2 |
| Pulse (R-006-01 to 05) | 5.7 |
| Cover by height, never reduces damage or movement (R-007-01 to 05) | 5.3 |
| Cross-layer fire: range, damage, area by signed offset (Q-008-03, the unknowns) | 5.4, 5.5 |

Production fidelity: where production is symmetric and E-01 says otherwise (R-005-05, Q-005-02) the lab runs production's symmetric table by default and takes vision by signed offset so the asymmetric reading is one table edit.

## 3. Defaults (`scenarios/base.toml`)

Everything below is the default; a scenario overrides by deep-merge. Types carry production numbers (`csrc/om_constants.h`), `movement_kind = "fly"` for all six (Q-004-05 reading a1), cost computed by the power rating: `cost = hp * dmg / interval / 31.25` (Vanguard = 100; Q-074-01) unless the type sets `cost` explicitly, `body_radius = 15`, `arc_deg = 360`, `turn_rate` 6.0 / 4.0 / 2.5 for Strike / Line / Siege.

| Type | cat | hp | dmg | interval | range | speed | sensor | transition_s | aoe_r |
|---|---|---|---|---|---|---|---|---|---|
| raider | Strike | 250 | 9.0 | 0.8 | 200 | 150 | 800 | 1.0 | 0 |
| interceptor | Strike | 325 | 6.0 | 1.0 | 250 | 130 | 1000 | 1.2 | 0 |
| vanguard | Line | 500 | 7.5 | 1.2 | 300 | 80 | 700 | 2.5 | 0 |
| warden | Line | 375 | 4.0 | 1.5 | 350 | 70 | 800 | 2.0 | 0 |
| bombard | Siege | 400 | 17.5 | 3.0 | 1200 | 50 | 300 | 4.0 | 150 |
| bastion | Siege | 1050 | 7.0 | 1.8 | 800 | 40 | 300 | 5.0 | 0 |
| caster (lab-only) | Line | 120 | 4.0 | 1.5 | 450 | 55 | 700 | 3.0 | 0 |

`caster`: ability burst, `ab_dmg_mult = 6.0`, `ab_radius = 120`, `ab_windup_s = 1.5`, `ab_cooldown_s = 12.0`, `ab_min_targets = 3`, `cost = 150` (explicit: expensive, per the strategic-depth pillar). Lab-only; it stands in for the storm shape and is not a game unit.

Rules defaults: `vis_factor = [0, 0, 0.2, 0.5, 1.0, 0.5, 0.2, 0, 0]`; `vantage_vis_factor = [0, 0.2, 0.4, 1.0, 1.0, 1.0, 0.4, 0.2, 0]`; `sensor_elev_bonus_per_layer = 0.15`; `range_mult = dmg_mult = aoe_layer_mult = [0, 0, 0, 0, 1, 0, 0, 0, 0]` (same-layer only, Q-008-01: cross-layer fire is off until a scenario turns it on); `category_mult` rows (attacker) Strike `[1.0, 0.75, 1.5]`, Line `[1.5, 1.0, 0.75]`, Siege `[0.20, 1.5, 1.0]`; `aoe_cap_mult = 4.0`; `pulse_radius = 500`, `pulse_reveal_s = 2.0`, `pulse_cooldown_s = 20.0`; `transition_speed_mult = 1.0`; `separation_weight = 0.5`; `spawn_jitter = 10`; flags `fire_requires_vision = 1`, `facing_gates_fire = 0`, `halfway_mode = 1 (rule)`, `auto_transition = 1`, `cover_mode = 1`, `chase_when_idle = 0`, `forced_change_penalty = 100000`, `timed_new_layer_at_half = 1`; `max_ticks = 6000`, `stalemate_ticks = 400`. Terrain default: 80 x 40 cells of 50 units (arena 4000 x 2000), preset `flat`, `layer_spacing = 0`.

## 4. The knobs the lab sweeps

The `ll_rules` fields and the unit-type fields are the sweep surface. Any scalar is swept by dotted path (section 8). The ones the experiments lean on: `rules.range_mult[i]`, `rules.dmg_mult[i]`, `rules.aoe_layer_mult[i]`, `rules.vis_factor[i]`, `rules.vantage_vis_factor[i]`, `rules.sensor_elev_bonus_per_layer`, `terrain.layer_spacing`, `rules.halfway_mode`, `rules.auto_transition`, `rules.forced_change_penalty`, `types.<name>.<field>`, group counts, formation parameters, terrain preset parameters. A path that does not resolve is an error, never ignored.

## 5. Tick and behavior

One tick is 1/20 s, `dt = 0.05`. Iteration is always in index order (unit id = index in `spawns`); no hash order, no pointer order, no wall clock.

### 5.1 Effective layer
`u.layer` is the layer the unit counts as being on. It is recomputed at the start of every tick (step 2) from the unit's movement state:
- Not changing layer: its layer.
- Timed transfer from L0 to L1, elapsed `e`, duration `D = transition_s`: L0 while `e < D/2`; from `D/2` on, L1 if `timed_new_layer_at_half` else L0 until `e >= D`, then L1.
- On a slope with bottom layer `B`, top `T`, `n = T - B`, position `t` in [0,1]: `B + count of k in 1..n with t >= (k - 0.5) / n`. At the midline of a one-layer slope the unit counts as upper (R-004-06 "at or above"). Direction (up or down) does not matter.

A unit is `changing` while in a timed transfer or on a slope.

### 5.2 Vision
`can_see(o, t)` (observer alive; both layers effective):
1. `off = LL_OFFS(o.layer, t.layer)`. `f = in_vantage(o) ? vantage_vis_factor[off] : vis_factor[off]`. `in_vantage`: observer xy inside any vantage disc (any layer). If `f <= 0`, false.
2. `interf` = sum over zones with `zone.layer == o.layer` and `d < r` of `intensity * (1 - d / r)`, clamped to [0,1] (d xy distance from observer to zone centre).
3. `elev = max(0, 1 + sensor_elev_bonus_per_layer * (o.layer - t.layer))`.
4. `eff_r = o.sensor * (1 - interf) * elev * f`.
5. `d3 = sqrt(dx^2 + dy^2 + (dl * layer_spacing)^2)`, `dl = o.layer - t.layer` (with spacing 0 this is xy distance). Visible if `d3 <= eff_r`.
6. If `cover_mode`, not blocked (5.3).

Side visibility, computed once per tick (step 3) into `side_sees[side][unit]`: unit `e` is seen by side `S` if any alive unit of `S` `can_see(e)`, or `e.pre_revealed` and `e.side != S`, or a pulse of side `S` covers it (5.7). Target acquisition and the fire check both read `side_sees`; there is no second visibility function.

`ll_probe_can_see(sc, seed, o, t)` runs spawn placement and evaluates step 5.2 for the pair at tick 0 (`can_see` only, no side union).

### 5.3 Cover (R-007-01 to 05)
With `cover_mode = 1`, a disc blocks the sight line from `o` to `t` when: neither endpoint's xy is inside the disc (`dist <= r`); the closest point of the xy segment to the disc centre, at parameter `s` in [0,1], is closer than `r`; and `lerp(o.layer, t.layer, s) <= height_layer`. R-007-01 (both on 1, height 2) blocks; R-007-02 (both on 3) does not. Cover never changes damage, movement or fire: a hidden attacker still fires at an observer it can see (R-007-03); the cover test is applied only inside `can_see`. The layer interpolation is the lab's choice for cross-layer lines; it is recorded as T1-candidate and may be varied by `cover_mode` values added later.

### 5.4 Acquisition and eligibility
For every alive unit `u` in index order, candidates are alive enemies `e` with:
- visibility: `side_sees[u.side][e]`, unless `fire_requires_vision = 0`.
- `off = LL_OFFS(u.layer, e.layer)` and `range_mult[off] > 0` and `dmg_mult[off] > 0` (area units: `aoe_layer_mult[off] > 0`).
- halfway eligibility, if `e` is changing: `halfway_mode = RULE`: only attackers whose `u.layer == e.layer` (the effective layer) may target it, with `off = 4`; `BOTH`: attackers on either endpoint layer of the change (timed: from and to; slope: bottom and top) as if same layer (`off = 4`); `UNTARGETABLE`: none.
- range: `d3 <= u.range * range_mult[off]`.
- if `facing_gates_fire`: the bearing to `e` lies within `arc_deg / 2` of the facing (dot product against `cos(arc/2)`, 5.12).

A changing unit may itself acquire and fire on any candidate its own effective layer allows (R-004-02: it stops only when the transition takes its sight away, which falls out of `side_sees`: if that side no longer sees the target it is not a candidate).

Selection: policy `NEAREST` (smallest `d3`), `LOWEST_HP` (smallest absolute HP), `HIGHEST_COST` (largest type cost); ties break nearest, then lowest index.

A unit under a `MOVE` order that has not arrived does not acquire or fire. Units in an ability windup do not fire.

### 5.5 Fire and damage
Each unit has a cooldown; `cooldown -= dt` each tick (step 1). It fires when it has a target, `cooldown <= 0`, and nothing above forbids it. Firing sets `cooldown += interval_s`. A cooldown below zero on a tick with nothing to fire at is reset to 0, so an idle unit banks no shots. Initial cooldown is drawn at spawn: `U(0, interval_s)`.

All firing decisions in a tick are made before any damage applies (simultaneous fire; a unit killed this tick still fires). Events are queued and applied together in step 6:
- Direct (`aoe_r == 0`): `dmg * category_mult[a.cat][t.cat] * dmg_mult[off]` to the target.
- Area (`aoe_r > 0`): centre = target xy at fire time. Every alive enemy within `aoe_r` (xy) of the centre that passes halfway eligibility takes `dmg * category_mult * aoe_layer_mult[LL_OFFS(attacker.layer, e.layer)]`. Per target per tick, the sum of area damage is clamped to `aoe_cap_mult` times the largest single area hit it took that tick. No friendly fire.
- Burst ability (5.6) damage is applied in the same step and is not capped.

Damage dealt is counted after clamping to the target's remaining HP. A unit with `hp <= 0` after step 6 is dead; its type cost is added to `cost_lost[side]`.

### 5.6 Burst ability (the storm shape)
A unit with `ability_kind = BURST`, not winding, with ability cooldown `<= 0`: looks at visible, eligible enemies within `range`; for each, counts eligible enemies within `ab_radius` (xy) of it; takes the one with the largest count (ties nearest, then lowest index). If the count is `>= ab_min_targets`, it locks that enemy's xy as the centre and starts a windup of `ab_windup_s`; during the windup the unit does not move or fire. At expiry every alive enemy within `ab_radius` of the locked centre (enemies may have left; that is the counterplay) takes `dmg * ab_dmg_mult * aoe_layer_mult[off]` (no category multiplier); the ability cooldown starts at expiry. A caster that dies in its windup casts nothing. A cast counts as one shot.

### 5.7 Pulse (R-006)
A `pulse_capable` unit with `spawn.pulse_tick >= 0` pulses on that tick if its cooldown is ready. For `pulse_reveal_s` seconds after, its side sees every alive enemy on any layer within `pulse_radius * (1 - interf_at_pulser)` (xy) of the pulser's current position, if the pulser is alive. Cooldown `pulse_cooldown_s` from the pulse tick. No heuristic trigger.

### 5.8 Timed transfer (flyers only)
Started by `spawn.transfer_layer` at `transfer_tick`, or by a forced change (5.10). Walkers never make timed transfers. A transfer to the unit's own layer completes at once with no transition. Otherwise: duration `transition_s` whatever the distance (Q-002-01); the target layer must be open at the unit's xy when it starts (else it stays pending and starts on the first tick it is, R-002-02). During the transfer the unit moves at `speed * transition_speed_mult` and may enter only cells open on both layers (else it stands). A new transfer ordered mid-transfer becomes pending and starts when the current completes (R-004-04). The unit's `transitions` counter increments each time its effective layer value changes.

### 5.9 Slopes and walking (R-001-06, R-001-07, R-004-06 to 08)
Flyers ignore slopes: they are terrain, not paths, for them. Walkers occupy only cells where `land` has their layer's bit, and change layer only by walking a slope.

A walker mounts a slope when its flow-field step says to take it and it is within `max(body_radius, 0.5 * cell)` of the matching edge centre; it is placed at the edge centre, `t = 0` (bottom) or `1` (top). On a slope it moves along the slope direction at its own speed (`speed`, never `transition_s`; R-004-07: 600 units at speed 150 takes exactly 80 ticks, at speed 40 exactly 300 ticks), lateral position fixed on the centre line, no separation push. Each tick it compares the flow field's cost-to-go at the two edge nodes and moves toward the cheaper one (ties keep the current direction), so a changed goal turns it back (R-004-08); a unit with no goal (hold) stops where it is. It dismounts at `t >= 1` or `t <= 0` onto the edge's layer and cell. Its layer while on the slope is 5.1. Eligibility while on a slope is 5.4 with `changing` true.

### 5.10 Movement (deliberately crude; transfer class T3)
Per tick, per unit not winding and not on a slope: a goal point is chosen. `HOLD`: none (with `chase_when_idle`, the nearest visible enemy this unit could hit if in range, as for `ATTACK_MOVE`). `MOVE`: the order goal; arrival within `1.5 * body_radius`, after which the unit behaves as `HOLD`. `ATTACK_MOVE`: if a visible enemy it could hit exists and is out of range, its position (chase), but if some candidate is already in range the unit stands and fires; otherwise the order goal.

Path: if the straight segment to the goal is clear (sampled every half cell; each sampled cell open on the unit's layer, and `land` for a walker) the unit steers straight. Otherwise it follows a flow field. A flow field is a Dijkstra cost-to-go from the goal over nodes `(cell, layer)`, cached by `(goal cell, movement kind, auto_transition)`:
- same-layer edges to the 8 neighbours, cost = distance, allowed if the neighbour cell is open on that layer (and `land` for walkers; no diagonal corner cutting through a blocked cell);
- flyers, if `auto_transition`: a layer-change edge `(cell, L) -> (cell, M)` for every `M != L` open at that cell, cost `forced_change_penalty * |M - L|` (so a detour on the current layer beats any change, and the nearest open layer is the cheapest change; ties go to the lower layer). With `auto_transition = 0` there are no layer-change edges and a blocked destination leaves the unit standing at the edge;
- walkers: a slope edge between the two edge nodes, cost = slope length, both directions;
- goal nodes: every layer on which the goal cell is open (and land for walkers). If the goal cell has none, the goal snaps to the nearest cell that is open on the unit's current layer by centre distance, and the unit stops there (R-001-05 second clause).

A step whose next node changes layer starts a forced timed transfer to that layer at the current xy (5.8) and the unit keeps following the field. Steering is toward the next node's cell centre. Movement is axis-separated against blocked cells (try the full step, then x, then y). After movement, same-layer separation: for pairs `i < j` both not on a slope, effective layers equal, `overlap = r_i + r_j - d > 0`: each is pushed apart by `overlap / 2 * separation_weight` along the pair axis (along +x if `d == 0`); a push into a blocked cell is skipped.

### 5.11 Termination and outcomes
After step 6: a side with no alive units loses; both empty the same tick is `MUTUAL`. Otherwise `STALEMATE` after `stalemate_ticks` consecutive ticks with no damage applied; `CAP` at `max_ticks`. `ticks` is the number of ticks run.
- `hp_ratio[s]`: remaining HP of side `s` over its starting HP. `survivors`, `cost_lost`, `damage_dealt`, `shots` per side. `transitions`: total across units.
- `first_shot_side/tick`: the first tick any shot is fired; if both sides fire on that tick, side 0 is recorded (the trace shows the tie).
- `first_contact_tick`: first tick on which any `side_sees` entry is set for an alive enemy.
- `unanswered_ticks[s]`: ticks on which side `s` fired at least one shot and side `1 - s` fired none, counted only while both sides have alive units.
- `unit[i]`: final xy, hp, layer, alive, transitions.

### 5.12 Numerics
Doubles only. `sqrt` is allowed (IEEE correctly rounded); no other libm call in the sim path (`sin`, `cos`, `atan2`, `pow`, `exp` are banned). Facing is stored as a unit vector. `sincos` is the production Taylor series (7 terms, argument wrapped to [-pi, pi]): used to turn `facing_deg`, `arc_deg / 2` and the per-tick turn step into vectors and cosines. Turning: if `dot(facing, desired) >= cos(step)` snap to desired, else rotate by `step = turn_rate * dt` toward desired using the sign of the cross product. Arc test: `dot(facing, bearing) >= cos(arc / 2)`; `arc_deg >= 360` skips the test.

### 5.13 RNG
PCG32 exactly as the contract at `csrc/ouroboros_sim.h:310-322` (reference `pcg32_random_r`; `inc = (seed ^ 0xDA3E39CB94B95BDBULL) << 1 | 1`, `state = 0`, step, `state += seed`, step; `u` from two outputs with 53 bits; `U(lo, hi) = lo + (hi - lo) * u`). The only draws, in this order, per spawn in index order: jitter x `U(-j, j)`, jitter y `U(-j, j)`, initial cooldown `U(0, interval_s)`. Nothing else touches the stream. (The re-implementation follows the written contract; it does not copy production code.)

## 6. Terrain presets (`layerlab/terrain.py`)

A preset builds `open` and `land` arrays and the slope list from parameters. `open` bit `L-1` is set unless the preset blocks layer `L` there; `land` defaults to equal `open` (every open layer is a deck a walker can stand on) except as stated. Arena `W x H` in cells; `h` = blocked height (layers `1..h` blocked inside the footprint); strips are defined by x.
- `flat`: all open, all land.
- `block`: a rectangle `bw x bh` cells at the arena centre, layers `1..h` blocked, `land` cleared on those layers there.
- `wall`: a strip `wt` cells thick in x across the arena centre, spanning y from `end_gap` cells from the bottom to `end_gap` cells from the top (open ends), layers `1..h` blocked.
- `barrier`: a strip `wt` cells thick in x spanning the full y range, layers `1..h` blocked.
- `lane`: two blocks above and below a channel `ch` cells wide at the arena's mid-y, each spanning a strip `wt` thick in x, layers `1..h` blocked; channel open on all layers.
- `ramp`: a barrier from `x1` to the arena's far edge (the plateau), layers `1..h` blocked there. Ground layer `g` (default 1). `land` outside the plateau: only layer `g`. `land` inside the plateau: only layers `h+1..5`. One slope on the plateau's face at mid-y: bottom edge centre `(x1 * cell, mid-y)` on layer `g`, direction `+x`, length `sl`, width `sw`, top layer `h+1` (it spans `h + 1 - g` layers). The slope's top edge centre must fall inside the plateau on layer `h+1`; the preset asserts it. Flyers ignore `land`.

Every preset validates: spawns land on open (and land for walkers) cells; slope edge cells are `land` on their layers; slope footprints do not overlap. Violations raise before the C call.

## 7. Formations (`layerlab/formations.py`)

Return `(x, y, facing_deg)` per unit for `n` units; parameters per group. `line`: perpendicular to the group's facing, `spacing` apart, centred at `(x, y)`. `column`: along the facing. `box`: `cols` wide grid. `concave`: units on a circle of radius `R` around `center = (cx, cy)` (the enemy's centre), spanning `arc_deg` centred on the bearing from `center` to the group's `(x, y)`, each facing `center`. `screen`: `n_screen` units on a circle of radius `screen_r` around the group's `(x, y)` (the protected unit stands at `(x, y)`), facing outward, spanning `arc_deg` centred on the enemy bearing; the protected unit is a separate group. `spacing` default is `2.5 * body_radius`. Placement is pure geometry: no draws.

## 8. Python driver

- `ffi.py`: ctypes mirror of the header; at import, assert `ll_abi_version() == 1` and `ll_sizeof(i)` equals `ctypes.sizeof` for each mirrored struct; builds nothing (the Makefile builds `build/liblayerlab.so`; `tests/conftest.py` runs `make` once).
- `scenario.py`: loads a TOML with `extends = "base.toml"` (deep merge of dicts, lists replaced); schema: `[rules]`, `[type_defaults]` (merged under every type) and `[types.<name>]` (field overrides; `movement_kind = "fly" | "walk"`, `category = "strike" | "line" | "siege"`, `cost` optional), `[terrain]` (`preset`, preset parameters, `layer_spacing`, optional `[[terrain.cover]]`, `[[terrain.vantage]]`, `[[terrain.zone]]`, `[[terrain.slope]]`), `[[groups]]` (`side = "A" | "B"`, `type`, `count`, `formation` and its parameters, `x`, `y`, `facing`, `layer`, `order`, `goal = [x, y]`, `pre_revealed`, `transfer_layer`, `transfer_tick`, `pulse_tick`, `target_policy`), `[run]` (`max_ticks`, `stalemate_ticks`). `set_path(scn, "rules.range_mult[5]", v)` and `groups[0].count` style dotted-index paths; an unresolvable path raises `KeyError`. `to_c(scn) -> ll_scenario` and a `scenario_diff(a, b)` returning the changed dotted paths (used by the log).
- `run.py`: `run(scn, seed=0, trace=False, lib="O2") -> Result`. `lib` is `"O2"` (`build/O2/liblayerlab.so`), `"O0"`, or a path. `Result` is a dataclass with one attribute per `ll_result` field under the same name (`winner` an int; `survivors`, `hp_ratio`, `cost_lost`, `damage_dealt`, `shots`, `unanswered_ticks` as 2-tuples; `unit` as a list of dicts with `x y hp layer alive transitions`), plus `trace` (numpy structured array of shape `(ticks, n_units)` with the 20-byte record dtype `x y hp progress layer side alive flags`, or `None`) and `raw` (the exact bytes of the C `ll_result`, for byte comparisons). `layerlab.ffi` exports `WIN_NONE WIN_A WIN_B WIN_STALEMATE WIN_CAP WIN_MUTUAL` with the header's values. `layerlab.scenario` exports `load(path) -> dict`, `set_path(scn, path, value) -> dict` (returns a modified copy), `scenario_diff`, `to_c`. A win for `expect` (`"A"` or `"B"`) is `winner == expect`; anything else is not a win, and stalemate and cap counts are reported separately.
- `sweep.py`: `sweep(scn, var, values, seeds=range(5), var2=None, values2=None, metric="win_rate", expect="A") -> SweepTable`. Metrics: `win_rate`, `hp_ratio_A`, `hp_ratio_B`, `ticks`, `unanswered_A`, `unanswered_B`, `cost_lost_A`, `cost_lost_B`. Prints a fixed-width table (one line per value; a matrix for two variables) with mean over seeds, the count of stalemates and caps, and the seed range; saves a matplotlib PNG to `results/` (line plus per-seed scatter; heatmap for two variables); `find_crossings(xs, ys, level=0.5)` returns the interpolated x where the series crosses the level, in order; the table prints them. Appends to `results/log.md` through `log.py`.
- `log.py`: `append(entry)`; each entry carries date, the command line, `scenario_diff` against `base.toml`, the table, the PNG path, and a transfer class (`T1`, `T2`, `T3`; section 12) that the caller must pass (no default).
- `replay.py`: `replay(trace, terrain)` as `matplotlib.animation.FuncAnimation`: top-down view, colour per side, marker shape per type category, layer keys `1` to `5` filter or highlight a layer, HP bars, hollow marker while changing layer, slopes drawn as bands with the midline, `save_gif(path)`. No other graphics library (pygame is not installed).
- `__main__.py`: `python3 -m layerlab run <scenario.toml> [--seed N] [--set path=value ...]`, `sweep <scenario.toml> --var path --values a,b,c [--var2 ... --values2 ...] [--seeds N] [--metric m] [--expect A|B] [--class T1|T2|T3]`, `replay <scenario.toml> [--seed N] [--gif path]`.

## 9. Build and determinism

`Makefile` builds `build/liblayerlab.so` from `src/*.c`. Flags: `-std=c11 -Wall -Wextra -Iinclude -fPIC -fno-fast-math -ffp-contract=off -fno-math-errno`, plus `-msse2 -mfpmath=sse -fexcess-precision=standard` only when `uname -m` is `x86_64` (they fail on this arm64 Mac). Targets: `all` (O2), `O0`, `O2` (separate dirs `build/O0`, `build/O2`), `clean`. `OPT` and `WERROR` variables as in the root Makefile. The Makefile and `src/*.c` produce no warnings with `WERROR=1`.

Determinism gate: the same scenario and seed twice give identical `ll_result` bytes and identical trace bytes; the O0 and O2 builds give identical trace bytes; different seeds differ (jitter and cooldown draws).

## 10. Tests (`tests/`, pytest; `conftest.py` builds the lib once)

Each test's docstring names the E-01 rule or register row it mirrors. Positive control for every detector.

1. Determinism: twice identical; O0 vs O2 identical; seeds 0 and 1 differ.
2. Positive control: `r0_raiders_10v5` (10 vs 5 raiders, flat, same layer, attack-move): A wins on 20 of 20 seeds. Mirror (5 vs 5 identical, same formation): winners split across 20 seeds with each side winning at least 4.
3. Negative control: A on layer 5, B on layer 1, both `hold`, default rules (cross-layer off), `fire_requires_vision = 1`: `winner = STALEMATE`, `damage_dealt = [0, 0]`, `shots = [0, 0]`, `first_contact_tick = -1`.
4. `can_see` isolation on R-005-01 to 07's numbers (observer sensor 1000 on layer 3; enemy layer 3 at 900, layer 4 at 400 and 600, layer 5 at 150 and 250, layer 1 at any distance with the default table, vantage case, interference 0.5 case), via `ll_probe_can_see`, with a positive and a negative case each. R-005-05 is run twice: default (symmetric table; two layers below at 150 is visible) and the asymmetric table (zero for offsets 2 below), both as explicit tests naming `Q-005-02`.
5. Cover: R-007-01 and R-007-02; a disc that contains an endpoint does not hide it; cover never changes damage (same scenario with `cover_mode` 0 and 1 and the observer able to see in both: identical damage totals).
6. Halfway rule from both sides: a flyer in a timed transfer from layer 3 to 4 (`transition_s = 2`), with a same-layer attacker on 3 and another on 4: the layer-3 attacker fires at it before 1.0 s (tick 20) and not after; the layer-4 attacker the reverse; `halfway_mode` 0 and 2 change this as defined. The changing unit itself fires at a visible target and stops when the target leaves its sight.
7. Auto-transition ruling: a `barrier` with `h = 2`; a flying raider on layer 1 ordered across: `auto_transition = 1` arrives on layer 3 (nearest open layer) and was in a timed transfer at the strip's near edge; `= 0` stops at the edge. With `forced_change_penalty = 0` and an open end shorter than the transfer cost, it takes the shorter route (Q-001-04 b); with 100000 it takes the detour (a). A destination blocked on every layer: the unit stops as close as it can on its layer.
8. Slopes: `ramp` with `h = 1`, `sl = 600`: a walking raider (speed 150) takes 80 ticks (+/- 1) from mounting to dismount, a walking bastion (speed 40) 300 ticks (R-004-07); on a 150-long slope 20 and 75. Eligibility: below the midline an attacker on the lower layer may target the climber and one on the upper layer may not; at and above the midline the reverse (R-004-06). Turn back: a walker given a goal that reverses before the midline dismounts at the bottom with `transitions = 0`; after the midline it ends with `transitions = 2` (R-004-08). A walker at a `barrier` with no slope never crosses. A flyer ignores the slope and crosses by timed transfer. A slope spanning two layers (`h = 2`, `g = 1`): two cross-overs at `t = 0.25` and `0.75`.
9. Area damage: bombard against a 3-unit cluster, `aoe_layer_mult` zero for off-layer neighbours: only same-layer units are hit; the per-target cap holds (4 bombards firing on one tick deal at most `4.0 x` one hit to a target).
10. Burst ability: `caster` against 3 clustered raiders deals `dmg * 6.0` to each inside the locked centre at expiry; a target that left the radius during the windup takes nothing; a caster killed in its windup casts nothing.
11. Arc gate (R2): a unit facing away does not fire with `facing_gates_fire = 1` and does with `= 0`; it turns at `turn_rate`.
12. Crossing detector: `find_crossings` on a synthetic sigmoid returns the known crossing within 1e-9 (positive control); on a flat series returns none (negative control); the count-ratio sweep (1:2 to 2:1 of equal forces on flat) shows a crossing between 0.8 and 1.25 (positive control from the README).
13. Speed gate: 20 v 20 raiders, a 25-value sweep x 5 seeds completes in under 20 s on this machine; the test prints the time.

## 11. Rungs (one Engineer spawn each; the Architect reviews before the next)

| Rung | Content | Done when |
|---|---|---|
| R0 | `ll_math.c`, `ll_sim.c` (loop, spawn, RNG, termination, trace), `ll_combat.c` (nearest target, direct fire, same-layer area, category matrix, cooldown), flat `ll_move.c` (straight steering, attack-move, hold, move, separation), `ll_terrain.c` stub (flat grid queries), `ll_vision.c` (5.2 steps 1 to 5 and `side_sees`; no cover, no pulse), Makefile, `ffi.py`, `scenario.py`, `run.py`, `terrain.py` (preset `flat` only), `formations.py` (`line` only), `scenarios/base.toml`, `scenarios/r0_raiders_10v5.toml`, tests 1 and 2. All header fields exist; layer-related ones are inert (read, validated, unused). | `make -C toys/layerlab && python3 -m pytest toys/layerlab/tests -q` green for tests 1 and 2; Makefile warning-free at `WERROR=1`; a 10 v 5 run prints a result |
| R1 | `ll_terrain.c` (masks, land, slopes, Dijkstra flow fields, straight-segment clear test), `ll_vision.c` (5.3 cover and 5.7 pulse added), `ll_move.c` (timed transfers, forced change, slopes, walkers), `ll_combat.c` (all cross-layer knob sites, halfway eligibility), `terrain.py` presets `block wall barrier lane ramp` and the scenario terrain schema; tests 3 to 9 | tests 1 to 9 green |
| R2 | facing, turn, arc gate; `formations.py` (`column box concave screen`); burst ability; `r2_bombard_screen.toml`; tests 10 and 11 | tests 1 to 11 green |
| R3 | `sweep.py`, `replay.py`, `log.py`, CLI, `README.md` (how to run a run, a sweep, a replay; the knob table), first log entries from the controls (test 12 sweep, X0, X1); test 12 and 13 | tests 1 to 13 green; `results/log.md` has the count-ratio crossing entry |

R0 is two passes: C first, then driver and tests. Each pass reports separately.

## 12. Transfer classes (every log entry and PNG title carries one)

- **T1** rule geometry that ports to the game as is: vision tables, cover-height LOS, the halfway rule, slope midline eligibility, offset multipliers, area splash, arcs.
- **T2** magnitudes whose direction transfers but whose numbers retune: win rates, HP ratios, ticks, cost lost. The lab has no economy, no Warden aura, brace, fortify, backswing or cohort targeting, no high-load halving, and fog is symmetric.
- **T3** lab-only: steering, the coarse flow fields, formation drift, pulse timing, the stalemate window.

## 13. Not built

Layer preference (S-003), hard-transfer rejection and era masks (S-011), commands during a run, per-faction fog, economy, `Q-004-05` choices other than reading (a) (the knobs that exist for them are `timed_new_layer_at_half` and the `movement_kind` per type), and any rendering beyond the matplotlib replay.
