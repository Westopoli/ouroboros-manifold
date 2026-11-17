# Rule pins: R-087-04, R-096-02, R-004-06
"""Engine rules round 5, G6 (DEC-hill-order-points-2026-11-17, `docs/northstar/plans/engine-rules-2026-11-08/round5.md` G6): a hill layout whose attackers must climb
sends them past the slope's midline.

Round 5 piece G6, word for word: "In a catalogue layout where one side must climb a slope to reach the other, that side's attack-move point lies at least
`DRAFT-hill-order-margin` = 30 wu past the slope's midline, on the high side."

Why (Westley, 2026-11-17, on the side agent's note that an attacker hit on the approach may back off once and stand): "For the lab layouts that require units to walk up a hill,
we need to make sure that the units on the low ground are attack moved beyond the threshold of the reduced vision of the low-ground". R-004-06: below the midline a unit is on
the lower layer, at or above it on the upper one, and the lower layer cannot see (or be seen from) the upper one until then.
E-11 R-087-04 (current text): an attack-mover acquires "within its notice distance"; a unit whose point lies on the low side of the midline marches to a point from which it
cannot see up the hill and stops there (it has arrived).

What this file measures, from the layout's own geometry and orders (no engine run):
  - the hill: each `vantage` feature is a disc of `radius` on a radial ramp of `hills.RAMP_WU` (hills.py: the band boundary, so the layer flip, falls at the ramp's middle,
    so the midline is the circle of radius + RAMP_WU / 2 about the feature's centre and the high side is inside it); each `slope` feature rises toward +x (features.py: only
    heading 0 is built) and its midline is the column where the band changes, x = c1 * cell, c1 = int((x + length / 2) // cell) - 1; the high side is beyond it
  - a side MUST CLIMB when every living enemy unit starts on the high side of one feature (no enemy is reachable on the flat) and the side has a unit that starts on the low side
    (the trap layouts, where some of the other side stand on the flat beyond the hill, have no side that must climb: a force can reach them without climbing)
  - the side's attack-move point(s) are the lab's own: `arena.run._orders_point` for both_same_point / hold:X; for `groups` each attack_move row's `to` (an `enemy_centroid`
    is read as the centroid of the enemy's starting positions)
  - the depth of a point is how far it is past the midline on the high side of the feature the enemy stand on (negative: short of it)

Positive controls: `test_control_*` below. The lint finds layouts that must climb (a count, so a lint that sees none cannot pass), flags a planted layout whose attackers stop at the
foot of the hill, and is silent on the same layout with the point moved up the slope.
"""
import copy
import glob
import math
import tomllib
from pathlib import Path

import pytest

from scripts.skilllab.arena import features, groups, hills, run

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue"
IDS = sorted(Path(p).stem for p in glob.glob(str(CATALOGUE / "L-*.toml")))

HILL_ORDER_MARGIN = 30.0     # DRAFT-hill-order-margin (wu): the attack-move point lies at least this far past the midline, on the high side (round5.md G6; Westley's to change)
CELL = hills.TERRAIN_CELL


def load(name):
    with open(CATALOGUE / (name + ".toml"), "rb") as f:
        return tomllib.load(f)


