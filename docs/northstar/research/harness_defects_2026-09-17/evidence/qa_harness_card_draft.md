---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "scenes/harness/e02_harness.gd implements the T2 QA harness scene: the desktop debug-port protocol (state/tree/nav/quit per agora's docs/desktop-qa-protocol.md) plus rendering one region's six numbers from a JSON snapshot file into the Status label, so agora's qa.toml scenario region-numbers-render (text_contains \"stability:\") can pass. Does NOT touch the .tscn (already committed as a skeleton) and does NOT write the snapshot file itself — that is a separate, not-yet-built bridge script (see note below); this card only consumes whatever JSON already sits at the snapshot path."
acceptance:
  - "/home/westopoli/Projects/ouroboros-manifold/.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_e02_harness_render.py"
allowed_files: "scenes/harness/e02_harness.gd"
snippet_file: scenes/harness/e02_harness.gd
snippet_symbol: "_load_snapshot, _format_region, _handle, _tree_rows"
test_file: tests/test_e02_harness_render.py
expected_lines: 90
max_wall_minutes: 25
---

## Brief for DeepSeek

Fill in the four stubbed functions in `scenes/harness/e02_harness.gd`. Everything else
in the file (the `extends`, consts, `@onready` var, `_ready()`, `_debug_port()`,
`_process()`) is already correct — copy it through unchanged in your whole-file reply.

**Protocol (agora repo, `docs/desktop-qa-protocol.md`).** One TCP debug port, opened by
`_ready()` (already wired). One command per line, newline-terminated, ASCII/UTF-8. One
JSON reply per command, newline-terminated, on the same connection.

- `state` → reply a JSON object with at least `"route": "harness"`.
- `tree` → reply a JSON array, one object per inspectable element, shaped
  `{"role": ..., "name": ..., "text": ..., "x": ..., "y": ..., "w": ..., "h": ...,
  "enabled": true}`. This scene has exactly one element: the `Status` label. Use
  `status.get_global_rect()` for x/y/w/h (screen coordinates), `status.text` for both
  `name` and `text`, role `"label"`.
- `nav <anything>` → single-route scene, ack unconditionally: reply
  `{"route": "harness"}` (do not change route).
- `quit` → reply `"bye"` then `get_tree().quit()`.
- Any other line → no reply (drop it).

Reference implementation of this exact shape (a different repo, read-only, copy the
pattern): `agora-proving-ground/probe_d/toy_scene/main.gd`, functions `_handle` and
`_tree`. This scene has no click/layer/fault behavior — only `state`/`tree`/`nav`/`quit`.

**Snapshot rendering.** `_load_snapshot()` reads the file at `SNAPSHOT_PATH` (already
declared as a const in the skeleton, resolved from `QA_SNAPSHOT_PATH` env or a default —
that resolution is already written, don't redo it) using `FileAccess.open(path,
FileAccess.READ)`, parses it as JSON with `JSON.new().parse(...)`, and returns the
first entry of its `"regions"` array as a `Dictionary`. If the file does not exist, or
parsing fails, or `"regions"` is empty, return `{}` — do not push_error, do not crash.

The file shape (written by a separate script, not part of this card):

```json
{"type": "full_snapshot",
 "regions": [{"region_idx": 0, "stability": 41.2, "capacity": 55.0,
              "military": 30.0, "economy": 60.0, "tension": 12.5, "population": 48.0}]}
```

`_format_region(r)` takes that dict and returns exactly this string shape (2 decimal
places, `%.2f`, literal `" | "` separators, in this field order):

```
stability: 41.20 | capacity: 55.00 | military: 30.00 | economy: 60.00 | tension: 12.50 | population: 48.00
```

If `r` is empty (missing keys), format every missing field as `0.00` — do not crash,
do not omit a field. Use `r.get("stability", 0.0)` etc. for every one of the six keys.

`_ready()` already calls `_load_snapshot()` then `status.text = _format_region(region)`
before opening the debug port — do not reorder this or the `tree` command will see stale
text.

## Skeleton

The parent commits both of these before this card runs; the card only rewrites the four
stub functions inside the `.gd` file, keeping the rest byte-for-byte.

`scenes/harness/e02_harness.tscn` (new file, minimal, not touched by this card):

```
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scenes/harness/e02_harness.gd" id="1_harness"]

