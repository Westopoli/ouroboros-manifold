"""Phase C, step G3: units fire at what their SIDE can see (E-12 S-093; E-01 R-008-04).

R-093-02: "Given any unit of any side, When it acquires, pursues or fires at a target, Then the target is
in its side's visible set: the union of what that side's living units see (R-089-01, E-01 S-005) and what
its pings reveal (E-01 S-162); the rule is the same for the player's units and the enemy's (Westley,
2026-10-02). A unit whose sensor is shorter than its range (Bombard, Bastion: sensor 300) fires beyond its
sensor only at what another friendly unit or a ping sees."
R-008-04: "a unit never fires at a target its side cannot see, on its own layer or another; a target seen
by any friendly unit or revealed by a ping may be fired at."
R-089-02: the visible set is the union of every friendly unit's visible set.
R-093-01 / the E-12 invariant: what the player is shown never changes combat resolution; each side's own
visible set does. Switch OM_TP_TARGET_BY_SIGHT: 1 (default) is this rule, 0 is today's behaviour.

RED TODAY, and why: csrc/unit.c acquires inside attack range with no sight test (om_tac_nearest_hostile,
om_tac_unit_ai), and its Bombard auto-Barrage trigger (om_tac_nearest_enemy_within_range) reads no sight
either, so a Bombard with nobody on its side seeing the target fires at it (a first hit at tick 31, then
one every 60). The control tests (a spotter present; the switch at 0) are green today on purpose: they are
the positive controls that show the detector in the 'no fire' tests can read a real hit.

Scene: see test_PP_C_g3_support.siege_scene. Window 200 ticks = 10 s: a Bombard hits at ticks 31, 60, 120,
180 (measured), so a window of 200 always holds shots.
"""
import pytest

from test_PP_C_g3_support import (BIG_HP, BOMBARD, INTERCEPTOR, RAIDER, can_see, cohort_cycle, get_param, hp,
                                  inert, kill, run_and_watch, set_param, siege_scene, spawn, step, target)

WINDOW = 200

# the four ways a siege scene can be set up: whose unit it is, and whether the client draws fog (R-093-01)
SIDES = [(0, 0), (0, 1), (1, 0), (1, 1)]  # (siege faction, player fog on)


def _fog(lib, w, on):
    lib.om_visibility_set_player_fog(w, on)


@pytest.mark.parametrize("siege_faction,fog_on", SIDES)
def test_R_093_02_siege_without_eyes_does_not_fire(lib, world_factory, siege_faction, fog_on):
    """R-093-02, R-008-04, R-093-01: a Bombard whose side sees nothing of the target (it is 1,000 wu away,
    sensor 300) neither targets it nor damages it, for either faction and with player fog on or off.
    Red today: it fires from tick 31 on (see module doc)."""
    w = world_factory(n_regions=1)
    _fog(lib, w, fog_on)
    bombard, supply, _ = siege_scene(lib, w, siege_faction, spotter=False)

    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)

    assert not held, f"the Bombard took the unseen target {supply} as its target"
    assert min(hps) == BIG_HP, f"the Bombard hit a target nobody on its side sees: hp fell to {min(hps)}"


@pytest.mark.parametrize("siege_faction,fog_on", SIDES)
def test_R_093_02_siege_with_a_spotter_fires(lib, world_factory, siege_faction, fog_on):
    """Positive control for the test above (same scene, one friendly Interceptor that sees the target at
    900 and cannot fire at it): the Bombard targets it and damages it. A 'no fire' check that cannot see
    this hit would pass for any reason. Green today and after."""
    w = world_factory(n_regions=1)
    _fog(lib, w, fog_on)
    bombard, supply, spotter = siege_scene(lib, w, siege_faction, spotter=True)

    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)

    assert held, "with a spotter the Bombard should take the target"
    assert min(hps) < BIG_HP, "with a spotter the Bombard should damage the target"
    assert hp(lib, w, spotter) > 0, "fixture: the spotter was killed"


def test_R_089_02_a_side_sees_the_union_of_its_units(lib, world_factory):
    """R-089-02, R-093-02: one friendly unit that cannot see the target (an Interceptor 1,044 wu away,
    sensor 1000) does not let the Bombard fire; the moment a second friendly unit that does see it joins,
    it fires. Phase 1 is red today (fires with nobody seeing); phase 2 is the control."""
    w = world_factory(n_regions=1)
    bombard, supply, _ = siege_scene(lib, w, 0, spotter=False)
    far = spawn(lib, w, INTERCEPTOR, 0, 0.0, 300.0)
    assert can_see(lib, w, far, supply) == 0, "fixture: the first friend must not see the target"

    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)
    assert not held and min(hps) == BIG_HP, "no unit of the side sees the target: no target, no fire"

    near = spawn(lib, w, INTERCEPTOR, 0, 100.0, 0.0)
    assert can_see(lib, w, near, supply) == 1, "fixture: the second friend must see the target"
    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)
    assert held and min(hps) < BIG_HP, "once any friendly unit sees the target the Bombard fires"


