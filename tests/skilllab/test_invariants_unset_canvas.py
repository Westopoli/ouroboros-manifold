# Rule pins: R-207-07
"""Engine rules round 2, T6: R-207-07 on a canvas the lab never set.

R-207-07 (docs/bible/epics/E-13-movement-and-command.md): "Given a position, a destination or a collision push, When it is applied, Then the position is
clamped to the map, and a push is slid along a blocked cell and not into it."

THE DEFECT. A lab fight that sets no terrain has no map: fight.fight hands the checker `(inf, inf)` (fight.py: `canvas = ... else (float("inf"), float("inf"))`;
invariants.watch has the same default), the Monitor builds `Rules(inf, inf)`, and `_Checker.feed` still demands `0.0 <= x` and `0.0 <= y`. The lab spawns such
fights at negative coordinates (a blob is centred on its group's x, y plus a spread), so every unit trips R-207-07 on every tick. The checker's own docstring
(`watch`) says a canvas the lab never set is as wide as the world, "R-207-07 cannot fire". And "since the checker runs inside every lab fight", every
terrain-less lab fight is marked invalid.

WHAT THESE TESTS PIN
  1. unset canvas (width = height = inf, what the Monitor passes): a unit at negative coordinates is no R-207-07 violation, and the report says R-207-07 is
     suspended, with a reason that names the unbounded canvas: a check that cannot judge says so, it does not pass in silence. (`Report.suspended` is
     {rule: reason}; the other entries hold a switch name, this one holds a sentence. Its exact wording is not pinned: it must be a non-empty string that says
     "canvas" and one of unbounded / unset / infinite / inf.)
  2. controls, green today and after: with a 4000 x 4000 canvas the four sides just outside are violations, the corners (0, 0) and (4000, 4000) are not (the
     far edge is inclusive: tests/skilllab/test_invariants.py plants x = 4000.0, y = 0.0 as inside), and R-207-07 is not suspended.
  3. real fight, terrain-less: blob_play(16) against 12 through scripts/skilllab/fight.py::fight, no R-207-07 violation, R-207-07 suspended, and the result
     is not invalid on account of it.
  4. real fight control: catalogue layout L-0039 (has terrain: a landscape preset canvas) through scripts/skilllab/arena/run.py::fight keeps R-207-07
     judged (the Monitor does not list it as suspended) and still flags a unit planted outside its canvas.

PREMISE, dumped 2026-11-11 on branch s/engine-rules-r2-t6 (87072cb5), fight.fight(blob_play(16)(12, False), seed 0, swap False), 13.9 s, 1819 ticks:
    result.invalid True, result.suspended {}, every one of the 30,536 violations of the Monitor is R-207-07 (Counter({'R-207-07': 30536}))
    first: {'rule': 'R-207-07', 'tick': 1, 'unit': 1, 'detail': 'at (-433.0, 3.1) outside the inf x inf canvas'}
"""
import ctypes
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight, invariants, plays  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

INF = float("inf")
CANVAS = 4000.0
L0039 = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "catalogue" / "L-0039.toml"
RULE = "R-207-07"
CANVAS_WORDS = ("unbounded", "unset", "infinite", "inf")


def row(x, y, side=0, layer=0, alive=True, hp=100.0, target=0, **extra):
    return dict({"x": float(x), "y": float(y), "layer": layer, "alive": alive, "hp": float(hp), "side": side, "target": target}, **extra)


def trace(*steps):
    """steps: one {unit id: row} per frame, frame 0 first (no shots)."""
    return [{"tick": n, "units": units, "fires": []} for n, units in enumerate(steps)]


def check_canvas(width, height, *positions):
    """R-207-07 only, over frames 0 and 1 of one unit (id 1) that stands at the first position, then at each following one."""
    tr = trace(*[{1: row(x, y)} for x, y in positions])
    return invariants.check(tr, invariants.Rules(width, height), only=[RULE])


def said(report):
    return [v for v in report.violations if v["rule"] == RULE]


# ------------------------------------------------------------------ 1. planted frames, canvas unset

