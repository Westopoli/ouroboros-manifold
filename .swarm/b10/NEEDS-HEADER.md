# NEEDS-HEADER — B10, om_world generation/serial field

Not blocking B10-1 (worked around locally, see `.swarm/b10/questions/leaf-01-Q1.md`), but flagging for M0/Westley before B10-2/3/4 or any other piece needs the real fix.

## Problem

`csrc/unit.c` (and likely any future module needing per-world private state, since `om_world`/`om_internal.h` have no unit-storage slot for it) tracks its own tactical state in a static registry keyed by `om_world*` identity. `world_factory`'s per-test `om_world_free()` frees a world at teardown; the next test's `om_world_new()` gets glibc's freed block back — confirmed 100% reproducible in this repo's test harness (same struct size, tight alloc/free loop, LIFO tcache reuse). A pointer-identity check (`registry.owner == w`) is therefore not a reliable "is this the same logical world" test — it silently false-negatives across test boundaries, letting one test's leftover unit state leak into the next test that happens to get the same address.

`om_world_new` calloc-zeroes the struct identically every call (same seed/n_regions in these tests), so content-fingerprinting doesn't distinguish "new" from "reused" either.

## Proposed fix (candidate, not decided)

Add a monotonically-increasing `uint64_t generation` (or `serial`) field to `struct om_world` in `csrc/om_internal.h`, bumped by a process-global counter inside `om_world_new` (`csrc/region.c`) every call, independent of the malloc address. Any module keeping a private pointer-keyed registry can then check `(owner == w && owner_generation == w->generation)` instead of pointer identity alone, which is unambiguous regardless of address reuse.

This is a one-field, additive header change (ABI 3, per the plan's `freeze/F2b`-style mechanism for post-freeze header changes) — no existing symbol signature changes, no test currently reads or asserts on it.

## What B10-1 did instead (already landed, works for its own scope)

A `battle_ticked` flag in unit.c's own registry: any spawn call after a tick forces a full reset regardless of pointer match, since no B10-1 test spawns reinforcements into an already-ticked, not-yet-reset battle. This will misbehave if a later B10 increment or another piece legitimately needs "add units mid-battle, same world, no reset" (e.g. reinforcement drops). Whoever builds that piece needs either this header fix landed first, or to lift/rework the flag check with its own solution.
