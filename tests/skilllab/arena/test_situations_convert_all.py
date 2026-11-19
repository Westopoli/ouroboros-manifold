# spec: docs/northstar/plans/engine-rules-2026-11-08/round6.md (L3); docs/stories/H-040.md (Part 5: situations converter)
"""Round 6, L3: his stage 2 situations convert (`scripts/skilllab/arena/situations.py`).

round6.md L3: "SIT-0105, SIT-0106 and SIT-0107 are rejected today with 'arc too small: 8 units at pitch 40 on 32 degrees need radius 502'. They converted and were approved on
2026-11-02 ... Proof: a test that all of SIT-0101 to SIT-0109 convert." The ids are given to the converter as `L-0101` (`--next-id`), not `101`.

One test per situation file (the file alone in a fresh situations directory, converted with `--next-id L-0101`), so each result is its own: SIT-0101 to SIT-0104, SIT-0108 and SIT-0109 convert
today (green); SIT-0105, SIT-0106 and SIT-0107 are rejected today with "arc too small" (red, for that reason). The converter is run as the CLI, as test_situations.py does, so the exit code, the
`CONVERTED <sit> <layout>` line and the layout file it writes are what is read. A converted layout must also pass the producer's own `check_layout` (the converter runs it; this re-reads it).
The whole directory converting at once (every file, one run, exit 0, no REJECT line) is the last test.
"""
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab.catalogue.produce import check_layout, presets, rules  # noqa: E402

SITUATIONS = ROOT / "docs" / "northstar" / "research" / "layer_dynamics" / "situations"
FIRST_ID = "L-0101"
IDS = ["SIT-%04d" % n for n in range(101, 110)]


def _file(sit):
    found = sorted(SITUATIONS.glob(sit + "-*.md"))
    assert len(found) == 1, "%s: expected one file under %s, found %s" % (sit, SITUATIONS, found)
    return found[0]


def _convert(sit_dir, out):
    return subprocess.run([sys.executable, "-m", "scripts.skilllab.arena.situations", "--dir", str(sit_dir), "--out", str(out), "--next-id", FIRST_ID],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("sit", IDS)
def test_L3_the_situation_converts_to_a_layout_that_passes_check_layout(sit, tmp_path):
    """round6.md L3 / H-040 Part 5: SIT-0101 to SIT-0109 each give `CONVERTED <file stem> L-0101`, exit 0, and a layout file that loads and passes `check_layout`. Red today for SIT-0105,
    SIT-0106 and SIT-0107: `REJECT <sit> arc too small: 8 units at pitch 40 on 32 degrees need radius 502` (and exit 2); green for the other six."""
    src = tmp_path / "situations"
    src.mkdir()
    shutil.copy(_file(sit), src / _file(sit).name)
    out = tmp_path / "catalogue"
    done = _convert(src, out)
    said = done.stdout + done.stderr
    stem = _file(sit).stem            # the converter prints the file's stem, e.g. SIT-0109-slope
    assert done.returncode == 0 and ("CONVERTED %s %s" % (stem, FIRST_ID)) in done.stdout.splitlines(), "exit %d: %s" % (done.returncode, said.strip())
    with open(out / (FIRST_ID + ".toml"), "rb") as f:
        layout = tomllib.load(f)
    assert layout["id"] == FIRST_ID and layout["side_a"]["units"] and layout["side_b"]["units"]
    assert check_layout(layout, presets(), rules()) == []


def test_L3_all_nine_situations_convert_in_one_run_with_no_reject(tmp_path):
    """round6.md L3 'a test that all of SIT-0101 to SIT-0109 convert': the whole situations directory in one converter run exits 0, prints nine CONVERTED lines in file order and no REJECT.
    Red today for the reason of the three rejected files above."""
    out = tmp_path / "catalogue"
    done = _convert(SITUATIONS, out)
    said = done.stdout + done.stderr
    converted = [ln.split()[1][:8] for ln in done.stdout.splitlines() if ln.startswith("CONVERTED ")]
    assert "REJECT" not in said and done.returncode == 0, "exit %d: %s" % (done.returncode, said.strip())
    assert converted == IDS, converted
