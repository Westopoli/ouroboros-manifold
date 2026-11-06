# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-6
"""S-247 wave 2, leaf 2: `--break bounds` and the bounds check (R-112-05 check 6).

Criterion 6: the edit is deterministic, `om_lk_run_checks` runs after it, and the JSON's `checks` then show it: the first place lies 100 wu past the canvas edge.
Positive control: the check is false after the edit and true without it, judged twice: by the JSON's `checks` and
by a Python re-implementation of the spec's check over the JSON's own lanes (tests/csim/layout_kit_cli_helpers.py,
`py_checks`, a Dijkstra written there). The edit itself is compared with the edit the spec words ("apply_break").
Red until csrc/tools/layout_dump.c exists. Budget: see test_layout_kit_cli.py.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import layout_kit_cli_helpers as H   # noqa: E402

NAME = "bounds"


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    return H.build_cli(tmp_path_factory)


def pair(cli, seed, sides, canvas=None):
    return H.load(H.dump(cli, seed, sides, canvas=canvas)), H.load(H.dump(cli, seed, sides, canvas=canvas, brk=NAME))


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_bounds_false_after_break_true_without(cli, seed, sides):
    """S-247 R-112-05: seeds 1..12 x three sides modes: the bounds check is true on the layout and false after
    --break bounds, in the JSON's `checks` and in the Python oracle alike."""
    base, broken = pair(cli, seed, sides)
    assert ((broken["checks"][NAME], H.py_checks(broken)[NAME]), (base["checks"][NAME], H.py_checks(base)[NAME])) == (
        (False, False), (True, True))


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_bounds_break_is_exactly_the_spec_edit(cli, seed, sides):
    """S-247 R-112-05: `--break bounds` sets the first place's x, and its node's x, to canvas + 100 wu. Nothing else changes, and the figures that follow from the lanes
    (fairness distances, route_count, every check) are recomputed after the edit."""
    base, broken = pair(cli, seed, sides)
    assert H.edit_problems(base, broken, NAME) + H.consistency_problems(broken) + H.consistency_problems(base) == []


@pytest.mark.parametrize("canvas", [8000, 16000, 64000])
@pytest.mark.parametrize("sides", H.SIDES)
def test_S_247_bounds_break_follows_the_canvas(cli, sides, canvas):
    """S-247 R-112-05: the edge is the canvas that was asked for: at 8,000, 16,000 and 64,000 wu the layout is on the
    canvas (true), and after --break bounds the first place and its node sit at canvas + 100 wu and the check is
    false."""
    base, broken = pair(cli, 4, sides, canvas=canvas)
    p0 = broken["places"][0]
    assert (base["checks"]["bounds"], broken["checks"]["bounds"], p0["x"], broken["nodes"][p0["node"]]["x"],
            H.edit_problems(base, broken, NAME)) == (True, False, canvas + 100, canvas + 100, [])
