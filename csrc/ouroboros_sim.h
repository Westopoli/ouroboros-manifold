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

/* ABI version reported by om_abi_version(). Bump when signatures change. */
#define OM_ABI_VERSION 8

/* Number of layers: engine layers 0 to OM_LAYER_COUNT - 1 (bible layer n is engine layer n - 1). */
#define OM_LAYER_COUNT 5

/* Largest canvas side om_map_set_canvas accepts; equals OM_CANVAS_SIZE_RANGES_LARGE_HI in om_constants.h. */
#define OM_MAP_MAX_CANVAS 28000.0

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
 * breaking change to a signature or struct layout. Bumped to 2 at freeze/F2
 * (OM_FEAT_TACTICAL, the E-06/E-07/E-11 tick-order bug ids, and the three
 * core symbols below are new since version 1). Bumped to 3 (HDR3): added
 * om_player_faction(), OM_MAX_UNITS, and faction_id params to om_player_can_see,
 * om_player_can_see_friendly, om_player_faction_collapsed,
 * om_mission_get_player_parity, om_mission_get_player_units,
 * om_mission_set_player_units, om_mission_set_player_held_structures_count,
 * om_gen_set_player_preference. Bumped to 4 (PP-contract): added om_tactical_get_param/set_param
 * (om_tac_param), om_map_set_canvas, om_map_block_rect, om_command_set_layer, om_unit_transition_progress,
 * om_unit_get_target_layer, om_roster_set_reach, om_unit_profile_reach, om_command_set_emission
 * (om_emission), om_unit_get_emission, om_command_ping, om_ping_alert_count/get (om_ping_alert),
 * om_unit_get_group_id, om_unit_get_leash_anchor, om_unit_get_engaged. */
uint32_t om_abi_version(void);
/* T1's pipe hello checks the caller's struct sizes against the library's own
 * before trusting anything else over the wire (audit 2026-09-21, A F-8-5):
 * returns 1 when every size matches this build's sizeof, 0 otherwise. */
int      om_abi_layout_check(uint32_t sizeof_trace_row, uint32_t sizeof_drift_row,
                             uint32_t sizeof_collision);

/* OM_MAX_UNITS: hard cap on simultaneous tactical units (E-11 10k-unit scale
 * requirement + headroom, ALG-32-01). Single definition for all modules. */
#define OM_MAX_UNITS 10100

/* om_player_faction: returns the faction id of the first in-use faction whose
 * archetype is OM_ARCH_PLAYER, or -1 when no such faction is configured.
 * Used by callers that need the world's authoritative player id rather than
 * a hardcoded constant. */
int32_t om_player_faction(const om_world *w);

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
/* Test hook (K-e5, ABI 7; docs/northstar/spec_factory/signatures.toml, scripts/specfactory/reach_allowlist.toml): replaces the
 * height grid of a generated ground mission with `cm` (centimetres, row-major, cells_w * cells_h values) so a test can set a flat,
 * sea or ridge terrain. Returns 0 and changes nothing when (cells_w, cells_h) differ from the terrain's cell dimensions or the
 * world has no terrain. Otherwise it recomputes the five band floors as generation does (lo and hi over the cells above the dry
 * level; when no cell is above it, lo and hi are the minimum and maximum of all cells), re-bands the cells, runs
 * om_terrain_apply_ground (walkable, slopes, walk masks and the mapgen blocked bits are rewritten, so blocked rects laid after
 * generation are erased; obstacle discs and cover rows survive; the move epoch is bumped) and rebuilds the density inputs; returns 1.
 * The generator's dry-level rule is not enforced on `cm`: flat test terrains use heights above 6000 cm (the dry test is strict). */
int om_terrain_set_heights(om_world *w, const int32_t *cm, uint32_t cells_w, uint32_t cells_h);

/* ---- tick (7-step sequence, tick auto-increments from 1) ---- */
uint64_t om_world_step(om_world *w);                 /* advance one tick, return new tick */
uint64_t om_world_run(om_world *w, uint64_t n_ticks); /* bulk path the scale gate times */
/* Fixture setter (E-06/E-10): moves the tick counter directly, with no other
 * side effect. The next om_world_step() then returns tick + 1. */
void     om_world_set_tick(om_world *w, uint64_t tick);

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
/* Same value as om_world_checksum (T1's snapshot/delta and E-12/E-13's own
 * checksum reads all name this symbol instead; kept as a second entry point
 * rather than a rename so om_world_checksum's existing callers are untouched). */
uint64_t om_world_get_state_checksum(const om_world *w);

/* ---- deterministic transcendental ---- */
/* The one platform-independent sine used by the ALG-01 oscillator. Compiled
 * identically on every platform; the sim never calls libm sin(). */
double om_sin(double x);
/* Deterministic pow(base, exp) for base >= 0 (ALG-03's headroom^0.3 term);
 * base <= 0 returns 0.0, exp == 0 returns 1.0. Compiled identically on
 * every platform; the sim never calls libm pow(). */
double om_pow(double base, double exp);

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
    OM_BUG_DRIFT_GATE_IGNORED = 6, /* drift runs even with OM_FEAT_DRIFT off (S-160) */
    OM_BUG_LIBM_POW          = 7, /* om_pow's deterministic polynomial swapped for libm pow(),
                                    * breaking the cross-platform determinism contract */
    OM_BUG_RNG_UNSEEDED      = 8  /* the world RNG stream is never derived from the seed: every
                                    * seed draws the same values (the push-day M1 finding) */
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
    OM_FEAT_LIFECYCLE     = 7,  /* tick step 6 (E-07) */
    OM_FEAT_TACTICAL      = 8   /* tactical orchestrator (E-11): with a tactical map
                                 * loaded, runs after every strategic step (decision 3,
                                 * docs/northstar/plans/briefs/2026-09-22-two-day-push.md) */
} om_feature;
void om_world_set_feature(om_world *w, om_feature f, int on);

/* Lockstep command verbs (OMNetCommand.verb; lockstep spec 2026-10-05). */
typedef enum {
    OM_NET_VERB_MOVE             = 0,
    OM_NET_VERB_ATTACK_MOVE      = 1,
    OM_NET_VERB_ATTACK_TARGET    = 2,
    OM_NET_VERB_ACTIVATE_ABILITY = 3,
    OM_NET_VERB_SET_LAYER        = 4,
    OM_NET_VERB_SET_EMISSION     = 5,
    OM_NET_VERB_PING             = 6,
    OM_NET_VERB_GUARD            = 7,
    OM_NET_VERB_ASSIGN_COMMANDER = 8
} om_net_verb;
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
    OM_BUG_E05_SLOW                  = 109, /* deliberate slowdown for the scale gate */
    OM_BUG_SAME_TICK_REDECLARE       = 110, /* 3d re-declares against a target this faction
                                              * already resolved an attack against this tick */
    OM_BUG_INJECT_IGNORED            = 111, /* 3d wipes an om_intent_inject entry and
                                              * recomputes the faction's decision naturally */
    OM_BUG_COLLISION_AFTER_RESOLVE   = 112  /* the collision step (3f-minus, S-039) runs
                                              * after om_step_resolve instead of before it,
                                              * so 3f double-resolves the colliding intents */
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
int32_t om_chain_counter(const om_world *w);   /* last-assigned chain tag (tags start at 1), 0 if none yet; saved with the world */
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

/* ---- module-owned named templates (F2h, ALG-27b: Knowledge Lost) ----
 * The 26-template launch library (R-030-01) is fixed; a module that needs its
 * own named event outside that table (e.g. E-06's Knowledge Lost, R-045-07)
 * registers one here instead of editing the launch library. Returns a
 * template id >= om_event_template_count(w) (the launch library size) that
 * om_event_queue_external accepts and that om_event_template_get and
 * om_event_template_name report on, same as any launch-library id. The
 * registered template has no trigger (R-030-02: it never starts a chain on
 * its own -- it fires only as a spawn, exactly like any other trigger-less
 * template), no effects, exclusion tag OM_EXCL_NONE, and the given
 * significance tier. Registering the same name twice returns the same id
 * (idempotent by name). Ids are assigned in registration order, so the draw
 * order and the state checksum stay deterministic across a run. Registered
 * templates are saved and restored with the world. om_event_template_count
 * -- the accessor the S-030 contract test (test_R_030_01) reads -- excludes
 * registrations: it always reports the launch-library size, never grows when
 * a template is registered. */
int32_t om_event_register_external(om_world *w, const char *name, int32_t significance_tier);

/* No existing accessor maps a template id back to its name (only
 * om_event_template_by_name, name -> id, and om_event_template_get, id ->
 * the full struct). Added so a registered external template's name can be
 * read without pulling the whole struct. NULL if id is out of range. */
const char *om_event_template_name(const om_world *w, uint32_t template_id);

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
    OM_BUG_E04_SLOW                = 209,
    OM_BUG_EVENTS_AFTER_FACTIONS   = 210  /* tick steps 1-2 (events) run after step 3 (factions)
                                            * instead of before it */
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
void om_gen_set_region_range(om_world *w, uint32_t lo, uint32_t hi);   /* default [250, 400] (R-021-01, ALG-31) */
void om_gen_set_faction_count(om_world *w, uint32_t n);                /* default 15 (R-021-01) */
void om_gen_set_extra_edge_ratio(om_world *w, double ratio);          /* default 0.12 (R-021-08) */
/* Player faction (id 0) template preference (R-021-04): raises that template's
 * weight in the player roll only, never locks it, and consumes no RNG that would
 * shift any NPC roll. OM_TMPL_NONE (default) = equal weight, same as an NPC. */
void om_gen_set_player_preference(om_world *w, int32_t faction_id, om_template pref);
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
    OM_BUG_E03_SLOW              = 311, /* deliberate O(N^2) slowdown for the 110-region scale gate */
    OM_BUG_STARTING_RATIO_SWAPPED = 312 /* ALG-30 general formula: economy uses STARTING_MIL_RATIO and military uses STARTING_ECO_RATIO */
} om_bug_e03;
#endif


/* ======================================================================
 * E-06: diplomacy and technology (epics/E-06-diplomacy-and-technology.md).
 * Appended 2026-09-22 (freeze/F2): tick-order wiring only -- om_step_diplomacy
 * and om_step_technology are internal hooks (csrc/om_internal.h) that run at
 * tick steps 4.25 and 4.5 (docs/bible/algorithms.md:25-26); the epic's own
 * symbols (stance, tech growth) land with card B5. Nothing above this line
 * changes.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_DIPLOMACY_AFTER_DRIFT   = 400, /* step 4.25 runs after step 5 (drift) instead of before it */
    OM_BUG_TECHNOLOGY_BEFORE_ADMIN = 401, /* step 4.5 runs before step 4.1 (admin revolts) instead of after it */
    OM_BUG_TECH_GROWTH_TERMS_SWAPPED = 402 /* ALG-27 om_tech_step: avg_e and avg_p swapped between the growth ratio and the TECH_POPULATION_FLOOR clamp */
} om_bug_e06;
#endif


/* ======================================================================
 * E-07: civilizational lifecycle (epics/E-07-civilizational-lifecycle.md).
 * Appended 2026-09-22 (freeze/F2): tick-order wiring only -- om_step_lifecycle
 * is an internal hook (csrc/om_internal.h) that runs at tick step 6, after
 * drift (docs/bible/algorithms.md:28, "Zombie faction cleanup"); the epic's
 * own symbols land with card B6. Nothing above this line changes.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_LIFECYCLE_BEFORE_DRIFT = 500, /* step 6 runs before step 5 (drift) instead of after it */
    OM_BUG_ZOMBIE_PASS1_GE_NOT_GT = 501 /* ALG-42 pass 1 removes a zero-region breakaway only when creation tick is > 5 ticks ago, not >= 5 */
} om_bug_e07;
#endif


