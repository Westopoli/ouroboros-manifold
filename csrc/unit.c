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

#define OM_MAX_UNITS 4096
#define OM_MAX_CUSTOM_TYPES 64
#define OM_UNIT_TYPE_COUNT 6

#define OM_UT_RAIDER 0
#define OM_UT_INTERCEPTOR 1
#define OM_UT_VANGUARD 2
#define OM_UT_WARDEN 3
#define OM_UT_BOMBARD 4
#define OM_UT_BASTION 5

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

/* S-081's stationary fight loop needs a hard iteration cap so a real bug
 * (e.g. two forces that can never reach each other) fails fast instead of
 * hanging the test process. */
#define OM_TACTICAL_MAX_RUN_TICKS 1000000

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

#define OM_ABILITY_EVENT_BUFFER_CAP 256

#define OM_ABILITY_PHASE_IDLE 0
#define OM_ABILITY_PHASE_WINDUP 1
#define OM_ABILITY_PHASE_ACTIVE 2
#define OM_ABILITY_PHASE_CANCELING 3
#define OM_ABILITY_PHASE_TELEGRAPH 4

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
} om_unit_row;

typedef struct {
    uint32_t        type_id;
    int             in_use;
    om_unit_type_profile profile;
} om_custom_type_row;

typedef struct {
    om_unit_row         units[OM_MAX_UNITS];
    uint32_t            n_units;
    uint32_t            next_unit_id;
    om_custom_type_row  custom_types[OM_MAX_CUSTOM_TYPES];
    uint32_t            n_custom_types;
    /* S-086 ability-event feed: drained on read (om_tick_read_ability_events)
     * -- see the end of the file. */
    om_ability_event    ability_events[OM_ABILITY_EVENT_BUFFER_CAP];
    uint32_t            n_ability_events;
    uint64_t            current_tick;
} om_tac_state;

static void om_tac_state_free(void *p) {
    free(p);
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

static om_unit_row *om_registry_find_in(om_tac_state *st, uint32_t unit_id) {
    uint32_t i;
    if (!st || unit_id == 0) return NULL;
    for (i = 0; i < st->n_units; i++) {
        if (st->units[i].in_use && st->units[i].unit_id == unit_id) {
            return &st->units[i];
        }
    }
    return NULL;
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

static uint32_t om_unit_spawn_internal(om_world *w, int unit_type, int32_t faction_id,
                                        double x, double y, uint32_t layer) {
    const om_unit_type_profile *prof;
    om_unit_row *row;
    om_tac_state *st = om_tac(w);
    if (st->n_units >= OM_MAX_UNITS) return 0;
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
    return row->unit_id;
}

static double om_tactical_dist2(const om_unit_row *a, const om_unit_row *b) {
    double dx = a->x - b->x;
    double dy = a->y - b->y;
    return dx * dx + dy * dy;
}

/* Nearest living enemy, fixed registry (spawn/unit_id) iteration order --
 * S-084's range-gated attack timer (R-084-01) is a later piece (held back
 * as "B10b" per the B10 spec); this increment's stationary S-081 fights
 * resolve on category/HP math alone, so target selection is not cut off
 * by attack_range here. No movement/pathing either way -- that is B12's
 * tactical_move.c. */
static om_unit_row *om_tactical_pick_target(om_tac_state *st, const om_unit_row *attacker) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0;
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        om_unit_row *cand = &st->units[j];
        double d2;
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id == attacker->faction_id) continue;
        d2 = om_tactical_dist2(attacker, cand);
        if (!best || d2 < best_d2) { best = cand; best_d2 = d2; }
    }
    return best;
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
    double dmg = attacker->base_damage * mult;
    target->hp -= dmg;
    if (target->hp < 0.0) target->hp = 0.0;
    attacker->cooldown = attacker->attack_interval * (double)OM_TACTICAL_TICK_RATE;
}

/* One stationary combat tick: alive units off cooldown, with a living
 * enemy (explicit attack-target if still valid, else nearest), deal
 * base_damage x category_multiplier. Fixed spawn-order iteration every
 * tick (determinism contract). */
