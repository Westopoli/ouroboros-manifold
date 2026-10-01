"""Pulse tests (SPEC.md 5.7; E-01 S-006, R-006-01 to R-006-05) at the lab's numbers.

Numbers: pulse_radius 500, reveal 2.0 s = 40 ticks, cooldown 20.0 s = 400 ticks, 20 ticks per
second. The pulser is an interceptor copy with pulse_capable = 1 on layer 5 at (2000, 1000); its
`pulse_tick` is set through the group key. Enemies are raiders on `hold` at layers 1 to 3 on the
x axis through the pulser, so default vision gives no passive sight (layers 4 or more apart: factor
0; two apart and sensor 1000 * 0.2 = 200 reaches nothing placed at 300 or more). Only the pulse can
reveal them. Spawn jitter is 0 so distances are exact.

Observation: trace flag bit3 (visible to the other side) of the ENEMY unit, plus
`first_contact_tick`. The window of a unit is the run of consecutive ticks with bit3 set.

Edges asserted (SPEC 5.7 says "pulses on that tick" and "for pulse_reveal_s seconds after", which
leaves one tick of slack about whether the trace row of tick p already shows the reveal):
  - the window START is tick p or p+1 (never before p: nothing may be revealed before the pulse);
  - the window LENGTH is exactly 40 ticks (so the end is start + 39, i.e. p+39 or p+40).
The reveal flag of tick p is read from the trace row of tick p.

R-006-03 (cooldown): one unit has exactly one `pulse_tick`, so a second pulse attempt inside the
400-tick cooldown cannot be ordered through the ABI. The cooldown is therefore tested only as far
as it is observable: over a 600-tick run exactly one window appears. A real cooldown test needs a
second pulse trigger in the contract (SPEC gap, reported).

Until the pulse is built, `ll_run` rejects any pulse_tick >= 0 with "unimplemented feature: pulse",
so the tests here fail with RuntimeError; the positive and negative twin of each test live in the
same function so none of them passes vacuously.
"""
import numpy as np
import pytest

import layerlab.run as runmod
from conftest import add_type, fire_ticks, grp, make_scenario, table9, unit_trace

P = 30                    # pulse tick
REVEAL = 40               # pulse_reveal_s 2.0 * 20 ticks per second
COOLDOWN = 400            # pulse_cooldown_s 20.0 * 20
PX, PY = 2000.0, 1000.0   # pulser position
LONG_RUN = {"stalemate_ticks": 6000}


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


def pulse_scn(enemies, *, pulse_tick=P, rules=None, terrain=None, max_ticks=200, groups_before=()):
    """Pulser (unit 0, layer 5) plus one raider group per (dx, layer) in `enemies`, enemy k is unit
    k + 1 at x = PX + dx on layer `layer`. `pulse_tick=None` leaves the pulse unordered."""
    kw = {} if pulse_tick is None else {"pulse_tick": pulse_tick}
    groups = [grp("A", "pulser", PX, PY, 5, **kw)] + list(groups_before)
    groups += [grp("B", "raider", PX + dx, PY, layer) for dx, layer in enemies]
    r = {"spawn_jitter": 0.0}
    r.update(rules or {})
    scn = make_scenario(groups, rules=r, terrain=terrain, run={"max_ticks": max_ticks, **LONG_RUN})
    return add_type(scn, "pulser", "interceptor", pulse_capable=1)


def check_window(vis, start_at=P, length=REVEAL):
    """Exactly one window, starting at start_at or start_at + 1, of exactly `length` ticks."""
    w = windows(vis)
    assert len(w) == 1, w
    s, e = w[0]
    assert start_at <= s <= start_at + 1, w
    assert e - s + 1 == length, w
    return s, e


# ---- R-006-01: reveal inside the radius for 40 ticks, nothing outside ----------------------------

