# LI2 interface: `scripts/skilllab/arena/isolation_measures.py` (2026-11-24)

What LI3 (arms M, V), LI4 (arms R, F, W, P) and LI5 (table, page) call. Pinned by `tests/skilllab/arena/test_isolation_measures_*.py` and `tests/skilllab/integration/test_isolation_measures_real_*.py`. The implementer builds to this and reports a test that looks wrong as a `test-defect`, never edits it. Spec: `docs/northstar/plans/lab-isolation-2026-11-24/spec.md` sections 3, 4, 7. Pure Python over a fight document (`om-fight-2`); it imports no engine, no look-rig module (the overlap rule is copied) and no clock.

## Convention: `not measured`

`NOT_MEASURED = "not measured"`. A cell the file cannot support is a string that starts with it (`"not measured: <reason>"`), never 0, `tie`, `n/a` or an empty list. It propagates cell by cell: a file with no `fired` makes every firing cell `not measured` and leaves margin, overlap, spread, idle measured.

## Constants (each on a line with a `DRAFT-` comment; values are proposals, Westley's; tests pin the starred ones)

`DRAFT_OPENING_WINDOW_40 = 40`*, `DRAFT_STUCK_TICKS = 200` (any positive int), `DRAFT_IDLE_TICKS_200 = 200`*, `DRAFT_IDLE_FRONT_BEHIND = 40`*, `DRAFT_ARRIVED_WU_75 = 75`*, `DRAFT_STILL_WU_PER_TICK = 0.05`*, `DRAFT_STILL_SLACK_WU = 0.01`*, `DRAFT_OVERLAP_RADIUS_15 = 15`*, `DRAFT_OVERLAP_MAX_TICKS_3 = 3`*. The still rule and 75 wu are those of `r6-compare/tmp/stats.py` (the facts files).

## Reading a fight

`load_fight(path) -> dict`: every top-level key except `frames`, plus `frames`: a re-iterable object (not a list) that re-reads the file one frame at a time on every iteration. Works whether the header is before `frames` (ladder files, one line) or after (indented files with sorted keys). All functions below take that dict or an in-memory one (`frames` a list).

## Functions (all take `doc`)

