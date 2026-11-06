/* Layout kit driver (S-247, E-17 S-112): the splitmix64 streams, the district grid, the candidates and sides modes,
 * om_lk_generate, the name tables and the drafts accessors. The pieces are in layout_kit_pieces.c, the route graph and
 * the checks in layout_kit_graph.c, every figure in layout_drafts.h. Port of the reference algorithm
 * scenes/mockups/layout/layout_gen.gd (branch push/proto-layout, reference only); the old library is never read.
 * Determinism: own streams, no world, no clock; angles from the Q16 tables of terrain_noise.c; only sqrt fabs fmin fmax.
 * See also: csrc/layout_kit.h (the contract), docs/northstar/plans/cascades/layout-kit-assault/spec.md. */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include "layout_kit.h"
#include "layout_drafts.h"

int32_t om_tn_sin_q16(uint32_t turn_q16);
int32_t om_tn_cos_q16(uint32_t turn_q16);

/* ---- the streams ---- */
static uint64_t lk_mix(uint64_t z) {
    z = (z ^ (z >> LK_RNG_SHIFT1)) * LK_RNG_MIX1;
    z = (z ^ (z >> LK_RNG_SHIFT2)) * LK_RNG_MIX2;
    return z ^ (z >> LK_RNG_SHIFT3);
}

/* one stream per (candidate, concern), derived from the seed by mixing */
void lk_rng_seed(lk_rng *r, uint64_t seed, int32_t cand, int32_t concern) {
    uint64_t base = lk_mix(seed + LK_RNG_GOLDEN * (uint64_t)(cand + 1));
    r->s = lk_mix(base ^ (LK_RNG_GOLDEN * (uint64_t)(concern + 1)));
}

uint64_t lk_rng_next(lk_rng *r) {
    r->s += LK_RNG_GOLDEN;
    return lk_mix(r->s);
}

double lk_rng_unit(lk_rng *r) {
    uint64_t v = lk_rng_next(r);
    return (double)(v >> LK_RNG_OUT_SHIFT) * LK_RNG_SCALE;
}

double lk_rng_range(lk_rng *r, double lo, double hi) {
    double u = lk_rng_unit(r);
    return lo + (hi - lo) * u;
}

int32_t lk_rng_int(lk_rng *r, int32_t lo, int32_t hi) {
    double u = lk_rng_unit(r);
    int32_t v = lo + (int32_t)floor(u * (double)(hi - lo + 1));
    return v > hi ? hi : v;
}

double lk_rng_sign(lk_rng *r) {
    double u = lk_rng_unit(r);
    return u < 1.0 / 2.0 ? -1.0 : 1.0;
}

/* ---- the frame ---- */
void lk_pt(const lk_frame *f, double u, double v, double *x, double *y) {
    u *= f->s;
    v *= f->s;
    *x = f->cx + u * f->ux - v * f->uy;
    *y = f->cy + u * f->uy + v * f->ux;
}

static void lk_zero(void *p, size_t n) {
    unsigned char *b = (unsigned char *)p;
    size_t i;
    for (i = 0; i < n; i++) b[i] = 0;
}

/* ---- the ground of each side ---- */
static void draw_ground(lk_rng *r, double su, lk_ground *g) {
    static const int32_t forms[] = { OM_LK_LF_BASIN, OM_LK_LF_PLATEAU, OM_LK_LF_BEND };
    double jb, bv, jg, gv, jeu, jev, es;
    int32_t form;
    jb = lk_rng_unit(r);
    bv = lk_rng_range(r, -DRAFT_BASE_V, DRAFT_BASE_V);
    jg = lk_rng_unit(r);
    gv = lk_rng_range(r, -DRAFT_GATE_V, DRAFT_GATE_V);
    jeu = lk_rng_unit(r);
    jev = lk_rng_unit(r);
    es = lk_rng_sign(r);
    form = lk_rng_int(r, 0, (int32_t)(sizeof forms / sizeof forms[0]) - 1);
    g->bu = su * (DRAFT_BASE_U + jb * DRAFT_BASE_U_JIT);
    g->bv = bv;
    g->gu = su * (DRAFT_GATE_U + jg * DRAFT_GATE_U_JIT);
    g->gv = gv;
    g->eu = g->gu + su * (DRAFT_EXP_DU + jeu * DRAFT_EXP_DU_JIT);
    g->ev = g->gv + es * (DRAFT_EXP_DV + jev * DRAFT_EXP_DV_JIT);
    g->landform = forms[form];
}

