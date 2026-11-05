"""Type contract of the lab-stage4 cascade: the shared interfaces the three leaves build and the shard tests import. Sentinel bodies only; each symbol cites the spec
criterion (docs/northstar/plans/cascades/lab-stage4/spec.md) it encodes. The real code lives in the module named above each symbol; a test imports the real module,
this file is the signature record the plan-consistency pass reads."""
from typing import Optional

# --- scripts/skilllab/arena/run.py (leaf A) ---

CHECK_EVERY = 20   # spec 2: ticks, one sim second (TICKS_PER_SECOND 20, run.py already defines it as TICKS_PER_SECOND), DRAFT-seen-sample-seconds 1; `first_seen` is sampled on this cadence, tick 0 included


def fight(layout: dict, seed: int, sight: str, cap_seconds: int):
    """spec 1 and 2. Signature unchanged. With sight == "on" the stage 4 rule set runs (targeting by sight on, ground era, every role walks on a canvas, reach 0 up 1 down,
    the holder of hold:A / hold:B on engine.order_guard); with sight == "off" nothing changes. sight == "control" (internal, spec 4) is the stage 4 rule set with OM_TP_TARGET_BY_SIGHT 0: its document is written with sight "off", movement_kind 1, orders.guard as applied, and none of seen / sights / first_seen. Return shape unchanged (frames by tick, last tick, end, orders block);
    the orders block gains "guard": bool when sight == "on"; the frames gain per-unit "seen"; the end state carries first_seen for _document to write."""
    raise NotImplementedError


# CLI (spec 4): python3 -m scripts.skilllab.arena.run --layout <toml> --seed N --out <dir> [--seeds N] [--sight off|on] [--control-dir D] [--control ground|sight] [--cap-seconds S]
#   --control ground (default): today's twin (features emptied, units walk), D/<id>-control.toml, .json and D/<id>-control-s<n>.fight.json
#   --control sight: the same layout and seed with --sight off, D/<id>-control-s<n>.fight.json only, its layout_path the original layout

# fight document, additive optional keys on schema `om-fight-2` (spec 2, 3; scripts/skilllab/arena/snapshot.py validates, SNAPSHOT.md documents), written only with sight "on":
#   frames[i].units[j]["seen"]: list[int]        sorted living enemy unit ids this unit sees (engine.can_see); [] for a dead unit
#   doc["sights"]: dict[str, float]              role -> sensor radius (engine.type_stats), as doc["ranges"]
#   doc["result"]["first_seen"]: {"A": int | None, "B": int | None}   first sampled tick at which that side's living units see any living enemy
#   doc["orders"]["guard"]: bool                 true when the holder was given order_guard, false for both_same_point
# results.md (spec 4): with --sight on only, header '| id | a:b | predict | winner | survivors | ticks | agree | blocked | first seen A | first seen B |', last two cells a tick or '-'; with --sight off stage 3's header and rows, unchanged
#   doc["movement_kind"]: 1 for every --sight on fight (spec 1)

# --- scripts/skilllab/arena/snapshot.py (leaf A) ---

def validate(doc: dict) -> list:
    """spec 3. Accepts seen / sights / result.first_seen / orders.guard on om-fight-2, absent or present; rejects each on om-fight-1 naming the key. Signature unchanged: returns the list of problem messages, [] when valid (as today)."""
    raise NotImplementedError


# --- scripts/skilllab/arena/page.py (leaf C) ---

def build(d: str, out: str, control_dir: Optional[str] = None, stage: Optional[int] = None, sentences: Optional[str] = None) -> int:
    """spec 10 and 11. Signature unchanged. stage == 4 prints the header 'Stage 4, sight'. The control caption is 'control: the same fight with everyone seeing everyone
    (sight off)' when the control document's sight is 'off' and the main fight's is 'on', else today's ground caption. Every row prints
    'first seen A <tick|never>  B <tick|never>' ('-' when result.first_seen is absent). Returns 0."""
    raise NotImplementedError


# --- scenes/proto/fight_replay/fight_replay.gd (leaf B), qa_state() keys (spec 7, 8, 9) ---
QA_STATE_KEYS_STAGE4 = ("sight_rings", "sight_mode", "hollow_units", "hud_sight", "seen_counts")   # spec 7, 8, 9: the keys fight_replay.gd qa_state() gains (the .gd file has no Python symbol)
#   "sight_rings": list      [{side, role, radius, centre}, ...] as "rings"; [] when the fight file has no "sights"
#   "sight_mode": str        "role" (default) or "unit" (key V toggles)
#   "hollow_units": list     sorted unit ids drawn hollow at the current frame ([] when the frame has no "seen" keys)
#   "hud_sight": str         the HUD sight text: "A sees %d  B sees %d" on the tick line, "first seen A <tick|never>  B <tick|never>" on the last frame's end line
#   "seen_counts": list      [a, b], the sizes of the two sides' unions of "seen" at the current frame
# HUD tick line (extends stage 3's): "tick %d  A %d  B %d  blocked %d  A sees %d  B sees %d  frame %d/%d"
# DRAFT-sight-alpha 0.25, DRAFT-hollow-alpha 0.35
