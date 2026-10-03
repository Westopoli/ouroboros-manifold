"""Phase C, step G3 with step G4's layer change: E-01 R-004-02 ("its sight") and R-004-04.

R-004-02 (the part about sight): "the transitioning unit itself attacks, in a timed transfer or on a
slope, as a unit of the layer it is leaving until it reaches the cross-over point (halfway through a timed
transfer ...) and as a unit of the layer it is moving to from then on; it attacks only a target its side
can see (S-005, R-008-04), and stops attacking a target the moment its side loses sight of it."
R-004-04: "Given a unit mid-transition, When a new hard transfer to another layer is issued, Then the unit
completes the current transition first and the new transfer becomes pending."

Both need om_command_set_layer, om_unit_transition_progress, om_unit_get_layer and
om_unit_get_target_layer (contract rows 5 to 7; today generated stubs: a transfer is accepted and does
nothing, the progress is always 0.0, the layer never changes). So the tests below are red today for TWO
reasons that arrive in different steps: the transition is not built (G4) and fire is not gated by sight
(G3). The first assertion of each names the transition, so the first red reason today is G4; once G4 is in,
the sight assertion is the one that must go green with G3. The R-004-04 test has no sight content and is
red on the stub alone; it is listed because the brief names it for Phase C (A143) and G4's writer may also
cover it (the report says so).

Timings used: a Bastion's transition takes 5.0 s = 100 ticks (R-004-01 'current config', provisional,
Q-004-01), so its cross-over is at tick 50 and a Bastion hits every 36 ticks (measured; first hit at tick
36), so a window before the cross-over holds a hit. A Raider's takes 1.0 s = 20 ticks.
"""
import ctypes

from test_PP_C_g3_support import (BASTION, BIG_HP, INTERCEPTOR, RAIDER, can_see, cohort_cycle, hp, inert, kill, spawn,
                                  step, target)


def _set_layer(lib, w, uid, layer):
    arr = (ctypes.c_uint32 * 1)(uid)
    return lib.om_command_set_layer(w, arr, 1, layer)


def _bastion_scene(lib, w, spotter):
    """A Bastion with a Supply 700 wu away (inside its range 800, outside its sensor 300). The spotter is an
    Interceptor 100 wu in front of it: sees the Supply at 600, cannot fire at it (range 250)."""
    bastion = spawn(lib, w, BASTION, 0, 0.0, 0.0)
    supply = inert(lib, w, 1, 700.0, 0.0)
    spot = spawn(lib, w, INTERCEPTOR, 0, 100.0, 0.0) if spotter else None
    assert can_see(lib, w, bastion, supply) == 0, "fixture: the Bastion must not see the target itself"
    if spot is not None:
        assert can_see(lib, w, spot, supply) == 1, "fixture: the spotter must see the target"
    return bastion, supply, spot


def _assert_mid_transition(lib, w, uid, why):
    progress = lib.om_unit_transition_progress(w, uid)
    assert 0.0 < progress < 1.0, f"{why}: not mid-transition (progress {progress}); the layer change is not built"
    assert lib.om_unit_get_layer(w, uid) == 0, f"{why}: before the cross-over it is still a layer-0 unit"


def test_R_004_02_a_transitioning_unit_attacks_what_its_side_sees_control(lib, world_factory):
    """Positive control for the two tests below: a Bastion ordered to layer 1 with a spotter alive is
    mid-transition at tick 20 and has hit the target by tick 49 (a Bastion hits every 36 ticks; first hit
    at 36; cross-over at tick 50): 'it attacks as a unit of the layer it is leaving until the cross-over'.
    Red today only on the transition (G4); the damage half is green today."""
    w = world_factory(n_regions=1)
    bastion, supply, _ = _bastion_scene(lib, w, spotter=True)
    assert _set_layer(lib, w, bastion, 1) == 0
    step(lib, w, 20)
    _assert_mid_transition(lib, w, bastion, "tick 20")

    step(lib, w, 29)

    assert hp(lib, w, supply) < BIG_HP, "a transitioning unit must fire as a unit of the layer it is leaving"


