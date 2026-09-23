/* csrc/lifecycle.c — E-07 civilizational lifecycle (ALG-41..44,
 * docs/bible/epics/E-07-civilizational-lifecycle.md). */
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
#include <stdlib.h>
#include <string.h>

#define LC_TEMPLATE_ADMIN_BREAKAWAY 101

#define LC_PHASE_FRAGMENTATION 0
#define LC_PHASE_OVEREXTENSION 1
#define LC_PHASE_CONFLICT      2
#define LC_PHASE_EXPANSION     3
#define LC_PHASE_CONSOLIDATION 4
#define LC_PHASE_EQUILIBRIUM   5

static const om_archetype LC_ADMIN_BREAKAWAY_ARCHETYPES[5] = {
    OM_ARCH_CONQUEROR, OM_ARCH_FORTIFIER, OM_ARCH_WARLORD,
    OM_ARCH_OPPORTUNIST, OM_ARCH_SCHISM
};
#define LC_ADMIN_ARCHETYPE_COUNT \
    (sizeof(LC_ADMIN_BREAKAWAY_ARCHETYPES) / sizeof(LC_ADMIN_BREAKAWAY_ARCHETYPES[0]))

int32_t om_region_previous_owner(const om_world *w, uint32_t idx) {
    if (!w || idx >= w->n_regions || w->region_previous_owner == NULL)
        return -1;
    return w->region_previous_owner[idx];
}

void om_region_set_previous_owner(om_world *w, uint32_t idx, int32_t faction_id) {
    if (!w || idx >= w->n_regions)
        return;
    if (w->region_previous_owner == NULL) {
        w->region_previous_owner = malloc(w->n_regions * sizeof(int32_t));
        if (!w->region_previous_owner)
            return;
        for (uint32_t i = 0; i < w->n_regions; i++)
            w->region_previous_owner[i] = -1;
    }
    w->region_previous_owner[idx] = faction_id;
}

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
    if (rg->tension > OM_REVOLT_TENSION_CAP)
        rg->tension = OM_REVOLT_TENSION_CAP;
    if (rg->population < OM_REVOLT_BREAKAWAY_POP_FLOOR)
        rg->population = OM_REVOLT_BREAKAWAY_POP_FLOOR;
    if (rg->economy < OM_REVOLT_ECONOMY_FLOOR)
        rg->economy = OM_REVOLT_ECONOMY_FLOOR;
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

static void lc_log_revolt(om_world *w, uint32_t region_idx, int32_t original_faction,
                           double success_rate, double draw, uint32_t faction_created,
                           int32_t new_faction_id, double military_stolen,
                           double economy_stolen, int32_t reverted_faction) {
    if (w->lc_revolts_n >= OM_MAX_REGIONS)
        return;
    om_revolt_record *rec = &w->lc_revolts[w->lc_revolts_n++];
    rec->tick = w->tick;
    rec->region_idx = region_idx;
    rec->original_faction = original_faction;
    rec->success_rate = success_rate;
    rec->draw = draw;
    rec->faction_created = faction_created;
    rec->new_faction_id = new_faction_id;
    rec->military_stolen = military_stolen;
    rec->economy_stolen = economy_stolen;
    rec->reverted_faction = reverted_faction;
}

static void lc_log_reversion(om_world *w, uint32_t region_idx, int32_t original_faction,
                              int32_t restored_faction, double military_stolen,
                              double economy_stolen) {
    if (w->lc_reversions_n >= OM_MAX_REGIONS)
        return;
    om_reversion_record *rec = &w->lc_reversions[w->lc_reversions_n++];
    rec->tick = w->tick;
    rec->region_idx = region_idx;
    rec->original_faction = original_faction;
    rec->restored_faction = restored_faction;
    rec->military_stolen = military_stolen;
    rec->economy_stolen = economy_stolen;
}

/* ALG-41 breakaway creation, fired from the E-04 hook
 * om_region_faction_creation_pending. Admin-chain pruning (ALG-41
 * "pruned if...") is E-04's job: by the time the hook fires, that check has
 * already run, so old_owner here is always the chain's live source. */
