/* Places lane P1 units 2 to 4: argument validation, the objective and the two bases, the cached grid, the score,
 * the resource-hosting towns, the other towns by score, their ages, satellites, richness and the order
 * (docs/northstar/plans/2026-10-13-places-lane-spec.md, "P1 the engine", steps 1 to 9).
 * Pure function of its arguments: no world, no global state. The engine calls nothing defined in layout_terrain.c
 * (gap 3): the grid is filled only through the t->height_at and t->walkable_at callbacks. */
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "layout_internal.h"
#include "om_internal.h"

#define LAYOUT_CANVAS_MAX     24000   /* canvas side cap, wu (spec P1 interface) */
#define LAYOUT_CANVAS_CELL    100     /* canvas is a multiple of one 100 wu cell (spec P1 interface) */
#define LAYOUT_ARCHETYPES     10      /* archetype ids 0..9 (mission.c:161-170, R-177-02 table) */
#define LAYOUT_HOME_AGE       40      /* DRAFT-home-age: growth steps a HOME base has lived */

#define LAYOUT_CELL_WU        100.0   /* canvas cell, wu (spec P1 algorithm: the canvas is a grid of side/100 cells) */
#define LAYOUT_GRID_STEP      4       /* DRAFT-places-grid 400 wu: candidates are the cells with index 1 mod 4 */
#define LAYOUT_WATER_R        6       /* DRAFT-places-water-radius 600 wu in cells: loop bound for the disc below */
#define LAYOUT_WATER_R2       36      /* DRAFT-places-water-radius 600 wu: squared cell distance, inclusive (gap 5) */
#define LAYOUT_WATER_SAT      12.0    /* DRAFT-places-water-sat: water cells that saturate water_within */
#define LAYOUT_FLAT_R2        9       /* DRAFT-places-flat-radius 300 wu: squared cell distance, inclusive (gap 5) */
#define LAYOUT_FLAT_SLOPE     0.06    /* DRAFT-places-flat-slope: a cell is flat when its slope is under this (strict, gap 5) */
#define LAYOUT_W_WATER        0.45    /* DRAFT-places-weights: water_within */
#define LAYOUT_W_FLAT         0.30    /* DRAFT-places-weights: flatness */
#define LAYOUT_W_NOISE        0.25    /* DRAFT-places-weights: noise01 */
#define LAYOUT_NOISE_LATTICE  1600    /* DRAFT-places-noise-lattice, wu */
#define LAYOUT_NOISE_OCTAVES  3       /* DRAFT-places-noise-octaves (gain 0.5) */
#define LAYOUT_NOISE_GAIN     32768   /* DRAFT-places-noise-octaves: gain 0.5 in Q16 */
#define LAYOUT_Q16_ONE        65536   /* Q16 one */
#define LAYOUT_NOISE_SPAN     131072.0 /* fbm range -65536..65536 mapped to 0..1 */
#define LAYOUT_SALT_PLACES    410     /* seed salt of the score noise (added to the seed) */
#define LAYOUT_SALT_AGE       450     /* seed salt of the age noise */
#define LAYOUT_SALT_RICH      460     /* seed salt of the richness noise */
#define LAYOUT_SPACING        4000.0  /* DRAFT-places-spacing, wu */
#define LAYOUT_RES_CLEARANCE  2400.0  /* DRAFT-resource-clearance, wu */
#define LAYOUT_RES_FAIRNESS   600.0   /* DRAFT-resource-fairness, wu */
#define LAYOUT_SAT_OFFSET     300.0   /* DRAFT-satellite-offset, wu */
#define LAYOUT_AGE_MIN        10      /* DRAFT-town-age-min */
#define LAYOUT_AGE_SPAN       30      /* DRAFT-town-age-max 40 minus DRAFT-town-age-min 10 */
#define LAYOUT_RICH_BASE      0.2     /* DRAFT-richness-formula */
#define LAYOUT_RICH_SLOPE     0.8     /* DRAFT-richness-formula */
#define LAYOUT_RICH_MID       0.5     /* DRAFT-richness-formula */
#define LAYOUT_RICH_MAX       100     /* richness is 0..100 */
#define LAYOUT_DEFENDER_SLANT 10      /* DRAFT-defender-slant */
#define LAYOUT_FLOOR          0.35    /* DRAFT-places-floor: a further town needs a score above this (strict) */
#define LAYOUT_TOWNS_MAX      6       /* DRAFT-towns-max: settlements and HOME bases together are fewer than this before one more */
#define LAYOUT_SAT_AXES       4       /* satellite axis steps E, S, W, N (spec step 7) */
#define LAYOUT_SAT_SHIFT      14      /* spec step 7: start index is (u_q16 >> 14) & 3 */