@pytest.mark.parametrize("siege_faction", [0, 1])
def test_R_008_04_fire_stops_when_the_spotter_dies(lib, world_factory, siege_faction):
    """R-008-04, R-093-02, G3 ('a unit never sits holding a target it cannot fire at'): the Bombard fires
    while the spotter lives; the spotter dies; from the next tick no damage lands (nothing sees the target
    now) and the target is dropped within one cohort cycle. 200 ticks of firing come first, so the
    Bombard's auto-Barrage (cooldown 1,800 ticks; it lands as the first, larger hit at tick 31) is
    spent and cannot be the damage read after the death. Red today: it fires on."""
    w = world_factory(n_regions=1)
    bombard, supply, spotter = siege_scene(lib, w, siege_faction, spotter=True)
    step(lib, w, WINDOW)
    assert target(lib, w, bombard) == supply and hp(lib, w, supply) < BIG_HP, "control: it fired while the spotter lived"

    kill(lib, w, spotter)
    before = hp(lib, w, supply)
    cycle = cohort_cycle(lib, w)
    dropped = False
    for tick in range(WINDOW):
        step(lib, w)
        if tick + 1 == cycle:
            dropped = target(lib, w, bombard) != supply
        assert hp(lib, w, supply) == before, f"damage landed {tick + 1} tick(s) after the side lost sight"
    assert dropped, f"the Bombard still held the unseen target {cycle} ticks after the side lost sight"


def test_R_093_02_blind_by_interference_does_not_fire(lib, world_factory):
    """R-089-01, R-093-02: sight is reduced by interference (effective radius r x (1 - i)); a Raider
    standing in a zone of intensity 0.9 sees 80 wu and its target is 150 away, inside its attack range
    200. It must neither target nor hit it. Red today: it fires (range only)."""
    w = world_factory(n_regions=1)
    raider = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    supply = inert(lib, w, 1, 150.0, 0.0)
    lib.om_map_add_interference_zone(w, 0.0, 0.0, 0, 0.9, 50.0)
    assert can_see(lib, w, raider, supply) == 0, "fixture: the blinded Raider must not see the target"

    hps, held = run_and_watch(lib, w, 100, supply, raider, supply)

    assert not held and min(hps) == BIG_HP, "a blinded unit with nobody else seeing fired at an unseen target"


def test_R_093_02_blind_by_interference_control_a_friend_sees(lib, world_factory):
    """Positive control: the same blinded Raider, plus a friendly Interceptor outside the zone that sees
    the target from 427 wu (it cannot fire: its range is 250). The Raider fires on what its side
    sees. Green today and after."""
    w = world_factory(n_regions=1)
    raider = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    supply = inert(lib, w, 1, 150.0, 0.0)
    friend = spawn(lib, w, INTERCEPTOR, 0, 0.0, 400.0)
    lib.om_map_add_interference_zone(w, 0.0, 0.0, 0, 0.9, 50.0)
    assert can_see(lib, w, raider, supply) == 0 and can_see(lib, w, friend, supply) == 1, "fixture: sight"

    hps, held = run_and_watch(lib, w, 100, supply, raider, supply)

    assert held and min(hps) < BIG_HP, "a unit whose side sees the target must fire at it"


def test_R_093_02_unseen_attacker_is_not_answered(lib, world_factory):
    """R-093-02, R-087-01: a Raider blinded by interference is shot at by a Raider that sees it. It cannot
    see its attacker (nor can its side), so it takes no target and returns no fire; the attacker stays at
    full hp. Interference falls off linearly from the zone centre (intensity x (1 - d / radius), fog.c);
    the zone is centred on the victim with radius 600, so after the 200 wu move away that R-087-01 gives a
    unit hit by an attacker it cannot see the victim's sight (320 wu) is still short of the attacker (350
    wu): it stays blind for the whole window and no later honest sighting can start a fight. Red today: it targets the
    attacker at once and trades hits (the hit-for-hit control is the next test)."""
    w = world_factory(n_regions=1)
    attacker = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    victim = spawn(lib, w, RAIDER, 1, 150.0, 0.0)
    lib.om_map_add_interference_zone(w, 150.0, 0.0, 0, 0.9, 600.0)
    assert can_see(lib, w, attacker, victim) == 1 and can_see(lib, w, victim, attacker) == 0, "fixture: sight"
    full = hp(lib, w, attacker)

    hps, held = run_and_watch(lib, w, 100, attacker, victim, attacker)

    assert not held, "the blinded victim took its unseen attacker as a target"
    assert min(hps) == full, f"the blinded victim shot its unseen attacker: hp fell to {min(hps)}"


