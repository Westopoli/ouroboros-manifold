"""T1-N: the tactical frame's "mission_over"/"band" fields (docs/architecture.md
"C transport v1", tactical snapshot), and that a mission run by `tactical_step`
alone (no client `mission_end`) reaches `mission_over` within its own time
limit. Before this piece `handle_tactical_step` never checked
`om_mission_check_terminated`, so the client learned a mission had ended only
by pressing End Mission -- see the 2026-09-28 QA-run wiring brief.

Base times (docs/bible/algorithms.md ALG-56, csrc/mission.c
om_archetype_base_time_ticks) top out at 4.5 minutes * 60 * 20 ticks/s = 5400
ticks; R-076-01's floor never drops an archetype's own base below 0.6x itself,
so 5400 ticks of `tactical_step` is enough to cross any archetype's deadline
regardless of which one the candidate pool selects for this seed. This test
does not choose the archetype: whichever mission seed=1 draws, the time-limit
path (wired for every archetype, unlike the two objective kinds the wiring
brief leaves out -- see the report) must still end it.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SET_SEED = {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": FEATURES}
STEP10 = {"type": "cmd", "name": "step", "n": 10}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
STEP = {"type": "cmd", "name": "tactical_step", "n": 1}
QUIT = {"type": "cmd", "name": "quit"}

# Max base time (4.5 min) in ticks, plus margin for a floor-reduced deadline
# never landing exactly on a step boundary.
MAX_STEPS = 6000

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
    frames = _run([SET_SEED, STEP10, START, BEGIN] + [STEP] * MAX_STEPS, timeout=180)
    mission = [f for f in frames if f["type"] == "mission"][0]
    deadline = mission["deadline_ticks"]
    assert 0 < deadline <= MAX_STEPS, "deadline_ticks=%r outside this test's MAX_STEPS margin" % deadline

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
    end_frames = _run([SET_SEED, STEP10, START, BEGIN] + [STEP] * MAX_STEPS + [{"type": "cmd", "name": "mission_end"}], timeout=180)
    tail_types = [f["type"] for f in end_frames[-2:]]
    assert tail_types == ["debrief", "snapshot"], end_frames[-2:]
