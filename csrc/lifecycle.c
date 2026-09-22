/* csrc/lifecycle.c — E-07 civilizational lifecycle (tick wiring only; the
 * epic's own zombie-cleanup and coherence-ledger math lands with card B6).
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

void om_step_lifecycle(om_world *w) {
    /* STUB */
    (void)w;
}

/* ---- generated stubs from signatures.toml ---- */
int om_faction_is_active(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

void om_faction_mark_conquered_this_tick(om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
}

void om_faction_remove(om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
}

void om_faction_set_created_tick(om_world *w, int32_t faction_id, uint64_t tick) {
    /* STUB */
    (void)w; (void)faction_id; (void)tick;
}

void om_faction_set_event_window_counts(om_world *w, int32_t faction_id, uint32_t total_events, uint32_t revolts, uint32_t attacks, uint32_t colonizations) {
    /* STUB */
    (void)w; (void)faction_id; (void)total_events; (void)revolts; (void)attacks; (void)colonizations;
}

int om_player_faction_collapsed(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

int32_t om_region_previous_owner(const om_world *w, uint32_t idx) {
    /* STUB */
    (void)w; (void)idx;
    return 0;
}

void om_region_set_previous_owner(om_world *w, uint32_t idx, int32_t faction_id) {
    /* STUB */
    (void)w; (void)idx; (void)faction_id;
}

uint32_t om_tick_absorptions(const om_world *w, om_absorption_record *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_reversions(const om_world *w, om_reversion_record *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_tick_revolts(const om_world *w, om_revolt_record *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

int om_world_is_terminal(const om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}
/* ---- end generated stubs ---- */
