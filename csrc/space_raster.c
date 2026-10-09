/* csrc/space_raster.c -- VG lane D, piece D3 (E-17 R-246-01, E-01 R-001-04): plate polygons to the 100 wu cell masks, and
 * the carve step that joins cut-off regions to the objective's. Port of scenes/mockups/landscape/field_map_space.gd.
 * Cells are sampled at their centres ((cx + .5) * 100 wu), so the mask and the polygons agree on the same 240 x 240 grid.
 * See also: om_space_field_generate_nodes in csrc/space_field.c, which calls both stages (D4). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "space_internal.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define SR_SIDE OM_SPACE_FIELD_SIDE
#define SR_CELLS OM_SPACE_FIELD_CELLS
#define SR_LAYERS OM_SPACE_FIELD_LAYERS
#define SR_ALL (SR_LAYERS * SR_CELLS)
#define SR_MIN_POCKET_CELLS 40 /* field_map_space.gd MIN_POCKET_CELLS */
#define SR_MAX_JOIN_ROUNDS 8   /* MAX_JOIN_ROUNDS */
#define SR_PASSAGE_CELLS 3     /* MIN_PASSAGE_WU 300 / SPACING 100 */
#define SR_NO_MAIN_D2 (1 << 28) /* NO_MAIN_D2 */
#define SR_NO_OWNER 0xFFFFu
#define SR_BIG 1e30
#define SR_CLIP_PTS 40
#define SR_MAX_PIECES 256
#define SR_MIN_PART_AREA 1.0  /* _subtract_rect: parts under one square wu are dropped */
#define SR_DEDUPE_WU 0.01     /* _subtract_rect: points closer than this are one point */
#define SR_HALF 0.5
#define SR_MIN_PTS 3
#define SR_PARTS 4 /* left, right, below, above */
#define SR_RUN_KEY 4096 /* _cut_polygons: start * 4096 + end names a run */
#define SR_BIT_SHIFT 3
#define SR_BIT_MASK 7u
#define SR_BYTE_BITS 8

typedef struct { int n; double xy[2 * SR_CLIP_PTS]; } sr_poly;
typedef struct { double x0, y0, x1, y1; } sr_rect;

typedef struct {
    int32_t *labels; /* per cell, region id or -1 */
    int32_t *sizes;  /* per region */
    int n_regions;
    int main_id;
} sr_labels;

/* field_map_space.gd _fill_polygon: even-odd scanline at each cell row centre. */
static void sr_fill_polygon(om_space_cells *r, uint32_t k, const double *xy, uint32_t n, uint8_t kind, uint16_t id) {
    double low_y = xy[1], high_y = xy[1];
    for (uint32_t i = 1; i < n; i++) {
        if (xy[2 * i + 1] < low_y) low_y = xy[2 * i + 1];
        if (xy[2 * i + 1] > high_y) high_y = xy[2 * i + 1];
    }
    int gy0 = (int)(low_y / OM_SPACE_FIELD_CELL_WU) - 1, gy1 = (int)(high_y / OM_SPACE_FIELD_CELL_WU) + 1;
    if (gy0 < 0) gy0 = 0;
    if (gy1 > SR_SIDE - 1) gy1 = SR_SIDE - 1;
    for (int gy = gy0; gy <= gy1; gy++) {
        double y = ((double)gy + SR_HALF) * OM_SPACE_FIELD_CELL_WU, xs[OM_SPACE_FIELD_MAX_PTS];
        int cnt = 0;
        for (uint32_t e = 0; e < n; e++) {
            uint32_t f = (e + 1) % n;
            double ay = xy[2 * e + 1], by = xy[2 * f + 1];
            if ((ay <= y && by > y) || (by <= y && ay > y)) {
                double v = xy[2 * e] + (y - ay) / (by - ay) * (xy[2 * f] - xy[2 * e]);
                int j = cnt++;
                while (j > 0 && xs[j - 1] > v) { xs[j] = xs[j - 1]; j--; }
                xs[j] = v;
            }
        }
        for (int p = 0; p + 1 < cnt; p += 2) {
            for (int gx = 0; gx < SR_SIDE; gx++) {
                double x = ((double)gx + SR_HALF) * OM_SPACE_FIELD_CELL_WU;
                if (x >= xs[p] && x <= xs[p + 1]) {
                    uint32_t i = (uint32_t)gy * SR_SIDE + (uint32_t)gx;
                    r->mask[k][i] = 1;
                    r->owner[k][i] = id;
                    r->kind[k][i] = kind;
                }
            }
        }
    }
}

