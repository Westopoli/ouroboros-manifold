/* csrc/space_plates.c -- VG lane D piece D2: the space field's plate polygons, ported from
 * scenes/mockups/landscape/field_map_space.gd (_lattice, _cell_polygon, _clip, _erode, _nearest_plate, _build_nodes and the
 * polygon part of _build_plate_layer). Double arithmetic, no libm beyond sqrt/floor/ceil/round; noise and hashes from
 * space_noise.c (D1). The mockup's tunables are constants here, the contract has no setter: plate_cell_wu 1600
 * (PLATE_CELL_WU, gd:43), layer_gap_wu 1000 (LAYER_GAP_WU, gd:22; a client drawing offset, unused in the sim frame),
 * size_spread 0.6 (SIZE_SPREAD, gd:49), density_swing 0.8 (DENSITY_SWING, gd:51), shared_density true (gd:87; one noise
 * field for every layer, one drop roll per coarse cell), small_share 7.5 (SMALL_SHARE_DEFAULT, gd:27; small-craft sections
 * are not part of D2). The mockup runs in float32 (Godot Vector2); this port is double, so it is a statistical match.
 * See also: csrc/space_internal.h (the stage interface), csrc/space_field.c (generate, D4 wires this in). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "space_internal.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define SP_PTS 48              /* working polygon capacity */
#define SP_NEIGH 128           /* neighbour sites of one site: 5 x 5 lattice cells x 4 */
#define SP_LINK_MAX 24
#define SP_WC 15               /* ceil(24000 / 1600) */
#define SP_PAD 3               /* LATTICE_PAD, gd:53 */
#define SP_STRIDE (SP_WC + 2 * SP_PAD)
#define SP_KEYS (SP_STRIDE * SP_STRIDE)
#define SP_SITES (4 * SP_KEYS) /* a lattice cell holds one site, or four when split */
#define SP_RWC 60              /* ceil(24000 / 400) */
#define SP_RSTRIDE (SP_RWC + 2 * SP_PAD)
#define SP_RKEYS (SP_RSTRIDE * SP_RSTRIDE)
#define SP_DIM 241             /* noise grid: canvas / SPACING + 1 */
#define SP_SPACING 100.0
#define SP_NODES 6
#define SP_NODES_MAX (SP_NODES + OM_SPACE_FIELD_MAX_NODES) /* the six built nodes plus any extra clearing nodes the caller gives */
#define SP_STAGE0 3 /* nodes: objective, spawn, spawn, staging, staging, vantage */
#define SP_VANTAGE 5
#define SP_LAYER_SEED_STEP 7919u /* LAYER_SEED_STEP, gd:39 */
#define SP_SIZE_SEED_OFFSET 104729u /* gd:52 */
#define SP_PLATE_CELL 1600.0
#define SP_CHANNEL 160.0
#define SP_JITTER_MAX 0.45
#define SP_RUBBLE_CELL 400.0
#define SP_RUBBLE_CHANNEL 100.0
#define SP_RUBBLE_SHARE 0.35
#define SP_SIZE_SPREAD 0.6
#define SP_SIZE_TAIL_SHARE 0.25
#define SP_DENSITY_SWING 0.8
#define SP_MASS_CHANCE 0.5
#define SP_MASS_RADIUS 2200.0
#define SP_ERODE_MAX 0.12
#define SP_CLEAR_RADIUS 600.0  /* CLEAR_RADIUS_WU, gd:23 */
#define SP_STAGING_REACH 1500.0
#define SP_DENSITY_MAX 90.0
#define SP_H_JITTER_X 0
#define SP_H_JITTER_Y 1
#define SP_H_MASS_ON 3
#define SP_H_MASS_PICK 4
#define SP_H_ERODE 5
#define SP_H_RUBBLE_X 6
#define SP_H_RUBBLE_Y 7
#define SP_H_RUBBLE_KEEP 8
#define SP_H_RUBBLE_ERODE 9
#define SP_H_SPLIT_X 10
#define SP_H_SPLIT_Y 11
#define SP_H_SPLIT_ERODE 13
#define SP_H_DROP 2
#define SP_U32_SPAN 4294967296.0
#define SP_REACH_SKIP 0.01
#define SP_EDGE_EPS 0.01
#define SP_CLAMP_EPS 1e-9 /* vertex-on-edge tolerance of the emit clamp (wave 6c ruling) */
#define SP_LINK_EPS 1.0
#define SP_SQUARE_PTS 4
#define SP_MIN_PTS 3
#define SP_ERODE_VSTRIDE 64 /* gd _erode: j * 64 + vertex */
#define SP_RING 2 /* the 5 x 5 lattice cells around a site */
#define SP_RING8 8 /* neighbours of a rubble cell */
#define SP_BOX_HI 3 /* the cell square spans lattice cells li - 2 .. li + 3, gd:513 */
#define SP_SPAWN_NEAR 0.15
#define SP_SPAWN_FAR 0.85
#define SP_Q_LO 0.25
#define SP_Q_HI 0.75
#define SP_QUARTERS 4
#define SP_SPLIT_OFFSET 0.25
#define SP_SPLIT_COUNT 4
#define SP_PERCENT 100.0

