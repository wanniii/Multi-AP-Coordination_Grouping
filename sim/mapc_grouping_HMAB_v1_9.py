"""
════════════════════════════════════════════════════════════════════════════
 MAPC 저지연 인지 협력 전송 시뮬레이터
════════════════════════════════════════════════════════════════════════════

 이 파일 하나로 종래 3 모델 + 제안(rule) + 제안(MAB) 의 실험과 그래프가 모두 나온다 (9/9 통합).
     python mapc.py            전체 실험 (부하 7 개 × 반복 N_TRIAL 회)
     python mapc.py --quick    빠른 확인 (부하 3 개 × 3 회)
 대량 반복(100 회) 은 run_parallel.py (평균 + 95 % CI 를 results.json 에 저장).

────────────────────────────────────────────────────────────────────────────
 제안 모델

   ① Master AP 가 각 AP 로부터 RSSI(섀도잉 포함) 와 트래픽 요구량을 수집한다
   ② RSSI 클러스터링으로 지리 그룹(BSS 들의 집합)을 만든다 (배치마다 1 회, 그 안에서 고정)
        부하율(STA 요구량 합 / 단독 링크 용량)이 낮은 = 가용 자원이 많은 AP 부터 센터 후보,
        기존 센터로부터 RSSI < CENTER_SEP_DBM 이면 새 센터
        1 대짜리 그룹도 허용한다 (주변에 가까운 AP 가 없으면 단독 그룹, 최대 전력 단독 전송)
   ③ 매 TXOP, 보낼 데이터가 있는 AP 만 활성. 저지연 큐가 있는 STA 를 가진 AP 는 "저지연 트래픽을 서비스하는 AP".
        (저지연 요구의 주체는 STA, 조율·전송의 주체는 AP — 9/10 교수님)
   ④ Case 판정 (교수님 8/19, 판정 기준은 9/10 피드백대로 "지금 저지연 STA 를 서비스하는 AP")
        저지연 서비스 AP 2 대 이상이 전부 한 그룹에   → Case 2
            그 그룹은 AP 마다 슬롯을 나눠 순차 전송 (c-TDMA), 나머지 그룹은 모든 슬롯 동시 전송 (c-SR)
        그 외 (여러 그룹에 흩어짐, 또는 1 대 이하)     → Case 1
            저지연 슬롯 = 저지연 서비스 AP 만 전송(나머지는 대기), 마지막 슬롯 = 활성 전원 동시
        저지연 그룹이 여럿인 혼합 상황은 ② 로 확정 (LL_INTRA='tdma', 9/11). ③ 은 비교용
   ⑤ 슬롯에 혼자 보내는 AP 는 전력을 낮추지 않는다 (멘토님 9/3 "나만 보내면 맥스 파워")
   ⑥ 그룹끼리는 동시 전송한다 (Case 1 의 저지연 슬롯 제외 — 그때는 저지연 서비스 AP 만 전송)
   ⑦ 슬롯 길이 · 전력
        rule (ablation) : 802.11e 수락 제어 기반 Medium Time / S.Park 기고문 전력 제어
        MAB (제안)      : Master AP 가 슬롯 길이(2단계)와 그룹 단위 전력 조합을 UCB 로 학습 (7절)
   ⑧ 측정 (9/10)
        손실·지연 : 생성 시각이 [warm-up 끝, 시뮬 끝 − 최대 마감) 인 패킷만 (코호트).
                    손실 = (재전송 한도 초과 + 마감 초과) / 생성  ← 마감 인지 손실률
        처리량    : 전달 완료 시각이 측정 구간 안인 비트

 트래픽: STA 마다 독립적으로 P_LL(25 %) 로 저지연 앱(RTMG/VR/VC), 아니면 배경 (9/10 교수님: 주체는 STA).
   한 AP 에 저지연·일반 STA 가 섞일 수 있고, AP 는 저지연 STA 에게 보낼 데이터가 있는 TXOP 에 저지연 슬롯을 받는다.
   Case 는 저지연 트래픽의 공간 분포에서 자연히 생김 (인위적 집중 배치 없음).
   (멘토님 9/3 "케이스를 나눠서 실험하지 말고 매 라운드 배치가 랜덤")

────────────────────────────────────────────────────────────────────────────
 비교 모델 (그룹핑 없음, 균등 슬롯 — 멘토님 2026-09-04. 9/12 표준 정합 재구현)
   CSMA/CA      협력 없음. IEEE 802.11-2020 EDCA (§10.23) 를 그대로 따른다.
                  · 보낼 데이터가 있는 AP 들이 head STA 트래픽의 AC (VO/VI/BE) 로 경쟁. CW·AIFSN = Table 9-155
                  · 매 접근마다 승자 1 대 (Bianchi 고정점의 AC 별 성공 확률로 추첨), 나머지는 대기
                  · 경쟁 비용 = 유휴 슬롯 + 충돌 시간 기댓값 (Bianchi), 충돌 길이 = 경쟁 AP 들의 의도 PPDU 길이 평균
                  · 승자는 TXOP limit (VO 2.080 ms, VI 4.096 ms, BE/BK = PPDU 1 개 ≤ 5.484 ms) 안에서 최대 전력 전송
                  · 단일 경쟁 영역 (AP 쌍 99 % 가 CCA −82 dBm 이상). 전송 후 SIFS + BlockAck, 다시 경쟁
                ※ v1.8 까지는 "활성 AP 전원이 매 TXOP 균등 슬롯 + Bianchi 효율 곱" 이어서 Co-TDMA 와 같은 스케줄이었다.
   Co-SR        (only c-SR) 활성 AP 전원이 한 슬롯에 동시 전송, 기고문 전력 제어
   Co-TDMA      (only c-TDMA) IEEE 802.11bn Co-TDMA, Lee et al. (arXiv:2508.18755) Fig. 1 의 절차:
                  TXOP 획득 (T_EDCA_ACCESS) → ICF/ICR 폴링 (T_MAPC_OH) → sharing AP 자기 DL → MU-RTS TXS 트리거 → CTS →
                  shared AP DL → BA (슬롯마다 T_ROUND_OH). shared AP 는 최대 전력. TXOP 당 TDMA_MAX_SHARE 대, 라운드 로빈.
                  시간 배분은 TDMA_SCHED: 'equal' (멘토님 균등 슬롯) / 'lee' (Lee 의 LL 수요 기반 할당). 논문 Table I 트래픽·AC 매핑은 본 코드와 동일.
                  'lee': sharing AP = EDCA 승자 (AC 우선순위 분포, 충돌 비용 없음) → 자기 DL → 남은 시간을 shared AP 의 LL 에 할당 →
                         TXOP 가 남으면 CF-End 후 다음 승자가 새 TXOP (스텝을 채울 때까지). 9/12 100회 실측으로 두 근사를 바로잡음.
   ※ MAPC 세 모델(Co-SR · Co-TDMA · 제안)의 TXOP 획득: 조정 AP(sharing AP) 가 EDCA 로 잡고, 조정 집합의 다른 AP 는
      트리거를 기다리므로 경쟁하지 않는다 (mapc-sim · Wojnar 와 같은 가정). 비용 = AIFS + 평균 백오프 = T_EDCA_ACCESS, TXOP 당 1 회.
      TXOP 안에서 전송하는 AP 는 v1.8 과 같다 (Co-SR · 제안: 활성 AP 전원, Co-TDMA: TXOP 당 TDMA_MAX_SHARE 대 라운드 로빈).

────────────────────────────────────────────────────────────────────────────
 출처
   경로손실·섀도잉 TGax Enterprise (IEEE 802.11-14/0980r16): BP 10 m, 벽 7 dB, 20 m 격자 (9/12 벽 반영)
   소규모 페이딩 Nakagami m=1.5 (Yu et al., arXiv:2506.14187 Table I)
   MCS / 잡음   mapc-sim 오픈소스
   전력 제어    S.Park et al., IEEE 802.11-20/0410r4 (기고문, 표준 아님)
   MAC 타이밍   IEEE 802.11-2020 (SIFS 16us, 슬롯 9us) / 11bn Co-TDMA 폴링
   EDCA 경쟁    IEEE 802.11-2020 §10.23, Table 9-155 (CW · AIFSN · TXOP limit); 충돌 모델 Bianchi (JSAC 2000) 의 AC 별 확장
   CCA          IEEE 802.11-2020 프리앰블 검출 −82 dBm (20 MHz)
   슬롯 배분    IEEE 802.11e TSPEC Medium Time + 수락 제어
   재전송       IEEE 802.11-2020 dot11ShortRetryLimit = 7
   트래픽       Lee et al., arXiv:2508.18755 Table I (RTMG · VR · VC · BG)
                마감: 3GPP TR 26.926 XR / dot11MaxTransmitMSDULifetime 512 TU
 설계 파라미터 (문헌값 아님, 본 연구가 정한 값)
   실험 설정   AP 20 대, 80×80 m, AP 당 STA 2 대, P_LL 25 %, 부하 400~1000 Mbps
   알고리즘    CENTER_SEP_DBM −70 dBm (벽 7 dB 기준 그룹 크기 ~4대), TARGET_SINR 10 dB(종래 c-SR),
               POWER_ARMS {6,12,24} dBm, JOINT_MAX 3, SLOT_ARMS {1..5}, LL_ARMS {10~90 %},
               Q_BUCKETS {100,500}, 보상 가중 ½:½
   튜닝으로 결정  UCB 탐색 계수 C_SLOT · C_POWER (최종 실험에 쓰지 않은 seed 100~114 에서 평균 보상 기준)
════════════════════════════════════════════════════════════════════════════
"""

import sys
import time
from collections import deque, Counter

import numpy as np
from scipy.stats import norm as scipy_norm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ══════════════════════════════════════════════════════════════════════════
# 1. PHY
# ══════════════════════════════════════════════════════════════════════════
MAX_TX_POWER = 24.0        # dBm, EIRP 상한

# ── 실내 채널 (TGax Enterprise 시나리오, IEEE 802.11-14/0980r16) ──
WALL_LOSS_DB   = 7.0       # dB/벽, TGax Enterprise (IEEE 802.11-14/0980r16). 9/12: 0(개방 공간) → 7. 벽이 없으면 AP 간격 18 m 에서
                           #   동시 전송 이득이 없어 Co-SR 계열이 직렬 Co-TDMA 를 못 넘는다 (100회 실측). 0 은 TGax 'Indoor small BSS' 식에 해당.
ROOM_SIZE      = 20.0      # m, 벽이 이 간격으로 격자 배치되어 있다고 본다
SHADOW_SIGMA   = 5.0       # dB, 링크별 섀도잉 표준편차 (TGax Enterprise)
NAKAGAMI_M     = 1.5       # 소규모 페이딩 (Yu et al. 2025 Table I)
MIN_TX_POWER = 1.0         # dBm, 전력 제어 하한
NOISE_FLOOR  = -93.97      # dBm
SIGMA        = 1.6         # dB, SINR → MPDU 성공확률 CDF 의 표준편차 (mapc-sim)
CENTRAL_FREQ = 5.160       # GHz
BP           = 10.0        # m, break-point
NOISE_LIN    = 10 ** (NOISE_FLOOR / 10)
TARGET_SINR  = 10.0        # dB, 종래 c-SR 전력 제어의 목표 SINR (최저 MCS 요구 SINR ≈ 11 dB. 9/8 민감도: 낮을수록 종래에 유리, 10 dB 채택)
RETRY_LIMIT  = 7           # dot11ShortRetryLimit

FRAME_LEN = 1500 * 8       # bits, Ethernet MTU
TAU       = 5.484e-3       # s, TXOP 길이

DATA_RATES = np.array([36.0, 72.1, 108.1, 144.1, 216.2, 288.2, 324.3,
                       360.3, 432.4, 480.4, 540.4, 600.5, 648.5, 720.6])
MEAN_SNRS  = np.array([12.287, 11.475, 11.209, 12.432, 14.802, 18.870, 20.203,
                       21.485, 25.403, 26.908, 34.376, 36.301, 40.107, 42.129])


def db2lin(x):
    return 10.0 ** (x / 10.0)


def lin2db(x):
    return 10.0 * np.log10(max(x, 1e-30))


def path_loss(d):
    """TGax Enterprise 경로손실 (dB), 벽·섀도잉 제외."""
    d = max(d, 1.0)
    return (40.05 + 20 * np.log10(min(d, BP) * CENTRAL_FREQ / 2.4)
            + (35 * np.log10(d / BP) if d > BP else 0.0))


def n_walls(p, q, room=ROOM_SIZE):
    """두 점 사이를 잇는 직선이 지나는 벽(격자선)의 개수."""
    nx = abs(int(np.floor(p[0] / room)) - int(np.floor(q[0] / room)))
    ny = abs(int(np.floor(p[1] / room)) - int(np.floor(q[1] / room)))
    return nx + ny


