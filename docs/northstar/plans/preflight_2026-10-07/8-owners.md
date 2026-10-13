# Pre-flight scout 8-owners (2026-10-07, Sonnet, read-only)

Scout 8 is done and the worktree is removed. Nothing is committed; the rows below were only run through `pieces.py` `check_owns_disjoint` (the same check `owner_lint.py` filters), on a merged base. The merged base is main plus the `TERRAIN-3` row and `C8` narrowing from `push/terrain3-land-2`, plus the `NET-wire-A` rows from `push/land-1007a`. That run returned zero VG findings.

Two facts to know first:
- origin has `push/land-1007a`, not `land-1007b`. I used 1007a: 30 ahead, 46 behind main.
- `pieces.py` checks every overlapping pair, attached or not. Each new row therefore needs a `depends_on` chain to every row it overlaps.

## File table (owner rows on main; "pend" is a stale-looking `pending`)

| File | Lanes | Owner rows |
|---|---|---|
| `csrc/pipe/om_pipe.c` | A, C, D, E, F, stage 3 | T1 (attached). Stage 3's diff touches it with no row. |
| `csrc/ouroboros_sim.h`, `signatures.toml` | A, C, D, E, stage 3 | core (no status, so in flight by lint), A2-contract and A117-contract (attached), A94-contract, PP-contract and SPEEDCAP-contract (pend) |
| `docs/architecture.md` | A, C, D, E, F | DOCS-arch (attached), PP-contract (pend) |
| `autoload/c_bridge.gd` | A, C, E, F, stage 3 | C2, T2g, C3, C4, C5, C8, all attached. No pending row. |
| `scenes/tactical_c/**` (`tactical_view.gd`/`.tscn`, `map_layer.gd`, `unit_visuals.gd`) | A, C, D, F5, stage 3, tv-read | C5 and C8 via glob (attached); `terrain_layer.gd` also TERRAIN-3 (pend). Not in `C5`/`C8`: the branch `tv-read` has no row. |
| `scenes/galaxy/**` | B | C2 and C8 (attached) |
| `scenes/shared/world_view/**` | B | none |
| `autoload/scene_router.gd` | B, F, E? | C8 (attached); `land-1007a` edits it |
| `csrc/terrain.c` | C, stage 3 | TERRAIN-1 (pend) |
| `csrc/mission.c` | D, E, stage 3 | B9 (pend) |
| `csrc/unit.c` | E | B10, B10c (attached), B10b and PP-unit (pend) |
| `csrc/tactical_mapgen.c` | D | B15m (attached), PP-mapgen (pend) |
| `csrc/checksum_full.c` | E (new world state in the hash), stage 3 | NET-backend (pend) |
| `csrc/save.c`, `csrc/om_internal.h` | E, stage 3 | T2c (attached); `om_internal.h` is core and A94-contract |
| `csrc/economy*.c` | E | none (new); `Makefile` uses `wildcard csrc/*.c`, so no Makefile edit |
| `scenes/main_menu/**` | F, stage 3 | C1 (attached); C8 drops it on the stage 3 branch |
| `scenes/lobby/**` | F | none (new) |
| `Makefile` | F | core (no status) |
| `export_presets.cfg` | F | `NET-wire-A` (pending, on the `land-1007a` branch only) |
| `autoload/net/**` | F | NET-backend (glob on main; `land-1007a` narrows it to three files); `NET-wire-A` (pending, branch only) |
| `scripts/build_pipe_*.sh`, `scripts/codesign_macos.sh` | F | none (new) |
| `tests/qa/desktop/**` | A, C, F, stage 3 | G-qadesktoptests (no status) |
| `autoload/qa_daemon.gd` (`qa_state` inventory) | A (guard 1) | C7 (attached) |
| `autoload/era_config.gd` | C, stage 3 | none on main; TERRAIN-3 on its branch |

## Collisions by pair (a file in more than one lane)

