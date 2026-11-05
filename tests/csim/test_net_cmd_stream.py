# Rule pins: R-096-07@cc574f, R-140-02@56c964, R-242-01@e377d2
"""Lockstep command stream (docs/northstar/plans/2026-10-05-lockstep-backend-spec.md, lane "cmd").

Rules: E-19 R-140-02 (each peer's commands for a tick are applied in a fixed
peer order before the tick advances), E-19 R-242-01 (a command is stamped with
its tick and applied in the fixed peer order), E-13 R-096-07 (commands for tick
t are applied before any state advances and recorded with the tick number for
replay). Peer then seq is the spec's fixed order.

Convention under test: om_cmd_reset sets om_net_tick to 0; each om_tactical_step
begins the next tick (net tick + 1) and applies every pending command stamped
with that tick first. A command for tick T <= om_net_tick is late and refused.
RED while csrc/cmd_stream.c holds the generator's stubs. Public symbols used are
only those the spec lists plus the existing om_command_* verbs.
"""
import ctypes

from b1_macro_scene import CANVAS, PLAYER_FAC, ENEMY_FAC, RAIDER, tactical_world
from conftest import OMNetCommand, OMVec2

VERB_MOVE, VERB_ATTACK_MOVE, VERB_ATTACK_TARGET, VERB_ABILITY = 0, 1, 2, 3
CX = CANVAS / 2.0
STEPS = 200


def _arr(ids):
    return (ctypes.c_uint32 * max(len(ids), 1))(*ids)


def _cmd(tick, peer, seq, verb, n, x=0.0, y=0.0, arg=0):
    return OMNetCommand(tick=tick, seq=seq, arg=arg, x=x, y=y, peer=peer, verb=verb, layer=0, n_units=n)


def _submit(lib, w, tick, peer, seq, verb, ids, x=0.0, y=0.0, arg=0):
    c = _cmd(tick, peer, seq, verb, len(ids), x, y, arg)
    return lib.om_cmd_submit(w, ctypes.byref(c), _arr(ids))


def _scene(lib, world_factory, seed=7):
    w = tactical_world(lib, world_factory, seed=seed)
    lib.om_cmd_reset(w)
    ps = [lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, CX - 90.0 + i * 60.0, 6000.0, 0) for i in range(4)]
    es = [lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, CX - 90.0 + i * 60.0, 6900.0, 0) for i in range(4)]
    return w, ps, es


def _dest(lib, w, uid):
    d = OMVec2()
    lib.om_unit_get_order_destination(w, uid, ctypes.byref(d))
    return d.x, d.y


def _kind(lib, w, uid):
    return lib.om_unit_get_order_kind(w, uid)


def _snap(lib, w, ids):
    return tuple((lib.om_unit_get_pos(w, u), lib.om_unit_get_hp(w, u)) for u in ids)


def _log_bytes(lib, w):
    buf = (ctypes.c_uint8 * 65536)()
    n = lib.om_cmd_log_write(w, buf, 65536)
    return bytes(buf[:n])


def test_R_140_02_net_tick_zero_after_reset_and_rises_per_step(lib, world_factory):
    w, _, _ = _scene(lib, world_factory)
    assert lib.om_net_tick(w) == 0
    for k in range(1, 6):
        lib.om_tactical_step(w)
        assert lib.om_net_tick(w) == k, f"net tick after {k} steps"


def test_R_140_02_net_tick_rises_with_no_units(lib, world_factory):
    w = tactical_world(lib, world_factory)
    lib.om_cmd_reset(w)
    assert lib.om_net_tick(w) == 0
    for k in range(1, 4):
        lib.om_tactical_step(w)
        assert lib.om_net_tick(w) == k, f"net tick after {k} steps with an empty world"
    lib.om_cmd_reset(w)
    assert lib.om_net_tick(w) == 0


def test_R_096_07_command_applied_in_its_tick_not_before(lib, world_factory):
    w, ps, _ = _scene(lib, world_factory)
    assert _kind(lib, w, ps[0]) == -1, "setup: no order yet"
    assert _submit(lib, w, 3, 0, 1, VERB_MOVE, ps, CX + 1234.0, 4321.0) == 0
    assert lib.om_cmd_pending_count(w) == 1
    for _ in range(2):
        lib.om_tactical_step(w)
    assert _kind(lib, w, ps[0]) == -1, "command for tick 3 applied before the step that begins tick 3"
    assert lib.om_cmd_pending_count(w) == 1
    lib.om_tactical_step(w)
    assert _kind(lib, w, ps[0]) != -1, "command for tick 3 not applied in the step that begins tick 3"
    assert lib.om_cmd_pending_count(w) == 0


