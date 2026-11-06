# Plan-consistency — layout-kit-assault

Run by the overlord 2026-11-05 against `spec.md` (S-247 cascade), `csrc/layout_kit.h` and `tests/csim/test_layout_kit.py`, all committed on `s/S-247-layout-kit-assault` (0f5f907b).

| # | check | finding | artifact + line | resolution |
|---|-------|---------|-----------------|------------|
| 2 | AC <-> contract | Leaf 1 criterion 2 asked for `memcmp` over the whole `om_lk_layout`; no test can run that (tests are Python over the CLI) and struct padding is indeterminate | spec.md leaf 1 criterion 2 | resolved: clause replaced by byte-identical JSON |
| 2 | AC <-> contract | The `vantage` request carries `side`, `om_lk_vantage` has no such field | spec.md Design step 5; layout_kit.h om_lk_vantage | resolved: spec defines side from straight-line nearness to a base |
| 1 | AC <-> AC | `--break approaches` said "the lane of kind objective_route that is not the spine's (or any one lane...)": two readings | spec.md leaf 2 criterion 6 | resolved: lowest-index lane touching the objective |
| 5 | named-entity | `libm_lint.py` rglob-scans `csrc/tools/` too, so the CLI is under the same ban | spec.md leaf 1 criterion 4 | resolved: sentence added |
| 5 | named-entity | `csrc/terrain_noise.c` is standalone | checked with `nm`: no undefined symbols | none needed |

## Checks with no finding
- AC <-> umbrella: no gap (umbrella asserts the checks object and place counts that criterion 1 lists).
- Observability: no gap beyond the memcmp clause above (every other criterion names a JSON key, exit status, file or pixel).
- Pillow 12.3.0 in the main checkout `.venv` (`import PIL`): verified, not external-unverified.
