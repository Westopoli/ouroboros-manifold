# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 item 6 and decision 44 item 3; Architect ruling 2026-10-19 (relayed): four plays
# (s1_outrange, s2_spread_line, s4_bait, s4_do_not_chase) are refused blind_post on layouts 81 and 78, so they have no naive-defender baseline on two of three
# smoke layouts; the refused lines must sit BESIDE those plays and the header must say batch one's C1 for them rests on naive_attacker only
"""LAB-REV2-FIX round 4: the refused lines beside the play, and the header sentence (report.artifact).

INTERFACE FOR THE BUILDER (frozen here; builds on test_drift_fix_refused_lines.py, whose global list stays unchanged)
  Shape chosen (the Architect's "choose ONE shape"): per-play block = <ul class="refused-play" data-family data-play> inside <section id="findings">, holding the SAME
      <li data-refused-baseline data-family data-play data-layout data-role data-reason>LINE ...</li> items as the global list (same LINE rule, same naive_ filter,
      same order: (layout, role) sorted as strings), only the entries of that (family, play). One such <ul> per (family, play) with at least one such entry.
  Placement: the <ul> is the element sibling IMMEDIATELY BEFORE the first <h2 data-notable=...> of that (family, play) (first in diagram.notables order; the order
      the page already lists them). A (family, play) with no notable in the page: its <ul> sits after the cut-scan list (if any), before the global
      <ul class="refused-baselines">, which stays the last element child; those uls in summary["order"] family order, then play sorted as strings.
  Header: <section id="drafts"> (the page's DRAFT/legend header) ends with ONE <p class="no-defender-baseline" data-plays-without-defender="a,b,c">, the last element
      child, after <ul class="drafts">. Its text starts with the exact sentence `C1 for plays without a naive defender baseline rests on naive_attacker only` and
      then names each play (any separator). data-plays-without-defender = the plays (deduped across families, sorted as strings, "," joined, no spaces) having at least
      one refused entry whose role starts with "naive_defender" (a family not in summary["order"] is not read). No such entry: no <p>, no attribute, and the page
      holds neither the sentence nor "data-plays-without-defender". A play refused only for naive_attacker (or any other non-defender role) is not named: the sentence
      would be false for it (Q-FIX4-1).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_report import _artifact_inputs, _cut_rows, _page, _sec, _summary_with, _tree, CUT  # noqa: E402
from test_drift_fix_refused_lines import entry, summary_with  # noqa: E402

SENTENCE = "C1 for plays without a naive defender baseline rests on naive_attacker only"
FOUR = ("s1_outrange", "s2_spread_line", "s4_bait", "s4_do_not_chase")


def four_plays(layouts=("81", "78")):
    return [entry("naive_defender", "blind_post", play=p, layout=l) for p in reversed(FOUR) for l in layouts]


def play_uls(html):
    sec = _sec(_tree(html), "findings")
    return sec, [u for u in sec.find("ul") if "refused-play" in u.attrs.get("class", "").split()]


def lines_of(ul):
    return [li.text().strip() for li in ul.find("li")]


def global_ul(sec):
    return [u for u in sec.find("ul") if "refused-baselines" in u.attrs.get("class", "").split()]


def header_ps(html):
    sec = _sec(_tree(html), "drafts")
    return sec, [p for p in sec.find("p") if "no-defender-baseline" in p.attrs.get("class", "").split()]


def first_h2(sec, family, play):
    """The first <h2 data-notable> of (family, play), by diagram.notables order, found among the findings' element children."""
    from scripts.skilllab import diagram
    _, rows, _ = _artifact_inputs()
    ids = [n.id for n in diagram.notables(rows) if (n.family, n.play) == (family, play)]
    assert ids, (family, play)
    h2s = [e for e in sec.elements() if e.name == "h2" and e.attrs.get("data-notable") in ids]
    return h2s[0]


# ---- (1) beside the play's own rows ----

