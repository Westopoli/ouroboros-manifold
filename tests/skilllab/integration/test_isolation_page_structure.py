# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 6 (Delivery: "One artifact page ... a standing page"), piece LI5 part 1
"""The form of the page: one HTML file, the A-003 theme form, dark overrides with the exact guard selectors, an explicit body background, no 100vh hero, fonts only from Google Fonts, no external
script outside the pinned cdnjs/jsdelivr allowlist, nothing that scrolls the page sideways, and the section order of spec 6 (banner, comparison, arms, DRAFT list, shas, then clips).
Interface: docs/reports/2026-11-24-li5-interface.md. Red today: `scripts/skilllab/arena/isolation_page.py` does not exist."""
import json

import pytest

import isolation_page_fixtures as pf


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("page-structure")
    manifest = pf.clip_dir(tmp / "clipsrc", [("l0084-changed", "L-0084", "changed", ["then", "now"])])
    out, res = pf.build(tmp, pf.synthetic_rows() + pf.synthetic_f_rows(), m=[pf.m_summary()], v=[pf.v_row()], clips=manifest)
    return out, res, (out / "index.html").read_text()


def test_one_index_html_and_one_ledger_fragment(built):
    out, res, _ = built
    assert res["index"] == out / "index.html" and res["row"] == out / "artifacts-row.md" and res["index"].is_file() and res["row"].is_file()


def test_html_is_well_formed(built):
    root = pf.parse(built[2])
    assert root.find("table") and root.find("section")


def test_theme_tokens_dark_overrides_and_guard_selectors(built):
    """spec 6 form, as A-003: tokens on :root; dark overrides under prefers-color-scheme guarded `:root:not([data-theme="light"])` and `:root[data-theme="dark"]`."""
    css = pf.css_of(pf.parse(built[2]))
    assert pf.problems_theme(css) == []
    assert ':root:not([data-theme="light"])' in css and ':root[data-theme="dark"]' in css and "prefers-color-scheme: dark" in css


def test_body_background_is_explicit_and_no_hero_height(built):
    css = pf.css_of(pf.parse(built[2]))
    assert pf.problems_body_background(css) == [] and pf.problems_no_hero(css) == []


def test_fonts_from_google_and_no_script_outside_the_allowlist(built):
    html = built[2]
    assert pf.problems_hosts(html) == []
    assert "fonts.googleapis.com" in html          # the page uses the A-003 families, not system fonts alone


def test_media_relative_with_posters_and_files_in_the_output(built):
    out, _, html = built
    root = pf.parse(html)
    assert root.find("video") and pf.problems_media(root, out) == []


def test_no_horizontal_page_scroll(built):
    root = pf.parse(built[2])
    assert pf.problems_mobile(root, pf.css_of(root)) == []


def test_sections_in_the_order_of_spec_6(built):
    """banner, one sentence per layout, the comparison table, the arms, the DRAFT list, the shas, then the clips."""
    root = pf.parse(built[2])
    order = [n.attrs["data-section"] for n in root.walk() if "data-section" in n.attrs]
    assert order[0] == "banner"
    arms = [order.index(a) for a in ("arm-M", "arm-V", "arm-W", "arm-F")]
    assert len(arms) == 4 and order.index("sentences") < order.index("comparison") < min(arms)
    assert max(arms) < order.index("drafts") < order.index("shas") < order.index("clips")
    assert len(order) == len(set(order))


def test_arm_sections_exist_only_for_arms_with_input(tmp_path):
    out, _ = pf.build(tmp_path, pf.synthetic_rows())
    sections = {n.attrs["data-section"] for n in pf.page_root(out).walk() if "data-section" in n.attrs}
    assert {"arm-W", "arm-F"} >= {s for s in sections if s.startswith("arm-")} and "arm-M" not in sections and "arm-V" not in sections and "clips" not in sections
    assert {"banner", "sentences", "comparison", "drafts", "shas"} <= sections


@pytest.mark.parametrize("kind", ["decision", "ask"])
def test_banner_text_is_passed_in_and_escaped(tmp_path, kind):
    """spec 6: the decision/ask banner (text passed in): first thing in the body, escaped, kind named."""
    out, _ = pf.build(tmp_path, pf.synthetic_rows(), kind=kind)
    html = (out / "index.html").read_text()
    root = pf.parse(html)
    banner = root.one(data_section="banner")
    assert banner.attrs.get("data-banner") == kind and pf.BANNER in banner.text()
    assert "<b>&</b>" not in html


def test_unknown_banner_kind_is_refused_and_nothing_is_written(tmp_path):
    with pytest.raises(pf.page().PageError):
        pf.build(tmp_path, pf.synthetic_rows(), kind="verdict")
    assert not (tmp_path / "out" / "index.html").exists() and not (tmp_path / "out" / "artifacts-row.md").exists()
