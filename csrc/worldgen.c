/* csrc/worldgen.c -- E-03 world generation and topology (build card B4).
 * docs/bible/epics/E-03-world-generation.md, docs/northstar/e2e/E-03.md,
 * docs/bible/algorithms.md ALG-30 (starting fields) and ALG-31 (topology).
 * Provides the strong om_world_generate() that overrides the weak stub in
 * csrc/region.c, plus every E-03 config setter and report accessor declared
 * in csrc/ouroboros_sim.h's E-03 block. Every stochastic draw goes through
 * om_rng_draw (csrc/om_internal.h) in the order the e2e file's "RNG draw
 * order" paragraph pins. */
/* PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).
 * Use exactly these member names; there are no others.
 * #define OM_MAX_NEIGHBORS 32
 * #define OM_DAMAGE_HISTORY_CAP 64
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
 *     uint64_t damage_tick[OM_DAMAGE_HISTORY_CAP];
 *     double   damage_military[OM_DAMAGE_HISTORY_CAP];
 *     double   damage_economy[OM_DAMAGE_HISTORY_CAP];
 *     uint32_t damage_head, damage_len;
 * } om_region;
 *
 * struct om_world { ... gen_region_min, gen_region_max, gen_faction_count,
 *     gen_extra_edge_ratio, gen_player_pref, gen_preference_weight,
 *     gen_extra_edges_on, gen_home_range[3][4], faction_template[OM_MAX_FACTIONS],
 *     generated, edge_count ... (full layout: csrc/om_internal.h) };
 */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include "om_constants.h"
#include <stddef.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

/* OM_GEN_TWO_PI promoted to csrc/om_constants.h as OM_TWO_PI (CONST-1). */
/* ALG-30's field clamp target; no named IDENT in the doc's own prose.
 * OM_GEN_FIELD_MAX 100.0 kept local: header has OM_FIELD_MAX 100 (int),
 * different type; not provably equivalent in all double contexts (CONST-1). */
#define OM_GEN_FIELD_MIN 0.0
#define OM_GEN_FIELD_MAX 100.0

/* gen_home_range[archetype][slot] slot indices (ouroboros_sim.h ~line 694:
 * "[mil_lo, mil_hi, eco_lo, eco_hi]"). */
#define OM_GEN_HR_MIL_LO 0
#define OM_GEN_HR_MIL_HI 1
#define OM_GEN_HR_ECO_LO 2
#define OM_GEN_HR_ECO_HI 3

/* ======================================================================
 * Both original blockers (om_world_new rejecting n_regions == 0; the
 * region_edge[64][64] cap below E-03's 110-region range) are fixed on
 * main as of freeze/F2d (fd01efd): om_world_new(0, seed) now defers the
 * count exactly as this file expects, and OM_MAX_REGIONS is 128 everywhere
 * region-indexed. Nothing left to report there.
 * ====================================================================== */

static double gen_uniform(om_world *w, double lo, double hi) {
    double u = om_rng_draw(w);
    return lo + (hi - lo) * u;
}

static uint32_t gen_randint(om_world *w, uint32_t lo, uint32_t hi) {
    double u = om_rng_draw(w);
    uint32_t n = hi - lo + 1;
    uint32_t off = (uint32_t)floor(u * (double)n);
    if (off >= n)
        off = n - 1;
    return lo + off;
}

static double gen_clamp(double v) {
    return fmax(OM_GEN_FIELD_MIN, fmin(OM_GEN_FIELD_MAX, v));
}

static om_template gen_roll_template(om_world *w, uint32_t fid, om_template pref, double pref_weight) {
    double u = om_rng_draw(w);
    double wt[3];
    if (fid == 0 && pref != OM_TMPL_NONE) {
        double remainder_each = (1.0 - pref_weight) / 2.0;
        wt[OM_TMPL_ISOLATED] = remainder_each;
        wt[OM_TMPL_TWIN_COLONY] = remainder_each;
        wt[OM_TMPL_ARCHIPELAGO] = remainder_each;
        wt[pref] = pref_weight;
    } else {
        double equal = 1.0 / (double)OM_TMPL_NONE;
        wt[OM_TMPL_ISOLATED] = equal;
        wt[OM_TMPL_TWIN_COLONY] = equal;
        wt[OM_TMPL_ARCHIPELAGO] = equal;
    }
    double c0 = wt[OM_TMPL_ISOLATED];
    double c1 = c0 + wt[OM_TMPL_TWIN_COLONY];
    if (u < c0)
        return OM_TMPL_ISOLATED;
    if (u < c1)
        return OM_TMPL_TWIN_COLONY;
    return OM_TMPL_ARCHIPELAGO;
}

