/* ouroboros_sim.h — the C sim-core ABI contract.
 *
 * This header is the fenced contract between the fenced test suite
 * (tests/csim/, which calls these functions via ctypes) and the Agora-written
 * implementation (csrc/*.c, which must satisfy them). It is owned by the parent
 * (Claude); Agora may not edit it. See docs/northstar/e2e/E-02.md and
 * docs/bible/algorithms.md for the behavior each function must reproduce, and
 * docs/northstar/research/c_rewrite.md for the determinism contract.
 *
 * Scope of this version: E-02 (region fields, composites, drift). It exposes a
 * hard-fixture path (om_region_set*) so E-02 is tested in isolation without a
 * live world generator (E-03) or faction agents (E-05). Later epics extend this
 * header; they never break an existing signature.
 *
 * Determinism: all math is double; same seed + same call sequence must produce a
 * byte-identical trace on Linux, Windows, and macOS. No platform transcendental
 * calls (use om_sin). Built with -fno-fast-math -ffp-contract=off and SSE math.
 */
#ifndef OUROBOROS_SIM_H
#define OUROBOROS_SIM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Opaque world handle. */
typedef struct om_world om_world;

/* Field and composite indices — stable, part of the ABI. */
typedef enum {
    OM_F_MILITARY   = 0,
    OM_F_ECONOMY    = 1,
    OM_F_TENSION    = 2,
    OM_F_POPULATION = 3,
    OM_F_COUNT      = 4
} om_field;

typedef enum {
    OM_C_STABILITY = 0,
    OM_C_CAPACITY  = 1,
    OM_C_COUNT     = 2
} om_composite;

typedef enum {
    OM_TIER_EMPTY    = 0,
    OM_TIER_FRONTIER = 1,
    OM_TIER_HOME     = 2
} om_tier;

/* Per-region, per-tick drift breakdown. One leg per named term in drift.py, so
 * behavior assertions and positive controls can read each contribution
 * (algorithms.md ALG-01..ALG-08). Every value is the signed contribution added
 * to the field this tick, before the net sum and the clamp. */
typedef struct om_drift_row {
    double military_decay;      /* ALG-02 */
    double military_recruit;    /* ALG-03 */
    double military_modifier;   /* ALG-04 faction modifier */
    double economy_growth;      /* ALG-05 */
    double economy_drag;        /* ALG-05 tension drag */
    double economy_overcap;     /* ALG-05 overcapacity decay */
    double economy_adjacency;   /* ALG-06 friendly-neighbor bonus */
    double economy_osc_delta;   /* ALG-01 oscillator delta (a delta, never a level) */
    double tension_economic;    /* ALG-07 */
    double tension_stress;      /* ALG-07 */
    double tension_subsist;     /* ALG-07 */
    double tension_decay;       /* ALG-07 */
    double tension_osc_delta;   /* ALG-01 */
    double population_base;      /* ALG-08 growth/decline */
    double population_subsist;   /* ALG-08 subsistence loss */
    double d_military;           /* net, post-sum, pre-clamp */
    double d_economy;
    double d_tension;
    double d_population;
} om_drift_row;

/* One row of the T1 state trace: fixed width, so two dumps diff by memcmp for
 * the cross-platform determinism test (R-020-01). Fields are POST-clamp;
 * composites are POST-recompute (2 decimal places, matching region.py). */
typedef struct om_trace_row {
    uint64_t     tick;
    uint32_t     region_idx;
    int32_t      faction_id;
    uint32_t     tier;          /* om_tier */
    uint32_t     _pad;          /* keep 8-byte alignment explicit and identical */
    double       military;
    double       economy;
    double       tension;
    double       population;
    double       stability;
    double       capacity;
    om_drift_row drift;
    uint64_t     checksum;      /* world checksum if tick % om_checksum_cadence() == 0, else 0 */
} om_trace_row;

/* ---- ABI version ---- */
/* The test harness asserts this matches what it was written against. Bump on any
 * breaking change to a signature or struct layout. */
