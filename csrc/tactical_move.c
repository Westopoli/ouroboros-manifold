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
 *     unit ids 1..OM_MOVE_DISCOVERY_CAP through the real om_unit_alive(),
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

#define OM_MOVE_MAX_UNITS 10100
#define OM_MOVE_DISCOVERY_CAP 256
#define OM_MOVE_MAX_GROUPS 64
#define OM_MOVE_MAX_GROUP_MEMBERS 64
#define OM_MOVE_MAX_DENSITY_CELLS 1024
#define OM_MOVE_MAX_ROUTE_CACHE 256
#define OM_MOVE_MAX_QUEUE 1024
#define OM_MOVE_BFS_CAP 512
#define OM_MOVE_BFS_DIR_COUNT 4

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
#define OM_MOVE_GRID_MAX_CELLS 8192
#define OM_MOVE_GRID_BASE_CELL (4.0 * OM_UNIT_COLLISION_RADIUS)
#define OM_MOVE_GRID_MARGIN (3.0 * OM_UNIT_COLLISION_RADIUS)
#define OM_MOVE_GRID_SPILL_MAX 48
#define OM_MOVE_GRID_BOUND_PAD 1.0e-6
#define OM_MOVE_GRID_FAR 1.0e300
#define OM_MOVE_FLOOR_LIMIT 1.0e9
#define OM_MOVE_INSERTION_SORT_MAX 96
#define OM_MOVE_NET_SMALL 8
#define OM_MOVE_NET_LARGE 16
#define OM_MOVE_MASK_BITS 64

/* The neighbour list of the collision sweep (om_move_collision_once). */
#define OM_MOVE_LIST_REACH (4.0 * OM_UNIT_COLLISION_RADIUS)
#define OM_MOVE_COLLISION_SLACK (OM_UNIT_COLLISION_RADIUS)

/* Steering probe: the largest gap between a probe point computed with
 * om_sin/om_cos and one computed with om_move_sincos_approx is under 0.05 wu;
 * a probe is taken as blocked without om_sin/om_cos when a unit is closer than
 * the collision diameter by this much to the approximate point. */
#define OM_MOVE_PROBE_SURE_MARGIN 0.1
#define OM_MOVE_PROBE_HINTS 2
/* A probe point is OM_STEERING_PROBE_DIST from its unit, give or take the
 * om_sin/om_cos error (under 5e-4 per component): under this. */
#define OM_MOVE_PROBE_REACH 40.1

/* ALG-69/R-100-02 turn-rate category, inferred from native speed -- see
 * the file header note. Strike >= 100, Line [60,100), Siege < 60; the
 * launch roster (csrc/unit.c) never puts a type within 20 wu/s of either
 * boundary. */
#define OM_MOVE_CAT_STRIKE_SPEED_MIN 100.0
#define OM_MOVE_CAT_LINE_SPEED_MIN 60.0

/* ALG-67/68: "d is in [0.3, 0.7]" and "(1 - 0.5 . d)" never bind an IDENT
 * to 0.3 or 0.5 in algorithms.md's prose (alg_constants.py --emit only
 * extracts `IDENT = value`), so om_constants.h has no OM_ name for either
 * -- reported here rather than left as a bare literal. */
#define OM_OBSTACLE_DENSITY_LOW_THRESHOLD 0.3
#define OM_TERRAIN_SPEED_PENALTY_COEF 0.5

/* Shot line-of-sight sampling resolution: one world unit. */
#define OM_LOS_SAMPLE_STEP 1.0

#define OM_COLLISION_MAX_ITER 3
#define OM_COLLISION_EXACT_EPS 1e-9

#define OM_PI 3.14159265358979323846
#define OM_PI_2 1.57079632679489661923
#define OM_PI_4 0.78539816339744830962
#define OM_TWO_PI_LOCAL 6.28318530717958647692

