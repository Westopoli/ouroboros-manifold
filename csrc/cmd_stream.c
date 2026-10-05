/* csrc/cmd_stream.c -- lockstep command stream (docs/northstar/plans/2026-10-05-lockstep-backend-spec.md,
 * lane "cmd"; E-19 R-140-02, R-242-01, E-13 R-096-07).
 * Commands are stamped with the tick they begin on and applied at the top of
 * that tactical step, ordered by peer then seq. Every applied command is
 * appended to a byte log that om_cmd_log_feed can reload for replay. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define OM_CMD_MAX_UNITS 70u
#define OM_CMD_PENDING_CAP 256u
#define OM_CMD_LOG_CAP 1048576u
#define OM_CMD_LOG_MAGIC_LEN 4u
#define OM_CMD_LOG_VERSION 1u
#define OM_CMD_LOG_HEADER_LEN 12u
#define OM_CMD_W32 4u
#define OM_CMD_W64 8u
#define OM_CMD_OFF_TICK 0u
#define OM_CMD_OFF_SEQ 8u
#define OM_CMD_OFF_ARG 12u
#define OM_CMD_OFF_X 16u
#define OM_CMD_OFF_Y 24u
#define OM_CMD_OFF_PEER 32u
#define OM_CMD_OFF_VERB 33u
#define OM_CMD_OFF_LAYER 34u
#define OM_CMD_OFF_NUNITS 35u
#define OM_CMD_OFF_IDS 36u
#define OM_CMD_LOG_OFF_VERSION 4u
#define OM_CMD_LOG_OFF_COUNT 8u
#define OM_CMD_ENTRY_FIXED_LEN OM_CMD_OFF_IDS
#define OM_CMD_BYTE_BITS 8u
#define OM_CMD_BYTE_MASK 0xffu
#define OM_CMD_VERB_LAST OM_NET_VERB_ASSIGN_COMMANDER

#define OM_CMD_ERR_LATE 1
#define OM_CMD_ERR_DUPLICATE 2
#define OM_CMD_ERR_MALFORMED 3
#define OM_CMD_ERR_FULL 4

typedef struct {
    uint64_t tick;
    uint32_t pending_n;
    uint32_t log_count;
    uint32_t log_len;
    uint32_t reserved_len;
    om_net_command pending[OM_CMD_PENDING_CAP];
    uint32_t ids[OM_CMD_PENDING_CAP][OM_CMD_MAX_UNITS];
    uint8_t log[OM_CMD_LOG_CAP];
} om_cmd_state;

static const uint8_t k_log_magic[OM_CMD_LOG_MAGIC_LEN] = { 'O', 'M', 'C', 'L' };

static void put_le(uint8_t *p, uint64_t v, uint32_t bytes);

static void log_header(om_cmd_state *st) {
    memcpy(st->log, k_log_magic, OM_CMD_LOG_MAGIC_LEN);
    put_le(st->log + OM_CMD_LOG_OFF_VERSION, OM_CMD_LOG_VERSION, OM_CMD_W32);
    put_le(st->log + OM_CMD_LOG_OFF_COUNT, st->log_count, OM_CMD_W32);
}

static om_cmd_state *cmd_state(om_world *w) {
    if (!w->net_state) {
        om_cmd_state *st = (om_cmd_state *)calloc(1, sizeof *st);
        if (!st) return NULL;
        st->log_len = OM_CMD_LOG_HEADER_LEN;
        st->reserved_len = OM_CMD_LOG_HEADER_LEN;
        log_header(st);
        w->net_state = st;
        w->net_state_free = free;
    }
    return (om_cmd_state *)w->net_state;
}

static uint32_t entry_len(uint32_t n) { return OM_CMD_ENTRY_FIXED_LEN + OM_CMD_W32 * n; }

static void put_le(uint8_t *p, uint64_t v, uint32_t bytes) {
    for (uint32_t i = 0; i < bytes; i++) p[i] = (uint8_t)((v >> (i * OM_CMD_BYTE_BITS)) & OM_CMD_BYTE_MASK);
}

static uint64_t get_le(const uint8_t *p, uint32_t bytes) {
    uint64_t v = 0;
    for (uint32_t i = 0; i < bytes; i++) v |= (uint64_t)p[i] << (i * OM_CMD_BYTE_BITS);
    return v;
}

static uint64_t dbl_bits(double d) { uint64_t u; memcpy(&u, &d, sizeof u); return u; }
static double bits_dbl(uint64_t u) { double d; memcpy(&d, &u, sizeof d); return d; }

static uint32_t pack_entry(uint8_t *p, const om_net_command *c, const uint32_t *ids) {
    put_le(p + OM_CMD_OFF_TICK, c->tick, OM_CMD_W64);
    put_le(p + OM_CMD_OFF_SEQ, c->seq, OM_CMD_W32);
    put_le(p + OM_CMD_OFF_ARG, c->arg, OM_CMD_W32);
    put_le(p + OM_CMD_OFF_X, dbl_bits(c->x), OM_CMD_W64);
    put_le(p + OM_CMD_OFF_Y, dbl_bits(c->y), OM_CMD_W64);
    p[OM_CMD_OFF_PEER] = c->peer; p[OM_CMD_OFF_VERB] = c->verb;
    p[OM_CMD_OFF_LAYER] = c->layer; p[OM_CMD_OFF_NUNITS] = c->n_units;
    for (uint32_t i = 0; i < c->n_units; i++) put_le(p + OM_CMD_OFF_IDS + OM_CMD_W32 * i, ids[i], OM_CMD_W32);
    return entry_len(c->n_units);
}

static void unpack_entry(const uint8_t *p, om_net_command *c, uint32_t *ids) {
    c->tick = get_le(p + OM_CMD_OFF_TICK, OM_CMD_W64);
    c->seq = (uint32_t)get_le(p + OM_CMD_OFF_SEQ, OM_CMD_W32);
    c->arg = (uint32_t)get_le(p + OM_CMD_OFF_ARG, OM_CMD_W32);
    c->x = bits_dbl(get_le(p + OM_CMD_OFF_X, OM_CMD_W64));
    c->y = bits_dbl(get_le(p + OM_CMD_OFF_Y, OM_CMD_W64));
    c->peer = p[OM_CMD_OFF_PEER]; c->verb = p[OM_CMD_OFF_VERB];
    c->layer = p[OM_CMD_OFF_LAYER]; c->n_units = p[OM_CMD_OFF_NUNITS];
    for (uint32_t i = 0; i < c->n_units && ids; i++) ids[i] = (uint32_t)get_le(p + OM_CMD_OFF_IDS + OM_CMD_W32 * i, OM_CMD_W32);
}

static int well_formed(const om_net_command *c, const uint32_t *ids) {
    if (!c) return 0;
    if (c->verb > OM_CMD_VERB_LAST) return 0;
    if (c->n_units == 0 || c->n_units > OM_CMD_MAX_UNITS) return 0;
    return ids != NULL;
}

static int logged(const om_cmd_state *st, uint8_t peer, uint32_t seq) {
    uint32_t off = OM_CMD_LOG_HEADER_LEN;
    for (uint32_t i = 0; i < st->log_count; i++) {
        const uint8_t *p = st->log + off;
        if (p[OM_CMD_OFF_PEER] == peer && (uint32_t)get_le(p + OM_CMD_OFF_SEQ, OM_CMD_W32) == seq) return 1;
        off += entry_len(p[OM_CMD_OFF_NUNITS]);
    }
    return 0;
}

static int pending_has(const om_cmd_state *st, uint8_t peer, uint32_t seq) {
    for (uint32_t i = 0; i < st->pending_n; i++)
        if (st->pending[i].peer == peer && st->pending[i].seq == seq) return 1;
    return 0;
}

/* Pending stays sorted by (tick, peer, seq); keys are unique, so the order is total. */
static int key_before(const om_net_command *a, const om_net_command *b) {
    if (a->tick != b->tick) return a->tick < b->tick;
    if (a->peer != b->peer) return a->peer < b->peer;
    return a->seq < b->seq;
}

