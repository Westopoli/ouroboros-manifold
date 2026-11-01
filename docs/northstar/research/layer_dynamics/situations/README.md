# Situations

Westley authors each fight situation here as one file, `SIT-NNNN-<kind>.md`, copied from `TEMPLATE.md`. Words and small tables only; `scripts/skilllab/arena/situations.py` (H-040 part 5) turns each file into a catalogue layout (`../catalogue/L-NNNN.toml`) in the H-025 schema and checks it against the layout rules. A situation written for a later stage is converted and waits in the catalogue until its stage runs. Verdicts on the fights go in `../catalogue/verdicts.md`, one row per fight id, in his words.
