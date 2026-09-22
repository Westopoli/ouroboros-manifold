/* csrc/collision.c — E-05 multi-faction collision (build card 205).
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

/* Same forced-draw-first, PCG-style RNG draw csrc/faction.c and csrc/agent.c
 * already use; returns U(0, 1). */
static double om_collision_draw(om_world *w) {
    if (w->rng_forced_len > 0) {
        double u = w->rng_forced[w->rng_forced_head];
        w->rng_forced_head++;
        w->rng_forced_len--;
        return u;
    }
    uint32_t next32 = (uint32_t)((w->rng_state >> 12) + w->rng_inc);
    w->rng_state = next32 * 6364136223846793005ULL + w->rng_inc;
    uint32_t a = next32 >> 5;
    next32 = (uint32_t)((w->rng_state >> 12) + w->rng_inc);
    w->rng_state = next32 * 6364136223846793005ULL + w->rng_inc;
    uint32_t b = next32 >> 6;
    return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
}

static double om_collision_faction_economy(const om_world *w, int32_t faction_id) {
    double sum = 0.0;
    for (uint32_t i = 0; i < w->n_regions; ++i) {
        if (w->regions[i].faction_id == faction_id) sum += w->regions[i].economy;
    }
    return sum;
}

static uint32_t om_collision_highest_military_region(const om_world *w, int32_t faction_id) {
    uint32_t best = UINT32_MAX;
    double best_mil = -1.0;
    for (uint32_t i = 0; i < w->n_regions; ++i) {
        if (w->regions[i].faction_id == faction_id && w->regions[i].military > best_mil) {
            best_mil = w->regions[i].military;
            best = i;
        }
    }
    return best;
}

/* Resolves one target's colliding group (ALG-23/24). members[] holds indices
 * into w->decisions[]; the caller marks them consumed and compacts. */
static void om_collision_resolve_group(om_world *w, const uint32_t *members, uint32_t n_members) {
    /* NEEDS-HEADER item 1 (leaf-01 escalation, docs at
     * .swarm/b2-collision/questions/leaf-01-Q1.md): ALG-23's per-collision
     * loser tension base and the narrow-margin colonize draw's upper bound
     * have no named constant in om_constants.h yet. Local placeholders,
     * awaiting promotion. */
    static const double LOSER_TENSION_BASE = 5.0;
    static const double NARROW_MIL_UPPER = 0.70;

    om_decision *ds[OM_MAX_COLLIDERS];
    for (uint32_t i = 0; i < n_members; ++i) ds[i] = &w->decisions[members[i]];
    uint32_t target_idx = ds[0]->target_idx;

    double factor[OM_MAX_COLLIDERS];
    double strength[OM_MAX_COLLIDERS];
    double max_eco = 0.0;
    double eco[OM_MAX_COLLIDERS];
    for (uint32_t i = 0; i < n_members; ++i) {
        eco[i] = om_collision_faction_economy(w, ds[i]->faction_id);
        if (eco[i] > max_eco) max_eco = eco[i];
    }
    if (max_eco <= 0.0) max_eco = 1.0;

    double total_strength = 0.0;
    for (uint32_t i = 0; i < n_members; ++i) {
        factor[i] = OM_COLLISION_ECONOMY_FLOOR +
                    (OM_COLLISION_ECONOMY_CEILING - OM_COLLISION_ECONOMY_FLOOR) * eco[i] / max_eco;
        int32_t f = ds[i]->faction_id;
        double surprise_i = (ds[i]->action == OM_ACT_ATTACK && ds[i]->mode == OM_MODE_SURPRISE) ? 0.5 : 1.0;
        strength[i] = ds[i]->commit * OM_ATTACK_EFFICIENCY * factor[i] * w->faction_tech_attack[f] * surprise_i;
        total_strength += strength[i];
    }

    double u_winner = om_collision_draw(w);
    uint32_t winner = n_members - 1;
#ifdef OM_DEBUG_INJECT
    if (w->inject == OM_BUG_COLLISION_MAX_STRENGTH) {
        double best = -1.0;
        for (uint32_t i = 0; i < n_members; ++i) {
            if (strength[i] > best) { best = strength[i]; winner = i; }
        }
    } else
#endif
    if (total_strength <= 0.0) {
        double cum = 0.0, step = 1.0 / (double)n_members;
        for (uint32_t i = 0; i < n_members; ++i) {
            cum += step;
            if (u_winner < cum) { winner = i; break; }
        }
    } else {
        double cum = 0.0;
        for (uint32_t i = 0; i < n_members; ++i) {
            cum += strength[i];
            if (u_winner < cum / total_strength) { winner = i; break; }
        }
    }

    double second = 0.0, loser_sum = 0.0;
    for (uint32_t i = 0; i < n_members; ++i) {
        if (i == winner) continue;
        if (strength[i] > second) second = strength[i];
        loser_sum += strength[i];
    }
    double winner_strength = strength[winner];
    double margin = (winner_strength + second > 0.0) ? winner_strength / (winner_strength + second) : 1.0;
    double opp = (winner_strength > 0.0) ? loser_sum / winner_strength : 0.0;
    double opp_term = 1.0 - opp * OM_COLLISION_RETENTION_OPPOSITION_SCALE;
    if (opp_term < 0.0) opp_term = 0.0;
    double ret_ceiling = OM_COLLISION_RETENTION_MAX * opp_term;

    double u_refund = om_collision_draw(w);
    double refund = ds[winner]->commit * u_refund * ret_ceiling;

    om_collision c;
    memset(&c, 0, sizeof(c));
    c.tick = w->tick;
    c.target_idx = target_idx;
    c.n_colliders = n_members;
    c.winner = ds[winner]->faction_id;
    c.margin = margin;
    c.retention_ceiling = ret_ceiling;
    c.refund = refund;

    for (uint32_t i = 0; i < n_members; ++i) {
        int32_t f = ds[i]->faction_id;
        c.faction[i] = f;
        c.commit[i] = ds[i]->commit;
        c.economy_factor[i] = factor[i];
        c.strength[i] = strength[i];

        /* Commits were reserved against the 3a pre-tick budget snapshot
         * (agent.c computes potential_commit off faction_budget_snapshot,
         * not the live, already-grown budget); spend and the tension
         * formula's denominator both read that same reserved baseline. */
        double budget_at_commit_time = w->faction_budget_snapshot[f];
        if (i == winner) {
            w->faction_budget[f] = budget_at_commit_time - (ds[i]->commit - refund);
            c.loser_tension[i] = 0.0;
        } else {
            double tension_delta = LOSER_TENSION_BASE * ds[i]->commit / budget_at_commit_time;
            w->faction_budget[f] = budget_at_commit_time - ds[i]->commit;
            c.loser_tension[i] = tension_delta;
            uint32_t hit_idx = om_collision_highest_military_region(w, f);
            if (hit_idx != UINT32_MAX) w->regions[hit_idx].tension += tension_delta;
        }
    }

    if (w->collisions_n < 64) w->collisions[w->collisions_n++] = c;

    if (w->regions[target_idx].faction_id < 0) {
        int32_t winner_faction = ds[winner]->faction_id;
        double start_military = OM_COLONY_START_MILITARY;
        if (margin < OM_COLLISION_NARROW_MARGIN) {
            double u_pen = om_collision_draw(w);
            double frac = OM_COLLISION_NARROW_MIL_PENALTY + (NARROW_MIL_UPPER - OM_COLLISION_NARROW_MIL_PENALTY) * u_pen;
            start_military = OM_COLONY_START_MILITARY * frac;
        }

        om_region_set_owner(w, target_idx, winner_faction, (int64_t)w->tick);
        w->regions[target_idx].tier = OM_TIER_FRONTIER;
        w->regions[target_idx].military = start_military;
        w->regions[target_idx].economy = OM_COLONY_START_ECONOMY;
        w->regions[target_idx].tension = OM_COLONY_START_TENSION;
        w->regions[target_idx].population = OM_COLONY_START_POPULATION;

        if (w->colonizations_n < 64) {
            om_colonize_result *cr = &w->colonizations[w->colonizations_n++];
            cr->tick = w->tick;
            cr->faction_id = winner_faction;
            cr->target_idx = target_idx;
            cr->start_military = start_military;
            cr->budget_spent = ds[winner]->commit - refund;
        }
    }
}

