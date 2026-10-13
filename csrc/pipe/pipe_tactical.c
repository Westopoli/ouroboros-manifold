#include "pipe_internal.h"

uint32_t g_mission_archetype = 0;

pipe_tac_state g_tac;

/* VG K-h: mission_start {fog_filter}; stored per mission by handle_mission_start. */
int g_fog_filter = 0;

/* Sight circles (x, y, radius) of the local faction's units in the frame being written, for structure visibility. */
typedef struct {
    double x, y, r;
} sight_circle;
static sight_circle *g_sight;
static uint32_t g_n_sight, g_cap_sight;

static int struct_in_sight(double x, double y) {
    for (uint32_t i = 0; i < g_n_sight; i++) {
        double dx = x - g_sight[i].x, dy = y - g_sight[i].y;
        if (dx * dx + dy * dy <= g_sight[i].r * g_sight[i].r) return 1;
    }
    return 0;
}

/* An event id is shown if the unit is in this frame's unit list or was in the previous one (kill and leave-sight frames). */
static int unit_shown(int64_t id) {
    return id >= 0 && (uint64_t)id < g_tac.cap && g_tac.by_id[id].seen == g_tac.serial;
}

static int event_shown(int32_t kind, uint32_t a, int32_t b) {
    if (kind == 3) return a < g_tac.st_cap && g_tac.st_by_id[a].in && g_tac.st_by_id[a].seen == g_tac.serial;
    if (unit_shown(a)) return 1;
    return (kind == 0 || kind == 2) && unit_shown(b);
}

/* VG K-a events: the fire, kill and capture events of the sim's per-step ring
 * and the ability events of the call, accumulated over the n steps of one
 * tactical_step call (docs/architecture.md, tactical frame `events`). */
#define OM_PIPE_EVENT_CAP 512
#define OM_PIPE_ABILITY_READ 256
static struct {
    int32_t kind;
    uint32_t a;
    int32_t b;
    int64_t tick;
} g_ev[OM_PIPE_EVENT_CAP];
static uint32_t g_ev_n, g_ev_dropped;
static uint8_t g_fired[OM_MAX_UNITS + 1];

void ev_reset(void) {
    g_ev_n = 0;
    g_ev_dropped = 0;
    memset(g_fired, 0, sizeof g_fired);
}

static void ev_push(int32_t kind, uint32_t a, int32_t b, int64_t tick) {
    if (kind == 0 && a <= OM_MAX_UNITS) g_fired[a] = 1;
    if (g_ev_n >= OM_PIPE_EVENT_CAP) {
        g_ev_dropped++;
        return;
    }
    g_ev[g_ev_n].kind = kind;
    g_ev[g_ev_n].a = a;
    g_ev[g_ev_n].b = b;
    g_ev[g_ev_n].tick = tick;
    g_ev_n++;
}

/* The sim's tactical tick and this file's g_tactical_tick can differ by a constant. */
static int64_t sim_tick_offset(void) {
    return (int64_t)om_tactical_tick(W) - (int64_t)g_tactical_tick;
}

/* Ability events come from om_tick_read_ability_events (kind 1 of the ring is skipped). */
void ev_collect_step(void) {
    int64_t off = sim_tick_offset();
    uint32_t n = om_tactical_event_count(W);
    for (uint32_t i = 0; i < n; i++) {
        int32_t kind = 0, b = 0;
        uint32_t a = 0;
        uint64_t tick = 0;
        if (om_tactical_event_get_at(W, i, &kind, &a, &b, &tick) != 0 || kind == 1) continue;
        ev_push(kind, a, b, (int64_t)tick - off);
    }
}

void ev_collect_abilities(void) {
    om_ability_event ab[OM_PIPE_ABILITY_READ];
    int64_t off = sim_tick_offset();
    uint32_t n = om_tick_read_ability_events(W, ab, OM_PIPE_ABILITY_READ);
    for (uint32_t i = 0; i < n; i++) ev_push(1, ab[i].unit_id, ab[i].ability_id, (int64_t)ab[i].tick - off);
}

