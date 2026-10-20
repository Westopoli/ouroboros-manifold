# spec: docs/northstar/plans/2026-10-19-skill-lab-rev3-plan.md (requirement R6, test T2: "inert at 16 heads, bites from 32" is a finding); Architect rulings 2026-10-20 (Q1 to Q4, R1 to R4); piece LAB-REV3-A
"""LAB-REV3-A, T2: the probe's per-point record reaches the batch summary and the artifact, so the page can say where a knob starts to
matter; the batch caches the base rows across families; the probe leaves arc, cone and pre-flight refusals alone. Fast, fakes only. The
probe itself is tests/skilllab/test_rev3_a_probe.py.

BUILDER CONTRACT (DRAFT names and markup, the Architect may veto):
  sweep.run_family(..., probe=True, base_cache=None)  entry["probed"] = [record, ...], one per (family, play, layout) probed, refused or
      not, in the order the (layout, play) loops visit them; the key is absent or empty when probe is off, when the family is skipped,
      for arc and cone (no OM_TP_* setting, never probed), and for a (play, layout) the pre-flight refused first (no_reach, no_fit,
      ...: not probed, no probe fight, no record). A record is
          {"family": str, "play": str, "layout": str, "first_differing": {"heads": int, "seed": int} or None, "line": str,
           "base_cached": bool}
      first_differing is the first differing point in the survey's own order (headcount ascending, then seed), None when no row differed.
      base_cached is True when every base row of this survey came from the cache (the base fights were not repeated), else False.
      line (Architect ruling R2): with (h, s) the first differing point and `silent` the list of (heads, seed) points, headcount at or
      below h, that did NOT differ (ascending; so a point of the same headcount with a lower seed counts):
          no differing point   -> "inert at every point"                                   (the family is refused there)
          silent == []         -> f"bites from {h} heads seed {s}"
          otherwise            -> f"bites from {h} heads seed {s}; silent at {silent}"     (the list's repr, tuples (heads, seed))
      so the line is true by construction. e.g. "bites from 8 heads seed 1; silent at [(8, 0)]".
      The cache (run-level, Architect ruling R1): one dict, created by sweep.run, passed to every run_family as `base_cache`; its key is
      (play, layout, tuple(sorted(base settings.items()))) with the survey's base settings, so range_up and sign_flip (the same four
      OM_TP_RANGE_* keys at BASES) share the base fights of a (play, layout). run_family called alone makes a private one.
  sweep.run(families, ..., probe=True)  summary["probed"] = every family's records, in summary["order"] family order, then each entry's order;
      present when the probe is on (an empty list when nothing was probed); sweep_summary.json carries it. A family entry without a
      "probed" key adds nothing (the stand-in entries of tests/skilllab/test_rev3_a_batch.py have none). The unmentioned `probe` default of
      sweep.run is not tested (it stays False, the Architect's ruling).
  report.artifact(summary, ...)  for each record of summary["probed"] (absent: none), in list order, ONE
          <p class="probed" data-family data-play data-layout>LINE</p>
      as the LAST element children of <section id="findings"> (after the cut-scan, refused-baseline and shifted-post lists; the
      artifact has no per-family section, findings is where the refused-baseline lines live). The text is the record's `line`, nothing
      else. No `probed` in the summary: no such paragraph. NOTE for the ruler: test_drift_fix_refused_lines.py:54, test_report.py:1628 and
      test_drift_fix_shifted_posts.py:200 claim the ul 'stays the last element child'; on a page that also has `probed` records that is
      untrue (they hold on pages without them, which is all their fixtures).
Red today: run_family has no `probed` or `base_cache`, sweep.run's summary has none, the artifact prints none."""
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, fake_builds  # noqa: E402
from scripts.skilllab import scan, sweep  # noqa: E402
from test_report import _artifact_inputs, _page, _sec, _tree  # noqa: E402
from test_rev3_a_probe import AT, BASE, CAPS, COARSE, N_CACHED, N_FIGHTS, SEEDS, reacts, run, sensitive_plays  # noqa: E402


def expected_line(differing):
    """Architect ruling R2, written out: the line for the set of (heads, seed) points that differed."""
    if not differing:
        return "inert at every point"
    h, s = min(differing)
    silent = [(x, y) for x in COARSE for y in SEEDS if x <= h and (x, y) not in differing]
    return "bites from %d heads seed %d" % (h, s) + ("; silent at %s" % silent if silent else "")


def rec(play, differing, family="range_up", layout="A", base_cached=False):
    first = min(differing) if differing else None
    return {"family": family, "play": play, "layout": layout, "first_differing": None if first is None else {"heads": first[0], "seed": first[1]},
            "line": expected_line(differing), "base_cached": base_cached}


