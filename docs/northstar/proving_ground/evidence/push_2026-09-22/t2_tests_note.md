# T2 tests note — save/load, C side (2026-09-22 two-day push, wave-2 row T2c)

Fenced tests wrote, red now. Impl `csrc/save.c` is M1 job (dep B7), not exist yet.

## File

`tests/csim/test_E16_S111_saving.py` — 9 tests. Three symbols missing from
header + conftest: `om_save_state_size`, `om_save_state_write`,
`om_load_state_read`. Bound local (`_bind_save()`), comment
`# local binding until the F1b freeze lands` per brief. `om_load_state_read`
bound `c_int` restype, not toml's void placeholder — see Q-111-02.

Bug id `_OM_BUG_SAVE_SKIPS_RNG_STATE = 1600` local enum, comment "F5 moves
it into conftest's OMBug." Checked against push-brief decision 6: save.c
owns 1600s range, 1600 correct, not guessed.

## Tests (9)

- `test_R_111_02_size_query_then_write_round_trips` — size query, write into
  exact-size buffer, buffer loads clean into fresh world
- `test_R_111_02_second_write_is_byte_identical` — same world, two writes,
  same bytes
- `test_R_111_02_checksum_equal_at_save_and_after_fifty_more_steps` —
  `om_world_get_state_checksum` matches source right after load and after
  50 more unforced steps, same seed (E-08 R-064-04's property, proved at
  save.c level, E-08 has no `om_time_jump_run` yet)
- `test_R_111_02_load_restores_tick_regions_factions_telegraphs_chain_and_rng` —
  granular restore check: region fields+owner, faction budget+stance,
  pending telegraph list, chain counter, then one unforced step both sides
  to prove RNG stream itself restored (no direct tick-read accessor exists,
  so tick restore proved via `om_world_step`'s return matching)
- `test_R_111_03_wrong_version_word_refused_target_unchanged` — flip first 4
  bytes (XOR 0xFF), refused non-zero rc, target checksum untouched
- `test_R_111_03_truncated_buffer_refused` — half-length buffer, refused
  non-zero rc
- `test_R_111_02_save_load_save_gives_identical_bytes` — save, load fresh
  world, save again, bytes match
- `test_R_111_02_integration_two_hundred_ticks_save_two_hundred_more_checksums_match` —
  10 regions, FACTIONS+EVENTS+FRICTION+ADMIN_REVOLTS+DRIFT (E-16
  mvp_features.toml default), launch events loaded, 200 ticks, save, 200
  more both sides, checksum match at every `om_checksum_cadence()` tick
- `test_control_R_111_02_om_bug_save_skips_rng_state_trips_the_detector` —
  positive control, `OM_BUG_SAVE_SKIPS_RNG_STATE` injected, checksums
  diverge after load (proves the RNG-state assertion above would catch it)

## Red proof

Repo live-dirty right now, not from this task: another agent's F1b
generation mid-flight in `csrc/ouroboros_sim.h` (1651 lines vs HEAD's 817)
and `tests/csim/conftest.py` (1176-line uncommitted diff) — matches
`q2_tests_note.md`'s same finding same session. Header currently fails
compile (duplicate param names `byref`/`c_double`/`int` from in-progress
`sig_table.py` gen — not csrc/conftest, never touched, not mine to fix).
Real `pytest tests/csim/test_E16_S111_saving.py` against live checkout:
`COMPILE ERROR` from conftest's build-on-import, same as every other test
in the dir right now.

Ran instead against clean git worktree at HEAD (`fe6166a`, "test(Q2): fenced
red tests for T1 rts detectors" — last commit before the dirty WIP), copy
of test file only, nothing else touched, worktree deleted after:

```
9 failed in 0.21s
FAILED test_R_111_02_size_query_then_write_round_trips
FAILED test_R_111_02_second_write_is_byte_identical
FAILED test_R_111_02_checksum_equal_at_save_and_after_fifty_more_steps
FAILED test_R_111_02_load_restores_tick_regions_factions_telegraphs_chain_and_rng
FAILED test_R_111_03_wrong_version_word_refused_target_unchanged
FAILED test_R_111_03_truncated_buffer_refused
FAILED test_R_111_02_save_load_save_gives_identical_bytes
FAILED test_R_111_02_integration_two_hundred_ticks_save_two_hundred_more_checksums_match
FAILED test_control_R_111_02_om_bug_save_skips_rng_state_trips_the_detector
```

All 9, same shape:

```
AttributeError: .../libouroboros.so: undefined symbol: om_save_state_size
```

(8x release lib, 1x dbg lib for the control). Every one dies inside
`_bind_save()`'s first line (`lib.om_save_state_size.argtypes = ...`), not
in test body logic — confirms fixture setup (region/faction/telegraph/chain
helpers, all real symbols already in the built lib) runs clean; only the
three missing save symbols block each test. Red for right reason, zero
`TypeError`/`NameError`/other Python bug in the test file itself.

## Q- candidates (full text in module docstring)

- **Q-111-03**, buffer format: S-111 silent on layout. (a) flat memcpy,
  version word first — assumed here, matches the bare-`uint8_t*` signature
  with no chunk/framing calls; (b) versioned TLV stream; (c) other opaque
  layout. Version-word test only checks refusal on a first-4-byte mismatch,
  never what the right word is — holds under any of the three.
- **Q-111-02**, `om_load_state_read` return: signatures.toml says void,
  note "int status plausible." R-111-03 needs refusal + a message naming
  versions; no message accessor anywhere in the header. (a) int status,
  client formats the message from separate (also uncontracted) version
  accessors — bound here, minimal shape satisfying "refused, non-zero"
  literally; (b) int status plus two version out-params; (c) void plus a
  separate `om_load_state_error()` read-after-failure accessor.

## Not tested here

R-111-01 (autosave fires at mission start/end/jump end) and R-111-04
(unlimited campaign slots, no mid-mission save) — client-side triggers, no
C accessor exists or should exist for either, T2g's job (Godot, `tests/test_load_game.gd`).
