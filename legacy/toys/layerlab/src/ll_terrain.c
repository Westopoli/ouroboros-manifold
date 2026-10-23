/* ll_terrain.c -- grid queries, slope geometry and flow fields (SPEC 5.9, 5.10, 6).
 *
 * A flow field is a Dijkstra cost-to-go in seconds, for one unit type, from the goal node (goal cell, goal
 * layer) over nodes (cell, layer), cached in s->nav by (goal cell, goal layer, movement kind, unit type,
 * auto_transition). Determinism: an indexed binary heap ordered by (cost, node index), neighbours in a
 * fixed order, no pointer-keyed structures. */
#include <stdlib.h>
#include <math.h>
#include "ll_nav.h"

double ll_terrain_width(const ll_terrain *t)  { return (double)t->w_cells * t->cell; }
double ll_terrain_height(const ll_terrain *t) { return (double)t->h_cells * t->cell; }

int ll_terrain_cell(const ll_terrain *t, double x, double y) {
    if (!(x >= 0.0 && y >= 0.0)) return -1;
    if (!(x < ll_terrain_width(t) && y < ll_terrain_height(t))) return -1;
    int cx = (int)(x / t->cell), cy = (int)(y / t->cell);
    if (cx >= t->w_cells) cx = t->w_cells - 1;    /* guards x/cell rounding up at the edge */
    if (cy >= t->h_cells) cy = t->h_cells - 1;
    return cy * t->w_cells + cx;
}

int ll_terrain_open(const ll_terrain *t, double x, double y, int layer) {
    int c = ll_terrain_cell(t, x, y);
    if (c < 0 || layer < 1 || layer > LL_LAYERS) return 0;
    return (t->open[c] >> (layer - 1)) & 1;
}

int ll_terrain_land(const ll_terrain *t, double x, double y, int layer) {
    int c = ll_terrain_cell(t, x, y);
    if (c < 0 || layer < 1 || layer > LL_LAYERS) return 0;
    return (t->land[c] >> (layer - 1)) & 1;
}

int ll_cell_passable(const ll_terrain *t, int cell, int layer, int walker) {
    unsigned bit = 1u << (layer - 1);
    if (!(t->open[cell] & bit)) return 0;
    return !walker || (t->land[cell] & bit) != 0;
}

void ll_cell_centre(const ll_terrain *t, int cell, double *x, double *y) {
    *x = ((double)(cell % t->w_cells) + 0.5) * t->cell;
    *y = ((double)(cell / t->w_cells) + 0.5) * t->cell;
}

/* Sampled every half cell, both endpoints included; every sampled cell must be passable on `layer`. */
int ll_segment_clear(const ll_terrain *t, double x0, double y0, double x1, double y1, int layer, int walker) {
    double dx = x1 - x0, dy = y1 - y0;
    double len = sqrt(dx * dx + dy * dy);
    int n = (int)(len / (0.5 * t->cell)) + 1;
    for (int i = 0; i <= n; i++) {
        double f = (double)i / (double)n;
        int c = ll_terrain_cell(t, x0 + dx * f, y0 + dy * f);
        if (c < 0 || !ll_cell_passable(t, c, layer, walker)) return 0;
    }
    return 1;
}

/* ---- validation ---- */

