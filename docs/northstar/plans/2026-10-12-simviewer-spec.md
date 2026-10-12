# Sim viewer spec (SV-0 to SV-3), pre-flighted 2026-10-12

Westley's ask 2026-10-12; the approved plan is `2026-10-12-simviewer-plan.md`. **Where this spec and that plan disagree, this spec wins.** Tooling only: never enters the game loop.

## Pre-flight corrections (each read from code on origin/main 3125ee77)

1. **Framing is binary, not JSON lines.** Every frame, both ways, is a 4-byte big-endian length then the JSON body (`tests/transport/test_pipe_debrief_region_delta.py` `_frame` / `_run`). The first frame the server writes is `hello`. `PipeSession` reads exactly that.
2. **`set_seed` answers no frame on success** (architecture.md:256); only `error` on failure. `step n` answers n `delta` frames; `snapshot` answers one `snapshot`; `mission_start` one `mission`; `objective_complete` one `ack`; `mission_end` and `mission_refuse` a `debrief` then a `snapshot`; `jump` a `chronicle` then a `snapshot`; `save` / `load` per architecture.md session commands. `error` ends any read. The terminal table is a module constant `TERMINAL` in `pipe_session.py`, filled from architecture.md by the builder and pinned by the test.
3. **`objective_complete` exists only in the debug pipe** (`#ifdef OM_DEBUG_INJECT`, `csrc/pipe/om_pipe.c:1731`). The viewer launches `pipe/ouroboros_pipe_dbg` (`make pipe/ouroboros_pipe_dbg`), the same binary the transport tests use.
4. **Client constants:** `DEFAULT_FEATURES = [0,1,2,3,4,5,6,7]` (`autoload/c_bridge.gd:27`); the client's jump is `{"name":"jump","ticks":50}` (`autoload/c_bridge.gd:749`). Both pinned as constants with that citation.
5. **"Pick an outcome" needs a core hook, not a pipe edit.** `om_mission_end` (`csrc/mission.c:1514`) computes retention inside one call and applies the band's consequences in the same call, so the pipe cannot substitute a value afterwards. Westley's idea (a hard-coded value in place of the computed one) is exactly the fix, and the hook is that substitution: a setter `void om_mission_set_retention_override(om_world *w, double r)` stores a transient value in the mission state (an `int` flag plus a `double`, zero by default, not saved, not hashed, cleared by `om_mission_end` after use); `om_mission_end` uses it in place of `om_mission_end_retention`. `mission_end` gains optional `"retention"` (0..1): present and in range calls the setter before `om_mission_end`; out of range or not a number answers `error` reason `bad retention` and changes nothing; in the release pipe a present field answers `error` reason `debug build required`. Without the field behaviour and bytes are unchanged.
6. **Owner conflict:** SV-0 touches `csrc/mission.c`, `csrc/ouroboros_sim.h`, `csrc/pipe/om_pipe.c`, `docs/architecture.md`, `docs/northstar/spec_factory/signatures.toml`; `VG-CONTRACT-E7` and `VG-W2` (queued) own mission.c, the header, architecture.md and signatures.toml. SV-0 queues behind both (`depends_on`), takes no file while they are in flight, and is audited by a second Fable chat. **SV-1 to SV-3 are new files only and run now.**
7. **Until SV-0 lands** the viewer still sends `retention`; the old pipe ignores the unknown field, so the "total failure" pick shows a red mismatch (a known gap, one line in the README), not a crash. The viewer pins the R-077-02 threshold table with its citation and the pick-versus-band mismatch is the tool's finding signal.

## Shared interfaces (frozen; test writers and builders both use exactly these)

`scripts/simviewer/pipe_session.py`
- `PIPE_DBG: Path` (repo root `/pipe/ouroboros_pipe_dbg`), `DEFAULT_FEATURES: list[int]`, `JUMP_TICKS: int = 50`, `TERMINAL: dict[str, ...]` (verb to the frame types it answers, in order; `step` handled by count).
- `class PipeSession`: `__init__(self, argv: list[str] | None = None)` spawns `argv` or `[str(PIPE_DBG)]` with `Popen(stdin=PIPE, stdout=PIPE)`, reads and stores `self.hello: dict`; `send(self, name: str, **fields) -> list[dict]` writes one `{"type":"cmd","name":name,**fields}` frame and returns the frames up to the verb's terminal frame (step: `n` deltas, default `n=1`); raises `PipeError(frame)` when an `error` frame arrives; `close(self)` sends `quit`, waits 5 s, kills on timeout; context manager.
- `class PipeError(Exception)`; `.frame: dict`.

`scripts/simviewer/history.py`
- `LAYOUT_ITERATIONS = 200`, `LAYOUT_SEED = 1`, `RING = 60`.
- `class History`: `__init__(self)`; `apply(self, frame: dict) -> None` folds a `snapshot`, `delta`, `mission`, `debrief` or `chronicle` frame (others ignored); `tick: int`; `regions: dict[int, dict]` (`owner`, `tier`, `military`, `economy`, `tension`, `population`, `stability`, `capacity`); `edges: list[tuple[int,int]]` from the snapshot; `factions: dict[int, dict]`; `ring(region: int, field: str) -> list[float]` (last `RING` values, oldest first, one per applied tick that listed the region); `events(region: int) -> list[dict]` (`tick`, `template`, `chain`, `delta`); `missions: list[dict]` (`tick`, `region`, `archetype`, `band`, `region_delta`); `layout(self) -> dict[int, tuple[float, float]]` (seeded force layout over `edges`, fixed iterations, rounded to 3 decimals, identical bytes over two runs on the same edges); `diff(before: dict, after: dict) -> list[int]` static: regions whose owner or any of the six values differ.

`scripts/simviewer/viewer.py` (SV-3): `class ViewerState` (pure state the draw reads: `mode` "tick"|"mission", `rate` from `RATES = (1,2,5,10,20,50)`, `paused`, `pick` 0..4 or `None`, `selected_region`, `pulse: dict[int,float]`, `last_debrief`) and `def draw(state, history, surface)`; the headless test imports these; `python -m scripts.simviewer` is `__main__.py`.

## Pieces

SV-0 (queued behind E7 and W2; contract; Fable audit), SV-1 `pipe_session.py`, SV-2 `history.py`, SV-3 `viewer.py` (+ README). Tests first by a different agent than the builder, red on the built tree for the stated reason; builders never edit tests; STOP rules in every brief.