void om_step_collisions(om_world *w) {
    if (!w) return;

    int used[64];
    memset(used, 0, sizeof(used));

    for (uint32_t i = 0; i < w->decisions_n; ++i) {
        if (used[i]) continue;
        om_decision *d = &w->decisions[i];
        if (d->action != OM_ACT_ATTACK && d->action != OM_ACT_COLONIZE) continue;
        if (d->target_idx == UINT32_MAX) continue;

        uint32_t members[OM_MAX_COLLIDERS];
        uint32_t n_members = 0;
        for (uint32_t j = i; j < w->decisions_n && n_members < OM_MAX_COLLIDERS; ++j) {
            if (used[j]) continue;
            om_decision *dj = &w->decisions[j];
            if (dj->action != OM_ACT_ATTACK && dj->action != OM_ACT_COLONIZE) continue;
            if (dj->target_idx != d->target_idx) continue;
            members[n_members++] = j;
        }
        if (n_members < 2) continue;
        /* ALG-23: an owned target (by a collider or anyone else) takes the
         * damage-application branch, R-039-05, out of scope (Q-039-01) --
         * leave those decisions for om_step_resolve rather than half-apply
         * collision math this piece doesn't implement. */
        if (w->regions[d->target_idx].faction_id >= 0) continue;

        om_collision_resolve_group(w, members, n_members);
        for (uint32_t k = 0; k < n_members; ++k) used[members[k]] = 1;
    }

    uint32_t out_n = 0;
    for (uint32_t i = 0; i < w->decisions_n; ++i) {
        if (!used[i]) w->decisions[out_n++] = w->decisions[i];
    }
    w->decisions_n = out_n;
}

uint32_t om_tick_collisions(const om_world *w, om_collision *out, uint32_t max) {
    if (!w || !out || max == 0) return 0;

    uint32_t count = w->collisions_n < max ? w->collisions_n : max;
    for (uint32_t i = 0; i < count; ++i) {
        out[i] = w->collisions[i];
    }
    return count;
}
