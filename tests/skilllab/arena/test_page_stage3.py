# spec: docs/northstar/plans/cascades/lab-stage3/spec.md::Acceptance criteria::AC-10
# Rule pins: none (lab harness story H-063)
"""lab-stage3 leaf-03, criteria 10 and 11 (spec lines 38 and 39): the stage page (scripts/skilllab/arena/page.py).

10: `build(d, out, control_dir=None, stage=None, sentences=None)` and the CLI flags `--stage N` and `--sentences <md>`: the header names the stage (3: "Stage 3, the
    ground pushes back"; 2: "Stage 2, roles and ranges"; otherwise "Stage N"), the words "not landed" and "pre-scale-lock" are gone; a sentences markdown table
    `| id | What to expect | Approve means | Deny means |` overrides the layout's own `what_to_expect`, `approve_means`, `deny_means`; a layout with neither shows `-`.
11: every fight (rated or not) whose control fight file exists in `--control-dir` for its seed gets the control strip with the caption "control: the same fight without
    the ground (features emptied)"; unrated rows get the three sentences and `blocked unit-frames: n`, n = sum of len(frame["blocked"]); a rated block shows the line too.

The page text is read the way a person reads it: tags removed, entities decoded, white space collapsed."""
import html
import json
import re
import struct
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.arena import page, snapshot  # noqa: E402
from scripts.skilllab.arena.rate import rate  # noqa: E402

CAPTION = "control: the same fight without the ground (features emptied)"
OWN = {"what_to_expect": "OWN-EXPECT red queues.", "approve_means": "OWN-APPROVE walls hold.", "deny_means": "OWN-DENY a wall is crossed."}
FILE = {"what_to_expect": "FILE-EXPECT red files in.", "approve_means": "FILE-APPROVE the gap queues.", "deny_means": "FILE-DENY a unit is inside."}
LABELS = ("What to expect", "Approve means", "Deny means")

LAYOUT = """id = "{lid}"
situation = "chokepoint"
landscape = "small_flat"
seed = 1
predict = "A"
predict_why = "WHYCHOKE blue holds the exit."
verdict = ""
feedback = ""
predict_rate = 0.98
{own}
[side_a]
headcount = 2

[side_b]
headcount = 2
"""


def _png(path):
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")) + chunk(b"IEND", b""))


def _fight(directory, stem, lid, layout_path, seed, blocked=None):
    doc = snapshot.example(frames=3, units_per_side=2, schema=snapshot.SCHEMA_V2)
    doc["layout_id"], doc["layout_path"], doc["seed"] = lid, str(layout_path), seed
    doc["result"]["predict"], doc["result"]["agree"] = "A", doc["result"]["winner"] == "A"
    for i, ids in (blocked or {}).items():
        doc["frames"][i]["blocked"] = ids
    snapshot.write(doc, directory / (stem + ".fight.json"))
    (directory / stem).mkdir()
    for i in range(3):
        _png(directory / stem / ("frame-%d.png" % i))
    return doc


def stage(tmp_path, lid="L-9501", seeds=(1,), own=True, blocked=None, control_seeds=(), rated=False):
    """(out dir, control dir, layout path): fights `<lid>-s<n>` for `seeds` in out (rated: plus `<lid>.rate.json`), control fights `<lid>-control-s<n>` for
    `control_seeds` in the control dir, all with PNGs; the layout TOML carries its own three sentences when `own`."""
    root = tmp_path / "repo"
    out, control = root / "out", root / "control"
    for d in (out, control, root / "layouts"):
        d.mkdir(parents=True)
    layout = root / "layouts" / (lid + ".toml")
    layout.write_text(LAYOUT.format(lid=lid, own="".join('%s = "%s"\n' % kv for kv in OWN.items()) if own else ""))
    docs = [_fight(out, "%s-s%d" % (lid, s), lid, layout, s, blocked) for s in seeds]
    for s in control_seeds:
        _fight(control, "%s-control-s%d" % (lid, s), lid, layout, s)
    if rated:
        (out / (lid + ".rate.json")).write_text(json.dumps(rate(docs, 0.98), indent=2) + "\n")
    return out, control, layout


