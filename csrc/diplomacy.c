/* csrc/diplomacy.c — E-06 diplomacy and technology (card B5).
 * Stance table (S-042), peace formation (S-043), betrayal (S-044),
 * technology growth/convergence (S-045/S-046/S-047) are implemented below,
 * backed by F2e's faction_stance_counter / faction_cooperative_since /
 * faction_last_knowledge_lost storage (csrc/om_internal.h). Knowledge
 * Lost's fired-event record (part of S-045 R-045-07) stays unwritten:
 * csrc/events.c's om_tick_events has no fired-event log storage yet
 * (that epic's own card), and this card may only edit this file.
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

/* True if region_idx has any edge (any type -- the general adjacency graph,
 * not the OM_EDGE_BORDER type specifically) to a region owned by other. */
static int om__region_borders_faction(const om_world *w, uint32_t region_idx, int32_t other) {
    for (uint32_t j = 0; j < w->n_regions; j++) {
        if (w->regions[j].faction_id != other) continue;
        om_edge_type et;
        if (om_region_edge(w, region_idx, j, &et)) return 1;
    }
    return 0;
}

/* Mean military of owner's regions bordering other -- ALG-40's "border
 * military". */
static double om__border_mean_military(const om_world *w, int32_t owner, int32_t other) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != owner) continue;
        if (!om__region_borders_faction(w, i, other)) continue;
        sum += w->regions[i].military;
        n++;
    }
    return (n > 0) ? (sum / (double)n) : 0.0;
}

static int om__find_weakest_bordering(const om_world *w, int32_t attacker, int32_t victim, uint32_t *out_idx) {
    int found = 0;
    double best_mil = 0.0;
    uint32_t best_idx = 0;
    for (uint32_t j = 0; j < w->n_regions; j++) {
        if (w->regions[j].faction_id != victim) continue;
        if (!om__region_borders_faction(w, j, attacker)) continue;
        if (!found || w->regions[j].military < best_mil) {
            best_mil = w->regions[j].military;
            best_idx = j;
            found = 1;
        }
    }
    if (found) *out_idx = best_idx;
    return found;
}

/* Every existing edge between an a-owned region and a b-owned region
 * becomes edge_type -- ALG-39's "shared edges become both" and ALG-40's
 * "shared edges become border" are the same rewrite with a different type. */
static void om__set_shared_edges(om_world *w, int32_t a, int32_t b, om_edge_type edge_type) {
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != a) continue;
        for (uint32_t j = 0; j < w->n_regions; j++) {
            if (w->regions[j].faction_id != b) continue;
            om_edge_type et;
            if (om_region_edge(w, i, j, &et)) {
                om_region_set_edge(w, i, j, edge_type);
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
    /* Edge retype (R-024-02) is om__enforce_stance_edges's job, run once at
     * the end of om_diplomacy_step over every pair's current stance. */

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

    if (w->attacks_n < OM_MAX_REGIONS) {
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

/* ---- S-043: peace formation (ALG-38/39) helpers ---- */

static int om__pair_has_edge(const om_world *w, int32_t a, int32_t b) {
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != a) continue;
        if (om__region_borders_faction(w, i, b)) return 1;
    }
    return 0;
}

static int om__pair_attacked_this_tick(const om_world *w, int32_t a, int32_t b) {
    for (uint32_t i = 0; i < w->attacks_n; i++) {
        const om_attack_result *r = &w->attacks[i];
        if (r->tick != w->tick) continue;
        if ((r->attacker == a && r->defender == b) || (r->attacker == b && r->defender == a)) return 1;
    }
    return 0;
}

static double om__faction_avg_economy(const om_world *w, int32_t f) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != f) continue;
        sum += w->regions[i].economy;
        n++;
    }
    return (n > 0) ? (sum / (double)n) : 0.0;
}

static double om__avg_border_stability(const om_world *w, int32_t owner, int32_t other) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != owner) continue;
        if (!om__region_borders_faction(w, i, other)) continue;
        sum += om_region_composite(w, i, OM_C_STABILITY);
        n++;
    }
    return (n > 0) ? (sum / (double)n) : 0.0;
}

