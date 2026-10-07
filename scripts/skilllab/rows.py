"""One CSV row per fight, and deterministic CSV writing (write_rows ported from toys/layerlab/layerlab/batch.py)."""
import csv
import os

_FIXED = ("outcome", "margin", "strength_left_0", "strength_left_1", "survivors_0", "survivors_1",
          "heads_0", "heads_1", "ticks", "first_contact_tick", "firing_unit_seconds_0",
          "firing_unit_seconds_1")

# Features field order, matching scripts.skilllab.maps.Features
_FEATURE_FIELDS = ("choke_count", "choke_width_wu", "choke_width_bodies", "lane_count", "blocked_layer_ranges",
                   "fight_layer_blocked", "cover_density_corridor", "start_distance", "detour_ratio", "blocked_layer_top")


def fight_row(result, features=None, **labels):
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
    if result.mopup_orders is not None:
        row["mopup_orders"] = result.mopup_orders
    if result.weighted is not None:
        row["weighted_unit_seconds_0"], row["weighted_unit_seconds_1"] = result.weighted_unit_seconds
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
