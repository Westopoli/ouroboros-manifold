# Lane P: the layout engine and the places (spec, rev 1, 2026-10-13)

**Status: spec, not launched.** Audit by a fresh Sonnet auditor next, then Westley approves, then the Dispatcher launches on his go. Pre-flight reports: `~/Projects/om-push/scratch/preflight_places/` (four read-only scouts of 2026-10-13, copied there from the Architect's scratchpad; the facts below cite them as `[S1..S4]`).

## Why

Westley, 2026-10-13, on the settlement shot: "there should be existing (neutral) towns that contain resources (economy) out on the map, some small some big ... the town is supposed to follow the biome engine in its stochasticity (remember it's a *sister* system)"; "let the economy system (layout engine) decide where those go, nothing hard coded"; "Your base: depends on the archetype, an attacker can't have a full town since they're attacking, they have a forward base." Rules rewritten the same day: E-17 R-191-06, R-193-01; E-22 R-177-02 (commit e5c0feeb).

Pre-flight finding that sizes the lane: **there is no layout engine in the C sim** `[S1]`. `csrc/tactical_mapgen.c` is a skeleton (`om_map_generate`, `_spine`, `_gradients`, `om_map_is_valid`, `select_layout_uniform` are stubs, :495-508, :602, :774); `om_mission_instantiate_map` (`csrc/mission.c:2701-2768`) places the objective at the canvas centre and one spawn at the top and bottom centre, after `om_terrain_generate` (:2720), then structures and `om_economy_init` (:2765-2767). The eight layouts and nine place kinds exist only in Python (`simulation/layout_library/*.json`, `simulation/layout_instantiator.py`). None of R-187-*, R-191-*, R-192-* (bar a partial R-192-01), R-195-* is built `[S1 §4]`. The settlement field has one core, the objective (`csrc/economy_density.c:153`), grows from one cell with no noise, lanes every 4th row and column (:106), lots at exact cell centres (`economy_lots.c:49-50`), cap 2,048 `[S2]`.

So lane P builds the layout engine in C with the places as its first job, then the multi-town growth, then the contract and wiring, then the client. The nine S-113 layout kinds (chokepoints, vantages, flank routes and the rest) are **not** in this lane: Westley 2026-10-03 wants the eight old layouts audited against the lab's layout search before any pairing (ROADMAP section 4); lane P leaves a hook for them (P1's place list is the same list they will join).

## What the player sees when the lane is done