def depth(feature, p):
    """How far past the feature's midline, on its high side, the point p lies (negative: on the low side)."""
    if feature["kind"] == "vantage":
        return feature["radius"] + hills.RAMP_WU / 2 - math.hypot(p[0] - feature["x"], p[1] - feature["y"])
    c1 = int((feature["x"] + feature["length"] / 2) // CELL) - 1
    return p[0] - c1 * CELL


def hill_features(layout):
    return hills.vantages(layout) + features.slopes(layout)


def start_depth(layout, unit):
    """(feature, depth) of the feature whose high side the unit starts deepest in, or (None, None) with no feature."""
    best = (None, None)
    for f in hill_features(layout):
        d = depth(f, (unit["x"], unit["y"]))
        if best[1] is None or d > best[1]:
            best = (f, d)
    return best


def points_of(layout, side_key):
    """The attack-move point(s) the lab gives side_key ('side_a' or 'side_b'), as the lab reads them."""
    centres = run._layout_centres(layout)
    if layout.get("orders", "both_same_point") == "groups":
        other = "side_b" if side_key == "side_a" else "side_a"
        pts = []
        for r in layout["order_groups"]:
            if groups.SIDES[r["side"]][1] != side_key or r["order"] != "attack_move":
                continue
            pts.append(tuple(r["to"]) if isinstance(r["to"], list) else centres[0 if other == "side_a" else 1])
        return pts
    point, movers = run._orders_point(layout, centres)
    return [tuple(point)] if side_key in movers else []


def climbers(layout):
    """[(side key, feature)] of every side that must climb: every enemy unit starts on the high side of one feature, and the side has a unit that starts on the low side."""
    out = []
    for mine, theirs in (("side_a", "side_b"), ("side_b", "side_a")):
        enemy = [start_depth(layout, u) for u in layout[theirs]["units"]]
        if not enemy or any(f is None or d < 0 for f, d in enemy):
            continue
        feats = {id(f): f for f, _ in enemy}
        if len(feats) != 1:
            continue
        feat = next(iter(feats.values()))
        if any(depth(feat, (u["x"], u["y"])) < 0 for u in layout[mine]["units"]):
            out.append((mine, feat))
    return out


def shortfalls(layout):
    """[(side key, point, depth)] of every point of a side that must climb that lies less than HILL_ORDER_MARGIN past the midline."""
    out = []
    for side_key, feat in climbers(layout):
        for p in points_of(layout, side_key):
            d = depth(feat, p)
            if d < HILL_ORDER_MARGIN:
                out.append((side_key, p, round(d, 1)))
    return out


@pytest.mark.parametrize("name", IDS)
def test_R_087_04_a_side_that_must_climb_attack_moves_past_the_midline(name):
    """G6 / R-087-04 / R-096-02: "In a catalogue layout where one side must climb a slope to reach the other, that side's attack-move point lies at least
    DRAFT-hill-order-margin = 30 wu past the slope's midline, on the high side." Red today for the layouts the report lists (both_same_point and hold layouts whose point
    sits on the low ground); a layout where no side must climb passes by the same assertion."""
    bad = shortfalls(load(name))
    assert not bad, "%s: %s" % (name, ["%s point (%.0f, %.0f) is %.1f wu past the midline, needs %.0f" % (s, p[0], p[1], d, HILL_ORDER_MARGIN) for s, p, d in bad])


def test_control_the_catalogue_has_layouts_that_must_climb():
    """Control (green today): the lint has something to judge: at least nine layouts have a side that must climb (the nine vantage and slope layouts with every enemy on the
    hill: L-0038, L-0045, L-0061 to L-0066, L-0084), and the trap layouts (some enemies on the flat) have none. A lint that found none would pass for want of looking."""
    must = sorted(n for n in IDS if climbers(load(n)))
    assert len(must) >= 9 and {"L-0038", "L-0045", "L-0061", "L-0084"} <= set(must), must
    assert not [n for n in IDS if n in ("L-0079", "L-0080", "L-0081", "L-0082", "L-0083") and climbers(load(n))]


def planted(point):
    """A hand-built layout (not in the catalogue): a hill of radius 700 at (2000, 2000), side A (8 units) on it near its centre, side B (8 units) at the foot; both sides attack-move
    to `point`."""
    return {"orders": "both_same_point", "orders_point": list(point),
            "features": [{"kind": "vantage", "x": 2000.0, "y": 2000.0, "radius": 700.0, "height_band": 1}],
            "side_a": {"units": [{"role": "Vanguard", "x": 2000.0 + 20 * i, "y": 2000.0, "layer": 1} for i in range(8)]},
            "side_b": {"units": [{"role": "Vanguard", "x": 600.0, "y": 1900.0 + 20 * i, "layer": 0} for i in range(8)]}}


def test_control_a_planted_layout_with_the_point_at_the_foot_of_the_hill_is_flagged():
    """Control: the planted hill (midline at radius 700 + 100 = 800 from (2000, 2000)) with the point at (1150, 2000), 850 from the centre, 50 wu short of the midline, is
    flagged for side_b (depth -50)."""
    assert shortfalls(planted((1150.0, 2000.0))) == [("side_b", (1150.0, 2000.0), -50.0)]


def test_control_the_planted_layout_with_the_point_moved_up_the_slope_is_silent():
    """Control: the same layout with the point at (1250, 2000), 750 from the centre, 50 wu past the midline, is silent; a point 20 wu past it (780 from the centre) is flagged, so
    the margin is read."""
    assert shortfalls(planted((1250.0, 2000.0))) == []
    assert shortfalls(planted((1220.0, 2000.0))) == [("side_b", (1220.0, 2000.0), 20.0)]


def test_control_a_planted_slope_layout_is_judged_at_the_column_where_the_band_changes():
    """Control: a slope feature at x 2000, length 600 (c1 = 22, midline x = 2200, hills/features `_slope_heights`): a point at x 2220 is 20 past it (flagged), at x 2250 is 50 past
    (silent), and a layout with a unit of side B on the high side has no side that must climb."""
    lay = copy.deepcopy(planted((2220.0, 2000.0)))
    lay["features"] = [{"kind": "slope", "x": 2000.0, "y": 2000.0, "length": 600, "width": 200, "heading": 0.0, "from_band": 0, "to_band": 1}]
    for i, u in enumerate(lay["side_a"]["units"]):
        u["x"], u["y"] = 2400.0 + 20 * i, 2000.0
    assert shortfalls(lay) == [("side_b", (2220.0, 2000.0), 20.0)]
    lay["orders_point"] = [2250.0, 2000.0]
    assert shortfalls(lay) == []
    lay["side_b"]["units"][0]["x"] = 2500.0
    assert climbers(lay) == [("side_b", lay["features"][0])]      # one B unit on the high side does not change that every A unit is high and B has low units
    for u in lay["side_a"]["units"][:2]:
        u["x"] = 1000.0                                           # two A units on the flat: B can reach them without climbing
    assert climbers(lay) == []
