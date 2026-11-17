#!/usr/bin/env python3
"""FINAL198 on FINAL197. Print sheets and Export list: no text is cut.
For every label of the media block the needed number of lines is estimated from the text length, the font size and the width
(Open Sans, conservative), separately for the full and the compact print layout:
  - labels and values get heights that hold all their lines (a wrapped label makes its row taller);
  - each column is re-chained (Y = previous Y + previous height), so a taller row pushes the next ones down, never over them;
  - a value longer than its line budget is shortened with '…' instead of being cut by the label edge;
  - the gallery row is as tall as the worst case of its longest column, and the page holds as many rows as fit.
The request header of the sheet gets larger text (10 / 12 pt) with room for two lines."""
import datetime, math, os, re, shutil, sys
from payaml import App, find
sys.path.insert(0, '.')
from fit_lib import two, line_h, cpl, text_lines, analyse, R, walk
SRC, NEW = 'newV59', 'newV60'
if os.path.exists(NEW): shutil.rmtree(NEW)
shutil.copytree(SRC, NEW)
app = App(NEW)
_rule = app.rule
app.rule = lambda *a: (lambda x: None if x is None else x.replace('\r\n', '\n'))(_rule(*a))
C = 'locPrinting And Coalesce(varCompactPrint, false)'
def setp(scr, ctl, prop, val):
    t = app.rule(scr, ctl, prop)
    if t is None: raise SystemExit(f'! {scr}.{ctl}.{prop} missing')
    if t.strip() != val.strip(): app.set(scr, ctl, prop, val, expect=t)
def iff(c, f): return f'If({C}, {c}, {f})' if c != f else str(f)
def trunc(expr, maxc):
    return f'With(\n    {{t: {expr.strip()}\n    }},\n    If(Len(t) > {maxc}, Left(t, {maxc - 1}) & "…", t)\n)'
