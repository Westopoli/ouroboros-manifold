# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 45 item 1 (D1, Architect 2026-10-19): the blind-post shift is reported as artifact lines
# "naive <role>: post shifted <wu> wu", one per (play, layout, role), and as a `shifted_posts` field in the smoke and sweep summaries; no CSV column
"""LAB-REV2-FIX round 5, D1: where the naive-defender shift goes (sweep.run_family, sweep.run_smoke, report.artifact). Ledger TD-LAB-REV2-FIX5-shifted-posts.

INTERFACE FOR THE BUILDER (frozen here)
  Source: the build's `labels["placement_shift"]` (sweep._naive_side; 0.0 when nothing moved or the build is refused). Nothing else changes in the builds.
  Summary: run_family's entry gets `shifted_posts` (always present, [] when none) and run_smoke's summary gets `shifted_posts` (always present):
      [{"family", "play", "layout", "role", "shift_wu"}, ...]   smoke entries WITHOUT "family"; shift_wu a float (not rounded)
    One entry per (play, layout, role) whose baseline ran (a refused baseline is never listed) with a shift above 0.0. shift_wu is the LARGEST placement_shift the
    build reported over the headcounts the sweep builds for it (the label already means "the largest distance moved"; Q-FIX5-1). Order: the order the sweep meets
    them (layout in the layouts' order, play in run order, role in baseline_roles order). No CSV column: no sweep or smoke CSV column holds "shift".
  Artifact (report.artifact reads summary["families"][family]["shifted_posts"], families in summary["order"], as for `refused`):
    LINE = "naive " + <role without "naive_", "_" as " "> + ": post shifted " + <shift_wu with ONE decimal, "%.1f"> + " wu"      e.g. "naive defender: post shifted 110.4 wu"
    - In <section id="findings">, AFTER the refused-baselines list when there is one: ONE <ul class="shifted-posts"> as the last element child, one
        <li data-shifted-post data-family data-play data-layout data-role data-shift-wu>LINE</li> per entry whose role starts with "naive_"; data-shift-wu is the
        one-decimal text. Order: summary["order"] family order, then (play, layout, role) sorted as strings (the refused rule).
    - Per play: <ul class="shifted-play" data-family data-play> with the same <li>s, only that (family, play)'s, the element sibling IMMEDIATELY AFTER that
        play's <ul class="refused-play"> block when it has one, else immediately before the play's first <h2 data-notable> (the refused block's own placement
        rule). A (family, play) with no finding: in the same region as the refused blocks (after the cut-scan list, before the global lists), ordered by (family
        order, play) with a play's refused block first and its shifted block next.
    - No shifted_posts anywhere (or all empty): none of these elements, and the page holds neither "post shifted" nor "shifted-posts" nor "shifted-play".
"""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fakes_scans import ScriptedFight, _fr, fake_builds  # noqa: E402
from scripts.skilllab.contract import Setup  # noqa: E402
from scripts.skilllab import sweep  # noqa: E402
from test_report import _artifact_inputs, _page, _sec, _tree  # noqa: E402
from test_drift_fix_refused_lines import entry as refused_entry  # noqa: E402
from test_drift_fix_refused_beside import first_h2, global_ul, play_uls  # noqa: E402

# ---------------------------------------------------------------------------------------------------- the sweep and the smoke summaries

CAPS = sweep.Capabilities(arc=True, cone=True)


def shifting(shifts, refuse=None):
    """fake_builds with a placement_shift label: shifts {(play, role): f(enemy_heads)}. The label is set at call time, as sweep._naive_side does."""
    inner = fake_builds(refuse=refuse)

    def builds(play, role, features):
        base = inner(play, role, features)
        fn = shifts.get((play, role))
        if fn is None:
            return base

        def build(enemy_heads, swap):
            setup = base(enemy_heads, swap)
            build.labels["prefight"] = base.labels["prefight"]
            build.labels["placement_shift"] = fn(enemy_heads) if base.labels["prefight"] in (None, "ok") else 0.0
            return setup
        build.labels = {"placement_shift": 0.0, "prefight": None}
        return build
    return builds


class Wins(ScriptedFight):
    def __init__(self):
        super().__init__(be_of=lambda setup: 20)


def run_family(tmp_path, builds, family="range_up", plays=("p2",), layouts=None):
    entry = sweep.run_family(family, tmp_path, builds=builds, layouts=layouts or {"A": {"id": 1}}, plays=plays, fight_fn=Wins(), caps=CAPS, replicates=1)
    with open(tmp_path / ("sweep_%s.csv" % family), newline="") as fh:
        return entry, list(csv.DictReader(fh))


