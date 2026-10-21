# Rule pins: R-126-02@2361a1
"""Visible-game lane E1, piece VG-E-prodslot: a produced unit is placed in the first free slot of the structure's 30 wu lattice
(csrc/tactical_support.c om_structure_tick_production and its driver, csrc/mission.c om_mission_production_slot). Tests first,
fenced: builders never edit this file. Proves R-126-02 (as GAP 3 rewrites it), TD-VG-E-29 (Westley's rule change of 2026-10-12)
and FINDING-production-stack.

THE BIBLE HAS NO SENTENCE ABOUT THE SLOT LATTICE. What is proved is exactly these texts (method rev 3, quoted word for word):

(1) The spec paragraph, docs/northstar/plans/2026-10-07-visible-game-spec.md line 362 (origin/main 73c4ce84):

**VG-E-prodslot (lane E1, after VG-CONTRACT-E7 lands; owner `csrc/tactical_support.c` production spawn lines, `csrc/mission.c` slot helper, `csrc/om_internal.h` one prototype plus its signatures row and EXPECTED_MODULE line, `tests/csim/test_VG_E_prodslot.py`).** `[P csrc/tactical_support.c:546-547: a produced unit lands at a random angle and a distance uniform in [0, OM_REINFORCEMENT_CAPTURE_RADIUS / 2 = 150 wu) from the structure, no occupancy check]` `[P csrc/unit.c:2980: om_unit_spawn checks terrain only]` `[P csrc/mission.c:2350, 2470: mission start uses a 30 wu slot lattice with used-slot checks; production never calls it]` `FINDING-production-stack`. Production places each new unit at the first free slot, in a fixed scan order, of a lattice centred on the structure at the spacing mission start uses (2 x OM_UNIT_COLLISION_RADIUS, `mission.c:2470`): slots P + (i s, j s), the origin excluded, rings r = max(|i|, |j|) scanned outward and row-major within a ring (not nearest-first past ring 3, by design), a slot counting when its distance from the structure is at most 150 wu (half the capture radius, inclusive) and free when no live unit stands strictly within one spacing of it (squared distances, no epsilon) and the terrain would accept a spawn there; helper `int om_mission_production_slot(const om_world *w, uint32_t structure, double *out_x, double *out_y)` in `mission.c`, declared in `om_internal.h`, bound for the isolation test through `tests/csim/conftest.py`; no free slot within 150 wu delays production one tick (the structure keeps its timer). Deterministic: scan order fixed, no RNG draw consumed (the two RNG draws at :546-547 are removed, so the RNG stream changes: goldens with production move once under `TD-VG-E-29`, rule-changed by Westley 2026-10-12, old and new named; goldens without production must not move, the Goldens step verifies). The Docs step rewrites R-126-02, E-15 line 184, ALG-75's spawn clause and the closed register row Q-126-02 to the lattice rule (texts in the args gap g3), and the eight tests that cite R-126-02 or last_spawn_distance get the new rule in their docstrings, assertions untouched (all bound the spawn at 150 wu inclusive). A golden both known-red under TD-VG-E-26 and moved here keeps its known-red line with the reason extended to both rows until startforce lands. Tests first: ten productions from one structure yield ten units pairwise at least 30 wu apart (red today: paste the first pair under 30); a structure with every slot within 150 wu occupied delays one tick and places when a slot frees; a save round trip mid-sequence gives the same positions; control: mission-start spacing unchanged.

(2) R-126-02 as the bible has it TODAY (docs/bible/epics/E-15-reinforcement-supply-and-hazards.md line 35):

- R-126-02  Given a held structure with a chosen unit type, When its production timer reaches 30 s × (that type's power / 100), Then one unit of that type spawns within half the capture radius of the structure on the structure's layer (position from two world-stream draws, angle then distance; never from any other generator) and the timer subtracts the interval.

    The Docs step rewrites it (GAP 3 ruling, Architect) to: "R-126-02  Given a held structure with a chosen unit type, When its
    production timer reaches 30 s x (that type's power / 100), Then one unit of that type spawns at the first free slot of the
    structure's spawn lattice (a grid at twice the unit collision radius centred on the structure, scanned ring by ring outward
    in a fixed order, within half the capture radius; a slot is free when no live unit stands within one spacing of it; no free
    slot delays production one tick) on the structure's layer, with no random draw, and the timer subtracts the interval
    (Westley 2026-10-12, TD-VG-E-29)." The old draw-order sentence (angle then distance) is retired by that rewrite.

(3) Westley's rule change of 2026-10-12, ledger row TD-VG-E-29 (docs/northstar/plans/push_ledger_2026-09-22.md line 1064), first
    sentence: "Production places each new unit in the nearest free slot of the 30 wu lattice; the two RNG draws at :541-545 are removed, so the RNG stream moves." (The clerk's rewrite approved in the pins reads "first free slot in scan order of the 30 wu
    lattice"; the scan order is the G2 ruling.)

(4) FINDING-production-stack (ledger line 1066): "A produced unit lands at a random angle and a distance uniform in [0, 150 wu) from the structure, with no occupancy check: `om_unit_spawn` (`unit.c:929-978`) checks terrain only, and production never calls the mission-start slot lattice. Units stack on the structure. Fix: VG-E-prodslot (after VG-CONTRACT-E7), TD-VG-E-29." Fix: VG-E-prodslot, TD-VG-E-29.

(5) The gap rulings, as the Architect gave them (the ruling wins over the spec sentence it amends):
  G1  int om_mission_production_slot(const om_world *w, uint32_t structure, double *out_x, double *out_y) in csrc/mission.c;
      returns 1 and the slot's world position, or 0 when no slot within the bound is free (the caller delays one tick, timer kept).
  G2  Origin the structure's point P; axes world x and y; spacing s = 2 x OM_UNIT_COLLISION_RADIUS (mission.c:2470); slots
      P + (i s, j s), the slot (0, 0) excluded; ring r = max(|i|, |j|); scan order rings r = 1, 2, 3, ... outward, within a ring
      j (the y offset) outer from -r to r and i (the x offset) inner from -r to r, keeping the cells with max(|i|, |j|) == r;
      fixed order, not nearest-first past ring 3; bound i*i + j*j <= RING_MAX^2 with RING_MAX = 150 / 30 = 5 (80 slots), exact
      in integers, 150 wu inclusive; free = no live unit's position strictly within s of the slot (squared distances, no
      epsilon; a unit at exactly s does not block); a slot om_unit_spawn would refuse for the produced type is skipped.
  G5..G10 null actions (a): terrain not consulted beyond the refusal in G2 (tested as G2 states it); last_spawn_x/y hold the
      slot and last_spawn_distance its distance from the structure; a blocked tick changes nothing and the driver loop ends for
      the tick; every live unit of every faction on every layer occupies, every producing owner (>= 0) uses the rule; no shot.

Pins (Architect 2026-10-21): tolerance DRAFT-prodslot-test-tol 1e-6 (wu^2 on the pairwise check, wu on positions) lives in the
test only; the fixture structure stands on an integer point so P + i*s is exact; the isolation test of the helper is bound in
this file (tests/csim/conftest.py is not in this piece's test files; the same argtypes the conftest block gets).

NOT PROVED HERE (nobody states it): the "structure's point block" of the spec sentence is vacuous on a lattice that excludes
the origin and has spacing 30 (every slot is at least 30 wu from P, and strictly-less blocks nothing at exactly 30), so no test
can tell it apart; the spec's "nearest" is replaced by G2's "first in the fixed scan order" and tested as the latter.

Non-vacuous: the structure stands at (3000, 3000), 3000 wu inside the 16000 wu canvas edges (ring 5 reaches 150 wu) and
about 7000 wu from the filler's resting place; the fixture seeds (12, 13) have no enemy wave in 6100 ticks (dumped; seeds 9, 11,
17, 19 do and are not used), so only the fixture's own units exist. Every test says in its docstring why it is red today.

PREMISES, DUMPED from origin/main (73c4ce84, built; `make` and the pipe) 2026-10-21 by running this fixture (not invented):
Fixture (every test): tactical_world(seed) = 2 regions, DEFENSIVE_STAND mission set up, tactical phase, no composed units; structure
slot 0 re-initialised: unit type 0 (raider), power 100.0, owner 0 (player), position (3000.0, 3000.0); mission slots 1 and 2 made
neutral; production interval om_structure_production_interval_ticks(100.0) = 600 ticks; timer 0; one filler unit before the first
production: id 1, faction 1, type 1, at (100000.0, 100000.0). No terrain. Seeds 12 and 13.
Produced today (random placement), (unit id, tick it appeared, x, y at that tick, last_spawn_distance), type 0, faction 0:
  seed 12: (2, 600, 2927.433, 2998.187, 72.59) (3, 1200, 2860.982, 2976.142, 141.056) (4, 1800, 3131.949, 2972.169, 134.852)
           (5, 2400, 2973.474, 3124.196, 127.002) (6, 3000, 3012.458, 3007.964, 14.786) (7, 3600, 2990.815, 2852.353, 147.933)
           (8, 4200, 3017.065, 3065.945, 68.12) (9, 4800, 3053.032, 3059.136, 79.433) (10, 5400, 3119.769, 2969.554, 123.578)
           (11, 6000, 3134.856, 2937.53, 148.622); unit 10 appears 12.4577 wu from unit 4 (first pair under 30 in time order).
  seed 13: (2, 600, 2910.419, 3028.484, 94.004) (3, 1200, 3029.251, 2999.473, 29.256) (4, 1800, 3128.139, 2984.663, 129.054)
           (5, 2400, 2988.696, 2912.963, 87.768) (6, 3000, 3013.892, 3022.696, 26.61) (7, 3600, 2995.901, 2998.432, 4.389)
           (8, 4200, 3008.997, 3018.217, 20.318) (9, 4800, 3018.572, 3004.169, 19.034) (10, 5400, 3035.707, 3110.92, 116.53)
           (11, 6000, 2869.99, 2958.057, 136.613); unit 6 appears 27.8427 wu from unit 3 (first pair under 30).
  The sim's collision step pushes overlapping units apart over the following ticks: by tick 6000 today's ten units of both seeds
  stand >= 30 wu apart (29.99999999999969 at worst), so the end-of-run pair check is green today and only the read at the tick a
  unit appears (T1) and the one-support-tick fixture (T1b) are red.
Ten productions in one support tick today (timer set to 10 x 600, one om_tactical_step): seed 12 first pair under 30 is
  ids (5, 6) at (3034.250, 2974.790) and (3007.751, 2988.850), 29.9977 wu; seed 13 ids (6, 9) at (2979.019, 2987.571) and
  (3003.475, 3003.964), 29.4423 wu.
Terrain fixture: tactical_world(12) with roster type 0 set to walking, om_terrain_generate(w, 777, 16000, 16000), structure at
  (1000.0, 13100.0): 27 of the 80 lattice slots are refused for a walker by om_unit_spawn (scan indices 1, 2, 4, 6, 7, 10, 11, 21,
  22, 27, 28, 29, 30, 32, 43, 44, 51, 53, 54, 55, 56, 58, 60, 72, 76, 78, 79); a flyer (type 1, movement kind 0) is refused at none.
Mission start (C3): archetype 3, military 20.0 in region 0, seeds 7 and 11: 301 player units, first twelve at
  (11920,120) (11950,120) (11980,120) (11920,150) (11950,150) (11980,150) (11920,180) (11950,180) (11980,180) (11820,120) (11850,120)
  (11880,120); sha256 per seed in MS_SHA below.
"""
import ctypes
import hashlib
import math
import struct

