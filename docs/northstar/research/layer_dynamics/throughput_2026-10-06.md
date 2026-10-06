# Skill lab throughput, measured 2026-10-06

Why: the layout-search spec estimated 17 worker-hours per 200-layout run; Westley wants wall time cut as far as the machine allows (two-week beta target). An engineer measured on a detached worktree of main, `-O2` library, with another workflow running on the box.

## Machine

Ryzen 7 3700X: 8 physical cores, 16 threads (SMT), 30 GB RAM, RTX 3060. The lab is scalar deterministic C driven from Python through ctypes; the GPU is not a lever (a GPU port would break the determinism contract).

## Measured

| Lever | Result |
|---|---|
| Build flags | The lab already compiles `-O2` in `scripts/skilllab/engine.py` (`_FLAGS`); `-O2` is 1.7x over `-O0`. No gain left |
| Workers | Fights/s: 1 worker 8.4; 4 workers 33.2 (3.9x); 8 workers 50.4 (6.0x); 12 workers 55.3 (6.6x). Linear to the 8 physical cores; SMT siblings add little |
| Memory | 32 MB per worker, 22 MB parent; 14 workers fit in 0.5 GB. The `MemoryMax=6G` scope is not a constraint |
| Per-fight profile (32v32, 7,500 ticks, 0.37 s) | about 40% in `om_tactical_step`, about 60% in Python: per-tick `unit_hp` polling (about 181k ctypes calls per fight), `unit_pos`, firing-count sampling. No lockstep hash runs per tick |
| Compile | Every worker process recompiles the library: 11 s each; `FightPool(workers=1)` ignores `library_path` |
| Scan shape | `scan.scan` sweeps every headcount 8..24 (17 cells x 2 x replicates = 340 fights at the default 10 replicates). A bracketed bisection needs about 5 cells: 3.4x fewer fights. The linear sweep is what detects multiple flips (`multi_flip`) |
| Early exit | A fight ends on a wipe, draw, stalemate (400 quiet ticks) or the cap; not on a fixed margin |

## Estimate for the 200-layout search

| Shape | Wall time at 12 workers |
|---|---|
| Today | about 2.6 h |
| With bisection (B10) | about 45 min |
| With bisection and batched hp reads (B11) | about 30 min |

## Changes (briefs B9 to B11 in `docs/northstar/plans/briefs/2026-10-06-sonnet-parallel-briefs.md`)

1. Compile the library once per run to a fixed, source-hashed path (B9).
2. Bracketed bisection as the default scan, the linear sweep behind `--full-scan` (B10, Architect ruling).
3. One batched hp read per tick in `fight.py` `_run`, rows byte-identical (B11; a new public symbol would be a contract piece).

Default worker count for lab batches: 12 (8 physical cores plus some SMT), `MemoryMax=6G`, `nice 10` when anything else runs.