/* side B from side A: mirror reflects across the map's mid line (u to -u), rotate turns half a turn about the centre */
static void copy_ground(const lk_ground *a, int32_t mode, lk_ground *b) {
    double sv = mode == OM_LK_SIDES_ROTATE ? -1.0 : 1.0;
    b->bu = -a->bu; b->bv = sv * a->bv;
    b->gu = -a->gu; b->gv = sv * a->gv;
    b->eu = -a->eu; b->ev = sv * a->ev;
    b->landform = a->landform;
}

/* ---- the district grid: anchors claim a cell each, the rest go to the nearest weighted anchor ---- */
static void fill_districts(lk_ctx *c) {
    om_lk_layout *l = c->l;
    static const int32_t roles[] = { OM_LK_DIST_OBJECTIVE, OM_LK_DIST_HOME_A, OM_LK_DIST_HOME_B, OM_LK_DIST_NEAR_A,
                                     OM_LK_DIST_NEAR_B, OM_LK_DIST_CONTESTED };
    enum { R_OBJ = 0, R_HA, R_HB, R_NA, R_NB, R_CON, R_COUNT };
    double ax[R_COUNT], ay[R_COUNT], w[R_COUNT], cell = l->canvas / (double)OM_LK_GRID;
    int32_t i, r, k, best;
    ax[R_OBJ] = l->nodes[c->n_o].x; ay[R_OBJ] = l->nodes[c->n_o].y;
    ax[R_HA] = l->nodes[c->n_a].x; ay[R_HA] = l->nodes[c->n_a].y;
    ax[R_HB] = l->nodes[c->n_b].x; ay[R_HB] = l->nodes[c->n_b].y;
    ax[R_CON] = l->nodes[c->n_m].x; ay[R_CON] = l->nodes[c->n_m].y;
    ax[R_NA] = ax[R_NB] = ay[R_NA] = ay[R_NB] = 0.0;
    for (i = 0; i < l->n_places; i++) {
        if (l->places[i].kind != OM_LK_PLACE_EXPANSION) continue;
        k = l->places[i].side ? R_NB : R_NA;
        ax[k] = l->places[i].x; ay[k] = l->places[i].y;
    }
    for (i = 0; i < R_COUNT; i++) w[i] = 1.0;
    if (c->pattern == 1) w[R_CON] = DRAFT_PATTERN_WIDE;                     /* ring: the contested band widens */
    if (c->pattern == 2) { w[R_NA] = DRAFT_PATTERN_WIDE; w[R_NB] = DRAFT_PATTERN_WIDE; }   /* two patches: the near lands */
    for (k = 0; k < R_COUNT; k++) {
        double bd = DRAFT_INF;
        best = -1;
        for (i = 0; i < OM_LK_GRID * OM_LK_GRID; i++) {
            double cx = ((double)(i % OM_LK_GRID) + 1.0 / 2.0) * cell, cy = ((double)(i / OM_LK_GRID) + 1.0 / 2.0) * cell;
            double d = (cx - ax[k]) * (cx - ax[k]) + (cy - ay[k]) * (cy - ay[k]);
            if (l->district[i / OM_LK_GRID][i % OM_LK_GRID] == OM_LK_DIST_NONE && d < bd) { bd = d; best = i; }
        }
        if (best >= 0) l->district[best / OM_LK_GRID][best % OM_LK_GRID] = (int8_t)roles[k];
    }
    for (i = 0; i < OM_LK_GRID * OM_LK_GRID; i++) {
        double cx = ((double)(i % OM_LK_GRID) + 1.0 / 2.0) * cell, cy = ((double)(i / OM_LK_GRID) + 1.0 / 2.0) * cell, bd = DRAFT_INF;
        if (l->district[i / OM_LK_GRID][i % OM_LK_GRID] != OM_LK_DIST_NONE) continue;
        best = 0;
        for (k = 0; k < R_COUNT; k++) {
            double d = ((cx - ax[k]) * (cx - ax[k]) + (cy - ay[k]) * (cy - ay[k])) / (w[k] * w[k]);
            if (d < bd) { bd = d; best = k; }
        }
        r = best;
        l->district[i / OM_LK_GRID][i % OM_LK_GRID] = (int8_t)roles[r];
    }
}