A ground mission begins among towns that have been there for years: several neutral settlements of different sizes sit where the land is good for them (water, flat ground), with resource sites near them and the richest ground opposite the objective; the player's own base is a grown town in a defensive mission and a forward camp in an attacking one; every town's edge is ragged and follows the ground, never a square; towns keep growing during play. Stories: S-191 (places), S-193 (settlement), S-222, S-237 (the look, lane E's shot), S-177 (base kinds). Acceptance is the S-191 play's shot, judged by Westley.

## Pieces, in landing order

Every piece: tests first by a different agent, red on the built tree for the stated reason, positive control green; `pre_gate.sh` before the push; one owner per file (rows below go into `pieces.toml` with the launch). Shared files are held today `[S4]`: `ouroboros_sim.h`, `signatures.toml`, `mission.c`, `checksum_full.c` by VG-CONTRACT-E7 (queued); `save.c`, `checksum_full.c`, `architecture.md` by VG-W2 (queued); `economy_density.c`, `economy_lots.c`, `strongpoint.c`, `economy_internal.h`, `scenes/settlement/**`, `tests/csim/test_VG_E_*.py` by VG-E1 (in_flight; its S-237 verdict is now in, rejected 2026-10-13, so the Dispatcher closes or attaches VG-E1 before P3) and VG-E1R (queued); `om_pipe.c` by SV-0 (queued); `mission.c` also by VG-E-prodslot. Lane P therefore starts in new files (P1, P2) and its shared-file pieces (P3 to P5) queue behind those rows in the order the Dispatcher already keeps for `architecture.md` (W2, E7, E1R, SV-0, then P4).

### P1 `csrc/layout_engine.c`, `csrc/layout_internal.h`, `tests/csim/test_VG_P_p1_*.py` (new files; owner VG-P1)

The engine. Pure function of (seed, canvas, archetype, player count, terrain readers), no world mutation, no libm, integer noise only (`om_tn_value2`, `om_tn_fbm2` from `om_internal.h:472-473` `[S2 §3]`).

```c
/* csrc/layout_internal.h (internal; the public getters are P4) */
typedef enum om_place_kind {
    /* the nine S-113 kinds keep the Python ids 0..8: objective 0 ... spawn_point 7, staging 8 (tests/csim/test_E17_S113_nine_kinds_of_place.py) */
    OM_PLACE_BASE_HOME = 9,          /* a side's base that is a grown town (R-177-02) */
    OM_PLACE_BASE_FORWARD = 10,      /* a side's base that is a camp (R-177-02) */
    OM_PLACE_NEUTRAL_SETTLEMENT = 11,/* R-191-06 */
    OM_PLACE_RESOURCE_SITE = 12,     /* R-191-03, R-177-06 */
    OM_PLACE_EXPANSION_SITE = 13,    /* R-191-05 */
    OM_PLACE_ECONOMIC_LOCATION = 14  /* R-191-03: a good place with no town yet */
} om_place_kind;

typedef struct om_place {
    double x, y;          /* canvas wu */
    int32_t kind;         /* om_place_kind */
    int32_t side;         /* -1 neutral, else faction slot */
    int32_t age_steps;    /* growth steps the settlement has lived before the mission; 0 for non-settlements */
    int32_t richness;     /* 0..100, resource sites only (R-177-06); 0 otherwise */
} om_place;

#define OM_PLACE_CAP 64
typedef struct om_layout_result { om_place places[OM_PLACE_CAP]; int32_t n; } om_layout_result;

/* Terrain readers the engine takes as callbacks, so P1's tests run on a stub terrain and the real one. */
typedef struct om_layout_terrain {
    void *ctx;
    double (*height_at)(void *ctx, double x, double y);
    int (*is_water)(void *ctx, double x, double y);
    int (*is_reachable)(void *ctx, double x, double y);   /* nearest-reachable rule, R-200-04 */
    double (*slope_at)(void *ctx, double x, double y);
} om_layout_terrain;

int om_layout_places(uint64_t seed, double canvas_w, double canvas_h, int32_t archetype,
                     int32_t n_players, const om_layout_terrain *t, om_layout_result *out);
```

Algorithm (all numbers are named drafts; Westley vetoes on the shot):
1. **Bases.** One per side: player's at (canvas_w/2, 0.15·canvas_h), enemy's at (canvas_w/2, 0.85·canvas_h) as today (`mission.c:2748-2749`), snapped to reachable ground; kind from the archetype table `DRAFT-base-kind`: Defensive Stand, Multi-Front Defense, Containment, Counterinsurgency → player BASE_HOME, enemy BASE_FORWARD; Siege Breaking, Reconquest, Assault, Suppression, Interception → player BASE_FORWARD, enemy BASE_HOME; Evacuation → both BASE_FORWARD. `[B R-177-02 table, E-22:194-201]`. Home bases get `age_steps = DRAFT-home-age` 400; forward bases 0.
2. **Objective** as today (`mission.c:2746`), kind 0.
3. **Economic locations by scoring, not by count** (Westley: "nothing hard coded"). Sample the canvas on a 400 wu grid; score each reachable, non-water cell: `s = 0.45·water_within(600 wu) + 0.30·flatness(slope < 0.06 within 300 wu) + 0.25·noise`, where `noise = om_tn_fbm2(seed ^ SALT_PLACES, x, y)` scaled 0..1, `SALT_PLACES` = 402 (`terrain.c:353-368` stop at 401 `[S2]`); cells within `DRAFT-places-spacing` 2,400 wu of a base, the objective or an already chosen place score 0. Choose greedily in score order while `s > DRAFT-places-floor` 0.55. The count falls out of the land: on the 16,000 wu canvas the control fixture gives 3 to 7.
4. **Kinds and ages.** Each chosen location becomes a NEUTRAL_SETTLEMENT with `age_steps = round(DRAFT-town-age-min 80 + (DRAFT-town-age-max 400 − 80) · u)`, `u = noise at the place`, so sizes spread from hamlet to town ("some small, some big"); the highest-scoring location opposite the objective (farther from the objective than the player's base, R-191-04 and Westley 2026-09-23 "significant resources placed opposite of the objective") also gets a RESOURCE_SITE 300 wu from it with `richness = 50 + 50·region_economy` (region economy 0..1 from `om_economy_init`'s sample, `economy.c:5-14`; which region is Q-193-09, open, interim the first HOME region as today). Every other location gets an EXPANSION_SITE at 300 wu (R-191-05). ECONOMIC_LOCATION is the kind of a chosen location that got no settlement (none in this rule; the kind exists for the later layout pairing).
5. Cap `OM_PLACE_CAP` 64; result order is deterministic (score, then x, then y).

Tests (`tests/csim/test_VG_P_p1_layout.py`, ctypes on the exported symbol as `tests/csim/test_VG_E_e1q_field.py` does): same seed twice gives byte-equal place lists; different seeds differ; no two places within 2,400 wu; no place on water or unreachable ground (stub terrain with a lake and a cliff); the base-kind table for all ten archetypes; ages in [80, 400]; exactly one RESOURCE_SITE and it is farther from the objective than the player's base; runtime under `DRAFT-places-budget` 20 ms on the 24,000 wu canvas (the mapgen rule is 50 ms for layouts, E-17:447-449 `[S1 §5]`). Positive controls: the stub that returns a constant score fails spacing; a stub without noise fails the "different seeds differ" test. Red reason: the file does not exist.

### P2 `csrc/economy_growth_noise.c`, `tests/csim/test_VG_P_p2_*.py` (new files; owner VG-P2)

The noisy growth factor and the contour lanes as pure functions P3 will call (new code in new files; P3 is the wiring into the held files):
- `double om_growth_noise(uint64_t seed, int32_t gx, int32_t gy)` returns `0.75 + 0.5·v`, `v = om_tn_fbm2(seed ^ SALT_GROWTH 403, gx·100, gy·100)` in 0..1, so a hop is multiplied by 0.75 to 1.25 `[DRAFT-growth-noise-band]`.
- `int om_lane_cell(const om_layout_terrain *t, int32_t gx, int32_t gy)`: a cell is a lane cell when a contour line crosses it (floor(height/`DRAFT-lane-contour` 40 wu) differs between the cell centre and its east or north neighbour) or it is within one cell of water (R-193-09: streets along contour lines and rivers). Replaces `gx%4==3 || gy%4==3` (`economy_density.c:106`).

Tests: noise band bounds over 10,000 cells; the same seed reproduces; a flat stub terrain has no contour lanes and a sloped stub has lanes along its contour; positive control: a stub returning constant height gives zero lane cells except by water.

### P3 multi-core growth and pre-growth (`csrc/economy_density.c`, `csrc/economy_lots.c`, `csrc/economy_internal.h`, `csrc/om_internal.h`, `tests/csim/test_VG_P_p3_*.py`; owner VG-P3; after VG-E1 and VG-E1R are attached)

- `om_economy_state` (`om_internal.h:86-112`) gains `cores[OM_PLACE_CAP]` `{cell, age_steps, side, economy}` and `n_cores`; `core_cell` stays as `cores[0].cell` for readers until P4 removes it. `density_economy` stays the mission's one value for now (Q-193-09 open); per-core economy is `density_economy · (0.5 + 0.5·age/400)` `[DRAFT-core-economy]` so big towns are richer.
- `om_density_init` takes the place list (P5 hands it in; until P5 lands, a test-only setter `om_density_set_places` feeds it): every BASE_HOME and NEUTRAL_SETTLEMENT place is a core; no core at the objective unless a place is there. Then **pre-growth**: run `max_age` growth steps in one loop, activating core i at step `max_age − age_i`, with maturity computed from the virtual tick `age·60` not the mission tick (`economy_density.c:188-189`), and one `om_lots_step` per 4 growth steps; cost measured 0.15 ms per growth step and 0.19 ms per lot step `[S2 §2]`, so 400 steps are about 80 ms, under `DRAFT-pregrow-budget` 250 ms (no mission-start budget exists; `om_mission_setup` takes 30 ms today).
- The hop in `om_density_step` multiplies `factor()` by `om_growth_noise(seed, gx, gy)` (P2). The seed is the mission seed `om_world_seed ^ region·0x9E3779B1 ^ archetype` (`mission.c:2719`); `terrain.c` gets a getter `uint64_t om_terrain_seed(const om_world*)` (one line, owner P3; `terrain.c` is free).
- Lane rule: `om_lane_cell` (P2) via the real terrain readers.
- Lot cap 2,048 → `DRAFT-lot-cap` 8,192 (`om_internal.h`; the state struct grows by about 150 KB); the ring scan runs per core in core order, nearest ring first across all cores (one scan over a min-heap of (ring, core)), so the cap fills evenly.
- Lot position stays the cell centre in the sim; jitter and yaw stay client-side derived from the lot id (E1k does this today; no `om_lot` field, no ABI change).
- Save: cores and ages join the economy block (`save.c:416-461`, read :722-795) and `ck_economy` (`checksum_full.c:381-420`): format 10 → the next free number after W2 (11) and E7 (12), so **13**; the pins that move are listed in `[S2 §4]` and become one test-defect row `TD-VG-P-1` with this spec as the ruling. P3 therefore lands after W2 and E7, and its `save.c`/`checksum_full.c` edits are the only ones it makes to held files beyond the economy files.
- **Tests retired by the rewritten rules** (test-defect rows with the ruling, listed before the build): `test_VG_E_e1q_field.py::test_core_cell_is_the_cell_holding_the_objective` (R-191-06: cores are places), `::test_flat_land_reach_after_k_growth_steps_is_at_least_k` and `test_VG_E_e1b.py::test_one_ring_per_tick`, `::test_decay_bound` (R-193-01: the front is noisy; replaced by a band test: reach after k steps is between 0.6k and 1.3k), `::test_..._symmetric_about_the_core_under_transposition` and `::_eight_fold_symmetric` (R-193-01: never symmetric; replaced by "two seeds give different fronts"), `test_VG_E_e1q_lots.py::test_no_lot_on_a_lane_cell_...` and `::test_control_rule_model_detectors`, `test_VG_E_e1c.py::test_streets_are_left_open` (R-193-09 lanes follow contours), `test_VG_E_ke5.py::test_ke5_init_gives_terrain_side_one_active_and_objective_core` (several cores). `test_economy_zero_gives_zero_density_everywhere` and the frontier round-trips stay and must pass.
- New tests: a flat stub with three places pre-grows three towns whose lot counts order by age; a town's bounding box is never a square (the ratio of lots inside the inscribed ellipse to lots in the box is above 0.80 for every core with age ≥ 200; the scout measured 0.72 for today's square `[S0 2026-10-13 scout]`); save/load round-trips cores and ages byte-identically; pre-growth time under 250 ms on the real terrain.

