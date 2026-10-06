/* csrc/region.c — E-02 region state and composites (build card 200). */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

static uint64_t om_world_serial_counter = 1;

void om_mission_install_save_hooks(om_world *w); /* csrc/mission.c, not in a header */

om_world *om_world_new(uint32_t n_regions, uint64_t seed) {
    om_world *w = calloc(1, sizeof(om_world));
    if (!w) return NULL;
    w->n_regions = n_regions;
    w->seed = seed;
    om_rng_seed(w, seed);
    w->tick = 0;
    w->trace_on = 0;
    /* R11 (DECISIONS.md): -1, not 0 -- OM_BUG_OSC_AS_LEVEL is bug id 0, so a
     * default of 0 collided with it and every debug-build world ran with
     * that fault active until some other bug was deliberately injected. */
    w->inject = -1;
    /* F2d: n_regions == 0 defers the count to om_world_generate() (E-03,
     * ouroboros_sim.h ~line 693-694); regions/n_regions stay NULL/0 here and
     * csrc/worldgen.c's om_world_generate allocates w->regions itself. */
    if (n_regions > OM_MAX_REGIONS) {
        free(w);
        return NULL;
    }
    if (n_regions > 0) {
        w->regions = calloc(n_regions, sizeof(om_region));
        if (!w->regions) {
            free(w);
            return NULL;
        }
        for (uint32_t i = 0; i < n_regions; i++) {
            w->regions[i].faction_id = -1;
        }
    } else {
        w->regions = NULL;
    }
    /* D1 (two-day-push brief, decision 4): om_world_new() sets no feature.
     * conftest.py's world_factory applies each test's epic feature set from
     * docs/northstar/spec_factory/mvp_features.toml on top of a raw world. */
    memset(w->region_edge, -1, sizeof(w->region_edge));
    w->trace = NULL;
    w->trace_len = 0;
    w->trace_cap = 0;
    /* F2b: E-03 generation defaults (ouroboros_sim.h ~line 690, ALG-30/31).
     * The om_gen_set_* setters in csrc/worldgen.c overwrite these. */
    w->gen_region_min = OM_WORLD_REGION_COUNT_RANGE_LO;
    w->gen_region_max = OM_WORLD_REGION_COUNT_RANGE_HI;
    w->gen_faction_count = OM_WORLD_FACTIONS_PER_GAME;
    w->gen_extra_edge_ratio = OM_WORLD_EXTRA_EDGE_RATIO;
    w->gen_player_pref = OM_TMPL_NONE;
    w->gen_preference_weight = OM_WORLD_PLAYER_PREFERENCE_WEIGHT;
    w->gen_extra_edges_on = 1;
    {
        const double ranges[3][4] = {
            { OM_CONQUEROR_HOME_RANGE_MILITARY_LO, OM_CONQUEROR_HOME_RANGE_MILITARY_HI,
              OM_CONQUEROR_HOME_RANGE_ECONOMY_LO, OM_CONQUEROR_HOME_RANGE_ECONOMY_HI },
            { OM_FORTIFIER_HOME_RANGE_MILITARY_LO, OM_FORTIFIER_HOME_RANGE_MILITARY_HI,
              OM_FORTIFIER_HOME_RANGE_ECONOMY_LO, OM_FORTIFIER_HOME_RANGE_ECONOMY_HI },
            { OM_OPPORTUNIST_HOME_RANGE_MILITARY_LO, OM_OPPORTUNIST_HOME_RANGE_MILITARY_HI,
              OM_OPPORTUNIST_HOME_RANGE_ECONOMY_LO, OM_OPPORTUNIST_HOME_RANGE_ECONOMY_HI },
        };
        memcpy(w->gen_home_range, ranges, sizeof(ranges));
    }
    for (uint32_t i = 0; i < OM_MAX_FACTIONS; i++) {
        w->faction_template[i] = OM_TMPL_NONE;
    }
    w->generated = 0;
    w->edge_count = 0;

    /* F2c: E-07 lifecycle log/window/tactical-state storage. calloc above
     * already zeroes these; set explicitly so this list is the field list. */
    w->lc_revolts_n = 0;
    w->lc_reversions_n = 0;
    w->lc_absorptions_n = 0;
    for (uint32_t i = 0; i < OM_MAX_FACTIONS; i++) {
        w->faction_created_tick[i] = 0;
        w->faction_conquered_this_tick[i] = 0;
        w->faction_window_total[i] = 0;
        w->faction_window_revolts[i] = 0;
        w->faction_window_attacks[i] = 0;
        w->faction_window_colonizations[i] = 0;
    }
    /* NULL until first om_region_set_previous_owner call; getter returns
     * -1 while NULL (same convention as region_held_since). */
    w->region_previous_owner = NULL;
    w->tactical_state = NULL;
    w->tactical_state_free = NULL;
    w->tactical_state_size = NULL;
    w->tactical_state_write = NULL;
    w->tactical_state_read = NULL;
    w->generational_state = NULL;
    w->generational_state_free = NULL;
    w->generational_state_size = NULL;
    w->generational_state_write = NULL;
    w->generational_state_read = NULL;
    w->events_state = NULL;
    w->events_state_free = NULL;
    w->events_state_size = NULL;
    w->events_state_write = NULL;
    w->events_state_read = NULL;
    /* F2m: install the two modules' save hooks now, on the just-zeroed
     * slots above, so a world that never touches events/generational still
     * has a working read hook if a save is loaded into it (om_internal.h;
     * csrc/events.c / csrc/generational.c set the same pointers again, not
     * the state itself, the first time either module is actually used). */
    om_events_install_save_hooks(w);
    om_generational_install_save_hooks(w);
    {
        uint32_t ns;
        for (ns = 0; ns < OM_NET_SECTION_COUNT; ns++) w->net_section_hash[ns] = NULL;
    }
    w->net_unit_hashes = NULL;
    w->net_state = NULL;
    w->net_state_free = NULL;
    w->mission_state = NULL;
    w->mission_state_free = NULL;
    w->mission_state_size = NULL;
    w->mission_state_write = NULL;
    w->mission_state_read = NULL;
    om_mission_install_save_hooks(w);
    w->fog_state = NULL;
    w->fog_state_free = NULL;
    w->fog_state_size = NULL;
    w->fog_state_write = NULL;
    w->fog_state_read = NULL;
    w->chronicle_state = NULL;
    w->chronicle_state_free = NULL;
    w->chronicle_state_size = NULL;
    w->chronicle_state_write = NULL;
    w->chronicle_state_read = NULL;
    w->move_state = NULL;
    w->move_state_free = NULL;
    w->move_state_size = NULL;
    w->move_state_write = NULL;
    w->move_state_read = NULL;
    w->macro_state = NULL;
    w->macro_state_free = NULL;
    w->macro_state_size = NULL;
    w->macro_state_write = NULL;
    w->macro_state_read = NULL;
    w->support_state = NULL;
    w->support_state_free = NULL;
    w->support_state_size = NULL;
    w->support_state_write = NULL;
    w->support_state_read = NULL;
    w->mapgen_state = NULL;
    w->mapgen_state_free = NULL;
    w->mapgen_state_size = NULL;
    w->mapgen_state_write = NULL;
    w->mapgen_state_read = NULL;
    om_unit_install_net_hooks(w);
    om_move_install_net_hooks(w);
    om_macro_install_net_hooks(w);
    om_fog_install_net_hooks(w);
    om_support_install_net_hooks(w);
    om_mission_install_net_hooks(w);
    om_mapgen_install_net_hooks(w);
    w->terrain_state = NULL;
    w->terrain_state_free = NULL;
    w->terrain_state_size = NULL;
    w->terrain_state_write = NULL;
    w->terrain_state_read = NULL;
    om_terrain_install_net_hooks(w);

    /* F2e: E-06 diplomacy storage. calloc above already zeroes
     * faction_stance_counter/faction_cooperative_since (0 = never-counted /
     * never-cooperative, om_internal.h); faction_last_knowledge_lost needs
     * the explicit -1 "never fired" sentinel calloc cannot give it. */
    for (int32_t i = 0; i < OM_MAX_FACTIONS; i++) {
        w->faction_last_knowledge_lost[i] = -1;
    }
    w->world_serial = om_world_serial_counter++;
    return w;
}