/* side B's road lane tuned by bisection so the fair point is the same route distance from both bases */
static void tune_meander(lk_ctx *c) {
    om_lk_layout *l = c->l;
    double da[OM_LK_MAX_NODES], db[OM_LK_MAX_NODES], lo = DRAFT_MEANDER_MIN, hi = DRAFT_MEANDER_MAX;
    int32_t i;
    if (c->mb_sign == 0.0) c->mb_sign = 1.0;
    for (i = 0; i < DRAFT_MEANDER_STEPS; i++) {
        double mid = (lo + hi) / 2.0;
        lk_set_bulge(l, c->lane_mb, mid, c->mb_sign);
        lk_dijkstra(l, c->n_a, -1, da);
        lk_dijkstra(l, c->n_b, -1, db);
        if (db[c->n_m] > da[c->n_m]) hi = mid; else lo = mid;
    }
    lk_set_bulge(l, c->lane_mb, (lo + hi) / 2.0, c->mb_sign);
}

/* one candidate; 0 when built whole, -1 when a cap was exceeded */
static int32_t build(om_lk_layout *l, uint64_t seed, int32_t cand, double canvas, int32_t mode) {
    lk_ctx c;
    double meander = DRAFT_MEANDER_MIN;
    int32_t i, k, kk;
    uint32_t turn;
    lk_zero(l, sizeof *l);
    lk_zero(&c, sizeof c);
    l->seed = seed;
    l->archetype = OM_LK_ARCH_ASSAULT;
    l->sides_mode = mode;
    l->canvas = canvas;
    l->candidate = cand;
    c.l = l;
    c.mode = mode;
    for (i = 0; i < LK_S_COUNT; i++) lk_rng_seed(&c.st[i], seed, cand, i);

    c.pattern = lk_rng_int(&c.st[LK_S_DISTRICT], 0, DRAFT_PATTERN_COUNT - 1);
    if (mode == OM_LK_SIDES_MIRROR) {
        kk = lk_rng_int(&c.st[LK_S_DISTRICT], 0, DRAFT_AXIS_STEPS / DRAFT_MIRROR_AXIS_STEP - 1);
        k = kk * DRAFT_MIRROR_AXIS_STEP;
    } else {
        k = lk_rng_int(&c.st[LK_S_DISTRICT], 0, DRAFT_AXIS_STEPS - 1);
    }
    turn = (uint32_t)((k * DRAFT_TURN_Q16) / DRAFT_AXIS_STEPS);
    c.f.cx = canvas / 2.0;
    c.f.cy = canvas / 2.0;
    c.f.s = canvas / (double)DRAFT_CANVAS_ASSAULT;
    c.f.ux = (double)om_tn_cos_q16(turn) / (double)DRAFT_TURN_Q16;
    c.f.uy = (double)om_tn_sin_q16(turn) / (double)DRAFT_TURN_Q16;

    draw_ground(&c.st[LK_S_SIDE_A], -1.0, &c.ga);
    if (mode == OM_LK_SIDES_SEPARATE) {
        draw_ground(&c.st[LK_S_SIDE_B], 1.0, &c.gb);
        meander = lk_rng_range(&c.st[LK_S_MEANDER], DRAFT_MEANDER_MIN, DRAFT_MEANDER_MAX);
    } else {
        copy_ground(&c.ga, mode, &c.gb);
    }
    c.m_pref = meander;

    if (lk_piece_home_ground(&c, 0) || lk_piece_home_ground(&c, 1)) return -1;
    if (lk_piece_objective_ground(&c)) return -1;
    if (lk_piece_crossing(&c)) return -1;
    if (lk_piece_prize(&c, meander)) return -1;
    if (lk_piece_heights(&c)) return -1;
    if (mode == OM_LK_SIDES_SEPARATE) tune_meander(&c);
    if (lk_build_requests(&c)) return -1;
    fill_districts(&c);
    om_lk_run_checks(l);
    return 0;
}

