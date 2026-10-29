# Handoff, Mac chat to Linux chat (2026-10-19)

Read this first on the Linux box. It is the whole state the Mac chat held; nothing else lives in that chat's memory. Then open `docs/northstar/plans/decision_pack_2026-10-18/answers.md` and follow the instruction at its top **exactly** (do not read past its "## Batch A" line yourself; spawn a sub-agent per three points with only the files, the question verbatim and Westley's response; an agent whose task is a back-and-forth stays alive until the overlord chat releases it).

## Where things stand

- **Westley's batch is partly answered.** `answers.md` covers Batch A pictures 1 to 11 (of 24); parts B and C are unanswered. Nothing from `answers.md` has been folded into the register, the epics or the queue yet. The pack: `decision_pack_2026-10-18/batch.md` (the stories' voice), `README.md` (index; section C lists the implementation decisions the Architect took, Westley may veto), `register_extract.md`, `doc_branches_digest.md`.
- **Two audits Westley asked for at the top of `answers.md`**, before or beside the per-point work: (1) every prototype, screenshot and in-flight feature audited for consistency with his decisions and rulings (several Batch A answers are "investigate why what I decided did not reach the prototype"); (2) an analysis of how decisions reach specs: where the gap sits between what was ruled and what the building agent was given. Both are fresh-Sonnet read-only audits reporting to him unedited; the drift-audit procedure (`workflows_2026-10-07/drift_audit.md`) is the pattern.
- **Standing rule (Westley, 2026-10-18):** implementation decisions are the Architect's; only rules, thresholds and tolerances, looks and process are his. Decide, record ("Architect, <date> (implementation; Westley may veto)"), tell him in one line.

## Branches waiting for the Linux gate (all pushed; none landed)

| Branch | What | Tests |
|---|---|---|
| `push/proto-transition` e4d8e6bd | transition mockup, S-108, pass 1c (star field) | 27 green; Westley: not approved yet, wants to run it and the architecture explained (answers 1, 2) |
| `push/proto-terrain-obeys` 804f666b, `push/proto-terrain-obeys-2` f57af240 | terrain obeys the layout, passes 1 and 2 (route carving) | pass 2: 316 green, all six cases; Westley: not approved, colour legend and layout-engine-first feedback (answers 3, 4) |
| `push/simlogs-tests` + `push/simlogs-tests-2` | SIM-LOGS ring, appends, readers, flag tests (red on main by design) | spec `2026-10-15-sim-logs-spec.md` rev 4, rulings taken; needs the second-Fable audit (Dispatcher spawns it) or Westley's waiver (pack B5) |
| `push/chron-context-tests` 1c2e40b6 | CHRON-CONTEXT tests (4 red by design) | spec `2026-10-18-chron-context-spec.md`; after SIM-LOGS |
| `push/alg-cover-e08-e10` d1be855a | 11 ALG coverage tests, 311 green, 1 red (ALG-49 successor region, pack B23) | land through the gate; findings in the sim lane ledger rows 18 to 24 |
| `push/const-2` 32fb5c2b | CONST-2, code reads 18 named constants, byte-identical | gate |
| site repo `~/Projects/ouroboros-site` branch `refresh-2026-10-18` | website draft (T8), local to the Mac only | Westley's publishing answers (pack B22) |

## Build order for the week (the Dispatcher's, from the state; Westley's answers may reorder)

1. Full csim suite on Linux as the baseline; diff against `sim_lane_2026-10-12/runs/2026-10-18_mac/csim_top.summary.txt`.
2. The `answers.md` points, three per agent, per its instruction; the two audits beside them.
3. Gates for the branches above (prototype branches do not land; they are judged by eye).
4. SIM-LOGS build after LAB-REV2-E0, CONTRACT-cone-state, VG-CONTRACT-E7, VG-E-prodslot, VG-E-startforce, B5 land (its `depends_on`); then CH-1, CH-2, CH-3 and the mission swap as a skeleton seen in the sim viewer; then CHRON-CONTEXT, SEL-ORDER, CONTROLS-IDS-1 (`controls_triage.md`).
5. Lane fix pieces from the picture verdicts as they come.
6. The lab: the Mac could not finish a 200-layout layout search in an hour (`runs/2026-10-18_mac/README.md`); lab rev 2 runs on Linux.

## Facts the Linux chat should not re-derive

- The macOS pipe builds, is signed ad hoc, and its full checksums equal the Linux pins (`2026-10-18-macos-pipe-probe.md`); Q-NET-05 closed (a) after PROBE-2.
- The mission generator silently swaps 14 percent of missions (Defensive Stand without an attack); the chronicle drops the family entry past a 256-candidate cap, pushes chain clusters at score 0, and emits blank shells: all confirmed with counts (`sim_lane_2026-10-12/README.md`, rows 3, 7, 8, 9, `finding_chronicle_internals.md`). The Python reference kept three jump logs the C port dropped; SIM-LOGS restores them.
- Mac-only reds: the `-msse2` probe builds (8 errors), `test_W7_library_imports_no_sin` (`nm -D`); the A99 hashes are red on Linux too (a harness `math.hypot`, TD-SIM-5).
- The drift audit procedure is in the repo (`workflows_2026-10-07/drift_audit.md`); last run 2026-10-18, fixed in `20d7436d`.
- 250 branches are proven landed (`branch_triage_2026-10-15/delete_list.txt`); the guard denied the delete; Westley runs it or rules again.
- The seven doc branches question (`doc_branches_digest.md`): two map-design branches are already on main; the other three wait on his a/b/c.
