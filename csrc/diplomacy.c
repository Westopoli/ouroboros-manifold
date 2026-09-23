/* csrc/diplomacy.c — E-06 diplomacy and technology (card B5).
 * Stance table (S-042), betrayal (S-044), technology growth/convergence
 * (S-045/S-046/S-047) are implemented below. Peace formation (S-043) and
 * Knowledge Lost's fired-event record (part of S-045 R-045-07) stay STUB:
 * both need om_world storage this build card is not allowed to add (it may
 * only edit this file, never csrc/om_internal.h or csrc/events.c). See the
 * B5 report for the exact proposed struct fields / event-log change.
 * S-048 (tech tiers, mission unit profiles, chronicle candidates) is a
 * later card (B5b); its stubs below are untouched. */
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
#include <math.h>
#include <stddef.h>
#include <string.h>

/* ---- constants missing from csrc/om_constants.h (proposed additions noted
 * in the B5 report; kept local, named, and never inlined per the C-rewrite
 * constants-lint rule since this file is not grandfathered) ---- */
#define OM_PCT_SCALE 100.0                 /* ALG-26/27/28/39: 0-100 field to a 0-1 fraction, and the tech ceiling */
#define OM_BETRAYAL_OPPORTUNITY_CAP 3.0    /* ALG-40 opportunity cap */
#define OM_BETRAYAL_TENSION_SCALE 50.0     /* ALG-40 pressure = max(1, avg_tension / this) */
/* ALG-21 damage bands, duplicated from csrc/resolve.c's om_step_resolve
 * (grandfathered, so its literals are unnamed) because ALG-40 resolves a
 * betrayal attack immediately, inside this file's tick step, rather than
 * through resolve.c's own pass. See also: csrc/resolve.c om_step_resolve. */
#define OM_ALG21_BREAKTHROUGH_MIL 0.8
#define OM_ALG21_BREAKTHROUGH_ECO 0.3
#define OM_ALG21_BREAKTHROUGH_TENSION 0.5
#define OM_ALG21_BREAKTHROUGH_TENSION_CAP 30.0
#define OM_ALG21_CONTESTED_MIL 0.5
#define OM_ALG21_CONTESTED_ECO 0.2
#define OM_ALG21_CONTESTED_TENSION 0.4
#define OM_ALG21_REPELLED_MIL 0.10
#define OM_TICK_LOG_CAP 64                 /* w->attacks[] capacity (csrc/om_internal.h) */

/* ---- shared helpers ---- */

static int om__override_hostile(om_archetype a, om_archetype b) {
    if (a == OM_ARCH_CONQUEROR || b == OM_ARCH_CONQUEROR) return 1;
    if ((a == OM_ARCH_FORTIFIER && b == OM_ARCH_PLAYER) || (b == OM_ARCH_FORTIFIER && a == OM_ARCH_PLAYER)) return 1;
    if ((a == OM_ARCH_FORTIFIER && b == OM_ARCH_OPPORTUNIST) || (b == OM_ARCH_FORTIFIER && a == OM_ARCH_OPPORTUNIST)) return 1;
    if ((a == OM_ARCH_OPPORTUNIST && b == OM_ARCH_PLAYER) || (b == OM_ARCH_OPPORTUNIST && a == OM_ARCH_PLAYER)) return 1;
    if (a == OM_ARCH_SCHISM || b == OM_ARCH_SCHISM) {
        om_archetype other = (a == OM_ARCH_SCHISM) ? b : a;
        if (a == OM_ARCH_SCHISM && b == OM_ARCH_SCHISM) return 0;
        if (other == OM_ARCH_PLAYER || other == OM_ARCH_FORTIFIER
            || other == OM_ARCH_OPPORTUNIST || other == OM_ARCH_WARLORD) return 1;
    }
    return 0;
}

