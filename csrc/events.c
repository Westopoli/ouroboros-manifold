/* csrc/events.c — E-04 event library, triggers, queue resolution (E-04 build cards).
 * 26-template launch library, threshold/probability triggers (ALG-32..34),
 * pending-queue resolver (ALG-35..37: condition, exclusion, probability,
 * spawns), 9 OM_BUG_* positive controls under OM_DEBUG_INJECT. Per-world
 * event state has no home in om_world/om_region (parent-owned); lives in a
 * private pointer-keyed slot table below — see leaf-01.ASSUMPTIONS.md and
 * questions/leaf-01-Q1..4.md for the escalations this file works around
 * (missing OM_FIELD_CEILING, no struct field for this state, and a class
 * of acceptance tests that stay red against a rule-faithful
 * implementation). Draws go through om_rng_draw (csrc/sim.c); region.c
 * seeds the world. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include <stddef.h>
#include <string.h>
#include <math.h>

#define OM_EVT_FIELD_CEILING 100.0

#define OM_EVT_MAX_SLOTS   128
#define OM_EVT_MAX_REGIONS 64
#define OM_EVT_LOG_CAP     128
#define OM_EVT_QUEUE_CAP   64

typedef struct {
    const om_world *owner;
    int      in_use;

    om_event_template templates[OM_MAX_TEMPLATES];
    uint32_t n_templates;

    double   noise[OM_EVT_MAX_REGIONS][OM_MAX_TEMPLATES];
    int      breached[OM_EVT_MAX_REGIONS][OM_MAX_TEMPLATES];
    int64_t  last_fired[OM_EVT_MAX_REGIONS][OM_MAX_TEMPLATES];

    int32_t  chain_counter;
    uint32_t faction_pending[OM_EVT_MAX_REGIONS];
    double   applied_delta[OM_EVT_MAX_REGIONS][OM_F_COUNT];
    int      touched[OM_EVT_MAX_REGIONS]; /* 1 if an event fired here this tick; an
                                            * untouched region must not be floor-clamped */

    uint32_t queue_source[OM_EVT_QUEUE_CAP]; /* om_event_source, parallel to w->event_queue[] */

    om_fired_event   fired[OM_EVT_LOG_CAP];
    uint32_t         fired_n;
    om_pruned_event  pruned[OM_EVT_LOG_CAP];
    uint32_t         pruned_n;
    om_delayed_event delayed[OM_EVT_LOG_CAP];
    uint32_t         delayed_n;
} om_evt_state;

static om_evt_state g_evt_slots[OM_EVT_MAX_SLOTS];

static om_evt_state *evt_find(const om_world *w) {
    if (!w) return NULL;
    for (uint32_t i = 0; i < OM_EVT_MAX_SLOTS; i++) {
        if (g_evt_slots[i].in_use && g_evt_slots[i].owner == w) return &g_evt_slots[i];
    }
    return NULL;
}

static om_evt_state *evt_reset_slot(const om_world *w) {
    om_evt_state *s = evt_find(w);
    if (!s) {
        for (uint32_t i = 0; i < OM_EVT_MAX_SLOTS; i++) {
            if (!g_evt_slots[i].in_use) { s = &g_evt_slots[i]; break; }
        }
        if (!s) s = &g_evt_slots[0]; /* out of slots: last resort, reuse slot 0 */
    }
    memset(s, 0, sizeof(*s));
    s->owner = w;
    s->in_use = 1;
    for (uint32_t r = 0; r < OM_EVT_MAX_REGIONS; r++) {
        for (uint32_t t = 0; t < OM_MAX_TEMPLATES; t++) {
            s->last_fired[r][t] = -1;
        }
    }
    return s;
}

