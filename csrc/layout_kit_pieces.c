/* Layout kit: the six pieces of round A and the request list (S-247, R-112-03, R-113-01..04).
 * home ground, gate (the gate nodes of home ground), crossing, heights, prize, objective ground.
 * Each piece is one choice with numbers; it adds places, nodes and lanes to the candidate under construction.
 * Draws never sit inside argument lists (evaluation order is unspecified): each is assigned to a local first.
 * See also: csrc/layout_drafts.h (every figure), csrc/layout_kit_graph.c (lengths), csrc/layout_kit.c (driver). */
#include <math.h>
#include <stdint.h>
#include "layout_kit.h"
#include "layout_drafts.h"

/* defined in csrc/terrain_noise.c (declared in om_internal.h, which the kit does not include) */
int32_t om_tn_sin_q16(uint32_t turn_q16);
int32_t om_tn_cos_q16(uint32_t turn_q16);

int32_t lk_add_node(om_lk_layout *l, double x, double y, int32_t place) {
    int32_t i = l->n_nodes;
    if (i >= OM_LK_MAX_NODES) return -1;
    l->nodes[i].x = x;
    l->nodes[i].y = y;
    l->nodes[i].place = place;
    l->n_nodes++;
    return i;
}

/* a place and its node; returns the place index */
int32_t lk_add_place(om_lk_layout *l, int32_t kind, int32_t side, double x, double y, double pad_r, int32_t piece) {
    int32_t i = l->n_places, node;
    if (i >= OM_LK_MAX_PLACES) return -1;
    node = lk_add_node(l, x, y, i);
    if (node < 0) return -1;
    l->places[i].kind = kind;
    l->places[i].side = side;
    l->places[i].x = x;
    l->places[i].y = y;
    l->places[i].pad_r = pad_r;
    l->places[i].piece = piece;
    l->places[i].node = node;
    l->n_places++;
    return i;
}

/* a straight lane between two nodes */
int32_t lk_add_lane(om_lk_layout *l, int32_t kind, int32_t a, int32_t b, double width) {
    int32_t i = l->n_lanes;
    if (i >= OM_LK_MAX_LANES) return -1;
    l->lanes[i].kind = kind;
    l->lanes[i].a = a;
    l->lanes[i].b = b;
    l->lanes[i].width = width;
    l->lanes[i].n_pts = 2;
    l->lanes[i].px[0] = l->nodes[a].x;
    l->lanes[i].py[0] = l->nodes[a].y;
    l->lanes[i].px[1] = l->nodes[b].x;
    l->lanes[i].py[1] = l->nodes[b].y;
    l->n_lanes++;
    return i;
}

static void lay_bulge(om_lk_lane *a, double x0, double y0, double x1, double y1, double nx, double ny, double h) {
    int32_t i;
    a->n_pts = DRAFT_BULGE_PTS;
    for (i = 0; i < DRAFT_BULGE_PTS; i++) {
        double t = (double)i / (double)(DRAFT_BULGE_PTS - 1);
        double w = 1.0 - (2.0 * t - 1.0) * (2.0 * t - 1.0);
        a->px[i] = x0 + t * (x1 - x0) + h * w * nx;
        a->py[i] = y0 + t * (y1 - y0) + h * w * ny;
    }
}

/* Re-lays a lane as a parabolic bulge whose polyline is `ratio` times its chord (1.0 or less: straight). `sign`
 * picks the side (+1: left of the a-to-b direction). The height is found by bisection, so the ratio is exact. */
