#!/usr/bin/env python3
"""Checks for FINAL50 against FINAL49: every navigation menu uses the same 9 px gap between its buttons."""
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
A = 'varUserRole = "ADMINISTRATOR"'
menu = re.compile(r'^\w+?_Menu_(Panel|Dashboard|Requests|Review|Export|Help)(_1)?$')
ch = {k for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex'}
bad = [k for k in ch if not menu.match(k[1])]
if bad: fails.append(f'non-menu changes: {bad}')
def val(s, c, p, admin):
    v = n[(s, c)][p]; m = re.fullmatch(r'If\(' + re.escape(A) + r', (\d+), (\d+)\)', v)
    return int(m.group(1 if admin else 2)) if m else int(v)
screens = {k[0] for k in n if menu.match(k[1])}
for s in sorted(screens):
    pre = {re.match(r'^(\w+?)_Menu_', k[1]).group(1) + ('_1' if k[1].endswith('_1') else '') for k in n if k[0] == s and menu.match(k[1])}
    for pf in pre:
        sfx = '_1' if pf.endswith('_1') else ''
        base = pf[:-2] if sfx else pf
        nm = lambda i: f'{base}_Menu_{i}{sfx}'
        for admin in (True, False):
            px, pw = val(s, nm('Panel'), 'X', admin), val(s, nm('Panel'), 'Width', admin)
            seq = ['Dashboard', 'Requests'] + (['Review'] if admin else []) + ['Export', 'Help']
            prev = None
            for i in seq:
                x, w = val(s, nm(i), 'X', admin), val(s, nm(i), 'Width', admin)
                if w != 83: fails.append(f'{s} {i} width {w}')
                if not (px <= x and x + w <= px + pw): fails.append(f'{s} {i} outside panel (admin={admin})')
                if prev is not None and x - prev != 92: fails.append(f'{s} {i} gap {x - prev - 83} (admin={admin})')
                prev = x
            if px + pw != 1110: fails.append(f'{s} panel right edge {px + pw}')
            if admin and px != 621 or (not admin and px != 713): fails.append(f'{s} panel X {px}')
        if n[(s, nm('Review'))].get('Visible') != A: fails.append(f'{s} Review visibility {n[(s, nm("Review"))].get("Visible")}')
print(len(screens), 'screens checked')
print('FAIL' if fails else 'PASS')
for f in fails: print(' -', f)
sys.exit(1 if fails else 0)
