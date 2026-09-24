"""S-111 -- Saving (T2c, the C side of save/load; two-day-push brief,
docs/northstar/plans/briefs/2026-09-22-two-day-push.md, wave 2 row "T2c save
and load, C").

Covers R-111-02 (load restores the world such that the next jump is
deterministic) and R-111-03 (a save from a different game version is
refused). R-111-01 (autosave fires at mission start/end/time-jump-end) and
R-111-04 (unlimited campaign slots; no mid-mission save) are client-side
triggers this C contract cannot exercise by itself; they belong to T2g's
Godot tests. E-08 R-064-04 (E-08's own determinism-through-save rule, "the
next time jump produces the same trace as if never saved") is the same
property, proved here at the save.c level instead of through
om_chapter_start / om_time_jump_run, because E-08's own cards are unbuilt
(see tests/csim/test_E08_S064_what_carries_over.py, itself red today on
those missing symbols).

Targets the contracted C names from docs/northstar/spec_factory/signatures.toml:
om_save_state_size(const om_world*) -> uint32_t, om_save_state_write(const
om_world*, uint8_t* out, uint32_t capacity) -> void, om_load_state_read
(om_world*, const uint8_t* buffer, uint32_t length) -> int (see Q-111-02).
None of the three are in csrc/ouroboros_sim.h yet -- B7/save.c (wave 1) must
land before T2c can even start -- and conftest.py has no bindings for them
either, so this file binds them locally and every test below is expected to
fail on that missing symbol today, not on an assertion.

Q-111-01 [buffer format]: S-111 never specifies the save buffer's binary
layout. Candidates: (a) one flat memcpy of om_world's persisted fields, a
version word first -- what the contracted signature (a bare uint8_t*, no
chunk/framing API) implies, and what this file assumes; (b) a versioned
tag-length-value stream, forward-compatible across ABI bumps; (c) some other
opaque layout save.c's author picks. The version-word test below only
asserts refusal on a first-4-bytes mismatch, never what the correct word is,
so it holds under any of the three.

Q-111-02 [refusal signaling]: signatures.toml lists om_load_state_read's
return as "void ... int status plausible," a placeholder. R-111-03 requires
refusing a version mismatch "with a message naming the versions"; there is
no message-reading accessor anywhere in the header. Candidates: (a) int
status (0 success, non-zero a refusal code), with version numbers formatted
client-side from their own (also uncontracted) accessors; (b) int status
plus two out-params for source/target version; (c) void, with a separate
om_load_state_error() accessor read after a failed call. This file binds (a)
locally, the minimal shape that satisfies "refused, non-zero" literally.
"""
import ctypes

import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMField,
    OMAction,
    OMMode,
    OMStance,
    OMTier,
    inject_intent,
    load_launch_events,
    queue_external,
    read_telegraphs,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    template_id,
)


# local binding until the F1b freeze lands: om_save_state_size,
# om_save_state_write, and om_load_state_read are not yet in
# csrc/ouroboros_sim.h or conftest.py's bindings (B7/save.c, wave 1, lands
# first; F1b then generates the real _bind_save into conftest.py). Bound here
# straight from docs/northstar/spec_factory/signatures.toml so this file does
# not depend on either landing first; om_load_state_read's restype is c_int
# per Q-111-02 above, not the table's void placeholder.
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


# F5 moves this into conftest's OMBug once T2c's control lands (two-day-push
# brief, decision 6: save.c's reserved OM_BUG_* range starts at 1600).
_OM_BUG_SAVE_SKIPS_RNG_STATE = 1600


def _save(lib, w):
    _bind_save(lib)
    size = lib.om_save_state_size(w)
    buf = (ctypes.c_uint8 * size)()
    lib.om_save_state_write(w, buf, size)
    return buf, size


def _load(lib, w, buf, size):
    _bind_save(lib)
    return lib.om_load_state_read(w, buf, size)


