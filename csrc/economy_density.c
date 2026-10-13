/* csrc/economy_density.c -- VG E1q-field: settlement density field (R-193-01, R-193-06, R-193-08; Q-166-02; Q-193-07 (a); Q-222-01 a).
 * Ported from scenes/mockups/settlement/settlement_sim.gd (S) and scenes/mockups/landscape/field_map.gd (FM), read-only, as of
 * ff2ed55f. Grid: density_side x density_side cells of OM_TERRAIN_CELL_WU (100 wu), one per terrain cell, side from om_terrain_cells.
 * P (reach) and D (eased density) are saved and hashed with the frontier `active` and `core_cell`; the derived grids
 * (elev_cm, water, wdist, slope_q, lane, lot_at) are rebuilt by om_density_rebuild_inputs at init and at the end of a load.
 * Deliberate departure: the mockup holds P and D as float32; the port uses doubles, truncated through q16() each growth step.
 * Not ported: the Q-168-05 base cap is not enforced (flagged, spec rev 8). Plain double arithmetic, fabs and fmin only. */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include "om_constants.h"
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define OM_DENSITY_RING_TICKS 60   /* liberty 2026-10-10: 3 s at OM_TACTICAL_TICK_RATE 20; S:10 TICK_S 3.0 */
#define OM_DENSITY_Q16_ONE 65536.0 /* Q16 fixed-point scale, 2^16 */
#define CM_PER_WU 100.0            /* named literal: terrain heights are cm, the mockup's are wu */
#define WDIST_NONE 255             /* S:150, 156: cells farther from water than WDIST_CAP */
#define WDIST_CAP 8                /* S:166: the water-distance BFS stops expanding at depth 8 */
#define WATER_NEAR_CELLS 3         /* S:15, 190 */
#define LANE_PERIOD 4              /* S:41, 89 */
#define LANE_PHASE 3               /* S:89: LANE_PERIOD - 1 */
#define SLOPE_NORM 6.25            /* FM:380-402: PEAK_HEIGHT_WU * 0.25 / (SPACING * 2) */
#define SLOPE_Q_MAX 65535          /* uint16 slope_q cannot hold 1.0 in Q16 (65536); a slope of 1 is stored as 65535 (liberty 2026-10-10) */
#define BASE_DECAY 0.99            /* S:8 */
#define DIAG_DECAY 0.99            /* S:183 */
#define WATER_CROSS 0.85           /* S:14, 185 */
#define CLIMB_WU 900.0             /* S:7, 187 */
#define CLIMB_CLAMP 0.8            /* S:187 */
#define CLIMB_HALF 0.5             /* S:187 */
#define STEEP_W 0.25               /* S:188 */
#define NONWATER_FAR 0.99          /* S:10, 190 */
#define P_EPS 0.0005               /* S:225 */
#define P_MIN 0.02                 /* S:225 */
#define EASE 0.35                  /* S:16, 235 */
#define M_START 0.6                /* S:17, 194 */
#define M_FULL_TICKS (300.0 * 20.0) /* S:18, 194: M_FULL_S 300 s at 20 Hz */

static double q16(double v) { return (double)(int64_t)(v * OM_DENSITY_Q16_ONE) / OM_DENSITY_Q16_ONE; }

double om_density_at(const om_world *w, double x, double y) {
    if (!w || !w->economy.density_present || w->economy.density_side == 0) return 0.0;
    double canvas = (double)w->economy.density_side * OM_TERRAIN_CELL_WU;
    if (!(x >= 0.0) || !(y >= 0.0) || x >= canvas || y >= canvas) return 0.0;
    uint32_t cx = (uint32_t)(x / OM_TERRAIN_CELL_WU), cy = (uint32_t)(y / OM_TERRAIN_CELL_WU);
    return w->economy.density[cy * w->economy.density_side + cx];
}

/* S:150-171: Chebyshev distance to the nearest water cell by 8-neighbour BFS, depth WDIST_CAP, WDIST_NONE beyond. */
static void build_wdist(om_economy_state *e, uint32_t side, uint32_t *queue) {
    uint32_t n = side * side, head = 0, tail = 0;
    for (uint32_t i = 0; i < n; i++) {
        if (e->water[i]) { e->wdist[i] = 0; queue[tail++] = i; }
        else e->wdist[i] = WDIST_NONE;
    }
    while (head < tail) {
        uint32_t i = queue[head++];
        uint32_t d = e->wdist[i];
        if (d >= WDIST_CAP) continue;
        int cx = (int)(i % side), cy = (int)(i / side);
        for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++) {
                int nx = cx + dx, ny = cy + dy;
                if (nx < 0 || ny < 0 || nx >= (int)side || ny >= (int)side) continue;
                uint32_t j = (uint32_t)ny * side + (uint32_t)nx;
                if (e->wdist[j] == WDIST_NONE) { e->wdist[j] = (uint8_t)(d + 1); queue[tail++] = j; }
            }
    }
}