int om_lk_generate(uint64_t seed, int32_t archetype, double canvas, int32_t sides_mode, om_lk_layout *out) {
    om_lk_layout cur, best;
    int32_t cand, best_passes = -1;
    if (!out) return LK_RC_NULL_OUT;
    if (archetype != OM_LK_ARCH_ASSAULT) return LK_RC_ARCH;          /* outside 0..9, or a kind not built yet */
    if (!(canvas >= DRAFT_CANVAS_MIN && canvas <= DRAFT_CANVAS_MAX) || sides_mode < 0 || sides_mode > OM_LK_SIDES_SEPARATE)
        return LK_RC_RANGE;
    lk_zero(out, sizeof *out);
    lk_zero(&best, sizeof best);
    for (cand = 0; cand < DRAFT_CANDIDATES; cand++) {
        int32_t passes;
        if (build(&cur, seed, cand, canvas, sides_mode)) continue;      /* over a cap: discarded */
        passes = lk_checks_passed(cur.checks);
        if (passes > best_passes) { best_passes = passes; best = cur; }
        if (cur.checks == OM_LK_CHECKS_ALL) break;                       /* nothing can beat it */
    }
    if (best_passes < 0) return LK_RC_NULL_OUT;     /* no candidate fits the caps */
    *out = best;
    return LK_RC_OK;
}

/* ---- names ---- */
const char *om_lk_name(int32_t domain, int32_t id) {
    static const char *const place[] = { "objective", "base_home", "base_forward", "resource", "expansion" };
    static const char *const lane[] = { "route", "way_round", "climb", "hidden", "objective_route" };
    static const char *const form[] = { "none", "coast", "canyon", "mesa", "ridge", "hill", "plateau", "basin", "bend",
                                        "ford", "pass", "gate" };
    static const char *const req[] = { "pad", "choke", "vantage", "route", "landform" };
    static const char *const mode[] = { "keep_open", "keep_closed", "height", "room", "number" };
    static const char *const piece[] = { "none", "home_ground", "gate", "crossing", "heights", "prize", "objective_ground" };
#define LK_PICK(tab) return (id >= 0 && id < (int32_t)(sizeof tab / sizeof tab[0])) ? tab[id] : NULL
    enum { D_PLACE = 0, D_LANE, D_FORM, D_REQ, D_MODE, D_PIECE };
    switch (domain) {
    case D_PLACE: LK_PICK(place);
    case D_LANE: LK_PICK(lane);
    case D_FORM: LK_PICK(form);
    case D_REQ: LK_PICK(req);
    case D_MODE: LK_PICK(mode);
    case D_PIECE: LK_PICK(piece);
    default: return NULL;
    }
#undef LK_PICK
}

/* ---- the drafts table as data ---- */
#define LK_X_NAME(n, v) #n,
#define LK_X_VALUE(n, v) (double)(v),
static const char *const lk_draft_names[] = { LK_DRAFT_TABLE(LK_X_NAME) };
static const double lk_draft_values[] = { LK_DRAFT_TABLE(LK_X_VALUE) };

int32_t om_lk_draft_count(void) { return (int32_t)(sizeof lk_draft_names / sizeof lk_draft_names[0]); }

const char *om_lk_draft_name(int32_t i) {
    return (i >= 0 && i < om_lk_draft_count()) ? lk_draft_names[i] : NULL;
}

double om_lk_draft_value(int32_t i) {
    return (i >= 0 && i < om_lk_draft_count()) ? lk_draft_values[i] : 0.0;
}
