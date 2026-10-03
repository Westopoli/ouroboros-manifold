"""PP-fog Phase C, brief G6 "Going dark": emission mode, the sight multiplier and the seen-from multiplier
(E-01 S-163 R-163-01 to R-163-03, with R-005-02 to R-005-05 as the baseline numbers; contract
docs/northstar/plans/push/pp_contract.md rows 10 and 11, settings OM_TP_EMIT_SIGHT_MULT and OM_TP_EMIT_SEEN_MULT).

What the brief says (section 5, G6, quoted): "A unit is silent or emitting. Silent is the default and is exactly
today's behaviour. Switching costs nothing and takes effect on the next tick. An emitting observer's cross-layer
vision factors are multiplied by OM_TP_EMIT_SIGHT_MULT; the result is capped at 1.0. An emitting unit is seen from
other layers as if the observer's cross-layer factor were multiplied by OM_TP_EMIT_SEEN_MULT, capped at 1.0.
Same-layer sight is unchanged in both directions." Its test numbers: observer sensor 1000, silent: an enemy one
layer up is seen at 400 and not at 600; the observer emitting sees it at 600; a silent observer sees an emitting
enemy one layer up at 600; both silent, unchanged. The engine default of both multipliers is 1.0 (brief section 6),
so the tests that expect an effect set them to the lab's 2.0 (a provisional number, set here only as a lever).

Layers are engine layers 0 to 4 (A132). The observer is an Interceptor (sensor radius 1,000, om_constants.h).

Open flag, not decided here: Q-163-01 (whether same-layer sight changes when a force emits). The brief says it does
not; the same-layer tests below follow the brief and would change with the register's answer.

Today's inert stubs (csrc/fog.c): om_command_set_emission returns 0 and stores nothing, om_unit_get_emission returns
0 for every unit, and nothing in the sight rule reads either multiplier. So the mode tests fail on the readback
(get returns 0 after a set to ACTIVE) and on the invalid-mode return (a stub returns 0, the contract says -1), and the
sight tests fail where an emitting unit must see or be seen further (600 is not visible). Every "unchanged" test and
every baseline is a positive control that passes today."""
import pytest

from conftest import OMEmission
from test_PP_C_g67_support import (INTERCEPTOR, SUPPLY, can_see, emission, place, set_emission, set_param,
                                   sees_at, spawn, step)

OBS = INTERCEPTOR  # sensor radius 1,000


@pytest.fixture
def pair(lib, world_factory):
    """(world, observer, enemies): observer faction 0 on engine layer 2, silent; `enemies[layer]` is a silent
    faction 1 Supply unit (never fires) spawned on that layer, parked far away until a test places it. A unit's layer
    is fixed at spawn (om_unit_teleport ignores its layer argument), hence one enemy per layer."""
    w = world_factory(n_regions=1)
    obs = spawn(lib, w, OBS, 0, 0.0, 0.0, 2)
    enemies = {layer: spawn(lib, w, SUPPLY, 1, 9000.0 + 100.0 * layer, 0.0, layer) for layer in range(5)}
    return w, obs, enemies


# ---- the emission mode (R-163-03, contract rows 10 and 11) ----

def test_R_163_02_silent_is_the_default_for_every_unit(lib, world_factory):
    """R-163-02 / brief G6: silent is the default. A new unit of either side reads emission 0. (Control: passes today.)"""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, OBS, 0, 0.0, 0.0)
    b = spawn(lib, w, SUPPLY, 1, 500.0, 0.0)
    assert emission(lib, w, a) == OMEmission.SILENT
    assert emission(lib, w, b) == OMEmission.SILENT


