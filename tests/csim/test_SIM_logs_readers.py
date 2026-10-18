"""SIM-LOGS, the readers: what the mission generator reads from the logs.

Spec: docs/northstar/plans/2026-10-15-sim-logs-spec.md rev 4 ("Readers"), with the Architect's rulings of
2026-10-18 recorded there: W1 (a) the window is `tick > window_start`, everything when `window_start` is 0;
W2 (a) a resolved attack in the window or a pending telegraph triggers Defensive Stand and the hostile-neighbour
shortcut goes; W4 (a) Containment counts colonisations (kind 5) by the contained faction into regions adjacent to
r, >= 2, and the revolt-or-archetype gate goes.

How the logs are filled here. The spec gives no setter (the only writers are the call sites). A reader test needs
exact entries (an attacker, a tick, a kind), so the fixture builds the world through the real setters, saves it,
splices the log block of the save (the layout the ring test's docstring fixes: window_start i64, last_mission_region
i32, the three n as u32, then the entries oldest first, then times_run) and loads it into a fresh world. The
loaded logs are read back through the accessors and compared with what was spliced (a layout mismatch fails there,
by name, not as a reader failure). If the saved block is length-prefixed the prefix is corrected (checked for u32
and u64); that is an assumption about save.c the builder must either meet or tell the Architect.

RED today: the log block is not in the save, so every test that splices fails at `block_header` with
"the saved block's header was not found". Two groups fail by assertion on today's tree instead (the old arm still
fires): test_hostile_neighbour_alone_*, test_multi_front_hostile_neighbours_alone_*, test_containment_*_gate_*,
and the force/urgency/telegraph tests whose expected number differs from today's. Tests that need no new symbol and
are green today are marked CONTROL.

Names the spec leaves implicit, decided here:
  * The archetype a refresh reads `times_run` for: relevance(r, archetype) uses times_run[slot(seated)][archetype]
    of the archetype asked, so a lineage that ran Defensive Stand 3 times lifts Defensive Stand's relevance by 0.3
    and leaves Assault's alone (ALG-55: `archetype_count` is per archetype). The spec says "from times_run[..][archetype]"
    at mission.c:2261 where refresh has no archetype; the builder may store the row on the region context, but
    om_mission_compute_relevance(w, r, archetype) must show the per-archetype value after a refresh.
  * "times_run lowers fit" in the brief reads as the ALG-55 formula says: fit = min(1, times_run / 3) RAISES the
    fit term (and relevance). The tests assert the formula.
  * Whether `attack_budget_sum` includes pending telegraph commits is not stated; no test depends on it (the
    pending-plus-logged urgency case is chosen so the clamp hides it).
"""
import ctypes
import struct

import pytest

from conftest import (
    OMAction,
    OMArchetype,
    OMEdge,
    OMMode,
    OMStance,
    OMTier,
    inject_intent,
    isolate_agents,
    read_telegraphs,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)
from test_E10_S072_orders_come_from_where_the_world_hurts import (
    OMMissionArchetype as A,
    read_mission_candidates,
)
from test_E10_S072_a2_refresh_telegraph_defensive_stand import (
    ATTACKED,
    QUIET,
    _telegraphed_frontier,
)
from test_SIM_logs_ring import (
    OM_CONQ_ATTACK,
    OM_CONQ_ABSORPTION,
    OM_CONQ_COLONISATION,
    OM_CONQ_MISSION,
    OM_CONQ_REVERSION,
    OM_CONQ_REVOLT,
    bind_logs,
    load_bytes,
    read_log,
    save_bytes,
)

