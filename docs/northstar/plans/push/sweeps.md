# Sweeps

One row per slow-tier run on main, newest last. `status_check.py` reads the last PASS or BASE row as the anchor of its `sweep` check; a REJECT row is a FINDING, never an anchor. The BASE row (the landing sha of HARNESS-gate-tiers) is written by a records push right after that landing.

Row format (spec `docs/northstar/plans/2026-10-29-layered-gate-spec.md` section 8 B2): `| <UTC %Y-%m-%d %H:%M> | <main sha> | PASS|REJECT|BASE | new: <ids|none> | red: <n> | <ids, or a list-file path under docs/northstar/plans/push/sweeps/ above 20> |`. "Main is green" means PASS and `red: 0`.

| Date-time UTC | Main sha | Verdict | New | Red | Red ids |
|---|---|---|---|---|---|
