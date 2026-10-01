"""Targeted ping tests (SPEC.md 15.3; E-01 S-162, rung L3; ABI 3). Written before the builder replaces the
no-op stub in src/ll_ping.c, so every test that needs a real ping fails today because the stub does nothing.

Numbers: ping_reach 1200, ping_radius 250, ping_s 0.5 = 10 ticks (20 ticks per second), cooldown 6.0 s (not
testable here: a unit has exactly one `ping_tick`, so a second ping cannot be ordered; SPEC gap, as for the
pulse). The pinger is unit 0, side A, on layer 5 at (2000, 1000); the pinged enemies are raiders on `hold` on
layer 1 near (1800, 1000). Layers 5 and 1 are four apart, so passive vision is zero (vis_factor[0] = 0) and only
the ping can reveal them. Spawn jitter is 0, so every distance is exact; hold orders, so nobody moves; the
default rules are same-layer-only combat, and a test that wants the pinger's side to shoot across layers turns
on the layer-5-to-layer-1 entry (offset -4) of range_mult and dmg_mult. fire_requires_vision stays 1 (base
default): a shot at a layer-1 enemy proves the side saw it (SPEC 5.4, no blind fire).

Observables: trace flag bit3 of the pinged unit (visible to the other side, read from the row of the tick
itself, after step 3 vision), the shots of the shooter (`fire_ticks`, `first_shot_tick`, `shots`,
`damage_dealt`), `first_contact_tick`, and the alert fields of the result.

Edge reading (SPEC 15.3 "a window of round(ping_s * 20) ticks from the ping tick", and ll_ping_update runs in step 3
before ll_side_vision in the same tick): a ping at tick p reveals on the rows p .. p + N - 1, N = (int)(ping_s * 20
+ 0.5). The window is asserted exactly, with no slack. ping_s values are chosen away from x.5 products so no
floating point noise decides the rounding (0.58 * 20 = 11.6 rounds to 12, which truncation would get wrong).

Shooter: `gun` is an interceptor with interval_s 0.2 (4 ticks) so a 10-tick window holds several shots; its
initial cooldown (U(0, 0.2 s)) has run out by tick 30 and an idle unit banks nothing (SPEC 5.5), so it fires on
the first tick it sees something.

The pinger of most tests is a `seer` (dmg 0: never fires, so the pinged unit is never shot and the geometry is the
only variable); `frag` is a seer with hp 10, for the death tests.
"""
import copy
import math

import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, fire_ticks, grp, make_scenario, table9, unit_trace

P = 30                       # ping tick
N = 10                       # round(0.5 * 20): the default window, in ticks
PX, PY = 2000.0, 1000.0      # pinger
TX, TY = 1800.0, 1000.0      # the default pinged enemy
LONG = {"stalemate_ticks": 6000}
FIRE_DOWN = {"range_mult": table9(m4=1), "dmg_mult": table9(m4=1)}   # layer 5 shoots layer 1 (offset -4)
ALL_TYPES = ["raider", "interceptor", "vanguard", "warden", "bombard", "bastion", "caster", "seer"]


def windows(vis):
    """Runs of consecutive True in a bool array, as (start, end) tick pairs, end inclusive."""
    out, start = [], None
    for t, v in enumerate(np.asarray(vis, dtype=bool)):
        if v and start is None:
            start = t
        if not v and start is not None:
            out.append((start, t - 1))
            start = None
    if start is not None:
        out.append((start, len(vis) - 1))
    return out


def vis(res, i):
    return unit_trace(res, i).visible


def ping_scn(*, ping_tick=P, layer=1, place=(TX, TY), pinger="seer", pinger_xy=(PX, PY), pinger_layer=5,
             targets=((TX, TY, 1),), rules=None, extra=(), max_ticks=120, fire=False, ping_extra=None):
    """Unit 0 = the pinger (side A); units 1.. = one B raider per (x, y, layer) in `targets`; then `extra` groups.
    `ping_tick=None` leaves the ping unordered (the no-ping twin). `fire` turns layer-5-to-1 fire on."""
    kw = {}
    if ping_tick is not None:
        kw = {"ping_tick": ping_tick, "ping_layer": layer, "ping_x": float(place[0]), "ping_y": float(place[1])}
    kw.update(ping_extra or {})
    groups = [grp("A", pinger, pinger_xy[0], pinger_xy[1], pinger_layer, **kw)]
    groups += [grp("B", "raider", x, y, ly) for x, y, ly in targets]
    groups += list(extra)
    r = {"spawn_jitter": 0.0}
    if fire:
        r.update(FIRE_DOWN)
    r.update(rules or {})
    scn = make_scenario(groups, rules=r, run={"max_ticks": max_ticks, **LONG})
    add_type(scn, "gun", "interceptor", interval_s=0.2)
    add_type(scn, "frag", "seer", hp=10.0)
    return scn


def assert_window(res, i, start, length):
    assert windows(vis(res, i)) == [(start, start + length - 1)], windows(vis(res, i))


def assert_never_seen(res, i):
    assert not vis(res, i).any(), "unit %d was revealed" % i


