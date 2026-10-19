# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-19
"""Leaf-06: report(batch, out_dir) writes one self-contained HTML page. Asserts on parsed structure.

## Conventions the report tests rely on

The spec (AC 18-19) does not fix these; the tests do, and the leaf-06 brief and spec should state them.

1. Break-even marker: a vertical `<line>` (x1 == x2, y1 != y2) whose x lies strictly between the cx of the dot
   for N and the cx of the dot for N+1, and the `beats N, loses to N+1` `<text>` has an `x` attribute equal to
   that line's x. (A gridline at a dot x, or one with no label, is not a marker.)
2. Every svg `<text>` carries plain numeric `x` and `y` attributes.
3. Firing chart series labels: the `Side 0` and `Side 1` text are placed at the end of their own line: the text's
   `y` is strictly nearer to the last point's y of its own polyline than to the last point's y of the other one.
   (Which polyline is drawn first is not fixed; the label ties a line to its side.)
4. Firing chart gap shading: one `<polygon points>` or `<path d>` using absolute coordinates only (M/L/Z, no
   H/V/relative commands) whose numbers contain every polyline x and every polyline y of both lines; it is
   filled (a `fill` that is not none, or a `class` or `style`). See also 12.
5. Firing chart and table share a y scale across both lines: a larger count is a smaller y, equal counts equal y.
6. Firing table: each data row is exactly three cells, tick, Side 0 count, Side 1 count, in that order, one row
   per sample in sample order; a header row (cells not all numeric) is allowed.
7. Scan table: a header row (th) holds a cell `In words`; the column under it reads
   `{size} units beat {enemy_heads}` for a won cell and `{size} units lose to {enemy_heads}` for a lost one; the
   row of a cell is the one row with a cell equal to its enemy headcount.
8. The page contains no `url(...)` pointing outside itself: each `url()` target is a `#fragment`, a `data:` URI,
   or an https host `fonts.googleapis.com`; no other host (no `fonts.gstatic.com`). Every `href`/`src` is a
   `#fragment`, a `data:` URI or a `fonts.googleapis.com` URL (no relative stylesheet or image).
9. Each finding sentence sits inside one `<h2>` element (the combined sentence in a single `<h2>`); the only
   `<h1>` is `Batch.title`. A scan labelled other than `reach`/`identical` gets its own sentence even when the
   combined sentence is shown; a lone `reach` or lone `identical` is treated like any other label.
10. Scan table: a column headed `Mean margin` whose cell is the cell's `mean_margin` formatted with 3 decimals
    (`f"{m:.3f}"`); each dot's `cy` is strictly decreasing in mean margin (larger margin, smaller cy; equal
    margins, equal cy).
11. Scan dots are `<circle>` elements whose class list holds `cell` (colour by won/lost is a further class, fill,
    style or enclosing `<g>`). A scan chart draws no `<polyline>`. A firing chart draws exactly two `<polyline>`
    and no `class="cell"` circle; no other `<svg>` or `<table>` is in the page; the labels `Side 0` and `Side 1`
    each appear once per firing chart.
12. Gap shading (refines 4): the polygon or path is absolute M/L/Z only, and its vertices trace the region between
    the two lines, so its absolute shoelace area equals the area between the two series (checked on a fixture
    where one side is never below the other).
"""
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.contract import Batch, CellResult, FightResult, ScanResult  # noqa: E402
from scripts.skilllab.report import report  # noqa: E402

FONT_HOSTS = {"fonts.googleapis.com"}
FIRING = [(0, 0, 0), (5, 2, 1), (10, 3, 1), (15, 3, 2), (20, 1, 1), (25, 1, 1)]   # 6 samples: no scan has 6 cells
# The lines cross and the last tick has side 1 above side 0: ties each polyline to its label.
FIRING_SKEW = [(0, 0, 0), (5, 1, 3), (10, 2, 4), (15, 4, 3), (20, 3, 5), (25, 3, 5)]   # 6 samples


def _fight(firing=None):
    return FightResult(outcome="side0", margin=0.4, strength_left=(0.7, 0.3), survivors=(11, 4),
                       heads=(16, 12), ticks=100, first_contact_tick=5,
                       firing=list(firing if firing is not None else FIRING),
                       firing_unit_seconds=(2.0, 1.0))


def _scan(size, first, last, won_up_to):
    """Cells first..last; won (margin +0.5) up to won_up_to, lost (-0.5) above; None breaks even if no change."""
    cells = []
    for n in range(first, last + 1):
        won = n <= won_up_to
        cells.append(CellResult(enemy_heads=n, fights=[_fight()], mean_margin=0.5 if won else -0.5, won=won))
    changed = any(a.won and not b.won for a, b in zip(cells, cells[1:]))
    beats = won_up_to if changed else None
    return ScanResult(size=size, cells=cells, beats=beats, loses_to=None if beats is None else beats + 1)


def _batch(title="Controls"):
    reach = _scan(16, 10, 14, 12)      # 5 cells, beats 12
    ident = _scan(16, 10, 16, 11)      # 7 cells, beats 11
    return Batch(title=title, scans={"reach": reach, "identical": ident},
                 firing_example={"reach": _fight(), "identical": _fight()}, rows=[])


def _flat(first, last, margin):
    cells = [CellResult(n, [_fight()], margin, margin > 0.05) for n in range(first, last + 1)]
    return ScanResult(size=16, cells=cells, beats=None, loses_to=None)


class Page(HTMLParser):
    """Collects the structure the assertions need; no knowledge of how the report builds it."""

    def __init__(self):
        super().__init__()
        self.blocks = []          # ("svg"|"table", index) in document order
        self.svgs = []
        self.tables = []
        self.tags = []            # every start tag name
        self.urls = []
        self.order = 0
        self.headings = []        # (order, text)
        self.h1s = []
        self.h2s = []             # text of every <h2>
        self.first_svg_order = None
        self._chars = []
        self._svg = None
        self._table = None
        self._row = None
        self._cell = None
        self._text = None
        self._text_a = None
        self._heading = None
        self._skip = 0
        self._g = []              # attrs of enclosing <g> elements inside an svg

    @staticmethod
    def sig(attrs, g):
        keys = ("fill", "class", "style", "stroke")
        return tuple([tuple(attrs.get(k) for k in keys)] + [tuple(a.get(k) for k in keys) for a in g])

    def handle_starttag(self, tag, attrs):
        self._start(tag, dict(attrs), selfclosing=False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, dict(attrs), selfclosing=True)
        self.handle_endtag_inner(tag, selfclosing=True)

    def _start(self, tag, a, selfclosing):
        self.order += 1
        self.tags.append(tag)
        for k in ("href", "src", "xlink:href"):
            if a.get(k):
                self.urls.append(a[k])
        for m in re.finditer(r"url\(\s*['\"]?([^)'\"]+)", a.get("style") or ""):
            self.urls.append(m.group(1))
        if tag in ("style", "script"):
            self._skip += 1
        if tag == "svg":
            self._svg = {"circles": [], "lines": [], "polylines": [], "shapes": [], "texts": [], "text_at": [],
                         "order": self.order}
            self.svgs.append(self._svg)
            self.blocks.append(("svg", len(self.svgs) - 1))
            if self.first_svg_order is None:
                self.first_svg_order = self.order
            self._g = []
        elif self._svg is not None:
            if tag == "g":
                self._g.append(a)
            elif tag == "circle":
                self._svg["circles"].append({"a": a, "sig": self.sig(a, self._g)})
            elif tag == "line":
                self._svg["lines"].append(a)
            elif tag == "polyline":
                self._svg["polylines"].append(a)
            elif tag in ("polygon", "path"):
                self._svg["shapes"].append({"tag": tag, "a": a})
            elif tag == "text" and not selfclosing:
                self._text = []
                self._text_a = a
        if tag == "table":
            self._table = []
            self.tables.append(self._table)
            self.blocks.append(("table", len(self.tables) - 1))
        elif self._table is not None:
            if tag == "tr":
                self._row = []
                self._table.append(self._row)
            elif tag in ("td", "th") and self._row is not None and not selfclosing:
                self._cell = []
        if re.fullmatch(r"h[1-4]", tag) and not selfclosing:
            self._heading = [self.order, [], tag]
        if tag in ("style", "script") and selfclosing:
            self._skip -= 1

    def handle_endtag(self, tag):
        self.handle_endtag_inner(tag, selfclosing=False)

    def handle_endtag_inner(self, tag, selfclosing):
        if tag in ("style", "script") and not selfclosing:
            self._skip -= 1
        if tag == "svg":
            self._svg = None
        elif tag == "g" and self._g:
            self._g.pop()
        elif tag == "text" and self._text is not None and self._svg is not None:
            label = "".join(self._text).strip()
            self._svg["texts"].append(label)
            self._svg["text_at"].append((label, self._text_a))
            self._text = None
        elif tag in ("td", "th") and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr":
            self._row = None
        elif tag == "table":
            self._table = None
        elif re.fullmatch(r"h[1-4]", tag) and self._heading is not None:
            text = " ".join("".join(self._heading[1]).split())
            self.headings.append((self._heading[0], text))
            if self._heading[2] == "h1":
                self.h1s.append(text)
            if self._heading[2] == "h2":
                self.h2s.append(text)
            self._heading = None

    def handle_data(self, data):
        if self._skip:
            return
        self._chars.append(data)
        for sink in (self._text, self._cell, self._heading and self._heading[1]):
            if sink is not None:
                sink.append(data)

    @property
    def text(self):
        return " ".join("".join(self._chars).split())


def _render(batch, tmp_path):
    path = report(batch, tmp_path)
    html = Path(path).read_text(encoding="utf-8")
    page = Page()
    page.feed(html)
    page.close()
    return path, html, page


def _cell_dots(svg):
    return [c for c in svg["circles"] if "cell" in (c["a"].get("class") or "").split()]


def _scan_svg(page, ncells):
    """The scan chart svg: the one drawing ncells class="cell" circles, none a firing chart (convention 11)."""
    found = [s for s in page.svgs if len(_cell_dots(s)) == ncells and len(s["polylines"]) != 2]
    assert len(found) == 1
    assert found[0]["polylines"] == []
    return found[0]


def _firing_svgs(page):
    return [s for s in page.svgs if len(s["polylines"]) == 2]


def _xs_ys(polyline):
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?", polyline["points"])]
    return nums[0::2], nums[1::2]


