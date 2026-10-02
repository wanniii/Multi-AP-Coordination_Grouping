import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
plt.rcParams['font.family']=['WenQuanYi Zen Hei','DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False

C={'data':'#4C72B0','ack':'#B7C9E6','ctrl':'#E8B84A','resp':'#F6E2B3','prio':'#D9534F','shared':'#BFBFBF','wait':'white','busy':'#EEEEEE','bo':'#DDD6A0'}
def box(ax,x,w,y,label='',fc='white',ls='-',h=0.7,fs=9,ec='black',tc='black',bold=False):
    ax.add_patch(Rectangle((x,y-h/2),w,h,fc=fc,ec=ec,lw=0.9,ls=ls))
    if label: ax.text(x+w/2,y,label,ha='center',va='center',fontsize=fs,color=tc,fontweight='bold' if bold else 'normal')
def rowlab(ax,y,t,c='black'): ax.text(-0.3,y,t,ha='right',va='center',fontsize=10,color=c,fontweight='bold')
def txop_bar(ax,x0,x1,y,label='TXOP'):
    ax.annotate('',xy=(x0,y),xytext=(x1,y),arrowprops=dict(arrowstyle='|-|',lw=1,shrinkA=0,shrinkB=0))
    ax.text((x0+x1)/2,y-0.35,label,ha='center',va='top',fontsize=10)
def panel(ax,title,note,ylim):
    ax.set_xlim(-2.6,15.5); ax.set_ylim(*ylim); ax.axis('off')
    ax.text(-2.6,ylim[1]-0.15,title,fontsize=12,fontweight='bold',va='top')
    ax.text(15.5,ylim[1]-0.15,note,fontsize=9.5,va='top',ha='right',color='#333333',style='italic')

fig,axs=plt.subplots(4,1,figsize=(12,12.5))

# (1) 기본 TXOP: AP 하나가 채널을 잡고 연속 전송
ax=axs[0]; panel(ax,'① 기본 Wi-Fi의 TXOP: 경쟁에서 이긴 장치가 일정 시간 동안 연속 전송',
                 '하나의 채널 = 하나의 시간축. 그 시간엔 다른 장치는 모두 대기(NAV)',(-1.6,2.2))
y1,y2,y3=1.4,0.6,-0.2
rowlab(ax,y1,'AP 1'); rowlab(ax,y2,'AP 2'); rowlab(ax,y3,'STA들')
box(ax,0,1.6,y1,'백오프\n(경쟁)',C['bo'],fs=8)
x=1.6
for k in range(3):
    box(ax,x,2.2,y1,'DATA',C['data'],tc='white'); x+=2.2
    box(ax,x,0.2,y1,'',C['busy']); x+=0.2          # SIFS
    box(ax,x,0.7,y1,'ACK',C['ack'],fs=8); x+=0.7
    box(ax,x,0.2,y1,'',C['busy']); x+=0.2
box(ax,1.6,x-1.6,y2,'대기 (채널 바쁨, NAV)',C['wait'],ls='--',fs=9)
box(ax,1.6,x-1.6,y3,'AP 1의 데이터를 받고 ACK 응답',C['wait'],ls=':',fs=9)
txop_bar(ax,1.6,x,-0.9,'TXOP (TXOP limit 안에서 프레임-ACK 반복)')

# (2) Co-TDMA: sharing AP의 TXOP를 슬롯으로 쪼개 다른 AP에 나눠줌
ax=axs[1]; panel(ax,'② 11bn Co-TDMA: TXOP를 잡은 AP(sharing AP)가 그 시간을 슬롯으로 쪼개 다른 AP에게 나눠줌',
                 '시간 분할: 한 시점에 보내는 AP는 하나',(-1.6,2.6))
ys=[1.9,1.1,0.3,-0.5]; labs=['Master AP\n(sharing)','AP 1','AP 2','AP 3']
for y,l in zip(ys,labs): rowlab(ax,y,l)
box(ax,0,0.9,ys[0],'EDCA',C['bo'],fs=8); box(ax,0.9,0.7,ys[0],'ICF',C['ctrl'],fs=8)
for y in ys[1:]: box(ax,1.6,0.7,y,'ICR',C['resp'],fs=8)
box(ax,2.3,0.5,ys[0],'TRG',C['ctrl'],fs=7)   # trigger
sl=[(ys[1],'AP 1 → 자기 STA'),(ys[2],'AP 2 → 자기 STA'),(ys[3],'AP 3 → 자기 STA')]
x=2.8
for i,(y,l) in enumerate(sl):
    w=[3.6,2.8,3.4][i]
    box(ax,x,w,y,l+'  (slot %d)'%(i+1),C['data'],tc='white',fs=9)
    for yy,_ in sl:
        if yy!=y: box(ax,x,w,yy,'',C['wait'],ls='--')
    x+=w
txop_bar(ax,0.9,x,-1.15,'Master AP가 잡은 TXOP 하나를 세 슬롯으로 분할')

# (3) Co-SR: 같은 시간에 여러 AP 동시 전송
ax=axs[2]; panel(ax,'③ 11bn Co-SR: 같은 TXOP 안에서 여러 AP가 동시에 전송 (전력 조절)',
                 '공간 재사용: 한 시점에 여러 AP가 보냄 → 서로 간섭',(-1.6,2.6))
for y,l in zip(ys,labs): rowlab(ax,y,l)
box(ax,0,0.9,ys[0],'EDCA',C['bo'],fs=8); box(ax,0.9,0.7,ys[0],'ICF',C['ctrl'],fs=8)
for y in ys[1:]: box(ax,1.6,0.7,y,'ICR',C['resp'],fs=8)
box(ax,2.3,0.5,ys[0],'TRG',C['ctrl'],fs=7)
for y,l in zip(ys[1:],['AP 1 → 자기 STA','AP 2 → 자기 STA','AP 3 → 자기 STA']):
    box(ax,2.8,9.8,y,l+'   (모두 동시에)',C['data'],tc='white',fs=9)
txop_bar(ax,0.9,12.6,-1.15,'같은 TXOP, 같은 시간을 세 AP가 함께 사용')

# (4) TAG-ST Distributed: 그룹 간은 동시(Co-SR), 그룹 안은 시간 분할(Co-TDMA)
ax=axs[3]; panel(ax,'④ TAG-ST (Distributed, wait): 그룹 사이는 동시 전송, 저지연 데이터는 시간 분할로 먼저',
                 '',(-2.8,2.6))
ys=[1.9,1.1,0.3,-0.5]; labs=['Master AP','G1','G2','G3']; cols=['black','#C0392B','#1F4FD8','#2E8B2E']
for y,l,c in zip(ys,labs,cols): rowlab(ax,y,l,c)
box(ax,0,0.9,ys[0],'EDCA',C['bo'],fs=8); box(ax,0.9,0.7,ys[0],'ICF',C['ctrl'],fs=8)
for y in ys[1:]: box(ax,1.6,0.7,y,'ICR',C['resp'],fs=8)
box(ax,2.3,0.5,ys[0],'TRG',C['ctrl'],fs=7)
p1,p2,sh=3.0,3.6,3.2; x0=2.8
box(ax,x0,p1+p2,ys[1],'대기',C['wait'],ls='--'); box(ax,x0+p1+p2,sh,ys[1],'G1의 모든 STA',C['shared'])
box(ax,x0,p1,ys[2],'→ A',C['prio'],tc='white',bold=True); box(ax,x0+p1,p2,ys[2],'대기',C['wait'],ls='--'); box(ax,x0+p1+p2,sh,ys[2],'G2의 나머지 STA',C['shared'])
box(ax,x0,p1,ys[3],'→ B',C['prio'],tc='white',bold=True); box(ax,x0+p1,p2,ys[3],'→ C',C['prio'],tc='white',bold=True); box(ax,x0+p1+p2,sh,ys[3],'G3의 나머지 STA',C['shared'])
box(ax,x0+p1,0.3,ys[0],'',C['ctrl']); box(ax,x0+p1+p2,0.3,ys[0],'',C['ctrl'])
ax.text(x0+p1+p2+sh,ys[0],'← 라운드마다 트리거\n   (슬롯 경계가 모든 그룹에서 같아짐)',fontsize=8.5,ha='left',va='center',color='#555555')
txop_bar(ax,0.9,x0+p1+p2+sh,-1.6,'TXOP 하나')
ax.text(x0+(p1+p2)/2,-1.05,'Priority slot (저지연 전용)',fontsize=9,ha='center',va='top',color='#8B1A1A')
ax.text(x0+p1+p2+sh/2,-1.05,'Shared slot (전원 동시)',fontsize=9,ha='center',va='top',color='#555555')
ax.text(x0+(p1+p2)/2+1.5,-2.4,'↑ A와 B가 같은 시각 = 다른 그룹끼리 동시 전송(Co-SR).  B 다음 C = 같은 그룹 안 순차(Co-TDMA)',fontsize=9,ha='center',color='#333333')

plt.tight_layout(h_pad=1.2)
fig.savefig('txop_explained.png',dpi=170,bbox_inches='tight'); print('ok')
