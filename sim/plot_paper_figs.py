"""
plot_paper_figs.py (Colab 버전) — 논문에 넣을 그림 3장(지표별, 각 (a) 부하 / (b) 저지연 비율 2패널)만 그린다.

원본 plot_results.py (Colab 버전) — 실험 결과가 코드 안에 들어 있어 파일 업로드 없이 바로 그린다.

사용법
  1) 이 셀을 실행하면 그래프 10 장이 셀 아래에 표시되고, FIG['formats'] 에 적은 형식(pdf, png)으로 저장된다.
  2) FIG['download'] = True 면 저장한 파일을 zip 으로 묶어 내려받는다.

수정하고 싶은 것은 전부 아래 [설정] 블록에 모아 두었다.
    STYLE   : 모델별 색 · 마커 · 선 · 레전드 이름
    PANELS  : 어떤 지표를 그릴지, y축 라벨, 파일 이름
    YAXIS   : 지표별 y축 범위와 눈금 간격
    FIG     : 글자 크기(축 제목 · 눈금 · 레전드) · 선 굵기 · 마커 크기 · 그리드 · 저장 형식
    DATA_LOAD / DATA_LL : 실험 1 · 실험 2 결과 (results.json / results_ll.json 의 값, 100회 평균)
"""
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# ══════════════════════════════ [설정] ══════════════════════════════
OUT_DIR = 'figs'                # 저장 폴더

# 모델별 스타일. key 는 결과의 키와 같아야 한다. label 은 레전드에 표시될 이름.
STYLE = {
    # 회색 단계: CSMA/CA 가장 연함 → Co-TDMA → Co-SR → 제안 2 종은 검정.
    # 제안 규칙 버전은 검정 실선 + 속 빈 동그라미, 제안 ML 버전은 검정 실선 + 채운 동그라미.
    'CSMA/CA':               dict(label='CSMA/CA',               color='#9a9a9a', marker='x', ls=':',  mfc='#9a9a9a'),
    'only c-TDMA':           dict(label='Co-TDMA',               color='#7f7f7f', marker='^', ls='-.', mfc='#7f7f7f'),
    'only c-SR':             dict(label='Co-SR',                 color='#545454', marker='D', ls='--', mfc='#545454'),
    'Proposed (Rule-based)': dict(label='TAG-ST (Rule-based)', color='#000000', marker='o', ls='-',  mfc='#ffffff'),
    'Proposed (ML-based)':   dict(label='TAG-ST (ML-based)',   color='#000000', marker='o', ls='-',  mfc='#000000'),
}
ORDER = ['CSMA/CA', 'only c-TDMA', 'only c-SR', 'Proposed (Rule-based)', 'Proposed (ML-based)']   # 레전드 순서
#   ※ DATA 에 없는 키는 그리지 않고 건너뛴다. 새 100회 결과(results.json)의 키 이름이 위와 같아야 한다.

# 결과 파일이 같은 폴더에 있으면 그것을 우선 사용하고, 없으면 아래 DATA_LOAD / DATA_LL (코드 안 값) 을 쓴다.
RESULT_FILES = dict(load='results.json', ll='results_ll.json')

# 그릴 지표: (결과 키, y축 제목, 파일 접미사)
PANELS = [
    ('tp',      'Throughput (Mbps)',      'throughput'),
    ('loss_ll', 'Packet loss ratio (%)',  'loss_ll'),
    ('lat_ll',  'Latency (ms)',           'latency_ll'),
    ('loss',    'Packet loss ratio (%)',  'loss'),
    ('lat',     'Latency (ms)',           'latency'),
]

