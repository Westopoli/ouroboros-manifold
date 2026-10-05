"""One peer stops sending at a chosen tick. The others stall, drop it after the drop
count and carry on with equal checksums (R-140-04). Drop is 100 rounds here, not the
default 1200, to keep the run short; it is a driver parameter."""
import pytest

from driver import FakeNet, net_available, open_cluster

pytestmark = pytest.mark.skipif(not net_available(), reason="pipe has no net_reset yet (lockstep spec, pipe lane)")


def test_live_peers_drop_the_silent_one_and_stay_equal():
    net = FakeNet(9, delay=(1, 2), loss=0.05)
    cl, _, pipes, _ = open_cluster(3, net=net, drop=100, drop_peer=2, drop_at=300)
    try:
        cl.run(1000)
        assert cl.tick[0] == cl.tick[1] == 1000, cl.tick
        assert {(p, s) for p, s, _, _ in cl.drop_log} == {(0, 2), (1, 2)}, cl.drop_log
        assert cl.first_mismatch([0, 1]) is None, cl.first_mismatch([0, 1])
    finally:
        for pp in pipes:
            pp.close()
