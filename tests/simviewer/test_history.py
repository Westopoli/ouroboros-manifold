"""SV-2: tests for scripts/simviewer/history.py (class History), the sim viewer's
fold of pipe frames into per-region state, rings, events, missions and layout.

Frozen API: docs/northstar/plans/2026-10-12-simviewer-spec.md "Shared interfaces".
Fixtures in tests/simviewer/fixtures/ were recorded once from the real dbg pipe
(seed 1, 80 regions, features 0..7, new_campaign false; 80 because 60 fails
generation): snapshot_t0, the 20 `step n=20` deltas, snapshot_t20, a mission and
debrief frame (seed 16, objective_complete 0 1.0, mission_end), a chronicle frame
and the snapshot after `jump 50`.

Red on the built tree: module scripts.simviewer.history does not exist.
"""
import copy
import json
from pathlib import Path

from scripts.simviewer.history import History, LAYOUT_ITERATIONS, LAYOUT_SEED, RING

FIX = Path(__file__).resolve().parent / "fixtures"
SIX = ("military", "economy", "tension", "population", "stability", "capacity")
# Snapshot values are rounded to two decimals, delta values are not (recorded):
# a folded delta and a snapshot of the same tick agree to within that rounding.
SNAP_TOL = 0.006


def _load(name):
    return json.loads((FIX / name).read_text())


def _fresh_t0():
    h = History()
    h.apply(_load("snapshot_t0.json"))
    return h


def _folded_t20():
    h = _fresh_t0()
    for d in _load("deltas_t1_t20.json"):
        h.apply(d)
    return h


def test_snapshot_t0_fills_regions_edges_factions():
    """SV-2: applying a snapshot gives every region with owner/tier/six values,
    the edge list as (a, b) tuples, and the factions keyed by id."""
    snap = _load("snapshot_t0.json")
    h = _fresh_t0()
    assert h.tick == snap["tick"] == 0
    assert len(h.regions) == 80
    assert set(h.regions) == set(range(80))
    for r in snap["regions"]:
        row = h.regions[r["i"]]
        assert row["owner"] == r["owner"]
        assert row["tier"] == r["tier"]
        for k in SIX:
            assert row[k] == r[k]
    assert h.edges
    assert [tuple(e) for e in h.edges] == [(e["a"], e["b"]) for e in snap["edges"]]
    assert all(isinstance(a, int) and isinstance(b, int) for a, b in h.edges)
    assert h.factions
    assert set(h.factions) == {f["id"] for f in snap["factions"]}


def test_delta_fold_matches_snapshot_at_tick_20():
    """SV-2: folding the 20 recorded deltas onto snapshot_t0 yields the same owner
    and six values per region as snapshot_t20 (the delta fold is correct)."""
    h = _folded_t20()
    snap = _load("snapshot_t20.json")
    assert h.tick == 20 == snap["tick"]
    assert len(h.regions) == len(snap["regions"]) == 80
    for r in snap["regions"]:
        row = h.regions[r["i"]]
        assert row["owner"] == r["owner"], r["i"]
        for k in SIX:
            assert abs(row[k] - r[k]) <= SNAP_TOL, (r["i"], k, row[k], r[k])


def test_delta_changes_only_regions_it_lists():
    """SV-2: a delta rewrites the regions it lists and leaves every other region
    (and the tier, which deltas do not carry) untouched."""
    h = _fresh_t0()
    before = copy.deepcopy(h.regions)
    delta = _load("deltas_t1_t20.json")[0]
    listed = {r["i"] for r in delta["regions"]}
    assert listed and len(listed) < 80  # recorded: 51 of 80 listed at tick 1
    h.apply(delta)
    assert h.tick == 1
    for i in range(80):
        if i not in listed:
            assert h.regions[i] == before[i], i
    for r in delta["regions"]:
        row = h.regions[r["i"]]
        assert row["owner"] == r["owner"]
        assert row["tier"] == before[r["i"]]["tier"]
        for k in SIX:
            assert row[k] == r[k]
    assert any(h.regions[i] != before[i] for i in listed)


def _tick_offset(deltas, offset):
    out = copy.deepcopy(deltas)
    for d in out:
        d["tick"] += offset
    return out


def test_ring_is_capped_oldest_first_and_ends_at_current_value():
    """SV-2: ring(r, field) holds at most RING values, oldest first, one per applied
    tick that listed the region; its last value is the region's current value."""
    deltas = _load("deltas_t1_t20.json")
    always = set.intersection(*({r["i"] for r in d["regions"]} for d in deltas))
    assert always, "fixture has no region listed in all 20 deltas"
    r = min(always)
    h = _fresh_t0()
    for d in deltas:
        h.apply(d)
    ring = h.ring(r, "military")
    expected = [next(x for x in d["regions"] if x["i"] == r)["military"] for d in deltas]
    assert 20 <= len(ring) <= RING
    assert ring[-20:] == expected
    assert ring[-1] == h.regions[r]["military"]

    # Push past the cap: fold the same 20 deltas again enough times to exceed RING.
    h2 = _fresh_t0()
    reps = RING // 20 + 2
    all_vals = []
    for k in range(reps):
        for d in _tick_offset(deltas, 20 * k):
            h2.apply(d)
        all_vals += expected
    ring2 = h2.ring(r, "military")
    assert len(ring2) == RING
    assert ring2 == all_vals[-RING:]
    assert ring2[-1] == h2.regions[r]["military"]


