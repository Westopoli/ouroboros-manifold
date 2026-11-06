/* layout_dump: command-line tool over the layout kit (S-247, cascade layout-kit-assault, leaf 2).
 * Prints the JSON "om-layout-1" of spec.md for a seed, applies a deterministic --break edit for the checks' positive
 * controls, or re-judges a file this tool wrote (--check). Numbers print with integer arithmetic only (hundredths).
 * Build: cc -I csrc -o layout_dump csrc/tools/layout_dump.c csrc/layout_kit*.c csrc/terrain_noise.c -lm
 * See also: csrc/layout_kit.h (the contract), csrc/layout_drafts.h (drafts), docs/northstar/plans/cascades/layout-kit-assault/spec.md. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "layout_kit.h"
#include "layout_drafts.h"

#define HUND          100            /* the JSON prints hundredths: DRAFT_JSON_QUANT is 1 / HUND */
#define NUM_CLAMP     9.0e15         /* magnitudes above this clamp before printing (spec "JSON") */
#define NUM_HALF      0.5
#define EXIT_FAIL     1
#define EXIT_USAGE    2
#define CHECK_COUNT   6
#define FILE_MAX      (1 << 20)
#define KEY_MAX       32
#define PATH_MAX_LEN  512
#define DOM_PLACE     0
#define DOM_LANE      1
#define DOM_FORM      2
#define DOM_PIECE     5
#define BREAK_EXTRA_W 100.0          /* --break chokes / bounds overshoot, wu */

static const char *const CHECK_NAMES[CHECK_COUNT] = { "connected", "fairness", "bypass", "approaches", "chokes", "bounds" };
static const char *const SIDES_NAMES[3] = { "mirror", "rotate", "separate" };
/* the other nine archetypes of csrc/mission.c, snake_case: known, not built in round A */
static const char *const OTHER_ARCH[] = { "defensive_stand", "siege_breaking", "reconquest", "suppression",
    "multi_front_defense", "interception", "evacuation", "containment", "counterinsurgency" };

static int usage(const char *msg, const char *arg) {
    fprintf(stderr, "layout_dump: %s%s%s\n", msg, arg ? ": " : "", arg ? arg : "");
    fprintf(stderr, "usage: layout_dump --seed N [--archetype assault] [--canvas W] [--sides mirror|rotate|separate]\n"
                    "                   [--break <check>] [--out file.json]\n"
                    "       layout_dump --seeds A..B --out-dir D [--archetype assault] [--canvas W] [--sides S]\n"
                    "       layout_dump --check file.json\n");
    return EXIT_USAGE;
}

/* ---- numbers ---- */
static void put_q(FILE *f, double v) {
    int64_t h;
    int neg;
    double a;
    if (!(v == v)) v = 0.0;
    if (v > NUM_CLAMP) v = NUM_CLAMP;
    if (v < -NUM_CLAMP) v = -NUM_CLAMP;
    neg = v < 0.0;
    a = neg ? -v : v;
    h = (int64_t)(a * (double)HUND + NUM_HALF);        /* half away from zero (a is not negative) */
    fprintf(f, "%s%lld.%02lld", (neg && h != 0) ? "-" : "", (long long)(h / HUND), (long long)(h % HUND));
}

static void put_pts(FILE *f, const om_lk_lane *a) {
    int32_t i;
    fputc('[', f);
    for (i = 0; i < a->n_pts; i++) {
        fputs(i ? ", [" : "[", f);
        put_q(f, a->px[i]);
        fputs(", ", f);
        put_q(f, a->py[i]);
        fputc(']', f);
    }
    fputc(']', f);
}

static const char *nm(int32_t domain, int32_t id) {
    const char *s = om_lk_name(domain, id);
    return s ? s : "none";
}

/* ---- JSON out ---- */
static void put_xy(FILE *f, const char *k1, double a, const char *k2, double b) {
    fprintf(f, "\"%s\": ", k1);
    put_q(f, a);
    fprintf(f, ", \"%s\": ", k2);
    put_q(f, b);
}

