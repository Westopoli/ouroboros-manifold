import glob, json, os, re, shutil, subprocess, sys, time

SCRATCH = "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/e5a6ed2f-9b6f-4836-ba20-e13fc9129eef/scratchpad/splice"
SKELETON = os.path.join(SCRATCH, "skeleton")
WORK = os.path.join(SCRATCH, "e4work")
PY = "/home/westopoli/Projects/agora/.venv/bin/python"

RUN_DIRS = sorted(
    glob.glob(os.path.expanduser("~/Projects/agora/runs/_archive_202b2_pre_gemini_switch/*/"))
    + glob.glob(os.path.expanduser("~/Projects/agora/runs/_archive_202b2_pre_timeout_fix/*/"))
    + glob.glob(os.path.expanduser("~/Projects/agora/runs/202b2-e05-faction-budget-2026*/"))
)

STUB = """void om_faction_step_budget(om_world *w) {
    /* STUB: implemented by card 202b2 */
    (void)w;
}
"""

FUNC_START_RE = re.compile(r"\bom_faction_step_budget\s*\([^;{}]*\)\s*\{")


def extract_function(text):
    """Find 'om_faction_step_budget(...) {' then match braces to the closing one.
    Returns the full function text (from return-type token before the name, best
    effort: we just start at the first line that begins the signature) or None."""
    m = FUNC_START_RE.search(text)
    if not m:
        return None
    # walk back to start of line containing the return type (e.g. "void ")
    line_start = text.rfind("\n", 0, m.start()) + 1
    brace_start = text.index("{", m.start())
    depth = 0
    i = brace_start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[line_start:i + 1] + "\n"
        i += 1
    return None  # unbalanced


def load_candidates(run_dir):
    path = os.path.join(run_dir, "candidates.jsonl")
    rows = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows[d.get("n")] = d
    return rows


def main():
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    os.makedirs(WORK)

    results = []
    for run_dir in RUN_DIRS:
        run_name = os.path.basename(run_dir.rstrip("/"))
        cands = load_candidates(run_dir)
        reply_files = sorted(
            glob.glob(os.path.join(run_dir, "reply-*.md")),
            key=lambda p: int(re.search(r"reply-(\d+)\.md", p).group(1)),
        )
        for rf in reply_files:
            n = int(re.search(r"reply-(\d+)\.md", rf).group(1))
            cand = cands.get(n, {})
            model = cand.get("model", "?")
            reason = cand.get("reason", "?")
            text = open(rf, encoding="utf-8", errors="replace").read()
            func = extract_function(text)
            row = {
                "run": run_name, "n": n, "model": model, "cand_reason": reason,
                "extract": None, "splice_result": None, "detail": "",
            }
            if func is None:
                row["extract"] = "no-function-found"
                results.append(row)
                continue
            row["extract"] = f"ok({len(func.splitlines())} lines)"

            # splice into a fresh skeleton copy
            tree = os.path.join(WORK, f"{run_name}__reply{n}")
            shutil.copytree(SKELETON, tree, ignore=shutil.ignore_patterns("*.so"))
            fpath = os.path.join(tree, "csrc", "faction.c")
            src = open(fpath).read()
            if STUB not in src:
                row["splice_result"] = "stub-not-found"
                results.append(row)
                shutil.rmtree(tree, ignore_errors=True)
                continue
            spliced = src.replace(STUB, func)
            open(fpath, "w").write(spliced)

            # build
            for so in ("libouroboros.so", "libouroboros_dbg.so"):
                p = os.path.join(tree, so)
                if os.path.exists(p):
                    os.remove(p)
            r = subprocess.run(
                ["make", "-s", "libouroboros.so", "libouroboros_dbg.so"],
                cwd=tree, capture_output=True, text=True, timeout=60,
            )
            if r.returncode != 0:
                row["splice_result"] = "compile-error"
                row["detail"] = (r.stderr or r.stdout)[-800:]
                results.append(row)
                shutil.rmtree(tree, ignore_errors=True)
                continue

            # run acceptance
            try:
                r = subprocess.run(
                    [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/csim/test_E05_S033_territory_pays_or_costs.py::test_R_033_01_budget_66_8_40_8"],
                    cwd=tree, capture_output=True, text=True, timeout=60,
                )
            except subprocess.TimeoutExpired:
                row["splice_result"] = "timeout"
                results.append(row)
                shutil.rmtree(tree, ignore_errors=True)
                continue
            out = r.stdout + r.stderr
            if "1 passed" in out:
                row["splice_result"] = "PASS"
            elif "1 failed" in out or "failed" in out:
                row["splice_result"] = "fail"
                m = re.search(r"^>\s+assert[^\n]*\n(?:E[^\n]*\n)*", out, re.M)
                if m:
                    obtained = re.search(r"Obtained:\s*([^\n]*)", out)
                    row["detail"] = m.group(0).strip().replace("\n", " | ")[:160]
                    if obtained:
                        row["detail"] += f" || Obtained: {obtained.group(1)}"
                else:
                    row["detail"] = out[-300:]
            elif "error" in out.lower():
                row["splice_result"] = "error"
                row["detail"] = out[-500:]
            else:
                row["splice_result"] = "unknown"
                row["detail"] = out[-500:]
            results.append(row)
            shutil.rmtree(tree, ignore_errors=True)

    # print table
    print(f"{'run':<45} {'n':>3} {'model':<20} {'cand_reason':<15} {'extract':<20} {'splice_result':<15} detail")
    for row in results:
        print(f"{row['run']:<45} {row['n']:>3} {row['model']:<20} {row['cand_reason']:<15} {row['extract']:<20} {row['splice_result'] or '':<15} {row['detail'][:120]}")

    n_total = len(results)
    n_extracted = sum(1 for r in results if r["extract"] and r["extract"].startswith("ok"))
    n_pass = sum(1 for r in results if r["splice_result"] == "PASS")
    n_fail = sum(1 for r in results if r["splice_result"] == "fail")
    n_compile_err = sum(1 for r in results if r["splice_result"] == "compile-error")
    print(f"\nTOTAL replies: {n_total}")
    print(f"function extracted: {n_extracted}")
    print(f"function-level splice PASS: {n_pass}")
    print(f"function-level splice fail (test assertion): {n_fail}")
    print(f"function-level splice compile-error: {n_compile_err}")

    json.dump(results, open(os.path.join(SCRATCH, "e4_results.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
