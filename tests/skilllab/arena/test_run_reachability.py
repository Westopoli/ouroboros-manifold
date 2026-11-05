# Rule pins: none (H-063 names no R-id here; story lines quoted in the docstring, Flag client)
# spec: docs/stories/H-063.md (arena stage 3); Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn
"""H-063, the arena asks the engine for blocking and REJECTs a layout whose attackers cannot reach the defenders (scripts/skilllab/arena/run.py).

Story line proved here: "The arena asks the engine for blocking (the ground lab's preflight route check in `scripts/skilllab/scenes_ground.py` is the pattern) and
REJECTs a layout whose attackers cannot reach the defenders, with a line naming the first unreachable unit (a new rule id, the next free in `rules.toml`; test with a
positive control)." Tests line: "`test_run.py` (the unreachable-layout REJECT with the unit named; control: a reachable layout runs)". This file sits beside
test_run.py (new file, test_run.py untouched).

Fixture: `city` on small_flat, orders hold:A, so side B is the attacker. B's units 2 and 5 each stand in a one-unit pen of four 40 wu building strips (160 wu inside,
100 wu from every strip centre, so R6's 15 wu standoff holds; widened from 80 and 60 for the 50 wu route cells of lab-stage3 criterion 1); the pens are closed. The control opens the top strip of both pens. Premises dumped on base aac0cd41:
the stage 2 runner ignores features, so both layouts run to a result today (exit 0): the control is green today and the closed pens are red.

Rulings (H-063 "Rulings for the build", 1 to 3): the rule is the next free id above R7 (R8 once H-053 has landed); the tests read `rules.toml` for exactly one new id.
The line reads `REJECT <layout id> <rule id> unreachable: side_b unit 2` (row index, side token). Attackers are the side that is not `hold`; for `both_same_point`
every moving unit's route to the point is checked."""
import h063_fixtures as fx
from scripts.skilllab.catalogue import produce

KNOWN = {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}   # R1 to R6 are H-025's, R7 is H-053's arc placement
PENS = {2: (3000.0, 2800.0), 5: (3000.0, 3300.0)}


def _pen(cx, cy, open_top):
    strips = [fx.rect(cx, cy + 100, 280, 40), fx.rect(cx - 100, cy, 40, 280), fx.rect(cx + 100, cy, 40, 280)]
    if not open_top:
        strips.append(fx.rect(cx, cy - 100, 280, 40))
    return strips


def pen_layout(lid, open_top):
    buildings = [r for cx, cy in PENS.values() for r in _pen(cx, cy, open_top)]
    feature = {"kind": "city", "x": 2000.0, "y": 2000.0, "radius": 800, "buildings": buildings}
    lay = fx.layout(lid, "city", "small_flat", feature, orders="hold:A")
    for i, (cx, cy) in PENS.items():
        lay["side_b"]["units"][i].update(x=cx, y=cy)
    return lay


def pen_layout_both(lid):
    """both_same_point: every unit moves to the point, so A unit 1 (moved out to its own closed pen at the west edge) is unreachable too, and it is the only one."""
    lay = pen_layout(lid, True)
    lay["orders"] = "both_same_point"
    lay.pop("defender", None)
    lay["features"][0]["buildings"] = _pen(500.0, 1000.0, False)
    lay["side_a"]["units"][1].update(x=500.0, y=1000.0)
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
    """H-063 "REJECTs a layout whose attackers cannot reach the defenders, with a line naming the first unreachable unit" and ruling 2: "The line reads
    `REJECT <layout id> R8 unreachable: side_b unit 2`". Closed pens around B units 2 and 5 (B attacks, hold:A, ruling 3): exit 2, exactly one such line with the new
    rule id, `unit 2` and no mention of unit 5, no fight file."""
    proc, doc = fx.fight(pen_layout("L-9130", False), tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 2, "exit %d: %s" % (proc.returncode, (proc.stdout + proc.stderr)[-400:])
    new = _new_rule_ids()
    assert len(new) == 1, "rules.toml carries %r above R7, want exactly one new rule" % (new,)
    want = "REJECT L-9130 %s unreachable: side_b unit 2" % new[0]
    lines = [l.strip() for l in proc.stdout.splitlines() if l.startswith("REJECT L-9130") and new[0] in l]
    assert lines == [want], "want exactly %r, got %r" % (want, lines)
    assert doc is None, "a fight file was written for a rejected layout"


def test_both_same_point_checks_every_moving_unit(tmp_path):
    """H-063 ruling 3: "for `both_same_point` every moving unit's route to the point is checked". The unreachable unit is side A's unit 1 (closed pen at the west edge),
    so the line names `side_a unit 1`; the fight is not run."""
    lay = pen_layout_both("L-9132")
    assert produce.check_layout(lay, produce.presets(), produce.rules()) == []
    proc, doc = fx.fight(lay, tmp_path, 1, "--cap-seconds", "5")
    assert proc.returncode == 2, "exit %d: %s" % (proc.returncode, (proc.stdout + proc.stderr)[-400:])
    new = _new_rule_ids()
    assert len(new) == 1, "rules.toml carries %r above R7, want exactly one new rule" % (new,)
    lines = [l.strip() for l in proc.stdout.splitlines() if l.startswith("REJECT L-9132") and new[0] in l]
    assert lines == ["REJECT L-9132 %s unreachable: side_a unit 1" % new[0]], lines
    assert doc is None