static double evt_clamp(double v, double lo, double hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static int evt_delay_from_u(double lo, double hi, double u) {
    double mode = (lo + hi) / 2.0;
    double c = (hi > lo) ? (mode - lo) / (hi - lo) : 0.5;
    double uu = u, cc = c, l = lo, h = hi;
    if (uu > cc) {
        uu = 1.0 - uu;
        cc = 1.0 - cc;
        double t = l; l = h; h = t;
    }
    double val = l + (h - l) * sqrt(uu * cc);
    double r = floor(val + 0.5);
    if (r < lo) r = lo;
    if (r > hi) r = hi;
    return (int)r;
}

/* ---- template table install/validate ---- */

static int evt_install(om_evt_state *s, const om_event_template *src, uint32_t n) {
    if (n > OM_MAX_TEMPLATES) return -1;
    for (uint32_t i = 0; i < n; i++) {
        const om_event_template *t = &src[i];
        if (t->trigger_kind > OM_TRIG_PROBABILITY) return -1;
        if (t->trigger_kind != OM_TRIG_NONE && t->trigger_field >= OM_F_COUNT) return -1;
        if (t->n_spawns > OM_MAX_SPAWNS) return -1;
        for (uint32_t j = 0; j < t->n_spawns; j++) {
            const om_spawn *sp = &t->spawns[j];
            if (sp->template_id >= n) return -1;
            if (sp->delay_max < sp->delay_min) return -1;
            if (sp->probability < 0.0 || sp->probability > 1.0) return -1;
            if (sp->cond_kind > OM_COND_BELOW) return -1;
            if (sp->cond_kind != OM_COND_NONE && sp->cond_field >= OM_F_COUNT) return -1;
        }
    }
    for (uint32_t i = 0; i < n; i++) {
        s->templates[i] = src[i];
        s->templates[i].id = i;
    }
    s->n_templates = n;
    return 0;
}

int om_events_load(om_world *w, const om_event_template *templates, uint32_t n) {
    if (!w || !templates) return -1;
    om_evt_state *s = evt_reset_slot(w);
    if (evt_install(s, templates, n) != 0) {
        s->n_templates = 0;
        return -1;
    }
    return 0;
}

static void evt_mk(om_event_template *t, const char *name,
                    uint32_t trig_kind, uint32_t trig_field, double threshold,
                    double prob_base, double prob_exp, uint32_t cooldown,
                    double m, double e, double te, double p,
                    uint32_t excl, uint32_t creates_faction, uint32_t chain_step) {
    memset(t, 0, sizeof(*t));
    strncpy(t->name, name, OM_TEMPLATE_NAME - 1);
    t->trigger_kind = trig_kind;
    t->trigger_field = trig_field;
    t->threshold = threshold;
    t->prob_base = prob_base;
    t->prob_exponent = prob_exp;
    t->cooldown_ticks = cooldown;
    t->effect[OM_F_MILITARY] = m;
    t->effect[OM_F_ECONOMY] = e;
    t->effect[OM_F_TENSION] = te;
    t->effect[OM_F_POPULATION] = p;
    t->n_spawns = 0;
    t->exclusion_tag = excl;
    t->creates_faction = creates_faction;
    t->admin_chain_step = chain_step;
}

static void evt_spawn(om_event_template *t, uint32_t target, uint32_t dmin, uint32_t dmax,
                       double prob, uint32_t cond_kind, uint32_t cond_field, double cond_value) {
    om_spawn *sp = &t->spawns[t->n_spawns++];
    sp->template_id = target;
    sp->delay_min = dmin;
    sp->delay_max = dmax;
    sp->cond_kind = cond_kind;
    sp->cond_field = cond_field;
    sp->_pad = 0;
    sp->probability = prob;
    sp->cond_value = cond_value;
}

/* Template ids, fixed by row order in the S-030 table
 * (docs/bible/epics/E-04-events-and-chains.md lines 96-123). */
enum {
    TID_GARRISON_COLLAPSE = 0, TID_BORDER_INCURSION, TID_EMERGENCY_LEVY,
    TID_REGIONAL_REVOLT, TID_REVOLT_CRUSHED, TID_REVOLT_ENTRENCHED,
    TID_TRADE_BOOM, TID_PROSPERITY_UNREST, TID_POPULATION_CRISIS,
    TID_RESISTANCE_MOVEMENT, TID_CONQUEST_UNREST, TID_LABOR_SHORTAGE,
    TID_IMMIGRATION_WAVE, TID_INFRASTRUCTURE_DECAY, TID_MILITARY_BUILDUP,
    TID_WAR_WEARINESS, TID_CULTURAL_RENAISSANCE, TID_FAMINE, TID_FAMINE_RELIEF,
    TID_DIPLOMATIC_INCIDENT, TID_HARVEST_SURPLUS, TID_ADMIN_SEPARATIST,
    TID_ADMIN_POLITICAL_CRISIS, TID_ADMIN_POPULAR_SUPPORT,
    TID_ADMIN_MILITARY_DEFECTION, TID_ADMIN_BREAKAWAY,
    TID_LAUNCH_COUNT
};

void om_events_load_launch(om_world *w) {
    if (!w) return;
    om_evt_state *s = evt_reset_slot(w);
    om_event_template t[TID_LAUNCH_COUNT];

    evt_mk(&t[TID_GARRISON_COLLAPSE], "Garrison Collapse", OM_TRIG_BELOW, OM_F_MILITARY, 30.0,
           0.0, 0.0, 0, -2.0, 0.0, 3.0, 0.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_GARRISON_COLLAPSE], TID_BORDER_INCURSION, 3, 7, 0.55, OM_COND_BELOW, OM_F_MILITARY, 18.0);
    evt_spawn(&t[TID_GARRISON_COLLAPSE], TID_EMERGENCY_LEVY, 2, 5, 0.40, OM_COND_ABOVE, OM_F_ECONOMY, 25.0);

    evt_mk(&t[TID_BORDER_INCURSION], "Border Incursion", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -2.0, -2.0, 2.0, 0.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_BORDER_INCURSION], TID_REGIONAL_REVOLT, 3, 6, 0.60, OM_COND_ABOVE, OM_F_TENSION, 40.0);

    evt_mk(&t[TID_EMERGENCY_LEVY], "Emergency Levy", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, 3.0, -2.0, 2.0, 0.0, OM_EXCL_MILITARY_RELIEF, 0, 0);

    evt_mk(&t[TID_REGIONAL_REVOLT], "Regional Revolt", OM_TRIG_PROBABILITY, OM_F_TENSION, 0.0,
           OM_REVOLT_BASE_PROBABILITY, OM_REVOLT_TENSION_EXPONENT, OM_REVOLT_COOLDOWN_TICKS,
           -2.0, -2.0, 4.0, 0.0, OM_EXCL_POLITICAL_RESOLUTION, 0, 0);
    evt_spawn(&t[TID_REGIONAL_REVOLT], TID_REVOLT_CRUSHED, 2, 5, 0.45, OM_COND_ABOVE, OM_F_MILITARY, 35.0);
    evt_spawn(&t[TID_REGIONAL_REVOLT], TID_REVOLT_ENTRENCHED, 3, 8, 0.55, OM_COND_ABOVE, OM_F_TENSION, 40.0);

    evt_mk(&t[TID_REVOLT_CRUSHED], "Revolt Crushed", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -1.0, 0.0, -2.0, 0.0, OM_EXCL_REVOLT_OUTCOME, 0, 0);

    evt_mk(&t[TID_REVOLT_ENTRENCHED], "Revolt Entrenched", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -4.0, -2.0, 2.0, -2.0, OM_EXCL_REVOLT_OUTCOME, 1, 0);

    evt_mk(&t[TID_TRADE_BOOM], "Trade Boom", OM_TRIG_ABOVE, OM_F_ECONOMY, 55.0,
           0.0, 0.0, 0, 0.0, 2.0, 1.0, 1.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_TRADE_BOOM], TID_PROSPERITY_UNREST, 8, 15, 0.25, OM_COND_ABOVE, OM_F_TENSION, 40.0);

    evt_mk(&t[TID_PROSPERITY_UNREST], "Prosperity Unrest", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, 0.0, -1.0, 4.0, 0.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_POPULATION_CRISIS], "Population Crisis", OM_TRIG_BELOW, OM_F_POPULATION, 20.0,
           0.0, 0.0, 0, -2.0, -2.0, 2.0, 0.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_RESISTANCE_MOVEMENT], "Resistance Movement", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -2.0, 0.0, 5.0, 0.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_CONQUEST_UNREST], "Conquest Unrest", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -1.0, -2.0, 6.0, 0.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_CONQUEST_UNREST], TID_REGIONAL_REVOLT, 3, 6, 0.60, OM_COND_ABOVE, OM_F_TENSION, 40.0);

    evt_mk(&t[TID_LABOR_SHORTAGE], "Labor Shortage", OM_TRIG_BELOW, OM_F_POPULATION, 40.0,
           0.0, 0.0, 0, 0.0, -2.0, 2.0, 0.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_LABOR_SHORTAGE], TID_IMMIGRATION_WAVE, 5, 12, 0.40, OM_COND_ABOVE, OM_F_ECONOMY, 30.0);

    evt_mk(&t[TID_IMMIGRATION_WAVE], "Immigration Wave", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, 0.0, 1.0, 2.0, 3.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_INFRASTRUCTURE_DECAY], "Infrastructure Decay", OM_TRIG_BELOW, OM_F_ECONOMY, 40.0,
           0.0, 0.0, 0, 0.0, -3.0, 2.0, -1.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_MILITARY_BUILDUP], "Military Buildup", OM_TRIG_ABOVE, OM_F_MILITARY, 50.0,
           0.0, 0.0, 0, 2.0, -2.0, 1.0, 0.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_MILITARY_BUILDUP], TID_WAR_WEARINESS, 8, 15, 0.35, OM_COND_ABOVE, OM_F_TENSION, 30.0);

    evt_mk(&t[TID_WAR_WEARINESS], "War Weariness", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -2.0, -1.0, 3.0, 0.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_CULTURAL_RENAISSANCE], "Cultural Renaissance", OM_TRIG_ABOVE, OM_F_ECONOMY, 60.0,
           0.0, 0.0, 0, 0.0, 1.0, -3.0, 1.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_FAMINE], "Famine", OM_TRIG_BELOW, OM_F_ECONOMY, 10.0,
           0.0, 0.0, 0, 0.0, -1.0, 4.0, -3.0, OM_EXCL_NONE, 0, 0);
    evt_spawn(&t[TID_FAMINE], TID_REGIONAL_REVOLT, 3, 6, 0.50, OM_COND_ABOVE, OM_F_TENSION, 40.0);
    evt_spawn(&t[TID_FAMINE], TID_FAMINE_RELIEF, 5, 12, 0.55, OM_COND_ABOVE, OM_F_ECONOMY, 12.0);

    evt_mk(&t[TID_FAMINE_RELIEF], "Famine Relief", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, 0.0, 3.0, -3.0, 2.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_DIPLOMATIC_INCIDENT], "Diplomatic Incident", OM_TRIG_ABOVE, OM_F_TENSION, 35.0,
           0.0, 0.0, 0, 1.0, -1.0, 3.0, 0.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_HARVEST_SURPLUS], "Harvest Surplus", OM_TRIG_ABOVE, OM_F_POPULATION, 50.0,
           0.0, 0.0, 0, 0.0, 2.0, -1.0, 1.0, OM_EXCL_NONE, 0, 0);

    evt_mk(&t[TID_ADMIN_SEPARATIST], "Admin Separatist", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, 0.0, -1.0, 3.0, 0.0, OM_EXCL_NONE, 0, 1);

    evt_mk(&t[TID_ADMIN_POLITICAL_CRISIS], "Admin Political Crisis", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -1.0, -2.0, 4.0, 0.0, OM_EXCL_NONE, 0, 2);

    evt_mk(&t[TID_ADMIN_POPULAR_SUPPORT], "Admin Popular Support", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, 0.0, 0.0, 2.0, -1.0, OM_EXCL_NONE, 0, 3);

    evt_mk(&t[TID_ADMIN_MILITARY_DEFECTION], "Admin Military Defection", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -3.0, 0.0, 2.0, 0.0, OM_EXCL_NONE, 0, 4);

    evt_mk(&t[TID_ADMIN_BREAKAWAY], "Admin Breakaway", OM_TRIG_NONE, 0, 0.0,
           0.0, 0.0, 0, -4.0, -3.0, 5.0, -2.0, OM_EXCL_NONE, 1, 5);

    evt_install(s, t, TID_LAUNCH_COUNT);
}

