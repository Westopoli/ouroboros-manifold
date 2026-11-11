# Rule pins: R-207-06, R-207-07, R-087-04, R-084-04, R-087-03, R-087-09, R-083-03, R-004-06
"""Engine rule fixes 2026-11-08, F0, the checker: `scripts/skilllab/invariants.py`, pure predicates over a recorded per-tick trace.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F0". Each check fires on a planted bad trace and stays silent on a clean one (the
positive control: a clean twin of every planted trace is the same trace with the one fault taken out). The online wrapper `run.fight` uses, the
fight-document keys, `snapshot.validate`, `run.py` and `page.py` are tests/skilllab/arena/test_invariants_wiring.py.

THE API THIS FILE PINS (the test writer's design, as narrow as the spec allows; the implementer builds to it, the chat may rename):

    RULES = ("R-207-06", "R-207-07", "R-087-04", "R-084-04", "R-087-03", "R-087-09", "R-083-03", "continuity")

    Rules(width, height, blocked_cell=None, max_step=None, sensor_radius=None, suspended=None)
        width, height   the canvas in wu (R-207-07)
        blocked_cell    callable (cx, cy, layer) -> bool over the engine's 100 wu cells; None: no cell is blocked
        max_step        {unit id: wu per tick at full speed}; a unit with no entry is not checked for continuity
        sensor_radius   {unit id: wu}; a unit with no entry is never excused by the leash
        suspended       {rule: switch name} for rules the run cannot judge because it turned that switch off

    check(trace, rules, only=None) -> Report            pure; `only` is an iterable of rule names (default: all RULES)
        Report.violations   list of {"rule": str, "tick": int, "unit": int, "detail": str}, ordered by (tick, rule, unit)
        Report.suspended    {rule: switch} for the suspended rules that `only` selected; a suspended rule reports no violation
        Report.invalid      bool, True when violations is not empty

    trace = [frame0, frame1, ...]; frame k holds the state AFTER step k (frame0: before the first step):
        {"tick": int, "units": {unit id: row}, "fires": [(attacker id, target id), ...]}      "fires" are the shots of the step that made the frame
        row = {"x": float, "y": float, "layer": int, "alive": bool, "hp": float, "side": int, "target": int (0: none)}
              optional keys: "seen" (bool; the unit's side sees its target; default True), "order" (any equal-comparable token that changes when
              the unit is given a new order; default None), "shootable" (bool; the unit can shoot its target; default True)

Rule semantics pinned here, each from the spec's F0 list (numbers are the spec's DRAFT constants, Westley's):
    R-207-06    a living unit ends a frame inside a cell for which blocked_cell(cx, cy, layer) is true and deeper than 1 wu from the nearest face that
                borders an open cell (DRAFT-inv-cell-depth 1)
    R-207-07    a living unit outside 0..width, 0..height
    R-087-04    a unit in "fires" whose position moved more than 0.5 wu since the previous frame with no other living unit within 40 wu (DRAFT-inv-push-radius)
    R-084-04    a unit that did not fire this frame and moved more than 0.5 wu in frames 1 to 9 after its own last shot, no unit within 40 wu
    R-087-03    a unit's target changed from a living enemy to another target while the old one was alive and "seen" in both frames, the unit's "order" token
                unchanged, and the unit within sensor_radius + 25 wu of where it took that lock
    R-087-09    a held target that is not "shootable" for more than 20 consecutive frames (DRAFT-inv-stuck-ticks) while the distance to it did not fall
                by more than 1 wu below the run's first distance
    R-083-03    a living unit's hp rose by more than 0.075 (plus 1e-6) in a frame in which no shot hit it
    continuity  a living unit moved more than max_step[unit] + 1.3 wu (+ DRAFT-inv-push-allowance 2.0 when a unit is within 40 wu) in a frame (DRAFT-inv-step-slack;
                layer change included); round 2: a push explains at most 2.0 wu
"""
import importlib

import pytest

BLOCKED = (5, 4)          # the cell x 500..600, y 400..500


class _Module:
    """The module under test, imported on first use so that a missing scripts/skilllab/invariants.py fails each test with that message (not a collection error)."""

    def __getattr__(self, name):
        try:
            mod = importlib.import_module("scripts.skilllab.invariants")
        except ModuleNotFoundError as err:
            pytest.fail("F0 not built: %s" % err)
        return getattr(mod, name)


@pytest.fixture(scope="module")
def inv():
    return _Module()


