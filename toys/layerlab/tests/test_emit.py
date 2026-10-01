"""Rung L2 tests (SPEC.md section 15.2, E-01 S-163): going dark, emit and silent.

The rule under test: with `rules.emit_on = 1`, `can_see` (SPEC 5.2 step 4) multiplies the effective radius by
`emit_see_mult[observer.emit] * emit_seen_mult[target.emit]` for a CROSS-LAYER pair and by 1.0 for a same-layer
pair. State 0 is silent, 1 emitting; the group keys `emit`, `emit_switch_tick`, `emit_switch_to` set it. Starting
tables: `emit_see_mult = [1.0, 1.5]`, `emit_seen_mult = [0.5, 1.5]`; they are written into every scenario here
that turns the rule on, so the tests do not depend on what base.toml happens to hold.

Numbers: an interceptor (sensor 1000) looking at an adjacent layer has base radius 1000 * 0.5 = 500 (R-005-02,
R-005-03), two layers 1000 * 0.2 = 200 (R-005-04), with `sensor_elev_bonus_per_layer = 0` as in test_vision.py.
Spawn jitter is 0 so distances are exact. Vision is read with `probe_can_see` where only geometry matters, with
the trace flag "visible to the other side" for the timed switches (SPEC 5.2 side vision, trace bit3), and with a
moving fight where the first shot depends on who sees whom.

State today: ll_emit.c is a neutral stub (factor 1.0, validation always ok), so the multiplier, switch, fight and
validation tests fail; the emit_on = 0 legacy test and the control cases named in their docstrings pass by design.
"""
import math

import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, fire_ticks, grp, make_scenario, table9, unit_trace

OBS_X, OBS_Y = 1000.0, 1000.0
SEE = [1.0, 1.5]       # emit_see_mult, indexed by the observer's state (0 silent, 1 emitting)
SEEN = [0.5, 1.5]      # emit_seen_mult, indexed by the target's state
EMIT_ON = {"spawn_jitter": 0.0, "sensor_elev_bonus_per_layer": 0.0, "emit_on": 1,
           "emit_see_mult": SEE, "emit_seen_mult": SEEN}
EMIT_OFF = {**EMIT_ON, "emit_on": 0}


def probe(obs_layer, tgt_layer, dist, obs_emit, tgt_emit, rules=EMIT_ON):
    """Interceptor observer (sensor 1000) at (1000, 1000), raider target `dist` along +x; the group `emit` keys
    set both states. Returns probe_can_see(observer=0, target=1)."""
    scn = make_scenario(
        [grp("A", "interceptor", OBS_X, OBS_Y, obs_layer, emit=obs_emit),
         grp("B", "raider", OBS_X + dist, OBS_Y, tgt_layer, emit=tgt_emit)],
        rules=dict(rules))
    return bool(runmod.probe_can_see(scn, 0, 1))


# ---- test 1: emit_on = 0 is the legacy behaviour ---------------------------------------------------------

STRIKER_X, WATCHER_X = 1600.0, 3000.0


def fight(a_kw=None, b_kw=None, rules=None):
    """The moving cross-layer fight used by tests 1, 6 and 7. B is a stationary 'watcher' on layer 4 (sensor 1000,
    range 1200, so what it sees is what it shoots); A is a slow 'striker' on layer 3 under attack_move (sensor
    1000, range 600) that walks toward the watcher, chases what it sees to within its range and stands. Both have
    5000 hp so nothing dies in the window. Cross-layer fire is on for offsets -1, 0, +1 (damage and range). Group
    keys in `a_kw` / `b_kw` (emit ...) pass through; absent keys mean the loader default."""
    on = table9(m1=1, z=1, p1=1)
    r = {"spawn_jitter": 0.0, "sensor_elev_bonus_per_layer": 0.0, "range_mult": on, "dmg_mult": on}
    r.update(rules or {})
    scn = make_scenario(
        [grp("A", "striker", STRIKER_X, OBS_Y, 3, order="attack_move", goal=[WATCHER_X, OBS_Y], **(a_kw or {})),
         grp("B", "watcher", WATCHER_X, OBS_Y, 4, **(b_kw or {}))],
        rules=r, run={"max_ticks": 700, "stalemate_ticks": 6000})
    add_type(scn, "striker", "raider", hp=5000.0, range=600.0, sensor=1000.0, speed=60.0)
    add_type(scn, "watcher", "interceptor", hp=5000.0, range=1200.0, sensor=1000.0, interval_s=1.0)
    return scn


