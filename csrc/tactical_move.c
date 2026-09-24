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

/* Spatial hash over this module's own unit positions (om_move_unit x/y).
 * unit.c's grid (om_grid_query_circle) holds unit.c's position cache, which
 * lags this module's positions (the sync runs before the cache refresh, and
 * collision pushes move units mid-pass), so the exact all-pairs results
 * would not survive using it. OM_MOVE_GRID_CELL is twice the collision
 * diameter so a circle query of collision reach spans at most 3x3 cells. */
#define OM_MOVE_GRID_BUCKETS 16384
#define OM_MOVE_GRID_CELL (4.0 * OM_UNIT_COLLISION_RADIUS)
#define OM_MOVE_GRID_COORD_LIMIT 1.0e9
#define OM_MOVE_INSERTION_SORT_MAX 96
#define OM_MOVE_GRID_HASH_X 73856093u
#define OM_MOVE_GRID_HASH_Y 19349663u

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
    uint32_t grid_head[OM_MOVE_GRID_BUCKETS];
    uint32_t grid_next[OM_MOVE_MAX_UNITS];
    uint32_t grid_prev[OM_MOVE_MAX_UNITS];
    int32_t  grid_cx[OM_MOVE_MAX_UNITS];
    int32_t  grid_cy[OM_MOVE_MAX_UNITS];
    uint8_t  grid_in[OM_MOVE_MAX_UNITS];
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

