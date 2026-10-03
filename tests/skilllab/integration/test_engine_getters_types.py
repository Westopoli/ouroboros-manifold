# spec: Architect speed brief, change 3 (leaner hot getters keep their return types)
"""Real library: unit_hp float, unit_layer int, unit_alive and can_shoot bool, equal to the raw library values."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.skilllab import engine  # noqa: E402


@pytest.fixture(scope="module")
def library():
    return engine.Engine()


def test_types_and_values_match_the_library(library):
    w = library.new_world(0)
    try:
        t = library.type_id("Vanguard")
        a = library.spawn(w, t, 0, 0.0, 0.0, 0)
        b = library.spawn(w, t, 1, 50.0, 0.0, 0)
        lib = library._lib
        assert type(a) is int
        hp, layer, alive, shoot = library.unit_hp(w, a), library.unit_layer(w, a), \
            library.unit_alive(w, a), library.can_shoot(w, a, b)
        assert type(hp) is float and hp == lib.om_unit_get_hp(w, a) and hp > 0
        assert type(layer) is int and layer == lib.om_unit_get_layer(w, a)
        assert type(alive) is bool and alive is True and alive == bool(lib.om_unit_alive(w, a))
        assert type(shoot) is bool and shoot == bool(lib.om_combat_can_shoot(w, a, b))
    finally:
        library.free_world(w)
