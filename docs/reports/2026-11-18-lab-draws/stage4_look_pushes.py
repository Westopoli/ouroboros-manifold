import json, math, sys
from collections import Counter, defaultdict
d = json.load(open(sys.argv[1])); frames = d["frames"]
def dist(a,b): return math.hypot(a["x"]-b["x"], a["y"]-b["y"])
# role speed = most common large step
steps = defaultdict(Counter)
prev=None
for fr in frames:
    U={u["id"]:u for u in fr["units"]}
    if prev:
        for u in fr["units"]:
            p=prev.get(u["id"])
            if p and u["alive"]:
                s=round(dist(u,p),1)
                if s>1.5: steps[u["role"]][s]+=1
    prev=U
speed={r:c.most_common(1)[0][0] for r,c in steps.items()}
print(d["layout_id"],"role step per tick (most common):",speed)
E_alone=E_near=0; F_full=F_small_alone=F_small_near=0; exE=[]; exF=[]
last_shot={}; prev=None
runs=Counter(); longest=Counter(); mind={}; total_ut=0; pairs_side=Counter()
for fr in frames:
    t=fr["tick"]; U={u["id"]:u for u in fr["units"]}; alive=[u for u in fr["units"] if u["alive"]]
    if prev:
        for u in alive:
            p=prev.get(u["id"])
            if not p: continue
            moved=dist(u,p)
            near=min([dist(p,o) for o in prev.values() if o["alive"] and o["id"]!=u["id"]] or [9e9])
            if u.get("fired") and u["target"] is not None:
                if moved>0.5:
                    if near<=34: E_near+=1
                    else:
                        E_alone+=1
                        if len(exE)<8: exE.append((t,u["id"],u["role"],round(moved,2),round(near,1)))
                last_shot[u["id"]]=t
            ls=last_shot.get(u["id"])
            if ls is not None and 0<t-ls<=9 and moved>1.0:
                if moved>=0.9*speed.get(u["role"],99):
                    F_full+=1
                    if len(exF)<10: exF.append((t,u["id"],u["role"],round(moved,2),t-ls,round(near,1)))
                elif near<=34: F_small_near+=1
                else: F_small_alone+=1
    now=set()
    for i,a in enumerate(alive):
        for b in alive[i+1:]:
            if a["layer"]==b["layer"] and abs(a["x"]-b["x"])<28 and abs(a["y"]-b["y"])<28:
                dd=dist(a,b)
                if dd<28:
                    k=(a["id"],b["id"]); now.add(k); mind[k]=min(mind.get(k,99),dd)
    for k in list(runs):
        if k not in now: del runs[k]
    for k in now:
        runs[k]+=1; longest[k]=max(longest[k],runs[k])
        if runs[k]>3: total_ut+=1
    prev=U
print("E fired on a tick it moved: with a unit within 34 wu (push possible)",E_near,"| with nobody near",E_alone,exE)
print("F moved within 9 ticks of a shot: full own-speed steps",F_full,exF,"| small steps with a unit near",F_small_near,"| small steps alone",F_small_alone)
L=[(v,k,round(mind[k],1)) for k,v in longest.items() if v>3]
L.sort(reverse=True)
sides={u["id"]:u["side"] for u in frames[0]["units"]}
print("J pairs under 28 wu for more than 3 ticks:",len(L),"| pair-ticks beyond the third:",total_ut,"| longest runs (ticks, pair, closest wu, sides):",[(v,k,m,sides[k[0]]+sides[k[1]]) for v,k,m in L[:8]])
print("   run-length histogram:",sorted(Counter(min(v//10*10,100) for v,k,m in L).items()), "| closest under 15 wu:",sum(1 for v,k,m in L if m<15))
