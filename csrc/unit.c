/* csrc/unit.c — E-11 units, combat, and the tactical orchestrator (tick
 * wiring only; the epic's own unit/combat math lands with card B10).
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
#include "move_commit.h"
#include "economy_internal.h"
#include "om_constants.h"
#include <math.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

/* ---- B10-1/B10-2: E-11 roster table, category multiplier, stationary
 * combat, traits/ability contract, Warden aura ----
 * All unit/tactical state lives in w->tactical_state (om_tac_state below),
 * heap-allocated per om_world and freed by om_world_free through the
 * registered tactical_state_free hook (csrc/region.c) -- no file-static
 * state keyed by om_world* identity, so a freed test world's malloc
 * address being reused by a later world can never alias another world's
 * units (see leaf-01-Q1.md for the ABA hazard this structurally
 * eliminates). */

/* OM_MAX_UNITS is now defined in csrc/ouroboros_sim.h (HDR3) as a public macro.
 * OM_UNITS_INITIAL_CAP and per-unit internal arrays remain local. */
/* OM_MAX_UNITS 10100 -- see ouroboros_sim.h */
#define OM_UNITS_INITIAL_CAP 64
#define OM_GRID_UNLINKED 0xFFFFFFFFu
/* OM_GRID_CELL_SIZE promoted to csrc/om_constants.h (ALG-66, CONST-1). */
/* Spatial grid count cap and buffer pad are plumbing, stay local. */
#define OM_GRID_MAX_DIM 256
#define OM_GRID_PAD 1e-6
#define OM_GRID_INSERTION_SORT_MAX 32
/* om_tac_nearest_hostile: a second-nearest distance within this of the
 * nearest hands the choice back to the ordered reference scan. */
#define OM_TIE_SCAN_WINDOW (4.0 * OM_TIE_EPSILON)
#define OM_MAX_CUSTOM_TYPES 64
/* F5 (R-087-09, Westley 2026-10-07: "a unit gives up ... if it can't find a firing spot within 1 second"): the run, in base ticks. */
#define OM_GIVEUP_TICKS 20
/* DRAFT-giveup-exclusion-ticks: a target a unit gave up is not eligible for it for this many base ticks, or until it has a clear line to it (spec F5, Westley's to change). */
#define OM_GIVEUP_EXCLUSION_TICKS 100
/* F6 (R-096-08) DRAFT-guard-radius: how far from its post a guard walks, wu; the attack-move leash of R-087-05, Westley's number to change. */
#define OM_GUARD_RADIUS 200.0
#define OM_UNIT_TYPE_COUNT 6

#define OM_UT_RAIDER 0
#define OM_UT_INTERCEPTOR 1
#define OM_UT_VANGUARD 2
#define OM_UT_WARDEN 3
#define OM_UT_BOMBARD 4
#define OM_UT_BASTION 5
#define OM_UT_SUPPLY 6
#define OM_UT_EVACUATION 7

#define OM_CAT_STRIKE 0
#define OM_CAT_LINE 1
#define OM_CAT_SIEGE 2

/* S-082 launch roster: OM_ROSTER_*_HP/DAMAGE/INTERVAL/RANGE/SPEED/SENSOR/AOE
 * promoted to csrc/om_constants.h (ALG-60/61, CONST-1).
 * LAYER_TRANSITION constants not in original inventory (added after c882449);
 * kept local pending a future F3 pass that covers them. AOE 0.0 trivially
 * excluded per inventory criterion. */
#define OM_ROSTER_RAIDER_LAYER_TRANSITION 1.0
#define OM_ROSTER_RAIDER_AOE 0.0

#define OM_ROSTER_INTERCEPTOR_LAYER_TRANSITION 1.2
#define OM_ROSTER_INTERCEPTOR_AOE 0.0

#define OM_ROSTER_VANGUARD_LAYER_TRANSITION 2.5
#define OM_ROSTER_VANGUARD_AOE 0.0

#define OM_ROSTER_WARDEN_LAYER_TRANSITION 2.0
#define OM_ROSTER_WARDEN_AOE 0.0

#define OM_ROSTER_BOMBARD_LAYER_TRANSITION 4.0
/* OM_ROSTER_BOMBARD_AOE promoted to csrc/om_constants.h (ALG-61, CONST-1). */

#define OM_ROSTER_BASTION_LAYER_TRANSITION 5.0
#define OM_ROSTER_BASTION_AOE 0.0

/* Fallback profile for an unrecognized unit_type (never a roster/custom
 * hit) -- keeps om_unit_spawn from producing a unit that cannot fight or
 * be queried, without inventing roster numbers. */
#define OM_UNIT_FALLBACK_HP 100.0
#define OM_UNIT_FALLBACK_DAMAGE 5.0
#define OM_UNIT_FALLBACK_INTERVAL 1.0
#define OM_UNIT_FALLBACK_RANGE 100.0

/* OM_RETURN_FIRE_FLEE_DIST, OM_ATTACK_MOVE_LEASH_DIST promoted to
 * csrc/om_constants.h (ALG-62/68, CONST-1). */

/* order kinds unit.c itself records (attack-move and attack-target;
 * a plain move and no order at all are read back from tactical_move.c) */
#define OM_ORDER_NONE 0
#define OM_ORDER_ATTACK_MOVE 1
#define OM_ORDER_ATTACK_TARGET 2

/* OM_COMPOSITION_* promoted to csrc/om_constants.h (ALG-75, CONST-1). */

/* S-081's stationary fight loop needs a hard iteration cap so a real bug
 * (e.g. two forces that can never reach each other) fails fast instead of
 * hanging the test process. */
#define OM_TACTICAL_MAX_RUN_TICKS 1000000

/* A run helper that watches for the fight ending gives up once the living
 * units' total HP has not reached a new low for the longest ability cooldown
 * (ALG-63 Barrage, 1800 ticks): a real stalemate (nobody in range of
 * anybody, or Warden aura regen outpacing the damage) then returns in a
 * moment instead of at the 1M-tick cap. */
#define OM_TACTICAL_STALEMATE_TICKS ((uint64_t)OM_ABILITY_BARRAGE_COOLDOWN_TICKS)

/* E-13 R-099-03 (decision A): above OM_TACTICAL_HIGH_LOAD_UNITS live units
 * (hp > 0) each tactical step spans OM_TACTICAL_HIGH_LOAD_PERIOD base ticks
 * (20 -> 10 ticks per second). Neither number has an ALG id or a
 * simulation/config.py name; the bible pins them in prose only. */
#define OM_TACTICAL_HIGH_LOAD_UNITS 1000
#define OM_TACTICAL_HIGH_LOAD_PERIOD 2

/* OM_ABILITY_SURGE_*, OM_ABILITY_INTERCEPT_*, OM_ABILITY_BRACE_*,
 * OM_ABILITY_RALLY_HEAL_AMOUNT/_RADIUS/_COOLDOWN_TICKS,
 * OM_ABILITY_BARRAGE_*, OM_ABILITY_FORTIFY_* promoted to csrc/om_constants.h
 * (ALG-63, CONST-1).
 * OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION 0.5: no ALG/config source; kept local.
 * OM_ABILITY_DAMAGE_REDUCTION_CAP 0.9: no ALG/config source; kept local. */
#define OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION 0.5
#define OM_ABILITY_DAMAGE_REDUCTION_CAP 0.9
/* ALG-60: "after firing the unit's movement pauses ATTACK_BACKSWING_SEC =
 * 0.5" -- OM_ATTACK_BACKSWING_SEC/OM_TACTICAL_TICK_RATE are both already
 * declared in om_constants.h. */
#define OM_BACKSWING_TICKS ((uint32_t)(OM_ATTACK_BACKSWING_SEC * (double)OM_TACTICAL_TICK_RATE))

#define OM_ABILITY_EVENT_BUFFER_CAP 256

#define OM_ABILITY_PHASE_IDLE 0
#define OM_ABILITY_PHASE_WINDUP 1
#define OM_ABILITY_PHASE_ACTIVE 2
#define OM_ABILITY_PHASE_CANCELING 3
#define OM_ABILITY_PHASE_TELEGRAPH 4

/* S-088 render-facing metadata. om_cue_lookup and the Barrage activation
 * site below both read OM_CUE_BARRAGE_TELEGRAPH as their one shared source
 * of truth, so a name looked up by the renderer and the id stamped on the
 * event always agree. */
#define OM_CUE_NONE 0
#define OM_CUE_BARRAGE_TELEGRAPH 1

/* Strike squads render as several small craft sharing one HP bar/position
 * (R-088-01); every other category is a single hull, so 1 is the natural
 * default. */
#define OM_RENDER_CRAFT_COUNT_STRIKE 4
#define OM_RENDER_CRAFT_COUNT_DEFAULT 1

/* R-088-03: silhouette size keyed on category with a clear gap between
 * tiers -- Strike smallest, Line middle, Siege largest, regardless of any
 * per-unit variation within a category. */
#define OM_RENDER_SILHOUETTE_STRIKE 10.0
#define OM_RENDER_SILHOUETTE_LINE 20.0
#define OM_RENDER_SILHOUETTE_SIEGE 30.0

typedef struct {
    int    category;
    double max_hp;
    double base_damage;
    double attack_interval;
    double attack_range;
    double speed;
    double sensor_radius;
    double layer_transition_time;
    double aoe_radius;
} om_unit_type_profile;

typedef struct {
    uint32_t unit_id;
    int      in_use;
    int      unit_type;
    int      category;
    int32_t  faction_id;
    double   x, y;
    uint32_t layer;
    double   hp;
    double   max_hp;
    double   base_damage;
    double   attack_interval;
    double   attack_range;
    double   cooldown;
    uint32_t target_id;
    /* S-086 ability state: OM_ABILITY_PHASE_*, per-phase countdown, whether
     * the phase's bonus is currently granted (distinguishes Brace windup
     * from active/canceling), the ability's own cooldown (distinct from
     * `cooldown` above, which is the ordinary attack timer), and the
     * Bombard's recorded Barrage target. */
    int      ability_phase;
    int      ability_bonus_on;
    uint32_t ability_ticks_remaining;
    double   ability_cooldown;
    double   ability_target_x, ability_target_y;
    /* B10b/S-084 (ALG-60): backswing pause after a landed attack, and the
     * three test-facing forced-reduction flags om_unit_set_brace_active/
     * om_unit_set_fortify_active/om_unit_set_warden_aura_active drive
     * directly (independent of the real Brace/Fortify ability phase or a
     * nearby Warden, so a test can force exactly one reduction term without
     * standing up the whole ability chain). */
    uint32_t backswing_ticks_remaining;
    int      backswing_active;
    int      force_brace_reduction;
    int      force_fortify_reduction;
    int      force_warden_aura_reduction;
    /* S-087/ALG-62 decision state. `order` is unit.c's own record of an
     * attack-move / attack-target (tactical_move.c only knows a destination);
     * `issued_x/y` is the last destination unit.c handed to
     * om_command_move for this unit, so a different destination read back
     * later is recognised as the player's own plain move. `halted` means
     * unit.c is holding the unit still in tactical_move.c
     * (om_unit_engage / a kiting-in-place order). */
    int      order;
    double   order_x, order_y;
    double   issued_x, issued_y;
    int      halted;
    /* R-096-02 (PURSUE_BY_STEERING): the move group an attack-move of two or more units formed (0 for a lone
     * unit) and whether this member has held a target since (R-096-02 rewritten 2026-10-13: nothing ends the group on it;
     * a member resumes toward the point after every engagement). */
    uint32_t am_gid;
    int      am_engaged;
    /* R-096-08: set by om_command_guard (tactical_move.c); the unit holds, fires in range, never walks */
    int      guard;
    int      anchor_set;
    double   anchor_x, anchor_y;
    int      flinching;
    double   flinch_x, flinch_y;
    uint32_t last_attacker;
    int      fire_pending;
    int      stealth;
    /* set each tactical tick while the unit is under an order (move,
     * attack-move, attack-target) or fleeing: a threshold auto-activation
     * (om_ability_autotrigger_scan) is auto-engagement, and the order wins
     * over it (R-087-02); a Brace it started would also pin the unit. */
    int      suppress_auto;
    /* the current Brace was started by the threshold scan, not by a player
     * activation: a later order cancels it (om_tac_unit_ai). */
    int      brace_auto;
    /* the current Fortify was started by the threshold scan, not by a player
     * activation: a later order cancels it (om_tac_unit_ai) per R-087-02.
     * om_unit_effective_speed returns native speed (not 0.4x) when set, so
     * om_command_group_move computes speed_cap at the native rate. */
    int      fortify_auto;
    /* where an attack-target order last saw its target (S-093): refreshed
     * every tick the target is visible to the unit's faction. */
    double   last_seen_x, last_seen_y;
    /* R-084-01: set once the unit has landed an attack; until then the attack
     * is ready without waiting out the first interval. */
    int      fired;
    /* VG K-a: roster tier at spawn (Q-133-02), tick of the last landed attack, kill event already logged */
    uint32_t tier;
    uint64_t fired_tick;
    int      kill_logged;
    /* F5 (R-087-09): the give-up run. giveup_target is the target held while it could not be shot, giveup_ticks the base ticks of that run,
     * giveup_ref the distance to it when the run began (a run restarts when the unit closes in on it by more than 1 wu: the F0 checker's own
     * test). excl_id is the target the unit gave up, ineligible for it until excl_until (base tick) or until the unit has a clear line to it.
     * spot_x/y is the firing spot an idle unit or a guard is walking to (spot_set). All zero at rest; hashed while any is set; not saved
     * (saving them needs OM_SAVE_FORMAT_VERSION and the pipe sidecar bumped, a contract step): a loaded game starts a fresh run. */
    uint32_t giveup_target;
    uint32_t giveup_ticks;
    double   giveup_ref;
    uint32_t excl_id;
    uint64_t excl_until;
    int      spot_set;
    double   spot_x, spot_y;
} om_unit_row;

/* VG K-a tactical event ring: fire, ability and kill events of one om_tactical_step call. */
#define OM_TAC_EVENT_CAP 512
#define OM_TAC_EV_FIRE 0
#define OM_TAC_EV_ABILITY 1
#define OM_TAC_EV_KILL 2
typedef struct {
    int32_t  kind;
    uint32_t a;
    int32_t  b;
    uint64_t tick;
} om_tac_event;

typedef struct {
    uint32_t        type_id;
    int             in_use;
    om_unit_type_profile profile;
} om_custom_type_row;

/* Spatial hash grid over every living unit row, hp > 0 (see om_grid_query_circle
 * in om_internal.h for the contract). Cells are a linked list of unit index + 1
 * (0 ends a list); rebuilt over the current bounding box every tactical tick
 * and updated in place when unit.c moves, spawns or kills a unit. cell_of is
 * OM_GRID_UNLINKED for a unit that is not in the grid. The per-unit arrays are
 * sized by om_tac_reserve. */
typedef struct {
    int       built;
    double    ox, oy, cell;
    int32_t   cols, rows;
    uint32_t *head;
    uint32_t  head_cap;
    uint32_t *next;
    uint32_t *prev;
    uint32_t *cell_of;
    uint32_t *scratch;
    uint32_t *fcnt;   /* per cell, linked units per faction bucket (om_grid_fbucket) */
    uint32_t *khead;  /* per cell, heads of the linked Warden list [2c] and Bastion list [2c+1] (unit index + 1) */
    uint32_t *knext;  /* per unit, next in its kind list */
    uint32_t *kprev;  /* per unit, previous in its kind list */
    uint32_t *dmg;    /* per cell, badly damaged units; read only while dmg_valid */
    int       dmg_valid;
} om_grid;
#define OM_GRID_FBUCKETS 4

typedef struct {
    om_unit_row        *units;
    uint32_t            unit_cap;
    uint32_t            n_units;
    uint32_t            next_unit_id;
    om_custom_type_row  custom_types[OM_MAX_CUSTOM_TYPES];
    uint32_t            n_custom_types;
    /* S-086 ability-event feed: drained on read (om_tick_read_ability_events)
     * -- see the end of the file. */
    om_ability_event    ability_events[OM_ABILITY_EVENT_BUFFER_CAP];
    uint32_t            n_ability_events;
    uint64_t            current_tick;
    /* R-099-03: base ticks the current step spans, recomputed from the live
     * count at the start of every step; 0 (fresh or reset state) reads as 1.
     * Every per-step quantity in this file scales by it so per-second values
     * stay put. Not saved: tactical_state has no write hook, and the next
     * step recomputes it. See also: om_tactical_tick_period. */
    uint32_t            tick_period_ticks;
    /* Sum of every step's period since the last reset: real battle time in
     * base ticks (== current_tick at period 1). See also: om_tactical_base_tick. */
    uint64_t            base_tick;
    int                 abilities_disabled;
    uint64_t            validated_tick;
    om_grid             grid;
    uint32_t           *aura_count;
    /* aura regen scratch: living units sorted by grid cell (aura_cs is the per-cell start) */
    double             *aura_x, *aura_y;
    int32_t            *aura_f;
    uint32_t           *aura_id, *aura_n, *aura_cs;
    uint32_t            aura_cap, aura_cs_cap;
    /* units of each type ever spawned since the last reset (a unit's type
     * never changes): zero means no candidate can match, so the aura and
     * fortify scans in om_unit_damage_reduction are skipped. */
    uint32_t            n_wardens, n_bastions;
    /* events of the last step; ev_closed marks them as read so the next emit or step starts a fresh ring */
    om_tac_event        events[OM_TAC_EVENT_CAP];
    uint32_t            n_events, events_dropped;
    int                 ev_closed;
    uint64_t            ev_tick;   /* tick every event of the running step carries; 0 outside a step */
} om_tac_state;

static void om_tac_ev_emit(om_tac_state *st, int32_t kind, uint32_t a, int32_t b) {
    if (st->ev_closed) { st->n_events = 0; st->events_dropped = 0; st->ev_closed = 0; }
    if (st->n_events >= OM_TAC_EVENT_CAP) { st->events_dropped++; return; }
    st->events[st->n_events].kind = kind;
    st->events[st->n_events].a = a;
    st->events[st->n_events].b = b;
    st->events[st->n_events].tick = st->ev_tick ? st->ev_tick : st->current_tick + 1;
    st->n_events++;
}

static void om_tac_release_arrays(om_tac_state *st) {
    free(st->units);
    free(st->aura_count);
    free(st->aura_x);
    free(st->aura_y);
    free(st->aura_f);
    free(st->aura_id);
    free(st->aura_n);
    free(st->aura_cs);
    free(st->grid.head);
    free(st->grid.fcnt);
    free(st->grid.khead);
    free(st->grid.knext);
    free(st->grid.kprev);
    free(st->grid.dmg);
    free(st->grid.next);
    free(st->grid.prev);
    free(st->grid.cell_of);
    free(st->grid.scratch);
}

static void om_tac_state_free(void *p) {
    if (p) om_tac_release_arrays((om_tac_state *)p);
    free(p);
}

/* Grows every per-unit array to hold at least `need` units (doubling, capped
 * at OM_MAX_UNITS). Rows move when the arrays grow: never keep an om_unit_row
 * pointer across a spawn. Returns 0 when `need` exceeds the cap or an
 * allocation fails, leaving the state as it was. */
