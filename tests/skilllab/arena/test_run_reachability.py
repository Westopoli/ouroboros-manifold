# spec: docs/stories/H-063.md (arena stage 3); Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn
"""H-063, the arena asks the engine for blocking and REJECTs a layout whose attackers cannot reach the defenders (scripts/skilllab/arena/run.py).

Story line proved here: "The arena asks the engine for blocking (the ground lab's preflight route check in `scripts/skilllab/scenes_ground.py` is the pattern) and
REJECTs a layout whose attackers cannot reach the defenders, with a line naming the first unreachable unit (a new rule id, the next free in `rules.toml`; test with a
positive control)." Tests line: "`test_run.py` (the unreachable-layout REJECT with the unit named; control: a reachable layout runs)". This file sits beside
test_run.py (new file, test_run.py untouched).

Fixture: `city` on small_flat, orders hold:A, so side B is the attacker. B's units 2 and 5 each stand in a one-unit pen of four 40 wu building strips (80 wu inside,
60 wu from every strip centre, so R6's 15 wu standoff holds); the pens are closed. The control opens the top strip of both pens. Premises dumped on base aac0cd41:
the stage 2 runner ignores features, so both layouts run to a result today (exit 0): the control is green today and the closed pens are red.

Rule id: the story says "the next free in `rules.toml`" without a number (R7 is H-053's arc placement, so R8 on a tree that has it). The tests take the one id
above R7 from `rules.toml` instead of pinning a number (question for the Architect in the report)."""
import re

import h063_fixtures as fx
from scripts.skilllab.catalogue import produce

KNOWN = {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}   # R1 to R6 are H-025's, R7 is H-053's arc placement
PENS = {2: (3000.0, 2800.0), 5: (3000.0, 3300.0)}


def _pen(cx, cy, open_top):
    strips = [fx.rect(cx, cy + 60, 200, 40), fx.rect(cx - 60, cy, 40, 200), fx.rect(cx + 60, cy, 40, 200)]
    if not open_top:
        strips.append(fx.rect(cx, cy - 60, 200, 40))
    return strips


def pen_layout(lid, open_top):
    buildings = [r for cx, cy in PENS.values() for r in _pen(cx, cy, open_top)]
    feature = {"kind": "city", "x": 2000.0, "y": 2000.0, "radius": 800, "buildings": buildings}
    lay = fx.layout(lid, "city", "small_flat", feature, orders="hold:A")
    for i, (cx, cy) in PENS.items():
        lay["side_b"]["units"][i].update(x=cx, y=cy)
    return lay


def _new_rule_ids():
    return sorted(set(produce.rules()) - KNOWN)


def test_control_pen_fixture_is_legal_and_both_layouts_run_today(tmp_path):
    """H-063 "test with a positive control". CONTROL "control: a reachable layout runs" (green today, must stay green): both pen layouts pass check_layout (R1 to R7) and the
    open-topped one, reachable, runs to a result with exit 0 and a fight file, so the REJECT below is the reachability check and not a bad fixture."""
    pre, rul = produce.presets(), produce.rules()
    assert produce.check_layout(pen_layout("L-9130", False), pre, rul) == []
    assert produce.check_layout(pen_layout("L-9131", True), pre, rul) == []
    proc, doc = fx.fight(pen_layout("L-9131", True), tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 0, proc.stdout[-300:] + proc.stderr[-500:]
    assert doc is not None


def test_rules_toml_carries_one_new_reachability_rule():
    """H-063 "a new rule id, the next free in `rules.toml`" and Files "rules.toml and produce.py (the reachability rule)". rules.toml has exactly one id beyond
    R1 to R7, with a text that mentions reach."""
    new = _new_rule_ids()
    assert len(new) == 1, "want exactly one new rule id beyond R1 to R7, rules.toml has %r" % (new,)
    assert "reach" in produce.rules()[new[0]]["text"].lower()


def test_closed_pens_reject_naming_the_first_unreachable_unit(tmp_path):
    """H-063 "REJECTs a layout whose attackers cannot reach the defenders, with a line naming the first unreachable unit". Closed pens around B units 2 and 5: exit
    2, a REJECT line for the layout id carrying the new rule id and `unit 2` (the first, by the row index convention of check_layout's own messages, `side_b unit 2`;
    the format is a question for the Architect), no fight file."""
    proc, doc = fx.fight(pen_layout("L-9130", False), tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 2, "exit %d: %s" % (proc.returncode, (proc.stdout + proc.stderr)[-400:])
    new = _new_rule_ids()
    assert len(new) == 1, "rules.toml carries %r above R7, want exactly one new rule" % (new,)
    lines = [l for l in proc.stdout.splitlines() if l.startswith("REJECT L-9130")]
    assert any(new[0] in l for l in lines), "no REJECT line with %s: %r" % (new[0], proc.stdout[-400:])
    line = next(l for l in lines if new[0] in l)
    assert re.search(r"\bunit 2\b", line) and re.search(r"side_b|\bB\b", line), line
    assert not re.search(r"\bunit 5\b", line), "the line names a later unit as well as the first: " + line
    assert doc is None, "a fight file was written for a rejected layout"
