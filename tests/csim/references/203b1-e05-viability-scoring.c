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
#include <stddef.h>
#include <string.h>

static void om_faction_arch_weights(om_archetype a, double *weakness, double *value, double *position,
                                    int *tension_primary, int *can_colonize, double *boost) {
    switch (a) {
        case OM_ARCH_CONQUEROR:   *weakness = 0.40; *value = 0.25; *position = 0.35; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_FORTIFIER:   *weakness = 0.25; *value = 0.20; *position = 0.55; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_OPPORTUNIST: *weakness = 0.35; *value = 0.30; *position = 0.35; *tension_primary = 0; *can_colonize = 1; *boost = 1.5; break;
        case OM_ARCH_WARLORD:     *weakness = 0.20; *value = 0.35; *position = 0.45; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_SCHISM:      *weakness = 0.20; *value = 0.30; *position = 0.50; *tension_primary = 1; *can_colonize = 0; *boost = 0.0; break;
        case OM_ARCH_PLAYER:      *weakness = 0.60; *value = 0.25; *position = 0.15; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        case OM_ARCH_BREAKAWAY:   *weakness = 0.45; *value = 0.30; *position = 0.25; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
        default:                 *weakness = 0.40; *value = 0.30; *position = 0.30; *tension_primary = 0; *can_colonize = 1; *boost = 0.0; break;
    }
}

static double om_current_value(const om_region *r) {
    return ((r->economy * 0.60 + r->population * 0.40) / 100.0) * 2.0;
}

static double om_strategic_position(const om_world *w, uint32_t target_idx, int32_t faction_id) {
    double sum = 0.0;
    uint32_t n = 0;
    for (uint32_t k = 0; k < w->n_regions; k++) {
        if (k == target_idx)
            continue;
        om_edge_type et;
        if (!om_region_edge(w, target_idx, k, &et))
            continue;
        if (w->regions[k].faction_id == faction_id)
            continue;
        if (w->regions[k].faction_id < 0) {
            sum += 0.15; /* EXPANSION_POTENTIAL */
        } else {
            sum += (w->regions[k].economy * 0.60 + w->regions[k].population * 0.40) / 100.0;
        }
        n++;
    }
    return n > 0 ? sum / (double)n : 0.0;
}

/* ALG-12/13: entrenchment + net + viability for every attack candidate in
 * cands[0..n). Mutates cands[i].entrenchment/net/viable in place. */
static void om_faction_evaluate_attacks(const om_world *w, uint64_t tick, om_candidate *cands, uint32_t n,
                                        double potential_commit, double confidence,
                                        double *out_break_even, double *out_eff_conf) {
    double weakest = -1.0;
    for (uint32_t i = 0; i < n; i++) {
        if (cands[i].kind != OM_CAND_ATTACK)
            continue;
        const om_region *tgt = &w->regions[cands[i].region_idx];
        int64_t held_since = om_region_held_since(w, cands[i].region_idx);
        double entrenchment;
        if (held_since < 0) {
            entrenchment = 2.0;
        } else {
            double ratio = (double)((int64_t)tick - held_since) / 100.0;
            if (ratio < 0.0) ratio = 0.0;
            if (ratio > 1.0) ratio = 1.0;
            entrenchment = 1.0 + ratio;
        }
        cands[i].entrenchment = entrenchment;
        cands[i].net = potential_commit - tgt->military * 0.55 * entrenchment;
        if (weakest < 0.0 || tgt->military < weakest)
            weakest = tgt->military;
    }

    double break_even = (weakest >= 0.0) ? (weakest * 0.55 / 0.70) : 0.0;
    double eff_conf = confidence;
    if (break_even > 0.0) {
        double budget = potential_commit / 0.70;
        double ratio = budget / break_even;
        if (ratio > 0.8)
            eff_conf = confidence * (0.8 / ratio);
    }
    for (uint32_t i = 0; i < n; i++) {
        if (cands[i].kind != OM_CAND_ATTACK)
            continue;
        cands[i].viable = (cands[i].net > eff_conf) ? 1u : 0u;
    }
    if (out_break_even) *out_break_even = break_even;
    if (out_eff_conf) *out_eff_conf = eff_conf;
}

