# Roster mix analyses A and B (2026-10-19)

## Purpose

Westley asked on 2026-10-19 whether the skill lab's roster mixes cover the unit roster well enough. Two Opus analysts were given the same question independently. `analysis_A.md` and `analysis_B.md` are their reports, byte for byte; `A_evidence/` and `B_evidence/` hold the scripts, run output and logs each used. Files over 2 MB were skipped (none were over).

## The Architect's arbitration

- Keep M0 to M4 and M3b.
- Add M5 8 Raider + 8 Bombard, M6 8 Interceptor + 8 Bombard, M7 8 Raider + 8 Interceptor, M8 8 Bombard + 8 Bastion, M9 12 Vanguard + 4 Warden.
- All six types in one roster become a batch-two robustness mix.
- Fixes come first: copied types lose the Warden aura and the Bastion cap, and the naive attacker always fields 16 Vanguards.
- Each new mix gets a 30-fight mirror.

## Westley's acceptance

"I agree with all of your arbitration logic" (Westley, 2026-10-19).

## Files

- `analysis_A.md`, `analysis_B.md`
- `A_evidence/`: exp.py, exp2.py, exp3.py, t1.py, mixlab.py, exp_catmult.json, exp_engine.json, exp_mirror.json, exp_mirror_nopoint.json, exp_plays.json, exp_reach.json
- `B_evidence/`: mixlib.py, exp1_mirrors.py, exp2_skill.py, exp3_deadknob.py, exp3b_rosters.py, exp3c_knob_warden.py, exp4_more.py, exp1.json, exp2.json, exp3c.json, exp4.json, exp3c.log, exp4.log
