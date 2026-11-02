"""F1 (A7 sim-step fix 1, architect rulings 2 Addendum 3 A5/A6; profile docs/northstar/plans/
2026-10-01-a7-sim-profile.md): om_fog_faction_sees (csrc/fog.c, B11) searches observers of the
queried faction only, through a read-only per-faction grid accessor added to csrc/unit.c (B10).

THE ACCESSOR (internal, csrc/om_internal.h next to om_grid_query_circle / om_grid_iter; NOT a
public contract: no ouroboros_sim.h, signatures.toml, symbol_modules.toml or conftest bind change,
so there is no push/F1-contract branch). Two functions, same matching rule as the unfiltered
grid (a living unit, hp > 0, matches when dx*dx + dy*dy <= r*r at the position unit.c caches;
dead units are not indexed, revived units are):

    uint32_t om_grid_query_circle_faction(om_world *w, int32_t faction, double x, double y,
                                          double r, uint32_t *out_ids, uint32_t max);
    void     om_grid_iter_begin_faction(om_grid_iter *it, om_world *w, int32_t faction,
                                        double x, double y, double r);   /* then om_grid_iter_next */

Contract the tests below pin:
- query: writes the ids of exactly the units of `faction` inside the circle, ascending id (the
  all-pairs order, same as om_grid_query_circle), the lowest `max` when more match, and returns
  the total match count (above `max` means truncated). Unknown or negative faction: returns 0.
- iterator: yields exactly that same set once each, then 0. Order is deterministic (identical
  worlds give identical sequences) but NOT specified to be id order, exactly as om_grid_iter.
  The grid must not change while one is live. The om_grid_iter struct may grow: these tests give
  it a 256-byte buffer, never its C layout.
- the existing om_grid_query_circle, om_grid_iter_* and the nearest-hostile search in unit.c
  (the (d2, id) tie-break and the OM_TIE_SCAN_WINDOW fallback to the ordered scan) are unchanged.
  They are pinned by the 400-tick combat goldens below (units fight, so target choice feeds the
  state hash) and by the equidistant-target test.

THE OLD RULE (what fog.c computes, quoted so the Python reference is exact). om_player_can_see_unit(
w, p, u): false if u has no faction (faction < 0); true if u is faction p; true if the player-fog
switch was explicitly turned off (these scenes never touch it); else om_fog_faction_sees(w, p, u).
om_fog_faction_sees(w, p, u) is an any-of over the grid candidates within om_fog_world_bound of u
(max sensor radius times elevation slack, about 800 in these scenes) that are of faction p, of
om_unit_can_see(w, o, u). om_unit_can_see is false unless the observer is alive, both factions
are >= 0, the cross-layer factor is > 0, dist(o, u) <= effective radius(o) * factor and no cover
blocks the line. The reference below therefore computes, per unit u, any(om_unit_can_see(o, u)
for live o of faction p within REF_PREFILTER of u), REF_PREFILTER (2000) being a Python-side
distance prefilter larger than every sensor radius in these scenes (RAIDER 800, no elevation).

Groups:
1. accessor isolation (RED on main: the symbols do not exist).
2. equivalence (GREEN on main, must stay green): the per-unit answers and the whole `visible[]`
   list of the tactical frame (om_pipe.c builds it as ids in om_unit_id_at order filtered by
   om_player_can_see_unit(player), reproduced here) equal the OLD reference, seeded clash and
   spread scenes at 100, 1,000 and 5,000 units, some units dead.
3. positive control: altered references (wrong faction filter, no range limit) must differ.
4. golden: unit-state hash + om_world_checksum + visible[] hash after 400 ticks (GREEN on main).
5. the skip observation (RED on main): a probe build wraps om_grid_iter_next and records every
   candidate id fog.c walks while answering the player's visible[] queries. A wrong-faction row
   must never be returned to the observer search.
"""
import ctypes
import hashlib
import struct
import subprocess

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMFeature,
    REPO_ROOT,
    _bind_generated,
    _configure_common,
    _world_factory_for,
    set_edge,
    set_faction,
    set_owner,
)

