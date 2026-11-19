#!/usr/bin/env python3
"""Checks for FINAL46 against FINAL45: only the Visible rule of the two contact "+" buttons changed."""
import json, sys, zipfile
PKG, BASE = sys.argv[1], sys.argv[2]
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
(new, nref), (old, oref) = load(PKG), load(BASE)
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules']} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
fails = []
if nref != oref: fails.append('data sources changed')
if set(n) != set(o): fails.append('controls differ')
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
exp = sorted([(('RequesDetailScreen', 'RS_DetailsToggle_contrator_1'), 'Visible'), (('RequesDetailScreen', 'RS_DetailsToggle_contrator'), 'Visible')])
if ch != exp: fails.append(f'unexpected changes: {ch}')
for c in ('RS_DetailsToggle_contrator_1', 'RS_DetailsToggle_contrator'):
    if n[('RequesDetailScreen', c)]['Visible'] != 'Not(locDetailsCollapsed) And Not(varRequestorLocked)': fails.append(f'{c} visible rule')
print(f'{3 + 2 - len(fails)}/5 checks passed' if not fails else 'FAIL ' + '; '.join(fails))
sys.exit(1 if fails else 0)
