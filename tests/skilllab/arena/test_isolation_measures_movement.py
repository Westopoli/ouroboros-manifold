# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 3 arm M ("Arrival and finishing", "Spread over time ... idle counts split behind the firing line and in front of it") and section 8 (DRAFT-stuck-ticks, DRAFT-idle-front-behind)
"""LI2, orders ended short, idle units behind and in front, per-side spread. Planted documents with a known answer, each with controls that must NOT be flagged.

Spec 3 arm M: "Of alive units at the end of the fight or at the tick cap, count those with an active order and no progress; orders ended short must be 0. Any unit
counted is listed by id with its tick and place, a finding, not a pass or fail." "Spread over time (distance from the side's centre of mass, every K ticks), idle counts
split behind the firing line and in front of it. Behind is expected and counted separately; in front is the one to look at." Spec 1.8: "Units stuck behind the firing
line are expected (2026-11-19); counted, not flagged."
Brief (Architect): idle behind = "a friend within 40 wu nearer the destination"; the 200+ ticks and the 40 wu are DRAFT constants imported from the module.

FALLBACK, because the fight file carries NO per-unit destination (premise dumped from real files: only `orders` {mode, attacker, point}): a unit is "ordered" when `orders`
says so (both_same_point: every unit; hold_and_attack: the attacker's side only), and its order "stopped before arrival" when, at its last living frame, it has been
still (moved less than DRAFT_STILL_WU_PER_TICK * gap + DRAFT_STILL_SLACK_WU between frames) for at least DRAFT_STUCK_TICKS, with no target, farther than
DRAFT_ARRIVED_WU_75 from orders.point, and with no living enemy in notice. Notice = `sights[role]` when the file has `sights`, else `ranges[role]` (weapon range), planar.
`alive_at_end` = ordered units alive in the last frame; `died` = ordered units that were in that state at the last frame they were alive.
This rule is the one used in these tests; every number in it is a DRAFT constant. `basis` in the result says "fallback".

Controls (green today): the planted documents are valid lab files."""
import math

import pytest

import measures_fixtures as fx

NM = fx.NOT_MEASURED
DEST = (1000.0, 1000.0)
SPEED = 0.5                        # wu per tick for a unit that is moving: far above the still threshold


def _mover(x0, y0, stop):
    """Walks +x at SPEED until tick `stop` (None: never stops), then stands still."""
    return lambda t: (x0 + SPEED * (t if stop is None else min(t, stop)), y0)


