/* csrc/sim.c — E-02 tick loop, drift, oscillator, clamps, trace, checksum
 * (build cards 201a/201b). Hand-written after the local build ladder
 * exhausted 30 runs at best 28/40 on the acceptance suite.
 *
 * PRIVATE LAYOUT, verbatim from csrc/om_internal.h (already included below).
 *
 * Key correction found during hand-implementation, not present in any prior
 * candidate or in card 201a's own brief: the "previous oscillator value"
 * (osc(tick-1)) must be recomputed FRESH each step directly from the GLOBAL
 * tick counter and the region's phase -- NOT read from a stored
 * r->prev_econ_osc / r->prev_tension_osc field. Those fields exist in the
 * private layout but are never load-bearing: tests call om_region_set
 * between om_world_step calls within a single test (e.g.
 * test_R_018_03_coupling_reads_trend_not_raw), and om_region_set
 * unconditionally resets prev_econ_osc/prev_tension_osc to 0.0 (region.c).
 * A stateful implementation that relies on those fields being carried
 * forward across step calls breaks exactly this class of fixture -- almost
 * certainly why every local-model candidate stalled around 0-28/40 despite
 * getting the capacity/stability split correct. The oscillator is a pure
 * function of (tick, phase); it needs no persisted state at all.
 */
#include "ouroboros_sim.h"
#include "om_internal.h"
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ---------------------------------------------------------------- om_sin */

static const double OM_PI = 3.14159265358979323846264338327950288;
static const double OM_TWO_PI = 6.28318530717958647692528676655900577;

/* Deterministic, portable sine: range-reduce into [-pi, pi], then a
 * minimax-style Taylor polynomial. Never calls libm sin() so the trace is
 * identical bit-for-bit across platforms. Used consistently by every
 * drift/oscillator computation below and by the test harness's own oracle
 * (conftest.osc calls this same function via ctypes), so accuracy against
 * the mathematical sine only needs to be good enough for the "probe economy
 * settles 50-60" behavioral gate -- a 7-term series is comfortably enough. */
double om_sin(double x) {
    double k = floor(x / OM_TWO_PI + 0.5);
    double r = x - k * OM_TWO_PI; /* r in [-pi, pi] */
    double r2 = r * r;
    double term = r;
    double sum = r;
    term *= -r2 / (2.0 * 3.0);  sum += term;   /* -x^3/3! */
    term *= -r2 / (4.0 * 5.0);  sum += term;   /* +x^5/5! */
    term *= -r2 / (6.0 * 7.0);  sum += term;   /* -x^7/7! */
    term *= -r2 / (8.0 * 9.0);  sum += term;   /* +x^9/9! */
    term *= -r2 / (10.0 * 11.0); sum += term;  /* -x^11/11! */
    return sum;
}

static double om_osc(double amplitude, double period, double phase, uint64_t tick) {
    return amplitude * om_sin(OM_TWO_PI * (double)tick / period + phase);
}

/* Previous-tick oscillator value: 0 at tick 1 (R-018-02), otherwise the
 * oscillator evaluated fresh at tick-1. Stateless by design -- see file
 * header comment. */
static double om_osc_prev(double amplitude, double period, double phase, uint64_t tick) {
    if (tick <= 1) return 0.0;
    return om_osc(amplitude, period, phase, tick - 1);
}

#define ECON_AMPLITUDE 6.0
#define ECON_PERIOD 15.0
#define TENSION_AMPLITUDE 2.0
#define TENSION_PERIOD 18.0

/* ---------------------------------------------------------------- clamp */