static void put_field(FILE *f, const char *key, double v) {
    fprintf(f, ", \"%s\": ", key);
    put_q(f, v);
}

static void put_dist_list(FILE *f, const char *key, const double *d) {
    fprintf(f, "    \"%s\": [", key);
    put_q(f, d[0]);
    fputs(", ", f);
    put_q(f, d[1]);
    fputc(']', f);
}

static void emit_json(FILE *f, const om_lk_layout *l) {
    int32_t i, j, n = om_lk_draft_count();
    static const char *const side_txt[3] = { "none", "A", "B" };
    fputs("{\n  \"schema\": \"om-layout-1\",\n", f);
    fprintf(f, "  \"seed\": %llu,\n  \"archetype\": \"assault\",\n  \"canvas\": ", (unsigned long long)l->seed);
    put_q(f, l->canvas);
    fprintf(f, ",\n  \"sides\": \"%s\",\n  \"candidate\": %d,\n  \"drafts\": {\n", SIDES_NAMES[l->sides_mode], (int)l->candidate);
    for (i = 0; i < n; i++) {
        fprintf(f, "    \"%s\": ", om_lk_draft_name(i));
        put_q(f, om_lk_draft_value(i));
        fputs(i + 1 < n ? ",\n" : "\n", f);
    }
    fputs("  },\n  \"district\": [\n", f);
    for (i = 0; i < OM_LK_GRID; i++) {
        fputs("    [", f);
        for (j = 0; j < OM_LK_GRID; j++) fprintf(f, "%s%d", j ? ", " : "", (int)l->district[i][j]);
        fputs(i + 1 < OM_LK_GRID ? "],\n" : "]\n", f);
    }
    fputs("  ],\n  \"places\": [\n", f);
    for (i = 0; i < l->n_places; i++) {
        const om_lk_place *p = &l->places[i];
        fprintf(f, "    {\"kind\": \"%s\", \"side\": \"%s\", ", nm(DOM_PLACE, p->kind),
                side_txt[p->side == 0 ? 1 : (p->side == 1 ? 2 : 0)]);
        put_xy(f, "x", p->x, "y", p->y);
        put_field(f, "pad_r", p->pad_r);
        fprintf(f, ", \"piece\": \"%s\", \"node\": %d}%s\n", nm(DOM_PIECE, p->piece), (int)p->node, i + 1 < l->n_places ? "," : "");
    }
    fputs("  ],\n  \"nodes\": [\n", f);
    for (i = 0; i < l->n_nodes; i++) {
        fputs("    {", f);
        put_xy(f, "x", l->nodes[i].x, "y", l->nodes[i].y);
        fprintf(f, ", \"place\": %d}%s\n", (int)l->nodes[i].place, i + 1 < l->n_nodes ? "," : "");
    }
    fputs("  ],\n  \"lanes\": [\n", f);
    for (i = 0; i < l->n_lanes; i++) {
        const om_lk_lane *a = &l->lanes[i];
        fprintf(f, "    {\"kind\": \"%s\", \"a\": %d, \"b\": %d", nm(DOM_LANE, a->kind), (int)a->a, (int)a->b);
        put_field(f, "width", a->width);
        fputs(", \"pts\": ", f);
        put_pts(f, a);
        fputs(i + 1 < l->n_lanes ? "},\n" : "}\n", f);
    }
    fputs("  ],\n  \"chokes\": [\n", f);
    for (i = 0; i < l->n_chokes; i++) {
        const om_lk_choke *c = &l->chokes[i];
        fputs("    {", f);
        put_xy(f, "x", c->x, "y", c->y);
        put_field(f, "width", c->width);
        put_field(f, "length", c->length);
        fprintf(f, ", \"axis_k\": %d", (int)c->axis_k);
        put_field(f, "wall_span", c->wall_span);
        put_field(f, "frac", c->frac);
        fprintf(f, ", \"lane\": %d, \"landform\": \"%s\", \"piece\": \"%s\"}%s\n", (int)c->lane, nm(DOM_FORM, c->landform),
                nm(DOM_PIECE, c->piece), i + 1 < l->n_chokes ? "," : "");
    }
    fputs("  ],\n  \"vantages\": [\n", f);
    for (i = 0; i < l->n_vantages; i++) {
        const om_lk_vantage *v = &l->vantages[i];
        fputs("    {", f);
        put_xy(f, "x", v->x, "y", v->y);
        put_field(f, "radius", v->radius);
        fprintf(f, ", \"height_bands\": %d, \"overlooks\": %d, \"climb\": [%d, %d], \"landform\": \"%s\", \"piece\": \"%s\"}%s\n",
                (int)v->height_bands, (int)v->overlooks, (int)v->climb[0], (int)v->climb[1], nm(DOM_FORM, v->landform),
                nm(DOM_PIECE, v->piece), i + 1 < l->n_vantages ? "," : "");
    }
    fputs("  ],\n  \"requests\": [\n", f);
    for (i = 0; i < l->n_requests; i++) {
        const om_lk_request *q = &l->requests[i];
        fprintf(f, "    {\"kind\": \"%s\", \"mode\": \"%s\", \"piece\": \"%s\", \"name\": \"%s\", ", nm(3, q->kind), nm(4, q->mode),
                nm(DOM_PIECE, q->piece), q->name);
        put_xy(f, "x", q->x, "y", q->y);
        put_field(f, "r", q->r);
        put_field(f, "w", q->w);
        put_field(f, "len", q->len);
        put_field(f, "span", q->span);
        put_field(f, "frac", q->frac);
        fprintf(f, ", \"axis_k\": %d", (int)q->axis_k);
        put_field(f, "height_bands", q->height_bands);
        fprintf(f, ", \"side\": %d, \"landform\": \"%s\"}%s\n", (int)q->side, nm(DOM_FORM, q->landform),
                i + 1 < l->n_requests ? "," : "");
    }
    fputs("  ],\n  \"fairness\": {\n    \"dist_a_objective\": ", f);
    put_q(f, l->fairness.dist_a_objective);
    fputs(",\n    \"dist_b_objective\": ", f);
    put_q(f, l->fairness.dist_b_objective);
    fputs(",\n", f);
    put_dist_list(f, "dist_a_res", l->fairness.dist_a_res);
    fputs(",\n", f);
    put_dist_list(f, "dist_b_res", l->fairness.dist_b_res);
    fputs("\n  },\n  \"checks\": {\n", f);
    for (i = 0; i < CHECK_COUNT; i++)
        fprintf(f, "    \"%s\": %s%s\n", CHECK_NAMES[i], (l->checks >> i) & 1u ? "true" : "false", i + 1 < CHECK_COUNT ? "," : "");
    fprintf(f, "  },\n  \"route_count\": %d\n}\n", (int)l->route_count);
}

