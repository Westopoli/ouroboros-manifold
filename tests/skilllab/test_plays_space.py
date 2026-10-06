# spec: docs/northstar/plans/2026-10-05-space-lab-stage1-spec.md, lane "plays" (drafts, none measured)
"""Registered space-lab draft plays: valid Setups, a 50-tick real-engine run, words/skill/status/numbers, a page that
regenerates byte-identically, and registry entries in skills.py pointing at the plays.
Reading: PlayDraft.setup_fn takes no arguments and returns a Setup whose side 0 fields 16 units.
The lab has no integration marker; the engine test is the only one that loads the library (like tests/skilllab/integration)."""
import dataclasses
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import plays_space, skills, timeline  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402

SKILLED = ("s1_hold_choke", "s2_concave", "s2_spread_line", "s2_screen", "s3_types_by_reach", "s4_bait",
           "s5_vulnerable_away")
COUNTERS = ("s2_mass_one_end", "s4_do_not_chase", "s1_outrange")
NAMES = SKILLED + COUNTERS
STATUS = "unconfirmed draft, not measured"
UNITS = 16
TICKS = 50


def test_registry_holds_exactly_the_registered_plays():
    assert set(plays_space.PLAYS) == set(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_play_builds_a_valid_setup_of_16_units(name):
    setup = plays_space.PLAYS[name].setup_fn()
    assert isinstance(setup, Setup)
    timeline.validate(setup)
    assert sum(g.count for g in setup.groups if g.side == 0) == UNITS
    assert sum(g.count for g in setup.groups if g.side == 1) >= 1


@pytest.mark.parametrize("name", NAMES)
def test_play_has_words_skill_status_and_a_named_number(name):
    p = plays_space.PLAYS[name]
    assert isinstance(p.words, str) and p.words.strip()
    assert p.skill in ("S1", "S2", "S3", "S4", "S5") and name.startswith(p.skill.lower() + "_")
    assert p.status.startswith(STATUS)
    assert isinstance(p.numbers, dict) and len(p.numbers) >= 1
    assert all(isinstance(k, str) and k and isinstance(v, (int, float)) for k, v in p.numbers.items())
    assert isinstance(p.timeline, tuple)


@pytest.mark.parametrize("name", NAMES)
def test_play_runs_50_ticks_on_the_open_map_in_the_real_engine(name):
    from scripts.skilllab.fight import fight
    setup = plays_space.PLAYS[name].setup_fn()
    result = fight(dataclasses.replace(setup, max_ticks=TICKS, terrain=None), seed=0)
    assert result.ticks <= TICKS


def test_page_renders_byte_identically_and_names_every_play():
    a, b = plays_space.render_drafts_page(), plays_space.render_drafts_page()
    assert isinstance(a, str) and a == b and a.encode() == b.encode()
    for name in NAMES:
        assert name in a
    assert STATUS in a


@pytest.mark.parametrize("name", NAMES)
def test_skills_registry_points_at_the_play_with_status_draft(name):
    p = plays_space.PLAYS[name]
    role = "counter" if name in COUNTERS else "skilled"
    entry = skills.get(p.skill, role)
    assert entry.status == "draft"
    assert entry.skill == p.skill and entry.role == role