import pytest

from conftest import (OMArchetype, OMEdge, OMFeature, OMTier, force_draws,
                      set_edge, set_faction, set_owner, set_region)
from b1_macro_scene import ENEMY_FAC, PLAYER_FAC, tactical_world

V = ctypes.c_void_p
P = ctypes.POINTER

# ---- numbers: the spec's two (30, 150), the G2 integer bound, fixture values ---------------------------------------
SPACING = 30.0          # spec: "the same 30 wu lattice"; 2.0 * OM_UNIT_COLLISION_RADIUS (om_constants.h:581 = 15, mission.c:2470)
BOUND = 150.0           # spec: "within 150 wu"; OM_REINFORCEMENT_CAPTURE_RADIUS / 2.0 (om_constants.h:630 = 300)
RING_MAX = 5            # G2: (OM_REINFORCEMENT_CAPTURE_RADIUS / 2) / SPACING, exact; a slot counts when i*i + j*j <= RING_MAX^2
N_SLOTS = 80            # G2: "5 today, 80 slots at ring 5" (the 81 integer points of the disc of radius 5, origin excluded)
TOL = 1e-6              # DRAFT-prodslot-test-tol (pin 6): wu^2 on the pairwise check, wu on positions; used in the test only
SQ = SPACING * SPACING
STRUCT = 0              # fixture structure slot (mission setup also places slots 0..2; 1 and 2 are made neutral below)
AT = (3000.0, 3000.0)   # fixture value: an integer point, so AT + i * SPACING is exact (pin 6); ring 5 stays inside the 16000 wu canvas
POWER = 100.0           # fixture value; interval = om_structure_production_interval_ticks(100.0) = 600 ticks (dumped below)
UTYPE = 0               # fixture value: roster type 0 (raider)
FILLER_TYPE = 1         # fixture value: the far unit that keeps om_tactical_step running (B14N pattern); a flyer so the terrain fixture accepts it
FAR = (100000.0, 100000.0)
SEEDS = (12, 13)        # fixture seeds: dumped 6100-tick runs of both show no enemy wave (seeds 9, 11, 17, 19 do), so only the fixture's units exist
TERRAIN_SEED = 777      # fixture value, om_terrain_generate(w, 777, 16000, 16000); the same call as the dump of the premises
AT_TERRAIN = (1000.0, 13100.0)  # fixture value: on that terrain 27 of the 80 slots are unwalkable or band 0 (premise dumped), slot index 1 and 2 among them
MOVE_WALKING = 1        # csrc/ouroboros_sim.h:1085

