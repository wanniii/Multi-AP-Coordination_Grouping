const pptxgen = require('pptxgenjs');
const pres = new pptxgen(); pres.layout = 'LAYOUT_WIDE';   // 13.33 x 7.5 (= 12192000 x 6858000 EMU)
const F='Pretendard', FB='Pretendard ExtraBold', NAVY='1F2D5C', GREY='595959', HL='E2F0D9', PUR='E9DDF7';
function header(s, num, title){
  s.addText(num,{x:0.3,y:0.22,w:0.7,h:0.5,fontFace:FB,fontSize:24,bold:true,color:'000000',isTextBox:true,margin:0});
  s.addShape(pres.ShapeType.rect,{x:0.3,y:0.72,w:0.55,h:0.06,fill:{color:'000000'},line:{color:'000000'}});
  s.addText(title,{x:1.0,y:0.22,w:6,h:0.5,fontFace:F,fontSize:22,bold:true,color:'000000',isTextBox:true,margin:0});
  s.addShape(pres.ShapeType.line,{x:5.9,y:0.47,w:7.1,h:0,line:{color:'000000',width:0.75}});
}
function band(s, text, y){ s.addText(text,{x:0.55,y,w:12.2,h:0.36,fontFace:F,fontSize:13,bold:true,fill:{color:PUR},isTextBox:true,margin:[0,0,0,8],valign:'middle'}); }
// bullet levels: 0 = ▪ bold, 1 = ➢, 2 = •
function bullets(s, items, x, y, w, h, fs){
  fs = fs || 12.5;
  const runs = items.map(([lvl,txt,opt],i)=>{
    const o = Object.assign({fontFace:F,fontSize:fs,color:'000000',breakLine:i<items.length-1,paraSpaceAfter:5},opt||{});
    if(lvl===0){ o.bullet={code:'25AA'}; o.bold=true; o.indentLevel=0; }
    else if(lvl===1){ o.bullet={code:'27A2'}; o.indentLevel=1; }
    else { o.bullet={code:'2022'}; o.indentLevel=2; o.fontSize=fs-1; }
    return {text:txt,options:o};
  });
  s.addText(runs,{x,y,w,h,isTextBox:true,valign:'top',margin:[2,2,2,2]});
}
function cap(s,t,x,y,w){ s.addText(t,{x,y,w,h:0.3,fontFace:F,fontSize:11,bold:true,align:'center',isTextBox:true,margin:0}); }

// ───────── 1. 개요 ─────────
let s=pres.addSlide(); header(s,'00','제안 모델 (TAG-ST) 상세');
band(s,'❖  MobiSec 2026: RSSI and Traffic-Aware Grouping with Spatial-Temporal Coordination',0.95);
bullets(s,[
 [0,'문제 정의'],
 [1,'다수 BSS가 겹치는 밀집 환경에서 저지연(latency-sensitive) 트래픽이 일반 트래픽과 채널을 경쟁'],
 [1,'기존 Co-SR / Co-TDMA는 협력 방식을 하나로 고정하고, 어떤 AP끼리 협력할지(그룹)를 정하지 않음'],
 [0,'구성 요소'],
 [1,'Master AP: 그룹화·협력 방식·슬롯·전력을 결정하는 조정 AP (sharing AP 역할)'],
 [1,'AP(BSS): 자기 STA를 서비스, Master AP의 트리거에 따라 전송'],
 [1,'STA: 트래픽 종류(저지연 / 일반)를 가짐. 저지연 STA를 서비스하는 AP = "저지연 서비스 AP"'],
 [0,'동작 구조 (2단계)'],
 [1,'① 초기화: Master AP가 AP 간 RSSI로 BSS를 그룹화 (배치 동안 고정)'],
 [1,'② TXOP마다: 저지연 트래픽 분포 관측 → 협력 방식 결정 → ML로 슬롯·전력 결정 → 협력 전송'],
 [0,'하향링크만 고려, 저지연 트래픽 하나만 특성으로 사용'],
],0.55,1.45,7.0,5.5);
s.addImage({path:'fig2.png',x:7.9,y:1.45,w:5.1,h:4.64});
cap(s,'TAG-ST 동작 흐름',7.9,6.12,5.1);