def assert_no_alert(res):
    assert res.alerted_tick == (-1, -1) and res.alerts == (0, 0)
    assert res.alert_dir_x == (0.0, 0.0) and res.alert_dir_y == (0.0, 0.0)


# ---- 1. a ping reveals an otherwise unseen enemy (S-162) ---------------------------------------------------------

def test_ping_reveals_unseen_enemy_and_the_pinger_fires_only_after_the_ping_tick():
    """S-162, SPEC 15.3: the target on layer 1 is four layers from the pinger on layer 5, so passive sight is zero
    and, with no blind fire (5.4), nothing is shot without the ping. The 'gun' pinger (range 250, target at 200,
    layer-5-to-1 fire on) fires after the ping: first shot at or after tick P, every shot inside the 10-tick
    window P .. P + 9, at least two of them (interval 4 ticks), damage dealt, first_contact_tick == P. Twin without
    a ping_tick: zero shots on both sides, no damage, first_shot_tick -1, first_contact_tick -1."""
    res = runmod.run(ping_scn(pinger="gun", fire=True), seed=0, trace=True)
    shots = fire_ticks(res, 0)
    assert len(shots) >= 2, shots
    assert shots.min() >= P and shots.max() <= P + N - 1, shots
    assert res.first_shot_tick >= P and res.first_shot_side == 0
    assert res.shots[0] == len(shots) and res.shots[1] == 0
    assert res.damage_dealt[0] > 0 and res.damage_dealt[1] == 0.0
    assert res.first_contact_tick == P
    assert_window(res, 1, P, N)

    ctl = runmod.run(ping_scn(pinger="gun", fire=True, ping_tick=None), seed=0, trace=True)
    assert ctl.shots == (0, 0) and ctl.damage_dealt == (0.0, 0.0)
    assert ctl.first_shot_tick == -1 and ctl.first_contact_tick == -1
    assert_never_seen(ctl, 1)


def test_ping_reveal_is_for_the_whole_side_an_ally_shoots_what_the_pinger_revealed():
    """S-162, SPEC 15.3 ('for the pinger's side') and 5.2 (side_sees): the pinger is a seer (never fires); a second
    A unit, a 'gun' on layer 5 at (2000, 1100), cannot see the layer-1 target itself and fires at it only inside the
    window the seer's ping opened (positive: at least two shots, all in P .. P + 9). Twin with no ping: the ally
    never fires (negative)."""
    ally = [grp("A", "gun", 2000.0, 1100.0, 5)]
    res = runmod.run(ping_scn(fire=True, extra=ally), seed=0, trace=True)
    shots = fire_ticks(res, 2)
    assert len(shots) >= 2 and shots.min() >= P and shots.max() <= P + N - 1, shots
    assert not fire_ticks(res, 0).size
    ctl = runmod.run(ping_scn(fire=True, extra=ally, ping_tick=None), seed=0, trace=True)
    assert ctl.shots == (0, 0)


# ---- 2. layer and place matter -----------------------------------------------------------------------------------

@pytest.mark.parametrize("layer", [1, 2, 3, 4, 5])
def test_ping_reveals_only_enemies_on_the_pinged_layer(layer):
    """S-162, SPEC 15.3 ('effective layer equals ping_layer'): the place (1800, 1050) is 50 from a raider on layer 1
    (unit 1) and 50 from a raider on layer 2 (unit 2), both four or three layers below the layer-5 pinger (no
    passive sight). Aimed at layer 1 only unit 1 is revealed, at layer 2 only unit 2; aimed at 3, 4 or 5 nobody (the
    wrong layer reveals nothing, positive and negative cases in one parametrized family). A revealed unit is shown
    for exactly the window; the 'gun' pinger shoots iff the layer-1 raider is revealed (layer-2 raiders are out of
    its fire table), and nobody is alerted when nobody is revealed."""
    res = runmod.run(ping_scn(layer=layer, place=(TX, 1050.0), pinger="gun", fire=True,
                              targets=((TX, TY, 1), (TX, 1100.0, 2))), seed=0, trace=True)
    for unit, own_layer in ((1, 1), (2, 2)):
        if layer == own_layer:
            assert_window(res, unit, P, N)
        else:
            assert_never_seen(res, unit)
    assert (res.shots[0] > 0) == (layer == 1)
    if layer in (1, 2):
        assert res.alerts == (0, 1) and res.alerted_tick == (-1, P)
    else:
        assert_no_alert(res)


@pytest.mark.parametrize("radius,dx,revealed", [
    (250.0, 0.0, True), (250.0, 100.0, True), (250.0, 249.0, True), (250.0, 250.0, True),
    (250.0, 251.0, False), (250.0, 400.0, False), (250.0, -251.0, False), (250.0, -240.0, True),
    (100.0, 99.0, True), (100.0, 150.0, False), (400.0, 300.0, True), (400.0, 401.0, False),
])
def test_ping_reveals_only_inside_the_radius_of_the_place(radius, dx, revealed):
    """S-162, SPEC 15.3 ('xy distance to the place is at most rules.ping_radius'): the place is `dx` along x from
    the layer-1 raider at (1800, 1000), the right layer. Revealed when |dx| <= radius, including exactly on the edge
    (250 -> 250); not revealed 1 beyond it; the rule value is what decides (radius 100 and 400 move the edge).
    The run is the no-reveal case when the place is outside: no alert at all."""
    res = runmod.run(ping_scn(place=(TX + dx, TY), rules={"ping_radius": radius}), seed=0, trace=True)
    if revealed:
        assert_window(res, 1, P, N)
        assert res.alerts == (0, 1)
    else:
        assert_never_seen(res, 1)
        assert_no_alert(res)


