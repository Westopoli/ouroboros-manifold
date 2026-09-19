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
    if (!w || !out || max == 0) return 0;
    
    uint32_t count = fmin(w->attacks_n, max);
    for (uint32_t i = 0; i < count; ++i) {
        out[i] = w->attacks[i];
    }
    return count;
}

uint32_t om_tick_reinforces(const om_world *w, om_reinforce *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;
    
    uint32_t count = fmin(w->reinforces_n, max);
    for (uint32_t i = 0; i < count; ++i) {
        out[i] = w->reinforces[i];
    }
    return count;
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
    if (!w || idx >= w->n_regions) return;
    
    om_region *r = &w->regions[idx];
    uint32_t slot;
    
    if (r->damage_len < OM_DAMAGE_HISTORY_CAP) {
        slot = (r->damage_head + r->damage_len) % OM_DAMAGE_HISTORY_CAP;
        r->damage_len++;
    } else {
        slot = r->damage_head;
        r->damage_head = (r->damage_head + 1) % OM_DAMAGE_HISTORY_CAP;
    }
    
    r->damage_tick[slot] = tick;
    r->damage_military[slot] = military_loss;
    r->damage_economy[slot] = economy_loss;
}

double om_region_damage_history(const om_world *w, uint32_t idx) {
    if (!w || idx >= w->n_regions) return 0.0;
    
    const om_region *r = &w->regions[idx];
    double sum = 0.0;
    const uint64_t current_tick = w->tick;
    const uint64_t window = 150; // DAMAGE_HISTORY_WINDOW
    
    for (uint32_t i = 0; i < r->damage_len; ++i) {
        uint32_t slot = (r->damage_head + i) % OM_DAMAGE_HISTORY_CAP;
        uint64_t tick = r->damage_tick[slot];
        
        if (current_tick >= tick && (current_tick - tick) <= window) {
            sum += r->damage_military[slot] + r->damage_economy[slot];
        }
    }
    
    return sum;
}