def _ended_short_doc(mode="hold_and_attack", extra_enemy=None, with_sights=False, S=None):
    """Ordered side A (hold_and_attack, attacker A), destination (1000, 1000), Vanguards, weapon range 300.
    A1 stops short for 2 x S ticks, far from the destination, no target, no enemy near: FLAGGED, alive at the end.
    A2 stands 10 wu from the destination for 2 x S: arrived, not flagged.   A3 stops only S/2 ticks before the end: too short, not flagged.
    A4 stands still 2 x S with a target (a held fight): not flagged.        A5 stands still with an enemy 200 wu away (inside weapon range): not flagged.
    A6 creeps at 0.3 wu/tick the whole fight (never still): not flagged.     A7 stops for 2 x S, then dies: listed under `died`.
    A8 moves, then dies: not listed.   B1 stands near A5.   B2 stands still far away for the whole fight, no target (a holder when only A is ordered; ordered under both_same_point).
    `extra_enemy` is (id, (x, y)) of a further stationary B unit."""
    S = S if S is not None else fx.m().DRAFT_STUCK_TICKS
    ticks, step = fx.grid(3 * S + 100)
    end = ticks[-1]
    s1 = max(t for t in ticks if t <= end - 2 * S)
    s3 = min(t for t in ticks if t >= end - S // 2)
    assert s3 < end and end - s1 >= 2 * S and end - s3 <= S // 2        # the planted durations hold on this grid
    d_t = end - step                                                 # last frame A7 and A8 are alive
    roster = [(i, "A", "Vanguard") for i in range(1, 9)] + [(11, "B", "Vanguard"), (12, "B", "Vanguard")]
    paths = {1: _mover(100.0, 600.0, s1), 2: lambda t: (1010.0, 1000.0), 3: _mover(100.0, 1400.0, s3), 4: lambda t: (600.0, 1800.0),
             5: lambda t: (3000.0, 300.0), 6: lambda t: (100.0 + 0.3 * t, 2200.0), 7: _mover(100.0, 2600.0, s1), 8: _mover(100.0, 3000.0, None),
             11: lambda t: (3000.0, 100.0), 12: lambda t: (6000.0, 6000.0)}
    if extra_enemy:
        roster.append((extra_enemy[0], "B", "Vanguard"))
        paths[extra_enemy[0]] = lambda t: extra_enemy[1]
    ranges = {"Vanguard": 300.0}
    kw = {"sights": {"Vanguard": 800.0}} if with_sights else {}
    doc = fx.make_doc(roster, ticks, pos=lambda u, t: paths[u](t), target=lambda u, t: 12 if u == 4 else None,
                      alive=lambda u, t: not (u in (7, 8) and t > d_t), orders={"attacker": "A" if mode == "hold_and_attack" else None, "mode": mode, "point": list(DEST)},
                      ranges=ranges, res=fx.result("A", [6, 3], end), **kw)
    return doc, ticks, s1, end, d_t, paths


def ids(rows):
    return sorted(r["id"] for r in rows)


def test_control_planted_documents_are_valid_lab_files():
    """Positive control: both planted documents (built for 200 ticks, the proposed constants) pass the lab's validator."""
    from scripts.skilllab.arena import snapshot
    assert snapshot.validate(_idle_doc(I=200)[0]) == []
    doc, *_ = _ended_short_doc(S=200)
    assert snapshot.validate(doc) == []


def test_draft_constants_exist_with_their_documented_values():
    """Numbers nobody gave are DRAFT constants imported from the module; those the spec or the facts files fix are pinned: 200 idle ticks, 40 wu friend radius,
    75 wu arrival (r6-compare/tmp/stats.py `dd < 75`), still 0.05 wu per tick + 0.01 (stats.py `0.5 * ev / 10 + 0.01`). DRAFT_STUCK_TICKS is Westley's (spec 8): any positive int."""
    mod = fx.m()
    assert (mod.DRAFT_IDLE_TICKS_200, mod.DRAFT_IDLE_FRONT_BEHIND, mod.DRAFT_ARRIVED_WU_75) == (200, 40, 75)
    assert (mod.DRAFT_STILL_WU_PER_TICK, mod.DRAFT_STILL_SLACK_WU) == (0.05, 0.01)
    assert isinstance(mod.DRAFT_STUCK_TICKS, int) and mod.DRAFT_STUCK_TICKS > 0


def test_orders_ended_short_finds_the_planted_stopped_unit_and_nothing_else():
    """The one flagged unit among eight ordered ones is A1; the arrived unit, the late stopper, the fighter, the engaged unit and the creeper are the controls."""
    doc, ticks, s1, end, d_t, paths = _ended_short_doc()
    r = fx.m().orders_ended_short(doc)
    assert r["basis"].startswith("fallback")
    assert ids(r["alive_at_end"]) == [1]
    (a1,) = r["alive_at_end"]
    assert (a1["side"], a1["tick"], a1["since"]) == ("A", end, s1)
    assert (a1["x"], a1["y"]) == pytest.approx(paths[1](end), abs=0.01)
    assert ids(r["died"]) == [7]
    (a7,) = r["died"]
    assert (a7["tick"], a7["since"]) == (d_t, s1)


def test_only_the_ordered_side_counts_and_both_sides_count_when_both_are_ordered():
    """hold_and_attack with attacker A: the holder B2 (still, no target, 5000 wu from the point) is not an order that stopped. both_same_point: B2 is, and B1 (A5 in
    weapon range) is not."""
    held, *_ = _ended_short_doc("hold_and_attack")
    both, *_ = _ended_short_doc("both_same_point")
    assert 12 not in ids(fx.m().orders_ended_short(held)["alive_at_end"])
    assert ids(fx.m().orders_ended_short(both)["alive_at_end"]) == [1, 12]


def test_notice_is_the_sensor_when_the_file_has_one_and_the_weapon_range_when_it_has_not():
    """An enemy 500 wu from A1's resting place is outside weapon range 300 (A1 flagged) and inside sensor 800 (A1 not flagged)."""
    probe, ticks, s1, end, d_t, paths = _ended_short_doc()
    x, y = paths[1](end)
    enemy = (20, (x + 500.0, y))
    plain, *_ = _ended_short_doc(extra_enemy=enemy)
    sensed, *_ = _ended_short_doc(extra_enemy=enemy, with_sights=True)
    assert 1 in ids(fx.m().orders_ended_short(plain)["alive_at_end"])
    assert 1 not in ids(fx.m().orders_ended_short(sensed)["alive_at_end"])


def test_stuck_ticks_is_a_parameter_and_a_longer_demand_flags_nothing():
    doc, *_ = _ended_short_doc()
    mod = fx.m()
    r = mod.orders_ended_short(doc, stuck_ticks=10 * mod.DRAFT_STUCK_TICKS)
    assert r["alive_at_end"] == [] and r["died"] == []


def test_orders_ended_short_without_orders_in_the_file_is_not_measured():
    """No `orders` in the file: no point to arrive at, nothing to say: `not measured`, never an empty list that reads as zero."""
    doc, *_ = _ended_short_doc()
    del doc["orders"]
    r = fx.m().orders_ended_short(doc)
    assert isinstance(r, str) and r.startswith(NM)


def _idle_doc(dest_missing=False, I=None):
    """Both sides ordered to (1000, 1000); every unit below stands still from tick 0 unless noted, no target, over twice DRAFT_IDLE_TICKS_200 ticks.
    F (500,500) front. Bk (400,400) with G (420,420) 28 wu away and nearer the point: Bk behind, G front. Ar (1030,1000) arrived (30 wu).
    H (200,200) and I (260,260): the nearer friend is 85 wu away, outside 40: both front. J (300,900) with K (320,910) nearer but dead: J front (a dead friend does not shield).
    L (800,300) with enemy Be (820,310) nearer: L front (an enemy does not count). M (700,200) with N (720,230) moving, 36 wu away, nearer: M behind (the friend need not be idle).
    P stops only I/2 ticks before the end: not idle yet. Q stands with a target: not idle.  Expected: total 9 = arrived 1 + behind 2 (Bk, M) + front 6 (F, G, H, I, J, L)."""
    I = I if I is not None else fx.m().DRAFT_IDLE_TICKS_200
    ticks, step = fx.grid(2 * I + 100)
    end = ticks[-1]
    sp = min(t for t in ticks if t >= end - I // 2)
    pts = {1: (500, 500), 2: (400, 400), 3: (420, 420), 4: (1030, 1000), 5: (200, 200), 6: (260, 260), 7: (300, 900), 8: (320, 910), 9: (800, 300),
           10: (700, 200), 13: (900, 700)}
    names = {"F": 1, "Bk": 2, "G": 3, "Ar": 4, "H": 5, "I": 6, "J": 7, "K": 8, "L": 9, "M": 10, "N": 11, "P": 12, "Q": 13, "Be": 21}
    paths = {u: (lambda p: (lambda t: p))(p) for u, p in pts.items()}
    paths[11] = lambda t: (720.0 - 0.5 * (end - t), 230.0)
    paths[12] = lambda t: (900.0 - 0.5 * (end - min(t, sp)), 100.0)
    paths[21] = lambda t: (820.0 - 0.5 * (end - t), 310.0)
    roster = [(i, "A", "Vanguard") for i in range(1, 14)] + [(21, "B", "Vanguard")]
    orders = {"attacker": None, "mode": "both_same_point", "point": list(DEST)}
    doc = fx.make_doc(roster, ticks, pos=lambda u, t: paths[u](t), target=lambda u, t: 21 if u == 13 else None,
                      alive=lambda u, t: not (u == 8 and t == end), orders=orders, res=fx.result("A", [12, 1], end, "silence"))
    if dest_missing:
        del doc["orders"]
    return doc, names


def test_idle_units_split_arrived_behind_front_with_the_planted_answer():
    doc, names = _idle_doc()
    r = fx.m().idle_units(doc)
    assert (r["total"], r["arrived"], r["behind"], r["front"]) == (9, 1, 2, 6)
    by = {u["id"]: u["class"] for u in r["units"]}
    n = names
    assert by == {n["F"]: "front", n["Bk"]: "behind", n["G"]: "front", n["Ar"]: "arrived", n["H"]: "front", n["I"]: "front", n["J"]: "front",
                  n["L"]: "front", n["M"]: "behind"}
    assert all(u["since"] == 0 for u in r["units"])


def test_idle_needs_the_full_duration_and_no_target():
    """P (still for I/2), Q (target set), N (moving) and the dead K are not idle at 200+; asking for 10 x the duration finds nobody."""
    doc, names = _idle_doc()
    mod = fx.m()
    assert {names["P"], names["Q"], names["N"], names["K"]}.isdisjoint({u["id"] for u in mod.idle_units(doc)["units"]})
    r = mod.idle_units(doc, min_ticks=10 * mod.DRAFT_IDLE_TICKS_200)
    assert (r["total"], r["arrived"], r["behind"], r["front"]) == (0, 0, 0, 0)


def test_idle_without_a_point_is_not_measured():
    doc, _ = _idle_doc(dest_missing=True)
    r = fx.m().idle_units(doc)
    assert isinstance(r, str) and r.startswith(NM)


def _spread_doc():
    """Side A: four living units on (+-3, +-4) around (100, 100) at tick 0, on (+-6, +-8) at tick 50 and 100; a fifth A unit dead from the start, far away (9999, 9999).
    Side B: one living unit, dead at tick 100."""
    roster = [(1, "A", "Vanguard"), (2, "A", "Vanguard"), (3, "A", "Vanguard"), (4, "A", "Vanguard"), (5, "A", "Vanguard"), (6, "B", "Vanguard")]
    k = {1: (1, 1), 2: (1, -1), 3: (-1, 1), 4: (-1, -1)}

    def pos(u, t):
        if u == 5:
            return (9999.0, 9999.0)
        if u == 6:
            return (500.0, 500.0)
        f = 1 if t == 0 else 2
        return (100.0 + 3 * f * k[u][0], 100.0 + 4 * f * k[u][1])
    return fx.make_doc(roster, [0, 50, 100], pos=pos, alive=lambda u, t: not (u == 5 or (u == 6 and t == 100)))


def test_spread_is_the_rms_distance_from_the_side_centroid_of_the_living():
    """Four units at distance 5 from their centroid: RMS 5.0; at distance 10: 10.0; a dead unit far away is not in it. One living unit: 0.0.
    Spec 3 arm M: spread 'distance from the side's centre of mass, every K ticks'."""
    s = fx.m().spread_at(_spread_doc(), [0, 50])
    assert s[0] == {"A": pytest.approx(5.0), "B": pytest.approx(0.0)}
    assert s[50] == {"A": pytest.approx(10.0), "B": pytest.approx(0.0)}


def test_spread_with_nothing_to_measure_is_not_measured_and_ticks_keep_their_order():
    """Side B is dead at tick 100: no living unit, `not measured` (not 0.0, which would read as a tight blob). Tick 25 has no frame: `not measured` for the tick."""
    s = fx.m().spread_at(_spread_doc(), [100, 25, 0])
    assert list(s) == [100, 25, 0]
    assert s[100]["A"] == pytest.approx(10.0)
    assert isinstance(s[100]["B"], str) and s[100]["B"].startswith(NM)
    assert isinstance(s[25], str) and s[25].startswith(NM)
