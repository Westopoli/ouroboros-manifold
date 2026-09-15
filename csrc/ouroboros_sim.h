/* ouroboros_sim.h — the C sim-core ABI contract.
 *
 * This header is the fenced contract between the fenced test suite
 * (tests/csim/, which calls these functions via ctypes) and the Agora-written
 * implementation (the csrc .c files, which must satisfy them). It is owned by the parent
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


/* ======================================================================
 * E-05: faction agents and conflict (epics/E-05-faction-agents-and-conflict.md,
 * e2e/E-05.md, algorithms.md ALG-11..ALG-25, ALG-29).
 *
 * Appended 2026-09-14. Nothing above this line changes. Everything below is the
 * hard-fixture path and the tick-log readers E-05's isolation tests need. World
 * generation (E-03), stance evolution (E-06), tech growth (E-06), event
 * resolution (E-04), and breakaway creation (E-07) are NOT implemented by E-05
 * cards; tests set their inputs directly with the om_faction_set* / om_region_set*
 * functions here, and read what E-05 wrote into the queue and the tick log.
 * ====================================================================== */

typedef enum {
    OM_ARCH_PLAYER      = 0,   /* player_civilization */
    OM_ARCH_CONQUEROR   = 1,
    OM_ARCH_FORTIFIER   = 2,
    OM_ARCH_OPPORTUNIST = 3,
    OM_ARCH_WARLORD     = 4,
    OM_ARCH_SCHISM      = 5,
    OM_ARCH_BREAKAWAY   = 6,
    OM_ARCH_DEFAULT     = 7
} om_archetype;

typedef enum {
    OM_STANCE_HOSTILE     = 0,
    OM_STANCE_NEUTRAL     = 1,
    OM_STANCE_COOPERATIVE = 2
} om_stance;

typedef enum {
    OM_EDGE_BORDER = 0,
    OM_EDGE_TRADE  = 1,
    OM_EDGE_BOTH   = 2
} om_edge_type;

/* ---- feature switches (fixture) ----
 * Mirror the tick sequence's launch flags (algorithms.md "Tick sequence"), all
 * on by default, plus DRIFT so a step can be isolated: an E-05 test switches
 * drift, events, diplomacy, and technology off and reads exactly what the
 * agents and the resolver did. Switching a feature off skips its step
 * entirely; it never changes what an enabled step computes. */
typedef enum {
    OM_FEAT_EVENTS        = 0,  /* tick steps 1 and 2 (E-04) */
    OM_FEAT_FACTIONS      = 1,  /* tick step 3 (E-05) */
    OM_FEAT_FRICTION      = 2,  /* tick step 4 (E-05, ALG-25) */
    OM_FEAT_ADMIN_REVOLTS = 3,  /* tick step 4.1 (E-05, ALG-29) */
    OM_FEAT_DIPLOMACY     = 4,  /* tick step 4.25 (E-06) */
    OM_FEAT_TECHNOLOGY    = 5,  /* tick step 4.5 (E-06) */
    OM_FEAT_DRIFT         = 6,  /* tick step 5 (E-02) */
    OM_FEAT_LIFECYCLE     = 7   /* tick step 6 (E-07) */
} om_feature;
void om_world_set_feature(om_world *w, om_feature f, int on);
int  om_world_feature(const om_world *w, om_feature f);

/* ---- faction fixture ----
 * Creates or replaces faction faction_id (0..OM_MAX_FACTIONS-1). budget and tech
 * are the starting values. attack_confidence < 0 means "roll it once from the
 * archetype's range with the world RNG" (R-032-01); >= 0 pins it (fixture).
 * Every stance toward every other faction starts hostile (R-032-04).
 * Returns 0 on success. */
#define OM_MAX_FACTIONS 64
int  om_faction_set(om_world *w, int32_t faction_id, om_archetype archetype,
                    double budget, double tech, double attack_confidence);
void om_faction_set_stance(om_world *w, int32_t from, int32_t toward, om_stance s); /* directed */
/* ALG-26 multipliers are E-06's; E-05 consumes them. Fixture pins them per faction
 * (1.0, 1.0, 1.0 = "no tech"). E-06 later computes them from tech and archetype. */
void om_faction_set_tech_multipliers(om_world *w, int32_t faction_id,
                                     double attack, double defense, double economy);
uint32_t om_faction_count(const om_world *w);
om_archetype om_faction_archetype(const om_world *w, int32_t faction_id);
double   om_faction_budget(const om_world *w, int32_t faction_id);
double   om_faction_confidence(const om_world *w, int32_t faction_id);
double   om_faction_tech(const om_world *w, int32_t faction_id);
om_stance om_faction_stance(const om_world *w, int32_t from, int32_t toward);
uint32_t om_faction_territory(const om_world *w, int32_t faction_id);  /* owned inhabited regions */

