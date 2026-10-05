# tests/net: lockstep proof harness

Spec: `docs/northstar/plans/2026-10-05-lockstep-backend-spec.md`.

`driver.py` runs N `pipe/ouroboros_pipe` processes (the `Pipe` class of
`tests/long/harness.py`) joined by a seeded fake network (delay, loss, reordering, one
peer that stops). Lockstep rule: input delay 3 ticks; a packet for tick t carries the
sender's commands for ticks t-4..t; a tick is stepped only when every live peer's
packet for it is in; stall (20) and drop (1200) are counted in driver rounds. Each peer
submits every peer's commands with `net_submit` and steps with `net_step`; checksums are
compared at every tenth tick.

Pipe verbs needed (pipe lane, not on this branch before integration): `net_reset`,
`net_submit`, `net_step`, `net_checksum`. Every pipe test skips until the pipe answers
`net_reset` with a `net_ack` (probed once per session, `driver.net_available`).
The fake network and driver-logic tests in `test_lockstep_equal.py` need no pipe and run always.

Run: `cd tests/net && python -m pytest -q` (set `OM_NET_TICKS` to cut a mission short).
Multi-process runs: `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 -- ...`.
