"""Stage 3 rung K1: situations and guards (SPEC.md 14.2; README section 4 of the layer dynamics research).

Red until `layerlab/skill/situation.py` exists. Each test names the SPEC line it proves.

Fixtures worth knowing (all numbers derived from SPEC 6 and 14.2):
- Arena 80 x 40 cells of 50 = 4000 x 2000 world units (base.toml). `block` cx/cy default to the arena
  centre; a `ramp` with x1 40, sl 600, sw 200, g 1, h 2 has its bottom edge centre at (1975, 1000) on
  layer 1 and its top edge centre at (2575, 1000) on layer 3 (top layer = h + 1).
- Hand-built situations use the SPEC's Situation fields only, with `w_cells`, `h_cells`, `cell` in the terrain
  dict (allowed scalars in SPEC 6) so they convert whether or not `base_scenario` merges over base.toml.

SPEC gaps filled here (the tests pin the reading; a Doer who disagrees raises it, not the test):
- The "main terrain feature" of a family (asymmetry test): `block` its centre point, `wall`/`barrier`/`lane` the
  strip's centre line (x only), `ramp` the slope's bottom edge centre, and the `cover` family the largest cover
  disc. `barrier_ramp` and `ramp_defense` are read from their `preset` the same way. Flat has none and is skipped.
- Reason strings are not specified: each reason test accepts any of a few plain words naming the fault
  (see KEYWORDS) in at least one reason, and demands a non-empty list of strings.
- `goal_clear` on a layer: an edge belongs to a layer when it is the slope's bottom edge on `bottom_layer` or its
  top edge on `top_layer`. A middle layer of a multi-layer slope has no edge.
- `validate` checks anchors against slope edges on the situation's own `layer` (via goal_clear), so an anchor
  near the bottom edge (layer 1) of the ramp is clear when the situation layer is 3.
- `audit` "ticks after 20" is ambiguous by one or two: the overlap test accepts any value between the max over
  trace ticks >= 22 and the max over trace ticks >= 19.
- `stuck_units` as defined also counts a unit that has arrived at a MOVE goal and sits still; the tests avoid
  asserting on arrivals. The stuck control is a walker that reaches an uncrossable barrier and stays there.
- `sample_situations(40, seed=1)` covering all seven families is asserted as the SPEC says (n >= 14); a sampler
  that draws families at random could in principle miss one at that size, which is a finding, not a flake.
"""
import copy
import dataclasses
import math
from types import SimpleNamespace

import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, grp, make_scenario
from layerlab import scenario
from layerlab.skill.situation import (FAMILIES, Situation, audit, base_scenario, goal_clear, min_spacing,
                                      run_params, sample_situations, side_bias, spacing_ok, validate)

ROSTER = {"raider", "interceptor", "vanguard", "warden", "bombard", "bastion"}
ARENA = (4000.0, 2000.0)
CELL = 50.0
ARENA_TERRAIN = {"w_cells": 80, "h_cells": 40, "cell": CELL, "layer_spacing": 0.0}
KEYWORDS = {
    "arena": ("arena", "outside", "inside", "bounds"),
    "blocked": ("open", "block", "layer"),
    "approach": ("approach", "600", "distance", "close"),
    "edge": ("slope", "edge"),
    "mix": ("mix", "share", "sum", "1.0"),
}
RAMP = {"preset": "ramp", "x1": 40, "sl": 600.0, "sw": 200.0, "g": 1, "h": 2, **ARENA_TERRAIN}
BOTTOM_EDGE = (1975.0, 1000.0)    # layer 1
TOP_EDGE = (2575.0, 1000.0)       # layer 3


# ---- helpers -----------------------------------------------------------------------------------

def _sit(**over):
    """A clean hand-built flat situation; `over` replaces fields. approach_distance follows the anchors
    unless it is given."""
    base = dict(id=0, seed=0, family="flat", terrain={"preset": "flat", **ARENA_TERRAIN}, jitter=10.0,
                anchor_A=(500.0, 1000.0), anchor_B=(3500.0, 1000.0), facing_A=0.0, facing_B=180.0, layer=3,
                mix={"raider": 1.0}, hidden={"route": 0, "layer": 3}, approach_distance=None, notes=[])
    base.update(over)
    if base["approach_distance"] is None:
        base["approach_distance"] = math.dist(base["anchor_A"], base["anchor_B"])
    return Situation(**base)


