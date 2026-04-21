import config
from outcome_resolver import compute_delta
from impact_preview_templates import build_impact_preview


BAND_PROSE = {
    "total_success":   "A decisive victory — the objective was overwhelmed.",
    "strong_success":  "A hard-fought victory that achieved its aims.",
    "partial_success": "The objective was met, but at significant cost.",
    "partial_failure": "The mission fell short — losses outweighed gains.",
    "total_failure":   "A catastrophic defeat. The position is lost.",
}

COMMANDER_FATE_MAP = {
    True: "survived",
    False: "killed_in_action",
}


def assemble_debrief(mission_result, archetype, region_fields):
    table = config.CONSEQUENCE_TABLES.get(archetype, {})
    band_deltas_spec = table.get(mission_result.outcome_band, [])

    raw_deltas = {"military": 0.0, "tension": 0.0, "economy": 0.0, "population": 0.0}
    for spec in band_deltas_spec:
        field = spec["field"]
        if field not in raw_deltas:
            continue
        current = region_fields.get(field, 50.0)
        delta_val = compute_delta(current, spec["form"], spec["pct"])
        raw_deltas[field] += delta_val

    field_deltas, impact_text = build_impact_preview(raw_deltas)

    final_score = (mission_result.objective_score * config.OUTCOME_WEIGHT_OBJECTIVE +
                   mission_result.force_retention * config.OUTCOME_WEIGHT_RETENTION)

    objectives = []
    for obj in mission_result.per_objective:
        objectives.append({
            "id": obj["id"],
            "type": obj["type"],
            "weight": obj["weight"],
            "completion": obj["completion"],
            "label": obj.get("label", obj["id"]),
        })

    ticks = mission_result.ticks_elapsed
    duration_sec = ticks * config.TACTICAL_TICK_DURATION

    return {
        "outcome_band": mission_result.outcome_band,
        "outcome_band_prose": BAND_PROSE.get(mission_result.outcome_band, ""),
        "final_score": round(final_score, 4),
        "objective_score": round(mission_result.objective_score, 4),
        "force_retention": round(mission_result.force_retention, 4),
        "objectives": objectives,
        "field_deltas": field_deltas,
        "impact_preview": impact_text,
        "commander_fate": COMMANDER_FATE_MAP.get(mission_result.commander_survived, "survived"),
        "mission_duration_ticks": ticks,
        "mission_duration_seconds": round(duration_sec, 1),
    }
