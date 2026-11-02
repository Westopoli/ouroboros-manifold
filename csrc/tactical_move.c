/* csrc/tactical_move.c -- E-13 movement, pathing, steering, collision, and
 * command dispatch (card B12). Owns w->move_state (F2i slot). Units are
 * unit.c's (om_unit_position_x/y, om_unit_effective_speed, om_unit_alive,
 * om_unit_ability_active -- all public, read-only from here); the navmesh
 * obstacle grid conceptually belongs to tactical_mapgen.c but
 * om_map_set_obstacle_density, the om_navmesh_ family, and the
 * om_steering_ family were generated into THIS file by sig_table.py, so
 * they are this card's to fill.
 *
 * Design note (read before touching this file): sim.c's om_world_step only
 * calls om_tactical_step (csrc/unit.c), never anything of this file's --
 * there is no per-tick callback into tactical_move.c. Every accessor below
 * therefore starts by calling om_move_sync(), which replays this module's
 * own tick loop from its last-seen tactical tick (om_tactical_tick,
 * csrc/unit.c; the strategic w->tick is a distinct clock, R-055-02) up to
 * the current one before reading or writing anything. This makes every
 * command "apply immediately" (no tick boundary needed to observe it)
 * while still producing a real per-tick simulation for
 * position/facing/collision -- see om_move_sync/
 * om_move_tick_once below.
 *
 * Known cross-module gaps (unit.c/B10b, tactical_mapgen.c/B15m, fog.c/B11
 * all still STUB or missing a reader for what this card would need):
 *   - om_command_attack_move and the real om_command_attack_target
 *     (csrc/unit.c) never call into this module, so a plain attack-move/
 *     attack-target order never produces movement or a readable target
 *     here. om_unit_get_target/om_unit_target (csrc/unit.c) are also STUB.
 *   - om_unit_attack (csrc/unit.c) is STUB: never deals damage, so
 *     om_combat_can_shoot's answer is never consulted or exercised.
 *   - om_map_add_obstacle/om_map_add_cover (csrc/tactical_mapgen.c) are
 *     STUB and have no public reader, so a slot-unwalkable fallback or a
 *     cover-blocks-LOS check driven through them cannot be observed here.
 *   - no public accessor returns a unit's faction, category, or unit_type
 *     from its id (only from a unit_type by om_unit_profile_*, and only
 *     position/hp/effective_speed/alive/ability_active by id). Two
 *     approximations follow from this, both noted at their definition:
 *     the ally-only steering probe (R-097-03) treats every other living
 *     unit as a potential blocker, and the Strike/Line/Siege turn-rate
 *     bucket (R-100-02) is inferred from a unit's own native speed against
 *     the roster's speed bands (csrc/unit.c OM_ROSTER_*_SPEED), which are
 *     disjoint (Strike 130-150, Line 70-80, Siege 40-50) for the six
 *     launch types.
 *   - no accessor enumerates a world's units. om_move_discover() probes
 *     unit ids 1..OM_MAX_UNITS through the real om_unit_alive(),
 *     since ids are dense from 1 (csrc/unit.c om_tac_state.next_unit_id).
 *     Fine at this suite's scale (<=20 units/world); not what the epic's
 *     1,000/10,000-unit scale requirement wants long-term.
 */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include <math.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#if defined(__SSE2__)
#include <emmintrin.h>
#endif

/* ---------------------------------------------------------------- setup */

#define OM_MOVE_MAX_UNITS (OM_MAX_UNITS + 1)
/* PP-unit G5: the six built-in unit types plus unit.c's OM_MAX_CUSTOM_TYPES (64). */
#define OM_PP_REACH_MAX 70
#define OM_MOVE_MAX_GROUPS OM_MAX_UNITS
#define OM_MOVE_MAX_GROUP_MEMBERS OM_MAX_UNITS
/* Dense density grid (A134): one value per 100 wu cell of the largest canvas, per layer. */
#define OM_MOVE_DENSITY_SIDE (OM_CANVAS_SIZE_RANGES_LARGE_HI / OM_NAVMESH_CELL_SIZE)
#define OM_MOVE_MAX_ROUTE_CACHE OM_MAX_UNITS
#define OM_MOVE_MAX_QUEUE OM_MAX_UNITS
#define OM_MOVE_BFS_DIR_COUNT 4
/* Route fields kept for shared destinations (R-097-02): one distance per cell of the largest canvas, each. */
#define OM_MOVE_FIELD_POOL 16
#define OM_MOVE_FIELD_UNREACHED UINT32_MAX
/* R-099-04, ALG-68 WAYPOINT_ARRIVE_MULT: hand-defined here, om_constants.h is not generated from algorithms.md (as OM_COLLISION_PASSES was). */
#define OM_WAYPOINT_ARRIVE_MULT 2.0

/* Spatial index over this module's own unit positions (om_move_unit x/y).
 * unit.c's grid (om_grid_query_circle) holds unit.c's position cache, which
 * lags this module's positions (the sync runs before the cache refresh, and
 * collision pushes move units mid-pass), so the exact all-pairs results
 * would not survive using it.
 *
 * The index is a dense grid: living units are filed once, sorted by cell
 * (ids ascending inside a cell) into flat slot arrays, so a row of cells is
 * one run of slots and a query is a few straight loops. A unit that moves is
 * not re-filed; it keeps its slot and its position is updated in place, and a
 * query widens its cell range by how far any filed unit has moved
 * (grid_disp). A unit that gets more than OM_MOVE_GRID_MARGIN from where it
 * was filed goes to a short spill list that every query scans as well; a
 * full spill list refiles everything (from the index itself, without touching
 * the units). Results never depend on this layout: a query returns exactly
 * the units within its radius. */
#define OM_MOVE_GRID_MAX_CELLS 65536
#define OM_MOVE_GRID_BASE_CELL (4.0 * OM_UNIT_COLLISION_RADIUS)
#define OM_MOVE_GRID_MARGIN (3.0 * OM_UNIT_COLLISION_RADIUS)
#define OM_MOVE_GRID_SPILL_MAX 48
#define OM_MOVE_GRID_BOUND_PAD 1.0e-6
#define OM_MOVE_GRID_FAR 1.0e300
#define OM_MOVE_DESCENT_SEARCH_RINGS 64
#define OM_MOVE_CELL_MID 0.5
#define OM_MOVE_ROUND_HALF 0.5
#define OM_MOVE_FLOOR_LIMIT 1.0e9
#define OM_MOVE_INSERTION_SORT_MAX 96
#define OM_MOVE_NET_SMALL 8
#define OM_MOVE_NET_LARGE 16
#define OM_MOVE_MASK_BITS 64

/* The neighbour list of the collision sweep (om_move_collision_once) reaches this many collision radii. */
#define OM_MOVE_LIST_REACH_RADII 4.0
/* Marking stops, and every unit takes its turn, once this fraction (1 / the divisor) of the units have been
 * marked in one collision call: past that a dense scene revisits nearly everyone and the marking costs more
 * than it saves. A turn the marks would have skipped writes nothing, so results are bit-identical. */
#define OM_MOVE_MARK_FULL_DIV 4

/* Steering probe: the largest gap between a probe point computed with
 * om_sin/om_cos and one computed with om_move_sincos_approx is under 0.05 wu;
 * a probe is taken as blocked without om_sin/om_cos when a unit is closer than
 * the collision diameter by this much to the approximate point. */
#define OM_MOVE_PROBE_SURE_MARGIN 0.1
#define OM_MOVE_PROBE_HINTS 2
/* A probe point is OM_STEERING_PROBE_DIST from its unit, give or take the
 * om_sin/om_cos error (under 5e-4 per component): under this. */
#define OM_MOVE_PROBE_REACH 40.1

/* OM_MOVE_CAT_STRIKE_SPEED_MIN, OM_MOVE_CAT_LINE_SPEED_MIN, OM_OBSTACLE_DENSITY_LOW_THRESHOLD,
 * OM_TERRAIN_SPEED_PENALTY_COEF, OM_LOS_SAMPLE_STEP, OM_STEERING_SWEEP_COUNT,
 * OM_STEERING_SWEEP_DELTA_RAD promoted to csrc/om_constants.h (CONST-1, ALG-67/68/69).
 * OM_TWO_PI_LOCAL promoted to csrc/om_constants.h as OM_TWO_PI (CONST-1, math).
 * OM_MOVE_PROBE_REACH 40.1 kept local: deliberately not 40.0 (tolerance note above). */

#define OM_COLLISION_MAX_ITER 3 /* PURSUE_BY_STEERING = 0 baseline; 1 uses OM_COLLISION_PASSES (A156) */
#define OM_COLLISION_EXACT_EPS 1e-9
#define OM_COLLISION_SETTLE_EPS2 (OM_COLLISION_SETTLE_EPS * OM_COLLISION_SETTLE_EPS)

#define OM_PI 3.14159265358979323846
#define OM_PI_2 1.57079632679489661923
#define OM_PI_4 0.78539816339744830962

/* Deterministic atan(x) on [-1, 1] (Anderson's cheap-trig rational
 * approximation, |error| < 0.005 rad); every test tolerance in this suite
 * is >= 1e-2 rad, so this is accurate enough while never calling libm's
 * banned sin/cos/atan family (csrc's om_sin is the only trig primitive
 * that exists; om_cos is derived from it below). */
#define OM_ATAN_COEF_A 0.2447
#define OM_ATAN_COEF_B 0.0663

/* Multiples of OM_STEERING_SWEEP_DELTA_RAD (om_constants.h); pre-computed
 * to avoid repeated multiply in the sweep loop. */
#define OM_STEERING_SWEEP_DELTA_RAD_2X 0.5235987756
#define OM_STEERING_SWEEP_DELTA_RAD_2X 0.5235987756
#define OM_STEERING_SWEEP_DELTA_RAD_3X 0.7853981634
#define OM_STEERING_SWEEP_DELTA_RAD_4X 1.0471975512
#define OM_STEERING_SWEEP_DELTA_RAD_5X 1.3089969390
#define OM_STEERING_SWEEP_DELTA_RAD_6X 1.5707963268

/* Planner points a walker keeps (point 0 is the unit; a longer plan stores nothing and replans at each waypoint). */
#define OM_MOVE_WALK_PTS 512
#define OM_MOVE_ROUTE_HALF 0.5 /* walk_route.c WR_HALF: a cell centre is (cell + 1/2) * OM_TERRAIN_CELL_WU */

typedef struct {
    int      in_use;
    uint32_t unit_id;
    double   x, y;
    double   pushed_x, pushed_y;
    double   facing;
    double   prev_x, prev_y, prev_facing;
    int      has_dest;
    uint32_t giveup_near;
    double   dest_x, dest_y;
    int      direct_move;
    uint32_t group_id;
    double   speed_cap;
    int      engaged;
    int      kiting;
    uint32_t kite_target;
    int      order_kind;
    double   native_speed;
    int      deflecting;
    double   deflect_heading;
    double   deflect_origin_x, deflect_origin_y;
    int      waiting;
    double   detour_remaining, detour_dx, detour_dy;
    int      visible[OM_MAX_FACTIONS];
    int      plan_valid;                 /* PP-move route (ROUTE_AROUND_TERRAIN): aim_x/aim_y is the next waypoint */
    uint32_t plan_epoch;
    uint32_t plan_layer;                 /* the walker's layer when the plan was made; a different layer replans */
    double   plan_dest_x, plan_dest_y, aim_x, aim_y;
    int      aim_is_waypoint;
    int      routed; /* this order's route had a waypoint: its final arrival radius is the waypoint's (R-099-04) */
    /* G4 layer transfer (R-002-02 to R-002-07, R-004-01 to R-004-04): lay_state OM_LAY_NONE, OM_LAY_PENDING (waiting
     * for lay_to to be open here) or OM_LAY_FLIGHT (lay_t of lay_dur ticks done; the layer crosses over at half).
     * lay_pend is an order given in flight, begun when the flight ends. transit: the router sent the unit over a
     * mass and it comes back down to transit_home; lay_route marks the pending order as the router's. */
    int      lay_state, lay_has_pend, lay_route, transit;
    uint32_t lay_to, lay_pend, lay_t, lay_dur, transit_home;
    /* W2 stored walk route: the planner's points 1 .. route_n - 1 live as terrain cells in om_move_state.route_cx/route_cy
     * (slot 0, the unit, is not stored); route_i is the slot the walker aims at. route_n 0 = nothing stored.
     * See also: tests/csim/test_VG_W_w2_routes.py, om_move_walker_step */
    uint16_t route_n, route_i;
    uint8_t  route_ends_at_goal;
} om_move_unit;

typedef struct {
    int      active;
    uint32_t id;
    uint32_t first_member;
    uint32_t n_members;
    double   click_x, click_y;
    double   speed_cap;
} om_move_group;

typedef struct {
    int      in_use;
    uint32_t layer;
    int32_t  cx, cy;
} om_move_route_entry;

typedef struct {
    int      in_use;
    uint32_t layer, epoch;
    int32_t  cx, cy;
    uint32_t *dist; /* cells to the destination along the grid, counting both ends; OM_MOVE_FIELD_UNREACHED if cut off */
} om_move_field;

typedef struct {
    int      in_use;
    uint64_t tick;
    int      kind;
    uint32_t unit_id;
    double   x, y;
} om_move_queue_entry;

typedef struct {
    om_move_unit units[OM_MOVE_MAX_UNITS];
    uint32_t     discovery_max;
    /* W2: [unit id][slot] terrain cells of the stored routes; each table is one calloc on the first stored plan (NULL until then). */
    uint16_t     (*route_cx)[OM_MOVE_WALK_PTS], (*route_cy)[OM_MOVE_WALK_PTS];

    om_move_group groups[OM_MOVE_MAX_GROUPS];
    uint32_t      n_groups;
    uint32_t      group_members[OM_MOVE_MAX_GROUP_MEMBERS];
    uint32_t      n_group_members;
    uint32_t      next_group_id;

    uint64_t last_synced_tick;
    uint32_t period_seen;
    int      syncing; /* transient: set while om_move_sync runs ticks, so a read from inside a tick (om_walk_route) does not re-enter */

    om_move_field        fields[OM_MOVE_FIELD_POOL];
    uint32_t             field_next, terrain_epoch;
    uint32_t             *bfs_queue, *bfs_scratch; /* a cell per entry of the largest canvas, allocated by the first search */
    double               *density; /* OM_LAYER_COUNT * OM_MOVE_DENSITY_SIDE^2, allocated by the first set */

    om_move_route_entry route_cache[OM_MOVE_MAX_ROUTE_CACHE];
    uint32_t             n_route_cache;
    uint32_t             route_evict;
    uint32_t             cache_hits;
    int                  last_path_straightened;

    om_move_queue_entry queue[OM_MOVE_MAX_QUEUE];
    uint32_t            n_queue;

    int      grid_live;
    double   grid_ox, grid_oy, grid_cell, grid_inv;
    int32_t  grid_w, grid_h;
    uint32_t grid_start[OM_MOVE_GRID_MAX_CELLS + 1];
    uint32_t grid_fill[OM_MOVE_GRID_MAX_CELLS];
    uint32_t slot_base, n_spill;
    double   grid_disp;
    /* Largest distance from a unit's start-of-tick position to where the grid filed it: the probe's widening. */
    double   probe_extra;
    uint32_t slot_id[OM_MOVE_MAX_UNITS + OM_MOVE_GRID_SPILL_MAX];
    double   slot_x[OM_MOVE_MAX_UNITS + OM_MOVE_GRID_SPILL_MAX];
    double   slot_y[OM_MOVE_MAX_UNITS + OM_MOVE_GRID_SPILL_MAX];
    double   slot_fx[OM_MOVE_MAX_UNITS], slot_fy[OM_MOVE_MAX_UNITS];
    /* start_x / start_y of the unit filed in each cell slot, in slot order, for the steering probe's scan. */
    double   slot_sx[OM_MOVE_MAX_UNITS], slot_sy[OM_MOVE_MAX_UNITS];
    uint32_t unit_slot[OM_MOVE_MAX_UNITS];
    uint32_t unit_cell[OM_MOVE_MAX_UNITS];
    double   scan_x[OM_MOVE_MAX_UNITS], scan_y[OM_MOVE_MAX_UNITS];
    uint8_t  grid_in[OM_MOVE_MAX_UNITS];
    double   sweep_cos[OM_STEERING_SWEEP_COUNT], sweep_sin[OM_STEERING_SWEEP_COUNT];
    uint8_t  stat[OM_MOVE_MAX_UNITS];
uint8_t  col_need[OM_MOVE_MAX_UNITS];
uint32_t col_marks;
uint8_t  col_all;
uint8_t  col_open;
uint32_t col_moved;
uint8_t  col_last;
uint32_t col_cur;
    uint32_t grid_scratch[OM_MOVE_MAX_UNITS];

    int      settle_valid;
    uint32_t settle_max;
    uint8_t  settle_flag[OM_MOVE_MAX_UNITS];
    double   settle_x[OM_MOVE_MAX_UNITS];
    double   settle_y[OM_MOVE_MAX_UNITS];

    /* Per-cell group sentinel for probe_gather cell skip.
     * UINT32_MAX = all units in cell share the same group_id (or cell empty).
     * 0          = heterogeneous (no skip possible).
     * other      = that group_id (skip safe for a probe with self_group == it).
     * Recomputed by om_move_grid_rebuild. */
    uint32_t cell_group[OM_MOVE_GRID_MAX_CELLS];
    /* Flat group_id mirror: unit_group[id] == units[id].group_id.
     * 140-byte stride to units[] trashes cache in the probe inner loop;
     * this array keeps group_id at a 4-byte stride. */
    uint32_t unit_group[OM_MOVE_MAX_UNITS];

    /* PP-move (PURSUE_BY_STEERING): every unit's position and layer at the start of the tick, which
     * the steering probe reads (R-097-03); it never sees a position an earlier unit moved this tick. */
    double   start_x[OM_MOVE_MAX_UNITS], start_y[OM_MOVE_MAX_UNITS];
    double   pass_x[OM_MOVE_MAX_UNITS], pass_y[OM_MOVE_MAX_UNITS];
    int32_t  start_layer[OM_MOVE_MAX_UNITS];
    /* col_pursue / col_route cache the two switches during a collision pass. */
    int      col_pursue, col_route;
    /* The runtime unit collision radius (OM_TP_UNIT_COLLISION_RADIUS), read once per tick and per standalone collision
     * pass by om_move_load_radius; every site that ruling 15 names reads this, never the compile-time default. */
    double   radius;
    /* PP-move (PURSUE_BY_STEERING): the map canvas, 0 x 0 when unset (no clamp); see om_move_set_canvas_size. */
    double   canvas_w, canvas_h;

    /* PP-move: the tunable settings (om_tac_param); see om_tactical_set_param. */
    double   param[OM_TP__COUNT];
    int      lay_any; /* a layer order or a routed transfer has happened: the per-tick layer pass runs */
    /* PP-unit G5 (R-164-02): reach by unit type; a type absent here has reach 0 up, 0 down. Kept with the settings, so
     * unit.c's om_tactical_reset carries the built-in types across the reset. See also: om_roster_set_reach. */
    uint32_t reach_n;
    int32_t  reach_type[OM_PP_REACH_MAX];
    uint32_t reach_up[OM_PP_REACH_MAX], reach_down[OM_PP_REACH_MAX];
    /* Terrain stage 2: movement kind per unit type (om_movement_kind), a sparse list keyed by type like reach; an
     * unset type reads flying. Kept and carried across om_tactical_reset like reach. See also: om_roster_set_movement_kind. */
    uint32_t kind_n;
    int32_t  kind_type[OM_PP_REACH_MAX];
    int32_t  kind_val[OM_PP_REACH_MAX];
} om_move_state;

enum { OM_LAY_NONE, OM_LAY_PENDING, OM_LAY_FLIGHT };

/* See also: om_tac_unit_set_layer in unit.c, which owns the unit's layer row */
void om_tac_unit_set_layer(om_world *w, uint32_t unit_id, uint32_t layer);
/* See also: om_tac_unit_set_guard in unit.c, which owns the guard flag (R-096-08) */
void om_tac_unit_set_guard(om_world *w, uint32_t unit_id, int on);

/* A new move order ends a routed transfer that has not begun; one in flight finishes (R-002-04: a user's transfer
 * is never cleared by a move order). */
static void om_move_transit_cancel(om_move_unit *mu) {
    if (!mu->transit) return;
    mu->transit = 0;
    if (mu->lay_route && mu->lay_state == OM_LAY_PENDING) mu->lay_state = OM_LAY_NONE;
}

/* PP-move: every om_tac_param member's kind, default and refusal range (docs/northstar/plans/push/pp_contract.md
 * section 4). The ranges are the writer's refusal bounds for the lab's setting call, never game values (A133 Q-C9);
 * they are named here because om_constants.h has no home for them. */
#define OM_PP_MULT_HI 10.0
#define OM_PP_TERRAIN_STEEP_DEFAULT 35.0 /* provisional (2026-10-05) */
#define OM_PP_TERRAIN_STEEP_HI 90.0
#define OM_PP_SLOPE_FACTOR_DEFAULT 1.1 /* R-004-07: Westley 2026-10-06; provisional (2026-10-06) */
#define OM_PP_SIGHT_EYE_DEFAULT 50.0 /* wu above the ground; provisional (2026-10-06) lab draft */
#define OM_PP_SIGHT_EYE_HI 1000.0
#define OM_PP_ARC_DEFAULT 360.0 /* LAB-REV2 E0: no arc; provisional draft, Westley owns */
#define OM_PP_ARC_LO 10.0
#define OM_PP_ARC_HI 360.0
#define OM_PP_FLYER_SEEN_DEFAULT 1.5 /* provisional (2026-10-06) lab draft; Westley: longer than the flyer's own vision */
#define OM_PP_AOE_CAP_HI 100.0
#define OM_PP_PING_REACH_DEFAULT 2000.0
/* R-162-01: 5 s at the tactical rate; om_constants.h OM_PULSE_REVEAL_TICKS (40) is the bible's old 2 s */
#define OM_PP_PING_REVEAL_DEFAULT 100
#define OM_PP_PING_REVEAL_HI 1200
#define OM_PP_PING_COOLDOWN_HI 12000

typedef struct { uint8_t kind; double def, lo, hi; } om_pp_row;
enum { OM_PP_BOOL, OM_PP_INT, OM_PP_REAL };

#define OM_PP_SWITCH(d) { OM_PP_BOOL, d, 0.0, 1.0 }
#define OM_PP_MULT(d) { OM_PP_REAL, d, 0.0, OM_PP_MULT_HI }
#define OM_PP_MULT4(d) OM_PP_MULT(d), OM_PP_MULT(d), OM_PP_MULT(d), OM_PP_MULT(d)
#define OM_PP_VIS(d) { OM_PP_REAL, d, 0.0, 1.0 }
#define OM_PP_VIS4 OM_PP_VIS(OM_CONE_LAYER_1_FACTOR), OM_PP_VIS(OM_CONE_LAYER_2_FACTOR), OM_PP_VIS(0.0), OM_PP_VIS(0.0)
#define OM_PP_DIST(d) { OM_PP_REAL, d, 0.0, OM_CANVAS_SIZE_RANGES_LARGE_HI }

static const om_pp_row OM_PP_ROWS[OM_TP__COUNT] = {
    /* A155/A156: PURSUE_BY_STEERING defaults 1 (the option c' interim default 0 is reverted) */
    OM_PP_SWITCH(1.0), OM_PP_SWITCH(1.0), OM_PP_SWITCH(0.0),
    { OM_PP_INT, 0.0, 0.0, 1.0 },
    OM_PP_SWITCH(1.0), OM_PP_SWITCH(1.0),
    /* H-057: OM_ATTACK_MOVE_LEASH_DIST is 0.0 = the type's own leash, max(sensor_radius, attack_range); non-zero overrides in wu */
    OM_PP_DIST(OM_ATTACK_MOVE_LEASH_DIST), OM_PP_DIST(OM_RETURN_FIRE_FLEE_DIST),
    { OM_PP_REAL, OM_UNIT_COLLISION_RADIUS, 0.0, OM_GRID_CELL_SIZE / 2.0 },
    OM_PP_MULT(OM_VANTAGE_CONE_MULTIPLIER),
    { OM_PP_REAL, OM_AOE_DAMAGE_CAP_MULTIPLIER, 0.0, OM_PP_AOE_CAP_HI },
    { OM_PP_INT, OM_TARGETING_COHORT_COUNT, 1.0, OM_TACTICAL_TICK_RATE },
    OM_PP_MULT(OM_CATEGORY_MULTIPLIER_LINE_LINE), OM_PP_MULT(OM_CATEGORY_MULTIPLIER_LINE_SIEGE),
    OM_PP_MULT(OM_CATEGORY_MULTIPLIER_LINE_STRIKE), OM_PP_MULT(OM_CATEGORY_MULTIPLIER_SIEGE_LINE),
    OM_PP_MULT(OM_CATEGORY_MULTIPLIER_SIEGE_SIEGE), OM_PP_MULT(OM_CATEGORY_MULTIPLIER_SIEGE_STRIKE),
    OM_PP_MULT(OM_CATEGORY_MULTIPLIER_STRIKE_LINE), OM_PP_MULT(OM_CATEGORY_MULTIPLIER_STRIKE_SIEGE),
    OM_PP_MULT(OM_CATEGORY_MULTIPLIER_STRIKE_STRIKE),
    OM_PP_MULT(1.0), OM_PP_MULT(1.0),
    OM_PP_DIST(OM_PULSE_RADIUS),
    { OM_PP_INT, OM_PP_PING_REVEAL_DEFAULT, 0.0, OM_PP_PING_REVEAL_HI },
    { OM_PP_INT, OM_PULSE_COOLDOWN_TICKS, 0.0, OM_PP_PING_COOLDOWN_HI },
    OM_PP_DIST(OM_PP_PING_REACH_DEFAULT),
    OM_PP_VIS4, OM_PP_VIS4,
    OM_PP_MULT4(1.0), OM_PP_MULT4(1.0), OM_PP_MULT4(1.0), OM_PP_MULT4(1.0), OM_PP_MULT4(1.0), OM_PP_MULT4(1.0),
    /* A196: faction 1's target policy, -1 = unset (follows OM_TP_TARGET_POLICY); lab only */
    { OM_PP_INT, -1.0, -1.0, 1.0 },
    /* R-162-03: the pinged side's alert, 0 off (default), 1 on */
    OM_PP_SWITCH(0.0),
    /* R-200-03, Q-189-02: steepest walkable slope in degrees, 35 default (provisional 2026-10-05; Westley owns) */
    { OM_PP_REAL, OM_PP_TERRAIN_STEEP_DEFAULT, 0.0, OM_PP_TERRAIN_STEEP_HI },
    /* R-004-07: slope speed divided going up, multiplied going down (1.1 each; Westley 2026-10-06; provisional) */
    { OM_PP_REAL, OM_PP_SLOPE_FACTOR_DEFAULT, 1.0, OM_PP_MULT_HI },
    { OM_PP_REAL, OM_PP_SLOPE_FACTOR_DEFAULT, 1.0, OM_PP_MULT_HI },
    /* R-005-10: eye height above the ground at both ends of a sight line, wu (lab draft) */
    { OM_PP_REAL, OM_PP_SIGHT_EYE_DEFAULT, 0.0, OM_PP_SIGHT_EYE_HI },
    /* R-005-11: ground-era flyer seen from max(sensor radii) x this; at least 1 so it is seen from farther than it sees */
    { OM_PP_REAL, OM_PP_FLYER_SEEN_DEFAULT, 1.0, OM_PP_MULT_HI },
    /* LAB-REV2 E0 (R-100 draft): firing arc in degrees, 360 = no arc (default); read by the fire pass from LAB-REV2-E2 */
    { OM_PP_REAL, OM_PP_ARC_DEFAULT, OM_PP_ARC_LO, OM_PP_ARC_HI },
};