def test_ping_radius_is_planar_and_diagonal_distance_counts():
    """SPEC 15.3 ('xy distance'): a place 242 away on the diagonal (150, 190) reveals (positive); (180, 180), 254.6
    away, does not (negative); a large layer_spacing (the vertical term of passive sight) changes nothing."""
    inside = runmod.run(ping_scn(place=(TX + 150.0, TY + 190.0)), seed=0, trace=True)
    assert_window(inside, 1, P, N)
    outside = runmod.run(ping_scn(place=(TX + 180.0, TY + 180.0)), seed=0, trace=True)
    assert_never_seen(outside, 1)
    scn = ping_scn()
    scn["terrain"]["layer_spacing"] = 1000.0
    spaced = runmod.run(scn, seed=0, trace=True)
    assert_window(spaced, 1, P, N)


# ---- 3. the window -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("ping_s,length", [(0.5, 10), (0.52, 10), (0.58, 12), (1.0, 20), (0.05, 1)])
@pytest.mark.parametrize("tick", [0, P, 77])
def test_ping_window_is_round_of_ping_s_times_twenty_ticks(ping_s, length, tick):
    """SPEC 15.3 (window of round(ping_s * 20) ticks, (int)(x + 0.5)): the revealed enemy has bit3 set on exactly
    the rows tick .. tick + length - 1 and on no other row (0.58 s is 12 ticks, 0.52 s is 10, 0.05 s is 1; a ping
    at tick 0 is honoured). Before the ping and after the window the enemy is unseen (the 120-row run shows both
    sides of the window)."""
    res = runmod.run(ping_scn(ping_tick=tick, rules={"ping_s": ping_s}), seed=0, trace=True)
    assert_window(res, 1, tick, length)


def test_ping_shots_fall_inside_the_window_and_stop_when_it_ends():
    """SPEC 15.3 and 5.5: a 'gun' (cooldown 4 ticks) fires only while the target is seen. With ping_s 1.0 (window
    P .. P + 19) it shoots at least five times inside the window (interval 4 ticks) and never after P + 19; with the
    default 0.5 s (P .. P + 9) it shoots at least two times and never after P + 9. The window, not the cooldown,
    ends the firing: the pinger's cooldown would allow shots on every fourth tick afterwards (the no-ping twin
    in the first test shows it is held back only by sight)."""
    for ping_s, last in ((1.0, P + 19), (0.5, P + N - 1)):
        res = runmod.run(ping_scn(pinger="gun", fire=True, rules={"ping_s": ping_s}), seed=0, trace=True)
        shots = fire_ticks(res, 0)
        assert len(shots) >= (5 if ping_s == 1.0 else 2), (ping_s, shots)
        assert shots.min() >= P and shots.max() <= last, (ping_s, shots)
        assert res.ticks > last + 20, "the run must go on well past the window for 'stops' to mean something"


def _killer_scn(killer_dx, *, ping_tick, ping_s=2.0):
    """Fragile seer pinger (hp 10) at layer 5; a raider killer on layer 5 on hold at |killer_dx| from it (range 200, hits
    of 9: two hits kill it, dead between about tick 16 and 33); a bystander A interceptor far away keeps side A
    alive so the trace continues after the death; the layer-1 target is at (1800, 1000). Units: 0 pinger,
    1 target, 2 killer, 3 bystander."""
    return ping_scn(pinger="frag", ping_tick=ping_tick, rules={"ping_s": ping_s}, max_ticks=140,
                    extra=[grp("B", "raider", PX + killer_dx, PY, 5), grp("A", "interceptor", 300.0, 200.0, 5)])


def test_ping_window_ends_early_when_the_pinger_dies():
    """SPEC 15.3 ('the window ends early if the pinger dies'): the pinger pings at tick 2 with ping_s 2.0 (a 40-tick
    window, 2 .. 41) and a raider on its layer 150 away kills it inside the window. The target is revealed from the
    ping up to the death (positive) and never on a row after the death tick (the death tick's own row may still
    show it: it is decided in step 3 before the damage of step 6). Negative twin: the same killer 600 away cannot
    reach, the pinger lives and the full 40-tick window shows."""
    res = runmod.run(_killer_scn(150.0, ping_tick=2), seed=0, trace=True)
    dead = np.flatnonzero(unit_trace(res, 0).alive == 0)
    assert dead.size, "the pinger should have been killed"
    d = int(dead[0])
    assert 2 + 5 < d < 2 + 40 - 2, "the kill must land inside the window for this test to bite (death tick %d)" % d
    v = vis(res, 1)
    assert v[2:d].all(), "target should be revealed from the ping until the pinger dies"
    assert not v[d + 1:].any(), "the reveal outlived the pinger"

    safe = runmod.run(_killer_scn(600.0, ping_tick=2), seed=0, trace=True)
    assert unit_trace(safe, 0).alive.all()
    assert_window(safe, 1, 2, 40)