const char *ll_terrain_validate(const ll_terrain *t) {
    if (t->w_cells < 1 || t->w_cells > LL_MAX_GRID_W) return "terrain: w_cells out of range";
    if (t->h_cells < 1 || t->h_cells > LL_MAX_GRID_H) return "terrain: h_cells out of range";
    if (!ll_finite(t->cell) || t->cell <= 0.0) return "terrain: cell must be positive";
    if (!ll_finite(t->layer_spacing) || t->layer_spacing < 0.0) return "terrain: layer_spacing must be >= 0";
    if (t->n_cover < 0 || t->n_cover > LL_MAX_COVER) return "terrain: n_cover out of range";
    if (t->n_vantage < 0 || t->n_vantage > LL_MAX_VANTAGE) return "terrain: n_vantage out of range";
    if (t->n_zone < 0 || t->n_zone > LL_MAX_ZONES) return "terrain: n_zone out of range";
    if (t->n_slope < 0 || t->n_slope > LL_MAX_SLOPES) return "terrain: n_slope out of range";
    for (int i = 0; i < t->w_cells * t->h_cells; i++)
        if (t->land[i] & ~t->open[i]) return "terrain: land must be a subset of open";
    for (int i = 0; i < t->n_slope; i++) {
        const ll_slope *s = &t->slope[i];
        if (!ll_finite(s->x0) || !ll_finite(s->y0) || !ll_finite(s->dx) || !ll_finite(s->dy) ||
            !ll_finite(s->length) || !ll_finite(s->width))
            return "terrain: slope has a non-finite field";
        double n = sqrt(s->dx * s->dx + s->dy * s->dy);
        if (!(n > 1.0 - 1e-6 && n < 1.0 + 1e-6)) return "terrain: slope direction must be a unit vector";
        if (!(s->length > 0.0) || !(s->width > 0.0)) return "terrain: slope length and width must be > 0";
        if (s->bottom_layer < 1 || s->top_layer > LL_LAYERS || s->bottom_layer >= s->top_layer)
            return "terrain: slope layers must satisfy 1 <= bottom < top <= LL_LAYERS";
    }
    for (int i = 0; i < t->n_cover; i++) {
        const ll_cover *c = &t->cover[i];
        if (!ll_finite(c->x) || !ll_finite(c->y) || !ll_finite(c->r) || c->r < 0.0)
            return "terrain: cover disc has a bad field";
        if (c->height_layer < 0 || c->height_layer > LL_LAYERS) return "terrain: cover height_layer out of range";
    }
    for (int i = 0; i < t->n_vantage; i++) {
        const ll_vantage *v = &t->vantage[i];
        if (!ll_finite(v->x) || !ll_finite(v->y) || !ll_finite(v->r) || v->r < 0.0)
            return "terrain: vantage disc has a bad field";
    }
    for (int i = 0; i < t->n_zone; i++) {
        const ll_zone *z = &t->zone[i];
        if (!ll_finite(z->x) || !ll_finite(z->y) || !ll_finite(z->r) || z->r < 0.0 ||
            !ll_finite(z->intensity) || z->intensity < 0.0)
            return "terrain: interference zone has a bad field";
        if (z->layer < 1 || z->layer > LL_LAYERS) return "terrain: zone layer out of range";
    }
    return 0;
}

/* ---- slope geometry (SPEC 5.1, 5.9) ---- */

void ll_slope_edge(const ll_slope *sl, int top, double *x, double *y) {
    double f = top ? sl->length : 0.0;
    *x = sl->x0 + sl->dx * f;
    *y = sl->y0 + sl->dy * f;
}

/* B + count of k in 1..n with t >= (k - 0.5) / n. The 1e-9 absorbs the rounding of a position that is
 * accumulated tick by tick, so a unit exactly on a cross-over counts as past it. */
int ll_slope_layer(const ll_slope *sl, double t) {
    int n = sl->top_layer - sl->bottom_layer, count = 0;
    for (int k = 1; k <= n; k++)
        if (t >= ((double)k - 0.5) / (double)n - 1e-9) count++;
    return sl->bottom_layer + count;
}

int ll_goal_cell(const ll_terrain *t, double gx, double gy, int layer, int walker, int *snapped) {
    *snapped = 0;
    int c = ll_terrain_cell(t, gx, gy);
    if (c >= 0)
        for (int l = 1; l <= LL_LAYERS; l++)
            if (ll_cell_passable(t, c, l, walker)) return c;
    *snapped = 1;
    int best = -1;
    double bd = 0.0;
    for (int i = 0; i < t->w_cells * t->h_cells; i++) {
        if (!ll_cell_passable(t, i, layer, walker)) continue;
        double cx, cy;
        ll_cell_centre(t, i, &cx, &cy);
        double d = (cx - gx) * (cx - gx) + (cy - gy) * (cy - gy);
        if (best < 0 || d < bd) { best = i; bd = d; }
    }
    return best;
}

