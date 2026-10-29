# spec: LAB-REV2-L6 (test-defect fix: stalemate_ticks retired by L2, the three fight tests take the L1/L2 `seam` fixture; field_seed kept by the shift); docs/northstar/plans/push/pp_contract.md::section 5 (om_map_set_canvas, om_map_block_rect, om_map_add_cover); plan Phase S item 5a (terrain in a Setup)
"""Terrain in a Setup: contract dataclasses, scripts/skilllab/terrain.py, and the apply order in fight().

Contract these tests fix (the implementation comes later):
  Block(x0, y0, x1, y1, layer_lo=0, layer_hi=4), Cover(x, y, radius, height), Terrain(canvas, blocks=(), covers=())
  are frozen dataclasses in contract.py; Setup.terrain defaults to None.
  Terrain(canvas, blocks=(), covers=(), field_seed=None): field_seed (a generated ground field, era kind 1) survives shift_terrain
  and with_terrain unchanged (LAB-REV2-L6: the field scene needs it).
  fight(): terrain not None -> set_canvas once, every Block in order, every Cover in order, after the settings
  and before any unit type is registered or unit spawned. terrain None -> no terrain call at all.
  terrain.shift_terrain(t, dx, dy) and terrain.with_terrain(build, terrain) -> BuildFn (terrain in play coordinates,
  shifted by (canvas_w/2, canvas_h/2) together with every group, goal, point and timeline step goal).
"""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.skilllab.fight as fight_mod  # noqa: E402
import scripts.skilllab.formations as formations_mod  # noqa: E402
from fakes_terrain import TerrainFakeEngine  # noqa: E402
from scripts.skilllab.contract import Block, Cover, Group, Setup, Step, Terrain  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402
from scripts.skilllab.terrain import shift_terrain, with_terrain  # noqa: E402

TOL = 1e-9
CANVAS = (4000.0, 3000.0)
T = Terrain(canvas=CANVAS, blocks=(Block(-10.0, -200.0, 10.0, 200.0, 0, 2), Block(50.0, 60.0, 80.0, 90.0)),
            covers=(Cover(0.0, 300.0, 40.0, 1), Cover(-100.0, -100.0, 25.0, 5)))


@pytest.fixture(autouse=True)
def place_stub(monkeypatch):
    def stub(kind, n, x, y, facing_deg, params):
        return [(x + 7.0 * i, y) for i in range(n)]

    monkeypatch.setattr(formations_mod, "place", stub)
    monkeypatch.setattr(fight_mod, "place", stub, raising=False)


def G(side, x, y=0.0, goal=None, params=None, formation="line"):
    return Group(side=side, unit="Vanguard", count=2, formation=formation, x=x, y=y,
                 facing_deg=0.0 if side == 0 else 180.0, layer=0, order="attack_move", goal=goal,
                 params=params if params is not None else {})


def S(groups=None, timeline=(), terrain=None):
    return Setup(groups=groups or (G(0, -300.0), G(1, 300.0)), unit_types={}, max_ticks=5,
                 timeline=timeline, terrain=terrain)


def built(terrain=T, setup=None):
    s = setup or S()
    return with_terrain(lambda enemy_heads, swap: s, terrain)(2, False)


# ---------------------------------------------------------------- dataclasses