static int om_tac_reserve(om_tac_state *st, uint32_t need) {
    uint32_t cap = st->unit_cap ? st->unit_cap : OM_UNITS_INITIAL_CAP;
    void *p;
    if (need <= st->unit_cap) return 1;
    if (need > OM_MAX_UNITS) return 0;
    while (cap < need) cap *= 2;
    if (cap > OM_MAX_UNITS) cap = OM_MAX_UNITS;
    if (!(p = realloc(st->units, (size_t)cap * sizeof(om_unit_row)))) return 0;
    st->units = (om_unit_row *)p;
    if (!(p = realloc(st->aura_count, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->aura_count = (uint32_t *)p;
    if (!(p = realloc(st->grid.next, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->grid.next = (uint32_t *)p;
    if (!(p = realloc(st->grid.prev, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->grid.prev = (uint32_t *)p;
    if (!(p = realloc(st->grid.knext, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->grid.knext = (uint32_t *)p;
    if (!(p = realloc(st->grid.kprev, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->grid.kprev = (uint32_t *)p;
    if (!(p = realloc(st->grid.cell_of, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->grid.cell_of = (uint32_t *)p;
    if (!(p = realloc(st->grid.scratch, (size_t)cap * sizeof(uint32_t)))) return 0;
    st->grid.scratch = (uint32_t *)p;
    st->unit_cap = cap;
    return 1;
}

/* Lazily calloc's the per-world tactical state into w->tactical_state on
 * first use and registers the free hook om_world_free calls; every other
 * call returns the existing pointer. Needs a non-const om_world* since it
 * writes w->tactical_state -- om_unit_get_hp (const om_world*) goes
 * through om_tac_ro instead, which never allocates. */
static uint32_t om_unit_save_size(const om_world *w);
static void om_unit_save_write(const om_world *w, uint8_t *out);
static int om_unit_save_read(om_world *w, const uint8_t *buf, uint32_t len);

static om_tac_state *om_tac(om_world *w) {
    om_tac_state *st = (om_tac_state *)w->tactical_state;
    if (!st) {
        st = (om_tac_state *)calloc(1, sizeof(om_tac_state));
        st->next_unit_id = 1;
        w->tactical_state = st;
        w->tactical_state_free = om_tac_state_free;
        w->tactical_state_size = om_unit_save_size;
        w->tactical_state_write = om_unit_save_write;
        w->tactical_state_read = om_unit_save_read;
    }
    return st;
}

void om_tac_event_push(om_world *w, int kind, int a, int b) {
    om_tac_ev_emit(om_tac(w), kind, (uint32_t)a, b);
}

/* Read-only: returns the existing tactical state, or NULL if none has been
 * allocated yet -- never allocates, so it is safe to call through a const
 * om_world*. */
static om_tac_state *om_tac_ro(const om_world *w) {
    return (om_tac_state *)w->tactical_state;
}

static uint32_t om_tac_period(const om_tac_state *st) {
    return st->tick_period_ticks ? st->tick_period_ticks : 1;
}

/* Called at the top of every step: the boundary at which the period may change. */
static void om_tac_update_period(om_tac_state *st) {
    uint32_t i, live = 0;
    for (i = 0; i < st->n_units; i++) {
        if (st->units[i].in_use && st->units[i].hp > 0.0) live++;
    }
    st->tick_period_ticks = live > OM_TACTICAL_HIGH_LOAD_UNITS ? OM_TACTICAL_HIGH_LOAD_PERIOD : 1;
}

/* A countdown in base ticks advanced by one step of `period` base ticks. */
static uint32_t om_ticks_down(uint32_t remaining, uint32_t period) {
    return remaining > period ? remaining - period : 0;
}

static const om_unit_type_profile OM_BUILTIN_PROFILES[OM_UNIT_TYPE_COUNT] = {
    [OM_UT_RAIDER] = {
        .category = OM_CAT_STRIKE, .max_hp = OM_ROSTER_RAIDER_HP,
        .base_damage = OM_ROSTER_RAIDER_DAMAGE, .attack_interval = OM_ROSTER_RAIDER_INTERVAL,
        .attack_range = OM_ROSTER_RAIDER_RANGE, .speed = OM_ROSTER_RAIDER_SPEED,
        .sensor_radius = OM_ROSTER_RAIDER_SENSOR, .layer_transition_time = OM_ROSTER_RAIDER_LAYER_TRANSITION,
        .aoe_radius = OM_ROSTER_RAIDER_AOE,
    },
    [OM_UT_INTERCEPTOR] = {
        .category = OM_CAT_STRIKE, .max_hp = OM_ROSTER_INTERCEPTOR_HP,
        .base_damage = OM_ROSTER_INTERCEPTOR_DAMAGE, .attack_interval = OM_ROSTER_INTERCEPTOR_INTERVAL,
        .attack_range = OM_ROSTER_INTERCEPTOR_RANGE, .speed = OM_ROSTER_INTERCEPTOR_SPEED,
        .sensor_radius = OM_ROSTER_INTERCEPTOR_SENSOR, .layer_transition_time = OM_ROSTER_INTERCEPTOR_LAYER_TRANSITION,
        .aoe_radius = OM_ROSTER_INTERCEPTOR_AOE,
    },
    [OM_UT_VANGUARD] = {
        .category = OM_CAT_LINE, .max_hp = OM_ROSTER_VANGUARD_HP,
        .base_damage = OM_ROSTER_VANGUARD_DAMAGE, .attack_interval = OM_ROSTER_VANGUARD_INTERVAL,
        .attack_range = OM_ROSTER_VANGUARD_RANGE, .speed = OM_ROSTER_VANGUARD_SPEED,
        .sensor_radius = OM_ROSTER_VANGUARD_SENSOR, .layer_transition_time = OM_ROSTER_VANGUARD_LAYER_TRANSITION,
        .aoe_radius = OM_ROSTER_VANGUARD_AOE,
    },
    [OM_UT_WARDEN] = {
        .category = OM_CAT_LINE, .max_hp = OM_ROSTER_WARDEN_HP,
        .base_damage = OM_ROSTER_WARDEN_DAMAGE, .attack_interval = OM_ROSTER_WARDEN_INTERVAL,
        .attack_range = OM_ROSTER_WARDEN_RANGE, .speed = OM_ROSTER_WARDEN_SPEED,
        .sensor_radius = OM_ROSTER_WARDEN_SENSOR, .layer_transition_time = OM_ROSTER_WARDEN_LAYER_TRANSITION,
        .aoe_radius = OM_ROSTER_WARDEN_AOE,
    },
    [OM_UT_BOMBARD] = {
        .category = OM_CAT_SIEGE, .max_hp = OM_ROSTER_BOMBARD_HP,
        .base_damage = OM_ROSTER_BOMBARD_DAMAGE, .attack_interval = OM_ROSTER_BOMBARD_INTERVAL,
        .attack_range = OM_ROSTER_BOMBARD_RANGE, .speed = OM_ROSTER_BOMBARD_SPEED,
        .sensor_radius = OM_ROSTER_BOMBARD_SENSOR, .layer_transition_time = OM_ROSTER_BOMBARD_LAYER_TRANSITION,
        .aoe_radius = OM_ROSTER_BOMBARD_AOE,
    },
    [OM_UT_BASTION] = {
        .category = OM_CAT_SIEGE, .max_hp = OM_ROSTER_BASTION_HP,
        .base_damage = OM_ROSTER_BASTION_DAMAGE, .attack_interval = OM_ROSTER_BASTION_INTERVAL,
        .attack_range = OM_ROSTER_BASTION_RANGE, .speed = OM_ROSTER_BASTION_SPEED,
        .sensor_radius = OM_ROSTER_BASTION_SENSOR, .layer_transition_time = OM_ROSTER_BASTION_LAYER_TRANSITION,
        .aoe_radius = OM_ROSTER_BASTION_AOE,
    },
};

/* unit ids are dense from 1 and never reused (om_unit_spawn_internal and
 * om_tactical_reset advance/reset next_unit_id and n_units together), so
 * an id maps straight to its row. */
static om_unit_row *om_registry_find_in(om_tac_state *st, uint32_t unit_id) {
    om_unit_row *row;
    if (!st || unit_id == 0 || unit_id > st->n_units) return NULL;
    row = &st->units[unit_id - 1];
    return (row->in_use && row->unit_id == unit_id) ? row : NULL;
}

static const om_unit_type_profile *om_get_builtin_profile(int unit_type) {
    if (unit_type < 0 || unit_type >= OM_UNIT_TYPE_COUNT) return NULL;
    return &OM_BUILTIN_PROFILES[unit_type];
}

/* Builtin roster entries are compile-time constants (no per-world state);
 * only a custom registration needs the per-world tactical state. */
static const om_unit_type_profile *om_get_profile(om_world *w, int unit_type) {
    const om_unit_type_profile *builtin = om_get_builtin_profile(unit_type);
    om_tac_state *st;
    uint32_t i;
    if (builtin) return builtin;
    st = om_tac(w);
    for (i = 0; i < st->n_custom_types; i++) {
        if (st->custom_types[i].in_use
            && st->custom_types[i].type_id == (uint32_t)unit_type) {
            return &st->custom_types[i].profile;
        }
    }
    return NULL;
}

/* G5 (R-164-02, Q-008-03): reach by unit type. A target on another layer is fought only when its offset from the
 * attacker is within the attacker type's reach, and range, damage and area damage are scaled by the settings of that
 * signed offset; same layer is always reachable at 1.0. Offsets are counted from the attacker, for splash victims too. */
enum { OM_REACH_RANGE, OM_REACH_DAMAGE, OM_REACH_AREA, OM_REACH_FAMILIES };
#define OM_REACH_MAX_OFFSET 4

static int om_tac_in_reach(const om_world *w, const om_unit_row *a, const om_unit_row *t) {
    uint32_t up, down;
    if (a->layer == t->layer) return 1;
    if (om_unit_profile_reach(w, a->unit_type, &up, &down) != 0) return 0;
    return t->layer > a->layer ? t->layer - a->layer <= up : a->layer - t->layer <= down;
}

static double om_tac_offset_param(const om_world *w, int family, int up, uint32_t n) {
    static const om_tac_param first[OM_REACH_FAMILIES] = { OM_TP_RANGE_UP_1, OM_TP_DAMAGE_UP_1, OM_TP_AREA_UP_1 };
    if (n == 0 || n > OM_REACH_MAX_OFFSET) return 1.0;
    return om_tactical_get_param(w, (om_tac_param)((int)first[family] + (up ? 0 : OM_REACH_MAX_OFFSET) + (int)n - 1));
}

static double om_tac_offset_mult(const om_world *w, int family, const om_unit_row *a, const om_unit_row *t) {
    if (a->layer == t->layer) return 1.0;
    return t->layer > a->layer ? om_tac_offset_param(w, family, 1, t->layer - a->layer)
                               : om_tac_offset_param(w, family, 0, a->layer - t->layer);
}

static int om_tac_dist_le(double dx, double dy, double r) {
    return (dx * dx + dy * dy) <= (r * r);
}

static int32_t om_grid_coord(double v, double origin, double cell, int32_t dim) {
    double t = (v - origin) / cell;
    if (!(t > 0.0)) return 0;
    if (t >= (double)dim) return dim - 1;
    return (int32_t)t;
}

static uint32_t om_grid_cell_of_row(const om_grid *g, const om_unit_row *u) {
    return (uint32_t)om_grid_coord(u->y, g->oy, g->cell, g->rows) * (uint32_t)g->cols
           + (uint32_t)om_grid_coord(u->x, g->ox, g->cell, g->cols);
}

/* Faction bucket: neutral (-1) 0, factions 0 and 1 buckets 1 and 2, every
 * higher faction the shared last bucket, which is never proven absent. */
static uint32_t om_grid_fbucket(int32_t faction) {
    if (faction < 0) return 0;
    return (uint32_t)faction + 1 < OM_GRID_FBUCKETS ? (uint32_t)faction + 1 : OM_GRID_FBUCKETS - 1;
}

/* 0 only when the cell provably holds no linked unit of a faction other than
 * `faction`. */
static int om_grid_cell_has_other_faction(const om_grid *g, uint32_t cell, int32_t faction) {
    const uint32_t *c = &g->fcnt[(size_t)cell * OM_GRID_FBUCKETS];
    uint32_t b = om_grid_fbucket(faction), k;
    if (b == OM_GRID_FBUCKETS - 1) return 1;
    for (k = 0; k < OM_GRID_FBUCKETS; k++) if (k != b && c[k]) return 1;
    return 0;
}

/* Kind list a unit belongs to: 0 Warden, 1 Bastion, -1 neither. */
static int om_grid_kind(const om_unit_row *u) {
    return u->unit_type == OM_UT_WARDEN ? 0 : u->unit_type == OM_UT_BASTION ? 1 : -1;
}

static void om_grid_link(om_tac_state *st, uint32_t i) {
    om_grid *g = &st->grid;
    uint32_t cell = om_grid_cell_of_row(g, &st->units[i]);
    int kind;
    g->fcnt[(size_t)cell * OM_GRID_FBUCKETS + om_grid_fbucket(st->units[i].faction_id)]++;
    g->cell_of[i] = cell;
    g->prev[i] = 0;
    g->next[i] = g->head[cell];
    if (g->head[cell]) g->prev[g->head[cell] - 1] = i + 1;
    g->head[cell] = i + 1;
    kind = om_grid_kind(&st->units[i]);
    if (kind >= 0) {
        uint32_t *kh = &g->khead[(size_t)cell * 2 + (uint32_t)kind];
        g->kprev[i] = 0;
        g->knext[i] = *kh;
        if (*kh) g->kprev[*kh - 1] = i + 1;
        *kh = i + 1;
    }
}

static void om_grid_unlink(om_tac_state *st, uint32_t i) {
    om_grid *g = &st->grid;
    int kind;
    g->fcnt[(size_t)g->cell_of[i] * OM_GRID_FBUCKETS + om_grid_fbucket(st->units[i].faction_id)]--;
    if (g->prev[i]) g->next[g->prev[i] - 1] = g->next[i];
    else g->head[g->cell_of[i]] = g->next[i];
    if (g->next[i]) g->prev[g->next[i] - 1] = g->prev[i];
    kind = om_grid_kind(&st->units[i]);
    if (kind >= 0) {
        if (g->kprev[i]) g->knext[g->kprev[i] - 1] = g->knext[i];
        else g->khead[(size_t)g->cell_of[i] * 2 + (uint32_t)kind] = g->knext[i];
        if (g->knext[i]) g->kprev[g->knext[i] - 1] = g->kprev[i];
    }
}

/* Living, in the sense every caller filters on: `hp <= 0.0` is dead, so a NaN
 * hp still counts as living. */
static int om_grid_living(const om_unit_row *u) {
    return !(u->hp <= 0.0);
}

/* Call after any write to a unit's hp: links a revived unit, unlinks a dead
 * one, so a query never returns a unit the all-pairs scan would have skipped
 * as dead and never misses one it would have accepted. */
static void om_grid_sync(om_tac_state *st, uint32_t i) {
    om_grid *g = &st->grid;
    int living = om_grid_living(&st->units[i]);
    if (!g->built) return;
    if (living && g->cell_of[i] == OM_GRID_UNLINKED) {
        om_grid_link(st, i);
    } else if (!living && g->cell_of[i] != OM_GRID_UNLINKED) {
        om_grid_unlink(st, i);
        g->cell_of[i] = OM_GRID_UNLINKED;
    }
}

static void om_grid_rebuild(om_tac_state *st) {
    om_grid *g = &st->grid;
    double minx = 0.0, miny = 0.0, maxx = 0.0, maxy = 0.0, span, cell = OM_GRID_CELL_SIZE;
    uint32_t i, ncells;
    int any = 0;
    for (i = 0; i < st->n_units; i++) {
        const om_unit_row *u = &st->units[i];
        if (!u->in_use || !om_grid_living(u)) continue;
        if (!any) { minx = maxx = u->x; miny = maxy = u->y; any = 1; continue; }
        if (u->x < minx) minx = u->x;
        if (u->x > maxx) maxx = u->x;
        if (u->y < miny) miny = u->y;
        if (u->y > maxy) maxy = u->y;
    }
    g->built = 0;
    if (!any) return;
    span = (maxx - minx > maxy - miny) ? maxx - minx : maxy - miny;
    if (span > cell * (double)(OM_GRID_MAX_DIM - 1)) cell = span / (double)(OM_GRID_MAX_DIM - 1);
    g->ox = minx; g->oy = miny; g->cell = cell;
    g->cols = om_grid_coord(maxx, minx, cell, OM_GRID_MAX_DIM) + 1;
    g->rows = om_grid_coord(maxy, miny, cell, OM_GRID_MAX_DIM) + 1;
    ncells = (uint32_t)g->cols * (uint32_t)g->rows;
    if (ncells > g->head_cap) {
        free(g->head);
        free(g->fcnt);
        free(g->khead);
        free(g->dmg);
        g->head = (uint32_t *)malloc((size_t)ncells * sizeof(uint32_t));
        g->fcnt = (uint32_t *)malloc((size_t)ncells * OM_GRID_FBUCKETS * sizeof(uint32_t));
        g->dmg = (uint32_t *)malloc((size_t)ncells * sizeof(uint32_t));
        g->khead = (uint32_t *)malloc((size_t)ncells * 2 * sizeof(uint32_t));
        g->head_cap = (g->head && g->fcnt && g->dmg && g->khead) ? ncells : 0;
        if (!g->head_cap) return;
    }
    memset(g->head, 0, (size_t)ncells * sizeof(uint32_t));
    memset(g->fcnt, 0, (size_t)ncells * OM_GRID_FBUCKETS * sizeof(uint32_t));
    memset(g->khead, 0, (size_t)ncells * 2 * sizeof(uint32_t));
    for (i = st->n_units; i-- > 0;) {
        if (st->units[i].in_use && om_grid_living(&st->units[i])) om_grid_link(st, i);
        else g->cell_of[i] = OM_GRID_UNLINKED;
    }
    g->built = 1;
}

static void om_grid_move(om_tac_state *st, uint32_t i) {
    om_grid *g = &st->grid;
    if (!g->built || g->cell_of[i] == OM_GRID_UNLINKED) return;
    if (om_grid_cell_of_row(g, &st->units[i]) == g->cell_of[i]) return;
    om_grid_unlink(st, i);
    om_grid_link(st, i);
}

/* Contract (om_internal.h om_grid_iter): visits every unit row whose cached
 * position lies within r of (x, y), inclusive, in cell order (row-major,
 * within a cell the last-linked unit first). */
/* Iterator filter bits in `done` (bit 0 is the finished flag): bits 1..30 hold
 * faction + 1 for a faction filter, with OM_ITER_OTHER also set the iterator
 * is the "any faction but" one. Either way a cell the filter proves empty is
 * skipped; units within a visited cell keep their order. */
#define OM_ITER_OTHER 0x80000000u
#define OM_ITER_FMASK 0x7ffffffeu

static uint32_t om_grid_iter_head(const om_grid *g, const om_grid_iter *it) {
    uint32_t cell = (uint32_t)it->cy * (uint32_t)g->cols + (uint32_t)it->cx, d = (uint32_t)it->done;
    int32_t faction = (int32_t)((d & OM_ITER_FMASK) >> 1) - 1;
    if (d & OM_ITER_OTHER) {
        if (!om_grid_cell_has_other_faction(g, cell, faction)) return 0;
    } else if (d & OM_ITER_FMASK) {
        if (!g->fcnt[(size_t)cell * OM_GRID_FBUCKETS + om_grid_fbucket(faction)]) return 0;
    }
    return g->head[cell];
}

static void om_grid_iter_begin_st(om_grid_iter *it, om_tac_state *st, double x, double y, double r) {
    om_grid *g = &st->grid;
    double reach = (r < 0.0 ? -r : r) + OM_GRID_PAD;
    if (!g->built) om_grid_rebuild(st);
    it->state = st;
    it->x = x; it->y = y; it->r = r;
    it->done = !g->built;
    it->cur = 0;
    if (it->done) return;
    it->cx0 = om_grid_coord(x - reach, g->ox, g->cell, g->cols);
    it->cx1 = om_grid_coord(x + reach, g->ox, g->cell, g->cols);
    it->cy1 = om_grid_coord(y + reach, g->oy, g->cell, g->rows);
    it->cx = it->cx0;
    it->cy = om_grid_coord(y - reach, g->oy, g->cell, g->rows);
    it->cur = om_grid_iter_head(g, it);
}

/* Counts the linked units of kind list `kind` (0 Warden, 1 Bastion) of
 * `faction` within r of (x, y): the cells and distance test of
 * om_grid_iter_begin_st, walking only that kind's list. The bastion scan
 * (`want_phase` >= 0) stops at the first unit in that ability phase, as the
 * all-units scan did. Counts and any-of do not depend on the order. */
static uint32_t om_grid_kind_scan(om_tac_state *st, int kind, int32_t faction, int want_phase, double x, double y, double r) {
    const om_grid *g = &st->grid;
    double reach = (r < 0.0 ? -r : r) + OM_GRID_PAD;
    int32_t cx0, cx1, cy0, cy1, cx, cy;
    uint32_t n = 0, id;
    if (!g->built) om_grid_rebuild(st);
    if (!g->built) return 0;
    cx0 = om_grid_coord(x - reach, g->ox, g->cell, g->cols);
    cx1 = om_grid_coord(x + reach, g->ox, g->cell, g->cols);
    cy0 = om_grid_coord(y - reach, g->oy, g->cell, g->rows);
    cy1 = om_grid_coord(y + reach, g->oy, g->cell, g->rows);
    for (cy = cy0; cy <= cy1; cy++) {
        for (cx = cx0; cx <= cx1; cx++) {
            uint32_t cell = (uint32_t)cy * (uint32_t)g->cols + (uint32_t)cx;
            for (id = g->khead[(size_t)cell * 2 + (uint32_t)kind]; id; id = g->knext[id - 1]) {
                const om_unit_row *cand = &st->units[id - 1];
                if (cand->hp <= 0.0) continue;
                if (cand->faction_id != faction) continue;
                if (want_phase >= 0 && cand->ability_phase != want_phase) continue;
                if (!om_tac_dist_le(cand->x - x, cand->y - y, r)) continue;
                n++;
                if (want_phase >= 0) return n;
            }
        }
    }
    return n;
}

uint32_t om_grid_iter_next(om_grid_iter *it) {
    om_tac_state *st = (om_tac_state *)it->state;
    const om_grid *g;
    if (it->done & 1) return 0;
    g = &st->grid;
    for (;;) {
        while (it->cur) {
            const om_unit_row *u = &st->units[it->cur - 1];
            it->cur = g->next[it->cur - 1];
            if (!((uint32_t)it->done & OM_ITER_OTHER) && ((uint32_t)it->done & OM_ITER_FMASK)
                && u->faction_id != (int32_t)(((uint32_t)it->done & OM_ITER_FMASK) >> 1) - 1) continue;
            if (om_tac_dist_le(u->x - it->x, u->y - it->y, it->r)) return u->unit_id;
        }
        if (++it->cx > it->cx1) {
            it->cx = it->cx0;
            if (++it->cy > it->cy1) { it->done |= 1; return 0; }
        }
        it->cur = om_grid_iter_head(g, it);
    }
}

void om_grid_iter_begin(om_grid_iter *it, om_world *w, double x, double y, double r) {
    om_grid_iter_begin_st(it, om_tac(w), x, y, r);
}

/* Faction-filtered iterator: `done` bit 0 is the finished flag, bits 1.. hold
 * faction + 1 (0 = unfiltered), so om_grid_iter needs no new field. A negative
 * or out-of-range faction matches nothing. */
void om_grid_iter_begin_faction(om_grid_iter *it, om_world *w, int32_t faction, double x, double y, double r) {
    om_grid_iter_begin_st(it, om_tac(w), x, y, r);
    if (faction < 0 || faction >= 0x3fffffff) { it->done |= 1; return; }
    it->done |= (int)((uint32_t)(faction + 1) << 1);
    if (it->cur) it->cur = om_grid_iter_head(&om_tac(w)->grid, it);
}

/* Internal: like the faction iterator but over units of every faction except
 * `faction` (callers still test each unit). */
static void om_grid_iter_begin_other_st(om_grid_iter *it, om_tac_state *st, int32_t faction, double x, double y, double r) {
    om_grid_iter_begin_st(it, st, x, y, r);
    if (it->done) return;
    it->done = (int)(OM_ITER_OTHER | ((uint32_t)(faction < 0 ? 0 : faction < 0x3fffffff ? faction + 1 : 0x3fffffff) << 1));
    it->cur = om_grid_iter_head(&st->grid, it);
}

static void om_grid_sift_down(uint32_t *a, uint32_t root, uint32_t n) {
    for (;;) {
        uint32_t child = 2 * root + 1, t;
        if (child >= n) return;
        if (child + 1 < n && a[child + 1] > a[child]) child++;
        if (a[root] >= a[child]) return;
        t = a[root]; a[root] = a[child]; a[child] = t;
        root = child;
    }
}

/* Ascending unit ids: insertion sort for the usual handful of candidates,
 * heapsort past OM_GRID_INSERTION_SORT_MAX (ids are unique, so the order is
 * total and no stability question arises). */
static void om_grid_sort_ids(uint32_t *a, uint32_t n) {
    uint32_t i, j;
    if (n > OM_GRID_INSERTION_SORT_MAX) {
        for (i = n / 2; i-- > 0;) om_grid_sift_down(a, i, n);
        for (i = n; i-- > 1;) {
            uint32_t t = a[0]; a[0] = a[i]; a[i] = t;
            om_grid_sift_down(a, 0, i);
        }
        return;
    }
    for (i = 1; i < n; i++) {
        uint32_t v = a[i];
        for (j = i; j > 0 && a[j - 1] > v; j--) a[j] = a[j - 1];
        a[j] = v;
    }
}

static uint32_t om_grid_query_st(om_tac_state *st, double x, double y, double r, uint32_t *out_ids, uint32_t max) {
    uint32_t *buf = st->grid.scratch;
    uint32_t n = 0, i, id;
    om_grid_iter it;
    om_grid_iter_begin_st(&it, st, x, y, r);
    while ((id = om_grid_iter_next(&it)) != 0) buf[n++] = id;
    om_grid_sort_ids(buf, n);
    for (i = 0; i < n && i < max; i++) out_ids[i] = buf[i];
    return n;
}

uint32_t om_grid_query_circle(om_world *w, double x, double y, double r, uint32_t *out_ids, uint32_t max) {
    return om_grid_query_st(om_tac(w), x, y, r, out_ids, max);
}

uint32_t om_grid_query_circle_faction(om_world *w, int32_t faction, double x, double y, double r, uint32_t *out_ids, uint32_t max) {
    uint32_t *buf = om_tac(w)->grid.scratch;
    uint32_t n = 0, i, id;
    om_grid_iter it;
    om_grid_iter_begin_faction(&it, w, faction, x, y, r);
    while ((id = om_grid_iter_next(&it)) != 0) buf[n++] = id;
    om_grid_sort_ids(buf, n);
    for (i = 0; i < n && i < max; i++) out_ids[i] = buf[i];
    return n;
}

/* See om_internal.h: for tactical_move.c, which owns a unit's live position
 * and writes it outside unit.c's own refresh (teleport, set_pos, move sync). */
void om_tac_unit_sync_position(om_world *w, uint32_t unit_id, double x, double y) {
    om_tac_state *st = w ? (om_tac_state *)w->tactical_state : NULL;
    om_unit_row *u = om_registry_find_in(st, unit_id);
    if (!u) return;
    u->x = x;
    u->y = y;
    om_grid_move(st, unit_id - 1);
}

/* See also: the extern of the same name in tactical_move.c, the only caller: the cross-over of a layer transfer
 * (R-004-02) sets the unit's effective layer. The grid is not layered, so nothing is re-bucketed. */
void om_tac_unit_set_layer(om_world *w, uint32_t unit_id, uint32_t layer) {
    om_tac_state *st = w ? (om_tac_state *)w->tactical_state : NULL;
    om_unit_row *u = om_registry_find_in(st, unit_id);
    if (!u || layer >= OM_LAYER_COUNT) return;
    u->layer = layer;
}

static uint32_t om_unit_spawn_internal(om_world *w, int unit_type, int32_t faction_id,
                                        double x, double y, uint32_t layer) {
    const om_unit_type_profile *prof;
    om_unit_row *row;
    om_tac_state *st = om_tac(w);
    if (om_terrain_present(w) && om_unit_profile_movement_kind(w, unit_type) == OM_MOVE_WALKING) {
        om_slope sl;
        int band = om_terrain_band_at(w, x, y);
        if (om_terrain_slope_at(w, x, y, &sl) >= 0) {
            double along = (x - sl.mx) * (sl.x1 - sl.x0) + (y - sl.my) * (sl.y1 - sl.y0);
            band = along >= 0.0 ? sl.upper_band : sl.lower_band;
        }
        if (band < 1 || !om_terrain_walkable_at(w, x, y)) return 0;
        layer = (uint32_t)(band - 1);
    }
    if (!om_tac_reserve(st, st->n_units + 1)) return 0;
    prof = om_get_profile(w, unit_type);
    row = &st->units[st->n_units++];
    memset(row, 0, sizeof(*row));
    row->unit_id = st->next_unit_id++;
    row->in_use = 1;
    row->unit_type = unit_type;
    row->faction_id = faction_id;
    row->x = x;
    row->y = y;
    row->layer = layer;
    row->target_id = 0;
    row->cooldown = 0.0;
    row->tier = om_faction_unit_tier(w, faction_id);
    if (prof) {
        row->category = prof->category;
        row->max_hp = prof->max_hp;
        row->hp = prof->max_hp;
        row->base_damage = prof->base_damage;
        row->attack_interval = prof->attack_interval;
        row->attack_range = prof->attack_range;
    } else {
        row->category = OM_CAT_STRIKE;
        row->max_hp = OM_UNIT_FALLBACK_HP;
        row->hp = OM_UNIT_FALLBACK_HP;
        row->base_damage = OM_UNIT_FALLBACK_DAMAGE;
        row->attack_interval = OM_UNIT_FALLBACK_INTERVAL;
        row->attack_range = OM_UNIT_FALLBACK_RANGE;
    }
    if (unit_type == OM_UT_WARDEN) st->n_wardens++;
    if (unit_type == OM_UT_BASTION) st->n_bastions++;
    st->grid.cell_of[st->n_units - 1] = OM_GRID_UNLINKED;
    om_grid_sync(st, st->n_units - 1);
    return row->unit_id;
}

/* R-081-03's "Siege exception to Strike-beats-Siege": the Bastion (anchor
 * role) never takes a category-advantage multiplier above 1.0 -- every
 * other matchup (including every other Siege unit) uses the plain
 * OM_CATEGORY_MULTIPLIER_* matrix unchanged. */
static double om_resolve_hit_multiplier(om_world *w, int attacker_category, const om_unit_row *target) {
    double mult = om_tactical_category_multiplier(w, attacker_category, target->category);
    if (target->unit_type == OM_UT_BASTION && mult > 1.0) mult = 1.0;
    return mult;
}

static int om_tac_pursue(const om_world *w) {
    return om_tactical_get_param(w, OM_TP_PURSUE_BY_STEERING) != 0.0;
}

/* A188 (R-087-05, R-096-03): the leash tests the unit's own distance from its anchor, never the target's.
 * Switch 0 keeps the old target-distance test: old path kept as baseline only, deleted at end of Phase E.
 * See also: simulation/movement.py _update_attack_move_state */
static double om_tac_leash(const om_world *w, const om_unit_row *u);
static int om_tac_leash_broken(const om_world *w, const om_unit_row *u, const om_unit_row *t) {
    const om_unit_row *p = om_tac_pursue(w) ? u : t;
    return !om_tac_dist_le(p->x - u->anchor_x, p->y - u->anchor_y, om_tac_leash(w, u));
}

/* H-057 (DEC-leash-param-2026-11-01): the leash and the acquisition radius are the unit's own type's
 * max(sensor_radius, attack_range); OM_TP_ATTACK_MOVE_LEASH 0 (the default) means that, non-zero overrides in wu. */
static double om_tac_leash(const om_world *w, const om_unit_row *u) {
    double p = om_tactical_get_param(w, OM_TP_ATTACK_MOVE_LEASH), r;
    const om_unit_type_profile *prof;
    if (p != 0.0) return p;
    /* Switch 0 (the pre-H-057 baseline arm) keeps the old literal 200 wu, so its goldens stand (H-057, DEC-leash-param-2026-11-01).
     * See also: OM_ATTACK_MOVE_LEASH_DIST is now 0.0 in om_constants.h */
    if (!om_tac_pursue(w)) return OM_ATTACK_MOVE_LEASH_BASELINE;
    prof = om_get_profile((om_world *)w, u->unit_type);
    r = prof ? prof->sensor_radius : 0.0;
    return r > u->attack_range ? r : u->attack_range;
}

/* R-087-06: the unit returns fire at the lowest-id living same-layer attacker
 * (a cross-layer one only while no same-layer one has hit it). With pursuit
 * by steering off, the last writer wins as it did. */
static void om_tac_note_attacker(om_world *w, om_tac_state *st, om_unit_row *target, const om_unit_row *attacker) {
    const om_unit_row *cur = om_registry_find_in(st, target->last_attacker);
    if (cur && cur->hp > 0.0 && om_tac_pursue(w)) {
        int cur_same = cur->layer == target->layer, new_same = attacker->layer == target->layer;
        if (cur_same != new_same ? cur_same : cur->unit_id < attacker->unit_id) return;
    }
    /* PP baseline only (switch = 0); deleted with the two movement switches at the end of Phase E (A140) */
    /* See also: the pursue branch above is the new path (R-087-06); here the last writer wins */
    target->last_attacker = attacker->unit_id;
}

static void om_tactical_apply_hit(om_world *w, om_unit_row *attacker, om_unit_row *target) {
    double mult = om_resolve_hit_multiplier(w, attacker->category, target);
    double output_mult = om_unit_output_multiplier(w, attacker->unit_id);
    double reduction = om_unit_damage_reduction(w, target->unit_id);
    double dmg = attacker->base_damage * mult * output_mult * (1.0 - reduction) * om_tac_offset_mult(w, OM_REACH_DAMAGE, attacker, target);
    target->hp -= dmg;
    if (target->hp < 0.0) target->hp = 0.0;
    om_grid_sync(om_tac(w), target->unit_id - 1);
    om_tac_note_attacker(w, om_tac(w), target, attacker);
    attacker->cooldown = 0.0;
    attacker->fired = 1;
    attacker->backswing_ticks_remaining = OM_BACKSWING_TICKS;
    attacker->backswing_active = 1;
}

static double om_tactical_total_hp(const om_tac_state *st) {
    uint32_t i;
    double total = 0.0;
    for (i = 0; i < st->n_units; i++) {
        if (st->units[i].in_use && st->units[i].hp > 0.0) total += st->units[i].hp;
    }
    return total;
}

static int om_tactical_multiple_factions_alive(const om_tac_state *st) {
    int32_t first_faction = 0;
    int have_first = 0;
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        const om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        if (!have_first) { first_faction = u->faction_id; have_first = 1; continue; }
        if (u->faction_id != first_faction) return 1;
    }
    return 0;
}

/* R-083-03/R-084-01, Q-084-01 closed 2026-10-20 "no stacking": one Warden in
 * range gives the reduction 0.10; two or more give the same 0.10. */
static double om_warden_aura_reduction_for(om_tac_state *st, const om_unit_row *target) {
    if (st->n_wardens == 0) {
        if (!st->grid.built) om_grid_rebuild(st);
        return 0.0;
    }
    return om_grid_kind_scan(st, 0, target->faction_id, -1, target->x, target->y, (double)OM_WARDEN_AURA_RADIUS) > 0
        ? OM_WARDEN_AURA_DAMAGE_REDUCTION : 0.0;
}

/* Each Warden counts the same-faction living units in its circle. The counts are
 * integers, so the walk order does not matter; the candidate cells, the distance
 * test and the faction test are those of om_grid_iter_begin_st. Candidates are
 * copied cell by cell into flat arrays first so a query reads no unit rows. */
static int om_aura_flatten(om_tac_state *st) {
    om_grid *g = &st->grid;
    uint32_t cell, ncells, n = 0, id;
    void *p;
    if (!g->built) om_grid_rebuild(st);
    if (!g->built) return 0;
    ncells = (uint32_t)g->cols * (uint32_t)g->rows;
    if (ncells + 1 > st->aura_cs_cap) {
        if (!(p = realloc(st->aura_cs, ((size_t)ncells + 1) * sizeof(uint32_t)))) return 0;
        st->aura_cs = (uint32_t *)p;
        st->aura_cs_cap = ncells + 1;
    }
    if (st->unit_cap > st->aura_cap) {
        size_t c = st->unit_cap;
        if (!(p = realloc(st->aura_x, c * sizeof(double)))) return 0;
        st->aura_x = (double *)p;
        if (!(p = realloc(st->aura_y, c * sizeof(double)))) return 0;
        st->aura_y = (double *)p;
        if (!(p = realloc(st->aura_f, c * sizeof(int32_t)))) return 0;
        st->aura_f = (int32_t *)p;
        if (!(p = realloc(st->aura_id, c * sizeof(uint32_t)))) return 0;
        st->aura_id = (uint32_t *)p;
        if (!(p = realloc(st->aura_n, c * sizeof(uint32_t)))) return 0;
        st->aura_n = (uint32_t *)p;
        st->aura_cap = st->unit_cap;
    }
    for (cell = 0; cell < ncells; cell++) {
        st->aura_cs[cell] = n;
        for (id = g->head[cell]; id; id = g->next[id - 1], n++) {
            const om_unit_row *u = &st->units[id - 1];
            st->aura_x[n] = u->x;
            st->aura_y[n] = u->y;
            st->aura_f[n] = u->faction_id;
            st->aura_id[n] = id - 1;
            st->aura_n[n] = 0;
        }
    }
    st->aura_cs[ncells] = n;
    return 1;
}

/* R-083-03: the heal does not stack either: one Warden in range heals 0.075 a tick, a second adds nothing (Q-084-01). */
static void om_tactical_apply_aura_regen(om_world *w) {
    om_tac_state *st = om_tac(w);
    uint32_t i, k;
    memset(st->aura_count, 0, (size_t)st->n_units * sizeof(uint32_t));
    if (st->n_wardens > 0 && om_aura_flatten(st)) {
        const om_grid *g = &st->grid;
        const double r = (double)OM_WARDEN_AURA_RADIUS, reach = r + OM_GRID_PAD;
        for (i = 0; i < st->n_units; i++) {
            const om_unit_row *warden = &st->units[i];
            int32_t cx0, cx1, cy0, cy1, cy;
            if (!warden->in_use || warden->hp <= 0.0 || warden->unit_type != OM_UT_WARDEN) continue;
            cx0 = om_grid_coord(warden->x - reach, g->ox, g->cell, g->cols);
            cx1 = om_grid_coord(warden->x + reach, g->ox, g->cell, g->cols);
            cy0 = om_grid_coord(warden->y - reach, g->oy, g->cell, g->rows);
            cy1 = om_grid_coord(warden->y + reach, g->oy, g->cell, g->rows);
            for (cy = cy0; cy <= cy1; cy++) {
                uint32_t lo = st->aura_cs[(size_t)cy * (size_t)g->cols + (size_t)cx0];
                uint32_t hi = st->aura_cs[(size_t)cy * (size_t)g->cols + (size_t)cx1 + 1];
                for (k = lo; k < hi; k++) {
                    if (st->aura_f[k] == warden->faction_id
                        && om_tac_dist_le(st->aura_x[k] - warden->x, st->aura_y[k] - warden->y, r)) st->aura_n[k]++;
                }
            }
        }
        for (k = 0; k < st->aura_cs[(size_t)g->cols * (size_t)g->rows]; k++) st->aura_count[st->aura_id[k]] = st->aura_n[k];
    }
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (st->aura_count[i] > 0) {
            u->hp += OM_WARDEN_AURA_REPAIR_RATE * (double)om_tac_period(st);
            if (u->hp > u->max_hp) u->hp = u->max_hp;
        }
    }
}

/* ---- end B10-1/B10-2 tactical state ---- */

/* ---- B10-3: S-086 one ability each ----
 * Two independent activation paths onto the same per-unit ability state:
 * om_command_activate_ability (manual, checks only cooldown/already-active,
 * Brace excepted) and om_ability_autotrigger_scan (runs every tactical
 * tick over every unit regardless of faction; Intercept only ever fires
 * this way). Ability id == unit_type (1:1, OMAbility in the test file
 * matches OMUnitType by declared order). */

/* Visible to the unit's faction: any living friendly (itself included) can
 * see it through fog.c's om_fog_faction_sees, and it is not stealthed. */
static int om_tac_faction_sees(om_world *w, const om_unit_row *self, const om_unit_row *t) {
    if (t->stealth) return 0;
    if (om_unit_can_see(w, self->unit_id, t->unit_id)) return 1;
    return om_fog_faction_sees(w, self->faction_id, t->unit_id);
}

/* G3 (R-093-02, R-008-04): acquisition, pursuit, return fire and fire use the side's visible set. Switch 0 is the
 * PP baseline only (old path kept as baseline only, deleted at end of Phase E, A140). */
static int om_tac_by_sight(const om_world *w) {
    return om_tactical_get_param(w, OM_TP_TARGET_BY_SIGHT) != 0.0;
}

/* The target is usable by this unit: always at switch 0, else only when its side sees it. */
static int om_tac_may_act_on(om_world *w, const om_unit_row *self, const om_unit_row *t) {
    return !om_tac_by_sight(w) || om_tac_faction_sees(w, self, t);
}

/* The unit ids ascend in the old sorted scan and only a strictly smaller
 * distance replaced the best, so the answer is the lowest id at the minimum
 * distance; the unordered grid walk reaches it by comparing (d2, id). */
static om_unit_row *om_tac_nearest_enemy_within_range(om_world *w, om_tac_state *st, const om_unit_row *self, double range) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0;
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_other_st(&it, st, self->faction_id, self->x, self->y, range);
    while ((id = om_grid_iter_next(&it)) != 0) {
        om_unit_row *cand = &st->units[id - 1];
        double dx, dy, d2;
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        dx = cand->x - self->x; dy = cand->y - self->y; d2 = dx * dx + dy * dy;
        if (best && (d2 > best_d2 || (d2 == best_d2 && id > best->unit_id))) continue;
        if (!om_tac_may_act_on(w, self, cand)) continue;
        best = cand; best_d2 = d2;
    }
    return best;
}

/* Cell range a circle query covers (the same one om_grid_iter_begin_st
 * computes) plus the cell holding the query centre, which callers walk first:
 * a near hit there lets the rest be skipped or pruned. Returns 0 when there
 * is no grid. */
typedef struct {
    int32_t cx0, cx1, cy0, cy1, hx, hy;
} om_cell_span;

static int om_grid_span(om_tac_state *st, double x, double y, double r, om_cell_span *sp) {
    const om_grid *g = &st->grid;
    double reach = (r < 0.0 ? -r : r) + OM_GRID_PAD;
    if (!g->built) om_grid_rebuild(st);
    if (!g->built) return 0;
    sp->cx0 = om_grid_coord(x - reach, g->ox, g->cell, g->cols);
    sp->cx1 = om_grid_coord(x + reach, g->ox, g->cell, g->cols);
    sp->cy0 = om_grid_coord(y - reach, g->oy, g->cell, g->rows);
    sp->cy1 = om_grid_coord(y + reach, g->oy, g->cell, g->rows);
    sp->hx = om_grid_coord(x, g->ox, g->cell, g->cols);
    sp->hy = om_grid_coord(y, g->oy, g->cell, g->rows);
    return 1;
}

/* Squared distance from (x, y) to the rectangle a grid cell covers, widened
 * by OM_GRID_PAD; the outermost cells also hold every unit clamped into them
 * from beyond the grid box, so they are unbounded outward. */
static double om_grid_cell_gap2(const om_grid *g, int32_t cx, int32_t cy, double x, double y) {
    double dx = 0.0, dy = 0.0, lo, hi;
    if (cx > 0) {
        lo = g->ox + (double)cx * g->cell - OM_GRID_PAD;
        if (x < lo) dx = lo - x;
    }
    if (cx < g->cols - 1) {
        hi = g->ox + (double)(cx + 1) * g->cell + OM_GRID_PAD;
        if (x > hi) dx = x - hi;
    }
    if (cy > 0) {
        lo = g->oy + (double)cy * g->cell - OM_GRID_PAD;
        if (y < lo) dy = lo - y;
    }
    if (cy < g->rows - 1) {
        hi = g->oy + (double)(cy + 1) * g->cell + OM_GRID_PAD;
        if (y > hi) dy = y - hi;
    }
    return dx * dx + dy * dy;
}

static int om_tac_enemy_in_cell(om_tac_state *st, const om_unit_row *self, double range, uint32_t cell) {
    const om_grid *g = &st->grid;
    uint32_t cur;
    if (!om_grid_cell_has_other_faction(g, cell, self->faction_id)) return 0;
    for (cur = g->head[cell]; cur; cur = g->next[cur - 1]) {
        const om_unit_row *cand = &st->units[cur - 1];
        if (!om_tac_dist_le(cand->x - self->x, cand->y - self->y, range)) continue;
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        return 1;
    }
    return 0;
}

/* Any-of, so the walk order is free: the unit's own cell first, cells the
 * circle cannot reach skipped. */
static int om_tac_enemy_within_range(om_tac_state *st, const om_unit_row *self, double range) {
    const om_grid *g = &st->grid;
    om_cell_span sp;
    int32_t cx, cy;
    if (!om_grid_span(st, self->x, self->y, range, &sp)) return 0;
    if (om_tac_enemy_in_cell(st, self, range, (uint32_t)sp.hy * (uint32_t)g->cols + (uint32_t)sp.hx)) return 1;
    for (cy = sp.cy0; cy <= sp.cy1; cy++) {
        for (cx = sp.cx0; cx <= sp.cx1; cx++) {
            if (cx == sp.hx && cy == sp.hy) continue;
            if (om_grid_cell_gap2(g, cx, cy, self->x, self->y) > range * range) continue;
            if (om_tac_enemy_in_cell(st, self, range, (uint32_t)cy * (uint32_t)g->cols + (uint32_t)cx)) return 1;
        }
    }
    return 0;
}

static int om_tac_enemy_category_within(om_tac_state *st, const om_unit_row *self, int category, double range) {
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_other_st(&it, st, self->faction_id, self->x, self->y, range);
    while ((id = om_grid_iter_next(&it)) != 0) {
        const om_unit_row *cand = &st->units[id - 1];
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        if (cand->category != category) continue;
        return 1;
    }
    return 0;
}

static int om_tac_badly_damaged_candidate(const om_unit_row *self, const om_unit_row *cand) {
    if (cand->hp <= 0.0) return 0;
    if (cand->faction_id != self->faction_id) return 0;
    return !(cand->hp >= cand->max_hp * OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION);
}

/* Per-cell count of units below the Rally hp threshold (any faction), built
 * once at the top of the autotrigger scan. Nothing in that scan moves a unit
 * or lowers hp (Rally only heals), so a cell counted 0 stays 0 for the whole
 * scan; a stale nonzero count only costs a walk. */
static void om_grid_build_damage(om_tac_state *st) {
    om_grid *g = &st->grid;
    uint32_t c, cur, ncells;
    g->dmg_valid = 0;
    if (!g->built) om_grid_rebuild(st);
    if (!g->built) return;
    ncells = (uint32_t)g->cols * (uint32_t)g->rows;
    for (c = 0; c < ncells; c++) {
        uint32_t n = 0;
        for (cur = g->head[c]; cur; cur = g->next[cur - 1]) {
            const om_unit_row *u = &st->units[cur - 1];
            if (!(u->hp <= 0.0) && !(u->hp >= u->max_hp * OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION)) n++;
        }
        g->dmg[c] = n;
    }
    g->dmg_valid = 1;
}

static int om_tac_badly_damaged_friendly_within(om_tac_state *st, const om_unit_row *self, double range) {
    const om_grid *g = &st->grid;
    uint32_t id;
    om_grid_iter it;
    if (g->dmg_valid) {
        om_cell_span sp;
        int32_t cx, cy;
        if (!om_grid_span(st, self->x, self->y, range, &sp)) return 0;
        for (cy = sp.cy0; cy <= sp.cy1; cy++) {
            for (cx = sp.cx0; cx <= sp.cx1; cx++) {
                uint32_t cell = (uint32_t)cy * (uint32_t)g->cols + (uint32_t)cx, cur;
                if (!g->dmg[cell]) continue;
                for (cur = g->head[cell]; cur; cur = g->next[cur - 1]) {
                    const om_unit_row *cand = &st->units[cur - 1];
                    if (om_tac_dist_le(cand->x - self->x, cand->y - self->y, range) && om_tac_badly_damaged_candidate(self, cand)) return 1;
                }
            }
        }
        return 0;
    }
    om_grid_iter_begin_st(&it, st, self->x, self->y, range);
    while ((id = om_grid_iter_next(&it)) != 0) {
        if (om_tac_badly_damaged_candidate(self, &st->units[id - 1])) return 1;
    }
    return 0;
}

static int om_tac_count_friendlies_within(om_tac_state *st, const om_unit_row *self, double range) {
    uint32_t id;
    int n = 0;
    om_grid_iter it;
    om_grid_iter_begin_st(&it, st, self->x, self->y, range);
    while ((id = om_grid_iter_next(&it)) != 0) {
        const om_unit_row *cand = &st->units[id - 1];
        if (cand->hp <= 0.0) continue;
        if (cand == self) continue;
        if (cand->faction_id != self->faction_id) continue;
        n++;
    }
    return n;
}

/* Every activation (manual or auto) appends one event, tagged with the
 * tick it will be visible on: current_tick + 1, since an event created by
 * a command issued between tactical_step calls (or by the autotrigger scan
 * running inside the current call, before current_tick's own increment)
 * both become observable once the in-flight tick finishes advancing --
 * this is what makes test_R_086_09's `evt.tick == om_tactical_tick(w)`
 * hold for a Surge activated before any step and read after exactly one. */
static void om_ability_emit_event(om_tac_state *st, const om_unit_row *u, double target_x, double target_y,
                                   uint32_t duration, uint32_t telegraph_ticks, uint32_t cue_id, double radius) {
    om_ability_event *evt;
    om_tac_ev_emit(st, OM_TAC_EV_ABILITY, u->unit_id, u->unit_type);
    if (st->n_ability_events >= OM_ABILITY_EVENT_BUFFER_CAP) return;
    evt = &st->ability_events[st->n_ability_events++];
    evt->tick = st->current_tick + 1;
    evt->unit_id = u->unit_id;
    evt->ability_id = u->unit_type;
    evt->target_x = target_x;
    evt->target_y = target_y;
    evt->duration = duration;
    evt->telegraph_ticks = telegraph_ticks;
    evt->cue_id = cue_id;
    evt->radius = radius;
}

static void om_ability_start_surge(om_tac_state *st, om_unit_row *u) {
    u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
    u->ability_ticks_remaining = OM_ABILITY_SURGE_DURATION_TICKS;
    u->ability_bonus_on = 1;
    u->ability_cooldown = 0.0;
    om_ability_emit_event(st, u, u->x, u->y, OM_ABILITY_SURGE_DURATION_TICKS, 0, OM_CUE_NONE, 0.0);
}

/* R-086-03: reactivating while braced (windup, active, or already
 * canceling) does not reject or stack -- it cancels the current brace
 * through a mirrored 40-tick window (ability_bonus_on frozen at whatever
 * it already was: 0 mid-windup, 1 once active), ending fully idle when
 * that window elapses; see test_R_086_03's post-reactivation assertions. */
static void om_ability_start_or_cancel_brace(om_tac_state *st, om_unit_row *u) {
    if (u->ability_phase == OM_ABILITY_PHASE_IDLE) {
        u->ability_phase = OM_ABILITY_PHASE_WINDUP;
        u->ability_ticks_remaining = OM_ABILITY_BRACE_WINDUP_TICKS;
        u->ability_bonus_on = 0;
    } else {
        u->ability_phase = OM_ABILITY_PHASE_CANCELING;
        u->ability_ticks_remaining = OM_ABILITY_BRACE_WINDUP_TICKS;
    }
    u->ability_cooldown = OM_ABILITY_BRACE_COOLDOWN_TICKS;
    om_ability_emit_event(st, u, u->x, u->y, OM_ABILITY_BRACE_WINDUP_TICKS, 0, OM_CUE_NONE, 0.0);
}

static void om_ability_do_rally(om_tac_state *st, om_unit_row *u) {
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_st(&it, st, u->x, u->y, OM_ABILITY_RALLY_RADIUS);
    while ((id = om_grid_iter_next(&it)) != 0) {
        om_unit_row *cand = &st->units[id - 1];
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id != u->faction_id) continue;
        cand->hp += OM_ABILITY_RALLY_HEAL_AMOUNT;
        if (cand->hp > cand->max_hp) cand->hp = cand->max_hp;
    }
    u->ability_cooldown = OM_ABILITY_RALLY_COOLDOWN_TICKS;
    om_ability_emit_event(st, u, u->x, u->y, 0, 0, OM_CUE_NONE, OM_ABILITY_RALLY_RADIUS);
}

static void om_ability_start_barrage(om_tac_state *st, om_unit_row *u, double target_x, double target_y) {
    u->ability_phase = OM_ABILITY_PHASE_TELEGRAPH;
    u->ability_ticks_remaining = OM_ABILITY_BARRAGE_TELEGRAPH_TICKS;
    u->ability_target_x = target_x;
    u->ability_target_y = target_y;
    u->ability_cooldown = 0.0;
    om_ability_emit_event(st, u, target_x, target_y, OM_ABILITY_BARRAGE_TELEGRAPH_TICKS,
                          OM_ABILITY_BARRAGE_TELEGRAPH_TICKS,
                          om_cue_lookup("cue_barrage_telegraph"), OM_ABILITY_BARRAGE_RADIUS);
}

/* R-086-05/ALG-61: base * 3.0 through the S-081 category multiplier
 * (om_resolve_hit_multiplier, same helper the ordinary attack path uses,
 * including the Bastion siege exception), unit-id order, running total
 * capped at 4 * (base * 3.0). */
static void om_ability_resolve_barrage_damage(om_world *w, om_tac_state *st, om_unit_row *u) {
    double per_hit_base = u->base_damage * OM_ABILITY_BARRAGE_DAMAGE_MULT;
    double cap = per_hit_base * OM_AOE_DAMAGE_CAP_MULTIPLIER;
    double total = 0.0;
    uint32_t ids[st->n_units + 1];
    uint32_t j, n = om_grid_query_st(st, u->ability_target_x, u->ability_target_y, OM_ABILITY_BARRAGE_RADIUS, ids, st->n_units);
    for (j = 0; j < n; j++) {
        om_unit_row *cand = &st->units[ids[j] - 1];
        double mult, dmg, remaining;
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == u->faction_id) continue;
        if (!om_tac_in_reach(w, u, cand)) continue;
        if (total >= cap) break;
        mult = om_resolve_hit_multiplier(w, u->category, cand);
        dmg = per_hit_base * mult * om_tac_offset_mult(w, OM_REACH_AREA, u, cand);
        remaining = cap - total;
        if (dmg > remaining) dmg = remaining;
        cand->hp -= dmg;
        if (cand->hp < 0.0) cand->hp = 0.0;
        om_grid_sync(st, cand->unit_id - 1);
        total += dmg;
    }
}

static void om_ability_start_fortify(om_tac_state *st, om_unit_row *u) {
    u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
    u->ability_ticks_remaining = OM_ABILITY_FORTIFY_DURATION_TICKS;
    u->ability_bonus_on = 1;
    u->ability_cooldown = OM_ABILITY_FORTIFY_COOLDOWN_TICKS;
    om_ability_emit_event(st, u, u->x, u->y, OM_ABILITY_FORTIFY_DURATION_TICKS, 0, OM_CUE_NONE, OM_FORTIFY_RADIUS);
}

/* Cancel an auto-started Fortify when a player order arrives (R-087-02).
 * No cooldown: the player never chose it, so they pay nothing.  The scan
 * may re-trigger on the next idle tick if the unit is still near 2+
 * friendlies.  Emits a duration-0 event to signal termination to the
 * renderer.  fortify_auto is cleared. */
static void om_ability_cancel_fortify(om_tac_state *st, om_unit_row *u) {
    u->ability_phase = OM_ABILITY_PHASE_IDLE;
    u->ability_bonus_on = 0;
    u->ability_cooldown = 0.0;
    u->fortify_auto = 0;
    om_ability_emit_event(st, u, u->x, u->y, 0, 0, OM_CUE_NONE, OM_FORTIFY_RADIUS);
}

/* R-086-02: never manually activated -- always rejected here, regardless
 * of cooldown/phase. R-086-03: Brace is the one manual-activation special
 * case (never rejected while eligible at all -- reactivating while braced
 * cancels and restarts instead). Every other ability follows the plain
 * "off cooldown and not already in progress" rule (R-086-07). */
static int om_ability_can_manually_activate(const om_unit_row *u) {
    if (u->unit_type == OM_UT_INTERCEPTOR) return 0;
    if (u->unit_type == OM_UT_VANGUARD) return 1;
    if (u->ability_phase != OM_ABILITY_PHASE_IDLE) return 0;
    if (u->ability_cooldown > 0.0) return 0;
    return 1;
}

static void om_ability_manual_activate(om_world *w, om_tac_state *st, om_unit_row *u, double target_x, double target_y) {
    switch (u->unit_type) {
        case OM_UT_RAIDER:   om_ability_start_surge(st, u); break;
        case OM_UT_VANGUARD: om_ability_start_or_cancel_brace(st, u); break;
        case OM_UT_WARDEN:   om_ability_do_rally(st, u); break;
        case OM_UT_BOMBARD:  om_ability_start_barrage(st, u, target_x, target_y); break;
        case OM_UT_BASTION:
            om_ability_start_fortify(st, u);
            u->fortify_auto = 0;
            break;
        default: (void)w; break;
    }
}

/* R-086-08: runs every tactical tick over every unit regardless of
 * faction -- the mechanism is not faction-gated, only the threshold is.
 * Intercept always fires this way (never manually); the other five are
 * eligible here too, using each ability owner's own attack_range for the
 * "enemy in range" threshold (Surge/Brace/Barrage), a damaged friendly in
 * OM_ABILITY_RALLY_RADIUS (Rally), or 2+ friendlies in OM_FORTIFY_RADIUS
 * (Fortify). */
static void om_ability_autotrigger_scan(om_world *w, om_tac_state *st) {
    uint32_t i;
    if (st->n_wardens) om_grid_build_damage(st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        if (u->ability_phase != OM_ABILITY_PHASE_IDLE) continue;
        if (u->ability_cooldown > 0.0) continue;
        if (u->suppress_auto) continue;
        switch (u->unit_type) {
            case OM_UT_INTERCEPTOR:
                if (om_tac_enemy_category_within(st, u, OM_CAT_STRIKE, OM_INTERCEPT_DETECTION_RADIUS)) {
                    u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
                    u->ability_bonus_on = 1;
                    om_ability_emit_event(st, u, u->x, u->y, 0, 0, OM_CUE_NONE, OM_INTERCEPT_DETECTION_RADIUS);
                }
                break;
            case OM_UT_RAIDER:
                if (om_tac_enemy_within_range(st, u, u->attack_range)) om_ability_start_surge(st, u);
                break;
            case OM_UT_VANGUARD:
                if (om_tac_enemy_within_range(st, u, u->attack_range)) {
                    om_ability_start_or_cancel_brace(st, u);
                    u->brace_auto = 1;
                }
                break;
            case OM_UT_WARDEN:
                if (om_tac_badly_damaged_friendly_within(st, u, OM_ABILITY_RALLY_RADIUS)) om_ability_do_rally(st, u);
                break;
            case OM_UT_BOMBARD: {
                om_unit_row *tgt = om_tac_nearest_enemy_within_range(w, st, u, u->attack_range);
                if (tgt) om_ability_start_barrage(st, u, tgt->x, tgt->y);
                break;
            }
            case OM_UT_BASTION:
                if (om_tac_count_friendlies_within(st, u, OM_FORTIFY_RADIUS) >= 2) {
                    om_ability_start_fortify(st, u);
                    u->fortify_auto = 1;
                }
                break;
            default: break;
        }
    }
    st->grid.dmg_valid = 0;
}

static void om_ability_tick_surge(om_unit_row *u, uint32_t period) {
    if (u->ability_phase != OM_ABILITY_PHASE_ACTIVE) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining = om_ticks_down(u->ability_ticks_remaining, period);
    } else {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
        u->ability_cooldown = OM_ABILITY_SURGE_COOLDOWN_TICKS;
    }
}

/* R-086-02: Intercept lasts the engagement: it ends once no enemy Strike unit
 * is within detection range, and the 600 tick cooldown starts. */
static void om_ability_tick_intercept(om_tac_state *st, om_unit_row *u) {
    if (u->ability_phase != OM_ABILITY_PHASE_ACTIVE) return;
    if (om_tac_enemy_category_within(st, u, OM_CAT_STRIKE, OM_INTERCEPT_DETECTION_RADIUS)) return;
    u->ability_phase = OM_ABILITY_PHASE_IDLE;
    u->ability_bonus_on = 0;
    u->ability_cooldown = OM_ABILITY_INTERCEPT_COOLDOWN_TICKS;
}

static void om_ability_tick_brace(om_unit_row *u, uint32_t period) {
    if (u->ability_phase != OM_ABILITY_PHASE_WINDUP && u->ability_phase != OM_ABILITY_PHASE_CANCELING) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining = om_ticks_down(u->ability_ticks_remaining, period);
        return;
    }
    if (u->ability_phase == OM_ABILITY_PHASE_WINDUP) {
        u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
        u->ability_bonus_on = 1;
    } else {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
    }
}

static void om_ability_tick_barrage(om_world *w, om_tac_state *st, om_unit_row *u, uint32_t period) {
    if (u->ability_phase != OM_ABILITY_PHASE_TELEGRAPH) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining = om_ticks_down(u->ability_ticks_remaining, period);
        return;
    }
    om_ability_resolve_barrage_damage(w, st, u);
    u->ability_phase = OM_ABILITY_PHASE_IDLE;
    u->ability_cooldown = OM_ABILITY_BARRAGE_COOLDOWN_TICKS;
}

static void om_ability_tick_fortify(om_unit_row *u, uint32_t period) {
    if (u->ability_phase != OM_ABILITY_PHASE_ACTIVE) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining = om_ticks_down(u->ability_ticks_remaining, period);
    } else {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
        u->fortify_auto = 0;
    }
}

/* Cooldown decrements once per tactical step (by the step's period in base
 * ticks), first, so a value freshly
 * set by this same call's autotrigger/expiry processing (Surge, Barrage,
 * Rally set theirs on completion; Brace/Fortify set theirs at activation)
 * is never decremented before the caller can observe it. */
static void om_ability_advance_all(om_world *w) {
    om_tac_state *st = om_tac(w);
    uint32_t i, period = om_tac_period(st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use) continue;
        if (u->ability_cooldown > 0.0) u->ability_cooldown -= (double)period;
    }
    if (!st->abilities_disabled) om_ability_autotrigger_scan(w, st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        switch (u->unit_type) {
            case OM_UT_RAIDER:   om_ability_tick_surge(u, period); break;
            case OM_UT_INTERCEPTOR: om_ability_tick_intercept(st, u); break;
            case OM_UT_VANGUARD: om_ability_tick_brace(u, period); break;
            case OM_UT_BOMBARD:  om_ability_tick_barrage(w, st, u, period); break;
            case OM_UT_BASTION:  om_ability_tick_fortify(u, period); break;
            default: break;
        }
    }
    st->current_tick++;
}

/* ---- end B10-3 ability system ---- */

/* ALG-60 backswing: counts down the pause a landed hit (om_unit_deal_damage,
 * om_unit_fire_aoe_attack) puts on its attacker. backswing_active reports
 * "still paused as of the tick just simulated" -- it stays 1 through the
 * tick that consumes the last remaining count, and only reads 0 starting
 * the tick after, so a hit landed with OM_BACKSWING_TICKS remaining reads
 * in-backswing for exactly that many om_tactical_step calls. */
static void om_tactical_advance_backswing(om_tac_state *st) {
    uint32_t i, period = om_tac_period(st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use) continue;
        if (u->backswing_ticks_remaining > 0) {
            u->backswing_ticks_remaining = om_ticks_down(u->backswing_ticks_remaining, period);
            u->backswing_active = 1;
        } else {
            u->backswing_active = 0;
        }
    }
}

/* ---- S-087/ALG-62: target acquisition, return fire, flinch, and the
 * hold/chase handshake with csrc/tactical_move.c ----
 * tactical_move.c owns a unit's route (destination, plain-move stepping,
 * facing); unit.c owns what a unit decides to shoot. Positions are read out
 * of tactical_move.c once per tactical step (om_unit_get_pos) into the
 * row cache, and any position unit.c itself moves (flinch, approach) is
 * written back through om_unit_set_pos, so the two never disagree. While
 * unit.c is holding a unit (in range of a target, or approaching by its own
 * stepping) it engages the unit there so tactical_move.c does not also
 * move it; om_tac_release hands the route back. See also:
 * csrc/tactical_move.c om_move_sync -- steps off om_tactical_tick(w). */

static int om_tac_hostile(const om_unit_row *a, const om_unit_row *b) {
    return a->faction_id >= 0 && b->faction_id >= 0 && a->faction_id != b->faction_id;
}

static int om_tac_noncombat(const om_unit_row *u) {
    return u->faction_id < 0 || u->unit_type == OM_UT_SUPPLY || u->unit_type == OM_UT_EVACUATION;
}

static int om_tac_within(const om_unit_row *a, const om_unit_row *b, double r) {
    return om_tac_dist_le(a->x - b->x, a->y - b->y, r);
}

/* Targeting cohort slot: the Python staggers by its 0-based uid and the C ids are uid + 1, so under
 * PURSUE_BY_STEERING the slot is (id - 1) % count; PP baseline (switch = 0) keeps id % count, deleted with the
 * two movement switches at the end of Phase E (A140). */
static uint32_t om_unit_cohort_slot(const om_world *w, uint32_t unit_id) {
    return (om_tac_pursue(w) ? unit_id - 1 : unit_id) % OM_TARGETING_COHORT_COUNT;
}

/* In attack range of the target: same layer at the plain range, another layer only within reach, at the range times
 * the offset's multiplier. */
static int om_tac_in_range(const om_world *w, const om_unit_row *a, const om_unit_row *t) {
    if (a->layer == t->layer) return om_tac_within(a, t, a->attack_range);
    return om_tac_in_reach(w, a, t) && om_tac_within(a, t, a->attack_range * om_tac_offset_mult(w, OM_REACH_RANGE, a, t));
}

/* A196: the policy for this unit's side; faction 1's own id wins unless unset (-1), then OM_TP_TARGET_POLICY. */
static int om_tac_most_damaged_for(const om_world *w, const om_unit_row *self) {
    double p = self->faction_id == 1 ? om_tactical_get_param(w, OM_TP_TARGET_POLICY_FACTION_1) : -1.0;
    if (p < 0.0) p = om_tactical_get_param(w, OM_TP_TARGET_POLICY);
    return p == 1.0;
}

/* Acquisition for a unit whose type has reach: the better of the same-layer pick `same` and the best cross-layer
 * candidate in reach and in range at its offset (nearest, or per TARGET_POLICY 1 the most damaged). The cross-layer
 * pick replaces the same-layer one only when strictly better by OM_TIE_EPSILON. */
static om_unit_row *om_tac_pick_across(om_world *w, om_tac_state *st, const om_unit_row *self, om_unit_row *same) {
    uint32_t up, down, n, id;
    double widest = 0.0, best_frac = 0.0, best_d2 = 0.0, same_frac, same_d2 = 0.0, m;
    int most_damaged = om_tac_most_damaged_for(w, self);
    om_unit_row *best = NULL;
    om_grid_iter it;
    if (om_unit_profile_reach(w, self->unit_type, &up, &down) != 0 || (up == 0 && down == 0)) return same;
    for (n = 1; n <= OM_REACH_MAX_OFFSET; n++) {
        if (n <= up && (m = om_tac_offset_param(w, OM_REACH_RANGE, 1, n)) > widest) widest = m;
        if (n <= down && (m = om_tac_offset_param(w, OM_REACH_RANGE, 0, n)) > widest) widest = m;
    }
    if (widest <= 0.0) return same;
    om_grid_iter_begin_other_st(&it, st, self->faction_id, self->x, self->y, self->attack_range * widest);
    while ((id = om_grid_iter_next(&it)) != 0) {
        om_unit_row *cand = &st->units[id - 1];
        double dx = cand->x - self->x, dy = cand->y - self->y, d2 = dx * dx + dy * dy;
        double frac = cand->max_hp > 0.0 ? cand->hp / cand->max_hp : 1.0;
        if (cand->hp <= 0.0 || cand->stealth || cand->layer == self->layer || !om_tac_hostile(self, cand) || cand->unit_id == self->excl_id) continue;
        if (!om_tac_in_range(w, self, cand)) continue;
        if (!om_tac_may_act_on(w, self, cand)) continue;
        if (best) {
            int better = most_damaged
                ? (frac < best_frac - OM_TIE_EPSILON || (frac <= best_frac + OM_TIE_EPSILON && (d2 < best_d2 || (d2 == best_d2 && id < best->unit_id))))
                : (d2 < best_d2 || (d2 == best_d2 && id < best->unit_id));
            if (!better) continue;
        }
        best = cand; best_frac = frac; best_d2 = d2;
    }
    if (!best) return same;
    if (!same) return best;
    same_d2 = (same->x - self->x) * (same->x - self->x) + (same->y - self->y) * (same->y - self->y);
    same_frac = same->max_hp > 0.0 ? same->hp / same->max_hp : 1.0;
    if (most_damaged) {
        return (best_frac < same_frac - OM_TIE_EPSILON
                || (best_frac <= same_frac + OM_TIE_EPSILON && best_d2 < same_d2 - OM_TIE_EPSILON)) ? best : same;
    }
    return best_d2 < same_d2 - OM_TIE_EPSILON ? best : same;
}

/* The reference scan: candidates in ascending id order, a later one replaces
 * the best only when closer by more than OM_TIE_EPSILON. */
static om_unit_row *om_tac_nearest_hostile_ordered(om_tac_state *st, const om_unit_row *self, double radius) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0;
    uint32_t ids[st->n_units + 1];
    uint32_t j, n = om_grid_query_st(st, self->x, self->y, radius, ids, st->n_units);
    for (j = 0; j < n; j++) {
        om_unit_row *cand = &st->units[ids[j] - 1];
        double dx, dy, d2;
        if (cand->hp <= 0.0 || cand->stealth) continue;
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer || cand->unit_id == self->excl_id) continue;
        dx = cand->x - self->x; dy = cand->y - self->y; d2 = dx * dx + dy * dy;
        if (!best || d2 < best_d2 - OM_TIE_EPSILON) { best = cand; best_d2 = d2; }
    }
    return best;
}

typedef struct {
    om_unit_row *best;
    double       best_d2, next_d2;
    int          have_next;
} om_nearest_acc;

static void om_tac_nearest_scan_cell(om_tac_state *st, const om_unit_row *self, double radius, uint32_t cell, om_nearest_acc *acc) {
    const om_grid *g = &st->grid;
    uint32_t cur;
    if (!om_grid_cell_has_other_faction(g, cell, self->faction_id)) return;
    for (cur = g->head[cell]; cur; cur = g->next[cur - 1]) {
        om_unit_row *cand = &st->units[cur - 1];
        double dx = cand->x - self->x, dy = cand->y - self->y, d2;
        if (cand->hp <= 0.0 || cand->stealth) continue;
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer) continue;
        if (cand->unit_id == self->excl_id) continue;   /* F5: a target the unit gave up (R-087-09) */
        if (!om_tac_dist_le(dx, dy, radius)) continue;
        d2 = dx * dx + dy * dy;
        if (!acc->best) {
            acc->best = cand; acc->best_d2 = d2;
        } else if (d2 < acc->best_d2) {
            acc->next_d2 = acc->best_d2; acc->have_next = 1;
            acc->best = cand; acc->best_d2 = d2;
        } else if (d2 == acc->best_d2) {
            if (cand->unit_id < acc->best->unit_id) acc->best = cand;
        } else if (!acc->have_next || d2 < acc->next_d2) {
            acc->next_d2 = d2; acc->have_next = 1;
        }
    }
}

/* Same answer as the reference scan without sorting the candidates. When no
 * candidate lies within OM_TIE_SCAN_WINDOW above the minimum distance m, the
 * candidates are the ones at exactly m and ones too far to hold the best
 * against a first candidate at m, so the reference scan ends on the lowest id
 * at m. A candidate inside the window makes the answer depend on the whole
 * id-order chain, and the reference scan runs instead. The unit's own cell is
 * walked first, then every other cell in range unless the cell's nearest edge
 * is already farther than the best plus the window: nothing in it can be the
 * answer or sit inside the window. */
static om_unit_row *om_tac_nearest_hostile(om_tac_state *st, const om_unit_row *self, double radius) {
    const om_grid *g = &st->grid;
    om_nearest_acc acc = { NULL, 0.0, 0.0, 0 };
    om_cell_span sp;
    int32_t cx, cy;
    if (!om_grid_span(st, self->x, self->y, radius, &sp)) return NULL;
    om_tac_nearest_scan_cell(st, self, radius, (uint32_t)sp.hy * (uint32_t)g->cols + (uint32_t)sp.hx, &acc);
    for (cy = sp.cy0; cy <= sp.cy1; cy++) {
        for (cx = sp.cx0; cx <= sp.cx1; cx++) {
            double gap2;
            if (cx == sp.hx && cy == sp.hy) continue;
            gap2 = om_grid_cell_gap2(g, cx, cy, self->x, self->y);
            if (gap2 > radius * radius) continue;
            if (acc.best && gap2 > acc.best_d2 + OM_TIE_SCAN_WINDOW) continue;
            om_tac_nearest_scan_cell(st, self, radius, (uint32_t)cy * (uint32_t)g->cols + (uint32_t)cx, &acc);
        }
    }
    if (acc.have_next && acc.next_d2 - acc.best_d2 <= OM_TIE_SCAN_WINDOW) return om_tac_nearest_hostile_ordered(st, self, radius);
    return acc.best;
}

/* OM_TP_TARGET_POLICY 1 (lab only, R-087-03): the enemy in attack range with the
 * lowest hit point fraction, then nearest, then lowest id (ids ascend, so a
 * candidate replaces the best only when strictly better by OM_TIE_EPSILON). */
static om_unit_row *om_tac_most_damaged_hostile(om_world *w, om_tac_state *st, const om_unit_row *self, double radius) {
    om_unit_row *best = NULL;
    double best_frac = 0.0, best_d2 = 0.0;
    uint32_t ids[st->n_units + 1];
    uint32_t j, n = om_grid_query_st(st, self->x, self->y, radius, ids, st->n_units);
    for (j = 0; j < n; j++) {
        om_unit_row *cand = &st->units[ids[j] - 1];
        double dx = cand->x - self->x, dy = cand->y - self->y, d2 = dx * dx + dy * dy;
        double frac = cand->max_hp > 0.0 ? cand->hp / cand->max_hp : 1.0;
        if (cand->hp <= 0.0 || cand->stealth) continue;
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer || cand->unit_id == self->excl_id) continue;
        if (!om_tac_may_act_on(w, self, cand)) continue;
        if (!best || frac < best_frac - OM_TIE_EPSILON
            || (frac <= best_frac + OM_TIE_EPSILON && (d2 < best_d2 - OM_TIE_EPSILON
                || (d2 <= best_d2 + OM_TIE_EPSILON && cand->unit_id < best->unit_id)))) {
            best = cand; best_frac = frac; best_d2 = d2;
        }
    }
    return best;
}

static int om_tac_hostile_within(om_tac_state *st, const om_unit_row *self, double radius) {
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_other_st(&it, st, self->faction_id, self->x, self->y, radius);
    while ((id = om_grid_iter_next(&it)) != 0) {
        const om_unit_row *cand = &st->units[id - 1];
        if (cand->hp <= 0.0 || cand->stealth) continue;
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer) continue;
        return 1;
    }
    return 0;
}

static void om_tac_refresh_positions(om_world *w, om_tac_state *st) {
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        double x, y;
        if (!u->in_use) continue;
        if (om_unit_get_pos(w, u->unit_id, &x, &y)) { u->x = x; u->y = y; }
    }
    om_grid_rebuild(st);
}

/* One step of unit.c-driven movement at the unit's effective speed
 * (0 during backswing or a Brace). Returns 1 once (tx, ty) is reached.
 * leash_r >= 0 (F6, R-096-08): the step is cut back onto the circle of that radius about (cx, cy), so the unit never ends a step outside it. */
static int om_tac_step_leashed(om_world *w, om_unit_row *u, double tx, double ty, double cx, double cy, double leash_r) {
    double dx = tx - u->x, dy = ty - u->y;
    double d = sqrt(dx * dx + dy * dy);
    double step = om_unit_effective_speed(w, u->unit_id) / (double)OM_TACTICAL_TICK_RATE
                  * (double)om_tac_period(om_tac(w));
    if (d <= OM_TIE_EPSILON) return 1;
    if (step <= 0.0) return 0;
    {
        /* F1 (R-207-06, R-207-07): the step goes through the move side's commit, so a flinch or a seen-step cannot leave the canvas or enter a
         * blocked cell. A step the commit cut short ends the movement (the unit stands at the face), as arriving would. */
        double nx = d <= step ? tx : u->x + dx / d * step, ny = d <= step ? ty : u->y + dy / d * step;
        if (leash_r >= 0.0 && !om_tac_dist_le(nx - cx, ny - cy, leash_r)) {
            const double ex = nx - cx, ey = ny - cy, k = leash_r / sqrt(ex * ex + ey * ey);
            nx = cx + ex * k; ny = cy + ey * k;
        }
        const int cut = om_move_commit(w, u->unit_id, u->x, u->y, &nx, &ny, OM_COMMIT_FLINCH) & (OM_COMMIT_CLAMPED | OM_COMMIT_SLID | OM_COMMIT_HELD);
        u->x = nx; u->y = ny;
        om_grid_move(om_tac(w), u->unit_id - 1);
        om_unit_set_pos(w, u->unit_id, u->x, u->y);
        return d <= step || cut;
    }
}

static int om_tac_step_toward(om_world *w, om_unit_row *u, double tx, double ty) {
    return om_tac_step_leashed(w, u, tx, ty, 0.0, 0.0, -1.0);
}

/* See also: om_tac_move_resume in tactical_move.c, which clears the held flag and keeps the group */
int om_tac_move_resume(om_world *w, uint32_t unit_id);

static void om_tac_hold(om_world *w, om_unit_row *u, uint32_t target_id) {
    if (u->halted) return;
    om_unit_engage(w, u->unit_id, target_id);
    u->halted = 1;
    u->am_engaged = 1;
}

/* Hands a held unit its route back: an attack-move resumes toward its
 * recorded point after every engagement, group member or lone unit alike
 * (R-096-02); any other order simply clears. A lone unit goes through a plain
 * om_command_move, since tactical_move.c has no immediate attack-move; unit.c's
 * own `order` still says attack-move. */
static void om_tac_release(om_world *w, om_unit_row *u) {
    if (!u->halted) return;
    u->halted = 0;
    if (u->order == OM_ORDER_ATTACK_MOVE && u->am_gid != 0 && om_unit_get_group_id(w, u->unit_id) == u->am_gid) {
        om_tac_move_resume(w, u->unit_id);
    } else if (u->order == OM_ORDER_ATTACK_MOVE) {
        om_command_move(w, &u->unit_id, 1, u->order_x, u->order_y);
        u->issued_x = u->order_x;
        u->issued_y = u->order_y;
    } else {
        om_unit_clear_orders(w, u->unit_id);
    }
}

/* R-087-06 (2026-10-19): a return-fire redirect of an attack-moving unit is one engagement of its order. While it lasts
 * order_x/y stays the point to go back to (a group member's slot; am_gid is cleared, the member left the group) and
 * issued_x/y is the attacker's place; a lone attack-move otherwise has the two equal. */
static int om_tac_pursuing(const om_world *w, const om_unit_row *u) {
    return om_tac_pursue(w) && u->order == OM_ORDER_ATTACK_MOVE && u->am_gid == 0
        && (u->issued_x != u->order_x || u->issued_y != u->order_y);
}

static void om_tac_end_pursuit(om_world *w, om_unit_row *u) {
    u->target_id = 0;
    u->anchor_set = 0;
    u->halted = 0;
    om_command_move(w, &u->unit_id, 1, u->order_x, u->order_y);
    u->issued_x = u->order_x;
    u->issued_y = u->order_y;
}

/* H-057 (R-087-04 rev 2026-11-01): walk toward a target beyond attack range. The unit leaves its group for the
 * engagement exactly as the return-fire redirect does: am_gid cleared, order_x/y kept as the point to resume to. */
static void om_tac_chase(om_world *w, om_unit_row *u, const om_unit_row *t) {
    if (!u->halted && u->issued_x == t->x && u->issued_y == t->y) return;
    if (u->am_gid != 0 && om_unit_get_group_id(w, u->unit_id) == u->am_gid) {
        if (!om_unit_get_destination(w, u->unit_id, &u->order_x, &u->order_y)) {
            u->order_x = u->issued_x; u->order_y = u->issued_y;
        }
    }
    u->am_gid = 0;
    u->halted = 0;
    om_command_move(w, &u->unit_id, 1, t->x, t->y);
    u->issued_x = t->x; u->issued_y = t->y;
}

/* H-057 (DEC-leash-anchor-return-2026-11-01): anchor_set 2 = returning after a leash drop. An idle unit walks back to
 * its anchor (its order point is its post); an attack-mover resumes toward its point or slot. Either halts to fire at
 * anything in attack range and never pursues, and may acquire beyond attack range again only once within arrival
 * tolerance of its anchor-to-point line (idle: of the anchor). */
static void om_tac_return(om_world *w, om_unit_row *u) {
    double lx = u->order_x - u->anchor_x, ly = u->order_y - u->anchor_y;
    double px = u->x - u->anchor_x, py = u->y - u->anchor_y;
    double len2 = lx * lx + ly * ly, f = len2 > 0.0 ? (px * lx + py * ly) / len2 : 0.0;
    if (f < 0.0) f = 0.0;
    if (f > 1.0) f = 1.0;
    if (om_tac_dist_le(px - f * lx, py - f * ly, OM_ARRIVAL_TOLERANCE_MULT * OM_UNIT_COLLISION_RADIUS)) {
        om_tac_end_pursuit(w, u);
        return;
    }
    if (u->halted || u->issued_x != u->order_x || u->issued_y != u->order_y) {
        u->halted = 0;
        om_command_move(w, &u->unit_id, 1, u->order_x, u->order_y);
        u->issued_x = u->order_x; u->issued_y = u->order_y;
    }
}

static void om_tac_fire(om_world *w, om_unit_row *u, om_unit_row *t) {
    om_tac_state *st = om_tac(w);
    om_tac_ev_emit(st, OM_TAC_EV_FIRE, u->unit_id, (int32_t)t->unit_id);
    u->fired_tick = st->ev_tick ? st->ev_tick : st->current_tick + 1;
    const om_unit_type_profile *prof = om_get_profile(w, u->unit_type);
    if (prof && prof->aoe_radius > 0.0) {
        om_unit_fire_aoe_attack(w, u->unit_id, t->unit_id, prof->aoe_radius);
    } else {
        om_tactical_apply_hit(w, u, t);
    }
}

static void om_tac_start_flinch(om_unit_row *u, const om_unit_row *from) {
    double dx = u->x - from->x, dy = u->y - from->y;
    double d = sqrt(dx * dx + dy * dy);
    if (d <= OM_TIE_EPSILON) { dx = 1.0; dy = 0.0; d = 1.0; }
    u->flinching = 1;
    u->flinch_x = u->x + dx / d * OM_RETURN_FIRE_FLEE_DIST;
    u->flinch_y = u->y + dy / d * OM_RETURN_FIRE_FLEE_DIST;
}

/* R-087-04: the nearest enemy in sensor range that the unit itself sees (its
 * own set, as the Python); lowest id on a distance tie. */
static om_unit_row *om_tac_nearest_visible(om_world *w, om_tac_state *st, const om_unit_row *self, double radius) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0;
    uint32_t id;
    om_grid_iter it;
    int by_sight = om_tac_by_sight(w);
    om_grid_iter_begin_other_st(&it, st, self->faction_id, self->x, self->y, radius);
    while ((id = om_grid_iter_next(&it)) != 0) {
        om_unit_row *cand = &st->units[id - 1];
        double dx = cand->x - self->x, dy = cand->y - self->y, d2 = dx * dx + dy * dy;
        if (cand->hp <= 0.0 || cand->stealth) continue;
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer || cand->unit_id == self->excl_id) continue;
        if (best && (d2 > best_d2 || (d2 == best_d2 && id > best->unit_id))) continue;
        if (by_sight ? !om_tac_faction_sees(w, self, cand) : !om_unit_can_see(w, self->unit_id, id)) continue;
        best = cand; best_d2 = d2;
    }
    return best;
}

