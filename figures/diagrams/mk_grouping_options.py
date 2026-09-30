import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Arc, FancyArrowPatch, Ellipse
from matplotlib.lines import Line2D
plt.rcParams['font.family']='serif'; plt.rcParams['font.serif']=['Times New Roman','Liberation Serif','DejaVu Serif']

def ap(ax,x,y,color='black',scale=1.0):
    w,h=0.72*scale,0.22*scale
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.02,rounding_size=0.06',fc=color,ec=color,zorder=5))
    for i in range(3): ax.plot([x-w/2+0.12+i*0.1],[y],'o',color='white',ms=2.2,zorder=6)
    for r in (0.13,0.24): ax.add_patch(Arc((x+0.1*scale,y+h/2),r*2,r*2,theta1=30,theta2=150,color=color,lw=1.4,zorder=6))
    ax.plot([x+0.1*scale],[y+h/2+0.02],'o',color=color,ms=2.5,zorder=6)
def sta(ax,x,y): ax.add_patch(Circle((x,y),0.13,fc='#B0B0B0',ec='#666666',lw=1,zorder=5))
def ls(ax,x,y,label): ax.plot(x,y,marker='*',ms=17,color='#E0202A',mec='#7A0000',mew=0.6,zorder=6); ax.text(x,y-0.36,label,ha='center',va='top',fontsize=11,fontweight='bold')
def group(ax,cx,cy,r,color,label,dx=-0.1):
    ax.add_patch(Circle((cx,cy),r,fill=False,ec=color,lw=1.6,ls=(0,(2,3)),zorder=2))
    ax.text(cx-r+dx,cy+r-0.05,label,color=color,fontsize=12,fontweight='bold',ha='left',va='bottom')
def assoc(ax,p,q,style='-',color='#8A8A8A',lw=0.9,z=3): ax.plot([p[0],q[0]],[p[1],q[1]],ls=style,color=color,lw=lw,zorder=z)
def arrow(ax,p,q,color,lw=1.6,style='->',ls='-',z=7,shrink=8):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle=style,color=color,lw=lw,linestyle=ls,mutation_scale=13,shrinkA=shrink,shrinkB=shrink,zorder=z))
def master(ax,x,y):
    ax.add_patch(FancyBboxPatch((x-0.42,y-0.12),0.84,0.24,boxstyle='round,pad=0.02',fc='#2F4FBF',ec='#2F4FBF',zorder=5))
    for i in range(4): ax.plot([x-0.28+i*0.18],[y],'o',color='white',ms=2.2,zorder=6)
    for r in (0.16,0.3,0.44): ax.add_patch(Arc((x,y+0.12),r*2,r*2,theta1=35,theta2=145,color='#2F4FBF',lw=1.6,zorder=6))
    ax.text(x,y-0.3,'master AP',ha='center',va='top',fontsize=11,fontweight='bold',color='#2F4FBF')

# layout (same for both panels)
G={'G1':((1.9,6.4),1.55,'#D62728'),'G2':((7.1,6.4),1.55,'#1F4FD8'),'G3':((4.5,2.6),1.55,'#2E8B2E')}
AP={'ap1a':(2.2,7.0),'ap1b':(1.5,6.0),'ap2a':(7.4,7.0),'ap2b':(7.3,5.8),'ap3a':(3.9,3.1),'ap3b':(4.7,1.9)}
STA={'s1':(1.4,7.2,'ap1a'),'s2':(2.75,6.8,'ap1a'),'s3':(0.9,5.9,'ap1b'),'s4':(2.05,5.5,'ap1b'),'s5':(6.6,7.15,'ap2a'),'s6':(7.85,6.6,'ap2a'),'s7':(8.0,5.35,'ap2b'),'s8':(3.5,2.2,'ap3a')}
LS={'A':(6.6,5.75,'ap2b'),'B':(4.55,3.35,'ap3a'),'C':(5.35,1.85,'ap3b')}

