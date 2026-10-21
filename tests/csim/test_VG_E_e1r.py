"""Visible-game lane E1 part e, piece E1r (VG-E1R): placement clears instead of refusing
(docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12+, "Lane E1 part e", the E1r paragraph only; "Rev 12b rulings" and
"Rev 12c batch 2" do not amend it; Architect rulings on the script's gaps, 2026-10-19, taken as written and named below).
Fenced: builders never edit this file. Written on the built tree (origin/main): om_economy_place refuses a natural lot within
4 cells (E1E_OVERLAP 3) and om_lots_remove_row does not exist.

Rules proved, word for word:
  R-193-03 (docs/bible/epics/E-17-map-generation.md:317): "Given a building the player places, When it claims its footprint, Then
    the self-built pieces under it are cleared and the pieces around it are refilled. Where it may be placed is E-22 S-168."
  R-168-01 (docs/bible/epics/E-22-economy-and-bases.md:55): "Given a paired economy player, When he places a building, Then it
    claims its footprint and the self-built pieces around it are cleared and refilled, so the city reshapes around what he
    placed (E-17 R-166-03)."  (Read as R-193-03 and the spec's E1r do: the natural lots under the 5 x 5 footprint are cleared, the
    2-cell ring around it is refilled by the ordinary lot step; the footprint itself does not refill.)
  Q-168-01 (c), register, closed 2026-10-06: "free placement, with limits only from terrain". Q-168-05 (a): no maximum in the
    beta, terrain only (the lot table limit OM_LOT_CAP is the table's, DRAFT-lot-cap).
  DRAFT-place-on-placed (ledger day31, register Q-168-06, OPEN, default (a)): a placed building (owner >= 0) whose footprint
    overlaps the new footprint still refuses; (b) replace and (c) overlap are Westley's.

The fixture is the spec's: the E1q fixture (imported from test_VG_E_e1q_lots), a ground mission, seed 7, FLAT terrain, economy
40, 300 steps so natural lots exist. The lot table is read through om_lot_count / om_lot_get_at, lot_hit_tick through the save
bytes (hit_ticks), a patched lot_hit_tick through the saved economy block (locate, as test_VG_E_ke5.py does). The footprint is the
5 x 5 cells (Chebyshev <= 2) about the centre cell, the ring Chebyshev 3 and 4, 100 wu cells (economy_place.c E1E_HALF 2).
om_economy_place codes (economy_place.c:13-17, internal): 0 accepted, 2 unwalkable, 3 overlap, 4 table full.

Gap rulings used (script args.gaps, Architect 2026-10-19):
  lotat (a): `lot_at` has no getter, so its clearing is proved by the observable proxy: after the clearing and 40 further steps
    no two lots share a cell, no natural lot has been created inside the footprint, and every surviving lot is unchanged in id, x,
    y, building, owner and lot_hit_tick. PREMISE FIXED IN THE TEST: stage is not constant over 40 steps on this fixture (the
    first four lots rise from 1 to 2 at the lot step of tick 300, dumped below), so a survivor's stage is compared with the same
    lot in a twin world that ran the same steps without the placement. Nothing else about the survivors is loosened.
  ring (b): the refill is proved as: after the clear and 120 further ticks (two density steps) no lot exists inside the footprint,
    every ring lot that stood before the placement stands unchanged (id, x, y, building, owner; its stage may rise, as in the
    twin), and at least one new stage-1 lot has been created outside the footprint; the creation is also compared cell for cell
    with the twin world without the placement (creation continues as on every other cell, only the footprint is blocked). A
    fixture that creates no new lot in 120 ticks is a STOP ("gap:"), never a pass.
  tail (a): a removal shifts lots[] and lot_hit_tick[] down one and zeroes lot_hit_tick[old n_lots - 1]; zero is the saved and
    hashed value, so after a placement every slot from the new n_lots up to the old n_lots - 1 reads 0.
  full (a): E1E_FULL is tested after the clearing count, before any mutation: cleared = the natural lots under the footprint;
    refuse (4) only if n_lots - cleared + 1 > OM_LOT_CAP; a refusal changes nothing.
  play (a): defer. E1R lands sim-only; these C tests are the proof; plays/E/S-168.py is untouched.

Positive controls (green on the built tree): test_control_walkable_footprint_is_accepted_on_the_grown_fixture,
test_control_hit_tick_patch_loads_back, test_unwalkable_footprint_returns_2_and_changes_nothing,
test_placed_on_placed_four_apart_refuses_five_apart_accepts, test_at_the_cap_a_footprint_with_no_natural_lot_is_refused_full.
Everything else is red on the built tree because the first placement over natural lots returns E1E_OVERLAP (3).
No number in this file is a threshold, tolerance or window: 300 steps (the spec's), 40 (gap lotat), 120 (gap ring), the
fixture's economy 40 (E1q) and 100 for the cap (E1q's cap case), hit-tick markers equal to the lot id (a fixture marker).
"""
import ctypes
import struct