/* ---- --break: the deterministic edits of criterion 6 ---- */
static void remove_lane(om_lk_layout *l, int32_t idx) {
    int32_t i;
    for (i = idx; i + 1 < l->n_lanes; i++) l->lanes[i] = l->lanes[i + 1];
    memset(&l->lanes[l->n_lanes - 1], 0, sizeof l->lanes[0]);
    l->n_lanes--;
    for (i = 0; i < l->n_chokes; i++) if (l->chokes[i].lane > idx) l->chokes[i].lane--;
    for (i = 0; i < l->n_vantages; i++) {
        if (l->vantages[i].overlooks > idx) l->vantages[i].overlooks--;
        if (l->vantages[i].climb[0] > idx) l->vantages[i].climb[0]--;
        if (l->vantages[i].climb[1] > idx) l->vantages[i].climb[1]--;
    }
}

static int32_t nth_place_of(const om_lk_layout *l, int32_t kind) {
    int32_t i;
    for (i = 0; i < l->n_places; i++) if (l->places[i].kind == kind) return i;
    return -1;
}

/* 0 when applied; -1 (message on stderr) when the layout has nothing to edit */
static int apply_break(om_lk_layout *l, const char *what) {
    int32_t po = nth_place_of(l, OM_LK_PLACE_OBJECTIVE), i;
    if (!strcmp(what, "connected") || !strcmp(what, "approaches")) {
        int32_t obj = po >= 0 ? l->places[po].node : -1;
        int first_only = !strcmp(what, "approaches");
        for (i = l->n_lanes - 1; i >= 0 && first_only == 0; i--)
            if (l->lanes[i].a == obj || l->lanes[i].b == obj) remove_lane(l, i);
        for (i = 0; i < l->n_lanes && first_only; i++)
            if (l->lanes[i].a == obj || l->lanes[i].b == obj) { remove_lane(l, i); break; }
    } else if (!strcmp(what, "bypass")) {
        int32_t lane = l->n_chokes > 0 ? l->chokes[0].lane : -1;
        if (lane < 0 || lane >= l->n_lanes) { fprintf(stderr, "layout_dump: --break bypass: no choke\n"); return -1; }
        for (i = 0; i < l->n_lanes; i++) {
            const om_lk_lane *o = &l->lanes[i];
            if (o->kind == OM_LK_LANE_WAY_ROUND && ((o->a == l->lanes[lane].a && o->b == l->lanes[lane].b) ||
                                                    (o->a == l->lanes[lane].b && o->b == l->lanes[lane].a))) {
                remove_lane(l, i);
                return 0;
            }
        }
        fprintf(stderr, "layout_dump: --break bypass: no way round\n");
        return -1;
    } else if (!strcmp(what, "chokes")) {
        if (l->n_chokes < 1) { fprintf(stderr, "layout_dump: --break chokes: no choke\n"); return -1; }
        l->chokes[0].width = DRAFT_CHOKE_W_MAX + BREAK_EXTRA_W;
    } else if (!strcmp(what, "bounds")) {
        if (l->n_places < 1 || l->places[0].node < 0 || l->places[0].node >= l->n_nodes) {
            fprintf(stderr, "layout_dump: --break bounds: no place\n");
            return -1;
        }
        l->places[0].x = l->canvas + BREAK_EXTRA_W;
        l->nodes[l->places[0].node].x = l->canvas + BREAK_EXTRA_W;
    } else if (!strcmp(what, "fairness")) {
        int32_t pa = nth_place_of(l, OM_LK_PLACE_BASE_FORWARD), pr = nth_place_of(l, OM_LK_PLACE_RESOURCE), w = -1;
        om_lk_lane *n;
        for (i = 0; i < l->n_lanes && w < 0; i++) if (l->lanes[i].kind == OM_LK_LANE_ROUTE) w = i;
        if (pa < 0 || pr < 0 || w < 0 || l->n_lanes >= OM_LK_MAX_LANES) {
            fprintf(stderr, "layout_dump: --break fairness: nothing to join\n");
            return -1;
        }
        n = &l->lanes[l->n_lanes++];
        memset(n, 0, sizeof *n);
        n->kind = OM_LK_LANE_ROUTE;
        n->a = l->places[pa].node;
        n->b = l->places[pr].node;
        n->width = l->lanes[w].width;
        n->n_pts = 2;
        n->px[0] = l->nodes[n->a].x; n->py[0] = l->nodes[n->a].y;
        n->px[1] = l->nodes[n->b].x; n->py[1] = l->nodes[n->b].y;
    }
    return 0;
}

