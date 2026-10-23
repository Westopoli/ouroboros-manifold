"""Rung K2 tests (SPEC.md section 14.3): the `goals` loader change, plays, composition, build_scenario, profile.

Run from toys/layerlab/. Expected red until K2 is built: `layerlab.skill` does not exist (ModuleNotFoundError
in every test that touches it) and the loader has no `goals` key (the loader tests fail on the unknown key).
The skill modules are imported lazily so the loader tests run and fail for their own reason.

Conventions the SPEC leaves open and these tests fix (reported as gaps):
- `compose(sit, side, ...)`: `side` is 0 (label A) or 1 (label B); the group dicts it returns carry the
  loader's `"A"` / `"B"` in their `side` field.
- `enemy` is the tuple `(mix, counts)`: the share-of-cost dict and the integer count per type.
- A "mixed group" is one dict per type (a group holds one type), in roster order, contiguous in ONE shared
  line (or box): read through the spawns, the types appear in roster order along the line. S5 is the same
  list reordered by the beat rule, so the order of the dicts is the order across the approach.
- Geometry is read by re-placing every group with `formations.place` exactly as the loader does (spacing
  default 2.5 * 15 = 37.5 when the dict has no `spacing`), so a play is judged on its dicts, not on terrain.
- Naive centre: a line starts centred on the anchor; a box is only required within one spacing of it.
- S2: formation "concave", `center` = enemy anchor, `R` = 0.5 * approach_distance, `arc_deg` = 80, centred
  on the bearing to the own anchor (1 degree), `goals` of length count on one circle round the enemy
  anchor, strictly smaller than R ("the concave closes"), order attack_move.
- S1 `ramp_defense`: along the slope direction the hold centroid is the top edge + 300 (2 units), both sides.
  S1 `lane`: every hold unit inside the channel rectangle, on its own side of the strip centre.
  S1 `flat`: same start positions and layer as the naive line (order not asserted).
- Information (S4) is used only by S3 in K2 (the route feeds no slot that exists yet), so exactly the 8
  pairs {C, C + S4} with C a subset of {S1, S2, S5} coincide and the other 24 plays are distinct.
- `swap` exchanges only the `side` labels (and the group order, A first); positions stay with the geometry.
- `build_scenario(sit, skills, size, ladder="line", processes=None, config=None)`: `config` is accepted.
- `Profile.cells`: list of dicts with `situation` (the Situation id), `combo` (frozenset), `size`, `value`,
  `valid`, `r0`, `premium`, `flags`. `Profile.aggregate()`: dict keyed by combo frozenset with
  `median_premium` (None when no valid cell), `n_valid`, `n_invalid`.
"""
import copy
import dataclasses
import importlib
import itertools
import json
import math
import statistics

import pytest

from conftest import grp, make_scenario
from layerlab import scenario

FAMILIES = ("flat", "block", "wall", "barrier_ramp", "lane", "ramp_defense", "cover")
ROSTER = ("raider", "interceptor", "vanguard", "warden", "bombard", "bastion")
CAT = {"raider": "strike", "interceptor": "strike", "vanguard": "line", "warden": "line",
       "bombard": "siege", "bastion": "siege"}
BEATS = {"strike": "siege", "line": "strike", "siege": "line"}
RAIDERS = {"raider": 1.0}
MIXED = {"bombard": 0.25, "vanguard": 0.5, "raider": 0.25}      # scrambled on purpose; strike / line / siege
SKILLS5 = ("S1", "S2", "S3", "S4", "S5")


# ------------------------------------------------------------------ lazy imports and helpers

def _m(name):
    return importlib.import_module("layerlab.skill." + name)


def _sit(family, k=0, seed=7, mix=RAIDERS, **over):
    sits = _m("situation").sample_situations(k + 1, seed, families=[family])
    sit = sits[k]
    if mix is not None:
        over["mix"] = dict(mix)
    return dataclasses.replace(sit, **over) if over else sit


def _compose(sit, side, skills=(), size=8, ladder="line", enemy=None):
    return _m("plays").compose(sit, side, size, frozenset(skills), ladder=ladder, enemy=enemy)


def _anchor(sit, side):
    return tuple(sit.anchor_A if side == 0 else sit.anchor_B)


def _facing(sit, side):
    return sit.facing_A if side == 0 else sit.facing_B


def _letter(side):
    return "A" if side == 0 else "B"


def _enemy(sit, size):
    scn = _m("situation").base_scenario(sit)
    cost = _m("cost")
    total = size * cost.unit_cost(scn, "raider")
    return (dict(sit.mix), cost.counts_for_cost(sit.mix, total, scn))