from test_VG_E_e1q_lots import (scene, flat, FLAT_CM, steps, lots, cell_of, objective_cell, hit_ticks, save, load,
                                CELL_WU, bind, OM_LOT_CAP)
from test_VG_E_ke5 import locate

W = ctypes.c_void_p
U64 = ctypes.c_uint64

BUILDING = 3                 # the era-pack building id given to om_economy_place (any; e1e.py uses 3)
HALF = 2                     # E1E_HALF: footprint 5 x 5
SPAN = 2 * HALF              # E1E_SPAN: a lot within 4 cells
FIXTURE_STEPS = 300          # spec E1r: "300 steps so natural lots exist"
PROXY_STEPS = 40             # gap lotat (a)
REFILL_STEPS = 120           # gap ring (b): two density steps
E1E_OK, E1E_UNWALKABLE, E1E_OVERLAP, E1E_FULL = 0, 2, 3, 4
SAVE_SERIAL_OFFSET, SAVE_SERIAL_BYTES = 40, 8   # csrc/save.c:310 world_serial, per-process (as test_VG_W_w1_planner.py masks it)
CHECKSUM_SECTIONS = 9        # OM_NET_SECTION_COUNT

_CAP_BYTES = {}              # the saved world at the lot cap, built once per process


WALL_RISE_CM = 90000         # a 900 wu step: probed on this fixture, the cells at cx + 5 and cx + 6 are then unwalkable
WALL_COL = 6                 # the step starts at column cx + WALL_COL


def wall_east(gx, gy, cx, cy):
    """FLAT with a 900 wu wall from column cx + 6 east: a footprint reaching cx + 5 holds unwalkable cells (terrain limit)."""
    return FLAT_CM + (WALL_RISE_CM if gx >= cx + WALL_COL else 0)


def _bind_extra(lib):
    bind(lib)
    lib.om_terrain_walkable_at.argtypes = [W, ctypes.c_double, ctypes.c_double]
    lib.om_terrain_walkable_at.restype = ctypes.c_int


def grown(lib, make, *, terrain=flat, economy=40.0, n=FIXTURE_STEPS):
    """The spec's fixture: ground mission, seed 7, `terrain`, economy, n steps. Returns (world, objective cell)."""
    w = scene(lib, make, terrain=terrain, economy=economy)
    _bind_extra(lib)
    o = objective_cell(lib, w)
    steps(lib, w, n)
    return w, o


def clone(lib, make, src, *, terrain=flat, economy=40.0, patch=None):
    """A fresh scene loaded from src's save bytes (optionally with `patch(data, blk, lots)` applied to the bytes first)."""
    data = bytearray(save(lib, src))
    if patch is not None:
        blk = locate(lib, src, bytes(data))
        assert blk is not None, "the economy block of the save does not parse under the K-e5 layout"
        patch(data, blk, lots(lib, src))
    dst = scene(lib, make, terrain=terrain, economy=economy)
    assert load(lib, dst, bytes(data)) == 0, "the patched save was refused"
    return dst


def patch_hit_ticks_to_ids(data, blk, rows):
    """lot_hit_tick[row] = the id of the lot in that row: a unique nonzero marker per lot (all <= 100 here, so a stale marker on
    a stage-0 lot would trigger economy_waves.c:16 'rubble rebuild' at once, tick 300 - marker >= 200)."""
    for row, lot in enumerate(rows):
        struct.pack_into("<I", data, blk["lh_off"] + 4 * row, lot[0])


def centre_wu(c):
    return (c[0] + 0.5) * CELL_WU, (c[1] + 0.5) * CELL_WU


def place(lib, w, c, building=BUILDING):
    x, y = centre_wu(c)
    return lib.om_economy_place(w, building, x, y)


def dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def foot_walkable(lib, w, c):
    return all(lib.om_terrain_walkable_at(w, *centre_wu((c[0] + dx, c[1] + dy)))
               for dx in range(-HALF, HALF + 1) for dy in range(-HALF, HALF + 1))


def inside(L, c):
    """Rows of natural lots whose cell lies in the 5 x 5 footprint about c."""
    return [i for i, l in enumerate(L) if l[5] < 0 and dist(cell_of(l), c) <= HALF]


def ring(L, c):
    return [i for i, l in enumerate(L) if l[5] < 0 and HALF < dist(cell_of(l), c) <= SPAN]


def by_id(L):
    return {l[0]: l for l in L}


def new_lots_first_sight(lib, w, n):
    """Step n times one at a time; {id: (cell, stage at first sight, step index 1..n)} for every id that was not in the table
    before. Created lots are stage 1 at the step that creates them (economy_lots.c: the rise loop runs before creation)."""
    seen = {l[0] for l in lots(lib, w)}
    out = {}
    for k in range(1, n + 1):
        lib.om_world_step(w)
        for l in lots(lib, w):
            if l[0] not in seen:
                seen.add(l[0])
                out[l[0]] = (cell_of(l), l[3], k)
    return out


