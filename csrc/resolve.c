/* csrc/resolve.c — E-05 intent resolution: reinforce, attack, damage, conquest, colonize (build card 204).
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
#include <math.h>
#include <stddef.h>
#include <string.h>

uint32_t om_tick_attacks(const om_world *w, om_attack_result *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_reinforces(const om_world *w, om_reinforce *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_colonizations(const om_world *w, om_colonize_result *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_event_queue(const om_world *w, om_queued_event *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

int om_intent_inject(om_world *w, int32_t faction_id, om_action action, uint32_t target_idx,
                     uint32_t source_idx, double commit, om_attack_mode mode) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS || !w->faction_used[faction_id]) return -1;
    if (target_idx >= w->n_regions || source_idx >= w->n_regions) return -1;
    if (w->regions[source_idx].faction_id != faction_id) return -1;
    if (commit > w->faction_budget[faction_id]) return -1;

    if (w->decisions_n >= 64) return -1;
    om_decision *d = &w->decisions[w->decisions_n++];
    memset(d, 0, sizeof(*d));
    d->tick = w->tick;
    d->faction_id = faction_id;
    d->action = (uint32_t)action;
    d->target_idx = target_idx;
    d->source_idx = source_idx;
    d->commit = commit;
    d->mode = (uint32_t)mode;
    return 0;
}

void om_region_add_damage(om_world *w, uint32_t idx, double military_loss, double economy_loss, uint64_t tick) {
    /* STUB */
    (void)w; (void)idx; (void)military_loss; (void)economy_loss; (void)tick;
}

double om_region_damage_history(const om_world *w, uint32_t idx) {
    /* STUB */
    (void)w; (void)idx;
    return 0.0;
}

void om_step_telegraphs(om_world *w) {
    /* STUB */
    (void)w;
}

void om_step_reinforce(om_world *w) {
    /* STUB */
    (void)w;
}

void om_step_resolve(om_world *w) {
    /* STUB */
    (void)w;
}
