# Lockstep backend: spec (2026-10-05)

Written from the pre-flight of 2026-10-05 (seven scouts; findings cited as facts below). It overrides the plan where they disagree. Scope: the sim and pipe side of peer-to-peer lockstep for 2 to 4 peers commanding one shared force, a client session left unwired, and the proof harness. No Steam. Rules: E-19 R-139-03, R-139-04, R-140-02 to R-140-04, R-242-01; E-13 R-096-07; R-111-03.

Westley's decisions: input delay 3 ticks (150 ms); stall 1 s and drop 60 s as provisional settings; save format 5 to 6 with version 5 saves refused; launch without his review of this file; the result waits for him before it goes to main.

## Changes from the approved plan

| Plan | Spec | Why (pre-flight) |
|---|---|---|
| Reuse the sim's move queue | New command stream; the old queue is left alone | It carries only single-unit move and attack-move and changed a group move's result at tick 10 |
| One command batch per request | One command per `net_submit` frame | The pipe's parser reads flat objects only; no parser change is made |
| Debug verbs to plant a divergence | The driver withholds one command from one peer | No verb is needed for the positive control |
| Edit `csrc/save.c` | No edit | All ten slots are already written and parsed; a module only installs hooks |
| Five modules to save | Seven: units, movement, enemy, fog, support, mission, map | Routing reads the map state |
| A wiring phase after the builders | Every shared-file edit is made first, in the base, as stubs | Then every later lane owns its own files and nothing queues |
| Module section hash and save in one unit | Two stages per module: hash first, save second | The lockstep proof needs only the hashes; save is about 1,000 lines over 12 units and is the risky part |
| FNV-1a byte by byte | One 64-bit word per field | Measured: 1.0 ms against 6.2 ms at 5,000 units |

## Base branch: `push/net-base` (one agent, lands before any lane starts)

All contract and shared-file work, as stubs that build and link. After it, no lane touches a shared file.

1. **`docs/northstar/spec_factory/signatures.toml`** then `python3 scripts/specfactory/sig_table.py --emit` (never hand-edit the generated header block; doc text goes in `note`; bump `symbol_count` and `struct_count`):
   - struct `OMNetCommand` (`source_test = "tests/csim/test_net_cmd_stream.py"`): `tick uint64_t`, `seq uint32_t`, `arg uint32_t`, `x double`, `y double`, `peer uint8_t`, `verb uint8_t`, `layer uint8_t`, `n_units uint8_t`.
   - module `checksum_full.c`: `uint64_t om_world_checksum_full(const om_world*, uint64_t *sections, uint32_t cap)`; `uint32_t om_checksum_section_count(void)`; `const char* om_checksum_section_name(uint32_t)`; `int om_checksum_first_diff(const om_world *a, const om_world *b, uint32_t *section, uint32_t *unit_id)`; `uint32_t om_checksum_unit_hashes(const om_world*, uint64_t *out, uint32_t cap)`.
   - module `cmd_stream.c`: `int om_cmd_submit(om_world*, const OMNetCommand*, const uint32_t *unit_ids)` (0 accepted; nonzero codes: late, duplicate, malformed, full); `void om_cmd_reset(om_world*)`; `uint64_t om_net_tick(const om_world*)`; `uint32_t om_cmd_pending_count(const om_world*)`; `uint32_t om_cmd_log_size(const om_world*)`; `uint32_t om_cmd_log_write(const om_world*, uint8_t *out, uint32_t cap)`; `int om_cmd_log_feed(om_world*, const uint8_t *buf, uint32_t len)`.
   - Verb numbers as an enum in the header in the form the existing enums use: move 0, attack_move 1, attack_target 2, activate_ability 3, set_layer 4, set_emission 5, ping 6, guard 7, assign_commander 8.