static void pending_insert(om_cmd_state *st, const om_net_command *c, const uint32_t *ids) {
    uint32_t at = st->pending_n;
    while (at > 0 && key_before(c, &st->pending[at - 1])) at--;
    for (uint32_t i = st->pending_n; i > at; i--) {
        st->pending[i] = st->pending[i - 1];
        memcpy(st->ids[i], st->ids[i - 1], sizeof st->ids[i]);
    }
    st->pending[at] = *c;
    memcpy(st->ids[at], ids, sizeof(uint32_t) * c->n_units);
    st->pending_n++;
    st->reserved_len += entry_len(c->n_units);
}

int om_cmd_submit(om_world *w, const om_net_command *cmd, const uint32_t *unit_ids) {
    if (!w || !well_formed(cmd, unit_ids)) return OM_CMD_ERR_MALFORMED;
    om_cmd_state *st = cmd_state(w);
    if (!st) return OM_CMD_ERR_FULL;
    if (cmd->tick <= st->tick) return OM_CMD_ERR_LATE;
    if (pending_has(st, cmd->peer, cmd->seq) || logged(st, cmd->peer, cmd->seq)) return OM_CMD_ERR_DUPLICATE;
    if (st->pending_n >= OM_CMD_PENDING_CAP || st->reserved_len + entry_len(cmd->n_units) > OM_CMD_LOG_CAP)
        return OM_CMD_ERR_FULL;
    pending_insert(st, cmd, unit_ids);
    return 0;
}

