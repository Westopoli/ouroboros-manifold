"""Visible-game lane E1, contract piece K-e5 (VG-CONTRACT-E5): the saved density block, the load rejections, format 10, ABI 7
and the test hook om_terrain_set_heights. Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md rev 10d, "Lane E1 part c:
the settlement port", the K-e5 paragraph (every case names the K-e5 clause it proves). Rules R-168-01/05 (new world state is
saved and hashed), R-111-03 (a refused load touches nothing). Fenced: builders never edit this file. Written on the built tree
that has no K-e5 code (rules.md (d)).

How the economy block is read: through the save bytes, the way test_VG_E_contract.py reads the version word. The block is
located without a fixed offset: the eleven module slots close the buffer (u8 id, u32 length, blob; ids 0..10, csrc/om_internal.h
OM_SAVE_SLOT_*), the block ends where the first slot starts, and its start is the one offset from which the documented layout
parses to exactly that end (cross-checked against the live lot count). Every field is little-endian; a double is its IEEE bits.

  new layout (K-e5): u32 n_lots | n_lots x (u32 id, f64 x, f64 y, i32 stage, i32 building, i32 owner) | u32 density_present
    | only when 1: u32 density_side | f64 D[side*side] | f64 P[side*side] | u32 n_active | u32 active[n_active] | u32 core_cell
    | u32 n_strongpoints | n x (u32 id, f64 x, f64 y, i32 owner, i32 state) | u32 doctrine_chosen | i32 doctrine
    | u32 n_waves | n x (u32 tick, i32 kind, f64 x, f64 y) | f64 density_economy | u32 lot_hit_tick[OM_LOT_CAP] | u32 next_lot_id

OM_LOT_CAP is 2048 (DRAFT-lot-cap, named in the K-e5 paragraph); OM_DENSITY_MAX_SIDE is 240.

Fixture (dumped from a real run, see the report): era kind 1 (ground), om_terrain_generate(seed 7, 24000 x 24000) which gives
240 x 240 cells of 100 wu (57600 cells), om_mission_setup(region 0, archetype 3), om_mission_begin. The K-e5 tree still runs the
old growth on the legacy 120 grid, so the legacy case below (density_side 120, n_active 0, core_cell 60*120+60) belongs to the
K-e5 tree only: E1q rewrites the density (side = canvas / 100) and retires it under its own ledger row, as it does the
next_lot_id == 1 case. Every other case reads the side from the save, so it stays valid when E1q lands.

Libraries are opened here (klib / kmake), not through conftest's lib fixture: that fixture asserts the moved ABI pin (8) and so
fails every test of the suite on the built tree for the one reason (the library still reports 6); these cases must each fail for
their own reason. After the K-e5 build the two are the same library.

Red on the built tree: the block has no density_side, P, n_active, active, core_cell or next_lot_id and the version words are
9 / 8 / ABI 6. Controls (named test_control_*) are green on the built tree and stay green after K-e5.
"""
import ctypes
import json
import os
import pathlib
import re
import struct
import subprocess
import tempfile

import pytest

import conftest as C
from conftest import OMArchetype, OMEdge, OMFeature, OMTier, set_edge, set_faction, set_owner, set_region

REPO = pathlib.Path(__file__).resolve().parents[2]
PIPE = REPO / "pipe" / "ouroboros_pipe"
W = ctypes.c_void_p
P = ctypes.POINTER

CANVAS_WU = 24000.0
TERRAIN_SIDE = 240            # 24000 wu / OM_TERRAIN_CELL_WU 100 (om_terrain_cells on the fixture)
MAX_SIDE = 240                # OM_DENSITY_MAX_SIDE (K-e5)
LEGACY_SIDE = 120             # OM_DENSITY_SIDE, legacy until E1q
LOT_CAP = 2048                # DRAFT-lot-cap (K-e5 paragraph)
LEGACY_LOT_CAP = 256          # OM_LOT_CAP on the built tree (diagnostic only)
Q16 = 65536.0
FLAT_CM = 6000                # the brief's flat terrain: every cell at TG_DRY_LEVEL_WU 60 x 100 cm, so none is above it (the dry test is strict, csrc/terrain.c:737)
FLAT_DRY_CM = 7000            # fixture value (test writer): a flat terrain whose cells are all above the dry level
RIDGE_RISE_CM = 900 * 100     # a 900 wu ridge above the flat
RIDGE_COLS = range(118, 122)  # the flat top: four cells (400 wu) wide, full height; fixture choice of the test writer
RIDGE_RAMP_CELLS = 30         # each side climbs the 900 wu over 30 cells (0.3 rise per run). Fixture choice of the test writer: a
#                               sheer step (ramp 1 to 10 cells) is unwalkable at the sim's steep limit, so it makes no slope run
#                               (probed on a throwaway K-e5 reference build: ramps of 1, 2, 5, 10 cells give 0 slopes, 20, 30, 60 give 1440)


# ------------------------------------------------------------------------------------------------ library and scene