typedef struct { double x, y; } sp_v2;
typedef struct { int n; sp_v2 p[SP_PTS]; } sp_poly;
typedef struct {
    sp_v2 pos;
    int ix, iy, li, lj, plated, inside, erode;
} sp_site;

typedef struct {
    double cx[SP_KEYS], cy[SP_KEYS], v[SP_KEYS], us[SP_KEYS], sorted[SP_KEYS];
    double rcx[SP_RKEYS], rcy[SP_RKEYS], rv[SP_RKEYS];
    uint8_t removed[SP_KEYS];
    int first[SP_KEYS], count[SP_KEYS];
    sp_site sites[SP_SITES];
    sp_poly base[SP_SITES];
    int links[SP_SITES][SP_LINK_MAX];
    int nlinks[SP_SITES];
    int plated_ids[SP_SITES], inside_ids[SP_SITES];
    uint8_t kept[SP_SITES], mass[SP_SITES], cleared[SP_SITES], near_kept[SP_SITES];
    int poly_id[SP_SITES];
} sp_scratch;

static double sp_h01(int32_t ix, int32_t iy, int32_t ch, uint32_t ls) {
    return om_space_hash32(ix, iy, ch, ls) / SP_U32_SPAN;
}

static int sp_key(int i, int j, int stride) { return (j + SP_PAD) * stride + (i + SP_PAD); }
static int sp_clampi(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }
static int sp_floori(double x) { return (int)floor(x); }
static double sp_len(sp_v2 a) { return sqrt(a.x * a.x + a.y * a.y); }
static double sp_dist(sp_v2 a, sp_v2 b) { sp_v2 d = {a.x - b.x, a.y - b.y}; return sp_len(d); }
static double sp_dot(sp_v2 a, sp_v2 b) { return a.x * b.x + a.y * b.y; }

static void sp_sort(double *v, int n) {
    for (int i = 1; i < n; i++) {
        double x = v[i];
        int j = i - 1;
        while (j >= 0 && v[j] > x) { v[j + 1] = v[j]; j--; }
        v[j + 1] = x;
    }
}

static double sp_noise_at(const double *noise, sp_v2 pos) {
    int gx = sp_clampi((int)round(pos.x / SP_SPACING), 0, SP_DIM - 1);
    int gy = sp_clampi((int)round(pos.y / SP_SPACING), 0, SP_DIM - 1);
    return noise[gy * SP_DIM + gx];
}

/* gd _lattice: jittered square lattice of centres, indices -PAD .. wc + PAD - 1; the noise scales the jitter. */
static void sp_lattice(const double *noise, double cell, int wc, int stride, uint32_t ls, int hx, int hy,
                       double *cx, double *cy, double *v) {
    for (int j = -SP_PAD; j < wc + SP_PAD; j++)
        for (int i = -SP_PAD; i < wc + SP_PAD; i++) {
            int key = sp_key(i, j, stride);
            sp_v2 mid = {(i + 0.5) * cell, (j + 0.5) * cell};
            double vv = sp_noise_at(noise, mid);
            double amp = SP_JITTER_MAX * (0.5 + 0.5 * vv);
            v[key] = vv;
            cx[key] = (i + 0.5 + (sp_h01(i, j, hx, ls) * 2.0 - 1.0) * amp) * cell;
            cy[key] = (j + 0.5 + (sp_h01(i, j, hy, ls) * 2.0 - 1.0) * amp) * cell;
        }
}

/* gd _clip: keeps the part of a polygon with n . p <= d. */
static void sp_clip(sp_poly *poly, sp_v2 nrm, double d) {
    sp_poly out;
    out.n = 0;
    for (int i = 0; i < poly->n; i++) {
        sp_v2 a = poly->p[i], b = poly->p[(i + 1) % poly->n];
        double sa = sp_dot(nrm, a) - d, sb = sp_dot(nrm, b) - d;
        if (sa <= 0.0 && out.n < SP_PTS) out.p[out.n++] = a;
        if (((sa < 0.0 && sb > 0.0) || (sa > 0.0 && sb < 0.0)) && out.n < SP_PTS) {
            double t = sa / (sa - sb);
            out.p[out.n].x = a.x + (b.x - a.x) * t;
            out.p[out.n].y = a.y + (b.y - a.y) * t;
            out.n++;
        }
    }
    *poly = out;
}

