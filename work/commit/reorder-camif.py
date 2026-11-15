import sys
p=sys.argv[1]
L=[l for l in open(p).read().splitlines() if l.strip() and not l.startswith('#')]
subj=lambda l: l.split(' ',2)[2].removeprefix('# ').removesuffix(' # empty')
def move(s, before):
    x=[l for l in L if subj(l)==s][0]; L.remove(x)
    i=[i for i,l in enumerate(L) if subj(l)==before][0]; L.insert(i,x)
move("msm: camera: vfe170: Subscribe to CAMIF SOF/EPOCH/RUP IRQs", "=== Samsung gts4lv device support ===")
x=[l for l in L if subj(l)=="msm: camera: req_mgr: Accept the legacy link_control layout"][0]; L.remove(x)
i=[i for i,l in enumerate(L) if subj(l)=="msm: camera: req_mgr: Accept the legacy sched_request layout"][0]; L.insert(i+1,x)
open(p,'w').write('\n'.join(L)+'\n')