static int known_break(const char *s) {
    int i;
    for (i = 0; i < CHECK_COUNT; i++) if (!strcmp(s, CHECK_NAMES[i])) return 1;
    return 0;
}

/* ---- --check: a small parser for the files emit_json writes (numbers, strings, booleans, arrays, objects) ---- */
typedef struct { const char *p, *end; int err; } jp;

static void jws(jp *j) { while (j->p < j->end && (*j->p == ' ' || *j->p == '\n' || *j->p == '\r' || *j->p == '\t')) j->p++; }
static int jaccept(jp *j, char c) { jws(j); if (j->p < j->end && *j->p == c) { j->p++; return 1; } return 0; }
static void jexpect(jp *j, char c) { if (!jaccept(j, c)) j->err = 1; }

static void jstr(jp *j, char *buf, size_t cap) {
    size_t n = 0;
    jexpect(j, '"');
    while (!j->err && j->p < j->end && *j->p != '"') {
        if (*j->p == '\\' && j->p + 1 < j->end) j->p++;
        if (n + 1 < cap) buf[n++] = *j->p;
        j->p++;
    }
    if (j->p >= j->end) j->err = 1; else j->p++;
    buf[n] = 0;
}

/* a number as signed hundredths (digits beyond the second decimal are dropped; the writer prints exactly two) */
static int64_t jnum(jp *j) {
    int64_t whole = 0, frac = 0;
    int neg = 0, digits = 0, seen = 0;
    jws(j);
    if (j->p < j->end && *j->p == '-') { neg = 1; j->p++; }
    while (j->p < j->end && *j->p >= '0' && *j->p <= '9') { whole = whole * 10 + (*j->p - '0'); j->p++; seen = 1; }
    if (j->p < j->end && *j->p == '.') {
        j->p++;
        while (j->p < j->end && *j->p >= '0' && *j->p <= '9') {
            if (digits < 2) { frac = frac * 10 + (*j->p - '0'); digits++; }
            j->p++;
        }
    }
    if (!seen) { j->err = 1; return 0; }
    while (digits++ < 2) frac *= 10;
    return neg ? -(whole * HUND + frac) : whole * HUND + frac;
}

