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
 *   - No accessor wires a force composition into a started mission
 *     (om_mission_get_player_units reads st->player_units[], which nothing
 *     in the reachable API sets before mission_start); "force":{"types":
 *     [],"tiers":[]} is always empty.
 *   - om_objective_spec has no "node" or "radius" field (id, kind,
 *     is_primary, weight, completion, is_complete, is_failed only); both
 *     keys are emitted as 0.
 *   - "region_delta" in the debrief frame is from om_mission_get_region_delta
 *     (T1-8 accessor). om_mission_apply_consequences runs inside om_mission_end
 *     when mission_set is true and end_applied is false; the accessor returns
 *     the stored delta. When the accessor returns 0 (no consequence applied)
 *     all four keys are 0.
 *   - om_chronicle_entry has no accessor to read it back by id (only
 *     om_chronicle_entry_count/_is_retained); om_chronicle_get_cluster's
 *     om_chronicle_cluster is used instead (type/category/region/peak_score/
 *     start_tick/end_tick). It has one region, not a regions[] list, no
 *     faction refs, and no fragment id -- "refs.factions" and "fragment"
 *     are always empty/0.
 *   - Every om_map_get_* node/canvas accessor and om_tactical_step itself
 *     are STUBs (csrc/tactical_mapgen.c, csrc/unit.c: E-11 wiring, card
 *     B10/B12 not landed). There is also no enumerator for live tactical
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
 *   - No public getter reads back the chapter number set by
 *     om_chapter_start; the save sidecar's "chapter" is always 0.
 *   - GEN_PHASE_BRIEFING/GEN_PHASE_MISSION are private #defines in
 *     csrc/generational.c, not exported by ouroboros_sim.h; mirrored below
 *     as OM_PIPE_CHAPTER_PHASE_* since om_chapter_set_phase/
 *     om_chapter_mission_realtime take/read the raw int.
 */
#include <dirent.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ouroboros_sim.h"

/* csrc/generational.c GEN_PHASE_BRIEFING / GEN_PHASE_MISSION, not exported
 * by ouroboros_sim.h. See the file-header comment above. */
#define OM_PIPE_CHAPTER_PHASE_BRIEFING 0
#define OM_PIPE_CHAPTER_PHASE_MISSION 2
/* Upper bound on unit slots scanned with om_unit_id_at, and on distinct
 * factions listed in a tactical frame's "visible". */
#define OM_PIPE_UNIT_SCAN_MAX 1000000
#define OM_PIPE_MAX_FACTION_KEYS 32
/* Mirror of OM_MAX_UNITS in unit.c (E-11 10k-unit scale requirement + headroom,
 * unit.c:57).  Not exported from ouroboros_sim.h; mirrored here for the
 * command unit-list buffer in handle_command. */
#define OM_MAX_UNITS 10100

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

