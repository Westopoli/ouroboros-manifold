"""SIM-LOGS, the ring: struct layout, the cap, oldest-first iteration, determinism, save round trip, load rejections.

Spec: docs/northstar/plans/2026-10-15-sim-logs-spec.md rev 4 ("State", "Accessors", "Save and hash").
Covers only what the W1/W2/W4 rulings do not touch (no reader or flag tests here).

RED today: om_simlog_* are not in libouroboros.so yet. They are bound here straight from the
spec's Accessors paragraph with ctypes (conftest.py is not edited; its generated bindings pick
the symbols up when the builder adds the signatures.toml rows). Reaching a missing symbol raises
AttributeError from the library handle, which counts as red. The tests that need no new symbol
(struct sizes, the "an uncorrupted save loads" control, the corruption locator's negative case)
stay green.

Names the spec leaves implicit, decided here (builder: match or tell the Architect):
  om_simlog_conquest_count / om_simlog_conquest_get_at, om_simlog_event_count / om_simlog_event_get_at
  ("the same pair for conquests and events"); the saved block's header is contiguous
  (window_start i64, last_mission_region i32, attack n, conquest n, event n as u32, little-endian),
  followed by the attack entries, then the conquest entries, then the event entries, each oldest
  first, every field written one at a time in struct order (tick i64, then the four 4-byte fields;
  commit as the IEEE-754 bits of a double).
"""
import ctypes
import json
import pathlib
import struct
import subprocess
import sys

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMStance,
    OMTier,
    force_draws,
    isolate_agents,
    read_attacks,
    read_events,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)

CSIM_DIR = pathlib.Path(__file__).resolve().parent

OM_LOG_ATTACK_CAP = 4096
OM_LOG_CONQUEST_CAP = 1024
OM_LOG_EVENT_CAP = 4096
TID_LAUNCH_COUNT = 26
OM_CONQ_ATTACK, OM_CONQ_MISSION, OM_CONQ_REVOLT, OM_CONQ_REVERSION, OM_CONQ_ABSORPTION, OM_CONQ_COLONISATION = range(6)

CAMPAIGN_REGIONS = 80
CAMPAIGN_SEED = 7
MAX_TICKS = 20000


# ---- struct mirrors, field order per the spec's State block ----

class LogAttack(ctypes.Structure):
    _fields_ = [("tick", ctypes.c_int64), ("attacker", ctypes.c_int32),
                ("target_region", ctypes.c_int32), ("commit", ctypes.c_double)]


class LogConquest(ctypes.Structure):
    _fields_ = [("tick", ctypes.c_int64), ("region", ctypes.c_int32), ("old_faction", ctypes.c_int32),
                ("new_faction", ctypes.c_int32), ("kind", ctypes.c_int32)]


class LogEvent(ctypes.Structure):
    _fields_ = [("tick", ctypes.c_int64), ("region", ctypes.c_int32), ("template_id", ctypes.c_int32),
                ("chain_tag", ctypes.c_int32), ("creates_faction", ctypes.c_int32)]


KINDS = {
    "attack": (LogAttack, "om_simlog_attack_count", "om_simlog_attack_get_at", OM_LOG_ATTACK_CAP),
    "conquest": (LogConquest, "om_simlog_conquest_count", "om_simlog_conquest_get_at", OM_LOG_CONQUEST_CAP),
    "event": (LogEvent, "om_simlog_event_count", "om_simlog_event_get_at", OM_LOG_EVENT_CAP),
}


def bind_logs(lib):
    """Bind the Accessors paragraph's symbols. A missing symbol raises AttributeError here (the red)."""
    V = ctypes.c_void_p
    for _, (struct_t, count_name, get_name, _cap) in KINDS.items():
        count = getattr(lib, count_name)
        count.argtypes = [V]
        count.restype = ctypes.c_uint32
        get = getattr(lib, get_name)
        get.argtypes = [V, ctypes.c_uint32, ctypes.POINTER(struct_t)]
        get.restype = ctypes.c_int
    lib.om_simlog_window_start.argtypes = [V]
    lib.om_simlog_window_start.restype = ctypes.c_int64
    return lib


