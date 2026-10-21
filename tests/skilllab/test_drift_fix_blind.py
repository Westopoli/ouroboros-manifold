# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 items 1 and 5 (Architect, 2026-10-19): a fight whose survivors cannot see each other
# at the cap is a FINDING row (blind post), not a cap defect of the lab; decision 23 now reads "zero caps outside control_* that are not blind-post findings"
"""LAB-REV2-FIX round 2: blind caps are findings, counted apart from the cap defects.

INTERFACE FOR THE BUILDER (frozen here)
  scripts/skilllab/contract.py   FightResult.blind_cap: bool = False   (last field, after `reengage`)
    True iff the fight ended by the cap (outcome "cap") AND, at the cap tick (after engine step Setup.max_ticks), no living unit of
    either side sees any living enemy: engine.visible_enemies(w, side, living enemy ids) is empty for BOTH sides. False for every
    other end (elimination, draw) and for a cap in which at least one side sees at least one enemy. Read only on a cap. It is NOT a
    rows.fight_row fixed column (fight_row is unchanged: the tree's golden hashes of the controls stay as they are).
  scripts/skilllab/sweep.py
    label column `blind_post` (int 0/1 = int(result.blind_cap)) on EVERY row sweep writes (grid rows, control rows, smoke vision rows and
      smoke control rows), passed as a label straight AFTER baseline_no_fit and before family, at every fight_row call in sweep.py, so
      the key order of all calls is identical and the CSV header reads ... baseline_no_fit, blind_post, family ... (the earlier
      header-order defect: a label that first appears in a later row's dict lands at the end of the header).
    _defects(rows) -> {"cap_rows": caps outside control_* kinds that are NOT blind, "blind_post_rows": caps outside control_* kinds that
      ARE blind, "draw_rows": draws (all kinds, as before), "cells": distinct cells holding a draw or a non-blind non-control cap}.
      READING (question Q-FIX2-1): a blind-post cap is a finding and does not make its cell a defect cell.
    run_family's entry["defects"] and run_smoke's summary["defects"] carry the four keys.
Existing tests that pinned the three-key dict are updated (ledger TD-LAB-REV2-FIX-blind-keys)."""
import csv
import dataclasses
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_reengage import ReengageFakeEngine  # noqa: E402
from fakes_scans import _fr, fake_builds  # noqa: E402
from scripts.skilllab import contract, rows as rows_mod, sweep  # noqa: E402
from scripts.skilllab.contract import FightResult  # noqa: E402
from test_reengage import G, N, kill, run as fight_run  # noqa: E402
from test_sweep import World, _smoke, caps, control_builds, read  # noqa: E402
from test_sweep import run as sweep_run  # noqa: E402

CAP = 30


# ---------------------------------------------------------------------------------------------------------- the field

def test_blind_cap_is_a_bool_field_defaulting_to_false():
    fields = {f.name: f for f in dataclasses.fields(FightResult)}
    assert "blind_cap" in fields, "FightResult.blind_cap is not defined"
    assert fields["blind_cap"].default is False
    assert fields["blind_cap"].type in (bool, "bool")


# ---------------------------------------------------------------------------------------------------------- fight(): when a cap is blind

