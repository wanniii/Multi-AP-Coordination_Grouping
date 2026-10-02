# TAG-ST 연구 인수인계 문서 (Claude 채팅용 컨텍스트)

작성: 2026-10-02. 이 문서 하나로 연구 전체 맥락을 전달하는 것이 목적이다. Claude 채팅(Projects)에 이 문서와 함께
`docs/RESEARCH_NOTES.md`, `sim/mapc_grouping_HMAB_v2_0.py`(또는 v1_9), 논문 v1.2 docx를 올리면 이어서 작업할 수 있다.

---

## 0. 한 줄 요약

**TAG-ST (Traffic-Aware Grouping with Spatial-Temporal coordination)**: IEEE 802.11bn MAPC(Multi-AP Coordination) 환경에서
Master AP가 (1) RSSI로 가까운 BSS들을 그룹화해 두고, (2) 매 TXOP마다 저지연(latency-sensitive) STA가 어느 그룹에 있는지 보고
Co-SR(그룹 간 동시 전송)과 Co-TDMA(그룹 안 순차 전송)를 섞어 쓰며, (3) 슬롯 길이·송신 전력을 계층형 MAB(강화학습)로 정한다.
MobiSec 2026 논문(v1.2, 한글 본문) + 표준 특허 준비 중. 이후 이 주제는 특허로 마무리하고 보안 기반 새 주제로 전환하는 쪽으로 기울어 있음.

## 1. 사람·일정

- 연구자: 홍채완 (학부연구생). 지도교수(회의록의 "교수님"), 멘토(박사과정, 회의록의 "멘토님").
- MobiSec 2026 영문 버전 마감: 10월 첫째 주 토요일. 융합보안학회(WISA 논문 그대로 양식만 맞춰) 10/8 제출.
- 교수님 10/1 지시: MobiSec 투고와 동시에 특허 출원 준비.

## 2. 용어 규칙 (반드시 지킬 것)

- "저지연 AP"라고 쓰지 않는다. 주체는 STA. → "저지연 STA", "저지연 STA를 서비스하는 AP".
- 그룹 = **BSS(AP + 소속 STA)** 의 묶음. "AP끼리 그룹"이라 쓰지 않는다. RSSI는 AP 사이에서 측정하지만 그룹에는 STA도 들어간다.
- 하향링크만 다룬다. 데이터는 항상 AP → STA. "A가 보낸다"가 아니라 "A에게 가는 데이터가 나간다 / A를 서비스하는 AP가 보낸다".
- 저지연 트래픽의 지연·손실률 = 저지연 STA를 목적지로 하는 패킷만 모은 값(STA는 트래픽 종류가 하나라 둘은 같은 뜻).
- 모델 이름: TAG-ST (rule-based) / TAG-ST (RL-based). 비교 모델: CSMA/CA, Co-SR, Co-TDMA.
- "Case 1/Case 2" 대신 "Distributed / Concentrated traffic mode". 발표에서는 "흩어져 있을 때 / 몰려 있을 때".
- 논문 어투: "~에 초점을 두다", "~를 다루지 않았다" 대신 "~를 충분히 다루지 못하였다". 약어는 첫 등장에 소문자 풀이.
- MobiSec 템플릿: 저자-연도 인용 (Zhu et al., 2025), 참고문헌은 인용 순서, 저널명 이탤릭.

## 3. 시스템 모델 (코드 v1.9 / v2.0 기준)

- 80 m × 80 m, AP 20대 균등 랜덤, AP마다 STA 2대(AP에서 1~5 m), 총 STA 40대. 단일 경쟁 영역(AP 쌍 99%가 CCA −82 dBm 이상 들림).
- Master AP 1대: 조정 AP(802.11bn sharing AP 역할). EDCA로 TXOP 획득 → ICF → 각 AP ICR 응답 → 트리거로 슬롯 배정.
- STA: 앱 종류가 하나씩. 확률 0.25로 저지연 앱(RTMG/VR/VC, Lee et al. arXiv:2508.18755 Table I), 아니면 배경(BG). 트래픽은 STA 단위로 정해지지만
  데이터는 AP 큐에 쌓여 AP가 보낸다. STA는 제어 프레임을 보내지 않고 AP를 바꾸지 않는다(연결은 이미 된 상태를 가정). 이동 없음.
- TXOP = 5.484 ms (11ax 최대 PPDU). 매 TXOP 반복.
- 경로손실 TGax Enterprise(벽 7 dB, 섀도잉 5 dB), Nakagami m=1.5, 잡음 −94 dBm, 최대 전력 24 dBm, 재전송 7회, 마감: 저지연 20~30 ms, 배경 512 TU.
- 그룹 간 간섭은 0이 아니다. SINR 계산에 같은 슬롯의 모든 송신 AP(다른 그룹 포함)가 간섭원으로 들어간다.