/* ======================================================================
 * E-11: units and combat (epics/E-11-units-and-combat.md). Appended
 * 2026-09-22 (freeze/F2): the tactical orchestrator's wiring only --
 * om_tactical_step is the real orchestrator in csrc/unit.c; the epic's own
 * symbols land with card B10. Nothing above this line changes.
 * ====================================================================== */
/* The tactical orchestrator (decision 3, two-day-push brief): with
 * OM_FEAT_TACTICAL on, om_world_step calls this once, after every strategic
 * step, and ignores the return (mirrors the om_world_step pattern; a real
 * tick value backs it once B10 lands). */
uint64_t om_tactical_step(om_world *w);

#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_TACTICAL_BEFORE_STRATEGIC = 900, /* tactical runs before the strategic steps instead of after them */
    OM_BUG_BRACE_REDUCTION_WRONG_CONSTANT = 901 /* ALG-60 om_unit_damage_reduction: Brace reduction (0.50) implemented as Fortify's 0.20 */
} om_bug_e11;
#endif

/* ======================================================================
 * E-08: generational (epics/E-08-generational-play.md). Two-day-push brief
 * decision 6: 600s reserved. F5 window control only; the epic's own symbols
 * land with card B7.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_TIME_JUMP_CLAMP_SKIPPED = 600 /* ALG-45 om_time_jump_choose_length returns the raw requested length, skipping the [20, 100] clamp */
} om_bug_e08;
#endif

/* ======================================================================
 * E-09: chronicle (epics/E-09-chronicle.md). Two-day-push brief decision 6:
 * 700s reserved. F5 window control only; the epic's own symbols land with
 * card B8.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_SIGNIFICANCE_CAP_SKIPPED = 700 /* ALG-50 om_chronicle_score_base skips the SIGNIFICANCE_DELTA_CAP = 3.0 clamp on the delta term */
} om_bug_e09;
#endif

/* ======================================================================
 * E-10: missions (epics/E-10-missions.md). Two-day-push brief decision 6:
 * 800s reserved. F5 window control only; the epic's own symbols land with
 * card B9.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_URGENCY_DEFICIT_DIVISOR_WRONG = 800 /* ALG-55 om_mission_compute_urgency divides the three-term deficit sum by 200 instead of 300 */
} om_bug_e10;
#endif

/* ======================================================================
 * E-12: fog and sensors (epics/E-12-fog-and-sensors.md). Two-day-push brief
 * decision 6: 1000s reserved. F5 window control only; the epic's own
 * symbols land with card B11.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_INTERFERENCE_IGNORES_INTENSITY = 1000 /* ALG-65 om_zone_sample_interference returns 1.0 inside any zone instead of the zone's own configured intensity */
} om_bug_e12;
#endif

/* ======================================================================
 * E-13: movement and command (epics/E-13-movement-and-command.md). Two-day-
 * push brief decision 6: 1100s reserved. OM_BUG_MOVE_RUBBERBAND = 1100 is
 * already referenced by tests/qa/t1/test_rts_detectors.py's own local enum
 * (Q2); mirrored here by name and id per that file's own comment ("F5 moves
 * it into conftest"). F5 window control only; the epic's own symbols land
 * with card B12.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_MOVE_RUBBERBAND = 1100, /* a scripted move overshoots and corrects every tick instead of arriving directly (Q2 rts_detectors "rubberband") */
    OM_BUG_NAVMESH_CELL_SIZE_WRONG_CONSTANT = 1101 /* ALG-67 om_navmesh_get_cell_size returns NAVMESH_OBSTACLE_THRESHOLD (0.7) scaled onto the cell size (70.0) instead of NAVMESH_CELL_SIZE (100.0) */
} om_bug_e13;
#endif

/* ======================================================================
 * E-14: enemy macro behavior (epics/E-14-enemy-macro-behavior.md). Two-day-
 * push brief decision 6: 1200s reserved for this module. No id assigned by
 * F5: the one concrete number ALG-74 states (SCRIPT_EVAL_INTERVAL_TICKS =
 * 40) is exposed only by om_macro_evaluation_interval_ticks(void), which
 * takes no om_world*, so no per-world om_debug_inject could ever gate it --
 * a control built on it could not fail on any build, correct or buggy
 * (CLAUDE.md). The only om_world*-taking candidates (om_macro_get_threshold_noise
 * / om_macro_get_timer_noise) need a trigger point and a p1 indexing scheme
 * signatures.toml does not resolve; not guessed. See
 * docs/northstar/proving_ground/evidence/push_2026-09-22/f5_controls.md.
 * ====================================================================== */

/* ======================================================================
 * E-15: reinforcement structures (epics/E-15-reinforcement-structures.md).
 * Two-day-push brief decision 6: 1300s reserved. F5 window control only;
 * the epic's own symbols land with card B14.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_STRUCTURE_MAX_HP_WRONG_CONSTANT = 1300 /* ALG-75 om_structure_get_hud_data's max_hp field reads REINFORCEMENT_CAPTURE_RADIUS (300.0) instead of REINFORCEMENT_STRUCTURE_HP (3000.0); the pure om_structure_get_base_max_hp() getter takes no om_world* and cannot host a per-world fault */
} om_bug_e15;
#endif

/* ======================================================================
 * save.c (S-111 saving, epics/E-16-client-camera-hud-and-world-view.md).
 * Two-day-push brief decision 6: "save 1600s" reserved (no epic number of
 * its own). OM_BUG_SAVE_SKIPS_RNG_STATE = 1600 is already referenced by
 * tests/csim/test_E16_S111_saving.py's own local constant, mirrored here by
 * name and id per that file's own comment ("F5 moves this into conftest's
 * OMBug"). F5 window control only; the epic's own symbols land with card T2c.
 * ====================================================================== */
#ifdef OM_DEBUG_INJECT
typedef enum {
    OM_BUG_SAVE_SKIPS_RNG_STATE = 1600, /* save/load skips writing or restoring the PCG32 stream (test_E16_S111_saving.py's own control) */
    OM_BUG_SAVE_SKIPS_TICK = 1601 /* om_load_state_read restores everything but the tick counter, so a loaded world resumes stepping from tick 0 */
} om_bug_save;

/* VG K-d2 (lane D): debug-inject ids for the space field, passed to om_debug_inject before om_space_field_generate_nodes. */
typedef enum {
    OM_BUG_SPACE_NO_CARVE = 1700 /* space no-carve plant: the fill-and-carve join step is skipped (mockup QaPlants "space-no-carve"); the carve step reads w->inject */
} om_bug_space;
#endif

/* A53 (R-069-07): one clickable name inside a chronicle entry's text. start and
 * len are Unicode code point offsets into the entry text exactly as sent (not
 * byte offsets: the library text holds multi-byte characters such as the em
 * dash). kind is an OM_CHRON_MENTION_* value; id is the faction id or region
 * index the name stands for. (Struct om_chronicle_mention is in the generated
 * structs block below.) */
#define OM_CHRON_MENTION_FACTION 0
#define OM_CHRON_MENTION_REGION 1

/* PP-contract: tunable tactical settings, read and written with om_tactical_get_param and
 * om_tactical_set_param. Members are only ever appended before OM_TP__COUNT. Defaults and valid
 * ranges: docs/northstar/plans/push/pp_contract.md section 4. */
typedef enum {
    OM_TP_PURSUE_BY_STEERING = 0,
    OM_TP_ROUTE_AROUND_TERRAIN,
    OM_TP_LEASH_BEFORE_DAMAGE,
    OM_TP_TARGET_POLICY,
    OM_TP_TARGET_BY_SIGHT,
    OM_TP_ROUTE_ACROSS_LAYERS,
    OM_TP_ATTACK_MOVE_LEASH,
    OM_TP_RETURN_FIRE_FLEE_DIST,
    OM_TP_UNIT_COLLISION_RADIUS,
    OM_TP_VANTAGE_MULT,
    OM_TP_AOE_DAMAGE_CAP,
    OM_TP_TARGETING_COHORTS,
    OM_TP_CATMULT_LINE_LINE,
    OM_TP_CATMULT_LINE_SIEGE,
    OM_TP_CATMULT_LINE_STRIKE,
    OM_TP_CATMULT_SIEGE_LINE,
    OM_TP_CATMULT_SIEGE_SIEGE,
    OM_TP_CATMULT_SIEGE_STRIKE,
    OM_TP_CATMULT_STRIKE_LINE,
    OM_TP_CATMULT_STRIKE_SIEGE,
    OM_TP_CATMULT_STRIKE_STRIKE,
    OM_TP_EMIT_SIGHT_MULT,
    OM_TP_EMIT_SEEN_MULT,
    OM_TP_PING_RADIUS,
    OM_TP_PING_REVEAL_TICKS,
    OM_TP_PING_COOLDOWN_TICKS,
    OM_TP_PING_REACH,
    OM_TP_VISION_UP_1,
    OM_TP_VISION_UP_2,
    OM_TP_VISION_UP_3,
    OM_TP_VISION_UP_4,
    OM_TP_VISION_DOWN_1,
    OM_TP_VISION_DOWN_2,
    OM_TP_VISION_DOWN_3,
    OM_TP_VISION_DOWN_4,
    OM_TP_RANGE_UP_1,
    OM_TP_RANGE_UP_2,
    OM_TP_RANGE_UP_3,
    OM_TP_RANGE_UP_4,
    OM_TP_RANGE_DOWN_1,
    OM_TP_RANGE_DOWN_2,
    OM_TP_RANGE_DOWN_3,
    OM_TP_RANGE_DOWN_4,
    OM_TP_DAMAGE_UP_1,
    OM_TP_DAMAGE_UP_2,
    OM_TP_DAMAGE_UP_3,
    OM_TP_DAMAGE_UP_4,
    OM_TP_DAMAGE_DOWN_1,
    OM_TP_DAMAGE_DOWN_2,
    OM_TP_DAMAGE_DOWN_3,
    OM_TP_DAMAGE_DOWN_4,
    OM_TP_AREA_UP_1,
    OM_TP_AREA_UP_2,
    OM_TP_AREA_UP_3,
    OM_TP_AREA_UP_4,
    OM_TP_AREA_DOWN_1,
    OM_TP_AREA_DOWN_2,
    OM_TP_AREA_DOWN_3,
    OM_TP_AREA_DOWN_4,
    OM_TP_TARGET_POLICY_FACTION_1,
    OM_TP_PING_ALERT,
    OM_TP_TERRAIN_STEEP_DEG,
    OM_TP_SLOPE_UP_DIV,
    OM_TP_SLOPE_DOWN_MULT,
    OM_TP_SIGHT_EYE_HEIGHT,
    OM_TP_GROUND_FLYER_SEEN_MULT,
    OM_TP_FIRING_ARC_DEG,
    OM_TP__COUNT
} om_tac_param;

/* LAB-REV2 E0 (R-082-06 draft): per-type cone area attack, replacing the disc when range > 0. range 0 clears the cone.
 * half_angle_deg is in [1, 180], share in [0, 10], range >= 0. Returns 0 ok, -1 unknown type, -2 refused value.
 * Stub: returns -1 until LAB-REV2-E2 writes the body. */