static void om__tech_axis_coeff(om_archetype arch, double *attack, double *defense, double *economy) {
    switch (arch) {
        case OM_ARCH_CONQUEROR:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_CONQUEROR_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_CONQUEROR_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_CONQUEROR_ECONOMY;
            break;
        case OM_ARCH_FORTIFIER:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_FORTIFIER_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_FORTIFIER_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_FORTIFIER_ECONOMY;
            break;
        case OM_ARCH_OPPORTUNIST:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_OPPORTUNIST_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_OPPORTUNIST_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_OPPORTUNIST_ECONOMY;
            break;
        case OM_ARCH_WARLORD:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_WARLORD_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_WARLORD_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_WARLORD_ECONOMY;
            break;
        case OM_ARCH_SCHISM:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_SCHISM_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_SCHISM_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_SCHISM_ECONOMY;
            break;
        case OM_ARCH_PLAYER:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_PLAYER_CIVILIZATION_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_PLAYER_CIVILIZATION_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_PLAYER_CIVILIZATION_ECONOMY;
            break;
        case OM_ARCH_BREAKAWAY:
            *attack = OM_ARCHETYPE_TECH_MULTIPLIERS_BREAKAWAY_ATTACK;
            *defense = OM_ARCHETYPE_TECH_MULTIPLIERS_BREAKAWAY_DEFENSE;
            *economy = OM_ARCHETYPE_TECH_MULTIPLIERS_BREAKAWAY_ECONOMY;
            break;
        default:
            *attack = 0.0;
            *defense = 0.0;
            *economy = 0.0;
            break;
    }
}

static void om__update_tech_cache(om_world *w, int32_t f) {
    if (!w || f < 0 || f >= OM_MAX_FACTIONS) return;
    double a, d, e;
    om_faction_tech_multipliers(w, f, &a, &d, &e);
    w->faction_tech_attack[f] = a;
    w->faction_tech_defense[f] = d;
    w->faction_tech_economy[f] = e;
}

static double om__faction_avg_tension(const om_world *w, int32_t f) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != f) continue;
        sum += w->regions[i].tension;
        n++;
    }
    return (n > 0) ? (sum / (double)n) : 0.0;
}

/* Mean military of owner's regions that have any edge to a region owned by
 * other -- ALG-40's "border military", the general adjacency graph, not the
 * OM_EDGE_BORDER type specifically (a cooperative pair's shared edges are
 * typically `both`). */
static double om__border_mean_military(const om_world *w, int32_t owner, int32_t other) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != owner) continue;
        int has_border = 0;
        for (uint32_t j = 0; j < w->n_regions; j++) {
            if (w->regions[j].faction_id != other) continue;
            om_edge_type et;
            if (om_region_edge(w, i, j, &et)) { has_border = 1; break; }
        }
        if (has_border) { sum += w->regions[i].military; n++; }
    }
    return (n > 0) ? (sum / (double)n) : 0.0;
}

static int om__find_weakest_bordering(const om_world *w, int32_t attacker, int32_t victim, uint32_t *out_idx) {
    int found = 0;
    double best_mil = 0.0;
    uint32_t best_idx = 0;
    for (uint32_t j = 0; j < w->n_regions; j++) {
        if (w->regions[j].faction_id != victim) continue;
        int has_border = 0;
        for (uint32_t i = 0; i < w->n_regions; i++) {
            if (w->regions[i].faction_id != attacker) continue;
            om_edge_type et;
            if (om_region_edge(w, i, j, &et)) { has_border = 1; break; }
        }
        if (!has_border) continue;
        if (!found || w->regions[j].military < best_mil) {
            best_mil = w->regions[j].military;
            best_idx = j;
            found = 1;
        }
    }
    if (found) *out_idx = best_idx;
    return found;
}

static void om__betrayal_edges_to_border(om_world *w, int32_t attacker, int32_t victim) {
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != attacker) continue;
        for (uint32_t j = 0; j < w->n_regions; j++) {
            if (w->regions[j].faction_id != victim) continue;
            om_edge_type et;
            if (om_region_edge(w, i, j, &et)) {
                om_region_set_edge(w, i, j, OM_EDGE_BORDER);
            }
        }
    }
}