uint32_t om_faction_candidates(const om_world *w, int32_t faction_id, om_candidate *out, uint32_t max) {
    if (!w || faction_id < 0 || faction_id >= OM_MAX_FACTIONS || !w->faction_used[faction_id])
        return 0;

    double aw_weakness, aw_value, aw_position, aw_boost;
    int aw_tension_primary, aw_can_colonize;
    om_faction_arch_weights(w->faction_archetype[faction_id], &aw_weakness, &aw_value, &aw_position,
                            &aw_tension_primary, &aw_can_colonize, &aw_boost);

    uint32_t count = 0;
    unsigned char seen[64];
    memset(seen, 0, sizeof(seen));

    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id != faction_id)
            continue;

        for (uint32_t j = 0; j < w->n_regions; j++) {
            if (j == i)
                continue;
            om_edge_type et;
            if (!om_region_edge(w, i, j, &et))
                continue;
            if (w->regions[j].faction_id == faction_id)
                continue;
            if (j < 64 && seen[j])
                continue;

            int32_t owner = w->regions[j].faction_id;
            uint32_t kind;
            if (owner < 0) {
                if (!aw_can_colonize)
                    continue; /* schism never colonizes (ALG-11) */
                kind = OM_CAND_COLONIZE;
            } else {
                om_stance s_out = w->faction_stance[faction_id][owner];
                om_stance s_in = w->faction_stance[owner][faction_id];
                if (s_out != OM_STANCE_HOSTILE && s_in != OM_STANCE_HOSTILE)
                    continue; /* R-034-06 */
                kind = OM_CAND_ATTACK;
            }

            const om_region *tgt = &w->regions[j];
            double value = (owner < 0) ? 0.0 : om_current_value(tgt);
            if (kind == OM_CAND_ATTACK && value < 0.05)
                continue; /* MIN_ATTACK_VALUE, R-034-04 */

            if (j < 64)
                seen[j] = 1;
            if (count >= max)
                continue;

            double factor1 = aw_tension_primary ? (tgt->tension / 100.0) : (1.0 - tgt->military / 100.0);
            double position = om_strategic_position(w, j, faction_id);
            double attractiveness = aw_weakness * factor1 + aw_value * value + aw_position * position;
            if (aw_boost > 0.0) {
                double dmg = om_region_damage_history(w, j);
                attractiveness *= 1.0 + (dmg / 100.0) * aw_boost;
            }

            out[count].region_idx = j;
            out[count].kind = kind;
            out[count].weakness = factor1;
            out[count].value = value;
            out[count].position = position;
            out[count].attractiveness = attractiveness;
            out[count].entrenchment = 0.0;
            out[count].net = 0.0;
            out[count].viable = 0;
            out[count]._pad = 0;
            count++;
        }
    }

    double snapshot_budget = w->faction_budget_snapshot[faction_id];
    double potential_commit = snapshot_budget * 0.70;
    om_faction_evaluate_attacks(w, w->tick, out, count, potential_commit, w->faction_confidence[faction_id], NULL, NULL);

    return count;
}

/* ALG-14: builds this tick's decisions into w->decisions (mode/telegraph
 * queueing is card 203b2's addition). Mutating; called once per real tick
 * from sim.c step 3d. om_tick_decisions below is a plain reader over the
 * cache this fills. */