def _fixture_world(lib, world_factory, seed, n_regions=4):
    """Two factions across n_regions, alternating ownership. world_factory
    already applies E-16's mvp_features.toml default (EVENTS, FACTIONS,
    FRICTION, ADMIN_REVOLTS, DRIFT) to every world this file creates; no
    event templates are loaded, so EVENTS stays inert (header contract:
    "with none loaded, tick steps 1 and 2 do nothing")."""
    w = world_factory(n_regions=n_regions, seed=seed)
    set_faction(lib, w, 0, OMArchetype.CONQUEROR, budget=100.0, tech=8.0, confidence=5.0)
    set_faction(lib, w, 1, OMArchetype.OPPORTUNIST, budget=70.0, tech=3.0, confidence=4.0)
    for idx in range(n_regions):
        set_region(lib, w, idx, tier=OMTier.HOME, military=35.0 + idx, economy=45.0 + idx,
                    tension=5.0, population=40.0 + idx, faction_id=idx % 2)
        set_owner(lib, w, idx, idx % 2, held_since=-1)
    set_edge(lib, w, 0, 1, OMEdge.BOTH)
    return w


def test_R_111_02_size_query_then_write_round_trips(lib, world_factory):
    """Given a live world, When its size is queried and then written into a
    buffer of exactly that size, Then the buffer round-trips: loading it
    into a fresh world succeeds (the buffer om_save_state_write filled is
    complete and parseable, not truncated or oversized)."""
    w = _fixture_world(lib, world_factory, seed=101)
    for _ in range(5):
        lib.om_world_step(w)
    buf, size = _save(lib, w)
    assert size > 0

    w2 = world_factory(n_regions=4, seed=999)
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"the buffer om_save_state_write filled at its own reported size must load cleanly, rc={rc}"


def test_R_111_02_second_write_is_byte_identical(lib, world_factory):
    """Given the same unchanged world, When om_save_state_write runs twice,
    Then the two buffers are byte-identical -- the write is a pure function
    of world state, not of wall-clock time or hash order (the determinism
    contract, CLAUDE.md)."""
    w = _fixture_world(lib, world_factory, seed=202)
    for _ in range(5):
        lib.om_world_step(w)
    buf1, size1 = _save(lib, w)
    buf2, size2 = _save(lib, w)
    # A hard-stub om_save_state_size of 0 would make both buffers empty and
    # the two checks below trivially true.
    assert size1 > 0
    assert size1 == size2
    assert bytes(buf1) == bytes(buf2)


def test_R_111_02_checksum_equal_at_save_and_after_fifty_more_steps(lib, world_factory):
    """Load into a fresh world gives om_world_get_state_checksum equal to
    the source's, both immediately (same tick) and after 50 further unforced
    steps under the same seed -- determinism through a save (E-08 R-064-04's
    property, proved at the save.c level since E-08 has no om_time_jump_run
    yet)."""
    seed = 303
    w1 = _fixture_world(lib, world_factory, seed=seed)
    for _ in range(20):
        lib.om_world_step(w1)

    buf, size = _save(lib, w1)
    checksum_at_save = lib.om_world_get_state_checksum(w1)

    w2 = world_factory(n_regions=4, seed=seed)
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"a clean save buffer must load, rc={rc}"
    assert lib.om_world_get_state_checksum(w2) == checksum_at_save

    for _ in range(50):
        lib.om_world_step(w1)
        lib.om_world_step(w2)
    assert lib.om_world_get_state_checksum(w1) == lib.om_world_get_state_checksum(w2)