/* Nearest layer to `layer` on which `cell` is passable, ties to the lower layer; 0 when there is none. */
int ll_goal_layer(const ll_terrain *t, int cell, int layer, int walker) {
    for (int d = 0; d < LL_LAYERS; d++) {
        int lo = layer - d, hi = layer + d;
        if (lo >= 1 && lo <= LL_LAYERS && ll_cell_passable(t, cell, lo, walker)) return lo;
        if (d > 0 && hi >= 1 && hi <= LL_LAYERS && ll_cell_passable(t, cell, hi, walker)) return hi;
    }
    return 0;
}

/* ---- flow fields (SPEC 5.10) ---- */

#define NAV_SLOTS 16

struct ll_field {
    int goal_cell, goal_layer, walker, type, auto_tr;   /* the cache key; goal_cell < 0 marks an empty slot */
    double speed, trans_s;                /* of the unit type: edge costs are distance / speed seconds */
    unsigned long long stamp;             /* last use, for deterministic eviction */
    int sb[LL_MAX_SLOPES], st[LL_MAX_SLOPES];   /* cell of each slope's bottom and top edge, -1 outside */
    double *cost;                         /* per node, node = cell * LL_LAYERS + layer - 1 */
};

typedef struct ll_nav {
    ll_field slot[NAV_SLOTS];
    double *pool;                         /* NAV_SLOTS * n_nodes costs */
    int *heap, *pos;                      /* indexed binary heap scratch, n_nodes each */
    int n_nodes;
    unsigned long long clock;
} ll_nav;

int ll_nav_init(ll_state *s) {
    s->nav = 0;
    ll_nav *nv = (ll_nav *)calloc(1, sizeof *nv);
    int n_nodes = s->ter->w_cells * s->ter->h_cells * LL_LAYERS;
    if (nv) {
        nv->n_nodes = n_nodes;
        nv->pool = (double *)malloc((size_t)NAV_SLOTS * (size_t)n_nodes * sizeof(double));
        nv->heap = (int *)malloc((size_t)n_nodes * sizeof(int));
        nv->pos = (int *)malloc((size_t)n_nodes * sizeof(int));
    }
    if (!nv || !nv->pool || !nv->heap || !nv->pos) {
        if (nv) { free(nv->pool); free(nv->heap); free(nv->pos); free(nv); }
        ll_err("nav: out of memory");
        return 1;
    }
    for (int i = 0; i < NAV_SLOTS; i++) {
        nv->slot[i].goal_cell = -1;
        nv->slot[i].cost = nv->pool + (size_t)i * (size_t)n_nodes;
    }
    s->nav = nv;
    return 0;
}

void ll_nav_free(ll_state *s) {
    ll_nav *nv = (ll_nav *)s->nav;
    if (nv) { free(nv->pool); free(nv->heap); free(nv->pos); free(nv); }
    s->nav = 0;
}

/* Every layer change or slope mount costs this many seconds more than the SPEC's price. It is far below the
 * 1e-6 s tie rule and only makes a route with fewer changes win an exact tie as a whole, not just at its
 * first step; TIE_EPS absorbs the rounding of summed doubles when two steps are compared. */
#define CHANGE_EPS 1e-9
#define TIE_EPS 1e-12

typedef struct edge { int cell, layer, kind, slope; double w; } edge;
#define MAX_EDGES (8 + LL_LAYERS + 2 * LL_MAX_SLOPES)

/* Edges out of node (cell, layer), in the fixed order: 8 neighbours (orthogonal first), layer changes
 * by ascending layer, slopes by index. Every edge has a twin of equal cost, so a field built from the
 * goal is a cost-to-go. */
