# spec: docs/stories/H-040.md ("Orders and fight end"); docs/northstar/plans/engine-rules-2026-11-08/round6.md (L5); DEC-formation-kept-2026-11-19
"""Round 6, L5: a stage page shows an `apart` end as such, with the nearest distance, and still brings it to him (DEC-formation-kept-2026-11-19).

round6.md L5: "A stage page shows an `apart` end as such, with the nearest distance, and still lists it for him (`docs/stories/H-040.md`: a quiet fight with both sides alive is brought to him; the
label says which kind)."  A stall row today: class `stall` on the row, `end: silence (om-fight-2)` and `<b>stall: bring to Westley</b>` in the result cell (page.py `_row`).

WORDING PINNED HERE (the page builder follows it; the style is page.py's own):
  the result cell of an apart row says `end: apart (om-fight-2)` (the same `end:` line a stall has) and, on a line of its own in bold, `apart: nearest enemies <n> wu: bring to Westley`, n the
  `result.nearest_enemy_wu` of the fight file (test_run_apart_end.py) rounded to a whole number;
  the row carries the class token `apart` (the style defines `.apart`), flagged in a colour of its own; it carries no class `stall` and says nothing of `stall: bring to Westley`: an apart end is not a stall.
Fights ending by wipe or silence are shown as before and never say `apart`.

The v2 documents are built inline as test_page.py builds its stall fixture (`_v2_doc`), and written raw."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.skilllab.arena import snapshot  # noqa: E402
from test_page import _build, _Cells, _stage_v2, _v2_doc, stage  # noqa: E402, F401  (`stage` is the fixture)
from test_page_stage3 import visible  # noqa: E402

APART_WORDS = "apart: nearest enemies 378 wu: bring to Westley"


def _apart(lid="L-0203"):
    """A v2 apart fight: the stall fixture of test_page.py with the end changed to apart, stall false, winner draw, the distance 378 wu."""
    doc = _v2_doc(lid, 2, 3, "A", True)
    doc["result"].update({"end": "apart", "stall": False, "winner": "draw", "nearest_enemy_wu": 378.0})
    return doc


def _classes(page):
    cells = _Cells()
    cells.feed(page)
    return [t for tag, toks in cells.classes for t in toks]


def test_L5_page_shows_an_apart_fight_as_apart_with_the_nearest_distance_and_brings_it_to_him(stage):
    """H-040 "Orders and fight end" / DEC-formation-kept-2026-11-19: an apart fight is listed (not INVALID) with `end: apart`, the words `apart: nearest enemies 378 wu: bring to Westley`, the class `apart`
    on an element and the style rule `.apart`. Red today: `snapshot.validate` rejects the end, so the row is `INVALID L-0203`."""
    doc = _apart()
    assert snapshot.validate(doc) == [], "the apart fixture must be a valid om-fight-2 document: %s" % snapshot.validate(doc)
    _stage_v2(stage, [doc])
    page, _ = _build(stage)
    text = visible(page)
    assert "L-0203" in page and "INVALID L-0203" not in page
    assert "end: apart" in text and APART_WORDS in text, text[:600]
    assert "apart" in _classes(page) and ".apart" in page


def test_L5_page_does_not_show_an_apart_fight_as_a_stall(stage):
    """H-040 / DEC-formation-kept-2026-11-19: an apart end is not a stall: no element of the page carries the class `stall` and the page never says `stall: bring to Westley`. Red today for the
    reason above (the row is INVALID, so the first assertion fails)."""
    _stage_v2(stage, [_apart()])
    page, _ = _build(stage)
    assert APART_WORDS in visible(page)
    assert "stall" not in _classes(page) and "stall: bring to Westley" not in visible(page)


def test_L5_page_keeps_a_stall_and_a_wipe_as_they_were_beside_an_apart_fight(stage):
    """H-040 / DEC-formation-kept-2026-11-19: on one page, the stall fight keeps its class `stall` and `stall: bring to Westley` (once), the wipe fight says neither stall nor apart, and the apart
    fight says `apart: ...` exactly once. Red today: the apart row is INVALID."""
    stall, wipe = _v2_doc("L-0201", 2, 3, "A", True), _v2_doc("L-0202", 2, 3, "A", False)
    _stage_v2(stage, [stall, wipe, _apart()])
    page, _ = _build(stage)
    text = visible(page)
    assert text.count("stall: bring to Westley") == 1 and text.count("apart: nearest enemies") == 1 and "INVALID" not in text
    assert "stall" in _classes(page) and "apart" in _classes(page)


def test_L5_page_without_an_apart_fight_never_says_apart(stage):
    """Control, green today and must stay green: a page of a wipe fight and a stall fight carries no class `apart`, no `apart:` words and no `end: apart`."""
    _stage_v2(stage, [_v2_doc("L-0201", 2, 3, "A", True), _v2_doc("L-0202", 2, 3, "A", False)])
    page, _ = _build(stage)
    assert "apart" not in _classes(page) and "apart:" not in visible(page) and "end: apart" not in visible(page)
