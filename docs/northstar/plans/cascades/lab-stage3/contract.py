"""Type contract of the lab-stage3 cascade: the shared interfaces the seven leaves build and the shard tests import. Sentinel bodies only; each symbol cites the spec
criterion (docs/northstar/plans/cascades/lab-stage3/spec.md) it encodes. The real code lives in the module named above each symbol; a test imports the real module,
this file is the signature record the plan-consistency pass reads."""
from typing import Optional

# --- scripts/skilllab/arena/features.py (leaf A) ---

NAV_CELL = 50.0   # spec 1: wu, the engine's OM_NAVMESH_CELL_SIZE; the reachability grid's cell


def first_unreachable(engine, w, layout: dict, preset: dict, point: tuple, sides: tuple) -> Optional[str]:
    """spec 1. 'side_b unit 2' for the first unit (side_a rows first) of `sides` with no 4-connected route of open cells to `point`, else None. `w` is a world on which
    features.apply(engine, w, layout, preset, seed) has run (a slope's walk mask is read from it). Replaces the old (layout, preset, point, sides) signature."""
    raise NotImplementedError


# --- scripts/skilllab/arena/run.py (leaf B) ---

def control_twin(layout: dict, layout_path: str, control_dir: str):
    """spec 3 and 4. (twin_layout, twin_toml_path): twin_layout = {**layout, "features": [], "movement": "walk"} when features.bound(layout), else (None, None). Writes
    <control_dir>/<id>-control.toml and <id>-control.json; the returned path is the TOML, the control fight document's `layout_path`."""
    raise NotImplementedError


# fight document, additive optional keys on schema `om-fight-2` (spec 3, 5; scripts/skilllab/arena/snapshot.py validates, SNAPSHOT.md documents):
#   "landscape": str          the layout's preset name, always written by run.py
#   "movement_kind": int      1 when the fight's units walk (ground or a control twin with movement "walk"), key absent when they fly
# results.md (spec 6): header '| id | a:b | predict | winner | survivors | ticks | agree | blocked |', last cell = sum(len(frame.get("blocked", [])) for frame in frames)

# --- scripts/skilllab/arena/page.py (leaf D) ---

def build(d: str, out: str, control_dir: Optional[str] = None, stage: Optional[int] = None, sentences: Optional[str] = None) -> int:
    """spec 10 and 11. Writes the page; CLI flags --control-dir, --stage N, --sentences <md>. Returns 0."""
    raise NotImplementedError


# --- scenes/proto/fight_replay/fight_replay.gd (leaf C), qa_state() keys (spec 7, 8, 9) ---
#   "landscape": str          preset name used ("small_flat" when the fight file has none)
#   "features": list          [] for a control fight
#   "blocked_units": list     unit ids blocked at the current frame (exists today)
# HUD tick line: "tick %d  A %d  B %d  blocked %d  frame %d/%d"

# --- scripts/replay.sh (leaf E), spec 12 ---
#   scripts/replay.sh <fight.json> [--shots <dir>] [--dry-run]    env: GODOT, OM_UNAME; exit 2 on a missing fight file
#   --dry-run prints two lines: the import line (<godot> --headless --import --path <repo>) and the launch line with OM_FIGHT=<absolute fight path>

# --- scripts/skilllab/arena/situations.py (leaf G), spec 14 ---
#   Features table row kind=slope, size "<length> x <width>"  ->  {"kind": "slope", "x", "y", "length", "width", "heading": 0.0, "from_band": 0, "to_band": 1}