def _bind(h):
    u32, i32 = ctypes.c_uint32, ctypes.c_int32
    f64 = ctypes.c_double
    sig = {
        "om_abi_version": ([], u32),
        "om_terrain_generate": ([W, ctypes.c_uint64, f64, f64], ctypes.c_int),
        "om_terrain_cells": ([W, P(u32), P(u32)], u32),
        "om_terrain_get_heights": ([W, P(i32), u32], u32),
        "om_terrain_slope_count": ([W], u32),
        "om_terrain_walk_mask": ([W, ctypes.c_int, P(ctypes.c_uint8), u32], u32),
        "om_terrain_dump_bands": ([W, P(ctypes.c_uint8), u32], u32),
        "om_terrain_band_heights": ([W, P(f64), u32], u32),
        "om_density_at": ([W, f64, f64], f64),
        "om_save_state_size": ([W], u32),
        "om_save_state_write": ([W, P(ctypes.c_uint8), u32], None),
        "om_load_state_read": ([W, P(ctypes.c_uint8), u32], ctypes.c_int),
        "om_world_checksum_full": ([W, P(ctypes.c_uint64), u32], ctypes.c_uint64),
        "om_world_get_state_checksum": ([W], ctypes.c_uint64),
        "om_lot_count": ([W], u32),
        "om_strongpoint_count": ([W], u32),
        "om_wave_get_since": ([W, u32, ctypes.c_void_p, u32], u32),
        "om_mission_begin": ([W], None),
        "om_map_set_canvas": ([W, f64, f64], ctypes.c_int),
        "om_world_step": ([W], ctypes.c_uint64),
    }
    for name, (args, res) in sig.items():
        fn = getattr(h, name)
        fn.argtypes, fn.restype = args, res


def hook(h):
    """The K-e5 hook, bound here (not in conftest.py): int om_terrain_set_heights(w, const int32_t *cm, cells_w, cells_h)."""
    fn = getattr(h, "om_terrain_set_heights", None)
    assert fn is not None, "om_terrain_set_heights is missing from libouroboros.so (K-e5 hook not built)"
    fn.argtypes = [W, P(ctypes.c_int32), ctypes.c_uint32, ctypes.c_uint32]
    fn.restype = ctypes.c_int
    return fn


@pytest.fixture(scope="module")
def klib():
    if not C.LIB_PATH.exists():
        pytest.fail("libouroboros.so is not built")
    h = ctypes.CDLL(str(C.LIB_PATH))
    C._configure_common(h)
    C._bind_generated(h)
    _bind(h)
    return h


@pytest.fixture
def kmake(klib):
    make, created = C._world_factory_for(klib, None)
    yield make
    for w in created:
        klib.om_world_free(w)


def scene(h, make, *, seed=7, economy=10.0, era=1, terrain=True, setup=True):
    """A generated ground mission (the default): era 1, terrain 24000 x 24000, mission set up and begun."""
    w = make(n_regions=2, seed=seed)
    h.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(h, w, 0, OMArchetype.PLAYER)
    set_faction(h, w, 1, OMArchetype.CONQUEROR)
    set_owner(h, w, 0, 0, held_since=-1)
    set_owner(h, w, 1, 1, held_since=-1)
    set_edge(h, w, 0, 1, OMEdge.BOTH)
    set_region(h, w, 0, tier=OMTier.HOME, military=10.0, economy=economy, population=10.0, faction_id=0)
    set_region(h, w, 1, tier=OMTier.HOME, military=10.0, faction_id=1)
    assert h.om_set_era_kind(w, era) == 0
    if terrain:
        assert h.om_terrain_generate(w, seed, CANVAS_WU, CANVAS_WU) in (0, 1)
    if setup:
        h.om_mission_setup(w, 0, 3, 0)
        h.om_mission_begin(w)
    return w


def steps(h, w, n):
    for _ in range(n):
        h.om_world_step(w)


def save(h, w):
    n = h.om_save_state_size(w)
    buf = (ctypes.c_uint8 * n)()
    h.om_save_state_write(w, buf, n)
    return bytes(buf)


def load(h, w, data):
    buf = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    return h.om_load_state_read(w, buf, len(data))


def sections(h, w):
    sec = (ctypes.c_uint64 * 16)()
    full = h.om_world_checksum_full(w, sec, 16)
    return full, sec[1]  # section 1 (factions) holds ck_economy (csrc/checksum_full.c), as test_VG_E_ke3.py reads it


def heights(h, w):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    n = h.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    out = (ctypes.c_int32 * max(n, 1))()
    got = h.om_terrain_get_heights(w, out, n)
    return (cw.value, ch.value), list(out[:got])


# ------------------------------------------------------------------------------------------------ save bytes

def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def slot_chain(data):
    """(start of slot 0, [(id, blob offset, blob length)] x 11) of the unique chain of eleven slots that ends exactly at the end
    of the buffer, or None. Slots are the tail of the save (csrc/save.c sv_write_slots)."""
    n = len(data)
    s = data.find(b"\x00", max(0, n - 4_000_000))
    while s != -1:
        p, spans = s, []
        for sid in range(11):
            if p + 5 > n or data[p] != sid:
                break
            ln = u32(data, p + 1)
            spans.append((sid, p + 5, ln))
            p += 5 + ln
            if p > n:
                break
        else:
            if p == n:
                return s, spans
        s = data.find(b"\x00", s + 1)
    return None


LOT_ROW, SP_ROW, WAVE_ROW = 32, 28, 24  # bytes: (u32,f64,f64,i32,i32,i32) (u32,f64,f64,i32,i32) (u32,i32,f64,f64)


