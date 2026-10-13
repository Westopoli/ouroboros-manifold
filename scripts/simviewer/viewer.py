"""SV-3: the sim viewer's state machine, band table and drawing.

Spec: docs/northstar/plans/2026-10-12-simviewer-spec.md. Tests:
tests/simviewer/test_viewer_headless.py. Tooling only, never in the game loop.
The drawing is a port of simulation/strategic_viewer.py (hulls, edges, nodes,
radar, sparklines, sidebar, log) reading a History instead of a dump.

Two modes. "tick": advance() sends `step n=1`. "mission": advance() walks the phase
machine idle -> started -> debriefed -> idle on the dbg pipe: mission_start (a
`mission` frame), then once a band is picked one objective_complete per objective
plus mission_end (or mission_refuse for pick 5), then jump.

Pick a band: pick_to_inputs(archetype, band) gives the (completion, retention) pair
whose final = 0.75 c + 0.25 r (R-077-01) classifies into that band under the
R-077-02 thresholds of the archetype. The target is the band midpoint m; m >= 0.25
sets retention 1.0 and completion (m - 0.25) / 0.75, else retention 0.0 and
completion m / 0.75.

BAND_THRESHOLDS (R-077-02): archetype id -> (t1, t2, t3, t4); final below t1 is
band 0, below t2 band 1, below t3 band 2, below t4 band 3, else band 4. The values
are the OM_MISSION_BAND_THRESHOLDS_* defines in csrc/om_constants.h, grouped as
om_mission_classify_band (csrc/mission.c) selects them; archetype ids are the
OM_MISSION_ARCH_* defines (csrc/mission.c lines 161-170).
  STANDARD            0.20 0.40 0.60 0.80   ids 0 1 4 6 8 9
  RECONQUEST_ASSAULT  0.25 0.45 0.65 0.82   ids 2 3
  MULTI_FRONT         0.15 0.35 0.55 0.75   id 5
  EVACUATION          0.30 0.50 0.65 0.80   id 7
"""
import math

import pygame

from scripts.simviewer.pipe_session import JUMP_TICKS, PipeError
from scripts.simviewer.history import RING

_STANDARD = (0.20, 0.40, 0.60, 0.80)
_RECONQUEST_ASSAULT = (0.25, 0.45, 0.65, 0.82)
_MULTI_FRONT = (0.15, 0.35, 0.55, 0.75)
_EVACUATION = (0.30, 0.50, 0.65, 0.80)
BAND_THRESHOLDS = {
    0: _STANDARD, 1: _STANDARD, 2: _RECONQUEST_ASSAULT, 3: _RECONQUEST_ASSAULT,
    4: _STANDARD, 5: _MULTI_FRONT, 6: _STANDARD, 7: _EVACUATION, 8: _STANDARD,
    9: _STANDARD,
}

BAND_NAMES = ("total failure", "partial failure", "partial success", "strong success",
              "total success", "refused")
RATES = (1, 2, 5, 10, 20, 50)
PULSE_SECONDS = 2.0
MISSION_PERIOD = 1.0
MAX_STEPS_PER_UPDATE = RATES[-1]

# ---------------------------------------------------------------- layout, colours

W, H = 1280, 720
SIDEBAR_W = 320
CONTROLS_H = 56
LOG_H = 120
MAP_W = W - SIDEBAR_W
MAP_H = H - CONTROLS_H - LOG_H
SIDEBAR_H = H - CONTROLS_H
WORLD = 1000.0

BG_COLOR = (13, 13, 18)
CONTROLS_BG = (22, 22, 30)
SIDEBAR_BG = (18, 18, 26)
BORDER = (45, 45, 60)
LOG_BG = (16, 16, 24)
TEXT = (175, 175, 188)
BRIGHT = (230, 230, 245)
DIM = (90, 90, 105)
SELECTED = (255, 215, 50)
UNOWNED = (70, 70, 85)
EDGE = (55, 55, 72)
RED = (230, 70, 70)
FIELD_COLORS = {
    "military": (100, 160, 255),
    "economy": (80, 210, 120),
    "tension": (220, 80, 80),
    "population": (200, 180, 80),
}
RADAR_ARMS = (("military", 0), ("economy", 90), ("population", 180), ("tension", 270))

