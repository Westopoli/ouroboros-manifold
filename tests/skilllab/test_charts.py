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


# =====================================================================================================================
# LAB-REV2-L5 additions. spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-spec.md::Pieces::L5 ("the agreement table; the region map and
# the refinement listing"); ruling 4 (a play that beats 48 is a ceiling hit, never "no gain"); ruling 1 and contract.CellResult.defect
# (a draw or a cap in a cell is a lab defect, never a result); ruling 5 (a mismatch is a finding); README section 5 chart rules.
#
# INTERFACE FIXED HERE:
#   charts.small_multiples_html(panels, title=None)   (unchanged signature) now reads ScanResult.ceiling_hit and CellResult.defect:
#       - a panel whose scan has ceiling_hit draws its own mark, an svg element with class "ceiling" and the svg text "ceiling hit",
#         instead of the text "no break-even in range" and without the dashed `marker` line; its table row contains "ceiling hit"
#         and its Beats cell holds the top headcount (scan.beats)
#       - a panel without a break-even that is not a ceiling hit keeps "no break-even in range" (negative control)
#       - a defect cell's dot has the class tokens "cell defect" and neither "won" nor "lost"
#   charts.refinement_html(entries, title=None) -> str     entries = sweep_summary.json["families"] (dict family -> L4 entry with
#       "skipped", "refined", "refined_vs" {role: [values]}); one <table class="words"> with a header row and one row per family in
#       dict order: cell 1 the family; cell 2 for a skipped family "skipped: <the reason>"; else one clause per role in refined_vs
#       order "<role>: v1, v2" (values ascending, formatted with format(v, "g")) or "<role>: no crossing" when the role's list is empty;
#       a family with no role at all reads "no crossing"
#   charts.agreement_html(groups, title=None) -> str       groups = dict label -> iterable of agreement words; one <table class="words">
#       header "Group", the five words of evidence.AGREEMENTS in order, "Fights"; a row per label in dict order with the counts (never
#       ratios or percents) and the total; a count cell of "both_wrong" above zero has class "finding"
# =====================================================================================================================
def _ceiling_scan(top=48, heads=(8, 16, 24, 32, 40, 48)):
    cells = [CellResult(enemy_heads=h, fights=[], mean_margin=0.5, won=True) for h in heads]
    return ScanResult(size=16, cells=cells, beats=top, loses_to=None, ceiling_hit=True)


def _svgs(html):
    return re.findall(r"<svg.*?</svg>", html, flags=re.S)


def _visible(html):
    """The text a reader sees: no <style> block, no tags."""
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", "", html, flags=re.S))


def _has_class(svg, token):
    return any(token in m.split() for m in re.findall(r'class="([^"]*)"', svg))


def _table_rows(html):
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", html, flags=re.S):
        out.append([(m.group(1).strip(), re.sub(r"<[^>]+>", "", m.group(2)).strip())
                    for m in re.finditer(r"<t[hd]([^>]*)>(.*?)</t[hd]>", tr, flags=re.S)])
    return out


def test_l5_ceiling_hit_panel_says_ceiling_hit_not_no_break_even():
    html = charts.small_multiples_html([("up", _ceiling_scan()), ("cross", scan({8: True, 16: True, 24: False})),
                                        ("never", scan({8: False, 16: False, 24: False}))])
    s = _svgs(html)
    assert len(s) == 3
    assert _has_class(s[0], "ceiling") and "ceiling hit" in s[0] and "no break-even in range" not in s[0] and not _has_class(s[0], "marker")
    assert not _has_class(s[1], "ceiling") and not _has_class(s[2], "ceiling")        # negative controls: only the ceiling scan
    assert "no break-even in range" in s[2] and "ceiling hit" not in s[2]
    assert _has_class(s[1], "marker")                                                 # a real crossing keeps its marker


def test_l5_ceiling_hit_table_row_names_it_and_shows_the_top_headcount():
    html = charts.small_multiples_html([("up", _ceiling_scan()), ("cross", scan({8: True, 16: True, 24: False}))])
    rows = {r[0][1]: [c[1] for c in r] for r in _table_rows(html) if r and r[0][1] in ("up", "cross")}
    assert "48" in rows["up"] and any("ceiling hit" in c for c in rows["up"])
    assert not any("ceiling hit" in c for c in rows["cross"])