int om_roster_set_cone(om_world *w, int unit_type, double range, double half_angle_deg, double share);

/* LAB-REV2 E0 (R-100 draft): could the attacker fire at the target this tick if ready. -1 for an unknown id, a dead
 * unit, the same or a neutral faction, attacker == target, or a non-combat attacker; else the first failing reason:
 * 1 out of reach, 2 not seen by the side, 3 out of range at this offset, 4 outside the arc (arc below 360 only),
 * 5 line blocked; 0 when every gate passes. Ignores cooldown, backswing, the cohort slot and the order kind.
 * Stub: returns -1 until LAB-REV2-E2 writes the body. */
int om_combat_can_engage(const om_world *w, uint32_t attacker, uint32_t target);

/* PP-contract: a unit's active-emission mode (om_command_set_emission). */
typedef enum { OM_EMIT_SILENT = 0, OM_EMIT_ACTIVE = 1 } om_emission;

/* Terrain stage 2 (spec 2026-10-06): how a unit type moves (om_roster_set_movement_kind). */
typedef enum { OM_MOVE_FLYING = 0, OM_MOVE_WALKING = 1, OM_MOVE_SWIMMING = 2 } om_movement_kind;

/* VG K-e: visible-game economy fields (docs/architecture.md "Visible-game economy fields"). */
typedef struct om_lot {
    uint32_t id;
    double x, y;
    int32_t stage;
    int32_t building;
    int32_t owner;
} om_lot;
typedef struct om_strongpoint {
    uint32_t id;
    double x, y;
    int32_t owner;
    int32_t state;
} om_strongpoint;
typedef struct om_wave {
    uint32_t tick;
    int32_t kind;
    double x, y;
} om_wave;
/* VG-D8 R-246-07: the most clearing nodes om_space_field_generate_nodes takes (two faction anchors, the objective, extras). */
#define OM_SPACE_FIELD_MAX_NODES 8
#define OM_SPACE_FIELD_MIN_NODES 3 /* the two faction anchors and the objective; fewer takes the old diagonal nodes */

/* ---- generated from signatures.toml: strongpoint.c ---- */
uint32_t om_strongpoint_count(const om_world *w);
int om_strongpoint_get_at(const om_world *w, uint32_t i, om_strongpoint *out);
/* ---- end generated: strongpoint.c ---- */
/* ---- generated from signatures.toml: structs ---- */
typedef struct om_ability_event {
    uint64_t tick;
    uint32_t unit_id;
    int32_t ability_id;
    double target_x;
    double target_y;
    uint32_t duration;
    uint32_t telegraph_ticks;
    uint32_t cue_id;
    double radius;
} om_ability_event;

typedef struct om_absorption_record {
    uint64_t tick;
    int32_t absorbed_faction;
    int32_t absorbing_faction;
    uint32_t region_idx;
} om_absorption_record;

typedef struct om_archetype_metadata {
    uint32_t id;
    uint32_t canvas_category;
    uint32_t primary_objective;
    uint32_t transfer_on_total;
    uint32_t transfer_on_strong;
    uint32_t transfer_on_partial;
} om_archetype_metadata;

typedef struct om_briefing {
    char situation_text[1024];
    char objective_text[1024];
    char assets_text[1024];
    uint32_t has_situation;
    uint32_t has_objective;
    uint32_t has_assets;
} om_briefing;

typedef struct om_character_record {
    uint32_t id;
    char name[32];
    int32_t faction;
    uint32_t region;
    uint32_t rank;
    uint64_t birth_tick;
    uint32_t lifespan;
    uint32_t status;
    uint64_t death_tick;
    uint32_t lineage_id;
    uint32_t parent_id;
    uint32_t generation;
    uint32_t n_rival_tags;
    uint32_t n_children;
} om_character_record;

typedef struct om_chronicle_cluster {
    uint32_t type;
    uint32_t category;
    uint32_t region;
    double peak_score;
    int32_t chain_tag;
    uint64_t start_tick;
    uint64_t end_tick;
} om_chronicle_cluster;

typedef struct om_chronicle_entry {
    uint32_t id;
    uint32_t category;
    uint32_t region;
    char base_text[512];
    char expanded_text[1024];
    uint64_t start_tick;
    uint64_t end_tick;
    int32_t fragment_ids[3];
    int32_t region_ref;
    int32_t faction_ref;
    int32_t lineage_ref;
} om_chronicle_entry;

typedef struct om_chronicle_mention {
    uint32_t start;
    uint32_t len;
    uint32_t kind;
    int32_t id;
} om_chronicle_mention;

typedef struct om_client_unit {
    uint32_t id;
    int32_t faction_id;
} om_client_unit;

typedef struct om_composition_ratio {
    double line;
    double strike;
    double siege;
} om_composition_ratio;

typedef struct om_debrief {
    int32_t band;
    double objective_score;
    double retention;
    int32_t commander_fate;
    char text[2048];
} om_debrief;

typedef struct om_fairness_score {
    double route_count_balance;
    double travel_time_balance;
    double vantage_accessibility_balance;
    double hazard_symmetry;
    double composite_score;
} om_fairness_score;

typedef struct om_fragment_pool_counts {
    uint32_t openings;
    uint32_t details;
    uint32_t closings;
} om_fragment_pool_counts;

typedef struct om_gradient_properties {
    double obstacle_density;
    double cover_density;
    double sensor_interference;
    double elevation;
    uint32_t layer_accessibility_0;
    uint32_t layer_accessibility_1;
} om_gradient_properties;

typedef struct om_mission_candidate {
    uint32_t region_idx;
    uint32_t archetype;
    double urgency;
    double relevance;
    double preference;
    double score;
} om_mission_candidate;

typedef struct om_net_command {
    uint64_t tick;
    uint32_t seq;
    uint32_t arg;
    double x;
    double y;
    uint8_t peer;
    uint8_t verb;
    uint8_t layer;
    uint8_t n_units;
} om_net_command;

typedef struct om_objective_spec {
    uint32_t id;
    uint32_t kind;
    uint32_t is_primary;
    double weight;
    double completion;
    uint32_t is_complete;
    uint32_t is_failed;
} om_objective_spec;

typedef struct om_onboarding_config {
    uint32_t difficulty;
    double weights[10];
    uint32_t rare_marks[10];
} om_onboarding_config;

typedef struct om_ping_alert {
    uint64_t tick;
    int32_t faction;
    int32_t sector;
} om_ping_alert;

typedef struct om_reinforcement_wave {
    uint32_t is_scheduled;
    uint32_t direction;
    uint64_t arrival_tick;
    uint32_t is_spawned;
} om_reinforcement_wave;

typedef struct om_replay_command {
    uint64_t tick;
    uint32_t force_id;
    uint32_t command_type;
    double target_x;
    double target_y;
    uint32_t target_id;
} om_replay_command;

typedef struct om_reversion_record {
    uint64_t tick;
    uint32_t region_idx;
    int32_t original_faction;
    int32_t restored_faction;
    double military_stolen;
    double economy_stolen;
} om_reversion_record;

typedef struct om_revolt_record {
    uint64_t tick;
    uint32_t region_idx;
    int32_t original_faction;
    double success_rate;
    double draw;
    uint32_t faction_created;
    int32_t new_faction_id;
    double military_stolen;
    double economy_stolen;
    int32_t reverted_faction;
} om_revolt_record;

typedef struct om_selection_record {
    uint32_t rotated;
    uint32_t reason;
    uint32_t pool;
    uint32_t new_lineage_id;
    uint32_t commander_id;
    uint32_t chapters_in_lineage;
    uint32_t home_region_idx;
    uint32_t _pad;
} om_selection_record;

typedef struct om_slope {
    double x0;
    double y0;
    double x1;
    double y1;
    double mx;
    double my;
    double length;
    int32_t lower_band;
    int32_t upper_band;
} om_slope;

typedef struct om_structure_hud {
    double timer_progress;
    uint32_t next_unit_type;
    double hp;
    double max_hp;
} om_structure_hud;

typedef struct om_time_jump_report {
    uint64_t start_tick;
    uint64_t end_tick;
    uint32_t jump_ticks;
    uint32_t n_territory_changes;
    uint32_t n_faction_births;
    uint32_t n_faction_deaths;
    uint32_t n_conquests;
    uint32_t n_colonizations;
    uint32_t n_revolts;
    uint32_t n_chronicle_entries;
    uint32_t n_snapshots;
} om_time_jump_report;

typedef struct om_unit_profile {
    uint32_t unit_type;
    double hp;
    double base_damage;
    double attack_interval;
    double power;
} om_unit_profile;

typedef struct om_vec2 {
    double x;
    double y;
} om_vec2;

typedef struct om_client_snapshot {
    uint32_t unit_count;
    om_client_unit units[256];
} om_client_snapshot;
/* ---- end generated: structs ---- */

/* ---- generated from signatures.toml: checksum_full.c ---- */
uint64_t om_world_checksum_full(const om_world *w, uint64_t *sections, uint32_t cap);
uint32_t om_checksum_section_count(void);
const char *om_checksum_section_name(uint32_t section);
int om_checksum_first_diff(const om_world *a, const om_world *b, uint32_t *section, uint32_t *unit_id);
uint32_t om_checksum_unit_hashes(const om_world *w, uint64_t *out, uint32_t cap);
/* ---- end generated: checksum_full.c ---- */

