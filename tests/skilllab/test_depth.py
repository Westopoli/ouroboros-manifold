# spec: docs/northstar/plans/2026-10-06-layout-search-spec.md rev 2, piece P4 (LAB-SEARCH); sections 1 to 4
"""scripts/skilllab/depth.py and batches.layout_search: the Latin-hypercube draw, the depth score, the csv, summary and pages.

Seam under test: depth.run_layout(values, seed, replicates, scan_fn) calls scan_fn(label, build, replicates) once per
play and returns a ScanResult (break-even = result.beats). Labels are the plays_space.PLAYS names for the seven skilled
plays and the three counters, and "naive" and "naive_line" for the two naive baselines (Rev 4: 12 scans, placed scenes). Fakes return chosen break-evens; no engine.
Open reading, flagged in the report: a skill's B_s is its best (largest) skilled-play break-even (S2 has three plays).
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import batches, depth, maps, plays_space, report, scenes, skills  # noqa: E402
from scripts.skilllab.contract import Block, Terrain  # noqa: E402
from scripts.skilllab.terrain import shift_terrain  # noqa: E402
from tests.skilllab.fakes_scans import cell, fight, scan_of  # noqa: E402

KEYS = ("choke_width_bodies", "detour_ratio", "lane_count", "blocked_layer_top", "cover_density_corridor",
        "start_distance")
VALUES = {"choke_width_bodies": (0, 2, 4, 8), "detour_ratio": (0, 1.5, 3), "lane_count": (0, 1, 2),
          "blocked_layer_top": (0, 2, 4), "cover_density_corridor": (0, 0.1, 0.3), "start_distance": (1400, 2800)}
SKILLS = ("S1", "S2", "S3", "S4", "S5")
SKILLED = [n for n, p in plays_space.PLAYS.items() if n in (
    "s1_hold_choke", "s2_concave", "s2_spread_line", "s2_screen", "s3_types_by_reach", "s4_bait", "s5_vulnerable_away")]
COUNTERS = ["s2_mass_one_end", "s4_do_not_chase", "s1_outrange"]
HAS_COUNTER = {"S1", "S2", "S4"}
FLAT = Terrain(canvas=(4000.0, 4000.0))
WALLED = Terrain(canvas=(4000.0, 4000.0), blocks=(Block(-30.0, -500.0, 30.0, -100.0, 0, 4),))
SLOW = pytest.mark.skipif(os.environ.get("OM_LAB_SLOW") != "1", reason="real fights; set OM_LAB_SLOW=1")


@pytest.fixture(autouse=True)
def counters_s1_s2_s4(monkeypatch):
    monkeypatch.setattr(skills, "has_counter", lambda s: s in HAS_COUNTER)


def fake_scan(table, calls=None):
    """table: label -> break-even or None; every label must be present."""
    def scan_fn(label, build, replicates):
        if calls is not None:
            calls.append((label, build, replicates))
        return scan_of(16, table[label], [cell(8, [fight(), fight()])])
    return scan_fn


def table_all(skilled=10, naive=7, counter=8):
    t = {n: skilled for n in SKILLED}
    t.update({n: counter for n in COUNTERS})
    t["naive"] = naive
    t["naive_line"] = naive      # TD-LAB-twelve-scans
    return t


def values_of(**over):
    base = {"choke_width_bodies": 4, "detour_ratio": 1.5, "lane_count": 1, "blocked_layer_top": 2,
            "cover_density_corridor": 0.1, "start_distance": 1400}
    base.update(over)
    return base


# ---- the score rule (spec section 2) --------------------------------------------------------------------------

def test_score_follows_the_rule_gain_none_and_counter():
    """AC-score-1: S1 gain 3 counter works; S2 gain 2 (== G) counter fails; S3 gain 5 no counter; S4 gain 1; S5 B_s None."""
    skilled = {"S1": 10, "S2": 9, "S3": 12, "S4": 8, "S5": None}
    counters = {"S1": 8, "S2": 9, "S4": 5}
    r = depth.score_layout(skilled, 7, counters)
    assert r["gains"] == {"S1": 3, "S2": 2, "S3": 5, "S4": 1, "S5": None}
    assert r["counter_works"] == {"S1": True, "S2": False, "S3": None, "S4": True, "S5": None}
    assert r["no_gain"] == ["S5"]
    assert r["score"] == 2          # S1 (gain, counter works) and S3 (gain, no counter registered); S2's counter works


def test_score_s3_and_s5_count_on_gain_alone():
    """AC-score-2: no counter registered -> counted when the gain reaches G, and not marked as failed."""
    r = depth.score_layout({"S3": 9, "S5": 9}, 7, {})
    assert r["score"] == 2


def test_score_gain_below_g_never_counts_even_with_counter_working():
    r = depth.score_layout({"S1": 8}, 7, {"S1": 1})
    assert r["gains"]["S1"] == 1 and r["score"] == 0


def test_score_naive_none_is_no_gain():
    r = depth.score_layout({"S1": 10, "S3": 10}, None, {"S1": 5})
    assert r["gains"] == {"S1": None, "S3": None} and r["no_gain"] == ["S1", "S3"] and r["score"] == 0


def test_score_g_is_two_by_default_and_can_be_set():
    assert depth.G == 2
    assert depth.score_layout({"S3": 8}, 7, {}, g=1)["score"] == 1
    assert depth.score_layout({"S3": 8}, 7, {}, g=2)["score"] == 0


def test_score_skill_with_counter_registered_but_not_run_does_not_count():
    """A registered counter whose scan is absent from the dict is not 'works' (no evidence)."""
    assert depth.score_layout({"S1": 12}, 7, {})["score"] == 0


# ---- the Latin-hypercube draw ---------------------------------------------------------------------------------

def test_lhs_seed_7_is_byte_identical_twice():
    a, b = depth.lhs_draw(18, 7), depth.lhs_draw(18, 7)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert json.dumps(depth.lhs_draw(18, 8), sort_keys=True) != json.dumps(a, sort_keys=True)


def test_lhs_covers_every_value_of_every_feature_in_18_layouts():
    draw = depth.lhs_draw(18, 7)
    assert len(draw) == 18
    for k in KEYS:
        assert {d[k] for d in draw} == set(VALUES[k]), k
        assert all(d[k] in VALUES[k] for d in draw)
    assert all(set(d) == set(KEYS) for d in draw)


def test_lhs_values_are_balanced_across_a_draw():
    """Latin-hypercube: each value of a feature appears about n/k times (within 1 of the even share)."""
    n = 24
    draw = depth.lhs_draw(n, 3)
    for k in KEYS:
        for v in VALUES[k]:
            got = sum(1 for d in draw if d[k] == v)
            assert abs(got - n / len(VALUES[k])) <= 1, (k, v, got)


def test_depth_module_uses_no_numpy_and_no_global_random():
    src = (ROOT / "scripts/skilllab/depth.py").read_text()
    assert "numpy" not in src
    assert not re.search(r"\brandom\.(random|randint|uniform|shuffle|choice|sample|seed)\(", src)
    assert "random.Random(" in src


# ---- one layout: 12 scans, rows, seams ----------------------------------------------------------------------

def test_run_layout_makes_twelve_scans_at_three_replicates(monkeypatch):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    calls = []
    depth.run_layout(values_of(), 5, 3, fake_scan(table_all(), calls))
    labels = [c[0] for c in calls]
    assert len(labels) == 12 and sorted(labels) == sorted(SKILLED + COUNTERS + ["naive", "naive_line"])
    assert {c[2] for c in calls} == {3}


def test_run_layout_builds_the_map_from_features_and_passes_it_to_every_build(monkeypatch):
    seen = []

    def lm(features, seed, *a, **k):
        seen.append((features, seed))
        return WALLED
    monkeypatch.setattr(maps, "layout_map", lm)
    asked = []
    real = scenes.placed_scene
    monkeypatch.setattr(scenes, "placed_scene", lambda lay, play, d, *a, **k: (asked.append((play, d)), real(lay, play, d, *a, **k))[1])
    calls = []
    depth.run_layout(values_of(start_distance=2800, choke_width_bodies=8, lane_count=2), 5, 1, fake_scan(table_all(), calls))
    assert len(seen) == 1 and isinstance(seen[0][0], maps.Features) and isinstance(seen[0][1], int)
    f = seen[0][0]
    assert (f.choke_width_bodies, f.lane_count, f.detour_ratio, f.blocked_layer_top, f.cover_density_corridor,
            f.start_distance) == (8, 2, 1.5, 2, 0.1, 2800)
    # TD-LAB-twelve-scans: Rev 4 builds every scan with scenes.placed_scene on the layout, at the layout d (no objective scene)
    assert len(asked) == 12 and {d for _p, d in asked} == {2800} and {p for p, _d in asked} >= {"naive", "naive_line"}
    by = {c[0]: c[1] for c in calls}
    for label in ("naive", "naive_line", "s1_hold_choke"):
        want = real(WALLED, label, 2800, f)(16, False).terrain       # the layout moved as a whole into the canvas
        assert by[label](16, False).terrain == want
        assert by[label](16, False).decided_by_survivors is True


def test_run_layout_scores_from_the_scans(monkeypatch):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    t = table_all(skilled=12, naive=7, counter=8)       # every gain 5; counters work (8 < 12)
    r = depth.run_layout(values_of(), 5, 3, fake_scan(t))
    assert r["score"] == 5 and r["gains"] == {s: 5 for s in SKILLS}
    t2 = table_all(skilled=12, naive=7, counter=12)     # counters do not work: S3, S5 (no counter) still count
    assert depth.run_layout(values_of(), 5, 3, fake_scan(t2))["score"] == 2


def test_run_layout_flags_none_break_even_as_no_gain_in_the_row(monkeypatch):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    t = table_all()
    t["s5_vulnerable_away"] = None
    r = depth.run_layout(values_of(), 5, 3, fake_scan(t))
    assert r["gains"]["S5"] is None and "S5" in r["no_gain"]
    rows = [x for x in r["rows"] if x["play"] == "s5_vulnerable_away"]
    assert rows and all(x["no_gain"] is True and x["break_even"] is None for x in rows)
    other = [x for x in r["rows"] if x["play"] == "s1_hold_choke"]
    assert all(not x.get("no_gain") for x in other)


def test_run_layout_rows_one_per_fight_with_feat_columns_play_variant_break_even(monkeypatch):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    r = depth.run_layout(values_of(), 5, 3, fake_scan(table_all()))
    assert len(r["rows"]) == 12 * 2          # the fake scan returns two fights per scan
    row = next(x for x in r["rows"] if x["play"] == "s4_do_not_chase")
    assert row["variant"] == "counter" and row["break_even"] == 8
    assert {x["variant"] for x in r["rows"]} == {"skilled", "naive", "counter"}
    assert next(x for x in r["rows"] if x["play"] == "naive")["variant"] == "naive"
    for col, want in (("feat_choke_width_bodies", 4), ("feat_lane_count", 1), ("feat_detour_ratio", 1.5),
                      ("feat_blocked_layer_top", 2), ("feat_cover_density_corridor", 0.1), ("feat_start_distance", 1400)):
        assert row[col] == want, col


def test_skill_break_even_is_the_best_skilled_play_of_the_skill():
    """Flagged reading: S2 has three skilled plays; its B_s is the largest. Counters pair with the skill the same way."""
    b = depth.skill_break_evens({"s2_concave": 9, "s2_spread_line": 12, "s2_screen": 10, "s1_hold_choke": 6,
                                 "s3_types_by_reach": None, "s4_bait": 7, "s5_vulnerable_away": 7})
    assert b["S2"] == 12 and b["S1"] == 6 and b["S3"] is None


# ---- the batch: csv, summary, pages ------------------------------------------------------------------------------

@pytest.fixture
def run_small(tmp_path, monkeypatch):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    paths = depth.run(18, 7, 1, tmp_path, replicates=3, scan_fn=fake_scan(table_all(skilled=12)))
    return tmp_path, paths


def test_run_writes_csv_with_one_row_per_fight(run_small):
    out, paths = run_small
    csv_path = Path(next(p for p in paths.values() if str(p).endswith(".csv")))
    with open(csv_path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 18 * 12 * 2
    assert {"play", "variant", "break_even", "feat_choke_width_bodies", "feat_start_distance"} <= set(rows[0])


def test_depth_summary_json_shape(run_small):
    out, _ = run_small
    s = json.loads((out / "depth_summary.json").read_text())
    assert s["G"] == 2 and len(s["layouts"]) == 18
    lay = s["layouts"][0]
    assert set(lay) >= {"features", "gains", "score", "no_gain"} and set(lay["features"]) == set(KEYS)
    assert set(lay["gains"]) == set(SKILLS) and isinstance(lay["score"], int) and 0 <= lay["score"] <= 5
    means = s["feature_means"]
    assert set(means) == set(KEYS)
    assert set(means["choke_width_bodies"]) == {"0", "2", "4", "8"}
    assert set(means["start_distance"]) == {"1400", "2800"}
    for k in KEYS:
        for v, m in means[k].items():
            mine = [x["score"] for x in s["layouts"] if str(x["features"][k]) == v]
            assert m == pytest.approx(sum(mine) / len(mine))


def test_run_is_byte_identical_twice(tmp_path, monkeypatch):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    for d in ("a", "b"):
        depth.run(6, 7, 1, tmp_path / d, replicates=3, scan_fn=fake_scan(table_all()))
    assert (tmp_path / "a/depth_summary.json").read_bytes() == (tmp_path / "b/depth_summary.json").read_bytes()


# ---- the pages ---------------------------------------------------------------------------------------------------

def _summary():
    layouts = []
    for i, w in enumerate((0, 2, 4, 8)):
        layouts.append({"index": i, "features": values_of(choke_width_bodies=w), "gains": {s: i + 1 for s in SKILLS},
                        "no_gain": [], "score": i})
    return {"G": 2, "layouts": layouts, "feature_means": {
        k: {str(v): 1.0 for v in VALUES[k]} for k in KEYS}}


def test_chart_1_has_six_panels():
    svg = depth.chart_score_by_feature(_summary())
    assert svg.lstrip().startswith("<svg") and svg.count('class="panel"') == 6


def test_chart_2_has_one_line_per_skill():
    svg = depth.chart_gain_by_choke(_summary())
    assert svg.lstrip().startswith("<svg") and svg.count('class="line"') == 5
    for s in SKILLS:
        assert s in svg


def test_pillars_table_has_one_row_per_pillar_in_the_map_design_readme():
    readme = (ROOT / "docs/northstar/research/map_design/README.md").read_text()
    pillars = re.findall(r"^### (P\d+)\. (.+)$", readme, flags=re.M)
    assert len(pillars) == 8
    html = depth.pillars_table(_summary())
    assert html.count("<table") == 1
    body = html.split("</thead>")[-1] if "</thead>" in html else html
    assert body.count("<tr") == len(pillars) + (0 if "</thead>" in html else 1)
    for pid, title in pillars:
        assert pid in html and title.split(",")[0].split(" (")[0] in html


def test_page_joins_charts_and_table_in_the_lab_style(run_small):
    out, paths = run_small
    page = Path(next(p for p in paths.values() if str(p).endswith(".html"))).read_text()
    assert report.CSS in page and page.count('class="panel"') == 6 and "<table" in page
    assert "no counter registered" in page          # S3 and S5 are marked (spec section 2)


# ---- wiring ---------------------------------------------------------------------------------------------------------

def test_batches_names_contains_layout_search():
    assert "layout_search" in batches.NAMES


def test_cli_batch_layout_search_passes_layouts_default_200_and_workers(monkeypatch, tmp_path):
    from scripts.skilllab import __main__ as cli
    got = []
    monkeypatch.setattr(batches, "layout_search", lambda n_layouts, seed, workers, *a, **k: got.append((n_layouts, workers)) or {})
    assert cli.main(["batch", "layout_search", "--out", str(tmp_path)]) == 0
    assert cli.main(["batch", "layout_search", "--layouts", "5", "--workers", "3", "--out", str(tmp_path)]) == 0
    assert got == [(200, 1), (5, 3)]


def test_batches_layout_search_delegates_to_depth(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(depth, "run", lambda n, seed, workers, out_dir, **k: seen.append((n, seed, workers)) or {})
    batches.layout_search(4, 9, 2, tmp_path)
    assert seen == [(4, 9, 2)]


# ---- one real smoke ------------------------------------------------------------------------------------------------

@SLOW
def test_real_smoke_two_layouts_one_replicate_four_workers(tmp_path):
    paths = batches.layout_search(2, 7, 4, tmp_path, replicates=1)
    csv_path = next(Path(p) for p in paths.values() if str(p).endswith(".csv"))
    assert csv_path.exists() and csv_path.stat().st_size > 0
    assert (tmp_path / "depth_summary.json").exists()


# ---- TD-LAB-twelve-scans: the naive scenes are placed scenes on the layout (Rev 4) ----

@pytest.mark.parametrize("label", ["naive", "naive_line"])
def test_run_layout_naive_build_is_a_placed_scene_inside_the_canvas(monkeypatch, label):
    monkeypatch.setattr(maps, "layout_map", lambda f, s, *a, **k: FLAT)
    calls = []
    depth.run_layout(values_of(start_distance=2800), 5, 1, fake_scan(table_all(), calls))
    setup = {c[0]: c[1] for c in calls}[label](16, False)
    cw, ch = FLAT.canvas
    g0, g1 = [next(g for g in setup.groups if g.side == s) for s in (0, 1)]
    for x, y in [(g.x, g.y) for g in setup.groups] + [setup.hold_anchor]:
        assert 0 <= x <= cw and 0 <= y <= ch, (x, y)
    assert g1.x - g0.x == pytest.approx(2800) and g0.y == g1.y       # the naive defender is side 1, at the choke
    assert setup.decided_by_survivors is True and setup.defender_side == 1
    assert setup.hold_anchor == pytest.approx((g1.x, g1.y), abs=200.0)