def test_l5_defect_cell_is_drawn_as_a_defect_not_as_a_result():
    """Ruling 1: a draw or a cap in a cell is a lab defect; the dot is neither won nor lost."""
    sc = scan({8: True, 16: True, 24: False})
    cells = list(sc.cells)
    cells[1] = CellResult(enemy_heads=16, fights=[], mean_margin=0.0, won=False, defect=True)
    html = charts.small_multiples_html([("d", ScanResult(size=10, cells=cells, beats=None, loses_to=None)), ("plain", sc)])
    s = _svgs(html)
    classes = [set(m.split()) for m in re.findall(r'<circle class="([^"]*)"', s[0])]
    assert sum("defect" in c for c in classes) == 1
    assert all(not ({"won", "lost"} & c) for c in classes if "defect" in c)
    assert all("defect" not in c for c in [set(m.split()) for m in re.findall(r'<circle class="([^"]*)"', s[1])])


_ENTRIES = {
    "vision": {"skipped": None, "refined": [0.1875, 0.375], "refined_vs": {"naive_attacker": [0.1875, 0.375], "naive_defender": []}},
    "range_up": {"skipped": None, "refined": [], "refined_vs": {"naive_attacker": []}},
    "arc": {"skipped": "the library has no OM_TP_FIRING_ARC_DEG (LAB-REV2-E0 not built)", "refined": [], "refined_vs": {}},
    "emitting": {"skipped": None, "refined": [], "refined_vs": {}},
}


def test_l5_refinement_listing_one_row_per_family_with_the_refined_values_per_role():
    rows = _table_rows(charts.refinement_html(_ENTRIES))
    body = {r[0][1]: r[1][1] for r in rows[1:]}
    assert list(body) == ["vision", "range_up", "arc", "emitting"]
    assert "naive_attacker: 0.1875, 0.375" in body["vision"] and "naive_defender: no crossing" in body["vision"]
    assert body["range_up"] == "naive_attacker: no crossing"
    assert body["arc"] == "skipped: the library has no OM_TP_FIRING_ARC_DEG (LAB-REV2-E0 not built)"
    assert body["emitting"] == "no crossing"


def test_l5_refinement_listing_negative_control_nothing_refined_lists_no_value():
    quiet = {"vision": {"skipped": None, "refined": [], "refined_vs": {"naive_attacker": []}}}
    html = charts.refinement_html(quiet)
    assert "no crossing" in html and not re.search(r"\d\.\d", _visible(html))


def test_l5_refinement_listing_is_deterministic():
    assert charts.refinement_html(_ENTRIES) == charts.refinement_html(_ENTRIES)


_WORDS = ["both_right", "count_wrong_type_right", "both_wrong", "count_right_type_wrong", "n/a"]


def test_l5_agreement_table_counts_each_word_per_group():
    rows = _table_rows(charts.agreement_html({"vision/s3_layer_above": ["both_right", "both_right", "both_wrong", "n/a"],
                                              "vision/s3_types_by_reach": ["both_right"]}))
    assert [c[1] for c in rows[0]] == ["Group"] + _WORDS + ["Fights"]
    assert [c[1] for c in rows[1]] == ["vision/s3_layer_above", "2", "0", "1", "0", "1", "4"]
    assert [c[1] for c in rows[2]] == ["vision/s3_types_by_reach", "1", "0", "0", "0", "0", "1"]


def test_l5_agreement_table_marks_a_both_wrong_count_as_a_finding_and_only_that():
    """Ruling 5: a mismatch is a finding. Positive control: both_wrong > 0 is marked; negative: zero is not, nor any other word."""
    rows = _table_rows(charts.agreement_html({"a": ["both_wrong", "count_right_type_wrong"], "b": ["both_right"]}))
    a, b = rows[1], rows[2]
    assert "finding" in a[1 + _WORDS.index("both_wrong")][0]
    assert not any("finding" in attrs for attrs, _ in b)
    assert not any("finding" in a[1 + i][0] for i, w in enumerate(_WORDS) if w != "both_wrong")


def test_l5_agreement_table_has_counts_not_ratios():
    html = charts.agreement_html({"a": ["both_right"] * 3 + ["both_wrong"]})
    assert "%" not in _visible(html) and "0.75" not in _visible(html) and "0.25" not in _visible(html)


