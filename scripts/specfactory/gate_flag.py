#!/usr/bin/env python3
"""HARNESS-gate-flag (layered gate spec, layer 1): the per-piece `impact` flag and its verdict.

  gate_flag.py story-impact <story.md>      (H-006: the flag the gate reads)
  gate_flag.py impact <pieces.toml> <id>[,<id>...] [--require-key]
      prints the strictest flag of the listed rows (contract > sim > client > harness; a row without the key is sim);
      exit 2 on a value outside the four; with --require-key exit 3 when a listed row has no key (still prints it).
  gate_flag.py verdict <candidate> <base_ref> <impact> --merge-root <dir> --lib <path>
      runs checksum_trace.py and tactical_trace.py on the candidate's library, compares them with the base's pair
      (<merge_root>/trace_cache/<csrc tree>-<Makefile blob>.{strategic,tactical}.txt, built once in a throwaway worktree
      on a miss) and prints `flag <impact> traces <same|differ|skipped> footprint <ok|path> <OK|REJECT> <reason>`;
      exit 0 OK, 1 REJECT.

merge_gate.sh runs the stage `flag` right after `make` and picks the fast tier's suites from the flag.
See also: docs/northstar/plans/2026-10-29-layered-gate-spec.md (section 2 layer 1, the HARNESS-gate-flag paragraph,
sections 8 F4 to F6, N17), tests/specfactory/test_gate_flag.py.
"""
from __future__ import annotations

import argparse
import ctypes
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import merge_gate_support as msp

HERE = Path(__file__).resolve().parent
CHECKSUM_TRACE = HERE / "checksum_trace.py"
TACTICAL_TRACE = HERE / "tactical_trace.py"
STRICTNESS = ("harness", "client", "sim", "contract")
FOOTPRINT = {"harness": ("csrc/", "autoload/", "scenes/", "project.godot"), "client": ("csrc/",)}
PIN_FILES = ("csrc/ouroboros_sim.h", "docs/northstar/spec_factory/signatures.toml", "csrc/om_internal.h",
             "csrc/pipe/pipe_internal.h", "docs/architecture.md")
TRACES = (("strategic", CHECKSUM_TRACE, ["--seed", "1", "--regions", "60", "--ticks", "500", "--features", "6"]),
          ("tactical", TACTICAL_TRACE, ["--seed", "1", "--ticks", "1500"]))
TOOL_TIMEOUT_S = 600
MAKE_TIMEOUT_S = 300


class TraceFailed(Exception):
    pass


def cmd_impact(args) -> int:
    pieces = msp._load_pieces(Path(args.pieces))
    flags, missing = [], False
    for pid in args.ids.split(","):
        row = pieces.get(msp.resolve_piece_id(pid, pieces), {})
        flag = row.get("impact")
        if flag is None:
            missing = True
            flag = "sim"
        if flag not in STRICTNESS:
            print(f"gate_flag: {pid}: impact {flag!r} is not one of {', '.join(STRICTNESS)}", file=sys.stderr)
            return 2
        flags.append(flag)
    print(max(flags, key=STRICTNESS.index))
    return 3 if missing and args.require_key else 0


def cmd_story_impact(args) -> int:
    """H-006: the flag of a story file (`sim` when the line is absent); rc 2 outside the four."""
    flag = msp.story_flag(Path(args.story))
    if flag not in STRICTNESS:
        print(f"gate_flag: {args.story}: Flag {flag!r} is not one of {', '.join(STRICTNESS)}", file=sys.stderr)
        return 2
    print(flag)
    return 0


def _rev(cwd: str, rev: str) -> str:
    r = subprocess.run(["git", "rev-parse", "--verify", "-q", rev], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() or "none"


def _key(cwd: str, ref: str) -> str:
    return f"{_rev(cwd, ref + ':csrc')}-{_rev(cwd, ref + ':Makefile')}"


def _has_checksum_entry(lib: Path) -> bool:
    try:
        return hasattr(ctypes.CDLL(str(Path(lib).resolve())), "om_world_checksum_full")
    except OSError:
        return True  # the trace tool reports an unloadable library as its own failure


def _run_traces(lib: Path) -> dict[str, str]:
    out = {}
    for name, tool, args in TRACES:
        r = subprocess.run([sys.executable, str(tool), "--lib", str(lib), *args], capture_output=True, text=True,
                           timeout=TOOL_TIMEOUT_S)
        if r.returncode != 0:
            print(r.stderr[-600:], file=sys.stderr)
            raise TraceFailed(f"trace failed {tool.name} rc {r.returncode}")
        out[name] = r.stdout
    return out


def _build_base(cwd: str, base_ref: str, scratch: Path) -> dict[str, str] | None:
    """The base's trace pair from a throwaway worktree; None when it has no checksum entry point."""
    wt = Path(tempfile.mkdtemp(prefix="flagbase-", dir=scratch))
    subprocess.run(["git", "worktree", "add", "--detach", str(wt), base_ref], cwd=cwd, capture_output=True, check=True)
    try:
        opt = ["OPT=-O2", "WERROR=1"] if "$(OPT)" in (wt / "Makefile").read_text() else []
        r = subprocess.run(["make", "-s", "-C", str(wt), *opt, "libouroboros.so"], capture_output=True, text=True,
                           timeout=MAKE_TIMEOUT_S)
        if r.returncode != 0:
            print(r.stdout[-600:] + r.stderr[-600:], file=sys.stderr)
            sha = _rev(cwd, base_ref + "^{commit}")
            raise TraceFailed(f"base unbuildable {sha}")
        lib = wt / "libouroboros.so"
        return _run_traces(lib) if _has_checksum_entry(lib) else None
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=cwd, capture_output=True)


