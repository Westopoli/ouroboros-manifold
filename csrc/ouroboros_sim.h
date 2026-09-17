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
    OM_BUG_SLOW              = 5,  /* deliberate slowdown, to prove the speed leg can fail */
    OM_BUG_DRIFT_GATE_IGNORED = 6  /* drift runs even with OM_FEAT_DRIFT off (S-160) */
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
 * Mirror the tick sequence's launch flags (algorithms.md "Tick sequence").
 * om_world_new() switches only DRIFT on by default (S-160); every other
 * switch starts off until its own epic decides its launch default (A4,
 * open). A fixture turns on exactly the steps a test needs isolated: an
 * E-05 test turns on FACTIONS (and FRICTION/ADMIN_REVOLTS as needed) and
 * leaves DRIFT, EVENTS, DIPLOMACY, and TECHNOLOGY off, so it reads exactly
 * what the agents and the resolver did. Switching a feature off skips its
 * step entirely; it never changes what an enabled step computes. */
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

/* ---- damage history (fixture and reader) ----
 * ALG-11's opportunist boost reads the military plus economy a region lost to
 * attack resolutions in the last DAMAGE_HISTORY_WINDOW = 150 ticks. The resolver
 * records losses itself; this fixture records one as if an attack had landed on
 * tick `tick`, so a test can plant exact amounts. A loss counts while
 * now - tick <= 150 and is dropped after. om_region_damage_history returns the
 * current windowed sum as the agent would read it on the next step. */
void   om_region_add_damage(om_world *w, uint32_t idx, double military_loss, double economy_loss, uint64_t tick);
double om_region_damage_history(const om_world *w, uint32_t idx);

/* ---- the world RNG contract (every card that draws follows this exactly) ----
 * One PCG32 stream per world (O'Neill PCG-XSH-RR 64/32, the reference
 * pcg32_random_r): state {uint64 state, uint64 inc}. Seeding from
 * om_world_new(seed) / om_world_set_seed(seed): inc = (seed ^ 0xDA3E39CB94B95BDBULL) << 1 | 1;
 * state = 0; step; state += seed; step. next32() is the reference output.
 * u = uniform in [0, 1) with 53 bits: a = next32() >> 5, b = next32() >> 6,
 * u = (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)  (two 32-bit outputs, a then b).
 * U(lo, hi) = lo + (hi - lo) * u. randint(a, b) inclusive: n = b - a + 1,
 * threshold = (uint32_t)(-n) % n, loop r = next32() until r >= threshold,
 * return a + (r % n). triangular(lo, hi, mode): u = uniform; c = (mode - lo)/(hi - lo);
 * if u > c { u = 1 - u; c = 1 - c; swap(lo, hi); } return lo + (hi - lo) * sqrt(u * c)
 * (IEEE sqrt is correctly rounded on every platform, so it is allowed).
 * round(x) = floor(x + 0.5). Every draw consumes the stream in the order the
 * e2e file's "Draw order" paragraph states; nothing else touches the stream.
 *
 * ---- forced RNG draws (fixture) ----
 * Rules quote exact stochastic draws ("a draw of 1.0", "draw 0.7"). This queues
 * values that the next n uniform draws (u above, so also every U/randint/
 * triangular that consumes one u) return instead of the stream, in order; when
 * the queue empties the stream resumes. A forced randint takes its value as
 * a + floor(u * n). Every
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

/* ---- intent injection (fixture) ----
 * Places an intent into the next om_world_step exactly as if faction_id had
 * decided it in step 3d: an attack (with mode; a telegraphed one enters the
 * pending list and resolves at tick + 3), a colonize, or a reinforce. A faction
 * with an injected intent this tick skips its own 3d decision, so a test
 * controls exactly which intents collide. commit is taken as given (a colonize
 * may carry any commit here, unlike ALG-16's fixed 20). Returns 0 on success,
 * -1 if faction_id is unknown, source_idx is not owned by it, target_idx is out
 * of range, or commit exceeds its budget. Injected intents are consumed by the
 * step and never persist past it. */