/* The feasibility gate (ALG-31 step 3, "no draw") runs before a Twin
 * Colony's per-home frontier counts are rolled (step 4), so it reserves
 * each faction's smallest possible size, never the roll it hasn't taken
 * yet -- reserving the largest possible size instead fails generation far
 * more often than the roll actually requires. Placement then spends the
 * region count's slack over that minimum (gen_twin_slack in
 * om_world_generate) so a later faction's roll can never overrun the
 * already-fixed budget. */
static uint32_t gen_template_min_size(om_template t) {
    switch (t) {
        case OM_TMPL_ISOLATED:
            return 1 + OM_ISOLATED_FRONTIER_COUNT;
        case OM_TMPL_TWIN_COLONY:
            return OM_TWIN_COLONY_HOME_COUNT * (1 + OM_TWIN_COLONY_FRONTIER_RANGE_LO);
        case OM_TMPL_ARCHIPELAGO:
        default:
            return 1 + OM_ARCHIPELAGO_FRONTIER_COUNT;
    }
}

/* Edge type is fixed for the whole of generation once ownership is placed
 * (ALG-31: "no draw" at the typing step): both endpoints owned by the same
 * real faction is `both`, everything else (including two empties, or one
 * empty) is `border` (R-023-01). */
static void gen_add_edge(om_world *w, uint32_t a, uint32_t b) {
    if (a == b)
        return;
    om_edge_type existing;
    if (om_region_edge(w, a, b, &existing))
        return;
    int32_t oa = w->regions[a].faction_id;
    int32_t ob = w->regions[b].faction_id;
    om_edge_type t = (oa >= 0 && oa == ob) ? OM_EDGE_BOTH : OM_EDGE_BORDER;
    om_region_set_edge(w, a, b, t);
    w->edge_count++;
}

static void gen_place_region(om_world *w, uint32_t idx, om_tier tier, int32_t fid, om_archetype arch,
                              double *pop_sum, uint32_t *pop_count) {
    double pop = (tier == OM_TIER_HOME)
        ? gen_uniform(w, OM_HOME_POPULATION_RANGE_LO, OM_HOME_POPULATION_RANGE_HI)
        : gen_uniform(w, OM_FRONTIER_POPULATION_RANGE_LO, OM_FRONTIER_POPULATION_RANGE_HI);

    int use_home_range = (tier == OM_TIER_HOME) &&
        (arch == OM_ARCH_CONQUEROR || arch == OM_ARCH_FORTIFIER || arch == OM_ARCH_OPPORTUNIST);

    double econ_val, mil_val;
    if (use_home_range) {
        const double *hr = w->gen_home_range[arch - OM_ARCH_CONQUEROR];
        econ_val = gen_uniform(w, hr[OM_GEN_HR_ECO_LO], hr[OM_GEN_HR_ECO_HI]); /* economy slot */
        mil_val  = gen_uniform(w, hr[OM_GEN_HR_MIL_LO], hr[OM_GEN_HR_MIL_HI]); /* military slot */
    } else {
        double j1 = gen_uniform(w, -OM_STARTING_FIELD_JITTER, OM_STARTING_FIELD_JITTER);
        econ_val = gen_clamp(pop * OM_STARTING_ECO_RATIO + j1);
        double j2 = gen_uniform(w, -OM_STARTING_FIELD_JITTER, OM_STARTING_FIELD_JITTER);
        mil_val = gen_clamp(pop * OM_STARTING_MIL_RATIO + j2);
    }
    double j3 = gen_uniform(w, -OM_STARTING_FIELD_JITTER, OM_STARTING_FIELD_JITTER);
    double tension_val = gen_clamp(pop * OM_STARTING_TENSION_RATIO + j3);
    double econ_phase = gen_uniform(w, OM_GEN_FIELD_MIN, OM_TWO_PI);
    double tension_phase = gen_uniform(w, OM_GEN_FIELD_MIN, OM_TWO_PI);

    om_region_set(w, idx, tier, mil_val, econ_val, tension_val, pop, econ_phase, tension_phase, fid);
    om_region_set_owner(w, idx, fid, -1);

    *pop_sum += pop;
    (*pop_count)++;
}

