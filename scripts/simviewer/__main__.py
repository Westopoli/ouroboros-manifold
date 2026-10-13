"""Launch the sim viewer: python -m scripts.simviewer (see README.md)."""
import argparse
import os
import sys

from scripts.simviewer.history import History
from scripts.simviewer.pipe_session import DEFAULT_FEATURES, PipeError, PipeSession

SHOT_WARMUP_STEPS = 30
SHOT_MISSION_PICKS = (3, 2)


def _parse(argv):
    p = argparse.ArgumentParser(prog="scripts.simviewer", description=__doc__)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--n-regions", type=int, default=80)
    p.add_argument("--rate", type=int, default=5)
    p.add_argument("--mode", choices=("tick", "mission"), default="tick")
    p.add_argument("--shot", metavar="DIR", help="headless: write tick_mode.png and mission_mode.png")
    return p.parse_args(argv)


def _open(args, viewer):
    session = PipeSession()
    session.send("set_seed", seed=args.seed, n_regions=args.n_regions, features=DEFAULT_FEATURES)
    history = History()
    state = viewer.ViewerState(history, session)
    for fr in session.send("snapshot"):
        state.apply(fr)
    while state.rate != args.rate and args.rate in viewer.RATES:
        (state.rate_up if state.rate < args.rate else state.rate_down)()
    if args.mode == "mission":
        state.toggle_mode()
    return session, history, state


def _shot(args, viewer, state, history, surface, pygame):
    out = args.shot
    os.makedirs(out, exist_ok=True)
    state.mode = "tick"
    for _ in range(SHOT_WARMUP_STEPS):
        state.advance()
    busiest = max(history.regions, key=lambda r: history.regions[r]["military"])
    state.selected_region = busiest
    state.pulse = {busiest: 1.0}
    viewer.draw(state, history, surface)
    pygame.image.save(surface, os.path.join(out, "tick_mode.png"))
    state.toggle_mode()
    for n, pick in enumerate(SHOT_MISSION_PICKS):
        state.pulse.clear()
        state.advance()
        state.set_pick(pick)
        state.advance()
        if n < len(SHOT_MISSION_PICKS) - 1:
            state.advance()
    viewer.draw(state, history, surface)
    pygame.image.save(surface, os.path.join(out, "mission_mode.png"))


def _loop(viewer, state, history, pygame, screen):
    clock = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                return
            if ev.type == pygame.KEYDOWN:
                state.handle_key(ev.key)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                state.mouse_down(ev.pos, ev.button)
            elif ev.type == pygame.MOUSEBUTTONUP:
                state.mouse_up(ev.pos, ev.button)
            elif ev.type == pygame.MOUSEMOTION:
                state.mouse_move(ev.pos)
            elif ev.type == pygame.MOUSEWHEEL:
                state.wheel(pygame.mouse.get_pos(), ev.y)
        state.update(clock.tick(60) / 1000.0)
        viewer.draw(state, history, screen)
        pygame.display.flip()


def main(argv=None):
    args = _parse(argv)
    if args.shot:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    from scripts.simviewer import viewer
    pygame.init()
    try:
        session, history, state = _open(args, viewer)
    except (PipeError, OSError, EOFError) as e:
        print("simviewer: %s" % e, file=sys.stderr)
        return 1
    try:
        if args.shot:
            _shot(args, viewer, state, history, pygame.Surface((viewer.W, viewer.H)), pygame)
        else:
            pygame.display.set_caption("sim viewer: seed %d, %d regions" % (args.seed, args.n_regions))
            _loop(viewer, state, history, pygame, pygame.display.set_mode((viewer.W, viewer.H)))
    finally:
        session.close()
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