# ---- 4. reach, a dead pinger, any unit type ---------------------------------------------------------------------

@pytest.mark.parametrize("dist,reach,started", [
    (1100.0, 1200.0, True), (1200.0, 1200.0, True), (1201.0, 1200.0, False), (1300.0, 1200.0, False),
    (150.0, 100.0, False), (150.0, 200.0, True), (0.0, 0.0, True),
])
def test_ping_reach_limits_how_far_from_the_pinger_the_place_can_be(dist, reach, started):
    """SPEC 15.3 ('xy distance from the unit to the place is at most rules.ping_reach; otherwise it is refused (nothing
    happens)'): pinger on layer 5 at (500, 1000), the layer-1 target and the place `dist` along x. Started up to and
    including exactly the reach (1200 -> 1200; and 0 with reach 0); refused 1 beyond it, with no reveal, no alert
    and first_contact_tick -1; the rule value decides (reach 100 refuses 150, reach 200 accepts it)."""
    res = runmod.run(ping_scn(pinger_xy=(500.0, PY), place=(500.0 + dist, PY), targets=((500.0 + dist, PY, 1),),
                              rules={"ping_reach": reach}), seed=0, trace=True)
    if started:
        assert_window(res, 1, P, N)
        assert res.alerts == (0, 1) and res.alerted_tick == (-1, P)
    else:
        assert_never_seen(res, 1)
        assert_no_alert(res)
        assert res.first_contact_tick == -1


def test_ping_reach_is_measured_to_the_place_not_to_the_revealed_unit():
    """SPEC 15.3: the place is 1150 from the pinger (inside reach 1200) and the enemy stands 200 beyond it, 1350 from
    the pinger but 200 from the place (inside the radius): revealed (positive). The same enemy with the place
    moved out to 1250 from the pinger is refused (negative)."""
    near = runmod.run(ping_scn(pinger_xy=(500.0, PY), place=(1650.0, PY), targets=((1850.0, PY, 1),)),
                      seed=0, trace=True)
    assert_window(near, 1, P, N)
    far = runmod.run(ping_scn(pinger_xy=(500.0, PY), place=(1750.0, PY), targets=((1850.0, PY, 1),)),
                     seed=0, trace=True)
    assert_never_seen(far, 1)
    assert_no_alert(far)


def test_a_pinger_dead_at_the_ping_tick_does_nothing():
    """SPEC 15.3 ('starts if the unit is alive'): the fragile pinger is killed by tick 40 at the latest (precondition
    asserted: dead before tick 60) and was to ping at tick 60: the target is never revealed and nobody is alerted.
    Positive control: the same pinger with the killer out of reach pings at 60 and the window shows."""
    res = runmod.run(_killer_scn(150.0, ping_tick=60, ping_s=0.5), seed=0, trace=True)
    dead = np.flatnonzero(unit_trace(res, 0).alive == 0)
    assert dead.size and dead[0] < 60, "the pinger must be dead before its ping tick for this test to bite"
    assert_never_seen(res, 1)
    assert_no_alert(res)

    safe = runmod.run(_killer_scn(600.0, ping_tick=60, ping_s=0.5), seed=0, trace=True)
    assert_window(safe, 1, 60, N)


@pytest.mark.parametrize("pinger", ALL_TYPES)
def test_any_unit_type_may_ping(pinger):
    """SPEC 15.3 ('Any unit type may ping'): each roster type, as the layer-5 pinger (cross-layer fire off, so none
    of them shoots), reveals the layer-1 raider 300 away (outside every passive range at four layers) for the
    window and alerts side B once."""
    res = runmod.run(ping_scn(pinger=pinger, targets=((PX - 300.0, PY, 1),), place=(PX - 300.0, PY)),
                     seed=0, trace=True)
    assert_window(res, 1, P, N)
    assert res.alerts == (0, 1)


# ---- 5. the pinger stays hidden; passive vision is untouched ---------------------------------------------------

def test_ping_does_not_reveal_the_pinger_to_the_enemy():
    """SPEC 15.3 ('does not reveal the pinger'): layer-5 'gun' pinger, layer-1 raider at 150 (inside the raider's range
    200), fire tables on in BOTH directions so the raider would shoot if it saw the pinger. During the ping the
    raider is revealed and shot at (positive: the pinger fires), but the pinger's visible bit is never set and the
    raider never fires (negative); twin without a ping: the raider never fires either."""
    both = {"range_mult": table9(m4=1, p4=1), "dmg_mult": table9(m4=1, p4=1)}
    tgt = ((PX - 150.0, PY, 1),)
    res = runmod.run(ping_scn(pinger="gun", targets=tgt, place=tgt[0][:2], rules=both), seed=0, trace=True)
    assert len(fire_ticks(res, 0)) >= 2, "the ping must have revealed the raider to the pinger's side"
    assert_never_seen(res, 0)
    assert not fire_ticks(res, 1).size and res.shots[1] == 0
    assert unit_trace(res, 0).hp[-1] == pytest.approx(325.0)
    ctl = runmod.run(ping_scn(pinger="gun", targets=tgt, ping_tick=None, rules=both), seed=0, trace=True)
    assert ctl.shots == (0, 0)