/* ---- generated from signatures.toml: chronicle.c ---- */
void om_chronicle_add_chain_event(om_world *w, int32_t chain_tag, uint32_t region_idx, uint32_t category);
void om_chronicle_add_cluster_direct(om_world *w, uint32_t cluster_type, uint32_t category, double score);
void om_chronicle_add_consequence_event(om_world *w, uint32_t region_idx, uint32_t outcome);
void om_chronicle_add_event(om_world *w, uint32_t region_idx, double score);
void om_chronicle_add_lineage_event(om_world *w, uint32_t lineage_id, uint32_t region_idx, uint32_t category, double score);
void om_chronicle_add_mock_entry(om_world *w, uint32_t entry_id, uint64_t start_tick, uint64_t end_tick);
void om_chronicle_add_ownership_change_event(om_world *w, uint32_t region_idx, uint64_t tick);
void om_chronicle_add_raw_entry(om_world *w, uint32_t entry_id, const char *text);
int om_chronicle_add_regional_event(om_world *w, uint32_t region_idx, uint32_t category, double score);
const char *om_chronicle_apply_slot_echo_anaphora(om_world *w, const char *fragment1_slot, const char *fragment2_slot);
const char *om_chronicle_apply_word_echo_synonym(om_world *w, const char *text);
int om_chronicle_assemble_cluster_entry(om_world *w, uint32_t category, uint32_t region_idx, om_chronicle_entry *out_entry);
void om_chronicle_assemble_with_seed(om_world *w, uint64_t seed);
uint32_t om_chronicle_build_chain_clusters(om_world *w);
void om_chronicle_build_opening_scroll(om_world *w);
double om_chronicle_calculate_score(const om_world *w, uint32_t tier, double delta_sum, int in_mission_region, int has_character, uint32_t chain_length, int has_lineage_member);
uint32_t om_chronicle_categorize_chain_cluster(const om_world *w, const char *template_name, uint32_t n_events, double net_mil, double net_eco, double net_ten);
uint32_t om_chronicle_categorize_lineage_cluster(const om_world *w, const char *template_name, double net_eco, double net_mil, double net_ten);
uint32_t om_chronicle_categorize_regional_cluster(const om_world *w, int has_conquest_or_revolt, double net_eco_pop);
const char *om_chronicle_category_name(uint32_t category);
uint32_t om_chronicle_chain_category_count(const om_world *w);
double om_chronicle_context_multiplier(const om_world *w, int in_mission_region, int has_character, uint32_t chain_length, int has_lineage_member);
uint32_t om_chronicle_count_by_type(const om_world *w, uint32_t cluster);
void om_chronicle_dedup_content_words(om_world *w, double threshold);
void om_chronicle_dismiss_expanded(om_world *w);
void om_chronicle_distill_and_assemble(om_world *w);
uint32_t om_chronicle_entry_count(const om_world *w);
int om_chronicle_entry_get(const om_world *w, uint32_t index, om_chronicle_entry *out);
int om_chronicle_entry_is_retained(const om_world *w, uint32_t entry_id);
int om_chronicle_fragment_batch_exceeds_rejection_limit(const om_world *w, uint32_t rejected_count, uint32_t total_count);
uint32_t om_chronicle_fragment_category_count(const om_world *w);
int om_chronicle_fragment_check_near_duplicate(const om_world *w, const char *p0, const char *p1);
void om_chronicle_fragment_inject_invalid_slot(om_world *w, uint32_t category, const char *invalid_slot);
void om_chronicle_fragment_library_load_launch(om_world *w);
int om_chronicle_fragment_library_validate(const om_world *w);
int om_chronicle_fragment_pool_counts(const om_world *w, uint32_t category, om_fragment_pool_counts *out);
void om_chronicle_generate_map_keyframes(om_world *w);
int om_chronicle_get_cluster(const om_world *w, uint32_t entry, om_chronicle_cluster *out);
const char *om_chronicle_get_full_scroll_text(const om_world *w);
int om_chronicle_handle_click(om_world *w, uint32_t entry_id);
int om_chronicle_get_keyframe(const om_world *w, uint32_t i, uint64_t *tick_out);
int om_chronicle_has_keyframe_at_tick(const om_world *w, uint64_t p0);
int om_chronicle_has_keyframe_in_range(const om_world *w, uint64_t p0, uint64_t p1);
int om_chronicle_is_lineage_event(const om_world *w, uint32_t lineage_id, uint32_t region_idx, uint32_t attached_character_id, uint32_t mission_region);
int om_chronicle_is_paused(const om_world *w);
uint32_t om_chronicle_keyframe_count(const om_world *w);
uint32_t om_chronicle_lineage_category_count(const om_world *w);
int om_chronicle_map_is_master_clock(const om_world *w);
uint32_t om_chronicle_mention_count(const om_world *w, uint32_t index, int expanded);
int om_chronicle_mention_get(const om_world *w, uint32_t index, int expanded, uint32_t mention_idx, om_chronicle_mention *out);
void om_chronicle_mock_populate_events(om_world *w, uint32_t n_events);
double om_chronicle_presentation_entry_hold_sec(const om_world *w);
double om_chronicle_presentation_map_width_ratio(const om_world *w);
double om_chronicle_presentation_slide_in_sec(const om_world *w);
double om_chronicle_presentation_slide_out_sec(const om_world *w);
double om_chronicle_presentation_word_cadence_sec(const om_world *w);
double om_chronicle_presentation_word_fade_sec(const om_world *w);
uint32_t om_chronicle_regional_category_count(const om_world *w);
const char *om_chronicle_render_character_rank(const om_world *w, uint32_t character_id);
const char *om_chronicle_render_region_mention(const om_world *w, uint32_t region_idx, int is_first_mention);
uint32_t om_chronicle_rendered_entry_count(const om_world *w);
double om_chronicle_score_base(const om_world *w, uint32_t tier, double delta_sum);
double om_chronicle_score_event(const om_world *w, uint32_t region_idx, uint32_t tier, double delta_sum);
void om_chronicle_select_clusters(om_world *w);
uint32_t om_chronicle_selected_category_count(const om_world *w, uint32_t category);
void om_chronicle_set_entry_state(om_world *w, uint32_t entry_id, int is_printing);
int om_chronicle_validate_event_template_prose(const om_world *w);
const char *om_event_template_chronicle_prose(const om_world *w, uint32_t template);
/* ---- end generated: chronicle.c ---- */

/* ---- generated from signatures.toml: cmd_stream.c ---- */
int om_cmd_submit(om_world *w, const om_net_command *cmd, const uint32_t *unit_ids);
void om_cmd_reset(om_world *w);
uint64_t om_net_tick(const om_world *w);
uint32_t om_cmd_pending_count(const om_world *w);
uint32_t om_cmd_log_size(const om_world *w);
uint32_t om_cmd_log_write(const om_world *w, uint8_t *out, uint32_t cap);
int om_cmd_log_feed(om_world *w, const uint8_t *buf, uint32_t len);
/* ---- end generated: cmd_stream.c ---- */

/* ---- generated from signatures.toml: diplomacy.c ---- */
double om_archetype_betrayal_weight(om_archetype archetype);
double om_archetype_peace_disposition(om_archetype archetype);
int32_t om_breakaway_create(om_world *w, int32_t parent, uint32_t region_idx);
uint32_t om_chronicle_distill_candidates(const om_world *w, uint32_t *out, uint32_t max);
void om_diplomacy_init(om_world *w);
void om_diplomacy_step(om_world *w);
double om_faction_betrayal_chance(const om_world *w, int32_t betrayer, int32_t partner);
double om_faction_betrayal_opportunity(const om_world *w, int32_t betrayer, int32_t partner);
uint64_t om_faction_cooperative_since(const om_world *w, int32_t p0, int32_t p1);
void om_faction_create_breakaway(om_world *w, int32_t parent, uint32_t p1);
int64_t om_faction_last_knowledge_lost(const om_world *w, int32_t faction_id);
uint32_t om_faction_next_mission_unit_tier(const om_world *w, int32_t faction_id);
void om_faction_set_last_knowledge_lost(om_world *w, int32_t faction_id, int64_t tick);
void om_faction_set_stance_counter(om_world *w, int32_t p0, int32_t p1, uint32_t counter);
uint32_t om_faction_stance_counter(const om_world *w, int32_t p0, int32_t faction);
double om_faction_tech_attack(const om_world *w, int32_t faction_id);
double om_faction_tech_defense(const om_world *w, int32_t faction_id);
double om_faction_tech_economy(const om_world *w, int32_t faction_id);
void om_faction_tech_multipliers(const om_world *w, int32_t faction_id, double *attack, double *defense, double *economy);
uint32_t om_faction_tech_tier(const om_world *w, int32_t faction_id);
int om_faction_tier_transition_candidate(const om_world *w, int32_t faction_id);
uint32_t om_faction_unit_tier(const om_world *w, int32_t faction_id);
uint32_t om_mission_start(om_world *w, int32_t faction_id);
uint32_t om_mission_unit_tier(const om_world *w, uint32_t mission_id);
void om_tech_step(om_world *w);
uint32_t om_tech_tier(double tech);
int om_tier_transition_candidate_exists(const om_world *w, int32_t faction_id);
/* ---- end generated: diplomacy.c ---- */

/* ---- generated from signatures.toml: economy_density.c ---- */
double om_density_at(const om_world *w, double x, double y);
/* ---- end generated: economy_density.c ---- */

/* ---- generated from signatures.toml: economy_doctrine.c ---- */
int om_doctrine_get(const om_world *w);
uint32_t om_wave_get_since(const om_world *w, uint32_t tick, om_wave *out, uint32_t cap);
/* ---- end generated: economy_doctrine.c ---- */

/* ---- generated from signatures.toml: economy_lots.c ---- */
uint32_t om_lot_count(const om_world *w);
int om_lot_get_at(const om_world *w, uint32_t i, om_lot *out);
int om_economy_place(om_world *w, int32_t building, double x, double y);
/* ---- end generated: economy_lots.c ---- */

/* ---- generated from signatures.toml: enemy_macro.c ---- */
void om_macro_bind_hook_flag(om_world *w, uint32_t p1, const char *p2);
uint32_t om_macro_bus_get_active_flags_count(om_world *w);
int om_macro_bus_get_flag(om_world *w, const char *p1);
void om_macro_bus_register_vocab(const char *p0);
void om_macro_bus_set_flag(om_world *w, const char *p1, int p2);
void om_macro_enemy_leaves_trigger(om_world *w, uint32_t p1);
int om_macro_eval_hook_flag(om_world *w, uint32_t p1, const char *p2);
int om_macro_eval_timer_transition(uint64_t p0, uint64_t p1, double p2);
int om_macro_eval_transitions(om_world *w, uint32_t p1);
uint32_t om_macro_evaluation_interval_ticks(void);
int om_macro_execute_behavior(om_world *w, uint32_t p1, int p2, int p3);
int om_macro_get_behavior(om_world *w, uint32_t p1);
uint32_t om_macro_get_eval_interval(int p0);
int om_macro_get_last_issued_command_type(om_world *w, uint32_t p1);
int om_macro_get_modifier(om_world *w, uint32_t p1);
uint32_t om_macro_get_phased_subgroups(om_world *w, uint32_t p1);
double om_macro_get_speed_multiplier(int p0);
double om_macro_get_threshold_noise(om_world *w, uint32_t p1);
double om_macro_get_timer_noise(om_world *w, uint32_t p1);
int om_macro_has_evaluated(om_world *w);
void om_macro_init_force(om_world *w, uint32_t p1, int32_t p2);
int om_macro_is_hidden(om_world *w, uint32_t p1);
int om_macro_issues_illegal_command(om_world *w);
int om_macro_mutates_unit_stats(om_world *w);
void om_macro_player_enter_objective(om_world *w, uint32_t p1);
int om_macro_reads_player_visibility_set(om_world *w);
int om_macro_resolve_conflict(int p0, int p1);
int om_macro_resolve_conflict_types(int p0, int p1);
void om_macro_set_base_transition_true(om_world *w, uint32_t p1, int p2);
void om_macro_set_force_fallback_point(om_world *w, uint32_t force, double x, double y);
void om_macro_set_force_hp_pct(om_world *w, uint32_t p1, double p2);
void om_macro_set_hook_true(om_world *w, uint32_t p1, int p2);
void om_macro_set_state(om_world *w, uint32_t p1, int p2, int p3);
void om_macro_tick(om_world *w, uint64_t p1);
void om_macro_trigger_ambush(om_world *w, uint32_t p1);
void om_macro_update_bus_runner(om_world *w);
int om_macro_validate_bus_flag(const char *p0);
int om_macro_validate_condition_name(const char *p0);
int om_macro_validate_state(int p0, int p1);
int om_map_is_edge_coord(om_world *w, double p1, double p2);
void om_mission_check_external_reinforcements(om_world *w);
double om_mission_get_external_reinforcement_prob(void);
uint32_t om_mission_get_reinforcement_foreshadow_text(om_world *w, char *p1, uint32_t p2);
void om_mission_get_reinforcement_spawn_pos(om_world *w, double *p1, double *p2);
void om_mission_init_seed(om_world *w, uint64_t p1);
int om_mission_is_reinforcement_spawned(om_world *w);
void om_mission_schedule_external_reinforcement(om_world *w, om_reinforcement_wave *p1);
void om_mission_set_external_reinforcement(om_world *w, const om_reinforcement_wave *p1);
uint32_t om_replay_command_count(om_world *w);
uint32_t om_replay_get_commands(om_world *w, om_replay_command *p1, uint32_t p2);
void om_replay_log_command(om_world *w, uint64_t p1, uint32_t p2, uint32_t p3, double p4, double p5, uint32_t p6);
void om_session_capture_enable(om_world *w, int p1);
uint32_t om_session_capture_get_size(om_world *w);
int om_session_capture_is_enabled(om_world *w);
uint32_t om_session_capture_read(om_world *w, char *p1, uint32_t p2);
double om_unit_get_base_hp(uint32_t p0, int p1);
const void *om_unit_get_decision_loop_ptr(uint32_t p0, int p1);
/* ---- end generated: enemy_macro.c ---- */

