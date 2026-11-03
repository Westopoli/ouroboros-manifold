"""H-074: a full gate scratch (quota or disk) is an environment fault, never a code red.

`scratch_full_only(log)` is True when the log carries a scratch-full signature and no real code red beside it.
Mirrors gpu_preflight.gpu_memory_only (H-073). See also: docs/stories/H-074.md, merge_gate_support.py
playthrough_check and lane_plays_check, merge_gate.sh scratch_full_exit.
"""
import re

SCRATCH_SIGNATURES = ("Disk quota exceeded", "No space left on device")
_SECTION = re.compile(r"^_{3,} .+ _{3,}$", re.M)  # pytest's per-test failure header


def scratch_full_only(log: str) -> bool:
    """With pytest's per-test sections every section must carry a signature (a real code red always wins);
    without them the log must carry one and no assertion."""
    if not any(s in log for s in SCRATCH_SIGNATURES):
        return False
    parts = _SECTION.split(log)[1:]
    if parts:
        return all(any(s in p for s in SCRATCH_SIGNATURES) for p in parts)
    return not re.search(r"^E\s+(assert|\w*Error)|AssertionError", log, re.M)
