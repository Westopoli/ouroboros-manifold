# PX-15 — Control liveness (proving the factory)

Run 2026-09-20 (ouroboros `930c004`: `scripts/specfactory/control_liveness.py`, `tests/specfactory/test_control_liveness.py`, 29 tests). Claim (DECISIONS.md R10): a positive control proves nothing unless it behaves differently on the clean build and on the debug build with its own `OM_BUG_*` injected; one mechanical check catches every dead-control cause without reading docstring conventions.

Result: **pass**, and the sweep is the finding.

## The claim

The three known dead controls all report `DEAD`, each because both runs fail identically: `agent_reads_live` (`assert 0.7 != 0.7`, R7h), `garrison_before_damage` (`assert 31.3 != 31.3`, R7l), `telegraph_after_reinforce` (`assert 1 != 1`, R9). Three different causes, one check. Live controls report `LIVE`: `empty_drifts`, `ge_not_gt`, `raw_not_trend`, `slow`, `drift_gate_ignored`, and the new `e05_inject_ignored`.

Method: a scratch copy of `tests/csim/conftest.py` monkeypatches the injection call to a no-op under an environment flag, so the test body is unchanged and only the fault is absent; the scratch tree symlinks the already-built libraries, so nothing races Agora's own build.

Cost: 28.7 s for all 119 controls, 241 ms each. Per-card gating is affordable.

## The sweep: 10 live, 17 dead, 92 error, out of 119

- **92 ERROR**: auto-generated skeletons for unbuilt epics (E-03, E-06 through E-17) naming `OMBug` members that do not exist yet. These are placeholders, not controls. Worth knowing: most of what looks like a control suite is not one yet.
- **17 DEAD**, in two kinds that the gate must treat differently:
  - *Blocked by unbuilt features*: all seven E-04 controls (events are not wired into `om_world_step` at all, A5), plus `admin_roll_per_faction`, `collision_max_strength`, `friction_counts_trade`, whose fixtures never reach the asserted condition in the current build. These will come alive when their feature is built.
  - *Defective fixtures*: `agent_reads_live`, `garrison_before_damage`, `telegraph_after_reinforce` (R7h, R7l, R9), `composite_pre_clamp` (a known pre-existing failure that stops on its own guard assertion before reaching the injected check), and `osc_as_level` (below).
- **10 LIVE**: the whole suite's working positive-control coverage today.

## New defect found: bug id zero collides with "no bug"

`OM_BUG_OSC_AS_LEVEL = 0` (`csrc/ouroboros_sim.h:156`) and `om_world_new` sets `w->inject = 0` (`csrc/region.c:17`). `csrc/sim.c:176` reads `osc_as_level = (w->inject == OM_BUG_OSC_AS_LEVEL)`. So **every debug-build world runs with the oscillator-as-level bug active unless some other bug is explicitly injected**, and injecting any other bug incidentally "fixes" the oscillator. Confirmed empirically by comparing the release build, the debug build with no injection, and the debug build with another bug injected. Its own control can therefore never see a clean state.

This is a sim defect, not a tool artifact, and it is C work: ledgered as R11 for the session that owns `csrc/`. Options: initialise `w->inject` to a reserved `OM_BUG_NONE` outside the id space, or renumber the E-02 block to start at 1.

## Design consequences

1. **Liveness is required at queue time for the story's own controls, not for every control in the repo.** A control dead because its feature is unbuilt is `PENDING`, not defective; requiring liveness repo-wide would block every card behind features further down the chain, the same false-stop PX-08 found with the plain plateau rule. The checker reports the two kinds separately.
2. The gate belongs in the CPU slot with the other pre-queue checks (241 ms per control).
3. A control that is `DEAD` with its feature built is a `test-defect` for the escalator; PX-13's detectors supply the cause and, for the vacuous class, the distinguishing value.
4. Inventory for Westley: 10 live controls, and 92 placeholder skeletons that read as controls but are not. Every epic's "ways this could be wrong" list is currently unproven except where those 10 sit.
