# Boundary sweep — C7 / leaf-01 / shard default

Single leaf, single assertion (subprocess exit code of the fenced
`tests/test_qa_daemon.gd` run). Boundary space is narrow: the adapter has
exactly one input (does `autoload/qa_daemon.gd` exist and satisfy the fenced
test's four checks: script loads, is a Script, instantiates, has `state()`
returning a Dictionary with `scene`/`tick`) and one output (process exit
code 0/1).

| boundary | pinned by | status |
|---|---|---|
| missing `qa_daemon.gd` (pre-impl state) | spec: fenced test's own `ResourceLoader.exists` check | tested — confirmed RED for this exact reason |
| present + correct `qa_daemon.gd` (post-impl state) | spec Acceptance section | tested — the leaf's own RED-then-GREEN run before this test is admitted |
| subprocess timeout (Godot hangs) | not pinned by spec | open — adapter sets 120s pytest-side timeout vs. runner's internal 300s `--quit-after`; a hang surfaces as `TimeoutExpired`, still red, not silently green. No spec line pins a timeout value, so no assertion added; flagged here rather than guessed. |
| `--qa-port` / `--qa-script` wire shape | not pinned by fenced test | out of scope for this adapter — the fenced test never exercises the dev-only verb surface, only `state()` via direct `load()`. Leaf brief covers it as free-standing implementation, not test-covered here. |

No `growth_claim`/`scale_assertions` on this brief — not a hot path, no
Scale & Boundary Profile entry in the spec. Composition rule (mockist)
not applicable — adapter has exactly one impl-adjacent target
(`scripts/run_godot_tests.sh`, invoked, not owned by this leaf) and no
in-process collaborators to assert interaction against.
