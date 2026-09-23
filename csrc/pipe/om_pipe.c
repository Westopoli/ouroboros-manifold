/* csrc/pipe/om_pipe.c -- T1 pipe server (docs/architecture.md, "C transport v1").
 *
 * Reads length-prefixed JSON command frames from stdin, drives an om_world
 * through libouroboros.so, and writes length-prefixed JSON response frames
 * to stdout. Framing (both directions): 4-byte big-endian length prefix,
 * then a UTF-8 JSON object, no separators. stdout carries frames only.
 *
 * Documented deviation from docs/architecture.md (spec_file
 * docs/northstar/plans/push/specs/T1.md, "Documented deviation" section):
 * set_seed emits no frame at all, not even an ack. The fenced test
 * (tests/transport/test_pipe_shapes.py) asserts the ten frames right after
 * hello are all "delta" once set_seed/step(n:10) run, which only holds if
 * set_seed is silent.
 */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ouroboros_sim.h"

/* ---------------------------------------------------------------------
 * Frame I/O
 * --------------------------------------------------------------------- */

static int read_frame(char **out_buf, uint32_t *out_len) {
    unsigned char hdr[4];
    if (fread(hdr, 1, 4, stdin) != 4) return -1;
    uint32_t len = ((uint32_t)hdr[0] << 24) | ((uint32_t)hdr[1] << 16) |
                   ((uint32_t)hdr[2] << 8) | (uint32_t)hdr[3];
    char *buf = malloc((size_t)len + 1);
    if (!buf) return -1;
    if (len > 0 && fread(buf, 1, len, stdin) != len) {
        free(buf);
        return -1;
    }
    buf[len] = '\0';
    *out_buf = buf;
    *out_len = len;
    return 0;
}

static void write_frame(const char *buf, uint32_t len) {
    unsigned char hdr[4] = {
        (unsigned char)((len >> 24) & 0xFF), (unsigned char)((len >> 16) & 0xFF),
        (unsigned char)((len >> 8) & 0xFF), (unsigned char)(len & 0xFF)};
    fwrite(hdr, 1, 4, stdout);
    fwrite(buf, 1, len, stdout);
    fflush(stdout);
}

/* ---------------------------------------------------------------------
 * Growable JSON output buffer
 * --------------------------------------------------------------------- */

typedef struct {
    char *buf;
    size_t len;
    size_t cap;
} jbuf;

static void jb_init(jbuf *j) {
    j->cap = 256;
    j->buf = malloc(j->cap);
    j->len = 0;
    j->buf[0] = '\0';
}

static void jb_free(jbuf *j) { free(j->buf); }

static void jb_reserve(jbuf *j, size_t extra) {
    if (j->len + extra + 1 <= j->cap) return;
    while (j->len + extra + 1 > j->cap) j->cap *= 2;
    j->buf = realloc(j->buf, j->cap);
}

static void jb_raw(jbuf *j, const char *s) {
    size_t n = strlen(s);
    jb_reserve(j, n);
    memcpy(j->buf + j->len, s, n);
    j->len += n;
    j->buf[j->len] = '\0';
}

static void jb_putc(jbuf *j, char c) {
    jb_reserve(j, 1);
    j->buf[j->len++] = c;
    j->buf[j->len] = '\0';
}

static void jb_str(jbuf *j, const char *s) {
    jb_putc(j, '"');
    for (const unsigned char *p = (const unsigned char *)s; *p; p++) {
        if (*p == '"' || *p == '\\') {
            jb_putc(j, '\\');
            jb_putc(j, (char)*p);
        } else if (*p == '\n') {
            jb_putc(j, '\\');
            jb_putc(j, 'n');
        } else if (*p < 0x20) {
            char tmp[8];
            snprintf(tmp, sizeof tmp, "\\u%04x", (unsigned)*p);
            jb_raw(j, tmp);
        } else {
            jb_putc(j, (char)*p);
        }
    }
    jb_putc(j, '"');
}