/* R-177-02, a rule not a draft: base kind per archetype, player then enemy. HOME = a grown town, FORWARD = a camp. */
static const int32_t layout_base_kind[LAYOUT_ARCHETYPES][2] = {
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Defensive Stand */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_FORWARD },  /* Siege Breaking: relief camp, siege camp */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_HOME },     /* Reconquest: the city being taken */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_HOME },     /* Assault: the city or fortress being taken */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Suppression: garrison in a city */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Multi-Front Defense */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_FORWARD },  /* Interception: field camp, staging camp */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Evacuation: the place being left */
    { OM_PLACE_BASE_FORWARD, OM_PLACE_BASE_FORWARD },  /* Containment */
    { OM_PLACE_BASE_HOME,    OM_PLACE_BASE_FORWARD },  /* Counterinsurgency: garrison in a city */
};

static int layout_canvas_ok(double w, double h)
{
    if (w != h || w <= 0.0 || w > (double)LAYOUT_CANVAS_MAX) return 0;
    return (int64_t)w % LAYOUT_CANVAS_CELL == 0 && (double)(int64_t)w == w;
}

static om_place layout_base(double x, double y, int32_t kind, int32_t side)
{
    om_place p;
    memset(&p, 0, sizeof p);
    p.x = x;
    p.y = y;
    p.kind = kind;
    p.side = side;
    p.age_steps = kind == OM_PLACE_BASE_HOME ? LAYOUT_HOME_AGE : 0;
    return p;
}

/* The cached grid and the candidate scores. Heights are read once through t->height_at, at cell centres. */
typedef struct layout_work {
    int      n;      /* cells per side */
    int      m;      /* candidates per side: cells 1 mod 4 */
    double  *h;      /* n*n heights */
    double  *s;      /* m*m scores (step 3) */
    uint8_t *water;  /* n*n: height < 0.0 */
    uint8_t *flat;   /* n*n: slope under DRAFT-places-flat-slope; an edge cell takes its inner neighbour (om_layout_slope) */
    uint8_t *ok;     /* m*m: the candidate is valid (not water and walkable at its centre) */
} layout_work;

/* Two bases and the objective, with d the unit vector perpendicular to B1-B0. */
typedef struct layout_geom {
    double canvas, b0x, b0y, b1x, b1y, ox, oy, dx, dy;
} layout_geom;

static int32_t layout_noise_q16(double wu)
{
    return (int32_t)((int64_t)wu * LAYOUT_Q16_ONE / LAYOUT_NOISE_LATTICE);
}

static double layout_noise01(uint64_t seed, int salt, double x, double y)
{
    int32_t f = om_tn_fbm2(seed + (uint64_t)salt, layout_noise_q16(x), layout_noise_q16(y),
                           LAYOUT_NOISE_OCTAVES, LAYOUT_NOISE_GAIN);
    return (double)(f + LAYOUT_Q16_ONE) / LAYOUT_NOISE_SPAN;
}

static double layout_dist(double ax, double ay, double bx, double by)
{
    return sqrt((ax - bx) * (ax - bx) + (ay - by) * (ay - by));
}

static double layout_cell_centre(int i)
{
    return (double)i * LAYOUT_CELL_WU + LAYOUT_CELL_WU * 0.5;
}

/* Step 3: the score of the candidate (a, b); cells of the discs that fall outside the canvas are not counted
 * (flatness is the share of the cells that exist within 300 wu). */