2. **`csrc/om_internal.h`**: a section table on `om_world` (for each of the nine sections a hash function pointer `uint64_t (*)(const om_world*)` and, for units, a per-unit function `uint32_t (*)(const om_world*, uint64_t *out, uint32_t cap)`); a `net_state` pointer with its free function; internal prototypes `void om_cmd_apply_tick(om_world*)` and `void om_<module>_install_net_hooks(om_world*)` for unit, move, macro, fog, support, mission, mapgen; `OM_SAVE_FORMAT_VERSION` 6.
3. **`csrc/region.c`** (`om_world_new` and the free path): null the new fields; call each module's `om_<module>_install_net_hooks`; free `net_state`.
4. **Each of `csrc/unit.c`, `tactical_move.c`, `enemy_macro.c`, `fog.c`, `tactical_support.c`, `mission.c`, `tactical_mapgen.c`**: an empty `om_<module>_install_net_hooks` at the end of the file, under a comment line `/* ---- net hooks (lockstep spec 2026-10-05) ---- */`. Module lanes write only below that line.
5. **`csrc/unit.c`**: `om_cmd_apply_tick(w);` as the first statement of `om_tactical_step`, before the zero-units guard, and the same call in the empty branch of `om_tactical_tick_to`. (Pre-flight: it must run before `om_tac_update_period`.)
6. **`csrc/checksum_full.c`, `csrc/cmd_stream.c`**: new files holding the stubs the generator writes; `om_cmd_apply_tick` a no-op.
7. **Version 6 pins**: `csrc/pipe/om_pipe.c` `OM_PIPE_SAVE_FORMAT_VERSION`, `scenes/load_game/load_game.gd` `CURRENT_SAVE_VERSION`, and the three tests that pin the number (`tests/csim/test_E16_B5_save_version.py`, `test_E16_C2_save_version.py`, `tests/test_load_game_wrong_version.gd`), as test defect `TD-NET-save-version-6` with a ledger row.
8. Checks: builds with `make OPT=-O2 WERROR=1`; `sig_table.py --check`; `merge_gate_support.py sig-check`, `sig-blocked`, `symbols`; `libm_lint`; `alg_constants --lint`; `owner_lint`; `tests/csim` failing ids equal to main's; transport 259; with the stubs in place behaviour is unchanged, so no recorded hash may move.

## Lanes (each branches from `push/net-base`; files are disjoint)