REVOLT_TIDS = [3, 5, 9, 21, 22, 23, 24, 25]   # TID_REGIONAL_REVOLT .. TID_ADMIN_BREAKAWAY, spec "recent_revolt_events"
NON_REVOLT_TIDS = [0, 1, 2, 4, 6, 7, 8, 10, 20]
OM_BUDGET_TO_POWER_SCALE = 300                # csrc/om_constants.h:428
URGENCY_CONFLICT_ATTACK = 0.4 * 0.5           # URGENCY_CONFLICT_WEIGHT x CONFLICT_ATTACK_TERM_WEIGHT (mission.c:1470-1473)
URGENCY_CHAIN = 0.2                           # URGENCY_CHAIN_WEIGHT
URGENCY_LOSS = 0.4 * 0.3                      # URGENCY_CONFLICT_WEIGHT x CONFLICT_LOSS_TERM_WEIGHT
TIMES_RUN_BYTES = 512 * 10 * 2                # OM_SIMLOG_MAX_LINEAGES x OM_MISSION_N_ARCHETYPES x u16
EMPTY_BLOCK_LEN = 24 + TIMES_RUN_BYTES


# ---------------------------------------------------------------- splicing the log block

def block_header(data, ns=(0, 0, 0)):
    pat = struct.pack("<qiIII", 0, -1, *ns)
    n = data.count(pat)
    assert n == 1, ("the saved block's header was not found exactly once (found %d): the build writes no SIM-LOGS "
                    "block, or lays it out differently from the ring test's docstring" % n)
    return data.find(pat)


def splice(data, attacks=(), conquests=(), events=(), window_start=0, times_run=None):
    """Replace the empty log block of `data` with one holding the given entries.
    attacks: (tick, attacker, target_region, commit); conquests: (tick, region, old, new, kind);
    events: (tick, region, template_id, chain_tag, creates_faction); times_run: {(slot, archetype): count}."""
    h = block_header(data)
    body = struct.pack("<qiIII", window_start, -1, len(attacks), len(conquests), len(events))
    body += b"".join(struct.pack("<qiid", *a) for a in attacks)
    body += b"".join(struct.pack("<qiiii", *c) for c in conquests)
    body += b"".join(struct.pack("<qiiii", *e) for e in events)
    tail = bytearray(data[h + 24: h + 24 + TIMES_RUN_BYTES])
    assert len(tail) == TIMES_RUN_BYTES, "the times_run rows do not follow the header of an empty block"
    for (slot, arch), v in (times_run or {}).items():
        struct.pack_into("<H", tail, (slot * 10 + arch) * 2, v)
    out = bytearray(data[:h]) + body + tail + data[h + EMPTY_BLOCK_LEN:]
    new_len = len(body) + TIMES_RUN_BYTES
    if struct.unpack_from("<I", data, h - 4)[0] == EMPTY_BLOCK_LEN:        # a u32 length prefix
        struct.pack_into("<I", out, h - 4, new_len)
    elif h >= 8 and struct.unpack_from("<Q", data, h - 8)[0] == EMPTY_BLOCK_LEN:   # a u64 length prefix
        struct.pack_into("<Q", out, h - 8, new_len)
    return bytes(out)


def with_logs(lib, wf, w, n_regions, seed=1, *, attacks=(), conquests=(), events=(), window_start=0, times_run=None):
    """w (an empty-log world) -> a fresh world carrying exactly these log entries."""
    data = splice(save_bytes(lib, w), attacks, conquests, events, window_start, times_run)
    w2 = wf(n_regions=n_regions, seed=seed)
    assert load_bytes(lib, w2, data) == 0, "the spliced save was refused: layout or validation differs from the ring test's docstring"
    bind_logs(lib)
    assert read_log(lib, w2, "attack") == [(a[0], a[1], a[2], pytest.approx(a[3])) for a in attacks]
    assert read_log(lib, w2, "conquest") == [tuple(c) for c in conquests]
    assert read_log(lib, w2, "event") == [tuple(e) for e in events]
    assert lib.om_simlog_window_start(w2) == window_start
    return w2


# ---------------------------------------------------------------- worlds

