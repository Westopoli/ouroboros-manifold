/* Parent-owned probe for the S-247 layout kit tests (not a test file; the pytest module builds it with cc).
 * Usage:
 *   layout_kit_probe gen <seed> <archetype-id> <canvas> <sides-mode>
 *   layout_kit_probe null [<archetype-id> <canvas> <sides-mode>]
 *                                  (om_lk_generate with a NULL out; defaults are valid Assault arguments)
 *   layout_kit_probe chain <seedA> <seedB> <archetype-id> <canvas> <sides-mode>
 *                                  (one process, one struct filled with 0xA5, seed A then B then A again; prints
 *                                  "run k" and the same text as gen for each, then "tail_clean a b c")
 *   layout_kit_probe names         (om_lk_name over domains -1..6 and ids -1..count, count 0 out of range)
 *   layout_kit_probe drafts        (om_lk_draft_count and each name and value, then "oob" rows: index -1 and count)
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

/* Everything cmd_gen prints after the rc line (the text the tests compare). */
static void emit(const om_lk_layout *l) {
    int k, cnt[OM_LK_PLACE_KIND_COUNT];
    static const char *cn[6] = {"connected", "fairness", "bypass", "approaches", "chokes", "bounds"};
    char key[64];
    kv("checks", (long long)l->checks);
    for (k = 0; k < 6; k++) {
        snprintf(key, sizeof key, "check_%s", cn[k]);
        kv(key, (l->checks >> k) & 1u);
    }
    memset(cnt, 0, sizeof cnt);
    for (k = 0; k < l->n_places; k++)
        if (l->places[k].kind >= 0 && l->places[k].kind < OM_LK_PLACE_KIND_COUNT) cnt[l->places[k].kind]++;
    kv("count_objective", cnt[OM_LK_PLACE_OBJECTIVE]);
    kv("count_base_home", cnt[OM_LK_PLACE_BASE_HOME]);
    kv("count_base_forward", cnt[OM_LK_PLACE_BASE_FORWARD]);
    kv("count_resource", cnt[OM_LK_PLACE_RESOURCE]);
    kv("count_expansion", cnt[OM_LK_PLACE_EXPANSION]);
    kv("count_chokes", l->n_chokes);
    kv("count_vantages", l->n_vantages);
    kv("count_requests", l->n_requests);
    kv("count_lanes", l->n_lanes);
    kv("fair_dist_a_objective", hund(l->fairness.dist_a_objective));
    kv("fair_dist_b_objective", hund(l->fairness.dist_b_objective));
    kv("fair_dist_a_res0", hund(l->fairness.dist_a_res[0]));
    kv("fair_dist_a_res1", hund(l->fairness.dist_a_res[1]));
    kv("fair_dist_b_res0", hund(l->fairness.dist_b_res[0]));
    kv("fair_dist_b_res1", hund(l->fairness.dist_b_res[1]));
    dump(l);
}

/* 1 when every field of every element past the used count is zero (header: "fills *out (zeroed first)").
 * Field by field, never memcmp: padding bytes are not the engine's to zero. */
static int tail_clean(const om_lk_layout *l) {
    int i, j;
    if (l->n_places < 0 || l->n_places > OM_LK_MAX_PLACES || l->n_nodes < 0 || l->n_nodes > OM_LK_MAX_NODES ||
        l->n_lanes < 0 || l->n_lanes > OM_LK_MAX_LANES || l->n_chokes < 0 || l->n_chokes > OM_LK_MAX_CHOKES ||
        l->n_vantages < 0 || l->n_vantages > OM_LK_MAX_VANTAGES || l->n_requests < 0 || l->n_requests > OM_LK_MAX_REQUESTS)
        return 0;   /* a count that was never set is not a layout */
    for (i = l->n_places; i < OM_LK_MAX_PLACES; i++) {
        const om_lk_place *p = &l->places[i];
        if (p->kind || p->side || p->x != 0.0 || p->y != 0.0 || p->pad_r != 0.0 || p->piece || p->node) return 0;
    }
    for (i = l->n_nodes; i < OM_LK_MAX_NODES; i++)
        if (l->nodes[i].x != 0.0 || l->nodes[i].y != 0.0 || l->nodes[i].place) return 0;
    for (i = l->n_lanes; i < OM_LK_MAX_LANES; i++) {
        const om_lk_lane *a = &l->lanes[i];
        if (a->kind || a->a || a->b || a->width != 0.0 || a->n_pts) return 0;
        for (j = 0; j < OM_LK_LANE_PTS; j++) if (a->px[j] != 0.0 || a->py[j] != 0.0) return 0;
    }
    for (i = l->n_chokes; i < OM_LK_MAX_CHOKES; i++) {
        const om_lk_choke *k = &l->chokes[i];
        if (k->x != 0.0 || k->y != 0.0 || k->width != 0.0 || k->length != 0.0 || k->axis_k || k->wall_span != 0.0 ||
            k->frac != 0.0 || k->lane || k->landform || k->piece) return 0;
    }
    for (i = l->n_vantages; i < OM_LK_MAX_VANTAGES; i++) {
        const om_lk_vantage *v = &l->vantages[i];
        if (v->x != 0.0 || v->y != 0.0 || v->radius != 0.0 || v->height_bands || v->overlooks || v->climb[0] ||
            v->climb[1] || v->landform || v->piece) return 0;
    }
    for (i = l->n_requests; i < OM_LK_MAX_REQUESTS; i++) {
        const om_lk_request *q = &l->requests[i];
        if (q->kind || q->mode || q->piece || q->name[0] || q->x != 0.0 || q->y != 0.0 || q->r != 0.0 || q->w != 0.0 ||
            q->len != 0.0 || q->span != 0.0 || q->frac != 0.0 || q->axis_k || q->height_bands != 0.0 || q->side ||
            q->landform) return 0;
    }
    return 1;
}

