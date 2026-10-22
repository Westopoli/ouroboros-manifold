# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md A185 (Addendum 64), A125
# spec: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md Phase C, G3
"""G3 hash invariant. With OM_TP_TARGET_BY_SIGHT = 0 (reach 0 and emission silent are the defaults)
every recorded hash is unchanged: the A99 tactical traces (tests/csim/data/a99_tactical_hashes.json,
per step), the baseline fights (tests/csim/parity/baseline/baseline_hashes.json, with the
baseline switches still 0), and the F1/F2/F3 goldens. These are guards: green now, green after G3.

Positive controls: a perturbed recorded hash is caught; and (RED until G3 lands) with the switch at 1 a
scene where a unit has an enemy in its own range that its side cannot see gives a different hash than
with the switch at 0. Today the switch is not read by the C code, so that control fails: that is the
red-before, and it must pass once G3 is built.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

import pytest

import a99_tactical_runs as A
import test_F1_fog_per_faction_observers as F1
import test_F2_nearest_hostile_search as F2
import test_F3_macro_contact_skip as F3
from test_PP_C_g3_support import BOMBARD, SUPPLY, set_param, spawn, step

sys.path.insert(0, str(Path(__file__).resolve().parent / "parity" / "baseline"))
import baseline_fights as B  # noqa: E402

TBS = 4  # OM_TP_TARGET_BY_SIGHT

# Frozen pre-G3 goldens (copies of origin/main before the default-1 re-record; A99 fights re-frozen at A188). The shared
# a99_tactical_hashes.json and baseline_hashes.json now hold the default-1 hashes.
# a99_tactical_hashes_pre_g3.json: the four fight ids fight_502_gap100, fight_990_gap300, fight_990_gap1500,
# fight_990_gap3000 are re-frozen at A188 and again at A199 (recorded with OM_TP_TARGET_BY_SIGHT = 0 on the build with the
# default PURSUE_BY_STEERING = 1 leash), so the invariant guards "G3 off equals the engine without G3".
# See also: TD-PP-A188-g3-invariant-reference, TD-PP-C-invariant-goldens in docs/northstar/plans/push_ledger_2026-09-22.md
_DATA = Path(__file__).resolve().parent / "data"
PRE_G3_A99 = json.loads((_DATA / "a99_tactical_hashes_pre_g3.json").read_text())
PRE_G3_BASELINE = json.loads((_DATA / "baseline_hashes_pre_g3.json").read_text())


def _off(lib, w):
    assert lib.om_tactical_set_param(w, TBS, 0.0) == 0
    assert lib.om_tactical_get_param(w, TBS) == 0.0


FAST = [r for r in A.RUNS if r[4] == "fast"]


@pytest.mark.parametrize("run", FAST, ids=[r[0] for r in FAST])
def test_G3_A99_traces_unchanged_with_target_by_sight_0(lib, run):
    """A185: switch 0 leaves every recorded A99 per-step hash byte-identical (reference frozen at A188)."""
    name, units, gap, steps, _t = run
    rec = PRE_G3_A99[name]["hashes"]
    w = A.build(lib, units)
    _off(lib, w)
    if gap is not None:
        A.stage_fight(lib, w, A._slots(lib, w), gap)
    got = []
    for _ in range(steps):
        lib.om_tactical_step(w)
        got.append(A.state_hash(lib, w))
    lib.om_world_free(w)
    bad = A.first_mismatch(rec, got)
    assert bad is None, f"{name}: step {bad} hash differs from recorded with TARGET_BY_SIGHT 0"


def test_G3_positive_control_perturbed_recorded_hash_is_caught(lib):
    name, units, gap, _s, _t = FAST[0]
    rec = list(PRE_G3_A99[name]["hashes"][:30])
    w = A.build(lib, units)
    _off(lib, w)
    got = []
    for _ in range(30):
        lib.om_tactical_step(w)
        got.append(A.state_hash(lib, w))
    lib.om_world_free(w)
    assert A.first_mismatch(rec, got) is None
    rec[9] = ("0" if rec[9][0] != "0" else "1") + rec[9][1:]
    assert A.first_mismatch(rec, got) == 9


def _flip(h):
    return ("0" if h[0] != "0" else "1") + h[1:]


def _g3_first_run(lib, steps=30):
    name, units, _gap, _s, _t = FAST[0]
    w = A.build(lib, units)
    _off(lib, w)
    got = []
    for _ in range(steps):
        lib.om_tactical_step(w)
        got.append(A.state_hash(lib, w))
    lib.om_world_free(w)
    return got


def test_G3_control_survives_a_stale_recorded_reference(lib, monkeypatch):
    """TD-VG-E-26: the existing perturbed-hash control must reach its perturbation arm and catch step 9
    even when the recorded table is stale (every hash altered). RED while the control first asserts
    built == recorded."""
    name = FAST[0][0]
    stale = dict(PRE_G3_A99[name])
    stale["hashes"] = [_flip(h) for h in PRE_G3_A99[name]["hashes"]]
    monkeypatch.setitem(PRE_G3_A99, name, stale)
    calls, real = [], A.first_mismatch
    monkeypatch.setattr(A, "first_mismatch", lambda r, g: calls.append((r is g, list(r), list(g), real(r, g))) or calls[-1][3])
    test_G3_positive_control_perturbed_recorded_hash_is_caught(lib)
    assert calls and calls[0][3] is None and not calls[0][0] and calls[0][1] == calls[0][2], "unperturbed arm must compare two distinct equal lists"
    assert calls[-1][3] == 9 and calls[-1][1][9] != calls[-1][2][9], "perturbation arm must run and catch step 9"


def test_G3_control_mechanism_catches_the_perturbed_step_only(lib):
    """TD-VG-E-26 positive control, green now and after the fix: against a first-run reference the
    unperturbed prefix is not flagged, and perturbing step k reports k (9, then 21)."""
    got = _g3_first_run(lib)
    assert A.first_mismatch(list(got), got) is None
    for k in (9, 21):
        rec = list(got)
        rec[k] = _flip(rec[k])
        assert A.first_mismatch(rec, got) == k


@pytest.mark.parametrize("name", B.all_names())
def test_G3_baseline_fights_unchanged_with_target_by_sight_0(name, monkeypatch):
    """A185: baseline_hashes.json holds with the baseline switches at 0 AND TARGET_BY_SIGHT 0."""
    B.build_libs()
    orig = B.apply_baseline_settings

    def both(lib, w):
        orig(lib, w)
        assert lib.om_tactical_set_param(w, TBS, 0.0) == 0
    monkeypatch.setattr(B, "apply_baseline_settings", both)
    got = B.run_one(B.LIB["O2"], name)
    assert got["final"] == PRE_G3_BASELINE[name]["final"], f"{name}: final hash moved with TARGET_BY_SIGHT 0"


@pytest.mark.parametrize("kind", F1.SCENE_KINDS)
def test_G3_F1_golden_with_target_by_sight_0(lib, world_factory, kind):
    w = F1._world(lib, world_factory, 1)
    _off(lib, w)
    assert F1._full_run(lib, w, kind) == F1.GOLDEN[kind]


@pytest.mark.parametrize("kind", ["clash", "spread"])
def test_G3_F2_golden_with_target_by_sight_0(lib, world_factory, kind):
    w = F2._world(lib, world_factory, 1, custom=False)
    _off(lib, w)
    assert F2._full_run(lib, w, kind) == F2.GOLDEN[kind]


@pytest.mark.parametrize("kind", ["clash", "spread"])
def test_G3_F3_golden_with_target_by_sight_0(lib, world_factory, kind):
    w = F3._world(lib, world_factory, 1)
    _off(lib, w)
    assert F3._full_run(lib, w, kind) == F3.GOLDEN[kind]


# ---- positive control: the switch must change something at 1 -------------------------------

def unseen_in_range_hashes(lib, w_factory, switch, ticks=80):
    """A Bombard (range 1200, sensor 300) with a never-firing 5,000 hp Supply 800 wu away on its own
    layer, no other friendly: in the Bombard's range, unseen by its side."""
    w = w_factory(n_regions=1)
    set_param(lib, w, "TARGET_BY_SIGHT", switch)
    b = spawn(lib, w, BOMBARD, 0, 0.0, 0.0)
    t = spawn(lib, w, SUPPLY, 1, 800.0, 0.0)
    lib.om_unit_set_hp(w, t, 5000.0)
    lib.om_visibility_compute(w)
    assert not lib.om_unit_can_see(w, b, t), "scene premise: the target is outside the side's sight"
    out = []
    for _ in range(ticks):
        step(lib, w)
        x, y = lib.om_unit_get_pos(w, t)
        out.append(hashlib.sha256(struct.pack("<IddddI", t, x, y, lib.om_unit_get_hp(w, t), 0.0,
                                              lib.om_unit_get_target(w, b))).hexdigest()[:16])
    return out


def test_G3_positive_control_hash_differs_at_1_when_a_target_is_in_range_but_unseen(lib, world_factory):
    """RED until G3: at 1 the Bombard may not fire at what its side cannot see, so hp and target
    differ from the switch-0 run (where it fires)."""
    off = unseen_in_range_hashes(lib, world_factory, 0.0)
    on = unseen_in_range_hashes(lib, world_factory, 1.0)
    assert off != on, "TARGET_BY_SIGHT 1 changed nothing on an in-range, unseen target"
