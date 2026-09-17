# Test-audit brief — wave 1, shard default (drift-gate-and-green-check)

## ROUND 2 — re-audit after fixes

Round 1 (`TEST-AUDIT.md` in this directory) found 1 🔴 + 8 🟡. All nine are addressed
— see `BOUNDARIES.md`'s "Audit round 1 resolution" section in this same directory
for exactly what changed and why, including one case (the friction/admin-revolts
ordering test) where the parent removed a fixer-written test after discovering it
could never pass under any correct implementation, and replaced it with an explicit,
reasoned deferral row in BOUNDARIES.md instead.

**Your job this round:** verify each round-1 fix actually resolves its finding
(don't retake the fixes on faith — re-derive independently, same posture as round
1), and do a fresh full pass for anything NEW the changes might have introduced
(a new test with a hole, a deferral that isn't actually justified, a budget
overrun).

**IMPORTANT — the code blocks below (from round 1) are STALE.** They predate the
fixes and do not reflect the current files. Ignore them entirely and instead read
these three files fresh from disk — they are short:
- `/home/westopoli/Projects/ouroboros-manifold/tests/csim/test_E02_S160_drift_gate.py` (this wave's umbrella; also the shard's own test file — degenerate case, no separate umbrella)
- `/home/westopoli/Projects/ouroboros-manifold/tests/csim/controls/test_control_drift_gate_ignored.py` (unchanged since round 1)
- `/home/westopoli/Projects/ouroboros-manifold/tests/specfactory/test_green_check.py`

Also read `/home/westopoli/Projects/ouroboros-manifold/.swarm/drift-gate-and-green-check/audits/wave-1/default/BOUNDARIES.md` (fully rewritten post-fix) and
`/home/westopoli/Projects/ouroboros-manifold/.swarm/drift-gate-and-green-check/audits/wave-1/default/TEST-AUDIT.md` (the round-1 report, for what was found) and
`/home/westopoli/Projects/ouroboros-manifold/.claude-swarm.toml` (for the corrected `apex_test_cmd`) and
`/home/westopoli/Projects/ouroboros-manifold/docs/test_specs/drift-gate-and-green-check.md` (spec, AC5 wording corrected to "card file path").

Everything else in this brief below (shard's stated goal, contract excerpts, scale
profile) is still accurate and unchanged from round 1.

---

## Umbrella test (full text)

`umbrella_test_cmd` runs `tests/csim/test_E02_S160_drift_gate.py` in full. Its
complete text (this wave's own new file, so "umbrella" and "shard tests" overlap
here — there is no separate pre-existing umbrella for this specific behavior):

