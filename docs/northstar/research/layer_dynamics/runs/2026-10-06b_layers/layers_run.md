# Skill lab layers batch

Pass marks provisional (A174). Unconfirmed definitions stay unconfirmed.

Lab rule, provisional: mop-up order. A side whose units have stopped, none with an enemy in attack range, that sees an enemy, re-issues its attack-move at the centroid of the enemies it sees, at most once per mopup_interval_ticks. Setting: mopup=True, mopup_interval_ticks=200. Each fight's count is the mopup_orders column.

## Scene

Tables LA (vision only), LB (vision and reach) and LC (vision, reach and damage) by four scenes: a mirror, high ground and two chokes. 16 Vanguards against 8 to 24. The LB and LC values are sweep points proposed by the Architect as drafts (A174), not confirmed by Westley. The sampled choke is a sampled wall from maps.sample_map and the Phase B choke is its own cell: a 3000 by 1600 canvas with a gap in the wall, where the defenders attack-move (the idle version is in the landscape batch) and side 0 is the 8 defenders against 7 to 12 attackers. The last 16 cells are a Raider mirror over collision radius and attack range (reach against body size), also drafts.

## Cells

| cell | size | enemy range | replicates | fights per cell | status |
|---|---|---|---|---|---|
| LA:mirror | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| LA:high_ground | 16 | 8 to 24 | 10 | 20 | not expressed |
| LA:choke | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| LA:choke_phase_b | 8 | 7 to 12 | 10 | 20 | unconfirmed draft |
| LB:mirror:up1=0.5,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:mirror:up1=0.5,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:mirror:up1=0.75,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:mirror:up1=0.75,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:mirror:up1=1.0,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:mirror:up1=1.0,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:high_ground:up1=0.5,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:high_ground:up1=0.5,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:high_ground:up1=0.75,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:high_ground:up1=0.75,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:high_ground:up1=1.0,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:high_ground:up1=1.0,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke:up1=0.5,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke:up1=0.5,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke:up1=0.75,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke:up1=0.75,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke:up1=1.0,up2=0.25 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke:up1=1.0,up2=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LB:choke_phase_b:up1=0.5,up2=0.25 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LB:choke_phase_b:up1=0.5,up2=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LB:choke_phase_b:up1=0.75,up2=0.25 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LB:choke_phase_b:up1=0.75,up2=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LB:choke_phase_b:up1=1.0,up2=0.25 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LB:choke_phase_b:up1=1.0,up2=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:mirror:up1=0.5,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.5,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.75,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.75,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=1.0,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=1.0,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.5,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.5,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.75,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=0.75,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=1.0,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:mirror:up1=1.0,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.5,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.5,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.75,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.75,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=1.0,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=1.0,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.5,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.5,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.75,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=0.75,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=1.0,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:high_ground:up1=1.0,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.5,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.5,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.75,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.75,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=1.0,up2=0.25,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=1.0,up2=0.5,dmg1=0.5 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.5,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.5,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.75,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=0.75,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=1.0,up2=0.25,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke:up1=1.0,up2=0.5,dmg1=0.75 | 16 | 8 to 24 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.5,up2=0.25,dmg1=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.5,up2=0.5,dmg1=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.75,up2=0.25,dmg1=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.75,up2=0.5,dmg1=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=1.0,up2=0.25,dmg1=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=1.0,up2=0.5,dmg1=0.5 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.5,up2=0.25,dmg1=0.75 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.5,up2=0.5,dmg1=0.75 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.75,up2=0.25,dmg1=0.75 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=0.75,up2=0.5,dmg1=0.75 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=1.0,up2=0.25,dmg1=0.75 | 8 | 7 to 12 | 10 | 20 | not expressed |
| LC:choke_phase_b:up1=1.0,up2=0.5,dmg1=0.75 | 8 | 7 to 12 | 10 | 20 | not expressed |
| body20_range150_ratio7.5 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body20_range200_ratio10.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body20_range300_ratio15.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body20_range450_ratio22.5 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body30_range150_ratio5.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body30_range200_ratio6.7 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body30_range300_ratio10.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body30_range450_ratio15.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body40_range150_ratio3.8 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body40_range200_ratio5.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body40_range300_ratio7.5 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body40_range450_ratio11.2 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body60_range150_ratio2.5 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body60_range200_ratio3.3 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body60_range300_ratio5.0 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |
| body60_range450_ratio7.5 | 16 | 8 to 24 | 10 | 20 | unconfirmed draft |

Cells within 2 enemy units of a break-even run 3 times the fights.

## Results