static void om_pp_load_defaults(double *out) {
    uint32_t k;
    for (k = 0; k < OM_TP__COUNT; k++) out[k] = OM_PP_ROWS[k].def;
}

/* Defined in tactical_mapgen.c: the route grid's blocked bits (om_map_block_rect and density above the threshold).
 * See also: om_mapgen_cell_blocked / om_mapgen_cell_set_density there. */
int om_mapgen_cell_blocked(const om_world *w, uint32_t layer, int32_t cx, int32_t cy);
void om_mapgen_cell_set_density(om_world *w, uint32_t layer, int32_t cx, int32_t cy, double density);
int om_mapgen_terrain_free(const om_world *w);

static void om_move_state_free_fn(void *p) {
    if (p) {
        om_move_state *ms = (om_move_state *)p;
        uint32_t k;
        for (k = 0; k < OM_MOVE_FIELD_POOL; k++) free(ms->fields[k].dist);
        free(ms->bfs_queue);
        free(ms->bfs_scratch);
        free(ms->density);
        free(ms->route_cx);
        free(ms->route_cy);
    }
    free(p);
}

/* -------------------------------------------------------------- geometry */

static double om_cos(double x) {
    return om_sin(x + OM_PI_2);
}

static double om_atan_unit(double x) {
    double ax = fabs(x);
    return (OM_PI_4 * x) - x * (ax - 1.0) * (OM_ATAN_COEF_A + OM_ATAN_COEF_B * ax);
}

static double om_atan(double x) {
    if (fabs(x) <= 1.0) return om_atan_unit(x);
    if (x > 0.0) return OM_PI_2 - om_atan_unit(1.0 / x);
    return -OM_PI_2 - om_atan_unit(1.0 / x);
}

static double om_atan2(double y, double x) {
    if (x > 0.0) return om_atan(y / x);
    if (x < 0.0 && y >= 0.0) return om_atan(y / x) + OM_PI;
    if (x < 0.0 && y < 0.0) return om_atan(y / x) - OM_PI;
    if (x == 0.0 && y > 0.0) return OM_PI_2;
    if (x == 0.0 && y < 0.0) return -OM_PI_2;
    return 0.0;
}

static double om_wrap_pi(double a) {
    while (a > OM_PI) a -= OM_TWO_PI;
    while (a <= -OM_PI) a += OM_TWO_PI;
    return a;
}

/* Fast sine and cosine for the steering probe's blocked-for-sure test: Taylor
 * series on [-pi, pi] whose first dropped terms bound the error (alternating,
 * decreasing): under 2.3e-5 for sin, 4.4e-6 for cos. Not om_sin: it stands in
 * for om_sin only where a margin covers the difference (see
 * om_move_probe_sure_blocked). The series are single-line defines because the
 * constants lint reads a #define line as a named constant. */
#define OM_MOVE_TAYLOR_SIN(r, r2) ((r) * (1.0 + (r2) * (-1.0 / 6.0 + (r2) * (1.0 / 120.0 + (r2) * (-1.0 / 5040.0 + (r2) * (1.0 / 362880.0 + (r2) * (-1.0 / 39916800.0 + (r2) * (1.0 / 6227020800.0))))))))
#define OM_MOVE_TAYLOR_COS(r2) (1.0 + (r2) * (-1.0 / 2.0 + (r2) * (1.0 / 24.0 + (r2) * (-1.0 / 720.0 + (r2) * (1.0 / 40320.0 + (r2) * (-1.0 / 3628800.0 + (r2) * (1.0 / 479001600.0 + (r2) * (-1.0 / 87178291200.0))))))))

static void om_move_sincos_approx(double a, double *s, double *c) {
    double r = om_wrap_pi(a), r2 = r * r;
    *s = OM_MOVE_TAYLOR_SIN(r, r2);
    *c = OM_MOVE_TAYLOR_COS(r2);
}

static double om_move_turn_rate_for(double native_speed) {
    if (native_speed >= OM_MOVE_CAT_STRIKE_SPEED_MIN) return OM_FACING_ROTATION_SPEED_STRIKE;
    if (native_speed >= OM_MOVE_CAT_LINE_SPEED_MIN) return OM_LINE;
    return OM_SIEGE;
}

/* R-100-02: the turn cap is set by category (0 Strike, 1 Line, else Siege), never by speed.
 * See also: om_move_turn_rate_for, the speed-band rate the baseline (switch = 0) keeps. */
static double om_move_turn_rate_by_category(om_world *w, uint32_t id) {
    int cat = om_unit_profile_category(w, om_unit_get_unit_type(w, id));
    if (cat == 0) return OM_FACING_ROTATION_SPEED_STRIKE;
    return cat == 1 ? OM_LINE : OM_SIEGE;
}

/* arc_low: an exact half-turn goes the negative way, as the Python's shortest arc on [-pi, pi) (facing.py
 * _shortest_arc); the PURSUE_BY_STEERING facing pass sets it. */
static double om_move_turn_toward(double current, double target, double rate_per_sec, uint32_t period, int arc_low) {
    double delta = om_wrap_pi(target - current);
    if (arc_low && delta >= OM_PI) delta -= OM_TWO_PI;
    double max_step = rate_per_sec * (double)period / (double)OM_TACTICAL_TICK_RATE;
    if (delta > max_step) delta = max_step;
    if (delta < -max_step) delta = -max_step;
    return current + delta;
}

static double om_move_terrain_multiplier(double density) {
    if (density > OM_NAVMESH_OBSTACLE_THRESHOLD) return 0.0;
    if (density >= OM_OBSTACLE_DENSITY_LOW_THRESHOLD) {
        return 1.0 - OM_TERRAIN_SPEED_PENALTY_COEF * density;
    }
    return 1.0;
}

/* PP-move P8 (R-097-03, ALG-68): the six sweep headings as fixed direction vectors (cos, sin) of
 * +30, -30, +60, -60, +90, -90 degrees, in the order the sweep tries them; no trig. */
#define OM_PP_SQRT3_HALF 0.866025403784439
#define OM_PP_HALF 0.5
#define OM_PP_SWEEP_N 6
static const double OM_PP_SWEEP_COS[OM_PP_SWEEP_N] = { OM_PP_SQRT3_HALF, OM_PP_SQRT3_HALF, OM_PP_HALF, OM_PP_HALF, 0.0, 0.0 };
static const double OM_PP_SWEEP_SIN[OM_PP_SWEEP_N] = { OM_PP_HALF, -OM_PP_HALF, OM_PP_SQRT3_HALF, -OM_PP_SQRT3_HALF, 1.0, -1.0 };

static const double OM_STEERING_SWEEP_ANGLES[OM_STEERING_SWEEP_COUNT] = {
    0.0,
    OM_STEERING_SWEEP_DELTA_RAD, -OM_STEERING_SWEEP_DELTA_RAD,
    OM_STEERING_SWEEP_DELTA_RAD_2X, -OM_STEERING_SWEEP_DELTA_RAD_2X,
    OM_STEERING_SWEEP_DELTA_RAD_3X, -OM_STEERING_SWEEP_DELTA_RAD_3X,
    OM_STEERING_SWEEP_DELTA_RAD_4X, -OM_STEERING_SWEEP_DELTA_RAD_4X,
    OM_STEERING_SWEEP_DELTA_RAD_5X, -OM_STEERING_SWEEP_DELTA_RAD_5X,
    OM_STEERING_SWEEP_DELTA_RAD_6X, -OM_STEERING_SWEEP_DELTA_RAD_6X,
};

static void om_move_set_save_hooks(om_world *w);
static om_move_state *om_ms(om_world *w) {
    om_move_state *ms = (om_move_state *)w->move_state;
    if (!ms) {
        uint32_t k;
        ms = (om_move_state *)calloc(1, sizeof(om_move_state));
        for (k = 0; k < OM_STEERING_SWEEP_COUNT; k++) {
            om_move_sincos_approx(OM_STEERING_SWEEP_ANGLES[k], &ms->sweep_sin[k], &ms->sweep_cos[k]);
        }
        ms->next_group_id = 1;
        om_pp_load_defaults(ms->param);
        w->move_state = ms;
        w->move_state_free = om_move_state_free_fn;
        om_move_set_save_hooks(w);
    }
    return ms;
}

static int om_move_param_on(const om_move_state *ms, om_tac_param p) {
    return ms->param[p] != 0.0;
}

/* A changed radius ends the settle cache: a pass that found no overlap at the old radius may find one at the new. */
static void om_move_load_radius(om_move_state *ms) {
    const double r = ms->param[OM_TP_UNIT_COLLISION_RADIUS];
    if (r == ms->radius) return;
    ms->radius = r;
    ms->settle_valid = 0;
}

/* Internal, not in the header: a cell turned blocked or open outside om_map_set_obstacle_density (om_map_block_rect),
 * so every kept route is stale (R-207-03). See also: om_map_block_rect in csrc/tactical_mapgen.c, the caller to be. */
void om_move_terrain_changed(om_world *w) {
    if (w) om_ms(w)->terrain_epoch++;
}

/* Internal, not in the header: the route-cache epoch, part of the planner's cache key.
 * See also: walk_route.c, the caller; om_move_terrain_changed above, the bump. */
uint32_t om_move_terrain_epoch(om_world *w) {
    return w ? om_ms(w)->terrain_epoch : 0;
}

/* Internal, not in the header: the canvas only lives in the private mapgen state, so om_map_set_canvas and
 * om_map_clear (tactical_mapgen.c) hand its size over; 0 x 0 = unset.
 * See also: om_map_set_canvas in csrc/tactical_mapgen.c, the caller. */
void om_move_set_canvas_size(om_world *w, double width, double height) {
    om_move_state *ms;
    if (!w) return;
    ms = om_ms(w);
    ms->canvas_w = width;
    ms->canvas_h = height;
    ms->terrain_epoch++;
}

/* Internal, not in the header: the canvas size om_move_set_canvas_size stored; 0 x 0 = unset.
 * See also: the patrol waypoint clamp in om_macro_issue_group_orders (csrc/enemy_macro.c), the caller. */
void om_move_get_canvas_size(om_world *w, double *width, double *height) {
    *width = w ? om_ms(w)->canvas_w : 0.0;
    *height = w ? om_ms(w)->canvas_h : 0.0;
}

/* Python movement.py: new positions are clamped to [0, width] x [0, height]. */
static double om_move_clamp_axis(double v, double lim) {
    if (lim <= 0.0) return v;
    return v < 0.0 ? 0.0 : (v > lim ? lim : v);
}

/* ---------------------------------------------------------- unit lookup */

static om_move_unit *om_move_get(om_move_state *ms, uint32_t unit_id) {
    if (unit_id == 0 || unit_id >= OM_MOVE_MAX_UNITS) return NULL;
    return &ms->units[unit_id];
}

/* W2: both route tables, allocated together on first use; 0 when memory is short (the walker then stores nothing). */
static int om_move_route_tables(om_move_state *ms) {
    if (!ms->route_cx) ms->route_cx = (uint16_t (*)[OM_MOVE_WALK_PTS])calloc(OM_MOVE_MAX_UNITS, sizeof *ms->route_cx);
    if (!ms->route_cy) ms->route_cy = (uint16_t (*)[OM_MOVE_WALK_PTS])calloc(OM_MOVE_MAX_UNITS, sizeof *ms->route_cy);
    return ms->route_cx && ms->route_cy;
}

/* floor(t) as an int32, clamped to +-1e9 (NaN counts as -1e9); monotone in t.
 * The grid indexes with this instead of libm's floor, which is a call
 * without SSE4.1 and dominates a query's setup. */
static int32_t om_move_floor_i(double t) {
    int32_t i;
    if (!(t > -OM_MOVE_FLOOR_LIMIT)) return -(int32_t)OM_MOVE_FLOOR_LIMIT;
    if (t > OM_MOVE_FLOOR_LIMIT) return (int32_t)OM_MOVE_FLOOR_LIMIT;
    i = (int32_t)t;
    return (double)i > t ? i - 1 : i;
}

/* Cell of v along one axis, clamped into [0, n); monotone in v, so a query's
 * cell range and a unit's filed cell always agree. */
static int32_t om_move_grid_axis_cell(double v, double origin, double inv_cell, int32_t n) {
    int32_t t = om_move_floor_i((v - origin) * inv_cell);
    return t < 0 ? 0 : (t >= n ? n - 1 : t);
}

static void om_move_grid_rebuild(om_world *w, om_move_state *ms, int from_units);

/* Moves a filed unit to (x, y). A unit that gets more than
 * OM_MOVE_GRID_MARGIN from where it was filed leaves its cell for the spill
 * list (its cell slot goes NaN, which no distance test passes), so every
 * unit still in a cell is within grid_disp of its filed position. A full
 * spill list refiles everything instead. */
static void om_move_grid_set(om_move_state *ms, uint32_t id, double x, double y) {
    uint32_t s = ms->unit_slot[id], t;
    double d;
    ms->slot_x[s] = x;
    ms->slot_y[s] = y;
    if (s >= ms->slot_base) return;
    d = fabs(x - ms->slot_fx[s]);
    if (fabs(y - ms->slot_fy[s]) > d) d = fabs(y - ms->slot_fy[s]);
    if (d <= OM_MOVE_GRID_MARGIN) {
        if (d > ms->grid_disp) ms->grid_disp = d;
        return;
    }
    if (ms->n_spill == OM_MOVE_GRID_SPILL_MAX) {
        om_move_grid_rebuild(NULL, ms, 0);
        return;
    }
    t = ms->slot_base + ms->n_spill++;
    ms->slot_x[s] = ms->slot_y[s] = 0.0 / 0.0;
    ms->slot_id[t] = id;
    ms->slot_x[t] = x;
    ms->slot_y[t] = y;
    ms->unit_slot[id] = t;
}

static double om_move_grid_x(const om_move_state *ms, uint32_t id) {
    return ms->slot_x[ms->unit_slot[id]];
}

static double om_move_grid_y(const om_move_state *ms, uint32_t id) {
    return ms->slot_y[ms->unit_slot[id]];
}

/* Mirrors a unit's x/y into the index after this module moved it. */
static void om_move_grid_update(om_move_state *ms, const om_move_unit *mu) {
    if (!ms->grid_live || !ms->grid_in[mu->unit_id]) return;
    om_move_grid_set(ms, mu->unit_id, mu->x, mu->y);
}

/* Files every living unit from its current position: from the units' x/y
 * (and their liveness), or, to file the same units again, from the index
 * itself, which mirrors every position this module moves. */
static void om_move_grid_rebuild(om_world *w, om_move_state *ms, int from_units) {
    double minx = OM_MOVE_GRID_FAR, miny = OM_MOVE_GRID_FAR, maxx = -OM_MOVE_GRID_FAR, maxy = -OM_MOVE_GRID_FAR;
    double cell = OM_MOVE_GRID_BASE_CELL, spanx, spany;
    uint32_t id, c, n = 0, cells;
    int32_t gw, gh;
    double extra = 0.0;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        int live;
        double x = 0.0, y = 0.0;
        if (from_units) {
            const om_move_unit *mu = &ms->units[id];
            live = mu->in_use && om_unit_alive(w, id);
            x = mu->x;
            y = mu->y;
        } else {
            live = ms->grid_in[id];
            if (live) {
                x = ms->slot_x[ms->unit_slot[id]];
                y = ms->slot_y[ms->unit_slot[id]];
            }
        }
        ms->grid_in[id] = (uint8_t)live;
        if (!live) continue;
        ms->scan_x[id] = x;
        ms->scan_y[id] = y;
        if (x < minx) minx = x;
        if (x > maxx) maxx = x;
        if (y < miny) miny = y;
        if (y > maxy) maxy = y;
        n++;
    }
    if (n == 0) { minx = miny = maxx = maxy = 0.0; }
    spanx = maxx - minx;
    spany = maxy - miny;
    if (!(spanx < OM_MOVE_GRID_FAR)) spanx = OM_MOVE_GRID_FAR;
    if (!(spany < OM_MOVE_GRID_FAR)) spany = OM_MOVE_GRID_FAR;
    while ((floor(spanx / cell) + 1.0) * (floor(spany / cell) + 1.0) > (double)OM_MOVE_GRID_MAX_CELLS) cell *= 2.0;
    gw = (int32_t)(floor(spanx / cell) + 1.0);
    gh = (int32_t)(floor(spany / cell) + 1.0);
    cells = (uint32_t)gw * (uint32_t)gh;
    ms->grid_ox = minx;
    ms->grid_oy = miny;
    ms->grid_cell = cell;
    ms->grid_inv = 1.0 / cell;
    ms->grid_w = gw;
    ms->grid_h = gh;
    memset(ms->grid_start, 0, (cells + 1) * sizeof(uint32_t));
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        if (!ms->grid_in[id]) continue;
        c = (uint32_t)om_move_grid_axis_cell(ms->scan_y[id], miny, ms->grid_inv, gh) * (uint32_t)gw
            + (uint32_t)om_move_grid_axis_cell(ms->scan_x[id], minx, ms->grid_inv, gw);
        ms->unit_cell[id] = c;
        ms->grid_start[c + 1]++;
    }
    for (c = 0; c < cells; c++) {
        ms->grid_start[c + 1] += ms->grid_start[c];
        ms->grid_fill[c] = ms->grid_start[c];
    }
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        uint32_t slot;
        if (!ms->grid_in[id]) continue;
        slot = ms->grid_fill[ms->unit_cell[id]]++;
        ms->unit_slot[id] = slot;
        ms->slot_id[slot] = id;
        ms->slot_x[slot] = ms->slot_fx[slot] = ms->scan_x[id];
        ms->slot_y[slot] = ms->slot_fy[slot] = ms->scan_y[id];
        ms->slot_sx[slot] = ms->start_x[id];
        ms->slot_sy[slot] = ms->start_y[id];
        if (fabs(ms->start_x[id] - ms->scan_x[id]) > extra) extra = fabs(ms->start_x[id] - ms->scan_x[id]);
        if (fabs(ms->start_y[id] - ms->scan_y[id]) > extra) extra = fabs(ms->start_y[id] - ms->scan_y[id]);
    }
    /* Compute per-cell group sentinel and flat unit_group mirror.
     * cell_group[c] starts as UINT32_MAX (homogeneous / empty).
     * First unit in c sets it to its group_id.
     * A second unit with a different group_id sets it to 0 (mixed). */
    memset(ms->cell_group, 0xFF, cells * sizeof(uint32_t));
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        uint32_t gid, cc;
        if (!ms->grid_in[id]) continue;
        gid = ms->units[id].group_id;
        ms->unit_group[id] = gid;
        cc = ms->unit_cell[id];
        if (ms->cell_group[cc] == (uint32_t)~0u) {
            ms->cell_group[cc] = gid;
        } else if (ms->cell_group[cc] != gid) {
            ms->cell_group[cc] = 0;
        }
    }

    ms->slot_base = n;
    ms->n_spill = 0;
    ms->grid_disp = 0.0;
    ms->probe_extra = extra;
    ms->grid_live = 1;
}

/* The cells that can hold a unit within r of (x, y): every unit still in a
 * cell is within grid_disp of where it was filed. The cells of one row are
 * consecutive slots. Returns 0 when there are none. */
static inline int om_move_grid_box_disp(const om_move_state *ms, double disp, double x, double y, double r, int32_t *x0, int32_t *x1, int32_t *y0, int32_t *y1) {
    double reach = r + disp + OM_MOVE_GRID_BOUND_PAD;
    int32_t xa = om_move_floor_i((x - reach - ms->grid_ox) * ms->grid_inv), xb = om_move_floor_i((x + reach - ms->grid_ox) * ms->grid_inv);
    int32_t ya = om_move_floor_i((y - reach - ms->grid_oy) * ms->grid_inv), yb = om_move_floor_i((y + reach - ms->grid_oy) * ms->grid_inv);
    if (xa >= ms->grid_w || xb < 0 || ya >= ms->grid_h || yb < 0) return 0;
    *x0 = xa > 0 ? xa : 0;
    *x1 = xb >= ms->grid_w ? ms->grid_w - 1 : xb;
    *y0 = ya > 0 ? ya : 0;
    *y1 = yb >= ms->grid_h ? ms->grid_h - 1 : yb;
    return 1;
}

static inline int om_move_grid_box(const om_move_state *ms, double x, double y, double r, int32_t *x0, int32_t *x1, int32_t *y0, int32_t *y1) {
    return om_move_grid_box_disp(ms, ms->grid_disp, x, y, r, x0, x1, y0, y1);
}

static void om_move_grid_refresh(om_world *w, om_move_state *ms) {
    if (!ms->grid_live) om_move_grid_rebuild(w, ms, 1);
}

/* Sorting networks (Batcher's odd-even merge sort) for the short candidate
 * lists a collision query yields: fixed compare-exchanges with no data-
 * dependent branch, which beat insertion sort on lists this short. */
#define OM_MOVE_CE(lo, hi) do { t = (lo) < (hi) ? (lo) : (hi); (hi) = (lo) < (hi) ? (hi) : (lo); (lo) = t; } while (0)

static void om_move_sort8(uint32_t *a) {
    const uint32_t *in = a;
    uint32_t *out = a;
    uint32_t v0 = *in++, v1 = *in++, v2 = *in++, v3 = *in++, v4 = *in++, v5 = *in++, v6 = *in++, v7 = *in++, t;
    OM_MOVE_CE(v0, v1);
    OM_MOVE_CE(v2, v3);
    OM_MOVE_CE(v4, v5);
    OM_MOVE_CE(v6, v7);
    OM_MOVE_CE(v0, v2);
    OM_MOVE_CE(v1, v3);
    OM_MOVE_CE(v4, v6);
    OM_MOVE_CE(v5, v7);
    OM_MOVE_CE(v1, v2);
    OM_MOVE_CE(v5, v6);
    OM_MOVE_CE(v0, v4);
    OM_MOVE_CE(v1, v5);
    OM_MOVE_CE(v2, v6);
    OM_MOVE_CE(v3, v7);
    OM_MOVE_CE(v2, v4);
    OM_MOVE_CE(v3, v5);
    OM_MOVE_CE(v1, v2);
    OM_MOVE_CE(v3, v4);
    OM_MOVE_CE(v5, v6);
    *out++ = v0;
    *out++ = v1;
    *out++ = v2;
    *out++ = v3;
    *out++ = v4;
    *out++ = v5;
    *out++ = v6;
    *out++ = v7;
}

static void om_move_sort16(uint32_t *a) {
    const uint32_t *in = a;
    uint32_t *out = a;
    uint32_t v0 = *in++, v1 = *in++, v2 = *in++, v3 = *in++, v4 = *in++, v5 = *in++, v6 = *in++, v7 = *in++, v8 = *in++, v9 = *in++, v10 = *in++, v11 = *in++, v12 = *in++, v13 = *in++, v14 = *in++, v15 = *in++, t;
    OM_MOVE_CE(v0, v1);
    OM_MOVE_CE(v2, v3);
    OM_MOVE_CE(v4, v5);
    OM_MOVE_CE(v6, v7);
    OM_MOVE_CE(v8, v9);
    OM_MOVE_CE(v10, v11);
    OM_MOVE_CE(v12, v13);
    OM_MOVE_CE(v14, v15);
    OM_MOVE_CE(v0, v2);
    OM_MOVE_CE(v1, v3);
    OM_MOVE_CE(v4, v6);
    OM_MOVE_CE(v5, v7);
    OM_MOVE_CE(v8, v10);
    OM_MOVE_CE(v9, v11);
    OM_MOVE_CE(v12, v14);
    OM_MOVE_CE(v13, v15);
    OM_MOVE_CE(v1, v2);
    OM_MOVE_CE(v5, v6);
    OM_MOVE_CE(v9, v10);
    OM_MOVE_CE(v13, v14);
    OM_MOVE_CE(v0, v4);
    OM_MOVE_CE(v1, v5);
    OM_MOVE_CE(v2, v6);
    OM_MOVE_CE(v3, v7);
    OM_MOVE_CE(v8, v12);
    OM_MOVE_CE(v9, v13);
    OM_MOVE_CE(v10, v14);
    OM_MOVE_CE(v11, v15);
    OM_MOVE_CE(v2, v4);
    OM_MOVE_CE(v3, v5);
    OM_MOVE_CE(v10, v12);
    OM_MOVE_CE(v11, v13);
    OM_MOVE_CE(v1, v2);
    OM_MOVE_CE(v3, v4);
    OM_MOVE_CE(v5, v6);
    OM_MOVE_CE(v9, v10);
    OM_MOVE_CE(v11, v12);
    OM_MOVE_CE(v13, v14);
    OM_MOVE_CE(v0, v8);
    OM_MOVE_CE(v1, v9);
    OM_MOVE_CE(v2, v10);
    OM_MOVE_CE(v3, v11);
    OM_MOVE_CE(v4, v12);
    OM_MOVE_CE(v5, v13);
    OM_MOVE_CE(v6, v14);
    OM_MOVE_CE(v7, v15);
    OM_MOVE_CE(v4, v8);
    OM_MOVE_CE(v5, v9);
    OM_MOVE_CE(v6, v10);
    OM_MOVE_CE(v7, v11);
    OM_MOVE_CE(v2, v4);
    OM_MOVE_CE(v3, v5);
    OM_MOVE_CE(v6, v8);
    OM_MOVE_CE(v7, v9);
    OM_MOVE_CE(v10, v12);
    OM_MOVE_CE(v11, v13);
    OM_MOVE_CE(v1, v2);
    OM_MOVE_CE(v3, v4);
    OM_MOVE_CE(v5, v6);
    OM_MOVE_CE(v7, v8);
    OM_MOVE_CE(v9, v10);
    OM_MOVE_CE(v11, v12);
    OM_MOVE_CE(v13, v14);
    *out++ = v0;
    *out++ = v1;
    *out++ = v2;
    *out++ = v3;
    *out++ = v4;
    *out++ = v5;
    *out++ = v6;
    *out++ = v7;
    *out++ = v8;
    *out++ = v9;
    *out++ = v10;
    *out++ = v11;
    *out++ = v12;
    *out++ = v13;
    *out++ = v14;
    *out++ = v15;
}