def _parse(data, p, end, layout, live):
    """Parse one economy block starting at p under `layout` ('new' = K-e5, 'legacy' = the built tree). Returns a dict of
    offsets and values, or None when the bytes do not parse to exactly `end` or disagree with the live counts `live`
    (lot, strongpoint and wave counts); under 'new' next_lot_id must be at least 1 (it starts at 1), so a run of zero bytes never
    parses as a block."""
    try:
        q = p
        nl = u32(data, q)
        if nl > LOT_CAP:
            return None
        q += 4 + LOT_ROW * nl
        blk = {"start": p, "nl": nl, "dp_off": q}
        dp = u32(data, q)
        q += 4
        blk["dp"] = dp
        if dp not in (0, 1):
            return None
        if dp == 1 and layout == "legacy":
            blk["d_off"] = q
            q += 8 * LEGACY_SIDE * LEGACY_SIDE
        elif dp == 1:
            side = u32(data, q)
            if not 1 <= side <= MAX_SIDE:
                return None
            blk["side_off"], blk["side"] = q, side
            q += 4
            blk["d_off"] = q
            q += 8 * side * side
            blk["p_off"] = q
            q += 8 * side * side
            na = u32(data, q)
            if na > side * side:
                return None
            blk["na_off"], blk["na"] = q, na
            q += 4
            blk["act_off"] = q
            q += 4 * na
            blk["core_off"], blk["core"] = q, u32(data, q)
            q += 4
        blk["tail_off"] = q
        nsp = u32(data, q)
        q += 4 + SP_ROW * nsp
        if nsp != live["nsp"]:
            return None
        q += 8
        nw = u32(data, q)
        if nw != live["nw"]:
            return None
        q += 4 + WAVE_ROW * nw
        blk["de_off"] = q
        q += 8
        blk["lh_off"] = q
        q += 4 * (LOT_CAP if layout == "new" else LEGACY_LOT_CAP)
        if layout == "new":
            blk["nid_off"] = q
            if u32(data, q) < 1:
                return None
            q += 4
        if q != end:
            return None
        blk["end"], blk["layout"] = end, layout
        return blk
    except struct.error:
        return None


def locate(h, w, data, layout="new"):
    """The economy block of a save written by world w (the live lot count seeds the search), or None."""
    chain = slot_chain(data)
    assert chain is not None, "the save does not end in the eleven module slots (csrc/save.c sv_write_slots)"
    end = chain[0]
    nl = h.om_lot_count(w)
    live = {"nsp": h.om_strongpoint_count(w), "nw": h.om_wave_get_since(w, 0, None, 0)}
    cands = []
    # density_present == 1: the dword 1 that follows the n_lots dword and the lot rows
    one = struct.pack("<I", 1)
    q = data.find(one, max(0, end - 1_600_000), end)
    while q != -1:
        p = q - 4 - LOT_ROW * nl
        if p >= 0 and u32(data, p) == nl:
            cands.append(p)
        q = data.find(one, q + 1, end)
    # density_present == 0: the whole block is small
    for q in range(max(0, end - 4 * LOT_CAP - 8000), end):
        p = q - 4 - LOT_ROW * nl
        if p >= 0 and u32(data, q) == 0 and u32(data, p) == nl:
            cands.append(p)
    for p in cands:
        blk = _parse(data, p, end, layout, live)
        if blk is not None:
            return blk
    return None


def read_block(data, blk):
    f = {"head": data[blk["start"]:blk["dp_off"] + 4], "dp": blk["dp"],
         "tail": data[blk["tail_off"]:blk["lh_off"] + 4 * LOT_CAP], "nid": u32(data, blk["nid_off"])}
    if blk["dp"]:
        s = blk["side"]
        f["side"] = s
        f["D"] = list(struct.unpack_from(f"<{s * s}d", data, blk["d_off"]))
        f["P"] = list(struct.unpack_from(f"<{s * s}d", data, blk["p_off"]))
        f["active"] = list(struct.unpack_from(f"<{blk['na']}I", data, blk["act_off"]))
        f["core"] = blk["core"]
    return f


def write_block(f):
    out = bytearray(f["head"])
    if f["dp"]:
        out += struct.pack("<I", f["side"])
        out += struct.pack(f"<{len(f['D'])}d", *f["D"])
        out += struct.pack(f"<{len(f['P'])}d", *f["P"])
        out += struct.pack("<I", len(f["active"]))
        out += struct.pack(f"<{len(f['active'])}I", *f["active"])
        out += struct.pack("<I", f["core"])
    out += f["tail"]
    out += struct.pack("<I", f["nid"])
    return bytes(out)


def splice(data, blk, f):
    """The save with its economy block replaced by the block `f` describes."""
    return data[:blk["start"]] + write_block(f) + data[blk["end"]:]


def zeros(n):
    return [0.0] * n


def patched_load(h, make, src_data, src_blk, f):
    """Load the patched save into a fresh scene identical to the source's; return (rc, dst world, dst save, dst block)."""
    dst = scene(h, make)
    rc = load(h, dst, splice(src_data, src_blk, f))
    back = save(h, dst)
    return rc, dst, back, locate(h, dst, back)


def diagnose(h, w, data):
    leg = locate(h, w, data, "legacy")
    if leg is not None:
        return ("the economy block parses only as the built tree's layout (no density_side, P, n_active, active, core_cell or "
                f"next_lot_id; lot_hit_tick has {LEGACY_LOT_CAP} entries): n_lots={leg['nl']} density_present={leg['dp']}")
    return "the economy block parses under neither the K-e5 layout nor the built tree's layout"


