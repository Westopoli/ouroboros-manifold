# spec: docs/northstar/plans/2026-10-14-skill-lab-rev2-decisions.md decision 43 item 6 ('the artifact says "no naive defender: blind post"') and decision 44 item 3 (Architect,
# 2026-10-19): the artifact lists every refused baseline, for every reason, as one line
"""LAB-REV2-FIX round 3: the artifact's line for each refused baseline (report.artifact reads the sweep entry's `refused` list, which it ignored).

INTERFACE FOR THE BUILDER (frozen here; the full text is in test_drift_fix_blind_post.py's header)
  summary["families"][family]["refused"] = [{"family", "play", "layout", "role", "reason"}, ...]   (sweep's entry key; may be missing or empty)
  In <section id="findings">, after the cut-scan list when there is one: ONE <ul class="refused-baselines"> as the last element child, one
      <li data-refused-baseline data-family data-play data-layout data-role data-reason>LINE ...</li>   per entry whose role starts with "naive_".
  LINE = "no naive " + <role without "naive_", "_" as " "> + ": " + <reason, "_" as " ">   (Q-FIX3-1, Q-FIX3-2: the test writer's one rule; the Architect's own
      sentence "no naive defender: blind post" is its instance). data-role and data-reason carry the codes with their underscores.
  Order: summary["order"] family order (a family in the summary and not in "order" is not read, as everywhere else), then (play, layout, role) sorted as strings.
  Nothing refused: no such <ul>, and the page holds neither "no naive" nor "blind post".
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from test_report import _artifact_inputs, _cut_rows, _page, _sec, _summary_with, _tree, CUT  # noqa: E402


def entry(role, reason, play="s3_layer_above", layout="192", family="range_up"):
    return {"family": family, "play": play, "layout": layout, "role": role, "reason": reason}


def summary_with(*refused, family="range_up", **more):
    _, _, summary = _artifact_inputs()
    summary["families"][family] = dict(summary["families"][family], refused=list(refused), **more)
    return summary


def refused_lis(html):
    sec = _sec(_tree(html), "findings")
    uls = [u for u in sec.find("ul") if "refused-baselines" in u.attrs.get("class", "").split()]
    return sec, uls, [li for u in uls for li in u.find("li")]


def lines(html):
    return [li.text().strip() for li in refused_lis(html)[2]]


def test_the_architects_sentence_for_a_blind_post(tmp_path):
    _, _, html, _ = _page(tmp_path, summary=summary_with(entry("naive_defender", "blind_post")))
    sec, uls, lis = refused_lis(html)
    assert len(uls) == 1 and len(lis) == 1
    li = lis[0]
    assert li.text().strip().startswith("no naive defender: blind post")
    assert "data-refused-baseline" in li.attrs
    assert (li.attrs["data-family"], li.attrs["data-play"], li.attrs["data-layout"], li.attrs["data-role"], li.attrs["data-reason"]) == (
        "range_up", "s3_layer_above", "192", "naive_defender", "blind_post")
    assert sec.elements()[-1] is uls[0]


def test_every_reason_and_role_has_its_line(tmp_path):
    got = [entry("naive_defender", "blind_post", play="p1"), entry("naive_defender", "no_fit", play="p2"),
           entry("naive_attacker", "unroutable", play="p3"), entry("naive_defender_play_layer", "no_reach", play="p4"),
           entry("naive_defender_attacker_layer", "blind_post", play="p5")]
    _, _, html, _ = _page(tmp_path, summary=summary_with(*got))
    _, _, lis = refused_lis(html)
    texts = [li.text().strip() for li in lis]
    want = ["no naive defender: blind post", "no naive defender: no fit", "no naive attacker: unroutable",
            "no naive defender play layer: no reach", "no naive defender attacker layer: blind post"]
    assert len(texts) == 5 and all(t.startswith(w) for t, w in zip(texts, want)), texts
    assert [li.attrs["data-reason"] for li in lis] == ["blind_post", "no_fit", "unroutable", "no_reach", "blind_post"]


def test_family_order_then_play_layout_role_as_strings(tmp_path):
    summary = summary_with(entry("naive_defender", "no_fit", play="b_play", layout="81"), entry("naive_attacker", "no_fit", play="a_play", layout="78"),
                           entry("naive_defender", "blind_post", play="a_play", layout="192"), entry("naive_attacker", "blind_post", play="a_play", layout="192"))
    summary["families"]["vision"] = dict(summary["families"]["vision"], refused=[entry("naive_defender", "no_reach", play="a_play", layout="1", family="vision")])
    summary["families"]["arc"] = dict(summary["families"]["arc"], refused=[entry("naive_defender", "no_reach", play="zz", layout="1", family="arc")])
    _, _, html, _ = _page(tmp_path, summary=summary)
    _, _, lis = refused_lis(html)
    assert [(li.attrs["data-family"], li.attrs["data-play"], li.attrs["data-layout"], li.attrs["data-role"]) for li in lis] == [
        ("range_up", "a_play", "192", "naive_attacker"), ("range_up", "a_play", "192", "naive_defender"),
        ("range_up", "a_play", "78", "naive_attacker"), ("range_up", "b_play", "81", "naive_defender"),
        ("vision", "a_play", "1", "naive_defender")]               # layout "192" < "78" < "81" as strings; family arc is not in summary["order"]: not read


def test_a_refused_list_follows_the_cut_list_when_both_exist(tmp_path):
    summary = _summary_with(CUT)
    summary["families"]["range_up"]["refused"] = [entry("naive_defender", "blind_post")]
    _, _, html, _ = _page(tmp_path, rows=_cut_rows(), summary=summary)
    sec, refused, _ = refused_lis(html)
    cuts = [u for u in sec.find("ul") if "cut-scans" in u.attrs.get("class", "").split()]
    elements = sec.elements()
    assert len(cuts) == 1 and len(refused) == 1
    assert elements.index(cuts[0]) < elements.index(refused[0]) and elements[-1] is refused[0]


def test_nothing_refused_means_no_list_and_no_words(tmp_path):
    """Negative control: an empty list, a missing key and the fixture's own summary read alike."""
    for n, summary in enumerate((summary_with(), _artifact_inputs()[2])):
        _, _, html, _ = _page(tmp_path / str(n), summary=summary)
        assert not refused_lis(html)[1] and "no naive" not in html and "blind post" not in html


def test_the_page_is_deterministic(tmp_path):
    summary = summary_with(entry("naive_defender", "blind_post"), entry("naive_attacker", "no_fit", play="p2"))
    pages = [_page(tmp_path / n, summary=summary)[2] for n in ("a", "b")]
    assert pages[0] == pages[1]
