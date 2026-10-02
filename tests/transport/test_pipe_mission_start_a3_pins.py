"""A3 pins (architect rulings 2026-10-01 round 2, Addendum 22, A50): two cases the A3 tests left
unpinned. R-072-07 / R-072-08.

(1) The player owns no region. mission_start answers an error frame and starts nothing. The
    pipe checks this BEFORE asking core for a fallback region: om_mission_fallback_region
    returns 0 when the player owns nothing, and region 0 is a real region, so a pipe that
    trusts that answer composes a mission on a region the player does not own (red today: the
    mission frame is answered, region 0, with enemy units on the field).
(2) No reachable enemy. Factions that cannot be reached by connection hops from the fallback
    region count as equally far, so R-072-08's tie rule picks among them: highest total
    military across all their regions (a tie being within OM_TIE_EPSILON), then the lowest
    faction id. The fallback is a quiet-world Defensive Stand against that faction. With no
    non-player, non-neutral faction at all, mission_start answers an error frame.
    (Red today: om_mission_fallback_enemy skips unreachable factions and returns -1, the pipe
    drops out of the fallback and answers "no viable mission".)

Fixtures. Worlds are constructed (80 regions, every region neutral and edgeless unless a row
says otherwise) through libouroboros.so's hard-fixture setters, written with om_save_state_write
and `load`ed into the pipe after a features-off set_seed (military is static through the retry
jumps with no features, so the fallback is reached). Region ids, military values and the owner
rows are fixtures, not thresholds. The enemy is read from the units of a full tactical frame
(A7: a delta frame has no `units`).

Controls: each error case has the same world with the one blocking fact removed (the player owns
a region; one enemy exists), which answers a mission; the unreachable cases have connected
variants where hops decide, and the tie cases have a reference that applies the wrong rule
(strongest region only, lowest id only) and names a different faction on the same fixture.
"""
import ctypes
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
LIB = ROOT / "libouroboros.so"

pytestmark = [
    pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)"),
    pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built"),
]

N_REGIONS = 80
PLAYER = 0
NEUTRAL = -1
HOME = 2  # OMTier.HOME
ARCH_PLAYER, ARCH_OTHER = 0, 1
EDGE_BOTH = 2
DEFENSIVE_STAND = 0
NEUTRAL_ROW = (NEUTRAL, 0.0, 0.0, 0.0, 0.0)  # owner, military, economy, tension, population


def _lib():
    lib = ctypes.CDLL(str(LIB))
    v = ctypes.c_void_p
    lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    lib.om_world_new.restype = v
    lib.om_world_free.argtypes = [v]
    lib.om_region_set.argtypes = [v, ctypes.c_uint32, ctypes.c_int] + [ctypes.c_double] * 6 + [ctypes.c_int32]
    lib.om_region_set.restype = ctypes.c_int
    lib.om_faction_set.argtypes = [v, ctypes.c_int32, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double]
    lib.om_faction_set.restype = ctypes.c_int
    lib.om_region_set_owner.argtypes = [v, ctypes.c_uint32, ctypes.c_int32, ctypes.c_int64]
    lib.om_region_set_edge.argtypes = [v, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int]
    lib.om_save_state_size.argtypes = [v]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [v, ctypes.c_char_p, ctypes.c_uint32]
    return lib


def _build_save(path, rows, edges):
    """rows: {region index: (owner, military, economy, tension, population)}, the rest neutral.
    edges: [(a, b)]. Faction 0 is the player (registered even if it owns nothing)."""
    lib = _lib()
    w = lib.om_world_new(N_REGIONS, 1)
    try:
        for f in sorted({r[0] for r in rows.values() if r[0] >= 0} | {PLAYER}):
            assert lib.om_faction_set(w, f, ARCH_PLAYER if f == PLAYER else ARCH_OTHER, 0.0, 0.0, -1.0) == 0
        for i in range(N_REGIONS):
            owner, mil, eco, ten, pop = rows.get(i, NEUTRAL_ROW)
            assert lib.om_region_set(w, i, HOME, mil, eco, ten, pop, 0.0, 0.0, owner) == 0
            lib.om_region_set_owner(w, i, owner, -1)
        for a, b in edges:
            lib.om_region_set_edge(w, a, b, EDGE_BOTH)
        n = lib.om_save_state_size(w)
        buf = ctypes.create_string_buffer(n)
        lib.om_save_state_write(w, buf, n)
        Path(path).write_bytes(bytes(buf))
    finally:
        lib.om_world_free(w)


def _frame(obj):
    body = json.dumps(obj).encode()
    return len(body).to_bytes(4, "big") + body