/* ALG-39: a<b already NEUTRAL and sharing a border, counter just updated by
 * om__peace_pass and read as the current value. */
static void om__peace_check_overture(om_world *w, int32_t a, int32_t b) {
    double stab_a = om__avg_border_stability(w, a, b);
    double stab_b = om__avg_border_stability(w, b, a);
    double stab = (stab_a < stab_b) ? stab_a : stab_b;

    if (stab < OM_PEACE_STABILITY_THRESHOLD) {
        om_faction_set_stance_counter(w, a, b, 0);
        return;
    }

    double avg_e_a = om__faction_avg_economy(w, a);
    double avg_e_b = om__faction_avg_economy(w, b);
    double econ_diff = avg_e_a - avg_e_b;
    if (econ_diff < 0.0) econ_diff = -econ_diff;
    double compatibility = 1.0 - (econ_diff / OM_PCT_SCALE);
    double disp_a = om_archetype_peace_disposition(w->faction_archetype[a]);
    double disp_b = om_archetype_peace_disposition(w->faction_archetype[b]);

    double p = OM_PEACE_BASE_PROBABILITY * compatibility * (stab / OM_PCT_SCALE) * disp_a * disp_b;
    if (p < 0.0) p = 0.0;
    if (p > 1.0) p = 1.0;

    double draw = om_rng_draw(w);
    if (draw < p) {
        w->faction_stance[a][b] = OM_STANCE_COOPERATIVE;
        w->faction_stance[b][a] = OM_STANCE_COOPERATIVE;
        w->faction_cooperative_since[a][b] = w->tick;
        w->faction_cooperative_since[b][a] = w->tick;
        /* Edge retype (R-024-01) is om__enforce_stance_edges's job, run once
         * at the end of om_diplomacy_step over every pair's current stance. */
    } else {
        om_faction_set_stance_counter(w, a, b, 0);
    }
}