static double layout_score(const layout_work *g, uint64_t seed, int a, int b)
{
    int ci = LAYOUT_GRID_STEP * a + 1, cj = LAYOUT_GRID_STEP * b + 1;
    int di, dj, nw = 0, flat = 0, inside = 0;
    double flatness;
    for (dj = -LAYOUT_WATER_R; dj <= LAYOUT_WATER_R; dj++) {
        for (di = -LAYOUT_WATER_R; di <= LAYOUT_WATER_R; di++) {
            int d2 = di * di + dj * dj, i = ci + di, j = cj + dj;
            if (d2 > LAYOUT_WATER_R2 || i < 0 || i >= g->n || j < 0 || j >= g->n) continue;
            if (g->water[j * g->n + i]) nw++;
            if (d2 <= LAYOUT_FLAT_R2) {
                inside++;
                if (g->flat[j * g->n + i]) flat++;
            }
        }
    }
    flatness = (double)flat / (double)inside;
    return LAYOUT_W_WATER * fmin(1.0, (double)nw / LAYOUT_WATER_SAT) + LAYOUT_W_FLAT * flatness
         + LAYOUT_W_NOISE * layout_noise01(seed, LAYOUT_SALT_PLACES, layout_cell_centre(ci), layout_cell_centre(cj));
}

static void layout_work_free(layout_work *g)
{
    free(g->h);
    free(g->water);
    g->h = NULL;
    g->water = NULL;
}

/* Reads the grid once and scores every valid candidate. Returns 0, or -1 when the allocation fails. */
static int layout_work_fill(layout_work *g, uint64_t seed, double canvas, const om_layout_terrain *t)
{
    int n = (int)(canvas / LAYOUT_CELL_WU), m = (n + LAYOUT_GRID_STEP - 2) / LAYOUT_GRID_STEP;
    int i, j, a, b;
    size_t cells = (size_t)n * (size_t)n, cands = (size_t)m * (size_t)m;
    memset(g, 0, sizeof *g);
    g->n = n;
    g->m = m;
    g->h = (double *)malloc((cells + cands) * sizeof(double));
    g->water = (uint8_t *)malloc(2 * cells + cands);
    if (!g->h || !g->water) {
        layout_work_free(g);
        return -1;
    }
    g->s = g->h + cells;
    g->flat = g->water + cells;
    g->ok = g->flat + cells;
    for (j = 0; j < n; j++) {
        for (i = 0; i < n; i++) {
            double hh = t->height_at(t->ctx, layout_cell_centre(i), layout_cell_centre(j));
            g->h[j * n + i] = hh;
            g->water[j * n + i] = hh < 0.0;
        }
    }
    for (j = 0; j < n; j++) {
        for (i = 0; i < n; i++) {
            int i1 = i + 1 < n ? i + 1 : i - 1, j1 = j + 1 < n ? j + 1 : j - 1;
            double hc = g->h[j * n + i];
            double rise = fmax(fabs(g->h[j * n + i1] - hc), fabs(g->h[j1 * n + i] - hc));
            g->flat[j * n + i] = rise / LAYOUT_CELL_WU < LAYOUT_FLAT_SLOPE;
        }
    }
    for (b = 0; b < m; b++) {
        for (a = 0; a < m; a++) {
            int ci = LAYOUT_GRID_STEP * a + 1, cj = LAYOUT_GRID_STEP * b + 1;
            int ok = !g->water[cj * n + ci] && t->walkable_at(t->ctx, layout_cell_centre(ci), layout_cell_centre(cj));
            g->ok[b * m + a] = (uint8_t)ok;
            g->s[b * m + a] = ok ? layout_score(g, seed, a, b) : 0.0;
        }
    }
    return 0;
}

/* The fixed tie-break: greatest score, then lower y, then lower x; an equal candidate keeps the lower index
 * because the callers scan in index order and replace only on a strictly better one. */
static int layout_better(double s, double y, double x, int have, double bs, double by, double bx)
{
    if (!have) return 1;
    if (s != bs) return s > bs;
    if (y != by) return y < by;
    return x < bx;
}

/* Step 4 for one side sigma: the best valid candidate (no floor) that is clear of the objective along d, level
 * between the bases, 4000 wu from both bases, with a valid satellite point. Returns 1 and fills p and q, else 0. */
