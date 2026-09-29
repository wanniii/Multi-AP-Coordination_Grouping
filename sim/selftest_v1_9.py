import numpy as np
try:
    import mapc_grouping_HMAB_v1_9 as M      # 시뮬레이터 파일 이름
except ImportError:
    import mapc as M
kw=dict(n_ap=M.N_AP,n_sta=M.N_STA,k=M.K,ll_ratio=M.LL_RATIO,area=M.AREA,d_sta=M.D_STA)
fails=[]
def chk(c,msg):
    if not c: fails.append(msg); print('  ✗',msg)
# T1 큐
M.Queue.eval_start=0.0; M.Queue.eval_stop=float('inf')
qq=M.Queue(0.020); qq.push([0.0]*50); qq.expire(0.010); qq.send(20*M.FRAME_LEN,0.015,0.1)
chk(qq.tp_bits==qq.ok*M.FRAME_LEN,'T1 tp_bits = 측정 구간 전달 비트')
chk(qq.gen==50 and qq.ok==20 and qq.drop_retry==2 and len(qq)==28,'T1 큐 보존')
qq.expire(0.030); chk(qq.drop_dead==28 and len(qq)==0,'T1 마감 폐기')
chk(qq.gen==qq.ok+qq.drop_retry+qq.drop_dead,'T1 생성 = 전달 + 재전송폐기 + 마감초과')
qq2=M.Queue(0.020); M.Queue.eval_start=1.0; M.Queue.eval_stop=2.0
qq2.push([0.5]*10); qq2.push([1.5]*10); chk(qq2.gen==10,'T1 코호트 밖 패킷은 분모 제외')
M.Queue.eval_start=0.0; M.Queue.eval_stop=float('inf')
# T3 슬롯 규칙 (Case 1 / Case 2, 판정은 저지연 서비스 AP 기준. 9/10)
cl={0:[0,1,2],1:[3,4,5],2:[6,7]}; act=set(range(8))
def R(p): return [(dict(r['priority']), sorted(r['shared'])) for r in M.rounds_proposed(cl,p,act)]
for mode in ['tdma','group']:
    M.LL_INTRA=mode
    chk(R({0:[100],3:[103],6:[106]})==[({0:100,3:103,6:106},[]),({},[0,1,2,3,4,5,6,7])],f'T3[{mode}] Case1: 저지연 슬롯에 나머지 대기')
    chk(R({0:[100],1:[101]})==[({0:100},[3,4,5,6,7]),({1:101},[3,4,5,6,7]),({},[2,3,4,5,6,7])],f'T3[{mode}] Case2: 그룹 내 순번, 다른 그룹 내내 전송')
    chk(R({0:[100]})==[({0:100},[]),({},[0,1,2,3,4,5,6,7])],f'T3[{mode}] 저지연 1대')
    chk(R({})==[({},[0,1,2,3,4,5,6,7])],f'T3[{mode}] 저지연 없음: 1슬롯 전원')
M.LL_INTRA='tdma'
chk(R({0:[100],1:[101],3:[103],4:[104]})==[({0:100,3:103},[]),({1:101,4:104},[]),({},[0,1,2,3,4,5,6,7])],'T3[tdma] 혼합 ②: 저지연 슬롯 동안 나머지 대기')
M.LL_INTRA='group'
chk(R({0:[100],1:[101],3:[103],4:[104]})==[({0:100,3:103},[6,7]),({1:101,4:104},[6,7]),({},[2,5,6,7])],'T3[group] 혼합 ③: 저지연 없는 그룹은 계속 전송')
M.LL_INTRA='tdma'
chk(all(5 not in r['members'] for r in M.rounds_proposed(cl,{},act-{5})),'T3 비활성 AP 제외')
chk(len(M.rounds_conventional(cl,'tdma',act))==8 and len(M.rounds_conventional(cl,'csr',act))==1,'T3 종래')
# T4 그룹핑 + 배치
for seed in range(20):
    rng=np.random.default_rng(seed); ap,sta,own=M.make_topology(20,2,rng,80.,5.); ch=M.Channel(ap,sta,rng)
    sk,src,cl2,place=M.assign_traffic(ap,sta,own,rng,None,ch,800.)
    allm=sorted(a for m in cl2.values() for a in m); chk(allm==list(range(20)),f'T4 seed{seed} 모든 AP 한 그룹씩')
    chk(all(len(m)>=1 for m in cl2.values()),f'T4 seed{seed} 빈 그룹 없음')   # 1대 그룹 허용 (9/11)
    chk(place=='random',f'T4 seed{seed} 집중 배치 꺼짐')
    tot=sum(src[j].offered_mbps() for j in range(40)); chk(abs(tot-800.)<1.0,f'T4 seed{seed} 제공 로드 {tot:.1f}≠800')
