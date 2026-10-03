# spec: item 7b (briefs/t7b.md): decision-tree summary in words (scripts/skilllab/tree.py)
"""Greedy CART summary: hand-computed tiny sets, exact thresholds, exact words."""
import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.tree import Node, fit_tree, tree_words  # noqa: E402


def _rows(feats, labels, names=("a",)):
    return [dict(zip(names, f if isinstance(f, tuple) else (f,)), holds=h) for f, h in zip(feats, labels)]


def _leaf(node, holds, fails):
    assert node.feature is None and node.left is None and node.right is None
    assert (node.holds, node.fails) == (holds, fails)


def test_one_clean_split_midpoint_exact():
    """Four rows, one feature: split at the midpoint 1.5 of the two distinct values, both leaves pure."""
    t = fit_tree(_rows([1, 1, 2, 2], [True, True, False, False]), ["a"], 3, 1)
    assert (t.feature, t.threshold) == ("a", 1.5)
    _leaf(t.left, 2, 0)
    _leaf(t.right, 0, 2)


def test_split_picks_lowest_weighted_gini_between_consecutive_values():
    """Values 100,200,500,600: the clean split is the midpoint of 200 and 500, which is 350."""
    t = fit_tree(_rows([100, 200, 500, 600], [True, True, False, False], ("range",)), ["range"], 2, 1)
    assert (t.feature, t.threshold) == ("range", 350.0)
    _leaf(t.left, 2, 0)
    _leaf(t.right, 0, 2)


def test_xor_needs_depth_two():
    """XOR of a and b: depth 1 leaves stay mixed (1 and 1); depth 2 separates fully."""
    rows = [{"a": 0, "b": 0, "holds": False}, {"a": 0, "b": 1, "holds": True},
            {"a": 1, "b": 0, "holds": True}, {"a": 1, "b": 1, "holds": False}]
    t1 = fit_tree(rows, ["a", "b"], 1, 1)
    assert (t1.feature, t1.threshold) == ("a", 0.5)  # all first splits tie; feature order picks a
    _leaf(t1.left, 1, 1)
    _leaf(t1.right, 1, 1)
    t2 = fit_tree(rows, ["a", "b"], 2, 1)
    assert (t2.left.feature, t2.left.threshold) == ("b", 0.5)
    assert (t2.right.feature, t2.right.threshold) == ("b", 0.5)
    _leaf(t2.left.left, 0, 1)
    _leaf(t2.left.right, 1, 0)
    _leaf(t2.right.left, 1, 0)
    _leaf(t2.right.right, 0, 1)


def test_tie_between_features_broken_by_feature_order():
    """a and b separate the rows identically; the first in `features` wins, and reversing flips it."""
    rows = [{"a": 1, "b": 5, "holds": True}, {"a": 2, "b": 6, "holds": False}]
    assert fit_tree(rows, ["a", "b"], 1, 1).feature == "a"
    assert fit_tree(rows, ["b", "a"], 1, 1).feature == "b"


def test_tie_between_thresholds_broken_by_lower():
    """Values 1,2,3 labelled F,T,F: splits at 1.5 and 2.5 tie on impurity; the lower is chosen."""
    t = fit_tree(_rows([1, 2, 3], [False, True, False]), ["a"], 1, 1)
    assert t.threshold == 1.5
    _leaf(t.left, 0, 1)
    _leaf(t.right, 1, 1)


def test_min_leaf_blocks_the_best_split():
    """1,2,3,4 labelled F,F,F,T: the pure split at 3.5 leaves one row, so min_leaf 2 forces 2.5."""
    rows = _rows([1, 2, 3, 4], [False, False, False, True])
    t = fit_tree(rows, ["a"], 5, 2)
    assert t.threshold == 2.5
    _leaf(t.left, 0, 2)
    _leaf(t.right, 1, 1)  # cannot split again under min_leaf 2
    assert fit_tree(rows, ["a"], 5, 1).threshold == 3.5


def test_min_leaf_with_no_allowed_split_gives_a_leaf():
    """Four rows with min_leaf 3 cannot put 3 on both sides."""
    _leaf(fit_tree(_rows([1, 2, 3, 4], [False, False, False, True]), ["a"], 5, 3), 1, 3)


