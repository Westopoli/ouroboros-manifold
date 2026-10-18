/* csrc/agent.c — E-05 faction agent decisions (build card 203).
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
#include <float.h>
#include <stdint.h>
#include <math.h>

static inline double clamp(double v, double lo, double hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}
uint32_t om_faction_candidates(const om_world *w, int32_t faction_id, om_candidate *out, uint32_t max) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS || !w->faction_used[faction_id] || !out || max == 0) {
        return 0;
    }

    om_archetype archetype = w->faction_archetype[faction_id];
    double w_weakness, w_value, w_position;
    int tension_primary, can_colonize;
    double boost = 0.0;

    switch (archetype) {
        case OM_ARCH_CONQUEROR:
            w_weakness = 0.40; w_value = 0.25; w_position = 0.35;
            tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_WARLORD:
            w_weakness = 0.20; w_value = 0.35; w_position = 0.45;
            tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_FORTIFIER:
            w_weakness = 0.25; w_value = 0.20; w_position = 0.55;
            tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_OPPORTUNIST:
            w_weakness = 0.35; w_value = 0.30; w_position = 0.35;
            tension_primary = 0; can_colonize = 1;
            boost = 1.5;
            break;
        case OM_ARCH_SCHISM:
            w_weakness = 0.20; w_value = 0.30; w_position = 0.50;
            tension_primary = 1; can_colonize = 0;
            break;
        case OM_ARCH_PLAYER:
            w_weakness = 0.60; w_value = 0.25; w_position = 0.15;
            tension_primary = 0; can_colonize = 1;
            break;
        case OM_ARCH_BREAKAWAY:
            w_weakness = 0.45; w_value = 0.30; w_position = 0.25;
            tension_primary = 0; can_colonize = 1;
            break;
        default:
            w_weakness = 0.40; w_value = 0.30; w_position = 0.30;
            tension_primary = 0; can_colonize = 1;
            break;
    }

    uint32_t count = 0;
    int seen[OM_MAX_REGIONS] = {0};

    double weakest_mil = DBL_MAX;

    for (uint32_t i = 0; i < w->n_regions && count < max; ++i) {
        if (w->regions[i].faction_id != faction_id) continue;

        for (uint32_t j = 0; j < w->n_regions && count < max; ++j) {
            om_edge_type edge_type;
            if (i == j || !om_region_edge(w, i, j, &edge_type) || seen[j]) continue;

            int32_t owner = w->regions[j].faction_id;
            om_candidate_kind kind = OM_CAND_ATTACK;

            if (owner < 0) {
                if (!can_colonize) continue;
                kind = OM_CAND_COLONIZE;
            } else {
                om_stance stance1 = w->faction_stance[faction_id][owner];
                om_stance stance2 = w->faction_stance[owner][faction_id];
                if (stance1 != OM_STANCE_HOSTILE && stance2 != OM_STANCE_HOSTILE) continue;
            }

            double factor_1 = 0.0;
            if (tension_primary) {
                factor_1 = w->regions[j].tension / 100.0;
            } else {
                factor_1 = 1.0 - w->regions[j].military / 100.0;
            }

            double current_value = 0.0;
            if (owner >= 0) {
                current_value = ((w->regions[j].economy * 0.60 + w->regions[j].population * 0.40) / 100.0) * 2.0;
            }

            if (owner >= 0 && current_value < 0.05) continue;

            double strategic_position = 0.0;
            uint32_t neighbor_count = 0;
            for (uint32_t k = 0; k < w->n_regions; ++k) {
                om_edge_type edge_type_k;
                if (j == k || !om_region_edge(w, j, k, &edge_type_k)) continue;

                int32_t neighbor_owner = w->regions[k].faction_id;
                if (neighbor_owner == faction_id) continue;

                double score = 0.0;
                if (neighbor_owner < 0) {
                    score = 0.15; // EXPANSION_POTENTIAL
                } else {
                    score = (w->regions[k].economy * 0.60 + w->regions[k].population * 0.40) / 100.0;
                }
                strategic_position += score;
                neighbor_count++;
            }

            if (neighbor_count > 0) {
                strategic_position /= neighbor_count;
            } else {
                strategic_position = 0.0;
            }

            double attractiveness = w_weakness * factor_1 + w_value * current_value + w_position * strategic_position;

            if (boost != 0.0 && owner >= 0) {
                double damage = om_region_damage_history(w, j);
                attractiveness *= 1.0 + (damage / 100.0) * boost;
            }

            out[count].region_idx = j;
            out[count].kind = kind;
            out[count].weakness = factor_1;
            out[count].value = current_value;
            out[count].position = strategic_position;
            out[count].attractiveness = attractiveness;
            out[count].entrenchment = 0.0;
            out[count].net = 0.0;
            out[count].viable = 0;
            out[count]._pad = 0;

            if (kind == OM_CAND_ATTACK) {
                double m = w->regions[j].military;
                if (m < weakest_mil) weakest_mil = m;
            }

            seen[j] = 1;
            count++;
        }
    }

    double potential_commit;
    if (w->inject == 100) { // OM_BUG_AGENT_READS_LIVE
        potential_commit = w->faction_budget[faction_id] * 0.70;
    } else {
        potential_commit = w->faction_budget_snapshot[faction_id] * 0.70;
    }

    double break_even = 0.0;
    if (weakest_mil != DBL_MAX) {
        break_even = (weakest_mil * 0.55) / 0.70;
    }
    double effective_confidence = w->faction_confidence[faction_id];
    if (break_even > 0.0) {
        double ratio = (potential_commit / 0.70) / break_even;
        if (ratio > OM_BUDGET_PRESSURE_THRESHOLD) { /* ALG-12 OM_BUDGET_PRESSURE_THRESHOLD */
            effective_confidence *= OM_BUDGET_PRESSURE_THRESHOLD / ratio;
        }
    }

    for (uint32_t i = 0; i < count; ++i) {
        om_candidate *c = &out[i];
        if (c->kind == OM_CAND_COLONIZE) {
            c->entrenchment = 0.0;
            c->net = 0.0;
            c->viable = 0;
        } else {
            int64_t held_since;
            if (w->inject == 103) { // OM_BUG_ENTRENCH_CURRENT_TICK
                held_since = w->tick; // use live tick instead of held_since
            } else {
                held_since = om_region_held_since(w, c->region_idx);
            }
            double ent = (held_since < 0) ? 2.0
                                          : 1.0 + clamp((w->tick - held_since) / 100.0, 0.0, 1.0);
            c->entrenchment = ent;
            c->net = potential_commit - w->regions[c->region_idx].military * 0.55 * ent;
            c->viable = (c->net > effective_confidence) ? 1 : 0;
        }
    }

    return count;
}

