# Goal 4: the economy with nobody in the seat, options

Written 2026-10-02 for Westley. Surface level; standard and wild per part. Flags: Q-159-02 (how it runs itself), Q-159-03 (what a solo commander may place).

## Already decided

- Rules run the economy for the player, and run it well. No intelligent agent.
- The base is a spectacle in every mode: buildings rise, expansions are made, density changes.
- The solo commander does not administer the economy.
- The enemy's difficulty scales its economic prosperity and its multi-layer intelligence (Q-125-02).
- The economy is the one in `current_system.md`: workers, three resources, one population cap, production, technology, expansions, defenses, shipments, counters, a schedule, forward bases.
- The game never calls a model at runtime, and the same seed and commands give the same result.

---

## Part A. How the rules decide

**Standard**

- **A1. Build orders.** A written opening and priority list for each kind of base and mission archetype, followed step by step. Predictable and easy to tune; it does the same thing every time.
- **A2. A checklist of reflexes.** A set of standing rules that react to the state, the same list a good player keeps in his head: house before the cap, never an idle worker, rebalance when one resource floods, expand when the home sites are saturated, wall the lane that was raided. No plan, only good habits.
- **A3. Doctrines.** A few named ways of playing (boom, fortify, press, balanced), each a build order with its own checklist weights. Something chooses the doctrine per mission.

**Wild**

- **A4. The civilization's character runs it.** The doctrine and its weights come from the simulation: a wealthy civilization booms, a tense one fortifies, a militarist one presses, a declining one makes do with less. The economy the commander is given feels like the civilization he serves. It always runs competently; what changes is what it values.
- **A5. Recorded hands.** The rules replay build orders recorded from good human economy players, chosen to fit the situation and adjusted by the checklist. Nothing is computed by a model at runtime; the recordings ship with the game and grow over time.

## Part B. How good "well" is

- **B1. A competent partner.** About as good as a decent human, fixed. A skilled human partner is clearly better.
- **B2. It follows difficulty.** The player's side runs better or worse with the difficulty setting.
- **B3. Perfect hands, no foresight.** The rules never idle a worker, never hit the cap, never float resources. They do not scout, do not read the enemy, do not counter-pick technology and do not disguise anything. Everything a human adds is the thinking-ahead part, which is where the skill of the seat was put.

## Part C. What the solo commander can do with it

**Standard**

- **C1. Watch.** Nothing; it is a backdrop that works.
- **C2. One dial.** The commander sets the balance between economy, technology and army, and may name the unit family he wants more of. The rules carry it out. This is the StarCraft balance as a single choice, and it is a nudge, not administration.
- **C3. Place the pieces that are his.** The commander may place the buildings that are military decisions: a forward base, a wall, a tower, where the next expansion goes. The rules build them and everything else. This matches "the player can place buildings wherever they want, and the city will morph around them".

**Wild**

- **C4. Ask by pointing.** The commander marks the map as he would ask a partner: expand here, fortify this pass, I need siege at this gate. The rules answer and say, in the ticker, what they will do and when. There is no menu and no queue.
- **C5. A quartermaster.** The rules speak as a named officer in the ticker, in the register of the chronicle: what is short, what is coming, what was lost on the road. The commander learns the state of the economy from a person's reports and not from a panel.

## Part D. Who decides which units are made, when alone

- **D1. The commander picks.** At a production building he picks a type, as he does at a reinforcement structure today.
- **D2. The rules pick, he can override.** The rules produce the mix the mission archetype calls for, and the commander can change any building's choice.
- **D3. The rules counter what has been seen.** The rules shift production toward what counters the enemy units the commander's forces have actually seen. They use only what the fog has revealed.

## Part E. The enemy's economy

- **E1. The same rules.** The enemy's economy is run by the same rules as the solo player's, with prosperity scaled by difficulty as already decided.
- **E2. The same rules, with a character.** As E1, and the enemy's doctrine comes from its own civilization's state in the simulation, so different enemies build differently.
- **E3 (wild). The enemy does what the player's rules cannot.** At higher difficulty the enemy's economy also scouts, counters and disguises. Difficulty then scales both its prosperity and its foresight, which is the economic twin of "multi-layer intelligence".

---

## A note that follows from lockstep

If a human economy player drops out of a paired mission, the same rules take over his seat for the rest of it. Any of the options above gives this for free.

## My lean (opinion, Westley's call)

A2 with A4, B3, C2 with C3 and C5, D2 with D3, E2 with E3.

- **A2 with A4:** good habits always, and the civilization's character decides what the habits are aimed at.
- **B3:** "well" gets a clear meaning, and it leaves the human seat exactly the part that was designed to be skilled.
- **C2 and C3:** the smallest hands-on a commander needs, and both are military choices.
- **C5:** gives the economy a voice without a panel, in the game's own tone.
- **D2 with D3:** the commander is never forced to manage production and can always overrule it.
- **E2 with E3:** enemies differ, and difficulty has an economic side that is more than a bigger number.
