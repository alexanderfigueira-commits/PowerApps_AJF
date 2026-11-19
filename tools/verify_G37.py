#!/usr/bin/env python3
"""Checks for FINAL47 against FINAL46: text inputs are black in view mode on the three screens."""
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
check(set(n) == set(o), 'same controls')
tmpl = {(s, c['Name']): c['Template']['Name'] for s, t in new.items() for c in walk(t)}
texts = sorted(k for k, v in tmpl.items() if v == 'text' and k[0] in ('RequesDetailScreen', 'ChildInfoScreen', 'ChildMetaScreen'))
ch = sorted((k, p) for k in n if k in o for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p) and p != 'ZIndex')
check(ch == [(k, 'Color') for k in texts], f'only Color of the {len(texts)} text inputs changed (got {len(ch)} changes)')
check(len(texts) == 31, f'31 text inputs, found {len(texts)}')
for k in texts:
    c = n[k]['Color'].replace('\n', ' ')
    check('Self.DisplayMode = DisplayMode.View' in c and 'RGBA(0, 0, 0, 1)' in c and bal(n[k]['Color']), f'{k[1]} rule')
    # the edit-mode colour is exactly what it was
    prev = o[k]['Color'].replace('\r\n', '\n').strip()
    check(prev in n[k]['Color'].replace('\r\n', '\n').replace('\n    ', '\n'), f'{k[1]} keeps its previous colour outside view mode')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