def base(ax,title):
    ax.set_xlim(-0.2,9.3); ax.set_ylim(0.2,9.1); ax.set_aspect('equal'); ax.axis('off')
    for k,(c,r,col) in G.items(): group(ax,c[0],c[1],r,col,k)
    for k,p in AP.items(): ap(ax,*p)
    for k,(x,y,a) in STA.items(): sta(ax,x,y); assoc(ax,(x,y),AP[a])
    master(ax,4.5,6.35)
    ax.text(4.55,8.75,title,ha='center',va='center',fontsize=13,fontweight='bold')

fig,(a1,a2)=plt.subplots(1,2,figsize=(13.2,6.2))
# (a) 논리 그룹
base(a1,'(a) Logical grouping: association unchanged')
for k,(x,y,a) in LS.items(): assoc(a1,(x,y),AP[a]); ls(a1,x,y,k)
a1.add_patch(Ellipse((5.5,3.65),2.4,5.4,angle=-30,fill=False,ec='#7B2CBF',lw=2.0,ls=(0,(5,3)),zorder=4))
a1.text(6.55,2.0,'LS group\n(logical)',color='#7B2CBF',fontsize=11,fontweight='bold',ha='left',va='top')
for a in ('ap2b','ap3a','ap3b'): arrow(a1,(4.5,6.35),AP[a],'#2F4FBF',lw=1.5,ls='-')
a1.text(5.35,6.25,'slot / power',color='#2F4FBF',fontsize=10,ha='left',va='bottom',rotation=-11)
# (b) 재연결
base(a2,'(b) Re-association: LS STAs moved to one AP')
tgt=AP['ap3a']
NEW={'A':(3.3,3.6),'C':(4.4,2.6)}
for k,(x,y,a) in LS.items():
    if k=='B': assoc(a2,(x,y),tgt); ls(a2,x,y,k)
    else:
        assoc(a2,(x,y),AP[a],style=(0,(2,2)),color='#C8C8C8')          # dropped association
        a2.plot(x,y,marker='*',ms=17,mfc='white',mec='#E0202A',mew=1.0,alpha=0.7,zorder=6)  # old position
        a2.text(x,y-0.36,k,ha='center',va='top',fontsize=11,color='#999999')
        nx,ny=NEW[k]; assoc(a2,(nx,ny),tgt); ls(a2,nx,ny,k)
        arrow(a2,(x,y),(nx,ny),'#E0202A',lw=1.8,ls=(0,(6,3)),shrink=11)  # re-association
a2.add_patch(Circle(tgt,0.9,fill=False,ec='#7B2CBF',lw=2.0,ls=(0,(5,3)),zorder=4))
a2.text(2.55,3.05,'LS-serving AP\n(Co-TDMA inside)',color='#7B2CBF',fontsize=10.5,fontweight='bold',ha='right',va='center')
arrow(a2,(4.5,6.35),tgt,'#2F4FBF',lw=1.5)
a2.text(4.1,5.1,'assign',color='#2F4FBF',fontsize=10,ha='right',va='center')
# legend
h=[Line2D([],[],marker='s',color='black',ls='',ms=9,label='AP'),
   Line2D([],[],marker='o',color='#B0B0B0',mec='#666',ls='',ms=9,label='STA'),
   Line2D([],[],marker='*',color='#E0202A',ls='',ms=14,label='latency-sensitive STA'),
   Line2D([],[],color='#8A8A8A',lw=1,label='association'),
   Line2D([],[],color='#E0202A',lw=1.8,ls=(0,(6,3)),label='re-association'),
   Line2D([],[],color='#7B2CBF',lw=2,ls=(0,(5,3)),label='LS group'),
   Line2D([],[],color='#2F4FBF',lw=1.5,label='master AP control')]
fig.legend(handles=h,loc='lower center',ncol=7,frameon=False,fontsize=11,bbox_to_anchor=(0.5,-0.01))
fig.tight_layout(rect=(0,0.06,1,1))
fig.savefig('grouping_options.png',dpi=200); fig.savefig('grouping_options.pdf'); print('ok')
