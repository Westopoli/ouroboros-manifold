# HUD mockup QA checklist

Real measured numbers from `scripts/mockup_qa.sh` and `scripts/mockup_verify.sh` runs, Godot 4.6.3, llvmpipe, 1280x720 unless noted. TBD until the clean and planted runs land.

## Verify checks (`verify.gd`)

| id | check | clean result | plant | planted result |
|---|---|---|---|---|
| DET-1 | 300 ticks twice give equal hashes; seed 12 differs | TBD | none | n/a |
| BOX-2 | box over both layers selects all friendlies | TBD | `box-one-layer` | TBD |
| NARROW-3 | narrow(2) keeps layer-2 only, `focus_layer` unchanged | TBD | `narrow-moves-focus` | TBD |
| GROUP-4 | bind exclusivity; recall(2) selects exactly group 2 | TBD | `group-shared` | TBD |
| CENTRE-5 | recall twice within 0.4s reports centre_requested | TBD | none | n/a |
| NOALL-6 | no select-all-like command anywhere | TBD | `select-all-exists` | TBD |
| SHIFT-7 | shift-click adds/removes | TBD | none | n/a |
| BOUND-8 | camera clamp, pitch 90, focus_layer doesn't move camera | TBD | `camera-unbounded` | TBD |
| CLOCK-9 | clock_s from tick, not wall time | TBD | `clock-wallclock` | TBD |
| PANEL-10 | panel rows, focus_mode, overlay mouse_filter | TBD | none | n/a |
| JSON-11 | qa_state round-trips; qa_plant contract | TBD | none | n/a |

## Xvfb oracles

| id | oracle | threshold (candidate; Westley owns) | measured clean | measured planted | plant |
|---|---|---|---|---|---|
| ERR-0 | `errors.txt` count, `exit.txt`, no `UNIFORM` | TBD | TBD | — | none |
| GPU-0 | `_qa.adapter` contains llvmpipe | exact | TBD | — | none |
| BOX-X | `qa/box.json` drag selects expected uids | exact match | TBD | TBD | `box-one-layer` |
| TAB-X | `diff recall_none.png recall_2.png` over tabs crop | TBD | TBD | TBD | `group-shared` |
| EDGE-X | two shots at east bound identical | < 0.001 | TBD | TBD | `camera-unbounded` |
| DRAG-X | box overlay differs from boot.png | TBD | TBD | n/a | none |

## Visual questions

| q | question | proves | answer | proving screenshot |
|---|---|---|---|---|
| Q1 | Is the HUD lean: only objective line, clock, selection panel, group tabs, layer strip? | S-P12, R-104-09 | TBD | TBD |
| Q2 | Is selection state obvious at a glance? | S-105 | TBD | TBD |
| Q3 | Does the layer strip read as focus; does narrowing read as selection change not focus change? | R-105-06, R-009-03 | TBD | TBD |
| Q4 | Is the box overlay visible while dragging and gone after? | R-105-01 | TBD | TBD |
| Q5 | Does the camera stop cleanly at the bound? | R-103-02 | TBD | TBD |
| Q6 | Is all text legible at 720p; anything clipped? | hygiene | TBD | TBD |

**HELD:** TBD

## Timings

TBD (`timing_ms.tick_avg`, `_qa.fps_ms` under llvmpipe at 720p with 24 units).
