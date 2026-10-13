#!/usr/bin/env python3
"""Godot reachability lint: .gd files under scenes/** and autoload/** not reachable from the
main scene or an autoload, read from git refs. Regression mode: only newly unreachable rejects.
Usage: gd_reach_lint.py --ref R --base-ref B --project DIR [--stubs FILE]"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

RES = re.compile(r'res://([^"\'\s)]+)')
EXT_RES = re.compile(r'\[ext_resource[^\]]*?path="res://([^"]+)"')
CLASS = re.compile(r'^\s*class_name\s+(\w+)', re.M)
IDENT = re.compile(r'\b[A-Za-z_]\w*\b')
TEXT_EXT = (".gd", ".tscn", ".tres")


def git(project, *args):
    p = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def unreachable(project, ref, stubs):
    files = set(git(project, "ls-tree", "-r", "--name-only", ref).splitlines())
    cache = {}

    def text(path):
        if path not in cache:
            cache[path] = git(project, "show", f"{ref}:{path}") if path in files else ""
        return cache[path]

    gd = [f for f in files if f.endswith(".gd")]
    classes = {}
    for f in gd:
        m = CLASS.search(text(f))
        if m:
            classes[m.group(1)] = f
    roots = []
    for line in text("project.godot").splitlines():
        m = re.match(r'\s*run/main_scene\s*=\s*"res://([^"]+)"', line)
        if not m:
            m = re.match(r'\s*\w+\s*=\s*"\*?res://([^"]+)"', line) if "autoload" in section(text("project.godot"), line) else None
        if m:
            roots.append(m.group(1))
    seen, todo = set(), list(roots)
    while todo:
        f = todo.pop()
        if f in seen or f not in files:
            continue
        seen.add(f)
        if not f.endswith(TEXT_EXT):
            continue
        body = text(f)
        if f.endswith(".gd"):
            refs = RES.findall(body)  # any res:// literal (router dicts, preload, load, extends)
            refs += [classes[n] for n in set(IDENT.findall(body)) & classes.keys()]
        else:
            refs = EXT_RES.findall(body) + RES.findall(body)
        todo.extend(refs)
    return {f for f in gd if f.startswith(("scenes/", "autoload/")) and f not in seen and f not in stubs}


def section(text, line):
    cur = ""
    for ln in text.splitlines():
        if ln.startswith("["):
            cur = ln.strip()
        if ln is line or ln == line:
            return cur
    return ""


def load_stubs(path):
    if not Path(path).is_file():
        return set()
    out = set()
    for ln in Path(path).read_text().splitlines():
        ln = ln.split("#", 1)[0].strip()
        if ln:
            out.add(ln.removeprefix("res://"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--base-ref", required=True)
    ap.add_argument("--project", required=True)
    ap.add_argument("--stubs")
    a = ap.parse_args()
    stubs = a.stubs or str(Path(a.project) / "scripts/specfactory/gd_reach_stubs.txt")
    if not Path(stubs).is_file():
        stubs = str(Path(__file__).with_name("gd_reach_stubs.txt"))
    ex = load_stubs(stubs)
    head = unreachable(a.project, a.ref, ex)
    base = unreachable(a.project, a.base_ref, ex)
    new = sorted(head - base)
    for f in new:
        print(f"NEW UNREACHABLE {f}")
    for f in sorted(head & base):
        print(f"UNREACHABLE {f}")
    if new:
        print(f"GD REACH LINT FAILED ({len(new)} new unreachable)")
        return 1
    print(f"GD REACH LINT OK ({len(head)} unreachable at HEAD, {len(base)} at base, none new)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
