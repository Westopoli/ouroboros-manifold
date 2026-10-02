# Quick check: per-layer binary open/blocked maps for a space battlefield.
# Compares (A) independent 2D noise per layer with (B) one 3D noise cut into five slices.
import numpy as np, collections, sys
N=160; L=5            # 160 cells x 100 wu = 16,000 wu canvas, five layers
def smooth(shape, cells, rng):
    # value noise: random lattice, smoothstep-interpolated up to `shape`
    g=rng.random([c+2 for c in cells]); idx=[np.linspace(0,c,s,endpoint=False) for c,s in zip(cells,shape)]
    out=g
    for ax,(ix,c) in enumerate(zip(idx,cells)):
        i0=np.floor(ix).astype(int); t=ix-i0; t=t*t*(3-2*t)
        a=np.take(out,i0,axis=ax); b=np.take(out,i0+1,axis=ax)
        sh=[1]*out.ndim; sh[ax]=-1; t=t.reshape(sh)
        out=a*(1-t)+b*t
    return out
def field3d(rng, zcells):
    f=0.65*smooth((L,N,N),(zcells,5,5),rng)+0.35*smooth((L,N,N),(zcells*2,14,14),rng)
    return f
def field2d(rng):
    return np.stack([0.65*smooth((N,N),(5,5),rng)+0.35*smooth((N,N),(14,14),rng) for _ in range(L)])
def stats(open_):
    tot=open_.sum(); seen=np.zeros_like(open_,bool); best=0; comps=0
    for s in zip(*np.nonzero(open_)):
        if seen[s]: continue
        comps+=1; q=collections.deque([s]); seen[s]=True; n=0
        while q:
            z,y,x=q.popleft(); n+=1
            for dz,dy,dx in ((0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,0,0),(-1,0,0)):
                a,b,c=z+dz,y+dy,x+dx
                if 0<=a<L and 0<=b<N and 0<=c<N and open_[a,b,c] and not seen[a,b,c]:
                    seen[a,b,c]=True; q.append((a,b,c))
        best=max(best,n)
    cross=(open_[:-1]&open_[1:]).mean()          # share of positions where two neighbouring layers are both open
    # per-layer largest component without vertical moves, averaged
    return tot/open_.size, best/max(tot,1), comps, cross
print("mode  blocked%  open%  biggest_open_region%  regions  crossable%")
for name,mk in (("A 2D per layer",lambda r:field2d(r)),("B 3D slices  ",lambda r:field3d(r,2))):
    for target in (0.15,0.35,0.55,0.70):
        rows=[]
        for seed in range(6):
            f=mk(np.random.default_rng(seed)); thr=np.quantile(f,target)   # block the lowest `target` share
            rows.append(stats(f>thr))
        m=np.mean(rows,axis=0)
        print(f"{name}  {target*100:5.0f}   {m[0]*100:5.1f}   {m[1]*100:6.1f}            {m[2]:5.1f}   {m[3]*100:5.1f}")
