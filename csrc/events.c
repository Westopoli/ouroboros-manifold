/* csrc/events.c — E-04 event library, triggers, queue resolution (E-04 build cards).
 * 26-template launch library, threshold/probability triggers (ALG-32..34),
 * pending-queue resolver (ALG-35..37: condition, exclusion, probability,
 * spawns), 9 OM_BUG_* positive controls under OM_DEBUG_INJECT. Per-world
 * event state lives in one struct calloc'd on first use and hung off
 * w->events_state (om_internal.h), freed via w->events_state_free on
 * om_world_free (region.c) -- see leaf-01.ASSUMPTIONS.md and
 * questions/leaf-01-Q1..4.md for the escalations this file works around
 * (missing OM_FIELD_CEILING, no struct field for this state, and a class
 * of acceptance tests that stay red against a rule-faithful
 * implementation). Draws go through om_rng_draw (csrc/sim.c); region.c
 * seeds the world. */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define OM_EVT_FIELD_CEILING 100.0

#define OM_EVT_MAX_REGIONS  64
#define OM_EVT_LOG_CAP      128
#define OM_EVT_QUEUE_CAP    64
#define OM_EVT_MANUAL_CAP   256
#define OM_EVT_MAX_ATTACHED 8

/* A manually-fired event (om_event_fire_manual) and the characters ALG-49
 * attaches to it. om_fired_event (the tick log, ouroboros_sim.h ~line 609)
 * has no field for attached character ids and is parent-owned, so this
 * record -- and the id om_event_fire_manual hands out -- lives here, next
 * to the rest of the per-world event state this file already keeps outside
 * om_world (see the file header comment). */
typedef struct {
    uint32_t id;
    uint32_t region_idx;
    uint32_t tier;
    uint32_t attached[OM_EVT_MAX_ATTACHED];
    uint32_t n_attached;
} om_evt_manual_fire;

typedef struct {
    om_event_template templates[OM_MAX_TEMPLATES];
    uint32_t n_templates;
    uint32_t launch_count;                        /* F2h: the S-030 accessor's count, excludes registrations */
    int32_t  significance_tier[OM_MAX_TEMPLATES];  /* F2h: om_event_register_external's own field, no public getter yet */

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

    om_evt_manual_fire manual[OM_EVT_MANUAL_CAP];
    uint32_t           manual_n;
    uint32_t           manual_next_id; /* last id handed out; 0 means none yet */
} om_evt_state;

static uint32_t evt_save_size(const om_world *w);
static void evt_save_write(const om_world *w, uint8_t *out);
static int evt_save_read(om_world *w, const uint8_t *buf, uint32_t len);

/* F2m (om_internal.h): wires the three save hooks onto a world that has not
 * yet allocated w->events_state, so a fresh world's read hook is never NULL
 * (evt_save_read below already copes with a NULL events_state / len == 0 by
 * building fresh state or writing a 0-length blob). Called once from
 * om_world_new (csrc/region.c); evt_alloc below sets the same three
 * pointers again once state actually exists, so this never allocates. */
void om_events_install_save_hooks(om_world *w) {
    w->events_state_size = evt_save_size;
    w->events_state_write = evt_save_write;
    w->events_state_read = evt_save_read;
}

static om_evt_state *evt_find(const om_world *w) {
    if (!w) return NULL;
    return (om_evt_state *)w->events_state;
}

static void evt_state_reset_fields(om_evt_state *s) {
    memset(s, 0, sizeof(*s));
    for (uint32_t r = 0; r < OM_EVT_MAX_REGIONS; r++) {
        for (uint32_t t = 0; t < OM_MAX_TEMPLATES; t++) {
            s->last_fired[r][t] = -1;
        }
    }
}

/* Allocates w->events_state on first use; w already owns and frees this
 * pointer (om_internal.h struct om_world, region.c om_world_free). */
static om_evt_state *evt_alloc(om_world *w) {
    om_evt_state *s = calloc(1, sizeof(om_evt_state));
    if (!s) return NULL;
    evt_state_reset_fields(s);
    w->events_state = s;
    w->events_state_free = free;
    w->events_state_size = evt_save_size;
    w->events_state_write = evt_save_write;
    w->events_state_read = evt_save_read;
    return s;
}

static om_evt_state *evt_reset_slot(om_world *w) {
    if (!w) return NULL;
    om_evt_state *s = (om_evt_state *)w->events_state;
    if (!s) return evt_alloc(w);
    evt_state_reset_fields(s);
    return s;
}