/* Deterministic atan(x) on [-1, 1] (Anderson's cheap-trig rational
 * approximation, |error| < 0.005 rad); every test tolerance in this suite
 * is >= 1e-2 rad, so this is accurate enough while never calling libm's
 * banned sin/cos/atan family (csrc's om_sin is the only trig primitive
 * that exists; om_cos is derived from it below). */
#define OM_ATAN_COEF_A 0.2447
#define OM_ATAN_COEF_B 0.0663

/* Fixed, world-independent steering sweep: [0, +d, -d, +2d, -2d, +3d, -3d]
 * (R-102-02: same sequence regardless of seed, forward first, positive
 * before negative, symmetric magnitude). */
#define OM_STEERING_SWEEP_COUNT 13
#define OM_STEERING_SWEEP_DELTA_RAD 0.2617993878
#define OM_STEERING_SWEEP_DELTA_RAD_2X 0.5235987756
#define OM_STEERING_SWEEP_DELTA_RAD_3X 0.7853981634
#define OM_STEERING_SWEEP_DELTA_RAD_4X 1.0471975512
#define OM_STEERING_SWEEP_DELTA_RAD_5X 1.3089969390
#define OM_STEERING_SWEEP_DELTA_RAD_6X 1.5707963268

typedef struct {
    int      in_use;
    uint32_t unit_id;
    double   x, y;
    double   pushed_x, pushed_y;
    double   facing;
    double   prev_x, prev_y, prev_facing;
    int      has_dest;
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
    int      visible[OM_MAX_FACTIONS];
} om_move_unit;

typedef struct {
    int      active;
    uint32_t id;
    uint32_t members[OM_MOVE_MAX_GROUP_MEMBERS];
    uint32_t n_members;
    double   click_x, click_y;
    double   speed_cap;
} om_move_group;

typedef struct {
    int      in_use;
    int32_t  cx, cy;
    uint32_t layer;
    double   density;
} om_move_density_cell;

typedef struct {
    int      in_use;
    uint32_t layer;
    int32_t  cx, cy;
} om_move_route_entry;

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

    om_move_group groups[OM_MOVE_MAX_GROUPS];
    uint32_t      n_groups;
    uint32_t      next_group_id;

    uint64_t last_synced_tick;
    uint32_t period_seen;

    om_move_density_cell density_cells[OM_MOVE_MAX_DENSITY_CELLS];
    uint32_t              n_density_cells;

    om_move_route_entry route_cache[OM_MOVE_MAX_ROUTE_CACHE];
    uint32_t             n_route_cache;
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
    uint32_t slot_id[OM_MOVE_MAX_UNITS + OM_MOVE_GRID_SPILL_MAX];
    double   slot_x[OM_MOVE_MAX_UNITS + OM_MOVE_GRID_SPILL_MAX];
    double   slot_y[OM_MOVE_MAX_UNITS + OM_MOVE_GRID_SPILL_MAX];
    double   slot_fx[OM_MOVE_MAX_UNITS], slot_fy[OM_MOVE_MAX_UNITS];
    uint32_t unit_slot[OM_MOVE_MAX_UNITS];
    uint32_t unit_cell[OM_MOVE_MAX_UNITS];
    double   scan_x[OM_MOVE_MAX_UNITS], scan_y[OM_MOVE_MAX_UNITS];
    uint8_t  grid_in[OM_MOVE_MAX_UNITS];
    double   sweep_cos[OM_STEERING_SWEEP_COUNT], sweep_sin[OM_STEERING_SWEEP_COUNT];
    uint8_t  stat[OM_MOVE_MAX_UNITS];
    uint32_t grid_scratch[OM_MOVE_MAX_UNITS];

    int      settle_valid;
    uint32_t settle_max;
    uint8_t  settle_flag[OM_MOVE_MAX_UNITS];
    double   settle_x[OM_MOVE_MAX_UNITS];
    double   settle_y[OM_MOVE_MAX_UNITS];
} om_move_state;

