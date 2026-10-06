/* csrc/walk_route.c -- terrain stage 2 (spec 2026-10-06): least-time routes for walking units.
 * Part A (planner-a): single-layer Dijkstra over the unit's walk mask. Part B (planner-b) writes below the marker.
 * With no terrain generated the canvas is all open (every cell walkable, flat), although the contract mask is 0 there. */
#include <stdint.h>
#include <stdlib.h>
#include "ouroboros_sim.h"
#include "om_internal.h"

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

void om_move_get_canvas_size(om_world *w, double *width, double *height); /* csrc/tactical_move.c */

typedef struct {
    uint32_t cw, ch;
    const uint8_t *mask; /* NULL = all open */
    int64_t *dist;
    uint32_t *prev, *heap, *hpos;
    uint32_t hn;
} wr_ctx;

static int wr_less(const wr_ctx *c, uint32_t a, uint32_t b) {
    return c->dist[a] < c->dist[b] || (c->dist[a] == c->dist[b] && a < b);
}

static void wr_swap(wr_ctx *c, uint32_t i, uint32_t j) {
    uint32_t t = c->heap[i];
    c->heap[i] = c->heap[j];
    c->heap[j] = t;
    c->hpos[c->heap[i]] = i;
    c->hpos[c->heap[j]] = j;
}

static void wr_up(wr_ctx *c, uint32_t i) {
    while (i > 0 && wr_less(c, c->heap[i], c->heap[(i - 1) / 2])) {
        wr_swap(c, i, (i - 1) / 2);
        i = (i - 1) / 2;
    }
}

static void wr_down(wr_ctx *c, uint32_t i) {
    for (;;) {
        uint32_t l = 2 * i + 1, r = l + 1, m = i;
        if (l < c->hn && wr_less(c, c->heap[l], c->heap[m])) m = l;
        if (r < c->hn && wr_less(c, c->heap[r], c->heap[m])) m = r;
        if (m == i) return;
        wr_swap(c, i, m);
        i = m;
    }
}

static uint32_t wr_pop(wr_ctx *c) {
    uint32_t top = c->heap[0];
    c->hn--;
    if (c->hn > 0) {
        c->heap[0] = c->heap[c->hn];
        c->hpos[c->heap[0]] = 0;
        wr_down(c, 0);
    }
    c->hpos[top] = WR_NONE;
    return top;
}

static double wr_height(const om_world *w, uint32_t cell, uint32_t cw) {
    return om_terrain_height_at(w, ((double)(cell % cw) + WR_HALF) * OM_TERRAIN_CELL_WU,
                                ((double)(cell / cw) + WR_HALF) * OM_TERRAIN_CELL_WU);
}

