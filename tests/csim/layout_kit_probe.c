/* Parent-owned probe for the S-247 layout kit tests (not a test file; the pytest module builds it with cc).
 * Usage:
 *   layout_kit_probe gen <seed> <archetype-id> <canvas> <sides-mode>
 *   layout_kit_probe null          (om_lk_generate with a NULL out)
 *   layout_kit_probe names         (om_lk_name over every domain and id range, plus one past, plus -1)
 *   layout_kit_probe drafts        (om_lk_draft_count and each name and value)
 * Output is text, one fact per line. Doubles print as integer hundredths (round half up), never %g/%f, so two
 * runs (or an -O0 and an -O2 build) compare as text. Exit 0 for any rc; exit 2 on a usage error.
 * Spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md "Tests". */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "layout_kit.h"

static long long hund(double v) { return (long long)floor(v * 100.0 + 0.5); }

static void kv(const char *k, long long v) { printf("%s %lld\n", k, v); }

static void dump(const om_lk_layout *l) {
    int i, j, r, c;
    printf("seed %llu\n", (unsigned long long)l->seed);
    kv("archetype", l->archetype);
    kv("sides_mode", l->sides_mode);
    kv("canvas", hund(l->canvas));
    kv("candidate", l->candidate);
    kv("n_places", l->n_places);
    kv("n_nodes", l->n_nodes);
    kv("n_lanes", l->n_lanes);
    kv("n_chokes", l->n_chokes);
    kv("n_vantages", l->n_vantages);
    kv("n_requests", l->n_requests);
    for (i = 0; i < l->n_places; i++) {
        const om_lk_place *p = &l->places[i];
        printf("place %d kind=%d side=%d x=%lld y=%lld pad_r=%lld piece=%d node=%d\n", i, p->kind, p->side,
               hund(p->x), hund(p->y), hund(p->pad_r), p->piece, p->node);
    }
    for (i = 0; i < l->n_nodes; i++) {
        const om_lk_node *n = &l->nodes[i];
        printf("node %d x=%lld y=%lld place=%d\n", i, hund(n->x), hund(n->y), n->place);
    }
    for (i = 0; i < l->n_lanes; i++) {
        const om_lk_lane *a = &l->lanes[i];
        printf("lane %d kind=%d a=%d b=%d width=%lld n_pts=%d pts=", i, a->kind, a->a, a->b, hund(a->width), a->n_pts);
        for (j = 0; j < a->n_pts && j < OM_LK_LANE_PTS; j++) printf("%s%lld,%lld", j ? ";" : "", hund(a->px[j]), hund(a->py[j]));
        printf("\n");
    }
    for (i = 0; i < l->n_chokes; i++) {
        const om_lk_choke *k = &l->chokes[i];
        printf("choke %d x=%lld y=%lld width=%lld length=%lld axis_k=%d wall_span=%lld frac=%lld lane=%d landform=%d piece=%d\n",
               i, hund(k->x), hund(k->y), hund(k->width), hund(k->length), k->axis_k, hund(k->wall_span), hund(k->frac),
               k->lane, k->landform, k->piece);
    }
    for (i = 0; i < l->n_vantages; i++) {
        const om_lk_vantage *v = &l->vantages[i];
        printf("vantage %d x=%lld y=%lld radius=%lld height_bands=%d overlooks=%d climb0=%d climb1=%d landform=%d piece=%d\n",
               i, hund(v->x), hund(v->y), hund(v->radius), v->height_bands, v->overlooks, v->climb[0], v->climb[1],
               v->landform, v->piece);
    }
    for (i = 0; i < l->n_requests; i++) {
        const om_lk_request *q = &l->requests[i];
        printf("request %d kind=%d mode=%d piece=%d name=%.*s x=%lld y=%lld r=%lld w=%lld len=%lld span=%lld frac=%lld axis_k=%d height_bands=%lld side=%d landform=%d\n",
               i, q->kind, q->mode, q->piece, OM_LK_NAME_LEN, q->name, hund(q->x), hund(q->y), hund(q->r), hund(q->w),
               hund(q->len), hund(q->span), hund(q->frac), q->axis_k, hund(q->height_bands), q->side, q->landform);
    }
    printf("fair dist_a_objective=%lld dist_b_objective=%lld dist_a_res0=%lld dist_a_res1=%lld dist_b_res0=%lld dist_b_res1=%lld\n",
           hund(l->fairness.dist_a_objective), hund(l->fairness.dist_b_objective), hund(l->fairness.dist_a_res[0]),
           hund(l->fairness.dist_a_res[1]), hund(l->fairness.dist_b_res[0]), hund(l->fairness.dist_b_res[1]));
    kv("route_count", l->route_count);
    for (r = 0; r < OM_LK_GRID; r++) {
        printf("district %d", r);
        for (c = 0; c < OM_LK_GRID; c++) printf(" %d", (int)l->district[r][c]);
        printf("\n");
    }
}

