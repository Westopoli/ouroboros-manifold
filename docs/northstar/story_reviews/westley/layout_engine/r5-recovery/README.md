# R5 recovery, terrain-obeys pass 2, as it is (2026-11-08)

Five seeds of the October "layout first, landscape obeys" prototype, recovered unchanged from the branch `push/proto-terrain-obeys-2` (head `f57af240`). Canvas 16,000 wu, windowed render at 1920x1080. This is the start point you chose on 2026-11-08 (DEC-layout-r5-start-point-2026-11-08). More sets (pass 5, a modified R5) follow in this folder; this README grows then.

## How it makes a map

A seed picks the axis angle. The two bases sit at the two ends of the line, 2,400 wu in from the edge. A choke sits 35 to 65 percent along the line, 180 to 600 wu wide. The objective sits 1,500 wu off the line, the two resource sites 2,400 wu either side of it, the vantage 1,500 wu beside the choke. Two to four routes run from the base to each place. The terrain is shaped to fit: flat pads, walls at the choke, carved roads, and the checks run on the finished ground (35-degree walk limit).

## Colours (walk view)

Dark blue water. Green reachable ground. Purple unreachable ground. Orange thin route (180 wu). Light blue wide route (600 wu). Red circle: a place whose check failed. Pink ring: the vantage. Black squares: unreachable peaks. Teal squares: reachable peaks.

## Pictures

| File | What to expect | Approve means | Deny means |
|---|---|---|---|
| `obey/obey_16000_1.png` | Seed 1: four route counts, choke at 0.60 of the line, 20 carved routes | This is the start point, keep it | Not this one; say what is missing |
| `obey/obey_16000_2.png` | Seed 2: two routes, choke at 0.58 | same | same |
| `obey/obey_16000_3.png` | Seed 3: two routes, choke at 0.39 (nearest the attacker) | same | same |
| `obey/obey_16000_4.png` | Seed 4: three routes, choke at 0.59 | same | same |
| `obey/obey_16000_5.png` | Seed 5: two routes, narrowest choke (210 wu) | same | same |

Each `obey/obey_panel_16000_N.txt` is the prototype's own panel for that picture (numbers, checks, the 25 named drafts), copied verbatim.