static int edges(const ll_state *s, const ll_field *f, int cell, int layer, edge *e) {
    static const int dxs[8] = {1, -1, 0, 0, 1, 1, -1, -1};
    static const int dys[8] = {0, 0, 1, -1, 1, -1, 1, -1};
    const ll_terrain *t = s->ter;
    int w = t->w_cells, h = t->h_cells, cx = cell % w, cy = cell / w, n = 0;
    double straight = t->cell / f->speed, diag = t->cell * sqrt(2.0) / f->speed;
    for (int k = 0; k < 8; k++) {
        int nx = cx + dxs[k], ny = cy + dys[k];
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        if (!ll_cell_passable(t, ny * w + nx, layer, f->walker)) continue;
        if (k >= 4 && (!ll_cell_passable(t, cy * w + nx, layer, f->walker) ||
                       !ll_cell_passable(t, ny * w + cx, layer, f->walker))) continue;   /* no corner cutting */
        e[n].cell = ny * w + nx; e[n].layer = layer; e[n].kind = LL_STEP_MOVE; e[n].slope = -1;
        e[n].w = k >= 4 ? diag : straight;
        n++;
    }
    if (!f->walker && f->auto_tr) {
        for (int m = 1; m <= LL_LAYERS; m++) {
            if (m == layer || !ll_cell_passable(t, cell, m, 0)) continue;
            e[n].cell = cell; e[n].layer = m; e[n].kind = LL_STEP_LAYER; e[n].slope = -1;
            e[n].w = f->trans_s + (double)s->rules->forced_change_penalty * (double)(m > layer ? m - layer : layer - m) / f->speed + CHANGE_EPS;
            n++;
        }
    }
    if (f->walker) {
        for (int i = 0; i < t->n_slope; i++) {
            const ll_slope *sl = &t->slope[i];
            int to = -1, tl = 0;
            if (f->sb[i] == cell && sl->bottom_layer == layer) { to = f->st[i]; tl = sl->top_layer; }
            else if (f->st[i] == cell && sl->top_layer == layer) { to = f->sb[i]; tl = sl->bottom_layer; }
            if (to < 0 || !ll_cell_passable(t, to, tl, 1)) continue;
            e[n].cell = to; e[n].layer = tl; e[n].kind = LL_STEP_SLOPE; e[n].slope = i;
            e[n].w = sl->length / f->speed + CHANGE_EPS;
            n++;
        }
    }
    return n;
}

static int heap_less(const double *cost, int a, int b) {
    return cost[a] < cost[b] || (cost[a] == cost[b] && a < b);
}

static void sift_up(ll_nav *nv, const double *cost, int i) {
    int node = nv->heap[i];
    while (i > 0) {
        int p = (i - 1) / 2;
        if (!heap_less(cost, node, nv->heap[p])) break;
        nv->heap[i] = nv->heap[p];
        nv->pos[nv->heap[i]] = i;
        i = p;
    }
    nv->heap[i] = node;
    nv->pos[node] = i;
}

static void sift_down(ll_nav *nv, const double *cost, int n, int i) {
    int node = nv->heap[i];
    for (;;) {
        int c = 2 * i + 1;
        if (c >= n) break;
        if (c + 1 < n && heap_less(cost, nv->heap[c + 1], nv->heap[c])) c++;
        if (!heap_less(cost, nv->heap[c], node)) break;
        nv->heap[i] = nv->heap[c];
        nv->pos[nv->heap[i]] = i;
        i = c;
    }
    nv->heap[i] = node;
    nv->pos[node] = i;
}

static void build_field(const ll_state *s, ll_nav *nv, ll_field *f) {
    const ll_terrain *t = s->ter;
    double *cost = f->cost;
    int hn = 0;
    for (int i = 0; i < nv->n_nodes; i++) { cost[i] = LL_FAR; nv->pos[i] = -1; }
    for (int i = 0; i < t->n_slope; i++) {
        double x, y;
        ll_slope_edge(&t->slope[i], 0, &x, &y);
        f->sb[i] = ll_terrain_cell(t, x, y);
        ll_slope_edge(&t->slope[i], 1, &x, &y);
        f->st[i] = ll_terrain_cell(t, x, y);
    }
    if (ll_cell_passable(t, f->goal_cell, f->goal_layer, f->walker)) {
        int node = f->goal_cell * LL_LAYERS + f->goal_layer - 1;
        cost[node] = 0.0;
        nv->heap[hn] = node;
        sift_up(nv, cost, hn);
        hn++;
    }
    while (hn > 0) {
        int node = nv->heap[0];
        hn--;
        nv->pos[node] = -1;
        if (hn > 0) { nv->heap[0] = nv->heap[hn]; sift_down(nv, cost, hn, 0); }
        edge e[MAX_EDGES];
        int n = edges(s, f, node / LL_LAYERS, node % LL_LAYERS + 1, e);
        for (int k = 0; k < n; k++) {
            int to = e[k].cell * LL_LAYERS + e[k].layer - 1;
            double c = cost[node] + e[k].w;
            if (!(c < cost[to])) continue;
            cost[to] = c;
            if (nv->pos[to] < 0) { nv->heap[hn] = to; sift_up(nv, cost, hn); hn++; }
            else sift_up(nv, cost, nv->pos[to]);
        }
    }
}

