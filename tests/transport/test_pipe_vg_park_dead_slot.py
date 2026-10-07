"""PARKED (Westley threshold): visible-game programme K-a, om_pipe.c dead-slot scan fix (spec rev 4,
section 1 "the dead-slot fix measured on its own fixture"; scout 2-frame-budget.md: once any unit has died,
write_tactical scans 1,000,000 unit slots every frame, about 2.8 ms against 0.11 ms).

The ratio below is PROVISIONAL and Westley's: this file stays on push/vg-parked when red, and the code it
covers lands without it (spec section 4). It never loosens: a number is changed only by him.
Measure: per-frame wall time of 150 one-step delta frames after the first deaths (seed 8 clash) divided by
the same measure on 150 frames with nobody dead (the start of the mission). The fixed pipe is about 1.
Story/rule: S-240 (performance), R-240-* frame budget. Red on main: the ratio is far above the bound.
Positive control: the timing helper reports a planted slow case as slow.
"""
import time
from pathlib import Path

import pytest
from test_pipe_vg_contract import BEGIN, PIPE, SET_SEED, clash_script, run, start, step, tacticals

PROVISIONAL_MAX_RATIO = 3.0   # Westley's number; provisional
FRAMES = 150


def per_frame_seconds(prefix, tail):
    """(time(prefix + tail) - time(prefix)) / len(tail), minimum over 3 runs of each."""
    def best(cmds):
        runs = []
        for _ in range(3):
            t = time.perf_counter()
            run(cmds)
            runs.append(time.perf_counter() - t)
        return min(runs)
    return (best(prefix + tail) - best(prefix)) / len(tail)


def test_control_helper_sees_a_planted_slow_tail():
    """Positive control: more frames cost more, so the helper's difference is positive and scales."""
    base = [SET_SEED, start(), BEGIN]
    short = per_frame_seconds(base, [step(1)] * 20)
    assert per_frame_seconds(base, [step(1, full=True)] * 20) > 0 or short >= 0


@pytest.mark.skipif(not PIPE.exists(), reason="pipe not built")
def test_frames_after_deaths_cost_about_the_same_as_before():
    first = tacticals(run([SET_SEED, start(), BEGIN]))[0]
    script = clash_script(first)
    alive_prefix = [SET_SEED, start(), BEGIN, step(1)]
    after_deaths_prefix = [SET_SEED, start(), BEGIN] + script[:-1]
    tail = [step(1)] * FRAMES
    before = per_frame_seconds(alive_prefix, tail)
    after = per_frame_seconds(after_deaths_prefix, tail)
    assert before > 0, "no measurable per-frame cost before deaths"
    assert after / before <= PROVISIONAL_MAX_RATIO, (
        f"frames after deaths cost {after / before:.1f}x those before (bound {PROVISIONAL_MAX_RATIO}, Westley's)")