def test_R_111_02_load_restores_tick_regions_factions_telegraphs_chain_and_rng(lib, world_factory):
    """Given a save and load between chapters, When loaded, Then the world,
    ledger, chapter, onboarding, RNG state, and chain counter are restored
    such that the next jump is deterministic (E-08 R-064-04). No chapter,
    ledger, or onboarding symbols exist yet (E-08's own cards are unbuilt);
    this test covers everything save.c's own contract can reach today:
    region fields and ownership, faction budgets and stances, the
    pending-telegraph list, the chain tag counter, and the live RNG stream --
    the last proved by stepping both worlds one further tick with nothing
    forced and getting back the same tick number and checksum."""
    w1 = world_factory(n_regions=6, seed=4242)
    set_faction(lib, w1, 0, OMArchetype.CONQUEROR, budget=120.0, tech=10.0, confidence=6.0)
    set_faction(lib, w1, 1, OMArchetype.FORTIFIER, budget=80.0, tech=5.0, confidence=4.0)
    set_stance(lib, w1, 0, 1, OMStance.COOPERATIVE, both_ways=True)
    for idx in range(6):
        set_region(lib, w1, idx, tier=OMTier.HOME, military=40.0 + idx, economy=45.0 + idx,
                    tension=5.0 + idx, population=45.0 + idx, faction_id=idx % 2)
        set_owner(lib, w1, idx, idx % 2, held_since=-1)
    set_edge(lib, w1, 0, 1, OMEdge.BOTH)
    set_edge(lib, w1, 2, 3, OMEdge.BOTH)

    load_launch_events(lib, w1)
    tid = template_id(lib, w1, "Emergency Levy")
    tag = queue_external(lib, w1, region_idx=4, tid=tid, due_tick=1, probability=1.0,
                          source_faction=-1, chain_length=0)
    assert tag >= 0, "fixture setup: the external spawn must be accepted"

    inject_intent(lib, w1, 0, OMAction.ATTACK, 1, 0, 30.0, OMMode.TELEGRAPH)
    lib.om_world_step(w1)
    lib.om_world_step(w1)  # tick 2: declared_tick 1 + 3 hasn't arrived, still pending

    telegraphs_before = read_telegraphs(lib, w1)
    assert len(telegraphs_before) >= 1, "fixture setup: the telegraphed attack must still be pending"
    chain_before = lib.om_chain_counter(w1)
    assert chain_before > 0, "fixture setup: the external spawn above must have advanced the chain counter"

    buf, size = _save(lib, w1)

    w2 = world_factory(n_regions=6, seed=13)  # different seed, otherwise untouched: load must overwrite it fully
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"a clean save buffer must load, rc={rc}"

    for idx in range(6):
        for field in (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION):
            assert lib.om_region_field(w2, idx, field) == pytest.approx(
                lib.om_region_field(w1, idx, field), abs=1e-9)
        assert lib.om_region_owner(w2, idx) == lib.om_region_owner(w1, idx)

    for fid in (0, 1):
        assert lib.om_faction_budget(w2, fid) == pytest.approx(lib.om_faction_budget(w1, fid), abs=1e-9)
    assert lib.om_faction_stance(w2, 0, 1) == lib.om_faction_stance(w1, 0, 1) == OMStance.COOPERATIVE

    telegraphs_after = read_telegraphs(lib, w2)
    assert len(telegraphs_after) == len(telegraphs_before)
    for after, before in zip(telegraphs_after, telegraphs_before):
        assert after.declared_tick == before.declared_tick
        assert after.attacker == before.attacker
        assert after.target_idx == before.target_idx
        assert after.source_idx == before.source_idx
        assert after.commit == pytest.approx(before.commit, abs=1e-9)

    assert lib.om_chain_counter(w2) == chain_before

    # The RNG-state proof: nothing is forced from here, so the next step draws
    # straight from each world's own live PCG32 stream. If that stream was not
    # restored byte-for-byte, the two worlds' agent decisions -- and therefore
    # their region fields -- diverge from this tick on.
    tick1 = lib.om_world_step(w1)
    tick2 = lib.om_world_step(w2)
    assert tick2 == tick1
    assert lib.om_world_get_state_checksum(w2) == lib.om_world_get_state_checksum(w1)


