# spec: docs/northstar/plans/skilllab-harness-spec.md::Acceptance criteria::AC-20
"""Umbrella: the controls command writes one rows file and one HTML page and exits 0.

Red until every leaf of the skilllab-harness cascade is admitted.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_controls_command_writes_rows_and_page(tmp_path):
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.skilllab", "controls", "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    csvs = sorted(out.glob("*.csv"))
    pages = sorted(out.glob("*.html"))
    assert len(csvs) == 1 and len(pages) == 1
    assert csvs[0].stat().st_size > 0
    html = pages[0].read_text()
    assert "<html" in html.lower() and "beats" in html