def row(x, y, side=0, layer=0, alive=True, hp=100.0, target=0, **extra):
    return dict({"x": float(x), "y": float(y), "layer": layer, "alive": alive, "hp": float(hp), "side": side, "target": target}, **extra)


def trace(*steps):
    """steps: one entry per frame, each {unit id: row} or ({unit id: row}, [fires]); frame 0 first."""
    out = []
    for n, step in enumerate(steps):
        units, fires = step if isinstance(step, tuple) else (step, [])
        out.append({"tick": n, "units": units, "fires": list(fires)})
    return out


def still(n, **units):
    """n identical frames of units given as u1=row, u2=row (ids 1, 2)."""
    return [{int(k[1:]): v for k, v in units.items()} for _ in range(n)]


def rules(inv, **kw):
    kw.setdefault("width", 4000.0)
    kw.setdefault("height", 4000.0)
    return inv.Rules(**kw)


def run(inv, tr, only=None, **kw):
    return inv.check(tr, rules(inv, **kw), only=only)


def of(report, rule):
    return [v for v in report.violations if v["rule"] == rule]


def cell5_4(cx, cy, layer):
    return (cx, cy) == BLOCKED and layer == 0


# ------------------------------------------------------------------ the report

def test_the_report_of_a_clean_trace_is_empty_and_valid(inv):
    """Control: a quiet trace is not invalid, whatever the checks."""
    rep = run(inv, trace(*still(5, u1=row(100, 100), u2=row(900, 900, side=1))), blocked_cell=cell5_4, max_step={1: 3.5, 2: 3.5})
    assert (rep.violations, rep.invalid, rep.suspended) == ([], False, {})


def test_a_violation_is_a_dict_of_rule_tick_unit_detail(inv):
    """F0: 'A violation is {rule, tick, unit, detail}'."""
    rep = run(inv, trace({1: row(450, 450)}, {1: row(550, 450)}), blocked_cell=cell5_4)
    assert rep.invalid and len(rep.violations) >= 1
    v = rep.violations[0]
    assert set(v) == {"rule", "tick", "unit", "detail"} and isinstance(v["detail"], str) and v["detail"]
    assert (v["rule"], v["tick"], v["unit"]) == ("R-207-06", 1, 1)


def test_rules_lists_the_nine_checks(inv):
    """F0 'Checks, each with its rule id'. Engine rules round 2 (T3): R-093-02 (fire only at what your side sees) is the ninth, appended; the pin was eight."""
    assert tuple(inv.RULES) == ("R-207-06", "R-207-07", "R-087-04", "R-084-04", "R-087-03", "R-087-09", "R-083-03", "continuity", "R-093-02")


# ------------------------------------------------------------------ R-207-06

def test_R_207_06_a_unit_ending_a_tick_inside_a_blocked_cell_is_flagged(inv):
    """R-207-06 / E-13 Invariants: planted, unit 1 ends tick 3 at (550, 450), the middle of the blocked cell, 50 wu from its nearest open face."""
    tr = trace(*[{1: row(450, 450)}] * 3, {1: row(550, 450)}, {1: row(450, 450)})
    rep = run(inv, tr, blocked_cell=cell5_4, only=["R-207-06"])
    assert [(v["rule"], v["tick"], v["unit"]) for v in rep.violations] == [("R-207-06", 3, 1)]


def test_R_207_06_control_a_unit_outside_the_cell_a_dead_unit_and_another_layer_are_silent(inv):
    """R-207-06 control: the same frames with the unit outside, dead in the cell, or inside it on a layer the cell does not block, are silent."""
    for unit in (row(450, 450), row(550, 450, alive=False, hp=0.0), row(550, 450, layer=1)):
        rep = run(inv, trace({1: unit}, {1: unit}), blocked_cell=cell5_4, only=["R-207-06"])
        assert rep.violations == [], unit


def test_R_207_06_the_tolerance_is_one_wu_of_depth(inv):
    """R-207-06 (DRAFT-inv-cell-depth 1): 0.5 wu inside the face is silent, 2.5 wu is flagged. The west face of cell (5, 4) is x = 500 and
    its west neighbour is open."""
    shallow = run(inv, trace({1: row(450, 450)}, {1: row(500.5, 450)}), blocked_cell=cell5_4, only=["R-207-06"])
    deep = run(inv, trace({1: row(450, 450)}, {1: row(502.5, 450)}), blocked_cell=cell5_4, only=["R-207-06"])
    assert (shallow.violations, len(deep.violations)) == ([], 1)


