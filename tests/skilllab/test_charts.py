# spec: docs/northstar/plans/push/ (item 7a), docs/northstar/research/layer_dynamics/README.md section 5
"""Item 7a: chart forms in scripts/skilllab/charts.py: regions, region_map_html, small_multiples_html.

Chart rules proved here: counts not ratios, position on a common scale, no log scales, no dual axes,
small multiples not animation. Unit tests only: hand-made grids and hand-made ScanResults, no engine.
"""
import inspect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import charts  # noqa: E402
from scripts.skilllab.contract import CellResult, ScanResult  # noqa: E402


def grid(rows, xs=None, ys=None):
    """rows: list of strings, top row = highest y index; '#' holds, '.' fails. Returns cells."""
    h = len(rows)
    xs = xs or list(range(len(rows[0])))
    ys = ys or list(range(h))
    return [{"x": xs[i], "y": ys[h - 1 - r], "holds": ch == "#"}
            for r, row in enumerate(rows) for i, ch in enumerate(row)]


def xy(region):
    return [tuple(c) for c in region]


# regions

def test_regions_single_block():
    """A single 2x2 block of holding cells is one region, cells in increasing (x, y) order."""
    out = charts.regions(grid(["...", ".##", ".##"]))
    assert [xy(r) for r in out] == [[(1, 0), (1, 1), (2, 0), (2, 1)]]


def test_regions_two_separate_blocks_ordered_by_first_cell():
    """Two blocks apart are two regions, ordered by their first cell."""
    out = charts.regions(grid(["#..#", "#..#"]))
    assert [xy(r) for r in out] == [[(0, 0), (0, 1)], [(3, 0), (3, 1)]]


def test_regions_diagonal_touch_is_not_connected():
    """Cells touching only at a corner are different regions."""
    out = charts.regions(grid(["#.", ".#"]))
    assert [xy(r) for r in out] == [[(0, 1)], [(1, 0)]]


def test_regions_l_shape_connected():
    """An L shape is one region."""
    out = charts.regions(grid(["#..", "#..", "###"]))
    assert len(out) == 1 and sorted(xy(out[0])) == [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]
    assert xy(out[0]) == sorted(xy(out[0]))


def test_regions_none_and_all():
    """No holding cell gives []; every cell holding gives one region of all cells."""
    assert charts.regions(grid(["..", ".."])) == []
    out = charts.regions(grid(["##", "##"]))
    assert len(out) == 1 and len(out[0]) == 4


def test_regions_uneven_axis_values_use_grid_index_adjacency():
    """Neighbours are by grid index, not by value distance: x = 1, 10, 100 are adjacent."""
    out = charts.regions(grid(["###"], xs=[1, 10, 100], ys=[5]))
    assert len(out) == 1


def test_regions_input_order_does_not_matter():
    """Shuffled cell order gives the same answer."""
    cells = grid(["#.#", "#.#"])
    assert charts.regions(cells) == charts.regions(list(reversed(cells)))


def test_regions_incomplete_or_duplicate_grid_is_valueerror():
    """A missing (x, y) pair, or a duplicate one, is a ValueError."""
    cells = grid(["##", "##"])
    with pytest.raises(ValueError):
        charts.regions(cells[1:])
    with pytest.raises(ValueError):
        charts.regions(cells + [cells[0]])


# region map

def attrs(tag):
    return dict(re.findall(r'([\w-]+)="([^"]*)"', tag))


def rects(html, cls):
    return [attrs(m) for m in re.findall(r"<rect\b[^>]*>", html) if f'class="{cls}"' in m]


def texts(html):
    return [(attrs(m.group(1)), m.group(2)) for m in re.finditer(r"<text\b([^>]*)>(.*?)</text>", html, re.S)]


def inside(t, r):
    x, y, w, h = (float(r[k]) for k in ("x", "y", "width", "height"))
    return x <= float(t["x"]) <= x + w and y <= float(t["y"]) <= y + h