@pytest.mark.parametrize("x,y", [(-433.0, 3.1), (100.0, -50.0), (-1.0, -1.0)])
def test_R_207_07_a_unit_at_negative_coordinates_on_an_unset_canvas_is_no_violation(x, y):
    """R-207-07 'the position is clamped to the map': there is no map when the lab set no terrain (canvas inf x inf, what the Monitor passes), so nothing can be
    outside it. Red today: tick 1 reports 'at (-433.0, 3.1) outside the inf x inf canvas'."""
    rep = check_canvas(INF, INF, (100.0, 100.0), (x, y))
    assert said(rep) == [] and rep.invalid is False, rep.violations


def test_R_207_07_an_unset_canvas_reports_the_check_suspended_and_why():
    """R-207-07: a check that cannot judge says so, it does not pass in silence. With the canvas unset (inf x inf) the report's `suspended` holds R-207-07 with
    a reason that names the unbounded canvas. Red today: `suspended` is {}."""
    rep = check_canvas(INF, INF, (100.0, 100.0), (-433.0, 3.1))
    reason = rep.suspended.get(RULE)
    assert isinstance(reason, str) and "canvas" in reason.lower() and any(w in reason.lower() for w in CANVAS_WORDS), rep.suspended


def test_R_207_07_an_unset_canvas_reports_it_suspended_with_no_unit_outside_too():
    """R-207-07: the suspension is a property of the run, not of what the units did: a unit well inside still leaves R-207-07 suspended. Red today: `suspended` is {}."""
    rep = check_canvas(INF, INF, (100.0, 100.0), (200.0, 200.0))
    assert RULE in rep.suspended and said(rep) == []


# ------------------------------------------------------------------ 2. planted frames, controls (green today and after)

@pytest.mark.parametrize("x,y", [(-1.0, 100.0), (100.0, -1.0), (CANVAS + 1, 100.0), (100.0, CANVAS + 1)])
def test_R_207_07_control_a_unit_just_outside_a_4000_canvas_is_a_violation(x, y):
    """R-207-07 control (green today): on a 4000 x 4000 canvas a unit one wu past an edge is flagged, once, at tick 1."""
    rep = check_canvas(CANVAS, CANVAS, (100.0, 100.0), (x, y))
    got = said(rep)
    assert [(v["tick"], v["unit"]) for v in got] == [(1, 1)] and rep.invalid is True, rep.violations


@pytest.mark.parametrize("x,y", [(0.0, 0.0), (CANVAS, CANVAS)])
def test_R_207_07_control_a_unit_on_the_edge_of_a_4000_canvas_is_not_a_violation(x, y):
    """R-207-07 control (green today): the corners (0, 0) and (4000, 4000) are on the map (both edges inclusive, as tests/skilllab/test_invariants.py pins for
    x = 4000, y = 0)."""
    rep = check_canvas(CANVAS, CANVAS, (100.0, 100.0), (x, y))
    assert said(rep) == [] and rep.invalid is False, rep.violations


def test_R_207_07_control_a_set_canvas_does_not_suspend_the_check():
    """R-207-07 control (green today): with a 4000 x 4000 canvas R-207-07 is judged, not suspended."""
    rep = check_canvas(CANVAS, CANVAS, (100.0, 100.0), (200.0, 200.0))
    assert RULE not in rep.suspended


# ------------------------------------------------------------------ 3. real fight, no terrain

@pytest.fixture(scope="module")
def blob_fight():
    """blob_play(16) against 12 through fight.fight, no terrain (Setup.terrain is None, the canvas is inf x inf). The Monitor is kept (a spy on
    invariants.watch) because FightResult.violations holds only the first 20; the monitor holds all of them."""
    seen, real = [], invariants.watch

    def spy(*args, **kw):
        mon = real(*args, **kw)
        seen.append(mon)
        return mon

    invariants.watch = spy
    try:
        setup = plays.blob_play(16)(12, False)
        result = fight.fight(setup, 0, False)
    finally:
        invariants.watch = real
    return setup, result, seen[0]


def test_R_207_07_control_the_blob_fight_is_terrain_less_and_spawns_below_zero(blob_fight):
    """Premise (green today): the setup sets no terrain, the checker got an unbounded canvas, and at least one unit spawned at a negative x or y (the first
    report is at (-433.0, 3.1) at tick 1)."""
    setup, result, mon = blob_fight
    assert setup.terrain is None
    assert (mon._chk.rules.width, mon._chk.rules.height) == (INF, INF)
    assert result.ticks > 0 and mon._frame["units"]