def test_R_163_03_set_emission_reads_back_per_unit_and_switches_both_ways(lib, world_factory):
    """R-163-03: the player switches a force between emitting and silent. A listed unit reads ACTIVE, an unlisted
    one stays SILENT, and switching back reads SILENT; every set returns 0. Per list of ids (the brief's signature),
    which settles the per-unit half of Q-005-04's 'per unit or per group'."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, OBS, 0, 0.0, 0.0)
    b = spawn(lib, w, OBS, 0, 100.0, 0.0)
    c = spawn(lib, w, OBS, 0, 200.0, 0.0)
    assert set_emission(lib, w, [a, b], OMEmission.ACTIVE) == 0
    assert [emission(lib, w, u) for u in (a, b, c)] == [1, 1, 0]
    assert set_emission(lib, w, [b], OMEmission.SILENT) == 0
    assert [emission(lib, w, u) for u in (a, b, c)] == [1, 0, 0]


def test_R_163_03_the_mode_persists_across_ticks(lib, world_factory):
    """Brief G6: 'takes effect on the next tick', and stays until switched back."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, OBS, 0, 0.0, 0.0)
    assert set_emission(lib, w, [a], OMEmission.ACTIVE) == 0
    step(lib, w, 1)
    assert emission(lib, w, a) == OMEmission.ACTIVE
    step(lib, w, 30)
    assert emission(lib, w, a) == OMEmission.ACTIVE


