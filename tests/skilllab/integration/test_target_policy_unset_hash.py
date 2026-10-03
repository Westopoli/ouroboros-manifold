# spec: ruling A196 (per-side target policy): unset policy is byte-identical to today
"""Whole-result digests, real library, seed 3, BASE_SETTINGS."""
import dataclasses
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import fight  # noqa: E402
from scripts.skilllab.asym import Side, asym_play  # noqa: E402
from scripts.skilllab.batches import BASE_SETTINGS  # noqa: E402
from scripts.skilllab.plays import blob_play, line_play  # noqa: E402

PLAYS = {
    "blob": lambda: blob_play(16)(12, False),
    "line": lambda: line_play(16)(16, True),
    "asym": lambda: asym_play(16, Side("skilled"), Side("blob"))(14, False),
}


def digest(name, settings=None, **kw):
    s = dataclasses.replace(PLAYS[name](), settings={**BASE_SETTINGS, **(settings or {})}, **kw)
    return hashlib.sha256(repr(dataclasses.asdict(fight.fight(s, 3, False))).encode()).hexdigest()


@pytest.mark.parametrize("name", sorted(PLAYS))
def test_explicit_none_equals_today(name):
    assert digest(name, target_policy=None) == digest(name)


@pytest.mark.parametrize("name", sorted(PLAYS))
def test_0_0_pair_equals_settings_policy_0(name):
    assert digest(name, target_policy=(0, 0)) == digest(name, {"OM_TP_TARGET_POLICY": 0})


@pytest.mark.parametrize("name", sorted(PLAYS))
def test_1_none_pair_equals_settings_policy_1(name):
    """The unset faction 1 follows faction 0."""
    assert digest(name, target_policy=(1, None)) == digest(name, {"OM_TP_TARGET_POLICY": 1})
