"""Design chat (b1): a tight arc at reach around the corridor mouth, walls blocking sight. Prediction to test: with the
attackers held to c units firing and D defenders all firing, the defenders beat about D(D+1)/(2c)."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'experiments')
import b1_choke as c, b1_look as L
if __name__=='__main__':
    for unit,R,k,heads in (('raider',190.0,8,[6,8,9,10,11,12,14,16,20,24]),('warden',335.0,14,[12,14,18,22,26,30,36,44,56])):
        sit=c.lane_sit(unit)
        b=c.with_walls(c.arc_build(sit,k,((R,k),),arc=120.0,unit=unit),sit)
        L.look(f'{unit}: {k} in a 120-degree arc at {R:.0f}', b, heads[len(heads)//2])
        c.table(f'{unit} (range {"200" if unit=="raider" else "350"}): {k} hold an arc around the mouth, walls block sight', b, k, heads, 10)
        nb=c.with_walls(c.lab_build(sit,k,frozenset()),sit)
        c.table(f'{unit}: {k} walk in against the same enemy (no skill)', nb, k, heads[:6], 10)