## 4. 제안 기법 동작

### 4.1 초기화: RSSI 기반 BSS 그룹화 (배치 동안 고정)
부하(자기 STA 요구량/단독 링크 속도 합)가 낮은 AP부터 center 후보. 기존 center들로부터의 RSSI가 모두 −70 dBm 미만이면 새 center.
나머지 AP는 RSSI 최대 center 그룹에 합류, STA는 자기 AP를 따름. 1대짜리 그룹 허용. 100회 평균 5.2개 그룹(3~8), 그룹당 AP 평균 3.8대,
1대 그룹 8.8%. **트래픽 특성은 그룹화에 쓰지 않는다**(부하 순서만).

### 4.2 매 TXOP: 저지연 STA 위치 관측 → 라운드 구성
"라운드" = Master AP가 트리거 한 번 보내고 AP들이 같은 길이로 전송하는 구간. TXOP = 라운드 몇 개. 라운드 길이는 Master AP가 정한다(RL).
- 저지연 STA(보낼 데이터 있는) 없음 → 라운드 1개, 전원 shared(Co-SR). TXOP의 1~35%(배치에 따라).
- **Distributed**(저지연 STA가 여러 그룹에 흩어짐, 또는 저지연 서비스 AP 1대) → priority 라운드 R개(R = 한 그룹 안 저지연 서비스 AP 최대 수),
  r번째 라운드에 각 그룹의 r번째 저지연 AP가 자기 저지연 STA에게만 전송(다른 그룹끼리 동시 = Co-SR, 같은 그룹 안은 순번 = Co-TDMA).
  그다음 shared 라운드 1개: 전원이 나머지 STA에게 동시 전송(같은 그룹 AP도 동시, 전력 조절). TXOP의 64~95%.
- **Concentrated**(저지연 서비스 AP 2대 이상이 전부 한 그룹) → 그 그룹의 AP마다 라운드 1개씩 차례로(저지연 AP 먼저, Co-TDMA),
  다른 그룹은 모든 라운드에서 shared(Co-SR). 별도 shared 라운드 없음. 저지연 AP의 나머지 STA는 이 TXOP에서 서비스되지 않음. TXOP의 1~5%.
- 그룹 안 순서: AC 우선순위 → 큐 길이 → 대기 시간. 판정 단위는 "저지연 STA를 가진 AP"(한 AP에 저지연 STA 둘이면 하나로 셈).

### 4.3 Distributed에서 "저지연 없는 그룹"의 처리 (`LL_INTRA`)
| 모드 | 저지연 없는 그룹(G1) | 저지연 전송을 마친 그룹(G2) | 비고 |
|---|---|---|---|
| `'tdma'` **wait** (v1.9, 논문) | priority 끝까지 대기 | 대기 | priority = 저지연 전용 (AP 단위) |
| `'group-wait'` (v2.0 기본, 10/2 추가) | priority 끝까지 대기 | 그 라운드부터 모든 AP가 shared처럼 전송 | **설계 의도**: priority는 "저지연이 있는 그룹"의 것 |
| `'group'` **no-wait** | 처음부터 전송 | 저지연 있는 그룹은 AP 하나씩 TDMA(저지연 AP 먼저), shared 라운드 없음 | |

8 seed 비교: group-wait ≈ wait (오차 안), 둘 다 no-wait와 구분됨. → 논문 수치(wait)는 유지해도 되고, 설계 설명·그림은 group-wait로 써도 모순 없음.
v2.0으로 100회 재실험 예정(사용자 PC, `run_parallel_v2_0.py --n 100 --ll --workers 14`).

### 4.4 슬롯·전력 결정: 계층형 MAB (UCB1)
- 결정: priority 총 비율 f_ll ∈ {0.1..0.9} → 라운드별 분배(SLOT_ARMS 1~5) → 그룹 송신 전력 {6,12,24} dBm(JOINT_MAX 3대 조합).
- 보상 = ½ 저지연 전달률 + ½ 전체 전달률(TXOP 시작 큐 대비). 온라인 학습, warm-up 60%, 그룹 구성별 에이전트. C_SLOT 0.3, C_POWER 0.1.
- 규칙 버전: 슬롯 길이 802.11e Medium Time 비례, 전력 Park 기고문 규칙.
- 공통 경계인 이유: RL이 길이를 학습하려면 Master AP가 길이를 미리 정해야 함. 표준의 "트리거 하나 = 공통 종료"와도 일치. A 데이터가 슬롯보다 짧으면 남은 시간은 빈다.

