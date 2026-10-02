# TAG-ST 연구 노트 (MobiSec 2026 → 특허 → SCI)

작성 기준일: 2026-09-29. 이 문서는 아이디어, 코드·실험 설정, 결과, 멘토·교수 피드백 반영 내역, 논문 검토 잔여 항목, 확장 계획을 한 곳에 정리한 것이다.

---

## 1. 제안 기법: TAG-ST (Traffic-Aware Grouping with Spatial-Temporal coordination)

### 1.1 문제
- 밀집 WLAN에서 같은 채널을 쓰는 BSS가 늘면 채널 경쟁과 BSS 간 간섭으로 처리량이 떨어지고 지연이 늘어난다.
- IEEE 802.11bn MAPC의 Co-SR은 동시 전송으로 경쟁을 줄이지만 간섭이 강한 AP끼리 동시에 쏘면 SINR이 떨어진다. Co-TDMA는 간섭은 없애지만 순차 전송이라 부하가 크면 처리량이 막힌다.
- latency-sensitive 트래픽은 deadline을 넘기면 폐기되므로 "제때 보내는가"가 문제다.
- 선행연구는 Co-SR 또는 Co-TDMA 하나를 고정한 채 그 안에서 전송 대상·전력·시간을 최적화하고, 학습을 써도 처리량만 목표로 한다.

### 1.2 핵심 아이디어 (한 줄)
Master AP가 (1) 인접 AP의 RSSI로 BSS를 그룹화하고, (2) TXOP마다 latency-sensitive 트래픽의 그룹별 분포를 보고 Co-SR과 Co-TDMA를 하나의 TXOP 안에서 조합하며, (3) 타임 슬롯 길이와 그룹별 송신 전력을 RL(H-MAB)로 조정한다.

### 1.3 구성 요소
**① RSSI 기반 BSS 그룹화 (초기화 단계, 이후 고정)**
- Master AP가 AP 간 RSSI와 트래픽 요구량을 수집.
- Center AP 선정: 트래픽 요구량이 적은 AP부터 후보. 기존 center AP들로부터의 RSSI가 −70 dBm(`CENTER_SEP_DBM`)보다 낮으면 새 center AP.
- 나머지 AP는 RSSI가 가장 큰 center AP의 그룹에 소속. non-AP STA는 소속 AP를 따라감.
- 20 AP 환경에서 평균 5.2개 그룹(최소 3, 최대 8), 그룹의 8.8%는 AP 1대짜리 단독 그룹. Master AP(전체 조정)와 center AP(그룹 기준 AP)는 다른 개념.

**② TXOP마다 협력 전송 구조 결정** (`rounds_proposed`)
- TXOP 시작 시 ICF/ICR로 각 AP의 데이터 유무와 LS 큐 유무를 수집.
- LS 없음(약 54%): 활성 그룹 전원 Co-SR (= Co-SR과 동일).
- Distributed traffic mode(약 32%): priority slot에 LS 서비스 AP가 먼저 전송. 다른 그룹끼리 동시(Co-SR), 같은 그룹 안 둘 이상이면 순서대로(Co-TDMA). LS 없는 그룹·전송 끝난 그룹은 대기. 이후 shared slot에 전원 Co-SR.
- Concentrated traffic mode(약 15%): LS가 몰린 그룹은 TXOP 전체를 Co-TDMA, 나머지 그룹은 동시에 Co-SR.
- Priority slot은 LS 트래픽이 있는 AP에만 배정되므로 슬롯 낭비 없음 (교수님 8/19 지적 대응).

**③ RL(H-MAB) 자원 조정** (Wojnar et al. 구조 차용, 학습 대상 변경)
- 슬롯 길이: 1단계 priority slot 비율 `LL_ARMS` 0.1~0.9, 2단계 동종 슬롯 상대 가중치 `SLOT_ARMS` 1~5. 문맥 = 슬롯의 트래픽 종류 + 큐 잔량 구간.
- 전력: 같은 슬롯에서 동시 전송하는 그룹 내 AP 전력 조합(`POWER_ARMS` {6,12,24} dBm, `JOINT_MAX` 3)을 그룹 단위 에이전트가 선택. 혼자 전송하면 24 dBm.
- UCB1, `C_SLOT` 0.3, `C_POWER` 0.1 (튜닝 seed 100~109).
- 보상 = ½·(LS 전달량/LS 큐) + ½·(전체 전달량/min(큐, 용량)).
- 사전 학습 없음. TXOP마다 결과로 갱신하는 온라인 학습. warm-up 60% 이후만 통계.

**비교 변형 TAG-ST (rule-based)**: 같은 구조, 슬롯 길이는 802.11e medium time 규칙, 전력은 Park et al. 목표 SINR 전력 제어.

