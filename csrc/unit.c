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

/* Unit capacity of one tactical battle: E-11's 10,000-unit scale requirement
 * plus headroom. The per-unit arrays in om_tac_state grow from
 * OM_UNITS_INITIAL_CAP by doubling (om_tac_reserve), so a world that never
 * fights allocates nothing and a small fight allocates little. */
#define OM_MAX_UNITS 10100
#define OM_UNITS_INITIAL_CAP 64
#define OM_GRID_UNLINKED 0xFFFFFFFFu
/* Spatial grid (om_grid_query_circle): cell edge in world units, the cell
 * count cap per axis (a wider bounding box enlarges the cell instead), and
 * the slack added to a query's cell range so a rounding step in the cell
 * arithmetic can never drop a unit the exact circle test accepts. */
#define OM_GRID_CELL_SIZE 400.0
#define OM_GRID_MAX_DIM 256
#define OM_GRID_PAD 1e-6
#define OM_GRID_INSERTION_SORT_MAX 32
/* om_tac_nearest_hostile: a second-nearest distance within this of the
 * nearest hands the choice back to the ordered reference scan. */
#define OM_TIE_SCAN_WINDOW (4.0 * OM_TIE_EPSILON)
#define OM_MAX_CUSTOM_TYPES 64
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

/* S-082 launch roster (tests/csim/test_E11_S082_the_six.py ROSTER_TABLE,
 * the fenced source of truth) -- one #define per stat per unit type so the
 * alg_constants.py lint sees no bare literal outside a #define line. */
#define OM_ROSTER_RAIDER_HP 250.0
#define OM_ROSTER_RAIDER_DAMAGE 9.0
#define OM_ROSTER_RAIDER_INTERVAL 0.8
#define OM_ROSTER_RAIDER_RANGE 200.0
#define OM_ROSTER_RAIDER_SPEED 150.0
#define OM_ROSTER_RAIDER_SENSOR 800.0
#define OM_ROSTER_RAIDER_LAYER_TRANSITION 1.0
#define OM_ROSTER_RAIDER_AOE 0.0

#define OM_ROSTER_INTERCEPTOR_HP 325.0
#define OM_ROSTER_INTERCEPTOR_DAMAGE 6.0
#define OM_ROSTER_INTERCEPTOR_INTERVAL 1.0
#define OM_ROSTER_INTERCEPTOR_RANGE 250.0
#define OM_ROSTER_INTERCEPTOR_SPEED 130.0
#define OM_ROSTER_INTERCEPTOR_SENSOR 1000.0
#define OM_ROSTER_INTERCEPTOR_LAYER_TRANSITION 1.2
#define OM_ROSTER_INTERCEPTOR_AOE 0.0

#define OM_ROSTER_VANGUARD_HP 500.0
#define OM_ROSTER_VANGUARD_DAMAGE 7.5
#define OM_ROSTER_VANGUARD_INTERVAL 1.2
#define OM_ROSTER_VANGUARD_RANGE 300.0
#define OM_ROSTER_VANGUARD_SPEED 80.0
#define OM_ROSTER_VANGUARD_SENSOR 700.0
#define OM_ROSTER_VANGUARD_LAYER_TRANSITION 2.5
#define OM_ROSTER_VANGUARD_AOE 0.0

#define OM_ROSTER_WARDEN_HP 375.0
#define OM_ROSTER_WARDEN_DAMAGE 4.0
#define OM_ROSTER_WARDEN_INTERVAL 1.5
#define OM_ROSTER_WARDEN_RANGE 350.0
#define OM_ROSTER_WARDEN_SPEED 70.0
#define OM_ROSTER_WARDEN_SENSOR 800.0
#define OM_ROSTER_WARDEN_LAYER_TRANSITION 2.0
#define OM_ROSTER_WARDEN_AOE 0.0

#define OM_ROSTER_BOMBARD_HP 400.0
#define OM_ROSTER_BOMBARD_DAMAGE 17.5
#define OM_ROSTER_BOMBARD_INTERVAL 3.0
#define OM_ROSTER_BOMBARD_RANGE 1200.0
#define OM_ROSTER_BOMBARD_SPEED 50.0
#define OM_ROSTER_BOMBARD_SENSOR 300.0
#define OM_ROSTER_BOMBARD_LAYER_TRANSITION 4.0
#define OM_ROSTER_BOMBARD_AOE 150.0

