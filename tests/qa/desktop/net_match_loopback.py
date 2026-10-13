# spec: docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md (W6 clerk: two-process loopback match), lane F
"""Two Godot instances in one lockstep match over autoload/net/loopback_transport.gd.

Run: pytest tests/qa/desktop/net_match_loopback.py   (or python tests/qa/desktop/net_match_loopback.py)

RED ON MAIN for the missing piece: autoload/qa_daemon.gd has no net_* verbs. The in-process
loopback transport cannot span two OS processes, so lane F must add daemon verbs that drive
NetMatch on each instance. The interface this test fixes (daemon verbs, all newline-JSON):
  net_loopback_start <role "host"|"guest"> <peer_qa_port:int> <mission_seed:int>
        -> {ok, result:{active:bool}}  builds NetMatch with loopback_transport (the two daemons
           relay transport frames to each other through the peer's qa port); host starts the mission.
  net_run <steps:int>   -> {ok, result:{steps:int}}   pumps NetMatch.session.poll() until `steps`
                           lockstep steps ran locally (no wall clock).
  net_frame             -> {ok, result:{tick:int, checksum:int, units:int}}  the tactical frame.
  net_command <cmd:dict>-> {ok, result:{queued_for_tick:int}}  NetMatch.command(cmd).
"""
from __future__ import annotations

import pytest

from daemon_client import GodotGame, pick_free_port

TOTAL_STEPS = 300
CHECK_EVERY = 50
MISSION_SEED = 1
BOOT_TIMEOUT_S = 60.0


def _ok(resp: dict, what: str) -> dict:
    assert resp.get("ok"), "%s failed: %r" % (what, resp)
    return resp["result"]


@pytest.fixture(scope="module")
def match():
    p_host, p_guest = pick_free_port(47500, 47549), pick_free_port(47550, 47599)
    host = GodotGame(qa_port=p_host, seed=MISSION_SEED)
    guest = GodotGame(qa_port=p_guest, seed=MISSION_SEED)
    host.start()
    guest.start()
    try:
        host.wait_for_port(timeout=BOOT_TIMEOUT_S)
        guest.wait_for_port(timeout=BOOT_TIMEOUT_S)
        r = _ok(guest.client.call("net_loopback_start", "guest", p_host, MISSION_SEED), "guest start")
        r2 = _ok(host.client.call("net_loopback_start", "host", p_guest, MISSION_SEED), "host start")
        assert r.get('active') and r2.get('active'), 'match not active: guest %r host %r' % (r, r2)
        yield host, guest
    finally:
        host.stop()
        guest.stop()


def _frame(g: GodotGame) -> dict:
    return _ok(g.client.call("net_frame"), "net_frame")


def test_300_steps_equal_ticks_and_checksums_every_50(match):
    host, guest = match
    for done in range(CHECK_EVERY, TOTAL_STEPS + 1, CHECK_EVERY):
        _ok(host.client.call("net_run", CHECK_EVERY), "host run")
        _ok(guest.client.call("net_run", CHECK_EVERY), "guest run")
        fh, fg = _frame(host), _frame(guest)
        assert fh["tick"] == fg["tick"], "step %d: host tick %r != guest tick %r" % (done, fh["tick"], fg["tick"])
        assert fh["checksum"] == fg["checksum"], "step %d: host checksum %r != guest %r" % (done, fh["checksum"], fg["checksum"])
    assert _frame(host)["tick"] >= TOTAL_STEPS


def test_command_on_one_peer_changes_the_others_frame(match):
    host, guest = match
    before = _frame(guest)
    _ok(host.client.call("net_command", {"kind": "move", "units": [0], "x": 10.0, "y": 10.0}), "host command")
    _ok(host.client.call("net_run", CHECK_EVERY), "host run")
    _ok(guest.client.call("net_run", CHECK_EVERY), "guest run")
    after_g, after_h = _frame(guest), _frame(host)
    assert after_g["checksum"] != before["checksum"], "guest frame unchanged after host command"
    assert after_g["checksum"] == after_h["checksum"], "peers diverged after the command"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-x", "-q"]))