static double jdbl(jp *j) { return (double)jnum(j) / (double)HUND; }
static int32_t jint(jp *j) { return (int32_t)(jnum(j) / HUND); }

static int32_t jname(jp *j, int32_t domain) {
    char buf[KEY_MAX];
    int32_t id;
    jstr(j, buf, sizeof buf);
    for (id = 0; om_lk_name(domain, id); id++) if (!strcmp(om_lk_name(domain, id), buf)) return id;
    if (!strcmp(buf, "none") && domain == DOM_PLACE) return -1;
    j->err = 1;
    return 0;
}

static void jskip(jp *j) {
    char tmp[KEY_MAX];
    jws(j);
    if (j->p >= j->end) { j->err = 1; return; }
    if (*j->p == '"') jstr(j, tmp, sizeof tmp);
    else if (*j->p == '{') {
        j->p++;
        while (!j->err && !jaccept(j, '}')) { jstr(j, tmp, sizeof tmp); jexpect(j, ':'); jskip(j); jaccept(j, ','); }
    } else if (*j->p == '[') {
        j->p++;
        while (!j->err && !jaccept(j, ']')) { jskip(j); jaccept(j, ','); }
    } else if ((*j->p >= 'a' && *j->p <= 'z')) {
        while (j->p < j->end && *j->p >= 'a' && *j->p <= 'z') j->p++;
    } else jnum(j);
}

/* one field of an element: reads the key, ':' and returns the key; the caller reads or skips the value */
static int jkey(jp *j, char *key) {
    if (j->err || jaccept(j, '}')) return 0;
    jstr(j, key, KEY_MAX);
    jexpect(j, ':');
    return !j->err;
}

static void parse_place(jp *j, om_lk_place *p) {
    char k[KEY_MAX], s[KEY_MAX];
    jexpect(j, '{');
    while (jkey(j, k)) {
        if (!strcmp(k, "kind")) p->kind = jname(j, DOM_PLACE);
        else if (!strcmp(k, "side")) { jstr(j, s, sizeof s); p->side = !strcmp(s, "A") ? 0 : (!strcmp(s, "B") ? 1 : -1); }
        else if (!strcmp(k, "x")) p->x = jdbl(j);
        else if (!strcmp(k, "y")) p->y = jdbl(j);
        else if (!strcmp(k, "pad_r")) p->pad_r = jdbl(j);
        else if (!strcmp(k, "piece")) p->piece = jname(j, DOM_PIECE);
        else if (!strcmp(k, "node")) p->node = jint(j);
        else jskip(j);
        jaccept(j, ',');
    }
}