def _differences(pair_a: dict[str, str], pair_b: dict[str, str], scratch: Path) -> list[str]:
    found = []
    for name, tool, _ in TRACES:
        fa, fb = scratch / f"a.{name}.txt", scratch / f"b.{name}.txt"
        fa.write_text(pair_a[name])
        fb.write_text(pair_b[name])
        r = subprocess.run([sys.executable, str(tool), "--compare", str(fa), str(fb)], capture_output=True, text=True)
        if r.returncode != 0:
            found.append(f"{name}: {r.stdout.strip()}")
    return found


def verdict(candidate: str, base_ref: str, impact: str, merge_root: Path, lib: Path) -> tuple[bool, str]:
    def line(traces: str, footprint: str, ok: bool, reason: str) -> tuple[bool, str]:
        return ok, f"flag {impact} traces {traces} footprint {footprint} {'OK' if ok else 'REJECT'} {reason}"

    changed = msp.changed_files(Path(candidate), base_ref)
    offending = next((p for p in changed if p.startswith(FOOTPRINT.get(impact, ()))), None)
    if offending:
        return line("skipped", offending, False, f"{impact} flag with a change under its footprint")
    if impact == "contract" and not set(changed) & set(PIN_FILES):
        return line("skipped", "ok", False, "contract flag without a contract change")
    if not _has_checksum_entry(lib):
        reason = "cannot verify flag: checksum entry point missing"
        if impact in FOOTPRINT:
            return line("skipped", "ok", False, reason)
        return line("differ", "ok", True, f"WARN {reason}")

    cache = Path(merge_root) / "trace_cache"
    cache.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="flagscratch-"))
    try:
        cand = _run_traces(lib)
        bkey = _key(candidate, base_ref)
        names = {n: cache / f"{bkey}.{n}.txt" for n, _, _ in TRACES}
        if all(p.is_file() for p in names.values()):
            base = {n: p.read_text() for n, p in names.items()}
        else:
            base = _build_base(candidate, base_ref, scratch)
            if base is not None:
                for n, p in names.items():
                    p.write_text(base[n])
        for n, _, _ in TRACES:
            (cache / f"{_key(candidate, 'HEAD')}.{n}.txt").write_text(cand[n])
        if base is None:
            reason = "cannot verify flag: checksum entry point missing in the base"
            return line("skipped", "ok", False, reason) if impact in FOOTPRINT else line("differ", "ok", True, f"WARN {reason}")
        found = _differences(cand, base, scratch)
    except TraceFailed as e:
        return line("skipped", "ok", False, str(e))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if not found:
        return line("same", "ok", True, "strategic and tactical traces match the base")
    detail = "; ".join(found)
    if impact in FOOTPRINT:
        return line("differ", "ok", False, f"sim moved under a non-sim flag ({detail})")
    return line("differ", "ok", True, detail)


def cmd_verdict(args) -> int:
    if args.impact not in STRICTNESS:
        print(f"gate_flag: impact {args.impact!r} is not one of {', '.join(STRICTNESS)}", file=sys.stderr)
        return 2
    ok, text = verdict(args.candidate, args.base_ref, args.impact, Path(args.merge_root), Path(args.lib))
    print(text)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    imp = sub.add_parser("impact")
    imp.add_argument("pieces")
    imp.add_argument("ids")
    imp.add_argument("--require-key", action="store_true")
    sti = sub.add_parser("story-impact")
    sti.add_argument("story")
    ver = sub.add_parser("verdict")
    ver.add_argument("candidate")
    ver.add_argument("base_ref")
    ver.add_argument("impact")
    ver.add_argument("--merge-root", required=True)
    ver.add_argument("--lib", required=True)
    args = ap.parse_args(argv)
    return {"impact": cmd_impact, "story-impact": cmd_story_impact}.get(args.cmd, cmd_verdict)(args)


if __name__ == "__main__":
    sys.exit(main())
