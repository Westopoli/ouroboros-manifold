# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2: probe default, batch runner, header); ledger FINDING-lab-d10; piece LAB-REV3-A
"""LAB-REV3-A, T2 at the batch level (Architect ruling 2026-10-20): `run_family` defaults to probe=False; the CLI and the batch runner
turn the probe on; the batch header says probe=on; a batch run with probe=off is REFUSED BY THE BATCH RUNNER, not by run_family.
Fast, fakes only (a fake run_family or a fake sweep.run capturing keywords).

THE BATCH RUNNER IS `sweep.run` and the CLI command `python -m scripts.skilllab sweep` that calls it (the plan names no other; the lab's
`batches.py` runs the older formation/focus-fire/landscape batches, not the knob families). A written choice, flagged to the Architect: the
existing tests that call `sweep.run(...)` with fakes whose result ignores the knob (test_sweep.py:963-964, 1032, 1040, 1050, 1061-1062,
test_sweep_baselines.py:274, 404-406, integration/test_workers_hash.py) do not mention `probe`. The tests here always pass it explicitly and pin nothing about what `sweep.run` does when it is not told: a
default of True there would refuse those inert fakes (the ruling's "the batch runner turns it on" is read as: sweep.run honours an
explicit True and refuses an explicit False; the CLI passes True).

BUILDER CONTRACT:
  - `sweep.run(families, out_dir, workers=1, full_scan=False, probe=..., **kw)` passes `probe=<its value>` on to every `run_family`
    call (kw already travels there); with probe=True the summary dict and sweep_summary.json carry the key `"probe": "on"`.
  - `sweep.run(..., probe=False)` raises ValueError whose message contains "probe" (and says the batch needs it on), before any
    run_family call and before sweep_summary.json is written.
  - The CLI command `sweep` calls `sweep.run(..., probe=True)`.
Red today: the summary has no "probe" key, probe=False is accepted, the CLI passes no `probe`."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import fake_builds  # noqa: E402
from scripts.skilllab import __main__ as cli, sweep  # noqa: E402


@pytest.fixture
def seen(monkeypatch):
    calls = []
    monkeypatch.setattr(sweep, "run_family",
                        lambda name, out_dir, **kw: calls.append((name, kw)) or {"family": name, "skipped": None, "csv": None, "rows": 0})
    return calls


def test_positive_control_the_batch_runner_forwards_its_keywords_to_every_family(tmp_path, seen):
    """Green on the lab tip: a keyword given to sweep.run reaches each run_family call, so the probe flag has a path to travel."""
    sweep.run(["range_up", "damage_up"], tmp_path, builds=fake_builds(), layouts={"A": {}}, probe=True)
    assert [(n, kw["probe"]) for n, kw in seen] == [("range_up", True), ("damage_up", True)]


def test_t2_the_batch_header_says_probe_on(tmp_path, seen):
    """T2 (ruling): the summary dict and sweep_summary.json record probe=on. Red today: KeyError 'probe'."""
    summary = sweep.run(["range_up"], tmp_path, builds=fake_builds(), layouts={"A": {}}, probe=True)
    assert summary["probe"] == "on"
    assert json.loads((tmp_path / "sweep_summary.json").read_text())["probe"] == "on"


def test_t2_a_batch_run_with_the_probe_off_is_refused_by_the_batch_runner(tmp_path, seen):
    """T2 (ruling): sweep.run(probe=False) is a ValueError naming the probe; no family runs, no summary is written.
    Red today: the run is accepted."""
    with pytest.raises(ValueError, match="probe"):
        sweep.run(["range_up"], tmp_path, builds=fake_builds(), layouts={"A": {}}, probe=False)
    assert seen == [] and not (tmp_path / "sweep_summary.json").exists()


def test_t2_the_cli_sweep_command_turns_the_probe_on(tmp_path, monkeypatch):
    """T2 (ruling): `python -m scripts.skilllab sweep` calls sweep.run with probe=True. Red today: no probe keyword is passed."""
    got = []
    monkeypatch.setattr(sweep, "run", lambda families, out_dir, workers=1, **kw: got.append(kw) or {"families": {}})
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path)]) == 0
    assert got and got[0].get("probe") is True
