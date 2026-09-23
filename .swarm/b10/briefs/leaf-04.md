---
leaf_id: leaf-04
spec_file: docs/northstar/plans/push/specs/B10-4.md
spec_lines: 1-42
test_files:
  - tests/push/test_leaf_B10_4.py
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
impl_line_budget: 250
test_assertion_budget: 1
test_owned_by: parent
wave: 4
---

## Task

Extend `csrc/unit.c` (carries B10-1/2/3's work) per
`docs/northstar/plans/push/specs/B10-4.md` (spec_lines 1-42): S-088, the
render-facing read surface, the last of B10's four increments.

Implement `om_unit_position_y` (spec_lines 14, same registry lookup as the
already-implemented `om_unit_position_x`, just the y field),
`om_unit_render_craft_count`, `om_cue_lookup`, `om_unit_render_silhouette_size`
(spec_lines 16). Read `tests/csim/test_E11_S088_reading_units_on_screen.py`
in full (short, exact) for every number: Raider/Interceptor craft count in
[3, 5]; silhouette size strictly ordered Strike < Line < Siege across every
unit type; `om_cue_lookup` returns an id consistent with whatever `cue_id`
you stamp on the Barrage ability event.

Required extension, not a new isolated function (spec_lines 20-24): read
the ability-event emission code B10-3 already built. Add `telegraph_ticks
== 30` and `cue_id == om_cue_lookup("cue_barrage_telegraph")` to the
Barrage activation event, and `radius == 350.0` (confirming `duration ==
400` already holds) to the Fortify activation event.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b10/worktrees/leaf-04/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to
anyone until the parent commits it.

Confirm RED on S-088 first, then GREEN on all five:

```
~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/csim/test_E11_S081_three_categories_a_soft_triangle.py \
  tests/csim/test_E11_S082_the_six.py \
  tests/csim/test_E11_S083_stats_traits_ability.py \
  tests/csim/test_E11_S086_one_ability_each.py \
  tests/csim/test_E11_S088_reading_units_on_screen.py
```

Then `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_B10_4.py -q`,
then from repo root:
`~/Projects/agora/.venv/bin/python scripts/specfactory/alg_constants.py --lint csrc`
`~/Projects/agora/.venv/bin/python scripts/specfactory/libm_lint.py csrc`
— both must exit 0.

Do NOT stage, copy, or move anything — the parent commits your declared
files. Do NOT modify any test file. Do NOT create files outside
`impl_files` (only `csrc/unit.c`). Do NOT edit anything in `do_not_edit`.

Small implementation choices (craft count for non-Strike types, exact
silhouette-size scale, cue-registry layout) are yours. Escalate only a
decision with real weight beyond your own file by writing
`.swarm/b10/questions/leaf-04-Q1.md` and proceeding under a recorded
best-guess.

When green, report back: "leaf-04 green" plus the files you changed and a
one-line summary of what you added.