def pick_centre(lib, make, w, o):
    """The placement cell, chosen by scanning offsets from the objective in a fixed order (Chebyshev radius, then row, then
    column) for the first whose 5 x 5 is walkable and which has, in the lot table of `w` at tick 300:
      (a) at least two natural lots under the footprint; (b) at least one natural lot in the ring (distance 3 or 4);
      (c) a natural lot in a LATER row of the table than the first removed one that is not removed (so the shift is non-trivial);
      (d) a cell in the ring that holds no lot now and receives one in the twin world within REFILL_STEPS (so the ring refill is
          observable). Returns (cell, premise dict). `w` is not stepped; the twin is a clone of it."""
    L = lots(lib, w)
    twin = clone(lib, make, w)
    ids0 = {l[0] for l in L}
    new = new_lots_first_sight(lib, twin, REFILL_STEPS)
    new_cells = {v[0] for v in new.values()}
    for r in range(0, 10):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                c = (o[0] + dx, o[1] + dy)
                ins, rg = inside(L, c), ring(L, c)
                if len(ins) < 2 or not rg or not foot_walkable(lib, w, c):
                    continue
                if not any(i > ins[0] and i not in ins for i in range(len(L))):
                    continue
                refill = sorted(x for x in new_cells if HALF < dist(x, c) <= SPAN)
                if not refill:
                    continue
                return c, {"cell": c, "inside_rows": ins, "ring_rows": rg, "refill_cells": refill, "n_before": len(L),
                           "twin_new": len(new), "ids0": ids0}
    raise AssertionError("gap: no cell within 10 of the objective has >= 2 natural lots under a walkable 5 x 5, a ring lot, a "
                         "surviving lot in a later row and a ring cell that receives a new lot in 120 ticks")


def dump(tag, **kv):
    print("PREMISE", tag, " ".join(f"{k}={v}" for k, v in kv.items()))


def lot_view(l):
    return (l[0], l[1], l[2], l[4], l[5])            # id, x, y, building, owner: what a survivor keeps exactly


def masked_save(lib, w):
    raw = bytearray(save(lib, w))
    assert int.from_bytes(raw[SAVE_SERIAL_OFFSET:SAVE_SERIAL_OFFSET + SAVE_SERIAL_BYTES], "little") >= 1, "premise: world serial"
    raw[SAVE_SERIAL_OFFSET:SAVE_SERIAL_OFFSET + SAVE_SERIAL_BYTES] = bytes(SAVE_SERIAL_BYTES)
    return bytes(raw)


def checksum(lib, w):
    secs = (U64 * CHECKSUM_SECTIONS)()
    full = lib.om_world_checksum_full(w, secs, CHECKSUM_SECTIONS)
    return full, list(secs)


# ------------------------------------------------------------------------------------------------ the controls (green today)

def test_control_walkable_footprint_is_accepted_on_the_grown_fixture(lib, world_factory):
    """T0, positive control (test_VG_E_e1e.py::test_control_walkable_footprint_is_accepted repeated on the E1q fixture): after
    300 steps a cell with a fully walkable 5 x 5 and NO lot of any kind within 4 cells is accepted (R-168-01 'it claims its
    footprint', Q-168-01 c) and the new lot, owned by the player's faction, is in the table. Green on the built tree."""
    w, o = grown(lib, world_factory)
    L = lots(lib, w)
    assert L, "control: no natural lots to test against"
    free = None
    for dx in range(12, 100):
        c = (o[0] + dx, o[1])
        if all(dist(cell_of(l), c) > SPAN for l in L) and foot_walkable(lib, w, c):
            free = c
            break
    assert free is not None, "control: no lot-free walkable cell east of the objective"
    dump("T0", n_lots=len(L), objective=o, cell=free, player_faction=lib.om_player_faction(w), cap=OM_LOT_CAP,
         tick=lib.om_tactical_tick(w), economy_steps=FIXTURE_STEPS)
    rc = place(lib, w, free)
    assert rc == E1E_OK, f"control: a walkable 5 x 5 with no lot within 4 cells was refused with {rc}"
    after = lots(lib, w)
    mine = [l for l in after if l[5] == lib.om_player_faction(w)]
    assert len(after) == len(L) + 1 and len(mine) == 1 and cell_of(mine[0]) == free and mine[0][4] == BUILDING, \
        f"control: the new lot is not in the table: {mine}"


def test_control_hit_tick_patch_loads_back(lib, world_factory):
    """Positive control for the T5 mechanism (the patch of the saved economy block): lot_hit_tick patched to the lot id in every
    row loads into a fresh scene and reads back row for row, and an unpatched clone reads all zero. Green on the built tree."""
    w, o = grown(lib, world_factory)
    L = lots(lib, w)
    patched = clone(lib, world_factory, w, patch=patch_hit_ticks_to_ids)
    plain = clone(lib, world_factory, w)
    assert lots(lib, patched) == L and lots(lib, plain) == L, "a save round trip changed the lot table"
    ht = hit_ticks(lib, patched)
    assert list(ht[:len(L)]) == [l[0] for l in L] and not any(ht[len(L):]), "the patched lot_hit_tick did not read back"
    assert not any(hit_ticks(lib, plain)), "an unpatched clone has a nonzero lot_hit_tick"