static void om_move_sift_down(uint32_t *a, uint32_t root, uint32_t n) {
    uint32_t v = a[root];
    for (;;) {
        uint32_t child = 2 * root + 1;
        if (child >= n) break;
        if (child + 1 < n && a[child + 1] > a[child]) child++;
        if (a[child] <= v) break;
        a[root] = a[child];
        root = child;
    }
    a[root] = v;
}

/* Sorts ids (unique). Up to 16 go through a network on a copy padded with
 * the largest value; more use insertion sort, then heapsort: libm_lint bans
 * qsort (its result on ties and its algorithm are the platform's). The array
 * must have room for 16 entries. */
static void om_move_sort_ids(uint32_t *a, uint32_t n) {
    uint32_t i;
    if (n < 2) return;
    if (n <= OM_MOVE_NET_SMALL) {
        for (i = n; i < OM_MOVE_NET_SMALL; i++) a[i] = 0xFFFFFFFFu;
        om_move_sort8(a);
        return;
    }
    if (n <= OM_MOVE_NET_LARGE) {
        for (i = n; i < OM_MOVE_NET_LARGE; i++) a[i] = 0xFFFFFFFFu;
        om_move_sort16(a);
        return;
    }
    if (n <= OM_MOVE_INSERTION_SORT_MAX) {
        for (i = 1; i < n; i++) {
            uint32_t v = a[i], j = i;
            while (j > 0 && a[j - 1] > v) { a[j] = a[j - 1]; j--; }
            a[j] = v;
        }
        return;
    }
    for (i = n / 2; i-- > 0;) om_move_sift_down(a, i, n);
    for (i = n - 1; i > 0; i--) {
        uint32_t t = a[0]; a[0] = a[i]; a[i] = t;
        om_move_sift_down(a, 0, i);
    }
}

/* Bit i of the result is set when slot lo + i (i < OM_MOVE_MASK_BITS, lo + i < hi) holds a
 * unit within sqrt(r2) of (x, y); a NaN slot (a free or vacated one) never
 * passes. The SSE2 path does the same IEEE double arithmetic two slots at a
 * time, so both paths agree. */
static uint64_t om_move_near_mask_at(const double *xs, const double *ys, uint32_t lo, uint32_t hi, double x, double y, double r2) {
    const double *sx = xs + lo, *sy = ys + lo;
    uint32_t count = hi - lo > OM_MOVE_MASK_BITS ? OM_MOVE_MASK_BITS : hi - lo, i = 0;
    uint64_t mask = 0;
#if defined(__SSE2__)
    const __m128d vx = _mm_set1_pd(x), vy = _mm_set1_pd(y), vr2 = _mm_set1_pd(r2);
    for (; i < count; i += 2) {
        __m128d dx = _mm_sub_pd(_mm_loadu_pd(sx + i), vx), dy = _mm_sub_pd(_mm_loadu_pd(sy + i), vy);
        mask |= (uint64_t)(uint32_t)_mm_movemask_pd(_mm_cmple_pd(_mm_add_pd(_mm_mul_pd(dx, dx), _mm_mul_pd(dy, dy)), vr2)) << i;
    }
    if (count < OM_MOVE_MASK_BITS) mask &= ((uint64_t)1 << count) - 1u;
#else
    for (; i < count; i++) {
        double dx = sx[i] - x, dy = sy[i] - y;
        mask |= (uint64_t)(dx * dx + dy * dy <= r2) << i;
    }
#endif
    return mask;
}

static uint64_t om_move_near_mask(const om_move_state *ms, uint32_t lo, uint32_t hi, double x, double y, double r2) {
    return om_move_near_mask_at(ms->slot_x, ms->slot_y, lo, hi, x, y, r2);
}

/* Index of the lowest set bit of a nonzero mask. */
static uint32_t om_move_lowest_bit(uint64_t mask) {
    uint32_t i = 0;
    while (!(mask & 1u)) { mask >>= 1; i++; }
    return i;
}

/* The scans below test slots [lo, hi) for a unit within sqrt(r2) of
 * (x, y) and append the hits from index n on, returning the new count. */
static uint32_t om_move_scan_ids(om_move_state *ms, uint32_t lo, uint32_t hi, double x, double y, double r2, uint32_t min_id, uint32_t n) {
    uint32_t base;
    for (base = lo; base < hi; base += OM_MOVE_MASK_BITS) {
        uint64_t mask = om_move_near_mask(ms, base, hi, x, y, r2);
        while (mask) {
            uint32_t id = ms->slot_id[base + om_move_lowest_bit(mask)];
            mask &= mask - 1;
            ms->grid_scratch[n] = id;
            n += (uint32_t)(id > min_id);
        }
    }
    return n;
}


/* Ids above min_id whose unit lies within r of (x, y), ascending, into
 * ms->grid_scratch; returns the count. The cells of one grid row are
 * consecutive, so a row of the query's cell range is one run of slots. */
static uint32_t om_move_grid_collect(om_world *w, om_move_state *ms, double x, double y, double r, uint32_t min_id) {
    const double r2 = r * r;
    int32_t cx0, cx1, cy0, cy1, cy;
    uint32_t n;
    om_move_grid_refresh(w, ms);
    n = om_move_scan_ids(ms, ms->slot_base, ms->slot_base + ms->n_spill, x, y, r2, min_id, 0);
    if (om_move_grid_box(ms, x, y, r, &cx0, &cx1, &cy0, &cy1)) {
        for (cy = cy0; cy <= cy1; cy++) {
            uint32_t row = (uint32_t)cy * (uint32_t)ms->grid_w;
            n = om_move_scan_ids(ms, ms->grid_start[row + (uint32_t)cx0], ms->grid_start[row + (uint32_t)cx1 + 1], x, y, r2, min_id, n);
        }
    }
    om_move_sort_ids(ms->grid_scratch, n);
    return n;
}

/* Whether any unit above min_id lies within r of (x, y). */
static int om_move_grid_any_above(om_world *w, om_move_state *ms, double x, double y, double r, uint32_t min_id) {
    const double r2 = r * r;
    int32_t cx0, cx1, cy0, cy1, cy;
    uint32_t i, base, lo, hi;
    om_move_grid_refresh(w, ms);
    for (i = ms->slot_base; i < ms->slot_base + ms->n_spill; i++) {
        double dx = ms->slot_x[i] - x, dy = ms->slot_y[i] - y;
        if (ms->slot_id[i] > min_id && dx * dx + dy * dy <= r2) return 1;
    }
    if (!om_move_grid_box(ms, x, y, r, &cx0, &cx1, &cy0, &cy1)) return 0;
    for (cy = cy0; cy <= cy1; cy++) {
        uint32_t row = (uint32_t)cy * (uint32_t)ms->grid_w;
        lo = ms->grid_start[row + (uint32_t)cx0];
        hi = ms->grid_start[row + (uint32_t)cx1 + 1];
        for (base = lo; base < hi; base += OM_MOVE_MASK_BITS) {
            uint64_t mask = om_move_near_mask(ms, base, hi, x, y, r2);
            while (mask) {
                if (ms->slot_id[base + om_move_lowest_bit(mask)] > min_id) return 1;
                mask &= mask - 1;
            }
        }
    }
    return 0;
}


static int32_t om_move_layer(const om_world *w, uint32_t id) {
    int32_t l = om_unit_get_layer(w, id);
    return l < 0 ? 0 : l;
}

static om_move_unit *om_move_touch(om_world *w, om_move_state *ms, uint32_t unit_id) {
    om_move_unit *mu = om_move_get(ms, unit_id);
    uint32_t f;
    if (!mu) return NULL;
    if (!mu->in_use) {
        mu->in_use = 1;
        mu->unit_id = unit_id;
        mu->x = om_unit_position_x(w, unit_id);
        mu->y = om_unit_position_y(w, unit_id);
        mu->facing = 0.0;
        mu->pushed_x = mu->x;
        mu->pushed_y = mu->y;
        mu->prev_x = mu->x;
        mu->prev_y = mu->y;
        mu->prev_facing = 0.0;
        mu->has_dest = 0;
        mu->dest_x = 0.0;
        mu->dest_y = 0.0;
        mu->direct_move = 0;
        mu->group_id = 0;
        mu->speed_cap = 0.0;
        mu->engaged = 0;
        mu->kiting = 0;
        mu->kite_target = 0;
        mu->order_kind = -1;
        mu->native_speed = om_unit_effective_speed(w, unit_id);
        mu->routed = 0;
        mu->deflecting = 0;
        mu->deflect_heading = 0.0;
        mu->deflect_origin_x = mu->x;
        mu->deflect_origin_y = mu->y;
        mu->waiting = 0;
        mu->plan_layer = 0;
        mu->route_n = 0;
        mu->route_i = 0;
        mu->route_ends_at_goal = 0;
        for (f = 0; f < OM_MAX_FACTIONS; f++) mu->visible[f] = 1;
        if (unit_id > ms->discovery_max) ms->discovery_max = unit_id;
        if (ms->grid_live && om_unit_alive(w, unit_id)) ms->grid_live = 0;
    }
    return mu;
}

static void om_move_discover(om_world *w, om_move_state *ms) {
    uint32_t id, last = om_unit_count(w); /* rows are never freed, so the count is the highest id */
    if (last >= OM_MOVE_MAX_UNITS) last = OM_MOVE_MAX_UNITS - 1;
    for (id = 1; id <= last; id++) {
        if (om_unit_alive(w, id)) {
            om_move_touch(w, ms, id);
        }
    }
}

static int om_move_is_stationary(const om_move_unit *mu) {
    if (mu->engaged) return 1;
    if (mu->kiting) return 0;
    if (!mu->has_dest) return 1;
    return 0;
}

/* Takes a slot and n member entries; when either table is full, finished
 * groups are dropped first (nothing reads a finished group but
 * om_group_is_active, which reports a dropped one as not active). NULL when
 * still full: the order is refused. */
static om_move_group *om_move_group_alloc(om_move_state *ms, uint32_t n) {
    om_move_group *grp;
    if (n > OM_MOVE_MAX_GROUP_MEMBERS) return NULL;
    if (ms->n_groups >= OM_MOVE_MAX_GROUPS || ms->n_group_members + n > OM_MOVE_MAX_GROUP_MEMBERS) {
        uint32_t g, kept = 0, used = 0;
        for (g = 0; g < ms->n_groups; g++) {
            om_move_group *src = &ms->groups[g];
            if (!src->active) continue;
            memmove(&ms->group_members[used], &ms->group_members[src->first_member], src->n_members * sizeof(uint32_t));
            ms->groups[kept] = *src;
            ms->groups[kept].first_member = used;
            used += src->n_members;
            kept++;
        }
        ms->n_groups = kept;
        ms->n_group_members = used;
        if (ms->n_groups >= OM_MOVE_MAX_GROUPS || ms->n_group_members + n > OM_MOVE_MAX_GROUP_MEMBERS) return NULL;
    }
    grp = &ms->groups[ms->n_groups++];
    grp->first_member = ms->n_group_members;
    ms->n_group_members += n;
    return grp;
}

static om_move_group *om_move_group_find(om_move_state *ms, uint32_t id) {
    uint32_t i;
    for (i = 0; i < ms->n_groups; i++) {
        if (ms->groups[i].id == id) return &ms->groups[i];
    }
    return NULL;
}

/* ------------------------------------------------------------- navmesh */

static int32_t om_move_cells_for(double extent) {
    int32_t n = (int32_t)(extent / OM_NAVMESH_CELL_SIZE);
    return (double)n * OM_NAVMESH_CELL_SIZE < extent ? n + 1 : n;
}

/* A cell of the density grid, or -1 when it lies outside the grid: the canvas when one is set, else the
 * largest canvas (A134: refused cleanly, nothing stored). */
static long om_move_density_index(const om_move_state *ms, int32_t cx, int32_t cy, uint32_t layer) {
    int32_t nx = OM_MOVE_DENSITY_SIDE, ny = OM_MOVE_DENSITY_SIDE;
    if (ms->canvas_w > 0.0 && ms->canvas_h > 0.0) {
        nx = om_move_cells_for(ms->canvas_w);
        ny = om_move_cells_for(ms->canvas_h);
    }
    if (layer >= OM_LAYER_COUNT || cx < 0 || cy < 0 || cx >= nx || cy >= ny) return -1;
    return ((long)layer * OM_MOVE_DENSITY_SIDE + cy) * OM_MOVE_DENSITY_SIDE + cx;
}

static double om_move_density_cell_get(om_move_state *ms, int32_t cx, int32_t cy, uint32_t layer) {
    long i = om_move_density_index(ms, cx, cy, layer);
    return (i < 0 || !ms->density) ? 0.0 : ms->density[i];
}

/* The route grid as movement reads it: a cell is blocked on a layer when the mapgen grid says so (om_map_block_rect,
 * the canvas edge) or its density is above the threshold (R-097-01). */
static int om_move_cell_blocked(const om_world *w, om_move_state *ms, uint32_t layer, int32_t cx, int32_t cy) {
    return om_mapgen_cell_blocked(w, layer, cx, cy) || om_move_density_cell_get(ms, cx, cy, layer) > OM_NAVMESH_OBSTACLE_THRESHOLD;
}

/* Terrain stage 2 (R-001-07): a walker's cell test reads the terrain's walk mask of its layer in place; with no
 * terrain generated it falls back to the mapgen grid, as om_walk_route treats the canvas as open. */
static int om_move_walk_blocked(const om_world *w, uint32_t layer, int32_t cx, int32_t cy) {
    const om_terrain_state *st = (const om_terrain_state *)w->terrain_state;
    if (!st || !st->present) return om_mapgen_cell_blocked(w, layer, cx, cy);
    if (layer >= OM_TERRAIN_BANDS || !st->walk[layer] || cx < 0 || cy < 0 || cx >= (int32_t)st->cells_w || cy >= (int32_t)st->cells_h) return 1;
    return !st->walk[layer][(size_t)cy * st->cells_w + (size_t)cx];
}

static int om_move_is_walker(const om_world *w, uint32_t id) {
    int t = om_unit_get_unit_type(w, id);
    return t >= 0 && om_unit_profile_movement_kind(w, t) == OM_MOVE_WALKING;
}

static int om_move_cell_blocked_for(const om_world *w, om_move_state *ms, int walk, uint32_t layer, int32_t cx, int32_t cy) {
    return walk ? om_move_walk_blocked(w, layer, cx, cy) : om_move_cell_blocked(w, ms, layer, cx, cy);
}

static double om_move_density_at_pos(om_move_state *ms, double x, double y, uint32_t layer) {
    int32_t cx = (int32_t)floor(x / OM_NAVMESH_CELL_SIZE);
    int32_t cy = (int32_t)floor(y / OM_NAVMESH_CELL_SIZE);
    return om_move_density_cell_get(ms, cx, cy, layer);
}

/* Formation slot walkability: this module's own density cells plus the
 * obstacle discs tactical_mapgen.c records (om_map_add_obstacle), read back
 * through its public sampler. */
static int om_move_slot_blocked(om_world *w, om_move_state *ms, double x, double y) {
    if (om_move_density_at_pos(ms, x, y, 0) > OM_NAVMESH_OBSTACLE_THRESHOLD) return 1;
    return om_map_sample_obstacle_density(w, x, y) > OM_NAVMESH_OBSTACLE_THRESHOLD;
}

static void om_move_route_touch(om_move_state *ms, uint32_t layer, double dest_x, double dest_y) {
    int32_t cx = (int32_t)floor(dest_x / OM_NAVMESH_CELL_SIZE);
    int32_t cy = (int32_t)floor(dest_y / OM_NAVMESH_CELL_SIZE);
    uint32_t i;
    for (i = 0; i < ms->n_route_cache; i++) {
        om_move_route_entry *r = &ms->route_cache[i];
        if (r->in_use && r->layer == layer && r->cx == cx && r->cy == cy) {
            ms->cache_hits++;
            return;
        }
    }
    {
        om_move_route_entry *r;
        if (ms->n_route_cache < OM_MOVE_MAX_ROUTE_CACHE) {
            r = &ms->route_cache[ms->n_route_cache++];
        } else {
            r = &ms->route_cache[ms->route_evict];
            ms->route_evict = (ms->route_evict + 1) % OM_MOVE_MAX_ROUTE_CACHE;
        }
        r->in_use = 1;
        r->layer = layer;
        r->cx = cx;
        r->cy = cy;
    }
}

/* Cells per axis of the search window: the canvas when set, else the largest canvas. */
static void om_move_window(const om_move_state *ms, int32_t *nx, int32_t *ny) {
    *nx = OM_MOVE_DENSITY_SIDE;
    *ny = OM_MOVE_DENSITY_SIDE;
    if (ms->canvas_w > 0.0 && ms->canvas_h > 0.0) {
        *nx = om_move_cells_for(ms->canvas_w);
        *ny = om_move_cells_for(ms->canvas_h);
    }
}

/* The route-grid cell a position is in; a position on the canvas edge belongs to the last cell. */
static void om_move_cell_at(const om_move_state *ms, double x, double y, int32_t *cx, int32_t *cy) {
    int32_t nx, ny;
    *cx = (int32_t)floor(x / OM_NAVMESH_CELL_SIZE);
    *cy = (int32_t)floor(y / OM_NAVMESH_CELL_SIZE);
    if (!(ms->canvas_w > 0.0 && ms->canvas_h > 0.0)) return;
    om_move_window(ms, &nx, &ny);
    if (*cx >= nx && x <= ms->canvas_w) *cx = nx - 1;
    if (*cy >= ny && y <= ms->canvas_h) *cy = ny - 1;
}

/* Exact grid walk (Amanatides and Woo) from (x0, y0) to (x1, y1) through the 100 wu cells: 1 when no cell it
 * touches is blocked on the layer. A line through a cell corner needs both side cells open. */
static int om_move_los_clear(const om_world *w, om_move_state *ms, double x0, double y0, double x1, double y1, uint32_t layer) {
    const double inf = OM_MOVE_GRID_FAR;
    int32_t cx, cy, ex, ey;
    const double dx = x1 - x0, dy = y1 - y0;
    const int32_t sx = dx > 0.0 ? 1 : -1, sy = dy > 0.0 ? 1 : -1;
    double tx, ty;
    const double ddx = dx != 0.0 ? (double)sx * OM_NAVMESH_CELL_SIZE / dx : inf;
    const double ddy = dy != 0.0 ? (double)sy * OM_NAVMESH_CELL_SIZE / dy : inf;
    int32_t left;
    om_move_cell_at(ms, x0, y0, &cx, &cy);
    om_move_cell_at(ms, x1, y1, &ex, &ey);
    tx = dx != 0.0 ? ((double)(sx > 0 ? cx + 1 : cx) * OM_NAVMESH_CELL_SIZE - x0) / dx : inf;
    ty = dy != 0.0 ? ((double)(sy > 0 ? cy + 1 : cy) * OM_NAVMESH_CELL_SIZE - y0) / dy : inf;
    left = (ex > cx ? ex - cx : cx - ex) + (ey > cy ? ey - cy : cy - ey) + 1;
    for (;;) {
        if (om_move_cell_blocked(w, ms, layer, cx, cy)) return 0;
        if ((cx == ex && cy == ey) || left-- <= 0) return 1;
        if (tx < ty) { cx += sx; tx += ddx; }
        else if (ty < tx) { cy += sy; ty += ddy; }
        else {
            if (om_move_cell_blocked(w, ms, layer, cx + sx, cy) || om_move_cell_blocked(w, ms, layer, cx, cy + sy)) return 0;
            cx += sx; cy += sy; tx += ddx; ty += ddy;
        }
    }
}

/* Breadth-first fill from one cell over open cells (4 neighbours, +x -x +y -y), O(cells), ties settled by the
 * fixed neighbour order: dist[y * nx + x] = steps + 1, OM_MOVE_FIELD_UNREACHED elsewhere. With a stop cell
 * (inside the window) the fill ends once that cell is reached: a one-off query, not a field to keep. */
static void om_move_bfs_fill(const om_world *w, om_move_state *ms, uint32_t layer, int32_t scx, int32_t scy, int32_t stop_cx, int32_t stop_cy, uint32_t *dist) {
    static const int32_t OM_BFS_DX[OM_MOVE_BFS_DIR_COUNT] = {1, -1, 0, 0};
    static const int32_t OM_BFS_DY[OM_MOVE_BFS_DIR_COUNT] = {0, 0, 1, -1};
    int32_t nx, ny;
    uint32_t head = 0, tail = 0, i;
    om_move_window(ms, &nx, &ny);
    for (i = 0; i < (uint32_t)(nx * ny); i++) dist[i] = OM_MOVE_FIELD_UNREACHED;
    if (scx < 0 || scy < 0 || scx >= nx || scy >= ny || om_move_cell_blocked(w, ms, layer, scx, scy)) return;
    dist[scy * nx + scx] = 1;
    ms->bfs_queue[tail++] = (uint32_t)(scy * nx + scx);
    while (head < tail) {
        uint32_t c = ms->bfs_queue[head++];
        int32_t cx = (int32_t)(c % (uint32_t)nx), cy = (int32_t)(c / (uint32_t)nx);
        int dir;
        for (dir = 0; dir < OM_MOVE_BFS_DIR_COUNT; dir++) {
            int32_t x = cx + OM_BFS_DX[dir], y = cy + OM_BFS_DY[dir];
            if (x < 0 || y < 0 || x >= nx || y >= ny || dist[y * nx + x] != OM_MOVE_FIELD_UNREACHED) continue;
            if (om_move_cell_blocked(w, ms, layer, x, y)) continue;
            dist[y * nx + x] = dist[c] + 1;
            ms->bfs_queue[tail++] = (uint32_t)(y * nx + x);
            if (x == stop_cx && y == stop_cy) return;
        }
    }
}

static int om_move_bfs_ready(om_move_state *ms) {
    const size_t n = (size_t)OM_MOVE_DENSITY_SIDE * OM_MOVE_DENSITY_SIDE;
    if (!ms->bfs_queue) ms->bfs_queue = (uint32_t *)malloc(n * sizeof(uint32_t));
    if (!ms->bfs_scratch) ms->bfs_scratch = (uint32_t *)malloc(n * sizeof(uint32_t));
    return ms->bfs_queue && ms->bfs_scratch;
}

static om_move_field *om_move_field_kept(om_move_state *ms, uint32_t layer, int32_t cx, int32_t cy) {
    uint32_t k;
    for (k = 0; k < OM_MOVE_FIELD_POOL; k++) {
        om_move_field *f = &ms->fields[k];
        if (f->in_use && f->layer == layer && f->cx == cx && f->cy == cy && f->epoch == ms->terrain_epoch) return f;
    }
    return NULL;
}

/* The distance field to a destination cell, from the pool of recent destinations (R-097-02: computed once for
 * a shared destination); NULL when the destination cell is blocked or outside the window. A cell that turns
 * blocked or open bumps terrain_epoch, which makes every kept field stale (R-207-03). */
static const uint32_t *om_move_field_for(const om_world *w, om_move_state *ms, uint32_t layer, int32_t cx, int32_t cy) {
    int32_t nx, ny;
    om_move_field *f;
    om_move_window(ms, &nx, &ny);
    if (cx < 0 || cy < 0 || cx >= nx || cy >= ny || om_move_cell_blocked(w, ms, layer, cx, cy)) return NULL;
    if ((f = om_move_field_kept(ms, layer, cx, cy)) != NULL) return f->dist;
    if (!om_move_bfs_ready(ms)) return NULL;
    f = &ms->fields[ms->field_next];
    ms->field_next = (ms->field_next + 1) % OM_MOVE_FIELD_POOL;
    if (!f->dist) f->dist = (uint32_t *)malloc((size_t)OM_MOVE_DENSITY_SIDE * OM_MOVE_DENSITY_SIDE * sizeof(uint32_t));
    if (!f->dist) { f->in_use = 0; return NULL; }
    om_move_bfs_fill(w, ms, layer, cx, cy, -1, -1, f->dist);
    f->in_use = 1;
    f->layer = layer;
    f->cx = cx;
    f->cy = cy;
    f->epoch = ms->terrain_epoch;
    return f->dist;
}

/* No route to (dx, dy): the nearest point to it that can be reached from (sx, sy), as a point at least a
 * collision radius inside its cell. Ties go to the lower cell id. Returns 0 when the start is not on an open cell. */