def build(lib, wf, owners, edges, *, stances=None, mil=None, archetypes=None, n_factions=None):
    """Regions 0..n-1 with owners[i]; faction 0 is the player. Every region military 50, economy 50, tension 20,
    population 50 (a healthy region: the deficit term is small and no stability gate fires) unless `mil` says."""
    n = len(owners)
    w = wf(n_regions=n)
    nf = n_factions or (max(owners) + 1)
    archetypes = archetypes or {}
    for f in range(nf):
        set_faction(lib, w, f, archetypes.get(f, OMArchetype.PLAYER if f == 0 else OMArchetype.CONQUEROR),
                    budget=50.0 if f == 0 else 100.0)
        set_tech_multipliers(lib, w, f, 1.0, 1.0, 1.0)
    for (a, b), s in (stances or {}).items():
        set_stance(lib, w, a, b, s)
    for r in range(n):
        set_region(lib, w, r, tier=OMTier.HOME, military=(mil or {}).get(r, 50.0), economy=50.0, tension=20.0,
                   population=50.0)
        set_owner(lib, w, r, owners[r], held_since=-1)
    for a, b in edges:
        set_edge(lib, w, a, b, OMEdge.BOTH)
    return w


def refresh(lib, w, region):
    lib.om_mission_refresh_context.argtypes = [type(w), ctypes.c_int32]
    lib.om_mission_refresh_context.restype = None
    lib.om_mission_refresh_context(w, region)


def pool(lib, w, n_regions):
    for r in range(n_regions):
        refresh(lib, w, r)
    lib.om_mission_build_candidate_pool(w)
    return {(c.region_idx, c.archetype) for c in read_mission_candidates(lib, w)}


def urgency_delta(lib, w, region, archetype=A.DEFENSIVE_STAND):
    before = lib.om_mission_compute_urgency(w, region, archetype)
    refresh(lib, w, region)
    return lib.om_mission_compute_urgency(w, region, archetype) - before


def telegraph_on(lib, w, attacker, target, source, commit=50.0):
    isolate_agents(lib, w)
    inject_intent(lib, w, attacker, OMAction.ATTACK, target, source, commit, mode=OMMode.TELEGRAPH)
    lib.om_world_step(w)
    assert any(t.target_idx == target for t in read_telegraphs(lib, w)), "fixture: telegraph not pending"


H = OMStance.HOSTILE
N = OMStance.NEUTRAL


def hostile_frontier(lib, wf):
    """Player region 0 (military 30) beside faction 1's region 1 (military 60), stance hostile. No attack anywhere.
    Siege Breaking fires on region 0 (its H(r, 50) arm), which proves the neighbour counts as hostile."""
    return build(lib, wf, [0, 1, 1, 1], [(0, 1)], stances={(0, 1): H}, mil={0: 30.0, 1: 60.0})


# ---------------------------------------------------------------- Defensive Stand (W2 a) and the window (W1 a)

def test_hostile_neighbour_alone_does_not_enter_defensive_stand(lib, world_factory):
    """TD-SIM-1: the hostile-neighbour half of the arm goes. CONTROL half: Siege Breaking, which reads the same
    neighbour, still fires, so the fixture's neighbour is hostile."""
    w = hostile_frontier(lib, world_factory)
    p = pool(lib, w, 4)
    assert (0, A.SIEGE_BREAKING) in p, "control: the fixture's neighbour is a hostile neighbour"
    assert (0, A.DEFENSIVE_STAND) not in p


def test_logged_attack_by_a_non_player_enters_defensive_stand(lib, world_factory):
    w = with_logs(lib, world_factory, hostile_frontier(lib, world_factory), 4, attacks=[(5, 1, 0, 70.0)])
    assert (0, A.DEFENSIVE_STAND) in pool(lib, w, 4)


def test_logged_attack_by_the_player_does_not_enter_defensive_stand(lib, world_factory):
    w = with_logs(lib, world_factory, hostile_frontier(lib, world_factory), 4, attacks=[(5, 0, 0, 70.0)])
    assert (0, A.DEFENSIVE_STAND) not in pool(lib, w, 4)


