"""Red-phase tests for `_load_sim_env` in pipe_transport.

Step C: when sim is launched with `--load <slot_id>`, it must rehydrate sim_env
from the autosave file matching the shape `_setup_sim_env()` returns so the
event loop can resume cleanly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from save.autosave import autosave_world_view


def _make_sim_env_and_autosave(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pipe_transport
    env = pipe_transport._setup_sim_env(seed=7)
    env["current_tick"] = 18
    env["era_id"] = "settled_reach"
    env["trigger_state"] = {
        list(env["world"].regions.keys())[0]: {
            "evt_garrison_collapse": True,
            "evt_regional_revolt_cooldown": 5,
        }
    }
    autosave_world_view(env)
    return env


def test_load_sim_env_returns_setup_env_keyset(tmp_path, monkeypatch):
    import pipe_transport
    original = _make_sim_env_and_autosave(tmp_path, monkeypatch)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert set(restored.keys()) >= set(original.keys()), \
        f"missing keys: {set(original.keys()) - set(restored.keys())}"


def test_load_sim_env_restores_tick(tmp_path, monkeypatch):
    import pipe_transport
    _make_sim_env_and_autosave(tmp_path, monkeypatch)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert restored["current_tick"] == 18


def test_load_sim_env_restores_trigger_state_and_noise_offsets(tmp_path, monkeypatch):
    import pipe_transport
    original = _make_sim_env_and_autosave(tmp_path, monkeypatch)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert restored["trigger_state"] == original["trigger_state"]
    assert restored["noise_offsets"] == original["noise_offsets"]


def test_load_sim_env_derives_player_fid_from_registry(tmp_path, monkeypatch):
    import pipe_transport
    original = _make_sim_env_and_autosave(tmp_path, monkeypatch)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert restored["player_fid"] == original["player_fid"]


def test_load_sim_env_returns_none_when_slot_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    import pipe_transport
    assert pipe_transport._load_sim_env("nonexistent_slot") is None


def test_load_sim_env_restores_regions(tmp_path, monkeypatch):
    import pipe_transport
    original = _make_sim_env_and_autosave(tmp_path, monkeypatch)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert set(restored["world"].regions.keys()) == set(original["world"].regions.keys())


def test_load_sim_env_restores_registry(tmp_path, monkeypatch):
    import pipe_transport
    original = _make_sim_env_and_autosave(tmp_path, monkeypatch)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert set(restored["registry"].keys()) == set(original["registry"].keys())


# ── BLOCKER 1 Step C: last-time-jump message replay ───────────────────────────

_SAMPLE_TJ_MESSAGES = [
    {"type": "time_jump_start", "time_jump_id": "tj_opening", "span_years": 5,
     "total_keyframes": 1, "total_entries": 1,
     "faction_names": {"player": "Player"},
     "ownership_timeline": [{"tick": 5, "ra": "player"}]},
    {"type": "chronicle_entry", "time_jump_id": "tj_opening", "entry_id": "ce_0",
     "tick_range_start": 0, "tick_range_end": 5,
     "base_form": "A reach holds.", "expanded_form": "A reach holds firm."},
    {"type": "keyframe", "time_jump_id": "tj_opening", "keyframe_index": 0,
     "tick": 5, "chronicle_entry_id": "ce_0",
     "regions_snapshot": [{"region_id": "ra", "owner_faction_id": "player",
                           "significance": 0.5, "x": 1.0, "y": 2.0, "z": 0.0}],
     "connections_snapshot": []},
    {"type": "time_jump_end", "time_jump_id": "tj_opening"},
]


def test_load_sim_env_restores_last_time_jump_messages(tmp_path, monkeypatch):
    """_load_sim_env rehydrates the persisted message list verbatim."""
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path))
    import pipe_transport
    env = pipe_transport._setup_sim_env(seed=23)
    env["current_tick"] = 11
    env["era_id"] = "settled_reach"
    env["last_time_jump_messages"] = [dict(m) for m in _SAMPLE_TJ_MESSAGES]
    autosave_world_view(env)
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert restored["last_time_jump_messages"] == _SAMPLE_TJ_MESSAGES


def test_load_sim_env_messages_empty_when_absent(tmp_path, monkeypatch):
    """Backcompat: saves without last_time_jump_messages -> restored gets []."""
    _make_sim_env_and_autosave(tmp_path, monkeypatch)  # baseline save w/o the key
    import pipe_transport
    restored = pipe_transport._load_sim_env(config.AUTOSAVE_SLOT_ID)
    assert restored["last_time_jump_messages"] == []


def test_persisted_message_stream_is_json_roundtrip_safe():
    """Stream must survive json.dumps/loads byte-identical so replay matches live."""
    msgs = _SAMPLE_TJ_MESSAGES
    assert json.loads(json.dumps(msgs)) == msgs


# ── integration: subprocess spawn with --load ──────────────────────────────────

import json
import os
import struct
import subprocess
import threading
import queue as _queue
import time


_SIM_DIR = str(Path(__file__).resolve().parent)
_PROJECT_ROOT = str(Path(_SIM_DIR).parent)
_PIPE_TRANSPORT = str(Path(_SIM_DIR) / "pipe_transport.py")


def _read_framed(pipe):
    header = pipe.read(4)
    if len(header) < 4:
        return None
    length = struct.unpack(">I", header)[0]
    body = pipe.read(length)
    if len(body) < length:
        return None
    return json.loads(body.decode("utf-8"))


def _write_framed(pipe, msg: dict) -> None:
    body = json.dumps(msg).encode("utf-8")
    pipe.write(struct.pack(">I", len(body)) + body)
    pipe.flush()


def _start_reader(proc):
    """One reader thread + queue for the lifetime of the subprocess."""
    q = _queue.Queue()

    def _reader():
        while True:
            m = _read_framed(proc.stdout)
            if m is None:
                q.put(None)
                return
            q.put(m)

    threading.Thread(target=_reader, daemon=True).start()
    return q


def _drain_until(q, deadline_s: float, stop_type: str) -> list[dict]:
    out = []
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        try:
            m = q.get(timeout=0.5)
        except _queue.Empty:
            continue
        if m is None:
            return out
        out.append(m)
        if m.get("type") == stop_type:
            return out
    return out


def test_load_flag_replays_time_jump_messages_verbatim(tmp_path, monkeypatch):
    """End-to-end: spawn sim w/ --load, after ready_for_time_jump expect the
    persisted last_time_jump_messages stream re-emitted byte-identical."""
    monkeypatch.setattr(config, "SAVE_ROOT", str(tmp_path / "saves"))
    import pipe_transport
    env = pipe_transport._setup_sim_env(seed=11)
    env["current_tick"] = 42
    env["era_id"] = "settled_reach"
    saved_messages = [dict(m) for m in _SAMPLE_TJ_MESSAGES]
    env["last_time_jump_messages"] = saved_messages
    autosave_world_view(env)

    proc = subprocess.Popen(
        [os.sys.executable, _PIPE_TRANSPORT,
         "--root", str(tmp_path),
         "--load", config.AUTOSAVE_SLOT_ID,
         "--real-missions"],
        stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=_PROJECT_ROOT,
    )
    try:
        q = _start_reader(proc)
        pre = _drain_until(q, deadline_s=20.0, stop_type="ready")
        assert any(m.get("type") == "ready" for m in pre), "no ready arrived"
        _write_framed(proc.stdin, {"cmd": "ready_for_time_jump"})
        post = _drain_until(q, deadline_s=15.0, stop_type="time_jump_end")
        # Strip anything emitted before the saved stream begins.
        try:
            start_ix = next(i for i, m in enumerate(post)
                            if m.get("type") == "time_jump_start"
                            and m.get("time_jump_id") == "tj_opening")
        except StopIteration:
            raise AssertionError(
                f"time_jump_start not received; got types: {[m.get('type') for m in post]}"
            )
        end_ix = next(i for i, m in enumerate(post)
                      if m.get("type") == "time_jump_end"
                      and m.get("time_jump_id") == "tj_opening")
        emitted = post[start_ix:end_ix + 1]
        assert emitted == saved_messages, (
            f"replay diverged from saved stream.\n"
            f"emitted={emitted}\nsaved={saved_messages}"
        )
        # T2: forbid double-jump. Live opening jump must be SKIPPED on --load.
        # If sim re-runs the opening jump alongside the replay, player sees
        # two time_jump_start envelopes and double narration.
        starts = [m for m in post if m.get("type") == "time_jump_start"]
        ends = [m for m in post if m.get("type") == "time_jump_end"]
        assert len(starts) == 1, (
            f"expected exactly one time_jump_start in --load stream; "
            f"got {len(starts)}: {[s.get('time_jump_id') for s in starts]}"
        )
        assert len(ends) == 1, (
            f"expected exactly one time_jump_end in --load stream; "
            f"got {len(ends)}: {[e.get('time_jump_id') for e in ends]}"
        )
    finally:
        proc.kill()
        proc.wait()
