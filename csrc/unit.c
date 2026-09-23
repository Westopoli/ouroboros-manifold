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
#include <string.h>

/* ---- B10-1: E-11 roster table, category multiplier, stationary combat ----
 * All unit/tactical state is private to this file (om_world/om_internal.h
 * carry none -- see the PRIVATE LAYOUT block above and the B10 spec's
 * architecture decision). A single static registry tracks one "current"
 * om_world*; every entry point rebinds (clears) it when the caller's world
 * pointer differs from the bound owner, which is also the defense against
 * a freed om_world's malloc address being reused by a later world_factory
 * world in the same test session. */

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
} om_unit_row;

typedef struct {
    uint32_t        type_id;
    int             in_use;
    om_unit_type_profile profile;
} om_custom_type_row;

static struct {
    const om_world     *owner;
    om_unit_row         units[OM_MAX_UNITS];
    uint32_t            n_units;
    uint32_t            next_unit_id;
    om_custom_type_row  custom_types[OM_MAX_CUSTOM_TYPES];
    uint32_t            n_custom_types;
    /* Set once om_tactical_run/run_until_eliminated has ticked this bound
     * world's battle at least once since the last (re)bind. A world_factory
     * test world is freed at test teardown and the next om_world_new can be
     * handed the exact same malloc address (glibc tcache reuse for a fixed
     * struct size in a tight alloc/free loop is not a corner case here --
     * it reproduces every run), so "owner == w" alone cannot tell a still-
     * live world apart from a new one wearing a dead one's address. A test
     * that spawns units for a fresh scenario always does so before ever
     * ticking combat; one that spawns MORE units into a battle already
     * ticked is, in every fenced B10-1 case, doing so only right after an
     * explicit om_tactical_reset (which clears this flag). So an
     * om_unit_spawn* call that finds this flag still set is never a
     * legitimate mid-battle reinforcement in this increment's scope -- it
     * is either the same stale world's registry (harmless to clear, the
     * battle already resolved) or a same-address-new-world collision
     * (must be cleared). See leaf-01-Q1.md for the header-level fix this
     * stands in for (a generation counter on om_world) that a future
     * increment needing real mid-battle reinforcement will need instead. */
    int                 battle_ticked;
} g_unit_registry;

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

/* registry.owner != w: a new om_world (possibly a freed one's reused malloc
 * address) -- clear every row and rebind rather than trust stale state. */
static void om_registry_bind(const om_world *w) {
    if (g_unit_registry.owner != w) {
        memset(&g_unit_registry, 0, sizeof(g_unit_registry));
        g_unit_registry.owner = w;
        g_unit_registry.next_unit_id = 1;
    }
}

/* See the battle_ticked comment on the registry struct: a spawn that lands
 * after this bound registry's battle has already been ticked at least once
 * is always the start of a new scenario in this increment's scope, whether
 * "w" is the same still-live world reused for a second fight or a brand
 * new world that happens to share a freed one's address. Clear units and
 * custom types alike, exactly like an explicit om_tactical_reset, and keep
 * the same owner/id-counter reset semantics. */
static void om_registry_start_new_battle_if_stale(const om_world *w) {
    if (g_unit_registry.battle_ticked) {
        memset(&g_unit_registry, 0, sizeof(g_unit_registry));
        g_unit_registry.owner = w;
        g_unit_registry.next_unit_id = 1;
    }
}

static om_unit_row *om_registry_find(uint32_t unit_id) {
    uint32_t i;
    if (unit_id == 0) return NULL;
    for (i = 0; i < g_unit_registry.n_units; i++) {
        if (g_unit_registry.units[i].in_use && g_unit_registry.units[i].unit_id == unit_id) {
            return &g_unit_registry.units[i];
        }
    }
    return NULL;
}

static const om_unit_type_profile *om_get_builtin_profile(int unit_type) {
    if (unit_type < 0 || unit_type >= OM_UNIT_TYPE_COUNT) return NULL;
    return &OM_BUILTIN_PROFILES[unit_type];
}