def test_logged_attack_on_another_region_does_not_enter_defensive_stand(lib, world_factory):
    w = with_logs(lib, world_factory, hostile_frontier(lib, world_factory), 4, attacks=[(5, 1, 2, 70.0)])
    assert (0, A.DEFENSIVE_STAND) not in pool(lib, w, 4)


def test_pending_telegraph_enters_defensive_stand_and_its_quiet_twin_does_not(lib, world_factory):
    """The positive control the brief names ('a context with pending_attacks 1 enters Defensive Stand') and the shape
    test_E10_S072_a2_refresh_telegraph_defensive_stand.py keeps: the attacked frontier enters; the twin with the same
    hostile neighbour and no telegraph does not (today it does, through the hostile-neighbour arm)."""
    w = _telegraphed_frontier(lib, world_factory)
    p = pool(lib, w, 4)
    assert (ATTACKED, A.DEFENSIVE_STAND) in p
    assert (QUIET, A.DEFENSIVE_STAND) not in p


@pytest.mark.parametrize("window_start,tick,counts", [
    (100, 99, False), (100, 100, False), (100, 101, True), (0, 0, True), (0, 1, True)],
    ids=["before", "at_window_start", "after", "ws0_tick0_counts", "ws0_tick1_counts"])
def test_window_decides_whether_a_logged_attack_counts(lib, world_factory, window_start, tick, counts):
    w = with_logs(lib, world_factory, hostile_frontier(lib, world_factory), 4,
                  attacks=[(tick, 1, 0, 70.0)], window_start=window_start)
    assert ((0, A.DEFENSIVE_STAND) in pool(lib, w, 4)) is counts


# ---------------------------------------------------------------- Multi-Front

def two_fronts(lib, wf):
    return build(lib, wf, [0, 1, 2, 1], [(0, 1), (0, 2)], stances={(0, 1): H, (0, 2): H}, mil={0: 30.0, 1: 60.0, 2: 60.0})


def test_multi_front_hostile_neighbours_alone_are_not_sources(lib, world_factory):
    w = two_fronts(lib, world_factory)
    p = pool(lib, w, 4)
    assert (0, A.SIEGE_BREAKING) in p, "control: both neighbours are hostile neighbours"
    assert (0, A.MULTI_FRONT_DEFENSE) not in p


def test_multi_front_two_distinct_logged_attackers(lib, world_factory):
    w = with_logs(lib, world_factory, two_fronts(lib, world_factory), 4, attacks=[(5, 1, 0, 70.0), (6, 2, 0, 40.0)])
    assert (0, A.MULTI_FRONT_DEFENSE) in pool(lib, w, 4)


@pytest.mark.parametrize("attacks", [
    [(5, 1, 0, 70.0), (6, 1, 0, 40.0)],          # one attacker twice
    [(5, 0, 0, 70.0), (6, 1, 0, 40.0)],          # the player is not a source
    [(5, 1, 0, 70.0)],                           # one attacker
], ids=["same_attacker_twice", "player_plus_one", "single"])
def test_multi_front_needs_two_distinct_non_player_attackers(lib, world_factory, attacks):
    w = with_logs(lib, world_factory, two_fronts(lib, world_factory), 4, attacks=attacks)
    assert (0, A.MULTI_FRONT_DEFENSE) not in pool(lib, w, 4)


def test_multi_front_counts_a_pending_attacker_with_a_logged_one(lib, world_factory):
    base = two_fronts(lib, world_factory)
    telegraph_on(lib, base, 2, 0, 2)
    w = with_logs(lib, world_factory, base, 4, attacks=[(5, 1, 0, 70.0)])
    assert len(read_telegraphs(lib, w)) == 1, "fixture: the telegraph survives the save"
    assert (0, A.MULTI_FRONT_DEFENSE) in pool(lib, w, 4)