static void lc_resolve_faction_creation(om_world *w, uint32_t region_idx, uint32_t template_id) {
    om_region *rg = &w->regions[region_idx];
    int32_t old_owner = rg->faction_id;
    if (old_owner < 0 || old_owner >= OM_MAX_FACTIONS)
        return;

    int is_admin = (template_id == LC_TEMPLATE_ADMIN_BREAKAWAY);
    double rate = 1.0;
    double check = 0.0;

    if (!is_admin) {
        rate = OM_REVOLT_SUCCESS_RANGE_LO +
            (OM_REVOLT_SUCCESS_RANGE_HI - OM_REVOLT_SUCCESS_RANGE_LO) * om_rng_draw(w);
        check = om_rng_draw(w);
        if (check > rate) {
            lc_log_revolt(w, region_idx, old_owner, rate, check, 0, -1, 0.0, 0.0, -1);
            return;
        }
        if (rg->population < OM_REVOLT_BREAKAWAY_POP_FLOOR) {
            lc_log_revolt(w, region_idx, old_owner, rate, check, 0, -1, 0.0, 0.0, -1);
            return;
        }
    }

    /* ALG-43 latent loyalty: only meaningful when the region still has a
     * living previous owner different from the one revolting, within the
     * window. The draw itself is made only once those two hold, so the
     * existence check can veto a draw already spent (matches the doc's
     * "..., one draw < 0.5, and the previous owner still exists"). */
    int32_t prev = om_region_previous_owner(w, region_idx);
    int64_t held_since = om_region_held_since(w, region_idx);
    int64_t age = (int64_t)w->tick - held_since;
    if (prev >= 0 && prev != old_owner && age <= OM_LATENT_LOYALTY_TICKS) {
        double reversion_draw = om_rng_draw(w);
        if (reversion_draw < OM_LATENT_LOYALTY_REVERT_CHANCE && om_faction_is_active(w, prev)) {
            double military_stolen = rg->military * OM_REVOLT_MILITARY_STEAL;
            double economy_stolen = rg->economy * OM_REVOLT_ECONOMY_STEAL;
            lc_split_region(rg);
            om_region_set_owner(w, region_idx, prev, (int64_t)w->tick);
            om_region_set_previous_owner(w, region_idx, -1);
            lc_log_reversion(w, region_idx, old_owner, prev, military_stolen, economy_stolen);
            lc_log_revolt(w, region_idx, old_owner, rate, check, 0, -1, military_stolen,
                          economy_stolen, prev);
            return;
        }
    }

    int32_t new_fid = lc_free_faction_slot(w);
    if (new_fid < 0) {
        lc_log_revolt(w, region_idx, old_owner, rate, check, 0, -1, 0.0, 0.0, -1);
        return;
    }

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
    om_faction_set_created_tick(w, new_fid, w->tick);

    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f] || f == new_fid)
            continue;
        om_faction_set_stance(w, new_fid, f, OM_STANCE_HOSTILE);
        om_faction_set_stance(w, f, new_fid, OM_STANCE_HOSTILE);
    }

    double military_stolen = rg->military * OM_REVOLT_MILITARY_STEAL;
    double economy_stolen = rg->economy * OM_REVOLT_ECONOMY_STEAL;
    lc_split_region(rg);
    om_region_set_owner(w, region_idx, new_fid, (int64_t)w->tick);
    om_region_set_previous_owner(w, region_idx, old_owner);
    lc_borderize_edges(w, region_idx);

    lc_log_revolt(w, region_idx, old_owner, rate, check, 1, new_fid, military_stolen,
                  economy_stolen, -1);
}

/* ALG-42 zombie cleanup. Pass 1 removes a zero-region breakaway once it is
 * ZOMBIE_GHOST_TICKS old; pass 2 (below) hands a lone-region breakaway's
 * region to its strongest border neighbor. Pass 2 skips a breakaway that
 * conquered a region this tick, then clears that per-tick flag once every
 * faction has been checked. */
