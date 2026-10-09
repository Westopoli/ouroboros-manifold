"""Story play S-108 "One unbroken shot", galaxy half: strategic time passes (step 60 ticks, as test_flow_spine does
before a mission) and the player looks at the galaxy straight after: flashes (R-106-04) and the shell tween (R-108-03).
Records right after the step (flashes live 1-2 s) and reports flashes_active/tick in the state. Does not assert a flash
occurred (a quiet 60 ticks may have none); the reviewer judges. The scroll panel / pull-back are not reached here.
"""
import time

import pytest

import _play as P


@pytest.fixture(scope="module")
def game():
    g = P.start_game()
    try:
        yield g
    finally:
        g.stop()


def test_s108_time_passes_and_the_galaxy_animates(game):
    c = game.client
    P.new_game(c)
    t0 = int(c.state()["result"]["qa"]["tick"])
    c.call("step", 60)
    time.sleep(0.4)
    qa = P.record(c, "S-108")["qa"]
    assert int(qa["tick"]) > t0, (t0, qa["tick"])
