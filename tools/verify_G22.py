#!/usr/bin/env python3
"""Checks for FINAL32 against FINAL31: only text/tooltip fixes and the Export Request ID search changed."""
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
check(set(n) == set(o), 'same controls')
ch = [(k, p) for k in n for p in set(n[k]) | set(o[k]) if n[k].get(p) != o[k].get(p)]
check(len(ch) == 33, f'33 rules changed, got {len(ch)}')
check(all(bal(n[k][p]) for k, p in ch), 'brackets in changed rules')
allt = ' '.join(v for d in n.values() for v in d.values())
check('clipbaoard' not in allt and 'Contrator' not in allt and 'Contact Saved' not in allt, 'typos gone')
check('IsNumeric(HP_TxtRequestID' not in allt and allt.count('StartsWith(RequestNumber, HP_TxtRequestID.Text)') == 15, 'Export ID search on RequestNumber (15 places)')
for k in (('RequesDetailScreen', 'RS_btnCancelContact'), ('RequesDetailScreen', 'RS_btnSaveContact')):
    check(n[k]['Tooltip'] != '"Save draft"', f'{k[1]} tooltip')
check(not re.search(r'[A-Za-z)]\*"', n[('RequesDetailScreen', 'RS_ArchivesSection')]['Text']), 'label spacing')
# unchanged on purpose
check('New archive' in json.dumps(n[('ChildMetaScreen', 'CM_Breadcrumb')]), 'data sentinel New archive kept')
print(f'{cnt - len(fails)}/{cnt} checks passed')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)