def test_ring_skips_ticks_that_do_not_list_the_region():
    """SV-2: a region absent from a delta gets no ring entry for that tick."""
    deltas = _load("deltas_t1_t20.json")
    r = next(i for i in range(80)
             if any(i not in {x["i"] for x in d["regions"]} for d in deltas))
    expected = [next(x for x in d["regions"] if x["i"] == r)["economy"]
                for d in deltas if any(x["i"] == r for x in d["regions"])]
    assert len(expected) < 20
    h = _fresh_t0()
    for d in deltas:
        h.apply(d)
    ring = h.ring(r, "economy")
    assert len(ring) <= RING
    assert ring[len(ring) - len(expected):] == expected


def test_events_returns_the_events_deltas_listed_for_the_region():
    """SV-2: events(r) returns, in arrival order, each delta event whose region is r,
    as dicts with tick, template, chain and delta."""
    deltas = _load("deltas_t1_t20.json")
    h = _fresh_t0()
    for d in deltas:
        h.apply(d)
    by_region = {}
    for d in deltas:
        for e in d["events"]:
            by_region.setdefault(e["region"], []).append(
                (e["tick"], e["template"], e["chain"], list(e["delta"])))
    assert len(by_region) >= 3
    for r, want in by_region.items():
        got = [(e["tick"], e["template"], e["chain"], list(e["delta"])) for e in h.events(r)]
        assert got == want, r
    quiet = next(i for i in range(80) if i not in by_region)
    assert h.events(quiet) == []


def _layout_json(h):
    return json.dumps(h.layout(), sort_keys=True)


def test_layout_is_byte_identical_across_instances_and_rounded():
    """SV-2: layout() is seeded and fixed-iteration: two History instances over the
    same edges give identical JSON; one entry per region; coordinates rounded to
    3 decimals."""
    assert LAYOUT_ITERATIONS == 200 and LAYOUT_SEED == 1
    h1, h2 = _fresh_t0(), _fresh_t0()
    assert _layout_json(h1) == _layout_json(h2)
    lay = h1.layout()
    assert set(lay) == set(range(80))
    for i, (x, y) in lay.items():
        assert round(x, 3) == x and round(y, 3) == y, i
    assert len({tuple(p) for p in lay.values()}) > 40  # not collapsed to a point


def test_layout_differs_for_a_different_edge_set():
    """SV-2: the layout follows the edges; a snapshot with half the edges lays out
    differently."""
    snap = _load("snapshot_t0.json")
    cut = copy.deepcopy(snap)
    cut["edges"] = cut["edges"][::2]
    assert 0 < len(cut["edges"]) < len(snap["edges"])
    h = History()
    h.apply(cut)
    assert _layout_json(h) != _layout_json(_fresh_t0())


def test_mission_and_debrief_give_one_missions_row():
    """SV-2: a mission frame then its debrief frame add exactly one missions row with
    tick, region, archetype, band and region_delta."""
    mission = _load("mission_frame.json")
    debrief = _load("debrief_frame.json")
    h = History()
    h.apply(_load("snapshot_t20.json"))
    assert h.missions == []
    h.apply(mission)
    h.apply(debrief)
    assert len(h.missions) == 1
    row = h.missions[0]
    assert row["tick"] == 20
    assert row["region"] == mission["region"] == 56
    assert row["archetype"] == mission["archetype"] == 5
    assert row["band"] == debrief["band"] == 4
    assert row["region_delta"] == debrief["region_delta"]
    assert any(v != 0 for v in row["region_delta"].values())


def test_chronicle_frame_is_accepted_and_does_not_touch_regions():
    """SV-2: a chronicle frame folds without error and leaves region state alone."""
    h = _folded_t20()
    before = copy.deepcopy(h.regions)
    h.apply(_load("chronicle_frame.json"))
    assert h.regions == before


def _regions_after(name):
    h = History()
    h.apply(_load(name))
    return h.regions


def test_diff_lists_exactly_the_regions_that_differ_after_a_jump():
    """SV-2: History.diff(before, after) over snapshot_t0 and snapshot_after_jump lists
    exactly the regions whose owner or any of the six values differ."""
    t0 = _load("snapshot_t0.json")
    jump = _load("snapshot_after_jump.json")
    old = {r["i"]: r for r in t0["regions"]}
    new = {r["i"]: r for r in jump["regions"]}
    expected = sorted(i for i in old
                      if old[i]["owner"] != new[i]["owner"]
                      or any(old[i][k] != new[i][k] for k in SIX))
    assert 0 < len(expected) <= 80
    got = History.diff(_regions_after("snapshot_t0.json"),
                       _regions_after("snapshot_after_jump.json"))
    assert sorted(got) == expected
    assert len(got) == len(set(got))
    assert History.diff(_regions_after("snapshot_t0.json"),
                        _regions_after("snapshot_t0.json")) == []


def test_diff_positive_control_one_hand_edited_owner():
    """SV-2 positive control: snapshot_t20 with one region's owner changed makes diff
    list exactly that region."""
    snap = _load("snapshot_t20.json")
    edited = copy.deepcopy(snap)
    target = 17
    edited["regions"][target]["owner"] = snap["regions"][target]["owner"] + 1
    assert edited["regions"][target]["i"] == target
    a, b = History(), History()
    a.apply(snap)
    b.apply(edited)
    assert History.diff(a.regions, b.regions) == [target]


def test_unknown_frame_types_are_ignored():
    """SV-2: frames of other types (hello, ack, error, tactical, anything) are ignored
    without error and change nothing."""
    h = _folded_t20()
    before_regions = copy.deepcopy(h.regions)
    before_tick, before_missions = h.tick, list(h.missions)
    for frame in ({"type": "hello", "abi": 7}, {"type": "ack", "name": "step", "tick": 99},
                  {"type": "error", "name": "x", "reason": "y"},
                  {"type": "tactical", "tick": 5}, {"type": "no_such_frame"}):
        h.apply(frame)
    assert h.regions == before_regions
    assert h.tick == before_tick
    assert h.missions == before_missions