static void parse_node(jp *j, om_lk_node *n) {
    char k[KEY_MAX];
    jexpect(j, '{');
    while (jkey(j, k)) {
        if (!strcmp(k, "x")) n->x = jdbl(j);
        else if (!strcmp(k, "y")) n->y = jdbl(j);
        else if (!strcmp(k, "place")) n->place = jint(j);
        else jskip(j);
        jaccept(j, ',');
    }
}

static void parse_lane(jp *j, om_lk_lane *a) {
    char k[KEY_MAX];
    jexpect(j, '{');
    while (jkey(j, k)) {
        if (!strcmp(k, "kind")) a->kind = jname(j, DOM_LANE);
        else if (!strcmp(k, "a")) a->a = jint(j);
        else if (!strcmp(k, "b")) a->b = jint(j);
        else if (!strcmp(k, "width")) a->width = jdbl(j);
        else if (!strcmp(k, "pts")) {
            jexpect(j, '[');
            while (!j->err && !jaccept(j, ']')) {
                if (a->n_pts >= OM_LK_LANE_PTS) { j->err = 1; break; }
                jexpect(j, '[');
                a->px[a->n_pts] = jdbl(j);
                jaccept(j, ',');
                a->py[a->n_pts] = jdbl(j);
                jexpect(j, ']');
                a->n_pts++;
                jaccept(j, ',');
            }
        } else jskip(j);
        jaccept(j, ',');
    }
}

static void parse_choke(jp *j, om_lk_choke *c) {
    char k[KEY_MAX];
    jexpect(j, '{');
    while (jkey(j, k)) {
        if (!strcmp(k, "x")) c->x = jdbl(j);
        else if (!strcmp(k, "y")) c->y = jdbl(j);
        else if (!strcmp(k, "width")) c->width = jdbl(j);
        else if (!strcmp(k, "length")) c->length = jdbl(j);
        else if (!strcmp(k, "axis_k")) c->axis_k = jint(j);
        else if (!strcmp(k, "wall_span")) c->wall_span = jdbl(j);
        else if (!strcmp(k, "frac")) c->frac = jdbl(j);
        else if (!strcmp(k, "lane")) c->lane = jint(j);
        else if (!strcmp(k, "landform")) c->landform = jname(j, DOM_FORM);
        else if (!strcmp(k, "piece")) c->piece = jname(j, DOM_PIECE);
        else jskip(j);
        jaccept(j, ',');
    }
}

static void parse_vantage(jp *j, om_lk_vantage *v) {
    char k[KEY_MAX];
    jexpect(j, '{');
    while (jkey(j, k)) {
        if (!strcmp(k, "x")) v->x = jdbl(j);
        else if (!strcmp(k, "y")) v->y = jdbl(j);
        else if (!strcmp(k, "radius")) v->radius = jdbl(j);
        else if (!strcmp(k, "height_bands")) v->height_bands = jint(j);
        else if (!strcmp(k, "overlooks")) v->overlooks = jint(j);
        else if (!strcmp(k, "climb")) {
            jexpect(j, '[');
            v->climb[0] = jint(j);
            jaccept(j, ',');
            v->climb[1] = jint(j);
            jexpect(j, ']');
        } else if (!strcmp(k, "landform")) v->landform = jname(j, DOM_FORM);
        else if (!strcmp(k, "piece")) v->piece = jname(j, DOM_PIECE);
        else jskip(j);
        jaccept(j, ',');
    }
}

/* parse the array at the cursor into elements of `size` bytes at `base`; *count gets the number read (cap `cap`) */
static void parse_array(jp *j, void *base, size_t size, int32_t cap, int32_t *count, void (*one)(jp *, void *)) {
    jexpect(j, '[');
    while (!j->err && !jaccept(j, ']')) {
        if (*count >= cap) { j->err = 1; break; }
        one(j, (char *)base + (size_t)(*count)++ * size);
        jaccept(j, ',');
    }
}
static void one_place(jp *j, void *e) { parse_place(j, (om_lk_place *)e); }
static void one_node(jp *j, void *e) { parse_node(j, (om_lk_node *)e); }
static void one_lane(jp *j, void *e) { parse_lane(j, (om_lk_lane *)e); }
static void one_choke(jp *j, void *e) { parse_choke(j, (om_lk_choke *)e); }
static void one_vantage(jp *j, void *e) { parse_vantage(j, (om_lk_vantage *)e); }

