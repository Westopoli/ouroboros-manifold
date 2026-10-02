"""T1-N: the tactical frame's "mission_over"/"band" fields (docs/architecture.md
"C transport v1", tactical snapshot), and that a mission run by `tactical_step`
alone (no client `mission_end`) reaches `mission_over` within its own time
limit. Before this piece `handle_tactical_step` never checked
`om_mission_check_terminated`, so the client learned a mission had ended only
by pressing End Mission -- see the 2026-09-28 QA-run wiring brief.

The step bound comes from the rule, not a constant: missions are 30 to 60
minutes of battle time (R-076-02 table, Q-076-02), so the test reads the
deadline_ticks the mission frame reports and steps DEADLINE_MARGIN past it.
Seed 3 is a fixture choice for cost, not a threshold: its first mission is an
evacuation (30-minute base, deadline about 30430 ticks) with a small force
(about 500 units), so the sim finishes in about a minute. It is one of only two
seeds in 1-400 that draw an evacuation on both the pre-A81 and post-A81 worlds
(the other, 154, has a longer deadline post-A81); _steps_for_deadline asserts
the draw, because a seed that falls through to a siege-breaking mission costs
50 ms per tick (TD-A89-2). Evacuation's escort
objective is one of the two kinds the wiring brief leaves out, so only the
time-limit path (wired for every archetype) can end it.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 3, "n_regions": 80, "features": FEATURES}
STEP10 = {"type": "cmd", "name": "step", "n": 10}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
STEP = {"type": "cmd", "name": "tactical_step", "n": 1}
QUIT = {"type": "cmd", "name": "quit"}

# The mission frame's deadline_ticks is the bound; the end check may land up to
# this many ticks after it (same slack the first_over tick assertion allows).
DEADLINE_MARGIN = 2

# Mission archetype id of Evacuation (docs/bible R-076-02 table).
EVACUATION = 7

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds, timeout=120):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=timeout)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


def _steps_for_deadline():
    """Steps needed to cross this seed's deadline, read from the mission frame."""
    frames = _run([SET_SEED, STEP10, START, BEGIN])
    mission = [f for f in frames if f["type"] == "mission"][0]
    assert mission["archetype"] == EVACUATION, (
        "seed 3 no longer draws an evacuation (archetype %r); re-pick the fixture seed"
        % mission["archetype"])
    deadline = mission["deadline_ticks"]
    assert deadline < 31000, "evacuation deadline_ticks=%r, expected the 30-minute base" % deadline
    assert deadline > 0, "deadline_ticks=%r" % deadline
    return deadline, deadline + DEADLINE_MARGIN


def test_fresh_tactical_frame_carries_mission_over_false_and_band_unknown():
    """Before a mission ends, "mission_over" is false and "band" is the
    OM_MISSION_BAND_UNKNOWN sentinel (-1), not merely absent from the frame."""
    frames = _run([SET_SEED, STEP10, START, BEGIN, STEP])
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert tactical, frames
    for t in tactical:
        assert t["mission_over"] is False, t
        assert t["band"] == -1, t


def test_tactical_step_alone_reaches_mission_over_within_its_time_limit():
    """R-075-07 / R-076-01: a mission run by tactical_step alone (never an
    explicit mission_end command) still reaches mission_over, at or before
    its own deadline_ticks, because om_tactical_step's own mission hook (not
    the client) now calls om_mission_check_terminated and ends it."""
    deadline, max_steps = _steps_for_deadline()
    # A tactical_step with n > 1 writes only its last frame and does not stop
    # early at mission end (its frame "tick" is the batch's last tick), so one
    # big batch covers the bulk and the final TAIL ticks go one frame each:
    # a mission ending in the tail has its first_over frame observed exactly.
    # A mission that ends earlier is already over in the batch's frame, whose
    # tick is <= deadline + 2, so the same bound assertion below still holds.
    tail = min(max_steps, 8)
    batch = {"type": "cmd", "name": "tactical_step", "n": max_steps - tail}
    end = {"type": "cmd", "name": "mission_end"}
    frames = _run([SET_SEED, STEP10, START, BEGIN, batch] + [STEP] * tail + [end], timeout=500)
    end_frames = frames[-2:]
    frames = frames[:-2]

    tacticals = [f for f in frames if f["type"] == "tactical"]
    over = [t for t in tacticals if t["mission_over"]]
    assert over, "tactical_step alone never reached mission_over in %d steps (deadline_ticks=%d)" % (len(tacticals), deadline)

    first_over = over[0]
    assert first_over["tick"] <= deadline + 2, (
        "mission_over appeared at tick %d, well past its own deadline_ticks %d" % (first_over["tick"], deadline))
    assert first_over["band"] != -1, "mission_over true but band still the UNKNOWN sentinel"

    # Once ended, every later frame stays ended with the same band (R-076-03:
    # the result is decided once, frozen after).
    idx = tacticals.index(first_over)
    for t in tacticals[idx:]:
        assert t["mission_over"] is True and t["band"] == first_over["band"], t

    # End Mission must still work unchanged after an auto-ended mission: the
    # explicit command still answers the normal debrief/snapshot pair, not
    # an error, exactly as it does for a mission the client ends itself.
    tail_types = [f["type"] for f in end_frames]
    assert tail_types == ["debrief", "snapshot"], end_frames