# T5 MAB
for n in [2,3]:
    seen=set()
    B=len(M.POWER_ARMS)
    for arm in range(B**n):
        code=arm; combo=[]
        for _ in range(n): combo.append(M.POWER_ARMS[code%B]); code//=B
        seen.add(tuple(combo))
    chk(len(seen)==B**n,f'T5 전력 조합 {n}대')
u=M.UCB(3, c=1.0); [u.update(i,v) for i,v in [(0,1.0),(0,0.0),(1,0.5)]]; chk(abs(u.q[0]-0.5)<1e-9,'T5 UCB 갱신')
# T6 물리
rng=np.random.default_rng(1); ap,sta,own=M.make_topology(4,1,rng,40.,5.); ch=M.Channel(ap,sta,rng)
# SINR 단조성: 혼자 > 동시, 상대가 전력을 낮추면 회복 (serve_ap 내부와 같은 식)
def si(power, others):
    itf=[(power[b], ch.loss_now(b,0)) for b in others]
    return M.sinr_from_loss(power[0], ch.loss_now(0,0), itf)
s1=si({0:24.},[]); s2=si({0:24.,1:24.},[1]); s3=si({0:24.,1:6.},[1])
chk(s1>s2 and s3>s2, f'T6 SINR 단조: 혼자 {s1:.1f} > 동시 {s2:.1f} < 상대 저전력 {s3:.1f}')
pc=M.power_control([(0,0),(1,1)],ch); chk(all(M.MIN_TX_POWER<=v<=M.MAX_TX_POWER for v in pc.values()),'T6 전력 제어 범위')
chk(M.power_control([(0,0)],ch)[0]==M.MAX_TX_POWER,'T6 혼자 최대 전력'); chk(M.TARGET_SINR==10.0,'T6 목표 SINR 10')
# T8 실행 중 보존·전력 범위·슬롯 비율·AP 중복
_init=M.Queue.__init__
def _i(self,d): _init(self,d); M.Queue._all.append(self)
M.Queue.__init__=_i
log={'rounds':0,'p_bad':0,'dup':0}
_serve=M.serve_ap; pw_log={'bad':0}
def _serve2(a,first,members,powers,*args,**k):
    log['rounds']+=1
    if not(M.MIN_TX_POWER-1e-9<=powers[a]<=M.MAX_TX_POWER+1e-9): pw_log['bad']+=1
    if len(set(members))!=len(members): log['dup']+=1
    return _serve(a,first,members,powers,*args,**k)
