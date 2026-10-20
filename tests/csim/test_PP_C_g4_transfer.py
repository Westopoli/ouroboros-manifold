# Rule pins: R-001-07@8f31c3, R-002-01@6ac3b0, R-002-02@3f01e4, R-002-03@f4690a, R-002-04@5ee121, R-002-05@de5c73, R-002-06@7e0b06, R-002-07@247e37, R-004-01@61a9b6, R-004-02@7d61a4, R-004-03@c0c24d, R-004-04@9004f6
"""Phase C step G4: the hard layer transfer (E-01 S-002 and S-004; cascade brief section 5 "G4. Changing layer").

Proves R-002-01 to R-002-07 (the rules the plan adds) and R-004-01 to R-004-04, with R-001-07 (every Settled Reach
type flies). Layers are engine layers 0 to OM_LAYER_COUNT - 1 (A132): the bible's "layer 3 to layer 4" is 2 to 3.
Tick conventions: see test_PP_C_g4_support.py. Every test that proves a behaviour has a control that must trip the
detector (the same scene where the thing under test is absent), named in its docstring.

Red today, for one reason: the three calls are inert stubs (`om_command_set_layer` returns 0 and does nothing,
`om_unit_transition_progress` returns 0.0, `om_unit_get_target_layer` returns 0), so no unit ever changes layer and
no rejection is ever reported. The scenes with a blocked layer also need `om_map_block_rect`, which is a Phase A stub
until wave A4; those fail first on a named precondition (see `block_column`). Controls that need neither are green
today and say so.

Unclear rules, not tested (see the report): how long a pending transfer lives when the unit's move order completes
while the target layer is still blocked (Q-002-02 closed as "until move order completes", R-002-02 to R-002-04 say
"stays pending"); what `om_unit_get_target_layer` returns for a unit whose transfer is pending but not begun; the
rule for a route that changes layer while a transfer is pending (R-002-02 "[Q-001-05]").
"""
import pytest

from test_PP_C_g4_support import (
    BASTION, DURATION_TICKS, ENEMY, FRIEND, RAIDER, TYPE_NAME, accessible, block_column, first_begun,
    layer_count, new_world, run, set_layer, snap, spawn, step,
)

SIX = sorted(DURATION_TICKS)
OLD, NEW = 2, 3            # the bible's "layer 3 to layer 4"
UP_FAR = 4                 # the bible's "layer 3 to layer 5"
RUN_LIMIT = 80             # a loop bound for a Raider scene (20 ticks of transition plus margin), not a rule value


# ---------------------------------------------------------------- R-002-01, R-004-01, R-004-03, R-001-07