static void sp_clip_canvas(sp_poly *poly, double canvas) {
    sp_v2 nx = {-1.0, 0.0}, px = {1.0, 0.0}, ny = {0.0, -1.0}, py = {0.0, 1.0};
    sp_clip(poly, nx, 0.0);
    sp_clip(poly, px, canvas);
    sp_clip(poly, ny, 0.0);
    sp_clip(poly, py, canvas);
}

/* gd _cell_polygon: the square lo..hi cut by the bisector against each of others, pulled in by insets toward c. The
 * first `near` are always cut; the rest only while their cut can still reach the polygon. found gets the index of every
 * neighbour whose cut leaves an edge. */
static int sp_cell_polygon(sp_v2 c, const sp_v2 *others, int n_others, int near, sp_v2 lo, sp_v2 hi,
                           const double *insets, int *found, int found_cap, sp_poly *poly) {
    sp_v2 nrm[SP_NEIGH];
    double dd[SP_NEIGH];
    uint8_t cut[SP_NEIGH];
    double reach = HUGE_VAL;
    int nf = 0;
    poly->n = SP_SQUARE_PTS;
    poly->p[0] = lo;
    poly->p[1].x = hi.x; poly->p[1].y = lo.y;
    poly->p[2] = hi;
    poly->p[SP_SQUARE_PTS - 1].x = lo.x; poly->p[SP_SQUARE_PTS - 1].y = hi.y;
    for (int idx = 0; idx < n_others; idx++) {
        sp_v2 q = others[idx], dv, mid;
        double ln;
        if (idx == near) {
            reach = 0.0;
            for (int i = 0; i < poly->n; i++) {
                double r = sp_dist(poly->p[i], c);
                if (r > reach) reach = r;
            }
        }
        dv.x = q.x - c.x; dv.y = q.y - c.y;
        ln = sp_len(dv);
        nrm[idx].x = ln > 0.0 ? dv.x / ln : 0.0;
        nrm[idx].y = ln > 0.0 ? dv.y / ln : 0.0;
        mid.x = (c.x + q.x) * 0.5; mid.y = (c.y + q.y) * 0.5;
        dd[idx] = sp_dot(nrm[idx], mid) - insets[idx];
        if (idx >= near && dd[idx] - sp_dot(nrm[idx], c) >= reach) { cut[idx] = 0; continue; }
        sp_clip(poly, nrm[idx], dd[idx]);
        cut[idx] = 1;
    }
    for (int idx = 0; idx < n_others && found; idx++) {
        sp_v2 first = {0.0, 0.0};
        int seen = 0;
        if (!cut[idx]) continue;
        for (int i = 0; i < poly->n; i++) {
            if (fabs(sp_dot(nrm[idx], poly->p[i]) - dd[idx]) < SP_EDGE_EPS) {
                if (!seen) { first = poly->p[i]; seen = 1; }
                else if (sp_dist(poly->p[i], first) > SP_LINK_EPS) {
                    if (nf < found_cap) found[nf++] = idx;
                    break;
                }
            }
        }
    }
    return nf;
}

/* gd _erode: each vertex moves toward the centroid by a hashed share (up to ERODE_MAX); canvas-edge vertices stay. */
static void sp_erode(sp_poly *poly, int i, int j, uint32_t ls, int channel, double canvas) {
    sp_v2 cen = {0.0, 0.0};
    for (int v = 0; v < poly->n; v++) { cen.x += poly->p[v].x; cen.y += poly->p[v].y; }
    cen.x /= poly->n; cen.y /= poly->n;
    for (int v = 0; v < poly->n; v++) {
        sp_v2 p = poly->p[v];
        if (p.x < SP_EDGE_EPS || p.y < SP_EDGE_EPS || p.x > canvas - SP_EDGE_EPS || p.y > canvas - SP_EDGE_EPS) continue;
        double s = sp_h01(i, j * SP_ERODE_VSTRIDE + v, channel, ls) * SP_ERODE_MAX;
        poly->p[v].x = p.x + (cen.x - p.x) * s;
        poly->p[v].y = p.y + (cen.y - p.y) * s;
    }
}

