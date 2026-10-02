import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
plt.rcParams['font.family']='serif'; plt.rcParams['font.serif']=['Liberation Serif','WenQuanYi Zen Hei','DejaVu Serif']; plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei']
C=dict(icf='#E8B84A',icr='#F6E2B3',prio='#D9534F',shared='#C8C8C8',wait='white')
GC={'G1':'#C0392B','G2':'#1F4FD8','G3':'#2E8B2E'}
H=0.62
def box(ax,x,w,y,label='',fc='white',ls='-',fs=11,tc='black',bold=False,lw=1.0):
    ax.add_patch(Rectangle((x,y-H/2),w,H,fc=fc,ec='black',lw=lw,ls=ls))
    if label: ax.text(x+w/2,y,label,ha='center',va='center',fontsize=fs,color=tc,fontweight='bold' if bold else 'normal')
def timeline(ax,title,rows,bounds,round_names,note):
    """rows: list of (group, [(x0,x1,label,kind),...]); bounds: x of round boundaries; round_names: labels per round segment"""
    ax.set_xlim(-1.6,13.6); ax.set_ylim(-1.9,3.4); ax.axis('off')
    ax.text(-1.6,3.25,title,fontsize=12.5,fontweight='bold',va='top',fontfamily='sans-serif')
    ax.text(13.6,3.25,note,fontsize=9.5,va='top',ha='right',color='#444444',fontfamily='sans-serif')
    ym=1.95; ys={'G1':1.1,'G2':0.3,'G3':-0.5}
    ax.text(-0.15,ym,'master AP',ha='right',va='center',fontsize=11)
    box(ax,0,0.55,ym,'ICF',C['icf'],fs=9); box(ax,0.6,0.5,ym,'',C['wait'],ls='--')
    for g,y in ys.items():
        ax.text(-0.15,y,g,ha='right',va='center',fontsize=11,color=GC[g])
        box(ax,0,0.55,y,'',C['wait'],ls='--'); box(ax,0.6,0.5,y,'ICR',C['icr'],fs=9)
    for g,segs in rows:
        y=ys[g]
        for x0,x1,label,kind in segs:
            if kind=='prio': box(ax,x0,x1-x0,y,label,C['prio'],tc='white',bold=True)
            elif kind=='shared': box(ax,x0,x1-x0,y,label,C['shared'],fs=10)
            else: box(ax,x0,x1-x0,y,label,C['wait'],ls='--',fs=10)
    # trigger marks + round labels
    for i,b in enumerate(bounds[:-1]):
        box(ax,b-0.12,0.24,ym,'',C['icf'],lw=0.8)
        nb=bounds[i+1]
        ax.text((b+nb)/2,ym+0.55,round_names[i],ha='center',va='bottom',fontsize=9.5,color='#333333',fontfamily='sans-serif')
        ax.plot([b,b],[ys['G3']-H/2-0.08,ym+H/2],color='#888888',lw=0.7,ls=':')
    ax.plot([bounds[-1],bounds[-1]],[ys['G3']-H/2-0.08,ym+H/2],color='#888888',lw=0.7,ls=':')
    ax.annotate('',xy=(0,-1.05),xytext=(bounds[-1],-1.05),arrowprops=dict(arrowstyle='|-|',lw=1,shrinkA=0,shrinkB=0))
    ax.text(bounds[-1]/2,-1.15,'TXOP',ha='center',va='top',fontsize=11)
    ax.text(0.6+0.25,ym+0.55,'trigger',ha='center',va='bottom',fontsize=8.5,color='#333333')

fig,axs=plt.subplots(3,1,figsize=(12,10.5))
S=1.2   # data start

# (1) Distributed, one LS STA per group: A(G1) B(G2) C(G3)  → round 1 (priority) + round 2 (shared)
b1=[S,7.4,13.0]
timeline(axs[0],'(1) Distributed mode — A in G1, B in G2, C in G3   [코드: priority 라운드 1개 + shared 라운드 1개]',
  [('G1',[(S,7.4,'→ A','prio'),(7.4,13.0,'other STAs in G1','shared')]),
   ('G2',[(S,7.4,'→ B','prio'),(7.4,13.0,'other STAs in G2','shared')]),
   ('G3',[(S,7.4,'→ C','prio'),(7.4,13.0,'other STAs in G3','shared')])],
  b1,['round 1: priority (저지연 STA에게만, 그룹 간 동시)','round 2: shared (전원 동시)'],
  'A·B·C 슬롯 폭 동일, shared 시작선 하나')

# (2) Extended, wait: G1 none, G2 A, G3 B & C → round1 {A,B}, round2 {C}, round3 shared
b2=[S,4.6,8.0,13.0]
timeline(axs[1],'(2) Distributed mode (wait) — G1 none, A in G2, B·C in G3   [코드 LL_INTRA=\'tdma\']',
  [('G1',[(S,8.0,'wait','wait'),(8.0,13.0,'all STAs in G1','shared')]),
   ('G2',[(S,4.6,'→ A','prio'),(4.6,8.0,'wait','wait'),(8.0,13.0,'other STAs in G2','shared')]),
   ('G3',[(S,4.6,'→ B','prio'),(4.6,8.0,'→ C','prio'),(8.0,13.0,'other STAs in G3','shared')])],
  b2,['round 1: priority','round 2: priority','round 3: shared'],
  '저지연 전송이 없는 AP는 priority 라운드 동안 대기')

# (3) Extended, no-wait: G3 = TDMA group (B round, C round); G1, G2 shared in every round; no separate shared round
b3=[S,7.0,13.0]
timeline(axs[2],'(3) Distributed mode (no-wait) — 같은 상황   [코드 LL_INTRA=\'group\']',
  [('G1',[(S,13.0,'all STAs in G1','shared')]),
   ('G2',[(S,3.6,'→ A','prio'),(3.6,13.0,'other STAs in G2','shared')]),
   ('G3',[(S,7.0,'→ B','prio'),(7.0,13.0,'→ C','prio')])],
  b3,['round 1: B (G3) ‖ G1·G2 shared','round 2: C (G3) ‖ G1·G2 shared'],
  'G3만 순차(Co-TDMA), G1·G2는 처음부터 전송. G2의 A는 shared 안에서 먼저 나감')
# legend
h=[Rectangle((0,0),1,1,fc=C['icf'],ec='black'),Rectangle((0,0),1,1,fc=C['icr'],ec='black'),
   Rectangle((0,0),1,1,fc=C['prio'],ec='black'),Rectangle((0,0),1,1,fc=C['shared'],ec='black'),
   Rectangle((0,0),1,1,fc='white',ec='black',ls='--')]
fig.legend(h,['Control frame (ICF / trigger)','Response frame (ICR)','Priority slot (→ latency-sensitive STA)','Shared slot','Wait'],
           loc='lower center',ncol=5,frameon=False,fontsize=10,bbox_to_anchor=(0.5,0.0))
plt.tight_layout(rect=(0,0.04,1,1),h_pad=1.0)
fig.savefig('rounds_explained.png',dpi=170,bbox_inches='tight'); print('ok')
