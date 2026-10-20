# Rule pins: R-104-01@d9c166, R-235-01@4f35af, R-235-03@14ac1a, R-235-04@a81fce
"""Story play S-235 (E-16): "The map shows the economy and its news." Moment `ticker_and_markers`: the player has marched to
contact in the ground era, a strongpoint was taken or lost, the ticker names it once, and the strongpoint and home-base marks are on
the map. Piece E1w (wiring of scenes/economy/ticker_beats.gd and scenes/economy/map_markers.gd into the tactical view); tests in
tests/test_vg_e_e1w.gd. Screenshot and qa_state go to docs/northstar/story_reviews/shots/<run id>/.

Rules, word for word (docs/bible/epics/E-16-client-camera-hud-and-world-view.md:271-274, :70):
  R-235-01  Given the map view (S-161) and the tactical view, When the economy's places are drawn, Then the economic locations, the
            neutral settlements, the objective, the side's base of operations, its expansions and forward works, and on land maps
            the strongpoints are marked (E-22 S-175, S-177; E-15).
  R-235-03  Given the ticker (R-104-01), When a base is occupied, a side falls back to an expansion, an expansion is founded, a
            weather trouble arrives, or a strongpoint is taken or lost, Then the ticker names it; no other economy beat reaches the
            ticker (Westley, 2026-10-12).
  R-235-04  Given a shipment that does not arrive (E-22 S-176), When the ticker, the banners and the map are read, Then nothing on
            them explains why.
  R-104-01  Given a mission, When the HUD is drawn, Then the player can always see the objective list with progress (top-left) and a
            quiet ticker of notable beats beneath it; the ticker recognizes structure captured, structure lost, force routed, and
            objective threshold crossed, and nothing else at launch.

Ground era only (--era greek_placeholder): strongpoints stand on land maps (R-235-01, S-218). Seed 1, 1920x1080, vulkan renderer.

What the play drives (GAP 8 ruling, Architect 2026-10-14): it selects the army, attack-moves it to the nearest enemy (the S-134 march to
first contact, fog filter off as that play) and marches with step_ticks in blocks of BLOCK_TICKS, up to DRAFT-s235-budget ticks, and
takes the shot at the FIRST strongpoint beat on the ticker. A strongpoint beat MUST arrive by the cap (Architect round 3): none by the cap makes this play RED,
which is a FINDING (reported with the decisive line); no shot is taken and there is no "no beat in this shot" label.

STUB (not asserted here, listed as stub in the report and the queue row): the base occupied, fall back to an expansion, expansion
founded and weather arriving beats (FU-E1m-beat-base_occupied, -fallback, -expansion, -weather: no sim source, G3 a); the marks for
economic locations, neutral settlements, expansions, forward works and weather (G6). The four beats are proven by tests/test_vg_e_e1w.gd
([ORDER], emit_beat and the A8 listening path); the strongpoint beat by its [BEAT] group from a fixture frame.

How the ticker is read: qa_state carries only the count (inventory hud.events); the lines are read from the text of the Events label in
the scene tree (client.tree()), one line per beat. A line that names a strongpoint is a strongpoint beat; "taken" or "lost" in it picks
the kind (the beat texts are DRAFT-e1m-beat-text, so only those two words are read).

Red on origin/main for the stated reason: qa_state has no `map_markers` key (the first assert below)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "K"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "A"))
from _k_common import GodotGame, moment, pick_free_port, step_ticks, to_tactical  # noqa: E402
from play_support import _edge_scroll_to, nearest_enemy_px, select_own_by_drag  # noqa: E402

STORY = "S-235"

# DRAFT-s235-budget (named draft, ledger row; Westley's to change): the cap, in game ticks, on the march to the first strongpoint beat.
# The measured march to first contact at seed 1 is 5382 ticks (visible-game spec, A17 contact budgets paragraph, line 343); plus 10 percent
# = 5920, the same figure as DRAFT-a17-contact-budget. No beat by the cap makes the play RED (a finding), never a skip.
DRAFT_S235_BUDGET = 5920
BLOCK_TICKS = 25  # step_ticks block (the TD-VG-A-1 chunk of the S-134 play)
# Beat kinds the ticker may carry (R-235-03); a marker kind is one of two (G6 ruling).
KINDS = {"base_occupied", "fallback", "expansion", "weather", "strongpoint_taken", "strongpoint_lost"}
MARKER_KINDS = {"strongpoint", "home_base"}


@pytest.fixture(scope="module")
def game():
    g = GodotGame(qa_port=pick_free_port(), seed=1, resolution="1920x1080", extra_args=["--era", "greek_placeholder"], renderer="vulkan")
    g.start()
    g.wait_for_port(timeout=60.0)
    r = g.client.call("set_fog_filter", False)  # TD-VG-A-5: the march reads enemy positions (nearest_enemy_px), as the S-134 play
    assert r.get("ok", True), "S-235: set_fog_filter refused: %r" % r
    yield g
    g.stop()


def ticker_lines(client):
    """The ticker lines as text, read from the Events label: the first Label under Hud/Events (the second is the banner). Both are
    unnamed nodes (auto names such as @Label@12), so the control is found by class and parent, not by name."""
    for ctl in client.tree()["result"]["controls"]:
        if "/Events/" in ctl["path"] and ctl["class"] == "Label":
            return [ln for ln in str(ctl.get("text", "")).split("\n") if ln.strip()]
    return []


def beat_kind(line):
    """strongpoint_taken / strongpoint_lost for a line that names a strongpoint, else None."""
    low = line.lower()
    if "strongpoint" not in low:
        return None
    if "taken" in low and "lost" not in low:
        return "strongpoint_taken"
    if "lost" in low and "taken" not in low:
        return "strongpoint_lost"
    return "strongpoint_?"


def structure_lines(lines):
    return [ln for ln in lines if ln.lower().startswith("structure")]


def test_detector_controls():
    """Positive controls for this file's detectors (they run without the game)."""
    assert beat_kind("Strongpoint taken") == "strongpoint_taken", "CONTROL: a taken line is not read as taken"
    assert beat_kind("Strongpoint lost") == "strongpoint_lost", "CONTROL: a lost line is not read as lost"
    assert beat_kind("Structure lost") is None, "CONTROL: a Structure line is read as a strongpoint beat"
    assert structure_lines(["Objective 25%", "Structure captured"]) == ["Structure captured"], "CONTROL: structure_lines misses a Structure line"