// ───────── 2. 그룹화 ─────────
s=pres.addSlide(); header(s,'00','제안 모델 (TAG-ST) 상세');
band(s,'①  초기화: RSSI 기반 BSS 그룹화',0.95);
bullets(s,[
 [0,'입력'],
 [1,'Master AP가 각 AP의 부하(연결 STA 수·큐)와 AP 간 RSSI를 수집'],
 [0,'절차'],
 [1,'부하가 낮은 AP부터 center AP 후보로 검사'],
 [1,'기존 center AP들로부터의 RSSI가 모두 임계값(−70 dBm) 미만이면 새 center AP로 채택'],
 [1,'center가 아닌 AP는 RSSI가 가장 큰 center AP의 그룹에 합류, 소속 STA는 자기 AP를 따름'],
 [0,'특징'],
 [1,'그룹 = 서로 가까운 BSS 묶음 → 그룹 간 간섭이 작아 동시 전송(Co-SR)에 유리'],
 [1,'그룹 구성은 배치 동안 고정. 트래픽 특성은 그룹화에 쓰지 않음 (부하 순서만 사용)'],
 [1,'12 AP 배치 100회 기준 평균 5.2개 그룹 (최소 3, 최대 8)'],
 [0,'특허 관점'],
 [1,'Master AP → AP: 그룹 ID, center AP 여부를 통지해야 함 (MAPC Negotiation / Notification)'],
],0.55,1.45,6.4,5.5);
s.addImage({path:'fig1.png',x:7.2,y:1.75,w:5.8,h:3.26});
cap(s,'(a) 초기 BSS 배치  →  (b) RSSI 기반 그룹화 (center AP 표시)',7.2,5.05,5.8);

// ───────── 3. TXOP 협력 방식 ─────────
s=pres.addSlide(); header(s,'00','제안 모델 (TAG-ST) 상세');
band(s,'②  TXOP마다: 저지연 트래픽 분포 관측 → 협력 방식 결정',0.95);
bullets(s,[
 [0,'관측: Master AP가 TXOP 획득(EDCA) 후 ICF 전송, 각 AP는 ICR로 "저지연 큐 보유 여부·큐 상태" 응답'],
 [0,'판정 (STA 기준, 매 TXOP 반복)'],
 [1,'저지연 STA 없음 → 모든 그룹 동시 전송 (Co-SR)'],
 [1,'저지연 서비스 AP가 여러 그룹에 분산 (Distributed) → Priority slot: 저지연 서비스 AP만 전송 (다른 그룹끼리 동시, 같은 그룹은 순번), 나머지 AP는 대기 → Shared slot: 전원 Co-SR'],
 [1,'저지연 서비스 AP가 한 그룹에 집중 (Concentrated) → 그 그룹은 TXOP 전체를 AP별 순차 전송 (Co-TDMA), 다른 그룹은 Co-SR'],
 [0,'그룹 안 전송 순서: AC 우선순위 → 큐 길이 → 대기 시간'],
],0.55,1.45,12.3,2.6);
s.addImage({path:'s2_image2.png',x:0.55,y:4.15,w:6.15,h:1.8});  cap(s,'Distributed traffic mode',0.55,5.98,6.15);
s.addImage({path:'s2_image4.png',x:6.95,y:4.15,w:6.0,h:1.81});  cap(s,'Concentrated traffic mode',6.95,5.98,6.0);

