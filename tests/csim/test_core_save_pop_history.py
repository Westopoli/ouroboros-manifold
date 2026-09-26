"""SAVE-1: faction_pop_history ring round-trips through save/load (ALG-27b).

Tests that faction_pop_history / _head / _len are serialised so the
Knowledge-Lost pop-drop leg (R-045-07, R-045-09) fires in a loaded world at
the same tick as in the unsaved world.

RED on main for all three tests: the ring fields are not serialised, so after
a load the ring is empty and the pop-drop eligibility check never fires.
GREEN after SAVE-1 lands.
"""
import ctypes
import pytest

from conftest import (
    OMArchetype,
    OMFeature,
    OMTier,
    force_draws,
    set_faction,
    set_owner,
    set_region,
)


# ---- save/load helpers (same pattern as test_E16_S111_saving.py) ----

def _bind_save(lib):
    if getattr(lib, "_save_bound", False):
        return
    V = ctypes.c_void_p
    P = ctypes.POINTER
    lib.om_save_state_size.argtypes = [V]
    lib.om_save_state_size.restype = ctypes.c_uint32
    lib.om_save_state_write.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_save_state_write.restype = None
    lib.om_load_state_read.argtypes = [V, P(ctypes.c_uint8), ctypes.c_uint32]
    lib.om_load_state_read.restype = ctypes.c_int
    lib._save_bound = True


def _save(lib, w):
    _bind_save(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _load(lib, w, buf, size):
    _bind_save(lib)
    return lib.om_load_state_read(w, buf, size)


def _ring_world(lib, world_factory, *, pop=50.0, eco=25.0, tech=30.0):
    """1-region, 1-faction world. Only TECHNOLOGY feature enabled: om_world_step
    runs only the tech step, so population is stable (no drift). Tick starts at
    100 so the cooldown (OM_KNOWLEDGE_LOST_COOLDOWN=100) is clear from the
    first qualifying step (100 - (-1) = 101 >= 100). eco >= 20 disables the
    economy leg so only the pop-drop leg matters."""
    w = world_factory(n_regions=1)
    for feat in (OMFeature.EVENTS, OMFeature.FACTIONS, OMFeature.FRICTION,
                 OMFeature.ADMIN_REVOLTS, OMFeature.DRIFT, OMFeature.LIFECYCLE,
                 OMFeature.TACTICAL, OMFeature.DIPLOMACY):
        lib.om_world_set_feature(w, feat, 0)
    lib.om_world_set_feature(w, OMFeature.TECHNOLOGY, 1)
    lib.om_world_set_tick(w, 100)
    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=tech)
    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=eco,
               tension=10.0, population=pop)
    set_owner(lib, w, 0, 0)
    return w


def test_ring_round_trips_eligibility(lib, world_factory):
    """S-111 / R-045-07 / ALG-27b: ring serialised so loaded world fires KL.

    RED on main: after load the ring is empty (len=0), pop-drop leg is never
    eligible (requires len==50), KL does not fire, last_knowledge_lost stays -1.
    GREEN after: ring restored with len=50, pop=39.0 is a drop of 11.0 from the
    stored 50.0, draw 0.01 < 0.03 fires KL, tech drops 5.0 in both worlds.

    110 steps fill and cycle the ring: all 50 slots hold 50.0.  Save.  Load
    into a fresh world.  Set pop=39.0 in both, force draw 0.01 in both, step
    once.  Both must fire."""
    w1 = _ring_world(lib, world_factory)
    for _ in range(110):
        lib.om_world_step(w1)
    tech_at_save = lib.om_faction_tech(w1, 0)

    buf, size = _save(lib, w1)

    w2 = world_factory(n_regions=1)
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"save must load cleanly, rc={rc}"

    for w in (w1, w2):
        set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
                   tension=10.0, population=39.0, faction_id=0)
        force_draws(lib, w, [0.01])

    lib.om_world_step(w1)
    lib.om_world_step(w2)

    assert lib.om_faction_last_knowledge_lost(w1, 0) != -1, \
        "fixture: w1 must fire KL (ring full, pop drop 11.0, draw 0.01)"
    assert lib.om_faction_last_knowledge_lost(w2, 0) != -1, \
        "w2 (loaded) must fire KL; RED on main because ring is empty after load"
    assert lib.om_faction_tech(w2, 0) == pytest.approx(lib.om_faction_tech(w1, 0), abs=1e-9), \
        "tech must match w1; on main ring empty -> no KL drop in w2"