def test_l5_agreement_table_unknown_word_raises_and_empty_group_is_all_zeros():
    with pytest.raises(ValueError):
        charts.agreement_html({"a": ["often_right"]})
    row = _table_rows(charts.agreement_html({"a": []}))[1]
    assert [c[1] for c in row] == ["a", "0", "0", "0", "0", "0", "0"]


# =====================================================================================================================
# LAB-REV2-L5 fix pass (audit of the first L5 tests; decision 31 A "the artifact also shows the cone 3 by 3 grid"; item 9 of the audit).
#
# INTERFACE FIXED HERE:
#   charts.cone_grid_html(rows, title=None) -> str     rows = typed rows (diagram.read_rows). Only rows with family "cone" and kind grid or
#       refined are read; "" when there are none. For each (play, layout, baseline role) among them, sorted as strings, one
#       <table class="words cone-grid" data-play data-layout data-role>: the header row is "Range" then one cell per `point` label
#       (half=22.5 ...) ordered by the number after "=", ascending; then one row per range (knob_value) ascending numerically: first
#       cell the range as format(v, "g"), then one <td data-range data-point data-gain> per header point whose text is the signed gain
#       ("+16", "-8", "0"), gain = break-even(play) - break-even(role) in that series at that range, with the break-even of diagram.py
#       (top headcount when every cell is won, else the headcount before the first won-to-lost step, else 0); a (range, point) that
#       has no rows for the play or for the role reads "-" with data-gain "". Counts, never ratios.
#   charts.refinement_html: the values of a role are listed ascending whatever order they come in, each formatted with format(v, "g")
#       (1.0 reads "1", 360.0 reads "360", 0.1875 stays "0.1875": not str(v)).
# =====================================================================================================================
def _scan_cells(family, play, layout, point, knob, baseline, beats, won=None, kind="grid", heads=(8, 16, 24, 32, 40, 48)):
    """Typed rows (what diagram.read_rows returns, only the columns the grid reads): one row per headcount, won up to `beats`."""
    is_won = (lambda h: h in won) if won is not None else (lambda h: beats is not None and h <= beats)
    return [dict(family=family, play=play, layout=layout, point=point, kind=kind, baseline=baseline, knob_value=float(knob), enemy_heads=h,
                 outcome="side0" if is_won(h) else "side1", ceiling_hit=int(all(is_won(x) for x in heads))) for h in heads]


def _cone_rows(play_be_by_half, role="naive_attacker", base=16, play="s2_concave", layout="81", roles=None):
    rows = []
    for half, per_range in play_be_by_half.items():
        for rng, beats in per_range.items():
            rows += _scan_cells("cone", play, layout, "half=%s" % half, rng, "none", beats)
            for r, b in ((roles(per_range) if roles else {role: {k: base for k in per_range}}).items()):
                rows += _scan_cells("cone", play, layout, "half=%s" % half, rng, r, b[rng])
    return rows


_PLAY_CONE = {22.5: {150: 8, 300: 8, 600: 32}, 45: {150: 8, 300: 32, 600: 40}, 90: {150: 32, 300: 32, 600: 40}}


def _grid_cells(html):
    out = {}
    for tr in re.findall(r"<tr>(.*?)</tr>", html, flags=re.S)[1:]:
        for attrs, text in re.findall(r"<td([^>]*)>(.*?)</td>", tr, flags=re.S):
            rng = re.search(r"data-range=[\"']?([0-9.]+)", attrs)
            if rng:
                pt = re.search(r"data-point=[\"']?(half=[0-9.]+)", attrs).group(1)
                gain = re.search(r"data-gain=[\"']?([-+0-9]*)", attrs).group(1)
                out[(float(rng.group(1)), pt)] = (gain, re.sub(r"<[^>]+>", "", text).strip())
    return out


def test_l5_cone_grid_is_one_table_of_signed_gains_range_by_half_angle():
    html = charts.cone_grid_html(_cone_rows(_PLAY_CONE))
    assert html.count("cone-grid") >= 1 and len(re.findall(r"<table", html)) == 1
    head = [c for _, c in _table_rows(html)[0]]
    assert head == ["Range", "half=22.5", "half=45", "half=90"]
    body = [[c for _, c in r] for r in _table_rows(html)[1:]]
    assert [r[0] for r in body] == ["150", "300", "600"]
    gains = {(150, "half=22.5"): -8, (150, "half=45"): -8, (150, "half=90"): 16, (300, "half=22.5"): -8, (300, "half=45"): 16,
             (300, "half=90"): 16, (600, "half=22.5"): 16, (600, "half=45"): 24, (600, "half=90"): 24}
    cells = _grid_cells(html)
    assert set(cells) == {(float(r), p) for r, p in gains}
    for (r, p), g in gains.items():
        data, text = cells[(float(r), p)]
        assert int(data) == g and int(text) == g, (r, p)
    assert re.search(r"data-play=[\"']?s2_concave", html) and re.search(r"data-layout=[\"']?81", html) and re.search(r"data-role=[\"']?naive_attacker", html)