def _ramp_sit(**over):
    return _sit(family="ramp_defense", terrain=copy.deepcopy(RAMP), anchor_A=(900.0, 1000.0),
                anchor_B=(3200.0, 1000.0), **over)


def _words(reasons, key):
    return any(w in r.lower() for r in reasons for w in KEYWORDS[key])


def _bad(sit, key):
    reasons = validate(sit)
    assert isinstance(reasons, list) and reasons, "expected reasons, got %r" % (reasons,)
    assert all(isinstance(r, str) and r for r in reasons)
    assert _words(reasons, key), "no reason mentions %s: %r" % (key, reasons)
    return reasons


def _trivial_groups(sit):
    return [grp("A", "raider", sit.anchor_A[0], sit.anchor_A[1], sit.layer, count=3, spacing=50.0,
                facing=sit.facing_A),
            grp("B", "raider", sit.anchor_B[0], sit.anchor_B[1], sit.layer, count=3, spacing=50.0,
                facing=sit.facing_B)]


def _strip_centre_x(t, w=80):
    wt = int(t.get("wt", 4))
    cx = int(t.get("cx", w // 2))
    return (cx - wt // 2 + wt / 2.0) * CELL


def _feature(sit):
    """('point', (x, y)) or ('line', x) for the family's main terrain feature, or None (flat)."""
    t = sit.terrain
    if sit.family == "cover":
        discs = t.get("cover") or []
        d = max(discs, key=lambda c: c["r"])
        return "point", (float(d["x"]), float(d["y"]))
    preset = t.get("preset", "flat")
    if preset == "flat":
        return None
    if preset == "block":
        bw, bh = int(t.get("bw", 10)), int(t.get("bh", 10))
        cx, cy = int(t.get("cx", 40)), int(t.get("cy", 20))
        return "point", ((cx - bw // 2 + bw / 2.0) * CELL, (cy - bh // 2 + bh / 2.0) * CELL)
    if preset in ("wall", "barrier", "lane"):
        return "line", _strip_centre_x(t)
    if preset == "ramp":
        return "point", (float(t.get("x1", 40)) * CELL - CELL / 2.0, float(t.get("cy", 20.0)) * CELL)
    raise AssertionError("unknown preset %r" % preset)


def _dist(feature, p):
    kind, where = feature
    return math.dist(p, where) if kind == "point" else abs(p[0] - where)


def _overlap_series(res):
    """Pairs per trace tick: alive, same effective layer, neither on a slope, closer than 29 (no slopes in
    the scenarios that use this, so the mouth exclusion is moot)."""
    out = []
    for rec in res.trace:
        a = rec["alive"].astype(bool) & ((rec["flags"] & 4) == 0)
        x, y, lay = rec["x"].astype(float), rec["y"].astype(float), rec["layer"].astype(int)
        d = np.hypot(x[:, None] - x[None, :], y[:, None] - y[None, :])
        m = a[:, None] & a[None, :] & (lay[:, None] == lay[None, :]) & np.triu(np.ones((len(x),) * 2, bool), 1)
        out.append(int(((d < 29.0) & m).sum()))
    return out


# ---- sampling ----------------------------------------------------------------------------------

def test_sampling_is_reproducible_and_seed_sensitive():
    """SPEC 14.2 sample_situations: reproducible (random.Random(seed)). Twin: another seed differs."""
    a, b = sample_situations(20, seed=1), sample_situations(20, seed=1)
    assert a == b
    assert all(isinstance(s, Situation) for s in a)
    assert sample_situations(20, seed=2) != a


def test_sampling_count():
    """SPEC 14.2: `n` situations."""
    for n in (1, 7, 20):
        assert len(sample_situations(n, seed=3)) == n


def test_every_family_appears_in_a_40_sample():
    """SPEC 14.2 FAMILIES, equal default weights, n >= 14 covers all seven."""
    assert len(FAMILIES) == 7 and set(FAMILIES) == {
        "flat", "block", "wall", "barrier_ramp", "lane", "ramp_defense", "cover"}
    sits = sample_situations(40, seed=1)
    assert {s.family for s in sits} == set(FAMILIES)


def test_families_restricts_the_draw():
    """SPEC 14.2 `families=[...]` restricts. Negative twin: nothing outside the list appears."""
    sits = sample_situations(12, seed=4, families=["lane", "cover"])
    assert len(sits) == 12 and {s.family for s in sits} <= {"lane", "cover"}
    only = sample_situations(6, seed=4, families=["ramp_defense"])
    assert {s.family for s in only} == {"ramp_defense"}


@pytest.fixture(scope="module")
def grid():
    return sample_situations(40, seed=1) + sample_situations(40, seed=2)


def test_mixes_are_quarter_shares_of_one_to_three_roster_types(grid):
    """SPEC 14.2: mixes from the roster, 1 to 3 types, shares multiples of 0.25, summing to 1."""
    for s in grid:
        assert 1 <= len(s.mix) <= 3, s.mix
        assert set(s.mix) <= ROSTER, s.mix
        for share in s.mix.values():
            assert share > 0.0 and abs(share * 4 - round(share * 4)) < 1e-9, s.mix
        assert abs(sum(s.mix.values()) - 1.0) < 1e-9, s.mix


def test_hidden_answer_ranges(grid):
    """SPEC 14.2: hidden.route in {0, 1} and hidden.layer in {2, 3, 4}; both values of each occur in 80 draws."""
    assert {s.hidden["route"] for s in grid} == {0, 1}
    assert {s.hidden["layer"] for s in grid} <= {2, 3, 4}
    assert len({s.hidden["layer"] for s in grid}) >= 2


def test_every_sample_validates_and_converts(grid):
    """SPEC 14.2: every sampled situation passes validate(); base_scenario plus one trivial group per side
    converts through scenario.to_c (terrain, anchors and layer are consistent)."""
    for s in grid:
        assert validate(s) == [], (s.id, s.family, validate(s))
        scn = base_scenario(s)
        scn["groups"] = _trivial_groups(s)
        scenario.to_c(scn)


def test_approach_distance_is_the_anchor_distance(grid):
    """SPEC 14.2: approach_distance is the straight-line distance between the anchors, at least 600."""
    for s in grid:
        assert abs(s.approach_distance - math.dist(s.anchor_A, s.anchor_B)) < 1e-6
        assert s.approach_distance >= 600.0


def test_anchors_sit_at_different_distances_from_the_feature():
    """SPEC 14.2: asymmetric (anchors at different distances from the feature; flat has none, skipped).
    A clear majority (60 percent) of 30 situations differ by more than 100 units."""
    sits = [s for s in sample_situations(30, seed=5) if s.family != "flat"]
    assert len(sits) >= 15
    differ = [abs(_dist(_feature(s), s.anchor_A) - _dist(_feature(s), s.anchor_B)) > 100.0 for s in sits]
    assert sum(differ) >= 0.6 * len(sits), "only %d of %d" % (sum(differ), len(sits))


def test_asymmetry_check_has_a_positive_control():
    """The distance check above must be able to fail: a mirrored hand-built block situation is symmetric."""
    mirrored = _sit(family="block", terrain={"preset": "block", **ARENA_TERRAIN},
                    anchor_A=(1000.0, 1000.0), anchor_B=(3000.0, 1000.0))
    assert abs(_dist(_feature(mirrored), mirrored.anchor_A) - _dist(_feature(mirrored), mirrored.anchor_B)) < 1e-9


def test_cover_family_has_cover_discs():
    """SPEC 14.2: extras (cover discs, vantage nodes) in the cover family; at least one disc each time."""
    sits = sample_situations(10, seed=6, families=["cover"])
    for s in sits:
        discs = s.terrain.get("cover") or []
        assert len(discs) >= 1, s.terrain
        for d in discs:
            assert 0.0 <= d["x"] <= ARENA[0] and 0.0 <= d["y"] <= ARENA[1] and d["r"] > 0


# ---- guards ------------------------------------------------------------------------------------

def test_min_spacing_and_spacing_ok():
    """SPEC 14.2: min_spacing = 2 * body_radius + 2 * jitter (50 at jitter 10, 30 at 0)."""
    assert min_spacing(10) == 50
    assert min_spacing(0) == 30
    assert min_spacing(10, body_radius=20.0) == 60
    assert spacing_ok(50, 10) is True
    assert spacing_ok(37.5, 10) is False
    assert spacing_ok(50, 11) is False       # needs 52
    assert spacing_ok(52, 11) is True
    assert spacing_ok(30, 0) is True and spacing_ok(29.9, 0) is False


def test_goal_clear_at_the_bottom_edge():
    """SPEC 14.2 goal_clear: within 100 of an edge centre on that layer is not clear. Bottom edge layer 1."""
    sit = _ramp_sit()
    bx, by = BOTTOM_EDGE
    assert goal_clear(sit, bx - 60, by, 1) is False
    assert goal_clear(sit, bx - 99, by, 1) is False
    assert goal_clear(sit, bx - 101, by, 1) is True
    assert goal_clear(sit, bx - 160, by, 1) is True


def test_goal_clear_euclidean_distance():
    """Distance is Euclidean: 60 along and 90 across is 108 away (clear); 60 and 60 is 85 (not clear)."""
    sit = _ramp_sit()
    bx, by = BOTTOM_EDGE
    assert goal_clear(sit, bx - 60, by + 90, 1) is True
    assert goal_clear(sit, bx - 60, by + 60, 1) is False


def test_goal_clear_at_the_top_edge():
    """Top edge centre (2575, 1000) belongs to layer 3 (top_layer = h + 1)."""
    sit = _ramp_sit()
    tx, ty = TOP_EDGE
    assert goal_clear(sit, tx - 60, ty, 3) is False
    assert goal_clear(sit, tx + 60, ty, 3) is False
    assert goal_clear(sit, tx - 160, ty, 3) is True


def test_goal_clear_is_per_layer():
    """A point beside an edge on a layer the edge does not touch is clear (README: only edge layers matter)."""
    sit = _ramp_sit()
    bx, by = BOTTOM_EDGE
    tx, ty = TOP_EDGE
    for layer in (2, 3, 4, 5):
        assert goal_clear(sit, bx - 60, by, layer) is True, layer      # bottom edge is on layer 1 only
    for layer in (1, 2, 4, 5):
        assert goal_clear(sit, tx - 60, ty, layer) is True, layer      # top edge is on layer 3 only


def test_goal_clear_without_slopes_is_always_true():
    """Negative twin: a flat situation has no slope edges."""
    sit = _sit()
    assert goal_clear(sit, 1975.0, 1000.0, 1) is True and goal_clear(sit, 2575.0, 1000.0, 3) is True


def test_validate_accepts_the_clean_constructions():
    """Controls for the reason tests below: the hand-built flat and ramp situations are fine."""
    assert validate(_sit()) == []
    assert validate(_ramp_sit()) == []


@pytest.mark.parametrize("anchor", [(-100.0, 1000.0), (5000.0, 1000.0), (500.0, 2500.0), (500.0, -1.0)])
def test_validate_anchor_outside_the_arena(anchor):
    """SPEC 14.2 validate: anchors inside the arena."""
    _bad(_sit(anchor_A=anchor), "arena")


def test_validate_anchor_blocked_at_layer():
    """SPEC 14.2 validate: anchors open on `layer`. A block with h = 3 blocks layers 1 to 3 over x 1750..2250,
    y 750..1250. Control: the same anchor with h = 2 (layer 3 open) is clean."""
    block = {"preset": "block", "bw": 10, "bh": 10, **ARENA_TERRAIN}
    blocked = _sit(family="block", terrain={**block, "h": 3}, anchor_A=(2000.0, 1000.0), anchor_B=(400.0, 1000.0))
    _bad(blocked, "blocked")
    open_ = _sit(family="block", terrain={**block, "h": 2}, anchor_A=(2000.0, 1000.0), anchor_B=(400.0, 1000.0))
    assert validate(open_) == []


def test_validate_approach_distance_below_600():
    """SPEC 14.2 validate: approach_distance at least 600, built by moving anchor B (field follows the anchors).
    Boundary twin: exactly 600 is fine."""
    _bad(_sit(anchor_B=(800.0, 1000.0)), "approach")           # 300 apart
    _bad(_sit(anchor_B=(1090.0, 1000.0)), "approach")          # 590 apart
    assert validate(_sit(anchor_B=(1100.0, 1000.0))) == []


def test_validate_anchor_near_a_slope_edge():
    """SPEC 14.2 validate: anchors clear of slope edges. Anchor B within 100 of the top edge on layer 3."""
    near = _ramp_sit()
    near = dataclasses.replace(near, anchor_B=(2625.0, 1000.0))
    near = dataclasses.replace(near, approach_distance=math.dist(near.anchor_A, near.anchor_B))
    _bad(near, "edge")
    far = dataclasses.replace(near, anchor_B=(2700.0 + 100.0, 1000.0))
    far = dataclasses.replace(far, approach_distance=math.dist(far.anchor_A, far.anchor_B))
    assert validate(far) == []
    # Negative twin: beside the BOTTOM edge (a layer 1 edge) on layer 3 is clear.
    beside = dataclasses.replace(_ramp_sit(), anchor_A=(1925.0, 1000.0))
    beside = dataclasses.replace(beside, approach_distance=math.dist(beside.anchor_A, beside.anchor_B))
    assert validate(beside) == []


def test_validate_mix_shares_must_sum_to_one():
    """SPEC 14.2 validate: mix shares sum to 1. Control: 0.5 + 0.5 is fine."""
    _bad(_sit(mix={"raider": 0.5, "vanguard": 0.25}), "mix")
    _bad(_sit(mix={"raider": 0.75, "vanguard": 0.5}), "mix")
    assert validate(_sit(mix={"raider": 0.5, "vanguard": 0.5})) == []


def test_validate_collects_every_fault():
    """Two faults give at least two reasons (a list, not the first failure)."""
    reasons = validate(_sit(anchor_B=(800.0, 1000.0), mix={"raider": 0.5}))
    assert len(reasons) >= 2
    assert _words(reasons, "approach") and _words(reasons, "mix")


# ---- run_params --------------------------------------------------------------------------------

def test_run_params_formula():
    """SPEC 14.2: stalemate_ticks = max(400, ceil(1.5 * approach / slowest * 20)); max_ticks = 6 * that, cap 20000."""
    p = run_params(_sit(approach_distance=1000.0), slowest_speed=40.0)
    assert p["stalemate_ticks"] == 750 and p["max_ticks"] == 4500
    assert run_params(_sit(approach_distance=1000.0)) == p            # default slowest_speed is 40.0
    for d, v in ((1234.0, 37.0), (2750.5, 55.0), (3000.0, 40.0)):
        want = max(400, math.ceil(1.5 * d / v * 20))
        got = run_params(_sit(approach_distance=d), v)
        assert got["stalemate_ticks"] == want and got["max_ticks"] == min(20000, 6 * want)


def test_run_params_short_approach_floors_at_400():
    """Negative twin of the formula: a short approach gives the 400 floor and max_ticks 2400."""
    p = run_params(_sit(approach_distance=500.0), slowest_speed=40.0)    # 375 -> 400
    assert p["stalemate_ticks"] == 400 and p["max_ticks"] == 2400


def test_run_params_long_approach_caps_max_ticks():
    """SPEC 14.2: max_ticks capped at 20000 (stalemate_ticks is not)."""
    p = run_params(_sit(approach_distance=10000.0), slowest_speed=40.0)    # 7500, 6x = 45000
    assert p["stalemate_ticks"] == 7500 and p["max_ticks"] == 20000


def test_run_params_scales_with_slowest_speed():
    """Halving the slowest speed doubles the stalemate window (once above the floor)."""
    slow = run_params(_sit(approach_distance=1000.0), slowest_speed=20.0)
    assert slow["stalemate_ticks"] == 1500 and slow["max_ticks"] == 9000
    fast = run_params(_sit(approach_distance=1000.0), slowest_speed=80.0)    # 375 -> floor
    assert fast["stalemate_ticks"] == 400 and fast["max_ticks"] == 2400


# ---- base_scenario -----------------------------------------------------------------------------

def test_base_scenario_carries_base_rules_terrain_jitter_and_run():
    """SPEC 14.2 base_scenario: base.toml rules, [terrain] from the situation, rules.spawn_jitter, run params, no groups."""
    sit = _ramp_sit(jitter=12.0)
    before = copy.deepcopy(sit)
    scn = base_scenario(sit)
    assert sit == before                                   # the situation is not edited
    assert scn["rules"]["forced_change_penalty"] == 0
    vis = scn["rules"]["vis_factor"]
    assert vis == vis[::-1]                                # symmetric
    assert scn["rules"]["spawn_jitter"] == 12.0
    assert scn.get("groups", []) == []
    for k, v in sit.terrain.items():
        assert scn["terrain"][k] == v, k
    assert scn["terrain"]["preset"] == "ramp"
    p = run_params(sit)
    assert scn["run"]["stalemate_ticks"] == p["stalemate_ticks"] and scn["run"]["max_ticks"] == p["max_ticks"]
    assert set(scn["types"]) >= ROSTER


def test_base_scenario_default_jitter_is_ten():
    """SPEC 14.2: spawn jitter default 10 and it reaches the scenario."""
    assert base_scenario(_sit())["rules"]["spawn_jitter"] == 10.0


# ---- audit -------------------------------------------------------------------------------------

def _fight(side_x, order="attack_move"):
    """3 v 3 raiders on a flat arena, 600 apart on the mid line, attack-move at each other."""
    a, b = side_x
    scn = make_scenario(
        [grp("A", "raider", a, 1000.0, 3, count=3, spacing=50.0, order=order, goal=[b, 1000.0], facing=0.0),
         grp("B", "raider", b, 1000.0, 3, count=3, spacing=50.0, order=order, goal=[a, 1000.0], facing=180.0)],
        run={"max_ticks": 3000, "stalemate_ticks": 400})
    return scn


def test_audit_clean_fight():
    """SPEC 14.2 audit: a clean 3 v 3 flat fight has no overlap, no stuck units, contact, no stalemate."""
    scn = _fight((1200.0, 1800.0))
    res = runmod.run(scn, seed=0, trace=True)
    assert res.winner in (0, 1)                            # fixture: a decided fight
    assert max(_overlap_series(res)[19:]) == 0             # fixture: no overlap to find
    out = audit(scn, 0)
    assert out["overlap_pairs_max"] == 0 and out["stuck_units"] == 0
    assert out["contact"] is True and out["stalemate"] is False
    assert out["ticks"] == res.ticks


def test_audit_no_contact_is_a_stalemate():
    """SPEC 14.2 audit: two holding forces 3000 apart (sensor 800) never meet: no contact, stalemate."""
    scn = make_scenario(
        [grp("A", "raider", 500.0, 1000.0, 3, count=3, spacing=50.0, facing=0.0),
         grp("B", "raider", 3500.0, 1000.0, 3, count=3, spacing=50.0, facing=180.0)],
        run={"max_ticks": 3000, "stalemate_ticks": 400})
    res = runmod.run(scn, seed=0)
    assert res.first_contact_tick == -1                    # fixture
    out = audit(scn, 0)
    assert out["contact"] is False and out["stalemate"] is True
    assert out["stuck_units"] == 0                         # hold orders are never stuck
    assert out["overlap_pairs_max"] == 0


def _walkers(order, goal=(2300.0, 1000.0)):
    """Two walkers on the ground left of a full-height barrier (x 1900..2100, h = 2), goal beyond it; no slope.
    A far parked flyer on layer 5 gives the run a second side (as in test_slope_mouth.py)."""
    scn = make_scenario(
        [grp("A", "walker", 1500.0, 1000.0, 1, order=order, goal=list(goal)),
         grp("A", "walker", 1500.0, 600.0, 1, order=order, goal=list(goal)),
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain={"preset": "barrier", "wt": 4, "h": 2},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 800, "stalemate_ticks": 1200})   # runs to 800: the last 400 ticks (400..800) come after the walker's slide along the barrier (to about tick 300); with a stalemate timer of 500 the run ended at about 500 and the audit window held the slide: a fixture defect found by the K1 builder
    return add_type(scn, "walker", "raider", movement_kind="walk")


def test_audit_stuck_positive_control():
    """SPEC 14.2 audit: walkers ordered to a goal they cannot reach (barrier, no slope) are reported stuck."""
    scn = _walkers("move")
    res = runmod.run(scn, seed=0, trace=True)
    for i in (0, 1):                                       # fixture: they reach the wall and stop there
        assert res.trace[-1, i]["x"] < 1900.0 and abs(float(res.trace[-1, i]["x"]) - float(res.trace[200, i]["x"])) < 5.0
    assert audit(scn, 0)["stuck_units"] == 2


def test_audit_stuck_negative_controls():
    """Same walkers on `hold` are not stuck (hold is excluded); a flyer on a long MOVE that keeps moving through
    the last 400 ticks is not stuck either."""
    assert audit(_walkers("hold"), 0)["stuck_units"] == 0
    flyer = make_scenario(
        [grp("A", "raider", 100.0, 1000.0, 3, order="move", goal=[3900.0, 1000.0]),
         grp("B", "raider", 3900.0, 150.0, 5)],
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 3000, "stalemate_ticks": 600})
    res = runmod.run(flyer, seed=0, trace=True)
    x = res.trace[:, 0]["x"].astype(float)
    assert abs(x[-1] - x[-401]) > 5.0                      # fixture: still travelling in the window
    assert audit(flyer, 0)["stuck_units"] == 0


def _crowd():
    """60 raiders stacked on one point inside a one-cell-wide, 2000-long channel (lane ch 1, wt 40, h 3, on layer 3).
    Hard bodies cannot resolve this inside 20 ticks, so overlap persists past tick 20 (measured: dozens of pairs)."""
    return make_scenario(
        [grp("A", "raider", 2000.0, 1025.0, 3, count=60, formation="column", spacing=0.0, facing=0.0),
         grp("B", "raider", 3900.0, 150.0, 5)],
        terrain={"preset": "lane", "ch": 1, "wt": 40, "h": 3},
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 300, "stalemate_ticks": 300})


def test_audit_overlap_positive_control_matches_a_direct_count():
    """SPEC 14.2 audit: overlap_pairs_max is the largest count of same-layer alive pairs under 29 apart after tick 20.
    A crowd squeezed into a one-body channel keeps overlapping after tick 20; the audit equals the direct count
    from the trace (band: first counted tick 19 to 22, SPEC is off by one on 'after 20')."""
    scn = _crowd()
    series = _overlap_series(runmod.run(scn, seed=0, trace=True))
    lo, hi = max(series[22:]), max(series[19:])
    assert lo > 0                                          # fixture: overlap really persists
    got = audit(scn, 0)["overlap_pairs_max"]
    assert isinstance(got, int) and lo <= got <= hi


def test_audit_overlap_ignores_the_first_20_ticks():
    """Negative twin: 12 bastions stacked on a point overlap at the start (16 pairs at tick 0) but are resolved
    well before tick 20 (measured 0 from tick 19), so the audit reports 0."""
    scn = make_scenario(
        [grp("A", "bastion", 1000.0, 1000.0, 3, count=12, formation="box", cols=4, spacing=0.0),
         grp("B", "raider", 3900.0, 150.0, 5)],
        rules={"spawn_jitter": 0.0}, run={"max_ticks": 150, "stalemate_ticks": 150})
    series = _overlap_series(runmod.run(scn, seed=0, trace=True))
    assert series[0] > 0 and max(series[22:]) == 0         # fixture
    assert audit(scn, 0)["overlap_pairs_max"] == 0


def test_audit_is_deterministic():
    """Same scenario and seed give the same audit."""
    scn = _fight((1200.0, 1800.0))
    assert audit(scn, 3) == audit(scn, 3)


# ---- side_bias ---------------------------------------------------------------------------------

def test_side_bias_is_the_label_gap():
    """SPEC 14.2: side_bias(rstar_result) is RStar.label_gap; above 0.15 flags a situation."""
    assert side_bias(SimpleNamespace(label_gap=0.2)) == 0.2
    assert side_bias(SimpleNamespace(label_gap=0.0)) == 0.0
    assert side_bias(SimpleNamespace(label_gap=0.31, value=1.0)) == 0.31
