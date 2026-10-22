# Contributing

Tests come first. A story exists as failing tests before any code, in paths builders do not edit, and each test names the story (`S-###`) or rule (`R-###-##`) it proves. Every detector ships with a positive control, so a check that cannot fail is a defect. If a test looks wrong, say so with the failing assertion line and the spec line it contradicts; do not edit it to pass.

Every file has one owner at a time, named in `docs/northstar/plans/push/pieces.toml`, and two in-flight pieces never own the same file. New code goes in new files behind a frozen header, and wiring it up is its own small piece. Keep diffs minimal: no unasked-for layers, no cosmetic refactors inside another change, and update every doc a behaviour change makes wrong in the same change.

Work lands through the merge gate (`scripts/specfactory/merge_gate.sh`), never by a direct push of unchecked code to `main`; run `scripts/specfactory/pre_gate.sh` first so noise and lint rejects cost nothing. The ten-minute tour of how all this fits together, with the gate stages and the checks that guard it, is [`docs/METHOD.md`](docs/METHOD.md).
