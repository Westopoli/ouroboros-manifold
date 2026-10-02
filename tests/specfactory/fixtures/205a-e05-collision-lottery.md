---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/collision.c implements the S-039 collision tick step (om_step_collisions): grouping, strength calculation, weighted lottery, retention/refund, unowned-target colonize dispatch, owned-target multi-collider combat and conquest, and loser tension, so tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py (R-039-01..04, 06; R-039-05 skipped, reason Q-039-01), tests/csim/test_E05_S039_wiring.py, and tests/csim/controls/test_control_e05_collision_max_strength.py pass and earlier E-05 suites stay green"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py::test_R_039_01_factors_1_0_0_7 tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py::test_R_039_02_opposition_0_35_ceiling_0 tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py::test_R_039_03_its_highest_military_region_gains tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py::test_R_039_04_starter_military_10_0_margin tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py::test_R_039_06_same_rules_apply_with_second tests/csim/test_E05_S039_wiring.py tests/csim/controls/test_control_e05_collision_max_strength.py"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E05_S036_declared_or_sprung.py tests/csim/test_E05_S037_battles_have_a_shape.py tests/csim/test_E05_S038_taking_a_region.py tests/csim/controls/test_control_e05_surprise_on_defense.py tests/csim/controls/test_control_e05_entrench_current_tick.py tests/csim/controls/test_control_e05_same_tick_redeclare.py tests/csim/controls/test_control_e05_conquest_on_band.py tests/csim/controls/test_control_e05_garrison_before_damage.py"
allowed_files: "csrc/collision.c"
snippet_file: csrc/collision.c
snippet_symbol: "om_step_collisions,om_tick_collisions"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-05.md
test_file: tests/csim/test_E05_S039_when_everyone_wants_the_same_region.py
expected_lines: 80
max_wall_minutes: 90
---

## Brief for DeepSeek