# y축 범위와 눈금 간격. 키 = (실험, 지표). 실험은 'load'(실험 1) 또는 'll'(실험 2).
#   lim  = (아래, 위)   None 이면 자동
#   step = 눈금 간격    None 이면 자동
# 예) ('load', 'tp'): dict(lim=(0, 1200), step=200)  → 실험 1 처리량 그래프를 0~1200, 200 간격으로
YAXIS = {
    #   log=True 를 넣으면 그 그래프만 로그 눈금 (기본은 모두 선형)
    ('load', 'tp'):      dict(lim=(0, 800),  step=None),
    ('load', 'loss_ll'): dict(lim=(0, 80),   step=10),
    ('load', 'lat_ll'):  dict(lim=(4, 16),   step=2),
    ('load', 'loss'):    dict(lim=(0, 100),  step=10),
    ('load', 'lat'):     dict(lim=None,      step=25),
    ('ll',   'tp'):      dict(lim=(0, 750),  step=None),
    ('ll',   'loss_ll'): dict(lim=(0, 100),  step=10),
    ('ll',   'lat_ll'):  dict(lim=(4, 20),   step=2),
    ('ll',   'loss'):    dict(lim=(0, 100),  step=10),
    ('ll',   'lat'):     dict(lim=None,      step=None),
}

FIG = dict(
    size=(6.4, 4.6),        # inch
    formats=('pdf', 'png'), # 저장 형식. pdf 는 벡터라 확대해도 깨지지 않음. 논문에는 pdf 권장
    dpi=600,                # png 해상도
    font_axis=14,           # 축 제목 글자 크기
    font_tick=12,           # 눈금 숫자 글자 크기
    font_legend=12,         # 레전드 글자 크기
    lw=1.2,                 # 선 굵기
    ms=4.5,                 # 마커(점 표식) 크기
    mew=1.0,                # 마커 테두리 굵기
    grid=True,
    grid_style=':',         # 그리드 선 모양: ':' 점선, '--' 파선, '-' 실선
    grid_alpha=0.6,
    grid_lw=0.8,
    legend_above=True,      # True 면 레전드를 그래프 위쪽 바깥에 한 줄로 배치 (테두리 없음). False 면 legend_loc 사용
    legend_loc='best',      # legend_above=False 일 때 위치: 'best', 'upper left', 'lower right' ...
    legend_ncol=3,          # 레전드 열 수 (모델 5개는 3 → 두 줄로 배치)
    xlabel_load='Traffic load (Mbps)',
    xlabel_ll='Ratio of latency-sensitive STAs (%)',
    download=False,         # True 면 저장한 파일을 zip 으로 내려받기 (Colab)
)