def test_ping_changes_no_passive_vision_a_ping_of_what_is_already_seen_changes_nothing():
    """SPEC 15.3 ('does not change passive vision'): pinger on layer 2, raider on layer 1 at 150 (adjacent layers, factor
    0.5: they see each other passively, the raider reaches the pinger at 800 * 0.5 = 400); fire tables on both
    ways at offsets -1 and +1. They shoot each other from the start (non-vacuous: shots on both sides). A ping at
    tick 30 aimed at that raider reveals nothing new, so the trace and the result bytes are IDENTICAL to the
    no-ping twin apart from the alert fields (the trace carries every position, hp, shot and visibility bit)."""
    on = {"range_mult": table9(m1=1, p1=1), "dmg_mult": table9(m1=1, p1=1), "spawn_jitter": 0.0}
    kw = dict(pinger="gun", pinger_layer=2, targets=((PX - 150.0, PY, 1),), place=(PX - 150.0, PY), rules=on,
              max_ticks=60)
    ping = runmod.run(ping_scn(**kw), seed=3, trace=True)
    kw["ping_tick"] = None
    plain = runmod.run(ping_scn(**kw), seed=3, trace=True)
    assert ping.shots[0] > 0 and ping.shots[1] > 0
    assert np.ascontiguousarray(ping.trace).tobytes() == np.ascontiguousarray(plain.trace).tobytes()
    assert (ping.shots, ping.damage_dealt, ping.winner, ping.ticks) == (plain.shots, plain.damage_dealt,
                                                                       plain.winner, plain.ticks)


def test_a_ping_that_reveals_nothing_changes_nothing():
    """SPEC 15.3 ('costs nothing', 'does not change passive vision'): a ping aimed at the wrong layer, and one refused
    for reach (rules.ping_reach 100, the place 150 away), leave the trace bytes AND the whole result (raw bytes,
    alert fields included: -1, 0, 0) identical to the twin without a ping, on a scenario with shooting in it (the
    pinger's 'gun' on layer 3 fires at a passively seen layer-4 raider 150 away, sensor 1000 * 0.5), so the
    comparison is not empty."""
    on = {"range_mult": table9(p1=1), "dmg_mult": table9(p1=1), "spawn_jitter": 0.0, "ping_reach": 100.0}
    base = dict(pinger="gun", pinger_layer=3, targets=((PX - 150.0, PY, 4),), rules=on, max_ticks=80)
    plain = runmod.run(ping_scn(ping_tick=None, **base), seed=5, trace=True)
    assert plain.shots[0] > 0
    wrong_layer = runmod.run(ping_scn(layer=1, place=(PX - 150.0, PY), **base), seed=5, trace=True)
    too_far = runmod.run(ping_scn(layer=4, place=(PX - 150.0, PY), **base), seed=5, trace=True)
    for res in (wrong_layer, too_far):
        assert res.raw == plain.raw
        assert np.ascontiguousarray(res.trace).tobytes() == np.ascontiguousarray(plain.trace).tobytes()


# ---- 6. alerts ---------------------------------------------------------------------------------------------------

def _alert_scn(**kw):
    """Pinger seer (unit 0) at (2000, 1000) on layer 5 pings layer 1 at (1850, 900) at tick P. Enemy raiders, all hold:
    unit 1 (1800, 1100) and unit 2 (1950, 800), both layer 1 and inside radius 250 of the place (206 and 141), are
    revealed; unit 3 (2250, 900) is on layer 1 but 400 from the place; unit 4 (1850, 900) is on layer 2 at the
    place: neither is revealed. The centroid of the revealed units is (1875, 950), which is NOT the place and NOT
    the centroid of all the enemies, so a wrong centroid shows."""
    kw.setdefault("place", (1850.0, 900.0))
    return ping_scn(targets=((1800.0, 1100.0, 1), (1950.0, 800.0, 1), (2250.0, 900.0, 1), (1850.0, 900.0, 2)), **kw)


def _unit_vec(fx, fy, tx, ty):
    d = math.hypot(tx - fx, ty - fy)
    return (tx - fx) / d, (ty - fy) / d