def map_html(rows=("#.#", "#.."), **kw):
    return charts.region_map_html(grid(list(rows), xs=kw.pop("xs", [100, 200, 300]),
                                       ys=kw.pop("ys", None)), "Soldiers", "Range", **kw)


def test_region_map_heading_counts_plural_and_singular():
    """The heading states the finding in counts, 'region' singular when there is one."""
    assert "3 of 6 settings pairs hold every condition, in 2 regions" in map_html()
    one = charts.region_map_html(grid(["##", ".."]), "a", "b")
    assert "2 of 4 settings pairs hold every condition, in 1 region" in one
    assert "in 1 regions" not in one
    none = charts.region_map_html(grid(["..", ".."]), "a", "b")
    assert "0 of 4 settings pairs hold every condition, in 0 regions" in none


def test_region_map_one_rect_per_cell_with_classes():
    """One rect per cell: 'cell holds' for holding, 'cell fails' otherwise."""
    html = map_html()
    assert len(rects(html, "cell holds")) == 3
    assert len(rects(html, "cell fails")) == 3


def test_region_map_positions_are_linear_in_values():
    """Uneven x values (100, 110, 300) are placed linearly in the value, not equal-spaced by index."""
    html = charts.region_map_html(grid(["###", "###"], xs=[100, 110, 300], ys=[2, 4]), "x", "y")
    xs = sorted({float(r["x"]) for r in rects(html, "cell holds")})
    assert len(xs) == 3
    assert (xs[1] - xs[0]) / 10 == pytest.approx((xs[2] - xs[1]) / 190, rel=1e-3)
    ws = {r["width"] for r in rects(html, "cell holds")}
    assert len(ws) == 1


def test_region_map_axis_names_and_tick_labels():
    """Axis names and a tick label per grid value appear as text."""
    html = charts.region_map_html(grid(["###", "###"], xs=[100, 200, 300], ys=[2, 4]), "Soldiers <n>", "Range")
    t = [s for _, s in texts(html)]
    assert "Soldiers &lt;n&gt;" in t and "Range" in t
    assert "Soldiers <n>" not in html
    for v in ("100", "200", "300", "2", "4"):
        assert v in t


def test_region_map_region_labels_at_first_cell():
    """Regions are numbered 1, 2 with a text label at each region's first cell."""
    html = map_html(rows=("#.#", "#.."))
    holds = rects(html, "cell holds")
    first = {1: (100, 0), 2: (300, 1)}
    by_pos = {}
    for r in holds:
        by_pos[(float(r["x"]), float(r["y"]))] = r
    xs = sorted({float(r["x"]) for r in rects(html, "cell holds") + rects(html, "cell fails")})
    ys = sorted({float(r["y"]) for r in rects(html, "cell holds") + rects(html, "cell fails")})
    labels = {s: a for a, s in texts(html) if s in ("1", "2") and "x" in a and "y" in a}
    assert set(labels) == {"1", "2"}
    # region 1 starts at x=100 (leftmost column), region 2 at x=300 (rightmost column)
    assert any(inside(labels["1"], r) and float(r["x"]) == xs[0] for r in holds)
    assert any(inside(labels["2"], r) and float(r["x"]) == xs[2] for r in holds)
    assert len(ys) == 2


def test_region_map_legend_words_and_table():
    """Legend words appear; the table has class words and one row per region with ranges in words."""
    html = map_html(rows=("###", "..."), ys=[2, 4])
    assert "holds every condition" in html and "fails at least one" in html
    assert 'class="words"' in html
    rows = re.findall(r"<tr\b.*?</tr>", re.search(r'<table class="words".*?</table>', html, re.S).group(0), re.S)
    body = [r for r in rows if "<td" in r]
    assert len(body) == 1
    cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>.*?</td>", body[0], re.S)]
    assert cells[0] == "1" and cells[1] == "3"
    assert "x from 100 to 300, y from 4 to 4" in " ".join(cells)