def _bytes(res):
    return res.raw, np.ascontiguousarray(res.trace).tobytes()


def test_emit_off_ignores_group_states_and_matches_a_scenario_that_never_mentions_emit():
    """S-163, SPEC 15.2 ('with 0 ll_emit_factor is 1.0 everywhere'): with emit_on = 0 a fight whose groups say
    emit 0 and carry a scheduled switch gives byte-identical result and trace to the same fight that never
    mentions emit (the legacy scenario), even with the multiplier tables left at their starting values. The fight
    is not vacuous: both sides shoot (shots > 0). Passes today by design (the stub is neutral); it is the guard
    that the real factor must not leak when the rule is off."""
    legacy = runmod.run(fight(), seed=2, trace=True)
    off = runmod.run(
        fight(a_kw={"emit": 0, "emit_switch_tick": 100, "emit_switch_to": 1}, b_kw={"emit": 0},
              rules=EMIT_OFF),
        seed=2, trace=True)
    assert legacy.shots[0] > 0 and legacy.shots[1] > 0
    assert _bytes(off) == _bytes(legacy)


def test_emit_on_with_silent_groups_changes_the_fight():
    """S-163 (the twin that proves the detector can fail, for the test above): the same fight with emit_on = 1 and
    the striker silent is NOT byte-identical to the legacy fight. Red until the factor is wired."""
    legacy = runmod.run(fight(), seed=2, trace=True)
    on = runmod.run(fight(a_kw={"emit": 0}, b_kw={"emit": 1}, rules=EMIT_ON), seed=2, trace=True)
    assert _bytes(on) != _bytes(legacy)


# ---- test 2: the four cross-layer combinations --------------------------------------------------------

# (observer emit, target emit, multiplier): see[o] * seen[t]
COMBOS = [(1, 1, 1.5 * 1.5), (1, 0, 1.5 * 0.5), (0, 1, 1.0 * 1.5), (0, 0, 1.0 * 0.5)]


@pytest.mark.parametrize("tgt_layer", [4, 2], ids=["adjacent-up", "adjacent-down"])
@pytest.mark.parametrize("obs_emit,tgt_emit,mult", COMBOS)
def test_cross_layer_radius_is_scaled_by_both_states_adjacent(obs_emit, tgt_emit, mult, tgt_layer):
    """S-163, SPEC 15.2 and 5.2 step 4: observer on layer 3, target on an adjacent layer (base radius 500,
    R-005-02). Radius = 500 * see_mult[observer] * seen_mult[target]: emitting/emitting 2.25x = 1125,
    emitting/silent 0.75x = 375, silent/emitting 1.5x = 750, silent/silent 0.5x = 250. Each combination is
    visible 10 inside the scaled radius (positive) and not visible 10 outside it (negative)."""
    radius = 500.0 * mult
    assert probe(3, tgt_layer, radius - 10.0, obs_emit, tgt_emit) is True
    assert probe(3, tgt_layer, radius + 10.0, obs_emit, tgt_emit) is False


@pytest.mark.parametrize("obs_emit,tgt_emit,mult", COMBOS)
def test_cross_layer_radius_is_scaled_by_both_states_two_layers(obs_emit, tgt_emit, mult):
    """S-163, SPEC 15.2: the same four combinations two layers apart (base radius 200, R-005-04): the factor
    multiplies whatever the layer table gives. Visible at 10 inside 200 * mult, not at 10 outside."""
    radius = 200.0 * mult
    assert probe(3, 5, radius - 10.0, obs_emit, tgt_emit) is True
    assert probe(3, 5, radius + 10.0, obs_emit, tgt_emit) is False


