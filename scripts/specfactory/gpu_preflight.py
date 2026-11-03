#!/usr/bin/env python3
"""H-073 gate-gpu-preflight. CLI: read free graphics memory from nvidia-smi and print one line.

  GPU OK <free_mib>               exit 0
  GPU LOW <free_mib> need <need>  exit 3 (free < need; retryable, not a test red)
  GPU UNKNOWN                     exit 0 (no nvidia-smi, or unreadable: never blocks a machine without a card)

NEED_MIB is DRAFT-gpu-need, Westley's number to rule. The wait before `GATE <stage> GPU-LOW`
(MERGE_GATE_GPU_WAIT_S, default 1200 = DRAFT-gpu-wait) lives in merge_gate.sh.
Also holds the log classifier merge_gate_support.py uses for `GPU-MEMORY`.
See also: docs/stories/H-073.md, merge_gate.sh gpu_wait, merge_gate_support.py playthrough_check / lane_plays_check."""
import re
import subprocess
import sys

NEED_MIB = 3000  # DRAFT-gpu-need: Westley rules this number

GPU_SIGNATURES = ("ERR_CANT_CREATE", "index_array_create", "VK_ERROR_OUT_OF_DEVICE_MEMORY")
_SECTION = re.compile(r"^_{3,} .+ _{3,}$", re.M)


def free_mib():
    """Free device memory in MiB, or None when nvidia-smi is missing or unreadable."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=30)
        used, total = (int(x) for x in out.stdout.strip().splitlines()[0].split(","))
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None
    return total - used


def gpu_memory_only(log: str) -> bool:
    """True when the log's reds are all GPU-memory signatures: a real code red always wins. With pytest's
    per-test sections every section must carry a signature; without them the log must carry one and no assertion."""
    if not any(s in log for s in GPU_SIGNATURES):
        return False
    parts = _SECTION.split(log)[1:]
    if parts:
        return all(any(s in p for s in GPU_SIGNATURES) for p in parts)
    return not re.search(r"^E\s+(assert|\w*Error)|AssertionError", log, re.M)


def main() -> int:
    free = free_mib()
    if free is None:
        print("GPU UNKNOWN")
        return 0
    if free < NEED_MIB:
        print(f"GPU LOW {free} need {NEED_MIB}")
        return 3
    print(f"GPU OK {free}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