/* ---- simple accessors ---- */

uint32_t om_event_template_count(const om_world *w) {
    om_evt_state *s = evt_find(w);
    return s ? s->n_templates : 0;
}

int om_event_template_get(const om_world *w, uint32_t id, om_event_template *out) {
    om_evt_state *s = evt_find(w);
    if (!s || !out || id >= s->n_templates) return -1;
    *out = s->templates[id];
    return 0;
}

int32_t om_event_template_by_name(const om_world *w, const char *name) {
    om_evt_state *s = evt_find(w);
    if (!s || !name) return -1;
    for (uint32_t i = 0; i < s->n_templates; i++) {
        if (strncmp(s->templates[i].name, name, OM_TEMPLATE_NAME) == 0) return (int32_t)i;
    }
    return -1;
}

static void evt_roll_noise_internal(om_evt_state *s, om_world *w) {
    for (uint32_t r = 0; r < w->n_regions && r < OM_EVT_MAX_REGIONS; r++) {
        for (uint32_t t = 0; t < s->n_templates; t++) {
            if (s->templates[t].trigger_kind != OM_TRIG_ABOVE && s->templates[t].trigger_kind != OM_TRIG_BELOW) continue;
            double u = om_rng_draw(w);
            s->noise[r][t] = -OM_EVENT_NOISE_RANGE + 2.0 * OM_EVENT_NOISE_RANGE * u;
        }
    }
}