/* ---- generated from signatures.toml: events.c ---- */
uint32_t om_event_fire_manual(om_world *w, uint32_t region_idx, uint32_t tier);
uint32_t om_event_get_attached_character(const om_world *w, uint32_t event, uint32_t p1);
int32_t om_event_template_significance_tier(const om_world *w, uint32_t template_id);
/* ---- end generated: events.c ---- */

/* ---- generated from signatures.toml: fog.c ---- */
om_client_snapshot *om_client_snapshot_read(const om_world *w);
double om_fog_get_drawn_sensor_circle_radius(const om_world *w, uint32_t unit);
int om_fog_get_treatment_at(const om_world *w, double x, double y, uint32_t layer);
uint32_t om_map_add_hazard_zone(om_world *w, double x, double y, double p2);
void om_map_add_interference_zone(om_world *w, double x, double y, uint32_t layer, double intensity, double radius);
void om_map_add_moving_interference_zone(om_world *w, double x, double y, uint32_t layer, double intensity, double radius, double vx, double vy);
void om_map_add_vantage_node(om_world *w, double x, double y, double radius);
void om_mission_begin(om_world *w);
uint64_t om_mission_get_clock(const om_world *w);
int om_mission_get_phase(const om_world *w);
int om_mission_is_started(const om_world *w);
void om_mission_set_phase(om_world *w, int phase);
int om_player_can_see(const om_world *w, int32_t faction_id, uint32_t unit);
int om_player_can_see_friendly(const om_world *w, int32_t faction_id, uint32_t unit);
int om_player_can_see_unit(const om_world *w, int32_t p0, uint32_t unit);
double om_recon_get_terrain_visibility_ratio(const om_world *w);
int om_recon_is_enemy_visible(const om_world *w, uint32_t unit);
int om_recon_is_feature_visible(const om_world *w, uint32_t feature_id);
int om_recon_is_spawn_point_visible(const om_world *w, uint32_t spawn_id);
int om_recon_is_structure_ownership_visible(const om_world *w, uint32_t structure_id);
void om_set_era_flag(om_world *w, const char *name, int on);
void om_set_era_name(om_world *w, const char *name);
double om_strategic_agent_read_region_field(const om_world *w, int32_t p0, uint32_t region_idx, om_field field);
void om_unit_acquire_target(om_world *w, uint32_t unit);
int om_unit_can_see(const om_world *w, uint32_t observer, uint32_t target);
double om_unit_get_cross_layer_factor(const om_world *w, uint32_t unit, uint32_t p0);
double om_unit_get_effective_sensor_radius_to_target_elevation(const om_world *w, uint32_t unit, uint32_t target_elevation_tier);
uint32_t om_unit_spawn_with_elevation(om_world *w, int unit_type, int32_t faction_id, double x, double y, uint32_t layer, uint32_t elevation_tier);
void om_visibility_compute(om_world *w);
void om_visibility_set_player_fog(om_world *w, int on);
double om_zone_sample_interference(const om_world *w, double x, double y, uint32_t layer);
int om_command_set_emission(om_world *w, const uint32_t *unit_ids, uint32_t n_units, om_emission mode);
int om_unit_get_emission(const om_world *w, uint32_t unit);
int om_command_ping(om_world *w, uint32_t caster, uint32_t layer, double x, double y);
uint32_t om_ping_alert_count(const om_world *w, int32_t faction);
int om_ping_alert_get(const om_world *w, int32_t faction, uint32_t index, om_ping_alert *out);
int om_set_era_kind(om_world *w, int kind);
int om_era_kind(const om_world *w);
/* ---- end generated: fog.c ---- */

/* ---- generated from signatures.toml: generational.c ---- */
int om_campaign_check_surviving_factions(const om_world *w);
uint32_t om_campaign_commander(const om_world *w);
uint32_t om_campaign_lineage(const om_world *w);
int om_campaign_needs_onboarding(const om_world *w);
uint32_t om_campaign_opening_jump_length(const om_world *w);
void om_campaign_start(om_world *w, uint32_t chapter);
void om_campaign_trigger_terminal_restart(om_world *w);
void om_chapter_advance_phase(om_world *w);
int om_chapter_current_phase(const om_world *w);
uint32_t om_chapter_get_number(const om_world *w);
int om_chapter_last_end_reason(const om_world *w);
int om_chapter_end_reason_for_collapse(const om_world *w, int32_t player_faction);
int om_chapter_mission_realtime(const om_world *w);
int om_chapter_recon_has_clock(const om_world *w);
void om_chapter_set_phase(om_world *w, int p0);
void om_chapter_start(om_world *w, uint32_t chapter);
void om_chapter_transition_complete(om_world *w);
void om_chapter_transition_start(om_world *w);
uint32_t om_character_count(const om_world *w);
void om_character_create(om_world *w, uint32_t character_id, uint32_t lineage_id, uint32_t region_idx, uint32_t rank, uint64_t birth_tick, uint32_t lifespan);
void om_character_create_child(om_world *w, uint32_t child_id, uint32_t parent_id, uint32_t region_idx, uint64_t birth_tick, uint32_t lifespan);
uint32_t om_character_create_random(om_world *w, int32_t faction_id, uint32_t region_idx);
uint32_t om_character_create_with_rank(om_world *w, int32_t faction_id, uint32_t region_idx, uint32_t rank, uint64_t birth_tick, uint32_t lifespan);
int32_t om_character_faction(const om_world *w, uint32_t character);
int om_character_get_record(const om_world *w, uint32_t character, om_character_record *out);
int om_character_has_event_history(const om_world *w, uint32_t character);
int om_character_has_rival_tag(const om_world *w, uint32_t character_id, uint32_t target_commander_id);
uint32_t om_character_id_at(const om_world *w, uint32_t index);
int om_character_is_main_character(const om_world *w, uint32_t character_id);
void om_character_kill(om_world *w, uint32_t character_id, uint64_t tick);
uint32_t om_character_lineage_id(const om_world *w, uint32_t character);
uint32_t om_character_name_reuse_cooldown(const om_world *w, uint32_t character_id);
void om_character_selector_confirm_commander(om_world *w, uint32_t character_id);
void om_character_selector_force_rotate(om_world *w, uint32_t lineage_id, uint32_t mission_region, int reason, int pool, om_selection_record *out_record);
uint32_t om_character_selector_input_region(const om_world *w);
void om_character_selector_resolve_commander_death(om_world *w, uint32_t lineage_id, uint32_t mission_region, om_selection_record *out_record);
void om_character_selector_run(om_world *w);
void om_character_selector_run_for_lineage(om_world *w, uint32_t lineage_id, uint32_t mission_region, om_selection_record *out_record);
void om_character_set_faction(om_world *w, uint32_t character_id, int32_t faction_id);
void om_character_set_generation(om_world *w, uint32_t character_id, uint32_t generation);
void om_character_tag_rival(om_world *w, uint32_t character_id, uint32_t rival_of_character_id);
uint32_t om_chronicle_consequence_entry_count(const om_world *w);
int om_chronicle_has_faction_fall_entry(const om_world *w, int32_t old_faction);
int om_chronicle_has_mission_consequence_flag(const om_world *w);
uint32_t om_chronicle_lineage_entry_count(const om_world *w);
uint32_t om_event_attached_character_count(const om_world *w, uint32_t event);
void om_faction_create_named(om_world *w, int32_t faction_id, uint32_t first_region);
uint32_t om_faction_supreme_commander(const om_world *w, int32_t faction_id);
uint32_t om_force_allocated_unit_count(const om_world *w, uint32_t mission_id);
void om_force_allocator_run(om_world *w, uint32_t mission_id, double budget);
void om_force_set_surviving_units(om_world *w, uint32_t mission_id, uint32_t n_survivors);
int om_ledger_commander_death_outcome_band(const om_world *w, uint32_t commander_id);
uint32_t om_ledger_commander_death_region(const om_world *w, uint32_t commander_id);
uint32_t om_lineage_chapter_count(const om_world *w, uint32_t lineage_id);
uint32_t om_lineage_count(const om_world *w);
void om_lineage_create(om_world *w, uint32_t lineage_id, uint32_t home_region);
int32_t om_lineage_first_member_region(const om_world *w, uint32_t lineage_id);
uint32_t om_lineage_generate_descendants(om_world *w, uint32_t lineage_id, uint32_t jump_ticks);
int32_t om_lineage_history_region(const om_world *w, uint32_t lineage_id, uint32_t idx);
uint32_t om_lineage_home_region(const om_world *w, uint32_t lineage_id);
uint32_t om_lineage_id_at(const om_world *w, uint32_t index);
int om_lineage_member_in_region(const om_world *w, uint32_t lineage_id, uint32_t region_idx);
void om_lineage_record_history_region(om_world *w, uint32_t lineage_id, uint32_t region_idx);
void om_lineage_set_chapter_count(om_world *w, uint32_t lineage_id, uint32_t chapters);
uint32_t om_lineage_spawn_descendant_at_tick(om_world *w, uint32_t lineage_id, uint32_t parent_id, uint64_t tick);
uint32_t om_lineage_spawn_single_descendant(om_world *w, uint32_t lineage_id);
uint32_t om_mission_generator_chosen_region(const om_world *w);
int32_t om_mission_generator_chosen_archetype(const om_world *w);
void om_mission_generator_run(om_world *w);
void om_mission_tag_rivals(om_world *w, uint32_t mission_region, uint32_t commander_id);
void om_onboarding_load_from_slot(const om_world *w, uint32_t slot_id, om_onboarding_config *out_cfg);
void om_onboarding_save_to_slot(om_world *w, uint32_t slot_id, const om_onboarding_config *cfg);
int om_onboarding_update_choices(om_world *w, uint32_t slot_id, const om_onboarding_config *new_cfg);
int om_onboarding_validate(const om_onboarding_config *cfg);
void om_outcome_apply_consequences(om_world *w, uint32_t target_region, double delta_military, double delta_economy);
void om_outcome_record_commander_death(om_world *w, uint32_t commander_id, uint32_t mission_region, int outcome_band);
int om_player_faction_check_collapse(const om_world *w, int32_t player_faction);
int32_t om_player_faction_reassign_on_collapse(om_world *w, int32_t player_faction);
void om_player_faction_record_reassignment(om_world *w, int32_t old_faction, int32_t new_faction);
void om_process_natural_deaths(om_world *w, uint64_t tick);
uint32_t om_progression_carried_commander_stats_count(const om_world *w);
int om_progression_has_player_level(const om_world *w);
int om_progression_supports_era_unlocks(const om_world *w);
void om_region_assign_regional_commander(om_world *w, uint32_t region_idx, int32_t faction_id);
uint32_t om_region_regional_commander(const om_world *w, uint32_t region_idx);
void om_rng_force_descendant_spread(om_world *w, double spread_draw);
void om_rng_force_selector_draw(om_world *w, double forced);
double om_selector_base_rotation_prob(const om_world *w, double delta);
void om_selector_clear_pools(om_world *w);
double om_selector_decayed_rotation_prob(const om_world *w, double base_p, uint32_t chapters);
uint32_t om_selector_draw_unrelated(om_world *w, uint32_t mission_region);
uint32_t om_selector_gather_nemesis_candidates(om_world *w, uint32_t mission_region);
uint32_t om_selector_get_nemesis_candidate(const om_world *w, uint32_t candidate);
int om_selector_resolve_fallback_pool(const om_world *w, int initial_pool);
int om_selector_roll_pool(const om_world *w, double draw);
double om_selector_score_previous_lineage(const om_world *w, uint32_t chapters_ago, uint32_t living_nearby);
uint32_t om_time_jump_choose_length(om_world *w, uint32_t requested);
uint32_t om_time_jump_choose_opening_length(om_world *w);
uint32_t om_time_jump_death_pass_count(const om_world *w);
uint64_t om_time_jump_death_processing_tick(const om_world *w);
uint32_t om_time_jump_get_ownership_snapshot(const om_world *w, uint32_t k, int32_t *owners_out, uint32_t cap);
int om_time_jump_interrupt(om_world *w);
uint64_t om_time_jump_lineage_generation_tick(const om_world *w);
uint32_t om_time_jump_ownership_snapshot_count(const om_world *w);
uint32_t om_time_jump_report_faction_field_deltas_count(const om_world *w, const om_time_jump_report *report);
int om_time_jump_run(om_world *w, uint32_t n_ticks, om_time_jump_report *report);
void om_time_jump_run_tracked(om_world *w, uint32_t jump);
uint64_t om_time_jump_start_tick(const om_world *w);
void om_world_set_strategic_tick(om_world *w, uint64_t tick);
uint64_t om_world_strategic_tick(const om_world *w);
/* ---- end generated: generational.c ---- */

