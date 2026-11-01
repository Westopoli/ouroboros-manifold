"""The `om-fight-1` fight file: one arena fight written down as a small file of snapshots (spec: docs/stories/H-039.md,
format for readers: docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md).

Every number is an Architect draft dated 2026-10-31 that Westley rules: DRAFT-snapshot-count (MAX_FRAMES, MIN_FRAMES),
DRAFT-snapshot-seconds (5 s between frames), DRAFT-fight-cap (CAP_SECONDS), DRAFT-winner."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.skilllab.contract import TICKS_PER_SECOND

SCHEMA = "om-fight-1"
MAX_FRAMES = 20     # DRAFT-snapshot-count
MIN_FRAMES = 10     # DRAFT-snapshot-count; advisory, not enforced (a short fight writes fewer)
CAP_SECONDS = 600   # DRAFT-fight-cap

_TOP = {"schema": str, "layout_id": str, "layout_path": str, "seed": int, "tick_rate": int, "snapshot_every": int,
        "sight": str, "frames": list, "result": dict}
_FRAME = {"tick": int, "alive": list, "units": list}
_UNIT = {"id": int, "side": str, "role": str, "x": "num", "y": "num", "layer": int, "facing": "num", "hp": "num",
         "alive": bool, "target": "int_or_null"}
_RESULT = {"winner": str, "survivors": list, "ticks": int, "capped": bool, "predict": str, "agree": bool}


def _kind_ok(value, kind) -> bool:
    if kind == "num":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "int_or_null":
        return value is None or (isinstance(value, int) and not isinstance(value, bool))
    if kind is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, kind)


def _check_keys(node, spec: dict, where: str, out: list) -> bool:
    """Missing, unknown and wrongly typed keys of one table; True when every key is present and typed right."""
    prefix = where + "." if where else ""
    clean = True
    for key, kind in spec.items():
        if key not in node:
            out.append(f"missing {prefix}{key}")
            clean = False
        elif not _kind_ok(node[key], kind):
            out.append(f"bad type {prefix}{key}")
            clean = False
    for key in node:
        if key not in spec:
            out.append(f"unknown key {prefix}{key}")
            clean = False
    return clean


def _check_pair(value, where: str, out: list) -> None:
    if len(value) != 2 or not all(_kind_ok(v, int) for v in value):
        out.append(f"bad type {where} (want [a, b] ints)")


def validate(doc: dict) -> list[str]:
    """Every rule of the file spec as one message each; an empty list when the document is valid."""
    out: list[str] = []
    if not isinstance(doc, dict):
        return ["document is not a table"]
    _check_keys(doc, _TOP, "", out)
    if doc.get("schema") != SCHEMA and "schema" in doc:
        out.append(f"schema is not {SCHEMA}")
    if "sight" in doc and doc["sight"] not in ("off", "on"):
        out.append("sight is not off or on")
    frames = doc.get("frames")
    if isinstance(frames, list):
        if len(frames) > MAX_FRAMES:
            out.append(f"more than {MAX_FRAMES} frames")
        ticks = []
        for i, frame in enumerate(frames):
            where = f"frames[{i}]"
            if not isinstance(frame, dict):
                out.append(f"bad type {where}")
                continue
            ok = _check_keys(frame, _FRAME, where, out)
            if _kind_ok(frame.get("tick"), int):
                ticks.append(frame["tick"])
            if isinstance(frame.get("alive"), list):
                _check_pair(frame["alive"], f"{where}.alive", out)
            if not ok and not isinstance(frame.get("units"), list):
                continue
            units = frame["units"]
            ids = []
            for j, unit in enumerate(units):
                uwhere = f"{where}.units[{j}]"
                if not isinstance(unit, dict):
                    out.append(f"bad type {uwhere}")
                    continue
                _check_keys(unit, _UNIT, uwhere, out)
                if unit.get("side") not in ("A", "B") and "side" in unit:
                    out.append(f"{uwhere}.side is not A or B")
                if _kind_ok(unit.get("id"), int):
                    ids.append(unit["id"])
            if ids != sorted(ids):
                out.append(f"{where}.units not sorted by id")
        if ticks and ticks != sorted(set(ticks)) and len(ticks) == len(frames):
            out.append("frames not in tick order")
        if frames and isinstance(frames[0], dict) and _kind_ok(frames[0].get("tick"), int) and frames[0]["tick"] != 0:
            out.append("frames[0].tick is not 0")
    result = doc.get("result")
    if isinstance(result, dict):
        _check_keys(result, _RESULT, "result", out)
        if result.get("winner") not in ("A", "B", "draw") and "winner" in result:
            out.append("result.winner is not A, B or draw")
        if result.get("predict") not in ("A", "B", "draw") and "predict" in result:
            out.append("result.predict is not A, B or draw")
        if isinstance(result.get("survivors"), list):
            _check_pair(result["survivors"], "result.survivors", out)
        if (isinstance(result.get("agree"), bool) and "winner" in result and "predict" in result
                and result["agree"] != (result["winner"] == result["predict"])):
            out.append("result.agree disagrees with winner and predict")
    return out


def write(doc: dict, path: Path) -> None:
    """Validate, then write sorted keys, indent 2, trailing newline; an invalid document raises ValueError and writes nothing."""
    msgs = validate(doc)
    if msgs:
        raise ValueError("; ".join(msgs))
    Path(path).write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read(path: Path) -> dict:
    """Load a fight file and validate it; an invalid file raises ValueError with the messages joined."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    msgs = validate(doc)
    if msgs:
        raise ValueError("; ".join(msgs))
    return doc


