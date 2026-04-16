"""
Loads the three launch-grade save classes from disk.

  list_slots(save_root)            → list of slot metadata dicts
  load_sim_state(slot_id)          → dict | None
  load_tactical_state(slot_id)     → dict | None
  load_onboarding(slot_id)         → dict | None
  consume_tactical_state(slot_id)  → None  (deletes file after successful resume)
  delete_slot(slot_id)             → None  (removes entire slot directory)
"""

import json
import os
import shutil

import config
import onboarding_store


def list_slots(save_root: str = None) -> list:
    """Return metadata for every slot found on disk.

    Each entry: { slot_id, chapter_number, year, last_written_at,
                  has_tactical_state, onboarding_summary }
    """
    root = _resolve_root(save_root)
    if not os.path.isdir(root):
        return []

    slots = []
    for entry in sorted(os.listdir(root)):
        slot_dir = os.path.join(root, entry)
        if not os.path.isdir(slot_dir):
            continue
        sim = _load_json(os.path.join(slot_dir, "sim.json"))
        if sim is None:
            continue  # not a valid slot
        ob = onboarding_store.load_onboarding(entry, save_root)
        slots.append({
            "slot_id": entry,
            "chapter_number": sim.get("chapter_number", 0),
            "year": sim.get("year", 0),
            "last_written_at": sim.get("last_written_at", ""),
            "has_tactical_state": os.path.exists(os.path.join(slot_dir, "tactical.json")),
            "onboarding_summary": {
                "difficulty": ob.get("difficulty") if ob else None,
                "rare_mark_count": len(ob.get("rare_marks", [])) if ob else 0,
            },
        })
    return slots


def load_sim_state(slot_id: str, save_root: str = None) -> dict | None:
    return _load_json(_slot_path(save_root, slot_id, "sim.json"))


def load_tactical_state(slot_id: str, save_root: str = None) -> dict | None:
    return _load_json(_slot_path(save_root, slot_id, "tactical.json"))


def load_onboarding(slot_id: str, save_root: str = None) -> dict | None:
    return onboarding_store.load_onboarding(slot_id, save_root)


def consume_tactical_state(slot_id: str, save_root: str = None) -> None:
    """Delete the tactical save file after a successful resume."""
    path = _slot_path(save_root, slot_id, "tactical.json")
    if os.path.exists(path):
        os.remove(path)


def delete_slot(slot_id: str, save_root: str = None) -> None:
    """Remove the entire slot directory and all its files."""
    slot_dir = os.path.join(_resolve_root(save_root), slot_id)
    if os.path.isdir(slot_dir):
        shutil.rmtree(slot_dir)


# ── internal ──────────────────────────────────────────────────────────────────

def _slot_path(save_root, slot_id, filename):
    return os.path.join(_resolve_root(save_root), slot_id, filename)


def _resolve_root(save_root):
    root = save_root or config.SAVE_ROOT
    if root.startswith("user://"):
        root = os.path.join(os.getcwd(), root[len("user://"):])
    return root


def _load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