class Channel:
    """
    링크별 대규모 손실(경로손실 + 벽 + 섀도잉)과 TXOP 마다 새로 뽑는
    소규모 페이딩을 관리한다.

      대규모 : 배치 시 1 회 결정. 전력 제어는 이 값을 기준으로 한다.
      소규모 : 매 TXOP Nakagami-m 에서 새로 뽑아 실제 SINR 에 반영한다.
               → 같은 전력이라도 TXOP 마다 성공/실패가 달라진다.
    """

    def __init__(self, ap_pos, sta_pos, rng):
        n_ap, n_sta = len(ap_pos), len(sta_pos)
        self.rng = rng
        self.L = np.zeros((n_ap, n_sta))            # 대규모 손실 (dB)
        for i in range(n_ap):
            for j in range(n_sta):
                d = np.linalg.norm(ap_pos[i] - sta_pos[j])
                self.L[i, j] = (path_loss(d)
                                + WALL_LOSS_DB * n_walls(ap_pos[i], sta_pos[j])
                                + rng.normal(0.0, SHADOW_SIGMA))
        # AP 끼리 받는 비콘 RSSI 에도 같은 섀도잉 (대칭)
        self.S_ap = np.zeros((n_ap, n_ap))
        for i in range(n_ap):
            for j in range(i + 1, n_ap):
                self.S_ap[i, j] = self.S_ap[j, i] = rng.normal(0.0, SHADOW_SIGMA)
        self.F = np.zeros((n_ap, n_sta))            # 이번 TXOP 의 소규모 페이딩 (dB)
        self.new_txop()

    def rssi_ap(self, i, j, ap_pos):
        """AP j 가 AP i 의 비콘을 받는 세기 (dBm). 경로손실 + 벽 + 섀도잉."""
        d = np.linalg.norm(ap_pos[i] - ap_pos[j])
        return MAX_TX_POWER - path_loss(d) - WALL_LOSS_DB * n_walls(ap_pos[i], ap_pos[j]) + self.S_ap[i, j]

    def new_txop(self):
        """매 TXOP 소규모 페이딩을 새로 뽑는다. Nakagami-m 전력 이득을 dB 로."""
        g = self.rng.gamma(NAKAGAMI_M, 1.0 / NAKAGAMI_M, size=self.F.shape)
        self.F = 10.0 * np.log10(np.maximum(g, 1e-6))

    def loss_mean(self, i, j):
        return self.L[i, j]

    def loss_now(self, i, j):
        return self.L[i, j] - self.F[i, j]


def sinr_from_loss(tx_pow, loss_sig, interferers):
    """interferers = [(전력 dBm, 간섭원→수신기 손실 dB), ...]"""
    sig = db2lin(tx_pow - loss_sig)
    itf = sum(db2lin(p - l) for p, l in interferers)
    return lin2db(sig / (itf + NOISE_LIN))


def link_stats(sinr):
    """SINR → (원시 PHY 전송률 bps, MPDU 1 회 시도 성공확률)."""
    m = int(np.argmax(DATA_RATES * scipy_norm.cdf(sinr, MEAN_SNRS, SIGMA)))
    p = float(scipy_norm.cdf(sinr, MEAN_SNRS[m], SIGMA))
    return float(DATA_RATES[m]) * 1e6, float(np.clip(p, 1e-6, 1.0))


def arq(p, R=RETRY_LIMIT):
    """
    802.11 ARQ. 실패한 MPDU 를 재시도 한도까지 재전송하고 초과하면 폐기한다.
      E[N]    전달 1 건당 평균 전송 시도 수 = TSPEC 의 Surplus Bandwidth Allowance
      discard 전달된 MPDU 대비 재시도 한도 초과 폐기 비율
    유효 처리량은 원시 전송률 x p 가 된다 (재전송 airtime 이 반영된 값).
    """
    P_ok = 1.0 - (1.0 - p) ** R
    E_N = P_ok / p if p > 0 else float('inf')
    discard = (1.0 - P_ok) / P_ok if P_ok > 0 else 1e9
    return E_N, discard


def power_control(tx_pairs, ch):
    """
    Co-SR 전력 제어 — S. Park et al., IEEE 802.11-20/0410r4 (기고문) 방식.
      1) 각 수신 STA 가 목표 SINR 을 유지하며 견딜 수 있는 간섭량을 구한다
      2) 간섭원 수로 나눠 배분한다
      3) 각 AP 는 모든 상대 STA 제약 중 최솟값을 전력 상한으로 받는다
      4) 802.11h TPC 에 맞춰 1 dB 단위로 양자화한다
    대규모 손실(경로손실 + 벽 + 섀도잉)을 기준으로 정하며, 소규모 페이딩은
    알 수 없으므로 반영하지 않는다 (실제 SINR 은 이보다 흔들린다).
    동시 전송 AP 가 1 대뿐이면 전력을 낮출 이유가 없으므로 최대 전력을 쓴다.
    """
    if len(tx_pairs) <= 1:
        return {ap: MAX_TX_POWER for ap, _ in tx_pairs}

    gamma = db2lin(TARGET_SINR)
    n_itf = max(len(tx_pairs) - 1, 1)
    budget = {}
    for ap, sta in tx_pairs:
        sig = db2lin(MAX_TX_POWER - ch.loss_mean(ap, sta))
        budget[ap] = max(sig / gamma - NOISE_LIN, 1e-30) / n_itf

    out = {}
    for ap_j, _ in tx_pairs:
        cons = [lin2db(budget[ap_k]) + ch.loss_mean(ap_j, sta_k)
                for ap_k, sta_k in tx_pairs if ap_k != ap_j]
        out[ap_j] = float(np.clip(round(min(cons)), MIN_TX_POWER, MAX_TX_POWER))
    return out


# ══════════════════════════════════════════════════════════════════════════
# 2. MAC 타이밍 (IEEE 802.11-2020, 5 GHz OFDM)
# ══════════════════════════════════════════════════════════════════════════
SIFS       = 16e-6
SLOT_TIME  = 9e-6
T_PREAMBLE = 20e-6         # legacy preamble + SIGNAL
BASIC_RATE = 24e6          # bps, 제어 프레임 전송률


def ctrl_time(n_bytes):
    return T_PREAMBLE + n_bytes * 8 / BASIC_RATE


#   라운드(코디네이티드 슬롯) 1 회 오버헤드
#     Trigger → SIFS → CTS → SIFS → [DATA] → SIFS → BlockAck
T_ROUND_PRE  = ctrl_time(34) + SIFS + ctrl_time(14) + SIFS     # 슬롯 앞: Trigger → SIFS → CTS → SIFS
T_ROUND_POST = SIFS + ctrl_time(32)                             # 슬롯 뒤: SIFS → BlockAck
T_ROUND_OH   = T_ROUND_PRE + T_ROUND_POST
#   TXOP 당 1 회, MAPC 폴링 (ICF → SIFS → ICR → SIFS)
T_MAPC_OH = ctrl_time(34) + SIFS + ctrl_time(32) + SIFS



EDCA = {                   # IEEE 802.11-2020 Table 9-155 기본값
    'VO': dict(aifsn=2, cw_min=3,  cw_max=7),
    'VI': dict(aifsn=2, cw_min=7,  cw_max=15),
    'BE': dict(aifsn=3, cw_min=15, cw_max=1023),
    'BK': dict(aifsn=7, cw_min=15, cw_max=1023),
}


# ══════════════════════════════════════════════════════════════════════════
# 3. 트래픽 (802.11e Access Category)
#      VO / VI → 저지연,   BE / BK → 일반
# ══════════════════════════════════════════════════════════════════════════
TRAFFIC = {
    # 저지연·배경 트래픽 : Lee et al., "Performance Analysis of IEEE 802.11bn with
    #   Coordinated TDMA on Real-Time Applications" https://arxiv.org/abs/2508.18755 Table I
    #   (11bn MAPC · 저지연 · TGax 기업 시나리오. 본 연구와 가장 가까운 선행연구)
    'RTMG': dict(ac='VO', is_ll=True,  burst=0.08e3,   iat=23.06e-3, deadline=0.020),   # 80 B 지만 MPDU 1 개(1500 B) 로 추상화 → 실효 0.5 Mbps (가정으로 명시)
    'VR':   dict(ac='VO', is_ll=True,  burst=166.66e3, iat=33.33e-3, deadline=0.020),
    'VC':   dict(ac='VI', is_ll=True,  burst=7.81e3,   iat=33.33e-3, deadline=0.030),
    #   Background 는 CBR. 버스트 200 KB 는 유지하고 주기를 조정해 전체 로드를 맞춘다 (부하 조절 변수)
    'BG':   dict(ac='BE', is_ll=False, burst=200.0e3,  iat=8.0e-3,   deadline=0.524),
}
# 마감: 저지연은 3GPP TR 26.926 XR 지연 예산, 일반은 dot11MaxTransmitMSDULifetime 512 TU
MAX_DEADLINE = max(v['deadline'] for v in TRAFFIC.values())   # 0.524 s. 측정 코호트의 guard 구간
LL_KINDS = ['RTMG', 'VR', 'VC']
BE_KINDS = ['BG']
AC_RANK = {'VO': 0, 'VI': 1, 'BE': 2, 'BK': 3}   # 802.11e EDCA 우선순위

P_LL = 0.25                # STA 가 저지연 앱을 실행할 확률 (설계 파라미터). 40 대 중 평균 10 대.
                           #   9/10 교수님: "저지연은 STA 의 트래픽 특성이 정하고 AP 는 인프라". STA 마다 독립이라
                           #   한 AP 에 저지연 STA 와 일반 STA 가 섞이는 것이 자연스럽게 생긴다.
                           #   AP 는 이번 TXOP 에 저지연 STA 에게 보낼 데이터가 있을 때 저지연 슬롯을 받는다 (head_sta).
N_LL_EXACT = None          # 정수면 저지연 STA 를 정확히 그 수만큼 균등 랜덤 선택 (실험 2 용). None 이면 STA 마다 P_LL 확률


class Source:
    """STA 하나의 다운링크 트래픽 발생기. iat 마다 burst 만큼 한꺼번에 발생한다."""

    def __init__(self, kind, load=1.0):
        c = TRAFFIC[kind]
        self.cfg, self.load, self._next = c, load, 0.0
        self.iat, self.deadline = c['iat'], c['deadline']
        self.poisson = False

    def offered_mbps(self):
        return self.cfg['burst'] * 8 * self.load / self.iat / 1e6

    def arrivals(self, t0, t1, rng=None):
        if self.load <= 0:
            return []
        # 한 프레임보다 작은 버스트도 MPDU 1 개로 전송된다
        n = max(1, int(round(self.cfg['burst'] * 8 * self.load / FRAME_LEN)))
        out = []
        while self._next < t1:
            if self._next >= t0:
                out.extend([self._next] * n)
            # FTP 는 포아송 도착 (3GPP FTP Model 1) → 간격이 지수분포
            if self.poisson and rng is not None:
                self._next += rng.exponential(self.iat)
            else:
                self._next += self.iat
        return out


