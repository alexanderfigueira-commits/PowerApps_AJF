#!/usr/bin/env python3
"""Checks for FINAL34 against FINAL33: only CL_BtnNext.OnSelect changed."""
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
check(ch == [(('ChildLegalScreen', 'CL_BtnNext'), 'OnSelect')], f'only CL_BtnNext.OnSelect changed: {ch}')
t = n[('ChildLegalScreen', 'CL_BtnNext')]['OnSelect']
check(t.rstrip().endswith('Navigate(ChildValidScreen)'), 'still navigates to Validations')
check('Coalesce(varAttachRecord.ID, 0) = 0' in t and 'Set(varCurrentChildSPId, rid)' in t and 'Set(varAttachRecord, LookUp(' in t, 'recovers the id only when the card has none')
check(t.index('varCurrentChildSPId, 0) > 0') < t.index('colArchives') < t.index("'AV-CD-Mediafiles', ParentRequest"), 'order: variable, media list, latest item by title')
check(bal(t), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
