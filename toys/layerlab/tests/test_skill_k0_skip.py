"""Rung K0 addendum tests (SPEC.md section 14.1): unbuildable ratios in rstar, and the symmetric controls.

Red until the package layerlab/skill/ exists (ModuleNotFoundError on the imports below).

Layout: (1) the solver SKIPS a ratio whose `build` raises ValueError (scripted runner, as in
test_skill_k0.py: `layerlab.skill.rstar.run_fights` is replaced, so no C fights), (2) the controls'
builders: both sides attack-move, spacing, arena, the unit cap, the planted range advantage.

Conventions the tests fix where SPEC 14.1 is silent (reported to the Architect):
  * `skipped_ratios` is compared as a sorted list; a ratio is skipped when `build` raises for EITHER
    label (both labels must exist at every point), and the solver stops calling the runner for it.
  * `scan_max` is the largest ratio in `points` (what actually ran).
  * A refinement point is a ratio the solver chose itself; if `build` raises for one, it is skipped the
    same way (not exercised here: every planted bracket lies below the build limit).
  * `short_scan` is asserted as a flag only; whether `valid` changes is not tested.

Revised for SPEC 14.5 (test-defect fix, Architect-approved): the scripted `build` makes real group scenarios
(one raider group per side, counts from the ratio, as test_skill_k0r.py does) because `rstar` now reports the
cost ratio from the scenarios, and the scripted fight results carry alive_ticks, firing_ticks and heads. The
default `win_margin` is 0.02 and would move the planted crossing from 2.5 to about 2.4333; these tests are
about skipping, so the scripted `Script.run` passes `win_margin=0.0` unless a test gives its own.
"""
import copy
import importlib
import math

import pytest

from conftest import grp, make_scenario
from layerlab import ffi, scenario

rstarmod = importlib.import_module("layerlab.skill.rstar")
controls = importlib.import_module("layerlab.skill.controls")
RATIOS, rstar = rstarmod.RATIOS, rstarmod.rstar
mirror_build, advantage_build = controls.mirror_build, controls.advantage_build


# =========================================================================== (1) skipping in the solver


def base(r):
    """The planted skilled-side margin: linear through 0 at ratio 2.5, clipped to +-0.8."""
    return max(-0.8, min(0.8, (2.5 - r) * 0.3))


class FakeFight:
    """What a scripted run_fights returns: every field a FightResult carries (SPEC 14.5 item 3)."""

    def __init__(self, margin, outcome, heads):
        self.margin, self.raw_margin, self.outcome = margin, margin, outcome
        self.ticks, self.contact, self.survivors, self.error = 100, True, (1, 1), None
        self.first_contact_tick = 50
        self.alive_ticks, self.firing_ticks, self.heads = (100, 100), (50, 50), tuple(heads)

    def firing_per_head(self, label):
        return self.firing_ticks[label] / self.heads[label] if self.heads[label] else 0.0