#ifdef OM_DEBUG_INJECT
void om_debug_gen_config(const om_world *w, om_debug_gen_config_row *out) {
    if (!w || !out) return;
    out->region_min = w->gen_region_min;
    out->region_max = w->gen_region_max;
    out->faction_count = w->gen_faction_count;
    out->extra_edge_ratio = w->gen_extra_edge_ratio;
    out->player_pref = (int32_t)w->gen_player_pref;
    out->preference_weight = w->gen_preference_weight;
    out->extra_edges_on = w->gen_extra_edges_on;
    memcpy(out->home_range, w->gen_home_range, sizeof(out->home_range));
    out->generated = w->generated;
    out->edge_count = w->edge_count;
}
#endif

void om_world_free(om_world *w) {
    if (!w) return;
    if (w->tactical_state && w->tactical_state_free) {
        w->tactical_state_free(w->tactical_state);
    }
    if (w->generational_state && w->generational_state_free) {
        w->generational_state_free(w->generational_state);
    }
    if (w->events_state && w->events_state_free) {
        w->events_state_free(w->events_state);
    }
    if (w->net_state && w->net_state_free) {
        w->net_state_free(w->net_state);
    }
    if (w->terrain_state && w->terrain_state_free) {
        w->terrain_state_free(w->terrain_state);
    }
    if (w->mission_state && w->mission_state_free) {
        w->mission_state_free(w->mission_state);
    }
    if (w->fog_state && w->fog_state_free) {
        w->fog_state_free(w->fog_state);
    }
    if (w->chronicle_state && w->chronicle_state_free) {
        w->chronicle_state_free(w->chronicle_state);
    }
    if (w->move_state && w->move_state_free) {
        w->move_state_free(w->move_state);
    }
    if (w->macro_state && w->macro_state_free) {
        w->macro_state_free(w->macro_state);
    }
    if (w->support_state && w->support_state_free) {
        w->support_state_free(w->support_state);
    }
    if (w->mapgen_state && w->mapgen_state_free) {
        w->mapgen_state_free(w->mapgen_state);
    }
    free(w->region_previous_owner);
    free(w->regions);
    free(w->trace);
    free(w);
}

