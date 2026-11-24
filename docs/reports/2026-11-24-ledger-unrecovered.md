# Ledger backfill: approvals that could not be recovered (2026-11-24)

Ledger: `docs/northstar/story_reviews/westley/approved_scenes.toml`, 4 rows (stage 3, L-0055, L-0073, L-0084, L-0039, seed 10, all PASS on re-run at the pinned sha, byte-identical to the fight file he was shown). Rule used: a row needs a main sha that carried the lab and engine he watched, and a re-run whose output is the recorded fight. Anything else is listed here, not guessed.

## Scenes approved but not re-runnable at a main sha

| Approval | His words (date) | Why it has no row |
|---|---|---|
| Stage 1, L-0054 128 against 128 (movement and group arrival) | "straight draw isn't possible, that result is perfectly fine by me. Stage 1 approved" (2026-11-01, 23:32 local, chat 23477a3c line 818; DEC-stage1-seen-2026-11-01) | He watched a scratch merge of the H-057 branch into the stage 1 branch (`FIGHT L-0054 seed 1 winner B ticks 8167`). The H-057 engine was not on main until after 2026-11-02 11:03 and no commit holds that run. The file committed that night (`6de4a0f64`, 2026-11-02) is a different run (winner A 9:0, 8954 ticks). Route if wanted: pin the scratch merge's two branch tips (the Architect's call), re-run, compare to 8167 ticks. |
| Stage 2, SIT-0101, 0103, 0104, 0108 | per-fight "approved" words, 2026-11-02 11:03 local, chat 23477a3c line 2273; verbatim in `crossings.md` | Main at that moment (`be19ff950`) has neither H-057 nor `scripts/skilllab/arena/situations.py` (`No module named scripts.skilllab.arena.situations`); the pictures came from scratch copies. |
| Stage 2, SIT-0105, 0106, 0107 | same message; 0106: "this one also had the correct outcome, approved." | As above, and the situation files then carried arc radii the converter refuses; the approved radii were put back only on 2026-11-18 (DEC-sit-radii-2026-11-18). Re-running would use a file the approval day did not have. |
| Stage 2, SIT-0102 | denied, not an approval | Not a row. |

## Approvals with no scene to pin

| Statement | Date | Why |
|---|---|---|
| "the movement system is working as I approved it (from the times I've viewed and approved the movement in godot)" (chat 5404584c line 3231; DEC-stuck-behind-is-expected-2026-11-19) | 2026-11-18 | A reference to earlier approvals, with no scene named. The scenes it points at are stage 1 and stage 2 above (unrecovered) and stage 3 (rows). |
| 13 attack-move rulings (`docs/reports/2026-11-18-attack-move-drift.md`) | 2026-10-02 to 2026-11-18 | Rulings on rules, with no scene he watched; they belong in requirements, not this ledger. |
| Stage 4 (L-0061, L-0080, L-0083, L-0039) | 2026-11-05 layouts; 2026-11-18 look | No approval: ruled.md records "answered-awaiting-him"; two small breaks found, then "That's a bug, investigate" (2026-11-18). |
| Stage 3 per-fight verdicts | 2026-11-05 | He gave none. The four rows carry the stage-level words ("I rule approval on stage 3, we are go to move to stage 4"), and the `source` field says so. |
| Static pictures (catalogue verdicts, H-025 rounds, verdicts_2026-10) | various | Out of scope by the brief (scenes, not pictures). |

## Notes for the rig

- The stage 3 rows run the lab at the pinned sha in a scratch copy (`git archive`), so `verify` needs only the repository's git objects, not the checked-out code. Each takes about 15 seconds.
- Stage 3 L-0039 ends in a 600 s cap draw (8 against 8), recorded as he approved it; DEC-draws-are-defects-2026-11-18 later made such a draw a defect. Treat that row as a record of the approved picture, not as a current expectation.
- `requirements` on the rows (R-097-01, R-097-03, R-097-05) are the Architect-side reading of "units respect the ground"; he did not name rules.