void om_event_roll_noise(om_world *w) {
    if (!w) return;
    om_evt_state *s = evt_find(w);
    if (!s) return;
    evt_roll_noise_internal(s, w);
}

void om_event_set_noise(om_world *w, uint32_t region_idx, uint32_t template_id, double offset) {
    om_evt_state *s = evt_find(w);
    if (!s || region_idx >= OM_EVT_MAX_REGIONS || template_id >= OM_MAX_TEMPLATES) return;
    s->noise[region_idx][template_id] = offset;
}

double om_event_noise(const om_world *w, uint32_t region_idx, uint32_t template_id) {
    om_evt_state *s = evt_find(w);
    if (!s || region_idx >= OM_EVT_MAX_REGIONS || template_id >= OM_MAX_TEMPLATES) return 0.0;
    return s->noise[region_idx][template_id];
}

int om_event_breached(const om_world *w, uint32_t region_idx, uint32_t template_id) {
    om_evt_state *s = evt_find(w);
    if (!s || region_idx >= OM_EVT_MAX_REGIONS || template_id >= OM_MAX_TEMPLATES) return 0;
    return s->breached[region_idx][template_id] ? 1 : 0;
}

int64_t om_event_last_fired(const om_world *w, uint32_t region_idx, uint32_t template_id) {
    om_evt_state *s = evt_find(w);
    if (!s || region_idx >= OM_EVT_MAX_REGIONS || template_id >= OM_MAX_TEMPLATES) return -1;
    return s->last_fired[region_idx][template_id];
}

int32_t om_chain_counter(const om_world *w) {
    /* Most-recently-assigned tag (0 default), not next-to-assign -- see
     * leaf-01.ASSUMPTIONS.md (R-026-05 vs. chain_counter_unsaved control). */
    om_evt_state *s = evt_find(w);
    if (!s) return 0;
    return (s->chain_counter > 0) ? (s->chain_counter - 1) : 0;
}

uint32_t om_region_faction_creation_pending(const om_world *w, uint32_t region_idx) {
    om_evt_state *s = evt_find(w);
    if (!s || region_idx >= OM_EVT_MAX_REGIONS) return 0;
    return s->faction_pending[region_idx];
}

int om_region_event_delta(const om_world *w, uint32_t region_idx, double out[OM_F_COUNT]) {
    if (!w || !out || region_idx >= w->n_regions) return -1;
    om_evt_state *s = evt_find(w);
    if (!s || region_idx >= OM_EVT_MAX_REGIONS) {
        for (uint32_t f = 0; f < OM_F_COUNT; f++) out[f] = 0.0;
        return 0;
    }
    for (uint32_t f = 0; f < OM_F_COUNT; f++) out[f] = s->applied_delta[region_idx][f];
    return 0;
}

/* Queue insertion sink: step 1 resolves into a local working list (kept[]),
 * written back to w->event_queue[] once, so a mid-resolution spawn never
 * collides with due entries still being read from the same array; step 2
 * and om_event_queue_external write straight at the live queue. */
typedef struct {
    om_queued_event *arr;
    uint32_t        *src;
    uint32_t        *n;
    uint32_t         cap;
} evt_sink;

static int evt_enqueue(om_evt_state *s, om_world *w, evt_sink *sink,
                        uint32_t region_idx, uint32_t template_id, uint64_t due_tick,
                        double probability, int32_t source_faction, uint32_t chain_length,
                        uint32_t cond_kind, uint32_t cond_field, double cond_value,
                        int32_t chain_tag, uint32_t source) {
    if (*sink->n >= sink->cap) {
        if (s->pruned_n < OM_EVT_LOG_CAP) {
            om_pruned_event *pe = &s->pruned[s->pruned_n++];
            memset(pe, 0, sizeof(*pe));
            pe->tick = w->tick;
            pe->region_idx = region_idx;
            pe->template_id = template_id;
            pe->chain_tag = chain_tag;
            pe->cond_kind = OM_COND_NONE;
        }
        return 0;
    }
    uint32_t idx = (*sink->n)++;
    om_queued_event *qe = &sink->arr[idx];
    qe->due_tick = due_tick;
    qe->region_idx = region_idx;
    qe->template_id = template_id;
    qe->probability = probability;
    qe->chain_tag = chain_tag;
    qe->source_faction = source_faction;
    qe->chain_length = chain_length;
    qe->cond_kind = cond_kind;
    qe->cond_field = cond_field;
    qe->cond_value = cond_value;
    qe->exclusion_tag = (template_id < s->n_templates) ? s->templates[template_id].exclusion_tag : (uint32_t)OM_EXCL_NONE;
    sink->src[idx] = source;
    return 1;
}

int om_event_queue_external(om_world *w, uint32_t region_idx, uint32_t template_id,
                             uint64_t due_tick, double probability, int32_t source_faction,
                             uint32_t chain_length) {
    if (!w) return -1;
    om_evt_state *s = evt_find(w);
    if (!s) return -1;
    if (template_id >= s->n_templates) return -1;
    if (region_idx >= w->n_regions) return -1;
    if (w->regions[region_idx].tier == OM_TIER_EMPTY) return -1;
    if (due_tick <= w->tick) return -1;
    if (probability < 0.0 || probability > 1.0) return -1;
    if (s->templates[template_id].admin_chain_step > 0 && chain_length != 0 &&
        (chain_length < 3 || chain_length > 8)) return -1;

    evt_sink sink = { w->event_queue, s->queue_source, &w->event_queue_n, OM_EVT_QUEUE_CAP };
    int32_t tag = s->chain_counter;
    if (!evt_enqueue(s, w, &sink, region_idx, template_id, due_tick, probability,
                      source_faction, chain_length, OM_COND_NONE, 0, 0.0, tag, OM_SRC_EXTERNAL)) {
        return -1;
    }
    s->chain_counter++;
    return tag;
}

