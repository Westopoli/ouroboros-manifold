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
#include "om_constants.h"
#include <stddef.h>
#include <string.h>

/* B6 status: om_world/om_region carry no fields for a revolt/reversion/
 * absorption tick log, per-faction created_tick, per-faction event-window
 * counts, per-faction conquered_this_tick, or per-region previous_owner
 * (docs/bible/algorithms.md ALG-41..44). Those are om_internal.h additions
 * (out of scope for this build card -- allowed_files is csrc/lifecycle.c
 * only). Proposed diff, to struct om_world in om_internal.h:
 *
 *   om_revolt_record     revolts[64];      uint32_t revolts_n;
 *   om_reversion_record  reversions[64];   uint32_t reversions_n;
 *   om_absorption_record absorptions[64];  uint32_t absorptions_n;
 *   uint64_t faction_created_tick[OM_MAX_FACTIONS];
 *   int      faction_conquered_this_tick[OM_MAX_FACTIONS];
 *   uint32_t faction_window_total[OM_MAX_FACTIONS];
 *   uint32_t faction_window_revolts[OM_MAX_FACTIONS];
 *   uint32_t faction_window_attacks[OM_MAX_FACTIONS];
 *   uint32_t faction_window_colonizations[OM_MAX_FACTIONS];
 *   int32_t *region_previous_owner;   -- lazy calloc'd to -1, like region_held_since
 *
 * Until that lands, om_faction_set_created_tick, om_faction_set_event_window_counts,
 * om_faction_mark_conquered_this_tick, om_faction_phase, om_region_previous_owner,
 * om_region_set_previous_owner, om_tick_absorptions, om_tick_reversions, and
 * om_tick_revolts stay the original STUB bodies below: there is nowhere to
 * store what they would be given. Every S-053 rule and most of S-049/S-050/
 * S-051 need one of these fields; see the B6 report for the test-by-test
 * breakdown. */

/* ALG-41 breakaway creation. Fires from the E-04 hook
 * om_region_faction_creation_pending (csrc/events.c, card B1, itself a STUB
 * today, so this loop is a no-op until B1 lands -- wired here so it starts
 * working the moment it does). Admin-chain pruning (ALG-41 "pruned if...")
 * is E-04's job: by the time the hook fires, that check has already run. */
#define LC_TEMPLATE_REVOLT_ENTRENCHED 100
#define LC_TEMPLATE_ADMIN_BREAKAWAY   101

static const om_archetype LC_ADMIN_BREAKAWAY_ARCHETYPES[5] = {
    OM_ARCH_CONQUEROR, OM_ARCH_FORTIFIER, OM_ARCH_WARLORD,
    OM_ARCH_OPPORTUNIST, OM_ARCH_SCHISM
};
#define LC_ADMIN_ARCHETYPE_COUNT \
    (sizeof(LC_ADMIN_BREAKAWAY_ARCHETYPES) / sizeof(LC_ADMIN_BREAKAWAY_ARCHETYPES[0]))

static int32_t lc_free_faction_slot(const om_world *w) {
    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f])
            return f;
    }
    return -1;
}

static void lc_split_region(om_region *rg) {
    rg->military -= rg->military * OM_REVOLT_MILITARY_STEAL;
    rg->economy  -= rg->economy  * OM_REVOLT_ECONOMY_STEAL;
    if (rg->population < OM_REVOLT_BREAKAWAY_POP_FLOOR)
        rg->population = OM_REVOLT_BREAKAWAY_POP_FLOOR;
    /* ALG-41 also caps tension at 40.0 and floors economy at 20.0 here;
     * om_constants.h has no OM_REVOLT_TENSION_CAP / OM_REVOLT_ECONOMY_FLOOR
     * for those two literals (card_lint forbids inlining a bare number), so
     * they are missing pending that constant addition. */
}

static void lc_borderize_edges(om_world *w, uint32_t region_idx) {
    for (uint32_t j = 0; j < w->n_regions; j++) {
        if (j == region_idx)
            continue;
        om_edge_type et;
        if (!om_region_edge(w, region_idx, j, &et))
            continue;
        om_region_set_edge(w, region_idx, j, OM_EDGE_BORDER);
    }
}

