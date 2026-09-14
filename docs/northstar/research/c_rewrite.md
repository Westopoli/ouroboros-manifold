# R2 — C Rewrite Plan

How the Python sim becomes a C library without losing the equations or the determinism. Feeds Stage 1 algorithm pass, Stage 0 probes A through C, Stage 3 scale gates, and Sprint 0.

## Decided

- Core sim is a plain C library with a C ABI and no Godot dependency.
- Phase 1 reproduces today's snapshot, delta, and command JSON over the length-prefixed pipe so Godot is untouched.
- Phase 2 adds a thin GDExtension binding and deletes the pipe.
- Tests always hit the C library directly.
- **The C sim is bit-deterministic across Windows, macOS, and Linux** (decided 2026-09-10). Same seed and same command stream produce byte-identical traces on every platform. Required from the first sprint: identical compiler flags per platform, no `-ffast-math`, integer or fixed-point math where feasible, a state checksum hook every N ticks, and a cross-platform trace-diff test. This keeps lockstep co-op over Steam Datagram Relay possible at near-zero transport cost (see `multiplayer_sdr.md`) and cannot be bolted on later.

## Questions to answer

1. **Toolchain.** gcc and make are present; cmake, clang, ninja are not. Plain make or cmake? What must be installed on forge for Phase 2 (scons, godot-cpp, Godot 4.6 headers)?
2. **Test harness.** pytest plus ctypes against `libouroboros.so` (keeps Agora's existing pytest acceptance path and its `max_impl_lines` sizing) versus a C test runner. Recommendation and the reasons.
3. **Architecture.** SoA data layout for units. Seeded RNG contract (PCG32 or xoshiro; document the stream discipline so the same seed yields the same trace). Tick loop mirroring the current 7-step sequence in `simulation/tick.py`. Memory ownership and arena strategy. Trace writer for T1 QA.
4. **Serialization.** Phase 1 JSON shapes identical to `simulation/snapshot_serializer.py` (`full_snapshot`, `delta`, `apply_delta`) and the command file format `simulation/pipe_transport.py` polls. Contract tests for both.
5. **Algorithm inventory.** Every equation quoted with constants and file:line from `drift.py`, `region.py`, `world.py`, `faction.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `admin_revolt.py`. Proposed keep, retune, or drop for Stage 1's algorithm pass.
6. **Perf targets.** Proposed numbers for Stage 3 scale gates: tactical tick time at 1,000 and 10,000 units; strategic tick at 60 regions and 15 factions over 5,000 ticks; path queries per second; memory ceiling.
7. **Determinism proof.** A test that runs the same seed twice and diffs the traces byte for byte, on one machine and across platforms. Define the checksum hook (which fields, which cadence, how a desync is reported).

## Spike proof (gates Stage 0 probes A through C)

A toy `libtoy.so` with a seeded PRNG and one drift equation builds with the chosen toolchain and passes a pytest via ctypes. Record the command here.

## Findings

Sprint 0 decisions (2026-09-14). These resolve the open "Questions to answer" above for the sim core; recorded in `README.md`'s decisions table.

- **Build: plain `make`.** Forge has gcc + make, not cmake. A hand-written Makefile gives the exact per-platform flag control determinism needs. Phase 2 will use SCons for godot-cpp; cmake buys nothing now. See `Makefile` (parent-owned).
- **Determinism flags:** `-O2 -fno-fast-math -ffp-contract=off -fexcess-precision=standard -msse2 -mfpmath=sse -fno-math-errno`. Two targets: `libouroboros.so` and `libouroboros_dbg.so` (`-DOM_DEBUG_INJECT`).
- **RNG: PCG32** (pure integer ops, bit-identical cross-platform; state `{uint64 state, uint64 inc}`). The C trace is its own truth — it does not match Python's Mersenne Twister. Phase 1 mirrors JSON shapes, not draw values.
- **Transcendental: `om_sin`.** ALG-01's oscillator uses `sin` with an irrational (RNG-drawn) phase, so it cannot be tabulated, and CLAUDE.md forbids platform transcendentals. Ship a portable minimax-polynomial `om_sin` compiled identically everywhere; gate it with a cross-platform value test. The sim never calls libm `sin`.
- **Checksum: FNV-1a 64-bit**, over the little-endian IEEE-754 bits of every inhabited region's six numbers (military, economy, tension, population, plus 2-dp stability, capacity) in region-index order, folded with the tick. **Cadence N = 10 ticks.** Empty regions excluded. Exposed as `om_world_checksum` / `om_checksum_cadence`.
- **Test harness: pytest via ctypes** against `libouroboros.so`, keeping Agora's existing pytest acceptance path and `max_impl_lines` sizing. No separate C runner. Tests live fenced in `tests/csim/`.
- **T1 debug port: none needed.** The in-process ctypes ABI is the debug port for T1 (deterministic, fast) — commands are ABI calls, observations are `om_region_field` / `om_region_drift` / `om_trace_read`. Only T2 (Godot) uses the existing length-prefixed pipe, unchanged. No new socket protocol for the sim core.
- **The ABI contract** is `csrc/ouroboros_sim.h` (parent-owned): opaque `om_world`, a hard-fixture path (`om_region_set*`) so E-02 tests in isolation, `om_world_step` / `om_world_run`, per-term `om_drift_row`, and a fixed-width `om_trace_row` that diffs by `memcmp` for the cross-platform determinism test (R-020-01).

### Spike proof (to record on execution)

Build a toy `.so` = PCG32 + one drift equation + `om_sin`, pass one pytest-via-ctypes, and paste the exact build + test command here once run.