# ── 실험 1: 부하 400~1000 Mbps (results.json, 100회 평균, 9/14 Rule 포함) ──
DATA_LOAD = {
    'loads': [400, 500, 600, 700, 800, 900, 1000],
    'results': {
        'CSMA/CA': {
            'tp': [122.2081, 81.3355, 80.3584, 79.1351, 79.1253, 76.4283, 76.2384],
            'lat': [113.2911, 170.7910, 182.3657, 191.7153, 191.1812, 208.3845, 203.9075],
            'loss': [69.4262, 83.9385, 86.7081, 88.7533, 90.1152, 91.4803, 92.3483],
            'lat_ll': [13.7682, 15.3545, 15.3751, 15.3010, 15.1971, 15.3852, 15.3003],
            'loss_ll': [61.8058, 72.6629, 72.7090, 72.7650, 71.6363, 72.9298, 72.1457],
        },
        'only c-SR': {
            'tp': [325.8004, 388.0595, 447.6041, 503.1631, 559.9593, 607.8574, 656.0025],
            'lat': [29.1882, 42.1841, 51.2041, 59.4709, 68.1909, 75.6908, 83.1974],
            'loss': [18.5334, 22.3574, 25.4012, 28.0868, 29.8892, 32.3400, 34.2170],
            'lat_ll': [9.2254, 9.3420, 9.4878, 9.5932, 9.6846, 9.7702, 9.8771],
            'loss_ll': [25.9000, 31.2626, 34.0331, 36.3308, 38.1609, 40.2383, 41.7496],
        },
        'only c-TDMA': {
            'tp': [400.0505, 499.9656, 585.1602, 593.2900, 592.0349, 591.8794, 591.0747],
            'lat': [8.7763, 12.9003, 104.4593, 195.5770, 217.6979, 219.5886, 216.8175],
            'loss': [0.0538, 0.0415, 2.0057, 15.1055, 25.9497, 34.1457, 40.7270],
            'lat_ll': [5.5169, 5.6414, 6.6315, 7.0836, 7.3985, 7.7076, 7.9848],
            'loss_ll': [0.1798, 0.1715, 0.4722, 1.0002, 1.4911, 2.1609, 3.1519],
        },
        'Proposed (Rule-based)': {
            'tp': [380.4266, 447.9506, 497.9851, 548.3530, 598.9286, 645.9262, 691.8002],
            'lat': [19.0788, 31.9278, 46.1979, 58.1357, 66.8519, 74.1411, 82.1254],
            'loss': [4.8988, 10.4379, 16.9171, 21.5916, 25.0264, 28.0486, 30.7071],
            'lat_ll': [6.4097, 7.1824, 7.9225, 8.4407, 8.6894, 8.8915, 9.0459],
            'loss_ll': [2.6272, 6.8213, 12.9243, 18.0884, 21.5578, 24.8418, 27.2824],
        },
        'Proposed (ML-based)': {
            'tp': [389.2822, 475.6302, 549.2343, 616.6938, 672.6492, 726.2861, 764.1369],
            'lat': [19.0176, 27.3252, 42.5525, 52.6459, 67.5422, 78.1954, 89.7117],
            'loss': [2.6597, 5.0604, 8.4767, 12.1863, 15.9489, 19.4796, 23.6911],
            'lat_ll': [6.4615, 6.4725, 6.4865, 6.5568, 6.5599, 6.5886, 6.5706],
            'loss_ll': [0.7581, 0.7229, 0.9024, 0.9288, 0.9309, 1.1227, 1.0976],
        },
    },
}

