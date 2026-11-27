# Rule pins: R-091-12 (lab harness story H-091, lab stage 5, piece L1)
"""LAB stage 5, piece L1 (story H-091), R-091-12: `snapshot.validate` and `SNAPSHOT.md` for the three stage 5 additions.

  R-091-12  The snapshot checker accepts the three additions and still rejects an unknown key; `SNAPSHOT.md` describes them.

The three additions (R-091-09, R-091-10, R-091-11): the top-level `stage5` {arc_deg, slope_up_div, front_deg, rear_deg} (numbers), the per-unit `climbing` (a number), and the per-frame
`hits` (a list of {a, v, tick, off_deg, cls}: ints, a number, and cls front, side or rear). Like the stage 4 keys they belong to `om-fight-2`: accepted absent or present there, refused on an
`om-fight-1` document naming the key. The stories give no range for `climbing` and no bound for the numbers: only types and the three class names are tested.
`SNAPSHOT.md` is both files of that name: scripts/skilllab/arena/SNAPSHOT.md (the additions of the arena package, where the stage 4 test looks) and
docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md (the file readers open, which today still says stage 5 `climbing` is `transition_progress`, which reads 0 for a walker: the
stale-doc tripwire wants that sentence rewritten with the change).
Controls (green today, must stay green): a v2 document with none of the keys is valid; the unknown-key rejections of the existing levels; every stage 5 key is refused on a v1 document
(unknown to every schema today), and an unknown key is refused beside well-typed stage 5 keys."""
import re

import pytest

import h063_fixtures as fx
import h091_fixtures as f9
from scripts.skilllab.arena import snapshot

STAGE5 = {"arc_deg": 90, "slope_up_div": 1.1, "front_deg": 45, "rear_deg": 135}
HIT = {"a": 3, "v": 1, "tick": 4, "off_deg": 91.5, "cls": "side"}


def v2(stage5=True, climbing=True, hits=True, **extra):
    """An om-fight-2 example with the wanted stage 5 keys: `climbing` 0.0 on every row but unit 1's (0.5), `hits` [HIT] on the last frame and [] on the others."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    if stage5:
        doc["stage5"] = dict(STAGE5)
    for n, frame in enumerate(doc["frames"]):
        if hits:
            frame["hits"] = [dict(HIT)] if n == len(doc["frames"]) - 1 else []
        if climbing:
            for u in frame["units"]:
                u["climbing"] = 0.5 if u["id"] == 1 else 0.0
    doc.update(extra)
    return doc


def test_validate_accepts_the_stage5_keys_present_and_absent_on_v2():
    """R-091-12: "The snapshot checker accepts the three additions": all three together validate, each alone validates, and a v2 document with none still validates (CONTROL part: the
    last one is green today)."""
    docs = [v2(), v2(climbing=False, hits=False), v2(stage5=False, hits=False), v2(stage5=False, climbing=False), snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)]
    assert [snapshot.validate(d) for d in docs] == [[]] * 5


@pytest.mark.parametrize("key", ["stage5", "climbing", "hits"])
def test_control_each_stage5_key_is_refused_on_a_v1_document_naming_it(key):
    """CONTROL (green today, must stay green): the stage 5 keys are unknown to `om-fight-1`; each set on a v1 example gives a message that names it."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA)
    if key == "stage5":
        doc["stage5"] = dict(STAGE5)
    elif key == "climbing":
        doc["frames"][0]["units"][0]["climbing"] = 0.5
    else:
        doc["frames"][0]["hits"] = []
    assert any(key in e for e in snapshot.validate(doc)), snapshot.validate(doc)


BAD = {"stage5": [[90], {"arc_deg": "90", "slope_up_div": 1.1, "front_deg": 45, "rear_deg": 135}, {"arc_deg": 90, "slope_up_div": 1.1, "front_deg": 45},
                  {"arc_deg": 90, "slope_up_div": 1.1, "front_deg": 45, "rear_deg": 135, "extra": 1}, {"arc_deg": True, "slope_up_div": 1.1, "front_deg": 45, "rear_deg": 135}]}


@pytest.mark.parametrize("bad", BAD["stage5"])
def test_validate_rejects_a_badly_typed_or_incomplete_stage5_table_naming_it(bad):
    """R-091-12 ("still rejects an unknown key"): `stage5` not a table, with a string or a bool for a number, with a key missing, or with a fifth key is refused with a message naming
    `stage5`, while the well-typed document is accepted (so the refusal is for the value, not for an unknown top-level key)."""
    assert snapshot.validate(v2()) == []
    doc = v2(stage5=False)
    doc["stage5"] = bad
    assert any("stage5" in e for e in snapshot.validate(doc)), snapshot.validate(doc)


@pytest.mark.parametrize("bad", ["0.5", None, True, [0.5]])
def test_validate_rejects_a_badly_typed_climbing_naming_it(bad):
    """R-091-12: `climbing` that is not a number (a string, null, a bool, a list) is refused naming `climbing`; the well-typed document is accepted."""
    assert snapshot.validate(v2()) == []
    doc = v2()
    doc["frames"][1]["units"][0]["climbing"] = bad
    assert any("climbing" in e for e in snapshot.validate(doc)), snapshot.validate(doc)


