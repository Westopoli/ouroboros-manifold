# Stage 8.5 Perf Report

Generated from `logs/sim_perf.jsonl` + `logs/client_perf.jsonl`.

- sim_perf rows: 0  (0 snapshot, 0 delta)
- client messages received: 214
- snap events detected: 2564
- achieved tick rate: 0.00 Hz

## Server step time

(no samples)

## Serialization time


## Payload sizes


## Snap events (client-side DR vs authoritative)

- total: 2564
- by cause: {'delta_update': 1492, 'snapshot_stomp': 1072}
- snapshot_stomp magnitude (wu): mean 181.62  p95 405.00  max 405.00
- delta_update magnitude (wu):   mean 66.25  p95 256.03  max 397.52
- delta_update backward fraction: 1336/1492 (89.5%)

### Top snap-event ticks

| tick | msg type | snap events | % of 400 units |
|------|----------|-------------|----------------|
| 56 | snapshot | 392 | 98% |
| 109 | snapshot | 366 | 92% |
| 162 | snapshot | 314 | 78% |
| 148 | delta | 32 | 8% |
| 145 | delta | 30 | 8% |
| 86 | delta | 28 | 7% |
| 142 | delta | 28 | 7% |
| 149 | delta | 28 | 7% |
| 129 | delta | 26 | 6% |
| 147 | delta | 24 | 6% |
| 123 | delta | 22 | 6% |
| 125 | delta | 22 | 6% |

### Snapshot ticks vs stomp-event alignment

- full-snapshot ticks in log: []
- ticks with stomp events:    [56, 109, 162]
- aligned: []  (0/3 stomp ticks match a snapshot tick)

## Hypothesis verdict

- HYPOTHESIS A partial: 0/3 stomp ticks align with snapshot ticks. Investigate outliers.
- HYPOTHESIS B signal: 1336/1492 delta snap events are backward moves — resync threshold may be too loose.

## Hypothesis reminders

- **A (snapshot stomp):** snap-backs cluster on SNAPSHOT_INTERVAL boundaries, magnitude ≈ velocity × elapsed_since_last_resync.
- **B (loose resync threshold):** snap-backs spread across ticks, disproportionately backward, tied to direction changes.
- **C (Godot-side interp mismatch):** this probe uses exact Python dt; few snap-backs here means the protocol is clean and the bug is in Godot's display_positions interpolation, not the protocol.