void lk_set_bulge(om_lk_layout *l, int32_t lane, double ratio, double sign) {
    om_lk_lane *a = &l->lanes[lane];
    double x0 = l->nodes[a->a].x, y0 = l->nodes[a->a].y, x1 = l->nodes[a->b].x, y1 = l->nodes[a->b].y;
    double dx = x1 - x0, dy = y1 - y0, chord = sqrt(dx * dx + dy * dy), nx, ny, lo = 0.0, hi;
    int32_t i;
    a->n_pts = 2;
    a->px[0] = x0; a->py[0] = y0; a->px[1] = x1; a->py[1] = y1;
    if (ratio <= 1.0 + DRAFT_EPS || chord < DRAFT_EPS) return;
    nx = -dy / chord * sign;
    ny = dx / chord * sign;
    hi = chord / 2.0 * sqrt(ratio * ratio - 1.0);   /* the triangle's height: the parabola needs no more */
    for (i = 0; i < DRAFT_SOLVE_STEPS; i++) {
        double mid = (lo + hi) / 2.0;
        lay_bulge(a, x0, y0, x1, y1, nx, ny, mid);
        if (lk_lane_len(l, lane) < ratio * chord) lo = mid; else hi = mid;
    }
    lay_bulge(a, x0, y0, x1, y1, nx, ny, (lo + hi) / 2.0);
}

static double dist2(double ax, double ay, double bx, double by) {
    return sqrt((ax - bx) * (ax - bx) + (ay - by) * (ay - by));
}

/* ---- home ground: a base, its gate node, one expansion site (side 0 = A's forward camp, 1 = B's grown town) ---- */
int32_t lk_piece_home_ground(lk_ctx *c, int32_t side) {
    om_lk_layout *l = c->l;
    const lk_ground *g = side ? &c->gb : &c->ga;
    double bx, by, gx, gy, ex, ey;
    int32_t base, gate, exp_site, lane;
    lk_pt(&c->f, g->bu, g->bv, &bx, &by);
    lk_pt(&c->f, g->gu, g->gv, &gx, &gy);
    lk_pt(&c->f, g->eu, g->ev, &ex, &ey);
    base = lk_add_place(l, side ? OM_LK_PLACE_BASE_HOME : OM_LK_PLACE_BASE_FORWARD, side, bx, by,
                        (side ? DRAFT_PAD_BASE_B : DRAFT_PAD_BASE_A) * c->f.s, OM_LK_PIECE_HOME_GROUND);
    if (base < 0) return -1;
    gate = lk_add_node(l, gx, gy, -1);
    if (gate < 0) return -1;
    exp_site = lk_add_place(l, OM_LK_PLACE_EXPANSION, side, ex, ey, DRAFT_PAD_EXP * c->f.s, OM_LK_PIECE_HOME_GROUND);
    if (exp_site < 0) return -1;
    lane = lk_add_lane(l, OM_LK_LANE_ROUTE, l->places[base].node, gate, DRAFT_LANE_W_ROUTE);
    if (lane < 0) return -1;
    lane = lk_add_lane(l, OM_LK_LANE_ROUTE, gate, l->places[exp_site].node, DRAFT_LANE_W_ROUTE);
    if (lane < 0) return -1;
    if (side) { c->n_b = l->places[base].node; c->n_gb = gate; } else { c->n_a = l->places[base].node; c->n_ga = gate; }
    return 0;
}

/* ---- objective ground: beside the defender's base (Q-191-11), two approach lanes ---- */
int32_t lk_piece_objective_ground(lk_ctx *c) {
    om_lk_layout *l = c->l;
    double es = (c->gb.ev - c->gb.gv) >= 0.0 ? 1.0 : -1.0, x, y;
    int32_t obj, lane;
    lk_pt(&c->f, c->gb.bu - DRAFT_OBJ_DU, c->gb.bv - es * DRAFT_OBJ_DV, &x, &y);
    obj = lk_add_place(l, OM_LK_PLACE_OBJECTIVE, -1, x, y, DRAFT_PAD_OBJ * c->f.s, OM_LK_PIECE_OBJECTIVE_GROUND);
    if (obj < 0) return -1;
    c->n_o = l->places[obj].node;
    lane = lk_add_lane(l, OM_LK_LANE_OBJECTIVE_ROUTE, c->n_gb, c->n_o, DRAFT_LANE_W_OBJ);
    if (lane < 0) return -1;
    lane = lk_add_lane(l, OM_LK_LANE_OBJECTIVE_ROUTE, c->n_b, c->n_o, DRAFT_LANE_W_OBJ);
    return lane < 0 ? -1 : 0;
}