# ------------------------------------------------------------------------------------------------ the clearing (red today)

def test_placing_over_natural_lots_is_accepted(lib, world_factory):
    """T1, R-193-03 'the self-built pieces under it are cleared' + Q-168-01 c 'limits only from terrain': a placement whose
    walkable 5 x 5 holds >= 2 natural lots, with ring lots at distance 3 or 4 and a surviving lot in a later table row than the
    first removed one, is accepted. Red on the built tree: E1E_OVERLAP (3)."""
    w, o = grown(lib, world_factory)
    c, p = pick_centre(lib, world_factory, w, o)
    L = lots(lib, w)
    dump("T1", objective=o, cell=c, n_lots=len(L), pf=lib.om_player_faction(w), cap=OM_LOT_CAP, tick=lib.om_tactical_tick(w),
         inside=[(i, L[i][0], cell_of(L[i]), L[i][3]) for i in p["inside_rows"]],
         ring=[(i, L[i][0], cell_of(L[i]), L[i][3]) for i in p["ring_rows"]], refill_cells=p["refill_cells"],
         twin_new_in_120=p["twin_new"])
    rc = place(lib, w, c)
    assert rc == E1E_OK, f"R-193-03: placing over {len(p['inside_rows'])} natural lots was refused with code {rc} (E1E_OVERLAP is {E1E_OVERLAP})"


def test_the_natural_lots_under_the_footprint_are_gone_and_the_placed_lot_is_there(lib, world_factory):
    """T2, R-193-03 'cleared' / R-168-01 'it claims its footprint': after the accepted placement the natural lots whose cell lies
    in the 5 x 5 are absent from om_lot_get_at (compared by id), the placed lot (owner = the player's faction, the given building)
    stands at the cell centre, the count is before - removed + 1, ids ascend and are unique. Then, per gap lotat (a), the proxy for
    the cleared lot_at: after PROXY_STEPS further steps no two lots share a cell, no natural lot exists inside the footprint, and
    every surviving lot keeps id, x, y, building, owner and lot_hit_tick (stage as in the twin world without the placement)."""
    w, o = grown(lib, world_factory)
    c, p = pick_centre(lib, world_factory, w, o)
    twin = clone(lib, world_factory, w)
    before = lots(lib, w)
    gone = {before[i][0] for i in p["inside_rows"]}
    dump("T2-pre", cell=c, tick=lib.om_tactical_tick(w), n_before=len(before), removed_ids=sorted(gone),
         lots_before=[(l[0], cell_of(l), l[3]) for l in before])
    rc = place(lib, w, c)
    assert rc == E1E_OK, f"R-193-03: placement over natural lots refused with {rc}"
    after = lots(lib, w)
    ids = [l[0] for l in after]
    placed = [l for l in after if l[5] >= 0]
    dump("T2", removed_ids=sorted(gone), before=len(before), after=len(after), placed=placed,
         lots_before=[(l[0], cell_of(l), l[3]) for l in before], lots_after=[(l[0], cell_of(l), l[3]) for l in after])
    assert not gone & set(ids), f"natural lots still in the table under the footprint: {sorted(gone & set(ids))}"
    assert len(placed) == 1 and placed[0][5] == lib.om_player_faction(w) and placed[0][4] == BUILDING \
        and (placed[0][1], placed[0][2]) == centre_wu(c), f"the placed lot is not at the cell centre with the given building: {placed}"
    assert len(after) == len(before) - len(gone) + 1, f"count {len(after)}, expected {len(before)} - {len(gone)} + 1"
    assert ids == sorted(set(ids)) and placed[0][0] > max(l[0] for l in before), "ids do not ascend uniquely after the clear"
    steps(lib, w, PROXY_STEPS)
    steps(lib, twin, PROXY_STEPS)
    later = lots(lib, w)
    cells = [cell_of(l) for l in later]
    assert len(set(cells)) == len(cells), "two lots share a cell after the clear (lot_at proxy)"
    assert not [l for l in later if l[5] < 0 and dist(cell_of(l), c) <= HALF], "a natural lot was created inside the footprint"
    twin_by = by_id(lots(lib, twin))
    ht_a, ht_b = by_id_hits(lib, w), by_id_hits(lib, twin)
    for l in later:
        if l[0] in gone or l[0] not in {b[0] for b in before} or l[5] >= 0:
            continue
        assert lot_view(l) == lot_view(twin_by[l[0]]), f"survivor {l[0]} changed id/x/y/building/owner: {l} vs {twin_by[l[0]]}"
        assert l[3] == twin_by[l[0]][3], f"survivor {l[0]} stage {l[3]} differs from the twin without the placement ({twin_by[l[0]][3]})"
        assert ht_a[l[0]] == ht_b[l[0]], f"survivor {l[0]} lot_hit_tick moved: {ht_a[l[0]]} vs {ht_b[l[0]]}"