static int get_f64(const char *json, const char *key, double *out) {
    const char *p = find_key(json, key);
    if (!p) return 0;
    char *end;
    double v = strtod(p, &end);
    if (end == p) return 0;
    *out = v;
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
static uint64_t g_tactical_tick = 0;

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
 * session command frames: mission, debrief, chronicle, tactical, saves
 * (docs/architecture.md, "C transport v1", "session commands"). See the
 * file-header comment for every field this file cannot fill from the
 * current C API.
 * --------------------------------------------------------------------- */

static void write_mission(uint32_t archetype, uint32_t region, uint64_t deadline_ticks) {
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
            jb_key(&j, "node"); /* no field in om_objective_spec; reported */
            jb_uint(&j, 0);
            jb_putc(&j, ',');
            jb_key(&j, "primary");
            jb_bool(&j, o->is_primary);
            jb_putc(&j, ',');
            jb_key(&j, "radius"); /* no field in om_objective_spec; reported */
            jb_double(&j, 0.0);
            jb_putc(&j, ',');
            jb_key(&j, "progress");
            jb_double(&j, o->completion);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    /* "force": no accessor wires a composition into a started mission; see
     * the file-header comment. Always empty. */
    jb_key(&j, "force");
    jb_raw(&j, "{\"types\":[],\"tiers\":[]}");
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
            if (wrote) jb_putc(&j, ',');
            wrote = 1;
            jb_putc(&j, '{');
            jb_key(&j, "id");
            jb_uint(&j, i);
            jb_putc(&j, ',');
            jb_key(&j, "start_tick");
            jb_uint(&j, c.start_tick);
            jb_putc(&j, ',');
            jb_key(&j, "end_tick");
            jb_uint(&j, c.end_tick);
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
            jb_key(&j, "factions"); /* no faction refs on a cluster; reported */
            jb_raw(&j, "[]");
            jb_putc(&j, '}');
            jb_putc(&j, ',');
            jb_key(&j, "fragment"); /* no fragment id accessor; reported */
            jb_uint(&j, 0);
            jb_putc(&j, ',');
            jb_key(&j, "significance");
            jb_double(&j, c.peak_score);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "]}");
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

static uint32_t g_mission_archetype = 0;

static void write_tactical(void) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "tactical");
    jb_putc(&j, ',');
    jb_key(&j, "tick");
    jb_uint(&j, g_tactical_tick);
    jb_putc(&j, ',');

    jb_key(&j, "map");
    jb_putc(&j, '{');
    jb_key(&j, "canvas");
    jb_double(&j, om_map_get_canvas_base_dimension(om_map_archetype_canvas_category(g_mission_archetype)));
    jb_putc(&j, ',');
    jb_key(&j, "nodes");
    jb_putc(&j, '[');
    {
        uint32_t n = om_map_get_node_count(W);
        for (uint32_t i = 0; i < n; i++) {
            if (i > 0) jb_putc(&j, ',');
            om_vec2 pos;
            memset(&pos, 0, sizeof pos);
            om_map_get_node_pos(W, i, &pos);
            jb_putc(&j, '{');
            jb_key(&j, "i");
            jb_uint(&j, i);
            jb_putc(&j, ',');
            jb_key(&j, "kind");
            jb_int(&j, om_map_get_node_type(W, i));
            jb_putc(&j, ',');
            jb_key(&j, "x");
            jb_double(&j, pos.x);
            jb_putc(&j, ',');
            jb_key(&j, "y");
            jb_double(&j, pos.y);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");
    jb_key(&j, "cover");
    jb_putc(&j, '[');
    {
        uint32_t n = om_map_cover_count(W);
        for (uint32_t i = 0; i < n; i++) {
            double x = 0.0, y = 0.0, r = 0.0, h = 0.0;
            if (!om_map_cover_at(W, i, &x, &y, &r, &h)) continue;
            if (i > 0) jb_putc(&j, ',');
            jb_putc(&j, '{');
            jb_key(&j, "x");
            jb_double(&j, x);
            jb_putc(&j, ',');
            jb_key(&j, "y");
            jb_double(&j, y);
            jb_putc(&j, ',');
            jb_key(&j, "r");
            jb_double(&j, r);
            jb_putc(&j, ',');
            jb_key(&j, "h");
            jb_double(&j, h);
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");
    /* No accessor enumerates obstacles (om_map_add_obstacle only), so the
     * list stays empty; see the file-header comment. */
    jb_key(&j, "obstacles");
    jb_raw(&j, "[]");
    jb_putc(&j, '}');
    jb_putc(&j, ',');

    /* Units: om_unit_id_at scans the unit slots (0 for an unused one), so
     * collect om_unit_count ids. "tier" and "state" have no accessor and are
     * sent as 0. */
    uint32_t count = om_unit_count(W);
    uint32_t *ids = malloc(sizeof(uint32_t) * (count ? count : 1));
    uint32_t n_ids = 0;
    for (uint32_t i = 0; n_ids < count && i < OM_PIPE_UNIT_SCAN_MAX; i++) {
        uint32_t id = om_unit_id_at(W, i);
        if (id) ids[n_ids++] = id;
    }
    jb_key(&j, "units");
    jb_putc(&j, '[');
    for (uint32_t k = 0; k < n_ids; k++) {
        uint32_t id = ids[k];
        double x = 0.0, y = 0.0;
        om_unit_get_pos(W, id, &x, &y);
        if (k > 0) jb_putc(&j, ',');
        jb_putc(&j, '{');
        jb_key(&j, "id");
        jb_uint(&j, id);
        jb_putc(&j, ',');
        jb_key(&j, "faction");
        jb_int(&j, om_unit_get_faction(W, id));
        jb_putc(&j, ',');
        jb_key(&j, "type");
        jb_int(&j, om_unit_get_unit_type(W, id));
        jb_putc(&j, ',');
        jb_key(&j, "tier");
        jb_int(&j, 0);
        jb_putc(&j, ',');
        jb_key(&j, "x");
        jb_double(&j, x);
        jb_putc(&j, ',');
        jb_key(&j, "y");
        jb_double(&j, y);
        jb_putc(&j, ',');
        jb_key(&j, "hp");
        jb_double(&j, om_unit_get_hp(W, id));
        jb_putc(&j, ',');
        jb_key(&j, "layer");
        jb_int(&j, om_unit_get_layer(W, id));
        jb_putc(&j, ',');
        jb_key(&j, "facing");
        jb_double(&j, om_unit_get_facing(W, id));
        jb_putc(&j, ',');
        jb_key(&j, "target");
        jb_int(&j, om_unit_target(W, id));
        jb_putc(&j, ',');
        jb_key(&j, "state");
        jb_int(&j, 0);
        jb_putc(&j, '}');
    }
    jb_raw(&j, "],");

    /* visible[faction]: the unit ids that faction can see, for every faction
     * that has units. */
    jb_key(&j, "visible");
    jb_putc(&j, '{');
    {
        int32_t seen[OM_PIPE_MAX_FACTION_KEYS];
        uint32_t n_seen = 0;
        for (uint32_t k = 0; k < n_ids; k++) {
            int32_t f = om_unit_get_faction(W, ids[k]);
            int known = 0;
            for (uint32_t m = 0; m < n_seen; m++) {
                if (seen[m] == f) known = 1;
            }
            if (!known && n_seen < OM_PIPE_MAX_FACTION_KEYS) seen[n_seen++] = f;
        }
        for (uint32_t a = 1; a < n_seen; a++) {
            int32_t key = seen[a];
            uint32_t b = a;
            while (b > 0 && seen[b - 1] > key) {
                seen[b] = seen[b - 1];
                b--;
            }
            seen[b] = key;
        }
        for (uint32_t m = 0; m < n_seen; m++) {
            if (m > 0) jb_putc(&j, ',');
            char key[16];
            snprintf(key, sizeof key, "%d", (int)seen[m]);
            jb_key(&j, key);
            jb_putc(&j, '[');
            int first = 1;
            for (uint32_t k = 0; k < n_ids; k++) {
                if (!om_player_can_see_unit(W, seen[m], ids[k])) continue;
                if (!first) jb_putc(&j, ',');
                first = 0;
                jb_uint(&j, ids[k]);
            }
            jb_putc(&j, ']');
        }
    }
    jb_putc(&j, '}');
    jb_putc(&j, '}');
    free(ids);
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

static void handle_mission_start(const char *json) {
    if (!W) {
        write_error("mission_start", "no world");
        return;
    }
    int64_t faction = 0;
    get_i64(json, "faction", &faction);

    /* om_mission_start itself does not start anything (see the file-header
     * comment); the real region/archetype/objective wiring is composed here
     * from the lower-level mission.c/fog.c API. */
    (void)om_mission_start(W, (int32_t)faction);
    om_mission_build_candidate_pool(W);
    uint32_t idx = om_mission_select(W);
    static om_mission_candidate pool[256];
    uint32_t n = om_mission_candidates(W, pool, 256);
    uint32_t region = 0, archetype = 0;
    if (idx < n) {
        region = pool[idx].region_idx;
        archetype = pool[idx].archetype;
    }
    om_mission_setup(W, region, archetype, 0);
    om_mission_build_objectives(W, archetype);
    g_mission_archetype = archetype;
    /* Recon (E-12 S-092): the mission is not begun here; mission_begin is the
     * player's Begin. */
    om_chapter_set_phase(W, OM_PIPE_CHAPTER_PHASE_MISSION);
    g_tactical_tick = 0;

    write_mission(archetype, region, om_mission_get_time_limit(W));
}

/* R-092-02: during recon (the mission phase holds, mission_begin not yet
 * sent) the mission clock has not started and no unit moves. */
static int in_recon(void) {
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
    write_tactical();
}

static void handle_mission_end(void) {
    if (!W) {
        write_error("mission_end", "no world");
        return;
    }
    om_mission_end(W);
    write_debrief();
    om_chapter_set_phase(W, OM_PIPE_CHAPTER_PHASE_BRIEFING);
    write_snapshot();
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
    int64_t n = 1;
    get_i64(json, "n", &n);
    for (int64_t i = 0; i < n; i++) {
        om_tactical_step(W);
        g_tactical_tick++;
        write_tactical();
    }
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
        struct dirent *ent;
        while ((ent = readdir(d)) != NULL) {
            size_t nlen = strlen(ent->d_name);
            if (nlen < 6 || strcmp(ent->d_name + nlen - 5, ".json") != 0) continue;

            char full[2048];
            snprintf(full, sizeof full, "%s/%s", dir, ent->d_name);
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
            snprintf(slot_path, sizeof slot_path, "%s/%.*s", dir, (int)(nlen - 5), ent->d_name);

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
        closedir(d);
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
        jb_key(&sj, "chapter"); /* no getter for the chapter number; reported */
        jb_uint(&sj, 0);
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
        jb_uint(&sj, 1);
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
        } else if (!strcmp(name, "mission_start")) {
            handle_mission_start(buf);
        } else if (!strcmp(name, "mission_begin")) {
            handle_mission_begin();
        } else if (!strcmp(name, "mission_end")) {
            handle_mission_end();
        } else if (!strcmp(name, "jump")) {
            handle_jump(buf);
        } else if (!strcmp(name, "tactical_step")) {
            handle_tactical_step(buf);
        } else if (!strcmp(name, "command")) {
            handle_command(buf);
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