/* _open_block, size SR_PASSAGE_CELLS: a cell stays open only if a fully open 3 x 3 block inside the layer covers it.
 * out is 1 open. */
static void sr_open_block(const om_space_cells *r, uint8_t *out) {
    uint8_t *rows = malloc(SR_CELLS), *er = malloc(SR_CELLS), *dl = malloc(SR_CELLS);
    const int last = SR_SIDE - 1;
    for (int k = 0; k < SR_LAYERS; k++) {
        const uint8_t *m = r->mask[k];
        uint8_t *o = out + (size_t)k * SR_CELLS;
        memset(rows, 0, SR_CELLS);
        memset(er, 0, SR_CELLS);
        for (int y = 0; y < SR_SIDE; y++)
            for (int x = 1; x < last; x++) {
                int i = y * SR_SIDE + x;
                rows[i] = (uint8_t)(!m[i - 1] && !m[i] && !m[i + 1]);
            }
        for (int y = 1; y < last; y++)
            for (int x = 0; x < SR_SIDE; x++) {
                int i = y * SR_SIDE + x;
                er[i] = rows[i - SR_SIDE] & rows[i] & rows[i + SR_SIDE];
            }
        for (int y = 0; y < SR_SIDE; y++)
            for (int x = 0; x < SR_SIDE; x++) {
                int i = y * SR_SIDE + x;
                uint8_t v = er[i];
                if (x > 0) v |= er[i - 1];
                if (x < last) v |= er[i + 1];
                dl[i] = v;
            }
        for (int y = 0; y < SR_SIDE; y++)
            for (int x = 0; x < SR_SIDE; x++) {
                int i = y * SR_SIDE + x;
                uint8_t v = dl[i];
                if (y > 0) v |= dl[i - SR_SIDE];
                if (y < last) v |= dl[i + SR_SIDE];
                o[i] = v;
            }
    }
    free(rows); free(er); free(dl);
}

/* _label_regions: six-neighbour flood over open cells; main is the region at layer 0, objective cell (-1 if blocked). */
static int sr_label(const uint8_t *open, uint32_t obj_cx, uint32_t obj_cy, sr_labels *L, int32_t *stack) {
    L->n_regions = 0;
    for (int i = 0; i < SR_ALL; i++) L->labels[i] = -1;
    for (int start = 0; start < SR_ALL; start++) {
        if (!open[start] || L->labels[start] != -1) continue;
        int id = L->n_regions++, top = 0, size = 0;
        L->labels[start] = id;
        stack[top++] = start;
        while (top) {
            int c = stack[--top], k = c / SR_CELLS, p = c - k * SR_CELLS, gy = p / SR_SIDE, gx = p - gy * SR_SIDE;
            int nb[6], nn = 0;
            size++;
            if (gx > 0) nb[nn++] = c - 1;
            if (gx < SR_SIDE - 1) nb[nn++] = c + 1;
            if (gy > 0) nb[nn++] = c - SR_SIDE;
            if (gy < SR_SIDE - 1) nb[nn++] = c + SR_SIDE;
            if (k > 0) nb[nn++] = c - SR_CELLS;
            if (k < SR_LAYERS - 1) nb[nn++] = c + SR_CELLS;
            for (int q = 0; q < nn; q++)
                if (open[nb[q]] && L->labels[nb[q]] == -1) { L->labels[nb[q]] = id; stack[top++] = nb[q]; }
        }
        L->sizes[id] = size;
    }
    L->main_id = L->labels[obj_cy * SR_SIDE + obj_cx];
    return L->n_regions;
}

/* _fill_pockets: regions other than main under SR_MIN_POCKET_CELLS become solid, with no owner. */
static void sr_fill_pockets(om_space_cells *r, const sr_labels *L) {
    for (int c = 0; c < SR_ALL; c++) {
        int id = L->labels[c];
        if (id >= 0 && id != L->main_id && L->sizes[id] < SR_MIN_POCKET_CELLS) {
            int k = c / SR_CELLS, i = c - k * SR_CELLS;
            r->mask[k][i] = 1;
        }
    }
}

