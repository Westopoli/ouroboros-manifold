import sys, pickle
from capprobe import *
caps=pickle.load(open("caps_damage_up.pkl","rb"))
i=int(sys.argv[1]); watch=int(sys.argv[2])
(setup,seed,swap),out,surv,ticks=caps[i]
eng=Engine("/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/6595578b-476b-499c-ae9d-903b2a7b43bd/scratchpad/libdbg.so")
orig=eng.step; t=[0]; last=[("x",)]
def step(w):
    orig(w); t[0]+=1
    sys.stderr.write("TICK %d\n"%t[0])
    d=eng.unit_destination(w,watch)
    if d!=last[0]:
        sys.stderr.write("WATCH t%d u%d dest %s -> %s pos %s hp %.0f tgt %d\n"%(t[0],watch,last[0],d,tuple(round(v) for v in eng.unit_pos(w,watch)),eng.unit_hp(w,watch),eng.unit_target(w,watch)))
        last[0]=d
eng.step=step
F.fight(setup,seed,swap,eng)
