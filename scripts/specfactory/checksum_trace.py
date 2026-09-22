#!/usr/bin/env python3
"""F6 item 3 (two-day push): the O0-vs-O2 determinism gate's trace tool.
Loads a given libouroboros*.so, builds a world, steps it, and prints one
checksum line per cadence tick (`om_checksum_cadence()`) plus a final line --
two invocations, one per optimisation level, are then diffed by `--compare`.
The merge gate runs `build/O0/libouroboros.so` against `build/O2/libouroboros.so`
over 500 ticks; any divergence is a determinism-contract violation (CLAUDE.md:
"same seed, same command stream, byte-identical trace ... with a checksum
every 10 ticks").

Loads tests/csim/conftest.py directly (the same importlib technique
tests/qa/t1/run_trace.py already uses) to reuse its struct/enum mirrors and
`_configure_common`, which only takes a ctypes handle and sets its
argtypes/restypes -- it has no dependency on conftest.py's own hardcoded
LIB_PATH constant, so this tool builds its own `ctypes.CDLL(explicit_path)`
per `--lib` and never needs to read or touch that constant. (conftest.py is
fenced to another manager's edit for the freeze window regardless; this
turned out not to require the env-override fallback the item's own text
anticipated -- see the finishing report.)
"""
from __future__ import annotations

import argparse
import ctypes
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSIM_CONFTEST = REPO / "tests" / "csim" / "conftest.py"

_TICK_RE = re.compile(r"^tick (\d+) (\d+)$")
_FINAL_RE = re.compile(r"^final (\d+)$")


def load_csim_conftest():
    spec = importlib.util.spec_from_file_location("_checksum_trace_csim_conftest", CSIM_CONFTEST)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_handle(lib_path: Path, csim) -> ctypes.CDLL:
    # dlopen resolves a bare relative filename against the system library
    # search path, not the current directory -- an absolute path is what
    # every caller (merge_gate.sh, a shell one-liner, a test) actually means.
    handle = ctypes.CDLL(str(Path(lib_path).resolve()))
    csim._configure_common(handle)
    return handle


def parse_features(spec: str | None) -> list[int]:
    if not spec:
        return []
    return [int(tok) for tok in spec.split(",") if tok.strip() != ""]


def run_trace(handle: ctypes.CDLL, *, seed: int, regions: int, ticks: int,
              features: list[int]) -> tuple[list[tuple[int, int]], int]:
    """([(tick, checksum), ...] at every cadence tick, final_checksum) from a
    freshly built world -- the caller decides what to do with them (print,
    or compare against a second handle's own trace)."""
    w = handle.om_world_new(ctypes.c_uint32(regions), ctypes.c_uint64(seed))
    assert w, "om_world_new returned NULL"
    try:
        for feat in features:
            handle.om_world_set_feature(w, ctypes.c_int(feat), ctypes.c_int(1))
        cadence = handle.om_checksum_cadence()
        if cadence <= 0:
            cadence = ticks + 1  # never fires on its own; the final line still does
        rows: list[tuple[int, int]] = []
        for t in range(1, ticks + 1):
            handle.om_world_step(w)
            if t % cadence == 0:
                rows.append((t, handle.om_world_get_state_checksum(w)))
        final = handle.om_world_get_state_checksum(w)
        return rows, final
    finally:
        handle.om_world_free(w)


def cmd_run(args: argparse.Namespace) -> int:
    csim = load_csim_conftest()
    handle = load_handle(Path(args.lib), csim)
    version = handle.om_abi_version()
    print(f"# lib={args.lib} abi={version} seed={args.seed} regions={args.regions} ticks={args.ticks}")
    features = parse_features(args.features)
    rows, final = run_trace(handle, seed=args.seed, regions=args.regions, ticks=args.ticks, features=features)
    for tick, checksum in rows:
        print(f"tick {tick} {checksum}")
    print(f"final {final}")
    return 0


def parse_trace_output(text: str) -> tuple[list[tuple[int, int]], int | None]:
    """([(tick, checksum), ...], final_checksum) from `cmd_run`'s stdout (or
    a file it was redirected to). `#`-prefixed header lines are ignored."""
    rows: list[tuple[int, int]] = []
    final = None
    for line in text.splitlines():
        m = _TICK_RE.match(line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2))))
            continue
        m = _FINAL_RE.match(line)
        if m:
            final = int(m.group(1))
    return rows, final


def compare_traces(text_a: str, text_b: str) -> tuple[bool, str]:
    """(equal, detail). Compares tick-by-tick checksums and the final
    checksum; the first divergence (or a length mismatch) is named."""
    rows_a, final_a = parse_trace_output(text_a)
    rows_b, final_b = parse_trace_output(text_b)

    if len(rows_a) != len(rows_b):
        return False, f"different number of cadence rows: {len(rows_a)} vs {len(rows_b)}"
    for (tick_a, cs_a), (tick_b, cs_b) in zip(rows_a, rows_b):
        if tick_a != tick_b:
            return False, f"tick sequence diverged: {tick_a} vs {tick_b}"
        if cs_a != cs_b:
            return False, f"checksum diverged at tick {tick_a}: {cs_a} vs {cs_b}"
    if final_a != final_b:
        return False, f"final checksum diverged: {final_a} vs {final_b}"
    if final_a is None:
        return False, "no final checksum line found in one or both traces"
    return True, f"IDENTICAL ({len(rows_a)} cadence rows, final={final_a})"


def cmd_compare(args: argparse.Namespace) -> int:
    text_a = Path(args.file_a).read_text()
    text_b = Path(args.file_b).read_text()
    equal, detail = compare_traces(text_a, text_b)
    print(("MATCH " if equal else "DIVERGE ") + detail)
    return 0 if equal else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")

    run = sub.add_parser("run", help="default when --lib is given directly")
    run.add_argument("--lib", required=True)
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--regions", type=int, required=True)
    run.add_argument("--ticks", type=int, required=True)
    run.add_argument("--features", default=None, help="comma-separated om_feature ints to enable")

    cmp_p = sub.add_parser("compare")
    cmp_p.add_argument("file_a")
    cmp_p.add_argument("file_b")

    # Flat form (no subcommand) mirrors the item's own usage line:
    # `checksum_trace.py --lib path --seed N --regions R --ticks T`, and
    # `checksum_trace.py --compare fileA fileB`.
    ap.add_argument("--lib", dest="flat_lib", default=None)
    ap.add_argument("--seed", dest="flat_seed", type=int, default=None)
    ap.add_argument("--regions", dest="flat_regions", type=int, default=None)
    ap.add_argument("--ticks", dest="flat_ticks", type=int, default=None)
    ap.add_argument("--features", dest="flat_features", default=None)
    ap.add_argument("--compare", dest="flat_compare", nargs=2, default=None, metavar=("FILE_A", "FILE_B"))

    args = ap.parse_args(argv)

    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    if args.flat_compare is not None:
        args.file_a, args.file_b = args.flat_compare
        return cmd_compare(args)
    if args.flat_lib is not None:
        args.lib, args.seed = args.flat_lib, args.flat_seed
        args.regions, args.ticks, args.features = args.flat_regions, args.flat_ticks, args.flat_features
        return cmd_run(args)

    ap.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