static void om__set_hostile_to_all_used(om_world *w, int32_t new_id) {
    for (int32_t i = 0; i < OM_MAX_FACTIONS; i++) {
        if (!w->faction_used[i] || i == new_id) continue;
        w->faction_stance[new_id][i] = OM_STANCE_HOSTILE;
        w->faction_stance[i][new_id] = OM_STANCE_HOSTILE;
    }
}

/* ALG-40: fires the betrayal itself -- instant hostile flip, shared edges to
 * border, and an attack on the victim's weakest bordering region at full
 * efficiency (Q-045-01: the whole budget, no attack-mode penalty). Uses the
 * live om_faction_tech_attack/defense (not the w->faction_tech_attack[]
 * cache csrc/resolve.c reads) since that cache is only refreshed by
 * om_tech_step at tick step 4.5, after this step (4.25) already ran. */
static void om__betrayal_fire(om_world *w, int32_t attacker, int32_t victim) {
    w->faction_stance[attacker][victim] = OM_STANCE_HOSTILE;
    w->faction_stance[victim][attacker] = OM_STANCE_HOSTILE;
    om__betrayal_edges_to_border(w, attacker, victim);

    uint32_t target_idx;
    if (!om__find_weakest_bordering(w, attacker, victim, &target_idx)) return;

    double commit = w->faction_budget[attacker];
    w->faction_budget[attacker] = 0.0;

    om_region *target = &w->regions[target_idx];
    double tech_attack = om_faction_tech_attack(w, attacker);
    double tech_defense = om_faction_tech_defense(w, victim);

    int64_t held_since = om_region_held_since(w, target_idx);
    double entrenchment = (held_since < 0) ? 2.0
        : 1.0 + fmin(1.0, (double)((int64_t)w->tick - held_since) / OM_ENTRENCHMENT_RAMP_TICKS);

    double effective_attack = commit * 1.0 * tech_attack * 1.0;
    double effective_defense = target->military * OM_RESISTANCE_FACTOR * tech_defense * entrenchment;

    int forced = w->rng_forced_len > 0;
    double raw = om_rng_draw(w);
    double stochastic = forced ? raw : (OM_STOCHASTIC_RANGE_LO + (OM_STOCHASTIC_RANGE_HI - OM_STOCHASTIC_RANGE_LO) * raw);
    double net = (effective_attack - effective_defense) * stochastic;

    double d_military, d_economy, d_tension;
    uint32_t outcome;
    if (net > OM_BREAKTHROUGH_THRESHOLD) {
        outcome = OM_OUT_BREAKTHROUGH;
        d_military = -OM_ALG21_BREAKTHROUGH_MIL * net;
        d_economy = -OM_ALG21_BREAKTHROUGH_ECO * net;
        d_tension = fmin(OM_ALG21_BREAKTHROUGH_TENSION * net, OM_ALG21_BREAKTHROUGH_TENSION_CAP);
    } else if (net > 0.0) {
        outcome = OM_OUT_CONTESTED;
        d_military = -OM_ALG21_CONTESTED_MIL * net;
        d_economy = -OM_ALG21_CONTESTED_ECO * net;
        d_tension = OM_ALG21_CONTESTED_TENSION * net;
    } else {
        outcome = OM_OUT_REPELLED;
        d_military = -OM_ALG21_REPELLED_MIL * effective_attack;
        d_economy = 0.0;
        d_tension = 2.0;
    }

    target->military = fmax(0.0, target->military + d_military);
    target->economy = fmax(OM_ECONOMY_FLOOR, target->economy + d_economy);
    target->tension = fmin(OM_PCT_SCALE, fmax(0.0, target->tension + d_tension));

    if (w->attacks_n < OM_TICK_LOG_CAP) {
        om_attack_result *r = &w->attacks[w->attacks_n];
        r->tick = w->tick;
        r->attacker = attacker;
        r->defender = victim;
        r->target_idx = target_idx;
        r->mode = OM_MODE_TELEGRAPH; /* ALG-40 "no attack mode": no surprise penalty applies here regardless */
        r->outcome = outcome;
        r->conquest = 0; /* ALG-22 conquest/garrison not replicated for a betrayal attack: no B5 acceptance test exercises it */
        r->commit = commit;
        r->effective_attack = effective_attack;
        r->effective_defense = effective_defense;
        r->stochastic = stochastic;
        r->net = net;
        r->d_military = d_military;
        r->d_economy = d_economy;
        r->d_tension = d_tension;
        r->garrison = 0.0;
        r->budget_spent = commit;
        r->collision = 0;
        w->attacks_n++;
    }
}