RAIDER = 0
PLAYER_FAC = 0
ENEMY_FAC = 1
DEFENSIVE_STAND = 0
OM_MACRO_ADVANCE = 0
OM_MACRO_MOD_CAUTIOUS = 0
REF_PREFILTER = 2000.0
W = ctypes.c_void_p


def _world(lib, factory, seed):
    w = factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    lib.om_mission_setup(w, 0, DEFENSIVE_STAND, 0)
    lib.om_mission_set_phase(w, 1)
    return w


class _Xorshift:
    def __init__(self, seed):
        self.s = (seed * 2654435761 + 88172645463325252) & 0xFFFFFFFFFFFFFFFF

    def next(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFFFFFFFFFF
        s ^= s >> 7
        s ^= (s << 17) & 0xFFFFFFFFFFFFFFFF
        self.s = s
        return s

    def unit(self):
        return (self.next() >> 11) / float(1 << 53)


def _all_ids(lib, w):
    out = []
    total = lib.om_unit_count(w)
    i = 0
    while len(out) < total:
        uid = lib.om_unit_id_at(w, i)
        i += 1
        if uid:
            out.append(uid)
    return out


def _build_scene(lib, w, kind, n, seed):
    """clash: two touching blocks (one per faction), so most units see enemies. spread:
    uniform scatter at constant density (about 8 units per sensor circle), factions at
    random, so visibility is partial. Every 20th unit is killed (hp 0)."""
    rng = _Xorshift(seed)
    ids = []
    if kind == "clash":
        half = n // 2
        cols = max(1, int(half ** 0.5))
        rows = (half + cols - 1) // cols
        for fac, oy in ((ENEMY_FAC, 6000.0), (PLAYER_FAC, 6000.0 - rows * 40.0 - 200.0)):
            for i in range(half):
                x = 6000.0 + (i % cols) * 40.0 + rng.unit() * 10.0
                y = oy + (i // cols) * 40.0 + rng.unit() * 10.0
                ids.append(lib.om_unit_spawn(w, RAIDER, fac, x, y, 0))
    else:
        side = 500.0 * (n ** 0.5)
        for _ in range(n):
            fac = PLAYER_FAC if rng.next() & 1 else ENEMY_FAC
            ids.append(lib.om_unit_spawn(w, RAIDER, fac, 1000.0 + rng.unit() * side,
                                         1000.0 + rng.unit() * side, 0))
    assert all(ids), f"{kind} n={n}: a spawn failed (map or unit cap)"
    for k, uid in enumerate(ids):
        if k % 20 == 7:
            lib.om_unit_set_hp(w, uid, 0.0)
    return ids


# ---- the OLD answer, as a Python reference over ctypes (do not "improve") -------------

def _snapshot(lib, w):
    ids = _all_ids(lib, w)
    pos = {}
    fac = {}
    for u in ids:
        pos[u] = lib.om_unit_get_pos(w, u)
        fac[u] = lib.om_unit_get_faction(w, u)
    return ids, pos, fac


def _bucket(pos, members):
    cells = {}
    for u in members:
        x, y = pos[u]
        cells.setdefault((int(x // REF_PREFILTER), int(y // REF_PREFILTER)), []).append(u)
    return cells


def reference_visible(lib, w, player, mode="old"):
    """Ids visible to `player` in om_unit_id_at order. mode: old (reference), wrong_faction
    (observers are every faction EXCEPT the player's), no_range (any live observer of the
    player faction anywhere sees everything)."""
    ids, pos, fac = _snapshot(lib, w)
    if mode == "wrong_faction":
        obs = [u for u in ids if fac[u] >= 0 and fac[u] != player]
    else:
        obs = [u for u in ids if fac[u] == player]
    live_obs = [u for u in obs if lib.om_unit_alive(w, u)]
    cells = _bucket(pos, live_obs)
    out = []
    for u in ids:
        if fac[u] < 0:
            continue
        if fac[u] == player:
            out.append(u)
            continue
        if mode == "no_range":
            if live_obs:
                out.append(u)
            continue
        x, y = pos[u]
        cx, cy = int(x // REF_PREFILTER), int(y // REF_PREFILTER)
        seen = False
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for o in cells.get((gx, gy), ()):
                    ox, oy = pos[o]
                    if (ox - x) ** 2 + (oy - y) ** 2 > REF_PREFILTER ** 2:
                        continue
                    if lib.om_unit_can_see(w, o, u):
                        seen = True
                        break
                if seen:
                    break
            if seen:
                break
        if seen:
            out.append(u)
    return out


def library_visible(lib, w, player):
    """The tactical frame's visible[] loop (csrc/pipe/om_pipe.c): unit ids in om_unit_id_at
    order, kept when om_player_can_see_unit(player, id)."""
    return [u for u in _all_ids(lib, w) if lib.om_player_can_see_unit(w, player, u)]


SCENE_KINDS = ("clash", "spread")
COUNTS = (100, 1000, 5000)


@pytest.mark.parametrize("n", COUNTS)
@pytest.mark.parametrize("kind", SCENE_KINDS)
def test_F1_equivalence_visible_list_matches_old_reference(lib, world_factory, kind, n):
    """The whole visible[] list for the player's faction equals the OLD any-of-observers
    reference, in a clash and a spread scene, at every unit count, seeds 1 and 2."""
    for seed in (1, 2):
        w = _world(lib, world_factory, seed)
        _build_scene(lib, w, kind, n, seed)
        player = lib.om_player_faction(w)
        assert player == PLAYER_FAC, "scene guard: player faction"
        got = library_visible(lib, w, player)
        want = reference_visible(lib, w, player)
        assert got == want, (
            f"{kind} n={n} seed={seed}: visible[] differs from the old reference "
            f"(library {len(got)} ids, reference {len(want)}; "
            f"only-library {sorted(set(got) - set(want))[:5]}, "
            f"only-reference {sorted(set(want) - set(got))[:5]})"
        )
        own = sum(1 for u in want if lib.om_unit_get_faction(w, u) == player)
        enemy_seen = len(want) - own
        enemy_total = sum(1 for u in _all_ids(lib, w) if lib.om_unit_get_faction(w, u) == ENEMY_FAC)
        hides_some = enemy_seen < enemy_total or kind == "clash"
        assert enemy_seen > 0 and hides_some, (
            f"scene guard {kind} n={n} seed={seed}: enemy units seen {enemy_seen} of "
            f"{enemy_total}; the scene must show some (spread: and hide some)"
        )


@pytest.mark.parametrize("ticks", [1, 40])
@pytest.mark.parametrize("kind", SCENE_KINDS)
def test_F1_equivalence_after_movement(lib, world_factory, kind, ticks):
    """Same equivalence after units have moved and fought for a few ticks (the grid is
    rebuilt each tick; the any-of answer must still be the reference's)."""
    w = _world(lib, world_factory, 1)
    _build_scene(lib, w, kind, 300, 1)
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    lib.om_tactical_tick_to(w, ticks)
    player = lib.om_player_faction(w)
    assert library_visible(lib, w, player) == reference_visible(lib, w, player), (
        f"{kind} after {ticks} ticks: visible[] differs from the old reference")


@pytest.mark.parametrize("mode", ["wrong_faction", "no_range"])
def test_F1_positive_control_altered_reference_is_caught(lib, world_factory, mode):
    """An altered reference (observers of the wrong faction, or no range limit) must differ
    from the library in at least one scene; otherwise the equivalence test above could not
    have caught a wrong per-faction search."""
    differing = 0
    for kind in SCENE_KINDS:
        w = _world(lib, world_factory, 1)
        _build_scene(lib, w, kind, 300, 1)
        player = lib.om_player_faction(w)
        if library_visible(lib, w, player) != reference_visible(lib, w, player, mode):
            differing += 1
    assert differing > 0, f"altered reference '{mode}' agreed with the library in every scene"


# ---- golden: full run after 400 ticks, recorded on main before the change ------------

def _state_hash(lib, w):
    h = hashlib.sha256()
    for uid in _all_ids(lib, w):
        x, y = lib.om_unit_get_pos(w, uid)
        h.update(struct.pack("<IddddI", uid, x, y, lib.om_unit_get_hp(w, uid), 0.0,
                             lib.om_unit_alive(w, uid)))
    h.update(struct.pack("<Q", lib.om_world_checksum(w)))
    return h.hexdigest()


def _visible_hash(lib, w):
    vis = library_visible(lib, w, lib.om_player_faction(w))
    return hashlib.sha256(struct.pack("<%dI" % len(vis), *vis)).hexdigest()


# Re-recorded day20 on push/pp-c3-land (parity wave, leash anchor, give-up rule moved target choice and paths on purpose; baseline_hashes.json still green with both switches at 0; was: A155 to A159 recorded).
# Re-recorded day21 on push/pp-settle-gold (A184 collision settle epsilon 0.1 wu ends the push sequence early; was: day20 pp-c3-land recorded).
# Re-recorded day23 on push/pa-land (A199: an attack-mover no longer walks toward an enemy it merely sees, R-087-04; was: day21 pp-settle-gold recorded). TD-PP-A199-rerecord.
GOLDEN = {
    "clash": ("e10663fd10109b51c6e14b44dfe0828a0031580bb15ca02fe52d1a55c56666eb",
              "740858b42c174da068bb0ad94b10fddef168a6b370c8b6d5f99b51e9e89b57df"),
    "spread": ("b98bdb02c701ee3a875e5566eef0b0580764186436f916411b7437da47856e61",
               "4b28a8fba6ffbcd30bf97182d8cd4ded79232b2dd749fc664fab17d831f274db"),
}


def _full_run(lib, w, kind):
    if kind == "spread":
        # PP: scene is off canvas; baseline routing (A147 option c', test-defect)
        assert lib.om_tactical_set_param(w, 1, 0.0) == 0  # OM_TP_ROUTE_AROUND_TERRAIN
    _build_scene(lib, w, kind, 600, 7)
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    lib.om_tactical_tick_to(w, 400)
    return _state_hash(lib, w), _visible_hash(lib, w)


@pytest.mark.parametrize("kind", SCENE_KINDS)
def test_F1_full_run_state_and_visible_are_byte_identical_to_golden(lib, world_factory, kind):
    """Unit-state hash (positions, hp, alive, om_world_checksum) and the visible[] hash after
    400 ticks of a 600-unit scene (units fight, so nearest-hostile choice feeds the hash)."""
    got = _full_run(lib, _world(lib, world_factory, 1), kind)
    again = _full_run(lib, _world(lib, world_factory, 1), kind)
    assert got == again, "run is not even self-deterministic"
    assert got == GOLDEN[kind], f"{kind}: (state, visible) hashes {got} != golden {GOLDEN[kind]}"


def test_F1_equidistant_targets_still_break_ties_by_lowest_id(lib, world_factory):
    """Two enemies at exactly the same distance: om_unit_acquire_target picks the lower id,
    whichever side of the observer it stands on (the (d, id) tie-break must stay intact)."""
    for swap in (False, True):
        w = _world(lib, world_factory, 1)
        obs = lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, 3000.0, 3000.0, 0)
        a_pos, b_pos = ((3100.0, 3000.0), (3000.0, 3100.0))
        if swap:
            a_pos, b_pos = b_pos, a_pos
        a = lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, a_pos[0], a_pos[1], 0)
        b = lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, b_pos[0], b_pos[1], 0)
        assert a < b
        lib.om_unit_acquire_target(w, obs)
        assert lib.om_unit_get_target(w, obs) == a, f"swap={swap}: tie did not go to the lower id"


# ---- accessor isolation (RED on main: the symbols do not exist) -----------------------

ITER_BUF = 256


def _bind_accessor(lib):
    for name in ("om_grid_query_circle_faction", "om_grid_iter_begin_faction"):
        assert hasattr(lib, name), f"{name} missing from libouroboros (F1 accessor in csrc/unit.c)"
    lib.om_grid_query_circle_faction.argtypes = [W, ctypes.c_int32, ctypes.c_double, ctypes.c_double,
                                                 ctypes.c_double, ctypes.POINTER(ctypes.c_uint32),
                                                 ctypes.c_uint32]
    lib.om_grid_query_circle_faction.restype = ctypes.c_uint32
    lib.om_grid_query_circle.argtypes = [W, ctypes.c_double, ctypes.c_double, ctypes.c_double,
                                         ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    lib.om_grid_query_circle.restype = ctypes.c_uint32
    lib.om_grid_iter_begin_faction.argtypes = [ctypes.c_void_p, W, ctypes.c_int32, ctypes.c_double,
                                               ctypes.c_double, ctypes.c_double]
    lib.om_grid_iter_begin_faction.restype = None
    lib.om_grid_iter_next.argtypes = [ctypes.c_void_p]
    lib.om_grid_iter_next.restype = ctypes.c_uint32


def _query(lib, w, faction, x, y, r, cap):
    buf = (ctypes.c_uint32 * max(cap, 1))()
    total = lib.om_grid_query_circle_faction(w, faction, x, y, r, buf, cap)
    return total, list(buf)[:min(total, cap)]


def _iterate(lib, w, faction, x, y, r):
    it = ctypes.create_string_buffer(ITER_BUF)
    lib.om_grid_iter_begin_faction(it, w, faction, x, y, r)
    out = []
    while len(out) < 100000:
        u = lib.om_grid_iter_next(it)
        if not u:
            return out
        out.append(u)
    raise AssertionError("iterator did not terminate")


def _iso_world(lib, factory):
    """300 units of two factions scattered over 3000 x 3000, two exactly on a circle edge,
    some dead, some teleported, one revived."""
    w = _world(lib, factory, 5)
    rng = _Xorshift(5)
    ids = []
    for _ in range(300):
        fac = PLAYER_FAC if rng.next() & 1 else ENEMY_FAC
        ids.append(lib.om_unit_spawn(w, RAIDER, fac, 500.0 + rng.unit() * 3000.0,
                                     500.0 + rng.unit() * 3000.0, 0))
    edge_a = lib.om_unit_spawn(w, RAIDER, PLAYER_FAC, 2300.0, 2000.0, 0)   # dx = +300 exactly
    edge_b = lib.om_unit_spawn(w, RAIDER, ENEMY_FAC, 2000.0, 1700.0, 0)    # dy = -300 exactly
    ids += [edge_a, edge_b]
    for k in range(0, 300, 11):
        lib.om_unit_set_hp(w, ids[k], 0.0)
    lib.om_unit_set_hp(w, ids[11], 10.0)
    for k in range(3, 300, 17):
        lib.om_unit_teleport(w, ids[k], 500.0 + rng.unit() * 3000.0, 500.0 + rng.unit() * 3000.0, 0)
    return w, ids


CIRCLES = [(2000.0, 2000.0, 300.0), (1500.0, 1500.0, 150.0), (2500.0, 2500.0, 800.0),
           (2000.0, 2000.0, 0.0), (1000.0, 3000.0, 400.0), (2000.0, 2000.0, 1.0e9),
           (-9000.0, -9000.0, 500.0), (3300.0, 800.0, 1000.0)]


def _expected(lib, w, ids, faction, x, y, r):
    out = []
    for u in sorted(ids):
        if lib.om_unit_get_faction(w, u) != faction or not lib.om_unit_alive(w, u):
            continue
        ux, uy = lib.om_unit_get_pos(w, u)
        if (ux - x) ** 2 + (uy - y) ** 2 <= r * r:
            out.append(u)
    return out


@pytest.mark.parametrize("faction", [PLAYER_FAC, ENEMY_FAC, 7, -1])
def test_F1_accessor_query_returns_exactly_that_factions_units_ascending(lib, world_factory, faction):
    _bind_accessor(lib)
    w, ids = _iso_world(lib, world_factory)
    nonempty = 0
    for (x, y, r) in CIRCLES:
        want = _expected(lib, w, ids, faction, x, y, r)
        total, got = _query(lib, w, faction, x, y, r, len(ids) + 5)
        assert total == len(want) and got == want, (
            f"faction {faction} circle ({x},{y},{r}): got {got[:6]} (total {total}), expected {want[:6]} "
            f"(total {len(want)})")
        nonempty += bool(want)
    if faction in (PLAYER_FAC, ENEMY_FAC):
        assert nonempty >= 6, "scene guard: most circles must contain units of the faction"
        edge = _expected(lib, w, ids, faction, 2000.0, 2000.0, 300.0)
        assert any(lib.om_unit_get_pos(w, u) in ((2300.0, 2000.0), (2000.0, 1700.0)) for u in edge), \
            "scene guard: the exact-radius edge unit must be matched (<= r*r)"


def test_F1_accessor_query_truncates_like_the_unfiltered_query(lib, world_factory):
    """A small buffer gets the lowest ids and the full total is still returned."""
    _bind_accessor(lib)
    w, ids = _iso_world(lib, world_factory)
    want = _expected(lib, w, ids, PLAYER_FAC, 2000.0, 2000.0, 1.0e9)
    assert len(want) > 10
    total, got = _query(lib, w, PLAYER_FAC, 2000.0, 2000.0, 1.0e9, 10)
    assert total == len(want) and got == want[:10]


def test_F1_accessor_union_over_factions_equals_unfiltered_query(lib, world_factory):
    """Per-faction results merged equal the existing om_grid_query_circle, which must be unchanged."""
    _bind_accessor(lib)
    w, ids = _iso_world(lib, world_factory)
    for (x, y, r) in CIRCLES:
        merged = sorted(_query(lib, w, PLAYER_FAC, x, y, r, len(ids))[1] +
                        _query(lib, w, ENEMY_FAC, x, y, r, len(ids))[1])
        buf = (ctypes.c_uint32 * len(ids))()
        total = lib.om_grid_query_circle(w, x, y, r, buf, len(ids))
        assert list(buf)[:total] == merged, f"circle ({x},{y},{r}): union differs from om_grid_query_circle"


def test_F1_accessor_iterator_yields_the_same_set_in_a_deterministic_order(lib, world_factory):
    _bind_accessor(lib)
    w1, ids1 = _iso_world(lib, world_factory)
    w2, ids2 = _iso_world(lib, world_factory)
    for faction in (PLAYER_FAC, ENEMY_FAC, 7):
        for (x, y, r) in CIRCLES:
            seq1 = _iterate(lib, w1, faction, x, y, r)
            seq2 = _iterate(lib, w2, faction, x, y, r)
            assert seq1 == seq2, f"faction {faction} circle ({x},{y},{r}): iteration order is not deterministic"
            assert len(seq1) == len(set(seq1)), "iterator yielded a unit twice"
            assert sorted(seq1) == _expected(lib, w1, ids1, faction, x, y, r), (
                f"faction {faction} circle ({x},{y},{r}): iterator set differs from the faction's units in range")


def test_F1_accessor_follows_ticks_deaths_and_revivals(lib, world_factory):
    """After tactical ticks (grid rebuilt, units die in combat) the accessor still equals the
    faction's members of the unfiltered grid query."""
    _bind_accessor(lib)
    w, ids = _iso_world(lib, world_factory)
    lib.om_macro_set_state(w, 0, OM_MACRO_ADVANCE, OM_MACRO_MOD_CAUTIOUS)
    lib.om_tactical_tick_to(w, 40)
    buf = (ctypes.c_uint32 * len(ids))()
    for (x, y, r) in CIRCLES:
        total = lib.om_grid_query_circle(w, x, y, r, buf, len(ids))
        everyone = list(buf)[:total]
        for faction in (PLAYER_FAC, ENEMY_FAC):
            want = [u for u in everyone if lib.om_unit_get_faction(w, u) == faction]
            assert _query(lib, w, faction, x, y, r, len(ids))[1] == want
            assert sorted(_iterate(lib, w, faction, x, y, r)) == want


# ---- the skip: which candidates does fog.c's observer search walk? --------------------

_SHIM = r"""
#include <stdint.h>
uint32_t __real_om_grid_iter_next(void *it);
static unsigned hits[65536];
uint32_t __wrap_om_grid_iter_next(void *it) {
    uint32_t id = __real_om_grid_iter_next(it);
    if (id && id < 65536) hits[id]++;
    return id;
}
unsigned om_f1_hits(uint32_t id) { return id < 65536 ? hits[id] : 0; }
void om_f1_reset(void) { for (int i = 0; i < 65536; i++) hits[i] = 0; }
"""


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    d = tmp_path_factory.mktemp("f1probe")
    shim = d / "shim.c"
    shim.write_text(_SHIM)
    so = d / "libouroboros_f1probe.so"
    srcs = sorted(str(p) for p in (REPO_ROOT / "csrc").glob("*.c"))
    cmd = ["cc", "-std=c11", "-Wall", "-Wextra", "-I" + str(REPO_ROOT / "csrc"), "-fPIC", "-O2",
           "-fno-fast-math", "-ffp-contract=off", "-fexcess-precision=standard", "-msse2",
           "-mfpmath=sse", "-fno-math-errno", "-shared", "-Wl,--wrap=om_grid_iter_next",
           "-o", str(so)] + srcs + [str(shim)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, "probe build failed:\n" + r.stderr
    handle = ctypes.CDLL(str(so))
    _configure_common(handle)
    _bind_generated(handle)
    handle.om_f1_hits.restype = ctypes.c_uint
    handle.om_f1_hits.argtypes = [ctypes.c_uint32]
    handle.om_f1_reset.restype = None
    handle.om_f1_reset.argtypes = []
    make, created = _world_factory_for(handle, None)
    yield handle, make
    for w in created:
        handle.om_world_free(w)


def _walk_counts(handle, w, player):
    own = wrong = 0
    for u in _all_ids(handle, w):
        h = handle.om_f1_hits(u)
        if not h:
            continue
        if handle.om_unit_get_faction(w, u) == player:
            own += h
        else:
            wrong += h
    return own, wrong


def test_F1_observer_search_never_walks_wrong_faction_candidates(probe):
    """Answer the player's visible[] queries for a clash scene (every enemy unit asks 'does
    the player's faction see me?'). Count every candidate om_grid_iter_next hands to fog.c by
    faction. Only the player's own units can be observers, so zero enemy rows may be walked
    (the profile measured about 660 candidates per query, most of them the wrong faction)."""
    handle, make = probe
    w = _world(handle, make, 1)
    _build_scene(handle, w, "clash", 300, 1)
    player = handle.om_player_faction(w)
    ids = _all_ids(handle, w)
    handle.om_f1_reset()
    for u in ids:
        handle.om_player_can_see_unit(w, player, u)
    own, wrong = _walk_counts(handle, w, player)
    assert wrong == 0, (
        f"fog.c's observer search was handed {wrong} wrong-faction candidates "
        f"(and {own} own-faction ones) while answering the player's visible[] queries")


def test_F1_probe_positive_control_counts_candidates_by_faction(probe):
    """Control for the counter: om_unit_acquire_target (fog.c, unfiltered candidate
    walk, called across translation units so the wrap sees it) hands back rows of both factions, so the counter would register wrong-faction rows if
    fog.c walked them. Also the real visible[] queries must be counted as own-faction walks
    or nothing (the counter reaches fog.c's calls only if it walks the grid at all)."""
    handle, make = probe
    w = _world(handle, make, 1)
    _build_scene(handle, w, "clash", 300, 1)
    player = handle.om_player_faction(w)
    handle.om_f1_reset()
    for u in [u for u in _all_ids(handle, w) if handle.om_unit_get_faction(w, u) == player][:40]:
        handle.om_unit_acquire_target(w, u)  # fog.c walks every faction's rows here
    own, wrong = _walk_counts(handle, w, player)
    assert own > 0 and wrong > 0, "counter did not see both factions through the unfiltered walk"
    handle.om_f1_reset()
    for u in _all_ids(handle, w):
        handle.om_player_can_see_unit(w, player, u)
    own, _wrong = _walk_counts(handle, w, player)
    assert own > 0, "the observer search walked no own-faction candidates at all (scene or counter broken)"