class Script:
    """A scripted `run_fights` and a `build` that raises ValueError when `unbuildable(ratio, swap)`, else makes
    a REAL scenario dict with groups: 8 skilled raiders against round(8 * ratio) naive raiders, the skilled
    side on label B when swap is True. `run` passes `win_margin=0.0` unless the test gives one (see the
    module docstring).

    skilled(ratio, seed, swap) -> the SKILLED side's margin; the fight's own A-minus-B margin is that on
    label A (swap False) and its negative on label B (swap True)."""

    def __init__(self, monkeypatch, skilled, unbuildable):
        self.skilled, self.unbuildable = skilled, unbuildable
        self.seen = []            # (ratio, swap, seed) for every fight the solver asked for
        self.built = {}           # id(scenario) -> (scenario, snapshot, ratio, swap), to prove scenarios pass through untouched
        self.build_calls = []     # (ratio, swap) for every build call, raising ones included
        monkeypatch.setattr(rstarmod, "run_fights", self.run_fights)

    def build(self, ratio, swap):
        self.build_calls.append((ratio, swap))
        if self.unbuildable(ratio, swap):
            raise ValueError("ratio %g does not fit: units exceed LL_MAX_UNITS" % ratio)
        sk, nv = ("B", "A") if swap else ("A", "B")
        scn = make_scenario([grp(sk, "raider", 1000, 1000, 3, count=8),
                             grp(nv, "raider", 3000, 1000, 3, count=max(1, round(8 * ratio)))])
        scn["groups"].sort(key=lambda g: g["side"])
        self.built[id(scn)] = (scn, copy.deepcopy(scn), ratio, swap)
        return scn

    def run_fights(self, jobs, *args, **kwargs):
        out = []
        for scn, seed in jobs:
            keep, snapshot, r, sw = self.built[id(scn)]
            assert keep is scn and scn == snapshot, "scenario was altered"
            self.seen.append((r, sw, seed))
            m = self.skilled(r, seed, sw)
            m = -m if sw else m
            n_nv = max(1, round(8 * r))
            out.append(FakeFight(m, "win_A" if m > 0 else "win_B", (n_nv, 8) if sw else (8, n_nv)))
        return out

    def run(self, **kw):
        kw.setdefault("win_margin", 0.0)
        return rstar(self.build, **kw)

    def ratios_run(self):
        return {r for r, _, _ in self.seen}


def test_skipped_ratios_above_the_limit_are_skipped_and_the_crossing_is_still_found(monkeypatch):
    """SPEC 14.1 'Unbuildable ratios' (1): build raises ValueError above ratio 5; margin crosses 0 at 2.5.
    The solver does not raise; value within 0.05 of 2.5; skipped_ratios is exactly [6.0, 8.0] (2.9, 3.5,
    4.2 and 5.0 are buildable; 5.0 is not above 5); scan_max 5.0 (refinement stays inside (2.4, 2.9));
    fights are 2 labels x 2 seeds over the 13 scanned + 4 refined points that ran, none for the skipped
    ones; short_scan False because scan_max > 3."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r), lambda r, sw: r > 5.0)
    res = sc.run(refine=4)
    assert res.value == pytest.approx(2.5, abs=0.05)
    assert sorted(res.skipped_ratios) == [6.0, 8.0]
    assert res.scan_max == 5.0
    ratios = [p["ratio"] for p in res.points]
    assert ratios == sorted(ratios) and max(ratios) == 5.0 and len(ratios) == 13 + 4
    assert 6.0 not in ratios and 8.0 not in ratios
    assert res.fights == len(sc.seen) == 4 * 17
    assert res.short_scan is False
    assert res.above_scan is False and res.below_scan is False
    assert res.valid is True and res.monotonic is True


def test_nothing_skipped_when_every_ratio_builds(monkeypatch):
    """SPEC 14.1 (negative twin of (1)): the same curve with nothing unbuildable skips nothing, reaches 8.0
    and is not a short scan (so the skipping above is caused by the raising build and nothing else)."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r), lambda r, sw: False)
    res = sc.run(refine=4)
    assert list(res.skipped_ratios) == []
    assert res.scan_max == 8.0 and res.short_scan is False
    assert res.value == pytest.approx(2.5, abs=0.05)
    assert res.fights == len(sc.seen) == 4 * 19


def test_curve_still_positive_where_the_build_stops_is_a_short_scan(monkeypatch):
    """SPEC 14.1 (2): build raises above ratio 2.0 and the skilled side still wins at 2.0: above_scan True
    (only a statement about scan_max), value None, scan_max 2.0, short_scan True (the 3x scan was not
    reached; the callers leave it out of aggregates). Skipped are the 7 scanned ratios above 2.0; no
    refine point (no bracket); 8 ratios x 4 fights."""
    sc = Script(monkeypatch, lambda r, seed, sw: 0.5, lambda r, sw: r > 2.0)
    res = sc.run(refine=4)
    assert res.above_scan is True and res.value is None and res.below_scan is False
    assert res.scan_max == 2.0
    assert res.short_scan is True
    assert sorted(res.skipped_ratios) == [2.4, 2.9, 3.5, 4.2, 5.0, 6.0, 8.0]
    assert [p["ratio"] for p in res.points] == [0.5, 0.7, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0]
    assert res.fights == len(sc.seen) == 8 * 4
    assert max(sc.ratios_run()) == 2.0