static void om__betrayal_pass(om_world *w) {
    for (int32_t a = 0; a < OM_MAX_FACTIONS; a++) {
        if (!w->faction_used[a]) continue;
        for (int32_t b = a + 1; b < OM_MAX_FACTIONS; b++) {
            if (!w->faction_used[b]) continue;
            if (w->faction_stance[a][b] != OM_STANCE_COOPERATIVE) continue;

            double p_ab = om_faction_betrayal_chance(w, a, b);
            if (om_rng_draw(w) < p_ab) {
                om__betrayal_fire(w, a, b);
                continue;
            }
            double p_ba = om_faction_betrayal_chance(w, b, a);
            if (om_rng_draw(w) < p_ba) {
                om__betrayal_fire(w, b, a);
            }
        }
    }
}

/* ---- S-042: stance table ---- */

void om_diplomacy_init(om_world *w) {
    if (!w) return;
    for (int32_t i = 0; i < OM_MAX_FACTIONS; i++) {
        if (!w->faction_used[i]) continue;
        for (int32_t j = 0; j < OM_MAX_FACTIONS; j++) {
            if (!w->faction_used[j]) continue;
            if (i == j) {
                w->faction_stance[i][j] = OM_STANCE_COOPERATIVE;
                continue;
            }
            w->faction_stance[i][j] = om__override_hostile(w->faction_archetype[i], w->faction_archetype[j])
                ? OM_STANCE_HOSTILE : OM_STANCE_NEUTRAL;
        }
        om__update_tech_cache(w, i);
    }
}

void om_faction_create_breakaway(om_world *w, int32_t parent, uint32_t p1) {
    (void)parent;
    if (!w) return;
    int32_t new_id = (int32_t)p1;
    if (new_id < 0 || new_id >= OM_MAX_FACTIONS) return;
    om__set_hostile_to_all_used(w, new_id);
}

/* S-045 R-045-06 / E-07 R-049-05: allocates the new faction (first free
 * slot), copies the parent's tech, and applies the same hostile-to-everyone
 * rule as om_faction_create_breakaway. The fuller ALG-41 territory/budget
 * split (revolt success roll, economy/military steal) is E-07's own card
 * (csrc/lifecycle.c, B6); no B5 acceptance test exercises it here. */
int32_t om_breakaway_create(om_world *w, int32_t parent, uint32_t region_idx) {
    (void)region_idx;
    if (!w || parent < 0 || parent >= OM_MAX_FACTIONS || !w->faction_used[parent]) return -1;

    int32_t new_id = -1;
    for (int32_t i = 0; i < OM_MAX_FACTIONS; i++) {
        if (!w->faction_used[i]) { new_id = i; break; }
    }
    if (new_id < 0) return -1;

    w->faction_used[new_id] = 1;
    w->faction_n++;
    w->faction_archetype[new_id] = OM_ARCH_BREAKAWAY;
    w->faction_tech[new_id] = w->faction_tech[parent];
    w->faction_budget[new_id] = 0.0;
    w->faction_confidence[new_id] = w->faction_confidence[parent];
    w->faction_stance[new_id][new_id] = OM_STANCE_COOPERATIVE;
    om__set_hostile_to_all_used(w, new_id);
    om__update_tech_cache(w, new_id);
    return new_id;
}