static int om_move_nearest_reachable(const om_world *w, om_move_state *ms, uint32_t layer, double sx, double sy, double dx, double dy, double *ox, double *oy) {
    int32_t nx, ny, c, scx = (int32_t)floor(sx / OM_NAVMESH_CELL_SIZE), scy = (int32_t)floor(sy / OM_NAVMESH_CELL_SIZE);
    double best = OM_MOVE_GRID_FAR;
    int32_t best_c = -1;
    om_move_window(ms, &nx, &ny);
    if (!om_move_bfs_ready(ms)) return 0;
    om_move_bfs_fill(w, ms, layer, scx, scy, -1, -1, ms->bfs_scratch);
    for (c = 0; c < nx * ny; c++) {
        double x0, y0, qx, qy, d2;
        if (ms->bfs_scratch[c] == OM_MOVE_FIELD_UNREACHED) continue;
        x0 = (double)(c % nx) * OM_NAVMESH_CELL_SIZE;
        y0 = (double)(c / nx) * OM_NAVMESH_CELL_SIZE;
        qx = dx < x0 ? x0 : (dx > x0 + OM_NAVMESH_CELL_SIZE ? x0 + OM_NAVMESH_CELL_SIZE : dx);
        qy = dy < y0 ? y0 : (dy > y0 + OM_NAVMESH_CELL_SIZE ? y0 + OM_NAVMESH_CELL_SIZE : dy);
        d2 = (qx - dx) * (qx - dx) + (qy - dy) * (qy - dy);
        if (d2 < best) { best = d2; best_c = c; }
    }
    if (best_c < 0) return 0;
    {
        double x0 = (double)(best_c % nx) * OM_NAVMESH_CELL_SIZE + ms->radius;
        double y0 = (double)(best_c / nx) * OM_NAVMESH_CELL_SIZE + ms->radius;
        double x1 = x0 + OM_NAVMESH_CELL_SIZE - 2.0 * ms->radius, y1 = y0 + OM_NAVMESH_CELL_SIZE - 2.0 * ms->radius;
        *ox = dx < x0 ? x0 : (dx > x1 ? x1 : dx);
        *oy = dy < y0 ? y0 : (dy > y1 ? y1 : dy);
    }
    return 1;
}

/* Cells the route from (x0, y0) to a destination takes, counting both ends: 2 when the straight line is clear
 * (straightened), 1 when there is no route (also when either end is off the grid). A kept field answers if there is one. last_path_straightened records the first. */
static uint32_t om_move_route_len(const om_world *w, om_move_state *ms, uint32_t layer, double x0, double y0, double x1, double y1, int *straight) {
    int32_t nx, ny, scx, scy, dcx, dcy;
    const om_move_field *kept;
    const uint32_t *f;
    om_move_cell_at(ms, x0, y0, &scx, &scy);
    om_move_cell_at(ms, x1, y1, &dcx, &dcy);
    *straight = om_move_los_clear(w, ms, x0, y0, x1, y1, layer);
    if (*straight) return 2;
    om_move_window(ms, &nx, &ny);
    if (scx < 0 || scy < 0 || scx >= nx || scy >= ny || dcx < 0 || dcy < 0 || dcx >= nx || dcy >= ny) return 1;
    kept = om_move_field_kept(ms, layer, dcx, dcy);
    if (kept) f = kept->dist;
    else {
        if (!om_move_bfs_ready(ms)) return 1;
        om_move_bfs_fill(w, ms, layer, dcx, dcy, scx, scy, ms->bfs_scratch);
        f = ms->bfs_scratch;
    }
    return f[scy * nx + scx] == OM_MOVE_FIELD_UNREACHED ? 1 : f[scy * nx + scx];
}

/* One unit's route (R-097-01, R-097-02): sets aim to the next waypoint toward the destination: the farthest
 * cell centre on the shortest grid path that is still in line of sight, or the destination itself when it is.
 * A destination with no route is replaced by the nearest point that can be reached.
 * See also: om_move_steer_step, which follows the aim. */
static void om_move_route_plan(const om_world *w, om_move_state *ms, om_move_unit *mu, uint32_t layer) {
    int32_t nx, ny, cx, cy, dcx, dcy;
    double tx = om_move_clamp_axis(mu->dest_x, ms->canvas_w), ty = om_move_clamp_axis(mu->dest_y, ms->canvas_h);
    const uint32_t *f;
    om_move_window(ms, &nx, &ny);
    om_move_cell_at(ms, mu->x, mu->y, &cx, &cy);
    om_move_cell_at(ms, tx, ty, &dcx, &dcy);
    if (!mu->plan_valid || mu->plan_dest_x != mu->dest_x || mu->plan_dest_y != mu->dest_y) mu->routed = 0;
    mu->plan_valid = 1;
    mu->plan_epoch = ms->terrain_epoch;
    mu->plan_layer = (uint32_t)om_move_layer(w, mu->unit_id);
    mu->aim_is_waypoint = 0;
    mu->aim_x = tx;
    mu->aim_y = ty;
    if (cx < 0 || cy < 0 || cx >= nx || cy >= ny || om_move_los_clear(w, ms, mu->x, mu->y, tx, ty, layer)) goto done;
    f = om_move_field_for(w, ms, layer, dcx, dcy);
    if (!f || f[cy * nx + cx] == OM_MOVE_FIELD_UNREACHED) {
        double px, py;
        if (!om_move_nearest_reachable(w, ms, layer, mu->x, mu->y, tx, ty, &px, &py)) goto done;
        mu->dest_x = mu->aim_x = tx = px;
        mu->dest_y = mu->aim_y = ty = py;
        if (om_move_los_clear(w, ms, mu->x, mu->y, px, py, layer)) goto done;
        om_move_cell_at(ms, px, py, &dcx, &dcy);
        f = om_move_field_for(w, ms, layer, dcx, dcy);
        if (!f || f[cy * nx + cx] == OM_MOVE_FIELD_UNREACHED) goto done;
    }
    {
        static const int32_t OM_BFS_DX[OM_MOVE_BFS_DIR_COUNT] = {1, -1, 0, 0};
        static const int32_t OM_BFS_DY[OM_MOVE_BFS_DIR_COUNT] = {0, 0, 1, -1};
        int seen_all = 1;
        while (f[cy * nx + cx] > 1) {
            int dir;
            int32_t bx = cx, by = cy;
            for (dir = 0; dir < OM_MOVE_BFS_DIR_COUNT; dir++) {
                int32_t x = cx + OM_BFS_DX[dir], y = cy + OM_BFS_DY[dir];
                if (x < 0 || y < 0 || x >= nx || y >= ny || f[y * nx + x] != f[cy * nx + cx] - 1) continue;
                bx = x;
                by = y;
                break;
            }
            if (bx == cx && by == cy) { seen_all = 0; break; }
            cx = bx;
            cy = by;
            if (!om_move_los_clear(w, ms, mu->x, mu->y, ((double)cx + 0.5) * OM_NAVMESH_CELL_SIZE, ((double)cy + 0.5) * OM_NAVMESH_CELL_SIZE, layer)) { seen_all = 0; break; }
            mu->aim_x = ((double)cx + 0.5) * OM_NAVMESH_CELL_SIZE;
            mu->aim_y = ((double)cy + 0.5) * OM_NAVMESH_CELL_SIZE;
            mu->aim_is_waypoint = 1;
            mu->routed = 1;
        }
        if (seen_all && mu->aim_is_waypoint) {
            mu->aim_x = tx;
            mu->aim_y = ty;
            mu->aim_is_waypoint = 0;
        }
    }
done:
    mu->plan_dest_x = mu->dest_x;
    mu->plan_dest_y = mu->dest_y;
}

/* ------------------------------------------------------------ collision */

/* The steering probe of R-097-03 for one unit: probe_clear asks whether
 * (cand_x, cand_y) is at least the two collision radii from every other unit,
 * against the units gathered around the probing unit. Every probe point is
 * OM_STEERING_PROBE_DIST (om_sin/om_cos are off by under 5e-4 each, so
 * under 40.1) from that unit, so its blockers all lie within the gather
 * radius. */
/* Same-group mates (self_group nonzero, candidate group_id == self_group) are
 * not blockers for a group-move probe: the ALG-68 collision pass separates
 * them after the tick. All other units (different group, group 0, stationary)
 * still block. */
static uint32_t om_move_probe_gather(om_world *w, om_move_state *ms, uint32_t self_id, uint32_t self_group, double x, double y) {
    const double r = OM_MOVE_PROBE_REACH + 2.0 * ms->radius;
    const double r2 = r * r;
    int32_t cx0, cx1, cy0, cy1, cy;
    uint32_t n = 0, base;
    om_move_grid_refresh(w, ms);
    for (base = ms->slot_base; base < ms->slot_base + ms->n_spill; base += OM_MOVE_MASK_BITS) {
        uint32_t hi2 = ms->slot_base + ms->n_spill;
        uint64_t mask = om_move_near_mask(ms, base, hi2, x, y, r2);
        while (mask) {
            uint32_t slot = base + om_move_lowest_bit(mask);
            uint32_t cid = ms->slot_id[slot];
            mask &= mask - 1;
            if (cid == self_id) continue;
            if (self_group != 0 && ms->units[cid].group_id == self_group) continue;
            ms->scan_x[n] = ms->slot_x[slot];
            ms->scan_y[n] = ms->slot_y[slot];
            n++;
        }
    }
    if (om_move_grid_box(ms, x, y, r, &cx0, &cx1, &cy0, &cy1)) {
        for (cy = cy0; cy <= cy1; cy++) {
            uint32_t row = (uint32_t)cy * (uint32_t)ms->grid_w;
            int32_t cx;
            for (cx = cx0; cx <= cx1; cx++) {
                uint32_t ci = row + (uint32_t)cx;
                uint32_t lo, hi;
                /* Skip cells where every unit is in the same group as self:
                 * all would be filtered by the per-unit check below.
                 * cell_group[ci] == UINT32_MAX means empty or first-unit not
                 * yet encountered (cannot happen post-rebuild), so the guard
                 * self_group != 0 prevents a false skip for ungrouped probes. */
                if (self_group != 0 && ms->cell_group[ci] == self_group) continue;
                lo = ms->grid_start[ci];
                hi = ms->grid_start[ci + 1];
                for (base = lo; base < hi; base += OM_MOVE_MASK_BITS) {
                    uint64_t mask = om_move_near_mask(ms, base, hi, x, y, r2);
                    while (mask) {
                        uint32_t slot = base + om_move_lowest_bit(mask);
                        uint32_t cid = ms->slot_id[slot];
                        mask &= mask - 1;
                        if (cid == self_id) continue;
                        if (self_group != 0 && ms->unit_group[cid] == self_group) continue;
                        ms->scan_x[n] = ms->slot_x[slot];
                        ms->scan_y[n] = ms->slot_y[slot];
                        n++;
                    }
                }
            }
        }
    }
    return n;
}

/* Whether any gathered unit is closer than sqrt(limit2) to (cand_x, cand_y).
 * Neighbouring probe points share blockers, so the last few blockers found
 * (hints, indexes into the gathered list) are tried first; whether any unit
 * blocks does not depend on the order they are tried in. */
static int om_move_probe_blocked(const om_move_state *ms, uint32_t n_near, uint32_t *hints, double cand_x, double cand_y, double limit2) {
    uint32_t i, h;
    if (n_near == 0) return 0;
    for (h = 0; h < OM_MOVE_PROBE_HINTS; h++) {
        double dx = ms->scan_x[hints[h]] - cand_x, dy = ms->scan_y[hints[h]] - cand_y;
        if (dx * dx + dy * dy < limit2) return 1;
    }
    for (i = 0; i < n_near; i++) {
        double dx = ms->scan_x[i] - cand_x, dy = ms->scan_y[i] - cand_y;
        if (dx * dx + dy * dy < limit2) {
            for (h = OM_MOVE_PROBE_HINTS - 1; h > 0; h--) hints[h] = hints[h - 1];
            hints[0] = i;
            return 1;
        }
    }
    return 0;
}

/* sqrt(d2) < block_r exactly when d2 < block_r^2 (sqrt is correctly rounded
 * and rounds the predecessor of block_r^2 below block_r), so this is the
 * sqrt compare of R-097-03 without the sqrt. */
static int om_move_probe_clear(const om_move_state *ms, uint32_t n_near, uint32_t *hints, double cand_x, double cand_y) {
    return !om_move_probe_blocked(ms, n_near, hints, cand_x, cand_y, (2.0 * ms->radius) * (2.0 * ms->radius));
}

/* A probe point computed with om_sin/om_cos is within 0.05 of the same point
 * computed with om_move_sincos_approx (om_sin is off by under 4.6e-4 and the
 * approximation by under 2.3e-5 per component, times the 40 wu probe
 * distance, times sqrt(2)), so a unit closer to the approximate point than
 * the collision diameter less OM_MOVE_PROBE_SURE_MARGIN is closer than the
 * diameter to the real one: the probe is blocked without evaluating
 * om_sin/om_cos for it. */
static int om_move_probe_sure_blocked(const om_move_state *ms, uint32_t n_near, uint32_t *hints, double cand_x, double cand_y) {
    const double sure = 2.0 * ms->radius > OM_MOVE_PROBE_SURE_MARGIN ? 2.0 * ms->radius - OM_MOVE_PROBE_SURE_MARGIN : 0.0;
    return om_move_probe_blocked(ms, n_near, hints, cand_x, cand_y, sure * sure);
}

/* PP-move (ROUTE_AROUND_TERRAIN): a push that would end in a blocked cell of the unit's layer, or in an obstacle
 * disc, slides along one axis, else reverts (Python _resolve_collisions, R-099-04). */
static int om_move_slide_blocked(om_world *w, om_move_state *ms, int walk, uint32_t layer, double x, double y) {
    return om_move_cell_blocked_for(w, ms, walk, layer, (int32_t)floor(x / OM_NAVMESH_CELL_SIZE), (int32_t)floor(y / OM_NAVMESH_CELL_SIZE))
        || om_map_sample_obstacle_density(w, x, y) > OM_NAVMESH_OBSTACLE_THRESHOLD;
}

static void om_move_slide(om_world *w, om_move_state *ms, int walk, uint32_t layer, double ox, double oy, double *nx, double *ny) {
    if ((*nx == ox && *ny == oy) || !om_move_slide_blocked(w, ms, walk, layer, *nx, *ny)) return;
    if (!om_move_slide_blocked(w, ms, walk, layer, *nx, oy)) *ny = oy;
    else if (!om_move_slide_blocked(w, ms, walk, layer, ox, *ny)) *nx = ox;
    else { *nx = ox; *ny = oy; }
}

/* One colliding pair, a's id below b's; returns 1 when a position was
 * written. d2 >= target^2 implies sqrt(d2) >= target (sqrt is monotonic and
 * exact at target^2), so that early return matches the sqrt compare. */
static int om_move_collide_pair(om_world *w, om_move_state *ms, uint32_t ia, uint32_t ib) {
    double dx, dy, dist, target, overlap, ux, uy;
    double ax = om_move_grid_x(ms, ia), ay = om_move_grid_y(ms, ia);
    double bx = om_move_grid_x(ms, ib), by = om_move_grid_y(ms, ib);
    const double oax = ax, oay = ay, obx = bx, oby = by;
    int changed = 0, routed = 0;
    if (ms->col_pursue && ms->start_layer[ia] != ms->start_layer[ib]) return 0;
    dx = bx - ax; dy = by - ay;
    target = 2.0 * ms->radius;
    if (dx * dx + dy * dy >= target * target) return 0;
    dist = sqrt(dx * dx + dy * dy);
    if (dist >= target) return 0;
    if (dist < OM_COLLISION_EXACT_EPS) {
        /* R-097-07: exact overlap -- the lower unit id (a, since
         * a's id < b's always here) moves in the canonical +x
         * direction, the higher id the opposite way. */
        double half = target / 2.0;
        ax = om_move_clamp_axis(ax + half, ms->col_pursue ? ms->canvas_w : 0.0);
        bx = om_move_clamp_axis(bx - half, ms->col_pursue ? ms->canvas_w : 0.0);
        changed = 1;
    } else {
        int a_stat = ms->stat[ia];
        int b_stat = ms->stat[ib];
        overlap = target - dist;
        ux = dx / dist; uy = dy / dist;
        if (a_stat && b_stat && !ms->col_pursue) {
            /* PP baseline only (switch = 0); deleted with the two movement switches at the end of Phase E (A140)
             * Both fixed: neither takes a push. Under PURSUE_BY_STEERING two stationary units split it (R-097-10). */
            return 0;
        } else if (a_stat && !b_stat) {
            bx += ux * overlap; by += uy * overlap;
            changed = 1;
        } else if (b_stat && !a_stat) {
            ax -= ux * overlap; ay -= uy * overlap;
            changed = 1;
        } else {
            ax -= ux * overlap * 0.5; ay -= uy * overlap * 0.5;
            bx += ux * overlap * 0.5; by += uy * overlap * 0.5;
            changed = 1;
        }
        if (ms->col_pursue) {
            ax = om_move_clamp_axis(ax, ms->canvas_w); ay = om_move_clamp_axis(ay, ms->canvas_h);
            bx = om_move_clamp_axis(bx, ms->canvas_w); by = om_move_clamp_axis(by, ms->canvas_h);
        }
        if (ms->col_route && !ms->col_open) {
            om_move_slide(w, ms, om_move_is_walker(w, ia), (uint32_t)om_move_layer(w, ia), oax, oay, &ax, &ay);
            om_move_slide(w, ms, om_move_is_walker(w, ib), (uint32_t)om_move_layer(w, ib), obx, oby, &bx, &by);
            routed = 1;
        }
    }
    /* R-001-07: a walker's push result stays on its walk mask. See also: tests/csim/test_E01_T2_collision_mask.py */
    if (changed && !routed) {
        if (om_move_is_walker(w, ia)) om_move_slide(w, ms, 1, (uint32_t)om_move_layer(w, ia), oax, oay, &ax, &ay);
        if (om_move_is_walker(w, ib)) om_move_slide(w, ms, 1, (uint32_t)om_move_layer(w, ib), obx, oby, &bx, &by);
    }
    om_move_grid_set(ms, ia, ax, ay);
    om_move_grid_set(ms, ib, bx, by);
    return changed;
}

/* A pair that neither unit has left since it was last checked cannot have started to overlap, so after the
 * first iteration only units with something new to check take a turn: col_need marks a unit that moved, and
 * every lower-id unit within the collision diameter of where a unit moved to (the pair is checked in the
 * lower unit's turn). A skipped turn would have found no overlapping pair and written nothing. */
static void om_move_collision_mark(om_move_state *ms, uint32_t id) {
    const double target = 2.0 * ms->radius;
    const double r2 = target * target;
    const double x = om_move_grid_x(ms, id), y = om_move_grid_y(ms, id);
    int32_t cx0, cx1, cy0, cy1, cy;
    uint32_t base, lo, hi;
    if (ms->col_all) return;
    if (++ms->col_marks > ms->discovery_max / OM_MOVE_MARK_FULL_DIV) { ms->col_all = 1; return; }
    ms->col_need[id] = 1;
    if (ms->col_last && id <= ms->col_cur + 1) return;
    for (base = ms->slot_base; base < ms->slot_base + ms->n_spill; base += OM_MOVE_MASK_BITS) {
        uint64_t mask = om_move_near_mask(ms, base, ms->slot_base + ms->n_spill, x, y, r2);
        for (; mask; mask &= mask - 1) {
            uint32_t v = ms->slot_id[base + om_move_lowest_bit(mask)];
            if (v < id && (!ms->col_last || v > ms->col_cur)) ms->col_need[v] = 1;
        }
    }
    if (!om_move_grid_box(ms, x, y, target, &cx0, &cx1, &cy0, &cy1)) return;
    for (cy = cy0; cy <= cy1; cy++) {
        uint32_t row = (uint32_t)cy * (uint32_t)ms->grid_w;
        lo = ms->grid_start[row + (uint32_t)cx0];
        hi = ms->grid_start[row + (uint32_t)cx1 + 1];
        for (base = lo; base < hi; base += OM_MOVE_MASK_BITS) {
            uint64_t mask = om_move_near_mask(ms, base, hi, x, y, r2);
            for (; mask; mask &= mask - 1) {
                uint32_t v = ms->slot_id[base + om_move_lowest_bit(mask)];
                if (v < id && (!ms->col_last || v > ms->col_cur)) ms->col_need[v] = 1;
            }
        }
    }
}

/* One pair, and whichever of its units it displaced (bit-compared) is marked for the next checks. */
static void om_move_collide_pair_marked(om_world *w, om_move_state *ms, uint32_t ia, uint32_t ib) {
    const double ax = om_move_grid_x(ms, ia), ay = om_move_grid_y(ms, ia);
    const double bx = om_move_grid_x(ms, ib), by = om_move_grid_y(ms, ib);
    if (!om_move_collide_pair(w, ms, ia, ib)) return;
    if (memcmp(&ax, &ms->slot_x[ms->unit_slot[ia]], sizeof ax) || memcmp(&ay, &ms->slot_y[ms->unit_slot[ia]], sizeof ay)) {
        om_move_collision_mark(ms, ia);
        ms->col_moved = 1;
    }
    if (memcmp(&bx, &ms->slot_x[ms->unit_slot[ib]], sizeof bx) || memcmp(&by, &ms->slot_y[ms->unit_slot[ib]], sizeof by)) {
        om_move_collision_mark(ms, ib);
        ms->col_moved = 1;
    }
}

/* One collision iteration: units in ascending id order; for unit a, its
 * partners (the units above it that overlap it) in ascending id order, each
 * resolved against a's position as the earlier ones left it, which is the
 * order of an all-pairs i < j sweep with live positions. Nothing but a's own
 * pairs moves a partner b during a's turn, so the partners come from a
 * neighbour list: the units above a within target + slack of a's position
 * when queried. It stays complete while a is within slack of that position,
 * and a is re-queried once it has moved further.
 *
 * Kept from the sweep this replaced (see also: OM_MOVE_LIST_REACH_RADII): that sweep
 * built its list at twice the reach and examined a's drift only before its
 * next listed candidate, so a unit that drifted past the slack after its last
 * listed candidate ended its turn without a re-query, whatever it now
 * overlapped. Results match it bit for bit, so that stop is reproduced: the
 * turn ends when the wider list has no candidate left
 * (om_move_grid_any_above). Returns whether any unit was displaced. */
static int om_move_collision_once(om_world *w, om_move_state *ms, int first, int last) {
    const double target = 2.0 * ms->radius;
    const double slack = ms->radius;
    const double drift2 = slack * slack;
    uint32_t id_i;
    ms->col_moved = 0;
    ms->col_last = (uint8_t)last;
    for (id_i = 1; id_i <= ms->discovery_max; id_i++) {
        uint32_t n, k;
        double ax0, ay0;
        if (!ms->grid_in[id_i]) continue;
        if (!first && !ms->col_all && !ms->col_need[id_i]) continue;
        ms->col_need[id_i] = 0;
        ms->col_cur = id_i;
        ax0 = om_move_grid_x(ms, id_i); ay0 = om_move_grid_y(ms, id_i);
        n = om_move_grid_collect(w, ms, ax0, ay0, target + slack, id_i);
        for (k = 0; k < n; k++) {
            uint32_t id_j = ms->grid_scratch[k];
            double mx, my;
            om_move_collide_pair_marked(w, ms, id_i, id_j);
            mx = om_move_grid_x(ms, id_i) - ax0; my = om_move_grid_y(ms, id_i) - ay0;
            if (mx * mx + my * my > drift2) {
                if (k + 1 >= n && !om_move_grid_any_above(w, ms, ax0, ay0, OM_MOVE_LIST_REACH_RADII * ms->radius, id_j)) break;
                ax0 = om_move_grid_x(ms, id_i); ay0 = om_move_grid_y(ms, id_i);
                n = om_move_grid_collect(w, ms, ax0, ay0, target + slack, id_j);
                k = (uint32_t)-1;
            }
        }
    }
    return (int)ms->col_moved;
}

/* A collision pass reads only each unit's x/y, its stationary flag, and
 * whether it is in the grid. A pass that writes nothing is a fixpoint: the
 * same state gives the same (empty) pass again, so the remaining iterations
 * and, next time this state is seen, the whole pass are skipped. settle_*
 * holds that state exactly (bit-compared). */
static uint8_t om_move_settle_flag(const om_move_unit *mu, int live) {
    return (uint8_t)((live ? 1 : 0) | (om_move_is_stationary(mu) ? 2 : 0));
}

static int om_move_settle_matches(om_world *w, om_move_state *ms) {
    uint32_t id;
    if (!ms->settle_valid || !ms->grid_live || ms->settle_max != ms->discovery_max) return 0;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        const om_move_unit *mu = &ms->units[id];
        int live = mu->in_use && om_unit_alive(w, id);
        if (live != (int)ms->grid_in[id] || om_move_settle_flag(mu, live) != ms->settle_flag[id]) return 0;
        if (live && (memcmp(&mu->x, &ms->settle_x[id], sizeof(double)) != 0
                  || memcmp(&mu->y, &ms->settle_y[id], sizeof(double)) != 0)) return 0;
    }
    return 1;
}

static void om_move_settle_record(om_move_state *ms) {
    uint32_t id;
    ms->settle_max = ms->discovery_max;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        const om_move_unit *mu = &ms->units[id];
        ms->settle_flag[id] = om_move_settle_flag(mu, ms->grid_in[id]);
        ms->settle_x[id] = mu->x;
        ms->settle_y[id] = mu->y;
    }
    ms->settle_valid = 1;
}

/* A184: true when no unit moved more than OM_COLLISION_SETTLE_EPS over the pass just run (squared compare, no sqrt). */
static int om_move_pass_settled(const om_move_state *ms) {
    uint32_t id;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        double dx, dy;
        if (!ms->grid_in[id]) continue;
        dx = om_move_grid_x(ms, id) - ms->pass_x[id];
        dy = om_move_grid_y(ms, id) - ms->pass_y[id];
        if (dx * dx + dy * dy > OM_COLLISION_SETTLE_EPS2) return 0;
    }
    return 1;
}

/* Every unit starts pair checks, moving or stopped (A156, R-097-10). Under PURSUE_BY_STEERING the push pass
 * repeats up to OM_COLLISION_PASSES times and stops early when a pass changes nothing, i.e. no pair is
 * closer than 2 * radius, or when no unit moved more than OM_COLLISION_SETTLE_EPS in it (A184). A140: with it 0 the baseline's 3 passes stay. */
