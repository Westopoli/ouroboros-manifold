# B1 events — csrc/events.c

## Summary

E-04 event library, triggers, spawns, queue resolution. Tick steps 1 (resolve
due queue) and 2 (evaluate fresh triggers against tick-start fields), summed
per region and applied once. Skeleton already in `csrc/events.c` (all bodies
`/* STUB */`); this piece replaces every stub with a real implementation.
Contract is fixed in `csrc/ouroboros_sim.h` lines 516-665 (E-04 block) plus
the shared `om_queued_event` type in the E-05 block (lines 465-490) — do not
change any signature or struct field.

## Bible Compliance

- **Bible path:** `docs/bible/epics/E-04-events-and-chains.md`
- **Sections referenced:** S-026 through S-030 (Rules R-026-01..07,
  R-027-01..07, R-028-01..05, R-029-01..05, R-030-01..03), Inputs, Outputs,
  Invariants, "Ways this could be wrong".
- **Deliberate divergences:** S-031 (world-moves-without-you trajectory
  invariants) has no acceptance test in this window — its Python-reference
  measurement is not yet done (epic: "S-031 is not Ready") — so this piece
  does not implement anything S-031-specific beyond what S-026..030 already
  require.

## Acceptance criteria

The 31 node ids in `tests/csim/test_E04_S02[6-9]*.py`, `test_E04_S030*.py`,
`test_E04_wiring.py` (collected 2026-09-22, unchanged), each proving the
R-### rule its test name encodes:

1. R-026-01..07 — threshold crossing fires once, not on level; grace period
   ticks 1-3 prime silently; noise offset per (region, template) persists a
   whole time-jump; refiring needs a fresh crossing with a new chain tag;
   effect deltas floor at economy 8.0 / tension 12.0, ceiling 100 (needs
   `OM_FIELD_CEILING`, see NEEDS-HEADER item 1); same-tick crossings in
   different regions are judged against tick-start fields, never each
   other's post-fire state.
2. R-027-01..07 — spawn delay is one triangular(a,b,mid) draw, `round`,
   `clamp(a,b)`; condition checked at resolution time, not spawn time, and a
   failed condition drops with a `pruned` record and no probability draw;
   condition met draws probability `r` and fires iff `r <= p`; chain tag
   propagates from root to every spawn; admin chain delay/skip pattern
   (R-027-05) reads `chain_length` from the queued entry, not a fresh roll.
3. R-028-01..05 — same-tick same-region due entries sum deltas against
   tick-start fields, apply once; mutually-exclusive same-tick pair keeps by
   fixed probability table (Entrenched/Crushed) or one uniform draw at 0.5
   tie-break, loses re-queues (never cancels) at `tick + randint(1,2)`;
   independent same-tick pairs both fire; exclusion tags process in sorted
   tag order, a removed event drops out of later tags.
4. R-029-01..05 — regional revolt roll `p = 0.007 * (tension/100)^0.8`
   (`OM_REVOLT_BASE_PROBABILITY`, `OM_REVOLT_TENSION_EXPONENT`); tension 0
   gives p 0; 12-tick cooldown (`OM_REVOLT_COOLDOWN_TICKS`) after a fire, no
   roll during it; fire effects military -2 economy -2 tension +4, conditional
   spawns Revolt Crushed / Revolt Entrenched; Entrenched marks the region for
   E-07's faction-creation check (`om_region_faction_creation_pending`).
5. R-030-01..03 — `om_events_load_launch` installs exactly the 26-template
   table below field for field; a no-trigger template never starts a chain
   (spawn-only); every template's summed effect is an integer in [-4, 6].

## The 26-template launch library (verbatim, epic S-030 table)