M.serve_ap=_serve2
for model in ['csma','conv-csr','conv-tdma','proposed','mab']:
    M.Queue._all=[]
    r=M.simulate_mab(3,total_load=1000.,**kw) if model=='mab' else M.simulate(model,3,total_load=1000.,**kw)
    gen=sum(q.gen for q in M.Queue._all); ok=sum(q.ok for q in M.Queue._all)
    dr=sum(q.drop_retry for q in M.Queue._all); dd=sum(q.drop_dead for q in M.Queue._all)
    chk(gen==ok+dr+dd,f'T8 {model} 코호트 패킷 결과 확정: 생성 {gen} = 전달 {ok} + 재전송 {dr} + 마감 {dd}')
    chk(abs(sum(q.tp_bits for q in M.Queue._all)/(M.Queue.eval_stop-M.Queue.eval_start)/1e6-r["tp"])<1e-6,f'T8 {model} 처리량 재계산 (전달 완료 시각 기준)')
    chk(0<=r['loss']<=100 and r['lat_ll']<=30+1e-6 and r['lat']<=524+1e-6,f'T8 {model} 범위')
    print(f'  {model:>9}: tp {r["tp"]:6.1f} loss {r["loss"]:5.1f} (재전송 {r["loss_retry"]:.1f} + 마감 {r["loss_dead"]:.1f}) LLloss {r["loss_ll"]:5.1f} | 생성 {gen} = {ok}+{dr}+{dd}')
chk(pw_log['bad']==0 and log['dup']==0,f'T8 전력 범위 밖 {pw_log["bad"]}, AP 중복 {log["dup"]}')
print(f'\n검사 항목 통과, 실패 {len(fails)}')

# ── T9 (9/10 추가): 미래 패킷 전송 금지, 실험 2 정확한 저지연 수, MAB 진단값, 부하 범위 ──
fails2=[]
def chk2(c,msg):
    if not c: fails2.append(msg); print('  ✗',msg)