/* ---- firing: log, sum/apply the delta, mark faction creation, dispatch spawns ---- */

static uint32_t evt_admin_chain_spawn(om_evt_state *s, om_world *w, evt_sink *sink,
                                       uint32_t region_idx, const om_event_template *t,
                                       int32_t chain_tag, int32_t source_faction, uint32_t L) {
    uint32_t cs = t->admin_chain_step;
    if (cs == 0 || cs >= 5 || L < 3) return 0;
    if (L > 8) L = 8;
    uint32_t Sn = 3 + (L - 3) / 2;
    uint32_t included[5];
    uint32_t ni = 0;
    included[ni++] = 1;
    if (Sn >= 4) included[ni++] = 2;
    if (Sn >= 5) included[ni++] = 3;
    included[ni++] = 4;
    included[ni++] = 5;

    uint32_t idx = 0;
    int found = 0;
    for (uint32_t i = 0; i < ni; i++) {
        if (included[i] == cs) { idx = i; found = 1; break; }
    }
    if (!found || idx + 1 >= ni) return 0;

    uint32_t next_step = included[idx + 1];
    uint32_t T = ni - 1;
    uint32_t target_span = L - 1;
    uint32_t surplus = (target_span > T) ? (target_span - T) : 0;
    uint32_t gap = 1 + ((idx < surplus) ? 1 : 0);
    uint64_t due = w->tick + gap;

    uint32_t next_tid = OM_MAX_TEMPLATES;
    for (uint32_t i = 0; i < s->n_templates; i++) {
        if (s->templates[i].admin_chain_step == next_step) { next_tid = i; break; }
    }
    if (next_tid == OM_MAX_TEMPLATES) return 0;

    return (uint32_t)evt_enqueue(s, w, sink, region_idx, next_tid, due, 1.0,
                                  source_faction, L, OM_COND_NONE, 0, 0.0, chain_tag, OM_SRC_SPAWN);
}

static uint32_t evt_create_spawn(om_evt_state *s, om_world *w, evt_sink *sink,
                                  uint32_t region_idx, const om_spawn *sp,
                                  int32_t chain_tag, int32_t source_faction,
                                  const double *snap_region) {
    double u = om_rng_draw(w);
    int delay = evt_delay_from_u((double)sp->delay_min, (double)sp->delay_max, u);
    uint64_t due = w->tick + (uint64_t)delay;
    uint32_t cond_kind = sp->cond_kind;
    uint32_t cond_field = sp->cond_field;
    double cond_value = sp->cond_value;

#ifdef OM_DEBUG_INJECT
    if (w->inject == OM_BUG_COND_AT_SPAWN && cond_kind != OM_COND_NONE && snap_region) {
        double fv = snap_region[cond_field];
        int met = (cond_kind == OM_COND_ABOVE) ? (fv > cond_value) : (fv < cond_value);
        if (met) cond_kind = OM_COND_NONE;
    }
#else
    (void)snap_region;
#endif

    return (uint32_t)evt_enqueue(s, w, sink, region_idx, sp->template_id, due, sp->probability,
                                  source_faction, 0, cond_kind, cond_field, cond_value,
                                  chain_tag, OM_SRC_SPAWN);
}

static void evt_fire(om_evt_state *s, om_world *w, uint32_t region_idx, uint32_t tid,
                      int32_t chain_tag, uint32_t source, double draw,
                      int32_t source_faction, uint32_t chain_length,
                      const double *snap_region, evt_sink *sink) {
    if (tid >= s->n_templates) return;
    om_event_template *t = &s->templates[tid];
    uint64_t tick = w->tick;

    om_fired_event *fe = NULL;
    if (s->fired_n < OM_EVT_LOG_CAP) {
        fe = &s->fired[s->fired_n++];
        memset(fe, 0, sizeof(*fe));
        fe->tick = tick;
        fe->region_idx = region_idx;
        fe->template_id = tid;
        fe->chain_tag = chain_tag;
        fe->source = source;
        for (uint32_t f = 0; f < OM_F_COUNT; f++) fe->delta[f] = t->effect[f];
        fe->draw = draw;
        fe->creates_faction = t->creates_faction;
    }

    if (region_idx < OM_EVT_MAX_REGIONS) {
        s->last_fired[region_idx][tid] = (int64_t)tick;
        for (uint32_t f = 0; f < OM_F_COUNT; f++) s->applied_delta[region_idx][f] += t->effect[f];
        s->touched[region_idx] = 1;
        if (t->creates_faction) s->faction_pending[region_idx] = tid + 1;
    }

#ifdef OM_DEBUG_INJECT
    if (w->inject == OM_BUG_SEQUENTIAL_DELTAS && region_idx < w->n_regions) {
        om_region *rg = &w->regions[region_idx];
        rg->military = evt_clamp(rg->military + t->effect[OM_F_MILITARY], 0.0, OM_EVT_FIELD_CEILING);
        rg->economy = evt_clamp(rg->economy + t->effect[OM_F_ECONOMY], OM_ECONOMY_FLOOR, OM_EVT_FIELD_CEILING);
        rg->tension = evt_clamp(rg->tension + t->effect[OM_F_TENSION], OM_TENSION_FLOOR, OM_EVT_FIELD_CEILING);
        rg->population = evt_clamp(rg->population + t->effect[OM_F_POPULATION], 0.0, OM_EVT_FIELD_CEILING);
    }
#endif

    uint32_t nsp = 0;
    if (t->admin_chain_step > 0) {
        nsp += evt_admin_chain_spawn(s, w, sink, region_idx, t, chain_tag, source_faction, chain_length);
    } else {
        for (uint32_t j = 0; j < t->n_spawns; j++) {
            nsp += evt_create_spawn(s, w, sink, region_idx, &t->spawns[j], chain_tag, source_faction, snap_region);
        }
    }
    if (fe) fe->n_spawned = nsp;
}