@pytest.mark.parametrize("utype", SIX, ids=[TYPE_NAME[t] for t in SIX])
def test_R_004_01_transition_takes_the_type_duration_and_crosses_over_halfway(lib, world_factory, utype):
    """R-004-01, R-002-01, R-001-07 (E-01): ordered up one layer at an open position, a unit begins on the first tick,
    is on the new layer exactly its type's transition time later (Q-004-01 as is: Raider 1.0 s = 20 ticks, Interceptor
    1.2 s = 24, Vanguard 2.5 s = 50, Warden 2.0 s = 40, Bombard 4.0 s = 80, Bastion 5.0 s = 100) and is on the layer it
    is leaving until halfway (R-004-02, Q-004-05: cross-over at half the duration). Every type flies (R-001-07), so all
    six change layer here. Today: stub, no unit ever leaves its layer; progress reads 0.0 and the target layer 0.
    Control: before the order (and for a unit never ordered) progress is 0.0 and the layer does not change."""
    d = DURATION_TICKS[utype]
    w = new_world(world_factory, lib)
    ctl = spawn(lib, w, utype, FRIEND, 1500.0, 1500.0, OLD)  # never ordered
    u = spawn(lib, w, utype, FRIEND, 300.0, 400.0, OLD)
    assert snap(lib, w, u)[:3] == (OLD, 0.0, OLD), "before any order: settled on its own layer"
    assert set_layer(lib, w, [u], NEW) == 0
    trace = run(lib, w, u, d + 5)
    assert first_begun(trace) == 1, "R-002-01: the transition begins on the first tick (target layer open here)"
    for k in range(1, d):
        layer, prog, tgt, _, _ = trace[k - 1]
        assert 0.0 < prog < 1.0, f"step {k}: progress {prog} not in (0, 1) mid-transition"
        assert tgt == NEW, f"step {k}: om_unit_get_target_layer is the layer it is moving to"
        assert layer == (OLD if k < d // 2 else NEW), f"step {k}: effective layer {layer}; cross-over at step {d // 2}"
    progs = [s[1] for s in trace[:d - 1]]
    assert progs == sorted(progs) and len(set(progs)) == len(progs), "progress rises every tick"
    layer, prog, tgt, _, _ = trace[d - 1]
    assert (layer, prog, tgt) == (NEW, 0.0, NEW), f"R-004-01: settled on the new layer after {d} ticks"
    assert snap(lib, w, u)[:3] == (NEW, 0.0, NEW), "and it stays settled"
    assert snap(lib, w, ctl)[:3] == (OLD, 0.0, OLD), "control: an unordered unit never changes layer"


def test_R_004_01_raider_is_on_the_new_layer_20_ticks_later_and_a_bastion_100(lib, world_factory):
    """R-004-01 / brief G4 test list, the two numbers in one world: ordered together up one layer, the Raider is settled
    after 20 ticks and the Bastion (still in transition, on its old layer) is not until 100."""
    w = new_world(world_factory, lib)
    r = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, OLD)
    b = spawn(lib, w, BASTION, FRIEND, 300.0, 800.0, OLD)
    assert set_layer(lib, w, [r, b], NEW) == 0
    step(lib, w, 20)
    assert snap(lib, w, r)[:3] == (NEW, 0.0, NEW)
    layer, prog, tgt, _, _ = snap(lib, w, b)
    assert 0.0 < prog < 1.0 and tgt == NEW and layer == OLD
    step(lib, w, 79)
    assert 0.0 < snap(lib, w, b)[1] < 1.0, "the Bastion is still in transition at tick 99"
    step(lib, w, 1)
    assert snap(lib, w, b)[:3] == (NEW, 0.0, NEW), "the Bastion is on the new layer at tick 100"


def test_R_004_03_completion_order_matches_transition_time_order(lib, world_factory):
    """R-004-03 (E-01): units of different types ordered to the same layer on the same tick complete in transition-time
    order, whatever the order they were listed or spawned in. Six types, listed slowest first, each at its own spot."""
    w = new_world(world_factory, lib)
    ids = {}
    for i, t in enumerate(reversed(SIX)):                      # spawned and listed slowest first
        ids[t] = spawn(lib, w, t, FRIEND, 200.0 + 250.0 * (i % 4), 300.0 + 600.0 * (i // 4), OLD)
    assert set_layer(lib, w, [ids[t] for t in reversed(SIX)], NEW) == 0
    done = {}
    for k in range(1, max(DURATION_TICKS.values()) + 5):
        step(lib, w)
        for t, u in ids.items():
            if t not in done and snap(lib, w, u)[:2] == (NEW, 0.0):
                done[t] = k
    assert set(done) == set(SIX), f"every type completed: {done}"
    by_time = sorted(SIX, key=lambda t: done[t])
    assert [DURATION_TICKS[t] for t in by_time] == sorted(DURATION_TICKS.values()), f"completion order {done}"
    assert done[RAIDER] == 20 and done[BASTION] == 100


def test_Q_002_01_a_far_transfer_is_one_transition_of_one_duration(lib, world_factory):
    """R-002-01 with Q-002-01 (a), closed: the bible's example "layer 3 to layer 5" (engine 2 to 4) is one transition
    of one duration regardless of distance. A Raider is settled on layer 4 after 20 ticks, not 40. Today: stub."""
    w = new_world(world_factory, lib)
    u = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, OLD)
    assert set_layer(lib, w, [u], UP_FAR) == 0
    step(lib, w, 20)
    assert snap(lib, w, u)[:3] == (UP_FAR, 0.0, UP_FAR)


# ---------------------------------------------------------------- R-004-02: who may attack it, and whom it attacks

def _acquire_scene(lib, world_factory, transitioning):
    """T (Raider, side 0, layer 2) with an enemy O on the old layer 2 and an enemy N on the new layer 3, each 100 wu
    away (Raider range 200, sensor 800: all in range and in sight). Same-layer targeting only (the Raider's reach is
    set to (0, 0) here; TD-VG-T-1: the scene tests transition timing, not reach, and no longer relies on the engine's
    default). When `transitioning` the transfer to layer 3 is ordered, else T stays put (the control)."""
    w = new_world(world_factory, lib)
    assert lib.om_roster_set_reach(w, RAIDER, 0, 0) == 0
    t = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, OLD)
    o = spawn(lib, w, RAIDER, ENEMY, 400.0, 400.0, OLD)
    n = spawn(lib, w, RAIDER, ENEMY, 300.0, 500.0, NEW)
    if transitioning:
        assert set_layer(lib, w, [t], NEW) == 0
    held = {"T": [], "O": [], "N": []}   # held["O"][k - 1]: whom O targets after step k
    for _ in range(24):
        step(lib, w)
        held["T"].append(lib.om_unit_get_target(w, t))
        held["O"].append(lib.om_unit_get_target(w, o))
        held["N"].append(lib.om_unit_get_target(w, n))
    return t, o, n, held