# ---- the independent oracle: the G2 lattice, computed here from integers --------------------------------------------


def scan_order():
    """G2: rings r = 1.. outward; within a ring j (y offset) outer from -r to r, i (x offset) inner from -r to r, only
    cells with max(|i|, |j|) == r; a slot counts when i*i + j*j <= RING_MAX^2. The origin (0, 0) is excluded."""
    out = []
    for r in range(1, RING_MAX + 1):
        for j in range(-r, r + 1):
            for i in range(-r, r + 1):
                if max(abs(i), abs(j)) == r and i * i + j * j <= RING_MAX * RING_MAX:
                    out.append((i, j))
    return out


ORDER = scan_order()


def slot_xy(at, ij):
    return (at[0] + ij[0] * SPACING, at[1] + ij[1] * SPACING)


def d2(a, b):
    return (a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1])


def free_slots(at, points, refused=()):
    """The G2 free rule, from positions only: a slot is free when no live unit's position is strictly within one
    spacing of it (squared distances, no epsilon), and it is not one the terrain refuses. In scan order."""
    return [ij for ij in ORDER if ij not in refused and all(d2(slot_xy(at, ij), p) >= SQ for p in points)]


def expected_sequence(at, points, k, refused=()):
    """The slots the first k productions take, each seeing the earlier ones as live units; fewer when blocked."""
    pts = list(points)
    got = []
    for _ in range(k):
        free = free_slots(at, pts, refused)
        if not free:
            break
        got.append(free[0])
        pts.append(slot_xy(at, free[0]))
    return got


def pairs_closer_than_spacing(points):
    """Every pair (a, b, d2) of points whose squared distance is below SPACING^2 (minus the DRAFT-prodslot-test-tol)."""
    bad = []
    for a in range(len(points)):
        for b in range(a + 1, len(points)):
            dd = d2(points[a], points[b])
            if dd < SQ - TOL:
                bad.append((a, b, dd))
    return bad


# ---- the fixture -----------------------------------------------------------------------------------------------------


def interval(lib):
    return lib.om_structure_production_interval_ticks(ctypes.c_double(POWER))


def alive(lib, w):
    ids = [lib.om_unit_id_at(w, k) for k in range(lib.om_unit_count(w))]
    return [u for u in ids if lib.om_unit_alive(w, u)]


def xy(lib, w, u):
    return (lib.om_unit_position_x(w, u), lib.om_unit_position_y(w, u))


def build(lib, world_factory, seed, owner=PLAYER_FAC, at=AT, utype=UTYPE, terrain=False):
    """tactical_world (mission set up, tactical phase), the two other mission structures made neutral, structure 0 held by
    `owner` at `at`, one far filler unit of the other faction so om_tactical_step runs."""
    w = tactical_world(lib, world_factory, seed=seed)
    if terrain:
        assert lib.om_roster_set_movement_kind(w, UTYPE, MOVE_WALKING) == 0
        assert lib.om_terrain_generate(w, TERRAIN_SEED, 16000.0, 16000.0) == 0
    for s in (1, 2):
        lib.om_structure_set_owner(w, s, -1)
    lib.om_structure_init(w, STRUCT, utype, ctypes.c_double(POWER))
    lib.om_structure_set_owner(w, STRUCT, owner)
    lib.om_structure_set_position(w, STRUCT, at[0], at[1])
    other = ENEMY_FAC if owner == PLAYER_FAC else PLAYER_FAC
    assert lib.om_unit_spawn(w, FILLER_TYPE, other, FAR[0], FAR[1], 0) != 0, "fixture: the filler unit was refused"
    return w


def step(lib, w, n=1):
    for _ in range(n):
        lib.om_tactical_step(w)


def produce(lib, w, k):
    """k productions in one support tick: the timer is set to k intervals and one om_tactical_step runs the driver, whose
    loop spawns each unit at once, so the next production of the tick sees it as a live unit."""
    lib.om_structure_set_timer(w, STRUCT, k * interval(lib))
    step(lib, w, 1)


def new_units(lib, w, before):
    return [u for u in alive(lib, w) if u not in before]


def positions_of(lib, w, ids):
    return [xy(lib, w, u) for u in ids]


def near(a, b):
    return abs(a[0] - b[0]) <= TOL and abs(a[1] - b[1]) <= TOL


def assert_slots(lib, w, ids, at, expected, why):
    got = positions_of(lib, w, ids)
    want = [slot_xy(at, ij) for ij in expected]
    assert len(got) == len(want) and all(near(g, t) for g, t in zip(got, want)), (
        f"{why}: new units (ascending id) at {got}, the scan order wants {want} (slots {expected})")