def test_region_map_table_one_row_per_region():
    """Two regions give two body rows."""
    html = map_html()
    table = re.search(r'<table class="words".*?</table>', html, re.S).group(0)
    assert table.count("<td") // max(1, len(re.findall(r"<td", re.findall(r"<tr\b.*?</tr>", table, re.S)[-1]))) == 2


def test_region_map_no_log_parameter():
    """There is no log-scale option."""
    for fn in (charts.region_map_html, charts.small_multiples_html):
        assert not any("log" in p for p in inspect.signature(fn).parameters)


def test_region_map_needs_two_values_per_axis():
    """One distinct value on an axis is a ValueError."""
    with pytest.raises(ValueError):
        charts.region_map_html(grid(["###"], ys=[5]), "x", "y")
    with pytest.raises(ValueError):
        charts.region_map_html(grid(["#", "#"], xs=[5]), "x", "y")


def test_region_map_failing_counts_all_or_none():
    """With 'failing', failing cells show the count as text and the legend explains it; mixed is a ValueError."""
    cells = grid(["#.", ".."])
    for c in cells:
        c["failing"] = 0 if c["holds"] else 2
    html = charts.region_map_html(cells, "x", "y")
    fails = rects(html, "cell fails")
    twos = [a for a, s in texts(html) if s == "2" and "x" in a]
    assert len(fails) == 3 and sum(any(inside(t, r) for t in twos) for r in fails) == 3
    assert "number = conditions failing" in html
    assert "number = conditions failing" not in charts.region_map_html(grid(["#.", ".."]), "x", "y")
    del cells[0]["failing"]
    with pytest.raises(ValueError):
        charts.region_map_html(cells, "x", "y")


def test_region_map_css_classes_only_and_safe():
    """Colour only through a <style> block (with dark mode); no inline fill, no script, escaped title, deterministic."""
    html = map_html(title="A <b>title</b>")
    assert "<style" in html and "prefers-color-scheme: dark" in html
    assert "fill=" not in html.replace("text-anchor", "") and 'style="' not in html
    assert "<script" not in html.lower()
    assert "<b>title" not in html and "&lt;b&gt;title" in html
    assert html == map_html(title="A <b>title</b>")
    assert 'id="' not in html or html == map_html(title="A <b>title</b>")


# small multiples

def scan(label_won, size=10):
    """label_won: {enemy_heads: won}; break-even computed as scan() does (first won -> lost step)."""
    heads = sorted(label_won)
    cells = [CellResult(enemy_heads=h, fights=[], mean_margin=0.5 if label_won[h] else -0.5, won=label_won[h])
             for h in heads]
    beats = loses = None
    for a, b in zip(cells, cells[1:]):
        if a.won and not b.won:
            beats, loses = a.enemy_heads, b.enemy_heads
            break
    return ScanResult(size=size, cells=cells, beats=beats, loses_to=loses)


A = scan({1: True, 2: True, 3: False, 4: False})
B = scan({3: True, 5: True, 7: False, 9: False})
C = scan({1: True, 2: True, 3: True})


def svgs(html):
    return re.findall(r"<svg\b.*?</svg>", html, re.S)


def dots(svg):
    return [attrs(m) for m in re.findall(r"<(?:circle|rect)\b[^>]*>", svg) if 'class="cell' in m]


def sm(panels=None, **kw):
    return charts.small_multiples_html(panels or [("alpha", A), ("beta", B)], **kw)


def test_sm_heading_and_panel_counts():
    """Heading states the panel count; one svg per panel; dot counts and won/lost classes match the cells."""
    html = sm([("alpha", A), ("beta", B), ("gamma", C)])
    assert "3 panels, same enemy headcounts on every panel" in html
    s = svgs(html)
    assert len(s) == 3
    assert [len(dots(x)) for x in s] == [4, 4, 3]
    assert html.count('class="cell won"') == 2 + 2 + 3 and html.count('class="cell lost"') == 2 + 2 + 0


