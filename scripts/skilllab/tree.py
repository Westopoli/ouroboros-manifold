"""Greedy CART summary of which settings sets hold, in plain words."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Optional


@dataclass
class Node:
    feature: Optional[str]
    threshold: Optional[float]
    left: Optional["Node"]
    right: Optional["Node"]
    holds: int
    fails: int


def _weighted_gini(h_l, f_l, h_r, f_r):
    def part(h, f):
        n = h + f
        return Fraction(2 * h * f, n)  # n * gini = 2hf / n
    return part(h_l, f_l) + part(h_r, f_r)


def _best_split(rows, features, min_leaf):
    best = None  # (impurity, threshold, feature)
    for feat in features:
        vals = sorted({r[feat] for r in rows})
        for lo, hi in zip(vals, vals[1:]):
            thr = (lo + hi) / 2
            left = [r for r in rows if r[feat] <= thr]
            right = len(rows) - len(left)
            if len(left) < min_leaf or right < min_leaf:
                continue
            h_l = sum(1 for r in left if r["holds"])
            h_r = sum(1 for r in rows if r["holds"]) - h_l
            imp = _weighted_gini(h_l, len(left) - h_l, h_r, right - h_r)
            if best is None or imp < best[0] or (imp == best[0] and best[2] == feat and thr < best[1]):
                best = (imp, thr, feat)
    return best


def _grow(rows, features, depth, max_depth, min_leaf):
    holds = sum(1 for r in rows if r["holds"])
    fails = len(rows) - holds
    if holds == 0 or fails == 0 or depth >= max_depth:
        return Node(None, None, None, None, holds, fails)
    best = _best_split(rows, features, min_leaf)
    if best is None:
        return Node(None, None, None, None, holds, fails)
    _, thr, feat = best
    left = [r for r in rows if r[feat] <= thr]
    right = [r for r in rows if r[feat] > thr]
    return Node(feat, thr, _grow(left, features, depth + 1, max_depth, min_leaf),
                _grow(right, features, depth + 1, max_depth, min_leaf), holds, fails)


def fit_tree(rows, features, max_depth, min_leaf) -> Node:
    if max_depth < 0 or min_leaf < 1:
        raise ValueError("max_depth must be >= 0 and min_leaf >= 1")
    if not rows:
        raise ValueError("no rows")
    for r in rows:
        for f in features:
            v = r.get(f)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError(f"feature {f!r} is missing or not numeric")
    return _grow(rows, features, 0, max_depth, min_leaf)


def _num(x):
    return f"{x:g}"


def tree_words(node, names=None) -> list:
    names = names or {}
    out = []

    def walk(n, pad):
        total = n.holds + n.fails
        if n.feature is None:
            word, k = ("holds", n.holds) if n.holds > n.fails else ("fails", n.fails)
            out.append(f"{pad}{word} in {k} of {total} settings sets")
            return
        name = names.get(n.feature, n.feature)
        for op, child, rel in (("<=", n.left, 0), (">", n.right, 1)):
            out.append(f"{pad}if {name} {op} {_num(n.threshold)} "
                       f"({child.holds + child.fails} settings sets):")
            walk(child, pad + "  ")

    walk(node, "")
    return out