def fill(lib, w, at, slots, faction=PLAYER_FAC, utype=UTYPE, layer=0):
    """The occupancy fixture builder: one unit exactly on each listed slot; returns {slot: unit id}."""
    placed = {}
    for ij in slots:
        x, y = slot_xy(at, ij)
        uid = lib.om_unit_spawn(w, utype, faction, x, y, layer)
        assert uid != 0, f"fixture: unit refused at slot {ij} ({x}, {y})"
        placed[ij] = uid
    return placed


def bind_rng_remaining(lib):
    lib.om_rng_forced_remaining.argtypes = [V]
    lib.om_rng_forced_remaining.restype = ctypes.c_uint32


def save(lib, w):
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


# =========================================================================================================================
# POSITIVE CONTROLS (green today on the built tree, and green after the build)
# =========================================================================================================================


@pytest.mark.parametrize("seed", SEEDS)
def test_C1_a_held_structure_produces_one_unit_after_its_interval(lib, world_factory, seed):
    """Control (the mechanism works at all): nothing for interval-1 ticks, then exactly one new unit of the owner's faction and
    the structure's type within 150 wu of the structure. Premise: before the first production only the filler exists."""
    w = build(lib, world_factory, seed)
    before = alive(lib, w)
    assert len(before) == 1, f"premise: only the filler stands before the first production, found {before}"
    n = interval(lib)
    step(lib, w, n - 1)
    assert new_units(lib, w, before) == [], "control: a unit appeared before the interval elapsed"
    step(lib, w, 1)
    new = new_units(lib, w, before)
    assert len(new) == 1, f"control: exactly one unit at tick {n}, found {len(new)}"
    u = new[0]
    assert lib.om_unit_get_faction(w, u) == PLAYER_FAC and lib.om_unit_get_unit_type(w, u) == UTYPE
    assert d2(xy(lib, w, u), AT) <= BOUND * BOUND + TOL, "control: the unit stands beyond 150 wu of the structure"


def test_C2_the_pairwise_detector_flags_a_planted_pair_and_passes_a_pair_at_30():
    """Control for the pairwise checks below (a detector with its control): a planted pair at 29.0 wu is flagged, a pair at
    exactly 30.0 wu is not, a pair at 29.999999 wu (inside the DRAFT-prodslot-test-tol) is not, a pair at 29.99 is."""
    assert pairs_closer_than_spacing([(0.0, 0.0), (29.0, 0.0)]) == [(0, 1, 841.0)]
    assert pairs_closer_than_spacing([(0.0, 0.0), (30.0, 0.0)]) == []
    assert pairs_closer_than_spacing([(0.0, 0.0), (0.0, 30.0), (30.0, 30.0)]) == []
    assert len(pairs_closer_than_spacing([(0.0, 0.0), (29.99, 0.0)])) == 1
    assert len(pairs_closer_than_spacing([(5.0, 5.0), (5.0, 5.0)])) == 1


# Premises DUMPED from origin/main (73c4ce84 built) 2026-10-21 with scene(seed, military) below; not invented.
MS_SEEDS = (7, 11)
MS_MILITARY = 20.0      # the military value test_E01_T3_mission_ground.py uses (its MILITARY, "provisional")
MS_ARCHETYPE = 3        # ASSAULT, a battle archetype
MS_PLAYER_N = 301       # DUMP: player units after om_mission_setup, both seeds
MS_FIRST_12 = [         # DUMP: (unit id, x, y) of the first twelve player units, both seeds
    (1, 11920.0, 120.0), (2, 11950.0, 120.0), (3, 11980.0, 120.0), (4, 11920.0, 150.0), (5, 11950.0, 150.0), (6, 11980.0, 150.0),
    (7, 11920.0, 180.0), (8, 11950.0, 180.0), (9, 11980.0, 180.0), (10, 11820.0, 120.0), (11, 11850.0, 120.0), (12, 11880.0, 120.0)]
MS_SHA = {              # DUMP: sha256 over every player unit "id,type,x.hex(),y.hex();" per seed
    7: "10090fa72123fdb294c40c9548c38913e45419f58f848313b0497e7b9e70fa0a",
    11: "4d02119831eb3f2ff61817064cae69bb3cc37ac94d4df1f558ba1070bd5cf1e2",
}