/* ---- step 1: resolve the due queue (R-027-02/03/07, R-028-01..05) ---- */

typedef struct {
    uint32_t region_idx, template_id;
    double   probability;
    int32_t  chain_tag;
    int32_t  source_faction;
    uint32_t chain_length;
    uint32_t exclusion_tag;
    uint32_t source;
    int      removed;
    double   r_draw;
    int      has_r;
} evt_cand;

static void evt_resolve_queue(om_evt_state *s, om_world *w, double snap[][OM_F_COUNT], evt_sink *kept_sink) {
    uint64_t tick = w->tick;
    uint32_t n = w->event_queue_n;
    if (n > OM_EVT_QUEUE_CAP) n = OM_EVT_QUEUE_CAP;

    om_queued_event cur[OM_EVT_QUEUE_CAP];
    uint32_t cur_src[OM_EVT_QUEUE_CAP];
    memcpy(cur, w->event_queue, n * sizeof(om_queued_event));
    memcpy(cur_src, s->queue_source, n * sizeof(uint32_t));

    evt_cand cand[OM_EVT_QUEUE_CAP];
    uint32_t cn = 0;

    for (uint32_t i = 0; i < n; i++) {
        om_queued_event *qe = &cur[i];
        if (qe->due_tick != tick) {
            evt_enqueue(s, w, kept_sink, qe->region_idx, qe->template_id, qe->due_tick,
                        qe->probability, qe->source_faction, qe->chain_length,
                        qe->cond_kind, qe->cond_field, qe->cond_value, qe->chain_tag, cur_src[i]);
            continue;
        }
        if (qe->template_id >= s->n_templates) continue; /* unknown template: drop defensively */

        evt_cand *c = &cand[cn];
        c->region_idx = qe->region_idx;
        c->template_id = qe->template_id;
        c->probability = qe->probability;
        c->chain_tag = qe->chain_tag;
        c->source_faction = qe->source_faction;
        c->chain_length = qe->chain_length;
        c->exclusion_tag = qe->exclusion_tag;
        c->source = cur_src[i];
        c->removed = 0;
        c->has_r = 0;
        c->r_draw = 0.0;

#ifdef OM_DEBUG_INJECT
        if (w->inject == OM_BUG_DRAW_BEFORE_CONDITION) {
            c->r_draw = om_rng_draw(w);
            c->has_r = 1;
        }
#endif

        int cond_met = 1;
        double fv = 0.0;
        if (qe->cond_kind != OM_COND_NONE) {
            fv = (qe->region_idx < OM_EVT_MAX_REGIONS) ? snap[qe->region_idx][qe->cond_field] : 0.0;
            cond_met = (qe->cond_kind == OM_COND_ABOVE) ? (fv > qe->cond_value) : (fv < qe->cond_value);
        }
        if (!cond_met) {
            c->removed = 1;
            if (s->pruned_n < OM_EVT_LOG_CAP) {
                om_pruned_event *pe = &s->pruned[s->pruned_n++];
                pe->tick = tick;
                pe->region_idx = qe->region_idx;
                pe->template_id = qe->template_id;
                pe->chain_tag = qe->chain_tag;
                pe->cond_kind = qe->cond_kind;
                pe->cond_field = qe->cond_field;
                pe->_pad = 0;
                pe->cond_value = qe->cond_value;
                pe->field_value = fv;
            }
        }
        cn++;
    }

    /* phase 1: exclusion resolution, sorted tag order, region-scoped groups */
    for (uint32_t tag = OM_EXCL_MILITARY_RELIEF; tag <= OM_EXCL_REVOLT_OUTCOME; tag++) {
        for (uint32_t ri = 0; ri < cn; ri++) {
            if (cand[ri].removed || cand[ri].exclusion_tag != tag) continue;
            uint32_t region = cand[ri].region_idx;
            int is_first = 1;
            for (uint32_t k = 0; k < ri; k++) {
                if (!cand[k].removed && cand[k].exclusion_tag == tag && cand[k].region_idx == region) { is_first = 0; break; }
            }
            if (!is_first) continue;

            uint32_t members[OM_EVT_QUEUE_CAP];
            uint32_t mn = 0;
            for (uint32_t k = ri; k < cn; k++) {
                if (!cand[k].removed && cand[k].exclusion_tag == tag && cand[k].region_idx == region) members[mn++] = k;
            }
            if (mn < 2) continue;

            double maxp = -1.0;
            uint32_t maxidxs[OM_EVT_QUEUE_CAP];
            uint32_t nmax = 0;
            for (uint32_t k = 0; k < mn; k++) {
                double p = cand[members[k]].probability;
                if (p > maxp + 1e-12) { maxp = p; nmax = 0; maxidxs[nmax++] = members[k]; }
                else if (fabs(p - maxp) <= 1e-12) { maxidxs[nmax++] = members[k]; }
            }
            uint32_t winner;
            if (nmax == 1) {
                winner = maxidxs[0];
            } else {
                double d = om_rng_draw(w);
                uint32_t earliest = maxidxs[0], latest = maxidxs[0];
                for (uint32_t k = 1; k < nmax; k++) {
                    if (maxidxs[k] < earliest) earliest = maxidxs[k];
                    if (maxidxs[k] > latest) latest = maxidxs[k];
                }
                winner = (d < 0.5) ? earliest : latest;
            }

            for (uint32_t k = 0; k < mn; k++) {
                if (members[k] == winner) continue;
                evt_cand *loser = &cand[members[k]];
#ifdef OM_DEBUG_INJECT
                if (w->inject == OM_BUG_EXCLUSION_CANCELS) { loser->removed = 1; continue; }
#endif
                double dd = om_rng_draw(w);
                int extra = (int)floor(dd * 2.0);
                uint64_t new_due = tick + 1 + (uint64_t)extra;
                if (s->delayed_n < OM_EVT_LOG_CAP) {
                    om_delayed_event *de = &s->delayed[s->delayed_n++];
                    de->tick = tick;
                    de->region_idx = loser->region_idx;
                    de->template_id = loser->template_id;
                    de->chain_tag = loser->chain_tag;
                    de->exclusion_tag = loser->exclusion_tag;
                    de->kept_template_id = cand[winner].template_id;
                    de->_pad = 0;
                    de->new_due = new_due;
                }
                evt_enqueue(s, w, kept_sink, loser->region_idx, loser->template_id, new_due,
                            loser->probability, loser->source_faction, loser->chain_length,
                            OM_COND_NONE, 0, 0.0, loser->chain_tag, loser->source);
                loser->removed = 1;
            }
        }
    }

    /* phase 2: probability roll for every surviving candidate, original order */
    for (uint32_t i = 0; i < cn; i++) {
        evt_cand *c = &cand[i];
        if (c->removed) continue;
        double r = c->has_r ? c->r_draw : om_rng_draw(w);
        if (r <= c->probability) {
            const double *snap_region = (c->region_idx < OM_EVT_MAX_REGIONS) ? snap[c->region_idx] : NULL;
            evt_fire(s, w, c->region_idx, c->template_id, c->chain_tag, c->source, r,
                     c->source_faction, c->chain_length, snap_region, kept_sink);
        }
        /* r > probability: drops silently, not re-queued, not logged */
    }
}