def by_id_hits(lib, w):
    ht = hit_ticks(lib, w)
    return {l[0]: ht[row] for row, l in enumerate(lots(lib, w))}


def test_a_ring_lot_survives_the_placement_unchanged(lib, world_factory):
    """T3, R-193-03 'the pieces around it are refilled' (they stand, they are not cleared): every natural lot outside the 5 x 5,
    the ring lots at distance 3 and 4 first, stands after the placement with the same id, x, y, stage, building and owner."""
    w, o = grown(lib, world_factory)
    c, p = pick_centre(lib, world_factory, w, o)
    before = lots(lib, w)
    ring_before = [before[i] for i in p["ring_rows"]]
    rc = place(lib, w, c)
    assert rc == E1E_OK, f"R-193-03: placement over natural lots refused with {rc}"
    after = by_id(lots(lib, w))
    for l in ring_before:
        assert after.get(l[0]) == l, f"ring lot {l} did not survive unchanged: {after.get(l[0])}"
    gone = {before[i][0] for i in p["inside_rows"]}
    for l in before:
        if l[0] not in gone:
            assert after.get(l[0]) == l, f"a natural lot outside the footprint changed: {l} -> {after.get(l[0])}"
    dump("T3", ring_survivors=[(l[0], cell_of(l), l[3]) for l in ring_before])


def test_the_ring_refills_and_the_footprint_does_not(lib, world_factory):
    """T4, R-193-03 'the pieces around it are refilled' (gap ring (b)): after the clear and REFILL_STEPS (120) ticks no natural
    lot exists inside the footprint, every ring lot that stood before stands (id, x, y, building, owner), at least one NEW stage-1
    lot has been created outside the footprint, and the new lots are exactly the twin world's (no placement) minus the footprint
    cells: creation continues on every other cell, the footprint stays blocked. Premise dumped; no new lot at all is a STOP."""
    w, o = grown(lib, world_factory)
    c, p = pick_centre(lib, world_factory, w, o)
    twin = clone(lib, world_factory, w)
    before = lots(lib, w)
    ids0 = {l[0] for l in before}
    d_ring = [(x, lib.om_density_at(w, *centre_wu(x))) for x in p["refill_cells"]]
    dump("T4-pre", cell=c, tick=lib.om_tactical_tick(w), ring_cells_expected=p["refill_cells"], D_before_placement=d_ring,
         twin_new_in_120=p["twin_new"])
    assert place(lib, w, c) == E1E_OK, "R-193-03: placement over natural lots refused"
    new = new_lots_first_sight(lib, w, REFILL_STEPS)
    tnew = new_lots_first_sight(lib, twin, REFILL_STEPS)
    d_after = [(x, lib.om_density_at(w, *centre_wu(x))) for x in p["refill_cells"]]
    dump("T4", cell=c, placement_tick=FIXTURE_STEPS, steps=REFILL_STEPS, ring_cells_expected=p["refill_cells"],
         D_before_placement=d_ring, D_after=d_after, new_with_placement=sorted((v[2], v[0], v[1]) for v in new.values()),
         new_twin=len(tnew))
    if not tnew:
        raise AssertionError("gap: the fixture creates no lot at all in 120 ticks, the refill cannot be observed")
    footprint = {(c[0] + dx, c[1] + dy) for dx in range(-HALF, HALF + 1) for dy in range(-HALF, HALF + 1)}
    now = lots(lib, w)
    assert not [l for l in now if l[5] < 0 and cell_of(l) in footprint], "a natural lot was created inside the footprint"
    assert new, "no new lot was created in 120 ticks outside the footprint (creation must continue as on every other cell)"
    assert all(v[1] == 1 for v in new.values()), f"a new lot did not start at stage 1: {new}"
    assert all(v[0] not in footprint for v in new.values()), "a new lot appeared in the footprint"
    assert {v[0] for v in new.values()} == {v[0] for v in tnew.values()} - footprint, \
        "the new lots differ from the no-placement world's outside the footprint"
    assert any(HALF < dist(v[0], c) <= SPAN for v in new.values()), "no new lot was created in the 2-cell ring"
    cur = by_id(now)
    for l in before:
        if l[0] in ids0 and HALF < dist(cell_of(l), c) <= SPAN and l[5] < 0:
            assert l[0] in cur and lot_view(cur[l[0]]) == lot_view(l), f"ring lot {l[0]} did not stand unchanged"