def test_R_207_07_a_terrain_less_blob_fight_has_no_R_207_07_violation(blob_fight):
    """R-207-07: no unit is outside a map that does not exist. Red today: 30,536 violations, every one R-207-07, the first 'tick 1, unit 1, at (-433.0, 3.1)
    outside the inf x inf canvas'."""
    _, result, mon = blob_fight
    got = [v for v in mon.violations if v["rule"] == RULE]
    assert got == [], "%d R-207-07 violations, the first %r" % (len(got), got[0])
    assert not [v for v in result.violations if v["rule"] == RULE]


def test_R_207_07_the_terrain_less_blob_fight_result_says_the_check_is_suspended(blob_fight):
    """R-207-07: FightResult.suspended names R-207-07 with a reason that names the unbounded canvas (a check that cannot judge says so). Red today: {}."""
    _, result, _ = blob_fight
    reason = result.suspended.get(RULE)
    assert isinstance(reason, str) and "canvas" in reason.lower() and any(w in reason.lower() for w in CANVAS_WORDS), result.suspended


def test_R_207_07_the_terrain_less_blob_fight_is_not_invalid_on_account_of_R_207_07(blob_fight):
    """R-207-07: the fight is not invalid because of R-207-07. Other rules may still flag it; this pins that R-207-07 is not the reason: every violation the
    result carries (and every one the Monitor found) is of some other rule. Red today: the result is invalid and all of it is R-207-07."""
    _, result, mon = blob_fight
    assert RULE not in {v["rule"] for v in mon.violations}
    assert RULE not in {v["rule"] for v in result.violations}
    if result.invalid:
        assert {v["rule"] for v in mon.violations} - {RULE}, "invalid with nothing but R-207-07 to say so"


# ------------------------------------------------------------------ 4. real fight control, with terrain

def _layout():
    with open(L0039, "rb") as f:
        return tomllib.load(f)


def _spy_monitor(monkeypatch):
    seen, real = [], invariants.Monitor

    class Spy(real):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            seen.append(self)

    monkeypatch.setattr(invariants, "Monitor", Spy)
    return seen


def test_R_207_07_control_a_catalogue_layout_with_terrain_keeps_the_check_judged(monkeypatch):
    """R-207-07 control (green today and after): L-0039 (a landscape with terrain, so a canvas) through arena/run.py::fight: the Monitor's canvas is finite and
    R-207-07 is not among its suspended rules; it ran for the 2 simulated seconds asked."""
    seen = _spy_monitor(monkeypatch)
    _, last, _, _ = run.fight(_layout(), 1, "on", 2)
    mon = seen[0]
    assert RULE not in mon.suspended, mon.suspended
    assert 0 < mon._chk.rules.width < INF and 0 < mon._chk.rules.height < INF and last > 0


def test_R_207_07_control_a_unit_planted_outside_the_canvas_of_L_0039_is_still_flagged(monkeypatch):
    """R-207-07 control (green today and after): a wrapper of Engine.step puts one unit at x = -50 after step 3 (om_unit_set_pos, as
    tests/skilllab/arena/test_invariants_wiring.py plants its faults); the Monitor of the terrain fight reports R-207-07 for it at tick 3."""
    real, count = Engine.step, {}
    planted = {}

    def step(self, w):
        real(self, w)
        count[w.value] = count.get(w.value, 0) + 1
        if count[w.value] == 3:
            lib = self._lib
            lib.om_unit_set_pos.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
            u = sorted(self._own[(w.value, 0)])[0]
            lib.om_unit_set_pos(w, u, -50.0, 100.0)
            planted["unit"] = u

    monkeypatch.setattr(Engine, "step", step)
    seen = _spy_monitor(monkeypatch)
    run.fight(_layout(), 1, "on", 2)
    got = [v for v in seen[0].violations if v["rule"] == RULE]
    assert ("unit" in planted) and any(v["tick"] == 3 and v["unit"] == planted["unit"] for v in got), (planted, seen[0].violations[:3])