/* ---- generated from signatures.toml: lifecycle.c ---- */
int om_faction_is_active(const om_world *w, int32_t faction_id);
void om_faction_mark_conquered_this_tick(om_world *w, int32_t faction_id);
int om_faction_phase(const om_world *w, int32_t faction_id);
void om_faction_remove(om_world *w, int32_t faction_id);
void om_faction_set_created_tick(om_world *w, int32_t faction_id, uint64_t tick);
void om_faction_set_event_window_counts(om_world *w, int32_t faction_id, uint32_t total_events, uint32_t revolts, uint32_t attacks, uint32_t colonizations);
int om_player_faction_collapsed(const om_world *w, int32_t faction_id);
int32_t om_region_previous_owner(const om_world *w, uint32_t idx);
void om_region_set_previous_owner(om_world *w, uint32_t idx, int32_t faction_id);
uint32_t om_tick_absorptions(const om_world *w, om_absorption_record *out, uint32_t max);
uint32_t om_tick_reversions(const om_world *w, om_reversion_record *out, uint32_t max);
uint32_t om_tick_revolts(const om_world *w, om_revolt_record *out, uint32_t max);
int om_world_is_terminal(const om_world *w);
/* ---- end generated: lifecycle.c ---- */

/* ---- generated from signatures.toml: mission.c ---- */
uint64_t om_archetype_base_time_ticks(uint32_t archetype);
double om_consequence_apply_clamped(double current, double delta);
double om_consequence_eval_delta_current(double current, double pct);
double om_consequence_eval_delta_deficit(double current, double pct);
void om_mission_allocate_force_profile(const om_world *w, uint32_t archetype, double total_power, double *out_ratios);
void om_mission_apply_capacity_shortfall(om_world *w, double capacity);
void om_mission_apply_consequences(om_world *w, uint32_t region_idx, uint32_t archetype, int32_t band);
void om_mission_apply_target_adjacent_player(om_world *w, uint32_t region_idx, om_field field, double delta);
uint32_t om_mission_archetype_count(const om_world *w);
int om_mission_assemble_briefing(const om_world *w, om_briefing *out);
void om_mission_build_candidate_pool(om_world *w);
void om_mission_build_objectives(om_world *w, uint32_t archetype);
int om_mission_can_edit_loadout(const om_world *w);
double om_mission_candidate_score(double urgency, double relevance, double preference);
uint32_t om_mission_candidates(const om_world *w, om_mission_candidate *out, uint32_t max);
int om_mission_check_terminated(const om_world *w, uint32_t p1);
int32_t om_mission_classify_band(uint32_t archetype, double final);
double om_mission_compute_base_parity(double c);
double om_mission_compute_difficulty_parity(double base, int difficulty);
double om_mission_compute_enemy_power(om_world *w, uint32_t archetype, double committed_budget, double military, double population);
double om_mission_compute_final_score(double o, double r);
double om_mission_compute_parity(double p0, int p1);
double om_mission_compute_preference(const om_world *w, uint32_t archetype);
double om_mission_compute_relevance(const om_world *w, uint32_t region_idx, uint32_t archetype);
double om_mission_compute_retention(double deployed_power, double surviving_power);
uint64_t om_mission_compute_time_limit(uint64_t B, double u);
double om_mission_compute_urgency(const om_world *w, uint32_t region_idx, uint32_t archetype);
void om_mission_end(om_world *w);
int32_t om_mission_eval_commander_fate(double hp, double max_hp);
double om_mission_eval_destroy_targets(om_world *w, uint32_t objective_idx, uint32_t destroyed);
double om_mission_eval_eliminate(om_world *w, uint32_t objective_idx, double hp_destroyed);
double om_mission_eval_escort(om_world *w, uint32_t objective_idx, uint32_t reached_alive);
void om_mission_eval_hold_zone(om_world *w, uint32_t objective_idx, uint32_t enemies_inside);
double om_mission_eval_survive(om_world *w, uint32_t objective_idx, uint64_t elapsed_ticks, int player_alive);
uint32_t om_mission_fallback_archetype(const om_world *w);
int32_t om_mission_fallback_enemy(const om_world *w, uint32_t region_idx);
uint32_t om_mission_fallback_region(const om_world *w);
double om_mission_fill_player_force(om_world *w, double P, double parity);
int om_mission_get_archetype_metadata(const om_world *w, uint32_t archetype, om_archetype_metadata *out);
double om_mission_get_archetype_preference_weight(const om_world *w, uint32_t archetype, int is_rare);
int32_t om_mission_get_band(const om_world *w);
uint32_t om_mission_get_briefing_controls(const om_world *w);
void om_mission_get_briefing_text(const om_world *w, char *out, uint32_t cap);
double om_mission_get_candidate_score(const om_world *w, uint32_t region_idx, uint32_t archetype);
uint32_t om_mission_get_compatible_layouts(const om_world *w, uint32_t archetype, uint32_t *out, uint32_t max);
uint32_t om_mission_get_commander_unit(const om_world *w);
int om_mission_assign_commander(om_world *w, uint32_t unit_id);
int om_mission_get_debrief(const om_world *w, om_debrief *out);
uint32_t om_mission_get_deployed_force_count(const om_world *w);
int32_t om_mission_get_enemy_faction(const om_world *w);
double om_mission_get_enemy_power(const om_world *w);
uint32_t om_mission_get_force_count(const om_world *w);
int om_mission_get_force_unit(const om_world *w, uint32_t i, int32_t *type, int32_t *tier);
double om_mission_get_objective_completion(const om_world *w, uint32_t objective_idx);
double om_mission_get_objective_score(const om_world *w);
uint32_t om_mission_get_objectives(const om_world *w, om_objective_spec *out, uint32_t max);
double om_mission_get_player_parity(const om_world *w, int32_t faction_id);
void om_mission_get_player_units(const om_world *w, int32_t faction_id, uint32_t *out, uint32_t max);
int om_mission_get_region_delta(const om_world *w, double *military, double *economy, double *tension, double *population);
void om_mission_get_shortfall_text(const om_world *w, char *out, uint32_t cap);
uint64_t om_mission_get_time_limit(const om_world *w);
int om_mission_has_ended(const om_world *w);
void om_mission_inject_candidate(om_world *w, uint32_t region_idx, uint32_t archetype, double score);
int om_mission_is_ended(const om_world *w);
void om_mission_load_launch_library(om_world *w);
uint32_t om_mission_objective_count(const om_world *w);
uint32_t om_mission_last_region(const om_world *w);
void om_mission_refresh_context(om_world *w, int32_t region);
void om_mission_resolve_refusal(om_world *w, uint32_t region_idx);
uint32_t om_mission_select(om_world *w);
uint32_t om_mission_select_candidate(om_world *w);
uint32_t om_mission_select_layout(om_world *w, uint32_t archetype, uint32_t p2);
void om_mission_set_archetype_profile(om_world *w, uint32_t archetype, const double *profile, uint32_t n_types);
void om_mission_set_candidate_viable(om_world *w, uint32_t archetype, int viable);
void om_mission_set_conflict_context(om_world *w, uint32_t region_idx, uint32_t recent_attacks, double attack_budget_sum, uint32_t adjacent_lost);
void om_mission_set_lineage_context(om_world *w, uint32_t region_idx, double lineage, uint32_t hops, uint32_t times_run);
void om_mission_set_objective_completion(om_world *w, uint32_t objective_idx, double completion);
void om_mission_set_player_units(om_world *w, int32_t faction_id, const uint32_t *counts, uint32_t n_types);
void om_mission_set_preference(om_world *w, uint32_t archetype, double weight);
void om_mission_set_revolt_events(om_world *w, uint32_t region_idx, uint32_t recent_revolt_events);
void om_mission_setup(om_world *w, uint32_t p1, uint32_t archetype, int lineage_connection);
void om_mission_setup_destroy_targets(om_world *w, uint32_t objective_idx, uint32_t total);
void om_mission_setup_eliminate(om_world *w, uint32_t objective_idx, double initial_hp);
void om_mission_setup_escort(om_world *w, uint32_t objective_idx, uint32_t total);
void om_mission_setup_fallback(om_world *w, uint32_t region_idx, int32_t enemy_faction);
void om_mission_setup_hold_zone(om_world *w, uint32_t objective_idx, uint64_t required_ticks);
void om_mission_setup_survive(om_world *w, uint32_t objective_idx, uint64_t required_ticks);
void om_mission_setup_tactical(om_world *w, uint32_t p1, uint64_t time_limit);
void om_mission_setup_termination(om_world *w, uint32_t p1, int primary_complete, int p3, uint64_t tick, uint64_t time_limit, int player_alive);
int om_objective_get_center(const om_world *w, uint32_t objective_idx, om_vec2 *out);
int32_t om_objective_get_node(const om_world *w, uint32_t objective_idx);
double om_objective_get_radius(const om_world *w, uint32_t objective_idx);
int om_objective_set_center(om_world *w, uint32_t objective_idx, double x, double y);
int64_t om_region_get_held_since(const om_world *w, uint32_t idx);
int32_t om_region_get_owner(const om_world *w, uint32_t idx);
void om_set_neighbors(om_world *w, uint32_t a, uint32_t b);
int om_unit_get_profile(uint32_t unit_type, int difficulty, om_unit_profile *out);
double om_unit_power(uint32_t unit_type);
int om_objective_get_done(const om_world *w, uint32_t idx);
/* ---- end generated: mission.c ---- */

/* ---- generated from signatures.toml: save.c ---- */
int om_load_state_read(om_world *w, const uint8_t *buffer, uint32_t length);
uint32_t om_save_state_size(const om_world *w);
void om_save_state_write(const om_world *w, uint8_t *out, uint32_t capacity);
/* ---- end generated: save.c ---- */

