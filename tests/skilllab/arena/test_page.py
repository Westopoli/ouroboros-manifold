# spec: docs/stories/H-040.md (Part 4: stage page); Flag client; Scene res://scenes/proto/fight_replay/fight_replay.tscn (this file's part has no scene)
"""H-040 part 4, the stage page: `python3 -m scripts.skilllab.arena.page --dir <out dir> --out <html>`.

S-H040 part 4 states: "`scripts/skilllab/arena/page.py`, CLI `python3 -m scripts.skilllab.arena.page --dir <out dir> --out <html>`:
one static page in the shape of `scripts/skilllab/catalogue/review.py build` (same CSS, no new framework). One row per `*.fight.json`:
id, pair, predict and predict_why (from the layout), winner, survivors, ticks, agree in green or red, then the frame strip (every
`frame-<i>.png` in order, 240 px high, captions `tick <t> A <a> B <b>`), then the fall map (the last frame larger). Reads `fight.json`
and the layout; imports `snapshot.read` and `tomllib` only. The page's words are Westley's verdict cell per fight as in `review.py`
(`verdicts.md` shape, one row per fight id)." and "with two example fights and stub PNGs the page lists both ids, every PNG once in
order, the agree cell carries the right class; a `fight.json` that fails `validate` is listed as `INVALID <id>` and the page still
builds (positive control)."

CLI premises this file assumes (the story leaves them open; each is a gap for the Architect, see the commit body):
  P1 layout lookup: `layout_path` in the fight file is repository-relative; the page resolves it against the current directory (the
     repository root when run as the story's run line does). The tests run the CLI with cwd = a tmp "repo root" holding the layouts.
  P2 PNG location: `OM_SHOT_OUT=${F%.fight.json}` in the story's run line puts the PNGs of `<stem>.fight.json` in the directory
     `<dir>/<stem>/frame-<i>.png`; the page's img src ends `<stem>/frame-<i>.png`.
  P3 agree cell: the cell carries the class token `agree` (agree true) or `disagree` (agree false), and the page's style defines both.
  P4 id of an INVALID file is its name up to `.fight.json`; the test accepts the bare layout id or the whole stem after `INVALID `.
  P5 the last frame is shown twice (strip, then the fall map "the last frame larger"); every earlier frame once.
  P6 the verdict cell is a cell whose text begins `verdict`, one per valid fight, as in review.py's `verdict: -` cell.

The page module is run as a subprocess, never imported, so while it is missing every page test fails for the missing-module reason
and the controls (test_control_*) still run green."""
import ast
import importlib
import re
import struct
import subprocess
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.arena import snapshot  # noqa: E402

PAGE_PY = ROOT / "scripts" / "skilllab" / "arena" / "page.py"

LAYOUT_TOML = """id = "{lid}"
situation = "open_field"
landscape = "small_flat"
seed = 1
predict = "{predict}"
predict_why = "{why}"
verdict = ""
feedback = ""

[side_a]
headcount = {n}

[side_b]
headcount = {n}
"""

# (layout id, units per side, frames, predict, why): the first predicted right, the second predicted wrong.
FIGHTS = [
    ("L-0101", 2, 11, "A", "WHYONE side A holds the better ground."),
    ("L-0102", 3, 3, "B", "WHYTWO side B has the numbers."),
]


def _png(path: Path) -> None:
    """A 1x1 valid PNG from the standard library."""
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    raw = b"\x00\xff\x00\x00"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _fight_doc(lid, n, frames, predict):
    doc = snapshot.example(frames=frames, units_per_side=n)
    doc["layout_id"] = lid
    doc["layout_path"] = f"layouts/{lid}.toml"
    doc["result"]["predict"] = predict
    doc["result"]["agree"] = doc["result"]["winner"] == predict
    return doc