void om_world_set_seed(om_world *w, uint64_t seed) {
    if (!w) return;
    w->seed = seed;
    om_rng_seed(w, seed);
}

/* weak: csrc/worldgen.c (card B4) provides the strong definition; delete this stub after attach/B4 */
__attribute__((weak)) void om_world_generate(om_world *w) {
    (void)w;
}

int om_region_set(om_world *w, uint32_t idx, om_tier tier,
                  double military, double economy, double tension, double population,
                  double econ_phase, double tension_phase, int32_t faction_id) {
    if (!w || idx >= w->n_regions) return -1;
    om_region *r = &w->regions[idx];
    r->tier = tier;
    r->military = military;
    r->economy = economy;
    r->tension = tension;
    r->population = population;
    r->econ_phase = econ_phase;
    r->tension_phase = tension_phase;
    r->prev_econ_osc = 0.0;
    r->prev_tension_osc = 0.0;
    r->faction_id = faction_id;
    r->n_neighbors = 0;
    return 0;
}

void om_region_set_adjacency(om_world *w, uint32_t idx,
                             const uint32_t *neighbor_idx, uint32_t n_neighbors) {
    if (!w || idx >= w->n_regions) return;
    om_region *r = &w->regions[idx];
    uint32_t count = n_neighbors < OM_MAX_NEIGHBORS ? n_neighbors : OM_MAX_NEIGHBORS;
    if (neighbor_idx) {
        memcpy(r->neighbors, neighbor_idx, count * sizeof(uint32_t));
    }
    r->n_neighbors = count;
}