def test_multi_front_pending_and_logged_from_the_same_attacker_is_one_source(lib, world_factory):
    base = two_fronts(lib, world_factory)
    telegraph_on(lib, base, 2, 0, 2)
    w = with_logs(lib, world_factory, base, 4, attacks=[(5, 2, 0, 70.0)])
    assert (0, A.MULTI_FRONT_DEFENSE) not in pool(lib, w, 4)


# ---------------------------------------------------------------- Interception (as today)

def test_interception_pending_without_a_hostile_neighbour_CONTROL(lib, world_factory):
    w = build(lib, world_factory, [0, 1], [(0, 1)], stances={(0, 1): N})
    telegraph_on(lib, w, 1, 0, 1)
    p = pool(lib, w, 2)
    assert (0, A.INTERCEPTION) in p
    assert (0, A.DEFENSIVE_STAND) in p


def test_interception_not_with_a_hostile_neighbour_CONTROL(lib, world_factory):
    w = build(lib, world_factory, [0, 1], [(0, 1)], stances={(0, 1): H}, mil={1: 60.0})
    telegraph_on(lib, w, 1, 0, 1)
    p = pool(lib, w, 2)
    assert (0, A.INTERCEPTION) not in p
    assert (0, A.DEFENSIVE_STAND) in p


def test_interception_needs_a_pending_attack_not_a_logged_one(lib, world_factory):
    w = with_logs(lib, world_factory, build(lib, world_factory, [0, 1], [(0, 1)], stances={(0, 1): N}), 2,
                  attacks=[(5, 1, 0, 70.0)])
    p = pool(lib, w, 2)
    assert (0, A.DEFENSIVE_STAND) in p
    assert (0, A.INTERCEPTION) not in p


# ---------------------------------------------------------------- Reconquest

def lost_region_world(lib, wf):
    return build(lib, wf, [0, 1, 1], [(0, 1), (1, 2)], stances={(0, 1): N})


@pytest.mark.parametrize("kind,fires", [
    (OM_CONQ_ATTACK, True), (OM_CONQ_MISSION, True),
    (OM_CONQ_REVOLT, False), (OM_CONQ_REVERSION, False), (OM_CONQ_ABSORPTION, False)],
    ids=["attack", "mission", "revolt", "reversion", "absorption"])
def test_reconquest_on_a_logged_conquest_of_the_players_region(lib, world_factory, kind, fires):
    w = with_logs(lib, world_factory, lost_region_world(lib, world_factory), 3, conquests=[(5, 1, 0, 1, kind)])
    assert ((1, A.RECONQUEST) in pool(lib, w, 3)) is fires


def test_reconquest_not_when_the_old_owner_was_not_the_player(lib, world_factory):
    w = with_logs(lib, world_factory, lost_region_world(lib, world_factory), 3, conquests=[(5, 1, 2, 1, OM_CONQ_ATTACK)])
    assert (1, A.RECONQUEST) not in pool(lib, w, 3)


def test_reconquest_does_not_read_previous_owner_alone(lib, world_factory):
    """The previous_owner walk goes (spec: Reconquest is the conquest log). Contradicts any test that sets
    om_region_set_previous_owner and expects Reconquest."""
    w = lost_region_world(lib, world_factory)
    lib.om_region_set_previous_owner(w, 1, 0)
    assert (1, A.RECONQUEST) not in pool(lib, w, 3)


@pytest.mark.parametrize("window_start,tick,fires", [(100, 100, False), (100, 101, True), (0, 0, True)])
def test_reconquest_window(lib, world_factory, window_start, tick, fires):
    w = with_logs(lib, world_factory, lost_region_world(lib, world_factory), 3,
                  conquests=[(tick, 1, 0, 1, OM_CONQ_ATTACK)], window_start=window_start)
    assert ((1, A.RECONQUEST) in pool(lib, w, 3)) is fires


# ---------------------------------------------------------------- adjacent-lost (urgency)