def test_R_004_02_old_layer_may_attack_until_halfway_new_layer_from_halfway_on(lib, world_factory):
    """R-004-02 (E-01; Q-004-02 as ruled by Westley 2026-09-13: "It should still be attackable by those units until the
    transition is halfway completed. New layer can attack it after it's halfway completed"; brief G4: "before tick 10
    an attacker on the old layer may target the Raider and one on the new layer may not, and the reverse from tick
    10"). Targets are acquired on a 4-tick cohort cadence, so the windows leave out the cross-over tick itself and the
    ticks right after it: O (old layer) holds T through step 9 and not after step 11; N (new layer) holds T at no step
    up to 9 and holds it by step 19. Today: stub, T never leaves layer 2, so N never targets it."""
    t, o, n, held = _acquire_scene(lib, world_factory, transitioning=True)
    assert held["O"][8] == t, "old layer attacker holds the transitioning unit at step 9"
    assert any(x == t for x in held["O"][:8]), "and acquired it before halfway"
    assert all(x != t for x in held["O"][11:]), "after the cross-over the old layer may not attack it"
    assert all(x != t for x in held["N"][:9]), "before halfway the new layer may not attack it"
    assert held["N"][18] == t and held["N"][19] == t, "from halfway on the new layer attacks it"


def test_R_004_02_the_transitioning_unit_attacks_as_a_unit_of_the_layer_it_is_leaving_then_the_one_it_moves_to(lib, world_factory):
    """R-004-02 / Q-004-05 (Westley, 2026-10-01: "A unit can attack on the layer it's leaving until it hits the
    cross-over point, then it swaps to the layer it's moving to"): T targets only O (old layer) up to step 9 and holds
    O at step 9, drops O after the cross-over and holds N (new layer) by step 19. Same windows as the test above."""
    t, o, n, held = _acquire_scene(lib, world_factory, transitioning=True)
    assert held["T"][8] == o and all(x != n for x in held["T"][:9]), "before halfway: attacks the old layer only"
    assert all(x != o for x in held["T"][11:]), "after the cross-over it no longer attacks the old layer"
    assert held["T"][18] == n and held["T"][19] == n, "from halfway on: attacks the new layer"