@pytest.mark.parametrize("bad_mode", [2, -1, 100])
def test_R_163_03_an_invalid_mode_is_refused_and_changes_nothing(lib, world_factory, bad_mode):
    """Contract section 6: 'OM_EMIT_SILENT (0) or OM_EMIT_ACTIVE (1). 0 ok; -1 for any other mode, nothing changed.'
    Positive control inside: a valid mode on the same unit returns 0 and reads back, so a call that returns -1 (or
    0) for everything cannot pass."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, OBS, 0, 0.0, 0.0)
    assert set_emission(lib, w, [a], bad_mode) == -1
    assert emission(lib, w, a) == OMEmission.SILENT
    assert set_emission(lib, w, [a], OMEmission.ACTIVE) == 0
    assert set_emission(lib, w, [a], bad_mode) == -1
    assert emission(lib, w, a) == OMEmission.ACTIVE, "a refused mode must not clear the earlier valid one"


def test_R_163_03_unknown_ids_are_skipped_and_known_ones_still_set(lib, world_factory):
    """Contract section 6: 'Unknown ids skipped.' A list with an unknown id and a live one: returns 0, the live one is
    set. An unknown unit reads emission 0 (contract: 'the unit's mode; 0 for an unknown unit')."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, OBS, 0, 0.0, 0.0)
    assert set_emission(lib, w, [999999, a], OMEmission.ACTIVE) == 0
    assert emission(lib, w, a) == OMEmission.ACTIVE
    assert emission(lib, w, 999999) == 0
    assert emission(lib, w, 0) == 0


# ---- the baseline: silent, exactly today's numbers (R-005-02 to R-005-05, brief G6 test) ----

@pytest.mark.parametrize("dist,expected", [(400.0, 1), (500.0, 1), (600.0, 0)])
@pytest.mark.parametrize("target_layer", [3, 1])
def test_control_R_005_02_silent_cross_layer_baseline(lib, pair, dist, expected, target_layer):
    """Positive control (passes today): both silent, one layer apart (factor 0.50, effective radius 500), up (layer 3)
    or down (layer 1, R-005-05 symmetry): seen at 400 and at 500, not at 600."""
    w, obs, enemies = pair
    assert sees_at(lib, w, obs, enemies[target_layer], dist) == expected


@pytest.mark.parametrize("dist,expected", [(150.0, 1), (200.0, 1), (250.0, 0)])
def test_control_R_005_04_silent_two_layers_baseline(lib, pair, dist, expected):
    """Positive control (passes today): two layers apart (factor 0.20, effective radius 200)."""
    w, obs, enemies = pair
    assert sees_at(lib, w, obs, enemies[4], dist) == expected


# ---- an emitting observer sees further across layers (R-163-01, brief G6) ----

def test_R_163_01_emitting_observer_sees_one_layer_away_at_600(lib, pair):
    """Brief G6 test: observer sensor 1000, silent: enemy one layer up seen at 400, not at 600 (today); emitting
    (sight multiplier 2.0: factor 0.50 x 2.0 = 1.0, effective radius 1,000): seen at 600. The next-tick rule: the
    switch is made, one tick runs, then sight is read."""
    w, obs, enemies = pair
    up = enemies[3]
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    assert sees_at(lib, w, obs, up, 600.0) == 0, "silent observer must not see 600 away (today's rule)"
    assert set_emission(lib, w, [obs], OMEmission.ACTIVE) == 0
    step(lib, w, 1)
    assert sees_at(lib, w, obs, up, 400.0) == 1
    assert sees_at(lib, w, obs, up, 600.0) == 1, "R-163-01: an emitting force sees other layers further"


def test_R_163_01_emitting_observer_sees_downward_too(lib, pair):
    """R-005-05 symmetry carries over: an emitting observer sees a layer below at 600 as well."""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    set_emission(lib, w, [obs], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[1], 600.0) == 1


def test_R_163_01_the_sight_multiplier_value_is_what_scales_the_factor(lib, pair):
    """EMIT_SIGHT_MULT 1.5: one layer away the factor is 0.50 x 1.5 = 0.75, so sight reaches 750 and not 760; two
    layers away 0.20 x 1.5 = 0.30, so 300 and not 310. Detects an implementation that is on/off only."""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SIGHT_MULT", 1.5)
    set_emission(lib, w, [obs], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 740.0) == 1
    assert sees_at(lib, w, obs, enemies[3], 760.0) == 0
    assert sees_at(lib, w, obs, enemies[4], 290.0) == 1
    assert sees_at(lib, w, obs, enemies[4], 310.0) == 0


def test_R_163_01_the_emitting_factor_is_capped_at_1(lib, pair):
    """Brief G6: 'the result is capped at 1.0'. Multiplier 4.0: one layer away 0.50 x 4.0 = 2.0 caps to 1.0, so sight
    reaches 1,000 and not 1,010 (an uncapped 2.0 would reach 2,000); two layers away 0.20 x 4.0 = 0.8, reach 800 not
    810 (under the cap, so the control for 'the cap does not bite early')."""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SIGHT_MULT", 4.0)
    set_emission(lib, w, [obs], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 990.0) == 1
    assert sees_at(lib, w, obs, enemies[3], 1010.0) == 0
    assert sees_at(lib, w, obs, enemies[4], 790.0) == 1
    assert sees_at(lib, w, obs, enemies[4], 810.0) == 0


def test_R_163_01_default_multipliers_make_emitting_a_no_op(lib, pair):
    """Brief section 6: engine default of both multipliers is 1.0, 'no effect until set'. Emitting with the defaults
    leaves 600 unseen. (Control: passes today, and must keep passing once the mode exists.)"""
    w, obs, enemies = pair
    set_emission(lib, w, [obs], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 600.0) == 0


def test_R_163_01_emitting_does_not_bring_three_layers_into_sight(lib, world_factory):
    """R-005-05: a pair three or more layers apart is never visible by passive detection. The vision factor there is
    0.0, and 0.0 x any multiplier is 0.0: an emitting observer still does not see three layers away, at any distance.
    (Reading of the brief's 'multiplied'; the contract's VISION_UP_3 and DOWN_3 default to 0.0.) Control inside (fails
    today): the same observer sees a unit one layer up at 600 once emitting, so the emitting factor is live."""
    w = world_factory(n_regions=1)
    low = spawn(lib, w, OBS, 0, 0.0, 0.0, 0)
    far = spawn(lib, w, SUPPLY, 1, 9000.0, 0.0, 3)
    near = spawn(lib, w, SUPPLY, 1, 9100.0, 0.0, 1)
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    set_param(lib, w, "EMIT_SEEN_MULT", 2.0)
    set_emission(lib, w, [low, far, near], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, low, near, 600.0) == 1
    assert sees_at(lib, w, low, far, 10.0) == 0


def test_R_163_03_switching_back_to_silent_restores_today_s_sight(lib, pair):
    """R-163-03: switching is free and reversible. Emitting sees 600; after switching back (next tick) it does not."""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    set_emission(lib, w, [obs], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 600.0) == 1
    set_emission(lib, w, [obs], OMEmission.SILENT)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 600.0) == 0


# ---- an emitting unit is seen from further across layers (R-163-01) ----