static int layout_resource_town(const layout_work *g, const om_layout_terrain *t, const layout_geom *geo,
                                double sigma, double *px, double *py, double *qx, double *qy)
{
    int a, b, have = 0;
    double bs = 0.0, by = 0.0, bx = 0.0;
    for (b = 0; b < g->m; b++) {
        for (a = 0; a < g->m; a++) {
            double x, y, s, tt, q_x, q_y;
            if (!g->ok[b * g->m + a]) continue;
            x = layout_cell_centre(LAYOUT_GRID_STEP * a + 1);
            y = layout_cell_centre(LAYOUT_GRID_STEP * b + 1);
            s = g->s[b * g->m + a];
            if (!layout_better(s, y, x, have, bs, by, bx)) continue;
            tt = (x - geo->ox) * geo->dx + (y - geo->oy) * geo->dy;
            if (sigma * tt < LAYOUT_RES_CLEARANCE) continue;
            if (fabs(layout_dist(x, y, geo->b0x, geo->b0y) - layout_dist(x, y, geo->b1x, geo->b1y)) > LAYOUT_RES_FAIRNESS) continue;
            if (layout_dist(x, y, geo->b0x, geo->b0y) < LAYOUT_SPACING || layout_dist(x, y, geo->b1x, geo->b1y) < LAYOUT_SPACING) continue;
            q_x = x + sigma * LAYOUT_SAT_OFFSET * geo->dx;
            q_y = y + sigma * LAYOUT_SAT_OFFSET * geo->dy;
            if (q_x < 0.0 || q_x >= geo->canvas || q_y < 0.0 || q_y >= geo->canvas) continue;
            if (t->height_at(t->ctx, q_x, q_y) < 0.0 || !t->walkable_at(t->ctx, q_x, q_y)) continue;
            if (fabs(layout_dist(q_x, q_y, geo->b0x, geo->b0y) - layout_dist(q_x, q_y, geo->b1x, geo->b1y)) > LAYOUT_RES_FAIRNESS) continue;
            have = 1;
            bs = s;
            by = y;
            bx = x;
            *px = x;
            *py = y;
            *qx = q_x;
            *qy = q_y;
        }
    }
    return have;
}

/* The age noise at a town in Q16, 0..65536 (step 6); step 7 reads its start axis from the same value. */
static int64_t layout_age_u(uint64_t seed, double x, double y)
{
    return ((int64_t)om_tn_fbm2(seed + LAYOUT_SALT_AGE, layout_noise_q16(x), layout_noise_q16(y),
                                LAYOUT_NOISE_OCTAVES, LAYOUT_NOISE_GAIN) + LAYOUT_Q16_ONE) / 2;
}

/* Step 6: 10 to 40 growth steps from the age noise at the town. */
static int32_t layout_town_age(uint64_t seed, double x, double y)
{
    int64_t u = layout_age_u(seed, x, y);
    return (int32_t)(LAYOUT_AGE_MIN + (LAYOUT_AGE_SPAN * u + LAYOUT_Q16_ONE / 2) / LAYOUT_Q16_ONE);
}

/* Step 8: the richness of a resource site, before the defender slant. */
static int32_t layout_richness(uint64_t seed, double region_economy, double x, double y)
{
    double v = LAYOUT_RICH_BASE + LAYOUT_RICH_SLOPE * region_economy * (LAYOUT_RICH_MID + layout_noise01(seed, LAYOUT_SALT_RICH, x, y));
    v = fmin(1.0, fmax(0.0, v));
    return (int32_t)round((double)LAYOUT_RICH_MAX * v);
}

static void layout_push(om_layout_result *out, double x, double y, int32_t kind, int32_t age, int32_t richness)
{
    om_place *p = &out->places[out->n++];
    p->x = x;
    p->y = y;
    p->kind = kind;
    p->side = -1;
    p->age_steps = age;
    p->richness = richness;
}

/* Steps 3, 4, 6, 8 and 9 (the resource-hosting towns): one town and one resource site each side of the objective.
 * Liberty (spec step 8 says "the resource site nearer that base"): with only one site found there is no "nearer",
 * so the defender slant is applied only when both sites exist and their distances to the HOME base differ. */