/* Like evt_reset_slot, but never clears state that already exists -- used
 * by om_event_fire_manual, which must not discard a world's loaded
 * templates just because it runs before the first om_events_load. */
static om_evt_state *evt_ensure(om_world *w) {
    if (!w) return NULL;
    if (w->events_state) return (om_evt_state *)w->events_state;
    return evt_alloc(w);
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
    s->launch_count = n; /* F2h: a (re)load resets the S-030 count and drops any registrations */
    return 0;
}

int om_events_load(om_world *w, const om_event_template *templates, uint32_t n) {
    if (!w || !templates) return -1;
    om_evt_state *s = evt_reset_slot(w);
    if (!s) return -1;
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
    if (!s) return;
    om_event_template t[TID_LAUNCH_COUNT];

    /* constants-table: docs/bible/epics/E-04-events-and-chains.md S-030 */
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
    /* end constants-table */

    evt_install(s, t, TID_LAUNCH_COUNT);
}

/* ---- simple accessors ---- */

uint32_t om_event_template_count(const om_world *w) {
    om_evt_state *s = evt_find(w);
    return s ? s->launch_count : 0; /* F2h: excludes om_event_register_external ids */
}

/* F2h: registers a named template outside the fixed launch library, id
 * >= om_event_template_count(w). Idempotent by name; no trigger (R-030-02
 * spawn-only), no effects, exclusion tag NONE. */
int32_t om_event_register_external(om_world *w, const char *name, int32_t significance_tier) {
    if (!w || !name) return -1;
    om_evt_state *s = evt_ensure(w);
    if (!s) return -1;
    for (uint32_t i = s->launch_count; i < s->n_templates; i++) {
        if (strncmp(s->templates[i].name, name, OM_TEMPLATE_NAME) == 0) return (int32_t)i;
    }
    if (s->n_templates >= OM_MAX_TEMPLATES) return -1;
    uint32_t id = s->n_templates;
    om_event_template *t = &s->templates[id];
    memset(t, 0, sizeof(*t));
    strncpy(t->name, name, OM_TEMPLATE_NAME - 1);
    t->id = id;
    t->trigger_kind = OM_TRIG_NONE;
    t->exclusion_tag = OM_EXCL_NONE;
    s->significance_tier[id] = significance_tier;
    s->n_templates = id + 1;
    return (int32_t)id;
}

/* F2h: no existing accessor maps id -> name. NULL if out of range. */
const char *om_event_template_name(const om_world *w, uint32_t template_id) {
    om_evt_state *s = evt_find(w);
    if (!s || template_id >= s->n_templates) return NULL;
    return s->templates[template_id].name;
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
    /* Most-recently-assigned tag, 0 while none has been assigned: tags start
     * at 1, so the counter is both "last used" (R-026-05 and the
     * chain_counter_unsaved control read it that way) and never 0 once a chain
     * exists (test_R_111_02 load-restores test). */
    om_evt_state *s = evt_find(w);
    if (!s) return 0;
    return s->chain_counter;
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
        (chain_length < OM_ADMIN_REVOLT_CHAIN_MIN || chain_length > OM_ADMIN_REVOLT_CHAIN_MAX)) return -1;

    evt_sink sink = { w->event_queue, s->queue_source, &w->event_queue_n, OM_EVT_QUEUE_CAP };
    int32_t tag = s->chain_counter + 1;
    if (!evt_enqueue(s, w, &sink, region_idx, template_id, due_tick, probability,
                      source_faction, chain_length, OM_COND_NONE, 0, 0.0, tag, OM_SRC_EXTERNAL)) {
        return -1;
    }
    s->chain_counter = tag;
    return tag;
}

/* ---- firing: log, sum/apply the delta, mark faction creation, dispatch spawns ---- */

