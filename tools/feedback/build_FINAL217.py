#!/usr/bin/env python3
"""FINAL217 on FINAL216.
A. Long texts:
   - form: Description (Info, Photo/Video), Description of the podcast and Photo caption limited to 500 characters, with a counter
     "(n / 500)" on the label from 400 characters;
   - PDF (2 media per page kept): Description (Video, Photo), Photo caption, Description of the podcast and Summary of the episode
     leave the columns and are shown in full-width rows under the three columns, up to 2 lines each ('…' after); the rest of the
     block is refitted (field names 9 pt, values 10 pt in the PDF). The screen sheet is unchanged.
B. Modern date pickers show the date as dd-mm-yyyy: a label under each picker shows Text(SelectedDate, "dd-mm-yyyy") (or a grey
   "dd-mm-yyyy" when empty) and carries the fill and the amber "mandatory" border; the picker itself is transparent on top
   (one click opens the calendar and picks the date)."""
import copy, datetime, glob, json, os, re, shutil, sys
sys.path.insert(0, '.')
from payaml import App, find, block_span
from hp_common import Builder
from fit_lib import line_h, cpl
from fit_plan import plan, fit, lab_of
SRC, NEW = 'newV78', 'newV79'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
import hp_common; hp_common.NEW = NEW
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop); assert t is not None, (scr, ctl, prop)
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
ALL = 'Coalesce(locAllPages, false)'
BLANK = 'Coalesce(ThisItem.PdfBlank, false)'
# ---------------- A1. form limits + counters
CNT = lambda var: f' & If(Len(Coalesce({var}, "")) >= 400, "  (" & Len(Coalesce({var}, "")) & " / 500)", "")'
for scr, box, lbl, var, base in (('ChildInfoScreen', 'CI_Description', 'CI_LblDescription', 'varChildDescription1', 'If(varChildMediaType = "Photo", "Description *", "Description")'),
                                  ('ChildInfoScreen', 'CI_PodcastDesc', 'CI_LblPodcastDesc', 'varChildDescription1', '"Description of the podcast *"'),
                                  ('ChildMetaScreen', 'CM_Caption', 'CM_LblCaptions', 'varChildPhotoCaption', '"Photo caption/Short Description *"')):
    setp(scr, box, 'MaxLength', '500')
    assert app.rule(scr, lbl, 'Text').strip() == base, (lbl, app.rule(scr, lbl, 'Text'))
    setp(scr, lbl, 'Text', f'({base}){CNT(var)}')
# ---------------- A2. PDF: full-width long texts, refit
LONG = {'PrintVideoDetailScreen': ('PVD', ['PVD_Val2']), 'PrintPodcastDetailScreen': ('PPoD', ['PPoD_Val4']),
        'PrintPhotoDetailScreen': ('PPD', ['PPD_Val2', 'PPD_Val8'])}