int om_space_raster(const om_space_plates *plates, double cell_wu, om_space_cells *raster) {
    uint8_t *open;
    int32_t *stack;
    sr_labels L;
    if (!plates || !raster || cell_wu != OM_SPACE_FIELD_CELL_WU) return -1;
    memset(raster, 0, sizeof *raster);
    memset(raster->owner, 0xFF, sizeof raster->owner);
    for (uint32_t i = 0; i < plates->n_plates; i++) {
        const om_space_plate *p = &plates->plates[i];
        if (!p->dropped && p->layer < SR_LAYERS && p->n_pts >= SR_MIN_PTS) sr_fill_polygon(raster, p->layer, p->xy, p->n_pts, p->kind, p->id);
    }
    open = malloc(SR_ALL);
    stack = malloc(sizeof(int32_t) * SR_ALL);
    L.labels = malloc(sizeof(int32_t) * SR_ALL);
    L.sizes = malloc(sizeof(int32_t) * SR_ALL);
    if (!open || !stack || !L.labels || !L.sizes) { free(open); free(stack); free(L.labels); free(L.sizes); return -1; }
    sr_open_block(raster, open);
    sr_label(open, OM_SPACE_OBJECTIVE_CX, OM_SPACE_OBJECTIVE_CY, &L, stack);
    sr_fill_pockets(raster, &L);
    free(open); free(stack); free(L.labels); free(L.sizes);
    return 0;
}

/* ---- polygon cutting: _clip, _subtract_rect, _cut_polygons ---- */

static void sr_clip(const sr_poly *in, double nx, double ny, double d, sr_poly *out) {
    out->n = 0;
    for (int i = 0; i < in->n; i++) {
        int j = (i + 1) % in->n;
        double ax = in->xy[2 * i], ay = in->xy[2 * i + 1], bx = in->xy[2 * j], by = in->xy[2 * j + 1];
        double sa = nx * ax + ny * ay - d, sb = nx * bx + ny * by - d;
        if (sa <= 0.0 && out->n < SR_CLIP_PTS) { out->xy[2 * out->n] = ax; out->xy[2 * out->n + 1] = ay; out->n++; }
        if (((sa < 0.0 && sb > 0.0) || (sa > 0.0 && sb < 0.0)) && out->n < SR_CLIP_PTS) {
            double t = sa / (sa - sb);
            out->xy[2 * out->n] = ax + (bx - ax) * t;
            out->xy[2 * out->n + 1] = ay + (by - ay) * t;
            out->n++;
        }
    }
}

static int sr_clean(sr_poly *p) {
    sr_poly c;
    double area = 0.0;
    c.n = 0;
    for (int i = 0; i < p->n; i++) {
        double x = p->xy[2 * i], y = p->xy[2 * i + 1];
        if (c.n) {
            double dx = x - c.xy[2 * (c.n - 1)], dy = y - c.xy[2 * (c.n - 1) + 1];
            if (dx * dx + dy * dy <= SR_DEDUPE_WU * SR_DEDUPE_WU) continue;
        }
        c.xy[2 * c.n] = x; c.xy[2 * c.n + 1] = y; c.n++;
    }
    if (c.n > 1) {
        double dx = c.xy[0] - c.xy[2 * (c.n - 1)], dy = c.xy[1] - c.xy[2 * (c.n - 1) + 1];
        if (dx * dx + dy * dy <= SR_DEDUPE_WU * SR_DEDUPE_WU) c.n--;
    }
    for (int i = 0; i < c.n; i++) {
        int j = (i + 1) % c.n;
        area += c.xy[2 * i] * c.xy[2 * j + 1] - c.xy[2 * j] * c.xy[2 * i + 1];
    }
    if (c.n < SR_MIN_PTS || (area < 0 ? -area : area) * SR_HALF < SR_MIN_PART_AREA) return 0;
    *p = c;
    return 1;
}

/* A convex polygon minus an axis-aligned rectangle: the parts left of, right of, below and above it. */
static int sr_subtract_rect(const sr_poly *poly, const sr_rect *r, sr_poly *parts) {
    sr_poly rest, next;
    int n = 0;
    sr_poly t[SR_PARTS];
    sr_clip(poly, 1.0, 0.0, r->x0, &t[0]);
    sr_clip(poly, -1.0, 0.0, -r->x0, &rest);
    sr_clip(&rest, -1.0, 0.0, -r->x1, &t[1]);
    sr_clip(&rest, 1.0, 0.0, r->x1, &next); rest = next;
    sr_clip(&rest, 0.0, 1.0, r->y0, &t[2]);
    sr_clip(&rest, 0.0, -1.0, -r->y0, &next); rest = next;
    sr_clip(&rest, 0.0, -1.0, -r->y1, &t[SR_PARTS - 1]);
    for (int i = 0; i < SR_PARTS; i++) if (sr_clean(&t[i])) parts[n++] = t[i];
    return n;
}

