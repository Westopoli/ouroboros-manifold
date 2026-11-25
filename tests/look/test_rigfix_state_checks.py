"""look-judge-rig fixes, defects 7 and 8 (measurement 2026-11-24, real fight L-0039 seed 1, fixture tests/look/fixtures/l0039_s1.fight.json.gz: 2214 frames, `seen` lists dropped).
Spec piece 1 (state checks over a fight file): a unit inside a wall FAILs; frozen frames FAIL.

Defect 7: real fight files keep walls under `built_features[].boxes`, each {"x", "y", "w", "h"} (x, y the centre), here L-0039's three cover boxes (1900,1800,2000,1900)
(1900,2000,2000,2100) (1900,2200,2000,2300) as (x0, y0, x1, y1); `check_unit_in_wall` returned UNSURE "fight has no walls". The existing top-level `walls` [x0,y0,x1,y1] stays.
Defect 8: `check_frozen` compared only x, y, hp, alive, so a window where a unit fired or changed target (nothing moving) counted as identical. Pinned: a frame difference is
any difference in a unit record (fired, target, facing, ...); frozen is a run of frames identical in that sense longer than max_identical. In L-0039 the longest run of fully
identical frames is 19 (the sig-only run is 20, at tick 1927 and again at 2172): the tests pass max_identical explicitly; the window itself is Westley's (see the report).
"""
import copy
import gzip
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
L39 = ROOT / "tests" / "look" / "fixtures" / "l0039_s1.fight.json.gz"
BOXES = [(1900.0, 1800.0, 2000.0, 1900.0), (1900.0, 2000.0, 2000.0, 2100.0), (1900.0, 2200.0, 2000.0, 2300.0)]


@pytest.fixture(scope="module")
def l39():
    return json.loads(gzip.open(L39, "rt").read())


def unit(i, x, y, side="A", layer=0, **kw):
    u = {"id": i, "side": side, "role": "Bombard", "layer": layer, "x": x, "y": y, "hp": 100.0, "alive": True, "facing": 0.0, "fired": False, "target": None}
    u.update(kw)
    return u


def fight(frames, extra=None):
    d = {"schema": "om-fight-2", "seed": 1, "tick_rate": 20, "snapshot_every": 1, "orders": {}, "result": {}, "violations": [],
         "frames": [{"tick": t, "alive": [len(u), 0], "units": u} for t, u in enumerate(frames)]}
    d.update(extra or {})
    return d


def inside(u, b):
    return b[0] <= u["x"] <= b[2] and b[1] <= u["y"] <= b[3]


def test_control_l0039_premises_and_walls_are_found_independently(l39):
    """Premises dumped (green today): L-0039 has 2214 frames and one cover feature with the three boxes above (x, y centre, w = h = 100); an independent scan finds no living unit
    in any box (nearest 26.9 wu outside); the existing top-level `walls` form still FAILs a planted unit."""
    from scripts.look.state_checks import check_unit_in_wall
    assert len(l39["frames"]) == 2214
    f = l39["built_features"][0]
    assert f["kind"] == "cover" and [(b["x"] - b["w"] / 2, b["y"] - b["h"] / 2, b["x"] + b["w"] / 2, b["y"] + b["h"] / 2) for b in f["boxes"]] == BOXES
    assert not any(inside(u, b) for fr in l39["frames"] for u in fr["units"] if u["alive"] for b in BOXES)
    legacy = fight([[unit(1, 1950.0, 1850.0)] for _ in range(3)], {"walls": [list(BOXES[0])]})
    assert check_unit_in_wall(legacy)["verdict"] == "FAIL"


def test_walls_are_read_from_built_features_boxes_pass_on_l0039(l39):
    """Spec piece 1 "a unit inside a wall FAILs", piece 1 "nothing returns PASS on missing data": with the boxes read from built_features, L-0039 seed 1 (no unit inside, verified
    independently above) PASSes, not UNSURE 'fight has no walls'."""
    from scripts.look.state_checks import check_unit_in_wall
    r = check_unit_in_wall(l39)
    assert r["verdict"] == "PASS", r