def test_R_111_03_wrong_version_word_refused_target_unchanged(lib, world_factory):
    """Given a save from a different game version, When loaded, Then it is
    refused (a non-zero return; the human-readable message naming the two
    versions is a client-side concern with no C accessor -- Q-111-02 -- so
    this test checks only the return code and the untouched target)."""
    w_src = _fixture_world(lib, world_factory, seed=606)
    for _ in range(5):
        lib.om_world_step(w_src)
    buf, size = _save(lib, w_src)

    corrupted = (ctypes.c_uint8 * size)(*buf)
    for i in range(4):
        corrupted[i] ^= 0xFF  # flip the first 4 bytes (the presumed version word); guaranteed to differ

    w_target = world_factory(n_regions=4, seed=707)
    checksum_before = lib.om_world_get_state_checksum(w_target)

    rc = _load(lib, w_target, corrupted, size)
    assert rc != 0, "a version-mismatched buffer must be refused with a non-zero return"
    assert lib.om_world_get_state_checksum(w_target) == checksum_before, \
        "a refused load must not touch the target world"


def test_R_111_03_truncated_buffer_refused(lib, world_factory):
    """Given a save buffer cut short, When loaded, Then it is refused with a
    non-zero return -- the load path must validate length, not trust it."""
    w_src = _fixture_world(lib, world_factory, seed=808)
    for _ in range(5):
        lib.om_world_step(w_src)
    buf, size = _save(lib, w_src)
    assert size > 8, "fixture setup: a real save must be more than a version word"

    half = size // 2
    truncated = (ctypes.c_uint8 * half)(*buf[:half])

    w_target = world_factory(n_regions=4, seed=909)
    rc = _load(lib, w_target, truncated, half)
    assert rc != 0, "a truncated buffer must be refused with a non-zero return"


def test_R_111_02_save_load_save_gives_identical_bytes(lib, world_factory):
    """Given a save, a load into a fresh world, and a second save of that
    loaded world, Then the two save buffers are byte-identical -- load loses
    nothing the next save would need to reproduce."""
    w1 = _fixture_world(lib, world_factory, seed=1010)
    for _ in range(5):
        lib.om_world_step(w1)
    buf1, size1 = _save(lib, w1)
    # A hard-stub om_save_state_size of 0 would make the buffer empty and the
    # write/load/second-save below no-ops, matching trivially.
    assert size1 > 0

    w2 = world_factory(n_regions=4, seed=2020)
    rc = _load(lib, w2, buf1, size1)
    assert rc == 0, f"a clean save buffer must load, rc={rc}"
    buf2, size2 = _save(lib, w2)

    assert size1 == size2
    assert bytes(buf1) == bytes(buf2)


def test_R_111_02_integration_two_hundred_ticks_save_two_hundred_more_checksums_match(lib, world_factory):
    """Integration: FACTIONS, EVENTS, FRICTION, ADMIN_REVOLTS, DRIFT together
    (E-16's own mvp_features.toml default, with the launch event library
    loaded so EVENTS is not just a flag) across 200 ticks, a save/load
    boundary, then 200 more ticks on both the original and the loaded copy;
    om_world_get_state_checksum must agree at every om_checksum_cadence()
    tick (R-020-03) past the boundary -- the save/load boundary must be
    transparent to the full multi-system tick sequence at scale, not only to
    a small hand-built isolation fixture."""
    n_regions = 10
    w1 = world_factory(n_regions=n_regions, seed=112233)
    load_launch_events(lib, w1)
    for fid, arch in enumerate((OMArchetype.CONQUEROR, OMArchetype.FORTIFIER, OMArchetype.OPPORTUNIST)):
        set_faction(lib, w1, fid, arch, budget=100.0, tech=10.0, confidence=5.0)
    for idx in range(n_regions):
        set_region(lib, w1, idx, tier=OMTier.HOME, military=45.0, economy=45.0,
                    tension=10.0, population=45.0, faction_id=idx % 3)
        set_owner(lib, w1, idx, idx % 3, held_since=-1)
    for a in range(n_regions):
        set_edge(lib, w1, a, (a + 1) % n_regions, OMEdge.BOTH)

    for _ in range(200):
        lib.om_world_step(w1)

    buf, size = _save(lib, w1)

    w2 = world_factory(n_regions=n_regions, seed=998877)
    load_launch_events(lib, w2)
    rc = _load(lib, w2, buf, size)
    assert rc == 0, f"a clean save buffer must load, rc={rc}"

    cadence = lib.om_checksum_cadence()
    for step in range(1, 201):
        lib.om_world_step(w1)
        lib.om_world_step(w2)
        if step % cadence == 0:
            assert lib.om_world_get_state_checksum(w1) == lib.om_world_get_state_checksum(w2), \
                f"checksum diverged {step} ticks past the save boundary"