@pytest.mark.usefixtures("seam")
class TestFightBlindCap:
    def test_a_cap_where_nobody_sees_anybody_is_blind(self):
        res, _ = fight_run([G(0), G(1)], cap=CAP, fake=ReengageFakeEngine(visible_fn=lambda f, side, e: False))
        assert res.outcome == "cap" and res.blind_cap is True

    def test_a_cap_where_everybody_sees_everybody_is_not_blind(self):
        """Negative control for the whole detector."""
        res, _ = fight_run([G(0), G(1)], cap=CAP)
        assert res.outcome == "cap" and res.blind_cap is False

    @pytest.mark.parametrize("seer", (0, 1))
    def test_a_cap_where_one_side_sees_one_enemy_is_not_blind(self, seer):
        res, _ = fight_run([G(0), G(1)], cap=CAP, fake=ReengageFakeEngine(visible_fn=lambda f, side, e: side == seer))
        assert res.outcome == "cap" and res.blind_cap is False

    def test_it_is_the_sight_at_the_cap_tick_that_counts(self):
        """Sight that ends before the cap tick: blind. Sight that begins at the cap tick: not blind (the step count reads CAP then)."""
        gone, _ = fight_run([G(0), G(1)], cap=CAP, fake=ReengageFakeEngine(visible_fn=lambda f, side, e: f.step_count < CAP - 1))
        back, _ = fight_run([G(0), G(1)], cap=CAP, fake=ReengageFakeEngine(visible_fn=lambda f, side, e: f.step_count >= CAP))
        assert gone.blind_cap is True and back.blind_cap is False

    def test_an_elimination_is_never_blind_whatever_sight_says(self):
        res, _ = fight_run([G(0), G(1)], cap=CAP, fake=ReengageFakeEngine(visible_fn=lambda f, side, e: False),
                           script_events={0: [kill(1, 0), kill(1, 1)]})
        assert res.outcome == "side0" and res.blind_cap is False

    def test_a_draw_is_never_blind(self):
        res, _ = fight_run([G(0), G(1)], cap=CAP, fake=ReengageFakeEngine(visible_fn=lambda f, side, e: False),
                           script_events={0: [kill(0, 0), kill(0, 1), kill(1, 0), kill(1, 1)]})
        assert res.outcome == "draw" and res.blind_cap is False


# ---------------------------------------------------------------------------------------------------------- sweep: worlds with blind caps

def _is_play_cell(setup):
    return (setup.unit_types["_role"] == "play" and setup.unit_types["enemy"] == sweep.ENEMY_FROM and setup.max_ticks != sweep.CONTROL_MAX_TICKS
            and setup.unit_types["_play"] not in ("mirror", "numbers", "planted"))


class BlindWorld(World):
    """test_sweep.World, plus: in the smallest cell of every play scan, seed 0 unswapped is a BLIND cap; seed 1 unswapped is
    `seed1` ("draw", "cap" (not blind) or None for the world's own result). With control_blind, every cap of a control_* kind is blind too."""

    def __init__(self, seed1=None, control_blind=False, **kw):
        super().__init__(**kw)
        self.seed1, self.control_blind = seed1, control_blind

    def __call__(self, setup, seed, swap):
        out = super().__call__(setup, seed, swap)
        if _is_play_cell(setup) and not swap:
            if seed == 0:
                return dataclasses.replace(_fr("cap", setup.unit_types["enemy"]), blind_cap=True)
            if seed == 1 and self.seed1:
                return _fr(self.seed1, setup.unit_types["enemy"])
        if self.control_blind and out.outcome == "cap" and setup.max_ticks == sweep.CONTROL_MAX_TICKS:
            return dataclasses.replace(out, blind_cap=True)
        return out


def defects_of(rows):
    """The pinned definition of entry["defects"], recounted from the CSV rows (this file's header)."""
    cell = lambda r: (r["play"], r["layout"], r["kind"], r["knob_value"], r["baseline"], r["enemy_heads"])
    live = lambda r: not r["kind"].startswith("control_")
    blind = lambda r: r["outcome"] == "cap" and r["blind_post"] == "1"
    bad = [r for r in rows if live(r) and (r["outcome"] == "draw" or (r["outcome"] == "cap" and not blind(r)))]
    return {"cap_rows": sum(r["outcome"] == "cap" for r in bad), "blind_post_rows": sum(live(r) and blind(r) for r in rows),
            "draw_rows": sum(r["outcome"] == "draw" for r in rows), "cells": len({cell(r) for r in bad}),
            "no_reach_stall_rows": sum(live(r) and r.get("verdict") == "no_reach_stall" for r in rows),        # LAB-REV3-C
            "decided_one_way_reach_rows": sum(live(r) and r.get("verdict") == "decided_one_way_reach" for r in rows)}