/* G3 acquisition: the nearest enemy in range, and when it is the side's to act on that is the answer (one sight check
 * per pick); only when the nearest is hidden does the sight-filtered scan run. Switch 0: the plain nearest. */
static om_unit_row *om_tac_nearest_actable(om_world *w, om_tac_state *st, const om_unit_row *self, double radius) {
    om_unit_row *best = om_tac_nearest_hostile(st, self, radius);
    if (!best || om_tac_may_act_on(w, self, best)) return best;
    return om_tac_nearest_visible(w, st, self, radius);
}

/* ---- F5/F6: R-087-09 give-up and firing spot, R-096-08 guard ---- */

/* F5 (R-087-09): the run is over, or never began. */
static void om_tac_giveup_clear(om_unit_row *u) {
    u->giveup_target = 0; u->giveup_ticks = 0; u->giveup_ref = 0.0;
    u->spot_set = 0; u->spot_x = 0.0; u->spot_y = 0.0;
}

/* F5 (R-087-09): the unit holds t and `shootable` says whether it can shoot it. A target that cannot be shot and that the unit does not close in on
 * (by more than 1 wu from where the run began; the F0 checker's own test, scripts/skilllab/invariants.py R-087-09) for OM_GIVEUP_TICKS is given up:
 * the unit may not take it again for OM_GIVEUP_EXCLUSION_TICKS, or until it has a clear line to it (om_tac_excl_refresh). Returns 1 on the give-up. */
