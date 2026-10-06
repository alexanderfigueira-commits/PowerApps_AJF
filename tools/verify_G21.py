#!/usr/bin/env python3
"""Checks for FINAL31 against FINAL30: only the border of CL_DCAttachValue changed."""
import json, re, sys, zipfile
PKG, BASE = sys.argv[1], sys.argv[2]
fails, cnt = [], 0
def check(ok, msg):
    global cnt
    cnt += 1
    if not ok: fails.append(msg)
def load(p):
    z = zipfile.ZipFile(p); js = {}
    for i in z.infolist():
        f = i.filename.replace('\\', '/')
        if f.startswith('Controls/'):
            d = json.loads(z.read(i).decode('utf-8-sig')); js[d['TopParent']['Name']] = d['TopParent']
    return js
def walk(c):
    yield c
    for k in c.get('Children', []): yield from walk(k)
def bal(t):
    v = re.sub(r'(?m)^\s*//[^\n]*', '', t); v = re.sub(r'"[^"\n]*"', '""', v)
    return v.count('(') == v.count(')') and v.count('{') == v.count('}')
flat = lambda js: {(s, c['Name']): {r['Property']: r['InvariantScript'] for r in c['Rules'] if r['Property'] != 'ZIndex'} for s, t in js.items() for c in walk(t)}
n, o = flat(load(PKG)), flat(load(BASE))
ch = sorted((k, p) for k in n for p in set(n[k]) | set(o.get(k, {})) if n[k].get(p) != o.get(k, {}).get(p))
check(ch == [(('ChildLegalScreen', 'CL_DCAttachValue'), 'BorderColor'), (('ChildLegalScreen', 'CL_DCAttachValue'), 'BorderThickness')], f'only the two border rules changed: {ch}')
r = n[('ChildLegalScreen', 'CL_DCAttachValue')]
check('CountRows(CL_DCAttachValue.Attachments) = 0' in r['BorderColor'] and 'CountRows(CL_DCAttachValue.Attachments) = 0' in r['BorderThickness'], 'empty test in colour and thickness')
check('Color.Red' in r['BorderColor'] and 'CL_LblVTT.Visible' in r['BorderColor'], 'red error and VTT rule kept')
check(bal(r['BorderColor']) and bal(r['BorderThickness']), 'brackets')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
