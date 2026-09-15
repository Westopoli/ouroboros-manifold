#include "ouroboros_sim.h"
#include "om_internal.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

double om_sin(double x) {
    const double tau = 6.283185307179586;
    long long k = (long long)(x / tau);
    double r = x - (double)k * tau;
    return r - r*r*r/6.0 + r*r*r*r*r/120.0 - r*r*r*r*r*r*r/5040.0;
}

uint64_t om_world_step(om_world *w) {
    if (!w) return 0;
    w->tick++;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        om_region *r = &w->regions[i];
        if (r->tier == OM_TIER_EMPTY) continue;

        double trend_econ = r->economy - r->prev_econ_osc;
        double trend_tension = r->tension - r->prev_tension_osc;
        double stability = om_region_composite(w, i, OM_C_STABILITY);
        double capacity = om_region_composite(w, i, OM_C_CAPACITY);

        double military_decay = -(r->military) * 0.006 * (1.0 - trend_econ/100.0);
        if (trend_econ >= 100.0) military_decay = 0.0;

        double military_recruit = 0.0;
        if (trend_econ > 20.0 && r->military < 90.0) {
            military_recruit = (0.1 * (r->population/100.0) + 12.0 * (trend_econ/100.0) * (r->population/100.0) * pow(0.8, 0.3)) * (1.0 - r->military/90.0);
        }

        double military_modifier = 0.0;
        if (r->faction_id >= 0 && w->faction_mod[r->faction_id][OM_F_MILITARY] != 0) {
            military_modifier = 0.05 * (90.0 - r->military);
        }

        double economy_growth = 2.0 * (r->population/100.0);
        double economy_drag = 0.2 * (trend_tension/100.0);
        double economy_overcap = 0.0;
        if (trend_econ > capacity) {
            economy_overcap = 15.0 * (trend_econ - capacity)/100.0;
        }

        double economy_adjacency = 0.0;
        for (uint32_t j = 0; j < r->n_neighbors; j++) {
            uint32_t n_idx = r->neighbors[j];
            om_region *n = &w->regions[n_idx];
            if ((n->faction_id == r->faction_id) || 
                (om_faction_stance(w, r->faction_id, n->faction_id) == OM_STANCE_COOPERATIVE)) {
                economy_adjacency += 0.05 * (n->economy/100.0);
            }
        }

        double econ_phase = 6.283185307179586 * (double)w->tick / 15.0 + r->econ_phase;
        double prev_econ_phase = 6.283185307179586 * (double)(w->tick - 1) / 15.0 + r->econ_phase;
        double economy_osc_delta = 6.0 * (om_sin(econ_phase) - om_sin(prev_econ_phase));

        double tension_economic = (trend_econ/100.0) * 0.5 * 0.5;
        double tension_stress = 0.0;
        if (stability < 40.0) {
            tension_stress = (40.0 - stability) * 0.008;
        }

        double tension_subsist = 0.0;
        if (trend_econ < 11.0) {
            tension_subsist = 0.15 * ((11.0 - trend_econ)/3.0) * (r->population/100.0);
        }

        double tension_decay = -0.20 * (trend_tension/100.0);

        double tension_phase = 6.283185307179586 * (double)w->tick / 18.0 + r->tension_phase;
        double prev_tension_phase = 6.283185307179586 * (double)(w->tick - 1) / 18.0 + r->tension_phase;
        double tension_osc_delta = 2.0 * (om_sin(tension_phase) - om_sin(prev_tension_phase));

        double population_base = 0.0;
        if (trend_econ > 15.0 && r->population < 100.0) {
            population_base = 2.0 * ((trend_econ - 15.0)/85.0) * 0.4;
        }

        double population_subsist = 0.0;
        if (trend_econ < 11.0) {
            population_subsist = -0.08 * ((11.0 - trend_econ)/3.0);
        }

        double d_military = military_decay + military_recruit + military_modifier;
        double d_economy = economy_growth - economy_drag - economy_overcap + economy_adjacency + economy_osc_delta;
        double d_tension = tension_economic + tension_stress + tension_subsist + tension_decay + tension_osc_delta;
        double d_population = population_base + population_subsist;

        r->military = fmax(0.0, fmin(100.0, r->military + d_military));
        r->economy = fmax(8.0, fmin(100.0, r->economy + d_economy));
        r->tension = fmax(0.0, fmin(100.0, r->tension + d_tension));
        r->population = fmax(0.0, fmin(100.0, r->population + d_population));

        r->prev_econ_osc = om_sin(econ_phase);
        r->prev_tension_osc = om_sin(tension_phase);

        om_region_composite(w, i, OM_C_STABILITY);
        om_region_composite(w, i, OM_C_CAPACITY);

        r->last_drift.military_decay = military_decay;
        r->last_drift.military_recruit = military_recruit;
        r->last_drift.military_modifier = military_modifier;
        r->last_drift.economy_growth = economy_growth;
        r->last_drift.economy_drag = economy_drag;
        r->last_drift.economy_overcap = economy_overcap;
        r->last_drift.economy_adjacency = economy_adjacency;
        r->last_drift.economy_osc_delta = economy_osc_delta;
        r->last_drift.tension_economic = tension_economic;
        r->last_drift.tension_stress = tension_stress;
        r->last_drift.tension_subsist = tension_subsist;
        r->last_drift.tension_decay = tension_decay;
        r->last_drift.tension_osc_delta = tension_osc_delta;
        r->last_drift.population_base = population_base;
        r->last_drift.population_subsist = population_subsist;
        r->last_drift.d_military = d_military;
        r->last_drift.d_economy = d_economy;
        r->last_drift.d_tension = d_tension;
        r->last_drift.d_population = d_population;

        if (w->trace_on) {
            if (w->trace_len >= w->trace_cap) {
                w->trace_cap *= 2;
                w->trace = realloc(w->trace, sizeof(om_trace_row) * w->trace_cap);
            }
            om_trace_row *row = &w->trace[w->trace_len++];
            row->tick = w->tick;
            row->region_idx = i;
            row->faction_id = r->faction_id;
            row->tier = r->tier;
            row->military = r->military;
            row->economy = r->economy;
            row->tension = r->tension;
            row->population = r->population;
            row->stability = om_region_composite(w, i, OM_C_STABILITY);
            row->capacity = om_region_composite(w, i, OM_C_CAPACITY);
            row->drift = r->last_drift;
            row->checksum = (w->tick % 10 == 0) ? om_world_checksum(w) : 0;
        }
    }

    return w->tick;
}