# ------------------------------------------------------------------ R-207-07

def test_R_207_07_a_unit_outside_the_canvas_is_flagged_and_one_on_the_edge_is_not(inv):
    """R-207-07: planted, unit 1 ends tick 2 at x = 4007.5 on a 4000 canvas; control: x = 4000 and y = 0 are inside."""
    bad = run(inv, trace({1: row(3990, 100)}, {1: row(3990, 100)}, {1: row(4007.5, 100)}), only=["R-207-07"])
    edge = run(inv, trace({1: row(3990, 100)}, {1: row(4000.0, 0.0)}), only=["R-207-07"])
    assert ([(v["tick"], v["unit"]) for v in bad.violations], edge.violations) == ([(2, 1)], [])


# ------------------------------------------------------------------ R-087-04

def _shot(inv, move, neighbour=None, fires=True, **kw):
    units = {1: row(100, 100), 2: row(300, 100, side=1)}
    moved = {1: row(100 + move, 100), 2: row(300, 100, side=1)}
    if neighbour is not None:
        units[3] = moved[3] = row(100 + neighbour, 100)
    return run(inv, trace(units, (moved, [(1, 2)] if fires else [])), only=["R-087-04"], **kw)


def test_R_087_04_a_unit_that_fires_on_a_tick_it_moved_is_flagged(inv):
    """R-087-04: planted, unit 1 fires at tick 1 after moving 4 wu, no other unit within 40 wu."""
    rep = _shot(inv, 4.0)
    assert [(v["rule"], v["tick"], v["unit"]) for v in rep.violations] == [("R-087-04", 1, 1)]


@pytest.mark.parametrize("move,neighbour,fires", [(0.0, None, True), (4.0, None, False), (4.0, 30.0, True)],
                         ids=["fires-halted", "moves-without-firing", "pushed-by-a-neighbour-30-wu-away"])
def test_R_087_04_control_halted_fire_a_plain_move_and_a_pushed_unit_are_silent(inv, move, neighbour, fires):
    """R-087-04 control: a halted shooter, a mover that does not fire, and a shooter displaced with a friendly unit within 40 wu (a collision
    push; spec: 'pushes by neighbours excluded') are silent."""
    assert _shot(inv, move, neighbour, fires).violations == []


# ------------------------------------------------------------------ R-084-04

def _pause(inv, moves_at, neighbour=False):
    """Unit 1 fires at tick 2 (halted) and then moves 3 wu at tick `moves_at` (without firing)."""
    frames, x = [{1: row(100, 100), 2: row(300, 100, side=1)}], 100.0
    for t in range(1, 16):
        if t == moves_at:
            x += 3.0
        u = {1: row(x, 100), 2: row(300, 100, side=1)}
        if neighbour:
            u[3] = row(x + 30, 100)
        frames.append((u, [(1, 2)] if t == 2 else []))
    return run(inv, trace(*frames), only=["R-084-04"])


@pytest.mark.parametrize("at", [3, 6, 11])
def test_R_084_04_a_unit_that_moves_in_the_nine_ticks_after_its_shot_is_flagged(inv, at):
    """R-084-04: planted, a shot at tick 2 and a 3 wu step at tick `at` (ticks 3, 6 and 11 are 1, 4 and 9 ticks after the shot)."""
    assert [(v["rule"], v["tick"], v["unit"]) for v in _pause(inv, at).violations] == [("R-084-04", at, 1)]


@pytest.mark.parametrize("at", [12, 14])
def test_R_084_04_control_the_tenth_tick_after_the_shot_is_free(inv, at):
    """R-084-04 control: a step 10 ticks (tick 12) or 12 ticks after the shot is silent."""
    assert _pause(inv, at).violations == []


def test_R_084_04_control_a_pushed_unit_is_silent(inv):
    """R-084-04 control: the same step with a friendly unit 30 wu away is a push."""
    assert _pause(inv, 6, neighbour=True).violations == []


# ------------------------------------------------------------------ R-087-03

def _lock(inv, change_at=3, **kw):
    """Unit 1 (side 0) locks enemy 2 for frames 1-2 and changes to enemy 4 at frame `change_at`; enemies 2 and 4 stand still."""
    frames = []
    for t in range(0, 6):
        tgt = 0 if t == 0 else (2 if t < change_at else 4)
        frames.append({1: row(100, 100, target=tgt, **kw.get("one", {})), 2: row(300, 100, side=1, **kw.get("two", {})), 4: row(250, 120, side=1)})
    for t, extra in kw.get("late", {}).items():
        frames[t][1].update(extra)
    return run(inv, trace(*frames), only=["R-087-03"], sensor_radius={1: 100.0, 2: 100.0})


