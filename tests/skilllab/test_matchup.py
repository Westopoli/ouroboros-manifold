# spec: item 7b (briefs/t7b.md): S5 matchup grid (scripts/skilllab/matchup.py)
"""Break-even grid: heading, classes, sentences, escaping, errors, determinism."""
import inspect
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.matchup import matchup_grid_html  # noqa: E402

ROWS = ["Lancer", "Shield"]
COLS = ["Raider", "Archer", "Pike"]
CELLS = {("Lancer", "Raider"): 24, ("Lancer", "Archer"): 16, ("Lancer", "Pike"): 8,
         ("Shield", "Raider"): None, ("Shield", "Archer"): 20, ("Shield", "Pike"): 24}


class _P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []  # (class, [(tag, class, text)])
        self._cur = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._cur = (a.get("class"), [])
            self.tables.append(self._cur)
        elif tag in ("td", "th") and self._cur is not None:
            self._cell = [tag, a.get("class"), ""]

    def handle_data(self, data):
        if self._cell is not None:
            self._cell[2] += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._cur[1].append(tuple(self._cell))
            self._cell = None
        elif tag == "table":
            self._cur = None


def _tables(html):
    p = _P()
    p.feed(html)
    return p.tables


def _grid(html):
    return next(c for k, c in _tables(html) if k and "grid" in k.split())


def _html(cells=CELLS, rows=ROWS, cols=COLS, size=16, **kw):
    return matchup_grid_html(rows, cols, cells, size, **kw)


def test_signature_size_is_required_after_cells():
    """size is a required parameter after cells, before title."""
    ps = list(inspect.signature(matchup_grid_html).parameters.values())
    assert [p.name for p in ps] == ["row_names", "col_names", "cells", "size", "title"]
    assert ps[3].default is inspect.Parameter.empty


def test_heading_exact():
    """The heading names the greatest cell: Lancer vs Raider at 24."""
    assert "Most lopsided pair: Lancer (16 units) beats up to 24 Raider." in _html()


def test_heading_tie_first_in_row_then_column_order():
    """Equal maxima: the first in row-major order wins."""
    cells = dict(CELLS)
    cells[("Shield", "Pike")] = 24
    cells[("Lancer", "Pike")] = 24
    assert "Lancer (16 units) beats up to 24 Raider." in _html(cells)
    cells[("Lancer", "Raider")] = 10
    assert "Lancer (16 units) beats up to 24 Pike." in _html(cells)


def test_heading_ignores_none_cells():
    """None is not a value: the greatest integer is used."""
    cells = {k: None for k in CELLS}
    cells[("Shield", "Archer")] = 3
    assert "Most lopsided pair: Shield (16 units) beats up to 3 Archer." in _html(cells)


def test_grid_headers_and_cell_text_and_classes():
    """One td per cell in row-major order; text is the integer or 'none'; class by comparison with size."""
    cells = _grid(_html())
    ths = [t for tag, _, t in cells if tag == "th"]
    for n in ROWS + COLS:
        assert n in [x.strip() for x in ths]
    tds = [(c, t.strip()) for tag, c, t in cells if tag == "td"]
    assert tds == [("above", "24"), ("level", "16"), ("below", "8"),
                   ("none", "none"), ("above", "20"), ("above", "24")]


def test_words_table_sentences():
    """One sentence per row type, in column order, 'above' cells only."""
    html = _html()
    words = next(c for k, c in _tables(html) if k and "words" in k.split())
    sentences = [t.strip() for tag, _, t in words if tag == "td"]
    assert sentences == ["Lancer beats more than its own size against: Raider",
                         "Shield beats more than its own size against: Archer, Pike"]


def test_words_sentence_for_nothing_in_range():
    """A row with no above cell says so."""
    cells = {k: 16 for k in CELLS}
    html = _html(cells)
    assert "Lancer beats more than its own size against nothing in range" in html
    assert "Shield beats more than its own size against nothing in range" in html


def test_names_are_escaped():
    """A '<b>' in a name never reaches the output raw."""
    rows = ["<b>Lancer", "Shield"]
    cells = {(("<b>Lancer" if r == "Lancer" else r), c): v for (r, c), v in CELLS.items()}
    html = _html(cells, rows=rows, title="T <i>")
    assert "&lt;b&gt;Lancer" in html
    assert "<b>" not in html and "<i>" not in html


def test_missing_pair_raises():
    """Every (row, column) pair must be present."""
    cells = dict(CELLS)
    del cells[("Shield", "Pike")]
    with pytest.raises(ValueError):
        _html(cells)


def test_duplicate_names_raise():
    """Row names and column names must each be unique."""
    with pytest.raises(ValueError):
        _html(rows=["Lancer", "Lancer"])
    with pytest.raises(ValueError):
        _html(cols=["Raider", "Raider", "Pike"])


def test_deterministic_and_static():
    """Same inputs give identical output; no script, no inline style, dark-mode CSS in a style block."""
    a, b = _html(), _html(dict(reversed(list(CELLS.items()))))
    assert a == b
    assert "<script" not in a.lower()
    assert 'style="' not in a
    assert "<style>" in a and "prefers-color-scheme: dark" in a and "var(--" in a
