# Audit round1-opus (2026-10-07)

The verdict is to approve with the listed changes. Three items are blocking: #1 the contract wave cannot pass its own tests as written, #2 lane A's fog piece builds something the bible forbids, and #6 most acceptance stories are not Ready. Two more are close to blocking: lane D builds on open questions (#5) and lane B starts from a branch stack 1,359 commits behind main (#7). All of this was read on origin/main in a detached worktree, which is now removed. "Spec" means `2026-10-07-visible-game-spec.md`; "S1" to "S10" are the ten scout reports.

**Issues**

1. **Blocking. Contract wave (K1) declares functions with no owner to write them, and its tests cannot pass.**
   - K1 lists only the header, `signatures.toml`, `om_internal.h` and bindings (spec:30). The function bodies would have to go in `unit.c` (`om_tac_fire` is static at `unit.c:1924`, so the fire-event ring must hook there), `mission.c` (objective done), `tactical_mapgen.c` (obstacles), `fog.c` and `tactical_move.c`. S8's rows give `unit.c`, `mission.c` and `save.c` to VG-E and `tactical_mapgen.c` to VG-D.
   - The space-field, lots, density and strongpoint data are only created later, by lanes D and E1. So "every getter against a fixture world" (spec:34) cannot be green when the wave lands, and stubs would fail "wired, not just tested".
   - Smallest change: K implements only getters over state that exists today (structures, profiles, unit state bits, ability tick, sight, layer target/done, objective done, heights, obstacles enumerator, `set_layer`). It names the `.c` files it touches and owns them for the wave. The D and E getters move to amendments that land with their sim pieces.

2. **Blocking. Piece A4 draws "remembered positions (R-093) as faded marks" (spec:47).** The bible forbids this: R-089-04 says "there is no memory of last-seen positions", R-206-02 says "no marker on screen", and E-12:184 lists it under "Ways this could be wrong". Change: delete the clause from A4.

3. **Major. Lane A's "forbidden" list misreads the bible (spec:40).**
   - R-104-10 *requires* "a thin HP bar above it". S1 F8 only said the legacy screen lacked one.
   - R-104-01 *includes* "force routed" in the ticker, and says it recognises those four beats "and nothing else at launch". A8's ticker adds kills and ability casts (spec:51), which contradicts it.
   - Change: put HP bars back in A1; limit A8 to the four R-104-01 beats; flag "force routed" (no C source, S1 F5) as a sim gap.

4. **Major. Builders get choices the bible already fixes.**
   - A7 binds control groups 1..9; R-104-07 says 1 through 0.
   - A7 omits double-press-to-centre (R-105-02), Tab (R-105-03), narrowing by layer (R-105-06) and the Comb (R-105-07).
   - A3 binds `set_layer` to "X and shift+1..5". In the legacy screen shift+1..5 meant standing preference, which has no sim accessor (S1 F4), and the layer keys are undesigned (Q-110-04 answered (b); Q-232-01 open).
   - A10's "5/15/30 s" against R-136-01 (darken over 3 to 5 s) and R-136-03 (150-wreck cap); A9's "others projectile" against R-134-05 (volleys for Interceptor and Bombard).
   - Change: quote the rule numbers into A3, A7, A9 and A10, and route the layer key binding as a question.

5. **Blocking for lane D. It builds against open flags.**
   - Q-STAGE3-03 is `open` (register:44), yet lane D runs D1 to D8.
   - On Q-166-02 Westley said "this needs more design work so we can't write stories for it", yet the spec has the Architect write S-246.
   - R-188-05 ("all five are open at every position") is cited by R-236-03 and E-01 Q-001-01. Rewriting it changes what a rule means, so it is not a liberty.
   - D8's pass band is "a band Westley sets later", so that test cannot be written first. S-007 for plates is S5 flag 6, not routed.
   - Change: hold lane D until Q-STAGE3-03 and Q-166-02 are answered; move R-188-05 and S-246 into Westley's routed list; D8 needs his band first.