def _units(groups):
    """One dict per unit, placed the way the loader places them (no terrain checks)."""
    from layerlab.formations import place
    out = []
    for gi, g in enumerate(groups):
        n = int(g["count"])
        spacing = float(g["spacing"]) if "spacing" in g else 37.5
        params = {k: g[k] for k in ("cols", "center", "R", "arc_deg", "screen_r") if k in g}
        pl = place(g.get("formation", "line"), n, float(g["x"]), float(g["y"]), float(g.get("facing", 0.0)),
                   spacing, **params)
        if "goals" in g:
            goals = [tuple(p) for p in g["goals"]]
        else:
            goals = [tuple(g.get("goal", (g["x"], g["y"])))] * n
        for k, (x, y, f) in enumerate(pl):
            out.append({"side": g["side"], "type": g["type"], "x": x, "y": y, "facing": f, "layer": g["layer"],
                        "order": g.get("order", "hold"), "goal": goals[k], "group": gi,
                        "policy": g.get("target_policy", "nearest")})
    return out


def _centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def _min_pair(units):
    return min(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) for a, b in itertools.combinations(units, 2))


def _angdiff(a, b):
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _perp(sit):
    ax, ay = sit.anchor_A
    bx, by = sit.anchor_B
    d = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / d, (by - ay) / d
    return (-uy, ux), (ux, uy)


def _lateral_means(sit, units):
    """Mean absolute lateral coordinate (across the approach) per type."""
    (px, py), _ = _perp(sit)
    acc = {}
    for u in units:
        acc.setdefault(u["type"], []).append(u["x"] * px + u["y"] * py)
    return {t: sum(v) / len(v) for t, v in acc.items()}


def _slopes(sit):
    sc = scenario.to_c(_m("situation").base_scenario(sit))
    out = []
    for i in range(sc.terrain.n_slope):
        s = sc.terrain.slope[i]
        out.append({"bottom": (s.x0, s.y0), "top": (s.x0 + s.dx * s.length, s.y0 + s.dy * s.length),
                    "dir": (s.dx, s.dy), "bl": s.bottom_layer, "tl": s.top_layer})
    return out


def _sig(groups):
    return json.dumps(groups, sort_keys=True)


def _shape(groups):
    """What a slot-blind reader sees: per-type counts, layers, orders, policies, sides."""
    counts = {}
    for g in groups:
        counts[g["type"]] = counts.get(g["type"], 0) + int(g["count"])
    return {"counts": counts, "layers": sorted(g["layer"] for g in groups),
            "orders": sorted(g.get("order", "hold") for g in groups),
            "policies": sorted(g.get("target_policy", "nearest") for g in groups),
            "sides": sorted(g["side"] for g in groups)}


# ------------------------------------------------------------------ loader: `goals`

def _goal_scn(**extra):
    return make_scenario([grp("A", "raider", 500, 1000, 3, count=3, **extra)])


GOALS = [[1000.0, 100.0], [1500.0, 300.0], [2000.0, 700.0]]


def test_goals_give_each_unit_its_own_goal():
    sc = scenario.to_c(_goal_scn(order="attack_move", goals=GOALS))
    assert sc.n_spawns == 3
    for i, (gx, gy) in enumerate(GOALS):
        assert (sc.spawns[i].gx, sc.spawns[i].gy) == (gx, gy)


def test_goals_leave_other_groups_on_their_goal():
    scn = make_scenario([grp("A", "raider", 500, 1000, 3, count=3, order="attack_move", goals=GOALS),
                         grp("B", "raider", 3000, 1000, 3, count=2, order="attack_move", goal=[10.0, 20.0])])
    sc = scenario.to_c(scn)
    assert [(sc.spawns[i].gx, sc.spawns[i].gy) for i in (3, 4)] == [(10.0, 20.0)] * 2
    assert (sc.spawns[2].gx, sc.spawns[2].gy) == (2000.0, 700.0)


@pytest.mark.parametrize("goals", [[], [[1.0, 2.0]] * 2, [[1.0, 2.0]] * 4], ids=["none", "short", "long"])
def test_goals_wrong_length_raises(goals):
    scenario.to_c(_goal_scn(order="attack_move", goals=[[1.0, 2.0]] * 3))    # right length loads: only the length is wrong
    with pytest.raises(ValueError):
        scenario.to_c(_goal_scn(order="attack_move", goals=goals))


def test_goals_exact_length_is_accepted():          # negative twin of the wrong-length cases
    scenario.to_c(_goal_scn(order="attack_move", goals=[[1.0, 2.0]] * 3))


def test_goal_and_goals_together_raise():
    scenario.to_c(_goal_scn(order="attack_move", goals=GOALS))               # each alone is fine
    scenario.to_c(_goal_scn(order="attack_move", goal=[1000.0, 1000.0]))
    with pytest.raises(ValueError):
        scenario.to_c(_goal_scn(order="attack_move", goal=[1000.0, 1000.0], goals=GOALS))


def test_scenario_without_goals_unchanged(scenarios_dir):
    path = scenarios_dir / "x0_mirror.toml"
    a = scenario.to_c(scenario.load(path))
    b = scenario.to_c(scenario.load(path))
    assert bytes(a) == bytes(b)
    assert [(a.spawns[i].gx, a.spawns[i].gy) for i in range(10)] == [(3000.0, 1000.0)] * 10
    assert [(a.spawns[i].gx, a.spawns[i].gy) for i in range(10, 20)] == [(1000.0, 1000.0)] * 10