def test_unit_planted_inside_a_real_box_fails(l39):
    """Spec piece 1 control "a unit inside a wall rect FAILs": unit 1 moved to the middle of the first cover box for frames 100..110 of the real fight FAILs, naming unit 1 and tick 100;
    the same unit planted there but dead does not FAIL."""
    from scripts.look.state_checks import check_unit_in_wall
    bad = copy.deepcopy(l39)
    for fr in bad["frames"][100:111]:
        u = next(v for v in fr["units"] if v["id"] == 1)
        u["x"], u["y"] = 1950.0, 1850.0
    r = check_unit_in_wall(bad)
    assert r["verdict"] == "FAIL" and r["tick"] == 100
    assert {h["unit"] for h in r["numbers"]["hits"]} == {1}
    for fr in bad["frames"][100:111]:
        next(v for v in fr["units"] if v["id"] == 1)["alive"] = False
    assert check_unit_in_wall(bad)["verdict"] == "PASS"


def test_small_fight_with_boxes_in_built_features(tmp_path):
    """Spec piece 1, same read on a hand-made fight: a centre-format box {"x": 200, "y": 200, "w": 100, "h": 100} (150..250) FAILs a unit at (250, 250) and PASSes a unit at (251, 250)."""
    from scripts.look.state_checks import check_unit_in_wall
    ft = {"built_features": [{"kind": "cover", "x": 200.0, "y": 200.0, "boxes": [{"x": 200.0, "y": 200.0, "w": 100.0, "h": 100.0}]}]}
    assert check_unit_in_wall(fight([[unit(1, 250.0, 250.0)]] * 4, ft))["verdict"] == "FAIL"
    assert check_unit_in_wall(fight([[unit(1, 251.0, 250.0)]] * 4, ft))["verdict"] == "PASS"


def test_control_identical_frames_are_frozen_and_moving_frames_are_not():
    """Positive control (spec piece 1, green today): twelve frames with every unit record identical FAIL at max_identical=5; a unit that moves each frame PASSes."""
    from scripts.look.state_checks import check_frozen
    assert check_frozen(fight([[unit(1, 5.0, 5.0), unit(2, 9.0, 9.0)] for _ in range(12)]), max_identical=5)["verdict"] == "FAIL"
    assert check_frozen(fight([[unit(1, 5.0 + t, 5.0)] for t in range(12)]), max_identical=5)["verdict"] == "PASS"


@pytest.mark.parametrize("field,values", [("fired", [False, True]), ("target", [None, 7]), ("facing", [0.0, 0.5])])
def test_a_fired_target_or_facing_change_with_nobody_moving_is_not_frozen(field, values):
    """Spec piece 1 "frozen frames FAIL": positions, hp and alive never change for twelve frames, but unit 2's `%s` alternates every frame: the frames differ, so not frozen
    (PASS at max_identical=5). Reloading units that stand still are not a frozen render."""
    from scripts.look.state_checks import check_frozen
    frames = [[unit(1, 5.0, 5.0), unit(2, 9.0, 9.0, **{field: values[t % 2]})] for t in range(12)]
    assert check_frozen(fight(frames), max_identical=5)["verdict"] == "PASS"


def test_one_state_change_breaks_the_identical_run_at_the_boundary():
    """Spec piece 1: a single `fired` frame at tick 6 of twelve otherwise identical frames splits the run into 6 (ticks 0..5), 1 and 5 (ticks 7..11): FAIL at max_identical=5
    (the run of 6 is frozen), PASS at max_identical=6. Today the sig ignores `fired` and sees one run of 12."""
    from scripts.look.state_checks import check_frozen
    frames = [[unit(1, 5.0, 5.0), unit(2, 9.0, 9.0, fired=(t == 6))] for t in range(12)]
    assert check_frozen(fight(frames), max_identical=5)["verdict"] == "FAIL"
    assert check_frozen(fight(frames), max_identical=6)["verdict"] == "PASS"


def test_control_l0039_longest_sig_run_is_20(l39):
    """Premise (green today): at max_identical=20 the real L-0039 does not FAIL: the longest run that ignores `fired` and `target` is 20 frames (ticks 1908..1927)."""
    from scripts.look.state_checks import check_frozen
    assert check_frozen(l39, max_identical=20)["verdict"] == "PASS"


def test_l0039_the_fired_frame_at_tick_1908_breaks_the_20_run(l39):
    """Spec piece 1 on the real fight: unit 5 (Interceptor) fires at tick 1908, the first frame of the 20-frame window in which nothing moves; the frames 1908 and 1909 differ, so the
    longest fully identical run in L-0039 is 19: at max_identical=19 the real fight is not frozen (PASS); one frame below, at 18, it is still frozen (FAIL), tick 1927 or 2172."""
    from scripts.look.state_checks import check_frozen
    assert check_frozen(l39, max_identical=19)["verdict"] == "PASS"
    r = check_frozen(l39, max_identical=18)
    assert r["verdict"] == "FAIL" and r["numbers"]["longest_identical"] == 19