def read_log(lib, w, kind):
    """The whole log, oldest first, as tuples."""
    struct_t, count_name, get_name, _ = KINDS[kind]
    n = getattr(lib, count_name)(w)
    out = []
    for i in range(n):
        rec = struct_t()
        assert getattr(lib, get_name)(w, i, ctypes.byref(rec)) == 0, f"{get_name}({i}) of {n} failed"
        out.append(tuple(getattr(rec, f[0]) for f in struct_t._fields_))
    assert getattr(lib, get_name)(w, n, ctypes.byref(struct_t())) == 1, f"{get_name}(n) must return 1 (bad index)"
    return out


def read_all(lib, w):
    return {k: read_log(lib, w, k) for k in KINDS}


# ---- the save helpers (local binding, as test_E16_S111_saving.py does) ----

def _bind_save(lib):
    V, P = ctypes.c_void_p, ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int


def save_bytes(lib, w):
    _bind_save(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return bytes(buf)


def load_bytes(lib, w, data):
    _bind_save(lib)
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    return lib.om_load_state_read(w, buf, len(data))


def full_hash(lib, w):
    sections = (ctypes.c_uint64 * 16)()
    return lib.om_world_checksum_full(w, sections, 16), list(sections)


# ---- scenarios ----

def campaign(lib, seed=CAMPAIGN_SEED, n_regions=CAMPAIGN_REGIONS):
    """The same campaign the lifecycle tests build: generated world, launch event and mission libraries."""
    w = lib.om_world_new(n_regions, seed)
    for f in range(9):
        lib.om_world_set_feature(w, f, 1 if f < 8 else 0)
    lib.om_world_generate(w)
    assert lib.om_world_generated(w)
    lib.om_events_load_launch(w)
    lib.om_mission_load_launch_library(w)
    lib.om_campaign_start(w, 1)
    return w


def conquest_world(lib, world_factory):
    """test_E05_S038 R-038-01: a telegraphed attack declared on tick 1 conquers region 1 on tick 4.
    Leaves one attack entry and one kind-0 conquest entry (after the symbols exist)."""
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=60.0, confidence=2.0)
    set_faction(lib, w, 1, OMArchetype.FORTIFIER, budget=0.0)
    set_stance(lib, w, 0, 1, OMStance.HOSTILE)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_tech_multipliers(lib, w, 1, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=8.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=20.0, economy=16.0, tension=10.0, population=50.0, faction_id=1)
    set_owner(lib, w, 1, 1, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    force_draws(lib, w, [0.1, 0.5])
    lib.om_world_step(w)
    lib.om_world_step(w)
    lib.om_world_step(w)
    force_draws(lib, w, [1.0, 0.8])
    lib.om_world_step(w)
    assert lib.om_region_owner(w, 1) == 0, "fixture: the attack must conquer region 1"
    return w


def event_world(lib, world_factory):
    """test_E07_S049 R-049-01 case B: Revolt Entrenched fires in region 0 and a breakaway faction forms."""
    from conftest import OMFeature, load_only_templates, queue_external, template_id
    w = world_factory(n_regions=2)
    isolate_agents(lib, w)
    lib.om_world_set_feature(w, OMFeature.FACTIONS, 0)
    load_only_templates(lib, w, "Revolt Entrenched")
    lib.om_world_set_feature(w, OMFeature.EVENTS, 1)
    lib.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=10.0, confidence=5.0)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=50.0, tension=70.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=50.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 1, 0, held_since=-1)
    queue_external(lib, w, 0, template_id(lib, w, "Revolt Entrenched"), due_tick=1, probability=1.0)
    force_draws(lib, w, [0.99, 0.50, 0.50, 0.50])
    lib.om_world_step(w)
    assert lib.om_faction_count(w) == 2, "fixture: the breakaway must form"
    return w


class Run:
    """One long campaign run, with the per-tick attack and event records the old API exposes
    accumulated in Python so the ring can be checked against what was produced."""
    pass