static void om_tactical_tick_once(om_world *w) {
    om_tac_state *st = om_tac(w);
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        om_unit_row *target = NULL;
        if (!u->in_use || u->hp <= 0.0) continue;
        if (u->cooldown > 0.0) { u->cooldown -= 1.0; continue; }
        if (u->target_id != 0) {
            om_unit_row *explicit_target = om_registry_find_in(st, u->target_id);
            if (explicit_target && explicit_target->hp > 0.0
                && explicit_target->faction_id != u->faction_id) {
                target = explicit_target;
            }
        }
        if (!target) target = om_tactical_pick_target(st, u);
        if (!target) continue;
        om_tactical_apply_hit(w, u, target);
    }
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
static double om_warden_aura_reduction_for(const om_tac_state *st, const om_unit_row *target) {
    uint32_t j;
    int n = 0;
    double undamaged_factor;
    for (j = 0; j < st->n_units; j++) {
        const om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->unit_type != OM_UT_WARDEN) continue;
        if (cand->faction_id != target->faction_id) continue;
        if (om_tactical_dist2(target, cand) <= OM_WARDEN_AURA_RADIUS * OM_WARDEN_AURA_RADIUS) n++;
    }
    if (n <= 0) return 0.0;
    undamaged_factor = 1.0;
    while (n-- > 0) undamaged_factor *= (1.0 - OM_WARDEN_AURA_DAMAGE_REDUCTION);
    return 1.0 - undamaged_factor;
}

/* R-083-03: healing stacks linearly, unlike the damage reduction above. */
static void om_tactical_apply_aura_regen(om_world *w) {
    om_tac_state *st = om_tac(w);
    uint32_t i, j;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        int n_wardens = 0;
        if (!u->in_use || u->hp <= 0.0) continue;
        for (j = 0; j < st->n_units; j++) {
            const om_unit_row *cand = &st->units[j];
            if (!cand->in_use || cand->hp <= 0.0) continue;
            if (cand->unit_type != OM_UT_WARDEN) continue;
            if (cand->faction_id != u->faction_id) continue;
            if (om_tactical_dist2(u, cand) <= OM_WARDEN_AURA_RADIUS * OM_WARDEN_AURA_RADIUS) n_wardens++;
        }
        if (n_wardens > 0) {
            u->hp += OM_WARDEN_AURA_REPAIR_RATE * (double)n_wardens;
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

static int om_tac_dist_le(double dx, double dy, double r) {
    return (dx * dx + dy * dy) <= (r * r);
}

static int om_tac_enemy_within_range(const om_tac_state *st, const om_unit_row *self, double range) {
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        const om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        if (om_tac_dist_le(cand->x - self->x, cand->y - self->y, range)) return 1;
    }
    return 0;
}

static om_unit_row *om_tac_nearest_enemy_within_range(om_tac_state *st, const om_unit_row *self, double range) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0, r2 = range * range;
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        om_unit_row *cand = &st->units[j];
        double dx, dy, d2;
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        dx = cand->x - self->x; dy = cand->y - self->y; d2 = dx * dx + dy * dy;
        if (d2 > r2) continue;
        if (!best || d2 < best_d2) { best = cand; best_d2 = d2; }
    }
    return best;
}

static int om_tac_enemy_category_within(const om_tac_state *st, const om_unit_row *self, int category, double range) {
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        const om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id == self->faction_id) continue;
        if (cand->layer != self->layer) continue;
        if (cand->category != category) continue;
        if (om_tac_dist_le(cand->x - self->x, cand->y - self->y, range)) return 1;
    }
    return 0;
}

static int om_tac_badly_damaged_friendly_within(const om_tac_state *st, const om_unit_row *self, double range) {
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        const om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id != self->faction_id) continue;
        if (cand->hp >= cand->max_hp * OM_ABILITY_RALLY_AUTOTRIGGER_HP_FRACTION) continue;
        if (om_tac_dist_le(cand->x - self->x, cand->y - self->y, range)) return 1;
    }
    return 0;
}

static int om_tac_count_friendlies_within(const om_tac_state *st, const om_unit_row *self, double range) {
    uint32_t j;
    int n = 0;
    for (j = 0; j < st->n_units; j++) {
        const om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand == self) continue;
        if (cand->faction_id != self->faction_id) continue;
        if (om_tac_dist_le(cand->x - self->x, cand->y - self->y, range)) n++;
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
                                   uint32_t duration, uint32_t telegraph_ticks, double radius) {
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
    evt->cue_id = 0;
    evt->radius = radius;
}

