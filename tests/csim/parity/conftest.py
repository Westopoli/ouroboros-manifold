"""PP pending list (Architect ruling A135): pending.txt, next to this file,
names test ids that are red until a later wave. Each listed id is marked
strict xfail, so it turns into a failure the moment it passes and its line
must then be removed. One id per line, '#' comments and blank lines ignored.

pytest_collection_modifyitems is a global hook: it sees every item of the
whole session, not just this directory. Ids are matched by full node id, so
nothing outside the list is touched, and the stale-id check only covers ids
whose file was collected in this session (a partial run is not an error).
This directory is a package so this file does not clash with
tests/csim/conftest.py (see tests/csim/scale/conftest.py).
"""
import pathlib

import pytest

PENDING = pathlib.Path(__file__).resolve().parent / "pending.txt"
REASON = "PP pending: code not built yet"


def _read_pending():
    ids = []
    for line in PENDING.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.append(line)
    return ids


def pytest_collection_modifyitems(config, items):
    if not PENDING.is_file():
        return
    ids = _read_pending()
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        raise pytest.UsageError("pending.txt: duplicate line(s): %s" % ", ".join(dups))
    by_id = {item.nodeid: item for item in items}
    files = {nodeid.split("::", 1)[0] for nodeid in by_id}
    stale = [i for i in ids if i.split("::", 1)[0] in files and i not in by_id]
    if stale:
        raise pytest.UsageError("pending.txt: stale id(s), no such test: %s" % ", ".join(stale))
    for i in ids:
        if i in by_id:
            by_id[i].add_marker(pytest.mark.xfail(strict=True, reason=REASON))
