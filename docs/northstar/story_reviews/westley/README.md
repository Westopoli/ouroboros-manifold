# Shots waiting on Westley

At most one shot per lane waits here at a time (Westley, 2026-10-13: "avoid multiple photo entries of the same letter"); a lane's next shot stays in its queue file until he has ruled on the one here.

This folder holds exactly the screenshots that wait on Westley's verdict, each under a name that says what it is, so he never has to open a run-id folder. The table is the page table: the name here, the row it stands for, and where the original lives. Rule (Westley, 2026-10-13): a shot enters this folder when its queue row is written, and leaves it (file and table row deleted, in the verdict's commit) when he rules; `git log` keeps the history. The queue rows in `../<lane>.md` stay the record; this folder is only the view.

Name form: `<lane>-<story>-<what it shows>.png`. One row per file.

| File here | Story | Lane | Queue row (run id) | Original | What to judge |
|---|---|---|---|---|---|
| `F-S140-net-first-tick-after-move-order.png` | S-140 | F | `F.md` 20261012-2033-b12b47a | `shots/20261012-2033-b12b47a/S-140_after_move_order.png` | Host frame after a move order over the network: 56 units ordered; does the frame show them moving? |
| `A-S002-layer-transfer-buttons.png` | S-002 | A | `A.md` 20261013-0103-00d5637 | `shots/20261013-0103-00d5637/S-002_hard_transfer.png` | Battle screen with 330 units selected and the five "To layer" buttons at the right edge; the look of the strip |
| `A-S103-start-view-opening-frame.png` | S-103 | A | `A.md` 20261013-1625-c79d141 | `shots/20261013-1625-c79d141/S-103_start_view.png` | The first battle frame after Deploy (space era): is your army framed in the middle with a visible margin, "of your base", nothing under the panels? |