static void om_ability_start_surge(om_tac_state *st, om_unit_row *u) {
    u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
    u->ability_ticks_remaining = OM_ABILITY_SURGE_DURATION_TICKS;
    u->ability_bonus_on = 1;
    u->ability_cooldown = 0.0;
    om_ability_emit_event(st, u, u->x, u->y, OM_ABILITY_SURGE_DURATION_TICKS, 0, 0.0);
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
    om_ability_emit_event(st, u, u->x, u->y, OM_ABILITY_BRACE_WINDUP_TICKS, 0, 0.0);
}

static void om_ability_do_rally(om_tac_state *st, om_unit_row *u) {
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id != u->faction_id) continue;
        if (!om_tac_dist_le(cand->x - u->x, cand->y - u->y, OM_ABILITY_RALLY_RADIUS)) continue;
        cand->hp += OM_ABILITY_RALLY_HEAL_AMOUNT;
        if (cand->hp > cand->max_hp) cand->hp = cand->max_hp;
    }
    u->ability_cooldown = OM_ABILITY_RALLY_COOLDOWN_TICKS;
    om_ability_emit_event(st, u, u->x, u->y, 0, 0, OM_ABILITY_RALLY_RADIUS);
}

static void om_ability_start_barrage(om_tac_state *st, om_unit_row *u, double target_x, double target_y) {
    u->ability_phase = OM_ABILITY_PHASE_TELEGRAPH;
    u->ability_ticks_remaining = OM_ABILITY_BARRAGE_TELEGRAPH_TICKS;
    u->ability_target_x = target_x;
    u->ability_target_y = target_y;
    u->ability_cooldown = 0.0;
    om_ability_emit_event(st, u, target_x, target_y, OM_ABILITY_BARRAGE_TELEGRAPH_TICKS,
                          OM_ABILITY_BARRAGE_TELEGRAPH_TICKS, OM_ABILITY_BARRAGE_RADIUS);
}

/* R-086-05/ALG-61: base * 3.0 through the S-081 category multiplier
 * (om_resolve_hit_multiplier, same helper the ordinary attack path uses,
 * including the Bastion siege exception), unit-id order, running total
 * capped at 4 * (base * 3.0). */
static void om_ability_resolve_barrage_damage(om_world *w, om_tac_state *st, om_unit_row *u) {
    double per_hit_base = u->base_damage * OM_ABILITY_BARRAGE_DAMAGE_MULT;
    double cap = per_hit_base * OM_AOE_DAMAGE_CAP_MULTIPLIER;
    double total = 0.0;
    uint32_t j;
    for (j = 0; j < st->n_units; j++) {
        om_unit_row *cand = &st->units[j];
        double mult, dmg, remaining;
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->faction_id == u->faction_id) continue;
        if (cand->layer != u->layer) continue;
        if (!om_tac_dist_le(cand->x - u->ability_target_x, cand->y - u->ability_target_y, OM_ABILITY_BARRAGE_RADIUS)) continue;
        if (total >= cap) break;
        mult = om_resolve_hit_multiplier(w, u->category, cand);
        dmg = per_hit_base * mult;
        remaining = cap - total;
        if (dmg > remaining) dmg = remaining;
        cand->hp -= dmg;
        if (cand->hp < 0.0) cand->hp = 0.0;
        total += dmg;
    }
}

