/* csrc/economy_place.c -- VG E1e: the placement entry (R-168-01, R-193-03, R-218-05). */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include <stddef.h>
#include <math.h>

/* liberty 2026-10-10: 100 wu cells, 5x5 footprint (half 2), as the settlement mockup; the 2-cell ring is ring only
 * and not checked. Q-168-05 base cap is open: not enforced. */
#define E1E_CELL 100.0
#define E1E_HALF 2

static int32_t e1e_cell(double v) { return (int32_t)floor(v / E1E_CELL); }

int om_economy_place(om_world *w, int32_t building, double x, double y) {
    int32_t cx, cy, dx, dy;
    uint32_t i;
    om_economy_state *e;
    if (!w) return 1;
    e = &w->economy;
    cx = e1e_cell(x);
    cy = e1e_cell(y);
    /* liberty 2026-10-10: a rubble strongpoint at the cell is refounded regardless of lots (R-218-05). */
    for (i = 0; i < e->n_strongpoints; i++) {
        om_strongpoint *sp = &e->strongpoints[i];
        if (sp->state == 2 && e1e_cell(sp->x) == cx && e1e_cell(sp->y) == cy) {
            int32_t pf = om_player_faction(w);
            om_structure_refound(w, sp->id, pf);
            sp->owner = pf;
            sp->state = 1;
            return 0;
        }
    }
    for (dx = -E1E_HALF; dx <= E1E_HALF; dx++)
        for (dy = -E1E_HALF; dy <= E1E_HALF; dy++)
            if (!om_terrain_walkable_at(w, (cx + dx + 0.5) * E1E_CELL, (cy + dy + 0.5) * E1E_CELL)) return 2;
    for (i = 0; i < e->n_lots; i++) {
        int32_t lx = e1e_cell(e->lots[i].x), ly = e1e_cell(e->lots[i].y);
        if (lx - cx >= -2 * E1E_HALF && lx - cx <= 2 * E1E_HALF && ly - cy >= -2 * E1E_HALF && ly - cy <= 2 * E1E_HALF) return 3;
    }
    if (e->n_lots >= OM_LOT_CAP) return 4;
    {
        om_lot *l = &e->lots[e->n_lots];
        l->id = e->n_lots;
        l->x = (cx + 0.5) * E1E_CELL;
        l->y = (cy + 0.5) * E1E_CELL;
        l->stage = 0;
        l->building = building;
        l->owner = om_player_faction(w);
        e->n_lots++;
    }
    return 0;
}
