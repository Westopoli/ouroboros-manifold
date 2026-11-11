/* csrc/walk_route.c -- terrain stage 2 (spec 2026-10-06): least-time routes for walking units.
 * Part A (planner-a): single-layer Dijkstra over the unit's walk mask. Part B (planner-b) writes below the marker.
 * With no terrain generated the canvas is all open (every cell walkable, flat), although the contract mask is 0 there.
 * VG-W1 (visible-game spec Lane W W1, Rev 12b and 12c): still pure Dijkstra with today's settle order, so every route and
 * every seconds value is unchanged; only the cost changes. One static scratch (dist, prev, heap and the per-cell edge
 * tables below) is allocated on the first call and reused. The walk-mask copy and its popcount, the cell-centre height
 * cache (cm) and the per-cell edge tables built from them (which neighbours a step may take, and whether each rises, falls
 * or is flat) are rebuilt only when the cache key (world pointer, terrain gen_id, terrain_epoch, layer, cells_w, cells_h)
 * changes. The sim is single-threaded per world, so one scratch serves every call.
 * F1 (R-097-01, R-207-05, R-190-07): a mapgen box, wall, building or dense obstacle cell is closed to the router on the unit's layer, with or
 * without terrain, so a walker goes round it (before F1 the router saw only the walk mask, and no mask at all without terrain). The cells
 * come from om_move_route_cell_blocked, the same definition the walker's step is held to (csrc/move_commit.c); any change to them bumps the
 * epoch in the cache key.
 * See also: tests/csim/test_VG_W_w1_planner.py; csrc/tactical_move.c om_move_terrain_epoch, the epoch getter. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "move_commit.h"

#ifndef OM_WALK_OPEN_CAP
#define OM_WALK_OPEN_CAP 65536u /* provisional (2026-10-06): planner open-set cap, nodes */
#endif
#define WR_Q16_ONE 65536.0
#define WR_Q16_DIAG 92682.0           /* Q16 sqrt 2 */
#define WR_INF INT64_MAX
#define WR_NONE UINT32_MAX
#define WR_HALF 0.5
#define WR_NEIGHBOURS 8
#define WR_KINDS 3 /* flat, rising, falling */
#define WR_STEPS 2 /* straight, diagonal */
#define WR_KIND_BITS 2 /* bits a neighbour's kind takes in the per-cell kinds word */
#define WR_KIND_MASK 3u
/* spec Lane W W1 names OM_WALK_CELLS_MAX, absent on main, value 280 * 280 from om_internal.h:437 */
#define OM_WALK_CELLS_MAX ((uint32_t)OM_TERRAIN_MAX_CELLS * OM_TERRAIN_MAX_CELLS)
#define WR_CM_PER_WU 100.0 /* TG_CM_PER_WU in csrc/terrain.c: om_terrain_height_at returns cm / 100 */

void om_move_get_canvas_size(om_world *w, double *width, double *height); /* csrc/tactical_move.c */

static const int wr_dxs[WR_NEIGHBOURS] = {-1, 0, 1, -1, 1, -1, 0, 1};
static const int wr_dys[WR_NEIGHBOURS] = {-1, -1, -1, 0, 0, 1, 1, 1};

typedef struct {
    int64_t d;
    uint32_t cell;
} wr_node;

typedef struct {
    int64_t dist;
    uint32_t prev;
    uint32_t settled; /* 1 once popped with its final dist */
} wr_cell;

typedef struct {
    wr_cell *cell;
    wr_node *heap; /* open set: a binary heap on (dist, cell index), a total order; an improved cell leaves a stale entry */
    uint32_t *touched; /* cells given a dist this call; the end of the call resets them */
    uint32_t hn, tn, open_n;
} wr_ctx;

#define WR_HEAP_CAP (2u * OM_WALK_CELLS_MAX) /* heap entries: an improved dist adds one, the stale one is skipped at pop */