6. **Blocking. Stories that cannot reach `Seen`, and the Definition of Ready.**
   - CLAUDE.md says "a story is built only after it passes the Definition of Ready"; `agile.md:98` says "Only Ready stories get tests". Every listed story is Spec'd or "not scheduled".
   - Explicitly blocked: S-009 (Q-009-02), S-132 (Q-132-02), S-234 (Q-103-05), S-144 (Q-144-03), S-205 (Q-205-01).
   - Cannot be shown as specified:
     - S-133: tier ships as 0.
     - S-010: R-010-03 needs more than 5% vertical screen offset, which a 2D lane A cannot give.
     - S-090 and S-094: zones are stubs (`tactical_mapgen.c:500`).
     - S-089: R-089-03 says a hidden enemy is "not in the client's data", but the pipe sends every live unit (`om_pipe.c:1210-1215`).
     - S-238: needs workers and disguise, which are E2.
     - S-159, S-241, S-242: need E2 and Q-217-01.
     - S-193: the slowdown and cover parts are parked.
     - S-081, S-085, S-087, S-093: sim and balance claims a screenshot cannot judge.
   - Change: add one line Westley signs with his go ("this programme builds Spec'd stories; DoR is waived for the visual layer only"). Split each lane's list into "Seen-reachable" and "blocked on Q / E2 / C", and move S-010 to lane C.

7. **Major. Lane B's base is stale and its checks are known to fail.**
   - `push/A54-*` and `A55-names` are **1,359 commits behind** origin/main (measured), with 28 files and +2,395 lines. They include "A56 suspends A48-3, A48-4" (suspended checks).
   - B1 ports FIELD-EQ, which fails at 2.10% against 2% (S3). B5 needs a 3x speed-up (35.6 to 12 ms) with no approach given.
   - The plan says lane B "starts on Westley's look approval" (programme:41), but spec:102 runs B0 to B5 straight after the contract wave.
   - Change: a clerk merge-tree and test pre-check of the stack before the programme, with rebase or rebuild as fallbacks. Measure FIELD-EQ on the 80-region fixture before B1. Route the FIELD-EQ, REFILL and pixel-tolerance numbers (rulebook rows 19 and 20) to Westley with the look approval, and gate B1 on it.

8. **Major. Owner collisions the sequencing does not resolve.**
   - `autoload/qa_daemon.gd`: G2 and G3 (VG-GUARD) against VG-A (S8 row).
   - `save.c`: K4 has it in the contract wave, while section 6 gives it to VG-E.
   - `checksum_full.c` and `om_internal.h` are VG-CONTRACT's only, but E1's lots and strongpoints must be hashed and need new world fields.
   - The fire hook in `unit.c` is VG-E's, but A owns the events (S8's unanswered point).
   - B8's `scene_router.gd` is VG-F's. B9's `time_jump_sequencer.gd` is G-timejump's.
   - E1g's SettlementLayer has to be wired into `tactical_view.gd`, which runs through the A→C→D→F5 chain, and E is not in it.
   - VG-D and VG-F5 depend on VG-E, which stays in flight through E2. That parks multiplayer on Westley's economy answers.
   - VG-GUARD has no row; S8 wrote eight rows, not nine.
   - Change: split VG-E into E1 and E2 rows, add a VG-GUARD row, and add explicit handoffs for these seven files.

9. **Major. The contract wave's size, and what it leaves unpinned.**
   - About 20 getters, about 15 frame changes, the bridge and the save, against the "about one file and under about 100 lines" rule. With 37% of doers stopping (S9), one gate is all-or-nothing, and two rejections kill the whole run.
   - Not pinned:
     - The ABI bump (4 to N; rulebook row 27).
     - The `events[]` element shape and kind enum, and the ring overflow policy.
     - The `state` bit values, and which of `tier` and `state` re-pins rulebook row 22.
     - Field names for `profiles` and `structures`.
     - The packing and coordinate type of the space field.
     - Lot fields. The spec's own rule (spec:36) would leave lots out, yet E1f puts them in.
     - Whether `map` stays in full frames: spec:79 says "once per mission", rulebook rows 25 and 26 say full frames.
     - Cover `class`: a sim getter in K1 but a client radius threshold in section 7.
   - Section 2 says field names come from "the contract wave's `architecture.md` rev", which is circular, so tests cannot be written first.
   - The byte-identical test (spec:34) can never pass: `profiles[6]` is added to every full frame, and live missions have structures and a cover disc.
   - Change: split into K-a (lane A fields plus heights), K-f (`net_step`, `_setmode`, exe path), and later amendments for D and E1. Put a field table with names, types and enums in the spec. Make the identity test "identical after stripping the named new keys".

