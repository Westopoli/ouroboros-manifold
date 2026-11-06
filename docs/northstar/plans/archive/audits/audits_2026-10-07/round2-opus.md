# Audit round2-opus (2026-10-07)

Verdict: approve with the listed changes. Lane structure, guards, the K0/K-a/K-f split and the D hold are sound, but as written K-a cannot pass its gate (#1, #2), K0 can trip the reach lint (#3), and an ordinary failure path can end the run with nothing visible landed (#7, #8).

I read rev 2 on origin/main at f78540fa in a detached worktree, now removed; nothing was edited.

**Blocking**

1. **K-a's hidden-unit filter breaks tests the rulebook protects or never lists.**
   - Row 26 is on the do-not-touch list. Its test `tests/test_tactical_delta_reconstruction.gd` needs at least two factions in the first frame (:107) and averages enemy positions from that frame (:141-151); with no visible foe it divides by zero.
   - The same test treats any disappearance as a death (:157-160). A unit fogging out would pass that check for the wrong reason.
   - Four transport tests read enemy positions from the first frame and have no rulebook row: `test_pipe_assign_commander.py:85-87`, `test_pipe_tactical_tier_state_reserved.py:64-65`, `test_pipe_macro_group_orders.py:59-60` (which fails as "vacuous" with no enemies), and `test_pipe_tactical_delta_frame.py` (the nearest-enemy attack, :21).
   - K-a's own identity test ("identical after stripping the named new keys") also fails, because the filter removes units rather than keys.
   - Structures are still sent unfiltered, although R-205-02 has the same "not in the client's data" clause.
   - Smallest change: take the filter out of K-a into its own amendment, behind a session flag the game client sets (for example `mission_start "fog_filter":true`, off by default). Add rulebook rows for these tests, and state the delta rule: a unit that leaves sight goes in `units_removed`, distinct from a `kill` event. Otherwise keep S-089 blocked.

2. **Rulebook row 22 is on the do-not-touch list (rulebook:50), but spec §3 has K-a re-pin it.** K-a's `state` bits turn `test_pipe_tactical_tier_state_reserved.py:88` red, and the ruling agent must then refuse under condition (5). Separately, K-a says "units gain `tier`" while the tier source (A30) is routed to Westley.
   - Smallest change: move row 22 off the list with an RP rule (re-pin to the new literal, quoting the spec) for `state` only; `tier` stays pinned at 0; drop "gain `tier`" from K-a.

3. **K0's stub test can trip the reach lint.** `reach_lint.py:65-71,170-179` counts any `lib.om_x(` call or `getattr(lib,"om_x")` from a test as "tested", and rejects a new tested symbol that nothing in the running game reaches. Only names matching `_get_|_count$|_is_|_has_` are exempt.
   - Not exempt: `om_structure_at`, `om_objective_done`, `om_fog_sight_radius`, `om_unit_layer_target`, `om_unit_layer_done_tick`, `om_map_obstacle_at`, `om_terrain_dump_heights`. In K0 these are stubs no pipe code calls yet. Two rejections of a contract gate trigger the kill rule.
   - Smallest change: the stub test checks presence with `hasattr` only, or the names take `_get_`.

**Major**

4. **The landing order contradicts itself.**
   - §6 orders the `tactical_view.gd` chain (VG-VIEW) as A12 → C5 → E1p → F5 → D hook. Lane F's text (and the parallelism audit, §3 item 7) says F5 comes "right after A12".
   - §1 lands the VG-VIEW chain (including C5 and E1p) before C's 3D and before the E1 sim. So C5 hosts C2–C4, which are not yet on main, and E1p wires E1k, whose lot fields arrive with K-e later.
   - Smallest change: chain A12 → F5 → C5 (after C2–C4 land) → E1p (after K-e).

5. **Owner gaps remain.**
   - Heights decode: C1 ("bridge heights decode") and K-a (`c_bridge.gd` heights) duplicate it, and VG-C does not own `c_bridge.gd`. The parallelism audit flagged this; it is still open.
   - A14 lists "+ bridge `activate_ability`", duplicating K-a. The pipe verb already exists (`om_pipe.c:1758`).
   - C10 re-projects A's files (`fog_layer.gd` and the others) under VG-A's glob with no handoff.
   - K-e (E1i) edits `om_internal.h`, `checksum_full.c`, the header and the pipe, all VG-CONTRACT files. No handoff is listed (round-1 #8, half done).
   - E1h edits `unit.c`/`mission.c` while K-a holds them, since K-a "runs beside the lane builds". That is two in-flight owners of one file.
   - `tests/qa/desktop/plays/` is shared by every lane and has no owner.
   - Smallest change: delete C1 and A14's bridge clause; add the handoffs; sequence E1h after K-a lands; give plays per-lane subdirectories.

6. **The T0 start breaks "nothing builds against a missing precondition".**
   - B1–B5 and B7 start at T0 beside B0, whose result (rebase or rebuild of a stack 1,360 commits behind) is their base.
   - E1's test writers start at T0, but its lot, density and strongpoint shapes exist only in K-e (E1i, placed after E1a–E1h). §2 has no E1 fields.
   - K-a's `terrain.c` piece needs the 240/280 cell cap, which is still a Westley question. `terrain.c:345` notes that more than 24000 wu "needs the mapgen grid widened", so 280 grows K-a.
   - Smallest change: T0 starts B0 only for lane B. Put K-e first in E1, or move E1's tests to after it. Default the cap to 240 (today's limit) and treat 280 as a later amendment.

7. **The park rule has no gate mechanism and can empty lane B.**
   - The gate compares failing-test sets, so a red parked test rejects the candidate. Making it pass needs a skip or xfail, and CLAUDE.md forbids reclassifying a real finding as a skip.
   - FIELD-EQ is B1's test, and B2–B9 build on B1, so "the lane lands everything else" lands nothing.
   - Smallest change: a parked test file is held off the candidate and listed, and the code it covers lands.

8. **The kill rule can end the run with nothing visible landed.**
   - One piece reaching its 2.4M hard stop, or "cause not found", stops the lane. A stopped lane drops its dependents (C5, C6, C10, E1p, F5), which makes two lanes dropped: kill.
   - A double reject of K-a kills everything, including B and the F scripts, which need no contract.
   - G1's `look` stage does not say whether it compares against main (regression mode, as `reach_lint` does) or checks frames in absolute terms. If absolute, today's 24 px grey stub may fail every candidate until A12 lands. Its near-uniform threshold is Westley's but is not on the routed list.
   - Smallest change: a stopped piece parks only that piece and its dependents; a contract double-reject stops only the lanes that depend on it; land B with the F scripts right after GUARD; make `look` regression-mode and route its threshold.

9. **The budget arithmetic is wrong again.**
   - §8's own components sum to 90 pieces, not 82: 8+7+17+10+11+9+20+8. The lists themselves give A 18 (not 17) and B 11 (not 10).
   - "Contracts 7" counts gates, not one-file pieces: K-a alone touches 9 files and K0 3.
   - At 90 pieces the expected cost is about 91M. At about 103 per-file pieces it is about 104M, against the 110M ceiling.
   - A's first workflow has 11 pieces; at p90 that is 13.2M against the 12M per-workflow cap.
   - Smallest change: recount and restate.

10. **K0's field table cannot carry the T0 tests.** §2 lacks:
    - the `state` bit values (round-1 #9 asked for them);
    - what "in flight" means; the sim has no such state (only a comment, `unit.c:1336`);
    - types and per-tick/periodic/once cadence for `acd`, `tl`, `ld`;
    - `structures_changed`/`removed`;
    - the event overflow counter's field;
    - the next unit type and the production period. R-104-06 needs a "next unit icon" and a timer bar, and `nst` alone gives neither;
    - `ability` and `aoe` in `profiles` (Bombard's volley).

    The inventory keys and node names have nothing for A1b, A7b, A13, A14, A15, E1l or E1n, so their element-inventory tests cannot be written.
    - Smallest change: complete the §2 table.

11. **The cover class is decided in two places.** K-a makes it a sim getter and §7 makes it a radius liberty (round-1 #9 again). Smallest change: say the sim applies §7's thresholds.

12. **The Seen-reachable lists claim stories that cannot be reached.**
    - S-090 and S-094 are listed, but zones were dropped for having no data source.
    - A4's test column covers S-089–S-094, so it includes S-093, a sim/balance claim.
    - S-235 sits in E1, but its beats (occupation, weather, expansions) are E2. It is "not scheduled" in `stories.md`.
    - S-193's parked parts are not marked.
    - Smallest change: move these to the blocked lists.

13. **The go line waives only the Definition of Ready.** CLAUDE.md also says "An epic with an open flag is not built". E-16 (Q-232-01, Q-103-05), E-18 (Q-132-02), E-12 (Q-205-01) and E-22 (Q-168-05) are open. Smallest change: the go line names that rule too.

**Minor**

14. **The layer keys are still a guess.** A3 builds "narrowing by layer hotkey (R-105-06)", but Q-232-01 asks whether that hotkey shares the number keys with groups 1–0 and the ping. Smallest change: A3 waits on the same routed answer as `set_layer`.

15. **Stale text.**
    - Programme:11 still says `push/land-1007b`.
    - Programme:40-47 and :99 still carry rev-1 counts, order and "D (Q-STAGE3-03 → yes)".
    - Rulebook row 7 still mentions "remembered-fog marks".
    - §7 still lists the E2 liberties (Q-167, Q-170, Q-174-02, Q-179-02, Q-180-01), which §0 says were dropped.

16. **Builder guesses left open.**
    - Whether fire or kill events whose shooter or victim is hidden are sent, and where a shot is drawn from.
    - How `events` accumulate over n>1 steps against the cap of 512 per step.
    - Which progress values count as "objective threshold crossed" (R-104-01).
    - How E1m feeds A8 without editing `events_feed.gd`.
    - Whether "defaults omitted" also covers `state`. The reserved test's control (:98) treats a missing key as a violation.

**Round-1 items not fully resolved:**
- Opus #1/#9: field table gaps, cover class, and K-a still one gate with an oversized `om_pipe.c` piece.
- Opus #6: zones, S-235, the open-flag rule.
- Opus #7: B builds before B0 and parks on B1.
- Opus #8: no K-e handoff.
- Opus #12: the arithmetic.
- Opus #13: the E2 rows are still in §7.
- Opus #15: `1007b`.
- Parallelism: the C1/K3 duplicate, F5 after A12, and K2's three-way split.

**Resolved:** Opus #2, #3, #5, #10, #11 and #14, plus parallelism's T0 tests, K0, GUARD order, pairs, the lab night run and the `space_*` split.

**Verdict: approve with the listed changes.** Fix #1 to #3 before launch and #4 to #10 in rev 3.