@pytest.mark.parametrize("obs_emit,tgt_emit", [(c[0], c[1]) for c in COMBOS])
def test_emit_off_keeps_the_base_radius_for_every_state(obs_emit, tgt_emit):
    """S-163, SPEC 15.2 (negative control for the two tests above): with emit_on = 0 the same pair has the plain
    adjacent-layer radius 500 whatever the states: visible at 490, not at 510. Passes today by design; it shows the
    scaled radii above come from the switch, not from the geometry."""
    assert probe(3, 4, 490.0, obs_emit, tgt_emit, rules=EMIT_OFF) is True
    assert probe(3, 4, 510.0, obs_emit, tgt_emit, rules=EMIT_OFF) is False


# ---- test 3: same-layer pairs are unaffected -------------------------------------------------------------

@pytest.mark.parametrize("obs_emit,tgt_emit", [(c[0], c[1]) for c in COMBOS])
def test_same_layer_pair_ignores_emit_state(obs_emit, tgt_emit):
    """S-163, SPEC 15.2 ('1.0 for a same-layer pair'): observer and target both on layer 3, emit_on = 1: the
    radius is the plain sensor 1000 (R-005-01) in all four state combinations, so a silent target (and a silent
    observer) is seen at 990 and not at 1010. Control in the same rules (positive: emit_on is live and the test can
    fail): a silent target one layer up at 260, inside the plain adjacent radius 500, is NOT seen when the observer
    is silent (radius 250)."""
    assert probe(3, 3, 990.0, obs_emit, tgt_emit) is True
    assert probe(3, 3, 1010.0, obs_emit, tgt_emit) is False
    assert probe(3, 4, 260.0, 0, 0) is False


# ---- test 4: the scheduled switch --------------------------------------------------------------------

SWITCH = 40
SWITCH_RULES = {**EMIT_ON}


def _visible_series(a_kw, b_kw, dist, a_layer=3, b_layer=4):
    """Static pair on hold orders, 100 ticks, jitter 0. Returns the per-tick 'visible to the other side' flag of
    unit B (trace bit3: side A sees it), the cleanest per-tick observable of can_see (SPEC 5.2 side vision) that
    needs no weapons."""
    scn = make_scenario(
        [grp("A", "interceptor", OBS_X, OBS_Y, a_layer, **a_kw),
         grp("B", "raider", OBS_X + dist, OBS_Y, b_layer, **b_kw)],
        rules=dict(SWITCH_RULES), run={"max_ticks": 100, "stalemate_ticks": 6000})
    res = runmod.run(scn, seed=0, trace=True)
    return unit_trace(res, 1).visible


# (a_kw, b_kw, distance, seen before the switch, seen after). A silent observer sees an emitting target at 750 and
# a silent one at 250; an emitting observer sees an emitting target at 1125 and a silent one at 375.
SWITCH_CASES = [
    pytest.param({"emit": 0}, {"emit": 1, "emit_switch_tick": SWITCH, "emit_switch_to": 0}, 700.0, True, False,
                 id="target-emit-to-silent"),
    pytest.param({"emit": 0}, {"emit": 0, "emit_switch_tick": SWITCH, "emit_switch_to": 1}, 700.0, False, True,
                 id="target-silent-to-emit"),
    pytest.param({"emit": 1, "emit_switch_tick": SWITCH, "emit_switch_to": 0}, {"emit": 0}, 350.0, True, False,
                 id="observer-emit-to-silent"),
    pytest.param({"emit": 0, "emit_switch_tick": SWITCH, "emit_switch_to": 1}, {"emit": 1}, 1000.0, False, True,
                 id="observer-silent-to-emit"),
]


@pytest.mark.parametrize("a_kw,b_kw,dist,before,after", SWITCH_CASES)
def test_scheduled_switch_changes_visibility_at_the_switch_tick(a_kw, b_kw, dist, before, after):
    """S-163, SPEC 15.2 (one scheduled switch at emit_switch_tick, immediate, before vision in the tick). The
    observable is the trace flag 'visible to the other side' of the target (bit3, side A sees B), read per tick on
    a static cross-layer pair (A layer 3, B layer 4, hold, no damage). Target switching emit to silent at tick 40
    at distance 700 (needs the 1.5 multiplier: seen at 750 while emitting, 250 once silent): seen at ticks
    2..37, not seen at ticks 42..99. The three twins: silent to emit (the reverse), and the same two on the
    observer's state (emitting sees a silent target at 350 within 375, silent does not). A margin of two ticks
    each side of the switch leaves the off-by-one in when the trace samples open."""
    vis = _visible_series(a_kw, b_kw, dist)
    assert len(vis) == 100
    assert bool(vis[2:SWITCH - 2].all()) is before and bool(vis[2:SWITCH - 2].any()) is before
    assert bool(vis[SWITCH + 2:].all()) is after and bool(vis[SWITCH + 2:].any()) is after


