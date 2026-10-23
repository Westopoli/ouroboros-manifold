import sys; sys.path.insert(0,'.'); sys.path.insert(0,'experiments')
import numpy as np
import b1_choke as c
from layerlab.run import run
def look(name, build, n):
    res=run(build(n,False),seed=0,trace=True); tr=res.trace; side=tr['side'][0]; fire=(tr['flags']&16)!=0; alive=tr['alive']!=0
    if not fire.any(): print(name,'no firing; winner',res.winner,res.survivors); return
    first=int(np.argmax(fire.any(axis=1)))
    print(f"{name}: v {n}, winner {res.winner}, survivors {res.survivors}, ticks {res.ticks}")
    for t in (first+40,first+120,first+300,first+600):
        if t<len(tr):
            th=[float(x) for x,a,s in zip(tr['x'][t],alive[t],side) if s==1 and a]
            print(f"   t={t}: ours firing {int(fire[t][side==0].sum())}/{int(alive[t][side==0].sum())}  theirs {int(fire[t][side==1].sum())}/{int(alive[t][side==1].sum())}  their front x {min(th):.0f}" if th else f"   t={t}: enemy dead")
if __name__=='__main__':
    sit=c.lane_sit(); n=int(sys.argv[1]) if len(sys.argv)>1 else 32
    look('arc R190 x12, walls block sight', c.with_walls(c.arc_build(sit,12,((190.0,12),)),sit), n)
    look('arc R190 x12 + R140 x4, walls block sight', c.with_walls(c.arc_build(sit,16),sit), n)
    look('lab S1 block, walls block sight', c.with_walls(c.lab_build(sit,16,frozenset({'S1'})),sit), n)
    look('both walk in, walls block sight', c.with_walls(c.lab_build(sit,16,frozenset()),sit), n)
