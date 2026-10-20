# PP-contract: the contract document for ABI 4

Written before implementation, 2026-10-02, for piece `PP-contract` (owns `csrc/ouroboros_sim.h`, `docs/northstar/spec_factory/signatures.toml`, `tests/csim/conftest.py`). Source of truth: `docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md` (the plan; its appendix is the contract), `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` (the brief) sections 5 and 6, `docs/northstar/plans/2026-10-01-architect-rulings-2.md` Addendum 45. Rulings: `docs/northstar/plans/2026-10-01-architect-rulings-2.md` Addendum 46, A131 to A136 (section 7 lists them). Where a number or a rule is the writer's and not a source's, the text says "proposed by writer"; the 59 parameter ranges are the writer's, accepted by A133 only as refusal bounds (section 4).

## 1. What lands

One ABI bump, 3 to 4, covering every call in the plan appendix (Phases A and C). No pipe frame changes shape. The pipe hello carries `om_abi_version()`, so its value reads 4 instead of 3; no frame field is added or reshaped.

New header content: two enums (`om_tac_param`, `om_emission`), one struct (`om_ping_alert`), 18 functions, and two named constants (below). No existing signature changes.

Calls marked (brief) are specified in the brief section 5; this document adds the signature in `signatures.toml` form, the error returns the brief leaves open, and the defining file.

| # | Call | Phase | Defined in | Brief |
|---|---|---|---|---|
| 1 | `double om_tactical_get_param(const om_world *w, om_tac_param p)` | A | `csrc/tactical_move.c` | G1 |
| 2 | `int om_tactical_set_param(om_world *w, om_tac_param p, double value)` | A | `csrc/tactical_move.c` | G1 |
| 3 | `int om_map_set_canvas(om_world *w, double width, double height)` | A | `csrc/tactical_mapgen.c` | plan appendix |
| 4 | `int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi)` | A | `csrc/tactical_mapgen.c` | G2 |
| 5 | `int om_command_set_layer(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t layer)` | C | `csrc/tactical_move.c` | G4 |
| 6 | `double om_unit_transition_progress(const om_world *w, uint32_t unit)` | C | `csrc/tactical_move.c` | G4 |
| 7 | `uint32_t om_unit_get_target_layer(const om_world *w, uint32_t unit)` | C | `csrc/tactical_move.c` | G4 |
| 8 | `int om_roster_set_reach(om_world *w, int unit_type, uint32_t layers_up, uint32_t layers_down)` | C | `csrc/tactical_move.c` | G5 |
| 9 | `int om_unit_profile_reach(const om_world *w, int unit_type, uint32_t *up, uint32_t *down)` | C | `csrc/tactical_move.c` | G5 |
| 10 | `int om_command_set_emission(om_world *w, const uint32_t *unit_ids, uint32_t n_units, om_emission mode)` | C | `csrc/fog.c` | G6 |
| 11 | `int om_unit_get_emission(const om_world *w, uint32_t unit)` | C | `csrc/fog.c` | G6 |
| 12 | `int om_command_ping(om_world *w, uint32_t caster, uint32_t layer, double x, double y)` | C | `csrc/fog.c` | G7 |
| 13 | `uint32_t om_ping_alert_count(const om_world *w, int32_t faction)` | C | `csrc/fog.c` | G7 |
| 14 | `int om_ping_alert_get(const om_world *w, int32_t faction, uint32_t index, om_ping_alert *out)` | C | `csrc/fog.c` | G7 |
| 15 | `uint32_t om_unit_get_group_id(const om_world *w, uint32_t unit)` | A (stub; A3 fills) | `csrc/tactical_move.c` | A133 |
| 16 | `int om_unit_get_leash_anchor(const om_world *w, uint32_t unit, double *x, double *y)` | A (stub; A3 fills) | `csrc/tactical_move.c` | A133 |
| 17 | `int om_unit_get_engaged(const om_world *w, uint32_t unit)` | A (stub; A3 fills) | `csrc/tactical_move.c` | A133 |
| 18 | `int om_command_guard(om_world *w, const uint32_t *unit_ids, uint32_t n_units)` | A (stub; PP-unit fills) | `csrc/tactical_move.c` | A170 |

Two named constants, written by hand beside `OM_MAX_UNITS` in the header, each defined once (A132, A133 Q-C3):

- `#define OM_LAYER_COUNT 5`: the number of layers. The bible numbers layers 1 to 5 from the bottom; the engine and every test count the same layers 0 to 4 (bible layer n is engine layer n - 1). Every call that takes a layer (`om_map_block_rect`, `om_command_set_layer`, `om_command_ping`, and the cover height) has the valid range 0 to `OM_LAYER_COUNT - 1`. No other file writes the literal 5 for this meaning.
- `#define OM_MAP_MAX_CANVAS 28000.0`: the largest canvas side `om_map_set_canvas` accepts. Equals `OM_CANVAS_SIZE_RANGES_LARGE_HI` in `om_constants.h` (the public header does not include that file); the fixed tables are sized for it (A134).
The plan appendix's `om_map_add_cover(..., uint32_t height_layers)` is not a call in this table (section 5).

