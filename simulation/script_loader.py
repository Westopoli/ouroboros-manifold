"""
Loader and per-archetype dispatcher for behavior script JSON files.

Scripts live in simulation/scripts/<archetype>.json.
Non-prototype archetypes fall back to _stub_default.json with a logged warning.
load_all_scripts() eager-preloads at engine start; any schema error is raised
immediately so the mission generator never sees a broken script.
"""
import json
import os
import random

import config
from script_schema import validate_script

_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

_PROTOTYPE_ARCHETYPES = frozenset({
    "defensive_stand",
    "assault",
    "multi_front_defense",
    "counterinsurgency",
})

_ALL_ARCHETYPES = _PROTOTYPE_ARCHETYPES | frozenset({
    "siege_breaking",
    "reconquest",
    "suppression",
    "evacuation",
    "raid",
    "rear_guard",
})

_STUB_FILENAME = "_stub_default.json"


def _load_and_validate(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        script = json.load(fh)
    errors = validate_script(script)
    if errors:
        raise ValueError(
            f"Script {os.path.basename(path)!r} failed schema validation:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )
    return script


_FRAGMENTATION_BUCKETS = ("concentrated", "dispersed", "fragmented")


def _roll_fragmentation(rng: random.Random) -> str:
    """Pick a counterinsurgency fragmentation bucket weighted by config."""
    weights = config.COUNTERINSURGENCY_FRAGMENTATION_WEIGHTS
    r = rng.random()
    cumulative = 0.0
    for bucket in _FRAGMENTATION_BUCKETS:
        cumulative += weights[bucket]
        if r < cumulative:
            return bucket
    return _FRAGMENTATION_BUCKETS[-1]


def load_script(archetype: str, seed: int | None = None,
                front_count: int | None = None) -> dict:
    """Return the validated script dict for the given archetype.

    Prototype archetypes load their dedicated JSON file.
    Counterinsurgency rolls a fragmentation bucket (concentrated / dispersed /
    fragmented) using the provided seed; seed=None defaults to 0.
    Multi-front defense selects 2front or 3front variant by front_count;
    front_count=None or >=3 selects the 3-force variant.
    Non-prototype archetypes (and any unknown archetype) fall back to the stub
    with a warning so the engine never blocks on an unwritten script.
    """
    stub_path = os.path.join(_SCRIPTS_DIR, _STUB_FILENAME)

    if archetype == "counterinsurgency":
        rng = random.Random(seed if seed is not None else 0)
        bucket = _roll_fragmentation(rng)
        path = os.path.join(_SCRIPTS_DIR, f"counterinsurgency_{bucket}.json")
        return _load_and_validate(path)

    if archetype == "multi_front_defense":
        variant = "2front" if front_count == 2 else "3front"
        path = os.path.join(_SCRIPTS_DIR, f"multi_front_defense_{variant}.json")
        return _load_and_validate(path)

    if archetype in _PROTOTYPE_ARCHETYPES:
        path = os.path.join(_SCRIPTS_DIR, f"{archetype}.json")
        if os.path.exists(path):
            return _load_and_validate(path)
        # Prototype file not yet authored — fall back to stub during development
        print(
            f"[script_loader] WARNING: no script file for prototype archetype "
            f"{archetype!r}; falling back to stub (file expected at {path})"
        )
        return _load_and_validate(stub_path)

    if archetype not in _ALL_ARCHETYPES:
        print(
            f"[script_loader] WARNING: unknown archetype {archetype!r}; "
            f"falling back to stub"
        )
    else:
        print(
            f"[script_loader] WARNING: {archetype!r} has no authored script yet; "
            f"using stub fallback"
        )
    return _load_and_validate(stub_path)


def load_all_scripts(counterinsurgency_seed: int = 0) -> dict[str, dict]:
    """Eager-preload all archetypes. Raises on the first schema error encountered.

    multi_front_defense loads both variants; keys are "multi_front_defense_2front"
    and "multi_front_defense_3front" alongside the default "multi_front_defense"
    (3-front) entry.
    """
    scripts = {}
    for archetype in sorted(_ALL_ARCHETYPES):
        scripts[archetype] = load_script(archetype, seed=counterinsurgency_seed)
    scripts["multi_front_defense_2front"] = load_script("multi_front_defense", front_count=2)
    scripts["multi_front_defense_3front"] = load_script("multi_front_defense", front_count=3)
    return scripts