def test_blind_caps_are_counted_apart_from_cap_defects_in_a_sweep(tmp_path):
    entry, _ = sweep_run(tmp_path, "damage_up", world=BlindWorld(seed1="draw"))
    rows = read(tmp_path, "damage_up")
    blind = [r for r in rows if r["blind_post"] == "1"]
    assert blind and all(r["outcome"] == "cap" and r["kind"] == "grid" for r in blind)          # the detector's input is really there
    assert {r["blind_post"] for r in rows} == {"0", "1"}
    assert entry["defects"] == defects_of(rows)
    assert entry["defects"]["cap_rows"] == 0 and entry["defects"]["blind_post_rows"] == len(blind) > 0
    assert entry["defects"]["draw_rows"] > 0 and entry["defects"]["cells"] > 0          # the draws in the same cells stay defects


def test_a_blind_cap_alone_makes_no_defect_cell_and_no_cap_defect(tmp_path):
    """READING Q-FIX2-1: a blind-post cap is a finding; a cell holding nothing else is not a defect cell."""
    entry, _ = sweep_run(tmp_path, "damage_up", world=BlindWorld())
    rows = read(tmp_path, "damage_up")
    assert entry["defects"] == defects_of(rows) == {"cap_rows": 0, "blind_post_rows": entry["defects"]["blind_post_rows"], "draw_rows": 0, "cells": 0,
                                                       "no_reach_stall_rows": 0, "decided_one_way_reach_rows": 0}
    assert entry["defects"]["blind_post_rows"] > 0


def test_a_plain_cap_is_still_a_cap_defect_beside_a_blind_one(tmp_path):
    """Positive control: the same cell holds a blind cap (seed 0) and a plain cap (seed 1): both are counted, each in its own key."""
    entry, _ = sweep_run(tmp_path, "damage_up", world=BlindWorld(seed1="cap"))
    rows = read(tmp_path, "damage_up")
    d = entry["defects"]
    assert d == defects_of(rows) and d["cap_rows"] > 0 and d["blind_post_rows"] > 0 and d["cap_rows"] == d["blind_post_rows"] and d["cells"] == d["cap_rows"]


def test_a_blind_cap_in_a_control_kind_is_neither_counted_nor_hidden(tmp_path):
    """The vision-zero control caps by design; with its caps blind the row carries blind_post 1 and the defect counts stay zero."""
    class W(World):
        def __call__(self, setup, seed, swap):
            out = super().__call__(setup, seed, swap)
            return dataclasses.replace(out, blind_cap=True) if out.outcome == "cap" and setup.max_ticks == sweep.CONTROL_MAX_TICKS else out
    entry, _ = sweep_run(tmp_path, "vision", world=W())
    rows = read(tmp_path, "vision")
    controls = [r for r in rows if r["kind"].startswith("control_") and r["outcome"] == "cap"]
    assert controls and {r["blind_post"] for r in controls} == {"1"}
    assert entry["defects"] == defects_of(rows) and entry["defects"]["cap_rows"] == 0 and entry["defects"]["blind_post_rows"] == 0


def test_smoke_counts_blind_posts_apart_and_asserts_no_other_cap(tmp_path):
    """Decision 23 as amended: zero caps outside control_* that are not blind-post findings; the blind rows are listed in their own key."""
    summary, _, rows = _smoke(tmp_path, world=BlindWorld(), control_builds=control_builds())
    noncontrol_caps = [r for r in rows if r["outcome"] == "cap" and not r["kind"].startswith("control_")]
    assert noncontrol_caps and {r["blind_post"] for r in noncontrol_caps} == {"1"}
    assert summary["defects"] == defects_of(rows) and summary["defects"]["cap_rows"] == 0 and summary["defects"]["blind_post_rows"] == 6
    assert json.loads((tmp_path / "smoke_summary.json").read_text())["defects"] == summary["defects"]
    assert {r["blind_post"] for r in rows if r["outcome"] != "cap"} == {"0"}