static int om_tac_giveup(om_unit_row *u, const om_unit_row *t, int shootable, uint32_t period, uint64_t tick) {
    double dx = t->x - u->x, dy = t->y - u->y, dist;
    if (shootable) { om_tac_giveup_clear(u); return 0; }
    dist = sqrt(dx * dx + dy * dy);
    if (u->giveup_target != t->unit_id || dist < u->giveup_ref - 1.0) {
        u->giveup_target = t->unit_id; u->giveup_ref = dist; u->giveup_ticks = 0; u->spot_set = 0;
    }
    u->giveup_ticks += period;
    if (u->giveup_ticks < OM_GIVEUP_TICKS) return 0;
    u->excl_id = t->unit_id;
    u->excl_until = tick + OM_GIVEUP_EXCLUSION_TICKS;
    om_tac_giveup_clear(u);
    return 1;
}

/* F5: the exclusion ends with its time, with the target, or with a clear line to it. */
static void om_tac_excl_refresh(om_world *w, om_tac_state *st, om_unit_row *u, uint64_t tick) {
    const om_unit_row *ex;
    if (u->excl_id == 0) return;
    ex = om_registry_find_in(st, u->excl_id);
    if (!ex || ex->hp <= 0.0 || tick >= u->excl_until || om_combat_can_shoot(w, u->unit_id, ex->unit_id)) {
        u->excl_id = 0;
        u->excl_until = 0;
    }
}