static uint32_t evt_admin_chain_spawn(om_evt_state *s, om_world *w, evt_sink *sink,
                                       uint32_t region_idx, const om_event_template *t,
                                       int32_t chain_tag, int32_t source_faction, uint32_t L) {
    uint32_t cs = t->admin_chain_step;
    /* constants-table: docs/bible/epics/E-04-events-and-chains.md S-030 */
    if (cs == 0 || cs >= 5 || L < OM_ADMIN_REVOLT_CHAIN_MIN) return 0;
    if (L > OM_ADMIN_REVOLT_CHAIN_MAX) L = OM_ADMIN_REVOLT_CHAIN_MAX;
    uint32_t Sn = OM_ADMIN_REVOLT_CHAIN_MIN + (L - OM_ADMIN_REVOLT_CHAIN_MIN) / 2;
    uint32_t included[5];
    uint32_t ni = 0;
    included[ni++] = 1;
    if (Sn >= 4) included[ni++] = 2;
    if (Sn >= 5) included[ni++] = 3;
    included[ni++] = 4;
    included[ni++] = 5;
    /* end constants-table */

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
        /* ALG-41: an Admin Breakaway (or any faction-creating template)
         * queued through om_event_queue_external is pruned if the region's
         * owner no longer matches the chain's source faction by the time it
         * resolves -- the chain's own owner-mismatch/changed-hands rule,
         * unimplemented anywhere until now (see om_event_queue_external's
         * hardcoded OM_COND_NONE and evt_admin_chain_spawn, which never
         * carried a condition either). */
        if (cond_met && cur_src[i] == OM_SRC_EXTERNAL && qe->source_faction >= 0 &&
            s->templates[qe->template_id].creates_faction) {
            int32_t owner = (qe->region_idx < w->n_regions) ? w->regions[qe->region_idx].faction_id : -1;
            if (owner != qe->source_faction) {
                cond_met = 0;
                fv = (double)owner;
            }
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
                if (p > maxp + OM_TIE_EPSILON) { maxp = p; nmax = 0; maxidxs[nmax++] = members[k]; }
                else if (fabs(p - maxp) <= OM_TIE_EPSILON) { maxidxs[nmax++] = members[k]; }
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
                double p = t->prob_base * om_pow(fv / OM_FIELD_MAX, t->prob_exponent);
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
            int32_t tag = ++s->chain_counter;
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
            int32_t tag = ++s->chain_counter;
            evt_fire(s, w, r, revolt_tid, tag, OM_SRC_TRIGGER, revolt_draw, -1, 0, snap[r], sink);
        }
    }
}

/* ---- om_step_events: tick steps 1-2 ---- */