static void om_ability_start_fortify(om_tac_state *st, om_unit_row *u) {
    u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
    u->ability_ticks_remaining = OM_ABILITY_FORTIFY_DURATION_TICKS;
    u->ability_bonus_on = 1;
    u->ability_cooldown = OM_ABILITY_FORTIFY_COOLDOWN_TICKS;
    om_ability_emit_event(st, u, u->x, u->y, OM_ABILITY_FORTIFY_DURATION_TICKS, 0, OM_FORTIFY_RADIUS);
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
        switch (u->unit_type) {
            case OM_UT_INTERCEPTOR:
                if (om_tac_enemy_category_within(st, u, OM_CAT_STRIKE, OM_INTERCEPT_DETECTION_RADIUS)) {
                    u->ability_phase = OM_ABILITY_PHASE_ACTIVE;
                    u->ability_bonus_on = 1;
                    om_ability_emit_event(st, u, u->x, u->y, 0, 0, OM_INTERCEPT_DETECTION_RADIUS);
                }
                break;
            case OM_UT_RAIDER:
                if (om_tac_enemy_within_range(st, u, u->attack_range)) om_ability_start_surge(st, u);
                break;
            case OM_UT_VANGUARD:
                if (om_tac_enemy_within_range(st, u, u->attack_range)) om_ability_start_or_cancel_brace(st, u);
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

static void om_ability_tick_surge(om_unit_row *u) {
    if (u->ability_phase != OM_ABILITY_PHASE_ACTIVE) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining--;
    } else {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
        u->ability_cooldown = OM_ABILITY_SURGE_COOLDOWN_TICKS;
    }
}

static void om_ability_tick_brace(om_unit_row *u) {
    if (u->ability_phase != OM_ABILITY_PHASE_WINDUP && u->ability_phase != OM_ABILITY_PHASE_CANCELING) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining--;
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

static void om_ability_tick_barrage(om_world *w, om_tac_state *st, om_unit_row *u) {
    if (u->ability_phase != OM_ABILITY_PHASE_TELEGRAPH) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining--;
        return;
    }
    om_ability_resolve_barrage_damage(w, st, u);
    u->ability_phase = OM_ABILITY_PHASE_IDLE;
    u->ability_cooldown = OM_ABILITY_BARRAGE_COOLDOWN_TICKS;
}

static void om_ability_tick_fortify(om_unit_row *u) {
    if (u->ability_phase != OM_ABILITY_PHASE_ACTIVE) return;
    if (u->ability_ticks_remaining > 0) {
        u->ability_ticks_remaining--;
    } else {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
    }
}

/* Cooldown decrements once per tactical tick, first, so a value freshly
 * set by this same call's autotrigger/expiry processing (Surge, Barrage,
 * Rally set theirs on completion; Brace/Fortify set theirs at activation)
 * is never decremented before the caller can observe it. */
static void om_ability_advance_all(om_world *w) {
    om_tac_state *st = om_tac(w);
    uint32_t i;
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use) continue;
        if (u->ability_cooldown > 0.0) u->ability_cooldown -= 1.0;
    }
    om_ability_autotrigger_scan(st);
    for (i = 0; i < st->n_units; i++) {
        om_unit_row *u = &st->units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        switch (u->unit_type) {
            case OM_UT_RAIDER:   om_ability_tick_surge(u); break;
            case OM_UT_VANGUARD: om_ability_tick_brace(u); break;
            case OM_UT_BOMBARD:  om_ability_tick_barrage(w, st, u); break;
            case OM_UT_BASTION:  om_ability_tick_fortify(u); break;
            default: break;
        }
    }
    st->current_tick++;
}

/* ---- end B10-3 ability system ---- */

uint64_t om_tactical_step(om_world *w) {
    /* No-op until a tactical battle actually exists (tests/csim/test_E11_wiring.py
     * ::test_R_wiring_tactical_step_is_callable): a strategic-only world with no
     * units spawned must not advance the tactical tick counter at all. */
    om_tac_state *ro = om_tac_ro(w);
    if (!ro || ro->n_units == 0) return ro ? ro->current_tick : 0;
    om_tactical_apply_aura_regen(w);
    om_ability_advance_all(w);
    return om_tac(w)->current_tick;
}

/* ---- generated stubs from signatures.toml ---- */
int om_command_activate_ability(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double target_x, double target_y) {
    om_tac_state *st = om_tac(w);
    uint32_t i;
    om_unit_row *u;
    for (i = 0; i < n_units; i++) {
        u = om_registry_find_in(st, unit_ids[i]);
        if (!u || !om_ability_can_manually_activate(u)) return 1;
    }
    for (i = 0; i < n_units; i++) {
        u = om_registry_find_in(st, unit_ids[i]);
        om_ability_manual_activate(w, st, u, target_x, target_y);
    }
    return 0;
}