/* Builtin roster entries are compile-time constants (no per-world state);
 * only a custom registration needs the owner-bound registry. */
static const om_unit_type_profile *om_get_profile(const om_world *w, int unit_type) {
    const om_unit_type_profile *builtin = om_get_builtin_profile(unit_type);
    uint32_t i;
    if (builtin) return builtin;
    om_registry_bind(w);
    for (i = 0; i < g_unit_registry.n_custom_types; i++) {
        if (g_unit_registry.custom_types[i].in_use
            && g_unit_registry.custom_types[i].type_id == (uint32_t)unit_type) {
            return &g_unit_registry.custom_types[i].profile;
        }
    }
    return NULL;
}

static uint32_t om_unit_spawn_internal(om_world *w, int unit_type, int32_t faction_id,
                                        double x, double y, uint32_t layer) {
    const om_unit_type_profile *prof;
    om_unit_row *row;
    om_registry_bind(w);
    om_registry_start_new_battle_if_stale(w);
    if (g_unit_registry.n_units >= OM_MAX_UNITS) return 0;
    prof = om_get_profile(w, unit_type);
    row = &g_unit_registry.units[g_unit_registry.n_units++];
    memset(row, 0, sizeof(*row));
    row->unit_id = g_unit_registry.next_unit_id++;
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
static om_unit_row *om_tactical_pick_target(const om_unit_row *attacker) {
    om_unit_row *best = NULL;
    double best_d2 = 0.0;
    uint32_t j;
    for (j = 0; j < g_unit_registry.n_units; j++) {
        om_unit_row *cand = &g_unit_registry.units[j];
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
    uint32_t i;
    for (i = 0; i < g_unit_registry.n_units; i++) {
        om_unit_row *u = &g_unit_registry.units[i];
        om_unit_row *target = NULL;
        if (!u->in_use || u->hp <= 0.0) continue;
        if (u->cooldown > 0.0) { u->cooldown -= 1.0; continue; }
        if (u->target_id != 0) {
            om_unit_row *explicit_target = om_registry_find(u->target_id);
            if (explicit_target && explicit_target->hp > 0.0
                && explicit_target->faction_id != u->faction_id) {
                target = explicit_target;
            }
        }
        if (!target) target = om_tactical_pick_target(u);
        if (!target) continue;
        om_tactical_apply_hit(w, u, target);
    }
}

static int om_tactical_multiple_factions_alive(void) {
    int32_t first_faction = 0;
    int have_first = 0;
    uint32_t i;
    for (i = 0; i < g_unit_registry.n_units; i++) {
        om_unit_row *u = &g_unit_registry.units[i];
        if (!u->in_use || u->hp <= 0.0) continue;
        if (!have_first) { first_faction = u->faction_id; have_first = 1; continue; }
        if (u->faction_id != first_faction) return 1;
    }
    return 0;
}

/* ---- end B10-1 registry ---- */

uint64_t om_tactical_step(om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

/* ---- generated stubs from signatures.toml ---- */
int om_command_activate_ability(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double target_x, double target_y) {
    /* STUB */
    (void)w; (void)unit_ids; (void)n_units; (void)target_x; (void)target_y;
    return 0;
}

int om_command_attack_move(om_world *w, const uint32_t *unit_ids, uint32_t n_units, double x, double y) {
    /* STUB */
    (void)w; (void)unit_ids; (void)n_units; (void)x; (void)y;
    return 0;
}

int om_command_attack_target(om_world *w, const uint32_t *unit_ids, uint32_t n_units, uint32_t target_unit) {
    uint32_t i;
    om_registry_bind(w);
    for (i = 0; i < n_units; i++) {
        om_unit_row *u = om_registry_find(unit_ids[i]);
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
    om_custom_type_row *row;
    uint32_t i;
    (void)role; (void)ability_id;
    om_registry_bind(w);
    if (om_get_builtin_profile((int)type_id) != NULL) return -1;
    row = NULL;
    for (i = 0; i < g_unit_registry.n_custom_types; i++) {
        if (g_unit_registry.custom_types[i].in_use && g_unit_registry.custom_types[i].type_id == type_id) {
            row = &g_unit_registry.custom_types[i];
            break;
        }
    }
    if (!row) {
        if (g_unit_registry.n_custom_types >= OM_MAX_CUSTOM_TYPES) return -1;
        row = &g_unit_registry.custom_types[g_unit_registry.n_custom_types++];
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
    memset(&g_unit_registry, 0, sizeof(g_unit_registry));
    g_unit_registry.owner = w;
    g_unit_registry.next_unit_id = 1;
}

uint64_t om_tactical_run(om_world *w, uint64_t n_ticks) {
    uint64_t i;
    om_registry_bind(w);
    g_unit_registry.battle_ticked = 1;
    for (i = 0; i < n_ticks; i++) {
        om_tactical_tick_once(w);
    }
    return n_ticks;
}

uint64_t om_tactical_run_until_eliminated(om_world *w) {
    uint64_t ticks = 0;
    om_registry_bind(w);
    g_unit_registry.battle_ticked = 1;
    while (ticks < OM_TACTICAL_MAX_RUN_TICKS && om_tactical_multiple_factions_alive()) {
        om_tactical_tick_once(w);
        ticks++;
    }
    return ticks;
}

uint64_t om_tactical_run_until_engagement_ends(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
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
    /* STUB */
    (void)w; (void)x; (void)y;
    return 0;
}

uint64_t om_tactical_tick(om_world *w) {
    /* STUB */
    (void)w;
    return 0;
}

uint64_t om_tactical_tick_to(om_world *w, uint64_t tick) {
    /* STUB */
    (void)w; (void)tick;
    return 0;
}

int om_tactical_zone_visible_to_enemy(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
}

int om_unit_ability_active(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
}

double om_unit_ability_cooldown(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
}

int om_unit_alive(om_world *w, uint32_t unit_id) {
    om_unit_row *row;
    om_registry_bind(w);
    row = om_registry_find(unit_id);
    return (row && row->hp > 0.0) ? 1 : 0;
}

void om_unit_apply_trait_modifier(om_world *w, uint32_t unit_id, int stat_field, double delta) {
    /* STUB */
    (void)w; (void)unit_id; (void)stat_field; (void)delta;
}

void om_unit_attack(om_world *w, uint32_t attacker, uint32_t target) {
    /* STUB */
    (void)w; (void)attacker; (void)target;
}

double om_unit_damage_reduction(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
}

void om_unit_deal_damage(om_world *w, uint32_t p1, uint32_t p2, double p3) {
    om_unit_row *attacker, *target;
    double mult, dmg;
    om_registry_bind(w);
    attacker = om_registry_find(p1);
    target = om_registry_find(p2);
    if (!attacker || !target) return;
    mult = om_resolve_hit_multiplier(w, attacker->category, target);
    dmg = p3 * mult;
    target->hp -= dmg;
    if (target->hp < 0.0) target->hp = 0.0;
}

double om_unit_effective_speed(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
}

void om_unit_fire_aoe_attack(om_world *w, uint32_t attacker_id, uint32_t target_id, double radius) {
    /* STUB */
    (void)w; (void)attacker_id; (void)target_id; (void)radius;
}

double om_unit_get_hp(const om_world *w, uint32_t unit) {
    om_unit_row *row;
    om_registry_bind(w);
    row = om_registry_find(unit);
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
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
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
    /* STUB */
    (void)w; (void)unit_type;
    return 0;
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
    /* STUB */
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
    /* STUB */
    (void)w; (void)unit_id; (void)ticks;
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
    /* STUB */
    (void)w; (void)p0; (void)p1;
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
    /* STUB */
    (void)w; (void)out; (void)max;
    return 0;
}
/* ---- end generated stubs ---- */