/* the gap's axis in 15-degree steps 0..11: the step whose direction lies closest to the lane's line */
static int32_t axis_step(double dx, double dy) {
    double len = sqrt(dx * dx + dy * dy), best = -1.0;
    int32_t k, pick = 0;
    if (len < DRAFT_EPS) return 0;
    for (k = 0; k < DRAFT_AXIS_STEPS / 2; k++) {
        uint32_t turn = (uint32_t)((k * DRAFT_TURN_Q16) / DRAFT_AXIS_STEPS);
        double cs = (double)om_tn_cos_q16(turn) / (double)DRAFT_TURN_Q16, sn = (double)om_tn_sin_q16(turn) / (double)DRAFT_TURN_Q16;
        double score = fabs((dx * cs + dy * sn) / len);
        if (score > best) { best = score; pick = k; }
    }
    return pick;
}

/* ---- crossing: one choke on the spine lane, and the way round (R-113-03) ---- */
int32_t lk_piece_crossing(lk_ctx *c) {
    om_lk_layout *l = c->l;
    lk_rng *r = &c->st[LK_S_PIECES];
    static const int32_t forms[] = { OM_LK_LF_FORD, OM_LK_LF_PASS, OM_LK_LF_GATE, OM_LK_LF_CANYON };
    double ax = l->nodes[c->n_ga].x, ay = l->nodes[c->n_ga].y, bx = l->nodes[c->n_gb].x, by = l->nodes[c->n_gb].y;
    double dx = bx - ax, dy = by - ay, g = sqrt(dx * dx + dy * dy), ex, ey, nx, ny;
    double t, vj, len_u, ratio, frac, width, cs, sn, x1, y1, x2, y2, rx, ry, lane_len;
    int32_t lean, kk, form, j1, j2, lane;
    uint32_t turn;
    if (g < DRAFT_EPS || DRAFT_ASSAULT_CROSSINGS != 1) return -1;     /* one crossing per Assault layout, as built */
    ex = dx / g; ey = dy / g;
    nx = -ey; ny = ex;
    t = lk_rng_range(r, DRAFT_CROSS_T_MIN, DRAFT_CROSS_T_MAX);
    vj = lk_rng_range(r, -DRAFT_CROSS_V, DRAFT_CROSS_V);
    lean = lk_rng_int(r, -DRAFT_CROSS_TURN_MAX, DRAFT_CROSS_TURN_MAX);
    len_u = lk_rng_unit(r);
    ratio = lk_rng_range(r, DRAFT_BYPASS_MIN + DRAFT_WAYROUND_MARGIN, DRAFT_BYPASS_MAX - DRAFT_WAYROUND_MARGIN);
    c->way_sign = lk_rng_sign(r);
    frac = lk_rng_range(r, DRAFT_CHOKE_FRAC_MIN, DRAFT_CHOKE_FRAC_MAX);
    width = lk_rng_range(r, DRAFT_CHOKE_W_MIN, DRAFT_CHOKE_W_MAX);
    form = lk_rng_int(r, 0, (int32_t)(sizeof forms / sizeof forms[0]) - 1);
    lane_len = (DRAFT_CROSS_LEN + len_u * DRAFT_CROSS_LEN_JIT) * c->f.s;
    kk = (lean + DRAFT_AXIS_STEPS) % DRAFT_AXIS_STEPS;
    turn = (uint32_t)((kk * DRAFT_TURN_Q16) / DRAFT_AXIS_STEPS);
    cs = (double)om_tn_cos_q16(turn) / (double)DRAFT_TURN_Q16;
    sn = (double)om_tn_sin_q16(turn) / (double)DRAFT_TURN_Q16;
    x1 = ax + t * dx + nx * vj * c->f.s;
    y1 = ay + t * dy + ny * vj * c->f.s;
    rx = ex * cs - ey * sn;
    ry = ex * sn + ey * cs;
    x2 = x1 + rx * lane_len;
    y2 = y1 + ry * lane_len;
    j1 = lk_add_node(l, x1, y1, -1);
    j2 = lk_add_node(l, x2, y2, -1);
    if (j1 < 0 || j2 < 0) return -1;
    c->n_j1 = j1; c->n_j2 = j2;
    lane = lk_add_lane(l, OM_LK_LANE_ROUTE, c->n_ga, j1, DRAFT_LANE_W_ROUTE);
    if (lane < 0) return -1;
    c->lane_cross = lk_add_lane(l, OM_LK_LANE_ROUTE, j1, j2, DRAFT_LANE_W_ROUTE);
    c->lane_way = lk_add_lane(l, OM_LK_LANE_WAY_ROUND, j1, j2, DRAFT_LANE_W_WAY);
    if (c->lane_cross < 0 || c->lane_way < 0) return -1;
    lk_set_bulge(l, c->lane_way, ratio, c->way_sign);
    if (l->n_chokes >= OM_LK_MAX_CHOKES) return -1;
    {
        om_lk_choke *k = &l->chokes[l->n_chokes++];
        k->x = x1 + frac * (x2 - x1);
        k->y = y1 + frac * (y2 - y1);
        k->width = width;
        k->length = DRAFT_CHOKE_LEN * c->f.s;
        k->axis_k = axis_step(x2 - x1, y2 - y1);
        k->wall_span = DRAFT_WALL_SPAN * c->f.s;
        k->frac = frac;
        k->lane = c->lane_cross;
        k->landform = forms[form];
        k->piece = OM_LK_PIECE_CROSSING;
    }
    return 0;
}