/* F5/F6: whether the unit is shooting t is asked once a tick: `known_for` is the target the cached `val` answers. */
static int om_tac_shootable(om_world *w, const om_unit_row *u, const om_unit_row *t, uint32_t *known_for, int *val) {
    if (*known_for != t->unit_id) { *val = om_combat_can_shoot(w, u->unit_id, t->unit_id); *known_for = t->unit_id; }
    return *val;
}

/* The sixteen compass directions (multiples of 22.5 degrees) the firing-spot search looks along; literals, so no libm. */
static const double OM_SPOT_DIRS[16][2] = {
    { 1, 0 },
    { 0.92387953251128674, 0.38268343236508978 },
    { 0.70710678118654757, 0.70710678118654746 },
    { 0.38268343236508984, 0.92387953251128674 },
    { 6.123233995736766e-17, 1 },
    { -0.38268343236508973, 0.92387953251128674 },
    { -0.70710678118654746, 0.70710678118654757 },
    { -0.92387953251128674, 0.38268343236508989 },
    { -1, 1.2246467991473532e-16 },
    { -0.92387953251128685, -0.38268343236508967 },
    { -0.70710678118654768, -0.70710678118654746 },
    { -0.3826834323650895, -0.92387953251128685 },
    { -1.8369701987210297e-16, -1 },
    { 0.38268343236509, -0.92387953251128663 },
    { 0.70710678118654735, -0.70710678118654768 },
    { 0.92387953251128685, -0.38268343236508956 }
};

/* F5 (R-087-09): a spot with a clear line to t, no farther than the unit can walk before the give-up and inside its attack range of t, reached by a
 * straight walk the move commit lets through; the nearest such spot (rings of a tenth of that walk, the sixteen directions in order). leash_r >= 0
 * (a guard): the spot lies inside that circle about (cx, cy) (R-096-08). Sets spot_x/y and spot_set; 0 when there is none. */
static int om_tac_find_spot(om_world *w, om_unit_row *u, const om_unit_row *t, double cx, double cy, double leash_r) {
    const double per_tick = om_unit_effective_speed(w, u->unit_id) / (double)OM_TACTICAL_TICK_RATE;
    const double max_r = per_tick * (double)(OM_GIVEUP_TICKS > u->giveup_ticks ? OM_GIVEUP_TICKS - u->giveup_ticks : 0);
    const double range = u->attack_range * om_tac_offset_mult(w, OM_REACH_RANGE, u, t);
    int ring, dir;
    if (max_r <= 0.0) return 0;
    for (ring = 1; ring <= 10; ring++) {
        const double r = max_r * (double)ring / 10.0;
        for (dir = 0; dir < 16; dir++) {
            const double sx = u->x + OM_SPOT_DIRS[dir][0] * r, sy = u->y + OM_SPOT_DIRS[dir][1] * r;
            int n, k, ok = 1;
            double px = u->x, py = u->y;
            if (leash_r >= 0.0 && !om_tac_dist_le(sx - cx, sy - cy, leash_r)) continue;
            if (!om_tac_dist_le(sx - t->x, sy - t->y, range)) continue;
            if (!om_combat_can_shoot_from(w, u->unit_id, sx, sy, t->unit_id)) continue;
            n = (int)(r / 10.0) + 1;
            for (k = 1; k <= n && ok; k++) {
                double qx = u->x + (sx - u->x) * (double)k / (double)n, qy = u->y + (sy - u->y) * (double)k / (double)n;
                const double wx = qx, wy = qy;
                if (om_move_commit(w, u->unit_id, px, py, &qx, &qy, OM_COMMIT_FLINCH) & (OM_COMMIT_CLAMPED | OM_COMMIT_SLID | OM_COMMIT_HELD)) ok = 0;
                px = wx; py = wy;
            }
            if (!ok) continue;
            u->spot_x = sx; u->spot_y = sy; u->spot_set = 1;
            return 1;
        }
    }
    return 0;
}

/* F5/F6: a unit about to walk for its own purpose (to a firing spot, after a target, back to a post) is not braced, as a unit under an order is not
 * (R-087-02, om_tac_unit_ai): an auto Brace or Fortify it holds is cancelled (a Brace roots the unit, om_unit_speed_with_modifiers) and the threshold
 * scan stays off this tick. */
static void om_tac_unbrace_for_walk(om_tac_state *st, om_unit_row *u) {
    u->suppress_auto = 1;
    if (u->brace_auto && (u->ability_phase == OM_ABILITY_PHASE_WINDUP || u->ability_phase == OM_ABILITY_PHASE_ACTIVE)) {
        om_ability_start_or_cancel_brace(st, u);
        u->brace_auto = 0;
    }
    if (u->fortify_auto && u->ability_phase == OM_ABILITY_PHASE_ACTIVE) om_ability_cancel_fortify(st, u);
}

/* F5/F6: one step toward the unit's firing spot (searched for first). Returns 1 when the unit moved: a unit that moved does not fire this tick (R-087-04). */
static int om_tac_spot_step(om_world *w, om_unit_row *u, const om_unit_row *t, double cx, double cy, double leash_r) {
    const double bx = u->x, by = u->y;
    om_tac_unbrace_for_walk(om_tac(w), u);
    if (!u->spot_set && !om_tac_find_spot(w, u, t, cx, cy, leash_r)) return 0;
    if (om_tac_step_leashed(w, u, u->spot_x, u->spot_y, cx, cy, leash_r)) u->spot_set = 0;   /* reached, or cut short: look again */
    return u->x != bx || u->y != by;
}

/* F6 (R-096-08): a guard may engage t when it can shoot it from where it stands, or could from the edge of its radius about its post (px, py). */
static int om_tac_guard_engageable(const om_world *w, const om_unit_row *u, const om_unit_row *t, double px, double py) {
    return om_tac_in_reach(w, u, t)
        && om_tac_dist_le(t->x - px, t->y - py, OM_GUARD_RADIUS + u->attack_range * om_tac_offset_mult(w, OM_REACH_RANGE, u, t));
}

/* F6 (R-096-08): the nearest enemy the guard's side sees that it can engage from its radius (lowest id on a tie), on its layer or another within reach. */
static om_unit_row *om_tac_guard_seen(om_world *w, om_tac_state *st, const om_unit_row *u, double px, double py) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0, widest = 1.0, m;
    uint32_t id, n;
    om_grid_iter it;
    for (n = 1; n <= OM_REACH_MAX_OFFSET; n++) {
        if ((m = om_tac_offset_param(w, OM_REACH_RANGE, 1, n)) > widest) widest = m;
        if ((m = om_tac_offset_param(w, OM_REACH_RANGE, 0, n)) > widest) widest = m;
    }
    om_grid_iter_begin_other_st(&it, st, u->faction_id, px, py, OM_GUARD_RADIUS + u->attack_range * widest);
    while ((id = om_grid_iter_next(&it)) != 0) {
        om_unit_row *cand = &st->units[id - 1];
        double dx = cand->x - u->x, dy = cand->y - u->y, d2 = dx * dx + dy * dy;
        if (cand->hp <= 0.0 || cand->stealth || !om_tac_hostile(u, cand) || cand->unit_id == u->excl_id) continue;
        if (best && (d2 > best_d2 || (d2 == best_d2 && id > best->unit_id))) continue;
        if (!om_tac_guard_engageable(w, u, cand, px, py) || !om_tac_may_act_on(w, u, cand)) continue;
        best = cand; best_d2 = d2;
    }
    return best;
}

/* F6: one step toward (tx, ty), cut back onto the circle of radius leash_r about the post (px, py) when leash_r >= 0; 1 when the guard moved. */
static int om_tac_guard_step(om_world *w, om_unit_row *u, double tx, double ty, double px, double py, double leash_r) {
    const double bx = u->x, by = u->y;
    om_tac_unbrace_for_walk(om_tac(w), u);
    om_tac_step_leashed(w, u, tx, ty, px, py, leash_r);
    return u->x != bx || u->y != by;
}

/* F6 (R-096-08, R-208-01): a guard's tick under pursuit by steering. It engages what its side sees that it can reach from inside GUARD_RADIUS of its
 * post (the post is anchor_x/y, set when the order was given), steps toward it no farther than the radius, fires when in range, and walks back to the
 * post when it has no target. The lock is as any unit's (R-087-03): kept until the target dies, leaves sight or reach, or can no longer be engaged
 * from the radius; R-087-09 applies to a guard as to any unit. A guard that moved this tick does not fire (R-087-04). */
static void om_tac_guard_tick(om_world *w, om_tac_state *st, om_unit_row *u, uint64_t tick) {
    const double px = u->anchor_x, py = u->anchor_y;
    const uint32_t period = om_tac_period(st);
    const int cohort_turn = (uint64_t)(om_unit_cohort_slot(w, u->unit_id)) == tick % OM_TARGETING_COHORT_COUNT;
    uint32_t shoot_for = 0;
    int shoot = 0, stepped = 0;
    om_unit_row *t = u->target_id != 0 ? om_registry_find_in(st, u->target_id) : NULL;
    if (u->target_id != 0) {
        int drop = !t || t->hp <= 0.0 || !om_tac_hostile(u, t) || t->stealth || !om_tac_may_act_on(w, u, t)
                   || !(om_tac_in_range(w, u, t) || om_tac_guard_engageable(w, u, t, px, py));
        if (!drop && om_tac_giveup(u, t, om_tac_shootable(w, u, t, &shoot_for, &shoot), period, tick)) drop = 1;
        if (drop) { u->target_id = 0; om_tac_giveup_clear(u); t = NULL; }
    }
    if (!t && cohort_turn && u->attack_range > 0.0) {
        t = om_tac_most_damaged_for(w, u) ? om_tac_most_damaged_hostile(w, st, u, u->attack_range)
                                          : om_tac_nearest_actable(w, st, u, u->attack_range);
        t = om_tac_pick_across(w, st, u, t);
        if (!t) t = om_tac_guard_seen(w, st, u, px, py);
        if (t) u->target_id = t->unit_id;
    }
    if (t) {
        if (!om_tac_in_range(w, u, t)) stepped = om_tac_guard_step(w, u, t->x, t->y, px, py, OM_GUARD_RADIUS);
        else if (!om_tac_shootable(w, u, t, &shoot_for, &shoot)) stepped = om_tac_spot_step(w, u, t, px, py, OM_GUARD_RADIUS);
        if (!stepped) u->fire_pending = 1;
    } else if (!om_tac_dist_le(u->x - px, u->y - py, OM_TIE_EPSILON)) {
        om_tac_guard_step(w, u, px, py, px, py, -1.0);
    }
}