def test_r006_01_enemies_in_radius_revealed_for_forty_ticks_outside_never():
    """R-006-01: pulser on layer 5, enemies on layer 1 at xy 100, 300 and 480 (inside radius 500)
    are revealed for exactly 40 ticks starting at tick p or p+1 (edge asserted: start in [p, p+1],
    length exactly 40). Enemies at 520 and 800 (outside, negative) are never revealed. Twin: the
    same scenario with no pulse_tick reveals nobody and first_contact_tick is -1."""
    enemies = [(100, 1), (-300, 1), (480, 1), (-520, 1), (800, 1)]
    res = runmod.run(pulse_scn(enemies), seed=0, trace=True)
    for i in (1, 2, 3):
        check_window(unit_trace(res, i).visible)
    for i in (4, 5):
        assert not unit_trace(res, i).visible.any(), "enemy outside the pulse radius was revealed"

    ctl = runmod.run(pulse_scn(enemies, pulse_tick=None), seed=0, trace=True)
    for i in range(1, 6):
        assert not unit_trace(ctl, i).visible.any()
    assert ctl.first_contact_tick == -1


@pytest.mark.parametrize("layer", [1, 2, 3])
def test_r006_01_reveals_any_layer_below_the_pulser(layer):
    """R-006-01 ('any layer'): an enemy at xy 300 on layer 1, 2 or 3 (two or more below the pulser,
    no passive sight at 300) is revealed for 40 ticks. Negative control in the same run: an enemy at
    xy 700 on the same layer is not."""
    res = runmod.run(pulse_scn([(300, layer), (-700, layer)]), seed=0, trace=True)
    check_window(unit_trace(res, 1).visible)
    assert not unit_trace(res, 2).visible.any()


def test_r006_01_pulse_radius_is_planar_layer_spacing_does_not_shrink_it():
    """SPEC 5.7 ('within pulse_radius ... (xy)'): the pulse radius is measured in xy only, so a large
    layer_spacing (vertical term of the passive-sight distance) does not change who is revealed: the
    enemy at 300 is still revealed (positive), the one at 520 still is not (negative)."""
    res = runmod.run(pulse_scn([(300, 1), (-520, 1)], terrain={"layer_spacing": 1000.0}), seed=0, trace=True)
    check_window(unit_trace(res, 1).visible)
    assert not unit_trace(res, 2).visible.any()


# ---- R-006-02: hidden again after the window ------------------------------------------------------

def test_r006_02_enemy_hidden_again_after_the_window():
    """R-006-02: the revealed layer-1 enemy has bit3 clear from the end of the window (tick p+40 or
    p+41, one tick of slack) to the end of a 200-tick run, and is visible through the interior of
    the window (p+2 .. p+38) (positive). Negative twin: an enemy on layer 4 at 300, which the pulser
    sees passively (sensor 1000 * 0.5), stays visible after the window, so 'hidden again' only
    happens when no passive detection applies."""
    res = runmod.run(pulse_scn([(300, 1), (-300, 4)]), seed=0, trace=True)
    vis = unit_trace(res, 1).visible
    assert vis[P + 2:P + 39].all()
    assert not vis[P + REVEAL + 1:].any()
    passive = unit_trace(res, 2).visible
    assert passive[P + REVEAL + 1:].all() and passive[:P].all()


# ---- R-006-03: cooldown (as far as the ABI lets it be observed) -----------------------------------

def test_r006_03_one_pulse_one_window_over_a_run_longer_than_the_cooldown():
    """R-006-03: cooldown 400 ticks. One unit has one pulse_tick, so a second attempt cannot be
    ordered (SPEC gap, see module docstring); asserted instead: over a 600-tick run (1.5 cooldowns)
    exactly one window appears (positive: one window exists, so the count is not vacuous).
    Second case: a pulse_tick of 500 is honoured late (window starts at 500 or 501, length 40), and
    again only one window appears. Negative twin: no pulse_tick gives zero windows."""
    res = runmod.run(pulse_scn([(300, 1)], max_ticks=600), seed=0, trace=True)
    assert len(res.trace) == 600
    check_window(unit_trace(res, 1).visible)

    late = runmod.run(pulse_scn([(300, 1)], pulse_tick=500, max_ticks=600), seed=0, trace=True)
    check_window(unit_trace(late, 1).visible, start_at=500)

    none = runmod.run(pulse_scn([(300, 1)], pulse_tick=None, max_ticks=600), seed=0, trace=True)
    assert windows(unit_trace(none, 1).visible) == []


# ---- R-006-04: interference halves the radius ------------------------------------------------------

