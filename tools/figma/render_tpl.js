const D = __DATA__;
const START = __START__;
const page = figma.root.children.find(p => p.name === 'Screens'); await figma.setCurrentPageAsync(page);
if (START === 0) for (const c of [...page.children]) c.remove();
for (const st of ['Regular','SemiBold','Bold']) await figma.loadFontAsync({family:'Open Sans',style:st});
const V = {}; for (const v of await figma.variables.getLocalVariablesAsync('COLOR')) V[v.name] = v;
const TS = {}; for (const s of await figma.getLocalTextStylesAsync()) TS[s.name] = s;
const [btnSet, inpSet, chkSet] = await Promise.all(['5:12','5:21','5:29'].map(id => figma.getNodeByIdAsync(id)));
const TOK = {'0,18,107':'brand/navy','0,13,75':'brand/navy-dark','56,96,178':'brand/blue','136,160,209':'brand/blue-mid','186,202,226':'brand/blue-light','215,223,240':'brand/blue-soft','230,236,245':'brand/blue-tint','99,96,178':'brand/purple','247,248,250':'surface/page','244,245,248':'surface/subtle','240,242,246':'surface/table-header','255,255,255':'surface/white','0,0,0':'surface/black','220,224,230':'border/default','230,232,238':'border/soft','30,34,44':'text/primary','60,66,80':'text/secondary','96,104,120':'text/muted','150,155,165':'text/placeholder','140,148,160':'text/disabled','22,128,80':'status/success','255,204,0':'status/warning','193,40,40':'status/danger','168,0,0':'status/danger-dark','0,100,0':'status/success-dark','211,211,211':'badge/draft','189,183,107':'badge/pending','106,90,205':'badge/processing','184,134,11':'badge/partially-approved','240,128,128':'badge/rejected','128,128,128':'badge/published'};
const SN = {'22B':'Heading/22 Bold','16B':'Title/16 Bold','14S':'Title/14 Semibold','13S':'Body/13 Semibold','13R':'Body/13 Regular','12S':'Body/12 Semibold','12R':'Body/12 Regular','11S':'Body/11 Semibold','11R':'Body/11 Regular','10S':'Label/10 Semibold','10R':'Label/10 Regular','9S':'Caption/9 Semibold','9R':'Caption/9 Regular'};
let bound = 0, raw = 0, inst = 0, nodes = 0;
function paint(c) {
  const key = c[0]+','+c[1]+','+c[2]; const tk = TOK[key];
  let p = {type:'SOLID', color:{r:c[0]/255, g:c[1]/255, b:c[2]/255}};
  if (tk && V[tk] && c[3] >= 1) { p = figma.variables.setBoundVariableForPaint(p, 'color', V[tk]); bound++; } else raw++;
  if (c[3] < 1) p = {type:'SOLID', color:{r:c[0]/255, g:c[1]/255, b:c[2]/255}, opacity: c[3]};
  return p;
}
function font(t, size, wt) {
  const sn = SN[size+wt];
  if (sn && TS[sn]) t.textStyleId = TS[sn].id;
  else { t.fontName = {family:'Open Sans', style: wt==='B'?'Bold':wt==='S'?'SemiBold':'Regular'}; t.fontSize = size; }
}
function mkText(parent, str, x, y, w, h, size, wt, al, va, col) {
  const t = figma.createText(); font(t, size, wt); t.characters = str; t.textAutoResize = 'NONE'; t.resize(Math.max(w,1), Math.max(h,1));
  t.textAlignHorizontal = al==='C'?'CENTER':al==='R'?'RIGHT':'LEFT'; t.textAlignVertical = va==='T'?'TOP':va==='B'?'BOTTOM':'CENTER';
  if (col) t.fills = [paint(col)]; parent.appendChild(t); t.x = x; t.y = y; nodes++; return t;
}
function mkRect(parent, x, y, w, h, fill, stroke, sw, rad, name) {
  const r = figma.createRectangle(); r.resize(Math.max(w,1), Math.max(h,1)); r.fills = fill ? [paint(fill)] : [];
  if (stroke && sw > 0) { r.strokes = [paint(stroke)]; r.strokeWeight = sw; }
  if (rad) r.cornerRadius = Math.min(rad, Math.min(w,h)/2);
  if (name) r.name = name; parent.appendChild(r); r.x = x; r.y = y; nodes++; return r;
}
function prop(i, pre) { return Object.keys(i.componentProperties).find(k => k.startsWith(pre)); }
const out = [];
for (let j = 0; j < D.length; j++) {
  const d = D[j], P = d.p, i = START + j;
  const fr = figma.createFrame(); fr.name = d.n + ' / ' + d.v; fr.resize(1366, 768); fr.clipsContent = true;
  fr.fills = [paint(P[d.f])]; page.appendChild(fr); fr.x = (i % 3) * 1500; fr.y = Math.floor(i / 3) * 900 + 70;
  const cap = figma.createText(); font(cap, 16, 'B'); cap.characters = d.n + '  |  ' + d.v; cap.fills = [paint([0,18,107,1])]; page.appendChild(cap); cap.x = fr.x; cap.y = fr.y - 44;
  let par = fr, gx = 0, gy = 0;
  for (const o of d.o) {
    const k = o[0], ing = o[o.length-1] === 1;
    if (k === 'g') {
      const g = figma.createFrame(); g.name = 'gallery'; g.resize(Math.max(o[3],1), Math.max(o[4],1)); g.fills = []; g.clipsContent = true; fr.appendChild(g); g.x = o[1]; g.y = o[2]; gx = o[1]; gy = o[2]; par = g; nodes++; continue;
    }
    if (!ing) { par = fr; gx = 0; gy = 0; }
    const x = o[1] - gx, y = o[2] - gy, w = o[3], h = o[4];
    if (x > 1366 || y > 768 + 2000) continue;
    const C = n => n >= 0 ? P[n] : null;
    if (k === 'r') { mkRect(par, x, y, w, h, C(o[5]), C(o[6]), o[7], o[8]); }
    else if (k === 'l') { if (o[5] >= 0) mkRect(par, x, y, w, h, C(o[5]), null, 0, 0); if (o[7]) mkText(par, o[7], x, y, w, h, o[8], o[9], o[10], o[11], C(o[6])); }
    else if (k === 'b') {
      if (!o[10]) { mkRect(par, x, y, w, h, C(o[5]), C(o[7]), o[8], o[9]); continue; }
      const fc = C(o[5]); const kind = !fc || fc[3] === 0 ? 'Ghost' : (fc[0]===56 && fc[1]===96 && fc[2]===178) ? 'Primary' : (fc[0]===193 && fc[1]===40) ? 'Danger' : 'Secondary';
      const it = btnSet.children.find(c => c.name === 'Kind=' + kind).createInstance(); par.appendChild(it); it.x = x; it.y = y; it.resize(Math.max(w,8), Math.max(h,8));
      it.setProperties({[prop(it,'Label')]: o[10]});
      const tn = it.findOne(n => n.type === 'TEXT'); font(tn, o[11], o[12]); if (o[6] >= 0) tn.fills = [paint(P[o[6]])];
      it.fills = fc && fc[3] > 0 ? [paint(fc)] : []; if (o[7] >= 0 && o[8] > 0) { it.strokes = [paint(P[o[7]])]; it.strokeWeight = o[8]; } else it.strokes = [];
      it.cornerRadius = Math.min(o[9], Math.min(w,h)/2); inst++; nodes++;
    }
    else if (k === 'i') {
      const it = inpSet.children.find(c => c.name === 'Kind=' + ['Text','Combo','Date'][o[5]]).createInstance(); par.appendChild(it); it.x = x; it.y = y; it.resize(Math.max(w,24), Math.max(h,20));
      it.setProperties({[prop(it,'Text')]: o[6] || ' '}); inst++; nodes++;
    }
    else if (k === 'c') {
      const it = chkSet.children.find(c => c.name === 'Checked=false').createInstance(); par.appendChild(it); it.x = x; it.y = y; it.resize(Math.max(w,24), Math.max(h,16));
      it.setProperties({[prop(it,'Label')]: o[5] || ' '}); inst++; nodes++;
    }
    else if (k === 'm') { const r = mkRect(par, x, y, w, h, [230,232,238,0.55], [150,155,165,1], 1, 3, 'image'); mkText(par, o[5], x, y, w, h, 9, 'R', 'C', 'M', [96,104,120,1]); }
    else if (k === 'o') { const e = figma.createEllipse(); e.resize(Math.max(Math.min(w,h),10), Math.max(Math.min(w,h),10)); e.fills = []; e.strokes = [paint(C(o[5]) || [96,104,120,1])]; e.strokeWeight = 1.5; e.name = 'icon'; par.appendChild(e); e.x = x; e.y = y; nodes++; mkText(par, o[6], x, y, Math.min(w,h), Math.min(w,h), 9, 'S', 'C', 'M', C(o[5]) || [96,104,120,1]); }
  }
  out.push({id: fr.id, name: fr.name, children: fr.children.length});
}
return {frames: out, bound, raw, inst, nodes};