# ---------------------------------------------------------------------------------------------------------- the CSV label and its place

def test_the_family_csv_header_has_blind_post_straight_after_baseline_no_fit(tmp_path):
    sweep_run(tmp_path, "damage_up", world=BlindWorld())
    with open(tmp_path / "sweep_damage_up.csv", newline="") as fh:
        header = next(csv.reader(fh))
    assert header.count("blind_post") == 1 and header.index("blind_post") == header.index("baseline_no_fit") + 1


def test_the_smoke_csv_header_has_blind_post_straight_after_baseline_no_fit(tmp_path):
    _smoke(tmp_path, world=BlindWorld(), control_builds=control_builds())
    with open(tmp_path / "smoke.csv", newline="") as fh:
        header = next(csv.reader(fh))
    assert header.count("blind_post") == 1 and header.index("blind_post") == header.index("baseline_no_fit") + 1


def test_the_smoke_csv_header_is_right_when_the_control_rows_alone_define_it(tmp_path):
    """Audit of 32039a0f item 4: the header is the union of the rows' keys in first-appearance order, so a label placed wrongly at the smoke-control
    call site only shows when no grid row comes first. Both vision plays refused: the only rows are the three controls', and blind_post must still
    follow baseline_no_fit (the permutation of the family test, without the spy)."""
    refuse = {(p, "play"): "no_reach" for p in sweep.PLAYS_BY_FAMILY["vision"]}
    sweep.run_smoke(tmp_path, workers=1, builds=fake_builds(refuse=refuse), fight_fn=BlindWorld(), control_builds=control_builds())
    with open(tmp_path / "smoke.csv", newline="") as fh:
        reader = csv.reader(fh)
        header, body = next(reader), list(reader)
    assert body and {row[header.index("family")] for row in body} == {"controls"}              # fixture: control rows alone
    assert header.count("blind_post") == 1 and header.index("blind_post") == header.index("baseline_no_fit") + 1


def test_every_fight_row_call_in_sweep_passes_the_labels_in_the_same_order(tmp_path, monkeypatch):
    """Grid rows (_scan_rows), control rows (_control_rows) and the smoke's control rows must use the same key order, so a label can
    never first appear late in a later row's dict. Recorded at every rows.fight_row call of a family run and of a smoke run."""
    seen = []
    real = rows_mod.fight_row
    named = {"knob", "knob_value", "baseline", "ceiling_hit", "prefight"}

    def spy(result, *a, **kw):
        labels = tuple(k for k in kw if k not in named)
        if labels:                 # the controls' identical-rows check calls fight_row(result) bare
            seen.append(labels)
        return real(result, *a, **kw)
    monkeypatch.setattr(rows_mod, "fight_row", spy)
    sweep_run(tmp_path / "f", "damage_up", world=BlindWorld())
    n_family = len(seen)
    _smoke(tmp_path / "s", world=BlindWorld(), control_builds=control_builds())
    assert n_family > 0 and len(seen) > n_family
    assert len(set(seen)) == 1, sorted(set(seen))
    order = seen[0]
    assert order.index("blind_post") == order.index("baseline_no_fit") + 1


# ---------------------------------------------------------------------------------------------------------- a baseline refused blind_post (the generic path)

def test_a_baseline_refused_blind_post_is_listed_and_the_play_still_runs(tmp_path):
    """Control, green on the tree: sweep treats the new refusal word like no_reach and unroutable (listed with its role, left out,
    the play and the other baselines run). Whether a pre-flight can say it: question Q-FIX2-2 in the report."""
    entry, _ = sweep_run(tmp_path, "range_up", builds=fake_builds(refuse={("p2", "naive_defender"): "blind_post"}))
    assert {"family": "range_up", "play": "p2", "layout": "A", "role": "naive_defender", "reason": "blind_post"} in entry["refused"]
    rows = read(tmp_path, "range_up")
    assert "naive_defender" not in {r["baseline"] for r in rows} and "none" in {r["baseline"] for r in rows}
