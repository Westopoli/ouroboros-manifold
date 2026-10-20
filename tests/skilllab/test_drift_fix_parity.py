# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 41 ruling 1 (Architect, 2026-10-19: the smoke command runs firing.parity
# once E0 is in the landing; until then the field reads "skipped: E0 absent"); harness spec clause 10 (parity); README section 7
"""LAB-REV2-FIX: smoke_summary.json carries `parity`.

INTERFACE FROZEN FOR THE BUILDER
  sweep.run_smoke(out_dir, workers=12, *, builds=None, control_builds=None, layouts=None, fight_fn=None, map_fn=None, full_scan=False,
                  replicates=REPLICATES, caps=None, parity_fn=None)
    caps       Capabilities or None; None means sweep.detect() (the module attribute, read at call time: the lab's convention for 'E0 is
               in the library' is detect().arc, the parameter OM_TP_FIRING_ARC_DEG in the table, exactly as for the arc family).
    parity_fn  a zero-argument callable or None. None means the builder's default: firing.parity (read as the module attribute, at call
               time) run on a smoke world; the tests never use the default, it needs a library with E0 (an integration check at landing).
    Summary key `parity` (always present, also in smoke_summary.json on disk):
      caps.arc False -> the exact string "skipped: E0 absent"; parity_fn is NOT called.
      caps.arc True  -> parity_fn()'s return value, written as given (the ints firing.parity returns: the units whose composed answer
                        differs from the engine's, [] when parity holds; a dict of such lists is as good: the value is not reshaped).
  THE DEFAULT parity_fn (parity_fn=None with caps.arc True; frozen by the audit of 013370a4, Architect's coordinator 2026-10-19): a dedicated
    16 v 16 mirror world, NOT one of the smoke's fights: Setup = sweep.default_control_builds()["mirror"](16, False), i.e. the lab's own
    mirror blob play plays.blob_play(16) (open ground, so no smoke layout shapes it; the key is simply written once per smoke, with the first
    smoke layout's run), both sides placed in the real engine exactly as fight() places them (same type registration, spawn and opening
    orders, seed 0), then firing.parity(engine, w, units0, units1, 360.0) is run ONCE at the first sample tick (tick 0, before any
    engine step) and its return value is the summary value. The unit tests never use it (they pass parity_fn); the SLOW integration test
    integration/test_drift_fix_parity_real.py runs it on the real library (skipped with reason 'E0 absent' without OM_TP_FIRING_ARC_DEG and
    om_combat_can_engage). The README (or the harness spec) documents the `parity` key of smoke_summary.json (tests/specfactory/test_lab_docs.py).
  Nothing else in the summary or in smoke.csv changes: rows_sha256 is the same in both states.
The fake engine is sweep's own FakeLib convention (test_sweep.py): param_id raises ValueError for an unknown parameter."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes import FakeEngine, Seam  # noqa: E402
from fakes_scans import ScriptedFight, fake_builds  # noqa: E402
from scripts.skilllab import firing, sweep  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

SKIP = "skipped: E0 absent"
LAYOUTS = {"A": {"id": 1}}


class FakeLib:
    """What sweep.detect reads: param_id (ValueError when unknown), a probe world and a cone setter that is absent."""

    def __init__(self, params=()):
        self.params = set(params)

    def param_id(self, name):
        if name not in self.params:
            raise ValueError("unknown parameter %r" % (name,))
        return 1

    def new_world(self, seed):
        return object()

    def free_world(self, w):
        pass

    def type_id(self, name):
        return 2

    def set_cone(self, *a):
        raise AttributeError("undefined symbol: om_roster_set_cone")


def smoke(tmp_path, **kw):
    controls = {n: (lambda h, swap, n=n: Setup(groups=(), unit_types={"enemy": h, "swap": swap, "_play": n, "_role": "play"}))
                for n in ("mirror", "numbers", "planted")}
    summary = sweep.run_smoke(tmp_path, workers=1, builds=fake_builds(), layouts=LAYOUTS, fight_fn=ScriptedFight(be_of=lambda s: 20),
                              control_builds=controls, **kw)
    return summary, json.loads((tmp_path / "smoke_summary.json").read_text())


def boom():
    pytest.fail("parity_fn was called")


# ---- E0 absent ----------------------------------------------------------------------------------------------------------------------

def test_without_e0_the_parity_field_reads_skipped_and_parity_is_not_run(tmp_path):
    summary, disk = smoke(tmp_path, caps=sweep.Capabilities(arc=False, cone=False), parity_fn=boom)
    assert summary["parity"] == SKIP == disk["parity"]


def test_e0_absent_is_read_through_detect_on_a_library_without_the_arc_parameter(tmp_path, monkeypatch):
    real = sweep.detect
    monkeypatch.setattr(sweep, "detect", lambda engine=None: real(FakeLib()))
    summary, disk = smoke(tmp_path, parity_fn=boom)
    assert summary["parity"] == SKIP == disk["parity"]


# ---- E0 present ---------------------------------------------------------------------------------------------------------------------

def test_with_e0_the_parity_result_is_written_as_given(tmp_path):
    summary, disk = smoke(tmp_path, caps=sweep.Capabilities(arc=True, cone=False), parity_fn=lambda: [3, 7])
    assert summary["parity"] == [3, 7] == disk["parity"]


def test_a_dict_result_is_written_unchanged(tmp_path):
    result = {"81/s3_layer_above": [4], "78/s3_layer_above": []}
    summary, disk = smoke(tmp_path, caps=sweep.Capabilities(arc=True, cone=False), parity_fn=lambda: result)
    assert summary["parity"] == result == disk["parity"]


def test_a_holding_parity_is_an_empty_list_not_the_skip_string(tmp_path):
    """Null control: nothing to report is [] (parity holds), which is not 'skipped'."""
    summary, disk = smoke(tmp_path, caps=sweep.Capabilities(arc=True, cone=False), parity_fn=lambda: [])
    assert summary["parity"] == [] == disk["parity"] and summary["parity"] != SKIP


def test_e0_present_is_read_through_detect_on_a_library_with_the_arc_parameter(tmp_path, monkeypatch):
    real = sweep.detect
    monkeypatch.setattr(sweep, "detect", lambda engine=None: real(FakeLib(params={"OM_TP_FIRING_ARC_DEG"})))
    summary, _ = smoke(tmp_path, parity_fn=lambda: [9])
    assert summary["parity"] == [9]


def test_the_result_is_what_firing_parity_returns(tmp_path, monkeypatch):
    """parity_fn here calls the real module attribute firing.parity, replaced by the seam's recorder (fakes.Seam.parity): the ints it
    returns reach the summary, and it was asked once with the fake engine."""
    seam = Seam()
    seam.parity_units = [3, 7]
    monkeypatch.setattr(firing, "parity", seam.parity)
    fake = FakeEngine()
    summary, _ = smoke(tmp_path, caps=sweep.Capabilities(arc=True, cone=False), parity_fn=lambda: firing.parity(fake, None, [], [], 360.0))
    assert summary["parity"] == [3, 7] and len(seam.calls_named("parity")) == 1 and seam.calls_named("parity")[0][1] is fake


# ---- nothing else moves --------------------------------------------------------------------------------------------------------------

def test_the_rows_and_the_other_summary_keys_are_the_same_in_both_states(tmp_path):
    a, _ = smoke(tmp_path / "off", caps=sweep.Capabilities(arc=False, cone=False), parity_fn=boom)
    b, _ = smoke(tmp_path / "on", caps=sweep.Capabilities(arc=True, cone=False), parity_fn=lambda: [])
    assert {k: v for k, v in a.items() if k != "parity"} == {k: v for k, v in b.items() if k != "parity"}
    assert (tmp_path / "off" / "smoke.csv").read_bytes() == (tmp_path / "on" / "smoke.csv").read_bytes()