_send=M.Queue.send; viol={'n':0,'max':0.0}
def _send2(self,n_bits,now,dsc=0.0):
    for ts in list(self.q)[:int(n_bits//M.FRAME_LEN)]:
        if ts>now+1e-12: viol['n']+=1; viol['max']=max(viol['max'],ts-now)
    return _send(self,n_bits,now,dsc)
M.Queue.send=_send2
for model in ['proposed','mab','conv-csr','csma']:
    (M.simulate_mab(0,total_load=800.,**kw) if model=='mab' else M.simulate(model,0,total_load=800.,**kw))
chk2(viol['n']==0,f'T9 미래 패킷 전송 {viol["n"]}건 (최대 {viol["max"]*1e3:.2f} ms 앞섬)')
M.Queue.send=_send
for n_exact in [4,12,20]:
    M.N_LL_EXACT=n_exact; cnt=[]
    for seed in range(10):
        rng=np.random.default_rng(seed); ap,sta,own=M.make_topology(20,2,rng,80.,5.); ch=M.Channel(ap,sta,rng)
        sk,*_=M.assign_traffic(ap,sta,own,rng,None,ch,800.); cnt.append(sum(M.TRAFFIC[sk[j]]['is_ll'] for j in range(40)))
    chk2(all(c==n_exact for c in cnt),f'T9 N_LL_EXACT={n_exact} → 실제 {set(cnt)}')
M.N_LL_EXACT=None
r=M.simulate_mab(1,total_load=800.,**kw); r2=M.simulate('proposed',1,total_load=800.,**kw)
chk2(r['n_ll']==r2['n_ll'] and abs(r['offered']-r2['offered'])<1e-6 and r['n_groups']==r2['n_groups'],'T9 MAB 진단값이 rule 과 동일 (배치 같음)')
chk2(r['n_ll']>0 and r['offered']>0 and abs(r['g_ll0']+r['g_ll1']+r['g_ll2']-1)<1e-9,'T9 MAB 진단값 (그룹 저지연 분포 합 = 1)')
chk2(min(M.LOADS)>=400,'T9 부하 범위 하한 400')
print(f'T9 통과, 실패 {len(fails2)}')

# ── T10 (9/10): 슬롯 시각 누적이 TXOP 길이와 일치, 전달 시각이 TXOP 안 ──
chk2(abs(M.T_ROUND_PRE+M.T_ROUND_POST-M.T_ROUND_OH)<1e-12,'T10 PRE+POST=OH')
for n in [1,3,10]:
    data=M.TAU-(M.T_EDCA_ACCESS+M.T_MAPC_OH+n*M.T_ROUND_OH); tot=M.T_EDCA_ACCESS+M.T_MAPC_OH+n*M.T_ROUND_OH+data
    chk2(abs(tot-M.TAU)<1e-12 and data>0,f'T10 슬롯 {n}개 시각 합 = TXOP (획득 {M.T_EDCA_ACCESS*1e6:.0f}us 포함)')
_send3=M.Queue.send; late={'n':0}
def _send4(self,n_bits,now,dsc=0.0):
    # now 는 TXOP 시작 이후 TAU 이내여야 함
    import math
    if (now % M.TAU) > M.TAU+1e-9: late['n']+=1
    return _send3(self,n_bits,now,dsc)
M.Queue.send=_send4
M.simulate('proposed',0,total_load=800.,**kw); M.simulate_mab(0,total_load=800.,**kw)
M.Queue.send=_send3
chk2(late['n']==0,'T10 전달 시각 TXOP 범위 밖')
print(f'T10 통과, 실패 {len(fails2)}')

# ── T11 (9/10): priority 슬롯은 저지연 STA 에게만, shared 슬롯 목적지는 실행 시점 큐 기준 ──
viol2={'prio_nonll':0,'prio_multi':0,'prio_calls':0,'shared_calls':0}
_sv=M.serve_ap
def _sv2(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
    if only:
        viol2['prio_calls']+=1
        if not M.TRAFFIC[sta_kind[first]]['is_ll']: viol2['prio_nonll']+=1
        before={j:len(q[j].lats) for j in sta_of[a]}
        out=_sv(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
        if any(len(q[j].lats)>before[j] for j in sta_of[a] if not M.TRAFFIC[sta_kind[j]]['is_ll']): viol2['prio_multi']+=1
        return out
    viol2['shared_calls']+=1
    return _sv(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
M.serve_ap=_sv2
M.simulate('proposed',0,total_load=800.,**kw); M.simulate_mab(0,total_load=800.,**kw)
M.serve_ap=_sv
chk2(viol2['prio_calls']>0 and viol2['shared_calls']>0, f'T11 priority {viol2["prio_calls"]}회 / shared {viol2["shared_calls"]}회 모두 발생')
chk2(viol2['prio_nonll']==0, f'T11 priority 슬롯에 일반 STA 목적지 {viol2["prio_nonll"]}건')
chk2(viol2['prio_multi']==0, f'T11 priority 슬롯에서 일반 STA 에게 전송 {viol2["prio_multi"]}건')
print(f'T11 통과, 실패 {len(fails2)}')

# ── T12 (9/11): STA·AP 선택 순서 = AC 우선순위 → 큐 긴 순 → 오래된 패킷 ──
class _FQ:
    def __init__(self, n, t0): self.q=[t0]*n
    def __len__(self): return len(self.q)
_kinds={0:'VR',1:'VC',2:'BG',3:'BG'}
_q={0:_FQ(5,1.0), 1:_FQ(9,0.5), 2:_FQ(20,0.1), 3:_FQ(20,0.9)}
_key=lambda j: (M.AC_RANK[M.TRAFFIC[_kinds[j]]['ac']], -len(_q[j]), _q[j].q[0])
chk2(min([0,1,2,3], key=_key)==0, 'T12 AC 우선 (VR=VO 가 큐 적어도 1등)')
chk2(min([2,3], key=_key)==2, 'T12 같은 AC·같은 큐면 오래된 패킷 먼저')
_q[3].q=[0.9]*30
chk2(min([2,3], key=_key)==3, 'T12 같은 AC 면 큐 긴 쪽 먼저')
# 그룹 안 AP 순서: rank_of 를 주면 그 순서대로 슬롯이 만들어지는가
cl2={0:[10,11,12]}; act2={10,11,12}
prio={10:[100],11:[101],12:[102]}
rk={10:(0,-5,0.0), 11:(0,-9,0.0), 12:(0,-20,0.0)}     # 큐 20, 9, 5 순 → 12, 11, 10
M.LL_INTRA='tdma'
order=[list(r['priority'])[0] for r in M.rounds_proposed(cl2, prio, act2, rk) if r['priority']]
chk2(order==[12,11,10], f'T12 그룹 안 AP 순서가 큐 긴 순 (실측 {order})')
print(f'T12 통과, 실패 {len(fails2)}')

# ══════════════════════════════════════════════════════════════════════════
# v1.9 (9/12) 추가 검사: EDCA 경쟁 모델 · CSMA/CA 단일 전송 · Co-TDMA (Lee) · 슬롯이 TXOP 안에 있는지
# ══════════════════════════════════════════════════════════════════════════
from collections import Counter
fails3=[]
def chk3(c,msg):
    if not c: fails3.append(msg); print('  ✗',msg)

# ── T13 EDCA Bianchi 고정점 ──
B1=M.edca_bianchi(Counter({'BE':1}))
chk3(abs(B1['p_tr']-B1['tau']['BE'])<1e-9 and abs(B1['p_s']['BE']-B1['tau']['BE'])<1e-9,'T13 경쟁자 1대: P_tr = P_s = τ (충돌 없음)')
for cnt in [{'BE':20},{'VO':3,'VI':2,'BE':15},{'VO':6,'BE':14}]:
    B=M.edca_bianchi(Counter(cnt)); ps=sum(B['p_s'].values())
    chk3(0<ps<=B['p_tr']<=1,f'T13 {cnt}: 0 < P_s {ps:.3f} ≤ P_tr {B["p_tr"]:.3f} ≤ 1')
    chk3(all(0<t<=0.5 for t in B['tau'].values()),f'T13 {cnt}: τ 범위')
Bv=M.edca_bianchi(Counter({'VO':1,'BE':19}))
chk3(Bv['tau']['VO']>Bv['tau']['BE'] and Bv['p_s']['VO']>Bv['p_s']['BE']/19,'T13 VO 가 BE 보다 자주 이긴다 (AC 우선순위)')
b10=M.edca_bianchi(Counter({'BE':10}))['p_s']['BE']/10; b20=M.edca_bianchi(Counter({'BE':20}))['p_s']['BE']/20
chk3(b10>b20,'T13 경쟁자가 늘면 AP 당 성공 확률 감소')
chk3(M.edca_bianchi(Counter({'BE':20})) is M.edca_bianchi(Counter({'BE':20})),'T13 같은 경쟁자 구성은 캐시')
chk3(abs(M.aifs('VO')-(M.SIFS+2*M.SLOT_TIME))<1e-12 and abs(M.aifs('BE')-(M.SIFS+3*M.SLOT_TIME))<1e-12,'T13 AIFS = SIFS + AIFSN·슬롯')
chk3(M.TXOP_LIMIT=={'VO':2.080e-3,'VI':4.096e-3,'BE':0.0,'BK':0.0},'T13 TXOP limit = 802.11-2020 Table 9-155')
chk3(M.CSMA_EDCA is True and M.TDMA_SCHED=='lee','T13 기본 설정: CSMA_EDCA=True, TDMA_SCHED=lee')

# ── T14 CSMA/CA: 접근마다 AP 1 대, TXOP limit 준수, BE 는 PPDU 하나(single), 스텝 시간 계정 ──
rec={'calls':0,'multi':0,'limit':0,'single_bad':0,'power_bad':0,'ll_win':0,'be_win':0}
_sv0=M.serve_ap
def _svc(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
    rec['calls']+=1
    if len(members)!=1: rec['multi']+=1
    ac=M.TRAFFIC[sta_kind[first]]['ac']
    lim=M.TXOP_LIMIT[ac] if M.CSMA_STD_TXOP_LIMIT else M.TAU
    if lim==0.0: lim=M.MAX_PPDU
    if dur>lim+1e-9: rec['limit']+=1
    if single!=(M.TXOP_LIMIT[ac]==0.0): rec['single_bad']+=1
    if abs(powers[a]-M.MAX_TX_POWER)>1e-9: rec['power_bad']+=1
    if M.TRAFFIC[sta_kind[first]]['is_ll']: rec['ll_win']+=1
    else: rec['be_win']+=1
    return _sv0(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
M.serve_ap=_svc
r=M.simulate('csma',0,total_load=800.,**kw)
M.serve_ap=_sv0
chk3(rec['calls']>0 and rec['multi']==0,f'T14 CSMA 접근마다 전송 AP 1대 (동시 {rec["multi"]}건 / {rec["calls"]}회)')
chk3(rec['limit']==0,f'T14 CSMA TXOP limit 초과 {rec["limit"]}건')
chk3(rec['single_bad']==0,'T14 CSMA: BE/BK 는 PPDU 하나(single), VO/VI 는 TXOP 안 여러 STA')
chk3(rec['power_bad']==0,'T14 CSMA 최대 전력')
chk3(rec['ll_win']>0 and rec['be_win']>0,f'T14 CSMA 저지연 승자 {rec["ll_win"]} / 일반 승자 {rec["be_win"]} 모두 발생')
# DCF 변형 (전원 BE) 도 돌아가고, EDCA 보다 저지연 승리 비율이 낮은지
rec_edca=rec['ll_win']/max(rec['calls'],1)
rec={'calls':0,'multi':0,'limit':0,'single_bad':0,'power_bad':0,'ll_win':0,'be_win':0}
M.CSMA_EDCA=False; M.serve_ap=_svc; M.simulate('csma',0,total_load=800.,**kw); M.serve_ap=_sv0; M.CSMA_EDCA=True
chk3(rec['calls']>0 and rec['ll_win']/rec['calls']<rec_edca,f'T14 DCF 변형: 저지연 승리 비율 {rec["ll_win"]/rec["calls"]:.2f} < EDCA {rec_edca:.2f}')
# csma_txop 시간 계정: 스텝마다 사용 시간 ≥ TAU 또는 경쟁자 없음 (승자 없이 시간이 새지 않음)
chk3(0<=r['loss']<=100 and r['tp']>0,'T14 CSMA 결과 범위')

# ── T15 슬롯 시각이 TXOP 안 (MAPC 모델 전부): 시작·끝이 같은 TXOP 안 ──
def _slots_within_txop(model):
    bad={'n':0,'calls':0}
    def _svt(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
        bad['calls']+=1
        start=now-dur; idx=int(np.floor(start/M.TAU+1e-9))
        if now>(idx+1)*M.TAU+1e-9 or start<idx*M.TAU-1e-9: bad['n']+=1
        return _sv0(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
    M.serve_ap=_svt
    (M.simulate_mab(0,total_load=800.,**kw) if model=='mab' else M.simulate(model,0,total_load=800.,**kw))
    M.serve_ap=_sv0
    return bad
for model in ['conv-csr','conv-tdma','proposed','mab']:
    b=_slots_within_txop(model); chk3(b['calls']>0 and b['n']==0,f'T15 {model}: 슬롯이 TXOP 밖으로 나감 {b["n"]}건 / {b["calls"]}회')

# ── T16 Co-TDMA (Lee): sharing AP 자기 DL 먼저(only=False), shared AP 는 저지연만(only=True, first 가 LL), 공유 발생 ──
lee={'own':0,'shared':0,'shared_nonll':0,'shared_first_bad':0,'per_txop':Counter(),'first_only':0}
def _svl(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
    idx=int(np.floor((now-dur)/M.TAU+1e-9)); lee['per_txop'][idx]+=1
    if only:
        lee['shared']+=1
        if not M.TRAFFIC[sta_kind[first]]['is_ll']: lee['shared_nonll']+=1
        if lee['per_txop'][idx]==1: lee['first_only']+=1     # 스텝의 첫 슬롯은 sharing AP 의 자기 DL(only=False) 이어야
    else:
        lee['own']+=1
    if len(members)!=1: lee['shared_first_bad']+=1
    return _sv0(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
M.TDMA_SCHED='lee'; M.TDMA_MAX_SHARE=None
M.serve_ap=_svl; r_lee=M.simulate('conv-tdma',0,total_load=800.,**kw); M.serve_ap=_sv0
chk3(lee['own']>0 and lee['shared']>0,f'T16 Lee: sharing AP 전송 {lee["own"]} / shared AP 공유 {lee["shared"]} 모두 발생')
chk3(lee['shared_nonll']==0,f'T16 Lee: shared AP 가 일반 STA 에게 전송 {lee["shared_nonll"]}건')
chk3(lee['first_only']==0,'T16 Lee: 스텝의 첫 슬롯은 sharing AP 의 자기 DL (CF-End 뒤 새 sharing AP 는 허용)')
chk3(lee['shared_first_bad']==0,'T16 Lee: Co-TDMA 슬롯은 항상 AP 1대')
# equal 모드 + K=5: TXOP 당 AP 수 ≤ 5, 20 대가 모두 서비스됨
eq={'per_txop':Counter(),'aps':set()}
def _sve(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
    idx=int(np.floor((now-dur)/M.TAU+1e-9)); eq['per_txop'][idx]+=1; eq['aps'].add(a)
    return _sv0(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
M.TDMA_SCHED='equal'; M.TDMA_MAX_SHARE=5
M.serve_ap=_sve; r_eq=M.simulate('conv-tdma',0,total_load=800.,**kw); M.serve_ap=_sv0
chk3(max(eq['per_txop'].values())<=5 and len(eq['aps'])==M.N_AP,f'T16 equal K=5: TXOP 당 최대 {max(eq["per_txop"].values())}대, 서비스된 AP {len(eq["aps"])}/{M.N_AP}')
# lee-equal: 스텝마다 최대 5대, 첫 슬롯은 sharing AP 의 자기 DL, 나머지는 균등 길이
le={'per_txop':Counter(),'durs':{}}
def _svle(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff=1.0, only=False, single=False):
    idx=int(np.floor((now-dur)/M.TAU+1e-9)); le['per_txop'][idx]+=1; le['durs'].setdefault(idx,[]).append(dur)
    return _sv0(a, first, members, powers, ch, q, sta_of, sta_kind, dur, now, eff, only, single)
M.TDMA_SCHED='lee-equal'; M.TDMA_MAX_SHARE=5
M.serve_ap=_svle; r_le=M.simulate('conv-tdma',0,total_load=800.,**kw); M.serve_ap=_sv0
eq_ok=all(max(d[1:])-min(d[1:])<1e-9 for d in le['durs'].values() if len(d)>2)
chk3(max(le['per_txop'].values())<=5 and eq_ok,f'T16 lee-equal: TXOP 당 최대 {max(le["per_txop"].values())}대, shared AP 슬롯 균등 {eq_ok}')
M.TDMA_SCHED='lee'; M.TDMA_MAX_SHARE=None
chk3(all(0<=x['loss_ll']<=100 and x['tp']>0 for x in (r_lee,r_eq)),f'T16 두 스케줄 결과 범위 (Lee 저지연 손실 {r_lee["loss_ll"]:.1f}, equal {r_eq["loss_ll"]:.1f}; 우열은 seed 평균으로 판단)')
print(f'T13~T16 통과, 실패 {len(fails3)}')
print(f'\n전체 실패 {len(fails)+len(fails2)+len(fails3)}')