static void sr_bounds(const sr_poly *p, sr_rect *b) {
    b->x0 = b->x1 = p->xy[0]; b->y0 = b->y1 = p->xy[1];
    for (int i = 1; i < p->n; i++) {
        if (p->xy[2 * i] < b->x0) b->x0 = p->xy[2 * i];
        if (p->xy[2 * i] > b->x1) b->x1 = p->xy[2 * i];
        if (p->xy[2 * i + 1] < b->y0) b->y0 = p->xy[2 * i + 1];
        if (p->xy[2 * i + 1] > b->y1) b->y1 = p->xy[2 * i + 1];
    }
}

static int sr_overlap(const sr_rect *a, const sr_rect *b) {
    return a->x0 < b->x1 && b->x0 < a->x1 && a->y0 < b->y1 && b->y0 < a->y1;
}

/* _cut_polygons: the opened channel (1 per cell inside low..high) is cut out of layer k's polygons by clipping, one
 * rectangle per run of equal rows. Pieces beyond OM_SPACE_FIELD_MAX_POLYS are discarded; their cells stay blocked. */
static void sr_cut_polygons(om_space_plates *pl, uint32_t k, const uint8_t *channel, int lx, int ly, int hx, int hy) {
    const double S = OM_SPACE_FIELD_CELL_WU;
    int cap_rects = (hy - ly + 1) * ((hx - lx + 1) / 2 + 1), n_rects = 0, prev_n = 0, cur_n = 0;
    sr_rect *rects = malloc(sizeof(sr_rect) * (size_t)cap_rects);
    int *prev_key = malloc(sizeof(int) * (size_t)cap_rects), *prev_at = malloc(sizeof(int) * (size_t)cap_rects);
    int *cur_key = malloc(sizeof(int) * (size_t)cap_rects), *cur_at = malloc(sizeof(int) * (size_t)cap_rects);
    sr_poly *pa = malloc(sizeof(sr_poly) * SR_MAX_PIECES), *pb = malloc(sizeof(sr_poly) * SR_MAX_PIECES);
    om_space_plate *out = malloc(sizeof(om_space_plate) * OM_SPACE_FIELD_MAX_POLYS);
    uint32_t s = 0, cnt, n_out = 0;
    sr_rect box;
    if (!rects || !prev_key || !prev_at || !cur_key || !cur_at || !pa || !pb || !out) goto done;
    for (int gy = ly; gy <= hy; gy++) {
        int gx = lx;
        cur_n = 0;
        while (gx <= hx) {
            if (!channel[gy * SR_SIDE + gx]) { gx++; continue; }
            int start = gx, key, at = -1;
            while (gx <= hx && channel[gy * SR_SIDE + gx]) gx++;
            key = start * SR_RUN_KEY + gx;
            for (int q = 0; q < prev_n; q++) if (prev_key[q] == key) { at = prev_at[q]; break; }
            if (at >= 0) rects[at].y1 += S;
            else {
                at = n_rects++;
                rects[at].x0 = start * S; rects[at].x1 = gx * S; rects[at].y0 = gy * S; rects[at].y1 = (gy + 1) * S;
            }
            cur_key[cur_n] = key; cur_at[cur_n++] = at;
        }
        memcpy(prev_key, cur_key, sizeof(int) * (size_t)cur_n);
        memcpy(prev_at, cur_at, sizeof(int) * (size_t)cur_n);
        prev_n = cur_n;
    }
    box.x0 = lx * S; box.y0 = ly * S; box.x1 = (hx + 1) * S; box.y1 = (hy + 1) * S;
    for (uint32_t i = 0; i < k; i++) s += pl->per_layer[i];
    cnt = pl->per_layer[k];
    for (uint32_t i = s; i < s + cnt; i++) {
        const om_space_plate *src = &pl->plates[i];
        int np = 1;
        sr_rect b;
        pa[0].n = src->n_pts;
        memcpy(pa[0].xy, src->xy, sizeof(double) * 2u * src->n_pts);
        sr_bounds(&pa[0], &b);
        if (!src->dropped && sr_overlap(&b, &box)) {
            for (int r = 0; r < n_rects; r++) {
                int nn = 0;
                for (int q = 0; q < np; q++) {
                    sr_rect pb_b;
                    sr_bounds(&pa[q], &pb_b);
                    if (sr_overlap(&pb_b, &rects[r])) {
                        sr_poly parts[SR_PARTS];
                        int m = sr_subtract_rect(&pa[q], &rects[r], parts);
                        for (int z = 0; z < m && nn < SR_MAX_PIECES; z++) pb[nn++] = parts[z];
                    } else if (nn < SR_MAX_PIECES) pb[nn++] = pa[q];
                }
                memcpy(pa, pb, sizeof(sr_poly) * (size_t)nn);
                np = nn;
            }
        }
        for (int q = 0; q < np; q++) {
            if (pa[q].n > OM_SPACE_FIELD_MAX_PTS) continue;
            if (n_out + (pl->n_plates - s - cnt) + s >= OM_SPACE_FIELD_MAX_POLYS) continue;
            out[n_out] = *src;
            out[n_out].n_pts = (uint8_t)pa[q].n;
            memcpy(out[n_out].xy, pa[q].xy, sizeof(double) * 2u * (size_t)pa[q].n);
            n_out++;
        }
    }
    memmove(&pl->plates[s + n_out], &pl->plates[s + cnt], sizeof(om_space_plate) * (pl->n_plates - s - cnt));
    memcpy(&pl->plates[s], out, sizeof(om_space_plate) * n_out);
    pl->n_plates = pl->n_plates - cnt + n_out;
    pl->per_layer[k] = n_out;
done:
    free(rects); free(prev_key); free(prev_at); free(cur_key); free(cur_at); free(pa); free(pb); free(out);
}

