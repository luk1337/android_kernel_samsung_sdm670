import sys
p=sys.argv[1]
L=[l for l in open(p).read().splitlines() if l.strip() and not l.startswith('#')]
subj=lambda l: l.split(' ',2)[2].removeprefix('# ').removesuffix(' # empty')
def mv(s, before):
    x=[l for l in L if subj(l)==s][0]; L.remove(x)
    i=[i for i,l in enumerate(L) if subj(l)==before][0]; L.insert(i,x)
mv("msm: camera: eeprom: Don't fail on positive read_seq return values", "=== Samsung gts4lv device support ===")
mv("msm: camera: eeprom: Support Samsung's addressed memory map layout", "=== Temporary bring-up hacks ===")
open(p,'w').write('\n'.join(L)+'\n')