void om_region_set_faction_modifier(om_world *w, int32_t faction_id,
                                    om_field field, double value) {
    if (!w) return;
    if (faction_id < 0 || faction_id >= OM_MAX_FACTIONS) return;
    if (field >= OM_F_COUNT) return;
    w->faction_mod[faction_id][field] = value;
}

uint32_t om_region_count(const om_world *w) {
    if (!w) return 0;
    return w->n_regions;
}



double om_region_field(const om_world *w, uint32_t idx, om_field f) {
    if (!w || idx >= w->n_regions) return 0.0;
    if (f >= OM_F_COUNT) return 0.0;
    const om_region *r = &w->regions[idx];
    if (r->tier == OM_TIER_EMPTY) return 0.0;
    switch (f) {
        case OM_F_MILITARY: return r->military;
        case OM_F_ECONOMY:  return r->economy;
        case OM_F_TENSION:  return r->tension;
        case OM_F_POPULATION:return r->population;
        default: return 0.0;
    }
}

double om_region_composite(const om_world *w, uint32_t idx, om_composite c) {
    if (!w || idx >= w->n_regions) return 0.0;
    if (c >= OM_C_COUNT) return 0.0;
    const om_region *r = &w->regions[idx];
    if (r->tier == OM_TIER_EMPTY) return 0.0;
    double chosen = 0.0;
    if (c == OM_C_STABILITY) {
        chosen = r->military * 0.40 + (100.0 - r->tension) * 0.35 + r->population * 0.25;
        if (r->military < 10.0) chosen *= 0.70;
        if (r->population < 20.0) chosen *= 0.75;
    } else if (c == OM_C_CAPACITY) {
        chosen = r->economy * 0.50 + r->population * 0.35 + r->military * 0.15;
        if (r->economy < 20.0) chosen *= 0.65;
        if (r->population < 20.0) chosen *= 0.70;
    }
    return round(chosen * 100.0) / 100.0;
}

om_tier om_region_tier(const om_world *w, uint32_t idx) {
    if (!w || idx >= w->n_regions) return OM_TIER_EMPTY;
    return w->regions[idx].tier;
}



uint32_t om_checksum_cadence(void) {
    return 10;
}






uint32_t om_abi_version(void) {
    return OM_ABI_VERSION;
}

/* Card-201 (sim.c) functions as WEAK stubs: lets the E-02 fenced suite load the
 * library with only region.c present (card 200). When sim.c lands (card 201),
 * its strong definitions override these with no multiple-definition link error. */
__attribute__((weak)) uint64_t om_world_step(om_world *w) { if (!w) return 0; w->tick++; return w->tick; }
__attribute__((weak)) uint64_t om_world_run(om_world *w, uint64_t n) { (void)n; return w ? w->tick : 0; }
__attribute__((weak)) int om_region_drift(const om_world *w, uint32_t idx, om_drift_row *out) { (void)w;(void)idx;(void)out; return -1; }
__attribute__((weak)) uint64_t om_world_checksum(const om_world *w) { (void)w; return 0; }
__attribute__((weak)) void om_trace_enable(om_world *w, int on) { if (w) w->trace_on = on ? 1 : 0; }
__attribute__((weak)) uint64_t om_trace_len(const om_world *w) { return w ? w->trace_len : 0; }
__attribute__((weak)) uint64_t om_trace_read(const om_world *w, uint64_t s, uint64_t c, om_trace_row *o) { (void)w;(void)s;(void)c;(void)o; return 0; }
#ifdef OM_DEBUG_INJECT
__attribute__((weak)) void om_debug_inject(om_world *w, om_bug bug) { (void)w;(void)bug; }
#endif
