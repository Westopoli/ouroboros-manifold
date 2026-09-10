# Ambiguity Register

Every open design question that blocks a story from being Ready. Claude raises flags here instead of guessing. Westley answers; the answer becomes a rule in the epic file and the flag closes. Closed flags stay in the table with their answer so the reasoning survives.

Schema: `Q-<story>-<nn>` where `<story>` is the story number the flag blocks, or `E##` when it blocks a whole epic that has no story numbers yet.

| Flag | Epic / story | Question | Candidate answers | Status | Answer |
|---|---|---|---|---|---|
| Q-E01-01 | Layer System | What elevation does each layer map to on screen, in world units, and is the mapping fixed per era or per map? | (a) fixed per era in the theme manifest; (b) per map from the generator; (c) fixed globally | open | |
| Q-E01-02 | Layer System | When a unit's layer changes, does it visibly move to the new elevation, and over how many ticks? | (a) instant snap; (b) tween over N ticks with the unit unable to fire while moving; (c) tween with no restrictions | open | |
| Q-E01-03 | Layer System | What can a unit on layer 2 see on layers 1 and 3, and at what range compared to its own layer? | (a) same range, all layers; (b) reduced range on adjacent layers, none beyond; (c) cone and pulse model from `bible_world.md` with concrete numbers | open | |
| Q-E01-04 | Layer System | Do layers change pathing, damage, or cover? Which of the three, and how? | (a) vision only; (b) vision and damage modifiers; (c) vision, damage, and separate pathing per layer | open | |
| Q-E01-05 | Layer System | What does the player see in the HUD about a selected unit's layer and about enemies on other layers? | (a) layer badge on the unit; (b) badge plus per-layer filter toggle; (c) nothing beyond elevation on screen | open | |
| Q-E01-06 | Layer System | Under fog, how does an enemy on another layer appear compared to one on the same layer? | (a) identical; (b) silhouette only on other layers; (c) hidden unless a pulse is active | open | |
| Q-E01-07 | Layer System | Is the layer system still "the" strategic defining characteristic, and if so what is the one-sentence player-facing promise it must keep? | Westley to write the sentence | open | |