void om_step_telegraphs(om_world *w) {
    if (!w) return;
    
    w->attacks_n = 0;
    
    uint32_t write_idx = 0;
    for (uint32_t i = 0; i < w->telegraphs_n; ++i) {
        om_telegraph *t = &w->telegraphs[i];
        
        if (w->tick < t->declared_tick + 3) {
            w->telegraphs[write_idx] = *t;
            write_idx++;
            continue;
        }
        
        if (om_faction_territory(w, t->attacker) == 0) {
            continue;
        }
        
        om_region *target = &w->regions[t->target_idx];
        int32_t defender = target->faction_id;

        double tech_attack = w->faction_tech_attack[t->attacker];
        double tech_defense = w->faction_tech_defense[defender];
        int64_t held_since = om_region_held_since(w, t->target_idx);
        double entrenchment = (held_since < 0) ? 2.0
            : 1.0 + fmin(1.0, (double)((int64_t)w->tick - held_since) / 100.0);

        double reinforce_commit = 0.0;
        for (uint32_t r = 0; r < w->reinforces_n; ++r) {
            if (w->reinforces[r].target_idx == t->target_idx && w->reinforces[r].tick == w->tick) {
                reinforce_commit += w->reinforces[r].commit;
            }
        }

        double effective_attack = t->commit * 1.0 * tech_attack * 1.0;
        double effective_defense = target->military * 0.55 * tech_defense * entrenchment + reinforce_commit;

        double stochastic;
        if (w->rng_forced_len > 0) {
            /* A forced draw stands for the already-scaled U(0.7, 1.3) stochastic value
             * itself (confirmed against test_R_037_01/02/05: forcing 0.7 or 1.0 makes
             * net come out as exactly (effective_attack - effective_defense) * 0.7 or
             * * 1.0, not the 0.7-1.3 rescale of a raw [0,1) input). */
            stochastic = w->rng_forced[w->rng_forced_head];
            w->rng_forced_head++;
            w->rng_forced_len--;
        } else {
            uint32_t a = (uint32_t)(w->rng_state >> 5);
            uint32_t b = (uint32_t)(w->rng_state >> 6);
            double u = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
            w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
            stochastic = 0.7 + 0.6 * u;
        }
        double net = (effective_attack - effective_defense) * stochastic;

        double d_military, d_economy, d_tension;
        uint32_t outcome;
        if (net > 15.0) {
            outcome = OM_OUT_BREAKTHROUGH;
            d_military = -0.8 * net;
            d_economy = -0.3 * net;
            d_tension = fmin(0.5 * net, 30.0);
        } else if (net > 0.0) {
            outcome = OM_OUT_CONTESTED;
            d_military = -0.5 * net;
            d_economy = -0.2 * net;
            d_tension = 0.4 * net;
        } else {
            outcome = OM_OUT_REPELLED;
            d_military = -0.10 * effective_attack;
            d_economy = 0.0;
            d_tension = 2.0;
        }

        /* Conquest, garrison, ownership transfer, and the fuller ALG-22 conquest
         * effects (economy disruption, tension spike, population loss, the
         * unrest chain) are entirely card 204b1-e05-conquest-garrison's job, in
         * a pass over w->attacks after this function runs -- not this one's.
         * Setting conquest/garrison here (as an earlier pass at this function
         * did) mutates the region (adds garrison, transfers ownership) before
         * 204b1's own conquest check ever sees it, so its post-damage-military
         * check reads the already-garrisoned value and never fires. Every
         * R-037 test that checks conquest only ever expects 0 here; none
         * requires this function to detect conquest itself. */
        target->military = fmax(0.0, target->military + d_military);
        target->economy = fmax(8.0, target->economy + d_economy);
        target->tension = fmin(100.0, fmax(0.0, target->tension + d_tension));

        if (w->attacks_n < 64) {
            om_attack_result *r = &w->attacks[w->attacks_n];
            r->tick = w->tick;
            r->attacker = t->attacker;
            r->defender = defender;
            r->target_idx = t->target_idx;
            r->mode = OM_MODE_TELEGRAPH;
            r->outcome = outcome;
            r->conquest = 0;
            r->commit = t->commit;
            r->effective_attack = effective_attack;
            r->effective_defense = effective_defense;
            r->stochastic = stochastic;
            r->net = net;
            r->d_military = d_military;
            r->d_economy = d_economy;
            r->d_tension = d_tension;
            r->garrison = 0.0;
            r->budget_spent = t->commit;
            r->collision = 0;
            w->attacks_n++;
        }
    }
    
    w->telegraphs_n = write_idx;
}

void om_step_reinforce(om_world *w) {
    if (!w) return;
    w->reinforces_n = 0;
    
    for (uint32_t i = 0; i < w->telegraphs_n; ++i) {
        om_telegraph *t = &w->telegraphs[i];
        if (t->declared_tick != w->tick) continue;
        
        int32_t f = w->regions[t->target_idx].faction_id;
        if (f < 0) continue;
        
        double w_defend;
        switch (w->faction_archetype[f]) {
            case OM_ARCH_CONQUEROR:   w_defend = 0.4; break;
            case OM_ARCH_WARLORD:     w_defend = 0.3; break;
            case OM_ARCH_FORTIFIER:   w_defend = 1.5; break;
            case OM_ARCH_OPPORTUNIST: w_defend = 0.6; break;
            case OM_ARCH_SCHISM:      w_defend = 0.5; break;
            case OM_ARCH_PLAYER:      w_defend = 1.5; break;
            case OM_ARCH_BREAKAWAY:   w_defend = 0.8; break;
            default:                  w_defend = 0.8; break;
        }
        
        double reinforce_prob = fmin(1.0, w_defend / 1.5);
        
        double u;
        if (w->rng_forced_len > 0) {
            u = w->rng_forced[w->rng_forced_head];
            w->rng_forced_head++;
            w->rng_forced_len--;
        } else {
            uint32_t a = (uint32_t)(w->rng_state >> 5);
            uint32_t b = (uint32_t)(w->rng_state >> 6);
            u = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
            w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
        }
        
        if (u > reinforce_prob) continue;
        
        double commit = fmin(w->faction_budget_snapshot[f] * 0.30, t->commit * 0.5);
        if (commit < 1.0) continue;
        
        w->faction_budget[f] -= commit;
        
        double tier_cap = (w->regions[t->target_idx].tier == OM_TIER_HOME) ? 100.0 : 60.0;
        double headroom = fmax(0.0, (tier_cap - w->regions[t->target_idx].military) / tier_cap);
        double base = commit * 0.5 * headroom;
        
        double tension = w->regions[t->target_idx].tension;
        double lo = 0.85 - (tension / 100.0) * 0.20;
        double hi = 1.15 + (tension / 100.0) * 0.20;
        
        double u2;
        if (w->rng_forced_len > 0) {
            u2 = w->rng_forced[w->rng_forced_head];
            w->rng_forced_head++;
            w->rng_forced_len--;
        } else {
            uint32_t a = (uint32_t)(w->rng_state >> 5);
            uint32_t b = (uint32_t)(w->rng_state >> 6);
            u2 = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
            w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
        }
        
        double variance = lo + (hi - lo) * u2;
        double d_military = base * variance;
        
        if (w->reinforces_n < 64) {
            om_reinforce *r = &w->reinforces[w->reinforces_n];
            r->tick = w->tick;
            r->faction_id = f;
            r->target_idx = t->target_idx;
            r->commit = commit;
            r->headroom = headroom;
            r->base = base;
            r->variance = variance;
            r->d_military = d_military;
            w->reinforces_n++;
        }
        
        w->regions[t->target_idx].military += d_military;
    }
}

