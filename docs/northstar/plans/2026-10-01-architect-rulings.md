# Architect rulings, 2026-10-01 (mission-plays plan, Waves A and B)

Answers every item under "Architect rulings needed" in the coordinator's 2026-10-01 continuation note. Rule text changed in the same commit: E-10 R-072-08, E-09 R-065-01/02/06, E-08 R-055-06, E-16 R-103-08, E-13 pipe budget, register Q-065-03. Where a ruling says "contract piece", the shape below is approved: land it as a docs-profile piece (header, `signatures.toml`, `symbol_modules.toml`, conftest binding, `docs/architecture.md`) before its consumers.

Four of these were Westley's decisions (2026-10-01): the pipe budget, the attack-move input, the chronicle cap, the band mapping. The rest are implementation rulings from the existing rules.

## A3: the quiet-world fallback (R-072-07, R-072-08)

1. **Which enemy.** The non-player faction nearest the fallback region by connection hops (breadth-first over the region graph); ties go to the faction with the highest total military, then the lowest faction id. "Adjacent" was too narrow: in fallback worlds the player borders only its own and neutral regions.
2. **"Strongest" / total military** = the sum of `OM_F_MILITARY` over the faction's regions.
3. **Parity direction.** R-074-04 stands: the enemy's power is P, the player's budget is P · parity. P for the fallback = the enemy faction's strongest region's military × 2000 (R-074-01's default form), raised to the power of one unit of the enemy's cheapest profile if it would otherwise field nothing. The A3 tests assert the player's budget against P · parity; a test asserting "enemy ≥ parity × player" is rewritten by the Engineer (rule text changed, ledger row).
4. **Contract piece (header).** One function: `void om_mission_setup_fallback(om_world *w, uint32_t region_idx, int32_t enemy_faction);` It sets the archetype to Defensive Stand, the region, and the enemy faction; enemy power follows item 3 inside `mission.c`. No parity-floor parameter. Then `mission.c` (B9-N) implements, then `om_pipe.c` (T1-N) does the five retries, the weakest-region pick and `quiet_world`.
5. **`quiet_world` is in the mission frame only.** It is not added to the T1 trace; no ABI change. R-072-08 no longer mentions the trace.

## A4: the briefing

1. **Frame shape.** The documented nested shape stands: `{archetype, region, deadline_ticks, objectives[{i,kind,node,primary,radius,progress}], force:{types,tiers}, quiet_world}`. The plan's "top-level node/radius/force[]" wording yields to the contract.
2. **No `position_name`.** Frames carry no names. The client derives the position's name from `objectives[0].node` and `region` with its existing derivation (`chronicle_names.gd`).
3. **Briefing text.** New frame field `"briefing":{"situation":"...","objective":"...","assets":"..."}`, the three `om_briefing` texts from `om_mission_assemble_briefing`, all three (R-079-01); a part whose `has_*` is 0 is an empty string. Contract piece: `docs/architecture.md` only, no header change.
4. **Parity.** New numeric frame field `"parity"` (data for tests and QA). The client never renders it; the Assets text already states parity in prose (R-079-01, R-079-04).
5. **`force.types`** is six counts, one per unit type in type-id order; `force.tiers` is the tier per type. The worked example `[2,2,1,0,0,0]` is correct as written.
6. **HDR4 accessors.** Rebuild on fresh main as `HDR4-2-r` (contract piece): objective node and radius, force count and unit accessors, commander unit getter. Start from `~/Projects/om-push/wt/HDR4-2-r`'s uncommitted work as reference; do not merge `push/HDR4-2`. A4-pipe builds after it lands.
7. **The 2 reds in `tests/test_briefing_debrief.gd`** are a separate Engineer investigation (hypothesis: the test's seed-1 bridge world differs from the live world in archetype and deadline); not part of A4, and not reclassified as skips.

## B5: the chronicle

1. **Band to outcome** (Westley): total_success and strong_success give success; partial_success and partial_failure give mixed; total_failure and refusal give failure. In R-065-02.
2. **`om_chronicle_distill_candidates`** yields no entry of its own. It is the scored candidate list that ranking (R-065-03 to R-065-06) consumes; `gen_time_jump` calls it between scoring and cluster building.
3. **No repeat.** The consequence cluster appears only in the jump that directly follows the mission; the flag is cleared once that scroll is built. A retry jump or a second jump has none.
4. **Wiring, no header change.** `gen_time_jump` feeds chain events, calls `om_chronicle_build_chain_clusters` and the three categorize functions, adds the consequence event from the last mission's result (`om_mission_last_region`), and builds the `consequence_ripple` cluster from flagged events in adjacent regions (Q-067-01). `om_chronicle_consequence_entry_count` and `om_mission_has_mission_consequence_flag` stop being stubs.
5. **Cap wins** (Westley, Q-065-03): never more than 2 entries per category; a quiet jump may show 4. The earlier test fix that expected 5 is reversed by the Engineer as a test-defect with a ledger row.
6. **`pieces.toml`:** `B5-chronicle` depends on `A2-contract`, not on B7b.

## B6: the chapter lifecycle (new rule R-055-06)

1. **When the chapter advances.** Once, at the end of each jump that follows a mission (played or refused). A retry jump with no mission never advances it.
2. **The opening jump** belongs to chapter 1 and does not advance it.
3. **Order at the end of such a jump:** collapse check, mission generator, character selector, chapter advance. The generator runs once per chapter, here; `mission_start` reads its result. If `handle_mission_start` does its own selection today, move that call, do not run selection twice (a second weighted draw would break determinism).
4. **Test fixture.** No debug verb in the shipped pipe. The Engineer searches seeds 1 to 400 for a campaign where the lineage loses its last living member within three jumps and uses that seed in the transport test; if none exists, the rotation path is proven by a core test through the same public functions `handle_jump` calls, and `reach_lint` proves the wiring.
5. **Contract piece.** Snapshot frame gains `"chapter"` (uint) and `"commander"` (character id); the chronicle frame's `jump` object gains `"chapter_end_reason"` (0 normal, the `GEN_CHAPTER_END_*` values). Header: add `uint32_t om_campaign_commander(const om_world *w);` only if no existing getter returns the current commander's character id.

## A6 follow-ups

1. `tests/test_tactical_view.gd` against `tests/test_tactical_camera.gd`: the Engineer reconciles them now that enemies exist at mission start; a fixture that assumed an empty field is a test-defect with a ledger row.
2. **Objective progress in the HUD.** Contract piece: the tactical frame gains `"objectives":[{"i":0,"progress":0.0}]`, then T1-N, then C5-N.
3. **`_session_mission` reach-in.** `autoload/c_bridge.gd` gets a public `mission() -> Dictionary`; the HUD uses it.
4. **Attack-move** (Westley): press A, then left-click. R-103-08. `settings.gd`'s "A+RMB" text is corrected. The rest of Q-103-04 stays open and blocks nothing here.
5. **Ownership.** `scenes/tactical_c/**` belongs to C5; C8 loses that glob. A6 work takes `C5-N` ids.

## A7: pipe cost

Budget (Westley): one `tactical_step` round trip under 50 ms at 5,000 units (E-13). Order of work: (1) contract piece for a delta tactical frame: `units_changed[]` each step, a full `units[]` frame every 20 steps and on request; `visible` only for the player's faction; when `tactical_step` carries `n > 1` only the last frame is written; (2) T1-N; (3) C5-N; (4) re-measure with `scripts/bench_tactical_pipe.py`. If still over budget, profile the sim step itself and report; do not tune anything further without a ruling.

## Housekeeping

- Piece ids: plan labels (A1, A2, ...) are not piece ids. Use the owning piece's next increment (`T1-N`, `B9-N`, `C5-N`, ...). Add one `pieces.toml` row `DOCS-arch` owning `docs/architecture.md` for contract docs pieces.
- `docs/northstar/plans/briefs/leaf-mechanics.md`: replace `sonnet46-doer` with `doer`.
- `scripts/run_godot_tests.sh`: unset `DISPLAY` and `WAYLAND_DISPLAY` inside the script; replace the frame-counted `--quit-after 300` with a limit that lets `test_tactical_camera` finish (Engineer picks the mechanism, reports the value).
- Westley's live checkout has an unpushed local commit `9a83096` duplicating `f005eaa`; it is his to drop. Nobody else touches that checkout.
