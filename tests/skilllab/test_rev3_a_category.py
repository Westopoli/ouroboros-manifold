# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R8, test T10; defect D6); ledger FINDING-lab-d6; piece LAB-REV3-A
"""LAB-REV3-A, T10 (R8, D6): the category-matrix family is listed unavailable with its finding. The library's OM_TP_CATMULT_* settings are
never read (csrc/unit.c uses the compile-time OM_CATEGORY_MULTIPLIER_* constants), so a family sweeping them could only produce
identical rows; the lab marks it unavailable, not swept, with FINDING-lab-d6 as the pointer, until an engine piece makes the settings
live. Fast half, fakes (no engine); the engine premise is tests/skilllab/integration/test_rev3_a_category_real.py.

BUILDER CONTRACT (the family's name is the test writer's: "category"):
  - `sweep.skip_reason("category", caps)` is a string naming `FINDING-lab-d6` and `OM_TP_CATMULT`, for any capabilities (an engine
    capability cannot make it available), like the existing reasons for "arc" and "cone".
  - `sweep.run_family("category", out_dir, ...)` returns the skipped entry (entry["skipped"] is that string, csv None, rows 0), fights
    nothing, writes no sweep_category.csv.
  - `sweep.run(["category"], out_dir, ...)` puts the same entry under summary["families"]["category"] and in sweep_summary.json.
Positive control (green on the lab tip): the existing unavailable families keep their reasons."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, fake_builds  # noqa: E402
from scripts.skilllab import sweep  # noqa: E402

CAPS = [sweep.Capabilities(arc=a, cone=c) for a in (True, False) for c in (True, False)]


def test_positive_control_a_missing_capability_family_keeps_its_reason():
    """Green on the lab tip: arc and cone report their missing build; nothing else reports."""
    assert "LAB-REV2-E0" in sweep.skip_reason("arc", sweep.Capabilities(arc=False, cone=True))
    assert "LAB-REV2-E2" in sweep.skip_reason("cone", sweep.Capabilities(arc=True, cone=False))
    assert sweep.skip_reason("range_up", sweep.Capabilities(arc=False, cone=False)) is None


@pytest.mark.parametrize("caps", CAPS)
def test_t10_the_category_family_is_unavailable_whatever_the_library_can_do(caps):
    """T10 (D6): the reason names the finding and the settings. Red today: None."""
    reason = sweep.skip_reason("category", caps)
    assert reason and "FINDING-lab-d6" in reason and "OM_TP_CATMULT" in reason


def test_t10_run_family_returns_the_skipped_entry_and_fights_nothing(tmp_path):
    """T10 (D6): no fight, no csv. Red today: ValueError, the family is unknown."""
    fight_fn = ScriptedFight(be_of=lambda setup: 20)
    entry = sweep.run_family("category", tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p",), fight_fn=fight_fn,
                             caps=sweep.Capabilities(arc=True, cone=True))
    assert "FINDING-lab-d6" in entry["skipped"] and entry["csv"] is None and entry["rows"] == 0
    assert fight_fn.calls == [] and not list(tmp_path.glob("sweep_category*"))


def test_t10_the_summary_lists_it_unavailable(tmp_path):
    """T10 (D6): the artifact carries the entry. Red today: ValueError, the family is unknown."""
    summary = sweep.run(["category"], tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p",),
                        fight_fn=ScriptedFight(be_of=lambda setup: 20), caps=sweep.Capabilities(arc=True, cone=True))
    on_disk = json.loads((tmp_path / "sweep_summary.json").read_text())
    for got in (summary, on_disk):
        assert "FINDING-lab-d6" in got["families"]["category"]["skipped"]