class Queue:
    """
    STA 하나의 다운링크 송신 큐 (AP 가 보유). 마감을 넘긴 패킷은 폐기한다 (MSDU lifetime).

    통계는 '측정 코호트' 기준 (9/10): 생성 시각이 [eval_start, eval_stop) 인 패킷만 센다.
      eval_stop = sim_dur - 최대 마감  → 측정 대상 패킷은 시뮬레이션이 끝나기 전에 반드시
      전달 / 재전송 폐기 / 마감 초과 중 하나로 결정된다 (미결 패킷이 분모에 섞이지 않음).
      손실 원인을 재전송 폐기(gen_retry) 와 마감 초과(gen_dead) 로 분리해 기록한다.
    """
    eval_start = 0.0
    eval_stop = float('inf')

    def __init__(self, deadline):
        self.q = deque()
        self.deadline = deadline
        self.sent_bits = 0.0        # on-time 전달 비트 누적 (구간 무관, MAB 학습용)
        self.tp_bits = 0.0          # 측정 구간에 전달 완료된 비트 (처리량용)
        self.lats = []
        self.gen = self.ok = self.drop_retry = self.drop_dead = 0

    @staticmethod
    def _in_eval(ts):
        return Queue.eval_start <= ts < Queue.eval_stop

    def push(self, times):
        self.q.extend(times)
        self.gen += sum(1 for ts in times if Queue._in_eval(ts))

    def expire(self, now):
        while self.q and now - self.q[0] > self.deadline:
            ts = self.q.popleft()
            if Queue._in_eval(ts):
                self.drop_dead += 1

    def send(self, n_bits, now, discard_ratio=0.0):
        n_pkt = int(n_bits // FRAME_LEN)
        delivered = 0
        for _ in range(min(n_pkt, len(self.q))):
            ts = self.q.popleft()
            ev = Queue._in_eval(ts)
            if now - ts > self.deadline:           # 전송 중 마감을 넘긴 패킷은 전달 실패
                if ev:
                    self.drop_dead += 1
                continue
            if ev:
                self.lats.append(max((now - ts) * 1000.0, 0.0))
                self.ok += 1
            self.sent_bits += FRAME_LEN
            if Queue.eval_start <= now < Queue.eval_stop:   # 처리량은 전달 완료 시각 기준 (9/11)
                self.tp_bits += FRAME_LEN
            delivered += 1
        # 재시도 한도 초과 폐기: 실제 전달된 수에 비례 (ARQ discard = 전달 1 건당 폐기 수의 기댓값)
        for _ in range(min(int(round(delivered * discard_ratio)), len(self.q))):
            ts = self.q.popleft()
            if Queue._in_eval(ts):
                self.drop_retry += 1

    def __len__(self):
        return len(self.q)


def serve_ap(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
    """
    AP a 가 슬롯 시간 dur 동안 자기 STA 들에게 순서대로 보낸다 (9/9).
      first 부터 (이번 TXOP 목적지, 저지연 판정에 쓴 STA), 큐가 비면 EDCA 순으로 다음 STA.
      STA 마다 SINR·MCS 를 따로 계산 (같은 슬롯 members 의 간섭 포함).
      → RTMG 1 프레임짜리 STA 가 슬롯을 통째로 점유해 같은 AP 의 VR 이 굶는 인공 현상 방지.
    반환: 전달된 프레임의 지연 목록
    """
    #   only=True 면 이 AP 의 저지연 STA 들에게만 (priority 슬롯, 9/10 교수님 "첫 슬롯은 저지연 STA 만")
    #   single=True 면 first 에게 PPDU 하나만 (CSMA/CA 에서 TXOP limit 0 인 AC: A-MPDU 는 수신 STA 하나)
    rest = [] if single else sorted((j for j in sta_of[a] if j != first and (not only or TRAFFIC[sta_kind[j]]['is_ll'])),
                                    key=lambda j: (AC_RANK[TRAFFIC[sta_kind[j]]['ac']], q[j].q[0] if len(q[j]) else 1e9))
    order = [first] + rest
    remaining = dur * eff
    lats = []
    for j in order:
        if len(q[j]) == 0 or remaining <= 1e-12:
            continue
        itf = [(powers[b], ch.loss_now(b, j)) for b in members if b != a]
        raw, p = link_stats(sinr_from_loss(powers[a], ch.loss_now(a, j), itf))
        _, dsc = arq(p)
        rate = raw * p
        use = min(remaining, len(q[j]) * FRAME_LEN / rate)
        before = len(q[j].lats)
        q[j].send(rate * use, now, dsc)
        lats.extend(q[j].lats[before:])
        remaining -= use
    return lats


def medium_time(bits, phy_rate, sba):
    """
    IEEE 802.11e TSPEC 의 Medium Time.
        Medium Time = SBA x pps x duration(Nominal MSDU Size, PHY Rate)
    표준은 최소 PHY 속도와 고정 SBA 를 쓰지만 보수적이므로,
    본 연구에서는 실측 PHY 속도와 재전송 확률에서 유도한 SBA 를 사용한다.
    반환값은 초당 필요한 매체 점유 시간 (TXOP 대비 비율로 사용 가능).
    """
    pps = np.ceil(bits / FRAME_LEN)
    return float(sba * pps * FRAME_LEN / max(phy_rate, 1e3))


# ══════════════════════════════════════════════════════════════════════════
# 4. 토폴로지와 그룹핑 (Master AP)
# ══════════════════════════════════════════════════════════════════════════
def make_topology(n_ap, n_sta, rng, area, d_sta):
    """AP 를 영역 전체에 균등 랜덤 배치하고, STA 를 자기 AP 로부터 1~d_sta m 에 둔다."""
    ap = rng.uniform(0.0, area, (n_ap, 2))
    sta, owner = [], []
    for i, xy in enumerate(ap):
        for _ in range(n_sta):
            ang = rng.uniform(0, 2 * np.pi)
            r = rng.uniform(1.0, d_sta)
            sta.append(xy + r * np.array([np.cos(ang), np.sin(ang)]))
            owner.append(i)
    sta, owner = np.array(sta), np.array(owner)
    return ap, sta, owner


CENTER_SEP_DBM = -70.0     # dBm, 센터 간 최소 이격 (9/12: −60 → −70, 벽 7 dB 를 켜면서 재조정). 기존 센터로부터 이보다 약하게 들려야 새 센터.
                           #   벽 7 dB 에서 40 seed: 그룹 수 평균 5.2, 그룹 크기 3.8, 1대 그룹 11 % (벽 0 dB · −60 dBm 때와 같은 수준).
                           #   −50 은 이웃 거리 16 m 라 단독 그룹이 34 % 였음. −60 에서 8 %, 평균 그룹 4.2 대 (40 trial).


def rssi_clustering(ap_pos, load, k=None, sep_dbm=None, ch=None):
    """
    Master AP 의 그룹핑 (교수님 2026-08-05: "그룹 갯수는 센터 노드를 기반으로").

      센터 노드 선정
        부하율(STA 요구량 합 / 단독 링크 용량)이 낮은 = 가용 자원이 많은 AP 부터 후보로 삼되 (멘토님 8/05),
        이미 뽑힌 모든 센터로부터 받는 RSSI(섀도잉 포함, 멘토님 8/24) 가 sep_dbm 미만일 때만 센터로 인정.
        → 서로 충분히 떨어진 AP 들이 센터가 되고, 그룹 수는 배치에서 저절로 정해진다.
      k 가 주어지면 그 수에 맞춘다 (실험 통제용).
      멤버 할당
        센터가 아닌 AP 는 RSSI 가 가장 큰 센터에 소속된다.
    """
    if sep_dbm is None:
        sep_dbm = CENTER_SEP_DBM
    n = len(ap_pos)
    if ch is not None:
        R = np.array([[ch.rssi_ap(i, j, ap_pos) if i != j else 1e9 for j in range(n)] for i in range(n)])
    else:
        R = np.array([[(MAX_TX_POWER - path_loss(np.linalg.norm(ap_pos[i] - ap_pos[j]))
                        - WALL_LOSS_DB * n_walls(ap_pos[i], ap_pos[j])) if i != j else 1e9
                       for j in range(n)] for i in range(n)])

    # 센터 후보 순서: 부하(자기 STA 요구량 합)가 적은 = 가용 자원이 많은 AP 부터 (멘토님 8/05)
    order = sorted(range(n), key=lambda i: load[i])
    centers = [order[0]]
    for i in order[1:]:
        if k is not None and len(centers) >= k:
            break
        if max(R[i, c] for c in centers) < sep_dbm:
            centers.append(i)
    if k is not None:
        while len(centers) < k:
            cand = [(max(R[i, c] for c in centers), i)
                    for i in range(n) if i not in centers]
            centers.append(min(cand)[1])

    clusters = {c: [] for c in range(len(centers))}
    for i in range(n):
        if i in centers:
            clusters[centers.index(i)].append(i)
        else:
            clusters[int(np.argmax([R[i, c] for c in centers]))].append(i)

    # 1 대짜리 그룹도 허용한다 (9/11 결정).
    #   주변에 가까운 AP 가 없는 AP 는 조율할 상대가 없으므로 혼자 그룹이 되고, 최대 전력으로 단독 전송한다.
    #   (이전에는 1 대 그룹이 생기면 센터 이격 기준을 2 dB 씩 완화해 다시 묶었으나,
    #    기준이 완화되면서 그룹이 지리적으로 넓어져 '같은 그룹 = 서로 간섭이 큼' 이라는 전제가 약해졌다.)
    return {c: m for c, m in clusters.items() if m}


# ══════════════════════════════════════════════════════════════════════════
# 5. 라운드 구성
# ══════════════════════════════════════════════════════════════════════════
def rounds_conventional(clusters, mode, active=None):
    """
    종래 MAPC. 인접 AP 를 그룹핑한 뒤 한 방식만 고정 사용한다.
      'csr'  Co-SR: 모든 AP 가 전력을 조정하여 동시 전송 (그룹 내부 · 그룹 간 모두)
      'tdma' Co-TDMA (IEEE 802.11bn): sharing AP 가 얻은 TXOP 를 MAPC 트리거로 shared AP 들에 순차 할당.
             한 슬롯에 한 AP 만, 최대 전력. 슬롯은 균등 (멘토님 9/04 "최적화 안 함"), 순서는 AP 번호 순
             (배치가 무작위라 순서에 편향 없음). TXOP 획득(T_EDCA_ACCESS)·슬롯 제어(T_ROUND_OH)는 simulate 에서 차감.
    active 가 주어지면 보낼 데이터가 있는 AP 만 참여한다 (제안 모델과 동일 조건).
    """
    cids = sorted(clusters)
    aps = [a for c in cids for a in clusters[c]]
    if active is not None:
        aps = [a for a in aps if a in active]
    if not aps:
        return []
    if mode == 'tdma':
        return [dict(members=[a], ll_ap=None) for a in aps]
    return [dict(members=list(aps), ll_ap=None)]


TDMA_SCHED = 'lee'         # Co-TDMA 의 TXOP 안 시간 배분 (9/12, Lee et al. arXiv:2508.18755 §III 과 대조)
                           #   'equal' = 멘토님 9/04: sharing AP + shared AP 들이 균등 슬롯, 각자 자기 STA 에게 (AC 순). 최적화 없음.
                           #   'lee'   = Lee et al. 스케줄링: sharing AP 가 자기 DL 을 먼저 보내고, 남은 시간을 저지연 큐가 있는
                           #             shared AP 에게 "저지연 트래픽에 필요한 만큼" 순차 할당 (LL 만 전송). 남는 시간이 없으면 공유 없음.
                           #             (논문은 AP 2 대 쌍만 다루지만 11bn 은 여러 shared AP 순차 공유를 허용 → TDMA_MAX_SHARE 까지)
                           #   'lee-equal' = Lee 의 절차(EDCA 승자 = sharing AP, 자기 DL 먼저, 트리거로 공유)는 그대로 두고, 남은 시간을
                           #             라운드 로빈 shared AP 들에게 균등 분배 (저지연 인지 없음, 각자 자기 STA 에게 AC 순). 멘토님 균등 + Lee 절차.
                           #             shared AP 수는 TDMA_MAX_SHARE−1 (None 이면 4). TXOP 가 남지 않으므로 CF-End 재획득은 없음.
TDMA_MAX_SHARE = None      # Co-TDMA: 한 TXOP 를 나눠 갖는 AP 수 상한. 'lee' 는 남는 시간만큼만 공유하므로 None (자연 제한),
                           #   'equal' 은 5 권장 (None 이면 v1.8 처럼 활성 AP 전원 균등 → 슬롯당 오버헤드가 데이터 시간과 맞먹음).
                           #   802.11bn Co-TDMA: sharing AP 가 EDCA 로 얻은 TXOP 를 ICF/ICR 폴링 뒤 MU-RTS TXS 트리거로 shared AP 에 할당
                           #   (Lee et al. Fig. 1 과 같은 순서: 폴링 → sharing AP DL → 트리거/CTS → shared AP → BA).
                           #   대상은 라운드 로빈, sharing AP 가 먼저 보낸다. 활성 AP 20 대를 한 TXOP 에 모두 넣으면 슬롯당 제어
                           #   오버헤드(T_ROUND_OH 135 us)가 데이터 시간과 맞먹으므로 (9/12 실측: 298 → 508 Mbps @700) K 를 제한한다.
LL_INTRA = 'tdma'          # 저지연 서비스 AP 가 2 대 이상인 그룹이 둘 이상인 혼합 상황의 처리 (9/10 PPT 논의사항)
                           #   'tdma' = 논문(wait) · 'group-wait' = 저지연 없는 그룹만 대기 (10/2) · 'group' = no-wait
                           #   'tdma' = ② Case 1 로 보되 각 저지연 그룹 안은 c-TDMA, 저지연 슬롯 동안 나머지 AP 대기  ← 확정 (9/11)
                           #   'group'= ③ Case 2 로 처리 (비교용). 순수 Case 1 · Case 2 는 두 설정에서 동일하게 동작.


def rounds_proposed(clusters, prio_of, active, rank_of=None):
    """
    제안 모델 슬롯 구성 (교수님 8/19 Case 1 / Case 2, 판정 기준은 9/10 피드백대로 STA 기준).

      prio_of : {AP: [저지연 큐가 있는 STA 들 (EDCA 순)]}  → 그 AP 가 이번 TXOP 의 "저지연 서비스 AP"
      active  : 보낼 데이터가 있는 AP 집합
      rank_of : {AP: 정렬 키}. 그룹 안 전송 순서 = 우선순위(AC) → 큐 긴 AP → 오래 기다린 AP (9/11 확정)

      Case 2  저지연 서비스 AP 2 대 이상이 전부 한 그룹에
              → 그 그룹은 AP 마다 슬롯을 나눠 순차 전송 (c-TDMA), 저지연 AP 먼저
              → 다른 그룹은 모든 슬롯에서 활성 전원 동시 전송 (c-SR)
      Case 1  그 외 (여러 그룹에 흩어짐, 또는 저지연 서비스 AP 1 대 이하)
              → 저지연 슬롯: 저지연 서비스 AP 가 전송, 나머지 AP 는 대기 (교수님 8/19 "나머지는 쉰다")
                 같은 그룹에 저지연 AP 가 2 대 이상이면 LL_INTRA 로 그룹 안 처리 결정 (②/③)
              → 마지막 슬롯: 활성 전원 동시 전송 (c-SR)

    반환: [ {priority: {AP: STA}, shared: [AP...], members: [AP...]} , ... ]
    """
    cids = sorted(clusters)
    act = {c: [a for a in clusters[c] if a in active] for c in cids}
    if rank_of is None:
        rank_of = {a: (0, 0, a) for c in cids for a in act[c]}
    ll_by_c = {c: sorted((a for a in act[c] if prio_of.get(a)), key=lambda a: rank_of[a]) for c in cids}
    ll_all = [a for c in cids for a in ll_by_c[c]]
    groups_with_ll = [c for c in cids if ll_by_c[c]]

    def rd(prio, shared):
        return dict(priority=prio, shared=shared, members=list(prio) + shared)

    # ── Case 2: 저지연 서비스 AP 가 전부 한 그룹에 (또는 ③ 설정에서 저지연 그룹이 여럿) ──
    multi = [c for c in cids if len(ll_by_c[c]) >= 2]
    case2 = (len(ll_all) >= 2 and len(groups_with_ll) == 1) or (LL_INTRA == 'group' and multi)
    if case2:
        tdma_c = groups_with_ll if LL_INTRA == 'group' else [groups_with_ll[0]]
        geo = [c for c in cids if c not in tdma_c]
        # 그룹 안 순서: 저지연 서비스 AP 먼저, 그 뒤 일반 AP
        order = {c: [(a, prio_of[a][0]) for a in ll_by_c[c]]
                    + [(a, None) for a in sorted((a for a in act[c] if not prio_of.get(a)), key=lambda a: rank_of[a])]
                 for c in tdma_c}
        n_r = max((len(v) for v in order.values()), default=1)
        out = []
        for r in range(n_r):
            prio, shared = {}, [a for c in geo for a in act[c]]
            for c in tdma_c:
                if not order[c]:
                    continue
                a, j = order[c][min(r, len(order[c]) - 1)]
                if j is not None:
                    prio[a] = j
                else:
                    shared.append(a)
            out.append(rd(prio, shared))
        return [x for x in out if x['members']]

    # ── Case 1: 저지연 슬롯(저지연 서비스 AP 만) → 마지막 슬롯(전원 shared) ──
    out = []
    if ll_all:
        if LL_INTRA in ('tdma', 'group-wait'):   # ② 같은 그룹 저지연 AP 끼리는 순번, 다른 그룹끼리는 동시
            n_r = max(len(v) for v in ll_by_c.values())
            for r in range(n_r):
                prio = {ll_by_c[c][r]: prio_of[ll_by_c[c][r]][0] for c in cids if r < len(ll_by_c[c])}
                shared = []
                if LL_INTRA == 'group-wait':
                    # 'group-wait' (10/2): priority 구간은 "저지연이 있는 그룹"의 것. 저지연 전송을 모두 마친 그룹은
                    #   그 라운드부터 자기 모든 활성 AP 가 shared 처럼 전송한다 (저지연 서비스 AP 의 나머지 STA 포함).
                    #   저지연이 없는 그룹만 마지막 shared 라운드까지 대기한다.
                    shared = [a for c in groups_with_ll if r >= len(ll_by_c[c]) for a in act[c]]
                out.append(rd(prio, shared))
        else:                           # 저지연 서비스 AP 전원이 한 슬롯에 동시
            out.append(rd({a: prio_of[a][0] for a in ll_all}, []))
    if any(act.values()):
        out.append(rd({}, [a for c in cids for a in act[c]]))
    return [x for x in out if x['members']]


# ══════════════════════════════════════════════════════════════════════════
# 6. 시뮬레이션
# ══════════════════════════════════════════════════════════════════════════
# ── EDCA 경쟁 모델 (IEEE 802.11-2020 §10.23, Bianchi 2000 의 AC 별 확장) ──
TXOP_LIMIT = {'VO': 2.080e-3, 'VI': 4.096e-3, 'BE': 0.0, 'BK': 0.0}   # Table 9-155 (OFDM PHY). 0 = TXOP 는 PPDU 하나
MAX_PPDU   = TAU                                                       # 5.484 ms, 802.11ax 최대 PPDU 길이
CSMA_STD_TXOP_LIMIT = True     # False 면 모든 AC 의 TXOP limit 을 TAU 로 (MAPC 와 같은 조건, 민감도 확인용)
CSMA_EDCA = True               # True  = 표준 EDCA: AP 마다 head STA 의 AC (VO/VI/BE) 로 경쟁 (Table 9-155)
                               # False = 레거시 DCF: 전원 BE 파라미터로 경쟁 (v1.8 과 같은 가정, 9/9 멘토님 논의).
                               #   ※ EDCA 는 VO(CW 3~7) 경쟁자가 6 대를 넘으면 충돌이 폭증해 CSMA/CA 처리량이 무너진다 (표준의 알려진 성질).
CCA_PD_DBM = -82.0             # 프리앰블 검출 CCA 문턱 (20 MHz). 본 배치는 AP 쌍의 99 % 가 이 이상 → 단일 경쟁 영역으로 본다
T_BA       = ctrl_time(32)     # BlockAck


def aifs(ac):
    return SIFS + EDCA[ac]['aifsn'] * SLOT_TIME


# MAPC (Co-SR · Co-TDMA · 제안) 의 TXOP 획득 비용: 조정 AP 가 EDCA 로 잡는다 (802.11bn: TXOP 획득은 EDCA). 조정 집합의 다른 AP 는
# 트리거를 기다리므로 경쟁 상대가 없다 → 충돌 없이 AIFS + 평균 백오프(CW_min/2 슬롯)만 든다. TXOP 당 1 회. 전송은 TXOP 안에서 전원이 한다.
T_EDCA_ACCESS = aifs('BE') + (EDCA['BE']['cw_min'] / 2) * SLOT_TIME


def tau_of(ac, p):
    """Bianchi 고정점: 충돌 확률 p 일 때 AC 의 슬롯당 전송 확률 τ. 백오프 단계 m 은 CW_min → CW_max 에서 결정."""
    e = EDCA[ac]
    W, Wmax = e['cw_min'], e['cw_max']
    m = max(int(round(np.log2(max(Wmax + 1, 2) / max(W + 1, 1)))), 0)
    p = float(np.clip(p, 1e-6, 0.99))
    if abs(p - 0.5) < 1e-6:
        b = W * (m + 1) / 2.0
    else:
        b = (W * (1 - p - p * (2 * p) ** m) / (1 - 2 * p) - 1) / 2.0
    return float(np.clip(1.0 / (max(b, 0.5) + 1.0), 1e-6, 0.5))


_bianchi_cache = {}


def edca_bianchi(counts):
    """
    AC 별 경쟁자 수 counts = {AC: n} 에 대한 Bianchi(2000) 고정점의 EDCA 확장 (포화 가정은 '지금 보낼 데이터가 있는 AP' 에만).
      p_AC = 1 − Π_b (1−τ_b)^(n_b − [b=AC]),   τ_AC = tau_of(AC, p_AC)
    반환 dict(tau={AC: τ}, p_tr=슬롯에 누군가 전송할 확률, p_s={AC: 그 AC 의 어떤 AP 가 단독 성공할 확률})
    같은 counts 는 캐시한다 (매 접근마다 다시 풀지 않는다).
    """
    key = tuple(sorted((a, n) for a, n in counts.items() if n > 0))
    if key in _bianchi_cache:
        return _bianchi_cache[key]
    acs = [a for a, _ in key]
    n = dict(key)
    tau = {a: 0.1 for a in acs}
    for _ in range(1000):
        p = {a: 1.0 - np.prod([(1.0 - tau[b]) ** (n[b] - (1 if b == a else 0)) for b in acs]) for a in acs}
        new = {a: tau_of(a, p[a]) for a in acs}
        diff = max(abs(new[a] - tau[a]) for a in acs)
        tau = {a: 0.7 * tau[a] + 0.3 * new[a] for a in acs}
        if diff < 1e-10:
            break
    p_tr = 1.0 - float(np.prod([(1.0 - tau[b]) ** n[b] for b in acs]))
    p_s = {a: n[a] * tau[a] * float(np.prod([(1.0 - tau[b]) ** (n[b] - (1 if b == a else 0)) for b in acs])) for a in acs}
    out = dict(tau=tau, p_tr=p_tr, p_s=p_s)
    _bianchi_cache[key] = out
    return out


def assign_traffic(ap_pos, sta_pos, owner, rng, k, ch, total_load):
    """
    STA 트래픽 배정 + 최종 그룹핑 + 부하 맞춤. 종래·제안·MAB 모두 이 함수를 쓴다.
      저지연 여부는 STA 단위 (9/10 교수님): STA 마다 독립적으로 확률 P_LL 로 저지연 앱(RTMG/VR/VC 중 하나), 아니면 BG.
      한 AP 에 저지연 STA 와 일반 STA 가 섞일 수 있다. AP 가 저지연 슬롯을 받는지는 TXOP 마다 큐로 정한다.
        STA 마다 독립 (기본)  /  N_LL_EXACT 면 저지연 STA 수 고정 (실험 2)
    반환: sta_kind, src, clusters, place
    """
    n_ap, n_all = len(ap_pos), len(sta_pos)
    clusters = rssi_clustering(ap_pos, {i: 0.0 for i in range(n_ap)}, k, ch=ch)   # 예비 (부하 0)
    place = 'random'
    n_ll_sta = None

    def kinds_from(ll_stas):
        return [LL_KINDS[int(rng.integers(0, len(LL_KINDS)))] if j in ll_stas
                else BE_KINDS[int(rng.integers(0, len(BE_KINDS)))] for j in range(n_all)]

    def finalize(sta_kind):
        """Source 생성 → BG 주기를 조정해 전체 로드를 맞춤 → AP 부하율 → 최종 그룹핑.
        (9/10 수정: 이전에는 주기 조정 전 기본값으로 그룹핑해 저지연 AP 가 항상 센터가 됐음)"""
        src = {j: Source(sta_kind[j]) for j in range(n_all)}
        ll_sta = [j for j in range(n_all) if TRAFFIC[sta_kind[j]]['is_ll']]
        be_sta = [j for j in range(n_all) if not TRAFFIC[sta_kind[j]]['is_ll']]
        ll_total = sum(src[j].offered_mbps() for j in ll_sta)
        if ll_total > total_load:
            import warnings
            warnings.warn(f'저지연 고정 부하 {ll_total:.0f} Mbps 가 목표 {total_load:.0f} 를 넘음 (실측 제공 로드는 목표보다 큼)')
        if be_sta:
            per_sta = max(total_load - ll_total, 1e-6) / len(be_sta)
            for j in be_sta:
                src[j].iat = src[j].cfg['burst'] * 8 / (per_sta * 1e6)
        # 가용 자원 = 1 − 부하율. 부하율 = AP 의 STA 요구량 합 / 단독 전송 시 평균 링크 용량 (멘토님 8/05 "가용 자원이 많은 AP")
        #   부하율 = Σ_STA (요구량 / 그 링크의 단독 유효 속도) = AP 가 자기 트래픽을 처리하는 데 필요한 airtime 비율
        util = {}
        for i in range(n_ap):
            u = 0.0
            for j in (j for j in range(n_all) if owner[j] == i):
                raw, p = link_stats(sinr_from_loss(MAX_TX_POWER, ch.loss_mean(i, j), []))
                u += src[j].offered_mbps() / max(raw * p / 1e6, 1e-6)
            util[i] = u
        return src, rssi_clustering(ap_pos, util, k, ch=ch)     # 최종: 부하율 낮은(가용 자원 많은) AP 부터 센터

    if N_LL_EXACT is not None:                     # 실험 2: 저지연 STA 수 고정, 위치만 랜덤
        ll_stas = set(rng.choice(n_all, min(N_LL_EXACT, n_all), replace=False).tolist())
    else:
        ll_stas = {j for j in range(n_all) if rng.random() < P_LL}
    sta_kind = kinds_from(ll_stas)
    src, clusters = finalize(sta_kind)

    for j in range(n_all):                     # 버스트 위상 무작위 (최종 주기 기준)
        src[j]._next = rng.uniform(0.0, src[j].iat)
    return sta_kind, src, clusters, place


def simulate(model, seed, n_ap=12, n_sta=2, k=None, ll_ratio=0.3,
             total_load=500.0, area=60.0, d_sta=5.0, sim_dur=5.0,
             eval_from=0.6):
    """
    eval_from : 이 비율 이후 구간만 통계에 넣는다 (기본 0.6 → 뒤 40 %).
                MAB 와 같은 시간 창에서 비교하기 위함. 큐가 쌓인 정상 상태를 잰다.
    """
    rng = np.random.default_rng(seed)
    rng_mac = np.random.default_rng(seed + 20_000)   # CSMA 승자 추첨 전용 (트래픽·배치 난수와 분리 → 모델 간 같은 배치)

    ap_pos, sta_pos, owner = make_topology(n_ap, n_sta, rng, area, d_sta)
    ch = Channel(ap_pos, sta_pos, rng)

    sta_kind, src, clusters, place = assign_traffic(ap_pos, sta_pos, owner, rng, k, ch, total_load)
    n_all_sta = len(sta_pos)
    is_ll = np.array([any(TRAFFIC[sta_kind[j]]['is_ll'] for j in range(n_all_sta) if owner[j] == i)
                      for i in range(n_ap)])                  # 통계용: 저지연 STA 를 가진 AP
    ll_i = [i for i in range(n_ap) if is_ll[i]]
    be_i = [i for i in range(n_ap) if not is_ll[i]]
    ll_sta = [j for j in range(n_all_sta) if TRAFFIC[sta_kind[j]]['is_ll']]
    be_sta = [j for j in range(n_all_sta) if not TRAFFIC[sta_kind[j]]['is_ll']]
    offered = {i: sum(src[j].offered_mbps() for j in range(n_all_sta) if owner[j] == i)
               for i in range(n_ap)}

    q = {j: Queue(TRAFFIC[sta_kind[j]]['deadline']) for j in range(n_all_sta)}
    sta_of = {i: [j for j in range(n_all_sta) if owner[j] == i] for i in range(n_ap)}

    def active_stas(i, ll_only=False):
        return [j for j in sta_of[i] if len(q[j]) > 0 and (not ll_only or TRAFFIC[sta_kind[j]]['is_ll'])]

    def head_sta(i, ll_only=False):
        """AP i 의 STA 중 지금 보낼 목적지.
        802.11e EDCA 우선순위(VO > VI > BE) → 같은 AC 면 큐가 긴 STA → 그것도 같으면 오래 기다린 STA (9/11 확정).
        ll_only=True 면 저지연 STA 중에서만 (priority 슬롯)."""
        js = active_stas(i, ll_only)
        return min(js, key=lambda j: (AC_RANK[TRAFFIC[sta_kind[j]]['ac']], -len(q[j]), q[j].q[0])) if js else None

    def ap_qlen(i):
        return sum(len(q[j]) for j in sta_of[i])
    eff = None
    # 슬롯 길이(Medium Time) 추정용 단독 링크 (간섭 없음, 최대 전력): 원시 PHY 속도 raw0 와 재전송 기댓값 E0.
    #   Medium Time = E0 × bits / raw0.  raw×p 를 넣으면 재전송이 이중 반영 (9/10 수정)
    raw0, E0 = {}, {}
    for j in range(n_all_sta):
        raw, p = link_stats(sinr_from_loss(MAX_TX_POWER, ch.loss_mean(owner[j], j), []))
        raw0[j], E0[j] = raw, arq(p)[0]

    carry = 0.0                                      # CSMA: 이전 스텝에서 넘어온 채널 점유 시간
    rr = deque(range(n_ap))                          # Co-TDMA 라운드 로빈 순서 (TDMA_MAX_SHARE 일 때)

    def csma_txop(t, used):
        """
        IEEE 802.11-2020 EDCA (§10.23) 를 길이 TAU 의 스텝 안에서 순차 경쟁으로 진행한다 (9/12).
          · 경쟁자 = 보낼 데이터가 있는 AP. 각 AP 는 head STA 트래픽의 AC 로 경쟁 (VO > VI > BE, Table 9-155 CW·AIFSN).
          · 승자 = Bianchi 고정점(AC 별 τ)의 성공 확률 P_s,AC 에 비례해 AC 를 뽑고, 그 AC 안에서 균등 추첨.
          · 경쟁 비용 = 성공 1 회당 유휴 슬롯·충돌 시간 기댓값 [(1−P_tr)σ + (P_tr−P_s)·T_c] / P_s + AIFS.
              충돌 길이 T_c = 경쟁 AP 들이 의도한 PPDU 길이 평균 + 프리앰블 + AIFS (EIFS 근사).
          · 승자는 TXOP limit (VO 2.080 ms, VI 4.096 ms, BE/BK 0 = PPDU 하나 ≤ 5.484 ms) 안에서 최대 전력으로 전송.
            limit 0 이면 head STA 에게 A-MPDU 하나, VO/VI TXOP 면 그 AC 의 트래픽(저지연 STA 들)에게 차례로 (§10.23.2.8).
          · 단일 경쟁 영역 (본 배치는 AP 쌍의 99 % 가 CCA −82 dBm 이상). 다른 AP 는 그 동안 대기.
          · 전송 뒤 프리앰블 + SIFS + BlockAck, 다시 경쟁. 스텝 경계를 넘긴 시간은 다음 스텝으로 이월.
        반환: 다음 스텝으로 넘기는 점유 시간 (≥ 0)
        """
        while used < TAU:
            contenders = [i for i in range(n_ap) if active_stas(i)]
            if not contenders:
                return 0.0
            ac_of = {i: (TRAFFIC[sta_kind[head_sta(i)]]['ac'] if CSMA_EDCA else 'BE') for i in contenders}
            B = edca_bianchi(Counter(ac_of.values()))
            intend, single_of = {}, {}
            for i in contenders:
                h = head_sta(i)
                limit = TXOP_LIMIT[ac_of[i]] if CSMA_STD_TXOP_LIMIT else TAU
                single_of[i] = (limit == 0.0)
                if single_of[i]:
                    limit = MAX_PPDU
                    bits = len(q[h]) * FRAME_LEN
                else:                                            # VO/VI TXOP: 획득한 AC 의 트래픽(저지연 STA) 만 전송
                    bits = sum(len(q[j]) for j in active_stas(i, True)) * FRAME_LEN
                intend[i] = min(medium_time(bits, raw0[h], E0[h]), limit)
            acs = list(B['p_s'])
            w = np.array([B['p_s'][a] for a in acs]); w = w / w.sum()
            ac_w = acs[int(rng_mac.choice(len(acs), p=w))]
            winner = int(rng_mac.choice([i for i in contenders if ac_of[i] == ac_w]))
            p_tr, p_s = B['p_tr'], float(sum(B['p_s'].values()))
            t_c = float(np.mean(list(intend.values()))) + T_PREAMBLE + aifs('BE')
            used += ((1.0 - p_tr) * SLOT_TIME + (p_tr - p_s) * t_c) / max(p_s, 1e-9) + aifs(ac_w)
            dur = intend[winner]
            serve_ap(winner, head_sta(winner), [winner], {winner: MAX_TX_POWER}, ch, q, sta_of, sta_kind,
                     dur, t + used + dur, only=(not single_of[winner]), single=single_of[winner])
            used += dur + T_PREAMBLE + SIFS + T_BA
        return used - TAU

    g_stat = np.zeros(3)                             # 그룹 상태 집계 (측정 구간): 저지연 서비스 AP 0 / 1 / 2+
    n_txop = int(sim_dur / TAU)
    t_eval = int(n_txop * eval_from)
    #   측정 코호트: warm-up 이후 ~ (끝 − 최대 마감) 에 생성된 패킷만 통계에 넣는다 (9/10).
    Queue.eval_start = t_eval * TAU
    Queue.eval_stop = max(sim_dur - MAX_DEADLINE, Queue.eval_start)
    for step in range(n_txop):
        t = step * TAU
        if step == t_eval:
            g_stat[:] = 0
        ch.new_txop()                              # 소규모 페이딩 갱신
        for j in range(n_all_sta):
            q[j].push(src[j].arrivals(t - TAU, t, rng))   # 이전 TXOP 동안 도착한 패킷만 (미래 패킷 전송 금지)
            q[j].expire(t)
        active = {i for i in range(n_ap) if active_stas(i)}
        if model == 'csma':
            carry = csma_txop(t, carry)              # EDCA 경쟁 (승자 1 대씩 순차). 아래 슬롯 실행은 MAPC 전용
            continue
        if not active:
            continue

        if model.startswith('proposed'):
            # 이번 TXOP 에 우선 서비스할 (AP, 저지연 STA): 큐 있는 저지연 STA 를 EDCA 순으로
            prio_of = {i: sorted(active_stas(i, True), key=lambda j: (AC_RANK[TRAFFIC[sta_kind[j]]['ac']], -len(q[j]), q[j].q[0]))
                       for i in active}
            rank_of = {a: (AC_RANK[TRAFFIC[sta_kind[prio_of[a][0]]]['ac']] if prio_of.get(a) else 9,
                           -sum(len(q[j]) for j in (prio_of.get(a) or sta_of[a])),
                           min((q[j].q[0] for j in (prio_of.get(a) or sta_of[a]) if len(q[j])), default=1e9))
                       for a in active}
            rounds = rounds_proposed(clusters, prio_of, active, rank_of)
            if step >= t_eval:
                for m in clusters.values():                # 그룹의 "저지연 트래픽을 서비스하는 AP" 수 0 / 1 / 2+
                    g_stat[min(sum(1 for a in m if a in active and prio_of.get(a)), 2)] += 1   # 그룹의 저지연 서비스 AP 수 0/1/2+
        else:
            rounds = [dict(priority={}, shared=list(rd['members']), members=list(rd['members']))
                      for rd in rounds_conventional(clusters, model.split('-')[1], active)]
        if not rounds:
            continue

        # ── TXOP 획득 (MAPC 공통): 조정 AP 가 EDCA 로 잡는다. 조정 집합의 다른 AP 는 트리거를 기다리므로 경쟁·충돌 없음 ──
        lee_w = None
        if model == 'conv-tdma':
            order = [a for a in rr if a in active]                            # 라운드 로빈 순서. 첫 AP = sharing AP (먼저 보냄)
            if TDMA_SCHED == 'lee-equal':
                # Lee 절차 + 균등 분배 (9/12): sharing AP = EDCA 승자, 자기 DL 먼저(필요한 만큼), 남은 시간을 K−1 대에 균등.
                need = lambda idxs: sum(medium_time(len(q[k]) * FRAME_LEN, raw0[k], E0[k]) for k in idxs)
                ac_of = {i: (TRAFFIC[sta_kind[head_sta(i)]]['ac'] if CSMA_EDCA else 'BE') for i in active}
                B = edca_bianchi(Counter(ac_of.values()))
                acs = list(B['p_s']); wts = np.array([B['p_s'][a] for a in acs]); wts = wts / wts.sum()
                ac_w = acs[int(rng_mac.choice(len(acs), p=wts))]
                sharing = int(rng_mac.choice([i for i in active if ac_of[i] == ac_w]))
                others = [a for a in rr if a in active and a != sharing][:(TDMA_MAX_SHARE or 5) - 1]
                n_r = 1 + len(others)
                budget = TAU - T_EDCA_ACCESS - T_MAPC_OH - n_r * T_ROUND_OH
                own = min(need(active_stas(sharing)), budget) if others else budget
                per = (budget - own) / len(others) if others else 0.0
                if others and per < T_PREAMBLE:                     # sharing AP 가 TXOP 를 다 쓰면 공유 없음 (Lee: 남는 시간이 없으면 미공유)
                    others, per = [], 0.0
                    own = TAU - T_EDCA_ACCESS - T_MAPC_OH - T_ROUND_OH
                rounds = [dict(priority={}, shared=[a], members=[a]) for a in [sharing] + others]
                durs = [own] + [per] * len(others)
                for a in [sharing] + others:
                    rr.remove(a); rr.append(a)
                lee_w = np.array(durs) / max(sum(durs), 1e-12)
                data_time = float(sum(durs))
            elif TDMA_SCHED == 'lee':
                # Lee et al. §III-A 를 한 스텝(TAU) 안에서 재현 (9/12):
                #   ① sharing AP = EDCA 승자 (CSMA/CA 와 같은 AC 우선순위 분포. 라운드 로빈이면 VO AP 가 110 ms 씩 기다려
                #      저지연 손실이 CSMA/CA 보다 나빠지는 모순이 생긴다). 충돌 비용은 MAPC 공통 가정대로 없음.
                #   ② sharing AP 가 자기 DL 을 먼저 보내고, 남은 TXOP 를 저지연 큐가 있는 shared AP 에게 LL 필요 시간만큼 순차 할당.
                #   ③ 그래도 TXOP 가 남으면 CF-End 로 끝내고 (논문 4)) 다음 EDCA 승자가 새 TXOP 를 시작 (획득 + 폴링 비용 다시).
                #      스텝을 채울 때까지 반복. 이것을 빼면 VO AP 가 잡은 TXOP 가 거의 비어 처리량이 25 % 떨어진다 (실측).
                need = lambda idxs: sum(medium_time(len(q[k]) * FRAME_LEN, raw0[k], E0[k]) for k in idxs)
                ac_of = {i: (TRAFFIC[sta_kind[head_sta(i)]]['ac'] if CSMA_EDCA else 'BE') for i in active}
                rounds, durs, gaps = [], [], []
                remaining = TAU - T_EDCA_ACCESS - T_MAPC_OH          # 스텝에 남은 시간 (첫 TXOP 획득·폴링 제외)
                served, gap = set(), 0.0
                while remaining > T_ROUND_OH + T_PREAMBLE:
                    cand = [i for i in active if i not in served]
                    if not cand:
                        break
                    B = edca_bianchi(Counter(ac_of[i] for i in cand))
                    acs = list(B['p_s']); wts = np.array([B['p_s'][a] for a in acs]); wts = wts / wts.sum()
                    ac_w = acs[int(rng_mac.choice(len(acs), p=wts))]
                    sharing = int(rng_mac.choice([i for i in cand if ac_of[i] == ac_w]))
                    txop_left = min(remaining, TAU - T_EDCA_ACCESS - T_MAPC_OH)
                    own = min(need(active_stas(sharing)), txop_left - T_ROUND_OH)
                    rounds.append(dict(priority={}, shared=[sharing], members=[sharing])); durs.append(own); gaps.append(gap)
                    served.add(sharing); txop_left -= T_ROUND_OH + own; remaining -= T_ROUND_OH + own; gap = 0.0
                    n_shared = 0                                      # 이 TXOP 안의 shared AP 수 (TDMA_MAX_SHARE − 1 까지)
                    for a in [b for b in rr if b in active and b not in served]:
                        if TDMA_MAX_SHARE and n_shared >= TDMA_MAX_SHARE - 1:
                            break
                        ll = active_stas(a, True)
                        if not ll or txop_left <= T_ROUND_OH + T_PREAMBLE:
                            continue
                        d = min(need(ll), txop_left - T_ROUND_OH)
                        j = min(ll, key=lambda k: (AC_RANK[TRAFFIC[sta_kind[k]]['ac']], -len(q[k]), q[k].q[0]))
                        rounds.append(dict(priority={a: j}, shared=[], members=[a])); durs.append(d); gaps.append(0.0)
                        served.add(a); txop_left -= T_ROUND_OH + d; remaining -= T_ROUND_OH + d; n_shared += 1
                    if txop_left > T_PREAMBLE:                        # TXOP 가 남음 → CF-End, 다음 승자가 새로 획득
                        gap = T_EDCA_ACCESS + T_MAPC_OH; remaining -= gap
                    else:
                        break
                for a in [rd['members'][0] for rd in rounds]:
                    rr.remove(a); rr.append(a)
                for rd, g in zip(rounds, gaps):
                    rd['gap'] = g
                lee_w = np.array(durs) / max(sum(durs), 1e-12)
                data_time = float(sum(durs))
            else:
                if TDMA_MAX_SHARE:
                    order = order[:TDMA_MAX_SHARE]
                for a in order:
                    rr.remove(a); rr.append(a)
                rounds = [dict(priority={}, shared=[a], members=[a]) for a in order]

        if lee_w is None:
            data_time = max(TAU - (T_EDCA_ACCESS + T_MAPC_OH + len(rounds) * T_ROUND_OH), 0.0)   # TXOP 획득 + 폴링 + 슬롯 제어

        # ── 슬롯 길이 ──
        #   종래 모델 : 균등 배분 (멘토님 2026-09-04 "동일 크기로 배분, 최적화 안 함")
        #   제안(rule): 802.11e 수락 제어 기반 Medium Time. priority AP 는 그 저지연 STA 의 큐, shared AP 는 AP 전체 큐 기준
        if lee_w is not None:
            w = lee_w                                  # Lee 스케줄링: 수요 기반 길이 (sharing AP 자기 DL, shared AP 는 LL 필요 시간)
        elif not model.startswith('proposed'):
            w = np.full(len(rounds), 1.0 / len(rounds))
        else:
            g_w, b_w = [], []
            for rd in rounds:
                vg = vb = 0.0
                for a in rd['priority']:                   # priority AP: 그 AP 의 저지연 STA 들의 Medium Time 합
                    vg = max(vg, sum(medium_time(len(q[k]) * FRAME_LEN, raw0[k], E0[k]) for k in active_stas(a, True)) / TAU)
                for a in rd['shared']:                     # shared AP: 그 AP 의 활성 STA 전체의 Medium Time 합
                    vb = max(vb, sum(medium_time(len(q[k]) * FRAME_LEN, raw0[k], E0[k]) for k in active_stas(a)) / TAU)
                g_w.append(vg); b_w.append(vb)
            # 한 슬롯 안의 priority 전송과 shared 전송은 동시(병렬)이므로 슬롯 필요시간 = max (합이 아님, 9/10)
            need = np.maximum(np.array(g_w), np.array(b_w))
            w = need / need.sum() if need.sum() > 0 else np.full(len(rounds), 1.0 / len(rounds))

        # ── 슬롯 실행: 슬롯마다 실제 목적지 결정 → 전력 → 전송 ──
        #   priority AP 는 정해진 저지연 STA 에게만 (only). shared AP 는 지금 큐 기준 EDCA 로 목적지 선택, 남으면 다음 STA.
        #   전달 시각 = TXOP 시작 + 폴링 + Σ(슬롯 제어 앞 + 데이터 + 제어 뒤)
        pre, post, elapsed = T_ROUND_PRE, T_ROUND_POST, T_EDCA_ACCESS + T_MAPC_OH
        for rd, frac in zip(rounds, w):
            dur = data_time * float(frac)
            elapsed += pre + rd.get('gap', 0.0)          # gap: Lee Co-TDMA 에서 CF-End 뒤 새 TXOP 획득·폴링 시간
            done = t + elapsed + dur
            targets = dict(rd['priority'])
            for a in rd['shared']:
                j = head_sta(a)
                if j is not None:
                    targets[a] = j
            targets = {a: j for a, j in targets.items() if len(q[j]) > 0}
            if targets:
                tx = [(a, j) for a, j in targets.items()]
                pw = power_control(tx, ch)
                live = list(targets)
                for a in live:
                    serve_ap(a, targets[a], live, pw, ch, q, sta_of, sta_kind, dur, done,
                             eff[a] if eff else 1.0, only=(a in rd['priority']))
            elapsed += dur + post

    # ── 집계 ──
    for j in range(n_all_sta):                       # 종료 시점에 큐에 남은 코호트 패킷은 마감 초과로 확정 (9/10)
        q[j].expire(sim_dur)
    def stat_sta(idxs):
        """측정 코호트 기준. viol = 마감 인지 손실률 = (재전송 폐기 + 마감 초과) / 생성."""
        lats = [v for j in idxs for v in q[j].lats]
        gen = sum(q[j].gen for j in idxs)
        dr = sum(q[j].drop_retry for j in idxs); dd = sum(q[j].drop_dead for j in idxs)
        return dict(p95=float(np.percentile(lats, 95)) if lats else 0.0,
                    mean=float(np.mean(lats)) if lats else 0.0,
                    viol=(dr + dd) / gen * 100 if gen else 0.0,
                    retry=dr / gen * 100 if gen else 0.0, dead=dd / gen * 100 if gen else 0.0)

    s_ll, s_be, s_all = stat_sta(ll_sta), stat_sta(be_sta), stat_sta(list(range(n_all_sta)))
    eval_dur = Queue.eval_stop - Queue.eval_start
    gs = g_stat / g_stat.sum() if g_stat.sum() > 0 else np.zeros(3)
    # 손실·지연은 생성 시각 코호트 기준, 처리량은 전달 완료 시각이 측정 구간 안인 비트 기준 (9/11)
    return dict(
        tp=sum(q[j].tp_bits for j in range(n_all_sta)) / eval_dur / 1e6,
        lat=s_all['mean'], loss=s_all['viol'],
        p95_ll=s_ll['p95'], lat_ll=s_ll['mean'], loss_ll=s_ll['viol'],
        lat_be=s_be['mean'], loss_retry=s_all['retry'], loss_dead=s_all['dead'],
        loss_retry_ll=s_ll['retry'], loss_dead_ll=s_ll['dead'],
        n_ll=len(ll_sta), n_ll_ap=int(is_ll.sum()), offered=sum(offered.values()), n_groups=len(clusters),
        offered_ll=sum(src[j].offered_mbps() for j in ll_sta),
        tp_ll=sum(q[j].tp_bits for j in ll_sta) / eval_dur / 1e6,      # 저지연 STA 앞 패킷만의 처리량 (10/1)
        tp_be=sum(q[j].tp_bits for j in be_sta) / eval_dur / 1e6,
        g_ll0=float(gs[0]), g_ll1=float(gs[1]), g_ll2=float(gs[2]),   # 평가 구간 TXOP×그룹 중 저지연 STA 0/1/2+ 비율
    )


def trials(model, n=30, **kw):
    rs = [simulate(model, seed=s, **kw) for s in range(n)]
    return {key: float(np.mean([r[key] for r in rs])) for key in rs[0]}


# ══════════════════════════════════════════════════════════════════════════
# 7. 제안 모델의 ML (H-MAB)  — 이전의 mapc_mab.py 를 통합 (9/9)
# ══════════════════════════════════════════════════════════════════════════
"""
MAB 기반 전력 · 슬롯 제어 (이전 mapc_mab.py, 9/9 통합)

근거
  "Coordinated Spatial Reuse Scheduling With Machine Learning in IEEE 802.11
   MAPC Networks"  https://arxiv.org/abs/2505.07278  (Wojnar et al., JSAC 2025)
    - 측정 없이 probing 으로 학습 (해보고 결과로 배움)
    - 계층적 MAB: Level 1 어떤 AP 들이 함께 / Level 2 어느 STA 에게 / Level 3 전력
    - 보상 = 정규화된 처리량
    - Sec. VI-D 에서 "클러스터 단위 C-SR" 을 향후 과제로 제시

본 연구의 대응
  Level 1 (AP 조합)   사용하지 않음. 보낼 데이터가 있는 AP 는 모두 보낸다 (사용자 설계).
                      그룹 안 동시 전송 여부는 규칙(rounds_proposed)이 정하고 ML 은 관여하지 않는다.
  Level 2 (STA 선택)  802.11e EDCA 우선순위 규칙이 대신함 (VO > VI > BE, 같으면 오래된 큐)
  Level 3 (전력)      Master AP 의 그룹 단위 전력 조합 MAB (POWER_MODE='joint'). 9/9 실측 (1000 Mbps, 흩어진 배치):
                        규칙만 668 / 저지연 손실 7.9  <  슬롯 ML + 전력 ML{6,12,24} 691 / 4.1  ≈  슬롯 ML + 전력 규칙 697 / 4.0
                      전력 ML 은 문맥 (그룹, AP 수) + 3 단계 arm 으로 두어야 5 초 안에 배운다.
                      Master AP 가 같은 슬롯의 그룹 AP 들의 전력 조합을 한꺼번에 고른다 (그룹 단위 에이전트).
                      AP 마다 {6, 12, 24} dBm, 조합 = 3^n (n ≤ JOINT_MAX, 큐 긴 순). 규칙 기준값 없음.
                      혼자 보내면 24 dBm 고정 (멘토님 9/3). off 없음 (보낼 게 있으면 보낸다).
                      문맥 = (그룹, 같은 슬롯의 그룹 AP 수). 보상 = 공통 보상. 탐색·갱신은 시뮬레이션 내내 계속.
                      같은 슬롯에서 자기 그룹에 혼자인 AP 들(priority 슬롯의 그룹 대표들)은 그룹 간
                      간섭을 주고받으므로 하나의 조합 에이전트로 묶는다 (교수님 8/19 "옆 그룹에 영향 안 주게").
                      ※ 9/8 검증 (1000 Mbps, 5 seed): 규칙 전력 제어 555 / ML 조합 626 / 같은 조합 무작위 599
                      ※ 시도했으나 채택하지 않은 것 (9/8):
                         - AP 마다 독립 MAB (절대값 또는 규칙 보정) → 다 같이 최저로 수렴, 처리량 -15 %
                         - Yu et al. (2506.14187) 식 5 개별 벌점  → 효과 없음
                         - 규칙 전력 위에 그룹 단위 보정 조합     → 568. 규칙이 전력을 과도하게 낮춰 ML 발목
                         원인: 전력은 그룹이 함께 정해야 하는 문제 (Wojnar 각주 4). 독립 학습으로는 조합을 못 찾음.
  슬롯 (논문에 없음)  TXOP 안의 모든 슬롯 길이를 MAB 가 두 단계로 정한다. 규칙 기준값 없음.
                      ① priority 슬롯(저지연 우선 전송이 하나라도 있는 슬롯) 전체 : shared 전용 슬롯 전체 비율 {10~90 %}
                         문맥 = (슬롯 수, 저지연 앱 종류 집합, shared 전용 슬롯 있는지)
                      ② 같은 종류 슬롯끼리 가중치 {1..5}, 길이 = 가중치 / 합
                         문맥 = (슬롯의 트래픽 종류 집합, 큐 크기 구간)  ← 교수님 8/05 "트래픽 빈도와 양"
                      ※ 슬롯마다 독립 에이전트가 한 번에 가중치를 고르는 방식은 저지연 슬롯이 모두 커져
                         일반이 밀림 (1000 Mbps 557). 두 단계로 나누면 626 수준 유지 (9/8).

  그룹핑 · Case 판정 · c-SR/c-TDMA 라운드 구성은 mapc.py 의 규칙 그대로 (rounds_proposed).

  보상
    'cls'  ½·(저지연 전달 / 저지연 큐) + ½·(전체 전달 / 전체 큐)   ← 기본값. 두 항 모두 0~1 (9/10 스케일 수정)
    'tp'   전달 비트 / 이론 최대 (Wojnar 원래 보상. ablation 용)
    'lat'  전달 패킷 평균 지연의 음수  (논문 Sec. VIII 이 향후 과제로 제시. 식은 본 연구 설계)
    ※ 'loss' 보상은 폐기 (5.5 ms 창에 BG 마감이 안 걸려 BG 를 굶김). 코드에서 제거.

  학습: 처음부터 끝까지 온라인 UCB (탐색 종료 단계 없음). 앞 60 % 는 warm-up 이라 통계에서 제외. 배치마다 독립 학습.

알고리즘  UCB1. 탐색 계수는 슬롯(C_SLOT)·전력(C_POWER)을 분리해 튜닝 seed 에서 결정 (현재 0.1 / 0.1)
  https://arxiv.org/abs/2505.07278 이 ε-greedy · Softmax · Thompson 과 비교해 H-MAB 에 UCB 가 최적이라 보고

검증: RANDOM_POLICY=True 로 두면 학습 없이 무작위 선택. MAB 가 실제로 배우는지 비교용.
"""

RANDOM_POLICY = False                     # True 면 MAB 대신 무작위 선택 (학습 효과 검증용)
# UCB 탐색 계수. Wojnar 는 계층마다 별도 하이퍼파라미터를 두고 Optuna 로 튜닝했다 (Sec. V).
#   본 연구도 슬롯·전력을 분리하고, 최종 실험에 쓰지 않는 튜닝 seed 에서 평균 보상이 최대인 값으로 결정한다 (9/11).
C_SLOT  = 0.3                              # 튜닝 seed 100~109 에서 평균 보상 최대 (9/11 재튜닝, 보상식 변경 후)
C_POWER = 0.1
POWER_MODE = 'joint'                        # 'joint' = 그룹 단위 전력 조합 MAB (제안 모델, 9/9 확정), 'rule' = 기고문 전력 제어 (ablation 용)
POWER_ARMS = [6.0, 12.0, 24.0]              # 그룹 안 AP 마다 고를 절대 전력 (dBm). 9/9: 4단계(64조합)보다 3단계(27조합)가 탐색 비용이 적어 더 잘 배움
JOINT_MAX  = 3                              # 조합 선택 대상 AP 상한 (큐 긴 순). 넘는 AP 는 24 dBm. 3^3 = 27 arm
# 슬롯 가중치 선택지. 슬롯 길이 = 가중치 / 합. 교수님 8/05 "인풋은 트래픽 빈도와 양, 아웃풋은 슬롯 길이"
SLOT_ARMS  = [1, 2, 3, 4, 5]                # ② 같은 종류 슬롯끼리 가중치
LL_ARMS    = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]   # ① 저지연 슬롯 전체가 차지할 비율
Q_BUCKETS  = [100, 500]                     # 슬롯의 AP 최대 큐(프레임) 구간 경계 → 0 / 1 / 2. 설계값 (VR 버스트 = 111 프레임)
# MAB 의 문맥(입력) 에 트래픽 종류를 넣는다. 앱 종류가 빈도·양·우선순위를 모두 담는다.
#   VR = 33 ms 마다 167 KB, VO / VC = 33 ms 마다 8 KB, VI / BG = 200 KB, BE


class UCB:
    rng = np.random.default_rng(0)             # RANDOM_POLICY 검증용. simulate_mab 이 seed 로 다시 설정

    def __init__(self, n_arms, c):
        self.n = np.zeros(n_arms)
        self.q = np.zeros(n_arms)
        self.t = 0
        self.c = c

    def select(self):
        """Wojnar Algorithm 1 과 동일하게 처음부터 끝까지 온라인 UCB (탐색을 끄는 단계 없음, 9/10).
        평가 구간에 처음 보는 문맥이 나와도 probing 으로 자연히 처리된다."""
        self.t += 1
        if RANDOM_POLICY:                       # 검증용: 학습 없이 무작위
            return int(UCB.rng.integers(self.n.size))
        untried = np.where(self.n == 0)[0]
        if len(untried):
            return int(untried[0])
        return int(np.argmax(self.q + self.c * np.sqrt(np.log(self.t) / self.n)))

    def update(self, arm, r):
        self.n[arm] += 1
        self.q[arm] += (r - self.q[arm]) / self.n[arm]


def simulate_mab(seed, reward='cls', sim_dur=5.0, train_frac=0.6, **kw):
    """
    제안 모델 (라운드 구성은 rounds_proposed 그대로) 에
    전력 · 슬롯 비율을 MAB 로 정한다. 활성 AP 는 모두 전송한다.
    MAB 는 처음부터 끝까지 온라인 학습·탐색 (Wojnar Algorithm 1). train_frac 은 통계 측정 시작 시점(warm-up)일 뿐이다.
    """
    n_ap = kw.get('n_ap', N_AP); n_sta = kw.get('n_sta', N_STA)
    k = kw.get('k', K)
    total_load = kw.get('total_load', 1200.0)
    area = kw.get('area', AREA); d_sta = kw.get('d_sta', D_STA)

    rng = np.random.default_rng(seed)
    UCB.rng = np.random.default_rng(seed + 10_000)
    ap_pos, sta_pos, owner = make_topology(n_ap, n_sta, rng, area, d_sta)
    ch = Channel(ap_pos, sta_pos, rng)
    sta_kind, src, clusters, place = assign_traffic(ap_pos, sta_pos, owner, rng, k, ch, total_load)
    n_all_sta = len(sta_pos)
    ll_sta = [j for j in range(n_all_sta) if TRAFFIC[sta_kind[j]]['is_ll']]
    be_sta = [j for j in range(n_all_sta) if not TRAFFIC[sta_kind[j]]['is_ll']]
    offered = {j: src[j].offered_mbps() for j in range(n_all_sta)}
    q = {j: Queue(TRAFFIC[sta_kind[j]]['deadline']) for j in range(n_all_sta)}
    sta_of = {i: [j for j in range(n_all_sta) if owner[j] == i] for i in range(n_ap)}

    def active_stas(i, ll_only=False):
        return [j for j in sta_of[i] if len(q[j]) > 0 and (not ll_only or TRAFFIC[sta_kind[j]]['is_ll'])]

    def head_sta(i, ll_only=False):
        js = active_stas(i, ll_only)
        return min(js, key=lambda j: (AC_RANK[TRAFFIC[sta_kind[j]]['ac']], -len(q[j]), q[j].q[0])) if js else None

    def ap_qlen(i):
        return sum(len(q[j]) for j in sta_of[i])

    # 단독 링크 기준 속도 (보상 정규화용, 간섭 없음·최대 전력)
    raw0, p0 = {}, {}
    for j in range(n_all_sta):
        raw0[j], p0[j] = link_stats(sinr_from_loss(MAX_TX_POWER, ch.loss_mean(owner[j], j), []))

    # ── MAB 에이전트 (문맥마다 UCB 하나씩) ──
    pw_agents = {}
    sl_agents = {}
    ap2c = {a: c for c, m in clusters.items() for a in m}

    def ll_agent(n_rounds, ll_kinds, has_shared):
        """① priority 슬롯 전체 : shared 전용 슬롯 전체 비율 MAB. 문맥 = (슬롯 수, 저지연 앱 종류 집합, shared 전용 슬롯 있는지)."""
        key = ('LL', min(n_rounds, 6), ll_kinds, has_shared)
        if key not in sl_agents:
            sl_agents[key] = UCB(len(LL_ARMS), c=C_SLOT)
        return sl_agents[key]

    def sl_agent(kinds, qb):
        """② 같은 종류 슬롯끼리 가중치 MAB. 문맥 = (슬롯 트래픽 종류 집합, 큐 크기 구간)."""
        key = (kinds, qb)
        if key not in sl_agents:
            sl_agents[key] = UCB(len(SLOT_ARMS), c=C_SLOT)
        return sl_agents[key]

    n_txop = int(sim_dur / TAU)
    t_train = int(n_txop * train_frac)
    Queue.eval_start = t_train * TAU              # 측정 코호트 (9/10)
    Queue.eval_stop = max(sim_dur - MAX_DEADLINE, Queue.eval_start)
    reward_log = []
    g_stat = np.zeros(3)
    max_bits = DATA_RATES[-1] * 1e6 * TAU * n_ap    # 보상 정규화용

    for step in range(n_txop):
        t = step * TAU
        if step == t_train:
            g_stat[:] = 0
        ch.new_txop()
        for j in range(n_all_sta):
            q[j].push(src[j].arrivals(t - TAU, t, rng)); q[j].expire(t)   # 이전 TXOP 동안 도착한 패킷만
        active = {i for i in range(n_ap) if active_stas(i)}
        if not active:
            continue
        prio_of = {i: sorted(active_stas(i, True), key=lambda j: (AC_RANK[TRAFFIC[sta_kind[j]]['ac']], -len(q[j]), q[j].q[0]))
                   for i in active}
        rank_of = {a: (AC_RANK[TRAFFIC[sta_kind[prio_of[a][0]]]['ac']] if prio_of.get(a) else 9,
                       -sum(len(q[j]) for j in (prio_of.get(a) or sta_of[a])),
                       min((q[j].q[0] for j in (prio_of.get(a) or sta_of[a]) if len(q[j])), default=1e9))
                   for a in active}
        rounds = rounds_proposed(clusters, prio_of, active, rank_of)
        if not rounds:
            continue
        if step >= t_train:
            for m in clusters.values():                    # 그룹의 저지연 서비스 AP 수 0 / 1 / 2+
                g_stat[min(sum(1 for a in m if a in active and prio_of.get(a)), 2)] += 1
        data_time = max(TAU - (T_EDCA_ACCESS + T_MAPC_OH + len(rounds) * T_ROUND_OH), 0.0)   # TXOP 획득 + 폴링 + 슬롯 제어

        # ── 슬롯 길이 (두 단계, 모두 MAB) ──
        #   priority 슬롯 = 저지연 우선 전송이 하나라도 있는 슬롯 (다른 그룹의 shared 전송과 섞일 수 있음)
        #   shared 전용 슬롯 = 모든 그룹이 shared 인 슬롯
        chosen_sl = []; picked_sl = {}
        pr_idx = [i for i, rd in enumerate(rounds) if rd['priority']]
        sh_idx = [i for i, rd in enumerate(rounds) if not rd['priority']]
        if pr_idx and sh_idx:
            ll_kinds = tuple(sorted({sta_kind[j] for i in pr_idx for a in rounds[i]['priority'] for j in active_stas(a, True)}))
            ag = ll_agent(len(rounds), ll_kinds, True)
            arm = ag.select(); chosen_sl.append((ag, arm))
            f_ll = LL_ARMS[arm]
        else:
            f_ll = 1.0 if pr_idx else 0.0
        w = np.zeros(len(rounds))
        for idxs, share in ((pr_idx, f_ll), (sh_idx, 1.0 - f_ll)):
            if not idxs:
                continue
            wts = []
            for i in idxs:
                rd = rounds[i]
                if rd['priority']:                 # 문맥 = priority AP 들이 이 슬롯에서 서비스할 저지연 STA 전체 (종류, AP 별 큐 합의 최대)
                    kinds = tuple(sorted({sta_kind[j] for a in rd['priority'] for j in active_stas(a, True)}))
                    qsum = max((sum(len(q[j]) for j in active_stas(a, True)) for a in rd['priority']), default=0)
                else:                              # shared 전용 슬롯: AP 전체 큐 중 최대
                    kinds = ('SHARED',)
                    qsum = max((ap_qlen(a) for a in rd['shared']), default=0)
                qb = int(np.searchsorted(Q_BUCKETS, qsum))
                if len(idxs) == 1:
                    wts.append(1.0); continue
                ag = sl_agent(kinds, qb)
                if (kinds, qb) not in picked_sl:
                    picked_sl[(kinds, qb)] = ag.select(); chosen_sl.append((ag, picked_sl[(kinds, qb)]))
                wts.append(float(SLOT_ARMS[picked_sl[(kinds, qb)]]))
            for i, wt in zip(idxs, wts):
                w[i] = share * wt / sum(wts)
        w = w / w.sum()

        # 보상 정규화용 기준 용량 (9/11):
        #   채널은 하나이므로 한 TXOP 의 기준은 "간섭 없는 단일 링크가 data_time 동안 보낼 수 있는 비트" 이다.
        #   속도는 지금 전송할 활성 링크들의 단독 유효 속도 평균을 쓴다 (링크 품질 반영, 행동과 무관).
        #   공간 재사용으로 이를 초과할 수 있으므로 보상은 1 로 clip 한다.
        #   ※ 활성 AP 들의 속도를 "합" 으로 두면 한 채널에서 동시에 낼 수 없는 양(활성 15 대 기준 약 10 Gbps)이
        #     분모가 되어 이 항이 다시 0.03 으로 죽는다 (9/11 실측).
        _rates = [raw0[_j] * p0[_j] for a in active for _j in [head_sta(a)] if _j is not None]
        cap_all = (sum(_rates) / len(_rates) * data_time) if _rates else 0.0

        # ── 슬롯 실행: 목적지 결정 → 그룹 단위 전력 조합 MAB → 전송 ──
        # 학습용 성공량은 측정 구간과 무관해야 한다 (q.lats 는 코호트 전용이라 warm-up 에 0 → 보상 0, 9/11 수정)
        sent_before = {j: q[j].sent_bits for j in range(n_all_sta)}
        q_before = {j: len(q[j]) for j in range(n_all_sta)}
        lats = []; elapsed = T_EDCA_ACCESS + T_MAPC_OH
        chosen_pw = []; picked_pw = {}
        for rd, frac in zip(rounds, w):
            dur = data_time * float(frac)
            elapsed += T_ROUND_PRE
            done = t + elapsed + dur
            targets = dict(rd['priority'])
            for a in rd['shared']:
                j = head_sta(a)
                if j is not None:
                    targets[a] = j
            targets = {a: j for a, j in targets.items() if len(q[j]) > 0}
            if targets:
                live = list(targets)
                powers = {a: MAX_TX_POWER for a in live}     # 기본 24: 혼자 보내거나 조합 대상 밖이면 그대로
                if POWER_MODE == 'rule':
                    powers = power_control([(a, targets[a]) for a in live], ch)
                elif len(live) >= 2:
                    by_g = {}
                    for a in live:
                        by_g.setdefault(ap2c[a], []).append(a)
                    singles = [mem[0] for mem in by_g.values() if len(mem) == 1]
                    groups = [(gid, mem) for gid, mem in by_g.items() if len(mem) >= 2]
                    if len(singles) >= 2:              # 그룹에 혼자인 AP 들끼리 그룹 간 간섭 조율
                        groups.append(('X', singles))
                    for gid, mem in groups:
                        mem = sorted(mem, key=lambda a: -ap_qlen(a))[:JOINT_MAX]
                        key = (gid, len(mem))
                        if key not in pw_agents:
                            pw_agents[key] = UCB(len(POWER_ARMS) ** len(mem), c=C_POWER)
                        ag = pw_agents[key]
                        if key not in picked_pw:       # 같은 TXOP 에서 같은 문맥은 한 번만 선택·갱신
                            picked_pw[key] = ag.select()
                            chosen_pw.append((ag, picked_pw[key]))
                        code = picked_pw[key]
                        for a in mem:
                            powers[a] = POWER_ARMS[code % len(POWER_ARMS)]; code //= len(POWER_ARMS)
                for a in live:
                    lats.extend(serve_ap(a, targets[a], live, powers, ch, q, sta_of, sta_kind, dur, done,
                                         only=(a in rd['priority'])))
            elapsed += dur + T_ROUND_POST
        sent_bits = sum(q[j].sent_bits - sent_before[j] for j in range(n_all_sta))

        # ── 보상 ──
        if reward == 'tp':
            r = sent_bits / max_bits
        elif reward == 'cls':
            # 두 항 모두 "TXOP 시작 큐 대비 전달 비율" (0~1). 이론 최대 대비 처리량(≈0.04)을 쓰면 저지연 항(0~1)이
            # 사실상 보상을 독점해 ML 이 처리량을 버리고 저지연만 좇는다 (9/10 실측). 저지연 큐 없으면 전체 항만.
            ll_sent = sum(q[j].sent_bits - sent_before[j] for j in ll_sta)
            ll_need = sum(q_before[j] for j in ll_sta) * FRAME_LEN
            #   전체 항의 분모 = min(전체 큐, 이번 TXOP 에 간섭 없이 처리 가능한 비트) (9/11 수정)
            #   누적 backlog 를 그대로 분모로 쓰면 고부하에서 분모가 폭주해 이 항이 0.01 로 죽는다 (실측 0.786 vs 0.013).
            #   분모는 행동과 무관한 기준 용량이라 MAB 가 분모를 조작할 수 없다.
            all_need = sum(q_before.values()) * FRAME_LEN
            den_all = min(all_need, cap_all)
            r_all = min(sent_bits / den_all, 1.0) if den_all > 0 else 1.0
            r = 0.5 * min(ll_sent / ll_need, 1.0) + 0.5 * r_all if ll_need > 0 else r_all
        elif reward == 'lat':
            r = -(np.mean(lats) / 50.0) if lats else -1.0
        else:
            raise ValueError(f"unknown reward '{reward}' (use 'cls', 'tp', 'lat')")
        for ag, arm in chosen_pw:
            ag.update(arm, r)
        for ag, arm in chosen_sl:
            ag.update(arm, r)
        reward_log.append(r)

    for j in range(n_all_sta):                       # 종료 시점에 큐에 남은 코호트 패킷은 마감 초과로 확정
        q[j].expire(sim_dur)
    eval_dur = Queue.eval_stop - Queue.eval_start
    def stat(idxs):
        lats = [v for j in idxs for v in q[j].lats]
        gen = sum(q[j].gen for j in idxs)
        dr = sum(q[j].drop_retry for j in idxs); dd = sum(q[j].drop_dead for j in idxs)
        return dict(mean=float(np.mean(lats)) if lats else 0.0,
                    viol=(dr + dd) / gen * 100 if gen else 0.0,
                    retry=dr / gen * 100 if gen else 0.0, dead=dd / gen * 100 if gen else 0.0)
    s_ll = stat(ll_sta); s_all = stat(list(range(n_all_sta))); s_be = stat(be_sta)
    is_ll_ap = [any(TRAFFIC[sta_kind[j]]['is_ll'] for j in sta_of[i]) for i in range(n_ap)]
    gs = g_stat / g_stat.sum() if g_stat.sum() > 0 else np.zeros(3)
    return dict(tp=sum(q[j].tp_bits for j in range(n_all_sta)) / eval_dur / 1e6,
                lat=s_all['mean'], loss=s_all['viol'],
                lat_ll=s_ll['mean'], loss_ll=s_ll['viol'], lat_be=s_be['mean'],
                loss_retry=s_all['retry'], loss_dead=s_all['dead'],
                loss_retry_ll=s_ll['retry'], loss_dead_ll=s_ll['dead'],
                n_ll=len(ll_sta), n_ll_ap=int(sum(is_ll_ap)), offered=sum(offered.values()), n_groups=len(clusters),
                offered_ll=sum(src[j].offered_mbps() for j in ll_sta),
                tp_ll=sum(q[j].tp_bits for j in ll_sta) / eval_dur / 1e6,
                tp_be=sum(q[j].tp_bits for j in be_sta) / eval_dur / 1e6,
                g_ll0=float(gs[0]), g_ll1=float(gs[1]), g_ll2=float(gs[2]),
                reward_log=reward_log, pw_agents=pw_agents, sl_agents=sl_agents)


def trials_mab(reward='cls', n=10, **kw):
    rs = [simulate_mab(seed=s, reward=reward, **kw) for s in range(n)]
    return {k: float(np.mean([r[k] for r in rs])) for k in rs[0] if k not in ('reward_log','pw_agents','sl_agents')}


# ══════════════════════════════════════════════════════════════════════════
# 8. 실험 및 그래프
#     x 축 = 전체 트래픽 로드 (멘토님 2026-09-04 지시)
#     지표 = 처리량 · 저지연 평균 지연 · 저지연 손실률 (3 개)
# ══════════════════════════════════════════════════════════════════════════
N_AP, N_STA, K = 20, 2, None      # K=None → 센터 노드 기반 자동 결정
AREA, D_STA = 80.0, 5.0
LOAD_PER_AP = 100.0                # AP 수 실험에서 AP 당 부하 (Mbps)
AP_COUNTS = [5, 10, 15, 20, 25, 30]
LL_RATIO = 0.25            # (미사용. 실제 배정은 P_LL) 호출부 호환용
EXTRA_KEYS = ['lat_be', 'loss_retry', 'loss_dead', 'loss_retry_ll', 'loss_dead_ll',
              'n_ll', 'n_ll_ap', 'offered', 'offered_ll', 'tp_ll', 'tp_be', 'n_groups', 'g_ll0', 'g_ll1', 'g_ll2']   # 그래프 외 진단값
N_TRIAL = 8
LOADS = [400, 500, 600, 700, 800, 900, 1000]   # Mbps, 100 간격 (9/10 결정). 하한 400 = 저지연 고정 부하 최대(~330) 보다 위

#   비교 대상은 종래 3 종 + 제안 모델 2 종 (9/14: rule 을 기본 실험에 포함).
#     'proposed' = 제안 구조(그룹핑·Case·슬롯)에 슬롯 길이는 802.11e Medium Time 비례, 전력은 Park 기고문 규칙 (ML 없음)
#     'mab'      = 같은 구조에 슬롯 길이·전력을 계층적 MAB 로 학습 (제안 모델)
MODELS = [
    ('csma',       'CSMA/CA',               '#B8860B', 'o', ':',  False),
    ('conv-csr',   'only c-SR',             '#5A6478', 's', '--', False),
    ('conv-tdma',  'only c-TDMA',           '#7F77DD', '^', '--', False),
    ('proposed',   'Proposed (Rule-based)', '#D85A30', 'v', '--', False),
    ('mab',        'Proposed (ML-based)',   '#1D9E75', 'D', '-',  True),   # 보상 = ½ 저지연 전달률 + ½ 전체 전달률
]
PROPOSED_LABEL = 'Proposed (ML-based)'          # 진단 출력에서 기준으로 쓰는 모델 라벨
PANELS = [
    ('tp',      'Aggregate throughput (Mbps)',                  'throughput'),
    ('lat',     'Mean packet latency, all traffic (ms)',        'latency'),
    ('loss',    'Packet loss ratio, all traffic (%)',           'loss'),
    ('lat_ll',  'Mean latency of low-latency traffic (ms)',     'latency_ll'),
    ('loss_ll', 'Packet loss ratio of low-latency traffic (%)', 'loss_ll'),
]

PLOT_MODELS_LL = [lab for _, lab, *_ in MODELS]
PLOT_LABEL = {}                                 # 그래프 레전드 표기용 치환 (필요 시)

plt.rcParams.update({'font.size': 12, 'axes.grid': True, 'grid.alpha': 0.3,
                     'legend.fontsize': 10})


def run_experiment(n_trial=N_TRIAL, loads=LOADS):
    keys = [p[0] for p in PANELS] + EXTRA_KEYS
    R = {lab: {k: [] for k in keys} for _, lab, *_ in MODELS}
    for L in loads:
        for mid, lab, *_ in MODELS:
            if mid == 'mab':
                res = trials_mab(reward='cls', n=n_trial, n_ap=N_AP,
                                          n_sta=N_STA, k=K, ll_ratio=LL_RATIO,
                                          total_load=float(L), area=AREA, d_sta=D_STA)
            else:
                res = trials(mid, n=n_trial, n_ap=N_AP, n_sta=N_STA, k=K,
                             ll_ratio=LL_RATIO, total_load=float(L),
                             area=AREA, d_sta=D_STA)
            for key in keys:
                R[lab][key].append(res[key])
        print(f'  load {L:>5} Mbps 완료', flush=True)
    return R


def plot(R, loads=LOADS, models=None):
    models = PLOT_MODELS_LL if models is None else models
    for key, ylab, suffix in PANELS:
        fig, ax = plt.subplots(figsize=(7.4, 5.3))
        for _, lab, color, mk, ls, fill in MODELS:
            if lab not in models:
                continue
            ys = R[lab][key]
            if key in ('lat', 'lat_ll'):
                ys = [y if y > 0 else float('nan') for y in ys]
            ax.plot(loads, ys, marker=mk, linestyle=ls, linewidth=2.2, label=PLOT_LABEL.get(lab, lab),
                    color=color, markeredgecolor=color, markersize=8,
                    markeredgewidth=2, markerfacecolor=(color if fill else 'white'))
        ax.set_xlabel('Offered traffic load (Mbps)')
        ax.set_ylabel(ylab)
        ax.set_xticks(loads)
        ax.legend(loc='best', framealpha=0.9)
        fig.tight_layout()
        fig.savefig(f'fig_{suffix}.png', dpi=200, bbox_inches='tight')
        plt.show()
        plt.close(fig)


def print_tables(R, loads=LOADS):
    for key, ylab, _ in PANELS:
        print(f'\n[{ylab}]')
        hdr = f'{"load":>6} | ' + ' | '.join(f'{lab:>12}' for _, lab, *_ in MODELS)
        print(hdr + '\n' + '-' * len(hdr))
        for i, L in enumerate(loads):
            print(f'{L:>6} | ' +
                  ' | '.join(f'{R[lab][key][i]:>12.1f}' for _, lab, *_ in MODELS))


def run_ap_experiment(n_trial=N_TRIAL, counts=AP_COUNTS):
    """실험 2: AP 수를 바꿔가며 (AP 당 부하 고정, 그룹 자동 결정)"""
    keys = [p[0] for p in PANELS] + ['n_groups']
    R = {lab: {k: [] for k in keys} for _, lab, *_ in MODELS}
    for n in counts:
        for mid, lab, *_ in MODELS:
            if mid == 'mab':
                res = trials_mab(reward='cls', n=n_trial, n_ap=n, n_sta=N_STA, k=K, ll_ratio=LL_RATIO,
                                 total_load=LOAD_PER_AP * n, area=AREA, d_sta=D_STA)
            else:
                res = trials(mid, n=n_trial, n_ap=n, n_sta=N_STA, k=K,
                             ll_ratio=LL_RATIO, total_load=LOAD_PER_AP * n,
                             area=AREA, d_sta=D_STA)
            for key in keys:
                R[lab][key].append(res[key])
        print(f'  AP {n:>2}대 (그룹 {R[PROPOSED_LABEL]["n_groups"][-1]:.1f}개) 완료')
    return R


def plot_ap(R, counts=AP_COUNTS):
    for key, ylab, suffix in PANELS:
        fig, ax = plt.subplots(figsize=(7.4, 5.3))
        for _, lab, color, mk, ls, fill in MODELS:
            ys = R[lab][key]
            if key in ('lat', 'lat_ll'):
                ys = [y if y > 0 else float('nan') for y in ys]
            ax.plot(counts, ys, marker=mk, linestyle=ls, linewidth=2.2, label=lab,
                    color=color, markeredgecolor=color, markersize=8,
                    markeredgewidth=2, markerfacecolor=(color if fill else 'white'))
        ax.set_xlabel(f'Number of APs (load {LOAD_PER_AP:.0f} Mbps per AP)')
        ax.set_ylabel(ylab)
        ax.set_xticks(counts)
        ax.legend(loc='best', framealpha=0.9)
        fig.tight_layout()
        fig.savefig(f'fig_ap_{suffix}.png', dpi=200, bbox_inches='tight')
        plt.show()
        plt.close(fig)


def print_ap_tables(R, counts=AP_COUNTS):
    for key, ylab, _ in PANELS:
        print(f'\n[{ylab}]')
        hdr = f'{"APs":>5} {"grp":>4} | ' + ' | '.join(f'{lab:>12}' for _, lab, *_ in MODELS)
        print(hdr + '\n' + '-' * len(hdr))
        for i, n in enumerate(counts):
            print(f'{n:>5} {R[PROPOSED_LABEL]["n_groups"][i]:>4.1f} | ' +
                  ' | '.join(f'{R[lab][key][i]:>12.1f}' for _, lab, *_ in MODELS))



# ══════════════════════════════════════════════════════════════════════════
# 9. 실험 2: 저지연 트래픽 비율 (교수님 8/19 "x축을 저지연 비율로")
#     전체 로드 고정, 저지연 STA 비율(N_LL_EXACT) 을 바꿔 가며. 그래프 레전드는 4개 (rule 제외)
# ══════════════════════════════════════════════════════════════════════════
LL_LOAD_TOTAL = 800.0                       # Mbps, 실험 2 의 전체 로드 (용량 근처)
LL_RATIOS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]   # 저지연 STA 비율, 5 % 간격 (40 대 중 4~20 대) (9/10 결정)