int om_command_attack_move(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double x, double y) {
    /* STUB */
    (void)w; (void)unit_ids; (void)n_units; (void)x; (void)y;
    return 0;
}

int om_command_attack_target(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t target_unit) {
    om_tac_state *st = om_tac(w);
    uint32_t i;
    for (i = 0; i < n_units; i++) {
        om_unit_row *u = om_registry_find_in(st, unit_ids[i]);
        if (u) u->target_id = target_unit;
    }
    return 0;
}

uint32_t om_cue_lookup(const char *name) {
    /* STUB */
    (void)name;
    return 0;
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
    /* STUB */
    (void)w;
}

void om_tactical_reset(om_world *w) {
    om_tac_state *st = om_tac(w);
    memset(st, 0, sizeof(*st));
    st->next_unit_id = 1;
}

uint64_t om_tactical_run(om_world *w, uint64_t n_ticks) {
    uint64_t i;
    for (i = 0; i < n_ticks; i++) {
        om_tactical_tick_once(w);
        om_tactical_step(w);
    }
    return n_ticks;
}

uint64_t om_tactical_run_until_eliminated(om_world *w) {
    uint64_t ticks = 0;
    om_tac_state *st = om_tac(w);
    while (ticks < OM_TACTICAL_MAX_RUN_TICKS && om_tactical_multiple_factions_alive(st)) {
        om_tactical_tick_once(w);
        om_tactical_step(w);
        ticks++;
    }
    return ticks;
}

uint64_t om_tactical_run_until_engagement_ends(om_world *w, uint32_t unit_id) {
    om_tac_state *st = om_tac(w);
    uint64_t ticks = 0;
    om_unit_row *u = om_registry_find_in(st, unit_id);
    if (!u) return 0;
    while (ticks < OM_TACTICAL_MAX_RUN_TICKS
           && u->hp > 0.0
           && om_tac_enemy_within_range(st, u, u->attack_range)) {
        om_tactical_tick_once(w);
        om_tactical_step(w);
        ticks++;
    }
    if (u->unit_type == OM_UT_INTERCEPTOR && u->ability_phase == OM_ABILITY_PHASE_ACTIVE) {
        u->ability_phase = OM_ABILITY_PHASE_IDLE;
        u->ability_bonus_on = 0;
        u->ability_cooldown = OM_ABILITY_INTERCEPT_COOLDOWN_TICKS;
    }
    return ticks;
}

void om_tactical_spawn_force_composition(om_world *w, int32_t faction_id, uint32_t count, const char *composition) {
    /* STUB */
    (void)w; (void)faction_id; (void)count; (void)composition;
}

int om_tactical_target_validation_runs_every_tick(om_world *w) {
    /* STUB */
    (void)w;
    return 0;
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
    /* STUB */
    (void)w; (void)tick;
    return 0;
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
    if (stat_field == 0) row->hp += delta;
}

void om_unit_attack(om_world *w, uint32_t attacker, uint32_t target) {
    /* STUB */
    (void)w; (void)attacker; (void)target;
}

/* ALG-60: Brace 0.50 (self, while its bonus is granted) + Fortify 0.20
 * (any friendly within OM_FORTIFY_RADIUS of an active Bastion) + Warden
 * aura (om_warden_aura_reduction_for, already diminishing per extra
 * Warden), capped at OM_ABILITY_DAMAGE_REDUCTION_CAP. */
double om_unit_damage_reduction(om_world *w, uint32_t unit_id) {
    om_tac_state *st = om_tac(w);
    om_unit_row *row = om_registry_find_in(st, unit_id);
    double reduction = 0.0;
    uint32_t j;
    int fortify_hit = 0;
    if (!row) return 0.0;
    if (row->unit_type == OM_UT_VANGUARD && row->ability_bonus_on
        && row->ability_phase != OM_ABILITY_PHASE_IDLE) {
        reduction += OM_ABILITY_BRACE_DAMAGE_REDUCTION;
    }
    for (j = 0; j < st->n_units; j++) {
        const om_unit_row *cand = &st->units[j];
        if (!cand->in_use || cand->hp <= 0.0) continue;
        if (cand->unit_type != OM_UT_BASTION) continue;
        if (cand->ability_phase != OM_ABILITY_PHASE_ACTIVE) continue;
        if (cand->faction_id != row->faction_id) continue;
        if (om_tac_dist_le(cand->x - row->x, cand->y - row->y, OM_FORTIFY_RADIUS)) { fortify_hit = 1; break; }
    }
    if (fortify_hit) reduction += OM_ABILITY_FORTIFY_DAMAGE_REDUCTION;
    reduction += om_warden_aura_reduction_for(st, row);
    if (reduction > OM_ABILITY_DAMAGE_REDUCTION_CAP) reduction = OM_ABILITY_DAMAGE_REDUCTION_CAP;
    return reduction;
}