TOP_GAP = 2
HDR_LBL_Y, HDR_LBL_H, HDR_VAL_Y = 152, 18, 170
VAL_LS = {'c': 11, 'f': 14}   # value font sizes (compact, full) after FINAL197
report = []
for scr, p, per_page_wish in (('PrintVideoDetailScreen', 'PVD', 1), ('PrintPodcastDetailScreen', 'PPoD', 1), ('PrintPhotoDetailScreen', 'PPD', 2)):
    tp, g, items = analyse(NEW, scr, p)
    by = {i['name']: i for i in items}
    # ---------- request header: bigger text, two lines for the values
    hdr_val_h = 2 * line_h(12) + 2
    for n in tp['Children']:
        nm = n['Name']
        if re.fullmatch(rf'{p}_HdrLbl\d', nm):
            sc, sf = two(R(n)['Size'])
            setp(scr, nm, 'Size', iff(max(sc, 8), max(sf, 10))); setp(scr, nm, 'Height', str(HDR_LBL_H)); setp(scr, nm, 'Y', str(HDR_LBL_Y))
        if re.fullmatch(rf'{p}_HdrVal\d', nm):
            r = R(n); wc, wf = two(r['Width'])
            setp(scr, nm, 'Size', iff(9, 12)); setp(scr, nm, 'Height', str(hdr_val_h)); setp(scr, nm, 'Y', str(HDR_VAL_Y))
            maxc = 2 * min(cpl(12, wf), cpl(9, wc))
            if 'Len(t) >' not in r['Text']: setp(scr, nm, 'Text', trunc(r['Text'], maxc))
    GAL_Y = HDR_VAL_Y + hdr_val_h + 4
    # ---------- media block
    # the compact layout is 70% of the width: its fonts follow the same ratio (FINAL197 had them at about 79%)
    for i in items:
        if i['kind'] in ('cap', 'sec', 'lbl', 'val'):
            if i['kind'] == 'lbl' and i['sf'] > 11: i['sf'] = 11   # field names 11 pt: fewer wrapped names
            if i['kind'] == 'val' and i['sf'] > 13: i['sf'] = 13   # values 13 pt (were 9 before FINAL197)
            sc = max(7, round(i['sf'] * 0.70))
            setp(scr, i['name'], 'Size', iff(sc, i['sf'])); i['sc'] = sc
    cap = by[f'{p}_RowCaption']
    cap_h = line_h(cap['sf'])
    setp(scr, cap['name'], 'Height', str(cap_h))
    TOP = cap_h + TOP_GAP
    LBL = {'c': line_h(8), 'f': line_h(11)}
    vals = [i for i in items if i['kind'] == 'val']
    for v in vals:
        t = v['text']
        v['cls'] = 'short' if ('✅' in t or '"Yes"' in t or re.search(r'Text\(ThisItem\.\w*(Date|On)\b', t)) else 'long' if v['h'] >= 42 else 'normal'
        num = v['name'].split('_Val')[1]
        lab = by.get(f'{p}_Lbl{num}')
        ONE_LINE = ('Season nr.', 'Episode nr.', 'Beluga reference', 'Type of product', 'Language version(s)', 'AI voice-over',
                    'Recording date', 'Filming date', 'Shooting date', 'Podcast visual', 'Episode visual', 'Music used')
        if lab and lab['text'].strip().strip('"') in ONE_LINE: v['cls'] = 'short'
        if lab is None:  # nearest label of the same column
            cands = [l for l in items if l['kind'] == 'lbl' and l['col'] == v['col'] and not l.get('paired')]
            lab = min(cands, key=lambda l: abs(l['y'] - v['y'])) if cands else None
        v['lab'] = lab
        if lab: lab['paired'] = v['name']
        txt = lab['text'].strip().strip('"') if lab else ''
        v['ll'] = {'c': text_lines(txt, lab['sc'], lab['wc']) if lab else 0, 'f': text_lines(txt, lab['sf'], lab['wf']) if lab else 0}
        v['cp'] = {'c': cpl(v['sc'], v['wc']), 'f': cpl(v['sf'], v['wf'])}
        v['lv'] = {'c': line_h(v['sc']), 'f': line_h(v['sf'])}
    secs = [i for i in items if i['kind'] == 'sec']
    for s in secs: s['hh'] = {'c': line_h(s['sc']), 'f': line_h(s['sf'])}
    # column order: by original Y; a value with a literal Y that collides with an earlier block goes after the section above it
    cols = {}
    for c in range(3):
        col = sorted([i for i in items if i['col'] == c and i['kind'] in ('sec', 'val')], key=lambda i: (i['y'], i['kind'] != 'sec'))
        cols[c] = col
    if p == 'PVD':   # Credits (Val7) has a literal Y that overlaps Beluga reference: it belongs under the "Metadata" section
        col = cols[0]; v7 = by['PVD_Val7']; col.remove(v7); col.insert(col.index(by['PVD_Sec6']) + 1, v7)
    def move(num, to_col, after_num, ref_num):
        v, a = by[f'{p}_Val{num}'], by[f'{p}_Val{after_num}']
        cols[v['col']].remove(v); cols[to_col].insert(cols[to_col].index(a) + 1, v); v['col'] = to_col
        for kind in ('Val', 'Lbl'):
            if f'{p}_{kind}{num}' in by:
                for prop in ('X', 'Width'):
                    setp(scr, f'{p}_{kind}{num}', prop, app.rule(scr, f'{p}_{kind}{ref_num}', prop))
    if p == 'PPoD':
        # balance the three columns so a full podcast media file fits on one page:
        # Publication end date next to Publication start date; place, links, tags and FTP path under the episode data
        move('12', 1, '11', '11')
        move('13', 0, '18', '1'); move('14', 0, '13', '1'); move('15', 0, '14', '1'); move('32', 0, '15', '1')
    def rowh(i, k):
        return max(k * i['lv']['f'], i['ll']['f'] * LBL['f'], k * i['lv']['c'], i['ll']['c'] * LBL['c'])
    def colh(col, caps):
        return TOP + sum(i['hh']['f'] if i['kind'] == 'sec' else rowh(i, caps[i['name']]) for i in col) + 6
    # the case name is never shortened; the other long fields give way in this order
    KEEP = ('Contract case',)
    GIVE = ('Attached documents', 'Audio files', 'FTP delivery path', 'Pertinent tags', 'Links', 'Script / shotlist', 'Credits', 'Notes',
            'Case 1 — required documents', 'Summary of the episode', 'Description', 'Photo caption / Short Description')
    def lab_of(i): return ((i['lab'] or {}).get('text', '')).strip().strip('"')
    def prio(i): return GIVE.index(lab_of(i)) if lab_of(i) in GIVE else len(GIVE)
    budget_bottom = 744 - 2        # footer top - gap ("Continued on page" now sits on the footer line, right-aligned)
    chosen = None
    for per_page in ([per_page_wish] + ([1] if per_page_wish > 1 else [])):
        budget = (budget_bottom - GAL_Y) // per_page
        caps = {i['name']: {'short': 1, 'normal': 2, 'long': 4}[i['cls']] for i in vals}
        ok = True
        for c, col in cols.items():
            # shrink the longest fields of this column first (long 4 -> 2, then names 2 -> 1) until the column fits
            order = [('long', 3), ('long', 2), ('normal', 1)]
            for cls, k in order:
                for i in sorted([i for i in col if i['kind'] == 'val' and i['cls'] == cls and lab_of(i) not in KEEP], key=lambda i: (prio(i), -caps[i['name']])):
                    if colh(col, caps) <= budget: break
                    caps[i['name']] = min(caps[i['name']], k)
            if colh(col, caps) > budget: ok = False
        if ok:
            TS = max(colh(col, caps) for col in cols.values())
            chosen = (per_page, caps, TS, budget); break
    assert chosen, scr
    per_page, caps, TS, budget = chosen
    summary = {}
    for i in vals: summary.setdefault(i['cls'], {}).setdefault(caps[i['name']], []).append((i['lab'] or {}).get('text', i['name']).strip('"'))
    report.append((scr, per_page, TS, budget, summary))
    # write the chains, heights and truncation
    for c, col in cols.items():
        prev = None
        for i in col:
            ynew = str(TOP) if prev is None else f'{prev}.Y + If({prev}.Visible, {prev}.Height, 0)'
            setp(scr, i['name'], 'Y', ynew)
            if i['kind'] == 'sec':
                setp(scr, i['name'], 'Height', iff(i['hh']['c'], i['hh']['f']))
            else:
                k = caps[i['name']]
                maxc = k * min(i['cp']['c'], i['cp']['f'])
                r = R(find(tp, i['name']))
                body = r['Text']
                yes_no_date = '✅' in body or '"Yes"' in body or re.search(r'Text\(ThisItem\.\w*(Date|On)\b', body)
                if 'Len(t) >' not in body and not yes_no_date:
                    setp(scr, i['name'], 'Text', trunc(body, maxc))
                h = (f'// as many lines as the text needs (up to {k}), and never less than its label\n'
                     f'With(\n    {{c: {C}}},\n    Max(\n        If(c, {i["lv"]["c"]}, {i["lv"]["f"]}) * Max(1, Min({k}, RoundUp(Len(Self.Text) / If(c, {i["cp"]["c"]}, {i["cp"]["f"]}), 0))),\n'
                     f'        If(c, {i["ll"]["c"] * LBL["c"]}, {i["ll"]["f"] * LBL["f"]})\n    )\n)')
                setp(scr, i['name'], 'Height', h)
                setp(scr, i['name'], 'VerticalAlign', 'VerticalAlign.Top') if 'VerticalAlign' in r else None
                if i['lab']:
                    setp(scr, i['lab']['name'], 'Y', f'{i["name"]}.Y')
                    setp(scr, i['lab']['name'], 'Height', f'{i["name"]}.Height')
                    lr = R(find(tp, i['lab']['name']))
                    if 'VerticalAlign' in lr: setp(scr, i['lab']['name'], 'VerticalAlign', 'VerticalAlign.Top')
            prev = i['name']
    # labels without a value keep their place but get a two-line height
    for l in items:
        if l['kind'] == 'lbl' and not l.get('paired'): print('  unpaired label', l['name'])
    # gallery geometry
    old_k = 1 if p in ('PVD', 'PPoD') else 2
    setp(scr, f'{p}_Gallery', 'Y', str(GAL_Y))
    setp(scr, f'{p}_Gallery', 'TemplateSize', str(TS))
    setp(scr, f'{p}_RowRule', 'Y', str(TS - 1)); setp(scr, f'{p}_RowRule', 'Height', '1')
    setp(scr, f'{p}_Gallery', 'Height', f'// the rows of this page only: a row is never cut by the page edge\n{TS} * Min({per_page}, Max(0, CountRows(colPrintReqMedia) - (Coalesce(locPage, 1) - 1) * {per_page}))')
    gi = app.rule(scr, f'{p}_Gallery', 'Items')
    setp(scr, f'{p}_Gallery', 'Items', gi.replace(f'- 1) * {old_k})), {old_k})', f'- 1) * {per_page})), {per_page})'))
    if per_page != old_k:
        for cn in walk(tp):
            for x in list(cn['Rules']):
                if f'CountRows(colPrintReqMedia) / {old_k}' in x['InvariantScript'] and x['Property'] != 'OnVisible':
                    t = app.rule(scr, cn['Name'], x['Property'])
                    app.set(scr, cn['Name'], x['Property'], t.replace(f'CountRows(colPrintReqMedia) / {old_k}', f'CountRows(colPrintReqMedia) / {per_page}'), expect=t)
    for nm in (f'{p}_More', f'{p}_Footer'):
        setp(scr, nm, 'Size', iff(8, 10)); setp(scr, nm, 'Height', '20')
    setp(scr, f'{p}_More', 'Y', '744')
    mr = R(find(tp, f'{p}_More'))
    if 'Align' in mr: setp(scr, f'{p}_More', 'Align', 'Align.Right')
    else: raise SystemExit('! More has no Align rule')