NODE_R_MIN = 30
NODE_R_MAX = 60
ZOOM_STEP = 1.15
ZOOM_MIN = 0.1
ZOOM_MAX = 15.0

_fonts = {}


def _font(size):
    if size not in _fonts:
        if not pygame.font.get_init():
            pygame.font.init()
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def _text(surface, text, pos, color=TEXT, size=17):
    surface.blit(_font(size).render(text, True, color), pos)


def faction_color(fid, factions):
    if fid not in factions:
        return UNOWNED
    hue = (fid * 0.381966) % 1.0
    c = pygame.Color(0)
    c.hsva = (hue * 360, 65, 90, 100)
    return (c.r, c.g, c.b)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- pick -> inputs

def pick_to_inputs(archetype, band):
    t = BAND_THRESHOLDS.get(archetype, _STANDARD)
    edges = (0.0,) + tuple(t) + (1.0,)
    m = (edges[band] + edges[band + 1]) / 2
    if m >= 0.25:
        return (m - 0.25) / 0.75, 1.0
    return m / 0.75, 0.0


# ---------------------------------------------------------------- state

class ViewerState:
    def __init__(self, history, session=None):
        self.history = history
        self.session = session
        self.mode = "tick"
        self.rate = 5
        self.paused = True
        self.pick = None
        self.phase = "idle"
        self.status = ""
        self.mismatch = False
        self.selected_region = None
        self.pulse = {}
        self.last_debrief = None
        self.player_faction = 0
        self.picked = []
        self.n_objectives = 1
        self.archetype = 0
        self.mission_region = None
        self.radar = True
        self.faction_view = False
        self.tracked_faction = None
        self.cam = None
        self._acc = 0.0
        self._panning = False
        self._drag_moved = False
        self._pan_last = (0, 0)

    # frames

    def apply(self, frame):
        if frame.get("type") == "snapshot":
            self.player_faction = frame.get("player_faction", 0)
        self.history.apply(frame)

    def _send(self, name, **fields):
        frames = self.session.send(name, **fields)
        for fr in frames:
            self.apply(fr)
        return frames

    def _pulse_diff(self, before, seconds):
        for rid in self.history.diff(before, self.history.regions):
            self.pulse[rid] = seconds

    def _snapshot_regions(self):
        return {i: dict(r) for i, r in self.history.regions.items()}

    # controls

    def toggle_mode(self):
        self.mode = "mission" if self.mode == "tick" else "tick"

    def toggle_pause(self):
        self.paused = not self.paused

    def rate_up(self):
        self.rate = RATES[min(RATES.index(self.rate) + 1, len(RATES) - 1)]

    def rate_down(self):
        self.rate = RATES[max(RATES.index(self.rate) - 1, 0)]

    def set_pick(self, band):
        self.pick = band

    def handle_key(self, key):
        if key == pygame.K_SPACE:
            self.toggle_pause()
        elif key == pygame.K_RIGHTBRACKET:
            self.rate_up()
        elif key == pygame.K_LEFTBRACKET:
            self.rate_down()
        elif key == pygame.K_RIGHT:
            self._step()
        elif key == pygame.K_m:
            self.toggle_mode()
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            self.set_pick(key - pygame.K_1)
        elif key == pygame.K_0:
            self.set_pick(5)
        elif key == pygame.K_RETURN:
            if self.mode == "mission":
                self.advance()
        elif key == pygame.K_f:
            self.faction_view = not self.faction_view
            owner = self.history.regions.get(self.selected_region, {}).get("owner")
            if self.faction_view and owner in self.history.factions:
                self.tracked_faction = owner
        elif key == pygame.K_TAB:
            ids = sorted(self.history.factions)
            if ids:
                i = ids.index(self.tracked_faction) if self.tracked_faction in ids else -1
                self.tracked_faction = ids[(i + 1) % len(ids)]
        elif key == pygame.K_v:
            self.radar = not self.radar
        elif key == pygame.K_r:
            self.cam = None

    # time

    def update(self, dt):
        self.pulse = {r: s - dt for r, s in self.pulse.items() if s - dt > 0}
        if self.paused:
            return
        if self.mode == "mission":
            self._acc += dt
            if self._acc >= MISSION_PERIOD:
                self._acc -= MISSION_PERIOD
                self.advance()
            return
        self._acc += dt * self.rate
        n = int(self._acc)
        self._acc -= n
        for _ in range(min(n, MAX_STEPS_PER_UPDATE)):
            self._step()

    def advance(self):
        if self.session is None:
            self.status = "no pipe session"
        elif self.mode == "tick":
            self._step()
        else:
            try:
                self._mission_advance()
            except PipeError as e:
                self.status = "%s: %s" % (e.frame.get("name", "error"), e.frame.get("reason"))

    def _step(self):
        if self.session is None:
            return
        try:
            frames = self._send("step", n=1)
        except PipeError as e:
            self.status = "%s: %s" % (e.frame.get("name", "error"), e.frame.get("reason"))
            return
        for fr in frames:
            for ev in fr.get("events", []):
                self.pulse[ev["region"]] = 1.0
        self.status = ""

    def _mission_advance(self):
        if self.phase == "idle":
            frames = self._send("mission_start", faction=self.player_faction, era_kind=0)
            m = frames[0]
            self.archetype = m["archetype"]
            self.n_objectives = max(1, len(m.get("objectives", [])))
            self.mission_region = m["region"]
            self.selected_region = m["region"]
            self.pulse[m["region"]] = PULSE_SECONDS
            self.last_debrief = None
            self.mismatch = False
            self.phase = "started"
            self.status = "mission started: pick a band (1-5, 0 refuse), RETURN to resolve"
        elif self.phase == "started":
            if self.pick is None:
                self.status = "pick a band first (1-5, 0 refuse)"
                return
            before = self._snapshot_regions()
            if self.pick == 5:
                frames = self._send("mission_refuse")
            else:
                c, r = pick_to_inputs(self.archetype, self.pick)
                for i in range(self.n_objectives):
                    self._send("objective_complete", objective=i, completion=c)
                frames = self._send("mission_end", retention=r)
            self.last_debrief = frames[0]
            self.mismatch = self.last_debrief["band"] != self.pick
            self.picked.append(self.pick)
            self._pulse_diff(before, PULSE_SECONDS)
            self.pulse[self.mission_region] = PULSE_SECONDS
            self.phase = "debriefed"
            self.status = "debrief: RETURN jumps %d ticks" % JUMP_TICKS
        else:
            before = self._snapshot_regions()
            self._send("jump", ticks=JUMP_TICKS)
            self._pulse_diff(before, 1.0)
            self.phase = "idle"
            self.pick = None
            self.status = "jumped: RETURN starts the next mission"

    # camera and mouse

    def camera(self):
        if self.cam is not None:
            return self.cam
        layout = self.history.layout()
        if not layout:
            return (WORLD / 2, WORLD / 2, 0.5)
        xs = [p[0] * WORLD for p in layout.values()]
        ys = [p[1] * WORLD for p in layout.values()]
        zoom = 0.9 * min(MAP_W / max(max(xs) - min(xs), 1.0), MAP_H / max(max(ys) - min(ys), 1.0))
        return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, zoom

    def mouse_down(self, pos, button):
        if button == 1 and pos[0] < MAP_W and pos[1] < MAP_H:
            self._panning = True
            self._drag_moved = False
            self._pan_last = pos
        elif button == 3:
            self.selected_region = None

    def mouse_move(self, pos):
        if not self._panning:
            return
        dx, dy = pos[0] - self._pan_last[0], pos[1] - self._pan_last[1]
        if abs(dx) > 2 or abs(dy) > 2:
            self._drag_moved = True
        cx, cy, zoom = self.camera()
        self.cam = (cx - dx / zoom, cy - dy / zoom, zoom)
        self._pan_last = pos

    def mouse_up(self, pos, button):
        if button != 1:
            return
        if self._panning and not self._drag_moved and pos[0] < MAP_W and pos[1] < MAP_H:
            self.selected_region = pick_region(self.history, self.camera(), pos)
        self._panning = False

    def wheel(self, pos, dy):
        if pos[0] >= MAP_W or pos[1] >= MAP_H:
            return
        cx, cy, zoom = self.camera()
        wx, wy = screen_to_world(pos, (cx, cy, zoom))
        new = max(ZOOM_MIN, min(ZOOM_MAX, zoom * (ZOOM_STEP if dy > 0 else 1.0 / ZOOM_STEP)))
        self.cam = (wx - (pos[0] - MAP_W / 2) / new, wy - (pos[1] - MAP_H / 2) / new, new)