void om_world_generate(om_world *w) {
    if (w == NULL)
        return;
    w->generated = 0;
    w->edge_count = 0;

    if (w->gen_faction_count < 2 || w->gen_faction_count > OM_MAX_FACTIONS)
        return;
    if (w->gen_extra_edge_ratio < 0.0)
        return;
    if (w->gen_player_pref != OM_TMPL_ISOLATED && w->gen_player_pref != OM_TMPL_TWIN_COLONY &&
        w->gen_player_pref != OM_TMPL_ARCHIPELAGO && w->gen_player_pref != OM_TMPL_NONE)
        return;

    uint32_t n_factions = w->gen_faction_count;

    /* (1) region count -- one draw, only when not pinned by om_world_new. */
    uint32_t n_regions = (w->n_regions > 0)
        ? w->n_regions
        : gen_randint(w, w->gen_region_min, w->gen_region_max);

    /* (2) template rolls, batched, before any placement. */
    om_template templates[OM_MAX_FACTIONS];
    for (uint32_t fid = 0; fid < n_factions; fid++)
        templates[fid] = gen_roll_template(w, fid, w->gen_player_pref, w->gen_preference_weight);

    /* (3) feasibility -- no draw. The epic's own Input table gives this as
     * "count < sum of every rolled faction's template size + 1 fails"; the
     * corridor step (R-021-06) needs one further distinct empty per faction
     * on top of that sum, so the "+1" here is n_factions worth of corridor
     * room, the loosest amount the corridor step can safely run on. Twin
     * Colony's per-home frontier counts are not rolled yet, so this reserves
     * each faction's minimum possible size, never the roll it hasn't taken
     * -- reserving the max instead fails generation far more often than the
     * roll actually needs. gen_twin_slack is the room left above that
     * minimum; placement spends it on a Twin Colony's actual frontier draw
     * so a later roll can never overrun the already-fixed budget. */
    uint32_t min_inhabited = 0;
    for (uint32_t fid = 0; fid < n_factions; fid++)
        min_inhabited += gen_template_min_size(templates[fid]);
    uint32_t needed_with_corridors = min_inhabited + n_factions;
    if (n_regions < needed_with_corridors) {
        /* Q-021-07: a DRAWN count below the feasible minimum is lifted to
         * it, with no extra draw, so every seed generates; a PINNED count
         * (om_world_new(n, seed), n > 0) below the minimum still fails
         * cleanly, keeping the tested "count too small" boundary cases. */
        if (w->n_regions > 0)
            return;
        n_regions = needed_with_corridors;
    }
    uint32_t gen_twin_slack = n_regions - needed_with_corridors;

    if (w->n_regions == 0) {
        om_region *regions = calloc(n_regions, sizeof(om_region));
        if (!regions)
            return;
        for (uint32_t i = 0; i < n_regions; i++)
            regions[i].faction_id = -1;
        w->regions = regions;
        w->n_regions = n_regions;
    }

    /* Faction setup: archetype (R-021-02), template, and the same bookkeeping
     * om_faction_set performs -- but without its RNG-consuming confidence
     * roll, which is not part of the E-03 draw order (R-022-04). */
    static const om_archetype ARCH_CYCLE[] = { OM_ARCH_CONQUEROR, OM_ARCH_FORTIFIER, OM_ARCH_OPPORTUNIST };
    for (uint32_t fid = 0; fid < n_factions; fid++) {
        om_archetype arch = (fid == 0)
            ? OM_ARCH_PLAYER
            : ARCH_CYCLE[(fid - 1) % (sizeof(ARCH_CYCLE) / sizeof(ARCH_CYCLE[0]))];
        w->faction_archetype[fid] = arch;
        w->faction_budget[fid] = 0.0;
        w->faction_tech[fid] = 0.0;
        w->faction_confidence[fid] = 0.0;
        if (w->faction_used[fid] == 0) {
            w->faction_used[fid] = 1;
            w->faction_n++;
        }
        for (uint32_t j = 0; j < OM_MAX_FACTIONS; j++)
            w->faction_stance[fid][j] = (j == fid) ? OM_STANCE_COOPERATIVE : OM_STANCE_HOSTILE;
        w->faction_template[fid] = templates[fid];
    }

    /* (4) per-faction placement, in faction order. */
    uint32_t cursor = 0;
    uint32_t highest_frontier[OM_MAX_FACTIONS];
    for (uint32_t fid = 0; fid < n_factions; fid++) {
        om_archetype arch = w->faction_archetype[fid];
        double pop_sum = 0.0;
        uint32_t pop_count = 0;

        if (templates[fid] == OM_TMPL_ISOLATED) {
            uint32_t home = cursor++;
            gen_place_region(w, home, OM_TIER_HOME, (int32_t)fid, arch, &pop_sum, &pop_count);
            for (uint32_t k = 0; k < OM_ISOLATED_FRONTIER_COUNT; k++) {
                uint32_t fr = cursor++;
                gen_place_region(w, fr, OM_TIER_FRONTIER, (int32_t)fid, arch, &pop_sum, &pop_count);
                gen_add_edge(w, home, fr);
            }
            highest_frontier[fid] = cursor - 1;
        } else if (templates[fid] == OM_TMPL_ARCHIPELAGO) {
            uint32_t home = cursor++;
            gen_place_region(w, home, OM_TIER_HOME, (int32_t)fid, arch, &pop_sum, &pop_count);
            uint32_t frontiers[OM_ARCHIPELAGO_FRONTIER_COUNT];
            for (uint32_t k = 0; k < OM_ARCHIPELAGO_FRONTIER_COUNT; k++) {
                frontiers[k] = cursor++;
                gen_place_region(w, frontiers[k], OM_TIER_FRONTIER, (int32_t)fid, arch, &pop_sum, &pop_count);
            }
            /* Only the first frontier touches the home; the rest chain off
             * each other, so the last is reachable only through the chain
             * (R-021-05's Archipelago shape, ALG-31). */
            gen_add_edge(w, home, frontiers[0]);
            for (uint32_t k = 1; k < OM_ARCHIPELAGO_FRONTIER_COUNT; k++)
                gen_add_edge(w, frontiers[k - 1], frontiers[k]);
            highest_frontier[fid] = frontiers[OM_ARCHIPELAGO_FRONTIER_COUNT - 1];
        } else { /* OM_TMPL_TWIN_COLONY */
            uint32_t f1 = gen_randint(w, OM_TWIN_COLONY_FRONTIER_RANGE_LO, OM_TWIN_COLONY_FRONTIER_RANGE_HI);
            uint32_t f2 = gen_randint(w, OM_TWIN_COLONY_FRONTIER_RANGE_LO, OM_TWIN_COLONY_FRONTIER_RANGE_HI);
            /* Spend only what the feasibility gate's slack (n_regions minus
             * every faction's reserved minimum) still has left; a draw above
             * OM_TWIN_COLONY_FRONTIER_RANGE_LO that the budget can't afford
             * falls back to the reserved minimum instead of overrunning it. */
            uint32_t extra1 = f1 - OM_TWIN_COLONY_FRONTIER_RANGE_LO;
            if (extra1 > gen_twin_slack)
                extra1 = 0;
            gen_twin_slack -= extra1;
            f1 = OM_TWIN_COLONY_FRONTIER_RANGE_LO + extra1;
            uint32_t extra2 = f2 - OM_TWIN_COLONY_FRONTIER_RANGE_LO;
            if (extra2 > gen_twin_slack)
                extra2 = 0;
            gen_twin_slack -= extra2;
            f2 = OM_TWIN_COLONY_FRONTIER_RANGE_LO + extra2;

            uint32_t home1 = cursor++;
            gen_place_region(w, home1, OM_TIER_HOME, (int32_t)fid, arch, &pop_sum, &pop_count);
            for (uint32_t k = 0; k < f1; k++) {
                uint32_t fr = cursor++;
                gen_place_region(w, fr, OM_TIER_FRONTIER, (int32_t)fid, arch, &pop_sum, &pop_count);
                gen_add_edge(w, home1, fr);
            }
            uint32_t home2 = cursor++;
            gen_place_region(w, home2, OM_TIER_HOME, (int32_t)fid, arch, &pop_sum, &pop_count);
            gen_add_edge(w, home1, home2);
            for (uint32_t k = 0; k < f2; k++) {
                uint32_t fr = cursor++;
                gen_place_region(w, fr, OM_TIER_FRONTIER, (int32_t)fid, arch, &pop_sum, &pop_count);
                gen_add_edge(w, home2, fr);
            }
            highest_frontier[fid] = cursor - 1;
        }

        w->faction_tech[fid] = (pop_count > 0) ? (pop_sum / (double)pop_count) * OM_STARTING_TECH_RATIO : 0.0;
        /* See also: csrc/faction.c om_faction_set -- the recalc must run
         * wherever archetype/tech land, and worldgen writes both fields
         * directly instead of going through that setter (avoids its RNG
         * confidence roll, R-022-04), so the cache would stay 0.0 forever
         * without this call. */
        om_faction_tech_multipliers_recalc(w, (int32_t)fid);
    }

    uint32_t total_inhabited = cursor;
    for (uint32_t idx = total_inhabited; idx < n_regions; idx++)
        om_region_set_owner(w, idx, -1, -1);

    /* (5) corridors, faction order: each faction's highest-numbered frontier
     * gets a chain of WORLD_MIN_FACTION_SEPARATION empties, and the 15
     * corridor ends are chained together in faction order (R-021-06). */
    uint32_t n_empty_pool = n_regions - total_inhabited;
    uint32_t *pool = calloc(n_empty_pool, sizeof(uint32_t));
    uint32_t *corridor_ends = calloc(n_factions, sizeof(uint32_t));
    uint32_t *connected = calloc(n_regions, sizeof(uint32_t));
    if (!pool || !corridor_ends || !connected) {
        free(pool);
        free(corridor_ends);
        free(connected);
        return;
    }
    for (uint32_t i = 0; i < n_empty_pool; i++)
        pool[i] = total_inhabited + i;
    uint32_t pool_n = n_empty_pool;

    for (uint32_t fid = 0; fid < n_factions; fid++) {
        double u = om_rng_draw(w);
        uint32_t pick = (uint32_t)floor(u * (double)pool_n);
        if (pick >= pool_n)
            pick = pool_n - 1;
        uint32_t chosen = pool[pick];
        pool[pick] = pool[pool_n - 1];
        pool_n--;
        gen_add_edge(w, highest_frontier[fid], chosen);
        corridor_ends[fid] = chosen;
    }
    for (uint32_t fid = 0; fid + 1 < n_factions; fid++)
        gen_add_edge(w, corridor_ends[fid], corridor_ends[fid + 1]);

    /* (6) empty attachment: each remaining empty links to one already-
     * connected region, re-rolling up to WORLD_EMPTY_ATTACH_REROLL_CAP times
     * to avoid a home (R-021-07). */
    uint32_t connected_n = 0;
    for (uint32_t i = 0; i < total_inhabited; i++)
        connected[connected_n++] = i;
    for (uint32_t fid = 0; fid < n_factions; fid++)
        connected[connected_n++] = corridor_ends[fid];

    for (uint32_t i = 0; i < pool_n; i++) {
        uint32_t empty_region = pool[i];
        uint32_t target = connected[0];
        for (uint32_t attempt = 0; attempt < OM_WORLD_EMPTY_ATTACH_REROLL_CAP; attempt++) {
            double u = om_rng_draw(w);
            uint32_t pick = (uint32_t)floor(u * (double)connected_n);
            if (pick >= connected_n)
                pick = connected_n - 1;
            target = connected[pick];
            if (w->regions[target].tier != OM_TIER_HOME)
                break;
        }
        gen_add_edge(w, empty_region, target);
        connected[connected_n++] = empty_region;
    }
    free(pool);
    free(corridor_ends);
    free(connected);

    /* (7) extra edges: max(1, floor(ratio * N)) attempted, at most
     * WORLD_EXTRA_EDGE_ATTEMPT_MULTIPLIER times that many draws, never
     * between two homes (R-021-08) and never between the player's home or
     * frontier and any NPC's (R-025-04). */
    if (w->gen_extra_edges_on) {
        uint32_t extra_target = (uint32_t)floor(w->gen_extra_edge_ratio * (double)n_regions);
        if (extra_target < 1)
            extra_target = 1;
        uint32_t max_attempts = extra_target * OM_WORLD_EXTRA_EDGE_ATTEMPT_MULTIPLIER;
        uint32_t successes = 0;
        for (uint32_t attempt = 0; attempt < max_attempts && successes < extra_target; attempt++) {
            double ua = om_rng_draw(w);
            uint32_t a = (uint32_t)floor(ua * (double)n_regions);
            if (a >= n_regions)
                a = n_regions - 1;
            double ub = om_rng_draw(w);
            uint32_t b = (uint32_t)floor(ub * (double)n_regions);
            if (b >= n_regions)
                b = n_regions - 1;
            if (a == b)
                continue;
            om_edge_type existing;
            if (om_region_edge(w, a, b, &existing))
                continue;
            if (w->regions[a].tier == OM_TIER_HOME && w->regions[b].tier == OM_TIER_HOME)
                continue;
            int32_t oa = w->regions[a].faction_id;
            int32_t ob = w->regions[b].faction_id;
            if ((oa == 0 && ob > 0) || (ob == 0 && oa > 0))
                continue; /* R-025-04: player <-> NPC rejected, re-rolled */
            gen_add_edge(w, a, b);
            successes++;
        }
    }

    /* (8) edge typing already happened at each gen_add_edge call (no
     * separate draw). One final reseed (ALG-31): the draw's IEEE-754 bit
     * pattern becomes the new RNG state, deterministic and platform-
     * independent, with no formula named in the doc for this step. */
    double final_u = om_rng_draw(w);
    uint64_t reseed_bits;
    memcpy(&reseed_bits, &final_u, sizeof(reseed_bits));
    om_rng_seed(w, reseed_bits);

    w->generated = 1;
}