/* ---- _main_nearest: per cell of layer k, squared plane distance to the nearest main-region cell (exact EDT) ---- */

static void sr_main_nearest(const int32_t *labels, int32_t main_id, uint32_t k, int32_t *d2, int32_t *src) {
    const int32_t *lab = labels + (size_t)k * SR_CELLS;
    int32_t *row_of = malloc(sizeof(int32_t) * SR_CELLS);
    double f[SR_SIDE], z[SR_SIDE + 1];
    int v[SR_SIDE];
    for (int gx = 0; gx < SR_SIDE; gx++) {
        int last = -1, next = -1;
        for (int gy = 0; gy < SR_SIDE; gy++) {
            if (lab[gy * SR_SIDE + gx] == main_id) last = gy;
            row_of[gy * SR_SIDE + gx] = last;
        }
        for (int gy = SR_SIDE - 1; gy >= 0; gy--) {
            int above;
            if (lab[gy * SR_SIDE + gx] == main_id) next = gy;
            above = row_of[gy * SR_SIDE + gx];
            if (next >= 0 && (above < 0 || next - gy < gy - above)) row_of[gy * SR_SIDE + gx] = next;
        }
    }
    for (int gy = 0; gy < SR_SIDE; gy++) {
        int top = 0;
        for (int gx = 0; gx < SR_SIDE; gx++) {
            int r = row_of[gy * SR_SIDE + gx];
            f[gx] = r >= 0 ? (double)((gy - r) * (gy - r)) : (double)SR_NO_MAIN_D2;
        }
        v[0] = 0; z[0] = -SR_BIG; z[1] = SR_BIG;
        for (int q = 1; q < SR_SIDE; q++) {
            double s = ((f[q] + q * q) - (f[v[top]] + v[top] * v[top])) / (double)(2 * q - 2 * v[top]);
            while (s <= z[top]) {
                top--;
                s = ((f[q] + q * q) - (f[v[top]] + v[top] * v[top])) / (double)(2 * q - 2 * v[top]);
            }
            top++; v[top] = q; z[top] = s; z[top + 1] = SR_BIG;
        }
        top = 0;
        for (int gx = 0; gx < SR_SIDE; gx++) {
            while (z[top + 1] < (double)gx) top++;
            d2[gy * SR_SIDE + gx] = (int32_t)((gx - v[top]) * (gx - v[top]) + f[v[top]]);
            src[gy * SR_SIDE + gx] = row_of[gy * SR_SIDE + v[top]] * SR_SIDE + v[top];
        }
    }
    free(row_of);
}

