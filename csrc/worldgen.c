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

/* Not an ALG-tuned constant (algorithms.md never names it as an IDENT =
 * value); matches the literal already used for the same purpose in
 * csrc/sim.c's static OM_TWO_PI so the two stay in step. */
#define OM_GEN_TWO_PI 6.28318530717958647692528676655900577
/* ALG-30's field clamp target; no named IDENT in the doc's own prose. */
#define OM_GEN_FIELD_MIN 0.0
#define OM_GEN_FIELD_MAX 100.0

/* gen_home_range[archetype][slot] slot indices (ouroboros_sim.h ~line 694:
 * "[mil_lo, mil_hi, eco_lo, eco_hi]"). */
#define OM_GEN_HR_MIL_LO 0
#define OM_GEN_HR_MIL_HI 1
#define OM_GEN_HR_ECO_LO 2
#define OM_GEN_HR_ECO_HI 3

/* ======================================================================
 * BLOCKER (reported, not fixed here -- out of scope: worldgen.c is the only
 * file this card may edit):
 *
 * 1. csrc/region.c:11 `if (n_regions == 0) return NULL;` in om_world_new
 *    contradicts ouroboros_sim.h:693-694's own documented contract ("pass
 *    n_regions == 0 to draw it uniformly ... at generation"). Every E-03
 *    acceptance test calls world_factory(n_regions=0, ...), so om_world_new
 *    returns NULL before this file ever runs. Proposed fix (2-line diff):
 *    guard the two n_regions-dependent blocks in om_world_new so 0 leaves
 *    w->regions == NULL / w->n_regions == 0 instead of failing; this file's
 *    om_world_generate() below already allocates w->regions itself when it
 *    finds w->n_regions == 0 on entry, so no other change is needed.
 *
 * 2. csrc/om_internal.h's `om_edge_type region_edge[64][64]` (and the
 *    matching `a >= 64 || b >= 64` guards in csrc/faction.c's
 *    om_region_set_edge/om_region_edge) cap recorded edges at region index
 *    63. E-03's own default region-count range is [60, 110]
 *    (OM_WORLD_REGION_COUNT_RANGE_*) and several tests force a draw that
 *    yields 85 regions, so any edge touching region 64+ silently fails to
 *    record. Proposed fix: widen region_edge to
 *    [OM_WORLD_REGION_COUNT_RANGE_HI][OM_WORLD_REGION_COUNT_RANGE_HI] (or a
 *    new OM_MAX_REGIONS constant >= 110) in om_internal.h and raise the two
 *    `>= 64` bounds in faction.c to match.
 *
 * Both are outside this file; this generator is written to be correct once
 * either lands, but cannot be exercised end-to-end until then.
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

static uint32_t gen_template_max_size(om_template t) {
    switch (t) {
        case OM_TMPL_ISOLATED:
            return 1 + OM_ISOLATED_FRONTIER_COUNT;
        case OM_TMPL_TWIN_COLONY:
            return OM_TWIN_COLONY_HOME_COUNT * (1 + OM_TWIN_COLONY_FRONTIER_RANGE_HI);
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
    double econ_phase = gen_uniform(w, OM_GEN_FIELD_MIN, OM_GEN_TWO_PI);
    double tension_phase = gen_uniform(w, OM_GEN_FIELD_MIN, OM_GEN_TWO_PI);

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

    /* (3) feasibility -- no draw. Twin Colony's per-home frontier counts are
     * not rolled yet, so the gate reserves each faction's max possible size
     * (never lets a later roll change the already-fixed budget). */
    uint32_t needed = n_factions; /* one corridor empty per faction */
    for (uint32_t fid = 0; fid < n_factions; fid++)
        needed += gen_template_max_size(templates[fid]);
    needed += 1;
    if (n_regions < needed)
        return;

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

void om_gen_set_player_preference(om_world *w, om_template pref) {
    if (w == NULL)
        return;
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