def frame_ticks(last_tick: int, tick_rate: int, every_seconds: int = 5, max_frames: int = MAX_FRAMES) -> list[int]:
    """The ticks the runner must snapshot: 0, then every `every_seconds`, ending in `last_tick`; the spacing doubles
    until the list has at most `max_frames` entries."""
    every = every_seconds * tick_rate
    while True:
        ticks = list(range(0, last_tick, every)) + [last_tick]
        if len(ticks) <= max_frames:
            return ticks
        every *= 2


def example(frames: int = 3, units_per_side: int = 2) -> dict:
    """A valid document for tests and readers' fixtures: `frames` frames 100 ticks apart, A and B each with
    `units_per_side` units; from the second frame on B's units are dead, so A wins, as predicted."""
    every = 5 * TICKS_PER_SECOND
    units = []
    for side_n, side in enumerate("AB"):
        for k in range(units_per_side):
            units.append({"id": side_n * units_per_side + k + 1, "side": side, "role": "Raider",
                          "x": 100.0 + 40.0 * side_n + 2.0 * k, "y": 50.0 + 4.0 * k, "layer": 0,
                          "facing": 0.0 if side == "A" else 3.142, "hp": 100.0, "alive": True, "target": None})
    last = (frames - 1) * every
    out_frames = []
    for n in range(frames):
        rows = json.loads(json.dumps(units))
        dead = n > 0 and n == frames - 1
        if dead:
            for row in rows:
                if row["side"] == "B":
                    row["hp"], row["alive"] = 0.0, False
        out_frames.append({"tick": n * every, "alive": [units_per_side, 0 if dead else units_per_side], "units": rows})
    return {
        "schema": SCHEMA, "layout_id": "L-0001", "layout_path": "docs/northstar/research/layer_dynamics/layouts/L-0001.toml",
        "seed": 1, "tick_rate": TICKS_PER_SECOND, "snapshot_every": every, "sight": "off",
        "frames": out_frames,
        "result": {"winner": "A", "survivors": [units_per_side, 0 if frames > 1 else units_per_side], "ticks": last, "capped": False,
                   "predict": "A", "agree": True},
    }