/* _widen_channel: opens one 3 x 3-block channel from the region's boundary to the nearest main cell on a layer both
 * touch. Returns 1 when a channel was cut, 0 when no layer of the region holds main cells. */
static int sr_widen_channel(om_space_plates *pl, om_space_cells *r, const sr_labels *L, const int32_t *main_count,
                            int32_t **near_d2, int32_t **near_src, const int32_t *cells, int n_cells) {
    const int radius = SR_PASSAGE_CELLS / 2;
    int best = SR_NO_MAIN_D2, best_k = -1, fx = 0, fy = 0, tx = 0, ty = 0;
    for (int q = 0; q < n_cells; q++) {
        int c = cells[q], k = c / SR_CELLS, p = c - k * SR_CELLS, gy = p / SR_SIDE, gx = p - gy * SR_SIDE;
        int32_t id = L->labels[c];
        if (main_count[k] == 0) continue;
        if (!((gx > 0 && L->labels[c - 1] != id) || (gx < SR_SIDE - 1 && L->labels[c + 1] != id) ||
              (gy > 0 && L->labels[c - SR_SIDE] != id) || (gy < SR_SIDE - 1 && L->labels[c + SR_SIDE] != id)))
            continue;
        if (!near_d2[k]) {
            near_d2[k] = malloc(sizeof(int32_t) * SR_CELLS);
            near_src[k] = malloc(sizeof(int32_t) * SR_CELLS);
            sr_main_nearest(L->labels, L->main_id, (uint32_t)k, near_d2[k], near_src[k]);
        }
        if (near_d2[k][p] < best) {
            int src = near_src[k][p];
            best = near_d2[k][p]; best_k = k; fx = gx; fy = gy;
            tx = src % SR_SIDE; ty = src / SR_SIDE;
        }
    }
    if (best_k < 0) return 0;
    {
        uint8_t *channel = calloc(SR_CELLS, 1);
        int lx = (fx < tx ? fx : tx) - 2 * radius, ly = (fy < ty ? fy : ty) - 2 * radius;
        int hx = (fx > tx ? fx : tx) + 2 * radius, hy = (fy > ty ? fy : ty) + 2 * radius;
        int dx = tx > fx ? tx - fx : fx - tx, dy = -(ty > fy ? ty - fy : fy - ty);
        int sx = fx < tx ? 1 : -1, sy = fy < ty ? 1 : -1, err = dx + dy, x = fx, y = fy;
        if (!channel) return 0;
        if (lx < 0) lx = 0;
        if (ly < 0) ly = 0;
        if (hx > SR_SIDE - 1) hx = SR_SIDE - 1;
        if (hy > SR_SIDE - 1) hy = SR_SIDE - 1;
        for (;;) {
            int bx = x - radius, by = y - radius;
            if (bx < 0) bx = 0;
            if (bx > SR_SIDE - 1 - 2 * radius) bx = SR_SIDE - 1 - 2 * radius;
            if (by < 0) by = 0;
            if (by > SR_SIDE - 1 - 2 * radius) by = SR_SIDE - 1 - 2 * radius;
            for (int cy = by; cy <= by + 2 * radius; cy++)
                for (int cx = bx; cx <= bx + 2 * radius; cx++) {
                    int i = cy * SR_SIDE + cx;
                    channel[i] = 1;
                    r->mask[best_k][i] = 0;
                    r->owner[best_k][i] = SR_NO_OWNER;
                    r->kind[best_k][i] = OM_SPACE_KIND_PLATE;
                }
            if (x == tx && y == ty) break;
            {
                int e2 = 2 * err;
                if (e2 >= dy) { err += dy; x += sx; }
                if (e2 <= dx) { err += dx; y += sy; }
            }
        }
        sr_cut_polygons(pl, (uint32_t)best_k, channel, lx, ly, hx, hy);
        free(channel);
    }
    return 1;
}

/* _drop_plates, for a region no channel can reach (no main cell on its layers): the plates bounding the region on a
 * layer are dropped (removed from the list and their cells opened) so the region grows into the layers around it. */
