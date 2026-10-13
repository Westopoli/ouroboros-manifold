/* csrc/space_field.c -- E-17 S-246 (R-246-01), E-01 R-001-04: the space mission's five open-or-blocked layers.
 * generate runs the port of scenes/mockups/landscape/field_map_space.gd: noise and plates (space_plates.c), raster and
 * carve (space_raster.c); the masks go to the route grid through om_map_set_obstacle_density (it can clear as well as set,
 * so a regenerate leaves no stale bits), and the field adds no cover obstacles. The getters and the state in om_internal.h stay.
 * See also: om_map_block_rect in csrc/tactical_mapgen.c, whose route grid mission_begin clears (om_map_clear). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include "space_internal.h"
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifdef OM_DEBUG_INJECT
#define SF_NO_CARVE(w) ((w)->inject == OM_BUG_SPACE_NO_CARVE)
#else
#define SF_NO_CARVE(w) 0
#endif
#define SF_BYTE_SHIFT 3
#define SF_BIT_MASK 7u
#define SF_BLOCKED_DENSITY 1.0 /* above OM_NAVMESH_OBSTACLE_THRESHOLD (0.7): the cell blocks (om_route_grid_is_cell_blocked) */
#define SF_OPEN_DENSITY 0.0

static int sf_centroid_blocked(const om_space_cells *cells, const om_space_plate *p) {
    double x = 0.0, y = 0.0;
    for (uint32_t c = 0; c < p->n_pts; c++) {
        x += p->xy[2u * c];
        y += p->xy[2u * c + 1u];
    }
    x /= (double)p->n_pts;
    y /= (double)p->n_pts;
    return cells->mask[p->layer][(uint32_t)(y / OM_SPACE_FIELD_CELL_WU) * OM_SPACE_FIELD_SIDE + (uint32_t)(x / OM_SPACE_FIELD_CELL_WU)] != 0;
}

/* VG-D8 R-246-07: the pocket at a node with slots needed grows by this step until its open cells hold the army; the clear
 * radius is CLEAR_RADIUS_WU (600, field_map_space.gd:23), the cap stops a pocket that cannot be made big enough. */
#define SF_CLEAR_RADIUS 600.0
#define SF_GROW_STEP 400.0
#define SF_GROW_CAP 6000.0
#define SF_OK_MARGIN 1 /* OM_MISSION_POCKET_MARGIN_CELLS in csrc/mission.c: an army cell has this many open cells round it on every layer */
#define SF_SLOTS_PER_CELL 9u /* OM_MISSION_SLOTS_PER_CELL in csrc/mission.c */

static int sf_cell_ok(const om_space_cells *cells, int32_t cx, int32_t cy) {
    const int32_t side = OM_SPACE_FIELD_SIDE, r = SF_OK_MARGIN;
    if (cx < r || cy < r || cx >= side - r || cy >= side - r) return 0;
    for (uint32_t k = 0; k < OM_SPACE_FIELD_LAYERS; k++)
        for (int32_t dy = -r; dy <= r; dy++)
            for (int32_t dx = -r; dx <= r; dx++)
                if (cells->mask[k][(cy + dy) * side + cx + dx]) return 0;
    return 1;
}

/* Open army cells within radius of (x, y). */
static uint32_t sf_pocket_cells(const om_space_cells *cells, double x, double y, double radius) {
    const int32_t side = OM_SPACE_FIELD_SIDE;
    int32_t span = (int32_t)(radius / OM_SPACE_FIELD_CELL_WU) + 1, ax = (int32_t)(x / OM_SPACE_FIELD_CELL_WU), ay = (int32_t)(y / OM_SPACE_FIELD_CELL_WU);
    uint32_t n = 0;
    for (int32_t cy = ay - span; cy <= ay + span; cy++)
        for (int32_t cx = ax - span; cx <= ax + span; cx++) {
            double dx = ((double)cx + 0.5) * OM_SPACE_FIELD_CELL_WU - x, dy = ((double)cy + 0.5) * OM_SPACE_FIELD_CELL_WU - y;
            if (cx < 0 || cy < 0 || cx >= side || cy >= side || dx * dx + dy * dy > radius * radius) continue;
            n += (uint32_t)sf_cell_ok(cells, cx, cy);
        }
    return n;
}