void om_step_decisions(om_world *w) {
    if (!w)
        return;

    w->decisions_n = 0;
    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (!w->faction_used[f])
            continue;
        if (w->decisions_n >= 64)
            break;

        om_candidate cands[256];
        uint32_t n = om_faction_candidates(w, f, cands, 256);

        double snapshot_budget = w->faction_budget_snapshot[f];
        double potential_commit = snapshot_budget * 0.70;
        double break_even = 0.0, eff_conf = w->faction_confidence[f];
        om_faction_evaluate_attacks(w, w->tick, cands, n, potential_commit, w->faction_confidence[f], &break_even, &eff_conf);

        int32_t best_attack_idx = -1;
        for (uint32_t i = 0; i < n; i++) {
            if (cands[i].kind != OM_CAND_ATTACK || !cands[i].viable)
                continue;
            if (best_attack_idx < 0 || cands[i].attractiveness > cands[(uint32_t)best_attack_idx].attractiveness)
                best_attack_idx = (int32_t)i;
        }
        int32_t best_col_idx = -1;
        for (uint32_t i = 0; i < n; i++) {
            if (cands[i].kind != OM_CAND_COLONIZE)
                continue;
            if (best_col_idx < 0 || cands[i].attractiveness > cands[(uint32_t)best_col_idx].attractiveness)
                best_col_idx = (int32_t)i;
        }

        double w_attack, w_expand;
        switch (w->faction_archetype[f]) {
            case OM_ARCH_CONQUEROR:   w_attack = 1.2; w_expand = 1.0; break;
            case OM_ARCH_WARLORD:     w_attack = 1.4; w_expand = 0.6; break;
            case OM_ARCH_FORTIFIER:   w_attack = 0.8; w_expand = 0.8; break;
            case OM_ARCH_OPPORTUNIST: w_attack = 1.0; w_expand = 0.7; break;
            case OM_ARCH_SCHISM:      w_attack = 1.3; w_expand = 0.0; break;
            case OM_ARCH_PLAYER:      w_attack = 0.3; w_expand = 0.5; break;
            default:                  w_attack = 0.8; w_expand = 0.6; break;
        }

        double best_net = (best_attack_idx >= 0) ? cands[(uint32_t)best_attack_idx].net : 0.0;
        double attack_norm = best_net / 40.0;
        if (attack_norm < 0.0) attack_norm = 0.0;
        if (attack_norm > 1.0) attack_norm = 1.0;
        double attack_score = (best_attack_idx >= 0) ? attack_norm * w_attack : 0.0;

        double best_attract = (best_col_idx >= 0) ? cands[(uint32_t)best_col_idx].attractiveness : 0.0;
        double col_norm = best_attract;
        if (col_norm < 0.0) col_norm = 0.0;
        if (col_norm > 1.0) col_norm = 1.0;
        double colonize_score = (best_col_idx >= 0) ? col_norm * w_expand : 0.0;

        om_decision d;
        memset(&d, 0, sizeof(d));
        d.tick = w->tick;
        d.faction_id = f;
        d.target_idx = UINT32_MAX;
        d.source_idx = UINT32_MAX;
        d.attack_score = attack_score;
        d.colonize_score = colonize_score;
        d.effective_confidence = eff_conf;
        d.break_even = break_even;

        if (attack_score >= colonize_score && attack_score >= 0.05 && best_attack_idx >= 0) {
            d.action = OM_ACT_ATTACK;
            d.target_idx = cands[(uint32_t)best_attack_idx].region_idx;
            d.commit = potential_commit;
            int32_t src = -1;
            double src_mil = -1.0;
            for (uint32_t i = 0; i < w->n_regions; i++) {
                if (w->regions[i].faction_id == f && w->regions[i].military > src_mil) {
                    src_mil = w->regions[i].military;
                    src = (int32_t)i;
                }
            }
            d.source_idx = (src >= 0) ? (uint32_t)src : UINT32_MAX;
        } else if (colonize_score > attack_score && colonize_score >= 0.05 && best_col_idx >= 0 && snapshot_budget >= 20.0) {
            d.action = OM_ACT_COLONIZE;
            d.target_idx = cands[(uint32_t)best_col_idx].region_idx;
            d.commit = 20.0;
            uint32_t tgt = d.target_idx;
            int32_t src = -1;
            for (uint32_t i = 0; i < w->n_regions; i++) {
                om_edge_type et;
                if (w->regions[i].faction_id == f && om_region_edge(w, i, tgt, &et)) {
                    src = (int32_t)i;
                    break;
                }
            }
            d.source_idx = (src >= 0) ? (uint32_t)src : UINT32_MAX;
        } else {
            d.action = OM_ACT_ACCUMULATE;
            d.commit = 0.0;
        }

        w->decisions[w->decisions_n++] = d;
    }
}

uint32_t om_tick_decisions(const om_world *w, om_decision *out, uint32_t max) {
    if (!w || !out)
        return 0;
    uint32_t n = w->decisions_n < max ? w->decisions_n : max;
    memcpy(out, w->decisions, n * sizeof(om_decision));
    return n;
}

uint32_t om_pending_telegraphs(const om_world *w, om_telegraph *out, uint32_t max) {
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}