static void sr_drop_ring(om_space_plates *pl, om_space_cells *r, const int32_t *cells, int n_cells) {
    uint8_t (*mark)[(OM_SPACE_FIELD_MAX_POLYS + SR_BYTE_BITS - 1) / SR_BYTE_BITS] = calloc(SR_LAYERS, sizeof *mark);
    if (!mark) return;
    for (int q = 0; q < n_cells; q++) {
        int c = cells[q], k = c / SR_CELLS, p = c - k * SR_CELLS, gy = p / SR_SIDE, gx = p - gy * SR_SIDE;
        int nb[4], nn = 0;
        if (gx > 0) nb[nn++] = p - 1;
        if (gx < SR_SIDE - 1) nb[nn++] = p + 1;
        if (gy > 0) nb[nn++] = p - SR_SIDE;
        if (gy < SR_SIDE - 1) nb[nn++] = p + SR_SIDE;
        for (int m = 0; m < nn; m++) {
            uint16_t o = r->owner[k][nb[m]];
            if (o != SR_NO_OWNER && o < OM_SPACE_FIELD_MAX_POLYS) mark[k][o >> SR_BIT_SHIFT] = (uint8_t)(mark[k][o >> SR_BIT_SHIFT] | (1u << (o & SR_BIT_MASK)));
        }
    }
    for (uint32_t i = 0; i < pl->n_plates; i++) {
        om_space_plate *p = &pl->plates[i];
        if (p->layer < SR_LAYERS && p->id < OM_SPACE_FIELD_MAX_POLYS && ((mark[p->layer][p->id >> SR_BIT_SHIFT] >> (p->id & SR_BIT_MASK)) & 1u)) p->dropped = 1;
    }
    for (int k = 0; k < SR_LAYERS; k++)
        for (int i = 0; i < SR_CELLS; i++) {
            uint16_t o = r->owner[k][i];
            if (o != SR_NO_OWNER && o < OM_SPACE_FIELD_MAX_POLYS && ((mark[k][o >> SR_BIT_SHIFT] >> (o & SR_BIT_MASK)) & 1u)) {
                r->mask[k][i] = 0;
                r->owner[k][i] = SR_NO_OWNER;
                r->kind[k][i] = OM_SPACE_KIND_PLATE;
            }
        }
    free(mark);
}

int om_space_carve(om_space_plates *plates, om_space_cells *raster, uint32_t obj_cx, uint32_t obj_cy, int no_carve) {
    uint8_t *open = malloc(SR_ALL);
    int32_t *stack = malloc(sizeof(int32_t) * SR_ALL), *cells = malloc(sizeof(int32_t) * SR_ALL);
    int32_t *near_d2[SR_LAYERS] = {0}, *near_src[SR_LAYERS] = {0}, main_count[SR_LAYERS];
    sr_labels L;
    int unreachable = -1;
    L.labels = malloc(sizeof(int32_t) * SR_ALL);
    L.sizes = malloc(sizeof(int32_t) * SR_ALL);
    if (!plates || !raster || obj_cx >= SR_SIDE || obj_cy >= SR_SIDE || !open || !stack || !cells || !L.labels || !L.sizes) goto done;
    for (int round = 0; round < SR_MAX_JOIN_ROUNDS && !no_carve; round++) {
        int any = 0;
        sr_open_block(raster, open);
        sr_label(open, obj_cx, obj_cy, &L, stack);
        if (L.main_id < 0) break;
        memset(main_count, 0, sizeof main_count);
        for (int id = 0; id < L.n_regions; id++) if (id != L.main_id && L.sizes[id] >= SR_MIN_POCKET_CELLS) any = 1;
        if (!any) break;
        for (int c = 0; c < SR_ALL; c++) if (L.labels[c] == L.main_id) main_count[c / SR_CELLS]++;
        for (int k = 0; k < SR_LAYERS; k++) { free(near_d2[k]); free(near_src[k]); near_d2[k] = near_src[k] = NULL; }
        for (int id = 0; id < L.n_regions; id++) {
            int n = 0;
            if (id == L.main_id || L.sizes[id] < SR_MIN_POCKET_CELLS) continue;
            for (int c = 0; c < SR_ALL; c++) if (L.labels[c] == id) cells[n++] = c;
            if (!sr_widen_channel(plates, raster, &L, main_count, near_d2, near_src, cells, n)) sr_drop_ring(plates, raster, cells, n);
        }
    }
    sr_open_block(raster, open);
    sr_label(open, obj_cx, obj_cy, &L, stack);
    unreachable = L.n_regions - (L.main_id >= 0 ? 1 : 0);
done:
    for (int k = 0; k < SR_LAYERS; k++) { free(near_d2[k]); free(near_src[k]); }
    free(open); free(stack); free(cells); free(L.labels); free(L.sizes);
    return unreachable;
}