#define OM_ROSTER_BASTION_HP 1050.0
#define OM_ROSTER_BASTION_DAMAGE 7.0
#define OM_ROSTER_BASTION_INTERVAL 1.8
#define OM_ROSTER_BASTION_RANGE 800.0
#define OM_ROSTER_BASTION_SPEED 40.0
#define OM_ROSTER_BASTION_SENSOR 300.0
#define OM_ROSTER_BASTION_LAYER_TRANSITION 5.0
#define OM_ROSTER_BASTION_AOE 0.0

/* Fallback profile for an unrecognized unit_type (never a roster/custom
 * hit) -- keeps om_unit_spawn from producing a unit that cannot fight or
 * be queried, without inventing roster numbers. */
#define OM_UNIT_FALLBACK_HP 100.0
#define OM_UNIT_FALLBACK_DAMAGE 5.0
#define OM_UNIT_FALLBACK_INTERVAL 1.0
#define OM_UNIT_FALLBACK_RANGE 100.0

/* ALG-62 `_RETURN_FIRE_FLEE_DIST` (simulation/damage.py): a unit that
 * cannot return fire moves this far directly away from the attacker.
 * R-087-05's anchor leash (simulation/movement.py `_ATTACK_MOVE_LEASH_SQ`
 * = 200 * 200) is the same distance. Neither has an IDENT binding in
 * algorithms.md, so om_constants.h has no OM_ name for them. */
#define OM_RETURN_FIRE_FLEE_DIST 200.0
#define OM_ATTACK_MOVE_LEASH_DIST 200.0

/* order kinds unit.c itself records (attack-move and attack-target;
 * a plain move and no order at all are read back from tactical_move.c) */
#define OM_ORDER_NONE 0
#define OM_ORDER_ATTACK_MOVE 1
#define OM_ORDER_ATTACK_TARGET 2

/* om_tactical_spawn_force_composition("default_balanced"): the only source
 * for the mix is the fenced test's own example (tests/csim/
 * test_E11_S085_long_enough_to_think.py::test_R_085_02: 15 Raider, 10
 * Interceptor, 15 Vanguard, 5 Warden, 3 Bombard, 2 Bastion per 50); the
 * bible names no numbers. Shares are per 50 units. */
#define OM_COMPOSITION_BASE 50
#define OM_COMPOSITION_RAIDER 15
#define OM_COMPOSITION_INTERCEPTOR 10
#define OM_COMPOSITION_VANGUARD 15
#define OM_COMPOSITION_WARDEN 5
#define OM_COMPOSITION_BOMBARD 3
#define OM_COMPOSITION_BASTION 2

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

/* S-086/ALG-63: one ability per unit type, exact numbers per
 * tests/csim/test_E11_S086_one_ability_each.py. OM_FORTIFY_RADIUS,
 * OM_INTERCEPT_DETECTION_RADIUS, OM_AOE_DAMAGE_CAP_MULTIPLIER and the
 * Warden aura constants already live in om_constants.h (ALG-60/61/63) and
 * are reused here rather than redefined. */
#define OM_ABILITY_SURGE_DURATION_TICKS 60
#define OM_ABILITY_SURGE_SPEED_MULT 2.5
#define OM_ABILITY_SURGE_OUTPUT_MULT 2.0
#define OM_ABILITY_SURGE_COOLDOWN_TICKS 1500.0

#define OM_ABILITY_INTERCEPT_SPEED_MULT 1.8
#define OM_ABILITY_INTERCEPT_OUTPUT_MULT 1.5
#define OM_ABILITY_INTERCEPT_COOLDOWN_TICKS 600.0

#define OM_ABILITY_BRACE_WINDUP_TICKS 40
#define OM_ABILITY_BRACE_DAMAGE_REDUCTION 0.50
#define OM_ABILITY_BRACE_OUTPUT_MULT 1.3
#define OM_ABILITY_BRACE_COOLDOWN_TICKS 700.0