static double om_clamp(double v, double lo, double hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

/* ---------------------------------------------------------------- trace */

static void om_trace_append(om_world *w, const om_trace_row *row) {
    if (!w->trace_on) return;
    if (w->trace_len >= w->trace_cap) {
        uint64_t new_cap = w->trace_cap ? w->trace_cap * 2 : 64;
        om_trace_row *grown = realloc(w->trace, new_cap * sizeof(om_trace_row));
        if (!grown) return; /* drop the row rather than crash */
        w->trace = grown;
        w->trace_cap = new_cap;
    }
    w->trace[w->trace_len++] = *row;
}

/* ---------------------------------------------------------------- step */

uint64_t om_world_step(om_world *w) {
    if (!w) return 0;
    w->tick++;
    uint64_t tick = w->tick;

    /* OM_BUG_SLOW: deliberate slowdown so the speed gate can be proven to
     * fail (test_control_slow). Independent of region count. */
#ifdef OM_DEBUG_INJECT
    if (w->inject == OM_BUG_SLOW) {
        volatile double junk = 0.0;
        for (long k = 0; k < 2000000; k++) junk += (double)k * 1.0000001;
        (void)junk;
    }
#endif

    /* Steps 1-2: Events (E-04): resolve the due queue, then evaluate fresh
     * triggers on every inhabited region (docs/bible/algorithms.md:13-14). */
#ifdef OM_DEBUG_INJECT
    int events_after_factions = (w->inject == OM_BUG_EVENTS_AFTER_FACTIONS);
#else
    int events_after_factions = 0;
#endif
    if (om_world_feature(w, OM_FEAT_EVENTS) && !events_after_factions) {
        om_step_events(w);              /* 1-2 */
    }

    /* Step 3: Factions (E-05) */
    if (om_world_feature(w, OM_FEAT_FACTIONS)) {
        /* 3a snapshot */
        memcpy(w->faction_budget_snapshot, w->faction_budget, sizeof(w->faction_budget));
        om_faction_step_budget(w);     /* 3b */
#ifdef OM_DEBUG_INJECT
        if (w->inject == OM_BUG_TELEGRAPH_AFTER_REINFORCE) {
            /* Fault: 3c (telegraph maturation) runs after 3e (reactive
             * reinforcement) instead of before it. */
            om_step_decisions(w);          /* 3d */
            om_step_reinforce(w);          /* 3e */
            om_step_telegraphs(w);         /* 3c */
        } else
#endif
        {
            om_step_telegraphs(w);         /* 3c */
            om_step_decisions(w);          /* 3d */
            om_step_reinforce(w);          /* 3e */
        }
#ifdef OM_DEBUG_INJECT
        if (w->inject == OM_BUG_COLLISION_AFTER_RESOLVE) {
            /* Fault: the collision step runs after 3f resolves individual
             * intents, so 3f has already double-resolved the colliding
             * ones before the collision step ever groups them. */
            om_step_resolve(w);        /* 3f */
            om_step_collisions(w);
        } else
#endif
        {
            om_step_collisions(w);     /* S-039: grouped-target resolution, before 3f */
            om_step_resolve(w);        /* 3f */
        }
    }

#ifdef OM_DEBUG_INJECT
    if (om_world_feature(w, OM_FEAT_EVENTS) && events_after_factions) {
        om_step_events(w);              /* Fault: 1-2 run after step 3 instead of before it */
    }
#endif

    /* Step 4: Friction & Admin Revolts (E-05) */
    if (om_world_feature(w, OM_FEAT_FRICTION)) {
        om_step_friction(w);           /* 4 */
    }
    if (om_world_feature(w, OM_FEAT_ADMIN_REVOLTS)) {
        om_step_admin_revolts(w);      /* 4.1 */
    }

    /* Step 5: Drift (E-02), gated on OM_FEAT_DRIFT and run after
     * factions/friction/admin-revolts (docs/bible/algorithms.md:9-29). */
#ifdef OM_DEBUG_INJECT
    int drift_gate_ignored = (w->inject == OM_BUG_DRIFT_GATE_IGNORED);
#else
    int drift_gate_ignored = 0;
#endif
    if (om_world_feature(w, OM_FEAT_DRIFT) || drift_gate_ignored) {
    for (uint32_t i = 0; i < w->n_regions; i++) {
        om_region *r = &w->regions[i];
        int inhabited = (r->tier != OM_TIER_EMPTY);
#ifdef OM_DEBUG_INJECT
        int drift_this_region = inhabited || (w->inject == OM_BUG_EMPTY_DRIFTS);
#else
        int drift_this_region = inhabited;
#endif
        if (!drift_this_region) continue;
#ifdef OM_DEBUG_INJECT
        if (!inhabited && w->inject == OM_BUG_EMPTY_DRIFTS) {
            /* om_region_field() masks every field to 0.0 for tier==EMPTY
             * (region.c) regardless of what is stored, so the only way this
             * injected bug can be externally observed at all is if the
             * region also stops reading as empty -- matches a plausible
             * real bug (the tier check itself was dropped, so the region is
             * treated as ordinary terrain everywhere, not just in drift). */
            r->tier = OM_TIER_FRONTIER;
        }
#endif

        int raw_not_trend = 0;
        int osc_as_level = 0;
        int ge_not_gt = 0;
        int composite_pre_clamp = 0;
#ifdef OM_DEBUG_INJECT
        raw_not_trend = (w->inject == OM_BUG_RAW_NOT_TREND);
        osc_as_level = (w->inject == OM_BUG_OSC_AS_LEVEL);
        ge_not_gt = (w->inject == OM_BUG_GE_NOT_GT);
        composite_pre_clamp = (w->inject == OM_BUG_COMPOSITE_PRE_CLAMP);
#endif

        double osc_econ_now = om_osc(ECON_AMPLITUDE, ECON_PERIOD, r->econ_phase, tick);
        double osc_econ_prev = om_osc_prev(ECON_AMPLITUDE, ECON_PERIOD, r->econ_phase, tick);
        double osc_tension_now = om_osc(TENSION_AMPLITUDE, TENSION_PERIOD, r->tension_phase, tick);
        double osc_tension_prev = om_osc_prev(TENSION_AMPLITUDE, TENSION_PERIOD, r->tension_phase, tick);

        double d_osc_econ = osc_as_level ? osc_econ_now : (osc_econ_now - osc_econ_prev);
        double d_osc_tension = osc_as_level ? osc_tension_now : (osc_tension_now - osc_tension_prev);

        double trend_economy = raw_not_trend ? r->economy : (r->economy - osc_econ_prev);
        double trend_tension = raw_not_trend ? r->tension : (r->tension - osc_tension_prev);
        double trend_population = r->population; /* no oscillator on population */

        om_drift_row d;
        memset(&d, 0, sizeof(d));

        /* ---- military (ALG-02, ALG-03, ALG-04) ---- */
        double headroom = 1.0 - r->military / 90.0;
        if (headroom < 0.0) headroom = 0.0;

        d.military_decay = -(r->military * 0.006) * (1.0 - trend_economy / 100.0);

        int recruit_gate = ge_not_gt ? (trend_economy >= 20.0) : (trend_economy > 20.0);
        double eco_term = 0.0;
        if (recruit_gate) {
            eco_term = 12.0 * (trend_economy / 100.0) * (trend_population / 100.0)
                       * pow(1.0 - r->tension / 100.0, 0.3);
        }
        d.military_recruit = (0.1 * (trend_population / 100.0) + eco_term) * headroom;

        double mod = 0.0;
        if (r->faction_id >= 0 && r->faction_id < OM_MAX_FACTIONS) {
            mod = w->faction_mod[r->faction_id][OM_F_MILITARY];
        }
        d.military_modifier = mod * headroom;

        d.d_military = d.military_decay + d.military_recruit + d.military_modifier;

        /* ---- economy (ALG-05, ALG-06) ---- */
        d.economy_growth = 2.0 * (trend_population / 100.0);
        d.economy_drag = -((trend_tension / 100.0) * 0.40);

        double local_capacity = trend_population * 0.85;
        int overcap_gate = ge_not_gt ? (trend_economy >= local_capacity) : (trend_economy > local_capacity);
        d.economy_overcap = overcap_gate ? -(15.0 * (trend_economy - local_capacity) / 100.0) : 0.0;

        double adjacency = 0.0;
        if (r->faction_id >= 0) {
            for (uint32_t k = 0; k < r->n_neighbors; k++) {
                uint32_t nidx = r->neighbors[k];
                if (nidx >= w->n_regions) continue;
                const om_region *nb = &w->regions[nidx];
                if (nb->tier == OM_TIER_EMPTY) continue;
                if (nb->faction_id != r->faction_id) continue;
                adjacency += 0.05 * (nb->economy / 100.0);
            }
        }
        d.economy_adjacency = adjacency;
        d.economy_osc_delta = d_osc_econ;

        d.d_economy = d.economy_growth + d.economy_drag + d.economy_overcap
                      + d.economy_adjacency + d.economy_osc_delta;

        /* ---- tension (ALG-07), s' from ALG-09's weights on primed inputs ---- */
        double s_prime = r->military * 0.40 + (100.0 - trend_tension) * 0.35 + trend_population * 0.25;
        if (r->military < 10.0) s_prime *= 0.70;
        if (trend_population < 20.0) s_prime *= 0.75;

        d.tension_economic = ((50.0 - trend_economy) / 100.0) * 0.5 * (trend_population / 100.0);
        double stress_margin = 40.0 - s_prime;
        d.tension_stress = (stress_margin > 0.0 ? stress_margin : 0.0) * 0.008;

        double thresh = 8.0 + 3.0;
        if (trend_economy < thresh) {
            double severity = (thresh - trend_economy) / 3.0;
            d.tension_subsist = 0.15 * severity * (trend_population / 100.0);
        } else {
            d.tension_subsist = 0.0;
        }
        d.tension_decay = -(0.20 * (trend_tension / 100.0));
        d.tension_osc_delta = d_osc_tension;

        d.d_tension = d.tension_economic + d.tension_stress + d.tension_subsist
                      + d.tension_decay + d.tension_osc_delta;

        /* ---- population (ALG-08) ---- */
        double pop_base;
        if (trend_economy > 15.0) {
            pop_base = 2.0 * ((trend_economy - 15.0) / 85.0) * (1.0 - trend_population / 100.0);
        } else {
            pop_base = -(15.0 - trend_economy) * 0.2;
        }
        d.population_base = pop_base;
        if (trend_economy < 11.0) {
            double severity = (11.0 - trend_economy) / 3.0;
            d.population_subsist = -(0.08 * severity);
        } else {
            d.population_subsist = 0.0;
        }
        d.d_population = d.population_base + d.population_subsist;

        /* ---- apply + clamp (composite_pre_clamp bug: skip the military/
         * population clamp bounds before the tick's fields settle, matching
         * the "composites computed before the clamp" watch-for as closely as
         * the ABI allows -- composites themselves are always a pure live
         * function of the final stored fields (region.c), so this bug's
         * only observable channel is via the fields it lets drift out of
         * bounds during the run). ---- */
        double new_military = r->military + d.d_military;
        double new_economy = r->economy + d.d_economy;
        double new_tension = r->tension + d.d_tension;
        double new_population = r->population + d.d_population;

        r->military = composite_pre_clamp ? new_military : om_clamp(new_military, 0.0, 100.0);
        r->economy = om_clamp(new_economy, 8.0, 100.0);
        r->tension = om_clamp(new_tension, 0.0, 100.0);
        r->population = composite_pre_clamp ? new_population : om_clamp(new_population, 0.0, 100.0);

        r->last_drift = d;

        if (w->trace_on) {
            om_trace_row row;
            memset(&row, 0, sizeof(row));
            row.tick = tick;
            row.region_idx = i;
            row.faction_id = r->faction_id;
            row.tier = (uint32_t)r->tier;
            row.military = r->military;
            row.economy = r->economy;
            row.tension = r->tension;
            row.population = r->population;
            row.stability = om_region_composite(w, i, OM_C_STABILITY);
            row.capacity = om_region_composite(w, i, OM_C_CAPACITY);
            row.drift = d;
            row.checksum = (tick % om_checksum_cadence() == 0) ? om_world_checksum(w) : 0;
            om_trace_append(w, &row);
        }
    }
    }

    return w->tick;
}

uint64_t om_world_run(om_world *w, uint64_t n_ticks) {
    if (!w) return 0;
    for (uint64_t i = 0; i < n_ticks; i++) {
        om_world_step(w);
    }
    return w->tick;
}

int om_region_drift(const om_world *w, uint32_t idx, om_drift_row *out) {
    if (!w || idx >= w->n_regions) return -1;
    const om_region *r = &w->regions[idx];
    if (r->tier == OM_TIER_EMPTY) return -1;
    if (out) *out = r->last_drift;
    return 0;
}

/* ---------------------------------------------------------------- trace ABI */

void om_trace_enable(om_world *w, int on) {
    if (!w) return;
    w->trace_on = on ? 1 : 0;
}

uint64_t om_trace_len(const om_world *w) {
    return w ? w->trace_len : 0;
}

uint64_t om_trace_read(const om_world *w, uint64_t start, uint64_t count, om_trace_row *out) {
    if (!w || !out) return 0;
    if (start >= w->trace_len) return 0;
    uint64_t avail = w->trace_len - start;
    uint64_t n = count < avail ? count : avail;
    memcpy(out, &w->trace[start], (size_t)n * sizeof(om_trace_row));
    return n;
}

/* ---------------------------------------------------------------- checksum */

static uint64_t om_fnv1a_bytes(uint64_t h, const void *data, size_t len) {
    const unsigned char *p = (const unsigned char *)data;
    for (size_t i = 0; i < len; i++) {
        h ^= p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

uint64_t om_world_checksum(const om_world *w) {
    if (!w) return 0;
    uint64_t h = 14695981039346656037ULL;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        const om_region *r = &w->regions[i];
        if (r->tier == OM_TIER_EMPTY) continue;
        double stability = om_region_composite(w, i, OM_C_STABILITY);
        double capacity = om_region_composite(w, i, OM_C_CAPACITY);
        double vals[6] = {r->military, r->economy, r->tension, r->population, stability, capacity};
        for (int k = 0; k < 6; k++) {
            h = om_fnv1a_bytes(h, &vals[k], sizeof(double));
        }
    }
    uint64_t tick_le = w->tick;
    h = om_fnv1a_bytes(h, &tick_le, sizeof(tick_le));
    return h;
}

/* ---------------------------------------------------------------- debug inject */

#ifdef OM_DEBUG_INJECT
void om_debug_inject(om_world *w, om_bug bug) {
    if (!w) return;
    w->inject = (int)bug;
}
#endif
