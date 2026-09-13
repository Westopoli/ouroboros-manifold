"""
Guard: bible files use asteroid/LOS language; no polygon-model or cover_density-damage-formula phrasing.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORLD = REPO / "docs/bible_history/bible_2_00_world.md"
COMBAT = REPO / "docs/bible_history/bible_2_00_combat.md"

world_text = WORLD.read_text()
combat_text = COMBAT.read_text()


# --- required tokens ---

def test_world_has_asteroid():
    assert "asteroid" in world_text.lower(), "docs/bible_history/bible_2_00_world.md missing 'asteroid'"


def test_world_has_los():
    pattern = re.compile(r"line.of.sight|line of sight|\blos\b", re.IGNORECASE)
    assert pattern.search(world_text), "docs/bible_history/bible_2_00_world.md missing LOS language"


def test_combat_has_asteroid():
    assert "asteroid" in combat_text.lower(), "docs/bible_history/bible_2_00_combat.md missing 'asteroid'"


def test_combat_has_los():
    pattern = re.compile(r"line.of.sight|line of sight|\blos\b", re.IGNORECASE)
    assert pattern.search(combat_text), "docs/bible_history/bible_2_00_combat.md missing LOS language"


# --- forbidden tokens ---

def test_world_no_polygon_los_blocker():
    assert "polygon LOS-blocker" not in world_text, \
        "docs/bible_history/bible_2_00_world.md still has Wave-2.5 'polygon LOS-blocker' language"


def test_world_no_same_polygon():
    assert "same polygon" not in world_text, \
        "docs/bible_history/bible_2_00_world.md still has Wave-2.5 'same polygon' language"


def test_combat_no_polygon_los_blocker():
    assert "polygon LOS-blocker" not in combat_text, \
        "docs/bible_history/bible_2_00_combat.md still has Wave-2.5 'polygon LOS-blocker' language"


def test_combat_no_same_polygon():
    assert "same polygon" not in combat_text, \
        "docs/bible_history/bible_2_00_combat.md still has Wave-2.5 'same polygon' language"


def test_combat_no_cover_density_damage_formula():
    # Matches (1.0 - cover_density) or (1 - cover_density) style damage formula
    pattern = re.compile(r"\(1\.0?\s*[-\u2212]\s*cover_density\)")
    assert not pattern.search(combat_text), \
        "docs/bible_history/bible_2_00_combat.md still has cover_density damage-multiplier formula"


def test_world_no_cover_density_damage_formula():
    pattern = re.compile(r"\(1\.0?\s*[-\u2212]\s*cover_density\)")
    assert not pattern.search(world_text), \
        "docs/bible_history/bible_2_00_world.md still has cover_density damage-multiplier formula"


def test_world_no_polygon_cover_definition():
    """cover_density definition must not describe polygonal regions."""
    assert "polygonal regions that block line of sight" not in world_text, \
        "docs/bible_history/bible_2_00_world.md cover_density still uses old polygon-region definition"


def test_combat_no_symmetric_blind():
    """Cover & Vision section must not reference symmetric-blind polygon cover model."""
    assert "symmetric blind" not in combat_text and "observer-in-cover blind" not in combat_text, \
        "docs/bible_history/bible_2_00_combat.md still references symmetric-blind polygon cover model"
