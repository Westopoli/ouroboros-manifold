# Audit round3-opus (2026-10-07)

**Round-3 audit of the visible game spec (rev 3, origin/main a843c91d)**

**Verdict: approve with the listed changes.** The lanes, the K0/K-a/K-f/K-h split and the D hold are sound, and most of round 2 is fixed. But K0 and K-a can still stop on their own text, and the K-h, park and look-stage rules lack a working mechanism. Every fix below is a text change.

I read rev 3 in a detached worktree, which is now removed. I edited nothing.

**Round-2 status.** Resolved: #3, #11, #12, #13, #14, #16. Only partly resolved:
- #4: the order line in §1 is still wrong (item 8).
- #7 and #8: the mechanisms are missing (items 7 and 9).
- #9: the piece count is still low (after launch).
- #10: getter names are missing (item 1).
- #15: the programme text is still stale (item 10).
- #1 and #2: fixed, but each fix brings a new defect (items 6 and 2).

**Must change before launch**

1. **Blocking: K0's symbol list duplicates existing getters and misses others** (spec:11, :36-37).
   - These already exist in the header: `om_unit_get_target_layer` (:1917, the spec proposes a new `om_unit_get_layer_target`), `om_fog_get_drawn_sensor_circle_radius` (:1530), `om_structure_get_hud_data` (:1953), `om_unit_is_braced` (:1908), `om_unit_transition_progress` (:1916), `om_unit_ability_cooldown` (:2029), `om_unit_in_backswing` (:2047) and `om_tick_read_ability_events` (:2027, which empties its buffer when read).
   - The pipe reads the sim only through the public header (`om_pipe.c:64`). Yet K0 declares no reader for fire, kill or capture events. No K-a piece produces kill or capture events. No getter carries `acd`, `acd_max` or the structure `stage`, and `stage` is never defined.
   - Smallest change: in K0, reuse the existing names, add the event reader under a lint-safe name (for example `om_tactical_event_count`/`_get_at`), put kill events in `unit.c` and capture events in `tactical_support.c`, and define `stage` (0 until E1).
2. **Blocking: rulebook row 22's re-pin of `state` breaks its own control.**
   - The test's control (`test_pipe_tactical_tier_state_reserved.py:97`) asserts that `state=1` is rejected, and its detector (:57) is `!= 0`.
   - Re-pinning therefore needs a new assertion shape and a changed control. Decision conditions (3) and (4) forbid both, so the ruling agent refuses and K-a stops.
   - Smallest change: row 22 spells out the edit (`state` present and `state & ~7 == 0`; the control plants `state=8` and a missing `state`) and permits that control literal.
3. **Major: K-a's own identity test cannot pass** (spec:37).
   - After K-a, `state` is non-zero for units that fired. Units also enter `units_changed` when `state`, `acd`, `tl`, `ld` or `sight` change, and the dead-slot fix can change which units appear at all. So frames are not identical to main's after stripping the new keys.
   - Smallest change: compare reconstructed full views with `state` set to 0 and the new keys stripped, on a fixture the dead-slot scan does not affect.
