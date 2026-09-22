#include "ouroboros_sim.h"
#include "om_internal.h"
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

void om_world_set_feature(om_world *w, om_feature f, int on) {
    if (w == NULL || (unsigned)f >= 9)
        return;
    w->features[f] = on != 0;
}

int om_world_feature(const om_world *w, om_feature f) {
    if (w == NULL || (unsigned)f >= 9)
        return 0;
    return w->features[f];
}

void om_region_set_edge(om_world *w, uint32_t a, uint32_t b, om_edge_type t) {
    if (w == NULL || a >= 64 || b >= 64)
        return;
    w->region_edge[a][b] = t;
    w->region_edge[b][a] = t;
}

int om_region_edge(const om_world *w, uint32_t a, uint32_t b, om_edge_type *out) {
    if (w == NULL || a >= 64 || b >= 64)
        return 0;
    if ((int)w->region_edge[a][b] < 0)
        return 0;
    if (out != NULL)
        *out = w->region_edge[a][b];
    return 1;
}

int om_faction_set(om_world *w, int32_t faction_id, om_archetype archetype, double budget, double tech, double attack_confidence) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return -1;
    
    w->faction_archetype[faction_id] = archetype;
    w->faction_budget[faction_id] = budget;
    w->faction_tech[faction_id] = tech;
    
    if (w->faction_used[faction_id] == 0) {
        w->faction_used[faction_id] = 1;
        w->faction_n++;
    }
    
    if (attack_confidence < 0) {
        double lo, hi;
        switch (archetype) {
            case OM_ARCH_CONQUEROR:     lo = 2.0; hi = 6.0; break;
            case OM_ARCH_FORTIFIER:     lo = 4.0; hi = 10.0; break;
            case OM_ARCH_PLAYER:        lo = 3.0; hi = 8.0; break;
            case OM_ARCH_BREAKAWAY:     lo = 2.0; hi = 5.0; break;
            default:                    lo = 4.0; hi = 8.0; break;
        }
        
        double u = om_rng_draw(w);
        w->faction_confidence[faction_id] = lo + (hi - lo) * u;
    } else {
        w->faction_confidence[faction_id] = attack_confidence;
    }
    
    for (int j = 0; j < OM_MAX_FACTIONS; j++) {
        if (j == faction_id)
            w->faction_stance[faction_id][j] = OM_STANCE_COOPERATIVE;
        else
            w->faction_stance[faction_id][j] = OM_STANCE_HOSTILE;
    }
    
    return 0;
}

void om_faction_set_stance(om_world *w, int32_t from, int32_t toward, om_stance s) {
    if (w == NULL || from < 0 || from >= OM_MAX_FACTIONS || toward < 0 || toward >= OM_MAX_FACTIONS)
        return;
    
    w->faction_stance[from][toward] = s;
}

void om_faction_set_tech_multipliers(om_world *w, int32_t faction_id, double attack, double defense, double economy) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return;
    
    w->faction_tech_attack[faction_id] = attack;
    w->faction_tech_defense[faction_id] = defense;
    w->faction_tech_economy[faction_id] = economy;
}

uint32_t om_faction_count(const om_world *w) {
    if (w == NULL)
        return 0;
    
    return w->faction_n;
}

om_archetype om_faction_archetype(const om_world *w, int32_t faction_id) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return OM_ARCH_DEFAULT;
    
    return w->faction_archetype[faction_id];
}

double om_faction_budget(const om_world *w, int32_t faction_id) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return 0.0;
    
    return w->faction_budget[faction_id];
}

double om_faction_confidence(const om_world *w, int32_t faction_id) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return 0.0;
    
    return w->faction_confidence[faction_id];
}

double om_faction_tech(const om_world *w, int32_t faction_id) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return 0.0;
    
    return w->faction_tech[faction_id];
}

om_stance om_faction_stance(const om_world *w, int32_t from, int32_t toward) {
    if (w == NULL || from < 0 || from >= OM_MAX_FACTIONS || toward < 0 || toward >= OM_MAX_FACTIONS)
        return OM_STANCE_HOSTILE;
    
    return w->faction_stance[from][toward];
}

uint32_t om_faction_territory(const om_world *w, int32_t faction_id) {
    if (w == NULL || faction_id < 0 || faction_id >= OM_MAX_FACTIONS)
        return 0;
    
    uint32_t count = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        if (w->regions[i].faction_id == faction_id)
            count++;
    }
    return count;
}

void om_region_set_owner(om_world *w, uint32_t idx, int32_t faction_id, int64_t held_since_tick) {
    if (w == NULL || idx >= w->n_regions)
        return;
    
    w->regions[idx].faction_id = faction_id;
    
    if (w->region_held_since == NULL) {
        w->region_held_since = calloc(w->n_regions, sizeof(int64_t));
    }
    
    w->region_held_since[idx] = held_since_tick;
}

int32_t om_region_owner(const om_world *w, uint32_t idx) {
    if (w == NULL || idx >= w->n_regions)
        return -1;
    
    return w->regions[idx].faction_id;
}

int64_t om_region_held_since(const om_world *w, uint32_t idx) {
    if (w == NULL || idx >= w->n_regions || w->region_held_since == NULL)
        return 0;
    
    return w->region_held_since[idx];
}

void om_rng_force(om_world *w, const double *draws, uint32_t n) {
    if (w == NULL || draws == NULL)
        return;

    for (uint32_t i = 0; i < n; i++) {
        w->rng_forced[(w->rng_forced_head + w->rng_forced_len + i) % 4096] = draws[i];
    }
    w->rng_forced_len += n;
}

uint32_t om_rng_forced_remaining(const om_world *w) {
    if (w == NULL)
        return 0;
    
    return w->rng_forced_len;
}

void om_faction_step_budget(om_world *w) {
    if (!w) return;
    for (int32_t f = 0; f < OM_MAX_FACTIONS; f++) {
        if (w->faction_used[f] == 0) continue;
        double delta = 0.0;
        for (uint32_t i = 0; i < w->n_regions; i++) {
            if (w->regions[i].faction_id == (int32_t)f) {
                delta += (w->regions[i].economy - 8.0) * 0.025;
            }
        }
        delta *= w->faction_tech_economy[f];
        w->faction_budget[f] += delta;
        if (w->faction_budget[f] < 0.0) {
            w->faction_budget[f] = 0.0;
        }
    }
}