uint32_t om_abi_version(void);

/* ---- lifecycle ---- */
om_world *om_world_new(uint32_t n_regions, uint64_t seed);
void      om_world_free(om_world *w);
void      om_world_set_seed(om_world *w, uint64_t seed);
void      om_world_generate(om_world *w);   /* E-03 world gen; not required for E-02 isolation tests */

/* ---- hard-fixture path (isolation testing) ----
 * Set a region's state directly, bypassing world generation, so E-02 drift is
 * tested against known inputs. econ_phase / tension_phase are the ALG-01 phase
 * offsets in [0, 2pi). faction_id < 0 means unowned. Returns 0 on success. */
int  om_region_set(om_world *w, uint32_t idx, om_tier tier,
                   double military, double economy, double tension, double population,
                   double econ_phase, double tension_phase, int32_t faction_id);
void om_region_set_adjacency(om_world *w, uint32_t idx,
                             const uint32_t *neighbor_idx, uint32_t n_neighbors);
void om_region_set_faction_modifier(om_world *w, int32_t faction_id,
                                    om_field field, double value);   /* ALG-04 */
uint32_t om_region_count(const om_world *w);

/* ---- tick (7-step sequence, tick auto-increments from 1) ---- */
uint64_t om_world_step(om_world *w);                 /* advance one tick, return new tick */
uint64_t om_world_run(om_world *w, uint64_t n_ticks); /* bulk path the scale gate times */

/* ---- read state ---- */
double  om_region_field(const om_world *w, uint32_t idx, om_field f);
double  om_region_composite(const om_world *w, uint32_t idx, om_composite c);
om_tier om_region_tier(const om_world *w, uint32_t idx);
/* Copy the last tick's drift breakdown for region idx into *out. Returns 0 on
 * success, non-zero if the region is empty (empty regions never drift). */
int     om_region_drift(const om_world *w, uint32_t idx, om_drift_row *out);

/* ---- checksum ---- */
/* FNV-1a 64-bit over the little-endian IEEE-754 bits of every inhabited region's
 * six numbers in region-index order, folded with the tick. Computable on demand. */
uint64_t om_world_checksum(const om_world *w);
uint32_t om_checksum_cadence(void);   /* returns 10 (R-020-03) */

/* ---- deterministic transcendental ---- */
/* The one platform-independent sine used by the ALG-01 oscillator. Compiled
 * identically on every platform; the sim never calls libm sin(). */
double om_sin(double x);

/* ---- T1 trace ---- */
void     om_trace_enable(om_world *w, int on);   /* record one row per (tick, region) while on */
uint64_t om_trace_len(const om_world *w);
/* Copy up to count rows starting at row index start into out[]; returns rows written. */
uint64_t om_trace_read(const om_world *w, uint64_t start, uint64_t count, om_trace_row *out);

/* ---- positive-control fault injection (debug build only) ----
 * Compiled only into libouroboros_dbg.so (-DOM_DEBUG_INJECT). Each bug reproduces
 * one "Ways this could be wrong" signature from the E-02 e2e so a control test can
 * prove its detector actually trips. Never present in the release library. */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_OSC_AS_LEVEL      = 0,  /* oscillator added as a level, not a delta */
    OM_BUG_RAW_NOT_TREND     = 1,  /* coupling reads the raw field, not the de-oscillated trend */
    OM_BUG_COMPOSITE_PRE_CLAMP = 2,/* composites computed before the clamp */
    OM_BUG_EMPTY_DRIFTS      = 3,  /* empty-tier region drifts */
    OM_BUG_GE_NOT_GT         = 4,  /* threshold uses >= where the source uses > */
    OM_BUG_SLOW              = 5   /* deliberate slowdown, to prove the speed leg can fail */
} om_bug;
void om_debug_inject(om_world *w, om_bug bug);
#endif

#ifdef __cplusplus
}
#endif

#endif /* OUROBOROS_SIM_H */
