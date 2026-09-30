# Spec 04: the mission clock table in C moves to 30 to 60 minutes (code only)

You are a Claude Sonnet 4.6 worker chat acting as the **builder**. You execute this spec directly. You do not spawn agents, redesign, or widen scope. You never edit anything under `tests/`. If a test looks wrong to you, say so in the report; do not touch it.

## Why

E-10 R-076-02 (closed by Q-076-01 and Q-076-02, Westley 2026-09-29) sets each mission archetype's base clock between 30 and 60 minutes of battle time. `csrc/mission.c` still holds the retired 3 to 4.5 minute table. Spec 03 has already landed tests that fail against it; your job is to make them pass with the smallest change.

## Where

Your own clone, never `~/Projects/ouroboros-manifold`:
```
git clone --branch main "$(git -C ~/Projects/ouroboros-manifold remote get-url origin)" ~/Projects/relay-04
cd ~/Projects/relay-04 && git checkout -b relay/04-clock-code
```
Confirm spec 03 is on main first: `grep -n "72000\|60,  *# SIEGE\|SIEGE_BREAKING" tests/csim/test_E10_S076_the_clock.py` must show the new values. If it does not, stop and report "spec 03 not landed".

## Files you may edit

- `csrc/mission.c`, and only the function `om_archetype_base_time_ticks` (around lines 601 to 610) and its comments.

Nothing else. No header change, no constants file change, no other function.

## The change

Replace the `minutes[OM_MISSION_N_ARCHETYPES]` table, indexed by archetype id 0 to 9:

```
37.5, 60.0, 45.0, 52.5, 30.0, 60.0, 37.5, 30.0, 52.5, 37.5,
```
(defensive stand, siege breaking, reconquest, assault, suppression, multi-front defense, interception, evacuation, containment, counterinsurgency.)

Rewrite the `/* constants-table: ... */` comment above it to cite `docs/bible/algorithms.md ALG-56 (Q-076-01 and Q-076-02: 30 to 60 minutes of battle time by archetype, times 60 seconds/minute)`. Keep the `/* end constants-table */` marker: a lint reads those markers. Keep the `minutes × 60 × OM_TACTICAL_TICK_RATE` computation exactly as it is; the values are exact in binary (multiples of 0.5), so the cast to `uint64_t` yields 45000, 72000, 54000, 63000, 36000, 72000, 45000, 36000, 63000, 45000.

Leave `OM_MISSION_DEFAULT_TIME_LIMIT_TICKS` (300) alone: it is only the fallback before a mission is set up, and it is not this spec's question. Mention it under Open if you think it should change.

## Steps

1. Make the change above.
2. `make -j8` (no warnings expected from your change).
3. `~/Projects/ouroboros-manifold/.venv/bin/pytest tests/csim/test_E10_S076_the_clock.py -q` → all pass.
4. `~/Projects/ouroboros-manifold/.venv/bin/pytest tests/csim -q` → record pass/fail counts. Every failure that was not failing on main before your change is yours to explain; do not fix tests.
5. Run the merge gate from the live checkout's scripts, against your clone as the candidate: `cd ~/Projects/ouroboros-manifold && scripts/specfactory/merge_gate.sh ~/Projects/relay-04 origin/main B9`. It prints one `GATE <step> ...` line per step. Paste every line into the report. If the `checksum` step reports a changed determinism trace, that is expected only if the trace exercises a mission clock; report it as-is, do not touch anything.
6. `git add csrc/mission.c`, commit in plain prose ending `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`, `git push origin relay/04-clock-code`. Stop.

## Report (your last message, nothing after it)

```
Branch: relay/04-clock-code (commit <hash>)
Files: csrc/mission.c (+N/-M lines)
S076: <pytest summary line>
tests/csim: <summary line>
Gate: <every GATE line>
Open: <anything, or "none">
```