def test_terrain_dataclasses_are_frozen_with_the_documented_defaults():
    """Block layers default 0..4; Terrain blocks and covers default empty; Setup.terrain defaults None; all frozen."""
    b, t = Block(0.0, 0.0, 1.0, 1.0), Terrain(canvas=(10.0, 10.0))
    assert (b.layer_lo, b.layer_hi) == (0, 4) and t.blocks == () and t.covers == () and S().terrain is None
    for obj, field in ((b, "x0"), (t, "canvas"), (Cover(0.0, 0.0, 1.0, 1), "radius")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(obj, field, 1)


# ---------------------------------------------------------------- shift_terrain

def test_shift_terrain_moves_every_block_and_cover_exactly_and_keeps_the_rest():
    """Blocks and covers move by (dx, dy) within 1e-9; canvas, layers, radius and height are untouched."""
    out = shift_terrain(T, 2000.0, 1500.0)
    assert out.canvas == CANVAS
    for a, b in zip(T.blocks, out.blocks):
        got = (b.x0, b.y0, b.x1, b.y1)
        assert got == pytest.approx((a.x0 + 2000.0, a.y0 + 1500.0, a.x1 + 2000.0, a.y1 + 1500.0), abs=TOL)
        assert (b.layer_lo, b.layer_hi) == (a.layer_lo, a.layer_hi)
    for a, c in zip(T.covers, out.covers):
        assert (c.x, c.y) == pytest.approx((a.x + 2000.0, a.y + 1500.0), abs=TOL)
        assert (c.radius, c.height) == (a.radius, a.height)
    assert len(out.blocks) == 2 and len(out.covers) == 2


def test_shift_terrain_leaves_the_input_untouched_and_is_deterministic():
    """The original Terrain is unchanged after a shift; two shifts are equal."""
    before = dataclasses.replace(T)
    assert shift_terrain(T, 5.0, -7.0) == shift_terrain(T, 5.0, -7.0)
    assert T == before and T.blocks[0].x0 == -10.0


def test_shift_terrain_keeps_corners_in_the_order_given():
    """A block given with corners reversed stays reversed after the shift."""
    t = Terrain(canvas=CANVAS, blocks=(Block(10.0, 20.0, -10.0, -20.0),))
    b = shift_terrain(t, 100.0, 200.0).blocks[0]
    assert (b.x0, b.y0, b.x1, b.y1) == pytest.approx((110.0, 220.0, 90.0, 180.0), abs=TOL)


# ---------------------------------------------------------------- with_terrain: shifting the situation

def test_with_terrain_shifts_groups_by_half_the_canvas_and_attaches_shifted_terrain():
    """Group x,y move by (w/2, h/2); the Setup carries the terrain shifted the same way."""
    out = built()
    assert [(g.x, g.y) for g in out.groups] == pytest.approx([(1700.0, 1500.0), (2300.0, 1500.0)], abs=TOL)
    assert out.terrain == shift_terrain(T, 2000.0, 1500.0)
    assert out.terrain.canvas == CANVAS


def test_with_terrain_shifts_goals_and_leaves_none_goals_none():
    """A Group.goal moves with the groups; a None goal stays None."""
    out = built(setup=S((G(0, -300.0, goal=(100.0, -50.0)), G(1, 300.0, goal=None))))
    assert out.groups[0].goal == pytest.approx((2100.0, 1450.0), abs=TOL) and out.groups[1].goal is None


def test_with_terrain_shifts_points_formation_params_and_only_those():
    """params["points"] are shifted; other params (spacing, radius) are untouched."""
    pts = [(-10.0, 5.0), (20.0, -30.0)]
    g0 = G(0, -300.0, formation="points", params={"points": pts, "spacing": 30.0})
    g1 = G(1, 300.0, params={"spacing": 30.0, "radius": 12.0})
    out = built(setup=S((g0, g1)))
    assert [tuple(p) for p in out.groups[0].params["points"]] == pytest.approx([(1990.0, 1505.0), (2020.0, 1470.0)],
                                                                              abs=TOL)
    assert out.groups[0].params["spacing"] == 30.0 and out.groups[1].params == {"spacing": 30.0, "radius": 12.0}


def test_with_terrain_shifts_timeline_step_goals_and_none_stays_none():
    """Step.goal tuples shift; a None step goal stays None; group index, when and order are untouched."""
    steps = (Step(0, ("tick", 3), "move", (10.0, 20.0)), Step(1, ("seen",), "attack_move", None))
    out = built(setup=S(timeline=steps))
    assert out.timeline[0].goal == pytest.approx((2010.0, 1520.0), abs=TOL) and out.timeline[1].goal is None
    assert [(s.group, s.when, s.order) for s in out.timeline] == [(0, ("tick", 3), "move"),
                                                                 (1, ("seen",), "attack_move")]


def test_with_terrain_does_not_touch_the_setup_the_build_returned():
    """The build's own frozen Setup and its groups are unchanged after wrapping."""
    s = S((G(0, -300.0, goal=(1.0, 2.0)), G(1, 300.0)), terrain=None)
    with_terrain(lambda e, sw: s, T)(2, False)
    assert (s.groups[0].x, s.groups[0].goal, s.terrain) == (-300.0, (1.0, 2.0), None)


def test_with_terrain_passes_enemy_heads_and_swap_to_the_build_and_is_deterministic():
    """The wrapped BuildFn forwards its arguments; two calls give equal Setups."""
    seen = []

    def build(enemy_heads, swap):
        seen.append((enemy_heads, swap))
        return S()

    wrapped = with_terrain(build, T)
    assert wrapped(7, True) == wrapped(7, True) and seen == [(7, True), (7, True)]


def test_shift_terrain_and_with_terrain_keep_the_field_seed():
    """A generated field is named by its seed: the shift moves blocks and covers and must not drop the seed (it did, 2026-10-14)."""
    t = Terrain(canvas=(12000.0, 12000.0), field_seed=11, blocks=(Block(0.0, 0.0, 10.0, 10.0),), covers=(Cover(1.0, 1.0, 5.0, 1),))
    assert shift_terrain(t, 5.0, 7.0).field_seed == 11
    assert built(terrain=t, setup=S(groups=(G(0, -300.0), G(1, 300.0)))).terrain.field_seed == 11
    assert shift_terrain(Terrain(canvas=CANVAS), 1.0, 1.0).field_seed is None


# ---------------------------------------------------------------- with_terrain: validation

def bad_terrain(**kw):
    base = dict(canvas=CANVAS, blocks=(Block(0.0, 0.0, 10.0, 10.0, 0, 4),), covers=(Cover(0.0, 0.0, 5.0, 2),))
    base.update(kw)
    return Terrain(**base)


def test_with_terrain_accepts_the_in_range_positive_control():
    """Control: an in-range terrain (canvas 28000 allowed, reversed corners, heights 0 and 5, layers 0..4) builds."""
    t = Terrain(canvas=(28000.0, 28000.0), blocks=(Block(10.0, 10.0, 0.0, 0.0, 0, 0), Block(0.0, 0.0, 1.0, 1.0, 4, 4)),
                covers=(Cover(0.0, 0.0, 0.5, 0), Cover(1.0, 1.0, 0.5, 5)))
    assert with_terrain(lambda e, s: S(), t)(1, False).terrain is not None


@pytest.mark.parametrize("canvas", [(0.0, 100.0), (100.0, 0.0), (-5.0, 100.0), (28000.5, 100.0), (100.0, 28001.0),
                                    (float("nan"), 100.0), (float("inf"), 100.0)])
def test_with_terrain_rejects_a_canvas_side_outside_zero_to_28000(canvas):
    """Canvas sides must be in (0, 28000] and finite; refused at with_terrain time, before any build call."""
    called = []
    with pytest.raises(ValueError):
        with_terrain(lambda e, s: called.append(1), bad_terrain(canvas=canvas))
    assert called == []


@pytest.mark.parametrize("block", [Block(5.0, 0.0, 5.0, 10.0), Block(0.0, 7.0, 10.0, 7.0),
                                   Block(0.0, 0.0, 10.0, 10.0, 3, 2), Block(0.0, 0.0, 10.0, 10.0, 0, 5)])
def test_with_terrain_rejects_a_bad_block(block):
    """Zero width, zero height, layer_lo > layer_hi and layer_hi 5 each raise ValueError at construction."""
    with pytest.raises(ValueError):
        with_terrain(lambda e, s: S(), bad_terrain(blocks=(block,)))


@pytest.mark.parametrize("cover", [Cover(0.0, 0.0, 0.0, 1), Cover(0.0, 0.0, -2.0, 1), Cover(0.0, 0.0, 5.0, 6),
                                   Cover(0.0, 0.0, 5.0, -1), Cover(0.0, 0.0, 5.0, 2.5)])
def test_with_terrain_rejects_a_bad_cover(cover):
    """Radius <= 0, height below 0 or above 5, and a non-whole height each raise ValueError at construction."""
    with pytest.raises(ValueError):
        with_terrain(lambda e, s: S(), bad_terrain(covers=(cover,)))


@pytest.mark.parametrize("groups,match", [
    ((G(0, -2500.0), G(1, 300.0)), "group"),                       # shifted x = -500, off the canvas
    ((G(0, -300.0), G(1, 300.0, y=1600.0)), "group"),              # shifted y = 3100 > 3000
    ((G(0, -300.0, goal=(3000.0, 0.0)), G(1, 300.0)), "goal"),     # shifted x = 5000
    ((G(0, -300.0, formation="points", params={"points": [(0.0, 9000.0)]}), G(1, 300.0)), "point"),
])
def test_with_terrain_rejects_a_position_goal_or_point_outside_the_canvas(groups, match):
    """The shifted situation must lie inside the canvas; the ValueError names what is outside. Control: the default is fine."""
    built()
    with pytest.raises(ValueError, match=match):
        built(setup=S(groups))


def test_with_terrain_rejects_a_timeline_step_goal_outside_the_canvas():
    """A step goal that shifts off the canvas raises ValueError naming the goal."""
    with pytest.raises(ValueError, match="goal"):
        built(setup=S(timeline=(Step(0, ("tick", 1), "move", (-9000.0, 0.0)),)))


# ---------------------------------------------------------------- fight(): apply order

def test_fight_applies_canvas_then_blocks_then_covers_before_any_registration_or_spawn(seam):
    """set_canvas once, every Block in order, every Cover in order; all after set_param and before register/spawn."""
    fake = TerrainFakeEngine()
    setup = dataclasses.replace(S(terrain=T), unit_types={"Big": {"base": "Vanguard", "scale": {"max_hp": 2.0}, "set": {}}},
                                groups=(G(0, -300.0), dataclasses.replace(G(1, 300.0), unit="Big")),
                                settings={"OM_TP_TARGET_POLICY": 1})
    fight(setup, 1, False, engine=fake)
    names = [c[0] for c in fake.calls]
    tc = fake.terrain_calls()
    assert [c[0] for c in tc] == ["set_canvas", "block_rect", "block_rect", "add_cover", "add_cover"]
    assert tc[0][2:] == (4000.0, 3000.0)
    assert [c[2:] for c in tc[1:3]] == [(-10.0, -200.0, 10.0, 200.0, 0, 2), (50.0, 60.0, 80.0, 90.0, 0, 4)]
    assert [c[2:] for c in tc[3:]] == [(0.0, 300.0, 40.0, 1), (-100.0, -100.0, 25.0, 5)]
    last_terrain = max(i for i, n in enumerate(names) if n in ("set_canvas", "block_rect", "add_cover"))
    first_unit = min(i for i, n in enumerate(names) if n in ("register_unit_type", "spawn", "type_stats"))
    assert names.index("set_param") < names.index("set_canvas") and last_terrain < first_unit
    assert names.count("set_canvas") == 1


def test_fight_with_no_terrain_makes_no_terrain_call_and_the_log_is_unchanged(seam):
    """terrain None: no terrain call; the whole call log equals the log of the same fight on a terrain-free Setup."""
    a, b = TerrainFakeEngine(), TerrainFakeEngine()
    fight(S(), 1, False, engine=a)
    fight(dataclasses.replace(S(), terrain=None), 1, False, engine=b)
    assert a.terrain_calls() == [] and a.calls == b.calls


def test_fight_with_terrain_is_deterministic_and_keeps_the_rest_of_the_log(seam):
    """Same seed twice gives equal results and logs; the log without terrain calls equals the no-terrain log."""
    a, b, c = TerrainFakeEngine(), TerrainFakeEngine(), TerrainFakeEngine()
    ra, rb = fight(S(terrain=T), 3, False, engine=a), fight(S(terrain=T), 3, False, engine=b)
    fight(S(), 3, False, engine=c)
    assert ra == rb and a.calls == b.calls
    assert [x for x in a.calls if x[0] not in ("set_canvas", "block_rect", "add_cover")] == c.calls
