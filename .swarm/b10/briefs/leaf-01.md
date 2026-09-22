---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/B10-1.md
spec_lines: 1-56
test_files:
  - tests/push/test_leaf_B10_1.py
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
impl_line_budget: 700
test_assertion_budget: 20
test_owned_by: parent
---

## Task

Extend `csrc/unit.c` (a generated STUB file, tick-wiring only today — never
recreate it, only add to it) per `docs/northstar/plans/push/specs/B10-1.md`
(spec_lines 1-56) so `tests/csim/test_E11_S081_three_categories_a_soft_triangle.py`
and `tests/csim/test_E11_S082_the_six.py` (both fenced, do not modify) go
green.

Architecture (spec_lines 15-19, decided by the parent, not yours to
re-derive): all unit/tactical state is a single static, file-local registry
in `unit.c` — no changes to `om_world`/`om_internal.h` (both parent-owned).
Fixed capacity via a local `#define` (e.g. `OM_MAX_UNITS 4096`). `om_tactical_reset(w)`
rebinds the registry's owner to `w` and clears every row; every other
function defensively treats a registry whose `owner != w` as freshly reset,
since `world_factory`'s per-test `om_world_free` can hand a new `om_world`
the same malloc address a freed one had.

Implement the symbol list at spec_lines 33-35 (category multiplier, roster
profile accessors, spawn/damage/hp/alive, `om_tactical_run`/`om_tactical_run_until_eliminated`,
`om_command_attack_target`, `om_roster_register_custom_unit`). Category
multipliers come from the `OM_CATEGORY_MULTIPLIER_*` defines already in
`csrc/om_constants.h` (spec_lines 22-23) — do not re-literal the matrix.
The roster table itself is `tests/csim/test_E11_S082_the_six.py`'s
`ROSTER_TABLE` dict — read it directly as the source of truth for the nine
per-unit-type stat rows (spec_lines 26-27); do not guess or transcribe
values from anywhere else. Every other declared `unit.c` symbol (abilities,
rendering reads, traits) is out of scope for this increment — leave
`om_tactical_step`'s existing stub behavior alone and give anything else a
minimal stub (spec_lines 36-38). `om_tactical_run`/`om_tactical_run_until_eliminated`
need only enough of a stationary combat loop to play out S-081's fights
(spec_lines 38-40) — no movement/targeting AI, that's a later piece.

Determinism (spec_lines 43-45): iterate the unit registry in a fixed order
(spawn/unit_id order) every tick, never hash-map order.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b10/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to
anyone until the parent commits it.

Confirm RED first, then GREEN:

```
~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/csim/test_E11_S081_three_categories_a_soft_triangle.py \
  tests/csim/test_E11_S082_the_six.py
```

Then also confirm the adapter passes:
`~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_B10_1.py -q`

Then run both lints from repo root and confirm exit 0 on each:
`~/Projects/agora/.venv/bin/python scripts/specfactory/alg_constants.py --lint csrc`
`~/Projects/agora/.venv/bin/python scripts/specfactory/libm_lint.py csrc`

Do NOT stage, copy, or move anything — the parent commits your declared
files. Do NOT modify test files. Do NOT create files outside `impl_files`
(only `csrc/unit.c`). Do NOT edit anything in `do_not_edit`.

Small implementation choices (registry struct layout, internal helper
names, exact combat-loop shape within the stationary-fight constraint) are
yours. Escalate only a decision with weight beyond your own file (e.g. you
believe a header change is genuinely unavoidable) by writing
`.swarm/b10/questions/leaf-01-Q1.md` and proceeding under a recorded
best-guess in `leaf-01.ASSUMPTIONS.md` — but re-read spec_lines 15-19 first,
the no-header-change path is deliberate and should work.

When green, report back: "leaf-01 green" plus the files you changed and a
one-line summary of the registry design you used.
