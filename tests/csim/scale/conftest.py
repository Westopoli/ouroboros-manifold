"""Gate for the scale suite (docs/bible/epics/E-*.md "Scale requirements"
sections). Every test under this directory is skipped unless OM_SCALE=1 is
set -- the regular gate's runs (make test / the merge gate) never see this
directory; a separate WARN step runs it on its own. Every item here also
carries the `scale` pytest marker.

This directory is a package (__init__.py present) so pytest imports this
file as "scale.conftest", not the bare "conftest" tests/csim/conftest.py
also uses -- without that, with neither tests/csim/ nor tests/csim/scale/
packaged, pytest's own conftest loader gives both files the same bare
module name and the one loaded later silently overwrites the earlier one in
sys.modules['conftest']; every sibling tests/csim/test_*.py file's own
`from conftest import ...` then resolves to whichever file won, breaking the
entire fenced suite (observed directly while writing this file). Test files
here get their shared helpers from `_scale_helpers.py` via an explicit
relative import (`from ._scale_helpers import ...`, required once this
directory is a package); `lib`/`dbg`/`world_factory` still come for free
from tests/csim/conftest.py, an ancestor conftest pytest loads regardless.

pytest_collection_modifyitems below is a global hook: it receives every
item pytest collected in the whole session, not just this subtree, so it
filters by path before marking/skipping anything -- an earlier version of
this file skipped the entire tests/csim/ suite by forgetting that (also
observed directly).
"""
import os
import pathlib

import pytest

OM_SCALE = os.environ.get("OM_SCALE") == "1"
_THIS_DIR = pathlib.Path(__file__).resolve().parent


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "scale: measures wall time/memory against a bible epic's "
        "Scale requirements budget; runs only with OM_SCALE=1"
    )


def pytest_collection_modifyitems(config, items):
    """pytest_collection_modifyitems receives the WHOLE session's item list,
    not just this conftest's own subtree -- every item is filtered by path
    here so a run of the rest of tests/csim/** is never touched (only items
    collected from this directory get the `scale` marker and the gate)."""
    skip_scale = pytest.mark.skip(reason="scale suite gated behind OM_SCALE=1 (a separate WARN step runs it)")
    for item in items:
        try:
            in_this_dir = _THIS_DIR in pathlib.Path(str(item.fspath)).resolve().parents
        except Exception:
            in_this_dir = False
        if not in_this_dir:
            continue
        item.add_marker(pytest.mark.scale)
        if not OM_SCALE:
            item.add_marker(skip_scale)
