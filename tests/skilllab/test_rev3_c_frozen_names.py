# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (test T2 "Frozen names": "C adds no_reach_stall and decided_one_way_reach"); Architect ruling 2026-10-20 on the names list; piece LAB-REV3-C
"""LAB-REV3-C, the frozen names: contract.FROZEN_NAMES (a tuple of strings, created by piece A as ("inert_knob", "category") and grown by A to six:
"inert_knob", "category", "survey", "checked", "seeds", "probed") gains "no_reach_stall" and "decided_one_way_reach" in this piece, and three more
frozen by the Architect (2026-10-20, after a4d27ae6): "paper_prediction" (the function scenes.paper_prediction), "reach" (the key of the
sweep.run summary header; "none" when no table is given) and "--reach" (the CLI flag of the sweep command, repeatable `--reach TYPE=UP,DOWN`,
values 0 to 2 else refused). Adding is fine; renaming or removing is a contract change. The verdict strings
fight() writes are those entries, read from the constant by the code, so a rename moves code and artifact together or fails here.

If piece A's FROZEN_NAMES is not on the base, the tests fail on the missing names (getattr with a default), not on an import.
BUILDER CONTRACT: both strings are in contract.FROZEN_NAMES after A's two (A's entries keep their positions: these tests pin membership
and A's six positions 0..5, never the length); FightResult.verdict (see test_rev3_c_stall.py) is exactly one of them or None."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_rev3_c_support import DECIDED, STALL, G, kill, run  # noqa: E402
from scripts.skilllab import contract  # noqa: E402

pytestmark = pytest.mark.usefixtures("seam")


def frozen():
    return getattr(contract, "FROZEN_NAMES", ())


def test_both_new_names_are_frozen_names_and_a_keeps_its_two_first():
    """Red today: FROZEN_NAMES is missing on the base (A's piece) or lacks both names."""
    names = frozen()
    assert STALL in names and DECIDED in names, "contract.FROZEN_NAMES = %r" % (names,)
    assert tuple(names[:6]) == ("inert_knob", "category", "survey", "checked", "seeds", "probed")
    assert isinstance(names, tuple) and all(isinstance(n, str) for n in names)


def test_the_stall_verdict_the_fight_writes_is_a_frozen_name():
    """The stall fight's verdict equals the FROZEN_NAMES entry (looked up in the constant, not repeated as a literal)."""
    r, _f = run([G(0, "Vanguard", 2, 0), G(1, "Vanguard", 2, 2)], cap=100)
    entry = next((n for n in frozen() if n == getattr(r, "verdict", None)), None)
    assert entry is not None, "verdict %r is not in FROZEN_NAMES %r (outcome %s, ticks %d)" % (getattr(r, "verdict", None), frozen(), r.outcome, r.ticks)
    assert entry == STALL


def test_the_decided_verdict_the_fight_writes_is_a_frozen_name():
    """The decided fight's verdict equals the FROZEN_NAMES entry."""
    r, _f = run([G(0, "Interceptor", 1, 0), G(1, "Vanguard", 1, 2)], cap=100)
    entry = next((n for n in frozen() if n == getattr(r, "verdict", None)), None)
    assert entry is not None, "verdict %r is not in FROZEN_NAMES %r (outcome %s, ticks %d)" % (getattr(r, "verdict", None), frozen(), r.outcome, r.ticks)
    assert entry == DECIDED


def test_control_an_ordinary_win_has_no_verdict():
    """Green today: a win by elimination carries no verdict (None), so the constant is not consulted for it."""
    r, _f = run([G(0, "Interceptor", 1, 0), G(1, "Raider", 1, 1)], cap=100, events={9: [kill(1, 0)]})
    assert r.outcome == "side0" and getattr(r, "verdict", None) is None


# ---- the three names frozen after a4d27ae6 (Architect 2026-10-20) ---------------------------------------------------------------------

def test_the_paper_reach_and_flag_names_are_frozen():
    """Membership only (not length). Red today: FROZEN_NAMES lacks them (and, on a base before piece A, does not exist)."""
    names = frozen()
    for n in ("paper_prediction", "reach", "--reach"):
        assert n in names, "contract.FROZEN_NAMES = %r lacks %r" % (names, n)


def test_the_paper_prediction_function_is_named_by_the_constant():
    """scenes.<the frozen entry> exists and says "no_reach" for Vanguards two layers apart (the entry is looked up in the constant, then read
    off the module with getattr). Red today: no entry, then no such function."""
    from scripts.skilllab import scenes
    from scripts.skilllab.contract import Setup
    name = next((n for n in frozen() if n == "paper_prediction"), None)
    assert name is not None, "contract.FROZEN_NAMES = %r" % (frozen(),)
    fn = getattr(scenes, name, None)
    assert callable(fn), "scenes has no %s" % name
    assert fn(Setup(groups=(G(0, "Vanguard", 2, 0), G(1, "Vanguard", 2, 2)), unit_types={}, max_ticks=3)) == "no_reach"


def test_the_summary_header_key_is_the_frozen_reach_name(tmp_path, monkeypatch):
    """sweep.run's summary (dict and sweep_summary.json) carries its reach configuration under the frozen entry "reach": "none" without a
    table, a string naming the type with one. Red today: no entry, no key."""
    import json
    from scripts.skilllab import sweep
    monkeypatch.setattr(sweep, "run_family", lambda family, out_dir, **kw: {"family": family, "skipped": None, "csv": None, "rows": 0})
    key = next((n for n in frozen() if n == "reach"), None)
    assert key is not None, "contract.FROZEN_NAMES = %r" % (frozen(),)
    assert sweep.run(["range_up"], tmp_path / "a").get(key) == "none"
    with_table = sweep.run(["range_up"], tmp_path / "b", reach={"Raider": (2, 1)})
    assert "Raider" in with_table.get(key, "")
    assert json.loads((tmp_path / "b" / "sweep_summary.json").read_text(encoding="utf-8"))[key] == with_table[key]


def test_the_cli_flag_is_the_frozen_name_and_repeats(tmp_path, monkeypatch):
    """The sweep command takes the frozen flag string, repeatable, TYPE=UP,DOWN; a value outside 0 to 2 is refused. Red today: no entry,
    then argparse refuses the flag (SystemExit 2)."""
    from scripts.skilllab import __main__ as cli, sweep
    got = []
    monkeypatch.setattr(sweep, "run", lambda families, out_dir, workers=1, **kw: got.append(kw) or {"families": {}})
    flag = next((n for n in frozen() if n == "--reach"), None)
    assert flag is not None, "contract.FROZEN_NAMES = %r" % (frozen(),)
    assert cli.main(["sweep", "damage_up", "--out", str(tmp_path), flag, "Raider=0,1", flag, "Interceptor=2,1"]) == 0
    assert got[0].get("reach") == {"Raider": (0, 1), "Interceptor": (2, 1)}
    with pytest.raises((SystemExit, ValueError)):
        cli.main(["sweep", "damage_up", "--out", str(tmp_path), flag, "Raider=3,1"])
    assert len(got) == 1
