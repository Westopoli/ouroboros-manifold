# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI2: the section 4 measures reproduce the recorded facts of the stage 3 situation SIT-0106 at three engines
"""LI2 whole-run, SIT-0106 (24 v 48, hold_and_attack, 11 to 23 MB files): approved (4fa618ce7) 11:0 tick 2315, today (main 45245ff88) 5:0 tick 2543, variant A 0:13 tick 2301.
Spec 1.8: "Findings are never smoothed over"; spec 4: the measure row per run. The facts are r6-compare/out/SIT-0106-*.facts.json (stats.py). Definitions that differ from
the facts' are listed in `isolation_measures_real.assert_reproduces_facts`.

Control (green today): the three files exist, their own result is the known one, and they carry the keys the measures read (`fired`, `orders`, `ranges`; no `sights`)."""
import json

import pytest

import isolation_measures_real as real

CASES = real.SIT
IDS = [c.key for c in CASES]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_control_files_are_the_recorded_fights(case):
    head = real.control_real_file(case)
    assert '"fired"' in head                    # every unit row of frame 0 carries it, in the first 8000 bytes of each file
    doc = json.loads(case.path.read_text())
    assert doc["schema"] == "om-fight-2" and doc["orders"]["mode"] == case.mode and "sights" not in doc and "ranges" in doc
    assert all("fired" in u and "target" in u for u in doc["frames"][3]["units"])


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_measures_reproduce_the_facts(case):
    real.assert_reproduces_facts(case)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_load_fight_equals_json_load_header_and_every_frame(case):
    """The streaming reader gives the same header keys and the same frames as `json.load`, whichever side of `frames` the header is on (ladder files: before; indented A files: after),
    and its frames can be iterated twice and are not a list held in memory."""
    mod = real.m()
    full = json.loads(case.path.read_text())
    doc = mod.load_fight(case.path)
    assert not isinstance(doc["frames"], (list, tuple))
    assert {k: v for k, v in doc.items() if k != "frames"} == {k: v for k, v in full.items() if k != "frames"}
    assert list(doc["frames"]) == full["frames"]
    assert [f["tick"] for f in doc["frames"]][:3] == [0, 2, 4]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_units_firing_equals_an_independent_count_from_the_file(case):
    """by_frame and first contact recounted here straight from the JSON: units whose `fired` is true, per side, per frame."""
    full = json.loads(case.path.read_text())
    expect = [[f["tick"], sum(1 for u in f["units"] if u["side"] == "A" and u.get("fired")), sum(1 for u in f["units"] if u["side"] == "B" and u.get("fired"))] for f in full["frames"]]
    doc, row = real.measured(case)
    assert row["units_firing"]["by_frame"] == expect
    assert row["first_contact_tick"] == next(t for t, a, b in expect if a + b)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_spread_at_tick_zero_is_the_rms_of_the_first_frame(case):
    full = json.loads(case.path.read_text())
    expect = {}
    for s in "AB":
        pts = [(u["x"], u["y"]) for u in full["frames"][0]["units"] if u["side"] == s and u["alive"]]
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        expect[s] = (sum((x - cx) ** 2 + (y - cy) ** 2 for x, y in pts) / len(pts)) ** 0.5
    doc, row = real.measured(case)
    assert row["spread"][0]["A"] == pytest.approx(expect["A"], rel=1e-9)
    assert row["spread"][0]["B"] == pytest.approx(expect["B"], rel=1e-9)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_the_row_is_the_same_every_time(case):
    mod = real.m()
    a = json.dumps(mod.measure_fight(mod.load_fight(case.path), spread_ticks=[0, 1000]), sort_keys=True)
    b = json.dumps(real.measured(case)[1], sort_keys=True)
    assert a == b


def test_the_three_engines_read_apart_by_survivors_margin():
    """The comparison the plan exists for, in soldiers: approved A ahead by 11, today A ahead by 5, variant A behind by 13 (spec 5 'beats 17, loses to 18' form)."""
    got = [real.measured(c)[1]["margin_survivors"] for c in CASES]
    assert got == [11, 5, -13]