def test_goal_default_is_group_position():
    sc = scenario.to_c(_goal_scn(order="attack_move"))
    assert [(sc.spawns[i].gx, sc.spawns[i].gy) for i in range(3)] == [(500.0, 1000.0)] * 3


def test_goals_all_equal_to_goal_is_byte_identical_to_goal():
    same = bytes(scenario.to_c(_goal_scn(order="attack_move", goal=[2500.0, 900.0])))
    assert bytes(scenario.to_c(_goal_scn(order="attack_move", goals=[[2500.0, 900.0]] * 3))) == same
    assert bytes(scenario.to_c(_goal_scn(order="attack_move", goals=GOALS))) != same     # control


# ------------------------------------------------------------------ combinations

def test_skills_and_slot_tables():
    plays = _m("plays")
    assert tuple(plays.SKILLS) == SKILLS5
    assert dict(plays.SLOT) == {"S1": "where", "S2": "shape", "S3": "layer", "S4": "info", "S5": "matchup"}


def test_all_combinations_32_distinct_fixed_order():
    combos = _m("plays").all_combinations()
    assert len(combos) == 32 and len(set(combos)) == 32
    assert all(isinstance(c, frozenset) and c <= set(SKILLS5) for c in combos)
    assert combos[0] == frozenset() and combos[-1] == frozenset(SKILLS5)
    expected = sorted((frozenset(c) for n in range(6) for c in itertools.combinations(SKILLS5, n)),
                      key=lambda c: (len(c), tuple(sorted(c))))
    assert combos == expected
    assert _m("plays").all_combinations() == combos


# ------------------------------------------------------------------ compose: the naive play

@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("ladder", ("blob", "line", "hold"))
def test_naive_play_structure(family, side, ladder):
    sit = _sit(family)
    groups = _compose(sit, side, (), 8, ladder)
    us = _units(groups)
    assert len(us) == 8                                           # 8 raider-equivalents of raiders
    assert {g["side"] for g in groups} == {_letter(side)}
    assert all(u["layer"] == sit.layer for u in us)
    assert _min_pair(us) >= 50.0 - 1e-3                           # spacing guard
    assert all(u["policy"] == "nearest" for u in us)
    anchor, enemy_anchor = _anchor(sit, side), _anchor(sit, 1 - side)
    if ladder == "hold":
        assert all(g.get("order") == "hold" for g in groups)
        assert all("goal" not in g and "goals" not in g for g in groups)
    else:
        assert all(g.get("order") == "attack_move" for g in groups)
        gc = _centroid([u["goal"] for u in us])
        assert math.hypot(gc[0] - enemy_anchor[0], gc[1] - enemy_anchor[1]) <= (60.0 if ladder == "blob" else 1.0)
    c = _centroid([(u["x"], u["y"]) for u in us])
    assert math.hypot(c[0] - anchor[0], c[1] - anchor[1]) <= (60.0 if ladder == "blob" else 1.0)
    if ladder == "blob":
        assert len(groups) == 1 and groups[0]["formation"] == "box" and groups[0]["cols"] == 5
    else:
        assert all(g.get("formation", "line") == "line" for g in groups)
        assert all(_angdiff(g.get("facing", 0.0), _facing(sit, side)) < 1e-6 for g in groups)
        along = [(u["x"] - anchor[0]) * math.cos(math.radians(_facing(sit, side)))
                 + (u["y"] - anchor[1]) * math.sin(math.radians(_facing(sit, side))) for u in us]
        assert max(along) - min(along) < 1e-3                    # abreast: a line across the approach


@pytest.mark.parametrize("side", (0, 1))
def test_naive_mixed_force_in_roster_order_in_one_line(side):
    sit = _sit("flat", mix=MIXED)
    scn = _m("situation").base_scenario(sit)
    cost = _m("cost")
    groups = _compose(sit, side, (), 6, "line")
    us = _units(groups)
    target = 6 * cost.unit_cost(scn, "raider")
    got = sum(cost.unit_cost(scn, u["type"]) for u in us)
    assert abs(got - target) <= max(cost.unit_cost(scn, t) for t in MIXED)
    assert {u["type"] for u in us} == set(MIXED)                  # every positive share has a unit
    ranks = [ROSTER.index(g["type"]) for g in groups]
    assert ranks == sorted(ranks)                                 # the dicts are in roster order
    (px, py), _ = _perp(sit)
    along_line = sorted(us, key=lambda u: u["x"] * px + u["y"] * py)
    seq = [ROSTER.index(u["type"]) for u in along_line]
    assert seq == sorted(seq) or seq == sorted(seq, reverse=True)  # one line, types contiguous in roster order
    assert _min_pair(us) >= 50.0 - 1e-3                           # also across group boundaries


# ------------------------------------------------------------------ compose: S3 layer and S4 info

