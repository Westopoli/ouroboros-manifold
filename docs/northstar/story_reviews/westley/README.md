# Shots waiting on Westley

This folder holds exactly the screenshots that wait on Westley's verdict, each under a name that says what it is, so he never has to open a run-id folder. The table is the page table: the name here, the row it stands for, and where the original lives. Rule (Westley, 2026-10-13): a shot enters this folder when its queue row is written, and leaves it (file and table row deleted, in the verdict's commit) when he rules; `git log` keeps the history. The queue rows in `../<lane>.md` stay the record; this folder is only the view.

Name form: `<lane>-<story>-<what it shows>.png`. One row per file.

| File here | Story | Lane | Queue row (run id) | Original | What to judge |
|---|---|---|---|---|---|
| `B-S106-galaxy-dot-colour-refix.png` | S-106 | B | `B.md` 20261013-0216-5f3ee95 | `shots/20261013-0216-5f3ee95/S-106.png` | Galaxy overview after the dot-colour fix: do the system dots show their owner colours as before the rebuild? |
| `E-S237-settlement-look-after-E1k.png` | S-237 | E | `E.md` 20261013-0350-20dfb2f | `shots/20261013-0350-20dfb2f/S-237.png` | Settlement after the look piece: building levels differ, footprints vary, yaw follows the slope, units no longer stacked? |
| `F-S141-lobby-two-members.png` | S-141 | F | `F.md` 20261012-1630-dbe480a | `shots/20261012-1630-dbe480a/S-141.png` | Multiplayer lobby with two members, placeholder layout; is a plain list acceptable for the beta? |
| `F-S140-net-first-tick-after-move-order.png` | S-140 | F | `F.md` 20261012-2033-b12b47a | `shots/20261012-2033-b12b47a/S-140_after_move_order.png` | Host frame after a move order over the network: 56 units ordered; does the frame show them moving? |
| `A-S002-layer-transfer-buttons.png` | S-002 | A | `A.md` 20261013-0103-00d5637 | `shots/20261013-0103-00d5637/S-002_hard_transfer.png` | Battle screen with 330 units selected and the five "To layer" buttons at the right edge; the look of the strip |