def _mission_start_scene(lib, world_factory, seed):
    w = world_factory(n_regions=2, seed=seed)
    lib.om_world_set_feature(w, OMFeature.TACTICAL, 1)
    set_faction(lib, w, PLAYER_FAC, OMArchetype.PLAYER)
    set_faction(lib, w, ENEMY_FAC, OMArchetype.CONQUEROR)
    set_owner(lib, w, 0, ENEMY_FAC, held_since=-1)
    set_owner(lib, w, 1, PLAYER_FAC, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    set_region(lib, w, 0, tier=OMTier.HOME, military=MS_MILITARY, faction_id=ENEMY_FAC)
    lib.om_mission_setup(w, 0, MS_ARCHETYPE, 0)
    return w


def _player_start_units(lib, w):
    return [u for u in alive(lib, w) if lib.om_unit_get_faction(w, u) == PLAYER_FAC]


@pytest.mark.parametrize("seed", MS_SEEDS)
def test_C3_mission_start_spacing_is_unchanged(lib, world_factory, seed):
    """Control (mission-start spacing, mission.c:2464-2520, is not touched by prodslot): the player's mission-start units are
    pairwise at least 30 wu apart and sit at the values dumped from the built tree (the first twelve literally, all 301 by
    sha256 of (id, type, x, y))."""
    w = _mission_start_scene(lib, world_factory, seed)
    ids = _player_start_units(lib, w)
    pts = positions_of(lib, w, ids)
    assert len(ids) == MS_PLAYER_N, f"premise: {MS_PLAYER_N} player units at mission start, found {len(ids)}"
    assert pairs_closer_than_spacing(pts) == [], "control: mission-start units closer than 30 wu"
    assert [(u,) + xy(lib, w, u) for u in ids[:12]] == MS_FIRST_12
    h = hashlib.sha256()
    for u, p in zip(ids, pts):
        h.update(f"{u},{lib.om_unit_get_unit_type(w, u)},{p[0].hex()},{p[1].hex()};".encode())
    assert h.hexdigest() == MS_SHA[seed], f"control: mission-start positions moved (sha256 {h.hexdigest()})"


def test_C4_a_known_drawer_consumes_a_forced_draw(lib, world_factory):
    """Control for the forced-draw reading (the test_core_reinforcement_wave.py pattern): the enemy-wave roll at tick 40 consumes
    one forced draw, so om_rng_forced_remaining detects consumption; and a tick before 40 consumes none (so a production
    on tick 1 below is the only possible drawer)."""
    bind_rng_remaining(lib)
    w = build(lib, world_factory, 12)
    force_draws(lib, w, [0.9])
    step(lib, w, 1)
    assert lib.om_rng_forced_remaining(w) == 1, "control: tick 1 consumed a draw (something else draws before tick 40)"
    step(lib, w, 40)
    assert lib.om_rng_forced_remaining(w) == 0, "control: the wave roll did not consume the forced draw, the reading is blind"


def _run_positions(lib, world_factory, seed, intervals):
    w = build(lib, world_factory, seed)
    step(lib, w, intervals * interval(lib))
    return alive(lib, w), w


@pytest.mark.parametrize("seed", SEEDS)
def test_C5_two_runs_from_one_seed_give_byte_equal_positions(lib, world_factory, seed):
    """Control (determinism): the same seed and the same steps give byte-equal (id, x, y) of every live unit."""
    blobs = []
    for _ in range(2):
        ids, w = _run_positions(lib, world_factory, seed, 5)
        assert len(ids) == 6, "control: filler plus five productions"
        blobs.append(b"".join(struct.pack("<Idd", u, *xy(lib, w, u)) for u in ids))
    assert blobs[0] == blobs[1], "control: two runs of one seed differ"


def test_C6_the_occupancy_fixture_is_really_full_and_one_removal_frees_exactly_one_slot(lib, world_factory):
    """Control for the occupancy fixture: it places a unit on every one of the lattice slots within 150 wu per the G2 ruling,
    the count of slots computed from the integer rule equals the units placed (80), the independent free-slot reading finds
    none free; the units stay put over several ticks; with one unit moved away exactly that slot is free."""
    assert len(ORDER) == N_SLOTS and len(set(ORDER)) == N_SLOTS, "oracle: the G2 rule gives 80 distinct slots"
    assert sum(1 for i in range(-RING_MAX, RING_MAX + 1) for j in range(-RING_MAX, RING_MAX + 1)
               if (i or j) and i * i + j * j <= RING_MAX * RING_MAX) == N_SLOTS
    assert all(math.hypot(*slot_xy((0.0, 0.0), ij)) <= BOUND + TOL for ij in ORDER), "oracle: every slot within 150 wu"
    w = build(lib, world_factory, 12)
    placed = fill(lib, w, AT, ORDER)
    assert len(placed) == N_SLOTS and len(set(placed.values())) == N_SLOTS
    pts = [xy(lib, w, u) for u in placed.values()]
    assert free_slots(AT, pts) == [], "fixture: not full"
    assert pairs_closer_than_spacing(pts) == [], "fixture: the placed units are closer than 30 wu"
    step(lib, w, 5)
    assert [xy(lib, w, u) for u in placed.values()] == pts, "fixture: the placed units moved over 5 ticks"
    victim = ORDER[37]
    lib.om_unit_set_pos(w, placed[victim], 14000.0, 14000.0)
    pts2 = [xy(lib, w, u) for u in placed.values()]
    assert free_slots(AT, pts2) == [victim], "fixture: removing one unit must free exactly one slot (the reading can see it)"


# =========================================================================================================================
# RED UNTIL BUILT
# =========================================================================================================================


def _crowding_at_spawn(lib, w, seen):
    """After one tick: for each unit that appeared in it, every live unit (any faction) closer than 30 wu to it, as
    (new id, other id, new position, other position, distance)."""
    found = []
    for u in new_units(lib, w, seen):
        for o in alive(lib, w):
            if o != u and d2(xy(lib, w, u), xy(lib, w, o)) < SQ - TOL:
                found.append((u, o, xy(lib, w, u), xy(lib, w, o), math.sqrt(d2(xy(lib, w, u), xy(lib, w, o)))))
        seen.append(u)
    return found


@pytest.mark.parametrize("seed", SEEDS)
def test_T1_ten_productions_are_ten_units_pairwise_30_apart_within_150(lib, world_factory, seed):
    """Spec: ten productions from one structure yield ten units pairwise at least 30 wu apart, each within 150 wu of the
    structure. Stepped through om_tactical_step (the driver runs), a far filler parked. Read at the tick each unit appears
    (the sim's collision step pushes overlapping units apart over the following ticks, so by the end of a 6000-tick run
    today's stacks have settled to 30 wu: the placement is what must not stack) and again at the end. RED today: the random
    placement puts a unit within 30 wu of a live unit (no occupancy check, FINDING-production-stack)."""
    w = build(lib, world_factory, seed)
    before = alive(lib, w)
    seen = list(before)
    crowded = []
    for _ in range(10 * interval(lib)):
        step(lib, w, 1)
        crowded += _crowding_at_spawn(lib, w, seen)
    new = new_units(lib, w, before)
    assert len(new) == 10, f"ten productions expected, found {len(new)} new units"
    pts = positions_of(lib, w, new)
    assert all(d2(p, AT) <= BOUND * BOUND + TOL for p in pts), "a unit stands beyond 150 wu of the structure"
    assert pairs_closer_than_spacing(pts) == [], "units closer than 30 wu at the end of the run"
    assert crowded == [], (
        "R-126-02/FINDING-production-stack: a produced unit appeared within 30 wu of a live unit; first pair "
        f"(new id {crowded[0][0]} at {crowded[0][2]}, id {crowded[0][1]} at {crowded[0][3]}, distance {crowded[0][4]:.4f} wu)")


@pytest.mark.parametrize("seed", SEEDS)
def test_T1_ten_productions_in_one_support_tick_are_ten_units_pairwise_30_apart(lib, world_factory, seed):
    """Spec: the later productions of one support tick see the earlier units as live, so ten productions in one tick are
    ten units pairwise at least 30 wu apart, each within 150 wu. RED today: the random placement stacks (the first pair under
    30 wu is in the failure message)."""
    w = build(lib, world_factory, seed)
    before = alive(lib, w)
    produce(lib, w, 10)
    new = new_units(lib, w, before)
    assert len(new) == 10
    pts = positions_of(lib, w, new)
    assert all(d2(p, AT) <= BOUND * BOUND + TOL for p in pts), "a unit stands beyond 150 wu of the structure"
    bad = pairs_closer_than_spacing(pts)
    assert bad == [], (
        "R-126-02/FINDING-production-stack: units closer than 30 wu; first pair "
        f"(ids {new[bad[0][0]]}, {new[bad[0][1]]}) at {pts[bad[0][0]]} and {pts[bad[0][1]]}, distance {math.sqrt(bad[0][2]):.4f} wu")


@pytest.mark.parametrize("seed", SEEDS)
def test_T2_the_first_two_natural_productions_take_the_first_two_slots(lib, world_factory, seed):
    """Spec/G2: the first production takes the first free slot in the scan order (-1,-1), the second the next (0,-1); each
    interval one unit. RED today: random angle and distance."""
    w = build(lib, world_factory, seed)
    n = interval(lib)
    before = alive(lib, w)
    step(lib, w, n)
    first = new_units(lib, w, before)
    step(lib, w, n)
    both = new_units(lib, w, before)
    assert_slots(lib, w, both, AT, ORDER[:2], "R-126-02 scan order")
    assert both[:1] == first


def test_T2_thirteen_productions_in_one_support_tick_fill_ring_one_and_start_ring_two_in_scan_order(lib, world_factory):
    """Spec/G2: ring 1 (8 slots, row-major j outer then i inner) then the start of ring 2, lowest slot index first; the later
    productions of one tick see the earlier units as live. RED today: random placement."""
    w = build(lib, world_factory, 12)
    before = alive(lib, w)
    produce(lib, w, 13)
    new = new_units(lib, w, before)
    assert len(new) == 13
    assert ORDER[:8] == [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)], "oracle: ring 1 row-major"
    assert_slots(lib, w, new, AT, ORDER[:13], "R-126-02 scan order (ring 1 then start of ring 2)")