def test_R_004_02_control_a_unit_that_never_transitions_is_attacked_and_attacks_on_its_own_layer_only(lib, world_factory):
    """Positive control for the two tests above (the detector must trip when the layers match and stay quiet when they
    differ): with no order T stays on layer 2; O (layer 2) holds it at steps 9 and 19, N (layer 3) never does, and T
    holds O and never N. Green today: it needs no layer change."""
    t, o, n, held = _acquire_scene(lib, world_factory, transitioning=False)
    assert held["O"][8] == t and held["O"][18] == t
    assert all(x != t for x in held["N"]), "a unit on another layer never targets it (reach 0)"
    assert held["T"][8] == o and held["T"][18] == o and all(x != n for x in held["T"])


# ---------------------------------------------------------------- R-002-02: pending while blocked

def _pending_world(lib, world_factory, utype=RAIDER, layer_from=OLD, blocked=UP_FAR):
    """A unit at (550, 400) inside the column x 500..600 that is blocked on `blocked` only, so the unit's own layer is
    open there and the target layer is not. East of x = 600 every layer is open."""
    w = new_world(world_factory, lib, canvas=True)
    block_column(lib, w, blocked, blocked)
    u = spawn(lib, w, utype, FRIEND, 550.0, 400.0, layer_from)
    return w, u


def test_R_002_02_transfer_to_a_blocked_layer_stays_pending_and_begins_where_it_is_open(lib, world_factory):
    """R-002-02 (E-01): a unit under a move order is ordered to a layer that is blocked where it stands. It keeps
    executing its order on its own layer (x rises every tick, no stall) and begins the transition on the first tick it
    occupies a position where the target layer is open (the position there is open on layer 4 and the unit was in the
    blocked column on the tick before). Then it is on layer 4 after its duration. Today: stub, it never begins.
    Control: the same unit ordered the same transfer with no wall in the way begins on step 1 (test_R_004_01)."""
    w, u = _pending_world(lib, world_factory)
    lib.om_command_move(w, u, 900.0, 400.0)
    assert set_layer(lib, w, [u], UP_FAR) == 0
    trace = run(lib, w, u, RUN_LIMIT)
    b = first_begun(trace)
    assert b is not None, "the transfer never began: R-002-02 says it begins on the first open tick"
    assert b > 1, "it was pending inside the blocked column first"
    assert all(s[0] == OLD and s[1] == 0.0 for s in trace[:b - 1]), "pending: still on its own layer, no transition"
    xs = [s[3] for s in trace[:b - 1]]
    assert len(xs) >= 2 and all(b_ > a for a, b_ in zip(xs, xs[1:])), "it kept executing its move order while pending"
    bx, by = trace[b - 1][3], trace[b - 1][4]
    assert accessible(lib, w, bx, by, UP_FAR) == 1, "it begins where the target layer is open"
    assert all(accessible(lib, w, s[3], s[4], UP_FAR) == 0 for s in trace[:b - 2]), \
        "while pending it was inside the blocked column (the last pending tick is left out: whether the check runs before or after the move inside a tick is not fixed)"
    assert trace[b - 1 + 19][0] == UP_FAR and trace[b - 1 + 19][1] == 0.0, "settled one duration after it began"


def test_R_002_04_a_move_order_never_clears_a_pending_transfer(lib, world_factory):
    """R-002-04 (E-01): transfer first (pending, the layer is blocked here), then a move order out of the column: the
    transfer is still pending and begins once the unit is out; it ends on layer 4. Today: stub.
    Control: the same move with no transfer ordered never changes the unit's layer (the detector stays quiet)."""
    w, u = _pending_world(lib, world_factory)
    assert set_layer(lib, w, [u], UP_FAR) == 0
    step(lib, w, 10)
    assert snap(lib, w, u)[:2] == (OLD, 0.0), "pending: stays put on its own layer"
    lib.om_command_move(w, u, 900.0, 400.0)
    trace = run(lib, w, u, RUN_LIMIT)
    assert first_begun(trace) is not None, "the move order cleared the transfer (it never began)"
    assert trace[-1][:3] == (UP_FAR, 0.0, UP_FAR)
    wc, uc = _pending_world(lib, world_factory)
    lib.om_command_move(wc, uc, 900.0, 400.0)
    tc = run(lib, wc, uc, RUN_LIMIT)
    assert all(s[0] == OLD and s[1] == 0.0 for s in tc), "control: a move order alone changes no layer"


