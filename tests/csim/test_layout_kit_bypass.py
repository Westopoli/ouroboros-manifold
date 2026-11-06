# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-6
"""S-247 wave 2, leaf 2: `--break bypass` and the bypass check (R-112-05 check 3, R-113-03).

Criterion 6: the edit is deterministic, `om_lk_run_checks` runs after it, and the JSON's `checks` then show it: the way-round lane of the first choke is gone.
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

NAME = "bypass"


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    return H.build_cli(tmp_path_factory)


def pair(cli, seed, sides, canvas=None):
    return H.load(H.dump(cli, seed, sides, canvas=canvas)), H.load(H.dump(cli, seed, sides, canvas=canvas, brk=NAME))


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_bypass_false_after_break_true_without(cli, seed, sides):
    """S-247 R-112-05: seeds 1..12 x three sides modes: the bypass check is true on the layout and false after
    --break bypass, in the JSON's `checks` and in the Python oracle alike."""
    base, broken = pair(cli, seed, sides)
    assert ((broken["checks"][NAME], H.py_checks(broken)[NAME]), (base["checks"][NAME], H.py_checks(base)[NAME])) == (
        (False, False), (True, True))


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_bypass_break_is_exactly_the_spec_edit(cli, seed, sides):
    """S-247 R-112-05: `--break bypass` removes the way-round lane of the first choke. Nothing else changes, and the figures that follow from the lanes
    (fairness distances, route_count, every check) are recomputed after the edit."""
    base, broken = pair(cli, seed, sides)
    assert H.edit_problems(base, broken, NAME) + H.consistency_problems(broken) + H.consistency_problems(base) == []