static void om_move_collision_pass_internal(om_world *w, om_move_state *ms) {
    int iter, passes, settled = 0;
    uint32_t id;
    om_move_discover(w, ms);
    om_move_load_radius(ms);
    ms->col_pursue = om_move_param_on(ms, OM_TP_PURSUE_BY_STEERING);
    ms->col_route = om_move_param_on(ms, OM_TP_ROUTE_AROUND_TERRAIN);
    ms->col_open = (uint8_t)(!ms->density && om_mapgen_terrain_free(w));
    if (ms->col_pursue) {
        for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
            const om_move_unit *mu = &ms->units[id];
            ms->start_layer[id] = mu->in_use && om_unit_alive(w, id) ? om_unit_get_layer(w, id) : -1;
        }
    }
    if (om_move_settle_matches(w, ms)) return;
    if (!ms->grid_live) om_move_grid_rebuild(w, ms, 1);
    ms->settle_valid = 0;
    ms->col_marks = 0;
    ms->col_all = 0;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        ms->stat[id] = (uint8_t)om_move_is_stationary(&ms->units[id]);
    }
    passes = ms->col_pursue ? OM_COLLISION_PASSES : OM_COLLISION_MAX_ITER;
    for (iter = 0; iter < passes; iter++) {
        if (ms->col_pursue) {
            for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
                if (!ms->grid_in[id]) continue;
                ms->pass_x[id] = om_move_grid_x(ms, id);
                ms->pass_y[id] = om_move_grid_y(ms, id);
            }
        }
        if (!om_move_collision_once(w, ms, iter == 0, iter == passes - 1)) {
            settled = 1;
            break;
        }
        if (ms->col_pursue && om_move_pass_settled(ms)) break;
    }
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        if (!ms->grid_in[id]) continue;
        ms->units[id].x = om_move_grid_x(ms, id);
        ms->units[id].y = om_move_grid_y(ms, id);
    }
    if (settled) om_move_settle_record(ms);
}

/* -------------------------------------------------------------- ticking */

static void om_move_apply_queue_for_tick(om_world *w, om_move_state *ms, uint64_t recorded_tick) {
    uint32_t i;
    for (i = 0; i < ms->n_queue; i++) {
        om_move_queue_entry *q = &ms->queue[i];
        om_move_unit *mu;
        if (!q->in_use || q->tick != recorded_tick) continue;
        mu = om_move_touch(w, ms, q->unit_id);
        if (!mu) continue;
        mu->has_dest = 1;
        mu->dest_x = q->x;
        mu->dest_y = q->y;
        mu->direct_move = 0;
        mu->group_id = 0;
        mu->engaged = 0;
        mu->kiting = 0;
        mu->deflecting = 0;
        mu->order_kind = q->kind;
        om_move_transit_cancel(mu);
        om_move_route_touch(ms, 0, q->x, q->y);
    }
}

/* PP-move P8 (PURSUE_BY_STEERING): the units a probe from (x, y) can touch, as their start-of-tick
 * positions, into scan_x/scan_y: same layer only, group mates and idle friends included, the unit itself
 * not. The grid was filed at the start of the tick, so a unit still in a cell is in the cell of its
 * start-of-tick position; a unit in the spill list is always a candidate. Returns the count. */
static uint32_t om_move_probe_gather_start(om_move_state *ms, uint32_t self_id, double x, double y) {
    const double r = OM_STEERING_PROBE_DIST + 2.0 * ms->radius + OM_MOVE_GRID_BOUND_PAD;
    const double r2 = r * r;
    const int32_t layer = ms->start_layer[self_id];
    int32_t cx0, cx1, cy0, cy1, cy;
    uint32_t n = 0, slot, cid;
    for (slot = ms->slot_base; slot < ms->slot_base + ms->n_spill; slot++) {
        cid = ms->slot_id[slot];
        double dx = ms->start_x[cid] - x, dy = ms->start_y[cid] - y;
        if (cid == self_id || ms->start_layer[cid] != layer || dx * dx + dy * dy > r2) continue;
        ms->scan_x[n] = ms->start_x[cid];
        ms->scan_y[n] = ms->start_y[cid];
        n++;
    }
    if (!om_move_grid_box_disp(ms, ms->probe_extra, x, y, r, &cx0, &cx1, &cy0, &cy1)) return n;
    for (cy = cy0; cy <= cy1; cy++) {
        uint32_t row = (uint32_t)cy * (uint32_t)ms->grid_w, lo = ms->grid_start[row + (uint32_t)cx0], hi = ms->grid_start[row + (uint32_t)cx1 + 1], base;
        for (base = lo; base < hi; base += OM_MOVE_MASK_BITS) {
            uint64_t mask = om_move_near_mask_at(ms->slot_sx, ms->slot_sy, base, hi, x, y, r2);
            for (; mask; mask &= mask - 1) {
                slot = base + om_move_lowest_bit(mask);
                cid = ms->slot_id[slot];
                if (ms->unit_slot[cid] != slot || cid == self_id || ms->start_layer[cid] != layer) continue;
                ms->scan_x[n] = ms->slot_sx[slot];
                ms->scan_y[n] = ms->slot_sy[slot];
                n++;
            }
        }
    }
    return n;
}

/* Length in wu of the route from (x0, y0) to (x1, y1) on one layer, the way om_move_route_plan walks it (the
 * farthest cell centre in line of sight, again and again); -1 when either end is blocked or no route exists.
 * See also: om_move_across_plan, which compares these lengths across layers (R-001-05). */
static double om_move_path_len(const om_world *w, om_move_state *ms, uint32_t layer, double x0, double y0, double x1, double y1) {
    static const int32_t OM_BFS_DX[OM_MOVE_BFS_DIR_COUNT] = {1, -1, 0, 0};
    static const int32_t OM_BFS_DY[OM_MOVE_BFS_DIR_COUNT] = {0, 0, 1, -1};
    int32_t nx, ny, cx, cy, dcx, dcy, guard;
    double px = x0, py = y0, total = 0.0;
    const uint32_t *f;
    om_move_window(ms, &nx, &ny);
    om_move_cell_at(ms, x0, y0, &cx, &cy);
    om_move_cell_at(ms, x1, y1, &dcx, &dcy);
    if (cx < 0 || cy < 0 || cx >= nx || cy >= ny || dcx < 0 || dcy < 0 || dcx >= nx || dcy >= ny) return -1.0;
    if (om_move_cell_blocked(w, ms, layer, cx, cy) || om_move_cell_blocked(w, ms, layer, dcx, dcy)) return -1.0;
    if (om_move_los_clear(w, ms, x0, y0, x1, y1, layer)) return sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0));
    f = om_move_field_for(w, ms, layer, dcx, dcy);
    if (!f || f[cy * nx + cx] == OM_MOVE_FIELD_UNREACHED) return -1.0;
    for (guard = 0; guard < nx * ny; guard++) {
        double lx = px, ly = py;
        int moved = 0;
        while (f[cy * nx + cx] > 1) {
            int dir;
            int32_t bx = -1, by = -1;
            double qx, qy;
            for (dir = 0; dir < OM_MOVE_BFS_DIR_COUNT; dir++) {
                int32_t x = cx + OM_BFS_DX[dir], y = cy + OM_BFS_DY[dir];
                if (x < 0 || y < 0 || x >= nx || y >= ny || f[y * nx + x] != f[cy * nx + cx] - 1) continue;
                bx = x;
                by = y;
                break;
            }
            if (bx < 0) return -1.0;
            qx = ((double)bx + OM_MOVE_CELL_MID) * OM_NAVMESH_CELL_SIZE;
            qy = ((double)by + OM_MOVE_CELL_MID) * OM_NAVMESH_CELL_SIZE;
            if (moved && !om_move_los_clear(w, ms, px, py, qx, qy, layer)) break;
            cx = bx;
            cy = by;
            lx = qx;
            ly = qy;
            moved = 1;
        }
        total += sqrt((lx - px) * (lx - px) + (ly - py) * (ly - py));
        px = lx;
        py = ly;
        if (f[cy * nx + cx] <= 1 || om_move_los_clear(w, ms, px, py, x1, y1, layer)) {
            return total + sqrt((x1 - px) * (x1 - px) + (y1 - py) * (y1 - py));
        }
    }
    return -1.0;
}

/* R-001-05 (Q-001-05 (a), provisional; ROUTE_ACROSS_LAYERS): the layer to plan on. Where the straight line is
 * blocked on the unit's layer, the quickest route by travel time wins: the walk on its own layer, or the walk
 * on another layer plus a transfer there and a transfer back (the unit ends on the layer it was ordered on).
 * Going over starts a routed transfer, which om_move_layer_unit brings back down. */
static uint32_t om_move_across_plan(om_world *w, om_move_state *ms, om_move_unit *mu, uint32_t layer) {
    const double tx = om_move_clamp_axis(mu->dest_x, ms->canvas_w), ty = om_move_clamp_axis(mu->dest_y, ms->canvas_h);
    double speed, len, best_t, xfer;
    uint32_t l, best = layer;
    if (mu->transit) return mu->lay_state != OM_LAY_NONE ? mu->lay_to : layer;
    if (!om_move_param_on(ms, OM_TP_ROUTE_ACROSS_LAYERS) || mu->lay_state != OM_LAY_NONE) return layer;
    if (om_move_los_clear(w, ms, mu->x, mu->y, tx, ty, layer)) return layer;
    speed = om_unit_effective_speed(w, mu->unit_id);
    if (!(speed > 0.0)) return layer;
    len = om_move_path_len(w, ms, layer, mu->x, mu->y, tx, ty);
    best_t = len < 0.0 ? OM_MOVE_GRID_FAR : len / speed;
    xfer = 2.0 * om_unit_profile_layer_transition_time(w, om_unit_get_unit_type(w, mu->unit_id));
    for (l = 0; l < OM_LAYER_COUNT; l++) {
        double t;
        if (l == layer) continue;
        len = om_move_path_len(w, ms, l, mu->x, mu->y, tx, ty);
        if (len < 0.0) continue;
        t = len / speed + xfer;
        if (t < best_t) { best_t = t; best = l; }
    }
    if (best == layer) return layer;
    mu->transit = 1;
    mu->transit_home = layer;
    mu->lay_state = OM_LAY_PENDING;
    mu->lay_to = best;
    mu->lay_route = 1;
    mu->lay_has_pend = 0;
    ms->lay_any = 1;
    return best;
}

/* The open cell of `layer` nearest to (px, py) within max_r rings; ties go to the lower row, then column. */
static int om_move_nearest_open(const om_world *w, om_move_state *ms, int walk, uint32_t layer, double px, double py, int32_t max_r, int32_t *out_x, int32_t *out_y) {
    int32_t nx, ny, cx, cy, r, best_x = -1, best_y = -1;
    double best = OM_MOVE_GRID_FAR;
    om_move_cell_at(ms, px, py, &cx, &cy);
    om_move_window(ms, &nx, &ny);
    for (r = 1; r < nx + ny && r <= max_r; r++) {
        int32_t x, y;
        if (best_x >= 0 && (double)r * OM_NAVMESH_CELL_SIZE * (double)r * OM_NAVMESH_CELL_SIZE >= best) break;
        for (y = cy - r; y <= cy + r; y++) {
            int32_t step = (y == cy - r || y == cy + r) ? 1 : 2 * r;
            for (x = cx - r; x <= cx + r; x += step) {
                double x0, y0, qx, qy, d2;
                if (x < 0 || y < 0 || x >= nx || y >= ny || om_move_cell_blocked_for(w, ms, walk, layer, x, y)) continue;
                x0 = (double)x * OM_NAVMESH_CELL_SIZE;
                y0 = (double)y * OM_NAVMESH_CELL_SIZE;
                qx = px < x0 ? x0 : (px > x0 + OM_NAVMESH_CELL_SIZE ? x0 + OM_NAVMESH_CELL_SIZE : px);
                qy = py < y0 ? y0 : (py > y0 + OM_NAVMESH_CELL_SIZE ? y0 + OM_NAVMESH_CELL_SIZE : py);
                d2 = (qx - px) * (qx - px) + (qy - py) * (qy - py);
                if (d2 < best || (d2 == best && (y < best_y || (y == best_y && x < best_x)))) { best = d2; best_x = x; best_y = y; }
            }
        }
    }
    *out_x = best_x;
    *out_y = best_y;
    return best_x >= 0;
}

/* W2: a stored walk route belongs to the order and the plan that made it; every event that clears the plan or the order drops it
 * too, so a stale route is never saved or hashed as live. See also: om_move_route_store, tests/csim/test_VG_W_w2_routes.py (N3). */
static void om_move_route_drop(om_move_unit *mu) {
    mu->route_n = 0;
    mu->route_i = 0;
    mu->route_ends_at_goal = 0;
}

/* R-097-09 (Westley, 2026-10-02): a unit found inside a blocked cell of its layer is moved to the nearest open
 * cell, not stalled: the nearest point of that cell at least a collision radius inside it; ties go to the lower
 * cell id. See also: om_move_tick_unit, which calls this each tick while ROUTE_AROUND_TERRAIN is on. */
static void om_move_leave_blocked(const om_world *w, om_move_state *ms, om_move_unit *mu) {
    const uint32_t layer = (uint32_t)om_move_layer(w, mu->unit_id);
    const int walk = om_move_is_walker(w, mu->unit_id);
    int32_t nx, ny, cx, cy, best_x, best_y;
    om_move_cell_at(ms, mu->x, mu->y, &cx, &cy);
    if (!om_move_cell_blocked_for(w, ms, walk, layer, cx, cy)) return;
    om_move_window(ms, &nx, &ny);
    if (!om_move_nearest_open(w, ms, walk, layer, mu->x, mu->y, nx + ny, &best_x, &best_y)) return;
    {
        const double lo = ms->radius, hi = OM_NAVMESH_CELL_SIZE - ms->radius;
        double rx = mu->x - (double)best_x * OM_NAVMESH_CELL_SIZE, ry = mu->y - (double)best_y * OM_NAVMESH_CELL_SIZE;
        mu->x = (double)best_x * OM_NAVMESH_CELL_SIZE + (rx < lo ? lo : (rx > hi ? hi : rx));
        mu->y = (double)best_y * OM_NAVMESH_CELL_SIZE + (ry < lo ? lo : (ry > hi ? hi : ry));
    }
    mu->plan_valid = 0;
    om_move_route_drop(mu);
    om_move_grid_update(ms, mu);
}

/* A step that would end in a blocked cell of the unit's layer slides along one axis, else is dropped, and
 * the route is planned again (E-13: a unit never enters a blocked cell). */
static void om_move_terrain_guard(const om_world *w, om_move_state *ms, om_move_unit *mu, uint32_t layer, double *nx, double *ny) {
    int32_t cx, cy;
    om_move_cell_at(ms, *nx, *ny, &cx, &cy);
    if (!om_move_cell_blocked(w, ms, layer, cx, cy)) return;
    mu->plan_valid = 0;
    om_move_route_drop(mu);
    om_move_cell_at(ms, *nx, mu->y, &cx, &cy);
    if (!om_move_cell_blocked(w, ms, layer, cx, cy)) { *ny = mu->y; return; }
    om_move_cell_at(ms, mu->x, *ny, &cx, &cy);
    if (!om_move_cell_blocked(w, ms, layer, cx, cy)) { *nx = mu->x; return; }
    *nx = mu->x;
    *ny = mu->y;
}

/* R-095-01, R-095-06 (Q-095-01; PURSUE_BY_STEERING): a group member moves at the group's slowest pace, except a unit
 * whose movement ability has it faster than its own base speed, which leaves the cap. */
static double om_move_member_pace(om_world *w, const om_move_unit *mu, uint32_t id) {
    double eff = om_unit_effective_speed(w, id);
    if (mu->group_id == 0) return eff;
    if (om_tactical_get_param(w, OM_TP_PURSUE_BY_STEERING) != 0.0 && eff > om_unit_profile_speed(w, om_unit_get_unit_type(w, id))) return eff;
    return mu->speed_cap;
}

/* PP-move P8, P7 (R-097-03, R-097-04, ALG-68, R-099-04): one unit's move under PURSUE_BY_STEERING, as the
 * Python's update_movement does it. Arrival is the slot radius, with no snap; the seek heading is the
 * unit vector to the destination; a blocked straight probe sweeps +30, -30, +60, -60, +90, -90 degrees
 * and takes the first clear one, holding it for the detour distance moved; none clear goes straight on.
 * See also: the 13-angle sweep in om_move_tick_unit, which this replaces when the switch is 0. */
static void om_move_steer_step(om_world *w, om_move_state *ms, om_move_unit *mu, uint32_t period) {
    uint32_t id = mu->unit_id;
    const int route = om_move_param_on(ms, OM_TP_ROUTE_AROUND_TERRAIN);
    double dx, dy, dist, steer_x, steer_y, step_dist, move_dist;
    if (route) {
        double wx = mu->aim_x - mu->x, wy = mu->aim_y - mu->y;
        const double reach = OM_WAYPOINT_ARRIVE_MULT * ms->radius;
        if (!mu->plan_valid || mu->plan_epoch != ms->terrain_epoch || mu->plan_dest_x != mu->dest_x || mu->plan_dest_y != mu->dest_y
            || (mu->aim_is_waypoint && wx * wx + wy * wy < reach * reach))
            om_move_route_plan(w, ms, mu, om_move_across_plan(w, ms, mu, (uint32_t)om_move_layer(w, id)));
        dx = mu->aim_x - mu->x;
        dy = mu->aim_y - mu->y;
    } else {
        dx = mu->dest_x - mu->x;
        dy = mu->dest_y - mu->y;
    }
    dist = sqrt(dx * dx + dy * dy);
    mu->waiting = 0;
    /* R-099-04: a move that followed route waypoints ends within the waypoint radius, like every one before it; a direct move and a group slot keep 1.5 radii. */
    if (sqrt((mu->dest_x - mu->x) * (mu->dest_x - mu->x) + (mu->dest_y - mu->y) * (mu->dest_y - mu->y))
        < (route && mu->routed && mu->group_id == 0 ? OM_WAYPOINT_ARRIVE_MULT : OM_ARRIVAL_TOLERANCE_MULT) * ms->radius) {
        mu->has_dest = 0;
        om_move_route_drop(mu);
        mu->deflecting = 0;
        return;
    }
    steer_x = dx / dist;
    steer_y = dy / dist;
    if (mu->deflecting && mu->detour_remaining > 0.0) {
        steer_x = mu->detour_dx;
        steer_y = mu->detour_dy;
    } else {
        uint32_t k, hints[OM_MOVE_PROBE_HINTS] = {0}, n_near = om_move_probe_gather_start(ms, id, mu->x, mu->y);
        mu->deflecting = 0;
        if (n_near && !om_move_probe_clear(ms, n_near, hints, mu->x + OM_STEERING_PROBE_DIST * steer_x, mu->y + OM_STEERING_PROBE_DIST * steer_y)) {
            double seek_x = steer_x, seek_y = steer_y;
            for (k = 0; k < OM_PP_SWEEP_N; k++) {
                double ax = seek_x * OM_PP_SWEEP_COS[k] - seek_y * OM_PP_SWEEP_SIN[k];
                double ay = seek_x * OM_PP_SWEEP_SIN[k] + seek_y * OM_PP_SWEEP_COS[k];
                if (!om_move_probe_clear(ms, n_near, hints, mu->x + OM_STEERING_PROBE_DIST * ax, mu->y + OM_STEERING_PROBE_DIST * ay)) continue;
                steer_x = ax;
                steer_y = ay;
                mu->deflecting = 1;
                mu->detour_dx = ax;
                mu->detour_dy = ay;
                mu->detour_remaining = OM_STEERING_DETOUR_MIN_DIST;
                break;
            }
        }
    }
    step_dist = om_move_member_pace(w, mu, id)
              * om_move_terrain_multiplier(om_move_density_at_pos(ms, mu->x, mu->y, route ? (uint32_t)om_move_layer(w, id) : 0))
              * (double)period / (double)OM_TACTICAL_TICK_RATE;
    move_dist = step_dist < dist ? step_dist : dist;
    if (move_dist > 0.0) {
        double nx = om_move_clamp_axis(mu->x + steer_x * move_dist, ms->canvas_w);
        double ny = om_move_clamp_axis(mu->y + steer_y * move_dist, ms->canvas_h);
        if (route) om_move_terrain_guard(w, ms, mu, (uint32_t)om_move_layer(w, id), &nx, &ny);
        mu->x = nx;
        mu->y = ny;
        om_move_grid_update(ms, mu);
    }
    if (mu->deflecting) {
        mu->detour_remaining -= move_dist;
        if (mu->detour_remaining <= 0.0) { mu->detour_remaining = 0.0; mu->deflecting = 0; }
    }
}

/* W2: point k of the stored route of mu, rebuilt by the expression walk_route.c wrote it with: a cell centre, except the
 * last point of a route that ended at the goal, which is the (clamped) destination the plan was made for. */
static void om_move_route_pt(const om_move_state *ms, const om_move_unit *mu, uint32_t k, double *x, double *y) {
    if (mu->route_ends_at_goal && k + 1u == mu->route_n) {
        *x = om_move_clamp_axis(mu->plan_dest_x, ms->canvas_w);
        *y = om_move_clamp_axis(mu->plan_dest_y, ms->canvas_h);
        return;
    }
    *x = ((double)ms->route_cx[mu->unit_id][k] + OM_MOVE_ROUTE_HALF) * OM_TERRAIN_CELL_WU;
    *y = ((double)ms->route_cy[mu->unit_id][k] + OM_MOVE_ROUTE_HALF) * OM_TERRAIN_CELL_WU;
}

/* W2: store the planner's points 1 .. n - 1 as terrain cells and start at point 1. Stores nothing (route_n 0, so the
 * walker replans at each waypoint as before) for a plan longer than OM_MOVE_WALK_PTS, a cell outside the terrain grid,
 * or a point that would not rebuild bit for bit. gx, gy is the clamped goal the planner was given. */
static int om_move_route_store(om_move_state *ms, om_move_unit *mu, const double *pts, int n, double gx, double gy) {
    const uint32_t id = mu->unit_id;
    const int ends = n > 1 && pts[2 * (n - 1)] == gx && pts[2 * (n - 1) + 1] == gy;
    int k;
    mu->route_n = 0;
    mu->route_i = 0;
    mu->route_ends_at_goal = 0;
    if (n < 2 || n > OM_MOVE_WALK_PTS || !om_move_route_tables(ms)) return 0;
    for (k = 1; k < n; k++) {
        const double fx = pts[2 * k] / OM_TERRAIN_CELL_WU, fy = pts[2 * k + 1] / OM_TERRAIN_CELL_WU;
        if (!(fx >= 0.0 && fy >= 0.0 && fx < (double)OM_TERRAIN_MAX_CELLS && fy < (double)OM_TERRAIN_MAX_CELLS)) return 0;
        ms->route_cx[id][k] = (uint16_t)(int)fx;
        ms->route_cy[id][k] = (uint16_t)(int)fy;
        if (!(ends && k == n - 1)
            && (((double)ms->route_cx[id][k] + OM_MOVE_ROUTE_HALF) * OM_TERRAIN_CELL_WU != pts[2 * k]
                || ((double)ms->route_cy[id][k] + OM_MOVE_ROUTE_HALF) * OM_TERRAIN_CELL_WU != pts[2 * k + 1])) return 0;
    }
    mu->route_n = (uint16_t)n;
    mu->route_i = 1;
    mu->route_ends_at_goal = (uint8_t)ends;
    return 1;
}

/* W2: the aim is the stored point route_i; it is a waypoint unless it is the last one. */
static void om_move_route_aim(const om_move_state *ms, om_move_unit *mu) {
    om_move_route_pt(ms, mu, mu->route_i, &mu->aim_x, &mu->aim_y);
    mu->aim_is_waypoint = (uint32_t)mu->route_i + 1u < mu->route_n;
}

/* Terrain stage 2 (R-001-07, R-004-07): a walker plans om_walk_route once per order and walks the stored points (W2).
 * It plans again when the plan is invalid, the terrain epoch, its layer or the destination changed. A plan of more than
 * OM_MOVE_WALK_PTS points is not stored: it replans from each waypoint it reaches, as before W2. A step that rises in
 * terrain height runs at 1/SLOPE_UP_DIV of the pace, one that falls at SLOPE_DOWN_MULT times it; the rest of the
 * tick's time carries over to the next waypoint. aim_is_waypoint is 1 while the aim is not the route's last point.
 * See also: om_move_walker_tick, which sets the layer after the step; tests/csim/test_VG_W_w2_routes.py. */
