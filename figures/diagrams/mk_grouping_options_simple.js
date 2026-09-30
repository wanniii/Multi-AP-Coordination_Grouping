const pptxgen = require('pptxgenjs');
const pres = new pptxgen(); pres.layout = 'LAYOUT_WIDE';
const s = pres.addSlide();
const RED='D62728', PUR='7B2CBF', BLUE='1E4B9E', GREY='8A8A8A', LGREY='C8C8C8';
const F='Times New Roman';
function img(f,x,y,w,h){ s.addImage({path:f,x:x-w/2,y:y-h/2,w,h}); }
function ap(x,y){ img('icons/ap.png',x,y,0.87,0.48); }
function master(x,y){ img('icons/master.png',x,y,0.9,0.56); s.addText('Master AP',{x:x-0.8,y:y+0.3,w:1.6,h:0.3,align:'center',fontSize:12,bold:true,color:BLUE,fontFace:F,isTextBox:true,margin:0}); }
function sta(x,y){ s.addShape(pres.ShapeType.ellipse,{x:x-0.08,y:y-0.08,w:0.16,h:0.16,fill:{color:'B0B0B0'},line:{color:'666666',width:0.75}}); }
function star(x,y,label,hollow){ s.addShape(pres.ShapeType.star5,{x:x-0.17,y:y-0.17,w:0.34,h:0.34,fill:hollow?{color:'FFFFFF'}:{color:'E0202A'},line:{color:hollow?'E0202A':'7A0000',width:hollow?1.25:0.5}});
  if(label) s.addText(label,{x:x-0.3,y:y+0.17,w:0.6,h:0.25,align:'center',fontSize:11,bold:!hollow,color:hollow?'999999':'000000',fontFace:F,isTextBox:true,margin:0}); }
function line(p,q,o){ o=o||{}; const x=Math.min(p[0],q[0]), y=Math.min(p[1],q[1]), w=Math.abs(q[0]-p[0]), h=Math.abs(q[1]-p[1]);
  const flipV=((q[0]-p[0])*(q[1]-p[1]))<0; const arrowAtEnd = q[0]>=p[0];
  const ln={color:o.color||GREY,width:o.width||1};
  if(o.dash) ln.dashType=o.dash; if(o.arrow){ if(arrowAtEnd) ln.endArrowType='triangle'; else ln.beginArrowType='triangle'; }
  s.addShape(pres.ShapeType.line,{x,y,w:Math.max(w,0.001),h:Math.max(h,0.001),flipV,line:ln}); }
function txt(t,x,y,w,o){ o=o||{}; s.addText(t,{x:x-w/2,y,w,h:o.h||0.3,align:'center',fontSize:o.fs||11,bold:!!o.bold,italic:!!o.it,color:o.color||'000000',fontFace:F,isTextBox:true,margin:0}); }

function panel(px, mode){
  // frame
  s.addShape(pres.ShapeType.rect,{x:px,y:0.45,w:6.0,h:5.05,fill:{color:'FFFFFF'},line:{color:'BFBFBF',width:0.75}});
  const M=[px+3.0,1.15], AP1=[px+1.35,3.0], AP2=[px+4.65,3.0];
  master(...M); ap(...AP1); ap(...AP2);
  // plain STAs
  const S1=[[px+0.75,2.45],[px+0.7,3.7]], S2=[[px+5.3,2.45],[px+5.35,3.7]];
  S1.forEach(p=>{line(p,AP1);sta(...p)}); S2.forEach(p=>{line(p,AP2);sta(...p)});
  const A=[px+2.1,3.65], B=[px+3.9,3.65];
  if(mode==='a'){
    line(A,AP1); line(B,AP2); star(...A,'A'); star(...B,'B');
    // logical LS group around A and B
    s.addShape(pres.ShapeType.ellipse,{x:px+1.55,y:3.2,w:2.9,h:1.25,fill:{type:'none'},line:{color:PUR,width:2,dashType:'dash'}});
    txt('LS group (logical)',px+3.0,4.5,2.6,{color:PUR,bold:true,fs:12});
    // master control to both serving APs
    line([M[0]-0.1,M[1]+0.28],[AP1[0]+0.1,AP1[1]-0.28],{color:BLUE,width:1.5,arrow:true});
    line([M[0]+0.1,M[1]+0.28],[AP2[0]-0.1,AP2[1]-0.28],{color:BLUE,width:1.5,arrow:true});
    txt('slot / power',px+3.0,2.05,1.6,{color:BLUE,it:true,fs:11});
  } else {
    // A leaves AP1 and joins AP2
    const A2=[px+4.2,4.3];
    line(A,AP1,{color:LGREY,dash:'sysDot'}); star(...A,'A',true);
    line(A2,AP2); line(B,AP2); star(...A2,'A'); star(...B,'B');
    line([A[0]+0.2,A[1]+0.05],[A2[0]-0.2,A2[1]-0.05],{color:'E0202A',width:2,dash:'dash',arrow:true});
    txt('re-association',px+3.05,4.35,1.6,{color:'E0202A',it:true,fs:11});
    // LS-serving AP outline
    s.addShape(pres.ShapeType.ellipse,{x:px+3.45,y:2.45,w:2.45,h:2.35,fill:{type:'none'},line:{color:PUR,width:2,dashType:'dash'}});
    txt('LS-serving AP',px+4.7,4.85,2.2,{color:PUR,bold:true,fs:12});
    line([M[0]+0.1,M[1]+0.28],[AP2[0]-0.1,AP2[1]-0.28],{color:BLUE,width:1.5,arrow:true});
    txt('assign',px+4.25,1.95,1.0,{color:BLUE,it:true,fs:11});
  }
}
panel(0.45,'a'); panel(6.88,'b');
txt('(a) Logical grouping (association unchanged)',3.45,5.7,6.0,{fs:14});
txt('(b) Re-association to one AP',9.88,5.7,6.0,{fs:14});
// legend
let lx=3.6, ly=6.55;
sta(lx,ly+0.15); txt('STA',lx+0.5,ly,0.8,{fs:11});
star(lx+1.5,ly+0.15,null); txt('latency-sensitive STA',lx+2.9,ly,2.2,{fs:11});
line([lx+4.5,ly+0.15],[lx+5.1,ly+0.15],{color:PUR,width:2,dash:'dash'}); txt('LS group',lx+5.65,ly,1.0,{fs:11});
pres.writeFile({fileName:'grouping_options.pptx'}).then(()=>console.log('ok'));