@pytest.fixture
def stage(tmp_path):
    """A tmp repo root with two layouts, two example fights written through snapshot.write, and stub PNGs in <out>/<stem>/."""
    root = tmp_path / "repo"
    out = root / "out"
    (root / "layouts").mkdir(parents=True)
    out.mkdir()
    docs = {}
    for lid, n, frames, predict, why in FIGHTS:
        (root / "layouts" / f"{lid}.toml").write_text(LAYOUT_TOML.format(lid=lid, predict=predict, why=why, n=n))
        doc = _fight_doc(lid, n, frames, predict)
        stem = f"{lid}-s1"
        snapshot.write(doc, out / f"{stem}.fight.json")
        (out / stem).mkdir()
        for i in range(frames):
            _png(out / stem / f"frame-{i}.png")
        docs[lid] = doc
    return root, out, docs


def _run_page(root, out, html):
    env = {"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin"}
    return subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.page", "--dir", str(out), "--out", str(html)],
                          cwd=root, env=env, capture_output=True, text=True, timeout=60)


def _build(stage):
    root, out, docs = stage
    html = root / "index.html"
    done = _run_page(root, out, html)
    assert done.returncode == 0, f"page CLI failed (rc {done.returncode}): {done.stderr.strip()[-300:]}"
    assert html.exists(), "page CLI wrote no html"
    return html.read_text(), docs


class _Cells(HTMLParser):
    """Collects the class tokens of every element and the text of every td."""
    def __init__(self):
        super().__init__()
        self.classes, self.cells, self._open = [], [], None

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "class" and v:
                self.classes.append((tag, v.split()))
        if tag == "td":
            self._open = []

    def handle_data(self, data):
        if self._open is not None:
            self._open.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self._open is not None:
            self.cells.append("".join(self._open).strip())
            self._open = None


# ---- controls: green today -------------------------------------------------------------------------------------------------

def test_control_fixtures_validate_through_snapshot_read(stage):
    """H-040 part 4 (harness control): the two example fights written by the fixture read back through snapshot.read clean,
    so a red page test means the page is missing, not that the fixtures are broken."""
    root, out, docs = stage
    for lid, doc in docs.items():
        assert snapshot.read(out / f"{lid}-s1.fight.json") == doc
        assert snapshot.validate(doc) == []
    assert docs["L-0101"]["result"]["agree"] is True and docs["L-0102"]["result"]["agree"] is False


def test_control_review_build_exists_as_the_shape_to_copy():
    """H-040 part 4 (harness control): 'in the shape of `scripts/skilllab/catalogue/review.py build`' - the function exists and its
    output has the verdicts.md instruction line and a `verdict:` cell the page copies."""
    review = importlib.import_module("scripts.skilllab.catalogue.review")
    assert callable(review.build)
    src = Path(review.__file__).read_text()
    assert "Answer in verdicts.md" in src and "verdict: %(verdict)s" in src


def test_control_stub_pngs_are_valid():
    """H-040 part 4 (harness control): the stub PNG writer makes a file with the PNG signature and an IEND chunk."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.png"
        _png(p)
        data = p.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n" and data.endswith(b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF))


# ---- the page ---------------------------------------------------------------------------------------------------------------

def test_page_lists_both_fight_ids_with_layout_words(stage):
    """H-040 part 4: 'one row per `*.fight.json`: id, pair, predict and predict_why (from the layout), winner, survivors, ticks,
    agree'. Both ids, both pairs and both predict_why words (read from the layout TOML at layout_path) are on the page."""
    page, docs = _build(stage)
    for lid, n, frames, predict, why in FIGHTS:
        assert lid in page, f"{lid} missing from the page"
        assert f"{n}:{n}" in page, f"pair {n}:{n} missing"
        assert why in page, f"predict_why of {lid} missing (layout lookup through layout_path)"
        assert docs[lid]["result"]["ticks"] is not None
    assert "verdicts.md" in page, "the page's words are Westley's verdicts.md, as in review.py"