def test_R_004_02_a_transitioning_unit_does_not_fire_at_what_its_side_cannot_see(lib, world_factory):
    """R-004-02, R-008-04: the same Bastion and order with NO spotter: its side sees nothing of the target,
    so through ticks 1 to 49 (before the cross-over at 50, so it still fires as a layer-0 unit) no damage
    lands and it holds no target. Red today: the layer change is a stub (the mid-transition check), then
    once G4 is built the hit at tick 36 lands (G3 not built)."""
    w = world_factory(n_regions=1)
    bastion, supply, _ = _bastion_scene(lib, w, spotter=False)
    assert _set_layer(lib, w, bastion, 1) == 0
    step(lib, w, 20)
    _assert_mid_transition(lib, w, bastion, "tick 20")

    for tick in range(21, 50):
        step(lib, w)
        assert hp(lib, w, supply) == BIG_HP, f"damage landed at tick {tick} from a unit whose side sees nothing"
        assert target(lib, w, bastion) != supply


def test_R_004_02_a_transitioning_unit_stops_when_its_side_loses_sight(lib, world_factory):
    """R-004-02 ('stops attacking a target the moment its side loses sight of it'): the spotter dies at
    tick 20, before the Bastion's first hit (tick 36) and before the cross-over (tick 50): no damage lands
    on any tick from 21 to 49, and the target is dropped within one cohort cycle. Red today as above."""
    w = world_factory(n_regions=1)
    bastion, supply, spotter = _bastion_scene(lib, w, spotter=True)
    assert _set_layer(lib, w, bastion, 1) == 0
    step(lib, w, 20)
    _assert_mid_transition(lib, w, bastion, "tick 20")

    kill(lib, w, spotter)
    cycle = cohort_cycle(lib, w)
    for tick in range(21, 50):
        step(lib, w)
        assert hp(lib, w, supply) == BIG_HP, f"damage landed at tick {tick}, after its side lost sight"
        if tick == 20 + cycle:
            assert target(lib, w, bastion) != supply, f"still holding the target {cycle} ticks after sight was lost"


def _layer_sequence(lib, w, uid, ticks, seen=None):
    """The unit's layer, one entry per change, over `ticks` ticks (continues `seen` when given)."""
    seen = seen if seen is not None else [lib.om_unit_get_layer(w, uid)]
    for _ in range(ticks):
        step(lib, w)
        layer = lib.om_unit_get_layer(w, uid)
        if layer != seen[-1]:
            seen.append(layer)
    return seen


def test_R_004_04_a_new_transfer_waits_for_the_current_one_control(lib, world_factory):
    """Positive control for the next test: a Raider ordered 0 to 1 and left alone ends on layer 1, settled
    (progress 0.0), its layer sequence 0 then 1. Red today: the transfer is a stub and the layer never
    changes (G4)."""
    w = world_factory(n_regions=1)
    raider = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    assert _set_layer(lib, w, raider, 1) == 0

    seen = _layer_sequence(lib, w, raider, 100)

    assert seen == [0, 1], f"layer sequence {seen}, want [0, 1]"
    assert lib.om_unit_transition_progress(w, raider) == 0.0


def test_R_004_04_a_new_transfer_waits_for_the_current_one(lib, world_factory):
    """R-004-04: a Raider ordered 0 to 1 is hit with a new order to layer 2 five ticks in (mid-transition:
    a Raider's takes 20 ticks). It completes the first transition and only then starts the second: its
    target layer is still 1 right after the second order (the new transfer is pending), its layer sequence
    is 0, 1, 2 (never straight from 0 to 2, which is what 'replace' would give), and it ends settled on 2.
    Red today: the layer change is a stub (G4); it fails there on the first layer-1 check."""
    w = world_factory(n_regions=1)
    raider = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    assert _set_layer(lib, w, raider, 1) == 0
    seen = _layer_sequence(lib, w, raider, 5)
    assert 0.0 < lib.om_unit_transition_progress(w, raider) < 1.0, "fixture: not mid-transition after 5 ticks (G4)"

    assert _set_layer(lib, w, raider, 2) == 0
    assert lib.om_unit_get_target_layer(w, raider) == 1, "the new transfer must be pending, not replace the first"
    _layer_sequence(lib, w, raider, 195, seen)

    assert seen == [0, 1, 2], f"layer sequence {seen}: the first transition must complete before the second"
    assert lib.om_unit_get_layer(w, raider) == 2
    assert lib.om_unit_transition_progress(w, raider) == 0.0
