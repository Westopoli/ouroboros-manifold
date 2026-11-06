/* Layout kit: the route graph, shortest paths, the fairness numbers and the six checks (S-247, R-112-05).
 * The graph is rebuilt from lanes alone (node i joined by every lane a/b), so a layout edited after generation is
 * judged on what it now is. Dijkstra is O(n squared) with strict < and lowest-index ties; no sort, no heap.
 * See also: csrc/layout_kit.h (om_lk_run_checks), csrc/layout_drafts.h. */
#include <math.h>
#include <stdint.h>
#include "layout_kit.h"
#include "layout_drafts.h"

double lk_lane_len(const om_lk_layout *l, int32_t lane) {
    const om_lk_lane *a = &l->lanes[lane];
    double sum = 0.0;
    int32_t i;
    for (i = 1; i < a->n_pts && i < OM_LK_LANE_PTS; i++) {
        double dx = a->px[i] - a->px[i - 1], dy = a->py[i] - a->py[i - 1];
        sum += sqrt(dx * dx + dy * dy);
    }
    return sum;
}

/* dist[i] = route distance from src to node i, DRAFT_INF when unreachable; skip_lane (or -1) is left out of the graph */
void lk_dijkstra(const om_lk_layout *l, int32_t src, int32_t skip_lane, double *dist) {
    int32_t done[OM_LK_MAX_NODES];
    double len[OM_LK_MAX_LANES];
    int32_t n = l->n_nodes, nl = l->n_lanes, i, j, k, best;
    if (n > OM_LK_MAX_NODES) n = OM_LK_MAX_NODES;
    if (nl > OM_LK_MAX_LANES) nl = OM_LK_MAX_LANES;
    for (i = 0; i < OM_LK_MAX_NODES; i++) { dist[i] = DRAFT_INF; done[i] = 0; }
    for (k = 0; k < nl; k++) len[k] = lk_lane_len(l, k);
    if (src < 0 || src >= n) return;
    dist[src] = 0.0;
    for (j = 0; j < n; j++) {
        best = -1;
        for (i = 0; i < n; i++)
            if (!done[i] && dist[i] < DRAFT_INF && (best < 0 || dist[i] < dist[best])) best = i;
        if (best < 0) break;
        done[best] = 1;
        for (k = 0; k < nl; k++) {
            int32_t a = l->lanes[k].a, b = l->lanes[k].b, other;
            if (k == skip_lane || a < 0 || a >= n || b < 0 || b >= n) continue;
            if (a == best) other = b;
            else if (b == best) other = a;
            else continue;
            if (!done[other] && dist[best] + len[k] < dist[other]) dist[other] = dist[best] + len[k];
        }
    }
}

int32_t lk_checks_passed(uint32_t checks) {
    int32_t n = 0;
    while (checks) { n += (int32_t)(checks & 1u); checks >>= 1; }
    return n;
}

/* node of the nth place of a kind, or -1 */
static int32_t kind_node(const om_lk_layout *l, int32_t kind, int32_t nth) {
    int32_t i, seen = 0, np = l->n_places > OM_LK_MAX_PLACES ? OM_LK_MAX_PLACES : l->n_places;
    for (i = 0; i < np; i++) {
        if (l->places[i].kind != kind) continue;
        if (seen == nth) return (l->places[i].node >= 0 && l->places[i].node < l->n_nodes) ? l->places[i].node : -1;
        seen++;
    }
    return -1;
}

static double known(double d) { return d < DRAFT_INF ? d : -1.0; }

static int32_t inside(double v, double lo, double hi) { return v >= lo && v <= hi; }

static int32_t check_bounds(const om_lk_layout *l) {
    int32_t i, j, np = l->n_places, nn = l->n_nodes, nl = l->n_lanes, nc = l->n_chokes, nv = l->n_vantages;
    double c = l->canvas;
    if (np > OM_LK_MAX_PLACES || nn > OM_LK_MAX_NODES || nl > OM_LK_MAX_LANES || nc > OM_LK_MAX_CHOKES ||
        nv > OM_LK_MAX_VANTAGES) return 0;
    for (i = 0; i < np; i++) {
        const om_lk_place *p = &l->places[i];
        if (!inside(p->x - p->pad_r, 0.0, c) || !inside(p->x + p->pad_r, 0.0, c) ||
            !inside(p->y - p->pad_r, 0.0, c) || !inside(p->y + p->pad_r, 0.0, c)) return 0;
    }
    for (i = 0; i < nn; i++)
        if (!inside(l->nodes[i].x, 0.0, c) || !inside(l->nodes[i].y, 0.0, c)) return 0;
    for (i = 0; i < nl; i++) {
        if (l->lanes[i].n_pts > OM_LK_LANE_PTS) return 0;
        for (j = 0; j < l->lanes[i].n_pts; j++)
            if (!inside(l->lanes[i].px[j], 0.0, c) || !inside(l->lanes[i].py[j], 0.0, c)) return 0;
    }
    for (i = 0; i < nc; i++)
        if (!inside(l->chokes[i].x, 0.0, c) || !inside(l->chokes[i].y, 0.0, c)) return 0;
    for (i = 0; i < nv; i++) {
        const om_lk_vantage *v = &l->vantages[i];
        if (!inside(v->x - v->radius, 0.0, c) || !inside(v->x + v->radius, 0.0, c) ||
            !inside(v->y - v->radius, 0.0, c) || !inside(v->y + v->radius, 0.0, c)) return 0;
    }
    return 1;
}

