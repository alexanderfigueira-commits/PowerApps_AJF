#!/usr/bin/env python3
"""Checks for FINAL40 against the owner's FINAL_1: end-of-day date, All Status order, "Partially approved" is no longer a status."""
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
check(set(n) == set(o), "same controls: the owner's layout edits are untouched")
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
exp = sorted([(('App', 'App'), 'OnStart'), (('RequestManagementScreen', 'RequestManagementScreen'), 'OnVisible'), (('RequestManagementScreen', 'HomeGallery'), 'Items'),
              (('RequesDetailScreen', 'Add_media_icon'), 'OnSelect'), (('ReviewScreen', 'RV_BtnApprove'), 'OnSelect')]
             + [((s, f'{p}_List{i}RowBadge'), q) for s, p in (('Dashboard-Ope-Administrator', 'DOA'), ('Dashboard-Ope-Requestor', 'DOR')) for i in (1, 2, 3) for q in ('Text', 'Tooltip', 'Fill')])
check(ch == exp, f'exactly the expected rules changed: extra={sorted(set(ch) - set(exp))} missing={sorted(set(exp) - set(ch))}')
ov = n[('RequestManagementScreen', 'RequestManagementScreen')]['OnVisible']
check('Set(varFilterEndDate, Today() + Time(23, 59, 59))' in ov and 'Set(varFilterEndDate, Today());' not in ov and 'varFilterDay <> Today()' in ov, 'default To = end of today, new-day reset')
it = n[('RequestManagementScreen', 'HomeGallery')]['Items']
check('If(Status.Value = "Draft", Created, Modified)' in it and 'If(Status.Value = "Draft", 10000000000, 0)' in it, 'All Status: drafts by Created first, others by Modified')
ap = n[('ReviewScreen', 'RV_BtnApprove')]['OnSelect']
check('Status: {Value: "Approved"}' in ap and '"Partially approved"' not in ap, 'Approve never writes "Partially approved"')
for s, pre in (('Dashboard-Ope-Administrator', 'DOA'), ('Dashboard-Ope-Requestor', 'DOR')):
    for i in (1, 2, 3):
        b = n[(s, f'{pre}_List{i}RowBadge')]
        check('Partially Approved Request.' in b['Tooltip'] and 'colOpeMedia' in b['Tooltip'] and 'ok > 0 And ok < n' in b['Tooltip'] and bal(b['Tooltip']), f'{pre} list {i}: tooltip')
        check('DarkGoldenRod' not in b['Fill'] and 'If(ThisItem.Status.Value = "Partially approved", "Approved", Text(ThisItem.Status.Value))' in b['Text'], f'{pre} list {i}: text and colour')
check(all(bal(n[k][p]) for k, p in ch), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