# ── 실험 2: 저지연 STA 비율 10~50 % (results_ll.json, 100회 평균, 800 Mbps) ──
DATA_LL = {
    'ratios': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
    'results': {
        'CSMA/CA': {
            'tp': [295.2356, 188.6820, 102.1147, 52.0502, 30.7601, 17.3386, 7.7876, 5.7120, 3.2132],
            'lat': [360.3965, 318.8868, 265.9909, 193.6722, 141.8366, 130.5224, 124.4569, 107.3717, 126.2779],
            'loss': [63.0657, 76.3779, 87.2706, 93.5070, 96.1166, 97.8146, 98.9744, 99.3080, 99.5699],
            'lat_ll': [13.0278, 13.4484, 14.2299, 15.2009, 16.2697, 17.2264, 18.3502, 18.3964, 19.5656],
            'loss_ll': [30.9214, 42.5101, 59.5594, 75.3919, 86.0520, 92.5045, 96.6034, 97.9677, 98.9863],
        },
        'only c-SR': {
            'tp': [565.2973, 560.2659, 562.3589, 553.5128, 556.4954, 558.1359, 546.1000, 545.3565, 549.5357],
            'lat': [75.5394, 70.6059, 73.3077, 66.6512, 65.8850, 61.2748, 60.1650, 61.2491, 59.0884],
            'loss': [29.0489, 29.6716, 29.4944, 30.5230, 30.3421, 30.0671, 31.7734, 31.8284, 31.2438],
            'lat_ll': [9.5249, 9.7608, 9.8422, 9.5976, 9.5935, 9.7314, 9.7925, 9.7364, 9.6739],
            'loss_ll': [33.2201, 35.5847, 39.4518, 39.0433, 37.2590, 40.2079, 36.9439, 35.0860, 35.6825],
        },
        'only c-TDMA': {
            'tp': [625.7539, 611.5490, 600.0099, 588.4186, 581.4374, 575.7122, 571.0497, 568.5580, 569.2967],
            'lat': [287.6830, 270.1117, 257.3893, 233.3082, 199.2608, 171.9402, 143.1185, 132.4338, 117.6300],
            'loss': [21.6643, 23.4347, 24.9149, 26.4017, 27.3557, 28.1718, 28.5828, 28.9954, 28.8037],
            'lat_ll': [7.3755, 7.2933, 7.1230, 7.0765, 7.3148, 7.4779, 7.7859, 8.0248, 8.4621],
            'loss_ll': [1.6851, 0.9170, 0.8686, 0.8928, 1.1854, 2.0592, 3.4258, 4.7590, 7.9408],
        },
        'Proposed (Rule-based)': {
            'tp': [590.1774, 594.9867, 605.1426, 600.3127, 601.7055, 605.2708, 604.5176, 604.9566, 614.9007],
            'lat': [76.5816, 73.1822, 76.3307, 66.5657, 64.1274, 56.6725, 54.6236, 55.5975, 51.0180],
            'loss': [26.0272, 25.3194, 24.1795, 24.7917, 24.6837, 24.2363, 24.4259, 24.3649, 23.1790],
            'lat_ll': [8.6550, 8.6772, 8.9400, 8.6807, 8.7075, 8.6529, 8.7294, 8.6884, 8.7492],
            'loss_ll': [17.8432, 17.8089, 22.4413, 23.4567, 22.3556, 24.6114, 21.9747, 21.1485, 21.9904],
        },
        'Proposed (ML-based)': {
            'tp': [686.3932, 680.1261, 682.3418, 677.4881, 675.3950, 677.3100, 676.8496, 682.0417, 686.7038],
            'lat': [62.4965, 67.6198, 69.5111, 69.0653, 69.8609, 62.9182, 61.9009, 61.7685, 53.9092],
            'loss': [14.3271, 15.1268, 15.0910, 15.5189, 15.7751, 15.5221, 15.4282, 15.0209, 14.2752],
            'lat_ll': [5.8135, 6.4624, 6.4891, 6.6253, 6.7452, 6.8950, 6.9851, 7.0463, 7.2722],
            'loss_ll': [0.1271, 0.9648, 1.2011, 1.0547, 1.1714, 1.5810, 2.0782, 2.0803, 2.7973],
        },
    },
}
# ═══════════════════════════════════════════════════════════════════

# ── 글꼴: Times New Roman ──
#   Colab 에는 Times New Roman 이 기본 설치되어 있지 않다. 아래 순서로 찾는다.
#   1) 시스템에 설치된 Times New Roman
#   2) FONT_FILES 에 적은 ttf 파일 (Windows 의 C:/Windows/Fonts/times.ttf 등을 Colab 에 업로드해 두면 됨)
#   3) 둘 다 없으면 같은 규격(글자 폭 동일)의 Liberation Serif 로 대체하고 안내 문구를 출력한다.
import matplotlib.font_manager as fm
FONT_FILES = ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf',        # 업로드한 파일 이름 (같은 폴더)
              '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf']   # apt 로 설치했을 때의 위치
for f in FONT_FILES:
    if os.path.exists(f):
        fm.fontManager.addfont(f)
_names = {f.name for f in fm.fontManager.ttflist}
if 'Times New Roman' in _names:
    _serif = ['Times New Roman']
else:
    _serif = ['Liberation Serif', 'Nimbus Roman', 'DejaVu Serif']
    print('[안내] Times New Roman 이 없어 Liberation Serif 로 그립니다. 진짜 Times New Roman 을 쓰려면 '
          'times.ttf 를 이 노트북 폴더에 업로드하거나, 셀에서 다음을 실행한 뒤 런타임을 재시작하세요:\n'
          '  !echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections\n'
          '  !apt-get -qq install -y ttf-mscorefonts-installer > /dev/null')
plt.rcParams.update({'font.family': 'serif',
                     'font.serif': _serif,
                     'mathtext.fontset': 'stix',                          # 수식 글꼴도 Times 계열
                     'figure.dpi': 120,                                   # figure.dpi 는 화면 표시용
                     'pdf.fonttype': 42})                                 # pdf 에 글꼴 포함 (편집 가능)