LBL, VAL, SEC, CAP = 9, 10, 11, 13
ROW, H_H = 448, 56
FW_X, FW_W = 194, 1096
SIZE_RE = re.compile(r'^If\(Coalesce\(locAllPages, false\), \d+, (\d+)\)$')
H_RE = re.compile(r'If\(c, \d+, (\d+)\) \* Max\(1, Min\(If\(c, \d+, (\d+)\), RoundUp\(Len\(Self\.Text\) / If\(c, \d+, (\d+)\), 0\)\)\),\s*If\(c, \d+, (\d+)\)', re.S)
N_RE = re.compile(r', n: If\(Coalesce\(locAllPages, false\), \d+, (\d+)\)\}')
report = []
for scr, (p, longs) in LONG.items():
    P = plan('newV59', scr, p)
    for c in P['cols']: P['cols'][c] = [i for i in P['cols'][c] if i['name'] not in longs]
    longv = [v for v in P['vals'] if v['name'] in longs]
    P['vals'] = [v for v in P['vals'] if v['name'] not in longs]
    n_rows = 2 if p != 'PVD' else 1
    full = n_rows * (2 * line_h(VAL) + 2) + 4
    ok, caps, h, m, sech = fit(P, LBL, VAL, ROW - H_H - 2 - full, line_h(CAP) + 2, SEC)
    assert ok, scr
    report.append((scr, h, full, {lab_of(i): caps[i['name']] for i in P['vals'] if caps[i['name']] < {'short': 1, 'normal': 2, 'long': 4}[i['cls']]}))
    def size(nm, v):
        t = app.rule(scr, nm, 'Size'); mm = SIZE_RE.match(t.strip()); assert mm, (nm, t)
        setp(scr, nm, 'Size', f'If({ALL}, {v}, {mm.group(1)})')
    size(f'{p}_RowCaption', CAP); setp(scr, f'{p}_RowCaption', 'Height', f'If({ALL}, {line_h(CAP)}, {line_h(17)})')
    for i in P['items']:
        nm = i['name']
        if i['kind'] == 'sec':
            size(nm, SEC); setp(scr, nm, 'Height', f'If({ALL}, {sech}, {line_h(14)})')
        elif i['kind'] == 'lbl':
            size(nm, LBL)
        elif i['kind'] == 'val' and nm not in longs:
            size(nm, VAL)
            hf = app.rule(scr, nm, 'Height'); hm = H_RE.search(hf); assert hm, nm
            lvF, kF, cpF, llF = hm.groups()
            mm_ = m[nm]; kP = caps[nm]; cpP = mm_['cp']; lvP = mm_['lv']; llP = mm_['ll'] * mm_['LL']
            setp(scr, nm, 'Height', (f'// lines the text needs (screen up to {kF}, PDF up to {kP}), never less than its label\n'
                                    f'With(\n    {{c: {ALL}}},\n    Max(\n        If(c, {lvP}, {lvF}) * Max(1, Min(If(c, {kP}, {kF}), RoundUp(Len(Self.Text) / If(c, {cpP}, {cpF}), 0))),\n'
                                    f'        If(c, {llP}, {llF})\n    )\n)'))
            t = app.rule(scr, nm, 'Text'); nm_ = N_RE.search(t)
            if nm_: setp(scr, nm, 'Text', t[:nm_.start()] + f', n: If({ALL}, {kP * cpP}, {nm_.group(1)})}}' + t[nm_.end():])
    # long fields: hidden in the PDF columns (their chain contribution becomes 0)
    for v in longv:
        vis = app.rule(scr, v['name'], 'Visible')
        setp(scr, v['name'], 'Visible', f'Not({ALL}) And ({vis.strip()})')
    # bottom of the three columns (PDF)
    bottoms = [f'{col[-1]["name"]}.Y + If({col[-1]["name"]}.Visible, {col[-1]["name"]}.Height, 0)' for col in P['cols'].values()]
    TOPFW = f'Max({", ".join(bottoms)}) + 4'
    cpF = cpl(VAL, FW_W); lv = line_h(VAL)
    rows = []
    if p == 'PPoD':
        rows.append(('PPoD_FwDesc', 'Description of the podcast', 'Trim(PlainText(ThisItem.Description))', 'PPoD_Val4', 'PPoD_Lbl4'))
        rows.append(('PPoD_FwSummary', 'Summary of the episode', 'Trim(Coalesce(ThisItem.EpisodeSummary, ""))', 'PPoD_Val4', 'PPoD_Lbl4'))
    elif p == 'PVD':
        rows.append(('PVD_FwDesc', 'Description', 'Trim(PlainText(ThisItem.Description))', 'PVD_Val2', 'PVD_Lbl2'))
    else:
        rows.append(('PPD_FwDesc', 'Description', 'Trim(PlainText(ThisItem.Description))', 'PPD_Val2', 'PPD_Lbl2'))
        rows.append(('PPD_FwCaption', 'Photo caption / Short Description', 'Trim(PlainText(ThisItem.PhotoCaption))', 'PPD_Val8', 'PPD_Lbl8'))
    b = Builder(app, scr)
    prev = None
    for nm, label, expr, dv, dl in rows:
        y = TOPFW if prev is None else f'{prev}.Y + If({prev}.Visible, {prev}.Height, 0) + 2'
        vis = f'{ALL} And Not({BLANK}) And Not(IsBlank({expr}))'
        b.clone(nm, scr, dv, {'X': str(FW_X), 'Width': str(FW_W), 'Y': y, 'Visible': vis, 'Size': str(VAL),
                'Text': f'With(\n    {{t: {expr}, n: {2 * cpF}}},\n    If(Len(t) > n, Left(t, n - 1) & "…", t)\n)',
                'Height': f'// full-width row of the PDF: up to 2 lines\n{lv} * Max(1, Min(2, RoundUp(Len(Self.Text) / {cpF}, 0)))',
                'Color': 'RGBA(30, 34, 44, 1)'}, parent=f'{p}_Gallery')
        b.clone(nm + 'Lbl', scr, dl, {'X': '12', 'Width': '180', 'Y': f'{nm}.Y', 'Height': f'{nm}.Height', 'Visible': f'{nm}.Visible',
                'Size': str(LBL), 'Text': f'"{label}"'}, parent=f'{p}_Gallery')
        prev = nm
    b.save()
# ---------------- B. dd-mm-yyyy labels under the modern date pickers
pickers = []
for f in glob.glob(f'{NEW}/Controls/*.json'):
    tp0 = json.load(open(f, encoding='utf-8-sig'))['TopParent']; scr = tp0['Name']
    def walk(n, par):
        if n['Template']['Name'] == 'modernDatePicker': pickers.append((scr, n['Name'], par))
        for c in n.get('Children', []): walk(c, n['Name'])
    walk(tp0, None)
DONOR_LBL = {'CM_Gallery': ('ChildMetaScreen', 'CM_LblShootDate'), 'CI_Gallery': ('ChildInfoScreen', 'CI_LblCaptureDate'),
             'RequestManagementScreen': None, 'HomePrintScreen': ('HomePrintScreen', 'HP_LblDates')}
def first_free_label(scr):
    tp = app.doc(scr)['TopParent']
    grouped = {k for g in tp['Children'] if g.get('IsGroupControl') for k in (g.get('GroupedControlsKey') or [])}
    for c in tp['Children']:
        if c['Template']['Name'] == 'label' and c['Name'] not in grouped: return (scr, c['Name'])