def test_R_087_03_a_lock_swapped_while_the_target_lives_and_is_seen_is_flagged(inv):
    """R-087-03 (rewritten 2026-11-08): planted, the target changes from enemy 2 to enemy 4 at tick 3 while 2 is alive and seen."""
    assert [(v["rule"], v["tick"], v["unit"]) for v in _lock(inv).violations] == [("R-087-03", 3, 1)]


@pytest.mark.parametrize("name,kw", [
    ("target-died", {"late": {}, "two": {}}),
    ("target-left-sight", {"late": {3: {"seen": False}}}),
    ("new-order", {"late": {3: {"order": "new"}}}),
], ids=lambda p: p if isinstance(p, str) else "")
def test_R_087_03_control_a_lock_that_ended_for_a_stated_reason_is_silent(inv, name, kw):
    """R-087-03 control: the same swap is legal when the old target died, left the side's sight, or the unit was given a new order. (The first
    variant kills enemy 2 in frame 3 by marking it dead below.)"""
    if name == "target-died":
        frames = []
        for t in range(0, 6):
            frames.append({1: row(100, 100, target=0 if t == 0 else (2 if t < 3 else 4)), 2: row(300, 100, side=1, alive=t < 3, hp=100.0 if t < 3 else 0.0), 4: row(250, 120, side=1)})
        rep = run(inv, trace(*frames), only=["R-087-03"], sensor_radius={1: 100.0})
    else:
        rep = _lock(inv, **kw)
    assert rep.violations == [], name


def test_R_087_03_control_a_unit_that_walked_past_its_leash_is_excused(inv):
    """R-087-03 control (R-087-05, the leash is its own rule and breaks a lock): the unit took the lock at (100, 100) with sensor radius 100
    and stands 400 wu away at the swap."""
    frames = []
    for t in range(0, 6):
        x = 100.0 + (0 if t < 2 else 400.0)
        frames.append({1: row(x, 100, target=0 if t == 0 else (2 if t < 3 else 4)), 2: row(300, 100, side=1), 4: row(250, 120, side=1)})
    rep = run(inv, trace(*frames), only=["R-087-03"], sensor_radius={1: 100.0})
    assert rep.violations == []


# ------------------------------------------------------------------ R-087-09

def _stuck(inv, ticks, shootable=False, closing=0.0):
    frames = [{1: row(100, 100), 2: row(500, 100, side=1)}]
    for t in range(1, ticks + 1):
        frames.append({1: row(100 + closing * t, 100, target=2, shootable=shootable), 2: row(500, 100, side=1)})
    return run(inv, trace(*frames), only=["R-087-09"])


def test_R_087_09_a_held_target_not_shootable_for_more_than_twenty_ticks_while_not_closing_in_is_flagged(inv):
    """R-087-09 (DRAFT-inv-stuck-ticks 20): planted, 25 ticks holding an unshootable target without closing in; the first flag is on tick 21 or 22."""
    rep = _stuck(inv, 25)
    assert rep.violations and rep.violations[0]["rule"] == "R-087-09" and rep.violations[0]["unit"] == 1
    assert rep.violations[0]["tick"] in (21, 22)


@pytest.mark.parametrize("ticks,shootable,closing", [(15, False, 0.0), (25, True, 0.0), (25, False, 5.0)],
                         ids=["only-15-ticks", "shootable", "closing-in-5-wu-a-tick"])
def test_R_087_09_control_short_shootable_or_closing_in_is_silent(inv, ticks, shootable, closing):
    """R-087-09 control: a 15-tick stall, a shootable target, and a unit closing in 5 wu a tick are silent."""
    assert _stuck(inv, ticks, shootable, closing).violations == []


# ------------------------------------------------------------------ R-083-03

def _heal(inv, gain, hit=False):
    fires = [(2, 1)] if hit else []
    return run(inv, trace({1: row(100, 100, hp=100.0), 2: row(300, 100, side=1)}, ({1: row(100, 100, hp=100.0 + gain), 2: row(300, 100, side=1)}, fires)), only=["R-083-03"])


def test_R_083_03_a_heal_of_more_than_one_wardens_0_075_on_an_unhit_tick_is_flagged(inv):
    """R-083-03: planted, unit 1 gains 0.15 hp in a tick nothing hit it (two Wardens stacked)."""
    assert [(v["rule"], v["tick"], v["unit"]) for v in _heal(inv, 0.15).violations] == [("R-083-03", 1, 1)]