def test_shift_keeps_ids_and_hit_ticks_of_survivors(lib, world_factory):
    """T5, the shift of lots[] and lot_hit_tick[] (E1r paragraph: 'shifts lots[] and lot_hit_tick[] down by one'; gap tail (a)):
    lot_hit_tick is patched to the lot's id in every row of the saved economy block and loaded (route: locate + splice of the
    saved bytes, as test_VG_E_ke5.py). After the placement every surviving lot has the same id, x, y, stage, building, owner
    and the same lot_hit_tick (re-indexed by id); the placed lot's slot and every vacated slot up to old n_lots - 1 read 0; a
    stale marker would rebuild the placed lot (economy_waves.c:16), so after 5 steps its stage equals the unpatched twin's; the
    economy block loads back and the loaded table equals the live one."""
    src, o = grown(lib, world_factory)
    c, p = pick_centre(lib, world_factory, src, o)
    a = clone(lib, world_factory, src, patch=patch_hit_ticks_to_ids)
    plain = clone(lib, world_factory, src)
    before = lots(lib, a)
    n0 = len(before)
    gone = {before[i][0] for i in p["inside_rows"]}
    first_gone = p["inside_rows"][0]
    later_survivors = [i for i in range(n0) if i > first_gone and before[i][0] not in gone]
    dump("T5", patch_route="locate(save bytes) + struct.pack_into lot_hit_tick[row] = lot id, then om_load_state_read into a fresh scene",
         n_before=n0, first_removed_row=first_gone, survivors_in_later_rows=len(later_survivors), last_row_id=before[-1][0],
         last_row_survives=before[-1][0] not in gone, hit_ticks_head=list(hit_ticks(lib, a)[:8]))
    assert hit_ticks(lib, a)[n0 - 1] == before[-1][0], "premise: the last row carries a nonzero lot_hit_tick"
    assert max(l[0] for l in before) <= 100, "premise: a marker above 100 would not trigger the rubble rebuild at tick 300"
    assert place(lib, a, c) == E1E_OK, "R-193-03: placement over natural lots refused"
    assert place(lib, plain, c) == E1E_OK
    after = lots(lib, a)
    ht = hit_ticks(lib, a)
    n1 = len(after)
    assert after == lots(lib, plain), "a nonzero lot_hit_tick changed the lot table through the placement"
    kept = {l[0]: l for l in before if l[0] not in gone}
    assert [r for r in after if r[0] in kept] == [kept[r[0]] for r in after if r[0] in kept], "a survivor changed"
    for row, l in enumerate(after):
        if l[5] < 0:
            assert l[0] in kept, f"a lot appeared that was not in the table: {l}"
            assert ht[row] == l[0], f"lot {l[0]} row {row}: lot_hit_tick {ht[row]}, expected {l[0]} (the shift moved the table but not lot_hit_tick)"
        else:
            assert ht[row] == 0, f"the placed lot's slot (row {row}) holds a stale lot_hit_tick {ht[row]}"
    assert list(ht[n1 - 1:n0]) == [0] * (n0 - n1 + 1), f"vacated slots {n1 - 1}..{n0 - 1} of lot_hit_tick are not zero: {list(ht[n1 - 1:n0])}"
    assert not any(ht[n0:]), "lot_hit_tick beyond the old table is nonzero"
    steps(lib, a, 5)
    steps(lib, plain, 5)
    pa = [l for l in lots(lib, a) if l[5] >= 0]
    pp = [l for l in lots(lib, plain) if l[5] >= 0]
    assert pa == pp, f"a stale lot_hit_tick changed the placed lot: {pa} vs {pp}"
    back = scene(lib, world_factory, terrain=flat)
    assert load(lib, back, save(lib, a)) == 0, "the economy block did not load back"
    assert lots(lib, back) == lots(lib, a) and hit_ticks(lib, back) == hit_ticks(lib, a), "the loaded world's table differs from the live one"


# ------------------------------------------------------------------------------------------------ the refusals stand

def test_unwalkable_footprint_returns_2_and_changes_nothing(lib, world_factory):
    """T6a, Q-168-01 c 'limits only from terrain': on the WALL fixture (FLAT with a 900 wu step from column cx + 6, economy 40,
    300 steps) a footprint with unwalkable cells (cx + 5, cx + 6) and natural lots under it is refused with 2 (E1E_UNWALKABLE) and the lot
    table and lot_hit_tick are unchanged (the clearing is all-or-nothing: a refused placement clears none). Green on the built tree."""
    w, o = grown(lib, world_factory, terrain=wall_east)
    c = (o[0] + 4, o[1])
    L = lots(lib, w)
    ins = inside(L, c)
    dump("T6a", objective=o, cell=c, natural_lots_under_footprint=[(L[i][0], cell_of(L[i])) for i in ins],
         foot_walkable=foot_walkable(lib, w, c),
         wall_cells_walkable=[lib.om_terrain_walkable_at(w, *centre_wu((o[0] + d, o[1]))) for d in range(2, 8)])
    assert ins, "premise: the footprint holds no natural lot, the all-or-nothing check would be vacuous"
    assert not foot_walkable(lib, w, c), "premise: the footprint is walkable"
    ht = hit_ticks(lib, w)
    assert place(lib, w, c) == E1E_UNWALKABLE
    assert lots(lib, w) == L and hit_ticks(lib, w) == ht, "a refused placement changed the table"