int om_walk_route(const om_world *w, uint32_t unit, double gx, double gy, double *pts, uint32_t cap, double *seconds) {
    static const int dxs[WR_NEIGHBOURS] = {-1, 0, 1, -1, 1, -1, 0, 1};
    static const int dys[WR_NEIGHBOURS] = {-1, -1, -1, 0, 0, 1, 1, 1};
    wr_ctx c;
    uint8_t *mask = NULL;
    uint32_t n_cells, start, goal, final_cell, i, k, count, layer_i;
    double ux, uy, speed, up_div, down_mult, cost[WR_KINDS][WR_STEPS], sx, sy;
    int64_t gcx, gcy, ncx, ncy;
    int terrain, layer;
    uint32_t cw = 0, ch = 0;
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
    if (n_cells == 0) return -1;
    layer = (int)om_unit_get_layer(w, unit);
    if (layer < 0) layer = 0;
    if (terrain) {
        mask = (uint8_t *)malloc(n_cells);
        if (!mask) return -1;
        if (om_terrain_walk_mask(w, layer, mask, n_cells) != n_cells) { free(mask); return -1; }
        for (i = 0, count = 0; i < n_cells; i++) count += mask[i] ? 1u : 0u;
        if (count == 0) { free(mask); return -1; }
    }
    speed = om_unit_effective_speed((om_world *)w, unit);
    up_div = om_tactical_get_param(w, OM_TP_SLOPE_UP_DIV);
    down_mult = om_tactical_get_param(w, OM_TP_SLOPE_DOWN_MULT);
    if (!(speed > 0.0) || !(up_div > 0.0) || !(down_mult > 0.0)) { free(mask); return -1; }
    /* cost[0] flat, [1] rising, [2] falling; [.][0] straight, [.][1] diagonal; Q16 seconds */
    for (k = 0; k < WR_STEPS; k++) {
        double base = (k ? WR_Q16_DIAG : WR_Q16_ONE) * OM_TERRAIN_CELL_WU;
        cost[0][k] = base / speed;
        cost[1][k] = base / (speed / up_div);
        cost[2][k] = base / (speed * down_mult);
    }
    c.cw = cw; c.ch = ch; c.mask = mask;
    c.dist = (int64_t *)malloc(sizeof(int64_t) * n_cells);
    c.prev = (uint32_t *)malloc(sizeof(uint32_t) * n_cells);
    c.heap = (uint32_t *)malloc(sizeof(uint32_t) * n_cells);
    c.hpos = (uint32_t *)malloc(sizeof(uint32_t) * n_cells);
    if (!c.dist || !c.prev || !c.heap || !c.hpos) goto out;
    for (i = 0; i < n_cells; i++) { c.dist[i] = WR_INF; c.prev[i] = WR_NONE; c.hpos[i] = WR_NONE; }
    c.hn = 0;

    sx = ux / OM_TERRAIN_CELL_WU; sy = uy / OM_TERRAIN_CELL_WU;
    ncx = (int64_t)(sx < 0.0 ? 0.0 : sx); ncy = (int64_t)(sy < 0.0 ? 0.0 : sy);
    if (ncx >= (int64_t)cw) ncx = (int64_t)cw - 1;
    if (ncy >= (int64_t)ch) ncy = (int64_t)ch - 1;
    start = (uint32_t)(ncy * (int64_t)cw + ncx);
    gcx = (int64_t)(gx < 0.0 ? 0.0 : gx / OM_TERRAIN_CELL_WU); gcy = (int64_t)(gy < 0.0 ? 0.0 : gy / OM_TERRAIN_CELL_WU);
    if (gcx >= (int64_t)cw) gcx = (int64_t)cw - 1;
    if (gcy >= (int64_t)ch) gcy = (int64_t)ch - 1;
    goal = (uint32_t)(gcy * (int64_t)cw + gcx);

    c.dist[start] = 0;
    c.heap[0] = start; c.hpos[start] = 0; c.hn = 1;
    while (c.hn > 0) {
        uint32_t cur = wr_pop(&c);
        uint32_t cx = cur % cw, cy = cur / cw;
        if (cur == goal) break;
        for (k = 0; k < WR_NEIGHBOURS; k++) {
            int64_t nx = (int64_t)cx + dxs[k], ny = (int64_t)cy + dys[k];
            uint32_t nb;
            double h0, h1;
            int kind;
            int64_t nd;
            if (nx < 0 || ny < 0 || nx >= (int64_t)cw || ny >= (int64_t)ch) continue;
            nb = (uint32_t)(ny * (int64_t)cw + nx);
            if (mask && !mask[nb]) continue;
            h0 = terrain ? wr_height(w, cur, cw) : 0.0;
            h1 = terrain ? wr_height(w, nb, cw) : 0.0;
            kind = h1 > h0 ? 1 : (h1 < h0 ? 2 : 0);
            nd = c.dist[cur] + (int64_t)(cost[kind][dxs[k] && dys[k] ? 1 : 0] + WR_HALF);
            if (nd < c.dist[nb]) {
                if (c.hpos[nb] == WR_NONE) {
                    if (c.dist[nb] != WR_INF) continue; /* already settled */
                    if (c.hn >= OM_WALK_OPEN_CAP) continue;
                    c.dist[nb] = nd; c.prev[nb] = cur;
                    c.heap[c.hn] = nb; c.hpos[nb] = c.hn; c.hn++;
                    wr_up(&c, c.hn - 1);
                } else {
                    c.dist[nb] = nd; c.prev[nb] = cur;
                    wr_up(&c, c.hpos[nb]);
                }
            }
        }
    }

    if (c.dist[goal] != WR_INF && c.hpos[goal] == WR_NONE) {
        final_cell = goal;
    } else {
        int64_t best = WR_INF;
        final_cell = start;
        for (i = 0; i < n_cells; i++) {
            int64_t dx, dy, d;
            if (c.dist[i] == WR_INF || c.hpos[i] != WR_NONE) continue;
            dx = (int64_t)(i % cw) - gcx; dy = (int64_t)(i / cw) - gcy;
            d = dx * dx + dy * dy;
            if (d < best) { best = d; final_cell = i; }
        }
    }
    if (final_cell == start) { ret = 0; goto out; }
    count = 1;
    for (i = final_cell; i != start; i = c.prev[i]) count++;
    ret = (int)count;
    if (count > cap || !pts) goto done;
    layer_i = count;
    for (i = final_cell; ; i = c.prev[i]) {
        layer_i--;
        pts[2 * layer_i] = ((double)(i % cw) + WR_HALF) * OM_TERRAIN_CELL_WU;
        pts[2 * layer_i + 1] = ((double)(i / cw) + WR_HALF) * OM_TERRAIN_CELL_WU;
        if (i == start) break;
    }
    pts[0] = ux; pts[1] = uy;
    if (final_cell == goal) { pts[2 * (count - 1)] = gx; pts[2 * (count - 1) + 1] = gy; }
done:
    if (seconds) *seconds = (double)c.dist[final_cell] / WR_Q16_ONE;
out:
    free(mask); free(c.dist); free(c.prev); free(c.heap); free(c.hpos);
    return ret;
}

/* ---- slope links ---- */
