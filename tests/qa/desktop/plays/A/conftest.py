import pytest

from play_support import start_tactical_game


@pytest.fixture(scope="module")
def tactical_game():
    g = start_tactical_game()
    try:
        yield g
    finally:
        g.stop()
