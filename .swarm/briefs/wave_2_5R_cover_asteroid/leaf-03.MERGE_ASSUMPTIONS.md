# leaf-03 merge assumptions

## Two-file rule override (path a)

Brief declared 3 staged files (1 test + 2 impl via plural `impl_files`: gradient_placer.py + config.py). Skill text says "exactly 2 files." Westley confirmed path (a): override + log. G1 parent-owned check passed (none of the 3 staged paths match parent_owned globs). Brief-path match confirmed.

## Pre/post delta = 0 (workflow caveat)

Leaf agents edit real files in-place during RED→GREEN cycle, then stage final copies. By the time /swarm-merge runs, real == staging (diff silent). Copy is no-op. Pre/post umbrella delta always 0. Real attribution: L3 brief acceptance 6/6 GREEN; umbrella still at 10 pass / 4 fail (B chokepoint cluster + F apex + F integration + G manifest pending later leaves).

Git is the actual revert mechanism per CLAUDE.md.

## Assumption sweep result

Clean vs L1 (docs only, no overlap) and L2 (L3's cover_polygons-as-silent-kwarg on TacticalMap matches L2's same convention). L3's sqrt-uniform disk sample differs from spec's "rejection sample" but produces equivalent uniform distribution; documented in L3.ASSUMPTIONS.md.
