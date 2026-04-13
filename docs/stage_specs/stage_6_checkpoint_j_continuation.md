# Stage 6 — Checkpoint J Continuation (v2.07)

> **Note:** This doc supersedes the v2.06 continuation doc. The earlier doc described a code state (LOS blocking + hard collision, RVO not yet attempted) that no longer exists. Most of its detail has been folded into the "Current Status" section at the top of `stage_6_spec.md`. This file is the current-state resume packet.

## Status

Checkpoints A through I: **PASS** (approved by Westley).
Checkpoint J: **IN PROGRESS** — movement model is in place and stable, but two of the four sub-claims are failing on stat-balance grounds.

## What's Built and Stable

### Movement (`movement.py`)

The fine-layer steering and collision system is the v2.07 model described in `bible_combat.md` → "Pathfinding and Movement":

- **Directional probe steering** — probes ahead along heading; if blocked by a same-layer ally, sweeps ±30°/±60°/±90° and takes the first clear angle. If straight-ahead is clear, no steering force is applied at all.
- **Detour commitment** — when a deflected angle is chosen, the unit commits to traveling `STEERING_DETOUR_MIN_DIST` (60 wu) before re-probing. Prevents per-tick oscillation between symmetric probe results.
- **Hard collision push-apart** (`_resolve_collisions`) — `COLLISION_RESOLUTION_ITERATIONS` (3) passes per tick, separating any pair within `2 × UNIT_COLLISION_RADIUS` (30 wu).
- **Stationary units are immovable** — a unit with no move target, or one held in place by attack-move engagement, absorbs zero push. The moving unit takes the full overlap. This is what produces concave formations.
- **Attack-move engagement leash** (`_update_attack_move_state`) — attack-moving units anchor on first engagement. If the engaged target drifts more than 200 wu from the anchor, the unit drops the target and resumes commanded movement.

### Damage (`damage.py`)

- Standard damage formula with category multiplier × cover.
- Bombard AoE with damage cap.
- Spatial-hash-driven targeting (`update_targeting`).
- Terrain LOS check via `has_combat_los` (Bresenham on navmesh) — blocks shots through terrain obstacles.
- **No friendly LOS blocking** — units fire through allies. Removed during the v2.06 → v2.07 work.

### Test scripts

- `test_checkpoint_6j.py` — the canonical L4 gradient test (T1 head-on, T2 flank vs formed, T3a flank vs column, T3b flank vs already-engaged), 25 seeds per tier.
- The earlier matrix/tuning/mixed-comp tests from the v2.06 attempt have been deleted or are obsolete; do not use them.

## What's Failing

### L1 — Strike beats Siege: 0% Strike wins

**Root causes (per the diagnostic runs):**
1. Bombard AoE with `AOE_DAMAGE_CAP_MULTIPLIER = 4.0` clusters on Strike spawn formations and front-loads kills before Strike closes range.
2. Bastion HP (2100) is too high for Strike effective DPS to crack inside the test window. Raider squad effective DPS against Bastion = 11.25 × 1.5 = 16.9, time-to-kill ≈ 124 sec per Bastion.
3. The 0.20× Siege→Strike multiplier in `config.py` (added as a band-aid) softens Bombard-on-Strike single-shot damage but doesn't help against the AoE saturation that does the actual killing.

### L4 — Flank gradient failing

**The mechanism works.** Firing-percentage data from the gradient test shows Line firing % drops to ~57% in flank scenarios (T2/T3a/T3b) vs head-on baseline. The directional-probe + stationary-immovable rule is producing the designed concave geometry.

**The stats don't reward the geometry.** Vanguard 1000 HP vs Raider 500 HP × Line→Strike 1.5× damage means Strike is out-traded even when geometric advantage cuts Line firing by 43%. The HP gap eats the firing-percentage win.

## Resume Sequence

The bible has been updated (v2.07) to ratify the current movement model and to mark the engagement-duration rebalance as resolved at the design level. The remaining work for J is balance, plus one code fix.

### 1. Code fix — `move` command should not halt on engagement

`movement.py:244` currently halts any unit with a move target the moment it acquires an `auto_engage_target`. Per the bible's clarified Command Vocabulary (v2.07):

- `move` — pure displacement. Unit does not acquire targets, does not return fire, does not stop if attacked.
- `attack_move` — moves toward target, halts to engage when an enemy enters range, resumes on target death or leash break.

Fix: gate the engagement-halt on `store.attack_moving[uid]`. Plain `move` units should continue moving regardless of `auto_engage_target` state. May also need to suppress `update_targeting` from setting `auto_engage_target` on plain-`move` units (so they don't even pick targets) — verify with the relevant test before deciding.

### 2. Stat rebalance pass

Run a tuning pass that:
- Closes the L1 Strike-vs-Siege gap. Tuning surfaces include the Siege→Strike multiplier (currently 0.20, originally 0.75), Bastion HP, Bombard `aoe_radius`, `AOE_DAMAGE_CAP_MULTIPLIER`, Surge parameters, and Raider/Interceptor HP.
- Closes the L4 flank-gradient gap (the 2× HP gap between Strike and Line is the proximate cause).
- Preserves L5/L6/L7 duration targets and L2/L3 RPS results.

Expect this to be iterative. Use `test_checkpoint_6j.py` for L4 gradient, `test_checkpoint_6c.py` for L1/L2/L3, `test_checkpoint_6d.py` for L5/L6/L7.

### 3. Re-run all of J

Once L1 and L4 pass alongside the still-passing L2/L3 and L5–L7, run the full Tactical Review Report for J and present to Westley.

### 4. After J passes

Proceed to Checkpoint K (performance stress test) and Checkpoint L (final invariants + Tactical Review Reports across the full scenario set).

## Files Modified Since the Last Continuation Doc

- `simulation/movement.py` — directional probe + detour commitment + collision moving/stationary push split (the latest commit `acdcc9a` is the directional-probe addition).
- `simulation/unit.py` — added `detour_dx`, `detour_dy`, `detour_remaining` fields. Removed `blocked_ticks` (LOS-era residue).
- `simulation/damage.py` — friendly LOS blocking and `blocked_ticks` retarget removed. Spatial-hash targeting and terrain LOS check kept.
- `simulation/config.py` — `STEERING_PROBE_DIST`, `STEERING_DETOUR_MIN_DIST` added; `RVO_*` and `LINE_OF_FIRE_ENABLED` / `BLOCKED_RETARGET_TICKS` removed; `STEERING_SEPARATION_RADIUS` removed (probe model uses no separation force); UNIT_STATS rebalanced; `CATEGORY_MULTIPLIER["Siege"]["Strike"] = 0.20`; ability flat values (`RALLY_HEAL_AMOUNT`, `WARDEN_AURA_REPAIR_RATE`) at current live values.
- Test files for the v2.06 RVO attempt were deleted during the revert; do not look for them.