HIT_BAD = [{"a": 3, "v": 1, "tick": 4, "off_deg": 91.5, "cls": "flank"}, {"a": "3", "v": 1, "tick": 4, "off_deg": 91.5, "cls": "side"}, {"a": 3, "v": 1, "tick": 4.5, "off_deg": 91.5, "cls": "side"},
           {"a": 3, "v": 1, "tick": 4, "off_deg": "91", "cls": "side"}, {"a": 3, "v": 1, "tick": 4, "off_deg": 91.5}, {"a": 3, "v": 1, "tick": 4, "off_deg": 91.5, "cls": "side", "extra": 1}, 7]


@pytest.mark.parametrize("bad", HIT_BAD)
def test_validate_rejects_a_bad_hit_entry_naming_hits(bad):
    """R-091-12: a `hits` entry with a cls other than front, side or rear, a string or float where an int belongs, a string off_deg, a key missing, a fifth key, or not a table is refused
    with a message naming `hits`; the well-typed entry (side, 91.5) is accepted."""
    assert snapshot.validate(v2()) == []
    doc = v2()
    doc["frames"][2]["hits"] = [bad]
    assert any("hits" in e for e in snapshot.validate(doc)), snapshot.validate(doc)


@pytest.mark.parametrize("cls", ["front", "side", "rear"])
def test_validate_accepts_each_hit_class(cls):
    """R-091-12: the three class names are each accepted."""
    doc = v2()
    doc["frames"][2]["hits"] = [dict(HIT, cls=cls)]
    assert snapshot.validate(doc) == []


def test_validate_rejects_hits_that_is_not_a_list_naming_it():
    """R-091-12: `hits` as a table or a number is refused naming `hits`; the well-typed document is accepted."""
    assert snapshot.validate(v2()) == []
    for bad in ({"a": 1}, 3):
        doc = v2()
        doc["frames"][1]["hits"] = bad
        assert any("hits" in e for e in snapshot.validate(doc)), (bad, snapshot.validate(doc))


def test_control_validate_still_rejects_an_unknown_key_at_every_level_beside_the_stage5_keys():
    """R-091-12 CONTROL (green today, must stay green): "still rejects an unknown key": a bogus key at the top level, on a frame, on a unit row, each beside well-typed stage 5 keys, is refused naming the bogus key."""
    top, frame, unit = v2(), v2(), v2()
    top["bogus"] = 1
    frame["frames"][0]["bogus"] = 1
    unit["frames"][0]["units"][0]["bogus"] = 1
    for doc, where in ((top, "bogus"), (frame, "frames[0].bogus"), (unit, "units[0].bogus")):
        assert any("unknown key" in e and where in e for e in snapshot.validate(doc)), (where, snapshot.validate(doc))


def test_a_written_stage5_document_reads_back(tmp_path):
    """R-091-12: `snapshot.write` then `snapshot.read` (which validates) round-trips a document carrying the three additions."""
    path = tmp_path / "x.fight.json"
    snapshot.write(v2(), path)
    got = snapshot.read(path)
    assert (got["stage5"], got["frames"][0]["units"][0]["climbing"], got["frames"][2]["hits"]) == (STAGE5, 0.5, [HIT])


def test_a_real_facing_on_fight_file_validates_and_reads_back(tmp_path):
    """R-091-12 through the runner (integration): `run.py --facing on` writes a file that `snapshot.read` (the writer's own gate, so the run exits 0) accepts and that carries all three
    additions; run through the real engine on the FLANK scene."""
    proc, doc = fx.fight(f9.flank_layout("L-9531", "north"), tmp_path, 1, "--facing", "on")
    assert proc.returncode == 0 and doc is not None, "run.py --facing on: exit %s, %s %s" % (proc.returncode, proc.stdout[-200:], proc.stderr[-300:])
    assert "stage5" in doc and all("climbing" in u for f in doc["frames"] for u in f["units"]) and all("hits" in f for f in doc["frames"])
    assert snapshot.validate(doc) == []


DOCS = {"scripts": fx.ROOT / "scripts" / "skilllab" / "arena" / "SNAPSHOT.md", "docs": fx.ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "arena" / "SNAPSHOT.md"}


@pytest.mark.parametrize("which", list(DOCS))
def test_snapshot_md_describes_the_stage5_additions(which):
    """R-091-12: "`SNAPSHOT.md` describes them": the file names `stage5` with its four keys (`arc_deg`, `slope_up_div`, `front_deg`, `rear_deg`), `climbing`, `hits` with its entry keys
    (`off_deg`, `cls`) and the three class names, and the switches `--facing` and `--arc-deg`."""
    text = DOCS[which].read_text()
    needed = ["stage5", "arc_deg", "slope_up_div", "front_deg", "rear_deg", "climbing", "hits", "off_deg", "cls", "front", "side", "rear", "--facing", "--arc-deg"]
    missing = [w for w in needed if not re.search(r"(?<![\w-])" + re.escape(w) + r"(?!\w)", text)]
    assert missing == [], "%s lacks %s" % (DOCS[which].relative_to(fx.ROOT), missing)


def test_snapshot_md_no_longer_says_climbing_is_transition_progress():
    """R-091-12 and the stale-doc rule: docs/northstar/research/layer_dynamics/arena/SNAPSHOT.md says "Stage 5 adds `climbing` (float 0 to 1, `transition_progress`)"; the story computes
    `climbing` from the slope's record and the unit's position, because `transition_progress` reads 0 for a walker. The sentence is rewritten, so `transition_progress` is not given as the
    source of `climbing` in either SNAPSHOT.md."""
    stale = [name for name, p in DOCS.items() if re.search(r"climbing[^.\n]*transition_progress", p.read_text())]
    assert stale == [], "still says climbing is transition_progress: %s" % stale