static void om_tac_drop_orders(om_unit_row *u) {
    u->order = OM_ORDER_NONE;
    u->target_id = 0;
    u->anchor_set = 0;
    u->halted = 0;
    u->am_gid = 0;
    u->am_engaged = 0;
    u->guard = 0;
}

/* See also: om_command_guard in tactical_move.c, which clears the movement side of the order */
void om_tac_unit_set_guard(om_world *w, uint32_t unit_id, int on) {
    om_unit_row *u = om_registry_find_in(om_tac(w), unit_id);
    if (!u) return;
    if (!on) { u->guard = 0; return; }
    if (u->guard) return;
    om_tac_drop_orders(u);
    u->flinching = 0;
    u->last_attacker = 0;
    u->guard = 1;
}

static void om_tac_unit_ai(om_world *w, om_tac_state *st, om_unit_row *u, uint64_t tick) {
    double dest_x = 0.0, dest_y = 0.0, interval_ticks = u->attack_interval * (double)OM_TACTICAL_TICK_RATE;
    int has_dest = om_unit_get_destination(w, u->unit_id, &dest_x, &dest_y);
    int kind = om_unit_get_order_kind(w, u->unit_id);
    int arrived = has_dest && om_tac_dist_le(dest_x - u->x, dest_y - u->y, OM_TIE_EPSILON);
    int noncombat = om_tac_noncombat(u);
    int pursue = om_tac_pursue(w);
    int most_damaged;
    int leash_first = om_tactical_get_param(w, OM_TP_LEASH_BEFORE_DAMAGE) != 0.0;
    int cohort_turn;
    /* P1: an attack-move that has arrived stays an attack-move (the chase persists) until a new order */
    int chase_idle = pursue && u->order == OM_ORDER_ATTACK_MOVE && !has_dest;
    int ordered = u->order != OM_ORDER_NONE && !chase_idle;
    om_unit_row *t;
    uint32_t shoot_for = 0;   /* F5: whose shot the unit has asked about this tick, and the answer (om_tac_shootable) */
    int shoot = 0;

    if (u->cooldown < interval_ticks) u->cooldown += (double)om_tac_period(st);
    u->suppress_auto = 0;
    om_tac_excl_refresh(w, st, u, tick);

    /* What tactical_move.c currently believes about this unit's route vs
     * what unit.c last asked for: a route unit.c did not issue is the
     * player's own order and wins (R-087-02). */
    if (has_dest && kind == 1) {
        u->order = OM_ORDER_ATTACK_MOVE;
        u->order_x = dest_x; u->order_y = dest_y;
        u->issued_x = dest_x; u->issued_y = dest_y;
        u->target_id = 0; u->anchor_set = 0; u->halted = 0;
    } else if (u->order != OM_ORDER_NONE && !chase_idle) {
        if (!has_dest
            || (kind == 0 && (dest_x != u->issued_x || dest_y != u->issued_y))
            || (kind == 2 && u->order != OM_ORDER_ATTACK_TARGET)) {
            om_tac_drop_orders(u);
        }
    }

    /* H-057, R-087-02: the order that wins over auto-engagement is the player's. An idle unit that engaged on sight
     * holds an attack-move whose point is its own post (order point == anchor, set together at acquisition); that is
     * not a player command, so it keeps its auto-abilities. A player's attack-move point is never its anchor.
     * Detection condition: an attack-move whose point equals the unit's own anchor (anchor_set). That condition
     * stands in for an explicit engage flag; there is no such flag on the unit.
     * See also: DEC-engage-keeps-abilities-2026-11-02 */
    if (ordered && !(u->order == OM_ORDER_ATTACK_MOVE && u->anchor_set
                     && u->order_x == u->anchor_x && u->order_y == u->anchor_y)) u->suppress_auto = 1;
    if (u->brace_auto && (ordered || (has_dest && !arrived))
        && (u->ability_phase == OM_ABILITY_PHASE_WINDUP || u->ability_phase == OM_ABILITY_PHASE_ACTIVE)) {
        om_ability_start_or_cancel_brace(st, u);
        u->brace_auto = 0;
    }
    if (u->fortify_auto && (ordered || (has_dest && !arrived))
        && u->ability_phase == OM_ABILITY_PHASE_ACTIVE) {
        om_ability_cancel_fortify(st, u);
    }
    if (u->order == OM_ORDER_NONE && has_dest && !arrived) {
        /* plain move: never acquires, never returns fire, never stops */
        u->target_id = 0; u->anchor_set = 0; u->halted = 0;
        u->flinching = 0; u->last_attacker = 0;
        u->suppress_auto = 1;
        return;
    }

    if (u->flinching) {
        if (u->order != OM_ORDER_NONE) {
            u->flinching = 0;
        } else {
            if (om_tac_step_toward(w, u, u->flinch_x, u->flinch_y)) u->flinching = 0;
            u->last_attacker = 0;
            u->suppress_auto = 1;
            return;
        }
    }

    if (u->last_attacker != 0) {
        om_unit_row *atk = om_registry_find_in(st, u->last_attacker);
        u->last_attacker = 0;
        /* PP baseline only (switch = 0): return fire for an idle unit only; see also the pursue term (R-087-06) */
        if (atk && atk->hp > 0.0 && om_tac_hostile(u, atk)
            && (u->order == OM_ORDER_NONE || (pursue && u->order == OM_ORDER_ATTACK_MOVE)) && u->target_id == 0) {
            if (u->guard) {
                /* R-096-08: a guard answers only what it can shoot, and never flees or walks */
                if (!noncombat && om_tac_in_reach(w, u, atk) && !atk->stealth && om_tac_in_range(w, u, atk)) u->target_id = atk->unit_id;
            } else if (noncombat || !om_tac_in_reach(w, u, atk) || atk->stealth) {
                if (u->order == OM_ORDER_NONE) om_tac_start_flinch(u, atk);
            } else if (om_tac_in_range(w, u, atk)) {
                u->target_id = atk->unit_id;
            } else {
                u->halted = 0;
                if (u->order == OM_ORDER_ATTACK_MOVE) {
                    /* one engagement of the order: keep the point of record and hold the attacker as the target, so
                     * its death, the leash and sight end it through the target checks below (R-087-06, R-087-08) */
                    if (u->am_gid != 0 && om_unit_get_group_id(w, u->unit_id) == u->am_gid) {
                        if (!om_unit_get_destination(w, u->unit_id, &u->order_x, &u->order_y)) {
                            u->order_x = u->issued_x; u->order_y = u->issued_y;
                        }
                    }
                    u->am_gid = 0;
                    u->target_id = atk->unit_id;
                    u->anchor_x = u->x; u->anchor_y = u->y; u->anchor_set = 1;
                } else {
                    u->order = OM_ORDER_ATTACK_MOVE;
                    u->order_x = atk->x; u->order_y = atk->y;
                }
                u->issued_x = atk->x; u->issued_y = atk->y;
                om_command_move(w, &u->unit_id, 1, atk->x, atk->y);
            }
        }
    }
    if (noncombat) { u->target_id = 0; return; }
    if (u->flinching) { u->suppress_auto = 1; return; }

    if (u->target_id != 0) {
        int drop, leash_drop = 0;
        t = om_registry_find_in(st, u->target_id);
        drop = !t || t->hp <= 0.0 || !om_tac_hostile(u, t);
        /* R-164-02: an attack-target order is bound by reach too; one beyond it is ended like a dead target's */
        if (!drop && u->order == OM_ORDER_ATTACK_TARGET && !om_tac_in_reach(w, u, t)) drop = 1;
        if (!drop && u->order == OM_ORDER_ATTACK_TARGET) {
            /* S-093: the engine keeps no information the player lost. A
             * target the faction no longer sees is dropped and the unit
             * attack-moves to where it was last seen. */
            if (om_tac_faction_sees(w, u, t)) {
                u->last_seen_x = t->x; u->last_seen_y = t->y;
            } else {
                double lx = u->last_seen_x, ly = u->last_seen_y;
                om_command_attack_move(w, &u->unit_id, 1, lx, ly);
                return;
            }
        }
        /* G3 (R-008-04): a held target the side no longer sees is dropped on the spot, one sight check per held target */
        if (!drop && u->order != OM_ORDER_ATTACK_TARGET && !om_tac_may_act_on(w, u, t)) drop = 1;
        if (!drop && u->order != OM_ORDER_ATTACK_TARGET) {
            /* P1: with pursuit by steering a target that has left attack range is kept until a cohort turn finds another */
            if (!om_tac_in_reach(w, u, t) || t->stealth || ((!pursue || u->guard) && !om_tac_in_range(w, u, t))) {
                drop = 1;
            } else if (pursue && u->anchor_set == 2 && !om_tac_in_range(w, u, t)) {
                drop = 1;   /* H-057: returning, it fires within attack range and does not pursue */
            } else if (!leash_first && u->order == OM_ORDER_ATTACK_MOVE && u->anchor_set == 1
                       && om_tac_leash_broken(w, u, t)) {
                drop = 1; leash_drop = 1;
            }
        }
        /* F5 (R-087-09): a target the unit holds and cannot shoot, and does not close in on, for 1 s is given up for the next 100 ticks */
        if (!drop && u->order != OM_ORDER_ATTACK_TARGET
            && om_tac_giveup(u, t, om_tac_shootable(w, u, t, &shoot_for, &shoot), om_tac_period(st), tick)) drop = 1;
        if (drop) {
            int gone = !t || t->hp <= 0.0 || (u->order == OM_ORDER_ATTACK_TARGET && !om_tac_in_reach(w, u, t));
            u->target_id = 0;
            om_tac_giveup_clear(u);
            /* H-057: a leash drop starts the walk back (2); a pursuit whose target is gone keeps its anchor until the
             * next cohort turn decides (never reset while pursuing); anything else clears it */
            if (leash_drop) u->anchor_set = 2;
            else if (!(pursue && u->order == OM_ORDER_ATTACK_MOVE && u->anchor_set && om_tac_pursuing(w, u))) u->anchor_set = 0;
            if (u->order == OM_ORDER_ATTACK_TARGET && gone) {
                u->order = OM_ORDER_NONE;
                u->halted = 0;
                om_unit_clear_orders(w, u->unit_id);
            }
        }
    }

    t = u->target_id != 0 ? om_registry_find_in(st, u->target_id) : NULL;
    most_damaged = om_tac_most_damaged_for(w, u);
    cohort_turn = (uint64_t)(om_unit_cohort_slot(w, u->unit_id)) == tick % OM_TARGETING_COHORT_COUNT;
    /* F3 (R-087-03, R-087-08 as rewritten 2026-11-08): acquisition runs only while the unit has no lock (or under the lab-only
     * most_damaged policy, Q-008-05). A locked target that stepped out of attack range is walked to (R-087-04), not swapped
     * for the nearest; it leaves the lock only by dying, leaving the side's sight, the leash or a new order. */
    if ((u->target_id == 0 || most_damaged) && u->order != OM_ORDER_ATTACK_TARGET
        && cohort_turn) {
        /* H-057: an idle or attack-moving unit looks as far as it can be led, the type's leash; a guard, and a unit on
         * its way back to its anchor, only as far as it can shoot */
        double acq = u->attack_range;
        if (pursue && !u->guard && u->anchor_set != 2) {
            acq = om_tac_leash(w, u);
            if (acq < u->attack_range) acq = u->attack_range;
        }
        t = most_damaged
            ? om_tac_most_damaged_hostile(w, st, u, u->attack_range)
            : om_tac_nearest_actable(w, st, u, acq);
        t = om_tac_pick_across(w, st, u, t);
        if (t) {
            u->target_id = t->unit_id;
            if (u->order == OM_ORDER_ATTACK_MOVE && (!pursue || !u->anchor_set)) {
                u->anchor_x = u->x; u->anchor_y = u->y; u->anchor_set = 1;
            }
        }
        /* H-057 (R-087-04 rev 2026-11-01, replaces A199): a target beyond attack range is walked to below. The
         * switch-0 baseline arm below (old path kept as baseline only, deleted at end of Phase E) still steps toward a
         * seen enemy. */
    }

    /* OM_TP_LEASH_BEFORE_DAMAGE 1 (R-087-05, R-096-03; the Python's order): the leash drop runs here, before this
     * tick's shot; at 0 it runs at the start of the next tick, after the shot. */
    if (leash_first && u->target_id != 0 && u->order == OM_ORDER_ATTACK_MOVE && u->anchor_set == 1) {
        t = om_registry_find_in(st, u->target_id);
        if (t && om_tac_leash_broken(w, u, t)) {
            u->target_id = 0;
            u->anchor_set = pursue ? 2 : 0;
        }
    }

    t = u->target_id != 0 ? om_registry_find_in(st, u->target_id) : NULL;
    if (t) {
        int in_range = om_tac_in_range(w, u, t), stepped = 0;
        if (pursue && u->order == OM_ORDER_NONE && !u->guard && !in_range) {
            /* H-057: an idle unit leaves its post as an attack-mover whose point is the post (it walks back to it) */
            u->order = OM_ORDER_ATTACK_MOVE;
            u->order_x = u->x; u->order_y = u->y;
            u->issued_x = u->x; u->issued_y = u->y;
            u->am_gid = 0;
            u->anchor_x = u->x; u->anchor_y = u->y; u->anchor_set = 1;
        }
        if (u->order == OM_ORDER_ATTACK_TARGET) {
            if (in_range) {
                if (!u->halted) {
                    om_command_attack_target_kiting(w, u->unit_id, t->unit_id, u->x, u->y);
                    u->halted = 1;
                }
            } else if (u->halted || u->issued_x != t->x || u->issued_y != t->y) {
                om_command_move(w, &u->unit_id, 1, t->x, t->y);
                u->issued_x = t->x; u->issued_y = t->y;
                u->halted = 0;
            }
        } else if (u->order == OM_ORDER_ATTACK_MOVE && pursue && !in_range && u->anchor_set == 1) {
            om_tac_chase(w, u, t);
        } else if (u->order == OM_ORDER_ATTACK_MOVE && pursue
                   && (!in_range || !om_combat_can_shoot(w, u->unit_id, t->unit_id))) {
            /* P1: holds only while its own target is in attack range and the unit can shoot it (A171, R-087-05),
             * otherwise walks its goal and fires when the line clears */
            om_tac_release(w, u);
        } else if (u->order == OM_ORDER_ATTACK_MOVE) {
            om_tac_hold(w, u, t->unit_id);
            /* a target taken by return fire is anchored here and leashed from the next tick */
            if (pursue && !u->anchor_set) { u->anchor_x = u->x; u->anchor_y = u->y; u->anchor_set = 1; }
        }
        /* F5 (R-087-09): an idle unit whose target is in range but behind a blocker walks to a spot with a clear line (an attack-mover walks its
         * goal, A171, and the give-up bounds it); a unit that moved does not fire this tick (R-087-04) */
        if (pursue && u->order == OM_ORDER_NONE && !u->guard && in_range && !om_tac_shootable(w, u, t, &shoot_for, &shoot)) {
            stepped = om_tac_spot_step(w, u, t, 0.0, 0.0, -1.0);
        }
        /* See also: om_tac_fire_pass, the same decision (and the first shot, R-084-01) after movement under
         * PURSUE_BY_STEERING (A178). PP baseline only (switch = 0): fire here; deleted with the two movement
         * switches at the end of Phase E (A140) */
        if (pursue) {
            if (!stepped) u->fire_pending = 1;
        } else if (in_range && u->cooldown >= interval_ticks - OM_TIE_EPSILON
            && om_combat_can_shoot(w, u->unit_id, t->unit_id)) {
            om_tac_fire(w, u, t);
        }
    } else if (u->order == OM_ORDER_ATTACK_MOVE && pursue) {
        if (u->anchor_set == 2) om_tac_return(w, u);
        else if (u->anchor_set == 1 && om_tac_pursuing(w, u) && !cohort_turn) {
            /* H-057: the target is gone; the walk goes on and the anchor stays until the next cohort turn finds another */
        } else if (om_tac_pursuing(w, u)) om_tac_end_pursuit(w, u);
        else { u->anchor_set = 0; om_tac_release(w, u); }
    } else if (u->order == OM_ORDER_ATTACK_MOVE) {
        /* PP baseline only (switch = 0); deleted with the two movement switches at the end of Phase E (A140) */
        /* old path kept as baseline only, deleted at end of Phase E. See also: A199 (R-087-04), the pursue branch above */
        const om_unit_type_profile *prof = om_get_profile(w, u->unit_type);
        om_unit_row *seen;
        if (om_tac_hostile_within(st, u, u->attack_range)) {
            om_tac_hold(w, u, 0);
        } else if (prof && prof->sensor_radius > u->attack_range
                   && (seen = om_tac_nearest_hostile(st, u, prof->sensor_radius)) != NULL) {
            om_tac_hold(w, u, seen->unit_id);
            om_tac_step_toward(w, u, seen->x, seen->y);
        } else {
            om_tac_release(w, u);
            if (arrived) om_tac_drop_orders(u);
        }
    }
}

/* P2 (A178, the Python's order: update_targeting, update_movement, resolve_damage): a shot is decided on the
 * positions after this tick's movement, and every shooter of the tick is chosen before any hit lands. */
static void om_tac_fire_pass(om_world *w, om_tac_state *st) {
    uint32_t i;
    om_tac_refresh_positions(w, st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        om_unit_row *t;
        int pending = u->fire_pending;
        u->fire_pending = 0;
        if (!pending || !u->in_use || u->hp <= 0.0 || u->target_id == 0) continue;
        /* F2 (R-087-04, R-096-02): a unit that walked this tick does not fire; it fires on the next, when halted. */
        if (om_move_moved_own_power(w, u->unit_id, om_tactical_tick(w))) continue;
        t = om_registry_find_in(st, u->target_id);
        if (t && t->hp > 0.0 && om_tac_in_range(w, u, t)
            && (u->cooldown >= u->attack_interval * (double)OM_TACTICAL_TICK_RATE - OM_TIE_EPSILON || !u->fired)
            && om_combat_can_shoot(w, u->unit_id, t->unit_id)) {
            u->fire_pending = 2;
        }
    }
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (u->fire_pending != 2) continue;
        u->fire_pending = 0;
        om_tac_fire(w, u, om_registry_find_in(st, u->target_id));
        u->backswing_ticks_remaining = OM_BACKSWING_TICKS - 1;
    }
}

static void om_tactical_ai_tick(om_world *w, om_tac_state *st) {
    uint64_t tick = st->current_tick + 1;
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        if (u->target_id == 0 && om_tac_pursuing(w, u)) {
            /* arrival at the attacker's place ends the pursuit too. Only while the unit holds no target: a unit that
             * halted to fire at, or has just been sent after, a locked target has no route, which is not arrival, and
             * ending the pursuit here cleared a live, seen lock (R-087-03, R-087-08). See also: om_tac_unit_ai, which
             * ends the pursuit itself once the target is gone. */
            double px, py;
            if (!om_unit_get_destination(w, u->unit_id, &px, &py) || om_tac_dist_le(px - u->x, py - u->y, OM_TIE_EPSILON)) {
                om_tac_end_pursuit(w, u);
            }
        }
        om_tac_unit_ai(w, st, u, tick);
    }
    st->validated_tick = tick;
}

/* ---- end S-087 ---- */

static void om_tac_log_kills(om_tac_state *st) {
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        const om_unit_row *k;
        int32_t killer = -1;
        if (!u->in_use || u->hp > 0.0 || u->kill_logged) continue;
        u->kill_logged = 1;
        k = om_registry_find_in(st, u->last_attacker);
        if (k && k->faction_id != u->faction_id) killer = (int32_t)k->unit_id;
        om_tac_ev_emit(st, OM_TAC_EV_KILL, u->unit_id, killer);
    }
}

uint64_t om_tactical_step(om_world *w) {
    om_cmd_apply_tick(w);
    /* No-op until a tactical battle actually exists (tests/csim/test_E11_wiring.py
     * ::test_R_wiring_tactical_step_is_callable): a strategic-only world with no
     * units spawned must not advance the tactical tick counter at all. */
    const om_tac_state *ro = om_tac_ro(w);
    om_tac_state *st;
    if (ro) om_economy_step(w, ro->current_tick);
    if (!ro || ro->n_units == 0) {
        if (ro) { om_tac(w)->n_events = 0; om_tac(w)->events_dropped = 0; om_tac(w)->ev_closed = 1; }
        return ro ? ro->current_tick : 0;
    }
    st = om_tac(w);
    if (st->ev_closed) { st->n_events = 0; st->events_dropped = 0; st->ev_closed = 0; }
    st->ev_tick = st->current_tick + 1;
    om_tac_update_period(st);
    st->base_tick += st->tick_period_ticks;
    om_tac_refresh_positions(w, st);
    om_tactical_ai_tick(w, st);
    om_tactical_apply_aura_regen(w);
    om_tactical_advance_backswing(st);
    om_ability_advance_all(w);
    if (om_tac_pursue(w)) om_tac_fire_pass(w, st);
    om_macro_tick(w, st->current_tick);
    om_support_tick(w);
    om_mission_tactical_tick(w);
    om_tac_log_kills(st);
    st->ev_tick = 0;
    st->ev_closed = 1;
    return st->current_tick;
}

/* ---- generated stubs from signatures.toml ---- */
int om_command_activate_ability(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double target_x, double target_y) {
    om_tac_state *st = om_tac(w);
    uint32_t i;
    om_unit_row *u;
    int activated = 0;
    /* R-096-05: each unit with its ability ready activates; an unready or
     * unknown unit is skipped. Returns 0 if at least one activated, else 1
     * (R-086-07: an all-rejected command reports rejection). */
    for (i = 0; i < n_units; i++) {
        u = om_registry_find_in(st, unit_ids[i]);
        if (!u || !om_ability_can_manually_activate(u)) continue;
        om_ability_manual_activate(w, st, u, target_x, target_y);
        activated = 1;
    }
    return activated ? 0 : 1;
}

int om_command_attack_move(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double x, double y) {
    om_tac_state *st = om_tac(w);
    uint32_t i, n_found = 0, gid = 0;
    int grouped;
    for (i = 0; i < n_units; i++) if (om_registry_find_in(st, unit_ids[i])) n_found++;
    /* R-096-02: two or more units take move-group slots (PURSUE_BY_STEERING); one is not a group */
    grouped = om_tac_pursue(w) && n_found >= 2;
    for (i = 0; i < n_units; i++) {
        om_unit_row *u = om_registry_find_in(st, unit_ids[i]);
        if (!u) continue;
        om_tac_drop_orders(u);
        u->flinching = 0;
        u->order = OM_ORDER_ATTACK_MOVE;
        u->order_x = x; u->order_y = y;
        u->issued_x = x; u->issued_y = y;
        if (!grouped) om_command_move(w, &u->unit_id, 1, x, y);
    }
    if (grouped) {
        uint32_t ids[OM_MAX_UNITS], k = 0;
        for (i = 0; i < n_units && k < OM_MAX_UNITS; i++) if (om_registry_find_in(st, unit_ids[i])) ids[k++] = unit_ids[i];
        gid = om_command_group_move(w, ids, k, x, y);
        for (i = 0; i < k; i++) {
            om_unit_row *u = om_registry_find_in(st, ids[i]);
            if (gid != 0) {
                u->am_gid = gid;
                om_unit_get_destination(w, ids[i], &u->issued_x, &u->issued_y);
            } else {
                om_command_move(w, &u->unit_id, 1, x, y);
            }
        }
    }
    return 0;
}

