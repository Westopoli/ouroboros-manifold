"""Lane F, depot script: the publishing policy, Westley's call (parked file).

Spec: Steam spec "T17"/Q-STEAM-01 (a private beta by Dev Comp key first). Story S-141; R-141-01. The check:
the build file must not push to the default (public) branch. Which branch name the beta uses is Westley's.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VDF = ROOT / "scripts/steam_app_build_5402100.vdf"


def test_the_upload_never_sets_the_default_branch_live():
    assert VDF.exists(), "scripts/steam_app_build_5402100.vdf does not exist (depot script not built)"
    text = VDF.read_text().lower().replace(" ", "")
    assert '"setlive""default"' not in text, "SetLive is the public default branch; the private beta must not publish there"
