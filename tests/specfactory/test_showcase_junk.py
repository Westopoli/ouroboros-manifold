# Rule pins: none (harness piece SHOWCASE-junk: no S- or R- id; spec docs/northstar/plans/showcase/README.md, paragraph "SHOWCASE-junk")
"""SHOWCASE-junk: the five junk paths are no longer tracked by git.

UNSTATED INTERFACE CHOICES (the paragraph says "the five paths" without listing them):
- The five are read as the five entries the paragraph adds to `.gitignore`: build/_pyi_dist/, .swarm/, graphify-out/,
  docs/research/graphify-out/, saves/. tuning_output/ (also `git rm`-ed by the paragraph, but not one of the five
  .gitignore entries) is deliberately not asserted here; reported as a gap.
- "Tracked" is `git ls-files -- <path>` run in the repo root against the index of the checked-out tree.
Positive control: a path known tracked (scripts/specfactory) must list files, so an empty answer for the junk
paths cannot come from a broken git call."""
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
JUNK = ["build/_pyi_dist", ".swarm", "graphify-out", "docs/research/graphify-out", "saves"]


def _tracked(path: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "--", path], cwd=REPO, check=True, capture_output=True, text=True)
    return out.stdout.splitlines()


@pytest.mark.parametrize("path", JUNK)
def test_junk_path_is_not_tracked(path):
    files = _tracked(path)
    assert files == [], f"{path} still has {len(files)} tracked files, e.g. {files[:2]}"


def test_positive_control_tracked_path_lists_files():
    assert _tracked("scripts/specfactory/merge_gate_support.py") == ["scripts/specfactory/merge_gate_support.py"]
    assert len(_tracked("scripts/specfactory")) > 5
