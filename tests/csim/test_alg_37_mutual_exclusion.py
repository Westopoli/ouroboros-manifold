"""ALG-37 Mutual exclusion (docs/bible/algorithms.md; E-04 S-028 R-028-02, R-028-03, R-028-05, Q-028-01).

Rule: collect every exclusion tag among the region's due entries; for each tag in sorted order,
among entries still resolved that carry the tag keep the one with the highest probability (ties:
one uniform draw, below 0.5 keeps the earlier-queued entry, otherwise the later) and re-queue each
other one with due = tick + randint(1, 2) (one draw per loser). ALG-36 sequences this per region:
exclusion pass, then conditions (skip, no draw), then one probability roll per survivor.

Custom templates (om_events_load) carry the exclusion tags; events are queued with
queue_external so queue order is explicit. Expected values are computed in this file. The last
three tests pin ALG-36's sequencing around the exclusion pass (per-region order; exclusion before
conditions; the re-queued entry keeps its conditions). Positive control: the debug build with
OM_BUG_EXCLUSION_CANCELS (losers dropped instead of re-queued) fails the main assertions.
"""
import pytest

from conftest import (
    OMBugE04,
    OMCond,
    OMExcl,
    OMField,
    OMTier,
    OmEventTemplate,
    force_draws,
    isolate_events,
    queue_external,
    read_delayed,
    read_event_queue,
    read_events,
    read_pruned,
    set_owner,
    set_region,
)


def tmpl(name, excl=OMExcl.NONE, spawns=()):
    t = OmEventTemplate()
    t.name = name.encode()
    t.exclusion_tag = excl
    t.n_spawns = len(spawns)
    for j, sp in enumerate(spawns):
        t.spawns[j].template_id = sp["tid"]
        t.spawns[j].delay_min = sp["lo"]
        t.spawns[j].delay_max = sp["hi"]
        t.spawns[j].probability = sp["p"]
        t.spawns[j].cond_kind = sp.get("ck", OMCond.NONE)
        t.spawns[j].cond_field = sp.get("cf", 0)
        t.spawns[j].cond_value = sp.get("cv", 0.0)
    return t


def load(handle, w, templates):
    arr = (OmEventTemplate * len(templates))(*templates)
    assert handle.om_events_load(w, arr, len(templates)) == 0


def region(handle, w, idx, m=50.0, e=50.0, t=50.0, p=50.0):
    set_region(handle, w, idx, tier=OMTier.HOME, military=m, economy=e, tension=t, population=p)
    set_owner(handle, w, idx, 0, held_since=-1)


def randint_1_2(dd):
    """Python randint(1, 2) from one uniform draw: 1 + floor(2*dd)."""
    return 1 + int(2 * dd)


def _pair(handle, factory, p_first, p_second, draws, tags=(OMExcl.MILITARY_RELIEF, OMExcl.MILITARY_RELIEF)):
    w = factory(n_regions=1)
    isolate_events(handle, w)
    load(handle, w, [tmpl("FIRST", tags[0]), tmpl("SECOND", tags[1])])
    region(handle, w, 0)
    queue_external(handle, w, 0, 0, due_tick=1, probability=p_first)
    queue_external(handle, w, 0, 1, due_tick=1, probability=p_second)
    force_draws(handle, w, draws)
    handle.om_world_step(w)
    return w


def _check_highest_probability_kept(handle, w, dd):
    fired = read_events(handle, w)
    delayed = read_delayed(handle, w)
    assert [e.template_id for e in fired] == [1]                 # SECOND (p 0.7) kept and fired (roll 0.0 <= 0.7)
    assert len(delayed) == 1
    assert delayed[0].template_id == 0 and delayed[0].kept_template_id == 1
    assert delayed[0].new_due == 1 + randint_1_2(dd)
    q = [e for e in read_event_queue(handle, w) if e.template_id == 0]
    assert len(q) == 1 and q[0].due_tick == 1 + randint_1_2(dd)
    assert q[0].probability == pytest.approx(0.3, abs=1e-12)


@pytest.mark.parametrize("dd", [0.0, 0.25, 0.499, 0.5, 0.75, 0.999])
def test_ALG_37_highest_probability_kept_loser_requeued_one_or_two_ticks_on(lib, world_factory, dd):
    w = _pair(lib, world_factory, 0.3, 0.7, [dd, 0.0])
    assert lib.om_rng_forced_remaining(w) == 0
    _check_highest_probability_kept(lib, w, dd)


