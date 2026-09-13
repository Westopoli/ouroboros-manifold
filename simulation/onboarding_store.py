"""
Read/write onboarding preferences.

Schema: { schema_version, difficulty, rare_marks, generational_cycle_id }
Validation: difficulty in {easy, medium, hard}; len(rare_marks) < 10 (at least one
archetype must remain unmarked — see docs/bible_history/bible_2_00_missions.md §archetype rare weighting).
"""

import json
import os

import config

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
_ARCHETYPE_COUNT = 10
_FILENAME = "onboarding.json"


def write_onboarding(slot_id: str, prefs: dict, save_root: str = None) -> None:
    """Write onboarding prefs. Raises ValueError on invalid payload."""
    _validate(prefs)
    path = _path(save_root, slot_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "schema_version": 1,
        "difficulty": prefs["difficulty"],
        "rare_marks": list(prefs["rare_marks"]),
        "generational_cycle_id": prefs.get("generational_cycle_id", 1),
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def load_onboarding(slot_id: str, save_root: str = None) -> dict | None:
    path = _path(save_root, slot_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _validate(prefs: dict) -> None:
    difficulty = prefs.get("difficulty")
    if difficulty not in VALID_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of {sorted(VALID_DIFFICULTIES)}, got {difficulty!r}"
        )
    rare_marks = prefs.get("rare_marks", [])
    if len(rare_marks) >= _ARCHETYPE_COUNT:
        raise ValueError(
            f"rare_marks must leave at least one archetype unmarked "
            f"({len(rare_marks)}/{_ARCHETYPE_COUNT} marked)"
        )


def _path(save_root: str | None, slot_id: str) -> str:
    return os.path.join(_resolve_root(save_root), slot_id, _FILENAME)


def _resolve_root(save_root: str | None) -> str:
    root = save_root or config.SAVE_ROOT
    if root.startswith("user://"):
        root = os.path.join(os.getcwd(), root[len("user://"):])
    return root