def run_to_cap(lib):
    w = campaign(lib)
    r = Run()
    r.w = w
    r.attacks, r.attack_conquests, r.events = [], [], []
    r.ticks = 0
    for t in range(1, MAX_TICKS + 1):
        lib.om_world_step(w)
        for a in read_attacks(lib, w):
            r.attacks.append((int(a.tick), int(a.attacker), int(a.target_idx), float(a.commit)))
            if a.conquest:
                r.attack_conquests.append((int(a.tick), int(a.target_idx), int(a.defender), int(a.attacker)))
        for e in read_events(lib, w):
            r.events.append((int(e.tick), int(e.region_idx), int(e.template_id), int(e.chain_tag), int(e.creates_faction)))
        r.ticks = t
        if (len(r.attacks) >= OM_LOG_ATTACK_CAP + 500 and len(r.attack_conquests) >= OM_LOG_CONQUEST_CAP + 200
                and len(r.events) >= OM_LOG_EVENT_CAP + 300):
            break
    return r


@pytest.fixture(scope="module")
def capped(lib):
    r = run_to_cap(lib)
    yield r
    lib.om_world_free(r.w)


# ---- layout (needs no new symbol: green today) ----

@pytest.mark.parametrize("struct_t", [LogAttack, LogConquest, LogEvent])
def test_log_structs_are_24_bytes_without_padding(struct_t):
    assert ctypes.sizeof(struct_t) == 24
    offsets = [getattr(struct_t, f[0]).offset for f in struct_t._fields_]
    assert offsets == [0, 8, 12, 16, 20][:len(offsets)] if struct_t is not LogAttack else offsets == [0, 8, 12, 16]


def test_the_cap_scenario_reaches_every_cap_without_new_symbols(lib, capped):
    """Fixture check: the 80-region campaign (seed 7) produces more than each cap, counted from the old per-tick
    records. Green today; the 'rings hold the newest' tests below rest on it."""
    assert len(capped.attacks) > OM_LOG_ATTACK_CAP, (capped.ticks, len(capped.attacks))
    assert len(capped.attack_conquests) > OM_LOG_CONQUEST_CAP, (capped.ticks, len(capped.attack_conquests))
    assert len(capped.events) > OM_LOG_EVENT_CAP, (capped.ticks, len(capped.events))


# ---- the ring ----

def test_attack_ring_keeps_the_newest_oldest_first(lib, capped):
    bind_logs(lib)
    log = read_log(lib, capped.w, "attack")
    assert len(log) == OM_LOG_ATTACK_CAP
    assert lib.om_simlog_attack_count(capped.w) == OM_LOG_ATTACK_CAP
    assert [e[0] for e in log] == sorted(e[0] for e in log), "oldest first: tick non-decreasing"
    expected = [(t, a, tr, c) for (t, a, tr, c) in capped.attacks[-OM_LOG_ATTACK_CAP:]]
    assert log == expected, "the 4,096 newest resolved attacks survive, in order"
    assert log[0][0] > capped.attacks[0][0], "the oldest are gone"


def test_conquest_ring_keeps_the_newest_oldest_first(lib, capped):
    bind_logs(lib)
    log = read_log(lib, capped.w, "conquest")
    assert len(log) == OM_LOG_CONQUEST_CAP
    assert [e[0] for e in log] == sorted(e[0] for e in log)
    assert log[0][0] > capped.attack_conquests[0][0], "the oldest conquest is gone"
    first_tick = log[0][0]
    # every attack conquest strictly newer than the ring's oldest tick is in the ring, as kind 0, in order
    want = [(t, reg, old, new) for (t, reg, old, new) in capped.attack_conquests if t > first_tick]
    got = [(e[0], e[1], e[2], e[3]) for e in log if e[4] == OM_CONQ_ATTACK and e[0] > first_tick]
    assert got == want
    assert all(0 <= e[4] <= OM_CONQ_COLONISATION for e in log)


def test_event_ring_keeps_the_newest_oldest_first(lib, capped):
    bind_logs(lib)
    log = read_log(lib, capped.w, "event")
    assert len(log) == OM_LOG_EVENT_CAP
    assert [e[0] for e in log] == sorted(e[0] for e in log)
    assert log == capped.events[-OM_LOG_EVENT_CAP:]
    assert log[0][0] > capped.events[0][0]