def test_ping_alerts_the_revealed_side_with_the_direction_from_the_revealed_centroid():
    """S-162, SPEC 15.3 (alerts): the ping reveals units 1 and 2 only (units 3 and 4 are outside the radius or on
    the wrong layer, see _alert_scn): alerted_tick[B] == P, alerts[B] == 1, and the pinger's side A is not
    alerted (-1, 0, direction 0). alert_dir[B] is the unit vector from the centroid (1875, 950) of the REVEALED
    units to the pinger's xy (2000, 1000), within 1e-9, and has length 1. Cross-checks that the revealed units are
    shown on the trace (units 3 and 4 never are)."""
    res = runmod.run(_alert_scn(), seed=0, trace=True)
    assert_window(res, 1, P, N)
    assert_window(res, 2, P, N)
    assert_never_seen(res, 3)
    assert_never_seen(res, 4)
    assert res.alerted_tick == (-1, P)
    assert res.alerts == (0, 1)
    ex, ey = _unit_vec(1875.0, 950.0, PX, PY)
    assert res.alert_dir_x[1] == pytest.approx(ex, abs=1e-9) and res.alert_dir_y[1] == pytest.approx(ey, abs=1e-9)
    assert math.hypot(res.alert_dir_x[1], res.alert_dir_y[1]) == pytest.approx(1.0, abs=1e-9)
    assert res.alert_dir_x[0] == 0.0 and res.alert_dir_y[0] == 0.0
    # the direction is not the one from the place or from the centroid of every enemy
    assert abs(res.alert_dir_x[1] - _unit_vec(1850.0, 900.0, PX, PY)[0]) > 1e-3
    assert abs(res.alert_dir_x[1] - _unit_vec(1950.0, 900.0, PX, PY)[0]) > 1e-3


def test_ping_that_reveals_no_enemy_leaves_the_alert_fields_untouched():
    """SPEC 15.3: a ping aimed at the wrong layer, one whose place (1850, 1400) is outside the radius of every
    layer-1 enemy (304 from the nearest), and one refused for reach (the place is 180 from the pinger, rules.ping_reach 100) each leave
    alerted_tick (-1, -1), alerts (0, 0) and the direction (0, 0), and no unit is shown. Positive control: the right
    layer, place and reach alert B (the scenario of the test above)."""
    wrong_layer = _alert_scn(layer=3)
    far_place = _alert_scn(place=(1850.0, 1400.0))
    refused = _alert_scn(rules={"ping_reach": 100.0})
    for scn in (wrong_layer, far_place, refused):
        res = runmod.run(scn, seed=0, trace=True)
        assert_no_alert(res)
        for unit in (1, 2, 3, 4):
            assert_never_seen(res, unit)
    ok = runmod.run(_alert_scn(), seed=0)
    assert ok.alerts == (0, 1)


def test_alert_direction_is_zero_when_the_revealed_centroid_is_the_pinger_position():
    """SPEC 15.3 ('if the centroid equals the pinger's position the vector is (0, 0)'): the pinger on layer 5 at
    (1850, 900) pings the single layer-1 raider standing at (1850, 900). alerts[B] == 1 and alerted_tick[B] == P
    (the alert happened) with direction exactly (0, 0), not NaN."""
    res = runmod.run(ping_scn(pinger_xy=(1850.0, 900.0), place=(1850.0, 900.0), targets=((1850.0, 900.0, 1),)),
                     seed=0, trace=True)
    assert_window(res, 1, P, N)
    assert res.alerted_tick == (-1, P) and res.alerts == (0, 1)
    assert res.alert_dir_x == (0.0, 0.0) and res.alert_dir_y == (0.0, 0.0)


def test_two_pings_that_reveal_the_same_enemy_count_twice_and_keep_the_first_alert():
    """SPEC 15.3 ('alerts[side] counts the pings that revealed that side', direction 'set at the first alert, left
    unchanged afterwards'): unit 0 (pinger at (2000, 1000)) pings at tick 25, unit 1 (pinger at (1700, 1300)) pings
    at tick 20, both at the layer-1 raider at (1800, 1000). The windows overlap (20 .. 29 and 25 .. 34) and the raider
    is shown on 20 .. 34. alerts[B] == 2, alerted_tick[B] == 20 (the first by TICK, not by unit index), and the
    direction is the first pinger's, from (1800, 1000) toward (1700, 1300), within 1e-9."""
    second = [grp("A", "seer", 1700.0, 1300.0, 5, ping_tick=20, ping_layer=1, ping_x=TX, ping_y=TY)]
    res = runmod.run(ping_scn(ping_tick=25, extra=second), seed=0, trace=True)
    assert windows(vis(res, 1)) == [(20, 34)]
    assert res.alerts == (0, 2) and res.alerted_tick == (-1, 20)
    ex, ey = _unit_vec(TX, TY, 1700.0, 1300.0)
    assert res.alert_dir_x[1] == pytest.approx(ex, abs=1e-9) and res.alert_dir_y[1] == pytest.approx(ey, abs=1e-9)
    assert res.alert_dir_x[0] == 0.0 and res.alert_dir_y[0] == 0.0


