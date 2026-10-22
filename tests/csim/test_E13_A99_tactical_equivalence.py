"""A99 equivalence guard (docs/northstar/plans/2026-10-01-architect-rulings-2.md A99; E-13
tactical scale). The A93 perf change (per-cell faction counts, damaged-unit prepass, grid
contact check) must leave the tactical trace byte-identical. This test pins the per-step
unit-state hash of eleven runs (4 idle openings, 7 combat runs at 502 to 4,996 units)
recorded on origin/main before any perf change, in tests/csim/data/a99_tactical_hashes.json.

Run definitions, the hash, and the generator live in tests/csim/a99_tactical_runs.py.
To record (only from the reference build; the committed file is the reference):

    make libouroboros.so && python tests/csim/a99_tactical_runs.py --generate

This file covers the runs the normal csim suite can afford ("fast" in RUNS); the large
runs (2,501 and 4,996 units, including the 4,996-unit fight with both id lists over the
2,048 contact cap) are in tests/csim/scale/test_scale_A99_tactical_equivalence.py behind
OM_SCALE=1. The checksum_trace O0 == O2 requirement is already enforced by the merge
gate (scripts/specfactory/merge_gate.sh step 10, scripts/specfactory/checksum_trace.py,
tests/specfactory/test_checksum_trace.py); it is not duplicated here.

Positive control: a perturbed recorded hash and one extra tactical tick both make the
check fail, so the equivalence assertion can fail.
"""
import pytest

import a99_tactical_runs as A

FAST = [r for r in A.RUNS if r[4] == "fast"]


def test_A99_recorded_file_covers_every_run():
    rec = A.load_recorded()
    for name, units, gap, steps, _tier in A.RUNS:
        assert name in rec, f"{name} missing from {A.DATA.name}"
        assert rec[name]["units"] == units and rec[name]["gap"] == gap
        assert rec[name]["steps"] == steps == len(rec[name]["hashes"])


@pytest.mark.parametrize("run", FAST, ids=[r[0] for r in FAST])
def test_A99_tactical_trace_equals_recorded_hashes(lib, run):
    name, units, gap, steps, _tier = run
    rec = A.load_recorded()[name]["hashes"]
    got = A.run_hashes(lib, units, gap, steps)
    bad = A.first_mismatch(rec, got)
    assert bad is None, f"{name}: step {bad} hash {got[bad:bad+1]} != recorded {rec[bad:bad+1]}"


def test_A99_positive_control_perturbed_hash_is_caught(lib):
    _n, units, gap, _steps, _t = FAST[0]
    rec = A.run_hashes(lib, units, gap, 40)
    got = A.run_hashes(lib, units, gap, 40)
    assert A.first_mismatch(rec, got) is None, "control premise: unperturbed prefix must match"
    rec[17] = ("0" if rec[17][0] != "0" else "1") + rec[17][1:]
    assert A.first_mismatch(rec, got) == 17


def _flip(h):
    return ("0" if h[0] != "0" else "1") + h[1:]


def test_A99_control_survives_a_stale_recorded_reference(lib, monkeypatch):
    """TD-VG-E-26: the existing perturbed-hash control must reach its perturbation arm and catch step 17
    even when the recorded file is stale (every hash altered). RED while the control first asserts
    built == recorded."""
    stale = {n: dict(v, hashes=[_flip(h) for h in v["hashes"]]) for n, v in A.load_recorded().items()}
    monkeypatch.setattr(A, "load_recorded", lambda: stale)
    calls, real = [], A.first_mismatch
    monkeypatch.setattr(A, "first_mismatch", lambda r, g: calls.append((r is g, list(r), list(g), real(r, g))) or calls[-1][3])
    test_A99_positive_control_perturbed_hash_is_caught(lib)
    assert calls and calls[0][3] is None and not calls[0][0] and calls[0][1] == calls[0][2], "unperturbed arm must compare two distinct equal lists"
    assert calls[-1][3] == 17 and calls[-1][1][17] != calls[-1][2][17], "perturbation arm must run and catch step 17"


def test_A99_control_mechanism_catches_the_perturbed_step_only(lib):
    """TD-VG-E-26 positive control, green now and after the fix: against a first-run reference the
    unperturbed prefix is not flagged, and perturbing step k reports k (17, then 33)."""
    _n, units, gap, _s, _t = FAST[0]
    got = A.run_hashes(lib, units, gap, 40)
    assert A.first_mismatch(list(got), got) is None
    for k in (17, 33):
        rec = list(got)
        rec[k] = _flip(rec[k])
        assert A.first_mismatch(rec, got) == k


@pytest.mark.parametrize("name", ["idle_502", "fight_502_gap100"])
def test_A99_positive_control_one_extra_tick_is_caught(lib, name):
    _n, units, gap, _steps, _t = next(r for r in A.RUNS if r[0] == name)
    rec = A.load_recorded()[name]["hashes"][:60]
    shifted = A.run_hashes(lib, units, gap, 60, extra_ticks=1)
    # the idle opening is quiet; the fight is not, so only require a difference somewhere
    # for the fight run and for the idle run once anything moves in 60 steps.
    assert A.first_mismatch(rec, shifted) is not None, f"{name}: one extra tick not detected"