#define OM_MOVE_WALK_AIM_X 2 /* pts[0..1] is the unit; the next point follows */
#define OM_MOVE_WALK_MAX_LEGS 16
static void om_move_walker_step(om_world *w, om_move_state *ms, om_move_unit *mu, uint32_t period) {
    const uint32_t id = mu->unit_id;
    const double speed = om_move_member_pace(w, mu, id);
    const int terrain = om_terrain_present(w);
    double left = (double)period / (double)OM_TACTICAL_TICK_RATE;
    int legs;
    mu->waiting = 0;
    for (legs = 0; legs < OM_MOVE_WALK_MAX_LEGS && left > 0.0 && mu->has_dest; legs++) {
        double dx, dy, d, v, f = 1.0;
        if (!mu->plan_valid || mu->plan_epoch != ms->terrain_epoch || mu->plan_layer != (uint32_t)om_move_layer(w, id)
            || mu->plan_dest_x != mu->dest_x || mu->plan_dest_y != mu->dest_y) {
            double buf[2 * OM_MOVE_WALK_PTS], secs, *pts = buf;
            const double gx = om_move_clamp_axis(mu->dest_x, ms->canvas_w), gy = om_move_clamp_axis(mu->dest_y, ms->canvas_h);
            /* om_walk_route reads the unit's row position, which this module hands over once per sync. */
            mu->pushed_x = mu->x;
            mu->pushed_y = mu->y;
            om_tac_unit_sync_position(w, id, mu->x, mu->y);
            int n = om_walk_route(w, id, gx, gy, pts, OM_MOVE_WALK_PTS, &secs);
            if (n > OM_MOVE_WALK_PTS) {
                pts = (double *)malloc(sizeof(double) * 2u * (size_t)n);
                n = pts ? om_walk_route(w, id, gx, gy, pts, (uint32_t)n, &secs) : -1;
            }
            if (n < 2) {
                if (pts != buf) free(pts);
                mu->has_dest = 0;
                mu->plan_valid = 0;
                mu->route_n = 0;
                mu->route_i = 0;
                mu->route_ends_at_goal = 0;
                return;
            }
            mu->plan_dest_x = mu->dest_x;
            mu->plan_dest_y = mu->dest_y;
            if (om_move_route_store(ms, mu, pts, n, gx, gy)) {
                om_move_route_aim(ms, mu);
            } else {
                mu->aim_x = pts[OM_MOVE_WALK_AIM_X];
                mu->aim_y = pts[OM_MOVE_WALK_AIM_X + 1];
                mu->aim_is_waypoint = n > 2;
            }
            if (pts != buf) free(pts);
            mu->plan_valid = 1;
            mu->plan_epoch = ms->terrain_epoch;
            mu->plan_layer = (uint32_t)om_move_layer(w, id);
        }
        dx = mu->aim_x - mu->x;
        dy = mu->aim_y - mu->y;
        d = sqrt(dx * dx + dy * dy);
        if (terrain) {
            double h0 = om_terrain_height_at(w, mu->x, mu->y), h1 = om_terrain_height_at(w, mu->aim_x, mu->aim_y);
            if (h1 > h0) f = 1.0 / om_tactical_get_param(w, OM_TP_SLOPE_UP_DIV);
            else if (h1 < h0) f = om_tactical_get_param(w, OM_TP_SLOPE_DOWN_MULT);
        }
        v = speed * f;
        if (d > 0.0 && !(v > 0.0)) { mu->waiting = 1; return; }
        /* See also: tests/csim/test_E01_T2_walker_waypoint_arrival.py */
        if (mu->aim_is_waypoint && d < OM_WAYPOINT_ARRIVE_MULT * ms->radius) {
            if (mu->route_n > 1) { mu->route_i++; om_move_route_aim(ms, mu); }
            else mu->plan_valid = 0;
        } else if (d == 0.0 || v * left >= d) {
            mu->x = mu->aim_x;
            mu->y = mu->aim_y;
            if (d > 0.0) left -= d / v;
            if (mu->aim_is_waypoint && mu->route_n > 1) {
                mu->route_i++;
                om_move_route_aim(ms, mu);
            } else {
                mu->plan_valid = 0;
                mu->route_n = 0;
                mu->route_i = 0;
                mu->route_ends_at_goal = 0;
                if (!mu->aim_is_waypoint) { mu->has_dest = 0; mu->deflecting = 0; }
            }
        } else {
            mu->x += dx / d * v * left;
            mu->y += dy / d * v * left;
            left = 0.0;
        }
        om_move_grid_update(ms, mu);
    }
}

/* Internal, not in the header (om_internal.h): the stored walk route of a unit. Returns route_n (0 without a movement
 * row or a stored route), writes route_i, and fills min(route_n, cap) interleaved (x, y) pairs: slot 0 is the unit's
 * own position (the planner's point 0, not stored), slots 1 .. route_n - 1 the stored points. Reads through
 * om_move_get, never om_move_touch, so a call changes no checksum.
 * See also: tests/csim/test_VG_W_w2_routes.py */
uint32_t om_move_route_get(const om_world *w, uint32_t unit_id, uint32_t *route_i, double *pts, uint32_t cap) {
    const om_move_state *ms = w ? (const om_move_state *)w->move_state : NULL;
    const om_move_unit *mu;
    uint32_t k, n;
    if (route_i) *route_i = 0;
    if (!ms) return 0;
    mu = om_move_get((om_move_state *)ms, unit_id);
    if (!mu || !mu->in_use || mu->route_n < 2) return 0;
    if (route_i) *route_i = mu->route_i;
    n = mu->route_n < cap ? mu->route_n : cap;
    for (k = 0; k < n && pts; k++) {
        if (k == 0) { pts[0] = mu->x; pts[1] = mu->y; }
        else om_move_route_pt(ms, mu, k, &pts[2 * k], &pts[2 * k + 1]);
    }
    return mu->route_n;
}

static void om_move_tick_unit(om_world *w, om_move_state *ms, uint32_t id, uint32_t period) {
    om_move_unit *mu = om_move_get(ms, id);
    double heading, speed, dist_to_dest, step_dist;
    int walker;

    if (!mu || !mu->in_use || !om_unit_alive(w, id)) return;

    mu->prev_x = mu->x;
    mu->prev_y = mu->y;
    mu->prev_facing = mu->facing;

    walker = om_move_is_walker(w, id);
    if (walker || om_move_param_on(ms, OM_TP_ROUTE_AROUND_TERRAIN)) om_move_leave_blocked(w, ms, mu);

    if (mu->kiting) {
        om_move_unit *tgt = om_move_touch(w, ms, mu->kite_target);
        if (tgt) mu->facing = om_atan2(tgt->y - mu->y, tgt->x - mu->x);
        dist_to_dest = sqrt((mu->dest_x - mu->x) * (mu->dest_x - mu->x)
                           + (mu->dest_y - mu->y) * (mu->dest_y - mu->y));
        heading = om_atan2(mu->dest_y - mu->y, mu->dest_x - mu->x);
        speed = om_unit_effective_speed(w, id);
        step_dist = speed * (double)period / (double)OM_TACTICAL_TICK_RATE;
        if (step_dist >= dist_to_dest) {
            mu->x = mu->dest_x; mu->y = mu->dest_y;
        } else if (step_dist > 0.0) {
            mu->x += step_dist * om_cos(heading);
            mu->y += step_dist * om_sin(heading);
        }
        om_move_grid_update(ms, mu);
        return;
    }

    if (om_move_is_stationary(mu)) { mu->waiting = 0; return; }
    if (walker) { om_move_walker_step(w, ms, mu, period); return; }
    if (om_move_param_on(ms, OM_TP_PURSUE_BY_STEERING)) { om_move_steer_step(w, ms, mu, period); return; }
    /* PP baseline only (switch = 0); deleted with the two movement switches at the end of Phase E (A140) */
    /* See also: om_move_steer_step, which replaces everything below when OM_TP_PURSUE_BY_STEERING is 1 */

    dist_to_dest = sqrt((mu->dest_x - mu->x) * (mu->dest_x - mu->x)
                       + (mu->dest_y - mu->y) * (mu->dest_y - mu->y));
    heading = om_atan2(mu->dest_y - mu->y, mu->dest_x - mu->x);

    if (mu->deflecting) {
        double traveled = sqrt((mu->x - mu->deflect_origin_x) * (mu->x - mu->deflect_origin_x)
                              + (mu->y - mu->deflect_origin_y) * (mu->y - mu->deflect_origin_y));
        if (traveled < OM_STEERING_DETOUR_MIN_DIST) {
            heading = mu->deflect_heading;
        } else {
            mu->deflecting = 0;
        }
    }

    int found = 0;
    double move_cos = 0.0, move_sin = 0.0;
    if (!mu->deflecting) {
        uint32_t k, hints[OM_MOVE_PROBE_HINTS] = {0}, n_near = om_move_probe_gather(w, ms, id, mu->group_id, mu->x, mu->y);
        double sin_h = 0.0, cos_h = 0.0;
        if (n_near) om_move_sincos_approx(heading, &sin_h, &cos_h);
        for (k = 0; k < OM_STEERING_SWEEP_COUNT; k++) {
            double test_heading = heading + OM_STEERING_SWEEP_ANGLES[k];
            if (n_near && om_move_probe_sure_blocked(ms, n_near, hints,
                    mu->x + OM_STEERING_PROBE_DIST * (cos_h * ms->sweep_cos[k] - sin_h * ms->sweep_sin[k]),
                    mu->y + OM_STEERING_PROBE_DIST * (sin_h * ms->sweep_cos[k] + cos_h * ms->sweep_sin[k]))) continue;
            double ch = om_cos(test_heading);
            double sh = om_sin(test_heading);
            double px = mu->x + OM_STEERING_PROBE_DIST * ch;
            double py = mu->y + OM_STEERING_PROBE_DIST * sh;
            if (om_move_probe_clear(ms, n_near, hints, px, py)) {
                heading = test_heading;
                move_cos = ch;
                move_sin = sh;
                found = 1;
                if (OM_STEERING_SWEEP_ANGLES[k] != 0.0) {
                    /* R-097-04: a freshly chosen deflection snaps facing to
                     * the new heading immediately and pins it there for
                     * the whole STEERING_DETOUR_MIN_DIST segment, rather
                     * than turning into it at the turn-rate cap (R-100-02
                     * governs the un-deflected, straight-line case). */
                    mu->deflecting = 1;
                    mu->deflect_heading = heading;
                    mu->deflect_origin_x = mu->x;
                    mu->deflect_origin_y = mu->y;
                    mu->facing = heading;
                }
                break;
            }
        }
        if (!found) { mu->waiting = 1; return; } /* fully blocked: wait this tick */
    }
    mu->waiting = 0;

    speed = (mu->group_id != 0) ? mu->speed_cap : om_unit_effective_speed(w, id);
    speed *= om_move_terrain_multiplier(om_move_density_at_pos(ms, mu->x, mu->y, 0));

    step_dist = speed * (double)period / (double)OM_TACTICAL_TICK_RATE;
    if (step_dist >= dist_to_dest) {
        mu->x = mu->dest_x;
        mu->y = mu->dest_y;
        mu->has_dest = 0;
        om_move_route_drop(mu);
    } else if (step_dist > 0.0) {
        mu->x += step_dist * (found ? move_cos : om_cos(heading));
        mu->y += step_dist * (found ? move_sin : om_sin(heading));
    }
    om_move_grid_update(ms, mu);

    if (mu->deflecting) {
        mu->facing = heading; /* pinned for the whole detour segment */
    } else {
        mu->facing = om_move_turn_toward(mu->facing, heading, om_move_turn_rate_for(mu->native_speed), period, 0);
    }
}

/* PP-move P7 (R-100-01, PURSUE_BY_STEERING): after the moves and the collision pass, every living unit turns
 * (at its category's capped rate) toward its engaged target when that target is within 1.5 x its attack
 * range, else toward its move target, else along its velocity this tick; with none of those it keeps its
 * facing. A stationary unit that is firing turns too. Python facing.py update_facing.
 * See also: the facing writes in om_move_tick_unit, which this replaces when the switch is 0. */
#define OM_PP_FACING_ENGAGE_MULT 1.5
#define OM_PP_FACING_MIN_MOVE_SQ 1.0
static void om_move_face_pass(om_world *w, om_move_state *ms, uint32_t period) {
    uint32_t id;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        om_move_unit *mu = &ms->units[id];
        uint32_t tgt;
        double dx = 0.0, dy = 0.0, reach;
        int have = 0;
        if (!mu->in_use || mu->kiting || !om_unit_alive(w, id)) continue;
        tgt = om_unit_get_target(w, id);
        if (tgt != 0 && om_unit_alive(w, tgt)) {
            const om_move_unit *tm = om_move_get(ms, tgt);
            reach = om_unit_profile_attack_range(w, om_unit_get_unit_type(w, id)) * OM_PP_FACING_ENGAGE_MULT;
            dx = (tm && tm->in_use ? tm->x : om_unit_position_x(w, tgt)) - mu->x;
            dy = (tm && tm->in_use ? tm->y : om_unit_position_y(w, tgt)) - mu->y;
            have = dx * dx + dy * dy <= reach * reach;
        }
        if (!have && mu->has_dest) {
            dx = mu->dest_x - mu->x;
            dy = mu->dest_y - mu->y;
            have = dx * dx + dy * dy > OM_PP_FACING_MIN_MOVE_SQ;
        }
        if (!have) {
            dx = mu->x - mu->prev_x;
            dy = mu->y - mu->prev_y;
            have = dx * dx + dy * dy > OM_PP_FACING_MIN_MOVE_SQ;
        }
        if (have) mu->facing = om_move_turn_toward(mu->facing, om_atan2(dy, dx), om_move_turn_rate_by_category(w, id), period, 1);
    }
}

static void om_move_groups_check_arrival(om_move_state *ms) {
    double tol = OM_ARRIVAL_TOLERANCE_MULT * ms->radius;
    uint32_t g, m;
    for (g = 0; g < ms->n_groups; g++) {
        om_move_group *grp = &ms->groups[g];
        double cx = 0.0, cy = 0.0, centroid_dist;
        int all_within = 1;
        if (!grp->active) continue;
        for (m = 0; m < grp->n_members; m++) {
            om_move_unit *mu = om_move_get(ms, ms->group_members[grp->first_member + m]);
            double d;
            if (!mu) continue;
            cx += mu->x; cy += mu->y;
            d = sqrt((mu->x - mu->dest_x) * (mu->x - mu->dest_x) + (mu->y - mu->dest_y) * (mu->y - mu->dest_y));
            if (d > tol) all_within = 0;
        }
        if (grp->n_members > 0) { cx /= (double)grp->n_members; cy /= (double)grp->n_members; }
        centroid_dist = sqrt((cx - grp->click_x) * (cx - grp->click_x) + (cy - grp->click_y) * (cy - grp->click_y));
        if (all_within || centroid_dist <= tol) grp->active = 0;
    }
}

/* One tick of a unit's layer transfer (R-002-01 to R-002-07, R-004-01 to R-004-04). A pending order begins on the
 * first tick the target layer is open at the unit's cell; the unit then counts lay_dur ticks (the type's
 * layer_transition_time), crosses over at half (R-004-02) and settles at the end. An order given in flight begins the
 * tick after. A routed unit that went over a mass asks to come back down once its own layer is open and clear. */
static void om_move_layer_unit(om_world *w, om_move_state *ms, om_move_unit *mu, uint32_t period) {
    const uint32_t id = mu->unit_id;
    const uint32_t cur = (uint32_t)om_move_layer(w, id);
    int32_t cx, cy;
    if (mu->lay_state == OM_LAY_NONE && mu->transit) {
        if (cur == mu->transit_home) mu->transit = 0;
        else {
            om_move_cell_at(ms, mu->x, mu->y, &cx, &cy);
            if (!mu->has_dest && om_move_cell_blocked(w, ms, mu->transit_home, cx, cy)) {
                /* R-001-05, R-097-09: the cell under the unit is blocked on its home layer; it walks on to the nearest open one before it descends. */
                int32_t ox, oy;
                if (om_move_nearest_open(w, ms, 0, mu->transit_home, mu->x, mu->y, OM_MOVE_DESCENT_SEARCH_RINGS, &ox, &oy)) {
                    mu->has_dest = 1;
                    mu->dest_x = ((double)ox + OM_MOVE_CELL_MID) * OM_NAVMESH_CELL_SIZE;
                    mu->dest_y = ((double)oy + OM_MOVE_CELL_MID) * OM_NAVMESH_CELL_SIZE;
                    mu->direct_move = 1;
                    mu->plan_valid = 0;
                    om_move_route_drop(mu);
                }
            } else if (!mu->has_dest || (!om_move_cell_blocked(w, ms, mu->transit_home, cx, cy)
                && om_move_los_clear(w, ms, mu->x, mu->y, om_move_clamp_axis(mu->dest_x, ms->canvas_w), om_move_clamp_axis(mu->dest_y, ms->canvas_h), mu->transit_home))) {
                mu->lay_state = OM_LAY_PENDING;
                mu->lay_to = mu->transit_home;
                mu->lay_route = 1;
            }
        }
    } else if (mu->lay_state == OM_LAY_PENDING && mu->transit && !mu->has_dest && cur == mu->transit_home) {
        mu->lay_state = OM_LAY_NONE;
        mu->transit = 0;
    }
    if (mu->lay_state == OM_LAY_PENDING) {
        double secs;
        if (mu->lay_to == cur) { mu->lay_state = OM_LAY_NONE; return; }
        om_move_cell_at(ms, mu->x, mu->y, &cx, &cy);
        if (om_move_cell_blocked(w, ms, mu->lay_to, cx, cy)) return;
        secs = om_unit_profile_layer_transition_time(w, om_unit_get_unit_type(w, id));
        mu->lay_dur = (uint32_t)floor(secs * (double)OM_TACTICAL_TICK_RATE + OM_MOVE_ROUND_HALF);
        if (mu->lay_dur < 1) mu->lay_dur = 1;
        mu->lay_state = OM_LAY_FLIGHT;
        mu->lay_t = 0;
    }
    if (mu->lay_state != OM_LAY_FLIGHT) return;
    mu->lay_t += period;
    if (2 * mu->lay_t >= mu->lay_dur && cur != mu->lay_to) om_tac_unit_set_layer(w, id, mu->lay_to);
    if (mu->lay_t < mu->lay_dur) return;
    mu->lay_state = OM_LAY_NONE;
    mu->lay_route = 0;
    if (mu->lay_has_pend) {
        mu->lay_has_pend = 0;
        mu->lay_state = OM_LAY_PENDING;
        mu->lay_to = mu->lay_pend;
    }
}

static void om_move_layer_pass(om_world *w, om_move_state *ms, uint32_t period) {
    uint32_t id;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        om_move_unit *mu = &ms->units[id];
        if (!mu->in_use || (mu->lay_state == OM_LAY_NONE && !mu->transit) || !om_unit_alive(w, id)) continue;
        om_move_layer_unit(w, ms, mu, period);
    }
}

/* PP-move R-099-05, A169 (PURSUE_BY_STEERING): a unit under a group move that has been within GROUP_GIVEUP_RADIUS of
 * its slot for GROUP_GIVEUP_TICKS consecutive ticks without arriving ends its order where it stands; leaving the
 * disc or arriving resets the count. Runs at the top of the tick, on the positions the last tick ended with. */
static void om_move_giveup_pass(om_world *w, om_move_state *ms) {
    uint32_t id;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        om_move_unit *mu = &ms->units[id];
        double dx, dy;
        if (!mu->in_use || !mu->has_dest || mu->group_id == 0 || !om_unit_alive(w, id)) { if (mu->in_use) mu->giveup_near = 0; continue; }
        dx = mu->dest_x - mu->x;
        dy = mu->dest_y - mu->y;
        if (dx * dx + dy * dy > (double)OM_GROUP_GIVEUP_RADIUS * (double)OM_GROUP_GIVEUP_RADIUS) { mu->giveup_near = 0; continue; }
        if (++mu->giveup_near >= OM_GROUP_GIVEUP_TICKS) {
            mu->has_dest = 0;
            om_move_route_drop(mu);
            mu->deflecting = 0;
            mu->giveup_near = 0;
        }
    }
}

static void om_move_tick_once(om_world *w, om_move_state *ms, uint64_t new_tick, uint32_t period) {
    uint32_t id;
    om_move_discover(w, ms);
    om_move_load_radius(ms);
    om_move_apply_queue_for_tick(w, ms, new_tick - 1);
    if (ms->lay_any) om_move_layer_pass(w, ms, period);
    om_move_grid_rebuild(w, ms, 1);
    if (om_move_param_on(ms, OM_TP_PURSUE_BY_STEERING)) om_move_giveup_pass(w, ms);
    if (om_move_param_on(ms, OM_TP_PURSUE_BY_STEERING)) {
        for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
            ms->start_x[id] = ms->units[id].x;
            ms->start_y[id] = ms->units[id].y;
            if (ms->grid_in[id]) {
                ms->slot_sx[ms->unit_slot[id]] = ms->start_x[id];
                ms->slot_sy[ms->unit_slot[id]] = ms->start_y[id];
            }
            ms->start_layer[id] = ms->grid_in[id] ? om_unit_get_layer(w, id) : -1;
        }
        ms->probe_extra = 0.0;
    }
    for (id = 1; id <= ms->discovery_max; id++) {
        om_move_tick_unit(w, ms, id, period);
    }
    om_move_walker_tick(w);
    om_move_collision_pass_internal(w, ms);
    if (om_move_param_on(ms, OM_TP_PURSUE_BY_STEERING)) om_move_face_pass(w, ms, period);
    om_move_groups_check_arrival(ms);
}

/* R-092-02: no unit moves in the recon phase. Phase -1 (no mission) and
 * tactical both let movement run; recon ends when the player begins. */
static int om_move_in_recon(const om_world *w) {
    return om_mission_get_phase(w) == 0;
}

/* Hands unit.c every position that changed since the last hand-off (once per
 * unit per sync, not per collision iteration), so its cached row and grid
 * track this module's positions without waiting for its next refresh. */
static void om_move_push_positions(om_world *w, om_move_state *ms) {
    uint32_t id;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        om_move_unit *mu = &ms->units[id];
        if (!mu->in_use || (mu->x == mu->pushed_x && mu->y == mu->pushed_y)) continue;
        mu->pushed_x = mu->x;
        mu->pushed_y = mu->y;
        om_tac_unit_sync_position(w, id, mu->x, mu->y);
    }
}

/* R-099-03: a replayed tick is a step of the period that step ran at, not
 * the period now: unit.c recomputes the period at the top of a step, then its
 * position refresh syncs here, so the tick being replayed belongs to the
 * previous step. period_seen is the period at the last sync (0 = none yet). */
static void om_move_sync(om_world *w) {
    om_move_state *ms = om_ms(w);
    uint64_t target = om_tactical_tick(w);
    uint32_t now = om_tactical_tick_period(w);
    uint32_t period = ms->period_seen ? ms->period_seen : now;
    uint64_t t;
    if (ms->last_synced_tick > target) ms->last_synced_tick = target;
    if (om_move_in_recon(w)) {
        ms->last_synced_tick = target;
        ms->period_seen = now;
        return;
    }
    if (ms->syncing) return;
    ms->syncing = 1;
    for (t = ms->last_synced_tick + 1; t <= target; t++) {
        om_move_tick_once(w, ms, t, period);
    }
    ms->syncing = 0;
    if (ms->last_synced_tick < target) om_move_push_positions(w, ms);
    ms->last_synced_tick = target;
    ms->period_seen = now;
}

static void om_move_enqueue(om_world *w, om_move_state *ms, int kind, uint32_t unit, double x, double y) {
    om_move_queue_entry *q;
    if (ms->n_queue >= OM_MOVE_MAX_QUEUE) {
        /* entries from ticks already stepped are spent (om_replay_get_command_count_at_tick
         * then no longer counts them); entries of this tick are pending and stay. */
        uint32_t i, kept = 0;
        for (i = 0; i < ms->n_queue; i++) {
            if (ms->queue[i].tick >= ms->last_synced_tick) ms->queue[kept++] = ms->queue[i];
        }
        ms->n_queue = kept;
        if (ms->n_queue >= OM_MOVE_MAX_QUEUE) return;
    }
    q = &ms->queue[ms->n_queue++];
    q->in_use = 1;
    q->tick = om_tactical_tick(w);
    q->kind = kind;
    q->unit_id = unit;
    q->x = x;
    q->y = y;
}

/* ------------------------------------------------------------- commands */

void om_collision_pass(om_world *w) {
    om_move_state *ms;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    om_move_collision_pass_internal(w, ms);
    om_move_push_positions(w, ms);
}

/* PP-move (ROUTE_AROUND_TERRAIN, R-098-02, R-007-01/02/06): the fire side of cover, the same test as fog.c's
 * om_fog_cover_blocks plus the height: a cover disc blocks a line only when neither unit stands inside it
 * and the line is on a layer the cover reaches (layers 0 to height - 1; for a line between two layers,
 * the lower one). See also: fog.c om_fog_cover_blocks, the sight side. */
static int om_combat_cover_blocks(const om_world *w, uint32_t p0, uint32_t p1, double ox, double oy, double tx, double ty) {
    int32_t l0 = om_unit_get_layer(w, p0), l1 = om_unit_get_layer(w, p1), layer = l0 < l1 ? l0 : l1;
    uint32_t i, n = om_map_cover_count(w);
    double dx = tx - ox, dy = ty - oy, len2 = dx * dx + dy * dy;
    for (i = 0; i < n; i++) {
        double cx, cy, r, h, t, px, py;
        if (!om_map_cover_at(w, i, &cx, &cy, &r, &h) || (double)layer >= h) continue;
        if ((ox - cx) * (ox - cx) + (oy - cy) * (oy - cy) <= r * r || (tx - cx) * (tx - cx) + (ty - cy) * (ty - cy) <= r * r) continue;
        t = len2 > 0.0 ? ((cx - ox) * dx + (cy - oy) * dy) / len2 : 0.0;
        t = t < 0.0 ? 0.0 : (t > 1.0 ? 1.0 : t);
        px = ox + dx * t - cx;
        py = oy + dy * t - cy;
        if (px * px + py * py < r * r) return 1;
    }
    return 0;
}