int om_intent_inject(om_world *w, int32_t faction_id, om_action action, uint32_t target_idx,
                     uint32_t source_idx, double commit, om_attack_mode mode);


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
    uint32_t cond_kind;       /* om_condition_kind (E-04): checked at resolution, not at spawn */
    uint32_t cond_field;      /* om_field the condition reads; unused when cond_kind is NONE */
    uint32_t exclusion_tag;   /* om_exclusion_tag (E-04) */
    double   cond_value;
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


/* ======================================================================
 * E-04: events and chains (epics/E-04-events-and-chains.md, e2e/E-04.md,
 * algorithms.md ALG-32..ALG-37). Appended 2026-09-14. Tick steps 1 and 2:
 * resolve the due queue, then evaluate fresh triggers on every inhabited
 * region against the tick-start fields, sum each region's deltas, apply once.
 * E-08 rolls the noise offsets at each time jump; here they are a fixture.
 * Faction creation on "creates_faction" events is E-07's; E-04 only marks
 * the region. Queue entries use om_queued_event from the E-05 block.
 * ====================================================================== */

#define OM_MAX_TEMPLATES 64
#define OM_MAX_SPAWNS    2
#define OM_TEMPLATE_NAME 32

typedef enum { OM_TRIG_NONE = 0, OM_TRIG_ABOVE = 1, OM_TRIG_BELOW = 2, OM_TRIG_PROBABILITY = 3 } om_trigger_kind;
typedef enum { OM_COND_NONE = 0, OM_COND_ABOVE = 1, OM_COND_BELOW = 2 } om_condition_kind;
typedef enum {
    OM_EXCL_NONE                 = 0,
    OM_EXCL_MILITARY_RELIEF      = 1,
    OM_EXCL_POLITICAL_RESOLUTION = 2,
    OM_EXCL_REVOLT_OUTCOME       = 3
} om_exclusion_tag;
typedef enum { OM_SRC_TRIGGER = 0, OM_SRC_SPAWN = 1, OM_SRC_EXTERNAL = 2 } om_event_source;

typedef struct om_spawn {
    uint32_t template_id;
    uint32_t delay_min;       /* inclusive, ticks; delay = clamp(round(triangular(min, max, mid)), min, max) */
    uint32_t delay_max;
    uint32_t cond_kind;       /* om_condition_kind */
    uint32_t cond_field;      /* om_field */
    uint32_t _pad;
    double   probability;
    double   cond_value;
} om_spawn;

typedef struct om_event_template {
    uint32_t id;                       /* index in the loaded library; stable for the world's life */
    char     name[OM_TEMPLATE_NAME];   /* exactly the S-030 table name */
    uint32_t trigger_kind;             /* om_trigger_kind; NONE = spawn only */
    uint32_t trigger_field;            /* om_field for ABOVE/BELOW/PROBABILITY */
    double   threshold;                /* ABOVE/BELOW */
    double   prob_base;                /* PROBABILITY: p = base * (field/100)^exponent */
    double   prob_exponent;
    uint32_t cooldown_ticks;           /* PROBABILITY */
    uint32_t n_spawns;
    double   effect[OM_F_COUNT];       /* military, economy, tension, population */
    om_spawn spawns[OM_MAX_SPAWNS];
    uint32_t exclusion_tag;            /* om_exclusion_tag */
    uint32_t creates_faction;          /* 1 for Revolt Entrenched and Admin Breakaway */
    uint32_t admin_chain_step;         /* 0 none; 1 Separatist, 2 Political Crisis, 3 Popular Support, 4 Military Defection, 5 Breakaway */
    uint32_t _pad;
} om_event_template;

/* ---- library ----
 * om_events_load_launch installs the 26-template launch library exactly as the
 * S-030 table (R-030-01's contract test reads it back). om_events_load replaces
 * the library from a caller-supplied array (fixture) and returns non-zero on any
 * rejected template per the epic's Inputs table: an out-of-range field id, an
 * unknown trigger or condition kind, delay_max < delay_min, probability outside
 * [0, 1], a spawn naming a template id >= n. The world starts with no library
 * loaded; with none loaded, tick steps 1 and 2 do nothing. */