def around_the_player(lib, wf):
    return build(lib, wf, [0, 1, 1], [(0, 1), (0, 2)], stances={(0, 1): N, (0, 2): N})


@pytest.mark.parametrize("conquests,lost", [
    ([(5, 1, 0, 1, OM_CONQ_ATTACK)], 1),
    ([(5, 1, 0, 1, OM_CONQ_MISSION)], 1),
    ([(5, 1, 0, 1, OM_CONQ_ATTACK), (6, 2, 0, 1, OM_CONQ_ATTACK)], 2),
    ([(5, 1, 0, 1, OM_CONQ_REVERSION)], 0),
    ([(5, 1, 0, 1, OM_CONQ_REVOLT)], 0),
    ([(5, 1, 2, 1, OM_CONQ_ATTACK)], 0),
    ([(5, 0, 1, 0, OM_CONQ_ATTACK)], 0),
], ids=["attack", "mission", "two_regions", "reversion_ignored", "revolt_ignored", "other_old_owner", "own_region_taken_from_enemy"])
def test_adjacent_lost_counts_a_neighbours_logged_loss(lib, world_factory, conquests, lost):
    """Given the player's neighbours in the conquest log with old_faction == the player, Then the urgency rises by
    0.4 * 0.3 * min(1, 0.5 * lost). TD-SIM-3: the previous_owner walk goes."""
    w = with_logs(lib, world_factory, around_the_player(lib, world_factory), 3, conquests=conquests)
    assert urgency_delta(lib, w, 0) == pytest.approx(URGENCY_LOSS * min(1.0, 0.5 * lost), abs=1e-9)


def test_adjacent_lost_window(lib, world_factory):
    w = with_logs(lib, world_factory, around_the_player(lib, world_factory), 3,
                  conquests=[(100, 1, 0, 1, OM_CONQ_ATTACK)], window_start=100)
    assert urgency_delta(lib, w, 0) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------- Containment (W4 a)

def contained_world(lib, wf):
    """Faction 1 is a Fortifier (passive) and no event has fired. Its region 1 touches the player's 0; its regions
    2 and 3 touch 1; region 4 touches only 3. Faction 2 owns region 5."""
    return build(lib, wf, [0, 1, 1, 1, 1, 2], [(0, 1), (1, 2), (1, 3), (3, 4), (4, 5)], stances={(0, 1): N},
                 archetypes={1: OMArchetype.FORTIFIER})


def colonised(region, new=1, tick=5):
    return (tick, region, -1, new, OM_CONQ_COLONISATION)


@pytest.mark.parametrize("conquests,fires", [
    ([colonised(2), colonised(3)], True),
    ([colonised(2), colonised(2, tick=6)], True),     # a count of entries, as the reference counted
    ([colonised(2)], False),
    ([colonised(2), colonised(4)], False),            # region 4 is not adjacent to region 1
    ([colonised(2, new=2), colonised(3, new=2)], False),   # the wrong faction
    ([(5, 2, 0, 1, OM_CONQ_ATTACK), (6, 3, 0, 1, OM_CONQ_ATTACK)], False),   # attack conquests are not colonisations
], ids=["two", "same_region_twice", "one", "one_not_adjacent", "other_faction", "attack_conquests"])
def test_containment_counts_colonisations_adjacent_to_the_region(lib, world_factory, conquests, fires):
    """No archetype gate, no revolt gate: faction 1 is a Fortifier and the world has no revolt event."""
    w = with_logs(lib, world_factory, contained_world(lib, world_factory), 6, conquests=conquests)
    assert ((1, A.CONTAINMENT) in pool(lib, w, 6)) is fires


def test_containment_window(lib, world_factory):
    w = with_logs(lib, world_factory, contained_world(lib, world_factory), 6,
                  conquests=[colonised(2, tick=100), colonised(3, tick=101)], window_start=100)
    assert (1, A.CONTAINMENT) not in pool(lib, w, 6), "the entry at the window start does not count, one is left"


