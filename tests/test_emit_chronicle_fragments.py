"""tests/test_emit_chronicle_fragments.py
C3-4: verify emit_chronicle_fragments.py output matches committed
library/chronicle/fragments.json, and that fragment count equals
CHRON_N_FRAGMENTS in csrc/chronicle.c.
"""
import copy
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "library", "emit_chronicle_fragments.py")
COMMITTED = os.path.join(REPO_ROOT, "library", "chronicle", "fragments.json")
C_SOURCE = os.path.join(REPO_ROOT, "csrc", "chronicle.c")
PYTHON = sys.executable


def _source() -> str:
    with open(C_SOURCE, encoding="utf-8") as f:
        return f.read()


def _n_define(src: str, name: str) -> int:
    m = re.search(r"#define\s+" + re.escape(name) + r"\s+(\d+)", src)
    assert m, f"{name} not found in C source"
    return int(m.group(1))


def _committed() -> dict:
    with open(COMMITTED, encoding="utf-8") as f:
        return json.load(f)


def _run(out_path: str) -> None:
    result = subprocess.run(
        [PYTHON, SCRIPT, out_path],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"script failed:\n{result.stderr}"


def test_fragment_count_matches_c_define():
    """Fragment count in committed JSON equals CHRON_N_FRAGMENTS from C source."""
    n = _n_define(_source(), "CHRON_N_FRAGMENTS")
    data = _committed()
    frags = data["fragments"] if isinstance(data, dict) else data
    assert len(frags) == n, (
        f"library/chronicle/fragments.json has {len(frags)} fragments; "
        f"C source defines CHRON_N_FRAGMENTS={n}"
    )


def test_script_output_matches_committed(tmp_path):
    """Re-running the script produces the same JSON as the committed file."""
    out = str(tmp_path / "out.json")
    _run(out)
    with open(out, encoding="utf-8") as f:
        generated = json.load(f)
    committed = _committed()
    assert generated == committed, (
        "Script output differs from committed library/chronicle/fragments.json. "
        "Run scripts/library/emit_chronicle_fragments.py to regenerate."
    )


def test_positive_control_altered_fragment():
    """Positive control: altering one fragment text makes it differ from committed."""
    committed = _committed()
    altered = copy.deepcopy(committed)
    frags = altered["fragments"] if isinstance(altered, dict) else altered
    original_text = frags[0]["text"]
    frags[0]["text"] = "ALTERED FOR POSITIVE CONTROL TEST"
    assert altered != committed, (
        "Positive control failed: altered data unexpectedly equals committed data. "
        f"Original first-fragment text: {original_text!r}"
    )
