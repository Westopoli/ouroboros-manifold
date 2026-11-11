"""The `om-fight-1` and `om-fight-2` fight file: one arena fight written down as a small file of snapshots (spec: docs/stories/H-039.md,
format for readers: docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md;
v2 adds orders and the fight end: docs/stories/H-052.md).

Every number is an Architect draft dated 2026-10-31 that Westley rules: DRAFT-snapshot-count (MAX_FRAMES, MIN_FRAMES),
DRAFT-snapshot-seconds (5 s between frames), DRAFT-fight-cap (CAP_SECONDS), DRAFT-winner."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.skilllab.contract import TICKS_PER_SECOND

SCHEMA = "om-fight-1"      # the v1 name; see also SCHEMA_V2, SCHEMAS (v1 files still validate, H-052)
SCHEMA_V2 = "om-fight-2"   # H-052: adds top-level orders, result.end, result.stall
SCHEMAS = (SCHEMA, SCHEMA_V2)
MAX_FRAMES = 20     # DRAFT-snapshot-count
MIN_FRAMES = 10     # DRAFT-snapshot-count; advisory, not enforced (a short fight writes fewer)
CAP_SECONDS = 600   # DRAFT-fight-cap

_TOP = {"schema": str, "layout_id": str, "layout_path": str, "seed": int, "tick_rate": int, "snapshot_every": int,
        "sight": str, "frames": list, "result": dict}
_FRAME = {"tick": int, "alive": list, "units": list}
_UNIT = {"id": int, "side": str, "role": str, "x": "num", "y": "num", "layer": int, "facing": "num", "hp": "num",
         "alive": bool, "target": "int_or_null"}
_RESULT = {"winner": str, "survivors": list, "ticks": int, "capped": bool, "predict": str, "agree": bool}
_ORDERS = {"mode": str, "point": list, "attacker": "side_or_null"}
_ORDER_MODES = ("both_same_point", "hold_and_attack", "groups")   # "groups": the stage 4 fix F3 per-group orders (groups.py)
_ENDS = ("wipe", "silence", "cap")
_VIOLATION = {"rule": str, "tick": int, "unit": int, "detail": str}   # F0 (scripts/skilllab/invariants.py): one broken rule, written under `violations`


def _kind_ok(value, kind) -> bool:
    if kind == "num":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "int_or_null":
        return value is None or (isinstance(value, int) and not isinstance(value, bool))
    if kind == "side_or_null":
        return value is None or value in ("A", "B")
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
    v2 = doc.get("schema") == SCHEMA_V2
    top = dict(_TOP, orders=dict) if v2 else _TOP
    if v2 and "ranges" in doc:
        top = dict(top, ranges=dict)   # H-053: optional {role: range wu}, om-fight-2 only
    if v2:
        top = dict(top, **{k: t for k, t in (("landscape", str), ("movement_kind", int), ("sights", dict), ("built_features", list), ("violations", list), ("invalid", bool)) if k in doc})   # H-063, H-088 (sights), stage 4 fix F2 (built_features), F0 2026-11-08 (violations, invalid): optional, om-fight-2 only
    _check_keys(doc, top, "", out)
    if v2 and isinstance(doc.get("violations"), list):
        for i, viol in enumerate(doc["violations"]):
            if not isinstance(viol, dict):
                out.append(f"bad type violations[{i}]")
            else:
                _check_keys(viol, _VIOLATION, f"violations[{i}]", out)
    if v2 and isinstance(doc.get("ranges"), dict):
        for role, rng in doc["ranges"].items():
            if not _kind_ok(rng, "num") or rng < 0:
                out.append(f"bad ranges.{role} (want a number at or above 0)")
    if doc.get("schema") not in SCHEMAS and "schema" in doc:
        out.append(f"schema is not {SCHEMA} or {SCHEMA_V2}")
    if v2 and isinstance(doc.get("sights"), dict):
        for role, rad in doc["sights"].items():
            if not _kind_ok(rad, "num") or rad < 0:
                out.append(f"bad sights.{role} (want a number at or above 0)")
    if v2 and isinstance(doc.get("orders"), dict):
        orders = doc["orders"]
        _check_keys(orders, dict(_ORDERS, **{k: t for k, t in (("guard", bool), ("groups", list)) if k in orders}), "orders", out)
        if "mode" in orders and orders["mode"] not in _ORDER_MODES:
            out.append("orders.mode is not both_same_point, hold_and_attack or groups")
        pt = orders.get("point")
        if isinstance(pt, list) and (len(pt) != 2 or not all(_kind_ok(v, "num") for v in pt)):
            out.append("bad type orders.point (want [x, y] numbers)")
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
            ok = _check_keys(frame, dict(_FRAME, blocked=list) if v2 and "blocked" in frame else _FRAME, where, out)   # H-063: optional, unit ids
            if v2 and isinstance(frame.get("blocked"), list) and not all(_kind_ok(b, int) for b in frame["blocked"]):
                out.append(f"bad type {where}.blocked (want a list of unit ids)")
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
                _check_keys(unit, dict(_UNIT, **{k: t for k, t in (("seen", list), ("fired", bool)) if v2 and k in unit}), uwhere, out)   # H-088: optional ids of the living enemies the unit sees; replay-firing-lines: optional `fired`
                if v2 and isinstance(unit.get("seen"), list) and not all(_kind_ok(e, int) for e in unit["seen"]):
                    out.append(f"bad type {uwhere}.seen (want a list of unit ids)")
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
        spec = dict(_RESULT, end=str, stall=bool, **({"first_seen": dict} if "first_seen" in result else {})) if v2 else _RESULT   # H-088: first_seen optional
        _check_keys(result, spec, "result", out)
        if v2 and isinstance(result.get("first_seen"), dict):
            _check_keys(result["first_seen"], {"A": "int_or_null", "B": "int_or_null"}, "result.first_seen", out)
        winners = ("A", "B", "draw", "stall", "none") if v2 else ("A", "B", "draw")
        if result.get("winner") not in winners and "winner" in result:
            out.append("result.winner is not " + ", ".join(winners[:-1]) + " or " + winners[-1])
        if v2:
            if "end" in result and result["end"] not in _ENDS:
                out.append("result.end is not wipe, silence or cap")
            stall = result.get("stall")
            if stall is True and result.get("end") != "silence":
                out.append("result.stall without result.end silence")
            if stall is True and "winner" in result and result["winner"] != "stall":
                out.append("result.stall needs result.winner stall")
            if stall is True and result.get("agree") is True:
                out.append("result.stall needs result.agree false")
            if stall is False and result.get("winner") == "stall":
                out.append("result.winner stall without result.stall")
            surv = result.get("survivors")
            if (stall is True and isinstance(surv, list) and len(surv) == 2
                    and all(_kind_ok(v, int) for v in surv) and not all(v > 0 for v in surv)):
                out.append("result.stall needs survivors on both sides")
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


def example(frames: int = 3, units_per_side: int = 2, schema: str = SCHEMA) -> dict:
    """A valid document for tests and readers' fixtures: `frames` frames 100 ticks apart, A and B each with
    `units_per_side` units; from the second frame on B's units are dead, so A wins, as predicted. `schema`
    om-fight-2 adds orders both_same_point and result.end wipe, stall false."""
    if schema not in SCHEMAS:
        raise ValueError(f"schema is not {SCHEMA} or {SCHEMA_V2}")
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
    doc = {
        "schema": schema, "layout_id": "L-0001", "layout_path": "docs/northstar/research/layer_dynamics/layouts/L-0001.toml",
        "seed": 1, "tick_rate": TICKS_PER_SECOND, "snapshot_every": every, "sight": "off",
        "frames": out_frames,
        "result": {"winner": "A", "survivors": [units_per_side, 0 if frames > 1 else units_per_side], "ticks": last, "capped": False,
                   "predict": "A", "agree": True},
    }
    if schema == SCHEMA_V2:
        doc["orders"] = {"mode": "both_same_point", "point": [120.0, 52.0], "attacker": None}
        doc["result"]["end"] = "wipe"
        doc["result"]["stall"] = False
        doc["ranges"] = {"Raider": 200.0}
    return doc
