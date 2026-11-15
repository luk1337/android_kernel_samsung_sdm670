import sys
p=sys.argv[1]
L=[l for l in open(p).read().splitlines() if l.strip() and not l.startswith('#')]
subj=lambda l: l.split(' ',2)[2].removeprefix('# ').removesuffix(' # empty')
for s in ["arm64: dts: qcom: sdm670-camera: Add IPE write constituent paths",
          "msm: camera: icp: Allow skipping the FW mem map command",
          "arm64: dts: qcom: sdm670-camera: Make camera SMMU faults non-fatal",
          "msm: camera: vfe_bus_ver2: Take UBWC config from the plane config"]:
    x=[l for l in L if subj(l)==s][0]; L.remove(x)
    i=[i for i,l in enumerate(L) if subj(l)=="=== Samsung gts4lv device support ==="][0]; L.insert(i,x)
open(p,'w').write('\n'.join(L)+'\n')
