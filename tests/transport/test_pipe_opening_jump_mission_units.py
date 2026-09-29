"""T1-17: a new campaign's first mission always has units (R-056-04, R-080-03).

Diagnosis (M0's brief, verified by reproduction): a new campaign's first
mission was started from a world at tick 0 -- the galaxy never steps the
world, and c_bridge.gd's begin_mission_live sends mission_start straight
away. On a tick-0 world om_mission_build_candidate_pool (csrc/mission.c)
finds no candidates (the trigger-scored pool needs elapsed ticks), so
om_mission_select returns "no candidate" and handle_mission_start
(csrc/pipe/om_pipe.c) silently fell back to region=0/archetype=0 -- a
mission with zero units. Some seeds still had zero units at tick 10 because
region 0 is not necessarily owned by, or adjacent to, the player.

The fix, entirely in csrc/pipe/om_pipe.c (T1's file; no csrc/generational.c
or csrc/mission.c changes needed -- both already had the functions this
calls, just no production caller):

  - handle_set_seed now calls om_campaign_start (csrc/generational.c), which
    runs the R-056-04 opening jump ([20, 50] ticks) before a NEW campaign's
    first mission_start can run. A `new_campaign: false` field on `set_seed`
    skips it -- autoload/c_bridge.gd's load() (continuing a save) sends
    that, since the following `load` command fully overwrites the tick/
    regions/chapter this world was given anyway (see docs/architecture.md
    "session commands"). Absent (the default, matching every raw
    `set_seed` this file and every other transport test send), it runs.
  - handle_set_seed also calls om_mission_load_launch_library
    (csrc/mission.c) once: om_mission_select_candidate and
    om_mission_archetype_count (both used by the fallback below) read
    st->library_loaded, which nothing in production ever set, so they
    silently behaved as "0 archetypes" -- a dependency the R-080-03 fallback
    cannot work without (a pure in-memory table fill, no side effects
    outside om_mission_state).
  - handle_mission_start uses om_mission_select_candidate plus the player's
    own first owned region instead of the silent region=0/archetype=0
    default when the trigger-scored pool is empty, and -- found during this
    fix's own verification, not in the original diagnosis -- verifies the
    chosen candidate (from either path) actually composed nonzero force on
    both sides before sending it. Three archetypes (DEFENSIVE_STAND,
    MULTI_FRONT_DEFENSE, INTERCEPTION) compute enemy power from a
    committed-attack-budget field (om_mission_set_conflict_context) that no
    production code populates -- a separate, pre-existing gap, not fixed
    here -- so any candidate that lands on one of those, from either path,
    always composed zero force. A composed-but-empty candidate now falls
    through to scanning every archetype against every player-owned region
    for one that actually produces units, and only then, if truly nothing
    does, answers `{"type":"error","name":"mission_start","reason":"no
    viable mission"}` instead of ever sending a zero-unit mission.

Positive control: every assertion below is red on unmodified origin/main
(tick stays 0, both unit counts are 0) for every seed in SEEDS; both go
green once handle_set_seed/handle_mission_start are fixed.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
FEATURES = [0, 1, 2, 3, 4, 5, 6, 7]
N_REGIONS = 80

# "seeds 1 and 2": [1, 2]. "the three seeds above" (M0's brief diagnosis --
# still zero units at tick 10 even before this fix, because region 0 is not
# reliably owned by the player): [2, 866843821, 1632119446] -- seed 2 is
# named in both groups; kept as a literal duplicate row rather than silently
# dropped, to match "10 seeds" as written. "5 values from derive_seed for
# arbitrary run ids": derive_seed("qa-run-1".."qa-run-5") from
# ~/Projects/agora/scripts/qa_run_seed.py.
SEEDS = [1, 2] + [2, 866843821, 1632119446] + [734681143, 1696945313, 532762897, 1032339966, 366862596]
assert len(SEEDS) == 10


def _frame(obj: dict) -> bytes:
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds)
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i = [], 0
    data = proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out


pytestmark = pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)")


@pytest.mark.parametrize("seed", SEEDS)
def test_new_campaign_first_mission_has_units_on_both_sides(seed):
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": N_REGIONS, "features": FEATURES},
        {"type": "cmd", "name": "snapshot"},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 1},
    ])
    snap = next(f for f in frames if f["type"] == "snapshot")
    assert snap["tick"] >= 20, "seed %d: world tick after set_seed = %d, expected >= 20 (R-056-04)" % (seed, snap["tick"])

    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, "seed %d: mission_start/mission_begin refused: %r" % (seed, errors)

    tactical = next((f for f in frames if f["type"] == "tactical"), None)
    assert tactical is not None, "seed %d: no tactical frame; frames = %r" % (seed, frames)
    units = tactical.get("units", [])
    player_units = [u for u in units if u.get("faction") == 0]
    enemy_units = [u for u in units if u.get("faction") not in (0, None)]
    assert len(player_units) > 0, "seed %d: 0 player units in the first tactical frame" % seed
    assert len(enemy_units) > 0, "seed %d: 0 enemy units in the first tactical frame" % seed


def test_set_seed_new_campaign_false_does_not_run_the_opening_jump():
    """autoload/c_bridge.gd's load() sends new_campaign:false to prep a world
    for a following `load` command; the opening jump must not run (the load
    that follows overwrites tick/regions/chapter anyway -- running the jump
    first would only waste time)."""
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": 2, "n_regions": N_REGIONS,
         "features": FEATURES, "new_campaign": False},
        {"type": "cmd", "name": "snapshot"},
    ])
    snap = next(f for f in frames if f["type"] == "snapshot")
    assert snap["tick"] == 0, "new_campaign:false still advanced the tick to %d" % snap["tick"]


@pytest.mark.parametrize("seed", SEEDS)
def test_mission_start_never_silently_composes_a_zero_unit_mission_at_tick_zero(seed):
    """Core test for the original bug: at tick 0 (new_campaign:false forces
    the trigger-scored candidate pool to be empty, csrc/mission.c
    om_mission_build_candidate_pool), handle_mission_start (csrc/pipe/om_pipe.c)
    must never silently answer a `mission` frame for a hardcoded
    region=0/archetype=0 with no units. It must either produce a mission
    with real units on both sides, or refuse with
    {"type":"error","name":"mission_start","reason":"no viable mission"} --
    never a `mission` frame with 0 units.

    Positive control: red on unmodified origin/main, where every one of
    these seeds answers a `mission` frame (never `error`) for archetype 0 at
    region 0 with 0 units in the following tactical frame.
    """
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": N_REGIONS,
         "features": FEATURES, "new_campaign": False},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 1},
    ])
    mission = next((f for f in frames if f["type"] == "mission"), None)
    error = next((f for f in frames if f["type"] == "error" and f.get("name") == "mission_start"), None)
    assert mission is not None or error is not None, "seed %d: neither a mission nor an error frame: %r" % (seed, frames)
    if error is not None:
        assert error.get("reason") == "no viable mission", "seed %d: unexpected refusal reason: %r" % (seed, error)
        return
    tactical = next((f for f in frames if f["type"] == "tactical"), None)
    assert tactical is not None, "seed %d: mission frame with no following tactical frame: %r" % (seed, frames)
    units = tactical.get("units", [])
    player_units = [u for u in units if u.get("faction") == 0]
    enemy_units = [u for u in units if u.get("faction") not in (0, None)]
    assert len(player_units) > 0 and len(enemy_units) > 0, (
        "seed %d: mission_start silently composed a zero-unit mission (archetype %r): %r"
        % (seed, mission.get("archetype"), tactical))
