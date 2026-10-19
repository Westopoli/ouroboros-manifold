# spec: LAB-REV2-L6 (docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md, the L6 row: the two variants; Architect design call 2026-10-14); R-005-09 (ground vision)
"""The two ground-scene variants of LAB-REV2-L6, each carrying the control of a knob that is inert in the natural scene s1_slope_top:
s1_slope_top_marginal (OM_TP_SIGHT_EYE_HEIGHT) and s1_slope_top_flyer (OM_TP_GROUND_FLYER_SEEN_MULT, R-005-11). Marked `variant`: they may
fail without blocking the natural scene.

Variant s1_slope_top_marginal: the eye-height control.

Why a variant: in the natural scene OM_TP_SIGHT_EYE_HEIGHT is inert (every sight line from the top of seed 11's slope 2 to its foot is clear
at eye 25 and up), so it is listed in INERT_KNOBS. This scene carries the control: the holder's post stands where the sight line to the
attackers' start flips between eye 50 (not seen) and eye 100 (seen).

Contract these tests fix for scripts/skilllab/ground/scenes_ground.py:
  slope_top_marginal(size=16) -> build(enemy_heads, swap) -> Setup, the same shape as slope_top (M1 on both sides in equal halves,
    holder on guard one layer above the attackers, attackers on attack_move to Setup.point = the holder's placed mean, seed 11, canvas
    sg.CANVAS, every placed unit on walkable ground of its own band at the jitter corners), build.labels["scene"] == "s1_slope_top_marginal",
    build.labels["prefight"] == "ok".
  INERT_KNOBS_BY_SCENE = {scene label: {parameter name: reason}}; the entry for "s1_slope_top_marginal" does not list OM_TP_SIGHT_EYE_HEIGHT.
Hint for the builder (measured 2026-10-14, seed 11, canvas 12000): the attackers' start must be inside the pocket that routing can use, the
band-2 cells of slope 2's foot (walk-mask cells (91,29), (92,29), (93,29), (93,30), (93,31) and the ribbon row 31), not the open ground east
of it; a pocket centred near (9270, 2950) with a holder centre near (8900, 3220) and a blob radius of about 30 + 3 * sqrt(heads) flips between
eye 50 and 100 for every attacker at every jitter corner. Do not widen preflight to make another place pass.
Test numbers are test drafts (2026-10-14), Westley may tighten: FOOT_NEAR, SEEDS."""
import ctypes
import dataclasses
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight, formations, scenes  # noqa: E402
from scripts.skilllab.contract import SHIFT_MAX  # noqa: E402
from scripts.skilllab.ground import scenes_ground as sg  # noqa: E402

pytestmark = pytest.mark.variant

SCENE = "s1_slope_top_marginal"
EYE = "OM_TP_SIGHT_EYE_HEIGHT"
FOOT_NEAR = 300.0                    # test draft (2026-10-14): the attackers start within this of the slope's foot
SEEDS = (1, 2)                       # test draft (2026-10-14)
OPENING = 20                         # ticks watched for first sight
CORNERS = ((0.0, 0.0), (-SHIFT_MAX, -SHIFT_MAX), (-SHIFT_MAX, SHIFT_MAX), (SHIFT_MAX, -SHIFT_MAX), (SHIFT_MAX, SHIFT_MAX))


class _Slope(ctypes.Structure):
    _fields_ = [(n, ctypes.c_double) for n in ("x0", "y0", "x1", "y1", "mx", "my", "length")] + \
               [("lower_band", ctypes.c_int32), ("upper_band", ctypes.c_int32)]


class Spy(engine.Engine):
    """Counts, before each of the first OPENING ticks, how many attackers (side 0) the holders (side 1) see."""

    def __init__(self):
        super().__init__()
        self.ids, self.tick, self.seen = {0: [], 1: []}, 0, []

    def spawn(self, w, type_id, side, x, y, layer):
        u = super().spawn(w, type_id, side, x, y, layer)
        self.ids[side].append(u)
        return u

    def step(self, w):
        if self.tick < OPENING:
            self.seen.append(len(self.seen_by_sight(w, 1, self.ids[0])))
        self.tick += 1
        return super().step(w)

    @property
    def first_sight(self):
        return next((t for t, n in enumerate(self.seen) if n), None)