### 1.4 실험 설정 (v1.9)
- Python 시뮬레이터. 80 m × 80 m, AP 20대 랜덤, AP당 STA 2대(1~5 m), 다운링크만, TGax enterprise 경로손실(벽 7 dB, 섀도잉 5 dB), 노이즈 −94 dBm, 최대 전력 24 dBm, 패킷 1,500 B, TXOP 5.484 ms, ICF/ICR 폴링 94 µs, 재전송 7회, 100회 반복.
- 트래픽: RTMG(80 B/23.06 ms, deadline 20 ms), VR(166.66 KB/33.33 ms, 20 ms), VC(7.81 KB/33.33 ms, 30 ms) = latency-sensitive; background = best-effort.
- 비교: CSMA/CA(EDCA), Co-SR(Park 전력 제어), Co-TDMA(Lee et al. 스케줄링), TAG-ST (rule-based), TAG-ST (RL-based).
- 시나리오 1: LS STA 25%, 로드 400~1,000 Mbps. 시나리오 2: 로드 800 Mbps, LS STA 10~50%.
- TXOP마다 master AP가 EDCA로 TXOP를 획득해 조정한다고 가정. TXOP 길이는 11ax 최대 PPDU 길이.

---

## 2. 결과 (100회 평균)

### 2.1 로드 1,000 Mbps
| 모델 | 처리량 (Mbps) | LS 지연 (ms) | LS 손실률 (%) |
|---|---|---|---|
| CSMA/CA | 76.2 | 15.30 | 72.15 |
| Co-SR | 656.0 | 9.88 | 41.75 |
| Co-TDMA | 591.1 | 7.98 | 3.15 |
| TAG-ST (rule-based) | 691.8 | 9.05 | 27.28 |
| TAG-ST (RL-based) | 764.1 | 6.57 | 1.10 |

RL vs Co-SR: 처리량 +16.5%, 지연 −33.5%, 손실 −97.4%. RL vs Co-TDMA: +29.3%, −17.7%, −65.2%. RL vs rule: +10.5%.

### 2.2 LS STA 비율 50% (800 Mbps)
| 모델 | 처리량 | LS 지연 | LS 손실률 |
|---|---|---|---|
| Co-SR | 549.5 | 9.67 | 35.68 |
| Co-TDMA | 569.3 | 8.46 | 7.94 |
| TAG-ST (rule-based) | 614.9 | 8.75 | 21.99 |
| TAG-ST (RL-based) | 686.7 | 7.27 | 2.80 |

RL vs Co-TDMA: 처리량 +20.6%, 지연 −14.1%, 손실 −64.8%. RL vs Co-SR: 지연 −24.8%, 손실 −92.2%.

### 2.3 Ablation (1,000 Mbps, 100회)
| 구성 | 처리량 | LS 지연 | LS 손실률 | 해석 |
|---|---|---|---|---|
| Co-SR | 656.0 | 9.88 | 41.7 | 기준 |
| + 협력 전송 구조 (rule-based) | 691.8 | 9.05 | 27.3 | priority slot 구조 |
| + 슬롯 길이 학습 | 672.0 | 6.52 | 1.34 | LS 보호의 핵심 |
| + 그룹별 전력 학습 (= TAG-ST) | 764.1 | 6.57 | 1.10 | 처리량 담당 |
| 그룹화 제거 (BSS 개별 그룹) | 689.3 | 7.14 | 5.44 | 그룹화 필요성 |
| 전체 한 그룹 | 435.4 | 7.49 | 5.81 | 붕괴 |
| Rule, 그룹화 제거 | 677.3 | 8.87 | 33.0 | |

- Priority slot 비중: rule 23%→5% (400→1,000 Mbps), RL 약 45% 유지 (계측).
- 슬롯 학습만 적용 시 처리량은 691.8→672.0으로 소폭 감소(priority 비중 증가로 shared slot 감소), 전력 학습이 회복.

### 2.4 Distributed mode에서 LS 없는 그룹의 대기 여부 (100회, RL 모델, `LL_INTRA`)
`'tdma'` = LS 없는 그룹이 priority slot 동안 대기(논문 채택, 9/11 확정), `'group'` = 처음부터 동시 전송. 그림 `figures/dtm_wait/`, 데이터 `results/cmp_wait_vs_nowait_sweep_100runs.json`.

| 구간 | 처리량 대기 / 동시 | LS 지연 대기 / 동시 | LS 손실 대기 / 동시 |
|---|---|---|---|
| 400 Mbps | 389.8 / 397.2 | 6.47 / 6.49 | 0.65 / 0.56 |
| 1,000 Mbps | 770.5 / 808.6 | 6.59 / 7.03 | 1.18 / 3.01 |
| LS 10% | 681.5 / 681.7 | 5.83 / 5.90 | 0.12 / 0.33 |
| LS 50% | 687.6 / 765.6 | 7.28 / 7.52 | 2.85 / 6.34 |