/* gd _nearest_plate: the surviving site nearest pos among the 5 x 5 lattice cells around it, or -1. */
static int sp_nearest_plate(const sp_scratch *sc, sp_v2 pos) {
    int bi = sp_clampi(sp_floori(pos.x / SP_PLATE_CELL), -1, SP_WC);
    int bj = sp_clampi(sp_floori(pos.y / SP_PLATE_CELL), -1, SP_WC);
    int best = -1;
    double best_d = HUGE_VAL;
    for (int j = bj - 2; j <= bj + 2; j++)
        for (int i = bi - 2; i <= bi + 2; i++) {
            int key = sp_key(i, j, SP_STRIDE);
            for (int t = 0; t < sc->count[key]; t++) {
                int s = sc->first[key] + t;
                double dx = sc->sites[s].pos.x - pos.x, dy = sc->sites[s].pos.y - pos.y, d = dx * dx + dy * dy;
                if (d < best_d) { best_d = d; best = s; }
            }
        }
    return best;
}

/* The two rings of neighbours of site s (ring 0 = the 3 x 3 lattice cells, ring 1 = the 5 x 5 rim), as in the gd loop. */
static int sp_gather(const sp_scratch *sc, int s, int *ids, sp_v2 *others, int *near) {
    int n = 0;
    const sp_site *site = &sc->sites[s];
    for (int ring = 0; ring < 2; ring++) {
        for (int dj = -SP_RING; dj <= SP_RING; dj++)
            for (int di = -SP_RING; di <= SP_RING; di++) {
                int adi = di < 0 ? -di : di, adj = dj < 0 ? -dj : dj;
                int in0 = (adi > adj ? adi : adj) <= 1;
                int key;
                if (in0 != (ring == 0)) continue;
                key = sp_key(site->li + di, site->lj + dj, SP_STRIDE);
                for (int t = 0; t < sc->count[key]; t++) {
                    int q = sc->first[key] + t;
                    if (q == s || n >= SP_NEIGH) continue;
                    ids[n] = q;
                    others[n] = sc->sites[q].pos;
                    n++;
                }
            }
        if (ring == 0) *near = n;
    }
    return n;
}

static int sp_emit(om_space_plates *out, int k, int kind, const sp_poly *poly) {
    om_space_plate *pl;
    if (poly->n < SP_MIN_PTS || poly->n > OM_SPACE_FIELD_MAX_PTS || out->n_plates >= OM_SPACE_FIELD_MAX_POLYS) return -1;
    if (out->per_layer[k] >= OM_SPACE_NO_REGION) return -1;
    pl = &out->plates[out->n_plates++];
    pl->layer = (uint8_t)k;
    pl->kind = (uint8_t)kind;
    pl->n_pts = (uint8_t)poly->n;
    pl->dropped = 0;
    pl->id = (uint16_t)out->per_layer[k]++;
    pl->region = OM_SPACE_NO_REGION;
    for (int v = 0; v < poly->n; v++) {
        double c[2] = {poly->p[v].x, poly->p[v].y};
        for (int a = 0; a < 2; a++) { /* D3 found a vertex at -2.84e-14: snap rounding noise at the canvas edge into [0, canvas] */
            if (c[a] < 0.0 && c[a] > -SP_CLAMP_EPS) c[a] = 0.0;
            else if (c[a] > OM_SPACE_FIELD_CANVAS_WU && c[a] < OM_SPACE_FIELD_CANVAS_WU + SP_CLAMP_EPS) c[a] = OM_SPACE_FIELD_CANVAS_WU;
        }
        pl->xy[2 * v] = c[0];
        pl->xy[2 * v + 1] = c[1];
    }
    return pl->id;
}

