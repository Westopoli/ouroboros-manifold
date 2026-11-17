# Rule pins: R-097-05, R-097-03, R-001-06, R-004-06, R-004-08
"""Engine rules round 5, G5, whole fights in the lab configuration: units on one slope collide across the layer line, and no unit flips layer back and forth across a midline.

Rule word for word (docs/bible/epics/E-13-movement-and-command.md, R-097-05, as it reads on the Round 5 branch): "Given two units on the same layer within 30 wu (2 x radius 15), or two units within 30 wu that
both stand on the same slope, whichever side of its midline each is on (E-01 R-001-06), When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3
iterations per tick. The slope case is there because a walker that crosses a slope's midline changes layer (E-01 R-004-06) and would otherwise arrive inside units of its new layer (Westley, 2026-11-17, asked whether
units on one slope collide across the layer line: "All the rest go with recommended", the recommendation being yes; a lab trial removed the pile-up on all six hill fights with every winner unchanged, at the cost of
queues on narrow ramps, docs/reports/2026-11-12-engine-rules-round-3.md)." And the invariant under E-13 (Invariants): "No two same-layer units, and no two units on the same slope (R-097-05), within 30 wu after the
collision pass, except when the pass hits its iteration cap."
round5.md G5 whole-run: "no two units on one slope closer than 30 wu after the pass except at the iteration cap, and no unit flips layer back and forth across a midline (three or more changes within 20 ticks)."

The single geometries are tests/csim/test_E13_R097_05_slope_collision.py. The judge here is a test-local oracle on the fight's own frames (a recorder of every step, `om_terrain_slope_at` read from the live world);
it does not use scripts/skilllab/invariants.py (the checker predicate of G7 is the lab builder's, tested beside it).

Configuration: `run.fight(layout, seed 1, sight "on", 600 simulated seconds)`: the lab's stage 4 rule set (walking units, the layout's hills laid as the lab lays them, targeting by sight on, nothing switched off), to the
lab's cap. The six hill layouts of the Round 3 trial (appendix-slope-pileup.md, the XL table): L-0061, L-0062, L-0063, L-0083, L-0084 (sight on) and L-0045 (the trial ran it with sight off; here sight on, the
lab's own setting), all catalogue layouts as they stand on this branch.

THE MEASURES (DRAFT numbers are Westley's):
  pile_up        a tick on which two living units on DIFFERENT layers that `om_terrain_slope_at` puts on the same slope (the same index, not -1) end the tick closer than PAIR 30 - SLACK wu (DRAFT-slope-slack-wu 2,
                 the sweep's I13: "closer than 28 wu after the step (R-097-05 says 30; 2 wu slack for the push pass)"), when neither unit has a third living unit within 30 wu of it (DRAFT-slope-cap-excuse: the pass
                 runs at most 3 iterations per tick, so a pair in a crowd may be left closer; an isolated pair is resolved by the first one). Only pairs on different layers are judged: that is the case R-097-05 adds.
                 Pairs on one layer are not, because the engine leaves isolated same-layer pairs closer than 28 wu today for reasons that are not the slope (a wall or a blocked cell the push may not enter; dumped
                 2026-11-17 on the Round 5 branch before the build, isolated same-layer pairs on a slope under 28 wu: L-0061 31, L-0062 37, L-0063 12, L-0083 73, L-0084 262, L-0045 12, and 0 to 13 of them off any
                 slope): a whole-fight "never closer than 30" cannot be asked of the slope case alone, and the spec's sentence ("no two units on one slope closer than 30 wu after the pass except at the iteration cap")
                 is reported as reading wider than the engine can meet (findings).
  flicker        a unit whose layer changes three or more times within FLICKER_TICKS 20 ticks (the spec's number): the layer flips and flips back across a midline.
"""
import contextlib
import math
import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402
from scripts.skilllab.engine import Engine  # noqa: E402

SECONDS = 600
HILLS = ["L-0061", "L-0062", "L-0063", "L-0083", "L-0084", "L-0045"]
PAIR = 30.0
SLACK = 2.0                 # DRAFT-slope-slack-wu
FLICKER_CHANGES = 3
FLICKER_TICKS = 20


