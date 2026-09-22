/* csrc/events.c — E-04 event library, triggers, queue resolution (E-04 build cards).
 * Skeleton written by the parent so the fenced suite fails red on assertions,
 * not on a missing symbol, and so the build harness has a file to read; every
 * body below is a STUB the build card replaces. */
/* PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).
 * Use exactly these member names; there are no others. Inventing a member
 * (previous_economy_osc, region_state, trace_enabled, adjacencies, faction_modifiers)
 * is a compile error and fails every test.
 * #define OM_MAX_NEIGHBORS 32
 * 
 * typedef struct {
 *     om_tier  tier;
 *     double   military, economy, tension, population;
 *     double   econ_phase, tension_phase;
 *     double   prev_econ_osc, prev_tension_osc;
 *     int32_t  faction_id;
 *     uint32_t neighbors[OM_MAX_NEIGHBORS];
 *     uint32_t n_neighbors;
 *     om_drift_row last_drift;
 * } om_region;
 * 
 * struct om_world {
 *     uint32_t n_regions;
 *     uint64_t seed;
 *     uint64_t tick;
 *     int      trace_on;
 *     int      inject;
 *     om_region *regions;
 *     double   faction_mod[OM_MAX_FACTIONS][OM_F_COUNT];
 *     om_trace_row *trace;
 *     uint64_t trace_len, trace_cap;
 * };
 */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>
#include <string.h>

void om_step_events(om_world *w) {
    /* STUB */
    (void)w;
}

void om_events_load_launch(om_world *w) {
    /* STUB */
    (void)w;
}

int om_events_load(om_world *w, const om_event_template *templates, uint32_t n) {
    /* STUB */
    (void)w; (void)templates; (void)n;
    return 0;
}

uint32_t om_event_template_count(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

int om_event_template_get(const om_world *w, uint32_t id, om_event_template *out) {
    /* STUB */
    (void)w; (void)id; (void)out;
    return 0;
}

int32_t om_event_template_by_name(const om_world *w, const char *name) {
    /* STUB */
    (void)w; (void)name;
    return 0;
}

void om_event_roll_noise(om_world *w) {
    /* STUB */
    (void)w;
}

void om_event_set_noise(om_world *w, uint32_t region_idx, uint32_t template_id, double offset) {
    /* STUB */
    (void)w; (void)region_idx; (void)template_id; (void)offset;
}

double om_event_noise(const om_world *w, uint32_t region_idx, uint32_t template_id) {
    /* STUB */
    (void)w; (void)region_idx; (void)template_id;
    return 0.0;
}

int om_event_breached(const om_world *w, uint32_t region_idx, uint32_t template_id) {
    /* STUB */
    (void)w; (void)region_idx; (void)template_id;
    return 0;
}

int64_t om_event_last_fired(const om_world *w, uint32_t region_idx, uint32_t template_id) {
    /* STUB */
    (void)w; (void)region_idx; (void)template_id;
    return 0;
}

int32_t om_chain_counter(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

uint32_t om_region_faction_creation_pending(const om_world *w, uint32_t region_idx) {
    /* STUB */
    (void)w; (void)region_idx;
    return 0;
}

int om_event_queue_external(om_world *w, uint32_t region_idx, uint32_t template_id, uint64_t due_tick, double probability, int32_t source_faction, uint32_t chain_length) {
    /* STUB */
    (void)w; (void)region_idx; (void)template_id; (void)due_tick; (void)probability; (void)source_faction; (void)chain_length;
    return 0;
}

uint32_t om_tick_events(const om_world *w, om_fired_event *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_pruned(const om_world *w, om_pruned_event *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_delayed(const om_world *w, om_delayed_event *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

int om_region_event_delta(const om_world *w, uint32_t region_idx, double out[OM_F_COUNT]) {
    /* STUB */
    (void)w; (void)region_idx; (void)out;
    return 0;
}

/* ---- generated stubs from signatures.toml ---- */
uint32_t om_event_fire_manual(om_world *w, uint32_t region_idx, uint32_t tier) {
    /* STUB */
    (void)w; (void)region_idx; (void)tier;
    return 0;
}

uint32_t om_event_get_attached_character(const om_world *w, uint32_t event, uint32_t p1) {
    /* STUB */
    (void)w; (void)event; (void)p1;
    return 0;
}
/* ---- end generated stubs ---- */