int om_space_field_generate_nodes(om_world *w, uint32_t seed, double canvas_w, double canvas_h, double density, const double *node_xy,
                                  const uint32_t *node_slots, uint32_t n_nodes) {
    double radius[OM_SPACE_FIELD_MAX_NODES], held_xy[2 * OM_SPACE_FIELD_MAX_NODES];
    uint32_t held_slots[OM_SPACE_FIELD_MAX_NODES];
    om_space_field_state *f;
    om_space_plates *pl;
    om_space_cells *cells;
    int rc = -1;
    if (!w || canvas_w != OM_SPACE_FIELD_CANVAS_WU || canvas_h != OM_SPACE_FIELD_CANVAS_WU) return -1;
    pl = malloc(sizeof *pl);
    cells = malloc(sizeof *cells);
    if (!pl || !cells) goto done;
    if (n_nodes < OM_SPACE_FIELD_MIN_NODES || !node_xy) { /* no nodes given: a held field of the same seed repeats its own (VG-D7 idempotence) */
        n_nodes = w->space_field.present && w->space_field.seed == seed ? w->space_field.n_nodes : 0;
        node_xy = held_xy;
        node_slots = held_slots;
        memcpy(held_xy, w->space_field.node_xy, sizeof held_xy);
        memcpy(held_slots, w->space_field.node_slots, sizeof held_slots);
    }
    if (!node_slots) { memset(held_slots, 0, sizeof held_slots); node_slots = held_slots; }
    if (n_nodes > OM_SPACE_FIELD_MAX_NODES) n_nodes = OM_SPACE_FIELD_MAX_NODES;
    if (n_nodes < OM_SPACE_FIELD_MIN_NODES) n_nodes = 0;
    memset(radius, 0, sizeof radius); /* 0 = the clear radius, space_plates.c */
    for (;;) {
        int grew = 0;
        if (om_space_plates_build_nodes(seed, canvas_w, density, node_xy, radius, n_nodes, pl) != 0 || om_space_raster(pl, OM_SPACE_FIELD_CELL_WU, cells) != 0) goto done;
        if (om_space_carve(pl, cells, OM_SPACE_OBJECTIVE_CX, OM_SPACE_OBJECTIVE_CY, SF_NO_CARVE(w)) < 0) goto done;
        for (uint32_t i = 0; i < n_nodes && node_slots; i++)
            if (node_slots[i] && radius[i] < SF_GROW_CAP &&
                sf_pocket_cells(cells, node_xy[2 * i], node_xy[2 * i + 1], radius[i] > 0.0 ? radius[i] : SF_CLEAR_RADIUS) * SF_SLOTS_PER_CELL < node_slots[i]) {
                radius[i] = (radius[i] > 0.0 ? radius[i] : SF_CLEAR_RADIUS) + SF_GROW_STEP;
                grew = 1;
            }
        if (!grew) break;
    }
    f = &w->space_field;
    memset(f, 0, sizeof *f);
    f->present = 1;
    f->seed = seed;
    f->n_nodes = n_nodes;
    memcpy(f->node_xy, node_xy, sizeof(double) * 2u * n_nodes);
    memcpy(f->node_slots, node_slots, sizeof(uint32_t) * n_nodes);
    for (uint32_t k = 0; k < OM_SPACE_FIELD_LAYERS; k++)
        for (uint32_t i = 0; i < OM_SPACE_FIELD_CELLS; i++) {
            int blocked = cells->mask[k][i] != 0;
            if (blocked) f->mask[k][i >> SF_BYTE_SHIFT] = (uint8_t)(f->mask[k][i >> SF_BYTE_SHIFT] | (1u << (i & SF_BIT_MASK)));
            om_map_set_obstacle_density(w, i % OM_SPACE_FIELD_SIDE, i / OM_SPACE_FIELD_SIDE, k,
                                        blocked ? SF_BLOCKED_DENSITY : SF_OPEN_DENSITY);
        }
    for (uint32_t n = 0; n < pl->n_plates && f->n_polys < OM_SPACE_FIELD_MAX_POLYS; n++) {
        const om_space_plate *src = &pl->plates[n];
        om_space_field_poly *p;
        if (src->dropped) continue;
        if (src->kind == OM_SPACE_KIND_RUBBLE && !sf_centroid_blocked(cells, src)) continue; /* the carve cleared it: rubble is not generated in cleared pools */
        p = &f->polys[f->n_polys++];
        p->layer = src->layer;
        p->kind = src->kind;
        p->n_pts = src->n_pts;
        memcpy(p->xy, src->xy, sizeof(double) * 2u * src->n_pts);
    }
    rc = 0;
done:
    free(pl);
    free(cells);
    return rc;
}

int om_space_field_present(const om_world *w) {
    return w && w->space_field.present;
}

uint32_t om_space_field_get_mask(const om_world *w, uint32_t layer, uint8_t *out, uint32_t cap) {
    if (!w || !out || !w->space_field.present || layer >= OM_SPACE_FIELD_LAYERS || cap < OM_SPACE_FIELD_CELLS) return 0;
    for (uint32_t i = 0; i < OM_SPACE_FIELD_CELLS; i++)
        out[i] = (uint8_t)((w->space_field.mask[layer][i >> SF_BYTE_SHIFT] >> (i & SF_BIT_MASK)) & 1u);
    return OM_SPACE_FIELD_CELLS;
}

void om_space_field_clear(om_world *w) {
    if (w) memset(&w->space_field, 0, sizeof w->space_field);
}

uint32_t om_space_field_poly_count(const om_world *w) {
    return w && w->space_field.present ? w->space_field.n_polys : 0;
}

uint32_t om_space_field_poly_get(const om_world *w, uint32_t i, uint32_t *layer, uint32_t *kind, double *xy, uint32_t cap_pts) {
    const om_space_field_poly *p;
    if (!w || !w->space_field.present || i >= w->space_field.n_polys) return 0;
    p = &w->space_field.polys[i];
    if (cap_pts < p->n_pts) return 0;
    if (layer) *layer = p->layer;
    if (kind) *kind = p->kind;
    if (xy) memcpy(xy, p->xy, sizeof(double) * 2u * p->n_pts);
    return p->n_pts;
}