def test_no_switch_keeps_the_state():
    """S-163, SPEC 15.2 (negative control for the switch tests): the target of the first switch case, with
    emit_switch_tick -1 (none) and emit_switch_to 0, stays emitting: seen on every tick from 2 to 99 at 700. The
    scheduled switch, not the passage of time, is what removes it. Red until the factor is wired (today it is
    unseen at 700 from the start)."""
    vis = _visible_series({"emit": 0}, {"emit": 1, "emit_switch_tick": -1, "emit_switch_to": 0}, 700.0)
    assert bool(vis[2:].all())


# ---- test 5: validation ------------------------------------------------------------------------------

def _probe_scn(a_kw=None, b_kw=None, rules=None):
    r = dict(EMIT_ON)
    r.update(rules or {})
    return make_scenario(
        [grp("A", "interceptor", OBS_X, OBS_Y, 3, **(a_kw or {})),
         grp("B", "raider", OBS_X + 300.0, OBS_Y, 4, **(b_kw or {}))],
        rules=r)


BAD = [
    pytest.param({"a_kw": {"emit": 2}}, id="emit-2"),
    pytest.param({"a_kw": {"emit": -1}}, id="emit-minus-1"),
    pytest.param({"b_kw": {"emit": 3}}, id="emit-3-on-b"),
    pytest.param({"a_kw": {"emit_switch_tick": 10, "emit_switch_to": 2}}, id="switch-to-2"),
    pytest.param({"a_kw": {"emit_switch_tick": 10, "emit_switch_to": -1}}, id="switch-to-minus-1"),
    pytest.param({"a_kw": {"emit_switch_tick": -2}}, id="switch-tick-minus-2"),
    pytest.param({"rules": {"emit_see_mult": [-0.1, 1.5]}}, id="see-negative"),
    pytest.param({"rules": {"emit_seen_mult": [0.5, -1.0]}}, id="seen-negative"),
    pytest.param({"rules": {"emit_see_mult": [1.0, math.nan]}}, id="see-nan"),
    pytest.param({"rules": {"emit_seen_mult": [math.inf, 1.5]}}, id="seen-inf"),
]


@pytest.mark.parametrize("kw", BAD)
def test_bad_emit_values_are_rejected_by_validation(kw):
    """S-163, SPEC 15.2 (ll_emit_validate: emit and emit_switch_to in {0, 1}; emit_switch_tick >= -1; multipliers
    finite and >= 0). Each bad value makes the run fail validation: RuntimeError whose message names emit and is
    not the 'unimplemented' stub, as the pulse validation test asserts. emit_on is 1 so the rule is live. Red until
    ll_emit_validate exists. Needs the C error text to contain 'emit'."""
    scn = _probe_scn(**kw)
    with pytest.raises(RuntimeError, match="emit") as exc:
        runmod.probe_can_see(scn, 0, 1)
    assert "unimplemented" not in str(exc.value)
    with pytest.raises(RuntimeError, match="emit"):
        runmod.run(scn, seed=0)


def test_edge_emit_values_are_accepted():
    """S-163, SPEC 15.2 (positive control for the rejections above): the edges of the allowed set run fine: emit 0
    and 1, emit_switch_tick -1 and 0 and 500, switch_to 0 and 1, multipliers 0.0 and large finite values. Passes
    today by design (the stub accepts everything); it keeps the validator from becoming too strict."""
    scn = _probe_scn(a_kw={"emit": 0, "emit_switch_tick": 0, "emit_switch_to": 1},
                     b_kw={"emit": 1, "emit_switch_tick": 500, "emit_switch_to": 0},
                     rules={"emit_see_mult": [0.0, 100.0], "emit_seen_mult": [0.0, 100.0]})
    runmod.probe_can_see(scn, 0, 1)
    scn2 = _probe_scn(a_kw={"emit_switch_tick": -1, "emit_switch_to": 1})
    runmod.probe_can_see(scn2, 0, 1)