# ---------------------------------------------------------------- inventory

def inventory(state, history):
    return {
        "mode": state.mode,
        "rate": state.rate,
        "paused": state.paused,
        "phase": state.phase,
        "pick": state.pick,
        "mismatch": state.mismatch,
        "regions_drawn": len(history.regions),
        "factions_listed": len(history.factions),
        "selected_region": state.selected_region,
        "mission_rows": len(history.missions),
        "pulsing": sorted(state.pulse),
    }


# ---------------------------------------------------------------- geometry

def world_to_screen(wx, wy, cam):
    cx, cy, zoom = cam
    return int((wx - cx) * zoom + MAP_W / 2), int((wy - cy) * zoom + MAP_H / 2)


def screen_to_world(pos, cam):
    cx, cy, zoom = cam
    return (pos[0] - MAP_W / 2) / zoom + cx, (pos[1] - MAP_H / 2) / zoom + cy


def _positions(history, cam):
    return {rid: world_to_screen(p[0] * WORLD, p[1] * WORLD, cam)
            for rid, p in history.layout().items()}


def node_radius(region):
    t = max(0.0, min(1.0, region.get("capacity", 0) / 100.0))
    return NODE_R_MIN + int((NODE_R_MAX - NODE_R_MIN) * t)


def pick_region(history, cam, pos):
    best, best_d = None, 1e9
    for rid, (sx, sy) in _positions(history, cam).items():
        r_px = max(6, int(node_radius(history.regions.get(rid, {})) * cam[2]))
        d = math.hypot(pos[0] - sx, pos[1] - sy)
        if d <= r_px + 4 and d < best_d:
            best, best_d = rid, d
    return best


