# Long-mission suite

Plays missions through the real pipe (`pipe/ouroboros_pipe`) to their own end:
new campaign, mission_start, mission_begin, attack-move orders for the player
force, `tactical_step` in batches until `mission_over` or 110% of the mission's
`deadline_ticks`. It sends `mission_end` only after a frame reports `mission_over` (as the client does), then the jump. Not collected by the merge gate
(it lives outside `tests/csim`, `tests/transport`, `tests/qa`); run it nightly
or per plan, not per merge.

    make libouroboros.so pipe/ouroboros_pipe
    cd tests/long
    ~/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider .

- `OM_LONG_SEEDS=3,5,6` overrides the seed list (default covers six archetypes plus reconquest seed 264).
- `OM_LONG_RESULTS=path.jsonl` sets where one JSON row per run is appended (default `/tmp/om_long_results.jsonl`): archetype, ticks, game seconds (ticks / 20), how it ended, alive per side, tactical-frame band, objective progress, wall time, ticks per second.
- A run can take several minutes (mission length 18 to 60 game minutes).
- The debrief (band, retention, commander fate) is read from the `mission_end` reply.