def test_T2_eighty_productions_fill_every_slot_in_order_and_the_81st_is_blocked(lib, world_factory):
    """Spec/G2: ring by ring outward up to the 150 wu bound inclusive (slot (0,5) and (5,0) are at exactly 150): 80 productions
    take the 80 slots in scan order and no more; a blocked structure ends the tick (the test would hang otherwise), pending 0,
    the timer kept. RED today: random placement."""
    w = build(lib, world_factory, 12)
    before = alive(lib, w)
    produce(lib, w, N_SLOTS + 1)
    new = new_units(lib, w, before)
    assert_slots(lib, w, new, AT, ORDER, "R-126-02 scan order over all 80 slots")
    assert lib.om_structure_pop_spawned_unit(w, STRUCT) == 0, "a blocked production left a pending spawn"
    assert lib.om_structure_get_timer(w, STRUCT) >= interval(lib), "the 81st production was blocked: the timer must be kept"


OCCUPANTS = [
    # (id, [(dx, dy, faction, layer)], expected first slot) -- offsets from the structure point AT
    ("own_unit_on_slot_one", [(-30.0, -30.0, PLAYER_FAC, 0)], (0, -1)),        # a unit at exactly 30 from the next slot does not block it (G2 "exactly s does not block")
    ("enemy_unit_on_slot_one", [(-30.0, -30.0, ENEMY_FAC, 0)], (0, -1)),       # G8 null action: every faction occupies
    ("unit_on_layer_one_on_slot_one", [(-30.0, -30.0, PLAYER_FAC, 1)], (0, -1)),  # G8 null action: every layer occupies
    ("off_lattice_unit_29_from_slot_one", [(-1.0, -30.0, PLAYER_FAC, 0)], (1, -1)),  # 1 from (0,-1), 29 from (-1,-1), 31 from (1,-1): strictly less than 30 blocks
    ("unit_at_30_from_slot_one_blocks_nothing", [(-60.0, -30.0, PLAYER_FAC, 0)], (-1, -1)),  # 30 from (-1,-1): not within strictly less
]


@pytest.mark.parametrize("name,occupants,expected", OCCUPANTS, ids=[o[0] for o in OCCUPANTS])
def test_T2_a_slot_is_free_when_no_live_unit_stands_strictly_within_30_wu(lib, world_factory, name, occupants, expected):
    """Spec/G2/G8: skipping slots within 30 wu of any live unit (strictly less, squared distances, no epsilon; every faction,
    every layer). RED today: random placement."""
    w = build(lib, world_factory, 12)
    for dx, dy, fac, layer in occupants:
        uid = lib.om_unit_spawn(w, UTYPE, fac, AT[0] + dx, AT[1] + dy, layer)
        assert uid != 0 and lib.om_unit_get_layer(w, uid) == layer, "fixture: occupant refused or on another layer"
    pts = [xy(lib, w, u) for u in alive(lib, w) if xy(lib, w, u) != FAR and d2(xy(lib, w, u), AT) < 1e6]
    assert free_slots(AT, pts)[0] == expected, "oracle: the expected first free slot"
    before = alive(lib, w)
    produce(lib, w, 1)
    assert_slots(lib, w, new_units(lib, w, before), AT, [expected], f"R-126-02 occupancy ({name})")