/* The one static scratch. mask, hcm, allow and kinds belong to the cache key below; cell, heap and touched are per call. */
static struct {
    wr_cell *cell;
    wr_node *heap;
    uint32_t *touched;
    uint8_t *mask;    /* copy of the unit layer's walk mask (terrain only) */
    int32_t *hcm;     /* cell-centre height in cm (terrain only) */
    uint8_t *allow;   /* per cell: bit k set when a step to neighbour k is open (in bounds, walkable, no corner cut) */
    uint16_t *kinds;  /* per cell: WR_KIND_BITS per neighbour, 0 flat, 1 rising, 2 falling */
    int keyed;
    const om_world *key_w;
    uint32_t key_gen, key_epoch, key_cw, key_ch, count;
    uint64_t key_serial;
    int key_layer;
} wr_scr;

static int wr_scratch_alloc(void) {
    uint32_t i;
    if (wr_scr.cell) return 1;
    wr_scr.cell = (wr_cell *)malloc(sizeof(wr_cell) * OM_WALK_CELLS_MAX);
    wr_scr.heap = (wr_node *)malloc(sizeof(wr_node) * WR_HEAP_CAP);
    wr_scr.touched = (uint32_t *)malloc(sizeof(uint32_t) * OM_WALK_CELLS_MAX);
    wr_scr.mask = (uint8_t *)malloc(OM_WALK_CELLS_MAX);
    wr_scr.hcm = (int32_t *)malloc(sizeof(int32_t) * OM_WALK_CELLS_MAX);
    wr_scr.allow = (uint8_t *)malloc(OM_WALK_CELLS_MAX);
    wr_scr.kinds = (uint16_t *)malloc(sizeof(uint16_t) * OM_WALK_CELLS_MAX);
    if (wr_scr.cell && wr_scr.heap && wr_scr.touched && wr_scr.mask && wr_scr.hcm && wr_scr.allow && wr_scr.kinds) {
        /* between calls every dist is WR_INF, every prev WR_NONE and nothing settled; a call resets the cells it touched */
        for (i = 0; i < OM_WALK_CELLS_MAX; i++) { wr_scr.cell[i].dist = WR_INF; wr_scr.cell[i].prev = WR_NONE; wr_scr.cell[i].settled = 0; }
        return 1;
    }
    free(wr_scr.cell); free(wr_scr.heap); free(wr_scr.touched); free(wr_scr.mask); free(wr_scr.hcm); free(wr_scr.allow); free(wr_scr.kinds);
    memset(&wr_scr, 0, sizeof(wr_scr));
    return 0;
}

/* Branch-free: a data-dependent branch here mispredicts about half the time and the heap is most of the planner's cost. */
static int wr_before(const wr_node *a, const wr_node *b) {
    return (a->d < b->d) | ((a->d == b->d) & (a->cell < b->cell));
}

static void wr_up(wr_ctx *c, uint32_t i, wr_node x) {
    while (i > 0 && wr_before(&x, &c->heap[(i - 1) / 2])) {
        c->heap[i] = c->heap[(i - 1) / 2];
        i = (i - 1) / 2;
    }
    c->heap[i] = x;
}

static void wr_down(wr_ctx *c, uint32_t i, wr_node x) {
    uint32_t l;
    while ((l = 2 * i + 1) < c->hn) {
        if (l + 1 < c->hn) l += (uint32_t)wr_before(&c->heap[l + 1], &c->heap[l]);
        if (!wr_before(&c->heap[l], &x)) break;
        c->heap[i] = c->heap[l];
        i = l;
    }
    c->heap[i] = x;
}

/* Full: drop the stale entries (a settled cell's, or one whose dist has since improved) and rebuild. What is left is at most
 * one entry per open cell, so at most OM_WALK_CELLS_MAX of the WR_HEAP_CAP. */
static void wr_compact(wr_ctx *c) {
    uint32_t i, n = 0;
    for (i = 0; i < c->hn; i++) {
        const wr_node e = c->heap[i];
        if (!c->cell[e.cell].settled && c->cell[e.cell].dist == e.d) c->heap[n++] = e;
    }
    c->hn = n;
    for (i = n / 2; i > 0; i--) wr_down(c, i - 1, c->heap[i - 1]);
}

static void wr_push(wr_ctx *c, int64_t d, uint32_t cell) {
    wr_node x;
    if (c->hn == WR_HEAP_CAP) wr_compact(c);
    x.d = d; x.cell = cell;
    c->hn++;
    wr_up(c, c->hn - 1, x);
}

