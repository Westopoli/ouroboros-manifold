import math
import config
from region import Region


def _osc_term(amplitude: float, period: int, phase: float, tick: int) -> float:
    return amplitude * math.sin(2.0 * math.pi * tick / period + phase)


def military_drift(fields: dict) -> float:
    maintenance_cost = fields["military"] * config.MILITARY_DECAY_RATE
    affordable = fields["economy"] / 100.0
    return -maintenance_cost * (1.0 - affordable)



def tension_drift(fields: dict, composites: dict) -> float:
    # Economic tension: low economy breeds unrest, high economy calms it
    eco_deviation = (config.TENSION_ECONOMY_MIDPOINT - fields["economy"]) / 100.0
    economic_tension = eco_deviation * config.TENSION_ECONOMY_RATE * (fields["population"] / 100.0)

    stress_pressure = (
        max(0.0, config.TENSION_STRESS_THRESHOLD - composites["stability"])
        * config.TENSION_STRESS_RATE
    )
    natural_decay = config.TENSION_NATURAL_DECAY_RATE * (fields["tension"] / 100.0)

    # Subsistence crisis: economy near floor creates compounding pressure
    subsistence_pressure = 0.0
    subsistence_thresh = config.ECONOMY_FLOOR + config.SUBSISTENCE_CRISIS_RANGE
    if fields["economy"] < subsistence_thresh:
        severity = (subsistence_thresh - fields["economy"]) / config.SUBSISTENCE_CRISIS_RANGE
        subsistence_pressure = config.SUBSISTENCE_TENSION_RATE * severity * (fields["population"] / 100.0)

    return economic_tension + stress_pressure + subsistence_pressure - natural_decay


def population_drift(fields: dict) -> float:
    if fields["economy"] > config.POPULATION_SUBSISTENCE:
        base = config.POPULATION_GROWTH_RATE * (
            (fields["economy"] - config.POPULATION_SUBSISTENCE) / (100.0 - config.POPULATION_SUBSISTENCE)
        ) * (1.0 - fields["population"] / 100.0)
    else:
        deficit = config.POPULATION_SUBSISTENCE - fields["economy"]
        base = -deficit * config.POPULATION_DECLINE_RATE

    # Subsistence crisis: economy near floor accelerates population loss
    subsistence_thresh = config.ECONOMY_FLOOR + config.SUBSISTENCE_CRISIS_RANGE
    if fields["economy"] < subsistence_thresh:
        severity = (subsistence_thresh - fields["economy"]) / config.SUBSISTENCE_CRISIS_RANGE
        base -= config.SUBSISTENCE_POP_RATE * severity

    return base


def _deoscillated_stability(fields: dict) -> float:
    m = fields["military"]
    t = fields["tension"]
    p = fields["population"]
    stability = (
        m * config.W_STAB_MILITARY
        + (100.0 - t) * config.W_STAB_TENSION
        + p * config.W_STAB_POPULATION
    )
    if m < config.STAB_MILITARY_THRESHOLD:
        stability *= config.STAB_MILITARY_PENALTY
    if p < config.STAB_POPULATION_THRESHOLD:
        stability *= config.STAB_POPULATION_PENALTY
    return stability