def test_s_235_ticker_names_a_strongpoint_and_the_map_marks_it(game):
    c = game.client
    qa = to_tactical(c)
    # R-235-01: the places drawn are marked; here the strongpoints and the base of operations (G6).
    assert "map_markers" in qa, "S-235: R-235-01 qa_state has no `map_markers` key (keys: %s)" % sorted(qa)
    marks = qa["map_markers"]
    assert marks, "S-235: R-235-01 map_markers is empty at the start of the mission"
    kinds = {m["kind"] for m in marks}
    assert "strongpoint" in kinds, "S-235: R-235-01 no strongpoint marker on a land map (kinds: %s)" % sorted(kinds)
    assert "home_base" in kinds, "S-235: R-235-01 no home_base marker, the side's base of operations (kinds: %s)" % sorted(kinds)
    assert kinds <= MARKER_KINDS, "S-235: R-235-01 / G6 a marker kind outside %s: %s" % (sorted(MARKER_KINDS), sorted(kinds - MARKER_KINDS))
    for m in marks:
        assert isinstance(m["owner"], int) and isinstance(m["state"], int), "S-235: R-235-01 marker without int owner and state: %r" % m
    assert qa["inventory"]["map_markers"] == len(marks), "S-235: the inventory map_markers is not the count of qa_state map_markers"
    assert not ticker_lines(c), "S-235: R-235-03 the ticker already carries a line at tick 0: %r" % ticker_lines(c)

    # March to contact: the army attack-moves to the nearest enemy (as the S-134 play), then steps in blocks (GAP 8).
    start_owner = {(m["x"], m["y"]): m["owner"] for m in marks if m["kind"] == "strongpoint"}
    select_own_by_drag(c)
    ex, ey = nearest_enemy_px(c, qa)
    c.call("input", "key", "A")
    c.call("input", "click", ex, ey, 1)

    stepped, sp_lines, before_structure = 0, [], len(structure_lines(ticker_lines(c)))
    while stepped < DRAFT_S235_BUDGET:
        step_ticks(c, BLOCK_TICKS)
        stepped += BLOCK_TICKS
        lines = ticker_lines(c)
        sp_lines = [ln for ln in lines if beat_kind(ln)]
        if sp_lines:
            break
    # A strongpoint beat MUST arrive by the cap (Architect round 3): none is a FINDING, the play is RED, no shot.
    assert sp_lines, "S-235: FINDING R-235-03 no strongpoint beat on the ticker in %d ticks of march (DRAFT-s235-budget %d); ticker %r, markers %r" % (stepped, DRAFT_S235_BUDGET, ticker_lines(c), c.state()["result"]["qa"].get("map_markers"))

    # The beat is on the ticker: bring the strongpoint mark that changed hands (else the first) on screen and take the shot.
    q = c.state()["result"]["qa"]
    sps = [m for m in q["map_markers"] if m["kind"] == "strongpoint"]
    hit = next((m for m in sps if start_owner.get((m["x"], m["y"])) != m["owner"]), sps[0])
    c.call("input", "move", 960, 540)
    r = c.call("project", float(hit["x"]), float(hit["y"]))
    if not (r.get("ok") is True and r["result"].get("on_screen")):
        assert _edge_scroll_to(c, float(hit["x"]), float(hit["y"]), q["camera"]), "S-235: a strongpoint mark never came on screen for the shot"
    shot = moment(c, STORY, "ticker_and_markers")

    # Inventory asserts, each naming its rule (the INVENTORY of the brief).
    marks = shot["map_markers"]
    assert any(m["kind"] == "strongpoint" for m in marks) and any(m["kind"] == "home_base" for m in marks), "S-235: R-235-01 the strongpoint or home_base mark is gone from the shot: %r" % marks
    assert all(isinstance(m["owner"], int) and isinstance(m["state"], int) for m in marks), "S-235: R-235-01 marker owner/state not ints in the shot: %r" % marks
    assert {m["kind"] for m in marks} <= MARKER_KINDS, "S-235: R-235-03 / G6 a marker kind outside %s: %r" % (sorted(MARKER_KINDS), marks)
    lines = ticker_lines(c)
    assert shot["inventory"]["hud"]["events"] >= 1, "S-235: R-235-03 hud.events is 0 although the ticker carried a strongpoint line"
    seen = [beat_kind(ln) for ln in lines if beat_kind(ln)]
    assert seen and set(seen) <= {"strongpoint_taken", "strongpoint_lost"}, "S-235: R-235-03 the strongpoint beat kind is neither strongpoint_taken nor strongpoint_lost: %r (lines %r)" % (seen, lines)
    assert len(sp_lines) == 1, "S-235: R-235-03 / G2 the first strongpoint event is not exactly one ticker line: %r" % sp_lines
    assert len(structure_lines(lines)) == before_structure, "S-235: R-235-03 / G2 a Structure captured / lost line came with the strongpoint line: %r" % lines
    assert not any("shipment" in ln.lower() for ln in lines), "S-235: R-235-04 a ticker line mentions a shipment: %r" % lines
    others = [ln for ln in lines if not beat_kind(ln) and not ln.lower().startswith(("objective", "structure"))]
    assert not others, "S-235: R-235-03 / R-104-01 a ticker line outside the strongpoint, structure and objective beats: %r" % others
    assert not any(k not in KINDS for k in seen), "S-235: R-235-03 a beat kind outside KINDS: %r" % seen