static int cmd_check(const char *path, om_lk_layout *l, char *text) {
    FILE *f = fopen(path, "rb");
    size_t n;
    jp j;
    char k[KEY_MAX];
    int i, all = 1;
    if (!f) return usage("cannot open", path);
    n = fread(text, 1, FILE_MAX - 1, f);
    fclose(f);
    if (n == 0 || n >= FILE_MAX - 1) return usage("empty or too large", path);
    j.p = text; j.end = text + n; j.err = 0;
    memset(l, 0, sizeof *l);
    l->archetype = OM_LK_ARCH_ASSAULT;
    jexpect(&j, '{');
    while (jkey(&j, k)) {
        if (!strcmp(k, "canvas")) l->canvas = jdbl(&j);
        else if (!strcmp(k, "places")) parse_array(&j, l->places, sizeof l->places[0], OM_LK_MAX_PLACES, &l->n_places, one_place);
        else if (!strcmp(k, "nodes")) parse_array(&j, l->nodes, sizeof l->nodes[0], OM_LK_MAX_NODES, &l->n_nodes, one_node);
        else if (!strcmp(k, "lanes")) parse_array(&j, l->lanes, sizeof l->lanes[0], OM_LK_MAX_LANES, &l->n_lanes, one_lane);
        else if (!strcmp(k, "chokes")) parse_array(&j, l->chokes, sizeof l->chokes[0], OM_LK_MAX_CHOKES, &l->n_chokes, one_choke);
        else if (!strcmp(k, "vantages")) parse_array(&j, l->vantages, sizeof l->vantages[0], OM_LK_MAX_VANTAGES, &l->n_vantages, one_vantage);
        else jskip(&j);
        jaccept(&j, ',');
    }
    if (j.err) return usage("not a layout_dump file", path);
    om_lk_run_checks(l);
    for (i = 0; i < CHECK_COUNT; i++) {
        int ok = (int)((l->checks >> i) & 1u);
        printf("%s %s\n", CHECK_NAMES[i], ok ? "true" : "false");
        if (!ok) all = 0;
    }
    return all ? 0 : EXIT_FAIL;
}

/* ---- arguments ---- */
static int parse_u64(const char *s, uint64_t *out) {
    uint64_t v = 0;
    if (!*s) return 0;
    for (; *s; s++) {
        uint64_t d = (uint64_t)(*s - '0');
        if (*s < '0' || *s > '9' || v > (UINT64_MAX - d) / 10u) return 0;
        v = v * 10u + d;
    }
    *out = v;
    return 1;
}

static int parse_canvas(const char *s, double *out) {
    uint64_t whole = 0, frac = 0, scale = 1;
    int seen = 0;
    for (; *s >= '0' && *s <= '9'; s++) { whole = whole * 10u + (uint64_t)(*s - '0'); seen = 1; }
    if (*s == '.') {
        for (s++; *s >= '0' && *s <= '9' && scale < 1000000u; s++) { frac = frac * 10u + (uint64_t)(*s - '0'); scale *= 10u; seen = 1; }
        while (*s >= '0' && *s <= '9') s++;
    }
    if (!seen || *s) return 0;
    *out = (double)whole + (double)frac / (double)scale;
    return 1;
}

static int generate(om_lk_layout *l, uint64_t seed, double canvas, int32_t sides, const char *brk) {
    int rc = om_lk_generate(seed, OM_LK_ARCH_ASSAULT, canvas, sides, l);
    if (rc != 0) { fprintf(stderr, "layout_dump: om_lk_generate failed: %d\n", rc); return EXIT_FAIL; }
    if (brk) {
        if (apply_break(l, brk)) return EXIT_FAIL;
        om_lk_run_checks(l);
    }
    return 0;
}

