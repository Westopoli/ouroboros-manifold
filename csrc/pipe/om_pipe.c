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
 *
 * T1-2 (session commands, v1.1, 2026-09-24): mission_start/mission_end/
 * jump/tactical_step/command/list_saves. Real gaps found while wiring
 * these against csrc/ouroboros_sim.h, all handled by leaving the affected
 * frame keys at 0/empty rather than inventing values -- see the comment at
 * each spot below and the T1-2 leaf report:
 *   - om_mission_start (csrc/diplomacy.c) is NOT a "start the mission"
 *     entrypoint; it only encodes the calling faction's tech tier into an
 *     opaque id for om_force_allocator_run/om_mission_unit_tier. The real
 *     region/archetype/objective/phase wiring is composed here from
 *     om_mission_build_candidate_pool + om_mission_select +
 *     om_mission_candidates + om_mission_setup + om_mission_build_objectives
 *     + om_mission_begin, none of which docs/architecture.md's session
 *     commands text names.
 *   - "region_delta" in the debrief frame is from om_mission_get_region_delta
 *     (T1-8 accessor). om_mission_apply_consequences runs inside om_mission_end
 *     when mission_set is true and end_applied is false; the accessor returns
 *     the stored delta. When the accessor returns 0 (no consequence applied)
 *     all four keys are 0.
 *   - om_chronicle_entry_get (T1-9) is used alongside om_chronicle_get_cluster
 *     to read fragment_ids[3] per entry; emitted as "fragment_ids":[id0,id1,id2]
 *     and "fragment":id0. When om_chronicle_entry_get returns 0 (cluster exists
 *     but text pass never ran for it) fragment_ids is [-1,-1,-1] and fragment is
 *     -1. refs.factions is [entry faction_ref] when it is >= 0, else [].
 *   - Every om_map_get_* node/canvas accessor is a STUB
 *     (csrc/tactical_mapgen.c: E-11 wiring, card B10/B12 not landed).
 *     There is also no enumerator for live tactical
 *     unit ids at all (only per-id accessors like om_unit_get_pos, and no
 *     om_map_get_cover/obstacle count+get pair even once B10 lands map
 *     nodes). "map.nodes" reflects the stub (always empty), "map.cover" and
 *     "map.obstacles" are always empty, and "units"/"visible" are always
 *     empty. "tick" is this file's own g_tactical_tick counter, since
 *     om_tactical_step's real counter does not advance with zero units.
 *   - There is no om_command_hold symbol (only om_unit_order_hold_node(w,
 *     unit_id, node_id), which needs a node this command frame does not
 *     carry); verb "hold" always answers error.
 *   - om_load_state_read returns one bool for both "version mismatch" and
 *     "corrupt" (csrc/save.c); this file always reports "corrupt".
  *   - GEN_PHASE_BRIEFING/GEN_PHASE_MISSION are private #defines in
 *     csrc/generational.c, not exported by ouroboros_sim.h; mirrored below
 *     as OM_PIPE_CHAPTER_PHASE_* since om_chapter_set_phase/
 *     om_chapter_mission_realtime take/read the raw int.
 */

/* Mirrors OM_SAVE_FORMAT_VERSION in om_internal.h (not visible to the pipe). */
#include "pipe_internal.h"

/* OM_MAX_UNITS is now defined in csrc/ouroboros_sim.h (HDR3); no local mirror needed. */

/* ---------------------------------------------------------------------
 * Frame I/O
 * --------------------------------------------------------------------- */