/* gd _build_nodes: objective, two spawns on the diagonal, two staging nodes toward the centre, one vantage. */
static void sp_nodes(double canvas, const double *xy, uint32_t n, sp_v2 *nodes) {
    sp_v2 centre = {canvas * 0.5, canvas * 0.5};
    sp_v2 spawn[2] = {{canvas * SP_SPAWN_NEAR, canvas * SP_SPAWN_NEAR}, {canvas * SP_SPAWN_FAR, canvas * SP_SPAWN_FAR}};
    if (n >= OM_SPACE_FIELD_MIN_NODES) { /* VG-D8 R-246-07: the mission's two anchors and objective replace the diagonal points */
        for (uint32_t i = 0; i < 2; i++) { spawn[i].x = xy[2 * i]; spawn[i].y = xy[2 * i + 1]; }
        centre.x = xy[2 * 2]; centre.y = xy[2 * 2 + 1];
    }
    static const double quarter[SP_QUARTERS][2] = {{SP_Q_LO, SP_Q_LO}, {SP_Q_HI, SP_Q_LO}, {SP_Q_LO, SP_Q_HI}, {SP_Q_HI, SP_Q_HI}};
    double best_score = -HUGE_VAL;
    sp_v2 best = centre;
    nodes[0] = centre;
    nodes[1] = spawn[0];
    nodes[2] = spawn[1];
    for (int s = 0; s < 2; s++) {
        sp_v2 dv = {centre.x - spawn[s].x, centre.y - spawn[s].y};
        double ln = sp_len(dv);
        nodes[SP_STAGE0 + s].x = spawn[s].x + (ln > 0.0 ? dv.x / ln : 0.0) * SP_STAGING_REACH;
        nodes[SP_STAGE0 + s].y = spawn[s].y + (ln > 0.0 ? dv.y / ln : 0.0) * SP_STAGING_REACH;
    }
    for (int q = 0; q < SP_QUARTERS; q++) {
        sp_v2 pos = {quarter[q][0] * canvas, quarter[q][1] * canvas};
        double d0 = sp_dist(pos, spawn[0]), d1 = sp_dist(pos, spawn[1]);
        double score = d0 < d1 ? d0 : d1;
        if (score > best_score + 1.0) { best_score = score; best = pos; }
    }
    nodes[SP_VANTAGE] = best;
    for (uint32_t i = OM_SPACE_FIELD_MIN_NODES; i < n && SP_NODES + (i - OM_SPACE_FIELD_MIN_NODES) < SP_NODES_MAX; i++) {
        nodes[SP_NODES + (i - OM_SPACE_FIELD_MIN_NODES)].x = xy[2 * i];
        nodes[SP_NODES + (i - OM_SPACE_FIELD_MIN_NODES)].y = xy[2 * i + 1];
    }
}