static void lc_resolve_faction_creation(om_world *w, uint32_t region_idx, uint32_t template_id) {
    int32_t old_owner = w->regions[region_idx].faction_id;
    if (old_owner < 0 || old_owner >= OM_MAX_FACTIONS)
        return;

    int is_admin = (template_id == LC_TEMPLATE_ADMIN_BREAKAWAY);

    if (!is_admin) {
        double rate = OM_REVOLT_SUCCESS_RANGE_LO +
            (OM_REVOLT_SUCCESS_RANGE_HI - OM_REVOLT_SUCCESS_RANGE_LO) * om_rng_draw(w);
        double check = om_rng_draw(w);
        if (check > rate)
            return;
        if (w->regions[region_idx].population < OM_REVOLT_BREAKAWAY_POP_FLOOR)
            return;
    }

    int32_t new_fid = lc_free_faction_slot(w);
    if (new_fid < 0)
        return;

    om_archetype archetype;
    if (is_admin) {
        double pick = om_rng_draw(w);
        int idx = (int)(pick * (double)LC_ADMIN_ARCHETYPE_COUNT);
        if (idx < 0)
            idx = 0;
        if (idx >= (int)LC_ADMIN_ARCHETYPE_COUNT)
            idx = (int)LC_ADMIN_ARCHETYPE_COUNT - 1;
        archetype = LC_ADMIN_BREAKAWAY_ARCHETYPES[idx];
    } else {
        archetype = OM_ARCH_BREAKAWAY;
    }

    double parent_tech = w->faction_tech[old_owner];
    om_faction_set(w, new_fid, archetype, 0.0, parent_tech, -1.0);

    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f] || f == new_fid)
            continue;
        om_faction_set_stance(w, new_fid, f, OM_STANCE_HOSTILE);
        om_faction_set_stance(w, f, new_fid, OM_STANCE_HOSTILE);
    }

    lc_split_region(&w->regions[region_idx]);
    om_region_set_owner(w, region_idx, new_fid, (int64_t)w->tick);
    lc_borderize_edges(w, region_idx);

    /* ALG-41 also sets region.previous_faction = old_owner and appends an
     * om_revolt_record; ALG-43 latent loyalty then may revert this region
     * to a still-living previous owner. Both need the om_internal.h fields
     * proposed at the top of this file. */
}

void om_step_lifecycle(om_world *w) {
    if (!w)
        return;
    for (uint32_t r = 0; r < w->n_regions; r++) {
        uint32_t pending = om_region_faction_creation_pending(w, r);
        if (pending == 0)
            continue;
        lc_resolve_faction_creation(w, r, pending - 1);
    }
    /* ALG-42 zombie cleanup runs here once faction_created_tick and
     * faction_conquered_this_tick exist (see the proposed diff above); it
     * needs both to find a breakaway's age and skip one that conquered a
     * region this tick. */
}

/* ---- generated stubs from signatures.toml ---- */
int om_faction_is_active(const om_world *w, int32_t faction_id) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return 0;
    return w->faction_used[faction_id] ? 1 : 0;
}

void om_faction_mark_conquered_this_tick(om_world *w, int32_t faction_id) {
    /* STUB: needs faction_conquered_this_tick (proposed diff, top of file). */
    (void)w; (void)faction_id;
}

void om_faction_remove(om_world *w, int32_t faction_id) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return;

    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id == faction_id)
            om_region_set_owner(w, i, -1, -1);
    }

    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        w->faction_stance[faction_id][f] = (om_stance)-1;
        w->faction_stance[f][faction_id] = (om_stance)-1;
    }

    if (w->faction_used[faction_id]) {
        w->faction_used[faction_id] = 0;
        w->faction_n--;
    }
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
    if (!w)
        return 0;
    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f] || w->faction_archetype[f] != OM_ARCH_PLAYER)
            continue;
        if (om_faction_territory(w, f) == 0)
            return 1;
    }
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
    /* Q-054-01 deferred (R-054-01): the final era continues indefinitely. */
    (void)w;
    return 0;
}
int om_faction_phase(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}
/* ---- end generated stubs ---- */