def build(out, **kw):
    target = out.parent / "index.html"
    assert page.build(str(out), str(target), **kw) == 0
    return target.read_text()


def visible(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text)))


def sentences_file(tmp_path, rows):
    path = tmp_path / "sentences.md"
    path.write_text("# sentences\n\n| id | What to expect | Approve means | Deny means |\n|---|---|---|---|\n" + "".join("| %s | %s | %s | %s |\n" % r for r in rows))
    return path


# ---------------------------------------------------------------- criterion 10: the header

@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
@pytest.mark.parametrize("number,words", [(3, "Stage 3, the ground pushes back"), (2, "Stage 2, roles and ranges"), (4, "Stage 4"), (1, "Stage 1")])
def test_header_names_the_stage_and_drops_the_old_words(number, words, rated, tmp_path):
    """Criterion 10, spec line 38: `--stage N` sets the header; 3 and 2 have their words, any other number reads `Stage N` (and neither of the two sets of words);
    "not landed" and "pre-scale-lock" are gone."""
    out, _, _ = stage(tmp_path, rated=rated)
    text = visible(build(out, stage=number))
    assert words in text
    if number not in (2, 3):
        assert "ground pushes back" not in text and "roles and ranges" not in text
    assert "not landed" not in text and "pre-scale-lock" not in text


def test_the_old_header_words_are_gone_without_a_stage_too(tmp_path):
    """Criterion 10: the words "not landed" and "pre-scale-lock" go, whatever `--stage` says; a rated page built with no stage carries neither."""
    out, _, _ = stage(tmp_path, rated=True)
    text = visible(build(out))
    assert "not landed" not in text and "pre-scale-lock" not in text


# ---------------------------------------------------------------- criterion 10: the sentences file

@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_sentences_file_row_overrides_the_layouts_own_sentences(rated, tmp_path):
    """Criterion 10, spec line 38: a row for the layout id overrides the layout keys, in the unrated row and the rated block alike; the layout's own words are not
    shown beside them."""
    out, _, _ = stage(tmp_path, rated=rated)
    text = visible(build(out, stage=3, sentences=str(sentences_file(tmp_path, [("L-9501", FILE["what_to_expect"], FILE["approve_means"], FILE["deny_means"])]))))
    for key in FILE:
        assert FILE[key] in text and OWN[key] not in text, key


def test_a_layout_without_a_sentences_row_keeps_its_own_sentences(tmp_path):
    """Criterion 10: the file speaks for the ids it lists; a row for another id changes nothing here (the layout keys stay)."""
    out, _, _ = stage(tmp_path)
    text = visible(build(out, stage=3, sentences=str(sentences_file(tmp_path, [("L-0000", FILE["what_to_expect"], FILE["approve_means"], FILE["deny_means"])]))))
    assert all(OWN[k] in text for k in OWN) and not any(FILE[k] in text for k in FILE)


def test_a_layout_with_neither_shows_a_dash_for_each_sentence(tmp_path):
    """Criterion 10 and 11: "a layout with neither shows `-`": an unrated row (which has no sentences today) shows each of the three labels followed by a dash."""
    out, _, _ = stage(tmp_path, own=False)
    text = visible(build(out))
    for label in LABELS:
        assert re.search(re.escape(label) + r"[:\s]*-(?=\s|$)", text), "no dash after %r in %r" % (label, text[-600:])


