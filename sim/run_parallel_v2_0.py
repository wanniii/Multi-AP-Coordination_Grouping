"""
100 회 반복 병렬 실행기  (run_parallel_v2_0.py, v2.0 용 — 10/2)

    python run_parallel.py                 실험 1 (부하 7개 × 4모델 × N회), 결과 results.json + fig_*.png
    python run_parallel.py --n 100         반복 횟수 지정 (기본 100)
    python run_parallel.py --ll            실험 2 (저지연 비율) 도 실행 → results_ll.json + fig_ll_*.png
    python run_parallel.py --workers 8     프로세스 수 (기본: CPU 코어 수)

  v1.9 설정을 명령줄에서 바꿀 수 있다 (기본값은 시뮬레이터 파일의 값):
    --tdma lee|lee-equal|equal   Co-TDMA 시간 배분 (기본 lee = Lee et al. 스케줄링, lee-equal = Lee 절차 + 균등 분배)
    --tdma-share K          Co-TDMA TXOP 당 AP 수 상한 (기본 None. lee-equal · equal 이면 5 권장)
    --csma edca|dcf         CSMA/CA 경쟁 파라미터 (기본 edca)

trial 하나(= 한 seed, 한 부하, 한 모델) 를 작업 단위로 모든 코어에 나눠 돌린다. seed 는 0..N-1 로 고정.
Windows 는 프로세스를 spawn 으로 만들어 부모의 모듈 변수를 물려받지 않으므로, 설정값은 작업마다 넘겨서 워커 안에서 적용한다.
"""
import sys, time, json, argparse
from multiprocessing import Pool, cpu_count
import numpy as np
try:
    import mapc_grouping_HMAB_v2_0 as M      # 시뮬레이터 파일 이름 (v2.0 = group-wait 기본)
except ImportError:
    import mapc as M

KW = dict(n_ap=M.N_AP, n_sta=M.N_STA, k=M.K, ll_ratio=M.LL_RATIO, area=M.AREA, d_sta=M.D_STA)
KEYS = [p[0] for p in M.PANELS] + M.EXTRA_KEYS


def apply_settings(cfg):
    """워커 프로세스 안에서 시뮬레이터 설정을 적용한다 (spawn 이라 매 작업마다)."""
    M.CSMA_EDCA = cfg['csma_edca']
    M.TDMA_SCHED = cfg['tdma_sched']
    M.TDMA_MAX_SHARE = cfg['tdma_max_share']
    M.N_LL_EXACT = cfg['n_ll_exact']


def one(task):
    mid, x, seed, mode, cfg = task
    cfg = dict(cfg)
    if mode == 'll':
        cfg['n_ll_exact'] = int(round(x * M.N_AP * M.N_STA))   # 실험 2: 정확한 저지연 STA 수 (9/10)
        load = M.LL_LOAD_TOTAL
    else:
        cfg['n_ll_exact'] = None
        load = x
    apply_settings(cfg)
    if mid == 'mab':
        r = M.simulate_mab(seed, reward='cls', total_load=float(load), **KW)
    else:
        r = M.simulate(mid, seed, total_load=float(load), **KW)
    return (mid, x, seed, {k: float(r[k]) for k in KEYS if k in r})


def run(mode, n, workers, cfg):
    xs = M.LOADS if mode == 'load' else M.LL_RATIOS
    tasks = [(mid, x, s, mode, cfg) for x in xs for mid, *_ in M.MODELS for s in range(n)]
    print(f'[{mode}] 작업 {len(tasks)}개, 프로세스 {workers}개, 설정 {cfg}', flush=True)
    t0 = time.time(); acc = {}
    with Pool(workers) as pool:
        for i, (mid, x, seed, r) in enumerate(pool.imap_unordered(one, tasks, chunksize=2), 1):
            acc.setdefault((mid, x), []).append(r)
            if i % max(len(tasks) // 20, 1) == 0:
                el = time.time() - t0
                print(f'  {i}/{len(tasks)}  경과 {el/60:.1f}분, 예상 남은 {el/i*(len(tasks)-i)/60:.1f}분', flush=True)
    lab = {mid: l for mid, l, *_ in M.MODELS}
    R = {lab[mid]: {k: [] for k in KEYS} for mid, *_ in M.MODELS}
    CI = {lab[mid]: {k: [] for k in KEYS} for mid, *_ in M.MODELS}
    for x in xs:
        for mid, *_ in M.MODELS:
            rs = acc[(mid, x)]
            for k in KEYS:
                v = np.array([r.get(k, 0.0) for r in rs])
                R[lab[mid]][k].append(float(v.mean()))
                CI[lab[mid]][k].append(float(1.96 * v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0)
    print(f'[{mode}] 완료 {(time.time()-t0)/60:.1f}분', flush=True)
    return R, CI


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=100)
    ap.add_argument('--workers', type=int, default=cpu_count())
    ap.add_argument('--ll', action='store_true')
    ap.add_argument('--tdma', choices=['lee', 'lee-equal', 'equal'], default=M.TDMA_SCHED)
    ap.add_argument('--tdma-share', type=int, default=M.TDMA_MAX_SHARE)
    ap.add_argument('--csma', choices=['edca', 'dcf'], default='edca' if M.CSMA_EDCA else 'dcf')
    a = ap.parse_args()
    cfg = dict(csma_edca=(a.csma == 'edca'), tdma_sched=a.tdma, tdma_max_share=a.tdma_share, n_ll_exact=None)
    meta = dict(n_trial=a.n, POWER_MODE=M.POWER_MODE, P_LL=M.P_LL, WALL_LOSS_DB=M.WALL_LOSS_DB, CSMA_EDCA=cfg['csma_edca'],
                CSMA_STD_TXOP_LIMIT=M.CSMA_STD_TXOP_LIMIT, TDMA_SCHED=cfg['tdma_sched'], TDMA_MAX_SHARE=cfg['tdma_max_share'],
                T_EDCA_ACCESS_us=M.T_EDCA_ACCESS * 1e6, LL_INTRA=M.LL_INTRA, CENTER_SEP_DBM=M.CENTER_SEP_DBM)
    R, CI = run('load', a.n, a.workers, cfg)
    M.print_tables(R, M.LOADS); M.plot(R, M.LOADS)
    json.dump(dict(loads=M.LOADS, results=R, ci95=CI, **meta), open('results.json', 'w'), indent=1)
    print('results.json, fig_*.png 저장')
    if a.ll:
        R2, CI2 = run('ll', a.n, a.workers, cfg)
        M.print_ll_tables(R2); M.plot_ll(R2)
        json.dump(dict(ratios=M.LL_RATIOS, results=R2, ci95=CI2, **meta), open('results_ll.json', 'w'), indent=1)
        print('results_ll.json, fig_ll_*.png 저장')
