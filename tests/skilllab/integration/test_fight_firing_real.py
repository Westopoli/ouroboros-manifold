# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-24; 2026-10-14-skill-lab-rev2-spec.md::L1+L2
"""Fight-level firing cases against the real engine. OWNED BY L2 (LAB-REV2-L2): fight.py and contract.py are its files.

GREEN ONLY ONCE L1 AND L2 LAND TOGETHER. The old AC-24 cases and the 16 v 16 control read the fight's own `firing`
series, so they go through fight.fight and the new firing.py seam (count_able(engine, w, units0, units1, arc_deg)),
which the current fight.py calls with the old signature; the two rev 2 wiring cases (weighted_unit_seconds always
populated, Setup.states giving (tick, unit, code) rows) need L2's contract. The count itself, the type weight, the
codes and the parity check are tested without a fight loop in test_firing_real.py (L1).

Side 0: three units in a row, A, B, C along +x. Side 1: one enemy E behind A on the -x side.
Distances from E, as fractions of the Vanguard attack range R: A 0.3, B 0.7, C 1.2.
Replicate shifts are at most 10 world units per axis, far inside every margin (R is read from
the engine, so no position is a magic number).
"""
import ctypes
import dataclasses
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, fight  # noqa: E402
from scripts.skilllab.contract import Group, Setup  # noqa: E402

UNIT = "Vanguard"
BASE_X, BASE_Y = 400.0, 400.0   # keeps every point positive
_SETUP_FIELDS = {f.name for f in dataclasses.fields(Setup)}


def make_setup(**kw):
    """Setup(**kw), plus the L2 field `point` (the shared attack-move point) when the contract has it: these cases use
    idle groups or a mutual approach, so the value is the arena centre and decides nothing."""
    if "point" in _SETUP_FIELDS and "point" not in kw:
        kw["point"] = (BASE_X, BASE_Y)
    return Setup(**kw)


class _BlockerEngine:
    """Real Engine plus blockers added to each new world; every other call passes through."""

    def __init__(self, real, blockers):
        self._real = real
        self._blockers = blockers

    def __getattr__(self, name):
        return getattr(self._real, name)

    def new_world(self, *args, **kwargs):
        w = self._real.new_world(*args, **kwargs)
        for x, y, r in self._blockers:
            self._real.add_blocker(w, x, y, r)
        return w


@pytest.fixture(scope="module")
def real_engine():
    return engine.Engine()


@pytest.fixture(scope="module")
def reach(real_engine):
    w = real_engine.new_world(0)
    try:
        stats = real_engine.type_stats(w, real_engine.type_id(UNIT))
    finally:
        real_engine.free_world(w)
    return float(stats["attack_range"])


def _points(reach):
    a = (BASE_X, BASE_Y)
    b = (BASE_X + 0.4 * reach, BASE_Y)
    c = (BASE_X + 0.9 * reach, BASE_Y)
    e = (BASE_X - 0.3 * reach, BASE_Y)
    return a, b, c, e


def _setup(reach, **kw):
    a, b, c, e = _points(reach)
    side0 = Group(side=0, unit=UNIT, count=3, formation="points", x=BASE_X, y=BASE_Y,
                  facing_deg=0.0, layer=0, order="idle", params={"points": [a, b, c]})
    side1 = Group(side=1, unit=UNIT, count=1, formation="points", x=e[0], y=e[1],
                  facing_deg=180.0, layer=0, order="idle", params={"points": [e]})
    return make_setup(groups=(side0, side1), unit_types={}, abilities=False, max_ticks=10, sample_every=5, **kw)


def _tick0(result):
    tick, able0, able1 = result.firing[0]
    assert tick == 0
    return able0, able1


def test_two_of_three_within_reach_reads_2_and_1(real_engine, reach):
    """AC 24 base case, also the no-blocker count the blocker cases compare against."""
    result = fight.fight(_setup(reach), 0, False, engine=real_engine)
    assert _tick0(result) == (2, 1)
    assert result.first_contact_tick == 0


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_count_holds_across_replicate_shifts(real_engine, reach, seed):
    """AC 24 / AC 6: the replicate shift (<= 10 wu per axis) does not change the hand-built count."""
    assert _tick0(fight.fight(_setup(reach), seed, True, engine=real_engine)) == (2, 1)


def test_blocker_between_one_pair_removes_one_shooter_from_the_losing_side(real_engine, reach):
    """AC 24 blocker case: disc between A and B blocks the E-B line only. Side 0 loses B (2 -> 1);
    side 1 still fires through A, so its count is unchanged."""
    a, b, c, e = _points(reach)
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=real_engine)) == (2, 1)   # no-blocker count first
    blocker = ((a[0] + b[0]) / 2.0, BASE_Y, 0.08 * reach)
    blocked = _BlockerEngine(real_engine, [blocker])
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=blocked)) == (1, 1)


def test_blocker_on_every_line_to_the_enemy_removes_the_enemys_shot_too(real_engine, reach):
    """AC 24 blocker case: disc between E and A lies on both E-A and E-B. Side 0 drops 2 -> 0,
    side 1 drops 1 -> 0 (it loses its only pair)."""
    a, b, c, e = _points(reach)
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=real_engine)) == (2, 1)   # no-blocker count first
    blocker = ((a[0] + e[0]) / 2.0, BASE_Y, 0.07 * reach)
    blocked = _BlockerEngine(real_engine, [blocker])
    assert _tick0(fight.fight(_setup(reach), 0, False, engine=blocked)) == (0, 0)


