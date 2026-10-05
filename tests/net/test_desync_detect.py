"""Positive control for the checksum detector: one move command withheld from one
peer must show as a checksum mismatch, naming the tick and the movement or units
section, within 10 ticks of the tick it was due (R-140-03)."""
import pytest

from driver import SECTIONS, FakeNet, net_available, open_cluster

pytestmark = pytest.mark.skipif(not net_available(), reason="pipe has no net_reset yet (lockstep spec, pipe lane)")


def test_withheld_command_is_detected_within_ten_ticks():
    # Peer 0's first command (seq 0) is stamped tick 3; peer 1 never submits it.
    cl, _, pipes, _ = open_cluster(2, net=FakeNet(5, delay=(1, 2)), withhold=(1, 0, 0))
    try:
        cl.run(40)
        mm = cl.first_mismatch()
        assert mm is not None, "withheld command went undetected"
        tick, diff, sums = mm
        assert 3 <= tick <= 3 + 10, "mismatch at tick %d, command was due at tick 3" % tick
        assert set(diff) & {"movement", "units"}, "sections named %r, expected movement or units" % diff
        assert set(diff) <= set(SECTIONS)
    finally:
        for pp in pipes:
            pp.close()


def test_without_the_withheld_command_the_same_run_is_equal():
    cl, _, pipes, _ = open_cluster(2, net=FakeNet(5, delay=(1, 2)))
    try:
        cl.run(40)
        assert cl.first_mismatch() is None
    finally:
        for pp in pipes:
            pp.close()