def test_above_scan_past_three_is_not_a_short_scan(monkeypatch):
    """SPEC 14.1 (positive/negative twin of (2)): the skilled side wins everywhere up to the limit 5.0:
    above_scan True and value None as before, but scan_max 5.0 > 3 so short_scan is False."""
    sc = Script(monkeypatch, lambda r, seed, sw: 0.5, lambda r, sw: r > 5.0)
    res = sc.run(refine=4)
    assert res.above_scan is True and res.value is None
    assert res.scan_max == 5.0 and res.short_scan is False
    assert sorted(res.skipped_ratios) == [6.0, 8.0]


def test_a_ratio_that_raises_for_one_label_only_is_skipped_whole(monkeypatch):
    """SPEC 14.1 (3): only swap=True raises (above ratio 5): both labels must exist at every point, so the
    whole ratio is skipped: no fight of either label at 6.0 or 8.0 (the buildable label is not run alone),
    and the points that remain have all four fights (2 labels x 2 seeds)."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r), lambda r, sw: sw and r > 5.0)
    res = sc.run(refine=4)
    assert sorted(res.skipped_ratios) == [6.0, 8.0]
    assert res.scan_max == 5.0
    assert not {(r, sw) for r, sw, _ in sc.seen if r > 5.0}
    for r in (5.0, 4.2, 2.9):
        assert {(sw, seed) for rr, sw, seed in sc.seen if rr == r} == {(False, 0), (False, 1), (True, 0), (True, 1)}
    assert res.fights == len(sc.seen) == 4 * 17
    assert res.value == pytest.approx(2.5, abs=0.05)


def test_the_runner_is_never_called_for_a_skipped_ratio(monkeypatch):
    """SPEC 14.1 (4): `build` is asked about the ratios above 5 (positive control: the raising path is
    taken), yet the runner never sees a scenario for any of them, in any label or seed, and no scenario
    reaches it that was not built. Also with a seeds tuple of three."""
    sc = Script(monkeypatch, lambda r, seed, sw: base(r), lambda r, sw: r > 5.0)
    res = sc.run(refine=4, seeds=(0, 1, 2))
    assert {r for r, _ in sc.build_calls} >= {6.0, 8.0}, "premise: the solver does try the unbuildable ratios"
    assert sc.ratios_run() and max(sc.ratios_run()) <= 5.0
    assert sorted(res.skipped_ratios) == [6.0, 8.0]
    assert res.fights == len(sc.seen) == 17 * 2 * 3


# =========================================================================== (2) the controls' builders


def _spawns(scn):
    """(side, x, y) per spawned unit as the loader places them; raises if any spawn is outside the arena."""
    sc = scenario.to_c(scn)
    return [(sc.spawns[i].side, sc.spawns[i].x, sc.spawns[i].y) for i in range(sc.n_spawns)]


def _side(spawns, side):
    return [(x, y) for s, x, y in spawns if s == side]


def _min_gap(points):
    return min((math.hypot(ax - bx, ay - by)
                for i, (ax, ay) in enumerate(points) for bx, by in points[i + 1:]), default=math.inf)


@pytest.mark.parametrize("size", [8, 16])
@pytest.mark.parametrize("swap", [False, True])
def test_mirror_build_at_ratio_one_is_two_equal_advancing_forces(size, swap):
    """SPEC 14.1 mirror_build: at ratio 1.0 each side has exactly `size` raiders; every group of both
    sides is attack_move (none hold: a side that holds still against one that advances is no mirror);
    within a side no two units are closer than 50 (the line abreast in ranks); every spawn is inside the
    arena (to_c succeeds, which checks it)."""
    scn = mirror_build(size)(1.0, swap)
    assert scn["groups"], "no groups"
    assert {g["order"] for g in scn["groups"]} == {"attack_move"}
    assert {g["type"] for g in scn["groups"]} == {"raider"}
    spawns = _spawns(scn)
    for side in (0, 1):
        pts = _side(spawns, side)
        assert len(pts) == size, (side, len(pts))
        assert _min_gap(pts) >= 50.0 - 1e-3, (side, _min_gap(pts))
    assert len(spawns) == 2 * size and sorted({s for s, _, _ in spawns}) == [0, 1]


@pytest.mark.parametrize("swap", [False, True])
def test_mirror_build_skilled_force_is_the_fixed_one_and_the_label_follows_swap(swap):
    """SPEC 14.1 build(ratio, swap): the skilled force is fixed at `size`, the other is ratio times it.
    At ratio 2.0 and size 8, swap False gives side A 8 units and side B 16; swap True the reverse; both
    sides attack_move and keep the spacing at the bigger size too."""
    scn = mirror_build(8)(2.0, swap)
    spawns = _spawns(scn)
    n_a, n_b = len(_side(spawns, 0)), len(_side(spawns, 1))
    assert (n_a, n_b) == ((16, 8) if swap else (8, 16))
    assert {g["order"] for g in scn["groups"]} == {"attack_move"}
    assert _min_gap(_side(spawns, 0)) >= 50.0 - 1e-3 and _min_gap(_side(spawns, 1)) >= 50.0 - 1e-3


@pytest.mark.parametrize("swap", [False, True])
def test_mirror_build_16_hits_the_unit_cap_at_ratio_max_units_over_16(swap):
    """SPEC 14.1 'Unbuildable ratios' (cap 4096 since SPEC 16; was 128 and ratio 8): size 16 at ratio
    MAX_UNITS / 16 = 256 is 16 + 4096 units, above ffi.MAX_UNITS: build raises ValueError and the message
    names LL_MAX_UNITS (the count check runs before any arena check, so this is the unit cap and not an
    arena error). Positive controls: ratio 255 (16 + 4080 = MAX_UNITS exactly) still builds the scenario
    dict (the unit-cap check is the only one `build` makes), and so do ratios 7 (128 units) and 6 (112
    units), which the loader also takes."""
    size = 16
    over = ffi.MAX_UNITS // size
    build = mirror_build(size)
    with pytest.raises(ValueError, match="LL_MAX_UNITS"):
        build(float(over), swap)
    at_cap = build(float(over - 1), swap)
    assert sum(g["count"] for g in at_cap["groups"]) == ffi.MAX_UNITS
    for ratio, total in ((7.0, 128), (6.0, 112)):
        scn = build(ratio, swap)
        spawns = _spawns(scn)
        assert len(spawns) == total, (ratio, len(spawns))
        assert sorted((len(_side(spawns, 0)), len(_side(spawns, 1)))) == [16, total - 16]
        assert {g["order"] for g in scn["groups"]} == {"attack_move"}


@pytest.mark.parametrize("swap", [False, True])
def test_advantage_build_plants_the_range_on_the_skilled_side_and_both_attack(swap):
    """SPEC 14.1 advantage_build: at ratio 1.0 the skilled side (A when swap is False, B when True) has
    raiders of range 240, the other side 200; both sides attack_move; each side has 8 units."""
    scn = advantage_build(8)(1.0, swap)
    assert {g["order"] for g in scn["groups"]} == {"attack_move"}
    names = {"A": 0, "B": 1}
    ranges = {0: set(), 1: set()}
    for g in scn["groups"]:
        side = names.get(g["side"], g["side"])
        ranges[side].add(scn["types"][g["type"]]["range"])
    skilled, other = (1, 0) if swap else (0, 1)
    assert ranges[skilled] == {240.0}, ranges
    assert ranges[other] == {200.0}, ranges
    spawns = _spawns(scn)
    assert len(_side(spawns, 0)) == len(_side(spawns, 1)) == 8