### P4 contract piece (`csrc/ouroboros_sim.h`, `docs/northstar/spec_factory/signatures.toml`, `csrc/pipe/pipe_tactical.c`, `csrc/pipe/om_pipe.c` `write_mission` only, `docs/architecture.md`, `tests/transport/test_pipe_vg_p.py`; owner VG-CONTRACT-P4; after E7, W2, E1R, SV-0; second-Fable audit of the paragraph)

Documented before implementation:
- `mission` frame gains `places: [{x, y, kind, side, age_steps, richness}]` (static per mission; written in `write_mission`, `om_pipe.c:770`) and `base_kind` (the player's base place kind).
- Full tactical frame gains `settlements: [{id, cx, cy, side, age_steps, lots}]` (one per core, `lots` the live count), written beside `write_tactical_economy` (`pipe_tactical.c:232`), full frames only like `strongpoints`.
- `lots` rows gain a 7th column `settlement` (core index); `write_lot_row` (`pipe_tactical.c:215`), the changed-check at :276 widens to it; `lots_dump` carries it.
- Public getters: `om_place_count`, `om_place_get(i, om_place*)`, `om_settlement_count`, `om_settlement_get(i, ...)`; `om_lot` is unchanged. ABI bump to the number after E7's 8: **9**; `signatures.toml` rows; the ABI pins at `push_ledger_2026-09-22.md:977` move under `TD-VG-P-2`.
- Tests: the frame shapes byte-for-byte against a fixture; a neutral settlement has `side` −1; the 6-column consumers (`tests/transport/test_pipe_vg_e.py:132`, `tests/test_c_bridge_vg_e.gd`) are updated under `TD-VG-P-2` (additive column).

### P5 wiring (`csrc/mission.c` `om_mission_instantiate_map` only; owner VG-P5; after E7 and VG-E-prodslot)

`om_layout_places` runs after `om_terrain_generate` (:2720) and before `om_mission_spawn_force` (:2750); spawns use the base places; the objective node stays; `om_economy_init` receives the place list (P3's setter becomes the real call); the test-only setter is removed. Ground era only (`om_era_kind == 1`); space keeps `om_space_field_generate_nodes` and one core as today until lane D's places (not in this lane). Test: a mission on seed 1 lists ≥ 3 settlements in the full frame and the player's base kind matches the archetype table; the playthrough gate passes.

### P6 client (`autoload/c_bridge.gd` `_lot_row` and a `settlements()` reader, `scenes/settlement/settlement_layer.gd`, new `scenes/settlement/places_layer.gd`, `scenes/tactical_c/tactical_view.gd` qa_state two keys, `tests/test_vg_p_client.gd`, `tests/qa/desktop/plays/E/S-191.py`; owner VG-P6; after P4 and lane E's E1k; `settlement_layer.gd` is released by VG-E1K's attach)

`_lot_row` reads r[6]; `settlement_layer.gd` tints by side (neutral = `StructuresLayer.NEUTRAL_COLOR`, the sides as today) and draws each town's streets within its own lots only (`settlement_streets.gd` joins by settlement, not distance); `places_layer.gd` draws a resource site as a marker (placeholder: a ring of the owner colour, radius 60 wu) and nothing for expansion sites and economic locations (kinds the player meets through the economy play later, lane E); no town names in this lane (the chronicle name table is a later item). qa_state gains `settlements` (list) and `places` (list). Play S-191: ground era, seed 1, step 60 ticks, assert ≥ 3 settlements with distinct lot counts spread by at least 2× between the smallest and largest, every neutral one `side` −1, the player's base kind per archetype; shot of the opening view scrolled to the biggest town; reviewer checklist: several towns of different sizes, ragged edges, no square. Westley's verdict on that shot before any polish piece.

## Numbers and drafts (all vetoable on the shot)

DRAFT-base-kind (archetype table), DRAFT-home-age 400, DRAFT-town-age-min 80, DRAFT-town-age-max 400, DRAFT-places-spacing 2,400 wu, DRAFT-places-floor 0.55, DRAFT-places-budget 20 ms, DRAFT-growth-noise-band 0.75..1.25, DRAFT-lane-contour 40 wu, DRAFT-core-economy, DRAFT-lot-cap 8,192, DRAFT-pregrow-budget 250 ms. The scoring weights 0.45/0.30/0.25 are DRAFT-places-weights. Nothing here is a threshold Westley has given; every one is a first value to look at.

## Not in this lane

The nine S-113 layout kinds and the eight old layouts (after the lab's audit); neutral populace hold timers and flips (R-177-09, Q-177-03), resource yields (R-175-*), expansion growth into a base (R-175-01): lane E's economy play, which reads P1's places; town names; space-era places (lane D); the region-economy choice (Q-193-09, open); district slowdown and cover (Q-193-04/05, parked).

## Open flags carried

Q-191-05 (counts and spacing: here the spacing draft and the floor, the count emerges), Q-193-09 (which region's economy), Q-191-08/09/10 (plays per layout, fairness slant, space layouts: untouched). No new Q rows: every unknown above is a named draft.

## Launch preconditions (the Dispatcher's pre-flight)

VG-E1 closed or attached after the 2026-10-13 rejection; W2 and E7 landed before P3; E1R and SV-0 landed before P4; VG-E-prodslot landed before P5; the save format and ABI numbers re-read from `om_internal.h:36` and `ouroboros_sim.h` at launch (13 and 9 assume W2 = 11, E7 = 12 and 8); `om_tn_fbm2` still exported (`om_internal.h:473`); the 24,000 wu canvas fixture exists (`tests/csim/test_E17_S186_terrain_field.py`); owner rows VG-P1 to VG-P6 and VG-CONTRACT-P4 pass `owner_lint`; free build slots.