def test_ring_round_trips_checksum(lib, world_factory):
    """S-111 / R-045-07 / ALG-27b: checksum and tech agree after 60 further
    steps past a save/load boundary when ring is correctly serialised.

    RED on main: w2 ring empty -> KL misses in step 1 -> tech diverges by 5.0
    -> checksum diverges.
    GREEN after: both worlds fire at step 1, grow identically for steps 2-60,
    checksums and tech match.

    Force draw 0.01 in both so the KL draw is consumed deterministically in
    step 1 regardless of the live RNG stream."""
    w1 = _ring_world(lib, world_factory)
    for _ in range(110):
        lib.om_world_step(w1)

    buf, size = _save(lib, w1)

    w2 = world_factory(n_regions=1)
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"save must load cleanly, rc={rc}"

    for w in (w1, w2):
        set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
                   tension=10.0, population=39.0, faction_id=0)
        force_draws(lib, w, [0.01])

    for _ in range(60):
        lib.om_world_step(w1)
        lib.om_world_step(w2)

    cs1 = lib.om_world_get_state_checksum(w1)
    cs2 = lib.om_world_get_state_checksum(w2)
    t1 = lib.om_faction_tech(w1, 0)
    t2 = lib.om_faction_tech(w2, 0)
    assert cs1 == cs2, \
        f"checksum diverged ({cs1} vs {cs2}); on main ring unserialized -> KL only in w1"
    assert t1 == pytest.approx(t2, abs=1e-9), \
        "tech must match; on main w1 fires KL (-5.0) but w2 does not"


def test_ring_partial_fill_round_trips(lib, world_factory):
    """S-111 / R-045-07 / ALG-27b: a save with len<50 restores head and len so
    eligibility becomes true at the same tick in the loaded world.

    Setup: 30 steps fill the ring to len=30.  Save.  Load into w2.  Both worlds
    then step 20 more times (ring reaches len=50 in both).  Then set pop=39.0,
    force draw 0.01, step once.  KL must fire at the same tick in both.

    RED on main: w2 len=0 after load; after 20 more steps len=20 < 50 -> not
    eligible -> no fire -> last_kl stays -1 != w1's fire tick.
    GREEN after: w2 len=30 restored; 20 more steps -> len=50 -> fires at same tick."""
    w1 = _ring_world(lib, world_factory)
    for _ in range(30):
        lib.om_world_step(w1)

    buf, size = _save(lib, w1)

    w2 = world_factory(n_regions=1)
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"save must load cleanly, rc={rc}"

    for w in (w1, w2):
        for _ in range(20):
            lib.om_world_step(w)

    for w in (w1, w2):
        set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=25.0,
                   tension=10.0, population=39.0, faction_id=0)
        force_draws(lib, w, [0.01])
        lib.om_world_step(w)

    lkl1 = lib.om_faction_last_knowledge_lost(w1, 0)
    lkl2 = lib.om_faction_last_knowledge_lost(w2, 0)
    assert lkl1 != -1, "fixture: w1 must fire KL after ring filled"
    assert lkl2 != -1, \
        "w2 (loaded, len=30 restored) must fire at same tick; RED on main (len=0 -> not eligible)"
    assert lkl1 == lkl2, \
        f"both worlds must fire at the same tick ({lkl1} vs {lkl2}); on main w2 ring starts empty"