class Slopes:
    """Per tick, for the units close to another: the pair, its distance, both layers and both slope indexes; per unit the ticks on which its layer changed."""

    def __init__(self, eng, w):
        self.eng, self.w = eng, w
        self.ids = sorted(u for (wa, f), us in eng._own.items() if wa == w.value for u in us)
        self.side = {u: f for (wa, f), us in eng._own.items() if wa == w.value for u in us}
        self.n = 0
        self.prev = {}
        self.changes = {u: [] for u in self.ids}
        self.close = []         # (tick, a, b, distance, layer a, layer b, slope a, slope b, crowded)
        self.changed_units = set()

    def step(self, orig):
        orig(self.eng, self.w)
        eng, w = self.eng, self.w
        self.n += 1
        rows = {}
        for u in self.ids:
            if eng.unit_alive(w, u):
                x, y = eng.unit_pos(w, u)
                layer = int(eng.unit_layer(w, u))
                rows[u] = (x, y, layer)
                if u in self.prev and self.prev[u] != layer:
                    self.changes[u].append(self.n)
                self.prev[u] = layer
        grid = {}
        for u, (x, y, _) in rows.items():
            grid.setdefault((int(x // PAIR), int(y // PAIR)), []).append(u)
        near = {u: 0 for u in rows}
        pairs = []
        for u, (x, y, _) in rows.items():
            cx, cy = int(x // PAIR), int(y // PAIR)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for o in grid.get((cx + dx, cy + dy), ()):
                        if o > u:
                            d = math.hypot(rows[o][0] - x, rows[o][1] - y)
                            if d < PAIR:
                                near[u] += 1
                                near[o] += 1
                                pairs.append((u, o, d))
        for u, o, d in pairs:
            su = eng.terrain_slope_at(w, rows[u][0], rows[u][1])
            so = eng.terrain_slope_at(w, rows[o][0], rows[o][1])
            self.close.append((self.n, u, o, d, rows[u][2], rows[o][2], su, so, near[u] > 1 or near[o] > 1))


@contextlib.contextmanager
def slope_recording():
    recs = {}
    orig = Engine.step

    def step(self, w):
        rec = recs.get(w.value)
        if rec is None:
            rec = recs[w.value] = Slopes(self, w)
        rec.step(orig)

    Engine.step = step
    try:
        yield recs
    finally:
        Engine.step = orig


@lru_cache(maxsize=None)
def played(name):
    with slope_recording() as recs:
        run.fight(oracle.catalogue(name), 1, "on", SECONDS, 100000)
    assert len(recs) == 1, "expected the fight to step exactly one world, got %d" % len(recs)
    return next(iter(recs.values()))


# ------------------------------------------------------------------ the measures

def pile_ups(rec_close, slack=SLACK):
    """[(tick, a, b, distance, layer a, layer b)] of pairs on one slope (same index, not -1) on different layers closer than PAIR - slack at the end of a tick, neither unit crowded by a third unit within 30 wu."""
    return [(t, a, b, round(d, 1), la, lb) for t, a, b, d, la, lb, sa, sb, crowded in rec_close
            if d < PAIR - slack and not crowded and sa >= 0 and sa == sb and la != lb]


def flickers(changes, count=FLICKER_CHANGES, within=FLICKER_TICKS):
    """[(unit, first tick)]: a unit with `count` layer changes inside `within` ticks (the last minus the first at most `within`)."""
    out = []
    for u, ts in changes.items():
        for i in range(len(ts) - count + 1):
            if ts[i + count - 1] - ts[i] <= within:
                out.append((u, ts[i]))
                break
    return sorted(out)


# ------------------------------------------------------------------ the measures against made-up frames (green today)

def test_control_the_measures_flag_planted_cases_and_nothing_else():
    """Control (green today): made-up frames. A pair on one slope on layers 0 and 1, 14 wu apart, alone, is a pile-up; the same pair at 29 wu (inside the 2 wu slack), crowded by a third unit, on slope -1 (two units on
    the flat on different layers: the rule does not apply), or on different slopes is not; a unit that changes layer at ticks 100, 105, 112 flickers, one at 100, 130, 160 does not."""
    close = [(1, 1, 2, 14.0, 0, 1, 7, 7, False), (2, 1, 2, 29.0, 0, 1, 7, 7, False), (3, 1, 2, 14.0, 0, 1, 7, 7, True),
             (4, 3, 4, 14.0, 0, 1, -1, -1, False), (5, 5, 6, 14.0, 0, 1, 7, 8, False), (6, 7, 8, 14.0, 1, 1, 7, 7, False)]
    assert pile_ups(close) == [(1, 1, 2, 14.0, 0, 1)]
    assert flickers({1: [100, 105, 112], 2: [100, 130, 160]}) == [(1, 100)]
    assert flickers({1: [100, 105], 2: []}) == []


# ------------------------------------------------------------------ the premises (green today)

@pytest.mark.parametrize("name", HILLS)
def test_premise_the_hill_fight_has_units_that_change_layer_and_meet_on_the_slope(name):
    """Premise (green today): the layout fought to its end in the lab configuration has units that change layer and pairs within 30 wu on a slope: the rule is exercised. Counts are dumped in the message, not pinned."""
    rec = played(name)
    changed = sum(1 for ts in rec.changes.values() if ts)
    on_slope = [c for c in rec.close if c[6] >= 0 and c[6] == c[7]]
    assert changed >= 3, "scene broken: only %d units changed layer in %s over %d ticks" % (changed, name, rec.n)
    assert on_slope, "scene broken: no two units came within 30 wu on a slope in %s over %d ticks" % (name, rec.n)


@pytest.mark.parametrize("name", ["L-0039", "L-0050"])
def test_control_a_fight_with_no_hill_has_no_pile_up_and_no_flicker(name):
    """R-097-05 control (green today and after): the same measures over fights that have no slope (L-0039, boxes; L-0050, an open field), sight on, to their end: no unit changes layer, no pair stands on a slope, and
    the measures read nothing. The two assertions below are red on the hill fights because of the slope, not because the measure reads every fight as a pile-up."""
    rec = played(name)
    assert rec.n >= 300, "scene broken: %s ran %d ticks" % (name, rec.n)
    assert pile_ups(rec.close) == [] and flickers(rec.changes) == [], "%s: pile-ups %s, flickers %s" % (name, pile_ups(rec.close)[:3], flickers(rec.changes)[:3])
    assert not any(ts for ts in rec.changes.values()) and not [c for c in rec.close if c[6] >= 0], "premise: %s has a slope" % name


# ------------------------------------------------------------------ the rule, whole fights

@pytest.mark.parametrize("name", HILLS)
def test_R_097_05_no_two_units_on_one_slope_end_a_tick_closer_than_30_wu(name):
    """R-097-05 / E-13 Invariants: "No two same-layer units, and no two units on the same slope (R-097-05), within 30 wu after the collision pass, except when the pass hits its iteration cap": on every tick of the
    fight no two units that stand on the same slope on different layers (the case R-097-05 adds) end the tick closer than 28 wu (30 less the sweep's 2 wu slack) unless a third unit crowds them (the 3-iteration
    cap). Red until Round 5 on all six: the pass skips a pair on different layers, and a walker that crosses the midline arrives inside the units of its new layer (isolated pairs today: L-0061 341, L-0062 103,
    L-0063 34, L-0083 1, L-0084 70, L-0045 319)."""
    rec = played(name)
    bad = pile_ups(rec.close)
    assert not bad, "%s: %d isolated pairs on one slope on different layers closer than 28 wu after the pass (tick, unit, unit, distance, layer, layer), %d pairs of units, first %s" % (
        name, len(bad), len({(p[1], p[2]) for p in bad}), bad[:4])


@pytest.mark.parametrize("name", HILLS)
def test_R_097_05_no_unit_flips_layer_back_and_forth_across_a_midline(name):
    """R-097-05 with R-004-06 / R-004-08 (the pile-up's symptom, round5.md G5: 'no unit flips layer back and forth across a midline (three or more changes within 20 ticks)'): in the whole fight no unit changes
    layer three times within 20 ticks. Red until Round 5 on L-0062 (27 units), L-0063 (38) and L-0084 (17); green today on L-0061, L-0083 and L-0045 (no unit flips three times in 20 ticks there), which the build must keep green (L-0063 flickered 6,724 unit-ticks in the Round 3 trial before the slope case, 175 after)."""
    rec = played(name)
    bad = flickers(rec.changes)
    assert not bad, "%s: %d units flip layer three or more times within 20 ticks (unit, first tick), first %s" % (name, len(bad), bad[:6])