int main(int argc, char **argv) {
    static om_lk_layout lay;
    static char text[FILE_MAX];
    const char *arch = "assault", *sides_s = "separate", *out = NULL, *out_dir = NULL, *brk = NULL, *check = NULL;
    const char *seeds = NULL, *seed_s = NULL, *canvas_s = NULL;
    uint64_t seed = 0, lo = 0, hi = 0, s;
    double canvas = DRAFT_CANVAS_ASSAULT;
    int32_t sides = OM_LK_SIDES_SEPARATE, i;
    int rc;
    for (i = 1; i < argc; i++) {
        const char *a = argv[i];
        const char **slot = !strcmp(a, "--seed") ? &seed_s : !strcmp(a, "--seeds") ? &seeds : !strcmp(a, "--archetype") ? &arch :
                            !strcmp(a, "--canvas") ? &canvas_s : !strcmp(a, "--sides") ? &sides_s : !strcmp(a, "--out") ? &out :
                            !strcmp(a, "--out-dir") ? &out_dir : !strcmp(a, "--break") ? &brk : !strcmp(a, "--check") ? &check : NULL;
        if (!slot) return usage("unknown option", a);
        if (i + 1 >= argc) return usage("missing value for", a);
        *slot = argv[++i];
    }
    if (check) return cmd_check(check, &lay, text);
    if (strcmp(arch, "assault")) {
        for (i = 0; i < (int32_t)(sizeof OTHER_ARCH / sizeof OTHER_ARCH[0]); i++)
            if (!strcmp(arch, OTHER_ARCH[i])) return usage("archetype not built (round A builds assault only)", arch);
        return usage("unknown archetype", arch);
    }
    for (sides = 0; sides < 3 && strcmp(sides_s, SIDES_NAMES[sides]); sides++) {}
    if (sides > 2) return usage("unknown sides mode", sides_s);
    if (canvas_s && !parse_canvas(canvas_s, &canvas)) return usage("bad canvas", canvas_s);
    if (brk && !known_break(brk)) return usage("unknown check for --break", brk);
    if (seeds) {
        const char *dots = strstr(seeds, "..");
        char head[32];
        size_t n = dots ? (size_t)(dots - seeds) : 0;
        if (!dots || n == 0 || n >= sizeof head) return usage("--seeds wants A..B", seeds);
        memcpy(head, seeds, n);
        head[n] = 0;
        if (!parse_u64(head, &lo) || !parse_u64(dots + 2, &hi) || lo > hi) return usage("--seeds wants A..B", seeds);
        if (!out_dir) return usage("--seeds needs --out-dir", NULL);
        for (s = lo; ; s++) {
            char path[PATH_MAX_LEN];
            FILE *f;
            rc = generate(&lay, s, canvas, sides, brk);
            if (rc) return rc;
            snprintf(path, sizeof path, "%s/layout_assault_s%llu_%s.json", out_dir, (unsigned long long)s, SIDES_NAMES[sides]);
            f = fopen(path, "wb");
            if (!f) { fprintf(stderr, "layout_dump: cannot write %s\n", path); return EXIT_FAIL; }
            emit_json(f, &lay);
            fclose(f);
            printf("seed %llu sides %s checks %d/%d\n", (unsigned long long)s, SIDES_NAMES[sides],
                   lk_checks_passed(lay.checks), CHECK_COUNT);
            if (s == hi) break;
        }
        return 0;
    }
    if (!seed_s) return usage("--seed (or --seeds, or --check) is required", NULL);
    if (!parse_u64(seed_s, &seed)) return usage("bad seed", seed_s);
    rc = generate(&lay, seed, canvas, sides, brk);
    if (rc) return rc;
    if (out) {
        FILE *f = fopen(out, "wb");
        if (!f) { fprintf(stderr, "layout_dump: cannot write %s\n", out); return EXIT_FAIL; }
        emit_json(f, &lay);
        fclose(f);
    } else emit_json(stdout, &lay);
    return 0;
}