int read_frame(char **out_buf, uint32_t *out_len) {
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

void write_frame(const char *buf, uint32_t len) {
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


void jb_init(jbuf *j) {
    j->cap = 256;
    j->buf = malloc(j->cap);
    j->len = 0;
    j->buf[0] = '\0';
}

void jb_free(jbuf *j) { free(j->buf); }

void jb_reserve(jbuf *j, size_t extra) {
    if (j->len + extra + 1 <= j->cap) return;
    while (j->len + extra + 1 > j->cap) j->cap *= 2;
    j->buf = realloc(j->buf, j->cap);
}

void jb_raw(jbuf *j, const char *s) {
    size_t n = strlen(s);
    jb_reserve(j, n);
    memcpy(j->buf + j->len, s, n);
    j->len += n;
    j->buf[j->len] = '\0';
}

void jb_putc(jbuf *j, char c) {
    jb_reserve(j, 1);
    j->buf[j->len++] = c;
    j->buf[j->len] = '\0';
}

void jb_str(jbuf *j, const char *s) {
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

void jb_key(jbuf *j, const char *k) {
    jb_str(j, k);
    jb_putc(j, ':');
}

void jb_int(jbuf *j, int64_t v) {
    char tmp[32];
    snprintf(tmp, sizeof tmp, "%lld", (long long)v);
    jb_raw(j, tmp);
}

void jb_uint(jbuf *j, uint64_t v) {
    char tmp[32];
    snprintf(tmp, sizeof tmp, "%llu", (unsigned long long)v);
    jb_raw(j, tmp);
}

void jb_double(jbuf *j, double v) {
    char tmp[64];
    snprintf(tmp, sizeof tmp, "%.17g", v);
    jb_raw(j, tmp);
}

void jb_bool(jbuf *j, int v) { jb_raw(j, v ? "true" : "false"); }

/* ---------------------------------------------------------------------
 * Minimal JSON field extraction for the flat command objects this server
 * reads (docs/northstar/spec_factory/transport/command.schema.json). Every
 * command frame is a single flat object -- no nesting except the top-level
 * "features" array -- so a plain key search is sufficient and avoids
 * pulling in a general JSON parser this build does not link.
 * --------------------------------------------------------------------- */

const char *find_key(const char *json, const char *key) {
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

int get_str(const char *json, const char *key, char *out, size_t cap) {
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

int get_i64(const char *json, const char *key, int64_t *out) {
    const char *p = find_key(json, key);
    if (!p) return 0;
    char *end;
    long long v = strtoll(p, &end, 10);
    if (end == p) return 0;
    *out = (int64_t)v;
    return 1;
}

int get_f64(const char *json, const char *key, double *out) {
    const char *p = find_key(json, key);
    if (!p) return 0;
    char *end;
    double v = strtod(p, &end);
    if (end == p) return 0;
    *out = v;
    return 1;
}

int get_bool(const char *json, const char *key, int *out) {
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

int get_int_array(const char *json, const char *key, int *out, int max) {
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

om_world *W = NULL;
uint64_t g_tick = 0;
int g_roster_types = 0;
uint32_t g_n_regions = 0;
uint64_t g_tactical_tick = 0;
int g_net_full_next = 0;
uint32_t g_n_placed_structures = 0;

static int32_t *prev_owner = NULL;
static double *prev_mil = NULL, *prev_econ = NULL, *prev_ten = NULL;
static double *prev_pop = NULL, *prev_stab = NULL, *prev_cap = NULL;

static uint8_t faction_seen[OM_MAX_FACTIONS];
static double prev_budget[OM_MAX_FACTIONS];
static double prev_tech[OM_MAX_FACTIONS];

#define LOG_MAX 8192

void realloc_regions(uint32_t n) {
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

void capture_baseline(void) {
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

void write_ack(const char *name) {
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

void write_error(const char *name, const char *reason) {
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

void write_snapshot(void) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "snapshot");
    jb_putc(&j, ',');
    jb_key(&j, "tick");
    jb_uint(&j, g_tick);
    jb_putc(&j, ',');
    jb_key(&j, "chapter");
    jb_uint(&j, om_chapter_get_number(W));
    jb_putc(&j, ',');
    jb_key(&j, "commander");
    jb_uint(&j, om_campaign_commander(W));
    jb_putc(&j, ',');
    jb_key(&j, "lineage");
    jb_uint(&j, om_campaign_lineage(W));
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
    jb_putc(&j, ',');
    /* T1-14: additive key; real value from om_player_faction after set_seed.
     * -1 if no player faction is configured (should not occur in a generated
     * world, but guard matches the hello-frame contract). */
    jb_key(&j, "player_faction");
    jb_int(&j, om_player_faction(W));

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
 * session command frames: mission, debrief, chronicle, tactical, saves
 * (docs/architecture.md, "C transport v1", "session commands"). See the
 * file-header comment for every field this file cannot fill from the
 * current C API.
 * --------------------------------------------------------------------- */

static void write_mission(uint32_t archetype, uint32_t region, uint64_t deadline_ticks, int quiet_world) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "mission");
    jb_putc(&j, ',');
    jb_key(&j, "archetype");
    jb_uint(&j, archetype);
    jb_putc(&j, ',');
    jb_key(&j, "region");
    jb_uint(&j, region);
    jb_putc(&j, ',');
    jb_key(&j, "deadline_ticks");
    jb_uint(&j, deadline_ticks);
    jb_putc(&j, ',');

    jb_key(&j, "objectives");
    jb_putc(&j, '[');
    {
        static om_objective_spec obuf[64];
        uint32_t n = om_mission_get_objectives(W, obuf, 64);
        if (n > 64) n = 64;
        for (uint32_t k = 0; k < n; k++) {
            if (k > 0) jb_putc(&j, ',');
            const om_objective_spec *o = &obuf[k];
            jb_putc(&j, '{');
            jb_key(&j, "i");
            jb_uint(&j, o->id);
            jb_putc(&j, ',');
            jb_key(&j, "kind");
            jb_uint(&j, o->kind);
            jb_putc(&j, ',');
            jb_key(&j, "node");
            jb_int(&j, om_objective_get_node(W, k));
            jb_putc(&j, ',');
            jb_key(&j, "primary");
            jb_bool(&j, o->is_primary);
            jb_putc(&j, ',');
            jb_key(&j, "radius");
            jb_double(&j, om_objective_get_radius(W, k));
            jb_putc(&j, ',');
            jb_key(&j, "progress");
            jb_double(&j, o->completion);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    int32_t counts[6] = {0}, tiers[6] = {0};
    for (uint32_t u = 0, nu = om_mission_get_force_count(W); u < nu; u++) {
        int32_t ty = 0, ti = 0;
        if (!om_mission_get_force_unit(W, u, &ty, &ti) || ty < 0 || ty > 5) continue;
        counts[ty]++;
        if (ti > tiers[ty]) tiers[ty] = ti;
    }
    jb_key(&j, "force");
    jb_raw(&j, "{\"types\":[");
    for (int t = 0; t < 6; t++) {
        if (t) jb_putc(&j, ',');
        jb_int(&j, counts[t]);
    }
    jb_raw(&j, "],\"tiers\":[");
    for (int t = 0; t < 6; t++) {
        if (t) jb_putc(&j, ',');
        jb_int(&j, tiers[t]);
    }
    jb_raw(&j, "]},");

    om_briefing b;
    memset(&b, 0, sizeof b);
    om_mission_assemble_briefing(W, &b);
    jb_key(&j, "briefing");
    jb_putc(&j, '{');
    jb_key(&j, "situation");
    jb_str(&j, b.has_situation ? b.situation_text : "");
    jb_putc(&j, ',');
    jb_key(&j, "objective");
    jb_str(&j, b.has_objective ? b.objective_text : "");
    jb_putc(&j, ',');
    jb_key(&j, "assets");
    jb_str(&j, b.has_assets ? b.assets_text : "");
    jb_raw(&j, "},");

    jb_key(&j, "parity");
    jb_double(&j, om_mission_get_player_parity(W, om_player_faction(W)));
    jb_putc(&j, ',');
    jb_key(&j, "commander_unit");
    jb_uint(&j, om_mission_get_commander_unit(W));
    jb_putc(&j, ',');
    jb_key(&j, "quiet_world");
    jb_bool(&j, quiet_world);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

static void write_debrief(void) {
    om_debrief d;
    memset(&d, 0, sizeof d);
    om_mission_get_debrief(W, &d);

    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "debrief");
    jb_putc(&j, ',');
    jb_key(&j, "band");
    jb_int(&j, d.band);
    jb_putc(&j, ',');
    jb_key(&j, "achieved");
    jb_double(&j, d.objective_score);
    jb_putc(&j, ',');
    jb_key(&j, "brought_home");
    jb_double(&j, d.retention);
    jb_putc(&j, ',');
    double mil = 0.0, eco = 0.0, ten = 0.0, pop = 0.0;
    om_mission_get_region_delta(W, &mil, &eco, &ten, &pop);
    jb_key(&j, "region_delta");
    jb_putc(&j, '{');
    jb_key(&j, "military"); jb_double(&j, mil); jb_putc(&j, ',');
    jb_key(&j, "economy");  jb_double(&j, eco); jb_putc(&j, ',');
    jb_key(&j, "tension");  jb_double(&j, ten); jb_putc(&j, ',');
    jb_key(&j, "population"); jb_double(&j, pop);
    jb_putc(&j, '}');
    if (d.band != OM_PIPE_MISSION_BAND_REFUSAL) {
        jb_putc(&j, ',');
        jb_key(&j, "commander_fate");
        jb_int(&j, d.commander_fate);
    }
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

static void write_chronicle(uint64_t from_tick, uint64_t to_tick) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "chronicle");
    jb_putc(&j, ',');
    jb_key(&j, "jump");
    jb_putc(&j, '{');
    jb_key(&j, "from_tick");
    jb_uint(&j, from_tick);
    jb_putc(&j, ',');
    jb_key(&j, "to_tick");
    jb_uint(&j, to_tick);
    jb_putc(&j, ',');
    jb_key(&j, "chapter_end_reason");
    jb_int(&j, om_chapter_last_end_reason(W));
    jb_putc(&j, '}');
    jb_putc(&j, ',');

    jb_key(&j, "entries");
    jb_putc(&j, '[');
    {
        uint32_t n = om_chronicle_entry_count(W);
        int wrote = 0;
        for (uint32_t i = 0; i < n; i++) {
            om_chronicle_cluster c;
            memset(&c, 0, sizeof c);
            if (!om_chronicle_get_cluster(W, i, &c)) continue;
            om_chronicle_entry ent;
            memset(&ent, 0, sizeof ent);
            int32_t frags[3] = { -1, -1, -1 };
            int32_t faction_ref = -1;
            if (om_chronicle_entry_get(W, i, &ent)) {
                faction_ref = ent.faction_ref;
                frags[0] = ent.fragment_ids[0];
                frags[1] = ent.fragment_ids[1];
                frags[2] = ent.fragment_ids[2];
            }
            /* B8-9: clusters with no event ticks (start_tick==end_tick==0;
             * all REGIONAL/LINEAGE/CONSEQUENCE are pushed 0,0 by chronicle.c)
             * take the jump window so the client can place them on the timeline. */
            uint64_t tick_lo = (c.start_tick == 0 && c.end_tick == 0) ? from_tick : c.start_tick;
            uint64_t tick_hi = (c.start_tick == 0 && c.end_tick == 0) ? to_tick   : c.end_tick;
            if (wrote) jb_putc(&j, ',');
            wrote = 1;
            jb_putc(&j, '{');
            jb_key(&j, "id");
            jb_uint(&j, i);
            jb_putc(&j, ',');
            jb_key(&j, "start_tick");
            jb_uint(&j, tick_lo);
            jb_putc(&j, ',');
            jb_key(&j, "end_tick");
            jb_uint(&j, tick_hi);
            jb_putc(&j, ',');
            jb_key(&j, "category");
            jb_uint(&j, c.category);
            jb_putc(&j, ',');
            jb_key(&j, "cluster_type");
            jb_uint(&j, c.type);
            jb_putc(&j, ',');
            jb_key(&j, "refs");
            jb_putc(&j, '{');
            jb_key(&j, "regions");
            jb_putc(&j, '[');
            jb_uint(&j, c.region);
            jb_putc(&j, ']');
            jb_putc(&j, ',');
            jb_key(&j, "factions");
            jb_putc(&j, '[');
            if (faction_ref >= 0) jb_int(&j, faction_ref);
            jb_putc(&j, ']');
            jb_putc(&j, '}');
            jb_putc(&j, ',');
            jb_key(&j, "fragment");
            jb_int(&j, frags[0]);
            jb_putc(&j, ',');
            jb_key(&j, "fragment_ids");
            jb_putc(&j, '[');
            jb_int(&j, frags[0]); jb_putc(&j, ',');
            jb_int(&j, frags[1]); jb_putc(&j, ',');
            jb_int(&j, frags[2]);
            jb_putc(&j, ']');
            jb_putc(&j, ',');
            jb_key(&j, "significance");
            jb_double(&j, c.peak_score);
            jb_putc(&j, ',');
            for (int f = 0; f < 2; f++) {
                jb_key(&j, f ? "expanded_text" : "text");
                jb_str(&j, f ? ent.expanded_text : ent.base_text);
                jb_putc(&j, ',');
                jb_key(&j, f ? "expanded_mentions" : "mentions");
                jb_putc(&j, '[');
                uint32_t nm = om_chronicle_mention_count(W, i, f);
                for (uint32_t k = 0; k < nm; k++) {
                    om_chronicle_mention m;
                    if (!om_chronicle_mention_get(W, i, f, k, &m)) break;
                    if (k) jb_putc(&j, ',');
                    jb_raw(&j, "{\"start\":"); jb_uint(&j, m.start);
                    jb_raw(&j, ",\"len\":"); jb_uint(&j, m.len);
                    jb_raw(&j, ",\"kind\":"); jb_str(&j, m.kind == OM_CHRON_MENTION_FACTION ? "faction" : "region");
                    jb_raw(&j, ",\"id\":"); jb_int(&j, m.id);
                    jb_putc(&j, '}');
                }
                jb_putc(&j, ']');
                if (!f) jb_putc(&j, ',');
            }
            jb_putc(&j, '}');
        }
    }
    jb_putc(&j, ']');
    /* G-C3 (A48 item 13, A59): replay timeline and keyframes, omitted when no jump built a timeline (e.g. after load). */
    om_chronicle_generate_map_keyframes(W);
    uint32_t n_snap = om_time_jump_ownership_snapshot_count(W);
    uint32_t n_reg = om_region_count(W);
    int32_t *owners = n_snap ? malloc((size_t)(n_reg ? n_reg : 1) * sizeof *owners) : NULL;
    if (owners) {
        jb_raw(&j, ",\"ownership\":{\"stride\":");
        jb_uint(&j, OM_OWNERSHIP_TIMELINE_STRIDE);
        jb_raw(&j, ",\"from_tick\":");
        jb_uint(&j, from_tick);
        jb_raw(&j, ",\"n_regions\":");
        jb_uint(&j, n_reg);
        jb_raw(&j, ",\"snapshots\":[");
        for (uint32_t k = 0; k < n_snap; k++) {
            if (k) jb_putc(&j, ',');
            jb_putc(&j, '[');
            uint32_t got = om_time_jump_get_ownership_snapshot(W, k, owners, n_reg);
            for (uint32_t r = 0; r < got; r++) {
                if (r) jb_putc(&j, ',');
                jb_int(&j, owners[r]);
            }
            jb_putc(&j, ']');
        }
        jb_raw(&j, "]},\"keyframes\":[");
        uint32_t n_kf = om_chronicle_keyframe_count(W);
        for (uint32_t i = 0; i < n_kf; i++) {
            uint64_t t = 0;
            if (!om_chronicle_get_keyframe(W, i, &t)) continue;
            if (i) jb_putc(&j, ',');
            jb_uint(&j, t);
        }
        jb_putc(&j, ']');
        free(owners);
    }
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
    /* R-056-04: a NEW campaign opens with a jump of [20, 50] ticks before
     * anything else happens; a world set_seed is building only to be
     * overwritten by a following `load` (autoload/c_bridge.gd's load()) is
     * not a new campaign and passes new_campaign:false to skip the wasted
     * jump. Default true: set_seed always meant "start fresh" until now,
     * and every other production caller (a real new campaign) wants it.
     * See also: csrc/generational.c om_campaign_start -- the jump itself. */
    int new_campaign = 1;
    get_bool(json, "new_campaign", &new_campaign);

    if (W) om_world_free(W);
    W = om_world_new((uint32_t)n_regions, (uint64_t)seed);
    g_tick = 0;
    g_n_placed_structures = 0;
    for (int i = 0; i < nf; i++) om_world_set_feature(W, (om_feature)feats[i], 1);
    om_world_generate(W);
    om_events_load_launch(W);
    if (!om_world_generated(W)) {
        write_error("set_seed", "generation failed");
        return;
    }
    /* om_mission_archetype_count/om_mission_select_candidate (both used by
     * handle_mission_start's R-080-03 fallback below) read st->library_loaded,
     * which nothing else in production code ever sets; without this they
     * silently act as if there were 0 archetypes. Dependency of the R-080-03
     * fallback, not new scope: a pure in-memory table fill, no side effects
     * beyond om_mission_state (csrc/mission.c om_mission_load_launch_library). */
    om_mission_load_launch_library(W);
    if (new_campaign) om_campaign_start(W, 1);
    g_tick = om_world_strategic_tick(W);
    realloc_regions(om_region_count(W));
    capture_baseline();
    /* Deviation from docs/architecture.md: no frame at all on success, not even an ack. */
}

static void handle_step(const char *json) {
    if (!W) {
        write_error("step", "no world");
        return;
    }
    if (om_chapter_mission_realtime(W)) {
        /* R-055-02: the strategic sim is stopped for a mission's whole
         * duration. */
        write_error("step", "mission running");
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
    if (om_chapter_mission_realtime(W)) {
        /* R-055-02: the strategic sim is stopped for a mission's whole
         * duration. */
        write_error("run_to", "mission running");
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

#define PIPE_SPACE_FIELD_LAYERS 5
#define PIPE_SPACE_FIELD_CELLS 57600u /* 240 x 240 */
#define PIPE_SPACE_FIELD_POLY_PTS 64u

/* K-d: {"type":"space_field", masks packed 8 cells per byte LSB first (1 blocked), polys [[layer,kind,[x,y,...]]]};
 * docs/architecture.md "space_field_dump". Without a field: error "no space field" (terrain_dump's form). */
static void handle_space_field_dump(void) {
    if (!W || !om_space_field_present(W)) {
        write_error("space_field_dump", "no space field");
        return;
    }
    uint8_t *cells = malloc(PIPE_SPACE_FIELD_CELLS);
    uint8_t *packed = malloc(PIPE_SPACE_FIELD_CELLS / 8);
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"space_field\",\"cells_w\":240,\"cells_h\":240,\"layers\":5,\"masks\":[");
    for (uint32_t k = 0; k < PIPE_SPACE_FIELD_LAYERS; k++) {
        om_space_field_get_mask(W, k, cells, PIPE_SPACE_FIELD_CELLS);
        memset(packed, 0, PIPE_SPACE_FIELD_CELLS / 8);
        for (uint32_t i = 0; i < PIPE_SPACE_FIELD_CELLS; i++)
            if (cells[i]) packed[i >> 3] = (uint8_t)(packed[i >> 3] | (1u << (i & 7)));
        if (k) jb_putc(&j, ',');
        hex_put(&j, packed, PIPE_SPACE_FIELD_CELLS / 8);
    }
    jb_raw(&j, "],\"polys\":[");
    uint32_t np = om_space_field_poly_count(W);
    for (uint32_t i = 0; i < np; i++) {
        double xy[2 * PIPE_SPACE_FIELD_POLY_PTS];
        uint32_t layer = 0, kind = 0;
        uint32_t n = om_space_field_poly_get(W, i, &layer, &kind, xy, PIPE_SPACE_FIELD_POLY_PTS);
        if (i) jb_putc(&j, ',');
        jb_raw(&j, "[");
        jb_uint(&j, layer);
        jb_putc(&j, ',');
        jb_uint(&j, kind);
        jb_raw(&j, ",[");
        for (uint32_t m = 0; m < 2 * n; m++) {
            if (m) jb_putc(&j, ',');
            jb_double(&j, xy[m]);
        }
        jb_raw(&j, "]]");
    }
    jb_raw(&j, "]}");
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
    free(cells);
    free(packed);
}

static void handle_mission_start(const char *json) {
    if (!W) {
        write_error("mission_start", "no world");
        return;
    }
    int64_t faction = 0;
    { int ff = 0; get_bool(json, "fog_filter", &ff); g_fog_filter = ff; }
    get_i64(json, "faction", &faction);
    int64_t era_kind = 0;
    get_i64(json, "era_kind", &era_kind);
    if (era_kind != 0 && era_kind != 1) {
        write_error("mission_start", "bad era_kind");
        return;
    }
    int mk[64];
    int mk_n = 0;
    const char *mk_p = find_key(json, "movement_kinds");
    if (mk_p) {
        const char *close = *mk_p == '[' ? strchr(mk_p, ']') : NULL;
        const char *inner = close ? memchr(mk_p + 1, '[', (size_t)(close - mk_p - 1)) : NULL;
        if (!close || inner) {
            write_error("mission_start", "bad movement_kinds");
            return;
        }
        mk_n = get_int_array(json, "movement_kinds", mk, 64);
        int mk_ok = mk_n % 2 == 0;
        for (int i = 0; mk_ok && i < mk_n; i += 2)
            mk_ok = mk[i] >= 0 && (mk[i + 1] == 0 || mk[i + 1] == 1);
        if (!mk_ok) {
            write_error("mission_start", "bad movement_kinds");
            return;
        }
    }

    int owns_region = 0;
    for (uint32_t ri = 0; ri < om_region_count(W) && !owns_region; ri++)
        owns_region = om_region_owner(W, ri) == om_player_faction(W);
    if (!owns_region) {
        write_error("mission_start", "player owns no region");
        return;
    }

    /* om_mission_start itself does not start anything (see the file-header
     * comment); the real region/archetype/objective wiring is composed here
     * from the lower-level mission.c/fog.c API. */
    (void)om_mission_start(W, (int32_t)faction);
    for (uint32_t ri = 0; ri < om_region_count(W); ri++) om_mission_refresh_context(W, (int32_t)ri);
    int32_t drawn = om_mission_generator_chosen_archetype(W);
    /* A3/Q-072-01: an empty pool retries after another 20-tick jump, up to
     * five times, then falls back to Defensive Stand (R-072-07/08). */
    for (int retry = 0; drawn < 0 && retry < 5; retry++) {
        om_time_jump_report report;
        memset(&report, 0, sizeof report);
        if (om_time_jump_run(W, 20, &report) != 0) break;
        g_tick = report.end_tick;
        capture_baseline();
        for (uint32_t ri = 0; ri < om_region_count(W); ri++) om_mission_refresh_context(W, (int32_t)ri);
        drawn = om_mission_generator_chosen_archetype(W);
    }
    uint32_t region = 0, archetype = 0, fb_enemy_ok = 0;
    int32_t fb_enemy = -1;
    int have_mission = 0, quiet_world = 0;
    if (drawn < 0) {
        region = om_mission_fallback_region(W);
        fb_enemy = om_mission_fallback_enemy(W, region);
        fb_enemy_ok = fb_enemy >= 0;
    }
    if (fb_enemy_ok) {
        have_mission = 1;
        quiet_world = 1;
    } else if (drawn >= 0) {
        region = om_mission_generator_chosen_region(W);
        archetype = (uint32_t)drawn;
        have_mission = 1;
    } else {
        /* R-080-03: the trigger-scored pool found nothing (an early-campaign
         * tick, or an unlucky seed). Never silently fall back to region 0 /
         * archetype 0 -- region 0 may be unowned or disconnected from the
         * player, which composes a mission with zero units. Mark every
         * archetype viable (there is no trigger-scored preference to defer
         * to here) and let om_mission_select_candidate (csrc/mission.c)
         * guarantee a pick, then use the player's own first owned region
         * instead of a raw index. */
        for (uint32_t a = 0; a < om_mission_archetype_count(W); a++)
            om_mission_set_candidate_viable(W, a, 1);
        archetype = om_mission_select_candidate(W);
        int32_t player = om_player_faction(W);
        uint32_t n_regions = om_region_count(W);
        for (uint32_t i = 0; i < n_regions; i++) {
            if (om_region_owner(W, i) == player) {
                region = i;
                have_mission = 1;
                break;
            }
        }
    }
    if (have_mission) {
        g_roster_types = mk_n / 2;
        for (int i = 0; i + 1 < mk_n; i += 2) (void)om_roster_set_movement_kind(W, mk[i], mk[i + 1]);
        om_set_era_kind(W, (int)era_kind);
        if (quiet_world)
            om_mission_setup_fallback(W, region, fb_enemy);
        else
            om_mission_setup(W, region, archetype, 0);
        /* Never compose a zero-unit mission silently: some archetypes'
         * enemy-power formula (csrc/mission.c om_mission_compute_enemy_power,
         * OM_MISSION_ARCH_DEFENSIVE_STAND/MULTI_FRONT_DEFENSE/INTERCEPTION)
         * reads a committed-attack-budget field that no production code
         * populates yet (om_mission_set_conflict_context has no caller
         * outside mission.c itself) -- a separate, pre-existing gap, not
         * this fix's bug; report it, do not fix it here. Detect it instead
         * of sending an empty mission. */
        if (om_mission_get_deployed_force_count(W) == 0 || om_mission_get_enemy_power(W) <= 0.0)
            have_mission = 0;
    }
    if (!have_mission) {
        /* Whatever came out of the trigger-scored pool or the R-080-03
         * fallback above composed with no real force on one side. Scan
         * every archetype against every player-owned region for one that
         * actually produces units on both sides before giving up -- bounded
         * (archetype count x region count), only reached on the already-rare
         * path above. */
        int32_t player = om_player_faction(W);
        uint32_t n_regions = om_region_count(W);
        uint32_t n_arch = om_mission_archetype_count(W);
        for (uint32_t a = 0; a < n_arch && !have_mission; a++) {
            for (uint32_t i = 0; i < n_regions; i++) {
                if (om_region_owner(W, i) != player) continue;
                om_mission_setup(W, i, a, 0);
                if (om_mission_get_deployed_force_count(W) > 0 && om_mission_get_enemy_power(W) > 0.0) {
                    region = i;
                    archetype = a;
                    have_mission = 1;
                    break;
                }
            }
        }
    }
    if (!have_mission) {
        write_error("mission_start", "no viable mission");
        return;
    }
    if (era_kind == 1 && !om_terrain_present(W)) {
        write_error("mission_start", "terrain generate failed");
        return;
    }
    om_mission_build_objectives(W, archetype);
    g_mission_archetype = archetype;
    /* Recon (E-12 S-092): the mission is not begun here; mission_begin is the
     * player's Begin. */
    om_chapter_set_phase(W, OM_PIPE_CHAPTER_PHASE_MISSION);
    g_tactical_tick = 0;

    write_mission(archetype, region, om_mission_get_time_limit(W), quiet_world);
}

/* R-092-02: during recon (the mission phase holds, mission_begin not yet
 * sent) the mission clock has not started and no unit moves. */
int in_recon(void) {
    return om_chapter_mission_realtime(W) && !om_mission_is_started(W);
}

static void handle_mission_begin(void) {
    if (!W) {
        write_error("mission_begin", "no world");
        return;
    }
    if (!in_recon()) {
        write_error("mission_begin", "not in recon");
        return;
    }
    om_mission_begin(W);
    g_tac.steps = 0;
    g_tac.n_prev = 0;
    g_tac.n_st_prev = 0;
    ev_reset();
    write_tactical(1);
}

int mission_refused(void) {
    return om_mission_get_band(W) == OM_PIPE_MISSION_BAND_REFUSAL;
}

static void handle_mission_refuse(void) {
    if (!W) {
        write_error("mission_refuse", "no world");
        return;
    }
    if (!om_chapter_mission_realtime(W)) {
        write_error("mission_refuse", "no mission");
        return;
    }
    if (!in_recon()) {
        write_error("mission_refuse", "already begun");
        return;
    }
    om_mission_resolve_refusal(W, om_mission_last_region(W));
    write_debrief();
    om_chapter_set_phase(W, OM_PIPE_CHAPTER_PHASE_BRIEFING);
    write_snapshot();
}

static void handle_mission_end(const char *json) {
    if (!W) {
        write_error("mission_end", "no world");
        return;
    }
    if (mission_refused()) {
        write_error("mission_end", "no mission");
        return;
    }
    const char *rp = find_key(json, "retention");
    if (rp) {
#ifdef OM_DEBUG_INJECT
        double retention = 0.0;
        if (!get_f64(json, "retention", &retention) || !(retention >= 0.0 && retention <= 1.0)) {
            write_error("mission_end", "bad retention");
            return;
        }
        uint32_t n = om_unit_count(W);
        for (uint32_t id = 1; id <= n; id++) {
            if (om_unit_alive(W, id) && om_unit_get_faction(W, id) == om_player_faction(W))
                om_unit_set_hp(W, id, retention * om_unit_profile_max_hp(W, om_unit_get_unit_type(W, id)));
        }
#else
        write_error("mission_end", "debug build required");
        return;
#endif
    }
    om_mission_end(W);
    write_debrief();
    om_chapter_set_phase(W, OM_PIPE_CHAPTER_PHASE_BRIEFING);
    write_snapshot();
}

static void handle_assign_commander(const char *json) {
    if (!W) {
        write_error("assign_commander", "no world");
        return;
    }
    if (om_mission_has_ended(W) || mission_refused()) {
        write_error("assign_commander", "mission ended");
        return;
    }
    if (!om_chapter_mission_realtime(W)) {
        write_error("assign_commander", "mission not started");
        return;
    }
    int64_t id = 0;
    if (!get_i64(json, "unit_id", &id)) {
        write_error("assign_commander", "missing unit_id");
        return;
    }
    uint32_t cur = om_mission_get_commander_unit(W);
    if (cur && !om_unit_alive(W, cur)) {
        write_error("assign_commander", "commander dead");
        return;
    }
    uint32_t uid = (id > 0 && id <= (int64_t)om_unit_count(W)) ? (uint32_t)id : 0;
    int in_force = uid && om_unit_get_faction(W, uid) == om_player_faction(W);
    if (!in_force) {
        write_error("assign_commander", "unit not in force");
        return;
    }
    if (!om_unit_alive(W, uid)) {
        write_error("assign_commander", "unit dead");
        return;
    }
    int rc = om_mission_assign_commander(W, uid);
    if (rc) {
        write_error("assign_commander", rc == 2 ? "commander dead" : "unit not in force");
        return;
    }
    write_ack("assign_commander");
}

static void handle_tactical_step(const char *json) {
    if (!W) {
        write_error("tactical_step", "no world");
        return;
    }
    if (in_recon()) {
        write_error("tactical_step", "not begun");
        return;
    }
    if (mission_refused()) {
        write_error("tactical_step", "no mission");
        return;
    }
    int64_t n = 1;
    get_i64(json, "n", &n);
    int want_full = 0;
    get_bool(json, "full", &want_full);
    uint64_t before = g_tac.steps;
    /* K-d1 (FINDING-delta-death-unit): an n == 0 full request steps nothing, so it keeps the previous call's
     * fired flags (state bit 1) and events; resetting here dropped bit 1 and made the client's delta-built view
     * differ from the server's full frame. See also tests/transport/test_pipe_tactical_delta_frame.py
     * test_kd1_nonstepping_full_request_keeps_state_bit_1 */
    if (n != 0) ev_reset();
    for (int64_t i = 0; i < n; i++) {
        om_tactical_step(W);
        g_tactical_tick++;
        g_tac.steps++;
        ev_collect_step();
    }
    ev_collect_abilities();
    if (n < 0) return;
    write_tactical(want_full || n == 0 || g_tac.steps / OM_PIPE_FULL_PERIOD > before / OM_PIPE_FULL_PERIOD);
}

static void handle_jump(const char *json) {
    if (!W) {
        write_error("jump", "no world");
        return;
    }
    int64_t ticks = 0;
    if (!get_i64(json, "ticks", &ticks)) {
        write_error("jump", "missing ticks");
        return;
    }
    om_time_jump_report report;
    memset(&report, 0, sizeof report);
    if (om_time_jump_run(W, (uint32_t)ticks, &report) != 0) {
        /* a mission is running (R-055-02: a jump cannot start or silently
         * continue while one is). */
        write_error("jump", "mission running");
        return;
    }
    g_tick = report.end_tick;
    /* Many ticks passed without streaming a delta per tick; reset the diff
     * baseline so the next step/run_to's delta is relative to post-jump
     * state, not pre-jump state. */
    capture_baseline();
    write_chronicle(report.start_tick, report.end_tick);
    write_snapshot();
}

static void handle_command(const char *json) {
    if (!W) {
        write_error("command", "no world");
        return;
    }
    if (in_recon()) {
        write_error("command", "not begun");
        return;
    }
    char verb[32] = {0};
    if (!get_str(json, "verb", verb, sizeof verb)) {
        write_error("command", "missing verb");
        return;
    }
    int units_i[OM_MAX_UNITS];
    int n_units = get_int_array(json, "units", units_i, OM_MAX_UNITS);
    uint32_t unit_ids[OM_MAX_UNITS];
    for (int i = 0; i < n_units; i++) unit_ids[i] = (uint32_t)units_i[i];

    int ret;
    if (!strcmp(verb, "move")) {
        double x = 0.0, y = 0.0;
        get_f64(json, "x", &x);
        get_f64(json, "y", &y);
        /* R-095-01: group_move caps all units at the slowest member's speed
         * and assigns formation slots.  om_command_move is the per-unit
         * primitive; the pipe always issues a group order for move commands
         * so the client's multi-unit selection behaves like the scale test. */
        ret = (om_command_group_move(W, unit_ids, (uint32_t)n_units, x, y) != 0) ? 0 : 1;
    } else if (!strcmp(verb, "attack_move")) {
        double x = 0.0, y = 0.0;
        get_f64(json, "x", &x);
        get_f64(json, "y", &y);
        ret = om_command_attack_move(W, unit_ids, (uint32_t)n_units, x, y);
    } else if (!strcmp(verb, "attack_target")) {
        int64_t target = -1;
        get_i64(json, "target", &target);
        ret = om_command_attack_target(W, unit_ids, (uint32_t)n_units, (uint32_t)target);
    } else if (!strcmp(verb, "activate_ability")) {
        double x = 0.0, y = 0.0;
        get_f64(json, "x", &x);
        get_f64(json, "y", &y);
        ret = om_command_activate_ability(W, unit_ids, (uint32_t)n_units, x, y);
    } else if (!strcmp(verb, "set_layer")) {
        int64_t layer = -1;
        get_i64(json, "layer", &layer);
        ret = layer < 0 ? 1 : om_command_set_layer(W, unit_ids, (uint32_t)n_units, (uint32_t)layer) != 0;
    } else if (!strcmp(verb, "ping")) {
        int64_t layer = -1;
        double x = 0.0, y = 0.0;
        get_i64(json, "layer", &layer);
        get_f64(json, "x", &x);
        get_f64(json, "y", &y);
        ret = (n_units < 1 || layer < 0) ? 1 : om_command_ping(W, unit_ids[0], (uint32_t)layer, x, y) != 0;
    } else if (!strcmp(verb, "place")) {
        double x = 0.0, y = 0.0;
        int64_t building = -1;
        ret = (n_units != 0 || !get_f64(json, "x", &x) || !get_f64(json, "y", &y) ||
               !get_i64(json, "building", &building) || building < 0 || building > INT32_MAX)
                  ? 1
                  : om_economy_place(W, (int32_t)building, x, y) != 0;
    } else if (!strcmp(verb, "hold")) {
        /* No om_command_hold symbol; only om_unit_order_hold_node(w, unit_id,
         * node_id), which needs a node this command frame doesn't carry.
         * Reported, not implemented. */
        write_error("command", "hold not supported: no om_command_hold symbol");
        return;
    } else {
        write_error("command", "unknown verb");
        return;
    }
    if (ret != 0) {
        write_error("command", "command failed");
        return;
    }
    write_ack("command");
}

static void handle_list_saves(const char *json) {
    char dir[1024];
    if (!get_str(json, "dir", dir, sizeof dir)) {
        write_error("list_saves", "missing dir");
        return;
    }
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "saves");
    jb_putc(&j, ',');
    jb_key(&j, "slots");
    jb_putc(&j, '[');

    DIR *d = opendir(dir);
    int wrote = 0;
    if (d) {
        enum { SLOT_NAME_MAX = 256 };
        char (*names)[SLOT_NAME_MAX] = NULL;
        size_t n_names = 0, cap_names = 0;
        struct dirent *ent;
        while ((ent = readdir(d)) != NULL) {
            size_t nlen = strlen(ent->d_name);
            if (nlen < 6 || nlen >= SLOT_NAME_MAX || strcmp(ent->d_name + nlen - 5, ".json") != 0) continue;
            if (n_names == cap_names) {
                cap_names = cap_names ? cap_names * 2 : 16;
                char (*grown)[SLOT_NAME_MAX] = realloc(names, cap_names * sizeof *names);
                if (!grown) break;
                names = grown;
            }
            memcpy(names[n_names++], ent->d_name, nlen + 1);
        }
        closedir(d);
        for (size_t a = 1; a < n_names; a++) {
            char tmp[SLOT_NAME_MAX];
            memcpy(tmp, names[a], SLOT_NAME_MAX);
            size_t b = a;
            while (b > 0 && strcmp(names[b - 1], tmp) > 0) {
                memcpy(names[b], names[b - 1], SLOT_NAME_MAX);
                b--;
            }
            memcpy(names[b], tmp, SLOT_NAME_MAX);
        }
        for (size_t ni = 0; ni < n_names; ni++) {
            const char *name = names[ni];
            size_t nlen = strlen(name);

            char full[2048];
            snprintf(full, sizeof full, "%s/%s", dir, name);
            FILE *f = fopen(full, "rb");
            if (!f) continue;
            fseek(f, 0, SEEK_END);
            long sz = ftell(f);
            fseek(f, 0, SEEK_SET);
            if (sz <= 0) {
                fclose(f);
                continue;
            }
            char *sbuf = malloc((size_t)sz + 1);
            size_t got = fread(sbuf, 1, (size_t)sz, f);
            fclose(f);
            sbuf[got] = '\0';

            int64_t tick = 0, chapter = 0, phase = 0, seed = 0, format_version = 0;
            get_i64(sbuf, "tick", &tick);
            get_i64(sbuf, "chapter", &chapter);
            get_i64(sbuf, "phase", &phase);
            get_i64(sbuf, "seed", &seed);
            get_i64(sbuf, "format_version", &format_version);
            free(sbuf);

            char slot_path[2048];
            snprintf(slot_path, sizeof slot_path, "%s/%.*s", dir, (int)(nlen - 5), name);

            if (wrote) jb_putc(&j, ',');
            wrote = 1;
            jb_putc(&j, '{');
            jb_key(&j, "path");
            jb_str(&j, slot_path);
            jb_putc(&j, ',');
            jb_key(&j, "tick");
            jb_int(&j, tick);
            jb_putc(&j, ',');
            jb_key(&j, "chapter");
            jb_int(&j, chapter);
            jb_putc(&j, ',');
            jb_key(&j, "phase");
            jb_int(&j, phase);
            jb_putc(&j, ',');
            jb_key(&j, "seed");
            jb_int(&j, seed);
            jb_putc(&j, ',');
            jb_key(&j, "format_version");
            jb_int(&j, format_version);
            jb_putc(&j, '}');
        }
        free(names);
    }
    jb_raw(&j, "]}");
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
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

static void handle_objective_complete(const char *json) {
#ifdef OM_DEBUG_INJECT
    if (!W) {
        write_error("objective_complete", "no world");
        return;
    }
    int64_t objective = 0;
    get_i64(json, "objective", &objective);
    double completion = 1.0;
    get_f64(json, "completion", &completion);
    om_mission_set_objective_completion(W, (uint32_t)objective, completion);
    write_ack("objective_complete");
#else
    (void)json;
    write_error("objective_complete", "debug build required");
#endif
}

#ifdef OM_DEBUG_INJECT
static void handle_place_structure(const char *json) {
    if (!W) {
        write_error("place_structure", "no world");
        return;
    }
    if (g_n_placed_structures >= 64) {
        write_error("place_structure", "structure limit");
        return;
    }
    int64_t kind = -1;
    if (!get_i64(json, "kind", &kind)) {
        write_error("place_structure", "missing kind");
        return;
    }
    if (kind < 0 || kind > 5) {
        write_error("place_structure", "kind out of range");
        return;
    }
    int64_t owner = INT64_MIN;
    if (!get_i64(json, "owner", &owner)) {
        write_error("place_structure", "missing owner");
        return;
    }
    double x = 0.0, y = 0.0;
    get_f64(json, "x", &x);
    get_f64(json, "y", &y);
    uint32_t slot = g_n_placed_structures++;
    om_structure_init(W, slot, (uint32_t)kind, om_unit_power((uint32_t)kind));
    om_structure_set_owner(W, slot, (int32_t)owner);
    om_structure_set_position(W, slot, x, y);
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "ok");
    jb_putc(&j, ',');
    jb_key(&j, "structure");
    jb_uint(&j, (uint64_t)slot);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}
#endif

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

    char sidecar[1032];
    snprintf(sidecar, sizeof sidecar, "%s.json", path);
    FILE *sf = fopen(sidecar, "wb");
    if (sf) {
        jbuf sj;
        jb_init(&sj);
        jb_putc(&sj, '{');
        jb_key(&sj, "tick");
        jb_uint(&sj, g_tick);
        jb_putc(&sj, ',');
        jb_key(&sj, "chapter");
        jb_uint(&sj, om_chapter_get_number(W));
        jb_putc(&sj, ',');
        jb_key(&sj, "phase");
        jb_int(&sj, om_chapter_current_phase(W));
        jb_putc(&sj, ',');
        jb_key(&sj, "seed");
        jb_uint(&sj, om_world_seed(W));
        jb_putc(&sj, ',');
        jb_key(&sj, "n_regions");
        jb_uint(&sj, g_n_regions);
        jb_putc(&sj, ',');
        jb_key(&sj, "format_version");
        jb_uint(&sj, OM_PIPE_SAVE_FORMAT_VERSION);
        jb_putc(&sj, '}');
        fwrite(sj.buf, 1, sj.len, sf);
        fclose(sf);
        jb_free(&sj);
    }
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
    int rc = om_load_state_read(W, buf, (uint32_t)sz);
    free(buf);
    if (rc != 0) {
        /* R-111-03: the world is left untouched. om_load_state_read
         * validates before it applies and returns nonzero without mutating
         * W when validation fails, so no restore is needed here. Its return
         * doesn't distinguish a version mismatch from a corrupt buffer
         * (csrc/save.c); "corrupt" covers both, see the file-header
         * comment. */
        write_error("load", "corrupt");
        return;
    }
    g_tick = om_world_strategic_tick(W);
    g_n_regions = om_region_count(W);
    realloc_regions(g_n_regions);
    capture_baseline();
    write_snapshot();
}



int main(void) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
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
    jb_putc(&hello, ',');
    /* HDR3: additive field. -1 at hello time (no world yet); the client uses
     * om_player_faction() via ctypes after set_seed to get the live value.
     * See docs/architecture.md "hello frame". */
    jb_key(&hello, "player_faction");
    jb_int(&hello, -1);
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
                if (om_chapter_mission_realtime(W) && om_mission_is_started(W)) {
                    ev_reset();
                    write_tactical(1);
                }
            }
        } else if (!strcmp(name, "set_seed")) {
            handle_set_seed(buf);
        } else if (!strcmp(name, "set_feature")) {
            handle_set_feature(buf);
        } else if (!strcmp(name, "inject")) {
            handle_inject(buf);
        } else if (!strcmp(name, "objective_complete")) {
            handle_objective_complete(buf);
#ifdef OM_DEBUG_INJECT
        } else if (!strcmp(name, "place_structure")) {
            handle_place_structure(buf);
#endif
        } else if (!strcmp(name, "save")) {
            handle_save(buf);
        } else if (!strcmp(name, "load")) {
            handle_load(buf);
        } else if (!strcmp(name, "mission_start")) {
            handle_mission_start(buf);
        } else if (!strcmp(name, "mission_begin")) {
            handle_mission_begin();
        } else if (!strcmp(name, "mission_refuse")) {
            handle_mission_refuse();
        } else if (!strcmp(name, "mission_end")) {
            handle_mission_end(buf);
        } else if (!strcmp(name, "assign_commander")) {
            handle_assign_commander(buf);
        } else if (!strcmp(name, "jump")) {
            handle_jump(buf);
        } else if (!strcmp(name, "tactical_step")) {
            handle_tactical_step(buf);
        } else if (!strcmp(name, "command")) {
            handle_command(buf);
        } else if (!strcmp(name, "net_reset")) {
            handle_net_reset();
        } else if (!strcmp(name, "net_submit")) {
            handle_net_submit(buf);
        } else if (!strcmp(name, "net_step")) {
            handle_net_step(buf);
        } else if (!strcmp(name, "net_checksum")) {
            handle_net_checksum();
        } else if (!strcmp(name, "net_log_dump")) {
            handle_net_log_dump();
        } else if (!strcmp(name, "net_log_load")) {
            handle_net_log_load(buf);
        } else if (!strcmp(name, "terrain_generate")) {
            handle_terrain_generate(buf);
        } else if (!strcmp(name, "terrain_dump")) {
            handle_terrain_dump();
        } else if (!strcmp(name, "lots_dump")) {
            handle_lots_dump();
        } else if (!strcmp(name, "space_field_dump")) {
            handle_space_field_dump();
        } else if (!strcmp(name, "terrain_probe")) {
            handle_terrain_probe(buf);
        } else if (!strcmp(name, "net_state_get")) {
            handle_net_state_get();
        } else if (!strcmp(name, "net_state_put")) {
            handle_net_state_put(buf);
        } else if (!strcmp(name, "net_state_diff")) {
            handle_net_state_diff(buf);
        } else if (!strcmp(name, "list_saves")) {
            handle_list_saves(buf);
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