@pytest.mark.parametrize("freed", (0, 12, N_SLOTS - 1), ids=("first_slot", "slot_12", "last_slot_at_150"))
def test_T3_a_full_lattice_delays_production_and_places_when_one_slot_frees(lib, world_factory, freed):
    """Spec: no free slot within 150 wu delays production one tick (the structure keeps its timer). Every slot occupied: for
    five support ticks no unit appears, pending stays 0, the timer is never subtracted, last_spawn_distance is unchanged;
    freeing exactly one slot makes the next support tick place the unit in that slot (timer subtracted); full again, it waits
    again. RED today: the random placement ignores occupancy and spawns."""
    w = build(lib, world_factory, 12)
    placed = fill(lib, w, AT, ORDER)
    n = interval(lib)
    dist0 = lib.om_structure_get_last_spawn_distance(w, STRUCT)
    count0 = len(alive(lib, w))
    for k in range(5):
        lib.om_structure_set_timer(w, STRUCT, n)
        step(lib, w, 1)
        t = lib.om_structure_get_timer(w, STRUCT)
        assert t >= n, f"tick {k + 1}: no free slot, the timer must be kept (not subtracted), read {t} (interval {n})"
        assert lib.om_structure_pop_spawned_unit(w, STRUCT) == 0, f"tick {k + 1}: a pending spawn with no free slot"
        assert len(alive(lib, w)) == count0, f"tick {k + 1}: a unit appeared with every slot within 150 wu occupied"
        assert lib.om_structure_get_last_spawn_distance(w, STRUCT) == dist0, f"tick {k + 1}: last_spawn_distance changed on a blocked tick"
    victim = ORDER[freed]
    lib.om_unit_set_pos(w, placed[victim], 14000.0, 14000.0)
    lib.om_structure_set_timer(w, STRUCT, n)
    before = alive(lib, w)
    step(lib, w, 1)
    assert_slots(lib, w, new_units(lib, w, before), AT, [victim], "R-126-02 the freed slot takes the unit on the next support tick")
    assert lib.om_structure_get_timer(w, STRUCT) < n, "the production happened: the timer must have subtracted the interval"
    d = lib.om_structure_get_last_spawn_distance(w, STRUCT)
    dist_slot = math.sqrt(SQ * (victim[0] * victim[0] + victim[1] * victim[1]))
    assert abs(d - dist_slot) <= TOL, f"last_spawn_distance {d} should be the slot's distance {dist_slot}"
    # full again (the new unit sits on the slot): waits again, distance stays at the slot's
    lib.om_structure_set_timer(w, STRUCT, n)
    count1 = len(alive(lib, w))
    step(lib, w, 3)
    assert len(alive(lib, w)) == count1 and lib.om_structure_get_last_spawn_distance(w, STRUCT) == d, "full again: it must wait again"


def test_T4_save_round_trip_mid_sequence_equals_an_uninterrupted_run(lib, world_factory):
    """Spec: save and load in the middle of a sequence give the same positions as an uninterrupted run. After three
    productions save, load into a fresh world, finish three more; every live unit's (id, x, y) equals the uninterrupted
    run's. (A guard that may be green on the built tree, where the draws live in the saved RNG state; T4b below is the red
    half.)"""
    n = interval(lib)
    a = build(lib, world_factory, 12)
    step(lib, a, 3 * n)
    buf, size = save(lib, a)
    step(lib, a, 3 * n)
    want = [(u,) + xy(lib, a, u) for u in alive(lib, a)]
    b = world_factory(n_regions=2, seed=12)
    assert lib.om_load_state_read(b, buf, size) == 0
    step(lib, b, 3 * n)
    got = [(u,) + xy(lib, b, u) for u in alive(lib, b)]
    assert len(want) == 7 and got == want, f"the resumed run differs from the uninterrupted one:\nuninterrupted {want}\nresumed       {got}"


def test_T4_the_comparison_sees_a_planted_difference(lib, world_factory):
    """Control for T4: the same load, but one extra unit planted on the next free slot before the sequence resumes, makes
    the resumed positions differ from the uninterrupted run (the comparison can fail)."""
    n = interval(lib)
    a = build(lib, world_factory, 12)
    step(lib, a, 3 * n)
    buf, size = save(lib, a)
    step(lib, a, 3 * n)
    want = [(u,) + xy(lib, a, u) for u in alive(lib, a)]
    b = world_factory(n_regions=2, seed=12)
    assert lib.om_load_state_read(b, buf, size) == 0
    lib.om_unit_spawn(b, UTYPE, PLAYER_FAC, 14000.0, 14000.0, 0)  # planted: one more unit than the uninterrupted run had
    step(lib, b, 3 * n)
    got = [(u,) + xy(lib, b, u) for u in alive(lib, b)]
    assert got != want, "control: a planted extra unit must make the resumed run differ"


def test_T4b_after_a_load_the_sequence_continues_the_scan_order(lib, world_factory):
    """Spec/G2 with a save in the middle: the loaded units are live units, so after three productions, save, load, three more,
    the six new units stand on the first six slots in scan order. RED today: random placement."""
    n = interval(lib)
    a = build(lib, world_factory, 12)
    before = alive(lib, a)
    step(lib, a, 3 * n)
    buf, size = save(lib, a)
    b = world_factory(n_regions=2, seed=12)
    assert lib.om_load_state_read(b, buf, size) == 0
    step(lib, b, 3 * n)
    assert_slots(lib, b, new_units(lib, b, before), AT, ORDER[:6], "R-126-02 scan order across a save and load")


def test_T5_a_production_consumes_no_rng_draw(lib, world_factory):
    """Spec: no RNG draw consumed. Four forced draws are loaded, a production runs (the public om_structure_tick_production,
    the drawer today), om_rng_forced_remaining is unchanged. RED today: it consumes 2 (angle, distance)."""
    bind_rng_remaining(lib)
    w = build(lib, world_factory, 12)
    force_draws(lib, w, [0.9, 0.1, 0.5, 0.5])
    lib.om_structure_set_timer(w, STRUCT, interval(lib))
    lib.om_structure_tick_production(w, STRUCT)
    assert lib.om_structure_pop_spawned_unit(w, STRUCT) == 1, "premise: the production happened"
    assert lib.om_rng_forced_remaining(w) == 4, f"TD-VG-E-29: a production consumed {4 - lib.om_rng_forced_remaining(w)} RNG draws"


def test_T5_the_placement_does_not_depend_on_the_rng_stream(lib, world_factory):
    """Spec: scan order fixed, no RNG draw. The same tick-1 production with forced draws 0.99/0.01 loaded and without them
    puts the unit at the same place (the slot), and consumes none of the forced draws (tick 1 is before the tick-40 wave
    roll, control C4). RED today: the position follows the draws."""
    bind_rng_remaining(lib)
    pos = []
    for forced in (None, [0.99, 0.01]):
        w = build(lib, world_factory, 12)
        if forced:
            force_draws(lib, w, forced)
        before = alive(lib, w)
        produce(lib, w, 1)
        new = new_units(lib, w, before)
        assert len(new) == 1
        pos.append(xy(lib, w, new[0]))
        if forced:
            assert lib.om_rng_forced_remaining(w) == 2, "the production consumed forced draws"
    assert near(pos[0], pos[1]) and near(pos[0], slot_xy(AT, ORDER[0])), f"placement followed the RNG: {pos}"


