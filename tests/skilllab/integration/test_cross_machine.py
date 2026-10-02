# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-26
"""AC 26 cross-machine: the rows of the three controls hash to tests/skilllab/golden_hashes.json.

The file is written on the first machine (SKILLAB_WRITE_GOLDEN=1) and must match on the second.
SKILLAB_WRITE_GOLDEN=1 refuses to overwrite an existing file; only SKILLAB_WRITE_GOLDEN=force does.
The planted hash covers the rows of every fight in the identical and damage scans (8..24) and both
scans' beats and loses_to, the same two scans the `controls` command runs.
A mismatch is a determinism finding to report to the design chat, never a value to patch.
"""
import hashlib
import json
import os
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine, plays, rows, scan  # noqa: E402

GOLDEN = ROOT / "tests" / "skilllab" / "golden_hashes.json"
REPLICATES = 10
KEYS = ("mirror", "numbers", "planted")


ENEMY_FROM, ENEMY_TO = 8, 24


def _csv_hash(tmp_path, name, row_list):
    path = tmp_path / (name + ".csv")
    rows.write_rows(row_list, path)
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _cell_rows(name, cell_result):
    return [rows.fight_row(f, play=name, enemy_heads=cell_result.enemy_heads) for f in cell_result.fights]


def _scan_rows(label, scan_result):
    return [r for c in scan_result.cells for r in _cell_rows(label, c)]


def _label_free(fights):
    return [rows.fight_row(f) for f in fights]


@pytest.fixture(scope="module")
def controls():
    """The fights of the three controls: mirror (cell 16), numbers (cell 8), planted (both scans)."""
    engine.Engine()
    mirror = scan.cell(plays.blob_play(16), 16, REPLICATES)
    numbers = scan.cell(plays.blob_play(16), 8, REPLICATES)
    identical = scan.scan(plays.blob_play(16), 16, ENEMY_FROM, ENEMY_TO, REPLICATES)
    damage = scan.scan(plays.damage_play(16), 16, ENEMY_FROM, ENEMY_TO, REPLICATES)
    return {"mirror": mirror, "numbers": numbers, "identical": identical, "damage": damage}


@pytest.fixture(scope="module")
def hashes(controls, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("cross_machine")
    planted_rows = _scan_rows("identical", controls["identical"]) + _scan_rows("damage", controls["damage"])
    planted = hashlib.sha256()
    planted.update(_csv_hash(tmp, "planted", planted_rows).encode())
    planted.update(json.dumps({
        "identical": [controls["identical"].beats, controls["identical"].loses_to],
        "damage": [controls["damage"].beats, controls["damage"].loses_to],
    }, sort_keys=True).encode())
    return {
        "mirror": _csv_hash(tmp, "mirror", _cell_rows("mirror", controls["mirror"])),
        "numbers": _csv_hash(tmp, "numbers", _cell_rows("numbers", controls["numbers"])),
        "planted": planted.hexdigest(),
    }


@pytest.fixture(scope="module")
def golden_written(hashes):
    """True when this run wrote the golden file. Refuses to overwrite an existing one unless force."""
    mode = os.environ.get("SKILLAB_WRITE_GOLDEN")
    if mode not in ("1", "force"):
        return False
    if mode == "1" and GOLDEN.exists():
        pytest.fail("golden_hashes.json already exists; AC 26 forbids patching it. Delete it deliberately, "
                    "or set SKILLAB_WRITE_GOLDEN=force, to rewrite it")
    GOLDEN.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    return True


def test_control_hashes_are_distinct(hashes):
    """AC 26 positive control: the three controls hash differently, so a match is not vacuous."""
    assert len(set(hashes.values())) == len(KEYS), hashes
    assert all(len(h) == 64 for h in hashes.values())


def test_control_hashes_are_distinct_without_labels(controls, tmp_path):
    """AC 26 positive control, non-vacuous: with no play or enemy_heads label, the rows of the three controls
    still hash differently, and their margin columns differ, so a detector that sees only labels is caught."""
    planted_fights = [f for c in controls["identical"].cells for f in c.fights] + \
        [f for c in controls["damage"].cells for f in c.fights]
    fights = {"mirror": controls["mirror"].fights, "numbers": controls["numbers"].fights,
              "planted": planted_fights}
    free = {k: _csv_hash(tmp_path, "free_" + k, _label_free(v)) for k, v in fights.items()}
    assert len(set(free.values())) == len(KEYS), free
    margins = {k: tuple(f.margin for f in v) for k, v in fights.items()}
    assert len(set(margins.values())) == len(KEYS), "controls have identical margin columns"
    # the numbers control is lopsided, the mirror is not: the margin columns carry real information
    assert statistics.fmean(margins["numbers"]) > statistics.fmean(abs(m) for m in margins["mirror"])


@pytest.mark.parametrize("key", KEYS)
def test_control_hash_matches_golden(hashes, golden_written, key):
    """AC 26: sha256 of the written CSV bytes equals the golden value for this control."""
    if golden_written:
        assert json.loads(GOLDEN.read_text())[key] == hashes[key]
        return
    if not GOLDEN.exists():
        pytest.fail("tests/skilllab/golden_hashes.json is missing; write it on the first machine with "
                    "SKILLAB_WRITE_GOLDEN=1 python3 -m pytest tests/skilllab/integration/test_cross_machine.py "
                    "-p no:cacheprovider -q")
    golden = json.loads(GOLDEN.read_text())
    assert key in golden, "golden file has no key %r" % key
    assert hashes[key] == golden[key], (
        "determinism finding: control %r hashes to %s here, golden is %s; report it, do not patch the file"
        % (key, hashes[key], golden[key]))