def test_ping_alert_counts_per_side_two_sides_pinging_each_other():
    """SPEC 15.3 (alerts per side): side B has its own layer-5 seer pinging layer 1 at the side-A raider, side A's
    seer pings the side-B raider: each side is alerted once at its own ping tick (A at 40, B at 25), and the
    directions point each side's revealed unit toward the OTHER side's pinger. Isolation: the four units are far
    from each other's passive sight."""
    groups = [grp("A", "seer", 300.0, 1000.0, 5, ping_tick=25, ping_layer=1, ping_x=900.0, ping_y=1000.0),
              grp("B", "raider", 900.0, 1000.0, 1),                                  # unit 1, pinged by A at 25
              grp("B", "seer", 3000.0, 1000.0, 5, ping_tick=40, ping_layer=1, ping_x=2400.0, ping_y=1000.0),
              grp("A", "raider", 2400.0, 1000.0, 1)]                                # unit 3, pinged by B at 40
    scn = make_scenario(groups, rules={"spawn_jitter": 0.0}, run={"max_ticks": 100, **LONG})
    res = runmod.run(scn, seed=0, trace=True)
    assert res.alerted_tick == (40, 25) and res.alerts == (1, 1)
    # side B's revealed raider (900, 1000) -> A's pinger (300, 1000): (-1, 0); side A's raider (2400, 1000) -> (3000, 1000): (1, 0)
    assert res.alert_dir_x[1] == pytest.approx(-1.0, abs=1e-9) and res.alert_dir_y[1] == pytest.approx(0.0, abs=1e-9)
    assert res.alert_dir_x[0] == pytest.approx(1.0, abs=1e-9) and res.alert_dir_y[0] == pytest.approx(0.0, abs=1e-9)


# ---- 7. validation (RuntimeError from ll_run whose message names the ping, as test_pulse does for the pulse) -----

def _reject(scn):
    with pytest.raises(RuntimeError, match="ping"):
        runmod.run(scn, seed=0)


def test_validation_baseline_runs():
    """Positive control for every validation test below: the plain valid ping scenario runs, and so does one with
    every ping rule at zero (SPEC 15.3: finite and >= 0 includes 0), and one with ping_layer left at the loader's
    default 0 and ping_tick -1 (the layer is only checked for ping_tick >= 0)."""
    assert runmod.run(ping_scn(), seed=0).ticks > 0
    zero = ping_scn(rules={"ping_reach": 0.0, "ping_radius": 0.0, "ping_s": 0.0, "ping_cooldown_s": 0.0})
    assert runmod.run(zero, seed=0).ticks > 0
    idle = ping_scn(ping_tick=None)
    assert idle["groups"][0].get("ping_layer", 0) == 0
    assert runmod.run(idle, seed=0).ticks > 0
    off = ping_scn(ping_tick=-1, ping_extra={"ping_layer": 9})
    assert runmod.run(off, seed=0).ticks > 0


@pytest.mark.parametrize("tick", [-2, -100])
def test_validation_ping_tick_below_minus_one_rejected(tick):
    """SPEC 15.3 (ll_ping_validate: ping_tick >= -1): -2 and -100 are rejected; -1 (no ping) is the baseline."""
    _reject(ping_scn(ping_tick=tick))


@pytest.mark.parametrize("layer", [0, 6, -1, 100])
def test_validation_ping_layer_outside_one_to_five_rejected_when_pinging(layer):
    """SPEC 15.3 (for ping_tick >= 0 ping_layer in 1..5): 0, 6, -1 and 100 are rejected with a ping ordered."""
    _reject(ping_scn(layer=layer))