def _table_after(page, svg):
    """The first table that follows the given svg in document order."""
    seen = False
    for kind, idx in page.blocks:
        if kind == "svg" and page.svgs[idx] is svg:
            seen = True
        elif kind == "table" and seen:
            return page.tables[idx]
    raise AssertionError("no table after the chart")


def _floats(text):
    return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:[eE]-?\d+)?", text)]


def _side_lines(svg):
    """(y list of side 0, y list of side 1): each polyline is tied to its side by the label placed at its end."""
    labels = {t: a for t, a in svg["text_at"] if t in ("Side 0", "Side 1")}
    assert set(labels) == {"Side 0", "Side 1"}
    lines = [_xs_ys(p)[1] for p in svg["polylines"]]
    assert len(lines) == 2
    out = {}
    for name, a in labels.items():
        dist = [abs(float(a["y"]) - ys[-1]) for ys in lines]
        assert dist[0] != dist[1]
        out[name] = lines[dist.index(min(dist))]
    assert out["Side 0"] is not out["Side 1"]
    return out["Side 0"], out["Side 1"]


def _follow_counts(counts0, counts1, y0, y1):
    """Larger count plots at a smaller y, equal counts at equal y, across both lines."""
    pts = list(zip(counts0, y0)) + list(zip(counts1, y1))
    for c1, v1 in pts:
        for c2, v2 in pts:
            assert (c1 > c2) == (v1 < v2) and (c1 == c2) == (v1 == v2)


def _gap_shape(svg, xs, ys):
    """The shaded gap: a filled polygon/path whose numbers hold every polyline x and every polyline y."""
    for s in svg["shapes"]:
        a = s["a"]
        if a.get("d") is not None and not re.fullmatch(r"[MLZ0-9eE\s,.+-]*", a["d"]):
            continue                                              # convention 4: absolute M/L/Z only
        nums = _floats(a.get("points") or a.get("d") or "")
        filled = a.get("fill") not in (None, "none") or a.get("class") or a.get("style")
        if filled and set(xs) <= set(nums[0::2]) and set(ys) <= set(nums[1::2]):
            return s
    return None


def _shoelace(shape):
    nums = _floats(shape["a"].get("points") or shape["a"].get("d") or "")
    pts = list(zip(nums[0::2], nums[1::2]))
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def _area_between(xs, ya, yb):
    """Trapezoid area between two lines that never cross (one never below the other)."""
    return sum(abs((ya[i] - yb[i]) + (ya[i + 1] - yb[i + 1])) / 2 * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))


def _outside_urls(html):
    """Hosts of external links, and any url() target that is neither #fragment, data: nor a font host."""
    bad = []
    for m in re.finditer(r"url\(\s*['\"]?\s*([^)'\"\s]*)", html):
        t = m.group(1)
        host = urlparse(t if not t.startswith("//") else "https:" + t).hostname
        if not (t.startswith("#") or t.startswith("data:") or host in FONT_HOSTS):
            bad.append(t)
    return bad


def test_report_returns_one_html_file_inside_out_dir(tmp_path):
    """AC-18: returns the path of one .html file written into out_dir, and nothing else is written."""
    path = report(_batch(), tmp_path)
    p = Path(os.fspath(path))
    assert p.is_file() and p.suffix == ".html"
    assert p.resolve().parent == tmp_path.resolve()
    assert [e.name for e in tmp_path.iterdir()] == [p.name]
    assert p.stat().st_size > 0


def test_heading_states_reach_and_identical_in_soldiers(tmp_path):
    """AC-19: exact heading sentence for scans labelled reach and identical, above the first figure."""
    _, _, page = _render(_batch(), tmp_path)
    sentence = "With longer reach, 16 units beat 12. Identical sides beat 11."
    assert len([t for t in page.h2s if sentence in t]) == 1
    hits = [o for o, t in page.headings if sentence in t]
    assert len(hits) == 1
    assert hits[0] < page.first_svg_order


