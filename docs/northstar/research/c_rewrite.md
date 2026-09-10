# R2 — C Rewrite Plan

How the Python sim becomes a C library without losing the equations or the determinism. Feeds Stage 1 algorithm pass, Stage 0 probes A through C, Stage 3 scale gates, and Sprint 0.

## Decided

- Core sim is a plain C library with a C ABI and no Godot dependency.
- Phase 1 reproduces today's snapshot, delta, and command JSON over the length-prefixed pipe so Godot is untouched.
- Phase 2 adds a thin GDExtension binding and deletes the pipe.
- Tests always hit the C library directly.

## Questions to answer

1. **Toolchain.** gcc and make are present; cmake, clang, ninja are not. Plain make or cmake? What must be installed on forge for Phase 2 (scons, godot-cpp, Godot 4.6 headers)?
2. **Test harness.** pytest plus ctypes against `libouroboros.so` (keeps Agora's existing pytest acceptance path and its `max_impl_lines` sizing) versus a C test runner. Recommendation and the reasons.
3. **Architecture.** SoA data layout for units. Seeded RNG contract (PCG32 or xoshiro; document the stream discipline so the same seed yields the same trace). Tick loop mirroring the current 7-step sequence in `simulation/tick.py`. Memory ownership and arena strategy. Trace writer for T1 QA.
4. **Serialization.** Phase 1 JSON shapes identical to `simulation/snapshot_serializer.py` (`full_snapshot`, `delta`, `apply_delta`) and the command file format `simulation/pipe_transport.py` polls. Contract tests for both.
5. **Algorithm inventory.** Every equation quoted with constants and file:line from `drift.py`, `region.py`, `world.py`, `faction.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `admin_revolt.py`. Proposed keep, retune, or drop for Stage 1's algorithm pass.
6. **Perf targets.** Proposed numbers for Stage 3 scale gates: tactical tick time at 1,000 and 10,000 units; strategic tick at 60 regions and 15 factions over 5,000 ticks; path queries per second; memory ceiling.
7. **Determinism proof.** A test that runs the same seed twice and diffs the traces byte for byte.

## Spike proof (gates Stage 0 probes A through C)

A toy `libtoy.so` with a seeded PRNG and one drift equation builds with the chosen toolchain and passes a pytest via ctypes. Record the command here.

## Findings

(empty until the Research Lane fills it)