def test_the_refused_lines_sit_right_before_the_plays_first_finding(tmp_path):
    summary = summary_with(entry("naive_defender", "blind_post", play="s3_layer_above", layout="81"),
                           entry("naive_defender", "blind_post", play="s3_layer_above", layout="78"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = play_uls(html)
    assert len(uls) == 1
    ul = uls[0]
    assert (ul.attrs["data-family"], ul.attrs["data-play"]) == ("range_up", "s3_layer_above")
    assert lines_of(ul) == ["no naive defender: blind post"] * 2
    assert [li.attrs["data-layout"] for li in ul.find("li")] == ["78", "81"]
    assert all("data-refused-baseline" in li.attrs for li in ul.find("li"))
    els = sec.elements()
    h2 = first_h2(sec, "range_up", "s3_layer_above")
    assert els.index(ul) == els.index(h2) - 1
    # the global list stays, with the same two lines
    g = global_ul(sec)
    assert len(g) == 1 and els[-1] is g[0] and lines_of(g[0]) == lines_of(ul)


def test_a_play_with_no_refusal_gets_no_block_and_the_same_play_in_another_family_gets_its_own(tmp_path):
    """Keyed by (family, play): s3_layer_above is a finding in range_up and in vision; only vision is refused here; s3_types_by_reach is never refused."""
    summary = summary_with(entry("naive_defender", "no_fit", play="s3_layer_above", layout="78", family="vision"), family="vision")
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = play_uls(html)
    assert [(u.attrs["data-family"], u.attrs["data-play"]) for u in uls] == [("vision", "s3_layer_above")]
    assert lines_of(uls[0]) == ["no naive defender: no fit"]
    els = sec.elements()
    assert els.index(uls[0]) == els.index(first_h2(sec, "vision", "s3_layer_above")) - 1
    # no block next to the range_up play or next to the other play
    for family, play in (("range_up", "s3_layer_above"), ("range_up", "s3_types_by_reach")):
        h = els.index(first_h2(sec, family, play))
        assert "refused-play" not in els[h - 1].attrs.get("class", "").split()


def test_two_refused_plays_each_carry_only_their_own_lines(tmp_path):
    summary = summary_with(entry("naive_defender", "blind_post", play="s3_layer_above", layout="81"),
                           entry("naive_attacker", "unroutable", play="s3_types_by_reach", layout="81"),
                           entry("naive_defender", "no_reach", play="s3_types_by_reach", layout="78"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = play_uls(html)
    got = {u.attrs["data-play"]: lines_of(u) for u in uls}
    assert got == {"s3_layer_above": ["no naive defender: blind post"],
                   "s3_types_by_reach": ["no naive defender: no reach", "no naive attacker: unroutable"]}   # layout 78 before 81
    els = sec.elements()
    for u in uls:
        assert els.index(u) == els.index(first_h2(sec, "range_up", u.attrs["data-play"])) - 1


def test_a_play_with_no_finding_still_has_its_block_before_the_global_list(tmp_path):
    summary = summary_with(*four_plays())
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = play_uls(html)
    assert [u.attrs["data-play"] for u in uls] == list(FOUR)                     # sorted as strings
    assert all(lines_of(u) == ["no naive defender: blind post"] * 2 for u in uls)
    els = sec.elements()
    g = global_ul(sec)
    assert len(g) == 1 and els[-1] is g[0] and len(g[0].find("li")) == 8
    idx = [els.index(u) for u in uls]
    assert idx == list(range(els.index(g[0]) - 4, els.index(g[0])))              # a contiguous run right before the global list


def test_the_blocks_without_a_finding_follow_the_cut_list(tmp_path):
    summary = _summary_with(CUT)
    summary["families"]["range_up"]["refused"] = [entry("naive_defender", "blind_post", play="s4_bait", layout="81")]
    _, _, html, _ = _page(tmp_path, rows=_cut_rows(), summary=summary)
    sec, uls = play_uls(html)
    cuts = [u for u in sec.find("ul") if "cut-scans" in u.attrs.get("class", "").split()]
    els = sec.elements()
    assert len(cuts) == 1 and len(uls) == 1 and uls[0].attrs["data-play"] == "s4_bait"
    assert els.index(cuts[0]) < els.index(uls[0]) < els.index(global_ul(sec)[0]) and els[-1] is global_ul(sec)[0]


def test_a_block_holds_only_the_naive_roles_like_the_global_list(tmp_path):
    summary = summary_with(entry("naive_defender", "blind_post", play="s4_bait"), entry("none", "no_fit", play="s4_bait"))
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, uls = play_uls(html)
    assert len(uls) == 1 and lines_of(uls[0]) == ["no naive defender: blind post"]


def test_the_block_lines_are_the_global_lines_for_that_play(tmp_path):
    summary = summary_with(*four_plays())
    _, _, html, _ = _page(tmp_path, summary=summary)
    sec, uls = play_uls(html)
    mine = [(li.attrs["data-play"], li.attrs["data-layout"], li.text().strip()) for u in uls for li in u.find("li")]
    theirs = sorted([(li.attrs["data-play"], li.attrs["data-layout"], li.text().strip()) for li in global_ul(sec)[0].find("li")])
    assert sorted(mine) == theirs and len(mine) == 8


def test_nothing_refused_means_no_block(tmp_path):
    """Negative control: an empty list, a missing key and the fixture's own summary read alike."""
    for n, summary in enumerate((summary_with(), _artifact_inputs()[2])):
        _, _, html, _ = _page(tmp_path / str(n), summary=summary)
        assert not play_uls(html)[1] and "refused-play" not in html


def test_a_family_outside_the_order_is_not_read_for_the_blocks(tmp_path):
    summary = summary_with()
    summary["families"]["arc"] = dict(summary["families"]["arc"], refused=[entry("naive_defender", "no_reach", play="zz", family="arc")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    assert not play_uls(html)[1] and "zz" not in html


# ---- (2) the header sentence ----

def test_the_header_says_c1_rests_on_naive_attacker_and_names_the_four_plays(tmp_path):
    _, _, html, _ = _page(tmp_path, summary=summary_with(*four_plays()))
    sec, ps = header_ps(html)
    assert len(ps) == 1
    p = ps[0]
    assert sec.elements()[-1] is p and sec.elements()[-2].name == "ul" and "drafts" in sec.elements()[-2].attrs.get("class", "").split()
    assert p.text().startswith(SENTENCE)
    assert p.attrs["data-plays-without-defender"] == "s1_outrange,s2_spread_line,s4_bait,s4_do_not_chase"
    assert all(name in p.text() for name in FOUR)
    assert html.count(SENTENCE) == 1


def test_the_named_plays_are_deduped_across_families_and_layouts_and_sorted_as_strings(tmp_path):
    summary = summary_with(entry("naive_defender", "blind_post", play="b_play", layout="81"), entry("naive_defender", "no_fit", play="b_play", layout="78"),
                           entry("naive_defender_play_layer", "no_reach", play="B_play"))
    summary["families"]["vision"] = dict(summary["families"]["vision"], refused=[entry("naive_defender", "blind_post", play="b_play", family="vision"),
                                                                                  entry("naive_defender", "blind_post", play="a_play", family="vision")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    assert header_ps(html)[1][0].attrs["data-plays-without-defender"] == "B_play,a_play,b_play"          # "B" < "a" as strings


def test_a_family_outside_the_order_does_not_add_a_play_to_the_header(tmp_path):
    summary = summary_with(entry("naive_defender", "blind_post", play="s4_bait"))
    summary["families"]["arc"] = dict(summary["families"]["arc"], refused=[entry("naive_defender", "no_reach", play="zz", family="arc")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    assert header_ps(html)[1][0].attrs["data-plays-without-defender"] == "s4_bait" and "zz" not in html


def test_a_play_refused_only_for_the_attacker_is_not_named(tmp_path):
    """Q-FIX4-1: the sentence says C1 rests on naive_attacker only; for a play whose attacker baseline is refused that would be false."""
    _, _, html, _ = _page(tmp_path, summary=summary_with(entry("naive_attacker", "unroutable", play="p1")))
    assert not header_ps(html)[1] and SENTENCE not in html and "data-plays-without-defender" not in html
    _, uls = play_uls(html)
    assert len(uls) == 1 and uls[0].attrs["data-play"] == "p1"                  # the line is still beside the play
    _, _, html2, _ = _page(tmp_path / "b", summary=summary_with(entry("naive_attacker", "unroutable", play="p1"), entry("naive_defender", "blind_post", play="p2")))
    assert header_ps(html2)[1][0].attrs["data-plays-without-defender"] == "p2"


def test_nothing_refused_means_no_header_sentence(tmp_path):
    """Negative control."""
    for n, summary in enumerate((summary_with(), _artifact_inputs()[2])):
        _, _, html, _ = _page(tmp_path / str(n), summary=summary)
        assert not header_ps(html)[1]
        assert SENTENCE not in html and "data-plays-without-defender" not in html and "no-defender-baseline" not in html


def test_the_page_with_blocks_and_header_is_deterministic(tmp_path):
    summary = summary_with(*four_plays())
    pages = [_page(tmp_path / n, summary=summary)[2] for n in ("a", "b")]
    assert pages[0] == pages[1]