void     om_events_load_launch(om_world *w);
int      om_events_load(om_world *w, const om_event_template *templates, uint32_t n);
uint32_t om_event_template_count(const om_world *w);
int      om_event_template_get(const om_world *w, uint32_t id, om_event_template *out); /* 0 on success */
int32_t  om_event_template_by_name(const om_world *w, const char *name);               /* id, or -1 */

/* ---- noise offsets and trigger state ----
 * ALG-32: om_event_roll_noise draws one offset per (region in index order,
 * template with a threshold trigger in id order) uniform in [-10, 10]. E-08
 * calls it at each time jump; tests either call it or pin offsets directly. */
void   om_event_roll_noise(om_world *w);
void   om_event_set_noise(om_world *w, uint32_t region_idx, uint32_t template_id, double offset);
double om_event_noise(const om_world *w, uint32_t region_idx, uint32_t template_id);
int     om_event_breached(const om_world *w, uint32_t region_idx, uint32_t template_id);  /* the stored 'was' flag */
int64_t om_event_last_fired(const om_world *w, uint32_t region_idx, uint32_t template_id); /* -1 if never (cooldown) */
int32_t om_chain_counter(const om_world *w);   /* next chain_NNNN; saved with the world */
uint32_t om_region_faction_creation_pending(const om_world *w, uint32_t region_idx); /* template id + 1 that marked it this tick, 0 if none */

/* ---- external spawns (E-05 calls these; tests may too) ---- */
int om_event_queue_external(om_world *w, uint32_t region_idx, uint32_t template_id,
                            uint64_t due_tick, double probability, int32_t source_faction,
                            uint32_t chain_length);
/* Returns the chain tag assigned, or -1 and queues nothing when: template_id is
 * not loaded, region_idx is out of range or empty-tier, due_tick <= the current
 * tick, probability is outside [0, 1], or the template is an admin chain step
 * and chain_length is outside [3, 8]. A spawn that would exceed the queue
 * capacity (2,000 entries) is dropped and recorded as a pruned record with
 * cond_kind OM_COND_NONE (the overflow marker). */

/* ---- tick-log readers for steps 1 and 2 (last step only) ---- */
typedef struct om_fired_event {
    uint64_t tick;
    uint32_t region_idx;
    uint32_t template_id;
    int32_t  chain_tag;
    uint32_t source;          /* om_event_source */
    double   delta[OM_F_COUNT];   /* this event's own deltas before the per-region sum and clamp */
    double   draw;            /* the probability draw used for a spawn, -1.0 for a trigger */
    uint32_t creates_faction;
    uint32_t n_spawned;       /* queue entries this firing added */
} om_fired_event;
uint32_t om_tick_events(const om_world *w, om_fired_event *out, uint32_t max);

typedef struct om_pruned_event {
    uint64_t tick;
    uint32_t region_idx;
    uint32_t template_id;
    int32_t  chain_tag;
    uint32_t cond_kind;
    uint32_t cond_field;
    uint32_t _pad;
    double   cond_value;
    double   field_value;     /* the field as read at resolution */
} om_pruned_event;
uint32_t om_tick_pruned(const om_world *w, om_pruned_event *out, uint32_t max);

typedef struct om_delayed_event {
    uint64_t tick;
    uint32_t region_idx;
    uint32_t template_id;     /* the loser re-queued */
    int32_t  chain_tag;
    uint32_t exclusion_tag;
    uint32_t kept_template_id;
    uint32_t _pad;
    uint64_t new_due;         /* tick + randint(1, 2) */
} om_delayed_event;
uint32_t om_tick_delayed(const om_world *w, om_delayed_event *out, uint32_t max);

/* Per-region applied sum for the last step: the once-applied event delta per field
 * after floors and ceiling (R-026-06, R-028-01). Zero for regions with no event. */
int om_region_event_delta(const om_world *w, uint32_t region_idx, double out[OM_F_COUNT]);