@pytest.mark.parametrize("tie,keeps", [(0.0, 0), (0.25, 0), (0.499999, 0), (0.5, 1), (0.75, 1), (1.0, 1)])
def test_ALG_37_tie_is_one_draw_below_half_keeps_the_earlier_queued(lib, world_factory, tie, keeps):
    w = _pair(lib, world_factory, 0.5, 0.5, [tie, 0.25, 0.0])
    assert lib.om_rng_forced_remaining(w) == 0, "tie draw, loser draw, winner roll"
    fired = read_events(lib, w)
    delayed = read_delayed(lib, w)
    assert [e.template_id for e in fired] == [keeps]
    assert [d.template_id for d in delayed] == [1 - keeps]
    assert delayed[0].new_due == 1 + randint_1_2(0.25)


def test_ALG_37_tags_are_processed_in_sorted_order(lib, world_factory):
    """Tag-2 pair is queued first, tag-1 pair second; sorted order means the first tie draw (0.25) decides the tag-1 pair and the second (0.75) the tag-2 pair."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load(lib, w, [tmpl("T2_EARLY", OMExcl.POLITICAL_RESOLUTION), tmpl("T2_LATE", OMExcl.POLITICAL_RESOLUTION),
                  tmpl("T1_EARLY", OMExcl.MILITARY_RELIEF), tmpl("T1_LATE", OMExcl.MILITARY_RELIEF)])
    region(lib, w, 0)
    for tid in range(4):
        queue_external(lib, w, 0, tid, due_tick=1, probability=0.5)
    # tag 1: tie 0.25 keeps T1_EARLY(2), loser draw 0.25; tag 2: tie 0.75 keeps T2_LATE(1), loser draw 0.25; rolls 0.0
    force_draws(lib, w, [0.25, 0.25, 0.75, 0.25, 0.0, 0.0])
    lib.om_world_step(w)
    assert lib.om_rng_forced_remaining(w) == 0
    assert sorted(e.template_id for e in read_events(lib, w)) == [1, 2]
    assert sorted(d.template_id for d in read_delayed(lib, w)) == [0, 3]


def test_ALG_37_entries_without_a_shared_tag_both_fire(lib, world_factory):
    w = _pair(lib, world_factory, 0.3, 0.7, [0.0, 0.0], tags=(OMExcl.MILITARY_RELIEF, OMExcl.POLITICAL_RESOLUTION))
    assert sorted(e.template_id for e in read_events(lib, w)) == [0, 1]
    assert read_delayed(lib, w) == []


def test_control_ALG_37_losers_dropped_instead_of_requeued_is_detected(dbg, dbg_world_factory):
    """Positive control: OM_BUG_EXCLUSION_CANCELS cancels the loser, so the requeue assertions must fail."""
    w = dbg_world_factory(n_regions=1)
    isolate_events(dbg, w)
    load(dbg, w, [tmpl("FIRST", OMExcl.MILITARY_RELIEF), tmpl("SECOND", OMExcl.MILITARY_RELIEF)])
    region(dbg, w, 0)
    queue_external(dbg, w, 0, 0, due_tick=1, probability=0.3)
    queue_external(dbg, w, 0, 1, due_tick=1, probability=0.7)
    dbg.om_debug_inject(w, OMBugE04.EXCLUSION_CANCELS)
    force_draws(dbg, w, [0.25, 0.0])
    dbg.om_world_step(w)
    with pytest.raises(AssertionError):
        _check_highest_probability_kept(dbg, w, 0.25)


def test_control_ALG_37_wrong_expectation_fails(lib, world_factory):
    w = _pair(lib, world_factory, 0.3, 0.7, [0.25, 0.0])
    _check_highest_probability_kept(lib, w, 0.25)
    with pytest.raises(AssertionError):
        _check_highest_probability_kept(lib, w, 0.75)   # would require tick + 2


# ---- ALG-36 sequencing around the exclusion pass ----

def test_ALG_36_37_exclusion_pass_then_rolls_per_region(lib, world_factory):
    """ALG-36: 'Per region: exclusion pass (ALG-37); then ... one draw' -- region 0 consumes its loser draw and its roll before region 1 starts. Draws [0.25, 0.1, 0.75, 0.9]: region 0 loser +1 and its survivor fires (0.1 <= 0.7); region 1 loser +2 and its survivor does not (0.9 > 0.7)."""
    w = world_factory(n_regions=2)
    isolate_events(lib, w)
    load(lib, w, [tmpl("LOW", OMExcl.MILITARY_RELIEF), tmpl("HIGH", OMExcl.MILITARY_RELIEF)])
    for r in range(2):
        region(lib, w, r)
    for r in range(2):
        queue_external(lib, w, r, 0, due_tick=1, probability=0.3)
        queue_external(lib, w, r, 1, due_tick=1, probability=0.7)
    force_draws(lib, w, [0.25, 0.1, 0.75, 0.9])
    lib.om_world_step(w)
    assert lib.om_rng_forced_remaining(w) == 0
    fired = [(e.region_idx, e.template_id) for e in read_events(lib, w)]
    assert fired == [(0, 1)]
    due = {d.region_idx: d.new_due for d in read_delayed(lib, w)}
    assert due == {0: 1 + randint_1_2(0.25), 1: 1 + randint_1_2(0.75)}


def test_ALG_36_37_exclusion_runs_before_conditions(lib, world_factory):
    """ALG-36 / e2e E-04 'Order of operations' (2) before (3): the p 0.6 entry whose condition fails (military above 90, region has 50) still wins the exclusion, so the p 0.4 entry is re-queued, and the winner is then pruned with no roll. Only the loser draw is consumed; nothing fires at tick 3."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load(lib, w, [tmpl("PARENT", spawns=[
        dict(tid=1, lo=2, hi=2, p=0.6, ck=OMCond.ABOVE, cf=OMField.MILITARY, cv=90.0),
        dict(tid=2, lo=2, hi=2, p=0.4)]),
        tmpl("A_FAILS_COND", OMExcl.REVOLT_OUTCOME), tmpl("B_NO_COND", OMExcl.REVOLT_OUTCOME)])
    region(lib, w, 0)
    queue_external(lib, w, 0, 0, due_tick=1, probability=1.0)
    force_draws(lib, w, [0.0, 0.0, 0.0])           # tick 1: parent roll, two spawn delay draws (delay 2 -> due tick 3)
    lib.om_world_step(w)
    lib.om_world_step(w)                            # tick 2
    force_draws(lib, w, [0.25, 0.0])                # tick 3: loser draw, then (if wrongly rolled) a firing roll
    lib.om_world_step(w)
    pruned = read_pruned(lib, w)
    delayed = read_delayed(lib, w)
    assert [(p.template_id) for p in pruned] == [1]
    assert [(d.template_id, d.kept_template_id, d.new_due) for d in delayed] == [(2, 1, 3 + randint_1_2(0.25))]
    assert read_events(lib, w) == []
    assert lib.om_rng_forced_remaining(w) == 1, "only the loser draw is consumed; the pruned winner rolls nothing"