def test_sm_common_x_scale():
    """The same headcount lands on the same pixel x in every panel, over the union range."""
    s = svgs(sm())
    def cx(svg):
        return [float(d.get("cx", d.get("x"))) for d in dots(svg)]
    a, b = cx(s[0]), cx(s[1])           # A: heads 1,2,3,4   B: heads 3,5,7,9
    assert a[2] == pytest.approx(b[0], abs=1e-3)    # headcount 3 in both
    pos = {1: a[0], 2: a[1], 3: a[2], 4: a[3], 5: b[1], 7: b[2], 9: b[3]}
    step = pos[2] - pos[1]
    for h in pos:
        assert pos[h] == pytest.approx(pos[1] + (h - 1) * step, abs=1e-2)
    vb = {re.search(r'viewBox="([^"]+)"', x).group(1) for x in s}
    assert len(vb) == 1


def test_sm_markers_between_beats_and_loses_to():
    """A panel with a break-even has one dashed marker between its two dots; one without says so in text."""
    html = sm([("alpha", A), ("gamma", C)])
    s = svgs(html)
    marks = [m for m in re.findall(r"<line\b[^>]*>", s[0]) if 'class="marker"' in m]
    assert len(marks) == 1
    m = attrs(marks[0])
    assert m["x1"] == m["x2"]
    xs = sorted(float(c.get("cx", c.get("x"))) for c in dots(s[0]))
    assert xs[1] < float(m["x1"]) < xs[2]
    assert 'class="marker"' not in s[1]
    assert "no break-even in range" in s[1] and "no break-even in range" not in s[0]
    assert html.count("no break-even in range") == 1


def test_sm_labels_and_table_counts_only():
    """Panel labels appear above each panel; the table lists label, beats, loses_to or none; no ratios."""
    html = sm([("alpha", A), ("gamma", C)])
    t = [s for _, s in texts(html)]
    assert "alpha" in t and "gamma" in t
    table = re.search(r'<table class="words".*?</table>', html, re.S).group(0)
    rows = [[re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>.*?</t[dh]>", r, re.S)]
            for r in re.findall(r"<tr\b.*?</tr>", table, re.S)]
    body = [r for r in rows if r and r[0] in ("alpha", "gamma")]
    assert [r[:3] for r in body] == [["alpha", "2", "3"], ["gamma", "3", "none"]]
    assert "%" not in table and "ratio" not in table.lower()


def test_sm_panel_count_limits():
    """Fewer than 2 or more than 12 panels is a ValueError; 2 and 12 are fine."""
    with pytest.raises(ValueError):
        charts.small_multiples_html([("a", A)])
    with pytest.raises(ValueError):
        charts.small_multiples_html([("p%d" % i, A) for i in range(13)])
    assert len(svgs(charts.small_multiples_html([("p%d" % i, A) for i in range(12)]))) == 12
    assert len(svgs(charts.small_multiples_html([("p%d" % i, A) for i in range(2)]))) == 2


def test_sm_empty_cells_is_valueerror():
    """A panel with no cells is a ValueError."""
    empty = ScanResult(size=1, cells=[], beats=None, loses_to=None)
    with pytest.raises(ValueError):
        charts.small_multiples_html([("a", A), ("e", empty)])


def test_sm_escaping_css_no_script_determinism():
    """Labels and title are escaped; colour via a <style> block with dark mode; no script; deterministic."""
    panels = [("<i>a</i>", A), ("b&c", B)]
    html = charts.small_multiples_html(panels, title="T <u>")
    assert "<i>a" not in html and "&lt;i&gt;a" in html and "b&amp;c" in html
    assert "<u>" not in html
    assert "<style" in html and "prefers-color-scheme: dark" in html
    assert "<script" not in html.lower() and 'style="' not in html
    assert "fill=" not in html.replace("text-anchor", "")
    assert html == charts.small_multiples_html(panels, title="T <u>")