static void lc_zombie_cleanup(om_world *w) {
    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f] || w->faction_archetype[f] != OM_ARCH_BREAKAWAY)
            continue;
        if (om_faction_territory(w, f) != 0)
            continue;
        uint64_t age = w->tick - w->faction_created_tick[f];
#ifdef OM_DEBUG_INJECT
        int ghost_due = (w->inject == OM_BUG_ZOMBIE_PASS1_GE_NOT_GT)
            ? (age > OM_ZOMBIE_GHOST_TICKS)
            : (age >= OM_ZOMBIE_GHOST_TICKS);
#else
        int ghost_due = (age >= OM_ZOMBIE_GHOST_TICKS);
#endif
        if (!ghost_due)
            continue;
        om_faction_remove(w, f);
    }

    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f] || w->faction_archetype[f] != OM_ARCH_BREAKAWAY)
            continue;
        if (w->faction_conquered_this_tick[f])
            continue;
        if (om_faction_territory(w, f) != 1)
            continue;
        if ((w->tick - w->faction_created_tick[f]) < OM_ZOMBIE_CLEANUP_TICKS)
            continue;
        if (w->faction_budget[f] >= OM_COLONIZE_COST)
            continue;

        uint32_t only_region = w->n_regions;
        for (uint32_t i = 0; i < w->n_regions; i++) {
            if (w->regions[i].faction_id == f) {
                only_region = i;
                break;
            }
        }
        if (only_region == w->n_regions)
            continue;

        int32_t best_fid = -1;
        uint32_t best_territory = 0;
        for (uint32_t j = 0; j < w->n_regions; j++) {
            if (j == only_region)
                continue;
            om_edge_type et;
            if (!om_region_edge(w, only_region, j, &et) || et != OM_EDGE_BORDER)
                continue;
            int32_t neighbor_fid = w->regions[j].faction_id;
            if (neighbor_fid < 0 || neighbor_fid == f)
                continue;
            uint32_t terr = om_faction_territory(w, neighbor_fid);
            if (best_fid < 0 || terr > best_territory) {
                best_fid = neighbor_fid;
                best_territory = terr;
            }
        }
        if (best_fid < 0)
            continue;

        if (w->lc_absorptions_n < OM_MAX_REGIONS) {
            om_absorption_record *rec = &w->lc_absorptions[w->lc_absorptions_n++];
            rec->tick = w->tick;
            rec->absorbed_faction = f;
            rec->absorbing_faction = best_fid;
            rec->region_idx = only_region;
        }

        om_region_set_owner(w, only_region, best_fid, (int64_t)w->tick);
        om_region_set_previous_owner(w, only_region, f);
        om_faction_remove(w, f);
    }

    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++)
        w->faction_conquered_this_tick[f] = 0;
}

void om_step_lifecycle(om_world *w) {
    if (!w)
        return;

    w->lc_revolts_n = 0;
    w->lc_reversions_n = 0;
    w->lc_absorptions_n = 0;

    for (uint32_t r = 0; r < w->n_regions; r++) {
        uint32_t pending = om_region_faction_creation_pending(w, r);
        if (pending == 0)
            continue;
        lc_resolve_faction_creation(w, r, pending - 1);
    }

    lc_zombie_cleanup(w);
}

int om_faction_is_active(const om_world *w, int32_t faction_id) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return 0;
    return w->faction_used[faction_id] ? 1 : 0;
}

void om_faction_mark_conquered_this_tick(om_world *w, int32_t faction_id) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return;
    w->faction_conquered_this_tick[faction_id] = 1;
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
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return;
    w->faction_created_tick[faction_id] = tick;
}

void om_faction_set_event_window_counts(om_world *w, int32_t faction_id, uint32_t total_events, uint32_t revolts, uint32_t attacks, uint32_t colonizations) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return;
    w->faction_window_total[faction_id] = total_events;
    w->faction_window_revolts[faction_id] = revolts;
    w->faction_window_attacks[faction_id] = attacks;
    w->faction_window_colonizations[faction_id] = colonizations;
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

