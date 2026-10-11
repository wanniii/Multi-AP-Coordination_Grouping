# 선행기술자료 조사서 — 2. 관련 논문 (TAG-ST 특허용 초안, 2026-10-11)

> 별지 제3호 서식의 "2. 관련 논문(보고서, 인터넷자료 등 포함)" 칸에 그대로 붙여 넣을 수 있도록 서식의 예시(LTF 난독화 건)와 같은 구조로 작성함.

## 가장 유사하다고 생각하는 논문 (문헌명/저자명/페이지 등)

D. Nunez, F. Wilhelmi, S. Avallone, M. Smith, and B. Bellalta, "TXOP Sharing with Coordinated Spatial Reuse in Multi-AP Cooperative IEEE 802.11be WLANs," *Proc. IEEE 19th Annual Consumer Communications & Networking Conference (CCNC)*, pp. 864–870, 2022.

## 선행문헌의 기술 요약과 기대효과

본 선행 논문은 IEEE 802.11be 다중 AP 협력(multi-AP coordination) 환경에서, TXOP을 획득한 sharing AP가 자신의 TXOP을 복수의 coordinated slot으로 분할하여 다른 AP(shared AP)에게 나누어 주되, 각 slot 안에서 복수의 AP가 송신 전력을 조절하며 동시에 전송하도록 허용하는 coordinated TDMA with spatial reuse(c-TDMA/SR) 방식을 제안한다. 구체적으로, sharing AP는 가능한 AP–STA 전송 조합과 각 AP의 송신 전력에 따른 예상 전송 성능을 계산하여 slot별 동시 전송 구성을 결정하며, 이를 통해 시간 분할만 사용하는 c-TDMA 대비 공간 재사용 이득을 추가로 확보한다. 기대효과는 하나의 TXOP 안에서 시간 분할(TDMA)과 공간 재사용(SR)을 함께 적용함으로써 다중 AP 환경의 집계 처리량을 향상시키는 것이다.

## 본 선행기술 대비 제안하는 발명의 차별성

본 선행 논문은 하나의 TXOP을 시간 슬롯으로 나누고 각 슬롯에서 복수 AP의 동시 전송을 허용한다는 점에서 본 발명과 TXOP 구성의 뼈대를 공유한다. 그러나 선행 논문은 (i) 어떤 AP들이 하나의 슬롯을 함께 사용할지를 가능한 AP–STA 및 송신 전력 조합을 모두 평가하여 결정하므로 AP와 STA 수가 증가할수록 계산 복잡도가 급격히 증가하고, (ii) 슬롯 구성의 기준이 집계 처리량이어서 트래픽의 지연 요구사항(latency-sensitive 트래픽의 존재와 분포)은 슬롯 구성에 반영되지 않으며, (iii) 결정에 필요한 정보를 어떤 프레임의 어떤 필드로 교환하는지에 대한 시그널링 절차는 다루지 않는다.

이에 반해, 본 발명은 다음과 같은 차별점을 가진다.

첫째, 본 발명은 마스터 AP가 AP 간 수신 신호 세기(RSSI)를 기준으로 상호 간섭이 큰 BSS(AP와 그 소속 STA)들을 사전에 그룹으로 구성하고, 그룹 식별자(Group ID)를 각 AP에 통지한다. 협력 전송 시 "다른 그룹 간에는 동시 전송, 같은 그룹 안에서는 순차 전송"이라는 규칙이 그룹 구성으로부터 자동으로 정해지므로, 선행 논문과 같이 매 TXOP마다 모든 AP–STA 조합을 평가할 필요가 없다.

둘째, 본 발명은 매 TXOP마다 각 AP의 latency-sensitive 트래픽 보유 여부를 수집하고, 해당 트래픽이 어느 그룹에 분포하는지(없음 / 여러 그룹에 분산 / 하나의 그룹에 집중)에 따라 동작 모드(Operation Mode)를 선택한다. 분산된 경우에는 TXOP 앞부분에 latency-sensitive 트래픽 전용의 우선 슬롯(priority slot)을 두고 뒷부분을 공유 슬롯(shared slot)으로 구성하며, 집중된 경우에는 해당 그룹만 TXOP 전체를 순차 전송하고 나머지 그룹은 동시 전송한다. 즉, 트래픽의 지연 민감도와 공간적 분포가 슬롯 구성의 직접적인 기준이 된다는 점에서, 처리량만을 기준으로 슬롯을 구성하는 선행 논문과 구별된다.

셋째, 본 발명은 우선 슬롯과 공유 슬롯의 길이 비율, 같은 종류 슬롯 간의 상대 길이, 그리고 그룹별 송신 전력을 사전 계산이 아니라 TXOP마다의 전송 결과를 보상으로 하는 온라인 학습(계층형 multi-armed bandit)으로 결정한다. 보상은 latency-sensitive 트래픽의 전달 비율과 전체 트래픽의 전달 비율을 동일 비중으로 결합한 값으로 정의하여, 지연 보호와 처리량을 함께 고려한다. 선행 논문은 모델 기반 계산으로 구성을 고정하므로 채널·트래픽 변화에 따른 적응 과정이 없다.

넷째, 본 발명은 위 동작에 필요한 정보의 교환 절차와 프레임 필드를 정의한다. 마스터 AP는 initial control frame(ICF)으로 각 AP를 폴링하고 AP는 initial control response(ICR)로 latency-sensitive 트래픽 보유 여부와 큐 상태를 응답하며, 마스터 AP는 트리거 프레임의 MAPC User Info 필드에 그룹 식별자(Group ID), 동작 모드(Operation Mode), 슬롯 순번(Slot Index)을 실어 각 AP에 전달하고 슬롯 길이는 Common Info의 길이 필드를, 송신 전력은 기존 송신 전력 필드를 이용한다. 이를 통해 IEEE 802.11bn MAPC 프레임 구조와 호환되는 형태로 제안 동작을 구현할 수 있으며, 선행 논문에는 이러한 시그널링 정의가 없다.

---

### (참고) 다른 후보 논문과 선택 이유

| 후보 | 유사한 점 | 본 발명과 다른 점 | 비고 |
|---|---|---|---|
| **Nunez et al., CCNC 2022** (선택) | TXOP 안에서 Co-TDMA와 Co-SR을 결합 | 처리량 기준, 전수 탐색, 그룹·트래픽 인지·학습·시그널링 없음 | 구조가 가장 가까움 |
| Wojnar et al., IEEE JSAC 2025 | 계층형 MAB으로 전송 AP·STA·전력 학습 | Co-SR 전용, 보상이 처리량, 우선 슬롯·그룹 없음 | 학습 방법이 가장 가까움 |
| Lee et al., IEEE GLOBECOM 2025 | latency-sensitive 트래픽 양에 따라 shared TXOP 길이 결정 | Co-TDMA 전용, 동시 전송·그룹·학습 없음 | 문제 설정이 가장 가까움 |
| Shah, SPCOM 2026 | 큐·deadline 기반 Co-SR 전송 그룹 선택 | Co-SR 전용, 시간 분할 없음 | 목표가 가까움 |

서식에 한 편만 적는다면 Nunez et al. 2022. 심사관이 학습 방법을 문제 삼을 가능성에 대비해 Wojnar et al.을 두 번째 항목으로 추가해도 된다(서식 표를 한 줄 더 복사).
