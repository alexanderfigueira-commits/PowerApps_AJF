#!/usr/bin/env python3
"""Checks for FINAL49 against FINAL48: the administrator dashboard menu holds all five buttons inside the panel."""
import json, re, sys, zipfile
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
S = 'Dashboard-Ope-Administrator'
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
exp = sorted([((S, 'DOA_Menu_Panel'), 'X'), ((S, 'DOA_Menu_Panel'), 'Width'), ((S, 'DOA_Menu_Dashboard'), 'X'), ((S, 'DOA_Menu_Requests'), 'X'), ((S, 'DOA_Menu_Review'), 'X'), ((S, 'DOA_Menu_Review'), 'Width')])
if ch != exp: fails.append(f'unexpected changes: {ch}')
# the administrator layout
px, pw = 686, 424
items = {'Dashboard': (705, 83), 'Requests': (797, 83), 'Review': (875, 83), 'Export': (951, 83), 'Help': (1030, 83)}
def val(c, p):
    v = n[(S, c)][p]; m = re.fullmatch(r'If\(varUserRole = "ADMINISTRATOR", (\d+), (\d+)\)', v)
    return int(m.group(1)) if m else int(v)
if (val('DOA_Menu_Panel', 'X'), val('DOA_Menu_Panel', 'Width')) != (px, pw): fails.append('panel geometry')
spans = []
for name, (x, w) in items.items():
    c = f'DOA_Menu_{name}'
    got = (val(c, 'X'), val(c, 'Width'))
    if got != (x, w): fails.append(f'{name}: {got} expected {(x, w)}')
    if not (px <= got[0] and got[0] + got[1] <= px + pw + 3): fails.append(f'{name} not inside the panel')
    spans.append(got)
spans.sort()
if any(spans[i][0] + spans[i][1] > spans[i + 1][0] + 8 for i in range(len(spans) - 1)): fails.append('buttons overlap')
if n[(S, 'DOA_Menu_Review')]['Visible'] != 'varUserRole = "ADMINISTRATOR"': fails.append('Review visibility changed')
# the other screens are untouched
if any(n[k] != o[k] for k in n if k[0] != S): fails.append('another screen changed')
print('FAIL: ' + '; '.join(fails) if fails else '8/8 checks passed')
sys.exit(1 if fails else 0)