def test_a_shifted_naive_defender_is_listed_with_its_family_play_layout_role_and_distance(tmp_path):
    entry, _ = run_family(tmp_path, shifting({("p2", "naive_defender"): lambda h: 110.43}))
    got = entry["shifted_posts"]
    assert len(got) == 1 and {k: v for k, v in got[0].items() if k != "shift_wu"} == {"family": "range_up", "play": "p2", "layout": "A", "role": "naive_defender"}
    assert got[0]["shift_wu"] == pytest.approx(110.43)


def test_control_nothing_moved_lists_nothing_and_the_key_is_there(tmp_path):
    entry, _ = run_family(tmp_path, fake_builds())
    assert entry["shifted_posts"] == []


def test_the_largest_shift_over_the_headcounts_is_the_one_reported(tmp_path):
    entry, _ = run_family(tmp_path, shifting({("p2", "naive_defender"): lambda h: 100.0 + h}))
    assert [e["shift_wu"] for e in entry["shifted_posts"]] == [100.0 + sweep.ENEMY_TO]


def test_the_largest_shift_is_found_when_it_sits_in_the_middle_of_the_headcounts(tmp_path):
    """Not the last build and not the larger of the two endpoint headcounts (8 and 48): the shift peaks at 24 (150.0; 8 gives 134.0, 48 gives 126.0)."""
    entry, _ = run_family(tmp_path, shifting({("p2", "naive_defender"): lambda h: 150.0 - abs(h - 24)}))
    assert [e["shift_wu"] for e in entry["shifted_posts"]] == [150.0]


def test_each_layer_variant_of_a_layer_holder_is_listed_in_baseline_order_per_layout(tmp_path):
    shifts = {(p, r): (lambda h, v=v: v) for p, base in (("s3_layer_above", 10.0), ("s3_types_by_reach", 20.0))
              for r, v in (("naive_defender_attacker_layer", base + 1.0), ("naive_defender_play_layer", base + 2.0))}
    entry, _ = run_family(tmp_path, shifting(shifts), plays=("s3_layer_above", "s3_types_by_reach"), layouts={"A": {"id": 1}, "B": {"id": 2}})
    assert [(e["layout"], e["play"], e["role"], e["shift_wu"]) for e in entry["shifted_posts"]] == [
        ("A", "s3_layer_above", "naive_defender_attacker_layer", 11.0), ("A", "s3_layer_above", "naive_defender_play_layer", 12.0),
        ("A", "s3_types_by_reach", "naive_defender_attacker_layer", 21.0), ("A", "s3_types_by_reach", "naive_defender_play_layer", 22.0),
        ("B", "s3_layer_above", "naive_defender_attacker_layer", 11.0), ("B", "s3_layer_above", "naive_defender_play_layer", 12.0),
        ("B", "s3_types_by_reach", "naive_defender_attacker_layer", 21.0), ("B", "s3_types_by_reach", "naive_defender_play_layer", 22.0)]


def test_a_refused_baseline_is_never_listed_as_shifted(tmp_path):
    entry, rows = run_family(tmp_path, shifting({("p2", "naive_defender"): lambda h: 55.0}, refuse={("p2", "naive_defender"): "no_reach"}))
    assert entry["shifted_posts"] == [] and any(r["reason"] == "no_reach" for r in entry["refused"])
    assert "naive_defender" not in {r["baseline"] for r in rows}


def test_the_attacker_baseline_is_not_listed_when_only_the_defender_moved(tmp_path):
    entry, _ = run_family(tmp_path, shifting({("p2", "naive_defender"): lambda h: 5.0}))
    assert {e["role"] for e in entry["shifted_posts"]} == {"naive_defender"}


def test_no_csv_column_holds_the_shift(tmp_path):
    _, rows = run_family(tmp_path, shifting({("p2", "naive_defender"): lambda h: 110.43}))
    assert rows and not [c for c in rows[0] if "shift" in c]


