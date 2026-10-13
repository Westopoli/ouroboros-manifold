"""ALG-44 Lifecycle phase (docs/bible/algorithms.md; E-07 S-053, R-053-01..07).

Rule, given a faction's recent event list, first match wins in this order:
  fragmentation  (admin events + revolts + reversions) / max(1, len(events)) >= 0.02
  overextension  regions * REGION_MAINTENANCE_COST (8.0) / sum(economy) > 0.4
  conflict       attacks / len >= 0.05
  expansion      distinct empty regions bordering the faction / inhabited regions >= 0.3
  consolidation  any colonization and no attack
  equilibrium    otherwise, and for a faction with zero regions.

The first group feeds the window through om_faction_set_event_window_counts (the only way a window
enters the sim) and checks om_faction_phase against a reference function written from the rule above.
The last test is the wiring check (CLAUDE.md 'wired, not just tested'): epic E-07 says the window
comes from the tick log and the phase is consumed by E-09 and E-10, so a faction that really attacked
must read as conflict without any test hand-feeding the counts. Positive control: a perturbed input
flips the phase, and the reference rejects a wrong order.
"""
import pytest

from conftest import (
    OMArchetype,
    OMEdge,
    OMFeature,
    OMStance,
    OMTier,
    force_draws,
    isolate_agents,
    read_attacks,
    set_edge,
    set_faction,
    set_owner,
    set_region,
    set_stance,
    set_tech_multipliers,
)

FRAG, OVER, CONFLICT, EXPANSION, CONSOLIDATION, EQUILIBRIUM = 0, 1, 2, 3, 4, 5
MAINTENANCE = 8.0


def phase_ref(total, revolts, attacks, colonizations, n_regions, sum_e, empty_bordering, inhabited):
    if n_regions == 0:
        return EQUILIBRIUM
    denom = max(1, total)
    if revolts / denom >= 0.02:
        return FRAG
    if sum_e > 0 and n_regions * MAINTENANCE / sum_e > 0.4:
        return OVER
    if attacks / denom >= 0.05:
        return CONFLICT
    if inhabited > 0 and empty_bordering / inhabited >= 0.3:
        return EXPANSION
    if colonizations > 0 and attacks == 0:
        return CONSOLIDATION
    return EQUILIBRIUM


