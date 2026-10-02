"""Design chat (b1): defenders start in an arc around the mouth and step forward to engage (hold + chase when idle),
walls blocking sight. Tests whether a choke caps the attackers' firing count."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'experiments')
import b1_choke as c, b1_look as L
def chase(build):
    def b(n, swap):
        scn = build(n, swap); scn["rules"] = dict(scn.get("rules", {}), chase_when_idle=1); return scn
    return b
if __name__=='__main__':
    sit=c.lane_sit('raider')
    for k,rings in ((12,((190.0,12),)),(16,((190.0,12),(250.0,4)))):
        b=chase(c.with_walls(c.arc_build(sit,k,rings,arc=170.0),sit))
        L.look(f'{k} raiders around the mouth, stepping forward to engage', b, 2*k)
        c.table(f'{k} raiders hold the mouth and step forward to engage; walls block sight', b, k, [k, int(1.25*k), int(1.5*k), int(1.75*k), 2*k, int(2.5*k), 3*k, 4*k], 10)
    nb=chase(c.with_walls(c.lab_build(sit,16,frozenset()),sit))
    c.table('16 raiders walk in to meet the enemy (no skill), same rules', nb, 16, [12,14,16,20,24], 10)