/* gd _build_plate_layer, polygons only. */
static int sp_layer(sp_scratch *sc, int k, uint32_t seed, double canvas, double density, const double *shared,
                    const double *size_noise, const sp_v2 *nodes, const double *rad, int n_nodes, om_space_plates *out) {
    uint32_t ls = seed + (uint32_t)k * SP_LAYER_SEED_STEP;
    int nsite = 0, nplated = 0, ninside = 0, tail, nkeys = SP_KEYS;
    double low_cut, high_cut, solid;
    memset(sc->removed, 0, sizeof sc->removed);
    memset(sc->kept, 0, sizeof sc->kept);
    memset(sc->mass, 0, sizeof sc->mass);
    memset(sc->cleared, 0, sizeof sc->cleared);
    memset(sc->near_kept, 0, sizeof sc->near_kept);
    memset(sc->count, 0, sizeof sc->count);
    for (int s = 0; s < SP_SITES; s++) { sc->poly_id[s] = -1; sc->nlinks[s] = 0; }

    sp_lattice(shared, SP_PLATE_CELL, SP_WC, SP_STRIDE, ls, SP_H_JITTER_X, SP_H_JITTER_Y, sc->cx, sc->cy, sc->v);
    for (int j = -SP_PAD; j < SP_WC + SP_PAD; j++)
        for (int i = -SP_PAD; i < SP_WC + SP_PAD; i++) {
            sp_v2 mid = {(i + 0.5) * SP_PLATE_CELL, (j + 0.5) * SP_PLATE_CELL};
            sc->us[sp_key(i, j, SP_STRIDE)] = sp_noise_at(size_noise, mid);
        }
    memcpy(sc->sorted, sc->us, sizeof(double) * (size_t)nkeys);
    sp_sort(sc->sorted, nkeys);
    tail = (int)floor(SP_SIZE_TAIL_SHARE * SP_SIZE_SPREAD * nkeys);
    low_cut = tail > 0 ? sc->sorted[tail] : -1.0;
    high_cut = tail > 0 ? sc->sorted[nkeys - 1 - tail] : 2.0;

    for (int j = -SP_PAD; j < SP_WC + SP_PAD; j++)
        for (int i = -SP_PAD; i < SP_WC + SP_PAD; i++) {
            int key = sp_key(i, j, SP_STRIDE), split = 0, plated, inside;
            double u = sc->us[key];
            if (tail > 0) {
                if (u > high_cut) split = 1;
                else if (u < low_cut) {
                    int free_ = 1;
                    for (int dj = -1; dj <= 1 && free_; dj++)
                        for (int di = -1; di <= 1; di++) {
                            int qi = i + di, qj = j + dj;
                            if (!di && !dj) continue;
                            if (qi >= -SP_PAD && qi < SP_WC + SP_PAD && qj >= -SP_PAD && qj < SP_WC + SP_PAD &&
                                sc->removed[sp_key(qi, qj, SP_STRIDE)]) { free_ = 0; break; }
                        }
                    if (free_) { sc->removed[key] = 1; continue; }
                }
            }
            plated = i >= -1 && i <= SP_WC && j >= -1 && j <= SP_WC;
            inside = i >= 0 && i < SP_WC && j >= 0 && j < SP_WC;
            sc->first[key] = nsite;
            if (!split) {
                sp_site *st = &sc->sites[nsite++];
                st->pos.x = sc->cx[key]; st->pos.y = sc->cy[key];
                st->ix = i; st->iy = j; st->li = i; st->lj = j; st->plated = plated; st->inside = inside;
                st->erode = SP_H_ERODE;
                sc->count[key] = 1;
                continue;
            }
            {
                double amp = SP_JITTER_MAX * (0.5 + 0.5 * sc->v[key]);
                for (int b = 0; b < 2; b++)
                    for (int a = 0; a < 2; a++) {
                        sp_site *st = &sc->sites[nsite++];
                        st->pos.x = (i + SP_SPLIT_OFFSET + 0.5 * a + (sp_h01(i * 2 + a, j * 2 + b, SP_H_SPLIT_X, ls) * 2.0 - 1.0) * amp * 0.5) * SP_PLATE_CELL;
                        st->pos.y = (j + SP_SPLIT_OFFSET + 0.5 * b + (sp_h01(i * 2 + a, j * 2 + b, SP_H_SPLIT_Y, ls) * 2.0 - 1.0) * amp * 0.5) * SP_PLATE_CELL;
                        st->ix = i * 2 + a; st->iy = j * 2 + b; st->li = i; st->lj = j;
                        st->plated = plated; st->inside = inside; st->erode = SP_H_SPLIT_ERODE;
                    }
                sc->count[key] = SP_SPLIT_COUNT;
            }
        }

    for (int s = 0; s < nsite; s++) {
        const sp_site *site = &sc->sites[s];
        int ids[SP_NEIGH], found[SP_NEIGH], near = 0, n, nf;
        sp_v2 others[SP_NEIGH], lo, hi;
        double insets[SP_NEIGH];
        if (!site->plated) continue;
        sc->plated_ids[nplated++] = s;
        if (site->inside) sc->inside_ids[ninside++] = s;
        n = sp_gather(sc, s, ids, others, &near);
        for (int q = 0; q < n; q++) insets[q] = SP_CHANNEL * 0.5;
        lo.x = (site->li - SP_RING) * SP_PLATE_CELL; lo.y = (site->lj - SP_RING) * SP_PLATE_CELL;
        hi.x = (site->li + SP_BOX_HI) * SP_PLATE_CELL; hi.y = (site->lj + SP_BOX_HI) * SP_PLATE_CELL;
        nf = sp_cell_polygon(site->pos, others, n, near, lo, hi, insets, found, SP_NEIGH, &sc->base[s]);
        for (int f = 0; f < nf && sc->nlinks[s] < SP_LINK_MAX; f++)
            if (sc->sites[ids[found[f]]].plated) sc->links[s][sc->nlinks[s]++] = ids[found[f]];
    }

    solid = (1.0 - SP_CHANNEL / SP_PLATE_CELL) * (1.0 - SP_CHANNEL / SP_PLATE_CELL) *
            (1.0 - SP_ERODE_MAX * 0.5) * (1.0 - SP_ERODE_MAX * 0.5);
    for (int t = 0; t < nplated; t++) {
        int s = sc->plated_ids[t];
        double keep_share = density > 0.0 ? density / SP_PERCENT / solid + (sp_noise_at(shared, sc->sites[s].pos) - 0.5) * SP_DENSITY_SWING : -1.0;
        sp_v2 cen = {0.0, 0.0};
        double roll;
        for (int v = 0; v < sc->base[s].n; v++) { cen.x += sc->base[s].p[v].x; cen.y += sc->base[s].p[v].y; }
        if (sc->base[s].n > 0) { cen.x /= sc->base[s].n; cen.y /= sc->base[s].n; }
        roll = sp_h01(sp_floori(cen.x / SP_PLATE_CELL), sp_floori(cen.y / SP_PLATE_CELL), SP_H_DROP, seed);
        sc->kept[s] = roll <= keep_share ? 1 : 0;
    }

    if (sp_h01(0, 0, SP_H_MASS_ON, ls) < SP_MASS_CHANCE && ninside > 0) {
        int pick = sc->inside_ids[(int)(sp_h01(0, 0, SP_H_MASS_PICK, ls) * ninside)];
        sp_v2 centre = sc->sites[pick].pos;
        for (int t = 0; t < nplated; t++) {
            int s = sc->plated_ids[t];
            if (sp_dist(sc->sites[s].pos, centre) <= SP_MASS_RADIUS) { sc->mass[s] = 1; sc->kept[s] = 1; }
        }
    }

    for (int nd = 0; nd < n_nodes; nd++) {
        int home = sp_nearest_plate(sc, nodes[nd]);
        for (int t = 0; t < nplated; t++) {
            int s = sc->plated_ids[t];
            if (!sc->cleared[s] && (s == home || sp_dist(sc->sites[s].pos, nodes[nd]) <= rad[nd])) {
                sc->cleared[s] = 1; sc->kept[s] = 0; sc->mass[s] = 0;
            }
        }
    }

    for (int t = 0; t < nplated; t++) {
        int s = sc->plated_ids[t], id;
        const sp_site *site = &sc->sites[s];
        sp_poly poly = sc->base[s];
        if (!sc->kept[s]) continue;
        if (sc->mass[s]) {
            int ids[SP_NEIGH], near = 0, n;
            sp_v2 others[SP_NEIGH], lo, hi;
            double insets[SP_NEIGH];
            n = sp_gather(sc, s, ids, others, &near);
            for (int q = 0; q < n; q++) insets[q] = sc->mass[ids[q]] ? 0.0 : SP_CHANNEL * 0.5;
            lo.x = (site->li - SP_RING) * SP_PLATE_CELL; lo.y = (site->lj - SP_RING) * SP_PLATE_CELL;
            hi.x = (site->li + SP_BOX_HI) * SP_PLATE_CELL; hi.y = (site->lj + SP_BOX_HI) * SP_PLATE_CELL;
            sp_cell_polygon(site->pos, others, n, near, lo, hi, insets, NULL, 0, &poly);
            sp_clip_canvas(&poly, canvas);
        } else {
            sp_clip_canvas(&poly, canvas);
            if (poly.n >= SP_MIN_PTS) sp_erode(&poly, site->ix, site->iy, ls, site->erode, canvas);
        }
        if (poly.n < SP_MIN_PTS) continue;
        id = sp_emit(out, k, sc->mass[s] ? OM_SPACE_KIND_MASS : OM_SPACE_KIND_PLATE, &poly);
        sc->poly_id[s] = id;
    }

    for (int t = 0; t < nplated; t++) {
        int s = sc->plated_ids[t];
        if (sc->kept[s] || sc->cleared[s]) continue;
        for (int l = 0; l < sc->nlinks[s]; l++)
            if (sc->kept[sc->links[s][l]]) { sc->near_kept[s] = 1; break; }
    }

    sp_lattice(shared, SP_RUBBLE_CELL, SP_RWC, SP_RSTRIDE, ls, SP_H_RUBBLE_X, SP_H_RUBBLE_Y, sc->rcx, sc->rcy, sc->rv);
    for (int j = -1; j < SP_RWC + 1; j++)
        for (int i = -1; i < SP_RWC + 1; i++) {
            int rk = sp_key(i, j, SP_RSTRIDE), parent, o = 0;
            sp_v2 centre, around[SP_RING8], lo, hi;
            double insets[8];
            sp_poly poly;
            if (sp_h01(i, j, SP_H_RUBBLE_KEEP, ls) >= SP_RUBBLE_SHARE * sc->rv[rk]) continue;
            centre.x = sc->rcx[rk]; centre.y = sc->rcy[rk];
            if (centre.x < -SP_RUBBLE_CELL * 0.5 || centre.y < -SP_RUBBLE_CELL * 0.5 ||
                centre.x > canvas + SP_RUBBLE_CELL * 0.5 || centre.y > canvas + SP_RUBBLE_CELL * 0.5) continue;
            parent = sp_nearest_plate(sc, centre);
            if (parent < 0 || !sc->near_kept[parent]) continue;
            for (int dj = -1; dj <= 1; dj++)
                for (int di = -1; di <= 1; di++) {
                    int q;
                    if (!di && !dj) continue;
                    q = sp_key(i + di, j + dj, SP_RSTRIDE);
                    around[o].x = sc->rcx[q]; around[o].y = sc->rcy[q]; o++;
                }
            for (int q = 0; q < SP_RING8; q++) insets[q] = SP_RUBBLE_CHANNEL * 0.5;
            lo.x = (i - 1) * SP_RUBBLE_CELL; lo.y = (j - 1) * SP_RUBBLE_CELL;
            hi.x = (i + 2) * SP_RUBBLE_CELL; hi.y = (j + 2) * SP_RUBBLE_CELL;
            sp_cell_polygon(centre, around, SP_RING8, SP_RING8, lo, hi, insets, NULL, 0, &poly);
            {
                const sp_poly *ol = &sc->base[parent];
                for (int e = 0; e < ol->n; e++) {
                    sp_v2 ed = {ol->p[(e + 1) % ol->n].x - ol->p[e].x, ol->p[(e + 1) % ol->n].y - ol->p[e].y};
                    double ln = sp_len(ed);
                    if (ln > SP_EDGE_EPS) {
                        sp_v2 outward = {ed.y / ln, -ed.x / ln};
                        sp_clip(&poly, outward, sp_dot(outward, ol->p[e]));
                    }
                }
            }
            sp_clip_canvas(&poly, canvas);
            if (poly.n < SP_MIN_PTS) continue;
            sp_erode(&poly, i, j, ls, SP_H_RUBBLE_ERODE, canvas);
            sp_emit(out, k, OM_SPACE_KIND_RUBBLE, &poly);
        }

    for (int t = 0; t < nplated; t++) {
        int s = sc->plated_ids[t], a = sc->poly_id[s];
        if (a < 0) continue;
        for (int l = 0; l < sc->nlinks[s]; l++) {
            int q = sc->links[s][l], b = sc->poly_id[q], recip = 0;
            if (b < 0 || a == b) continue;
            if (a > b) {
                for (int m = 0; m < sc->nlinks[q]; m++) if (sc->links[q][m] == s) { recip = 1; break; }
                if (recip) continue;
            }
            if (out->n_links < OM_SPACE_MAX_LINKS) {
                om_space_link *lk = &out->links[out->n_links++];
                lk->layer = (uint8_t)k;
                lk->a = (uint16_t)(a < b ? a : b);
                lk->b = (uint16_t)(a < b ? b : a);
            }
        }
    }
    return 0;
}