static void jb_key(jbuf *j, const char *k) {
    jb_str(j, k);
    jb_putc(j, ':');
}

static void jb_int(jbuf *j, int64_t v) {
    char tmp[32];
    snprintf(tmp, sizeof tmp, "%lld", (long long)v);
    jb_raw(j, tmp);
}

static void jb_uint(jbuf *j, uint64_t v) {
    char tmp[32];
    snprintf(tmp, sizeof tmp, "%llu", (unsigned long long)v);
    jb_raw(j, tmp);
}

static void jb_double(jbuf *j, double v) {
    char tmp[64];
    snprintf(tmp, sizeof tmp, "%.17g", v);
    jb_raw(j, tmp);
}

static void jb_bool(jbuf *j, int v) { jb_raw(j, v ? "true" : "false"); }

/* ---------------------------------------------------------------------
 * Minimal JSON field extraction for the flat command objects this server
 * reads (docs/northstar/spec_factory/transport/command.schema.json). Every
 * command frame is a single flat object -- no nesting except the top-level
 * "features" array -- so a plain key search is sufficient and avoids
 * pulling in a general JSON parser this build does not link.
 * --------------------------------------------------------------------- */

static const char *find_key(const char *json, const char *key) {
    char pat[64];
    snprintf(pat, sizeof pat, "\"%s\"", key);
    const char *p = strstr(json, pat);
    if (!p) return NULL;
    p += strlen(pat);
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') p++;
    if (*p != ':') return NULL;
    p++;
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') p++;
    return p;
}

static int get_str(const char *json, const char *key, char *out, size_t cap) {
    const char *p = find_key(json, key);
    if (!p || *p != '"') return 0;
    p++;
    size_t i = 0;
    while (*p && *p != '"' && i + 1 < cap) {
        if (*p == '\\' && p[1]) p++;
        out[i++] = *p++;
    }
    out[i] = '\0';
    return 1;
}

static int get_i64(const char *json, const char *key, int64_t *out) {
    const char *p = find_key(json, key);
    if (!p) return 0;
    char *end;
    long long v = strtoll(p, &end, 10);
    if (end == p) return 0;
    *out = (int64_t)v;
    return 1;
}

static int get_bool(const char *json, const char *key, int *out) {
    const char *p = find_key(json, key);
    if (!p) return 0;
    if (!strncmp(p, "true", 4)) {
        *out = 1;
        return 1;
    }
    if (!strncmp(p, "false", 5)) {
        *out = 0;
        return 1;
    }
    return 0;
}

static int get_int_array(const char *json, const char *key, int *out, int max) {
    const char *p = find_key(json, key);
    if (!p || *p != '[') return 0;
    p++;
    int n = 0;
    for (;;) {
        while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r' || *p == ',') p++;
        if (*p == ']' || *p == '\0') break;
        char *end;
        long v = strtol(p, &end, 10);
        if (end == p) break;
        if (n < max) out[n++] = (int)v;
        p = end;
    }
    return n;
}

/* ---------------------------------------------------------------------
 * World state and per-tick diff tracking
 * --------------------------------------------------------------------- */

static om_world *W = NULL;
static uint64_t g_tick = 0;
static uint32_t g_n_regions = 0;

static int32_t *prev_owner = NULL;
static double *prev_mil = NULL, *prev_econ = NULL, *prev_ten = NULL;
static double *prev_pop = NULL, *prev_stab = NULL, *prev_cap = NULL;

static uint8_t faction_seen[OM_MAX_FACTIONS];
static double prev_budget[OM_MAX_FACTIONS];
static double prev_tech[OM_MAX_FACTIONS];

#define LOG_MAX 8192

