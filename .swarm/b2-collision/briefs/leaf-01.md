---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/b2-collision.md
spec_lines: 1-90
test_file: tests/push/test_leaf_b2_collision.py
impl_file: csrc/collision.c
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
impl_line_budget: 300
test_assertion_budget: 20
test_owned_by: parent
---

## Task

Replace both `/* STUB */` bodies in `csrc/collision.c` (spec_lines 1-90 of
`docs/northstar/plans/push/specs/b2-collision.md`) implementing ALG-23/24
multi-faction collision resolution exactly as the spec's Acceptance
criteria section states (economy factor, strength, weighted-draw winner,
retention ceiling, refund, loser tension, colony starter military on
narrow margin). Group `w->decisions[]` by `target_idx`; every target with
2+ entries is a collision; apply the spec's math to it, append to
`w->collisions[]`, increment `w->collisions_n`, and remove those entries
from `w->decisions[]` (compact the array) so `om_step_resolve` never sees
them.

```c
void     om_step_collisions(om_world *w);
uint32_t om_tick_collisions(const om_world *w, om_collision *out, uint32_t max);
```

Mirror how `w->faction_tech_attack[f]` and the surprise multiplier are read
elsewhere in the E-05 block (grep `csrc/*.c` for `faction_tech_attack` and
`surprise_mult` for the existing pattern).

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/b2-collision/worktrees/leaf-01/`, which is your working directory
and which the parent manages. Never run git. Nothing you do there is
visible to a sibling leaf or to the user's checkout.

Run `~/Projects/agora/.venv/bin/python -m pytest tests/push/test_leaf_b2_collision.py tests/csim/controls/test_control_e05_collision_max_strength.py -q -p no:cacheprovider`
from the worktree root. Confirm RED first, then edit `csrc/collision.c`
until GREEN. Then run
`make -s OPT=-O2 WERROR=1 libouroboros.so libouroboros_dbg.so` and confirm
it links clean. Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- You need `OM_COLLISION_LOSER_TENSION_BASE` (or the narrow-margin `0.70`
  upper bound) as a named constant in `csrc/om_constants.h` —
  `.swarm/b2-collision/NEEDS-HEADER.md` already records this gap. File a
  contract proposal per the brief template rather than hardcoding the
  literal; proceed with the correct math using a local named `#define` or
  `static const` inside collision.c in the meantime if that keeps the lint
  question separate from correctness (log this choice in ASSUMPTIONS.md).
- `om_decision`'s field names differ from what `csrc/resolve.c` reads.
- impl approaches the 300-line budget with tests still failing.

## Assumption log

Log every inferred value to
`.swarm/b2-collision/briefs/leaf-01.ASSUMPTIONS.md` before you finish, per
the standard format in `brief-template.md`.
