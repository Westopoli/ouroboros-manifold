# spec: docs/northstar/proving_ground/PX-19-prefetch-resident-model.md
"""Tests for scripts/specfactory/prefetch_measure.py's pure parsing/stats logic
(gap distribution, load_duration dedup, prompt assembly, token estimate). The
`prep` subcommand's real worktree/make/pytest timing is exercised manually
against a live card for the PX-19 write-up, not re-run here (would need a
scratch git worktree and a real C toolchain in CI for no additional coverage
of this file's own logic)."""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts" / "specfactory"))

import prefetch_measure as pm  # noqa: E402


# --- gaps ------------------------------------------------------------------------------

def test_parse_dispatch_ticks_only_matches_build_and_burn():
    text = (
        "[10:00:00] dispatch -> driver\n"
        "driver: idle\n"
        "[10:01:00] dispatch -> build\n"
        "DONE: report at /home/x/runs/task-20200101-1001/report.md\n"
        "[10:03:00] dispatch -> qa\n"
        "[10:05:00] dispatch -> burn\n"
        "INCOMPLETE: report at /home/x/runs/task2-20200101-1005/report.md\n"
    )
    ticks = pm.parse_dispatch_ticks(text)
    assert len(ticks) == 2
    assert [t.strftime("%H:%M:%S") for _, t in ticks] == ["10:01:00", "10:05:00"]


def test_gap_stats_matches_brief_worked_example():
    # Brief's own two examples, reproduced against the real cron.log's anchored
    # dates: DONE at 21:50:30 -> next dispatch->build at 21:51:33 = 63s; DONE at
    # 14:40:31 -> 14:42:42 = 131s, then 14:42:42 -> 14:43:44 = 62s.
    text = (
        "[21:50:30] dispatch -> build\n"
        "DONE: report at /r/204z3-e05-s038-gate-20260919-2150/report.md\n"
        "[21:51:33] dispatch -> build\n"
        "INCOMPLETE: report at /r/207-e05-step-order-fault-20260919-2151/report.md\n"
    )
    text2 = (
        "[14:40:31] dispatch -> build\n"
        "DONE: report at /r/204b3-e05-damage-history-20260919-1440/report.md\n"
        "[14:42:42] dispatch -> build\n"
        "DONE: report at /r/204z-e05-s034-gate-20260919-1442/report.md\n"
        "[14:43:44] dispatch -> build\n"
        "DONE: report at /r/204b2-e05-unrest-colonize-20260919-1443/report.md\n"
    )
    gaps1 = [g for _, _, g in pm.gap_stats(pm.parse_dispatch_ticks(text))["pairs"]]
    gaps2 = [g for _, _, g in pm.gap_stats(pm.parse_dispatch_ticks(text2))["pairs"]]
    assert gaps1 == [63.0]
    assert gaps2 == [131.0, 62.0]


def test_gap_stats_empty():
    stats = pm.gap_stats([])
    assert stats["count"] == 0
    assert stats["median"] is None


def test_gap_stats_over_300s_count_and_percentiles():
    base = "20200101"
    text = "".join(
        f"[{(i * 100) // 3600:02d}:{((i * 100) % 3600) // 60:02d}:{(i * 100) % 60:02d}] dispatch -> build\n"
        f"DONE: report at /r/task-{base}-0000-{i}/report.md\n"
        for i in range(10)
    )
    ticks = pm.parse_dispatch_ticks(text)
    stats = pm.gap_stats(ticks)
    assert stats["count"] == 9
    assert stats["median"] == 100
    assert stats["p90"] == 100
    assert stats["max"] == 100
    assert stats["over_300s"] == 0


def test_gap_stats_rollover_negative_delta_wraps_forward():
    text = (
        "[23:59:00] dispatch -> build\n"
        "DONE: report at /r/task-20200101-2359/report.md\n"
        "[00:01:00] dispatch -> build\n"
        "DONE: report at /r/task-20200102-0001/report.md\n"
    )
    ticks = pm.parse_dispatch_ticks(text)
    stats = pm.gap_stats(ticks)
    assert stats["pairs"][0][2] == 120  # 2 minutes, not a huge negative number


def test_parse_dispatch_ticks_uses_anchor_to_span_a_real_multi_day_idle_gap():
    # No anchor on the SECOND tick's own outcome line missing would fall back to
    # same-day rollover; here it DOES have one, several days later, and the parser
    # must trust it instead of assuming a same-day wrap.
    text = (
        "[17:44:33] dispatch -> build\n"
        "UNSATISFIABLE: report at /r/111-probe-20260910-1744/report.md\n"
        "[10:02:51] dispatch -> build\n"
        "SPEC-INVALID: report at /r/200-e02-20260914-1003/report.md\n"
    )
    ticks = pm.parse_dispatch_ticks(text)
    stats = pm.gap_stats(ticks)
    gap = stats["pairs"][0][2]
    # real elapsed time is just under 4 days, not the ~16h a naive same-day
    # rollover would compute
    assert gap > 3 * 86400


# --- loads -------------------------------------------------------------------------------

