# Rule pins: R-087-09, R-087-03, R-190-07
"""Engine rule fixes 2026-11-08, F5, whole fights: a unit with a blocked line finds a firing spot or gives the target up after 1 s.

Spec: docs/northstar/plans/engine-rules-2026-11-08/spec.md "F5" and "Test architecture" (whole-run, per tick, the real lab engine, sight on,
walking units, the lab's boxes, catalogue layouts). Evidence: docs/reports/2026-11-07-rule-enforcement.md (sweep I4b, 3.5 million unit-ticks).
The single geometry is tests/csim/test_E11_R087_09_blocked_line_gives_up.py.

Rule word for word (docs/bible/epics/E-11-units-and-combat.md, R-087-09): "Given an idle or attack-moving unit with a target within its attack
range whose line of fire is blocked by units, cover or ground, When evaluated, Then it steers around the blockers by the probe of blocked
movement (R-097-03) until it reaches a spot with a clear line, and if it finds none within 1 s (20 ticks) it drops the target and acquires another
(...). An obstacle is a detour, never a full stop (E-17 R-190-07)."

The judge is the F0 checker's own `R-087-09` check, scripts/skilllab/invariants.py, run after every tick by `run.fight`: a target held more than
DRAFT-inv-stuck-ticks 20 ticks, not shootable, while the unit does not close in. These tests read the checker's complete violation list (the fight
document keeps only the first 20 of all rules) by wrapping `invariants.Monitor` for the call; the checker is not changed.

Configuration: `run.fight(layout, seed 1, sight "on", 100 simulated seconds)`: the lab's stage 4 rule set, walking units, the layout's boxes laid
as the lab lays them, targeting by sight on. Nothing is switched off.

Measured on the unfixed tree (2026-11-11, seed 1, 2000 ticks): R-087-09 violations L-0039 (cover boxes) 0, L-0046 (city) 335, L-0057
(chokepoint) 44, L-0060 (chokepoint) 30 (one of them a guard); whole catalogue, 84 layouts: also L-0043, L-0045, L-0055, L-0056, L-0058, L-0059, L-0063, L-0075, L-0076,
L-0080 to L-0083 (1 to 44 each). L-0039 is green today and is the control: a layout the checker can judge and finds clean.

Note for the implementer and the Architect (not a test): the checker's `R-087-09` counts any held target that cannot be shot, including one
beyond attack range that the unit fails to close on (L-0046 unit 68: 383 wu away); it does not know guards (L-0058, a hold:A layout, trips it on side
A, the guards). The rule text names an idle or attack-moving unit with the target in range; a guard is F6's. Whether the check should exempt a guard
is for the Architect; these tests choose layouts where the units that trip it are not guards (L-0046 orders both sides to one point, no guards; L-0057 trips
only on side B, the attackers). L-0060 is left out: 29 of its 30 are side B, one is a guard.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_rules_oracle as oracle  # noqa: E402
from scripts.skilllab import invariants  # noqa: E402
from scripts.skilllab.arena import run  # noqa: E402

RULE = "R-087-09"
SECONDS = oracle.FIGHT_SECONDS      # DRAFT-oracle-seconds 100 (2000 ticks)
MIN_TICKS = 300                     # detector bound: a fight shorter than this did not exercise the rule
_CACHE = {}


def judged(name):
    """(Monitor, ticks) of catalogue layout `name` fought as the lab fights it with sight on; cached for the session."""
    if name not in _CACHE:
        caught = []

        class Capture(invariants.Monitor):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                caught.append(self)

        original = invariants.Monitor
        invariants.Monitor = Capture
        try:
            _, last, _, _ = run.fight(oracle.catalogue(name), 1, "on", SECONDS, 100000)
        finally:
            invariants.Monitor = original
        assert len(caught) == 1, "expected the fight to build exactly one Monitor, got %d" % len(caught)
        _CACHE[name] = (caught[0], last)
    return _CACHE[name]


def test_R_087_09_the_checker_knows_the_rule():
    """Control (green today): R-087-09 is one of the checks scripts/skilllab/invariants.py runs and is not suspended by a sight-on run."""
    assert RULE in invariants.RULES
    assert RULE not in invariants.suspended_for("on")


def test_R_087_09_control_a_layout_the_checker_finds_clean_is_clean():
    """Control (green today): L-0039 (cover boxes), sight on, fought 2000 ticks, no R-087-09 violation, and the fight ran to the cap with all units
    judged. It proves the Monitor wrapper reads a real fight, so the red layouts below are red for the rule's sake."""
    m, last = judged("L-0039")
    assert last >= MIN_TICKS, "scene broken: the fight is %d ticks long" % last
    assert m.tick == last
    bad = [v for v in m.violations if v["rule"] == RULE]
    assert not bad, "L-0039: %d R-087-09 violations, first %s" % (len(bad), bad[:2])


@pytest.mark.parametrize("name", ["L-0039", "L-0046", "L-0057"])
def test_R_087_09_no_unit_holds_a_target_it_cannot_shoot_for_more_than_20_ticks(name):
    """R-087-09, per tick over a whole fight, sight on, walking units, the layout's boxes: no unit holds a target it cannot shoot for more than 20
    ticks without closing in; it finds a firing spot or drops the target and acquires another. L-0039 cover boxes (green today), L-0046 a city,
    L-0057 a chokepoint. Red today: 335 / 44 violations in the last two (a unit holds an unshootable target for ever)."""
    m, last = judged(name)
    assert last >= MIN_TICKS, "scene broken: %s ran %d ticks" % (name, last)
    bad = [v for v in m.violations if v["rule"] == RULE]
    units = len({v["unit"] for v in bad})
    assert not bad, "%s: %d R-087-09 violations in %d units over %d ticks, first %s" % (name, len(bad), units, last, bad[:2])
