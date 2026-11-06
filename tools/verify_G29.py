#!/usr/bin/env python3
"""Checks for FINAL39 against FINAL38: only the HomeGallery sort changed."""
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
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(new), flat(old)
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p))
check(ch == [(('RequestManagementScreen', 'HomeGallery'), 'Items')], f'only HomeGallery.Items changed: {ch}')
t = n[('RequestManagementScreen', 'HomeGallery')]['Items']
check(t.count('Filter(') == o[('RequestManagementScreen', 'HomeGallery')]['Items'].count('Filter('), 'filters untouched')
check('If(Status.Value = "Draft", 10000000000, 0)' in t and 'If(Status.Value = "Draft", Created, Modified)' in t, 'drafts by Created, others by Modified')
check(t.count('SortOrder.Descending') == 1 and t.count('SortOrder.Ascending') == 1, 'order: All newest first, single status oldest first')
check(bal(t), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
