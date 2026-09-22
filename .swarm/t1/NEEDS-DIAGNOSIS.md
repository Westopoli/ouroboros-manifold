# T1 blocked by two pre-existing defects outside piece scope — for M0

`csrc/pipe/om_pipe.c` (leaf-01, branch `push/T1`, commit `090c7699b134` on
base `dad7f6916046`) is implemented and independently verified correct: its
`snapshot` frame's checksum (`16038372209008516879`) for `set_seed(seed=1,
n_regions=60, features=[6])` + `step(n=10)` matches `om_world_get_state_checksum`
computed directly via ctypes on an equivalently-built world. Manually
re-verified by the manager (this session), not just taken on the leaf's word.

`tests/transport -q` currently reports 2 passed, 1 FAILED (previously
SKIPPED before the binary existed) — for two reasons, neither inside
`csrc/pipe/om_pipe.c`:

## 1. `tests/transport/test_pipe_shapes.py:76` calls `csim.load_lib()`, which does not exist

```python
sys.path.insert(0, str(ROOT / "tests/csim"))
import conftest as csim
...
lib = csim.load_lib()
```

`tests/csim/conftest.py` has no `load_lib` function — only a `lib`
pytest fixture (`@pytest.fixture(scope="session") def lib():` at line 248),
which pytest 9.1.1 refuses when called directly outside the fixture
machinery (`Failed: Fixture "lib" called directly. Fixtures are not meant
to be called directly...`). Every assertion in the test BEFORE this line
already passes against `om_pipe.c`'s real output (`kinds[0]=="hello"`,
`abi==2`, `layout_ok==True`, `snap["tick"]==10`); the test fails past that
point purely on its own missing helper. This is a `tests/**` file, parent-
owned, out of M3's reach to fix — verified manually (`grep -n "^def
load_lib\|@pytest.fixture" tests/csim/conftest.py` confirms no such
function; only fixtures).

**Candidate fixes** (for M0/whoever owns test-fix authority, not decided
here): (a) add a small `load_lib()` module-level function to
`tests/csim/conftest.py` that does what the `lib` fixture's body does,
usable both by the fixture and by direct callers like this test; (b) change
`test_pipe_shapes.py` to receive `lib` as a normal pytest fixture argument
instead of importing conftest and calling it directly (the more idiomatic
pytest fix, but changes the test's structure). Either is a `test-defect`
fix per the project's test-fix gate (`assertions_preserved`, `red_at_stub`,
`two_agent_confound`) — not something the M3 cascade may apply itself.

## 2. `om_region_neighbors` is declared in the header but implemented nowhere

`csrc/ouroboros_sim.h:741` declares
`uint32_t om_region_neighbors(const om_world *w, uint32_t idx, uint32_t *out, uint32_t max);`
and line 729's comment names it as part of the post-`om_world_generate`
read path. `grep -rn om_region_neighbors csrc/*.c` finds zero
implementations, and `nm -D libouroboros.so | grep om_region_neighbors`
returns nothing — it is not exported by the built library at all (would be
a link error for anything that calls it via the real symbol rather than
dlsym'd optionally). No piece in `pieces.toml` owns `region.c`; this looks
like a stub gap from the F1b/F2 freeze generation (the push ledger notes
"stubs in 13 modules", `worldgen.c created` — `om_region_neighbors` may
have been missed). `om_pipe.c`'s leaf worked around this locally, inside its
own file, by building the snapshot `edges` list with the O(N²)
`om_region_edge(w, i, j, &type)` sweep the header's own comment says
`om_region_neighbors` exists specifically to avoid (`om_region_neighbors`
is described as "the O(degree) accessor... instead of an O(N^2)
om_region_edge sweep"). That workaround is fine for T1's own correctness
(the fenced test doesn't touch edges) but doesn't fix the missing symbol
for whatever else may call it directly.

## What's needed from M0

1. Triage and apply whichever `load_lib`/fixture fix is correct under the
   test-fix gate, or tell M3 which to apply if M3 is meant to do it in a
   follow-up piece.
2. Decide who implements `om_region_neighbors` in `region.c` (parent-owned,
   not T1's) — or confirm it's dead/unused elsewhere and can stay
   unimplemented for now.
3. Once (1) lands, `tests/transport -q` should go fully green against the
   already-pushed `push/T1` branch with no further `om_pipe.c` changes
   needed — re-run to confirm before merging.

`push/T1` is pushed and ready; this file documents why its own fenced test
can't currently prove it clean, and that the gap is verified to be outside
`csrc/pipe/om_pipe.c`.