def _convex_hull(points):
    pts = sorted(set(map(tuple, points)))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _expand_hull(hull, pad):
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    out = []
    for px, py in hull:
        dx, dy = px - cx, py - cy
        dist = math.hypot(dx, dy)
        out.append((px, py) if dist < 1 else (px + dx / dist * pad, py + dy / dist * pad))
    return out


# ---------------------------------------------------------------- map drawing

def _draw_territories(surface, history, pos, cam):
    groups = {}
    for rid, r in history.regions.items():
        if r["owner"] in history.factions and rid in pos:
            groups.setdefault(r["owner"], []).append(pos[rid])
    pad = max(NODE_R_MAX * cam[2] + 12, 18)
    for fid, pts in groups.items():
        color = faction_color(fid, history.factions)
        if len(pts) == 1:
            r = int(pad)
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, 35), (r + 2, r + 2), r)
            pygame.draw.circle(s, (*color, 210), (r + 2, r + 2), r, 2)
            surface.blit(s, (pts[0][0] - r - 2, pts[0][1] - r - 2))
            continue
        if len(pts) == 2:
            (ax, ay), (bx, by) = pts
            length = math.hypot(bx - ax, by - ay)
            if length < 1:
                continue
            nx, ny = -(by - ay) / length * pad, (bx - ax) / length * pad
            poly = [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]
        else:
            hull = _convex_hull(pts)
            if len(hull) < 3:
                continue
            poly = _expand_hull(hull, pad)
        poly = [(int(x), int(y)) for x, y in poly]
        lo_x = min(p[0] for p in poly) - 4
        lo_y = min(p[1] for p in poly) - 4
        w = max(p[0] for p in poly) + 4 - lo_x
        h = max(p[1] for p in poly) + 4 - lo_y
        local = [(x - lo_x, y - lo_y) for x, y in poly]
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*color, 35), local)
        pygame.draw.polygon(s, (*color, 210), local, 2)
        surface.blit(s, (lo_x, lo_y))