def test_find_load_durations_dedupes_identical_content(tmp_path):
    a = tmp_path / "run1"
    b = tmp_path / "run2"
    a.mkdir()
    b.mkdir()
    payload = json.dumps({"load_duration": 5_000_000_000, "model": "m", "prompt_eval_count": 10})
    (a / "resp_t1.json").write_text(payload)
    (b / "resp_t1.json").write_text(payload)  # identical content, different location
    found = pm.find_load_durations(tmp_path)
    assert len(found) == 1
    assert found[0]["occurrences"] == 2
    assert found[0]["load_duration_s"] == 5.0
    assert found[0]["sha256"] == hashlib.sha256(payload.encode()).hexdigest()


def test_find_load_durations_ignores_files_without_the_field(tmp_path):
    (tmp_path / "state.json").write_text(json.dumps({"task": "x", "phase": "report"}))
    found = pm.find_load_durations(tmp_path)
    assert found == []


def test_find_load_durations_distinct_values_not_merged(tmp_path):
    (tmp_path / "resp_a.json").write_text(json.dumps({"load_duration": 1_000_000_000}))
    (tmp_path / "resp_b.json").write_text(json.dumps({"load_duration": 2_000_000_000}))
    found = pm.find_load_durations(tmp_path)
    assert sorted(v["load_duration_ns"] for v in found) == [1_000_000_000, 2_000_000_000]


def test_find_load_durations_skips_invalid_json(tmp_path):
    (tmp_path / "resp_bad.json").write_text("{not json")
    found = pm.find_load_durations(tmp_path)
    assert found == []


# --- prompt assembly -----------------------------------------------------------------------

def _write_card(path, project_dir):
    path.write_text(
        "---\n"
        f"project: {project_dir}\n"
        "goal: \"test goal\"\n"
        "acceptance:\n"
        "  - \"echo ok\"\n"
        "allowed_files: \"csrc/thing.c\"\n"
        "snippet_file: csrc/thing.c\n"
        "snippet_symbol: \"om_thing_do\"\n"
        "header_file: csrc/thing.h\n"
        "extra_context_files: csrc/internal.h\n"
        "expected_lines: 10\n"
        "max_wall_minutes: 5\n"
        "---\n\n"
        "## Brief for DeepSeek\n\n"
        "Implement om_thing_do.\n"
    )


def test_parse_card_reads_frontmatter_and_body(tmp_path):
    card = tmp_path / "card.md.hold"
    _write_card(card, tmp_path)
    spec, body = pm.parse_card(card)
    assert spec["snippet_file"] == "csrc/thing.c"
    assert "Implement om_thing_do." in body


def test_assemble_worker_prompt_includes_instruction_header_and_skeleton(tmp_path):
    card = tmp_path / "card.md.hold"
    _write_card(card, tmp_path)
    spec, body = pm.parse_card(card)
    worktree = tmp_path / "wt"
    (worktree / "csrc").mkdir(parents=True)
    (worktree / "csrc" / "thing.c").write_text("/* stub */\nvoid om_thing_do(void) {}\n")
    (worktree / "csrc" / "thing.h").write_text("void om_thing_do(void);\n")
    (worktree / "csrc" / "internal.h").write_text("struct om_internal { int x; };\n")

    prompt = pm.assemble_worker_prompt(spec, body, worktree)
    assert "Implement om_thing_do." in prompt
    assert "void om_thing_do(void);" in prompt  # header
    assert "struct om_internal { int x; };" in prompt  # extra context
    assert "/* stub */" in prompt  # whole-file skeleton
    assert "om_thing_do" in prompt.split("OUTPUT:")[-1]


def test_assemble_worker_prompt_uses_header_slice_when_present(tmp_path):
    card = tmp_path / "card.md.hold"
    card.write_text(
        "---\n"
        f"project: {tmp_path}\n"
        "goal: \"g\"\n"
        "acceptance:\n  - \"echo ok\"\n"
        "allowed_files: \"csrc/thing.c\"\n"
        "snippet_file: csrc/thing.c\n"
        "snippet_symbol: \"om_thing_do\"\n"
        "header_file: csrc/thing.h\n"
        "expected_lines: 10\n"
        "max_wall_minutes: 5\n"
        "---\n\n"
        "## Brief for DeepSeek\n\nDo it.\n\n"
        "## Header slice\n\nSLICE_MARKER_TEXT\n"
    )
    spec, body = pm.parse_card(card)
    worktree = tmp_path / "wt2"
    (worktree / "csrc").mkdir(parents=True)
    (worktree / "csrc" / "thing.c").write_text("void om_thing_do(void) {}\n")
    (worktree / "csrc" / "thing.h").write_text("FULL_HEADER_SHOULD_NOT_APPEAR_IF_SLICE_USED\n")
    prompt = pm.assemble_worker_prompt(spec, body, worktree)
    assert "SLICE_MARKER_TEXT" in prompt
    assert "FULL_HEADER_SHOULD_NOT_APPEAR_IF_SLICE_USED" not in prompt


def test_estimate_tokens_is_chars_over_four():
    assert pm.estimate_tokens("a" * 400) == 100
    assert pm.estimate_tokens("") == 0