/* ---- positive-control fault injection for E-04 (debug build only) ---- */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_FIRES_EVERY_TICK        = 200, /* fires while past the threshold, not on the crossing */
    OM_BUG_NOISE_REROLLED          = 201, /* offsets re-rolled every tick */
    OM_BUG_NO_GRACE_PERIOD         = 202,
    OM_BUG_COND_AT_SPAWN           = 203, /* spawn condition checked at spawn time */
    OM_BUG_SEQUENTIAL_DELTAS       = 204, /* same-tick deltas applied one after another */
    OM_BUG_EXCLUSION_CANCELS       = 205, /* loser cancelled instead of delayed */
    OM_BUG_DRAW_BEFORE_CONDITION   = 206, /* probability draw consumed before the condition check */
    OM_BUG_CHAIN_COUNTER_UNSAVED   = 207,
    OM_BUG_TRIGGERS_READ_LIVE      = 208, /* fresh triggers read another region's post-event field */
    OM_BUG_E04_SLOW                = 209
} om_bug_e04;
#endif


/* ======================================================================
 * E-03: world generation and topology (epics/E-03-world-generation.md,
 * e2e/E-03.md, algorithms.md ALG-30..ALG-31). Appended 2026-09-15. Nothing
 * above this line changes. This block turns om_world_generate() from the E-02
 * placeholder into a specified, seed-deterministic generator: it fixes the
 * region count, rolls each of the 15 factions a template, places and fields
 * their regions, lays corridors, attaches empties, adds extra edges, and types
 * every edge. Every draw follows the world RNG contract (the PCG32 block above)
 * in the e2e file's documented order (R-022-04, R-021-10). The generator owns
 * faction, region, ownership, and edge state; the om_faction_set* / om_region_set*
 * fixture setters remain for isolation tests of later epics.
 * ====================================================================== */

/* Faction template (R-021-05). OM_TMPL_NONE is the player "no preference"
 * sentinel for om_gen_set_player_preference; it is never a rolled result. */
typedef enum {
    OM_TMPL_ISOLATED    = 0,   /* 1 home + 2 frontiers, both adjacent to the home (3 regions) */
    OM_TMPL_TWIN_COLONY = 1,   /* 2 adjacent homes, each + 1 or 2 frontiers (4-6 regions) */
    OM_TMPL_ARCHIPELAGO = 2,   /* 1 home + 3 frontiers, >=1 reached only through a frontier chain (4 regions) */
    OM_TMPL_NONE        = 3
} om_template;

/* ---- generation config (set before om_world_generate; each has a launch default) ----
 * om_world_new(n_regions, seed): n_regions > 0 pins the count (the E-02 path);
 * pass n_regions == 0 to draw it uniformly from [region_min, region_max] at
 * generation (R-021-01). A pinned or drawn count below the minimum feasible
 * total (sum of every rolled template's size + one corridor empty per faction)
 * makes generation fail its feasibility check (om_world_generated() == 0). */
void om_gen_set_region_range(om_world *w, uint32_t lo, uint32_t hi);   /* default [60, 110] (Q-021-05) */
void om_gen_set_faction_count(om_world *w, uint32_t n);                /* default 15 (R-021-01) */
void om_gen_set_extra_edge_ratio(om_world *w, double ratio);          /* default 0.12 (R-021-08) */
/* Player faction (id 0) template preference (R-021-04): raises that template's
 * weight in the player roll only, never locks it, and consumes no RNG that would
 * shift any NPC roll. OM_TMPL_NONE (default) = equal weight, same as an NPC. */
void om_gen_set_player_preference(om_world *w, om_template pref);
/* Player-preference weight (Q-021-06, configurable): the probability the player's
 * own template roll gives the preferred template when a preference is set; the
 * other two split the remainder equally. Default WORLD_PLAYER_PREFERENCE_WEIGHT
 * = 0.50 (so 0.50 / 0.25 / 0.25). No effect without a preference; never touches an
 * NPC roll. In [0, 1]; a value < 1/3 is accepted (a preference may de-weight). */
