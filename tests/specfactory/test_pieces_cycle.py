# spec: docs/northstar/plans/2026-10-07-visible-game-spec.md, HARNESS-pieces-cycle (FINDING-pieces-cycle-undetected)
# Rule pins: (none: harness piece, no bible rule; proves FINDING-pieces-cycle-undetected)
"""HARNESS-pieces-cycle: `pieces.py --check` fails on a `depends_on` cycle and names it.

UNSTATED INTERFACE choices (the paragraph names only `check_depends_acyclic` and
the `A -> B -> ... -> A` form):
  * `scripts.specfactory.pieces.check_depends_acyclic(pieces: list[dict])` takes the
    same list `load_pieces` returns and returns findings in the shape of
    `check_owns_disjoint`: a list of (level, id, message) tuples; a cycle is level
    "FAIL" and its message contains the chain `A -> B -> ... -> A` (first node
    repeated last, each step a `depends_on` edge: A depends_on B). Which node the
    chain starts at is not asserted, only that it is closed and every step is an edge.
  * Ids named in `depends_on` that are not rows present are ignored ("rows present").
  * `run_check` is the `--check` path; it must include the pass.
Positive control: the layerspot cycle as it stood on 13c5e364 (read with `git show`).
"""
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))
import pieces  # noqa: E402

LAYERSPOT_COMMIT = "13c5e364"
CHAIN_RE = re.compile(r"[\w.-]+(?: -> [\w.-]+)+")


def row(pid, deps=(), owns=()):
    return {"id": pid, "owns": list(owns), "depends_on": list(deps)}


def cycle_chains(findings):
    out = []
    for level, _pid, msg in findings:
        if level == "FAIL":
            out += [m.split(" -> ") for m in CHAIN_RE.findall(msg)]
    return out


def assert_names_closed_cycle(findings, rows, expect_nodes):
    by_id = {r["id"]: r for r in rows}
    chains = cycle_chains(findings)
    assert chains, f"no FAIL finding names a cycle as 'A -> B -> A': {findings}"
    for ch in chains:
        if set(ch) == set(expect_nodes) and ch[0] == ch[-1]:
            for a, b in zip(ch, ch[1:]):
                assert b in by_id[a]["depends_on"], f"{a} -> {b} is not a depends_on edge"
            return
    raise AssertionError(f"no closed chain over {sorted(expect_nodes)} in {chains}")


def test_two_edge_cycle_fixture_fails_and_names_it():
    """three rows, B and C depend on each other; fails, names B and C."""
    rows = [row("A", ["B"]), row("B", ["C"]), row("C", ["B"])]
    f = pieces.check_depends_acyclic(rows)
    assert any(x[0] == "FAIL" for x in f), f
    assert_names_closed_cycle(f, rows, {"B", "C"})


def test_acyclic_fixture_of_same_shape_passes():
    """the same three rows with the back edge removed produce no finding."""
    rows = [row("A", ["B"]), row("B", ["C"]), row("C", [])]
    assert pieces.check_depends_acyclic(rows) == []


def test_dangling_dependency_is_not_a_cycle():
    """an id not among the rows present is ignored."""
    assert pieces.check_depends_acyclic([row("A", ["GONE"]), row("B", ["A"])]) == []


def test_layerspot_cycle_as_on_13c5e364_fails_positive_control():
    """FINDING-pieces-cycle-undetected positive control: layerspot with its three extra edges, E2/E4/R087-WIRE edges back."""
    text = subprocess.run(
        ["git", "show", f"{LAYERSPOT_COMMIT}:docs/northstar/plans/push/pieces.toml"],
        cwd=REPO, capture_output=True, text=True, check=True).stdout
    keep = {"VG-CONTRACT-layerspot", "LAB-REV2-E2", "LAB-REV2-E4", "VG-T-R087-WIRE"}
    rows = [p for p in tomllib.loads(text)["piece"] if p["id"] in keep]
    assert {r["id"] for r in rows} == keep
    f = pieces.check_depends_acyclic(rows)
    assert cycle_chains(f), f
    assert any("VG-CONTRACT-layerspot" in ch for ch in cycle_chains(f)), f


def test_check_mode_runs_the_pass():
    """run_check (the --check path) reports the cycle; a stub collector keeps it offline."""
    toml = REPO / "tests" / "specfactory" / "_pcyc_unused"
    rows = [row("B", ["C"]), row("C", ["B"])]
    orig = pieces.load_pieces
    pieces.load_pieces = lambda _p: rows
    try:
        findings, _n = pieces.run_check(toml, REPO, collector=lambda ids, root: (0, ""))
    finally:
        pieces.load_pieces = orig
    assert cycle_chains(findings), findings


def test_owns_disjoint_unchanged_for_cyclic_rows_with_shared_owns():
    """check_owns_disjoint still skips an overlap when the rows depend on each other."""
    rows = [row("B", ["C"], ["x.py"]), row("C", ["B"], ["x.py"])]
    assert pieces.check_owns_disjoint(rows) == []


def test_live_pieces_toml_has_no_cycle():
    """live pieces.toml is acyclic once LAB-REV2-L7 -> LAB-REV2-SPEED -> LAB-REV2-FIX -> LAB-REV2-L7 is broken."""
    f = pieces.check_depends_acyclic(pieces.load_pieces(pieces.DEFAULT_PIECES))
    assert f == [], f