동시 전송 허용 시 처리량 +2~12%(LS 비율이 높을수록 큼), LS 지연 +0.2~0.5 ms, LS 손실 2~2.6배. 저부하·저비율에서는 차이 없음. LS 보호 목적에 맞게 대기 채택. 처리량 우선 환경이면 no-wait 정책으로 전환 가능(SCI 운영 정책 실험 소재).

### 2.5 솔직한 약점
- Rule-based는 지연·손실이 Co-TDMA보다 나쁘다 (구조만으로는 부족, 슬롯 학습 필요).
- 저부하(400 Mbps)에서 폴링 오버헤드로 처리량이 Co-TDMA보다 2~5% 낮다.
- 그룹은 초기화 때 고정. 트래픽 종류(`Source.kind`)도 시행당 고정. 이동성 없음.
- 다운링크만.

---

## 3. 피드백 반영 내역

### 3.1 교수님 (8/5, 8/19, 9/10)
| 발언 | 반영 |
|---|---|
| ML 그룹핑은 비현실적, 그룹핑은 알고리즘, ML은 슬롯 길이 (8/5) | 반영 |
| 센터 노드 + RSSI 소속, 그룹 수 중요 (8/5) | 반영 |
| LS 노드가 흩어지면 슬롯 1 우선 후 슬롯 2 CSR, 몰리면 CSR (8/19) | Case 1/2 → distributed/concentrated mode |
| LS 슬롯을 길게 잡으면 평균 지연 악화 → 비율에 따라 조절 (8/19) | 슬롯 길이 학습 |
| 보낼 것 없는 노드에 슬롯 고정 배정은 낭비 (8/19) | LS 큐 있는 AP에만 priority slot |
| Master AP가 그룹핑·슬롯·전력 결정 (8/19) | 반영 |
| x축 LS 비율, 비교 CSR/Co-TDMA/경쟁 (8/19) | 반영 |
| "저지연 AP"는 잘못된 용어, 주체는 STA (9/10) | 논문 표현 수정 ("~를 서비스하는 AP") |
| 다운링크만 고려했음 (9/10) | 4.1에 명시 |
| 그룹 = AP + 주변 STA, master AP가 STA 묶음을 AP에 할당 (9/10) | **미반영**, 확인 필요 |
| 이동·트래픽 변화에 따른 재그룹핑 (8/19) | **미반영** (SCI) |
| 그룹핑도 나중에 AI로 (8/5) | **미반영** (SCI) |
| 특허: 구성도·절차도·시그널링 필드, 표준 프레임 포맷 위에 추가 (8/19, 9/10) | 미착수 |

### 3.2 멘토님 (8/5, 8/19, 9/3, 9/4, 9/14 초안 주석)
- 케이스를 나눠 실험하지 말고 매 라운드 랜덤(9/3) → 반영.
- 그룹 내부: 동시 전송 시 지리 그룹 CSR, LS 그룹 Co-TDMA, 혼자면 최대 전력(9/3) → 반영.
- x축 트래픽 로드 추가, 지표 3개만, RL 가능, 파라미터 고정(9/4) → 반영.
- 초안 주석(9/14): 초록 흐름(기존 한계→Co-xx 한계→제안), 제안 모델 첫 서술 일반화, RL 기본 모델, 기여점 3개(수치 없음), 강화학습 등장 논리, 한계는 "동작→성능 저하"로, 약자 소문자, Center AP 정의, ML/RL 통일, 그림 글자 확대 → 대부분 반영.

---

## 4. 논문 v1.2 잔여 검토 항목
- MobiSec 템플릿은 저자-연도 인용. `[17]` → `(Zhu et al., 2025)`, Table 1 Ref 열도 동일.
- Fig. 7 캡션 "Throughput of latency-sensitive traffic" → "Aggregate throughput ...".
- 트래픽 모델 인용 [20](Zhang) → [21](Lee).
- 2장 Shah/Zhang/Lee 한계가 "검증되지 않았다"형 → 동작→성능 저하형으로.
- 3.1 "AP는 TXOP 시작 시 ICF…" → "Master AP는".
- 지연·손실 정의를 LS 트래픽으로 한정.
- Table 3 Background 행 값·단위 확인. 결론 6.57/7.27 ms vs 본문 6.6/7.3 통일. "8080 영역" → 80 m × 80 m.
- STA 약자 풀이(초록, 본문 첫 등장), Table 3 AC 풀이.
- Distributed mode 그림(A·B·C가 그룹마다 한 개인 경우): 코드는 priority 라운드 하나를 모든 AP가 같은 길이로 쓰고 shared도 같은 시점에 시작한다 (`simulate_mab`의 `dur = data_time * frac` 가 라운드 공통). 현재 그림은 A·B·C 길이와 shared 시작점이 그룹마다 달라 코드와 어긋남 → A·B·C를 같은 폭으로, shared 경계를 한 선으로 맞출 것. (10/2 확인)
- 참고문헌: `paper/References_MobiSec_format.docx` 참조. DOI 미확인 4편(Geraci, Nunez 2025, Yu, Lee GLOBECOM), Xplore URL 대체 4편, 802.11 문서 저자 전원 기재.

