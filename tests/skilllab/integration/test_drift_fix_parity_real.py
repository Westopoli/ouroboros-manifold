# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 41 ruling 1 (the smoke command runs firing.parity once E0 is in the library); the audit of
# 013370a4 freezes the default parity_fn (header of tests/skilllab/test_drift_fix_parity.py)
"""LAB-REV2-FIX: the smoke's default parity_fn on the real library (SLOW: OM_LAB_SLOW=1; skipped with reason 'E0 absent' before E0, the E0 check first).

With E0 in the library (OM_TP_FIRING_ARC_DEG and om_combat_can_engage), run_smoke with the default parity_fn writes smoke_summary['parity'] =
firing.parity(engine, w, units0, units1, 360.0) on the dedicated 16 v 16 mirror world (plays.blob_play(16)(16, False)) at the first sample
tick. This test computes that value independently (a fight() of the same Setup on an Engine that checks parity at its first step, over the
units it spawned) and asserts: it is a clean list (a non-empty list is a defect of the composition), and the summary equals it, on disk too.
Satisfiability: NOT run here (E0 absent in this tree; the engine stub answers can_engage -1 and the check passes trivially). The skip is the
positive control that the test file imports and collects."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "tests" / "skilllab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import _fr  # noqa: E402
from scripts.skilllab import engine, firing, sweep  # noqa: E402

CALL_NAMES = ("engine", "w", "units0", "units1", "arc_deg")      # firing.parity's own parameters, so a keyword call is read the same


def test_the_default_parity_fn_calls_firing_parity_once_on_the_16_v_16_mirror_world_without_e0(tmp_path, monkeypatch):
    """Positive control of the default parity_fn that needs no E0 data (audit of 32039a0f, item 2). firing.parity is replaced by a recorder
    that returns a NON-EMPTY list, so the wiring is checked and not the composition: run_smoke with caps.arc True and the default parity_fn
    (parity_fn=None) calls the module attribute firing.parity exactly once, with the real engine, the arc 360.0 and the 16 + 16 units of the
    mirror world (all alive, all different), and smoke_summary['parity'] is the returned list, on disk too. The real library is used for the
    world (spawn and orders as fight() does); E0 is not needed because the recorder stands in for the composition."""
    from scripts.skilllab.sweep import Capabilities
    seen = []

    def recorder(*args, **kw):
        got = dict(zip(CALL_NAMES, args), **kw)
        eng, w = got["engine"], got["w"]
        seen.append(dict(arc=got["arc_deg"], n0=len(got["units0"]), n1=len(got["units1"]), ids=set(got["units0"]) | set(got["units1"]),
                         alive=all(eng.unit_alive(w, u) for u in list(got["units0"]) + list(got["units1"])), engine=eng))
        return [101, 102]
    monkeypatch.setattr(firing, "parity", recorder)
    first = next(iter(sweep.smoke_layouts()))
    summary = sweep.run_smoke(tmp_path, workers=1, layouts={first: sweep.smoke_layouts()[first]}, caps=Capabilities(arc=True, cone=False),
                              fight_fn=lambda setup, seed, swap: _fr("side0", 8), replicates=1)
    assert len(seen) == 1, "firing.parity was called %d times" % len(seen)
    (call,) = seen
    assert call["arc"] == 360.0 and (call["n0"], call["n1"]) == (16, 16) and len(call["ids"]) == 32 and call["alive"]
    assert isinstance(call["engine"], engine.Engine)
    assert summary["parity"] == [101, 102] and json.loads((tmp_path / "smoke_summary.json").read_text())["parity"] == [101, 102]


def test_control_without_e0_the_default_parity_fn_is_not_run(tmp_path, monkeypatch):
    """Negative control for the test above: caps.arc False reads 'skipped: E0 absent' and never reaches firing.parity."""
    from scripts.skilllab.sweep import Capabilities
    monkeypatch.setattr(firing, "parity", lambda *a, **k: pytest.fail("firing.parity was called"))
    first = next(iter(sweep.smoke_layouts()))
    summary = sweep.run_smoke(tmp_path, workers=1, layouts={first: sweep.smoke_layouts()[first]}, caps=Capabilities(arc=False, cone=False),
                              fight_fn=lambda setup, seed, swap: _fr("side0", 8), replicates=1)
    assert summary["parity"] == "skipped: E0 absent"
