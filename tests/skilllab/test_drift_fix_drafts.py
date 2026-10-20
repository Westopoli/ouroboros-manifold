# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 41 ruling 7 (Architect, 2026-10-19): the lab's own draft numbers are marked DRAFT
# in code and in the artifact header; dead logic is deleted
"""LAB-REV2-FIX: DRAFT marks in code.

INTERFACE (frozen here for the builder): the mark is the word `DRAFT` on the DEFINITION LINE of the constant, in a trailing comment (or
the line's own text), found by grep of the source. No registry, no new module. The lines:
  scripts/skilllab/scan.py            the line that defines COARSE_STEP: carries the name `DRAFT-coarse-step`
  scripts/skilllab/sweep.py           the line that defines CONTROL_MAX_TICKS: carries the name `DRAFT-control-max-ticks`
  scripts/skilllab/scenes.py          the line that defines BEHIND_COVER: carries `DRAFT-behind-cover`; AMBUSH_BEHIND: `DRAFT-ambush-behind`
LAB-REV2-FIX round 5 (decision 45, Architect 2026-10-19; ledger TD-LAB-REV2-FIX5-draft-names): the mark on those four lines is the Architect's NAME
(DRAFT-<name>), not the bare word; the bare word `DRAFT` still marks the five ground definitions and the lines of the positive control. The roster
mixes carry DRAFT-mix-M1..M4 and DRAFT-mix-M3b on the rows of the MIXES table (test_plays_space_mixes.py). DRAFT-probe-count-bound has no definition
line (the bound is derived in the tests from COARSE_STEP: tests/skilllab/fakes_scans.probe_bound), so no code line is pinned for it.
  scripts/skilllab/ground/scenes_ground.py   the line `return 30 + 3 * math.sqrt(n)` of _holder_radius and the one-line definitions of
                                      NATURAL_ATTACKERS, NATURAL_HOLDERS, MARGINAL_ATTACKERS, MARGINAL_HOLDERS, FLYER_ATTACKERS (the five
                                      coordinate pairs and the radii 20, 12 and 8 sit on those lines)
The names the artifact header lists (DRAFT-coarse-step, DRAFT-control-max-ticks, DRAFT-probe-count-bound, DRAFT-ground-geometry) are pinned
in test_report.py. The at-most-14 probe bound has no constant in the code (it is the bisection's property and a number in the tests), so no code
line is pinned for it (Q-FIX-3). plays.MAX_TICKS_BIG is deleted (test_plays_max_ticks.py)."""
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "scripts" / "skilllab"

NAMED = [    # (file, definition line, the Architect's name that line must carry; TD-LAB-REV2-FIX5-draft-names)
    ("scan.py", r"^COARSE_STEP\s*=", "DRAFT-coarse-step"),
    ("sweep.py", r"^CONTROL_MAX_TICKS\s*=", "DRAFT-control-max-ticks"),
    ("scenes.py", r"^BEHIND_COVER\s*=", "DRAFT-behind-cover"),
    ("scenes.py", r"^AMBUSH_BEHIND\s*=", "DRAFT-ambush-behind"),
]

DEFINITIONS = [
    ("ground/scenes_ground.py", r"return 30 \+ 3 \* math\.sqrt\(n\)"),
    ("ground/scenes_ground.py", r"^NATURAL_ATTACKERS\s*="),
    ("ground/scenes_ground.py", r"^NATURAL_HOLDERS\s*="),
    ("ground/scenes_ground.py", r"^MARGINAL_ATTACKERS\s*="),
    ("ground/scenes_ground.py", r"^MARGINAL_HOLDERS\s*="),
    ("ground/scenes_ground.py", r"^FLYER_ATTACKERS\s*="),
]


def line_of(path, pattern):
    hits = [ln for ln in (SRC / path).read_text().splitlines() if re.search(pattern, ln)]
    assert len(hits) == 1, "%s: %d lines match %r (want exactly one definition line)" % (path, len(hits), pattern)
    return hits[0]


@pytest.mark.parametrize("path,pattern", DEFINITIONS)
def test_the_definition_line_carries_the_word_draft(path, pattern):
    assert "DRAFT" in line_of(path, pattern)


@pytest.mark.parametrize("path,pattern,name", NAMED)
def test_the_definition_line_carries_the_architects_name(path, pattern, name):
    """Was: the bare word DRAFT on COARSE_STEP and CONTROL_MAX_TICKS (changed, TD-LAB-REV2-FIX5-draft-names). Now the NAME; the name is not a prefix of
    another (DRAFT-coarse-step is not satisfied by a line that only says DRAFT-coarse-steps)."""
    assert re.search(re.escape(name) + r"(?![\w-])", line_of(path, pattern))


def test_control_the_name_check_refuses_a_bare_word_and_a_longer_name():
    """Positive control for the name grep: today's COARSE_STEP comment says `DRAFT (Westley's number)`, which is not the name."""
    for text in ("COARSE_STEP = 8   # DRAFT (Westley's number)", "COARSE_STEP = 8   # DRAFT-coarse-steps"):
        assert not re.search(re.escape("DRAFT-coarse-step") + r"(?![\w-])", text)
    assert re.search(re.escape("DRAFT-coarse-step") + r"(?![\w-])", "COARSE_STEP = 8   # DRAFT-coarse-step (Westley's number)")


def test_the_named_lines_hold_the_numbers_they_name():
    """Control that the pinned lines are the definitions: COARSE_STEP 8, CONTROL_MAX_TICKS 600, BEHIND_COVER 150, AMBUSH_BEHIND 200."""
    for (path, pattern, _), number in zip(NAMED, ("8", "600", "150", "200")):
        assert re.search(r"=\s*%s(\.0)?\b" % number, line_of(path, pattern)), (path, number)


def test_control_a_number_already_marked_is_found_the_same_way():
    """Positive control for the grep: the slope divisor grid and the sweep's base values are marked today."""
    assert "DRAFT" in line_of("ground/scenes_ground.py", r'"OM_TP_SLOPE_UP_DIV":')
    assert "DRAFT" in line_of("sweep.py", r'"OM_TP_FIRING_ARC_DEG": 360\.0, "cone_range"')


def test_the_five_ground_definitions_hold_the_numbers_the_ruling_names():
    """Control that the pinned lines are the ones holding the geometry: radii 20, 12 and 8 and the five anchors."""
    text = "\n".join(line_of("ground/scenes_ground.py", pat) for _, pat in DEFINITIONS)
    for token in ("9330.0", "3135.0", "9050.0", "3180.0", "9220.0", "9320.0", "2954.0", "8900.0", "3220.0", "10550.0", "4350.0",
                  "20.0", "12.0", "8.0", "30 + 3"):
        assert token in text, token
