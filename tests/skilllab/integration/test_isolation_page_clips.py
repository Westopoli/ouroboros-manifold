# spec: docs/northstar/plans/lab-isolation-2026-11-24/spec.md section 6 ("MP4 clips of the decisive runs ... Each clip is captioned with layout, seed, version, tick range and its row on the table"), piece LI5 part 1
"""Clips on the page. Input: a manifest of clip sets, each a list of the clip pipeline's `facts.json` files (docs/reports/2026-11-24-clip-pipeline-interface.md); the media are fake bytes here (the
page copies, it never decodes). A set of two to four versions is a synced grid as in A-003; a set of one is a single clip. Interface: docs/reports/2026-11-24-li5-interface.md.
Red today: `scripts/skilllab/arena/isolation_page.py` does not exist."""
import filecmp
import json
import re

import pytest

import isolation_page_fixtures as pf


def render(tmp_path, sets):
    manifest = pf.clip_dir(tmp_path / "src", sets)
    out, _ = pf.build(tmp_path, pf.synthetic_rows(), clips=manifest)
    return pf.page_root(out), out, tmp_path / "src"


def test_four_versions_make_a_synced_four_up_grid(tmp_path):
    root, out, _ = render(tmp_path, [("l0084-four", "L-0084", "changed", ["then", "now", "fix", "alt"])])
    sec = root.one("section", id="l0084-four")
    (grid,) = sec.find("div", data_bench="true")
    assert len(grid.find("video")) == 4 and "bench" in grid.cls() and "grid" in grid.cls()
    assert grid.attrs["data-first"] == "0" and grid.attrs["data-last"] == "2098"
    (transport,) = [n for n in sec.find("div") if "transport" in n.cls()]
    assert transport.find(data_scrub=True) and transport.find(data_play=True)
    assert pf.problems_media(root, out) == []


def test_two_versions_are_a_grid_and_one_is_a_single_clip(tmp_path):
    root, out, _ = render(tmp_path, [("two", "L-0055", "same", ["then", "now"]), ("one", "L-0102", "l0102", ["now"])])
    two, one = root.one("section", id="two"), root.one("section", id="one")
    assert len(two.find("video")) == 2 and two.find("div", data_bench="true")
    assert len(one.find("video")) == 1 and not one.find("div", data_bench="true") and not [n for n in one.find("div") if "transport" in n.cls()]
    assert "controls" in one.one("video").attrs          # a single clip has its own controls


def test_more_than_four_versions_is_refused_and_nothing_is_written(tmp_path):
    manifest = pf.clip_dir(tmp_path / "src", [("five", "L-0084", "changed", ["a", "b", "c", "d", "e"])])
    with pytest.raises(pf.page().PageError):
        pf.build(tmp_path, pf.synthetic_rows(), clips=manifest)
    assert not (tmp_path / "out" / "index.html").exists()


def test_every_src_and_poster_is_relative_and_the_file_is_in_the_output_with_the_same_bytes(tmp_path):
    root, out, src = render(tmp_path, [("two", "L-0055", "same", ["then", "now"])])
    assert pf.problems_media(root, out) == []
    for v in root.find("video"):
        name = v.attrs["src"].rsplit("/", 1)[-1]
        assert filecmp.cmp(out / v.attrs["src"], src / "src" / name, shallow=False)
        assert filecmp.cmp(out / v.attrs["poster"], src / "src" / name.replace(".mp4", "-poster.jpg"), shallow=False)
    assert pf.all_problems((out / "index.html").read_text(), out) == []


def test_caption_has_layout_seed_version_tick_range_and_table_row(tmp_path):
    """spec 6: "captioned with layout, seed, version, tick range and its row on the table"."""
    root, _, _ = render(tmp_path, [("two", "L-0084", "changed", ["then", "now"])])
    figs = root.one("section", id="two").find("figure")
    assert len(figs) == 2
    for fig, version in zip(figs, ("then", "now")):
        cap = fig.one("figcaption").text()
        assert "L-0084" in cap and "seed 10" in cap and version in cap and "0" in cap and "2098" in cap and "row L-0084" in cap
    assert "changed" in root.one("section", id="two").text()


def test_clip_sets_keep_the_manifest_order_and_the_facts_order(tmp_path):
    root, _, _ = render(tmp_path, [("z-first", "L-0055", "same", ["now", "then"]), ("a-second", "L-0084", "changed", ["then", "now"])])
    ids = [n.attrs["id"] for n in root.one("section", data_section="clips").find("section") if "id" in n.attrs]
    assert ids == ["z-first", "a-second"]
    assert [v.attrs["src"].rsplit("/", 1)[-1] for v in root.one("section", id="z-first").find("video")] == ["z-first-now.mp4", "z-first-then.mp4"]


def test_the_engine_sha_of_a_clip_is_on_the_page(tmp_path):
    root, _, _ = render(tmp_path, [("one", "L-0055", "same", ["now", "alt"])])
    assert "0" * 40 in root.one("section", data_section="shas").text()          # the `alt` clip's facts carry engine_sha 40 zeros (fixtures.facts); no row has it


def test_a_clip_file_missing_is_an_error_and_nothing_is_written(tmp_path):
    manifest = pf.clip_dir(tmp_path / "src", [("one", "L-0055", "same", ["now"])])
    (tmp_path / "src" / "src" / "one-now.mp4").unlink()
    with pytest.raises(pf.page().PageError) as e:
        pf.build(tmp_path, pf.synthetic_rows(), clips=manifest)
    assert "one-now.mp4" in str(e.value) and not (tmp_path / "out" / "index.html").exists()


def test_a_facts_file_missing_a_key_the_page_reads_is_an_error(tmp_path):
    manifest = pf.clip_dir(tmp_path / "src", [("one", "L-0055", "same", ["now"])])
    p = tmp_path / "src" / "src" / "one-now.facts.json"
    d = json.loads(p.read_text())
    del d["first_tick"]
    p.write_text(json.dumps(d))
    with pytest.raises(pf.page().PageError) as e:
        pf.build(tmp_path, pf.synthetic_rows(), clips=manifest)
    assert "first_tick" in str(e.value)


def test_no_manifest_means_no_clips_section_and_no_video(tmp_path):
    out, _ = pf.build(tmp_path, pf.synthetic_rows())
    root = pf.page_root(out)
    assert not root.find("video") and not root.find(data_section="clips") and sorted(p.name for p in out.iterdir()) == ["artifacts-row.md", "index.html"]
