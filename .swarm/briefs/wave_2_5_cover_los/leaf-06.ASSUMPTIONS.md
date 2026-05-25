## Assumptions made during leaf-06

- **Defender unit type = Warden**: needed attack_range >= 300 (defender at (500,500), attacker at (200,500)). Raider (range 200) too short. Vanguard exactly 300 = edge case. Warden (range 350) safest fit. — source: `simulation/config.py:512-531 UNIT_STATS`, brief lines 153-157 of spec specify the 1v1 cover-peek geometry but not unit type.
- **Attacker unit type = Raider**: any unit that can't see the defender works. Raider is the lightest. — source: same as above.
- **Polygon shape = 12-vertex circle centered (500,500) radius 80**: matches brief Phase A directive in the leaf-06 brief (lines 4-5 of orchestrator phase-A spec). — source: orchestrator prompt + spec line 153 ("each source produces 1 polygon (8-12 vertex circle approximation)").
- **`behavior_runners` left empty**: spec line 39 says audit targets `simulation/tactical_engine.py`. Stage 7.5 behavior scripts (`ENABLE_BEHAVIOR_SCRIPTS=True`) are out of scope per brief line 61 ("Do not modify behavior scripts in other files"). Base AI targeting loop is the system under test. — source: brief lines 39-41, 61.
- **Defender fires detection = attacker HP drop**: cleanest observable. attack_timer reset would also work but HP delta is the integration-level signal that the L5 visibility gate also passed. — source: `simulation/damage.py:57-72` shows pending damage commits to HP.
- **L7 fixture (`simulation/cover_integration_fixture.py`) absent**: file does not exist at run time. Built equivalent in-test fixture per orchestrator phase-A step 4. — source: `ls` check.
- **Seed = 42**: deterministic run, arbitrary stable choice. — no source — pure guess.
