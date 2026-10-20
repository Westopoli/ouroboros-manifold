# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1, test T11; defects D2, D9); ledger FINDING-lab-d2, FINDING-lab-d9; piece LAB-REV3-B
"""LAB-REV3-B, R1 and T11 (D2, D9) against the real engine (OM_LAB_SLOW=1; about two minutes a mix: thirty real 16 v 16 fights, up to
about 8,500 ticks each for the M9 shape, measured under load 11 on the lab tip): the 30-fight naive mirror pre-check and the rows M5 to
M9 of plays_space.MIXES. Contract: tests/skilllab/test_rev3_b_mirror.py (sweep.mirror_precheck) and test_rev3_b_mixes.py (the rows).

  - THE TABLE AND THE PRE-CHECK AGREE: for each new row, a recorded real run of mirror_precheck(row units) has fights == 30, caps equal to
    the number of capped fights the run recorded, and ok equal to the row's `enabled` flag. Since the Architect's ruling of 2026-10-20 one
    capped fight rejects a mix, except the known cap of M9 (FINDING-lab-d9, fix FU-warden-no-stack): an enabled row never capped, or capped
    only at the Warden pattern (M9, ok True with reason known_cap:FINDING-lab-d9); a disabled row capped off the pattern, or was refused
    for Wardens.
  - MEASURED (2026-10-20, this file's reviewer, a scratch mirror of the same shape: blobs at x -350 and 350, seeds i // 2, swap i % 2,
    lab tip, built-in types): M5 0 caps, M6 0, M7 0, M8 0 (max 8295 ticks), M9 1 cap of 30 (seed 6, unswapped, 12000 ticks).
  - M9 ON THE REAL ENGINE (the ratified `living` shape, see test_rev3_b_mirror.py and test_rev3_b_living.py): its cap, if any, is fight 12 (seed 6 unswapped) and its living roster
    at the cap is ({'Vanguard': 2, 'Warden': 4}, {'Warden': 2}) (measured by the B builder: Architect ruling 2026-10-20, P1, side 1 is all
    Wardens), so M9 is accepted with the known-cap reason. This needs the real fight function to fill the `living`
    field of its result (the B builder owns that contract.py and fight.py edit).
  - POSITIVE CONTROL for the cap detection on the real engine: the same pre-check with every fight cut at 200 ticks (a fight_fn that
    lowers max_ticks) rejects an ordinary mix as capped, 30 of 30.
  - T11: the Warden refusal of the real path fights nothing (a fast test in test_rev3_b_mirror.py patches the engine out; here the
    unpatched call returns at once)."""
import dataclasses
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, sweep  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights; set OM_LAB_SLOW=1")
NEW = ("M5", "M6", "M7", "M8", "M9")


@SLOW
@pytest.mark.parametrize("name", NEW)
def test_r1_the_rows_enabled_flag_is_what_the_30_fight_mirror_said(name):
    """R1. Red today: no row, no pre-check."""
    row = next((r for r in plays_space.MIXES if r["name"] == name), None)
    assert row is not None, "MIXES has no row %s" % name
    outcomes = []

    def fight_fn(setup, seed, swap):
        r = fight(setup, seed, swap)
        outcomes.append(r.outcome)
        return r

    verdict = sweep.mirror_precheck(row["units"], fight_fn=fight_fn)
    assert verdict["fights"] == len(outcomes) == sweep.MIRROR_FIGHTS == 30, (verdict, len(outcomes))
    assert verdict["caps"] == outcomes.count("cap"), (verdict, outcomes)
    assert row["enabled"] is verdict["ok"], "%s: enabled=%r but the pre-check said %r (caps %d of 30)" % (name, row["enabled"], verdict["ok"], verdict["caps"])


@SLOW
def test_t1_m9_on_the_real_engine_is_accepted_and_its_only_cap_is_the_warden_stall_of_fight_12():
    """Architect ruling 2026-10-20, P1: M9 is enabled in the table; the 30-fight mirror is ok; every cap matches P1 (at least one side has
    living units and every living unit of that side is a Warden) and the cap is fight 12. MEASURED roster at that cap, pasted: side 0
    {'Vanguard': 2, 'Warden': 4}, side 1 {'Warden': 2} (seed 6 unswapped, 12000 ticks; FINDING-lab-d9). Red today: no row M9 or no P1
    pre-check; green on the builder's P1 fix."""
    row = next((r for r in plays_space.MIXES if r["name"] == "M9"), None)
    assert row is not None and row["enabled"] is True, row
    verdict = sweep.mirror_precheck(row["units"], fight_fn=fight)
    assert verdict["ok"] is True, verdict
    assert set(verdict["rosters"]) <= {12}, verdict["rosters"]
    assert verdict["reason"] == ("known_cap:FINDING-lab-d9" if verdict["caps"] else None), verdict
    for living in verdict["rosters"].values():
        assert any(side and set(side) == {"Warden"} for side in living), living
    if 12 in verdict["rosters"]:
        assert verdict["rosters"][12] == ({"Vanguard": 2, "Warden": 4}, {"Warden": 2}), verdict["rosters"][12]


@SLOW
def test_r1_positive_control_a_mirror_cut_at_200_ticks_is_rejected_as_capped():
    """Positive control for the detector on the real engine: no 16 v 16 fight ends in 200 ticks, so all 30 cap. Red today: no pre-check."""
    cut = lambda setup, seed, swap: fight(dataclasses.replace(setup, max_ticks=200), seed, swap)
    verdict = sweep.mirror_precheck({"Vanguard": 8, "Bombard": 8}, fight_fn=cut)
    assert verdict["ok"] is False and verdict["reason"] == "capped" and verdict["caps"] == 30 == verdict["fights"], verdict


@SLOW
def test_t11_the_unpatched_warden_refusal_returns_at_once():
    """T11 on the real path: 16 Wardens (20 of 20 caps measured) is refused without a fight; thirty such fights would take minutes."""
    t0 = time.time()
    verdict = sweep.mirror_precheck({"Warden": 16})
    assert verdict["ok"] is False and verdict["reason"] == "warden_cap" and verdict["fights"] == 0, verdict
    assert time.time() - t0 < 5