def test_max_depth_zero_is_a_single_leaf():
    """max_depth 0 never splits."""
    _leaf(fit_tree(_rows([1, 2], [True, False]), ["a"], 0, 1), 1, 1)


def test_pure_sets_and_single_row_are_leaves():
    """All holds, all fails and one row stop at once."""
    _leaf(fit_tree(_rows([1, 2, 3], [True] * 3), ["a"], 4, 1), 3, 0)
    _leaf(fit_tree(_rows([1, 2, 3], [False] * 3), ["a"], 4, 1), 0, 3)
    _leaf(fit_tree(_rows([7], [True]), ["a"], 4, 1), 1, 0)


def test_identical_feature_values_cannot_split():
    """No two distinct values means no candidate threshold."""
    _leaf(fit_tree(_rows([5, 5, 5], [True, False, True]), ["a"], 4, 1), 2, 1)


def test_deterministic():
    """Same rows give an identical tree (dataclass equality), including after reordering irrelevant dict keys."""
    rows = _rows([3, 1, 4, 1, 5, 9, 2, 6], [True, False, True, False, True, True, False, False])
    assert fit_tree(rows, ["a"], 3, 1) == fit_tree([dict(r) for r in rows], ["a"], 3, 1)


def test_required_inputs_have_no_defaults():
    """max_depth and min_leaf are required arguments."""
    ps = inspect.signature(fit_tree).parameters
    assert ps["max_depth"].default is inspect.Parameter.empty
    assert ps["min_leaf"].default is inspect.Parameter.empty


@pytest.mark.parametrize("depth,leaf", [(-1, 1), (1, 0), (1, -2)])
def test_bad_knobs_raise(depth, leaf):
    """max_depth < 0 or min_leaf < 1 is a ValueError."""
    with pytest.raises(ValueError):
        fit_tree(_rows([1, 2], [True, False]), ["a"], depth, leaf)


def test_bad_rows_raise():
    """Empty rows, a missing feature and a non-numeric feature are ValueErrors."""
    with pytest.raises(ValueError):
        fit_tree([], ["a"], 1, 1)
    with pytest.raises(ValueError):
        fit_tree([{"holds": True}], ["a"], 1, 1)
    with pytest.raises(ValueError):
        fit_tree([{"a": "wide", "holds": True}], ["a"], 1, 1)


def _leafn(h, f):
    return Node(None, None, None, None, h, f)


def test_words_small_tree_exact():
    """A one-split tree reads as two if-lines, each followed by its indented leaf; counts only."""
    t = fit_tree(_rows([100, 200, 500, 600], [True, True, False, False], ("range",)), ["range"], 2, 1)
    assert tree_words(t) == [
        "if range <= 350 (2 settings sets):",
        "  holds in 2 of 2 settings sets",
        "if range > 350 (2 settings sets):",
        "  fails in 2 of 2 settings sets",
    ]


def test_words_names_map_and_nesting_indent():
    """names maps feature keys to words; a second level indents by two more spaces."""
    node = Node("a", 1.5, Node("b", 0.5, _leafn(0, 1), _leafn(1, 0), 1, 1), _leafn(0, 2), 1, 3)
    assert tree_words(node, {"a": "attack reach"}) == [
        "if attack reach <= 1.5 (2 settings sets):",
        "  if b <= 0.5 (1 settings sets):",
        "    fails in 1 of 1 settings sets",
        "  if b > 0.5 (1 settings sets):",
        "    holds in 1 of 1 settings sets",
        "if attack reach > 1.5 (2 settings sets):",
        "  fails in 2 of 2 settings sets",
    ]


def test_words_leaf_wording_counts_not_ratios():
    """The majority outcome is named with its count out of the total; no percent signs or decimals."""
    assert tree_words(_leafn(9, 1)) == ["holds in 9 of 10 settings sets"]
    assert tree_words(_leafn(0, 4)) == ["fails in 4 of 4 settings sets"]
    assert tree_words(_leafn(1, 3)) == ["fails in 3 of 4 settings sets"]
    assert not any("%" in s for s in tree_words(_leafn(9, 1)))