/* The keys are totally ordered, so the cells settle in the same order whatever the heap's layout (today's: dist, then the
 * lower cell index). Pops until an entry is current (cell not settled, dist as pushed) and returns its cell, WR_NONE when the
 * heap runs dry. The root's hole sinks along the smaller children to a leaf (one compare a level), the last entry floats up. */
static uint32_t wr_pop(wr_ctx *c) {
    while (c->hn > 0) {
        wr_node top = c->heap[0];
        c->hn--;
        if (c->hn > 0) {
            wr_node x = c->heap[c->hn];
            uint32_t i = 0, l;
            while ((l = 2 * i + 1) < c->hn) {
                if (l + 1 < c->hn) l += (uint32_t)wr_before(&c->heap[l + 1], &c->heap[l]);
                c->heap[i] = c->heap[l];
                i = l;
            }
            wr_up(c, i, x);
        }
        if (!c->cell[top.cell].settled && c->cell[top.cell].dist == top.d) return top.cell;
    }
    return WR_NONE;
}

/* Heights in cm, one per cell centre, from om_terrain_height_at: at a cell centre the bilinear lookup is the stored cm
 * height, so the double is cm / 100 and h * 100 rounds back to the exact cm; two heights compare as doubles exactly as
 * their cm integers do, so h1 > h0 and h1 < h0 are unchanged. */
static int32_t wr_height_fill(const om_world *w, uint32_t cell, uint32_t cw) {
    double h = om_terrain_height_at(w, ((double)(cell % cw) + WR_HALF) * OM_TERRAIN_CELL_WU,
                                    ((double)(cell / cw) + WR_HALF) * OM_TERRAIN_CELL_WU) * WR_CM_PER_WU;
    return (int32_t)(h < 0.0 ? h - WR_HALF : h + WR_HALF);
}

/* The edge tables, once per cache key: which of a cell's eight steps are open and whether each rises, falls or is flat.
 * Exactly the old per-edge tests: in bounds, the neighbour walkable, a diagonal not cutting a corner (mask NULL = all open),
 * the kind from the two cell-centre heights (hcm NULL = flat).
 * See also: tests/csim/test_E01_T2_walker_no_corner_cut.py */
static void wr_edges_fill(uint32_t cw, uint32_t ch, const uint8_t *mask, const int32_t *hcm) {
    uint32_t cx, cy, k;
    for (cy = 0; cy < ch; cy++) for (cx = 0; cx < cw; cx++) {
        uint32_t cur = cy * cw + cx, kinds = 0;
        unsigned allow = 0;
        for (k = 0; k < WR_NEIGHBOURS; k++) {
            int64_t nx = (int64_t)cx + wr_dxs[k], ny = (int64_t)cy + wr_dys[k];
            uint32_t nb;
            int32_t h0, h1;
            unsigned kind;
            if (nx < 0 || ny < 0 || nx >= (int64_t)cw || ny >= (int64_t)ch) continue;
            nb = (uint32_t)(ny * (int64_t)cw + nx);
            if (mask && !mask[nb]) continue;
            if (mask && wr_dxs[k] && wr_dys[k] &&
                (!mask[cy * cw + (uint32_t)nx] || !mask[(uint32_t)ny * cw + cx])) continue;
            h0 = hcm ? hcm[cur] : 0;
            h1 = hcm ? hcm[nb] : 0;
            kind = h1 > h0 ? 1u : (h1 < h0 ? 2u : 0u);
            allow |= 1u << k;
            kinds |= kind << (WR_KIND_BITS * k);
        }
        wr_scr.allow[cur] = (uint8_t)allow;
        wr_scr.kinds[cur] = (uint16_t)kinds;
    }
}