[node name="E02Harness" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1_harness")

[node name="Status" type="Label" parent="."]
layout_mode = 0
offset_left = 40.0
offset_top = 40.0
offset_right = 900.0
offset_bottom = 80.0
text = "stability: -- | capacity: -- | military: -- | economy: -- | tension: -- | population: --"
```

`scenes/harness/e02_harness.gd` (skeleton the card starts from):

```gdscript
extends Control

const DEFAULT_PORT := 47010
const SNAPSHOT_PATH := _resolve_snapshot_path()

var server := TCPServer.new()
var peers: Array[StreamPeerTCP] = []
var region: Dictionary = {}

@onready var status: Label = $Status


static func _resolve_snapshot_path() -> String:
	var env_path := OS.get_environment("QA_SNAPSHOT_PATH")
	return env_path if env_path != "" else "user://qa/e02_snapshot.json"


func _ready() -> void:
	get_window().title = "E02Harness"
	region = _load_snapshot()
	status.text = _format_region(region)
	var err := server.listen(_debug_port(), "127.0.0.1")
	if err != OK:
		push_error("debug port listen failed: %d" % err)


func _debug_port() -> int:
	for arg in OS.get_cmdline_args():
		if arg.begins_with("--debug-port="):
			return int(arg.substr(len("--debug-port=")))
	var env_port := OS.get_environment("QA_DEBUG_PORT")
	if env_port != "":
		return int(env_port)
	return DEFAULT_PORT


func _load_snapshot() -> Dictionary:
	# STUB
	return {}


func _format_region(r: Dictionary) -> String:
	# STUB
	return ""


func _process(_delta: float) -> void:
	while server.is_connection_available():
		peers.append(server.take_connection())
	for peer in peers.duplicate():
		peer.poll()
		if peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
			peers.erase(peer)
			continue
		if peer.get_available_bytes() > 0:
			var line: String = peer.get_utf8_string(peer.get_available_bytes()).strip_edges()
			_handle(peer, line)


func _handle(peer: StreamPeerTCP, line: String) -> void:
	# STUB
	pass


func _tree_rows() -> Array:
	# STUB
	return []
```

`tests/test_e02_harness_render.py` (new file, committed by the parent as the gate the
card must pass — not edited by the card):

```python
import json
import os
import pathlib
import socket
import subprocess
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
GODOT = "/home/westopoli/.local/bin/godot"
PORT = 47011
SNAPSHOT_PATH = REPO / ".qa" / "e02_snapshot_test.json"

pytestmark = pytest.mark.skipif(not pathlib.Path(GODOT).exists(), reason="godot required")


def _write_fixture_snapshot() -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps({
        "type": "full_snapshot",
        "regions": [{"region_idx": 0, "stability": 41.2, "capacity": 55.0,
                     "military": 30.0, "economy": 60.0, "tension": 12.5,
                     "population": 48.0}],
    }))


def _rpc(port: int, cmd: str, timeout: float = 5.0) -> dict:
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
        sock.sendall((cmd + "\n").encode("utf-8"))
        line = sock.makefile("rb").readline()
    return json.loads(line.decode("utf-8"))


def test_harness_renders_region_numbers():
    _write_fixture_snapshot()
    env = {**os.environ, "QA_SNAPSHOT_PATH": str(SNAPSHOT_PATH), "QA_DEBUG_PORT": str(PORT)}
    proc = subprocess.Popen(
        [GODOT, "--headless", "--path", str(REPO),
         "res://scenes/harness/e02_harness.tscn", f"--debug-port={PORT}"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.time() + 15.0
        reply = None
        while time.time() < deadline:
            try:
                reply = _rpc(PORT, "state", 0.5)
                break
            except OSError:
                time.sleep(0.1)
        assert reply is not None, "harness never answered `state`"
        assert reply.get("route") == "harness"
        tree = _rpc(PORT, "tree")
        text = " ".join(row.get("text", "") for row in tree)
        assert "stability:" in text
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
```