def test_placed_on_placed_four_apart_refuses_five_apart_accepts(lib, world_factory):
    """T6b, DRAFT-place-on-placed (Q-168-06 default (a)): a first building on lot-free ground; a second 4 cells east (footprints
    share a column) is refused (nonzero) and changes nothing; 5 cells east (no shared cell) is accepted (the control that the
    refusal is about a placed building's footprint). Green on the built tree (no natural lot is near, so nothing is cleared)."""
    w, o = grown(lib, world_factory)
    a = (o[0] + 60, o[1])
    L = lots(lib, w)
    assert all(dist(cell_of(l), (a[0] + 5, a[1])) > SPAN for l in L) and foot_walkable(lib, w, a), "premise: the spot is not lot-free"
    assert place(lib, w, a) == E1E_OK, "control: the first building was refused"
    snap, ht = lots(lib, w), hit_ticks(lib, w)
    rc = place(lib, w, (a[0] + SPAN, a[1]))
    dump("T6b", first=a, second=(a[0] + SPAN, a[1]), rc_four_apart=rc)
    assert rc != E1E_OK, "DRAFT-place-on-placed: a building 4 cells from a placed one was accepted"
    assert lots(lib, w) == snap and hit_ticks(lib, w) == ht, "the refused placement changed the table"
    assert place(lib, w, (a[0] + SPAN + 1, a[1])) == E1E_OK, "control: 5 cells apart (no shared cell) was refused"


def test_a_refused_placement_over_a_placed_building_clears_no_natural_lot(lib, world_factory):
    """T6c, all-or-nothing (E1r paragraph: the placed-lot overlap 'still refuses'; a refusal changes nothing): a first building
    is placed over the town (cleared), 20 steps grow more lots, and a second 4 cells east whose footprint overlaps the first AND
    holds natural lots is refused; no natural lot is cleared, the table and lot_hit_tick are unchanged.
    Red on the built tree: the first placement returns E1E_OVERLAP."""
    w, o = grown(lib, world_factory)
    c, p = pick_centre(lib, world_factory, w, o)
    assert place(lib, w, c) == E1E_OK, f"R-193-03: the first placement over natural lots was refused"
    steps(lib, w, 20)
    second = (c[0] + SPAN, c[1])
    L = lots(lib, w)
    nat = [L[i] for i in inside(L, second)]
    dump("T6c", first=c, second=second, natural_under_second=[(l[0], cell_of(l)) for l in nat])
    assert nat, "premise: the second footprint holds no natural lot, the all-or-nothing check would be vacuous"
    assert foot_walkable(lib, w, second), "premise: the second footprint is not walkable"
    ht = hit_ticks(lib, w)
    rc = place(lib, w, second)
    assert rc != E1E_OK, "DRAFT-place-on-placed: a building 4 cells from a placed one was accepted"
    assert lots(lib, w) == L and hit_ticks(lib, w) == ht, "the refused placement cleared natural lots or changed the table"


def capped_bytes(lib, make):
    """The saved FLAT world, economy 100, after 2400 steps: the table at OM_LOT_CAP (E1q's cap fixture), built once."""
    if "b" not in _CAP_BYTES:
        w = scene(lib, make, terrain=flat, economy=100.0)
        steps(lib, w, 2400)
        assert lib.om_lot_count(w) == OM_LOT_CAP, f"premise: {lib.om_lot_count(w)} lots after 2400 steps, the cap is {OM_LOT_CAP}"
        _CAP_BYTES["b"] = save(lib, w)
    return _CAP_BYTES["b"]


def capped_world(lib, make):
    data = capped_bytes(lib, make)
    w = scene(lib, make, terrain=flat, economy=100.0)
    _bind_extra(lib)
    assert load(lib, w, data) == 0
    assert lib.om_lot_count(w) == OM_LOT_CAP, "premise: the loaded world is not at the cap"
    return w, objective_cell(lib, w)


def cap_scan(lib, w, L):
    """Centres by their natural-lot counts: {cell: (inside count, ring count)} over the lots' bounding box + 6."""
    have = {cell_of(l) for l in L}
    cells = list(have)
    x0, x1 = min(c[0] for c in cells) - 6, max(c[0] for c in cells) + 6
    y0, y1 = min(c[1] for c in cells) - 6, max(c[1] for c in cells) + 6
    out = {}
    for cx in range(max(x0, SPAN), min(x1, 236)):
        for cy in range(max(y0, SPAN), min(y1, 236)):
            ni = sum(((cx + dx, cy + dy) in have) for dx in range(-HALF, HALF + 1) for dy in range(-HALF, HALF + 1))
            nr = sum(((cx + dx, cy + dy) in have) for dx in range(-SPAN, SPAN + 1) for dy in range(-SPAN, SPAN + 1)) - ni
            out[(cx, cy)] = (ni, nr)
    return out


