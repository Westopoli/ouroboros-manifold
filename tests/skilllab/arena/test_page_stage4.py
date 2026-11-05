# spec: docs/northstar/plans/cascades/lab-stage4/spec.md::Acceptance criteria::AC-10
# Rule pins: none (lab harness story H-088)
"""lab-stage4 leaf-03, criteria 10 and 11 (spec lines 34 and 35): the stage 4 page (scripts/skilllab/arena/page.py).

10: the control caption is chosen from the two documents: a control whose `sight` is `off` while the main fight's is `on` reads
    `control: the same fight with everyone seeing everyone (sight off)`; otherwise today's ground caption. `--stage 4` prints the header `Stage 4, sight`.
11: every row, rated or not, gains `first seen A <tick|never>  B <tick|never>` beside the first-shot line, from `result.first_seen` (`-` when the key is absent).

The fight files are hand-written (snapshot.example with `sight`, `result.first_seen` set; the staging helpers are those of test_page_stage3.py). `page.build` reads them
through `snapshot.read`, whose checker learns `first_seen` in leaf A (criterion 3), a different leaf's file: so `snapshot.validate` is made to accept everything for the
duration of each test here (the checker is tested in test_stage4_snapshot.py, not through the page). The first-seen line is looked for in the page source, with its two
spaces, as the umbrella test does; the captions are read the way a person reads the page (test_page_stage3.visible).

Controls (green today, must stay green): a control that is not sight off, or a main fight that is not sight on, keeps the ground caption."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_page_stage3 import CAPTION as GROUND, LAYOUT, OWN, _png, visible  # noqa: E402
from scripts.skilllab.arena import page, snapshot  # noqa: E402
from scripts.skilllab.arena.rate import rate  # noqa: E402

SIGHT = "control: the same fight with everyone seeing everyone (sight off)"


@pytest.fixture(autouse=True)
def _checker_accepts_the_stage4_keys(monkeypatch):
    monkeypatch.setattr(snapshot, "validate", lambda doc: [])


def fight(directory, stem, lid, layout_path, seed, sight, first_seen=..., ticks=None):
    """Write `<stem>.fight.json` (raw JSON) and three PNG frames; `first_seen` Ellipsis leaves the key out of `result`; `ticks` sets `result.ticks` (the rate file's median
    seed is the middle one of the seeds ordered by ticks)."""
    doc = snapshot.example(frames=3, units_per_side=2, schema=snapshot.SCHEMA_V2)
    doc["layout_id"], doc["layout_path"], doc["seed"], doc["sight"] = lid, str(layout_path), seed, sight
    if ticks is not None:
        doc["result"]["ticks"] = ticks
    doc["result"]["predict"], doc["result"]["agree"] = "A", doc["result"]["winner"] == "A"
    if first_seen is not ...:
        doc["result"]["first_seen"] = first_seen
    (directory / (stem + ".fight.json")).write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")
    (directory / stem).mkdir()
    for i in range(3):
        _png(directory / stem / ("frame-%d.png" % i))
    return doc


def stage(tmp_path, lid="L-9501", seeds=(1,), main_sight="on", first_seen=..., per_seed=None, controls=None, rated=False, ticks=None):
    """(out dir, control dir): fights `<lid>-s<n>` for `seeds` (sight `main_sight`, `first_seen` as given for all, or `per_seed` {seed: first_seen}, `result.ticks` per
    `ticks` {seed: ticks}), control fights `<lid>-control-s<n>` for the {seed: control sight} in `controls`, rated: plus the rate file."""
    root = tmp_path / "repo"
    out, control = root / "out", root / "control"
    for d in (out, control, root / "layouts"):
        d.mkdir(parents=True)
    layout = root / "layouts" / (lid + ".toml")
    layout.write_text(LAYOUT.format(lid=lid, own="".join('%s = "%s"\n' % kv for kv in OWN.items())))
    docs = [fight(out, "%s-s%d" % (lid, s), lid, layout, s, main_sight, (per_seed or {}).get(s, first_seen), (ticks or {}).get(s)) for s in seeds]
    for s, sight in (controls or {}).items():
        fight(control, "%s-control-s%d" % (lid, s), lid, layout, s, sight)
    if rated:
        (out / (lid + ".rate.json")).write_text(json.dumps(rate(docs, 0.98), indent=2) + "\n")
    return out, control


def build(out, **kw):
    target = out.parent / "index.html"
    assert page.build(str(out), str(target), **kw) == 0
    return target.read_text()


# ---------------------------------------------------------------- criterion 10: header and caption

@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_stage_4_prints_its_header(rated, tmp_path):
    """Criterion 10, spec line 34: `--stage 4` prints the header `Stage 4, sight`, on an unrated page and on a rated one."""
    out, _ = stage(tmp_path, rated=rated)
    assert "Stage 4, sight" in visible(build(out, stage=4))


def test_the_cli_flag_stage_4_prints_the_header(tmp_path):
    """Criterion 10 through `page.main`: `--stage 4` gives the header and exit code 0."""
    out, control = stage(tmp_path, controls={1: "off"})
    target = tmp_path / "cli.html"
    assert (page.main(["--dir", str(out), "--out", str(target), "--control-dir", str(control), "--stage", "4"]), "Stage 4, sight" in visible(target.read_text())) == (0, True)


@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_a_sight_off_control_of_a_sight_on_fight_gets_the_sight_caption(rated, tmp_path):
    """Criterion 10, spec line 34: the control document's `sight` is `off` and the main fight's is `on`: the strip reads the sight caption, once, and not the ground one."""
    out, control = stage(tmp_path, controls={1: "off"}, rated=rated)
    text = visible(build(out, control_dir=str(control), stage=4))
    assert (text.count(SIGHT), GROUND in text) == (1, False)


@pytest.mark.parametrize("main,control", [("off", "off"), ("on", "on"), ("off", "on")], ids=["both-off", "both-on", "main-off-control-on"])
def test_control_every_other_pair_keeps_the_ground_caption(main, control, tmp_path):
    """CONTROL (green today, must stay green), criterion 10 "otherwise today's ground caption": any pair of documents but (main on, control off) reads the ground caption."""
    out, ctl = stage(tmp_path, main_sight=main, controls={1: control})
    text = visible(build(out, control_dir=str(ctl)))
    assert (text.count(GROUND), SIGHT in text) == (1, False)


def test_the_caption_is_chosen_per_control_file(tmp_path):
    """Criterion 10: "chosen from the two documents": two unrated seeds of one layout, the seed 1 control sight off and the seed 2 control sight on, give one sight caption
    and one ground caption."""
    out, control = stage(tmp_path, seeds=(1, 2), controls={1: "off", 2: "on"})
    text = visible(build(out, control_dir=str(control)))
    assert (text.count(SIGHT), text.count(GROUND)) == (1, 1)


# ---------------------------------------------------------------- criterion 11: the first-seen line

@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
@pytest.mark.parametrize("first_seen,words", [({"A": 140, "B": None}, "first seen A 140  B never"), ({"A": None, "B": 60}, "first seen A never  B 60"),
                                              ({"A": 0, "B": 0}, "first seen A 0  B 0")], ids=["b-never", "a-never", "tick-zero"])
def test_every_row_prints_the_first_seen_line(first_seen, words, rated, tmp_path):
    """Criterion 11, spec line 35: a row (unrated, or a rated layout's block) prints `first seen A <tick|never>  B <tick|never>` from `result.first_seen`: null is `never`,
    a tick of 0 is printed as 0."""
    out, _ = stage(tmp_path, first_seen=first_seen, rated=rated)
    assert words in build(out, stage=4)


@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_a_fight_without_first_seen_prints_a_dash(rated, tmp_path):
    """Criterion 11, spec line 35 (ruling Q3): "the line is `first seen A -  B -` when the key is absent": exactly that, and neither `never` nor a tick."""
    out, _ = stage(tmp_path, rated=rated)
    raw = build(out, stage=4)
    assert ("first seen A -  B -" in raw, "never" in visible(raw)) == (True, False)


def test_each_row_prints_its_own_seeds_first_seen(tmp_path):
    """Criterion 11: "every row": two unrated seeds with different `first_seen` print their own line each."""
    out, _ = stage(tmp_path, seeds=(1, 2), per_seed={1: {"A": 20, "B": None}, 2: {"A": None, "B": 80}})
    raw = build(out, stage=4)
    assert ("first seen A 20  B never" in raw, "first seen A never  B 80" in raw) == (True, True)


@pytest.mark.parametrize("ticks,median", [({1: 200, 2: 100, 3: 300}, 1), ({1: 300, 2: 100, 3: 200}, 3), ({}, 2)], ids=["median-seed-1", "median-seed-3", "median-seed-2"])
def test_a_rated_block_prints_the_median_seeds_first_seen_and_no_other(ticks, median, tmp_path):
    """Criterion 11, spec line 35 (ruling Y5): "in a rated block the line is the median seed's, the seed whose strip the block shows": three rated seeds with different
    `first_seen`; the median seed (the middle one by `result.ticks`, ties to the lower seed: 2 when the ticks are equal) is printed and neither of the other two is, so the line
    is not the first seed's, the last seed's, the middle number's, nor every seed's."""
    lines = {1: ({"A": 20, "B": None}, "first seen A 20  B never"), 2: ({"A": 40, "B": 80}, "first seen A 40  B 80"), 3: ({"A": None, "B": 60}, "first seen A never  B 60")}
    out, _ = stage(tmp_path, seeds=(1, 2, 3), per_seed={s: v[0] for s, v in lines.items()}, rated=True, ticks=ticks)
    raw = build(out, stage=4)
    assert {s: v[1] in raw for s, v in lines.items()} == {s: s == median for s in lines}
