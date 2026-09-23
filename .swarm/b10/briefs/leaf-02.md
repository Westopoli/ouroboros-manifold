---
leaf_id: leaf-02
spec_file: docs/northstar/plans/push/specs/B10-2.md
spec_lines: 1-58
test_files:
  - tests/push/test_leaf_B10_2.py
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
impl_line_budget: 500
test_assertion_budget: 20
test_owned_by: parent
wave: 2
---

## Task

Extend `csrc/unit.c` (already carries B10-1's S-081/S-082 work — read the
whole file first, especially the `g_unit_registry` static struct and its
`om_registry_bind`/`om_registry_start_new_battle_if_stale`/`battle_ticked`
machinery) per `docs/northstar/plans/push/specs/B10-2.md` (spec_lines 1-58).

Two parts, first is mandatory before the second:

1. **Migration (spec_lines 9-16).** `struct om_world` (`csrc/om_internal.h`,
   already on this base, do not edit it) now has `void *tactical_state`,
   `void (*tactical_state_free)(void *)`, `uint64_t world_serial`. Replace
   the file-static `g_unit_registry` (and every `owner`/`battle_ticked`
   check) with a heap-allocated struct stored in `w->tactical_state`,
   lazily allocated on first use via a helper, freed automatically by
   `om_world_free` through the registered `tactical_state_free` hook
   (already wired in `csrc/region.c` — do not touch that file, just rely
   on it). Delete the ABA-hazard comment block and `battle_ticked` entirely
   — it is fully superseded, not layered on top of. `om_tactical_reset(w)`
   still clears the struct's contents, just through the new pointer.
   Confirm this didn't regress S-081/S-082 (re-run their two test files —
   must stay green) before moving on.

2. **S-083 (spec_lines 20-24).** Implement `om_unit_profile_trait_count`,
   `om_unit_profile_ability_count`, `om_unit_apply_trait_modifier`,
   `om_unit_set_hp`, `om_tactical_step` per spec_lines 28-38. Built-in
   roster units report `trait_count == 0` and `ability_count == 1`
   (Q-083-01 resolved — no trait exists in code today, but the modifier
   mechanism must still work generically, exercised directly by the fenced
   test). Warden passive aura (R-083-03, spec_lines 22-23): friendly units
   within 300 wu take 10% less damage (diminishing per additional Warden:
   first 0.10, second 0.05) and regain 0.075 HP/tick per Warden in range
   (this part stacks linearly, unlike the damage reduction), applied inside
   `om_unit_deal_damage` (damage-reduction lookup) and once per
   `om_tactical_step` call (regen). Read `om_tactical_step`'s current stub
   body and `om_tactical_run`'s B10-1 combat-loop body before writing this
   — don't fork per-tick logic that already exists, reuse it.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b10/worktrees/leaf-02/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to
anyone until the parent commits it.

Confirm RED on S-083 first (S-081/S-082 should already be green from the
base you're starting on), then GREEN on all three:

```
~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/csim/test_E11_S081_three_categories_a_soft_triangle.py \
  tests/csim/test_E11_S082_the_six.py \
  tests/csim/test_E11_S083_stats_traits_ability.py
```

Then `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_B10_2.py -q`,
then from repo root:
`~/Projects/agora/.venv/bin/python scripts/specfactory/alg_constants.py --lint csrc`
`~/Projects/agora/.venv/bin/python scripts/specfactory/libm_lint.py csrc`
— both must exit 0.

Do NOT stage, copy, or move anything — the parent commits your declared
files. Do NOT modify any test file. Do NOT create files outside
`impl_files` (only `csrc/unit.c`). Do NOT edit anything in `do_not_edit`.

Small implementation choices (heap-struct helper naming, whether the trait
modifier also touches max_hp, exact aura-lookup shape) are yours. Escalate
only a decision with real weight beyond your own file by writing
`.swarm/b10/questions/leaf-02-Q1.md` and proceeding under a recorded
best-guess in `leaf-02.ASSUMPTIONS.md`.

When green, report back: "leaf-02 green" plus the files you changed and a
one-line summary of the migration and the Warden-aura implementation.
