# Scale suite

Gated behind `OM_SCALE=1` (see `conftest.py`); the regular gate never runs
this directory. Run: `OM_SCALE=1 python -m pytest tests/csim/scale -q`.

Every test's budget check is `measured_raw_median <= budget / OM_SCALE_CPU_FACTOR`.
The bible's Scale requirements budgets are set for the min-spec machine
(Ryzen 5 1600 / i5-7600 class); this suite has been run on the forge (Ryzen 7
3700X), which is faster single-thread by `OM_SCALE_CPU_FACTOR` (default
1.35). A run on the actual min-spec machine sets `OM_SCALE_CPU_FACTOR=1.0` so
the measured median is checked against the bare budget.