def test_containment_without_a_log_does_not_fire_for_a_conqueror(lib, world_factory):
    """The revolt-or-archetype gate went: a Conqueror owner with no colonisations is no longer enough."""
    w = build(lib, world_factory, [0, 1, 1, 1], [(0, 1), (1, 2), (1, 3)], stances={(0, 1): N})
    assert (1, A.CONTAINMENT) not in pool(lib, w, 4)


# ---------------------------------------------------------------- urgency: conflict and chain terms

def duel(lib, wf):
    return build(lib, wf, [0, 1], [(0, 1)], stances={(0, 1): N})


@pytest.mark.parametrize("attacks,pressure", [
    ([(5, 1, 0, 90.0)], 0.5 + 90.0 / 600),
    ([(5, 0, 0, 60.0)], 0.5 + 60.0 / 600),                       # the player's own attack counts
    ([(5, 0, 0, 60.0), (6, 1, 0, 90.0)], 1.0),                   # 1.0 + 0.25 clamped
    ([(5, 1, 0, 90.0), (6, 1, 0, 90.0), (7, 1, 0, 90.0)], 1.0),
], ids=["other", "player", "two_clamped", "three_clamped"])
def test_conflict_term_counts_all_attackers(lib, world_factory, attacks, pressure):
    """conflict = clamp(border + 0.5 * min(1, (recent + pending) * 0.5 + budget_sum / 600) + loss)."""
    w = with_logs(lib, world_factory, duel(lib, world_factory), 2, attacks=attacks)
    assert urgency_delta(lib, w, 0) == pytest.approx(URGENCY_CONFLICT_ATTACK * pressure, abs=1e-9)


def test_conflict_term_adds_pending_to_logged(lib, world_factory):
    """One pending (0.5) plus one logged player attack (0.5): the pressure is >= 1 whatever the budget sum includes."""
    base = duel(lib, world_factory)
    telegraph_on(lib, base, 1, 0, 1)
    w = with_logs(lib, world_factory, base, 2, attacks=[(5, 0, 0, 60.0)])
    assert urgency_delta(lib, w, 0) == pytest.approx(URGENCY_CONFLICT_ATTACK * 1.0, abs=1e-9)


def test_conflict_term_window(lib, world_factory):
    w = with_logs(lib, world_factory, duel(lib, world_factory), 2, attacks=[(100, 1, 0, 90.0)], window_start=100)
    assert urgency_delta(lib, w, 0) == pytest.approx(0.0, abs=1e-9)


def event(tick, region, tid):
    return (tick, region, tid, 0, 0)


@pytest.mark.parametrize("tids,n", [
    ([3], 1), ([3, 5], 2), ([9, 21, 22], 3), ([23, 24, 25, 3], 4), ([3, 5, 9, 21, 22, 23, 24, 25], 8),
], ids=["one", "two", "three", "four_capped", "all_eight_capped"])
def test_chain_term_is_0_3_per_revolt_event_capped(lib, world_factory, tids, n):
    w = with_logs(lib, world_factory, duel(lib, world_factory), 2, events=[event(5 + i, 0, t) for i, t in enumerate(tids)])
    assert urgency_delta(lib, w, 0) == pytest.approx(URGENCY_CHAIN * min(1.0, 0.3 * n), abs=1e-9)


def test_chain_term_ignores_other_templates_other_regions_and_the_window(lib, world_factory):
    evs = [event(5 + i, 0, t) for i, t in enumerate(NON_REVOLT_TIDS)] + [event(5, 1, 3), event(100, 0, 3)]
    w = with_logs(lib, world_factory, duel(lib, world_factory), 2, events=evs, window_start=100)
    assert urgency_delta(lib, w, 0) == pytest.approx(0.0, abs=1e-9)