int om_walk_route(const om_world *w, uint32_t unit, double gx, double gy, double *pts, uint32_t cap, double *seconds) {
    wr_ctx c;
    uint32_t n_cells, start, goal, final_cell, i, k, count, layer_i;
    double ux, uy, speed, up_div, down_mult, cost[WR_KINDS][WR_STEPS], sx, sy;
    int64_t step_q[WR_KINDS][WR_STEPS]; /* cost rounded to whole Q16 seconds, as the relax step added it */
    int64_t gcx, gcy, ncx, ncy;
    int32_t off[WR_NEIGHBOURS];
    int terrain, layer;
    uint32_t cw = 0, ch = 0, gen, epoch;
    uint64_t serial;
    int ret = -1;

    if (seconds) *seconds = 0.0;
    if (!w || om_unit_get_pos(w, unit, &ux, &uy) != 1) return -1;
    terrain = om_terrain_present(w);
    n_cells = terrain ? om_terrain_cells(w, &cw, &ch) : 0;
    if (!terrain) {
        double cvw, cvh;
        om_move_get_canvas_size((om_world *)w, &cvw, &cvh);
        cw = (uint32_t)(cvw / OM_TERRAIN_CELL_WU);
        ch = (uint32_t)(cvh / OM_TERRAIN_CELL_WU);
        n_cells = cw * ch;
    }
    if (n_cells == 0 || n_cells > OM_WALK_CELLS_MAX) return -1;
    layer = (int)om_unit_get_layer(w, unit);
    if (layer < 0) layer = 0;
    if (!wr_scratch_alloc()) return -1;
    gen = terrain ? ((const om_terrain_state *)w->terrain_state)->gen_id : 0;
    epoch = om_move_terrain_epoch((om_world *)w);
    serial = om_move_world_serial((om_world *)w);
    if (!(wr_scr.keyed && wr_scr.key_w == w && wr_scr.key_serial == serial && wr_scr.key_gen == gen && wr_scr.key_epoch == epoch && wr_scr.key_layer == layer &&
          wr_scr.key_cw == cw && wr_scr.key_ch == ch)) {
        wr_scr.keyed = 0;
        wr_scr.count = 0;
        if (terrain) {
            if (om_terrain_walk_mask(w, layer, wr_scr.mask, n_cells) != n_cells) return -1;
            for (i = 0; i < n_cells; i++) wr_scr.mask[i] = (uint8_t)(wr_scr.mask[i] && !om_move_route_cell_blocked(w, (uint32_t)layer, (int32_t)(i % cw), (int32_t)(i / cw)));
            for (i = 0; i < n_cells; i++) wr_scr.count += wr_scr.mask[i] ? 1u : 0u;
            for (i = 0; i < n_cells; i++) wr_scr.hcm[i] = wr_height_fill(w, i, cw);
        } else {
            for (i = 0; i < n_cells; i++) wr_scr.mask[i] = (uint8_t)!om_move_route_cell_blocked(w, (uint32_t)layer, (int32_t)(i % cw), (int32_t)(i / cw));
        }
        wr_edges_fill(cw, ch, wr_scr.mask, terrain ? wr_scr.hcm : NULL);
        wr_scr.key_w = w; wr_scr.key_serial = serial; wr_scr.key_gen = gen; wr_scr.key_epoch = epoch; wr_scr.key_layer = layer;
        wr_scr.key_cw = cw; wr_scr.key_ch = ch;
        wr_scr.keyed = 1;
    }
    if (terrain && wr_scr.count == 0) return -1;
    speed = om_unit_effective_speed((om_world *)w, unit);
    up_div = om_tactical_get_param(w, OM_TP_SLOPE_UP_DIV);
    down_mult = om_tactical_get_param(w, OM_TP_SLOPE_DOWN_MULT);
    if (!(speed > 0.0) || !(up_div > 0.0) || !(down_mult > 0.0)) return -1;
    /* cost[0] flat, [1] rising, [2] falling; [.][0] straight, [.][1] diagonal; Q16 seconds */
    for (k = 0; k < WR_STEPS; k++) {
        double base = (k ? WR_Q16_DIAG : WR_Q16_ONE) * OM_TERRAIN_CELL_WU;
        cost[0][k] = base / speed;
        cost[1][k] = base / (speed / up_div);
        cost[2][k] = base / (speed * down_mult);
    }
    for (i = 0; i < WR_KINDS; i++) for (k = 0; k < WR_STEPS; k++) step_q[i][k] = (int64_t)(cost[i][k] + WR_HALF);
    for (k = 0; k < WR_NEIGHBOURS; k++) off[k] = wr_dys[k] * (int32_t)cw + wr_dxs[k];
    c.cell = wr_scr.cell; c.heap = wr_scr.heap; c.touched = wr_scr.touched;
    c.hn = 0; c.tn = 0; c.open_n = 1;

    sx = ux / OM_TERRAIN_CELL_WU; sy = uy / OM_TERRAIN_CELL_WU;
    ncx = (int64_t)(sx < 0.0 ? 0.0 : sx); ncy = (int64_t)(sy < 0.0 ? 0.0 : sy);
    if (ncx >= (int64_t)cw) ncx = (int64_t)cw - 1;
    if (ncy >= (int64_t)ch) ncy = (int64_t)ch - 1;
    start = (uint32_t)(ncy * (int64_t)cw + ncx);
    gcx = (int64_t)(gx < 0.0 ? 0.0 : gx / OM_TERRAIN_CELL_WU); gcy = (int64_t)(gy < 0.0 ? 0.0 : gy / OM_TERRAIN_CELL_WU);
    if (gcx >= (int64_t)cw) gcx = (int64_t)cw - 1;
    if (gcy >= (int64_t)ch) gcy = (int64_t)ch - 1;
    goal = (uint32_t)(gcy * (int64_t)cw + gcx);

    c.cell[start].dist = 0;
    c.touched[c.tn++] = start;
    wr_push(&c, 0, start);
    for (;;) {
        uint32_t cur = wr_pop(&c);
        if (cur == WR_NONE) break;
        c.cell[cur].settled = 1;
        c.open_n--;
        const unsigned allow = wr_scr.allow[cur];
        const unsigned kinds = wr_scr.kinds[cur];
        if (cur == goal) break;
        for (k = 0; k < WR_NEIGHBOURS; k++) {
            uint32_t nb;
            int64_t nd;
            if (!((allow >> k) & 1u)) continue;
            nb = cur + (uint32_t)off[k];
            /* A settled cell can never improve (every step costs >= 0), so the old late "already settled" skip is
             * hoisted here: the same edges are relaxed. */
            if (c.cell[nb].settled) continue;
            nd = c.cell[cur].dist + step_q[(kinds >> (WR_KIND_BITS * k)) & WR_KIND_MASK][wr_dxs[k] && wr_dys[k] ? 1 : 0];
            if (nd < c.cell[nb].dist) {
                if (c.cell[nb].dist == WR_INF) {
                    if (c.open_n >= OM_WALK_OPEN_CAP) continue;
                    c.open_n++;
                    c.touched[c.tn++] = nb;
                }
                c.cell[nb].dist = nd; c.cell[nb].prev = cur;
                wr_push(&c, nd, nb);
            }
        }
    }

    if (c.cell[goal].settled) {
        final_cell = goal;
    } else {
        int64_t best = WR_INF;
        final_cell = start;
        for (i = 0; i < n_cells; i++) {
            int64_t dx, dy, d;
            if (!c.cell[i].settled) continue;
            dx = (int64_t)(i % cw) - gcx; dy = (int64_t)(i / cw) - gcy;
            d = dx * dx + dy * dy;
            if (d < best) { best = d; final_cell = i; }
        }
    }
    if (final_cell == start) { ret = 0; goto out; }
    count = 1;
    for (i = final_cell; i != start; i = c.cell[i].prev) count++;
    ret = (int)count;
    if (count > cap || !pts) goto done;
    layer_i = count;
    for (i = final_cell; ; i = c.cell[i].prev) {
        layer_i--;
        pts[2 * layer_i] = ((double)(i % cw) + WR_HALF) * OM_TERRAIN_CELL_WU;
        pts[2 * layer_i + 1] = ((double)(i / cw) + WR_HALF) * OM_TERRAIN_CELL_WU;
        if (i == start) break;
    }
    pts[0] = ux; pts[1] = uy;
    if (final_cell == goal) { pts[2 * (count - 1)] = gx; pts[2 * (count - 1) + 1] = gy; }
done:
    if (seconds) *seconds = (double)c.cell[final_cell].dist / WR_Q16_ONE;
out:
    for (i = 0; i < c.tn; i++) { wr_cell *q = &c.cell[c.touched[i]]; q->dist = WR_INF; q->prev = WR_NONE; q->settled = 0; }
    return ret;
}

/* ---- slope links ---- */
