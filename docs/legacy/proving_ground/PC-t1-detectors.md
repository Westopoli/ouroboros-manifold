# Probe C — T1 detectors, positive and negative controls

**Proves.** The state-trace detectors from R4 fire on exactly their planted bug and stay silent on a clean build; fingerprints are stable across seeds.

**Fixture.** `~/Projects/agora-proving-ground`/probe_c: `mover.c` built five ways by `make c` (`MOVER_BUG` 0–4: clean, rubberband, stuck, backwards, dropped), `detectors/rts.py` (four detectors + fingerprint), `scenario.py` (10 units, 400 ticks, dt 0.05, commands at ticks 0/100/200/300), `tests/test_detectors.py` (20 tests).

**Run by.** pytest directly, not Agora. This is a harness probe.

**Pass criterion.** 20 passed. Per variant the fired set equals exactly its bug. Clean silent on seeds 1–5. Fingerprints equal across seeds 1 and 2.

**Result 2026-09-10.** 20 passed. Counts per seed: rubberband 200, stuck 5, backwards 12–15, dropped 13, clean 0. Thresholds kept at spec defaults.

**Carry-forward.** Recommended: lift `detectors/rts.py` and the trace shape into Ouroboros `tests/qa/t1/` for Stage 5.
