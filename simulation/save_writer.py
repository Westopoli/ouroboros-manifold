"""
Writes the three launch-grade save classes to disk.

  write_sim_state(slot_id, sim_state)      → <save_root>/<slot_id>/sim.json
  write_tactical_state(slot_id, tactical)  → <save_root>/<slot_id>/tactical.json
  write_onboarding(slot_id, prefs)         → <save_root>/<slot_id>/onboarding.json

All writes are atomic overwrites (no history, no snapshot stack — rewind is
post-launch). Paths using the Godot-style "user://" prefix are remapped to a
local OS path by _resolve_root().
"""

import json
import os
from datetime import datetime, timezone

import config
import onboarding_store

_SCHEMA_VERSION = 1


def write_sim_state(slot_id: str, sim_state: dict, save_root: str = None) -> None:
    """Write current simulation state.

    sim_state keys expected:
      chapter_number (int), year (int), rng_state (str),
      sim_state (dict with regions/factions/coherence_ledger/diplomacy/technology/lifecycle/chronicle_entries)
    """
    path = _slot_path(save_root, slot_id, "sim.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "slot_id": slot_id,
        "chapter_number": sim_state.get("chapter_number", 0),
        "year": sim_state.get("year", 0),
        "last_written_at": _now_iso(),
        "rng_state": sim_state.get("rng_state", ""),
        "sim_state": sim_state.get("sim_state", {}),
        "last_time_jump_messages": sim_state.get("last_time_jump_messages", []),
    }
    _write_json(path, payload)


def write_tactical_state(slot_id: str, tactical_state: dict, save_root: str = None) -> None:
    """Write mid-mission tactical state for single-slot quit-and-resume.

    tactical_state keys expected:
      mission_id (str), tick (int), rng_state (str),
      engine_state (dict — TacticalEngine.export_full_state() output),
      mission_setup (dict — MissionSetup serialization)
    """
    path = _slot_path(save_root, slot_id, "tactical.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "slot_id": slot_id,
        **tactical_state,
    }
    _write_json(path, payload)


def write_onboarding(slot_id: str, prefs: dict, save_root: str = None) -> None:
    """Delegate to onboarding_store; validation lives there."""
    onboarding_store.write_onboarding(slot_id, prefs, save_root)


# ── internal ──────────────────────────────────────────────────────────────────

def _slot_path(save_root, slot_id, filename):
    return os.path.join(_resolve_root(save_root), slot_id, filename)


def _resolve_root(save_root):
    root = save_root or config.SAVE_ROOT
    if root.startswith("user://"):
        root = os.path.join(os.getcwd(), root[len("user://"):])
    return root


def _write_json(path, payload):
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
