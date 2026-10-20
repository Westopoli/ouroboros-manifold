# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 41 ruling 1 (the smoke command runs firing.parity once E0 is in the library); the audit of
# 013370a4 freezes the default parity_fn (header of tests/skilllab/test_drift_fix_parity.py)
"""LAB-REV2-FIX: the smoke's default parity_fn on the real library (SLOW: OM_LAB_SLOW=1; skipped with reason 'E0 absent' before E0, the E0 check first).

With E0 in the library (OM_TP_FIRING_ARC_DEG and om_combat_can_engage), run_smoke with the default parity_fn writes smoke_summary['parity'] =
firing.parity(engine, w, units0, units1, 360.0) on the dedicated 16 v 16 mirror world (plays.blob_play(16)(16, False)) at the first sample
tick. This test computes that value independently (a fight() of the same Setup on an Engine that checks parity at its first step, over the
units it spawned) and asserts: it is a clean list (a non-empty list is a defect of the composition), and the summary equals it, on disk too.
Satisfiability: NOT run here (E0 absent in this tree; the engine stub answers can_engage -1 and the check passes trivially). The skip is the
positive control that the test file imports and collects."""
import dataclasses
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, firing, sweep  # noqa: E402
from scripts.skilllab.fight import fight  # noqa: E402

ARC_OFF = 360.0


def _e0_on_main(lib):
    return "OM_TP_FIRING_ARC_DEG" in engine._load_param_ids() and hasattr(lib._lib, "om_combat_can_engage")


class _FirstTickParity(engine.Engine):
    """Real Engine whose first step() first runs firing.parity over the units this wrapper spawned (the first sample tick, tick 0)."""

    def __init__(self):
        super().__init__()
        self.value, self._n = None, 0

    def step(self, w):
        if self._n == 0:
            sides = [[u for u in self._own.get((w.value, f), []) if self.unit_alive(w, u)] for f in (0, 1)]
            self.value = firing.parity(self, w, sides[0], sides[1], ARC_OFF)
        self._n += 1
        super().step(w)


def test_the_default_parity_of_the_smoke_is_the_clean_list_of_the_mirror_world(tmp_path):
    from scripts.skilllab import plays
    lib = engine.Engine()
    if not _e0_on_main(lib):
        pytest.skip("E0 absent")
    if os.environ.get("OM_LAB_SLOW") != "1":
        pytest.skip("real smoke run; set OM_LAB_SLOW=1")
    spy = _FirstTickParity()
    setup = dataclasses.replace(sweep.default_control_builds()["mirror"](16, False), max_ticks=5)
    fight(setup, 0, False, engine=spy)
    assert spy.value == [] and isinstance(spy.value, list)
    first = next(iter(sweep.smoke_layouts()))
    summary = sweep.run_smoke(tmp_path, workers=1, layouts={first: sweep.smoke_layouts()[first]})
    assert summary["parity"] == spy.value
    assert json.loads((tmp_path / "smoke_summary.json").read_text())["parity"] == spy.value
    assert plays.blob_play(16)(16, False).groups == sweep.default_control_builds()["mirror"](16, False).groups      # the world is the lab's own mirror play