/* Section 2 `cover.class`: 0 small (< 150 wu), 1 medium (< 400), 2 huge. */
static int cover_class(double r) {
    return r < 150.0 ? 0 : r < 400.0 ? 1 : 2;
}

/* Section 2 `profiles.acd_max`: the cooldown the ability of each of the six unit types sets
 * (csrc/om_constants.h OM_ABILITY_*_COOLDOWN_TICKS; type order of csrc/unit.c OM_UT_*). */
static const double PROFILE_ACD_MAX[6] = {
    OM_ABILITY_SURGE_COOLDOWN_TICKS, OM_ABILITY_INTERCEPT_COOLDOWN_TICKS, OM_ABILITY_BRACE_COOLDOWN_TICKS,
    OM_ABILITY_RALLY_COOLDOWN_TICKS, OM_ABILITY_BARRAGE_COOLDOWN_TICKS,   OM_ABILITY_FORTIFY_COOLDOWN_TICKS};

/* Section 2 `structures` (full) / `structures_changed` + `structures_removed` (delta); writes a trailing comma. */
static void write_tactical_structures(jbuf *j, int full) {
    uint32_t n = om_structure_count(W);
    uint32_t *ids = malloc(sizeof(uint32_t) * (n ? n : 1));
    uint32_t n_ids = 0, max_id = 0;
    for (uint32_t i = 0; i < n; i++) {
        uint32_t id = om_structure_get_at(W, i);
        if (id == UINT32_MAX || om_structure_is_destroyed(W, id)) continue;
        if (g_fog_filter && om_structure_get_owner(W, id) != om_player_faction(W)) {
            om_vec2 sp;
            memset(&sp, 0, sizeof sp);
            om_structure_get_position(W, id, &sp);
            if (!struct_in_sight(sp.x, sp.y)) continue;
        }
        ids[n_ids++] = id;
        if (id > max_id) max_id = id;
    }
    if (max_id >= g_tac.st_cap) {
        uint32_t cap = max_id + 64;
        g_tac.st_by_id = realloc(g_tac.st_by_id, sizeof(tac_struct) * cap);
        memset(g_tac.st_by_id + g_tac.st_cap, 0, sizeof(tac_struct) * (cap - g_tac.st_cap));
        g_tac.st_cap = cap;
    }
    uint64_t serial = g_tac.serial;
    jb_key(j, full ? "structures" : "structures_changed");
    jb_putc(j, '[');
    int wrote = 0;
    for (uint32_t k = 0; k < n_ids; k++) {
        uint32_t id = ids[k];
        tac_struct cur;
        memset(&cur, 0, sizeof cur);
        om_vec2 pos;
        memset(&pos, 0, sizeof pos);
        om_structure_hud hud;
        memset(&hud, 0, sizeof hud);
        om_structure_get_position(W, id, &pos);
        om_structure_get_hud_data(W, id, &hud);
        cur.in = 1;
        cur.type = (int32_t)om_structure_get_unit_type(W, id);
        cur.owner = om_structure_get_owner(W, id);
        cur.x = pos.x;
        cur.y = pos.y;
        cur.hp = om_structure_get_hp(W, id);
        {
            double cp = om_structure_get_capture_progress(W, id) * 1000.0 + 0.5;
            cur.cap = cp < 0.0 ? 0 : cp > 1000.0 ? 1000 : (int32_t)cp;
        }
        cur.next_type = (int32_t)hud.next_unit_type;
        cur.period = (int64_t)om_structure_production_interval_ticks(om_unit_power(hud.next_unit_type));
        {
            int64_t left = cur.period - (int64_t)(hud.timer_progress * (double)cur.period + 0.5);
            cur.nst = (int64_t)g_tactical_tick + (left > 0 ? left : 0);
        }
        cur.seen = serial;
        tac_struct *old = &g_tac.st_by_id[id];
        int is_new = full || !old->in;
        int d_type = is_new || old->type != cur.type, d_owner = is_new || old->owner != cur.owner;
        int d_pos = is_new || old->x != cur.x || old->y != cur.y, d_hp = is_new || old->hp != cur.hp;
        int d_cap = is_new || old->cap != cur.cap, d_nst = is_new || old->nst != cur.nst;
        int d_nt = is_new || old->next_type != cur.next_type, d_per = is_new || old->period != cur.period;
        *old = cur;
        if (!(d_type || d_owner || d_pos || d_hp || d_cap || d_nst || d_nt || d_per)) continue;
        if (wrote) jb_putc(j, ',');
        wrote = 1;
        jb_raw(j, "{\"id\":");
        jb_uint(j, id);
        if (d_type) { jb_raw(j, ",\"type\":"); jb_int(j, cur.type); }
        if (d_owner) { jb_raw(j, ",\"owner\":"); jb_int(j, cur.owner); }
        if (d_pos) {
            jb_raw(j, ",\"x\":"); jb_double(j, cur.x);
            jb_raw(j, ",\"y\":"); jb_double(j, cur.y);
        }
        if (d_hp) { jb_raw(j, ",\"hp\":"); jb_double(j, cur.hp); }
        if (is_new) jb_raw(j, ",\"stage\":0");
        if (d_cap) { jb_raw(j, ",\"cap\":"); jb_int(j, cur.cap); }
        if (d_nst) { jb_raw(j, ",\"nst\":"); jb_int(j, cur.nst); }
        if (d_nt) { jb_raw(j, ",\"next_type\":"); jb_int(j, cur.next_type); }
        if (d_per) { jb_raw(j, ",\"period\":"); jb_int(j, cur.period); }
        jb_putc(j, '}');
    }
    jb_raw(j, "],");
    if (!full) {
        jb_key(j, "structures_removed");
        jb_putc(j, '[');
        wrote = 0;
    }
    for (uint32_t k = 0; k < g_tac.n_st_prev; k++) {
        uint32_t id = g_tac.st_prev[k];
        if (g_tac.st_by_id[id].seen == serial) continue;
        g_tac.st_by_id[id].in = 0;
        if (g_fog_filter) g_tac.st_by_id[id].seen = serial;
        if (full) continue;
        if (wrote) jb_putc(j, ',');
        wrote = 1;
        jb_uint(j, id);
    }
    if (!full) jb_raw(j, "],");
    if (n_ids > g_tac.cap_st_prev) {
        g_tac.st_prev = realloc(g_tac.st_prev, sizeof(uint32_t) * n_ids);
        g_tac.cap_st_prev = n_ids;
    }
    memcpy(g_tac.st_prev, ids, sizeof(uint32_t) * n_ids);
    g_tac.n_st_prev = n_ids;
    free(ids);
}