def _run(cmds):
    script = b"".join(_frame(c) for c in cmds + [{"type": "cmd", "name": "quit"}])
    proc = subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
    out, i, data = [], 0, proc.stdout
    while i + 4 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big")
        out.append(json.loads(data[i + 4:i + 4 + n]))
        i += 4 + n
    return out[1:]


def _mission_start(tmp_path, rows, edges):
    path = tmp_path / "pins.save"
    _build_save(path, rows, edges)
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": N_REGIONS, "features": [],
         "new_campaign": False},
        {"type": "cmd", "name": "load", "path": str(path)},
        {"type": "cmd", "name": "mission_start", "faction": PLAYER},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 1, "full": True},  # A7
    ])
    # the set_seed frames are not about this test; the load must have worked
    assert not [f for f in frames if f["type"] == "error" and f["name"] in ("set_seed", "load")], frames
    return frames


def _errors(frames, name):
    return [f for f in frames if f["type"] == "error" and f["name"] == name]


def _mission(frames):
    return next((f for f in frames if f["type"] == "mission"), None)


def _enemies(frames):
    tactical = [f for f in frames if f["type"] == "tactical"]
    assert tactical, "no tactical frame: %r" % frames
    units = tactical[-1]["units"]
    assert any(u["faction"] == PLAYER for u in units), "fixture drift: no player units"
    return {u["faction"] for u in units if u["faction"] not in (PLAYER, NEUTRAL)}


# ---- (1) the player owns no region ----

def _no_player_rows(region0_owner):
    """Player owns nothing. Region 0 belongs to region0_owner; factions 1 and 2 hold regions near it."""
    rows = {1: (1, 40.0, 20.0, 20.0, 50.0), 2: (2, 60.0, 20.0, 20.0, 50.0)}
    if region0_owner != NEUTRAL:
        rows[0] = (region0_owner, 50.0, 20.0, 20.0, 50.0)
    return rows


NO_PLAYER_EDGES = [(0, 30), (30, 1), (1, 2)]  # region 30 is neutral; no hostile neighbour of region 0


@pytest.mark.parametrize("region0_owner", [1, NEUTRAL])
def test_player_owning_no_region_answers_an_error_and_starts_nothing(tmp_path, region0_owner):
    """A50 (1): an error frame for mission_start, no mission frame, nothing started: mission_begin
    is refused ("not in recon") and the first tactical frame has no units. Region 0 is a real
    region (owned by another faction, or neutral), so the pipe must not take core's fallback 0.
    Red today: the pipe answers a Defensive Stand on region 0."""
    frames = _mission_start(tmp_path, _no_player_rows(region0_owner), NO_PLAYER_EDGES)
    assert _errors(frames, "mission_start"), "no error frame for a player who owns no region: %r" % frames
    assert _mission(frames) is None, "a mission was composed for a player who owns no region: %r" % _mission(frames)
    assert _errors(frames, "mission_begin"), "mission_begin must refuse: nothing was started"
    assert not [f for f in frames if f["type"] == "tactical" and f.get("units")], (
        "units fielded although mission_start errored")


def test_control_player_owning_a_region_answers_a_mission(tmp_path):
    """Positive control: the same world with region 0 given to the player answers a quiet-world
    Defensive Stand on it and no error, so the fixture can start a mission and the error above is
    caused by the missing region alone."""
    rows = _no_player_rows(NEUTRAL)
    rows[0] = (PLAYER, 50.0, 20.0, 20.0, 50.0)
    frames = _mission_start(tmp_path, rows, NO_PLAYER_EDGES)
    assert not _errors(frames, "mission_start"), frames
    mission = _mission(frames)
    assert mission is not None and mission["region"] == 0, mission
    assert (mission["archetype"], mission.get("quiet_world")) == (DEFENSIVE_STAND, True), mission
    assert _enemies(frames) == {1}  # nearest by hops: faction 1 is 2 hops from region 0, faction 2 is 3


# ---- (2) no reachable enemy ----
# Player: regions 0, 1 (joined to each other, nothing else). Everyone else is out of reach.

PLAYER_ROWS = {0: (PLAYER, 30.0, 30.0, 30.0, 50.0), 1: (PLAYER, 40.0, 30.0, 30.0, 50.0)}


def _unreachable_rows(extra):
    rows = dict(PLAYER_ROWS)
    rows.update(extra)
    return rows


# Faction 1: one region, 40. Faction 2: one region, 60 (the strongest single region). Faction 3:
# two regions of 35, total 70 (the highest total). Region order is chosen so the strongest-region
# and lowest-id rules each name a different faction than the total rule.
TOTALS = {10: (1, 40.0, 20.0, 20.0, 50.0), 11: (2, 60.0, 20.0, 20.0, 50.0),
          12: (3, 35.0, 20.0, 20.0, 50.0), 13: (3, 35.0, 20.0, 20.0, 50.0)}


