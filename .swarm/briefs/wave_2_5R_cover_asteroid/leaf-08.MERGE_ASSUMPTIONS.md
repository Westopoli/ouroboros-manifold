# leaf-08 merge assumptions

## Two-file rule override (path a)

Brief declared 3 staged files (1 test + 2 impl via plural `impl_files`: snapshot_serializer.py + docs/architecture.md). Skill text says "exactly 2 files." Westley confirmed path (a): override + log. G1 parent-owned check passed (none of the 3 staged paths match parent_owned globs).

## Pre/post delta = 0 (workflow caveat)

Edit-in-place workflow: real == staging at merge time. Umbrella 10 pass / 4 fail unchanged across copy. Brief acceptance: 5/5 GREEN.

## Umbrella G still RED — fixture bug, not L8 regression

`test_umbrella_g_manifest_shape` uses dict-shape `spine_nodes` ({"type": "chokepoint", ...}); L3's `place_asteroid_fields` accesses `node.node_type` (object attribute). Failure is in the umbrella fixture (parent-owned file `test_asteroid_umbrella.py`), not in L8's serializer or L3's placer. L8 serializer logic itself is verified GREEN via test_asteroid_manifest.py 5/5. Parent will patch umbrella fixture before apex E2E run.

Git is real revert mechanism per CLAUDE.md.
