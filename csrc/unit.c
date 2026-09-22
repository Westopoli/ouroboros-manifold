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
#include <stddef.h>
#include <string.h>

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
    /* STUB */
    (void)w; (void)unit_ids; (void)n_units; (void)target_unit;
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
    /* STUB */
    (void)w; (void)type_id; (void)category; (void)role; (void)max_hp; (void)base_damage; (void)attack_interval; (void)attack_range; (void)speed; (void)sensor_radius; (void)layer_transition_time; (void)aoe_radius; (void)ability_id;
    return 0;
}

double om_tactical_category_multiplier(om_world *w, int attacker_category, int target_category) {
    /* STUB */
    (void)w; (void)attacker_category; (void)target_category;
    return 0.0;
}

void om_tactical_disable_abilities(om_world *w) {
    /* STUB */
    (void)w;
}

void om_tactical_reset(om_world *w) {
    /* STUB */
    (void)w;
}

uint64_t om_tactical_run(om_world *w, uint64_t n_ticks) {
    /* STUB */
    (void)w; (void)n_ticks;
    return 0;
}

uint64_t om_tactical_run_until_eliminated(om_world *w) {
    /* STUB */
    (void)w;
    return 0;
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
    /* STUB */
    (void)w; (void)unit_id;
    return 0;
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
    /* STUB */
    (void)w; (void)p1; (void)p2; (void)p3;
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
    /* STUB */
    (void)w; (void)unit;
    return 0.0;
}

uint32_t om_unit_get_target(const om_world *w, uint32_t unit) {
    /* STUB */
    (void)w; (void)unit;
    return 0;
}

double om_unit_hp(om_world *w, uint32_t unit_id) {
    /* STUB */
    (void)w; (void)unit_id;
    return 0.0;
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
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_attack_interval(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_attack_range(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_base_damage(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

int om_unit_profile_category(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0;
}

double om_unit_profile_dps(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_layer_transition_time(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_max_hp(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_sensor_radius(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
}

double om_unit_profile_speed(om_world *w, int unit_type) {
    /* STUB */
    (void)w; (void)unit_type;
    return 0.0;
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
    /* STUB */
    (void)w; (void)unit_type; (void)faction_id; (void)x; (void)y; (void)layer;
    return 0;
}

uint32_t om_unit_spawn_combat(om_world *w, int32_t p1, double p2, double x) {
    /* STUB */
    (void)w; (void)p1; (void)p2; (void)x;
    return 0;
}

uint32_t om_unit_spawn_for_category(om_world *w, int category, int32_t faction_id, double x, double y, uint32_t layer) {
    /* STUB */
    (void)w; (void)category; (void)faction_id; (void)x; (void)y; (void)layer;
    return 0;
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
