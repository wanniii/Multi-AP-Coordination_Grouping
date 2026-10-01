"""
plot_tp_ll.py — 저지연 트래픽 처리량(tp_ll) 그림. plot_paper_figs.py 와 같은 형식
  (한 장 = (a) 부하 실험, (b) 저지연 STA 비율 실험; 모델 스타일·글꼴·범례 동일).

사용법:  python plot_tp_ll.py <results.json> <results_ll.json> [out_dir]
  results.json / results_ll.json 은 run_parallel_v1_9.py (10/1 이후, tp_ll 포함) 출력.
"""
import os, sys, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import MultipleLocator

STYLE = {
    'CSMA/CA':               dict(label='CSMA/CA',             color='#9a9a9a', marker='x', ls=':',  mfc='#9a9a9a'),
    'only c-TDMA':           dict(label='Co-TDMA',             color='#7f7f7f', marker='^', ls='-.', mfc='#7f7f7f'),
    'only c-SR':             dict(label='Co-SR',               color='#545454', marker='D', ls='--', mfc='#545454'),
    'Proposed (Rule-based)': dict(label='TAG-ST (Rule-based)', color='#000000', marker='o', ls='-',  mfc='#ffffff'),
    'Proposed (ML-based)':   dict(label='TAG-ST (ML-based)',   color='#000000', marker='o', ls='-',  mfc='#000000'),
}
ORDER = ['CSMA/CA', 'only c-TDMA', 'only c-SR', 'Proposed (Rule-based)', 'Proposed (ML-based)']
FIG = dict(formats=('pdf', 'png'), dpi=600, font_axis=14, font_tick=12, font_legend=12,
           lw=1.2, ms=4.5, mew=1.0, grid_style=':', grid_alpha=0.6, grid_lw=0.8,
           xlabel_load='Traffic load (Mbps)', xlabel_ll='Ratio of latency-sensitive STAs (%)')
FIG2 = dict(size=(11.0, 4.2), wspace=0.28)
PANEL_TAG = ['(a)', '(b)']

# 그릴 지표: (키, y축 제목, 파일 이름, (a) y범위/눈금, (b) y범위/눈금)
FIGS = [
    ('tp_ll', 'Throughput of latency-sensitive traffic (Mbps)', 'fig_tp_ll',
     dict(lim=(0, 160), step=20), dict(lim=(0, 350), step=50)),
    ('tp_be', 'Throughput of background traffic (Mbps)', 'fig_tp_be',
     dict(lim=None, step=None), dict(lim=None, step=None)),
]

_names = {f.name for f in fm.fontManager.ttflist}
_serif = ['Times New Roman'] if 'Times New Roman' in _names else ['Liberation Serif', 'Nimbus Roman', 'DejaVu Serif']
plt.rcParams.update({'font.family': 'serif', 'font.serif': _serif, 'mathtext.fontset': 'stix', 'pdf.fonttype': 42})


def _panel(ax, R, xs, key, xlabel, ylab, ya):
    for m in ORDER:
        if m not in R or key not in R[m]:
            continue
        st = STYLE[m]
        ax.plot(xs, R[m][key], label=st['label'], color=st['color'], marker=st['marker'], linestyle=st['ls'],
                linewidth=FIG['lw'], markersize=FIG['ms'], markerfacecolor=st['mfc'],
                markeredgecolor=st['color'], markeredgewidth=FIG['mew'])
    ax.set_xlabel(xlabel, fontsize=FIG['font_axis'])
    ax.set_ylabel(ylab, fontsize=FIG['font_axis'])
    ax.set_xticks(xs)
    ax.tick_params(axis='both', labelsize=FIG['font_tick'])
    if ya.get('lim') is not None:
        ax.set_ylim(*ya['lim'])
    if ya.get('step') is not None:
        ax.yaxis.set_major_locator(MultipleLocator(ya['step']))
    ax.grid(True, linestyle=FIG['grid_style'], alpha=FIG['grid_alpha'], linewidth=FIG['grid_lw'])


def draw(D1, D2, out_dir):
    xs1 = D1['loads']
    xs2 = [round(r * 100) for r in D2['ratios']]
    saved = []
    for key, ylab, name, ya1, ya2 in FIGS:
        fig, (a, b) = plt.subplots(1, 2, figsize=FIG2['size'])
        _panel(a, D1['results'], xs1, key, FIG['xlabel_load'], ylab, ya1)
        _panel(b, D2['results'], xs2, key, FIG['xlabel_ll'], ylab, ya2)
        for ax, tag in zip((a, b), PANEL_TAG):
            ax.text(0.5, -0.30, tag, transform=ax.transAxes, ha='center', va='top', fontsize=FIG['font_axis'])
        h, l = a.get_legend_handles_labels()
        fig.legend(h, l, loc='lower center', bbox_to_anchor=(0.5, 0.97), ncol=len(l),
                   fontsize=FIG['font_legend'], frameon=False, handlelength=2.2, columnspacing=1.6)
        fig.subplots_adjust(wspace=FIG2['wspace'])
        os.makedirs(out_dir, exist_ok=True)
        for ext in FIG['formats']:
            p = os.path.join(out_dir, f'{name}.{ext}')
            fig.savefig(p, dpi=FIG['dpi'], bbox_inches='tight'); saved.append(p)
        plt.close(fig)
    return saved


if __name__ == '__main__':
    f1, f2 = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else 'figs'
    D1 = json.load(open(f1, encoding='utf-8')); D2 = json.load(open(f2, encoding='utf-8'))
    for p in draw(D1, D2, out):
        print('saved', p)
    # 1000 Mbps 표
    i = D1['loads'].index(1000)
    print('\n1000 Mbps:  model | tp | tp_ll | tp_be | offered_ll | loss_ll')
    for m in ORDER:
        r = D1['results'][m]
        print(f"  {STYLE[m]['label']:20s} {r['tp'][i]:7.1f} {r['tp_ll'][i]:7.1f} {r['tp_be'][i]:7.1f} "
              f"{r['offered_ll'][i]:7.1f} {r['loss_ll'][i]:6.2f}")