def points(pred):
    return {(h, s) for h in COARSE for s in SEEDS if pred(h, s)}


def test_positive_control_the_coarse_list_is_what_the_sweep_scans_first():
    """Green on the tip: COARSE is the first pass of scan.scan (8..48 by scan.COARSE_STEP), the one place the literal list is written."""
    assert COARSE == [8, 16, 24, 32, 40, 48] == sorted(set(range(sweep.ENEMY_FROM, sweep.ENEMY_TO + 1, scan.COARSE_STEP)) | {sweep.ENEMY_TO})


def test_positive_control_the_line_rule_reads_the_rulings_own_examples():
    """Green on the tip: expected_line reproduces the Architect's example texts, so the pins below are the ruling's and not the helper's."""
    assert expected_line(set()) == "inert at every point"
    assert expected_line(points(lambda h, s: True)) == "bites from 8 heads seed 0"
    assert expected_line(points(lambda h, s: (h, s) != (8, 0))) == "bites from 8 heads seed 1; silent at [(8, 0)]"


# ---- the record: the line is true by construction (ruling R2) ----------------------------------------------------------------------------

def test_t2_an_inert_play_has_a_record_saying_inert_at_every_point(tmp_path):
    """T2: the refused play still has a record, first_differing None. Red today: no `probed`."""
    entry, _ = run(tmp_path, ("p1",), sensitive_plays(), probe=True)
    assert entry["probed"] == [rec("p1", set())]
    assert entry["probed"][0]["line"] == "inert at every point" and entry["probed"][0]["first_differing"] is None


CASES = {
    "every point": lambda h, s: True,
    "from a mid headcount, both seeds": lambda h, s: h >= AT,
    "the vision shape: all but (smallest headcount, seed 0)": lambda h, s: (h, s) != (COARSE[0], 0),
    "monotonicity: only (smallest headcount, seed 0)": lambda h, s: (h, s) == (COARSE[0], 0),
    "seed 1 only at a mid headcount": lambda h, s: (h, s) == (AT, 1),
    "seed 1 only everywhere": lambda h, s: s == 1,
}


@pytest.mark.parametrize("name", list(CASES))
def test_t2_the_line_and_the_first_differing_point_follow_the_ruling(tmp_path, name):
    """T2 (R2): first_differing is the first differing point, the line names it and every silent point at or below its headcount.
    Red today: no `probed`."""
    differing = points(CASES[name])
    entry, _ = run(tmp_path, ("p1",), reacts(lambda e, sd: (e, sd) in differing, "p1"), probe=True)
    assert entry["probed"] == [rec("p1", differing)]


def test_t2_the_ruling_examples_pin_the_exact_text(tmp_path):
    """T2 (R2): the three shapes, written with the headcounts taken from COARSE (smallest, AT)."""
    lo = COARSE[0]
    cases = [(lambda e, sd: True, "bites from %d heads seed 0" % lo),
             (lambda e, sd: (e, sd) != (lo, 0), "bites from %d heads seed 1; silent at [(%d, 0)]" % (lo, lo)),
             (lambda e, sd: (e, sd) == (lo, 0), "bites from %d heads seed 0; silent at [(%d, 1)]" % (lo, lo)),
             (lambda e, sd: e >= AT, "bites from %d heads seed 0; silent at %s" % (AT, [(h, s) for h in COARSE if h < AT for s in SEEDS]))]
    for i, (pred, line) in enumerate(cases):
        entry, _ = run(tmp_path / str(i), ("p1",), reacts(pred, "p1"), probe=True)
        assert [r["line"] for r in entry["probed"]] == [line]


def test_t2_every_probed_play_has_a_record_in_visit_order_over_two_layouts(tmp_path):
    """T2 (D5): records come in the order the sweep visits (layout, then play): A/p1, A/p2, B/p1, B/p2; refused and not refused alike."""
    entry, _ = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"), layouts={"A": {"id": 1}, "B": {"id": 2}}, probe=True)
    assert [(r["play"], r["layout"], r["first_differing"] is None) for r in entry["probed"]] == [
        ("p1", "A", True), ("p2", "A", False), ("p1", "B", True), ("p2", "B", False)]


def test_positive_control_without_the_probe_nothing_is_recorded(tmp_path):
    """Green-side control: probe off, no record (the key is absent or empty)."""
    entry, _ = run(tmp_path, ("p1",), sensitive_plays("p1"))
    assert not entry.get("probed")