void om_step_events(om_world *w) {
    if (!w) return;
    om_evt_state *s = evt_find(w);
    if (!s || s->n_templates == 0) {
        /* No template library loaded. Drain any due entries written directly to
         * w->event_queue by om_step_admin_revolts (ALG-29) and faction conquest
         * (ALG-22) so they do not accumulate to OM_EVT_QUEUE_CAP and block future
         * om_event_queue_external calls. Non-due entries are kept in case templates
         * are loaded before their due_tick arrives. */
        uint64_t tick = w->tick;
        uint32_t kn = 0;
        for (uint32_t i = 0; i < w->event_queue_n; i++) {
            if (w->event_queue[i].due_tick > tick) {
                if (kn != i) {
                    w->event_queue[kn] = w->event_queue[i];
                    if (s) s->queue_source[kn] = s->queue_source[i];
                }
                kn++;
            }
        }
        w->event_queue_n = kn;
        return;
    }

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
        if (w->inject != OM_BUG_SEQUENTIAL_DELTAS && w->inject != OM_BUG_TRIGGERS_READ_LIVE)
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

/* ---- manual event firing + ALG-49 character attachment (E-08/E-09) ---- */

/* Attaches char_id to mf if it names a living character actually in the
 * fired region: om_character_get_record succeeds, its region matches, and
 * its status is 0 (generational.c's GEN_STATUS_ACTIVE -- private to that
 * module, not exposed here, so compared by the ALWAYS_EXEMPT_VALUES literal
 * rather than a name events.c has no header access to). Skips duplicates
 * and stops at OM_EVT_MAX_ATTACHED. char_id 0 is generational.c's own
 * "none" sentinel (om_faction_supreme_commander / om_region_regional_commander
 * return 0 for no commander), so it is never a real character. */
static void evt_manual_try_attach(om_evt_manual_fire *mf, const om_world *w, uint32_t char_id) {
    if (char_id == 0 || mf->n_attached >= OM_EVT_MAX_ATTACHED) return;
    for (uint32_t i = 0; i < mf->n_attached; i++) {
        if (mf->attached[i] == char_id) return;
    }
    om_character_record rec;
    if (om_character_get_record(w, char_id, &rec) != 0) return;
    if (rec.region != mf->region_idx) return;
    if (rec.status != 0) return;
    mf->attached[mf->n_attached++] = char_id;
}

static void evt_manual_attach_lineage(om_evt_manual_fire *mf, const om_world *w) {
    uint32_t n = om_character_count(w);
    for (uint32_t i = 0; i < n && mf->n_attached < OM_EVT_MAX_ATTACHED; i++) {
        uint32_t id = om_character_id_at(w, i);
        om_character_record rec;
        if (om_character_get_record(w, id, &rec) != 0 || rec.lineage_id == 0) continue;
        evt_manual_try_attach(mf, w, id);
    }
}

uint32_t om_event_fire_manual(om_world *w, uint32_t region_idx, uint32_t tier) {
    if (!w || region_idx >= w->n_regions) return 0;
    om_evt_state *s = evt_ensure(w);
    if (!s || s->manual_n >= OM_EVT_MANUAL_CAP) return 0;

    om_evt_manual_fire *mf = &s->manual[s->manual_n++];
    memset(mf, 0, sizeof(*mf));
    mf->id = ++s->manual_next_id;
    mf->region_idx = region_idx;
    mf->tier = tier;

    if (tier >= OM_CHARACTER_ATTACHMENT_TIER_THRESHOLD) {
        evt_manual_try_attach(mf, w, om_region_regional_commander(w, region_idx));
        int32_t owner = w->regions[region_idx].faction_id;
        if (owner >= 0) {
            evt_manual_try_attach(mf, w, om_faction_supreme_commander(w, owner));
        }
        evt_manual_attach_lineage(mf, w);
    }

    return mf->id;
}

static om_evt_manual_fire *evt_manual_find(om_evt_state *s, uint32_t event_id) {
    for (uint32_t i = 0; i < s->manual_n; i++) {
        if (s->manual[i].id == event_id) return &s->manual[i];
    }
    return NULL;
}

uint32_t om_event_get_attached_character(const om_world *w, uint32_t event, uint32_t p1) {
    om_evt_state *s = evt_find(w);
    if (!s) return 0;
    om_evt_manual_fire *mf = evt_manual_find(s, event);
    if (!mf || p1 >= mf->n_attached) return 0;
    return mf->attached[p1];
}

/* ---- save/load slot (S-111, csrc/save.c OM_SAVE_SLOT_EVENTS) ----
 * Blob: n_regions rows (min(w->n_regions, OM_EVT_MAX_REGIONS)) by n_templates
 * columns for the per-(region, template) tables, then the queue's parallel
 * source array, the tick logs and the manual-fire records, each as a count
 * plus that many entries. Explicit little-endian scalars, no struct memcpy.
 * The pending queue itself (w->event_queue) and telegraphs are written by
 * csrc/save.c's body; only queue_source lives here. A zero-length blob
 * restores "no events state", the same as a world that never loaded events. */

typedef struct {
    uint8_t *buf; /* NULL: size-only pass */
    uint32_t pos;
} evt_wr;

static void evt_put(evt_wr *o, uint64_t v, uint32_t width) {
    if (o->buf) {
        for (uint32_t i = 0; i < width; i++) {
            o->buf[o->pos + i] = (uint8_t)((v >> (OM_SAVE_BYTE_BITS * i)) & OM_SAVE_BYTE_MASK);
        }
    }
    o->pos += width;
}

static void evt_put_u8(evt_wr *o, uint64_t v)  { evt_put(o, v, (uint32_t)sizeof(uint8_t)); }
static void evt_put_u32(evt_wr *o, uint64_t v) { evt_put(o, v, (uint32_t)sizeof(uint32_t)); }
static void evt_put_u64(evt_wr *o, uint64_t v) { evt_put(o, v, (uint32_t)sizeof(uint64_t)); }

static void evt_put_f64(evt_wr *o, double d) {
    uint64_t bits;
    memcpy(&bits, &d, sizeof(bits));
    evt_put_u64(o, bits);
}

static void evt_put_name(evt_wr *o, const char *name) {
    if (o->buf) memcpy(o->buf + o->pos, name, OM_TEMPLATE_NAME);
    o->pos += OM_TEMPLATE_NAME;
}

static void evt_put_template(evt_wr *o, const om_event_template *t) {
    evt_put_u32(o, t->id);
    evt_put_name(o, t->name);
    evt_put_u32(o, t->trigger_kind);
    evt_put_u32(o, t->trigger_field);
    evt_put_f64(o, t->threshold);
    evt_put_f64(o, t->prob_base);
    evt_put_f64(o, t->prob_exponent);
    evt_put_u32(o, t->cooldown_ticks);
    evt_put_u32(o, t->n_spawns);
    for (uint32_t f = 0; f < OM_F_COUNT; f++) evt_put_f64(o, t->effect[f]);
    for (uint32_t j = 0; j < OM_MAX_SPAWNS; j++) {
        const om_spawn *sp = &t->spawns[j];
        evt_put_u32(o, sp->template_id);
        evt_put_u32(o, sp->delay_min);
        evt_put_u32(o, sp->delay_max);
        evt_put_u32(o, sp->cond_kind);
        evt_put_u32(o, sp->cond_field);
        evt_put_f64(o, sp->probability);
        evt_put_f64(o, sp->cond_value);
    }
    evt_put_u32(o, t->exclusion_tag);
    evt_put_u32(o, t->creates_faction);
    evt_put_u32(o, t->admin_chain_step);
}

static void evt_save_body(const om_world *w, const om_evt_state *s, evt_wr *o) {
    uint32_t nreg = (w->n_regions < OM_EVT_MAX_REGIONS) ? w->n_regions : OM_EVT_MAX_REGIONS;
    uint32_t nq = (w->event_queue_n < OM_EVT_QUEUE_CAP) ? w->event_queue_n : OM_EVT_QUEUE_CAP;

    evt_put_u32(o, s->n_templates);
    evt_put_u32(o, s->launch_count);
    evt_put_u32(o, nreg);
    evt_put_u32(o, (uint32_t)s->chain_counter);
    for (uint32_t t = 0; t < s->n_templates; t++) {
        evt_put_template(o, &s->templates[t]);
        evt_put_u32(o, (uint32_t)s->significance_tier[t]);
    }
    for (uint32_t r = 0; r < nreg; r++) {
        for (uint32_t t = 0; t < s->n_templates; t++) {
            evt_put_f64(o, s->noise[r][t]);
            evt_put_u8(o, s->breached[r][t] ? 1 : 0);
            evt_put_u64(o, (uint64_t)s->last_fired[r][t]);
        }
        evt_put_u32(o, s->faction_pending[r]);
        for (uint32_t f = 0; f < OM_F_COUNT; f++) evt_put_f64(o, s->applied_delta[r][f]);
        evt_put_u8(o, s->touched[r] ? 1 : 0);
    }

    evt_put_u32(o, nq);
    for (uint32_t i = 0; i < nq; i++) evt_put_u32(o, s->queue_source[i]);

    evt_put_u32(o, s->fired_n);
    for (uint32_t i = 0; i < s->fired_n; i++) {
        const om_fired_event *e = &s->fired[i];
        evt_put_u64(o, e->tick);
        evt_put_u32(o, e->region_idx);
        evt_put_u32(o, e->template_id);
        evt_put_u32(o, (uint32_t)e->chain_tag);
        evt_put_u32(o, e->source);
        for (uint32_t f = 0; f < OM_F_COUNT; f++) evt_put_f64(o, e->delta[f]);
        evt_put_f64(o, e->draw);
        evt_put_u32(o, e->creates_faction);
        evt_put_u32(o, e->n_spawned);
    }
    evt_put_u32(o, s->pruned_n);
    for (uint32_t i = 0; i < s->pruned_n; i++) {
        const om_pruned_event *e = &s->pruned[i];
        evt_put_u64(o, e->tick);
        evt_put_u32(o, e->region_idx);
        evt_put_u32(o, e->template_id);
        evt_put_u32(o, (uint32_t)e->chain_tag);
        evt_put_u32(o, e->cond_kind);
        evt_put_u32(o, e->cond_field);
        evt_put_f64(o, e->cond_value);
        evt_put_f64(o, e->field_value);
    }
    evt_put_u32(o, s->delayed_n);
    for (uint32_t i = 0; i < s->delayed_n; i++) {
        const om_delayed_event *e = &s->delayed[i];
        evt_put_u64(o, e->tick);
        evt_put_u32(o, e->region_idx);
        evt_put_u32(o, e->template_id);
        evt_put_u32(o, (uint32_t)e->chain_tag);
        evt_put_u32(o, e->exclusion_tag);
        evt_put_u32(o, e->kept_template_id);
        evt_put_u64(o, e->new_due);
    }

    evt_put_u32(o, s->manual_n);
    evt_put_u32(o, s->manual_next_id);
    for (uint32_t i = 0; i < s->manual_n; i++) {
        const om_evt_manual_fire *m = &s->manual[i];
        evt_put_u32(o, m->id);
        evt_put_u32(o, m->region_idx);
        evt_put_u32(o, m->tier);
        evt_put_u32(o, m->n_attached);
        for (uint32_t k = 0; k < m->n_attached; k++) evt_put_u32(o, m->attached[k]);
    }
}

static uint32_t evt_save_size(const om_world *w) {
    const om_evt_state *s = evt_find(w);
    if (!s) return 0;
    evt_wr o = { NULL, 0 };
    evt_save_body(w, s, &o);
    return o.pos;
}

static void evt_save_write(const om_world *w, uint8_t *out) {
    const om_evt_state *s = evt_find(w);
    if (!s || !out) return;
    evt_wr o = { out, 0 };
    evt_save_body(w, s, &o);
}

typedef struct {
    const uint8_t *p;
    uint32_t len;
    uint32_t pos;
    int ok;
} evt_rd;

static uint64_t evt_get(evt_rd *r, uint32_t width) {
    uint64_t v = 0;
    if (!r->ok || width > r->len - r->pos) { r->ok = 0; return 0; }
    for (uint32_t i = 0; i < width; i++) {
        v |= ((uint64_t)r->p[r->pos + i]) << (OM_SAVE_BYTE_BITS * i);
    }
    r->pos += width;
    return v;
}

static uint8_t  evt_get_u8(evt_rd *r)  { return (uint8_t)evt_get(r, (uint32_t)sizeof(uint8_t)); }
static uint32_t evt_get_u32(evt_rd *r) { return (uint32_t)evt_get(r, (uint32_t)sizeof(uint32_t)); }
static uint64_t evt_get_u64(evt_rd *r) { return evt_get(r, (uint32_t)sizeof(uint64_t)); }

static double evt_get_f64(evt_rd *r) {
    uint64_t bits = evt_get_u64(r);
    double d;
    memcpy(&d, &bits, sizeof(d));
    return d;
}

/* Reads a count and fails the reader when it exceeds cap. */
static uint32_t evt_get_count(evt_rd *r, uint32_t cap) {
    uint32_t n = (uint32_t)evt_get_u32(r);
    if (n > cap) { r->ok = 0; return 0; }
    return n;
}

static void evt_get_template(evt_rd *r, om_event_template *t) {
    memset(t, 0, sizeof(*t));
    t->id = (uint32_t)evt_get_u32(r);
    for (uint32_t i = 0; i < OM_TEMPLATE_NAME; i++) t->name[i] = (char)evt_get_u8(r);
    t->trigger_kind = (uint32_t)evt_get_u32(r);
    t->trigger_field = (uint32_t)evt_get_u32(r);
    t->threshold = evt_get_f64(r);
    t->prob_base = evt_get_f64(r);
    t->prob_exponent = evt_get_f64(r);
    t->cooldown_ticks = (uint32_t)evt_get_u32(r);
    t->n_spawns = evt_get_count(r, OM_MAX_SPAWNS);
    for (uint32_t f = 0; f < OM_F_COUNT; f++) t->effect[f] = evt_get_f64(r);
    for (uint32_t j = 0; j < OM_MAX_SPAWNS; j++) {
        om_spawn *sp = &t->spawns[j];
        sp->template_id = (uint32_t)evt_get_u32(r);
        sp->delay_min = (uint32_t)evt_get_u32(r);
        sp->delay_max = (uint32_t)evt_get_u32(r);
        sp->cond_kind = (uint32_t)evt_get_u32(r);
        sp->cond_field = (uint32_t)evt_get_u32(r);
        sp->probability = evt_get_f64(r);
        sp->cond_value = evt_get_f64(r);
    }
    t->exclusion_tag = (uint32_t)evt_get_u32(r);
    t->creates_faction = (uint32_t)evt_get_u32(r);
    t->admin_chain_step = (uint32_t)evt_get_u32(r);
}

static void evt_load_body(evt_rd *r, om_evt_state *s) {
    s->n_templates = evt_get_count(r, OM_MAX_TEMPLATES);
    s->launch_count = evt_get_count(r, s->n_templates);
    uint32_t nreg = evt_get_count(r, OM_EVT_MAX_REGIONS);
    s->chain_counter = (int32_t)evt_get_u32(r);
    for (uint32_t t = 0; t < s->n_templates && r->ok; t++) {
        evt_get_template(r, &s->templates[t]);
        s->significance_tier[t] = (int32_t)evt_get_u32(r);
    }
    for (uint32_t i = 0; i < nreg && r->ok; i++) {
        for (uint32_t t = 0; t < s->n_templates && r->ok; t++) {
            s->noise[i][t] = evt_get_f64(r);
            s->breached[i][t] = (int)evt_get_u8(r);
            s->last_fired[i][t] = (int64_t)evt_get_u64(r);
        }
        s->faction_pending[i] = (uint32_t)evt_get_u32(r);
        for (uint32_t f = 0; f < OM_F_COUNT; f++) s->applied_delta[i][f] = evt_get_f64(r);
        s->touched[i] = (int)evt_get_u8(r);
    }

    uint32_t nq = evt_get_count(r, OM_EVT_QUEUE_CAP);
    for (uint32_t i = 0; i < nq && r->ok; i++) s->queue_source[i] = (uint32_t)evt_get_u32(r);

    s->fired_n = evt_get_count(r, OM_EVT_LOG_CAP);
    for (uint32_t i = 0; i < s->fired_n && r->ok; i++) {
        om_fired_event *e = &s->fired[i];
        e->tick = evt_get_u64(r);
        e->region_idx = (uint32_t)evt_get_u32(r);
        e->template_id = (uint32_t)evt_get_u32(r);
        e->chain_tag = (int32_t)evt_get_u32(r);
        e->source = (uint32_t)evt_get_u32(r);
        for (uint32_t f = 0; f < OM_F_COUNT; f++) e->delta[f] = evt_get_f64(r);
        e->draw = evt_get_f64(r);
        e->creates_faction = (uint32_t)evt_get_u32(r);
        e->n_spawned = (uint32_t)evt_get_u32(r);
    }
    s->pruned_n = evt_get_count(r, OM_EVT_LOG_CAP);
    for (uint32_t i = 0; i < s->pruned_n && r->ok; i++) {
        om_pruned_event *e = &s->pruned[i];
        e->tick = evt_get_u64(r);
        e->region_idx = (uint32_t)evt_get_u32(r);
        e->template_id = (uint32_t)evt_get_u32(r);
        e->chain_tag = (int32_t)evt_get_u32(r);
        e->cond_kind = (uint32_t)evt_get_u32(r);
        e->cond_field = (uint32_t)evt_get_u32(r);
        e->cond_value = evt_get_f64(r);
        e->field_value = evt_get_f64(r);
    }
    s->delayed_n = evt_get_count(r, OM_EVT_LOG_CAP);
    for (uint32_t i = 0; i < s->delayed_n && r->ok; i++) {
        om_delayed_event *e = &s->delayed[i];
        e->tick = evt_get_u64(r);
        e->region_idx = (uint32_t)evt_get_u32(r);
        e->template_id = (uint32_t)evt_get_u32(r);
        e->chain_tag = (int32_t)evt_get_u32(r);
        e->exclusion_tag = (uint32_t)evt_get_u32(r);
        e->kept_template_id = (uint32_t)evt_get_u32(r);
        e->new_due = evt_get_u64(r);
    }

    s->manual_n = evt_get_count(r, OM_EVT_MANUAL_CAP);
    s->manual_next_id = (uint32_t)evt_get_u32(r);
    for (uint32_t i = 0; i < s->manual_n && r->ok; i++) {
        om_evt_manual_fire *m = &s->manual[i];
        m->id = (uint32_t)evt_get_u32(r);
        m->region_idx = (uint32_t)evt_get_u32(r);
        m->tier = (uint32_t)evt_get_u32(r);
        m->n_attached = evt_get_count(r, OM_EVT_MAX_ATTACHED);
        for (uint32_t k = 0; k < m->n_attached && r->ok; k++) m->attached[k] = (uint32_t)evt_get_u32(r);
    }
}

static int evt_save_read(om_world *w, const uint8_t *buf, uint32_t len) {
    if (!w) return -1;
    if (len == 0) {
        if (w->events_state && w->events_state_free) w->events_state_free(w->events_state);
        w->events_state = NULL;
        return 0;
    }
    if (!buf) return -1;
    om_evt_state *s = calloc(1, sizeof(om_evt_state));
    if (!s) return -1;
    evt_state_reset_fields(s);
    evt_rd r = { buf, len, 0, 1 };
    evt_load_body(&r, s);
    if (!r.ok || r.pos != len) {
        free(s);
        return -1;
    }
    if (w->events_state && w->events_state_free) w->events_state_free(w->events_state);
    w->events_state = s;
    w->events_state_free = free;
    w->events_state_size = evt_save_size;
    w->events_state_write = evt_save_write;
    w->events_state_read = evt_save_read;
    return 0;
}

int32_t om_event_template_significance_tier(const om_world *w, uint32_t template_id) {
    static const int32_t launch_tier[TID_LAUNCH_COUNT] = {
        [TID_GARRISON_COLLAPSE] = OM_EVENT_TIER_EVT_GARRISON_COLLAPSE,
        [TID_BORDER_INCURSION] = OM_EVENT_TIER_EVT_BORDER_INCURSION,
        [TID_EMERGENCY_LEVY] = OM_EVENT_TIER_EVT_EMERGENCY_LEVY,
        [TID_REGIONAL_REVOLT] = OM_EVENT_TIER_EVT_REGIONAL_REVOLT,
        [TID_REVOLT_CRUSHED] = OM_EVENT_TIER_EVT_REVOLT_CRUSHED,
        [TID_REVOLT_ENTRENCHED] = OM_EVENT_TIER_EVT_REVOLT_ENTRENCHED,
        [TID_TRADE_BOOM] = OM_EVENT_TIER_EVT_TRADE_BOOM,
        [TID_PROSPERITY_UNREST] = OM_EVENT_TIER_EVT_PROSPERITY_UNREST,
        [TID_POPULATION_CRISIS] = OM_EVENT_TIER_EVT_POPULATION_CRISIS,
        [TID_RESISTANCE_MOVEMENT] = OM_EVENT_TIER_EVT_RESISTANCE_MOVEMENT,
        [TID_CONQUEST_UNREST] = OM_EVENT_TIER_CONQUEST_UNREST,
        [TID_LABOR_SHORTAGE] = OM_EVENT_TIER_EVT_LABOR_SHORTAGE,
        [TID_IMMIGRATION_WAVE] = OM_EVENT_TIER_EVT_IMMIGRATION_WAVE,
        [TID_INFRASTRUCTURE_DECAY] = OM_EVENT_TIER_EVT_INFRASTRUCTURE_DECAY,
        [TID_MILITARY_BUILDUP] = OM_EVENT_TIER_EVT_MILITARY_BUILDUP,
        [TID_WAR_WEARINESS] = OM_EVENT_TIER_EVT_WAR_WEARINESS,
        [TID_CULTURAL_RENAISSANCE] = OM_EVENT_TIER_EVT_CULTURAL_RENAISSANCE,
        [TID_FAMINE] = OM_EVENT_TIER_EVT_FAMINE,
        [TID_FAMINE_RELIEF] = OM_EVENT_TIER_EVT_FAMINE_RELIEF,
        [TID_DIPLOMATIC_INCIDENT] = OM_EVENT_TIER_EVT_DIPLOMATIC_INCIDENT,
        [TID_HARVEST_SURPLUS] = OM_EVENT_TIER_EVT_HARVEST_SURPLUS,
        [TID_ADMIN_SEPARATIST] = OM_EVENT_TIER_EVT_ADMIN_SEPARATIST,
        [TID_ADMIN_POLITICAL_CRISIS] = OM_EVENT_TIER_EVT_ADMIN_POLITICAL_CRISIS,
        [TID_ADMIN_POPULAR_SUPPORT] = OM_EVENT_TIER_EVT_ADMIN_POPULAR_SUPPORT,
        [TID_ADMIN_MILITARY_DEFECTION] = OM_EVENT_TIER_EVT_ADMIN_MILITARY_DEFECTION,
        [TID_ADMIN_BREAKAWAY] = OM_EVENT_TIER_EVT_ADMIN_BREAKAWAY,
    };
    om_evt_state *s = evt_find(w);
    if (!s || template_id >= s->n_templates) return -1;
    if (template_id < TID_LAUNCH_COUNT) return launch_tier[template_id];
    return s->significance_tier[template_id];
}
