---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/b1-events.md
spec_lines: 1-140
test_file: tests/push/test_leaf_b1_events.py
impl_file: csrc/events.c
contract_imports:
do_not_edit:
  - "csrc/*.h"
  - "csrc/sim.c"
  - "csrc/region.c"
  - "csrc/om_constants.h"
  - "Makefile"
  - "project.godot"
  - "tests/csim/**"
  - "tests/qa/**"
  - "tests/transport/**"
  - "docs/**"
  - "scripts/**"
impl_line_budget: 900
test_assertion_budget: 20
test_owned_by: parent
---

## Task

Replace every `/* STUB */` body in `csrc/events.c` (spec_lines 1-140 of
`docs/northstar/plans/push/specs/b1-events.md`) with a real implementation of
the 18 declared functions (contract already fixed in `csrc/ouroboros_sim.h`
lines 516-665, do not touch). Implement the 26-template launch library
table verbatim from the spec's "The 26-template launch library" section,
threshold-crossing triggers with the grace period and per-(region,template)
noise offset, spawn delay/condition/probability resolution, same-tick delta
summation with exclusion-tag tie-breaking, and the regional-revolt
probability roll, per the spec's Acceptance criteria section and the
Constants and Controls sections (plant the 9 `OM_BUG_*` branches under
`#ifdef OM_DEBUG_INJECT`, values 200-208, reading `w->inject`).

```c
void om_step_events(om_world *w);
int  om_events_load(om_world *w, const om_event_template *templates, uint32_t n);
uint32_t om_tick_events(const om_world *w, om_fired_event *out, uint32_t max);
```

Mirror the RNG-draw calling convention `csrc/friction.c` already uses for its
admin roll (one call per draw, no batching) so determinism holds.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b1-events/worktrees/leaf-01/`, which is your working directory and
which the parent manages. Never run git. Nothing you do there is visible to
a sibling leaf or to the user's checkout.

Run `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_b1_events.py tests/csim/controls/test_control_e04_*.py -q -p no:cacheprovider` from
the worktree root. Confirm RED first (the adapter test and every control
already fail). Edit `csrc/events.c` in place until the adapter test is
GREEN and every `test_control_e04_*` control trips (each asserts its bug
class is detected — GREEN there means the detector fired as designed, not
that the bug is silently absent). Then also run
`make -s OPT=-O2 WERROR=1 libouroboros.so libouroboros_dbg.so` and confirm
it links clean. Stop.

Do not stage, copy, commit, or move anything. The parent commits your
declared files from the worktree onto your branch after you finish.

## Escalation triggers

Stop and report to the parent if:
- You need the `OM_FIELD_CEILING` constant (or any other symbol) added to
  `csrc/om_constants.h` or `csrc/om_internal.h` — file a contract proposal
  per the template's protocol; do not hardcode a bare `100.0` literal
  (`alg_constants.py --lint` will flag it and events.c has no allowlist
  entry). `.swarm/b1-events/NEEDS-HEADER.md` already records this gap; add
  your proposal alongside it rather than guessing a workaround.
- Any control test's fault site does not map cleanly onto a single `if`
  branch keyed on `w->inject == OM_BUG_<NAME>`.
- Two acceptance tests seem to require contradictory behavior.
- impl approaches the 900-line budget with tests still failing.

## Assumption log

Log every inferred value (e.g. the internal representation choice for the
pending queue's condition fields, or how ties are broken when the spec is
silent) to `.swarm/b1-events/briefs/leaf-01.ASSUMPTIONS.md` before you
finish, per the standard format in `brief-template.md`.
