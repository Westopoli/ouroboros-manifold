"""Phase C step G4: routing across layers by travel time (E-01 R-001-05, R-001-07, R-004-05; cascade brief section 5
"G4"; switch OM_TP_ROUTE_ACROSS_LAYERS, default 1; Q-001-05 (a), provisional: shortest by travel time, a flying unit
ends on the layer it was ordered on).

The brief's test line: "a unit ordered to a point behind a mass blocked on its layer and open above goes over when
that is quicker and around when that is quicker, and ends on its own layer; with the switch off it goes around or
stops; same seed, same ticks (R-004-05)." Terrain is hand-placed (P4 is held): the column x 500..600 from y = 0 up to
`y_hi`, blocked on engine layer 0 only (open on layers 1 to 4), on a 2000 x 2000 canvas (`om_map_set_canvas`,
`om_map_block_rect`).

- OVER wins: a Raider (speed 150, transfer 1.0 s) at (300, 400) ordered to (900, 400) behind a column up to y = 1800.
  Straight 600 wu is 4 s; up and down is 2 s of transfer on top (6 s); the way round the open end at y > 1800 is about
  3,000 wu, 20 s. Over is quicker by about 14 s.
- AROUND wins: a Bastion (speed 40, transfer 5.0 s) at (300, 450) ordered to (900, 450) behind a column from y = 0 to
  y = 600 (rows 0 to 5 are blocked, the end is open above y = 600, 150 wu away). Round is about 700 wu, 17.5 s; over is
  15 s straight plus 10 s of transfers, 25 s. Around is quicker by about 7 s.
These margins are the scene's arithmetic, not a threshold: the tests assert which route was taken and that the unit
ends on its own layer, never an arrival time in seconds.

Red today for two stacked reasons: `om_map_block_rect` and `om_map_sample_layer_accessibility` are Phase A stubs (wave
A4), so the wall is not there (every scene fails first on that named precondition, see `block_column`); and with the
wall present, `om_command_set_layer`, the transfer itself and a router that works over layers do not exist (G4 stubs;
G2's router is Phase A). Loop bounds are generous run limits that end a broken build, not rule values.
"""
import math

import pytest

from test_PP_C_g4_support import (
    BASTION, FRIEND, RAIDER, block_column, new_world, set_layer, snap, spawn, step, tp,
)

DEST_TOL = 30.0           # the same arrival radius as test_PP_move_route.py
RUN_LIMIT = 700           # ticks: far above any route in these scenes
SETTLE = 120              # extra ticks after arrival for a descent to finish
WALL_X = (500.0, 600.0)


def _in_wall(x, y, y_hi):
    return WALL_X[0] <= x < WALL_X[1] and 0.0 <= y < y_hi


def _drive(lib, w, u, dest, y_hi, limit=RUN_LIMIT):
    """Step until the unit is within DEST_TOL of dest, then SETTLE more ticks. Returns (arrival step or None, trace of
    (layer, progress, target layer, x, y) per step)."""
    trace = []
    arrive = None
    k = 0
    while k < limit:
        k += 1
        step(lib, w)
        trace.append(snap(lib, w, u))
        if arrive is None and math.hypot(trace[-1][3] - dest[0], trace[-1][4] - dest[1]) <= DEST_TOL:
            arrive = k
            limit = min(limit, k + SETTLE)
    return arrive, trace


def _over_scene(lib, world_factory, across=None):
    w = new_world(world_factory, lib, canvas=True)
    if across is not None:
        assert lib.om_tactical_set_param(w, tp("ROUTE_ACROSS_LAYERS"), across) == 0
    block_column(lib, w, 0, 0, y_hi=1800.0)
    u = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(w, u, 900.0, 400.0)
    return w, u


def _around_scene(lib, world_factory, across=None):
    w = new_world(world_factory, lib, canvas=True)
    if across is not None:
        assert lib.om_tactical_set_param(w, tp("ROUTE_ACROSS_LAYERS"), across) == 0
    block_column(lib, w, 0, 0, y_hi=600.0)
    u = spawn(lib, w, BASTION, FRIEND, 300.0, 450.0, 0)
    lib.om_command_move(w, u, 900.0, 450.0)
    return w, u