void om_cmd_reset(om_world *w) {
    if (!w) return;
    om_cmd_state *st = cmd_state(w);
    if (!st) return;
    memset(st, 0, sizeof *st);
    st->log_len = OM_CMD_LOG_HEADER_LEN;
    st->reserved_len = OM_CMD_LOG_HEADER_LEN;
    log_header(st);
}

uint64_t om_net_tick(const om_world *w) {
    return (w && w->net_state) ? ((const om_cmd_state *)w->net_state)->tick : 0;
}

uint32_t om_cmd_pending_count(const om_world *w) {
    return (w && w->net_state) ? ((const om_cmd_state *)w->net_state)->pending_n : 0;
}

uint32_t om_cmd_log_size(const om_world *w) {
    return (w && w->net_state) ? ((const om_cmd_state *)w->net_state)->log_len : OM_CMD_LOG_HEADER_LEN;
}

uint32_t om_cmd_log_write(const om_world *w, uint8_t *out, uint32_t cap) {
    uint32_t n = om_cmd_log_size(w);
    if (!out || cap < n) return 0;
    if (w->net_state) {
        const om_cmd_state *st = (const om_cmd_state *)w->net_state;
        memcpy(out, st->log, n);
    } else {
        memcpy(out, k_log_magic, OM_CMD_LOG_MAGIC_LEN);
        put_le(out + OM_CMD_LOG_OFF_VERSION, OM_CMD_LOG_VERSION, OM_CMD_W32);
        put_le(out + OM_CMD_LOG_OFF_COUNT, 0, OM_CMD_W32);
    }
    return n;
}

