#!/usr/bin/env bash
# H-031 piece two: a real capture of the desktop through the xdg-desktop-portal Screenshot method
# (docs/stories/H-031.md, Capture). screen_capture.sh <out.png>
# Prints `CAPTURE portal <out.png>` (preceded by `CAPTURE fraction <f>`) and exits 0; a portal denial prints
# `CAPTURE REJECT portal denied` and exits 2; a flat capture prints `CAPTURE REJECT uniform` and exits 3.
set -uo pipefail
[[ $# -eq 1 ]] || { echo "usage: screen_capture.sh <out.png>" >&2; exit 64; }
exec python3 - "$1" <<'PY'
import re, shutil, subprocess, sys
from urllib.parse import unquote, urlparse
from gi.repository import Gio, GLib
from PIL import Image

out = sys.argv[1]


def reject(why, code):
    print("CAPTURE REJECT " + why)
    sys.exit(code)


# One connection: subscribe to Request.Response first, then call Screenshot("", {"interactive": False}).
try:
    conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    loop, got = GLib.MainLoop(), {}

    def on_response(c, sender, path, iface, signal, params):
        got["code"], results = params.unpack()
        got["uri"] = results.get("uri", "")
        loop.quit()

    conn.signal_subscribe("org.freedesktop.portal.Desktop", "org.freedesktop.portal.Request", "Response",
                          None, None, Gio.DBusSignalFlags.NONE, on_response)
    conn.call_sync("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop",
                   "org.freedesktop.portal.Screenshot", "Screenshot",
                   GLib.Variant("(sa{sv})", ("", {"interactive": GLib.Variant("b", False)})),
                   GLib.VariantType("(o)"), Gio.DBusCallFlags.NONE, 10000, None)
    GLib.timeout_add_seconds(30, loop.quit)
    loop.run()
except GLib.Error as e:
    reject("portal unavailable: " + e.message, 2)
if got.get("code") != 0 or not got.get("uri"):
    reject("portal denied", 2)
shot = unquote(urlparse(got["uri"]).path)  # the file the portal wrote, ~/Pictures/Screenshot-N.png

# Crop to the monitor holding the Godot window when xdotool and xrandr can say which; else the whole desktop.
box = None
try:
    wid = subprocess.run(["xdotool", "search", "--name", "Ouroboros"], capture_output=True, text=True, timeout=10).stdout.split()[0]
    geo = dict(l.split("=") for l in subprocess.run(["xdotool", "getwindowgeometry", "--shell", wid],
                                                    capture_output=True, text=True, timeout=10, check=True).stdout.split())
    wx, wy = int(geo["X"]), int(geo["Y"])
    for m in re.finditer(r"(\d+)/\d+x(\d+)/\d+\+(\d+)\+(\d+)", subprocess.run(
            ["xrandr", "--listmonitors"], capture_output=True, text=True, timeout=10).stdout):
        w, h, x, y = map(int, m.groups())
        if x <= wx < x + w and y <= wy < y + h:
            box = (x, y, x + w, y + h)
except (IndexError, KeyError, ValueError, OSError, subprocess.SubprocessError):
    pass

img = Image.open(shot).convert("RGB")
if box:
    img = img.crop(box)

# The gate's look metric (merge_gate_support.frame_busyness): fraction of pixels differing from the most
# common luminance, 0 = blank. Only 0 rejects; the near-uniform threshold is Westley's and not given (spec G1).
# See also: scripts/specfactory/merge_gate_support.py frame_busyness
lum = img.convert("L")
fraction = 1.0 - max(n for n, _ in lum.getcolors(maxcolors=256)) / (lum.width * lum.height)
if fraction == 0:
    reject("uniform capture (fraction 0)", 3)
if box:
    img.save(out)
else:
    shutil.copyfile(shot, out)
print("CAPTURE fraction %.4f" % fraction)
print("CAPTURE portal " + out)
PY
