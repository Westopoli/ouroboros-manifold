# leaf-01 assumptions

No sibling ASSUMPTIONS files existed at start except leaf-02's (unrelated file,
green_check). Nothing here was escalated -- no do_not_edit conflict, no
ambiguity a sibling leaf or the umbrella test could observe.

- `OM_FEAT_DRIFT` default-on write in `om_world_new` uses
  `om_world_set_feature(w, OM_FEAT_DRIFT, 1)` (declared in
  `csrc/ouroboros_sim.h`, defined in `csrc/faction.c`) rather than a raw
  `w->features[OM_FEAT_DRIFT] = 1` write -- brief said "om_world_set_feature
  equivalent", either satisfies it; calling the real setter seemed more
  idiomatic and is the same one line.
- `OM_BUG_DRIFT_GATE_IGNORED` override variable named `drift_gate_ignored`,
  computed once per `om_world_step` call (not per-region, unlike the other
  `#ifdef OM_DEBUG_INJECT` bug flags which are re-derived per region) --
  the gate itself is a per-step, not per-region, decision, so this matches
  the other feature-gate ifs (`OM_FEAT_FACTIONS` etc.) immediately above it.
- Did not re-indent the relocated drift loop body one level deeper inside
  its new `if (om_world_feature(w, OM_FEAT_DRIFT) || drift_gate_ignored) {`
  wrapper -- kept the diff to the wrap/move only, per "No cosmetic
  refactoring in a change that fixes or builds something else" / minimal
  diffs (CLAUDE.md Code Quality). Body text is byte-identical to before.

Final: all 6 tests in `tests/csim/test_E02_S160_drift_gate.py` pass, plus
`tests/csim/controls/test_control_drift_gate_ignored.py` (confirmed RED
per the brief's stated baseline, then GREEN after the fix). Full
`tests/csim` sweep shows many unrelated pre-existing failures (missing
map-generation symbols, `om_step_decisions` telegraph/commit recording in
`csrc/agent.c`, a few E-02 tests that were only passing vacuously before
because `OM_FEAT_DRIFT` defaulted off) -- none touch `csrc/sim.c` or
`csrc/region.c`, none are in my `impl_files`, and the spec's own Out of
scope section excludes "the 'earlier suites stay green' clause," so these
are left alone.
