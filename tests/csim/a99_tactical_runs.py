"""Run definitions and per-step state hash for the A99 tactical equivalence guard.

Shared by tests/csim/test_E13_A99_tactical_equivalence.py (compare) and the generator
(record). Regenerate the data file ONLY from a build whose tactical behaviour is the
reference one (origin/main before any A99 perf change):

    make libouroboros.so && python tests/csim/a99_tactical_runs.py --generate \
        [--only NAME ...]      # writes tests/csim/data/a99_tactical_hashes.json

Scenario (docs/northstar/proving_ground/evidence/a91_tactical_tick_harness.c, A93 report):
seed 121, 80 regions, features 0..7, 10 world steps, mission context refresh, region 0
military set to the size's value, om_mission_setup(0,1,0) + om_mission_begin. Fight runs
then teleport the player block (om_unit_set_pos) so its centroid sits at the enemy
centroid plus a gap along the enemy->player direction (gap + both blocks' radii, so "gap"
is the clear distance between block edges), and give every player unit
om_command_attack_move at the enemy centroid. Per step: om_tactical_step, then one
sha256 over every in-use unit (re-enumerated each step, so spawns count) (id, alive, x, y, target, hp) and om_world_checksum.
"""
import ctypes
import hashlib
import json
import math
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
DATA = HERE / "data" / "a99_tactical_hashes.json"

# military value -> units: 8.6/17/42.8/85 for 502/990/2501/4996 (A93 report)
MIL = {502: 8.6, 990: 17.0, 2501: 42.8, 4996: 85.0}
# name, units, gap (None = idle opening), steps, tier ("fast" always, "scale" OM_SCALE=1)
RUNS = [
    ("idle_502", 502, None, 1500, "fast"),
    ("idle_990", 990, None, 1500, "fast"),
    ("idle_2501", 2501, None, 600, "scale"),
    ("idle_4996", 4996, None, 400, "scale"),
    ("fight_502_gap100", 502, 100, 1200, "fast"),
    ("fight_990_gap300", 990, 300, 1500, "fast"),
    ("fight_990_gap1500", 990, 1500, 1500, "fast"),
    ("fight_990_gap3000", 990, 3000, 1200, "fast"),
    ("fight_2501_gap600", 2501, 600, 600, "scale"),
    ("fight_2501_gap2000", 2501, 2000, 600, "scale"),
    ("fight_4996_gap900", 4996, 900, 500, "scale"),
]
# 11 runs = 4 idle + 7 fight, the report's "11 cases" (the brief's "fifteen" double-counts).


def _load():
    from conftest import (_bind_generated, _configure_common, LIB_PATH)
    h = ctypes.CDLL(str(LIB_PATH))
    _configure_common(h)
    _bind_generated(h)
    return h