10. **Major. Lane C is underscoped.** Lanes A4, A5, A9, A10 and A3 draw in screen space. S4 says perspective radii "would have to be re-derived". C6 covers only A1's shapes. Change: add re-projection pieces for fog, the map layer, shots, deaths and layer rings, and re-run lane A's story plays after C.

11. **Major. Rows from the 49-row legacy inventory that lane A dropped with no reason given.**
    - Row 18 (structures drawn in the world) and row 31 (reinforcement panel, R-104-06): K1 sends the structures but no piece draws them.
    - Row 42: no piece sends `activate_ability`. The bridge allows only move, attack_move and attack_target (S1 row 42), so S-096 and S-086 cannot be acted out.
    - Row 47: ability visuals for S-135 (R-135-01..04).
    - Row 4: squads (R-132-03, 3 to 5 models).
    - Row 44: volleys and LOD.
    - Rows 48 and 49: ambient effects and the loading overlay.
    - A5 draws "zones", but zones have no data and no contract field.
    - Change: add pieces or state the reasons.

12. **Major. Budget arithmetic against S9.**
    - The spec has about 78 pieces (G8 + K4 + A12 + B11 + C9 + D8 + E1 about 18 + F8). S9's 52M expected was for 50.
    - Rescaled: 78 × 0.707 = 55.1M, retries 78 × 0.176 = 13.7M, 9 clerks 4.5M, audits 5M, reviewer passes about 1M. That totals about 79M, above the 75M ceiling. So the run's own expected path triggers the kill rule.
    - S9's "per lane ... 1.2M" is per piece: the p90s 340k + 537k + 312k sum to 1.19M. Read as per lane, lane A stops after about two pieces.
    - The 10M per-workflow cap is below lane A's expected about 11M and E1's about 16M.
    - Change: re-derive the numbers for 78 pieces, say "per piece", and split A and E1 into two workflows each.

13. **Major. Liberties that change what a rule means (design-level under the 5% rule).**
    - R-188-05 (see #5).
    - The Q-219-02 straight-line mover: Westley said "mark to be designed", and this picks candidate (b).
    - Q-173-01/02: Q-159-12 says "what tech will do exactly is undecided".
    - Q-167-03 is roster membership, not a "lab-set number", and touches R-238-01.
    - Q-180-01 (dial form) is borderline.
    - Unlisted liberties: E1c's 10 s rebuild, the `set_layer` keys, flyer altitude and shadow (S4: "a mockup is cheaper than guessing"), and ground colour.
    - The E2 liberties (Q-167, Q-170, Q-173, Q-174, Q-179, Q-180) are taken for work this revision does not schedule.
    - Change: route the design-level ones to Westley, add the unlisted ones to the table, and drop the E2 rows until rev 2.

14. **Major. Stop causes from S9 that no self-healing rule handles.**
    - Missing precondition (5 cases).
    - Contract need in lanes A to D (only the E2 amendment is reserved).
    - Reach-lint REJECT on a new unreachable symbol (`om_set_era_kind`).
    - "Tests were green, not red".
    - "Cause not found within budget".
    - Parallel ledger and `pieces.toml` conflicts (S8 found live ones).
    - A stop on a Westley-owned threshold (FIELD-EQ, REFILL, pixel tolerance, D8) currently counts as a failed check: two dropped lanes kill the programme, and B and D are likely candidates.
    - Change: add a "park on Westley threshold, not counted as a failure" rule, plus rules for the precondition and contract-need cases.
    - The flake rule also disagrees: the plan says "re-run once" (programme:82), section 4 says "up to twice". Pick one.

15. **Minor.**
    - Heights are int32 hex: 460 KB at 240² and 627 KB at 280², not the "230 to 314 KB" in spec:12.
    - The plate polygons are about 400 KB (S5) and missing from the 85 KB figure.
    - The 160 and 520 KB worst cases are S2's arithmetic, not measurements.
    - `push/land-1007b` does not exist on origin; it is `1007a` (programme:11).
    - G1's `look` stage has no positive control.
    - G5 depends on Agora `relay/05` and `relay/07`, which are not landed and not sequenced.
    - The 240 vs 280 cell cap (S4) is not addressed.
    - iGPU and Compatibility-renderer cost for lane B was not measured (S3).

**Verdict: approve with the listed changes.** The lane structure and guards hold, but the contract wave as written cannot pass its own tests (#1, #9), A4 breaks a bible rule (#2), and lanes B and D start on unverified ground (#5, #7). Fix those first.