/* ---- region ownership and typed edges (fixture) ----
 * held_since_tick < 0 means "never conquered" (ALG-13: entrenchment 2.0).
 * om_region_set_edge replaces om_region_set_adjacency for E-05 and later: an
 * undirected edge with a type. Setting the same pair twice replaces the type. */
void    om_region_set_owner(om_world *w, uint32_t idx, int32_t faction_id, int64_t held_since_tick);
int32_t om_region_owner(const om_world *w, uint32_t idx);
int64_t om_region_held_since(const om_world *w, uint32_t idx);   /* < 0 if never conquered */
void    om_region_set_edge(om_world *w, uint32_t a, uint32_t b, om_edge_type t);
int     om_region_edge(const om_world *w, uint32_t a, uint32_t b, om_edge_type *out); /* 0 if no edge */

/* ---- forced RNG draws (fixture) ----
 * Rules quote exact stochastic draws ("a draw of 1.0", "draw 0.7"). The world
 * RNG is one PCG32 stream; this queues values that the next n uniform draws
 * return instead of the stream, in order, then the stream resumes. Every
 * consumer of the stream (agents, resolution, friction, admin roll, drift
 * oscillator does not draw) takes from the same queue, so tests set draws in
 * the documented draw order (algorithms.md). Draw order is part of the contract. */
void om_rng_force(om_world *w, const double *draws, uint32_t n);
uint32_t om_rng_forced_remaining(const om_world *w);

/* ---- tick log readers: everything E-05 decided or resolved on the LAST step ----
 * Each reader copies up to max records into out[] and returns the count. A
 * record set is replaced on every om_world_step; om_world_run keeps only the
 * final tick's records. Order within a set is the order the sim produced them
 * (faction id ascending for decisions; resolution order for the rest). */

typedef enum { OM_ACT_ACCUMULATE = 0, OM_ACT_ATTACK = 1, OM_ACT_COLONIZE = 2, OM_ACT_REINFORCE = 3 } om_action;
typedef enum { OM_MODE_TELEGRAPH = 0, OM_MODE_SURPRISE = 1 } om_attack_mode;
typedef enum { OM_OUT_BREAKTHROUGH = 0, OM_OUT_CONTESTED = 1, OM_OUT_REPELLED = 2 } om_outcome;
typedef enum { OM_CAND_ATTACK = 0, OM_CAND_COLONIZE = 1 } om_candidate_kind;

/* ALG-11..ALG-14 per-candidate diagnostics for one faction (S-034, S-035). */
typedef struct om_candidate {
    uint32_t region_idx;
    uint32_t kind;            /* om_candidate_kind */
    double   weakness;        /* factor_1 (tension for schism) */
    double   value;           /* current_value */
    double   position;        /* strategic_position */
    double   attractiveness;
    double   entrenchment;    /* attack candidates only, ALG-13 */
    double   net;             /* attack candidates only, ALG-14 */
    uint32_t viable;          /* attack candidates only */
    uint32_t _pad;
} om_candidate;
uint32_t om_faction_candidates(const om_world *w, int32_t faction_id, om_candidate *out, uint32_t max);

typedef struct om_decision {
    uint64_t tick;
    int32_t  faction_id;
    uint32_t action;          /* om_action */
    uint32_t target_idx;      /* UINT32_MAX if none */
    uint32_t source_idx;      /* UINT32_MAX if none */
    double   commit;
    uint32_t mode;            /* om_attack_mode, attacks only */
    uint32_t _pad;
    double   attack_score;
    double   colonize_score;
    double   effective_confidence;
    double   break_even;
    double   telegraph_preference;   /* ALG-15 pref after adjustments, attacks only */
} om_decision;
uint32_t om_tick_decisions(const om_world *w, om_decision *out, uint32_t max);

typedef struct om_telegraph {
    uint64_t declared_tick;   /* resolves on declared_tick + 3 (R-036-03) */
    int32_t  attacker;
    uint32_t target_idx;
    uint32_t source_idx;
    uint32_t _pad;
    double   commit;
} om_telegraph;
uint32_t om_pending_telegraphs(const om_world *w, om_telegraph *out, uint32_t max);

typedef struct om_attack_result {
    uint64_t tick;
    int32_t  attacker;
    int32_t  defender;        /* -1 if the target was unowned */
    uint32_t target_idx;
    uint32_t mode;            /* om_attack_mode */
    uint32_t outcome;         /* om_outcome */
    uint32_t conquest;        /* 1 if the region changed hands (ALG-22) */
    double   commit;
    double   effective_attack;
    double   effective_defense;
    double   stochastic;      /* the U(0.7,1.3) draw used */
    double   net;
    double   d_military;      /* damage deltas, before conquest extras */
    double   d_economy;
    double   d_tension;
    double   garrison;        /* commit * 0.65 if conquest, else 0 */
    double   budget_spent;
    uint32_t collision;       /* 1 if resolved inside an ALG-23 collision */
    uint32_t _pad;
} om_attack_result;
uint32_t om_tick_attacks(const om_world *w, om_attack_result *out, uint32_t max);