// ───────── 4. ML + 정보 매핑 ─────────
s=pres.addSlide(); header(s,'00','제안 모델 (TAG-ST) 상세');
band(s,'③  ML(H-MAB)로 슬롯·전력 결정  &  단계별 필요 정보 → 필드',0.95);
bullets(s,[
 [0,'결정 변수 (Master AP, TXOP마다)'],
 [1,'Priority slot 시간 비율 (0.1–0.9),  슬롯 수 (1–5),  그룹 송신 전력 (6 / 12 / 24 dBm)'],
 [0,'학습'],
 [1,'입력: 그룹 구성, 저지연 서비스 AP, 큐 상태 / 보상: 저지연 패킷 전달률 + 전체 전달률'],
 [1,'사전 데이터 없이 온라인 학습 (UCB1), 그룹 구성별로 별도 에이전트'],
],0.55,1.45,12.3,1.75);
const th={bold:true,fill:{color:'D9D9D9'},fontFace:F,fontSize:11.5,align:'center',valign:'middle'};
const td={fontFace:F,fontSize:11,valign:'middle'};
const tdc=Object.assign({},td,{align:'center'});
const rows=[
 [{text:'단계',options:th},{text:'필요한 정보',options:th},{text:'방향',options:th},{text:'전달 프레임 / 필드 (Draft 기준 후보)',options:th}],
 [{text:'① 그룹화',options:tdc},{text:'그룹 ID, center AP 여부',options:td},{text:'Master → AP',options:tdc},{text:'MAPC Negotiation / Notification (Action frame, MAPC element)',options:td}],
 [{text:'② 관측',options:tdc},{text:'저지연 큐 보유 여부, 큐 상태',options:td},{text:'AP → Master',options:tdc},{text:'ICR (기존 Co-TDMA 폴링 응답)',options:td}],
 [{text:'② 협력 방식',options:tdc},{text:'동작 모드 (Co-SR / Distributed / Concentrated)',options:td},{text:'Master → AP',options:tdc},{text:'Trigger frame · MAPC User Info: Operation Mode',options:td}],
 [{text:'③ 슬롯',options:tdc},{text:'슬롯 순번, 슬롯 길이(비율)',options:td},{text:'Master → AP',options:tdc},{text:'Trigger frame · MAPC User Info: Slot Index',options:td}],
 [{text:'③ 전력',options:tdc},{text:'그룹 송신 전력 상한',options:td},{text:'Master → AP',options:tdc},{text:'Trigger frame · MAPC User Info: TX Power Limit (기존 필드)',options:td}],
];
s.addTable(rows,{x:0.55,y:3.35,w:12.3,colW:[1.4,3.6,1.5,5.8],border:{type:'solid',color:'7F7F7F',pt:0.75},rowH:0.42});
s.addText('→ 그룹 ID · 동작 모드 · 슬롯 순번이 제안에서 새로 필요한 정보, TX Power Limit은 기존 필드 재사용',{x:0.55,y:6.35,w:12.3,h:0.35,fontFace:F,fontSize:11.5,color:NAVY,bold:true,isTextBox:true,margin:0});

// ───────── 5. 결과 요약 ─────────
s=pres.addSlide(); header(s,'00','제안 모델 (TAG-ST) 상세');
band(s,'실험 결과 요약 (12 AP, 100회 평균, 총 부하 1000 Mbps)',0.95);
s.addImage({path:'fig7.png',x:0.4,y:1.45,w:4.15,h:2.37}); cap(s,'Throughput',0.4,3.83,4.15);
s.addImage({path:'fig8.png',x:4.6,y:1.45,w:4.15,h:2.37}); cap(s,'Latency (latency-sensitive)',4.6,3.83,4.15);
s.addImage({path:'fig9.png',x:8.8,y:1.45,w:4.15,h:2.37}); cap(s,'Packet loss ratio (latency-sensitive)',8.8,3.83,4.15);
const rh={bold:true,fill:{color:'D9D9D9'},fontFace:F,fontSize:11,align:'center',valign:'middle'};
const rc={fontFace:F,fontSize:11,align:'center',valign:'middle'};
const rb=Object.assign({},rc,{bold:true,fill:{color:HL}});
const R=[
 [{text:'',options:rh},{text:'CSMA/CA',options:rh},{text:'Co-SR',options:rh},{text:'Co-TDMA',options:rh},{text:'TAG-ST (rule)',options:rh},{text:'TAG-ST (RL)',options:rh}],
 [{text:'처리량 (Mbps)',options:rh},{text:'76.2',options:rc},{text:'656.0',options:rc},{text:'591.1',options:rc},{text:'691.8',options:rc},{text:'764.1',options:rb}],
 [{text:'저지연 지연 (ms)',options:rh},{text:'15.30',options:rc},{text:'9.88',options:rc},{text:'7.98',options:rc},{text:'9.05',options:rc},{text:'6.57',options:rb}],
 [{text:'저지연 손실률 (%)',options:rh},{text:'72.15',options:rc},{text:'41.75',options:rc},{text:'3.15',options:rc},{text:'27.28',options:rc},{text:'1.10',options:rb}],
];
s.addTable(R,{x:1.2,y:4.35,w:10.9,colW:[2.1,1.76,1.76,1.76,1.76,1.76],border:{type:'solid',color:'7F7F7F',pt:0.75},rowH:0.36});
bullets(s,[
 [1,'그룹화 + 저지연 우선 슬롯으로 Co-TDMA 수준의 지연·손실을 유지하면서 Co-SR 이상의 처리량 확보'],
 [1,'RL이 저지연 트래픽에 필요한 만큼 priority slot 비중을 늘려(규칙 5% → 약 45%) 손실률을 크게 낮춤'],
],0.55,5.9,12.3,0.9,12);
pres.writeFile({fileName:'model_slides.pptx'}).then(()=>console.log('ok'));