| Lane | Files | What |
|---|---|---|
| cksum | `csrc/checksum_full.c`, `tests/csim/test_net_checksum.py` | Sections in fixed order: 0 regions, 1 factions, 2 rng, 3 units, 4 movement, 5 mission, 6 fog, 7 macro, 8 support and map. Regions, factions and rng are hashed here from `om_internal.h` fields; the others through the section table (a missing hook hashes as 0). One 64-bit word per field: `h = (h ^ v) * prime; h ^= h >> 29`. Doubles by bit pattern. `first_diff` names the first differing section and, for units, the lowest differing unit id |
| cmd | `csrc/cmd_stream.c`, `tests/csim/test_net_cmd_stream.py` | State in `net_state`: the net tick, a buffer of pending commands with their unit ids, the log. `om_net_tick` counts tactical steps begun since `om_cmd_reset`; `om_cmd_apply_tick` increments it and applies every command stamped with the new tick, sorted by peer then seq, by calling the existing `om_command_group_move`, `om_command_attack_move`, `om_command_attack_target`, `om_command_activate_ability`, `om_command_set_layer`, `om_command_set_emission`, `om_command_ping`, `om_command_guard`, `om_mission_assign_commander`. A command for a tick already begun is refused as late; a repeated (peer, seq) is ignored; at most 70 unit ids. Every applied command is appended to the log; `om_cmd_log_feed` loads a log into the pending buffer |
| pipe | `csrc/pipe/om_pipe.c`, `docs/architecture.md`, `docs/northstar/spec_factory/transport/command.schema.json`, `tests/transport/test_pipe_net_verbs.py` | Documented first. `net_reset`; `net_submit` (one flat command: `tick, peer, seq, verb, arg, layer, x, y, units[]`), answering `net_ack` with the code; `net_step {n}` stepping n tactical ticks and answering one `net_ack {tick, checksum, sections[]}` with no unit frame (checksum fields present when the tick is a multiple of 10 or `checksum:true` is asked); `net_checksum`; `net_log_dump` and `net_log_load` (hex); `net_state_get` and `net_state_put` (the save buffer as hex, plus the pipe's own `g_tactical_tick`, `g_tac.steps`, `g_mission_archetype`, `g_n_placed_structures`; on put, rebuild the baseline as `load` does). Today's `command` and `tactical_step` verbs are not changed |
| harness | `tests/net/driver.py`, `tests/net/test_lockstep_equal.py`, `test_desync_detect.py`, `test_single_peer_equiv.py`, `test_peer_drop.py`, `tests/net/README.md` | Built on `tests/long/harness.py`'s `Pipe`. A seeded in-process fake network (delay, loss, reordering, one peer drop); the lockstep rule (delay 3, each packet repeats the last 5 ticks, step tick t only when every live peer's packet for t is in, stall and drop as tick counts). Asserts equal full checksums on 2, 3 and 4 peers at every tenth tick to the end of a real mission; the positive control withholds one move command from one peer and requires a mismatch naming the tick and the movement or units section within 10 ticks; one peer with delay 0 through `net_submit` and `net_step` gives the same checksum trace as the same commands through `command` and `tactical_step` |
| gd | `autoload/net/transport.gd`, `loopback_transport.gd`, `lockstep_session.gd`, `tests/test_lockstep_session.gd` | Plain classes loaded by path; no `class_name`, no autoload entry, nothing wired. The test follows the runner's pattern (`extends SceneTree`, `_initialize`, the `PASS: n  FAIL: m` line) and uses no real time |
| trace | `scripts/specfactory/tactical_trace.py`, `tests/specfactory/test_tactical_trace.py`, `scripts/specfactory/merge_gate.sh` | A scripted mission with a scripted command stream on the O0 and O2 builds; full checksums compared every tenth tick; one gate stage after `checksum_trace` |
| mod-unit, mod-move, mod-macro, mod-fog, mod-support, mod-mission, mod-mapgen | that module's file, below its net-hooks comment line; `tests/csim/test_net_save_<module>.py` | Stage 1, the section hash: every field that affects play, rows `[0, n)` only, never caches, never pointers; units also fill the per-unit hash array. Stage 2, the save hooks, installed from `om_<module>_install_net_hooks`: size, write, read; field by field, little-endian, with `OM_SAVE_BYTE_BITS` and `OM_SAVE_BYTE_MASK`; the read parses into scratch, checks length and every count against its cap first, installs only at the end, frees its own memory on failure, accepts length 0, and never touches the world's regions or public accessors (the validate pass runs it on an empty shadow world). Caches are marked for rebuild on first use, not saved. `mod-macro` also moves `g_macro_vocab` into the module state |
| check | `scripts/integration_check.sh`, `docs/northstar/regression.md`, `docs/northstar/baselines/` | Built from the inventory scout's commands; runs on main as the baseline |

Tests come first in every lane, written by a different agent than the builder.

**Stage 2 of the module lanes is the known risk.** The spatial grids are linked lists whose order depends on history; a rebuild after load may walk them in a different order. The stage 2 test for every module is: save mid-battle, load into a fresh world, step both 500 ticks, full checksum equal at every tenth tick. A module whose stage 2 fails is left out; its stage 1 hash still lands.

## Order

1. Base, then its gate.
2. All lanes in parallel; within a lane, test-writer then builder; module lanes run stage 1 then stage 2.
3. One clerk merges every lane that passed its gate into `push/net-land`, runs `tests/net`, every suite and the merge gate from the candidate. It does not push to main.

## Limits for every agent

Sonnet; one step; its own worktree under `~/Projects/om-push/wt/net-<lane>-<step>` from the branch named in its brief; at most 40 tool calls; the last message is the report. Build first (`make libouroboros.so pipe/ouroboros_pipe pipe/ouroboros_pipe_dbg`); never `make clean`; stage files by name; never commit `.import`, `.uid` or build outputs; anything multi-process inside `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0`; kill only its own pids. Stop and report, do not improvise, on: a recorded hash that moves, a public symbol not listed here, an existing test that looks wrong, a file outside the lane, a number or rule nobody gave.

## Kill rule

The run stops if the base fails its gate, or if three lanes are dropped. A lane is dropped after one retry. Dropping `cksum`, `cmd` or `pipe` skips the harness's end-to-end proof, and the report says so.