@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("ladder", ("line", "hold"))
def test_s3_alone_changes_only_the_layer(family, side, ladder):
    sit = _sit(family, mix=MIXED)
    naive = _compose(sit, side, (), 6, ladder)
    s3 = _compose(sit, side, ("S3",), 6, ladder)
    assert len(s3) == len(naive)
    for a, b in zip(naive, s3):
        assert {k for k in set(a) | set(b) if a.get(k) != b.get(k)} == {"layer"}
        assert a["layer"] == sit.layer and b["layer"] == sit.layer + 1


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("side", (0, 1))
def test_s4_alone_equals_naive(family, side):
    sit = _sit(family, mix=MIXED, hidden={"route": 1, "layer": 2})
    for ladder in ("line", "hold", "blob"):
        assert _compose(sit, side, ("S4",), 6, ladder) == _compose(sit, side, (), 6, ladder)


@pytest.mark.parametrize("hidden_layer", (2, 3, 4))
def test_s3_with_s4_uses_the_hidden_layer(hidden_layer):
    sit = _sit("flat", hidden={"route": 1, "layer": hidden_layer})
    s3 = _compose(sit, 0, ("S3",))
    both = _compose(sit, 0, ("S3", "S4"))
    assert {g["layer"] for g in s3} == {sit.layer + 1}            # the naive guess: sit.layer
    assert {g["layer"] for g in both} == {hidden_layer + 1}
    assert {g["layer"] for g in _compose(sit, 0, ("S4",))} == {sit.layer}


def test_s3_with_s4_differs_from_s3_when_the_guess_is_wrong_and_equals_it_when_right():
    wrong = _sit("flat", hidden={"route": 0, "layer": 2})
    assert _compose(wrong, 0, ("S3", "S4")) != _compose(wrong, 0, ("S3",))        # positive control
    right = _sit("flat", hidden={"route": 0, "layer": 3})
    assert _compose(right, 0, ("S3", "S4")) == _compose(right, 0, ("S3",))


# ------------------------------------------------------------------ compose: S2 shape

@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("family", ("flat", "lane", "cover"))
def test_s2_alone_is_an_80_degree_concave_with_per_unit_goals(family, side):
    sit = _sit(family)
    groups = _compose(sit, side, ("S2",), 8)
    assert len(groups) == 1
    g = groups[0]
    ex, ey = _anchor(sit, 1 - side)
    assert g["formation"] == "concave" and g["arc_deg"] == 80
    assert tuple(g["center"]) == pytest.approx((ex, ey), abs=1e-6)
    radius = 0.5 * sit.approach_distance
    assert g["R"] == pytest.approx(radius)
    assert g["order"] == "attack_move" and "goal" not in g
    assert len(g["goals"]) == g["count"] == 8
    us = _units(groups)
    assert all(u["layer"] == sit.layer for u in us)
    assert _min_pair(us) >= 50.0 - 1e-3
    bearings = [math.degrees(math.atan2(u["y"] - ey, u["x"] - ex)) for u in us]
    assert all(math.hypot(u["x"] - ex, u["y"] - ey) == pytest.approx(radius, abs=1e-3) for u in us)
    own = _anchor(sit, side)
    axis = math.degrees(math.atan2(own[1] - ey, own[0] - ex))
    rel = sorted(((b - axis + 180.0) % 360.0) - 180.0 for b in bearings)
    assert rel[-1] - rel[0] == pytest.approx(80.0, abs=1e-3)
    assert abs((rel[0] + rel[-1]) / 2.0) < 1.0                    # centred on the approach bearing
    gr = [math.hypot(x - ex, y - ey) for x, y in g["goals"]]      # the goals lie on a smaller concave
    assert max(gr) - min(gr) < 1e-3 and gr[0] < radius
    assert len({tuple(p) for p in g["goals"]}) == 8               # per-unit, not one point


# ------------------------------------------------------------------ compose: S5 matchup

def _s5_case(side):
    sit = _sit("flat", mix=MIXED)
    enemy = _enemy(sit, 6)
    own = _compose(sit, side, ("S5",), 6, "line", enemy=enemy)
    foe = _units(_compose(sit, 1 - side, (), 6, "line"))
    return sit, own, foe


@pytest.mark.parametrize("side", (0, 1))
def test_s5_one_group_per_type_each_opposite_the_type_it_beats(side):
    sit, own, foe = _s5_case(side)
    assert sorted(g["type"] for g in own) == sorted(MIXED)        # one group per type
    us = _units(own)
    mine = _lateral_means(sit, us)
    theirs = _lateral_means(sit, foe)
    enemy_by_cat = {CAT[t]: lat for t, lat in theirs.items()}
    want = sorted(mine, key=lambda t: enemy_by_cat[BEATS[CAT[t]]])
    got = sorted(mine, key=lambda t: mine[t])
    assert got == want
    assert _min_pair(us) >= 50.0 - 1e-3                           # abreast, spacing kept across groups
    assert len({round(u["x"] * _perp(sit)[1][0] + u["y"] * _perp(sit)[1][1], 3) for u in us}) == 1
    assert {g["layer"] for g in own} == {sit.layer} and all(g["order"] == "attack_move" for g in own)


@pytest.mark.parametrize("side", (0, 1))
def test_s5_negative_control_naive_order_does_not_satisfy_the_beat_rule(side):
    sit, _, foe = _s5_case(side)
    naive = _units(_compose(sit, side, (), 6, "line"))
    mine = _lateral_means(sit, naive)
    enemy_by_cat = {CAT[t]: lat for t, lat in _lateral_means(sit, foe).items()}
    want = sorted(mine, key=lambda t: enemy_by_cat[BEATS[CAT[t]]])
    assert sorted(mine, key=lambda t: mine[t]) != want