# ---- test 6: the positive control for the whole feature ---------------------------------------------------

def test_silent_striker_closes_unseen_and_shoots_first_where_an_emitting_one_is_shot_first():
    """S-163, SPEC 15.2 (positive control for the whole rule; cross-layer fight, jitter 0, seed 3). Watcher B on
    layer 4 emits (see 1.5); it sees an EMITTING striker at 500 * 1.5 * 1.5 = 1125 and a SILENT striker at
    500 * 1.5 * 0.5 = 375. Striker A on layer 3 (range 600, sensor 1000, walks at 60 per second under attack_move
    from 1400 away) sees the emitting watcher at 1125 and, silent itself, still sees it at 500 * 1.0 * 1.5 = 750,
    then stands at its range 600 and fires. Twin 1, striker emitting: the watcher (range 1200) is shooting at 1125
    while the striker is still closing, so the watcher's first shot comes at least 100 ticks before the
    striker's and first_shot_side is B. Twin 2, striker silent: it stops at about 600, outside the 375 at which the
    watcher sees it, so the striker shoots first (first_shot_side A) and the watcher never fires a shot at all
    (shots[1] == 0, damage_dealt[1] == 0): the observer fires later (never) in the window than in twin 1."""
    twin = runmod.run(fight(a_kw={"emit": 1}, b_kw={"emit": 1}, rules=EMIT_ON), seed=3, trace=True)
    silent = runmod.run(fight(a_kw={"emit": 0}, b_kw={"emit": 1}, rules=EMIT_ON), seed=3, trace=True)

    tw_b, tw_a = fire_ticks(twin, 1), fire_ticks(twin, 0)
    assert tw_b.size and tw_a.size, "twin: both sides should fire in the window"
    assert tw_b[0] + 100 <= tw_a[0], "twin: the watcher should shoot at the emitting striker long before it shoots back"
    assert twin.first_shot_side == 1

    si_a = fire_ticks(silent, 0)
    assert si_a.size, "silent: the striker should reach its range and fire"
    assert silent.first_shot_side == 0
    assert silent.shots[1] == 0 and silent.damage_dealt[1] == 0.0
    assert silent.damage_dealt[0] > 0.0
    assert twin.shots[1] > 0, "the watcher can shoot when it sees (positive control)"


# ---- test 7: determinism -----------------------------------------------------------------------------

def test_emit_scenario_is_byte_identical_across_O0_and_O2():
    """S-163, SPEC 9 / E-01 R-004-05 (determinism across builds) on an emit scenario: the moving fight with
    emit_on = 1, a silent striker that goes loud at tick 250 and a watcher that goes silent at tick 400 gives the
    same result bytes and the same trace bytes on the O0 and O2 libraries for seeds 0, 1 and 7. Also not vacuous:
    the same scenario with emit_on = 0 gives different result bytes (red until the factor is wired)."""
    scn = fight(a_kw={"emit": 0, "emit_switch_tick": 250, "emit_switch_to": 1},
                b_kw={"emit": 1, "emit_switch_tick": 400, "emit_switch_to": 0}, rules=EMIT_ON)
    for seed in (0, 1, 7):
        a = runmod.run(scn, seed=seed, trace=True, lib="O0")
        b = runmod.run(scn, seed=seed, trace=True, lib="O2")
        assert _bytes(a) == _bytes(b), "emit scenario differs O0 vs O2 at seed %d" % seed
    off = fight(a_kw={"emit": 0, "emit_switch_tick": 250, "emit_switch_to": 1},
                b_kw={"emit": 1, "emit_switch_tick": 400, "emit_switch_to": 0}, rules=EMIT_OFF)
    assert runmod.run(off, seed=0).raw != runmod.run(scn, seed=0).raw