def test_page_lists_every_png_in_order_and_captions(stage):
    """H-040 part 4: 'the frame strip (every `frame-<i>.png` in order, 240 px high, captions `tick <t> A <a> B <b>`)'. Every earlier
    frame appears once, the last twice (strip, fall map: 'the last frame larger'), in numeric order (frame-10 after frame-9)."""
    page, docs = _build(stage)
    for lid, n, frames, predict, why in FIGHTS:
        stem = f"{lid}-s1"
        first = []
        for i in range(frames):
            src = f"{stem}/frame-{i}.png"
            want = 2 if i == frames - 1 else 1
            assert page.count(src) == want, f"{src} appears {page.count(src)} times, want {want}"
            first.append(page.index(src))
        assert first == sorted(first), f"frames of {lid} not in order"
        pos = -1
        for frame in docs[lid]["frames"]:
            a, b = frame["alive"]
            caption = f"tick {frame['tick']} A {a} B {b}"
            found = page.find(caption, pos + 1)
            assert found > pos, f"caption {caption!r} missing or out of order for {lid}"
            pos = found
    assert re.search(r"height\s*[=:]\s*[\"']?240", page), "frame strip images are not 240 px high"


def test_page_agree_cell_class_per_fight(stage):
    """H-040 part 4: 'agree in green or red'. In fight order the agree cells carry class `agree` (L-0101, predicted right) then
    `disagree` (L-0102, predicted wrong), and the style defines both."""
    page, docs = _build(stage)
    cells = _Cells()
    cells.feed(page)
    tokens = [t for tag, toks in cells.classes for t in toks if t in ("agree", "disagree")]
    assert tokens == ["agree", "disagree"], f"agree cell classes in order: {tokens}"
    assert ".agree" in page and ".disagree" in page, "style does not define the green and red classes"


def test_page_has_a_verdict_cell_per_fight(stage):
    """H-040 part 4: 'Westley's verdict cell per fight as in `review.py` (`verdicts.md` shape, one row per fight id)'. One cell whose
    text begins `verdict` per fight."""
    page, _ = _build(stage)
    cells = _Cells()
    cells.feed(page)
    assert sum(1 for c in cells.cells if c.lower().startswith("verdict")) == len(FIGHTS), cells.cells


def test_page_marks_an_invalid_fight_and_still_builds(stage):
    """H-040 part 4 (positive control, detector): 'a `fight.json` that fails `validate` is listed as `INVALID <id>` and the page
    still builds'. A third file with one unit's hp removed is listed INVALID, the two valid fights are still listed, none of them
    is marked INVALID, and the exit code is 0."""
    root, out, docs = stage
    bad = _fight_doc("L-0103", 2, 3, "A")
    del bad["frames"][1]["units"][0]["hp"]
    assert snapshot.validate(bad) != [], "control: the planted document must fail validate"
    import json
    (out / "L-0103-s1.fight.json").write_text(json.dumps(bad, sort_keys=True, indent=2) + "\n")
    page, _ = _build(stage)
    assert "INVALID L-0103" in page
    for lid, *_ in FIGHTS:
        assert lid in page and f"INVALID {lid}" not in page


# ---- imports ----------------------------------------------------------------------------------------------------------------

def test_page_module_imports_snapshot_read_and_tomllib_only():
    """H-040 part 4: 'imports `snapshot.read` and `tomllib` only'. By ast: from the lab it imports only `read` from
    `scripts.skilllab.arena.snapshot`; it imports `tomllib`; everything else is the standard library."""
    assert PAGE_PY.exists(), "scripts/skilllab/arena/page.py does not exist"
    tree = ast.parse(PAGE_PY.read_text())
    mods, names = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            mods.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
    assert "tomllib" in mods, "page.py does not import tomllib"
    assert "scripts.skilllab.arena.snapshot.read" in names, "page.py does not import snapshot.read"
    lab = {m for m in mods if m.split(".")[0] == "scripts"}
    assert lab == {"scripts.skilllab.arena.snapshot"}, f"lab imports beyond snapshot: {sorted(lab)}"
    assert {n for n in names if n.startswith("scripts.")} == {"scripts.skilllab.arena.snapshot.read"}
    other = {m.split(".")[0] for m in mods} - {"scripts"} - set(sys.stdlib_module_names)
    assert not other, f"non-standard-library imports: {sorted(other)}"
