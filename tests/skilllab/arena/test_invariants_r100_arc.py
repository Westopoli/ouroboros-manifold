# Rule pins: R-091-15, R-100-04 (lab harness story H-091, lab stage 5, piece L2)
"""LAB stage 5, piece L2 (story H-091), R-091-15: the arc check, a lab check that no shot leaves outside the arc (E-13 R-100-04).

  R-091-15  The arc check (`scripts/skilllab/invariants_r100.py`, a new file, not registered in the checker's rule list) fails a fight when a unit fired on a tick when its target was
            outside its arc (unit, target, tick, angle named), and passes a fight where every shot is inside. Planted fights prove both.

THE API THIS FILE PINS (the story names the file and what the check says, not the function; the test writer's pick, reported; the lab builder builds to it):
    scripts/skilllab/invariants_r100.py (a new file)
        check_arc(doc) -> list of violations, empty when the fight passes. `doc` is an every-tick facing-on fight document; the arc is `doc["stage5"]["arc_deg"]`. For every entry of every
        frame's `hits` (a shot: attacker `a`, victim `v`, tick T) it takes the angle between the attacker's facing at the START of tick T (its row in frame T-1: csrc/unit.c
        om_tac_in_arc reads the facing the unit had when the tick began, as tests/csim/test_E13_R100_04_firing_arc.py does) and the direction from the attacker to the victim on the positions
        of frame T, and reports a shot whose angle is more than half the arc (a target at exactly half the arc is inside, R-091-06, to the file's rounding). One violation per such shot, in
        (tick, unit) order, each {"rule": "R-100-04", "tick": T, "unit": a, "target": v, "angle_deg": the angle, "detail": a sentence naming the unit, the target, the tick and the angle}.
    scripts/skilllab/invariants.py is NOT changed: its RULES tuple (the checker's rule list) does not gain the rule.
Not tested, the story does not say: a file that is not every tick, a facing-off file (no `stage5`), the tolerance at the edge beyond 'exactly half is inside'.

Planted fights (h091_fixtures.planted_doc, frames at ticks 0 to 4, units standing still but for unit 7's facing, hits placed by tick):
    unit 1 (A) at (0, 0) facing 0.0, victim 2 at (100, 100): 45.0 degrees, exactly half of arc 90      shot on tick 2
    unit 3 (A) at (0, 50) facing 1.0 rad, victim 4 at (200, 50): bearing 0, 57.30 degrees              shot on tick 3
    unit 5 (B) at (300, 0) facing pi, victim 6 at (200, 0): dead ahead, 0 degrees                      shot on tick 2
    unit 7 (A) at (0, 100) facing 0.9 rad on ticks 0 to 2 and 0.7 rad from tick 3 (it turned 0.2 rad), victim 8 at (200, 100): bearing 0; 51.57 degrees at the start of tick 3, 40.11 at its
    end                                                                                              shot on tick 3
So at arc 90 the shots of units 3 and 7 are outside (7 only by the facing it had at the start of the tick), at 60 also unit 1's, at 120 and 360 none.
Green today: the controls (the rule list). Red today: the missing module."""
import importlib
import math
import re

import pytest

import h091_fixtures as f9
from scripts.skilllab import invariants

SIDES = {1: "A", 2: "B", 3: "A", 4: "B", 5: "B", 6: "A", 7: "A", 8: "B"}
XY = {1: (0.0, 0.0), 2: (100.0, 100.0), 3: (0.0, 50.0), 4: (200.0, 50.0), 5: (300.0, 0.0), 6: (200.0, 0.0), 7: (0.0, 100.0), 8: (200.0, 100.0)}
FACING = {1: 0.0, 3: 1.0, 5: math.pi}
HITS = [(2, 1, 2, 90.0, "side"), (3, 3, 4, 90.0, "side"), (2, 5, 6, 0.0, "front"), (3, 7, 8, 90.0, "side")]


def facing(uid, t):
    return (0.9 if t <= 2 else 0.7) if uid == 7 else FACING.get(uid, 0.0)


def planted(arc=90, hits=HITS):
    return f9.planted_doc(SIDES, 4, hits, pos=lambda uid, t: XY[uid], facing=facing, arc_deg=arc)


def check(doc):
    try:
        mod = importlib.import_module("scripts.skilllab.invariants_r100")
    except ModuleNotFoundError as err:
        pytest.fail("L2 not built: %s" % err)
    return mod.check_arc(doc)