static void om__peace_pass(om_world *w) {
    for (int32_t a = 0; a < OM_MAX_FACTIONS; a++) {
        if (!w->faction_used[a]) continue;
        for (int32_t b = a + 1; b < OM_MAX_FACTIONS; b++) {
            if (!w->faction_used[b]) continue;
            if (w->faction_stance[a][b] != OM_STANCE_NEUTRAL) continue;
            if (!om__pair_has_edge(w, a, b)) continue;

            uint32_t counter = om__pair_attacked_this_tick(w, a, b)
                ? 0 : om_faction_stance_counter(w, a, b) + 1;
            om_faction_set_stance_counter(w, a, b, counter);

            if (counter >= OM_PEACE_FORMATION_THRESHOLD) {
                om__peace_check_overture(w, a, b);
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

/* ---- S-043: peace formation (ALG-38/39), backed by F2e's
 * faction_stance_counter / faction_cooperative_since (csrc/om_internal.h). ---- */

uint32_t om_faction_stance_counter(const om_world *w, int32_t p0, int32_t faction) {
    if (!w || p0 < 0 || p0 >= OM_MAX_FACTIONS || faction < 0 || faction >= OM_MAX_FACTIONS) return 0;
    return w->faction_stance_counter[p0][faction];
}

void om_faction_set_stance_counter(om_world *w, int32_t p0, int32_t p1, uint32_t counter) {
    if (!w || p0 < 0 || p0 >= OM_MAX_FACTIONS || p1 < 0 || p1 >= OM_MAX_FACTIONS) return;
    w->faction_stance_counter[p0][p1] = counter;
    w->faction_stance_counter[p1][p0] = counter;
}

uint64_t om_faction_cooperative_since(const om_world *w, int32_t p0, int32_t p1) {
    if (!w || p0 < 0 || p0 >= OM_MAX_FACTIONS || p1 < 0 || p1 >= OM_MAX_FACTIONS) return 0;
    return w->faction_cooperative_since[p0][p1];
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

/* ALG-27b Knowledge Lost, backed by F2e's faction_last_knowledge_lost
 * (csrc/om_internal.h; -1 = never, set by csrc/region.c's om_world_new). */
int64_t om_faction_last_knowledge_lost(const om_world *w, int32_t faction_id) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS) return -1;
    return w->faction_last_knowledge_lost[faction_id];
}

void om_faction_set_last_knowledge_lost(om_world *w, int32_t faction_id, int64_t tick) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS) return;
    w->faction_last_knowledge_lost[faction_id] = tick;
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
        uint32_t highest_pop_idx = 0;
        double highest_pop = -1.0;
        for (uint32_t i = 0; i < w->n_regions; i++) {
            if (w->regions[i].faction_id != f) continue;
            if (w->regions[i].tier == OM_TIER_EMPTY) continue;
            sum_e += w->regions[i].economy;
            sum_p += w->regions[i].population;
            n++;
            if (w->regions[i].population > highest_pop) {
                highest_pop = w->regions[i].population;
                highest_pop_idx = i;
            }
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
                /* B1-2's om_event_fire_manual (ALG-49) attaches the region's
                 * regional/supreme commander at this significance tier; it
                 * writes to events.c's manual-fire table, not the
                 * trigger-pipeline s->fired[]/om_tick_events log.
                 * F2h's om_event_register_external gets Knowledge Lost a
                 * real template id in that same pipeline (idempotent by
                 * name, so registering again next time is a lookup, not a
                 * duplicate); om_event_queue_external then queues it so it
                 * reaches om_tick_events -- but only one tick later, at the
                 * queued due_tick's own step 1-2 (om_event_queue_external
                 * rejects due_tick <= the current tick), and only if
                 * OM_FEAT_EVENTS is on (csrc/sim.c gates om_step_events on
                 * it; E-06's test fixtures leave it off -- isolate_agents
                 * turns it off explicitly, and it is not one of the two
                 * features world_factory turns on for this epic's module).
                 * A single-step E-06 test, or one that never enables
                 * EVENTS, will not see this record in read_events(). */
                om_event_fire_manual(w, highest_pop_idx, OM_CHARACTER_ATTACHMENT_TIER_THRESHOLD);
                int32_t kl_template = om_event_register_external(w, "Knowledge Lost",
                    OM_CHARACTER_ATTACHMENT_TIER_THRESHOLD);
                if (kl_template >= 0) {
                    om_event_queue_external(w, highest_pop_idx, (uint32_t)kl_template,
                        w->tick + 1, 1.0, f, 0);
                }
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

/* E-03 S-024 invariant (R-024-01/02, docs/bible/epics/E-03-*.md; matches the
 * E-06 epic's own "cooperative implies both, hostile implies border"
 * invariant): every shared edge follows the pair's current stance,
 * regardless of how that stance got there -- the direct om_faction_set_stance
 * setter included, per test_E03_S024_politics_redraws_the_routes.py's own
 * fixtures. Run once, after betrayal and peace have applied this tick's
 * transitions, so it retypes from the up-to-date stance table. A neutral
 * pair's edges are left as they are (no invariant governs them). */
static void om__enforce_stance_edges(om_world *w) {
    for (int32_t a = 0; a < OM_MAX_FACTIONS; a++) {
        if (!w->faction_used[a]) continue;
        for (int32_t b = a + 1; b < OM_MAX_FACTIONS; b++) {
            if (!w->faction_used[b]) continue;
            om_stance s = w->faction_stance[a][b];
            if (s == OM_STANCE_COOPERATIVE) {
                om__set_shared_edges(w, a, b, OM_EDGE_BOTH);
            } else if (s == OM_STANCE_HOSTILE) {
                om__set_shared_edges(w, a, b, OM_EDGE_BORDER);
            }
        }
    }
}

void om_diplomacy_step(om_world *w) {
    if (!w) return;
    om__betrayal_pass(w);
    om__peace_pass(w);
    om__enforce_stance_edges(w);
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
