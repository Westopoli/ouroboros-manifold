/* csrc/economy_place.c -- VG E1e, E1r: the placement entry (R-168-01, R-193-03, R-218-05).
 * R-193-03 (E1r): placing clears the natural lots under the 5 x 5 footprint (om_lots_remove_row); the ring around it refills by
 * the ordinary lot step; a placed building still refuses a placed one within E1E_SPAN cells (DRAFT-place-on-placed, Q-168-06 (a)).
 * See also: csrc/economy_lots.c, tests/csim/test_VG_E_e1r.py. */
#include "ouroboros_sim.h"
#include "economy_internal.h"
#include <stddef.h>
#include <math.h>

/* liberty 2026-10-10: 100 wu cells, 5x5 footprint (half 2), as the settlement mockup; the 2-cell ring is ring only
 * and not checked; E1r clears natural lots under the footprint and leaves the ring's. Q-168-05 base cap is open: not enforced. */
#define E1E_CELL 100.0
#define E1E_HALF 2
/* om_economy_place return codes: accepted, no world, footprint on unwalkable ground, too close to a placed lot, lot table full. */
#define E1E_OK 0
#define E1E_NO_WORLD 1
#define E1E_UNWALKABLE 2
#define E1E_OVERLAP 3
#define E1E_FULL 4
/* a placed lot within this many cells of the target cell is an overlap */
#define E1E_SPAN (2 * E1E_HALF)

static int32_t e1e_cell(double v) { return (int32_t)floor(v / E1E_CELL); }

int om_economy_place(om_world *w, int32_t building, double x, double y) {
    int32_t cx, cy, dx, dy;
    uint32_t i, cleared = 0;
    om_economy_state *e;
    if (!w) return E1E_NO_WORLD;
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
            return E1E_OK;
        }
    }
    for (dx = -E1E_HALF; dx <= E1E_HALF; dx++)
        for (dy = -E1E_HALF; dy <= E1E_HALF; dy++)
            if (!om_terrain_walkable_at(w, (cx + dx + 0.5) * E1E_CELL, (cy + dy + 0.5) * E1E_CELL)) return E1E_UNWALKABLE;
    /* pass 1, refusals only: DRAFT-place-on-placed (Q-168-06 default (a)): a placed lot (owner >= 0) within E1E_SPAN cells refuses;
     * a natural lot (owner < 0, building 0) never does. A lot is placed when its owner is >= 0 or its building is != 0; it is natural when its owner is < 0
     * and its building is 0. Natural lots always carry building 0 (lot_try_create), so a placed lot in a fixture with no mission
     * (owner -1, as test_VG_E_e1e.py's world_factory(n_regions=1)) is still placed and is never cleared (Architect 2026-10-21).
     * E1E_FULL counts the lots the clearing frees first (gap full (a)). */
    for (i = 0; i < e->n_lots; i++) {
        int32_t lx = e1e_cell(e->lots[i].x), ly = e1e_cell(e->lots[i].y);
        if (e->lots[i].owner < 0 && e->lots[i].building == 0) {
            if (lx - cx >= -E1E_HALF && lx - cx <= E1E_HALF && ly - cy >= -E1E_HALF && ly - cy <= E1E_HALF) cleared++;
            continue;
        }
        if (lx - cx >= -E1E_SPAN && lx - cx <= E1E_SPAN && ly - cy >= -E1E_SPAN && ly - cy <= E1E_SPAN) return E1E_OVERLAP;
    }
    if (e->n_lots - cleared + 1 > OM_LOT_CAP) return E1E_FULL;
    /* pass 2, after every refusal: clear the natural lots under the footprint, walking down so rows do not skip. */
    for (i = e->n_lots; i-- > 0;) {
        int32_t lx = e1e_cell(e->lots[i].x), ly = e1e_cell(e->lots[i].y);
        if (e->lots[i].owner < 0 && e->lots[i].building == 0 && lx - cx >= -E1E_HALF && lx - cx <= E1E_HALF && ly - cy >= -E1E_HALF && ly - cy <= E1E_HALF)
            om_lots_remove_row(w, i);
    }
    {
        om_lot *l = &e->lots[e->n_lots];
        l->id = e->next_lot_id++; /* E1q-lots: the same counter as natural lots; n_lots duplicated an id */
        l->x = (cx + 0.5) * E1E_CELL;
        l->y = (cy + 0.5) * E1E_CELL;
        l->stage = 0;
        l->building = building;
        l->owner = om_player_faction(w);
        e->n_lots++;
    }
    return E1E_OK;
}
