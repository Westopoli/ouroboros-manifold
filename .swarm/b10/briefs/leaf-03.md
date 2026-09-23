---
leaf_id: leaf-03
spec_file: docs/northstar/plans/push/specs/B10-3.md
spec_lines: 1-62
test_files:
  - tests/push/test_leaf_B10_3.py
impl_files:
  - csrc/unit.c
contract_imports:
do_not_edit:
  - csrc/ouroboros_sim.h
  - csrc/om_internal.h
  - csrc/om_constants.h
  - Makefile
  - project.godot
  - tests/**
  - docs/**
  - csrc/agent.c
  - csrc/chronicle.c
  - csrc/collision.c
  - csrc/diplomacy.c
  - csrc/enemy_macro.c
  - csrc/events.c
  - csrc/faction.c
  - csrc/fog.c
  - csrc/friction.c
  - csrc/generational.c
  - csrc/lifecycle.c
  - csrc/mission.c
  - csrc/pipe/**
  - csrc/region.c
  - csrc/resolve.c
  - csrc/sim.c
  - csrc/tactical_mapgen.c
  - csrc/tactical_move.c
  - csrc/tactical_support.c
  - csrc/worldgen.c
impl_line_budget: 900
test_assertion_budget: 1
test_owned_by: parent
wave: 3
---

## Task

Extend `csrc/unit.c` (already carries B10-1/B10-2's work — read the whole
file first) per `docs/northstar/plans/push/specs/B10-3.md` (spec_lines
1-62): S-086, six unique per-unit abilities, manual activation, enemy
auto-activation, telegraphs, zones, and the ability-event feed.

Implement `om_command_activate_ability`, `om_unit_output_multiplier`,
`om_unit_ability_cooldown`, `om_unit_ability_active`,
`om_tactical_run_until_engagement_ends`, `om_unit_damage_reduction`,
`om_tactical_telegraph_active`, `om_tactical_zone_visible_to_enemy`,
`om_unit_set_ability_cooldown`, `om_tick_read_ability_events`,
`om_tactical_tick`, `om_unit_effective_speed` (spec_lines 28-32).

Two independent trigger paths (spec_lines 20-24, read this section
closely, it resolves an apparent contradiction between two of the fenced
tests): `om_command_activate_ability` is the manual path — checks only
cooldown/already-active (plus Brace's cancel-and-restart), no threshold
gate, always rejects an Interceptor. The auto-trigger check runs every
tactical tick over every unit regardless of faction, firing whichever of
the five non-Intercept abilities has its threshold condition met (Intercept
always fires through this path, never the manual one).

Exact numbers per ability, all spec_lines 12-19, all directly asserted by
`tests/csim/test_E11_S086_one_ability_each.py` (read it in full, it is the
ground truth): Surge (Raider) 60 ticks speed×2.5/damage×2.0 then 1500-tick
cooldown; Intercept (Interceptor, auto-only, 350wu enemy-Strike-on-layer
trigger) speed×1.8/damage×1.5 for first engagement then 600-tick cooldown;
Brace (Vanguard) speed=0 immediately, 40-tick windup with no bonus, then
50% damage reduction and 1.3× output, re-activation cancels and restarts
the 40-tick windup, 700-tick cooldown starting at activation; Rally
(Warden) instant +112 HP to every friendly within 400wu capped at max_hp,
1500-tick cooldown; Barrage (Bombard) 30-tick telegraph visible both sides,
then base×3.0 (through the S-081 category multiplier) to every enemy
within 100wu of the target position on the Bombard's layer, total blast
damage capped at 4×(base×3.0), 1800-tick cooldown; Fortify (Bastion) 400
ticks of 20% damage reduction to friendlies within 350wu of the Bastion's
current (moving) position, Bastion's own speed×0.4 while active, zone
visible to enemy, 1400-tick cooldown. An ability on cooldown rejects
activation with no state change (spec_lines 18).

Ability-event emission (spec_lines 34-36): every activation, manual or
auto, appends an `om_ability_event` (already declared in
`csrc/ouroboros_sim.h`: tick/unit_id/ability_id/target_x/target_y/duration/
telegraph_ticks/cue_id/radius) to a per-tick buffer that
`om_tick_read_ability_events` drains on read. Ability-id-to-unit-type is
1:1 by declared order (Raider=0..Bastion=5, matching `OMAbility` in the
test file).

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b10/worktrees/leaf-03/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to
anyone until the parent commits it.

Confirm RED on S-086 first, then GREEN on all four:

```
~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/csim/test_E11_S081_three_categories_a_soft_triangle.py \
  tests/csim/test_E11_S082_the_six.py \
  tests/csim/test_E11_S083_stats_traits_ability.py \
  tests/csim/test_E11_S086_one_ability_each.py
```

Then `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_B10_3.py -q`,
then from repo root:
`~/Projects/agora/.venv/bin/python scripts/specfactory/alg_constants.py --lint csrc`
`~/Projects/agora/.venv/bin/python scripts/specfactory/libm_lint.py csrc`
— both must exit 0.

Do NOT stage, copy, or move anything — the parent commits your declared
files. Do NOT modify any test file. Do NOT create files outside
`impl_files` (only `csrc/unit.c`). Do NOT edit anything in `do_not_edit`.

Small implementation choices (per-unit ability state layout, the exact
auto-trigger radius for Surge/Brace/Barrage beyond "consistent with the
fenced test," event-buffer sizing/clearing) are yours. If you find a
genuine contradiction between two fenced tests (like B10-2's leaf found
between S-081 and S-083), verify it concretely before assuming it, write
it to `.swarm/b10/questions/leaf-03-Q1.md`, implement the behavior that's
actually correct per the bible/S-081 contract, and report the discrepancy
honestly rather than forcing a wrong number.

When green, report back: "leaf-03 green" plus the files you changed and a
one-line summary of the ability-state design and auto-trigger mechanism.
