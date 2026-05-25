# leaf-01 merge assumptions

## Two-file rule override

Brief declared 3 staged files (1 test + 2 impl via plural `impl_files`). Skill text says "exactly 2 files." Westley confirmed path (a): override + log. G1 parent-owned check passed (bible_world.md + bible_combat.md not in parent_owned per .claude-swarm.toml narrowing). Brief-path match confirmed.

## Pre/post delta = 0 (workflow caveat)

Leaf agents edit real files in-place during RED→GREEN cycle, then stage final copies. By the time /swarm-merge runs, real == staging. Copy is no-op. Pre/post umbrella delta always 0. Real attribution: L1 added 4 passes vs pre-wave baseline (e_world, e_combat already passing pre-wave incidentally — net contribution is the bible rewrite content, not new test slots).

Git is the actual revert mechanism per CLAUDE.md.