def _zone(layer=5, x=PX, y=PY, r=400.0, intensity=0.5):
    return {"zone": [{"x": x, "y": y, "r": r, "intensity": intensity, "layer": layer}]}


def test_r006_04_interference_at_the_pulser_halves_the_radius():
    """R-006-04: a zone of intensity 0.5 on the pulser's layer centred on the pulser gives interference
    0.5 at the pulser, radius 500 * (1 - 0.5) = 250. Enemy at xy 300: revealed without the zone
    (positive) and NOT with it (negative). Enemy at xy 200: revealed with the zone (positive)."""
    enemies = [(300, 1), (-200, 1)]
    free = runmod.run(pulse_scn(enemies), seed=0, trace=True)
    check_window(unit_trace(free, 1).visible)
    check_window(unit_trace(free, 2).visible)

    zoned = runmod.run(pulse_scn(enemies, terrain=_zone()), seed=0, trace=True)
    assert not unit_trace(zoned, 1).visible.any(), "radius not halved: 300 still revealed"
    check_window(unit_trace(zoned, 2).visible)


def test_r006_04_zone_on_another_layer_or_not_covering_the_pulser_changes_nothing():
    """R-006-04 negative twins (zones apply on the pulser's own layer and only inside their radius,
    SPEC 5.2 step 2): a zone on layer 4 centred on the pulser, and a layer-5 zone whose disc is 800
    away from the pulser, both leave the enemy at 300 revealed for 40 ticks. Positive control: the
    layer-5 zone on the pulser hides it (see the test above), re-asserted here."""
    enemies = [(300, 1)]
    for terrain in (_zone(layer=4), _zone(x=PX + 800.0, r=100.0)):
        res = runmod.run(pulse_scn(enemies, terrain=terrain), seed=0, trace=True)
        check_window(unit_trace(res, 1).visible)
    hidden = runmod.run(pulse_scn(enemies, terrain=_zone()), seed=0, trace=True)
    assert not unit_trace(hidden, 1).visible.any()


# ---- R-006-05: layer 5 observer reveals layer 1; the reveal is one-way and ends --------------------

def test_r006_05_reveal_is_one_way_and_deals_no_damage_by_itself():
    """R-006-05: observer on layer 5, enemy on layer 1 at 300 (default rules: cross-layer fire off).
    The enemy is revealed for 40 ticks and hidden again afterwards (positive). The reveal changes
    nothing else (negative): the pulser is never visible to the enemy side, no shots, no damage,
    full enemy HP at the last tick."""
    res = runmod.run(pulse_scn([(300, 1)]), seed=0, trace=True)
    s, e = check_window(unit_trace(res, 1).visible)
    assert not unit_trace(res, 1).visible[e + 2:].any()
    assert not unit_trace(res, 0).visible.any(), "the pulse revealed the pulser to the enemy"
    assert res.shots == (0, 0)
    assert res.damage_dealt == (0.0, 0.0)
    assert unit_trace(res, 1).hp[-1] == pytest.approx(250.0)


def test_r006_05_revealed_enemy_is_targetable_only_inside_the_window():
    """R-006-05 / SPEC 5.4 ('there is no second visibility function'): with the layer-5 to layer-1
    fire tables on (offset 0) and the enemy at xy 200 (pulser range 250), the pulser fires at it
    during the window (positive: at least one shot, every shot inside p .. p+41, none before p) and
    the enemy never fires back (negative: it cannot see layer 5). Twin without a pulse: no shot and
    no damage at all."""
    on = table9(m4=1)
    rules = {"range_mult": on, "dmg_mult": on}
    res = runmod.run(pulse_scn([(200, 1)], rules=rules), seed=0, trace=True)
    shots = fire_ticks(res, 0)
    assert len(shots) >= 1
    assert shots.min() >= P and shots.max() <= P + REVEAL + 1, shots
    assert res.damage_dealt[0] > 0 and res.damage_dealt[1] == 0.0
    assert not fire_ticks(res, 1).size

    ctl = runmod.run(pulse_scn([(200, 1)], rules=rules, pulse_tick=None), seed=0, trace=True)
    assert ctl.shots == (0, 0) and ctl.damage_dealt == (0.0, 0.0)