## 5. 결과 (100회 평균, v1.9)

1000 Mbps: CSMA/CA 76.2 / 15.30 ms / 72.15 % · Co-SR 656.0 / 9.88 / 41.75 · Co-TDMA 591.1 / 7.98 / 3.15 · rule 691.8 / 9.05 / 27.28 · **RL 764.1 / 6.57 / 1.10**
(처리량 Mbps / 저지연 지연 / 저지연 손실률). 재실행 시 RL 770.5 / 6.59 / 1.18 (논문 작성 뒤 코드 미세 변경 흔적).
LS 50 % (800 Mbps): Co-SR 549.5/9.67/35.68 · Co-TDMA 569.3/8.46/7.94 · rule 614.9/8.75/21.99 · RL 686.7/7.27/2.80.
Ablation(1000): 슬롯만 학습 672.0/6.52/1.34, ML k=20 689.3/7.14/5.44, 그룹 1개 435.4, rule k=20 677.3/8.87/33.0. priority 비중 rule 5% → RL ≈45%.
**저지연 처리량**(10/1 추가, 제공 143.1 Mbps): CSMA 32.8 · Co-TDMA 138.2 · Co-SR 83.3 · rule 103.8 · RL 142.2. 저지연은 고정 속도라 처리량 = 제공 × (1 − 손실률).
wait vs no-wait 100회: 1000 Mbps 770.5/808.6, 6.59/7.03, 1.18/3.01 · LS50% 687.6/765.6, 7.28/7.52, 2.85/6.34.
**저지연 처리량(wait/no-wait, 100회, 10/2)**: 부하 400→1000에서 wait 143.2→142.2, no-wait 143.5→138.6 (제공 143.1). LS 비율 10→50%에서 wait 57.7→285.9, no-wait 57.5→275.4 (제공 57→292). 전체 처리량은 no-wait가 높지만(1000 Mbps 809 vs 770) 저지연 처리량은 wait가 높고 부하·비율이 커질수록 차이가 벌어진다(50%에서 10.5 Mbps). no-wait 전체 처리량이 LS 비율과 함께 오르는 것은 배경 트래픽이 채널을 꽉 쓰기 때문이고, 망가지는 쪽은 저지연 손실(6.3%)이다. 그림 `figures/dtm_wait/cmp_wait100_throughput_ll.*`.
이유: no-wait는 저지연 없는 그룹의 유휴 시간을 써서 처리량↑, 그러나 priority 구간 동시 송신기 2~4대→10대+ 로 저지연 손실↑.

## 6. 피드백 이력

- 8/5 교수님: 그룹 수는 center 노드 기반. 8/19: 저지연 위치에 따른 두 케이스(흩어짐/몰림), "나머지는 쉰다".
- 9/3·9/4 멘토: 케이스 나눠 실험하지 말고 매 라운드 랜덤, 그룹 안 방식 고정, x축 부하, 지표 3개, RL 가능, 특허에 ML 선택.
- 9/10 교수님: "저지연 AP" 틀림(주체 STA), 그룹은 AP+STA, 첫 슬롯은 저지연 STA만, master AP가 모든 STA 인식 → 저지연 STA 묶어 AP 할당(해석 불명확), 하향링크만 언급, 표준 특허는 MAPC 프레임 형식·새 필드, ML은 어떤 정보가 어느 필드에 실리는지.
- 9/30 멘토: 내일은 특허까지만 공유(SCI 확장·그룹 정의 논의 제외). 특허 필드는 드래프트 기반이라 "검토" 어조. MAPC element가 11bn에 들어오는지 교수님께 확인, 아니면 기존 필드 reserved bit 활용. STA는 지금 트래픽 라벨 외 동작 없음 → STA 기준 그룹화는 다른 문제(소속 AP 결정). 지리적 그룹화 유지. 트래픽 변화 시나리오 불필요. 전체가 복잡하니 단순화 또는 새 주제(보안). SCI 신규성 30%.
- **10/1 교수님**: 둘 다 특허화(표준 특허 가능 영역), MobiSec 투고와 동시에 출원. wait/no-wait: "충돌 나지 않나" → 저지연 손실·지연으로 설명됨.
  **처리량도 저지연 트래픽의 처리량으로 비교하라**(전체 처리량과 저지연 지연·손실을 섞어 보여주면 비교가 안 됨). 전체는 비슷, 저지연은 wait이 훨씬 좋다는 그림. 저지연 비율↑에 따라 차이 커지는지, no-wait 처리량이 계속 오르는 게 맞는지 체크.
  특허 필드: 프레임 선택·Info Type 7 신설은 좋음. **TX Power Limit은 "너는 이 전력까지만"이라는 뜻**이라 "내가 보내는 전력"과 다름 → 의미 재검토, 송신 전력이면 TX Power로.
  **그룹화 절차**(누가 어떻게 그룹을 짓는지)를 특허에 서술할 것. 필드(Group ID, Operation Mode, Slot Index)만으로 모든 동작이 제어되는지 점검. 트리거를 받은 쪽의 **응답 프레임**까지 포함해야 완성된 발명. 표준은 BSS 2개 기준으로 쓰지만 MAPC는 확장성이 중요.
  드래프트는 AI에 넣어도 됨(문서 자체를 외부 공개만 금지).