def compute_drift_deltas(region: Region, tick: int = 0,
                         faction_modifier: dict | None = None,
                         adjacency_bonus: float = 0.0) -> dict:
    if region.tier == "empty":
        return {}
    f = region.fields
    c = region.composites

    # ── Oscillation: feedback-isolated additive ──────────────────────────────
    # The stored field = trend + prev_osc. Cross-field coupling reads de-oscillated
    # values (the trend). The field's own drift gets osc(t) - osc(t-1) added.
    if config.ENABLE_OSCILLATION and tick > 0:
        econ_osc = _osc_term(config.ECON_OSCILLATION_AMPLITUDE,
                             config.ECON_OSCILLATION_PERIOD,
                             region.econ_phase_offset, tick)
        prev_econ_osc = _osc_term(config.ECON_OSCILLATION_AMPLITUDE,
                                  config.ECON_OSCILLATION_PERIOD,
                                  region.econ_phase_offset, tick - 1) if tick > 1 else 0.0
        tension_osc = _osc_term(config.TENSION_OSCILLATION_AMPLITUDE,
                                config.TENSION_OSCILLATION_PERIOD,
                                region.tension_phase_offset, tick)
        prev_tension_osc = _osc_term(config.TENSION_OSCILLATION_AMPLITUDE,
                                     config.TENSION_OSCILLATION_PERIOD,
                                     region.tension_phase_offset, tick - 1) if tick > 1 else 0.0

        # De-oscillated field values for cross-field coupling
        eco_trend = f["economy"] - prev_econ_osc
        ten_trend = f["tension"] - prev_tension_osc
        f_deosc = {**f, "economy": eco_trend, "tension": ten_trend}
        c_deosc = {"stability": _deoscillated_stability(f_deosc)}

        econ_osc_delta = econ_osc - prev_econ_osc
        tension_osc_delta = tension_osc - prev_tension_osc
    else:
        f_deosc = f
        c_deosc = c
        econ_osc_delta = 0.0
        tension_osc_delta = 0.0

    # Cross-field reads use de-oscillated values; own-field oscillation added as delta
    eco_base_growth   = config.ECONOMY_BASE_GROWTH * (f_deosc["population"] / 100.0)
    eco_tension_drag  = (f_deosc["tension"] / 100.0) * config.ECONOMY_TENSION_PENALTY_RATE
    eco_capacity      = f_deosc["population"] * config.ECO_POP_RATIO
    eco_overcap_decay = (
        config.ECO_OVERCAPACITY_DECAY * (f_deosc["economy"] - eco_capacity) / 100.0
        if f_deosc["economy"] > eco_capacity else 0.0
    )
    eco_drift_net = eco_base_growth - eco_tension_drag - eco_overcap_decay

    if config.DIAGNOSTIC_PRINTS and tick > 0 and tick % 25 == 0:
        ten_drift = tension_drift(f_deosc, c_deosc)
        pop_drift = population_drift(f_deosc)
        print(
            f"  [DRIFT t={tick:>3}] {region.id}"
            f"  eco={f_deosc['economy']:.1f}  pop={f_deosc['population']:.1f}"
            f"  ten={f_deosc['tension']:.1f}  mil={f_deosc['military']:.1f}"
            f"  | eco_drift: growth={eco_base_growth:+.3f}"
            f" t_drag={-eco_tension_drag:+.3f}"
            f" overcap={-eco_overcap_decay:+.3f}"
            f" osc={econ_osc_delta:+.3f}"
            f" adj={adjacency_bonus:+.3f}"
            f" net={eco_drift_net + adjacency_bonus + econ_osc_delta:+.3f}"
            f"  | ten_drift={ten_drift:+.4f}"
            f"  | pop_drift={pop_drift:+.4f}"
        )

    deltas = {
        "military":   military_drift(f_deosc),
        "economy":    eco_drift_net + adjacency_bonus + econ_osc_delta,
        "tension":    tension_drift(f_deosc, c_deosc) + tension_osc_delta,
        "population": population_drift(f_deosc),
    }

    if faction_modifier:
        for field, bonus in faction_modifier.items():
            if field in deltas:
                if field == "military" and config.ENABLE_RECRUITMENT:
                    # Gate military modifier by recruitment headroom so it respects the ceiling
                    mil_headroom = max(0.0, 1.0 - f["military"] / config.RECRUITMENT_CEILING)
                    deltas[field] += bonus * mil_headroom
                else:
                    deltas[field] += bonus

    # Recruitment reads de-oscillated economy
    if config.ENABLE_RECRUITMENT:
        eco_for_recruit = f_deosc["economy"]
        headroom = max(0.0, 1.0 - f["military"] / config.RECRUITMENT_CEILING)
        pop_factor = f_deosc["population"] / 100.0
        eco_recruitment = (
            config.RECRUITMENT_RATE
            * (eco_for_recruit / 100.0)
            * pop_factor
            * (1.0 - f["tension"] / 100.0)
        ) if eco_for_recruit > config.RECRUITMENT_THRESHOLD else 0.0
        recruitment = (config.RECRUITMENT_BASELINE * pop_factor + eco_recruitment) * headroom
        deltas["military"] += recruitment

    return deltas


def apply_drift_deltas(region: Region, deltas: dict) -> None:
    if not deltas:
        return
    for field, delta in deltas.items():
        floor = config.ECONOMY_FLOOR if field == "economy" else 0.0
        region.fields[field] = max(floor, min(100.0, region.fields[field] + delta))
    region.recompute_composites()


