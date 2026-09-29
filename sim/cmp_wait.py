"""LL_INTRA 'tdma'(G1 대기) vs 'group'(G1 동시 전송, Case 2 취급) 빠른 비교. ML 모델만."""
import time, json, sys
from multiprocessing import Pool
import numpy as np
import mapc_grouping_HMAB_v1_9 as M
KEYS = ['tp','lat_ll','loss_ll','lat','loss','g_ll0','g_ll1','g_ll2']
def one(task):
    intra, seed, load, nll = task
    M.LL_INTRA = intra; M.POWER_MODE = 'joint'; M.N_LL_EXACT = nll
    kw = dict(n_ap=M.N_AP, n_sta=M.N_STA, k=None, ll_ratio=M.LL_RATIO, area=M.AREA, d_sta=M.D_STA, total_load=float(load))
    r = M.simulate_mab(seed, reward='cls', **kw)
    return (intra, load, nll, seed, {k: float(r[k]) for k in KEYS if k in r})
if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    scen = [(1000.0, None), (800.0, 20)]   # (로드, 저지연 STA 수) : 실험1 1000Mbps(P_LL=0.25), 실험2 50%
    tasks = [(i, s, L, nll) for i in ('tdma','group') for (L,nll) in scen for s in range(n)]
    t0=time.time(); acc={}
    with Pool(4) as p:
        for intra, L, nll, seed, r in p.imap_unordered(one, tasks, chunksize=1):
            acc.setdefault((intra,L,nll), []).append(r)
            print(f'  done {intra} L={L:.0f} nll={nll} seed={seed}  {(time.time()-t0)/60:.1f}min', flush=True)
    out={}
    for key, rs in sorted(acc.items(), key=lambda x: (x[0][1], x[0][2] or 0, x[0][0])):
        m={k: float(np.mean([x[k] for x in rs])) for k in KEYS}
        out[str(key)] = m
        print(f"{key}: n={len(rs)} tp={m['tp']:.1f} lat_ll={m['lat_ll']:.2f} loss_ll={m['loss_ll']:.2f} lat_all={m['lat']:.1f} loss_all={m['loss']:.1f} case0/1/2={m['g_ll0']:.2f}/{m['g_ll1']:.2f}/{m['g_ll2']:.2f}")
    json.dump(out, open('cmp_wait.json','w'), indent=1)