Defining files: rows 5 to 9 are defined in `csrc/tactical_move.c`, not `unit.c`, by the coordinator's ruling on Q-C1: the contract piece must not touch `unit.c`, `mission.c` or `tactical_support.c`, so its stubs land only in `tactical_move.c`, `tactical_mapgen.c` and `fog.c`. A later wave (PP-unit) may move them to `unit.c`, where `pieces.toml` puts the layer steps and roster of Phase C. Rows 10 to 14 are PP-fog's `fog.c` ("side sight, emission and the ping"). The brief names no file for them. Rows 1 to 4 are as the task assigned them; rows 15 to 17 are A133's and sit in `tactical_move.c`, never `unit.c` (`module = "tactical_move.c"` in `signatures.toml`).

## 2. How it lands (mechanics the builder needs)

1. `csrc/ouroboros_sim.h`: `OM_ABI_VERSION` 4, `OM_LAYER_COUNT` and `OM_MAP_MAX_CANVAS` (section 1), and the comment above `om_abi_version()` gains a "Bumped to 4" sentence. The two enums are written by hand beside the other enums, as **anonymous-tag typedefs** (`typedef enum { ... } om_tac_param;`), because `sig_table.py`'s enum recogniser (`Types.enums`) matches only `typedef enum {`; a tagged `typedef enum om_tac_param {` as in the brief's sketch would leave rows that take it blocked. The 17 declarations come from `sig_table --emit` into the generated blocks of their module.
2. `docs/northstar/spec_factory/signatures.toml`: 18 `[[symbols]]` rows and one `[[structs]]` row (`OMPingAlert`, fields `tick uint64_t`, `faction int32_t`, `sector int32_t`; C name `om_ping_alert`, 16 bytes). `[meta] abi_version` becomes 4 (it reads 2 today while the header reads 3; stale before this piece). Parameter names are those in the table above. `epics`: rows 1, 2 `E-11`; rows 3, 4 `E-13`; rows 5 to 14 `E-01`; rows 15 to 17 `E-13`.
3. `tests/csim/conftest.py`: `EXPECTED_ABI_VERSION = 4`; hand-written enum mirrors `OMTacParam` (members named as the header's minus the `OM_TP_` prefix, `COUNT` included) and `OMEmission` (`SILENT = 0`, `ACTIVE = 1`); the bindings and the `OMPingAlert` mirror come from `sig_table --emit`.
4. `sig_table --emit` also appends a `/* STUB */` body for every new symbol to its module's `.c`, before the file's trailing `/* ---- end generated stubs ---- */`. That edits `tactical_move.c`, `tactical_mapgen.c` and `fog.c`, which other pieces own (never `unit.c`, `mission.c` or `tactical_support.c`). The stubs are mechanical and contain no logic; they are needed so the library links and the new tests fail on behaviour, not on a missing symbol. Ruled (A133 Q-C1): the stubs land with the contract in one merge that names `PP-contract` and the owning pieces; stubs only, no lint exemption is written, and none lands in `unit.c`, `mission.c` or `tactical_support.c`.
5. Expected red after the contract lands: the new `tests/csim/test_PP_settings.py` goes red on the stubs (a stub `om_tactical_set_param` returns 0 for everything and `get` returns 0.0). It turns green when PP-move lands the two param calls and PP-mapgen the canvas and cover calls. The three getters of rows 15 to 17 are stubs in this wave (a stub returns 0 and writes nothing); A3 fills them.

Hash baseline: with every parameter at its default and no new call made, behaviour is exactly today's. The defaults below equal today's constants wherever a constant exists.

## 3. Settings: `om_tactical_get_param`, `om_tactical_set_param`

```c
typedef enum { OM_TP_PURSUE_BY_STEERING = 0, /* ... section 4 ... */ OM_TP__COUNT } om_tac_param;
double om_tactical_get_param(const om_world *w, om_tac_param p);
int    om_tactical_set_param(om_world *w, om_tac_param p, double value);
```

Behaviour (brief G1 unless marked):
- `get` returns the current value of `p`. A new world holds every parameter at its section 4 default.
- `set` stores `value` and returns 0 when `p` is a member below `OM_TP__COUNT` and `value` is inside the member's valid range (section 4, columns lo and hi, both inclusive). Anything else returns -1 and changes nothing.
- Refused with -1 (proposed by writer, the brief says only "unknown or out of range"): `w` NULL; `p` below 0 or at or above `OM_TP__COUNT`; `value` NaN or infinite; `value` outside [lo, hi]; for kind `bool`, any value other than exactly 0.0 or 1.0; for kind `int`, a value with a fractional part.
- `get` on a NULL world or an unknown `p` returns -1.0. No valid value is negative, so -1.0 is unambiguous (proposed by writer).
- A parameter set before any unit is spawned applies to the whole fight. A parameter set mid-fight takes effect on the next `om_tactical_step` (brief G1); a set between two steps is never half applied.
- Settings are configuration, not simulation state (A133 Q-C4): they survive `om_tactical_reset`, they are neither saved nor part of `om_world_get_state_checksum`, and a new world starts at the section 4 defaults. The game never sets one, so a game trace is unaffected.
- Other files read a setting through the public `om_tactical_get_param`; no internal header change is part of this piece. Storage lives with the world's tactical state and must outlive `om_tactical_reset`: `om_tactical_reset` frees `w->move_state`, so a table kept there would be wiped.

What the parameters mean:
- `PURSUE_BY_STEERING` default 1 (A155/A156: the option c' interim default 0 is reverted). Pursuit sets the unit's move goal to the nearest visible enemy and walks it through the ordinary movement step (brief G8, plan P1).
- `ROUTE_AROUND_TERRAIN` 1: movement routes on the 100 wu per-layer grid, blocked cells block sight and fire on their layers (plan P3). 0: today's behaviour (layer 0 sampled, no route grid).
- `LEASH_BEFORE_DAMAGE` 0: today's order. 1: the Python's order, the leash runs before damage, so an attack-moving unit never shoots a target more than `ATTACK_MOVE_LEASH` from its anchor (parity requirements item 7, audit G03; plan decisions table; A125). The side Westley does not pick is deleted later, with this parameter.
- `TARGET_POLICY` 0: nearest hostile, the game's rule. 1: most damaged, lab only. "Most damaged" is the lowest hp fraction; ties go to the nearest, then the lowest unit id (A133 Q-C5).
- `TARGET_BY_SIGHT` 1: a unit acquires, keeps and fires only at targets in its side's visible set (brief G3, A125). 0: today's behaviour.
- `ROUTE_ACROSS_LAYERS` 1: the router works over cells and layers together, by travel time (brief G4). 0: the router stays on the unit's layer.
- `ATTACK_MOVE_LEASH`: distance from its anchor beyond which an attack-moving unit drops a target (today `OM_ATTACK_MOVE_LEASH_DIST`).
- `RETURN_FIRE_FLEE_DIST`: the flinch distance (today `OM_RETURN_FIRE_FLEE_DIST`).
- `UNIT_COLLISION_RADIUS`: the body size the sim uses (Q-LAB-02 (a); the Architect, 2026-10-13, widening A133 Q-C6, which had it reach the collision pass only). `tactical_move.c` reads it once per tick and uses it in the steering probe (gather, blocked and sure-blocked tests), the collision pass (pair push, neighbour list reach and slack, mark and sweep), the navmesh margins (a unit moved out of a blocked cell, the nearest reachable point) and the arrival tolerances (the unit's own 1.5 radii, the route-waypoint 2 radii, the group centroid 1.5 radii). Compile-time and unchanged by it: the broad-phase grid layout (base cell, margin), and the spawn spacing in `mission.c`, `enemy_macro.c` and `unit.c`. Changing it between ticks ends the collision pass's settled-state cache.
- `VANTAGE_MULT`: the vantage multiplier on a cross-layer vision factor, the product capped at 1.0 (today `OM_VANTAGE_CONE_MULTIPLIER`). The vantage rules that read the offset 1 and 2 factors are unchanged.
- `AOE_DAMAGE_CAP`: area damage total cap as a multiple of base damage.
- `TARGETING_COHORTS`: `unit_id % N == tick % N` cohort rule.
- `CATMULT_<attacker>_<defender>`: the nine category multipliers; `om_tactical_category_multiplier` and the damage path read them. Brief G1 test: a changed multiplier changes damage by exactly that factor.
- `EMIT_SIGHT_MULT`, `EMIT_SEEN_MULT`: brief G6, result capped at 1.0. Default 1.0 means no effect until set.
- `PING_*`: brief G7.
- `VISION_UP_n` and `VISION_DOWN_n`: the cross-layer vision factor (a fraction of sensor radius) when the other unit is n layers above, or below, the observer. These replace the brief's `OM_TP_CONE_LAYER_1` and `OM_TP_CONE_LAYER_2`: the plan's Phase C asks for "the vision factor per signed offset", and offsets 1 and 2 carry the same two numbers in both directions today. Ruled, A133 Q-C2.
- `RANGE_*`, `DAMAGE_*`, `AREA_*`: multipliers on attack range, damage and area-attack damage at a signed layer offset (positive up: the target is n layers above the attacker, or above the area's centre layer). Offset 0 is always 1.0 and has no parameter. Which offsets a unit may fire at at all is its type's reach (`om_roster_set_reach`), not these.

## 4. `om_tac_param`: every member, in order

The `#` column is the enum value. Kind: `bool` accepts exactly 0 or 1; `int` accepts whole numbers in range; `real` any finite value in range. No source gives a valid range for any member (the brief says only that each has "a documented valid range"), so every range is proposed by writer; the last column says why. **The ranges are refusal bounds for the lab's setting call only (A133 Q-C9). They are not game values, thresholds or tolerances: every value the game ships and every pass mark stays Westley's, and a search that wants a value outside a bound stops and asks.** Defaults come from the cited source. This table is parsed by `tests/csim/test_PP_settings.py` and `tests/specfactory/test_pp_contract.py`; keep its shape when editing.

| # | member | kind | default | lo | hi | default source | range basis |
|---|---|---|---|---|---|---|---|
| 0 | `OM_TP_PURSUE_BY_STEERING` | bool | 1 | 0 | 1 | plan Phase A Settings; brief G8 | writer: switch: exactly 0 or 1 |
| 1 | `OM_TP_ROUTE_AROUND_TERRAIN` | bool | 1 | 0 | 1 | plan Phase A Settings; brief G2 and section 5 preamble | writer: switch: exactly 0 or 1 |
| 2 | `OM_TP_LEASH_BEFORE_DAMAGE` | bool | 0 | 0 | 1 | plan appendix (default 0, today's order); rulings-2 A125 | writer: switch: exactly 0 or 1 |
| 3 | `OM_TP_TARGET_POLICY` | int | 0 | 0 | 1 | plan appendix (0 nearest, the game's rule; 1 most damaged, lab only); rulings-2 A125 | writer: only the two named policies |
| 4 | `OM_TP_TARGET_BY_SIGHT` | bool | 1 | 0 | 1 | plan Phase C switches; brief section 5 preamble | writer: switch: exactly 0 or 1 |
| 5 | `OM_TP_ROUTE_ACROSS_LAYERS` | bool | 1 | 0 | 1 | plan Phase C switches; brief G4 and section 6 | writer: switch: exactly 0 or 1 |
| 6 | `OM_TP_ATTACK_MOVE_LEASH` | real | 200.0 | 0 | 28000 | om_constants.h OM_ATTACK_MOVE_LEASH_DIST | writer: 0 is brief G1's own test case; top is OM_CANVAS_SIZE_RANGES_LARGE_HI |
| 7 | `OM_TP_RETURN_FIRE_FLEE_DIST` | real | 200.0 | 0 | 28000 | om_constants.h OM_RETURN_FIRE_FLEE_DIST | writer: as ATTACK_MOVE_LEASH |
| 8 | `OM_TP_UNIT_COLLISION_RADIUS` | real | 15.0 | 0 | 200 | om_constants.h OM_UNIT_COLLISION_RADIUS | writer: top is half OM_GRID_CELL_SIZE (400), so a collision pair stays inside one broad-phase cell |
| 9 | `OM_TP_VANTAGE_MULT` | real | 2.0 | 0 | 10 | om_constants.h OM_VANTAGE_CONE_MULTIPLIER | writer: non-negative, top 10 |
| 10 | `OM_TP_AOE_DAMAGE_CAP` | real | 4.0 | 0 | 100 | om_constants.h OM_AOE_DAMAGE_CAP_MULTIPLIER (cap = base damage x this) | writer: non-negative, top 100 |
| 11 | `OM_TP_TARGETING_COHORTS` | int | 4 | 1 | 20 | om_constants.h OM_TARGETING_COHORT_COUNT | writer: at least 1; top is OM_TACTICAL_TICK_RATE (every unit retargets at least once a second) |
| 12 | `OM_TP_CATMULT_LINE_LINE` | real | 1.0 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_LINE_LINE (attacker_defender) | writer: non-negative, top 10 |
| 13 | `OM_TP_CATMULT_LINE_SIEGE` | real | 0.75 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_LINE_SIEGE (attacker_defender) | writer: non-negative, top 10 |
| 14 | `OM_TP_CATMULT_LINE_STRIKE` | real | 1.5 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_LINE_STRIKE (attacker_defender) | writer: non-negative, top 10 |
| 15 | `OM_TP_CATMULT_SIEGE_LINE` | real | 1.5 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_SIEGE_LINE (attacker_defender) | writer: non-negative, top 10 |
| 16 | `OM_TP_CATMULT_SIEGE_SIEGE` | real | 1.0 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_SIEGE_SIEGE (attacker_defender) | writer: non-negative, top 10 |
| 17 | `OM_TP_CATMULT_SIEGE_STRIKE` | real | 0.2 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_SIEGE_STRIKE (attacker_defender) | writer: non-negative, top 10 |
| 18 | `OM_TP_CATMULT_STRIKE_LINE` | real | 0.75 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_STRIKE_LINE (attacker_defender) | writer: non-negative, top 10 |
| 19 | `OM_TP_CATMULT_STRIKE_SIEGE` | real | 1.5 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_STRIKE_SIEGE (attacker_defender) | writer: non-negative, top 10 |
| 20 | `OM_TP_CATMULT_STRIKE_STRIKE` | real | 1.0 | 0 | 10 | om_constants.h OM_CATEGORY_MULTIPLIER_STRIKE_STRIKE (attacker_defender) | writer: non-negative, top 10 |
| 21 | `OM_TP_EMIT_SIGHT_MULT` | real | 1.0 | 0 | 10 | brief section 6 (engine default 1.0; lab 2.0); G6 | writer: non-negative, top 10 |
| 22 | `OM_TP_EMIT_SEEN_MULT` | real | 1.0 | 0 | 10 | brief section 6 (engine default 1.0; lab 2.0); G6 | writer: non-negative, top 10 |
| 23 | `OM_TP_PING_RADIUS` | real | 500.0 | 0 | 28000 | brief section 6; om_constants.h OM_PULSE_RADIUS | writer: top is OM_CANVAS_SIZE_RANGES_LARGE_HI |
| 24 | `OM_TP_PING_REVEAL_TICKS` | int | 100 | 0 | 1200 | brief section 6; om_constants.h OM_PULSE_REVEAL_TICKS | writer: whole ticks, top 1200 (60 s) |
| 25 | `OM_TP_PING_COOLDOWN_TICKS` | int | 400 | 0 | 12000 | brief section 6; om_constants.h OM_PULSE_COOLDOWN_TICKS | writer: whole ticks, top 12000 (10 min) |
| 26 | `OM_TP_PING_REACH` | real | 2000.0 | 0 | 28000 | brief section 6 (2,000, design chat proposal) | writer: top is OM_CANVAS_SIZE_RANGES_LARGE_HI |
| 27 | `OM_TP_VISION_UP_1` | real | 0.5 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 28 | `OM_TP_VISION_UP_2` | real | 0.2 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 29 | `OM_TP_VISION_UP_3` | real | 0.0 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 30 | `OM_TP_VISION_UP_4` | real | 0.0 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 31 | `OM_TP_VISION_DOWN_1` | real | 0.5 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 32 | `OM_TP_VISION_DOWN_2` | real | 0.2 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 33 | `OM_TP_VISION_DOWN_3` | real | 0.0 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 34 | `OM_TP_VISION_DOWN_4` | real | 0.0 | 0 | 1 | offsets 1 and 2: om_constants.h OM_CONE_LAYER_1_FACTOR and _2_FACTOR; offsets 3 and 4: fog.c om_unit_get_cross_layer_factor returns 0.0, E-01 R-005-05 | writer: a fraction of sensor radius; fog.c caps cross-layer factors at 1.0 |
| 35 | `OM_TP_RANGE_UP_1` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 36 | `OM_TP_RANGE_UP_2` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 37 | `OM_TP_RANGE_UP_3` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 38 | `OM_TP_RANGE_UP_4` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 39 | `OM_TP_RANGE_DOWN_1` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 40 | `OM_TP_RANGE_DOWN_2` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 41 | `OM_TP_RANGE_DOWN_3` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 42 | `OM_TP_RANGE_DOWN_4` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 43 | `OM_TP_DAMAGE_UP_1` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 44 | `OM_TP_DAMAGE_UP_2` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 45 | `OM_TP_DAMAGE_UP_3` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 46 | `OM_TP_DAMAGE_UP_4` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 47 | `OM_TP_DAMAGE_DOWN_1` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 48 | `OM_TP_DAMAGE_DOWN_2` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 49 | `OM_TP_DAMAGE_DOWN_3` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 50 | `OM_TP_DAMAGE_DOWN_4` | real | 1.0 | 0 | 10 | brief G5 and section 6 (1.0) | writer: non-negative, top 10 |
| 51 | `OM_TP_AREA_UP_1` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 52 | `OM_TP_AREA_UP_2` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 53 | `OM_TP_AREA_UP_3` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 54 | `OM_TP_AREA_UP_4` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 55 | `OM_TP_AREA_DOWN_1` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 56 | `OM_TP_AREA_DOWN_2` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 57 | `OM_TP_AREA_DOWN_3` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 58 | `OM_TP_AREA_DOWN_4` | real | 1.0 | 0 | 10 | plan Phase C (area multipliers by signed offset); no number given, 1.0 by analogy with RANGE and DAMAGE (writer) | writer: non-negative, top 10 |
| 59 | `OM_TP_TARGET_POLICY_FACTION_1` | int | -1 | -1 | 1 | A196: faction 1's target policy; -1 = unset, faction 1 follows `OM_TP_TARGET_POLICY` (faction 0's, range 0 to 1); 0 nearest, 1 most damaged | lab only; whole numbers -1 to 1 |
| 60 | `OM_TP_PING_ALERT` | bool | 0 | 0 | 1 | R-162-03 (Westley 2026-10-05): 0 the pinged side is told nothing, 1 it gets the 60-degree alert | switch: exactly 0 or 1 |
| 61 | `OM_TP_TERRAIN_STEEP_DEG` | real | 35 | 0 | 90 | R-200-03, Q-189-02 (30 to 35; the approved mockups used 35); terrain stage 1 spec 2026-10-05 | writer: degrees, 0 to 90 |
| 62 | `OM_TP_SLOPE_UP_DIV` | real | 1.1 | 1 | 10 | R-004-07 (Westley 2026-10-06): speed on a slope is divided by this going up; provisional (2026-10-06); terrain stage 2 spec | writer: 1 to 10 |
| 63 | `OM_TP_SLOPE_DOWN_MULT` | real | 1.1 | 1 | 10 | R-004-07 (Westley 2026-10-06): speed on a slope is multiplied by this going down; provisional (2026-10-06) | writer: 1 to 10 |
| 64 | `OM_TP_SIGHT_EYE_HEIGHT` | real | 50 | 0 | 1000 | R-005-10: eye height in wu above the ground at both ends of a sight line; lab draft, provisional (2026-10-06) | writer: wu, 0 to 1000 |
| 65 | `OM_TP_GROUND_FLYER_SEEN_MULT` | real | 1.5 | 1 | 10 | R-005-11: a ground-era flyer is seen from max(observer, flyer sensor radius) times this, so from farther than it sees; lab draft, provisional (2026-10-06) | writer: 1 to 10 |
| 66 | `OM_TP__COUNT` | - | - | - | - | sentinel, not a parameter | - |

Order: the six switches first (Phase A needs the first four, Phase C the last two), then the brief G1 numbers, then the section 6 numbers, then the four families by signed offset (up 1 to 4, then down 1 to 4, each family in the order VISION, RANGE, DAMAGE, AREA). A later member is only ever appended before `OM_TP__COUNT`, never inserted.

## 5. Map calls

**`int om_map_set_canvas(om_world *w, double width, double height)`** (`tactical_mapgen.c`). The map size movement clamps positions to; called by mission setup. Returns 0 and stores the size when `w` is non-NULL and both values are finite, greater than 0 and at most `OM_MAP_MAX_CANVAS` (28,000); returns -1 and changes nothing otherwise (NaN, infinity, zero, negative, a width or height above 28,000; A133 Q-C3, since the fixed tables are sized for that and nothing may corrupt). Before any call there is no canvas: no clamp and no route grid, which is today's behaviour. A later call replaces the canvas (blocked rectangles from `om_map_block_rect` are cleared when the size changes). `om_map_clear` also unsets the canvas. Replace, clear and the rest of the canvas rules are accepted as written (A133 Q-C3).

**`int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi)`** (`tactical_mapgen.c`, brief G2). Blocks every route-grid cell (100 wu per layer) the rectangle overlaps with positive area, on layers `layer_lo` to `layer_hi` inclusive. Corners may be given in either order. Returns 0 on success; -1 with nothing changed when no canvas is set, when `layer_lo > layer_hi`, when the rectangle has zero width or height, or when `layer_hi` is at or above `OM_LAYER_COUNT` (`layer_lo` is then also covered by `layer_lo <= layer_hi`; A132). "Overlaps with positive area" is proposed by writer. The cell is the unit of blocking: a rectangle that touches a cell blocks the whole cell.

**`om_map_add_cover` already exists; no second call is added (A132).** `uint32_t om_map_add_cover(om_world *w, double x, double y, double radius, double height)` (header line 1658, defined `csrc/tactical_mapgen.c`, row in `signatures.toml`). It stays one symbol with `double height`; the plan appendix's separate `uint32_t height_layers` adder was an error, corrected by A132, and does not exist. The height is a whole count of layers from the bottom: height h blocks engine layers 0 to h - 1 (R-007-01, R-007-02). Height 1.0 with both units on engine layer 0 blocks, which is what `test_E11_S084_flat_damage.py` expects; 5.0 (`mission.c`, `OM_MISSION_OBJECTIVE_COVER_HEIGHT`, and tests) blocks all five.
- Accepted: `height` is one of 0.0, 1.0, 2.0, 3.0, 4.0, 5.0 (`OM_LAYER_COUNT` is the top). Returns the 1-based index of the new row, as today. 0.0 adds an obstacle that blocks nothing.
- Refused (returns 0, nothing added, `om_map_cover_count` unchanged): a fractional height, a negative height, NaN or infinity, and a height above `OM_LAYER_COUNT`. A return of 0 is also what a full table gives (today's behaviour).
- `om_map_cover_at` hands the stored `height` back unchanged.

## 6. Layer, reach, emission and ping calls (Phase C)

Returns follow the existing `om_command_*` convention: 0 ok, nonzero otherwise. Reason numbers marked proposed are the writer's.

- **`om_command_set_layer`** (`tactical_move.c`, G4): orders each listed live unit to `layer`. Per R-002-02 to R-002-07: a transfer to a blocked layer stays pending; a second transfer replaces the first; a move order never clears one; a transfer to the unit's own layer is accepted and completes at once; each unit resolves independently. Returns -1, changing nothing, when `layer` is at or above `OM_LAYER_COUNT` (R-002-06, A132) or when `n_units > 0` and `unit_ids` is NULL; otherwise 0. Unknown or dead ids are skipped, as `om_command_attack_move` skips them (proposed by writer).
- **`om_unit_transition_progress`** (`tactical_move.c`, G4): 0.0 when settled, else in (0, 1); 0.0 for an unknown unit.
- **`om_unit_get_target_layer`** (`tactical_move.c`, G4): the layer the unit is moving to, or its own; for an unknown unit `UINT32_MAX` (proposed by writer; `om_unit_get_layer` returns -1 there).
- **`om_roster_set_reach`** (`tactical_move.c`, G5): sets how many layers above and below its own a unit type may acquire and fire at (R-164-02). 0 ok; -1 for an unknown type. The built-in roster defaults to 0 up, 0 down.
- **`om_unit_profile_reach`** (`tactical_move.c`, G5): writes the type's reach to `*up` and `*down` (either may be NULL). 0 ok; -1 for an unknown type. Declared `const om_world *` here, the brief's sketch has a non-const world for a read-only call.
- **`om_command_set_emission`** (`fog.c`, G6): `OM_EMIT_SILENT` (0, default, today's behaviour) or `OM_EMIT_ACTIVE` (1). 0 ok; -1 for any other mode, nothing changed. Unknown ids skipped. Takes effect on the next tick, costs nothing.
- **`om_unit_get_emission`** (`fog.c`, G6): the unit's mode; 0 for an unknown unit.
- **`om_command_ping`** (`fog.c`, G7): 0 ok and the ping is cast. A refused ping changes nothing and returns a reason: 1 caster unknown or dead, 2 point beyond `PING_REACH`, 3 caster on cooldown, 4 layer at or above `OM_LAYER_COUNT`, 5 the world's era kind is ground (`om_era_kind` 1; terrain stage 2, R-005-09: checked after the caster check and before the reach check, so an unknown or dead caster still returns 1) (reason numbers proposed by writer; the brief names the four reasons only).
- **`om_ping_alert_count`** (`fog.c`, G7): alerts held for `faction`; 0 for an unknown faction.
- **`om_ping_alert_get`** (`fog.c`, G7): copies alert `index` (0 oldest) into `*out`; 0 ok, -1 when `index` is out of range or `out` is NULL. `om_ping_alert`: `{ uint64_t tick; int32_t faction; int32_t sector; }`, sector 0 to 5 counter-clockwise from +x.

The behaviour that turns these on in play is built by PP-unit and PP-fog under the brief; this document fixes only the signatures and the refusals.

**Three read-only getters (A133; rows 15 to 17).** They let the tests and the lab read the movement state the attack-move group rule needs (R-096-02, R-096-03). All are defined in `csrc/tactical_move.c` (`module = "tactical_move.c"`), never `unit.c`, and change no state. In this wave each body is the generated stub (returns 0, writes nothing); A3 fills them, so no behaviour test is written yet, only the unknown-unit return and a call on a live unit.
- `uint32_t om_unit_get_group_id(const om_world *w, uint32_t unit)`: the id of the move group the unit belongs to (`om_move_unit.group_id`); 0 when the unit is in no group and for an unknown unit or a NULL world. Group ids start at 1.
- `int om_unit_get_leash_anchor(const om_world *w, uint32_t unit, double *x, double *y)`: when the unit holds a leash anchor (its position at target acquisition under an attack-move, R-087-05, R-096-03), writes it to `*x` and `*y` (either may be NULL) and returns 1. Returns 0 and writes nothing when the unit has no anchor, for an unknown unit, and for a NULL world. The anchor lives in `unit.c`'s unit row today (`anchor_set`, `anchor_x`, `anchor_y`); how A3 makes it visible from `tactical_move.c` is A3's to decide and is flagged here as a file-ownership point for the piece owning `unit.c`.
- `int om_unit_get_engaged(const om_world *w, uint32_t unit)`: 1 when the unit's engaged flag is set, else 0; 0 for an unknown unit or a NULL world. "Engaged" is the movement state's flag (`om_move_unit.engaged`): set when the unit engages a target (`om_unit_engage`, called when it starts attacking, `unit.c`), cleared by any new order (move, attack-move, group move, kite, `om_unit_clear_orders`). It is the flag the attack-move group-end rule reads: a group of two or more ends when every member has engaged and its members do not resume the march (R-096-02); a unit attack-moved alone is not a group and resumes.

**The guard call (A170; row 18).** `int om_command_guard(om_world *w, const uint32_t *unit_ids, uint32_t n_units)`, defined in `csrc/tactical_move.c` (`module = "tactical_move.c"`, like the other new calls), parameter names `w`, `unit_ids`, `n_units` (the style of `om_command_move`). Westley, in the record: "Yes a guard stance is fine". Rule R-096-05 (E-13 S-096; the builder writes it into E-13 with the landing): a unit ordered to guard holds its position, fires at any target it can shoot in range, never pursues, and resumes nothing; a move, attack-move or layer order ends the guard. Q-096-01 is closed provisionally (A170).
- Order semantics. The call is an order like `om_command_move`: each listed live unit drops its pending orders and destination (a pending move or attack-move is cancelled, nothing is resumed when a target dies or leaves), clears its group membership, and holds. It never moves the unit. Return fire (R-087-06) turns and targets an attacker in range but never gives a guarding unit a destination. `om_command_move`, `om_command_attack_move`, `om_command_group_move`, `om_command_set_layer` and `om_command_attack_target` end the guard; a new `om_command_guard` on a guarding unit is a no-op.
- Returns, the convention of `om_command_set_layer`. 0 ok. -1, changing nothing, when `w` is NULL or when `n_units > 0` and `unit_ids` is NULL. Unknown or dead ids are skipped, as `om_command_attack_move` skips them: the call still returns 0 and no unit anywhere is changed on their account. `n_units == 0` returns 0.
- No getter is added in this wave; the guard shows in play through position, destination and fire. Not decided here and left to the builder with a flag: a guard order on a unit with a pending layer transfer, and whether the pipe gets a guard command (a pipe frame is a separate contract piece).
- Hash baseline: with no guard order ever given, behaviour is exactly today's.

## 7. Rulings

Addendum 46 of `docs/northstar/plans/2026-10-01-architect-rulings-2.md`. The open questions of the first draft (Q-C1 to Q-C9) are answered; their text lives in git history.

- **A131**: the unit-file wave (A3) starts on `unit.c` once the damage-reduction-lists commit is on main; until then `PP-unit` is not released. A3 fills the three getters.
- **A132**: layers are 0 to 4 in the engine (bible layer n is engine layer n - 1); the header carries `OM_LAYER_COUNT` (5); `om_map_add_cover` stays one symbol with `double height`, a whole count of layers from the bottom (section 5).
- **A133**: Q-C1 stubs land with the contract in one merge; Q-C2 vision per signed offset; Q-C3 canvas rules, above `OM_MAP_MAX_CANVAS` refused; Q-C4 settings survive `om_tactical_reset`, not saved, not hashed, a new world at defaults; Q-C5 most damaged is the lowest hp fraction, then nearest, then lowest id; Q-C6 the collision-radius setting reaches the collision pass only; Q-C9 the 59 ranges are refusal bounds for the lab call, not game values; three read-only getters join ABI 4 (rows 15 to 17). `tests/csim/test_E02_S020_abi.py` asserting ABI 3 is a test defect with a ledger row.
- **A134**: tables sized for `OM_MAX_UNITS` and the 28,000 canvas; every fixed table refuses when full and returns an error, with a test that fills it.
- **A135**: tests red until a later wave sit on one strict expected-failure list owned by `PP-parity`; nothing else goes on it. In this document's tests, the Phase C refusals (`om_command_set_layer`, `om_command_ping`) are the kind that list takes until PP-unit and PP-fog land.
- **A170**: the guard call, row 18 (section 6, above); R-096-05 written into E-13 by the landing.
- **A196**: one setting joins the enum, appended last before `OM_TP__COUNT` (row 59): `OM_TP_TARGET_POLICY_FACTION_1`, int, default -1 (unset: faction 1 follows `OM_TP_TARGET_POLICY`), range -1 to 1, lab only. `OM_TP_TARGET_POLICY` keeps range 0 to 1 and means faction 0. `OM_TP__COUNT` becomes 60.
- **R-162-03**: one setting joins the enum, appended last before `OM_TP__COUNT` (row 60, no existing number moves): `OM_TP_PING_ALERT`, bool, default 0. `OM_TP__COUNT` becomes 61. R-162-01 also moves the `OM_TP_PING_REVEAL_TICKS` default from 40 to 100 (5 s); its range is unchanged.
- **TERRAIN-1**: one setting joins the enum, appended last before `OM_TP__COUNT` (row 61, no existing number moves): `OM_TP_TERRAIN_STEEP_DEG`, real, default 35, range 0 to 90. `OM_TP__COUNT` becomes 62. `OM_TP_PING_ALERT` landed first and holds 60, so this one is 61.
- **TERRAIN-2**: four settings join the enum, appended last before `OM_TP__COUNT` (rows 62 to 65, no existing number moves): `OM_TP_SLOPE_UP_DIV`, `OM_TP_SLOPE_DOWN_MULT`, `OM_TP_SIGHT_EYE_HEIGHT`, `OM_TP_GROUND_FLYER_SEEN_MULT`, all real, defaults 1.1, 1.1, 50, 1.5. `OM_TP__COUNT` becomes 66. Defaults are Westley's 2026-10-06 rulings (slope) and lab drafts (sight), provisional (2026-10-06); the ranges are the writer's refusal bounds. The ping refusal reason 5 is added to section 6.
- **A136**: the parity tolerances (1e-6 wu, 2e-3 rad) are provisional and Westley's; they are not part of this contract.

## 8. Tests that prove this piece

- `tests/specfactory/test_pp_contract.py`: ABI 4 in header, conftest and the table; `om_abi_version()` agrees; the 17 rows (rows 5 to 9 and the three getters in `tactical_move.c`), the struct row, the enums and the bindings exist with the signatures above; `OM_LAYER_COUNT` is 5 and `OM_MAP_MAX_CANVAS` is 28,000, each defined once; `sig_table --check` is clean; the header enum matches section 4 in names and order; `om_map_add_cover` stays one symbol with `double height`.
- `tests/csim/test_PP_settings.py`: defaults, in-range set and read back, refusals that change nothing, set before spawn and mid-fight, settings survive reset and are not hashed, a new world starts at defaults, canvas return values including the 28,000 limit, cover heights 0, 1 to 5 accepted and fractional, negative, non-finite and above 5 refused, layer range of the layer-taking calls, the three getters' unknown-unit returns. Each refusal check has an in-range positive control.
- `tests/csim/test_E02_S020_abi.py:21-22` asserts ABI 3: a test-defect candidate, not touched here.
- `tests/specfactory/test_pp_contract_guard.py`: the `om_command_guard` row (module `tactical_move.c`, signature above), its header declaration in the `tactical_move.c` block, its conftest binding after `sig_table --emit`, the stub or body in `tactical_move.c`, and this document naming it (A170).
- `tests/csim/test_PP_unit_guard.py`: R-096-05 behaviour: hold, fire in range, no pursuit, return fire does not move it, move, attack-move and layer orders end it, a pending move is cancelled, nothing resumes, a group, the refusals, and the choke scenario in miniature.