def test_heading_uses_each_scans_own_numbers(tmp_path):
    """AC-19: other sizes and break-evens change the sentence (guards against a hard-coded sentence)."""
    batch = Batch(title="t", scans={"reach": _scan(20, 8, 24, 17), "identical": _scan(20, 8, 24, 15)},
                  firing_example={"reach": _fight(), "identical": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    assert any("With longer reach, 20 units beat 17. Identical sides beat 15." in t for t in page.h2s)


def test_no_break_even_heading_uses_the_scans_own_range(tmp_path):
    """AC-19: a scan with beats None gets 'No break-even found between {A} and {B} enemy units.'"""
    batch = Batch(title="t", scans={"alpha": _flat(8, 24, 0.5), "beta": _flat(5, 9, -0.5)},
                  firing_example={"alpha": _fight(), "beta": _fight()}, rows=[])
    _, html, page = _render(batch, tmp_path)
    texts = list(page.h2s)
    assert any("No break-even found between 8 and 24 enemy units." in t for t in texts)
    assert any("No break-even found between 5 and 9 enemy units." in t for t in texts)
    assert "beats None" not in page.text and "loses to None" not in page.text
    assert not re.search(r"beats \d+, loses to \d+", page.text)


def test_break_even_label_on_each_scan_chart(tmp_path):
    """AC-19: 'beats N, loses to N+1' as a text element on the scan's own chart, N from the scan."""
    _, _, page = _render(_batch(), tmp_path)
    reach_svg = _scan_svg(page, 5)
    ident_svg = _scan_svg(page, 7)
    assert "beats 12, loses to 13" in reach_svg["texts"]
    assert "beats 11, loses to 12" in ident_svg["texts"]
    assert "beats 11, loses to 12" not in reach_svg["texts"]


def test_break_even_is_marked_with_a_vertical_line_between_the_two_cells(tmp_path):
    """AC-19: a vertical line strictly between the dot for N and the dot for N+1, carrying the label (convention 1)."""
    _, _, page = _render(_batch(), tmp_path)
    for ncells, first, beats, label in ((5, 10, 12, "beats 12, loses to 13"), (7, 10, 11, "beats 11, loses to 12")):
        svg = _scan_svg(page, ncells)
        cx = [float(c["a"]["cx"]) for c in _cell_dots(svg)]
        beats_x, loses_x = cx[beats - first], cx[beats - first + 1]
        label_x = [float(a["x"]) for t, a in svg["text_at"] if t == label]
        assert len(label_x) == 1
        markers = [l for l in svg["lines"] if "x1" in l and l.get("x1") == l.get("x2") and l.get("y1") != l.get("y2")
                   and abs(float(l["x1"]) - label_x[0]) < 1e-6]
        assert markers
        assert beats_x < label_x[0] < loses_x


def test_one_dot_per_cell_in_enemy_order_coloured_by_won_or_lost(tmp_path):
    """AC-19: one circle per cell, x increasing with enemy headcount, won and lost in two distinct colours."""
    _, _, page = _render(_batch(), tmp_path)
    svg = _scan_svg(page, 5)                                 # cells 10..14: won, won, won, lost, lost
    cx = [float(c["a"]["cx"]) for c in _cell_dots(svg)]
    assert cx == sorted(cx) and len(set(cx)) == 5
    sigs = [c["sig"] for c in _cell_dots(svg)]
    assert sigs[0] == sigs[1] == sigs[2]
    assert sigs[3] == sigs[4]
    assert sigs[0] != sigs[3]


GRADED = [0.9126, 0.3, -0.1234, -0.7]


def _graded_batch():
    cells = [CellResult(20 + i, [_fight()], m, m > 0.05) for i, m in enumerate(GRADED)]
    sc = ScanResult(size=17, cells=cells, beats=21, loses_to=22)
    return Batch(title="t", scans={"graded": sc}, firing_example={"graded": _fight()}, rows=[])


def test_dot_height_is_strictly_decreasing_in_mean_margin(tmp_path):
    """AC-19 / brief 'y = mean margin': larger mean margin plots at smaller cy; equal margins at equal cy (conv. 10)."""
    for batch, ncells, margins in ((_graded_batch(), 4, GRADED),
                                   (_batch(), 5, [0.5, 0.5, 0.5, -0.5, -0.5])):
        _, _, page = _render(batch, tmp_path)
        cy = [float(c["a"]["cy"]) for c in _cell_dots(_scan_svg(page, ncells))]
        assert len(cy) == len(margins)
        for i in range(len(cy)):
            for j in range(len(cy)):
                assert (margins[i] > margins[j]) == (cy[i] < cy[j])
                assert (margins[i] == margins[j]) == (cy[i] == cy[j])


def test_scan_table_shows_mean_margin_with_three_decimals(tmp_path):
    """AC-19: the table repeats the dots' numbers: a `Mean margin` column, mean_margin as f'{m:.3f}' (conv. 10)."""
    _, _, page = _render(_graded_batch(), tmp_path)
    table = _table_after(page, _scan_svg(page, 4))
    header = [c.strip() for c in table[0]]
    assert header.count("Mean margin") == 1
    col = header.index("Mean margin")
    for i, m in enumerate(GRADED):
        rows = [r for r in table[1:] if str(20 + i) in [c.strip() for c in r]]
        assert len(rows) == 1
        assert rows[0][col].strip() == f"{m:.3f}"


def test_scan_chart_draws_no_polyline_and_firing_chart_no_cell_dot(tmp_path):
    """AC-19: the two chart kinds cannot be confused: dots only in scan charts, lines only in firing charts (conv. 11)."""
    _, _, page = _render(_batch(), tmp_path)
    assert len(page.svgs) == 4
    firing = _firing_svgs(page)
    assert len(firing) == 2
    for svg in firing:
        assert _cell_dots(svg) == []
    for svg in page.svgs:
        if svg not in firing:
            assert svg["polylines"] == [] and len(_cell_dots(svg)) > 0


def test_no_break_even_scan_draws_no_break_even_label(tmp_path):
    """AC-19: a scan with beats None draws its dots but no 'beats' label."""
    batch = Batch(title="t", scans={"alpha": _flat(8, 12, 0.5)}, firing_example={"alpha": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    svg = _scan_svg(page, 5)
    assert not any("beats" in t for t in svg["texts"])


def _skew_batch():
    return Batch(title="t", scans={"reach": _scan(16, 10, 14, 12), "identical": _scan(16, 10, 16, 11)},
                 firing_example={"reach": _fight(FIRING_SKEW), "identical": _fight(FIRING_SKEW)}, rows=[])


def test_firing_chart_has_two_side_lines_with_labels_and_a_shaded_gap(tmp_path):
    """AC-19: units-able-to-fire chart: two polylines (one per side), series labels as text, gap shaded."""
    _, _, page = _render(_batch(), tmp_path)
    charts = _firing_svgs(page)
    assert len(charts) == 2
    svg = charts[0]
    (xa, ya), (xb, yb) = (_xs_ys(p) for p in svg["polylines"])
    assert len(xa) == len(xb) == len(FIRING)
    assert xa == xb and xa == sorted(xa) and len(set(xa)) == len(FIRING)
    upper, lower = (ya, yb) if sum(ya) < sum(yb) else (yb, ya)
    assert all(u <= l for u, l in zip(upper, lower)) and any(u < l for u, l in zip(upper, lower))
    stroke = [(p.get("stroke"), p.get("class"), p.get("style")) for p in svg["polylines"]]
    assert stroke[0] != stroke[1]
    assert "Side 0" in svg["texts"] and "Side 1" in svg["texts"]
    assert _gap_shape(svg, xa, ya + yb) is not None          # convention 4: shape spans both lines


def test_gap_shape_is_the_one_between_the_lines_not_an_axis(tmp_path):
    """AC-19: the shaded gap holds the points of both lines; a classed axis path does not count (convention 4)."""
    _, _, page = _render(_skew_batch(), tmp_path)
    assert len(_firing_svgs(page)) == 2
    for svg in _firing_svgs(page):
        (xa, ya), (xb, yb) = (_xs_ys(p) for p in svg["polylines"])
        shape = _gap_shape(svg, xa, ya + yb)
        assert shape is not None
        assert _gap_shape({"shapes": [{"tag": "path", "a": {"class": "axis", "d": "M0 0 L0 100 L400 100"}}]},
                          xa, ya + yb) is None                # positive control: an axis is not the gap


def test_gap_polygon_area_is_the_area_between_the_two_series(tmp_path):
    """AC-19: the shaded gap traces the region between the lines: shoelace area equals the area between (conv. 12)."""
    _, _, page = _render(_batch(), tmp_path)
    assert len(_firing_svgs(page)) == 2
    for svg in _firing_svgs(page):
        (xa, ya), (xb, yb) = (_xs_ys(p) for p in svg["polylines"])
        want = _area_between(xa, ya, yb)
        assert want > 0
        shape = _gap_shape(svg, xa, ya + yb)
        assert shape is not None
        assert abs(_shoelace(shape) - want) <= 1e-3 * want
    # positive control: a zigzag (a then b, b not reversed) has another area
    zig = {"a": {"fill": "gray", "points": " ".join(f"{x},{y}" for x, y in zip(xa + xb, ya + yb))}}
    assert abs(_shoelace(zig) - want) > 1e-3 * want


def test_firing_labels_tie_each_polyline_to_its_side(tmp_path):
    """AC-19: 'one line per side, labelled on the chart': heights follow Side 0 / Side 1 counts per label (conv. 3, 5)."""
    _, _, page = _render(_skew_batch(), tmp_path)
    assert len(_firing_svgs(page)) == 2
    for svg in _firing_svgs(page):
        y0, y1 = _side_lines(svg)
        assert len(y0) == len(y1) == len(FIRING_SKEW)
        _follow_counts([f[1] for f in FIRING_SKEW], [f[2] for f in FIRING_SKEW], y0, y1)
        assert y0[-1] > y1[-1] and y0[2] > y1[2] and y0[3] < y1[3]     # side 1 ends higher, side 0 higher at tick 15


def test_firing_line_heights_follow_the_numbers(tmp_path):
    """AC-19: equal counts plot at equal height; a larger count plots higher (smaller y) than a smaller one."""
    _, _, page = _render(_batch(), tmp_path)
    svg = _firing_svgs(page)[0]
    (_, ya), (_, yb) = (_xs_ys(p) for p in svg["polylines"])
    more, fewer = (ya, yb) if sum(ya) < sum(yb) else (yb, ya)
    assert more[0] == fewer[0] and more[4] == fewer[4]       # ticks 0 and 20: counts equal
    assert all(more[i] < fewer[i] for i in (1, 2, 3))        # ticks 5, 10, 15: side 0 able more


def test_each_chart_is_followed_by_a_table_view(tmp_path):
    """AC-19: one chart per scan and per firing example, each with one table under it before the next chart."""
    _, _, page = _render(_batch(), tmp_path)
    assert len(page.svgs) == 4 and len(page.tables) == 4
    assert [k for k, _ in page.blocks] == ["svg", "table"] * 4


def test_scan_table_lists_every_cell(tmp_path):
    """AC-19: the table under a scan chart has exactly one row per cell carrying its enemy headcount."""
    _, _, page = _render(_batch(), tmp_path)
    table = _table_after(page, _scan_svg(page, 5))
    for n in range(10, 15):
        assert len([r for r in table if str(n) in [c.strip() for c in r]]) == 1
    assert not any(str(n) in [c.strip() for r in table for c in r] for n in (9, 15))


def test_scan_table_has_an_in_words_column_with_the_plain_sentence_per_cell(tmp_path):
    """AC-19 Reading: header `In words`; '{size} units beat {n}' for a won cell, '{size} units lose to {n}' if lost."""
    batch = Batch(title="t", scans={"reach": _scan(16, 10, 14, 12), "identical": _scan(16, 10, 16, 11),
                                    "wide": _scan(20, 8, 11, 9)},
                  firing_example={"reach": _fight(), "identical": _fight(), "wide": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    for ncells, size, first, last, won_up_to in ((5, 16, 10, 14, 12), (7, 16, 10, 16, 11), (4, 20, 8, 11, 9)):
        table = _table_after(page, _scan_svg(page, ncells))
        header = [c.strip() for c in table[0]]
        assert header.count("In words") == 1
        col = header.index("In words")
        for n in range(first, last + 1):
            rows = [r for r in table[1:] if str(n) in [c.strip() for c in r]]
            assert len(rows) == 1
            want = f"{size} units beat {n}" if n <= won_up_to else f"{size} units lose to {n}"
            assert rows[0][col].strip() == want


def test_firing_table_repeats_the_sampled_numbers(tmp_path):
    """AC-19: the table under the firing chart carries every sample as tick, Side 0, Side 1 in order (conv. 6)."""
    _, _, page = _render(_skew_batch(), tmp_path)
    assert len(_firing_svgs(page)) == 2
    for svg in _firing_svgs(page):
        table = _table_after(page, svg)
        data = [[c.strip() for c in row] for row in table if row and all(c.strip().isdigit() for c in row)]
        assert data == [[str(tick), str(a0), str(a1)] for tick, a0, a1 in FIRING_SKEW]


def test_page_is_self_contained(tmp_path):
    """AC-18: no external script; the only external host is fonts.googleapis.com, in links and in url() (conv. 8)."""
    evil = '<style>body{background:url(https://evil.example.com/x.png)}</style>'
    assert _outside_urls(evil) == ["https://evil.example.com/x.png"]                   # positive controls
    assert _outside_urls('<style>@font-face{src:url(https://fonts.gstatic.com/a.woff2)}</style>')
    assert _outside_urls('<style>a{b:url(x.png)}</style>') == ["x.png"]
    assert _outside_urls("<style>a{b:url(https://fonts.googleapis.com/css2)} c{d:url(#g)}</style>") == []
    _, html, page = _render(_batch(), tmp_path)
    assert not re.search(r"<script[^>]*\bsrc\s*=", html, re.I)
    assert not re.search(r"@import", html)
    remote = [u for u in page.urls if re.match(r"(https?:)?//", u.strip())]
    assert {urlparse(u if not u.startswith("//") else "https:" + u).hostname for u in remote} <= FONT_HOSTS
    assert "gstatic" not in html
    assert all(u.strip().startswith(("#", "data:")) or urlparse(u.strip()).hostname in FONT_HOSTS for u in page.urls)
    assert _outside_urls(html) == []


def test_page_has_a_dark_mode(tmp_path):
    """AC-18: light and dark through prefers-color-scheme."""
    _, html, _ = _render(_batch(), tmp_path)
    assert "prefers-color-scheme: dark" in html


def test_labels_and_title_are_html_escaped(tmp_path):
    """AC-18/19: a label like '<b>&' never reaches the page as markup, in its own sentence or anywhere (conv. 9)."""
    evil = "<b>&"
    batch = Batch(title=evil, scans={"reach": _scan(16, 10, 14, 12), "identical": _scan(16, 10, 16, 11),
                                     evil: _scan(16, 10, 14, 12)},
                  firing_example={evil: _fight(), "reach": _fight(), "identical": _fight()}, rows=[])
    _, html, page = _render(batch, tmp_path)
    assert "<b>&" not in html
    assert "b" not in page.tags
    assert "&lt;b&gt;&amp;" in html
    assert "<b>&" in page.text
    assert evil in page.h1s
    assert html.lower().count("<html") == 1
    assert any("<b>&: 16 units beat 12." in t for t in page.h2s)
    assert any("With longer reach, 16 units beat 12. Identical sides beat 11." in t for t in page.h2s)


def test_other_label_beside_reach_and_identical_gets_its_own_sentence(tmp_path):
    """AC-19 Reading: the combined sentence does not replace the plain sentence of a third scan (conv. 9)."""
    batch = Batch(title="t", scans={"reach": _scan(16, 10, 14, 12), "identical": _scan(16, 10, 16, 11),
                                    "mirror": _scan(18, 10, 20, 14), "numbers": _flat(3, 6, 0.5)},
                  firing_example={k: _fight() for k in ("reach", "identical", "mirror", "numbers")}, rows=[])
    _, _, page = _render(batch, tmp_path)
    assert any("With longer reach, 16 units beat 12. Identical sides beat 11." in t for t in page.h2s)
    assert any("mirror: 18 units beat 14." in t for t in page.h2s)
    assert any("No break-even found between 3 and 6 enemy units." in t for t in page.h2s)


def test_lone_reach_is_treated_like_any_other_label(tmp_path):
    """AC-19 Reading: with only `reach` present it gets the plain sentence, no combined sentence."""
    batch = Batch(title="t", scans={"reach": _scan(16, 10, 14, 12)}, firing_example={"reach": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    assert any("reach: 16 units beat 12." in t for t in page.h2s)
    assert not any("With longer reach" in t or "Identical sides" in t for t in page.h2s)


def test_lone_identical_is_treated_like_any_other_label(tmp_path):
    """AC-19 Reading: with only `identical` present it gets the plain sentence, no combined sentence."""
    batch = Batch(title="t", scans={"identical": _scan(16, 10, 16, 11)}, firing_example={"identical": _fight()},
                  rows=[])
    _, _, page = _render(batch, tmp_path)
    assert any("identical: 16 units beat 11." in t for t in page.h2s)
    assert not any("With longer reach" in t or "Identical sides" in t for t in page.h2s)


def test_firing_series_are_named_side_0_and_side_1_on_every_firing_chart(tmp_path):
    """AC-19 Reading: each firing chart carries the text labels 'Side 0' and 'Side 1'."""
    _, _, page = _render(_batch(), tmp_path)
    charts = _firing_svgs(page)
    assert len(charts) == 2
    for svg in charts:
        assert svg["texts"].count("Side 0") == 1 and svg["texts"].count("Side 1") == 1


def test_report_creates_a_missing_out_dir_with_parents(tmp_path):
    """AC-18 Reading: a missing out_dir (nested) is created and holds the one html file."""
    out = tmp_path / "x" / "y"
    path = report(_batch(), out)
    assert out.is_dir()
    assert Path(os.fspath(path)).resolve().parent == out.resolve()
    assert [e.suffix for e in out.iterdir()] == [".html"]


def test_empty_batch_gives_a_valid_page_with_no_figures(tmp_path):
    """AC-18 Reading: an empty batch gives a valid page: html, title h1, no chart, no table."""
    batch = Batch(title="Nothing yet", scans={}, firing_example={}, rows=[])
    path, html, page = _render(batch, tmp_path)
    assert Path(os.fspath(path)).is_file()
    assert html.lower().count("<html") == 1 and "</html>" in html.lower()
    assert page.h1s == ["Nothing yet"]
    assert page.svgs == [] and page.tables == []
    assert "prefers-color-scheme: dark" in html


def test_batch_title_is_the_pages_h1(tmp_path):
    """AC-18 Reading: Batch.title is the page's <h1>, the only one, ahead of the first figure."""
    _, _, page = _render(_batch("Controls run 7"), tmp_path)
    assert page.h1s == ["Controls run 7"]
    first_h1 = min(o for o, t in page.headings if t == "Controls run 7")
    assert first_h1 < page.first_svg_order


def test_one_cell_scan_and_one_sample_series_draw_without_raising(tmp_path):
    """AC-18 Reading: a series with one point is drawn (finite coordinates), never raising."""
    one = ScanResult(size=16, cells=[CellResult(12, [_fight()], 0.5, True)], beats=None, loses_to=None)
    batch = Batch(title="t", scans={"solo": one}, firing_example={"solo": _fight([(0, 2, 1)])}, rows=[])
    _, _, page = _render(batch, tmp_path)
    scan_svg = _scan_svg(page, 1)
    c = _cell_dots(scan_svg)[0]["a"]
    assert all(v == v and abs(float(v)) != float("inf") for v in (c["cx"], c["cy"]))
    (xa, ya), (xb, yb) = (_xs_ys(p) for p in _firing_svgs(page)[0]["polylines"])
    assert len(xa) == len(ya) == len(xb) == len(yb) == 1
    assert all(abs(v) < 1e9 for v in xa + ya + xb + yb)
    assert len(page.tables) == 2


def test_all_zero_series_is_drawn_flat_and_finite(tmp_path):
    """AC-18 Reading: all-zero firing counts and all-zero margins draw flat lines/dots, never raising."""
    zeros = [(t, 0, 0) for t in (0, 5, 10, 15, 20)]
    flat = _flat(10, 13, 0.0)
    batch = Batch(title="t", scans={"flat": flat}, firing_example={"flat": _fight(zeros)}, rows=[])
    _, _, page = _render(batch, tmp_path)
    cy = [float(c["a"]["cy"]) for c in _cell_dots(_scan_svg(page, 4))]
    assert len(set(cy)) == 1 and abs(cy[0]) < 1e9
    (xa, ya), (xb, yb) = (_xs_ys(p) for p in _firing_svgs(page)[0]["polylines"])
    assert len(set(ya)) == 1 and len(set(yb)) == 1
    assert ya == yb
    assert len(ya) == 5 and all(abs(v) < 1e9 for v in ya)


def test_reach_with_no_break_even_gives_one_sentence_per_scan(tmp_path):
    """AC-19 Reading: reach has beats None, identical has a break-even: per-scan sentences, no combined one."""
    batch = Batch(title="t", scans={"reach": _flat(10, 14, 0.5), "identical": _scan(16, 10, 16, 11)},
                  firing_example={"reach": _fight(), "identical": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    texts = list(page.h2s)
    assert any("No break-even found between 10 and 14 enemy units." in t for t in texts)
    assert any("identical: 16 units beat 11." in t for t in texts)
    assert not any("With longer reach" in t for t in texts)


def test_identical_with_no_break_even_gives_one_sentence_per_scan(tmp_path):
    """AC-19 Reading: identical has beats None, reach has a break-even: per-scan sentences, no combined one."""
    batch = Batch(title="t", scans={"reach": _scan(16, 10, 14, 12), "identical": _flat(8, 20, -0.5)},
                  firing_example={"reach": _fight(), "identical": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    texts = list(page.h2s)
    assert any("reach: 16 units beat 12." in t for t in texts)
    assert any("No break-even found between 8 and 20 enemy units." in t for t in texts)
    assert not any("With longer reach" in t for t in texts)


def test_both_without_break_even_give_two_no_break_even_sentences(tmp_path):
    """AC-19 Reading: reach and identical both beats None: each scan's own no-break-even sentence."""
    batch = Batch(title="t", scans={"reach": _flat(10, 14, 0.5), "identical": _flat(8, 20, 0.5)},
                  firing_example={"reach": _fight(), "identical": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    texts = list(page.h2s)
    assert any("No break-even found between 10 and 14 enemy units." in t for t in texts)
    assert any("No break-even found between 8 and 20 enemy units." in t for t in texts)
    assert not any("With longer reach" in t for t in texts)
    assert not any("units beat" in t for t in texts)


def test_other_labels_get_the_plain_units_beat_sentence(tmp_path):
    """AC-19 Reading: a scan labelled other than reach/identical gets '{label}: {size} units beat {N}.'"""
    batch = Batch(title="t", scans={"mirror": _scan(18, 10, 20, 14), "numbers": _flat(3, 6, 0.5)},
                  firing_example={"mirror": _fight(), "numbers": _fight()}, rows=[])
    _, _, page = _render(batch, tmp_path)
    texts = list(page.h2s)
    assert any("mirror: 18 units beat 14." in t for t in texts)
    assert any("No break-even found between 3 and 6 enemy units." in t for t in texts)
    assert not any("With longer reach" in t for t in texts)


# =====================================================================================================================
# LAB-REV2-L5 additions. spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5 (test_report.py; "the artifact template of
# the README section 5 form"; "lists the both_wrong fights as findings, and marks every DRAFT number the data touched"); ruling 4 (ceiling
# hit, never "no gain"); ruling 1 and CellResult.defect; ruling 5; ruling 12 (output rule: diagrams with arrows, a number without its
# diagram is not evidence); decisions 29 and 31 (the audit items). Existing tests above stay: a scan without ceiling_hit and without
# defect reads exactly as before.
#
# INTERFACE FIXED HERE:
#   report.report(batch, out_dir) -> str    (unchanged signature and page) now also reads ScanResult.ceiling_hit and CellResult.defect:
#       - a ceiling-hit scan's finding sentence is one <h2> naming the label, the words "ceiling hit" and the top headcount
#         (scan.beats); the text "No break-even found" never appears for it; its scan chart carries an element with class token
#         "ceiling" and no element with class token "marker"
#       - a defect cell's dot has class tokens "cell defect" (neither won nor lost); its table row has Result "defect" and an
#         In-words cell containing "defect"
#   report.artifact(summary, rows, setup_for, out_dir, title="Skill lab artifact", verdicts=None) -> str
#       summary = the sweep_summary.json dict ({"order": [...], "replicates": n, "families": {family: L4 entry}}); rows = the typed rows
#       of diagram.notables (the family and smoke CSVs read by diagram.read_rows, concatenated); setup_for(notable) -> Setup;
#       verdicts = None, or {"window": [Verdict, ...], "whole": [Verdict, ...]} (conditions.evaluate_bases; the thresholds are Westley's
#       and are not the artifact's business, so the caller computes them).
#       Writes <out_dir>/artifact.html (out_dir created with parents) and <out_dir>/diagrams/<notable.id>.svg (diagram.write_all) and
#       returns the artifact path as str. The page is read as parsed HTML, never as text (quote style, attribute order and whitespace
#       are free). One <h1> = title (escaped: a title with markup characters reads back as that text and adds no element). Then eight
#       <section id=...> elements, SIBLINGS (none inside another, none inside an <h2>), in this order:
#         drafts, findings, baseline-ceiling, agreement, both-wrong, refinement, cone-grid, conditions
#       <section id="drafts"> (the header): one <li data-draft="NAME"> per DRAFT number in force, each name ONCE:
#           DRAFT-opening-window-ticks (text holds contract.OPENING_WINDOW_TICKS) only when rows is not empty;
#           DRAFT-firing-arc-deg when the arc family is in summary["families"] and not skipped; DRAFT-aoe-cone-range, DRAFT-aoe-cone-deg
#           and DRAFT-aoe-cone-share when the cone family is, likewise (a skipped family touched nothing);
#           DRAFT-guard-radius, DRAFT-mixes, DRAFT-reengage-silence-ticks and DRAFT-scale-marks always (names are the test writer's
#           reading of decision 29 item 4; no value is pinned for them). No name containing "slope" (the slope divisor joins only in a
#           batch that runs the ground scene; nothing here says how the artifact would know, so no positive test) and none containing
#           "band" (the 0.25x to 4x band is a ruling, decision 31 F, not a draft number).
#       <section id="findings">: for each notable, in diagram.notables order: one <h2 data-notable="<id>"> holding the sentence, then the
#           exact diagram.render svg text (its root id = the notable id) as the NEXT element sibling of the h2 and a child of the section,
#           then, for a crossing only, a <p class="counts" data-notable="<id>"> (the sentence under the diagram) holding one
#           <span class="count" data-scan data-knob data-beats data-loses-to> per knob value (knob_lo, knob_hi) and per scan (data-scan
#           "play" or the baseline role): data-knob the CSV text of the knob value, data-beats the break-even headcount, data-loses-to the
#           first lost headcount after it ("" when the scan has none); the p's text holds those numbers.
#           crossing:    family, play, layout, role, the CSV text of knob_lo and knob_hi, and the word "crosses"
#           ceiling_hit: play, layout, the CSV text of the knob value and the words "ceiling hit" (never "no gain")
#           both_wrong:  play, layout and the words "both predictions were wrong"; for a control or a baseline row also the role and the kind
#           with no notable at all: the section reads "no crossing", "no ceiling hit" and "no both_wrong fight" and the page holds no <svg>
#       <section id="baseline-ceiling">: one <li data-role data-family data-play data-layout data-point data-knob> per
#           diagram.baseline_ceilings(rows) entry, the text holding "baseline_ceiling" and the role; none: "no baseline_ceiling"
#       <section id="agreement">: charts.agreement_html(groups) where groups maps "<family>/<play>" (first appearance in rows) to the
#           list of that group's row `agreement` words
#       <section id="both-wrong">: one <li data-row="<row index>"> per both_wrong notable (ALL of them), whose text holds the CSV text of
#           that row's outcome, predicted_count, predicted_type, firing_window_0 and firing_window_1 (and the role, and the kind of a
#           control row); with none: "no both_wrong fight", no <li>
#       <section id="refinement">: charts.refinement_html(summary["families"]) verbatim
#       <section id="cone-grid">: charts.cone_grid_html(rows) verbatim; with no cone rows the text "no cone family"
#       <section id="conditions"> (decisions 29 item 2, 31 B, C): with verdicts None the text "no condition verdicts"; else, per basis
#           ("window" then "whole") one <table data-basis> with one <tr data-code data-baseline data-holds> per C1 verdict (the mirror
#           "C1:<skill>" has data-baseline "mirror"; "C1@<role>:<skill>" has the role; data-holds "true", "false" or "none"), the
#           mirror, naive_attacker and naive_defender rows all listed; then <ul class="basis-differences"> with one
#           <li data-code data-window data-whole> per verdict code whose holds differ between the two bases (both bool), or the text
#           "no verdict differs between the bases".
#       Deterministic (same bytes for the same input); self-contained (every url/href/src is a #fragment, a data: URI or a
#       fonts.googleapis.com URL, as test_page_is_self_contained).
#   summary.write (summary.json): per variant scan summary gains "ceiling_hit" (bool) and "multi_flip" (bool); "break_even" reads
#       "ceiling hit: ... up to <top>" for a ceiling-hit scan (today it formats loses_to=None with %d and raises TypeError); every
#       by_enemy_size entry gains "defect" (bool: a draw or a cap sits in the cell)
# =====================================================================================================================
import json  # noqa: E402
import re as _re  # noqa: E402

from scripts.skilllab import charts as _charts, summary as _summary  # noqa: E402


def _td():
    """test_diagram's fixtures; importing it raises until diagram.py exists, so only the L5 tests below are red, never the older ones."""
    import test_diagram
    return test_diagram


def _ceiling_scan_report(top=48):
    cells = [CellResult(n, [_fight()], 0.5, True) for n in (8, 16, 24, 32, 40, top)]
    return ScanResult(size=16, cells=cells, beats=top, loses_to=None, ceiling_hit=True)


def _html(batch, tmp_path):
    return Path(report(batch, tmp_path)).read_text(encoding="utf-8")


def _h2s(html):
    return [" ".join(_re.sub(r"<[^>]+>", "", h).split()) for h in _re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=_re.S)]


def _classes(svg):
    return [set(m.split()) for m in _re.findall(r'class="([^"]*)"', svg)]


def test_l5_report_ceiling_hit_sentence_chart_and_no_no_break_even(tmp_path):
    batch = Batch(title="Ceiling", scans={"s3_layer_above": _ceiling_scan_report()}, firing_example={"s3_layer_above": _fight()}, rows=[])
    html = _html(batch, tmp_path)
    sentences = [h for h in _h2s(html) if "s3_layer_above" in h]
    assert len(sentences) == 1 and "ceiling hit" in sentences[0] and "48" in sentences[0]
    assert "No break-even found" not in html
    chart = _re.findall(r"<svg.*?</svg>", html, flags=_re.S)[0]
    assert any("ceiling" in c for c in _classes(chart)) and not any("marker" in c for c in _classes(chart))


def test_l5_report_a_scan_without_ceiling_hit_keeps_its_break_even_and_marker(tmp_path):
    """Negative control: a crossing scan and a no-break-even scan read as before and carry no ceiling mark."""
    cross = _scan(16, 10, 14, 12)
    nothing = _flat(10, 14, -0.5)
    html = _html(Batch(title="Plain", scans={"cross": cross, "nothing": nothing}, firing_example={}, rows=[]), tmp_path)
    assert "No break-even found" in html and "ceiling hit" not in html
    charts_ = _re.findall(r"<svg.*?</svg>", html, flags=_re.S)
    assert any("marker" in c for c in _classes(charts_[0])) and not any("ceiling" in c for ch in charts_ for c in _classes(ch))


def test_l5_report_defect_cell_is_a_defect_in_chart_and_table(tmp_path):
    sc = _scan(16, 10, 14, 12)
    cells = list(sc.cells)
    cells[2] = CellResult(enemy_heads=12, fights=[_fight()], mean_margin=0.0, won=False, defect=True)
    html = _html(Batch(title="Defect", scans={"d": ScanResult(size=16, cells=cells, beats=None, loses_to=None)}, firing_example={}, rows=[]),
                 tmp_path)
    dots = [c for c in _classes(_re.findall(r"<svg.*?</svg>", html, flags=_re.S)[0]) if "cell" in c]
    assert len(dots) == 5 and sum("defect" in c for c in dots) == 1
    assert all(not ({"won", "lost"} & c) for c in dots if "defect" in c)
    row = [r for r in _re.findall(r"<tr>(.*?)</tr>", html, flags=_re.S) if "<td>12</td>" in r][0]
    cells_text = [_re.sub(r"<[^>]+>", "", c) for c in _re.findall(r"<td>(.*?)</td>", row, flags=_re.S)]
    assert cells_text[2] == "defect" and "defect" in cells_text[3]


# ---------- summary.json ----------

def _summary_defn(names=("cellA",)):
    from types import SimpleNamespace
    cells = [SimpleNamespace(label=n, status="ok", size=16, enemy_from=8, enemy_to=48, build=object(), reference=None, note=None) for n in names]
    return SimpleNamespace(name="formation", cells=cells, variants=[("naive", None)])


def _fr_for_summary(outcome):
    return FightResult(outcome=outcome, margin=0.5 if outcome == "side0" else -0.5, strength_left=(0.5, 0.5), survivors=(4, 0), heads=(16, 16),
                       ticks=100, first_contact_tick=5, firing=[(0, 1, 1)], firing_unit_seconds=(2.0, 1.0))


def test_l5_summary_write_reads_a_ceiling_hit_scan_without_raising(tmp_path):
    """Ruling 4: today `%d units beat %d, lose to %d` meets loses_to=None and raises TypeError."""
    cells = [CellResult(n, [_fr_for_summary("side0")], 0.5, True) for n in (8, 24, 48)]
    sc = ScanResult(size=16, cells=cells, beats=48, loses_to=None, ceiling_hit=True)
    path = tmp_path / "s.json"
    _summary.write(_summary_defn(), {("cellA", "naive"): sc}, path, "elimination only")
    v = json.loads(path.read_text(encoding="utf-8"))["cells"][0]["variants"]["naive"]
    assert v["ceiling_hit"] is True and v["multi_flip"] is False and v["beats"] == 48 and v["loses_to"] is None
    assert "ceiling hit" in v["break_even"] and "48" in v["break_even"] and "no break-even" not in v["break_even"]


def test_l5_summary_write_keeps_the_plain_strings_for_the_other_scans_and_flags_defect_cells(tmp_path):
    """Negative control: a crossing scan reads 'N units beat A, lose to B', a no-crossing one 'no break-even in range'; defect marks the cell."""
    ok = ScanResult(size=16, cells=[CellResult(8, [_fr_for_summary("side0")], 0.5, True), CellResult(24, [_fr_for_summary("side1"), _fr_for_summary("cap")], -0.5, False, defect=True)],
                    beats=8, loses_to=24)
    none = ScanResult(size=16, cells=[CellResult(8, [_fr_for_summary("side1")], -0.5, False)], beats=None, loses_to=None)
    path = tmp_path / "s.json"
    _summary.write(_summary_defn(("a", "b")), {("a", "naive"): ok, ("b", "naive"): none}, path, "r")
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    a, b = cells[0]["variants"]["naive"], cells[1]["variants"]["naive"]
    assert a["break_even"] == "16 units beat 8, lose to 24" and a["ceiling_hit"] is False
    assert b["break_even"] == "no break-even in range" and b["ceiling_hit"] is False
    assert [a["by_enemy_size"]["8"]["defect"], a["by_enemy_size"]["24"]["defect"], b["by_enemy_size"]["8"]["defect"]] == [False, True, False]




def test_l5_summary_write_carries_multi_flip_true_and_false_apart(tmp_path):
    """multi_flip True case (the first tests only pinned False): won, lost, won, lost -> two flips -> True; the plain crossing -> False."""
    flips = ScanResult(size=16, cells=[CellResult(n, [_fr_for_summary("side0" if w else "side1")], 0.0, w) for n, w in
                                       ((8, True), (16, False), (24, True), (32, False))], beats=8, loses_to=16, multi_flip=True)
    plain = ScanResult(size=16, cells=[CellResult(8, [_fr_for_summary("side0")], 0.5, True), CellResult(16, [_fr_for_summary("side1")], -0.5, False)],
                       beats=8, loses_to=16)
    path = tmp_path / "s.json"
    _summary.write(_summary_defn(("flips", "plain")), {("flips", "naive"): flips, ("plain", "naive"): plain}, path, "r")
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    assert cells[0]["variants"]["naive"]["multi_flip"] is True and cells[1]["variants"]["naive"]["multi_flip"] is False


def test_l5_summary_write_flags_a_cell_holding_only_a_draw_as_a_defect(tmp_path):
    """A draw-only cell (no cap): defect True, neither won nor lost counted, the draw counted; a plain lost cell is not a defect."""
    draw = ScanResult(size=16, cells=[CellResult(8, [_fr_for_summary("draw")], 0.0, False, defect=True),
                                      CellResult(16, [_fr_for_summary("side1")], -0.5, False)], beats=None, loses_to=None)
    path = tmp_path / "s.json"
    _summary.write(_summary_defn(), {("cellA", "naive"): draw}, path, "r")
    sizes = json.loads(path.read_text(encoding="utf-8"))["cells"][0]["variants"]["naive"]["by_enemy_size"]
    assert sizes["8"]["defect"] is True and (sizes["8"]["draw"], sizes["8"]["won"], sizes["8"]["lost"], sizes["8"]["cap"]) == (1, 0, 0, 0)
    assert sizes["16"]["defect"] is False and sizes["16"]["lost"] == 1


# ---------- the artifact: read as parsed HTML, never as text ----------

VOID = {"meta", "link", "br", "hr", "img", "input", "col", "base", "area", "wbr"}


class Node:
    def __init__(self, name, attrs, parent):
        self.name, self.attrs, self.parent, self.children = name, dict(attrs), parent, []

    def elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def text(self):
        return " ".join("".join(c if isinstance(c, str) else c.text() for c in self.children).split())

    def find(self, name, **attrs):
        return [n for n in self.iter() if n.name == name and all(n.attrs.get(k.replace("_", "-")) == v for k, v in attrs.items())]


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, [(k, v if v is not None else "") for k, v in attrs], self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, [(k, v if v is not None else "") for k, v in attrs], self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.name != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def _tree(html):
    t = _Tree()
    t.feed(html)
    t.close()
    return t.root


SECTIONS = ["drafts", "findings", "baseline-ceiling", "agreement", "both-wrong", "refinement", "cone-grid", "conditions"]


def _td():
    """test_diagram's fixtures; importing it raises until diagram.py exists, so only the L5 tests below are red, never the older ones."""
    import test_diagram
    return test_diagram


def _artifact_inputs():
    t = _td()
    rows = t.crossing_rows() + t.ceiling_rows(play="s3_types_by_reach") + [t.both_wrong_row()]
    summary = {"order": ["range_up", "vision"], "replicates": 3, "families": {
        "range_up": {"skipped": None, "refined": [0.625], "refined_vs": {"naive_attacker": [0.625]}},
        "vision": {"skipped": None, "refined": [], "refined_vs": {"naive_attacker": []}},
        "arc": {"skipped": "the library has no OM_TP_FIRING_ARC_DEG (LAB-REV2-E0 not built)", "refined": [], "refined_vs": {}}}}
    return t, rows, summary


def _page(tmp_path, rows=None, summary=None, title="Skill lab artifact", verdicts=None):
    from scripts.skilllab import report as report_mod
    t, base_rows, base_summary = _artifact_inputs()
    rows = base_rows if rows is None else rows
    path = report_mod.artifact(base_summary if summary is None else summary, rows, t.setup_for, tmp_path, title=title, verdicts=verdicts)
    return t, rows, Path(path).read_text(encoding="utf-8"), path


def _sec(root, name):
    found = root.find("section", id=name)
    assert len(found) == 1, "section %r: %d found" % (name, len(found))
    return found[0]


def _lis(sec, attr):
    return {li.attrs[attr]: li.text() for li in sec.find("li") if attr in li.attrs}


def test_l5_artifact_writes_the_page_and_one_svg_per_notable(tmp_path):
    from scripts.skilllab import diagram
    t, rows, html, path = _page(tmp_path)
    assert Path(path) == tmp_path / "artifact.html" and isinstance(path, str)
    ids = [n.id for n in diagram.notables(rows)]
    assert len(ids) == 3
    assert sorted(p.name for p in (tmp_path / "diagrams").glob("*.svg")) == sorted(i + ".svg" for i in ids)
    h1 = _tree(html).find("h1")
    assert len(h1) == 1 and h1[0].text() == "Skill lab artifact"


def test_l5_artifact_title_is_escaped_not_markup(tmp_path):
    """The title is text: markup characters read back as themselves and add no element."""
    _, _, html, _ = _page(tmp_path, title="A <b>bold</b> & \"quoted\" title")
    root = _tree(html)
    assert [h.text() for h in root.find("h1")] == ["A <b>bold</b> & \"quoted\" title"]
    assert not [n for n in root.iter() if n.name == "b"]


def test_l5_artifact_sections_are_siblings_in_the_fixed_order(tmp_path):
    """'Sections are siblings': eight sections with one parent, none nested in another, none inside a heading, in the header's order."""
    _, _, html, _ = _page(tmp_path)
    root = _tree(html)
    sections = root.find("section")
    assert [s.attrs["id"] for s in sections] == SECTIONS
    assert len({id(s.parent) for s in sections}) == 1
    for s in sections:
        assert not [n for n in s.iter() if n is not s and n.name == "section"]
        assert not [a for a in [s.parent] if a.name in ("h1", "h2")]
    assert not [n for n in root.find("h2") if n.find("svg") or n.find("section")]


def test_l5_artifact_findings_one_sentence_the_exact_diagram_and_the_counts_per_notable(tmp_path):
    from scripts.skilllab import diagram
    t, rows, html, _ = _page(tmp_path)
    ns = diagram.notables(rows)
    rendered = diagram.render_all(rows, t.setup_for)
    findings = _sec(_tree(html), "findings")
    h2 = findings.find("h2")
    assert [h.attrs["data-notable"] for h in h2] == [n.id for n in ns]
    kids = findings.elements()
    for n, h in zip(ns, h2):
        assert rendered[n.id] in html                                       # the exact diagram.render text
        i = kids.index(h)
        svg = kids[i + 1]                                                   # the svg is the h2's NEXT element sibling, not inside it
        assert svg.name == "svg" and svg.attrs.get("id") == n.id and svg.parent is findings
    cross, ceil, wrong = ns
    words = h2[0].text()
    for w in (cross.family, cross.play, cross.layout, cross.role, repr(cross.knob_lo), repr(cross.knob_hi), "crosses"):
        assert w in words, w
    words = h2[1].text()
    for w in (ceil.play, ceil.layout, repr(ceil.knob_lo), "ceiling hit"):
        assert w in words, w
    assert "no gain" not in words
    assert "both predictions were wrong" in h2[2].text()


def test_l5_artifact_crossing_counts_sit_under_the_diagram_with_the_break_even_of_each_scan(tmp_path):
    """Decision 31 D: the sentence under the diagram gives the counts. PLAY_BE (8 at 0.5, 32 at 0.75) against a flat baseline of 16: each
    scan's break-even and first lost headcount, per knob value."""
    from scripts.skilllab import diagram
    t, rows, html, _ = _page(tmp_path)
    cross = [n for n in diagram.notables(rows) if n.kind == diagram.CROSSING][0]
    findings = _sec(_tree(html), "findings")
    kids = findings.elements()
    svg = [k for k in kids if k.name == "svg" and k.attrs.get("id") == cross.id][0]
    counts = [k for k in kids if k.name == "p" and k.attrs.get("data-notable") == cross.id]
    assert len(counts) == 1 and "counts" in counts[0].attrs.get("class", "").split()
    assert kids.index(counts[0]) > kids.index(svg)
    got = {(sp.attrs["data-scan"], float(sp.attrs["data-knob"])): (sp.attrs["data-beats"], sp.attrs["data-loses-to"]) for sp in counts[0].find("span")
           if "count" in sp.attrs.get("class", "").split()}
    assert got == {("play", 0.5): ("8", "16"), ("naive_attacker", 0.5): ("16", "24"), ("play", 0.75): ("32", "40"), ("naive_attacker", 0.75): ("16", "24")}
    text = counts[0].text()
    for number in ("8", "16", "24", "32", "40"):
        assert re.search(r"(?<![\d.])%s(?![\d.])" % number, text), number


def test_l5_artifact_crossing_counts_of_a_ceiling_scan_have_no_lost_headcount(tmp_path):
    """A scan that won everywhere has beats = the top and data-loses-to empty (negative control of the lost headcount)."""
    t = _td()
    rows = t.sweep_rows({0.5: None, 0.75: 48}, {"naive_attacker": {0.5: 16, 0.75: 16}})
    _, _, html, _ = _page(tmp_path, rows=rows)
    spans = {(sp.attrs["data-scan"], float(sp.attrs["data-knob"])): (sp.attrs["data-beats"], sp.attrs["data-loses-to"])
             for sp in _tree(html).find("span") if "count" in sp.attrs.get("class", "").split()}
    assert spans[("play", 0.75)] == ("48", "") and spans[("play", 0.5)] == ("0", "8")


def test_l5_artifact_agreement_section_is_the_charts_table_over_family_play_groups(tmp_path):
    t, rows, html, _ = _page(tmp_path)
    groups = {}
    for r in rows:
        groups.setdefault("%s/%s" % (r["family"], r["play"]), []).append(r["agreement"])
    assert list(groups) == ["range_up/s3_layer_above", "range_up/s3_types_by_reach", "vision/s3_layer_above"]
    want = _tree(_charts.agreement_html(groups)).find("table")[0]
    got = _sec(_tree(html), "agreement").find("table")
    assert len(got) == 1 and got[0].text() == want.text()
    assert _charts.agreement_html(groups) in html                                # verbatim


def test_l5_artifact_lists_every_both_wrong_fight_with_its_csv_values(tmp_path):
    """Several both_wrong rows (a play row, a baseline row, a control row): the list is not truncated; the role and a control's kind show."""
    t = _td()
    wrong = [t.both_wrong_row(), t.both_wrong_row(baseline="naive_attacker", ticks=301), t.both_wrong_row(kind="control_null", firing_window=(7.0, 9.0))]
    rows = t.crossing_rows() + wrong
    _, _, html, _ = _page(tmp_path, rows=rows)
    items = _lis(_sec(_tree(html), "both-wrong"), "data-row")
    idx = [i for i, r in enumerate(rows) if r["agreement"] == "both_wrong"]
    assert list(items) == [str(i) for i in idx] and len(idx) == 3
    for i in idx:
        r = rows[i]
        text = items[str(i)].split()
        for col in ("outcome", "predicted_count", "predicted_type", "firing_window_0", "firing_window_1"):
            assert str(r[col]) in text, (i, col)
    assert "naive_attacker" in items[str(idx[1])] and "control_null" in items[str(idx[2])]
    assert "naive_attacker" not in items[str(idx[0])] and "control_" not in items[str(idx[0])]


def test_l5_artifact_with_nothing_notable_has_no_diagram_and_says_so(tmp_path):
    """The control of the spec row: a fake with no crossing, no ceiling hit and no both_wrong produces no diagram."""
    t = _td()
    rows = t.sweep_rows({0.25: 32, 0.5: 32, 0.75: 40, 1.0: 40}, {"naive_attacker": t.FLAT16})
    _, _, html, _ = _page(tmp_path, rows=rows)
    root = _tree(html)
    text = _sec(root, "findings").text()
    for w in ("no crossing", "no ceiling hit", "no both_wrong fight"):
        assert w in text, w
    assert not root.find("svg") and not list((tmp_path / "diagrams").glob("*.svg"))
    both = _sec(root, "both-wrong")
    assert not both.find("li") and "no both_wrong fight" in both.text()


def test_l5_artifact_lists_a_baseline_that_also_wins_everywhere_as_baseline_ceiling_not_a_notable(tmp_path):
    """Decision 29 item 3: naive_attacker beats 48 at 0.5; listed with its role, and it makes no finding of its own."""
    from scripts.skilllab import diagram
    t = _td()
    rows = t.sweep_rows({0.5: 24, 1.0: 24}, {"naive_attacker": {0.5: 48, 1.0: 48}})
    assert [n for n in diagram.notables(rows) if n.kind != diagram.CROSSING] == []
    _, _, html, _ = _page(tmp_path, rows=rows)
    root = _tree(html)
    items = _sec(root, "baseline-ceiling").find("li")
    assert [(li.attrs["data-role"], float(li.attrs["data-knob"])) for li in items] == [("naive_attacker", 0.5), ("naive_attacker", 1.0)]
    assert all("baseline_ceiling" in li.text() and "naive_attacker" in li.text() for li in items)
    assert not [h for h in _sec(root, "findings").find("h2") if "ceiling hit" in h.text()]


def test_l5_artifact_baseline_ceiling_section_says_none_when_there_is_none(tmp_path):
    _, _, html, _ = _page(tmp_path)
    sec = _sec(_tree(html), "baseline-ceiling")
    assert not sec.find("li") and "no baseline_ceiling" in sec.text()


def test_l5_artifact_refinement_section_is_the_charts_listing(tmp_path):
    t, rows, html, _ = _page(tmp_path)
    _, _, summary = _artifact_inputs()
    want = _tree(_charts.refinement_html(summary["families"])).find("table")[0]
    got = _sec(_tree(html), "refinement").find("table")
    assert len(got) == 1 and got[0].text() == want.text()


def test_l5_artifact_cone_grid_section_is_the_charts_grid_or_says_there_is_no_cone_family(tmp_path):
    t = _td()
    root = _tree(_page(tmp_path / "none")[2])
    assert "no cone family" in _sec(root, "cone-grid").text() and not _sec(root, "cone-grid").find("table")
    rows = t.cone_series("half=22.5", {150: 8, 300: 32, 600: 40}) + t.cone_series("half=45", {150: 8, 300: 32, 600: 40})
    _, _, html, _ = _page(tmp_path / "cone", rows=rows)
    tables = _sec(_tree(html), "cone-grid").find("table")
    assert len(tables) == 1 and tables[0].text() == _tree(_charts.cone_grid_html(rows)).find("table")[0].text()


def test_l5_artifact_header_lists_every_draft_number_in_force_once(tmp_path):
    """Decision 29 item 4, 31 F. Arc skipped -> no arc; opening window because there are rows; the four always-in-force numbers present;
    each name once; no slope divisor and no band (the 0.25x to 4x band is a ruling, not a draft number)."""
    from scripts.skilllab import contract
    t, rows, summary = _artifact_inputs()
    root = _tree(_page(tmp_path)[2])
    names = [li.attrs["data-draft"] for li in _sec(root, "drafts").find("li") if "data-draft" in li.attrs]
    assert sorted(names) == sorted(["DRAFT-opening-window-ticks", "DRAFT-guard-radius", "DRAFT-mixes", "DRAFT-reengage-silence-ticks",
                                    "DRAFT-scale-marks"])
    assert not [n for n in names if "slope" in n or "band" in n]
    opening = [li for li in _sec(root, "drafts").find("li") if li.attrs.get("data-draft") == "DRAFT-opening-window-ticks"][0]
    assert str(contract.OPENING_WINDOW_TICKS) in opening.text().split()
    live = {**summary, "families": {**summary["families"], "arc": {"skipped": None, "refined": [], "refined_vs": {"naive_attacker": []}},
                                     "cone": {"skipped": None, "refined": [], "refined_vs": {}}}}
    root2 = _tree(_page(tmp_path / "live", summary=live)[2])
    names2 = [li.attrs["data-draft"] for li in _sec(root2, "drafts").find("li") if "data-draft" in li.attrs]
    assert sorted(names2) == sorted(names + ["DRAFT-firing-arc-deg", "DRAFT-aoe-cone-range", "DRAFT-aoe-cone-deg", "DRAFT-aoe-cone-share"])
    assert len(names2) == len(set(names2))


def test_l5_artifact_without_rows_does_not_mark_the_opening_window(tmp_path):
    """Negative control: no row means the opening window touched nothing; the other numbers in force stay listed."""
    root = _tree(_page(tmp_path, rows=[])[2])
    names = {li.attrs["data-draft"] for li in _sec(root, "drafts").find("li") if "data-draft" in li.attrs}
    assert "DRAFT-opening-window-ticks" not in names and {"DRAFT-guard-radius", "DRAFT-mixes", "DRAFT-reengage-silence-ticks", "DRAFT-scale-marks"} <= names
    assert not root.find("svg")


def test_l5_artifact_conditions_say_so_when_no_verdicts_were_given(tmp_path):
    sec = _sec(_tree(_page(tmp_path)[2]), "conditions")
    assert "no condition verdicts" in sec.text() and not sec.find("table")


def _verdicts():
    from scripts.skilllab.evidence import Verdict
    def v(code, holds):
        return Verdict(code, holds, 0.5, 0.5, "unconfirmed definition: test")
    window = [v("C0", True), v("C1:S2", True), v("C1@naive_attacker:S2", True), v("C1@naive_defender:S2", False), v("C2", True), v("C7", None)]
    whole = [v("C0", True), v("C1:S2", False), v("C1@naive_attacker:S2", True), v("C1@naive_defender:S2", False), v("C2", False), v("C7", None)]
    return {"window": window, "whole": whole}


def test_l5_artifact_conditions_list_the_mirror_and_both_baselines_on_both_bases(tmp_path):
    """Decision 31 B and C: the mirror C1, the naive attacker C1 and the naive defender C1 are all listed, for the window and the whole fight."""
    _, _, html, _ = _page(tmp_path, verdicts=_verdicts())
    sec = _sec(_tree(html), "conditions")
    tables = sec.find("table")
    assert [t.attrs["data-basis"] for t in tables] == ["window", "whole"]
    for table in tables:
        rows = {tr.attrs["data-code"]: tr for tr in table.find("tr") if tr.attrs.get("data-code", "").startswith("C1")}
        assert list(rows) == ["C1:S2", "C1@naive_attacker:S2", "C1@naive_defender:S2"]
        assert [tr.attrs["data-baseline"] for tr in rows.values()] == ["mirror", "naive_attacker", "naive_defender"]
    holds = {(t.attrs["data-basis"], tr.attrs["data-code"]): tr.attrs["data-holds"] for t in tables for tr in t.find("tr") if "data-code" in tr.attrs}
    assert holds[("window", "C1:S2")] == "true" and holds[("whole", "C1:S2")] == "false" and holds[("window", "C1@naive_defender:S2")] == "false"


def test_l5_artifact_lists_the_verdicts_that_differ_between_the_bases_and_only_those(tmp_path):
    """Mirror C1 and C2 differ (True/False), the attacker C1 and defender C1 and C0 do not, C7 is None on both: positive and negative controls."""
    _, _, html, _ = _page(tmp_path, verdicts=_verdicts())
    diff = _sec(_tree(html), "conditions").find("ul")
    assert len(diff) == 1 and "basis-differences" in diff[0].attrs.get("class", "").split()
    got = {li.attrs["data-code"]: (li.attrs["data-window"], li.attrs["data-whole"]) for li in diff[0].find("li")}
    assert got == {"C1:S2": ("true", "false"), "C2": ("true", "false")}


def test_l5_artifact_says_no_verdict_differs_when_the_bases_agree(tmp_path):
    same = _verdicts()
    same["whole"] = same["window"]
    sec = _sec(_tree(_page(tmp_path, verdicts=same)[2]), "conditions")
    assert "no verdict differs between the bases" in sec.text() and not sec.find("li")


def test_l5_artifact_is_deterministic_and_self_contained(tmp_path):
    _, _, a, _ = _page(tmp_path / "a", verdicts=_verdicts())
    _, _, b, _ = _page(tmp_path / "b", verdicts=_verdicts())
    assert a == b
    for url in re.findall(r'(?:href|src)=["\']([^"\']+)', a) + re.findall(r"url\(\s*['\"]?([^)'\"]+)", a):
        assert url.startswith(("#", "data:", "https://fonts.googleapis.com")), url


# =====================================================================================================================
# LAB-REV2-L5 fix pass 2 (decision 32 item 3, decision 26): a scan cut by baseline_no_fit is never read as "no crossing exists".
# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 32 items 2 and 3, decision 26; interface of the entry key
# fixed by tests/skilllab/test_sweep_baselines.py on push/labrev2-base-tests (header: "The entry (sweep) ... carry `baseline_no_fit`").
#
# INTERFACE FIXED HERE (additions to report.artifact; nothing earlier changes):
#   summary["families"][family]["baseline_no_fit"] = [ {"family", "play", "layout", "last_headcount"}, ... ]  (sweep's entry key; the key
#       may be missing (an older summary) or empty: nothing was cut). last_headcount K is an int (the last headcount the play was scanned
#       at) or None (the baseline could not be placed even at headcount 8: no scan rows of that play on that layout exist).
#   CUT SCANS ARE READ FROM THE SUMMARY ENTRIES ONLY. Rows of a cut scan carry the label column `baseline_no_fit` = 1 (decision 26) and
#       ceiling_hit 0; the artifact neither needs nor reads that column (the CSV text of it is "1", which diagram.read_rows may or may not
#       type), and a row is never turned into a notable by it.
#   In <section id="findings">, AFTER the last notable block (after every h2/svg/p of the notables), when at least one entry of any family
#       is cut: ONE <ul class="cut-scans"> (class token "cut-scans"), last element child of the section, holding one
#           <li data-cut-scan data-family="<family>" data-play="<play>" data-layout="<layout>" data-last-headcount="<K or empty>">
#       per cut entry, in summary["order"] family order and, inside a family, in the entry's list order (a family in the summary but not
#       in "order" is not read, as everywhere else). The li text holds the family, the play and the layout, and
#           K an int:  the exact sentence  "won through K, scan cut by baseline_no_fit"   (K as an integer: "24", never "24.0")
#           K None:    the layout listed as `baseline_no_fit` and the exact sentence  "no scan: baseline_no_fit at the smallest headcount"
#                      (data-last-headcount is the empty string; the words "won through" do not appear)
#       When nothing is cut there is no <ul class="cut-scans"> and the page holds the text "baseline_no_fit" nowhere.
#   A cut scan is NOT a ceiling hit and not a notable: it adds no h2, no svg, no <p class="counts">, no row to the baseline-ceiling list,
#       and the text of its li holds neither "ceiling hit" nor "no crossing". Notables of other (play, layout) pairs are unchanged.
#   NOT PINNED (QUESTION for the Architect): decision 32 item 3 says the sentence is for a play that WON throughout 8 to K. A cut scan
#       in which the play lost a cell below K has a break-even inside 8..K; whether the artifact then still says "won through K" (false
#       for it) or another sentence is not pinned; the fakes below are always-won.
#   Fakes: rows written with rows.fight_row (the label baseline_no_fit=1 on the cut rows, ceiling_hit 0), one knob value (so no crossing
#   can exist), headcounts 8..K only.
# =====================================================================================================================
from scripts.skilllab import rows as _rows_mod  # noqa: E402

CUT = {"family": "range_up", "play": "s3_layer_above", "layout": "192", "last_headcount": 24}
CUT_SENTENCE = "won through 24, scan cut by baseline_no_fit"
NO_SCAN_SENTENCE = "no scan: baseline_no_fit at the smallest headcount"


def _cut_rows(play="s3_layer_above", layout="192", family="range_up", top=24, baseline_roles=("none", "naive_attacker")):
    """The rows of a cut, always-won scan: headcounts 8..top, the play wins every cell, one knob value, ceiling_hit 0, label baseline_no_fit 1."""
    t = _td()
    out = []
    for role in baseline_roles:
        for h in (8, 16, 24, 32, 40, 48):
            if h > top:
                continue
            won = role == "none"
            row = _rows_mod.fight_row(t.fr("side0" if won else "side1"), knob=t.KNOB[family], knob_value=0.5, baseline=role,
                                               ceiling_hit=0, prefight="ok", family=family, play=play, layout=layout, kind="grid",
                                               enemy_heads=h, baseline_no_fit=1)
            row["point"] = "-"
            out.append(row)
    return out


def _summary_with(*cuts, family="range_up"):
    """The artifact fixture's summary with `cuts` as the baseline_no_fit list of `family`'s entry."""
    _, _, summary = _artifact_inputs()
    summary["families"][family] = dict(summary["families"][family], baseline_no_fit=list(cuts))
    return summary


def _cut_lis(html):
    sec = _sec(_tree(html), "findings")
    uls = [u for u in sec.find("ul") if "cut-scans" in u.attrs.get("class", "").split()]
    return sec, uls, [li for u in uls for li in u.find("li")]


def test_l5_artifact_says_won_through_k_for_a_scan_cut_by_baseline_no_fit(tmp_path):
    """Decision 32 item 3, positive control: the cut (play, layout) reads 'won through 24, scan cut by baseline_no_fit', K an integer."""
    t, base_rows, _ = _artifact_inputs()
    _, _, html, _ = _page(tmp_path, rows=base_rows + _cut_rows(), summary=_summary_with(CUT))
    sec, uls, lis = _cut_lis(html)
    assert len(uls) == 1 and len(lis) == 1
    li = lis[0]
    assert "data-cut-scan" in li.attrs
    assert (li.attrs["data-family"], li.attrs["data-play"], li.attrs["data-layout"], li.attrs["data-last-headcount"]) == ("range_up", "s3_layer_above", "192", "24")
    text = li.text()
    assert CUT_SENTENCE in text and "24.0" not in text
    for w in ("range_up", "s3_layer_above", "192"):
        assert w in text, w
    assert sec.elements()[-1] is uls[0]                                   # after the last notable block


def test_l5_artifact_cut_scan_is_not_a_ceiling_hit_and_not_a_notable(tmp_path):
    """A cut scan the play won throughout adds no notable, no svg, no baseline-ceiling entry; the other notables are unchanged (ceiling hit
    of another play stays a ceiling hit)."""
    from scripts.skilllab import diagram
    t, base_rows, _ = _artifact_inputs()
    rows = base_rows + _cut_rows()
    assert [n.kind for n in diagram.notables(rows)] == [n.kind for n in diagram.notables(base_rows)]          # fixture sanity: rows make no notable
    _, _, html, _ = _page(tmp_path, rows=rows, summary=_summary_with(CUT))
    root = _tree(html)
    findings = _sec(root, "findings")
    assert [h.attrs["data-notable"] for h in findings.find("h2")] == [n.id for n in diagram.notables(base_rows)]
    assert len(findings.find("svg")) == 3 and len(root.find("svg")) == 3
    assert [p.attrs["data-notable"] for p in findings.find("p") if "counts" in p.attrs.get("class", "").split()] == [diagram.notables(base_rows)[0].id]
    assert "ceiling hit" in findings.find("h2")[1].text()                  # the other play's ceiling hit still reads as one
    _, _, lis = _cut_lis(html)
    assert "ceiling hit" not in lis[0].text() and "no crossing" not in lis[0].text()
    assert not _sec(root, "baseline-ceiling").find("li")


def test_l5_artifact_cut_scan_alone_leaves_the_findings_with_no_notable(tmp_path):
    """Only the cut scan's rows: no h2, no svg, the section still says 'no crossing', 'no ceiling hit', 'no both_wrong fight', and lists the cut."""
    from scripts.skilllab import diagram
    rows = _cut_rows()
    assert diagram.notables(rows) == []
    _, _, html, _ = _page(tmp_path, rows=rows, summary=_summary_with(CUT))
    root = _tree(html)
    findings = _sec(root, "findings")
    assert not findings.find("h2") and not root.find("svg")
    ftext = findings.text()
    for w in ("no crossing", "no ceiling hit", "no both_wrong fight"):
        assert w in ftext, w
    assert CUT_SENTENCE in ftext


def test_l5_artifact_without_a_cut_has_no_cut_list_and_no_baseline_no_fit_text(tmp_path):
    """Negative control: an entry with an empty list, an entry without the key (older summary) and no key anywhere read alike."""
    for summary in (_summary_with(), _artifact_inputs()[2]):
        _, _, html, _ = _page(tmp_path / ("s%d" % id(summary)), summary=summary)
        _, uls, lis = _cut_lis(html)
        assert not uls and not lis
        assert "baseline_no_fit" not in html and "scan cut by" not in html


def test_l5_artifact_cut_with_no_scan_at_the_smallest_headcount_says_so(tmp_path):
    """Decision 32 item 2: last_headcount None, no scan rows of that play on that layout: the layout is listed as baseline_no_fit with the
    sentence 'no scan: baseline_no_fit at the smallest headcount' and never 'won through'."""
    t, base_rows, _ = _artifact_inputs()
    none_cut = {"family": "range_up", "play": "s3_layer_above", "layout": "192", "last_headcount": None}
    assert not [r for r in base_rows if (r["play"], r["layout"]) == ("s3_layer_above", "192")]            # no scan rows of the pair
    _, _, html, _ = _page(tmp_path, rows=base_rows, summary=_summary_with(none_cut))
    sec, uls, lis = _cut_lis(html)
    assert len(lis) == 1
    li = lis[0]
    assert li.attrs["data-last-headcount"] == "" and li.attrs["data-layout"] == "192"
    text = li.text()
    assert NO_SCAN_SENTENCE in text and "baseline_no_fit" in text and "192" in text and "s3_layer_above" in text
    assert "won through" not in text and "None" not in text
    assert "won through" not in html


def test_l5_artifact_cut_list_is_in_family_order_then_entry_order_and_each_k_is_its_own(tmp_path):
    """Two families, one with two cuts: summary['order'] family order, then the entry's order; each li carries its own K (and the None
    case beside an int case on the same page)."""
    a = {"family": "range_up", "play": "s3_layer_above", "layout": "192", "last_headcount": 24}
    b = {"family": "range_up", "play": "s3_layer_above", "layout": "78", "last_headcount": None}
    c = {"family": "vision", "play": "s3_types_by_reach", "layout": "81", "last_headcount": 40}
    summary = _summary_with(a, b)
    summary["families"]["vision"] = dict(summary["families"]["vision"], baseline_no_fit=[c])
    _, _, html, _ = _page(tmp_path, rows=_cut_rows(top=24) + _cut_rows(play="s3_types_by_reach", layout="81", family="vision", top=40), summary=summary)
    _, uls, lis = _cut_lis(html)
    assert len(uls) == 1
    assert [(li.attrs["data-family"], li.attrs["data-layout"], li.attrs["data-last-headcount"]) for li in lis] == [
        ("range_up", "192", "24"), ("range_up", "78", ""), ("vision", "81", "40")]
    assert "won through 24, scan cut by baseline_no_fit" in lis[0].text() and NO_SCAN_SENTENCE in lis[1].text()
    assert "won through 40, scan cut by baseline_no_fit" in lis[2].text()
    assert "won through 40" not in lis[0].text() and "won through" not in lis[1].text()


def test_l5_artifact_cut_list_is_deterministic(tmp_path):
    t, base_rows, _ = _artifact_inputs()
    pages = [_page(tmp_path / n, rows=base_rows + _cut_rows(), summary=_summary_with(CUT))[2] for n in ("a", "b")]
    assert pages[0] == pages[1]
