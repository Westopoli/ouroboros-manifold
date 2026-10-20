# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (test T2 "Frozen names"; requirement R6, R8); Architect ruling 2026-10-20 on the names list; piece LAB-REV3-A
"""LAB-REV3-A, the frozen names (Architect ruling 2026-10-20, relayed by the overseer): the lab contract file keeps a list of names other
code and the artifact match on; a rename is a contract change. Fast, fakes only.

BUILDER CONTRACT:
  scripts/skilllab/contract.py defines
      FROZEN_NAMES = ("inert_knob", "category")   # names other code and the artifact match on; adding is fine, renaming or removing is a contract change
  a tuple of strings. Today it holds the probe's refusal reason and the unavailable family's name, in that order. Piece LAB-REV3-C adds
  `no_reach_stall` and `decided_one_way_reach` later (adding is fine), so these tests pin membership and the two positions above, never the
  length. The probe's reason string and the sweep's family key are taken from the constant, not repeated as literals: the tests compare
  against the FROZEN_NAMES entries, so a rename in contract.py moves code and artifact together or fails here.
Red today: `contract.FROZEN_NAMES` does not exist (AttributeError)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, _fr, fake_builds  # noqa: E402
from scripts.skilllab import contract, sweep  # noqa: E402

CAPS = sweep.Capabilities(arc=True, cone=True)


def test_frozen_names_is_a_tuple_of_strings_holding_both_names():
    """The constant exists, is a tuple of strings, and holds the probe reason (first) and the unavailable family (second)."""
    names = contract.FROZEN_NAMES
    assert isinstance(names, tuple) and all(isinstance(n, str) for n in names)
    assert names[:2] == ("inert_knob", "category")


def test_the_probes_refusal_reason_is_a_frozen_name(tmp_path):
    """The `reason` of a probe refusal in `entry["refused"]` equals FROZEN_NAMES[0] (read from the constant, not a literal).
    Red today: no FROZEN_NAMES (and, behind it, no `probe` keyword)."""
    names = contract.FROZEN_NAMES

    def result(setup, seed, swap):          # inert on every play: the knob never moves the row
        return _fr("side0" if setup.unit_types["enemy"] <= 24 else "side1", setup.unit_types["enemy"])

    entry = sweep.run_family("range_up", tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p1",),
                             fight_fn=ScriptedFight(result_of=result), caps=CAPS, probe=True)
    reasons = [r["reason"] for r in entry["refused"]]
    assert reasons and set(reasons) == {names[0]}


def test_the_unavailable_family_is_read_from_the_frozen_names(tmp_path):
    """The family name the sweep marks unavailable is FROZEN_NAMES[1]: `skip_reason`, `run_family` and the summary's `unavailable` key
    all answer to that entry. Red today: no FROZEN_NAMES."""
    family = contract.FROZEN_NAMES[1]
    reason = sweep.skip_reason(family, CAPS)
    assert reason and "FINDING-lab-d6" in reason
    entry = sweep.run_family(family, tmp_path / "one", builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p",),
                             fight_fn=ScriptedFight(be_of=lambda s: 20), caps=CAPS)
    assert entry["skipped"] == reason
    summary = sweep.run(list(sweep.FAMILY_ORDER), tmp_path / "all", builds=fake_builds(), layouts={"A": {}}, plays=("p",),
                        fight_fn=ScriptedFight(be_of=lambda s: 20), caps=CAPS)
    assert list(summary["unavailable"]) == [family]


# ---- Q4 (Architect, 2026-10-20, implementation; Westley may veto): the probe's names are frozen too ----------------------------------------

PROBE_NAMES = ("survey", "checked", "seeds", "probed")
REFUSED_KEYS = {"family", "play", "layout", "role", "reason", "checked", "seeds"}      # the frozen shape of an `inert_knob` refusal
PROBED_KEYS = {"family", "play", "layout", "first_differing", "line"}                   # the frozen shape of a `probed` record


@pytest.mark.parametrize("name", PROBE_NAMES)
def test_the_probe_names_are_frozen(name):
    """contract.FROZEN_NAMES gains `survey` (probe.survey), `checked` and `seeds` (the refused entry's keys) and `probed` (the entry and
    summary key): membership only, no length, and the first two positions stay. Red today: not in the tuple."""
    assert name in contract.FROZEN_NAMES
    assert contract.FROZEN_NAMES[:2] == ("inert_knob", "category")


def test_the_refused_entry_and_the_probed_record_have_the_frozen_keys(tmp_path):
    """The `inert_knob` entry's keys are exactly REFUSED_KEYS, the `probed` record's exactly PROBED_KEYS, and the names in them that are
    FROZEN_NAMES come from the constant. Red today: no `checked`/`seeds`, no `probed`."""
    def result(setup, seed, swap):
        return _fr("side0" if setup.unit_types["enemy"] <= 24 else "side1", setup.unit_types["enemy"])

    entry = sweep.run_family("range_up", tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p1",),
                             fight_fn=ScriptedFight(result_of=result), caps=CAPS, probe=True)
    assert [set(r) for r in entry["refused"]] == [REFUSED_KEYS]
    assert [set(r) for r in entry["probed"]] == [PROBED_KEYS]
    assert {"checked", "seeds", "probed"} <= set(contract.FROZEN_NAMES) and entry["refused"][0]["reason"] == contract.FROZEN_NAMES[0]
