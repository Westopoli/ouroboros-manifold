"""B1-1 (plan 2026-09-30, item B1): om_macro_tick must call
om_macro_eval_transitions per force each macro interval and apply the result.

RED on main: om_macro_tick never calls om_macro_eval_transitions, so a force
whose transition condition is met keeps its state forever; the evaluator
itself is already covered by test_E14_S121 and is not what is under test here.

The bible gives transitions no to_state in the C contract (see report note:
R-121-04 names a to_state but csrc has no slot for it), so these tests assert
only that the (behavior, modifier) pair CHANGED, never which state it became.
"""
from b1_macro_scene import OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS

INTERVAL = 40  # R-120-04, om_macro_evaluation_interval_ticks()


def _state(lib, w):
    return lib.om_macro_get_behavior(w, 0), lib.om_macro_get_modifier(w, 0)


def _fresh_force(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    return w


def test_R_121_04_tick_applies_a_true_hook_transition(lib, world_factory):
    """R-121-04: a hook whose expression is true makes the force transition at once; wired means om_macro_tick over a macro interval does it, not only the evaluator."""
    w = _fresh_force(lib, world_factory)
    before = _state(lib, w)
    lib.om_macro_set_hook_true(w, 0, 1)
    lib.om_macro_tick(w, INTERVAL)
    assert _state(lib, w) != before, "R-121-04: hook transition condition met, om_macro_tick left the force state unchanged"


def test_R_121_01_tick_applies_a_true_threshold_transition(lib, world_factory):
    """R-121-01: a threshold transition whose condition is met changes the force's state when the macro tick evaluates it."""
    w = _fresh_force(lib, world_factory)
    before = _state(lib, w)
    lib.om_macro_set_base_transition_true(w, 0, 1)
    lib.om_macro_tick(w, INTERVAL)
    assert _state(lib, w) != before, "R-121-01: threshold transition condition met, om_macro_tick left the force state unchanged"


def test_R_120_04_transition_waits_for_the_interval_boundary(lib, world_factory):
    """R-120-04: evaluation runs every 40 ticks. Control for the two tests above and a detector for a tick that transitions every call: a true condition changes nothing before the first boundary, and does once the boundary is crossed."""
    w = _fresh_force(lib, world_factory)
    before = _state(lib, w)
    lib.om_macro_set_hook_true(w, 0, 1)
    for t in range(1, INTERVAL):
        lib.om_macro_tick(w, t)
    assert _state(lib, w) == before, "R-120-04: state changed before the first 40-tick boundary"
    lib.om_macro_tick(w, INTERVAL)
    assert _state(lib, w) != before, "R-120-04: boundary crossed with a true condition, state unchanged"


def test_R_121_04_positive_control_no_condition_no_change(lib, world_factory):
    """Positive control: with neither hook nor threshold condition true, many macro intervals leave the state alone, so a change in the tests above is caused by the condition."""
    w = _fresh_force(lib, world_factory)
    before = _state(lib, w)
    for k in range(1, 6):
        lib.om_macro_tick(w, k * INTERVAL)
    assert lib.om_macro_has_evaluated(w) == 1
    assert _state(lib, w) == before