Copy every row of the table at `docs/bible/epics/E-04-events-and-chains.md`
lines 96-123 exactly: name, trigger kind/field/threshold or probability
base/exponent/cooldown, four effect values (military, economy, tension,
population), up to two spawns (template name, delay range, probability,
condition), exclusion tag. `om_event_template_by_name` resolves a spawn's
target template id after every row has an id (two-pass load or name-index
first, effect-fill second — implementation's own internal choice).

## Contract (csrc/ouroboros_sim.h, unchanged)

- Enums: `om_trigger_kind` (NONE/ABOVE/BELOW/PROBABILITY), `om_condition_kind`
  (NONE/ABOVE/BELOW), `om_exclusion_tag` (NONE/MILITARY_RELIEF/
  POLITICAL_RESOLUTION/REVOLT_OUTCOME), `om_event_source`
  (TRIGGER/SPAWN/EXTERNAL).
- Structs: `om_spawn`, `om_event_template` (`OM_MAX_TEMPLATES` 64,
  `OM_MAX_SPAWNS` 2, `OM_TEMPLATE_NAME` 32), `om_fired_event`,
  `om_pruned_event`, `om_delayed_event`. `om_queued_event` lives in the E-05
  block (already shared with `csrc/friction.c`'s admin-revolt spawns and
  collision-adjacent conquest spawns — never redeclare it).
- Functions (all currently STUB in `csrc/events.c`): `om_step_events`,
  `om_events_load_launch`, `om_events_load`, `om_event_template_count`,
  `om_event_template_get`, `om_event_template_by_name`,
  `om_event_roll_noise`, `om_event_set_noise`, `om_event_noise`,
  `om_event_breached`, `om_event_last_fired`, `om_chain_counter`,
  `om_region_faction_creation_pending`, `om_event_queue_external`,
  `om_tick_events`, `om_tick_pruned`, `om_tick_delayed`,
  `om_region_event_delta`.
- `om_step_events(w)` is called from `csrc/sim.c`'s tick loop at step 1-2
  (before `om_step_diplomacy` etc.); the wiring itself is already landed
  (F2 freeze) — `test_E04_wiring.py::test_R026_wiring_events_step_runs`
  proves the call happens, not this piece's job to add the call site.

## Constants (csrc/om_constants.h, ALG-32..35 — never a literal in events.c)

- `OM_EVENT_NOISE_RANGE` 10.0 — noise offset range is `[-RANGE, +RANGE]`.
- `OM_EVENT_GRACE_PERIOD` 3 — ticks 1..3 prime trigger state, never fire.
- `OM_REVOLT_BASE_PROBABILITY` 0.007, `OM_REVOLT_TENSION_EXPONENT` 0.8,
  `OM_REVOLT_COOLDOWN_TICKS` 12.
- `OM_ECONOMY_FLOOR` 8.0, `OM_TENSION_FLOOR` 12.0 — military/population
  floor at 0 (no named constant; `0.0` is exempt as a bare literal).
- Ceiling 100 on every field: **blocked**, see NEEDS-HEADER item 1. Until
  `OM_FIELD_CEILING` lands, the leaf writes the clamp with the two floor
  constants and escalates the ceiling literal as a question
  (`.swarm/b1-events/questions/`) rather than guess an unlintable literal in;
  `alg_constants.py --lint csrc` is expected to flag it and that flag is
  recorded, not silently patched around.

## Controls (tests/csim/controls/test_control_e04_*.py, 9 files)

One live control per fault below; `csrc/events.c` plants the branch under
`#ifdef OM_DEBUG_INJECT` reading `w->inject == OM_BUG_<NAME>` (`om_bug_e04`
enum, `ouroboros_sim.h` lines 651-664, values 200-210):

| Bug | Control file |
|---|---|
| `OM_BUG_FIRES_EVERY_TICK` (200) | `test_control_e04_fires_every_tick.py` |
| `OM_BUG_NOISE_REROLLED` (201) | `test_control_e04_noise_rerolled.py` |
| `OM_BUG_NO_GRACE_PERIOD` (202) | `test_control_e04_no_grace_period.py` |
| `OM_BUG_COND_AT_SPAWN` (203) | `test_control_e04_cond_at_spawn.py` |
| `OM_BUG_SEQUENTIAL_DELTAS` (204) | `test_control_e04_sequential_deltas.py` |
| `OM_BUG_EXCLUSION_CANCELS` (205) | `test_control_e04_exclusion_cancels.py` |
| `OM_BUG_DRAW_BEFORE_CONDITION` (206) | `test_control_e04_draw_before_condition.py` |
| `OM_BUG_CHAIN_COUNTER_UNSAVED` (207) | `test_control_e04_chain_counter_unsaved.py` |
| `OM_BUG_TRIGGERS_READ_LIVE` (208) | `test_control_e04_triggers_read_live.py` |

`OM_BUG_E04_SLOW` (209, scale gate) and `OM_BUG_EVENTS_AFTER_FACTIONS` (210,
covered by `test_E04_wiring.py::test_control_events_after_factions_trips_the_detector`,
tick-order — sim.c's job not events.c's) are not this piece's control set to
plant a branch for beyond what the wiring test already exercises.

## Invariants (epic, verbatim)

- A threshold template fires at most once per crossing.
- Every fired event has a chain tag; spawns share the root's tag.
- No event ever pushes a field outside [floor, 100].
- Queue entries are consumed exactly once.
- Same seed, same event log, all platforms (determinism contract — no
  wall-clock, no hash-order, no non-deterministic libm call; `libm_lint.py`
  gates this).
- Over 5,000 ticks with 60 regions, the pending queue never exceeds 2,000
  entries — not gated by this piece's acceptance ids (see NEEDS-HEADER item
  2); the fixed `event_queue[64]` array is the real bound today.

## Scale requirements

Trigger evaluation for 60 regions x 26 templates under 20 microseconds per
tick; queue resolution O(due entries). Not separately gated by an acceptance
id in this window; keep the trigger loop a flat scan, no allocation per tick.

## Determinism

RNG draws only through the world's forced/PCG32 draw contract already used
elsewhere in the codebase (see `csrc/friction.c`'s admin roll or
`csrc/collision.c` for the calling pattern) — one uniform draw for the
triangular delay (R-027-01: "one uniform draw, the contract in
`ouroboros_sim.h`"), one for a spawn's probability resolution (R-027-03), one
for the regional-revolt roll, one for an exclusion tie-break (R-028-03). No
`rand()`, no `time()`, no `qsort` (banned by `libm_lint.py`'s extended list).

## Out of scope

- S-031 trajectory/pacing invariants (not Ready, no test file).
- The `OM_FIELD_CEILING` constant itself — parent territory, see
  NEEDS-HEADER item 1.
- The `event_queue[64]` vs 2,000-entry doc mismatch — parent territory, see
  NEEDS-HEADER item 2.
- Any change to `csrc/ouroboros_sim.h`, `csrc/om_internal.h`,
  `csrc/om_constants.h`, `csrc/sim.c`, `csrc/region.c` (all parent-owned).