#define OM_MAX_COLLIDERS 8
typedef struct om_collision {
    uint64_t tick;
    uint32_t target_idx;
    uint32_t n_colliders;
    int32_t  faction[OM_MAX_COLLIDERS];
    double   commit[OM_MAX_COLLIDERS];
    double   economy_factor[OM_MAX_COLLIDERS];
    double   strength[OM_MAX_COLLIDERS];
    int32_t  winner;
    uint32_t _pad;
    double   margin;
    double   retention_ceiling;
    double   refund;
    double   loser_tension[OM_MAX_COLLIDERS];  /* ALG-23 tension hit applied to each loser, 0 for the winner */
} om_collision;
uint32_t om_tick_collisions(const om_world *w, om_collision *out, uint32_t max);

typedef struct om_reinforce {
    uint64_t tick;
    int32_t  faction_id;
    uint32_t target_idx;
    double   commit;
    double   headroom;
    double   base;
    double   variance;
    double   d_military;
} om_reinforce;
uint32_t om_tick_reinforces(const om_world *w, om_reinforce *out, uint32_t max);

typedef struct om_colonize_result {
    uint64_t tick;
    int32_t  faction_id;
    uint32_t target_idx;
    double   start_military;  /* 10.0, or 10.0 * U(0.5, 0.70) after a narrow collision */
    double   budget_spent;
} om_colonize_result;
uint32_t om_tick_colonizations(const om_world *w, om_colonize_result *out, uint32_t max);

typedef struct om_friction {
    uint32_t region_idx;
    uint32_t hostile_neighbors;
    double   d_tension;
    double   d_economy;       /* <= 0, after the economy floor */
} om_friction;
uint32_t om_tick_friction(const om_world *w, om_friction *out, uint32_t max);

typedef struct om_admin_roll {
    uint64_t tick;
    int32_t  faction_id;
    uint32_t region_idx;
    double   chance;
    double   draw;
    uint32_t triggered;
    uint32_t _pad;
} om_admin_roll;
uint32_t om_tick_admin_rolls(const om_world *w, om_admin_roll *out, uint32_t max);

/* ---- event queue (shared with E-04) ----
 * E-05 writes two kinds of entries: OM_EVT_CONQUEST_UNREST after a conquest
 * (ALG-22, probability 0.60, delay round(triangular(4, 8, 6))) and
 * OM_EVT_ADMIN_SEPARATIST after a successful admin roll (ALG-29, due next tick,
 * probability 1.0, no condition, chain_length L in [3, 8] from one integer draw). E-04 resolves the queue (ALG-36); until E-04
 * is built the queue is inert and tests read it as written. Template ids for
 * the full authored set are assigned by E-04; these two are fixed here so both
 * epics agree. */
typedef enum {
    OM_EVT_CONQUEST_UNREST  = 100,
    OM_EVT_ADMIN_SEPARATIST = 101
} om_event_template_e05;
typedef struct om_queued_event {
    uint64_t due_tick;
    uint32_t region_idx;
    uint32_t template_id;
    double   probability;
    int32_t  chain_tag;       /* chain_NNNN sequential, E-04 R-027-06 */
    int32_t  source_faction;  /* the faction that queued it, or -1 */
    uint32_t chain_length;    /* admin chains: L in [3, 8]; 0 otherwise */
    uint32_t _pad;
} om_queued_event;
uint32_t om_event_queue(const om_world *w, om_queued_event *out, uint32_t max);

/* ---- positive-control fault injection for E-05 (debug build only) ---- */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_AGENT_READS_LIVE          = 100, /* decisions read post-mutation fields, not the 3a snapshot */
    OM_BUG_TELEGRAPH_AFTER_REINFORCE = 101, /* 3c runs after 3e */
    OM_BUG_SURPRISE_ON_DEFENSE       = 102, /* 0.5 applied to defense, not attack */
    OM_BUG_ENTRENCH_CURRENT_TICK     = 103, /* entrenchment reads the live tick, not the snapshot held-since */
    OM_BUG_COLLISION_MAX_STRENGTH    = 104, /* winner = max strength, no draw */
    OM_BUG_CONQUEST_ON_BAND          = 105, /* conquest on breakthrough band, not post-damage military */
    OM_BUG_GARRISON_BEFORE_DAMAGE    = 106,
    OM_BUG_ADMIN_ROLL_PER_FACTION    = 107, /* one roll per faction, not per region */
    OM_BUG_FRICTION_COUNTS_TRADE     = 108, /* trade-only edges count (Q-041-01 answered: border and both only) */
    OM_BUG_E05_SLOW                  = 109  /* deliberate slowdown for the scale gate */
} om_bug_e05;
#endif

#ifdef __cplusplus
}
#endif

#endif /* OUROBOROS_SIM_H */