- **A+C:** `tactical_view.gd`, `c_bridge.gd`, `om_pipe.c`, header, `signatures.toml`, `architecture.md`.
- **A+D:** `tactical_view.gd`, `om_pipe.c`, header, `signatures.toml`, `architecture.md`.
- **A+E:** the frame `structures` field is in both lanes' contract. It must be one definition. Also `om_pipe.c`, header, `signatures.toml`, `architecture.md`.
- **A+F:** `tactical_view.gd` (W5), `c_bridge.gd`, `om_pipe.c`, `architecture.md`, `tests/qa/desktop/**`.
- **C+D:** `tactical_view.gd`, `om_pipe.c`, header.
- **C+E:** `om_pipe.c`, header, `c_bridge.gd`.
- **C+F:** `tactical_view.gd`, `c_bridge.gd`, `om_pipe.c`, `scenes/main_menu/**` (stage 3 first).
- **D+E:** `mission.c`, `om_pipe.c`, header, `c_bridge.gd`.
- **D+F:** `tactical_view.gd`, `om_pipe.c`, `c_bridge.gd`.
- **E+F:** `om_pipe.c`, `c_bridge.gd`, header, and `scene_router.gd` if E adds an economy route.
- **B+F:** `scene_router.gd` (B's mission-to-galaxy transition).
- **B+A, B+C, B+D, B+E:** no file collision.

Live collisions on unmerged branches:
- `tv-read` and `terrain3-land-2` produce a merge conflict in `tactical_view.gd` (`git merge-tree`).
- `terrain3-land-2` and `land-1007a` conflict in `pieces.toml` and the ledger.
- `tv-read` and `land-1007a` conflict only in the ledger.

Registry defects:
- `TERRAIN-3` owns 10 files, but its diff has 38. The rest sit under B9, TERRAIN-1, NET-backend, C1, C5 and others. Its clerk must pass a comma list of ids to the footprint fence, or the row must be completed first.
- `NET-backend` is set to `status = "landed"` on `land-1007a`. `owner_lint` counts anything but `attached` or `done` as in flight, so it should be `attached`.
- `pieces.py --check` already FAILs on main for the pair `T2g/NET-backend`.
- About 25 rows say `pending` or have no status but their work is landed (B9, B10b, B14, PP-*, TERRAIN-1/2, A94-*, SPEEDCAP, core, G-*). Every one of them counts as in flight. I did not verify which are actually landed.

## Sequencing graph (rows are in `depends_on` order)

```
stage 3 (TERRAIN-3) + land-1007a (NET-wire-A)      first; tv-read waits, then rebases onto VG-A
  -> VG-CONTRACT   (one gate; sole owner of om_pipe.c, header, signatures.toml, architecture.md, c_bridge.gd, checksum_full.c)
       -> VG-A  -> VG-C  -> VG-D  -> VG-F5     (tactical_view.gd chain: A, then C, then D, then F's W5)
       -> VG-E  -----------^ (E before D on mission.c)
       -> VG-B        (independent; scene_router.gd edit only if the transition needs it)
       -> VG-F        (everything except tactical_view.gd; scene_router.gd; main_menu after stage 3)
```

- **`om_pipe.c`:** only `VG-CONTRACT` holds it. It carries the serializers for A/C/D/E, `net_step`, and `_setmode`. Lanes then implement getters in new `csrc/*.c` files (free via the wildcard) and never reopen `om_pipe.c`. If a getter shape changes, that needs a contract amendment, not a lane edit.
- **`c_bridge.gd`:** the six attached owners are history. After stage 3, `VG-CONTRACT` is the only owner, and it adds the wrappers for all new verbs, the frame passthrough, and the exe path (W8c).
- **`tactical_view.gd`:** C5 and C8 are attached, and both stage 3 and `tv-read` edit it now. They land first and second. After that the chain is A, C, D, F5. F must split because W5 is last on this file while the rest of F runs early.
- **`scenes/main_menu/**`:** `VG-F` takes it only after `TERRAIN-3` lands, which drops it from C8. C1 is attached.
- **`scene_router.gd`:** open for the Architect. I gave it to `VG-F` (lobby route, and `land-1007a` already edits it). B and E should avoid it, or `VG-CONTRACT` pre-registers the routes.

## New rows

Add them to `pieces.toml` only after `TERRAIN-3` and `NET-wire-A` are on main. Otherwise their ids are unknown to the file. Shown here: `id`, `owns`, `owns_glob`, `depends_on`. The rest of each row is mechanical: `manager`, `wave = 7`, `acceptance`, `status = "pending"`, `tests_pending = true`.

```toml
[[piece]]  # id = "VG-CONTRACT"
owns = ["csrc/ouroboros_sim.h","docs/northstar/spec_factory/signatures.toml","docs/architecture.md","csrc/pipe/om_pipe.c","csrc/om_internal.h","csrc/checksum_full.c","autoload/c_bridge.gd","tests/csim/test_VG_contract.py","tests/transport/test_pipe_vg_contract.py","tests/test_c_bridge_vg.gd"]
depends_on = ["TERRAIN-3","PP-contract","A94-contract","SPEEDCAP-contract","NET-backend","TERRAIN-1","core","T1","C8","C5","T2g"]
[[piece]]  # id = "VG-A"
owns = ["autoload/qa_daemon.gd"]
owns_glob = ["scenes/tactical_c/**","csrc/tactical_events.c","tests/test_vg_a_*.gd","tests/qa/desktop/test_vg_a_*.py"]
depends_on = ["VG-CONTRACT","TERRAIN-3","C7","G-qadesktoptests"]
[[piece]]  # id = "VG-B"
owns_glob = ["scenes/galaxy/**","scenes/shared/world_view/**","tests/test_vg_b_*.gd"]
depends_on = ["VG-CONTRACT","C2","C8"]
[[piece]]  # id = "VG-C"
owns = ["csrc/terrain.c","autoload/era_config.gd"]
owns_glob = ["scenes/tactical_c/**","assets/land/**","tests/test_vg_c_*.gd","tests/qa/desktop/test_vg_c_*.py"]
depends_on = ["VG-A","TERRAIN-3","TERRAIN-1","G-qadesktoptests"]
[[piece]]  # id = "VG-D"
owns = ["csrc/tactical_mapgen.c","csrc/space_kit.c"]
owns_glob = ["scenes/tactical_c/**","tests/csim/test_VG_D_*.py","tests/test_vg_d_*.gd"]
depends_on = ["VG-C","VG-E","PP-mapgen","B15m"]
[[piece]]  # id = "VG-E"
owns = ["csrc/mission.c","csrc/unit.c","csrc/save.c"]
owns_glob = ["csrc/economy*.c","scenes/settlement/**","scenes/economy/**","tests/csim/test_VG_E_*.py","tests/test_vg_e_*.gd"]
depends_on = ["VG-CONTRACT","B9","B10b","PP-unit","T2c"]
[[piece]]  # id = "VG-F"
owns = ["Makefile","export_presets.cfg","autoload/scene_router.gd","scripts/codesign_macos.sh","tests/test_main_menu_items.gd"]
owns_glob = ["scenes/lobby/**","scenes/main_menu/**","autoload/net/**","scripts/build_pipe_*.sh","tests/test_vg_f_*.gd","tests/transport/test_vg_f_*.py"]
depends_on = ["VG-CONTRACT","TERRAIN-3","NET-wire-A","NET-backend","core","C1","C8"]
[[piece]]  # id = "VG-F5"
owns = ["scenes/tactical_c/tactical_view.gd","tests/test_vg_f5_hookup.gd"]
depends_on = ["VG-D","VG-F"]
```

- **Lint minimums:** the row sets above passed with zero VG findings. Pruned, the minimum was `VG-A:[TERRAIN-3]`, `VG-C:[VG-A]`, `VG-D:[VG-C, PP-mapgen]`, `VG-F5:[VG-D]`, `VG-E:[PP-unit, T2c]`. I kept the semantic `VG-CONTRACT` and `VG-E` dependencies anyway.
- **Row count:** one row per lane is not enough. It takes eight rows: a contract row, A to F, and F5 split off. E can stay one row only if the economy client uses new scenes alone.
- **Test fence:** the footprint fence counts tests, so each row owns its own test globs. I added `tests/test_main_menu_items.gd` to `VG-F`, because stage 3 edits it and nothing owns it.

## Existing rows to retire or narrow

- **No narrowing is needed:** C5, C8, C2, C1, T2g, T1 and the other attached rows stay as history. The lint ignores attached pairs, and chaining through `TERRAIN-3` or `C8` is enough.
- **Already done on the branches:** stage 3 drops `scenes/main_menu/**` from C8, and `land-1007a` narrows `autoload/net/**`.
- **Needed:** flip stale `pending` rows to `attached` after verifying each is landed (the list under Registry defects). Do this before the VG rows land, or every VG row has to name them as dependencies. Also fix `NET-backend` from `"landed"` to `"attached"`, and resolve the `T2g/NET-backend` overlap.
- **Retire:** `TERRAIN-3` and `NET-wire-A` once they land. Complete `TERRAIN-3`'s owns list before its gate.

## Contract wave recommendation

Do one combined wave, `VG-CONTRACT`, with one gate. It covers:
- A: tactical events in the frame.
- A and E: the shared `structures` field.
- C: the height array.
- D: the space-kit param and geometry.
- E: workers and lots in the frame, plus their verbs and a save-version bump (the same bump style as stage 3's `TD-SAVE-7`).
- F: `net_step` emitting the tactical frame, and `_setmode`.
- All bridge wrappers.

Sequential pieces would take 6 gates (A, C, D, E×2, F's W-contract) and would serialise the same four files six times. F's `net_step` has to emit the same frame as `tactical_step` (`write_tactical`), so it must follow or join the frame fields, not precede them.

Reserve one more gate (2 total) for an E amendment, because E's open economy rules may still move shapes. Any field a lane spec has not fully pinned stays out of the wave and goes into that amendment. That keeps the "frozen and minimal" rule.

Unverified: whether tactical-event emission (A) needs edits in `mission.c` or `unit.c` (A against E on those files), and whether D's mapgen mode switch needs a hook in `mission.c`. Scout 1 (legacy inventory) and scout 5 (space kit) answer these. The `VG-D` and `VG-E` ordering above assumes the answer is yes.
