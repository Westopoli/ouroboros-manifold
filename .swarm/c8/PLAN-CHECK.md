# Plan-consistency + invariant-audit notes — c8

## check_invariants.py known-limitation waiver (same class as prior pieces)

`spec-link` FAILs on `tests/qa/desktop/test_flow_spine.py` on all four
leaves. The file DOES carry a spec-link header (`# spec:
docs/northstar/plans/push/specs/C8.md::Acceptance`, line 1) but the
checker's regex requires a stricter three-segment form ending in
`::AC-<N>`; this test uses story-local ids (S-C8-01..07) not `AC-N`
numbering, so it doesn't match even though real traceability is present
and correct. Same class of pre-existing-fenced-test gap as every prior
piece's waiver. Accepted as-is.

## Plan-consistency (1.5)

1. AC↔AC: no gap across the four legs — each owns disjoint files, no
   leaf's change contradicts another's.
2. AC↔contract: no C ABI symbols. `c_bridge.gd`'s new `snapshot()`
   accessor and `scene_router.gd`'s new `SCENES` keys are cited exactly
   by name in the legs that depend on them (leaf-02/03/04 reference
   leaf-01's additions by string/method name, verified consistent across
   all four brief files).
3. AC↔test: every one of the 7 fenced sub-tests (S-C8-01..07) is covered
   by some leg: S-C8-01 (boot) is pre-existing/unaffected; S-C8-02
   (NewGame→galaxy) leaf-02; S-C8-03 (Mission→briefing) leaf-02+leaf-03
   boundary (galaxy's Mission button routes to the already-existing
   mission_briefing route, no leg needs to add that route); S-C8-04
   (Deploy→tactical) leaf-03; S-C8-05 (EndMission→debrief→Continue→chronicle)
   leaf-03+leaf-04 boundary; S-C8-06 (Return→galaxy) leaf-04; S-C8-07
   (boot race) leaf-01.
4. Observability: every check in the fenced test reads `state().scene` or
   `tree()`'s control list, both already-existing daemon verbs (plus the
   `rect_px` addition M0 already landed as a disclosed exception) — no
   new observability surface needed from any leg.
5. Named-entity resolution: the chronicle `SCENES` key name is the one
   place a cross-leg naming mismatch could silently break the combined
   flow (leaf-01 picks it, leaf-04's `_on_continue` retarget must match
   exactly) — flagged explicitly in leaf-04's brief with an instruction
   to check leaf-01's ASSUMPTIONS file before finalizing, falling back to
   the spec's own suggested `"chronicle"` if leaf-01 hasn't reported yet.
   This is a real cross-leaf coordination point, handled via the
   sibling-assumption-read mechanism rather than guessed independently by
   both sides.

## Ownership note (broader than pieces.toml's own owns_glob)

`scenes/loading_screen/loading_screen.gd` is touched by leaf-01 despite
not being in C8's `owns_glob` per `pieces.toml` — the piece spec
`docs/northstar/plans/push/specs/C8.md` "Findings" section explicitly
assigns the S-C8-07 fix here, so it's in scope by that authority, not
silently expanded.

## Split rationale (four legs, not one leaf or seven)

Task genuinely spans 8 files across the whole client surface, cross-cut
by one shared shared-file dependency (`scene_router.gd`'s `SCENES` dict,
which every other leg's routing calls reference by string). Splitting by
"flow leg" (plumbing / galaxy / mission / debrief) keeps each leaf
file-disjoint while grouping naturally-paired changes (each leg's
"exit scene" wiring pairs with the next leg's "entry scene" self-load
pattern) rather than one leaf per file, which would have meant 8 leaves
each touching a single small change with high combined-verification
coordination overhead for no real parallelism benefit (the four legs
already run fully in parallel; more legs wouldn't finish faster given
the shared combined-test bottleneck).
