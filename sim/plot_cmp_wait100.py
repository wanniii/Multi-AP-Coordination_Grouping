import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
for f in ['/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf','/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf']:
    try: font_manager.fontManager.addfont(f)
    except Exception: pass
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman','Liberation Serif','DejaVu Serif'],'font.size':11,
                     'axes.labelsize':12,'legend.fontsize':10,'axes.grid':True,'grid.alpha':0.3})
import sys
D=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'cmp_wait_sweep_n100.json'))
STY={'tdma':('TAG-ST (DTM-wait)','#1D9E75','D','-'),'group':('TAG-ST (DTM-no wait)','#D85A30','s','--')}
METRICS=[('tp','Aggregate throughput (Mbps)','throughput'),('tp_ll','Throughput of latency-sensitive traffic (Mbps)','throughput_ll'),('tp_be','Throughput of background traffic (Mbps)','throughput_be'),('lat_ll','Latency of latency-sensitive traffic (ms)','latency_ll'),('loss_ll','Packet loss ratio of latency-sensitive traffic (%)','loss_ll')]
xs_load=D['loads']; xs_ll=[int(r*100) for r in D['ratios']]
for key,ylab,fname in METRICS:
    fig,(a,b)=plt.subplots(1,2,figsize=(11.0,4.2))
    for ax,exp,xs,xl,tag in ((a,'load',xs_load,'Traffic load (Mbps)','(a)'),(b,'ll',xs_ll,'Latency-sensitive STA ratio (%)','(b)')):
        for intra,(lab,col,mk,ls) in STY.items():
            if key not in D['results'][intra][exp]: continue
            y=D['results'][intra][exp][key]
            ax.plot(xs,y,label=lab,color=col,marker=mk,ls=ls,lw=1.6,ms=6)
        ax.set_xlabel(xl); ax.set_ylabel(ylab); ax.set_xticks(xs)
        ax.text(0.5,-0.24,tag,transform=ax.transAxes,ha='center',fontsize=12)
        if key=='loss_ll': ax.set_ylim(bottom=0)
    a.legend(loc='best')
    fig.tight_layout()
    fig.savefig(f'cmp_wait100_{fname}.png',dpi=200); fig.savefig(f'cmp_wait100_{fname}.pdf')
print('ok')
