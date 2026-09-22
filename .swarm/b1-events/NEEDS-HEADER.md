piece: B1 events (csrc/events.c)
manager: M1

1. No `OM_FIELD_CEILING` (or equivalent) constant in `csrc/om_constants.h`. R-026-06
   requires "ceiling 100" on every field after an event delta applies; `om_constants.h`
   has floors (`OM_ECONOMY_FLOOR` 8.0, `OM_TENSION_FLOOR` 12.0) but no ceiling constant,
   and `csrc/om_internal.h` exposes no shared field-clamp helper events.c can call.
   `alg_constants.py --lint` forbids the bare literal `100.0` in a module `.c` file with
   no allowlist entry (events.c has none). Needed before the leaf can implement R-026-06 /
   R-028-01 without an unlintable literal. Proposed fix: add `#define OM_FIELD_CEILING 100.0`
   under ALG-35 in `om_constants.h`.

2. `csrc/om_internal.h`'s `om_world.event_queue[64]` (fixed array, `event_queue_n` counter)
   contradicts `csrc/ouroboros_sim.h`'s own comment on `om_event_queue_external`
   ("A spawn that would exceed the queue capacity (2,000 entries) is dropped and recorded
   as a pruned record") and the epic invariant "the pending queue never exceeds 2,000
   entries". Not blocking B1's acceptance tests (tests/csim/test_E04_*.py, 31 ids, small
   fixtures) but flagging so the 2,000-entry invariant is not silently unbuildable later.
   No action taken by this leaf; the array stays 64 and om_event_queue_external's overflow
   path is written against the real array bound, not the doc's 2,000.