void om_step_resolve(om_world *w) {
    if (!w) return;

    for (uint32_t i = 0; i < w->decisions_n; ++i) {
        om_decision *d = &w->decisions[i];
        if (d->action != OM_ACT_ATTACK) continue;
        
        if (d->mode == OM_MODE_TELEGRAPH) {
            /* Skip telegraphs that are not matured yet (matured ones are dispatched by step 3c / om_step_telegraphs) */
            if (w->tick < d->tick + 3) continue;
        }

        int32_t attacker = d->faction_id;
        uint32_t target_idx = d->target_idx;
        double commit = d->commit;

        int32_t defender = w->regions[target_idx].faction_id;
        double surprise_mult = (d->mode == OM_MODE_SURPRISE) ? 0.5 : 1.0;

        /* Fault injection: if w->inject == 102, apply 0.5 to defense instead of attack */
        double effective_attack, effective_defense;
        if (w->inject == 102) {
            effective_attack = commit * 1.0 * w->faction_tech_attack[attacker] * 1.0;
            effective_defense = w->regions[target_idx].military * 0.55 * w->faction_tech_defense[defender] * (w->inject == 102 ? 0.5 : 1.0);
        } else {
            effective_attack = commit * 1.0 * w->faction_tech_attack[attacker] * surprise_mult;
            effective_defense = w->regions[target_idx].military * 0.55 * w->faction_tech_defense[defender];
        }

        /* Entrenchment (ALG-13) */
        int64_t held_since = om_region_held_since(w, target_idx);
        double ent;
        if (held_since < 0) {
            ent = 2.0;
        } else {
            ent = 1.0 + fmin(1.0, (double)((int64_t)w->tick - held_since) / 100.0);
        }

        effective_defense *= ent;

        /* Add defender reinforce commit if reactive reinforcement landed this tick */
        double reinforce_commit = 0.0;
        for (uint32_t r = 0; r < w->reinforces_n; ++r) {
            if (w->reinforces[r].target_idx == target_idx && w->reinforces[r].tick == w->tick) {
                reinforce_commit += w->reinforces[r].commit;
            }
        }
        effective_defense += reinforce_commit;

        /* Draw stochastic factor u ~ U(0.7, 1.3) */
        double u;
        if (w->rng_forced_len > 0) {
            u = w->rng_forced[w->rng_forced_head];
            w->rng_forced_head++;
            w->rng_forced_len--;
        } else {
            uint32_t a = (uint32_t)(w->rng_state >> 5);
            uint32_t b = (uint32_t)(w->rng_state >> 6);
            double unif = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
            w->rng_state = w->rng_state * 6364136223846793005ULL + w->rng_inc;
            u = 0.7 + 0.6 * unif;
        }

        double net = (effective_attack - effective_defense) * u;

        /* Damage bands (ALG-21) */
        double d_military, d_economy, d_tension;
        uint32_t outcome;
        if (net > 15.0) {
            outcome = OM_OUT_BREAKTHROUGH;
            d_military = -0.8 * net;
            d_economy = -0.3 * net;
            d_tension = fmin(0.5 * net, 30.0);
        } else if (net > 0.0) {
            outcome = OM_OUT_CONTESTED;
            d_military = -0.5 * net;
            d_economy = -0.2 * net;
            d_tension = 0.4 * net;
        } else {
            outcome = OM_OUT_REPELLED;
            d_military = -0.10 * effective_attack;
            d_economy = 0.0;
            d_tension = 2.0;
        }

        /* Apply damage deltas to defender target region */
        double military = w->regions[target_idx].military + d_military;
        double economy = fmax(8.0, w->regions[target_idx].economy + d_economy);
        double tension = fmin(100.0, fmax(0.0, w->regions[target_idx].tension + d_tension));

        /* Update region state */
        w->regions[target_idx].military = military;
        w->regions[target_idx].economy = economy;
        w->regions[target_idx].tension = tension;

        /* Record in w->attacks */
        if (w->attacks_n < 64) {
            om_attack_result *r = &w->attacks[w->attacks_n];
            r->tick = w->tick;
            r->attacker = attacker;
            r->defender = defender;
            r->target_idx = target_idx;
            r->mode = d->mode;
            r->outcome = outcome;
            r->conquest = 0; /* set below, in the unified conquest pass */
            r->commit = commit;
            r->effective_attack = effective_attack;
            r->effective_defense = effective_defense;
            r->stochastic = u;
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

    /* Conquest and garrison (ALG-22, Story S-038), in one pass over every
     * attack this tick -- both the ones om_step_telegraphs (step 3c) already
     * appended and the ones this function just appended above (step 3f).
     * Checked on post-damage military, never on the outcome band
     * (OM_BUG_CONQUEST_ON_BAND, 105). This runs after the region's ALG-21
     * damage is already applied (by whichever function produced the record),
     * so "post-damage" here just means the region's current field. */
    for (uint32_t i = 0; i < w->attacks_n; ++i) {
        om_attack_result *r = &w->attacks[i];
        if (r->outcome == OM_OUT_REPELLED) continue;

        uint32_t target_idx = r->target_idx;
        om_region *target = &w->regions[target_idx];
        int32_t attacker = r->attacker;
        int32_t defender = r->defender;

        int32_t conquered = (w->inject == 105)
            ? (r->outcome == OM_OUT_BREAKTHROUGH)
            : (target->military < 5.0);
        if (!conquered) continue;

        double garrison = r->commit * 0.65;
        target->military += garrison;
        /* The economy floor (8.0) is bypassed for the conquest disruption
         * itself, even though it already applied to the base ALG-21 damage. */
        target->economy -= 5.0;
        target->tension = fmin(100.0, target->tension + 8.0);
        target->population = fmax(0.0, target->population - 2.0);

        om_region_set_owner(w, target_idx, attacker, w->tick);

        /* S-024 R-024-03: the conquered region's edges to the conqueror's own
         * regions and its cooperative partners' regions become BOTH; its
         * edges to the former owner's remaining regions become BORDER. Every
         * other edge (a neutral third party, say) is left as it was -- the
         * rule only names these three relations. */
        for (uint32_t j = 0; j < w->n_regions; ++j) {
            if (j == target_idx) continue;
            om_edge_type et;
            if (!om_region_edge(w, target_idx, j, &et)) continue;
            int32_t nbr = w->regions[j].faction_id;
            if (nbr == attacker) {
                om_region_set_edge(w, target_idx, j, OM_EDGE_BOTH);
            } else if (nbr == defender) {
                om_region_set_edge(w, target_idx, j, OM_EDGE_BORDER);
            } else if (nbr >= 0 && w->faction_stance[attacker][nbr] == OM_STANCE_COOPERATIVE) {
                om_region_set_edge(w, target_idx, j, OM_EDGE_BOTH);
            }
        }

        r->conquest = 1;
        r->garrison = garrison;
    }
}