void om_unit_deal_damage(om_world *w, uint32_t p1, uint32_t p2, double p3) {
    om_tac_state *st = om_tac(w);
    om_unit_row *attacker, *target;
    double mult, dmg, reduction;
    attacker = om_registry_find_in(st, p1);
    target = om_registry_find_in(st, p2);
    if (!attacker || !target) return;
    mult = om_resolve_hit_multiplier(w, attacker->category, target);
    reduction = om_warden_aura_reduction_for(st, target);
    dmg = p3 * mult * (1.0 - reduction);
    target->hp -= dmg;
    if (target->hp < 0.0) target->hp = 0.0;
}

double om_unit_effective_speed(om_world *w, uint32_t unit_id) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    double base;
    if (!row) return 0.0;
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

void om_unit_fire_aoe_attack(om_world *w, uint32_t attacker_id, uint32_t target_id, double radius) {
    /* STUB */
    (void)w; (void)attacker_id; (void)target_id; (void)radius;
}

double om_unit_get_hp(const om_world *w, uint32_t unit) {
    om_unit_row *row = om_registry_find_in(om_tac_ro(w), unit);
    return row ? row->hp : 0.0;
}

uint32_t om_unit_get_target(const om_world *w, uint32_t unit) {
    /* STUB */
    (void)w; (void)unit;
    return 0;
}

double om_unit_hp(om_world *w, uint32_t unit_id) {
    return om_unit_get_hp(w, unit_id);
}

int om_unit_in_backswing(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
}

int om_unit_in_flinch(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
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
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
}

double om_unit_position_y(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
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
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
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
    /* STUB */
    (void)w; (void)unit_type;
    return 0;
}

double om_unit_render_silhouette_size(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

void om_unit_set_ability_cooldown(om_world *w, uint32_t unit_id, double ticks) {
    om_unit_row *row = om_registry_find_in(om_tac(w), unit_id);
    if (row) row->ability_cooldown = ticks;
}

void om_unit_set_brace_active(om_world *w, uint32_t unit_id, int on) {
    /* STUB */
    (void)w; (void)unit_id; (void)on;
}

void om_unit_set_elevation_tier(om_world *w, uint32_t unit_id, int tier) {
    /* STUB */
    (void)w; (void)unit_id; (void)tier;
}

void om_unit_set_fortify_active(om_world *w, uint32_t unit_id, int on) {
    /* STUB */
    (void)w; (void)unit_id; (void)on;
}

void om_unit_set_hp(om_world *w, uint32_t p0, double p1) {
    om_unit_row *row = om_registry_find_in(om_tac(w), p0);
    if (row) row->hp = p1;
}

void om_unit_set_stealth(om_world *w, uint32_t unit_id, int on) {
    /* STUB */
    (void)w; (void)unit_id; (void)on;
}

void om_unit_set_warden_aura_active(om_world *w, uint32_t unit_id, int on) {
    /* STUB */
    (void)w; (void)unit_id; (void)on;
}

uint32_t om_unit_spawn(om_world *w, int unit_type, int32_t faction_id, double x, double y, uint32_t layer) {
    return om_unit_spawn_internal(w, unit_type, faction_id, x, y, layer);
}

uint32_t om_unit_spawn_combat(om_world *w, int32_t p1, double p2, double x) {
    /* STUB */
    (void)w; (void)p1; (void)p2; (void)x;
    return 0;
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
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
}

uint32_t om_unit_targeting_cohort(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
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
/* ---- end generated stubs ---- */
