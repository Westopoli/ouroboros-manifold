import subprocess,sys,functools,re
def g(*a):
    r=subprocess.run(['git']+list(a),capture_output=True,text=True);return r.stdout.strip() if r.returncode==0 else None
@functools.lru_cache(None)
def mainblobs(path):
    s=set()
    for c in (g('rev-list','origin/main','--',path) or '').split():
        b=g('rev-parse',f'{c}:{path}')
        if b:s.add(b)
    return s
pt=open('docs/northstar/plans/push/pieces.toml').read()+open('docs/northstar/plans/push_ledger_2026-09-22.md').read()
for b in open('/tmp/fam.txt').read().split():
    tip=g('rev-parse','--short',b);mb=g('merge-base','origin/main',b)
    subj=g('log','-1','--format=%s',b)
    files=(g('diff','--name-only',mb,b) or '').split('\n')
    files=[f for f in files if f]
    fail=None;kinds=set()
    for f in files:
        bl=g('rev-parse',f'{b}:{f}')
        if bl:
            if bl in mainblobs(f):kinds.add('i')
            else: fail=f;break
        else:
            if g('cat-file','-e',f'origin/main:{f}') is not None or subprocess.run(['git','cat-file','-e',f'origin/main:{f}'],capture_output=True).returncode==0:
                fail=f+' (deleted on branch, present on main)';break
            kinds.add('ii')
    print('|'.join([b.replace('origin/',''),tip,str(len(files)),'PROVEN' if not fail else 'NOT',(','.join(sorted(kinds)) if not fail else fail),subj[:70]]))