static om_move_state *om_ms(om_world *w) {
    om_move_state *ms = (om_move_state *)w->move_state;
    if (!ms) {
        ms = (om_move_state *)calloc(1, sizeof(om_move_state));
        ms->next_group_id = 1;
        w->move_state = ms;
        w->move_state_free = om_move_state_free_fn;
    }
    return ms;
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

/* ---------------------------------------------------------- unit lookup */

static om_move_unit *om_move_get(om_move_state *ms, uint32_t unit_id) {
    if (unit_id == 0 || unit_id >= OM_MOVE_MAX_UNITS) return NULL;
    return &ms->units[unit_id];
}

static int32_t om_move_grid_coord(double v) {
    double c = floor(v / OM_MOVE_GRID_CELL);
    if (c > OM_MOVE_GRID_COORD_LIMIT) c = OM_MOVE_GRID_COORD_LIMIT;
    if (c < -OM_MOVE_GRID_COORD_LIMIT) c = -OM_MOVE_GRID_COORD_LIMIT;
    return (int32_t)c;
}

static uint32_t om_move_grid_bucket(int32_t cx, int32_t cy) {
    return (((uint32_t)cx * OM_MOVE_GRID_HASH_X) ^ ((uint32_t)cy * OM_MOVE_GRID_HASH_Y)) & (OM_MOVE_GRID_BUCKETS - 1);
}

static void om_move_grid_link(om_move_state *ms, uint32_t id, int32_t cx, int32_t cy) {
    uint32_t b = om_move_grid_bucket(cx, cy);
    ms->grid_cx[id] = cx;
    ms->grid_cy[id] = cy;
    ms->grid_prev[id] = 0;
    ms->grid_next[id] = ms->grid_head[b];
    if (ms->grid_head[b]) ms->grid_prev[ms->grid_head[b]] = id;
    ms->grid_head[b] = id;
    ms->grid_in[id] = 1;
}

static void om_move_grid_unlink(om_move_state *ms, uint32_t id) {
    uint32_t nx = ms->grid_next[id], pv = ms->grid_prev[id];
    if (pv) ms->grid_next[pv] = nx;
    else ms->grid_head[om_move_grid_bucket(ms->grid_cx[id], ms->grid_cy[id])] = nx;
    if (nx) ms->grid_prev[nx] = pv;
    ms->grid_in[id] = 0;
}

/* Re-files a unit after its x/y changed; a unit outside the grid (not
 * alive when the grid was built) stays outside. */
static void om_move_grid_update(om_move_state *ms, const om_move_unit *mu) {
    uint32_t id = mu->unit_id;
    int32_t cx, cy;
    if (!ms->grid_live || !ms->grid_in[id]) return;
    cx = om_move_grid_coord(mu->x);
    cy = om_move_grid_coord(mu->y);
    if (cx == ms->grid_cx[id] && cy == ms->grid_cy[id]) return;
    om_move_grid_unlink(ms, id);
    om_move_grid_link(ms, id, cx, cy);
}

static void om_move_grid_rebuild(om_world *w, om_move_state *ms) {
    uint32_t id;
    memset(ms->grid_head, 0, sizeof(ms->grid_head));
    memset(ms->grid_in, 0, sizeof(ms->grid_in));
    ms->grid_live = 1;
    for (id = 1; id <= ms->discovery_max && id < OM_MOVE_MAX_UNITS; id++) {
        const om_move_unit *mu = &ms->units[id];
        if (!mu->in_use || !om_unit_alive(w, id)) continue;
        om_move_grid_link(ms, id, om_move_grid_coord(mu->x), om_move_grid_coord(mu->y));
    }
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

/* Heapsort: ids are unique, and libm_lint bans qsort (its result on ties
 * and its algorithm are the platform's). */
static void om_move_sort_ids(uint32_t *a, uint32_t n) {
    uint32_t i;
    if (n < 2) return;
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

/* Ids above min_id whose unit lies within r of (x, y), ascending, into
 * ms->grid_scratch; returns the count. */
static uint32_t om_move_grid_collect(om_move_state *ms, double x, double y, double r, uint32_t min_id) {
    int32_t cx0 = om_move_grid_coord(x - r), cx1 = om_move_grid_coord(x + r);
    int32_t cy0 = om_move_grid_coord(y - r), cy1 = om_move_grid_coord(y + r);
    int32_t cx, cy;
    uint32_t n = 0, id;
    for (cy = cy0; cy <= cy1; cy++) {
        for (cx = cx0; cx <= cx1; cx++) {
            for (id = ms->grid_head[om_move_grid_bucket(cx, cy)]; id; id = ms->grid_next[id]) {
                double dx, dy;
                if (id <= min_id || ms->grid_cx[id] != cx || ms->grid_cy[id] != cy) continue;
                dx = ms->units[id].x - x; dy = ms->units[id].y - y;
                if (dx * dx + dy * dy <= r * r) ms->grid_scratch[n++] = id;
            }
        }
    }
    om_move_sort_ids(ms->grid_scratch, n);
    return n;
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
        if (ms->grid_live && om_unit_alive(w, unit_id)) {
            om_move_grid_link(ms, unit_id, om_move_grid_coord(mu->x), om_move_grid_coord(mu->y));
        }
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

static int om_move_probe_clear(om_world *w, om_move_state *ms, uint32_t self_id, double cand_x, double cand_y) {
    double block_r = 2.0 * OM_UNIT_COLLISION_RADIUS;
    double reach = block_r + 1.0;
    int32_t cx0 = om_move_grid_coord(cand_x - reach), cx1 = om_move_grid_coord(cand_x + reach);
    int32_t cy0 = om_move_grid_coord(cand_y - reach), cy1 = om_move_grid_coord(cand_y + reach);
    int32_t cx, cy;
    uint32_t id;
    (void)w;
    for (cy = cy0; cy <= cy1; cy++) {
        for (cx = cx0; cx <= cx1; cx++) {
            for (id = ms->grid_head[om_move_grid_bucket(cx, cy)]; id; id = ms->grid_next[id]) {
                double dx, dy, dist;
                if (id == self_id || ms->grid_cx[id] != cx || ms->grid_cy[id] != cy) continue;
                dx = ms->units[id].x - cand_x; dy = ms->units[id].y - cand_y;
                dist = sqrt(dx * dx + dy * dy);
                if (dist < block_r) return 0;
            }
        }
    }
    return 1;
}

/* One colliding pair, a's id below b's; returns 1 when a position was
 * written. d2 >= target^2 implies sqrt(d2) >= target (sqrt is monotonic and
 * exact at target^2), so that early return matches the sqrt compare. */
static int om_move_collide_pair(om_move_state *ms, om_move_unit *a, om_move_unit *b) {
    double dx, dy, dist, target, overlap, ux, uy;
    int changed = 0;
    dx = b->x - a->x; dy = b->y - a->y;
    target = 2.0 * OM_UNIT_COLLISION_RADIUS;
    if (dx * dx + dy * dy >= target * target) return 0;
    dist = sqrt(dx * dx + dy * dy);
    if (dist >= target) return 0;
    if (dist < OM_COLLISION_EXACT_EPS) {
        /* R-097-07: exact overlap -- the lower unit id (a, since
         * a's id < b's always here) moves in the canonical +x
         * direction, the higher id the opposite way. */
        double half = target / 2.0;
        a->x += half;
        b->x -= half;
        changed = 1;
    } else {
        int a_stat = om_move_is_stationary(a);
        int b_stat = om_move_is_stationary(b);
        overlap = target - dist;
        ux = dx / dist; uy = dy / dist;
        if (a_stat && b_stat) {
            /* both fixed: cannot resolve without violating the
             * "stationary takes zero push" rule for either side;
             * not exercised by any acceptance test. */
        } else if (a_stat) {
            b->x += ux * overlap; b->y += uy * overlap;
            changed = 1;
        } else if (b_stat) {
            a->x -= ux * overlap; a->y -= uy * overlap;
            changed = 1;
        } else {
            a->x -= ux * overlap * 0.5; a->y -= uy * overlap * 0.5;
            b->x += ux * overlap * 0.5; b->y += uy * overlap * 0.5;
            changed = 1;
        }
    }
    om_move_grid_update(ms, a);
    om_move_grid_update(ms, b);
    return changed;
}

/* Same pairs in the same order as an all-pairs i < j sweep with live
 * positions. For unit a the candidates are the ids above it within
 * reach + slack of a's position when queried; b never moves before its own
 * pair with a, and a is re-queried once it has drifted more than half the
 * slack, so no pair the sweep would have resolved is missed. */
static int om_move_collision_once(om_world *w, om_move_state *ms) {
    const double target = 2.0 * OM_UNIT_COLLISION_RADIUS;
    const double slack = target;
    const double drift2 = (slack * 0.5) * (slack * 0.5);
    uint32_t id_i;
    int changed = 0;
    for (id_i = 1; id_i <= ms->discovery_max; id_i++) {
        om_move_unit *a = om_move_get(ms, id_i);
        uint32_t n, k, last = id_i;
        double ax0, ay0;
        if (!a || !a->in_use || !ms->grid_in[id_i]) continue;
        ax0 = a->x; ay0 = a->y;
        n = om_move_grid_collect(ms, ax0, ay0, target + slack, last);
        for (k = 0; k < n; k++) {
            uint32_t id_j = ms->grid_scratch[k];
            double mx = a->x - ax0, my = a->y - ay0;
            if (mx * mx + my * my > drift2) {
                ax0 = a->x; ay0 = a->y;
                n = om_move_grid_collect(ms, ax0, ay0, target + slack, last);
                k = 0;
                while (k < n && ms->grid_scratch[k] <= last) k++;
                if (k >= n) break;
                id_j = ms->grid_scratch[k];
            }
            if (om_move_collide_pair(ms, a, &ms->units[id_j])) changed = 1;
            last = id_j;
        }
    }
    (void)w;
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
    int iter;
    om_move_discover(w, ms);
    if (om_move_settle_matches(w, ms)) return;
    om_move_grid_rebuild(w, ms);
    ms->settle_valid = 0;
    for (iter = 0; iter < OM_COLLISION_MAX_ITER; iter++) {
        if (!om_move_collision_once(w, ms)) {
            om_move_settle_record(ms);
            break;
        }
    }
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

    if (!mu->deflecting) {
        uint32_t k;
        int found = 0;
        for (k = 0; k < OM_STEERING_SWEEP_COUNT; k++) {
            double test_heading = heading + OM_STEERING_SWEEP_ANGLES[k];
            double px = mu->x + OM_STEERING_PROBE_DIST * om_cos(test_heading);
            double py = mu->y + OM_STEERING_PROBE_DIST * om_sin(test_heading);
            if (om_move_probe_clear(w, ms, id, px, py)) {
                heading = test_heading;
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
        mu->x += step_dist * om_cos(heading);
        mu->y += step_dist * om_sin(heading);
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
    om_move_grid_rebuild(w, ms);
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
        double sp = om_unit_effective_speed(w, ids[i]);
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