void om_gen_set_region_range(om_world *w, uint32_t lo, uint32_t hi) {
    if (w == NULL)
        return;
    w->gen_region_min = lo;
    w->gen_region_max = hi;
}

void om_gen_set_faction_count(om_world *w, uint32_t n) {
    if (w == NULL)
        return;
    w->gen_faction_count = n;
}

void om_gen_set_extra_edge_ratio(om_world *w, double ratio) {
    if (w == NULL)
        return;
    w->gen_extra_edge_ratio = ratio;
}

void om_gen_set_player_preference(om_world *w, int32_t faction_id, om_template pref) {
    if (w == NULL)
        return;
    /* HDR3: faction_id param accepted; stored preference applies to fid==0 in
     * gen_roll_template (single gen_player_pref field; per-faction storage
     * requires an om_internal.h field not yet added). Default single-player
     * behaviour (faction_id==0) is identical to ABI 2. */
    (void)faction_id;
    w->gen_player_pref = pref;
}

void om_gen_set_preference_weight(om_world *w, double preferred) {
    if (w == NULL)
        return;
    w->gen_preference_weight = preferred;
}

void om_gen_set_extra_edges_enabled(om_world *w, int on) {
    if (w == NULL)
        return;
    w->gen_extra_edges_on = on != 0;
}

void om_gen_set_home_range(om_world *w, om_archetype archetype,
                           double mil_lo, double mil_hi, double eco_lo, double eco_hi) {
    if (w == NULL || archetype < OM_ARCH_CONQUEROR || archetype > OM_ARCH_OPPORTUNIST)
        return;
    double *hr = w->gen_home_range[archetype - OM_ARCH_CONQUEROR];
    hr[OM_GEN_HR_MIL_LO] = mil_lo;
    hr[OM_GEN_HR_MIL_HI] = mil_hi;
    hr[OM_GEN_HR_ECO_LO] = eco_lo;
    hr[OM_GEN_HR_ECO_HI] = eco_hi;
}

int om_world_generated(const om_world *w) {
    if (w == NULL)
        return 0;
    return w->generated;
}

uint64_t om_world_seed(const om_world *w) {
    if (w == NULL)
        return 0;
    return w->seed;
}

uint32_t om_world_edge_count(const om_world *w) {
    if (w == NULL)
        return 0;
    return w->edge_count;
}

om_template om_faction_template(const om_world *w, int32_t faction_id) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return OM_TMPL_NONE;
    return w->faction_template[faction_id];
}
