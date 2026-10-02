"""A3 tie-break (architect rulings 2026-10-01 round 2 section 7.3; R-072-08): the quiet-world
fallback enemy is the non-player faction nearest the fallback region by hops, ties to the
highest total military, then the lowest faction id. "Tie" means within OM_TIE_EPSILON like
the rest of the sim ("Ties break by OM_TIE_EPSILON", leaf-mechanics.md), so two candidate
factions whose totals differ by less than OM_TIE_EPSILON but are not bit-equal tie on
military and the lowest faction id wins. The pipe's quiet_world_enemy (csrc/pipe/om_pipe.c)
compares with a plain `>` and picks the (sub-epsilon) larger.

Fixture. No generated world has two factions that are nearly, but not exactly, equal, so the
world is built: seed 46, 80 regions, launch features off (military is static through the
retry jumps with no features, measured), fallback reached with no trigger. Factions 1 and 9
are both 5 hops from the fallback region. In the generated world faction 9 leads faction 1 by
2.98 total military. The fixture lowers one of faction 1's regions (region 10) to a pinned
value that brings faction 1 to within 2e-13 below faction 9, by patching the one 8-byte
military double of region 10 in the bytes of `om_save_state_write`, and the pipe `load`s it.
Region, value and seed are fixtures, not thresholds.

OM_TIE_EPSILON is 1e-12 (csrc/om_internal.h, not visible to the pipe: contract gap).

Controls: with the same patch moved by 1e-3 either way the gap is outside epsilon and the
larger total wins (faction 9 when it leads, faction 1 when it leads); they prove the
sub-epsilon case is the only thing that flips the pick. They share the helper with the tie
test, so all three read the enemy from a full tactical frame (`"full": true`, A7).
"""
import ctypes
import json
import struct
import subprocess
from collections import deque
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PIPE = ROOT / "pipe/ouroboros_pipe"
LIB = ROOT / "libouroboros.so"

pytestmark = [
    pytest.mark.skipif(not PIPE.exists(), reason="pipe/ouroboros_pipe not built (piece T1)"),
    pytest.mark.skipif(not LIB.exists(), reason="libouroboros.so not built"),
]

SEED = 46
N_REGIONS = 80
PATCH_REGION = 10
LOW, HIGH = 1, 9  # the two candidate factions: lowest id, and the sub-epsilon leader
LOW_MIL_FIXTURE = 18.62883240868037  # region 10 military: puts faction 1 about 2e-13 below faction 9
OM_TIE_EPSILON = 1e-12  # csrc/om_internal.h
M_MILITARY = 0


def _lib():
    lib = ctypes.CDLL(str(LIB))
    lib.om_world_new.argtypes = [ctypes.c_uint32, ctypes.c_uint64]
    lib.om_world_new.restype = ctypes.c_void_p
    lib.om_world_generate.argtypes = [ctypes.c_void_p]
    lib.om_world_free.argtypes = [ctypes.c_void_p]
    lib.om_save_state_size.argtypes = [ctypes.c_void_p]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    lib.om_load_state_read.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib.om_region_field.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
    lib.om_region_field.restype = ctypes.c_double
    lib.om_region_owner.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.om_region_owner.restype = ctypes.c_int32
    return lib


def _generated_save(lib):
    w = lib.om_world_new(N_REGIONS, SEED)
    try:
        lib.om_world_generate(w)
        n = lib.om_save_state_size(w)
        buf = ctypes.create_string_buffer(n)
        lib.om_save_state_write(w, buf, n)
        original = lib.om_region_field(w, PATCH_REGION, M_MILITARY)
        assert lib.om_region_owner(w, PATCH_REGION) == LOW, "fixture drift: region %d is not faction %d's" % (
            PATCH_REGION, LOW)
        return bytes(buf), original
    finally:
        lib.om_world_free(w)


def _patched_save(lib, military):
    data, original = _generated_save(lib)
    old = struct.pack("<d", original)
    assert data.count(old) == 1, "fixture drift: region military double not unique in the save (%d)" % data.count(old)
    return data.replace(old, struct.pack("<d", military))


def _exact_totals(lib, data):
    w = lib.om_world_new(N_REGIONS, SEED)
    try:
        assert lib.om_load_state_read(w, data, len(data)) == 0
        totals = {}
        for i in range(N_REGIONS):
            f = lib.om_region_owner(w, i)
            if f >= 0:
                totals[f] = totals.get(f, 0.0) + lib.om_region_field(w, i, M_MILITARY)
        return totals
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


