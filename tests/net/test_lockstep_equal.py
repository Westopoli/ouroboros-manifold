"""Lockstep proof: 2, 3 and 4 peers on one shared force, over a lossy reordering
network, give equal full checksums at every tenth tick to the end of a real mission
(R-139-03, R-140-02). Also the fake network's own tests, which need no pipe."""
import pytest

from driver import Cluster, FakeNet, net_available

needs_net = pytest.mark.skipif(not net_available(), reason="pipe has no net_reset yet (lockstep spec, pipe lane)")


class FakeBackend:
    """No sim: a checksum that folds every submitted command and the tick."""

    def __init__(self):
        self.t, self.h = 0, 0

    def submit(self, c):
        self.h ^= hash((c["tick"], c["peer"], c["seq"], tuple(c["units"])))
        return 0

    def step(self, n=1, checksum=False):
        self.t += 1
        r = {"type": "net_ack", "tick": self.t}
        if checksum:
            r["checksum"], r["sections"] = self.h, [self.h]
        return r


def _script(p, n, s):
    return [{"verb": 1, "arg": 0, "layer": 0, "x": 1.0, "y": 2.0, "units": [p, s]}] if s % 40 == 0 else []


def _cluster(n, seed=1, **kw):
    net = FakeNet(seed, delay=(1, 4), loss=0.15, reorder=0.3)
    return Cluster([FakeBackend() for _ in range(n)], _script, seed=seed, net=net, **kw)


def _deliveries(seed):
    net, out = FakeNet(seed, delay=(1, 4), loss=0.3, reorder=0.4), []
    for i in range(200):
        net.send(i // 4, 0, i)
    for now in range(0, 60):
        out += [(now, v) for v in net.poll(now, 0)]
    return out


def test_fakenet_is_reproducible_per_seed():
    assert _deliveries(7) == _deliveries(7)
    assert _deliveries(7) != _deliveries(8)


def test_fakenet_loses_delays_and_reorders():
    got = _deliveries(7)
    vals = [v for _, v in got]
    assert 0 < len(vals) < 200, "loss"
    assert any(now > v // 4 for now, v in got), "delay"
    assert vals != sorted(vals), "reordering"


def test_barrier_holds_until_every_packet_is_in_then_releases():
    cl = Cluster([FakeBackend(), FakeBackend()], _script, net=FakeNet(1, delay=(1, 1)))
    cl.known[0][1].pop(1)  # peer 0 has not got peer 1's packet for tick 1
    assert not cl._ready(0, 1) and cl._ready(1, 1)
    cl.known[0][1][1] = []
    assert cl._ready(0, 1)


@pytest.mark.parametrize("n", [2, 3, 4])
def test_driver_logic_keeps_peers_equal_under_loss_and_reorder(n):
    cl = _cluster(n).run(300)
    assert cl.tick == [300] * n
    assert cl.first_mismatch() is None


def test_driver_drops_a_silent_peer_after_the_drop_count_and_goes_on():
    cl = _cluster(3, drop=100, drop_peer=2, drop_at=50).run(200)
    assert cl.tick[0] == cl.tick[1] == 200
    assert {(p, s) for p, s, _, _ in cl.drop_log} == {(0, 2), (1, 2)}
    assert cl.first_mismatch([0, 1]) is None


@needs_net
@pytest.mark.parametrize("n", [2, 3, 4])
def test_peers_keep_equal_checksums_to_the_end_of_a_mission(n):
    from driver import open_cluster
    net = FakeNet(11, delay=(1, 3), loss=0.1, reorder=0.2)
    cl, ticks, pipes, _ = open_cluster(n, net=net)
    try:
        cl.run(ticks)
        assert cl.first_mismatch() is None, cl.first_mismatch()
        assert len(cl.trace[0]) >= ticks // 10
    finally:
        for pp in pipes:
            pp.close()