/* ---- prize: two significant resources either side of the road at equal route distance (R-113-02) ----
 * The fair point M lies on the road between the crossing and side B's gate, where the route distances from the two
 * bases are equal when the lane M to the gate is `meander` times its chord. */
int32_t lk_piece_prize(lk_ctx *c, double meander) {
    om_lk_layout *l = c->l;
    double jx = l->nodes[c->n_j2].x, jy = l->nodes[c->n_j2].y, gx = l->nodes[c->n_gb].x, gy = l->nodes[c->n_gb].y;
    double dx = gx - jx, dy = gy - jy, lr = sqrt(dx * dx + dy * dy), nx, ny, f, mx, my;
    double a_link = dist2(l->nodes[c->n_a].x, l->nodes[c->n_a].y, l->nodes[c->n_ga].x, l->nodes[c->n_ga].y);
    double b_link = dist2(l->nodes[c->n_b].x, l->nodes[c->n_b].y, gx, gy);
    double pre = dist2(l->nodes[c->n_ga].x, l->nodes[c->n_ga].y, l->nodes[c->n_j1].x, l->nodes[c->n_j1].y);
    double cross = dist2(l->nodes[c->n_j1].x, l->nodes[c->n_j1].y, jx, jy), spur = DRAFT_PRIZE_SPUR * c->f.s;
    int32_t m, r0, r1, lane;
    if (lr < DRAFT_EPS || DRAFT_ASSAULT_PRIZES != 1) return -1;
    f = (b_link + meander * lr - (a_link + pre + cross)) / ((1.0 + meander) * lr);
    f = fmin(fmax(f, DRAFT_M_FRAC_MIN), DRAFT_M_FRAC_MAX);
    mx = jx + f * dx;
    my = jy + f * dy;
    nx = -dy / lr; ny = dx / lr;
    m = lk_add_node(l, mx, my, -1);
    if (m < 0) return -1;
    c->n_m = m;
    lane = lk_add_lane(l, OM_LK_LANE_ROUTE, c->n_j2, m, DRAFT_LANE_W_ROUTE);
    if (lane < 0) return -1;
    c->lane_mb = lk_add_lane(l, OM_LK_LANE_ROUTE, m, c->n_gb, DRAFT_LANE_W_ROUTE);
    if (c->lane_mb < 0) return -1;
    if (meander > 1.0 + DRAFT_EPS) {
        c->mb_sign = lk_rng_sign(&c->st[LK_S_MEANDER]);
        lk_set_bulge(l, c->lane_mb, meander, c->mb_sign);
    }
    r0 = lk_add_place(l, OM_LK_PLACE_RESOURCE, -1, mx + nx * spur, my + ny * spur, DRAFT_PAD_RES * c->f.s, OM_LK_PIECE_PRIZE);
    r1 = lk_add_place(l, OM_LK_PLACE_RESOURCE, -1, mx - nx * spur, my - ny * spur, DRAFT_PAD_RES * c->f.s, OM_LK_PIECE_PRIZE);
    if (r0 < 0 || r1 < 0) return -1;
    lane = lk_add_lane(l, OM_LK_LANE_ROUTE, m, l->places[r0].node, DRAFT_LANE_W_ROUTE);
    if (lane < 0) return -1;
    lane = lk_add_lane(l, OM_LK_LANE_ROUTE, m, l->places[r1].node, DRAFT_LANE_W_ROUTE);
    return lane < 0 ? -1 : 0;
}