uint32_t om_tick_decisions(const om_world *w, om_decision *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;
    uint32_t n = (w->decisions_n < max) ? w->decisions_n : max;
    memcpy(out, w->decisions, n * sizeof(om_decision));
    return n;
}

uint32_t om_pending_telegraphs(const om_world *w, om_telegraph *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;
    
    uint32_t count = 0;
    uint32_t limit = (w->telegraphs_n < max) ? w->telegraphs_n : max;
    
    for (uint32_t i = 0; i < limit; ++i) {
        out[count] = w->telegraphs[i];
        count++;
    }
    
    return count;
}

void om_step_decisions(om_world *w) {
    if (!w) return;

    /* R8 (DECISIONS.md): om_intent_inject writes directly into w->decisions
     * before this step runs, stamped with the tick it applies to (w->tick,
     * here, since om_intent_inject reads w->tick before the increment). A
     * faction with such an entry skips its own recompute below (the header's
     * documented om_intent_inject contract); preserve those entries instead
     * of wiping them with the rest. */
    om_decision preserved[OM_MAX_REGIONS];
    uint32_t n_preserved = 0;
    int injected_faction[OM_MAX_FACTIONS] = {0};
#ifdef OM_DEBUG_INJECT
    if (w->inject != OM_BUG_INJECT_IGNORED) {
#endif
        for (uint32_t i = 0; i < w->decisions_n && n_preserved < OM_MAX_REGIONS; ++i) {
            if (w->decisions[i].tick == w->tick) {
                preserved[n_preserved++] = w->decisions[i];
                int32_t fid = w->decisions[i].faction_id;
                if (fid >= 0 && fid < OM_MAX_FACTIONS) injected_faction[fid] = 1;
            }
        }
#ifdef OM_DEBUG_INJECT
    }
#endif
    w->decisions_n = 0;
    for (uint32_t i = 0; i < n_preserved; ++i) {
        w->decisions[w->decisions_n++] = preserved[i];
    }

    om_candidate candidates[OM_MAX_REGIONS];
    for (int f = 0; f < OM_MAX_FACTIONS && w->decisions_n < OM_MAX_REGIONS; ++f) {
        if (!w->faction_used[f]) continue;
        if (injected_faction[f]) continue;
        uint32_t n = om_faction_candidates(w, f, candidates, OM_MAX_REGIONS);

        om_candidate *best_attack = NULL;
        om_candidate *best_colonize = NULL;
        for (uint32_t i = 0; i < n; ++i) {
            if (candidates[i].kind == OM_CAND_ATTACK && candidates[i].viable) {
                /* ALG-14/15 (C3, DECISIONS.md Seventh round): at most one
                 * resolved attack per attacker-target pair per tick. A target
                 * this faction already has a resolved attack against this
                 * tick (from step 3c's telegraph maturation, which runs
                 * before this step) is not re-declared against; the
                 * follow-up waits for the next tick. */
                int already_resolved = 0;
#ifdef OM_DEBUG_INJECT
                if (w->inject != OM_BUG_SAME_TICK_REDECLARE) {
#endif
                    for (uint32_t k = 0; k < w->attacks_n; ++k) {
                        if (w->attacks[k].tick == w->tick &&
                            w->attacks[k].attacker == f &&
                            w->attacks[k].target_idx == candidates[i].region_idx) {
                            already_resolved = 1;
                            break;
                        }
                    }
#ifdef OM_DEBUG_INJECT
                }
#endif
                if (already_resolved) continue;
                if (!best_attack || candidates[i].attractiveness > best_attack->attractiveness)
                    best_attack = &candidates[i];
            } else if (candidates[i].kind == OM_CAND_COLONIZE) {
                if (!best_colonize || candidates[i].attractiveness > best_colonize->attractiveness)
                    best_colonize = &candidates[i];
            }
        }

        // Compute potential_commit, weakest military, break_even, effective_confidence
        double potential_commit = w->faction_budget_snapshot[f] * 0.70;
        double weakest_mil = DBL_MAX;
        for (uint32_t i = 0; i < n; ++i) {
            if (candidates[i].kind == OM_CAND_ATTACK) {
                double m = w->regions[candidates[i].region_idx].military;
                if (m < weakest_mil) weakest_mil = m;
            }
        }
        double break_even = 0.0;
        if (weakest_mil != DBL_MAX) break_even = (weakest_mil * 0.55) / 0.70;
        double effective_confidence = w->faction_confidence[f];
        if (break_even > 0.0) {
            double ratio = (potential_commit / 0.70) / break_even;
            /* ALG-12 OM_BUDGET_PRESSURE_THRESHOLD */
            if (ratio > OM_BUDGET_PRESSURE_THRESHOLD) effective_confidence *= OM_BUDGET_PRESSURE_THRESHOLD / ratio;
        }

        // Archetype weights
        double w_attack = 0.8, w_expand = 0.6;
        switch (w->faction_archetype[f]) {
            case OM_ARCH_CONQUEROR: w_attack = 1.2; w_expand = 1.0; break;
            case OM_ARCH_WARLORD:   w_attack = 1.4; w_expand = 0.6; break;
            case OM_ARCH_FORTIFIER: w_attack = 0.8; w_expand = 0.8; break;
            case OM_ARCH_OPPORTUNIST: w_attack = 1.0; w_expand = 0.7; break;
            case OM_ARCH_SCHISM:   w_attack = 1.3; w_expand = 0.0; break;
            case OM_ARCH_PLAYER:   w_attack = 0.3; w_expand = 0.5; break;
            default:               w_attack = 0.8; w_expand = 0.6; break;
        }

        double attack_score = 0.0;
        if (best_attack) {
            attack_score = clamp(best_attack->net / 40.0, 0.0, 1.0) * w_attack;
        }
        double colonize_score = 0.0;
        if (best_colonize) {
            colonize_score = clamp(best_colonize->attractiveness, 0.0, 1.0) * w_expand;
        }

        om_decision d = {0};
        d.tick = w->tick;
        d.faction_id = f;
        d.attack_score = attack_score;
        d.colonize_score = colonize_score;
        d.effective_confidence = effective_confidence;
        d.break_even = break_even;
        d.target_idx = UINT32_MAX;
        d.source_idx = UINT32_MAX;
        d.mode = 0;
        d.telegraph_preference = 0.0;

        if (attack_score >= colonize_score && attack_score >= 0.05 && best_attack) {
            d.action = OM_ACT_ATTACK;
            d.target_idx = best_attack->region_idx;
            d.commit = potential_commit;
            // find owned region with highest military
            double max_mil = -1.0;
            uint32_t src = UINT32_MAX;
            for (uint32_t i = 0; i < w->n_regions; ++i) {
                if (w->regions[i].faction_id == f) {
                    if (w->regions[i].military > max_mil) {
                        max_mil = w->regions[i].military;
                        src = i;
                    }
                }
            }
            d.source_idx = src;

            // ALG-15 telegraph preference calculation
            double pref = 0.0;
            switch (w->faction_archetype[f]) {
                case OM_ARCH_CONQUEROR: pref = 0.70; break;
                case OM_ARCH_WARLORD:   pref = 0.30; break;
                case OM_ARCH_FORTIFIER: pref = 0.80; break;
                case OM_ARCH_OPPORTUNIST: pref = 0.40; break;
                case OM_ARCH_SCHISM:    pref = 0.30; break;
                case OM_ARCH_PLAYER:    pref = 0.60; break;
                default:                pref = 0.50; break;
            }

            double target_military = w->regions[best_attack->region_idx].military;
            if (target_military > 60.0) {
                pref += 0.20;
            } else if (target_military < 30.0) {
                pref -= 0.20;
            }

            pref = clamp(pref, 0.0, 1.0);
            d.telegraph_preference = pref;

            double u = om_rng_draw(w);

            om_attack_mode mode = OM_MODE_SURPRISE;
            if (u < pref) {
                mode = OM_MODE_TELEGRAPH;
                // Enqueue into telegraphs if space available
                if (w->telegraphs_n < OM_MAX_REGIONS) {
                    w->telegraphs[w->telegraphs_n].declared_tick = w->tick;
                    w->telegraphs[w->telegraphs_n].attacker = f;
                    w->telegraphs[w->telegraphs_n].target_idx = best_attack->region_idx;
                    w->telegraphs[w->telegraphs_n].source_idx = src;
                    w->telegraphs[w->telegraphs_n].commit = potential_commit;
                    w->telegraphs_n++;
                }
            }

            d.mode = mode;
        } else if (colonize_score > attack_score && colonize_score >= 0.05 &&
                   best_colonize && w->faction_budget_snapshot[f] >= 20.0) {
            d.action = OM_ACT_COLONIZE;
            d.target_idx = best_colonize->region_idx;
            d.commit = 20.0;
            // find owned region with edge to target
            uint32_t src = UINT32_MAX;
            for (uint32_t i = 0; i < w->n_regions; ++i) {
                if (w->regions[i].faction_id == f) {
                    om_edge_type t;
                    if (om_region_edge(w, i, best_colonize->region_idx, &t)) {
                        src = i;
                        break;
                    }
                }
            }
            d.source_idx = src;
        } else {
            d.action = OM_ACT_ACCUMULATE;
            d.commit = 0.0;
        }

        w->decisions[w->decisions_n++] = d;
        
        // Deduct commit from faction budget
        if (d.action == OM_ACT_ATTACK || d.action == OM_ACT_COLONIZE) {
            w->faction_budget[f] -= d.commit;
            if (w->faction_budget[f] < 0.0) {
                w->faction_budget[f] = 0.0;
            }
        }
    }
}