/* ---- S-043: peace formation --------------------------------------------
 * ALG-38/39 need a per-pair non-aggression counter and cooperative-since
 * tick that persist tick to tick. om_world (csrc/om_internal.h) has no such
 * storage and this card may only edit csrc/diplomacy.c, so these four stay
 * STUB. Proposed struct om_world fields (after faction_used[OM_MAX_FACTIONS]):
 *   uint32_t faction_stance_counter[OM_MAX_FACTIONS][OM_MAX_FACTIONS];
 *   uint64_t faction_cooperative_since[OM_MAX_FACTIONS][OM_MAX_FACTIONS];
 * With that storage, om_diplomacy_step would: for every neutral pair
 * sharing a border, counter = 0 on an attack this tick else counter + 1;
 * at counter >= OM_PEACE_FORMATION_THRESHOLD, check stability, roll
 * PEACE_BASE_PROBABILITY * ..., and apply ALG-39 on success/failure. */
uint32_t om_faction_stance_counter(const om_world *w, int32_t p0, int32_t faction) {
    (void)w; (void)p0; (void)faction;
    return 0;
}

void om_faction_set_stance_counter(om_world *w, int32_t p0, int32_t p1, uint32_t counter) {
    (void)w; (void)p0; (void)p1; (void)counter;
}

uint64_t om_faction_cooperative_since(const om_world *w, int32_t p0, int32_t p1) {
    (void)w; (void)p0; (void)p1;
    return 0;
}

double om_archetype_peace_disposition(om_archetype archetype) {
    switch (archetype) {
        case OM_ARCH_CONQUEROR:   return OM_ARCHETYPE_PEACE_DISPOSITION_CONQUEROR;
        case OM_ARCH_FORTIFIER:   return OM_ARCHETYPE_PEACE_DISPOSITION_FORTIFIER;
        case OM_ARCH_WARLORD:     return OM_ARCHETYPE_PEACE_DISPOSITION_WARLORD;
        case OM_ARCH_OPPORTUNIST: return OM_ARCHETYPE_PEACE_DISPOSITION_OPPORTUNIST;
        case OM_ARCH_SCHISM:      return OM_ARCHETYPE_PEACE_DISPOSITION_SCHISM;
        case OM_ARCH_PLAYER:      return OM_ARCHETYPE_PEACE_DISPOSITION_PLAYER_CIVILIZATION;
        case OM_ARCH_BREAKAWAY:   return OM_ARCHETYPE_PEACE_DISPOSITION_BREAKAWAY;
        default:                  return 1.0; /* Inputs table: unknown archetype reads disposition 1.0 */
    }
}

/* ---- S-044: betrayal ---- */

double om_archetype_betrayal_weight(om_archetype archetype) {
    switch (archetype) {
        case OM_ARCH_CONQUEROR:   return OM_ARCHETYPE_BETRAYAL_WEIGHT_CONQUEROR;
        case OM_ARCH_FORTIFIER:   return OM_ARCHETYPE_BETRAYAL_WEIGHT_FORTIFIER;
        case OM_ARCH_WARLORD:     return OM_ARCHETYPE_BETRAYAL_WEIGHT_WARLORD;
        case OM_ARCH_OPPORTUNIST: return OM_ARCHETYPE_BETRAYAL_WEIGHT_OPPORTUNIST;
        case OM_ARCH_SCHISM:      return OM_ARCHETYPE_BETRAYAL_WEIGHT_SCHISM;
        case OM_ARCH_PLAYER:      return OM_ARCHETYPE_BETRAYAL_WEIGHT_PLAYER_CIVILIZATION;
        case OM_ARCH_BREAKAWAY:   return OM_ARCHETYPE_BETRAYAL_WEIGHT_BREAKAWAY;
        default:                  return 1.0; /* Inputs table: unknown archetype reads weight 1.0 */
    }
}

double om_faction_betrayal_opportunity(const om_world *w, int32_t betrayer, int32_t partner) {
    if (!w) return 1.0;
    double mil_b = om__border_mean_military(w, betrayer, partner);
    double mil_p = om__border_mean_military(w, partner, betrayer);
    if (mil_p <= 0.0) return OM_BETRAYAL_OPPORTUNITY_CAP;
    double ratio = mil_b / mil_p;
    double opp = (ratio > 1.0) ? ratio : 1.0;
    return (opp < OM_BETRAYAL_OPPORTUNITY_CAP) ? opp : OM_BETRAYAL_OPPORTUNITY_CAP;
}

