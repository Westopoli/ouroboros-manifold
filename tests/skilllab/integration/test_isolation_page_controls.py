# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 6 (the page form), piece LI5 part 1
"""Positive and negative controls for the detectors the LI5 page tests use. These are green today: a red page test then means the page generator is missing or wrong, not that the harness is.
Controls: the standing page A-003 (data/a003_page.html, a copy of the published source) passes every checker; each checker rejects a planted bad snippet; `html.parser` builds the DOM and
rejects a mis-nested tag; `isolation_fw.comparison_rows` accepts the synthetic rows the other tests feed the page (so a synthetic input is a real LI4 input)."""
import pytest

import isolation_page_fixtures as pf


def test_a003_passes_every_checker():
    html = pf.A003.read_text()
    assert pf.all_problems(html) == []


def test_a003_has_the_form_the_page_copies():
    root = pf.parse(pf.A003.read_text())
    css = pf.css_of(root)
    assert pf.rule_body(css, r':root\[data-theme="dark"\]') and root.find("video") and root.find("table")
    assert all(v.attrs["poster"] and v.attrs["src"] for v in root.find("video"))


@pytest.mark.parametrize("bad, checker", [
    ("a{} :root { --bg: #fff; }", "problems_theme"),
    (':root { --bg:#fff; --panel:1; --fg:1; --muted:1; --line:1; --accent:1; --blue:1; --red:1; --warn:1; --warn-bg:1 } :root[data-theme="dark"] { --bg:#000 }', "problems_theme"),
    ("body { color: red }", "problems_body_background"),
    (".hero { height: 100vh }", "problems_no_hero"),
])
def test_css_checkers_reject_a_planted_bad_css(bad, checker):
    assert getattr(pf, checker)(bad) != []


def test_css_checkers_accept_a_planted_good_css():
    tokens = " ".join("%s: #123;" % t for t in pf.THEME_TOKENS)
    css = (":root { %s } @media (prefers-color-scheme: dark) { :root:not([data-theme=\"light\"]) { %s } } :root[data-theme=\"dark\"] { %s } body { background: var(--bg); }" % (tokens, tokens, tokens))
    assert pf.problems_theme(css) == [] and pf.problems_body_background(css) == [] and pf.problems_no_hero(css) == []


@pytest.mark.parametrize("bad", [
    '<script src="https://evil.example/x.js"></script>',
    '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/latest/d3.js"></script>',
    '<img src="https://example.com/a.png">',
    '<link rel="stylesheet" href="https://example.com/a.css">',
])
def test_host_checker_rejects_a_planted_external(bad):
    assert pf.problems_hosts(bad) != []


def test_host_checker_accepts_the_allowlist():
    ok = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans">'
          '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js"></script>'
          '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script><script>var x = "//not a url";</script>')
    assert pf.problems_hosts(ok) == []


def test_media_checker_rejects_absolute_missing_and_posterless(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"x")
    (tmp_path / "a.jpg").write_bytes(b"x")
    good = pf.parse('<video src="a.mp4" poster="a.jpg"></video>')
    assert pf.problems_media(good, tmp_path) == []
    for bad in ('<video src="/a.mp4" poster="a.jpg"></video>', '<video src="https://x/a.mp4" poster="a.jpg"></video>', '<video src="a.mp4"></video>', '<video src="b.mp4" poster="a.jpg"></video>'):
        assert pf.problems_media(pf.parse(bad), tmp_path) != []


def test_mobile_checker_rejects_a_bare_table():
    root = pf.parse("<style>video { max-width: 100%; }</style><table><tr><td>x</td></tr></table>")
    assert pf.problems_mobile(root, pf.css_of(root)) != []


def test_dom_rejects_a_mis_nested_tag_and_reads_text():
    with pytest.raises(pf.Malformed):
        pf.parse("<div><p>x</div></p>")
    with pytest.raises(pf.Malformed):
        pf.parse("<div><p>x</p>")
    root = pf.parse('<p>a &amp; <b>b</b> &lt;c&gt; <style>x{}</style></p>')
    assert root.one("p").text() == "a & b <c>"


def test_synthetic_rows_are_accepted_by_the_real_comparison_consumer():
    """The inputs the page tests use are inputs of the LI4-FW consumer: comparison_rows reads them and gives the facts the interface pins (L-0055 same, L-0084 changed in both seeds)."""
    got = {r["layout"]: r for r in pf.fw().comparison_rows(pf.synthetic_rows(), repo=pf.ROOT)}
    assert list(got) == ["L-0055", "L-0084"]
    assert (got["L-0055"]["same_or_changed"], got["L-0055"]["seeds_flipped"]) == ("same", 0)
    assert (got["L-0084"]["same_or_changed"], got["L-0084"]["seeds_flipped"]) == ("changed", 2)
    assert got["L-0084"]["ruling"]["words"] == pf.WORDS["L-0084"] and got["L-0084"]["control"]["then"]["defect"] is True
