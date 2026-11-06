# spec: docs/northstar/plans/cascades/layout-kit-assault/spec.md::Tests::AC-6
"""S-247 wave 2, leaf 2: `--break chokes` and the chokes check (R-112-05 check 5, R-113-03).

Criterion 6: the edit is deterministic, `om_lk_run_checks` runs after it, and the JSON's `checks` then show it: the first choke is 800 wu wide.
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

NAME = "chokes"


@pytest.fixture(scope="module")
def cli(tmp_path_factory):
    return H.build_cli(tmp_path_factory)


def pair(cli, seed, sides, canvas=None):
    return H.load(H.dump(cli, seed, sides, canvas=canvas)), H.load(H.dump(cli, seed, sides, canvas=canvas, brk=NAME))


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_chokes_false_after_break_true_without(cli, seed, sides):
    """S-247 R-112-05: seeds 1..12 x three sides modes: the chokes check is true on the layout and false after
    --break chokes, in the JSON's `checks` and in the Python oracle alike."""
    base, broken = pair(cli, seed, sides)
    assert ((broken["checks"][NAME], H.py_checks(broken)[NAME]), (base["checks"][NAME], H.py_checks(base)[NAME])) == (
        (False, False), (True, True))


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_chokes_break_is_exactly_the_spec_edit(cli, seed, sides):
    """S-247 R-112-05: `--break chokes` sets the first choke's width to DRAFT_CHOKE_W_MAX + 100 = 800 wu. Nothing else changes, and the figures that follow from the lanes
    (fairness distances, route_count, every check) are recomputed after the edit."""
    base, broken = pair(cli, seed, sides)
    assert H.edit_problems(base, broken, NAME) + H.consistency_problems(broken) + H.consistency_problems(base) == []


@pytest.mark.parametrize("seed,sides", H.ALL36, ids=H.IDS36)
def test_S_247_chokes_break_prints_800_and_unbroken_widths_are_300_to_700(cli, seed, sides):
    """S-247 R-113-03 R-112-05: without --break every choke is 300..700 wu wide (the band of DRAFT_CHOKE_W_MIN and
    _MAX, both ends allowed); with it the first choke's width prints 800.00 and the other chokes are untouched."""
    base, broken = pair(cli, seed, sides)
    raw = H.load_raw(H.dump(cli, seed, sides, brk=NAME))["chokes"]
    assert ([H.CHOKE_W_MIN <= c["width"] <= H.CHOKE_W_MAX for c in base["chokes"]], raw[0]["width"],
            [c["width"] for c in broken["chokes"][1:]]) == (
        [True] * len(base["chokes"]), "800.00", [c["width"] for c in base["chokes"][1:]])
