#include "pipe_internal.h"

/* ---------------------------------------------------------------------
 * Lockstep verbs (docs/architecture.md "Lockstep verbs")
 * --------------------------------------------------------------------- */

void hex_put(jbuf *j, const uint8_t *b, uint32_t n) {
    static const char d[] = "0123456789abcdef";
    jb_putc(j, '"');
    for (uint32_t i = 0; i < n; i++) {
        jb_putc(j, d[b[i] >> 4]);
        jb_putc(j, d[b[i] & 15]);
    }
    jb_putc(j, '"');
}

static int hex_nibble(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

/* Decodes the "hex" string field into a new buffer; NULL on absent or bad. */
static uint8_t *hex_get(const char *json, const char *key, uint32_t *len_out, const char **why) {
    const char *p = find_key(json, key);
    if (!p || *p != '"') {
        *why = "missing field";
        return NULL;
    }
    p++;
    const char *e = strchr(p, '"');
    size_t n = e ? (size_t)(e - p) : 0;
    if (!e || (n & 1)) {
        *why = "bad hex";
        return NULL;
    }
    uint8_t *out = malloc(n / 2 ? n / 2 : 1);
    for (size_t i = 0; i < n / 2; i++) {
        int hi = hex_nibble(p[2 * i]), lo = hex_nibble(p[2 * i + 1]);
        if (hi < 0 || lo < 0) {
            free(out);
            *why = "bad hex";
            return NULL;
        }
        out[i] = (uint8_t)(hi << 4 | lo);
    }
    *len_out = (uint32_t)(n / 2);
    return out;
}

static int net_guard(const char *name, int need_begun) {
    if (!W) {
        write_error(name, "no world");
        return 0;
    }
    if (need_begun) {
        if (in_recon()) {
            write_error(name, "not begun");
            return 0;
        }
        if (mission_refused()) {
            write_error(name, "no mission");
            return 0;
        }
    }
    return 1;
}

static void net_ack_open(jbuf *j, const char *name) {
    jb_init(j);
    jb_putc(j, '{');
    jb_key(j, "type");
    jb_str(j, "net_ack");
    jb_putc(j, ',');
    jb_key(j, "name");
    jb_str(j, name);
    jb_putc(j, ',');
    jb_key(j, "tick");
    jb_uint(j, om_net_tick(W));
}

static void net_ack_checksum(jbuf *j) {
    uint64_t sec[9];
    uint64_t h = om_world_checksum_full(W, sec, 9);
    jb_putc(j, ',');
    jb_key(j, "checksum");
    jb_uint(j, h);
    jb_putc(j, ',');
    jb_key(j, "sections");
    jb_putc(j, '[');
    for (int i = 0; i < 9; i++) {
        if (i) jb_putc(j, ',');
        jb_uint(j, sec[i]);
    }
    jb_putc(j, ']');
}

static void net_ack_names(jbuf *j) {
    jb_putc(j, ',');
    jb_key(j, "names");
    jb_putc(j, '[');
    for (uint32_t i = 0; i < om_checksum_section_count(); i++) {
        if (i) jb_putc(j, ',');
        jb_str(j, om_checksum_section_name(i));
    }
    jb_putc(j, ']');
}

static void net_ack_close(jbuf *j) {
    jb_putc(j, '}');
    write_frame(j->buf, (uint32_t)j->len);
    jb_free(j);
}

void handle_net_reset(void) {
    if (!net_guard("net_reset", 0)) return;
    om_cmd_reset(W);
    g_net_full_next = 1;
    jbuf j;
    net_ack_open(&j, "net_reset");
    net_ack_close(&j);
}

void handle_net_submit(const char *json) {
    if (!net_guard("net_submit", 1)) return;
    int64_t tick, peer, seq, verb;
    if (!get_i64(json, "tick", &tick) || !get_i64(json, "peer", &peer) || !get_i64(json, "seq", &seq) ||
        !get_i64(json, "verb", &verb)) {
        write_error("net_submit", "missing field");
        return;
    }
    om_net_command c;
    memset(&c, 0, sizeof c);
    int64_t arg = 0, layer = 0;
    get_i64(json, "arg", &arg);
    get_i64(json, "layer", &layer);
    get_f64(json, "x", &c.x);
    get_f64(json, "y", &c.y);
    int units_i[OM_MAX_UNITS];
    uint32_t ids[OM_MAX_UNITS];
    int n = get_int_array(json, "units", units_i, OM_MAX_UNITS);
    for (int i = 0; i < n; i++) ids[i] = (uint32_t)units_i[i];
    c.tick = (uint64_t)tick;
    c.seq = (uint32_t)seq;
    c.arg = (uint32_t)arg;
    c.peer = (uint8_t)peer;
    c.verb = (uint8_t)verb;
    c.layer = (uint8_t)layer;
    c.n_units = (uint8_t)n;
    int code = om_cmd_submit(W, &c, ids);
    jbuf j;
    net_ack_open(&j, "net_submit");
    jb_putc(&j, ',');
    jb_key(&j, "code");
    jb_int(&j, code);
    net_ack_close(&j);
}

void handle_net_step(const char *json) {
    if (!net_guard("net_step", 1)) return;
    int64_t n = 1;
    get_i64(json, "n", &n);
    int want = 0;
    get_bool(json, "checksum", &want);
    int want_frame = 0;
    get_bool(json, "frame", &want_frame);
    uint64_t before = g_tac.steps;
    ev_reset();
    for (int64_t i = 0; i < n; i++) {
        om_tactical_step(W);
        g_tactical_tick++;
        g_tac.steps++;
        ev_collect_step();
    }
    ev_collect_abilities(); /* drains the hashed ability buffer, as tactical_step does */
    jbuf j;
    net_ack_open(&j, "net_step");
    if (want || om_net_tick(W) % 10 == 0) net_ack_checksum(&j);
    net_ack_close(&j);
    if (want_frame && n >= 0) {
        int full = g_net_full_next;
        g_net_full_next = 0;
        write_tactical(full || n == 0 || g_tac.steps / OM_PIPE_FULL_PERIOD > before / OM_PIPE_FULL_PERIOD);
    }
}

void handle_net_checksum(void) {
    if (!net_guard("net_checksum", 0)) return;
    jbuf j;
    net_ack_open(&j, "net_checksum");
    net_ack_checksum(&j);
    net_ack_names(&j);
    net_ack_close(&j);
}

void handle_net_log_dump(void) {
    if (!net_guard("net_log_dump", 0)) return;
    uint32_t need = om_cmd_log_size(W);
    uint8_t *buf = malloc(need ? need : 1);
    uint32_t got = om_cmd_log_write(W, buf, need);
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"net_log\",\"name\":\"net_log_dump\",\"hex\":");
    hex_put(&j, buf, got);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
    free(buf);
}