/* ---- step 2: fresh triggers against tick-start fields (R-026-01..07, R-029-01..05) ---- */

static double evt_live_field(const om_world *w, uint32_t r, uint32_t field) {
    switch (field) {
        case OM_F_MILITARY:   return w->regions[r].military;
        case OM_F_ECONOMY:    return w->regions[r].economy;
        case OM_F_TENSION:    return w->regions[r].tension;
        case OM_F_POPULATION: return w->regions[r].population;
        default: return 0.0;
    }
}

/* Draw order (e2e "Draw order", ALG-34): per region, threshold crossings
 * detected with no draw; then one regional-revolt roll for the region
 * (even at p = 0); then the fired threshold templates' spawn-delay draws
 * in template-table order; then the revolt's own spawns last. */
static void evt_evaluate_triggers(om_evt_state *s, om_world *w, double snap[][OM_F_COUNT], evt_sink *sink) {
    uint64_t tick = w->tick;
    for (uint32_t r = 0; r < w->n_regions && r < OM_EVT_MAX_REGIONS; r++) {
        if (w->regions[r].tier == OM_TIER_EMPTY) continue;

        int grace = (tick <= OM_EVENT_GRACE_PERIOD);
#ifdef OM_DEBUG_INJECT
        if (w->inject == OM_BUG_NO_GRACE_PERIOD) grace = 0;
        int live = (w->inject == OM_BUG_TRIGGERS_READ_LIVE);
#else
        int live = 0;
#endif
        const double *reads = live ? NULL : snap[r];

        int should_fire[OM_MAX_TEMPLATES];
        memset(should_fire, 0, s->n_templates * sizeof(should_fire[0]));
        int revolt_fire = 0;
        uint32_t revolt_tid = 0;
        double revolt_draw = 0.0;

        for (uint32_t tid = 0; tid < s->n_templates; tid++) {
            om_event_template *t = &s->templates[tid];
            if (t->trigger_kind != OM_TRIG_ABOVE && t->trigger_kind != OM_TRIG_BELOW) continue;

            double fv = live ? evt_live_field(w, r, t->trigger_field) : reads[t->trigger_field];
            double noise = (tid < OM_MAX_TEMPLATES) ? s->noise[r][tid] : 0.0;
            double eff = t->threshold + noise;
            int is_past = (t->trigger_kind == OM_TRIG_ABOVE) ? (fv > eff) : (fv < eff);

            if (grace) { s->breached[r][tid] = is_past; continue; }

            int was = s->breached[r][tid];
            int fire = is_past && !was;
#ifdef OM_DEBUG_INJECT
            if (w->inject == OM_BUG_FIRES_EVERY_TICK) fire = is_past;
#endif
            s->breached[r][tid] = is_past;
            should_fire[tid] = fire;
        }

        if (!grace) {
            for (uint32_t tid = 0; tid < s->n_templates; tid++) {
                om_event_template *t = &s->templates[tid];
                if (t->trigger_kind != OM_TRIG_PROBABILITY) continue;
                int64_t last = s->last_fired[r][tid];
                if (last >= 0 && (int64_t)tick - last < (int64_t)t->cooldown_ticks) continue;
                double fv = live ? evt_live_field(w, r, t->trigger_field) : reads[t->trigger_field];
                double p = t->prob_base * om_pow(fv / 100.0, t->prob_exponent);
                double rr = om_rng_draw(w);
                if (rr < p) {
                    revolt_fire = 1;
                    revolt_tid = tid;
                    revolt_draw = rr;
                }
            }
        }

        for (uint32_t tid = 0; tid < s->n_templates; tid++) {
            if (!should_fire[tid]) continue;
            int32_t tag = s->chain_counter++;
            evt_fire(s, w, r, tid, tag, OM_SRC_TRIGGER, -1.0, -1, 0, snap[r], sink);
#ifdef OM_DEBUG_INJECT
            if (w->inject == OM_BUG_TRIGGERS_READ_LIVE) {
                om_event_template *t = &s->templates[tid];
                om_region *rg = &w->regions[r];
                rg->military = evt_clamp(rg->military + t->effect[OM_F_MILITARY], 0.0, OM_EVT_FIELD_CEILING);
                rg->economy = evt_clamp(rg->economy + t->effect[OM_F_ECONOMY], OM_ECONOMY_FLOOR, OM_EVT_FIELD_CEILING);
                rg->tension = evt_clamp(rg->tension + t->effect[OM_F_TENSION], OM_TENSION_FLOOR, OM_EVT_FIELD_CEILING);
                rg->population = evt_clamp(rg->population + t->effect[OM_F_POPULATION], 0.0, OM_EVT_FIELD_CEILING);
            }
#endif
        }

        if (revolt_fire) {
            int32_t tag = s->chain_counter++;
            evt_fire(s, w, r, revolt_tid, tag, OM_SRC_TRIGGER, revolt_draw, -1, 0, snap[r], sink);
        }
    }
}

