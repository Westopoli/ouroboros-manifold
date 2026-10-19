import sys, pickle
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/6595578b-476b-499c-ae9d-903b2a7b43bd/scratchpad")
from capprobe import *
caps=pickle.load(open("caps_damage_up.pkl","rb"))
idx=[i for i,c in enumerate(caps) if c[3]==12000]
print("12000-cap indices",idx)
i=idx[int(sys.argv[1])]
(setup,seed,swap),out,surv,ticks=caps[i]
print("job",i,"seed",seed,"swap",swap,"max_ticks",setup.max_ticks,"opu",setup.orders_per_unit,"point",setup.point)
for g in setup.groups: print(g)
lib=sys.argv[2] if len(sys.argv)>2 else None
if lib=="dbg":
    import dataclasses
    eng=Engine("/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/6595578b-476b-499c-ae9d-903b2a7b43bd/scratchpad/libdbg.so")
    orig=eng.step; t=[0]
    def step(w):
        orig(w); t[0]+=1; sys.stderr.write("TICK %d\n"%t[0])
    eng.step=step
    S=[None]
    of=eng.free_world
    def hook(w):
        S[0]=describe(eng,w,"cap"); of(w)
    eng.free_world=hook
    r=F.fight(setup,seed,swap,eng)
else:
    r=run(setup,seed,swap,extra=100)
