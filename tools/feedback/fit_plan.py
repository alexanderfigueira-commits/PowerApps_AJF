"""Column plan of the print sheets (order, classes, label pairing) and the per-field line caps for a given size / budget.
Same rules as build_V60 (FINAL198/201)."""
import math, re
from fit_lib import analyse, line_h, cpl, text_lines
KEEP = ('Contract case',)
GIVE = ('Attached documents', 'Audio files', 'FTP delivery path', 'Pertinent tags', 'Links', 'Script / shotlist', 'Credits', 'Notes',
        'Case 1 — required documents', 'Summary of the episode', 'Description', 'Photo caption / Short Description')
ONE_LINE = ('Season nr.', 'Episode nr.', 'Beluga reference', 'Type of product', 'Language version(s)', 'AI voice-over',
            'Recording date', 'Filming date', 'Shooting date', 'Podcast visual', 'Episode visual', 'Music used')
def plan(tree, scr, p):
    tp, g, items = analyse(tree, scr, p)
    by = {i['name']: i for i in items}
    vals = [i for i in items if i['kind'] == 'val']
    for v in vals:
        t = v['text']
        v['cls'] = 'short' if ('✅' in t or '"Yes"' in t or re.search(r'Text\(ThisItem\.\w*(Date|On)\b', t)) else 'long' if v['h'] >= 42 else 'normal'
        num = v['name'].split('_Val')[1]
        lab = by.get(f'{p}_Lbl{num}')
        if lab is None:
            cands = [l for l in items if l['kind'] == 'lbl' and l['col'] == v['col'] and not l.get('paired')]
            lab = min(cands, key=lambda l: abs(l['y'] - v['y'])) if cands else None
        v['lab'] = lab
        if lab: lab['paired'] = v['name']
        if lab and lab['text'].strip().strip('"') in ONE_LINE: v['cls'] = 'short'
    cols = {c: sorted([i for i in items if i['col'] == c and i['kind'] in ('sec', 'val')], key=lambda i: (i['y'], i['kind'] != 'sec')) for c in range(3)}
    if p == 'PVD':
        col = cols[0]; v7 = by['PVD_Val7']; col.remove(v7); col.insert(col.index(by['PVD_Sec6']) + 1, v7)
    def move(num, to_col, after_num):
        v, a = by[f'{p}_Val{num}'], by[f'{p}_Val{after_num}']
        cols[v['col']].remove(v); cols[to_col].insert(cols[to_col].index(a) + 1, v); v['col'] = to_col
    if p == 'PPoD':
        move('12', 1, '11'); move('13', 0, '18'); move('14', 0, '13'); move('15', 0, '14'); move('32', 0, '15')
    return dict(tp=tp, items=items, by=by, vals=vals, cols=cols)
def lab_of(i): return ((i['lab'] or {}).get('text', '')).strip().strip('"')
def fit(P, lbl_sf, val_sf, budget, top, sec_sf=14, widths=None):
    """caps per value for one mode (sizes, budget); returns (caps, rowheight, metrics)"""
    m = {}
    for i in P['vals']:
        lab = i['lab']
        txt = lab_of(i)
        ll = text_lines(txt, lbl_sf, lab['wf']) if lab else 0
        m[i['name']] = dict(lv=line_h(val_sf), cp=cpl(val_sf, i['wf']), ll=ll, LL=line_h(lbl_sf))
    sech = line_h(sec_sf)
    def rowh(i, k): mm = m[i['name']]; return max(k * mm['lv'], mm['ll'] * mm['LL'])
    def colh(col, caps): return top + sum(sech if i['kind'] == 'sec' else rowh(i, caps[i['name']]) for i in col) + 6
    caps = {i['name']: {'short': 1, 'normal': 2, 'long': 4}[i['cls']] for i in P['vals']}
    ok = True
    for c, col in P['cols'].items():
        for cls, k in (('long', 3), ('long', 2), ('normal', 1), ('long', 1)):
            for i in sorted([i for i in col if i['kind'] == 'val' and i['cls'] == cls and lab_of(i) not in KEEP],
                            key=lambda i: (GIVE.index(lab_of(i)) if lab_of(i) in GIVE else len(GIVE), -caps[i['name']])):
                if colh(col, caps) <= budget: break
                caps[i['name']] = min(caps[i['name']], k)
        if colh(col, caps) > budget: ok = False
    return ok, caps, max(colh(col, caps) for col in P['cols'].values()), m, sech
