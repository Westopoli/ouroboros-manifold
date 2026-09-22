# leaf-01-Q1

Two blockers hit while building csrc/pipe/om_pipe.c against the locked
header. Impl is done and builds clean under `make -s OPT=-O2 WERROR=1
libouroboros.so libouroboros_dbg.so pipe/ouroboros_pipe`. Proceeded under
best-guess for both; tagging both `unanswered: true` in
leaf-01.ASSUMPTIONS.md. Neither blocks my own build any more (worked around
#1, can't work around #2), but both have cross-piece weight: other T1
consumers (C2/C3/C4/C5/T2g) and anything else that links csrc/ouroboros_sim.h
or runs the fenced transport test will hit the same two walls.

## 1. `om_region_neighbors` declared but not implemented

`csrc/ouroboros_sim.h` line 740 declares:

```
uint32_t om_region_neighbors(const om_world *w, uint32_t idx, uint32_t *out, uint32_t max);
```

with a comment (735-739) calling it "the O(degree) accessor connectivity and
adjacency tests use instead of an O(N^2) om_region_edge sweep." T1.md's
snapshot section (line 82-85) directs building the `edges` array with it.

`grep -rn "om_region_neighbors" csrc/*.c` returns nothing -- no `.c` file
defines it. `nm -D libouroboros.so | grep om_region_neighbors` returns
nothing either -- the symbol isn't exported. Linking `pipe/ouroboros_pipe`
against it fails: `undefined reference to 'om_region_neighbors'`.

Worked around inside `csrc/pipe/om_pipe.c` (the only file I own) by building
the `edges` array with the O(N^2) `om_region_edge(w, i, j, &t)` sweep the
header's own comment says `om_region_neighbors` exists to avoid.
`om_region_edge` IS implemented (`csrc/faction.c:26`) and exported. Fine at
n_regions=60-110 scale; a real problem only if a future piece actually needs
the O(degree) accessor's win.

Best guess: whichever `.c` file owns region adjacency (`csrc/region.c` or
`csrc/faction.c`, next to `om_region_set_edge`/`om_region_edge`) is missing
this one function; a one-function addition, not a design question. Flagging
because it's parent-owned/fenced territory (`csrc/region.c`, `csrc/faction.c`
are both in leaf-01's `do_not_edit`), not something I can add myself.

## 2. Fenced test calls a conftest function that doesn't exist

`tests/transport/test_pipe_shapes.py:76` (parent-owned, unmodifiable) does:

```python
import conftest as csim   # tests/csim/conftest.py
...
lib = csim.load_lib()
```

`tests/csim/conftest.py` has no `load_lib` at all --
`hasattr(csim, 'load_lib')` is `False`. The nearest candidate is `lib`
(line 248-263), a `@pytest.fixture(scope="session")`-decorated function.
Verified directly (see leaf-01's report to parent for the transcript):
calling `csim.lib()` raises pytest's own
`Failed: Fixture "lib" called directly. Fixtures are not meant to be called
directly...` (pytest 9.1.1's guard) -- so even renaming the call site from
`load_lib()` to `lib()` would not fix it as-is; the fixture would need
calling as a plain function outside pytest's fixture machinery (e.g. factor
the CDLL-loading body of `lib()` into a plain module-level function the
fixture then wraps, or have `test_pipe_shapes.py` construct the CDLL handle
itself rather than reaching into `tests/csim/conftest.py`).

This is entirely inside `tests/**`, fenced and owned by the parent
(`test_owned_by: parent` in my brief). I did not touch it. My own frames
(hello/delta x10/snapshot) are correct through the point the test's own
`csim.load_lib()` call raises `AttributeError` -- confirmed by running the
pipe binary by hand and by the pytest failure trace itself, which shows the
assertions on `kinds[0]`, `frames[0]["abi"]`, `layout_ok`, and
`snap["tick"] == 10` all passed before the `AttributeError`.

Per the repo rule that tests are the spec and the build worker never edits a
test, this looks like a `test-defect` finding (a helper the test references
that was never wired into conftest.py) for the parent/escalator to fix under
the test-fix gate, not something for this leaf to touch.