static void layout_resource_towns(const layout_work *g, uint64_t seed, double canvas, double region_economy, double objective_x,
                                  double objective_y, const double *base_xy, const int32_t *base_kind, const om_layout_terrain *t,
                                  om_layout_result *out)
{
    layout_geom geo;
    const double *enemy_xy = base_xy + 2;
    double bx = enemy_xy[0] - base_xy[0], by = enemy_xy[1] - base_xy[1];
    double len = sqrt(bx * bx + by * by);
    double px[2], py[2], qx[2], qy[2];
    int32_t rich[2];
    int found[2] = {0, 0}, k;
    if (len >= 1.0) {
        geo.canvas = canvas;
        geo.b0x = base_xy[0];
        geo.b0y = base_xy[1];
        geo.b1x = enemy_xy[0];
        geo.b1y = enemy_xy[1];
        geo.ox = objective_x;
        geo.oy = objective_y;
        geo.dx = -by / len;
        geo.dy = bx / len;
        for (k = 0; k < 2; k++) {
            double sigma = k == 0 ? -1.0 : 1.0;
            found[k] = layout_resource_town(g, t, &geo, sigma, &px[k], &py[k], &qx[k], &qy[k]);
        }
    }
    for (k = 0; k < 2; k++) rich[k] = found[k] ? layout_richness(seed, region_economy, qx[k], qy[k]) : 0;
    if (found[0] && found[1] && (base_kind[0] == OM_PLACE_BASE_HOME || base_kind[1] == OM_PLACE_BASE_HOME)) {
        int home = base_kind[0] == OM_PLACE_BASE_HOME ? 0 : 1;
        double d0 = layout_dist(qx[0], qy[0], base_xy[2 * home], base_xy[2 * home + 1]);
        double d1 = layout_dist(qx[1], qy[1], base_xy[2 * home], base_xy[2 * home + 1]);
        int near = d0 < d1 ? 0 : d1 < d0 ? 1 : -1;
        if (near >= 0) rich[near] = rich[near] + LAYOUT_DEFENDER_SLANT < LAYOUT_RICH_MAX ? rich[near] + LAYOUT_DEFENDER_SLANT : LAYOUT_RICH_MAX;
    }
    for (k = 0; k < 2; k++) {
        if (!found[k]) continue;
        layout_push(out, px[k], py[k], OM_PLACE_NEUTRAL_SETTLEMENT, layout_town_age(seed, px[k], py[k]), 0);
        layout_push(out, qx[k], qy[k], OM_PLACE_RESOURCE_SITE, 0, rich[k]);
    }
}

/* Step 5: the next town, the valid candidate with the greatest score above the floor that is at least 4000 wu from every
 * base, the objective and every place already in the first n_far entries of far[] (bases, objective, towns chosen).
 * Returns 1 and fills x and y, else 0. */
static int layout_next_town(const layout_work *g, const double *far, int n_far, double *tx, double *ty)
{
    int a, b, k, have = 0;
    double bs = 0.0, by = 0.0, bx = 0.0;
    for (b = 0; b < g->m; b++) {
        for (a = 0; a < g->m; a++) {
            double x, y, s;
            if (!g->ok[b * g->m + a]) continue;
            s = g->s[b * g->m + a];
            if (!(s > LAYOUT_FLOOR)) continue;
            x = layout_cell_centre(LAYOUT_GRID_STEP * a + 1);
            y = layout_cell_centre(LAYOUT_GRID_STEP * b + 1);
            if (!layout_better(s, y, x, have, bs, by, bx)) continue;
            for (k = 0; k < n_far; k++) {
                if (layout_dist(x, y, far[2 * k], far[2 * k + 1]) < LAYOUT_SPACING) break;
            }
            if (k < n_far) continue;
            have = 1;
            bs = s;
            by = y;
            bx = x;
            *tx = x;
            *ty = y;
        }
    }
    return have;
}

/* Step 7: the satellite of the town (x, y): 300 wu on the first of E, S, W, N (S is +y) from the age-noise start axis
 * that is inside the canvas on walkable dry ground. Returns 1 and fills sx and sy, else 0. */
static int layout_satellite(uint64_t seed, double canvas, const om_layout_terrain *t, double x, double y, double *sx, double *sy)
{
    static const int axis_x[LAYOUT_SAT_AXES] = { 1, 0, -1, 0 };
    static const int axis_y[LAYOUT_SAT_AXES] = { 0, 1, 0, -1 };
    int start = (int)((layout_age_u(seed, x, y) >> LAYOUT_SAT_SHIFT) & (LAYOUT_SAT_AXES - 1)), k;
    for (k = 0; k < LAYOUT_SAT_AXES; k++) {
        int ax = (start + k) & (LAYOUT_SAT_AXES - 1);
        double qx = x + LAYOUT_SAT_OFFSET * axis_x[ax], qy = y + LAYOUT_SAT_OFFSET * axis_y[ax];
        if (qx < 0.0 || qx >= canvas || qy < 0.0 || qy >= canvas) continue;
        if (t->height_at(t->ctx, qx, qy) < 0.0 || !t->walkable_at(t->ctx, qx, qy)) continue;
        *sx = qx;
        *sy = qy;
        return 1;
    }
    return 0;
}

