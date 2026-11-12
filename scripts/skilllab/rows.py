"""One CSV row per fight, and deterministic CSV writing (write_rows ported from toys/layerlab/layerlab/batch.py)."""
import csv
import os

_FROM_RESULT = ("outcome", "margin", "strength_left_0", "strength_left_1", "survivors_0", "survivors_1",
                "heads_0", "heads_1", "ticks", "first_contact_tick", "firing_unit_seconds_0",
                "firing_unit_seconds_1", "firing_window_0", "firing_window_1", "weighted_unit_seconds_0",
                "weighted_unit_seconds_1", "weighted_window_0", "weighted_window_1", "predicted_count",
                "predicted_type", "agreement")
_FIXED = _FROM_RESULT + ("knob", "knob_value", "baseline", "ceiling_hit", "prefight", "reengage_0", "reengage_1")

# Features field order, matching scripts.skilllab.maps.Features
_FEATURE_FIELDS = ("choke_count", "choke_width_wu", "choke_width_bodies", "lane_count", "blocked_layer_ranges",
                   "fight_layer_blocked", "cover_density_corridor", "start_distance", "detour_ratio", "blocked_layer_top")


def invalid_cell(result):
    """The sweep row's `invalid` cell: 1 a rule was broken, 0 judged clean, "suspended" not judged (checker off, engine unreadable); never 0 for a run nobody checked."""
    flag = getattr(result, "invalid", False)
    return "suspended" if flag is None else int(bool(flag))


def fight_row(result, features=None, knob="none", knob_value=None, baseline="none", ceiling_hit=0, prefight="ok", **labels):
    clash = [k for k in labels if k in _FIXED]
    if clash:
        raise ValueError("label names collide with fixed row keys: %s" % clash)
    row = dict(labels)
    row["outcome"] = result.outcome
    row["margin"] = result.margin
    row["strength_left_0"], row["strength_left_1"] = result.strength_left
    row["survivors_0"], row["survivors_1"] = result.survivors
    row["heads_0"], row["heads_1"] = result.heads
    row["ticks"] = result.ticks
    row["first_contact_tick"] = result.first_contact_tick
    row["firing_unit_seconds_0"], row["firing_unit_seconds_1"] = result.firing_unit_seconds
    row["firing_window_0"], row["firing_window_1"] = result.firing_window
    row["weighted_unit_seconds_0"], row["weighted_unit_seconds_1"] = result.weighted_unit_seconds
    row["weighted_window_0"], row["weighted_window_1"] = result.weighted_window
    row["predicted_count"], row["predicted_type"], row["agreement"] = result.predicted_count, result.predicted_type, result.agreement
    row["knob"], row["knob_value"], row["baseline"], row["ceiling_hit"], row["prefight"] = knob, knob_value, baseline, ceiling_hit, prefight
    row["reengage_0"], row["reengage_1"] = result.reengage
    if features is not None:
        for name in _FEATURE_FIELDS:
            row["feat_" + name] = getattr(features, name)
    return row


def _columns(rows):
    cols = {}
    for r in rows:
        for k in r:
            cols.setdefault(k, None)
    return list(cols)


def _cell(v):
    if v is None:
        return ""
    return repr(v) if isinstance(v, float) else str(v)


def write_rows(rows, path):
    rows = list(rows)
    parent = os.path.dirname(os.fspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if not rows:
            return
        cols = _columns(rows)
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([_cell(r.get(c)) for c in cols])