# ---- what is not probed (D5) -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("family", ["arc", "cone"])
def test_t2_arc_and_cone_are_not_probed_and_nothing_changes(tmp_path, family):
    """T2 (D5): arc and cone set no OM_TP_* setting (they act through Setup fields), so with probe=True they get no probe fight, no
    `probed` record and no refusal: the fights are those of the same run with the probe off. Red today only for a builder that probes
    them (no probe module yet: green on the tip, a control)."""
    on, fn_on = run(tmp_path / "on", ("p1",), sensitive_plays(), family=family, probe=True)
    off, fn_off = run(tmp_path / "off", ("p1",), sensitive_plays(), family=family)
    assert on["refused"] == off["refused"] == [] and not on.get("probed")
    assert [c["key"] for c in fn_on.calls] == [c["key"] for c in fn_off.calls] and fn_on.calls


@pytest.mark.parametrize("word", ["no_reach", "no_fit"])
def test_t2_a_play_the_preflight_refused_is_not_probed_and_has_no_record(tmp_path, word):
    """T2 (D5): p1 is refused by the pre-flight (its build's prefight word) before the probe: it keeps that refusal, fights nothing and
    has no record; p2 is probed as usual. Red today: no `probed`."""
    builds = fake_builds(refuse={("p1", "play"): word})
    entry, fight_fn = run(tmp_path, ("p1", "p2"), sensitive_plays("p2"), builds=builds, probe=True)
    assert [(r["play"], r["role"], r["reason"]) for r in entry["refused"]] == [("p1", "play", word)]
    assert [c for c in fight_fn.calls if c["play"] == "p1"] == []
    assert [r["play"] for r in entry["probed"]] == ["p2"]


# ---- the run-level base cache (ruling R1) -------------------------------------------------------------------------------------------------

def test_t2_two_families_with_the_same_base_keys_fight_the_base_once_and_the_second_says_cached(tmp_path):
    """T2 (R1): range_up and sign_flip reset the same four OM_TP_RANGE_* keys to BASES, so on one (play, layout) the base fights are made
    once: N_FIGHTS for the first family, N_CACHED for the second, every base (heads, seed) fought exactly once, and the second family's
    record says base_cached True (the first False). Both are inert (a flat fake) so only probe fights exist. Red today: no `probed`."""
    summary = sweep.run(["range_up", "sign_flip"], tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p1",),
                        fight_fn=(fn := ScriptedFight(result_of=sensitive_plays())), caps=CAPS, probe=True)
    assert [(r["family"], r["base_cached"]) for r in summary["probed"]] == [("range_up", False), ("sign_flip", True)]
    p1 = [c for c in fn.calls if c["play"] == "p1"]
    assert len(p1) == N_FIGHTS + N_CACHED
    bases = Counter((c["enemy"], c["seed"]) for c in p1 if all(c["settings"].get(k) == v for k, v in BASE.items()))
    assert len(bases) == N_CACHED and set(bases.values()) == {1}


def test_t2_a_family_with_other_base_keys_does_not_use_the_cache(tmp_path):
    """T2 (R1): damage_up's base is two other keys (OM_TP_DAMAGE_UP_*) and shares nothing with range_up: its record says base_cached
    False and it costs N_FIGHTS. Red today: no `probed`."""
    summary = sweep.run(["range_up", "damage_up"], tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p1",),
                        fight_fn=(fn := ScriptedFight(result_of=sensitive_plays())), caps=CAPS, probe=True)
    assert [(r["family"], r["base_cached"]) for r in summary["probed"]] == [("range_up", False), ("damage_up", False)]
    assert len([c for c in fn.calls if c["play"] == "p1"]) == 2 * N_FIGHTS


def test_t2_the_batch_runner_hands_one_cache_dict_to_every_family(tmp_path, monkeypatch):
    """T2 (R1): sweep.run passes the same `base_cache` dict object to every run_family call. Red today: no such keyword is passed."""
    seen = []
    monkeypatch.setattr(sweep, "run_family", lambda name, out_dir, **kw: seen.append(kw) or {"family": name, "skipped": None, "csv": None, "rows": 0})
    sweep.run(["range_up", "sign_flip"], tmp_path, builds=fake_builds(), layouts={"A": {}}, probe=True)
    assert len(seen) == 2 and isinstance(seen[0]["base_cache"], dict) and seen[0]["base_cache"] is seen[1]["base_cache"]


# ---- the batch summary ----------------------------------------------------------------------------------------------------------------