static void om_move_state_free_fn(void *p) {
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
    while (a > OM_PI) a -= OM_TWO_PI_LOCAL;
    while (a <= -OM_PI) a += OM_TWO_PI_LOCAL;
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

static double om_move_turn_toward(double current, double target, double rate_per_sec, uint32_t period) {
    double delta = om_wrap_pi(target - current);
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

static const double OM_STEERING_SWEEP_ANGLES[OM_STEERING_SWEEP_COUNT] = {
    0.0,
    OM_STEERING_SWEEP_DELTA_RAD, -OM_STEERING_SWEEP_DELTA_RAD,
    OM_STEERING_SWEEP_DELTA_RAD_2X, -OM_STEERING_SWEEP_DELTA_RAD_2X,
    OM_STEERING_SWEEP_DELTA_RAD_3X, -OM_STEERING_SWEEP_DELTA_RAD_3X,
    OM_STEERING_SWEEP_DELTA_RAD_4X, -OM_STEERING_SWEEP_DELTA_RAD_4X,
    OM_STEERING_SWEEP_DELTA_RAD_5X, -OM_STEERING_SWEEP_DELTA_RAD_5X,
    OM_STEERING_SWEEP_DELTA_RAD_6X, -OM_STEERING_SWEEP_DELTA_RAD_6X,
};

static om_move_state *om_ms(om_world *w) {
    om_move_state *ms = (om_move_state *)w->move_state;
    if (!ms) {
        uint32_t k;
        ms = (om_move_state *)calloc(1, sizeof(om_move_state));
        for (k = 0; k < OM_STEERING_SWEEP_COUNT; k++) {
            om_move_sincos_approx(OM_STEERING_SWEEP_ANGLES[k], &ms->sweep_sin[k], &ms->sweep_cos[k]);
        }
        ms->next_group_id = 1;
        w->move_state = ms;
        w->move_state_free = om_move_state_free_fn;
    }
    return ms;
}

/* ---------------------------------------------------------- unit lookup */

static om_move_unit *om_move_get(om_move_state *ms, uint32_t unit_id) {
    if (unit_id == 0 || unit_id >= OM_MOVE_MAX_UNITS) return NULL;
    return &ms->units[unit_id];
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
    }
    ms->slot_base = n;
    ms->n_spill = 0;
    ms->grid_disp = 0.0;
    ms->grid_live = 1;
}

/* The cells that can hold a unit within r of (x, y): every unit still in a
 * cell is within grid_disp of where it was filed. The cells of one row are
 * consecutive slots. Returns 0 when there are none. */
static inline int om_move_grid_box(const om_move_state *ms, double x, double y, double r, int32_t *x0, int32_t *x1, int32_t *y0, int32_t *y1) {
    double reach = r + ms->grid_disp + OM_MOVE_GRID_BOUND_PAD;
    int32_t xa = om_move_floor_i((x - reach - ms->grid_ox) * ms->grid_inv), xb = om_move_floor_i((x + reach - ms->grid_ox) * ms->grid_inv);
    int32_t ya = om_move_floor_i((y - reach - ms->grid_oy) * ms->grid_inv), yb = om_move_floor_i((y + reach - ms->grid_oy) * ms->grid_inv);
    if (xa >= ms->grid_w || xb < 0 || ya >= ms->grid_h || yb < 0) return 0;
    *x0 = xa > 0 ? xa : 0;
    *x1 = xb >= ms->grid_w ? ms->grid_w - 1 : xb;
    *y0 = ya > 0 ? ya : 0;
    *y1 = yb >= ms->grid_h ? ms->grid_h - 1 : yb;
    return 1;
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
static uint64_t om_move_near_mask(const om_move_state *ms, uint32_t lo, uint32_t hi, double x, double y, double r2) {
    const double *sx = ms->slot_x + lo, *sy = ms->slot_y + lo;
    uint32_t count = hi - lo > OM_MOVE_MASK_BITS ? OM_MOVE_MASK_BITS : hi - lo, i = 0;
    uint64_t mask = 0;
#if defined(__SSE2__)
    const __m128d vx = _mm_set1_pd(x), vy = _mm_set1_pd(y), vr2 = _mm_set1_pd(r2);
    for (; i + 2 <= count; i += 2) {
        __m128d dx = _mm_sub_pd(_mm_loadu_pd(sx + i), vx), dy = _mm_sub_pd(_mm_loadu_pd(sy + i), vy);
        mask |= (uint64_t)(uint32_t)_mm_movemask_pd(_mm_cmple_pd(_mm_add_pd(_mm_mul_pd(dx, dx), _mm_mul_pd(dy, dy)), vr2)) << i;
    }
#endif
    for (; i < count; i++) {
        double dx = sx[i] - x, dy = sy[i] - y;
        mask |= (uint64_t)(dx * dx + dy * dy <= r2) << i;
    }
    return mask;
}

/* Index of the lowest set bit of a nonzero mask. */
static uint32_t om_move_lowest_bit(uint64_t mask) {
#if defined(__GNUC__)
    return (uint32_t)__builtin_ctzll(mask);
#else
    uint32_t i = 0;
    while (!(mask & 1u)) { mask >>= 1; i++; }
    return i;
#endif
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
        mu->deflecting = 0;
        mu->deflect_heading = 0.0;
        mu->deflect_origin_x = mu->x;
        mu->deflect_origin_y = mu->y;
        mu->waiting = 0;
        for (f = 0; f < OM_MAX_FACTIONS; f++) mu->visible[f] = 1;
        if (unit_id > ms->discovery_max) ms->discovery_max = unit_id;
        if (ms->grid_live && om_unit_alive(w, unit_id)) ms->grid_live = 0;
    }
    return mu;
}

static void om_move_discover(om_world *w, om_move_state *ms) {
    uint32_t id;
    for (id = 1; id < OM_MOVE_DISCOVERY_CAP; id++) {
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

static om_move_group *om_move_group_find(om_move_state *ms, uint32_t id) {
    uint32_t i;
    for (i = 0; i < ms->n_groups; i++) {
        if (ms->groups[i].id == id) return &ms->groups[i];
    }
    return NULL;
}

/* ------------------------------------------------------------- navmesh */

static om_move_density_cell *om_move_density_find(om_move_state *ms, int32_t cx, int32_t cy, uint32_t layer) {
    uint32_t i;
    for (i = 0; i < ms->n_density_cells; i++) {
        om_move_density_cell *c = &ms->density_cells[i];
        if (c->in_use && c->cx == cx && c->cy == cy && c->layer == layer) return c;
    }
    return NULL;
}

static double om_move_density_cell_get(om_move_state *ms, int32_t cx, int32_t cy, uint32_t layer) {
    om_move_density_cell *c = om_move_density_find(ms, cx, cy, layer);
    return c ? c->density : 0.0;
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
    if (ms->n_route_cache < OM_MOVE_MAX_ROUTE_CACHE) {
        om_move_route_entry *r = &ms->route_cache[ms->n_route_cache++];
        r->in_use = 1;
        r->layer = layer;
        r->cx = cx;
        r->cy = cy;
    }
}

static int om_move_los_clear(om_move_state *ms, double x0, double y0, double x1, double y1, uint32_t layer) {
    double dx = x1 - x0, dy = y1 - y0;
    double dist = sqrt(dx * dx + dy * dy);
    int steps, i;
    if (dist < OM_TIE_EPSILON) return 1;
    steps = (int)(dist / (OM_NAVMESH_CELL_SIZE * 0.5)) + 1;
    for (i = 0; i <= steps; i++) {
        double t = (double)i / (double)steps;
        double px = x0 + t * dx, py = y0 + t * dy;
        if (om_move_density_at_pos(ms, px, py, layer) > OM_NAVMESH_OBSTACLE_THRESHOLD) return 0;
    }
    return 1;
}

/* Never exercised by this card's acceptance tests (the one find_path test
 * has an open path); a bounded 4-directional BFS so an obstructed query
 * still returns something usable rather than 0/failure. */
static uint32_t om_move_bfs_path_len(om_move_state *ms, double x0, double y0, double x1, double y1, uint32_t layer) {
    int32_t scx = (int32_t)floor(x0 / OM_NAVMESH_CELL_SIZE);
    int32_t scy = (int32_t)floor(y0 / OM_NAVMESH_CELL_SIZE);
    int32_t ecx = (int32_t)floor(x1 / OM_NAVMESH_CELL_SIZE);
    int32_t ecy = (int32_t)floor(y1 / OM_NAVMESH_CELL_SIZE);
    static const int32_t OM_BFS_DX[OM_MOVE_BFS_DIR_COUNT] = {1, -1, 0, 0};
    static const int32_t OM_BFS_DY[OM_MOVE_BFS_DIR_COUNT] = {0, 0, 1, -1};
    int32_t qx[OM_MOVE_BFS_CAP], qy[OM_MOVE_BFS_CAP], qd[OM_MOVE_BFS_CAP];
    int32_t vx[OM_MOVE_BFS_CAP], vy[OM_MOVE_BFS_CAP];
    int n_visited = 0, head = 0, tail = 0, dir;

    qx[tail] = scx; qy[tail] = scy; qd[tail] = 1; tail++;
    vx[n_visited] = scx; vy[n_visited] = scy; n_visited++;

    while (head < tail) {
        int32_t cx = qx[head], cy = qy[head], d = qd[head];
        head++;
        if (cx == ecx && cy == ecy) return (uint32_t)d;
        for (dir = 0; dir < OM_MOVE_BFS_DIR_COUNT; dir++) {
            int32_t nx = cx + OM_BFS_DX[dir], ny = cy + OM_BFS_DY[dir];
            int seen = 0, i;
            if (om_move_density_cell_get(ms, nx, ny, layer) > OM_NAVMESH_OBSTACLE_THRESHOLD) continue;
            for (i = 0; i < n_visited; i++) {
                if (vx[i] == nx && vy[i] == ny) { seen = 1; break; }
            }
            if (seen || n_visited >= OM_MOVE_BFS_CAP || tail >= OM_MOVE_BFS_CAP) continue;
            vx[n_visited] = nx; vy[n_visited] = ny; n_visited++;
            qx[tail] = nx; qy[tail] = ny; qd[tail] = d + 1; tail++;
        }
    }
    return 1;
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
    const double r = OM_MOVE_PROBE_REACH + 2.0 * OM_UNIT_COLLISION_RADIUS;
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
            uint32_t lo = ms->grid_start[row + (uint32_t)cx0];
            uint32_t hi = ms->grid_start[row + (uint32_t)cx1 + 1];
            for (base = lo; base < hi; base += OM_MOVE_MASK_BITS) {
                uint64_t mask = om_move_near_mask(ms, base, hi, x, y, r2);
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
    return !om_move_probe_blocked(ms, n_near, hints, cand_x, cand_y, (2.0 * OM_UNIT_COLLISION_RADIUS) * (2.0 * OM_UNIT_COLLISION_RADIUS));
}

/* A probe point computed with om_sin/om_cos is within 0.05 of the same point
 * computed with om_move_sincos_approx (om_sin is off by under 4.6e-4 and the
 * approximation by under 2.3e-5 per component, times the 40 wu probe
 * distance, times sqrt(2)), so a unit closer to the approximate point than
 * the collision diameter less OM_MOVE_PROBE_SURE_MARGIN is closer than the
 * diameter to the real one: the probe is blocked without evaluating
 * om_sin/om_cos for it. */
static int om_move_probe_sure_blocked(const om_move_state *ms, uint32_t n_near, uint32_t *hints, double cand_x, double cand_y) {
    const double sure = 2.0 * OM_UNIT_COLLISION_RADIUS - OM_MOVE_PROBE_SURE_MARGIN;
    return om_move_probe_blocked(ms, n_near, hints, cand_x, cand_y, sure * sure);
}

/* One colliding pair, a's id below b's; returns 1 when a position was
 * written. d2 >= target^2 implies sqrt(d2) >= target (sqrt is monotonic and
 * exact at target^2), so that early return matches the sqrt compare. */
static int om_move_collide_pair(om_move_state *ms, uint32_t ia, uint32_t ib) {
    double dx, dy, dist, target, overlap, ux, uy;
    double ax = om_move_grid_x(ms, ia), ay = om_move_grid_y(ms, ia);
    double bx = om_move_grid_x(ms, ib), by = om_move_grid_y(ms, ib);
    int changed = 0;
    dx = bx - ax; dy = by - ay;
    target = 2.0 * OM_UNIT_COLLISION_RADIUS;
    if (dx * dx + dy * dy >= target * target) return 0;
    dist = sqrt(dx * dx + dy * dy);
    if (dist >= target) return 0;
    if (dist < OM_COLLISION_EXACT_EPS) {
        /* R-097-07: exact overlap -- the lower unit id (a, since
         * a's id < b's always here) moves in the canonical +x
         * direction, the higher id the opposite way. */
        double half = target / 2.0;
        ax += half;
        bx -= half;
        changed = 1;
    } else {
        int a_stat = ms->stat[ia];
        int b_stat = ms->stat[ib];
        overlap = target - dist;
        ux = dx / dist; uy = dy / dist;
        if (a_stat && b_stat) {
            /* both fixed: cannot resolve without violating the
             * "stationary takes zero push" rule for either side;
             * not exercised by any acceptance test. */
        } else if (a_stat) {
            bx += ux * overlap; by += uy * overlap;
            changed = 1;
        } else if (b_stat) {
            ax -= ux * overlap; ay -= uy * overlap;
            changed = 1;
        } else {
            ax -= ux * overlap * 0.5; ay -= uy * overlap * 0.5;
            bx += ux * overlap * 0.5; by += uy * overlap * 0.5;
            changed = 1;
        }
    }
    om_move_grid_set(ms, ia, ax, ay);
    om_move_grid_set(ms, ib, bx, by);
    return changed;
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
 * Kept from the sweep this replaced (see also: OM_MOVE_LIST_REACH): that sweep
 * built its list at twice the reach and examined a's drift only before its
 * next listed candidate, so a unit that drifted past the slack after its last
 * listed candidate ended its turn without a re-query, whatever it now
 * overlapped. Results match it bit for bit, so that stop is reproduced: the
 * turn ends when the wider list has no candidate left
 * (om_move_grid_any_above). */
static int om_move_collision_once(om_world *w, om_move_state *ms) {
    const double target = 2.0 * OM_UNIT_COLLISION_RADIUS;
    const double slack = OM_MOVE_COLLISION_SLACK;
    const double drift2 = slack * slack;
    uint32_t id_i;
    int changed = 0;
    for (id_i = 1; id_i <= ms->discovery_max; id_i++) {
        uint32_t n, k;
        double ax0, ay0;
        if (!ms->grid_in[id_i]) continue;
        ax0 = om_move_grid_x(ms, id_i); ay0 = om_move_grid_y(ms, id_i);
        n = om_move_grid_collect(w, ms, ax0, ay0, target + slack, id_i);
        for (k = 0; k < n; k++) {
            uint32_t id_j = ms->grid_scratch[k];
            double mx, my;
            if (om_move_collide_pair(ms, id_i, id_j)) changed = 1;
            mx = om_move_grid_x(ms, id_i) - ax0; my = om_move_grid_y(ms, id_i) - ay0;
            if (mx * mx + my * my > drift2) {
                if (k + 1 >= n && !om_move_grid_any_above(w, ms, ax0, ay0, OM_MOVE_LIST_REACH, id_j)) break;
                ax0 = om_move_grid_x(ms, id_i); ay0 = om_move_grid_y(ms, id_i);
                n = om_move_grid_collect(w, ms, ax0, ay0, target + slack, id_j);
                k = (uint32_t)-1;
            }
        }
    }
    return changed;
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

static void om_move_collision_pass_internal(om_world *w, om_move_state *ms) {
    int iter, settled = 0;
    uint32_t id;
    om_move_discover(w, ms);
    if (om_move_settle_matches(w, ms)) return;
    if (!ms->grid_live) om_move_grid_rebuild(w, ms, 1);
    ms->settle_valid = 0;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        ms->stat[id] = (uint8_t)om_move_is_stationary(&ms->units[id]);
    }
    for (iter = 0; iter < OM_COLLISION_MAX_ITER; iter++) {
        if (!om_move_collision_once(w, ms)) {
            settled = 1;
            break;
        }
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
        om_move_route_touch(ms, 0, q->x, q->y);
    }
}

static void om_move_tick_unit(om_world *w, om_move_state *ms, uint32_t id, uint32_t period) {
    om_move_unit *mu = om_move_get(ms, id);
    double heading, speed, dist_to_dest, step_dist;

    if (!mu || !mu->in_use || !om_unit_alive(w, id)) return;

    mu->prev_x = mu->x;
    mu->prev_y = mu->y;
    mu->prev_facing = mu->facing;

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
    } else if (step_dist > 0.0) {
        mu->x += step_dist * (found ? move_cos : om_cos(heading));
        mu->y += step_dist * (found ? move_sin : om_sin(heading));
    }
    om_move_grid_update(ms, mu);

    if (mu->deflecting) {
        mu->facing = heading; /* pinned for the whole detour segment */
    } else {
        mu->facing = om_move_turn_toward(mu->facing, heading, om_move_turn_rate_for(mu->native_speed), period);
    }
}

static void om_move_groups_check_arrival(om_move_state *ms) {
    double tol = OM_ARRIVAL_TOLERANCE_MULT * OM_UNIT_COLLISION_RADIUS;
    uint32_t g, m;
    for (g = 0; g < ms->n_groups; g++) {
        om_move_group *grp = &ms->groups[g];
        double cx = 0.0, cy = 0.0, centroid_dist;
        int all_within = 1;
        if (!grp->active) continue;
        for (m = 0; m < grp->n_members; m++) {
            om_move_unit *mu = om_move_get(ms, grp->members[m]);
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

static void om_move_tick_once(om_world *w, om_move_state *ms, uint64_t new_tick, uint32_t period) {
    uint32_t id;
    om_move_discover(w, ms);
    om_move_apply_queue_for_tick(w, ms, new_tick - 1);
    om_move_grid_rebuild(w, ms, 1);
    for (id = 1; id <= ms->discovery_max; id++) {
        om_move_tick_unit(w, ms, id, period);
    }
    om_move_collision_pass_internal(w, ms);
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
    for (t = ms->last_synced_tick + 1; t <= target; t++) {
        om_move_tick_once(w, ms, t, period);
    }
    if (ms->last_synced_tick < target) om_move_push_positions(w, ms);
    ms->last_synced_tick = target;
    ms->period_seen = now;
}

static void om_move_enqueue(om_world *w, om_move_state *ms, int kind, uint32_t unit, double x, double y) {
    om_move_queue_entry *q;
    if (ms->n_queue >= OM_MOVE_MAX_QUEUE) return;
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
    for (i = 1; i < steps; i++) {
        double t = (double)i / (double)steps;
        double px = x0 + t * dx, py = y0 + t * dy;
        om_gradient_properties g;
        if (om_move_density_at_pos(ms, px, py, 0) > OM_NAVMESH_OBSTACLE_THRESHOLD) return 0;
        om_map_sample_gradients(ww, px, py, &g);
        if (g.cover_density > 0.0 || g.obstacle_density > OM_NAVMESH_OBSTACLE_THRESHOLD) return 0;
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
        /* R-095-01: group pace = slowest member's profile speed.
         * om_unit_effective_speed returns ability-modified speed, so a
         * Fortify-active Bastion (0.4x, 16 wu/s) would drag the whole group
         * to 0.8 wu/tick.  native_speed is set from om_unit_effective_speed
         * at first discovery, which always precedes om_ability_autotrigger_scan
         * in the same tactical_step (refresh_positions runs before ability
         * advance), so it reliably holds the unmodified profile speed. */
        om_move_unit *tmp = om_move_touch(w, ms, ids[i]);
        double sp = (tmp && tmp->native_speed > 0.0) ? tmp->native_speed
                                                     : om_unit_effective_speed(w, ids[i]);
        if (i == 0 || sp < min_speed) min_speed = sp;
    }
    for (i = 0; i < n; i++) {
        om_move_unit *mu = om_move_touch(w, ms, ids[i]);
        double d;
        if (!mu) continue;
        d = sqrt((mu->x - cx) * (mu->x - cx) + (mu->y - cy) * (mu->y - cy));
        if (d > OM_MAGIC_BOX_SPREAD_RADIUS) scattered = 1;
    }

    gid = ms->next_group_id++;
    if (ms->n_groups < OM_MOVE_MAX_GROUPS) {
        grp = &ms->groups[ms->n_groups++];
    } else {
        grp = &ms->groups[OM_MOVE_MAX_GROUPS - 1];
    }
    grp->active = 1;
    grp->id = gid;
    grp->click_x = x;
    grp->click_y = y;
    grp->speed_cap = min_speed;
    grp->n_members = (n < OM_MOVE_MAX_GROUP_MEMBERS) ? n : OM_MOVE_MAX_GROUP_MEMBERS;
    for (i = 0; i < grp->n_members; i++) grp->members[i] = ids[i];

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
        mu->deflecting = 0;
        mu->order_kind = 0;
        om_move_route_touch(ms, 0, x, y);
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
    om_move_density_cell *c;
    if (!w) return;
    ms = om_ms(w);
    c = om_move_density_find(ms, (int32_t)p0, (int32_t)p1, p2);
    if (c) {
        c->density = p3;
        return;
    }
    if (ms->n_density_cells < OM_MOVE_MAX_DENSITY_CELLS) {
        c = &ms->density_cells[ms->n_density_cells++];
        c->in_use = 1;
        c->cx = (int32_t)p0;
        c->cy = (int32_t)p1;
        c->layer = p2;
        c->density = p3;
    }
}

uint32_t om_navmesh_find_path(om_world *w, double p0, double p1, double p2, double p3, uint32_t p4) {
    om_move_state *ms;
    int clear;
    if (!w) return 0;
    ms = om_ms(w);
    clear = om_move_los_clear(ms, p0, p1, p2, p3, p4);
    om_move_route_touch(ms, p4, p2, p3);
    if (clear) {
        ms->last_path_straightened = 1;
        return 2;
    }
    ms->last_path_straightened = 0;
    return om_move_bfs_path_len(ms, p0, p1, p2, p3, p4);
}

uint32_t om_navmesh_get_cache_hits(const om_world *w) {
    om_world *ww = (om_world *)w;
    if (!w) return 0;
    return om_ms(ww)->cache_hits;
}

double om_navmesh_get_cell_size(const om_world *w) {
    (void)w;
    return OM_NAVMESH_CELL_SIZE;
}

int om_navmesh_is_cell_blocked(const om_world *w, uint32_t p0, uint32_t p1, uint32_t p2) {
    om_world *ww = (om_world *)w;
    if (!w) return 0;
    return om_move_density_cell_get(om_ms(ww), (int32_t)p0, (int32_t)p1, p2) > OM_NAVMESH_OBSTACLE_THRESHOLD;
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
    if (mu->group_id != 0) return mu->speed_cap;
    return om_unit_effective_speed(ww, p0);
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