int om_cmd_log_feed(om_world *w, const uint8_t *buf, uint32_t len) {
    if (!w || !buf || len < OM_CMD_LOG_HEADER_LEN) return OM_CMD_ERR_MALFORMED;
    if (memcmp(buf, k_log_magic, OM_CMD_LOG_MAGIC_LEN) != 0) return OM_CMD_ERR_MALFORMED;
    if (get_le(buf + OM_CMD_LOG_OFF_VERSION, OM_CMD_W32) != OM_CMD_LOG_VERSION) return OM_CMD_ERR_MALFORMED;
    uint32_t count = (uint32_t)get_le(buf + OM_CMD_LOG_OFF_COUNT, OM_CMD_W32);
    om_cmd_state *st = cmd_state(w);
    if (!st) return OM_CMD_ERR_FULL;
    if (count > OM_CMD_PENDING_CAP - st->pending_n) return OM_CMD_ERR_FULL;
    uint32_t off = OM_CMD_LOG_HEADER_LEN, added = 0;
    for (uint32_t i = 0; i < count; i++) {
        om_net_command c;
        if (len - off < OM_CMD_ENTRY_FIXED_LEN) return OM_CMD_ERR_MALFORMED;
        unpack_entry(buf + off, &c, NULL);
        if (c.verb > OM_CMD_VERB_LAST || c.n_units == 0 || c.n_units > OM_CMD_MAX_UNITS) return OM_CMD_ERR_MALFORMED;
        if (len - off < entry_len(c.n_units)) return OM_CMD_ERR_MALFORMED;
        if (c.tick <= st->tick) return OM_CMD_ERR_LATE;
        if (pending_has(st, c.peer, c.seq) || logged(st, c.peer, c.seq)) return OM_CMD_ERR_DUPLICATE;
        uint32_t off2 = OM_CMD_LOG_HEADER_LEN;
        for (uint32_t j = 0; j < i; j++) {
            const uint8_t *q = buf + off2;
            if (q[OM_CMD_OFF_PEER] == c.peer && (uint32_t)get_le(q + OM_CMD_OFF_SEQ, OM_CMD_W32) == c.seq) return OM_CMD_ERR_DUPLICATE;
            off2 += entry_len(q[OM_CMD_OFF_NUNITS]);
        }
        added += entry_len(c.n_units);
        off += entry_len(c.n_units);
    }
    if (off != len) return OM_CMD_ERR_MALFORMED;
    if (st->reserved_len + added > OM_CMD_LOG_CAP) return OM_CMD_ERR_FULL;
    off = OM_CMD_LOG_HEADER_LEN;
    for (uint32_t i = 0; i < count; i++) {
        om_net_command c;
        uint32_t ids[OM_CMD_MAX_UNITS];
        unpack_entry(buf + off, &c, ids);
        pending_insert(st, &c, ids);
        off += entry_len(c.n_units);
    }
    return 0;
}

static void apply_one(om_world *w, const om_net_command *c, const uint32_t *ids) {
    uint32_t n = c->n_units;
    switch ((om_net_verb)c->verb) {
    case OM_NET_VERB_MOVE: om_command_group_move(w, ids, n, c->x, c->y); break;
    case OM_NET_VERB_ATTACK_MOVE: om_command_attack_move(w, ids, n, c->x, c->y); break;
    case OM_NET_VERB_ATTACK_TARGET: om_command_attack_target(w, ids, n, c->arg); break;
    case OM_NET_VERB_ACTIVATE_ABILITY: om_command_activate_ability(w, ids, n, c->x, c->y); break;
    case OM_NET_VERB_SET_LAYER: om_command_set_layer(w, ids, n, c->layer); break;
    case OM_NET_VERB_SET_EMISSION: om_command_set_emission(w, ids, n, (om_emission)c->arg); break;
    case OM_NET_VERB_PING: om_command_ping(w, ids[0], c->layer, c->x, c->y); break;
    case OM_NET_VERB_GUARD: om_command_guard(w, ids, n); break;
    case OM_NET_VERB_ASSIGN_COMMANDER: om_mission_assign_commander(w, ids[0]); break;
    }
}

void om_cmd_apply_tick(om_world *w) {
    om_cmd_state *st = cmd_state(w);
    if (!st) return;
    st->tick++;
    uint32_t done = 0;
    while (done < st->pending_n && st->pending[done].tick == st->tick) {
        apply_one(w, &st->pending[done], st->ids[done]);
        st->log_len += pack_entry(st->log + st->log_len, &st->pending[done], st->ids[done]);
        st->log_count++;
        done++;
    }
    if (done) {
        for (uint32_t i = done; i < st->pending_n; i++) {
            st->pending[i - done] = st->pending[i];
            memcpy(st->ids[i - done], st->ids[i], sizeof st->ids[i]);
        }
        st->pending_n -= done;
    }
    log_header(st);
}