def test_R_001_05_the_switch_exists_and_defaults_to_on(lib, world_factory):
    """Brief G1/G4 and pp_contract.md section 4: `OM_TP_ROUTE_ACROSS_LAYERS` is a bool, default 1 (the game runs at the
    defaults), and it can be set to 0 and back. Green when the contract is in; here as the control that the scenes
    below really run with the switch they claim."""
    w = new_world(world_factory, lib)
    p = tp("ROUTE_ACROSS_LAYERS")
    assert lib.om_tactical_get_param(w, p) == 1.0
    assert lib.om_tactical_set_param(w, p, 0.0) == 0 and lib.om_tactical_get_param(w, p) == 0.0
    assert lib.om_tactical_set_param(w, p, 1.0) == 0 and lib.om_tactical_get_param(w, p) == 1.0


def test_R_001_05_a_unit_goes_over_a_mass_blocked_on_its_layer_when_that_is_quicker_and_ends_on_its_own_layer(lib, world_factory):
    """R-001-05 (E-01): the Raider's quickest route to (900, 400) by travel time is over the column (2 s of transfers
    beat a 20 s walk round). So: it is in the wall's cells on some layer above 0 and on layer 0 in none of them
    (R-001-01: never in a blocked cell), it arrives within 30 wu, and once settled it is on the layer it was ordered
    on, 0 (Q-001-05 (a)(2)), with no transition left and its target layer its own. Today: no wall (Phase A stub) and no
    layer change (G4 stub). Control: the next test runs the same scene round, with the switch off."""
    w, u = _over_scene(lib, world_factory)
    arrive, trace = _drive(lib, w, u, (900.0, 400.0), 1800.0)
    assert arrive is not None, "the unit never arrived"
    assert not any(_in_wall(s[3], s[4], 1800.0) and s[0] == 0 for s in trace), "never in a blocked cell on its own layer"
    assert any(_in_wall(s[3], s[4], 1800.0) and s[0] >= 1 for s in trace), "it went over the wall, on a layer above"
    assert trace[-1][:3] == (0, 0.0, 0), "it ends settled on the layer it was ordered on"


def test_R_001_05_with_the_switch_off_the_unit_stays_on_its_layer_and_goes_around_or_stops(lib, world_factory):
    """R-001-05 / brief G4: `OM_TP_ROUTE_ACROSS_LAYERS` 0 keeps the router on the unit's own layer: the same scene as
    the over test never leaves layer 0 and is never in a blocked cell; it goes round the open end or stops. And it is
    slower than going over (arrival later than the switch-on arrival of the previous test, or never): the detector
    that tells the two routes apart. Today: wall absent (Phase A stub), so the first named assertion fails."""
    w, u = _over_scene(lib, world_factory, across=0.0)
    arrive_off, trace = _drive(lib, w, u, (900.0, 400.0), 1800.0)
    assert all(s[0] == 0 and s[1] == 0.0 and s[2] == 0 for s in trace), "never changes layer with the switch off"
    assert not any(_in_wall(s[3], s[4], 1800.0) for s in trace), "never in a blocked cell"
    w1, u1 = _over_scene(lib, world_factory, across=1.0)
    arrive_on, _ = _drive(lib, w1, u1, (900.0, 400.0), 1800.0)
    assert arrive_on is not None and (arrive_off is None or arrive_on < arrive_off), \
        "control: with the switch on the unit arrives earlier (over), so the two settings are told apart"


def test_R_001_05_a_unit_goes_around_when_around_is_quicker_and_never_changes_layer(lib, world_factory):
    """R-001-05 (E-01): shortest is by travel time, so a slow Bastion (5.0 s per transfer) walks round a short mass
    (about 17.5 s) rather than go over it (about 25 s): it never leaves layer 0, never enters a blocked cell, arrives.
    Positive control for the over test (the router does not change layer just because it can): same scene as the over
    test with the roles reversed. Today: wall absent (Phase A stub)."""
    w, u = _around_scene(lib, world_factory)
    arrive, trace = _drive(lib, w, u, (900.0, 450.0), 600.0)
    assert arrive is not None, "the unit never arrived"
    assert all(s[0] == 0 and s[1] == 0.0 and s[2] == 0 for s in trace), "it stayed on layer 0 the whole way"
    assert not any(_in_wall(s[3], s[4], 600.0) for s in trace), "never in a blocked cell"
    assert any(s[4] >= 600.0 for s in trace), "it went round the open end (y above the column's top)"


