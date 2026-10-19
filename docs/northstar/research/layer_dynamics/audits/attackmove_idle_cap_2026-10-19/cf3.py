import sys, dataclasses
from capprobe import *
def cf(setup, seed, swap, point, label):
    eng=Engine(); of=eng.free_world
    def hook(w):
        S=survivors(eng,w)
        for s in (0,1):
            for u in S[s]: eng.order_attack_move(w,[u],point[0],point[1])
        for t in range(6000):
            eng.step(w)
            n=survivors(eng,w)
            if not n[0] or not n[1]: break
        print(label,"survivors at cap",S,"re-issue (per unit) attack-move to point",point,"-> after",t+1,"ticks:",{s:len(n[s]) for s in (0,1)})
        of(w)
    eng.free_world=hook
    F.fight(setup,seed,swap,eng)
b=scenes.objective_scene(2800.0)
s=dataclasses.replace(b(16,False),orders_per_unit=False,states=False)
cf(s,0,False,(0.0,0.0),"obj")
b=plays.blob_play(16)
s=dataclasses.replace(b(16,True),orders_per_unit=False,states=False)
print("mirror point",s.point,[ (g.goal,g.order) for g in s.groups])
cf(s,0,True,(0.0,0.0),"mirror")
