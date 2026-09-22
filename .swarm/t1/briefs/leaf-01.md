---
leaf_id: leaf-01
spec_file: docs/northstar/plans/push/specs/T1.md
spec_lines: 1-140
test_files:
  - tests/transport/test_pipe_shapes.py
impl_files:
  - csrc/pipe/om_pipe.c
contract_imports:
do_not_edit:
  - Makefile
  - project.godot
  - scripts/**
  - tests/**
  - docs/**
  - csrc/*.h
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
  - csrc/region.c
  - csrc/resolve.c
  - csrc/sim.c
  - csrc/tactical_mapgen.c
  - csrc/tactical_move.c
  - csrc/tactical_support.c
  - csrc/unit.c
  - csrc/worldgen.c
impl_line_budget: 1200
test_assertion_budget: 20
test_owned_by: parent
---

## Task

Replace the placeholder `csrc/pipe/om_pipe.c` with the real stdio pipe
server per spec_lines 1-140 of the spec file above: 4-byte big-endian
length-prefixed JSON frames both directions; write `hello` once at start
(`abi`/`layout_ok`/`checksum_cadence` from the header functions the spec
names); dispatch `cmd` frames read from stdin (`step`, `run_to`, `snapshot`,
`set_seed`, `set_feature`, `inject`, `save`, `load`, `quit`) per the spec's
command section, including the documented deviation that `set_seed` emits
no frame at all (silent reconfiguration only); stream one `delta` frame per
tick for `step`/`run_to` (region/faction diffs against the previous tick,
tick-log readers called once per step immediately after `om_world_step`);
answer `snapshot`/`set_feature`/`inject`/`save`/`load` with `ack` or `error`
per the spec; `quit` flushes stdout and exits 0.

## Acceptance

You are working inside your own git worktree — a private checkout at
`.swarm/t1/worktrees/leaf-01/`, which is your working directory and which
the parent manages. Never run git. Nothing you do there is visible to a
sibling leaf or to the user's checkout.

Run `~/Projects/agora/.venv/bin/python -m pytest tests/transport -q` for
this test_file (a directory of 3 tests spanning 2 files; only
`test_pipe_hello_snapshot_and_checksum_match_ctypes` in
`test_pipe_shapes.py` is currently red — the other two are already green
against the pre-built fixture and must stay green). Confirm the target test
is RED for the expected reason first (`pipe/ouroboros_pipe not built`,
via the test's own `skipif` — it will show as SKIPPED, not FAILED, until
the binary exists; that skip is your starting "red"). Edit `impl_files` in
place, at their normal path inside the worktree. Then build:
`make -s OPT=-O2 WERROR=1 libouroboros.so libouroboros_dbg.so
pipe/ouroboros_pipe` (must succeed with zero warnings under `WERROR=1`).
Confirm GREEN: `pytest tests/transport -q` shows all 3 tests passing (the
target test no longer skipped). Stop.

Do not stage, copy, commit, or move anything.

## Escalation triggers

Stop and report to the parent if:
- A symbol the spec or your impl needs is not in `contract_imports` and not
  resolvable by grepping `csrc/ouroboros_sim.h` yourself for the obvious
  candidate (e.g. a tick accessor, a save-state read-back function) — if you
  find it yourself by grepping the locked header, that's fine and expected,
  just cite the line you used in your ASSUMPTIONS entry; only escalate if
  nothing in the header covers the need at all.
- The impl would need to edit any file in `do_not_edit`.
- Impl approaches `impl_line_budget` (1200) with the target test still red.
- Two plausible field mappings between the doc and the header contradict
  each other AND the choice would be observed by a sibling piece (C2/C3/C4/
  C5/T2g all read this wire format) rather than staying internal to this
  file — log the internal ones as assumptions per usual; escalate only ones
  with real cross-piece weight.

## Assumption log

Log every inference to `.swarm/t1/briefs/leaf-01.ASSUMPTIONS.md` before you
finish — this piece has several deliberately-left-open field mappings (the
spec calls them out: the first hello's placeholder seed/n_regions/features,
the attack `"band"` field's doc/header mismatch, the admin-roll
triggered-only filter for `revolts`, which fields `om_tick_events` includes
beyond the doc's shape, how you obtain the current tick for `snapshot`).
Cite the spec section or header line for each.

## Sibling-assumption read

No sibling leaves in this wave (single-leaf piece). Skip.

## Question ledger

If genuinely blocked on something with cross-piece weight (see escalation
triggers), write `.swarm/t1/questions/leaf-01-Q<n>.md` per the standard
shape, proceed under best-guess, tag your ASSUMPTIONS entry
`unanswered: true`.

## Contract-proposal protocol

Not applicable unless you find the spec's `docs/architecture.md` deviation
note insufficient to proceed — in that case write
`.swarm/t1/proposals/leaf-01.md` describing the exact doc correction needed
(do not edit `docs/architecture.md` yourself, it is parent-owned) and
continue with the deviation as specced while the parent decides.