int om_combat_can_shoot(const om_world *w, uint32_t p0, uint32_t p1) {
    /* R-098-01: units never block fire, so no unit is consulted between the
     * endpoints. R-098-02: terrain (this module's density cells) and the
     * cover/obstacle discs tactical_mapgen.c records block the line the same
     * way they block a sight line; the discs are read through its public
     * sampler, which reports presence only (no cover height). Only points
     * strictly between the two units are sampled, at one-wu resolution. */
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    double x0, y0, dx, dy, dist;
    int steps, i;
    if (!w) return 0;
    ms = om_ms(ww);
    x0 = om_unit_position_x(ww, p0);
    y0 = om_unit_position_y(ww, p0);
    dx = om_unit_position_x(ww, p1) - x0;
    dy = om_unit_position_y(ww, p1) - y0;
    dist = sqrt(dx * dx + dy * dy);
    steps = (int)(dist / OM_LOS_SAMPLE_STEP);
    if (om_move_param_on(ms, OM_TP_ROUTE_AROUND_TERRAIN)) {
        /* R-098-02: a blocked cell on the lower of the two layers blocks the line, as the cover test does.
         * See also: fog.c, the sight side. */
        if (om_combat_cover_blocks(w, p0, p1, x0, y0, x0 + dx, y0 + dy)) return 0;
        if (!om_move_los_clear(w, ms, x0, y0, x0 + dx, y0 + dy, (uint32_t)om_move_layer(w, p0) < (uint32_t)om_move_layer(w, p1) ? (uint32_t)om_move_layer(w, p0) : (uint32_t)om_move_layer(w, p1))) return 0;
    }
    /* Terrain stage 2: in a ground era the ground between the two stands in the line, the same test as fog.c's. See also: om_fog_can_see_at. */
    if (om_era_kind(w) == 1 && om_terrain_present(w) && om_terrain_sight_blocks(w, om_move_layer(w, p0), x0, y0, om_move_layer(w, p1), x0 + dx, y0 + dy)) return 0;
    /* Nothing to sample: no density cell, no canvas or obstacle disc, no cover disc, so every sample reads zero. */
    if (!ms->density && om_mapgen_terrain_free(w) && om_map_cover_count(w) == 0) return 1;
    for (i = 1; i < steps; i++) {
        double t = (double)i / (double)steps;
        double px = x0 + t * dx, py = y0 + t * dy;
        om_gradient_properties g;
        if (!om_move_param_on(ms, OM_TP_ROUTE_AROUND_TERRAIN) && om_move_density_at_pos(ms, px, py, 0) > OM_NAVMESH_OBSTACLE_THRESHOLD) return 0;
        om_map_sample_gradients(ww, px, py, &g);
        /* PP baseline only (switch = 0); deleted with the two movement switches at the end of Phase E (A140) */
        if ((g.cover_density > 0.0 && !om_move_param_on(ms, OM_TP_ROUTE_AROUND_TERRAIN)) || g.obstacle_density > OM_NAVMESH_OBSTACLE_THRESHOLD) return 0;
    }
    return 1;
}

void om_command_attack_target_kiting(om_world *w, uint32_t unit, uint32_t target, double retreat_x, double retreat_y) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, unit);
    if (!mu) return;
    om_move_touch(w, ms, target);
    mu->kiting = 1;
    mu->kite_target = target;
    mu->has_dest = 1;
    mu->dest_x = retreat_x;
    mu->dest_y = retreat_y;
    mu->engaged = 0;
    mu->group_id = 0;
    mu->direct_move = 0;
    mu->deflecting = 0;
    mu->order_kind = 2;
}

void om_command_direct_move(om_world *w, uint32_t unit, double x, double y) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, unit);
    if (!mu) return;
    mu->has_dest = 1;
    mu->dest_x = x;
    mu->dest_y = y;
    mu->direct_move = 1;
    mu->group_id = 0;
    mu->engaged = 0;
    mu->kiting = 0;
    mu->deflecting = 0;
    mu->order_kind = 0;
    om_move_route_touch(ms, 0, x, y);
}

uint32_t om_command_group_move(om_world *w, const uint32_t *ids, uint32_t n, double x, double y) {
    om_move_state *ms;
    om_move_group *grp;
    uint32_t i, gid;
    double cx = 0.0, cy = 0.0, min_speed = 0.0;
    int scattered = 0;
    if (!w || !ids || n == 0) return 0;
    om_move_sync(w);
    ms = om_ms(w);
    for (i = 0; i < n; i++) {
        om_move_unit *mu = om_move_touch(w, ms, ids[i]);
        if (mu) { cx += mu->x; cy += mu->y; }
    }
    cx /= (double)n;
    cy /= (double)n;
    for (i = 0; i < n; i++) {
        double sp = om_unit_order_speed(w, ids[i]);
        if (i == 0 || sp < min_speed) min_speed = sp;
    }
    for (i = 0; i < n; i++) {
        om_move_unit *mu = om_move_touch(w, ms, ids[i]);
        double d;
        if (!mu) continue;
        d = sqrt((mu->x - cx) * (mu->x - cx) + (mu->y - cy) * (mu->y - cy));
        if (d > OM_MAGIC_BOX_SPREAD_RADIUS) scattered = 1;
    }

    grp = om_move_group_alloc(ms, n);
    if (!grp) return 0;
    gid = ms->next_group_id++;
    grp->active = 1;
    grp->id = gid;
    grp->click_x = x;
    grp->click_y = y;
    grp->speed_cap = min_speed;
    grp->n_members = n;
    for (i = 0; i < n; i++) ms->group_members[grp->first_member + i] = ids[i];

    for (i = 0; i < n; i++) {
        om_move_unit *mu = om_move_touch(w, ms, ids[i]);
        double slot_x, slot_y;
        if (!mu) continue;
        if (scattered) {
            slot_x = x;
            slot_y = y;
        } else {
            slot_x = x + (mu->x - cx);
            slot_y = y + (mu->y - cy);
        }
        if (om_move_slot_blocked(w, ms, slot_x, slot_y)) {
            slot_x = x;
            slot_y = y;
        }
        mu->has_dest = 1;
        mu->dest_x = slot_x;
        mu->dest_y = slot_y;
        mu->direct_move = 0;
        mu->group_id = gid;
        mu->speed_cap = min_speed;
        mu->engaged = 0;
        mu->kiting = 0;
        mu->deflecting = 0;
        mu->order_kind = 0;
        om_move_route_touch(ms, 0, slot_x, slot_y);
        om_tac_unit_set_guard(w, ids[i], 0);
    }
    return gid;
}

int om_command_issue_named(om_world *w, const char *name, uint32_t unit, double x, double y) {
    if (!w || !name) return 1;
    if (strcmp(name, "move") == 0) {
        return om_command_move(w, &unit, 1, x, y);
    }
    return 1; /* R-096-06: patrol/hold/stop/follow and anything else -- rejected, no state change */
}

int om_command_move(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double x, double y) {
    om_move_state *ms;
    uint32_t i;
    if (!w || !unit_ids) return 1;
    om_move_sync(w);
    ms = om_ms(w);
    for (i = 0; i < n_units; i++) {
        om_move_unit *mu = om_move_touch(w, ms, unit_ids[i]);
        if (!mu) continue;
        mu->has_dest = 1;
        mu->dest_x = x;
        mu->dest_y = y;
        mu->direct_move = 0;
        mu->group_id = 0;
        mu->engaged = 0;
        mu->kiting = 0;
        /* R-097-03: a new order does not cut a detour short; PP baseline only (switch = 0), deleted with the two movement switches at the end of Phase E (A140) */
        if (!om_move_param_on(ms, OM_TP_PURSUE_BY_STEERING)) mu->deflecting = 0;
        mu->order_kind = 0;
        om_move_transit_cancel(mu);
        om_move_route_touch(ms, 0, x, y);
        om_tac_unit_set_guard(w, unit_ids[i], 0);
    }
    return 0;
}

void om_command_queue_attack_move(om_world *w, uint32_t unit, double x, double y) {
    om_move_state *ms;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    om_move_touch(w, ms, unit);
    om_move_enqueue(w, ms, 1, unit, x, y);
}

void om_command_queue_move(om_world *w, uint32_t unit, double x, double y) {
    om_move_state *ms;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    om_move_touch(w, ms, unit);
    om_move_enqueue(w, ms, 0, unit, x, y);
}

int om_group_is_active(const om_world *w, uint32_t gid) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_group *grp;
    if (!w) return 0;
    om_move_sync(ww);
    ms = om_ms(ww);
    grp = om_move_group_find(ms, gid);
    return (grp && grp->active) ? 1 : 0;
}

void om_map_set_obstacle_density(om_world *w, uint32_t p0, uint32_t p1, uint32_t p2, double p3) {
    om_move_state *ms;
    long i;
    if (!w) return;
    ms = om_ms(w);
    i = om_move_density_index(ms, (int32_t)p0, (int32_t)p1, p2);
    if (i < 0) return;
    if (!ms->density) {
        ms->density = (double *)calloc((size_t)OM_LAYER_COUNT * OM_MOVE_DENSITY_SIDE * OM_MOVE_DENSITY_SIDE, sizeof(double));
        if (!ms->density) return;
    }
    ms->density[i] = p3;
    ms->terrain_epoch++;
    om_mapgen_cell_set_density(w, p2, (int32_t)p0, (int32_t)p1, p3);
}

uint32_t om_navmesh_find_path(om_world *w, double p0, double p1, double p2, double p3, uint32_t p4) {
    om_move_state *ms;
    int straight;
    uint32_t len;
    if (!w) return 0;
    ms = om_ms(w);
    len = om_move_route_len(w, ms, p4, p0, p1, p2, p3, &straight);
    om_move_route_touch(ms, p4, p2, p3);
    ms->last_path_straightened = straight;
    return len;
}

uint32_t om_navmesh_get_cache_hits(const om_world *w) {
    om_world *ww = (om_world *)w;
    if (!w) return 0;
    return om_ms(ww)->cache_hits;
}

double om_navmesh_get_cell_size(const om_world *w) {
#ifdef OM_DEBUG_INJECT
    if (w && w->inject == OM_BUG_NAVMESH_CELL_SIZE_WRONG_CONSTANT) return OM_NAVMESH_CELL_SIZE * OM_NAVMESH_OBSTACLE_THRESHOLD;
#endif
    (void)w;
    return OM_NAVMESH_CELL_SIZE;
}

int om_navmesh_is_cell_blocked(const om_world *w, uint32_t p0, uint32_t p1, uint32_t p2) {
    om_world *ww = (om_world *)w;
    if (!w) return 0;
    return om_move_cell_blocked(w, om_ms(ww), p2, (int32_t)p0, (int32_t)p1);
}

int om_navmesh_is_path_straightened(const om_world *w) {
    om_world *ww = (om_world *)w;
    if (!w) return 0;
    return om_ms(ww)->last_path_straightened;
}

double om_renderer_interpolate_facing(const om_world *w, uint32_t p0, double p1) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return 0.0;
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    if (!mu) return 0.0;
    return mu->prev_facing + p1 * (mu->facing - mu->prev_facing);
}

int om_renderer_interpolate_position(const om_world *w, uint32_t p0, double p1, double *p2, double *p3) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) { if (p2) *p2 = 0.0; if (p3) *p3 = 0.0; return 0; }
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    if (!mu) { if (p2) *p2 = 0.0; if (p3) *p3 = 0.0; return 0; }
    if (p2) *p2 = mu->prev_x + p1 * (mu->x - mu->prev_x);
    if (p3) *p3 = mu->prev_y + p1 * (mu->y - mu->prev_y);
    return 1;
}

uint32_t om_replay_get_command_count_at_tick(const om_world *w, uint64_t p0) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    uint32_t i, count = 0;
    if (!w) return 0;
    om_move_sync(ww);
    ms = om_ms(ww);
    for (i = 0; i < ms->n_queue; i++) {
        if (ms->queue[i].in_use && ms->queue[i].tick == p0) count++;
    }
    return count;
}

int om_steering_get_obstacle_repulsion(const om_world *w, uint32_t p0, double *p1, double *p2) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    double heading, ax, ay, density;
    if (!w) { if (p1) *p1 = 0.0; if (p2) *p2 = 0.0; return 0; }
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    if (!mu || !mu->has_dest || !mu->direct_move) {
        if (p1) *p1 = 0.0;
        if (p2) *p2 = 0.0;
        return 0;
    }
    heading = om_atan2(mu->dest_y - mu->y, mu->dest_x - mu->x);
    ax = mu->x + OM_STEERING_OBSTACLE_AVOIDANCE_RANGE * om_cos(heading);
    ay = mu->y + OM_STEERING_OBSTACLE_AVOIDANCE_RANGE * om_sin(heading);
    density = om_move_density_at_pos(ms, ax, ay, 0);
    if (density > OM_OBSTACLE_DENSITY_LOW_THRESHOLD) {
        if (p1) *p1 = -om_cos(heading);
        if (p2) *p2 = -om_sin(heading);
    } else {
        if (p1) *p1 = 0.0;
        if (p2) *p2 = 0.0;
    }
    return 1;
}

double om_steering_get_sweep_angle_at(const om_world *w, uint32_t p0) {
    (void)w;
    if (p0 >= OM_STEERING_SWEEP_COUNT) return 0.0;
    return OM_STEERING_SWEEP_ANGLES[p0];
}

uint32_t om_steering_get_sweep_angle_count(const om_world *w) {
    (void)w;
    return OM_STEERING_SWEEP_COUNT;
}

void om_unit_clear_orders(om_world *w, uint32_t p0) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, p0);
    if (!mu) return;
    mu->has_dest = 0;
    om_move_route_drop(mu);
    mu->engaged = 0;
    mu->kiting = 0;
    mu->direct_move = 0;
    mu->group_id = 0;
    mu->deflecting = 0;
}

double om_unit_compute_terrain_speed(const om_world *w, uint32_t p0, double p1) {
    om_world *ww = (om_world *)w;
    double base;
    if (!w) return 0.0;
    base = om_unit_effective_speed(ww, p0);
    return base * om_move_terrain_multiplier(p1);
}

void om_unit_engage(om_world *w, uint32_t p0, uint32_t p1) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, p0);
    if (!mu) return;
    om_move_touch(w, ms, p1);
    mu->engaged = 1;
}

double om_unit_get_current_speed(const om_world *w, uint32_t p0) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return 0.0;
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    if (!mu) return 0.0;
    if (mu->kiting) return om_unit_effective_speed(ww, p0);
    if (om_move_is_stationary(mu)) return 0.0;
    if (mu->waiting) return 0.0;
    return om_move_member_pace(ww, mu, p0);
}

int om_unit_get_destination(const om_world *w, uint32_t p0, double *p1, double *p2) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) { if (p1) *p1 = 0.0; if (p2) *p2 = 0.0; return 0; }
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    if (!mu) { if (p1) *p1 = 0.0; if (p2) *p2 = 0.0; return 0; }
    if (p1) *p1 = mu->dest_x;
    if (p2) *p2 = mu->dest_y;
    return mu->has_dest;
}

double om_unit_get_facing(const om_world *w, uint32_t p0) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return 0.0;
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    return mu ? mu->facing : 0.0;
}

int om_unit_get_order_kind(const om_world *w, uint32_t p0) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return -1;
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, p0);
    return mu ? mu->order_kind : -1;
}

int om_unit_get_pos(const om_world *w, uint32_t unit, double *out_x, double *out_y) {
    om_world *ww = (om_world *)w;
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) { if (out_x) *out_x = 0.0; if (out_y) *out_y = 0.0; return 0; }
    om_move_sync(ww);
    ms = om_ms(ww);
    mu = om_move_touch(ww, ms, unit);
    if (!mu) { if (out_x) *out_x = 0.0; if (out_y) *out_y = 0.0; return 0; }
    if (out_x) *out_x = mu->x;
    if (out_y) *out_y = mu->y;
    return 1;
}

/* Braced is the toggle the player sees: windup (1) and active (2) count,
 * canceling (3) and idle (0) do not. */
static int om_move_brace_toggled(om_world *w, uint32_t unit) {
    int32_t phase = om_unit_brace_phase(w, unit);
    return phase == 1 || phase == 2;
}

int om_unit_has_active_buff(const om_world *w, uint32_t p0, const char *p1) {
    om_world *ww = (om_world *)w;
    if (!w || !p1) return 0;
    if (strcmp(p1, "brace") == 0) return om_move_brace_toggled(ww, p0);
    /* No public accessor names which ability is active, only that one is
     * (om_unit_ability_active, csrc/unit.c) -- see file header. Raider Surge
     * is a manual ability activation, so this is the best available proxy. */
    if (strcmp(p1, "surge") == 0) return om_unit_ability_active(ww, p0);
    return 0;
}

int om_unit_is_braced(const om_world *w, uint32_t p0) {
    om_world *ww = (om_world *)w;
    if (!w) return 0;
    return om_move_brace_toggled(ww, p0);
}

void om_unit_set_facing(om_world *w, uint32_t p0, double p1) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, p0);
    if (!mu) return;
    mu->facing = p1;
    mu->prev_facing = p1;
}

void om_unit_set_pos(om_world *w, uint32_t p0, double p1, double p2) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, p0);
    if (!mu) return;
    mu->x = p1;
    mu->y = p2;
    mu->prev_x = p1;
    mu->prev_y = p2;
    mu->pushed_x = p1;
    mu->pushed_y = p2;
    om_tac_unit_sync_position(w, p0, p1, p2);
}

void om_unit_set_visible_to_faction(om_world *w, uint32_t p0, int32_t p1, int p2) {
    om_move_state *ms;
    om_move_unit *mu;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, p0);
    if (!mu) return;
    if (p1 >= 0 && p1 < OM_MAX_FACTIONS) mu->visible[p1] = p2;
}

void om_unit_teleport(om_world *w, uint32_t unit, double x, double y, uint32_t layer) {
    om_move_state *ms;
    om_move_unit *mu;
    (void)layer;
    if (!w) return;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, unit);
    if (!mu) return;
    mu->x = x;
    mu->y = y;
    mu->prev_x = x;
    mu->prev_y = y;
    mu->pushed_x = x;
    mu->pushed_y = y;
    om_tac_unit_sync_position(w, unit, x, y);
}

/* ---- generated stubs from signatures.toml ---- */
/* A133 Q-C4: settings survive om_tactical_reset and a new world starts at defaults. They are saved in the
 * movement slot and hashed in the movement section of the full checksum (every member, OM_TP__COUNT of them);
 * only the light om_world_get_state_checksum leaves them out.
 * # See also: om_tactical_reset (csrc/unit.c) frees w->move_state, which holds them. */
double om_tactical_get_param(const om_world *w, om_tac_param p) {
    const om_move_state *ms;
    if (!w || (int)p < 0 || p >= OM_TP__COUNT) return -1.0;
    ms = (const om_move_state *)w->move_state;
    return ms ? ms->param[p] : OM_PP_ROWS[p].def;
}

int om_tactical_set_param(om_world *w, om_tac_param p, double value) {
    const om_pp_row *row;
    if (!w || (int)p < 0 || p >= OM_TP__COUNT) return -1;
    row = &OM_PP_ROWS[p];
    if (!(value >= row->lo && value <= row->hi)) return -1;
    if (row->kind != OM_PP_REAL && (double)(int64_t)value != value) return -1;
    if (row->kind == OM_PP_BOOL && value != 0.0 && value != 1.0) return -1;
    om_ms(w)->param[p] = value;
    return 0;
}

int om_command_set_layer(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t layer) {
    om_move_state *ms;
    uint32_t i;
    if (!w || layer >= OM_LAYER_COUNT || (n_units > 0 && !unit_ids)) return -1;
    om_move_sync(w);
    ms = om_ms(w);
    for (i = 0; i < n_units; i++) {
        om_move_unit *mu;
        if (om_unit_get_layer(w, unit_ids[i]) < 0 || !om_unit_alive(w, unit_ids[i])) continue;
        if (om_move_is_walker(w, unit_ids[i])) continue; /* R-001-07: a walker takes no layer order */
        mu = om_move_touch(w, ms, unit_ids[i]);
        if (!mu) continue;
        ms->lay_any = 1;
        mu->transit = 0;
        om_tac_unit_set_guard(w, unit_ids[i], 0);
        if (mu->lay_state == OM_LAY_FLIGHT) {
            mu->lay_has_pend = layer != mu->lay_to;
            mu->lay_pend = layer;
        } else {
            mu->lay_route = 0;
            mu->lay_to = layer;
            mu->lay_state = layer == (uint32_t)om_move_layer(w, unit_ids[i]) ? OM_LAY_NONE : OM_LAY_PENDING;
        }
    }
    return 0;
}

double om_unit_transition_progress(const om_world *w, uint32_t unit) {
    const om_move_state *ms;
    if (!w) return 0.0;
    om_move_sync((om_world *)w);
    ms = om_ms((om_world *)w);
    if (unit >= OM_MOVE_MAX_UNITS || !ms->units[unit].in_use || ms->units[unit].lay_state != OM_LAY_FLIGHT) return 0.0;
    return (double)ms->units[unit].lay_t / (double)ms->units[unit].lay_dur;
}

uint32_t om_unit_get_target_layer(const om_world *w, uint32_t unit) {
    const om_move_state *ms;
    int32_t own;
    if (!w || (own = om_unit_get_layer(w, unit)) < 0) return UINT32_MAX;
    om_move_sync((om_world *)w);
    ms = om_ms((om_world *)w);
    if (unit < OM_MOVE_MAX_UNITS && ms->units[unit].in_use && ms->units[unit].lay_state != OM_LAY_NONE) return ms->units[unit].lay_to;
    return (uint32_t)om_unit_get_layer(w, unit);
}

/* R-164-02. A type never set reads 0 up, 0 down; -1 for a type that is not built in and not registered. */
int om_roster_set_reach(om_world *w, int unit_type, uint32_t layers_up, uint32_t layers_down) {
    om_move_state *ms;
    uint32_t i;
    if (!w || om_unit_profile_ability_count(w, unit_type) == 0u) return -1;
    ms = om_ms(w);
    for (i = 0; i < ms->reach_n && ms->reach_type[i] != unit_type; i++) {}
    if (i == ms->reach_n) {
        if (i >= OM_PP_REACH_MAX) return -1;
        ms->reach_n++;
        ms->reach_type[i] = unit_type;
    }
    ms->reach_up[i] = layers_up;
    ms->reach_down[i] = layers_down;
    return 0;
}

/* Terrain stage 2: 0 ok; 1 unknown type (or the kind list is full); 2 unknown kind. */
int om_roster_set_movement_kind(om_world *w, int type, int kind) {
    om_move_state *ms;
    uint32_t i;
    if (!w || type < 0 || om_unit_profile_ability_count(w, type) == 0u) return 1;
    if (kind != OM_MOVE_FLYING && kind != OM_MOVE_WALKING && kind != OM_MOVE_SWIMMING) return 2;
    ms = om_ms(w);
    for (i = 0; i < ms->kind_n && ms->kind_type[i] != type; i++) {}
    if (kind == OM_MOVE_FLYING) {
        for (; i + 1u < ms->kind_n; i++) { ms->kind_type[i] = ms->kind_type[i + 1u]; ms->kind_val[i] = ms->kind_val[i + 1u]; }
        if (i < ms->kind_n) ms->kind_n--;
        return 0;
    }
    if (i == ms->kind_n) {
        if (i >= OM_PP_REACH_MAX) return 1;
        ms->kind_n++;
        ms->kind_type[i] = type;
    }
    ms->kind_val[i] = kind;
    return 0;
}

int om_unit_profile_movement_kind(const om_world *w, int type) {
    const om_move_state *ms;
    uint32_t i;
    if (!w || type < 0 || om_unit_profile_ability_count((om_world *)w, type) == 0u) return OM_MOVE_FLYING;
    ms = (const om_move_state *)w->move_state;
    for (i = 0; ms && i < ms->kind_n; i++) {
        if (ms->kind_type[i] == type) return ms->kind_val[i];
    }
    return OM_MOVE_FLYING;
}

/* R-004-06: a walker on a slope is on the lower band below the slope's midline and the upper band at or above it.
 * See also: om_move_walker_step, which moves the walker. */
void om_move_walker_tick(om_world *w) {
    om_move_state *ms = om_ms(w);
    uint32_t id;
    if (!om_terrain_present(w)) return;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        om_move_unit *mu = &ms->units[id];
        om_slope s;
        double dot;
        int32_t band;
        if (!mu->in_use || !om_unit_alive(w, id) || !om_move_is_walker(w, id) || om_terrain_slope_at(w, mu->x, mu->y, &s) < 0) continue;
        dot = (mu->x - s.mx) * (s.x1 - s.x0) + (mu->y - s.my) * (s.y1 - s.y0);
        band = (dot < 0.0 ? s.lower_band : s.upper_band) - 1;
        if (om_move_layer(w, id) != band) {
            /* The walker's own crossing of a slope: its route already runs over the link, and a replan from mid-slope on the
             * new layer finds no route (tests/csim/test_E01_R004_07_slope_time.py). So the plan follows the layer here and the
             * stored route is dropped (Architect 2026-10-14): route_n 0 with the aim kept is the pre-W2 plan, which replans at the
             * next waypoint arrival; the layer trigger in om_move_walker_step covers every other change. */
            if (mu->plan_valid && mu->plan_layer == (uint32_t)om_move_layer(w, id)) {
                mu->plan_layer = (uint32_t)band;
                om_move_route_drop(mu); /* stale: the aim stays, the next waypoint arrival replans on this layer like the old walker */
            }
            om_tac_unit_set_layer(w, id, (uint32_t)band);
        }
    }
}

int om_unit_profile_reach(const om_world *w, int unit_type, uint32_t *up, uint32_t *down) {
    const om_move_state *ms;
    uint32_t i, u = 0, d = 0;
    if (!w || om_unit_profile_ability_count((om_world *)w, unit_type) == 0u) return -1;
    ms = (const om_move_state *)w->move_state;
    for (i = 0; ms && i < ms->reach_n; i++) {
        if (ms->reach_type[i] == unit_type) { u = ms->reach_up[i]; d = ms->reach_down[i]; break; }
    }
    if (up) *up = u;
    if (down) *down = d;
    return 0;
}
uint32_t om_unit_get_group_id(const om_world *w, uint32_t unit) {
    const om_move_state *ms;
    if (!w) return 0;
    om_move_sync((om_world *)w);
    ms = om_ms((om_world *)w);
    return (unit < OM_MOVE_MAX_UNITS && ms->units[unit].in_use) ? ms->units[unit].group_id : 0;
}

/* See also: om_tac_unit_leash_anchor in unit.c, which owns the anchor */
int om_tac_unit_leash_anchor(const om_world *w, uint32_t unit_id, double *x, double *y);

int om_unit_get_leash_anchor(const om_world *w, uint32_t unit, double *x, double *y) {
    return w ? om_tac_unit_leash_anchor(w, unit, x, y) : 0;
}

int om_unit_get_engaged(const om_world *w, uint32_t unit) {
    const om_move_state *ms;
    if (!w) return 0;
    om_move_sync((om_world *)w);
    ms = om_ms((om_world *)w);
    return (unit < OM_MOVE_MAX_UNITS && ms->units[unit].in_use) ? ms->units[unit].engaged : 0;
}