static void realloc_regions(uint32_t n) {
    free(prev_owner);
    free(prev_mil);
    free(prev_econ);
    free(prev_ten);
    free(prev_pop);
    free(prev_stab);
    free(prev_cap);
    g_n_regions = n;
    prev_owner = malloc(sizeof(*prev_owner) * (n ? n : 1));
    prev_mil = malloc(sizeof(*prev_mil) * (n ? n : 1));
    prev_econ = malloc(sizeof(*prev_econ) * (n ? n : 1));
    prev_ten = malloc(sizeof(*prev_ten) * (n ? n : 1));
    prev_pop = malloc(sizeof(*prev_pop) * (n ? n : 1));
    prev_stab = malloc(sizeof(*prev_stab) * (n ? n : 1));
    prev_cap = malloc(sizeof(*prev_cap) * (n ? n : 1));
}

static void capture_baseline(void) {
    for (uint32_t i = 0; i < g_n_regions; i++) {
        prev_owner[i] = om_region_owner(W, i);
        prev_mil[i] = om_region_field(W, i, OM_F_MILITARY);
        prev_econ[i] = om_region_field(W, i, OM_F_ECONOMY);
        prev_ten[i] = om_region_field(W, i, OM_F_TENSION);
        prev_pop[i] = om_region_field(W, i, OM_F_POPULATION);
        prev_stab[i] = om_region_composite(W, i, OM_C_STABILITY);
        prev_cap[i] = om_region_composite(W, i, OM_C_CAPACITY);
    }
    memset(faction_seen, 0, sizeof faction_seen);
    uint32_t nf = om_faction_count(W);
    if (nf > OM_MAX_FACTIONS) nf = OM_MAX_FACTIONS;
    for (uint32_t f = 0; f < nf; f++) {
        faction_seen[f] = 1;
        prev_budget[f] = om_faction_budget(W, f);
        prev_tech[f] = om_faction_tech(W, f);
    }
}

/* ---------------------------------------------------------------------
 * Response helpers
 * --------------------------------------------------------------------- */

static void write_ack(const char *name) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "ack");
    jb_putc(&j, ',');
    jb_key(&j, "name");
    jb_str(&j, name);
    jb_putc(&j, ',');
    jb_key(&j, "tick");
    jb_uint(&j, g_tick);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

static void write_error(const char *name, const char *reason) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "error");
    jb_putc(&j, ',');
    jb_key(&j, "name");
    jb_str(&j, name);
    jb_putc(&j, ',');
    jb_key(&j, "reason");
    jb_str(&j, reason);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

/* ---------------------------------------------------------------------
 * snapshot: full state (explicit "snapshot" cmd, and after "load")
 * --------------------------------------------------------------------- */