static int cmd_gen(int argc, char **argv) {
    static om_lk_layout l;   /* static: the struct is large; also zero-initialised */
    int rc;
    if (argc != 6) return 2;
    memset(&l, 0, sizeof l);
    rc = om_lk_generate(strtoull(argv[2], NULL, 10), atoi(argv[3]), strtod(argv[4], NULL), atoi(argv[5]), &l);
    printf("rc %d\n", rc);
    if (rc != 0) return 0;
    emit(&l);
    return 0;
}

/* chain: one struct, filled with 0xA5 once and never cleared again, seed A, seed B, seed A: a missed zeroing or a
 * static kept between calls shows as run 3 differing from run 1 or from gen, or as tail_clean 0. */
static int cmd_chain(int argc, char **argv) {
    static om_lk_layout l;
    uint64_t seed[3];
    int run, rc, clean[3];
    if (argc != 7) return 2;
    seed[0] = seed[2] = strtoull(argv[2], NULL, 10);
    seed[1] = strtoull(argv[3], NULL, 10);
    memset(&l, 0xA5, sizeof l);
    for (run = 0; run < 3; run++) {
        rc = om_lk_generate(seed[run], atoi(argv[4]), strtod(argv[5], NULL), atoi(argv[6]), &l);
        printf("run %d\nrc %d\n", run + 1, rc);
        if (rc == 0) emit(&l);
        clean[run] = tail_clean(&l);
    }
    printf("tail_clean %d %d %d\n", clean[0], clean[1], clean[2]);
    return 0;
}

static int cmd_null(int argc, char **argv) {
    if (argc != 2 && argc != 5) return 2;
    if (argc == 5) printf("rc %d\n", om_lk_generate(1, atoi(argv[2]), strtod(argv[3], NULL), atoi(argv[4]), NULL));
    else printf("rc %d\n", om_lk_generate(1, OM_LK_ARCH_ASSAULT, 24000.0, OM_LK_SIDES_SEPARATE, NULL));
    return 0;
}

static int cmd_names(void) {
    /* index d + 1: domains -1 and 6 are out of range and have no ids, so only -1 and 0 are asked */
    static const int32_t count[8] = {0, OM_LK_PLACE_KIND_COUNT, OM_LK_LANE_KIND_COUNT, OM_LK_LF_COUNT,
                                     OM_LK_REQ_KIND_COUNT, OM_LK_MODE_COUNT, OM_LK_PIECE_COUNT, 0};
    int d, id;
    for (d = -1; d <= 6; d++)
        for (id = -1; id <= count[d + 1]; id++) {
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
    /* header: draft accessors return NULL / 0.0 out of range */
    for (i = -1; i <= n; i += n + 1) {
        const char *s = om_lk_draft_name(i);
        printf("oob %d %s %lld\n", (int)i, s ? s : "NULL", hund(om_lk_draft_value(i)));
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    if (!strcmp(argv[1], "gen")) return cmd_gen(argc, argv);
    if (!strcmp(argv[1], "null")) return cmd_null(argc, argv);
    if (!strcmp(argv[1], "chain")) return cmd_chain(argc, argv);
    if (!strcmp(argv[1], "names")) return cmd_names();
    if (!strcmp(argv[1], "drafts")) return cmd_drafts();
    return 2;
}
