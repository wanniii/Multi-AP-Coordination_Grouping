"""Distributed traffic mode: LS 없는 그룹이 priority slot 동안 대기('tdma') vs 처음부터 동시 전송('group').
실험1(로드 400~1000, LS 25%)과 실험2(800 Mbps, LS 10~50%) 전 구간, RL 모델. 결과 cmp_wait_sweep_n%d.json"""
import time, json, sys
from multiprocessing import Pool
import numpy as np
import mapc_grouping_HMAB_v1_9 as M
KEYS = ['tp','lat_ll','loss_ll','lat','loss','g_ll0','g_ll1','g_ll2']
LOADS  = [400,500,600,700,800,900,1000]
RATIOS = [0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50]
def one(task):
    intra, exp, x, seed = task
    M.LL_INTRA = intra; M.POWER_MODE = 'joint'
    if exp == 'load':
        M.N_LL_EXACT = None; load = float(x)
    else:
        M.N_LL_EXACT = int(round(x * M.N_AP * M.N_STA)); load = float(M.LL_LOAD_TOTAL)
    kw = dict(n_ap=M.N_AP, n_sta=M.N_STA, k=None, ll_ratio=M.LL_RATIO, area=M.AREA, d_sta=M.D_STA, total_load=load)
    r = M.simulate_mab(seed, reward='cls', **kw)
    return (intra, exp, x, seed, {k: float(r[k]) for k in KEYS if k in r})
if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    tasks = [(i, 'load', L, s) for i in ('tdma','group') for L in LOADS for s in range(n)] + \
            [(i, 'll', r, s) for i in ('tdma','group') for r in RATIOS for s in range(n)]
    print(f'tasks {len(tasks)}', flush=True)
    t0=time.time(); acc={}
    with Pool(4) as p:
        for i,(intra, exp, x, seed, r) in enumerate(p.imap_unordered(one, tasks, chunksize=2),1):
            acc.setdefault((intra,exp,x), []).append(r)
            if i % 50 == 0: print(f'  {i}/{len(tasks)}  {(time.time()-t0)/60:.1f} min', flush=True)
    out = {'n_trial': n, 'loads': LOADS, 'ratios': RATIOS, 'results': {}, 'ci95': {}}
    for intra in ('tdma','group'):
        for exp, xs in (('load',LOADS),('ll',RATIOS)):
            for k in KEYS:
                out['results'].setdefault(intra,{}).setdefault(exp,{})[k] = [float(np.mean([r[k] for r in acc[(intra,exp,x)]])) for x in xs]
                out['ci95'].setdefault(intra,{}).setdefault(exp,{})[k] = [float(1.96*np.std([r[k] for r in acc[(intra,exp,x)]],ddof=1)/np.sqrt(n)) for x in xs]
    json.dump(out, open("cmp_wait_sweep_n%d.json" % n, "w"), indent=1)
    print(f'done {(time.time()-t0)/60:.1f} min', flush=True)