int om_command_attack_target(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t target_unit) {
    om_tac_state *st = om_tac(w);
    om_unit_row *t = om_registry_find_in(st, target_unit);
    uint32_t i;
    if (!t) return 1;
    for (i = 0; i < n_units; i++) {
        om_unit_row *u = om_registry_find_in(st, unit_ids[i]);
        if (!u) continue;
        om_tac_drop_orders(u);
        u->flinching = 0;
        u->order = OM_ORDER_ATTACK_TARGET;
        u->target_id = target_unit;
        u->last_seen_x = t->x; u->last_seen_y = t->y;
        u->issued_x = t->x; u->issued_y = t->y;
        om_command_move(w, &u->unit_id, 1, t->x, t->y);
    }
    return 0;
}

uint32_t om_cue_lookup(const char *name) {
    if (name && strcmp(name, "cue_barrage_telegraph") == 0) return OM_CUE_BARRAGE_TELEGRAPH;
    return OM_CUE_NONE;
}

int om_era_elevation_damage_bonus_enabled(om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

int om_roster_register_custom_unit(om_world *w, uint32_t type_id, int category, const char *role, double max_hp, double base_damage, double attack_interval, double attack_range, double speed, double sensor_radius, double layer_transition_time, double aoe_radius, int ability_id) {
    om_tac_state *st = om_tac(w);
    om_custom_type_row *row;
    uint32_t i;
    (void)role; (void)ability_id;
    if (om_get_builtin_profile((int)type_id) != NULL) return -1;
    row = NULL;
    for (i = 0; i < st->n_custom_types; i++) {
        if (st->custom_types[i].in_use && st->custom_types[i].type_id == type_id) {
            row = &st->custom_types[i];
            break;
        }
    }
    if (!row) {
        if (st->n_custom_types >= OM_MAX_CUSTOM_TYPES) return -1;
        row = &st->custom_types[st->n_custom_types++];
        row->type_id = type_id;
        row->in_use = 1;
    }
    row->profile.category = category;
    row->profile.max_hp = max_hp;
    row->profile.base_damage = base_damage;
    row->profile.attack_interval = attack_interval;
    row->profile.attack_range = attack_range;
    row->profile.speed = speed;
    row->profile.sensor_radius = sensor_radius;
    row->profile.layer_transition_time = layer_transition_time;
    row->profile.aoe_radius = aoe_radius;
    return 0;
}

double om_tactical_category_multiplier(om_world *w, int attacker_category, int target_category) {
    static const double m[3][3] = {
        { OM_CATEGORY_MULTIPLIER_STRIKE_STRIKE, OM_CATEGORY_MULTIPLIER_STRIKE_LINE, OM_CATEGORY_MULTIPLIER_STRIKE_SIEGE },
        { OM_CATEGORY_MULTIPLIER_LINE_STRIKE,   OM_CATEGORY_MULTIPLIER_LINE_LINE,   OM_CATEGORY_MULTIPLIER_LINE_SIEGE },
        { OM_CATEGORY_MULTIPLIER_SIEGE_STRIKE,  OM_CATEGORY_MULTIPLIER_SIEGE_LINE,  OM_CATEGORY_MULTIPLIER_SIEGE_SIEGE },
    };
    (void)w;
    if (attacker_category < 0 || attacker_category > 2 || target_category < 0 || target_category > 2) {
        return 1.0;
    }
    return m[attacker_category][target_category];
}

void om_tactical_disable_abilities(om_world *w) {
    om_tac(w)->abilities_disabled = 1;
}

/* A reset battle reuses unit ids from 1, so tactical_move.c's per-id mirror
 * (positions, orders, engagement) has to go too; om_ms re-creates its slot
 * lazily on the next command or read. */
/* A133 Q-C4: the tunable settings live in move_state, which is freed here; they
 * are configuration, so they survive the reset (a new world starts at the defaults). The built-in types' reach
 * (G5) and collision radius (H-041) live there too and survive the same way; a custom type's reach goes with its registration. */
void om_tactical_reset(om_world *w) {
    om_tac_state *st = om_tac(w);
    double kept[OM_TP__COUNT];
    uint32_t kept_up[OM_UNIT_TYPE_COUNT], kept_down[OM_UNIT_TYPE_COUNT];
    double kept_radius[OM_UNIT_TYPE_COUNT];
    int kept_kind[OM_UNIT_TYPE_COUNT];
    int k;
    for (k = 0; k < OM_TP__COUNT; k++) kept[k] = om_tactical_get_param(w, (om_tac_param)k);
    for (k = 0; k < OM_UNIT_TYPE_COUNT; k++) {
        om_unit_profile_reach(w, k, &kept_up[k], &kept_down[k]);
        kept_kind[k] = om_unit_profile_movement_kind(w, k);
        kept_radius[k] = om_move_type_radius(w, k);
    }
    om_tac_release_arrays(st);
    memset(st, 0, sizeof(*st));
    st->next_unit_id = 1;
    if (w->move_state && w->move_state_free) {
        w->move_state_free(w->move_state);
        w->move_state = NULL;
    }
    for (k = 0; k < OM_TP__COUNT; k++) {
        if (om_tactical_get_param(w, (om_tac_param)k) != kept[k]) om_tactical_set_param(w, (om_tac_param)k, kept[k]);
    }
    for (k = 0; k < OM_UNIT_TYPE_COUNT; k++) {
        if (kept_up[k] != 0 || kept_down[k] != 0) om_roster_set_reach(w, k, kept_up[k], kept_down[k]);
        if (kept_kind[k] != OM_MOVE_FLYING) om_roster_set_movement_kind(w, k, kept_kind[k]);
        if (kept_radius[k] != (double)OM_UNIT_COLLISION_RADIUS) om_roster_set_collision_radius(w, k, kept_radius[k]);
    }
}

/* n_ticks counts base ticks: a step at period 2 accounts for two. */
uint64_t om_tactical_run(om_world *w, uint64_t n_ticks) {
    uint64_t done = 0;
    while (done < n_ticks) {
        uint64_t before = om_tactical_base_tick(w);
        uint64_t after;
        om_tactical_step(w);
        after = om_tactical_base_tick(w);
        done += after > before ? after - before : 1;
    }
    return n_ticks;
}

uint64_t om_tactical_run_until_eliminated(om_world *w) {
    uint64_t ticks = 0;
    om_tac_state *st = om_tac(w);
    uint64_t start = st->base_tick;
    double lowest_hp = om_tactical_total_hp(st);
    uint64_t last_progress = 0;
    while (ticks < OM_TACTICAL_MAX_RUN_TICKS && om_tactical_multiple_factions_alive(st)) {
        double hp;
        om_tactical_step(w);
        ticks = st->base_tick - start;
        hp = om_tactical_total_hp(st);
        if (hp < lowest_hp - OM_TIE_EPSILON) { lowest_hp = hp; last_progress = ticks; }
        if (ticks - last_progress >= OM_TACTICAL_STALEMATE_TICKS) break;
    }
    return ticks;
}

uint64_t om_tactical_run_until_engagement_ends(om_world *w, uint32_t unit_id) {
    om_tac_state *st = om_tac(w);
    uint64_t start = st->base_tick, ticks = 0;
    om_unit_row *u = om_registry_find_in(st, unit_id);
    if (!u) return 0;
    while (ticks < OM_TACTICAL_MAX_RUN_TICKS
           && u->hp > 0.0
           && om_tac_enemy_within_range(st, u, u->attack_range)) {
        om_tactical_step(w);
        ticks = st->base_tick - start;
    }
    if (u->unit_type == OM_UT_INTERCEPTOR && u->ability_phase == OM_ABILITY_PHASE_ACTIVE) {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
        u->ability_cooldown = OM_ABILITY_INTERCEPT_COOLDOWN_TICKS;
    }
    return ticks;
}

/* "default_balanced" only (see OM_COMPOSITION_*): shares scale to `count`
 * by largest remainder, ties to the lower unit type. The two sides are laid
 * out as facing grids one shortest-launch attack range apart
 * (OM_ROSTER_RAIDER_RANGE), 2 * the roster's largest collision radius between neighbours,
 * faction 0 to the left of x = 0 and any other faction to the right of the
 * gap, so every fixture built through here starts inside somebody's range.
 * Each unit attack-moves to the opposing front line at its own y, so a force
 * that is out of range closes on the enemy instead of idling. */
void om_tactical_spawn_force_composition(om_world *w, int32_t faction_id, uint32_t count, const char *composition) {
    static const uint32_t share[OM_UNIT_TYPE_COUNT] = {
        OM_COMPOSITION_RAIDER, OM_COMPOSITION_INTERCEPTOR, OM_COMPOSITION_VANGUARD,
        OM_COMPOSITION_WARDEN, OM_COMPOSITION_BOMBARD, OM_COMPOSITION_BASTION,
    };
    uint32_t n[OM_UNIT_TYPE_COUNT], rem[OM_UNIT_TYPE_COUNT];
    uint32_t placed = 0, rows = 1, k = 0, type, left;
    double spacing = 2.0 * om_move_largest_radius(w);
    if (!composition || strcmp(composition, "default_balanced") != 0) return;
    for (type = 0; type < OM_UNIT_TYPE_COUNT; type++) {
        n[type] = count * share[type] / OM_COMPOSITION_BASE;
        rem[type] = count * share[type] % OM_COMPOSITION_BASE;
        placed += n[type];
    }
    for (left = count - placed; left > 0; left--) {
        uint32_t best = 0;
        for (type = 1; type < OM_UNIT_TYPE_COUNT; type++) {
            if (rem[type] > rem[best]) best = type;
        }
        n[best]++;
        rem[best] = 0;
    }
    while (rows * rows < count) rows++;
    for (type = 0; type < OM_UNIT_TYPE_COUNT; type++) {
        uint32_t j;
        for (j = 0; j < n[type]; j++, k++) {
            double depth = (double)(k / rows) * spacing;
            double x = faction_id == 0 ? -depth : (double)OM_ROSTER_RAIDER_RANGE + depth;
            double y = (double)(k % rows) * spacing;
            uint32_t id = om_unit_spawn_internal(w, (int)type, faction_id, x, y, 0);
            if (id != 0) om_command_attack_move(w, &id, 1, faction_id == 0 ? (double)OM_ROSTER_RAIDER_RANGE : 0.0, y);
        }
    }
}

int om_tactical_target_validation_runs_every_tick(om_world *w) {
    om_tac_state *st = om_tac(w);
    return (st->n_units > 0 && st->validated_tick == st->current_tick) ? 1 : 0;
}

int om_tactical_telegraph_active(om_world *w, double x, double y) {
    om_tac_state *st = om_tac(w);
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        const om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        if (u->ability_phase != OM_ABILITY_PHASE_TELEGRAPH) continue;
        if (u->ability_target_x == x && u->ability_target_y == y) return 1;
    }
    return 0;
}

uint64_t om_tactical_tick(om_world *w) {
    return om_tac(w)->current_tick;
}

uint64_t om_tactical_tick_to(om_world *w, uint64_t tick) {
    om_tac_state *st = om_tac(w);
    while (st->current_tick < tick) {
        if (st->n_units > 0) {
            om_tactical_step(w);
        } else {
            om_cmd_apply_tick(w);
            st->current_tick++;
            st->base_tick++;
            om_macro_tick(w, st->current_tick);
            om_support_tick(w);
        }
    }
    return st->current_tick;
}

int om_tactical_zone_visible_to_enemy(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return (row && row->unit_type == OM_UT_BASTION && row->ability_phase == OM_ABILITY_PHASE_ACTIVE) ? 1 : 0;
}

int om_unit_ability_active(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return (row && row->ability_phase != OM_ABILITY_PHASE_IDLE) ? 1 : 0;
}

double om_unit_ability_cooldown(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return row ? row->ability_cooldown : 0.0;
}

int om_unit_alive(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return (row && row->hp > 0.0) ? 1 : 0;
}

void om_unit_apply_trait_modifier(om_world *w, uint32_t unit_id, int stat_field, double delta) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (!row) return;
    if (stat_field == 0) {
        row->hp += delta;
        om_grid_sync(om_tac(w), unit_id - 1);
    }
}

void om_unit_attack(om_world *w, uint32_t attacker, uint32_t target) {
    om_tac_state *st = om_tac(w);
    om_unit_row *a = om_registry_find_in(st, attacker);
    om_unit_row *t = om_registry_find_in(st, target);
    if (!a || !t || a->hp <= 0.0 || t->hp <= 0.0) return;
    if (!om_tac_hostile(a, t) || !om_tac_in_range(w, a, t)) return;
    if (!om_combat_can_shoot(w, attacker, target)) return;
    om_tac_fire(w, a, t);
}

/* ALG-60: Brace 0.50 (self, while its bonus is granted) + Fortify 0.20
 * (any friendly within OM_FORTIFY_RADIUS of an active Bastion) + Warden
 * aura 0.10 (om_warden_aura_reduction_for, once however many Wardens
 * are in range: R-083-03), capped at OM_ABILITY_DAMAGE_REDUCTION_CAP. Brace/Fortify/Warden
 * each also have a force_*_reduction flag (om_unit_set_brace_active,
 * om_unit_set_fortify_active, om_unit_set_warden_aura_active) that a test
 * can set directly on any unit type, independent of the real Vanguard
 * Brace phase, a nearby active Bastion, or a nearby real Warden --
 * test_control_e11_window_brace_reduction_wrong_constant forces Brace on a
 * Raider and still expects exactly 0.50. */
double om_unit_damage_reduction(om_world *w, uint32_t unit_id) {
    om_tac_state *st = om_tac(w);
    om_unit_row *row = om_registry_find_in(st, unit_id);
    double reduction = 0.0;
    int fortify_hit = 0;
    int brace_hit;
    if (!row) return 0.0;
    brace_hit = row->force_brace_reduction
        || (row->unit_type == OM_UT_VANGUARD && row->ability_bonus_on
            && row->ability_phase != OM_ABILITY_PHASE_IDLE);
    if (brace_hit) {
#ifdef OM_DEBUG_INJECT
        if (w->inject == OM_BUG_BRACE_REDUCTION_WRONG_CONSTANT)
            reduction += OM_ABILITY_FORTIFY_DAMAGE_REDUCTION;
        else
#endif
        reduction += OM_ABILITY_BRACE_DAMAGE_REDUCTION;
    }
    if (row->force_fortify_reduction) {
        fortify_hit = 1;
    } else if (st->n_bastions == 0) {
        if (!st->grid.built) om_grid_rebuild(st);
    } else {
        fortify_hit = om_grid_kind_scan(st, 1, row->faction_id, OM_ABILITY_PHASE_ACTIVE, row->x, row->y, OM_FORTIFY_RADIUS) != 0;
    }
    if (fortify_hit) reduction += OM_ABILITY_FORTIFY_DAMAGE_REDUCTION;
    reduction += row->force_warden_aura_reduction
        ? OM_WARDEN_AURA_DAMAGE_REDUCTION
        : om_warden_aura_reduction_for(st, row);
    if (reduction > OM_ABILITY_DAMAGE_REDUCTION_CAP) reduction = OM_ABILITY_DAMAGE_REDUCTION_CAP;
    return reduction;
}

void om_unit_deal_damage(om_world *w, uint32_t p1, uint32_t p2, double p3) {
    om_tac_state *st = om_tac(w);
    om_unit_row *attacker, *target;
    double mult, dmg, reduction, output_mult;
    attacker = om_registry_find_in(st, p1);
    target = om_registry_find_in(st, p2);
    if (!attacker || !target) return;
    mult = om_resolve_hit_multiplier(w, attacker->category, target);
    output_mult = om_unit_output_multiplier(w, p1);
    reduction = om_unit_damage_reduction(w, p2);
    dmg = p3 * mult * output_mult * (1.0 - reduction);
    target->hp -= dmg;
    if (target->hp < 0.0) target->hp = 0.0;
    om_grid_sync(st, target->unit_id - 1);
    om_tac_note_attacker(w, st, target, attacker);
    /* ALG-60: "after firing the unit's movement pauses ATTACK_BACKSWING_SEC"
     * -- any landed hit through this path (auto-fire, manual command, or a
     * test driving the attack directly) pauses the attacker the same way. */
    attacker->backswing_ticks_remaining = OM_BACKSWING_TICKS;
    attacker->backswing_active = 1;
}

static double om_unit_speed_with_modifiers(om_world *w, uint32_t unit_id, int stop_in_backswing) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    double base;
    if (!row) return 0.0;
    if (stop_in_backswing && row->backswing_active) return 0.0;
    base = om_unit_profile_speed(w, row->unit_type);
    switch (row->unit_type) {
        case OM_UT_RAIDER:
            if (row->ability_phase == OM_ABILITY_PHASE_ACTIVE) return base * OM_ABILITY_SURGE_SPEED_MULT;
            break;
        case OM_UT_INTERCEPTOR:
            if (row->ability_phase == OM_ABILITY_PHASE_ACTIVE) return base * OM_ABILITY_INTERCEPT_SPEED_MULT;
            break;
        case OM_UT_VANGUARD:
            if (row->ability_phase != OM_ABILITY_PHASE_IDLE) return 0.0;
            break;
        case OM_UT_BASTION:
            if (row->ability_phase == OM_ABILITY_PHASE_ACTIVE && !row->fortify_auto)
                return base * OM_ABILITY_FORTIFY_SPEED_MULT;
            break;
        default: break;
    }
    return base;
}

double om_unit_effective_speed(om_world *w, uint32_t unit_id) {
    return om_unit_speed_with_modifiers(w, unit_id, 1);
}

double om_unit_order_speed(om_world *w, uint32_t unit_id) {
    return om_unit_speed_with_modifiers(w, unit_id, 0);
}

/* ALG-61: every enemy on the attacker's layer within `radius` of the
 * (already-resolved) target's position takes ALG-60 per-target damage,
 * fixed registry (spawn/unit_id) order, running total capped at
 * base * OM_AOE_DAMAGE_CAP_MULTIPLIER -- same shape as
 * om_ability_resolve_barrage_damage's Barrage cap, but at the caller's own
 * base_damage (no ability multiplier: this is the direct command path,
 * not the Barrage ability). */
void om_unit_fire_aoe_attack(om_world *w, uint32_t attacker_id, uint32_t target_id, double radius) {
    om_tac_state *st = om_tac(w);
    om_unit_row *attacker = om_registry_find_in(st, attacker_id);
    om_unit_row *center = om_registry_find_in(st, target_id);
    double cap, total = 0.0;
    uint32_t ids[st->n_units + 1];
    uint32_t j, n;
    if (!attacker || !center) return;
    om_economy_on_area_hit(w, center->x, center->y, radius);
    cap = attacker->base_damage * OM_AOE_DAMAGE_CAP_MULTIPLIER;
    n = om_grid_query_st(st, center->x, center->y, radius, ids, st->n_units);
    for (j = 0; j < n; j++) {
        om_unit_row *cand = &st->units[ids[j] - 1];
        double mult, dmg, remaining;
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == attacker->faction_id) continue;
        if (!om_tac_in_reach(w, attacker, cand)) continue;
        if (total >= cap) break;
        mult = om_resolve_hit_multiplier(w, attacker->category, cand);
        dmg = attacker->base_damage * mult * om_unit_output_multiplier(w, attacker_id)
              * (1.0 - om_unit_damage_reduction(w, cand->unit_id)) * om_tac_offset_mult(w, OM_REACH_AREA, attacker, cand);
        remaining = cap - total;
        if (dmg > remaining) dmg = remaining;
        cand->hp -= dmg;
        if (cand->hp < 0.0) cand->hp = 0.0;
        om_grid_sync(st, cand->unit_id - 1);
        om_tac_note_attacker(w, st, cand, attacker);
        total += dmg;
    }
    attacker->cooldown = 0.0;
    attacker->fired = 1;
    attacker->backswing_ticks_remaining = OM_BACKSWING_TICKS;
    attacker->backswing_active = 1;
}

double om_unit_get_hp(const om_world *w, uint32_t unit) {
    om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit);
    return row ? row->hp : 0.0;
}

uint32_t om_unit_get_target(const om_world *w, uint32_t unit) {
    om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit);
    return row ? row->target_id : 0;
}

void om_unit_clear_target(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (!row) return;
    row->target_id = 0;
}

double om_unit_hp(om_world *w, uint32_t unit_id) {
    return om_unit_get_hp(w, unit_id);
}

int om_unit_in_backswing(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return (row && row->backswing_active) ? 1 : 0;
}

int om_unit_in_flinch(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return (row && row->flinching) ? 1 : 0;
}

double om_unit_output_multiplier(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (!row) return 1.0;
    switch (row->unit_type) {
        case OM_UT_RAIDER:
            if (row->ability_phase == OM_ABILITY_PHASE_ACTIVE) return OM_ABILITY_SURGE_OUTPUT_MULT;
            break;
        case OM_UT_INTERCEPTOR:
            if (row->ability_phase == OM_ABILITY_PHASE_ACTIVE) return OM_ABILITY_INTERCEPT_OUTPUT_MULT;
            break;
        case OM_UT_VANGUARD:
            if (row->ability_bonus_on && row->ability_phase != OM_ABILITY_PHASE_IDLE) return OM_ABILITY_BRACE_OUTPUT_MULT;
            break;
        default: break;
    }
    return 1.0;
}

double om_unit_position_x(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return row ? row->x : 0.0;
}

double om_unit_position_y(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return row ? row->y : 0.0;
}

uint32_t om_unit_profile_ability_count(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? 1u : 0u;
}

double om_unit_profile_aoe_radius(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->aoe_radius : 0.0;
}

double om_unit_profile_attack_interval(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->attack_interval : 0.0;
}

double om_unit_profile_attack_range(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->attack_range : 0.0;
}

double om_unit_profile_base_damage(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->base_damage : 0.0;
}

int om_unit_profile_category(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->category : 0;
}

double om_unit_profile_dps(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    if (!p || p->attack_interval <= 0.0) return 0.0;
    return p->base_damage / p->attack_interval;
}

double om_unit_profile_layer_transition_time(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->layer_transition_time : 0.0;
}

double om_unit_profile_max_hp(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->max_hp : 0.0;
}

double om_unit_profile_sensor_radius(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->sensor_radius : 0.0;
}

double om_unit_profile_speed(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    return p ? p->speed : 0.0;
}

uint32_t om_unit_profile_trait_count(om_world *w, int unit_type) {
    /* Q-083-01 resolved: no trait exists in the launch roster's code today;
     * every built-in (and custom) unit type reports 0 until a trait pool
     * is built. om_unit_apply_trait_modifier below still works generically
     * for any future trait. */
    (void)w; (void)unit_type;
    return 0;
}

uint32_t om_unit_render_craft_count(om_world *w, int unit_type) {
    (void)w;
    if (unit_type == OM_UT_RAIDER || unit_type == OM_UT_INTERCEPTOR) {
        return OM_RENDER_CRAFT_COUNT_STRIKE;
    }
    return OM_RENDER_CRAFT_COUNT_DEFAULT;
}

