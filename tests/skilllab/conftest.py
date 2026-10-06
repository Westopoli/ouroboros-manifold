"""Shared fixtures for tests/skilllab."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import skills  # noqa: E402


@pytest.fixture
def strip():
    """strip(*skills): remove any real skilled/counter entry of those skills (ruling 2026-10-06 registers drafts);
    restored afterwards, so a skill with no entry can be tested whatever is registered."""
    saved = []

    def _strip(*names):
        for name in names:
            for role in ("skilled", "counter"):
                try:
                    play = skills.get(name, role)
                except ValueError:
                    continue
                skills.unregister(name, role)
                saved.append(play)

    yield _strip
    for play in saved:
        skills.register(play.skill, play.role, play.fn, play.status)
