# spec: docs/northstar/plans/2026-10-01-architect-rulings-2.md A185 (Addendum 64): "the controls re-hashed at 1 and the difference reported"
"""G3: the A99 and F1/F2/F3 control scenes are re-run with OM_TP_TARGET_BY_SIGHT 1 (the default) and
compared with the same scenes at 0. How many differ is REPORTED (printed, and in the assertion message
of test_G3_rehash_report_completes), not asserted: the number is a finding for Westley, not a threshold.
Asserted: every scene completes, and the sparse open-ground scenes (every enemy in a unit's range is also
visible to its side) have identical hashes at 0 and 1. Positive control: the sparse scene really fights,
and a differing pair is detected as differing.
"""
import a99_tactical_runs as A
import test_F1_fog_per_faction_observers as F1
import test_F2_nearest_hostile_search as F2
import test_F3_macro_contact_skip as F3
from test_PP_C_g3_support import RAIDER, set_param, spawn, step

TBS = 4
A99_STEPS = 300  # first steps of each fast A99 run; the full-length runs are the invariant file's job


def _a99(lib, run, switch):
    _n, units, gap, _s, _t = run
    w = A.build(lib, units)
    assert lib.om_tactical_set_param(w, TBS, switch) == 0
    if gap is not None:
        A.stage_fight(lib, w, A._slots(lib, w), gap)
    out = []
    for _ in range(A99_STEPS):
        lib.om_tactical_step(w)
        out.append(A.state_hash(lib, w))
    lib.om_world_free(w)
    return out


def _golden_scene(lib, world_factory, mod, kind, switch, **kw):
    w = mod._world(lib, world_factory, 1, **kw)
    assert lib.om_tactical_set_param(w, TBS, switch) == 0
    return mod._full_run(lib, w, kind)


def _rehash(lib, world_factory_module):
    res = {}
    for run in [r for r in A.RUNS if r[4] == "fast"]:
        res[f"A99 {run[0]}"] = (_a99(lib, run, 0.0) != _a99(lib, run, 1.0))
    for kind in ("clash", "spread"):
        res[f"F1 {kind}"] = (_golden_scene(lib, world_factory_module, F1, kind, 0.0)
                             != _golden_scene(lib, world_factory_module, F1, kind, 1.0))
        res[f"F2 {kind}"] = (_golden_scene(lib, world_factory_module, F2, kind, 0.0, custom=False)
                             != _golden_scene(lib, world_factory_module, F2, kind, 1.0, custom=False))
        res[f"F3 {kind}"] = (_golden_scene(lib, world_factory_module, F3, kind, 0.0)
                             != _golden_scene(lib, world_factory_module, F3, kind, 1.0))
    return res


def test_G3_rehash_report_completes(lib, world_factory):
    rehash = _rehash(lib, world_factory)
    differing = sorted(k for k, v in rehash.items() if v)
    msg = (f"A185 rehash report: {len(differing)} of {len(rehash)} control scenes differ at "
           f"TARGET_BY_SIGHT 1 vs 0: {differing}")
    print(msg)
    assert len(rehash) == 12, msg  # 6 fast A99 runs + F1, F2, F3 at clash and spread


def _sparse(lib, world_factory, switch, ticks=100, pairs=10):
    """Open ground, one layer: Raider (range 200, sensor 800) pairs 150 wu apart, 2,000 wu between pairs.
    Every enemy in a unit's range is inside its own sensor, so its side sees it."""
    w = world_factory(n_regions=1)
    set_param(lib, w, "TARGET_BY_SIGHT", switch)
    ids = []
    for i in range(pairs):
        x, y = 1000.0 + (i % 5) * 2000.0, 1000.0 + (i // 5) * 2000.0
        ids += [spawn(lib, w, RAIDER, 0, x, y), spawn(lib, w, RAIDER, 1, x + 150.0, y)]
    hashes = []
    for _ in range(ticks):
        step(lib, w)
        hashes.append(A.state_hash(lib, w))
    hp = sum(lib.om_unit_get_hp(w, u) for u in ids)
    return hashes, hp, len(ids)


def test_G3_sparse_open_ground_scene_is_unchanged_at_1(lib, world_factory):
    """A185: where every enemy in range is also visible, sight targeting changes nothing."""
    h0, _hp0, _n0 = _sparse(lib, world_factory, 0.0)
    h1, _hp1, _n1 = _sparse(lib, world_factory, 1.0)
    assert h0 == h1, "sparse open-ground scene differs at TARGET_BY_SIGHT 1"


def test_G3_sparse_scene_positive_control_it_fights_and_hashes_can_differ(lib, world_factory):
    """The sparse scene is not trivially unchanged because nothing happens: hashes change over time."""
    h0, hp, n = _sparse(lib, world_factory, 0.0)
    assert hp < n * 250.0, "no damage dealt: the scene never engaged"  # Raider hp from csrc/om_constants.h
    assert len(set(h0)) > 1, "the sparse scene never changes state: the equality above proves nothing"
    assert h0[:50] != h0[50:100], "state frozen after the first 50 ticks"
