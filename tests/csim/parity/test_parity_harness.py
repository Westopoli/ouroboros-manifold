"""Proof that the parity harness itself is sound: the fixture resets the Python's globals, the Python
draws no unseeded random, the two engines are fed the same stats, the comparator trips on a
perturbed trace and passes an identical one, and the proposed tolerance is backed by the
measurement it came from. These tests are GREEN today by design; the red tests are in
test_parity_scenes.py. Plan: docs/northstar/plans/2026-10-02-movement-layers-and-search-plan.md,
Phase A "Verification" 1. Rules the scenes prove are named in that file; this file proves the
instrument (CLAUDE.md "Every detector ships with a positive control").
"""
import copy
import math

import pytest

from . import parity_c
from . import parity_python
from .parity_compare import Trace, TWO_PI, compare
from .parity_scenes import CUSTOM_TYPES, SCENES, SIX
from .parity_tolerance import PARITY_FACING_TOLERANCE, PARITY_TOLERANCE


def _frames_equal(a, b):
    return a.frames == b.frames


# ---- the Python fixture -----------------------------------------------------------------------

def test_python_module_state_is_all_covered_by_the_reset():
    """Every piece of module-level mutable state the Python's tick path carries (found by reading the
    source) is on the reset list: a new global in damage.py, facing.py, movement.py, command.py or
    anywhere else on the path fails here instead of silently leaking between scenes."""
    found = parity_python.audit_state()
    assert found == parity_python.RESET_COVERS, (
        "module-level state in simulation/ differs from what parity_python.reset_globals resets: "
        "found %r, reset covers %r" % (found, parity_python.RESET_COVERS))


def test_python_runs_repeat_exactly_after_the_reset():
    """The same scene run twice, back to back, gives identical traces (the reset leaves nothing behind)."""
    scene = SCENES["target_walks_out_of_range"]
    first = parity_python.run_scene(scene)
    second = parity_python.run_scene(scene)
    assert _frames_equal(first, second)


