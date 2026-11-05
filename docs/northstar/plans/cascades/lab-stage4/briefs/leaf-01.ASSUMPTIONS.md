# leaf-01 assumptions

- **first_seen / sights carrier**: `fight()` keeps its 4-tuple return; under `--sight on` it puts `{"first_seen", "sights"}` in the orders block under a private key `stage4`, which `_document` copies away and pops before writing (so `orders` in the file holds only `mode/point/attacker/guard`) — source: contract.py "the end state carries first_seen for _document to write" and "Return shape unchanged"; tests unpack 4 values.
- **sampling point**: `first_seen` is sampled at tick 0 and after each step where `tick % CHECK_EVERY == 0` (before the wipe check), only for sides still `None`, over living enemies only — source: spec line 22.
- **usage error form**: `--control sight` with `--sight off` calls `ap.error` (argparse usage text on stderr, SystemExit 2) — source: spec line 24 "usage error (exit 2)".
- **results.md header choice**: decided by `--sight` (on writes SIGHT_RESULTS_HEAD only when the file is new/empty) — source: contract.py results.md line.
- **control sight with --seeds**: written inside the per-seed loop right after the main fight, before `--control ground` branch is considered (the two are exclusive via `elif`) — source: spec line 24.
- **order of stage 4 engine calls**: era kind and reach set after `walk_on_ground`, guard after the attack-move order of the other side — source: spec line 21 ("after spawning").
- **seen for sight "control"**: no `seen` computed in control frames (only sight == "on" computes it) — source: spec line 24.
