"""Lockstep pipe verbs (spec docs/northstar/plans/2026-10-05-lockstep-backend-spec.md, lane "pipe").

Proves: net_reset, net_submit, net_step, net_checksum, net_log_dump/net_log_load,
net_state_get/net_state_put (xfail until the module save hooks land), and that the
existing command / tactical_step verbs are unchanged. Rules: E-19 R-139-03, R-139-04,
R-140-02..R-140-04, R-242-01; E-13 R-096-07; R-111-03.

Frame shapes are the spec's: net_ack {tick, code (submit), checksum, sections[]},
checksum fields present when the acked tick is a multiple of 10 or checksum:true is
asked. The log and state blobs are hex strings in a field named "hex" (the spec names
no field; the builder documents it in docs/architecture.md first, fix here if it differs).
Interactive driver: tests/long/harness.py Pipe (the batch helper cannot interleave).
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
_spec = importlib.util.spec_from_file_location("long_harness", ROOT / "tests/long/harness.py")
_h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_h)
Pipe = _h.Pipe

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")

SEED = 1
FAR = (12000.0, 9000.0)
MOVE, LAYER0 = 0, 0


class Session:
    """One pipe process in a started tactical mission, net tick 0."""

    def __init__(self, seed=SEED, reset=True):
        self.pp = Pipe()
        self.pp.cmd("set_seed", seed=seed, n_regions=_h.N_REGIONS, features=_h.FEATURES)
        self.pp.cmd("snapshot")
        snap = self.pp.read_more()
        pf = snap.get("player_faction", 0)
        m = self.pp.send("mission_start", faction=pf)
        assert m["type"] == "mission", m
        t = self.pp.send("mission_begin")
        assert t["type"] == "tactical", t
        self.begin = t
        self.mine = [u["id"] for u in t["units"] if u["faction"] == pf]
        if reset:
            ack = self.pp.send("net_reset")
            assert ack["type"] == "net_ack" and ack["tick"] == 0, ack

    def submit(self, **kw):
        f = dict(tick=1, peer=0, seq=0, verb=MOVE, arg=0, layer=LAYER0,
                 x=FAR[0], y=FAR[1], units=self.mine[:20])
        f.update(kw)
        return self.pp.send("net_submit", **f)

    def step(self, n, **kw):
        return self.pp.send("net_step", n=n, **kw)

    def positions(self):
        self.pp.cmd("snapshot")
        a = self.pp.read_more()
        if a["type"] != "tactical":
            a = self.pp.read_more()
        assert a["type"] == "tactical", a
        return {u["id"]: (u["x"], u["y"]) for u in a["units"]}

    def close(self):
        self.pp.close()


@pytest.fixture
def sess():
    s = Session()
    yield s
    s.close()


def _trace(s, cmds, ticks, start=0):
    """Step from tick `start` to `ticks` in tens; returns {tick: (checksum, sections)}."""
    out = {}
    for tick in range(start + 10, ticks + 1, 10):
        for t in range(tick - 9, tick + 1):
            for c in cmds.get(t, []):
                assert s.submit(**c)["code"] == 0, c
        a = s.step(10)
        assert a["type"] == "net_ack" and a["tick"] == tick, a
        out[tick] = (a["checksum"], a["sections"])
    return out


def _script(s):
    """A fixed command script: peer 0 and peer 1 order moves on a few ticks."""
    u = s.mine
    return {
        12: [dict(tick=12, peer=0, seq=0, units=u[:10], x=FAR[0], y=FAR[1])],
        40: [dict(tick=40, peer=1, seq=0, units=u[10:25], x=3000.0, y=2000.0)],
        41: [dict(tick=41, peer=0, seq=1, verb=1, units=u[:10], x=6000.0, y=6000.0)],
        150: [dict(tick=150, peer=1, seq=1, units=u[:30], x=9000.0, y=1000.0)],
    }


def test_net_reset_acks_tick_zero():
    s = Session(reset=False)
    try:
        a = s.pp.send("net_reset")
        assert a["type"] == "net_ack" and a["tick"] == 0, a
    finally:
        s.close()


def test_submit_accepted_code_zero(sess):
    a = sess.submit(tick=5)
    assert a["type"] == "net_ack" and a["code"] == 0, a


def test_submit_duplicate_nonzero(sess):
    assert sess.submit(tick=5, peer=0, seq=7)["code"] == 0
    a = sess.submit(tick=5, peer=0, seq=7)
    assert a["type"] == "net_ack" and a["code"] != 0, a


def test_submit_late_nonzero(sess):
    sess.step(5)
    a = sess.submit(tick=3, seq=1)
    assert a["type"] == "net_ack" and a["code"] != 0, a


def test_step_n_exact_one_ack_no_unit_frame(sess):
    a = sess.step(7)
    assert a["type"] == "net_ack" and a["tick"] == 7, a
    # no extra frame is queued: the next reply answers the next request
    b = sess.step(3)
    assert b["type"] == "net_ack" and b["tick"] == 10, b
    assert "units" not in a and "units_changed" not in a


def test_checksum_fields_on_tenth_tick_only(sess):
    a = sess.step(9)
    assert "checksum" not in a and "sections" not in a, a
    b = sess.step(1)
    assert b["tick"] == 10 and "checksum" in b, b
    assert len(b["sections"]) == 9, b


def test_checksum_true_forces_fields(sess):
    a = sess.step(3, checksum=True)
    assert a["tick"] == 3 and "checksum" in a and len(a["sections"]) == 9, a


def test_net_checksum_matches_last_ack(sess):
    a = sess.step(10)
    c = sess.pp.send("net_checksum")
    assert c["checksum"] == a["checksum"] and c["sections"] == a["sections"], (a, c)
    b = sess.step(4, checksum=True)
    c = sess.pp.send("net_checksum")
    assert c["checksum"] == b["checksum"] and c["sections"] == b["sections"], (b, c)


def test_move_applies_from_its_tick_not_before(sess):
    start = sess.positions()
    assert sess.submit(tick=6)["code"] == 0
    sess.step(5)
    assert sess.positions() == start, "units moved before the command's tick 6"
    sess.step(15)
    now = sess.positions()
    moved = [i for i in sess.mine[:20] if now[i] != start[i]]
    assert moved, "no commanded unit moved after tick 6 + 14 ticks"


def test_two_processes_equal_checksums_300_ticks():
    a, b = Session(), Session()
    try:
        ta = _trace(a, _script(a), 300)
        tb = _trace(b, _script(b), 300)
        assert ta == tb
        assert len(ta) == 30
    finally:
        a.close(); b.close()


def test_log_dump_load_replays_same_checksums():
    a = Session()
    try:
        ta = _trace(a, _script(a), 300)
        d = a.pp.send("net_log_dump")
        blob = d["hex"]
        assert isinstance(blob, str) and len(blob) > 0 and bytes.fromhex(blob)
    finally:
        a.close()
    b = Session()
    try:
        r = b.pp.send("net_log_load", hex=blob)
        assert r["type"] == "net_ack" and r.get("code", 0) == 0, r
        tb = {}
        for tick in range(10, 301, 10):
            x = b.step(10)
            tb[tick] = (x["checksum"], x["sections"])
        assert tb == ta
    finally:
        b.close()


def test_existing_command_and_tactical_step_unchanged():
    s = Session(reset=False)
    try:
        start = s.positions()
        r = s.pp.send("command", verb="move", units=s.mine[:5], x=FAR[0], y=FAR[1])
        assert r["type"] == "ack", r
        f = s.pp.send("tactical_step", n=1)
        assert f["type"] == "tactical" and f["full"] is False and f["tick"] >= 1, f
        for _ in range(19):
            f = s.pp.send("tactical_step", n=1)
        assert f["type"] == "tactical"
        assert s.positions() != start
        # and the net verbs still answer on the same process
        a = s.pp.send("net_reset")
        assert a["type"] == "net_ack" and a["tick"] == 0, a
    finally:
        s.close()


def test_state_get_put_equal_checksums_next_100_ticks():
    a = Session()
    try:
        _trace(a, _script(a), 100)
        st = a.pp.send("net_state_get")
        assert st["type"] == "net_state" and isinstance(st["hex"], str), st
        ta = _trace(a, {}, 200, start=100)
        b = Session(reset=False)
        try:
            put = b.pp.send("net_state_put", **{k: v for k, v in st.items() if k != "type"})
            assert put["type"] == "net_ack", put
            tb = {}
            for tick in range(110, 201, 10):
                x = b.step(10)
                tb[tick] = (x["checksum"], x["sections"])
            assert all(tb[k] == ta[k] for k in tb)
        finally:
            b.close()
    finally:
        a.close()