def base_of(klib, kmake):
    """A ground mission at tick 0 (after begin), its save bytes and its located K-e5 block (an assertion, so a missing K-e5
    layout fails the case that asked, with the reason)."""
    w = scene(klib, kmake)
    data = save(klib, w)
    blk = locate(klib, w, data)
    assert blk is not None, diagnose(klib, w, data)
    return w, data, blk


# ------------------------------------------------------------------------------------------------ controls (green on the built tree)

def test_control_fresh_ground_mission_saves_loads_at_current_format_and_density_zero_before_setup(klib, kmake):
    """Positive control, same fixture as every case below: om_density_at answers 0.0 everywhere before om_mission_setup (the
    pre-setup test the K-e5 paragraph names); a fresh ground mission saves with the version word the header declares, loads
    back (0) and re-saves byte for byte."""
    pre = scene(klib, kmake, setup=False)
    for x, y in [(12000.0, 12000.0), (11950.0, 10450.0), (0.0, 0.0), (-5.0, 1e9)]:
        assert klib.om_density_at(pre, x, y) == 0.0
    w = scene(klib, kmake)
    declared = int(re.search(r"#define\s+OM_SAVE_FORMAT_VERSION\s+(\d+)", (REPO / "csrc/om_internal.h").read_text()).group(1))
    data = save(klib, w)
    assert struct.unpack_from("<I", data, 4)[0] == declared
    dst = scene(klib, kmake)
    assert load(klib, dst, data) == 0
    assert save(klib, dst) == data


def test_control_slot_chain_closes_the_save(klib, kmake):
    """Control for the byte reader: the eleven module slots are found, ids 0..10 in order, ending at the buffer end, and the
    terrain slot (id 10) carries the 240 x 240 height grid (4 bytes per cell plus its header)."""
    data = save(klib, scene(klib, kmake))
    start, spans = slot_chain(data)
    assert [s[0] for s in spans] == list(range(11))
    assert spans[-1][1] + spans[-1][2] == len(data)
    assert spans[10][2] >= 4 * TERRAIN_SIDE * TERRAIN_SIDE and start < spans[0][1]


def test_control_economy_block_is_found(klib, kmake):
    """Control for the locator (green before and after K-e5): the block parses under the K-e5 layout or, on the built tree, under
    the built tree's layout; so a red 'K-e5 layout not found' below means the layout is not there, not that the reader broke."""
    w = scene(klib, kmake)
    data = save(klib, w)
    blk = locate(klib, w, data) or locate(klib, w, data, "legacy")
    assert blk is not None and blk["dp"] == 1 and blk["nl"] == klib.om_lot_count(w)


# ------------------------------------------------------------------------------------------------ the saved block (K-e5: "Saved economy block")

def test_ke5_density_side_is_saved_after_density_present(klib, kmake):
    """K-e5: after density_present, only when it is 1, `uint32 density_side` (cells per side, at most OM_DENSITY_MAX_SIDE 240)."""
    w, data, blk = base_of(klib, kmake)
    assert blk["dp"] == 1 and 1 <= blk["side"] <= MAX_SIDE, blk