E-05 re-cut Card 9 (audit fix 2026-09-21: the old card ordered the const
read-back `om_tick_collisions` to mutate the world, which it structurally
cannot do -- `om_step_collisions` is the real mutating step; this card folds
in the former Card 205b's owned-target branch, since two cards owning one
symbol is not something this project's tooling supports). Implements S-039
(ALG-23, ALG-24) for R-039-01 through R-039-04 and R-039-06. R-039-05 is
excluded from this card's acceptance and its own test is skipped: whether a
same-tick multi-target *telegraph* maturation forms a collision at all is
`Q-039-01`, open in `docs/northstar/ambiguity_register.md`; this card does
not touch `om_step_telegraphs` and does not implement any telegraph
deferral mechanism. The owned-target combat math in part 2 below is general
(ALG-20..22) and is exercised today only by immediate (`OM_MODE_SURPRISE`)
same-tick collisions; it will also cover R-039-05 once Q-039-01 is answered
and its test unskipped.

Contract: `csrc/ouroboros_sim.h` (read-only). `csrc/om_internal.h` (read-only
here -- no new fields needed; `w->decisions[]`, `w->telegraphs[]`,
`w->attacks[]`, `w->collisions[]` already exist). Behavior and constants:
`projects/ouroboros/rules/E-05.md`, story S-039 rules R-039-01..06, citing
ALG-19 through ALG-24 in `docs/bible/algorithms.md`. Copy every constant
verbatim.

### 1. `om_step_collisions(om_world *w)` -- grouping and the shared lottery

Called once per tick, between `om_step_reinforce` (3e) and `om_step_resolve`
(3f) (already wired in `csrc/sim.c`, not this card's job). At entry:
`w->collisions_n = 0;`.

Group `w->decisions[]` entries by `target_idx` (both `OM_ACT_ATTACK` and
`OM_ACT_COLONIZE` actions; a decision with `mode == OM_MODE_TELEGRAPH` that
has not matured yet -- `w->tick < d->tick + 3` -- is not a collision
candidate here, since `om_step_resolve` skips it too until it matures). A
matured telegraph attack resolves inline in `om_step_telegraphs` today (3c,
unchanged by this card) and never reaches `w->decisions[]`; whether two
matured telegraphs on the same target the same tick should instead collide
here is `Q-039-01` (open), so this function only ever sees same-tick
immediate (`OM_MODE_SURPRISE`) attacks and colonize intents.

A target with 2 or more grouped intents is a collision. For each collision
group targeting region $T$, for each colliding intent $i$ of faction $f$:
- Empire economy `eco_f`: sum economy of all regions owned by $f$.
- `max_eco`: max `eco_f` among all colliders in this group (1.0 if all zero).
- `econ_factor = COLLISION_ECONOMY_FLOOR + (COLLISION_ECONOMY_CEILING - COLLISION_ECONOMY_FLOOR) * eco_f / max_eco`
  (floor `0.4`, ceiling `1.0`).
- `surprise = (mode == OM_MODE_SURPRISE) ? 0.5 : 1.0;` (telegraph and
  colonize intents always use `1.0`).
- `strength_i = commit_i * 1.0 * econ_factor * w->faction_tech_attack[f] * surprise;`
  (`1.0` is `ATTACK_EFFICIENCY`).

Winner lottery: drawn once, proportional to strength,
$P(i) = \text{strength}_i / \sum \text{strength}$ (equal shares if the sum
is 0). Fault injection: if `w->inject == OM_BUG_COLLISION_MAX_STRENGTH`
(104), winner is chosen by max strength with no draw.

Margin, opposition, refund (one draw): `second = max strength among
losers;` `margin = winner_strength / (winner_strength + second);`
`opp = (sum_strengths - winner_strength) / winner_strength;`
`ret_ceiling = COLLISION_RETENTION_MAX * max(0.0, 1.0 - opp * 0.6)` (max
`0.4`, scale `0.6`). Draw $u \sim U(0, \text{ret\_ceiling})$;
`refund = winner_commit * u;`. Every faction's full commit was already
deducted from `w->faction_budget` at decision time (`om_step_decisions`);
credit the refund back: `w->faction_budget[winner_faction] += refund;`.
Losers get no refund (their commit is already spent).

Fill the record in `w->collisions[w->collisions_n++]`: tick, target_idx =
T, n_colliders, faction[], commit[], economy_factor[], strength[], winner,
margin, retention_ceiling = ret_ceiling, refund, loser_tension[] (part 2).

After every group is resolved, compact `w->decisions[]` to remove every
intent that was part of a collision group (2+ colliders), preserving the
order of the intents that were not (`om_step_resolve` must never see a
collision-grouped intent again -- it double-resolves otherwise).

### 2. Unowned-target and owned-target resolution (same loop, per group)

If target region $T$ is unowned:
- Winner colonizes: `om_region_set_owner(w, T, winner_faction, w->tick);`,
  tier = `OM_TIER_FRONTIER`.
- If `margin < COLLISION_NARROW_MARGIN (0.6)`: draw
  $u_{\text{pen}} \sim U(0.5, 0.70)$; `starter_military = 10.0 * u_pen;`.
  Else `starter_military = 10.0`.
- Fields: military = starter_military, economy = `COLONY_START_ECONOMY`
  (20.0), tension = `COLONY_START_TENSION` (20.0), population =
  `COLONY_START_POPULATION` (25.0).
- Append a record to `w->colonizations[w->colonizations_n++]`: tick,
  faction_id = winner, target_idx = T, start_military, budget_spent =
  `COLONIZE_COST` (20.0) (the fixed colonize cost, already deducted from
  the winner's budget at decision time for a colonize intent; do not
  deduct it again here).
- Every loser takes a tension hit on its highest-military region:
  `loser_tension_i = COLLISION_LOSER_TENSION_BASE (5.0) * commit_i / budget_snapshot_f`
  (added to that region's tension, capped at 100.0).

If target region $T$ is owned (by a defender not among the colliders, or by
a collider -- either way, use the region's current owner as defender):
- Shared defense, computed ONCE before any collider's damage applies:
  `effective_defense = T.military * RESISTANCE_FACTOR (0.55) * tech_defense(defender) * entrenchment`,
  entrenchment from ALG-13 (`held_since < 0 ? 2.0 : 1.0 + min(1.0, (tick - held_since) / 100.0)`),
  same formula `om_step_resolve` already uses.
- For each collider $i$ (winner and losers alike, in collider index order):
  one fresh stochastic draw $u_i \sim U(0.7, 1.3)$;
  `net_i = (strength_i - effective_defense) * u_i;` (`strength_i` from part
  1 stands in for `effective_attack` here -- it already folds in commit,
  economy factor, tech, and surprise).
  Damage bands (ALG-21) on `net_i`: breakthrough (`net_i > 15.0`)
  `d_military = -0.8*net_i, d_economy = -0.3*net_i, d_tension = min(0.5*net_i, 30.0)`;
  contested (`0 < net_i <= 15`) `d_military = -0.5*net_i, d_economy = -0.2*net_i, d_tension = 0.4*net_i`;
  repelled (`net_i <= 0`) `d_military = -0.10*strength_i, d_economy = 0.0, d_tension = 2.0`.
- Sum every collider's damage deltas, apply once to $T$:
  `military = max(0.0, military + sum_d_military);`
  `economy = max(8.0, economy + sum_d_economy);`
  `tension = min(100.0, max(0.0, tension + sum_d_tension));`.
- Append one `om_attack_result` to `w->attacks[]` per collider (attacker =
  collider's faction, defender = T's owner before this resolution, mode,
  outcome = this collider's own band, `collision = 1`, commit, `effective_attack = strength_i`,
  `effective_defense` (the shared value, same for every collider),
  `stochastic = u_i`, net = net_i, its own d_military/d_economy/d_tension,
  `garrison = 0.0`, `budget_spent = commit_i`, `conquest = 0` -- conquest
  itself is decided and set by `om_step_resolve`'s existing conquest pass,
  which already iterates every `w->attacks[]` record with `outcome !=
  OM_OUT_REPELLED` and post-damage `military < 5.0` regardless of who wrote
  the record; do not duplicate that logic here).
- Every loser (including a non-winning collider against an owned target)
  still takes the ALG-23 tension hit on its highest-military region, same
  formula as the unowned case.

## Header slice

```c
typedef struct om_world om_world;

typedef enum {
    OM_F_MILITARY   = 0,
    OM_F_ECONOMY    = 1,
    OM_F_TENSION    = 2,
    OM_F_POPULATION = 3,
    OM_F_COUNT      = 4
} om_field;

typedef enum {
    OM_TIER_EMPTY    = 0,
    OM_TIER_FRONTIER = 1,
    OM_TIER_HOME     = 2
} om_tier;

/* ---- lifecycle ---- */
om_world *om_world_new(uint32_t n_regions, uint64_t seed);

void      om_world_free(om_world *w);

/* ---- hard-fixture path (isolation testing) ----
 * Set a region's state directly, bypassing world generation, so E-02 drift is
 * tested against known inputs. econ_phase / tension_phase are the ALG-01 phase
 * offsets in [0, 2pi). faction_id < 0 means unowned. Returns 0 on success. */
int  om_region_set(om_world *w, uint32_t idx, om_tier tier,
                   double military, double economy, double tension, double population,
                   double econ_phase, double tension_phase, int32_t faction_id);

/* ---- tick (7-step sequence, tick auto-increments from 1) ---- */
uint64_t om_world_step(om_world *w);                 /* advance one tick, return new tick */

/* ---- read state ---- */
double  om_region_field(const om_world *w, uint32_t idx, om_field f);

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

int  om_faction_set(om_world *w, int32_t faction_id, om_archetype archetype,
                    double budget, double tech, double attack_confidence);

void om_faction_set_stance(om_world *w, int32_t from, int32_t toward, om_stance s); /* directed */

void om_faction_set_tech_multipliers(om_world *w, int32_t faction_id,
                                     double attack, double defense, double economy);

double   om_faction_budget(const om_world *w, int32_t faction_id);

/* ---- region ownership and typed edges (fixture) ----
 * held_since_tick < 0 means "never conquered" (ALG-13: entrenchment 2.0).
 * om_region_set_edge replaces om_region_set_adjacency for E-05 and later: an
 * undirected edge with a type. Setting the same pair twice replaces the type. */
void    om_region_set_owner(om_world *w, uint32_t idx, int32_t faction_id, int64_t held_since_tick);

int32_t om_region_owner(const om_world *w, uint32_t idx);

int64_t om_region_held_since(const om_world *w, uint32_t idx);   /* < 0 if never conquered */

void    om_region_set_edge(om_world *w, uint32_t a, uint32_t b, om_edge_type t);

int     om_region_edge(const om_world *w, uint32_t a, uint32_t b, om_edge_type *out); /* 0 if no edge */

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
```

