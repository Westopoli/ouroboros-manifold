# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2: "inert at 16 heads, bites from 32" is a finding); Architect ruling 2026-10-20 (Q3); piece LAB-REV3-A
"""LAB-REV3-A, T2 (Q3): the probe's per-point record reaches the batch summary and the artifact, so the page can say where a knob starts
to matter. Fast, fakes only. The probe itself is tests/skilllab/test_rev3_a_probe.py.

BUILDER CONTRACT (DRAFT names and markup, the Architect may veto):
  sweep.run_family(..., probe=True)  entry["probed"] = [record, ...], one per (family, play, layout) probed, refused or not, in the order
      the (layout, play) loops visit them; the key is absent or empty when probe is off or the family is skipped. A record is
          {"family": str, "play": str, "layout": str, "first_differing": {"heads": int, "seed": int} or None, "line": str}
      first_differing is the first differing point in the survey's own order (headcount ascending, then seed), None when no row differed.
      line, from that point (h, s):
          None                                  -> "inert at every point"          (the family is refused there)
          h above the smallest probed headcount -> f"inert below {h} heads, bites from {h} seed {s}"
          h the smallest probed headcount       -> f"bites at every point from {h} heads seed {s}"      (DRAFT wording)
  sweep.run(families, ..., probe=True)  summary["probed"] = every family's records, in summary["order"] family order, then each entry's order;
      present when the probe is on (an empty list when nothing was probed); sweep_summary.json carries it. A family entry without a
      "probed" key adds nothing (the stand-in entries of tests/skilllab/test_rev3_a_batch.py have none).
  report.artifact(summary, ...)  for each record of summary["probed"] (absent: none), in list order, ONE
          <p class="probed" data-family data-play data-layout>LINE</p>
      as the LAST element children of <section id="findings"> (after the cut-scan, refused and shifted lists; the artifact has no
      per-family section, findings is where the refused-baseline lines live). The text is the record's `line`, nothing else. No `probed`
      in the summary: no such paragraph.
Red today: run_family has no `probed`, sweep.run's summary has none, the artifact prints none."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, fake_builds  # noqa: E402
from scripts.skilllab import scan, sweep  # noqa: E402
from test_report import _artifact_inputs, _page, _sec, _tree  # noqa: E402
from test_rev3_a_probe import CAPS, COARSE, sensitive_plays  # noqa: E402


def run(tmp_path, plays, result_of, family="range_up", **kw):
    return sweep.run_family(family, tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=plays,
                            fight_fn=ScriptedFight(result_of=result_of), caps=CAPS, **kw)


def rec(play, first, line, family="range_up", layout="A"):
    return {"family": family, "play": play, "layout": layout, "first_differing": first, "line": line}


def test_positive_control_the_coarse_list_is_what_the_sweep_scans_first():
    """Green on the tip: COARSE (8..48 by scan.COARSE_STEP) is the first pass of scan.scan, so the probe tests derive from the real constant."""
    assert COARSE == sorted(set(range(sweep.ENEMY_FROM, sweep.ENEMY_TO + 1, scan.COARSE_STEP)) | {sweep.ENEMY_TO})


def test_t2_an_inert_play_has_a_record_saying_inert_at_every_point(tmp_path):
    """T2 (Q3): the refused play still has a record, first_differing None. Red today: no `probed`."""
    entry = run(tmp_path, ("p1",), sensitive_plays(), probe=True)
    assert entry["probed"] == [rec("p1", None, "inert at every point")]


def test_t2_a_play_that_bites_from_32_heads_says_inert_below_32_bites_from_32_seed_0(tmp_path):
    """T2 (Q3, the regression): silent at 8, 16, 24; the first differing point is 32 heads seed 0."""
    entry = run(tmp_path, ("p1",), sensitive_plays("p1", heads=(32, 40, 48)), probe=True)
    assert entry["probed"] == [rec("p1", {"heads": 32, "seed": 0}, "inert below 32 heads, bites from 32 seed 0")]


def test_t2_the_first_differing_point_is_headcount_ascending_then_seed(tmp_path):
    """T2 (Q3): a fake that reacts at 24 heads on seed 1 only: first_differing is (24, 1), the line names both."""
    entry = run(tmp_path, ("p1",), sensitive_plays("p1", heads=(24,), seeds=(1,)), probe=True)
    assert entry["probed"] == [rec("p1", {"heads": 24, "seed": 1}, "inert below 24 heads, bites from 24 seed 1")]


def test_t2_a_play_that_bites_at_every_point_says_so_from_the_smallest_headcount(tmp_path):
    """T2 (Q3, DRAFT wording): the first differing point is the smallest headcount (8, seed 0)."""
    entry = run(tmp_path, ("p1",), sensitive_plays("p1"), probe=True)
    assert entry["probed"] == [rec("p1", {"heads": 8, "seed": 0}, "bites at every point from 8 heads seed 0")]


def test_t2_a_knob_that_bites_at_the_smallest_headcount_on_one_seed_only_has_that_point(tmp_path):
    """T2 (Q3): seed 1 only, every headcount: first_differing is (8, 1). The line text is not pinned (a ruling is asked: 'bites at every
    point' would be untrue here, seed 0 is silent at 8 heads)."""
    entry = run(tmp_path, ("p1",), sensitive_plays("p1", seeds=(1,)), probe=True)
    assert [r["first_differing"] for r in entry["probed"]] == [{"heads": 8, "seed": 1}]


def test_t2_every_probed_play_has_a_record_in_visit_order(tmp_path):
    entry = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"), probe=True)
    assert [(r["play"], r["first_differing"]) for r in entry["probed"]] == [("p1", None), ("p2", {"heads": 8, "seed": 0})]


def test_positive_control_without_the_probe_nothing_is_recorded(tmp_path):
    """Green-side control: probe off, no record (the key is absent or empty)."""
    entry = run(tmp_path, ("p1",), sensitive_plays("p1"))
    assert not entry.get("probed")


def test_t2_the_batch_summary_carries_every_families_records_in_order_and_writes_them(tmp_path):
    """T2 (Q3): sweep.run's summary["probed"] is range_up's records then damage_up's (the fake moves on range keys only, so damage_up is
    inert on both plays), and sweep_summary.json has the same list."""
    summary = sweep.run(["range_up", "damage_up"], tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p1", "p2"),
                        fight_fn=ScriptedFight(result_of=sensitive_plays("p2")), caps=CAPS, probe=True)
    want = [rec("p1", None, "inert at every point"), rec("p2", {"heads": 8, "seed": 0}, "bites at every point from 8 heads seed 0"),
            rec("p1", None, "inert at every point", family="damage_up"), rec("p2", None, "inert at every point", family="damage_up")]
    assert summary["probed"] == want
    assert json.loads((tmp_path / "sweep_summary.json").read_text())["probed"] == want


def test_t2_a_summary_without_family_records_still_runs(tmp_path, monkeypatch):
    """Positive control: the stand-in entries of test_rev3_a_batch.py have no `probed` key; the batch runner must not need it."""
    monkeypatch.setattr(sweep, "run_family", lambda name, out_dir, **kw: {"family": name, "skipped": None, "csv": None, "rows": 0})
    summary = sweep.run(["range_up"], tmp_path, builds=fake_builds(), layouts={"A": {}}, probe=True)
    assert summary["probed"] == []


# ---- the artifact -------------------------------------------------------------------------------------------------------------------------

LINES = ["inert at every point", "inert below 32 heads, bites from 32 seed 0", "inert below 16 heads, bites from 16 seed 1"]


def summary_with_probed():
    _, _, summary = _artifact_inputs()
    summary["probed"] = [rec("s3_layer_above", None, LINES[0], layout="192"),
                         rec("s3_types_by_reach", {"heads": 32, "seed": 0}, LINES[1], layout="192"),
                         rec("s3_layer_above", {"heads": 16, "seed": 1}, LINES[2], family="vision", layout="78")]
    return summary


def probed_ps(html):
    sec = _sec(_tree(html), "findings")
    return sec, [p for p in sec.find("p") if "probed" in p.attrs.get("class", "").split()]


def test_t2_the_artifact_prints_each_probed_line_as_a_paragraph_in_findings_in_list_order(tmp_path):
    """T2 (Q3): one <p class="probed"> per record, text exactly the line, data-family/play/layout, list order. Red today: none printed."""
    _, _, html, _ = _page(tmp_path, summary=summary_with_probed())
    sec, ps = probed_ps(html)
    assert [p.text().strip() for p in ps] == LINES
    assert [(p.attrs["data-family"], p.attrs["data-play"], p.attrs["data-layout"]) for p in ps] == [
        ("range_up", "s3_layer_above", "192"), ("range_up", "s3_types_by_reach", "192"), ("vision", "s3_layer_above", "78")]


def test_t2_the_probed_paragraphs_are_the_last_children_of_findings(tmp_path):
    """T2 (Q3): they come after every list the section already has."""
    _, _, html, _ = _page(tmp_path, summary=summary_with_probed())
    sec, ps = probed_ps(html)
    assert len(ps) == 3
    assert sec.elements()[-3:] == ps


def test_positive_control_a_summary_without_probed_prints_no_such_paragraph(tmp_path):
    """Green on the tip: no `probed` key, no paragraph."""
    _, _, html, _ = _page(tmp_path)
    assert probed_ps(html)[1] == []
