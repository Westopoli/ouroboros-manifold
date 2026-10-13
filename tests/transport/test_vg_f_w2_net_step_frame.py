"""Lane F, piece W2 contract side (net_step frame flag) feeding PipeSim.

Spec: docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md "What the Fable audit changed" (the frame is
opt-in: `net_step {"n":1,"frame":true}` answers `net_ack` first, then one `tactical` frame, full or delta by the
`tactical_step` rule) and visible-game spec section 2 (unit object, `state` always present). Stories S-140
(Commands over the wire), S-142; rules R-140-02 (every peer applies the same ticks), R-139-04.

Fenced: builders never edit this file. Without `frame` the verb is unchanged (CONTROL).
"""
import importlib.util
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
_spec = importlib.util.spec_from_file_location("long_harness", ROOT / "tests/long/harness.py")
_h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_h)

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built")


def _next(pp, what="a frame"):
    """read_more() with a 5 s limit: a missing frame is a failure, not a hang (the pipe is killed)."""
    box = []
    t = threading.Thread(target=lambda: box.append(pp.read_more()), daemon=True)
    t.start()
    t.join(5.0)
    if not box:
        pp.p.kill()
        pytest.fail(f"no {what} arrived within 5 s after net_step frame:true (the frame flag is not built)")
    return box[0]


def _session(seed=1):
    pp = _h.Pipe()
    pp.cmd("set_seed", seed=seed, n_regions=_h.N_REGIONS, features=_h.FEATURES)
    pp.cmd("snapshot")
    snap = pp.read_more()
    pf = snap.get("player_faction", 0)
    assert pp.send("mission_start", faction=pf)["type"] == "mission"
    assert pp.send("mission_begin")["type"] == "tactical"
    assert pp.send("net_reset")["type"] == "net_ack"
    return pp


def test_control_net_step_without_frame_is_one_ack_only():
    """CONTROL: the unflagged verb still answers exactly one net_ack (about 15 existing tests depend on it)."""
    pp = _session()
    try:
        ack = pp.send("net_step", n=1)
        assert ack["type"] == "net_ack" and ack["tick"] == 1
    finally:
        pp.close()


def test_net_step_frame_true_answers_ack_then_tactical_with_equal_ticks():
    """S-140/R-140-02: frame:true gives net_ack, then a tactical frame whose tick equals ack.tick."""
    pp = _session()
    try:
        ack = pp.send("net_step", n=1, frame=True)
        assert ack["type"] == "net_ack" and ack["tick"] == 1, ack
        frame = _next(pp, 'tactical frame')
        assert frame["type"] == "tactical", f"net_step frame:true wrote no tactical frame after the ack: {frame.get('type')}"
        assert frame["tick"] == ack["tick"], "the frame's tick differs from the ack's (the net tick is the match tick)"
    finally:
        pp.close()


def test_frames_alternate_full_and_delta_like_tactical_step():
    """First frame full, a later one delta (units_changed), every unit with `state` present (section 2)."""
    pp = _session()
    try:
        kinds = []
        for _ in range(3):
            pp.send("net_step", n=1, frame=True)
            f = _next(pp, 'tactical frame')
            kinds.append(f)
        assert kinds[0].get("full", True) is True and "units" in kinds[0]
        delta = kinds[1]
        assert delta.get("full") is False and "units_changed" in delta, "the second frame is not a delta"
        assert all("state" in u for u in kinds[0]["units"]), "section 2: `state` always present"
    finally:
        pp.close()


def test_frame_stepping_does_not_change_the_checksum():
    """write_tactical touches no world state: the same 20 steps with and without frame:true agree (R-139-03)."""
    a, b = _session(), _session()
    try:
        ra = rb = None
        for _ in range(20):
            ra = a.send("net_step", n=1, checksum=True)
            rb = b.send("net_step", n=1, frame=True, checksum=True)
            _next(b, 'tactical frame')
        assert ra["checksum"] == rb["checksum"] and ra["sections"] == rb["sections"]
    finally:
        a.close()
        b.close()