uint32_t om_tick_absorptions(const om_world *w, om_absorption_record *out, uint32_t max) {
    if (!w || !out || max == 0)
        return 0;
    uint32_t n = (w->lc_absorptions_n < max) ? w->lc_absorptions_n : max;
    memcpy(out, w->lc_absorptions, n * sizeof(om_absorption_record));
    return n;
}

uint32_t om_tick_reversions(const om_world *w, om_reversion_record *out, uint32_t max) {
    if (!w || !out || max == 0)
        return 0;
    uint32_t n = (w->lc_reversions_n < max) ? w->lc_reversions_n : max;
    memcpy(out, w->lc_reversions, n * sizeof(om_reversion_record));
    return n;
}

uint32_t om_tick_revolts(const om_world *w, om_revolt_record *out, uint32_t max) {
    if (!w || !out || max == 0)
        return 0;
    uint32_t n = (w->lc_revolts_n < max) ? w->lc_revolts_n : max;
    memcpy(out, w->lc_revolts, n * sizeof(om_revolt_record));
    return n;
}

int om_world_is_terminal(const om_world *w) {
    /* Q-054-01 deferred (R-054-01): the final era continues indefinitely. */
    (void)w;
    return 0;
}

static uint32_t lc_inhabited_region_count(const om_world *w) {
    uint32_t n = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].tier != OM_TIER_EMPTY)
            n++;
    }
    return n;
}

static uint32_t lc_empty_border_count(const om_world *w, int32_t fid) {
    uint32_t count = 0;
    for (uint32_t j = 0; j < w->n_regions; j++) {
        if (w->regions[j].tier != OM_TIER_EMPTY)
            continue;
        int touches = 0;
        for (uint32_t i = 0; i < w->n_regions && !touches; i++) {
            if (w->regions[i].faction_id != fid)
                continue;
            om_edge_type et;
            if (om_region_edge(w, i, j, &et))
                touches = 1;
        }
        if (touches)
            count++;
    }
    return count;
}

/* ALG-44 lifecycle phase: six checks in a fixed order, first match wins;
 * zero regions is equilibrium regardless of the window counts. */
int om_faction_phase(const om_world *w, int32_t faction_id) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return LC_PHASE_EQUILIBRIUM;

    uint32_t territory = om_faction_territory(w, faction_id);
    if (territory == 0)
        return LC_PHASE_EQUILIBRIUM;

    uint32_t total = w->faction_window_total[faction_id];
    uint32_t denom = (total > 0) ? total : 1;

    double revolt_share = (double)w->faction_window_revolts[faction_id] / (double)denom;
    if (revolt_share >= OM_LIFECYCLE_FRAGMENTATION_REVOLT_RATE)
        return LC_PHASE_FRAGMENTATION;

    double economy_sum = 0.0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id == faction_id)
            economy_sum += w->regions[i].economy;
    }
    if (economy_sum > 0.0) {
        double drain = ((double)territory * OM_REGION_MAINTENANCE_COST) / economy_sum;
        if (drain > OM_LIFECYCLE_OVEREXTENSION_DRAIN_RATIO)
            return LC_PHASE_OVEREXTENSION;
    }

    double attack_share = (double)w->faction_window_attacks[faction_id] / (double)denom;
    if (attack_share >= OM_LIFECYCLE_CONFLICT_ATTACK_RATE)
        return LC_PHASE_CONFLICT;

    uint32_t inhabited = lc_inhabited_region_count(w);
    if (inhabited > 0) {
        double empty_ratio = (double)lc_empty_border_count(w, faction_id) / (double)inhabited;
        if (empty_ratio >= OM_LIFECYCLE_EXPANSION_EMPTY_THRESHOLD)
            return LC_PHASE_EXPANSION;
    }

    if (w->faction_window_colonizations[faction_id] > 0 && w->faction_window_attacks[faction_id] == 0)
        return LC_PHASE_CONSOLIDATION;

    return LC_PHASE_EQUILIBRIUM;
}