void om_gen_set_preference_weight(om_world *w, double preferred);
/* Fixture isolation switch for the extra-edge step (R-021-08). Extra edges cannot
 * be turned off by ratio — the count is max(1, floor(ratio·N)), a floor of 1 — so
 * this boolean skips the whole step for isolation tests of placement (R-021-05),
 * empty attachment (R-021-07), and edge typing, exactly like a feature switch: it
 * removes the step, it never changes what the step computes. Default on (1). A
 * test of R-021-08 itself leaves it on. */
void om_gen_set_extra_edges_enabled(om_world *w, int on);
/* Per-archetype home military/economy ranges (R-022-05). Defaults are the epic's
 * numbers (Conqueror mil 50-65/eco 40-55; Fortifier 40-50/50-65; Opportunist
 * 45-55/45-55). archetype in {CONQUEROR, FORTIFIER, OPPORTUNIST}; PLAYER homes and
 * every faction's tension/population keep R-022-01/R-022-02's general ranges, and
 * frontier regions are archetype-independent regardless of this call. */
void om_gen_set_home_range(om_world *w, om_archetype archetype,
                           double mil_lo, double mil_hi, double eco_lo, double eco_hi);

/* ---- generation result and report (valid after om_world_generate) ----
 * om_world_generated returns 1 when the last om_world_generate succeeded, 0 when
 * it failed the feasibility check (the world is then left empty). The report
 * accessors below back the T1 generation trace: seed, region count, edge count,
 * and each faction's rolled template. Adjacency, edge types, tiers, owners, and
 * fields are read with om_region_neighbors / om_region_edge / om_region_tier /
 * om_region_owner / om_region_field (declared above). */
int         om_world_generated(const om_world *w);
uint64_t    om_world_seed(const om_world *w);
uint32_t    om_world_edge_count(const om_world *w);
om_template om_faction_template(const om_world *w, int32_t faction_id);   /* the rolled template */

/* Enumerate a region's neighbors (undirected). Copies up to max neighbor ids into
 * out[] in ascending id order and returns the total neighbor count (which may
 * exceed max; call again with a larger buffer). Pair each id with om_region_edge()
 * for its type. This is the O(degree) accessor connectivity and adjacency tests
 * use instead of an O(N^2) om_region_edge sweep. */
uint32_t    om_region_neighbors(const om_world *w, uint32_t idx, uint32_t *out, uint32_t max);

/* ---- positive-control fault injection for E-03 (debug build only) ----
 * One bug per E-03 e2e "QA watch-for", so each generation detector ships with a
 * planted control. Injected before om_world_generate; the generator then
 * reproduces exactly that flaw. */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_RNG_ORDER_SWAPPED     = 300, /* draws fields out of the R-022-04 order: seed no longer reproduces */
    OM_BUG_EXTRA_EDGE_TO_PLAYER  = 301, /* R-025-04 rejection skipped: an extra edge may touch a player region */
    OM_BUG_HOME_TO_HOME_EDGE     = 302, /* R-021-08 "never between two homes" skipped */
    OM_BUG_CORRIDOR_SKIPPED      = 303, /* corridor chain not laid: a faction can be unreachable */
    OM_BUG_EMPTY_EDGE_BOTH       = 304, /* an edge touching an empty region typed both/trade, not border */
    OM_BUG_FRONTIER_FROM_HOME    = 305, /* a frontier's fields rolled from the home/archetype range */
    OM_BUG_RESEED_PER_REGION     = 306, /* RNG reseeded per region: factions share phase offsets */
    OM_BUG_TWIN_SECOND_HOME_LOW  = 307, /* Twin Colony's second home rolled from the frontier range */
    OM_BUG_ARCHIPELAGO_DENSE     = 308, /* all Archipelago frontiers wired to the home (no sparse frontier) */
    OM_BUG_BUDGET_DRIFT          = 309, /* a late template roll changes the already-fixed region budget */
    OM_BUG_ARCHETYPE_RANGE_MISS  = 310, /* a home's mil/eco rolled outside its R-022-05 archetype range */
    OM_BUG_E03_SLOW              = 311  /* deliberate O(N^2) slowdown for the 110-region scale gate */
} om_bug_e03;
#endif

#ifdef __cplusplus
}
#endif

#endif /* OUROBOROS_SIM_H */