def run_ll_experiment(n_trial=N_TRIAL, ratios=LL_RATIOS, total_load=LL_LOAD_TOTAL):
    global N_LL_EXACT
    keys = [p[0] for p in PANELS] + ['n_ll', 'offered_ll']
    R = {lab: {k: [] for k in keys} for _, lab, *_ in MODELS}
    p0 = N_LL_EXACT
    for ratio in ratios:
        N_LL_EXACT = int(round(ratio * N_AP * N_STA))   # 비율 → 정확한 저지연 STA 수 (9/10)
        for mid, lab, *_ in MODELS:
            if mid == 'mab':
                res = trials_mab(reward='cls', n=n_trial, n_ap=N_AP, n_sta=N_STA, k=K,
                                          ll_ratio=ratio, total_load=float(total_load), area=AREA, d_sta=D_STA)
            else:
                res = trials(mid, n=n_trial, n_ap=N_AP, n_sta=N_STA, k=K, ll_ratio=ratio,
                             total_load=float(total_load), area=AREA, d_sta=D_STA)
            for key in keys:
                R[lab][key].append(res[key])
        print(f'  저지연 STA 비율 {ratio:.0%} (저지연 STA {R[PROPOSED_LABEL]["n_ll"][-1]:.1f}대, '
              f'{R[PROPOSED_LABEL]["offered_ll"][-1]:.0f} Mbps) 완료', flush=True)
    N_LL_EXACT = p0
    return R


