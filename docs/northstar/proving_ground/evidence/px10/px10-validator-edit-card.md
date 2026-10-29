---
project: /home/westopoli/Projects/ouroboros-manifold
kind: content
acceptance:
  - "python3 scripts/specfactory/pack_validate.py docs/northstar/proving_ground/evidence/px10/pack_clean"
allowed_files: "docs/northstar/proving_ground/evidence/px10/pack_clean/**, scripts/specfactory/pack_validate.py"
expected_lines: 0
---

## Brief

Data card, PX-10, never queued. Deliberately broken: `allowed_files` includes `scripts/specfactory/pack_validate.py`, the validator this card is graded against. Exists only so `card_lint.py` can be run on it to prove `FORBIDDEN_ALLOWED_PATH` fires -- see docs/legacy/proving_ground/PX-10-content-card.md.