def test_control_same_layer_16_v_16_blob_reads_16_16_on_the_lab_series(real_engine):
    """Positive control (green before and after L1): two Vanguard blobs of 16 on one layer, inside every range and
    sensor, read 16 and 16 on the fight's own firing series at tick 0, as they do today."""
    blob = lambda side, x, f: Group(side=side, unit=UNIT, count=16, formation="blob", x=x, y=1000.0, facing_deg=f,
                                    layer=0, order="idle", params={"radius": 60.0})
    setup = make_setup(groups=(blob(0, 1000.0, 0.0), blob(1, 1150.0, 180.0)), unit_types={}, max_ticks=10,
                       sample_every=5)
    assert fight.fight(setup, 0, False, engine=real_engine).firing[0] == (0, 16, 16)


# ---------------------------------------------------------------- rev 2 wiring (L2): weighted seconds and state codes

def _lines(**kw):
    """3 v 3 Vanguard lines 180 wu apart on one layer, both sides attack-moving at each other, 60 ticks."""
    g0 = Group(side=0, unit=UNIT, count=3, formation="line", x=300.0, y=400.0, facing_deg=0.0, layer=0,
               order="attack_move", params={"spacing": 30.0})
    g1 = Group(side=1, unit=UNIT, count=3, formation="line", x=480.0, y=400.0, facing_deg=180.0, layer=0,
               order="attack_move", params={"spacing": 30.0})
    return make_setup(groups=(g0, g1), unit_types={}, max_ticks=60, sample_every=5, **kw)


def _line_line_multiplier(lib):
    w = lib.new_world(0)
    try:
        c = lib.type_stats(w, lib.type_id(UNIT))["category"]
        fn = lib._lib.om_tactical_category_multiplier
        fn.argtypes, fn.restype = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int], ctypes.c_double
        return float(fn(w, c, c))
    finally:
        lib.free_world(w)


def test_there_is_no_weighted_flag_and_no_order_ends(real_engine):
    """L2 contract: Setup.weighted is gone (the weighted count is always taken) and so is FightResult.order_ends."""
    assert "weighted" not in _SETUP_FIELDS
    from scripts.skilllab.contract import FightResult
    names = {f.name for f in dataclasses.fields(FightResult)}
    assert "weighted" not in names and "order_ends" not in names
    assert {"weighted_unit_seconds", "weighted_window", "states"} <= names


def test_weighted_unit_seconds_is_always_populated_and_is_the_multiplier_times_the_count(real_engine):
    """L2 contract: with no flag set, weighted_unit_seconds is a pair of floats. In a one-type fight every able unit
    weighs the same multiplier m(line, line), so the weighted seconds are exactly m times firing_unit_seconds (the
    count is positive: asserted), on both sides."""
    r = fight.fight(_lines(), 0, False, engine=real_engine)
    m = _line_line_multiplier(real_engine)
    assert len(r.weighted_unit_seconds) == 2 and all(type(v) is float for v in r.weighted_unit_seconds)
    assert min(r.firing_unit_seconds) > 0
    assert r.weighted_unit_seconds == pytest.approx(tuple(m * v for v in r.firing_unit_seconds))
    assert fight.fight(_lines(), 0, False, engine=real_engine).weighted_unit_seconds == r.weighted_unit_seconds


def test_states_off_by_default_and_on_gives_tick_unit_code_rows(real_engine):
    """L2 contract: Setup.states stays an opt-in. Off: no rows. On: (tick, unit, code) int rows ordered by tick then unit
    id, starting at tick 0 with all six units, every code in -1..5, at least one 0 (a shot is possible) and none
    reading -1 while both sides live; the same fight twice gives the same rows."""
    assert not fight.fight(_lines(), 1, False, engine=real_engine).states
    r = fight.fight(_lines(states=True), 1, False, engine=real_engine)
    assert r.states and all(len(row) == 3 and all(type(v) is int for v in row) for row in r.states)
    assert [row[:2] for row in r.states] == sorted(row[:2] for row in r.states)
    assert [u for t, u, _ in r.states if t == 0] == [1, 2, 3, 4, 5, 6]
    assert all(-1 <= c <= 5 for _, _, c in r.states) and any(c == 0 for _, _, c in r.states)
    assert fight.fight(_lines(states=True), 1, False, engine=real_engine).states == r.states


def test_state_zero_codes_equal_the_firing_series_at_every_sample(real_engine):
    """The zero codes are the count: at each sampled tick the side-0 units (ids 1 to 3) with code 0 number the series'
    able0 and the side-1 units (4 to 6) its able1."""
    r = fight.fight(_lines(states=True), 1, False, engine=real_engine)
    for tick, able0, able1 in r.firing:
        rows = [(u, c) for t, u, c in r.states if t == tick]
        assert rows, "no state rows at the sampled tick %d" % tick
        assert (sum(1 for u, c in rows if u <= 3 and c == 0), sum(1 for u, c in rows if u > 3 and c == 0)) == (able0, able1)
