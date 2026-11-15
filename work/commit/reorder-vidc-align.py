import sys
p=sys.argv[1]
L=[l for l in open(p).read().splitlines() if l.strip() and not l.startswith('#')]
subj=lambda l: l.split(' ',2)[2].removeprefix('# ').removesuffix(' # empty')
x=[l for l in L if subj(l)=="msm: vidc: Use legacy NV12 alignment on SDM670"][0]; L.remove(x)
i=[i for i,l in enumerate(L) if subj(l)=="=== Samsung gts4lv device support ==="][0]; L.insert(i,x)
open(p,'w').write('\n'.join(L)+'\n')
