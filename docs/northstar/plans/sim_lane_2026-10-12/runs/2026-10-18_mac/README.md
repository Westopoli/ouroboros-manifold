# Offline run on the Mac, 2026-10-18 20:47 to 21:58 (`scripts/simviewer/probes/offline_run.sh`)

Full outputs stay on the Mac at `~/offline_2026-10-18/` (300 MB, mostly `chronicle_twin/camp_*.json`); this folder holds the summaries.

| Step | Wall | Exit | Headline |
|---|---|---|---|
| mission_choice, 50 seeds x 10 | 53 s | 0 | 500 missions, 5,655 candidate rows, every draw in the top 5, argmax rate 0.258 (a weighted draw as the rule says); **70 of 500 swapped (14 percent, the same rate as the 100-mission pass)**: the Defensive Stand composes nothing without an attack and is silently replaced |
| chronicle_twin, 20 seeds x 5 | 28 s | 0 | 100 chapters, 969 entries; **204 blank shells (21 percent)**, 218 ripple entries, 302 consequence, **5 lineage entries in 100 jumps**, 0 chain entries; 6,764 ownership changes with no entry |
| csim controls | 36 s | 1 | 92 failed (the generated stubs, `controls_triage.md`), 38 passed |
| csim parity | 46 s | 0 | 56 passed |
| csim scale | 0 s | 0 | marker-gated, 0 run |
| csim top level | 8 min | 1 | 2,838 passed, 31 failed, 8 errors (the Mac `-msse2` probe errors, the A99 harness reds, the E-17 S112 to S119 backlog, `test_W7_library_imports_no_sin` needs `nm -D`) |
| lab layout search, 8 workers | 60 min | killed at the cap | no output under `lab/`; `lab.tail.txt` ends in leaked-semaphore warnings; the lab at 200 layouts does not finish in an hour on 10 Mac cores: a Linux-only run, or a smaller batch |

The Linux baseline run diffs against `csim_top.summary.txt` and `csim_controls.summary.txt`.