for scr, nm, par in sorted(pickers):
    donor = DONOR_LBL.get(par) or first_free_label(scr)
    r = {k: app.rule(scr, nm, k) for k in ('X', 'Y', 'Width', 'Height', 'Visible', 'Fill', 'BorderColor', 'BorderThickness', 'Size', 'Font', 'Color', 'ZIndex')}
    host = None if par == scr else par
    b = Builder(app, scr)
    ln = nm + '_Txt'
    b.clone(ln, donor[0], donor[1], {
        'X': r['X'], 'Y': r['Y'], 'Width': r['Width'], 'Height': r['Height'], 'Visible': r['Visible'] or 'true',
        'Text': f'If(IsBlank({nm}.SelectedDate), "dd-mm-yyyy", Text({nm}.SelectedDate, "dd-mm-yyyy"))',
        'Color': f'If(IsBlank({nm}.SelectedDate), RGBA(150, 155, 165, 1), RGBA(0, 0, 0, 1))',
        'Fill': r['Fill'] or 'RGBA(255, 255, 255, 1)', 'BorderColor': r['BorderColor'] or 'RGBA(0, 18, 107, 1)',
        'BorderThickness': r['BorderThickness'] or '1', 'Size': r['Size'] or '11', 'Font': r['Font'] or "Font.'Open Sans'",
        'FontWeight': 'FontWeight.Normal', 'PaddingLeft': '12', 'VerticalAlign': 'VerticalAlign.Middle', 'Align': 'Align.Left',
        'BorderStyle': 'BorderStyle.Solid', 'RadiusTopLeft': '5', 'RadiusTopRight': '5', 'RadiusBottomLeft': '5', 'RadiusBottomRight': '5'} if False else {
        'X': r['X'], 'Y': r['Y'], 'Width': r['Width'], 'Height': r['Height'], 'Visible': r['Visible'] or 'true',
        'Text': f'If(IsBlank({nm}.SelectedDate), "dd-mm-yyyy", Text({nm}.SelectedDate, "dd-mm-yyyy"))',
        'Color': f'If(IsBlank({nm}.SelectedDate), RGBA(150, 155, 165, 1), RGBA(0, 0, 0, 1))',
        'Fill': r['Fill'] or 'RGBA(255, 255, 255, 1)', 'BorderColor': r['BorderColor'] or 'RGBA(0, 18, 107, 1)',
        'BorderThickness': r['BorderThickness'] or '1', 'Size': r['Size'] or '11', 'Font': r['Font'] or "Font.'Open Sans'",
        'FontWeight': 'FontWeight.Normal', 'PaddingLeft': '12', 'VerticalAlign': 'VerticalAlign.Middle', 'Align': 'Align.Left',
        'BorderStyle': 'BorderStyle.Solid'}, parent=host)
    b.save()
    # the picker becomes transparent on top of its label
    for prop, v in (('Fill', 'RGBA(0, 0, 0, 0)'), ('Color', 'RGBA(0, 0, 0, 0)'), ('BorderColor', 'RGBA(0, 0, 0, 0)'), ('BorderThickness', '0'), ('Placeholder', '" "')):
        setp(scr, nm, prop, v)
    # z-order: label just under the picker (JSON ZIndex and YAML order)
    tp = app.doc(scr)['TopParent']
    hostn = tp if host is None else find(tp, host)
    kids = hostn['Children']
    pick = next(c for c in kids if c['Name'] == nm); lab = next(c for c in kids if c['Name'] == ln)
    zr = lambda c: [x for x in c['Rules'] if x['Property'] == 'ZIndex'][0]
    pz = int(zr(pick)['InvariantScript'])
    for c in kids:
        if c is lab: continue
        z = int(zr(c)['InvariantScript']) if [x for x in c['Rules'] if x['Property'] == 'ZIndex'] else 0
        if z >= pz: zr(c)['InvariantScript'] = str(z + 1)
    zr(lab)['InvariantScript'] = str(pz)
    kids.remove(lab); kids.insert(kids.index(pick), lab)
    app.save()
    yf = f'{NEW}/Src/{scr}.pa.yaml'; L = open(yf, encoding='utf-8', newline='').read().replace('\r\n', '\n').split('\n')
    ls, le = block_span(L, ln); blk = L[ls:le]; del L[ls:le]
    ps, pe = block_span(L, nm); L[ps:ps] = blk
    open(yf, 'w', encoding='utf-8', newline='').write('\n'.join(L))
# control counts
p_ = f'{NEW}/Properties.json'
raw = open(p_, 'rb').read(); bom = raw.startswith(b'\xef\xbb\xbf'); t = raw.decode('utf-8-sig')
added = 2 * sum(2 if p != 'PVD' else 1 for _, (p, _) in LONG.items()) + len(pickers)
t = re.sub(r'("label"\s*:\s*)(\d+)', lambda mm: mm.group(1) + str(int(mm.group(2)) + added), t, count=1)
open(p_, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(t)
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
for r_ in report: print('REPORT', r_)
print('pickers', len(pickers)); print('FINAL217 built')