static void write_snapshot(void) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "snapshot");
    jb_putc(&j, ',');
    jb_key(&j, "tick");
    jb_uint(&j, g_tick);
    jb_putc(&j, ',');
    jb_key(&j, "checksum");
    jb_uint(&j, om_world_get_state_checksum(W));
    jb_putc(&j, ',');

    jb_key(&j, "regions");
    jb_putc(&j, '[');
    for (uint32_t i = 0; i < g_n_regions; i++) {
        if (i > 0) jb_putc(&j, ',');
        jb_putc(&j, '{');
        jb_key(&j, "i");
        jb_uint(&j, i);
        jb_putc(&j, ',');
        jb_key(&j, "owner");
        jb_int(&j, om_region_owner(W, i));
        jb_putc(&j, ',');
        jb_key(&j, "tier");
        jb_uint(&j, (uint32_t)om_region_tier(W, i));
        jb_putc(&j, ',');
        jb_key(&j, "military");
        jb_double(&j, om_region_field(W, i, OM_F_MILITARY));
        jb_putc(&j, ',');
        jb_key(&j, "economy");
        jb_double(&j, om_region_field(W, i, OM_F_ECONOMY));
        jb_putc(&j, ',');
        jb_key(&j, "tension");
        jb_double(&j, om_region_field(W, i, OM_F_TENSION));
        jb_putc(&j, ',');
        jb_key(&j, "population");
        jb_double(&j, om_region_field(W, i, OM_F_POPULATION));
        jb_putc(&j, ',');
        jb_key(&j, "stability");
        jb_double(&j, om_region_composite(W, i, OM_C_STABILITY));
        jb_putc(&j, ',');
        jb_key(&j, "capacity");
        jb_double(&j, om_region_composite(W, i, OM_C_CAPACITY));
        jb_putc(&j, '}');
    }
    jb_raw(&j, "],");

    uint32_t nf = om_faction_count(W);
    jb_key(&j, "factions");
    jb_putc(&j, '[');
    for (uint32_t f = 0; f < nf; f++) {
        if (f > 0) jb_putc(&j, ',');
        jb_putc(&j, '{');
        jb_key(&j, "id");
        jb_uint(&j, f);
        jb_putc(&j, ',');
        jb_key(&j, "archetype");
        jb_uint(&j, (uint32_t)om_faction_archetype(W, (int32_t)f));
        jb_putc(&j, ',');
        jb_key(&j, "budget");
        jb_double(&j, om_faction_budget(W, (int32_t)f));
        jb_putc(&j, ',');
        jb_key(&j, "tech");
        jb_double(&j, om_faction_tech(W, (int32_t)f));
        jb_putc(&j, ',');
        jb_key(&j, "stance");
        jb_putc(&j, '[');
        int wrote = 0;
        for (uint32_t k = 0; k < nf; k++) {
            if (k == f) continue;
            if (wrote) jb_putc(&j, ',');
            jb_uint(&j, (uint32_t)om_faction_stance(W, (int32_t)f, (int32_t)k));
            wrote = 1;
        }
        jb_putc(&j, ']');
        jb_putc(&j, '}');
    }
    jb_raw(&j, "],");

    jb_key(&j, "edges");
    jb_putc(&j, '[');
    {
        /* om_region_neighbors is declared in ouroboros_sim.h (the header's
         * documented O(degree) accessor for this) but is not implemented in
         * any csrc source file and does not appear in libouroboros.so's symbol
         * table -- linking against it fails. Escalated:
         * .swarm/t1/questions/leaf-01-Q1.md. Worked around with the O(N^2)
         * om_region_edge sweep the header comment says om_region_neighbors
         * exists to avoid; om_region_edge itself is implemented (csrc/faction.c). */
        int wrote = 0;
        for (uint32_t i = 0; i < g_n_regions; i++) {
            for (uint32_t nb = i + 1; nb < g_n_regions; nb++) {
                om_edge_type t;
                if (!om_region_edge(W, i, nb, &t)) continue;
                if (wrote) jb_putc(&j, ',');
                jb_putc(&j, '{');
                jb_key(&j, "a");
                jb_uint(&j, i);
                jb_putc(&j, ',');
                jb_key(&j, "b");
                jb_uint(&j, nb);
                jb_putc(&j, ',');
                jb_key(&j, "t");
                jb_uint(&j, (uint32_t)t);
                jb_putc(&j, '}');
                wrote = 1;
            }
        }
    }
    jb_raw(&j, "],");

    jb_key(&j, "telegraphs");
    jb_putc(&j, '[');
    {
        static om_telegraph tbuf[1024];
        uint32_t n = om_pending_telegraphs(W, tbuf, 1024);
        if (n > 1024) n = 1024;
        for (uint32_t k = 0; k < n; k++) {
            if (k > 0) jb_putc(&j, ',');
            jb_putc(&j, '{');
            jb_key(&j, "attacker");
            jb_int(&j, tbuf[k].attacker);
            jb_putc(&j, ',');
            jb_key(&j, "target");
            jb_uint(&j, tbuf[k].target_idx);
            jb_putc(&j, ',');
            jb_key(&j, "commit");
            jb_double(&j, tbuf[k].commit);
            jb_putc(&j, ',');
            jb_key(&j, "declared_tick");
            jb_uint(&j, tbuf[k].declared_tick);
            jb_putc(&j, '}');
        }
    }
    jb_putc(&j, ']');

    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