# ---------------------------------------------------------------- R-002-03: a second transfer replaces the first

def test_R_002_03_a_second_transfer_replaces_the_first(lib, world_factory):
    """R-002-03 (E-01): the unit starts on layer 1 in a column blocked on layers 3 and 4. A first transfer to 4 and a
    second to 3 are both pending; the first is discarded. Once out of the column the unit goes to 3 only: the layers it
    is ever on are exactly {1, 3}, it never reaches 4. Today: stub, it stays on 1 and never reaches 3.
    Control: the same scene with only the transfer to 4 ends on 4 (the detector sees a layer-4 arrival when ordered)."""
    def scene(orders):
        w = new_world(world_factory, lib, canvas=True)
        block_column(lib, w, 3, 4)
        u = spawn(lib, w, RAIDER, FRIEND, 550.0, 400.0, 1)
        for target in orders:
            assert set_layer(lib, w, [u], target) == 0
            step(lib, w, 3)
        lib.om_command_move(w, u, 900.0, 400.0)
        return {s[0] for s in (snap(lib, w, u),)} | {s[0] for s in run(lib, w, u, 120)}, snap(lib, w, u)
    seen, final = scene([4, 3])
    assert seen == {1, 3}, f"R-002-03: only the second transfer survives; layers visited {sorted(seen)}"
    assert final[:3] == (3, 0.0, 3)
    seen_c, final_c = scene([4])
    assert final_c[0] == 4 and 4 in seen_c, "control: the single transfer to 4 is carried out"


def test_R_002_03_a_same_layer_order_replaces_a_pending_transfer(lib, world_factory):
    """R-002-03 with R-002-05: a pending transfer to 4 is replaced by an order to the unit's own layer (accepted,
    completes immediately); the unit then leaves the column and never changes layer. Today: red on the wall
    precondition (Phase A stub), and once the wall is there the stub's target layer 0 is not the unit's own 2. Control:
    test_R_002_03_a_second_transfer_replaces_the_first (one order only) shows the same scene does change layer when
    the first order stands."""
    w, u = _pending_world(lib, world_factory)
    assert set_layer(lib, w, [u], UP_FAR) == 0
    step(lib, w, 3)
    assert set_layer(lib, w, [u], OLD) == 0
    lib.om_command_move(w, u, 900.0, 400.0)
    trace = run(lib, w, u, RUN_LIMIT)
    assert all(s[0] == OLD and s[1] == 0.0 and s[2] == OLD for s in trace), "the discarded transfer never begins"


# ---------------------------------------------------------------- R-002-05: same layer

def test_R_002_05_a_transfer_to_the_current_layer_completes_at_once_with_no_window(lib, world_factory):
    """R-002-05 (E-01): accepted (returns 0), completes immediately with no transition and no vulnerability window:
    progress is 0.0 and the layer and target layer are the unit's own at every tick, and the unit's effective layer
    never differs from where it started. Today: the first assertion fails because the stub `om_unit_get_target_layer`
    returns 0, not the unit's own layer 2 (the stub accepts the order and moves nothing, so the rest would hold).
    Control: a different layer on the same scene shows progress > 0 on step 1 (the detector trips), red today."""
    w = new_world(world_factory, lib)
    u = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, OLD)
    assert set_layer(lib, w, [u], OLD) == 0
    assert snap(lib, w, u)[:3] == (OLD, 0.0, OLD)
    assert all(s[:3] == (OLD, 0.0, OLD) for s in run(lib, w, u, 25))
    c = spawn(lib, w, RAIDER, FRIEND, 300.0, 1400.0, OLD)
    assert set_layer(lib, w, [c], NEW) == 0
    step(lib, w, 1)
    assert snap(lib, w, c)[1] > 0.0, "control: a real change of layer does show progress"