uint64_t om_world_run(om_world *w, uint64_t n_ticks) {
    for (uint64_t i = 0; i < n_ticks; i++) {
        om_world_step(w);
    }
    return w->tick;
}

int om_region_drift(const om_world *w, uint32_t idx, om_drift_row *out) {
    if (!w || idx >= w->n_regions || !out) return -1;
    om_region *r = &w->regions[idx];
    if (r->tier == OM_TIER_EMPTY) return -1;

    *out = r->last_drift;
    return 0;
}

uint64_t om_world_checksum(const om_world *w) {
    if (!w) return 0;
    uint64_t checksum = 0;
    for (uint32_t i = 0; i < w->n_regions; i++) {
        om_region *r = &w->regions[i];
        if (r->tier == OM_TIER_EMPTY) continue;
        checksum ^= (uint64_t)(r->military * 1000) << 0;
        checksum ^= (uint64_t)(r->economy * 1000) << 8;
        checksum ^= (uint64_t)(r->tension * 1000) << 16;
        checksum ^= (uint64_t)(r->population * 1000) << 24;
        checksum ^= (uint64_t)r->faction_id << 32;
        checksum ^= (uint64_t)r->tier << 40;
    }
    return checksum;
}

void om_trace_enable(om_world *w, int on) {
    if (!w) return;
    w->trace_on = on;
}

uint64_t om_trace_len(const om_world *w) {
    if (!w) return 0;
    return w->trace_len;
}

uint64_t om_trace_read(const om_world *w, uint64_t start, uint64_t count, om_trace_row *out) {
    if (!w || !out || start >= w->trace_len) return 0;
    uint64_t read_count = fmin(count, w->trace_len - start);
    memcpy(out, &w->trace[start], sizeof(om_trace_row) * read_count);
    return read_count;
}

#ifdef OM_DEBUG_INJECT
void om_debug_inject(om_world *w, om_bug bug) {
    if (!w) return;
    w->inject = bug;
}
#endif