#define OM_ABILITY_RALLY_HEAL_AMOUNT 112.0
#define OM_ABILITY_RALLY_RADIUS 400.0
#define OM_ABILITY_RALLY_COOLDOWN_TICKS 1500.0
/* Auto-trigger only ("a damaged friendly", R-086-08) reads as meaningfully
 * wounded, not merely off full HP: test_R_083_03 (must stay green) has a
 * Warden with a friendly at 400/500 HP (0.80) in radius that must NOT
 * auto-fire Rally (only the passive aura applies that tick), while
 * test_R_086_08 has one at 200/500 (0.40) that must. 0.5 cleanly separates
 * them; the manual/instant heal itself (om_ability_do_rally) has no such
 * gate -- it heals every friendly in radius regardless of current HP,
 * per R-086-04. */
#define OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION 0.5

#define OM_ABILITY_BARRAGE_TELEGRAPH_TICKS 30
#define OM_ABILITY_BARRAGE_DAMAGE_MULT 3.0
#define OM_ABILITY_BARRAGE_RADIUS 100.0
#define OM_ABILITY_BARRAGE_COOLDOWN_TICKS 1800.0

#define OM_ABILITY_FORTIFY_DURATION_TICKS 400
#define OM_ABILITY_FORTIFY_DAMAGE_REDUCTION 0.20
#define OM_ABILITY_FORTIFY_SPEED_MULT 0.4
#define OM_ABILITY_FORTIFY_COOLDOWN_TICKS 1400.0

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
    int      anchor_set;
    double   anchor_x, anchor_y;
    int      flinching;
    double   flinch_x, flinch_y;
    uint32_t last_attacker;
    int      stealth;
    /* set each tactical tick while the unit is under an order (move,
     * attack-move, attack-target) or fleeing: a threshold auto-activation
     * (om_ability_autotrigger_scan) is auto-engagement, and the order wins
     * over it (R-087-02); a Brace it started would also pin the unit. */
    int      suppress_auto;
    /* the current Brace was started by the threshold scan, not by a player
     * activation: a later order cancels it (om_tac_unit_ai). */
    int      brace_auto;
    /* where an attack-target order last saw its target (S-093): refreshed
     * every tick the target is visible to the unit's faction. */
    double   last_seen_x, last_seen_y;
} om_unit_row;

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
} om_grid;

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
    /* units of each type ever spawned since the last reset (a unit's type
     * never changes): zero means no candidate can match, so the aura and
     * fortify scans in om_unit_damage_reduction are skipped. */
    uint32_t            n_wardens, n_bastions;
} om_tac_state;

