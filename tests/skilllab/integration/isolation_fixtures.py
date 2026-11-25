# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md, piece LI1 (the version runner)
"""Helpers shared by test_isolation_runner_*.py. The runner is imported lazily so a missing module fails each test (red), not the collection.

The whole-run fixture: `then` (4fa618ce7) and `now` (origin/main) run the same real lab fight, L-0047 (16 a side, flat ground, one feature, sight off) at seed 10, written twice by
`run_matrix` into two rows files in two out dirs of one scratch root. Probe, 2026-11-24: each fight is about 14 s, a build 13 s."""
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
CHECKOUT = Path.home() / "Projects" / "ouroboros-manifold"   # Westley's live checkout: read-only here, `git --no-optional-locks`, never written
PY = "/home/westopoli/Projects/ouroboros-manifold/.venv/bin/python"
THEN_SHA = "4fa618ce78349fcc077ce552753131e737ae2cea"
LAYOUT, SEED = "L-0047", 10        # a catalogue id in both versions; R6 rejects a featureless layout, so the open field is the one-feature 16 v 16
SITUATION = "SIT-0106"             # converts at `now`; at `then` the converter rejects it ("arc too small": the situation file changed since)
ROW_KEYS = {"version", "lab_sha", "arm", "layout", "seed", "result", "margin", "units_firing", "fight_path", "fight_sha256", "error"}
RESULT_KEYS = {"winner", "survivors", "last_tick", "end"}
ENDS = ("wipe", "apart", "silence", "cap")
_memo = {}


def runner():
    import importlib
    return importlib.import_module("scripts.skilllab.arena.isolation_runner")


def git(repo, *args):
    return subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sans_path(row):
    """The row as bytes with the one field that names a place (fight_path) removed; equal runs are equal in these bytes."""
    return json.dumps({k: v for k, v in row.items() if k != "fight_path"}, sort_keys=True)


def matrix(scratch):
    """SimpleNamespace(first, second, file1, file2, out1, out2): the two matrix runs (rows lists as run_matrix returns them, rows files)."""
    key = str(scratch)
    if key not in _memo:
        ir = runner()
        out = {}
        for n in (1, 2):
            rows_file = Path(scratch) / ("rows%d" % n) / "rows.jsonl"
            out[n] = (ir.run_matrix(["then", "now"], [LAYOUT], [SEED], scratch, rows_file, repo=ROOT, out_dir=Path(scratch) / ("fights%d" % n)), rows_file)
        _memo[key] = SimpleNamespace(first=out[1][0], second=out[2][0], file1=out[1][1], file2=out[2][1], out1=Path(scratch) / "fights1", out2=Path(scratch) / "fights2")
    return _memo[key]


def by_version(rows, name):
    (row,) = [r for r in rows if r["version"] == name]
    return row
