# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L4 (summary.py edit is L4's, Architect 2026-10-14); decisions 12
"""LAB-REV2-L4 fix pass: summary.write runs UNSTUBBED on FightResults that have no `mopup_orders` (L2 retired the field).

The batch tests replace summary.write with a stub (fakes_batches.stub_summary_write, autouse where imported), which hid that
summary.py still read `f.mopup_orders`. This file never imports that stub, so the real function is the one called."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import _fr, scan_of  # noqa: E402
from scripts.skilllab import summary  # noqa: E402
from scripts.skilllab.contract import CellResult, FightResult  # noqa: E402


def _scan(outcomes):
    fights = [_fr(o, 16) for o in outcomes]
    cell = CellResult(enemy_heads=16, fights=fights, mean_margin=sum(f.margin for f in fights) / len(fights), won=all(o == "side0" for o in outcomes))
    return scan_of(16, 16, [cell])


def _defn():
    cells = [SimpleNamespace(label="cellA", status="ok", size=16, enemy_from=8, enemy_to=24, build=object(), reference=None, note=None),
             SimpleNamespace(label="cellB", status="ok", size=16, enemy_from=8, enemy_to=24, build=object(), reference=object(), note=None)]
    return SimpleNamespace(name="formation", cells=cells, variants=[("naive", None)])


def test_the_function_under_test_is_the_real_one_and_the_stub_is_not_imported():
    """Positive control: nothing replaced summary.write (its code lives in summary.py), and this file does not use the autouse stub."""
    assert summary.write.__module__ == "scripts.skilllab.summary" and summary.write.__code__.co_filename.endswith("summary.py")
    imports = [ln for ln in Path(__file__).read_text().splitlines() if ln.startswith(("from ", "import "))]
    assert imports and not [ln for ln in imports if "fakes_batches" in ln]


def test_the_results_it_is_given_have_no_mopup_orders_field():
    """The input has the post-L2 shape: a field that is gone cannot be read."""
    assert not hasattr(_fr("side0", 16), "mopup_orders") and "mopup_orders" not in FightResult.__dataclass_fields__


def test_write_runs_unstubbed_and_reports_the_counts(tmp_path):
    scans = {("cellA", "naive"): _scan(["side0", "side0", "side1"]),
             ("cellB", "naive"): _scan(["side1", "draw", "cap"]),
             ("cellB", "reference"): _scan(["side0", "side0", "side0"])}
    path = tmp_path / "summary.json"
    summary.write(_defn(), scans, path, "elimination only")
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["batch"] == "formation" and doc["rule"] == "elimination only" and [c["label"] for c in doc["cells"]] == ["cellA", "cellB"]
    a = doc["cells"][0]["variants"]["naive"]["by_enemy_size"]["16"]
    assert (a["fights"], a["won"], a["lost"], a["cap"], a["draw"]) == (3, 2, 1, 0, 0)
    b = doc["cells"][1]["variants"]["naive"]["by_enemy_size"]["16"]
    assert (b["fights"], b["won"], b["lost"], b["cap"], b["draw"]) == (3, 0, 1, 1, 1)
    assert doc["cells"][1]["reference_naive_v_naive"]["by_enemy_size"]["16"]["won"] == 3
    assert doc["cells"][0]["variants"]["naive"]["beats"] == 16


def test_a_not_expressed_cell_is_written_without_reading_any_fight(tmp_path):
    defn = SimpleNamespace(name="formation", variants=[("naive", None)], cells=[
        SimpleNamespace(label="gone", status="n/a", size=16, enemy_from=8, enemy_to=24, build=None, reference=None, note="no play built")])
    path = tmp_path / "s.json"
    summary.write(defn, {}, path, "r")
    assert json.loads(path.read_text(encoding="utf-8"))["cells"][0]["not_expressed"] == "no play built"