def _hops_from(snap, region):
    adj = {}
    for e in snap["edges"]:
        adj.setdefault(e["a"], []).append(e["b"])
        adj.setdefault(e["b"], []).append(e["a"])
    dist, queue = {region: 0}, deque([region])
    while queue:
        x = queue.popleft()
        for y in adj.get(x, []):
            if y not in dist:
                dist[y] = dist[x] + 1
                queue.append(y)
    return dist


def _fallback_enemy(tmp_path, data):
    """Load `data` into the pipe, run mission_start into the quiet-world fallback and
    return (enemy factions on the field, nearest hops of LOW, nearest hops of HIGH, the
    rounded snapshot totals of both)."""
    path = tmp_path / "tie.save"
    path.write_bytes(data)
    frames = _run([
        {"type": "cmd", "name": "set_seed", "seed": SEED, "n_regions": N_REGIONS, "features": [],
         "new_campaign": False},
        {"type": "cmd", "name": "load", "path": str(path)},
        {"type": "cmd", "name": "mission_start", "faction": 0},
        {"type": "cmd", "name": "snapshot"},
        {"type": "cmd", "name": "mission_begin"},
        {"type": "cmd", "name": "tactical_step", "n": 1, "full": True},  # A7: a delta frame has no `units`
    ])
    errors = [f for f in frames if f["type"] == "error"]
    assert not errors, errors
    mission = next(f for f in frames if f["type"] == "mission")
    assert mission.get("quiet_world") is True, "fixture drift: fallback not reached: %r" % mission
    snap = [f for f in frames if f["type"] == "snapshot"][-1]
    tactical = [f for f in frames if f["type"] == "tactical"][-1]
    player = snap["player_faction"]
    dist = _hops_from(snap, mission["region"])
    hops = {LOW: 10 ** 9, HIGH: 10 ** 9}
    total = {LOW: 0.0, HIGH: 0.0}
    for r in snap["regions"]:
        if r["owner"] in hops and r["i"] in dist:
            hops[r["owner"]] = min(hops[r["owner"]], dist[r["i"]])
            total[r["owner"]] += r["military"]
    enemies = {u["faction"] for u in tactical["units"] if u["faction"] not in (player, -1)}
    return enemies, hops, total


def test_fixture_is_a_sub_epsilon_unequal_tie(tmp_path):
    lib = _lib()
    totals = _exact_totals(lib, _patched_save(lib, LOW_MIL_FIXTURE))
    gap = totals[HIGH] - totals[LOW]
    assert 0.0 < gap <= OM_TIE_EPSILON, "fixture drift: military gap %.3e is not in (0, OM_TIE_EPSILON]" % gap
    assert totals[HIGH] != totals[LOW]


def test_totals_within_tie_epsilon_pick_the_lowest_faction_id(tmp_path):
    """R-072-08 with OM_TIE_EPSILON: factions 1 and 9 tie on hops and on military (gap about
    2e-13, not bit-equal), so the lowest id, faction 1, is the enemy. Red today: the plain `>`
    picks faction 9."""
    lib = _lib()
    enemies, hops, total = _fallback_enemy(tmp_path, _patched_save(lib, LOW_MIL_FIXTURE))
    assert hops[LOW] == hops[HIGH], "fixture drift: factions %d and %d no longer tie on hops: %r" % (LOW, HIGH, hops)
    assert abs(total[HIGH] - total[LOW]) <= 0.01
    assert enemies == {LOW}, (
        "enemy faction(s) %r on the field; totals within OM_TIE_EPSILON must tie and pick the lowest faction id %d (R-072-08)"
        % (sorted(enemies), LOW))


def test_control_a_gap_outside_epsilon_picks_the_larger_total_high_leads(tmp_path):
    """Positive control: lower faction 1 by a further 1e-3 (outside epsilon); the larger total,
    faction 9, wins, so the sub-epsilon case above is the only thing that flips the pick."""
    lib = _lib()
    enemies, hops, _ = _fallback_enemy(tmp_path, _patched_save(lib, LOW_MIL_FIXTURE - 1e-3))
    assert hops[LOW] == hops[HIGH]
    assert enemies == {HIGH}, sorted(enemies)


def test_control_a_gap_outside_epsilon_picks_the_larger_total_low_leads(tmp_path):
    """Positive control: raise faction 1 by 1e-3 so it leads outright; it wins as the highest total."""
    lib = _lib()
    enemies, hops, _ = _fallback_enemy(tmp_path, _patched_save(lib, LOW_MIL_FIXTURE + 1e-3))
    assert hops[LOW] == hops[HIGH]
    assert enemies == {LOW}, sorted(enemies)