/* ---- om_step_events: tick steps 1-2 ---- */

void om_step_events(om_world *w) {
    if (!w) return;
    om_evt_state *s = evt_find(w);
    if (!s || s->n_templates == 0) return;

#ifdef OM_DEBUG_INJECT
    if (w->inject == OM_BUG_NOISE_REROLLED) evt_roll_noise_internal(s, w);
#endif

    s->fired_n = 0;
    s->pruned_n = 0;
    s->delayed_n = 0;
    for (uint32_t r = 0; r < w->n_regions && r < OM_EVT_MAX_REGIONS; r++) {
        s->faction_pending[r] = 0;
        s->touched[r] = 0;
        for (uint32_t f = 0; f < OM_F_COUNT; f++) s->applied_delta[r][f] = 0.0;
    }

    double snap[OM_EVT_MAX_REGIONS][OM_F_COUNT];
    for (uint32_t r = 0; r < w->n_regions && r < OM_EVT_MAX_REGIONS; r++) {
        snap[r][OM_F_MILITARY] = w->regions[r].military;
        snap[r][OM_F_ECONOMY] = w->regions[r].economy;
        snap[r][OM_F_TENSION] = w->regions[r].tension;
        snap[r][OM_F_POPULATION] = w->regions[r].population;
    }

    om_queued_event kept[OM_EVT_QUEUE_CAP];
    uint32_t ksrc[OM_EVT_QUEUE_CAP];
    uint32_t kn = 0;
    evt_sink kept_sink = { kept, ksrc, &kn, OM_EVT_QUEUE_CAP };

    evt_resolve_queue(s, w, snap, &kept_sink);

    memcpy(w->event_queue, kept, kn * sizeof(om_queued_event));
    memcpy(s->queue_source, ksrc, kn * sizeof(uint32_t));
    w->event_queue_n = kn;

    evt_sink live_sink = { w->event_queue, s->queue_source, &w->event_queue_n, OM_EVT_QUEUE_CAP };
    evt_evaluate_triggers(s, w, snap, &live_sink);

    for (uint32_t r = 0; r < w->n_regions && r < OM_EVT_MAX_REGIONS; r++) {
        if (w->regions[r].tier == OM_TIER_EMPTY) continue;
        if (!s->touched[r]) continue; /* no event fired here this tick: leave fields untouched,
                                        * never lift an already-below-floor field just by evaluating */
        om_region *rg = &w->regions[r];
#ifdef OM_DEBUG_INJECT
        if (w->inject != OM_BUG_SEQUENTIAL_DELTAS)
#endif
        {
            double nm = evt_clamp(snap[r][OM_F_MILITARY] + s->applied_delta[r][OM_F_MILITARY], 0.0, OM_EVT_FIELD_CEILING);
            double ne = evt_clamp(snap[r][OM_F_ECONOMY] + s->applied_delta[r][OM_F_ECONOMY], OM_ECONOMY_FLOOR, OM_EVT_FIELD_CEILING);
            double nt = evt_clamp(snap[r][OM_F_TENSION] + s->applied_delta[r][OM_F_TENSION], OM_TENSION_FLOOR, OM_EVT_FIELD_CEILING);
            double np = evt_clamp(snap[r][OM_F_POPULATION] + s->applied_delta[r][OM_F_POPULATION], 0.0, OM_EVT_FIELD_CEILING);
            rg->military = nm;
            rg->economy = ne;
            rg->tension = nt;
            rg->population = np;
        }
        s->applied_delta[r][OM_F_MILITARY] = rg->military - snap[r][OM_F_MILITARY];
        s->applied_delta[r][OM_F_ECONOMY] = rg->economy - snap[r][OM_F_ECONOMY];
        s->applied_delta[r][OM_F_TENSION] = rg->tension - snap[r][OM_F_TENSION];
        s->applied_delta[r][OM_F_POPULATION] = rg->population - snap[r][OM_F_POPULATION];
    }
}

/* ---- tick-log readers (last step only) ---- */

uint32_t om_tick_events(const om_world *w, om_fired_event *out, uint32_t max) {
    om_evt_state *s = evt_find(w);
    if (!s || !out) return 0;
    uint32_t n = s->fired_n < max ? s->fired_n : max;
    memcpy(out, s->fired, n * sizeof(om_fired_event));
    return n;
}

uint32_t om_tick_pruned(const om_world *w, om_pruned_event *out, uint32_t max) {
    om_evt_state *s = evt_find(w);
    if (!s || !out) return 0;
    uint32_t n = s->pruned_n < max ? s->pruned_n : max;
    memcpy(out, s->pruned, n * sizeof(om_pruned_event));
    return n;
}

uint32_t om_tick_delayed(const om_world *w, om_delayed_event *out, uint32_t max) {
    om_evt_state *s = evt_find(w);
    if (!s || !out) return 0;
    uint32_t n = s->delayed_n < max ? s->delayed_n : max;
    memcpy(out, s->delayed, n * sizeof(om_delayed_event));
    return n;
}
