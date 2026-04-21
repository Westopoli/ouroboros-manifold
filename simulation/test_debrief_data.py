import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mission_contracts import MissionResult
from debrief_data import assemble_debrief

ARCHETYPES = ["defensive_stand", "assault", "evacuation"]
BANDS = ["total_failure", "partial_failure", "partial_success", "strong_success", "total_success"]

REGION_FIELDS = {"military": 50.0, "tension": 60.0, "economy": 45.0, "population": 70.0}

SCORE_MAP = {
    "total_failure": 0.10,
    "partial_failure": 0.30,
    "partial_success": 0.50,
    "strong_success": 0.70,
    "total_success": 0.90,
}

RETENTION_MAP = {
    "total_failure": 0.20,
    "partial_failure": 0.45,
    "partial_success": 0.60,
    "strong_success": 0.75,
    "total_success": 0.90,
}


def _make_result(band, archetype):
    return MissionResult(
        mission_id=f"test_{archetype}_{band}",
        outcome_band=band,
        objective_score=SCORE_MAP[band],
        force_retention=RETENTION_MAP[band],
        per_objective=[
            {"id": "obj_primary", "type": "hold_zone", "weight": 0.6,
             "completion": SCORE_MAP[band], "is_primary": True, "failed": False,
             "label": "Hold the northern approach"},
            {"id": "obj_secondary", "type": "eliminate_force", "weight": 0.4,
             "completion": SCORE_MAP[band] * 0.8, "is_primary": False, "failed": False,
             "label": "Destroy the assault force"},
        ],
        commander_survived=(band != "total_failure"),
        ticks_elapsed=36000,
    )


def test_all_combinations():
    passed = 0
    failed = 0

    for archetype in ARCHETYPES:
        for band in BANDS:
            result = _make_result(band, archetype)
            region = dict(REGION_FIELDS)
            payload = assemble_debrief(result, archetype, region)

            errors = []

            if payload["outcome_band"] != band:
                errors.append(f"outcome_band: expected {band}, got {payload['outcome_band']}")

            if not payload["outcome_band_prose"]:
                errors.append("outcome_band_prose is empty")

            if not isinstance(payload["final_score"], float):
                errors.append(f"final_score not float: {type(payload['final_score'])}")

            if not isinstance(payload["objectives"], list) or len(payload["objectives"]) != 2:
                errors.append(f"objectives count: expected 2, got {len(payload.get('objectives', []))}")

            for field_name in ("military", "tension", "economy", "population"):
                fd = payload["field_deltas"].get(field_name)
                if fd is None:
                    errors.append(f"missing field_delta for {field_name}")
                    continue
                for key in ("raw", "direction", "magnitude", "prose"):
                    if key not in fd:
                        errors.append(f"field_delta[{field_name}] missing key {key}")

            preview = payload["impact_preview"]
            if not isinstance(preview, str) or len(preview) == 0:
                errors.append("impact_preview is empty or not a string")

            sentence_count = preview.count(". ") + (1 if preview.endswith(".") else 0)
            if "." in preview:
                sentences = [s.strip() for s in preview.split(".") if s.strip()]
                sentence_count = len(sentences)
            if sentence_count > 3:
                errors.append(f"impact_preview has {sentence_count} sentences (max 3)")

            if band == "total_failure" and payload["commander_fate"] != "killed_in_action":
                errors.append(f"commander_fate: expected killed_in_action, got {payload['commander_fate']}")
            elif band != "total_failure" and payload["commander_fate"] != "survived":
                errors.append(f"commander_fate: expected survived, got {payload['commander_fate']}")

            if payload["mission_duration_ticks"] != 36000:
                errors.append(f"mission_duration_ticks: expected 36000, got {payload['mission_duration_ticks']}")

            expected_sec = 36000 * 0.05
            if abs(payload["mission_duration_seconds"] - expected_sec) > 0.1:
                errors.append(f"mission_duration_seconds: expected {expected_sec}, got {payload['mission_duration_seconds']}")

            if errors:
                failed += 1
                print(f"FAIL  {archetype}/{band}")
                for e in errors:
                    print(f"      {e}")
            else:
                passed += 1
                print(f"PASS  {archetype}/{band}")
                print(f"      deltas: mil={payload['field_deltas']['military']['raw']:+.1f}"
                      f"  ten={payload['field_deltas']['tension']['raw']:+.1f}"
                      f"  eco={payload['field_deltas']['economy']['raw']:+.1f}"
                      f"  pop={payload['field_deltas']['population']['raw']:+.1f}")
                print(f"      preview: {preview}")

    print(f"\n{passed}/{passed + failed} passed")
    return failed == 0


if __name__ == "__main__":
    success = test_all_combinations()
    sys.exit(0 if success else 1)
