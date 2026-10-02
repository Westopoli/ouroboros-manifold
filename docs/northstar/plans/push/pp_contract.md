# PP-contract: the contract document for ABI 4

Written before implementation, 2026-10-02, for piece `PP-contract` (owns `csrc/ouroboros_sim.h`, `docs/northstar/spec_factory/signatures.toml`, `tests/csim/conftest.py`). Source of truth: `docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md` (the plan; its appendix is the contract), `docs/northstar/plans/2026-10-02-skill-lab-cascade.md` (the brief) sections 5 and 6, `docs/northstar/plans/2026-10-01-architect-rulings-2.md` Addendum 45. Where a number or a rule is the writer's and not a source's, the text says "proposed by writer" and the Architect rules on it (section 7).

## 1. What lands

One ABI bump, 3 to 4, covering every call in the plan appendix (Phases A and C). No pipe frame changes shape. The pipe hello carries `om_abi_version()`, so its value reads 4 instead of 3; no frame field is added or reshaped.

New header content: two enums (`om_tac_param`, `om_emission`), one struct (`om_ping_alert`), 14 functions. No existing signature changes.

Calls marked (brief) are specified in the brief section 5; this document adds the signature in `signatures.toml` form, the error returns the brief leaves open, and the defining file.

| # | Call | Phase | Defined in | Brief |
|---|---|---|---|---|
| 1 | `double om_tactical_get_param(const om_world *w, om_tac_param p)` | A | `csrc/tactical_move.c` | G1 |
| 2 | `int om_tactical_set_param(om_world *w, om_tac_param p, double value)` | A | `csrc/tactical_move.c` | G1 |
| 3 | `int om_map_set_canvas(om_world *w, double width, double height)` | A | `csrc/tactical_mapgen.c` | plan appendix |
| 4 | `int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi)` | A | `csrc/tactical_mapgen.c` | G2 |
| 5 | `int om_command_set_layer(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t layer)` | C | `csrc/unit.c` | G4 |
| 6 | `double om_unit_transition_progress(const om_world *w, uint32_t unit)` | C | `csrc/unit.c` | G4 |
| 7 | `uint32_t om_unit_get_target_layer(const om_world *w, uint32_t unit)` | C | `csrc/unit.c` | G4 |
| 8 | `int om_roster_set_reach(om_world *w, int unit_type, uint32_t layers_up, uint32_t layers_down)` | C | `csrc/unit.c` | G5 |
| 9 | `int om_unit_profile_reach(const om_world *w, int unit_type, uint32_t *up, uint32_t *down)` | C | `csrc/unit.c` | G5 |
| 10 | `int om_command_set_emission(om_world *w, const uint32_t *unit_ids, uint32_t n_units, om_emission mode)` | C | `csrc/fog.c` | G6 |
| 11 | `int om_unit_get_emission(const om_world *w, uint32_t unit)` | C | `csrc/fog.c` | G6 |
| 12 | `int om_command_ping(om_world *w, uint32_t caster, uint32_t layer, double x, double y)` | C | `csrc/fog.c` | G7 |
| 13 | `uint32_t om_ping_alert_count(const om_world *w, int32_t faction)` | C | `csrc/fog.c` | G7 |
| 14 | `int om_ping_alert_get(const om_world *w, int32_t faction, uint32_t index, om_ping_alert *out)` | C | `csrc/fog.c` | G7 |

The plan appendix's `om_map_add_cover(..., uint32_t height_layers)` is not a call in this table (section 5).

Defining files for rows 5 to 14 follow `pieces.toml` (PP-unit owns the layer steps and roster of Phase C; PP-fog owns "side sight, emission and the ping"); the brief names no file for them. Rows 1 to 4 are as the task assigned them.

## 2. How it lands (mechanics the builder needs)

