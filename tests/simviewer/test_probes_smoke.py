"""Smoke test for scripts/simviewer/probes/ (sim lane 2026-10-12 method notes): each probe at one seed
and one mission/chapter into a temp dir writes its summary files with the expected keys."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBES = ROOT / "scripts" / "simviewer" / "probes"

pytestmark = pytest.mark.skipif(not (ROOT / "pipe" / "ouroboros_pipe_dbg").exists()
                                or not (ROOT / "libouroboros_dbg.so").exists(),
                                reason="needs `make all pipe/ouroboros_pipe_dbg`")


def run(script, *args):
    r = subprocess.run([sys.executable, str(PROBES / script), *args], cwd=ROOT, capture_output=True, text=True, timeout=90)
    assert r.returncode == 0, r.stderr[-2000:]


def test_mission_choice_probe(tmp_path):
    run("mission_choice.py", "--seeds", "1", "--missions", "1", "--out", str(tmp_path))
    s = json.loads((tmp_path / "mission_summary.json").read_text())
    for k in ("missions_run", "draws_checked", "argmax_rate", "rank_histogram", "swapped_count", "swapped",
              "first_mission_relevance_zero_rows", "archetypes_seen", "archetypes_played", "max_urgency"):
        assert k in s
    assert s["missions_run"] == 1 and s["shadow_problems"] == []
    rows = json.loads((tmp_path / "rows.json").read_text())
    assert rows and {"seed", "tick", "region", "archetype", "urgency", "relevance", "preference", "score", "drawn", "played"} <= set(rows[0])
    assert sum(r["played"] for r in rows) <= 1
    assert (tmp_path / "mission_summary.md").read_text().startswith("# Mission choice summary")


def test_chronicle_twin_probe(tmp_path):
    run("chronicle_twin.py", "--seeds", "1", "--chapters", "1", "--out", str(tmp_path))
    camp = json.loads((tmp_path / "camp_1.json").read_text())
    assert len(camp["chapters"]) == 1 and camp["chapters"][0]["twin_match"] is True
    s = json.loads((tmp_path / "chronicle_summary.json").read_text())
    assert {"totals", "mismatch_classes", "groups"} <= set(s)
    assert {"family_entries", "chain_entries", "blank_shells", "ripple_over_cap", "repeats",
            "significance_threshold_explanations"} <= set(s["groups"])
    assert "twin_checksum_mismatch" not in s["mismatch_classes"]
    assert (tmp_path / "chronicle_summary.md").read_text().startswith("# Chronicle twin summary")
