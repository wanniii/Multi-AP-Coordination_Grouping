import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
exec(open('rounds.py').read().split("fig,axs=plt.subplots")[0])   # reuse box/timeline helpers & style
fig,axs=plt.subplots(2,1,figsize=(12,7.8))
S=1.2
# (4) Concentrated: A,B,C all in G3 (3 APs), G3 also has one AP without LS STA → 4 rounds
b=[S,4.0,6.8,9.6,13.0]
timeline(axs[0],'(4) Concentrated mode — A·B·C 모두 G3 (저지연 AP 3대 + 일반 AP 1대)',
  [('G1',[(S,13.0,'all STAs in G1','shared')]),
   ('G2',[(S,13.0,'all STAs in G2','shared')]),
   ('G3',[(S,4.0,'→ A','prio'),(4.0,6.8,'→ B','prio'),(6.8,9.6,'→ C','prio'),(9.6,13.0,'STAs of the 4th AP in G3','shared')])],
  b,['round 1: AP(A)','round 2: AP(B)','round 3: AP(C)','round 4: 4th AP'],
  '')
axs[0].text(S,-1.55,'G3 안은 AP 하나씩 차례로(Co-TDMA, 저지연 AP 먼저), G1·G2는 전 구간 동시(Co-SR). 별도 shared 라운드 없음.\n※ A·B·C를 서비스하는 AP의 "나머지 STA"는 이 TXOP에서 서비스되지 않음 (priority 라운드는 저지연 STA 전용)',
            fontsize=9.5,color='#333333',fontfamily='sans-serif',va='top',linespacing=1.5)
# (0) No LS traffic: single shared round
b0=[S,13.0]
timeline(axs[1],'(0) 저지연 트래픽 없음 — 모든 그룹 Co-SR   [코드: shared 라운드 1개]',
  [('G1',[(S,13.0,'all STAs in G1','shared')]),('G2',[(S,13.0,'all STAs in G2','shared')]),('G3',[(S,13.0,'all STAs in G3','shared')])],
  b0,['round 1: shared (전원 동시)'],'')
h=[Rectangle((0,0),1,1,fc=C['icf'],ec='black'),Rectangle((0,0),1,1,fc=C['icr'],ec='black'),
   Rectangle((0,0),1,1,fc=C['prio'],ec='black'),Rectangle((0,0),1,1,fc=C['shared'],ec='black'),
   Rectangle((0,0),1,1,fc='white',ec='black',ls='--')]
fig.legend(h,['Control frame (ICF / trigger)','Response frame (ICR)','Priority slot (→ latency-sensitive STA)','Shared slot','Wait'],
           loc='lower center',ncol=5,frameon=False,fontsize=10,bbox_to_anchor=(0.5,0.0))
plt.tight_layout(rect=(0,0.05,1,1),h_pad=1.0)
fig.savefig('conc_explained.png',dpi=170,bbox_inches='tight'); print('ok')