/* ---- heights: a vantage that overlooks the crossing lane, two climb lanes up to it (R-113-04) ---- */
int32_t lk_piece_heights(lk_ctx *c) {
    om_lk_layout *l = c->l;
    lk_rng *r = &c->st[LK_S_PIECES];
    static const int32_t forms[] = { OM_LK_LF_RIDGE, OM_LK_LF_HILL, OM_LK_LF_MESA };
    double x1 = l->nodes[c->n_j1].x, y1 = l->nodes[c->n_j1].y, x2 = l->nodes[c->n_j2].x, y2 = l->nodes[c->n_j2].y;
    double dx = x2 - x1, dy = y2 - y1, len = sqrt(dx * dx + dy * dy), vx, vy;
    int32_t bands, form, v, c0, c1;
    if (len < DRAFT_EPS || DRAFT_ASSAULT_HEIGHTS != 1 || l->n_vantages >= OM_LK_MAX_VANTAGES) return -1;
    bands = lk_rng_int(r, DRAFT_VANTAGE_BANDS_MIN, DRAFT_VANTAGE_BANDS_MAX);
    form = lk_rng_int(r, 0, (int32_t)(sizeof forms / sizeof forms[0]) - 1);
    vx = (x1 + x2) / 2.0 + dy / len * c->way_sign * DRAFT_VANT_OFFSET * c->f.s;   /* off the side the way round is not */
    vy = (y1 + y2) / 2.0 - dx / len * c->way_sign * DRAFT_VANT_OFFSET * c->f.s;
    v = lk_add_node(l, vx, vy, -1);
    if (v < 0) return -1;
    c->n_v = v;
    c0 = lk_add_lane(l, OM_LK_LANE_CLIMB, v, c->n_j1, DRAFT_LANE_W_CLIMB);
    c1 = lk_add_lane(l, OM_LK_LANE_CLIMB, v, c->n_ga, DRAFT_LANE_W_CLIMB);
    if (c0 < 0 || c1 < 0) return -1;
    {
        om_lk_vantage *w = &l->vantages[l->n_vantages++];
        w->x = vx;
        w->y = vy;
        w->radius = DRAFT_VANT_R * c->f.s;
        w->height_bands = bands;
        w->overlooks = c->lane_cross;
        w->climb[0] = c0;
        w->climb[1] = c1;
        w->landform = forms[form];
        w->piece = OM_LK_PIECE_HEIGHTS;
    }
    return 0;
}

/* ---- the request list: what the landscape engine is asked to make real (the B3 seam) ---- */
static om_lk_request *req_new(om_lk_layout *l, int32_t kind, int32_t mode, int32_t piece) {
    om_lk_request *q;
    if (l->n_requests >= OM_LK_MAX_REQUESTS) return 0;
    q = &l->requests[l->n_requests++];
    q->kind = kind;
    q->mode = mode;
    q->piece = piece;
    return q;
}

static void set_name(char *dst, const char *src, int32_t digit) {
    int32_t i = 0;
    while (src[i] && i < OM_LK_NAME_LEN - 2) { dst[i] = src[i]; i++; }
    if (digit >= 0) dst[i++] = (char)('0' + digit);
    dst[i] = 0;
}