# ---------------------------------------------------------------- R-002-06: out of range

def test_R_002_06_a_layer_outside_the_range_is_rejected_and_changes_nothing(lib, world_factory):
    """R-002-06 (E-01) with A132 and pp_contract.md: the valid layers are 0 .. OM_LAYER_COUNT - 1 (engine numbering);
    OM_LAYER_COUNT and 0xFFFFFFFF are rejected, `om_command_set_layer` returns -1, and no unit's state changes: not its
    layer, progress or target layer. Today: the stub returns 0, so the -1 assertion fails.
    Control: the top valid layer is accepted (0) and carried out, and layer 0 is accepted."""
    count = layer_count()
    w = new_world(world_factory, lib)
    a = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, OLD)
    b = spawn(lib, w, BASTION, FRIEND, 300.0, 900.0, OLD)
    for bad in (count, count + 1, 0xFFFFFFFF):
        assert set_layer(lib, w, [a, b], bad) == -1, f"layer {bad} is out of range (count {count})"
    for u in (a, b):
        assert snap(lib, w, u)[:3] == (OLD, 0.0, OLD), "a rejected order changes nothing"
    step(lib, w, 25)
    for u in (a, b):
        assert snap(lib, w, u)[:3] == (OLD, 0.0, OLD), "and nothing starts later"
    assert set_layer(lib, w, [a], count - 1) == 0, "control: the top layer is accepted"
    assert set_layer(lib, w, [b], 0) == 0, "control: layer 0 is accepted"
    step(lib, w, 20)
    assert snap(lib, w, a)[:3] == (count - 1, 0.0, count - 1), "control: and carried out"


def test_R_002_06_a_rejected_order_leaves_a_pending_and_a_running_transfer_alone(lib, world_factory):
    """R-002-06: 'the unit's state does not change' includes what it already has. A pending transfer (blocked here) is
    not discarded by a rejected order, and a transition in flight is not disturbed by one: the pending one begins when
    the unit is out of the column, the other completes on its own tick. Today: the rejection is not reported (the stub returns 0), and the wall is absent (Phase A stub)."""
    count = layer_count()
    w, u = _pending_world(lib, world_factory)
    assert set_layer(lib, w, [u], UP_FAR) == 0
    assert set_layer(lib, w, [u], count) == -1
    lib.om_command_move(w, u, 900.0, 400.0)
    trace = run(lib, w, u, RUN_LIMIT)
    assert first_begun(trace) is not None and trace[-1][:3] == (UP_FAR, 0.0, UP_FAR), "the pending transfer survived"
    w2 = new_world(world_factory, lib)
    r = spawn(lib, w2, RAIDER, FRIEND, 300.0, 400.0, OLD)
    assert set_layer(lib, w2, [r], NEW) == 0
    step(lib, w2, 5)
    assert set_layer(lib, w2, [r], count) == -1
    step(lib, w2, 15)
    assert snap(lib, w2, r)[:3] == (NEW, 0.0, NEW), "the running transition completed on its own tick"
    step(lib, w2, 30)
    assert snap(lib, w2, r)[:3] == (NEW, 0.0, NEW), "and nothing was queued behind it"


# ---------------------------------------------------------------- R-002-07: mixed selection

