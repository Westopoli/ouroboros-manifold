import json
import os
from pathlib import Path

REQUIRED_FIELDS = {"id", "trigger_event", "headline", "body", "pointed_anchor", "accent_hint"}
LOCKED_TRIGGERS = {
    "mission_load",
    "first_unit_visible",
    "first_unit_selected",
    "first_mission_loaded",
    "first_mission_complete",
}
LOCKED_MAPPING = {
    "TUT_001": "mission_load",
    "TUT_002": "first_unit_visible",
    "TUT_003": "first_unit_selected",
    "TUT_004": "first_mission_loaded",
    "TUT_005": "first_mission_complete",
}


def _beats_path() -> Path:
    override = os.environ.get("BEATS_JSON_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "library" / "tutorial" / "beats.json"


def _load_beats() -> dict:
    with _beats_path().open("r", encoding="utf-8") as f:
        return json.load(f)


def test_beats_loads_as_dict_of_length_5():
    beats = _load_beats()
    assert isinstance(beats, dict)
    assert len(beats) == 5


def test_every_beat_has_required_fields():
    beats = _load_beats()
    for beat_id, beat in beats.items():
        assert isinstance(beat, dict), f"{beat_id} not a dict"
        assert REQUIRED_FIELDS.issubset(beat.keys()), (
            f"{beat_id} missing fields: {REQUIRED_FIELDS - set(beat.keys())}"
        )


def test_no_beat_has_placeholder_trigger_event_TBD():
    beats = _load_beats()
    for beat_id, beat in beats.items():
        assert "trigger_event_TBD" not in beat, f"{beat_id} still has trigger_event_TBD"


def test_each_trigger_event_in_allowlist():
    beats = _load_beats()
    for beat_id, beat in beats.items():
        assert beat["trigger_event"] in LOCKED_TRIGGERS, (
            f"{beat_id} trigger_event={beat['trigger_event']!r} not in allowlist"
        )


def test_trigger_events_form_exact_allowlist_set():
    beats = _load_beats()
    triggers = {beat["trigger_event"] for beat in beats.values()}
    assert triggers == LOCKED_TRIGGERS


def test_locked_mapping_per_beat_id():
    beats = _load_beats()
    for beat_id, expected_trigger in LOCKED_MAPPING.items():
        assert beat_id in beats, f"missing {beat_id}"
        assert beats[beat_id]["trigger_event"] == expected_trigger, (
            f"{beat_id} expected trigger_event={expected_trigger!r} "
            f"got {beats[beat_id]['trigger_event']!r}"
        )