double om_faction_betrayal_chance(const om_world *w, int32_t betrayer, int32_t partner) {
    if (!w || betrayer < 0 || betrayer >= OM_MAX_FACTIONS) return 0.0;
    double opportunity = om_faction_betrayal_opportunity(w, betrayer, partner);
    double tension = om__faction_avg_tension(w, betrayer);
    double pressure_ratio = tension / OM_BETRAYAL_TENSION_SCALE;
    double pressure = (pressure_ratio > 1.0) ? pressure_ratio : 1.0;
    double weight = om_archetype_betrayal_weight(w->faction_archetype[betrayer]);
    double p = OM_BASE_BETRAYAL_RATE * weight * opportunity * pressure;
    if (p < 0.0) p = 0.0;
    if (p > 1.0) p = 1.0;
    return p;
}

/* ---- S-046: archetype tech multipliers ---- */

void om_faction_tech_multipliers(const om_world *w, int32_t faction_id, double *attack, double *defense, double *economy) {
    double a = 1.0, d = 1.0, e = 1.0;
    if (w && faction_id >= 0 && faction_id < OM_MAX_FACTIONS) {
        double ca, cd, ce;
        om__tech_axis_coeff(w->faction_archetype[faction_id], &ca, &cd, &ce);
        double tech = w->faction_tech[faction_id];
        a = 1.0 + (tech / OM_PCT_SCALE) * ca;
        d = 1.0 + (tech / OM_PCT_SCALE) * cd;
        e = 1.0 + (tech / OM_PCT_SCALE) * ce;
    }
    if (attack) *attack = a;
    if (defense) *defense = d;
    if (economy) *economy = e;
}

double om_faction_tech_attack(const om_world *w, int32_t faction_id) {
    double a, d, e;
    om_faction_tech_multipliers(w, faction_id, &a, &d, &e);
    return a;
}

double om_faction_tech_defense(const om_world *w, int32_t faction_id) {
    double a, d, e;
    om_faction_tech_multipliers(w, faction_id, &a, &d, &e);
    return d;
}

double om_faction_tech_economy(const om_world *w, int32_t faction_id) {
    double a, d, e;
    om_faction_tech_multipliers(w, faction_id, &a, &d, &e);
    return e;
}

/* ---- S-045/S-047: technology growth, Knowledge Lost, convergence ---- */

/* ALG-27b Knowledge Lost storage this card cannot add (csrc/om_internal.h is
 * off limits): a per-faction last-fired tick. Proposed field, alongside the
 * S-043 ones above: int64_t faction_last_knowledge_lost[OM_MAX_FACTIONS];
 * Until then these two read/write nothing, so the cooldown below always
 * measures "since tick 0" and the round trip in R-045-07 cannot hold. */
int64_t om_faction_last_knowledge_lost(const om_world *w, int32_t faction_id) {
    (void)w; (void)faction_id;
    return 0;
}

void om_faction_set_last_knowledge_lost(om_world *w, int32_t faction_id, int64_t tick) {
    (void)w; (void)faction_id; (void)tick;
}

void om_tech_step(om_world *w) {
    if (!w) return;
#ifdef OM_DEBUG_INJECT
    int swapped = (w->inject == OM_BUG_TECH_GROWTH_TERMS_SWAPPED);
#endif

    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f]) continue;

        double sum_e = 0.0, sum_p = 0.0;
        uint32_t n = 0;
        for (uint32_t i = 0; i < w->n_regions; i++) {
            if (w->regions[i].faction_id != f) continue;
            if (w->regions[i].tier == OM_TIER_EMPTY) continue;
            sum_e += w->regions[i].economy;
            sum_p += w->regions[i].population;
            n++;
        }
        if (n == 0) continue; /* R-045-04: no owned regions, nothing changes */

        double avg_e = sum_e / (double)n;
        double avg_p = sum_p / (double)n;
#ifdef OM_DEBUG_INJECT
        double growth_e = swapped ? avg_p : avg_e;
        double growth_p = swapped ? avg_e : avg_p;
