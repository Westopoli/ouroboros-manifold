# Story review queue

Every story play that reaches the player's eyes gets a queue row. Westley approves or rejects it. Only then does a story become `Seen`.

## Files

`docs/northstar/story_reviews/<lane>.md`, one markdown table per lane, columns in this order:

| story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) | Westley verdict (pending/approved/rejected) | date |
|---|---|---|---|---|---|---|---|---|

### Lane key

The single-letter files are the lane tables, one per area of the game. They are read by `scripts/specfactory/batch_review.py` and matched by `scripts/specfactory/pieces.py`, which is why they keep their short names.

| File | Lane | Last row |
|---|---|---|
| `A.md` | Battle screen (the ground and space tactical view) | 2026-10-13 |
| `B.md` | Galaxy view | 2026-10-08 |
| `C.md` | Ground era | 2026-10-09 |
| `D.md` | The space battlefield | 2026-10-19 |
| `E.md` | Settlement and economy | 2026-10-20 |
| `F.md` | Steam phase B and shipping | 2026-10-12 |
| `P.md` | Prototype review queue (mockups, prototype gate) | 2026-10-18 |
| `V.md` | Sim viewer (tooling shots, no story id) | 2026-10-20 |

## Screenshots

Committed copies live under `docs/northstar/story_reviews/shots/<run id>/<story>.png`. The run id is a timestamp plus the commit hash, so a re-run never overwrites an earlier one. The `qa_state` dump sits beside the png, same folder, same stem.

## Verdicts

- Reviewer verdict: `yes`, `no` or `unclear`, followed by the evidence (what was seen, which state field).
- Westley verdict: `pending` on entry, then `approved` or `rejected`.
- The verdict cell holds only the word approved or rejected; Westley's words go in the date cell in parentheses; status_check counts the exact word.

## Seen

- `Seen` is the status for a story that is built, shown to the player and approved by Westley (vocabulary in `docs/northstar/agile.md`).
- Only a clerk edits the Status cell in `docs/bible/stories.md`, and only when the queue row says `approved`. The clerk changes the status cell and commits it with the queue row, in one commit.
- Reviewer agents never edit `stories.md`, and neither does the 30B.
- A `rejected` row sets the story back to Built or Revised.

## Compound status

Many status cells hold compound text such as "Spec'd, blocked on Q-009-02". `Seen` applies only once the flag is closed; a story whose epic has an open flag is not built, so it cannot be seen. A clerk who meets a compound cell leaves it alone and flags it in the queue row.

## Westley's folder

`docs/northstar/story_reviews/westley/` holds a plainly named copy of every shot that waits on Westley, with `README.md` as the reading page: one block per picture (what you see, what to judge, the beta status of each feature shown). The clerk that writes a queue row adds the copy and the block; the clerk that records his verdict deletes both in the same commit. Every prototype and lane shot queued for Westley carries a one-line ground legend in its block (what each colour and mark means), written by the shot's clerk from the mockup's overlay constants; HARNESS-C235's legend check (legend=, unit=, band= in the reviewer cell) stays. Run-id folders under `shots/` are never deleted; the folder is a view, not the record (Westley, 2026-10-13; blocks and beta status, 2026-10-21).