/* See also: om_tac_release in unit.c: a held attack-move group member goes back to its slot with its group and cap */
int om_tac_move_resume(om_world *w, uint32_t unit_id) {
    om_move_state *ms;
    om_move_unit *mu;
    om_move_sync(w);
    ms = om_ms(w);
    mu = om_move_touch(w, ms, unit_id);
    if (!mu) return 0;
    mu->engaged = 0;
    return 1;
}
int om_command_guard(om_world *w, const uint32_t *unit_ids, uint32_t n_units) {
    om_move_state *ms;
    uint32_t i;
    if (!w || (n_units > 0 && !unit_ids)) return -1;
    om_move_sync(w);
    ms = om_ms(w);
    for (i = 0; i < n_units; i++) {
        om_move_unit *mu;
        if (om_unit_get_layer(w, unit_ids[i]) < 0 || !om_unit_alive(w, unit_ids[i])) continue;
        om_unit_clear_orders(w, unit_ids[i]);
        mu = om_move_touch(w, ms, unit_ids[i]);
        if (!mu) continue;
        /* a transfer not yet under way is dropped, one in flight lands and nothing follows it */
        if (mu->lay_state == OM_LAY_PENDING) mu->lay_state = OM_LAY_NONE;
        mu->lay_has_pend = 0;
        om_move_transit_cancel(mu);
        om_tac_unit_set_guard(w, unit_ids[i], 1);
    }
    return 0;
}
int om_roster_set_cone(om_world *w, int unit_type, double range, double half_angle_deg, double share) {
    /* LAB-REV2 E0 contract stub: -1 (not built) until LAB-REV2-E2 writes the cone table. See also: om_combat_can_engage. */
    (void)w; (void)unit_type; (void)range; (void)half_angle_deg; (void)share;
    return -1;
}
/* ---- end generated stubs ---- */

/* ---- net hooks (lockstep spec 2026-10-05) ---- */
#define OM_MV_PRIME 1099511628211ULL
#define OM_MV_SEED  14695981039346656037ULL
#define OM_MV_MIX_SHIFT 29
#define OM_MV_SECTION 4
#define OM_MV_WORD_BITS 64
#define OM_MV_NULL  0x6d6f76652d6e756cULL
static uint64_t mv_word(uint64_t h, uint64_t v) {
    h = (h ^ v) * OM_MV_PRIME;
    return h ^ (h >> OM_MV_MIX_SHIFT);
}
static uint64_t mv_dbl(uint64_t h, double d) {
    uint64_t v;
    memcpy(&v, &d, sizeof v);
    return mv_word(h, v);
}
/* A row still in the state om_move_touch gives a new row hashes as an absent one: reads such as om_unit_get_pos
 * create rows lazily, and a read must never change the checksum. Mirrors every field om_move_touch initialises.
 * See also: om_move_touch */
static int mv_row_is_fresh(const om_world *cw, const om_move_unit *mu) {
    om_world *w = (om_world *)cw; /* the position and speed getters only read */
    uint32_t f;
    double x = om_unit_position_x(w, mu->unit_id), y = om_unit_position_y(w, mu->unit_id);
    if (mu->x != x || mu->y != y) return 0;
    if (mu->pushed_x != x || mu->pushed_y != y || mu->prev_x != x || mu->prev_y != y) return 0;
    if (mu->deflect_origin_x != x || mu->deflect_origin_y != y) return 0;
    if (mu->facing != 0.0 || mu->prev_facing != 0.0 || mu->has_dest || mu->dest_x != 0.0 || mu->dest_y != 0.0) return 0;
    if (mu->direct_move || mu->group_id || mu->speed_cap != 0.0 || mu->engaged || mu->kiting || mu->kite_target) return 0;
    if (mu->order_kind != -1 || mu->routed || mu->deflecting || mu->deflect_heading != 0.0 || mu->waiting) return 0;
    if (mu->native_speed != om_unit_effective_speed(w, mu->unit_id)) return 0;
    for (f = 0; f < OM_MAX_FACTIONS; f++) if (!mu->visible[f]) return 0;
    return !mu->giveup_near && !mu->detour_remaining && !mu->detour_dx && !mu->detour_dy && !mu->plan_valid &&
           !mu->plan_epoch && !mu->plan_dest_x && !mu->plan_dest_y && !mu->aim_x && !mu->aim_y &&
           !mu->aim_is_waypoint && !mu->lay_state && !mu->lay_has_pend && !mu->lay_route && !mu->transit &&
           !mu->lay_to && !mu->lay_pend && !mu->lay_t && !mu->lay_dur && !mu->transit_home &&
           !mu->plan_layer && !mu->route_n && !mu->route_i && !mu->route_ends_at_goal;
}
static uint64_t om_move_section_hash(const om_world *w) {
    const om_move_state *ms = (const om_move_state *)w->move_state;
    uint64_t h = OM_MV_SEED;
    uint32_t id, k, nu;
    if (!ms) return OM_MV_NULL;
    nu = ms->discovery_max < OM_MOVE_MAX_UNITS - 1 ? ms->discovery_max : OM_MOVE_MAX_UNITS - 1;
    h = mv_word(h, ms->discovery_max);
    for (id = 1; id <= nu; id++) {
        const om_move_unit *mu = &ms->units[id];
        uint64_t bits = 0;
        int live = mu->in_use && !mv_row_is_fresh(w, mu);
        h = mv_word(h, (uint64_t)(int64_t)live);
        if (!live) continue;
        h = mv_word(h, mu->unit_id);
        h = mv_dbl(h, mu->x); h = mv_dbl(h, mu->y);
        h = mv_dbl(h, mu->pushed_x); h = mv_dbl(h, mu->pushed_y);
        h = mv_dbl(h, mu->facing);
        h = mv_dbl(h, mu->prev_x); h = mv_dbl(h, mu->prev_y); h = mv_dbl(h, mu->prev_facing);
        h = mv_word(h, (uint64_t)(int64_t)mu->has_dest);
        h = mv_word(h, mu->giveup_near);
        h = mv_dbl(h, mu->dest_x); h = mv_dbl(h, mu->dest_y);
        h = mv_word(h, (uint64_t)(int64_t)mu->direct_move);
        h = mv_word(h, mu->group_id);
        h = mv_dbl(h, mu->speed_cap);
        h = mv_word(h, (uint64_t)(int64_t)mu->engaged);
        h = mv_word(h, (uint64_t)(int64_t)mu->kiting);
        h = mv_word(h, mu->kite_target);
        h = mv_word(h, (uint64_t)(int64_t)mu->order_kind);
        h = mv_dbl(h, mu->native_speed);
        h = mv_word(h, (uint64_t)(int64_t)mu->deflecting);
        h = mv_dbl(h, mu->deflect_heading);
        h = mv_dbl(h, mu->deflect_origin_x); h = mv_dbl(h, mu->deflect_origin_y);
        h = mv_word(h, (uint64_t)(int64_t)mu->waiting);
        h = mv_dbl(h, mu->detour_remaining); h = mv_dbl(h, mu->detour_dx); h = mv_dbl(h, mu->detour_dy);
        for (k = 0; k < OM_MAX_FACTIONS; k++) {
            if (mu->visible[k]) bits |= 1ULL << (k % OM_MV_WORD_BITS);
        }
        h = mv_word(h, bits);
        h = mv_word(h, (uint64_t)(int64_t)mu->plan_valid);
        h = mv_word(h, mu->plan_epoch);
        h = mv_word(h, mu->plan_layer);
        h = mv_dbl(h, mu->plan_dest_x); h = mv_dbl(h, mu->plan_dest_y);
        h = mv_dbl(h, mu->aim_x); h = mv_dbl(h, mu->aim_y);
        h = mv_word(h, (uint64_t)(int64_t)mu->aim_is_waypoint);
        h = mv_word(h, (uint64_t)(int64_t)mu->routed);
        h = mv_word(h, (uint64_t)(int64_t)mu->lay_state);
        h = mv_word(h, (uint64_t)(int64_t)mu->lay_has_pend);
        h = mv_word(h, (uint64_t)(int64_t)mu->lay_route);
        h = mv_word(h, (uint64_t)(int64_t)mu->transit);
        h = mv_word(h, mu->lay_to); h = mv_word(h, mu->lay_pend);
        h = mv_word(h, mu->lay_t); h = mv_word(h, mu->lay_dur);
        h = mv_word(h, mu->transit_home);
        h = mv_word(h, mu->route_n); h = mv_word(h, mu->route_i); h = mv_word(h, mu->route_ends_at_goal);
        for (k = 1; k < mu->route_n; k++) {
            h = mv_word(h, ms->route_cx[id][k]); h = mv_word(h, ms->route_cy[id][k]);
        }
    }
    h = mv_word(h, ms->n_groups);
    h = mv_word(h, ms->next_group_id);
    for (k = 0; k < ms->n_groups && k < OM_MOVE_MAX_GROUPS; k++) {
        const om_move_group *g = &ms->groups[k];
        h = mv_word(h, (uint64_t)(int64_t)g->active);
        h = mv_word(h, g->id); h = mv_word(h, g->first_member); h = mv_word(h, g->n_members);
        h = mv_dbl(h, g->click_x); h = mv_dbl(h, g->click_y); h = mv_dbl(h, g->speed_cap);
    }
    h = mv_word(h, ms->n_group_members);
    for (k = 0; k < ms->n_group_members && k < OM_MOVE_MAX_GROUP_MEMBERS; k++) h = mv_word(h, ms->group_members[k]);
    h = mv_word(h, ms->last_synced_tick);
    h = mv_word(h, ms->period_seen);
    h = mv_word(h, ms->terrain_epoch);
    h = mv_word(h, ms->n_queue);
    for (k = 0; k < ms->n_queue && k < OM_MOVE_MAX_QUEUE; k++) {
        const om_move_queue_entry *q = &ms->queue[k];
        h = mv_word(h, (uint64_t)(int64_t)q->in_use);
        h = mv_word(h, q->tick);
        h = mv_word(h, (uint64_t)(int64_t)q->kind);
        h = mv_word(h, q->unit_id);
        h = mv_dbl(h, q->x); h = mv_dbl(h, q->y);
    }
    h = mv_dbl(h, ms->canvas_w); h = mv_dbl(h, ms->canvas_h);
    for (k = 0; k < OM_TP__COUNT; k++) h = mv_dbl(h, ms->param[k]);
    h = mv_word(h, (uint64_t)(int64_t)ms->lay_any);
    h = mv_word(h, ms->reach_n);
    for (k = 0; k < ms->reach_n && k < OM_PP_REACH_MAX; k++) {
        h = mv_word(h, (uint64_t)(int64_t)ms->reach_type[k]);
        h = mv_word(h, ms->reach_up[k]);
        h = mv_word(h, ms->reach_down[k]);
    }
    h = mv_word(h, ms->kind_n);
    for (k = 0; k < ms->kind_n && k < OM_PP_REACH_MAX; k++) {
        h = mv_word(h, (uint64_t)(int64_t)ms->kind_type[k]);
        h = mv_word(h, (uint64_t)(int64_t)ms->kind_val[k]);
    }
    return h;
}
typedef struct {
    uint8_t *out;
    uint32_t pos;
} mv_sw;
static void mv_put(mv_sw *s, uint64_t v, uint32_t width) {
    uint32_t i;
    if (s->out) {
        for (i = 0; i < width; i++) s->out[s->pos + i] = (uint8_t)((v >> (OM_SAVE_BYTE_BITS * i)) & OM_SAVE_BYTE_MASK);
    }
    s->pos += width;
}
static void mv_put_u32(mv_sw *s, uint32_t v) { mv_put(s, v, sizeof v); }
static void mv_put_i32(mv_sw *s, int32_t v) { mv_put(s, (uint32_t)v, sizeof v); }
static void mv_put_u64(mv_sw *s, uint64_t v) { mv_put(s, v, sizeof v); }
static void mv_put_f64(mv_sw *s, double d) {
    uint64_t v;
    memcpy(&v, &d, sizeof v);
    mv_put_u64(s, v);
}
static uint32_t mv_unit_count(const om_move_state *ms) {
    return ms->discovery_max < OM_MOVE_MAX_UNITS - 1 ? ms->discovery_max : OM_MOVE_MAX_UNITS - 1;
}
static void mv_save_all(const om_move_state *ms, mv_sw *s) {
    uint32_t id, k, nu = mv_unit_count(ms);
    mv_put_u32(s, ms->discovery_max);
    for (id = 1; id <= nu; id++) {
        const om_move_unit *mu = &ms->units[id];
        mv_put_i32(s, mu->in_use);
        if (!mu->in_use) continue;
        mv_put_u32(s, mu->unit_id);
        mv_put_f64(s, mu->x); mv_put_f64(s, mu->y);
        mv_put_f64(s, mu->pushed_x); mv_put_f64(s, mu->pushed_y);
        mv_put_f64(s, mu->facing);
        mv_put_f64(s, mu->prev_x); mv_put_f64(s, mu->prev_y); mv_put_f64(s, mu->prev_facing);
        mv_put_i32(s, mu->has_dest);
        mv_put_u32(s, mu->giveup_near);
        mv_put_f64(s, mu->dest_x); mv_put_f64(s, mu->dest_y);
        mv_put_i32(s, mu->direct_move);
        mv_put_u32(s, mu->group_id);
        mv_put_f64(s, mu->speed_cap);
        mv_put_i32(s, mu->engaged);
        mv_put_i32(s, mu->kiting);
        mv_put_u32(s, mu->kite_target);
        mv_put_i32(s, mu->order_kind);
        mv_put_f64(s, mu->native_speed);
        mv_put_i32(s, mu->deflecting);
        mv_put_f64(s, mu->deflect_heading);
        mv_put_f64(s, mu->deflect_origin_x); mv_put_f64(s, mu->deflect_origin_y);
        mv_put_i32(s, mu->waiting);
        mv_put_f64(s, mu->detour_remaining); mv_put_f64(s, mu->detour_dx); mv_put_f64(s, mu->detour_dy);
        for (k = 0; k < OM_MAX_FACTIONS; k++) mv_put_i32(s, mu->visible[k]);
        mv_put_i32(s, mu->plan_valid);
        mv_put_u32(s, mu->plan_epoch);
        mv_put_u32(s, mu->plan_layer);
        mv_put_f64(s, mu->plan_dest_x); mv_put_f64(s, mu->plan_dest_y);
        mv_put_f64(s, mu->aim_x); mv_put_f64(s, mu->aim_y);
        mv_put_i32(s, mu->aim_is_waypoint);
        mv_put_i32(s, mu->routed);
        mv_put_i32(s, mu->lay_state);
        mv_put_i32(s, mu->lay_has_pend);
        mv_put_i32(s, mu->lay_route);
        mv_put_i32(s, mu->transit);
        mv_put_u32(s, mu->lay_to); mv_put_u32(s, mu->lay_pend);
        mv_put_u32(s, mu->lay_t); mv_put_u32(s, mu->lay_dur);
        mv_put_u32(s, mu->transit_home);
        mv_put_u32(s, mu->route_n); mv_put_u32(s, mu->route_i); mv_put_u32(s, mu->route_ends_at_goal);
        for (k = 1; k < mu->route_n; k++) {
            mv_put_u32(s, ms->route_cx[id][k]); mv_put_u32(s, ms->route_cy[id][k]);
        }
    }
    mv_put_u32(s, ms->n_groups);
    mv_put_u32(s, ms->next_group_id);
    for (k = 0; k < ms->n_groups && k < OM_MOVE_MAX_GROUPS; k++) {
        const om_move_group *g = &ms->groups[k];
        mv_put_i32(s, g->active);
        mv_put_u32(s, g->id); mv_put_u32(s, g->first_member); mv_put_u32(s, g->n_members);
        mv_put_f64(s, g->click_x); mv_put_f64(s, g->click_y); mv_put_f64(s, g->speed_cap);
    }
    mv_put_u32(s, ms->n_group_members);
    for (k = 0; k < ms->n_group_members && k < OM_MOVE_MAX_GROUP_MEMBERS; k++) mv_put_u32(s, ms->group_members[k]);
    mv_put_u64(s, ms->last_synced_tick);
    mv_put_u32(s, ms->period_seen);
    mv_put_u32(s, ms->terrain_epoch);
    mv_put_u32(s, ms->n_queue);
    for (k = 0; k < ms->n_queue && k < OM_MOVE_MAX_QUEUE; k++) {
        const om_move_queue_entry *q = &ms->queue[k];
        mv_put_i32(s, q->in_use);
        mv_put_u64(s, q->tick);
        mv_put_i32(s, q->kind);
        mv_put_u32(s, q->unit_id);
        mv_put_f64(s, q->x); mv_put_f64(s, q->y);
    }
    mv_put_f64(s, ms->canvas_w); mv_put_f64(s, ms->canvas_h);
    for (k = 0; k < OM_TP__COUNT; k++) mv_put_f64(s, ms->param[k]);
    mv_put_i32(s, ms->lay_any);
    mv_put_u32(s, ms->reach_n);
    for (k = 0; k < ms->reach_n && k < OM_PP_REACH_MAX; k++) {
        mv_put_i32(s, ms->reach_type[k]);
        mv_put_u32(s, ms->reach_up[k]);
        mv_put_u32(s, ms->reach_down[k]);
    }
    mv_put_u32(s, ms->kind_n);
    for (k = 0; k < ms->kind_n && k < OM_PP_REACH_MAX; k++) {
        mv_put_i32(s, ms->kind_type[k]);
        mv_put_i32(s, ms->kind_val[k]);
    }
}
static uint32_t om_move_save_size(const om_world *w) {
    const om_move_state *ms = (const om_move_state *)w->move_state;
    mv_sw s = { NULL, 0 };
    if (!ms) return 0;
    mv_save_all(ms, &s);
    return s.pos;
}
static void om_move_save_write(const om_world *w, uint8_t *out) {
    const om_move_state *ms = (const om_move_state *)w->move_state;
    mv_sw s = { out, 0 };
    if (ms) mv_save_all(ms, &s);
}

typedef struct {
    const uint8_t *p;
    uint32_t len, pos;
    int ok;
} mv_sr;
static uint64_t mv_get(mv_sr *r, uint32_t width) {
    uint64_t v = 0;
    uint32_t i;
    if (!r->ok || width > r->len - r->pos) {
        r->ok = 0;
        return 0;
    }
    for (i = 0; i < width; i++) v |= ((uint64_t)r->p[r->pos + i]) << (OM_SAVE_BYTE_BITS * i);
    r->pos += width;
    return v;
}
static uint32_t mv_get_u32(mv_sr *r) { return (uint32_t)mv_get(r, sizeof(uint32_t)); }
static int32_t mv_get_i32(mv_sr *r) { return (int32_t)mv_get(r, sizeof(int32_t)); }
static uint64_t mv_get_u64(mv_sr *r) { return mv_get(r, sizeof(uint64_t)); }
static double mv_get_f64(mv_sr *r) {
    uint64_t bits = mv_get_u64(r);
    double v;
    memcpy(&v, &bits, sizeof v);
    return v;
}
static uint32_t mv_get_count(mv_sr *r, uint32_t cap) {
    uint32_t n = mv_get_u32(r);
    if (n > cap) {
        r->ok = 0;
        return 0;
    }
    return n;
}
static int om_move_save_read(om_world *w, const uint8_t *buf, uint32_t len) {
    mv_sr r;
    om_move_state *ms;
    uint32_t id, k, nu;
    if (len == 0) return 0;
    if (!buf) return 1;
    r.p = buf; r.len = len; r.pos = 0; r.ok = 1;
    ms = (om_move_state *)calloc(1, sizeof(om_move_state));
    if (!ms) return 1;
    for (k = 0; k < OM_STEERING_SWEEP_COUNT; k++) {
        om_move_sincos_approx(OM_STEERING_SWEEP_ANGLES[k], &ms->sweep_sin[k], &ms->sweep_cos[k]);
    }
    ms->discovery_max = mv_get_count(&r, OM_MOVE_MAX_UNITS - 1);
    nu = ms->discovery_max;
    for (id = 1; id <= nu && r.ok; id++) {
        om_move_unit *mu = &ms->units[id];
        mu->in_use = mv_get_i32(&r);
        if (!mu->in_use) continue;
        mu->unit_id = mv_get_u32(&r);
        if (mu->unit_id != id) r.ok = 0;
        mu->x = mv_get_f64(&r); mu->y = mv_get_f64(&r);
        mu->pushed_x = mv_get_f64(&r); mu->pushed_y = mv_get_f64(&r);
        mu->facing = mv_get_f64(&r);
        mu->prev_x = mv_get_f64(&r); mu->prev_y = mv_get_f64(&r); mu->prev_facing = mv_get_f64(&r);
        mu->has_dest = mv_get_i32(&r);
        mu->giveup_near = mv_get_u32(&r);
        mu->dest_x = mv_get_f64(&r); mu->dest_y = mv_get_f64(&r);
        mu->direct_move = mv_get_i32(&r);
        mu->group_id = mv_get_u32(&r);
        mu->speed_cap = mv_get_f64(&r);
        mu->engaged = mv_get_i32(&r);
        mu->kiting = mv_get_i32(&r);
        mu->kite_target = mv_get_u32(&r);
        mu->order_kind = mv_get_i32(&r);
        mu->native_speed = mv_get_f64(&r);
        mu->deflecting = mv_get_i32(&r);
        mu->deflect_heading = mv_get_f64(&r);
        mu->deflect_origin_x = mv_get_f64(&r); mu->deflect_origin_y = mv_get_f64(&r);
        mu->waiting = mv_get_i32(&r);
        mu->detour_remaining = mv_get_f64(&r); mu->detour_dx = mv_get_f64(&r); mu->detour_dy = mv_get_f64(&r);
        for (k = 0; k < OM_MAX_FACTIONS; k++) mu->visible[k] = mv_get_i32(&r);
        mu->plan_valid = mv_get_i32(&r);
        mu->plan_epoch = mv_get_u32(&r);
        mu->plan_layer = mv_get_u32(&r);
        mu->plan_dest_x = mv_get_f64(&r); mu->plan_dest_y = mv_get_f64(&r);
        mu->aim_x = mv_get_f64(&r); mu->aim_y = mv_get_f64(&r);
        mu->aim_is_waypoint = mv_get_i32(&r);
        mu->routed = mv_get_i32(&r);
        mu->lay_state = mv_get_i32(&r);
        mu->lay_has_pend = mv_get_i32(&r);
        mu->lay_route = mv_get_i32(&r);
        mu->transit = mv_get_i32(&r);
        mu->lay_to = mv_get_u32(&r); mu->lay_pend = mv_get_u32(&r);
        mu->lay_t = mv_get_u32(&r); mu->lay_dur = mv_get_u32(&r);
        mu->transit_home = mv_get_u32(&r);
        mu->route_n = (uint16_t)mv_get_count(&r, OM_MOVE_WALK_PTS);
        mu->route_i = (uint16_t)mv_get_count(&r, OM_MOVE_WALK_PTS);
        mu->route_ends_at_goal = (uint8_t)mv_get_count(&r, 1);
        if (mu->route_n ? mu->route_i >= mu->route_n : mu->route_i != 0) r.ok = 0;
        if (r.ok && mu->route_n > 1 && !om_move_route_tables(ms)) r.ok = 0;
        for (k = 1; k < mu->route_n && r.ok; k++) {
            ms->route_cx[id][k] = (uint16_t)mv_get_count(&r, OM_TERRAIN_MAX_CELLS - 1);
            ms->route_cy[id][k] = (uint16_t)mv_get_count(&r, OM_TERRAIN_MAX_CELLS - 1);
        }
    }
    ms->n_groups = mv_get_count(&r, OM_MOVE_MAX_GROUPS);
    ms->next_group_id = mv_get_u32(&r);
    for (k = 0; k < ms->n_groups && r.ok; k++) {
        om_move_group *g = &ms->groups[k];
        g->active = mv_get_i32(&r);
        g->id = mv_get_u32(&r); g->first_member = mv_get_u32(&r); g->n_members = mv_get_u32(&r);
        g->click_x = mv_get_f64(&r); g->click_y = mv_get_f64(&r); g->speed_cap = mv_get_f64(&r);
    }
    ms->n_group_members = mv_get_count(&r, OM_MOVE_MAX_GROUP_MEMBERS);
    for (k = 0; k < ms->n_group_members && r.ok; k++) ms->group_members[k] = mv_get_u32(&r);
    ms->last_synced_tick = mv_get_u64(&r);
    ms->period_seen = mv_get_u32(&r);
    ms->terrain_epoch = mv_get_u32(&r);
    ms->n_queue = mv_get_count(&r, OM_MOVE_MAX_QUEUE);
    for (k = 0; k < ms->n_queue && r.ok; k++) {
        om_move_queue_entry *q = &ms->queue[k];
        q->in_use = mv_get_i32(&r);
        q->tick = mv_get_u64(&r);
        q->kind = mv_get_i32(&r);
        q->unit_id = mv_get_u32(&r);
        q->x = mv_get_f64(&r); q->y = mv_get_f64(&r);
    }
    ms->canvas_w = mv_get_f64(&r); ms->canvas_h = mv_get_f64(&r);
    for (k = 0; k < OM_TP__COUNT; k++) ms->param[k] = mv_get_f64(&r);
    ms->lay_any = mv_get_i32(&r);
    ms->reach_n = mv_get_count(&r, OM_PP_REACH_MAX);
    for (k = 0; k < ms->reach_n && r.ok; k++) {
        ms->reach_type[k] = mv_get_i32(&r);
        ms->reach_up[k] = mv_get_u32(&r);
        ms->reach_down[k] = mv_get_u32(&r);
    }
    ms->kind_n = mv_get_count(&r, OM_PP_REACH_MAX);
    for (k = 0; k < ms->kind_n && r.ok; k++) {
        ms->kind_type[k] = mv_get_i32(&r);
        ms->kind_val[k] = mv_get_i32(&r);
    }
    if (!r.ok || r.pos != len) {
        om_move_state_free_fn(ms);
        return 1;
    }
    if (w->move_state && w->move_state_free) w->move_state_free(w->move_state);
    w->move_state = ms;
    w->move_state_free = om_move_state_free_fn;
    return 0;
}
static void om_move_set_save_hooks(om_world *w) {
    w->move_state_size = om_move_save_size;
    w->move_state_write = om_move_save_write;
    w->move_state_read = om_move_save_read;
}
void om_move_install_net_hooks(om_world *w) {
    w->net_section_hash[OM_MV_SECTION] = om_move_section_hash;
    om_move_set_save_hooks(w);
}