def build(lib, units):
    w = lib.om_world_new(80, 121)
    for i in range(8):
        lib.om_world_set_feature(w, i, 1)
    lib.om_world_generate(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    lib.om_campaign_start(w, 1)
    for _ in range(10):
        lib.om_world_step(w)
    for r in range(lib.om_region_count(w)):
        lib.om_mission_refresh_context(w, r)
    mil = MIL[units]
    lib.om_region_set(w, 0, lib.om_region_tier(w, 0), mil, lib.om_region_field(w, 0, 1),
                      lib.om_region_field(w, 0, 3), lib.om_region_field(w, 0, 2), 0.0, 0.0,
                      lib.om_region_owner(w, 0))
    lib.om_mission_setup(w, 0, 1, 0)
    lib.om_mission_begin(w)
    return w


def _slots(lib, w):
    total = lib.om_unit_count(w)
    out, seen, i = [], 0, 0
    while seen < total:
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if uid:
            seen += 1
            out.append(uid)
    return out


def state_hash(lib, w):
    buf = bytearray()
    for u in _slots(lib, w):
        x, y = lib.om_unit_get_pos(w, u)
        buf += struct.pack("<IIddId", u, lib.om_unit_alive(w, u), x, y,
                           lib.om_unit_get_target(w, u), lib.om_unit_get_hp(w, u))
    buf += struct.pack("<Q", lib.om_world_checksum(w))
    return hashlib.sha256(bytes(buf)).hexdigest()[:16]


def stage_fight(lib, w, ids, gap):
    pf = lib.om_player_faction(w)
    pl = [u for u in ids if lib.om_unit_alive(w, u) and lib.om_unit_get_faction(w, u) == pf]
    en = [u for u in ids if lib.om_unit_alive(w, u) and lib.om_unit_get_faction(w, u) != pf]
    pos = {u: lib.om_unit_get_pos(w, u) for u in pl + en}

    def cen(g):
        return (sum(pos[u][0] for u in g) / len(g), sum(pos[u][1] for u in g) / len(g))

    def rad(g, c):
        return max(math.hypot(pos[u][0] - c[0], pos[u][1] - c[1]) for u in g)
    ce, cp = cen(en), cen(pl)
    d = math.hypot(cp[0] - ce[0], cp[1] - ce[1])
    ux, uy = (cp[0] - ce[0]) / d, (cp[1] - ce[1]) / d
    dist = gap + rad(en, ce) + rad(pl, cp)
    tx, ty = ce[0] + ux * dist, ce[1] + uy * dist
    for u in pl:
        lib.om_unit_set_pos(w, u, pos[u][0] + (tx - cp[0]), pos[u][1] + (ty - cp[1]))
    arr = (ctypes.c_uint32 * len(pl))(*pl)
    lib.om_command_attack_move(w, arr, len(pl), ce[0], ce[1])


def record_run(lib, name, units, gap, steps):
    w = build(lib, units)
    ids = _slots(lib, w)
    if gap is not None:
        stage_fight(lib, w, ids, gap)
    hashes = []
    for _ in range(steps):
        lib.om_tactical_step(w)
        hashes.append(state_hash(lib, w))
    live = sum(1 for u in _slots(lib, w) if lib.om_unit_alive(w, u))
    n_in_use = lib.om_unit_count(w)
    lib.om_world_free(w)
    return {"units": units, "gap": gap, "steps": steps, "in_use": n_in_use,
            "live_after": live, "hashes": hashes}


def load_recorded():
    return json.loads(DATA.read_text())


def run_hashes(lib, units, gap, steps, extra_ticks=0):
    """Per-step hashes of a rebuilt run; extra_ticks inserts that many unhashed
    om_tactical_step calls before the first hashed step (positive control)."""
    w = build(lib, units)
    if gap is not None:
        stage_fight(lib, w, _slots(lib, w), gap)
    for _ in range(extra_ticks):
        lib.om_tactical_step(w)
    out = []
    for _ in range(steps):
        lib.om_tactical_step(w)
        out.append(state_hash(lib, w))
    lib.om_world_free(w)
    return out


def side_counts(lib, units):
    w = build(lib, units)
    ids = _slots(lib, w)
    pf = lib.om_player_faction(w)
    p = sum(1 for u in ids if lib.om_unit_get_faction(w, u) == pf)
    lib.om_world_free(w)
    return p, len(ids) - p


def first_mismatch(recorded, got):
    for i, (a, b) in enumerate(zip(recorded, got)):
        if a != b:
            return i
    return None if len(recorded) == len(got) else min(len(recorded), len(got))


if __name__ == "__main__":
    lib = _load()
    only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else None
    data = json.loads(DATA.read_text()) if DATA.exists() else {}
    for name, units, gap, steps, tier in RUNS:
        if only and name not in only:
            continue
        data[name] = record_run(lib, name, units, gap, steps)
        print(name, data[name]["in_use"], data[name]["live_after"], flush=True)
        DATA.write_text(json.dumps(data, separators=(",", ":")) + "\n")
