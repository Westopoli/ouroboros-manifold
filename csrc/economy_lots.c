/* csrc/economy_lots.c -- VG lane E1: lot table getters, lots on the density field (E1q-lots), placement entry (E1e), area hits (E1d).
 * Port of the approved mockup scenes/mockups/settlement/settlement_sim.gd (S) at ff2ed55f; spec docs/northstar/plans/
 * 2026-10-07-visible-game-spec.md "Lane E1 part c" E1q-lots. No block and no appear timer: every LOT_RISE_TICKS the lot step
 * scans the grid by Chebyshev ring from the core and gives a stage-1 lot to every buildable cell the field has reached.
 * Reads the derived grids water, wdist, lane and slope_q and the field D that E1q-field fills; writes only lot_at.
 * om_lots_step is wired into the tactical tick by E1i. */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* S:9 THRESHOLDS: marked ground, scaffold, built, dense (R-193-05, Q-193-02). THRESHOLD_1 is also the density a cell needs for a lot. */
#define THRESHOLD_1 0.10
#define THRESHOLD_2 0.22
#define THRESHOLD_3 0.38
#define THRESHOLD_4 0.58
#define SHORE_MARGIN 1       /* S:42, buildable S:176-177: a cell needs wdist > SHORE_MARGIN */
#define CLIFF_SLOPE 0.22     /* S:25 */
#define CLIFF_MAX_STAGE 3    /* S:26 */
#define LOT_RISE_TICKS 20    /* DRAFT-lot-rise-ticks: one lot step per second; S RISE_S 0.9 is an animation time, not a pacing */
#define LOT_CELL_WU 100.0    /* S SPACING_WU 100: a lot sits at its cell centre */
#define LOT_FOOTPRINT_HALF 2 /* E1e / S PLAYER_HALF 2: the 5 x 5 footprint of a placed lot (owner >= 0) blocks natural lots */
#define LOT_Q16_ONE 65536.0  /* slope_q is stored Q16 */

static int32_t lot_threshold_count(double d) {
    return (d >= THRESHOLD_1) + (d >= THRESHOLD_2) + (d >= THRESHOLD_3) + (d >= THRESHOLD_4);
}

/* S:239-246 _target for a cell that holds a lot: thresholds passed, at most CLIFF_MAX_STAGE on a cliff. */
static int32_t lot_target(const om_economy_state *e, int32_t idx) {
    int32_t k = lot_threshold_count(e->density[idx]);
    if ((double)e->slope_q[idx] / LOT_Q16_ONE > CLIFF_SLOPE && k > CLIFF_MAX_STAGE) k = CLIFF_MAX_STAGE;
    return k;
}

/* S:176-177 buildable, without path (E2): the footprint test is derived from the lot table by the caller (blocked[]). */
static int lot_buildable(const om_economy_state *e, int32_t idx, const uint8_t *blocked) {
    return e->water[idx] == 0 && e->wdist[idx] > SHORE_MARGIN && e->lane[idx] == 0 && !blocked[idx];
}

/* Try the cell: a stage-1 lot when it is buildable, unoccupied and the field has reached THRESHOLD_1. */
static void lot_try_create(om_economy_state *e, int32_t gx, int32_t gy, int32_t side, const uint8_t *blocked) {
    int32_t idx = gy * side + gx;
    om_lot *l;
    if (e->n_lots >= OM_LOT_CAP || e->lot_at[idx] != -1 || !lot_buildable(e, idx, blocked) || e->density[idx] < THRESHOLD_1) return;
    l = &e->lots[e->n_lots];
    l->id = e->next_lot_id++;
    l->x = (gx + 0.5) * LOT_CELL_WU;
    l->y = (gy + 0.5) * LOT_CELL_WU;
    l->stage = 1;
    l->building = 0;
    l->owner = -1;
    e->lot_at[idx] = (int32_t)e->n_lots;
    e->n_lots++;
}

void om_lots_step(om_world *w, uint64_t tick) {
    om_economy_state *e = &w->economy;
    int32_t side = (int32_t)e->density_side, core_x, core_y, r, gx, gy, dx, dy;
    uint32_t i;
    if (tick % LOT_RISE_TICKS != 0 || !e->density_present || side <= 0 || side > OM_DENSITY_MAX_SIDE) return;
    {
        uint8_t blocked[OM_DENSITY_MAX_CELLS];
        memset(blocked, 0, (size_t)side * (size_t)side);
        for (i = 0; i < e->n_lots; i++) {
            if (e->lots[i].owner < 0) continue;
            gx = (int32_t)(e->lots[i].x / LOT_CELL_WU);
            gy = (int32_t)(e->lots[i].y / LOT_CELL_WU);
            for (dy = -LOT_FOOTPRINT_HALF; dy <= LOT_FOOTPRINT_HALF; dy++)
                for (dx = -LOT_FOOTPRINT_HALF; dx <= LOT_FOOTPRINT_HALF; dx++)
                    if (gx + dx >= 0 && gx + dx < side && gy + dy >= 0 && gy + dy < side) blocked[(gy + dy) * side + gx + dx] = 1;
        }
        /* a lot rises one stage per step toward its target and never falls here (E1d lowers it to rubble) */
        for (i = 0; i < e->n_lots; i++) {
            gx = (int32_t)(e->lots[i].x / LOT_CELL_WU);
            gy = (int32_t)(e->lots[i].y / LOT_CELL_WU);
            if (e->lots[i].x < 0.0 || e->lots[i].y < 0.0 || gx >= side || gy >= side) continue;
            if (e->lots[i].stage >= 1 && e->lots[i].stage < lot_target(e, gy * side + gx)) e->lots[i].stage++;
        }
        core_x = (int32_t)(e->core_cell % (uint32_t)side);
        core_y = (int32_t)(e->core_cell / (uint32_t)side);
        for (r = 0; r < side; r++) {
            for (gy = core_y - r; gy <= core_y + r; gy++) {
                int32_t step = (gy == core_y - r || gy == core_y + r) ? 1 : 2 * r;
                if (gy < 0 || gy >= side) continue;
                for (gx = core_x - r; gx <= core_x + r; gx += step) {
                    if (gx >= 0 && gx < side) lot_try_create(e, gx, gy, side, blocked);
                }
            }
        }
    }
}

uint32_t om_lot_count(const om_world *w) {
    return w ? w->economy.n_lots : 0;
}

int om_lot_get_at(const om_world *w, uint32_t i, om_lot *out) {
    if (!w || !out || i >= w->economy.n_lots) return 1;
    *out = w->economy.lots[i];
    return 0;
}

void om_lots_init(om_world *w) {
    w->economy.n_lots = 0;
    w->economy.next_lot_id = 1;
    memset(w->economy.lot_at, 0xFF, sizeof w->economy.lot_at); /* -1: no lot on any cell */
}
void om_lots_on_area_hit(om_world *w, double x, double y, double radius) {
    om_economy_state *e = &w->economy;
    uint32_t i;
    for (i = 0; i < e->n_lots; i++) {
        double dx = e->lots[i].x - x, dy = e->lots[i].y - y;
        if (dx * dx + dy * dy > radius * radius || e->lots[i].stage < 1) continue;
        e->lots[i].stage--;
        e->lot_hit_tick[i] = (uint32_t)om_tactical_tick(w);
    }
}
