"""Read the named constants a bible ALG row states from csrc/om_constants.h (then chronicle.c, mission.c).

Used by the tests/csim/test_ALG_*.py coverage tests (sim lane step 3): a test
asserts the row's arithmetic with the row's own constants, read here by name,
never retyped. Not a test module."""
import pathlib
import re

_CSRC = pathlib.Path(__file__).resolve().parents[2] / "csrc"
# om_constants.h first; chronicle.c and mission.c carry a few file-local row constants (e.g. the
# 0.40 dedup threshold) that have not been promoted to the header.
_FILES = [_CSRC / "om_constants.h", _CSRC / "chronicle.c", _CSRC / "mission.c"]
_DEF = re.compile(r"^#define\s+(OM_[A-Z0-9_]+)\s+(.+?)\s*(?:/\*.*)?$")


def _load():
    out = {}
    for path in _FILES:
        for line in path.read_text().splitlines():
            m = _DEF.match(line.strip())
            if not m or m.group(1) in out:
                continue
            txt = m.group(2).strip()
            try:
                out[m.group(1)] = float(txt) if any(c in txt for c in ".eE") else int(txt, 0)
            except ValueError:
                pass  # an expression or a string: read it by hand in the test
    return out


_C = _load()


def const(name):
    """Value of OM_<name> (name given without the OM_ prefix); KeyError if absent or not a plain number."""
    return _C["OM_" + name]
