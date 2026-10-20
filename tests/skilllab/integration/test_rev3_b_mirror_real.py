# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R1, test T11; defects D2, D9); ledger FINDING-lab-d2, FINDING-lab-d9; piece LAB-REV3-B
"""LAB-REV3-B, R1 and T11 (D2, D9) against the real engine (OM_LAB_SLOW=1; about two minutes a mix: thirty real 16 v 16 fights, up to
about 8,500 ticks each for the M9 shape, measured under load 11 on the lab tip): the 30-fight naive mirror pre-check and the rows M5 to
M9 of plays_space.MIXES. Contract: tests/skilllab/test_rev3_b_mirror.py (sweep.mirror_precheck) and test_rev3_b_mixes.py (the rows).

  - THE TABLE AND THE PRE-CHECK AGREE: for each new row, a recorded real run of mirror_precheck(row units) has fights == 30, caps equal to
    the number of capped fights the run recorded, and ok equal to the row's `enabled` flag ("a mix that caps is rejected and reported" is
    the flag; whether ONE capped fight or a share rejects is Westley's, so this test does not decide it: it holds the table to what the
    pre-check said). An enabled row never capped; a disabled row did, or the pre-check refused it for Wardens.
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