def _setup(build, heads=16, **settings):
    s = build(heads, False)
    return dataclasses.replace(s, settings={**s.settings, **settings})


def _watch(build, seed, **settings):
    spy = Spy()
    result = fight.fight(_setup(build, **settings), seed, False, engine=spy)
    return spy, result


@pytest.fixture(scope="module")
def lib():
    return engine.Engine()


@pytest.fixture(scope="module")
def field(lib):
    w = lib.new_world(0)
    lib.set_canvas(w, sg.CANVAS, sg.CANVAS)
    assert lib.terrain_generate(w, sg.SEED, sg.CANVAS) == 0
    yield w
    lib.free_world(w)


def _side(setup, side):
    return [g for g in setup.groups if g.side == side]


def _placed(groups):
    return [p for g in groups for p in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params)]


def _centroid(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


# ---------------------------------------------------------------- identity and structure (the natural scene's shape)

def test_labels_name_the_variant_and_the_preflight_is_ok(lib):
    build = sg.slope_top_marginal()
    s = build(16, False)
    assert build.labels["scene"] == SCENE and build.labels["prefight"] == "ok"
    assert scenes.preflight(s, lib) == "ok"
    assert s.terrain.field_seed == sg.SEED and s.terrain.canvas == (sg.CANVAS, sg.CANVAS)


def test_the_build_is_deterministic_and_swap_does_not_change_the_setup():
    build = sg.slope_top_marginal()
    assert build(16, False) == build(16, False) == build(16, True)


@pytest.mark.parametrize("size,heads", [(16, 16), (24, 12), (16, 48), (16, 8)])
def test_both_sides_field_the_m1_mix_in_equal_halves(size, heads):
    s = sg.slope_top_marginal(size)(heads, False)
    for side, n in ((0, size), (1, heads)):
        counts = {}
        for g in _side(s, side):
            counts[g.unit] = counts.get(g.unit, 0) + g.count
        assert set(counts) == {"Vanguard", "Raider"} and sum(counts.values()) == n and abs(counts["Vanguard"] - counts["Raider"]) <= 1, counts


def test_orders_point_and_layers_follow_the_natural_scene():
    s = sg.slope_top_marginal()(16, False)
    assert {g.order for g in _side(s, 1)} == {"guard"} and {g.order for g in _side(s, 0)} == {"attack_move"}
    hx, hy = _centroid(_placed(_side(s, 1)))
    assert s.point == pytest.approx((hx, hy), abs=1e-6)
    la, lh = {g.layer for g in _side(s, 0)}, {g.layer for g in _side(s, 1)}
    assert len(la) == 1 and len(lh) == 1 and lh.pop() == la.pop() + 1


def test_the_attackers_start_at_the_foot_and_the_holders_point_is_past_the_midline_on_the_top_band(lib, field):
    s = sg.slope_top_marginal()(16, False)
    la, lh = _side(s, 0)[0].layer, _side(s, 1)[0].layer
    ax, ay = _centroid(_placed(_side(s, 0)))
    px, py = s.point
    joining = []
    for i in range(int(lib._lib.om_terrain_slope_count(field))):
        sl = _Slope()
        assert lib._lib.om_terrain_slope_get(field, i, ctypes.byref(sl)) == 0
        if (sl.lower_band, sl.upper_band) == (la + 1, lh + 1):
            joining.append(sl)
    assert joining, "no slope of seed 11 joins band %d to band %d" % (la + 1, lh + 1)
    sl = min(joining, key=lambda t: math.hypot(t.x0 - ax, t.y0 - ay))
    assert math.hypot(sl.x0 - ax, sl.y0 - ay) <= FOOT_NEAR
    ux, uy = sl.x1 - sl.x0, sl.y1 - sl.y0
    along = lambda x, y: ((x - sl.x0) * ux + (y - sl.y0) * uy) / (ux * ux + uy * uy)
    assert along(px, py) >= along(sl.mx, sl.my) and lib.terrain_band_at(field, px, py) == lh + 1


@pytest.mark.parametrize("heads", [8, 16, 48])
def test_every_placed_unit_stands_on_walkable_ground_of_its_band_at_the_jitter_corners(lib, field, heads):
    """fight() shifts every unit by up to contract.SHIFT_MAX per axis; the four corners of that square are checked too."""
    s = sg.slope_top_marginal()(heads, False)
    for g in s.groups:
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            for dx, dy in CORNERS:
                assert lib.terrain_walkable_at(field, x + dx, y + dy) and lib.terrain_band_at(field, x + dx, y + dy) == g.layer + 1, \
                    "unit at (%.0f, %.0f) shifted by (%+.0f, %+.0f) is not walkable ground of band %d" % (x, y, dx, dy, g.layer + 1)


@pytest.mark.parametrize("heads", [8, 16, 48])
@pytest.mark.parametrize("seed", range(3))
def test_every_unit_spawns(seed, heads):
    spy = Spy()
    fight.fight(dataclasses.replace(_setup(sg.slope_top_marginal(), heads), max_ticks=1), seed, False, engine=spy)
    assert len(spy.ids[0]) + len(spy.ids[1]) == 16 + heads and 0 not in spy.ids[0] + spy.ids[1]


# ---------------------------------------------------------------- the eye-height control

@pytest.mark.parametrize("seed", SEEDS)
def test_the_holders_see_no_attacker_at_eye_25_and_50_and_all_at_100_and_200_on_the_first_tick(seed):
    """The marginal post: the same flip the engine-level control shows (not seen at 25 and 50, seen at 100 and 200), here for all
    16 attackers at their jittered start, read before the first step."""
    seen = {eye: _watch(sg.slope_top_marginal(), seed, **{EYE: eye})[0].seen[0] for eye in (25, 50, 100, 200)}
    assert seen == {25: 0, 50: 0, 100: 16, 200: 16}, seen


@pytest.mark.parametrize("seed", SEEDS)
def test_eye_height_50_against_100_changes_the_first_sight_tick_in_the_variant(seed):
    low, high = _watch(sg.slope_top_marginal(), seed, **{EYE: 50})[0], _watch(sg.slope_top_marginal(), seed, **{EYE: 100})[0]
    assert high.first_sight == 0 and low.first_sight is not None and low.first_sight > high.first_sight, (low.seen, high.seen)


@pytest.mark.parametrize("seed", SEEDS)
def test_negative_control_the_natural_scene_sees_all_at_both_eye_heights(seed):
    """What the variant exists for: the natural scene's first-sight reading does not depend on eye 50 against 100."""
    low, high = _watch(sg.slope_top(), seed, **{EYE: 50})[0], _watch(sg.slope_top(), seed, **{EYE: 100})[0]
    assert low.seen[0] == high.seen[0] == 16 and low.first_sight == high.first_sight == 0


@pytest.mark.parametrize("eye", [50, 100])
def test_the_variant_fight_still_ends_by_elimination(eye):
    r = _watch(sg.slope_top_marginal(), 1, **{EYE: eye})[1]
    assert r.outcome in ("side0", "side1") and min(r.survivors) == 0


def test_the_variant_does_not_list_eye_height_as_inert_and_the_natural_scene_does():
    assert SCENE in sg.INERT_KNOBS_BY_SCENE
    assert EYE not in sg.INERT_KNOBS_BY_SCENE[SCENE], "the variant exists to move eye height"
    assert EYE in sg.INERT_KNOBS, "the natural scene's eye height stays inert (INERT_KNOBS)"


# ================================================================ s1_slope_top_flyer: the flyer-seen multiplier control (R-005-11)
#
# Contract these tests fix for scripts/skilllab/ground/scenes_ground.py:
#   slope_top_flyer(size=16) -> build(enemy_heads, swap) -> Setup, the natural scene's shape (M1 on both sides in equal halves, the holders
#     on guard, the attackers on attack_move to Setup.point = the holders' placed mean, seed 11, canvas sg.CANVAS), with the Raider of
#     both sides a flyer (unit_types["Raider"] has no "movement": the engine default 0; the Vanguard stays "walking"), labels
#     scene "s1_slope_top_flyer", prefight "ok"; every Raider stands one layer or more above the ground it is over (group layer >
#     terrain_band_at - 1), because the engine applies the multiplier only to a flyer above the ground's layer; every placed unit stands
#     on walkable ground at the jitter corners; INERT_KNOBS_BY_SCENE["s1_slope_top_flyer"] does not list OM_TP_GROUND_FLYER_SEEN_MULT.
#   Observable: before the first step the holders see more of the attackers at multiplier 3 than at 1.25 (never fewer as it grows), and
#     at least one attacker Raider that they see stands farther from every holder than that Raider's own sensor radius.
# Hint for the builder (measured 2026-10-14, seed 11, canvas 12000; Raider sensor radius 800, Vanguard 700): the flyer is seen from
#   max(radii) x multiplier = 1000 to 2400 wu, so the attackers' Raiders must start between about 1800 and 2350 wu from the holders'
#   centre (9050, 3180) on walkable ground (the walkable band-2 ground east of the slope has such places, around (10450, 1350) and
#   (10550, 4350)), hovering at layer 2. The engine's routing check in scenes.preflight reads only the open cells of the group's own
#   layer, so a flyer standing over lower ground reads "unroutable" there: the scene is reachable only if preflight does not route a
#   mover whose unit type is not "walking" (a flyer needs no path). That is a change to scenes.py outside the L6 row as written: if it
#   is not wanted, this variant stays red (STOP-report to the Architect, 2026-10-19); do not widen preflight any other way.

MULT = "OM_TP_GROUND_FLYER_SEEN_MULT"
MULTS = (1.25, 1.5, 2, 3)
FLYER = "s1_slope_top_flyer"
RAIDER_SENSOR = 800.0                # test draft (2026-10-19): the Raider's sensor_radius in the engine


class _FlySpy(Spy):
    """Spy that also keeps each spawned unit's position and each type's movement kind, read just before the world is freed."""

    def __init__(self):
        super().__init__()
        self.at, self.type_of, self.kinds = {}, {}, {}

    def spawn(self, w, type_id, side, x, y, layer):
        u = super().spawn(w, type_id, side, x, y, layer)
        self.at[u], self.type_of[u] = (x, y), type_id
        return u

    def free_world(self, w):
        for tid in set(self.type_of.values()):
            self.kinds[tid] = self.movement_kind(w, tid)
        super().free_world(w)


def _fly_watch(build, seed, **settings):
    spy = _FlySpy()
    result = fight.fight(_setup(build, **settings), seed, False, engine=spy)
    return spy, result


def test_flyer_labels_name_the_variant_and_the_preflight_is_ok(lib):
    build = sg.slope_top_flyer()
    s = build(16, False)
    assert build.labels["scene"] == FLYER and build.labels["prefight"] == "ok"
    assert scenes.preflight(s, lib) == "ok"
    assert s.terrain.field_seed == sg.SEED and s.terrain.canvas == (sg.CANVAS, sg.CANVAS)


def test_flyer_build_is_deterministic_and_swap_does_not_change_the_setup():
    build = sg.slope_top_flyer()
    assert build(16, False) == build(16, False) == build(16, True)


@pytest.mark.parametrize("size,heads", [(16, 16), (24, 12), (16, 48), (16, 8)])
def test_flyer_both_sides_field_the_m1_mix_in_equal_halves(size, heads):
    s = sg.slope_top_flyer(size)(heads, False)
    for side, n in ((0, size), (1, heads)):
        counts = {}
        for g in _side(s, side):
            counts[g.unit] = counts.get(g.unit, 0) + g.count
        assert set(counts) == {"Vanguard", "Raider"} and sum(counts.values()) == n and abs(counts["Vanguard"] - counts["Raider"]) <= 1, counts


def test_flyer_orders_and_point_follow_the_natural_scene():
    s = sg.slope_top_flyer()(16, False)
    assert {g.order for g in _side(s, 1)} == {"guard"} and {g.order for g in _side(s, 0)} == {"attack_move"}
    hx, hy = _centroid(_placed(_side(s, 1)))
    assert s.point == pytest.approx((hx, hy), abs=1e-6)


def test_the_raider_is_a_flyer_on_both_sides_and_the_vanguard_walks():
    s = sg.slope_top_flyer()(16, False)
    assert s.unit_types["Vanguard"].get("movement") == "walking" and s.unit_types["Raider"].get("movement") != "walking"
    spy = _FlySpy()
    fight.fight(dataclasses.replace(s, max_ticks=1), 1, False, engine=spy)
    kinds = sorted(set(spy.kinds.values()))
    assert kinds == [0, 1], kinds                              # one flying type (the Raider), one walking type (the Vanguard)
    assert {spy.kinds[spy.type_of[u]] for u in spy.ids[0]} == {0, 1} == {spy.kinds[spy.type_of[u]] for u in spy.ids[1]}


@pytest.mark.parametrize("heads", [8, 16, 48])
def test_flyer_every_raider_hovers_above_the_ground_it_is_over(lib, field, heads):
    """R-005-11 applies to a flyer above the ground's layer; the multiplier does nothing for a Raider at or below it."""
    s = sg.slope_top_flyer()(heads, False)
    raiders = [g for g in s.groups if g.unit == "Raider"]
    assert len(raiders) >= 2
    for g in raiders:
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            assert g.layer > lib.terrain_band_at(field, x, y) - 1, "Raider at (%.0f, %.0f) layer %d is not above its ground" % (x, y, g.layer)


@pytest.mark.parametrize("heads", [8, 16, 48])
def test_flyer_every_placed_unit_stands_on_walkable_ground_at_the_jitter_corners(lib, field, heads):
    s = sg.slope_top_flyer()(heads, False)
    for g in s.groups:
        for x, y in formations.place(g.formation, g.count, g.x, g.y, g.facing_deg, g.params):
            for dx, dy in CORNERS:
                assert lib.terrain_walkable_at(field, x + dx, y + dy), \
                    "unit at (%.0f, %.0f) shifted by (%+.0f, %+.0f) is not walkable ground" % (x, y, dx, dy)


@pytest.mark.parametrize("heads", [8, 16, 48])
@pytest.mark.parametrize("seed", range(3))
def test_flyer_every_unit_spawns(seed, heads):
    spy = Spy()
    fight.fight(dataclasses.replace(_setup(sg.slope_top_flyer(), heads), max_ticks=1), seed, False, engine=spy)
    assert len(spy.ids[0]) + len(spy.ids[1]) == 16 + heads and 0 not in spy.ids[0] + spy.ids[1]


@pytest.mark.parametrize("seed", SEEDS)
def test_the_flyer_multiplier_changes_how_many_attackers_the_holders_see_on_the_first_tick(seed):
    seen = [_fly_watch(sg.slope_top_flyer(), seed, **{MULT: m})[0].seen[0] for m in MULTS]
    assert seen == sorted(seen) and seen[-1] > seen[0], dict(zip(MULTS, seen))


@pytest.mark.parametrize("seed", SEEDS)
def test_a_flyer_is_seen_from_farther_than_it_sees(seed):
    """At multiplier 3, some attacker Raider is seen by the holders from beyond its own sensor radius (so it cannot see them back)."""
    spy = _FlySpy()
    s = _setup(sg.slope_top_flyer(), **{MULT: 3})
    holders_seen = {}
    real_step = spy.step

    def step(w):
        if spy.tick == 0:
            holders_seen.update({u: True for u in spy.seen_by_sight(w, 1, spy.ids[0])})
        return real_step(w)
    spy.step = step
    fight.fight(dataclasses.replace(s, max_ticks=2), seed, False, engine=spy)
    holder_pos = [spy.at[u] for u in spy.ids[1]]
    raiders = [u for u in spy.ids[0] if spy.kinds[spy.type_of[u]] == 0]
    far = [u for u in raiders if holders_seen.get(u) and min(math.dist(spy.at[u], h) for h in holder_pos) > RAIDER_SENSOR]
    assert far, "no attacker Raider is seen from beyond %.0f wu" % RAIDER_SENSOR


@pytest.mark.parametrize("seed", SEEDS)
def test_negative_control_the_natural_scene_is_blind_to_the_flyer_multiplier(seed):
    a, b = (_fly_watch(sg.slope_top(), seed, **{MULT: m})[0].seen[0] for m in (1.25, 3))
    assert a == b == 16


def test_the_flyer_fight_still_ends_by_elimination():
    r = _fly_watch(sg.slope_top_flyer(), 1)[1]
    assert r.outcome in ("side0", "side1") and min(r.survivors) == 0


def test_the_flyer_scene_does_not_list_the_multiplier_as_inert():
    assert FLYER in sg.INERT_KNOBS_BY_SCENE
    assert MULT not in sg.INERT_KNOBS_BY_SCENE[FLYER], "the variant exists to move the flyer multiplier"
    assert MULT in sg.INERT_KNOBS, "the natural scene's multiplier stays inert (INERT_KNOBS)"