static int cmd_gen(int argc, char **argv) {
    static om_lk_layout l;   /* static: the struct is large; also zero-initialised */
    int rc, k, cnt[OM_LK_PLACE_KIND_COUNT];
    static const char *cn[6] = {"connected", "fairness", "bypass", "approaches", "chokes", "bounds"};
    char key[64];
    if (argc != 6) return 2;
    memset(&l, 0, sizeof l);
    rc = om_lk_generate(strtoull(argv[2], NULL, 10), atoi(argv[3]), strtod(argv[4], NULL), atoi(argv[5]), &l);
    printf("rc %d\n", rc);
    if (rc != 0) return 0;
    kv("checks", (long long)l.checks);
    for (k = 0; k < 6; k++) {
        snprintf(key, sizeof key, "check_%s", cn[k]);
        kv(key, (l.checks >> k) & 1u);
    }
    memset(cnt, 0, sizeof cnt);
    for (k = 0; k < l.n_places; k++)
        if (l.places[k].kind >= 0 && l.places[k].kind < OM_LK_PLACE_KIND_COUNT) cnt[l.places[k].kind]++;
    kv("count_objective", cnt[OM_LK_PLACE_OBJECTIVE]);
    kv("count_base_home", cnt[OM_LK_PLACE_BASE_HOME]);
    kv("count_base_forward", cnt[OM_LK_PLACE_BASE_FORWARD]);
    kv("count_resource", cnt[OM_LK_PLACE_RESOURCE]);
    kv("count_expansion", cnt[OM_LK_PLACE_EXPANSION]);
    kv("count_chokes", l.n_chokes);
    kv("count_vantages", l.n_vantages);
    kv("count_requests", l.n_requests);
    kv("count_lanes", l.n_lanes);
    kv("fair_dist_a_objective", hund(l.fairness.dist_a_objective));
    kv("fair_dist_b_objective", hund(l.fairness.dist_b_objective));
    kv("fair_dist_a_res0", hund(l.fairness.dist_a_res[0]));
    kv("fair_dist_a_res1", hund(l.fairness.dist_a_res[1]));
    kv("fair_dist_b_res0", hund(l.fairness.dist_b_res[0]));
    kv("fair_dist_b_res1", hund(l.fairness.dist_b_res[1]));
    dump(&l);
    return 0;
}

static int cmd_null(void) {
    printf("rc %d\n", om_lk_generate(1, OM_LK_ARCH_ASSAULT, 24000.0, OM_LK_SIDES_SEPARATE, NULL));
    return 0;
}

static int cmd_names(void) {
    static const int32_t count[6] = {OM_LK_PLACE_KIND_COUNT, OM_LK_LANE_KIND_COUNT, OM_LK_LF_COUNT,
                                     OM_LK_REQ_KIND_COUNT, OM_LK_MODE_COUNT, OM_LK_PIECE_COUNT};
    int d, id;
    for (d = 0; d < 6; d++)
        for (id = -1; id <= count[d]; id++) {
            const char *s = om_lk_name(d, id);
            printf("name %d %d %s\n", d, id, s ? s : "NULL");
        }
    return 0;
}

static int cmd_drafts(void) {
    int32_t i, n = om_lk_draft_count();
    printf("draft_count %d\n", (int)n);
    for (i = 0; i < n; i++) {
        const char *s = om_lk_draft_name(i);
        printf("draft %d %s %lld\n", (int)i, s ? s : "NULL", hund(om_lk_draft_value(i)));
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (!strcmp(argv[1], "gen")) return cmd_gen(argc, argv);
    if (!strcmp(argv[1], "null")) return cmd_null();
    if (!strcmp(argv[1], "names")) return cmd_names();
    if (!strcmp(argv[1], "drafts")) return cmd_drafts();
    return 2;
}
