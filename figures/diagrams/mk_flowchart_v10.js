const pptxgen = require('pptxgenjs');
const pres = new pptxgen();
pres.defineLayout({ name: 'FLOW', width: 10, height: 9.1 });
pres.layout = 'FLOW';
const s = pres.addSlide();
const NAVY = '1F3864', INK = '222222', FONT = 'Times New Roman';

function box(x, y, w, h, title, sub) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: 'FFFFFF' }, line: { color: NAVY, width: 1.5 } });
  const runs = [{ text: title, options: { bold: true, fontSize: 11.5, breakLine: !!sub } }];
  if (sub) runs.push({ text: sub, options: { fontSize: 9.5 } });
  s.addText(runs, { x, y, w, h, fontFace: FONT, color: INK, align: 'center', valign: 'middle', margin: 2, isTextBox: true });
}
function diamond(cx, cy, w, h, text) {
  s.addShape(pres.shapes.DIAMOND, { x: cx - w / 2, y: cy - h / 2, w, h, fill: { color: 'FFFFFF' }, line: { color: NAVY, width: 1.5 } });
  s.addText(text, { x: cx - w / 2 + 0.35, y: cy - h / 2, w: w - 0.7, h, fontFace: FONT, fontSize: 11, bold: true, color: INK, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
}
function seg(x1, y1, x2, y2, arrow) {
  const o = { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), line: { color: INK, width: 1.25 } };
  if (arrow) o.line.endArrowType = 'triangle';
  if (x2 < x1) o.flipH = true;
  if (y2 < y1) o.flipV = true;
  s.addShape(pres.shapes.LINE, o);
}
function lab(x, y, t, w = 0.6) {
  s.addText(t, { x, y, w, h: 0.25, fontFace: FONT, fontSize: 10.5, bold: true, color: INK, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
}

// phase bands
s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 0.3, w: 9.4, h: 2.05, fill: { color: 'E8E8E8' }, line: { color: '7F7F7F', width: 1 } });
s.addText('Initialization', { x: 0.45, y: 0.38, w: 2.5, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: '404040', margin: 0, isTextBox: true });
s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 2.45, w: 9.4, h: 6.35, fill: { color: 'DDE4EE' }, line: { color: '7F7F7F', width: 1 } });
s.addText('Per-TXOP', { x: 0.45, y: 2.53, w: 2.5, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: NAVY, margin: 0, isTextBox: true });

const CX = 5.0, BW = 3.6, BX = CX - BW / 2;
box(BX, 0.5, BW, 0.72, 'Network State Collection', 'Master AP collects inter-AP RSSI and traffic demand');
seg(CX, 1.22, CX, 1.48, true);
box(BX, 1.48, BW, 0.66, 'RSSI-based BSS Grouping', 'BSSs are grouped by RSSI proximity');
seg(CX, 2.14, CX, 2.7, true);

box(BX, 2.7, BW, 0.72, 'Traffic State Observation', 'Master AP collects traffic state of each group via ICF/ICR');
seg(CX, 3.42, CX, 3.62, true);

diamond(CX, 4.1, 3.3, 0.96, 'Latency-sensitive traffic\nin this TXOP?');
seg(CX + 1.65, 4.1, 7.35, 4.1, true); lab(6.7, 3.83, 'No');
box(7.35, 3.74, 2.2, 0.72, 'Coordinated Spatial Reuse', 'All groups transmit concurrently');
seg(CX, 4.58, CX, 4.78, true); lab(CX + 0.05, 4.55, 'Yes', 0.5);

diamond(CX, 5.26, 3.3, 0.96, 'Latency-sensitive traffic\nconcentrated in one group?');
seg(CX - 1.65, 5.26, 2.35, 5.26, false); seg(2.35, 5.26, 2.35, 6.0, true); lab(2.9, 4.99, 'No');
seg(CX + 1.65, 5.26, 7.35, 5.26, false); seg(7.35, 5.26, 7.35, 6.0, true); lab(6.8, 4.99, 'Yes');

box(0.55, 6.0, 3.6, 1.02, 'Latency-sensitive traffic\ndistributed across groups',
    'Groups with latency-sensitive traffic transmit first (priority slots),\nthen all groups transmit concurrently (Co-SR)');
box(5.55, 6.0, 3.6, 1.02, 'Latency-sensitive traffic\nconcentrated in one group',
    'The group transmits in turn (Co-TDMA),\nwhile the other groups transmit concurrently (Co-SR)');

// merge line
seg(2.35, 7.02, 2.35, 7.22, false); seg(7.35, 7.02, 7.35, 7.22, false);
seg(9.3, 4.46, 9.3, 7.22, false);           // from Co-SR box down
seg(2.35, 7.22, 9.3, 7.22, false);
seg(CX, 7.22, CX, 7.42, true);

box(BX, 7.42, BW, 0.72, 'Resource Allocation using ML', 'Master AP determines slot durations and group transmit power');
seg(CX, 8.14, CX, 8.3, true);
box(BX, 8.3, BW, 0.42, 'Coordinated Transmission');

// loop back: next TXOP
seg(CX + BW / 2, 8.51, 9.62, 8.51, false); seg(9.62, 8.51, 9.62, 3.06, false); seg(9.62, 3.06, CX + BW / 2, 3.06, true);
s.addText('Next TXOP', { x: 9.17, y: 6.05, w: 1.2, h: 0.3, fontFace: FONT, fontSize: 10, bold: true, color: INK, align: 'center', valign: 'middle', margin: 0, rotate: 270, isTextBox: true });

pres.writeFile({ fileName: 'flow9/flowchart_v10.pptx' }).then(() => console.log('ok'));