def test_R_093_02_unseen_attacker_control_open_ground_trades_fire(lib, world_factory):
    """Positive control for the test above: the same pair with no interference zone trade hits."""
    w = world_factory(n_regions=1)
    attacker = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
    victim = spawn(lib, w, RAIDER, 1, 150.0, 0.0)
    assert can_see(lib, w, victim, attacker) == 1, "fixture: sight"
    full = hp(lib, w, attacker)

    hps, held = run_and_watch(lib, w, 100, attacker, victim, attacker)

    assert held and min(hps) < full, "two Raiders in sight of each other must trade fire"


def test_R_093_02_switch_zero_is_todays_behaviour_and_both_ways(lib, world_factory):
    """OM_TP_TARGET_BY_SIGHT: default 1; 0 gives today's behaviour (a Bombard fires with nobody seeing,
    green today); switched to 1 in mid-fight it takes effect on the next tick (contract section 3) and the
    firing stops with no damage from then on (red today: 1 changes nothing); back to 0 it fires again
    (so the stop was the switch and not luck)."""
    w = world_factory(n_regions=1)
    assert get_param(lib, w, "TARGET_BY_SIGHT") == 1.0, "default must be the bible's rule (1)"
    bombard, supply, _ = siege_scene(lib, w, 0, spotter=False)

    assert set_param(lib, w, "TARGET_BY_SIGHT", 0) == 0
    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)
    assert held and min(hps) < BIG_HP, "switch 0: today's behaviour, the Bombard fires on an unseen target"

    assert set_param(lib, w, "TARGET_BY_SIGHT", 1) == 0
    frozen = hp(lib, w, supply)
    hps, _ = run_and_watch(lib, w, WINDOW, supply)
    assert min(hps) == frozen, "switch 1: no damage may land on a target nobody on the side sees"

    assert set_param(lib, w, "TARGET_BY_SIGHT", 0) == 0
    hps, _ = run_and_watch(lib, w, WINDOW, supply)
    assert min(hps) < frozen, "switch back to 0: it fires again"


def test_R_093_02_nothing_changes_when_the_target_is_seen_by_itself(lib, world_factory):
    """Guard against over-gating (G3 'two forces ... react'): two Raiders on open ground within each
    other's sight and range trade fire with the switch at its default, and the first hit lands within
    the same 100 ticks as with the switch at 0 (the two worlds' first-hit tick is equal: open ground
    controls must not change, plan Phase C 'the controls are re-hashed at 1 and the difference reported')."""
    firsts = []
    for switch in (1, 0):
        w = world_factory(n_regions=1)
        assert set_param(lib, w, "TARGET_BY_SIGHT", switch) == 0
        a = spawn(lib, w, RAIDER, 0, 0.0, 0.0)
        b = spawn(lib, w, RAIDER, 1, 150.0, 0.0)
        first = None
        for tick in range(1, 101):
            step(lib, w)
            if first is None and (hp(lib, w, a) < 250.0 or hp(lib, w, b) < 250.0):
                first = tick
        firsts.append(first)
    assert firsts[0] is not None, "two Raiders in sight and range must fire"
    assert firsts[0] == firsts[1], f"open-ground first hit moved with the switch: {firsts[0]} at 1, {firsts[1]} at 0"


def test_R_008_04_siege_across_layers_needs_a_seer_too(lib, world_factory):
    """R-008-04 ('on its own layer or another'), with reach (G5, E-01 S-164) built: a Bombard allowed to
    fire one layer up (om_roster_set_reach) at a target on layer 1, 600 wu away, does so only once a
    friendly unit sees it (the Bombard's cross-layer sight is 300 x 0.5 = 150). Phase 1 (no spotter, no
    fire) is green today for a wrong reason (no reach is built yet) and is kept so the control is
    meaningful after G5; phase 2 is red today because reach is not built, and stays red after G5 until G3
    lets a seen target be fired at. Both phases need G3 AND G5."""
    w = world_factory(n_regions=1)
    assert lib.om_roster_set_reach(w, BOMBARD, 1, 1) == 0, "reach for the Bombard type must be settable"
    bombard = spawn(lib, w, BOMBARD, 0, 0.0, 0.0, 0)
    supply = inert(lib, w, 1, 600.0, 0.0, 1)
    assert can_see(lib, w, bombard, supply) == 0, "fixture: the Bombard must not see one layer up at 600"

    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)
    assert not held and min(hps) == BIG_HP, "no unit of the side sees the target: no fire, whatever its layer"

    spotter = spawn(lib, w, INTERCEPTOR, 0, 500.0, 0.0, 1)
    assert can_see(lib, w, spotter, supply) == 1, "fixture: the spotter on layer 1 must see the target"
    hps, held = run_and_watch(lib, w, WINDOW, supply, bombard, supply)
    assert held and min(hps) < BIG_HP, "seen by a friend on its layer, the Bombard fires across layers"