def test_get_at_rejects_a_bad_index_and_null(lib, capped):
    bind_logs(lib)
    out = LogAttack()
    assert lib.om_simlog_attack_get_at(capped.w, OM_LOG_ATTACK_CAP, ctypes.byref(out)) == 1
    assert lib.om_simlog_attack_get_at(capped.w, 0, None) == 1


# ---- determinism across two processes ----

_CHILD = r'''
import json, sys
sys.path.insert(0, %(csim)r)
import test_SIM_logs_ring as T
import conftest as C
lib = C.load_lib()
T.bind_logs(lib)
w = T.campaign(lib)
for _ in range(%(ticks)d):
    lib.om_world_step(w)
print(json.dumps({"logs": T.read_all(lib, w), "ws": lib.om_simlog_window_start(w), "hash": T.full_hash(lib, w)}))
'''


def _child(ticks):
    code = _CHILD % {"csim": str(CSIM_DIR), "ticks": ticks}
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)
    assert res.returncode == 0, "child process failed:\n" + res.stderr[-1500:]
    return json.loads(res.stdout.strip().splitlines()[-1])


def test_same_seed_two_processes_byte_identical_logs():
    ticks = 1500
    a, b = _child(ticks), _child(ticks)
    assert len(a["logs"]["attack"]) > 100 and len(a["logs"]["conquest"]) > 10, "fixture: the logs must be non-empty"
    assert a["logs"] == b["logs"], "full iterated lists, all three logs"
    assert a["hash"] == b["hash"] and a["ws"] == b["ws"]


# ---- save round trip ----

def test_save_round_trip_of_a_wrapped_ring(lib, capped):
    bind_logs(lib)
    before = read_all(lib, capped.w)
    assert len(before["attack"]) == OM_LOG_ATTACK_CAP, "fixture: rings have wrapped, head != n mod cap in general"
    data = save_bytes(lib, capped.w)
    w2 = lib.om_world_new(CAMPAIGN_REGIONS, 999)
    try:
        assert load_bytes(lib, w2, data) == 0
        after = read_all(lib, w2)
        assert after == before
        assert lib.om_simlog_window_start(w2) == lib.om_simlog_window_start(capped.w)
        assert full_hash(lib, w2)[0] == full_hash(lib, capped.w)[0]
        assert save_bytes(lib, w2) == data, "head is not saved: a loaded world writes the same bytes back"
    finally:
        lib.om_world_free(w2)


# ---- load rejections ----

def find_header(data, window_start, last_mission_region, ns):
    """Locate the block's contiguous header (see the module docstring); -1 if absent."""
    pat = struct.pack("<qiIII", window_start, last_mission_region, *ns)
    return data.find(pat)


def patch(data, offset, fmt, value):
    out = bytearray(data)
    struct.pack_into("<" + fmt, out, offset, value)
    return bytes(out)


def _fresh_load(lib, world_factory, n_regions, data):
    w = world_factory(n_regions=n_regions)
    before = full_hash(lib, w)
    rc = load_bytes(lib, w, data)
    return rc, before, full_hash(lib, w)


def test_uncorrupted_save_loads_control(lib, world_factory):
    """Positive control, needs no new symbol: an unmodified save of the conquest fixture loads (rc 0)."""
    w = conquest_world(lib, world_factory)
    data = save_bytes(lib, w)
    rc, _, _ = _fresh_load(lib, world_factory, 2, data)
    assert rc == 0


def _block(lib, w, data):
    """(header_offset, n_attack, n_conquest, n_event) of w's saved block."""
    bind_logs(lib)
    ns = (lib.om_simlog_attack_count(w), lib.om_simlog_conquest_count(w), lib.om_simlog_event_count(w))
    h = find_header(data, lib.om_simlog_window_start(w), -1, ns)
    assert h >= 0, f"the saved block's header {ns} was not found: layout differs from the module docstring"
    return h, ns


# (name, kind of entry, field offset inside the 24-byte entry, struct format, bad value)
ATTACK_FIELDS = [("attacker=n_factions", 8, "i", 2), ("attacker=-1", 8, "i", -1),
                 ("target_region=n_regions", 12, "i", 2), ("target_region=-1", 12, "i", -1)]