/* VG K-e: the lot rows in the last tactical frame written, diffed for "lots_changed". */
static om_lot *g_lots_prev;
static uint32_t g_lots_prev_n, g_lots_prev_cap;

void write_lot_row(jbuf *j, const om_lot *l) {
    jb_putc(j, '[');
    jb_uint(j, l->id);
    jb_putc(j, ',');
    jb_double(j, l->x);
    jb_putc(j, ',');
    jb_double(j, l->y);
    jb_putc(j, ',');
    jb_int(j, l->stage);
    jb_putc(j, ',');
    jb_int(j, l->building);
    jb_putc(j, ',');
    jb_int(j, l->owner);
    jb_putc(j, ']');
}

/* VG K-e: delta "lots_changed" or full "strongpoints", then "economy"; each writes a trailing comma. */
static void write_tactical_economy(jbuf *j, int full) {
    if (full) {
        jb_raw(j, "\"strongpoints\":[");
        uint32_t n = om_strongpoint_count(W);
        int wrote = 0;
        for (uint32_t i = 0; i < n; i++) {
            om_strongpoint sp;
            if (om_strongpoint_get_at(W, i, &sp) != 0) continue;
            if (wrote) jb_putc(j, ',');
            wrote = 1;
            jb_raw(j, "{\"id\":");
            jb_uint(j, sp.id);
            jb_raw(j, ",\"x\":");
            jb_double(j, sp.x);
            jb_raw(j, ",\"y\":");
            jb_double(j, sp.y);
            jb_raw(j, ",\"owner\":");
            jb_int(j, sp.owner);
            jb_raw(j, ",\"state\":");
            jb_int(j, sp.state);
            jb_putc(j, '}');
        }
        jb_raw(j, "],");
    }
    uint32_t n = om_lot_count(W);
    if (n > g_lots_prev_cap) {
        free(g_lots_prev);
        g_lots_prev = malloc(sizeof(om_lot) * n);
        g_lots_prev_cap = n;
        g_lots_prev_n = 0;
    }
    om_lot *cur = malloc(sizeof(om_lot) * (n ? n : 1));
    uint32_t nc = 0;
    for (uint32_t i = 0; i < n; i++)
        if (om_lot_get_at(W, i, &cur[nc]) == 0) nc++;
    if (!full) {
        jb_raw(j, "\"lots_changed\":[");
        int wrote = 0;
        for (uint32_t i = 0; i < nc; i++) {
            const om_lot *p = NULL;
            for (uint32_t k = 0; k < g_lots_prev_n; k++)
                if (g_lots_prev[k].id == cur[i].id) {
                    p = &g_lots_prev[k];
                    break;
                }
            if (p && p->stage == cur[i].stage && p->building == cur[i].building && p->owner == cur[i].owner) continue;
            if (wrote) jb_putc(j, ',');
            wrote = 1;
            write_lot_row(j, &cur[i]);
        }
        jb_raw(j, "],");
    } else {
        jb_raw(j, "\"lots\":[");
        for (uint32_t i = 0; i < nc; i++) {
            if (i) jb_putc(j, ',');
            write_lot_row(j, &cur[i]);
        }
        jb_raw(j, "],");
    }
    if (nc) memcpy(g_lots_prev, cur, sizeof(om_lot) * nc);
    g_lots_prev_n = nc;
    free(cur);
    jb_raw(j, "\"economy\":{\"doctrine\":");
    jb_int(j, om_doctrine_get(W));
    jb_raw(j, ",\"resources\":{}},");
}

