"""B9-N: mission_started latch never resets, so every mission after the
first is refused "not in recon" (QA-004/005 blocker on the 30B QA harness).

csrc/fog.c's om_mission_begin sets a one-shot mission_started latch and
nothing ever cleared it. The pipe's in_recon() (csrc/pipe/om_pipe.c) requires
`!om_mission_is_started(W)`, so the second mission_begin in a session -- and
every one after it -- is refused even though csrc/mission.c's om_mission_setup
already resets the per-mission phase back to recon. The fix resets the latch
in om_mission_setup alongside the phase.

Positive control: test_three_cycles_of_mission_begin_all_succeed is red on
unmodified origin/main at the second cycle's mission_begin (refused "not in
recon"); it is green once om_mission_setup resets the latch.

The pipe's JSON frames never carry the mission clock (grepped
csrc/pipe/om_pipe.c: no "clock" key in any write_* function), so the clock
half of the fix (om_mission_get_clock reads the same stale latch) is checked
directly against the library via ctypes, replicating the pipe's own
handle_mission_start composition (csrc/pipe/om_pipe.c: build_candidate_pool
-> select -> candidates -> setup -> build_objectives) for three cycles on one
world.
"""
import ctypes
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
LIB = ROOT / "libouroboros.so"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
SEED = 1
N_REGIONS = 80

SET_SEED = {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": N_REGIONS, "features": FEATURES}
START = {"type": "cmd", "name": "mission_start", "faction": 0}
BEGIN = {"type": "cmd", "name": "mission_begin"}
END = {"type": "cmd", "name": "mission_end"}
JUMP_50 = {"type": "cmd", "name": "jump", "ticks": 50}
QUIT = {"type": "cmd", "name": "quit"}

pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [QUIT])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]  # drop hello


def test_three_cycles_of_mission_begin_all_succeed():
    """Three full mission_start/mission_begin/mission_end/jump(50) cycles on one
    pipe session; every mission_begin must answer a tactical frame, never
    "not in recon"."""
    cycle = [SET_SEED] + [START, BEGIN, END, JUMP_50] * 3
    frames = _run(cycle)

    begin_results = []
    i = 0
    for f in frames:
        if f["type"] == "mission":
            # the frame right after "mission" (mission_start's answer) is
            # mission_begin's answer.
            pass
    # Walk the frame stream in cycles of (mission, tactical|error, debrief,
    # snapshot, chronicle, snapshot) to isolate each mission_begin's answer.
    idx = 0
    for cycle_no in range(3):
        assert frames[idx]["type"] == "mission", (cycle_no, frames)
        idx += 1
        begin_frame = frames[idx]
        begin_results.append(begin_frame)
        idx += 1
        assert begin_frame["type"] == "tactical", (
            "cycle %d: mission_begin was refused: %r" % (cycle_no, begin_frame)
        )
        # mission_end -> debrief, snapshot; jump -> chronicle, snapshot.
        assert frames[idx]["type"] == "debrief", (cycle_no, frames)
        idx += 1
        assert frames[idx]["type"] == "snapshot", (cycle_no, frames)
        idx += 1
        assert frames[idx]["type"] == "chronicle", (cycle_no, frames)
        idx += 1
        assert frames[idx]["type"] == "snapshot", (cycle_no, frames)
        idx += 1

    assert len(begin_results) == 3
    assert all(f["type"] == "tactical" for f in begin_results), begin_results


@pytest.fixture(scope="module")
def cycle_lib():
    sys.path.insert(0, str(ROOT / "tests/csim"))
    import conftest as csim
    return csim.load_lib()


def _replicate_mission_start(lib, w, faction):
    """Replicates csrc/pipe/om_pipe.c handle_mission_start: build_candidate_pool
    -> select -> candidates -> setup -> build_objectives."""
    lib.om_mission_start(w, ctypes.c_int32(faction))
    lib.om_mission_build_candidate_pool(w)
    idx = lib.om_mission_select(w)
    import conftest as csim
    pool = (csim.OMMissionCandidate * 256)()
    n = lib.om_mission_candidates(w, ctypes.cast(pool, ctypes.c_void_p), ctypes.c_uint32(256))
    region, archetype = 0, 0
    if idx < n:
        region = pool[idx].region_idx
        archetype = pool[idx].archetype
    lib.om_mission_setup(w, ctypes.c_uint32(region), ctypes.c_uint32(archetype), ctypes.c_int(0))
    lib.om_mission_build_objectives(w, ctypes.c_uint32(archetype))


def test_mission_clock_reads_zero_after_each_mission_start_before_begin(cycle_lib):
    """The mission clock (om_mission_get_clock) must read 0 right after each of
    three mission_start-equivalent setups, before mission_begin -- it reads the
    same mission_started latch om_mission_is_started does, so a latch that never
    resets after the first mission would leave this stale too."""
    lib = cycle_lib
    w = lib.om_world_new(ctypes.c_uint32(N_REGIONS), ctypes.c_uint64(SEED))
    assert w, "om_world_new returned NULL"
    for f in FEATURES:
        lib.om_world_set_feature(w, f, 1)
    lib.om_world_generate(w)

    for cycle_no in range(3):
        _replicate_mission_start(lib, w, 0)

        assert lib.om_mission_is_started(w) == 0, (
            "cycle %d: mission_started still latched before mission_begin" % cycle_no
        )
        assert lib.om_mission_get_clock(w) == 0, (
            "cycle %d: mission clock is not 0 before mission_begin" % cycle_no
        )

        lib.om_mission_begin(w)
        assert lib.om_mission_is_started(w) == 1
        lib.om_mission_end(w)

    lib.om_world_free(w)