def _reference(rows, wrong=None):
    """The A50 rule over unreachable factions; `wrong` names the positive-control variant."""
    totals, strongest = {}, {}
    for owner, mil, *_ in (r for r in rows.values() if r[0] not in (PLAYER, NEUTRAL)):
        totals[owner] = totals.get(owner, 0.0) + mil
        strongest[owner] = max(strongest.get(owner, 0.0), mil)
    if wrong == "strongest_region":
        return min(strongest, key=lambda f: (-strongest[f], f))
    if wrong == "lowest_id":
        return min(totals)
    return min(totals, key=lambda f: (-totals[f], f))


def test_unreachable_factions_tie_and_the_highest_total_military_is_the_enemy(tmp_path):
    """A50 (2): no enemy reachable by hops, so all tie on distance; faction 3 (total 70 over two
    regions) beats faction 2 (60, the strongest single region) and faction 1 (40). Red today: core
    skips unreachable factions, answers -1, and the pipe answers "no viable mission"."""
    rows = _unreachable_rows(TOTALS)
    frames = _mission_start(tmp_path, rows, [(0, 1)])
    assert not _errors(frames, "mission_start"), frames
    mission = _mission(frames)
    assert mission is not None and mission.get("quiet_world") is True, mission
    assert mission["archetype"] == DEFENSIVE_STAND
    assert _enemies(frames) == {_reference(rows)} == {3}


def test_control_the_wrong_rules_name_other_factions_on_the_same_world():
    """Positive control for the test above: strongest-region-only names faction 2 and
    lowest-id-only names faction 1 on this very fixture, so it cannot pass under either."""
    rows = _unreachable_rows(TOTALS)
    assert _reference(rows, "strongest_region") == 2
    assert _reference(rows, "lowest_id") == 1
    assert _reference(rows) == 3


def test_unreachable_factions_with_equal_totals_go_to_the_lowest_faction_id(tmp_path):
    """A50 (2): factions 1 and 2 are both out of reach with exactly equal totals; faction 2 holds
    the lower region index, the lowest faction id (1) still wins; faction 3 is weaker."""
    rows = _unreachable_rows({10: (2, 50.0, 20.0, 20.0, 50.0), 11: (1, 50.0, 20.0, 20.0, 50.0),
                              12: (3, 20.0, 20.0, 20.0, 50.0)})
    frames = _mission_start(tmp_path, rows, [(0, 1)])
    assert not _errors(frames, "mission_start"), frames
    assert _mission(frames).get("quiet_world") is True
    assert _enemies(frames) == {1}


def test_control_a_reachable_weaker_faction_beats_unreachable_stronger_ones(tmp_path):
    """Positive control: the world of the first test with faction 1 (the weakest) joined to
    region 1. Hops still decide: faction 1 is the enemy. Passes today; it proves the fixture
    reaches the quiet-world fallback and that unreachable only ties among the unreachable."""
    rows = _unreachable_rows(TOTALS)
    frames = _mission_start(tmp_path, rows, [(0, 1), (1, 30), (30, 31), (31, 10)])  # 30, 31 neutral
    assert not _errors(frames, "mission_start"), frames
    assert _mission(frames).get("quiet_world") is True
    assert _enemies(frames) == {1}


def test_no_non_player_faction_at_all_answers_an_error(tmp_path):
    """A50 (2): only the player's regions and neutral regions exist: nobody to fight, so an error
    frame, no mission, nothing started."""
    rows = _unreachable_rows({10: NEUTRAL_ROW, 11: (NEUTRAL, 50.0, 20.0, 20.0, 50.0)})
    frames = _mission_start(tmp_path, rows, [(0, 1), (1, 11)])
    assert _errors(frames, "mission_start"), "no error frame with no enemy faction: %r" % frames
    assert _mission(frames) is None
    assert _errors(frames, "mission_begin")


def test_control_one_enemy_faction_anywhere_answers_a_mission(tmp_path):
    """Positive control: the same world plus one enemy region, two hops past a neutral one,
    answers a mission."""
    rows = _unreachable_rows({11: (NEUTRAL, 50.0, 20.0, 20.0, 50.0), 20: (1, 10.0, 20.0, 20.0, 50.0)})
    frames = _mission_start(tmp_path, rows, [(0, 1), (1, 11), (11, 12), (12, 20)])
    assert not _errors(frames, "mission_start"), frames
    assert _enemies(frames) == {1}
