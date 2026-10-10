/* csrc/economy_lots.c -- VG lane E1: lot table getters, lot stages by density (E1c), placement entry (stub; E1e fills it).
 * lots_tick below is the E1c step; it is reached only once E1i wires it into the tactical tick (this piece owns no other file). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>

/* liberty 2026-10-07: R-193-05 stage thresholds (Q-193-02), the settlement block, its street spacing and the pacing. */
#define LOT_T1 0.10
#define LOT_T2 0.22
#define LOT_T3 0.38
#define LOT_T4 0.58
#define LOT_BLOCK 10 /* liberty 2026-10-07: settlement block is 10x10 density cells at the canvas centre */
#define LOT_STREET 3 /* liberty 2026-10-07: every third column and row is left open (R-193-09) */
#define LOT_APPEAR_TICKS 10 /* liberty 2026-10-07: one new lot per 10 ticks */
#define LOT_RISE_TICKS 20 /* liberty 2026-10-07: a lot rises one stage per 20 ticks */

static int32_t lot_target(double d) {
    return 1 + (d >= LOT_T1) + (d >= LOT_T2) + (d >= LOT_T3) + (d >= LOT_T4);
}

/* Lot k-th candidate cell: row-major over the block, skipping street columns and rows. Returns 0 when k is past the end. */
static int lot_cell(uint32_t k, int *cx, int *cy) {
    int a, b;
    uint32_t n = 0;
    int c0 = (OM_DENSITY_SIDE - LOT_BLOCK) / 2;
    for (b = 0; b < LOT_BLOCK; b++)
        for (a = 0; a < LOT_BLOCK; a++) {
            if (a % LOT_STREET == 0 || b % LOT_STREET == 0) continue;
            if (n++ == k) { *cx = c0 + a; *cy = c0 + b; return 1; }
        }
    return 0;
}

__attribute__((unused)) /* wired by E1i */
static void lots_tick(om_world *w, uint64_t tick) {
    om_economy_state *e = &w->economy;
    uint32_t i;
    int cx, cy;
    if (tick % LOT_APPEAR_TICKS == 0 && e->n_lots < OM_LOT_CAP && lot_cell(e->n_lots, &cx, &cy)) {
        om_lot *l = &e->lots[e->n_lots];
        l->id = e->n_lots + 1;
        l->x = cx * 200.0 + 100.0;
        l->y = cy * 200.0 + 100.0;
        l->stage = 1;
        l->building = 0;
        l->owner = -1;
        e->n_lots++;
    }
    if (tick % LOT_RISE_TICKS != 0) return;
    for (i = 0; i < e->n_lots; i++) {
        int32_t t = lot_target(om_density_at(w, e->lots[i].x, e->lots[i].y));
        if (e->lots[i].stage >= 1 && e->lots[i].stage < t) e->lots[i].stage++;
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

int om_economy_place(om_world *w, int32_t building, double x, double y) {
    (void)w;
    (void)building;
    (void)x;
    (void)y;
    return 0;
}