1. `csrc/ouroboros_sim.h`: `OM_ABI_VERSION` 4, and the comment above `om_abi_version()` gains a "Bumped to 4" sentence. The two enums are written by hand beside the other enums, as **anonymous-tag typedefs** (`typedef enum { ... } om_tac_param;`), because `sig_table.py`'s enum recogniser (`Types.enums`) matches only `typedef enum {`; a tagged `typedef enum om_tac_param {` as in the brief's sketch would leave rows that take it blocked. The 14 declarations come from `sig_table --emit` into the generated blocks of their module.
2. `docs/northstar/spec_factory/signatures.toml`: 14 `[[symbols]]` rows and one `[[structs]]` row (`OMPingAlert`, fields `tick uint64_t`, `faction int32_t`, `sector int32_t`; C name `om_ping_alert`, 16 bytes). `[meta] abi_version` becomes 4 (it reads 2 today while the header reads 3; stale before this piece). Parameter names are those in the table above. `epics`: rows 1, 2 `E-11`; rows 3, 4 `E-13`; rows 5 to 14 `E-01`.
3. `tests/csim/conftest.py`: `EXPECTED_ABI_VERSION = 4`; hand-written enum mirrors `OMTacParam` (members named as the header's minus the `OM_TP_` prefix, `COUNT` included) and `OMEmission` (`SILENT = 0`, `ACTIVE = 1`); the bindings and the `OMPingAlert` mirror come from `sig_table --emit`.
4. `sig_table --emit` also appends a `/* STUB */` body for every new symbol to its module's `.c`, before the file's trailing `/* ---- end generated stubs ---- */`. That edits `tactical_move.c`, `tactical_mapgen.c`, `unit.c` and `fog.c`, which other pieces own. The stubs are mechanical and contain no logic; they are needed so the library links and the new tests fail on behaviour, not on a missing symbol. Needs an Architect ruling on ownership (section 7, Q-C1).
5. Expected red after the contract lands: the new `tests/csim/test_PP_settings.py` goes red on the stubs (a stub `om_tactical_set_param` returns 0 for everything and `get` returns 0.0). It turns green when PP-move lands the two param calls and PP-mapgen the canvas call.

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
- Settings are configuration, not simulation state: they are not part of `om_world_get_state_checksum` and not written by the save calls (proposed by writer, Q-C4).
- Other files read a setting through the public `om_tactical_get_param`; no internal header change is part of this piece. Storage lives with the world's tactical state and must outlive `om_tactical_reset` if reset is ruled to keep settings (Q-C4): `om_tactical_reset` frees `w->move_state`, so a table kept there would be wiped.

What the parameters mean:
- `PURSUE_BY_STEERING` 1: pursuit sets the unit's move goal to the nearest visible enemy and walks it through the ordinary movement step (brief G8, plan P1). 0: today's straight-line `om_tac_step_toward` pursuit.
- `ROUTE_AROUND_TERRAIN` 1: movement routes on the 100 wu per-layer grid, blocked cells block sight and fire on their layers (plan P3). 0: today's behaviour (layer 0 sampled, no route grid).
- `LEASH_BEFORE_DAMAGE` 0: today's order. 1: the Python's order, the leash runs before damage, so an attack-moving unit never shoots a target more than `ATTACK_MOVE_LEASH` from its anchor (parity requirements item 7, audit G03; plan decisions table; A125). The side Westley does not pick is deleted later, with this parameter.
- `TARGET_POLICY` 0: nearest hostile, the game's rule. 1: most damaged, lab only. "Most damaged" is the lowest hp fraction; ties go to the nearest, then the lowest unit id (tie order proposed by writer, for determinism, Q-C5).
- `TARGET_BY_SIGHT` 1: a unit acquires, keeps and fires only at targets in its side's visible set (brief G3, A125). 0: today's behaviour.
- `ROUTE_ACROSS_LAYERS` 1: the router works over cells and layers together, by travel time (brief G4). 0: the router stays on the unit's layer.
- `ATTACK_MOVE_LEASH`: distance from its anchor beyond which an attack-moving unit drops a target (today `OM_ATTACK_MOVE_LEASH_DIST`).
- `RETURN_FIRE_FLEE_DIST`: the flinch distance (today `OM_RETURN_FIRE_FLEE_DIST`).
- `UNIT_COLLISION_RADIUS`: read by the collision pass in `tactical_move.c`. Mission spawn spacing in `mission.c` and `enemy_macro.c` keeps the compile-time constant (Q-C6).
- `VANTAGE_MULT`: the vantage multiplier on a cross-layer vision factor, the product capped at 1.0 (today `OM_VANTAGE_CONE_MULTIPLIER`). The vantage rules that read the offset 1 and 2 factors are unchanged.
- `AOE_DAMAGE_CAP`: area damage total cap as a multiple of base damage.
- `TARGETING_COHORTS`: `unit_id % N == tick % N` cohort rule.
- `CATMULT_<attacker>_<defender>`: the nine category multipliers; `om_tactical_category_multiplier` and the damage path read them. Brief G1 test: a changed multiplier changes damage by exactly that factor.
- `EMIT_SIGHT_MULT`, `EMIT_SEEN_MULT`: brief G6, result capped at 1.0. Default 1.0 means no effect until set.
- `PING_*`: brief G7.
- `VISION_UP_n` and `VISION_DOWN_n`: the cross-layer vision factor (a fraction of sensor radius) when the other unit is n layers above, or below, the observer. These replace the brief's `OM_TP_CONE_LAYER_1` and `OM_TP_CONE_LAYER_2`: the plan's Phase C asks for "the vision factor per signed offset", and offsets 1 and 2 carry the same two numbers in both directions today. Proposed by writer, Q-C2.
- `RANGE_*`, `DAMAGE_*`, `AREA_*`: multipliers on attack range, damage and area-attack damage at a signed layer offset (positive up: the target is n layers above the attacker, or above the area's centre layer). Offset 0 is always 1.0 and has no parameter. Which offsets a unit may fire at at all is its type's reach (`om_roster_set_reach`), not these.

## 4. `om_tac_param`: every member, in order

The `#` column is the enum value. Kind: `bool` accepts exactly 0 or 1; `int` accepts whole numbers in range; `real` any finite value in range. No source gives a valid range for any member (the brief says only that each has "a documented valid range"), so every range is proposed by writer; the last column says why. Defaults come from the cited source. This table is parsed by `tests/csim/test_PP_settings.py` and `tests/specfactory/test_pp_contract.py`; keep its shape when editing.

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
| 24 | `OM_TP_PING_REVEAL_TICKS` | int | 40 | 0 | 1200 | brief section 6; om_constants.h OM_PULSE_REVEAL_TICKS | writer: whole ticks, top 1200 (60 s) |
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
| 59 | `OM_TP__COUNT` | - | - | - | - | sentinel, not a parameter | - |

Order: the six switches first (Phase A needs the first four, Phase C the last two), then the brief G1 numbers, then the section 6 numbers, then the four families by signed offset (up 1 to 4, then down 1 to 4, each family in the order VISION, RANGE, DAMAGE, AREA). A later member is only ever appended before `OM_TP__COUNT`, never inserted.

## 5. Map calls

**`int om_map_set_canvas(om_world *w, double width, double height)`** (`tactical_mapgen.c`). The map size movement clamps positions to; called by mission setup. Returns 0 and stores the size when `w` is non-NULL and both values are finite and greater than 0; returns -1 and changes nothing otherwise (NaN, infinity, zero, negative). Before any call there is no canvas: no clamp and no route grid, which is today's behaviour. A later call replaces the canvas (blocked rectangles from `om_map_block_rect` are cleared when the size changes, proposed by writer, Q-C3). `om_map_clear` also unsets the canvas (proposed by writer, Q-C3). No upper size is enforced here; the fixed tables must cover the largest canvas, `OM_CANVAS_SIZE_RANGES_LARGE_HI` 28,000, plan P5 (Q-C3).

**`int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi)`** (`tactical_mapgen.c`, brief G2). Blocks every route-grid cell (100 wu per layer) the rectangle overlaps with positive area, on layers `layer_lo` to `layer_hi` inclusive. Corners may be given in either order. Returns 0 on success; -1 with nothing changed when no canvas is set, when `layer_lo > layer_hi`, when the rectangle has zero width or height, or when a layer is outside the map's layer range (Q-C7). "Overlaps with positive area" is proposed by writer. The cell is the unit of blocking: a rectangle that touches a cell blocks the whole cell.

**`om_map_add_cover` already exists; no second call is added.** Today: `uint32_t om_map_add_cover(om_world *w, double x, double y, double radius, double height)` (header line 1658, defined `csrc/tactical_mapgen.c:259`, row in `signatures.toml`). Returns the 1-based index of the new cover row, or 0 when the table is full. Callers: `mission.c:2455` (`OM_MISSION_OBJECTIVE_COVER_HEIGHT`, 5.0) and tests passing 5.0 or 1.0. The plan appendix proposes a new `uint32_t height_layers` adder; that would be a second symbol with the same name, which C cannot hold. The contract instead keeps the signature and **reads the existing `height` as a count of layers**: the obstacle blocks sight and fire on layers 1 to `height` (whole number of layers, the fractional part dropped), per E-01 R-007-01 and R-007-02 and the plan's "cover height" decision. 5.0 means all five layers, 1.0 layer 1 only. `om_map_cover_at` already hands `height` back unchanged. See also plan conflict Q-C8 (section 7): the plan's sentence "the existing height-less adder keeps its meaning" is wrong, the existing adder has a height and every caller sets it.

## 6. Layer, reach, emission and ping calls (Phase C)

Returns follow the existing `om_command_*` convention: 0 ok, nonzero otherwise. Reason numbers marked proposed are the writer's.

- **`om_command_set_layer`** (`unit.c`, G4): orders each listed live unit to `layer`. Per R-002-02 to R-002-07: a transfer to a blocked layer stays pending; a second transfer replaces the first; a move order never clears one; a transfer to the unit's own layer is accepted and completes at once; each unit resolves independently. Returns -1, changing nothing, when `layer` is outside the map's layer range (R-002-06, Q-C7) or when `n_units > 0` and `unit_ids` is NULL; otherwise 0. Unknown or dead ids are skipped, as `om_command_attack_move` skips them (proposed by writer).
- **`om_unit_transition_progress`** (`unit.c`, G4): 0.0 when settled, else in (0, 1); 0.0 for an unknown unit.
- **`om_unit_get_target_layer`** (`unit.c`, G4): the layer the unit is moving to, or its own; for an unknown unit `UINT32_MAX` (proposed by writer; `om_unit_get_layer` returns -1 there).
- **`om_roster_set_reach`** (`unit.c`, G5): sets how many layers above and below its own a unit type may acquire and fire at (R-164-02). 0 ok; -1 for an unknown type. The built-in roster defaults to 0 up, 0 down.
- **`om_unit_profile_reach`** (`unit.c`, G5): writes the type's reach to `*up` and `*down` (either may be NULL). 0 ok; -1 for an unknown type. Declared `const om_world *` here, the brief's sketch has a non-const world for a read-only call.
- **`om_command_set_emission`** (`fog.c`, G6): `OM_EMIT_SILENT` (0, default, today's behaviour) or `OM_EMIT_ACTIVE` (1). 0 ok; -1 for any other mode, nothing changed. Unknown ids skipped. Takes effect on the next tick, costs nothing.
- **`om_unit_get_emission`** (`fog.c`, G6): the unit's mode; 0 for an unknown unit.
- **`om_command_ping`** (`fog.c`, G7): 0 ok and the ping is cast. A refused ping changes nothing and returns a reason: 1 caster unknown or dead, 2 point beyond `PING_REACH`, 3 caster on cooldown, 4 layer outside the map's range (reason numbers proposed by writer; the brief names the four reasons only).
- **`om_ping_alert_count`** (`fog.c`, G7): alerts held for `faction`; 0 for an unknown faction.
- **`om_ping_alert_get`** (`fog.c`, G7): copies alert `index` (0 oldest) into `*out`; 0 ok, -1 when `index` is out of range or `out` is NULL. `om_ping_alert`: `{ uint64_t tick; int32_t faction; int32_t sector; }`, sector 0 to 5 counter-clockwise from +x.

The behaviour that turns these on in play is built by PP-unit and PP-fog under the brief; this document fixes only the signatures and the refusals.

## 7. Questions for the Architect

- **Q-C1. Stubs in files other pieces own.** `sig_table --emit` writes a stub into `unit.c`, `fog.c`, `tactical_move.c`, `tactical_mapgen.c`. Does the contract piece get a one-time exemption in the ownership lint, or do the stubs go in as part of each owner's first unit?
- **Q-C2. Vision by signed offset.** Brief G1 lists `OM_TP_CONE_LAYER_1` and `_2`; the plan's Phase C asks for the vision factor per signed offset. This document replaces the two with `VISION_UP_1..4` and `VISION_DOWN_1..4`. Alternative: keep the two and add multipliers (cannot enable three-layer vision). Which?
- **Q-C3. Canvas rules** in section 5 (replace, clear, `om_map_clear`, no upper size).
- **Q-C4. Do settings survive `om_tactical_reset`, and are they saved or hashed?** Proposed: reset keeps them; they are neither saved nor hashed; a new world starts at defaults.
- **Q-C5. "Most damaged"** tie order (section 3).
- **Q-C6. Collision radius** reaches only the collision pass; spawn spacing stays compile-time. `tactical_move.c` sizes grids from `OM_UNIT_COLLISION_RADIUS` at compile time today.
- **Q-C7. The map's layer range** is in no header. The bible numbers layers 1 to 5; the engine compares layers for equality and the tests spawn on layer 0. `om_command_set_layer`, `om_map_block_rect`, `om_command_ping` and the cover height all need the range and the numbering (does layer 1 or layer 0 sit at the bottom). Not guessed here.
- **Q-C8. Plan conflict, cover.** The plan appendix adds `om_map_add_cover(w, x, y, radius, uint32_t height_layers)` and says the existing adder is height-less. It is not: `double height`, callers pass 5.0 and 1.0, `mission.c` passes 5.0. This document keeps the one symbol and reads `height` as a layer count. Consequence for Q-C7: `1.0` in `test_E11_S084_flat_damage.py:135` blocks layer 1 only, while that test spawns on layer 0.
- **Q-C9. All 59 ranges** in section 4 are the writer's.

## 8. Tests that prove this piece

- `tests/specfactory/test_pp_contract.py`: ABI 4 in header, conftest and the table; `om_abi_version()` agrees; the 14 rows, the struct row, the enums and the bindings exist with the signatures above; `sig_table --check` is clean; the header enum matches section 4 in names and order; `om_map_add_cover` stays one symbol with `double height`.
- `tests/csim/test_PP_settings.py`: defaults, in-range set and read back, refusals that change nothing, set before spawn and mid-fight, canvas return values. Each refusal check has an in-range positive control.
- `tests/csim/test_E02_S020_abi.py:21-22` asserts ABI 3: a test-defect candidate, not touched here.
