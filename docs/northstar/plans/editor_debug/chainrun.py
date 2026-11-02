#!/usr/bin/env python3
"""Walk privacy -> menu -> galaxy -> mission -> Deploy -> tactical like a real player
(no galaxy 'step 10' shortcut), capture console, print distinct ERROR signatures.
usage: chainrun.py <worktree> <run-name> [--soak S] [--step10]"""
import re, sys, time, collections
from pathlib import Path
wt = Path(sys.argv[1]).resolve()
name = sys.argv[2]
soak = float(sys.argv[sys.argv.index("--soak") + 1]) if "--soak" in sys.argv else 10.0
step10 = "--step10" in sys.argv
sys.path.insert(0, str(wt / "tests/qa/desktop"))
from daemon_client import GodotGame, pick_free_port, find_control, control_center, wait_for, control_names

OUT = Path(__file__).parent / "runs"
OUT.mkdir(exist_ok=True)
S = {"priv": "privacy_modal", "menu": "main_menu", "gal": "galaxy_view",
     "brief": "mission_briefing", "tac": "tactical_view"}

import os, daemon_client as dc
real = "--real" in sys.argv
if real:
    _ge = dc.godot_env
    def _env(base, scratch, save_dir):
        e = _ge(base, scratch, save_dir)
        for v in ("DISPLAY","WAYLAND_DISPLAY","XAUTHORITY","XDG_RUNTIME_DIR"):
            if v in os.environ: e[v] = os.environ[v]
        e.pop("LIBGL_ALWAYS_SOFTWARE", None); e.pop("GALLIUM_DRIVER", None)
        e["OM_GODOT_GUI"] = "1"
        return e
    dc.godot_env = _env
    dc.find_godot = lambda: os.path.expanduser("~/.local/bin/godot.real")
g = GodotGame(pick_free_port(), seed=1, renderer="forward_plus" if real else None)
if real:
    g.godot_args = lambda godot="godot": [godot, "--path", str(dc.REPO_ROOT), "--display-driver", "wayland", "--rendering-driver", "vulkan", "--resolution", "1919x1080", "--", "--qa-port", str(g.qa_port), "--seed", "1"]
g.start()
stage = "launch"
try:
    g.wait_for_port(60)
    c = g.client
    def scene(): return c.state()["result"].get("scene", "")
    def click(ctrl):
        ctl = find_control(c.tree(), ctrl)
        assert ctl, "no control %s among %r" % (ctrl, control_names(c.tree()))
        c.click(*control_center(ctl))
    def shoot(n): c.screenshot("%s_%s" % (name, n))
    stage = "privacy/menu"
    t = time.monotonic() + 45; done = False
    while time.monotonic() < t:
        s = scene()
        if S["menu"] in s: break
        if S["priv"] in s and not done and find_control(c.tree(), "AcceptButton"):
            click("AcceptButton"); done = True
        time.sleep(0.5)
    assert S["menu"] in scene(), "never reached menu, at %r" % scene()
    shoot("1_menu")
    stage = "new game"; click("NewGame")
    wait_for(c, lambda s: S["gal"] in s.get("scene", ""), 15, label="galaxy"); shoot("2_galaxy")
    if step10:
        c.call("step", 10); time.sleep(1)
    stage = "mission"; click("Mission")
    wait_for(c, lambda s: S["brief"] in s.get("scene", ""), 15, label="briefing"); shoot("3_brief")
    time.sleep(1)
    stage = "deploy"; click("Deploy")
    wait_for(c, lambda s: S["tac"] in s.get("scene", ""), 15, label="tactical")
    stage = "soak"; time.sleep(soak); shoot("4_tactical")
    print("WALK OK (reached tactical, soaked %ss)" % soak)
except BaseException as e:
    print("WALK STOPPED at stage %r: %s: %s" % (stage, type(e).__name__, str(e)[:300]))
finally:
    g.stop()
    log = (g.out_dir / "stderr.log").read_text(errors="replace") + "\n" + (g.out_dir / "stdout.log").read_text(errors="replace")
    (OUT / (name + ".log")).write_text(log)
    for p in (g.user_dir / "qa").glob("%s_*.png" % name):
        (OUT / p.name).write_bytes(p.read_bytes())
    sigs = collections.OrderedDict()
    lines = log.splitlines()
    for i, l in enumerate(lines):
        if re.search(r"(SCRIPT )?ERROR:", l):
            at = next((x.strip() for x in lines[i+1:i+3] if x.strip().startswith("at:")), "")
            k = (l.strip()[:200], at)
            sigs[k] = sigs.get(k, 0) + 1
    print("distinct error signatures: %d (total lines %d)  log: %s" % (len(sigs), sum(sigs.values()), OUT / (name + ".log")))
    for (m, at), n in list(sigs.items())[:15]:
        print("  x%d %s %s" % (n, m, at))
    for l in lines:
        if "DBG-" in l: print(l)
