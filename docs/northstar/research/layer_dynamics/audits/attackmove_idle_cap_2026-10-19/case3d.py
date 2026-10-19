import sys, dataclasses
sys.path.insert(0, "/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/6595578b-476b-499c-ae9d-903b2a7b43bd/scratchpad")
from probe import *
which=sys.argv[1]; swap=sys.argv[2]=="1"; seed=int(sys.argv[3]); watch=[int(x) for x in sys.argv[4].split(",")]
b=scenes.objective_scene(2800.0) if which=="obj" else plays.blob_play(16)
s=dataclasses.replace(b(16,swap),orders_per_unit=False,states=False)
eng=Engine("/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/6595578b-476b-499c-ae9d-903b2a7b43bd/scratchpad/libdbg.so")
orig=eng.step; t=[0]; last={}
def step(w):
    orig(w); t[0]+=1
    sys.stderr.write("TICK %d\n"%t[0])
    for u in watch:
        if not eng.unit_alive(w,u): continue
        d=eng.unit_destination(w,u)
        if last.get(u,"x")!=d:
            sys.stderr.write("WATCH t%d u%d dest %s -> %s pos %s hp %.0f tgt %d\n"%(t[0],u,last.get(u),d,tuple(round(v) for v in eng.unit_pos(w,u)),eng.unit_hp(w,u),eng.unit_target(w,u)))
            last[u]=d
eng.step=step
r=F.fight(s,seed,swap,eng); print(r.outcome,r.survivors)
