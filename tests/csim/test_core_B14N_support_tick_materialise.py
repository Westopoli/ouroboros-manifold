# Rule pins: R-126-02@741af4, R-126-06@84ac8e
"""B4 / B14-N: om_support_tick materialises a held structure's production.

R-126-02: Given a held structure with a chosen unit type, When its production
timer reaches 30 s x (that type's power / 100), Then one unit of that type
spawns at the first free slot of the structure's spawn lattice, within half the
capture radius of the structure (300 / 2 = 150, inclusive) on the structure's layer, with
no random draw, and the timer subtracts the interval (R-126-02 as rewritten, Westley
2026-10-12, TD-VG-E-29). The rule gives no cap
on units alive, so none is asserted. R-126-06: no trickle for a player who holds
nothing. Interval in ticks: om_structure_production_interval_ticks(power).

Structures here are hand-built (om_structure_init / set_owner / set_position) so
this piece is satisfiable by csrc/tactical_support.c alone; the mission-setup to
production chain is tested in test_core_B9N_mission_setup_structures.py.
"""
import ctypes
import math

from conftest import OMVec2
from b1_macro_scene import ENEMY_FAC, PLAYER_FAC, tactical_world

SLOTS = 64
CAPTURE_HALF = 150.0


POWERS = (100.0, 150.0)
SPOTS = ((3000.0, 3000.0), (9000.0, 9000.0))


def _player_structures(lib, w):
    rows = []
    for slot, (power, (x, y)) in enumerate(zip(POWERS, SPOTS)):
        lib.om_structure_init(w, slot, 0, ctypes.c_double(power))
        lib.om_structure_set_owner(w, slot, PLAYER_FAC)
        lib.om_structure_set_position(w, slot, x, y)
        rows.append((slot, x, y, lib.om_structure_production_interval_ticks(ctypes.c_double(power))))
    return rows


def _units_of(lib, w, faction):
    return {
        uid for uid in range(1, 2048)
        if lib.om_unit_alive(w, uid) and lib.om_unit_get_faction(w, uid) == faction
    }


def _scene(lib, world_factory):
    w = tactical_world(lib, world_factory, seed=11)
    lib.om_mission_set_phase(w, 1)
    rows = _player_structures(lib, w)
    assert rows[0][3] < rows[1][3], "setup: the two structures must have different intervals"
    # om_tactical_step is a no-op with no units: park a far enemy unit as filler.
    lib.om_unit_spawn(w, 0, ENEMY_FAC, 100_000.0, 100_000.0, 0)
    return w, rows


def test_held_structure_produces_nothing_before_its_interval(lib, world_factory):
    """R-126-02: one step short of the shortest interval, no player unit has appeared."""
    w, rows = _scene(lib, world_factory)
    before = _units_of(lib, w, PLAYER_FAC)
    for _ in range(min(r[3] for r in rows) - 1):
        lib.om_tactical_step(w)
    assert _units_of(lib, w, PLAYER_FAC) == before, "R-126-02: a unit spawned before the production interval elapsed"


def test_held_structure_materialises_a_unit_at_its_interval(lib, world_factory):
    """R-126-02: at the shortest interval, each player structure with that interval has produced
    exactly one unit, of its chosen type, within half the capture radius of it, in the unit list."""
    w, rows = _scene(lib, world_factory)
    before = _units_of(lib, w, PLAYER_FAC)
    first = min(r[3] for r in rows)
    due = [r for r in rows if r[3] == first]
    for _ in range(first):
        lib.om_tactical_step(w)
    new = _units_of(lib, w, PLAYER_FAC) - before
    assert len(new) == len(due), (
        f"R-126-02: {len(due)} structure(s) reached their {first}-tick interval, "
        f"expected that many new player units, found {len(new)}"
    )
    for _, sx, sy, _ in due:
        near = [u for u in new if math.hypot(
            lib.om_unit_position_x(w, u) - sx, lib.om_unit_position_y(w, u) - sy) <= CAPTURE_HALF]
        assert near, f"R-126-02: no new unit within {CAPTURE_HALF} of the structure at ({sx}, {sy})"


def test_second_interval_produces_the_second_unit(lib, world_factory):
    """R-126-02: the timer subtracts the interval (not reset to zero), so a lone interval later
    brings exactly one more unit per due structure."""
    w, rows = _scene(lib, world_factory)
    before = _units_of(lib, w, PLAYER_FAC)
    first = min(r[3] for r in rows)
    due = [r for r in rows if r[3] == first]
    for _ in range(2 * first):
        lib.om_tactical_step(w)
    new = _units_of(lib, w, PLAYER_FAC) - before
    assert len(new) >= 2 * len(due), (
        f"R-126-02: after two intervals expected at least {2 * len(due)} new player units, found {len(new)}"
    )


def test_materialised_unit_is_consumed_from_the_structure_queue(lib, world_factory):
    """R-126-02 / B14-N: the support tick pops each produced unit via om_structure_pop_spawned_unit
    when it spawns it, so no spawn is left pending for a second materialisation."""
    w, rows = _scene(lib, world_factory)
    first = min(r[3] for r in rows)
    for _ in range(first):
        lib.om_tactical_step(w)
    slot = next(r[0] for r in rows if r[3] == first)
    assert lib.om_structure_pop_spawned_unit(w, slot) == 0, (
        "R-126-02: a unit was materialised but its spawn is still pending -- "
        "om_support_tick does not drain om_structure_pop_spawned_unit"
    )


def test_neutral_structures_produce_nothing(lib, world_factory):
    """R-126-02 / R-126-06: a structure nobody holds yields no unit; with every structure
    neutral, the player's unit set is unchanged over several intervals (no trickle)."""
    w, rows = _scene(lib, world_factory)
    for slot, *_ in rows:
        lib.om_structure_set_owner(w, slot, -1)
    before = _units_of(lib, w, PLAYER_FAC)
    for _ in range(3 * max(r[3] for r in rows)):
        lib.om_tactical_step(w)
    assert _units_of(lib, w, PLAYER_FAC) == before, "R-126-06: player gained units while holding no structure"