/* Steps 5, 6, 7 and 9 for the towns that host no resource site: they follow the resource towns in the order chosen,
 * then their satellites in the same order. Each pending satellite reserves a place (n + 2 <= OM_PLACE_CAP). */
static void layout_other_towns(const layout_work *g, uint64_t seed, double canvas, const double *base_xy,
                               const int32_t *base_kind, const om_layout_terrain *t, double objective_x, double objective_y,
                               om_layout_result *out)
{
    double far[2 * OM_PLACE_CAP];
    double tx[OM_PLACE_CAP], ty[OM_PLACE_CAP];
    int n_far = 0, n_town = 0, settlements = 0, k;
    for (k = 0; k < 2; k++) settlements += base_kind[k] == OM_PLACE_BASE_HOME;
    far[2 * n_far] = objective_x;
    far[2 * n_far++ + 1] = objective_y;
    for (k = 0; k < 2; k++) {
        far[2 * n_far] = base_xy[2 * k];
        far[2 * n_far++ + 1] = base_xy[2 * k + 1];
    }
    for (k = 0; k < out->n; k++) {
        if (out->places[k].kind != OM_PLACE_NEUTRAL_SETTLEMENT) continue;
        far[2 * n_far] = out->places[k].x;
        far[2 * n_far++ + 1] = out->places[k].y;
        settlements++;
    }
    while (settlements < LAYOUT_TOWNS_MAX && out->n + n_town + 2 <= OM_PLACE_CAP) {
        double x, y;
        if (!layout_next_town(g, far, n_far, &x, &y)) break;
        far[2 * n_far] = x;
        far[2 * n_far++ + 1] = y;
        tx[n_town] = x;
        ty[n_town++] = y;
        settlements++;
        layout_push(out, x, y, OM_PLACE_NEUTRAL_SETTLEMENT, layout_town_age(seed, x, y), 0);
    }
    for (k = 0; k < n_town && out->n < OM_PLACE_CAP; k++) {
        double sx, sy;
        if (layout_satellite(seed, canvas, t, tx[k], ty[k], &sx, &sy)) layout_push(out, sx, sy, OM_PLACE_EXPANSION_SITE, 0, 0);
    }
}

int om_layout_places(uint64_t seed, double canvas_w, double canvas_h, int32_t archetype, double region_economy,
                     double objective_x, double objective_y, const double *base_xy, const int32_t *base_side,
                     const om_layout_terrain *t, om_layout_result *out)
{
    om_place obj;
    layout_work g;
    const double *enemy_xy;
    if (!base_xy || !base_side || !t || !out) return -1;
    if (!layout_canvas_ok(canvas_w, canvas_h) || archetype < 0 || archetype >= LAYOUT_ARCHETYPES) return -1;

    enemy_xy = base_xy + 2;
    memset(out, 0, sizeof *out);
    memset(&obj, 0, sizeof obj);
    obj.x = objective_x;
    obj.y = objective_y;
    obj.kind = OM_PLACE_OBJECTIVE;
    obj.side = -1;
    out->places[out->n++] = obj;
    out->places[out->n++] = layout_base(base_xy[0], base_xy[1], layout_base_kind[archetype][0], base_side[0]);
    out->places[out->n++] = layout_base(enemy_xy[0], enemy_xy[1], layout_base_kind[archetype][1], base_side[1]);
    if (layout_work_fill(&g, seed, canvas_w, t) != 0) return -1;
    layout_resource_towns(&g, seed, canvas_w, region_economy, objective_x, objective_y, base_xy,
                          layout_base_kind[archetype], t, out);
    layout_other_towns(&g, seed, canvas_w, base_xy, layout_base_kind[archetype], t, objective_x, objective_y, out);
    layout_work_free(&g);
    return out->n;
}