def test_R_163_01_a_silent_observer_sees_an_emitting_enemy_one_layer_up_at_600(lib, pair):
    """Brief G6 test: 'a silent observer sees an emitting enemy one layer up at 600'. Seen-from multiplier 2.0: the
    observer's factor 0.50 x 2.0 = 1.0. The observer stays silent. Control inside: before the enemy emits it is not
    seen at 600."""
    w, obs, enemies = pair
    up = enemies[3]
    set_param(lib, w, "EMIT_SEEN_MULT", 2.0)
    assert sees_at(lib, w, obs, up, 600.0) == 0
    assert set_emission(lib, w, [up], OMEmission.ACTIVE) == 0
    step(lib, w, 1)
    assert emission(lib, w, obs) == OMEmission.SILENT
    assert sees_at(lib, w, obs, up, 600.0) == 1


def test_R_163_01_seen_from_applies_from_below_and_two_layers_away(lib, pair):
    """The seen-from rule does not care about direction (R-005-05) and scales the two-layer factor too:
    an emitting enemy one layer below is seen at 600 (0.50 x 2.0), two layers below at 390 and not at 410
    (0.20 x 2.0 = 0.40)."""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SEEN_MULT", 2.0)
    set_emission(lib, w, [enemies[1], enemies[0]], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[1], 600.0) == 1
    assert sees_at(lib, w, obs, enemies[0], 390.0) == 1
    assert sees_at(lib, w, obs, enemies[0], 410.0) == 0


def test_R_163_01_the_seen_multiplier_is_capped_at_1(lib, pair):
    """Brief G6: capped at 1.0. Seen multiplier 4.0 one layer away: reach 1,000 and not 1,010."""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SEEN_MULT", 4.0)
    set_emission(lib, w, [enemies[3]], OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 990.0) == 1
    assert sees_at(lib, w, obs, enemies[3], 1010.0) == 0


def test_R_163_02_both_silent_is_unchanged_even_with_both_multipliers_set(lib, pair):
    """Brief G6 test: 'both silent, unchanged'. The multipliers are 2.0 but nothing emits: 600 one layer away is
    unseen. Silent is today's behaviour. (Control: passes today.)"""
    w, obs, enemies = pair
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    set_param(lib, w, "EMIT_SEEN_MULT", 2.0)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, enemies[3], 600.0) == 0
    assert sees_at(lib, w, obs, enemies[3], 400.0) == 1


def test_R_163_01_emitting_does_not_change_the_sight_of_units_that_are_not_listed(lib, world_factory):
    """Per-unit mode: emission set on A does not extend B's sight (B silent, same side). A sees an enemy 600 away one
    layer up; B, silent, does not."""
    w = world_factory(n_regions=1)
    a = spawn(lib, w, OBS, 0, 0.0, 0.0, 2)
    b = spawn(lib, w, OBS, 0, 5000.0, 0.0, 2)
    enemy = spawn(lib, w, SUPPLY, 1, 9000.0, 0.0, 3)
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    set_emission(lib, w, [a], OMEmission.ACTIVE)
    step(lib, w, 1)
    place(lib, w, a, 0.0, 0.0)
    place(lib, w, b, 5000.0, 0.0)
    place(lib, w, enemy, 600.0, 0.0)
    assert can_see(lib, w, a, enemy) == 1
    place(lib, w, enemy, 5600.0, 0.0)
    assert can_see(lib, w, b, enemy) == 0


# ---- same-layer sight is unchanged in both directions (brief G6; Q-163-01 open) ----

@pytest.mark.parametrize("who", ["observer", "target", "both"])
def test_R_163_01_same_layer_sight_is_unchanged_by_emitting(lib, pair, who):
    """Brief G6: 'Same-layer sight is unchanged in both directions.' Sensor 1,000, both on layer 2, multipliers 2.0:
    seen at 990, not at 1,010, whoever emits. (Q-163-01 is open in the register; the brief's reading is tested.
    Control: passes today with nobody emitting, and must keep passing.)"""
    w, obs, enemies = pair
    same = enemies[2]
    set_param(lib, w, "EMIT_SIGHT_MULT", 2.0)
    set_param(lib, w, "EMIT_SEEN_MULT", 2.0)
    ids = {"observer": [obs], "target": [same], "both": [obs, same]}[who]
    set_emission(lib, w, ids, OMEmission.ACTIVE)
    step(lib, w, 1)
    assert sees_at(lib, w, obs, same, 990.0) == 1
    assert sees_at(lib, w, obs, same, 1010.0) == 0