def test_ke5_init_gives_terrain_side_one_active_and_objective_core(klib, kmake):
    """K-e5 as E1q re-pinned it (spec :216 E1q init): density_side = om_terrain_cells' width, n_active = 1 (the core), core_cell =
    the objective cell, read at tick 0 (before any step). Derived from the fixture, no literal. Retires the K-e5 tree's legacy
    init (120, 0, 60 * 120 + 60) under TD-VG-E-23."""
    w, data, blk = base_of(klib, kmake)
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    klib.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    v = C.OMVec2()
    assert klib.om_objective_get_center(w, 0, ctypes.byref(v)) == 1
    core = int(v.y // 100) * cw.value + int(v.x // 100)
    assert (blk["side"], blk["na"], blk["core"]) == (cw.value, 1, core), (blk["side"], blk["na"], blk["core"])


def test_ke5_d_and_p_are_side_squared_doubles_in_q16(klib, kmake):
    """K-e5: D[side*side] and P[side*side] doubles, both Q16-truncated. The mission runs three density ticks (60 steps each) so D
    is non-zero; every saved D and P value is a multiple of 1/65536. (P stays all-zero on the K-e5 tree, whose old growth does
    not use it, so the Q16 claim for P is exercised for real by the patch case below and by the E1q field tests.)"""
    w = scene(klib, kmake)
    steps(klib, w, 180)
    data = save(klib, w)
    blk = locate(klib, w, data)
    assert blk is not None, diagnose(klib, w, data)
    f = read_block(data, blk)
    s = blk["side"]
    assert len(f["D"]) == s * s and len(f["P"]) == s * s
    assert any(v != 0.0 for v in f["D"]), "positive control: density D is non-zero after three density ticks"
    bad = [i for i, v in enumerate(f["D"] + f["P"]) if abs(v * Q16 - round(v * Q16)) > 1e-6]
    assert not bad, f"{len(bad)} saved D or P values are not Q16 multiples, first index {bad[0]}"


def test_ke5_next_lot_id_follows_lot_hit_tick_and_is_one(klib, kmake):
    """K-e5: `lot_hit_tick[OM_LOT_CAP]` (OM_LOT_CAP 2048) then `uint32 next_lot_id`, always written; 1 on the K-e5 tree where the old
    code still numbers lots n_lots + 1 (so it is 1 even with lots present; E1q retires the value)."""
    # TD-VG-E-22: E1q retires the value 1 (spec E1q-lots: id = next_lot_id++, starting at 1, so the counter is n_lots + 1) and the
    # field's D at economy 10 never reaches THRESHOLD_1, so the premise scene takes economy 40 (as TD-VG-E-20). See also: ledger.
    w = scene(klib, kmake, economy=40.0)
    steps(klib, w, 400)
    assert klib.om_lot_count(w) > 0, "premise: the old code has raised lots by tick 400"
    data = save(klib, w)
    blk = locate(klib, w, data)
    assert blk is not None, diagnose(klib, w, data)
    assert blk["nid_off"] == blk["lh_off"] + 4 * LOT_CAP and blk["end"] == blk["nid_off"] + 4
    assert u32(data, blk["nid_off"]) == klib.om_lot_count(w) + 1


def test_ke5_next_lot_id_is_written_without_a_field(klib, kmake):
    """K-e5: next_lot_id is always written, density_present 0 included (a space mission has no density fields)."""
    w = scene(klib, kmake, era=0, terrain=False)
    data = save(klib, w)
    blk = locate(klib, w, data)
    assert blk is not None, diagnose(klib, w, data)
    assert blk["dp"] == 0 and "side_off" not in blk
    assert u32(data, blk["nid_off"]) == 1


def test_ke5_identity_splice_reproduces_the_save(klib, kmake):
    """Control for the patch cases (red with them: it needs the K-e5 block): re-serialising the parsed block gives the same bytes."""
    w, data, blk = base_of(klib, kmake)
    assert splice(data, blk, read_block(data, blk)) == data


def test_ke5_patched_d_and_p_round_trip(klib, kmake):
    """K-e5: D and P round trip. D[k] and P[k] set to Q16 values, loaded into a fresh mission, come back unchanged on re-save."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    s = f["side"]
    k = 123
    f["D"][k], f["P"][k] = 0.5 + 3 / Q16, 0.25 + 5 / Q16
    rc, dst, back, nb = patched_load(klib, kmake, data, blk, f)
    assert rc == 0, "a well-formed K-e5 block with patched D and P is refused"
    g = read_block(back, nb)
    assert (g["side"], g["D"][k], g["P"][k]) == (s, f["D"][k], f["P"][k])


def test_ke5_patched_n_active_and_active_round_trip(klib, kmake):
    """K-e5: `uint32 n_active` then `uint32 active[n_active]` (the growth frontier in order) round trip in order."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    s = f["side"]
    f["active"] = [s * s - 1, 7, 7 + s, 3]
    rc, dst, back, nb = patched_load(klib, kmake, data, blk, f)
    assert rc == 0
    assert nb["na"] == 4 and read_block(back, nb)["active"] == [s * s - 1, 7, 7 + s, 3]


def test_ke5_patched_core_cell_round_trips(klib, kmake):
    """K-e5: `uint32 core_cell` round trips."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    f["core"] = 4321
    rc, dst, back, nb = patched_load(klib, kmake, data, blk, f)
    assert rc == 0 and nb["core"] == 4321


def test_ke5_patched_next_lot_id_round_trips(klib, kmake):
    """K-e5: `uint32 next_lot_id` after lot_hit_tick round trips."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    f["nid"] = 777
    rc, dst, back, nb = patched_load(klib, kmake, data, blk, f)
    assert rc == 0 and u32(back, nb["nid_off"]) == 777


def test_ke5_patched_density_side_round_trips_at_the_maximum(klib, kmake):
    """K-e5: density_side up to OM_DENSITY_MAX_SIDE (240) is accepted and read from the save, not a constant: a 240 block (the
    boundary of the rejection below) loads and re-saves with side 240 and 240 x 240 doubles each for D and P."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    f.update(side=MAX_SIDE, D=zeros(MAX_SIDE * MAX_SIDE), P=zeros(MAX_SIDE * MAX_SIDE), active=[], core=0)
    rc, dst, back, nb = patched_load(klib, kmake, data, blk, f)
    assert rc == 0, "a density_side 240 block (the maximum) is refused"
    g = read_block(back, nb)
    assert g["side"] == MAX_SIDE and len(g["D"]) == len(g["P"]) == MAX_SIDE * MAX_SIDE


@pytest.mark.parametrize("field", ["D", "P", "active", "core", "nid"])
def test_ke5_checksum_hashes_each_new_field(klib, kmake, field):
    """K-e5: "The checksum hashes the same fields in the same order": changing any one of D, P, active, core_cell or next_lot_id
    in an otherwise identical loaded world changes the economy section of om_world_checksum_full (section 1). Positive control
    first: an unpatched reload hashes the same as the source."""
    w, data, blk = base_of(klib, kmake)
    ref = sections(klib, w)
    ctl = scene(klib, kmake)
    assert load(klib, ctl, data) == 0 and sections(klib, ctl) == ref
    f = read_block(data, blk)
    if field in ("D", "P"):
        f[field][99] = 0.5
    elif field == "active":
        f["active"] = [11]
    elif field == "core":
        f["core"] = 4321
    else:
        f["nid"] = 5
    dst = scene(klib, kmake)
    assert load(klib, dst, splice(data, blk, f)) == 0
    assert sections(klib, dst)[1] != ref[1], f"the economy hash ignores {field}"


def test_ke5_checksum_hashes_density_side(klib, kmake):
    """K-e5: the checksum loops over density_side: a 240 block whose last cell holds one Q16 unit hashes differently from the
    all-zero 240 block (E1q makes the native side 240, so the "other side" case became a last-cell case, TD-VG-E-23)."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    s = f["side"]
    f.update(D=zeros(s * s), P=zeros(s * s), active=[], core=0)
    a = scene(klib, kmake)
    assert load(klib, a, splice(data, blk, f)) == 0
    f.update(side=MAX_SIDE, D=zeros(MAX_SIDE * MAX_SIDE)[:-1] + [1.0 / Q16], P=zeros(MAX_SIDE * MAX_SIDE))
    b = scene(klib, kmake)
    assert load(klib, b, splice(data, blk, f)) == 0
    assert sections(klib, a)[1] != sections(klib, b)[1]


# ------------------------------------------------------------------------------------------------ load rejections (K-e5: "Load rejects ...")

def _refuses(klib, kmake, data, blk, f):
    """(load result, True when the target world's checksums are unchanged by the refused load)."""
    dst = scene(klib, kmake)
    before = (sections(klib, dst), klib.om_world_get_state_checksum(dst))
    rc = load(klib, dst, splice(data, blk, f))
    return rc, before == (sections(klib, dst), klib.om_world_get_state_checksum(dst))


def _accepts(klib, kmake, data, blk, f):
    return load(klib, scene(klib, kmake), splice(data, blk, f)) == 0


def test_ke5_load_rejects_density_side_above_the_maximum(klib, kmake):
    """K-e5: load rejects density_side > OM_DENSITY_MAX_SIDE. A 241 block (correctly sized arrays, nothing else wrong) is refused
    and leaves the target world untouched (R-111-03); the 240 sibling is accepted."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    f.update(side=MAX_SIDE, D=zeros(MAX_SIDE ** 2), P=zeros(MAX_SIDE ** 2), active=[], core=0)
    assert _accepts(klib, kmake, data, blk, f), "positive control: the 240 block is accepted"
    over = MAX_SIDE + 1
    f.update(side=over, D=zeros(over * over), P=zeros(over * over))
    rc, untouched = _refuses(klib, kmake, data, blk, f)
    assert rc != 0, "density_side 241 was accepted"
    assert untouched


def test_ke5_load_rejects_n_active_above_side_squared(klib, kmake):
    """K-e5: load rejects n_active > side * side. side*side entries (all in range) are accepted; one more is refused."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    s2 = f["side"] ** 2
    f["active"] = [0] * s2
    assert _accepts(klib, kmake, data, blk, f), "positive control: n_active == side*side is accepted"
    f["active"] = [0] * (s2 + 1)
    rc, untouched = _refuses(klib, kmake, data, blk, f)
    assert rc != 0, "n_active == side*side + 1 was accepted"
    assert untouched


def test_ke5_load_rejects_an_active_entry_at_or_above_side_squared(klib, kmake):
    """K-e5: load rejects any active[k] >= side * side. active = [1, 2, side*side - 1] is accepted; [1, 2, side*side] is refused."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    s2 = f["side"] ** 2
    f["active"] = [1, 2, s2 - 1]
    assert _accepts(klib, kmake, data, blk, f), "positive control: active[k] == side*side - 1 is accepted"
    f["active"] = [1, 2, s2]
    rc, untouched = _refuses(klib, kmake, data, blk, f)
    assert rc != 0, "active[2] == side*side was accepted"
    assert untouched


def test_ke5_load_rejects_core_cell_at_or_above_side_squared(klib, kmake):
    """K-e5: load rejects core_cell >= side * side. side*side - 1 is accepted; side*side is refused."""
    w, data, blk = base_of(klib, kmake)
    f = read_block(data, blk)
    s2 = f["side"] ** 2
    f["core"] = s2 - 1
    assert _accepts(klib, kmake, data, blk, f), "positive control: core_cell == side*side - 1 is accepted"
    f["core"] = s2
    rc, untouched = _refuses(klib, kmake, data, blk, f)
    assert rc != 0, "core_cell == side*side was accepted"
    assert untouched


# ------------------------------------------------------------------------------------------------ version pins

def test_ke5_save_format_version_is_10(klib, kmake):
    """K-e5: OM_SAVE_FORMAT_VERSION 9 to 10; W2 moved it to 11 (TD-VG-W-1); LAB-REV2 E0 moved it to 12; read as the moved pins read it (header bytes 4..8 of a save)."""
    assert struct.unpack_from("<I", save(klib, scene(klib, kmake)), 4)[0] == 12


def test_ke5_abi_version_is_7(klib):
    """K-e5: OM_ABI_VERSION 6 to 7 (the one new public symbol), read from om_abi_version() as the moved pins read it; LAB-REV2 E0 moved it to 8 (two new public symbols)."""
    assert klib.om_abi_version() == 8


def test_ke5_pipe_sidecar_format_version_is_10_and_matches_the_save():
    """K-e5: OM_PIPE_SAVE_FORMAT_VERSION goes to 10 (it is 8 today; finding FINDING-pipe-save-version); W2 moved it to 11 (TD-VG-W-1); LAB-REV2 E0 moved it to 12. A save written through the
    pipe has sidecar format_version 12 and a version word 12 (the sidecar is the key the load-game screen reads). Control
    first: both exist and are integers."""
    if not PIPE.exists():
        pytest.fail("pipe/ouroboros_pipe is not built")

    def frame(obj):
        body = json.dumps(obj).encode()
        return len(body).to_bytes(4, "big") + body
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "slot.omsave")
        script = b"".join(frame(c) for c in [
            {"type": "cmd", "name": "set_seed", "seed": 1, "n_regions": 80, "features": [6], "new_campaign": False},
            {"type": "cmd", "name": "save", "path": path}, {"type": "cmd", "name": "quit"}])
        subprocess.run([str(PIPE)], input=script, capture_output=True, timeout=60)
        side = json.load(open(path + ".json"))
        word = struct.unpack_from("<I", open(path, "rb").read(), 4)[0]
    assert isinstance(side.get("format_version"), int) and isinstance(word, int)
    assert side["format_version"] == 12, f"sidecar format_version {side['format_version']} (save version word {word})"
    assert word == 12


# ------------------------------------------------------------------------------------------------ the hook om_terrain_set_heights

def _cells(h, w):
    cw, ch = ctypes.c_uint32(), ctypes.c_uint32()
    h.om_terrain_cells(w, ctypes.byref(cw), ctypes.byref(ch))
    return cw.value, ch.value


def _array(vals):
    return (ctypes.c_int32 * len(vals))(*vals)


def flat(cm, side=TERRAIN_SIDE):
    return [cm] * (side * side)


def ridge(base_cm, side=TERRAIN_SIDE):
    """A ridge over the full height of the map: a flat top RIDGE_RISE_CM (900 wu) above base_cm on columns RIDGE_COLS, falling
    linearly to base_cm over RIDGE_RAMP_CELLS cells on each side."""
    lo, hi = RIDGE_COLS[0], RIDGE_COLS[-1]
    out = []
    for i in range(side * side):
        gx = i % side
        d = 0 if gx in RIDGE_COLS else min(abs(gx - lo), abs(gx - hi))
        out.append(base_cm + max(0, RIDGE_RISE_CM * (RIDGE_RAMP_CELLS - d) // RIDGE_RAMP_CELLS))
    return out


def walk_masks(h, w):
    out = []
    for layer in range(5):
        buf = (ctypes.c_uint8 * (TERRAIN_SIDE * TERRAIN_SIDE))()
        n = h.om_terrain_walk_mask(w, layer, buf, TERRAIN_SIDE * TERRAIN_SIDE)
        out.append(bytes(buf[:n]))
    return out


def move_blob(data):
    """The bytes of the move slot (id 6) of a save: it holds the route-cache epoch (csrc/tactical_move.c, terrain_epoch)."""
    _, spans = slot_chain(data)
    _, off, ln = spans[6]
    return data[off:off + ln]


def epoch_delta(before, after):
    """k > 0 when the two move blobs differ only inside a 4-byte window whose lowest differing byte went up by k (a u32 epoch
    bumped by k); 0 when they are equal; -1 for any other difference."""
    assert len(before) == len(after)
    diff = [i for i in range(len(before)) if before[i] != after[i]]
    if not diff:
        return 0
    if diff[-1] - diff[0] > 3:
        return -1
    return (after[diff[0]] - before[diff[0]]) % 256


def test_control_hook_probe_epoch_blob_diff_detects_a_known_bump(klib, kmake):
    """Control for the epoch probe (green on the built tree): two saves with no change in between have equal move slots, and
    om_map_set_canvas, which bumps terrain_epoch today (tactical_move.c om_move_set_canvas_size), changes only the epoch word."""
    w = scene(klib, kmake)
    a, b = save(klib, w), save(klib, w)
    assert move_blob(a) == move_blob(b)
    assert klib.om_map_set_canvas(w, CANVAS_WU, CANVAS_WU) in (0, 1)
    c = save(klib, w)
    assert epoch_delta(move_blob(a), move_blob(c)) >= 1


def test_control_hook_probe_walk_mask_and_slopes_tell_two_terrains_apart(klib, kmake):
    """Control for the flat-vs-ridge comparison (green on the built tree): the walk-mask and slope-count probe separates two
    generated terrains of different seeds and agrees for the same seed."""
    a, b, c = scene(klib, kmake, seed=7), scene(klib, kmake, seed=7), scene(klib, kmake, seed=11)
    assert (walk_masks(klib, a), klib.om_terrain_slope_count(a)) == (walk_masks(klib, b), klib.om_terrain_slope_count(b))
    assert (walk_masks(klib, a), klib.om_terrain_slope_count(a)) != (walk_masks(klib, c), klib.om_terrain_slope_count(c))


def test_control_terrain_survives_a_save_round_trip_without_the_hook(klib, kmake):
    """Positive control for the hook round-trip case (green on the built tree): the same comparison on a generated terrain."""
    src, dst = scene(klib, kmake, seed=9), scene(klib, kmake, seed=9)
    data = save(klib, src)
    assert load(klib, dst, data) == 0
    assert heights(klib, dst)[1] == heights(klib, src)[1]
    assert klib.om_world_get_state_checksum(src) == klib.om_world_get_state_checksum(dst)
    assert sections(klib, src) == sections(klib, dst)


def test_ke5_hook_flat_terrain_returns_1_and_reads_back(klib, kmake):
    """K-e5 hook: on a generated ground mission, a flat terrain (every cell 6000 cm, none above the dry level, so the floors fall
    back to min and max of all cells) returns 1 and om_terrain_get_heights returns the given cm values."""
    fn = hook(klib)
    w = scene(klib, kmake)
    cm = flat(FLAT_CM)
    assert fn(w, _array(cm), TERRAIN_SIDE, TERRAIN_SIDE) == 1
    dims, got = heights(klib, w)
    assert dims == (TERRAIN_SIDE, TERRAIN_SIDE) and got == cm


def test_ke5_hook_ridge_terrain_returns_1_and_reads_back(klib, kmake):
    """K-e5 hook: a 900 wu ridge above the flat returns 1 and the heights read back as given."""
    fn = hook(klib)
    w = scene(klib, kmake)
    cm = ridge(FLAT_CM)
    assert fn(w, _array(cm), TERRAIN_SIDE, TERRAIN_SIDE) == 1
    assert heights(klib, w)[1] == cm


def test_ke5_hook_size_mismatch_returns_0_and_changes_nothing(klib, kmake):
    """K-e5 hook: dimensions must match the terrain's cell dimensions, else 0 (1 x 1, one column short, one row over); the
    terrain keeps its generated heights."""
    fn = hook(klib)
    w = scene(klib, kmake)
    _, before = heights(klib, w)
    assert fn(w, _array(flat(FLAT_CM, 1)), 1, 1) == 0
    assert fn(w, _array([FLAT_CM] * ((TERRAIN_SIDE - 1) * TERRAIN_SIDE)), TERRAIN_SIDE - 1, TERRAIN_SIDE) == 0
    assert fn(w, _array([FLAT_CM] * (TERRAIN_SIDE * (TERRAIN_SIDE + 1))), TERRAIN_SIDE, TERRAIN_SIDE + 1) == 0
    assert heights(klib, w)[1] == before


def test_ke5_hook_returns_0_with_no_terrain_on_a_space_mission(klib, kmake):
    """K-e5 hook: returns 0 with no terrain (a space mission, era kind 0, never generated one)."""
    fn = hook(klib)
    w = scene(klib, kmake, era=0, terrain=False)
    assert _cells(klib, w) == (0, 0)
    assert fn(w, _array(flat(FLAT_CM, 4)), 4, 4) == 0
    assert fn(w, _array(flat(FLAT_CM)), TERRAIN_SIDE, TERRAIN_SIDE) == 0


def test_ke5_hook_slopes_and_walkable_mask_differ_between_flat_and_ridge(klib, kmake):
    """K-e5 hook: it re-runs om_terrain_apply_ground, so a ridge changes the slopes and the walkable mask. A flat terrain above
    the dry level has no slope; the same flat with a 900 wu ridge (ramped sides: a sheer step is unwalkable and makes no slope
    run) has some and its walk masks differ. The comparison base is a flat above the dry level (the spec's 'flat test terrains
    use heights above 6000 cm'); the flat at exactly 6000 cm is covered by the cases above and by the round trip."""
    fn = hook(klib)
    a, b = scene(klib, kmake), scene(klib, kmake)
    assert fn(a, _array(flat(FLAT_DRY_CM)), TERRAIN_SIDE, TERRAIN_SIDE) == 1
    assert fn(b, _array(ridge(FLAT_DRY_CM)), TERRAIN_SIDE, TERRAIN_SIDE) == 1
    assert klib.om_terrain_slope_count(a) == 0
    assert klib.om_terrain_slope_count(b) > 0
    assert walk_masks(klib, a) != walk_masks(klib, b)


def test_ke5_hook_bumps_the_move_epoch(klib, kmake):
    """K-e5 hook: it ends in om_terrain_apply_ground, which bumps the move (route-cache) epoch; the move slot of a save differs
    before and after only in the epoch word, which went up."""
    fn = hook(klib)
    w = scene(klib, kmake)
    before = move_blob(save(klib, w))
    assert fn(w, _array(ridge(FLAT_DRY_CM)), TERRAIN_SIDE, TERRAIN_SIDE) == 1
    assert epoch_delta(before, move_blob(save(klib, w))) >= 1


@pytest.mark.parametrize("name,cm", [("flat6000", flat(FLAT_CM)), ("ridge", ridge(FLAT_DRY_CM)), ("ridge_on_6000", ridge(FLAT_CM))])
def test_ke5_hook_terrain_survives_a_save_round_trip(klib, kmake, name, cm):
    """K-e5 hook: a save round trip on the synthetic terrain keeps the heights, the band floors, the cell bands and the
    checksums (ts_bands_from_floors is shared with ts_save_read, so the bands re-derived on load equal the ones the hook set).
    The destination is a fresh mission with its own generated terrain."""
    fn = hook(klib)
    src, dst = scene(klib, kmake), scene(klib, kmake)
    assert fn(src, _array(cm), TERRAIN_SIDE, TERRAIN_SIDE) == 1
    data = save(klib, src)
    assert load(klib, dst, data) == 0
    assert heights(klib, dst)[1] == cm
    n = TERRAIN_SIDE * TERRAIN_SIDE
    bs, bd = (ctypes.c_uint8 * n)(), (ctypes.c_uint8 * n)()
    assert klib.om_terrain_dump_bands(src, bs, n) == klib.om_terrain_dump_bands(dst, bd, n) == n
    assert bytes(bs) == bytes(bd)
    fs, fd = (ctypes.c_double * 5)(), (ctypes.c_double * 5)()
    assert klib.om_terrain_band_heights(src, fs, 5) == klib.om_terrain_band_heights(dst, fd, 5) == 5
    assert list(fs) == list(fd)
    assert klib.om_world_get_state_checksum(src) == klib.om_world_get_state_checksum(dst)
    assert sections(klib, src) == sections(klib, dst)
    assert save(klib, dst) == data
