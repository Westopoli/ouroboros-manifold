# Map of `docs/`

Start with [`METHOD.md`](METHOD.md) (how the repo is run) and [`bible/game_bible.md`](bible/game_bible.md) (what the game is). Folder by folder, as of 2026-11-05:

| Path | What is in it |
|---|---|
| `bible/` | The source of truth for the game: hub, story catalog, one file per epic, references, `algorithms.md` |
| `bible_history/` | Snapshots of retired bible text; the bible itself is rewrite-not-append |
| `method/` | The current method: roles, the story loop, the harness, the cards every plan shares |
| `stories/` | The harness and lab stories (`H-###`), one file each |
| `northstar/` | The records: roadmap, ambiguity register, plans, research, story reviews. Its own [`README.md`](northstar/README.md) maps it |
| `architecture.md` | The pipe frames and cross-stage contracts |
| `legacy/` | Retired docs, indexed in [`legacy/README.md`](legacy/README.md): the first (Agora) method, the Python-era stage and test specs, early research dumps, the lean-MVP plan, old C4 diagrams |

Retired text is moved to `legacy/` (or `northstar/plans/archive/`), never deleted. The root `legacy/` holds retired code and build output ([`../legacy/README.md`](../legacy/README.md)).
