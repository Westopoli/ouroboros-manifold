# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md::Phase A::verification 4
# spec: docs/northstar/plans/2026-10-02-skill-lab-cascade.md::section 5 invariant
"""Baseline guard: unit-state hashes of a fixed set of fights, recorded on the engine as it
was before any movement change (baseline_hashes.json, from tests/csim/parity/baseline/
baseline_fights.py --generate). Green today. After the two switches exist
(OM_TP_PURSUE_BY_STEERING, OM_TP_ROUTE_AROUND_TERRAIN) and are set to 0 in
baseline_fights.apply_baseline_settings, the same hashes must still hold: the plan's
"with the two movement switches at 0 the recorded hashes are unchanged". Hashes that
change on purpose at 1 are re-recorded once per wave with a ledger row; a hash that
moves with the switches at 0 is a regression, never re-recorded.

Also here: the O0 build and the O2 build give the same per-tick trace on every fight
(CLAUDE.md determinism contract; checksum_trace.py is the merge gate's world-checksum
version of the same comparison), and a positive control showing the hash notices a
one-unit nudge.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # repo root, for scripts.skilllab
sys.path.insert(0, str(Path(__file__).resolve().parent))

import baseline_fights as B  # noqa: E402

NAMES = B.all_names()


@pytest.fixture(scope="module")
def traces():
    B.build_libs()
    cache = {}

    def get(level, name):
        key = (level, name)
        if key not in cache:
            cache[key] = B.run_one(B.LIB[level], name)
        return cache[key]
    return get


def _first_drift(rec, got):
    if rec["ticks"] != got["ticks"]:
        return f"tick count {rec['ticks']} vs {got['ticks']}"
    for i, (a, b) in enumerate(zip(rec["checkpoints"], got["checkpoints"])):
        if a != b:
            return f"first drift in ticks {i * B.CHECKPOINT_EVERY + 1}..{(i + 1) * B.CHECKPOINT_EVERY}"
    return "drift after the last checkpoint" if rec["final"] != got["final"] else None


def test_baseline_file_names_the_fixed_set():
    rec = B.load_recorded()
    assert sorted(rec) == sorted(NAMES), "baseline_hashes.json does not list exactly the fixed set of fights"
    assert len([n for n in rec if n.startswith("skilllab_")]) == 6   # three controls, two cells each
    for n, r in rec.items():
        assert r["ticks"] > 0 and len(r["final"]) == 64, n


@pytest.mark.parametrize("name", NAMES)
def test_baseline_unit_state_hash_unchanged_o2(traces, name):
    """The unchanged engine reproduces the recorded per-tick unit-state hash."""
    rec = B.load_recorded()[name]
    got = traces("O2", name)
    assert got["final"] == rec["final"], f"{name}: {_first_drift(rec, got)}"


@pytest.mark.parametrize("name", NAMES)
def test_baseline_o0_and_o2_builds_identical(traces, name):
    """Determinism contract: -O0 and -O2 give byte-identical per-tick unit state."""
    a, b = traces("O0", name), traces("O2", name)
    assert a == b, f"{name}: O0 vs O2 {_first_drift(a, b)}"


def test_baseline_control_hash_notices_a_nudge(traces):
    """Positive control: moving one unit by 1e-6 wu before the first tick changes the hash.
    Without this the guard could be passing because it compares nothing."""
    lib = B.csim_handle(B.LIB["O2"])
    w, _cell, steps = B.FIXTURES["fixture_mixed_march"](lib)
    x, y = lib.om_unit_get_pos(w, 1)
    lib.om_unit_set_pos(w, 1, x + 1e-6, y)
    roll = B._Roller()
    ids = list(range(1, lib.om_unit_count(w) + 1))
    for _ in range(steps):
        lib.om_tactical_step(w)
        roll.tick(B._records(lib, w, ids))
    lib.om_world_free(w)
    assert roll.result()["final"] != B.load_recorded()["fixture_mixed_march"]["final"]
    assert roll.result()["final"] != traces("O2", "fixture_mixed_march")["final"]


def test_baseline_control_drift_is_located(traces):
    """Positive control for the drift locator: a doctored record names the checkpoint window."""
    rec = dict(B.load_recorded()["fixture_wall_gap"])
    rec["checkpoints"] = list(rec["checkpoints"])
    rec["checkpoints"][2] = "0" * 16
    where = _first_drift(rec, traces("O2", "fixture_wall_gap"))
    assert where == "first drift in ticks 201..300"