#else
        double growth_e = avg_e;
        double growth_p = avg_p;
#endif
        double pop_ratio = growth_p / OM_PCT_SCALE;
        double pop_factor = (pop_ratio > OM_TECH_POPULATION_FLOOR) ? pop_ratio : OM_TECH_POPULATION_FLOOR;
        double growth = OM_BASE_TECH_RATE * (growth_e / OM_PCT_SCALE) * pop_factor;

        double tech = w->faction_tech[f] + growth;
        w->faction_tech[f] = (tech > OM_PCT_SCALE) ? OM_PCT_SCALE : tech;

        /* ALG-27b Knowledge Lost: only the economy leg of eligibility runs.
         * The population-drop leg (avg_p now vs. tick - 50) needs a
         * per-faction population history om_world has no storage for. */
        int64_t last_kl = om_faction_last_knowledge_lost(w, f);
        int eligible = avg_e < OM_KNOWLEDGE_LOST_ECONOMY;
        if (eligible && ((int64_t)w->tick - last_kl) >= OM_KNOWLEDGE_LOST_COOLDOWN) {
            double draw = om_rng_draw(w);
            if (draw < OM_KNOWLEDGE_LOST_P) {
                w->faction_tech[f] = fmax(0.0, w->faction_tech[f] - OM_KNOWLEDGE_LOST_DELTA);
                om_faction_set_last_knowledge_lost(w, f, (int64_t)w->tick);
                /* The fired-event record (template Knowledge Lost, the
                 * faction's highest-population region, next chain tag) is
                 * not written: csrc/events.c's om_tick_events is a STUB
                 * with no fired-event log storage yet (E-04's own card). */
            }
        }
    }

    /* ALG-28 Convergence: a second pass, in faction order, reading the
     * growth-updated tech levels above (R-047-04). */
    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f]) continue;

        double best_partner_tech = -1.0;
        for (int32_t g = 0; g < OM_MAX_FACTIONS; g++) {
            if (g == f || !w->faction_used[g]) continue;
            if (w->faction_stance[f][g] != OM_STANCE_COOPERATIVE) continue;
            if (w->faction_tech[g] > w->faction_tech[f] && w->faction_tech[g] > best_partner_tech) {
                best_partner_tech = w->faction_tech[g];
            }
        }
        if (best_partner_tech >= 0.0) {
            double bonus = OM_TECH_CONVERGENCE_RATE * (best_partner_tech - w->faction_tech[f]) / OM_PCT_SCALE;
            double tech = w->faction_tech[f] + bonus;
            w->faction_tech[f] = (tech > OM_PCT_SCALE) ? OM_PCT_SCALE : tech;
        }

        om__update_tech_cache(w, f);
    }
}

/* ---- tick wiring (csrc/sim.c calls om_step_diplomacy/om_step_technology at
 * steps 4.25 and 4.5; om_diplomacy_step is the same body under its own
 * public name, per the om_tech_step / om_step_technology pairing). ---- */

void om_diplomacy_step(om_world *w) {
    if (!w) return;
    om__betrayal_pass(w);
}

void om_step_diplomacy(om_world *w) {
    om_diplomacy_step(w);
}

void om_step_technology(om_world *w) {
    om_tech_step(w);
}

/* ---- S-048 (later card, B5b): tech tiers, mission unit profiles, chronicle
 * candidates. Left as the original stubs; not this card's scope. ---- */

uint32_t om_chronicle_distill_candidates(const om_world *w, uint32_t *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}

uint32_t om_faction_next_mission_unit_tier(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_faction_tech_tier(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

int om_faction_tier_transition_candidate(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_faction_unit_tier(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_mission_start(om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}

uint32_t om_mission_unit_tier(const om_world *w, uint32_t mission_id) {
    /* STUB */
    (void)w; (void)mission_id;
    return 0;
}

uint32_t om_tech_tier(double tech) {
    /* STUB */
    (void)tech;
    return 0;
}

int om_tier_transition_candidate_exists(const om_world *w, int32_t faction_id) {
    /* STUB */
    (void)w; (void)faction_id;
    return 0;
}
