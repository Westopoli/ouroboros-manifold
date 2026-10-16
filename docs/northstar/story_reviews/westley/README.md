# Shots waiting on Westley

At most one shot per lane waits here at a time (Westley, 2026-10-13: "avoid multiple photo entries of the same letter"); a lane's next shot stays in its queue file until he has ruled on the one here.

This folder holds exactly the screenshots that wait on Westley's verdict, each under a name that says what it is, so he never has to open a run-id folder. The table is the page table: the name here, the row it stands for, and where the original lives. Rule (Westley, 2026-10-13): a shot enters this folder when its queue row is written, and leaves it (file and table row deleted, in the verdict's commit) when he rules; `git log` keeps the history. The queue rows in `../<lane>.md` stay the record; this folder is only the view.

Name form: `<lane>-<story>-<what it shows>.png`. One row per file.

| File here | Story | Lane | Queue row (run id) | Original | What to judge |
|---|---|---|---|---|---|
| `P-S108-galaxy-moment-after-pullback.png` | S-108 | prototype (transition mockup, pass 1b) | `../P.md` row 1 (branch `push/proto-transition` at 5537d3cb) | `../shots/proto-transition-1b/03_galaxy.png` | Scale: the battlefield's point of light is now about 13x smaller than pass 1 (below one system dot) at the galaxy moment; the panel at 38 percent; your 2026-10-15 note "10-20x smaller" |
| `P-S108-mid-pullback-star-blobs.png` | S-108 | prototype (transition mockup, pass 1b) | `../P.md` row 1 | `../shots/proto-transition-1b/02_pullback_mid.png` | The mid pull-back: the inner-halo stars read as large hexagonal blobs, not a fine star field (the Doer flagged it); approve the path, reject the blobs, or both |