/* FM:380-402: mean |dh| over the orthogonal neighbours that exist, in wu per terrain cell, over SLOPE_NORM, clamped to 1, in Q16. */
static void build_slope(om_economy_state *e, uint32_t side) {
    for (uint32_t gy = 0; gy < side; gy++)
        for (uint32_t gx = 0; gx < side; gx++) {
            uint32_t i = gy * side + gx;
            int64_t sum = 0;
            int count = 0;
            int64_t h = e->elev_cm[i];
            if (gx > 0) { int64_t d = h - e->elev_cm[i - 1]; sum += d < 0 ? -d : d; count++; }
            if (gx < side - 1) { int64_t d = h - e->elev_cm[i + 1]; sum += d < 0 ? -d : d; count++; }
            if (gy > 0) { int64_t d = h - e->elev_cm[i - side]; sum += d < 0 ? -d : d; count++; }
            if (gy < side - 1) { int64_t d = h - e->elev_cm[i + side]; sum += d < 0 ? -d : d; count++; }
            double s = count > 0 ? (double)sum / (double)count / CM_PER_WU / OM_TERRAIN_CELL_WU / SLOPE_NORM : 0.0;
            if (s > 1.0) s = 1.0;
            int64_t q = (int64_t)(s * OM_DENSITY_Q16_ONE);
            e->slope_q[i] = (uint16_t)(q > SLOPE_Q_MAX ? SLOPE_Q_MAX : q);
        }
}

/* Builds the derived grids from the terrain; returns the side, or 0 when the terrain is absent, not square or too big.
 * from_table: lot_at is rebuilt from the lot table (load, set_heights); at init the table is about to be reset, so it starts empty. */
static uint32_t build_inputs(om_world *w, int from_table) {
    om_economy_state *e = &w->economy;
    uint32_t cw = 0, ch = 0;
    if (!om_terrain_present(w) || om_terrain_cells(w, &cw, &ch) == 0) return 0;
    if (cw != ch || cw == 0 || cw > OM_DENSITY_MAX_SIDE) return 0;
    uint32_t side = cw, n = side * side;
    if (om_terrain_get_heights(w, e->elev_cm, n) != n) return 0;
    uint32_t *queue = malloc((size_t)n * sizeof(uint32_t));
    if (!queue) return 0;
    for (uint32_t i = 0; i < n; i++) {
        e->water[i] = e->elev_cm[i] < 0 ? 1 : 0;
        uint32_t gx = i % side, gy = i / side;
        e->lane[i] = (gx % LANE_PERIOD == LANE_PHASE || gy % LANE_PERIOD == LANE_PHASE) ? 1 : 0;
        e->lot_at[i] = -1;
    }
    build_wdist(e, side, queue);
    free(queue);
    build_slope(e, side);
    if (from_table) {
        uint32_t nl = om_lot_count(w);
        for (uint32_t k = 0; k < nl; k++) {
            om_lot l;
            if (om_lot_get_at(w, k, &l) != 0 || !(l.x >= 0.0) || !(l.y >= 0.0)) continue;
            uint32_t gx = (uint32_t)(l.x / OM_TERRAIN_CELL_WU), gy = (uint32_t)(l.y / OM_TERRAIN_CELL_WU);
            if (gx < side && gy < side) e->lot_at[gy * side + gx] = (int32_t)k;
        }
    }
    return side;
}

/* Called by om_terrain_set_heights and at the end of a load (save.c). Rebuilds the derived grids; clears the field when the
 * terrain is missing or its cell dimensions differ from density_side. See also: the K-e5 paragraph of docs/architecture.md. */
void om_density_rebuild_inputs(om_world *w) {
    om_economy_state *e;
    if (!w) return;
    e = &w->economy;
    if (!e->density_present) return;
    if (build_inputs(w, 1) != e->density_side) {
        e->density_present = 0;
        e->n_active = 0;
        memset(e->density, 0, sizeof e->density);
        memset(e->P, 0, sizeof e->P);
    }
}