def test_the_smoke_summary_lists_the_shift_without_a_family(tmp_path):
    controls = {n: (lambda h, swap, n=n: Setup(groups=(), unit_types={"enemy": h, "swap": swap, "_play": n, "_role": "play"}))
                for n in ("mirror", "numbers", "planted")}
    shifts = {("s3_layer_above", "naive_defender_play_layer"): lambda h: 33.3}
    summary = sweep.run_smoke(tmp_path, workers=1, builds=shifting(shifts), layouts={"A": {"id": 1}}, fight_fn=Wins(), control_builds=controls,
                              replicates=1, caps=sweep.Capabilities(arc=False, cone=False))
    assert len(summary["shifted_posts"]) == 1
    got = summary["shifted_posts"][0]
    assert {k: v for k, v in got.items() if k != "shift_wu"} == {"play": "s3_layer_above", "layout": "A", "role": "naive_defender_play_layer"}
    assert got["shift_wu"] == pytest.approx(33.3)
    with open(tmp_path / "smoke.csv", newline="") as fh:
        assert not [c for c in next(csv.reader(fh)) if "shift" in c]


def test_control_the_smoke_summary_with_no_shift_has_the_empty_list(tmp_path):
    controls = {n: (lambda h, swap, n=n: Setup(groups=(), unit_types={"enemy": h, "swap": swap, "_play": n, "_role": "play"}))
                for n in ("mirror", "numbers", "planted")}
    summary = sweep.run_smoke(tmp_path, workers=1, builds=fake_builds(), layouts={"A": {"id": 1}}, fight_fn=Wins(), control_builds=controls, replicates=1,
                              caps=sweep.Capabilities(arc=False, cone=False))
    assert summary["shifted_posts"] == []


# ---------------------------------------------------------------------------------------------------- the artifact

def shifted(role, wu, play="s3_layer_above", layout="192", family="range_up"):
    return {"family": family, "play": play, "layout": layout, "role": role, "shift_wu": wu}


def with_shifts(*shifts, refused=(), family="range_up"):
    _, _, summary = _artifact_inputs()
    summary["families"][family] = dict(summary["families"][family], shifted_posts=list(shifts), refused=list(refused))
    return summary


def shifted_uls(html, cls):
    sec = _sec(_tree(html), "findings")
    return sec, [u for u in sec.find("ul") if cls in u.attrs.get("class", "").split()]


def in_sec(sec, cls):
    return [u for u in sec.find("ul") if cls in u.attrs.get("class", "").split()]


def lines_of(ul):
    return [li.text().strip() for li in ul.find("li")]


