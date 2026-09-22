---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/b3-friction.md
spec_lines: 1-110
test_file: tests/push/test_leaf_b3_friction.py
impl_file: csrc/friction.c
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
impl_line_budget: 350
test_assertion_budget: 20
test_owned_by: parent
---

## Task

Replace all four `/* STUB */` bodies in `csrc/friction.c` (spec_lines 1-110
of `docs/northstar/plans/push/specs/b3-friction.md`) implementing ALG-25
border friction and ALG-29 admin revolt rolls exactly as the spec's
Acceptance criteria section states, including the two `OM_BUG_*` control
branches it lists.

```c
uint32_t om_tick_friction(const om_world *w, om_friction *out, uint32_t max);
uint32_t om_tick_admin_rolls(const om_world *w, om_admin_roll *out, uint32_t max);
void     om_step_friction(om_world *w);
void     om_step_admin_revolts(om_world *w);
```

The R-040-03 queue write goes straight into `w->event_queue[]` (see the
spec Summary for the field-by-field shape) rather than through any other
module's function. No acceptance test asserts the queued entry's
`chain_tag` value and there is no public setter for the shared
`om_chain_counter` in the contract — write a fixed placeholder (e.g. `-1`)
for `chain_tag` on entries this piece queues; log it as an assumption.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b3-friction/worktrees/leaf-01/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is
visible to a sibling leaf or to the user's checkout.

Run `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_b3_friction.py tests/csim/controls/test_control_e05_admin_roll_per_faction.py tests/csim/controls/test_control_e05_friction_counts_trade.py -q -p no:cacheprovider`
from the worktree root. Confirm RED first, then edit `csrc/friction.c`
until GREEN. Then run
`make -s OPT=-O2 WERROR=1 libouroboros.so libouroboros_dbg.so` and confirm
it links clean. Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- Territory count needs a computation you cannot find an existing pattern
  for elsewhere in `csrc/*.c` (grep `om_faction_territory`).
- Two acceptance tests seem to require contradictory behavior.
- impl approaches the 350-line budget with tests still failing.

## Assumption log

Log every inferred value to
`.swarm/b3-friction/briefs/leaf-01.ASSUMPTIONS.md` before you finish, per
the standard format in `brief-template.md`.