# ── 논문용 그림: 지표 1개 = 그림 1장, (a) 부하 실험  (b) 저지연 STA 비율 실험 ──
FIGS = [
    ('tp',      'Throughput (Mbps)',     'fig4_throughput'),
    ('lat_ll',  'Latency (ms)',          'fig5_latency_ll'),
    ('loss_ll', 'Packet loss ratio (%)', 'fig6_loss_ll'),
]
PANEL_TAG = ['(a)', '(b)']          # 패널 아래 글자. 캡션에 (a)(b) 를 쓰면 여기서 빼도 됨 → PANEL_TAG = ['', '']
FIG2 = dict(size=(11.0, 4.2), wspace=0.28)


def _panel(ax, R, xs, key, xlabel, ylab, exp):
    for m in ORDER:
        if m not in R:
            continue
        st = STYLE[m]
        ax.plot(xs, R[m][key], label=st['label'], color=st['color'],
                marker=st['marker'], linestyle=st['ls'], linewidth=FIG['lw'],
                markersize=FIG['ms'], markerfacecolor=st['mfc'], markeredgecolor=st['color'],
                markeredgewidth=FIG['mew'])
    ax.set_xlabel(xlabel, fontsize=FIG['font_axis'])
    ax.set_ylabel(ylab, fontsize=FIG['font_axis'])
    ax.set_xticks(xs)
    ax.tick_params(axis='both', labelsize=FIG['font_tick'])
    ya = YAXIS.get((exp, key), {})
    if ya.get('lim') is not None:
        ax.set_ylim(*ya['lim'])
    if ya.get('step') is not None:
        ax.yaxis.set_major_locator(MultipleLocator(ya['step']))
    if FIG['grid']:
        ax.grid(True, linestyle=FIG['grid_style'], alpha=FIG['grid_alpha'], linewidth=FIG['grid_lw'])


def draw_paper(D1, D2):
    saved = []
    xs1 = D1['loads']
    xs2 = [round(r * 100) for r in D2['ratios']]
    for key, ylab, name in FIGS:
        fig, (a, b) = plt.subplots(1, 2, figsize=FIG2['size'])
        _panel(a, D1['results'], xs1, key, FIG['xlabel_load'], ylab, 'load')
        _panel(b, D2['results'], xs2, key, FIG['xlabel_ll'],   ylab, 'll')
        for ax, tag in zip((a, b), PANEL_TAG):
            if tag:
                ax.text(0.5, -0.30, tag, transform=ax.transAxes, ha='center', va='top', fontsize=FIG['font_axis'])
        h, l = a.get_legend_handles_labels()
        fig.legend(h, l, loc='lower center', bbox_to_anchor=(0.5, 0.97), ncol=len(l),
                   fontsize=FIG['font_legend'], frameon=False, handlelength=2.2, columnspacing=1.6)
        fig.subplots_adjust(wspace=FIG2['wspace'])
        os.makedirs(OUT_DIR, exist_ok=True)
        for ext in FIG['formats']:
            path = f'{OUT_DIR}/{name}.{ext}'
            fig.savefig(path, dpi=FIG['dpi'], bbox_inches='tight')
            saved.append(path)
        plt.show()
        plt.close(fig)
    return saved


import json
def load_results(kind, fallback):
    path = RESULT_FILES[kind]
    if os.path.exists(path):
        d = json.load(open(path, encoding='utf-8'))
        print(f'[{kind}] {path} 사용 (모델: {list(d["results"])})')
        return d
    print(f'[{kind}] {path} 없음 → 코드 안 DATA 사용')
    return fallback

D1 = load_results('load', DATA_LOAD)
D2 = load_results('ll', DATA_LL)
saved = draw_paper(D1, D2)
print('저장:', *saved, sep='\n  ')
if FIG['download']:
    import shutil
    from google.colab import files
    shutil.make_archive('figs', 'zip', OUT_DIR)
    files.download('figs.zip')