def test_the_line_is_naive_role_post_shifted_with_one_decimal(tmp_path):
    summary = with_shifts(shifted("naive_defender", 110.43), shifted("naive_defender_play_layer", 87.0, layout="81"),
                          shifted("naive_defender_attacker_layer", 110.46, layout="78"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = shifted_uls(html, "shifted-posts")
    assert len(uls) == 1
    lis = uls[0].find("li")
    assert [li.text().strip() for li in lis] == ["naive defender: post shifted 110.4 wu", "naive defender attacker layer: post shifted 110.5 wu",
                                                 "naive defender play layer: post shifted 87.0 wu"]      # layout 192 < 78 < 81 as strings
    assert [li.attrs["data-layout"] for li in lis] == ["192", "78", "81"]
    assert all("data-shifted-post" in li.attrs for li in lis)
    assert [li.attrs["data-shift-wu"] for li in lis] == ["110.4", "110.5", "87.0"]
    assert [(li.attrs["data-family"], li.attrs["data-play"], li.attrs["data-role"]) for li in lis] == [
        ("range_up", "s3_layer_above", "naive_defender"), ("range_up", "s3_layer_above", "naive_defender_attacker_layer"),
        ("range_up", "s3_layer_above", "naive_defender_play_layer")]


def test_the_global_list_is_the_last_element_child_and_sorted_by_family_then_play_layout_role(tmp_path):
    _, _, summary = _artifact_inputs()
    summary["families"]["range_up"] = dict(summary["families"]["range_up"], shifted_posts=[
        shifted("naive_defender", 9.0, play="b_play", layout="81"), shifted("naive_defender", 8.0, play="a_play", layout="81"),
        shifted("naive_defender", 7.0, play="a_play", layout="192")])
    summary["families"]["vision"] = dict(summary["families"]["vision"], shifted_posts=[shifted("naive_defender", 6.0, play="a_play", layout="1", family="vision")])
    summary["families"]["arc"] = dict(summary["families"]["arc"], shifted_posts=[shifted("naive_defender", 5.0, play="zz", layout="1", family="arc")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = shifted_uls(html, "shifted-posts")
    assert sec.elements()[-1] is uls[0]
    assert [(li.attrs["data-family"], li.attrs["data-play"], li.attrs["data-layout"]) for li in uls[0].find("li")] == [
        ("range_up", "a_play", "192"), ("range_up", "a_play", "81"), ("range_up", "b_play", "81"), ("vision", "a_play", "1")]   # arc is not in summary["order"]


def test_with_a_refused_list_the_shifted_list_comes_after_it(tmp_path):
    summary = with_shifts(shifted("naive_defender", 12.0), refused=[refused_entry("naive_attacker", "unroutable", play="s3_types_by_reach")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = shifted_uls(html, "shifted-posts")
    els = sec.elements()
    assert len(global_ul(sec)) == 1 and els[-1] is uls[0] and els[-2] is global_ul(sec)[0]


def test_a_play_with_a_finding_gets_its_block_right_before_the_first_finding(tmp_path):
    summary = with_shifts(shifted("naive_defender", 12.0, layout="81"), shifted("naive_defender", 13.0, layout="78"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = shifted_uls(html, "shifted-play")
    assert len(uls) == 1 and (uls[0].attrs["data-family"], uls[0].attrs["data-play"]) == ("range_up", "s3_layer_above")
    assert lines_of(uls[0]) == ["naive defender: post shifted 13.0 wu", "naive defender: post shifted 12.0 wu"]      # layout 78 before 81
    els = sec.elements()
    assert els.index(uls[0]) == els.index(first_h2(sec, "range_up", "s3_layer_above")) - 1


def test_the_shifted_block_follows_the_plays_refused_block(tmp_path):
    summary = with_shifts(shifted("naive_defender", 12.0), refused=[refused_entry("naive_attacker", "no_reach")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, refused_uls = play_uls(html)
    uls = in_sec(sec, "shifted-play")
    els = sec.elements()
    assert len(refused_uls) == 1 and len(uls) == 1
    assert els.index(uls[0]) == els.index(refused_uls[0]) + 1 and els.index(uls[0]) == els.index(first_h2(sec, "range_up", "s3_layer_above")) - 1


def test_a_play_with_no_finding_still_has_its_block_before_the_global_lists_after_its_refused_block(tmp_path):
    summary = with_shifts(shifted("naive_defender", 12.0, play="s1_outrange"), refused=[refused_entry("naive_attacker", "no_reach", play="s1_outrange")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, refused_uls = play_uls(html)
    uls = in_sec(sec, "shifted-play")
    els = sec.elements()
    assert len(uls) == 1 and uls[0].attrs["data-play"] == "s1_outrange"
    assert els.index(uls[0]) == els.index(refused_uls[0]) + 1
    assert els.index(uls[0]) < els.index(global_ul(sec)[0]) < els.index(in_sec(sec, "shifted-posts")[0])


def test_two_plays_each_carry_only_their_own_shifted_lines(tmp_path):
    summary = with_shifts(shifted("naive_defender", 12.0, play="s3_layer_above"), shifted("naive_defender", 14.0, play="s3_types_by_reach"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, uls = shifted_uls(html, "shifted-play")
    assert {u.attrs["data-play"]: lines_of(u) for u in uls} == {"s3_layer_above": ["naive defender: post shifted 12.0 wu"],
                                                                "s3_types_by_reach": ["naive defender: post shifted 14.0 wu"]}


def test_nothing_shifted_no_element_and_no_words(tmp_path):
    for summary in (_artifact_inputs()[2], with_shifts()):
        _, _, html, _ = _page(tmp_path, summary=summary)
        assert "post shifted" not in html and "shifted-posts" not in html and "shifted-play" not in html and "data-shifted-post" not in html


def test_control_the_refused_lists_alone_are_unchanged(tmp_path):
    summary = with_shifts(refused=[refused_entry("naive_defender", "blind_post")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec = _sec(_tree(html), "findings")
    assert sec.elements()[-1] is global_ul(sec)[0] and "post shifted" not in html


# ---------------------------------------------------------------------------------------------------- the artifact: orders and the naive_ filter (audit of FIX5)

def sequence(sec, *classes):
    """The (class, family, play) of the per-play blocks, in the order they sit among the findings' element children."""
    return [(u.attrs["class"], u.attrs["data-family"], u.attrs["data-play"]) for u in sec.elements()
            if u.name == "ul" and u.attrs.get("class") in classes]


def keys(ul, *attrs):
    return [tuple(li.attrs[a] for a in attrs) for li in ul.find("li")]


def two_families(order, **by_family):
    _, _, summary = _artifact_inputs()
    summary["order"] = list(order)
    for fam, posts in by_family.items():
        summary["families"][fam] = dict(summary["families"][fam], shifted_posts=list(posts))
    return summary


def test_the_global_list_sorts_by_play_before_layout_and_before_role(tmp_path):
    """Play a is on layout 81 and play b on layout 192: (play, layout, role) puts a before b, (layout, play, role) would not."""
    summary = with_shifts(shifted("naive_defender", 1.0, play="b_play", layout="192"), shifted("naive_defender", 2.0, play="a_play", layout="81"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, uls = shifted_uls(html, "shifted-posts")
    assert keys(uls[0], "data-play", "data-layout") == [("a_play", "81"), ("b_play", "192")]


def test_the_global_list_sorts_by_layout_before_role_within_a_play(tmp_path):
    """Layout 192 carries the role that sorts LAST and layout 81 the role that sorts first: layout order and role order disagree."""
    summary = with_shifts(shifted("naive_defender_play_layer", 1.0, layout="192"), shifted("naive_defender", 2.0, layout="81"),
                          shifted("naive_defender_attacker_layer", 3.0, layout="81"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, uls = shifted_uls(html, "shifted-posts")
    assert keys(uls[0], "data-layout", "data-role") == [("192", "naive_defender_play_layer"), ("81", "naive_defender"), ("81", "naive_defender_attacker_layer")]


def test_the_per_play_block_sorts_layouts_as_strings_and_layout_before_role(tmp_path):
    """Layouts 192 and 78: as strings 192 < 78 (as integers 78 < 192); the role on 192 sorts after the role on 78."""
    summary = with_shifts(shifted("naive_defender_play_layer", 1.0, layout="192"), shifted("naive_defender", 2.0, layout="78"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, uls = shifted_uls(html, "shifted-play")
    assert len(uls) == 1 and keys(uls[0], "data-layout", "data-role") == [("192", "naive_defender_play_layer"), ("78", "naive_defender")]


def test_families_follow_summary_order_not_the_alphabet(tmp_path):
    """summary["order"] = vision, range_up: vision comes first in the global list; alphabetically range_up would."""
    summary = two_families(["vision", "range_up"], range_up=[shifted("naive_defender", 1.0)],
                           vision=[shifted("naive_defender", 2.0, family="vision", play="s3_types_by_reach")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, uls = shifted_uls(html, "shifted-posts")
    assert keys(uls[0], "data-family", "data-play") == [("vision", "s3_types_by_reach"), ("range_up", "s3_layer_above")]


def test_a_non_naive_role_is_in_no_shifted_list(tmp_path):
    summary = with_shifts(shifted("reach_zero", 7.0), shifted("play", 8.0, layout="81"), shifted("naive_defender", 9.0, layout="78"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = shifted_uls(html, "shifted-posts")
    assert keys(uls[0], "data-role") == [("naive_defender",)]
    assert [keys(u, "data-role") for u in in_sec(sec, "shifted-play")] == [[("naive_defender",)]]
    assert "reach zero: post shifted" not in html and "play: post shifted" not in html


def test_control_only_non_naive_roles_leave_no_shifted_element(tmp_path):
    _, _, html, _ = _page(tmp_path, summary=with_shifts(shifted("reach_zero", 7.0), shifted("play", 8.0, layout="81")))
    assert "post shifted" not in html and "shifted-posts" not in html and "shifted-play" not in html


def test_leftover_plays_are_ordered_by_family_then_play_each_refused_block_just_before_its_shifted_block(tmp_path):
    """Leftover plays (no notable on the page): s4_bait has a refused and a shifted block, s1_outrange only a shifted one. The inputs list s4_bait first."""
    _, _, summary = _artifact_inputs()
    summary["order"] = ["vision", "range_up"]
    summary["families"]["range_up"] = dict(summary["families"]["range_up"], shifted_posts=[
        shifted("naive_defender", 3.0, play="s4_bait"), shifted("naive_defender", 4.0, play="s1_outrange")],
        refused=[refused_entry("naive_attacker", "no_reach", play="s4_bait")])
    summary["families"]["vision"] = dict(summary["families"]["vision"], shifted_posts=[shifted("naive_defender", 5.0, play="s2_spread_line", family="vision")],
                                         refused=[refused_entry("naive_attacker", "no_reach", play="s2_spread_line", family="vision")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec = _sec(_tree(html), "findings")
    assert sequence(sec, "refused-play", "shifted-play") == [
        ("refused-play", "vision", "s2_spread_line"), ("shifted-play", "vision", "s2_spread_line"),
        ("shifted-play", "range_up", "s1_outrange"), ("refused-play", "range_up", "s4_bait"), ("shifted-play", "range_up", "s4_bait")]