def test_ALG_36_37_requeued_entry_keeps_its_conditions(lib, world_factory):
    """ALG-35/36 entries are {template, region, due, probability, conditions, chain_tag}; ALG-37 re-queues the same entry. The loser (military above 40) is re-queued to tick 4; military is dropped to 20 before tick 4, so on its new due the condition fails and it is pruned, not fired."""
    w = world_factory(n_regions=1)
    isolate_events(lib, w)
    load(lib, w, [tmpl("PARENT", spawns=[
        dict(tid=1, lo=2, hi=2, p=0.8, ck=OMCond.ABOVE, cf=OMField.MILITARY, cv=40.0),
        dict(tid=2, lo=2, hi=2, p=0.4, ck=OMCond.ABOVE, cf=OMField.MILITARY, cv=40.0)]),
        tmpl("WINNER", OMExcl.REVOLT_OUTCOME), tmpl("LOSER", OMExcl.REVOLT_OUTCOME)])
    region(lib, w, 0)
    queue_external(lib, w, 0, 0, due_tick=1, probability=1.0)
    force_draws(lib, w, [0.0, 0.0, 0.0])
    lib.om_world_step(w)
    lib.om_world_step(w)
    force_draws(lib, w, [0.0, 1.0])                 # tick 3: loser draw 0.0 -> tick 4; winner roll 1.0 > 0.8 (no fire)
    lib.om_world_step(w)
    assert [(d.template_id, d.new_due) for d in read_delayed(lib, w)] == [(2, 4)]
    region(lib, w, 0, m=20.0)
    force_draws(lib, w, [0.0])                      # a wrongly rolled loser would fire on this draw
    lib.om_world_step(w)                            # tick 4
    assert [p.template_id for p in read_pruned(lib, w)] == [2]
    assert read_events(lib, w) == []