def test_R_096_07_late_command_refused_and_changes_nothing(lib, world_factory):
    w, ps, _ = _scene(lib, world_factory)
    for _ in range(3):
        lib.om_tactical_step(w)
    kind, log = _kind(lib, w, ps[0]), lib.om_cmd_log_size(w)
    for t in (3, 2, 1):
        assert _submit(lib, w, t, 0, 9, VERB_MOVE, ps, 100.0, 100.0) != 0, f"tick {t} already begun, must be refused"
    assert lib.om_cmd_pending_count(w) == 0
    lib.om_tactical_step(w)
    assert _kind(lib, w, ps[0]) == kind == -1
    assert lib.om_cmd_log_size(w) == log
    assert _submit(lib, w, 5, 0, 9, VERB_MOVE, ps, 100.0, 100.0) == 0, "positive control: a future tick is accepted"


def test_R_140_02_repeated_peer_seq_ignored(lib, world_factory):
    w, ps, _ = _scene(lib, world_factory)
    assert _submit(lib, w, 2, 1, 5, VERB_MOVE, ps, CX + 500.0, 3000.0) == 0
    assert _submit(lib, w, 2, 1, 5, VERB_MOVE, ps, CX - 500.0, 9000.0) != 0, "repeated (peer, seq) must not be accepted"
    assert lib.om_cmd_pending_count(w) == 1
    assert _submit(lib, w, 2, 1, 6, VERB_MOVE, ps, CX + 700.0, 3000.0) == 0, "positive control: a new seq is accepted"
    assert _submit(lib, w, 2, 2, 5, VERB_MOVE, ps, CX + 700.0, 3000.0) == 0, "positive control: same seq from another peer"
    assert lib.om_cmd_pending_count(w) == 3


A = (CX - 2000.0, 3000.0)
B = (CX + 2000.0, 5000.0)


def _settle(lib, w, ps, steps=30):
    for _ in range(steps):
        lib.om_tactical_step(w)
    return _snap(lib, w, ps)


def _reference(lib, world_factory, first, last):
    """Direct commands, the later-sorted one issued last, between steps 1 and 2."""
    w, ps, _ = _scene(lib, world_factory)
    lib.om_tactical_step(w)
    lib.om_command_group_move(w, _arr(ps), len(ps), *first)
    lib.om_command_group_move(w, _arr(ps), len(ps), *last)
    return _settle(lib, w, ps), _kind(lib, w, ps[0])


def _submitted(lib, world_factory, cmds):
    """cmds: (peer, seq, (x, y)) in submit order, all for tick 2."""
    w, ps, _ = _scene(lib, world_factory)
    lib.om_tactical_step(w)
    for peer, seq, (x, y) in cmds:
        assert _submit(lib, w, 2, peer, seq, VERB_MOVE, ps, x, y) == 0
    snap = _settle(lib, w, ps)
    return snap, _kind(lib, w, ps[0]), _log_bytes(lib, w)


def test_R_140_02_same_tick_applied_in_peer_order_whatever_submit_order(lib, world_factory):
    ref, ref_kind = _reference(lib, world_factory, A, B)
    other, _ = _reference(lib, world_factory, B, A)
    assert ref != other, "setup: the two orders must give different results"
    for cmds in (((0, 1, A), (1, 1, B)), ((1, 1, B), (0, 1, A))):
        snap, kind, _ = _submitted(lib, world_factory, cmds)
        assert snap == ref, f"submit order {[c[0] for c in cmds]}: result is not the one where peer 1 (later-sorted) was issued last"


def test_R_140_02_same_peer_applied_in_seq_order(lib, world_factory):
    ref, _ = _reference(lib, world_factory, A, B)
    snap, _, _ = _submitted(lib, world_factory, ((0, 2, B), (0, 1, A)))  # later seq submitted first
    assert snap == ref, "seq 2 must be applied after seq 1"


def test_R_140_02_submit_order_does_not_change_log(lib, world_factory):
    s1 = _submitted(lib, world_factory, ((0, 1, A), (1, 1, B)))
    s2 = _submitted(lib, world_factory, ((1, 1, B), (0, 1, A)))
    assert s1 == s2, "log bytes and state must not depend on submit order"
    assert len(s1[2]) > 0, "log must hold the applied commands"


