# Layers mockup QA checklist

Placeholder. Filled with real measured numbers from `scripts/mockup_qa.sh` and
`scripts/mockup_verify.sh` runs once the feature build steps land.

| id | oracle | threshold (candidate; Westley owns) | measured clean | measured planted | plant |
|---|---|---|---|---|---|
| DET-1 | headless hash/tick equality across two runs | equal | TBD | TBD | none |
| DUR-2 | fast/slow completion tick | 20 / 100 | TBD | TBD | instant-transfer |
| BLOCK-3 | pending transfer resolves on reaching an open cell | pending until open | TBD | TBD | blocked-ignored |
| SAME-4 | same-layer transfer is instant | no transition | TBD | TBD | none |
| VIS-5 | cross-layer sensor radius | half of same-layer | TBD | TBD | cross-layer-full-range |
| HEIGHT-6 | unit y vs layer_height_wu | equal on completion | TBD | TBD | wrong-height |
| RING-7 | ring colour flips on completion tick | flips at tick, not before | TBD | TBD | ring-colour-same |
| DIM-8 | non-focused layer alpha | 0.4 | TBD | TBD | no-dimming |
| FOCUS-9 | Tab cycles focus | 1 to 2 to 1 | TBD | TBD | none |
| JSON-10 | qa_state() contract shape | all keys present | TBD | TBD | none |

## Visual questions

TBD once pass-1 screenshots exist.

## Timings

TBD.

**HELD:** TBD.