def test_the_stage3_sentences_file_of_the_repository_is_read(tmp_path):
    """Criterion 10: the real `arena/stage3/sentences.md` is a sentences file; for its first row's id the page shows that row's three cells (the cells read here by
    splitting the table lines, apart from the page)."""
    real = ROOT / "docs/northstar/research/layer_dynamics/arena/stage3/sentences.md"
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in real.read_text().splitlines() if re.match(r"\|\s*L-\d{4}\s*\|", ln)]
    assert len(rows) >= 2
    lid, *cells = rows[0]
    out, _, _ = stage(tmp_path, lid=lid)
    text = visible(build(out, stage=3, sentences=str(real)))
    assert all(visible(c) in text for c in cells) and not any(OWN[k] in text for k in OWN)


# ---------------------------------------------------------------- criterion 11: control strip and blocked

@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_every_fight_with_a_control_file_gets_the_control_strip(rated, tmp_path):
    """Criterion 11, spec line 39: an unrated fight directory (and a rated one) with a control fight in the control dir prints the caption once and the control's three
    frames `<id>-control-s1/frame-<i>.png`; the page also lists the three sentences (from the layout keys) and the blocked line."""
    out, control, _ = stage(tmp_path, control_seeds=(1,), rated=rated)
    raw = build(out, control_dir=str(control))
    text = visible(raw)
    assert text.count(CAPTION) == 1
    assert sorted(set(re.findall(r"L-9501-control-s1/frame-(\d+)\.png", raw))) == ["0", "1", "2"]
    assert all(OWN[k] in text for k in OWN)
    assert "blocked unit-frames: 0" in text   # the fixture fight has no `blocked` key


def test_control_strip_is_matched_by_seed(tmp_path):
    """Criterion 11: "for its seed": two unrated fights (seeds 1 and 2) and a control for seed 1 only give one caption, the seed 1 control's frames and none of seed 2's."""
    out, control, _ = stage(tmp_path, seeds=(1, 2), control_seeds=(1,))
    raw = build(out, control_dir=str(control))
    assert visible(raw).count(CAPTION) == 1
    assert "L-9501-control-s1/frame-0.png" in raw and "control-s2" not in raw


def test_no_control_file_or_no_control_dir_shows_no_control_strip(tmp_path):
    """CONTROL (green today): an unrated fight with an empty control dir, and with no control dir at all, shows no control caption."""
    out, control, _ = stage(tmp_path)
    assert CAPTION not in visible(build(out, control_dir=str(control)))
    assert CAPTION not in visible(build(out))


@pytest.mark.parametrize("rated", [False, True], ids=["unrated", "rated"])
def test_blocked_unit_frames_line_counts_the_blocked_lists(rated, tmp_path):
    """Criterion 11 and 6: `blocked unit-frames: n` with n the sum over the fight's frames of len(frame["blocked"]): 0 + 2 + 3 = 5 here, 0 for a fight with no
    `blocked` key. (A rated layout is one seed here; spec line 39 does not say which seeds a many-seed block counts, see BOUNDARIES.md.)"""
    out, _, _ = stage(tmp_path / "with", blocked={1: [1, 2], 2: [1, 2, 4]}, rated=rated)
    assert "blocked unit-frames: 5" in visible(build(out))
    out, _, _ = stage(tmp_path / "without", rated=rated)
    assert "blocked unit-frames: 0" in visible(build(out))


# ---------------------------------------------------------------- the CLI flags

def test_cli_flags_stage_and_sentences_reach_build(tmp_path):
    """Criteria 10 and 11 through `page.main`: `--control-dir`, `--stage 3` and `--sentences <md>` together give the stage header, the file's sentences and the control
    caption; the exit code is 0."""
    out, control, _ = stage(tmp_path, control_seeds=(1,))
    target = tmp_path / "cli.html"
    md = sentences_file(tmp_path, [("L-9501", FILE["what_to_expect"], FILE["approve_means"], FILE["deny_means"])])
    assert page.main(["--dir", str(out), "--out", str(target), "--control-dir", str(control), "--stage", "3", "--sentences", str(md)]) == 0
    text = visible(target.read_text())
    assert "Stage 3, the ground pushes back" in text and CAPTION in text and FILE["deny_means"] in text