int om_space_plates_build_nodes(uint32_t seed, double canvas, double density, const double *node_xy, const double *node_radius,
                               uint32_t n_nodes, om_space_plates *out) {
    sp_scratch *sc;
    double *shared, *size_noise;
    sp_v2 nodes[SP_NODES_MAX];
    double rad[SP_NODES_MAX];
    int rc = 0, total;
    if (!out || canvas != OM_SPACE_FIELD_CANVAS_WU) return -1;
    memset(out, 0, sizeof *out);
    if (!(density > 0.0)) density = 0.0;
    if (density > SP_DENSITY_MAX) density = SP_DENSITY_MAX;
    sc = malloc(sizeof *sc);
    shared = malloc(sizeof(double) * SP_DIM * SP_DIM);
    size_noise = malloc(sizeof(double) * SP_DIM * SP_DIM);
    if (!sc || !shared || !size_noise) { free(sc); free(shared); free(size_noise); return -1; }
    if (om_space_noise_layer(seed, canvas, 0, 1, shared, SP_DIM * SP_DIM) == 0) rc = -1;
    if (n_nodes > OM_SPACE_FIELD_MAX_NODES) n_nodes = OM_SPACE_FIELD_MAX_NODES;
    if (n_nodes < OM_SPACE_FIELD_MIN_NODES) n_nodes = 0;
    sp_nodes(canvas, node_xy, n_nodes, nodes);
    total = SP_NODES + (n_nodes > OM_SPACE_FIELD_MIN_NODES ? (int)n_nodes - OM_SPACE_FIELD_MIN_NODES : 0);
    memset(rad, 0, sizeof rad);
    if (n_nodes >= OM_SPACE_FIELD_MIN_NODES) { rad[0] = node_radius[2]; rad[1] = node_radius[0]; rad[2] = node_radius[1]; /* nodes: objective, spawns */ }
    for (uint32_t i = OM_SPACE_FIELD_MIN_NODES; i < n_nodes; i++) rad[SP_NODES + (i - OM_SPACE_FIELD_MIN_NODES)] = node_radius[i];
    for (int i = 0; i < total; i++) if (!(rad[i] > 0.0)) rad[i] = SP_CLEAR_RADIUS;
    for (int k = 0; k < OM_SPACE_FIELD_LAYERS && rc == 0; k++) {
        uint32_t ls = seed + (uint32_t)k * SP_LAYER_SEED_STEP;
        if (om_space_noise_layer(ls + SP_SIZE_SEED_OFFSET, canvas, (uint32_t)k, 1, size_noise, SP_DIM * SP_DIM) == 0) { rc = -1; break; }
        rc = sp_layer(sc, k, seed, canvas, density, shared, size_noise, nodes, rad, total, out);
    }
    free(sc); free(shared); free(size_noise);
    return rc;
}

int om_space_plates_build(uint32_t seed, double canvas, double density, om_space_plates *out) {
    return om_space_plates_build_nodes(seed, canvas, density, NULL, NULL, 0, out);
}