def test_R_002_07_each_unit_in_a_mixed_selection_resolves_by_its_own_position_and_duration(lib, world_factory):
    """R-002-07 (E-01): one order, four units: a Raider where layer 4 is open, a Bastion where it is open, a Raider
    inside a column where it is blocked, and a Raider already on layer 4. The first is on 4 after 20 ticks; the Bastion
    is still on its old layer at 20 and is on 4 after 100; the blocked one is pending (no transition) for 60 ticks and,
    once moved out, begins on its own tick and is settled one Raider duration later; the one already there is settled
    from the start. Today: stub, nothing begins. Control: the already-there unit is settled from the start."""
    w = new_world(world_factory, lib, canvas=True)
    block_column(lib, w, UP_FAR, UP_FAR)
    r_open = spawn(lib, w, RAIDER, FRIEND, 200.0, 400.0, OLD)
    bast = spawn(lib, w, BASTION, FRIEND, 200.0, 900.0, OLD)
    r_blk = spawn(lib, w, RAIDER, FRIEND, 550.0, 1300.0, OLD)
    r_there = spawn(lib, w, RAIDER, FRIEND, 200.0, 1500.0, UP_FAR)
    assert set_layer(lib, w, [r_open, bast, r_blk, r_there], UP_FAR) == 0
    tr = {name: [] for name in ("r_open", "bast", "r_blk", "r_there")}
    ids = {"r_open": r_open, "bast": bast, "r_blk": r_blk, "r_there": r_there}
    for _ in range(100):
        step(lib, w)
        for name, u in ids.items():
            tr[name].append(snap(lib, w, u))
    assert all(s[:3] == (UP_FAR, 0.0, UP_FAR) for s in tr["r_there"]), "already on the layer: settled at once"
    assert tr["r_open"][19][:3] == (UP_FAR, 0.0, UP_FAR) and tr["r_open"][18][1] > 0.0
    assert tr["bast"][19][0] == OLD and tr["bast"][19][1] > 0.0, "the Bastion's own duration is longer"
    assert tr["bast"][98][1] > 0.0 and tr["bast"][99][:3] == (UP_FAR, 0.0, UP_FAR)
    assert all(s[0] == OLD and s[1] == 0.0 for s in tr["r_blk"]), "blocked here: pending, no transition, for 100 ticks"
    lib.om_command_move(w, r_blk, 900.0, 1300.0)
    later = run(lib, w, r_blk, RUN_LIMIT)
    b = first_begun(later)
    assert b is not None, "the blocked unit's own transfer begins once it is out of the column"
    assert later[b - 1 + 19][:3] == (UP_FAR, 0.0, UP_FAR) and later[b - 1 + 18][1] > 0.0, "one Raider duration after its begin"


# ---------------------------------------------------------------- R-004-04: a new transfer mid-transition

@pytest.mark.parametrize("issued_at", [5, 15], ids=["before_cross_over", "after_cross_over"])
def test_R_004_04_a_new_transfer_mid_transition_waits_for_the_current_one_to_complete(lib, world_factory, issued_at):
    """R-004-04 (E-01): a Raider ordered 2 to 3 is given a transfer to 4 while in flight (step 5, before the cross-over,
    or step 15, after it). The current transition completes first (settled on 3 after step 20, never on 4 before
    that, target layer still 3 until then) and the new one then runs (settled on 4 by step 41, never on 4 before the
    first transition is done); it begins as soon as the first completes. Today: stub, it never leaves layer 2.
    Control: the unit with no second order stays on 3."""
    w = new_world(world_factory, lib)
    u = spawn(lib, w, RAIDER, FRIEND, 300.0, 400.0, OLD)
    c = spawn(lib, w, RAIDER, FRIEND, 300.0, 1400.0, OLD)
    assert set_layer(lib, w, [u, c], NEW) == 0
    step(lib, w, issued_at)
    assert set_layer(lib, w, [u], UP_FAR) == 0
    layers = [snap(lib, w, u)]
    for _ in range(60 - issued_at):
        step(lib, w)
        layers.append(snap(lib, w, u))
    at = lambda k: layers[k - issued_at]
    assert at(issued_at + 1)[2] == NEW, "while the first runs, the layer it is moving to is still the first target"
    assert all(at(k)[0] != UP_FAR for k in range(issued_at, 21)), "never on 4 before the first transition is done"
    assert at(20)[0] == NEW, "the current transition completes first"
    assert at(41)[:3] == (UP_FAR, 0.0, UP_FAR), "the new transfer then completes one duration later"
    assert 0.0 < at(30)[1] < 1.0 and at(30)[2] == UP_FAR, "the second transition is in flight at step 30 (begun right after the first)"
    assert snap(lib, w, c)[:3] == (NEW, 0.0, NEW), "control: the unit with no second order is on 3 and stays"
