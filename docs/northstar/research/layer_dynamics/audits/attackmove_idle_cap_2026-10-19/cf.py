import sys, pickle, dataclasses
from capprobe import *
def counterfactual(setup, seed, swap, point, label):
    eng=Engine(); of=eng.free_world
    def hook(w):
        S=survivors(eng,w)
        for s in (0,1):
            for u in S[s]:
                # only the attackers (attack-move groups) get re-ordered; guards stay
                pass
        att=[g for g in range(len(setup.groups)) if setup.groups[g].order=="attack_move"]
        side=setup.groups[att[0]].side if att else None
        # after swap, side ids: engine faction == group.side
        for u in S[side]: eng.order_attack_move(w,[u],point[0],point[1])
        for t in range(6000):
            eng.step(w)
            if not survivors(eng,w)[0] or not survivors(eng,w)[1]: break
        print(label,"counterfactual re-issue attack-move to point for faction",side,"survivors:",S[side],"-> after",t+1,"ticks:",{s:len(survivors(eng,w)[s]) for s in (0,1)})
        of(w)
    eng.free_world=hook
    F.fight(setup,seed,swap,eng)
if __name__=="__main__":
    caps=pickle.load(open("caps_damage_up.pkl","rb"))
    for i in (0,25,26):
        (setup,seed,swap),*_=caps[i]
        counterfactual(setup,seed,swap,setup.point,"job%d"%i)