int32_t lk_build_requests(lk_ctx *c) {
    om_lk_layout *l = c->l;
    int32_t i, site = 0;
    const om_lk_place *pa = 0, *pb = 0;
    for (i = 0; i < l->n_places; i++) {
        const om_lk_place *p = &l->places[i];
        om_lk_request *q = req_new(l, OM_LK_REQ_PAD, OM_LK_MODE_ROOM, p->piece);
        if (!q) return -1;
        q->x = p->x; q->y = p->y; q->r = p->pad_r;
        if (p->kind == OM_LK_PLACE_BASE_FORWARD) { set_name(q->name, "base_a", -1); pa = p; }
        else if (p->kind == OM_LK_PLACE_BASE_HOME) { set_name(q->name, "base_b", -1); pb = p; }
        else if (p->kind == OM_LK_PLACE_OBJECTIVE) set_name(q->name, "objective", -1);
        else set_name(q->name, "site_", site++);
    }
    if (!pa || !pb) return -1;
    for (i = 0; i < l->n_chokes; i++) {
        const om_lk_choke *k = &l->chokes[i];
        om_lk_request *q = req_new(l, OM_LK_REQ_CHOKE, OM_LK_MODE_KEEP_OPEN, k->piece);
        if (!q) return -1;
        q->x = k->x; q->y = k->y; q->w = k->width; q->len = k->length; q->span = k->wall_span; q->frac = k->frac;
        q->axis_k = k->axis_k; q->landform = k->landform;
    }
    for (i = 0; i < l->n_vantages; i++) {
        const om_lk_vantage *v = &l->vantages[i];
        double da = (v->x - pa->x) * (v->x - pa->x) + (v->y - pa->y) * (v->y - pa->y);
        double db = (v->x - pb->x) * (v->x - pb->x) + (v->y - pb->y) * (v->y - pb->y);
        om_lk_request *q = req_new(l, OM_LK_REQ_VANTAGE, OM_LK_MODE_HEIGHT, v->piece);
        if (!q) return -1;
        q->x = v->x; q->y = v->y; q->r = v->radius; q->height_bands = (double)v->height_bands;
        q->side = da < db ? 1 : (db < da ? -1 : 0);
        q->landform = v->landform;
    }
    for (i = 0; i < l->n_lanes; i++) {
        const om_lk_lane *a = &l->lanes[i];
        om_lk_request *q;
        if (a->kind != OM_LK_LANE_ROUTE && a->kind != OM_LK_LANE_WAY_ROUND && a->kind != OM_LK_LANE_OBJECTIVE_ROUTE) continue;
        q = req_new(l, OM_LK_REQ_ROUTE, OM_LK_MODE_NUMBER, OM_LK_PIECE_NONE);
        if (!q) return -1;
        q->x = (a->px[0] + a->px[a->n_pts - 1]) / 2.0;
        q->y = (a->py[0] + a->py[a->n_pts - 1]) / 2.0;
        q->r = a->width;
    }
    for (i = 0; i < l->n_chokes; i++) {
        om_lk_request *q = req_new(l, OM_LK_REQ_LANDFORM, OM_LK_MODE_KEEP_OPEN, l->chokes[i].piece);
        if (!q) return -1;
        q->x = l->chokes[i].x; q->y = l->chokes[i].y; q->r = l->chokes[i].wall_span; q->landform = l->chokes[i].landform;
    }
    for (i = 0; i < l->n_vantages; i++) {
        om_lk_request *q = req_new(l, OM_LK_REQ_LANDFORM, OM_LK_MODE_KEEP_OPEN, l->vantages[i].piece);
        if (!q) return -1;
        q->x = l->vantages[i].x; q->y = l->vantages[i].y; q->r = l->vantages[i].radius; q->landform = l->vantages[i].landform;
    }
    for (i = 0; i < 2; i++) {
        const om_lk_place *p = i ? pb : pa;
        om_lk_request *q = req_new(l, OM_LK_REQ_LANDFORM, OM_LK_MODE_KEEP_OPEN, OM_LK_PIECE_HOME_GROUND);
        if (!q) return -1;
        q->x = p->x; q->y = p->y; q->r = p->pad_r; q->landform = i ? c->gb.landform : c->ga.landform;
    }
    return 0;
}
