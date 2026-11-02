# Rule pins: none (H-063 names no R-id here; story lines quoted in the docstring, Flag client)
# spec: docs/stories/H-063.md (arena stage 3); Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn
"""H-063, the page's control strip (scripts/skilllab/arena/page.py).

Story lines proved here: "the same fight without the geometry beside it as a control strip (the layout with `features` emptied, same units), so the effect of the
ground is visible, not argued." and Files "`scripts/skilllab/arena/page.py` (control strip beside the fight)"; Tests "`test_page.py` (control strip present)". This file
sits beside test_page.py (new file, test_page.py untouched).

Interface (H-063 "Rulings for the build", 6): `page.py --control-dir <dir>`; the control fight of layout <id> seed <n> is `<id>-control-s<n>.fight.json` with its PNGs in
`<id>-control-s<n>/frame-<i>.png`, both in that directory (the runner produces them by emptying `features`), same units in frame 0.

Control (green today): the same fixture without control files builds a page with the layout's own strip, so a red below is the missing control strip."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.arena import snapshot  # noqa: E402
from scripts.skilllab.arena.rate import rate  # noqa: E402

LID = "L-0055"
LAYOUT = """id = "{lid}"
situation = "chokepoint"
landscape = "small_flat"
seed = 1
predict = "A"
predict_why = "WHYCHOKE blue holds the exit."
verdict = ""
feedback = ""
predict_rate = 0.98
what_to_expect = "WHATEXPECT"
approve_means = "APPROVEMEANS"
deny_means = "DENYMEANS"

[side_a]
headcount = 2

[side_b]
headcount = 2
"""


def _png(path):
    import struct
    import zlib
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")) + chunk(b"IEND", b""))


def _stage(tmp_path, control):
    root = tmp_path / "repo"
    out = root / "out"
    (root / "layouts").mkdir(parents=True)
    out.mkdir()
    (root / "layouts" / (LID + ".toml")).write_text(LAYOUT.format(lid=LID))
    (root / "control").mkdir()
    stems = ["%s-s1" % LID] + (["%s-control-s1" % LID] if control else [])
    docs = []
    for stem in stems:
        where = root / "control" if "control" in stem else out
        doc = snapshot.example(frames=3, units_per_side=2, schema=snapshot.SCHEMA_V2)
        doc["layout_id"], doc["layout_path"], doc["seed"] = LID, "layouts/%s.toml" % LID, 1
        doc["result"]["predict"], doc["result"]["agree"] = "A", doc["result"]["winner"] == "A"
        snapshot.write(doc, where / (stem + ".fight.json"))
        (where / stem).mkdir()
        for i in range(3):
            _png(where / stem / ("frame-%d.png" % i))
        docs.append(doc)
    (out / (LID + ".rate.json")).write_text(json.dumps(rate([docs[0]], 0.98), indent=2) + "\n")
    return root, out, docs


def _page(root, out, control=False):
    html = root / "index.html"
    env = {"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin"}
    done = subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.page", "--dir", str(out), "--out", str(html)] + (["--control-dir", str(root / "control")] if control else []), cwd=root, env=env, capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, "page CLI failed: " + done.stderr[-300:]
    return html.read_text()


def test_control_the_page_without_control_files_has_the_layout_strip_only(tmp_path):
    """CONTROL (green today, must stay green): a rated layout with no control files builds, shows its own frame images under `<id>-s1/` and no control strip."""
    root, out, _ = _stage(tmp_path, control=False)
    page = _page(root, out)
    assert len(re.findall(r"%s-s1/frame-\d+\.png" % LID, page)) >= 3
    assert "control" not in page.lower().replace("verdicts", "")


def test_page_shows_a_control_strip_beside_the_fight(tmp_path):
    """H-063 "the same fight without the geometry beside it as a control strip (the layout with `features` emptied, same units)". With control files present the page
    has the layout's strip and a second strip whose frames are the control's (`<id>-control-s1/frame-<i>.png`, all three), the word `control` appears in the layout's
    block, and the control fight's frame 0 holds the same units as the main one (the fixture says so; the page must not drop or reorder them: it lists the control's
    captions `tick <t> A <a> B <b>` for every frame)."""
    root, out, docs = _stage(tmp_path, control=True)
    page = _page(root, out, control=True)
    start = page.index("<h2>%s</h2>" % LID)
    block = re.split(r"<h2>", page[start + 4:], maxsplit=1)[0]   # the layout's block, up to the next heading
    assert sorted(set(re.findall(r"%s-control-s1/frame-(\d+)\.png" % LID, block))) == ["0", "1", "2"], "control frames missing from the layout's block"
    assert len(re.findall(r"%s-s1/frame-\d+\.png" % LID, block)) >= 3, "the layout's own strip vanished"
    assert "control" in re.sub(r'src="[^"]*"', "", block).lower(), "no visible word `control` in the block (a label, not only an image path)"
    assert "pair:" not in page, "the control fight is also listed as a stage 1 row"
    assert [u["id"] for u in docs[0]["frames"][0]["units"]] == [u["id"] for u in docs[1]["frames"][0]["units"]]
    for f in docs[1]["frames"]:
        assert "tick %d A %d B %d" % (f["tick"], f["alive"][0], f["alive"][1]) in page


def test_a_control_strip_is_not_a_second_layout_row(tmp_path):
    """H-063 "the control strip beside the fight" (not another fight): the control file's id is not listed as its own layout block or INVALID row; the summary table
    keeps one row for the layout."""
    root, out, _ = _stage(tmp_path, control=True)
    page = _page(root, out, control=True)
    assert page.count("<h2>%s</h2>" % LID) == 1
    assert "pair:" not in page and "<b>%s</b>" % LID not in page, "the control fight is listed as a stage 1 fight row"
    assert "INVALID" not in page