- LA:mirror (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 3257.3; mean firing unit-seconds 955.63 side 0, 837.45 side 1; stalled fights 13 (quiet stalemates only); caps 29; draws 0 | pair spread 0.60 to 0.72
- LA:choke (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 3257.3; mean firing unit-seconds 955.63 side 0, 837.45 side 1; stalled fights 13 (quiet stalemates only); caps 29; draws 0 | pair spread 0.60 to 0.72
- LA:choke_phase_b (unconfirmed draft), default: no break-even in range; mean fight ticks 2321.9; mean firing unit-seconds 429.31 side 0, 488.52 side 1; stalled fights 99 (quiet stalemates only); caps 0; draws 0
- body20_range150_ratio7.5 (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 966.0; mean firing unit-seconds 244.41 side 0, 212.29 side 1; stalled fights 5 (quiet stalemates only); caps 0; draws 0 | pair spread 0.59 to 0.70
- body20_range200_ratio10.0 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1266.4; mean firing unit-seconds 278.65 side 0, 274.09 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread -0.15 to 0.27
- body20_range300_ratio15.0 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1251.7; mean firing unit-seconds 276.11 side 0, 276.22 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.10 to 0.33
- body20_range450_ratio22.5 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1139.7; mean firing unit-seconds 276.14 side 0, 272.28 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread 0.04 to 0.30
- body30_range150_ratio5.0 (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 966.0; mean firing unit-seconds 244.41 side 0, 212.29 side 1; stalled fights 5 (quiet stalemates only); caps 0; draws 0 | pair spread 0.59 to 0.70
- body30_range200_ratio6.7 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1266.4; mean firing unit-seconds 278.65 side 0, 274.09 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread -0.15 to 0.27
- body30_range300_ratio10.0 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1251.7; mean firing unit-seconds 276.11 side 0, 276.22 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.10 to 0.33
- body30_range450_ratio15.0 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1139.7; mean firing unit-seconds 276.14 side 0, 272.28 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread 0.04 to 0.30
- body40_range150_ratio3.8 (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 966.0; mean firing unit-seconds 244.41 side 0, 212.29 side 1; stalled fights 5 (quiet stalemates only); caps 0; draws 0 | pair spread 0.59 to 0.70
- body40_range200_ratio5.0 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1266.4; mean firing unit-seconds 278.65 side 0, 274.09 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread -0.15 to 0.27
- body40_range300_ratio7.5 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1251.7; mean firing unit-seconds 276.11 side 0, 276.22 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.10 to 0.33
- body40_range450_ratio11.2 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1139.7; mean firing unit-seconds 276.14 side 0, 272.28 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread 0.04 to 0.30
- body60_range150_ratio2.5 (unconfirmed draft), default: 16 units beat 10, lose to 11; mean fight ticks 966.0; mean firing unit-seconds 244.41 side 0, 212.29 side 1; stalled fights 5 (quiet stalemates only); caps 0; draws 0 | pair spread 0.59 to 0.70
- body60_range200_ratio3.3 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1266.4; mean firing unit-seconds 278.65 side 0, 274.09 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread -0.15 to 0.27
- body60_range300_ratio5.0 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1251.7; mean firing unit-seconds 276.11 side 0, 276.22 side 1; stalled fights 0 (quiet stalemates only); caps 0; draws 0 | pair spread -0.10 to 0.33
- body60_range450_ratio7.5 (unconfirmed draft), default: 16 units beat 15, lose to 16; mean fight ticks 1139.7; mean firing unit-seconds 276.14 side 0, 272.28 side 1; stalled fights 3 (quiet stalemates only); caps 0; draws 0 | pair spread 0.04 to 0.30

## What the instrument could not express

- the tall-cover scene (needs reach)
- Vanguard and Warden 0 up 0 down; Raider 1 up 1 down; Interceptor 2 up 1 down; Bombard and Bastion 0 up 2 down (needs om_roster_set_reach bound in the harness and Phase C G5)
- high ground and the LB and LC tables wait for reach
- the choke cells use a sampled wall from maps.sample_map; the Phase B choke scene is its own cell, choke_phase_b
- LA:high_ground: units on different layers cannot fire until reach by type lands (Phase C G5)
- LB:mirror:up1=0.5,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:mirror:up1=0.5,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:mirror:up1=0.75,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:mirror:up1=0.75,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:mirror:up1=1.0,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:mirror:up1=1.0,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:high_ground:up1=0.5,up2=0.25: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LB:high_ground:up1=0.5,up2=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LB:high_ground:up1=0.75,up2=0.25: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LB:high_ground:up1=0.75,up2=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LB:high_ground:up1=1.0,up2=0.25: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LB:high_ground:up1=1.0,up2=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke:up1=0.5,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke:up1=0.5,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke:up1=0.75,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke:up1=0.75,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke:up1=1.0,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke:up1=1.0,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke_phase_b:up1=0.5,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke_phase_b:up1=0.5,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke_phase_b:up1=0.75,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke_phase_b:up1=0.75,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke_phase_b:up1=1.0,up2=0.25: needs reach by type (om_roster_set_reach) and Phase C G5
- LB:choke_phase_b:up1=1.0,up2=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.5,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.5,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.75,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.75,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=1.0,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=1.0,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.5,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.5,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.75,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=0.75,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=1.0,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:mirror:up1=1.0,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.5,up2=0.25,dmg1=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.5,up2=0.5,dmg1=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.75,up2=0.25,dmg1=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.75,up2=0.5,dmg1=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=1.0,up2=0.25,dmg1=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=1.0,up2=0.5,dmg1=0.5: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.5,up2=0.25,dmg1=0.75: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.5,up2=0.5,dmg1=0.75: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.75,up2=0.25,dmg1=0.75: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=0.75,up2=0.5,dmg1=0.75: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=1.0,up2=0.25,dmg1=0.75: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:high_ground:up1=1.0,up2=0.5,dmg1=0.75: units on different layers cannot fire until reach by type lands (Phase C G5); needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.5,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.5,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.75,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.75,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=1.0,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=1.0,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.5,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.5,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.75,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=0.75,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=1.0,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke:up1=1.0,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.5,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.5,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.75,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.75,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=1.0,up2=0.25,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=1.0,up2=0.5,dmg1=0.5: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.5,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.5,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.75,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=0.75,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=1.0,up2=0.25,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5
- LC:choke_phase_b:up1=1.0,up2=0.5,dmg1=0.75: needs reach by type (om_roster_set_reach) and Phase C G5

## Files

- layers.csv
- layers_run.md
- layers_page.html
