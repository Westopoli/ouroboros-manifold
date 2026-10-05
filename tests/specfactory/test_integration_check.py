"""scripts/integration_check.py comparison rule (docs/northstar/regression.md, Tier 2)."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import integration_check as ic  # noqa: E402


def suite(failing=(), passed=10):
    return {"status": "pass", "passed": passed, "failed": len(failing), "skipped": 0, "xfailed": 0,
            "aborted": 0, "wall_s": 1.0, "failing_ids": sorted(failing)}


def record():
    long = suite()
    long["seeds"] = {"3": {"archetype": "assault", "end": "won", "ticks": 4000, "alive": [5, 0], "wall_s": 9.0}}
    return {"suites": {"csim": suite(["t.py::old"]), "long": long}}


def test_identical_passes():
    assert ic.verdict(record(), record())[0] == "PASS"


def test_new_failing_id_regresses_and_names_it():
    cur = record()
    cur["suites"]["csim"] = suite(["t.py::old", "t.py::new"])
    v = ic.verdict(record(), cur)
    assert v[0] == "REGRESSION" and any("t.py::new" in x for x in v[1])


def test_declared_id_not_counted():
    cur = record()
    cur["suites"]["csim"] = suite(["t.py::old", "t.py::new"])
    v = ic.verdict(record(), cur, declared=["t.py::new"])
    assert v[0] == "PASS" and v[2]


def test_changed_long_ticks_regresses():
    cur = record()
    cur["suites"]["long"]["seeds"]["3"]["ticks"] = 4001
    assert ic.verdict(record(), cur)[0] == "REGRESSION"


def test_timing_change_alone_passes():
    cur = copy.deepcopy(record())
    cur["suites"]["csim"]["wall_s"] = 999.0
    cur["suites"]["long"]["seeds"]["3"]["wall_s"] = 99.0
    assert ic.verdict(record(), cur)[0] == "PASS"