```python
# spec: docs/test_specs/drift-gate-and-green-check.md::Acceptance criteria::AC-1
"""S-160 -- Drift can be switched off, and off means off.

R-160-01 .. R-160-03. sim.c ignored OM_FEAT_DRIFT entirely (card 202b2 /
the 2026-09-17 harness defect investigation): the drift loop ran
unconditionally, before the faction/friction/admin-revolt block, instead of
gated and last (tick sequence step 5, docs/bible/algorithms.md:9-29). This
module proves the gate now works and the step sits in the right place.
"""
from conftest import (
    OMArchetype,
    OMFeature,
    OMField,
    OMTier,
    set_faction,
    set_owner,
    set_region,
    set_tech_multipliers,
)


def _all_fields(lib, w, idx):
    return tuple(lib.om_region_field(w, idx, f) for f in
                 (OMField.MILITARY, OMField.ECONOMY, OMField.TENSION, OMField.POPULATION))


def test_R_160_01_drift_off_leaves_fields_unchanged(lib, world_factory):
    w = world_factory(n_regions=1)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)

    before = _all_fields(lib, w, 0)
    lib.om_world_step(w)
    after = _all_fields(lib, w, 0)

    assert after == before, (
        "OM_FEAT_DRIFT is off but the region's fields moved -- the drift "
        "step ran anyway"
    )


def test_R_160_02_default_world_has_only_drift_on(lib, world_factory):
    w = world_factory(n_regions=1)
    assert lib.om_world_feature(w, OMFeature.DRIFT) == 1, (
        "om_world_new must switch OM_FEAT_DRIFT on by default"
    )
    for feat in (OMFeature.EVENTS, OMFeature.FACTIONS, OMFeature.FRICTION,
                 OMFeature.ADMIN_REVOLTS, OMFeature.DIPLOMACY,
                 OMFeature.TECHNOLOGY, OMFeature.LIFECYCLE):
        assert lib.om_world_feature(w, feat) == 0, (
            f"om_world_new must leave feature {feat} off by default -- only "
            "DRIFT is decided (S-160); every other default is open flag A4"
        )


def test_R_160_02_default_world_drifts(lib, world_factory):
    w = world_factory(n_regions=1)
    set_region(lib, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)
    lib.om_world_step(w)
    assert lib.om_region_field(w, 0, OMField.ECONOMY) != 66.0, (
        "a freshly-made world did not drift on its own tick -- DRIFT is not "
        "actually on by default"
    )


def test_R_160_03_budget_step_reads_pre_drift_economy(lib, world_factory):
    """Given a faction owning regions with economy 66, 40, and 9, and DRIFT
    also on, When one tick runs, Then Δbudget still equals
    ((66-8)+(40-8)+(9-8))*0.025 = 2.275 -- the same-tick budget step must
    read economy as it stood before this tick's drift, matching tick.py's
    order (faction agents at step 3, drift at step 5)."""
    w = world_factory(n_regions=3)
    for feat in (OMFeature.EVENTS, OMFeature.FRICTION, OMFeature.ADMIN_REVOLTS,
                 OMFeature.DIPLOMACY, OMFeature.TECHNOLOGY, OMFeature.LIFECYCLE):
        lib.om_world_set_feature(w, feat, 0)
    lib.om_world_set_feature(w, OMFeature.FACTIONS, 1)
    lib.om_world_set_feature(w, OMFeature.DRIFT, 1)

    set_faction(lib, w, 0, OMArchetype.DEFAULT, budget=0.0, tech=0.0, confidence=5.0)
    set_tech_multipliers(lib, w, 0, 1.0, 1.0, 1.0)

    set_region(lib, w, 0, tier=OMTier.HOME, military=50.0, economy=66.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 0, 0, held_since=-1)
    set_region(lib, w, 1, tier=OMTier.HOME, military=50.0, economy=40.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 1, 0, held_since=-1)
    set_region(lib, w, 2, tier=OMTier.HOME, military=50.0, economy=9.0, tension=0.0, population=50.0, faction_id=0)
    set_owner(lib, w, 2, 0, held_since=-1)

    initial_budget = lib.om_faction_budget(w, 0)
    lib.om_world_step(w)
    budget_after = lib.om_faction_budget(w, 0)
    delta_budget = budget_after - initial_budget

    expected_delta = ((66.0 - 8.0) + (40.0 - 8.0) + (9.0 - 8.0)) * 0.025
    assert abs(delta_budget - expected_delta) < 1e-6, (
        f"budget delta {delta_budget} does not match pre-drift economy delta "
        f"{expected_delta} -- the budget step is reading economy after this "
        "tick's drift already moved it"
    )
```

## Shard's stated goal (spec excerpt)

**Summary (spec lines 1-9):**

1. **Drift gate** — `csrc/sim.c` runs the passive-drift loop unconditionally, ignoring
   `OM_FEAT_DRIFT`, and runs it *before* the faction/friction/admin-revolt block
   instead of after (tick sequence puts drift at step 5, after faction agents at
   step 3). Fix gates the loop on `OM_FEAT_DRIFT`, moves it to run last, sets
   `OM_FEAT_DRIFT = 1` in `om_world_new` (every other switch stays off — A4, open).
2. **green_check** — `red_check.py` confirms a stub fails; nothing confirmed a
   *reference* actually passes, so a detector that can never fail could ship
   undetected. `green_check.py` closes that gap.

**Acceptance criteria (spec lines 12-17):**

1. `OM_FEAT_DRIFT` off skips the drift step entirely; fields byte-identical across a tick.
2. `om_world_new` returns a world with `OM_FEAT_DRIFT` on, every other switch off.
3. With FACTIONS and DRIFT both on, the same-tick budget step reads economy as it
   stood before this tick's drift.
4. The committed `om_faction_step_budget` body produces the exact ALG-17 answer for
   `test_E05_S033...::test_R_033_01_budget_66_8_40_8` once (3) holds.
5. `green_check.py` exits 0 only if a reference passes in a scratch worktree; refuses
   (non-zero, explicit reason) a reference that also passes on the untouched stub.
6. `docs/northstar/spec_factory.md` pipeline table gains a `green_check.py` row.

Leaf-01 (`csrc/sim.c`, `csrc/region.c`) owns AC1-4. Leaf-02 (`scripts/specfactory/green_check.py`,
`docs/northstar/spec_factory.md`) owns AC5-6.

## Tests under audit (full text)

### `tests/csim/test_E02_S160_drift_gate.py`

