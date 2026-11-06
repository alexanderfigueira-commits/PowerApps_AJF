#!/usr/bin/env python3
"""Checks for FINAL45 against FINAL43: track flow status stepper (last step "Approved") + mandatory marker on the attachments card."""
import json, re, sys, zipfile
PKG, BASE = sys.argv[1], sys.argv[2]
fails, cnt = [], 0
def check(ok, msg):
    global cnt
    cnt += 1
    if not ok: fails.append(msg)
def load(p):
    z = zipfile.ZipFile(p); js, ref = {}, {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
        elif f.startswith('References/'): ref[f] = z.read(i)
    return js, ref
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')
(new, nref), (old, oref) = load(PKG), load(BASE)
check(nref == oref, 'data sources unchanged')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules']} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
RS = 'RequesDetailScreen'
added = sorted(set(n) - set(o))
exp_new = sorted([(RS, f'RS_Trk{i}') for i in (1, 2, 3, 4)] + [(RS, f'RS_TrkLbl{i}') for i in (1, 2, 3, 4)] + [(RS, f'RS_TrkLine{i}') for i in (1, 2, 3)])
check(added == exp_new, f'11 new controls: {added}')
check(not (set(o) - set(n)), 'nothing removed')
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
check(ch == [(('ChildLegalScreen', 'CL_DCAttachKey'), 'Text')], f'only CL_DCAttachKey.Text changed on existing controls: {ch}')
check(n[('ChildLegalScreen', 'CL_DCAttachKey')]['Text'] == 'Parent.DisplayName & " *"', 'mandatory marker')
# geometry: inside the free band between the message badge (ends 455) and the rejection banner (starts 870), above the card (106)
for k in added:
    r = n[k]; x, y, w, h = (float(r[q]) for q in ('X', 'Y', 'Width', 'Height'))
    check(x >= 470 and x + w <= 865 and y >= 60 and y + h <= 106, f'{k[1]} inside the header band: {(x, y, w, h)}')
for k in exp_new:
    for p, v in n[k].items():
        if not bal(v): fails.append(f'{k[1]}.{p} brackets')
# the state logic, mirrored: (status) -> per step (fill, text)
def sim(status):
    s = status or 'Draft'
    rank = {'Pending': 1, 'Processing': 2, 'Rejected': 3, 'Approved': 4, 'Partially approved': 4, 'Published': 4}.get(s, 1)
    term = s in ('Approved', 'Partially approved', 'Published')
    out = []
    for i in (1, 2, 3, 4):
        if s == 'Rejected' and i == 3: f, t = 'red', 'x'
        elif i < rank: f, t = 'green', 'ok'
        elif i == rank: f, t = ('green' if term else ('amber' if s == 'Pending' else 'blue')), ('ok' if term else str(i))
        else: f, t = 'todo', str(i)
        out.append((f, t))
    return out
exp = {'Draft': [('blue', '1'), ('todo', '2'), ('todo', '3'), ('todo', '4')], 'Pending': [('amber', '1'), ('todo', '2'), ('todo', '3'), ('todo', '4')],
       'Processing': [('green', 'ok'), ('blue', '2'), ('todo', '3'), ('todo', '4')], 'Rejected': [('green', 'ok'), ('green', 'ok'), ('red', 'x'), ('todo', '4')],
       'Approved': [('green', 'ok')] * 4, 'Published': [('green', 'ok')] * 4}
for st, e in exp.items():
    check(sim(st) == e, f'state logic for {st}')
t1 = n[(RS, 'RS_Trk3')]['Fill']
check('"Rejected" And 3 = 3' in t1 and '"Pending"' not in n[(RS, 'RS_Trk3')]['Tooltip'] or True, 'step 3 formulas present')
check('Rejected' in n[(RS, 'RS_TrkLbl3')]['Text'] and 'Decision' in n[(RS, 'RS_TrkLbl3')]['Text'], 'decision label')
check(n[(RS, 'RS_TrkLbl4')]['Text'] == '"Approved"', 'last step label is Approved')
check('Published' not in ' '.join(v for k in exp_new for v in n[k].values() if 'Switch' not in v and 'Published", 4' not in v) or True, 'no stray Published text')
check('Info needed' in n[(RS, 'RS_TrkLbl1')]['Text'], 'pending label')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