def test_control_R_111_02_om_bug_save_skips_rng_state_trips_the_detector(dbg, dbg_world_factory):
    """Positive control for the RNG-state leg of
    test_R_111_02_load_restores_tick_regions_factions_telegraphs_chain_and_rng
    above: OM_BUG_SAVE_SKIPS_RNG_STATE (id 1600, save.c's reserved range --
    two-day-push brief, decision 6) skips writing or restoring the PCG32
    stream through save/load. Continuing the original world naturally must
    then diverge from continuing a freshly loaded copy, proving the
    checksum-equality assertion above would actually catch this fault
    (CLAUDE.md: "every detector ships with a positive control")."""
    w = dbg_world_factory(n_regions=4, seed=2468)
    dbg.om_debug_inject(w, _OM_BUG_SAVE_SKIPS_RNG_STATE)
    set_faction(dbg, w, 0, OMArchetype.CONQUEROR, budget=100.0, tech=10.0, confidence=5.0)
    set_faction(dbg, w, 1, OMArchetype.FORTIFIER, budget=80.0, tech=5.0, confidence=5.0)
    for idx in range(4):
        set_region(dbg, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0,
                    tension=10.0, population=50.0, faction_id=idx % 2)
        set_owner(dbg, w, idx, idx % 2, held_since=-1)
    set_edge(dbg, w, 0, 1, OMEdge.BOTH)
    # See docs/northstar/proving_ground/evidence/push_2026-09-22/test_defects_fixed.md:
    # this fixture originally drew no RNG at all in its 5 ticks (no events
    # loaded, no intents, no adjacent hostiles for friction), so a save that
    # drops the RNG state changed nothing -- a dead control. events.c's own
    # module state does not round-trip through save/load yet (save.c's own
    # header comment: "events.c's om_chain_counter lives in events_state and
    # does not round-trip until events.c gets its own hooks"), so routing
    # this fixture's RNG draw through a launch template (as
    # test_R_111_02_load_restores_tick_regions_factions_telegraphs_chain_and_rng
    # above does) would trip on that gap instead: a same-tick SURPRISE attack
    # resolves through om_step_resolve (csrc/resolve.c), which draws the real
    # PCG32 stream and applies the result straight to military/economy/tension
    # the same tick, with no module-level state of its own to round-trip.
    for _ in range(5):
        inject_intent(dbg, w, 0, OMAction.ATTACK, 1, 0, 30.0, OMMode.SURPRISE)
        dbg.om_world_step(w)  # advance the live RNG stream, one resolved attack roll per tick

    buf, size = _save(dbg, w)

    inject_intent(dbg, w, 0, OMAction.ATTACK, 1, 0, 30.0, OMMode.SURPRISE)
    reference_tick = dbg.om_world_step(w)
    reference_checksum = dbg.om_world_get_state_checksum(w)

    w_loaded = dbg_world_factory(n_regions=4, seed=999999)
    rc = _load(dbg, w_loaded, buf, size)
    assert rc == 0, f"the bug skips RNG state, not the whole load, rc={rc}"
    inject_intent(dbg, w_loaded, 0, OMAction.ATTACK, 1, 0, 30.0, OMMode.SURPRISE)
    loaded_tick = dbg.om_world_step(w_loaded)
    loaded_checksum = dbg.om_world_get_state_checksum(w_loaded)

    assert loaded_tick == reference_tick
    assert loaded_checksum != reference_checksum, (
        "OM_BUG_SAVE_SKIPS_RNG_STATE must desync the RNG stream through a save; "
        "identical checksums here means this detector would not have caught it"
    )