| function | returns |
|---|---|
| `result_of(doc)` | `{winner: "A"\|"B"\|"draw"\|"cap", end, survivors [a, b], last_tick, defect}`; `cap` when `end == "cap"` or `capped`; any other non-A/B winner (draw, none, stall) is `draw`; `defect` is True for draw and cap |
| `survivors(doc)` | `result.survivors` (the engine's; the last frame can be a tick early) |
| `margin_survivors(doc)` | int, A survivors minus B survivors |
| `margin_hp_share(doc)` | float, `(sum hp/hp at frame 0 of A's living, last frame) / A heads - same for B`; heads = unit rows of the side in frame 0 |
| `first_contact_tick(doc)` | tick of the first frame where any unit has `fired`; `None` when none ever; `not measured` when no unit row has `fired` |
| `units_firing(doc, window_ticks=40)` | `{by_frame [[tick, A, B]...], first_contact, window_ticks, window [A, B] unit-seconds over [first_contact, +window_ticks), whole [A, B], peak [A, B]}`; unit-seconds of a frame = firing units x (tick - previous frame tick) / tick_rate; no contact: window `[0.0, 0.0]` |
| `predictions(doc, window_ticks=40)` | `{count, type, window_count, window_weighted, agreement}`; count and type are `"A"\|"B"\|"tie"`; type weights each firing unit by the category multiplier (om_constants.h:518-526; Vanguard, Warden Line; Raider, Interceptor Strike; Bombard, Bastion Siege) of its role against its target's role; target = the row's `target`, else the nearest living enemy that frame (squared distance, lower id); a target dead in the frame keeps its role |
| `agreement_word(winner, count, type)` | the lab's words (`evidence.agreement_word`) with A/B for side0/side1; `n/a` for a draw, a cap or a tie; `not measured` when a prediction is |
| `never_fired(doc)` | `{A, B, total, units_start}` (units of frame 0 never `fired`) |
| `orders_ended_short(doc, stuck_ticks=DRAFT_STUCK_TICKS)` | `{basis: "fallback: ...", alive_at_end [row], died [row]}`, row `{id, side, x, y, tick, since}` sorted by id; see the fallback below; `not measured` when `orders` has no `point` or the mode is neither `both_same_point` nor `hold_and_attack` |
| `idle_units(doc, min_ticks=DRAFT_IDLE_TICKS_200)` | `{total, arrived, behind, front, units: [{id, side, class, since, x, y}]}` at the last frame; `not measured` without `orders.point` |
| `spread_at(doc, ticks)` | `{tick: {"A": rms, "B": rms}}` in the order asked; a side with no living unit is `not measured`; a tick with no frame makes that tick's value a `not measured` string |
| `overlap_pairs(doc, radius=15, max_ticks=3)` | `{verdict "PASS"\|"FAIL", pairs [{a, b, ticks, last_tick, min_dist}], radius, max_ticks, max_per_frame, total_pair_frames}`; the look rig's `check_overlap` rule, copied: same layer, alive, distance strictly under the radius, runs counted in frames, listed when longer than max_ticks, longest run kept, min_dist of that run to 3 decimals |
| `reading(parts, whole)` | words `"pass"`, `"fail"`, `"no stated direction"` in; out `"all pass"`, `"parts pass and whole fails"`, `"a part fails and the whole crosses"`, `"all fail"`, or `"no stated direction"` (whole has none); parts with no direction are ignored; no other parameter; an unknown word is `ValueError` |
| `measure_fight(doc, spread_ticks=())` | one dict: `result, survivors, margin_survivors, margin_hp_share, first_contact_tick, units_firing, predictions, never_fired, orders_ended_short, idle_units, spread, overlap`, each equal to the function of that name; no bare `margin` key |

## The fallback for orders ended short (the file carries no per-unit destination)

The file has only `orders {mode, attacker, point}`. Ordered units: `both_same_point` every unit; `hold_and_attack` the `attacker` side. A unit's order stopped short, at its last living frame, when it has been still (moved under `DRAFT_STILL_WU_PER_TICK * frame gap + DRAFT_STILL_SLACK_WU` each frame) with no `target` for at least `stuck_ticks`, is at least `DRAFT_ARRIVED_WU_75` from `orders.point`, and no living enemy is within its notice (`sights[role]` when the file has `sights`, else `ranges[role]`, planar). `alive_at_end`: alive in the last frame. `died`: the state at the last frame the unit was alive. Idle (`idle_units`) is the same still rule without the order, notice or arrival tests, as the facts count it; behind = a living friend within `DRAFT_IDLE_FRONT_BEHIND` and nearer `orders.point`.

## Where a measure differs from the facts files (`r6-compare/out/*.facts.json`)

`never_fired`, `idle_units` and `overlap_pairs` reproduce the facts exactly (all six recorded fights). `orders_ended_short` is not in the facts: with `stuck_ticks=200` its `alive_at_end` equals idle total minus arrived on `both_same_point` files (L-0054: 0, 35, 5), and holders and units with an enemy in notice are excluded where the facts count them.

## Open for the chat (nobody decided; not tested)

- Cost-weighted margin: needs per-role cost; the fight file has none (it has `role`, `hp`, `ranges`). Not built.
- `reading` for parts that disagree while the whole fails (some pass, some fail): none of the four labels; untested.
- `orders` mode `groups` (stage 4 traps): `not measured` is not pinned either way; no per-unit destination there either.
- Notice for sight-off files is the weapon range here; Westley may mean something else (the sensor is the stage 4 notice).
- Sensor against notice distance, first-seen tick (spec 4 "new" list) belong to arm V and read `sights` and `result.first_seen`; not in LI2's brief, not tested.