def test_l5_cone_grid_has_a_table_per_baseline_role_and_ignores_other_families_and_kinds():
    roles = lambda per: {"naive_attacker": {r: 16 for r in per}, "naive_defender": {r: 24 for r in per}}
    rows = _cone_rows({45: {150: 8, 300: 32, 600: 40}}, roles=roles)
    rows += _scan_cells("range_up", "s2_concave", "81", "-", 0.5, "none", 8) + _scan_cells("range_up", "s2_concave", "81", "-", 0.5, "naive_attacker", 16)    # another family: not read
    rows += _scan_cells("cone", "s2_concave", "81", "half=45", 150.0, "none", 48, kind="control_positive")   # a control: not read
    html = charts.cone_grid_html(rows)
    assert sorted(re.findall(r"data-role=[\"']?(naive_\w+)", html)) == ["naive_attacker", "naive_defender"]
    by_role = {role: _grid_cells(t) for role, t in zip(("naive_attacker", "naive_defender"), re.findall(r"<table.*?</table>", html, flags=re.S))}
    assert int(by_role["naive_attacker"][(150.0, "half=45")][0]) == -8 and int(by_role["naive_defender"][(150.0, "half=45")][0]) == -16


def test_l5_cone_grid_a_missing_series_cell_reads_a_dash_and_zero_gain_reads_zero():
    rows = _cone_rows({45: {150: 16, 300: 32}, 90: {300: 16}})        # (150, half=90) has no rows; (150, half=45) is level with the baseline
    cells = _grid_cells(charts.cone_grid_html(rows))
    assert cells[(150.0, "half=90")] == ("", "-")
    assert int(cells[(150.0, "half=45")][0]) == 0 and cells[(150.0, "half=45")][1] in ("0", "+0", "-0")
    assert int(cells[(300.0, "half=90")][0]) == 0


def test_l5_cone_grid_without_cone_rows_is_empty_and_deterministic():
    assert charts.cone_grid_html(_scan_cells("range_up", "p", "81", "-", 0.5, "none", 8)) == "" and charts.cone_grid_html([]) == ""
    rows = _cone_rows(_PLAY_CONE)
    assert charts.cone_grid_html(rows) == charts.cone_grid_html(list(rows))


def test_l5_cone_grid_reads_the_first_won_to_lost_step_and_a_ceiling_as_the_top():
    """Same break-even as diagram.py: a play that wins 8, loses 16, wins 24 has break-even 8; one that wins everywhere has 48."""
    rows = (_scan_cells("cone", "s2_concave", "81", "half=45", 150, "none", None, won={8, 24}) +
            _scan_cells("cone", "s2_concave", "81", "half=45", 150, "naive_attacker", 16) +
            _scan_cells("cone", "s2_concave", "81", "half=45", 300, "none", 48) +
            _scan_cells("cone", "s2_concave", "81", "half=45", 300, "naive_attacker", 16))
    cells = _grid_cells(charts.cone_grid_html(rows))
    assert int(cells[(150.0, "half=45")][0]) == 8 - 16 and int(cells[(300.0, "half=45")][0]) == 48 - 16


def test_l5_refinement_values_are_listed_ascending_and_formatted_with_g_not_str():
    entries = {"damage_up": {"skipped": None, "refined": [], "refined_vs": {"naive_attacker": [1.0, 0.5, 0.1875, 360.0, 22.5],
                                                                          "naive_defender": [0.75]}}}
    body = {r[0][1]: r[1][1] for r in _table_rows(charts.refinement_html(entries))[1:]}
    clause = body["damage_up"]
    assert "naive_attacker: 0.1875, 0.5, 1, 22.5, 360" in clause and "naive_defender: 0.75" in clause
    assert "1.0" not in clause and "360.0" not in clause
