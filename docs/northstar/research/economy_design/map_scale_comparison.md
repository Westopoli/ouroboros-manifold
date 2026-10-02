# Map scale against Age of Empires 3 and World of Warships

Captured 2026-10-02 for Q-166-01 part 7. Tags: [V] a fetched page said it, [R] search summary, [E] not sourced.

World units, metres and kilometres cannot be compared directly, so the comparison is in two measures that do not depend on the unit: how many attack ranges of a standard line unit fit across the map, and how long a unit takes to cross it.

## Sources

- **Age of Empires 3.** Random map scripts set the side of the map as `2.0 * sqrt(players * playerTiles)` with `playerTiles = 10000` in the stock script quoted [V: https://aoe3.heavengames.com/cgi-bin/forums/display.cgi?action=ct&f=12,25074,2700,all]. That gives 283 m for 2 players, 400 m for 4 and 566 m for 8; a 4-player map is "about 400 m along one side" [R: https://support.ageofempires.com/hc/en-us/articles/8478836252564-Random-Map-Scripting-Commands] and a modder describes the stock limit as "~600x600 metres" [V, same forum thread]. The engine's maximum is 1024 x 1024 [V: https://aoe3.heavengames.com/cgi-bin/forums/display.cgi?action=st&fn=12&tn=25023]. Musketeer: speed 4, range 12. Hussar: speed 6.75 [R: https://ageofempires.fandom.com/wiki/Musketeer, https://ageofempires.fandom.com/wiki/Hussar_(Age_of_Empires_III)].
- **World of Warships.** Maps run from 24 x 24 km to 48 x 48 km; eleven maps are 48 x 48 km [V: https://wiki.worldofwarships.com/Ship:Maps]. How ship speed in knots converts to distance per second in the game could not be verified; the wiki's manoeuvring page does not state it. Battleship gun range of about 20 km is [E].
- **Ouroboros.** Roster table in E-11: Vanguard (line) range 300 wu, speed 80 wu/s; Raider speed 150 wu/s.

## The comparison

| Map | Side | Line-unit ranges across | Line unit crosses in | Fast unit crosses in |
|---|---|---|---|---|
| Age of Empires 3, 8 players, stock | 566 m | 47 | 2.4 min | 1.4 min |
| Age of Empires 3, engine maximum | 1,024 m | 85 | 4.3 min | 2.5 min |
| Ouroboros today, largest | 32,000 wu | 107 | 6.7 min | 3.6 min |
| Ouroboros 64,000 | 64,000 wu | 213 | 13.3 min | 7.1 min |
| Ouroboros 128,000 | 128,000 wu | 427 | 26.7 min | 14.2 min |
| World of Warships, largest | 48 km | about 2.4 battleship ranges [E] | not verified | not verified |

## Reading it

- Today's largest canvas is already about 2.3 times the width of the largest stock Age of Empires 3 map, in ranges, and about 5 times its area.
- 64,000 wu is about 4.5 times the width and 20 times the area of that map. 128,000 wu is about 9 times the width and 80 times the area.
- World of Warships is large in kilometres, but a battleship's guns reach across almost half the map. Measured in ranges it is a small map. Its sense of scale comes from the size of the ships against the islands and from the map view, not from the distance in ranges.
