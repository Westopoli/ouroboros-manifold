# Clip pipeline: interface the red tests expect (2026-11-24, piece LI5 first half)

Spec source: the brief (no story file). Tests: `tests/skilllab/integration/test_clip_pipeline_{functions,cli}.py`, `tests/qa/test_clip_pipeline_render.py`, `tests/qa/test_fight_replay_fit_extra.py`. Scratch recipe being replaced: `r6-clips/tmp/{rec.py,render.sh,enc.py,poster.sh}`, `r6-compare/tmp/{enc.py,facts.py,render.sh,run.sh}`.

## Module `scripts/skilllab/arena/clip.py`

Constants: `CHUNK_FRAMES = 500`, `WIDTH = 1600`, `FPS = 20`, `DEFAULT_MAX_MB = 9` (a megabyte is 1,000,000 bytes), `DEFAULT_GODOT = ~/.local/bin/godot.real`.

Exceptions: `ClipError(Exception)`; `ToolMissing(ClipError)` (godot, ffmpeg, ffprobe, xvfb-run); `SizeCapUnreachable(ClipError)` (crf 51 still over the cap).

Functions (all must stream: peak memory independent of file size):

- `position_box(fight_path) -> [x0, y0, x1, y1]`: min and max of every unit `x`, `y` in every frame (dead units too), as floats from the file.
- `union_box(*boxes) -> [x0, y0, x1, y1]`.
- `split_chunks(fight_path, chunk_dir, frames_per_chunk=CHUNK_FRAMES) -> list[dict]`: writes `chunk-000.fight.json`, `chunk-001.fight.json` ...; each is the original document (every key but `frames` unchanged) with a slice of `frames`; returns `{"file": Path, "first_tick": int, "frames": int}` per chunk, in order.
- `label_text(version, tick) -> str`: `"<version>  tick <tick>"` (two spaces).
- `record_fight(*, layout=None, situation=None, seed, every, out_dir, tree=None, work_dir=None) -> Path`: runs the sim in `tree` (default: this repo; a subprocess with `cwd=tree`, `PYTHONPATH=tree`, so an older engine tree records its own engine) and writes `<id>-s<seed>-every<K>.fight.json` into `out_dir`. Exactly the bytes `closeup` writes for the same layout, seed and `--every-ticks K` (sight off), written with `json.dump` rather than one string. `situation="SIT-NNNN"` converts as `regression._layout` does (needs `work_dir`). A missing tree raises `ClipError`.
- `encode_clip(frames, ticks, version, out_mp4, max_bytes, ffmpeg="ffmpeg", work=None) -> {"crf": int, "size_bytes": int, "command": str}`: `frames` are PNG paths in order, `ticks[i]` the real tick of frame i; burns `label_text(version, ticks[i])` top-left (font DejaVuSansMono 26, white on black box, as the scratch `enc.py`); H.264 `yuv420p`, `+faststart`, 20 fps, width 1600 (height by aspect, even); raises crf from a low start until the file is `<= max_bytes`.
- `make_poster(frame, version, tick, out_jpg, ffmpeg="ffmpeg") -> None`: first frame, width 1600, same label, JPEG.
- `main(argv=None) -> int`.

## CLI

```
python -m scripts.skilllab.arena.clip --out DIR --name NAME [--version LABEL]
    (--layout L.toml | --situation SIT-NNNN | --fight F.fight.json)
    [--seed N --every K]        required with --layout / --situation; refused with --fight
    [--tree DIR]                engine tree for --layout / --situation
    [--box x0,y0,x1,y1] [--box-with FIGHT]...     extra camera extent; --box-with is repeatable
    [--max-mb 9] [--chunk 500] [--work DIR] [--keep-work]
    [--godot PATH] [--ffmpeg PATH] [--ffprobe PATH]
```

`--version` defaults to NAME. Writes `DIR/NAME.mp4`, `DIR/NAME-poster.jpg`, `DIR/NAME.facts.json`, and nothing else in DIR; on any failure none of the three is left. The work dir (frames, chunks, the fight file when recorded) is deleted on success unless `--keep-work`.

Exit codes: 0 ok; 2 bad arguments, unreadable or frameless fight file, or a rejected layout (`REJECT ...` on stdout, as `closeup`); 3 a required tool is missing (godot, ffmpeg, ffprobe, xvfb-run; the message names it; checked before any work); 4 godot or ffmpeg failed; 5 `SizeCapUnreachable`.

Camera: the scene gets `OM_FIT_EXTRA` = `camera_box` for every chunk, so all chunks of a clip, and all clips given each other with `--box-with`, share one camera. `camera_box = union_box(position_box(own fight), --box, position_box(each --box-with))`.

Render: `xvfb-run -a -s '-screen 0 1920x1080x24' <godot> --path <repo> --display-driver x11 --rendering-driver opengl3 -w --position 0,0 --resolution 1920x1080 --fixed-fps 30 res://scenes/proto/fight_replay/fight_replay.tscn` with `OM_FIGHT`, `OM_SHOT_OUT`, `OM_FIT_EXTRA`, software GL, no DISPLAY.

## Scene change (source, for the builder)

`scenes/proto/fight_replay/fight_replay.gd` `_setup_camera`: when `OM_FIT_EXTRA` is `x0,y0,x1,y1` (four floats) the fit box is the union of every position, the ground features and that box (the scratch patch in `r6-clips/proj`). `qa_state().camera.fit` already reports the fit.

## `facts.json` (exact key set)

```
name, version, kind ("layout" | "situation" | "fight-file"), layout_id, seed, snapshot_every_ticks,
winner, survivors_A_B [a, b], last_tick (result.ticks), end_kind (result.end), capped,
frames (frames in the fight file), first_tick, last_frame_tick,
label {first, last}                      the label text of frame 0 and of the last frame
camera_box [4], position_box [4]
video {file, codec, pix_fmt, fps, width, height, frames, duration_s, size_bytes, max_bytes, crf, faststart, sha256}
poster {file, sha256}
fight {file, sha256, size_bytes}         file as given for --fight, else the recorded file's name
record_command                           string, null for --fight; work and out dirs written as <work> and <out>
render_command, encode_command           strings, same placeholders; render has OM_FIT_EXTRA, encode has libx264 yuv420p +faststart
tree, engine_sha                         null for --fight; else tree = the tree path (default: the repo root) and engine_sha = git rev-parse HEAD of it
chunk_frames
times {generated_at, record_s, render_s, encode_s}   the only keys allowed to differ between two runs
```

`video.file` and `poster.file` are base names. A re-run of the same arguments gives byte-identical `mp4`, poster and facts outside `times`.