@pytest.mark.parametrize("gain,hit", [(0.075, False), (0.0, False), (0.15, True)], ids=["one-warden", "no-heal", "hit-tick"])
def test_R_083_03_control_one_wardens_heal_and_hit_ticks_are_silent(inv, gain, hit):
    """R-083-03 control: a heal of exactly 0.075, no heal, and a tick on which the unit was shot (hp arithmetic mixes damage and heal there) are silent."""
    assert _heal(inv, gain, hit).violations == []


# ------------------------------------------------------------------ continuity

def _jump(inv, dist, layers=(0, 0), neighbour=False):
    after = {1: row(100 + dist, 100, layer=layers[1]), 2: row(900, 900, side=1)}
    if neighbour:
        after[3] = row(100 + dist + 30, 100)
    return run(inv, trace({1: row(100, 100, layer=layers[0]), 2: row(900, 900, side=1)}, after), only=["continuity"], max_step={1: 3.5, 2: 3.5, 3: 3.5})


def test_continuity_a_jump_beyond_max_speed_plus_slack_is_flagged(inv):
    """continuity (DRAFT-inv-step-slack 1.3): planted, unit 1 moves 25 wu in a tick with max_step 3.5 and no neighbour; with a layer change too."""
    plain = _jump(inv, 25.0)
    layered = _jump(inv, 25.0, layers=(0, 1))
    assert [(v["rule"], v["tick"], v["unit"]) for v in plain.violations] == [("continuity", 1, 1)] and len(layered.violations) == 1


@pytest.mark.parametrize("dist,neighbour", [(4.7, False), (6.5, True)], ids=["within-3.5-plus-1.3", "pushed-by-a-neighbour"])
def test_continuity_control_a_step_within_the_slack_or_a_push_is_silent(inv, dist, neighbour):
    """continuity control: 4.7 wu (max 3.5 + 1.3 = 4.8) is silent; 6.5 wu with a unit within 40 wu is a push of at most DRAFT-inv-push-allowance 2.0 over
    the limit (4.8 + 2.0 = 6.8), silent. (Engine rules round 2: this was 25 wu; a push no longer excuses a leap, see test_invariants_tightened.py.)"""
    assert _jump(inv, dist, neighbour=neighbour).violations == []


# ------------------------------------------------------------------ suspension and selection

def test_a_suspended_rule_reports_the_switch_and_no_violation(inv):
    """F0: 'a layout whose check depends on a switch the run turned off reports `suspended: <switch>` for that check, never a silent pass'.
    The planted R-087-03 swap above is not reported when the rule is suspended, and the report says which switch."""
    frames = []
    for t in range(0, 6):
        frames.append({1: row(100, 100, target=0 if t == 0 else (2 if t < 3 else 4)), 2: row(300, 100, side=1), 4: row(250, 120, side=1)})
    rep = run(inv, trace(*frames), only=["R-087-03"], sensor_radius={1: 100.0}, suspended={"R-087-03": "OM_TP_TARGET_BY_SIGHT"})
    assert (rep.violations, rep.suspended, rep.invalid) == ([], {"R-087-03": "OM_TP_TARGET_BY_SIGHT"}, False)


def test_only_selects_the_rules_checked(inv):
    """check(..., only=[rule]) checks that rule alone: a trace with an R-207-06 and an R-207-07 fault reports one rule under each selection."""
    tr = trace({1: row(450, 450)}, {1: row(550, 450)}, {1: row(4100, 450)})
    both = run(inv, tr, blocked_cell=cell5_4)
    assert {v["rule"] for v in both.violations} >= {"R-207-06", "R-207-07"}
    assert {v["rule"] for v in run(inv, tr, only=["R-207-07"], blocked_cell=cell5_4).violations} == {"R-207-07"}


def test_violations_are_ordered_by_tick_rule_unit(inv):
    """The report is ordered, so the first 20 written to a fight file are the earliest."""
    tr = trace({1: row(450, 450), 2: row(450, 460)}, {1: row(550, 450), 2: row(550, 460)}, {1: row(560, 450), 2: row(4100, 460)})
    keys = [(v["tick"], v["rule"], v["unit"]) for v in run(inv, tr, blocked_cell=cell5_4).violations]
    assert keys == sorted(keys) and len(keys) >= 3