@pytest.mark.parametrize("key", ["ping_x", "ping_y"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_validation_non_finite_ping_place_rejected_when_pinging(key, bad):
    """SPEC 15.3 (for ping_tick >= 0 ping_x and ping_y finite): NaN, +inf and -inf in either coordinate are rejected."""
    scn = ping_scn()
    scn["groups"][0][key] = bad
    _reject(scn)


@pytest.mark.parametrize("rule", ["ping_reach", "ping_radius", "ping_s", "ping_cooldown_s"])
@pytest.mark.parametrize("bad", [-1.0, -0.001, float("nan"), float("inf"), float("-inf")])
def test_validation_ping_rules_must_be_finite_and_non_negative(rule, bad):
    """SPEC 15.3 (rules.ping_reach, ping_radius, ping_s and ping_cooldown_s finite and >= 0): negative, NaN and
    infinite values are rejected, whether or not a ping is ordered."""
    _reject(ping_scn(rules={rule: bad}))
    _reject(ping_scn(ping_tick=None, rules={rule: bad}))


# ---- 8. legacy: no ping means the old results, byte for byte; the pulse still works ------------------------------

def _fight():
    """A small cross-layer fight with movement and shooting, no ping keys anywhere."""
    groups = [grp("A", "raider", 1200.0, 900.0, 1, count=4, order="attack_move", goal=[2600.0, 1000.0]),
              grp("A", "warden", 1000.0, 1100.0, 2, count=2, order="attack_move", goal=[2600.0, 1000.0]),
              grp("B", "raider", 2800.0, 1000.0, 1, count=4, order="attack_move", goal=[1200.0, 1000.0]),
              grp("B", "interceptor", 2900.0, 1100.0, 2, count=2, order="attack_move", goal=[1200.0, 1000.0])]
    return make_scenario(groups, rules={"range_mult": table9(m1=1, z=1, p1=1), "dmg_mult": table9(m1=1, z=1, p1=1)},
                         run={"max_ticks": 400, **LONG})


def test_ping_tick_minus_one_everywhere_equals_no_ping_keys_at_all():
    """SPEC 15 ('every new field is inert at its default') and 15.4: a fight whose groups carry ping_tick -1 (with
    arbitrary ping_layer, ping_x, ping_y, which must be ignored) and whose rules carry other ping numbers (reach 5,
    radius 99999, ping_s 9, cooldown 0) gives result bytes and trace bytes identical to the same fight with no
    ping keys. Non-vacuous: shots happened and the alert fields read -1, 0, 0."""
    plain = runmod.run(_fight(), seed=11, trace=True)
    assert plain.shots[0] > 0 and plain.shots[1] > 0
    assert_no_alert(plain)

    keyed = _fight()
    for g in keyed["groups"]:
        g.update(ping_tick=-1, ping_layer=3, ping_x=1234.0, ping_y=777.0)
    keyed["rules"].update(ping_reach=5.0, ping_radius=99999.0, ping_s=9.0, ping_cooldown_s=0.0)
    res = runmod.run(keyed, seed=11, trace=True)
    assert res.raw == plain.raw
    assert np.ascontiguousarray(res.trace).tobytes() == np.ascontiguousarray(plain.trace).tobytes()


def _pulse_and_ping(*, ping):
    """Unit 0 pulser (A, layer 5, (2000, 1000), pulse at tick 30, reveals radius 500); unit 1 seer pinger (A,
    layer 5, (1000, 1500)) aimed at layer 1 at (1100, 1500) at tick 100 when `ping`; unit 2 raider B layer 1 at
    (2300, 1000) (300 from the pulser: pulse only); unit 3 raider B layer 1 at (1100, 1500) (1030 from the pulser:
    ping only)."""
    kw = {"ping_tick": 100, "ping_layer": 1, "ping_x": 1100.0, "ping_y": 1500.0} if ping else {}
    groups = [grp("A", "pulser", 2000.0, 1000.0, 5, pulse_tick=30), grp("A", "seer", 1000.0, 1500.0, 5, **kw),
              grp("B", "raider", 2300.0, 1000.0, 1), grp("B", "raider", 1100.0, 1500.0, 1)]
    scn = make_scenario(groups, rules={"spawn_jitter": 0.0}, run={"max_ticks": 200, **LONG})
    return add_type(scn, "pulser", "interceptor", pulse_capable=1)


def test_the_pulse_still_works_beside_a_ping_and_is_not_an_alert():
    """SPEC 15.3 (the scripted pulse of 5.7 stays) and 15.4: a pulse at tick 30 and a ping at tick 100 in one scenario
    are independent. The pulse reveals its raider for its 40-tick window (start at 30 or 31 as test_pulse allows,
    exactly 40 long) and the ping reveals the other raider for exactly 10 ticks from 100 (the pulse does not
    reveal it: 1030 away; the ping does not reveal the first). Only the ping alerts: alerts[B] == 1, alerted_tick[B]
    == 100. Pulse alone (no ping ordered) leaves the alert fields at -1, 0, 0 (passes before the ping exists)."""
    res = runmod.run(_pulse_and_ping(ping=True), seed=0, trace=True)
    w = windows(vis(res, 2))
    assert len(w) == 1 and 30 <= w[0][0] <= 31 and w[0][1] - w[0][0] + 1 == 40, w
    assert_window(res, 3, 100, N)
    assert res.alerted_tick == (-1, 100) and res.alerts == (0, 1)

    pulse_only = runmod.run(_pulse_and_ping(ping=False), seed=0, trace=True)
    assert len(windows(vis(pulse_only, 2))) == 1
    assert_never_seen(pulse_only, 3)
    assert_no_alert(pulse_only)


# ---- 9. determinism ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [0, 1, 7])
def test_ping_scenario_is_byte_identical_across_o0_and_o2_and_across_repeats(seed):
    """SPEC 9 and E-01 R-004-05 (determinism is a contract): a scenario with two pings and shooting (the _alert_scn
    shape with a 'gun' ally firing on what the pings reveal) gives identical result bytes and trace bytes on lib O0
    and O2, and on a repeat of the same lib. Non-vacuous (fails while the ping is a stub): the pings alerted B
    twice and the ally shot."""
    def scn():
        ally = [grp("A", "gun", 2000.0, 1100.0, 5),
                grp("A", "seer", 1700.0, 1300.0, 5, ping_tick=45, ping_layer=1, ping_x=1850.0, ping_y=900.0)]
        s = _alert_scn(extra=ally, fire=True, rules={"spawn_jitter": 10.0})
        return s

    a = runmod.run(scn(), seed=seed, trace=True, lib="O0")
    b = runmod.run(scn(), seed=seed, trace=True, lib="O2")
    c = runmod.run(scn(), seed=seed, trace=True, lib="O2")
    assert a.alerts == (0, 2) and a.shots[0] > 0, "the pings must have revealed and the ally must have shot"
    assert a.raw == b.raw == c.raw
    ta, tb, tc = (np.ascontiguousarray(r.trace).tobytes() for r in (a, b, c))
    assert ta == tb == tc
