"""Story play S-110 (E-16 "Main menu and settings"): the player opens Settings from the main menu and sees the
galaxy quality choice beside resolution, fullscreen and the other options.

Rule R-110-02 (docs/bible/epics/E-16-client-camera-hud-and-world-view.md:167), word for word: "Given Settings, When
opened, Then it offers resolution, fullscreen, master and music volume, a camera pan-speed slider, and a galaxy
quality choice (full, stand-in, fewer particles) that the player sets by hand and the game never changes on its own;
key rebinding for the layer modifier and control groups joins it once the layer controls (Q-005-03) and the camera
controls (Q-103-04) are designed (Q-110-04); accessibility options (colorblind palette, UI scale) are a later story,
not in the first playtest rounds."

Interface this play fixes (additive keys of the Settings scene qa_state, read from result["qa"]):
  galaxy_quality        int 0..2, the selected item (0 = full, the default with nothing stored; ruling A54)
  galaxy_quality_items  list of 3 strings, in order full, stand-in, fewer particles
Existing keys scene, resolution_index, fullscreen, vsync are unchanged. The storage and apply checks are
tests/test_galaxy_quality_setting.gd; this play asserts only that the control is offered and on screen. Whether the
frame looks right is the reviewer's call on the screenshot. The open OptionButton popup is not drawn in the frame.
The play reads the player's own user://settings.cfg like the neighbouring plays; the default 0 holds while no
galaxy_quality other than 0 is stored there.
"""
import time

import pytest

import _play as P

SETTINGS = "res://scenes/settings/settings.tscn"
VIEWPORT = (1920, 1080)


@pytest.fixture(scope="module")
def game():
    g = P.start_game()
    try:
        yield g
    finally:
        g.stop()


@pytest.fixture(scope="module")
def settings(game):
    """Main menu -> Settings button, then the scene's qa_state, tree and screenshot."""
    c = game.client
    P.reach_main_menu(c)
    P.click_text(c, "settings", "menu")
    P.wait_for(c, lambda s: s.get("scene") == SETTINGS, P.STEP_S * 2, label="settings")
    time.sleep(1.0)  # settle; same value as tests/qa/desktop/plays/B/S-108.py:49
    qa = P.record(c, "S-110")["qa"]
    return qa, c.tree()["result"]["controls"]


def _inside_viewport(control: dict) -> bool:
    x, y, w, h = control["rect_px"]
    return x >= 0 and y >= 0 and x + w <= VIEWPORT[0] and y + h <= VIEWPORT[1]


def _control(controls: list, cls: str, text: str) -> dict | None:
    for c in controls:
        if c.get("class") == cls and text in str(c.get("text") or ""):
            return c
    return None


def test_s110_control_settings_offers_resolution_and_vsync(settings):
    qa, controls = settings
    assert qa["scene"] == "settings", qa
    assert "resolution_index" in qa, qa
    assert "vsync" in qa, qa
    dropdown = _control(controls, "OptionButton", "1920x1080")
    assert dropdown is not None, "no resolution dropdown showing 1920x1080 among %r" % [c.get("text") for c in controls]
    assert _inside_viewport(dropdown), dropdown


def test_s110_inventory_galaxy_quality_choice_is_offered(settings):
    qa, controls = settings
    assert qa["galaxy_quality"] == 0, qa
    items = qa["galaxy_quality_items"]
    assert len(items) == 3, items
    for item, word in zip(items, ("full", "stand", "particle")):
        assert word in str(item).lower(), items
    # An OptionButton showing the first item: the Fullscreen toggle is a Label and cannot match.
    quality = _control(controls, "OptionButton", items[0])
    assert quality is not None, "no OptionButton showing %r among %r" % (items[0], [c.get("text") for c in controls])
    assert _inside_viewport(quality), quality