def test_control_the_arc_rule_is_not_in_the_checker_s_rule_list():
    """R-091-15 CONTROL (green today, must stay green): "not registered in the checker's rule list": `scripts/skilllab/invariants.RULES` is the thirteen rules of Round 6 and has no R-100-04."""
    assert len(invariants.RULES) == 13 and "R-100-04" not in invariants.RULES


@pytest.mark.parametrize("arc,units", [(360, []), (120, []), (90, [3, 7]), (60, [1, 3, 7])])
def test_R_091_15_planted_fight_names_every_shot_outside_the_arc(arc, units):
    """R-091-15: "fails a fight when a unit fired on a tick when its target was outside its arc ... passes a fight where every shot is inside". The planted fight (module docstring) at arc
    360 and 120 passes (empty list), at 90 names the shots of units 3 and 7, at 60 those of 1, 3 and 7 (45 degrees is outside a half arc of 30); unit 5's shot (dead ahead) never."""
    got = check(planted(arc))
    assert [v["unit"] for v in got] == units, got


def test_R_091_15_a_violation_names_unit_target_tick_and_angle():
    """R-091-15: "(unit, target, tick, angle named)": at arc 90 the violations are (tick 3, unit 3, target 4, 57.30 degrees) and (tick 3, unit 7, target 8, 51.57 degrees: the facing it
    had at the start of the tick, 0.9 rad, not the 0.7 rad it ended it with), each carrying the rule R-100-04 and a `detail` sentence that names the unit, the target, the tick and the angle."""
    got = check(planted(90))
    assert [(v["tick"], v["unit"], v["target"]) for v in got] == [(3, 3, 4), (3, 7, 8)]
    assert [v["rule"] for v in got] == ["R-100-04", "R-100-04"]
    assert [v["angle_deg"] for v in got] == pytest.approx([math.degrees(1.0), math.degrees(0.9)], abs=0.01)
    for v in got:
        words = re.findall(r"\d+(?:\.\d+)?", v["detail"])
        assert all(str(n) in words for n in (v["unit"], v["target"], v["tick"])) and any(abs(float(w) - v["angle_deg"]) <= 0.5 for w in words), v["detail"]


def test_R_091_15_a_shot_at_exactly_half_the_arc_passes():
    """R-091-15 with R-091-06: "a target at exactly half the arc is inside": the planted fight with only unit 1's shot (45.0 degrees off, arc 90) and unit 5's (0 degrees) passes."""
    assert check(planted(90, [HITS[0], HITS[2]])) == []


def test_R_091_15_a_fight_with_no_shot_passes():
    """R-091-15: a fight with no `hits` entry has nothing outside the arc: an empty list (the planted units standing still)."""
    assert check(planted(90, [])) == []


@pytest.fixture(scope="module")
def north_runs(tmp_path_factory):
    return {arc: f9.closeup_doc(f9.flank_layout("L-9551", "north"), tmp_path_factory.mktemp("arc%d" % arc), 1, "--facing", "on", "--arc-deg", str(arc)) for arc in (90, 360)}


def north_doc(runs, arc):
    proc, doc = runs[arc]
    if proc.returncode != 0 or doc is None:
        pytest.fail("closeup --facing on --arc-deg %d: exit %s, stderr tail %r" % (arc, proc.returncode, proc.stderr[-300:]))
    return doc


def test_R_091_15_a_real_fight_with_the_arc_at_90_has_no_shot_outside_it(north_runs):
    """R-091-15, one real fight (the north FLANK scene, facing on, `--arc-deg 90`, every tick): every shot of the fight is inside the arc; the fight has shots (over a hundred) and the check
    ran over them. (With R-091-01 this is the arc working inside the lab's fight.)"""
    doc = north_doc(north_runs, 90)
    assert len(f9.hit_list(doc)) > 100
    assert check(doc) == []


def test_R_091_15_a_real_fight_with_the_arc_at_360_fails_the_check_at_90(north_runs):
    """R-091-15: the same fight with the arc at 360 (the holders shoot north at once, facing east: 90 degrees off) judged against an arc of 90 (the document's `stage5.arc_deg` set to 90)
    fails: at least 8 shots are named, each with an angle over 45, the earliest by a holder (ids 1 to 8, which fire north at the first volley) at a tick of the fight; the arc-360 fight is
    accepted against 360."""
    wide = north_doc(north_runs, 360)
    got = check(dict(wide, stage5=dict(wide["stage5"], arc_deg=90)))
    assert len(got) >= 8 and all(v["angle_deg"] > 45.0 for v in got) and 1 <= got[0]["unit"] <= 8, got[:3]
    assert check(wide) == []