def _draw_edges(surface, history, pos):
    for a, b in history.edges:
        if a in pos and b in pos:
            t = (history.regions[a]["tension"] + history.regions[b]["tension"]) / 200.0
            t = max(0.0, min(1.0, t))
            color = (int(55 + 200 * t), int(55 * (1 - t)), int(72 * (1 - t)))
            pygame.draw.line(surface, color, pos[a], pos[b], max(1, int(1 + 3 * t)))


def _draw_node(surface, state, history, rid, sxy, cam):
    r = history.regions[rid]
    base = faction_color(r["owner"], history.factions)
    stab = max(0.0, min(1.0, r["stability"] / 100.0))
    fill = _lerp((15, 15, 22), base, 0.25 + 0.75 * stab)
    sx, sy = sxy
    r_px = max(6, int(node_radius(r) * cam[2]))
    pygame.draw.circle(surface, fill, sxy, r_px)
    pygame.draw.circle(surface, base, sxy, r_px, 2)
    tension = r["tension"]
    if tension > 5:
        ring_t = int(max(1, min(5, tension / 20.0)))
        ring = pygame.Surface((r_px * 2 + 4, r_px * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring, (220, 60, 60, int(80 + 175 * tension / 100)),
                           (r_px + 2, r_px + 2), max(3, r_px - ring_t - 2), ring_t)
        surface.blit(ring, (sx - r_px - 2, sy - r_px - 2))
    left = state.pulse.get(rid)
    if left:
        alpha = int(70 + 185 * min(1.0, left / PULSE_SECONDS))
        p = pygame.Surface((r_px * 2 + 16, r_px * 2 + 16), pygame.SRCALPHA)
        pygame.draw.circle(p, (255, 240, 100, alpha), (r_px + 8, r_px + 8), r_px + 6, 3)
        surface.blit(p, (sx - r_px - 8, sy - r_px - 8))
    if rid == state.selected_region:
        pygame.draw.circle(surface, SELECTED, sxy, r_px + 4, 2)
    if r_px >= 9:
        label = _font(15).render(str(rid), True, BRIGHT)
        surface.blit(label, (sx - label.get_width() // 2, sy - label.get_height() // 2))


def _draw_radar(surface, region, sxy, cam):
    r_base = max(6, int(NODE_R_MAX * cam[2]))
    for field, deg in RADAR_ARMS:
        length = int(r_base * region[field] / 100.0)
        if length < 2:
            continue
        a = math.radians(deg - 90)
        end = (sxy[0] + int(length * math.cos(a)), sxy[1] + int(length * math.sin(a)))
        pygame.draw.line(surface, FIELD_COLORS[field], sxy, end, max(1, int(2 * cam[2])))


def _draw_map(surface, state, history):
    pygame.draw.rect(surface, BG_COLOR, (0, 0, MAP_W, MAP_H))
    cam = state.camera()
    pos = _positions(history, cam)
    _draw_territories(surface, history, pos, cam)
    _draw_edges(surface, history, pos)
    for rid in sorted(pos):
        if rid in history.regions:
            _draw_node(surface, state, history, rid, pos[rid], cam)
            if state.radar:
                _draw_radar(surface, history.regions[rid], pos[rid], cam)


# ---------------------------------------------------------------- sidebar

class _Column:
    """Top-down text column used by the sidebar."""

    def __init__(self, surface, x, y, w):
        self.surface, self.x, self.y, self.w = surface, x, y, w

    def line(self, text, color=TEXT, lh=16, size=17):
        _text(self.surface, text, (self.x, self.y), color, size)
        self.y += lh

    def bar(self, value, color, vmax=100.0):
        pygame.draw.rect(self.surface, (40, 40, 55), (self.x, self.y, self.w, 7), border_radius=3)
        fill = int(self.w * max(0.0, min(value, vmax)) / vmax)
        if fill > 0:
            pygame.draw.rect(self.surface, color, (self.x, self.y, fill, 7), border_radius=3)
        self.y += 10

    def sparkline(self, vals, color, h=16):
        if len(vals) >= 2:
            lo, hi = min(vals), max(vals)
            span = hi - lo if hi != lo else 1.0
            pts = [(self.x + int(i * self.w / (len(vals) - 1)),
                    self.y + h - int((v - lo) / span * h)) for i, v in enumerate(vals)]
            pygame.draw.lines(self.surface, color, False, pts, 1)
        self.y += h + 4

    def gap(self, px=6):
        self.y += px


def _sidebar_mission(col, state, history):
    col.line("MISSION  phase %s" % state.phase, BRIGHT)
    if state.phase != "idle":
        col.line("archetype %d  region %s  objectives %d" % (
            state.archetype, state.mission_region, state.n_objectives), DIM)
    d = state.last_debrief
    if d is None:
        col.line("RETURN starts / resolves / jumps", DIM)
    else:
        color = RED if state.mismatch else (80, 210, 120)
        col.line("sim band %d %s" % (d["band"], BAND_NAMES[d["band"]]), color)
        rd = d.get("region_delta", {})
        col.line("  ".join("%s %+.1f" % (k[:3], rd.get(k, 0.0)) for k in
                            ("military", "economy", "tension", "population")), DIM)
    col.gap()


def _sidebar_region(col, state, history):
    rid = state.selected_region
    r = history.regions.get(rid)
    if r is None:
        col.line("click a region to inspect", DIM)
        col.gap()
        return
    col.line("Region %d   tier %s" % (rid, r["tier"]), BRIGHT)
    owner = r["owner"]
    col.line("Owner: %s" % ("faction %d" % owner if owner in history.factions else "unclaimed"),
             faction_color(owner, history.factions))
    for field in ("military", "economy", "tension", "population"):
        color = FIELD_COLORS[field]
        col.line("%-11s %5.1f" % (field.capitalize(), r[field]), color, lh=15)
        col.bar(r[field], color)
        col.sparkline(history.ring(rid, field)[-RING:], color)
    for comp in ("stability", "capacity"):
        col.line("%-11s %5.1f" % (comp.capitalize(), r[comp]), TEXT, lh=15)
        col.bar(r[comp], (90, 130, 200))
    col.gap()


def _sidebar_faction_detail(col, state, history):
    fid = state.tracked_faction
    f = history.factions.get(fid)
    if f is None:
        col.line("[F] faction view: TAB picks a faction", DIM)
        col.gap()
        return
    color = faction_color(fid, history.factions)
    owned = [r for r in history.regions.values() if r["owner"] == fid]
    col.line("[F] Faction %d  archetype %s" % (fid, f.get("archetype", "?")), color)
    col.line("Regions %d   tech %.3f   budget %.1f" % (
        len(owned), f.get("tech", 0.0), f.get("budget", 0.0)), TEXT)
    for field in ("military", "economy", "population"):
        total = sum(r[field] for r in owned)
        col.line("%-11s %7.1f" % (field.capitalize(), total), FIELD_COLORS[field], lh=15)
        col.bar(total, FIELD_COLORS[field], vmax=100.0 * max(len(owned), 1))
    col.gap()


def _sidebar_factions(col, state, history):
    counts = {}
    for r in history.regions.values():
        counts[r["owner"]] = counts.get(r["owner"], 0) + 1
    col.line("-- factions --", DIM, lh=15)
    for fid in sorted(history.factions):
        color = faction_color(fid, history.factions)
        pygame.draw.rect(col.surface, color, (col.x, col.y + 3, 9, 9))
        mark = "*" if fid == state.player_faction else " "
        _text(col.surface, "%s f%-2d  %3d regions" % (mark, fid, counts.get(fid, 0)),
              (col.x + 14, col.y), BRIGHT if fid == state.tracked_faction else TEXT, 16)
        col.y += 14


def _draw_sidebar(surface, state, history):
    pygame.draw.rect(surface, SIDEBAR_BG, (MAP_W, 0, SIDEBAR_W, SIDEBAR_H))
    pygame.draw.line(surface, BORDER, (MAP_W, 0), (MAP_W, SIDEBAR_H))
    col = _Column(surface, MAP_W + 12, 10, SIDEBAR_W - 24)
    if state.mode == "mission":
        _sidebar_mission(col, state, history)
    if state.faction_view:
        _sidebar_faction_detail(col, state, history)
    else:
        _sidebar_region(col, state, history)
    _sidebar_factions(col, state, history)


# ---------------------------------------------------------------- log, controls

def _draw_log(surface, state, history):
    pygame.draw.rect(surface, LOG_BG, (0, MAP_H, MAP_W, LOG_H))
    pygame.draw.line(surface, BORDER, (0, MAP_H), (MAP_W, MAP_H))
    y = MAP_H + 5
    if state.mode == "mission":
        _text(surface, "tick   region  archetype  picked              sim band", (10, y), DIM, 16)
        rows = list(enumerate(history.missions))[-6:]
        for i, m in reversed(rows):
            pick = state.picked[i] if i < len(state.picked) else None
            picked = "-" if pick is None else "%d %s" % (pick, BAND_NAMES[pick])
            bad = pick is not None and pick != m["band"]
            band = "%d %s" % (m["band"], BAND_NAMES[m["band"]])
            y += 16
            _text(surface, "%-6d %-7s %-10s %-19s %s" % (
                m["tick"], m["region"], m["archetype"], picked, band),
                (10, y), RED if bad else TEXT, 16)
        if not history.missions:
            _text(surface, "no missions yet", (10, y + 16), DIM, 16)
        return
    events = [dict(e, region=rid) for rid in sorted(history.regions)
              for e in history.events(rid)]
    events.sort(key=lambda e: (e["tick"], e["region"]))
    _text(surface, "events (latest first)", (10, y), DIM, 16)
    for pos, e in enumerate(reversed(events[-6:])):
        y += 16
        _text(surface, "t%-5d region %-3d template %-3s chain %s" % (
            e["tick"], e["region"], e["template"], e["chain"]),
            (10, y), TEXT if pos == 0 else DIM, 16)
    if not events:
        _text(surface, "no events yet", (10, y + 16), DIM, 16)


def _draw_controls(surface, state, history):
    y0 = H - CONTROLS_H
    pygame.draw.rect(surface, CONTROLS_BG, (0, y0, W, CONTROLS_H))
    pygame.draw.line(surface, BORDER, (0, y0), (W, y0))
    pick = "-" if state.pick is None else "%d %s" % (state.pick, BAND_NAMES[state.pick])
    head = "%s mode | tick %d | %s | rate %d/s | pick %s | phase %s" % (
        state.mode.upper(), history.tick, "PAUSED" if state.paused else "RUNNING",
        state.rate, pick, state.phase)
    _text(surface, head, (10, y0 + 5), BRIGHT)
    if state.mismatch:
        w = _font(17).size(head)[0]
        d = state.last_debrief or {}
        _text(surface, "  MISMATCH: sim band %s != pick %s" % (d.get("band"), state.pick),
              (10 + w, y0 + 5), RED)
    _text(surface, state.status, (10, y0 + 22), TEXT)
    _text(surface, "SPACE run  RIGHT step  [ ] rate  M mode  1-5 pick band  0 refuse  "
          "RETURN advance  F faction  TAB cycle  V radar  R camera  ESC quit",
          (10, y0 + 39), DIM, 16)


# ---------------------------------------------------------------- frame

def draw(state, history, surface):
    surface.fill(BG_COLOR)
    _draw_map(surface, state, history)
    _draw_sidebar(surface, state, history)
    _draw_log(surface, state, history)
    _draw_controls(surface, state, history)
