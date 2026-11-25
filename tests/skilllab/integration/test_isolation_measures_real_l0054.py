# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI2: the section 4 measures reproduce the recorded facts of L-0054 (128 v 128 meeting) at three engines
"""LI2 whole-run, L-0054 (both_same_point, 150 to 230 MB files, streamed): approved (4fa618ce7) 9:0 tick 8954, today (main 45245ff88) 14:22 tick 10860 (a `draw`, end `apart`:
a defect cell), variant A 0:17 tick 6408. Facts: r6-compare/out/L-0054-*.facts.json: never fired 1/12:19/0, idle at the end 0/35/5, overlap pairs 0/5/2.
A `draw` is a lab bug to trace, not a result (spec 1.8): the row says `defect`, the agreement word is n/a.

Control (green today): the three files exist, their own result is the known one (read from the head or the tail only, never the whole file)."""
import json

import pytest

import isolation_measures_real as real

CASES = real.L54
IDS = [c.key for c in CASES]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_control_files_are_the_recorded_fights(case):
    head = real.control_real_file(case)
    assert '"fired"' in head                    # every unit row of frame 0 carries it, in the first 8000 bytes of each file
    assert case.path.stat().st_size > 100_000_000


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_measures_reproduce_the_facts(case):
    real.assert_reproduces_facts(case)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_load_fight_streams_a_big_file(case):
    """Spec 7 and the brief: frames are read incrementally. The header is whole and right (either side of `frames`), the frames iterate twice, are not a list, and their count
    and last tick are the facts' (3205/6408, 4478/8954, 5431/10860 frames per the facts files)."""
    mod = real.m()
    f = real.facts(case)
    doc = mod.load_fight(case.path)
    assert not isinstance(doc["frames"], (list, tuple))
    assert doc["result"]["winner"] == case.winner and doc["result"]["survivors"] == case.survivors
    assert doc["orders"]["mode"] == "both_same_point" and "sights" not in doc
    first = next(iter(doc["frames"]))
    again = next(iter(doc["frames"]))
    assert first["tick"] == again["tick"] == 0 and len(first["units"]) == f["never_fired"]["units_start"]
    n, last = 0, None
    for fr in doc["frames"]:
        n, last = n + 1, fr["tick"]
    assert (n, last) == (f["frames"], f["last_frame_tick"])


def test_the_draw_is_a_defect_with_no_agreement():
    """Today's engine ends this fight with both sides alive and apart (14:22): `draw`, a defect (precondition 8), agreement n/a, never a result."""
    row = real.measured([c for c in CASES if c.version == "today"][0])[1]
    assert row["result"]["winner"] == "draw" and row["result"]["end"] == "apart" and row["result"]["defect"] is True
    assert row["predictions"]["agreement"] == "n/a"


def test_the_movement_findings_that_the_facts_record():
    """Orders ended short on L-0054, alive at the end: approved 0, today 35 (23 in front of the firing line, 12 behind it), variant A 5 (4 front, 1 behind); the split is the idle split."""
    got = []
    for c in CASES:
        row = real.measured(c)[1]
        i = row["idle_units"]
        got.append((len(real.m().orders_ended_short(real.measured(c)[0], stuck_ticks=real.m().DRAFT_IDLE_TICKS_200)["alive_at_end"]), i["behind"], i["front"]))
    assert got == [(0, 0, 0), (35, 12, 23), (5, 1, 4)]
