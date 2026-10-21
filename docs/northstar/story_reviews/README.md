# Story review queue

Every story play that reaches the player's eyes gets a queue row. Westley approves or rejects it. Only then does a story become `Seen`.

## Files

`docs/northstar/story_reviews/<lane>.md`, one markdown table per lane, columns in this order:

| story | lane | run id | screenshot path | qa_state file | reviewer | reviewer verdict (yes/no/unclear + evidence) | Westley verdict (pending/approved/rejected) | date |
|---|---|---|---|---|---|---|---|---|

## Screenshots

Committed copies live under `docs/northstar/story_reviews/shots/<run id>/<story>.png`. The run id is a timestamp plus the commit hash, so a re-run never overwrites an earlier one. The `qa_state` dump sits beside the png, same folder, same stem.

## Verdicts

- Reviewer verdict: `yes`, `no` or `unclear`, followed by the evidence (what was seen, which state field).
- Westley verdict: `pending` on entry, then `approved` or `rejected`.

## Seen

- `Seen` is the status for a story that is built, shown to the player and approved by Westley (vocabulary in `docs/northstar/agile.md`).
- Only a clerk edits the Status cell in `docs/bible/stories.md`, and only when the queue row says `approved`. The clerk changes the status cell and commits it with the queue row, in one commit.
- Reviewer agents never edit `stories.md`, and neither does the 30B.
- A `rejected` row sets the story back to Built or Revised.

## Compound status

Many status cells hold compound text such as "Spec'd, blocked on Q-009-02". `Seen` applies only once the flag is closed; a story whose epic has an open flag is not built, so it cannot be seen. A clerk who meets a compound cell leaves it alone and flags it in the queue row.

## Westley's folder

`docs/northstar/story_reviews/westley/` holds a plainly named copy of every shot that waits on Westley, with `README.md` as the reading page: one block per picture (what you see, what to judge, the beta status of each feature shown). The clerk that writes a queue row adds the copy and the block; the clerk that records his verdict deletes both in the same commit. Run-id folders under `shots/` are never deleted; the folder is a view, not the record (Westley, 2026-10-13; blocks and beta status, 2026-10-21).
