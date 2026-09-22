---
project: /home/westopoli/Projects/ouroboros-manifold
kind: content
acceptance:
  - "python3 scripts/specfactory/pack_validate.py docs/northstar/proving_ground/evidence/px10/pack_clean"
  - "python3 scripts/specfactory/pack_validate.py --diff-mechanical docs/northstar/proving_ground/evidence/px10/pack_clean docs/northstar/proving_ground/evidence/px10/pack_clean"
allowed_files: "docs/northstar/proving_ground/evidence/px10/pack_clean/**"
expected_lines: 0
---

## Brief

Data card, PX-10 (docs/northstar/plans/briefs/2026-09-21-px-batch-b-spec-content-boundary.md). Not queued -- proves the shape of a `kind: content` card: no model call, no `csrc/` symbol, acceptance is `pack_validate.py` over the pack plus a fenced content diff of the pack's mechanical keys (R-146-02) against the reference pack. This card's own pack IS the reference (`pack_clean`), so the diff is a self-check proving the mechanism runs and is byte-identical to itself; a real content card would point `--diff-mechanical` at a sibling era pack instead of at itself (see the write-up's limits section).