def build(handle, factory, *, econ_each, n_owned=3, other_inhabited=7, empty_bordering=0, window=(0, 0, 0, 0)):
    """Faction 0 owns n_owned regions (economy econ_each); `other_inhabited` inhabited regions belong to faction 1;
    `empty_bordering` empty regions touch region 0 and one empty region touches nothing."""
    n = n_owned + other_inhabited + empty_bordering + 1
    w = factory(n_regions=n)
    isolate_agents(handle, w)
    handle.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    set_faction(handle, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=10.0, confidence=5.0)
    set_faction(handle, w, 1, OMArchetype.DEFAULT, budget=0.0, tech=10.0, confidence=5.0)
    idx = 0
    for _ in range(n_owned):
        set_region(handle, w, idx, tier=OMTier.HOME, military=50.0, economy=econ_each, tension=10.0, population=50.0, faction_id=0)
        set_owner(handle, w, idx, 0, held_since=-1)
        idx += 1
    for _ in range(other_inhabited):
        set_region(handle, w, idx, tier=OMTier.HOME, military=50.0, economy=50.0, tension=10.0, population=50.0, faction_id=1)
        set_owner(handle, w, idx, 1, held_since=-1)
        idx += 1
    for _ in range(empty_bordering):
        set_region(handle, w, idx, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
        set_edge(handle, w, 0, idx, OMEdge.BOTH)
        idx += 1
    set_region(handle, w, idx, tier=OMTier.EMPTY, military=0.0, economy=0.0, tension=0.0, population=0.0, faction_id=-1)
    total, revolts, attacks, colonizations = window
    handle.om_faction_set_event_window_counts(w, 0, total_events=total, revolts=revolts, attacks=attacks,
                                              colonizations=colonizations)
    inhabited = n_owned + other_inhabited
    return w, dict(total=total, revolts=revolts, attacks=attacks, colonizations=colonizations, n_regions=n_owned,
                   sum_e=n_owned * econ_each, empty_bordering=empty_bordering, inhabited=inhabited)


# (name, build kwargs, expected phase from the rule)
SCENARIOS = [
    ("fragmentation at 2/100", dict(econ_each=50.0, window=(100, 2, 0, 0)), FRAG),
    ("not fragmentation at 1/100", dict(econ_each=50.0, window=(100, 1, 0, 0)), EQUILIBRIUM),
    ("fragmentation with an empty window (max(1, len))", dict(econ_each=50.0, window=(0, 1, 0, 0)), FRAG),
    ("overextension 24/40 = 0.6", dict(econ_each=13.3333333333, window=(100, 0, 0, 0)), OVER),
    ("not overextension at exactly 0.4", dict(econ_each=20.0, n_owned=5, window=(100, 0, 0, 0)), EQUILIBRIUM),
    ("overextension just above 0.4", dict(econ_each=19.9, n_owned=5, window=(100, 0, 0, 0)), OVER),
    ("conflict at 5/100", dict(econ_each=50.0, window=(100, 0, 5, 0)), CONFLICT),
    ("not conflict at 4/100", dict(econ_each=50.0, window=(100, 0, 4, 0)), EQUILIBRIUM),
    ("expansion at 3 empty / 10 inhabited", dict(econ_each=50.0, empty_bordering=3, window=(100, 0, 0, 0)), EXPANSION),
    ("not expansion at 2 empty / 10 inhabited", dict(econ_each=50.0, empty_bordering=2, window=(100, 0, 0, 0)), EQUILIBRIUM),
    ("consolidation: colonizations and no attack", dict(econ_each=50.0, window=(100, 0, 0, 3)), CONSOLIDATION),
    ("not consolidation when attacks exist (below the conflict share)", dict(econ_each=50.0, window=(100, 0, 4, 3)), EQUILIBRIUM),
    ("order: fragmentation beats overextension and conflict", dict(econ_each=5.0, window=(100, 5, 50, 0)), FRAG),
    ("order: overextension beats conflict", dict(econ_each=5.0, window=(100, 0, 50, 0)), OVER),
    ("order: conflict beats expansion", dict(econ_each=50.0, empty_bordering=3, window=(100, 0, 50, 0)), CONFLICT),
    ("order: expansion beats consolidation", dict(econ_each=50.0, empty_bordering=3, window=(100, 0, 0, 4)), EXPANSION),
]


@pytest.mark.parametrize("name,kwargs,expected", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_ALG_44_first_matching_check_wins(lib, world_factory, name, kwargs, expected):
    w, inputs = build(lib, world_factory, **kwargs)
    assert phase_ref(**inputs) == expected, "the reference and the scenario agree (written from the rule)"
    assert lib.om_faction_phase(w, 0) == expected


def test_ALG_44_a_faction_with_no_regions_is_equilibrium_whatever_the_window(lib, world_factory):
    w, _ = build(lib, world_factory, econ_each=50.0, window=(100, 50, 50, 50))
    set_faction(lib, w, 2, OMArchetype.DEFAULT, budget=0.0, tech=10.0, confidence=5.0)
    lib.om_faction_set_event_window_counts(w, 2, total_events=100, revolts=50, attacks=50, colonizations=50)
    assert lib.om_faction_phase(w, 2) == EQUILIBRIUM
    assert lib.om_faction_phase(w, 0) == FRAG


def test_control_ALG_44_detector_fires(lib, world_factory):
    """Positive control: moving one input across its threshold changes the phase, and the wrong order is rejected."""
    w_a, _ = build(lib, world_factory, econ_each=50.0, window=(100, 0, 5, 0))
    w_b, _ = build(lib, world_factory, econ_each=50.0, window=(100, 0, 4, 0))
    assert lib.om_faction_phase(w_a, 0) == CONFLICT and lib.om_faction_phase(w_b, 0) == EQUILIBRIUM
    w_c, _ = build(lib, world_factory, econ_each=5.0, window=(100, 0, 50, 0))
    with pytest.raises(AssertionError):
        assert lib.om_faction_phase(w_c, 0) == CONFLICT     # overextension must win over conflict


def _live_war(handle, factory, attack):
    """Faction 0 (strong, rich) attacks faction 1 (weak) each tick when `attack`; otherwise faction 0 has no budget."""
    w = factory(n_regions=3)
    isolate_agents(handle, w)
    handle.om_world_set_feature(w, OMFeature.LIFECYCLE, 1)
    set_faction(handle, w, 0, OMArchetype.CONQUEROR, budget=400.0 if attack else 0.0, tech=10.0, confidence=2.0)
    set_faction(handle, w, 1, OMArchetype.DEFAULT, budget=0.0, tech=10.0, confidence=5.0)
    for f in (0, 1):
        set_tech_multipliers(handle, w, f, 1.0, 1.0, 1.0)
    set_stance(handle, w, 0, 1, OMStance.HOSTILE)
    set_region(handle, w, 0, tier=OMTier.HOME, military=90.0, economy=80.0, tension=10.0, population=60.0, faction_id=0)
    set_owner(handle, w, 0, 0, held_since=-1)
    set_region(handle, w, 1, tier=OMTier.HOME, military=60.0, economy=60.0, tension=10.0, population=60.0, faction_id=1)
    set_owner(handle, w, 1, 1, held_since=-1)
    set_region(handle, w, 2, tier=OMTier.HOME, military=60.0, economy=60.0, tension=10.0, population=60.0, faction_id=1)
    set_owner(handle, w, 2, 1, held_since=-1)
    set_edge(handle, w, 0, 1, OMEdge.BOTH)
    set_edge(handle, w, 0, 2, OMEdge.BOTH)
    attacks_seen = 0
    for _ in range(8):
        handle.om_world_step(w)
        attacks_seen += sum(1 for a in read_attacks(handle, w) if a.attacker == 0)
    return w, attacks_seen


def test_ALG_44_phase_follows_what_the_faction_actually_did(lib, world_factory):
    """WIRED: faction 0 attacked over eight ticks and was never in fragmentation or overextension; its phase reads conflict with no hand-fed window."""
    w, attacks = _live_war(lib, world_factory, attack=True)
    assert attacks >= 2, f"fixture check: faction 0 must really attack (saw {attacks})"
    assert lib.om_faction_phase(w, 0) == CONFLICT


def test_control_ALG_44_a_quiet_faction_is_not_in_conflict(lib, world_factory):
    w, attacks = _live_war(lib, world_factory, attack=False)
    assert attacks == 0
    assert lib.om_faction_phase(w, 0) != CONFLICT