4. **Major: two pieces own the same file at the same time.**
   - K-a and K-f run in parallel (spec:30) and both edit `om_pipe.c` and `c_bridge.gd` (:37-38). CLAUDE.md says two in-flight pieces never own one file. Scout 8 also says `net_step` must follow the frame fields.
   - K-h (after A4) and K-e (E1's first piece) both edit `om_pipe.c` and `c_bridge.gd`, and nothing orders them. K-h is also missing from the landing order.
   - Smallest change: K-f starts after K-a's pipe and bridge pieces pass their check. State "K-h lands before K-e starts".
5. **Major: T0 starts G1 without its base.** G1's `look` stage needs a near-uniform threshold that §7 routes to Westley (spec:122, :130). Smallest change: G1 ships `look` as warn-only (frames attached, metric reported) until Westley sets the number.
6. **Major: the claim that `fog_filter` is off in tests is false for tests that start missions through the bridge.**
   - Tests and the game share `c_bridge.gd` `_ensure_mission`/`load_tactical_live` (:498-501, :558). If K-h's bridge piece "sets the flag" there, `test_tactical_delta_reconstruction.gd:93-107` runs with it on. That file is row 33 and do-not-touch row 26.
   - `test_flow_spine.py:444-447` (S-C8-09) needs at least two factions in `qa.units` and has no row.
   - Smallest change: the flag is a bridge parameter, default off, set only by `tactical_view.gd`'s live call. Add a row for flow_spine with its rule decided now.
7. **Major: the park rule has no mechanism a script can run.**
   - The footprint fence only warns about owned files missing from the diff (`merge_gate_support.py:236-247`), so leaving a file out passes the gate.
   - But nothing requires a threshold assertion to sit in its own file, so holding a file off can take a piece's other tests with it (B1). Nothing says where a held file lives.
   - Smallest change: test writers put each threshold check (FIELD-EQ, REFILL, pixel tolerance, the D8 band) in its own `*_park_*` file; the clerk leaves it off the candidate and keeps it on a branch such as `push/vg-parked`.
8. **Major: the landing order in §1 still contradicts itself** (spec:30).
   - "VG-VIEW: A12 → F5 → C5 → E1p → D hook → C's 3D → E1 (K-e first) → D" puts C5 before C2–C4, E1p before K-e, and the D hook before D. Encoded literally, the script deadlocks.
   - Smallest change: write it as dependency edges (C2–C4 land → C5; K-e lands → E1p; D lands → D hook).
9. **Major: the kill rule has two undefined terms.**
   - "Two lanes dropped by failures" has no definition once failures only park pieces. It is also unclear whether lanes stopped by a contract double-reject count.
   - The VG-VIEW chain only orders who holds `tactical_view.gd`. If F5 parks and its "dependents" park with it, C5, E1p and the D hook park too.
   - Smallest change: define "lane dropped", and say a parked link hands `tactical_view.gd` on to the next link.
10. **Minor: stale-doc rule, and one undecided source branch.**
    - Programme lines 40-45 still carry rev-1 sizes and stories (A "10–12", with S-009/S-133 listed). Line 99 still has the rev-1 launch order and "E sim pieces now". Rev 3's §0 says this was fixed.
    - A1 says "from tv-read", but the spec never says what happens to `push/tv-read`: it edits `tactical_view.gd` and carries `test_tactical_readability.gd`. Smallest change: one line, "source only; its test is adopted for A1/A5 or dropped".

**After launch**
- **Budget recount from §1:**

  | | Spec | Recount |
  |---|---|---|
  | A | 18 | 20 (A13 and A15 are two pieces each, plus A12) |
  | K0 | 3 | about 9 (6 `.c` stub files) |
  | C10 | 1 | 5–6 files |
  | E1 | 20 | about 22 (16 pieces plus K-e's ~7 files) |
  | Total | 103 | about 117 |
  | Expected | about 103M | about 115M (ceiling 140M) |

  At about 15 pieces, C's single workflow is about 18M at p90, over the 14M per-workflow cap. Split C, or split C10 into one piece per file.
- **C10's handoff:** it says five files but lists six things. The rings live in `layer_view.gd` or `unit_visuals.gd`, so leave them in the handoff and the footprint fence rejects the edit. Name the files.
- §6 and lane D still say "E1h after K-a" and "after E1h". The `mission.c`/`unit.c` wiring piece is now E1i.
- Save format 8 is in both K-e and E1j.
- Rulebook row 3 (C: ARCH for perspective zoom) is a stop you can predict for C5. Rule on it before C starts.
- Write the `state` bits as values 1, 2 and 4, and say whether "fired" covers any of the n steps.
- §6 still gives the contract row (`VG-CONTRACT`) only "the named lines" of the seven `.c` files. The footprint fence checks whole files, so list the files.

**Approve with the listed changes.** The plan is sound, but items 1–4 stop K0 or K-a at their gates and items 5–9 leave GUARD, K-h, parking and the kill rule without a mechanism. All ten are text fixes.
