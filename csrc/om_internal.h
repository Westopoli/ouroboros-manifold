/* csrc/om_internal.h — private world layout shared by the C source files.
 * Parent-owned like ouroboros_sim.h. A build card that must add state to
 * om_world lists this file in allowed_files; a card that only reads it does
 * not. Never included by the tests; the public ABI is ouroboros_sim.h. */
#ifndef OM_INTERNAL_H
#define OM_INTERNAL_H

#include "ouroboros_sim.h"

#define OM_MAX_NEIGHBORS 32
#define OM_DAMAGE_HISTORY_CAP 64

typedef struct {
    om_tier  tier;
    double   military, economy, tension, population;
    double   econ_phase, tension_phase;
    double   prev_econ_osc, prev_tension_osc;
    int32_t  faction_id;
    uint32_t neighbors[OM_MAX_NEIGHBORS];
    uint32_t n_neighbors;
    om_drift_row last_drift;

    /* ALG-11 damage history (om_region_add_damage / om_region_damage_history,
     * ouroboros_sim.h ~line 254): a ring of (tick, military_loss, economy_loss)
     * entries, one per recorded attack-resolution loss, oldest overwritten past
     * OM_DAMAGE_HISTORY_CAP. Persists across ticks; never reset in sim.c. The
     * reader sums entries with tick within DAMAGE_HISTORY_WINDOW = 150 of the
     * current world tick (docs/bible/algorithms.md ALG-11; R-034-07). */
    uint64_t damage_tick[OM_DAMAGE_HISTORY_CAP];
    double   damage_military[OM_DAMAGE_HISTORY_CAP];
    double   damage_economy[OM_DAMAGE_HISTORY_CAP];
    uint32_t damage_head, damage_len;
} om_region;

struct om_world {
    uint32_t n_regions;
    uint64_t seed;
    uint64_t tick;
    int      trace_on;
    int      inject;
    om_region *regions;
    double   faction_mod[OM_MAX_FACTIONS][OM_F_COUNT];
    om_trace_row *trace;
    uint64_t trace_len, trace_cap;

    /* E-05 faction, ownership, typed edges, and RNG state.
     * features[] is sized for every om_feature id (OM_FEAT_EVENTS ..
     * OM_FEAT_TACTICAL, 9 today); bump alongside a new om_feature value. */
    int          features[9];
    double       faction_budget[OM_MAX_FACTIONS];
    double       faction_budget_snapshot[OM_MAX_FACTIONS];
    double       faction_tech[OM_MAX_FACTIONS];
    double       faction_confidence[OM_MAX_FACTIONS];
    om_archetype faction_archetype[OM_MAX_FACTIONS];
    om_stance    faction_stance[OM_MAX_FACTIONS][OM_MAX_FACTIONS];
    double       faction_tech_attack[OM_MAX_FACTIONS];
    double       faction_tech_defense[OM_MAX_FACTIONS];
    double       faction_tech_economy[OM_MAX_FACTIONS];
    int          faction_used[OM_MAX_FACTIONS];
    uint32_t     faction_n;
    int64_t     *region_held_since;
    om_edge_type region_edge[64][64];
    uint64_t     rng_state, rng_inc;
    double       rng_forced[4096];
    uint32_t     rng_forced_head, rng_forced_len;

    /* E-05 decision and resolution state */
    om_decision        decisions[64];
    uint32_t           decisions_n;
    om_telegraph       telegraphs[64];
    uint32_t           telegraphs_n;
    om_attack_result   attacks[64];
    uint32_t           attacks_n;
    om_collision       collisions[64];
    uint32_t           collisions_n;
    om_reinforce       reinforces[64];
    uint32_t           reinforces_n;
    om_colonize_result colonizations[64];
    uint32_t           colonizations_n;
    om_friction        frictions[64];
    uint32_t           frictions_n;
    om_admin_roll      admin_rolls[64];
    uint32_t           admin_rolls_n;

    /* event queue, shared with E-04 (ouroboros_sim.h ~line 454): entries are
     * queued by E-05 (conquest-unrest, admin-separatist chains) and resolved
     * by E-04 (ALG-36). Persists across ticks; never reset in sim.c. */
    om_queued_event    event_queue[64];
    uint32_t           event_queue_n;

    /* E-03 generation config and result (freeze/F2b). Config is written by
     * the om_gen_set_* setters (ouroboros_sim.h ~line 690, csrc/worldgen.c)
     * and read by om_world_generate; defaults are set in om_world_new
     * (csrc/region.c) from om_constants.h. gen_home_range is indexed
     * [archetype - OM_ARCH_CONQUEROR][mil_lo, mil_hi, eco_lo, eco_hi]
     * (R-022-05). faction_template holds each faction's rolled template
     * (OM_TMPL_NONE before generation); generated and edge_count back
     * om_world_generated / om_world_edge_count. */
    uint32_t    gen_region_min, gen_region_max;
    uint32_t    gen_faction_count;
    double      gen_extra_edge_ratio;
    om_template gen_player_pref;
    double      gen_preference_weight;
    int         gen_extra_edges_on;
    double      gen_home_range[3][4];
    om_template faction_template[OM_MAX_FACTIONS];
    int         generated;
    uint32_t    edge_count;
};

/* Debug-build mirror of the E-03 generation fields above, for the F2b storage
 * test (tests/csim/test_E03_wiring_storage.py). Not part of the public ABI. */
#ifdef OM_DEBUG_INJECT
typedef struct {
    uint32_t region_min, region_max;
    uint32_t faction_count;
    double   extra_edge_ratio;
    int32_t  player_pref;
    double   preference_weight;
    int32_t  extra_edges_on;
    double   home_range[3][4];
    int32_t  generated;
    uint32_t edge_count;
} om_debug_gen_config_row;
void om_debug_gen_config(const om_world *w, om_debug_gen_config_row *out);
#endif

/* Internal step hooks. om_step_collisions runs between om_step_reinforce
 * (3e) and om_step_resolve (3f): it groups this tick's pending intents in
 * w->decisions[] by target, resolves every target with two or more intents
 * (ALG-23/24, S-039), writes w->collisions[]/w->collisions_n, and removes
 * the colliding intents from w->decisions[] so om_step_resolve never
 * double-resolves them. See docs/bible/epics/E-05-faction-agents-and-conflict.md
 * R-039-01..06 and csrc/sim.c's tick-order wiring in om_world_step. */
void om_step_events(om_world *w);
void om_faction_step_budget(om_world *w);
void om_step_telegraphs(om_world *w);
void om_step_decisions(om_world *w);
void om_step_reinforce(om_world *w);
void om_step_collisions(om_world *w);
void om_step_resolve(om_world *w);
void om_step_friction(om_world *w);
void om_step_admin_revolts(om_world *w);
/* Tick steps 4.25, 4.5 (E-06) and 6 (E-07); wired in csrc/sim.c between
 * om_step_admin_revolts and the drift loop, and after it, respectively (F2
 * freeze). STUB bodies in csrc/diplomacy.c and csrc/lifecycle.c until B5/B6
 * land. */
void om_step_diplomacy(om_world *w);
void om_step_technology(om_world *w);
void om_step_lifecycle(om_world *w);

#endif /* OM_INTERNAL_H */