void write_tactical(int full) {
    jbuf j;
    jb_init(&j);
    jb_putc(&j, '{');
    jb_key(&j, "type");
    jb_str(&j, "tactical");
    jb_putc(&j, ',');
    jb_key(&j, "tick");
    jb_uint(&j, g_tactical_tick);
    jb_putc(&j, ',');

    /* docs/architecture.md "C transport v1", tactical snapshot: true once the
     * sim itself has ended the mission (om_mission_tactical_tick's R-075-07
     * check, or an explicit mission_end), so the client can route to the
     * debrief without waiting for the player to press End Mission. `band`
     * is -1 (OM_MISSION_BAND_UNKNOWN in the C ABI) until then. */
    jb_key(&j, "mission_over");
    jb_bool(&j, om_mission_has_ended(W));
    jb_putc(&j, ',');
    jb_key(&j, "band");
    jb_int(&j, om_mission_get_band(W));
    jb_putc(&j, ',');

    jb_key(&j, "full");
    jb_bool(&j, full);
    jb_putc(&j, ',');
    jb_key(&j, "objectives");
    jb_putc(&j, '[');
    {
        om_objective_spec obuf[64];
        uint32_t n = om_mission_get_objectives(W, obuf, 64);
        if (n > 64) n = 64;
        for (uint32_t k = 0; k < n; k++) {
            if (k > 0) jb_putc(&j, ',');
            jb_putc(&j, '{');
            jb_key(&j, "i");
            jb_uint(&j, obuf[k].id);
            jb_putc(&j, ',');
            jb_key(&j, "progress");
            jb_double(&j, obuf[k].completion);
            jb_putc(&j, ',');
            jb_key(&j, "done");
            jb_int(&j, om_objective_get_done(W, k));
            jb_putc(&j, '}');
        }
    }
    jb_raw(&j, "],");

    if (full) {
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
                jb_putc(&j, ',');
                jb_key(&j, "class");
                jb_int(&j, cover_class(r));
                jb_putc(&j, '}');
            }
        }
        jb_raw(&j, "],");
        jb_key(&j, "obstacles");
        jb_putc(&j, '[');
        {
            uint32_t n = om_map_obstacle_count(W);
            int first = 1;
            for (uint32_t i = 0; i < n; i++) {
                double x = 0.0, y = 0.0, r = 0.0;
                if (om_map_get_obstacle_at(W, i, &x, &y, &r) != 0) continue;
                if (!first) jb_putc(&j, ',');
                first = 0;
                jb_raw(&j, "{\"x\":");
                jb_double(&j, x);
                jb_raw(&j, ",\"y\":");
                jb_double(&j, y);
                jb_raw(&j, ",\"r\":");
                jb_double(&j, r);
                jb_putc(&j, '}');
            }
        }
        jb_putc(&j, ']');
        jb_putc(&j, '}');
        jb_putc(&j, ',');
        jb_key(&j, "profiles");
        jb_putc(&j, '[');
        for (int t = 0; t < 6; t++) {
            if (t) jb_putc(&j, ',');
            jb_raw(&j, "{\"type\":");
            jb_int(&j, t);
            jb_raw(&j, ",\"max_hp\":");
            jb_double(&j, om_unit_profile_max_hp(W, t));
            jb_raw(&j, ",\"range\":");
            jb_double(&j, om_unit_profile_attack_range(W, t));
            jb_raw(&j, ",\"interval\":");
            jb_double(&j, om_unit_profile_attack_interval(W, t));
            jb_raw(&j, ",\"sensor\":");
            jb_double(&j, om_unit_profile_sensor_radius(W, t));
            jb_raw(&j, ",\"ability\":");
            jb_int(&j, t);
            jb_raw(&j, ",\"acd_max\":");
            jb_double(&j, PROFILE_ACD_MAX[t]);
            jb_raw(&j, ",\"aoe\":");
            jb_double(&j, om_unit_profile_aoe_radius(W, t));
            jb_putc(&j, '}');
        }
        jb_raw(&j, "],");

    }

    /* Live units only (a dead unit leaves full frames and shows once in the
     * next delta's units_removed). A dead unit keeps its slot, so the scan
     * stops once every occupied slot (om_unit_count) has been seen, not at
     * OM_PIPE_UNIT_SCAN_MAX; with the old bound a single death made every
     * frame walk a million empty slots. */
    uint32_t count = om_unit_count(W);
    uint32_t *ids = malloc(sizeof(uint32_t) * (count ? count : 1));
    uint32_t n_ids = 0;
    uint32_t max_id = 0;
    uint32_t occupied = 0;
    for (uint32_t i = 0; occupied < count && i < OM_PIPE_UNIT_SCAN_MAX; i++) {
        uint32_t id = om_unit_id_at(W, i);
        if (!id) continue;
        occupied++;
        if (!om_unit_alive(W, id)) continue;
        if (g_fog_filter && !om_player_can_see_unit(W, om_player_faction(W), id)) continue;
        ids[n_ids++] = id;
        if (id > max_id) max_id = id;
    }
    if (max_id >= g_tac.cap) {
        uint32_t cap = max_id + 1024;
        g_tac.by_id = realloc(g_tac.by_id, sizeof(tac_unit) * cap);
        memset(g_tac.by_id + g_tac.cap, 0, sizeof(tac_unit) * (cap - g_tac.cap));
        g_tac.cap = cap;
    }
    g_tac.serial++;
    int32_t player = om_player_faction(W);
    g_n_sight = 0;
    jb_key(&j, full ? "units" : "units_changed");
    jb_putc(&j, '[');
    int wrote = 0;
    for (uint32_t k = 0; k < n_ids; k++) {
        tac_unit cur;
        memset(&cur, 0, sizeof cur);
        cur.id = ids[k];
        om_unit_get_pos(W, cur.id, &cur.x, &cur.y);
        cur.faction = om_unit_get_faction(W, cur.id);
        cur.type = om_unit_get_unit_type(W, cur.id);
        cur.hp = om_unit_get_hp(W, cur.id);
        cur.layer = om_unit_get_layer(W, cur.id);
        cur.facing = om_unit_get_facing(W, cur.id);
        cur.target = om_unit_target(W, cur.id);
        tac_unit *old = &g_tac.by_id[cur.id];
        cur.tier = (int32_t)om_faction_unit_tier(W, cur.faction);
        if (cur.id <= OM_MAX_UNITS && g_fired[cur.id]) cur.state |= 1;
        if (om_unit_is_braced(W, cur.id)) cur.state |= 2;
        {
            uint32_t tgt = om_unit_get_target_layer(W, cur.id);
            if (tgt != UINT32_MAX && (int32_t)tgt != cur.layer) {
                cur.state |= 4;
                cur.tl = (int32_t)tgt;
                if (old->id && (old->state & 4) && old->tl == cur.tl) {
                    cur.ld = old->ld;
                } else {
                    double left = (1.0 - om_unit_transition_progress(W, cur.id)) *
                                  om_unit_profile_layer_transition_time(W, cur.type) * (double)OM_TACTICAL_TICK_RATE;
                    cur.ld = (int64_t)g_tactical_tick + (int64_t)(left + 0.999999);
                    if (cur.ld <= (int64_t)g_tactical_tick) cur.ld = (int64_t)g_tactical_tick + 1;
                }
            }
        }
        {
            double cd = om_unit_ability_cooldown(W, cur.id);
            if (cd > 0.0) cur.acd = (int64_t)g_tactical_tick + (int64_t)(cd + 0.999999);
        }
        if (cur.faction == player) {
            double sr = om_fog_get_drawn_sensor_circle_radius(W, cur.id);
            cur.sight = (int32_t)(sr + 0.5);
            if (g_fog_filter) {
                if (g_n_sight >= g_cap_sight) {
                    g_cap_sight = g_cap_sight ? g_cap_sight * 2 : 64;
                    g_sight = realloc(g_sight, sizeof(sight_circle) * g_cap_sight);
                }
                g_sight[g_n_sight].x = cur.x;
                g_sight[g_n_sight].y = cur.y;
                g_sight[g_n_sight].r = sr;
                g_n_sight++;
            }
        }
        int changed = full || !old->id || old->faction != cur.faction || old->type != cur.type ||
                      old->layer != cur.layer || old->target != cur.target || old->x != cur.x ||
                      old->y != cur.y || old->hp != cur.hp || old->facing != cur.facing ||
                      old->tier != cur.tier || old->state != cur.state || old->acd != cur.acd ||
                      old->tl != cur.tl || old->ld != cur.ld || old->sight != cur.sight;
        cur.seen = g_tac.serial;
        *old = cur;
        if (!changed) continue;
        if (wrote) jb_putc(&j, ',');
        wrote = 1;
        jb_putc(&j, '{');
        jb_key(&j, "id");
        jb_uint(&j, cur.id);
        jb_putc(&j, ',');
        jb_key(&j, "faction");
        jb_int(&j, cur.faction);
        jb_putc(&j, ',');
        jb_key(&j, "type");
        jb_int(&j, cur.type);
        jb_putc(&j, ',');
        jb_key(&j, "tier");
        jb_int(&j, cur.tier);
        jb_putc(&j, ',');
        jb_key(&j, "x");
        jb_double(&j, cur.x);
        jb_putc(&j, ',');
        jb_key(&j, "y");
        jb_double(&j, cur.y);
        jb_putc(&j, ',');
        jb_key(&j, "hp");
        jb_double(&j, cur.hp);
        jb_putc(&j, ',');
        jb_key(&j, "layer");
        jb_int(&j, cur.layer);
        jb_putc(&j, ',');
        jb_key(&j, "facing");
        jb_double(&j, cur.facing);
        jb_putc(&j, ',');
        jb_key(&j, "target");
        jb_int(&j, cur.target);
        jb_putc(&j, ',');
        jb_key(&j, "state");
        jb_int(&j, cur.state);
        if (cur.acd) {
            jb_raw(&j, ",\"acd\":");
            jb_int(&j, cur.acd);
        }
        if (cur.state & 4) {
            jb_raw(&j, ",\"tl\":");
            jb_int(&j, cur.tl);
            jb_raw(&j, ",\"ld\":");
            jb_int(&j, cur.ld);
        }
        if (cur.faction == player) {
            jb_raw(&j, ",\"sight\":");
            jb_int(&j, cur.sight);
        }
        jb_putc(&j, '}');
    }
    jb_raw(&j, "],");
    if (!full) {
        jb_key(&j, "units_removed");
        jb_putc(&j, '[');
        wrote = 0;
    }
    for (uint32_t k = 0; k < g_tac.n_prev; k++) {
        uint32_t id = g_tac.prev_ids[k];
        if (g_tac.by_id[id].seen == g_tac.serial) continue;
        g_tac.by_id[id].id = 0;
        if (g_fog_filter) g_tac.by_id[id].seen = g_tac.serial;
        if (full) continue;
        if (wrote) jb_putc(&j, ',');
        wrote = 1;
        jb_uint(&j, id);
    }
    if (!full) jb_raw(&j, "],");
    if (n_ids > g_tac.cap_prev) {
        g_tac.prev_ids = realloc(g_tac.prev_ids, sizeof(uint32_t) * n_ids);
        g_tac.cap_prev = n_ids;
    }
    memcpy(g_tac.prev_ids, ids, sizeof(uint32_t) * n_ids);
    g_tac.n_prev = n_ids;

    write_tactical_structures(&j, full);
    write_tactical_economy(&j, full);

    jb_raw(&j, "\"events\":[");
    int ev_wrote = 0;
    for (uint32_t k = 0; k < g_ev_n; k++) {
        if (g_fog_filter && !event_shown(g_ev[k].kind, g_ev[k].a, g_ev[k].b)) continue;
        if (ev_wrote) jb_putc(&j, ',');
        ev_wrote = 1;
        jb_putc(&j, '[');
        jb_int(&j, g_ev[k].kind);
        jb_putc(&j, ',');
        jb_uint(&j, g_ev[k].a);
        jb_putc(&j, ',');
        jb_int(&j, g_ev[k].b);
        jb_putc(&j, ',');
        jb_int(&j, g_ev[k].tick);
        jb_putc(&j, ']');
    }
    jb_raw(&j, "],");
    if (g_ev_dropped) {
        jb_raw(&j, "\"events_dropped\":");
        jb_uint(&j, g_ev_dropped);
        jb_putc(&j, ',');
    }

    /* visible: the player's faction only, the complete id list each frame. */
    {
        char key[16];
        snprintf(key, sizeof key, "%d", (int)player);
        jb_key(&j, "visible");
        jb_putc(&j, '{');
        jb_key(&j, key);
        jb_putc(&j, '[');
        int first = 1;
        for (uint32_t k = 0; k < n_ids; k++) {
            if (!om_player_can_see_unit(W, player, ids[k])) continue;
            if (!first) jb_putc(&j, ',');
            first = 0;
            jb_uint(&j, ids[k]);
        }
        jb_putc(&j, ']');
        jb_putc(&j, '}');
    }
    jb_putc(&j, '}');
    free(ids);
    write_frame(j.buf, (uint32_t)j.len);
    jb_free(&j);
}