double om_unit_render_silhouette_size(om_world *w, int unit_type) {
    const om_unit_type_profile *p = om_get_profile(w, unit_type);
    int category = p ? p->category : OM_CAT_STRIKE;
    switch (category) {
        case OM_CAT_LINE:  return OM_RENDER_SILHOUETTE_LINE;
        case OM_CAT_SIEGE: return OM_RENDER_SILHOUETTE_SIEGE;
        default:            return OM_RENDER_SILHOUETTE_STRIKE;
    }
}

void om_unit_set_ability_cooldown(om_world *w, uint32_t unit_id, double ticks) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (row) row->ability_cooldown = ticks;
}

void om_unit_set_brace_active(om_world *w, uint32_t unit_id, int on) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (row) row->force_brace_reduction = on ? 1 : 0;
}

void om_unit_set_elevation_tier(om_world *w, uint32_t unit_id, int tier) {
    /* STUB */
    (void)w; (void)unit_id; (void)tier;
}

void om_unit_set_fortify_active(om_world *w, uint32_t unit_id, int on) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (row) row->force_fortify_reduction = on ? 1 : 0;
}

void om_unit_set_hp(om_world *w, uint32_t p0, double p1) {
    om_unit_row *row = om_registry_find_in(om_tac(w), p0);
    if (row) {
        row->hp = p1;
        om_grid_sync(om_tac(w), p0 - 1);
    }
}

void om_unit_set_stealth(om_world *w, uint32_t unit_id, int on) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (row) row->stealth = on ? 1 : 0;
}

void om_unit_set_warden_aura_active(om_world *w, uint32_t unit_id, int on) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (row) row->force_warden_aura_reduction = on ? 1 : 0;
}

uint32_t om_unit_spawn(om_world *w, int unit_type, int32_t faction_id, double x, double y, uint32_t layer) {
    return om_unit_spawn_internal(w, unit_type, faction_id, x, y, layer);
}

uint32_t om_unit_spawn_combat(om_world *w, int32_t p1, double p2, double x) {
    return om_unit_spawn_internal(w, OM_UT_RAIDER, p1, p2, x, 0);
}

uint32_t om_unit_spawn_for_category(om_world *w, int category, int32_t faction_id, double x, double y, uint32_t layer) {
    int unit_type;
    switch (category) {
        case OM_CAT_LINE:  unit_type = OM_UT_VANGUARD; break;
        case OM_CAT_SIEGE: unit_type = OM_UT_BOMBARD; break;
        case OM_CAT_STRIKE:
        default:           unit_type = OM_UT_RAIDER; break;
    }
    return om_unit_spawn_internal(w, unit_type, faction_id, x, y, layer);
}

int32_t om_unit_target(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    return (row && row->target_id != 0) ? (int32_t)row->target_id : -1;
}

uint32_t om_unit_targeting_cohort(om_world *w, uint32_t unit_id) {
    return om_unit_cohort_slot(w, unit_id);
}

void om_unit_get_position(om_world *w, uint32_t unit_id, om_vec2 *byref) {
    if (!byref) return;
    byref->x = om_unit_position_x(w, unit_id);
    byref->y = om_unit_position_y(w, unit_id);
}

uint32_t om_tick_read_ability_events(om_world *w, om_ability_event *out, uint32_t max) {
    om_tac_state *st = om_tac(w);
    uint32_t n = st->n_ability_events;
    uint32_t i;
    if (n > max) n = max;
    for (i = 0; i < n; i++) out[i] = st->ability_events[i];
    st->n_ability_events = 0;
    return n;
}
/* Vanguard Brace phase as unit.c tracks it: 0 idle, 1 windup, 2 active
 * (bonus granted), 3 canceling (the mirrored 40-tick window); -1 for a
 * unit that has no Brace. */
int32_t om_unit_brace_phase(const om_world *w, uint32_t unit_id) {
    const om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit_id);
    return (row && row->unit_type == OM_UT_VANGUARD) ? row->ability_phase : -1;
}

/* For tactical_move.c's om_unit_get_leash_anchor: 1 and the anchor while an
 * attack-moving unit holds one, else 0. Needs a prototype in om_internal.h
 * before tactical_move.c can call it. */
int om_tac_unit_leash_anchor(const om_world *w, uint32_t unit_id, double *x, double *y) {
    const om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit_id);
    if (!row || !row->anchor_set) return 0;
    if (x) *x = row->anchor_x;
    if (y) *y = row->anchor_y;
    return 1;
}

uint32_t om_unit_count(const om_world *w) {
    const om_tac_state *st = om_tac_ro(w);
    uint32_t i, n = 0;
    if (!st) return 0;
    for (i = 0; i < st->n_units; i++) {
        if (st->units[i].in_use) n++;
    }
    return n;
}

int32_t om_unit_get_faction(const om_world *w, uint32_t unit_id) {
    const om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit_id);
    return row ? row->faction_id : -1;
}

int32_t om_unit_get_layer(const om_world *w, uint32_t unit_id) {
    const om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit_id);
    return row ? (int32_t)row->layer : -1;
}

int32_t om_unit_get_unit_type(const om_world *w, uint32_t unit_id) {
    const om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit_id);
    return row ? row->unit_type : -1;
}

/* Spawn order: index 0 is the first unit spawned since the last reset. */
uint32_t om_unit_id_at(const om_world *w, uint32_t index) {
    const om_tac_state *st = om_tac_ro(w);
    if (!st || index >= st->n_units || !st->units[index].in_use) return 0;
    return st->units[index].unit_id;
}
uint32_t om_tactical_tick_period(const om_world *w) {
    const om_tac_state *st = om_tac_ro(w);
    return st ? om_tac_period(st) : 1;
}
uint64_t om_tactical_base_tick(const om_world *w) {
    const om_tac_state *st = w ? om_tac_ro(w) : NULL;
    return st ? st->base_tick : 0;
}
uint32_t om_tactical_event_count(om_world *w) {
    const om_tac_state *st = w ? om_tac_ro(w) : NULL;
    return st ? st->n_events : 0;
}

int om_tactical_event_get_at(om_world *w, uint32_t i, int32_t *kind, uint32_t *a, int32_t *b, uint64_t *tick) {
    const om_tac_state *st = w ? om_tac_ro(w) : NULL;
    if (!st || i >= st->n_events) return -1;
    if (kind) *kind = st->events[i].kind;
    if (a) *a = st->events[i].a;
    if (b) *b = st->events[i].b;
    if (tick) *tick = st->events[i].tick;
    return 0;
}
int om_combat_can_engage(const om_world *w, uint32_t attacker, uint32_t target) {
    /* LAB-REV2 E0 contract stub: -1 (not built) until LAB-REV2-E2 writes the gates. See also: om_roster_set_cone. */
    (void)w; (void)attacker; (void)target;
    return -1;
}
/* ---- end generated stubs ---- */

/* ---- net hooks (lockstep spec 2026-10-05) ---- */
#define OM_UNIT_CK_PRIME 1099511628211ULL
#define OM_UNIT_CK_SEED 14695981039346656037ULL
#define OM_UNIT_CK_NULL 0x6e756c6c74616374ULL
#define OM_UNIT_CK_MIX_SHIFT 29
#define OM_UNIT_CK_SECTION 3

static uint64_t om_unit_ck_word(uint64_t h, uint64_t v) {
    h = (h ^ v) * OM_UNIT_CK_PRIME;
    return h ^ (h >> OM_UNIT_CK_MIX_SHIFT);
}

static uint64_t om_unit_ck_dbl(uint64_t h, double d) {
    uint64_t v;
    memcpy(&v, &d, sizeof v);
    return om_unit_ck_word(h, v);
}

static uint64_t om_unit_ck_row(const om_unit_row *r) {
    uint64_t h = OM_UNIT_CK_SEED;
#define W(f) h = om_unit_ck_word(h, (uint64_t)(int64_t)(r->f))
#define D(f) h = om_unit_ck_dbl(h, r->f)
    W(unit_id); W(in_use); W(unit_type); W(category); W(faction_id);
    D(x); D(y); W(layer); D(hp); D(max_hp); D(base_damage); D(attack_interval);
    D(attack_range); D(cooldown); W(target_id);
    W(ability_phase); W(ability_bonus_on); W(ability_ticks_remaining);
    D(ability_cooldown); D(ability_target_x); D(ability_target_y);
    W(backswing_ticks_remaining); W(backswing_active); W(force_brace_reduction);
    W(force_fortify_reduction); W(force_warden_aura_reduction);
    W(order); D(order_x); D(order_y); D(issued_x); D(issued_y); W(halted);
    W(am_gid); W(am_engaged); W(guard); W(anchor_set); D(anchor_x); D(anchor_y);
    W(flinching); D(flinch_x); D(flinch_y); W(last_attacker); W(fire_pending);
    W(stealth); W(suppress_auto); W(brace_auto); W(fortify_auto);
    D(last_seen_x); D(last_seen_y); W(fired);
    /* F5: mixed only while a give-up run, an exclusion or a firing spot is live, so a world that never blocks hashes as it did */
    if (r->giveup_target || r->excl_id || r->spot_set) {
        W(giveup_target); W(giveup_ticks); D(giveup_ref); W(excl_id); W(excl_until); W(spot_set); D(spot_x); D(spot_y);
    }
#undef W
#undef D
    return h;
}

static uint64_t om_unit_ck_section(const om_world *w) {
    const om_tac_state *st = w ? (const om_tac_state *)w->tactical_state : NULL;
    if (!st) return OM_UNIT_CK_NULL;
    uint64_t h = OM_UNIT_CK_SEED;
    h = om_unit_ck_word(h, st->n_units);
    h = om_unit_ck_word(h, st->next_unit_id);
    h = om_unit_ck_word(h, st->current_tick);
    h = om_unit_ck_word(h, st->base_tick);
    h = om_unit_ck_word(h, (uint64_t)(int64_t)st->abilities_disabled);
    h = om_unit_ck_word(h, st->validated_tick);
    h = om_unit_ck_word(h, st->n_wardens);
    h = om_unit_ck_word(h, st->n_bastions);
    h = om_unit_ck_word(h, st->n_custom_types);
    for (uint32_t i = 0; i < st->n_custom_types && i < OM_MAX_CUSTOM_TYPES; i++) {
        const om_custom_type_row *c = &st->custom_types[i];
        const om_unit_type_profile *p = &c->profile;
        h = om_unit_ck_word(h, c->type_id);
        h = om_unit_ck_word(h, (uint64_t)(int64_t)c->in_use);
        h = om_unit_ck_word(h, (uint64_t)(int64_t)p->category);
        h = om_unit_ck_dbl(h, p->max_hp);
        h = om_unit_ck_dbl(h, p->base_damage);
        h = om_unit_ck_dbl(h, p->attack_interval);
        h = om_unit_ck_dbl(h, p->attack_range);
        h = om_unit_ck_dbl(h, p->speed);
        h = om_unit_ck_dbl(h, p->sensor_radius);
        h = om_unit_ck_dbl(h, p->layer_transition_time);
        h = om_unit_ck_dbl(h, p->aoe_radius);
    }
    h = om_unit_ck_word(h, st->n_ability_events);
    for (uint32_t i = 0; i < st->n_ability_events && i < OM_ABILITY_EVENT_BUFFER_CAP; i++) {
        const om_ability_event *e = &st->ability_events[i];
        h = om_unit_ck_word(h, e->tick);
        h = om_unit_ck_word(h, e->unit_id);
        h = om_unit_ck_word(h, (uint64_t)(int64_t)e->ability_id);
        h = om_unit_ck_dbl(h, e->target_x);
        h = om_unit_ck_dbl(h, e->target_y);
        h = om_unit_ck_word(h, e->duration);
        h = om_unit_ck_word(h, e->telegraph_ticks);
        h = om_unit_ck_word(h, e->cue_id);
        h = om_unit_ck_dbl(h, e->radius);
    }
    for (uint32_t i = 0; i < st->n_units; i++)
        h = om_unit_ck_word(h, om_unit_ck_row(&st->units[i]));
    return h;
}

static uint32_t om_unit_ck_per_unit(const om_world *w, uint64_t *out, uint32_t cap) {
    const om_tac_state *st = w ? (const om_tac_state *)w->tactical_state : NULL;
    if (!st) return 0;
    uint32_t n = st->next_unit_id;
    if (!out || !cap) return n;
    for (uint32_t i = 0; i < cap && i < n; i++) out[i] = 0;
    for (uint32_t i = 0; i < st->n_units; i++) {
        const om_unit_row *r = &st->units[i];
        if (r->in_use && r->unit_id && r->unit_id < cap && r->unit_id < n)
            out[r->unit_id] = om_unit_ck_row(r);
    }
    return n;
}

/* Save hooks, slot tactical_state: the fields the section hash covers, little-endian. Caches (grid, aura scratch,
 * tick period) are rebuilt on first use; grid.built stays 0 after a load so the grid is rebuilt in index order. */
#define OM_UNIT_SV_U32 4u
#define OM_UNIT_SV_U64 8u

typedef struct {
    uint8_t *out;
    uint32_t pos;
} om_unit_sw;

static void om_unit_sw_put(om_unit_sw *s, uint64_t v, uint32_t width) {
    for (uint32_t i = 0; i < width; i++, s->pos++)
        if (s->out) s->out[s->pos] = (uint8_t)((v >> (OM_SAVE_BYTE_BITS * i)) & OM_SAVE_BYTE_MASK);
}

static void om_unit_sw_dbl(om_unit_sw *s, double d) {
    uint64_t v;
    memcpy(&v, &d, sizeof v);
    om_unit_sw_put(s, v, OM_UNIT_SV_U64);
}

typedef struct {
    const uint8_t *p;
    uint32_t len, pos;
    int ok;
} om_unit_sr;

static uint64_t om_unit_sr_get(om_unit_sr *s, uint32_t width) {
    if (!s->ok || width > s->len - s->pos) {
        s->ok = 0;
        return 0;
    }
    uint64_t v = 0;
    for (uint32_t i = 0; i < width; i++) v |= ((uint64_t)s->p[s->pos + i]) << (OM_SAVE_BYTE_BITS * i);
    s->pos += width;
    return v;
}

static double om_unit_sr_dbl(om_unit_sr *s) {
    uint64_t v = om_unit_sr_get(s, OM_UNIT_SV_U64);
    double d;
    memcpy(&d, &v, sizeof d);
    return d;
}

static uint32_t om_unit_sr_count(om_unit_sr *s, uint32_t cap) {
    uint32_t n = (uint32_t)om_unit_sr_get(s, OM_UNIT_SV_U32);
    if (n > cap) {
        s->ok = 0;
        return 0;
    }
    return n;
}

/* row fields in hash order: U unsigned 32, I signed 32 (int), D double */
#define OM_UNIT_ROW_FIELDS(U, I, D) \
    U(unit_id) I(in_use) I(unit_type) I(category) I(faction_id) D(x) D(y) U(layer) D(hp) D(max_hp) \
    D(base_damage) D(attack_interval) D(attack_range) D(cooldown) U(target_id) \
    I(ability_phase) I(ability_bonus_on) U(ability_ticks_remaining) D(ability_cooldown) \
    D(ability_target_x) D(ability_target_y) U(backswing_ticks_remaining) I(backswing_active) \
    I(force_brace_reduction) I(force_fortify_reduction) I(force_warden_aura_reduction) \
    I(order) D(order_x) D(order_y) D(issued_x) D(issued_y) I(halted) U(am_gid) I(am_engaged) \
    I(guard) I(anchor_set) D(anchor_x) D(anchor_y) I(flinching) D(flinch_x) D(flinch_y) \
    U(last_attacker) I(fire_pending) I(stealth) I(suppress_auto) I(brace_auto) I(fortify_auto) \
    D(last_seen_x) D(last_seen_y) I(fired)

static void om_unit_sw_row(om_unit_sw *s, const om_unit_row *r) {
#define U(f) om_unit_sw_put(s, r->f, OM_UNIT_SV_U32);
#define I(f) om_unit_sw_put(s, (uint32_t)(int32_t)r->f, OM_UNIT_SV_U32);
#define D(f) om_unit_sw_dbl(s, r->f);
    OM_UNIT_ROW_FIELDS(U, I, D)
#undef U
#undef I
#undef D
}

static void om_unit_sr_row(om_unit_sr *s, om_unit_row *r) {
#define U(f) r->f = (uint32_t)om_unit_sr_get(s, OM_UNIT_SV_U32);
#define I(f) r->f = (int)(int32_t)(uint32_t)om_unit_sr_get(s, OM_UNIT_SV_U32);
#define D(f) r->f = om_unit_sr_dbl(s);
    OM_UNIT_ROW_FIELDS(U, I, D)
#undef U
#undef I
#undef D
}

static void om_unit_sw_state(om_unit_sw *s, const om_tac_state *st) {
    om_unit_sw_put(s, st->n_units, OM_UNIT_SV_U32);
    om_unit_sw_put(s, st->next_unit_id, OM_UNIT_SV_U32);
    om_unit_sw_put(s, st->current_tick, OM_UNIT_SV_U64);
    om_unit_sw_put(s, st->base_tick, OM_UNIT_SV_U64);
    om_unit_sw_put(s, (uint32_t)(int32_t)st->abilities_disabled, OM_UNIT_SV_U32);
    om_unit_sw_put(s, st->validated_tick, OM_UNIT_SV_U64);
    om_unit_sw_put(s, st->n_wardens, OM_UNIT_SV_U32);
    om_unit_sw_put(s, st->n_bastions, OM_UNIT_SV_U32);
    om_unit_sw_put(s, st->n_custom_types, OM_UNIT_SV_U32);
    for (uint32_t i = 0; i < st->n_custom_types; i++) {
        const om_custom_type_row *c = &st->custom_types[i];
        const om_unit_type_profile *p = &c->profile;
        om_unit_sw_put(s, c->type_id, OM_UNIT_SV_U32);
        om_unit_sw_put(s, (uint32_t)(int32_t)c->in_use, OM_UNIT_SV_U32);
        om_unit_sw_put(s, (uint32_t)(int32_t)p->category, OM_UNIT_SV_U32);
        om_unit_sw_dbl(s, p->max_hp);
        om_unit_sw_dbl(s, p->base_damage);
        om_unit_sw_dbl(s, p->attack_interval);
        om_unit_sw_dbl(s, p->attack_range);
        om_unit_sw_dbl(s, p->speed);
        om_unit_sw_dbl(s, p->sensor_radius);
        om_unit_sw_dbl(s, p->layer_transition_time);
        om_unit_sw_dbl(s, p->aoe_radius);
    }
    om_unit_sw_put(s, st->n_ability_events, OM_UNIT_SV_U32);
    for (uint32_t i = 0; i < st->n_ability_events; i++) {
        const om_ability_event *e = &st->ability_events[i];
        om_unit_sw_put(s, e->tick, OM_UNIT_SV_U64);
        om_unit_sw_put(s, e->unit_id, OM_UNIT_SV_U32);
        om_unit_sw_put(s, (uint32_t)e->ability_id, OM_UNIT_SV_U32);
        om_unit_sw_dbl(s, e->target_x);
        om_unit_sw_dbl(s, e->target_y);
        om_unit_sw_put(s, e->duration, OM_UNIT_SV_U32);
        om_unit_sw_put(s, e->telegraph_ticks, OM_UNIT_SV_U32);
        om_unit_sw_put(s, e->cue_id, OM_UNIT_SV_U32);
        om_unit_sw_dbl(s, e->radius);
    }
    for (uint32_t i = 0; i < st->n_units; i++) om_unit_sw_row(s, &st->units[i]);
}

static uint32_t om_unit_save_size(const om_world *w) {
    const om_tac_state *st = om_tac_ro(w);
    om_unit_sw s = {NULL, 0};
    if (!st) return 0;
    om_unit_sw_state(&s, st);
    return s.pos;
}

static void om_unit_save_write(const om_world *w, uint8_t *out) {
    const om_tac_state *st = om_tac_ro(w);
    om_unit_sw s = {out, 0};
    if (st && out) om_unit_sw_state(&s, st);
}

static int om_unit_save_read(om_world *w, const uint8_t *buf, uint32_t len) {
    if (len == 0) return 0;
    if (!buf) return 1;
    om_unit_sr s = {buf, len, 0, 1};
    om_tac_state *st = (om_tac_state *)calloc(1, sizeof(om_tac_state));
    if (!st) return 1;
    st->n_units = om_unit_sr_count(&s, OM_MAX_UNITS);
    st->next_unit_id = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
    st->current_tick = om_unit_sr_get(&s, OM_UNIT_SV_U64);
    st->base_tick = om_unit_sr_get(&s, OM_UNIT_SV_U64);
    st->abilities_disabled = (int)(int32_t)(uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
    st->validated_tick = om_unit_sr_get(&s, OM_UNIT_SV_U64);
    st->n_wardens = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
    st->n_bastions = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
    st->n_custom_types = om_unit_sr_count(&s, OM_MAX_CUSTOM_TYPES);
    for (uint32_t i = 0; i < st->n_custom_types && s.ok; i++) {
        om_custom_type_row *c = &st->custom_types[i];
        om_unit_type_profile *p = &c->profile;
        c->type_id = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        c->in_use = (int)(int32_t)(uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        p->category = (int)(int32_t)(uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        p->max_hp = om_unit_sr_dbl(&s);
        p->base_damage = om_unit_sr_dbl(&s);
        p->attack_interval = om_unit_sr_dbl(&s);
        p->attack_range = om_unit_sr_dbl(&s);
        p->speed = om_unit_sr_dbl(&s);
        p->sensor_radius = om_unit_sr_dbl(&s);
        p->layer_transition_time = om_unit_sr_dbl(&s);
        p->aoe_radius = om_unit_sr_dbl(&s);
    }
    st->n_ability_events = om_unit_sr_count(&s, OM_ABILITY_EVENT_BUFFER_CAP);
    for (uint32_t i = 0; i < st->n_ability_events && s.ok; i++) {
        om_ability_event *e = &st->ability_events[i];
        e->tick = om_unit_sr_get(&s, OM_UNIT_SV_U64);
        e->unit_id = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        e->ability_id = (int32_t)(uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        e->target_x = om_unit_sr_dbl(&s);
        e->target_y = om_unit_sr_dbl(&s);
        e->duration = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        e->telegraph_ticks = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        e->cue_id = (uint32_t)om_unit_sr_get(&s, OM_UNIT_SV_U32);
        e->radius = om_unit_sr_dbl(&s);
    }
    if (!s.ok || st->next_unit_id < 1 || st->next_unit_id > OM_MAX_UNITS + 1 ||
        !om_tac_reserve(st, st->n_units ? st->n_units : 1)) {
        om_tac_state_free(st);
        return 1;
    }
    for (uint32_t i = 0; i < st->n_units && s.ok; i++) {
        om_unit_sr_row(&s, &st->units[i]);
        if (st->units[i].in_use && st->units[i].unit_id >= st->next_unit_id) s.ok = 0;
    }
    if (!s.ok || s.pos != len) {
        om_tac_state_free(st);
        return 1;
    }
    for (uint32_t i = 0; i < st->n_units; i++) st->grid.cell_of[i] = OM_GRID_UNLINKED;
    if (w->tactical_state && w->tactical_state_free) w->tactical_state_free(w->tactical_state);
    w->tactical_state = st;
    w->tactical_state_free = om_tac_state_free;
    return 0;
}

void om_unit_install_net_hooks(om_world *w) {
    w->tactical_state_size = om_unit_save_size;
    w->tactical_state_write = om_unit_save_write;
    w->tactical_state_read = om_unit_save_read;
    w->net_section_hash[OM_UNIT_CK_SECTION] = om_unit_ck_section;
    w->net_unit_hashes = om_unit_ck_per_unit;
}
