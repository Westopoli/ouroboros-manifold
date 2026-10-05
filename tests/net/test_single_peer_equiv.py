"""One peer through net_submit and net_step gives the same checksum trace as the same
commands through today's command and tactical_step verbs (R-139-04).

"Delay 0" here: a command issued after s ticks is stamped s+1, the first tick not
yet begun, so it applies in the next step exactly as `command` then
`tactical_step` does."""
import pytest

from driver import CHECK_EVERY, REISSUE, make_script, net_available, run_ticks, start_mission
from harness import Pipe

pytestmark = pytest.mark.skipif(not net_available(), reason="pipe has no net_reset yet (lockstep spec, pipe lane)")


def test_net_verbs_equal_command_and_tactical_step():
    a, b = Pipe(), Pipe()
    try:
        info = start_mission(a, 3)
        start_mission(b, 3)
        script = make_script(info["mine"], info["target"])
        ticks = min(run_ticks(info["deadline"]), 2000)
        seq = 0
        for s in range(0, ticks, CHECK_EVERY):
            for c in script(0, 1, s):  # s is a multiple of 10, so a reissue lands on a batch edge
                r = a.send("net_submit", tick=s + 1, peer=0, seq=seq, verb=c["verb"], arg=0, layer=0,
                           x=c["x"], y=c["y"], units=c["units"])
                assert r["type"] == "net_ack" and r.get("code", 0) == 0, r
                seq += 1
                r = b.send("command", verb="attack_move", units=c["units"], x=c["x"], y=c["y"])
                assert r["type"] == "ack", r
            for k in range(CHECK_EVERY):
                ra = a.send("net_step", n=1)
            assert "checksum" in ra and ra["tick"] == s + CHECK_EVERY, ra
            b.send("tactical_step", n=CHECK_EVERY)
            rb = b.send("net_checksum")
            assert rb["type"] == "net_ack", rb
            assert ra["checksum"] == rb["checksum"], "diverged at tick %d" % (s + CHECK_EVERY)
        assert ticks >= REISSUE
    finally:
        a.close()
        b.close()
