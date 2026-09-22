# Test-audit context package — C7 / shard default / wave 1

## No project umbrella test yet

`tests/push/` is a brand-new shared directory (this is the first M3 piece to
land): there is no pre-existing `umbrella_test_cmd` behavioral test to check
alignment against. `.claude-swarm.toml`'s `umbrella_test_cmd =
"~/Projects/agora/.venv/bin/python -m pytest tests/push -q -p
no:cacheprovider"` will, after this piece lands, run this one adapter file —
it IS the seed of the umbrella, not a consumer of a prior one. Skip the
"umbrella alignment" check's cross-reference step; note that explicitly
rather than silently passing it.

## Shard's stated goal

Piece C7 (see `docs/northstar/plans/push/specs/C7.md` in full — read it).
One line: build `autoload/qa_daemon.gd` + `scenes/harness/**` so the fenced,
parent-owned `tests/test_qa_daemon.gd` goes green. That fenced test checks:
script exists at `res://autoload/qa_daemon.gd`, loads without parse error,
is a `Script`, can instantiate, has a `state()` method, and `state()` returns
a `Dictionary` with keys `scene` and `tick`.

Leaf brief: `.swarm/c7/briefs/leaf-01.md` (read it — spec_lines 1-95,
impl_files, escalation triggers).

## Test under audit

Full text of `tests/push/test_leaf_c7.py` (repo:
`~/Projects/om-push/m3/tests/push/test_leaf_c7.py` — read it directly,
it's ~15 lines).

## BOUNDARIES.md

`.swarm/c7/audits/wave-1/default/BOUNDARIES.md` (read it).

## Contract excerpts

None — this leaf's `contract_imports` is empty. `qa_daemon.gd` is pure
GDScript with no C ABI symbols from `csrc/ouroboros_sim.h` (the project's
locked `type_contract_path`); the fenced test itself is the only contract
that matters here, and it's parent-owned, unmodifiable, already on disk.

## Sibling shards

None — single-leaf wave, no sibling shards running concurrently.

## Already litigated

Nothing prior for this cascade (`c7` slug, first run).