def plot_ll(R, ratios=LL_RATIOS, models=PLOT_MODELS_LL):
    for key, ylab, suffix in PANELS:
        fig, ax = plt.subplots(figsize=(7.4, 5.3))
        for _, lab, color, mk, ls, fill in MODELS:
            if lab not in models:
                continue
            ys = R[lab][key]
            if key in ('lat', 'lat_ll'):
                ys = [y if y > 0 else float('nan') for y in ys]
            ax.plot([r * 100 for r in ratios], ys, marker=mk, linestyle=ls, linewidth=2.2, label=PLOT_LABEL.get(lab, lab),
                    color=color, markeredgecolor=color, markersize=8,
                    markeredgewidth=2, markerfacecolor=(color if fill else 'white'))
        ax.set_xlabel(f'Ratio of low-latency STAs (%)  (total load {LL_LOAD_TOTAL:.0f} Mbps)')
        ax.set_ylabel(ylab)
        ax.set_xticks([r * 100 for r in ratios])
        ax.legend(loc='best', framealpha=0.9)
        fig.tight_layout()
        fig.savefig(f'fig_ll_{suffix}.png', dpi=200, bbox_inches='tight')
        plt.close(fig)


def print_ll_tables(R, ratios=LL_RATIOS):
    for key, ylab, _ in PANELS:
        print(f'\n[{ylab}]')
        hdr = f'{"LL STA":>6} {"LL Mbps":>7} | ' + ' | '.join(f'{lab:>12}' for _, lab, *_ in MODELS)
        print(hdr + '\n' + '-' * len(hdr))
        for i, r in enumerate(ratios):
            print(f'{r:>6.0%} {R[PROPOSED_LABEL]["offered_ll"][i]:>7.0f} | ' +
                  ' | '.join(f'{R[lab][key][i]:>12.1f}' for _, lab, *_ in MODELS))

def main():
    quick = '--quick' in sys.argv
    n_trial = 3 if quick else N_TRIAL
    loads = [400, 700, 1000] if quick else LOADS
    t0 = time.time()
    print(f'[실험 1] 트래픽 로드 (AP {N_AP}대, {AREA:.0f}x{AREA:.0f}m, 그룹 자동, '
          f'반복 {n_trial}회)')
    R1 = run_experiment(n_trial, loads)
    print_tables(R1, loads)
    plot(R1, loads)
    import json
    json.dump({'loads': loads, 'results': R1}, open('results.json', 'w'), indent=1)
    print('\nresults.json 저장')
    print(f'\n총 {time.time() - t0:.0f}초')
    return R1


if __name__ == '__main__':
    main()