static void om_tac_release_arrays(om_tac_state *st) {
    free(st->units);
    free(st->aura_count);
    free(st->grid.head);
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
static om_tac_state *om_tac(om_world *w) {
    om_tac_state *st = (om_tac_state *)w->tactical_state;
    if (!st) {
        st = (om_tac_state *)calloc(1, sizeof(om_tac_state));
        st->next_unit_id = 1;
        w->tactical_state = st;
        w->tactical_state_free = om_tac_state_free;
    }
    return st;
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

static void om_grid_link(om_tac_state *st, uint32_t i) {
    om_grid *g = &st->grid;
    uint32_t cell = om_grid_cell_of_row(g, &st->units[i]);
    g->cell_of[i] = cell;
    g->prev[i] = 0;
    g->next[i] = g->head[cell];
    if (g->head[cell]) g->prev[g->head[cell] - 1] = i + 1;
    g->head[cell] = i + 1;
}

static void om_grid_unlink(om_tac_state *st, uint32_t i) {
    om_grid *g = &st->grid;
    if (g->prev[i]) g->next[g->prev[i] - 1] = g->next[i];
    else g->head[g->cell_of[i]] = g->next[i];
    if (g->next[i]) g->prev[g->next[i] - 1] = g->prev[i];
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
        g->head = (uint32_t *)malloc((size_t)ncells * sizeof(uint32_t));
        g->head_cap = g->head ? ncells : 0;
        if (!g->head) return;
    }
    memset(g->head, 0, (size_t)ncells * sizeof(uint32_t));
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
    it->cur = g->head[(uint32_t)it->cy * (uint32_t)g->cols + (uint32_t)it->cx];
}

uint32_t om_grid_iter_next(om_grid_iter *it) {
    om_tac_state *st = (om_tac_state *)it->state;
    const om_grid *g;
    if (it->done) return 0;
    g = &st->grid;
    for (;;) {
        while (it->cur) {
            const om_unit_row *u = &st->units[it->cur - 1];
            it->cur = g->next[it->cur - 1];
            if (om_tac_dist_le(u->x - it->x, u->y - it->y, it->r)) return u->unit_id;
        }
        if (++it->cx > it->cx1) {
            it->cx = it->cx0;
            if (++it->cy > it->cy1) { it->done = 1; return 0; }
        }
        it->cur = g->head[(uint32_t)it->cy * (uint32_t)g->cols + (uint32_t)it->cx];
    }
}

void om_grid_iter_begin(om_grid_iter *it, om_world *w, double x, double y, double r) {
    om_grid_iter_begin_st(it, om_tac(w), x, y, r);
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

static uint32_t om_unit_spawn_internal(om_world *w, int unit_type, int32_t faction_id,
                                        double x, double y, uint32_t layer) {
    const om_unit_type_profile *prof;
    om_unit_row *row;
    om_tac_state *st = om_tac(w);
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

static void om_tactical_apply_hit(om_world *w, om_unit_row *attacker, om_unit_row *target) {
    double mult = om_resolve_hit_multiplier(w, attacker->category, target);
    double output_mult = om_unit_output_multiplier(w, attacker->unit_id);
    double reduction = om_unit_damage_reduction(w, target->unit_id);
    double dmg = attacker->base_damage * mult * output_mult * (1.0 - reduction);
    target->hp -= dmg;
    if (target->hp < 0.0) target->hp = 0.0;
    om_grid_sync(om_tac(w), target->unit_id - 1);
    target->last_attacker = attacker->unit_id;
    attacker->cooldown = 0.0;
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

/* R-083-03/Q-084-01: n Wardens in range give diminishing reduction (first
 * 0.10, each additional Warden half the previous one's contribution --
 * equivalently 1 - (1 - OM_WARDEN_AURA_DAMAGE_REDUCTION)^n), computed by
 * repeated multiplication rather than a libm pow() call (determinism
 * contract, scripts/specfactory/libm_lint.py bans pow()). */
static double om_warden_aura_reduction_for(om_tac_state *st, const om_unit_row *target) {
    uint32_t id;
    int n = 0;
    double undamaged_factor;
    om_grid_iter it;
    if (st->n_wardens == 0) {
        if (!st->grid.built) om_grid_rebuild(st);
        return 0.0;
    }
    om_grid_iter_begin_st(&it, st, target->x, target->y, (double)OM_WARDEN_AURA_RADIUS);
    while ((id = om_grid_iter_next(&it)) != 0) {
        const om_unit_row *cand = &st->units[id - 1];
        if (cand->hp <= 0.0) continue;
        if (cand->unit_type != OM_UT_WARDEN) continue;
        if (cand->faction_id != target->faction_id) continue;
        n++;
    }
    if (n <= 0) return 0.0;
    undamaged_factor = 1.0;
    while (n-- > 0) undamaged_factor *= (1.0 - OM_WARDEN_AURA_DAMAGE_REDUCTION);
    return 1.0 - undamaged_factor;
}

/* R-083-03: healing stacks linearly, unlike the damage reduction above. */
static void om_tactical_apply_aura_regen(om_world *w) {
    om_tac_state *st = om_tac(w);
    uint32_t i, id;
    memset(st->aura_count, 0, (size_t)st->n_units * sizeof(uint32_t));
    for (i = 0; i < st->n_units; i++) {
        const om_unit_row *warden = &st->units[i];
        om_grid_iter it;
        if (!warden->in_use || warden->hp <= 0.0 || warden->unit_type != OM_UT_WARDEN) continue;
        om_grid_iter_begin_st(&it, st, warden->x, warden->y, (double)OM_WARDEN_AURA_RADIUS);
        while ((id = om_grid_iter_next(&it)) != 0) {
            const om_unit_row *cand = &st->units[id - 1];
            if (cand->hp <= 0.0 || cand->faction_id != warden->faction_id) continue;
            st->aura_count[id - 1]++;
        }
    }
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (st->aura_count[i] > 0) {
            u->hp += OM_WARDEN_AURA_REPAIR_RATE * (double)st->aura_count[i] * (double)om_tac_period(st);
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

/* The unit ids ascend in the old sorted scan and only a strictly smaller
 * distance replaced the best, so the answer is the lowest id at the minimum
 * distance; the unordered grid walk reaches it by comparing (d2, id). */
static om_unit_row *om_tac_nearest_enemy_within_range(om_tac_state *st, const om_unit_row *self, double range) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0;
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_st(&it, st, self->x, self->y, range);
    while ((id = om_grid_iter_next(&it)) != 0) {
        om_unit_row *cand = &st->units[id - 1];
        double dx, dy, d2;
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        dx = cand->x - self->x; dy = cand->y - self->y; d2 = dx * dx + dy * dy;
        if (!best || d2 < best_d2 || (d2 == best_d2 && id < best->unit_id)) { best = cand; best_d2 = d2; }
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
    om_grid_iter_begin_st(&it, st, self->x, self->y, range);
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

static int om_tac_badly_damaged_friendly_within(om_tac_state *st, const om_unit_row *self, double range) {
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_st(&it, st, self->x, self->y, range);
    while ((id = om_grid_iter_next(&it)) != 0) {
        const om_unit_row *cand = &st->units[id - 1];
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id != self->faction_id) continue;
        if (cand->hp >= cand->max_hp * OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION) continue;
        return 1;
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
        if (cand->layer != u->layer) continue;
        if (total >= cap) break;
        mult = om_resolve_hit_multiplier(w, u->category, cand);
        dmg = per_hit_base * mult;
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
        case OM_UT_BASTION:  om_ability_start_fortify(st, u); break;
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
static void om_ability_autotrigger_scan(om_tac_state *st) {
    uint32_t i;
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
                om_unit_row *tgt = om_tac_nearest_enemy_within_range(st, u, u->attack_range);
                if (tgt) om_ability_start_barrage(st, u, tgt->x, tgt->y);
                break;
            }
            case OM_UT_BASTION:
                if (om_tac_count_friendlies_within(st, u, OM_FORTIFY_RADIUS) >= 2) om_ability_start_fortify(st, u);
                break;
            default: break;
        }
    }
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
    if (!st->abilities_disabled) om_ability_autotrigger_scan(st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        switch (u->unit_type) {
            case OM_UT_RAIDER:   om_ability_tick_surge(u, period); break;
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
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer) continue;
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
    for (cur = g->head[cell]; cur; cur = g->next[cur - 1]) {
        om_unit_row *cand = &st->units[cur - 1];
        double dx = cand->x - self->x, dy = cand->y - self->y, d2;
        if (!om_tac_dist_le(dx, dy, radius)) continue;
        if (cand->hp <= 0.0 || cand->stealth) continue;
        if (!om_tac_hostile(self, cand) || cand->layer != self->layer) continue;
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

static int om_tac_hostile_within(om_tac_state *st, const om_unit_row *self, double radius) {
    uint32_t id;
    om_grid_iter it;
    om_grid_iter_begin_st(&it, st, self->x, self->y, radius);
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
 * (0 during backswing or a Brace). Returns 1 once (tx, ty) is reached. */
static int om_tac_step_toward(om_world *w, om_unit_row *u, double tx, double ty) {
    double dx = tx - u->x, dy = ty - u->y;
    double d = sqrt(dx * dx + dy * dy);
    double step = om_unit_effective_speed(w, u->unit_id) / (double)OM_TACTICAL_TICK_RATE
                  * (double)om_tac_period(om_tac(w));
    if (d <= OM_TIE_EPSILON) return 1;
    if (step <= 0.0) return 0;
    if (d <= step) {
        u->x = tx; u->y = ty;
    } else {
        u->x += dx / d * step;
        u->y += dy / d * step;
    }
    om_grid_move(om_tac(w), u->unit_id - 1);
    om_unit_set_pos(w, u->unit_id, u->x, u->y);
    return d <= step;
}

static void om_tac_hold(om_world *w, om_unit_row *u, uint32_t target_id) {
    if (u->halted) return;
    om_unit_engage(w, u->unit_id, target_id);
    u->halted = 1;
}

/* Hands a held unit its route back: an attack-move resumes toward its
 * recorded point (a plain om_command_move, since tactical_move.c has no
 * immediate attack-move; unit.c's own `order` still says attack-move), any
 * other order simply clears. */
static void om_tac_release(om_world *w, om_unit_row *u) {
    if (!u->halted) return;
    u->halted = 0;
    if (u->order == OM_ORDER_ATTACK_MOVE) {
        om_command_move(w, &u->unit_id, 1, u->order_x, u->order_y);
        u->issued_x = u->order_x;
        u->issued_y = u->order_y;
    } else {
        om_unit_clear_orders(w, u->unit_id);
    }
}

static void om_tac_fire(om_world *w, om_unit_row *u, om_unit_row *t) {
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

/* Visible to the unit's faction: any living friendly (itself included) can
 * see it through fog.c's om_fog_faction_sees, and it is not stealthed. */
static int om_tac_faction_sees(om_world *w, const om_unit_row *self, const om_unit_row *t) {
    if (t->stealth) return 0;
    return om_fog_faction_sees(w, self->faction_id, t->unit_id);
}

static void om_tac_drop_orders(om_unit_row *u) {
    u->order = OM_ORDER_NONE;
    u->target_id = 0;
    u->anchor_set = 0;
    u->halted = 0;
}

static void om_tac_unit_ai(om_world *w, om_tac_state *st, om_unit_row *u, uint64_t tick) {
    double dest_x = 0.0, dest_y = 0.0, interval_ticks = u->attack_interval * (double)OM_TACTICAL_TICK_RATE;
    int has_dest = om_unit_get_destination(w, u->unit_id, &dest_x, &dest_y);
    int kind = om_unit_get_order_kind(w, u->unit_id);
    int arrived = has_dest && om_tac_dist_le(dest_x - u->x, dest_y - u->y, OM_TIE_EPSILON);
    int noncombat = om_tac_noncombat(u);
    om_unit_row *t;

    if (u->cooldown < interval_ticks) u->cooldown += (double)om_tac_period(st);
    u->suppress_auto = 0;

    /* What tactical_move.c currently believes about this unit's route vs
     * what unit.c last asked for: a route unit.c did not issue is the
     * player's own order and wins (R-087-02). */
    if (has_dest && kind == 1) {
        u->order = OM_ORDER_ATTACK_MOVE;
        u->order_x = dest_x; u->order_y = dest_y;
        u->issued_x = dest_x; u->issued_y = dest_y;
        u->target_id = 0; u->anchor_set = 0; u->halted = 0;
    } else if (u->order != OM_ORDER_NONE) {
        if (!has_dest
            || (kind == 0 && (dest_x != u->issued_x || dest_y != u->issued_y))
            || (kind == 2 && u->order != OM_ORDER_ATTACK_TARGET)) {
            om_tac_drop_orders(u);
        }
    }

    if (u->order != OM_ORDER_NONE) u->suppress_auto = 1;
    if (u->brace_auto && (u->order != OM_ORDER_NONE || (has_dest && !arrived))
        && (u->ability_phase == OM_ABILITY_PHASE_WINDUP || u->ability_phase == OM_ABILITY_PHASE_ACTIVE)) {
        om_ability_start_or_cancel_brace(st, u);
        u->brace_auto = 0;
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
        if (atk && atk->hp > 0.0 && om_tac_hostile(u, atk)
            && u->order == OM_ORDER_NONE && u->target_id == 0) {
            if (noncombat || atk->layer != u->layer || atk->stealth) {
                om_tac_start_flinch(u, atk);
            } else if (om_tac_within(u, atk, u->attack_range)) {
                u->target_id = atk->unit_id;
            } else {
                u->order = OM_ORDER_ATTACK_MOVE;
                u->order_x = atk->x; u->order_y = atk->y;
                u->issued_x = atk->x; u->issued_y = atk->y;
                om_command_move(w, &u->unit_id, 1, atk->x, atk->y);
            }
        }
    }
    if (noncombat) { u->target_id = 0; return; }
    if (u->flinching) { u->suppress_auto = 1; return; }

    if (u->target_id != 0) {
        int drop;
        t = om_registry_find_in(st, u->target_id);
        drop = !t || t->hp <= 0.0 || !om_tac_hostile(u, t);
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
        if (!drop && u->order != OM_ORDER_ATTACK_TARGET) {
            if (t->layer != u->layer || t->stealth || !om_tac_within(u, t, u->attack_range)) {
                drop = 1;
            } else if (u->order == OM_ORDER_ATTACK_MOVE && u->anchor_set
                       && !om_tac_dist_le(t->x - u->anchor_x, t->y - u->anchor_y, OM_ATTACK_MOVE_LEASH_DIST)) {
                drop = 1;
            }
        }
        if (drop) {
            int gone = !t || t->hp <= 0.0;
            u->target_id = 0;
            u->anchor_set = 0;
            if (u->order == OM_ORDER_ATTACK_TARGET && gone) {
                u->order = OM_ORDER_NONE;
                u->halted = 0;
                om_unit_clear_orders(w, u->unit_id);
            }
        }
    }

    if (u->target_id == 0 && u->order != OM_ORDER_ATTACK_TARGET
        && (uint64_t)(u->unit_id % OM_TARGETING_COHORT_COUNT) == tick % OM_TARGETING_COHORT_COUNT) {
        t = om_tac_nearest_hostile(st, u, u->attack_range);
        if (t) {
            u->target_id = t->unit_id;
            if (u->order == OM_ORDER_ATTACK_MOVE) {
                u->anchor_x = u->x; u->anchor_y = u->y; u->anchor_set = 1;
            }
        }
    }

    t = u->target_id != 0 ? om_registry_find_in(st, u->target_id) : NULL;
    if (t) {
        int in_range = om_tac_within(u, t, u->attack_range);
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
        } else if (u->order == OM_ORDER_ATTACK_MOVE) {
            om_tac_hold(w, u, t->unit_id);
        }
        if (in_range && u->cooldown >= interval_ticks - OM_TIE_EPSILON
            && om_combat_can_shoot(w, u->unit_id, t->unit_id)) {
            om_tac_fire(w, u, t);
        }
    } else if (u->order == OM_ORDER_ATTACK_MOVE) {
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

static void om_tactical_ai_tick(om_world *w, om_tac_state *st) {
    uint64_t tick = st->current_tick + 1;
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        om_tac_unit_ai(w, st, u, tick);
    }
    st->validated_tick = tick;
}

/* ---- end S-087 ---- */

uint64_t om_tactical_step(om_world *w) {
    /* No-op until a tactical battle actually exists (tests/csim/test_E11_wiring.py
     * ::test_R_wiring_tactical_step_is_callable): a strategic-only world with no
     * units spawned must not advance the tactical tick counter at all. */
    const om_tac_state *ro = om_tac_ro(w);
    om_tac_state *st;
    if (!ro || ro->n_units == 0) return ro ? ro->current_tick : 0;
    st = om_tac(w);
    om_tac_update_period(st);
    st->base_tick += st->tick_period_ticks;
    om_tac_refresh_positions(w, st);
    om_tactical_ai_tick(w, st);
    om_tactical_apply_aura_regen(w);
    om_tactical_advance_backswing(st);
    om_ability_advance_all(w);
    om_macro_tick(w, st->current_tick);
    om_support_tick(w);
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
    uint32_t i;
    for (i = 0; i < n_units; i++) {
        om_unit_row *u = om_registry_find_in(st, unit_ids[i]);
        if (!u) continue;
        om_tac_drop_orders(u);
        u->flinching = 0;
        u->order = OM_ORDER_ATTACK_MOVE;
        u->order_x = x; u->order_y = y;
        u->issued_x = x; u->issued_y = y;
        om_command_move(w, &u->unit_id, 1, x, y);
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
void om_tactical_reset(om_world *w) {
    om_tac_state *st = om_tac(w);
    om_tac_release_arrays(st);
    memset(st, 0, sizeof(*st));
    st->next_unit_id = 1;
    if (w->move_state && w->move_state_free) {
        w->move_state_free(w->move_state);
        w->move_state = NULL;
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
 * (OM_ROSTER_RAIDER_RANGE), 2 * OM_UNIT_COLLISION_RADIUS between neighbours,
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
    double spacing = 2.0 * (double)OM_UNIT_COLLISION_RADIUS;
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
    if (!om_tac_hostile(a, t) || a->layer != t->layer || !om_tac_within(a, t, a->attack_range)) return;
    if (!om_combat_can_shoot(w, attacker, target)) return;
    om_tac_fire(w, a, t);
}

/* ALG-60: Brace 0.50 (self, while its bonus is granted) + Fortify 0.20
 * (any friendly within OM_FORTIFY_RADIUS of an active Bastion) + Warden
 * aura (om_warden_aura_reduction_for, already diminishing per extra
 * Warden), capped at OM_ABILITY_DAMAGE_REDUCTION_CAP. Brace/Fortify/Warden
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
    uint32_t id;
    int fortify_hit = 0;
    int brace_hit;
    if (!row) return 0.0;
    brace_hit = row->force_brace_reduction
        || (row->unit_type == OM_UT_VANGUARD && row->ability_bonus_on
            && row->ability_phase != OM_ABILITY_PHASE_IDLE);
    if (brace_hit) reduction += OM_ABILITY_BRACE_DAMAGE_REDUCTION;
    if (row->force_fortify_reduction) {
        fortify_hit = 1;
    } else if (st->n_bastions == 0) {
        if (!st->grid.built) om_grid_rebuild(st);
    } else {
        om_grid_iter it;
        om_grid_iter_begin_st(&it, st, row->x, row->y, OM_FORTIFY_RADIUS);
        while ((id = om_grid_iter_next(&it)) != 0) {
            const om_unit_row *cand = &st->units[id - 1];
            if (cand->hp <= 0.0) continue;
            if (cand->unit_type != OM_UT_BASTION) continue;
            if (cand->ability_phase != OM_ABILITY_PHASE_ACTIVE) continue;
            if (cand->faction_id != row->faction_id) continue;
            fortify_hit = 1;
            break;
        }
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
    target->last_attacker = attacker->unit_id;
    /* ALG-60: "after firing the unit's movement pauses ATTACK_BACKSWING_SEC"
     * -- any landed hit through this path (auto-fire, manual command, or a
     * test driving the attack directly) pauses the attacker the same way. */
    attacker->backswing_ticks_remaining = OM_BACKSWING_TICKS;
    attacker->backswing_active = 1;
}

double om_unit_effective_speed(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    double base;
    if (!row) return 0.0;
    if (row->backswing_active) return 0.0;
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
            if (row->ability_phase == OM_ABILITY_PHASE_ACTIVE) return base * OM_ABILITY_FORTIFY_SPEED_MULT;
            break;
        default: break;
    }
    return base;
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
    cap = attacker->base_damage * OM_AOE_DAMAGE_CAP_MULTIPLIER;
    n = om_grid_query_st(st, center->x, center->y, radius, ids, st->n_units);
    for (j = 0; j < n; j++) {
        om_unit_row *cand = &st->units[ids[j] - 1];
        double mult, dmg, remaining;
        if (cand->hp <= 0.0) continue;
        if (cand->faction_id == attacker->faction_id) continue;
        if (cand->layer != attacker->layer) continue;
        if (total >= cap) break;
        mult = om_resolve_hit_multiplier(w, attacker->category, cand);
        dmg = attacker->base_damage * mult * om_unit_output_multiplier(w, attacker_id)
              * (1.0 - om_unit_damage_reduction(w, cand->unit_id));
        remaining = cap - total;
        if (dmg > remaining) dmg = remaining;
        cand->hp -= dmg;
        if (cand->hp < 0.0) cand->hp = 0.0;
        om_grid_sync(st, cand->unit_id - 1);
        cand->last_attacker = attacker_id;
        total += dmg;
    }
    attacker->cooldown = 0.0;
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
    (void)w;
    return unit_id % OM_TARGETING_COHORT_COUNT;
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
/* ---- end generated stubs ---- */