def test_revolt_events_make_counterinsurgency_reachable_from_live_data(lib, world_factory):
    """refresh sets revolt_set unconditionally: Counterinsurgency (owner == player, a revolt event in the region) fires."""
    w = with_logs(lib, world_factory, duel(lib, world_factory), 2, events=[event(5, 0, 3)])
    assert (0, A.COUNTERINSURGENCY) in pool(lib, w, 2)


def test_no_revolt_event_no_counterinsurgency_CONTROL(lib, world_factory):
    assert (0, A.COUNTERINSURGENCY) not in pool(lib, duel(lib, world_factory), 2)


# ---------------------------------------------------------------- force composition: the top non-player attack

def enemy_power_with(lib, wf, attacks):
    w = with_logs(lib, wf, duel(lib, wf), 2, attacks=attacks)
    refresh(lib, w, 0)
    lib.om_mission_setup(w, 0, A.DEFENSIVE_STAND, 0)
    return lib.om_mission_get_enemy_power(w)


def test_force_composition_uses_the_top_attack_not_the_sum(lib, world_factory):
    got = enemy_power_with(lib, world_factory, [(5, 1, 0, 100.0), (6, 1, 0, 300.0)])
    assert got == pytest.approx(300.0 * OM_BUDGET_TO_POWER_SCALE, abs=1e-6), "not the sum (400)"


def test_force_composition_single_attack_control(lib, world_factory):
    assert enemy_power_with(lib, world_factory, [(5, 1, 0, 100.0)]) == pytest.approx(100.0 * OM_BUDGET_TO_POWER_SCALE, abs=1e-6)


def test_force_composition_ignores_the_players_own_attack(lib, world_factory):
    got = enemy_power_with(lib, world_factory, [(5, 0, 0, 500.0), (6, 1, 0, 300.0)])
    assert got == pytest.approx(300.0 * OM_BUDGET_TO_POWER_SCALE, abs=1e-6)


# ---------------------------------------------------------------- times_run (ALG-55 fit)

def lineage_world(lib, wf):
    w = duel(lib, wf)
    lib.om_lineage_create(w, 1, 0)
    lib.om_lineage_record_history_region(w, 1, 0)
    return w


def relevance_after_refresh(lib, w, archetype):
    refresh(lib, w, 0)
    return lib.om_mission_compute_relevance(w, 0, archetype)


@pytest.mark.parametrize("count,fit", [(1, 1 / 3), (2, 2 / 3), (3, 1.0), (7, 1.0)], ids=["1", "2", "3", "7_capped"])
def test_times_run_raises_that_archetypes_fit(lib, world_factory, count, fit):
    """relevance = 0.4 lineage + 0.3 proximity + 0.3 min(1, count / 3). The seated lineage (the only one: id 1,
    slot 0) ran Defensive Stand `count` times; Assault's fit and every other term stay as in the baseline world."""
    base = relevance_after_refresh(lib, lineage_world(lib, world_factory), A.DEFENSIVE_STAND)
    base_assault = relevance_after_refresh(lib, lineage_world(lib, world_factory), A.ASSAULT)
    w = with_logs(lib, world_factory, lineage_world(lib, world_factory), 2, times_run={(0, A.DEFENSIVE_STAND): count})
    lib.om_simlog_times_run.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
    lib.om_simlog_times_run.restype = ctypes.c_uint32
    assert lib.om_simlog_times_run(w, 1, A.DEFENSIVE_STAND) == count, "fixture: slot 0 is lineage 1"
    assert relevance_after_refresh(lib, w, A.DEFENSIVE_STAND) == pytest.approx(base + 0.3 * fit, abs=1e-9)
    assert relevance_after_refresh(lib, w, A.ASSAULT) == pytest.approx(base_assault, abs=1e-9)


def test_times_run_zero_adds_nothing_CONTROL(lib, world_factory):
    w = lineage_world(lib, world_factory)
    assert relevance_after_refresh(lib, w, A.DEFENSIVE_STAND) == relevance_after_refresh(lib, w, A.ASSAULT)
