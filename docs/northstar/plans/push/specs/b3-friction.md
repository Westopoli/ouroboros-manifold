# B3 friction, admin revolts — csrc/friction.c

## Summary

E-05 S-040 (empires fracture: admin revolt rolls) and S-041 (hostile
borders wear you down: border friction). Two independent tick steps, both
in `csrc/friction.c` (4 STUB functions): border friction (ALG-25) runs on
every inhabited owned region with a hostile neighbor; admin revolt rolls
(ALG-29) run per owned region, queuing an `OM_EVT_ADMIN_SEPARATIST` marker
entry directly into `w->event_queue[]` on success (this piece writes the
queue entry itself — do not call `om_event_queue_external`, E-04's own
external API, which is still a stub in another piece's parallel work; write
directly to `w->event_queue[w->event_queue_n++]` and fill every field,
mirroring the shape `csrc/collision.c`'s neighbor piece or
`csrc/events.c`'s E-05 block comment describes for the entry: `due_tick`,
`region_idx`, `template_id = OM_EVT_ADMIN_SEPARATIST` (101), `probability =
1.0`, `chain_tag` assigned however this ABI already assigns one (grep
`event_queue_n` / `chain_tag` usage elsewhere in `csrc/*.c` for the pattern,
or increment a region/tick-local counter if nothing else sets one yet —
log the choice in ASSUMPTIONS.md), `source_faction`, `chain_length = L`,
`cond_kind = OM_COND_NONE` (0)).

## Bible Compliance

- **Bible path:** `docs/bible/epics/E-05-faction-agents-and-conflict.md`
- **Sections referenced:** S-040 (R-040-01..05), S-041 (R-041-01..05).
- **Deliberate divergences:** none.

## Acceptance criteria

`tests/csim/test_E05_S040_empires_fracture.py` (5 tests) +
`tests/csim/test_E05_S041_hostile_borders_wear_you_down.py` (5 tests) = 10
node ids, no separate wiring test file for this piece.

1. **R-040-01/02** (`algorithms.md` ALG-29) — per faction, `excess =
   max(0, territory_count - OM_ADMIN_REVOLT_INFLECTION_POINT)` (4);
   `chance = OM_ADMIN_REVOLT_BASE_RATE + OM_ADMIN_REVOLT_SCALING_RATE *
   excess^2` (0.001 + 0.0005*excess²). One RNG draw **per owned region**,
   region-index ascending (not one draw per faction — that is
   `OM_BUG_ADMIN_ROLL_PER_FACTION`, the control this piece plants).
   `om_tick_admin_rolls` must report one `om_admin_roll` row per owned
   region every tick, `triggered` 0 or 1, `chance` and `draw` as rolled.
2. **R-040-03** — a triggered roll draws one more integer L uniform in
   [3, 8] (forced-draw contract: `a=3, n=6, L = a + floor(u*n)`) and writes
   one `om_queued_event` (see Summary) at `due_tick = tick+1`, `probability
   1.0`, `chain_length = L`, `cond_kind` NONE. This piece does **not**
   expand L into the named chain steps (Separatist/Political
   Crisis/Popular Support/Military Defection/Breakaway) or their individual
   due ticks — that is E-04's `om_step_events` reading `chain_length`
   later (R-027-05, a different piece).
3. **R-040-04** — nothing in this piece's own logic needs to special-case
   an in-flight admin chain; the chain's persistence is entirely E-04's
   concern once queued. (Test asserts observable behavior only through
   `read_admin_rolls`/`read_event_queue`, not anything friction.c
   recomputes after queuing.)
4. **R-040-05** — also not this piece: E-07 (a different piece) reacts to
   the eventual Admin Breakaway event. Nothing to implement here beyond
   correctly queuing the R-040-03 marker.
5. **R-041-01..05** (`algorithms.md` ALG-25) — for each inhabited region
   with an owner, over every neighbor across a `border` or `both`
   `om_edge_type` (never `trade`) owned by a **different** faction where
   either side's `om_stance` toward the other is `HOSTILE`:
   `Δtension_f = OM_BORDER_FRICTION_TENSION` (0.15), `Δeconomy_f =
   OM_BORDER_FRICTION_ECONOMY` (0.05), flat per hostile neighbor, never
   scaled by the neighbor's military. Sum over all qualifying neighbors;
   `tension = min(100, tension + sum)`; `economy = max(OM_ECONOMY_FLOOR,
   economy - sum)`. An empty neighbor, a same-faction neighbor, a
   trade-only edge, or a non-hostile stance each contribute nothing.
   `om_tick_friction` reports one `om_friction` row per region with any
   nonzero contribution (`hostile_neighbors` count, `d_tension`,
   `d_economy`).

## Contract (csrc/ouroboros_sim.h / csrc/om_internal.h, unchanged)

- `om_friction` struct: `region_idx`, `hostile_neighbors`, `d_tension`,
  `d_economy`. `uint32_t om_tick_friction(const om_world *w, om_friction
  *out, uint32_t max);`
- `om_admin_roll` struct: `tick`, `faction_id`, `region_idx`, `chance`,
  `draw`, `triggered`. `uint32_t om_tick_admin_rolls(const om_world *w,
  om_admin_roll *out, uint32_t max);`
- `void om_step_friction(om_world *w);`, `void om_step_admin_revolts(om_world *w);`
  (declared `om_internal.h`; already wired into `sim.c`'s tick loop at step
  4 / 4.1 — F2 freeze, do not touch `sim.c`).
- Reads `w->regions[]` (`neighbors[]`, `n_neighbors`, `faction_id`, fields),
  `w->region_edge[64][64]` (`om_edge_type`), `w->faction_stance[MAX][MAX]`
  (`om_stance`), `w->faction_budget`/territory count (grep `om_faction_territory`
  for how territory count is already computed elsewhere — mirror it, do not
  recompute a second way). Writes `w->frictions[]`/`frictions_n`,
  `w->admin_rolls[]`/`admin_rolls_n`, and (R-040-03) appends to
  `w->event_queue[]`/`event_queue_n`.

## Constants (csrc/om_constants.h — all present, no NEEDS-HEADER item)

`OM_BORDER_FRICTION_ECONOMY` 0.05, `OM_BORDER_FRICTION_TENSION` 0.15,
`OM_ECONOMY_FLOOR` 8.0, `OM_ADMIN_REVOLT_BASE_RATE` 0.001,
`OM_ADMIN_REVOLT_INFLECTION_POINT` 4, `OM_ADMIN_REVOLT_SCALING_RATE` 0.0005.

## Controls (tests/csim/controls/, 2 files this piece owns)

| Bug | Control file |
|---|---|
| `OM_BUG_ADMIN_ROLL_PER_FACTION` (107) — one roll per faction instead of per region | `test_control_e05_admin_roll_per_faction.py` |
| `OM_BUG_FRICTION_COUNTS_TRADE` (108) — trade-only edges count | `test_control_e05_friction_counts_trade.py` |

Plant both under `#ifdef OM_DEBUG_INJECT`, `w->inject == OM_BUG_<NAME>`.

## Determinism

Border friction draws no RNG. Admin revolt: exactly one draw per owned
region for the trigger chance, and (only on a triggered region) one more
integer draw for L — same contract as every other module's RNG calls.

## Out of scope

- Expanding an admin chain's `chain_length` into named steps (E-04, a
  different piece).
- E-07's faction-creation reaction to Admin Breakaway (a different piece).
- `csrc/ouroboros_sim.h`, `csrc/om_internal.h`, `csrc/om_constants.h`,
  `csrc/sim.c` (parent-owned).