def test_T6_an_enemy_owned_structure_follows_the_same_rule(lib, world_factory):
    """G8 null action: every producing owner (>= 0) uses the same rule. An enemy-owned structure: thirteen productions in one
    tick take the first thirteen slots in scan order, all of the enemy faction, pairwise 30 apart. RED today: random."""
    w = build(lib, world_factory, 12, owner=ENEMY_FAC)
    before = alive(lib, w)
    produce(lib, w, 13)
    new = new_units(lib, w, before)
    assert len(new) == 13 and all(lib.om_unit_get_faction(w, u) == ENEMY_FAC for u in new)
    assert pairs_closer_than_spacing(positions_of(lib, w, new)) == []
    assert_slots(lib, w, new, AT, ORDER[:13], "R-126-02 enemy-owned structure")


def test_T7_last_spawn_distance_is_zero_before_and_the_distance_to_the_unit_after(lib, world_factory):
    """G6 null action / ruling pin 8: 0.0 before any production; after a production it is <= 150.0 and equals the distance from
    the structure to the unit, which is the slot's distance (first slot (-1,-1): 30 * sqrt(2)). RED today: the draw's distance."""
    w = build(lib, world_factory, 12)
    assert lib.om_structure_get_last_spawn_distance(w, STRUCT) == 0.0
    before = alive(lib, w)
    produce(lib, w, 1)
    u = new_units(lib, w, before)[0]
    d = lib.om_structure_get_last_spawn_distance(w, STRUCT)
    assert d <= BOUND
    assert abs(d - SPACING * math.sqrt(2.0)) <= TOL, f"last_spawn_distance {d} is not the first slot's distance"
    assert abs(d - math.sqrt(d2(xy(lib, w, u), AT))) <= TOL, f"last_spawn_distance {d} is not the structure-to-unit distance"
    produce(lib, w, 12)
    d2nd = lib.om_structure_get_last_spawn_distance(w, STRUCT)
    last = [x for x in alive(lib, w) if x not in before][-1]
    assert abs(d2nd - math.sqrt(d2(xy(lib, w, last), AT))) <= TOL and d2nd <= BOUND


def _refused_slots(lib, world_factory, utype):
    """The slots om_unit_spawn itself refuses for a unit of this type on the terrain fixture (probed in a scratch world with
    the same terrain), by the production code's own predicate."""
    w = build(lib, world_factory, 12, at=AT_TERRAIN, terrain=True)
    out = set()
    for ij in ORDER:
        x, y = slot_xy(AT_TERRAIN, ij)
        if lib.om_unit_spawn(w, utype, PLAYER_FAC, x, y, 0) == 0:
            out.add(ij)
    return out


def test_T9_a_slot_the_terrain_refuses_for_a_walker_is_skipped(lib, world_factory):
    """G2 ruling (terrain): a slot om_unit_spawn would refuse is skipped as occupied; the pin-5 positive control: on a terrain
    fixture the refused points are exactly those om_unit_spawn refuses for a walker (band 0 and an unwalkable cell). The
    structure produces a walker; the units take the first free, accepted slots in order; none is lost to a refused spawn.
    Premise: the fixture refuses slots 1 and 2 (the ring-1 slots (0,-1), (1,-1)) and others, but not all. RED today: random."""
    refused = _refused_slots(lib, world_factory, UTYPE)
    assert 0 < len(refused) < N_SLOTS and ORDER[1] in refused and ORDER[2] in refused, f"premise: refused {sorted(refused)}"
    w = build(lib, world_factory, 12, at=AT_TERRAIN, terrain=True)
    before = alive(lib, w)
    produce(lib, w, N_SLOTS + 1)
    new = new_units(lib, w, before)
    want = expected_sequence(AT_TERRAIN, [], N_SLOTS + 1, refused)
    assert len(want) == N_SLOTS - len(refused)
    assert_slots(lib, w, new, AT_TERRAIN, want, "R-126-02 terrain-refused slots are skipped")


def test_T9_a_flyer_takes_the_slots_a_walker_is_refused(lib, world_factory):
    """Positive control for the terrain duplicate (pin 5): on the same terrain a flyer (movement kind 0) is accepted at every
    slot, so a structure producing flyers fills all 80 in scan order including the slots a walker is refused. RED today:
    random."""
    w = build(lib, world_factory, 12, at=AT_TERRAIN, utype=FILLER_TYPE, terrain=True)
    assert lib.om_unit_profile_movement_kind(w, FILLER_TYPE) == 0, "premise: type 1 is a flyer"
    before = alive(lib, w)
    produce(lib, w, N_SLOTS + 1)
    new = new_units(lib, w, before)
    assert_slots(lib, w, new, AT_TERRAIN, ORDER, "R-126-02 a flyer is accepted on every slot")


# ---- the helper (G1) in isolation: bound here because tests/csim/conftest.py is not in this piece's test files ----------


def _helper(lib):
    fn = lib.om_mission_production_slot  # AttributeError (undefined symbol) until the helper exists
    if not fn.argtypes:
        fn.argtypes = [V, ctypes.c_uint32, P(ctypes.c_double), P(ctypes.c_double)]
        fn.restype = ctypes.c_int
    return fn


def _ask(lib, w):
    fn = _helper(lib)
    x, y = ctypes.c_double(-1.0), ctypes.c_double(-1.0)
    rc = fn(w, STRUCT, ctypes.byref(x), ctypes.byref(y))
    return rc, (x.value, y.value)


def test_T10_the_helper_returns_the_first_free_slot_or_zero(lib, world_factory):
    """G1: int om_mission_production_slot(const om_world *w, uint32_t structure, double *out_x, double *out_y) returns 1 and
    the first free slot of the scan order, or 0 when no slot within 150 wu is free. RED on the built tree: the symbol does not
    exist."""
    w = build(lib, world_factory, 12)
    rc, p = _ask(lib, w)
    assert rc == 1 and near(p, slot_xy(AT, ORDER[0])), f"empty lattice: {rc} {p}"
    placed = fill(lib, w, AT, ORDER[:20])
    rc, p = _ask(lib, w)
    assert rc == 1 and near(p, slot_xy(AT, ORDER[20])), f"20 taken: {rc} {p}"
    fill(lib, w, AT, ORDER[20:])
    rc, _ = _ask(lib, w)
    assert rc == 0, "all 80 taken: no slot"
    lib.om_unit_set_pos(w, placed[ORDER[3]], 14000.0, 14000.0)
    rc, p = _ask(lib, w)
    assert rc == 1 and near(p, slot_xy(AT, ORDER[3])), f"one freed: {rc} {p}"