def test_at_the_cap_a_footprint_with_no_natural_lot_is_refused_full(lib, world_factory):
    """T6d, gap full (a), the table limit, control: with the table at OM_LOT_CAP a footprint with NO natural lot under it and none
    within 4 cells clears nothing, so n_lots - 0 + 1 > OM_LOT_CAP: refused with 4 (E1E_FULL), table and lot_hit_tick unchanged.
    Green on the built tree."""
    w, o = capped_world(lib, world_factory)
    L = lots(lib, w)
    ht = hit_ticks(lib, w)
    free = next((o[0] + dx, o[1]) for dx in range(60, 120) if all(dist(cell_of(l), (o[0] + dx, o[1])) > SPAN for l in L))
    assert foot_walkable(lib, w, free)
    rc = place(lib, w, free)
    dump("T6d-i", n_lots=len(L), cap=OM_LOT_CAP, cell=free, rc=rc)
    assert rc == E1E_FULL, f"a lot-free footprint at the cap returned {rc}, expected E1E_FULL ({E1E_FULL})"
    assert lots(lib, w) == L and hit_ticks(lib, w) == ht, "a refusal at the cap changed the table"


def test_at_the_cap_lots_only_in_the_ring_refuse_full_not_overlap(lib, world_factory):
    """T6d-ii, gap full (a), Q-168-01 c: at OM_LOT_CAP a spot with natural lots only in the 2-cell ring (distance 3 or 4) clears
    nothing and is refused with 4 (E1E_FULL), not 3 (E1E_OVERLAP): a natural lot outside the footprint never refuses. The table
    and lot_hit_tick are unchanged. Red on the built tree: E1E_OVERLAP."""
    w, o = capped_world(lib, world_factory)
    L = lots(lib, w)
    ht = hit_ticks(lib, w)
    scan = cap_scan(lib, w, L)
    edge = sorted(c for c, (ni, nr) in scan.items() if ni == 0 and nr >= 1 and foot_walkable(lib, w, c))
    assert edge, "premise: no spot with lots only in the ring at the cap"
    rc = place(lib, w, edge[0])
    dump("T6d-ii", n_lots=len(L), cap=OM_LOT_CAP, cell=edge[0], counts=scan[edge[0]], rc=rc)
    assert rc == E1E_FULL, f"a footprint with lots only in the ring at the cap returned {rc}, expected E1E_FULL ({E1E_FULL}); E1E_OVERLAP is {E1E_OVERLAP}"
    assert lots(lib, w) == L and hit_ticks(lib, w) == ht, "a refusal at the cap changed the table"


def test_at_the_cap_clearing_one_natural_lot_makes_room_for_the_placed_one(lib, world_factory):
    """T6e, gap full (a), the boundary: at OM_LOT_CAP a footprint with exactly one natural lot under it gives cleared = 1 and
    n_lots - 1 + 1 = OM_LOT_CAP, not above the cap: accepted, the table stays at OM_LOT_CAP, that lot is gone and the placed lot
    is there. Red on the built tree: E1E_OVERLAP."""
    w, o = capped_world(lib, world_factory)
    L = lots(lib, w)
    scan = cap_scan(lib, w, L)
    one = sorted(c for c, (ni, nr) in scan.items() if ni == 1 and foot_walkable(lib, w, c))
    assert one, "premise: no walkable footprint holds exactly one natural lot at the cap"
    c = one[0]
    victim = L[inside(L, c)[0]]
    dump("T6e", n_lots=len(L), cap=OM_LOT_CAP, cell=c, victim=victim)
    rc = place(lib, w, c)
    assert rc == E1E_OK, f"at the cap a footprint holding one natural lot returned {rc} (cleared 1, room for 1; E1E_FULL is {E1E_FULL})"
    after = lots(lib, w)
    assert len(after) == OM_LOT_CAP and victim[0] not in {l[0] for l in after}, "the cleared lot is still in the table or the count moved"
    assert [l for l in after if l[5] >= 0 and cell_of(l) == c], "the placed lot is not in the table"


# ------------------------------------------------------------------------------------------------ determinism

def test_the_clear_is_deterministic(lib, world_factory):
    """T7, Determinism is a contract: two worlds, same seed, same steps, same commands (a placement over the town, a second far
    placement, steps between) give identical lot tables, identical om_world_checksum_full (and sections) and identical save
    bytes (the per-process world serial masked, as test_VG_W_w1_planner.py does) after the placement and 100 more steps.
    Red on the built tree: the placement over the town is refused."""
    runs = []
    first = None
    for _ in range(2):
        w, o = grown(lib, world_factory)
        if first is None:
            first, _p = pick_centre(lib, world_factory, w, o)
        assert place(lib, w, first) == E1E_OK, "R-193-03: placement over natural lots refused"
        steps(lib, w, 40)
        assert place(lib, w, (o[0] + 60, o[1])) == E1E_OK, "control: the far placement was refused"
        steps(lib, w, 100)
        runs.append((lots(lib, w), hit_ticks(lib, w), checksum(lib, w), masked_save(lib, w)))
    assert runs[0][0] == runs[1][0] and runs[0][1] == runs[1][1], "the lot tables or lot_hit_tick differ between two identical runs"
    assert runs[0][2] == runs[1][2], f"om_world_checksum_full differs: {runs[0][2]} vs {runs[1][2]}"
    assert runs[0][3] == runs[1][3], "the save bytes differ between two identical runs"