CONQUEST_FIELDS = [("region=n_regions", 8, "i", 2), ("old_faction=-2", 12, "i", -2),
                   ("old_faction=n_factions", 12, "i", 2), ("new_faction=n_factions", 16, "i", 2),
                   ("new_faction=-1", 16, "i", -1), ("kind=6", 20, "i", 6), ("kind=-1", 20, "i", -1)]
EVENT_FIELDS = [("region=n_regions", 8, "i", 2), ("template_id=TID_LAUNCH_COUNT", 12, "i", TID_LAUNCH_COUNT),
                ("template_id=-1", 12, "i", -1)]


@pytest.mark.parametrize("name,off,fmt,bad", ATTACK_FIELDS, ids=[f[0] for f in ATTACK_FIELDS])
def test_load_rejects_bad_attack_field(lib, world_factory, name, off, fmt, bad):
    w = conquest_world(lib, world_factory)
    data = save_bytes(lib, w)
    h, (na, nc, ne) = _block(lib, w, data)
    assert na >= 1
    rc, before, after = _fresh_load(lib, world_factory, 2, patch(data, h + 24 + off, fmt, bad))
    assert rc != 0, f"load accepted attack entry 0 with {name}"
    assert after == before, "a refused load must not touch the world"


@pytest.mark.parametrize("name,off,fmt,bad", CONQUEST_FIELDS, ids=[f[0] for f in CONQUEST_FIELDS])
def test_load_rejects_bad_conquest_field(lib, world_factory, name, off, fmt, bad):
    w = conquest_world(lib, world_factory)
    data = save_bytes(lib, w)
    h, (na, nc, ne) = _block(lib, w, data)
    assert nc >= 1
    rc, before, after = _fresh_load(lib, world_factory, 2, patch(data, h + 24 + 24 * na + off, fmt, bad))
    assert rc != 0, f"load accepted conquest entry 0 with {name}"
    assert after == before


@pytest.mark.parametrize("name,off,fmt,bad", EVENT_FIELDS, ids=[f[0] for f in EVENT_FIELDS])
def test_load_rejects_bad_event_field(lib, world_factory, name, off, fmt, bad):
    w = event_world(lib, world_factory)
    data = save_bytes(lib, w)
    h, (na, nc, ne) = _block(lib, w, data)
    assert ne >= 1
    rc, before, after = _fresh_load(lib, world_factory, 2, patch(data, h + 24 + 24 * (na + nc) + off, fmt, bad))
    assert rc != 0, f"load accepted event entry 0 with {name}"
    assert after == before


@pytest.mark.parametrize("which,off,cap", [("attack", 12, OM_LOG_ATTACK_CAP), ("conquest", 16, OM_LOG_CONQUEST_CAP),
                                           ("event", 20, OM_LOG_EVENT_CAP)])
def test_load_rejects_n_above_cap(lib, world_factory, which, off, cap):
    """Positive control for the cap check: n = cap + 1 fails; n = the true n loads (the unmodified save)."""
    w = conquest_world(lib, world_factory)
    data = save_bytes(lib, w)
    h, _ = _block(lib, w, data)
    rc, before, after = _fresh_load(lib, world_factory, 2, patch(data, h + off, "I", cap + 1))
    assert rc != 0, f"load accepted {which} n = {cap + 1}"
    assert after == before
    assert _fresh_load(lib, world_factory, 2, data)[0] == 0


def test_corrupted_byte_in_the_block_changes_the_world_hash(lib, world_factory):
    """Positive control for the hash: flip one low mantissa bit of the first attack entry's commit (still a legal
    value, so the load succeeds); the loaded world's full hash differs from the clean load's."""
    w = conquest_world(lib, world_factory)
    data = save_bytes(lib, w)
    h, _ = _block(lib, w, data)
    commit_off = h + 24 + 16
    bent = bytearray(data)
    bent[commit_off] ^= 0x01
    rc_a, _, hash_clean = _fresh_load(lib, world_factory, 2, data)
    rc_b, _, hash_bent = _fresh_load(lib, world_factory, 2, bytes(bent))
    assert rc_a == 0 and rc_b == 0
    assert hash_clean[0] != hash_bent[0], "the world hash must cover the log block"
    assert hash_clean[1] != hash_bent[1], "and at least one named section must differ"