void om_lk_run_checks(om_lk_layout *l) {
    double da[OM_LK_MAX_NODES], db[OM_LK_MAX_NODES], dd[OM_LK_MAX_NODES];
    int32_t na, nb, no, res[2], i, k, ok, objective_lanes;
    uint32_t bits = 0;
    if (!l) return;
    if (l->n_nodes < 0 || l->n_nodes > OM_LK_MAX_NODES || l->n_lanes < 0 || l->n_lanes > OM_LK_MAX_LANES ||
        l->n_places < 0 || l->n_places > OM_LK_MAX_PLACES || l->n_chokes < 0 || l->n_chokes > OM_LK_MAX_CHOKES ||
        l->n_vantages < 0 || l->n_vantages > OM_LK_MAX_VANTAGES) {
        l->checks = 0;
        return;
    }
    na = kind_node(l, OM_LK_PLACE_BASE_FORWARD, 0);
    nb = kind_node(l, OM_LK_PLACE_BASE_HOME, 0);
    no = kind_node(l, OM_LK_PLACE_OBJECTIVE, 0);
    res[0] = kind_node(l, OM_LK_PLACE_RESOURCE, 0);
    res[1] = kind_node(l, OM_LK_PLACE_RESOURCE, 1);
    lk_dijkstra(l, na, -1, da);
    lk_dijkstra(l, nb, -1, db);

    l->fairness.dist_a_objective = no >= 0 && na >= 0 ? known(da[no]) : -1.0;
    l->fairness.dist_b_objective = no >= 0 && nb >= 0 ? known(db[no]) : -1.0;
    for (i = 0; i < 2; i++) {
        l->fairness.dist_a_res[i] = res[i] >= 0 && na >= 0 ? known(da[res[i]]) : -1.0;
        l->fairness.dist_b_res[i] = res[i] >= 0 && nb >= 0 ? known(db[res[i]]) : -1.0;
    }
    l->route_count = 0;
    for (k = 0; k < l->n_lanes; k++) {
        int32_t kind = l->lanes[k].kind;
        if (kind == OM_LK_LANE_ROUTE || kind == OM_LK_LANE_WAY_ROUND || kind == OM_LK_LANE_OBJECTIVE_ROUTE) l->route_count++;
    }

    /* 1 connected: every node reachable from side A's base */
    ok = na >= 0 && l->n_nodes > 0;
    for (i = 0; ok && i < l->n_nodes; i++) if (da[i] >= DRAFT_INF) ok = 0;
    if (ok) bits |= OM_LK_CHECK_CONNECTED;

    /* 2 fairness: both resources equal-distance from the two bases (the objective is slanted to the defender) */
    ok = na >= 0 && nb >= 0 && res[0] >= 0 && res[1] >= 0;
    for (i = 0; ok && i < 2; i++) {
        double a = l->fairness.dist_a_res[i], b = l->fairness.dist_b_res[i];
        if (a < 0.0 || b < 0.0 || fabs(a - b) > DRAFT_EQUAL_TOL * fmax(a, b)) ok = 0;
    }
    if (ok) bits |= OM_LK_CHECK_FAIRNESS;

    /* 3 bypass: the shortest path around a choke's lane is at least DRAFT_BYPASS_MIN times the lane */
    ok = 1;
    for (i = 0; ok && i < l->n_chokes; i++) {
        int32_t lane = l->chokes[i].lane;
        if (lane < 0 || lane >= l->n_lanes || l->lanes[lane].a < 0 || l->lanes[lane].a >= l->n_nodes ||
            l->lanes[lane].b < 0 || l->lanes[lane].b >= l->n_nodes) { ok = 0; break; }
        lk_dijkstra(l, l->lanes[lane].a, lane, dd);
        if (dd[l->lanes[lane].b] >= DRAFT_INF || dd[l->lanes[lane].b] < DRAFT_BYPASS_MIN * lk_lane_len(l, lane)) ok = 0;
    }
    if (ok) bits |= OM_LK_CHECK_BYPASS;

    /* 4 approaches: enough lanes reach the objective and no single one of them is the only way in from side A */
    ok = no >= 0 && na >= 0;
    objective_lanes = 0;
    for (k = 0; ok && k < l->n_lanes; k++) {
        if (l->lanes[k].a != no && l->lanes[k].b != no) continue;
        objective_lanes++;
        lk_dijkstra(l, na, k, dd);
        if (dd[no] >= DRAFT_INF) ok = 0;
    }
    if (ok && objective_lanes >= DRAFT_APPROACHES_MIN) bits |= OM_LK_CHECK_APPROACHES;

    /* 5 chokes: every width inside the band */
    ok = 1;
    for (i = 0; i < l->n_chokes; i++)
        if (!(l->chokes[i].width >= DRAFT_CHOKE_W_MIN && l->chokes[i].width <= DRAFT_CHOKE_W_MAX)) ok = 0;
    if (ok) bits |= OM_LK_CHECK_CHOKES;

    /* 6 bounds */
    if (check_bounds(l)) bits |= OM_LK_CHECK_BOUNDS;
    l->checks = bits;
}