/* ---- generated from signatures.toml: space_field.c ---- */
int om_space_field_generate_nodes(om_world *w, uint32_t seed, double canvas_w, double canvas_h, double density, const double *node_xy, const uint32_t *node_slots, uint32_t n_nodes);
int om_space_field_present(const om_world *w);
uint32_t om_space_field_get_mask(const om_world *w, uint32_t layer, uint8_t *out, uint32_t cap);
void om_space_field_clear(om_world *w);
uint32_t om_space_field_poly_count(const om_world *w);
uint32_t om_space_field_poly_get(const om_world *w, uint32_t i, uint32_t *layer, uint32_t *kind, double *xy, uint32_t cap_pts);
/* ---- end generated: space_field.c ---- */

/* ---- generated from signatures.toml: space_noise.c ---- */
uint32_t om_space_hash32(int32_t ix, int32_t iy, int32_t iz, uint32_t seed);
uint32_t om_space_noise_layer(uint32_t layer_seed, double canvas, uint32_t k, int independent, double *out, uint32_t cap);
/* ---- end generated: space_noise.c ---- */

/* ---- generated from signatures.toml: tactical_mapgen.c ---- */
void om_fairness_evaluate(om_world *w, om_fairness_score *byref);
void om_fairness_force_score(om_world *w, double composite);
int om_fairness_is_score_logged(om_world *w);
void om_fairness_run_post_generation_check(om_world *w);
void om_gradient_add_moving_source(om_world *w, int p1, double p2, double p3, double p4, double start, uint32_t period);
double om_gradient_combine_overlap(double p0, double p1);
double om_gradient_get_anchor_intensity(int node, int gradient);
double om_gradient_get_anchor_radius(int p0, int p1);
double om_gradient_sample_single(double p0, double p1, double p2, int p3);
uint32_t om_map_add_cover(om_world *w, double x, double y, double radius, double height);
void om_map_add_layer_restriction_zone(om_world *w, double p1, double zone, uint32_t p3);
uint32_t om_map_add_obstacle(om_world *w, double x, double y, double radius);
uint32_t om_map_add_spawn_point(om_world *w, double x, double y, int32_t faction_id);
uint32_t om_map_add_spine_node(om_world *w, double x, double y, int p2);
uint32_t om_map_add_structure(om_world *w, double x, double y, int32_t owner_faction);
int om_map_archetype_canvas_category(uint32_t mission);
double om_map_check_boundary_gradient_discontinuity(om_world *w, double p1, double boundary);
double om_map_clamp_flavoring_delta(double delta);
void om_map_clear(om_world *w);
double om_map_compute_chokepoint_width(double width);
double om_map_compute_economy_obstacle_delta(double economy);
double om_map_compute_modified_canvas(uint32_t archetype, double p1, double p2);
double om_map_compute_tension_cover_delta(double tension);
uint32_t om_map_count_distinct_routes_staging_to_objective(om_world *w, uint32_t p1);
uint32_t om_map_count_nodes_of_type(om_world *w, int p1);
int om_map_cover_at(const om_world *w, uint32_t index, double *x, double *y, double *radius, double *height);
uint32_t om_map_cover_count(const om_world *w);
double om_map_flavoring_stability_multiplier(double stability);
void om_map_generate(om_world *w, uint32_t p1, uint64_t p2);
void om_map_generate_gradients(om_world *w, uint32_t p1, uint64_t p2);
void om_map_generate_spine(om_world *w, uint32_t p1, uint64_t p2);
uint64_t om_map_get_active_seed(om_world *w);
double om_map_get_canvas_base_dimension(int p0);
uint32_t om_map_get_compatible_layout_count(om_world *w, uint32_t archetype);
uint32_t om_map_get_compatible_layouts(om_world *w, uint32_t archetype, uint32_t *out, uint32_t max);
uint32_t om_map_get_node_count(om_world *w);
void om_map_get_node_pos(om_world *w, uint32_t node, om_vec2 *byref);
int om_map_get_node_type(om_world *w, uint32_t node);
uint32_t om_map_get_nth_node_of_type(om_world *w, int p1, uint32_t nth);
int om_map_get_simulation_coupling(om_world *w);
int om_map_has_flank_bypass(om_world *w, uint32_t chokepoint);
void om_map_instantiate_zone_pos(double p0, double base_pct, double canvas_dim, uint64_t seed, om_vec2 *out);
int om_map_is_reachable_from_all_spawns(om_world *w, uint32_t node);
int om_map_is_reachable_from_staging(om_world *w, uint32_t node);
int om_map_is_valid(om_world *w);
int om_map_layout_check_hazard_approaches(uint32_t layout_id);
int om_map_layout_check_vantage_reachability(uint32_t layout_id);
int om_map_layout_file_has_forbidden_fields(uint32_t p0);
int om_map_layout_file_has_required_fields(uint32_t p0);
int om_map_layout_matches_archetype_filter(uint32_t layout, uint32_t archetype);
uint32_t om_map_library_total_layouts(void);
int32_t om_map_node_get_owner(om_world *w, uint32_t vantage);
void om_map_sample_gradients(om_world *w, double p1, double x, om_gradient_properties *byref);
int om_map_sample_layer_accessibility(om_world *w, double p1, double x, uint32_t layer);
double om_map_sample_obstacle_density(om_world *w, double p1, double x);
uint32_t om_map_select_layout_uniform(uint64_t seed, uint32_t pool_size);
void om_map_set_simulation_coupling(om_world *w, int on);
void om_map_setup_drifting_node(om_world *w, uint32_t node, uint32_t period);
int om_map_verify_flank_connections(om_world *w);
uint32_t om_proc_arch_resolve_section_piece(int section_type, int era);
int om_proc_arch_section_is_era_agnostic(int section_type);
int om_render_detect_repeated_tile_boundary(om_world *w);
int om_route_grid_is_cell_blocked(double obstacle);
void om_unit_get_position(om_world *w, uint32_t unit_id, om_vec2 *byref);
void om_unit_order_hold_node(om_world *w, uint32_t unit_id, uint32_t node_id);
int om_map_set_canvas(om_world *w, double width, double height);
int om_map_block_rect(om_world *w, double x0, double y0, double x1, double y1, uint32_t layer_lo, uint32_t layer_hi);
uint32_t om_map_obstacle_count(const om_world *w);
int om_map_get_obstacle_at(const om_world *w, uint32_t i, double *x, double *y, double *r);
/* ---- end generated: tactical_mapgen.c ---- */

/* ---- generated from signatures.toml: tactical_move.c ---- */
void om_collision_pass(om_world *w);
int om_combat_can_shoot(const om_world *w, uint32_t p0, uint32_t p1);
void om_command_attack_target_kiting(om_world *w, uint32_t p0, uint32_t p1, double p2, double p3);
void om_command_direct_move(om_world *w, uint32_t p0, double p1, double p2);
uint32_t om_command_group_move(om_world *w, const uint32_t *p0, uint32_t n, double p2, double p3);
int om_command_issue_named(om_world *w, const char *p0, uint32_t p1, double p2, double p3);
int om_command_guard(om_world *w, const uint32_t *unit_ids, uint32_t n_units);
int om_command_move(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double x, double y);
void om_command_queue_attack_move(om_world *w, uint32_t p0, double p1, double p2);
void om_command_queue_move(om_world *w, uint32_t p0, double p1, double p2);
int om_group_is_active(const om_world *w, uint32_t p0);
void om_map_set_obstacle_density(om_world *w, uint32_t p0, uint32_t p1, uint32_t p2, double p3);
uint32_t om_navmesh_find_path(om_world *w, double p0, double p1, double p2, double p3, uint32_t p4);
uint32_t om_navmesh_get_cache_hits(const om_world *w);
double om_navmesh_get_cell_size(const om_world *w);
int om_navmesh_is_cell_blocked(const om_world *w, uint32_t p0, uint32_t p1, uint32_t p2);
int om_navmesh_is_path_straightened(const om_world *w);
double om_renderer_interpolate_facing(const om_world *w, uint32_t p0, double p1);
int om_renderer_interpolate_position(const om_world *w, uint32_t p0, double p1, double *p2, double *p3);
uint32_t om_replay_get_command_count_at_tick(const om_world *w, uint64_t p0);
int om_steering_get_obstacle_repulsion(const om_world *w, uint32_t p0, double *p1, double *p2);
double om_steering_get_sweep_angle_at(const om_world *w, uint32_t p0);
uint32_t om_steering_get_sweep_angle_count(const om_world *w);
void om_unit_clear_orders(om_world *w, uint32_t p0);
double om_unit_compute_terrain_speed(const om_world *w, uint32_t p0, double p1);
void om_unit_engage(om_world *w, uint32_t p0, uint32_t p1);
double om_unit_get_current_speed(const om_world *w, uint32_t p0);
int om_unit_get_destination(const om_world *w, uint32_t p0, double *p1, double *p2);
double om_unit_get_facing(const om_world *w, uint32_t p0);
int om_unit_get_order_kind(const om_world *w, uint32_t p0);
int om_unit_get_pos(const om_world *w, uint32_t unit, double *out_x, double *out_y);
int om_unit_has_active_buff(const om_world *w, uint32_t p0, const char *p1);
int om_unit_is_braced(const om_world *w, uint32_t p0);
void om_unit_set_facing(om_world *w, uint32_t p0, double p1);
void om_unit_set_pos(om_world *w, uint32_t p0, double p1, double p2);
void om_unit_set_visible_to_faction(om_world *w, uint32_t p0, int32_t p1, int p2);
void om_unit_teleport(om_world *w, uint32_t unit, double x, double y, uint32_t layer);
double om_tactical_get_param(const om_world *w, om_tac_param p);
int om_tactical_set_param(om_world *w, om_tac_param p, double value);
int om_command_set_layer(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t layer);
double om_unit_transition_progress(const om_world *w, uint32_t unit);
uint32_t om_unit_get_target_layer(const om_world *w, uint32_t unit);
int om_roster_set_reach(om_world *w, int unit_type, uint32_t layers_up, uint32_t layers_down);
int om_unit_profile_reach(const om_world *w, int unit_type, uint32_t *up, uint32_t *down);
uint32_t om_unit_get_group_id(const om_world *w, uint32_t unit);
int om_unit_get_leash_anchor(const om_world *w, uint32_t unit, double *x, double *y);
int om_unit_get_engaged(const om_world *w, uint32_t unit);
int om_roster_set_movement_kind(om_world *w, int type, int kind);
int om_unit_profile_movement_kind(const om_world *w, int type);
/* ---- end generated: tactical_move.c ---- */