# ---- the pulser needs no passive sight; first contact is the pulse -----------------------------------

def test_pulse_is_first_contact_without_passive_sight():
    """R-006-01 / SPEC 5.11 (first_contact_tick: first tick any side_sees entry is set): the pulser
    cannot see the layer-1 enemy passively, yet first_contact_tick is the pulse tick (p or p+1, and
    equal to the first visible trace tick). Negative twin: no pulse_tick gives first_contact_tick -1."""
    res = runmod.run(pulse_scn([(300, 1)]), seed=0, trace=True)
    start, _ = check_window(unit_trace(res, 1).visible)
    assert res.first_contact_tick == start
    assert P <= res.first_contact_tick <= P + 1

    ctl = runmod.run(pulse_scn([(300, 1)], pulse_tick=None), seed=0, trace=True)
    assert ctl.first_contact_tick == -1


# ---- a killed pulser ends the reveal -------------------------------------------------------------------

def _killer_scn(killer_dx):
    """Fragile pulser (hp 10, interceptor otherwise) pulses at tick 2 on layer 5; a raider killer on
    layer 5 at xy distance |killer_dx| on hold (range 200, two hits of 9 kill it: dead between about
    tick 16 and 33); a bystander A unit far away keeps side A alive so the run goes on and the trace
    after the death is not empty; the layer-1 target enemy sits at xy 300 on the other side."""
    scn = pulse_scn([(-300, 1)], pulse_tick=2, max_ticks=120,
                    groups_before=[grp("A", "interceptor", 300.0, 200.0, 5),
                                   grp("B", "raider", PX + killer_dx, PY, 5)])
    scn["types"]["pulser"]["hp"] = 10.0
    return scn   # units: 0 pulser, 1 bystander, 2 killer, 3 target


def test_pulser_killed_during_the_window_ends_the_reveal():
    """SPEC 5.7 ('if the pulser is alive'): the pulser pulses at tick 2 and is killed by a raider on
    its own layer 150 away before the 40-tick window would end. The layer-1 target is revealed at
    the start (positive) and never visible more than one tick after the pulser's death (the death
    tick may still show the reveal, one tick of slack). Negative twin: the same killer 600 away
    cannot reach it (range 200), the pulser lives and the window runs its full 40 ticks."""
    res = runmod.run(_killer_scn(150.0), seed=0, trace=True)
    dead = np.flatnonzero(unit_trace(res, 0).alive == 0)
    assert dead.size, "pulser should have been killed"
    d = int(dead[0])
    assert 2 + 5 < d < 2 + REVEAL - 1, "the kill must land inside the window for this test to bite"
    vis = unit_trace(res, 3).visible
    assert vis[2:d - 1].all(), "target should be revealed from the pulse until the pulser dies"
    assert not vis[d + 2:].any(), "reveal outlived the pulser"

    safe = runmod.run(_killer_scn(600.0), seed=0, trace=True)
    assert unit_trace(safe, 0).alive.all()
    check_window(unit_trace(safe, 3).visible, start_at=2)


# ---- validation ----------------------------------------------------------------------------------------

def test_pulse_tick_on_a_non_pulse_capable_unit_is_rejected():
    """SPEC 5.7 ('A pulse_capable unit with spawn.pulse_tick >= 0 pulses'): a unit whose type has
    pulse_capable = 0 and pulse_tick >= 0 is rejected by validation: RuntimeError whose message
    mentions pulse and is not the 'unimplemented feature' stub. Controls: pulse_tick unset on a
    non-capable unit runs fine (passes today by design); the same pulse_tick on a pulse_capable
    unit runs fine (positive; red until the pulse exists)."""
    plain = pulse_scn([(300, 1)], pulse_tick=None)
    plain["groups"][0]["type"] = "interceptor"
    assert runmod.run(plain, seed=0).first_contact_tick == -1

    bad = pulse_scn([(300, 1)])
    bad["groups"][0]["type"] = "interceptor"
    with pytest.raises(RuntimeError, match="pulse") as exc:
        runmod.run(bad, seed=0)
    assert "unimplemented" not in str(exc.value)

    ok = runmod.run(pulse_scn([(300, 1)]), seed=0)
    assert ok.first_contact_tick >= 0