def test_positive_control_unreset_globals_change_the_trace():
    """Control for the reset: with the targeting clock left at a stale value (reset=False) the same
    scene gives a different trace, so the reset is not decoration."""
    scene = SCENES["target_walks_out_of_range"]
    fresh = parity_python.run_scene(scene)
    ns = parity_python.load("stock")
    ns.damage._targeting_tick = 1          # as if a previous scene had run 1 tick (cohort phase shifted)
    stale = parity_python.run_scene(scene, reset=False)
    rep = compare(fresh, stale, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    assert not rep.passes() and rep.first_target is not None, "a stale cohort clock did not change the trace"


def test_python_draws_no_unseeded_random_in_any_scene():
    """Every module-level random draw is replaced by one that raises while a scene runs, and every
    scene runs to the end. (The Python's only unseeded draw is reinforcement.py:69-70, reachable only
    with reinforcement structures, which no scene has.)"""
    for scene in SCENES.values():
        parity_python.run_scene(scene)      # raises AssertionError on any draw


def test_positive_control_a_random_draw_is_caught():
    import random
    with parity_python._forbid_global_random():
        with pytest.raises(AssertionError):
            random.random()


# ---- the C driver and the two engines' inputs -------------------------------------------------

def test_both_engines_start_from_the_same_scene():
    """Frame 0 of the Python and the C traces is the spawn state of the scene, unit for unit."""
    parity_c.build()
    for scene in SCENES.values():
        py = parity_python.run_scene(scene)
        c = parity_c.run_scene(scene)
        assert len(py.frames) == len(c.frames) == scene.ticks + 1
        for uid, (type_name, faction, x, y) in enumerate(scene.units):
            assert py.frames[0][uid][:3] == (True, x, y), (scene.name, uid)
            assert c.frames[0][uid][:3] == (True, x, y), (scene.name, uid)


def test_unit_stats_are_the_same_in_both_engines():
    """Every unit type the scenes use has the same stats in the Python (simulation/config.py,
    UNIT_STATS) and the C (csrc/unit.c profiles), so a divergence is behaviour, not data."""
    parity_c.build()
    keys = ("hp", "base_damage", "attack_interval", "attack_range", "speed", "sensor_radius",
            "layer_transition_time", "aoe_radius")
    used = sorted({u[0] for s in SCENES.values() for u in s.units})
    for type_name in used:
        py = parity_python.python_stats(type_name)
        c = parity_c.type_stats(type_name)
        for k in keys:
            assert c[k] == py[k], "%s %s: python %r c %r" % (type_name, k, py[k], c[k])


def test_positive_control_a_changed_stat_is_noticed():
    parity_c.build()
    py = dict(parity_python.python_stats("Raider"))
    py["attack_range"] += 1.0
    assert parity_c.type_stats("Raider")["attack_range"] != py["attack_range"]


def test_c_runs_repeat_exactly():
    """The C trace of a scene is the same on every run (determinism is a contract; the harness adds no noise)."""
    parity_c.build()
    scene = SCENES["attack_move_group_of_8"]
    assert _frames_equal(parity_c.run_scene(scene), parity_c.run_scene(scene))


def test_the_c_driver_really_drives_the_c():
    """Control: an extra order injected into the C between steps changes the C trace, so the trace
    is read from the live library and not replayed from a copy of the Python's."""
    parity_c.build()
    scene = SCENES["control_lone_march"]
    plain = parity_c.run_scene(scene)

    def hook(h, w, tick):
        if tick == 10:
            import ctypes
            ids = (ctypes.c_uint32 * 1)(1)
            h.om_command_move(w, ids, 1, 1000.0, 3000.0)
    pushed = parity_c.run_scene(scene, hook=hook)
    assert not _frames_equal(plain, pushed)
    assert pushed.frames[60][0][2] > plain.frames[60][0][2] + 100.0   # it turned toward +y


def test_control_scenes_line_up_apart_from_c_trig():
    """The two control marches (no port gap in play) agree in shape, target and alive state on every
    tick, and in facing within PARITY_FACING_TOLERANCE; their position deviation is the C's own trig
    error (om_atan2/om_cos), reported by measure.py (2.5e-5 wu along x, 4.7e-3 wu on the diagonal over
    60 ticks) and removed by the plan's fixed direction vectors, so it is not asserted here."""
    parity_c.build()
    for name in ("control_lone_march", "control_diagonal_march"):
        scene = SCENES[name]
        rep = compare(parity_python.run_scene(scene), parity_c.run_scene(scene),
                      PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
        assert not rep.shape_error and rep.first_target is None and rep.first_alive is None, name
        assert rep.first_facing is None, (name, rep.first_facing)


# ---- the comparator ---------------------------------------------------------------------------

def _base():
    return parity_python.run_scene(SCENES["target_walks_out_of_range"])


def _perturbed(trace, tick, uid, **delta):
    t = copy.deepcopy(trace)
    alive, x, y, tgt, face = t.frames[tick][uid]
    t.frames[tick][uid] = (delta.get("alive", alive), x + delta.get("dx", 0.0), y + delta.get("dy", 0.0),
                           delta.get("target", tgt), (face + delta.get("dface", 0.0)) % TWO_PI)
    return t


def test_comparator_passes_identical_traces():
    base = _base()
    rep = compare(base, copy.deepcopy(base), PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    assert rep.passes() and rep.max_pos == 0.0 and rep.max_facing == 0.0 and rep.first_divergence() is None


def test_positive_control_perturbed_position_trips_the_comparator():
    base = _base()
    bad = _perturbed(base, 37, 1, dx=PARITY_TOLERANCE * 2)
    rep = compare(base, bad, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    assert not rep.passes()
    assert rep.first_divergence() == (37, "position") and rep.first_pos[:2] == (37, 1)
    # the same perturbation in the other argument order, and on the C side of a real C trace:
    rep2 = compare(bad, base, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    assert rep2.first_divergence() == (37, "position")


def test_positive_control_a_perturbed_c_trace_trips_the_comparator():
    parity_c.build()
    scene = SCENES["control_lone_march"]
    c = parity_c.run_scene(scene)
    bad = _perturbed(c, 20, 0, dy=PARITY_TOLERANCE * 3)
    assert compare(c, c, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).passes()
    rep = compare(c, bad, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    assert rep.first_divergence() == (20, "position")


def test_comparator_allows_a_deviation_inside_the_tolerance():
    base = _base()
    ok = _perturbed(base, 12, 0, dx=PARITY_TOLERANCE * 0.5)
    assert compare(base, ok, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).passes()


def test_positive_control_target_alive_and_facing_trip_the_comparator():
    base = _base()
    assert compare(base, _perturbed(base, 9, 0, target=5), PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).first_target[:2] == (9, 0)
    assert compare(base, _perturbed(base, 9, 1, alive=False), PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).first_alive == (9, 1)
    assert compare(base, _perturbed(base, 9, 0, dface=PARITY_FACING_TOLERANCE * 2),
                   PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).first_facing[:2] == (9, 0)


def test_comparator_facing_wraps_at_two_pi():
    """Facing 0.0001 and 2 pi - 0.0001 are 0.0002 rad apart, not 6.28."""
    a = Trace("w", "x", [[(True, 0.0, 0.0, -1, 0.0001)]])
    b = Trace("w", "x", [[(True, 0.0, 0.0, -1, TWO_PI - 0.0001)]])
    rep = compare(a, b, PARITY_TOLERANCE, 0.001)
    assert rep.passes() and math.isclose(rep.max_facing, 0.0002, rel_tol=1e-6)


def test_positive_control_shape_mismatch_is_caught():
    base = _base()
    short = Trace(base.scene, "x", base.frames[:-1])
    assert compare(base, short, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).shape_error
    fewer = Trace(base.scene, "x", [f[:1] for f in base.frames])
    assert compare(base, fewer, PARITY_TOLERANCE, PARITY_FACING_TOLERANCE).shape_error


# ---- the tolerance is backed by its measurement -----------------------------------------------

@pytest.mark.parametrize("digits", [None, 12, 10, 8])
def test_fixed_direction_vectors_stay_inside_the_tolerance(digits):
    """Python with the sweep done by fixed direction vectors (plan P8), constants to `digits` decimals
    (None = full double), against the Python with trig: within PARITY_TOLERANCE and
    PARITY_FACING_TOLERANCE on every tick of every scene. Measured by measure.py --tolerance."""
    for scene in SCENES.values():
        ref = parity_python.run_scene(scene)
        rep = compare(ref, parity_python.run_scene(scene, "fixed", digits), PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
        assert rep.passes(), (scene.name, digits, rep.max_pos, rep.max_facing)


def test_positive_control_coarse_fixed_vectors_exceed_the_tolerance():
    """Control for the tolerance: constants rounded to 4 decimals move a unit by more than
    PARITY_TOLERANCE in at least one scene, so the tolerance is not so loose that nothing could fail."""
    worst = 0.0
    for name in SIX:
        scene = SCENES[name]
        rep = compare(parity_python.run_scene(scene), parity_python.run_scene(scene, "fixed", 4), 0.0, 0.0)
        worst = max(worst, rep.max_pos)
    assert worst > PARITY_TOLERANCE


def test_the_six_scenes_do_not_depend_on_collision_pair_order():
    """The Python takes collision pairs by grid cell, the C by id. In the six scenes reversing the
    Python's own pair order changes nothing beyond PARITY_TOLERANCE, so a divergence there cannot be
    blamed on pair order."""
    for name in SIX:
        scene = SCENES[name]
        rep = compare(parity_python.run_scene(scene), parity_python.run_scene(scene, "order_rev"),
                      PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
        assert rep.passes(), (name, rep.max_pos)


def test_positive_control_a_pile_up_does_depend_on_collision_pair_order():
    """Finding, pinned: in a pile-up (crowd_converges: eight units sent to one point) reversing the
    pair order moves units by far more than PARITY_TOLERANCE (124 wu measured), so exact parity through
    a dense pile-up needs the C to take pairs in the Python's order; the six scenes avoid pile-ups."""
    scene = SCENES["crowd_converges"]
    rep = compare(parity_python.run_scene(scene), parity_python.run_scene(scene, "order_rev"),
                  PARITY_TOLERANCE, PARITY_FACING_TOLERANCE)
    assert rep.max_pos > PARITY_TOLERANCE * 1000