## 7. 특허(표준) 작업 현황

- 11bn Draft 2.0 기반 분석: Management Action frame(Category 4)에 MAPC 6종(Discovery Req/Resp, Negotiation Req/Resp, Notification, TXOP return), MAPC element.
  Control Trigger frame의 User Info List에 MAPC User Info(AP ID 12 / MAPC Info Type 4 / MAPC Information 24 bit). Info Type 0~2 Co-BF, 3 Co-TDMA, 4~6 Co-SR, 7~15 reserved.
- 제안: Info Type 7 신설. MAPC Information(24 bit) = PHY Version Identifier 3 / TX Power Limit 6 / **Group ID 4 / Operation Mode 2 / Slot Index 3** / Reserved 6. 슬롯 길이는 Common Info의 Length 필드 재사용.
- 단계별 필요 정보: 그룹화(Group ID, center 여부; Master→AP; Negotiation/Notification), 관측(저지연 STA 유무·큐; AP→Master; ICR), 협력 방식(Operation Mode; Trigger), 슬롯(Slot Index; Trigger), 전력(TX Power Limit; Trigger).
- 남은 일: TX Power 의미 정리, 그룹화 절차 서술, 응답 프레임(Trigger 응답이 별도 정의인지) 조사, 필드 충분성 점검, 2-BSS 기준 서술 + 확장성.

## 8. 논문 v1.2 잔여 수정

인용을 저자-연도로, Fig. 7 캡션 "Aggregate throughput", 트래픽 모델 인용 Lee, 2장 한계 서술 "동작→성능 저하"형, 3.1 "Master AP는", 지연·손실 정의 저지연 한정,
Table 3 Background 행 확인, 6.57/7.27 vs 6.6/7.3 통일, "8080"→80 m × 80 m, STA/AC 약어 풀이, 참고문헌 `paper/References_MobiSec_format.docx`.
**Distributed 기본 그림: A·B·C priority 슬롯 폭을 같게, shared 시작선 하나로**(코드는 라운드 공통 경계). no-wait 그림에서 G3 끝 "other STAs in G3" 제거.
설계 설명을 group-wait("저지연 없는 그룹만 대기")로 바꾸려면 그림은 사용자가 그린 버전(G2는 A 다음 바로 나머지 STA) 사용 가능.

## 9. 파일 위치 (GitHub `wanniii/Multi-AP-Coordination_Grouping`, 브랜치 `claude/happy-lovelace-fm5ou6`)

- `sim/mapc_grouping_HMAB_v1_9.py` 논문 코드 · `v2_0.py` group-wait 기본 · `run_parallel_v1_9/v2_0.py` 100회 러너 · `cmp_wait*.py` wait 비교 · `plot_*.py`
- `results/` 100회 JSON(부하·비율·tp_ll 포함 버전·ablation·wait 비교), `figures/paper` 논문 그림, `figures/tp_ll` 저지연 처리량, `figures/dtm_wait` wait 비교,
  `figures/diagrams` 그룹화 그림, TXOP 설명, 라운드 타임라인(Distributed 4종, Concentrated), `paper/slides` 모델 상세 슬라이드, `paper/References_*.docx`
- `docs/RESEARCH_NOTES.md` 상세 노트. 회의록·논문 docx·선행연구 PDF는 레포에 없음(사용자 PC).

## 10. 열린 질문·다음 단계

1. v2.0(group-wait) 100회 결과 확인 → 논문 설명/그림을 어느 버전으로 할지 확정.
2. wait/no-wait 저지연 처리량 그래프(100회, `cmp_wait_sweep.py` 재실행 중)로 교수님 요청 반영.
3. 특허: 7절 남은 일. 교수님께 MAPC element 11bn 포함 여부 확인.
4. 이 주제를 특허+MobiSec으로 마무리하고 새 주제(보안)로 갈지 결정. 교수님 "저지연 STA를 묶어 AP에 할당"은 연결(association) 결정 문제라 별도 연구로 취급.