const ll_field *ll_nav_field(ll_state *s, int goal_cell, int goal_layer, int type) {
    ll_nav *nv = (ll_nav *)s->nav;
    if (!nv || goal_cell < 0 || goal_cell >= s->ter->w_cells * s->ter->h_cells) return 0;
    if (goal_layer < 1 || goal_layer > LL_LAYERS || type < 0 || type >= s->sc->n_types) return 0;
    const ll_unit_type *ty = &s->sc->types[type];
    int walker = ty->movement_kind == LL_MOVE_WALK, auto_tr = s->rules->auto_transition;
    for (int i = 0; i < NAV_SLOTS; i++) {
        ll_field *f = &nv->slot[i];
        if (f->goal_cell == goal_cell && f->goal_layer == goal_layer && f->type == type && f->walker == walker &&
            f->auto_tr == auto_tr) {
            f->stamp = ++nv->clock;
            return f;
        }
    }
    int victim = 0;                                  /* first empty slot, else the least recently used */
    for (int i = 0; i < NAV_SLOTS && nv->slot[victim].goal_cell >= 0; i++)
        if (nv->slot[i].goal_cell < 0 || nv->slot[i].stamp < nv->slot[victim].stamp) victim = i;
    ll_field *f = &nv->slot[victim];
    f->goal_cell = goal_cell;
    f->goal_layer = goal_layer;
    f->type = type;
    f->walker = walker;
    f->auto_tr = auto_tr;
    f->speed = ty->speed;
    f->trans_s = ty->transition_s;
    build_field(s, nv, f);
    f->stamp = ++nv->clock;
    return f;
}

double ll_field_cost(const ll_field *f, int cell, int layer) {
    return f->cost[cell * LL_LAYERS + layer - 1];
}

/* Descent from (cell, layer): the edge minimising edge cost + cost-to-go. A same-layer move wins any
 * tie with a layer change or a slope (within 1e-6 s), so a unit changes layer or mounts only where the
 * way on is blocked or dearer. Within a kind, equal totals (within TIE_EPS, rounding) go to the lower node. */
int ll_field_step(const ll_state *s, const ll_field *f, int cell, int layer, ll_step *out) {
    edge e[MAX_EDGES];
    int n = edges(s, f, cell, layer, e);
    int bm = -1, bo = -1;
    double tm = LL_FAR, to = LL_FAR;
    for (int k = 0; k < n; k++) {
        double c = ll_field_cost(f, e[k].cell, e[k].layer);
        if (c >= LL_FAR) continue;
        double tot = e[k].w + c;
        int node = e[k].cell * LL_LAYERS + e[k].layer;
        if (e[k].kind == LL_STEP_MOVE) {
            if (bm < 0 || tot < tm - TIE_EPS ||
                (tot <= tm + TIE_EPS && node < e[bm].cell * LL_LAYERS + e[bm].layer)) { bm = k; tm = tot; }
        } else if (bo < 0 || tot < to - TIE_EPS ||
                   (tot <= to + TIE_EPS && node < e[bo].cell * LL_LAYERS + e[bo].layer)) { bo = k; to = tot; }
    }
    int k = bm;
    if (bo >= 0 && (bm < 0 || to < tm - 1e-6)) k = bo;
    if (k < 0) return 0;
    out->kind = e[k].kind;
    out->cell = e[k].cell;
    out->layer = e[k].layer;
    out->slope = e[k].slope;
    return 1;
}