def test_R_140_02_oversize_and_unknown_verb_refused(lib, world_factory):
    w, ps, _ = _scene(lib, world_factory)
    ids71 = list(range(1, 72))
    assert _submit(lib, w, 2, 0, 1, VERB_MOVE, ids71, 1.0, 1.0) != 0, "71 unit ids must be refused"
    assert _submit(lib, w, 2, 0, 2, 99, ps, 1.0, 1.0) != 0, "unknown verb must be refused"
    assert lib.om_cmd_pending_count(w) == 0
    ids70 = list(range(1, 71))
    assert _submit(lib, w, 2, 0, 3, VERB_MOVE, ids70, 1.0, 1.0) == 0, "positive control: 70 unit ids accepted"
    assert lib.om_cmd_pending_count(w) == 1


# ---- equivalence -------------------------------------------------------------

def _script(ps, es):
    """(tick, verb, unit ids, x, y, arg): the four verbs of the scripted fight."""
    return [
        (1, VERB_MOVE, ps, CX, 6400.0, 0),
        (15, VERB_ATTACK_MOVE, ps, CX, 7400.0, 0),
        (40, VERB_ATTACK_TARGET, ps[:2], 0.0, 0.0, es[0]),
        (70, VERB_ABILITY, ps[:2], CX, 7000.0, 0),
    ]


def _direct(lib, w, verb, ids, x, y, arg):
    a, n = _arr(ids), len(ids)
    if verb == VERB_MOVE:
        lib.om_command_group_move(w, a, n, x, y)
    elif verb == VERB_ATTACK_MOVE:
        lib.om_command_attack_move(w, a, n, x, y)
    elif verb == VERB_ATTACK_TARGET:
        lib.om_command_attack_target(w, a, n, arg)
    else:
        lib.om_command_activate_ability(w, a, n, x, y)


def _run_direct(lib, world_factory):
    w, ps, es = _scene(lib, world_factory)
    script = {t: (v, i, x, y, a) for t, v, i, x, y, a in _script(ps, es)}
    trace = []
    for tick in range(1, STEPS + 1):
        if tick in script:
            _direct(lib, w, *script[tick])
        lib.om_tactical_step(w)
        trace.append(_snap(lib, w, ps + es))
    return trace


def _run_submitted(lib, world_factory, with_log=False):
    w, ps, es = _scene(lib, world_factory)
    script = {t: (v, i, x, y, a) for t, v, i, x, y, a in _script(ps, es)}
    trace = []
    for tick in range(1, STEPS + 1):
        if tick in script:
            v, ids, x, y, a = script[tick]
            assert _submit(lib, w, lib.om_net_tick(w) + 1, 0, tick, v, ids, x, y, a) == 0
        lib.om_tactical_step(w)
        trace.append(_snap(lib, w, ps + es))
    return (trace, w) if with_log else trace


def test_R_096_07_submitted_commands_equal_direct_commands_for_200_ticks(lib, world_factory):
    direct = _run_direct(lib, world_factory)
    submitted = _run_submitted(lib, world_factory)
    assert len(direct) == len(submitted) == STEPS
    for k, (d, s) in enumerate(zip(direct, submitted), start=1):
        assert d == s, f"tick {k}: submitted-command state differs from direct-command state"
    assert direct[0] != direct[-1], "positive control: the scripted fight moves units"


def test_R_096_07_log_holds_exactly_the_applied_commands_in_order(lib, world_factory):
    _, w = _run_submitted(lib, world_factory, with_log=True)
    assert lib.om_cmd_pending_count(w) == 0
    log = _log_bytes(lib, w)
    assert lib.om_cmd_log_size(w) > 0 and len(log) > 0, "four applied commands must be in the log"
    # A refused and a late command leave the log unchanged.
    size = lib.om_cmd_log_size(w)
    _submit(lib, w, 1, 0, 99, VERB_MOVE, [1], 1.0, 1.0)
    assert lib.om_cmd_log_size(w) == size
    assert _log_bytes(lib, w) == log


def test_R_096_07_log_write_then_feed_replays_identically(lib, world_factory):
    trace, w = _run_submitted(lib, world_factory, with_log=True)
    log = _log_bytes(lib, w)
    assert log, "log must not be empty"
    w2, ps, es = _scene(lib, world_factory)
    buf = (ctypes.c_uint8 * len(log)).from_buffer_copy(log)
    assert lib.om_cmd_log_feed(w2, buf, len(log)) == 0
    assert lib.om_cmd_pending_count(w2) == 4, "feed loads the four logged commands into the pending buffer"
    replay = []
    for _ in range(STEPS):
        lib.om_tactical_step(w2)
        replay.append(_snap(lib, w2, ps + es))
    for k, (a, b) in enumerate(zip(trace, replay), start=1):
        assert a == b, f"tick {k}: replay differs from the recorded run"
    assert _log_bytes(lib, w2) == log, "replayed world logs the same commands"