def test_t2_the_batch_summary_carries_every_families_records_in_order_and_writes_them(tmp_path):
    """T2: sweep.run's summary["probed"] is range_up's records then damage_up's (the fake moves on range keys only, so damage_up is
    inert on both plays), and sweep_summary.json has the same list."""
    summary = sweep.run(["range_up", "damage_up"], tmp_path, builds=fake_builds(), layouts={"A": {"id": 1}}, plays=("p1", "p2"),
                        fight_fn=ScriptedFight(result_of=sensitive_plays("p2")), caps=CAPS, probe=True)
    every = points(lambda h, s: True)
    want = [rec("p1", set()), rec("p2", every), rec("p1", set(), family="damage_up"), rec("p2", set(), family="damage_up")]
    assert [{k: v for k, v in r.items() if k != "base_cached"} for r in summary["probed"]] == [{k: v for k, v in w.items() if k != "base_cached"} for w in want]
    assert json.loads((tmp_path / "sweep_summary.json").read_text())["probed"] == summary["probed"]


def test_t2_a_summary_without_family_records_still_runs(tmp_path, monkeypatch):
    """Positive control: the stand-in entries of test_rev3_a_batch.py have no `probed` key; the batch runner must not need it."""
    monkeypatch.setattr(sweep, "run_family", lambda name, out_dir, **kw: {"family": name, "skipped": None, "csv": None, "rows": 0})
    summary = sweep.run(["range_up"], tmp_path, builds=fake_builds(), layouts={"A": {}}, probe=True)
    assert summary["probed"] == []


# ---- the artifact -------------------------------------------------------------------------------------------------------------------------

LINES = [expected_line(set()), expected_line(points(lambda h, s: h >= AT)), expected_line(points(lambda h, s: (h, s) != (COARSE[0], 0)))]


def summary_with_probed():
    _, _, summary = _artifact_inputs()
    summary["probed"] = [rec("s3_layer_above", set(), layout="192"),
                         rec("s3_types_by_reach", points(lambda h, s: h >= AT), layout="192"),
                         rec("s3_layer_above", points(lambda h, s: (h, s) != (COARSE[0], 0)), family="vision", layout="78")]
    return summary


def probed_ps(html):
    sec = _sec(_tree(html), "findings")
    return sec, [p for p in sec.find("p") if "probed" in p.attrs.get("class", "").split()]


def test_t2_the_artifact_prints_each_probed_line_as_a_paragraph_in_findings_in_list_order(tmp_path):
    """T2: one <p class="probed"> per record, text exactly the line, data-family/play/layout, list order. Red today: none printed."""
    _, _, html, _ = _page(tmp_path, summary=summary_with_probed())
    sec, ps = probed_ps(html)
    assert [p.text().strip() for p in ps] == LINES
    assert [(p.attrs["data-family"], p.attrs["data-play"], p.attrs["data-layout"]) for p in ps] == [
        ("range_up", "s3_layer_above", "192"), ("range_up", "s3_types_by_reach", "192"), ("vision", "s3_layer_above", "78")]


def test_t2_the_probed_paragraphs_are_the_last_children_of_findings(tmp_path):
    """T2: they come after every list the section already has."""
    _, _, html, _ = _page(tmp_path, summary=summary_with_probed())
    sec, ps = probed_ps(html)
    assert len(ps) == 3
    assert sec.elements()[-3:] == ps


def test_t2_with_refused_baselines_and_shifted_posts_present_the_probed_paragraphs_still_come_last(tmp_path):
    """T2 (D6): the page has a refused-baselines list, a shifted-posts list and the probed paragraphs: lists first (refused, then shifted,
    as their own tests pin), then the three paragraphs as the last children, so no `ul` is the last element child of this page."""
    summary = summary_with_probed()
    summary["families"]["range_up"] = dict(
        summary["families"]["range_up"],
        refused=[{"family": "range_up", "play": "s3_layer_above", "layout": "192", "role": "naive_defender", "reason": "blind_post"}],
        shifted_posts=[{"family": "range_up", "play": "s3_types_by_reach", "layout": "192", "role": "naive_defender", "shift_wu": 12.0}])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, ps = probed_ps(html)
    els = sec.elements()
    classes = [e.attrs.get("class", "") for e in els]
    assert len(ps) == 3 and els[-3:] == ps
    refused_at = next(i for i, c in enumerate(classes) if "refused-baselines" in c.split())
    shifted_at = next(i for i, c in enumerate(classes) if "shifted-posts" in c.split())
    assert refused_at < shifted_at < len(els) - 3


def test_positive_control_a_summary_without_probed_prints_no_such_paragraph(tmp_path):
    """Green on the tip: no `probed` key, no paragraph."""
    _, _, html, _ = _page(tmp_path)
    assert probed_ps(html)[1] == []