void handle_net_log_load(const char *json) {
    if (!net_guard("net_log_load", 0)) return;
    uint32_t len = 0;
    const char *why = NULL;
    uint8_t *buf = hex_get(json, "hex", &len, &why);
    if (!buf) {
        write_error("net_log_load", why);
        return;
    }
    int code = om_cmd_log_feed(W, buf, len);
    free(buf);
    jbuf j;
    net_ack_open(&j, "net_log_load");
    jb_putc(&j, ',');
    jb_key(&j, "code");
    jb_int(&j, code);
    net_ack_close(&j);
}

void handle_net_state_get(void) {
    if (!net_guard("net_state_get", 0)) return;
    uint32_t need = om_save_state_size(W);
    uint8_t *buf = malloc(need ? need : 1);
    om_save_state_write(W, buf, need);
    jbuf j;
    jb_init(&j);
    jb_raw(&j, "{\"type\":\"net_state\",\"hex\":");
    hex_put(&j, buf, need);
    jb_putc(&j, ',');
    jb_key(&j, "tactical_tick");
    jb_uint(&j, g_tactical_tick);
    jb_putc(&j, ',');
    jb_key(&j, "steps");
    jb_uint(&j, g_tac.steps);
    jb_putc(&j, ',');
    jb_key(&j, "mission_archetype");
    jb_uint(&j, g_mission_archetype);
    jb_putc(&j, ',');
    jb_key(&j, "placed_structures");
    jb_uint(&j, g_n_placed_structures);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
    free(buf);
}

void handle_net_state_put(const char *json) {
    if (!net_guard("net_state_put", 0)) return;
    int64_t tt, steps, arch, placed;
    if (!get_i64(json, "tactical_tick", &tt) || !get_i64(json, "steps", &steps) ||
        !get_i64(json, "mission_archetype", &arch) || !get_i64(json, "placed_structures", &placed)) {
        write_error("net_state_put", "missing field");
        return;
    }
    uint32_t len = 0;
    const char *why = NULL;
    uint8_t *buf = hex_get(json, "hex", &len, &why);
    if (!buf) {
        write_error("net_state_put", why);
        return;
    }
    int rc = om_load_state_read(W, buf, len);
    free(buf);
    if (rc != 0) {
        write_error("net_state_put", "corrupt");
        return;
    }
    g_tactical_tick = (uint64_t)tt;
    g_tac.steps = (uint64_t)steps;
    g_mission_archetype = (uint32_t)arch;
    g_n_placed_structures = (uint32_t)placed;
    g_tick = om_world_strategic_tick(W);
    g_n_regions = om_region_count(W);
    realloc_regions(g_n_regions);
    capture_baseline();
    jbuf j;
    net_ack_open(&j, "net_state_put");
    net_ack_close(&j);
}

void handle_net_state_diff(const char *json) {
    if (!net_guard("net_state_diff", 0)) return;
    uint32_t len = 0;
    const char *why = NULL;
    uint8_t *buf = hex_get(json, "state", &len, &why);
    if (!buf) {
        write_error("net_state_diff", why);
        return;
    }
    om_world *scratch = om_world_new(om_region_count(W), om_world_seed(W));
    for (int f = 0; f <= OM_FEAT_TACTICAL; f++)
        om_world_set_feature(scratch, (om_feature)f, om_world_feature(W, (om_feature)f));
    om_world_generate(scratch);
    om_events_load_launch(scratch);
    om_mission_load_launch_library(scratch);
    om_campaign_start(scratch, 1);
    int rc = om_load_state_read(scratch, buf, len);
    free(buf);
    if (rc != 0) {
        om_world_free(scratch);
        write_error("net_state_diff", "corrupt");
        return;
    }
    uint32_t section = 0, unit = 0;
    int diff = om_checksum_first_diff(W, scratch, &section, &unit);
    om_world_free(scratch);
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "net_ack");
    jb_putc(&j, ',');
    jb_key(&j, "name");
    jb_str(&j, "net_state_diff");
    jb_putc(&j, ',');
    jb_key(&j, "equal");
    jb_raw(&j, diff ? "false" : "true");
    jb_putc(&j, ',');
    jb_key(&j, "section");
    jb_int(&j, diff ? (int64_t)section : -1);
    jb_putc(&j, ',');
    jb_key(&j, "section_name");
    jb_str(&j, diff ? om_checksum_section_name(section) : "");
    jb_putc(&j, ',');
    jb_key(&j, "unit");
    jb_uint(&j, diff ? unit : 0);
    jb_putc(&j, '}');
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}

/* ---------------------------------------------------------------------
 * main
 * --------------------------------------------------------------------- */
