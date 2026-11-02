# spec: docs/stories/H-053.md "Replay readability" item 6; Flag client (no scene in this file)
"""H-053 Replay readability item 6, page.py: one strip per layout, no per-seed strip pages.

Quoted: "6. **No per-seed strip pages.** `page.py` writes one strip per layout and no `strip.html` per seed and no links to them."
Tests line: "`page.py` on a three-seed fixture writes no per-seed strip file."

Isolation: page.py on a hand-built three-seed directory. Integration: the rate file is the real output of `rate.rate()` over the three fights, not a hand-written one.
Positive controls (green today): the three-seed fixture validates and the page builds; the page carries exactly one median-seed strip for the rated layout; the
strip.html detector finds a file in a directory where one is planted.
Red on the built tree: page.py writes `<id>-s<k>/strip.html` for every seed and links to them from the seed numbers.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_page import LAYOUT_TOML, _Cells, _Imgs, _build, _fight_doc, _png  # noqa: E402
from scripts.skilllab.arena import rate as rate_mod, snapshot  # noqa: E402

SEEDS = (1, 2, 3)
FRAMES = 4


@pytest.fixture
def three_seeds(tmp_path):
    """tmp repo root with one layout L-0101 and three seed fights (seeds 1..3, 4 frames, stub PNGs per seed) plus the real rate file from rate.rate()."""
    root = tmp_path / "repo"
    out = root / "out"
    (root / "layouts").mkdir(parents=True)
    out.mkdir()
    (root / "layouts" / "L-0101.toml").write_text(LAYOUT_TOML.format(lid="L-0101", predict="A", why="WHYONE", n=2))
    docs = []
    for s in SEEDS:
        doc = _fight_doc("L-0101", 2, FRAMES, "A")
        doc["seed"] = s
        snapshot.write(doc, out / ("L-0101-s%d.fight.json" % s))
        (out / ("L-0101-s%d" % s)).mkdir()
        for i in range(FRAMES):
            _png(out / ("L-0101-s%d" % s) / ("frame-%d.png" % i))
        docs.append(doc)
    rate = rate_mod.rate(docs, 0.9)
    (out / "L-0101.rate.json").write_text(json.dumps(rate, sort_keys=True) + "\n")
    return root, out, docs, rate


def _strip_pages(root: Path) -> list[Path]:
    return sorted(root.rglob("strip.html"))


def test_control_three_seed_fixture_is_rated_and_builds_one_median_strip(three_seeds):
    """H-053 item 6 control (green today): the fixture has three seed fights and a rate file over seeds [1, 2, 3], the page builds, and the page's stage 2 block holds exactly
    a stage 2 strip (div.strip with images), so a red below is the per-seed pages."""
    root, out, docs, rate = three_seeds
    assert rate["seeds"] == [1, 2, 3] and len(list(out.glob("*.fight.json"))) == 3
    page, _ = _build((root, out, docs))
    imgs = _Imgs()
    imgs.feed(page)
    assert imgs.div_strip, "no stage 2 strip div on the page"


def test_control_strip_page_detector_finds_a_planted_file(three_seeds):
    """Detector control (green today): _strip_pages finds a strip.html planted in a seed directory, so an empty result below means none was written."""
    root, out, _, _ = three_seeds
    (out / "L-0101-s2" / "strip.html").write_text("<html></html>")
    assert _strip_pages(root) == [out / "L-0101-s2" / "strip.html"]


def test_page_writes_no_per_seed_strip_file(three_seeds):
    """Item 6: "no `strip.html` per seed": after page.py on the three-seed fixture there is no strip.html anywhere under the repo root."""
    root, out, docs, _ = three_seeds
    _build((root, out, docs))
    assert _strip_pages(root) == [], "per-seed strip pages written: %s" % [str(p.relative_to(root)) for p in _strip_pages(root)]


def test_page_has_no_links_to_seed_strip_pages_and_still_one_strip_for_the_layout(three_seeds):
    """Item 6: "no links to them": the page text has no `strip.html` and no href into an `-s<k>/` directory; the layout block still has its one strip."""
    root, out, docs, _ = three_seeds
    page, _ = _build((root, out, docs))
    assert "strip.html" not in page
    assert not re.search(r'href="[^"]*-s\d+/', page), "a link into a seed directory remains"
    imgs = _Imgs()
    imgs.feed(page)
    assert imgs.div_strip, "the layout's own strip is gone"
