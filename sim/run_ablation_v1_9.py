"""
구성 요소별 기여(ablation) 병렬 실행기  (v1.9 용, 9/14)

    python run_ablation_v1_9.py                 1000 Mbps, 8 변형 × N회 → ablation.json + 표 출력
    python run_ablation_v1_9.py --n 100         반복 횟수 (기본 100)
    python run_ablation_v1_9.py --load 800      로드 변경
    python run_ablation_v1_9.py --workers 8     프로세스 수

변형 (표 4 순서):
    conv-csr            Co-SR
    conv-tdma           Co-TDMA
    rule                Proposed (Rule-based)                 : priority 슬롯 + Medium Time 슬롯 + Park 전력
    rule-k20            Rule-based, AP 마다 독립 그룹 (그룹핑 제거)
    ml-slot             ML-based, 슬롯 학습만 (전력은 Park 규칙)    ← 슬롯 학습의 기여
    ml                  Proposed (ML-based)                   ← 전력 학습의 기여
    ml-k20              ML-based, AP 마다 독립 그룹 (그룹핑 제거)   ← 그룹핑의 기여
    ml-k1               ML-based, 전체 한 그룹 (항상 Case 2)

seed 는 run_parallel 과 같이 0..N-1. 설정값은 작업마다 넘겨서 워커 안에서 적용한다 (Windows spawn 대응).
"""
import time, json, argparse
from multiprocessing import Pool, cpu_count
import numpy as np
import mapc_grouping_HMAB_v1_9 as M

KEYS = ['tp', 'lat_ll', 'loss_ll', 'lat', 'loss', 'n_groups', 'g_ll0', 'g_ll1', 'g_ll2']
VARIANTS = [   # (id, 표시 이름, 모델, k, POWER_MODE)
    ('conv-csr',  'Co-SR',                              'conv-csr',  M.K,  'joint'),
    ('conv-tdma', 'Co-TDMA',                            'conv-tdma', M.K,  'joint'),
    ('rule',      'Proposed (Rule-based)',              'proposed',  None, 'joint'),
    ('rule-k20',  'Rule-based, no grouping (k=20)',     'proposed',  20,   'joint'),
    ('ml-slot',   'ML-based, slot learning only',       'mab',       None, 'rule'),
    ('ml',        'Proposed (ML-based)',                'mab',       None, 'joint'),
    ('ml-k20',    'ML-based, no grouping (k=20)',       'mab',       20,   'joint'),
    ('ml-k1',     'ML-based, single group (k=1)',       'mab',       1,    'joint'),
]


def one(task):
    vid, model, k, pmode, seed, load = task
    M.POWER_MODE = pmode
    M.N_LL_EXACT = None
    kw = dict(n_ap=M.N_AP, n_sta=M.N_STA, k=k, ll_ratio=M.LL_RATIO, area=M.AREA, d_sta=M.D_STA, total_load=float(load))
    r = M.simulate_mab(seed, reward='cls', **kw) if model == 'mab' else M.simulate(model, seed, **kw)
    return (vid, seed, {key: float(r[key]) for key in KEYS if key in r})


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=100)
    ap.add_argument('--load', type=float, default=1000.0)
    ap.add_argument('--workers', type=int, default=cpu_count())
    a = ap.parse_args()
    tasks = [(vid, model, k, pm, s, a.load) for vid, _, model, k, pm in VARIANTS for s in range(a.n)]
    print(f'작업 {len(tasks)}개, 프로세스 {a.workers}개, 로드 {a.load} Mbps', flush=True)
    t0 = time.time(); acc = {}
    with Pool(a.workers) as pool:
        for i, (vid, seed, r) in enumerate(pool.imap_unordered(one, tasks, chunksize=2), 1):
            acc.setdefault(vid, []).append(r)
            if i % max(len(tasks) // 20, 1) == 0:
                el = time.time() - t0
                print(f'  {i}/{len(tasks)}  경과 {el/60:.1f}분, 예상 남은 {el/i*(len(tasks)-i)/60:.1f}분', flush=True)
    R, CI = {}, {}
    for vid, name, *_ in VARIANTS:
        rs = acc[vid]
        R[name] = {key: float(np.mean([r.get(key, 0.0) for r in rs])) for key in KEYS}
        CI[name] = {key: float(1.96 * np.std([r.get(key, 0.0) for r in rs], ddof=1) / np.sqrt(len(rs))) if len(rs) > 1 else 0.0
                    for key in KEYS}
    print(f'\n완료 {(time.time()-t0)/60:.1f}분   (로드 {a.load:.0f} Mbps, {a.n}회 평균 ± 95% CI)')
    print(f'{"variant":<36} {"tp(Mbps)":>14} {"lat_ll(ms)":>14} {"loss_ll(%)":>14} {"groups":>7}')
    for _, name, *_ in VARIANTS:
        m, c = R[name], CI[name]
        print(f'{name:<36} {m["tp"]:>7.1f} ±{c["tp"]:<5.1f} {m["lat_ll"]:>7.2f} ±{c["lat_ll"]:<5.2f} '
              f'{m["loss_ll"]:>7.2f} ±{c["loss_ll"]:<5.2f} {m["n_groups"]:>7.1f}')
    json.dump(dict(load=a.load, n_trial=a.n, results=R, ci95=CI, P_LL=M.P_LL, CENTER_SEP_DBM=M.CENTER_SEP_DBM),
              open('ablation.json', 'w'), indent=1)
    print('ablation.json 저장')