---

## 5. 확장 계획

### 5.1 순서
1. MobiSec 마무리.
2. 교수님께 확인: 그룹 재구성이 (a) STA는 원래 AP에 두고 master AP가 LS STA 집합을 논리 그룹으로 묶어 슬롯·전력 배정인지, (b) LS STA를 실제로 다른 AP로 옮기는 것인지. → SCI 구조와 특허 필드가 이 답에 따라 갈림.
3. 특허: master AP 동작부 구성도(정보 수집, 그룹 구성, 모드 결정, 자원 할당, 학습, 제어 프레임 생성), 수집 정보(RSSI, 트래픽 요구량, LS 존재, 큐 잔량)와 전달 정보(그룹, 동작 모드, 슬롯 할당, 전력)의 필드 정의, TGbn ICF/ICR·MAPC element 위에 매핑. ML은 "적용할 수도 안 할 수도"로 넓게. LS 슬롯 내부 접근(컨텐션 vs 조정 배정)은 둘 다 포함.
4. SCI.

### 5.2 SCI 핵심 논리
"STA의 트래픽 특성과 위치가 시간에 따라 바뀌는 환경에서는 고정 그룹 TAG-ST가 열화되므로, 느린 시간 척도에서 그룹을 재구성하고 학습기가 그 변화를 따라가게 한다."

주의: 지금 그룹은 RSSI(간섭)로만 만들므로 "트래픽 변화 → 재그룹핑" 트리거만 넣으면 그룹이 바뀌지 않아 효과가 없다. TXOP 수준 적응(LS 큐 유무에 따른 mode·슬롯)은 이미 동적이다. 재그룹핑이 의미를 가지려면 그룹 규칙에 트래픽이 들어가야 한다.

### 5.3 작업 항목
1. **비정상 시나리오 생성기**: STA별 트래픽 종류가 마르코프 전이로 바뀌는 모델(+ random waypoint 이동성). 시뮬레이션 시간 연장, warm-up 규칙 수정. 첫 실험 = 고정 그룹 TAG-ST의 열화 확인.
2. **트래픽 반영 그룹 규칙 + 두 시간 척도 제어**: 방향 1 = 그룹 크기(임계값/그룹 수)를 LS 분포에 따라 느린 주기로 갱신 (ablation의 그룹 수 민감도가 근거). 방향 2 = (교수님 확인 후) LS STA 집합을 AP에 할당. 재구성 주기별 비용·이득 → "천천히 바꿔도 된다"의 정량화.
3. **비정상 밴딧**: UCB1 → sliding-window / discounted UCB. 재그룹핑 시 에이전트 통계 승계(`pw_agents` 키가 그룹 구성원 집합이라 현재는 리셋됨). 재수렴 TXOP 수를 지표로. "그룹핑 AI"는 재그룹핑 시점/할당 학습으로.
4. **평가 확장·이론**: AP 수, 임계값, 영역 민감도. priority slot 비율 대 deadline 초과 확률 큐 모델.
5. **업링크**: 마지막에 저지연 UL 슬롯 하나 수준으로만.
6. **2페이지 학술대회 발표**: 위 1~2의 예비 결과로 가능 (유사성 주의).

---

## 6. 파일 목록
- `sim/mapc_grouping_HMAB_v1_9.py` 시뮬레이터 최종본 (논문 결과 생성 버전). 1081행 주석의 "0.1 / 0.1"은 오래된 값(실제 C_SLOT 0.3).
- `sim/run_parallel_v1_9.py` 본실험 병렬 실행, `sim/run_ablation_v1_9.py` ablation, `sim/cmp_wait.py` 대기 vs 동시 전송 비교, `sim/selftest_v1_9.py` 자체 검증, `sim/plot_paper_figs.py` 논문 그림(범례 TAG-ST).
- `results/*.json` 100회 결과(로드, LS 비율, ablation), 8 seed 대기 비교.
- `figures/paper/` Fig. 7~9. `figures/diagrams/` Fig. 1(center AP 표시 v3), Fig. 2 플로우차트 v10.
- `paper/References_MobiSec_format.docx` 샘플 형식 참고문헌.