void om_density_init(om_world *w) {
    om_economy_state *e;
    om_vec2 c;
    if (!w) return;
    e = &w->economy;
    memset(e->density, 0, sizeof e->density);
    memset(e->P, 0, sizeof e->P);
    memset(e->active, 0, sizeof e->active);
    e->density_present = 0;
    e->density_side = 0;
    e->n_active = 0;
    e->core_cell = 0;
    e->next_lot_id = 1; /* K-e5: nothing numbers lots from it yet (the old code uses n_lots + 1); E1q-lots moves this to om_lots_init */
    if (om_era_kind(w) != 1 || !om_terrain_present(w)) return;
    if (!om_objective_get_center(w, 0, &c)) return; /* Q-193-07 (a): the core is the mission objective */
    uint32_t side = build_inputs(w, 0);
    if (side == 0) return;
    uint32_t gx = c.x > 0.0 ? (uint32_t)(c.x / OM_TERRAIN_CELL_WU) : 0, gy = c.y > 0.0 ? (uint32_t)(c.y / OM_TERRAIN_CELL_WU) : 0;
    if (gx >= side) gx = side - 1;
    if (gy >= side) gy = side - 1;
    e->density_side = side;
    e->core_cell = gy * side + gx;
    e->P[e->core_cell] = 1.0;
    e->active[0] = e->core_cell;
    e->n_active = 1;
    e->density_present = 1;
}

/* S:180-191 */
static double factor(const om_economy_state *e, uint32_t i, uint32_t j, int diag) {
    double f = BASE_DECAY;
    if (diag) f *= DIAG_DECAY;
    if (e->water[j]) return f * WATER_CROSS;
    int64_t dh = (int64_t)e->elev_cm[j] - (int64_t)e->elev_cm[i];
    double de = fabs((double)dh) / CM_PER_WU / CLIMB_WU;
    f *= 1.0 - fmin(de, CLIMB_CLAMP) * CLIMB_HALF;
    f *= 1.0 - STEEP_W * ((double)e->slope_q[j] / OM_DENSITY_Q16_ONE);
    if (e->wdist[j] > WATER_NEAR_CELLS) f *= NONWATER_FAR;
    return f;
}

void om_density_step(om_world *w, uint64_t tick) {
    if (!w || !w->economy.density_present || (tick % OM_DENSITY_RING_TICKS) != 0) return;
    om_economy_state *e = &w->economy;
    uint32_t side = e->density_side, n = side * side;
    /* K-e3: the target reads the economy sampled once at om_economy_init, not the live region. */
    double econ = e->density_economy / (double)OM_FIELD_MAX;
    if (econ < 0.0) econ = 0.0;
    if (econ > 1.0) econ = 1.0;
    double mt = (double)tick / M_FULL_TICKS;
    double mat = M_START + (1.0 - M_START) * fmin(1.0, mt); /* S:193-194 */

    uint32_t *next = malloc((size_t)n * sizeof(uint32_t));
    uint8_t *queued = calloc(n, 1);
    if (!next || !queued) { free(next); free(queued); return; }
    uint32_t nn = 0;
    /* S:210-236: in place, active in stored order, dy then dx over -1..1 (NW N NE W E SW S SE) */
    for (uint32_t k = 0; k < e->n_active; k++) {
        uint32_t i = e->active[k];
        int cx = (int)(i % side), cy = (int)(i / side);
        for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++) {
                if (dx == 0 && dy == 0) continue;
                int nx = cx + dx, ny = cy + dy;
                if (nx < 0 || ny < 0 || nx >= (int)side || ny >= (int)side) continue;
                uint32_t j = (uint32_t)ny * side + (uint32_t)nx;
                double v = e->P[i] * factor(e, i, j, dx != 0 && dy != 0);
                if (v > e->P[j] + P_EPS && v > P_MIN) {
                    e->P[j] = v;
                    if (!queued[j]) { queued[j] = 1; next[nn++] = j; }
                }
            }
    }
    memcpy(e->active, next, (size_t)nn * sizeof(uint32_t));
    e->n_active = nn;
    free(next);
    free(queued);
    /* S:195-199 row-major; the econ term is Q-222-01 (a), not in the mockup. Q16 truncation keeps a save mid-growth equal to a straight run. */
    for (uint32_t i = 0; i < n; i++) {
        if (e->P[i] <= 0.0) continue;
        double tgt = fmin(1.0, e->P[i] * mat * econ);
        if (tgt > e->density[i]) e->density[i] += (tgt - e->density[i]) * EASE;
        e->density[i] = q16(e->density[i]);
        e->P[i] = q16(e->P[i]);
    }
}