# ------------------------------------------------------------------ compose: S1 where

def _lane_rect(sit):
    t = _m("situation").base_scenario(sit)["terrain"]
    w, h, cell = t.get("w_cells", 80), t.get("h_cells", 40), t.get("cell", 50.0)
    wt, ch, cx = t.get("wt", 4), t.get("ch", 8), t.get("cx", w // 2)
    lo = h // 2 - ch // 2
    return ((cx - wt // 2) * cell, (cx - wt // 2 + wt) * cell, lo * cell, (lo + ch) * cell)


@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("k", (0, 1, 2))
def test_s1_on_lane_holds_inside_the_corridor_on_its_own_side(side, k):
    sit = _sit("lane", k=k)
    xl, xr, yl, yr = _lane_rect(sit)
    mid = (xl + xr) / 2.0
    assert (sit.anchor_A[0] - mid) * (sit.anchor_B[0] - mid) < 0   # the fixture: anchors on opposite sides
    groups = _compose(sit, side, ("S1",), 4)
    us = _units(groups)
    assert len(us) == 4 and all(g["order"] == "hold" for g in groups)
    own_sign = math.copysign(1.0, _anchor(sit, side)[0] - mid)
    for u in us:
        assert xl <= u["x"] <= xr and yl <= u["y"] <= yr
        assert math.copysign(1.0, u["x"] - mid) == own_sign
        assert u["layer"] == sit.layer
    assert _min_pair(us) >= 50.0 - 1e-3


@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("k", (0, 1, 2))
def test_s1_on_ramp_defense_holds_on_the_plateau_300_beyond_the_top_edge(side, k):
    sit = _sit("ramp_defense", k=k)
    slopes = _slopes(sit)
    assert slopes, "ramp_defense must carry a slope"
    s = slopes[0]
    groups = _compose(sit, side, ("S1",), 4)
    us = _units(groups)
    assert all(g["order"] == "hold" for g in groups)
    dx, dy = s["dir"]
    along = [(u["x"] - s["top"][0]) * dx + (u["y"] - s["top"][1]) * dy for u in us]
    assert all(a > 0 for a in along)                              # on the plateau side of the top edge
    assert sum(along) / len(along) == pytest.approx(300.0, abs=2.0)
    assert _min_pair(us) >= 50.0 - 1e-3


@pytest.mark.parametrize("side", (0, 1))
def test_s1_on_flat_is_the_naive_start(side):
    sit = _sit("flat")
    a = sorted((u["x"], u["y"], u["layer"]) for u in _units(_compose(sit, side, ("S1",), 8)))
    b = sorted((u["x"], u["y"], u["layer"]) for u in _units(_compose(sit, side, (), 8)))
    assert a == pytest.approx(b, abs=1e-6)


@pytest.mark.parametrize("family", ("block", "wall", "barrier_ramp", "cover"))
@pytest.mark.parametrize("side", (0, 1))
def test_s1_on_featured_maps_holds_and_moves_off_the_naive_start(family, side):
    sit = _sit(family)
    groups = _compose(sit, side, ("S1",), 4)
    us = _units(groups)
    assert len(us) == 4 and all(g["order"] == "hold" for g in groups) and all(u["layer"] == sit.layer for u in us)
    assert _min_pair(us) >= 50.0 - 1e-3
    naive = _units(_compose(sit, side, (), 4))
    c, n = _centroid([(u["x"], u["y"]) for u in us]), _centroid([(u["x"], u["y"]) for u in naive])
    assert math.hypot(c[0] - n[0], c[1] - n[1]) > 1.0             # a better point than the anchor exists


def test_slope_edge_detector_has_a_positive_control():
    sit = _sit("ramp_defense")
    s = _slopes(sit)[0]
    sit_mod = _m("situation")
    assert sit_mod.goal_clear(sit, s["top"][0], s["top"][1], s["tl"]) is False
    assert sit_mod.goal_clear(sit, s["top"][0] + 300.0, s["top"][1], s["tl"]) is True


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("side", (0, 1))
@pytest.mark.parametrize("k", (0, 1, 2))
def test_s1_never_holds_within_100_of_a_slope_edge(family, side, k):
    sit = _sit(family, k=k)
    us = _units(_compose(sit, side, ("S1",), 4))
    goal_clear = _m("situation").goal_clear
    for u in us:
        assert goal_clear(sit, u["x"], u["y"], u["layer"])
        for s in _slopes(sit):
            for (ex, ey), layer in ((s["bottom"], s["bl"]), (s["top"], s["tl"])):
                if u["layer"] == layer:
                    assert math.hypot(u["x"] - ex, u["y"] - ey) >= 100.0


# ------------------------------------------------------------------ each skill changes only its own slot

@pytest.mark.parametrize("side", (0, 1))
def test_each_skill_changes_only_its_own_slot(side):
    sit = _sit("lane", mix=MIXED, hidden={"route": 1, "layer": 2})
    enemy = _enemy(sit, 4)
    naive = _compose(sit, side, (), 4, "line", enemy)
    base = _shape(naive)

    def play(s):
        return _compose(sit, side, (s,), 4, "line", enemy)

    s3 = play("S3")
    assert [{k for k in set(a) | set(b) if a.get(k) != b.get(k)} for a, b in zip(naive, s3)] == [{"layer"}] * len(naive)

    s4 = play("S4")
    assert s4 == naive

    s5 = _shape(play("S5"))
    assert s5 == base                                             # counts, layers, orders, policies, sides unchanged
    assert [g["type"] for g in play("S5")] != [g["type"] for g in naive]   # only the grouping moved

    s1 = _shape(play("S1"))
    assert s1["counts"] == base["counts"] and s1["layers"] == base["layers"] and s1["policies"] == base["policies"]
    assert set(s1["orders"]) == {"hold"} and s1["orders"] != base["orders"]
    assert _units(play("S1")) != _units(naive)

    s2g = play("S2")
    s2 = _shape(s2g)
    assert s2["counts"] == base["counts"] and s2["layers"] == base["layers"] and s2["policies"] == base["policies"]
    assert set(s2["orders"]) == {"attack_move"}
    assert all("goals" in g for g in s2g)
    assert [(u["x"], u["y"]) for u in _units(s2g)] != [(u["x"], u["y"]) for u in _units(naive)]


# ------------------------------------------------------------------ independence of the slots

def _independence_sit():
    return _sit("lane", mix=MIXED, hidden={"route": 1, "layer": 2})


def test_s1_with_s3_is_the_s1_play_with_the_s3_layer_applied():
    sit = _independence_sit()
    enemy = _enemy(sit, 4)
    s1 = _compose(sit, 0, ("S1",), 4, "line", enemy)
    both = _compose(sit, 0, ("S1", "S3"), 4, "line", enemy)
    assert both == [dict(g, layer=sit.layer + 1) for g in s1]
    assert both != s1                                             # control: the layer really moved


@pytest.mark.parametrize("combo", [c for n in range(1, 6) for c in itertools.combinations(SKILLS5, n)
                                   if "S3" in c], ids=lambda c: "+".join(c))
def test_s3_is_the_same_layer_overlay_in_every_combination(combo):
    sit = _independence_sit()
    enemy = _enemy(sit, 4)
    rest = tuple(s for s in combo if s != "S3")
    layer = (2 if "S4" in combo else sit.layer) + 1
    assert _compose(sit, 0, combo, 4, "line", enemy) == \
        [dict(g, layer=layer) for g in _compose(sit, 0, rest, 4, "line", enemy)]


def _distinct_sit():
    """sit.layer 3, hidden.layer 4: S3 -> layer 4, S3 + S4 -> layer 5, both differ from the naive layer 3, so
    S4 changes the play exactly when S3 is present (SPEC 14.3: the S3 layer is guess + 1)."""
    sit = _sit("lane", mix=MIXED, hidden={"route": 1, "layer": 4})
    assert sit.layer == 3
    return sit


def test_the_32_combinations_are_distinct_except_the_s4_pairs():
    sit = _distinct_sit()
    enemy = _enemy(sit, 4)
    classes = {}
    for combo in _m("plays").all_combinations():
        classes.setdefault(_sig(_compose(sit, 0, combo, 4, "line", enemy)), []).append(combo)
    got = sorted(sorted(tuple(sorted(c)) for c in v) for v in classes.values())
    want = []
    merged = []
    for n in range(6):
        for c in itertools.combinations(SKILLS5, n):
            if "S3" in c:
                want.append([c])                                  # S3 reads the hidden layer: S4 changes the play
            elif "S4" not in c:
                pair = sorted([c, tuple(sorted(set(c) | {"S4"}))])   # S4 reads nothing here: same play as without it
                want.append(pair)
                merged.append(pair)
    assert len(merged) == 8                                       # C and C + S4 for the 8 subsets C of {S1, S2, S5}
    assert len(classes) == 32 - 8 == 24
    assert got == sorted(want)


# ------------------------------------------------------------------ build_scenario

def _flat_sit():
    return _sit("flat", mix={"raider": 0.5, "vanguard": 0.25, "bombard": 0.25})


@pytest.mark.parametrize("ratio", (1.0, 2.0, 3.5))
@pytest.mark.parametrize("swap", (False, True))
def test_build_scenario_force_by_cost(ratio, swap):
    sit = _flat_sit()
    build = _m("plays").build_scenario(sit, frozenset({"S2"}), 4)
    scn = build(ratio, swap)
    cost = _m("cost")
    target = 4 * cost.unit_cost(scn, "raider")
    one = max(cost.unit_cost(scn, t) for t in sit.mix)
    skilled, naive = (1, 0) if swap else (0, 1)
    assert abs(cost.force_cost(scn, skilled) - target) <= one
    assert abs(cost.force_cost(scn, naive) - ratio * target) <= one
    scenario.to_c(scn)                                            # the scenario converts


def test_build_scenario_swap_is_the_label_swapped_twin():
    sit = _flat_sit()
    build = _m("plays").build_scenario(sit, frozenset({"S3"}), 4)
    plain, swapped = build(2.0, False), build(2.0, True)
    flip = {"A": "B", "B": "A"}

    def sigs(groups):
        return sorted(_sig(g) for g in groups)

    assert sigs(swapped["groups"]) == sigs([dict(g, side=flip[g["side"]]) for g in plain["groups"]])
    assert sigs(swapped["groups"]) != sigs(plain["groups"])       # control: the sides really exchanged
    for scn in (plain, swapped):                                  # A's groups come first in both
        sides = [g["side"] for g in scn["groups"]]
        assert sides == sorted(sides)
    cost = _m("cost")
    assert cost.force_cost(plain, 0) < cost.force_cost(plain, 1)     # swap False: skilled (smaller) is A
    assert cost.force_cost(swapped, 0) > cost.force_cost(swapped, 1)  # swap True: skilled is B, naive A first


@pytest.mark.parametrize("swap", (False, True))
def test_build_scenario_naive_skilled_play_sits_at_the_anchors(swap):
    """By role: positions stay with the geometry and only the labels swap, so the skilled force is at anchor A
    and the naive force at anchor B for both swap values."""
    sit = _sit("flat")
    scn = _m("plays").build_scenario(sit, frozenset(), 4, "hold")(1.0, swap)
    skilled_label, naive_label = ("B", "A") if swap else ("A", "B")
    for label, anchor in ((skilled_label, sit.anchor_A), (naive_label, sit.anchor_B)):
        us = [u for u in _units(scn["groups"]) if u["side"] == label]
        assert us
        c = _centroid([(u["x"], u["y"]) for u in us])
        assert math.hypot(c[0] - anchor[0], c[1] - anchor[1]) <= 1.0
        assert {u["order"] for u in us} == {"hold"}
    wrong = [u for u in _units(scn["groups"]) if u["side"] == naive_label]      # control: the label is not the anchor
    c = _centroid([(u["x"], u["y"]) for u in wrong])
    assert math.hypot(c[0] - sit.anchor_A[0], c[1] - sit.anchor_A[1]) > 100.0


def test_build_scenario_run_params_and_terrain_follow_the_situation():
    sit = _sit("lane")
    scn = _m("plays").build_scenario(sit, frozenset(), 4)(1.7, False)
    for k, v in _m("situation").run_params(sit).items():
        assert scn["run"][k] == v
    base = _m("situation").base_scenario(sit)
    assert scn["terrain"] == base["terrain"] and scn["rules"] == base["rules"]   # config None: base rules


def test_attack_is_the_larger_sides_job_in_both_labels():
    sit = _sit("flat")
    scn = _m("plays").build_scenario(sit, frozenset(), 4)(2.0, False)
    assert {g["order"] for g in scn["groups"]} == {"attack_move"}


@pytest.mark.parametrize("cfg", ("LA", "LB", "LC"))
def test_apply_config_matches_experiments_configs(cfg):
    from experiments import configs
    scn = make_scenario([grp("A", "raider", 500, 1000, 3)])
    mine = _m("plays").apply_config(copy.deepcopy(scn), cfg)
    ref = configs.apply(copy.deepcopy(scn), cfg)
    assert mine == ref
    for k in ("range_mult", "dmg_mult", "aoe_layer_mult"):
        assert mine["rules"][k] == ref["rules"][k]
    assert mine["rules"]["range_mult"] != scn["rules"]["range_mult"]     # control: the table moved


def test_apply_config_rejects_an_unknown_config():
    scn = make_scenario([grp("A", "raider", 500, 1000, 3)])
    with pytest.raises(ValueError):
        _m("plays").apply_config(scn, "LZ")


@pytest.mark.parametrize("cfg", ("LA", "LB", "LC"))
def test_build_scenario_with_config_uses_the_lever_tables(cfg):
    from experiments import configs
    sit = _sit("flat")
    scn = _m("plays").build_scenario(sit, frozenset({"S3"}), 4, config=cfg)(1.0, False)
    ref = configs.apply(_m("situation").base_scenario(sit), cfg)
    for k in ("range_mult", "dmg_mult", "aoe_layer_mult"):
        assert scn["rules"][k] == ref["rules"][k]


# ------------------------------------------------------------------ profile

def _c(cell, key):
    return cell[key] if isinstance(cell, dict) else getattr(cell, key)


def _real_profile():
    sits = [dataclasses.replace(s, mix=dict(RAIDERS)) for s in _m("situation").sample_situations(2, 11, families=["flat"])]
    combos = [frozenset(), frozenset({"S2"}), frozenset({"S1", "S2"})]
    prof = _m("plays").profile(sits, sizes=(4,), ratios=(0.7, 1.4, 2.8), refine=1, seeds=(0,),
                               combos=combos, processes=0)
    return sits, combos, prof


def test_profile_cells_and_premium():
    sits, combos, prof = _real_profile()
    assert len(prof.cells) == len(sits) * len(combos)
    seen = {(_c(c, "situation"), _c(c, "combo"), _c(c, "size")) for c in prof.cells}
    assert seen == {(s.id, cb, 4) for s in sits for cb in combos}
    for c in prof.cells:
        for key in ("value", "valid", "r0", "premium", "flags"):
            _c(c, key)
        v, r0 = _c(c, "value"), _c(c, "r0")
        if _c(c, "valid") and v is not None and r0 is not None:
            assert _c(c, "premium") == pytest.approx(v / r0)
        else:
            assert _c(c, "premium") is None


def test_profile_is_deterministic():
    _, _, a = _real_profile()
    _, _, b = _real_profile()
    assert repr(a.cells) == repr(b.cells)
    assert repr(sorted(a.aggregate().items(), key=lambda kv: sorted(kv[0]))) == \
        repr(sorted(b.aggregate().items(), key=lambda kv: sorted(kv[0])))


def _scripted_fights(scn):
    """Bigger force (by cost) wins; a concave play is the skilled side: planted non-monotone on 'flat',
    a skill bonus on 'lane' (1.1) and 'block' (5.0), none elsewhere: the S2 premiums 1.0, ~1.25, ~5.6 have a
    mean (~2.6) far from the median (~1.25)."""
    cost, fight = _m("cost"), _m("fight")
    ca, cb = cost.force_cost(scn, 0), cost.force_cost(scn, 1)
    conc = {g["side"] for g in scn["groups"] if g.get("formation") == "concave"}
    if conc:
        skilled = 0 if "A" in conc else 1
        cs, co = (ca, cb)[skilled], (ca, cb)[1 - skilled]
        preset = scn["terrain"]["preset"]
        if preset == "flat":
            sx = 1.0 if (co / cs < 1.0 or co / cs >= 2.0) else -1.0
        else:
            eff = cs * {"lane": 1.1, "block": 5.0}.get(preset, 1.0)
            sx = (eff > co) - (eff < co)
        m = float(sx if skilled == 0 else -sx)
    else:
        m = float((ca > cb) - (ca < cb))
    outcome = "win_A" if m > 0 else "win_B" if m < 0 else "stalemate"
    sides = [u["side"] for u in cost.side_units(scn)]          # SPEC 14.5 (3): the fight row carries firing counts
    return fight.FightResult(margin=m, raw_margin=m, outcome=outcome, ticks=100, first_contact_tick=10,
                             contact=True, survivors=(), alive_ticks=(100, 100), firing_ticks=(50, 50),
                             heads=(sides.count(0), sides.count(1)))


def test_aggregate_counts_invalid_cells_and_never_averages_them_in(monkeypatch):
    rstar_mod = importlib.import_module("layerlab.skill.rstar")
    monkeypatch.setattr(rstar_mod, "run_fights",
                        lambda jobs, *a, **k: [_scripted_fights(scn) for scn, _seed in jobs])
    sits = []
    for i, fam in enumerate(("flat", "lane", "block", "wall")):
        sits.append(_sit(fam, id=100 + i))
    combos = [frozenset(), frozenset({"S2"}), frozenset({"S1", "S2"})]
    prof = _m("plays").profile(sits, sizes=(4,), ratios=(0.5, 0.9, 1.05, 1.3, 2.0, 3.0, 4.0, 6.0, 8.0), refine=3,
                               seeds=(0,), combos=combos, processes=0)    # a scan wide enough for the 5.0 bonus
    assert len(prof.cells) == 12
    by = {(_c(c, "situation"), _c(c, "combo")): c for c in prof.cells}
    planted = by[(100, frozenset({"S2"}))]                       # flat + concave: non-monotone, still after the re-run
    assert _c(planted, "valid") is False and _c(planted, "premium") is None
    for sid in (100, 101, 102, 103):                              # the unskilled cells equal their R0
        c = by[(sid, frozenset())]
        assert _c(c, "valid") is True and _c(c, "premium") == pytest.approx(1.0)
    agg = prof.aggregate()
    assert set(agg) == set(combos)
    for combo in combos:
        cells = [c for c in prof.cells if _c(c, "combo") == combo]
        ok = [_c(c, "premium") for c in cells if _c(c, "valid") and _c(c, "premium") is not None]
        assert agg[combo]["n_valid"] == len(ok)
        assert agg[combo]["n_invalid"] == len(cells) - len(ok)
        assert agg[combo]["median_premium"] == pytest.approx(statistics.median(ok))
    s2 = agg[frozenset({"S2"})]
    assert s2["n_invalid"] == 1 and s2["n_valid"] == 3            # the planted cell is counted, not averaged
    ok = sorted(_c(by[(sid, frozenset({"S2"}))], "premium") for sid in (101, 102, 103))
    assert s2["median_premium"] == pytest.approx(ok[1])
    assert abs(statistics.mean(ok) - ok[1]) > 0.5                 # the fixture can tell a median from a mean
    assert ok[0] < ok[1] < ok[2]
    assert agg[frozenset()]["n_invalid"] == 0 and agg[frozenset()]["median_premium"] == pytest.approx(1.0)