/* ---------------------------------------------------------------------
 * delta: one frame per tick advanced (step / run_to)
 * --------------------------------------------------------------------- */

static void write_delta(void) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "delta");
    jb_putc(&j, ',');
    jb_key(&j, "tick");
    jb_uint(&j, g_tick);
    jb_putc(&j, ',');

    uint32_t cadence = om_checksum_cadence();
    uint64_t checksum = (cadence != 0 && g_tick % cadence == 0) ? om_world_get_state_checksum(W) : 0;
    jb_key(&j, "checksum");
    jb_uint(&j, checksum);
    jb_putc(&j, ',');

    jb_key(&j, "regions");
    jb_putc(&j, '[');
    int wrote = 0;
    for (uint32_t i = 0; i < g_n_regions; i++) {
        int32_t owner = om_region_owner(W, i);
        double mil = om_region_field(W, i, OM_F_MILITARY);
        double econ = om_region_field(W, i, OM_F_ECONOMY);
        double ten = om_region_field(W, i, OM_F_TENSION);
        double pop = om_region_field(W, i, OM_F_POPULATION);
        double stab = om_region_composite(W, i, OM_C_STABILITY);
        double cap = om_region_composite(W, i, OM_C_CAPACITY);
        if (owner == prev_owner[i] && mil == prev_mil[i] && econ == prev_econ[i] &&
            ten == prev_ten[i] && pop == prev_pop[i] && stab == prev_stab[i] && cap == prev_cap[i]) {
            continue;
        }
        if (wrote) jb_putc(&j, ',');
        wrote = 1;
        jb_putc(&j, '{');
        jb_key(&j, "i");
        jb_uint(&j, i);
        jb_putc(&j, ',');
        jb_key(&j, "owner");
        jb_int(&j, owner);
        jb_putc(&j, ',');
        jb_key(&j, "military");
        jb_double(&j, mil);
        jb_putc(&j, ',');
        jb_key(&j, "economy");
        jb_double(&j, econ);
        jb_putc(&j, ',');
        jb_key(&j, "tension");
        jb_double(&j, ten);
        jb_putc(&j, ',');
        jb_key(&j, "population");
        jb_double(&j, pop);
        jb_putc(&j, ',');
        jb_key(&j, "stability");
        jb_double(&j, stab);
        jb_putc(&j, ',');
        jb_key(&j, "capacity");
        jb_double(&j, cap);
        jb_putc(&j, '}');
        prev_owner[i] = owner;
        prev_mil[i] = mil;
        prev_econ[i] = econ;
        prev_ten[i] = ten;
        prev_pop[i] = pop;
        prev_stab[i] = stab;
        prev_cap[i] = cap;
    }
    jb_raw(&j, "],");

    jb_key(&j, "events");
    jb_putc(&j, '[');
    {
        static om_fired_event ebuf[LOG_MAX];
        uint32_t n = om_tick_events(W, ebuf, LOG_MAX);
        if (n > LOG_MAX) n = LOG_MAX;
        for (uint32_t k = 0; k < n; k++) {
            if (k > 0) jb_putc(&j, ',');
            const om_fired_event *e = &ebuf[k];
            jb_putc(&j, '{');
            jb_key(&j, "tick");
            jb_uint(&j, e->tick);
            jb_putc(&j, ',');
            jb_key(&j, "region");
            jb_uint(&j, e->region_idx);
            jb_putc(&j, ',');
            jb_key(&j, "template");
            jb_uint(&j, e->template_id);
            jb_putc(&j, ',');
            jb_key(&j, "chain");
            jb_int(&j, e->chain_tag);
            jb_putc(&j, ',');
            jb_key(&j, "source");
            jb_uint(&j, e->source);
            jb_putc(&j, ',');
            jb_key(&j, "delta");
            jb_putc(&j, '[');
            for (int fi = 0; fi < OM_F_COUNT; fi++) {
                if (fi > 0) jb_putc(&j, ',');
                jb_double(&j, e->delta[fi]);
            }
            jb_putc(&j, ']');
            jb_putc(&j, ',');
            jb_key(&j, "creates_faction");
            jb_uint(&j, e->creates_faction);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    jb_key(&j, "attacks");
    jb_putc(&j, '[');
    {
        static om_attack_result abuf[LOG_MAX];
        uint32_t n = om_tick_attacks(W, abuf, LOG_MAX);
        if (n > LOG_MAX) n = LOG_MAX;
        for (uint32_t k = 0; k < n; k++) {
            if (k > 0) jb_putc(&j, ',');
            const om_attack_result *a = &abuf[k];
            jb_putc(&j, '{');
            jb_key(&j, "attacker");
            jb_int(&j, a->attacker);
            jb_putc(&j, ',');
            jb_key(&j, "target");
            jb_uint(&j, a->target_idx);
            jb_putc(&j, ',');
            jb_key(&j, "d_military");
            jb_double(&j, a->d_military);
            jb_putc(&j, ',');
            jb_key(&j, "d_economy");
            jb_double(&j, a->d_economy);
            jb_putc(&j, ',');
            jb_key(&j, "d_tension");
            jb_double(&j, a->d_tension);
            jb_putc(&j, ',');
            jb_key(&j, "collision");
            jb_uint(&j, a->collision);
            jb_putc(&j, ',');
            jb_key(&j, "conquest");
            jb_uint(&j, a->conquest);
            jb_putc(&j, ',');
            jb_key(&j, "outcome");
            jb_uint(&j, a->outcome);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    jb_key(&j, "collisions");
    jb_putc(&j, '[');
    {
        static om_collision cbuf[LOG_MAX];
        uint32_t n = om_tick_collisions(W, cbuf, LOG_MAX);
        if (n > LOG_MAX) n = LOG_MAX;
        for (uint32_t k = 0; k < n; k++) {
            if (k > 0) jb_putc(&j, ',');
            const om_collision *c = &cbuf[k];
            jb_putc(&j, '{');
            jb_key(&j, "target");
            jb_uint(&j, c->target_idx);
            jb_putc(&j, ',');
            jb_key(&j, "factions");
            jb_putc(&j, '[');
            for (uint32_t fi = 0; fi < c->n_colliders && fi < OM_MAX_COLLIDERS; fi++) {
                if (fi > 0) jb_putc(&j, ',');
                jb_int(&j, c->faction[fi]);
            }
            jb_putc(&j, ']');
            jb_putc(&j, ',');
            jb_key(&j, "winner");
            jb_int(&j, c->winner);
            jb_putc(&j, ',');
            jb_key(&j, "margin");
            jb_double(&j, c->margin);
            jb_putc(&j, ',');
            jb_key(&j, "refund");
            jb_double(&j, c->refund);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    jb_key(&j, "revolts");
    jb_putc(&j, '[');
    {
        static om_admin_roll rbuf[LOG_MAX];
        uint32_t n = om_tick_admin_rolls(W, rbuf, LOG_MAX);
        if (n > LOG_MAX) n = LOG_MAX;
        int rwrote = 0;
        for (uint32_t k = 0; k < n; k++) {
            const om_admin_roll *r = &rbuf[k];
            if (!r->triggered) continue;
            if (rwrote) jb_putc(&j, ',');
            rwrote = 1;
            jb_putc(&j, '{');
            jb_key(&j, "region");
            jb_uint(&j, r->region_idx);
            jb_putc(&j, ',');
            jb_key(&j, "faction");
            jb_int(&j, r->faction_id);
            jb_putc(&j, ',');
            jb_key(&j, "roll");
            jb_double(&j, r->draw);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    jb_key(&j, "factions");
    jb_putc(&j, '[');
    {
        uint32_t nf = om_faction_count(W);
        if (nf > OM_MAX_FACTIONS) nf = OM_MAX_FACTIONS;
        int fwrote = 0;
        for (uint32_t f = 0; f < nf; f++) {
            double budget = om_faction_budget(W, (int32_t)f);
            double tech = om_faction_tech(W, (int32_t)f);
            int changed = !faction_seen[f] || budget != prev_budget[f] || tech != prev_tech[f];
            faction_seen[f] = 1;
            prev_budget[f] = budget;
            prev_tech[f] = tech;
            if (!changed) continue;
            if (fwrote) jb_putc(&j, ',');
            fwrote = 1;
            jb_putc(&j, '{');
            jb_key(&j, "id");
            jb_uint(&j, f);
            jb_putc(&j, ',');
            jb_key(&j, "budget");
            jb_double(&j, budget);
            jb_putc(&j, ',');
            jb_key(&j, "tech");
            jb_double(&j, tech);
            jb_putc(&j, '}');
        }
    }
    jb_putc(&j, ']');

    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

/* ---------------------------------------------------------------------
 * Command handlers
 * --------------------------------------------------------------------- */

static void handle_set_seed(const char *json) {
    int64_t seed = 0, n_regions = 0;
    get_i64(json, "seed", &seed);
    get_i64(json, "n_regions", &n_regions);
    int feats[64];
    int nf = get_int_array(json, "features", feats, 64);

    if (W) om_world_free(W);
    W = om_world_new((uint32_t)n_regions, (uint64_t)seed);
    g_tick = 0;
    for (int i = 0; i < nf; i++) om_world_set_feature(W, (om_feature)feats[i], 1);
    om_world_generate(W);
    if (!om_world_generated(W)) {
        write_error("set_seed", "generation failed");
        return;
    }
    realloc_regions(om_region_count(W));
    capture_baseline();
    /* Deviation from docs/architecture.md: no frame at all on success, not even an ack. */
}

static void handle_step(const char *json) {
    if (!W) {
        write_error("step", "no world");
        return;
    }
    int64_t n = 1;
    get_i64(json, "n", &n);
    for (int64_t i = 0; i < n; i++) {
        g_tick = om_world_step(W);
        write_delta();
    }
    write_ack("step");
}

static void handle_run_to(const char *json) {
    if (!W) {
        write_error("run_to", "no world");
        return;
    }
    int64_t target = 0;
    if (!get_i64(json, "tick", &target)) {
        write_error("run_to", "missing tick");
        return;
    }
    while ((int64_t)g_tick < target) {
        g_tick = om_world_step(W);
        write_delta();
    }
    write_ack("run_to");
}

static void handle_set_feature(const char *json) {
    if (!W) {
        write_error("set_feature", "no world");
        return;
    }
    int64_t feature = -1;
    int on = 0;
    if (!get_i64(json, "feature", &feature) || !get_bool(json, "on", &on)) {
        write_error("set_feature", "missing feature or on");
        return;
    }
    om_world_set_feature(W, (om_feature)feature, on);
    write_ack("set_feature");
}

static void handle_inject(const char *json) {
#ifdef OM_DEBUG_INJECT
    if (!W) {
        write_error("inject", "no world");
        return;
    }
    int64_t bug = -1;
    if (!get_i64(json, "bug", &bug)) {
        write_error("inject", "missing bug");
        return;
    }
    om_debug_inject(W, (om_bug)bug);
    write_ack("inject");
#else
    (void)json;
    write_error("inject", "debug build required");
#endif
}

static void handle_save(const char *json) {
    if (!W) {
        write_error("save", "no world");
        return;
    }
    char path[1024];
    if (!get_str(json, "path", path, sizeof path)) {
        write_error("save", "missing path");
        return;
    }
    uint32_t need = om_save_state_size(W);
    uint8_t *buf = malloc(need ? need : 1);
    om_save_state_write(W, buf, need);
    FILE *f = fopen(path, "wb");
    if (!f) {
        free(buf);
        write_error("save", "open failed");
        return;
    }
    fwrite(buf, 1, need, f);
    fclose(f);
    free(buf);
    write_ack("save");
}

static void handle_load(const char *json) {
    char path[1024];
    if (!get_str(json, "path", path, sizeof path)) {
        write_error("load", "missing path");
        return;
    }
    FILE *f = fopen(path, "rb");
    if (!f) {
        write_error("load", "open failed");
        return;
    }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz < 0) {
        fclose(f);
        write_error("load", "stat failed");
        return;
    }
    uint8_t *buf = malloc((size_t)sz ? (size_t)sz : 1);
    size_t got = fread(buf, 1, (size_t)sz, f);
    fclose(f);
    if (got != (size_t)sz) {
        free(buf);
        write_error("load", "read failed");
        return;
    }
    if (!W) W = om_world_new(1, 0);
    om_load_state_read(W, buf, (uint32_t)sz);
    free(buf);
    g_n_regions = om_region_count(W);
    realloc_regions(g_n_regions);
    capture_baseline();
    write_snapshot();
}

/* ---------------------------------------------------------------------
 * main
 * --------------------------------------------------------------------- */

int main(void) {
    jbuf hello;
    jb_init(&hello);
    jb_putc(&hello, '{');
    jb_key(&hello, "type");
    jb_str(&hello, "hello");
    jb_putc(&hello, ',');
    jb_key(&hello, "abi");
    jb_uint(&hello, om_abi_version());
    jb_putc(&hello, ',');
    jb_key(&hello, "layout_ok");
    jb_bool(&hello, om_abi_layout_check(sizeof(om_trace_row), sizeof(om_drift_row), sizeof(om_collision)) != 0);
    jb_putc(&hello, ',');
    jb_key(&hello, "seed");
    jb_uint(&hello, 0);
    jb_putc(&hello, ',');
    jb_key(&hello, "n_regions");
    jb_uint(&hello, 0);
    jb_putc(&hello, ',');
    jb_key(&hello, "features");
    jb_raw(&hello, "[],");
    jb_key(&hello, "checksum_cadence");
    jb_uint(&hello, om_checksum_cadence());
    jb_putc(&hello, '}');
    write_frame(hello.buf, (uint32_t)hello.len);
    jb_free(&hello);

    for (;;) {
        char *buf;
        uint32_t len;
        if (read_frame(&buf, &len) != 0) break;

        char name[32] = {0};
        if (!get_str(buf, "name", name, sizeof name)) {
            write_error("", "missing name");
            free(buf);
            continue;
        }

        if (!strcmp(name, "step")) {
            handle_step(buf);
        } else if (!strcmp(name, "run_to")) {
            handle_run_to(buf);
        } else if (!strcmp(name, "snapshot")) {
            if (!W) {
                write_error("snapshot", "no world");
            } else {
                write_snapshot();
            }
        } else if (!strcmp(name, "set_seed")) {
            handle_set_seed(buf);
        } else if (!strcmp(name, "set_feature")) {
            handle_set_feature(buf);
        } else if (!strcmp(name, "inject")) {
            handle_inject(buf);
        } else if (!strcmp(name, "save")) {
            handle_save(buf);
        } else if (!strcmp(name, "load")) {
            handle_load(buf);
        } else if (!strcmp(name, "quit")) {
            free(buf);
            fflush(stdout);
            return 0;
        } else {
            write_error(name, "unknown command");
        }

        free(buf);
    }

    fflush(stdout);
    return 0;
}
