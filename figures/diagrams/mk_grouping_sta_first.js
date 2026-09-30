const pptxgen = require('pptxgenjs');
const pres = new pptxgen(); pres.layout = 'LAYOUT_WIDE';
const s = pres.addSlide();
const PUR='7B2CBF', BLUE='1E4B9E', GREY='8A8A8A', LGREY='C8C8C8', F='Times New Roman';
function img(f,x,y,w,h){ s.addImage({path:f,x:x-w/2,y:y-h/2,w,h}); }
function ap(x,y,label){ img('icons/ap.png',x,y,0.87,0.48); if(label) s.addText(label,{x:x-0.5,y:y-0.55,w:1.0,h:0.25,align:'center',fontSize:11,fontFace:F,isTextBox:true,margin:0}); }
function master(x,y){ img('icons/master.png',x,y,0.9,0.56); s.addText('Master AP',{x:x-0.8,y:y+0.3,w:1.6,h:0.3,align:'center',fontSize:12,bold:true,color:BLUE,fontFace:F,isTextBox:true,margin:0}); }
function sta(x,y){ s.addShape(pres.ShapeType.ellipse,{x:x-0.08,y:y-0.08,w:0.16,h:0.16,fill:{color:'B0B0B0'},line:{color:'666666',width:0.75}}); }
function star(x,y,label){ s.addShape(pres.ShapeType.star5,{x:x-0.17,y:y-0.17,w:0.34,h:0.34,fill:{color:'E0202A'},line:{color:'7A0000',width:0.5}});
  if(label) s.addText(label,{x:x-0.3,y:y+0.17,w:0.6,h:0.25,align:'center',fontSize:11,bold:true,fontFace:F,isTextBox:true,margin:0}); }
function line(p,q,o){ o=o||{}; const x=Math.min(p[0],q[0]), y=Math.min(p[1],q[1]), w=Math.abs(q[0]-p[0]), h=Math.abs(q[1]-p[1]);
  const flipV=((q[0]-p[0])*(q[1]-p[1]))<0; const arrowAtEnd=q[0]>=p[0]; const ln={color:o.color||GREY,width:o.width||1};
  if(o.dash) ln.dashType=o.dash; if(o.arrow){ if(arrowAtEnd) ln.endArrowType='triangle'; else ln.beginArrowType='triangle'; }
  s.addShape(pres.ShapeType.line,{x,y,w:Math.max(w,0.001),h:Math.max(h,0.001),flipV,line:ln}); }
function txt(t,x,y,w,o){ o=o||{}; s.addText(t,{x:x-w/2,y,w,h:o.h||0.3,align:'center',fontSize:o.fs||11,bold:!!o.bold,italic:!!o.it,color:o.color||'000000',fontFace:F,isTextBox:true,margin:0}); }

// same geometry in both panels
function panel(px, mode){
  const M=[px+3.0,0.95], AP1=[px+1.5,3.0], AP2=[px+4.5,3.0];
  master(...M); ap(...AP1); ap(...AP2);
  txt('AP1',AP1[0]-0.95,AP1[1]-0.15,0.6,{fs:11}); txt('AP2',AP2[0]+0.95,AP2[1]-0.15,0.6,{fs:11});
  const S=[[px+0.75,2.4],[px+0.7,3.7],[px+5.25,2.4],[px+5.3,3.7]];
  const L={A:[px+2.75,3.7],B:[px+3.25,3.7],C:[px+3.0,3.1]};
  if(mode==='a'){
    [AP1,AP2].forEach(c=>s.addShape(pres.ShapeType.ellipse,{x:c[0]-2.0,y:c[1]-1.8,w:4.0,h:3.6,fill:{type:'none'},line:{color:LGREY,width:1,dashType:'sysDot'}}));
    S.forEach(p=>sta(...p)); Object.entries(L).forEach(([k,p])=>star(...p,k));
    txt('STAs not yet associated  (dotted: AP coverage)',px+3.0,5.0,4.5,{color:'777777',it:true,fs:11});
  } else {
    S.slice(0,2).forEach(p=>{line(p,AP1);sta(...p)}); S.slice(2).forEach(p=>{line(p,AP2);sta(...p)});
    Object.values(L).forEach(p=>line(p,AP2));
    Object.entries(L).forEach(([k,p])=>star(...p,k));
    s.addShape(pres.ShapeType.ellipse,{x:px+2.2,y:2.7,w:1.6,h:1.65,fill:{type:'none'},line:{color:PUR,width:2,dashType:'dash'}});
    txt('LS STA group',px+3.0,4.5,1.8,{color:PUR,bold:true,fs:12});
    line([M[0],M[1]+0.3],[px+3.0,2.72],{color:BLUE,width:1.5,dash:'dash'});
    txt('group LS STAs',px+2.2,1.85,1.5,{color:BLUE,it:true,fs:11});
    line([M[0]+0.15,M[1]+0.3],[AP2[0]-0.1,AP2[1]-0.3],{color:BLUE,width:1.5,arrow:true});
    txt('assign group to AP2',px+4.55,1.65,1.9,{color:BLUE,it:true,fs:11});
  }
}
panel(0.7,'a'); panel(6.95,'b');
txt('(a) Before association: STAs and candidate APs',3.7,5.55,6.0,{fs:14});
txt('(b) Master AP groups LS STAs and assigns the group to one AP',9.95,5.55,6.0,{fs:14});
let lx=3.6, ly=6.55;
sta(lx,ly+0.15); txt('STA',lx+0.5,ly,0.8,{fs:11});
star(lx+1.5,ly+0.15,null); txt('latency-sensitive STA',lx+2.9,ly,2.2,{fs:11});
line([lx+4.5,ly+0.15],[lx+5.1,ly+0.15],{color:PUR,width:2,dash:'dash'}); txt('LS STA group',lx+5.8,ly,1.3,{fs:11});
pres.writeFile({fileName:'grouping_sta_first.pptx'}).then(()=>console.log('ok'));