# ---------- Export list: titles / DG / assignee shortened to the two lines the row can show
HP = 'HomePrintScreen'
hp = app.doc(HP)['TopParent']
for nm, w in (('HP_RowDescription', 256), ('HP_RowDG', 170), ('HP_RowDate_1', 280)):
    t = app.rule(HP, nm, 'Text')
    if 'Len(t) >' not in t: setp(HP, nm, 'Text', trunc(t, 2 * cpl(13, w)))
gy = app.rule(HP, 'HP_Gallery', 'Y')
for nm in ('HP_ThRequest', 'HP_ThDescription', 'HP_ThDG', 'HP_ThArchives', 'HP_ThStatus', 'HP_ThSubmitted', 'HP_ThDescription_1'):
    r = R(find(hp, nm)); w = int(r['Width'])
    if text_lines(r['Text'].strip('"'), 12, w) > 1: setp(HP, nm, 'Size', '11')   # a header that would wrap in 12 pt stays at 11
app.save()
h = open(f'{NEW}/Header.json', encoding='utf-8').read()
open(f'{NEW}/Header.json', 'w', encoding='utf-8', newline='').write(
    re.sub(r'"LastSavedDateTimeUTC":"[^"]+"', '"LastSavedDateTimeUTC":"' + datetime.datetime.utcnow().strftime('%m/%d/%Y %H:%M:%S') + '"', h))
for r in report:
    print('REPORT', r[0], 'per page', r[1], 'row', r[2], 'budget', r[3])
    for cls, d in r[4].items():
        for k, names in sorted(d.items()): print('    ', cls, k, 'lines:', ', '.join(names))
print('HP_Gallery Y', gy)
print('FINAL198 built')