def test_R_001_05_when_around_is_quicker_the_switch_changes_nothing(lib, world_factory):
    """R-001-05 / brief G4: the switch only removes the over route; where round is the quicker route the trace is
    identical with it on and off, tick for tick. Today: wall absent (Phase A stub)."""
    runs = []
    for across in (1.0, 0.0):
        w, u = _around_scene(lib, world_factory, across=across)
        runs.append(_drive(lib, w, u, (900.0, 450.0), 600.0))
    assert runs[0][0] is not None and runs[0] == runs[1]


def test_R_001_05_a_destination_behind_a_mass_blocked_on_every_layer_is_not_gone_over(lib, world_factory):
    """R-001-05 second clause (E-01): a column blocked on every layer cannot be gone over; with the switch on the unit
    paths as close as it can and stops (it advances from x = 300 and halts west of the wall), never in a blocked cell. Scene: column x 500..600, y 0..2000
    (the whole canvas), layers 0 to 4; a Raider at (300, 400) ordered to (900, 400). Today: wall absent (Phase A stub).
    Control: the same unit in the over test, with layers 1 to 4 left open, does get to the far side."""
    w = new_world(world_factory, lib, canvas=True)
    block_column(lib, w, 0, 4, y_hi=2000.0)
    u = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, 0)
    lib.om_command_move(w, u, 900.0, 400.0)
    arrive, trace = _drive(lib, w, u, (900.0, 400.0), 2000.0, limit=300)
    assert arrive is None, "it cannot arrive: the destination is cut off on every layer"
    assert not any(_in_wall(s[3], s[4], 2000.0) for s in trace), "never in a blocked cell"
    assert all(s[1] == 0.0 for s in trace), "and it does not start a futile layer change"
    assert 300.0 < trace[-1][3] < WALL_X[0], "it moved toward the destination and stopped on its own side of the wall"
    assert trace[-1][3:] == trace[-20][3:], "and it stopped (no movement over the last 20 ticks)"


def test_R_004_05_same_seed_same_commands_same_transitions_on_the_same_ticks(lib, world_factory):
    """R-004-05 (E-01): the same seed and command stream give every transition the same start and end tick. One scene
    with a routed Raider (over the wall), a Bastion on a plain transfer, and a Raider pending behind a layer-4 column
    that is moved out at tick 40; run twice at seed 1; the per-tick trace of (layer, progress, target layer, position)
    of every unit is identical. Positive control inside the test: the trace shows the transitions happened (a
    detector comparing two traces of nothing proves nothing), so the test needs the G4 build to pass. Today: wall
    absent (Phase A stub) and no transitions."""
    def play():
        w = new_world(world_factory, lib, canvas=True)
        block_column(lib, w, 0, 0, x0=500.0, x1=600.0, y_hi=1800.0)
        assert lib.om_map_block_rect(w, 1110.0, 10.0, 1190.0, 590.0, 4, 4) == 0
        r = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, 0)
        b = spawn(lib, w, BASTION, FRIEND, 300.0, 1700.0, 2)
        p = spawn(lib, w, RAIDER, FRIEND, 1150.0, 300.0, 2)
        lib.om_command_move(w, r, 900.0, 400.0)
        assert set_layer(lib, w, [b], 4) == 0
        assert set_layer(lib, w, [p], 4) == 0
        out = []
        for k in range(1, 301):
            if k == 41:
                lib.om_command_move(w, p, 1400.0, 300.0)
            step(lib, w)
            out.append([snap(lib, w, u) for u in (r, b, p)])
        return out
    a = play()
    assert a == play(), "R-004-05: the second run differs from the first"
    assert any(s[0][0] >= 1 for s in a), "control: the routed Raider changed layer (over the wall)"
    assert any(0.0 < s[1][1] < 1.0 for s in a) and a[-1][1][0] == 4, "control: the Bastion's transfer ran and finished"
    assert all(s[2][1] == 0.0 for s in a[:40]) and any(s[2][1] > 0.0 for s in a[40:]), \
        "control: the pending Raider began only after it was moved out"