/* ---- generated from signatures.toml: tactical_support.c ---- */
void om_drift_interpolate(const om_vec2 *p0, uint32_t waypoint, uint64_t period, int p3, uint64_t tick, om_vec2 *byref);
void om_enemy_production_adapt_target(const om_composition_ratio *target, const om_composition_ratio *player, om_composition_ratio *out);
int om_enemy_production_select_category(const om_composition_ratio *target, const om_composition_ratio *current);
void om_hazard_get_launch_types(uint32_t *p0, uint32_t max);
int om_hazard_is_enabled_at_launch(int p0);
uint32_t om_hazard_launch_type_count(void);
double om_hazard_sample_interference(om_world *w, double p1, double c_double);
uint32_t om_hazard_spawn_moving_interference(om_world *w, double p1, double p2, double p3, double c_double, uint64_t p5);
void om_mission_check_extraction_objectives(om_world *w);
double om_mission_compute_reinforcement_capacity(double c_double, uint64_t time);
double om_mission_compute_starting_force(double c_double);
uint32_t om_mission_get_reinforcement_trickle(om_world *w);
void om_mission_set_player_held_structures_count(om_world *w, int32_t faction_id, uint32_t held);
void om_mission_setup_extraction_point(om_world *w, double x, double y, double radius);
void om_objective_setup_drifting(om_world *w, uint32_t objective, uint64_t period);
uint32_t om_render_get_owner_color(int32_t owner);
uint32_t om_render_get_structure_silhouette_id(void);
uint32_t om_render_get_unit_silhouette_id(uint32_t unit);
int om_render_is_volume_obscuring(int p0);
void om_structure_apply_damage(om_world *w, uint32_t structure, double c_double, uint32_t attacker);
void om_structure_assign_owners(int mission, uint32_t total, uint32_t *p2, uint32_t *p3, uint32_t *byref);
uint32_t om_structure_compute_count(double ctypes, int p1);
double om_structure_get_base_max_hp(void);
double om_structure_get_capture_progress(om_world *w, uint32_t structure);
double om_structure_get_hp(om_world *w, uint32_t structure);
void om_structure_get_hud_data(om_world *w, uint32_t structure, om_structure_hud *byref);
double om_structure_get_last_spawn_distance(om_world *w, uint32_t structure);
double om_structure_get_matchup_multiplier(uint32_t attacker);
int32_t om_structure_get_owner(om_world *w, uint32_t structure);
void om_structure_get_position(om_world *w, uint32_t structure, om_vec2 *byref);
uint64_t om_structure_get_timer(om_world *w, uint32_t structure);
uint32_t om_structure_get_unit_type(om_world *w, uint32_t structure);
void om_structure_init(om_world *w, uint32_t structure, uint32_t unit, double c_double);
void om_structure_init_drifting(om_world *w, uint32_t structure, uint64_t period);
int om_structure_is_destroyed(om_world *w, uint32_t structure);
int om_structure_is_in_capture_radius(om_world *w, uint32_t structure, double p2, double x);
void om_structure_on_owner_changed(om_world *w, uint32_t structure, int32_t old, int32_t new);
int om_structure_pop_spawned_unit(om_world *w, uint32_t structure);
uint32_t om_structure_production_interval_ticks(double c_double);
void om_structure_set_capture_progress(om_world *w, uint32_t structure, double c_double);
void om_structure_set_capturing_faction(om_world *w, uint32_t structure, int32_t unopposed);
void om_structure_set_contested(om_world *w, uint32_t structure, int on);
void om_structure_set_owner(om_world *w, uint32_t structure, int32_t owner);
int om_structure_set_position(om_world *w, uint32_t slot, double x, double y);
void om_structure_set_timer(om_world *w, uint32_t structure, uint64_t timer);
void om_structure_switch_unit_type(om_world *w, uint32_t structure, uint32_t new);
void om_structure_tick_capture(om_world *w, uint32_t structure);
void om_structure_tick_production(om_world *w, uint32_t structure);
uint32_t om_structure_unit_cost(uint32_t unit);
void om_ticker_pop_message(om_world *w, char *create_string_buffer, uint32_t buffer);
int om_unit_can_return_fire(om_world *w, uint32_t unit);
void om_unit_get_order_destination(om_world *w, uint32_t unit, om_vec2 *byref);
int om_unit_has_non_combat_visual_tag(int p0);
int om_unit_is_flinching(om_world *w, uint32_t unit);
int om_unit_is_non_combat_supported(int p0);
void om_unit_order_move(om_world *w, uint32_t unit, double p2, double c_double);
uint32_t om_unit_spawn_non_combat(om_world *w, int p1, double p2, double c_double);
void om_unit_tick_decision_loop(om_world *w, uint32_t unit);
uint32_t om_structure_count(const om_world *w);
uint32_t om_structure_get_at(const om_world *w, uint32_t i);
/* ---- end generated: tactical_support.c ---- */

/* ---- generated from signatures.toml: terrain.c ---- */
int om_terrain_generate(om_world *w, uint64_t seed, double canvas_w, double canvas_h);
int om_terrain_present(const om_world *w);
double om_terrain_height_at(const om_world *w, double x, double y);
int om_terrain_band_at(const om_world *w, double x, double y);
int om_terrain_walkable_at(const om_world *w, double x, double y);
int om_terrain_ground_at(const om_world *w, int layer, double x, double y);
uint32_t om_terrain_band_heights(const om_world *w, double *out, uint32_t cap);
uint32_t om_terrain_slope_count(const om_world *w);
int om_terrain_slope_get(const om_world *w, uint32_t i, om_slope *out);
uint32_t om_terrain_cells(const om_world *w, uint32_t *w_cells, uint32_t *h_cells);
int om_terrain_cell_band(const om_world *w, uint32_t cx, uint32_t cy);
uint32_t om_terrain_dump_bands(const om_world *w, uint8_t *out, uint32_t cap);
uint32_t om_terrain_walk_mask(const om_world *w, int layer, uint8_t *out, uint32_t cap);
int om_terrain_slope_at(const om_world *w, double x, double y, om_slope *out);
int om_terrain_sight_blocks(const om_world *w, int layer0, double x0, double y0, int layer1, double x1, double y1);
int om_terrain_nearest_walkable(const om_world *w, double x, double y, double *ox, double *oy);
void om_terrain_clear(om_world *w);
uint32_t om_terrain_get_heights(const om_world *w, int32_t *out, uint32_t cap);
/* ---- end generated: terrain.c ---- */

/* ---- generated from signatures.toml: unit.c ---- */
int om_command_activate_ability(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double target_x, double target_y);
int om_command_attack_move(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double x, double y);
int om_command_attack_target(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t target_unit);
uint32_t om_cue_lookup(const char *name);
int om_era_elevation_damage_bonus_enabled(om_world *w);
int om_roster_register_custom_unit(om_world *w, uint32_t type_id, int category, const char *role, double max_hp, double base_damage, double attack_interval, double attack_range, double speed, double sensor_radius, double layer_transition_time, double aoe_radius, int ability_id);
double om_tactical_category_multiplier(om_world *w, int attacker_category, int target_category);
void om_tactical_disable_abilities(om_world *w);
void om_tactical_reset(om_world *w);
uint64_t om_tactical_run(om_world *w, uint64_t n_ticks);
uint64_t om_tactical_run_until_eliminated(om_world *w);
uint64_t om_tactical_run_until_engagement_ends(om_world *w, uint32_t unit_id);
void om_tactical_spawn_force_composition(om_world *w, int32_t faction_id, uint32_t count, const char *composition);
int om_tactical_target_validation_runs_every_tick(om_world *w);
int om_tactical_telegraph_active(om_world *w, double x, double y);
uint64_t om_tactical_tick(om_world *w);
uint64_t om_tactical_base_tick(const om_world *w);
uint32_t om_tactical_tick_period(const om_world *w);
uint64_t om_tactical_tick_to(om_world *w, uint64_t tick);
int om_tactical_zone_visible_to_enemy(om_world *w, uint32_t unit_id);
uint32_t om_tick_read_ability_events(om_world *w, om_ability_event *out, uint32_t max);
int om_unit_ability_active(om_world *w, uint32_t unit_id);
double om_unit_ability_cooldown(om_world *w, uint32_t unit_id);
int om_unit_alive(om_world *w, uint32_t unit_id);
void om_unit_apply_trait_modifier(om_world *w, uint32_t unit_id, int stat_field, double delta);
void om_unit_attack(om_world *w, uint32_t attacker, uint32_t target);
int32_t om_unit_brace_phase(const om_world *w, uint32_t unit_id);
uint32_t om_unit_count(const om_world *w);
double om_unit_damage_reduction(om_world *w, uint32_t unit_id);
void om_unit_deal_damage(om_world *w, uint32_t p1, uint32_t p2, double p3);
double om_unit_effective_speed(om_world *w, uint32_t unit_id);
double om_unit_order_speed(om_world *w, uint32_t unit_id);
void om_unit_fire_aoe_attack(om_world *w, uint32_t attacker_id, uint32_t target_id, double radius);
int32_t om_unit_get_faction(const om_world *w, uint32_t unit_id);
double om_unit_get_hp(const om_world *w, uint32_t unit);
int32_t om_unit_get_layer(const om_world *w, uint32_t unit_id);
uint32_t om_unit_get_target(const om_world *w, uint32_t unit);
int32_t om_unit_get_unit_type(const om_world *w, uint32_t unit_id);
double om_unit_hp(om_world *w, uint32_t unit_id);
uint32_t om_unit_id_at(const om_world *w, uint32_t index);
int om_unit_in_backswing(om_world *w, uint32_t unit_id);
int om_unit_in_flinch(om_world *w, uint32_t unit_id);
double om_unit_output_multiplier(om_world *w, uint32_t unit_id);
double om_unit_position_x(om_world *w, uint32_t unit_id);
double om_unit_position_y(om_world *w, uint32_t unit_id);
uint32_t om_unit_profile_ability_count(om_world *w, int unit_type);
double om_unit_profile_aoe_radius(om_world *w, int unit_type);
double om_unit_profile_attack_interval(om_world *w, int unit_type);
double om_unit_profile_attack_range(om_world *w, int unit_type);
double om_unit_profile_base_damage(om_world *w, int unit_type);
int om_unit_profile_category(om_world *w, int unit_type);
double om_unit_profile_dps(om_world *w, int unit_type);
double om_unit_profile_layer_transition_time(om_world *w, int unit_type);
double om_unit_profile_max_hp(om_world *w, int unit_type);
double om_unit_profile_sensor_radius(om_world *w, int unit_type);
double om_unit_profile_speed(om_world *w, int unit_type);
uint32_t om_unit_profile_trait_count(om_world *w, int unit_type);
uint32_t om_unit_render_craft_count(om_world *w, int unit_type);
double om_unit_render_silhouette_size(om_world *w, int unit_type);
void om_unit_set_ability_cooldown(om_world *w, uint32_t unit_id, double ticks);
void om_unit_set_brace_active(om_world *w, uint32_t unit_id, int on);
void om_unit_set_elevation_tier(om_world *w, uint32_t unit_id, int tier);
void om_unit_set_fortify_active(om_world *w, uint32_t unit_id, int on);
void om_unit_set_hp(om_world *w, uint32_t p0, double p1);
void om_unit_set_stealth(om_world *w, uint32_t unit_id, int on);
void om_unit_set_warden_aura_active(om_world *w, uint32_t unit_id, int on);
uint32_t om_unit_spawn(om_world *w, int unit_type, int32_t faction_id, double x, double y, uint32_t layer);
uint32_t om_unit_spawn_combat(om_world *w, int32_t p1, double p2, double x);
uint32_t om_unit_spawn_for_category(om_world *w, int category, int32_t faction_id, double x, double y, uint32_t layer);
int32_t om_unit_target(om_world *w, uint32_t unit_id);
uint32_t om_unit_targeting_cohort(om_world *w, uint32_t unit_id);
uint32_t om_tactical_event_count(om_world *w);
int om_tactical_event_get_at(om_world *w, uint32_t i, int32_t *kind, uint32_t *a, int32_t *b, uint64_t *tick);
/* ---- end generated: unit.c ---- */

#ifdef __cplusplus
}
#endif

#endif /* OUROBOROS_SIM_H */
