# spec: docs/northstar/plans/cascades/lab-stage4/spec.md::Acceptance criteria::AC-3
# Rule pins: none (lab harness story H-088)
"""lab-stage4 leaf-01, criterion 3 (spec line 23): `snapshot.validate` and `SNAPSHOT.md` for the sight keys.

3: `validate` accepts `seen` (a list of ints per unit), `sights` (a dict of non-negative numbers), `result.first_seen` (the two keys `A` and `B`, each an int or null)
   and `orders.guard` (a bool) on `om-fight-2`, absent or present, and rejects each on `om-fight-1` naming the key; `SNAPSHOT.md` documents them and the sight-off control.
`validate` returns the list of messages (an empty list is valid), as snapshot.py and every stage 3 test use it; contract.py's `-> None` is the one place that differs.

Controls (green today, must stay green): a v2 document with none of the keys is valid; the four keys are refused on a v1 document (they are unknown to every schema
today). Every rejection of a badly typed value below first requires the well-typed value to be accepted, so none of them passes only because the key is unknown."""
import copy
import re

import pytest

import h063_fixtures as fx   # puts the repository root on sys.path, as every arena test does
from scripts.skilllab.arena import snapshot

SIGHT_KEYS = {"seen": ("units", [3]), "sights": ("top", {"Raider": 0, "Vanguard": 700.5}), "first_seen": ("result", {"A": 0, "B": None}), "guard": ("orders", True)}


def v2(**keys):
    """An om-fight-2 example with the wanted sight keys set (`seen` on every unit: unit 1 lists enemy 3, the rest list none)."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA_V2)
    for key in keys:
        where, _ = SIGHT_KEYS[key]
        if where == "units":
            for f in doc["frames"]:
                for u in f["units"]:
                    u["seen"] = copy.deepcopy(keys[key]) if u["id"] == 1 else []
        elif where == "top":
            doc[key] = keys[key]
        else:
            doc[where][key] = keys[key]
    return doc


def full(**override):
    return v2(**{k: override.get(k, v) for k, (_, v) in SIGHT_KEYS.items()})


def test_validate_accepts_the_sight_keys_present_and_absent_on_v2():
    """Criterion 3: all four keys together validate (sights with a zero radius, the minimum; first_seen with one side null); a second document has the other side null and
    `guard` false; a v2 document with none of the keys still validates (CONTROL part: green today)."""
    other = full(first_seen={"A": None, "B": 140}, guard=False, seen=[])
    assert [snapshot.validate(d) for d in (full(), other, snapshot.example(frames=3, schema=snapshot.SCHEMA_V2))] == [[], [], []]


@pytest.mark.parametrize("key", list(SIGHT_KEYS))
def test_control_the_sight_keys_are_refused_on_a_v1_document_naming_the_key(key):
    """CONTROL (green today, must stay green), criterion 3 "rejects each on `om-fight-1` naming the key": each key set on an om-fight-1 example gives a message that names
    it. `orders.guard` has no `orders` table to sit in on a v1 document, so the refusal there names `orders`."""
    doc = snapshot.example(frames=3, schema=snapshot.SCHEMA)
    where, value = SIGHT_KEYS[key]
    if where == "units":
        doc["frames"][0]["units"][0]["seen"] = value
    elif where == "top":
        doc[key] = value
    else:
        doc[where] = {key: value} if where == "orders" else dict(doc[where], **{key: value})
    errors = snapshot.validate(doc)
    assert errors and any((("orders" if where == "orders" else key) in e) for e in errors), errors


BAD = {"seen": ["3", [1.5], ["3"]], "sights": [{"Raider": -1}, {"Raider": "700"}, ["Raider"]],
       "first_seen": [{"A": 1}, {"A": 1, "B": None, "C": 2}, {"A": 1.5, "B": None}, {"A": "1", "B": None}, [1, None]], "guard": [1, "true", None]}


@pytest.mark.parametrize("key", list(SIGHT_KEYS))
def test_validate_rejects_a_badly_typed_sight_key_naming_it(key):
    """Criterion 3 (Conformance, Range): `seen` not a list of ints, `sights` with a negative or non-number radius or not a dict, `first_seen` without both keys A and B, with
    a third key, or with a non-int tick, `guard` not a bool: each is refused with a message naming the key, while the well-typed document is accepted (so the refusal
    is for the type, not for an unknown key)."""
    assert snapshot.validate(full()) == []
    missed = []
    for bad in BAD[key]:
        errors = snapshot.validate(full(**{key: bad}))
        if not any(key in e for e in errors):
            missed.append((bad, errors))
    assert missed == []


def test_a_written_sight_document_reads_back(tmp_path):
    """Criterion 3: `snapshot.write` then `snapshot.read` (which validates) round-trips a document carrying the four keys."""
    path = tmp_path / "x.fight.json"
    snapshot.write(full(), path)
    got = snapshot.read(path)
    assert (got["sights"], got["result"]["first_seen"], got["orders"]["guard"], got["frames"][0]["units"][0]["seen"]) == ({"Raider": 0, "Vanguard": 700.5}, {"A": 0, "B": None}, True, [3])


def test_snapshot_md_documents_the_sight_keys_and_the_sight_off_control():
    """Criterion 3, spec line 23: `scripts/skilllab/arena/SNAPSHOT.md` documents `seen`, `sights`, `first_seen`, `guard` and the sight-off control (`--control sight`)."""
    text = (fx.ROOT / "scripts" / "skilllab" / "arena" / "SNAPSHOT.md").read_text()
    missing = [w for w in ("first_seen", "sights", "guard", "--control sight") if w not in text]
    if not re.search(r"(?<!\w)seen(?!\w)", text):
        missing.append("seen")
    assert missing == []
