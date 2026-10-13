"""Story play S-142 "No pause, no rewind": R-142-01 in a live match. Pressing the pause key does not pause: the tick
keeps advancing on both peers. Two real game processes on the Steam-less local test network (VG-F-SKEL-B; Q-F-1 closed
by Westley, 2026-10-11): the guest joins by the lobby id, the host presses Start, then Escape and P on the host. The qa
`net` key waits for a later piece (row FU-F-net-qa-key), so the check is the qa tick read before and after on each
process.
Red until VG-F-SKEL-B wires --net-local into lobby.gd: the Host button stays disabled.
"""
import time

import pytest

import _play as P


@pytest.fixture(scope="module")
def pair():
    yield from P.pair_games()


def test_s142_pause_key_does_not_pause_a_match(pair):
    host, guest = pair
    P.start_pair_match(host, guest)
    before = (int(P.tactical_qa(host.client)["tick"]), int(P.tactical_qa(guest.client)["tick"]))
    host.client.call("input", "key", "Escape")
    host.client.call("input", "key", "P")
    time.sleep(1.5)
    after_h = P.record(host.client, "S-142", "after_pause_key")["qa"]
    after = (int(after_h["tick"]), int(P.tactical_qa(guest.client)["tick"]))
    P.note("ticks before/after (host, guest):", before, after)
    assert after[0] > before[0], "the host's tick stopped after the pause key (R-142-01): %r -> %r" % (before, after)
    assert after[1] > before[1], "the guest's tick stopped after the host's pause key (R-142-01): %r -> %r" % (before, after)