Identical to the "Umbrella test" section above (this wave's umbrella IS this file).

### `tests/csim/controls/test_control_drift_gate_ignored.py`

```python
# spec: docs/test_specs/drift-gate-and-green-check.md::Acceptance criteria::AC-1
"""Positive control for OM_BUG_DRIFT_GATE_IGNORED.

Watch-for: "Drift runs regardless of the OM_FEAT_DRIFT switch" (E-02 epic,
"Ways this could be wrong"), the exact card-202b2 / 2026-09-17 harness
defect: sim.c ran the drift loop unconditionally.

Clean expectation: R-160-01, a region with DRIFT off is byte-identical
after one tick.

Reuses the R-160-01 fixture against the debug build with
OM_BUG_DRIFT_GATE_IGNORED injected, and asserts the detector now trips: at
least one field moves even though the switch is off.
"""
from conftest import OMBug, OMFeature, OMField, OMTier, set_region


def test_control_drift_gate_ignored_trips_the_gate_detector(dbg, dbg_world_factory):
    w = dbg_world_factory(n_regions=1)
    dbg.om_world_set_feature(w, OMFeature.DRIFT, 0)
    set_region(dbg, w, 0, tier=OMTier.HOME, military=42.0, economy=66.0,
               tension=18.0, population=60.0)
    dbg.om_debug_inject(w, OMBug.DRIFT_GATE_IGNORED)
    dbg.om_world_step(w)

    fields_changed = any(
        dbg.om_region_field(w, 0, f) != v
        for f, v in ((OMField.MILITARY, 42.0), (OMField.ECONOMY, 66.0),
                     (OMField.TENSION, 18.0), (OMField.POPULATION, 60.0))
    )
    assert fields_changed, (
        "OM_BUG_DRIFT_GATE_IGNORED injected but the region's fields are "
        "unchanged -- the drift-gate detector did not trip"
    )
```

NOTE for the auditor: this control currently passes today, before leaf-01 lands,
for the WRONG reason — the gate doesn't exist yet, so drift always runs regardless
of the switch or the injected bug, and the assertion happens to hold either way.
After leaf-01 lands, re-running this control must still pass, now for the right
reason (gate exists and correctly closes; injecting the bug reopens it). This is a
known, already-flagged property of the control, not something to re-discover.

### `tests/specfactory/test_green_check.py`

Full text — see the working tree at that path; reproduced in the "Tests under
audit" listing above is the umbrella and control only, to keep this brief a
readable size. The file has 5 tests: passes-on-real-reference (also asserts the
caller's own checkout file is unchanged), fails-a-non-passing-reference,
exits-3-on-missing-card, exits-3-on-missing-reference, refuses-a-stub-that-already-passes.
8 assert statements total.

## BOUNDARIES.md

See `.swarm/drift-gate-and-green-check/audits/wave-1/default/BOUNDARIES.md`
(same directory as this file).

## Spec's Scale & Boundary Profile

- N typical/peak: drift gate 1-60 regions (E-02's confirmed scale gate). green_check: one card per invocation.
- Growth claim: `unbounded-unknown — assert growth only, no absolutes`. Neither leaf changes an asymptotic shape this wave.
- Memory posture: bounded-buffer.
- External call budget: green_check shells out to `git worktree add` and the card's acceptance command once each per invocation.

## Composition-relevant contract excerpts (`csrc/ouroboros_sim.h`)

```c
typedef enum {
    OM_FEAT_EVENTS        = 0,
    OM_FEAT_FACTIONS      = 1,
    OM_FEAT_FRICTION      = 2,
    OM_FEAT_ADMIN_REVOLTS = 3,
    OM_FEAT_DIPLOMACY     = 4,
    OM_FEAT_TECHNOLOGY    = 5,
    OM_FEAT_DRIFT         = 6,
    OM_FEAT_LIFECYCLE     = 7
} om_feature;
void om_world_set_feature(om_world *w, om_feature f, int on);
int  om_world_feature(const om_world *w, om_feature f);
om_world *om_world_new(uint32_t n_regions, uint64_t seed);
double   om_faction_budget(const om_world *w, int32_t faction_id);
```

Leaf-02's contract surface is Python-only (no C symbols) — the shared
`type_contract_path` (`csrc/ouroboros_sim.h`) does not apply to it; its brief
carries an empty `contract_imports`.

## Sibling-shard awareness

Not applicable — this wave is a single shard ("default"), both leaves' briefs and
tests are all in this one package.

## Anything already litigated

Nothing yet — this is the first (and only) audit pass for this wave. The one
pre-flagged item is the control-test note above (expected-but-not-yet-meaningful
pass before leaf-01 lands).

## Your task

You are auditing shard "default"'s tests before any leaf sees them, per
`/manager-mode` Phase 3.4.2. Check GOAL FIDELITY, UMBRELLA ALIGNMENT, TEST QUALITY,
and BOUNDARY & SCALE FIDELITY as that phase's framing specifies. Write your report
to `.swarm/drift-gate-and-green-check/audits/wave-1/default/TEST-AUDIT.md`.
