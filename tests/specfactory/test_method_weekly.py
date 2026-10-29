# spec: docs/northstar/plans/method_rev3_2026-10-26/spec.md "Design" (weekly run without a chat), HARNESS-mm-4 and mm-6
"""method_weekly.sh --dry-run prints the commands it would run and runs none; the systemd units parse; the
SessionStart hook line for `method_metrics.py --last` is in .claude/settings.json (mm-6).

Interfaces fixed here (the spec leaves them open): --dry-run prints one `+ <command>` line per command, in order:
wt.py new, git fetch, method_metrics.py --week <last ISO week> --write, git commit, flock on records.lock then git
push, wt.py done; a dry run creates nothing under ~/Projects/om-push/wt/.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SF = REPO / "scripts" / "specfactory"
SCRIPT = SF / "method_weekly.sh"
UNITS = SF / "systemd"


def _dry():
    assert SCRIPT.exists(), f"{SCRIPT.relative_to(REPO)} does not exist"
    return subprocess.run(["bash", str(SCRIPT), "--dry-run"], capture_output=True, text=True, timeout=60)


def test_4_dry_run_prints_the_commands_in_order_and_runs_none():
    wt_before = set(p.name for p in (Path.home() / "Projects/om-push/wt").iterdir())
    r = _dry()
    assert r.returncode == 0, r.stdout + r.stderr
    cmds = [ln[2:] for ln in r.stdout.splitlines() if ln.startswith("+ ")]
    want = [r"wt\.py new", r"git .*fetch", r"method_metrics\.py --week \d{4}-W\d\d .*--write", r"git .*commit",
            r"flock .*records\.lock .*git .*push", r"wt\.py done"]
    pos = -1
    for pat in want:
        hit = next((i for i, c in enumerate(cmds) if i > pos and re.search(pat, c)), None)
        assert hit is not None, f"no command matching {pat!r} after position {pos} in {cmds}"
        pos = hit
    assert set(p.name for p in (Path.home() / "Projects/om-push/wt").iterdir()) == wt_before, "dry run made a tree"


def test_4_service_and_timer_files_exist_and_name_the_script():
    svc, tim = UNITS / "om-method-metrics.service", UNITS / "om-method-metrics.timer"
    assert svc.is_file() and tim.is_file(), "unit files missing"
    assert "method_weekly.sh" in svc.read_text() and "ExecStart=" in svc.read_text()
    assert "OnCalendar=Sun 23:00" in tim.read_text() and "[Install]" in tim.read_text()


def test_4_units_verify_with_systemd_analyze_when_present(tmp_path):
    svc, tim = UNITS / "om-method-metrics.service", UNITS / "om-method-metrics.timer"
    assert svc.is_file() and tim.is_file(), "unit files missing"
    if not shutil.which("systemd-analyze"):
        return  # the text check above is the fallback
    r = subprocess.run(["systemd-analyze", "verify", "--user", str(tim)], capture_output=True, text=True, timeout=60)
    assert "OnCalendar" not in r.stderr and "Failed to parse" not in r.stderr, r.stderr


def test_6_settings_has_the_session_start_hook_line_for_metrics_last():
    s = json.loads((REPO / ".claude/settings.json").read_text())
    cmds = [h.get("command", "") for g in s.get("hooks", {}).get("SessionStart", []) for h in g.get("hooks", [])]
    assert any("method_metrics.py --last" in c for c in cmds), cmds
    mc = next(i for i, c in enumerate(cmds) if "method_check.py" in c)
    mm = next(i for i, c in enumerate(cmds) if "method_metrics.py --last" in c)
    assert mm > mc or mm == mc, "metrics --last must come after method_check.py"


# spec: Amendment A12 (HARNESS-mm-15): the week, the exit, the reap
def _week_in_dry_run(now):
    r = subprocess.run(["bash", str(SCRIPT), "--dry-run"], capture_output=True, text=True, timeout=60,
                       env={**os.environ, "OM_NOW": now})
    assert r.returncode == 0, r.stdout + r.stderr
    m = re.search(r"method_metrics\.py --week (\d{4}-W\d\d)", r.stdout)
    assert m, r.stdout
    return m.group(1)


def test_a12_dry_run_names_the_week_ending_on_a_sunday_and_the_last_week_on_a_wednesday():
    assert _week_in_dry_run("2026-11-01 23:00") == "2026-W44"  # Sunday: the week that ends today
    assert _week_in_dry_run("2026-10-28 12:00") == "2026-W43"  # Wednesday: the week that ended last Sunday


def _live_run(tmp_path, now):
    home = tmp_path / "home"
    for week in ("W43", "W44"):  # the pre-fix script names W43; the fixed one W44
        w = home / f"Projects/om-push/wt/metrics-2026-{week}"
        (w / "scripts/specfactory").mkdir(parents=True)
        (w / "scripts/specfactory/method_metrics.py").write_text("import sys\nprint('FAIL M01')\nsys.exit(1)\n")
    wt = home / "Projects/om-push/wt/metrics-2026-W44"
    live = tmp_path / "live"
    (live / "scripts/specfactory").mkdir(parents=True)
    log = tmp_path / "calls.log"
    (live / "scripts/specfactory/wt.py").write_text(
        f"import sys\nopen({str(log)!r}, 'a').write('wt.py ' + ' '.join(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[1] == 'reap':\n    print('reap dry output')\n")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    for name in ("git", "flock"):
        (bin_ / name).write_text(f"#!/bin/sh\necho \"{name} $*\" >> {log}\n"
                                 "case \"$*\" in *rev-parse*) echo abc123;; esac\nexit 0\n")
        (bin_ / name).chmod(0o755)
    env = {**os.environ, "HOME": str(home), "OM_REPO": str(live), "OM_NOW": now, "PATH": f"{bin_}:{os.environ['PATH']}"}
    r = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, timeout=60, env=env)
    return r, log.read_text() if log.exists() else "", wt


def test_a12_a_fail_from_the_metrics_still_reaches_the_commit_line(tmp_path):
    r, calls, _ = _live_run(tmp_path, "2026-11-01 23:00")
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"git .*commit", calls), calls


def test_a12_reap_runs_dry_only_and_the_output_goes_into_the_weeks_commit(tmp_path):
    r, calls, wt = _live_run(tmp_path, "2026-11-01 23:00")
    reaps = [ln for ln in calls.splitlines() if ln.startswith("wt.py reap")]
    assert reaps and all("--dry-run" in ln for ln in reaps), calls
    assert (wt / "metrics/2026-W44_reap_dryrun.txt").read_text().strip() == "reap dry output"
    for ln in SCRIPT.read_text().splitlines():
        if re.search(r"wt\.py\"? reap", ln) and not ln.lstrip().startswith("#"):
            assert "--dry-run" in ln, ln
